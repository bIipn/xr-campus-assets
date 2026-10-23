// Walk the Archive - guided visits (see the header).

#include "Systems/WTAVisitSubsystem.h"
#include "Core/WTACharacter.h"
#include "Core/WTAGameMode.h"
#include "Core/WTAGameState.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "Core/WTAPlayerState.h"
#include "Core/WTASettings.h"
#include "Core/WTAText.h"
#include "Systems/WTAProgressSubsystem.h"
#include "Systems/WTATourSubsystem.h"
#include "CollisionQueryParams.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/NetDriver.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "IPAddress.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "NavigationSystem.h"
#include "Modules/ModuleManager.h"
#include "SocketSubsystem.h"
#include "SocketSubsystemModule.h"
#include "Sockets.h"
#include "UObject/UObjectGlobals.h"
#include "UObject/UObjectIterator.h"

namespace
{
	/** The campus takes a while to load: the guide's machine waits this long for a visitor still loading it (the
	    connection's first timeout runs until the visitor's controller exists), and a visit outlives a long hitch. */
	constexpr float VisitTimeoutSeconds = 120.f;

	/** The local player's view, with a seated eye brought down to standing on the floor under it. */
	FWTAView StandingViewOf(UWorld* World, const AWTACharacter* Character)
	{
		FWTAView View = Character->GetCurrentView();
		if (Character->IsSeated())
		{
			View.Location = UWTAVisitSubsystem::FloorUnder(World, View.Location, Character->EyeHeight) + FVector(0.f, 0.f, Character->EyeHeight);
			View.Pitch = 0.f;
		}
		return View;
	}

	const FName NAME_IPv4(TEXT("IPv4"));

	/**
	 * The platform's socket subsystem, reached through the Sockets module's interface: every call made on it here
	 * (and on its sockets and addresses) is virtual, so this module needs no link to Sockets and Build.cs stays as
	 * it is (a changed Build.cs recompiles the build-rules assembly; see CONTRACT.md section 4).
	 */
	ISocketSubsystem* SocketSubsystem()
	{
		FSocketSubsystemModule* Module = FModuleManager::GetModulePtr<FSocketSubsystemModule>(FName(TEXT("Sockets")));
		return Module ? Module->GetSocketSubsystem() : nullptr;
	}

	/** A non-blocking UDP socket: broadcasting for the guide's beacon, or bound to BindPort for listening to the
	    beacons (BindPort < 0: not bound). */
	FSocket* MakeUdpSocket(const TCHAR* Description, bool bBroadcast, int32 BindPort)
	{
		ISocketSubsystem* Sockets = SocketSubsystem();
		FSocket* Socket = Sockets ? Sockets->CreateSocket(NAME_DGram, Description, NAME_IPv4) : nullptr;
		if (Socket == nullptr)
		{
			return nullptr;
		}
		Socket->SetNonBlocking(true);
		Socket->SetReuseAddr(true);
		if (bBroadcast)
		{
			Socket->SetBroadcast(true);
		}
		if (BindPort >= 0)
		{
			TSharedRef<FInternetAddr> Any = Sockets->CreateInternetAddr(NAME_IPv4);
			Any->SetAnyAddress();
			Any->SetPort(BindPort);
			if (!Socket->Bind(*Any))
			{
				Sockets->DestroySocket(Socket);
				return nullptr;
			}
			int32 Size = 0;
			Socket->SetReceiveBufferSize(16 * 1024, Size);
		}
		return Socket;
	}

	FCollisionQueryParams IgnoringPeople(UWorld* World, const TCHAR* Tag)
	{
		FCollisionQueryParams Params{ FName(Tag), false };
		for (TActorIterator<AWTACharacter> It(World); It; ++It)
		{
			Params.AddIgnoredActor(*It);
		}
		return Params;
	}
}

UWTAVisitSubsystem* UWTAVisitSubsystem::Get(const UObject* WorldContextObject)
{
	if (WorldContextObject == nullptr || GEngine == nullptr)
	{
		return nullptr;
	}
	const UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull);
	const UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
	return GameInstance ? GameInstance->GetSubsystem<UWTAVisitSubsystem>() : nullptr;
}

void UWTAVisitSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	Collection.InitializeDependency(UWTATourSubsystem::StaticClass());
	Collection.InitializeDependency(UWTAProgressSubsystem::StaticClass());

	// Visitors walk to the stops on their own machine's NavMesh. A client world gets a navigation system only with
	// bAllowClientSideNavigation, which is off by default; it is set here, on the class default the engine reads
	// when a world is made, so DefaultEngine.ini stays as it is.
	if (UNavigationSystemV1* NavDefaults = GetMutableDefault<UNavigationSystemV1>())
	{
		if (FBoolProperty* Allow = FindFProperty<FBoolProperty>(UNavigationSystemV1::StaticClass(), TEXT("bAllowClientSideNavigation")))
		{
			Allow->SetPropertyValue_InContainer(NavDefaults, true);
		}
	}
	// A visitor loading the campus must not be dropped before they arrive (see VisitTimeoutSeconds).
	for (TObjectIterator<UClass> It; It; ++It)
	{
		if (It->IsChildOf(UNetDriver::StaticClass()) && !It->HasAnyClassFlags(CLASS_Abstract))
		{
			if (UNetDriver* DriverDefaults = It->GetDefaultObject<UNetDriver>())
			{
				DriverDefaults->InitialConnectTimeout = FMath::Max(DriverDefaults->InitialConnectTimeout, VisitTimeoutSeconds);
				DriverDefaults->ConnectionTimeout = FMath::Max(DriverDefaults->ConnectionTimeout, VisitTimeoutSeconds);
			}
		}
	}

	if (UWTATourSubsystem* Tour = GetGameInstance() ? GetGameInstance()->GetSubsystem<UWTATourSubsystem>() : nullptr)
	{
		Tour->OnTourChanged.AddDynamic(this, &UWTAVisitSubsystem::HandleTourChanged);
		bTourBound = true;
	}
	if (GEngine != nullptr)
	{
		NetworkFailureHandle = GEngine->OnNetworkFailure().AddUObject(this, &UWTAVisitSubsystem::HandleNetworkFailure);
		TravelFailureHandle = GEngine->OnTravelFailure().AddUObject(this, &UWTAVisitSubsystem::HandleTravelFailure);
	}
	PostLoadMapHandle = FCoreUObjectDelegates::PostLoadMapWithWorld.AddUObject(this, &UWTAVisitSubsystem::HandlePostLoadMap);
	TickHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateUObject(this, &UWTAVisitSubsystem::TickVisit), 0.f);
}

void UWTAVisitSubsystem::Deinitialize()
{
	FTSTicker::GetCoreTicker().RemoveTicker(TickHandle);
	if (GEngine != nullptr)
	{
		GEngine->OnNetworkFailure().Remove(NetworkFailureHandle);
		GEngine->OnTravelFailure().Remove(TravelFailureHandle);
	}
	FCoreUObjectDelegates::PostLoadMapWithWorld.Remove(PostLoadMapHandle);
	CloseSocket(BeaconSocket);
	CloseSocket(SearchSocket);
	Super::Deinitialize();
}

// --- Who we are ---------------------------------------------------------------------

UWorld* UWTAVisitSubsystem::CurrentWorld() const
{
	return GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
}

AWTAPlayerController* UWTAVisitSubsystem::LocalController() const
{
	UGameInstance* GameInstance = GetGameInstance();
	return GameInstance ? Cast<AWTAPlayerController>(GameInstance->GetFirstLocalPlayerController(CurrentWorld())) : nullptr;
}

AWTAGameState* UWTAVisitSubsystem::VisitState() const
{
	const UWorld* World = CurrentWorld();
	return World ? World->GetGameState<AWTAGameState>() : nullptr;
}

EWTAVisitRole UWTAVisitSubsystem::GetRole() const
{
	const UWorld* World = CurrentWorld();
	if (World == nullptr)
	{
		return EWTAVisitRole::Solo;
	}
	switch (World->GetNetMode())
	{
	case NM_ListenServer:
		return EWTAVisitRole::Guide;
	case NM_Client:
		return EWTAVisitRole::Visitor;
	default:
		return EWTAVisitRole::Solo;
	}
}

int32 UWTAVisitSubsystem::MySlot() const
{
	const AWTAPlayerController* PC = LocalController();
	const AWTAPlayerState* Person = PC ? PC->GetPlayerState<AWTAPlayerState>() : nullptr;
	return Person ? Person->Slot : 0;
}

FString UWTAVisitSubsystem::GetMyName() const
{
	const UWTAProgressSubsystem* Progress = GetGameInstance() ? GetGameInstance()->GetSubsystem<UWTAProgressSubsystem>() : nullptr;
	return Progress ? Progress->GetVisitorName() : FString();
}

void UWTAVisitSubsystem::SetMyName(const FString& Name)
{
	const FString Clean = Name.TrimStartAndEnd();
	if (Clean.IsEmpty())
	{
		return;
	}
	if (UWTAProgressSubsystem* Progress = GetGameInstance() ? GetGameInstance()->GetSubsystem<UWTAProgressSubsystem>() : nullptr)
	{
		Progress->SetVisitorName(Clean);
	}
	if (AWTAPlayerController* PC = LocalController())
	{
		if (IsInVisit())
		{
			PC->ServerSetVisitName(Clean);
		}
	}
}

FString UWTAVisitSubsystem::GetGuideName() const
{
	const AWTAGameState* State = VisitState();
	const AWTAPlayerState* Guide = State ? State->GetGuide() : nullptr;
	return Guide ? Guide->GetVisitName() : FString();
}

TArray<FWTAVisitPerson> UWTAVisitSubsystem::GetPeople() const
{
	TArray<FWTAVisitPerson> Out;
	const AWTAGameState* State = VisitState();
	if (State == nullptr || GetRole() == EWTAVisitRole::Solo)
	{
		return Out;
	}
	const AWTAPlayerController* PC = LocalController();
	const APlayerState* Mine = PC ? PC->PlayerState.Get() : nullptr;
	TArray<const AWTAPlayerState*> People;
	for (APlayerState* Player : State->PlayerArray)
	{
		if (const AWTAPlayerState* Person = Cast<AWTAPlayerState>(Player))
		{
			People.Add(Person);
		}
	}
	People.Sort([](const AWTAPlayerState& A, const AWTAPlayerState& B)
	{
		if (A.bGuide != B.bGuide)
		{
			return A.bGuide;
		}
		return A.Slot < B.Slot;
	});
	for (const AWTAPlayerState* Person : People)
	{
		FWTAVisitPerson Row;
		Row.Name = Person->GetVisitName();
		Row.Color = Person->GetVisitColor();
		Row.bGuide = Person->bGuide;
		Row.bYou = Person == Mine;
		Out.Add(Row);
	}
	return Out;
}

TArray<FString> UWTAVisitSubsystem::GetLocalAddresses() const
{
	TArray<FString> Out;
	ISocketSubsystem* Sockets = SocketSubsystem();
	TArray<TSharedPtr<FInternetAddr>> Addresses;
	if (Sockets != nullptr && Sockets->GetLocalAdapterAddresses(Addresses))
	{
		for (const TSharedPtr<FInternetAddr>& Address : Addresses)
		{
			if (!Address.IsValid() || Address->GetProtocolType() != NAME_IPv4)
			{
				continue;
			}
			const FString Text = Address->ToString(false);
			if (Text.StartsWith(TEXT("127.")) || Text.StartsWith(TEXT("169.254.")) || Text == TEXT("0.0.0.0"))
			{
				continue;
			}
			Out.AddUnique(Text);
		}
	}
	return Out;
}

FString UWTAVisitSubsystem::MapPath() const
{
	const UWorld* World = CurrentWorld();
	if (World == nullptr)
	{
		return TEXT("/Game/WTA/Maps/L_Campus");
	}
	return UWorld::RemovePIEPrefix(World->GetOutermost()->GetName());
}

// --- Doing ----------------------------------------------------------------------------

void UWTAVisitSubsystem::KeepCurrentView()
{
	UWorld* World = CurrentWorld();
	const AWTAPlayerController* PC = LocalController();
	const AWTACharacter* Character = PC ? PC->GetWTACharacter() : nullptr;
	if (World != nullptr && Character != nullptr)
	{
		LastKnownView = StandingViewOf(World, Character);
	}
	if (LastKnownView.bValid)
	{
		RestoreView = LastKnownView;
		bRestoreView = true;
	}
}

bool UWTAVisitSubsystem::LeadVisit()
{
	UWorld* World = CurrentWorld();
	if (World == nullptr || World->GetNetMode() != NM_Standalone)
	{
		return false;
	}
	KeepCurrentView();
	StopSearch();
	if (UWTATourSubsystem* Tour = GetGameInstance()->GetSubsystem<UWTATourSubsystem>())
	{
		Tour->End();
	}
	bLeading = true;
	Status = WTAText(TEXT("Opening the visit ..."));
	OnVisitChanged.Broadcast();
	UE_LOG(LogWTA, Log, TEXT("WTA_VISIT leading: %s reloads as a listen server"), *MapPath());
	UGameplayStatics::OpenLevel(World, FName(*MapPath()), true, TEXT("listen"));
	return true;
}

bool UWTAVisitSubsystem::JoinVisit(const FString& InAddress)
{
	UWorld* World = CurrentWorld();
	AWTAPlayerController* PC = LocalController();
	FString Address = InAddress.TrimStartAndEnd();
	if (World == nullptr || PC == nullptr || Address.IsEmpty() || World->GetNetMode() != NM_Standalone)
	{
		return false;
	}
	if (!Address.Contains(TEXT(":")))
	{
		Address += FString::Printf(TEXT(":%d"), GamePort);
	}
	KeepCurrentView();
	StopSearch();
	if (UWTATourSubsystem* Tour = GetGameInstance()->GetSubsystem<UWTATourSubsystem>())
	{
		Tour->End();
	}
	bJoining = true;
	JoiningAddress = Address;
	Status = FText::Format(WTAText(TEXT("Joining the visit at {0} ...")), FText::FromString(Address));
	OnVisitChanged.Broadcast();
	UE_LOG(LogWTA, Log, TEXT("WTA_VISIT joining %s"), *Address);
	PC->ClientTravel(Address, TRAVEL_Absolute);
	return true;
}

void UWTAVisitSubsystem::LeaveVisit()
{
	UWorld* World = CurrentWorld();
	const EWTAVisitRole Role = GetRole();
	if (World == nullptr || Role == EWTAVisitRole::Solo)
	{
		bJoining = false;
		return;
	}
	KeepCurrentView();
	bWasVisitor = false;                                  // leaving on purpose is not the guide going away
	PendingToast = Role == EWTAVisitRole::Guide
		? WTAText(TEXT("The visit is over. You're exploring on your own."))
		: WTAText(TEXT("You left the visit. You're exploring on your own."));
	Status = FText::GetEmpty();
	UE_LOG(LogWTA, Log, TEXT("WTA_VISIT %s"), Role == EWTAVisitRole::Guide ? TEXT("ended by the guide") : TEXT("left by this visitor"));
	UGameplayStatics::OpenLevel(World, FName(*MapPath()), true);
}

bool UWTAVisitSubsystem::GatherHere()
{
	UWorld* World = CurrentWorld();
	AWTAGameState* State = VisitState();
	AWTAPlayerController* PC = LocalController();
	const AWTACharacter* Character = PC ? PC->GetWTACharacter() : nullptr;
	if (GetRole() != EWTAVisitRole::Guide || State == nullptr || Character == nullptr)
	{
		return false;
	}
	const FWTAView View = StandingViewOf(World, Character);
	State->Gather(FloorUnder(World, View.Location, Character->EyeHeight), View.Yaw);
	PC->ShowToast(State->NumVisitors() > 0 ? WTAText(TEXT("Everyone is coming to you.")) : WTAText(TEXT("Nobody has joined yet.")), 0.f);
	return true;
}

bool UWTAVisitSubsystem::WalkToGuide()
{
	UWorld* World = CurrentWorld();
	const AWTAGameState* State = VisitState();
	const AWTAPlayerState* Guide = State ? State->GetGuide() : nullptr;
	const AWTACharacter* GuidePawn = Guide ? Guide->GetPawn<AWTACharacter>() : nullptr;
	if (GetRole() != EWTAVisitRole::Visitor || GuidePawn == nullptr)
	{
		return false;
	}
	// The guide's figure on this machine: its eye and the way it faces (the pawn turns with the guide's look).
	const FVector Eye = GuidePawn->GetActorLocation() + FVector(0.f, 0.f, GuidePawn->EyeHeight - 90.f);
	const FWTAView Spot = GroupSpot(World, FloorUnder(World, Eye, GuidePawn->EyeHeight), static_cast<float>(GuidePawn->GetActorRotation().Yaw), 0.f, MySlot(), GuidePawn->EyeHeight);
	MoveLocalPlayer(Spot, 6000.f);
	return true;
}

void UWTAVisitSubsystem::MoveLocalPlayer(const FWTAView& View, float WalkWithin)
{
	AWTAPlayerController* PC = LocalController();
	AWTACharacter* Character = PC ? PC->GetWTACharacter() : nullptr;
	if (PC == nullptr || Character == nullptr || !View.bValid)
	{
		return;
	}
	if (Character->IsSeated())
	{
		Character->StandUp(true);
	}
	const bool bWalk = FVector::Dist(Character->GetEyeLocation(), View.Location) < WalkWithin;
	PC->GoToView(View, bWalk);
}

// --- Finding visits ---------------------------------------------------------------------

void UWTAVisitSubsystem::StartSearch()
{
	if (SearchSocket != nullptr)
	{
		return;
	}
	SearchSocket = MakeUdpSocket(TEXT("WTAVisitSearch"), false, BeaconPort);
	if (SearchSocket == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("Visit: cannot listen for visits on UDP %d (joining by address still works)"), BeaconPort);
	}
}

void UWTAVisitSubsystem::StopSearch()
{
	CloseSocket(SearchSocket);
	Found.Reset();
}

void UWTAVisitSubsystem::CloseSocket(FSocket*& Socket)
{
	if (Socket == nullptr)
	{
		return;
	}
	Socket->Close();
	if (ISocketSubsystem* Sockets = SocketSubsystem())
	{
		Sockets->DestroySocket(Socket);
	}
	Socket = nullptr;
}

TArray<FWTAFoundVisit> UWTAVisitSubsystem::GetFoundVisits() const
{
	TArray<FWTAFoundVisit> Out;
	Found.GenerateValueArray(Out);
	Out.Sort([](const FWTAFoundVisit& A, const FWTAFoundVisit& B) { return A.GuideName < B.GuideName; });
	return Out;
}

void UWTAVisitSubsystem::SendBeacon()
{
	if (FParse::Param(FCommandLine::Get(), TEXT("WTANoBeacon")))
	{
		return;
	}
	ISocketSubsystem* Sockets = SocketSubsystem();
	if (Sockets == nullptr)
	{
		return;
	}
	if (BeaconSocket == nullptr)
	{
		BeaconSocket = MakeUdpSocket(TEXT("WTAVisitBeacon"), true, -1);
		if (BeaconSocket == nullptr)
		{
			return;
		}
	}
	int32 Port = GamePort;
	if (const UWorld* World = CurrentWorld())
	{
		if (UNetDriver* Driver = World->GetNetDriver())
		{
			const TSharedPtr<const FInternetAddr> Local = Driver->GetLocalAddr();
			if (Local.IsValid() && Local->GetPort() > 0)
			{
				Port = Local->GetPort();
			}
		}
	}
	const AWTAGameState* State = VisitState();
	const UWTASettings* Settings = UWTASettings::Get();
	const FString Message = FString::Printf(TEXT("WTAVISIT1|%s|%d|%d|%s"), *GetGuideName().Replace(TEXT("|"), TEXT(" ")), Port,
		State ? State->PlayerArray.Num() : 1, Settings ? *Settings->CampusTitle.Replace(TEXT("|"), TEXT(" ")) : TEXT(""));
	TSharedRef<FInternetAddr> To = Sockets->CreateInternetAddr(NAME_IPv4);
	To->SetBroadcastAddress();
	To->SetPort(BeaconPort);
	const FTCHARToUTF8 Utf8(*Message);
	int32 Sent = 0;
	BeaconSocket->SendTo(reinterpret_cast<const uint8*>(Utf8.Get()), Utf8.Length(), Sent, *To);
}

void UWTAVisitSubsystem::ReadBeacons()
{
	ISocketSubsystem* Sockets = SocketSubsystem();
	if (Sockets == nullptr || SearchSocket == nullptr)
	{
		return;
	}
	bool bChanged = false;
	uint32 Pending = 0;
	for (int32 Guard = 0; Guard < 32 && SearchSocket->HasPendingData(Pending) && Pending > 0; ++Guard)
	{
		TArray<uint8> Buffer;
		Buffer.SetNumZeroed(static_cast<int32>(FMath::Min<uint32>(Pending, 1024u)) + 1);
		int32 Read = 0;
		TSharedRef<FInternetAddr> From = Sockets->CreateInternetAddr(NAME_IPv4);
		if (!SearchSocket->RecvFrom(Buffer.GetData(), Buffer.Num() - 1, Read, *From) || Read <= 0)
		{
			break;
		}
		Buffer[Read] = 0;
		const FString Message = FString(UTF8_TO_TCHAR(reinterpret_cast<const ANSICHAR*>(Buffer.GetData())));
		TArray<FString> Parts;
		Message.ParseIntoArray(Parts, TEXT("|"), false);
		if (Parts.Num() < 4 || Parts[0] != TEXT("WTAVISIT1"))
		{
			continue;
		}
		FWTAFoundVisit Visit;
		Visit.GuideName = Parts[1].IsEmpty() ? WTAText(TEXT("Guide")).ToString() : Parts[1];
		Visit.Address = FString::Printf(TEXT("%s:%d"), *From->ToString(false), FCString::Atoi(*Parts[2]));
		Visit.People = FMath::Max(1, FCString::Atoi(*Parts[3]));
		Visit.Campus = Parts.Num() > 4 ? Parts[4] : FString();
		Visit.LastHeard = FPlatformTime::Seconds();
		const FWTAFoundVisit* Known = Found.Find(Visit.Address);
		bChanged |= Known == nullptr || Known->People != Visit.People || Known->GuideName != Visit.GuideName;
		Found.Add(Visit.Address, Visit);
	}
	if (bChanged)
	{
		OnVisitChanged.Broadcast();
	}
}

// --- Places round a spot ---------------------------------------------------------------------

FVector UWTAVisitSubsystem::FloorUnder(UWorld* World, const FVector& Eye, float EyeHeight)
{
	const FVector Below = Eye - FVector(0.f, 0.f, EyeHeight);
	if (World == nullptr)
	{
		return Below;
	}
	if (UNavigationSystemV1* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World))
	{
		FNavLocation Projected;
		if (Nav->ProjectPointToNavigation(Below, Projected, FVector(150.f, 150.f, 250.f)))
		{
			return Projected.Location;
		}
	}
	FHitResult Hit;
	if (World->LineTraceSingleByChannel(Hit, Eye, Eye - FVector(0.f, 0.f, EyeHeight + 150.f), ECC_Visibility, IgnoringPeople(World, TEXT("WTAFloorUnder"))))
	{
		return Hit.Location;
	}
	return Below;
}

FWTAView UWTAVisitSubsystem::GroupSpot(UWorld* World, const FVector& Floor, float Yaw, float Pitch, int32 Slot, float EyeHeight)
{
	FWTAView View;
	View.bValid = true;
	View.Yaw = Yaw;
	View.Pitch = Pitch;
	View.Location = Floor + FVector(0.f, 0.f, EyeHeight);
	if (Slot <= 0 || World == nullptr)
	{
		return View;
	}

	// (forward, right) in cm from the spot: two arcs behind and beside it, then a third row, so nobody stands in
	// front of the guide or between the group and what it looks at.
	static const FVector2D Places[] = {
		FVector2D(-110.f, -120.f), FVector2D(-110.f, 120.f), FVector2D(-15.f, -175.f), FVector2D(-15.f, 175.f),
		FVector2D(-210.f, -45.f), FVector2D(-210.f, 45.f), FVector2D(-185.f, -215.f), FVector2D(-185.f, 215.f),
		FVector2D(-300.f, -135.f), FVector2D(-300.f, 135.f), FVector2D(-95.f, -265.f), FVector2D(-95.f, 265.f),
		FVector2D(-310.f, 0.f), FVector2D(-275.f, -290.f), FVector2D(-275.f, 290.f), FVector2D(-395.f, -75.f),
		FVector2D(-395.f, 75.f), FVector2D(-390.f, -230.f), FVector2D(-390.f, 230.f), FVector2D(-480.f, 0.f) };
	const int32 Count = UE_ARRAY_COUNT(Places);
	const FRotator Facing(0.f, Yaw, 0.f);
	const FVector Forward = Facing.Vector();
	const FVector Right = FRotationMatrix(Facing).GetUnitAxis(EAxis::Y);
	UNavigationSystemV1* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
	const FCollisionQueryParams Params = IgnoringPeople(World, TEXT("WTAGroupSpot"));

	for (int32 k = 0; k < Count; ++k)
	{
		const FVector2D Place = Places[(Slot - 1 + k) % Count];
		const FVector Want = Floor + Forward * Place.X + Right * Place.Y;
		FVector Ground = Want;
		bool bFloor = false;
		if (Nav != nullptr)
		{
			FNavLocation Projected;
			if (Nav->ProjectPointToNavigation(Want, Projected, FVector(40.f, 40.f, 120.f)))
			{
				Ground = Projected.Location;
				bFloor = true;
			}
		}
		else
		{
			FHitResult Down;
			if (World->LineTraceSingleByChannel(Down, Want + FVector(0.f, 0.f, 120.f), Want - FVector(0.f, 0.f, 200.f), ECC_Visibility, Params))
			{
				Ground = Down.Location;
				bFloor = true;
			}
		}
		// Another storey, a stair or a ledge is not a place to stand with the group.
		if (!bFloor || FMath::Abs(Ground.Z - Floor.Z) > 60.f)
		{
			continue;
		}
		// A clear line from the spot at hip and at head height: no wall, case or figure between.
		FHitResult Hit;
		if (World->LineTraceSingleByChannel(Hit, Floor + FVector(0.f, 0.f, 90.f), Ground + FVector(0.f, 0.f, 90.f), ECC_Visibility, Params)
			|| World->LineTraceSingleByChannel(Hit, Floor + FVector(0.f, 0.f, 150.f), Ground + FVector(0.f, 0.f, 150.f), ECC_Visibility, Params))
		{
			continue;
		}
		View.Location = Ground + FVector(0.f, 0.f, EyeHeight);
		return View;
	}
	return View;
}

bool UWTAVisitSubsystem::ArrivalViewFor(const AWTAPlayerState* Person, FWTAView& OutView) const
{
	UWorld* World = CurrentWorld();
	const AWTAGameState* State = VisitState();
	if (World == nullptr || State == nullptr)
	{
		return false;
	}
	const int32 Slot = Person ? FMath::Max(1, Person->Slot) : 1;
	const AWTAPlayerState* Guide = State->GetGuide();
	const AWTACharacter* GuidePawn = Guide ? Guide->GetPawn<AWTACharacter>() : nullptr;
	const float EyeHeight = GuidePawn ? GuidePawn->EyeHeight : 162.f;
	if (State->TourStop >= 0)
	{
		const UWTATourSubsystem* Tour = GetGameInstance()->GetSubsystem<UWTATourSubsystem>();
		FWTAView StopView;
		if (Tour != nullptr && Tour->GetStopView(State->TourStop, StopView))
		{
			OutView = GroupSpot(World, FloorUnder(World, StopView.Location, EyeHeight), StopView.Yaw, StopView.Pitch, Slot, EyeHeight);
			return true;
		}
	}
	if (GuidePawn != nullptr)
	{
		const FWTAView GuideView = StandingViewOf(World, GuidePawn);
		OutView = GroupSpot(World, FloorUnder(World, GuideView.Location, EyeHeight), GuideView.Yaw, 0.f, Slot, EyeHeight);
		return true;
	}
	return false;
}

// --- From the game state -------------------------------------------------------------------

void UWTAVisitSubsystem::HandleTourChanged(int32 Index)
{
	// The guide's own tour: every stop it shows goes to everyone.
	if (GetRole() == EWTAVisitRole::Guide)
	{
		if (AWTAGameState* State = VisitState())
		{
			State->LeadStop(Index);
		}
	}
}

void UWTAVisitSubsystem::HandleTourReplicated(int32 Stop, int32 Serial)
{
	if (GetRole() != EWTAVisitRole::Visitor || Serial == LastTourSerial)
	{
		return;
	}
	UWTATourSubsystem* Tour = GetGameInstance()->GetSubsystem<UWTATourSubsystem>();
	AWTAPlayerController* PC = LocalController();
	AWTACharacter* Character = PC ? PC->GetWTACharacter() : nullptr;
	if (Tour == nullptr)
	{
		return;
	}
	if (Stop >= 0 && (Character == nullptr || MySlot() <= 0))
	{
		// Too early: no pawn or no place yet. The tick tries again.
		bPendingTour = true;
		PendingTourStop = Stop;
		PendingTourSerial = Serial;
		return;
	}
	bPendingTour = false;
	const bool bFirst = LastTourSerial < 0;
	LastTourSerial = Serial;
	if (Stop < 0)
	{
		if (Tour->IsFollowing())
		{
			Tour->StopFollowing();
			if (PC != nullptr && !bFirst)
			{
				PC->ShowToast(FText::Format(WTAText(TEXT("{0} ended the tour. Look around as long as you like.")), FText::FromString(GetGuideName())), 0.f);
			}
		}
		return;
	}
	FWTAView StopView;
	if (!Tour->GetStopView(Stop, StopView))
	{
		return;
	}
	UWorld* World = CurrentWorld();
	const FWTAView Spot = GroupSpot(World, FloorUnder(World, StopView.Location, Character->EyeHeight), StopView.Yaw, StopView.Pitch, MySlot(), Character->EyeHeight);
	if (Character->IsSeated())
	{
		Character->StandUp(true);
	}
	Tour->FollowStop(Stop, Spot, FVector::Dist(Character->GetEyeLocation(), Spot.Location) < 6000.f);
	UE_LOG(LogWTA, Log, TEXT("WTA_VISIT follow stop %d (serial %d) slot %d"), Stop, Serial, MySlot());
}

void UWTAVisitSubsystem::HandleGatherReplicated(const FVector& Floor, float Yaw, int32 Serial)
{
	if (GetRole() != EWTAVisitRole::Visitor || Serial == LastGatherSerial)
	{
		return;
	}
	if (LastGatherSerial < 0)
	{
		LastGatherSerial = Serial;                        // a gathering from before this visitor came
		return;
	}
	AWTAPlayerController* PC = LocalController();
	const AWTACharacter* Character = PC ? PC->GetWTACharacter() : nullptr;
	if (Character == nullptr || MySlot() <= 0)
	{
		bPendingGather = true;
		PendingGatherFloor = Floor;
		PendingGatherYaw = Yaw;
		PendingGatherSerial = Serial;
		return;
	}
	bPendingGather = false;
	LastGatherSerial = Serial;
	const FWTAView Spot = GroupSpot(CurrentWorld(), Floor, Yaw, 0.f, MySlot(), Character->EyeHeight);
	MoveLocalPlayer(Spot, 6000.f);
	PC->ShowToast(FText::Format(WTAText(TEXT("{0} is gathering the group.")), FText::FromString(GetGuideName())), 0.f);
	UE_LOG(LogWTA, Log, TEXT("WTA_VISIT gathered (serial %d) slot %d"), Serial, MySlot());
}

void UWTAVisitSubsystem::NoteGatherSerial(int32 Serial)
{
	if (LastGatherSerial < 0)
	{
		LastGatherSerial = Serial;
	}
}

// --- Map changes and failures ---------------------------------------------------------------

void UWTAVisitSubsystem::HandleNetworkFailure(UWorld* World, UNetDriver* NetDriver, ENetworkFailure::Type FailureType, const FString& Error)
{
	UE_LOG(LogWTA, Log, TEXT("WTA_VISIT network failure %s: %s"), ENetworkFailure::ToString(FailureType), *Error);
	if (bJoining)
	{
		bJoining = false;
		PendingToast = FText::Format(WTAText(TEXT("Could not join the visit at {0}.")), FText::FromString(JoiningAddress));
		Status = PendingToast;
	}
	else if (bWasVisitor)
	{
		bWasVisitor = false;
		PendingToast = WTAText(TEXT("The guide ended the visit. You're exploring on your own."));
		if (LastKnownView.bValid)
		{
			RestoreView = LastKnownView;
			bRestoreView = true;
		}
	}
	OnVisitChanged.Broadcast();
}

void UWTAVisitSubsystem::HandleTravelFailure(UWorld* World, ETravelFailure::Type FailureType, const FString& Error)
{
	UE_LOG(LogWTA, Log, TEXT("WTA_VISIT travel failure %s: %s"), ETravelFailure::ToString(FailureType), *Error);
	if (bJoining)
	{
		bJoining = false;
		PendingToast = FText::Format(WTAText(TEXT("Could not join the visit at {0}.")), FText::FromString(JoiningAddress));
		Status = PendingToast;
		OnVisitChanged.Broadcast();
	}
}

void UWTAVisitSubsystem::HandlePostLoadMap(UWorld* World)
{
	if (World == nullptr || World != CurrentWorld())
	{
		return;
	}
	LastTourSerial = -1;
	LastGatherSerial = -1;
	bPendingTour = false;
	bPendingGather = false;
	ClientNavTries = 0;
	PeopleSignature.Reset();
	const ENetMode Mode = World->GetNetMode();
	UWTATourSubsystem* Tour = GetGameInstance()->GetSubsystem<UWTATourSubsystem>();
	if (Tour != nullptr && Mode != NM_Client && Tour->IsFollowing())
	{
		Tour->StopFollowing();
	}
	if (Mode == NM_Client)
	{
		bJoining = false;
		bWasVisitor = true;
		Status = FText::GetEmpty();
		UE_LOG(LogWTA, Log, TEXT("WTA_VISIT role visitor"));
	}
	else if (Mode == NM_ListenServer)
	{
		bLeading = false;
		Status = FText::GetEmpty();
		int32 Port = GamePort;
		if (UNetDriver* Driver = World->GetNetDriver())
		{
			const TSharedPtr<const FInternetAddr> Local = Driver->GetLocalAddr();
			if (Local.IsValid() && Local->GetPort() > 0)
			{
				Port = Local->GetPort();
			}
		}
		UE_LOG(LogWTA, Log, TEXT("WTA_VISIT role guide, listening on %d"), Port);
	}
	else
	{
		if (bLeading)
		{
			bLeading = false;
			PendingToast = WTAText(TEXT("The visit could not be opened on this computer's network."));
			Status = PendingToast;
		}
		bWasVisitor = false;
		UE_LOG(LogWTA, Log, TEXT("WTA_VISIT role solo"));
	}
	// The controller may already have begun play (a client's arrives later): hand it the toast now if so.
	if (AWTAPlayerController* PC = LocalController())
	{
		FText Toast;
		if (TakePendingToast(Toast))
		{
			PC->ShowToast(Toast, 6.f);
		}
	}
	OnVisitChanged.Broadcast();
}

bool UWTAVisitSubsystem::TickVisit(float DeltaTime)
{
	UWorld* World = CurrentWorld();
	const EWTAVisitRole Role = GetRole();
	SinceKeep += DeltaTime;
	SinceBeacon += DeltaTime;
	SincePeople += DeltaTime;

	if (Role != EWTAVisitRole::Solo && SinceKeep >= 0.5f)
	{
		SinceKeep = 0.f;
		const AWTAPlayerController* PC = LocalController();
		if (const AWTACharacter* Character = PC ? PC->GetWTACharacter() : nullptr)
		{
			LastKnownView = StandingViewOf(World, Character);
		}
	}
	if (Role == EWTAVisitRole::Guide && SinceBeacon >= 1.f)
	{
		SinceBeacon = 0.f;
		SendBeacon();
	}
	if (SearchSocket != nullptr)
	{
		ReadBeacons();
	}
	if (Role == EWTAVisitRole::Visitor)
	{
		if (bPendingTour)
		{
			HandleTourReplicated(PendingTourStop, PendingTourSerial);
		}
		if (bPendingGather)
		{
			HandleGatherReplicated(PendingGatherFloor, PendingGatherYaw, PendingGatherSerial);
		}
	}
	if (SincePeople >= 0.5f)
	{
		SincePeople = 0.f;
		const double Now = FPlatformTime::Seconds();
		bool bChanged = false;
		for (auto It = Found.CreateIterator(); It; ++It)
		{
			if (Now - It.Value().LastHeard > 4.0)
			{
				It.RemoveCurrent();
				bChanged = true;
			}
		}
		FString Signature = FString::Printf(TEXT("%d|"), static_cast<int32>(Role));
		for (const FWTAVisitPerson& Person : GetPeople())
		{
			Signature += Person.Name + TEXT(";");
		}
		if (Signature != PeopleSignature)
		{
			PeopleSignature = Signature;
			bChanged = true;
		}
		if (bChanged)
		{
			OnVisitChanged.Broadcast();
		}
		// A visitor's NavMesh: built when the game state begins play; tried again a few times in case the
		// navigation data was not there yet.
		if (Role == EWTAVisitRole::Visitor && ClientNavTries < 3 && World != nullptr)
		{
			++ClientNavTries;
			AWTAGameMode::BuildNavigationIfEmpty(World);
		}
	}
	return true;
}

// --- Carried over a map change ------------------------------------------------------------------

bool UWTAVisitSubsystem::TakeRestoreView(FWTAView& OutView)
{
	if (!bRestoreView || !RestoreView.bValid)
	{
		return false;
	}
	OutView = RestoreView;
	bRestoreView = false;
	return true;
}

bool UWTAVisitSubsystem::TakePendingToast(FText& OutText)
{
	if (PendingToast.IsEmpty())
	{
		return false;
	}
	OutText = PendingToast;
	PendingToast = FText::GetEmpty();
	return true;
}

bool UWTAVisitSubsystem::TakePendingPlayTest(FString& OutPhases)
{
	if (PendingPlayTest.IsEmpty())
	{
		return false;
	}
	OutPhases = PendingPlayTest;
	PendingPlayTest.Reset();
	return true;
}
