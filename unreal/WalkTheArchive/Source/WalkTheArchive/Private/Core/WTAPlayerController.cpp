// Walk the Archive - the player controller: input, widgets, panels, travel.
//
// Enhanced Input is built here in code. The controller's InputComponent is a UEnhancedInputComponent only when
// Config/DefaultInput.ini sets DefaultInputComponentClass=/Script/EnhancedInput.EnhancedInputComponent (and
// DefaultPlayerInputClass=/Script/EnhancedInput.EnhancedPlayerInput); SetupInputComponent logs an error otherwise.

#include "Core/WTAPlayerController.h"
#include "Core/WTACharacter.h"
#include "Core/WTASettings.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayTest.h"
#include "Data/WTATypes.h"
#include "Interaction/WTAInteractionComponent.h"
#include "Systems/WTAContentSubsystem.h"
#include "Systems/WTADialogueSubsystem.h"
#include "Systems/WTAProgressSubsystem.h"
#include "Systems/WTARoomSubsystem.h"
#include "Systems/WTATourSubsystem.h"
#include "UI/WTAChatWidget.h"
#include "UI/WTAHudWidget.h"
#include "UI/WTAMenuWidget.h"
#include "UI/WTAPanelWidget.h"
#include "World/WTAExhibitActor.h"
#include "Blueprint/UserWidget.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/GameViewportClient.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "GameFramework/Pawn.h"
#include "InputAction.h"
#include "InputActionValue.h"
#include "InputCoreTypes.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "InputTriggers.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "NavigationSystem.h"
#include "TimerManager.h"
#include "UnrealClient.h"
#include "Widgets/SViewport.h"
#include "Widgets/SWidget.h"

namespace
{
	UInputAction* MakeAction(UObject* Outer, const TCHAR* Name, EInputActionValueType Type)
	{
		UInputAction* Action = NewObject<UInputAction>(Outer, FName(Name));
		Action->ValueType = Type;
		return Action;
	}

	/** Route a 1D key (W/S) into the Y axis of a 2D action. */
	void AddSwizzle(UObject* Outer, FEnhancedActionKeyMapping& Mapping)
	{
		UInputModifierSwizzleAxis* Swizzle = NewObject<UInputModifierSwizzleAxis>(Outer);
		Swizzle->Order = EInputAxisSwizzle::YXZ;
		Mapping.Modifiers.Add(Swizzle);
	}

	void AddNegate(UObject* Outer, FEnhancedActionKeyMapping& Mapping, bool bX, bool bY)
	{
		UInputModifierNegate* Negate = NewObject<UInputModifierNegate>(Outer);
		Negate->bX = bX;
		Negate->bY = bY;
		Negate->bZ = false;
		Mapping.Modifiers.Add(Negate);
	}

	void AddDeadZone(UObject* Outer, FEnhancedActionKeyMapping& Mapping)
	{
		UInputModifierDeadZone* DeadZone = NewObject<UInputModifierDeadZone>(Outer);
		DeadZone->LowerThreshold = 0.2f;
		DeadZone->UpperThreshold = 1.f;
		DeadZone->Type = EDeadZoneType::Radial;
		Mapping.Modifiers.Add(DeadZone);
	}

	/** Add the mapping context to the local player's Enhanced Input subsystem (once). */
	void EnsureContextAdded(APlayerController* PC, UInputMappingContext* Context)
	{
		if (PC == nullptr || Context == nullptr)
		{
			return;
		}
		ULocalPlayer* LocalPlayer = PC->GetLocalPlayer();
		UEnhancedInputLocalPlayerSubsystem* Subsystem = LocalPlayer ? LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>() : nullptr;
		// AddMappingContext stores the context in a map, so calling it again (SetupInputComponent, then BeginPlay) is harmless.
		if (Subsystem != nullptr)
		{
			Subsystem->AddMappingContext(Context, 0);
		}
	}

	/** The floor point under a view: the eye location dropped by the eye height, snapped to the NavMesh when there is one. */
	FVector FloorPointFor(const UWorld* World, const FVector& EyeLocation, float EyeHeight)
	{
		FVector Floor = EyeLocation;
		Floor.Z -= EyeHeight;
		if (UNavigationSystemV1* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(const_cast<UWorld*>(World)))
		{
			FNavLocation Projected;
			if (Nav->ProjectPointToNavigation(Floor, Projected, FVector(150.f, 150.f, 250.f)))
			{
				Floor = Projected.Location;
			}
		}
		return Floor;
	}
}

AWTAPlayerController::AWTAPlayerController()
{
	PrimaryActorTick.bCanEverTick = true;
	Interaction = CreateDefaultSubobject<UWTAInteractionComponent>(TEXT("Interaction"));
	bShowMouseCursor = false;
	bEnableClickEvents = true;
	bEnableMouseOverEvents = true;
}

// --- Lifecycle -------------------------------------------------------------------

void AWTAPlayerController::BeginPlay()
{
	Super::BeginPlay();
	if (!IsLocalController())
	{
		return;
	}

	// Look limits: enough to see the floor and the ceiling, as a PC first-person game expects.
	if (PlayerCameraManager != nullptr)
	{
		PlayerCameraManager->ViewPitchMin = -80.f;
		PlayerCameraManager->ViewPitchMax = 80.f;
	}

	CreateInputObjects();
	EnsureContextAdded(this, MappingContext);
	CreateWidgets();

	if (Interaction != nullptr)
	{
		Interaction->OnHoverChanged.AddDynamic(this, &AWTAPlayerController::HandleHoverChanged);
	}
	if (UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this))
	{
		Progress->OnBadgeAwarded.AddDynamic(this, &AWTAPlayerController::HandleBadgeAwarded);
		Progress->OnTokenCollected.AddDynamic(this, &AWTAPlayerController::HandleTokenCollected);
		Progress->OnProgressReset.AddDynamic(this, &AWTAPlayerController::HandleProgressReset);
		if (Hud != nullptr)
		{
			Hud->SetBadgeCount(Progress->NumBadges(), Progress->TotalBadges());
		}
	}
	if (UWTATourSubsystem* Tour = UWTATourSubsystem::Get(this))
	{
		Tour->OnTourChanged.AddDynamic(this, &AWTAPlayerController::HandleTourChanged);
	}
	if (UWTARoomSubsystem* Rooms = UWTARoomSubsystem::Get(this))
	{
		Rooms->OnRoomChanged.AddDynamic(this, &AWTAPlayerController::HandleRoomChanged);
		// Name the starting room even before any room volume overlaps.
		if (Rooms->GetCurrentRoom().IsNone() && GetPawn() != nullptr)
		{
			const FName StartRoom = Rooms->RoomAt(GetPawn()->GetActorLocation());
			if (!StartRoom.IsNone())
			{
				Rooms->EnterRoom(StartRoom);
			}
		}
	}

	const UWTASettings* Settings = UWTASettings::Get();
	if (Settings != nullptr && Settings->bShowIntroMenu && Menu != nullptr)
	{
		Menu->Open(true);
	}
	SetUIMode(IsAnyPanelOpen());
}

void AWTAPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();

	// SetupInputComponent runs before BeginPlay, so the actions are built here on first use.
	CreateInputObjects();
	EnsureContextAdded(this, MappingContext);

	UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(InputComponent);
	if (Input == nullptr)
	{
		UE_LOG(LogWTA, Error, TEXT("InputComponent is not a UEnhancedInputComponent. Set DefaultInputComponentClass=/Script/EnhancedInput.EnhancedInputComponent in Config/DefaultInput.ini."));
		return;
	}

	Input->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AWTAPlayerController::OnMove);
	Input->BindAction(LookAction, ETriggerEvent::Triggered, this, &AWTAPlayerController::OnLook);
	Input->BindAction(LookStickAction, ETriggerEvent::Triggered, this, &AWTAPlayerController::OnLookStick);
	Input->BindAction(JumpAction, ETriggerEvent::Started, this, &AWTAPlayerController::OnJump);
	Input->BindAction(JumpAction, ETriggerEvent::Completed, this, &AWTAPlayerController::OnJumpEnd);
	Input->BindAction(SprintAction, ETriggerEvent::Started, this, &AWTAPlayerController::OnSprint);
	Input->BindAction(SprintAction, ETriggerEvent::Completed, this, &AWTAPlayerController::OnSprintEnd);
	Input->BindAction(InteractAction, ETriggerEvent::Started, this, &AWTAPlayerController::OnInteract);
	Input->BindAction(BackAction, ETriggerEvent::Started, this, &AWTAPlayerController::OnBack);
	Input->BindAction(ToggleCursorAction, ETriggerEvent::Started, this, &AWTAPlayerController::OnToggleCursor);
	Input->BindAction(TourNextAction, ETriggerEvent::Started, this, &AWTAPlayerController::OnTourNext);
	Input->BindAction(PlacesAction, ETriggerEvent::Started, this, &AWTAPlayerController::OnPlaces);
	Input->BindAction(ChatAction, ETriggerEvent::Started, this, &AWTAPlayerController::OnChat);
}

void AWTAPlayerController::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// Standing between two facing wax scenes: the plaque and the narration follow where the player looks.
	if (InsideStageIds.Num() > 1)
	{
		UpdateFacedStage();
	}

	AWTACharacter* PlayerCharacter = GetWTACharacter();
	if (PlayerCharacter == nullptr)
	{
		return;
	}

	if (PlayerCharacter->IsAutoWalking())
	{
		FRotator Rotation = GetControlRotation().GetNormalized();
		bool bChanged = false;
		// Long trips: turn toward the direction of travel until the last 1.8 m (web travelFace, k = 3).
		if (bFaceTravelDirection)
		{
			const FVector Velocity = PlayerCharacter->GetVelocity();
			const float Remaining = bHasPendingView ? static_cast<float>(FVector::Dist2D(PlayerCharacter->GetActorLocation(), PendingView.Location)) : TNumericLimits<float>::Max();
			if (Velocity.Size2D() > 50.0 && Remaining > 180.f)
			{
				const float TargetYaw = static_cast<float>(Velocity.Rotation().Yaw);
				const float YawDelta = FMath::FindDeltaAngleDegrees(static_cast<float>(Rotation.Yaw), TargetYaw);
				Rotation.Yaw += YawDelta * (1.f - FMath::Exp(-3.f * DeltaSeconds));
				bChanged = true;
			}
		}
		// The pitch eases toward the view's pitch during the walk (web facePitch).
		if (bHasPendingView)
		{
			const float PitchDelta = FMath::FindDeltaAngleDegrees(static_cast<float>(Rotation.Pitch), PendingView.Pitch);
			Rotation.Pitch += PitchDelta * (1.f - FMath::Exp(-FaceViewRate * DeltaSeconds));
			bChanged = true;
		}
		if (bChanged)
		{
			SetControlRotation(Rotation);
		}
	}
	else
	{
		bFaceTravelDirection = false;
		if (bHasPendingView)
		{
			// Arrived: ease the camera onto the view with 1 - exp(-4.5 dt), then snap and forget it.
			FRotator Rotation = GetControlRotation().GetNormalized();
			const float Alpha = 1.f - FMath::Exp(-FaceViewRate * DeltaSeconds);
			const float YawDelta = FMath::FindDeltaAngleDegrees(static_cast<float>(Rotation.Yaw), PendingView.Yaw);
			const float PitchDelta = FMath::FindDeltaAngleDegrees(static_cast<float>(Rotation.Pitch), PendingView.Pitch);
			if (FMath::Abs(YawDelta) < 0.15f && FMath::Abs(PitchDelta) < 0.15f)
			{
				SetControlRotation(FRotator(PendingView.Pitch, PendingView.Yaw, 0.f));
				bHasPendingView = false;
			}
			else
			{
				Rotation.Yaw += YawDelta * Alpha;
				Rotation.Pitch += PitchDelta * Alpha;
				SetControlRotation(Rotation);
			}
		}
	}
}

void AWTAPlayerController::OnPossess(APawn* InPawn)
{
	Super::OnPossess(InPawn);
	// Start where the web started: the lobby spawn from the settings (the pawn itself spawns at the PlayerStart).
	const UWTASettings* Settings = UWTASettings::Get();
	AWTACharacter* PlayerCharacter = Cast<AWTACharacter>(InPawn);
	if (Settings != nullptr && PlayerCharacter != nullptr && Settings->SpawnView.bValid)
	{
		PlayerCharacter->TeleportToView(Settings->SpawnView);
	}
	bHasPendingView = false;
	bFaceTravelDirection = false;
}

// --- Setup -----------------------------------------------------------------------

void AWTAPlayerController::CreateInputObjects()
{
	if (MappingContext != nullptr)
	{
		return;
	}
	MappingContext = NewObject<UInputMappingContext>(this, FName(TEXT("IMC_WalkTheArchive")));

	MoveAction         = MakeAction(this, TEXT("IA_Move"), EInputActionValueType::Axis2D);
	LookAction         = MakeAction(this, TEXT("IA_Look"), EInputActionValueType::Axis2D);
	LookStickAction    = MakeAction(this, TEXT("IA_LookStick"), EInputActionValueType::Axis2D);
	JumpAction         = MakeAction(this, TEXT("IA_Jump"), EInputActionValueType::Boolean);
	SprintAction       = MakeAction(this, TEXT("IA_Sprint"), EInputActionValueType::Boolean);
	InteractAction     = MakeAction(this, TEXT("IA_Interact"), EInputActionValueType::Boolean);
	BackAction         = MakeAction(this, TEXT("IA_Back"), EInputActionValueType::Boolean);
	ToggleCursorAction = MakeAction(this, TEXT("IA_ToggleCursor"), EInputActionValueType::Boolean);
	TourNextAction     = MakeAction(this, TEXT("IA_TourNext"), EInputActionValueType::Boolean);
	PlacesAction       = MakeAction(this, TEXT("IA_Places"), EInputActionValueType::Boolean);
	ChatAction         = MakeAction(this, TEXT("IA_Chat"), EInputActionValueType::Boolean);

	// Move: X = right, Y = forward. W/S go through a swizzle into Y; S and A are negated.
	AddSwizzle(this, MappingContext->MapKey(MoveAction, EKeys::W));
	{
		FEnhancedActionKeyMapping& Mapping = MappingContext->MapKey(MoveAction, EKeys::S);
		AddNegate(this, Mapping, true, true);
		AddSwizzle(this, Mapping);
	}
	AddNegate(this, MappingContext->MapKey(MoveAction, EKeys::A), true, false);
	MappingContext->MapKey(MoveAction, EKeys::D);
	AddDeadZone(this, MappingContext->MapKey(MoveAction, EKeys::Gamepad_Left2D));

	// Look: the mouse as the Enhanced Input templates map it (Y negated); bInvertMouseY flips it back if needed.
	AddNegate(this, MappingContext->MapKey(LookAction, EKeys::Mouse2D), false, true);
	{
		// Same Y sign as the mouse (stick up = look up).
		FEnhancedActionKeyMapping& Mapping = MappingContext->MapKey(LookStickAction, EKeys::Gamepad_Right2D);
		AddDeadZone(this, Mapping);
		AddNegate(this, Mapping, false, true);
	}

	MappingContext->MapKey(JumpAction, EKeys::SpaceBar);
	MappingContext->MapKey(JumpAction, EKeys::Gamepad_FaceButton_Bottom);
	MappingContext->MapKey(SprintAction, EKeys::LeftShift);
	MappingContext->MapKey(SprintAction, EKeys::Gamepad_LeftThumbstick);
	MappingContext->MapKey(InteractAction, EKeys::LeftMouseButton);
	MappingContext->MapKey(InteractAction, EKeys::E);
	MappingContext->MapKey(InteractAction, EKeys::Gamepad_FaceButton_Left);
	// Escape is taken by the editor while playing in the editor; use the gamepad B button or a packaged build.
	MappingContext->MapKey(BackAction, EKeys::Escape);
	MappingContext->MapKey(BackAction, EKeys::Gamepad_FaceButton_Right);
	MappingContext->MapKey(ToggleCursorAction, EKeys::Tab);
	MappingContext->MapKey(TourNextAction, EKeys::T);
	MappingContext->MapKey(PlacesAction, EKeys::M);
	MappingContext->MapKey(ChatAction, EKeys::Enter);
}

void AWTAPlayerController::CreateWidgets()
{
	if (Hud == nullptr)
	{
		Hud = CreateWidget<UWTAHudWidget>(this, UWTAHudWidget::StaticClass());
		if (Hud != nullptr)
		{
			Hud->AddToViewport(0);
		}
	}
	if (Panel == nullptr)
	{
		Panel = CreateWidget<UWTAPanelWidget>(this, UWTAPanelWidget::StaticClass());
		if (Panel != nullptr)
		{
			Panel->AddToViewport(10);
			Panel->Close();
		}
	}
	if (Chat == nullptr)
	{
		Chat = CreateWidget<UWTAChatWidget>(this, UWTAChatWidget::StaticClass());
		if (Chat != nullptr)
		{
			Chat->AddToViewport(20);
			Chat->Close();
		}
	}
	if (Menu == nullptr)
	{
		Menu = CreateWidget<UWTAMenuWidget>(this, UWTAMenuWidget::StaticClass());
		if (Menu != nullptr)
		{
			Menu->AddToViewport(30);
			Menu->Close();
		}
	}
}

void AWTAPlayerController::UpdateInputMode()
{
	const bool bPanelOpen = IsAnyPanelOpen();
	const bool bCursor = bPanelOpen || bCursorFree;
	if (bCursor)
	{
		FInputModeGameAndUI Mode;
		Mode.SetHideCursorDuringCapture(false);
		Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
		// Keyboard focus goes to the top-most open widget so arrow keys, Enter and typing land there.
		if (Menu != nullptr && Menu->IsOpen())
		{
			Mode.SetWidgetToFocus(Menu->TakeWidget());
		}
		else if (Chat != nullptr && Chat->IsOpen())
		{
			Mode.SetWidgetToFocus(Chat->TakeWidget());
		}
		else if (Panel != nullptr && Panel->IsOpen())
		{
			Mode.SetWidgetToFocus(Panel->TakeWidget());
		}
		else if (UGameViewportClient* GameViewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr)
		{
			// Cursor free with nothing open (Tab or a running tour): give the keys back to the game. Without a widget
			// to focus, Slate keeps focus on the panel that just closed and Esc, T, Tab and WASD do nothing.
			Mode.SetWidgetToFocus(GameViewport->GetGameViewportWidget());
		}
		SetInputMode(Mode);
		bShowMouseCursor = true;
	}
	else
	{
		FInputModeGameOnly Mode;
		Mode.SetConsumeCaptureMouseDown(false);
		SetInputMode(Mode);
		bShowMouseCursor = false;
	}
	if (Interaction != nullptr)
	{
		Interaction->bUseMouseCursor = bCursor;
	}
	if (Hud != nullptr)
	{
		Hud->SetCrosshairVisible(!bCursor);
	}
}

void AWTAPlayerController::RefreshTourBar()
{
	UWTATourSubsystem* Tour = UWTATourSubsystem::Get(this);
	if (Hud != nullptr && Tour != nullptr && Tour->IsTouring())
	{
		Hud->SetTourVisible(!IsAnyPanelOpen());
	}
}

// --- Panels ----------------------------------------------------------------------

void AWTAPlayerController::OpenExhibit(FName ItemId)
{
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	if (Panel == nullptr || Content == nullptr || Content->FindExhibit(ItemId) == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("OpenExhibit: no exhibit '%s'"), *ItemId.ToString());
		return;
	}
	if (Chat != nullptr && Chat->IsOpen())
	{
		Chat->Close();
	}
	Panel->ShowExhibit(ItemId);
	if (UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this))
	{
		Progress->NoteExhibit(ItemId);
	}
	SetUIMode(true);
}

void AWTAPlayerController::StepExhibit(int32 Delta)
{
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	if (Panel == nullptr || Content == nullptr || Panel->GetMode() != EWTAPanelMode::Exhibit)
	{
		return;
	}
	const FName CurrentId = Panel->GetCurrentId();
	const FWTAExhibitRow* Current = Content->FindExhibit(CurrentId);
	if (Current == nullptr)
	{
		return;
	}
	const TArray<FName> List = Current->bWax ? Content->GetWaxExhibitIds() : Content->GetGalleryExhibitIds();
	const int32 Index = List.IndexOfByKey(CurrentId);
	if (Index == INDEX_NONE || List.Num() == 0)
	{
		return;
	}
	const int32 NewIndex = ((Index + Delta) % List.Num() + List.Num()) % List.Num();
	const FName NewId = List[NewIndex];
	if (const FWTAExhibitRow* Next = Content->FindExhibit(NewId))
	{
		GoToView(Next->View, true);
	}
	OpenExhibit(NewId);
}

void AWTAPlayerController::OpenBook(FName BookId, int32 Page)
{
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	const FWTABookRow* Book = Content ? Content->FindBook(BookId) : nullptr;
	if (Panel == nullptr || Book == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("OpenBook: no book '%s'"), *BookId.ToString());
		return;
	}
	const int32 ClampedPage = FMath::Clamp(Page, -1, Book->Pages.Num() - 1);
	if (Chat != nullptr && Chat->IsOpen())
	{
		Chat->Close();
	}
	Panel->ShowBook(BookId, ClampedPage);
	if (ClampedPage >= 0)
	{
		if (UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this))
		{
			Progress->NotePage(BookId, ClampedPage);
		}
	}
	SetUIMode(true);
}

void AWTAPlayerController::OpenStation(FName StationId)
{
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	if (Panel == nullptr || Content == nullptr || Content->FindStation(StationId) == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("OpenStation: no station '%s'"), *StationId.ToString());
		return;
	}
	if (Chat != nullptr && Chat->IsOpen())
	{
		Chat->Close();
	}
	Panel->ShowStation(StationId);
	SetUIMode(true);
}

void AWTAPlayerController::OpenRide(FName RideId)
{
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	if (Panel == nullptr || Content == nullptr || Content->FindRide(RideId) == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("OpenRide: no ride '%s'"), *RideId.ToString());
		return;
	}
	if (Chat != nullptr && Chat->IsOpen())
	{
		Chat->Close();
	}
	Panel->ShowRide(RideId);
	SetUIMode(true);
}

void AWTAPlayerController::OpenBadges()
{
	if (Panel == nullptr)
	{
		return;
	}
	if (Chat != nullptr && Chat->IsOpen())
	{
		Chat->Close();
	}
	Panel->ShowBadges();
	SetUIMode(true);
}

void AWTAPlayerController::OpenPlaces()
{
	if (Panel == nullptr)
	{
		return;
	}
	if (Chat != nullptr && Chat->IsOpen())
	{
		Chat->Close();
	}
	Panel->ShowPlaces();
	SetUIMode(true);
}

void AWTAPlayerController::OpenStaffChat(FName StaffId)
{
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	if (Chat == nullptr || Content == nullptr || Content->FindStaff(StaffId) == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("OpenStaffChat: no staff '%s'"), *StaffId.ToString());
		return;
	}
	if (Panel != nullptr && Panel->IsOpen())
	{
		Panel->Close();
	}
	Chat->Open(StaffId);
	SetUIMode(true);
	Chat->FocusInput();
}

bool AWTAPlayerController::CloseTopPanel()
{
	if (Menu != nullptr && Menu->IsOpen())
	{
		Menu->Close();
		SetUIMode(IsAnyPanelOpen());
		return true;
	}
	if (Chat != nullptr && Chat->IsOpen())
	{
		Chat->Close();
		SetUIMode(IsAnyPanelOpen());
		return true;
	}
	if (Panel != nullptr && Panel->IsOpen())
	{
		Panel->Close();
		SetUIMode(IsAnyPanelOpen());
		return true;
	}
	if (UWTATourSubsystem* Tour = UWTATourSubsystem::Get(this))
	{
		if (Tour->IsTouring())
		{
			Tour->End();
			return true;
		}
	}
	return false;
}

void AWTAPlayerController::ToggleMenu()
{
	if (Menu == nullptr)
	{
		return;
	}
	if (Menu->IsOpen())
	{
		Menu->Close();
		SetUIMode(IsAnyPanelOpen());
	}
	else
	{
		Menu->Open(false);
		SetUIMode(true);
	}
}

bool AWTAPlayerController::IsAnyPanelOpen() const
{
	return (Panel != nullptr && Panel->IsOpen()) || (Chat != nullptr && Chat->IsOpen()) || (Menu != nullptr && Menu->IsOpen());
}

// --- HUD messages ------------------------------------------------------------------

void AWTAPlayerController::ShowToast(const FText& Text, float Seconds)
{
	if (Hud == nullptr || Text.IsEmpty())
	{
		return;
	}
	const UWTASettings* Settings = UWTASettings::Get();
	const float Duration = Seconds > 0.f ? Seconds : (Settings ? Settings->ToastSeconds : 3.4f);
	Hud->ShowToast(Text, Duration);
}

void AWTAPlayerController::ShowCaption(const FText& Text)
{
	if (Hud != nullptr)
	{
		Hud->ShowCaption(Text);
	}
}

void AWTAPlayerController::ShowHint(const FText& Text)
{
	if (Hud == nullptr || Text.IsEmpty())
	{
		return;
	}
	const UWTASettings* Settings = UWTASettings::Get();
	Hud->ShowHint(Text, Settings ? Settings->HintSeconds : 6.f);
}

// --- Walk-up story plaque -------------------------------------------------------------

/** The opening sentences of a story, up to about MaxChars, ending on a full stop when there is one. */
static FText WTAStorySummary(const FText& Text, int32 MaxChars)
{
	const FString Full = Text.ToString();
	if (Full.Len() <= MaxChars)
	{
		return Text;
	}
	int32 Cut = INDEX_NONE;
	for (int32 i = 0; i + 1 < Full.Len() && i < MaxChars; ++i)
	{
		const TCHAR C = Full[i];
		if ((C == TEXT('.') || C == TEXT('!') || C == TEXT('?')) && Full[i + 1] == TEXT(' '))
		{
			Cut = i + 1;
		}
	}
	if (Cut != INDEX_NONE && Cut >= 60)
	{
		return FText::FromString(Full.Left(Cut));
	}
	// No sentence break early enough: cut at a word and add an ellipsis.
	const FString Head = Full.Left(MaxChars);
	int32 Space = INDEX_NONE;
	Head.FindLastChar(TEXT(' '), Space);
	return FText::FromString((Space > 0 ? Head.Left(Space) : Head) + FString(TEXT("...")));
}

void AWTAPlayerController::ShowStoryPlaque(FName ItemId)
{
	ShownStoryId = ItemId;
	if (Hud == nullptr)
	{
		return;
	}
	const UWTAContentSubsystem* Data = UWTAContentSubsystem::Get(this);
	const FWTAExhibitRow* Row = (Data != nullptr && !ItemId.IsNone()) ? Data->FindExhibit(ItemId) : nullptr;
	if (Row == nullptr)
	{
		Hud->HideStory();
		return;
	}
	const FText Kicker = (Row->bWax && !Row->Hall.IsEmpty()) ? Row->Hall : Row->Kind;
	const FText Hint = bCursorFree
		? FText::FromString(TEXT("Click to read the full story"))
		: FText::FromString(TEXT("Press E to read the full story"));
	Hud->ShowStory(Kicker, Row->Date, Row->Title, WTAStorySummary(Row->Description, 200), Hint);
}

void AWTAPlayerController::SetStageStory(FName ItemId, bool bInside)
{
	if (ItemId.IsNone())
	{
		return;
	}
	if (bInside)
	{
		InsideStageIds.AddUnique(ItemId);
	}
	else
	{
		InsideStageIds.Remove(ItemId);
	}
	UpdateFacedStage();
}

void AWTAPlayerController::UpdateFacedStage()
{
	FName Best = NAME_None;
	if (InsideStageIds.Num() == 1)
	{
		Best = InsideStageIds[0];
	}
	else if (InsideStageIds.Num() > 1)
	{
		// Scenes face each other across the aisle: pick the stage most in front of the camera.
		const UWTAContentSubsystem* Data = UWTAContentSubsystem::Get(this);
		FVector ViewLocation;
		FRotator ViewRotation;
		GetPlayerViewPoint(ViewLocation, ViewRotation);
		const FVector Forward = ViewRotation.Vector().GetSafeNormal2D();
		float BestDot = -2.f;
		for (const FName& Id : InsideStageIds)
		{
			const FWTAExhibitRow* ExhibitRow = Data != nullptr ? Data->FindExhibit(Id) : nullptr;
			const FName SceneName = (ExhibitRow != nullptr && !ExhibitRow->WaxSceneId.IsNone()) ? ExhibitRow->WaxSceneId : Id;
			const FWTAWaxSceneRow* SceneRow = Data != nullptr ? Data->FindWaxScene(SceneName) : nullptr;
			if (SceneRow == nullptr)
			{
				continue;
			}
			const float Dot = static_cast<float>(FVector::DotProduct(Forward, (SceneRow->StageLocation - ViewLocation).GetSafeNormal2D()));
			if (Dot > BestDot)
			{
				BestDot = Dot;
				Best = Id;
			}
		}
		if (Best.IsNone())
		{
			Best = InsideStageIds.Last();
		}
	}
	if (Best != StageStoryId)
	{
		StageStoryId = Best;
		RefreshStoryPlaque();
	}
}

void AWTAPlayerController::RefreshStoryPlaque()
{
	const FName Wanted = !HoverStoryId.IsNone() ? HoverStoryId : StageStoryId;
	if (Wanted != ShownStoryId)
	{
		ShowStoryPlaque(Wanted);
	}
}

// --- Actions and travel ------------------------------------------------------------

void AWTAPlayerController::RunAction(FName Action, FName Arg)
{
	if (Action.IsNone())
	{
		return;
	}
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	if (Action == WTAAction::GoPlace())
	{
		// The chat is a card in the middle of the screen: put it away so the player sees where they are going.
		if (Chat != nullptr && Chat->IsOpen())
		{
			Chat->Close();
			SetUIMode(IsAnyPanelOpen());
		}
		GoToPlace(Arg);
	}
	else if (Action == WTAAction::OpenItem())
	{
		if (const FWTAExhibitRow* Exhibit = Content ? Content->FindExhibit(Arg) : nullptr)
		{
			GoToView(Exhibit->View, true);
			OpenExhibit(Arg);
		}
	}
	else if (Action == WTAAction::OpenBook())
	{
		// "<book>" opens on the cover with the table of contents; "<book>#<page index>" (a staff answer that named
		// a page) opens at that page.
		const FString ArgString = Arg.ToString();
		FString BookId = ArgString;
		FString PagePart;
		int32 PageIndex = -1;
		if (ArgString.Split(TEXT("#"), &BookId, &PagePart) && PagePart.IsNumeric())
		{
			PageIndex = FCString::Atoi(*PagePart);
		}
		OpenBook(FName(*BookId), PageIndex);
	}
	else if (Action == WTAAction::OpenStation())
	{
		if (const FWTAStationRow* Station = Content ? Content->FindStation(Arg) : nullptr)
		{
			GoToView(Station->View, true);
			OpenStation(Arg);
		}
	}
	else if (Action == WTAAction::OpenRide())
	{
		OpenRide(Arg);
	}
	else if (Action == WTAAction::StartTour())
	{
		if (UWTATourSubsystem* Tour = UWTATourSubsystem::Get(this))
		{
			Tour->Start();
		}
	}
	else if (Action == WTAAction::OpenBadges())
	{
		OpenBadges();
	}
	else
	{
		UE_LOG(LogWTA, Warning, TEXT("RunAction: unknown action '%s' (%s)"), *Action.ToString(), *Arg.ToString());
	}
}

void AWTAPlayerController::GoToView(const FWTAView& View, bool bWalk)
{
	if (!View.bValid)
	{
		return;
	}
	AWTACharacter* PlayerCharacter = GetWTACharacter();
	if (PlayerCharacter == nullptr)
	{
		return;
	}
	if (!bWalk)
	{
		PlayerCharacter->TeleportToView(View);
		bHasPendingView = false;
		bFaceTravelDirection = false;
		return;
	}

	const FVector Dest = FloorPointFor(GetWorld(), View.Location, PlayerCharacter->EyeHeight);
	const float Distance = static_cast<float>(FVector::Dist2D(PlayerCharacter->GetActorLocation(), Dest));
	PlayerCharacter->WalkTo(Dest);
	PendingView = View;
	bHasPendingView = true;
	if (PlayerCharacter->IsAutoWalking())
	{
		bFaceTravelDirection = Distance > 400.f;
	}
	else
	{
		// No path (no NavMesh yet, or already there): a long trip teleports, a short one just turns.
		bFaceTravelDirection = false;
		if (Distance > 150.f)
		{
			PlayerCharacter->TeleportToView(View);
			bHasPendingView = false;
		}
	}
}

void AWTAPlayerController::GoToPlace(FName PlaceId)
{
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	const FWTAPlaceRow* Place = Content ? Content->FindPlace(PlaceId) : nullptr;
	if (Place == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("GoToPlace: no place '%s'"), *PlaceId.ToString());
		return;
	}
	GoToView(Place->View, true);
}

void AWTAPlayerController::SetUIMode(bool bPanelOpen)
{
	bUIMode = bPanelOpen;
	if (bUIMode)
	{
		// A panel takes the keys: stop sprinting so the player does not run off while reading.
		if (AWTACharacter* PlayerCharacter = GetWTACharacter())
		{
			PlayerCharacter->SetSprinting(false);
		}
	}
	UpdateInputMode();
	RefreshTourBar();
	// The plaque steps aside while a card, chat or menu is open and comes back after.
	if (Hud != nullptr)
	{
		Hud->SetStoryVisible(!bPanelOpen);
	}
	OnUIModeChanged.Broadcast(bPanelOpen);
}

void AWTAPlayerController::SetCursorFree(bool bFree)
{
	if (bCursorFree == bFree)
	{
		return;
	}
	bCursorFree = bFree;
	UpdateInputMode();
	if (bCursorFree && !bUIMode)
	{
		ShowToast(FText::FromString(TEXT("Cursor free: click the floor to walk, click things to open them. Tab goes back to mouse look.")), 0.f);
	}
	// The plaque's key hint ("Press E" / "Click") follows the cursor mode.
	if (!ShownStoryId.IsNone())
	{
		ShowStoryPlaque(ShownStoryId);
	}
}

AWTACharacter* AWTAPlayerController::GetWTACharacter() const
{
	return Cast<AWTACharacter>(GetPawn());
}

void AWTAPlayerController::WTAShotTour(float SecondsPerShot)
{
	UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	if (Content == nullptr)
	{
		return;
	}
	ShotTourViews.Reset();
	ShotTourSeconds = FMath::Max(SecondsPerShot, 1.f);
	for (const FName& Name : Content->GetRowNames(EWTATable::Places))
	{
		const FWTAPlaceRow* Row = Content->FindPlace(Name);
		if (Row != nullptr && !Row->View.Location.IsNearlyZero())
		{
			ShotTourViews.Emplace(TEXT("place_") + Name.ToString(), Row->View);
		}
	}
	for (const FName& Name : Content->GetRowNames(EWTATable::Staff))
	{
		const FWTAStaffRow* Row = Content->FindStaff(Name);
		if (Row != nullptr && Row->TalkView.bValid)
		{
			ShotTourViews.Emplace(TEXT("staff_") + Name.ToString(), Row->TalkView);
		}
	}
	for (const FName& Name : Content->GetRowNames(EWTATable::WaxScenes))
	{
		if (const FWTAWaxSceneRow* Row = Content->FindWaxScene(Name))
		{
			// From the aisle, 4.2 m in front of the stage, at eye height, looking back at the reenactors.
			const FVector Forward = FRotator(0.f, Row->StageYaw, 0.f).Vector();
			FWTAView View;
			View.Location = Row->StageLocation + Forward * 420.f;
			View.Location.Z = 162.f;
			View.Yaw = Row->StageYaw + 180.f;
			View.Pitch = -8.f;
			View.bValid = true;
			ShotTourViews.Emplace(TEXT("wax_") + Name.ToString(), View);
		}
	}
	while (CloseTopPanel())
	{
	}
	ShotTourIndex = 0;
	UE_LOG(LogWTA, Display, TEXT("WTA_SHOTTOUR start %d views, %.1f s each"), ShotTourViews.Num(), ShotTourSeconds);
	ShotTourTeleport();
}

void AWTAPlayerController::WTAChatTest()
{
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	UWTADialogueSubsystem* Dialogue = UWTADialogueSubsystem::Get(this);
	if (Content == nullptr || Dialogue == nullptr)
	{
		return;
	}
	// Each staff member's own chips, then questions any visitor might type: the lines of Saved/QA/chat_questions.txt
	// when that file exists (blank lines and lines starting with # are skipped), else a short built-in list.
	TArray<FString> Common;
	TArray<FString> Lines;
	if (FFileHelper::LoadFileToStringArray(Lines, *(FPaths::ProjectSavedDir() / TEXT("QA") / TEXT("chat_questions.txt"))))
	{
		for (const FString& Line : Lines)
		{
			const FString Trimmed = Line.TrimStartAndEnd();
			if (!Trimmed.IsEmpty() && !Trimmed.StartsWith(TEXT("#")))
			{
				Common.Add(Trimmed);
			}
		}
	}
	if (Common.Num() == 0)
	{
		Common = { TEXT("hello"), TEXT("who are you"), TEXT("what can you do"), TEXT("where is the library"), TEXT("take me to the yard"),
			TEXT("how do I move"), TEXT("tell me about Nevada"), TEXT("who runs XRLibraries"), TEXT("how many exhibits are there"),
			TEXT("what happened in 2019"), TEXT("recommend a book about oceans"), TEXT("is the coaster scary") };
	}
	int32 Count = 0;
	for (const FName& Name : Content->GetRowNames(EWTATable::Staff))
	{
		TArray<FString> Questions;
		for (const FText& Chip : Dialogue->GetChips(Name))
		{
			Questions.Add(Chip.ToString());
		}
		Questions.Append(Common);
		for (const FString& Question : Questions)
		{
			const FWTAReply Reply = Dialogue->Ask(Name, Question);
			const FString Offer = Reply.bOffer ? FString::Printf(TEXT(" offered: %s"), *Reply.OfferLabel.ToString()) : FString();
			UE_LOG(LogWTA, Display, TEXT("WTA_CHAT %s | %s -> %s [%s %s%s]"), *Name.ToString(), *Question, *Reply.Text.ToString(),
				*Reply.Action.ToString(), *Reply.ActionArg.ToString(), *Offer);
			++Count;
		}
	}
	UE_LOG(LogWTA, Display, TEXT("WTA_CHAT done %d questions"), Count);
}

void AWTAPlayerController::WTAChatShots(float SecondsPerShot)
{
	ChatShots.Reset();
	ChatShotClicks.Reset();
	bChatShotClicked = false;
	ChatShotSeconds = FMath::Max(SecondsPerShot, 1.f);
	TArray<FString> Lines;
	if (FFileHelper::LoadFileToStringArray(Lines, *(FPaths::ProjectSavedDir() / TEXT("QA") / TEXT("chat_shots.txt"))))
	{
		for (const FString& Line : Lines)
		{
			// "<staff> | <question>" or "<staff> | <question> | click"
			TArray<FString> Parts;
			Line.ParseIntoArray(Parts, TEXT("|"));
			for (FString& Part : Parts)
			{
				Part.TrimStartAndEndInline();
			}
			if (Parts.Num() >= 2 && !Parts[0].StartsWith(TEXT("#")) && !Parts[0].IsEmpty() && !Parts[1].IsEmpty())
			{
				ChatShots.Emplace(FName(*Parts[0]), Parts[1]);
				ChatShotClicks.Add(Parts.Num() >= 3 && Parts[2].Equals(TEXT("click"), ESearchCase::IgnoreCase));
			}
		}
	}
	if (ChatShots.Num() == 0)
	{
		ChatShots.Emplace(FName(TEXT("margaret")), TEXT("What is XRLibraries?"));
		ChatShots.Emplace(FName(TEXT("rosa")), TEXT("Recommend a book"));
		ChatShots.Emplace(FName(TEXT("hale")), TEXT("How do blueprints work?"));
		ChatShots.Emplace(FName(TEXT("rae")), TEXT("Where are the hidden tokens?"));
		ChatShotClicks.Init(false, ChatShots.Num());
	}
	while (CloseTopPanel())
	{
	}
	ChatShotIndex = 0;
	UE_LOG(LogWTA, Display, TEXT("WTA_CHATSHOT start %d questions, %.1f s each"), ChatShots.Num(), ChatShotSeconds);
	ChatShotAsk();
}

void AWTAPlayerController::WTAPlayTest(const FString& Phases)
{
	if (PlayTest == nullptr)
	{
		PlayTest = NewObject<UWTAPlayTest>(this, TEXT("WTAPlayTest"));
		PlayTest->RegisterComponent();
	}
	if (PlayTest->IsRunning())
	{
		UE_LOG(LogWTA, Warning, TEXT("WTAPlayTest: already running"));
		return;
	}
	PlayTest->Run(Phases);
}

void AWTAPlayerController::ChatShotAsk()
{
	while (CloseTopPanel())
	{
	}
	if (!ChatShots.IsValidIndex(ChatShotIndex))
	{
		UE_LOG(LogWTA, Display, TEXT("WTA_CHATSHOT done %d questions"), ChatShots.Num());
		ChatShotIndex = INDEX_NONE;
		return;
	}
	const FName StaffId = ChatShots[ChatShotIndex].Key;
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	const FWTAStaffRow* Staff = Content ? Content->FindStaff(StaffId) : nullptr;
	if (Staff != nullptr && Staff->TalkView.bValid)
	{
		GoToView(Staff->TalkView, false);
	}
	if (Chat != nullptr)
	{
		Chat->ClearConversation();
	}
	OpenStaffChat(StaffId);
	if (Chat != nullptr && Chat->IsOpen())
	{
		Chat->Send(ChatShots[ChatShotIndex].Value);
	}
	GetWorldTimerManager().SetTimer(ChatShotTimer, this, &AWTAPlayerController::ChatShotCapture, ChatShotSeconds, false);
}

void AWTAPlayerController::ChatShotCapture()
{
	if (!ChatShots.IsValidIndex(ChatShotIndex))
	{
		return;
	}
	const FString File = FPaths::ConvertRelativePathToFull(FPaths::ScreenShotDir() / FString::Printf(TEXT("QA/chat_%02d_%s%s.png"),
		ChatShotIndex, *ChatShots[ChatShotIndex].Key.ToString(), bChatShotClicked ? TEXT("_after") : TEXT("")));
	FScreenshotRequest::RequestScreenshot(File, true, false);
	UE_LOG(LogWTA, Display, TEXT("WTA_CHATSHOT %s | %s"), *File, *ChatShots[ChatShotIndex].Value);
	if (!bChatShotClicked && ChatShotClicks.IsValidIndex(ChatShotIndex) && ChatShotClicks[ChatShotIndex])
	{
		// Leave the screenshot a few frames, then click the answer's offer button and capture what it opens.
		GetWorldTimerManager().SetTimer(ChatShotTimer, this, &AWTAPlayerController::ChatShotClick, 0.5f, false);
		return;
	}
	bChatShotClicked = false;
	++ChatShotIndex;
	// Leave the screenshot a few frames before the next question.
	GetWorldTimerManager().SetTimer(ChatShotTimer, this, &AWTAPlayerController::ChatShotAsk, 0.5f, false);
}

void AWTAPlayerController::ChatShotClick()
{
	bChatShotClicked = true;
	const bool bClicked = Chat != nullptr && Chat->ClickOffer(0);
	UE_LOG(LogWTA, Display, TEXT("WTA_CHATSHOT click %s"), bClicked ? TEXT("ran the offer") : TEXT("found no offer button"));
	GetWorldTimerManager().SetTimer(ChatShotTimer, this, &AWTAPlayerController::ChatShotCapture, ChatShotSeconds, false);
}

void AWTAPlayerController::ShotTourTeleport()
{
	if (!ShotTourViews.IsValidIndex(ShotTourIndex))
	{
		UE_LOG(LogWTA, Display, TEXT("WTA_SHOTTOUR done %d views"), ShotTourViews.Num());
		ShotTourIndex = INDEX_NONE;
		return;
	}
	GoToView(ShotTourViews[ShotTourIndex].Value, false);
	GetWorldTimerManager().SetTimer(ShotTourTimer, this, &AWTAPlayerController::ShotTourCapture, ShotTourSeconds, false);
}

void AWTAPlayerController::ShotTourCapture()
{
	if (!ShotTourViews.IsValidIndex(ShotTourIndex))
	{
		return;
	}
	// An absolute path: a relative one with a folder in it would land next to the engine binaries.
	const FString File = FPaths::ConvertRelativePathToFull(FPaths::ScreenShotDir() /
		FString::Printf(TEXT("QA/%02d_%s.png"), ShotTourIndex, *ShotTourViews[ShotTourIndex].Key));
	FScreenshotRequest::RequestScreenshot(File, true, false);
	UE_LOG(LogWTA, Display, TEXT("WTA_SHOTTOUR %s"), *File);
	++ShotTourIndex;
	// Leave the screenshot a few frames before moving on.
	GetWorldTimerManager().SetTimer(ShotTourTimer, this, &AWTAPlayerController::ShotTourTeleport, 0.5f, false);
}

// --- Input handlers ---------------------------------------------------------------------

void AWTAPlayerController::OnMove(const FInputActionValue& Value)
{
	if (bUIMode)
	{
		return;
	}
	if (AWTACharacter* PlayerCharacter = GetWTACharacter())
	{
		if (PlayerCharacter->IsSeated())
		{
			if (!Value.Get<FVector2D>().IsNearlyZero())
			{
				PlayerCharacter->StandUp(true);        // a step off the seat; the walk starts from the next input
			}
			return;
		}
		PlayerCharacter->AddMoveInput(Value.Get<FVector2D>());
		bHasPendingView = false;
		bFaceTravelDirection = false;
	}
}

void AWTAPlayerController::OnLook(const FInputActionValue& Value)
{
	if (bUIMode || bCursorFree)
	{
		return;
	}
	const FVector2D Look = Value.Get<FVector2D>();
	if (Look.IsNearlyZero())
	{
		return;
	}
	// Any look input takes over from a pending face-view.
	bHasPendingView = false;
	bFaceTravelDirection = false;
	AddYawInput(static_cast<float>(Look.X) * MouseLookScale);
	AddPitchInput(static_cast<float>(Look.Y) * MouseLookScale * (bInvertMouseY ? -1.f : 1.f));
}

void AWTAPlayerController::OnLookStick(const FInputActionValue& Value)
{
	if (bUIMode)
	{
		return;
	}
	const FVector2D Look = Value.Get<FVector2D>();
	if (Look.IsNearlyZero())
	{
		return;
	}
	bHasPendingView = false;
	bFaceTravelDirection = false;
	const float DeltaSeconds = GetWorld() ? GetWorld()->GetDeltaSeconds() : 0.016f;
	AddYawInput(static_cast<float>(Look.X) * GamepadLookRate * DeltaSeconds);
	AddPitchInput(static_cast<float>(Look.Y) * GamepadLookRate * DeltaSeconds);
}

void AWTAPlayerController::OnJump(const FInputActionValue& Value)
{
	if (bUIMode)
	{
		return;
	}
	if (AWTACharacter* PlayerCharacter = GetWTACharacter())
	{
		if (PlayerCharacter->IsSeated())
		{
			PlayerCharacter->StandUp(true);
			return;
		}
		PlayerCharacter->Jump();
	}
}

void AWTAPlayerController::OnJumpEnd(const FInputActionValue& Value)
{
	if (AWTACharacter* PlayerCharacter = GetWTACharacter())
	{
		PlayerCharacter->StopJumping();
	}
}

void AWTAPlayerController::OnSprint(const FInputActionValue& Value)
{
	if (bUIMode)
	{
		return;
	}
	if (AWTACharacter* PlayerCharacter = GetWTACharacter())
	{
		PlayerCharacter->SetSprinting(true);
	}
}

void AWTAPlayerController::OnSprintEnd(const FInputActionValue& Value)
{
	if (AWTACharacter* PlayerCharacter = GetWTACharacter())
	{
		PlayerCharacter->SetSprinting(false);
	}
}

void AWTAPlayerController::OnInteract(const FInputActionValue& Value)
{
	if (bUIMode || Interaction == nullptr)
	{
		return;
	}
	if (Interaction->TryInteract())
	{
		return;
	}
	// Sitting with nothing under the crosshair: E stands up.
	if (AWTACharacter* Seated = GetWTACharacter(); Seated != nullptr && Seated->IsSeated())
	{
		Seated->StandUp(true);
		return;
	}
	// Standing in a wax scene with nothing under the crosshair: E opens that scene's story.
	if (!bCursorFree && !StageStoryId.IsNone())
	{
		OpenExhibit(StageStoryId);
		return;
	}
	// Free cursor: a click on the floor walks there; a click on a wall walks to 1.1 m in front of it.
	if (bCursorFree)
	{
		FVector Location;
		FVector Normal;
		AWTACharacter* PlayerCharacter = GetWTACharacter();
		if (PlayerCharacter != nullptr && Interaction->GetLastHitLocation(Location, Normal))
		{
			const FVector Target = Normal.Z > 0.5f ? Location : Location + Normal * 110.f;
			const FVector Dest = FloorPointFor(GetWorld(), Target + FVector(0.f, 0.f, PlayerCharacter->EyeHeight), PlayerCharacter->EyeHeight);
			const float Distance = static_cast<float>(FVector::Dist2D(PlayerCharacter->GetActorLocation(), Dest));
			PlayerCharacter->WalkTo(Dest);
			bHasPendingView = false;
			bFaceTravelDirection = PlayerCharacter->IsAutoWalking() && Distance > 400.f;
		}
	}
}

void AWTAPlayerController::OnBack(const FInputActionValue& Value)
{
	if (!CloseTopPanel())
	{
		ToggleMenu();
	}
}

void AWTAPlayerController::OnToggleCursor(const FInputActionValue& Value)
{
	if (bUIMode)
	{
		return;
	}
	bCursorFreedForTour = false; // the player chose; a tour ending leaves the cursor as it is
	SetCursorFree(!bCursorFree);
}

void AWTAPlayerController::OnTourNext(const FInputActionValue& Value)
{
	if (Menu != nullptr && Menu->IsOpen())
	{
		return;
	}
	if (Chat != nullptr && Chat->IsOpen())
	{
		return; // typing
	}
	if (UWTATourSubsystem* Tour = UWTATourSubsystem::Get(this))
	{
		if (Tour->IsTouring())
		{
			Tour->Next();
		}
		else
		{
			Tour->Start();
		}
	}
}

void AWTAPlayerController::OnPlaces(const FInputActionValue& Value)
{
	if (Menu != nullptr && Menu->IsOpen())
	{
		return;
	}
	if (Chat != nullptr && Chat->IsOpen())
	{
		return; // typing
	}
	if (Panel != nullptr && Panel->IsOpen() && Panel->GetMode() == EWTAPanelMode::Places)
	{
		CloseTopPanel();
		return;
	}
	OpenPlaces();
}

void AWTAPlayerController::OnChat(const FInputActionValue& Value)
{
	if (Menu != nullptr && Menu->IsOpen())
	{
		return;
	}
	if (Chat != nullptr && Chat->IsOpen())
	{
		Chat->FocusInput();
		return;
	}
	// Open the chat with the staff of the room you are in (Margaret in the lobby and the museum, and so on).
	FName StaffId;
	if (UWTARoomSubsystem* Rooms = UWTARoomSubsystem::Get(this))
	{
		FName Room = Rooms->GetCurrentRoom();
		if (Room.IsNone() && GetPawn() != nullptr)
		{
			Room = Rooms->RoomAt(GetPawn()->GetActorLocation());
		}
		StaffId = Rooms->GetStaffForRoom(Room);
	}
	if (StaffId.IsNone())
	{
		if (const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this))
		{
			const TArray<FName> Staff = Content->GetRowNames(EWTATable::Staff);
			if (Staff.Num() > 0)
			{
				StaffId = Staff[0];
			}
		}
	}
	if (!StaffId.IsNone())
	{
		OpenStaffChat(StaffId);
	}
}

// --- Delegate sinks --------------------------------------------------------------------

void AWTAPlayerController::HandleHoverChanged(const FText& Label)
{
	// Exhibits (gallery and wax scenes) get the museum plaque instead of the one-line label under the crosshair.
	const AWTAExhibitActor* Exhibit = Interaction != nullptr ? Cast<AWTAExhibitActor>(Interaction->GetHovered()) : nullptr;
	HoverStoryId = Exhibit != nullptr ? Exhibit->ItemId : NAME_None;
	if (Hud != nullptr)
	{
		Hud->SetHoverLabel(Exhibit != nullptr ? FText::GetEmpty() : Label);
	}
	RefreshStoryPlaque();
}

void AWTAPlayerController::HandleRoomChanged(FName RoomId)
{
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	const FWTARoomRow* Room = Content ? Content->FindRoom(RoomId) : nullptr;
	if (Room == nullptr || Hud == nullptr)
	{
		return;
	}
	Hud->SetRoom(Room->Kicker, Room->DisplayName, Room->Sub);
	const UWTARoomSubsystem* Rooms = UWTARoomSubsystem::Get(this);
	if (Rooms != nullptr && Rooms->IsFirstVisit() && !Room->Sub.IsEmpty())
	{
		ShowHint(Room->Sub);
	}
}

void AWTAPlayerController::HandleBadgeAwarded(FName BadgeId)
{
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	const FWTABadgeRow* Badge = Content ? Content->FindBadge(BadgeId) : nullptr;
	const FString Name = Badge ? Badge->DisplayName.ToString() : BadgeId.ToString();
	ShowToast(FText::FromString(FString::Printf(TEXT("Badge unlocked: %s"), *Name)), 3.6f);
	if (Hud != nullptr)
	{
		if (const UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this))
		{
			Hud->SetBadgeCount(Progress->NumBadges(), Progress->TotalBadges());
		}
	}
}

void AWTAPlayerController::HandleTokenCollected(FName TokenId, int32 Found, int32 Total)
{
	const FString Message = (Total > 0 && Found >= Total)
		? FString::Printf(TEXT("You found all %d XR tokens!"), Total)
		: FString::Printf(TEXT("XR token found! %d of %d."), Found, Total);
	ShowToast(FText::FromString(Message), 0.f);
}

void AWTAPlayerController::HandleTourChanged(int32 Index)
{
	// A tour frees the cursor so its bar's Back / Next / End buttons can be clicked (T and Esc work too);
	// mouse look comes back when it ends, unless the player toggled the cursor with Tab in between.
	const bool bTouring = Index >= 0;
	if (bTouring && !bTourActive)
	{
		if (!bCursorFree)
		{
			bCursorFree = true;
			bCursorFreedForTour = true;
			UpdateInputMode();
		}
		ShowToast(FText::FromString(TEXT("Tour: click Next or press T. Tab looks around, Esc ends the tour.")), 0.f);
	}
	else if (!bTouring && bTourActive && bCursorFreedForTour)
	{
		bCursorFreedForTour = false;
		SetCursorFree(false);
	}
	bTourActive = bTouring;

	if (Hud == nullptr)
	{
		return;
	}
	UWTATourSubsystem* Tour = UWTATourSubsystem::Get(this);
	FWTATourStopRow Stop;
	if (Index < 0 || Tour == nullptr || !Tour->GetCurrentStop(Stop))
	{
		Hud->HideTour();
		return;
	}
	Hud->ShowTour(Index, Tour->GetNumStops(), Stop.Title, Stop.DateLabel, Stop.Body, Stop.OpenLabel);
	RefreshTourBar();
}

void AWTAPlayerController::HandleProgressReset()
{
	if (Hud != nullptr)
	{
		if (const UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this))
		{
			Hud->SetBadgeCount(Progress->NumBadges(), Progress->TotalBadges());
		}
	}
	ShowToast(FText::FromString(TEXT("Progress reset. The tokens are back in their hiding places.")), 0.f);
}
