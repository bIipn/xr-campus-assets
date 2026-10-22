// Walk the Archive - QA play test (see the header for the phases and the log format).

#include "Core/WTAPlayTest.h"
#include "Core/WTACharacter.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "Core/WTASettings.h"
#include "Interaction/WTAInteractable.h"
#include "Interaction/WTAInteractionComponent.h"
#include "Systems/WTAContentSubsystem.h"
#include "Systems/WTAGraphicsLibrary.h"
#include "Systems/WTAProgressSubsystem.h"
#include "Systems/WTARoomSubsystem.h"
#include "Systems/WTATourSubsystem.h"
#include "Systems/WTAVoiceSubsystem.h"
#include "UI/WTAChatWidget.h"
#include "UI/WTAMenuWidget.h"
#include "UI/WTAPanelWidget.h"
#include "World/WTAAttractComponent.h"
#include "World/WTABookActor.h"
#include "World/WTAExhibitActor.h"
#include "World/WTAPeopleLibrary.h"
#include "World/WTARideActor.h"
#include "World/WTASeatActor.h"
#include "World/WTAStaffNPC.h"
#include "World/WTAStationActor.h"
#include "World/WTAStatueActor.h"
#include "World/WTACourseActor.h"
#include "World/WTATalkActor.h"
#include "UI/WTACertificateWidget.h"
#include "Components/EditableTextBox.h"
#include "HAL/FileManager.h"
#include "World/WTATokenActor.h"
#include "World/WTAWaxStageActor.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "CollisionQueryParams.h"
#include "CollisionShape.h"
#include "Components/CapsuleComponent.h"
#include "Components/ChildActorComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/OverlapResult.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/SkinnedAsset.h"
#include "ReferenceSkeleton.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Materials/MaterialInterface.h"
#include "NavigationPath.h"
#include "NavigationSystem.h"
#include "EngineUtils.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/GameUserSettings.h"
#include "HAL/IConsoleManager.h"
#include "InputActionValue.h"
#include "Misc/App.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "UnrealClient.h"

namespace
{
	const TCHAR* ResultWord(int32 Result)
	{
		switch (Result)
		{
		case 0: return TEXT("PASS");
		case 1: return TEXT("FAIL");
		case 2: return TEXT("SKIP");
		default: return TEXT("INFO");
		}
	}

	/** The floor height under (X, Y), searching down from FromZ; false when there is none within 6 m. */
	bool FloorUnder(const UWorld* World, double X, double Y, double FromZ, const AActor* Ignore, double& OutZ)
	{
		FCollisionQueryParams Params(FName(TEXT("WTAPlayFloor")), false, Ignore);
		FHitResult Hit;
		if (World->LineTraceSingleByChannel(Hit, FVector(X, Y, FromZ), FVector(X, Y, FromZ - 600.0), ECC_Pawn, Params))
		{
			OutZ = Hit.ImpactPoint.Z;
			return true;
		}
		return false;
	}

	/** True when a player capsule standing on FloorZ at (X, Y) touches nothing that blocks it. */
	bool CapsuleFits(const UWorld* World, double X, double Y, double FloorZ, const AActor* Ignore)
	{
		FCollisionQueryParams Params(FName(TEXT("WTAPlayFit")), false, Ignore);
		return !World->OverlapBlockingTestByChannel(FVector(X, Y, FloorZ + 92.0), FQuat::Identity, ECC_Pawn,
			FCollisionShape::MakeCapsule(29.f, 88.f), Params);
	}

	/** A component-space bone location, or zero when the mesh has no such bone. */
	FVector BoneInComponent(const USkeletalMeshComponent* Mesh, FName Bone)
	{
		if (Mesh == nullptr || Mesh->GetBoneIndex(Bone) == INDEX_NONE)
		{
			return FVector::ZeroVector;
		}
		return Mesh->GetSocketTransform(Bone, RTS_Component).GetLocation();
	}

	/** Where the bone sits in component space in the skeleton's reference (bind) pose. */
	FVector BoneInRefPose(const USkeletalMeshComponent* Mesh, FName Bone)
	{
		const USkinnedAsset* Asset = Mesh != nullptr ? Mesh->GetSkinnedAsset() : nullptr;
		if (Asset == nullptr)
		{
			return FVector::ZeroVector;
		}
		const FReferenceSkeleton& Ref = Asset->GetRefSkeleton();
		int32 Index = Ref.FindBoneIndex(Bone);
		if (Index == INDEX_NONE)
		{
			return FVector::ZeroVector;
		}
		FTransform T = FTransform::Identity;
		while (Index != INDEX_NONE)
		{
			T = T * Ref.GetRefBonePose()[Index];
			Index = Ref.GetParentIndex(Index);
		}
		return T.GetLocation();
	}

	/** The MetaHuman face mesh: the skeletal mesh component named Face, else one whose mesh asset says Face. */
	USkeletalMeshComponent* FindFace(AActor* Person)
	{
		if (Person == nullptr)
		{
			return nullptr;
		}
		TInlineComponentArray<USkeletalMeshComponent*> Meshes;
		Person->GetComponents(Meshes);
		for (USkeletalMeshComponent* Mesh : Meshes)
		{
			if (Mesh != nullptr && Mesh->GetFName() == TEXT("Face"))
			{
				return Mesh;
			}
		}
		for (USkeletalMeshComponent* Mesh : Meshes)
		{
			if (Mesh != nullptr && Mesh->GetSkeletalMeshAsset() != nullptr && Mesh->GetSkeletalMeshAsset()->GetName().Contains(TEXT("Face")))
			{
				return Mesh;
			}
		}
		return nullptr;
	}

	const TCHAR* PanelModeName(EWTAPanelMode Mode)
	{
		switch (Mode)
		{
		case EWTAPanelMode::Exhibit: return TEXT("Exhibit");
		case EWTAPanelMode::Book: return TEXT("Book");
		case EWTAPanelMode::Station: return TEXT("Station");
		case EWTAPanelMode::Ride: return TEXT("Ride");
		case EWTAPanelMode::Badges: return TEXT("Badges");
		case EWTAPanelMode::Places: return TEXT("Places");
		default: return TEXT("None");
		}
	}

	/** The data row an interactable stands for (exhibit, book, station, ride, person or token), so a line names it. */
	FName InteractRowId(const AActor* Actor)
	{
		if (const AWTAExhibitActor* Exhibit = Cast<AWTAExhibitActor>(Actor)) { return Exhibit->ItemId; }
		if (const AWTABookActor* Book = Cast<AWTABookActor>(Actor)) { return Book->BookId; }
		if (const AWTAStationActor* Station = Cast<AWTAStationActor>(Actor)) { return Station->StationId; }
		if (const AWTARideActor* Ride = Cast<AWTARideActor>(Actor)) { return Ride->RideId; }
		if (const AWTAStaffNPC* Staff = Cast<AWTAStaffNPC>(Actor)) { return Staff->StaffId; }
		if (const AWTATokenActor* Token = Cast<AWTATokenActor>(Actor)) { return Token->TokenId; }
		return NAME_None;
	}

	/** The view a place row stands at, or an invalid view. */
	FWTAView PlaceView(const UObject* WorldContext, const TCHAR* PlaceId)
	{
		const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(WorldContext);
		const FWTAPlaceRow* Row = Content != nullptr ? Content->FindPlace(FName(PlaceId)) : nullptr;
		FWTAView View = Row != nullptr ? Row->View : FWTAView();
		// Like the shot tour: a place with a location is a place to stand.
		View.bValid = View.bValid || !View.Location.IsNearlyZero();
		return View;
	}
}

UWTAPlayTest::UWTAPlayTest()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
	PrimaryComponentTick.bTickEvenWhenPaused = true;
}

AWTAPlayerController* UWTAPlayTest::PC() const
{
	return Cast<AWTAPlayerController>(GetOwner());
}

AWTACharacter* UWTAPlayTest::Player() const
{
	const AWTAPlayerController* Controller = PC();
	return Controller != nullptr ? Controller->GetWTACharacter() : nullptr;
}

void UWTAPlayTest::Report(const TCHAR* Phase, EResult Result, const FString& What, const FString& Details)
{
	switch (Result)
	{
	case EResult::Pass: ++NumPass; break;
	case EResult::Fail: ++NumFail; break;
	case EResult::Skip: ++NumSkip; break;
	default: break;
	}
	UE_LOG(LogWTA, Display, TEXT("WTA_PLAY %s %s %s | %s"), Phase, ResultWord(static_cast<int32>(Result)), *What, *Details);
}

void UWTAPlayTest::Shot(const FString& Name, bool bShowUI)
{
	const FString File = bShowUI
		? FPaths::ConvertRelativePathToFull(FPaths::ScreenShotDir() / FString::Printf(TEXT("QA/play_%02d_%s.png"), ShotIndex++, *Name))
		: FPaths::ConvertRelativePathToFull(FPaths::ScreenShotDir() / FString::Printf(TEXT("QA/face_%02d_%s.png"), FaceIndex++, *Name));
	FScreenshotRequest::RequestScreenshot(File, bShowUI, false);
	UE_LOG(LogWTA, Display, TEXT("WTA_PLAY shot %s"), *File);
}

void UWTAPlayTest::KeyDown(const FKey& Key)
{
	AWTAPlayerController* Controller = PC();
	if (bKeysWork && FSlateApplication::IsInitialized())
	{
		FSlateApplication::Get().ProcessKeyDownEvent(FKeyEvent(Key, FModifierKeysState(), 0u, false, 0u, 0u));
		return;
	}
	if (Controller == nullptr)
	{
		return;
	}
	// No key routing: run what the binding runs.
	const FInputActionValue Pressed(true);
	if (Key == EKeys::E)
	{
		Controller->OnInteract(Pressed);
	}
	else if (Key == EKeys::Escape)
	{
		Controller->OnBack(Pressed);
	}
	else if (Key == EKeys::T)
	{
		Controller->OnTourNext(Pressed);
	}
	else if (Key == EKeys::M)
	{
		Controller->OnPlaces(Pressed);
	}
	else if (Key == EKeys::Enter)
	{
		Controller->OnChat(Pressed);
	}
	else if ((Key == EKeys::Right || Key == EKeys::Left) && Controller->Panel != nullptr && Controller->Panel->GetMode() == EWTAPanelMode::Book)
	{
		Controller->OpenBook(Controller->Panel->GetCurrentId(), Controller->Panel->GetCurrentPage() + (Key == EKeys::Right ? 1 : -1));
	}
	else if (Key == EKeys::W)
	{
		bHoldForward = true;
	}
	else if (Key == EKeys::LeftShift)
	{
		if (AWTACharacter* Character = Player())
		{
			Character->SetSprinting(true);
		}
	}
}

void UWTAPlayTest::KeyUp(const FKey& Key)
{
	if (bKeysWork && FSlateApplication::IsInitialized())
	{
		FSlateApplication::Get().ProcessKeyUpEvent(FKeyEvent(Key, FModifierKeysState(), 0u, false, 0u, 0u));
		return;
	}
	if (Key == EKeys::W)
	{
		bHoldForward = false;
	}
	else if (Key == EKeys::LeftShift)
	{
		if (AWTACharacter* Character = Player())
		{
			Character->SetSprinting(false);
		}
	}
}

void UWTAPlayTest::AddTap(const FString& Name, const FKey& Key, float After)
{
	Steps.Add({ Name + TEXT(" down"), [this, Key]() -> float { KeyDown(Key); return 0.12f; } });
	Steps.Add({ Name + TEXT(" up"), [this, Key, After]() -> float { KeyUp(Key); return After; } });
}

void UWTAPlayTest::CloseAll()
{
	if (AWTAPlayerController* Controller = PC())
	{
		for (int32 Guard = 0; Guard < 6 && Controller->CloseTopPanel(); ++Guard)
		{
		}
	}
}

void UWTAPlayTest::StandAt(const FWTAView& View)
{
	// Through the controller, like the game's own teleports: that also drops a view the camera was still turning
	// toward. (E on an exhibit or station walks to its view spot and turns the camera there; a test teleporting
	// away mid-walk would otherwise be turned back toward the last exhibit.)
	if (AWTAPlayerController* Controller = PC())
	{
		Controller->GoToView(View, false);
	}
	else if (AWTACharacter* Character = Player())
	{
		Character->TeleportToView(View);
	}
}

FString UWTAPlayTest::DescribeAim(const AActor* Target) const
{
	const AWTAPlayerController* Controller = PC();
	const UWorld* World = GetWorld();
	if (Controller == nullptr || World == nullptr)
	{
		return TEXT("no view");
	}
	FVector Eye;
	FRotator Rotation;
	Controller->GetPlayerViewPoint(Eye, Rotation);
	FCollisionQueryParams Params(FName(TEXT("WTAPlayWhy")), false, Controller->GetPawn());
	FHitResult Hit;
	const bool bHit = World->LineTraceSingleByChannel(Hit, Eye, Eye + Rotation.Vector() * 1500.0, ECC_Visibility, Params);
	const FString Ray = bHit
		? FString::Printf(TEXT("the ray hits %s (%s) at %.0f cm"), *GetNameSafe(Hit.GetActor()), *GetNameSafe(Hit.GetComponent()), Hit.Distance)
		: FString(TEXT("the ray hits nothing within 15 m"));
	const FVector Centre = Target != nullptr ? Target->GetComponentsBoundingBox(true).GetCenter() : FVector::ZeroVector;
	return FString::Printf(TEXT("eye %s pitch %.0f yaw %.0f, %s; its centre %s is %.0f cm away"), *Eye.ToCompactString(),
		Rotation.Pitch, Rotation.Yaw, *Ray, *Centre.ToCompactString(), FVector::Dist(Eye, Centre));
}

void UWTAPlayTest::Run(const FString& Phases)
{
	Steps.Reset();
	StepIndex = INDEX_NONE;
	WaitSeconds = 0.f;
	NumPass = NumFail = NumSkip = 0;
	ShotIndex = FaceIndex = 0;
	WalkMoved = WalkTests = 0;
	bKeysWork = true;
	bHoldForward = false;
	bMeasuring = false;

	TArray<FString> Wanted;
	Phases.ToLower().ParseIntoArrayWS(Wanted, TEXT(","));
	// "only=<text>" keeps the people (faces, people) whose name contains <text>; several may be given.
	PeopleFilter.Reset();
	float SpeedDown = -1.f;
	for (int32 i = Wanted.Num() - 1; i >= 0; --i)
	{
		if (Wanted[i].StartsWith(TEXT("only=")))
		{
			PeopleFilter.Add(Wanted[i].Mid(5));
			Wanted.RemoveAt(i);
		}
		else if (Wanted[i].StartsWith(TEXT("speeddown=")))
		{
			SpeedDown = FCString::Atof(*Wanted[i].Mid(10));
			Wanted.RemoveAt(i);
		}
	}
	const bool bAll = Wanted.Num() == 0 || Wanted.Contains(TEXT("all"));
	auto Want = [&](const TCHAR* Phase) { return bAll || Wanted.Contains(Phase); };
	if (SpeedDown > 0.f)
	{
		Steps.Add({ TEXT("speed down"), [this, SpeedDown]() -> float
		{
			int32 Volumes = 0;
			for (TActorIterator<APostProcessVolume> It(GetWorld()); It; ++It)
			{
				It->Settings.bOverride_AutoExposureSpeedDown = true;
				It->Settings.AutoExposureSpeedDown = SpeedDown;
				++Volumes;
			}
			Report(TEXT("save"), EResult::Info, TEXT("auto exposure speed down"), FString::Printf(TEXT("%.1f on %d volumes"), SpeedDown, Volumes));
			return 0.f;
		} });
	}

	// The menu check needs the intro menu as the game left it, so it goes first; every other phase starts closed.
	if (Want(TEXT("menu")))
	{
		AddMenuPhase();
	}
	Steps.Add({ TEXT("close"), [this]() -> float { CloseAll(); return 0.3f; } });
	if (Want(TEXT("keys")) || Want(TEXT("walk")) || Want(TEXT("interact")) || Want(TEXT("wax")) || Want(TEXT("ui")))
	{
		AddKeysPhase();
	}
	if (Want(TEXT("walk")))
	{
		AddWalkPhase();
	}
	if (Want(TEXT("interact")))
	{
		AddInteractPhase();
	}
	if (Want(TEXT("wax")))
	{
		AddWaxPhase();
	}
	if (Want(TEXT("seats")))
	{
		AddSeatsPhase();
	}
	if (Want(TEXT("talks")))
	{
		AddTalksPhase();
	}
	if (Wanted.Contains(TEXT("quiz")))
	{
		AddQuizPhase();
	}
	if (Want(TEXT("stations")))
	{
		AddStationsPhase();
	}
	if (Want(TEXT("course")))
	{
		AddCoursePhase();
	}
	if (Want(TEXT("ui")))
	{
		AddUIPhase();
	}
	if (Want(TEXT("graphics")))
	{
		AddGraphicsPhase();
	}
	if (Want(TEXT("fps")))
	{
		AddFpsPhase();
	}
	if (Want(TEXT("people")))
	{
		AddPeoplePhase();
	}
	if (Want(TEXT("faces")))
	{
		AddFacesPhase();
	}
	// Only when named: a minute of standing in rooms, for screenshots rather than checks.
	if (Wanted.Contains(TEXT("adapt")))
	{
		AddAdaptPhase();
	}
	// Only when named: a whole loop of each wax scene, for the acting shots.
	if (Wanted.Contains(TEXT("acting")))
	{
		AddActingPhase();
	}
	if (Wanted.Contains(TEXT("attract")))
	{
		AddAttractPhase();
	}
	if (Wanted.Contains(TEXT("library")))
	{
		AddLibraryPhase();
	}
	if (Wanted.Contains(TEXT("museum")))
	{
		AddMuseumPhase();
	}
	if (Wanted.Contains(TEXT("doors")))
	{
		AddDoorsPhase();
	}
	Steps.Add({ TEXT("done"), [this]() -> float
	{
		CloseAll();
		UE_LOG(LogWTA, Display, TEXT("WTA_PLAY done %d pass, %d fail, %d skip"), NumPass, NumFail, NumSkip);
		return 0.f;
	} });

	UE_LOG(LogWTA, Display, TEXT("WTA_PLAY start '%s': %d steps"), *Phases, Steps.Num());
	if (const UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this))
	{
		Report(TEXT("save"), EResult::Info, TEXT("progress at start"), FString::Printf(TEXT("%d of %d badges, %d of %d tokens"),
			Progress->NumBadges(), Progress->TotalBadges(), Progress->NumTokens(), Progress->TotalTokens()));
	}
	StepIndex = 0;
	WaitSeconds = 0.f;
}

void UWTAPlayTest::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (bHoldForward)
	{
		if (AWTACharacter* Character = Player())
		{
			Character->AddMoveInput(FVector2D(0.f, 1.f));
		}
	}
	if (bMeasuring)
	{
		const float Frame = static_cast<float>(FApp::GetDeltaTime());
		MeasureSeconds += Frame;
		++MeasureFrames;
		WorstFrame = FMath::Max(WorstFrame, Frame);
	}

	if (!Steps.IsValidIndex(StepIndex))
	{
		return;
	}
	WaitSeconds -= DeltaTime;
	// Several zero-wait steps may run in one frame; a waiting step ends the frame.
	for (int32 Guard = 0; Guard < 64 && WaitSeconds <= 0.f && Steps.IsValidIndex(StepIndex); ++Guard)
	{
		const float Next = Steps[StepIndex].Do();
		if (Next < 0.f)
		{
			WaitSeconds = -Next;   // poll: run this step again later
		}
		else
		{
			WaitSeconds = Next;
			++StepIndex;
		}
	}
}

// --- menu ------------------------------------------------------------------------------------

void UWTAPlayTest::AddMenuPhase()
{
	Steps.Add({ TEXT("menu at start"), [this]() -> float
	{
		AWTAPlayerController* Controller = PC();
		const UWTASettings* Settings = UWTASettings::Get();
		const bool bWanted = Settings == nullptr || Settings->bShowIntroMenu;
		const bool bOpen = Controller != nullptr && Controller->Menu != nullptr && Controller->Menu->IsOpen();
		Report(TEXT("menu"), (bOpen || !bWanted) ? EResult::Pass : EResult::Fail, TEXT("intro menu at start"),
			bOpen ? TEXT("open") : (bWanted ? TEXT("not open") : TEXT("switched off in the settings")));
		Shot(TEXT("menu_intro"));
		return 0.4f;
	} });
	Steps.Add({ TEXT("menu enter"), [this]() -> float
	{
		// The Enter button runs CloseTopPanel.
		if (AWTAPlayerController* Controller = PC())
		{
			Controller->CloseTopPanel();
		}
		return 1.5f;
	} });
	Steps.Add({ TEXT("menu start view"), [this]() -> float
	{
		AWTAPlayerController* Controller = PC();
		AWTACharacter* Character = Player();
		const UWTARoomSubsystem* Rooms = UWTARoomSubsystem::Get(this);
		if (Controller == nullptr || Character == nullptr)
		{
			Report(TEXT("menu"), EResult::Fail, TEXT("start"), TEXT("no player"));
			return 0.f;
		}
		const FName Room = Rooms != nullptr ? Rooms->GetCurrentRoom() : NAME_None;
		const float Yaw = static_cast<float>(Controller->GetControlRotation().Yaw);
		// The galleries run along -Y from the lobby: facing them is a yaw of -90. The start is the forecourt
		// (the settings' SpawnView, on the path facing the portico) unless the settings put it back in the lobby.
		const float Off = FMath::Abs(FMath::FindDeltaAngleDegrees(Yaw, -90.f));
		const UWTASettings* Settings = UWTASettings::Get();
		const bool bOutside = Settings != nullptr && Settings->SpawnView.bValid && Settings->SpawnView.Location.Y > 1000.f;
		const FName Expected(bOutside ? TEXT("forecourt") : TEXT("lobby"));
		const bool bOk = Room == Expected && Off < 35.f && !Controller->IsAnyPanelOpen();
		Report(TEXT("menu"), bOk ? EResult::Pass : EResult::Fail, bOutside ? TEXT("Enter starts on the forecourt facing the museum") : TEXT("Enter starts in the lobby facing the galleries"),
			FString::Printf(TEXT("room %s, yaw %.0f (%.0f off), at %s, panels %s"), *Room.ToString(), Yaw, Off,
				*Character->GetActorLocation().ToCompactString(), Controller->IsAnyPanelOpen() ? TEXT("open") : TEXT("closed")));
		Shot(TEXT("start_view"));
		return 0.4f;
	} });
	AddTap(TEXT("menu esc"), EKeys::Escape, 0.5f);
	Steps.Add({ TEXT("menu pause"), [this]() -> float
	{
		AWTAPlayerController* Controller = PC();
		const bool bOpen = Controller != nullptr && Controller->Menu != nullptr && Controller->Menu->IsOpen();
		Report(TEXT("menu"), bOpen ? EResult::Pass : EResult::Fail, TEXT("Esc opens the pause menu"), bOpen ? TEXT("open") : TEXT("not open"));
		if (bOpen)
		{
			Shot(TEXT("menu_pause"));
		}
		return 0.4f;
	} });
	AddTap(TEXT("menu esc again"), EKeys::Escape, 0.5f);
	Steps.Add({ TEXT("menu closed"), [this]() -> float
	{
		AWTAPlayerController* Controller = PC();
		const bool bOpen = Controller != nullptr && Controller->IsAnyPanelOpen();
		Report(TEXT("menu"), bOpen ? EResult::Fail : EResult::Pass, TEXT("Esc closes the pause menu"), bOpen ? TEXT("still open") : TEXT("closed"));
		return 0.2f;
	} });
}

// --- keys ------------------------------------------------------------------------------------

void UWTAPlayTest::AddKeysPhase()
{
	Steps.Add({ TEXT("keys m"), [this]() -> float
	{
		CloseAll();
		KeyDown(EKeys::M);
		return 0.12f;
	} });
	Steps.Add({ TEXT("keys m up"), [this]() -> float { KeyUp(EKeys::M); return 0.5f; } });
	Steps.Add({ TEXT("keys check"), [this]() -> float
	{
		AWTAPlayerController* Controller = PC();
		const bool bPlaces = Controller != nullptr && Controller->Panel != nullptr && Controller->Panel->IsOpen()
			&& Controller->Panel->GetMode() == EWTAPanelMode::Places;
		if (bPlaces)
		{
			Report(TEXT("keys"), EResult::Pass, TEXT("M opens the places list"), TEXT("keys reach the game through Slate"));
			Shot(TEXT("places"));
		}
		else
		{
			bKeysWork = false;
			Report(TEXT("keys"), EResult::Info, TEXT("M through Slate did nothing"), TEXT("the window has no keyboard focus; the input handlers are called directly from here on"));
			KeyDown(EKeys::M);
			const bool bDirect = Controller != nullptr && Controller->Panel != nullptr && Controller->Panel->GetMode() == EWTAPanelMode::Places;
			Report(TEXT("keys"), bDirect ? EResult::Pass : EResult::Fail, TEXT("M handler opens the places list"), bDirect ? TEXT("open") : TEXT("not open"));
		}
		return 0.3f;
	} });
	AddTap(TEXT("keys esc"), EKeys::Escape, 0.4f);
	Steps.Add({ TEXT("keys esc check"), [this]() -> float
	{
		AWTAPlayerController* Controller = PC();
		const bool bOpen = Controller != nullptr && Controller->IsAnyPanelOpen();
		Report(TEXT("keys"), bOpen ? EResult::Fail : EResult::Pass, TEXT("Esc closes the places list"), bOpen ? TEXT("still open") : TEXT("closed"));
		CloseAll();
		return 0.2f;
	} });
}

// --- walk ------------------------------------------------------------------------------------

void UWTAPlayTest::AddWalkPhase()
{
	TArray<FString> Lines;
	const FString File = FPaths::ProjectSavedDir() / TEXT("QA") / TEXT("walk_tests.txt");
	if (!FFileHelper::LoadFileToStringArray(Lines, *File))
	{
		Steps.Add({ TEXT("walk none"), [this, File]() -> float
		{
			Report(TEXT("walk"), EResult::Skip, TEXT("walk tests"), FString::Printf(TEXT("no %s"), *File));
			return 0.f;
		} });
		return;
	}
	int32 Added = 0;
	for (const FString& Line : Lines)
	{
		// "<name> | <x> <y> | <yaw> | x|y <wall coordinate>"
		TArray<FString> Parts;
		Line.ParseIntoArray(Parts, TEXT("|"));
		for (FString& Part : Parts)
		{
			Part.TrimStartAndEndInline();
		}
		if (Parts.Num() < 4 || Parts[0].StartsWith(TEXT("#")))
		{
			continue;
		}
		TArray<FString> XY;
		TArray<FString> Wall;
		Parts[1].ParseIntoArrayWS(XY);
		Parts[3].ParseIntoArrayWS(Wall);
		if (XY.Num() < 2 || Wall.Num() < 2)
		{
			continue;
		}
		AddWalkTest(Parts[0], FVector2D(FCString::Atod(*XY[0]), FCString::Atod(*XY[1])), FCString::Atof(*Parts[2]),
			Wall[0].Equals(TEXT("x"), ESearchCase::IgnoreCase), FCString::Atof(*Wall[1]));
		++Added;
	}
	Steps.Add({ TEXT("walk summary"), [this, Added]() -> float
	{
		// The tests prove nothing if the keys never moved the player: some must cover real ground.
		Report(TEXT("walk"), (WalkTests == 0 || WalkMoved > 0) ? EResult::Pass : EResult::Fail, TEXT("summary"),
			FString::Printf(TEXT("%d tests from %d lines, %d walked 50 cm or more before stopping"), WalkTests, Added, WalkMoved));
		return 0.f;
	} });
}

void UWTAPlayTest::AddWalkTest(const FString& Name, const FVector2D& XY, float Yaw, bool bAxisX, float WallAt)
{
	TSharedRef<FVector> Start = MakeShared<FVector>(FVector::ZeroVector);
	TSharedRef<bool> bValid = MakeShared<bool>(false);

	Steps.Add({ Name, [this, Name, XY, Yaw, Start, bValid]() -> float
	{
		*bValid = false;
		AWTACharacter* Character = Player();
		const UWorld* World = GetWorld();
		if (Character == nullptr || World == nullptr)
		{
			return 0.f;
		}
		// The start is 150 cm from the wall's centre line. A thick wall (closets, a service gap between rooms) can
		// swallow that spot, so step back from the wall, 50 cm at a time, up to 250 cm further, to find floor
		// with room to stand.
		const FVector2D Back = -FVector2D(FMath::Cos(FMath::DegreesToRadians(Yaw)), FMath::Sin(FMath::DegreesToRadians(Yaw)));
		FVector2D At = XY;
		double FloorZ = 0.0;
		bool bFound = false;
		bool bAnyFloor = false;
		for (int32 Step = 0; Step <= 5 && !bFound; ++Step)
		{
			At = XY + Back * (50.0 * Step);
			// Search down from 60 cm: above stage platforms, below desks and benches (a start on a desk top
			// stepped off it and read as a fall).
			if (FloorUnder(World, At.X, At.Y, 60.0, Character, FloorZ))
			{
				bAnyFloor = true;
				bFound = CapsuleFits(World, At.X, At.Y, FloorZ, Character);
			}
		}
		if (!bFound)
		{
			Report(TEXT("walk"), EResult::Skip, Name, bAnyFloor ? TEXT("no room to stand within 4 m of the wall") : TEXT("no floor there"));
			return 0.f;
		}
		FWTAView View;
		View.Location = FVector(At.X, At.Y, FloorZ + Character->EyeHeight);
		View.Yaw = Yaw;
		View.Pitch = 0.f;
		View.bValid = true;
		CloseAll();
		StandAt(View);
		*bValid = true;
		return 0.3f;
	} });
	Steps.Add({ Name + TEXT(" go"), [this, Start, bValid]() -> float
	{
		if (!*bValid)
		{
			return 0.f;
		}
		if (AWTACharacter* Character = Player())
		{
			*Start = Character->GetActorLocation();
		}
		KeyDown(EKeys::LeftShift);
		KeyDown(EKeys::W);
		return 1.1f;
	} });
	Steps.Add({ Name + TEXT(" stop"), [this, bValid]() -> float
	{
		if (!*bValid)
		{
			return 0.f;
		}
		KeyUp(EKeys::W);
		KeyUp(EKeys::LeftShift);
		return 0.2f;
	} });
	Steps.Add({ Name + TEXT(" check"), [this, Name, Start, bValid, bAxisX, WallAt]() -> float
	{
		if (!*bValid)
		{
			return 0.f;
		}
		AWTACharacter* Character = Player();
		if (Character == nullptr)
		{
			return 0.f;
		}
		const FVector End = Character->GetActorLocation();
		const double S0 = (bAxisX ? Start->X : Start->Y) - WallAt;
		const double S1 = (bAxisX ? End.X : End.Y) - WallAt;
		const bool bCrossed = S0 * S1 < 0.0;
		const bool bFell = End.Z < Start->Z - 60.0;
		const double Moved = FVector::Dist2D(*Start, End);
		++WalkTests;
		if (Moved >= 50.0)
		{
			++WalkMoved;
		}
		Report(TEXT("walk"), (bCrossed || bFell) ? EResult::Fail : EResult::Pass, Name,
			FString::Printf(TEXT("started %.0f cm from the wall, walked %.0f cm, stopped %.0f cm from it%s%s"),
				FMath::Abs(S0), Moved, FMath::Abs(S1), bCrossed ? TEXT(", WENT THROUGH") : TEXT(""), bFell ? TEXT(", FELL") : TEXT("")));
		if (bCrossed || bFell)
		{
			Shot(TEXT("walk_fail_") + Name.Replace(TEXT(" "), TEXT("_")));
		}
		return 0.f;
	} });
}

// --- interact --------------------------------------------------------------------------------

void UWTAPlayTest::AddInteractPhase()
{
	TArray<AActor*> Found;
	int32 Collected = 0;
	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
		AActor* Actor = *It;
		if (Actor == nullptr || !Actor->Implements<UWTAInteractable>())
		{
			continue;
		}
		if (Actor->IsHidden())
		{
			++Collected;   // collected tokens hide
			continue;
		}
		if (Actor->IsA<AWTASeatActor>())
		{
			continue;      // the seats phase sits on every one of them
		}
		// "only=<text>" keeps the interactables whose row id or actor name contains <text>.
		if (PeopleFilter.Num() > 0)
		{
			const FString Id = InteractRowId(Actor).ToString() + TEXT(" ") + Actor->GetName();
			if (!PeopleFilter.ContainsByPredicate([&Id](const FString& Part) { return Id.Contains(Part); }))
			{
				continue;
			}
		}
		Found.Add(Actor);
	}
	// Grouped by class (books, exhibits, rides, staff, stations, tokens), then by name.
	Found.Sort([](const AActor& A, const AActor& B)
	{
		const FString ClassA = A.GetClass()->GetName();
		const FString ClassB = B.GetClass()->GetName();
		return ClassA != ClassB ? ClassA < ClassB : A.GetName() < B.GetName();
	});
	const int32 Count = Found.Num();
	Steps.Add({ TEXT("interact start"), [this, Count, Collected]() -> float
	{
		Report(TEXT("interact"), EResult::Info, TEXT("interactables"), FString::Printf(TEXT("%d to try, %d hidden (collected tokens)"), Count, Collected));
		return 0.f;
	} });
	TMap<UClass*, int32> PerClass;
	for (AActor* Actor : Found)
	{
		int32& Index = PerClass.FindOrAdd(Actor->GetClass());
		AddInteractTest(Actor, Index++);
	}
}

void UWTAPlayTest::AddInteractTest(AActor* Actor, int32 ClassIndex)
{
	struct FState
	{
		bool bOk = false;
		int32 Try = 0;
		FString Label;
		int32 PageBefore = -2;
	};
	const TWeakObjectPtr<AActor> Weak(Actor);
	const FString Kind = Actor->GetClass()->GetName().Replace(TEXT("WTA"), TEXT("")).Replace(TEXT("Actor"), TEXT("")).Replace(TEXT("NPC"), TEXT(""));
	const FString Name = FString::Printf(TEXT("%s %s (%s)"), *Kind, *InteractRowId(Actor).ToString(), *Actor->GetName());
	const FString ShotName = FString::Printf(TEXT("%s_%02d"), *Kind.ToLower(), ClassIndex);
	const TSharedRef<FState> S = MakeShared<FState>();
	const bool bToken = Actor->IsA<AWTATokenActor>();
	const bool bBook = Actor->IsA<AWTABookActor>();

	// A token only a ride reaches (the rides are a later build): out of reach on foot is right for it.
	FName RideGate;
	if (const AWTATokenActor* Token = Cast<AWTATokenActor>(Actor))
	{
		const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
		const FWTATokenRow* Row = Content != nullptr ? Content->FindToken(Token->TokenId) : nullptr;
		RideGate = Row != nullptr ? Row->RideGate : NAME_None;
	}
	const bool bGated = !RideGate.IsNone();
	auto OutOfReach = [this, Name, RideGate](const FString& Why)
	{
		if (!RideGate.IsNone())
		{
			Report(TEXT("interact"), EResult::Pass, Name, FString::Printf(TEXT("out of reach on foot, as it should be: the %s ride gets it (a later build)"),
				*RideGate.ToString()));
		}
		else
		{
			Report(TEXT("interact"), EResult::Fail, Name, Why);
		}
	};

	// 1. Stand at its view spot (where travel puts the player), else in front of it.
	Steps.Add({ Name, [this, Weak, Name, S, OutOfReach]() -> float
	{
		S->bOk = false;
		AActor* Target = Weak.Get();
		if (Target == nullptr)
		{
			Report(TEXT("interact"), EResult::Skip, Name, TEXT("gone"));
			return 0.f;
		}
		CloseAll();
		FWTAView View;
		S->Try = 0;
		bool bHave = IWTAInteractable::Execute_GetViewSpot(Target, View) && View.bValid;
		FString Why;
		if (!bHave)
		{
			S->Try = 1;
			bHave = FindAimView(Target, View, &Why);
		}
		if (!bHave)
		{
			OutOfReach(TEXT("no clear spot to stand and look at it, ") + Why);
			return 0.f;
		}
		StandAt(View);
		S->bOk = true;
		return 0.45f;
	} });

	// 2. The crosshair must name it. When the view spot frames it so something else is under the crosshair,
	//    try straight in front of it before calling it a failure.
	Steps.Add({ Name + TEXT(" hover"), [this, Weak, Name, ShotName, S, OutOfReach, bGated]() -> float
	{
		if (!S->bOk)
		{
			return 0.f;
		}
		AActor* Target = Weak.Get();
		AWTAPlayerController* Controller = PC();
		if (Target == nullptr || Controller == nullptr || Controller->Interaction == nullptr)
		{
			S->bOk = false;
			return 0.f;
		}
		if (Controller->Interaction->GetHovered() == Target)
		{
			return 0.f;
		}
		FString Why;
		if (S->Try == 0)
		{
			FWTAView Aim;
			if (FindAimView(Target, Aim, &Why))
			{
				S->Try = 1;
				StandAt(Aim);
				return -0.45f;
			}
		}
		S->bOk = false;
		if (bGated)
		{
			OutOfReach(Why);
			return 0.f;
		}
		const AActor* Other = Controller->Interaction->GetHovered();
		Report(TEXT("interact"), EResult::Fail, Name, FString::Printf(TEXT("the crosshair does not reach it (%s under it; %s)%s%s"),
			Other != nullptr ? *Other->GetName() : TEXT("nothing"), *DescribeAim(Target),
			Why.IsEmpty() ? TEXT("") : TEXT("; no spot to aim from, "), *Why));
		Shot(TEXT("interact_nohover_") + ShotName);
		// Hold this view for the screenshot (taken at the end of a frame) before the next test moves the player.
		return 0.3f;
	} });

	// 3. E.
	Steps.Add({ Name + TEXT(" E"), [this, Weak, S]() -> float
	{
		if (!S->bOk || Weak.Get() == nullptr)
		{
			return 0.f;
		}
		S->Label = IWTAInteractable::Execute_GetInteractLabel(Weak.Get()).ToString();
		KeyDown(EKeys::E);
		return 0.12f;
	} });
	Steps.Add({ Name + TEXT(" E up"), [this, S]() -> float
	{
		if (!S->bOk)
		{
			return 0.f;
		}
		KeyUp(EKeys::E);
		return 0.75f;
	} });

	// 4. What opened?
	Steps.Add({ Name + TEXT(" check"), [this, Weak, Name, ShotName, S, ClassIndex]() -> float
	{
		AActor* Target = Weak.Get();
		AWTAPlayerController* Controller = PC();
		if (!S->bOk || Target == nullptr || Controller == nullptr)
		{
			return 0.f;
		}
		const UWTAPanelWidget* Panel = Controller->Panel;
		const bool bPanel = Panel != nullptr && Panel->IsOpen();
		auto PanelIs = [&](EWTAPanelMode Mode, FName Id) { return bPanel && Panel->GetMode() == Mode && Panel->GetCurrentId() == Id; };
		FString Expected;
		bool bPass = false;
		bool bShot = ClassIndex < 2;
		if (const AWTAExhibitActor* Exhibit = Cast<AWTAExhibitActor>(Target))
		{
			Expected = TEXT("exhibit card ") + Exhibit->ItemId.ToString();
			bPass = PanelIs(EWTAPanelMode::Exhibit, Exhibit->ItemId);
		}
		else if (const AWTABookActor* Book = Cast<AWTABookActor>(Target))
		{
			Expected = TEXT("book ") + Book->BookId.ToString();
			bPass = PanelIs(EWTAPanelMode::Book, Book->BookId);
		}
		else if (const AWTAStationActor* Station = Cast<AWTAStationActor>(Target))
		{
			Expected = TEXT("station ") + Station->StationId.ToString();
			bPass = PanelIs(EWTAPanelMode::Station, Station->StationId);
		}
		else if (const AWTARideActor* Ride = Cast<AWTARideActor>(Target))
		{
			Expected = TEXT("ride card ") + Ride->RideId.ToString();
			bPass = PanelIs(EWTAPanelMode::Ride, Ride->RideId);
		}
		else if (const AWTAStaffNPC* Staff = Cast<AWTAStaffNPC>(Target))
		{
			Expected = TEXT("chat with ") + Staff->StaffId.ToString();
			bPass = Controller->Chat != nullptr && Controller->Chat->IsOpen() && Controller->Chat->GetStaffId() == Staff->StaffId;
		}
		else if (const AWTATokenActor* Token = Cast<AWTATokenActor>(Target))
		{
			const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
			const FWTATokenRow* Row = Content != nullptr ? Content->FindToken(Token->TokenId) : nullptr;
			const bool bGated = Row != nullptr && !Row->RideGate.IsNone();
			const UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this);
			const bool bGot = Progress != nullptr && Progress->HasToken(Token->TokenId);
			Expected = bGated ? FString::Printf(TEXT("token %s stays (needs the %s ride, a later build)"), *Token->TokenId.ToString(), *Row->RideGate.ToString())
				: FString::Printf(TEXT("token %s collected"), *Token->TokenId.ToString());
			bPass = bGated ? !bGot : (bGot && Token->IsCollected());
			bShot = ClassIndex < 1;
		}
		else
		{
			Expected = TEXT("something");
			bPass = Controller->IsAnyPanelOpen();
		}
		FString Got = TEXT("nothing open");
		if (Controller->Chat != nullptr && Controller->Chat->IsOpen())
		{
			Got = TEXT("chat with ") + Controller->Chat->GetStaffId().ToString();
		}
		else if (bPanel)
		{
			Got = FString::Printf(TEXT("panel %s %s page %d"), PanelModeName(Panel->GetMode()), *Panel->GetCurrentId().ToString(), Panel->GetCurrentPage());
		}
		Report(TEXT("interact"), bPass ? EResult::Pass : EResult::Fail, FString::Printf(TEXT("%s \"%s\""), *Name, *S->Label),
			FString::Printf(TEXT("expected %s; %s"), *Expected, *Got));
		if (bShot || !bPass)
		{
			Shot(TEXT("interact_") + ShotName);
		}
		if (!bPass)
		{
			S->bOk = false;
		}
		return 0.2f;
	} });

	// 5. Books: the right arrow turns the page.
	if (bBook)
	{
		Steps.Add({ Name + TEXT(" page"), [this, S]() -> float
		{
			AWTAPlayerController* Controller = PC();
			if (!S->bOk || Controller == nullptr || Controller->Panel == nullptr)
			{
				return 0.f;
			}
			S->PageBefore = Controller->Panel->GetCurrentPage();
			KeyDown(EKeys::Right);
			return 0.12f;
		} });
		Steps.Add({ Name + TEXT(" page up"), [this, S]() -> float
		{
			if (!S->bOk)
			{
				return 0.f;
			}
			KeyUp(EKeys::Right);
			return 0.5f;
		} });
		Steps.Add({ Name + TEXT(" page check"), [this, Weak, Name, ShotName, S, ClassIndex]() -> float
		{
			AWTAPlayerController* Controller = PC();
			const AWTABookActor* Book = Cast<AWTABookActor>(Weak.Get());
			if (!S->bOk || Controller == nullptr || Controller->Panel == nullptr || Book == nullptr)
			{
				return 0.f;
			}
			const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
			const FWTABookRow* Row = Content != nullptr ? Content->FindBook(Book->BookId) : nullptr;
			const int32 Last = Row != nullptr ? Row->Pages.Num() - 1 : 0;
			const int32 After = Controller->Panel->GetCurrentPage();
			const bool bPass = S->PageBefore >= Last ? After == S->PageBefore : After == S->PageBefore + 1;
			Report(TEXT("interact"), bPass ? EResult::Pass : EResult::Fail, Name + TEXT(" right arrow turns the page"),
				FString::Printf(TEXT("page %d -> %d of %d"), S->PageBefore, After, Last + 1));
			if (ClassIndex < 1 || !bPass)
			{
				Shot(TEXT("book_page_") + ShotName);
			}
			return 0.1f;
		} });
	}

	// 6. Esc closes it. A token opens nothing, and Esc would open the pause menu.
	if (!bToken)
	{
		Steps.Add({ Name + TEXT(" esc"), [this, S]() -> float
		{
			if (!S->bOk)
			{
				return 0.f;
			}
			KeyDown(EKeys::Escape);
			return 0.12f;
		} });
		Steps.Add({ Name + TEXT(" esc up"), [this, S]() -> float
		{
			if (!S->bOk)
			{
				return 0.f;
			}
			KeyUp(EKeys::Escape);
			return 0.45f;
		} });
		Steps.Add({ Name + TEXT(" closed"), [this, Name, S]() -> float
		{
			if (!S->bOk)
			{
				return 0.f;
			}
			AWTAPlayerController* Controller = PC();
			const bool bOpen = Controller != nullptr && Controller->IsAnyPanelOpen();
			Report(TEXT("interact"), bOpen ? EResult::Fail : EResult::Pass, Name + TEXT(" Esc closes it"), bOpen ? TEXT("still open") : TEXT("closed"));
			CloseAll();
			return 0.15f;
		} });
	}
}

bool UWTAPlayTest::FindAimView(AActor* Actor, FWTAView& OutView, FString* OutWhy) const
{
	const UWorld* World = GetWorld();
	const AWTACharacter* Character = Player();
	if (World == nullptr || Actor == nullptr || Character == nullptr)
	{
		return false;
	}
	const FBox Box = Actor->GetComponentsBoundingBox(true);
	if (!Box.IsValid)
	{
		return false;
	}
	FVector Target = Box.GetCenter();
	if (Actor->IsA<AWTAStaffNPC>())
	{
		Target = Actor->GetActorLocation() + FVector(0.f, 0.f, 40.f);
	}
	// Tall things (a ride's tower) are looked at low down, where a visitor would click them.
	Target.Z = FMath::Min(Target.Z, Box.Min.Z + 250.0);
	const FVector Extent = Box.GetExtent();
	const double Reach = FMath::Clamp(FMath::Max(Extent.X, Extent.Y) + 110.0, 140.0, 450.0);
	const FVector Forward = Actor->GetActorForwardVector().GetSafeNormal2D();
	const double BaseYaw = Forward.IsNearlyZero() ? 0.0 : FMath::RadiansToDegrees(FMath::Atan2(Forward.Y, Forward.X));
	FCollisionQueryParams Params(FName(TEXT("WTAPlayAim")), false, Character);
	int32 NoFloor = 0;
	int32 NoRoom = 0;
	int32 SeesNothing = 0;
	int32 Steep = 0;
	TMap<FString, int32> Blockers;
	// Close first, then further out (a hidden token is often seen from across the room; hover reaches 15 m).
	const double Distances[] = { Reach, Reach + 150.0, Reach + 350.0, Reach + 600.0, 1000.0, 1300.0 };
	for (const double Distance : Distances)
	{
		for (int32 i = 0; i < 24; ++i)
		{
			// The actor's forward first, then alternately left and right of it.
			const int32 Ring = (i + 1) / 2;
			const double Side = (i % 2 == 1) ? 1.0 : -1.0;
			const double Yaw = BaseYaw + Side * Ring * 15.0;
			const FVector Stand = Target + FRotator(0.0, Yaw, 0.0).Vector() * Distance;
			// The campus is one storey (floors at 0 to 20 cm, a stage platform): search down from 1.2 m, under every
			// ceiling (a token up on a cabinet would otherwise start the search above the room's ceiling), and stand
			// only on floor, not on a desk or a shelf.
			double FloorZ = 0.0;
			if (!FloorUnder(World, Stand.X, Stand.Y, 120.0, Character, FloorZ) || FloorZ > 50.0)
			{
				++NoFloor;
				continue;
			}
			if (!CapsuleFits(World, Stand.X, Stand.Y, FloorZ, Character))
			{
				++NoRoom;
				continue;
			}
			const FVector Eye(Stand.X, Stand.Y, FloorZ + Character->EyeHeight);
			const FRotator Look = (Target - Eye).Rotation();
			if (FMath::Abs(Look.Pitch) > 75.0)
			{
				++Steep;
				continue;
			}
			FHitResult Hit;
			if (!World->LineTraceSingleByChannel(Hit, Eye, Target, ECC_Visibility, Params))
			{
				++SeesNothing;
				continue;
			}
			if (Hit.GetActor() != Actor)
			{
				++Blockers.FindOrAdd(GetNameSafe(Hit.GetActor()));
				continue;
			}
			OutView.Location = Eye;
			OutView.Yaw = static_cast<float>(Look.Yaw);
			OutView.Pitch = static_cast<float>(Look.Pitch);
			OutView.bValid = true;
			return true;
		}
	}
	if (OutWhy != nullptr)
	{
		Blockers.ValueSort([](int32 A, int32 B) { return A > B; });
		FString Blocked;
		int32 Shown = 0;
		for (const TPair<FString, int32>& Pair : Blockers)
		{
			if (Shown++ < 3)
			{
				Blocked += FString::Printf(TEXT("%s%s x%d"), Blocked.IsEmpty() ? TEXT("") : TEXT(", "), *Pair.Key, Pair.Value);
			}
		}
		*OutWhy = FString::Printf(TEXT("of %d spots: %d no floor, %d no room to stand, %d too steep, %d see nothing at its centre (%s), blocked: %s"),
			static_cast<int32>(UE_ARRAY_COUNT(Distances)) * 24, NoFloor, NoRoom, Steep, SeesNothing, *Target.ToCompactString(), Blocked.IsEmpty() ? TEXT("none") : *Blocked);
	}
	return false;
}

// --- acting ----------------------------------------------------------------------------------

void UWTAPlayTest::AddActingPhase()
{
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	UWorld* World = GetWorld();
	if (Content == nullptr || World == nullptr)
	{
		return;
	}
	// Every stage in the hall, by scene id, so a shot can be matched to its row.
	TMap<FName, AWTAWaxStageActor*> Stages;
	for (TActorIterator<AWTAWaxStageActor> It(World); It; ++It)
	{
		Stages.Add(It->SceneId, *It);
	}
	for (const FName& SceneName : Content->GetRowNames(EWTATable::WaxScenes))
	{
		const FWTAWaxSceneRow* Row = Content->FindWaxScene(SceneName);
		AWTAWaxStageActor** Found = Stages.Find(SceneName);
		if (Row == nullptr || Found == nullptr || *Found == nullptr)
		{
			continue;
		}
		AWTAWaxStageActor* Stage = *Found;
		const FString Name = SceneName.ToString();
		// The aisle, 4.2 m in front of the stage: what a visitor sees walking up.
		FWTAView View;
		View.Location = Row->StageLocation + FRotator(0.f, Row->StageYaw, 0.f).Vector() * 420.f;
		View.Location.Z = 162.f;
		View.Yaw = Row->StageYaw + 180.f;
		View.Pitch = -6.f;
		View.bValid = true;
		Steps.Add({ TEXT("acting at ") + Name, [this, View]() -> float
		{
			CloseAll();
			StandAt(View);
			// Long enough for the figures to wake and their LODs to settle before the first shot.
			return 1.2f;
		} });
		// Six shots across the loop: enough to see every beat change and catch a figure stuck or sliding.
		const float Loop = Row->LoopSeconds > 0.f ? Row->LoopSeconds : 14.f;
		for (int32 Shot_ = 0; Shot_ < 6; ++Shot_)
		{
			const int32 Which = Shot_;
			Steps.Add({ FString::Printf(TEXT("acting %s %d"), *Name, Which), [this, Name, Which, Stage]() -> float
			{
				Shot(FString::Printf(TEXT("acting_%s_%d"), *Name, Which));
				if (IsValid(Stage))
				{
					UE_LOG(LogWTA, Display, TEXT("WTA_PLAY acting INFO %s"), *Stage->DescribeActing());
				}
				return 0.1f;
			} });
			Steps.Add({ FString::Printf(TEXT("acting %s wait %d"), *Name, Which), [Loop]() -> float { return Loop / 6.f; } });
		}
		// One pass over the figures after a whole loop: still acting, no bones left at the feet.
		Steps.Add({ TEXT("acting check ") + Name, [this, Name, Stage]() -> float
		{
			if (!IsValid(Stage))
			{
				return 0.f;
			}
			int32 Collapsed = 0;
			FString Who;
			for (AActor* Figure : Stage->Figures)
			{
				TInlineComponentArray<USkeletalMeshComponent*> Meshes;
				if (!IsValid(Figure))
				{
					continue;
				}
				Figure->GetComponents(Meshes);
				for (const USkeletalMeshComponent* Mesh : Meshes)
				{
					const int32 Bad = UWTAPeopleLibrary::CountCollapsedBones(Mesh);
					if (Bad > 0)
					{
						Collapsed += Bad;
						Who += (Who.IsEmpty() ? TEXT("") : TEXT(", ")) + Figure->GetName();
						break;
					}
				}
			}
			Report(TEXT("acting"), Stage->IsActing() && Collapsed == 0 ? EResult::Pass : EResult::Fail,
				Name + TEXT(" acts a whole loop"),
				FString::Printf(TEXT("%s, %d bones at the feet%s"), Stage->IsActing() ? TEXT("acting") : TEXT("NOT ACTING"),
					Collapsed, Who.IsEmpty() ? TEXT("") : *(TEXT(" (") + Who + TEXT(")"))));
			return 0.2f;
		} });
	}
}

// --- library ---------------------------------------------------------------------------------

/** Campus metres (x right, y up, z toward the viewer) -> Unreal cm: the mapping the whole project uses. */
static FVector CampusToUE(float cx, float cy, float cz)
{
	return FVector(cx * 100.f, cz * 100.f, cy * 100.f);
}

static FWTAView LookFrom(const FVector& Eye, const FVector& Target)
{
	FWTAView V;
	V.Location = Eye;
	const FVector D = Target - Eye;
	V.Yaw = FMath::RadiansToDegrees(FMath::Atan2(D.Y, D.X));
	V.Pitch = FMath::RadiansToDegrees(FMath::Atan2(D.Z, FVector2D(D.X, D.Y).Size()));
	V.bValid = true;
	return V;
}

void UWTAPlayTest::AddLibraryPhase()
{
	// Five viewpoints through the rebuilt Reading Room, plus the two checks that matter now there is a
	// second storey: that the gallery deck holds the player up, and that the navmesh can actually walk
	// them up the spiral stair to reach it.
	struct FSpot { const TCHAR* Name; FVector Eye; FVector Look; };
	const FVector GalleryStand = CampusToUE(-13.1f, 4.61f, -9.6f);   // on the east gallery, by the stair head
	const FVector StairFoot = CampusToUE(-16.9f, 0.90f, -9.6f);      // on the floor, just off the bottom tread
	const FSpot Spots[] = {
		{ TEXT("hall"),    CampusToUE(-12.7f, 1.62f, -3.0f), CampusToUE(-31.0f, 2.60f, -3.0f) },
		{ TEXT("window"),  CampusToUE(-22.0f, 1.62f, -3.0f), CampusToUE(-32.0f, 2.80f, -3.0f) },
		{ TEXT("stair"),   CampusToUE(-18.4f, 1.62f, -5.2f), CampusToUE(-15.1f, 2.30f, -9.6f) },
		{ TEXT("piano"),   CampusToUE(-18.9f, 1.55f,  0.9f), CampusToUE(-15.4f, 1.05f,  3.3f) },
		{ TEXT("gallery"), CampusToUE(-13.1f, 4.61f, -4.0f), CampusToUE(-26.0f, 1.60f, -3.0f) },
	};
	for (const FSpot& S : Spots)
	{
		const FString Name = S.Name;
		const FWTAView View = LookFrom(S.Eye, S.Look);
		Steps.Add({ TEXT("library at ") + Name, [this, View]() -> float
		{
			CloseAll();
			StandAt(View);
			return 1.5f;
		} });
		Steps.Add({ TEXT("library shot ") + Name, [this, Name]() -> float
		{
			Shot(TEXT("library_") + Name, false);
			return 0.1f;
		} });
	}
	// The gallery is the last spot, so the player is standing on it: did the deck hold them, or did they
	// drop through to the floor 3.7 m below?
	Steps.Add({ TEXT("library gallery holds"), [this, GalleryStand]() -> float
	{
		const AWTACharacter* Me = Player();
		const float Z = Me != nullptr ? Me->GetActorLocation().Z : -1.f;
		Report(TEXT("library"), Z > 300.f ? EResult::Pass : EResult::Fail, TEXT("the gallery deck holds you up"),
			FString::Printf(TEXT("standing at Z %.0f cm, deck is 371"), Z));
		return 0.1f;
	} });
	// Can you climb it? The player walks on collision, not on the navmesh, so the honest test is whether
	// every tread holds them: drop them a little above each one in turn and see where they come to rest.
	// A tread that does not hold drops them to the floor, which shows up as a Z far below the tread.
	const int32 N = 20;
	const float Rise = 3.71f / N;
	for (int32 i = 1; i < N; ++i)
	{
		const float Ang = FMath::DegreesToRadians((i - N) * (300.f / N));
		const float Ty = i * Rise;
		// 0.75 m out from the newel: the middle of the tread, where a foot actually lands.
		const FVector On = CampusToUE(-15.1f + 0.75f * FMath::Cos(Ang), Ty, -9.6f + 0.75f * FMath::Sin(Ang));
		Steps.Add({ FString::Printf(TEXT("library tread %d"), i), [this, On]() -> float
		{
			FWTAView V;
			V.Location = On + FVector(0.f, 0.f, 130.f);   // drop in from above, clear of the tread
			V.Yaw = 0.f; V.Pitch = 0.f; V.bValid = true;
			CloseAll();
			StandAt(V);
			return 0.6f;                                  // long enough to fall the 130 cm and settle
		} });
		Steps.Add({ FString::Printf(TEXT("library tread %d rests"), i), [this, On, i, Ty]() -> float
		{
			const AWTACharacter* Me = Player();
			const float Z = Me != nullptr ? Me->GetActorLocation().Z : -1.f;
			const float Above = Z - On.Z;
			// A capsule dropped on to a tread always gets stepped up on to the next one (its sides reach it),
			// so standing reads as tread + 109: the half-height plus one riser. Anything well off that is
			// the capsule coming to rest somewhere else - a tread or two down, or the landing - which is
			// exactly what a landing built over the top treads produced, so the band is kept tight.
			Report(TEXT("library"), Above > 85.f && Above < 125.f ? EResult::Pass : EResult::Fail,
				FString::Printf(TEXT("tread %d holds your weight"), i),
				FString::Printf(TEXT("tread top %.0f cm, resting at %.0f (%.0f above)"), On.Z, Z, Above));
			return 0.1f;
		} });
	}
	// Now walk it for real, the way a visitor does: from the floor at the stair's entry, hold W and steer along
	// the helix - each tick the heading is set to the tangent of the walking line at the player's own position
	// (climbing is increasing angle about the newel). Nine seconds is three times what the climb takes; by then
	// they are on the landing (Z 461) or they are not. This is the test the drops above are only a proxy for.
	{
		TSharedRef<int32> Polls = MakeShared<int32>(0);
		// Entry: on the floor before tread 1 (which sits at 75 degrees about the newel), at the walking radius,
		// far enough back (40 cm of arc) that the capsule does not land overlapping the tread's edge.
		// (A view's Location is the eye, 1.62 m up: lower and the capsule is teleported into the floor.)
		const float EntryDeg = 45.f;
		const FVector Entry = CampusToUE(-15.1f + 0.95f * FMath::Cos(FMath::DegreesToRadians(EntryDeg)), 1.62f,
		                                 -9.6f + 0.95f * FMath::Sin(FMath::DegreesToRadians(EntryDeg)));
		Steps.Add({ TEXT("library climb start"), [this, Entry, EntryDeg]() -> float
		{
			CloseAll();
			FWTAView V;
			V.Location = Entry;
			V.Yaw = FMath::RadiansToDegrees(FMath::Atan2(FMath::Cos(FMath::DegreesToRadians(EntryDeg)), -FMath::Sin(FMath::DegreesToRadians(EntryDeg))));
			V.Pitch = -10.f;
			V.bValid = true;
			StandAt(V);
			return 1.0f;      // let the teleport settle before any input, as the walk-in test does
		} });
		Steps.Add({ TEXT("library climb go"), [this, Polls]() -> float
		{
			*Polls = 0;
			KeyDown(EKeys::W);
			return 0.1f;
		} });
		Steps.Add({ TEXT("library climb"), [this, Polls]() -> float
		{
			AWTACharacter* Me = Player();
			AWTAPlayerController* C = PC();
			if (Me != nullptr && C != nullptr)
			{
				const FVector P = Me->GetActorLocation();
				const FVector2D Out(P.X + 1510.f, P.Y + 960.f);                  // from the newel (campus -15.1, -9.6)
				const float R = Out.Size();
				const float A = FMath::Atan2(Out.Y, Out.X);
				// Steer along the helix's tangent, bending in or out to hold the walking line at 80 cm from the
				// newel - what a visitor does by eye, and well inside the balustrade for a 60 cm capsule.
				FVector2D Dir = FVector2D(-FMath::Sin(A), FMath::Cos(A)) + (Out / FMath::Max(R, 1.f)) * ((80.f - R) / 40.f);
				Dir.Normalize();
				C->SetControlRotation(FRotator(-10.f, FMath::RadiansToDegrees(FMath::Atan2(Dir.Y, Dir.X)), 0.f));
				if (*Polls % 10 == 0)
				{
					UE_LOG(LogWTA, Display, TEXT("WTA_PLAY library INFO climb %.1f s: %.0f deg, %.0f cm out, Z %.0f"),
						*Polls * 0.1f, FMath::RadiansToDegrees(A), R, P.Z);
				}
			}
			if (++(*Polls) < 90)
			{
				return -0.1f;
			}
			KeyUp(EKeys::W);
			const FVector End = Me != nullptr ? Me->GetActorLocation() : FVector(-1.f);
			const float Ang = FMath::RadiansToDegrees(FMath::Atan2(End.Y + 960.f, End.X + 1510.f));
			// What is the capsule actually touching, and what stops it going forward? Ask the physics scene.
			if (Me != nullptr && GetWorld() != nullptr)
			{
				const UCapsuleComponent* Cap = Me->GetCapsuleComponent();
				const float Rad = Cap->GetScaledCapsuleRadius(), Half = Cap->GetScaledCapsuleHalfHeight();
				FCollisionQueryParams Q(FName(TEXT("WTAClimbProbe")), true, Me);
				TArray<FOverlapResult> Touch;
				GetWorld()->OverlapMultiByChannel(Touch, End, FQuat::Identity, ECC_Pawn, FCollisionShape::MakeCapsule(Rad + 2.f, Half + 2.f), Q);
				FString Names;
				for (const FOverlapResult& O : Touch)
				{
					Names += FString::Printf(TEXT("%s/%s "), O.GetActor() ? *O.GetActor()->GetActorLabel() : TEXT("?"), O.GetComponent() ? *O.GetComponent()->GetName() : TEXT("?"));
				}
				const FVector Fwd = C != nullptr ? C->GetControlRotation().Vector().GetSafeNormal2D() : FVector::ForwardVector;
				FHitResult Sweep;
				const bool bBlocked = GetWorld()->SweepSingleByChannel(Sweep, End, End + Fwd * 30.f, FQuat::Identity, ECC_Pawn, FCollisionShape::MakeCapsule(Rad, Half), Q);
				UE_LOG(LogWTA, Display, TEXT("WTA_PLAY library INFO climb touching: %s| forward 30 cm: %s %s at %s normal %s"),
					*Names, bBlocked ? TEXT("blocked by") : TEXT("clear"),
					bBlocked && Sweep.GetActor() ? *Sweep.GetActor()->GetActorLabel() : TEXT(""),
					bBlocked ? *Sweep.ImpactPoint.ToCompactString() : TEXT("-"), bBlocked ? *Sweep.ImpactNormal.ToCompactString() : TEXT("-"));
			}
			Report(TEXT("library"), End.Z > 440.f ? EResult::Pass : EResult::Fail, TEXT("you can walk up the stair to the gallery"),
				FString::Printf(TEXT("after 9 s of climbing, at %s - Z %.0f cm, %.0f deg round the newel, %.0f cm out; the landing puts you at 461"),
					*End.ToCompactString(), End.Z, Ang, FVector2D(End.X + 1510.f, End.Y + 960.f).Size()));
			return 0.3f;
		} });
	}
	// The navmesh is a separate question and only affects walk-to-view, not the player's own feet: Recast
	// erodes a spiral this tight away entirely (each tread is ~19 cm across at the walking line, narrower
	// than the agent). Reported, not failed.
	Steps.Add({ TEXT("library stair navmesh"), [this, StairFoot, GalleryStand]() -> float
	{
		UNavigationSystemV1* Nav = UNavigationSystemV1::GetCurrent(GetWorld());
		const UNavigationPath* Path = Nav ? Nav->FindPathToLocationSynchronously(GetWorld(), StairFoot, GalleryStand) : nullptr;
		const bool bOk = Path != nullptr && Path->IsValid() && !Path->IsPartial();
		Report(TEXT("library"), EResult::Info, TEXT("navmesh path up the stair"),
			FString::Printf(TEXT("%s, %.0f cm - walk-to-view cannot route to the gallery until a nav link is added"),
				bOk ? TEXT("found") : TEXT("not found"), Path != nullptr ? Path->GetPathLength() : 0.f));
		return 0.1f;
	} });
}

// --- museum ----------------------------------------------------------------------------------

void UWTAPlayTest::AddMuseumPhase()
{
	// Ten viewpoints from the forecourt path to the end of gallery 3 through the rebuilt museum (bl/museum.py:
	// portico, rotunda, lobby, vaulted galleries), then the walk a visitor makes: from the path, up the steps,
	// across the portico, through the front doors and the rotunda into the lobby, holding W. The forecourt
	// lies 0.75 m below the floors, so the eyes out there are at 0.87 m.
	struct FSpot { const TCHAR* Name; FVector Eye; FVector Look; };
	const FSpot Spots[] = {
		{ TEXT("approach"), CampusToUE( 0.0f, 0.87f,  40.0f), CampusToUE( 0.0f,  8.0f,  10.0f) },
		{ TEXT("steps"),    CampusToUE( 0.0f, 0.87f,  19.5f), CampusToUE( 0.0f,  5.0f,  12.0f) },
		{ TEXT("portico"),  CampusToUE( 0.0f, 1.62f,  14.8f), CampusToUE( 0.0f,  3.0f,   5.0f) },
		{ TEXT("rotunda"),  CampusToUE( 0.0f, 1.62f,   9.6f), CampusToUE( 0.0f,  4.5f,   0.0f) },
		{ TEXT("dome"),     CampusToUE( 0.0f, 1.62f,   5.8f), CampusToUE( 0.3f, 14.0f,   5.6f) },
		{ TEXT("lobby"),    CampusToUE( 0.0f, 1.62f,  -1.2f), CampusToUE( 0.0f,  2.8f, -12.0f) },
		{ TEXT("gallery"),  CampusToUE( 0.0f, 1.62f,  -7.0f), CampusToUE( 0.0f,  3.2f, -20.0f) },
		{ TEXT("bay"),      CampusToUE(-1.2f, 1.62f, -12.5f), CampusToUE(-6.0f,  2.2f,  -9.0f) },
		{ TEXT("vault"),    CampusToUE(-3.0f, 1.62f,  -8.0f), CampusToUE( 2.0f,  7.8f, -15.0f) },
		{ TEXT("end"),      CampusToUE( 0.0f, 1.62f, -31.0f), CampusToUE( 0.0f,  2.5f, -42.0f) },
		// the marble statues: on the west cheek block of the steps, and before the rotunda's west window
		{ TEXT("statue_steps"),   CampusToUE(-6.3f, 0.87f,  21.2f), CampusToUE(-8.65f, 1.25f, 17.2f) },
		{ TEXT("statue_rotunda"), CampusToUE( 1.2f, 1.62f,   5.8f), CampusToUE(-3.9f,  1.75f,  5.8f) },
		// the library's exit: from the reading room toward the hall, from an angle, and back from the hall
		{ TEXT("libexit_out"),    CampusToUE(-17.0f, 1.62f, -3.0f), CampusToUE(-11.0f, 1.5f, -3.0f) },
		{ TEXT("libexit_angle"),  CampusToUE(-15.0f, 1.62f, -7.5f), CampusToUE(-11.6f, 1.6f, -3.0f) },
		{ TEXT("libexit_back"),   CampusToUE( -8.5f, 1.62f, -3.0f), CampusToUE(-13.5f, 1.5f, -3.0f) },
		{ TEXT("waxdoor"),        CampusToUE(  0.0f, 1.62f, -37.0f), CampusToUE(0.0f, 1.2f, -44.0f) },
		{ TEXT("schooldoor"),     CampusToUE(  4.0f, 1.62f, -3.0f), CampusToUE(12.5f, 1.2f, -3.0f) },
	};
	for (const FSpot& S : Spots)
	{
		const FString Name = S.Name;
		const FWTAView View = LookFrom(S.Eye, S.Look);
		Steps.Add({ TEXT("museum at ") + Name, [this, View]() -> float
		{
			CloseAll();
			StandAt(View);
			return 1.5f;
		} });
		Steps.Add({ TEXT("museum shot ") + Name, [this, Name]() -> float
		{
			Shot(TEXT("museum_") + Name, false);
			return 0.1f;
		} });
	}
	// Thresholds: nothing to climb between the buildings. Along each passage, the floor under a ray every 10 cm
	// must stay within a sill's height (20 cm) of the passage's lowest floor; a kerb names the mesh that is one.
	struct FPassage { const TCHAR* Name; FVector2D From; FVector2D To; };
	const FPassage Passages[] = {
		{ TEXT("lobby to the library"),      FVector2D(-5.0f, -3.0f),  FVector2D(-15.0f, -3.0f) },
		{ TEXT("lobby to the school"),       FVector2D( 5.0f, -3.0f),  FVector2D( 15.0f, -3.0f) },
		{ TEXT("gallery 3 to the Wax Hall"), FVector2D( 0.0f, -38.0f), FVector2D(  0.0f, -47.0f) },
		{ TEXT("forecourt to the rotunda"),  FVector2D( 0.0f,  16.5f), FVector2D(  0.0f,   7.0f) },
	};
	for (const FPassage& P : Passages)
	{
		const FString Name = P.Name;
		const FVector2D From = P.From, To = P.To;
		Steps.Add({ TEXT("museum threshold ") + Name, [this, Name, From, To]() -> float
		{
			UWorld* World = GetWorld();
			float Low = TNumericLimits<float>::Max(), High = -TNumericLimits<float>::Max();
			FString Kerb;
			const int32 Samples = FMath::Max(2, FMath::RoundToInt(FVector2D::Distance(From, To) * 10.f));
			for (int32 i = 0; i <= Samples; ++i)
			{
				const FVector2D At = FMath::Lerp(From, To, static_cast<float>(i) / Samples);
				const FVector Top = CampusToUE(At.X, 1.5f, At.Y), Bottom = CampusToUE(At.X, -1.5f, At.Y);
				FHitResult Hit;
				FCollisionQueryParams Params(FName(TEXT("WTAThreshold")), true);
				if (const AWTACharacter* Me = Player()) { Params.AddIgnoredActor(Me); }
				if (World != nullptr && World->LineTraceSingleByChannel(Hit, Top, Bottom, ECC_Visibility, Params))
				{
					Low = FMath::Min(Low, static_cast<float>(Hit.Location.Z));
					if (Hit.Location.Z > High)
					{
						High = static_cast<float>(Hit.Location.Z);
						Kerb = FString::Printf(TEXT("%s at campus (%.1f, %.1f)"), Hit.GetComponent() ? *Hit.GetComponent()->GetName() : TEXT("?"), At.X, At.Y);
					}
				}
			}
			const bool bOk = Low < High && High - Low <= 20.f;
			Report(TEXT("museum"), Low <= High ? (bOk ? EResult::Pass : EResult::Fail) : EResult::Skip, TEXT("nothing to climb from the ") + Name,
				Low <= High ? FString::Printf(TEXT("floor from %.0f to %.0f cm; highest: %s"), Low, High, *Kerb) : TEXT("no floor found"));
			return 0.1f;
		} });
	}
	// The statues: every one placed (Pipeline/content/statues.json) has its figure built and carved in marble.
	Steps.Add({ TEXT("museum statues"), [this]() -> float
	{
		int32 Placed = 0, Built = 0, Marble = 0;
		FString Notes;
		for (TActorIterator<AWTAStatueActor> It(GetWorld()); It; ++It)
		{
			++Placed;
			AWTAStatueActor* Statue = *It;
			if (Statue->Figure == nullptr)
			{
				Notes += Statue->Describe() + TEXT("; ");
				continue;
			}
			++Built;
			const USkeletalMeshComponent* Body = UWTAPeopleLibrary::FindBody(Statue->Figure);
			const UMaterialInterface* Skin = Body != nullptr && Body->GetNumMaterials() > 0 ? Body->GetMaterial(0) : nullptr;
			if (Skin != nullptr && Skin->GetName().Contains(TEXT("Marble")))
			{
				++Marble;
			}
			else
			{
				Notes += Statue->Describe() + FString::Printf(TEXT(" wears %s; "), Skin != nullptr ? *Skin->GetName() : TEXT("nothing"));
			}
		}
		const bool bOk = Placed > 0 && Built == Placed && Marble == Placed;
		Report(TEXT("museum"), bOk ? EResult::Pass : (Placed == 0 ? EResult::Skip : EResult::Fail), TEXT("the statues stand in marble"),
			FString::Printf(TEXT("%d placed, %d built, %d in marble%s%s"), Placed, Built, Marble, Notes.IsEmpty() ? TEXT("") : TEXT(": "), *Notes));
		return 0.1f;
	} });
	// Does the floor hold where the new building meets the old: the stylobate, the door passage, the rotunda,
	// the lobby arch, the halls' thresholds? Drop in a little above each spot and read the resting height.
	struct FFloor { const TCHAR* Name; FVector On; };
	const FFloor Floors[] = {
		{ TEXT("forecourt path"), CampusToUE(0.0f, -0.75f, 24.0f) },
		{ TEXT("third step"),     CampusToUE(0.0f, -0.45f, 17.35f) },
		{ TEXT("stylobate"),      CampusToUE(0.0f,  0.00f, 14.8f) },
		{ TEXT("front door"),     CampusToUE(0.0f,  0.00f, 11.8f) },
		{ TEXT("rotunda floor"),  CampusToUE(0.0f,  0.00f,  5.8f) },
		{ TEXT("lobby arch"),     CampusToUE(0.0f,  0.00f,  0.4f) },
		{ TEXT("hall threshold"), CampusToUE(-6.1f, 0.00f, -3.0f) },
	};
	for (const FFloor& F : Floors)
	{
		const FString Name = F.Name;
		const FVector On = F.On;
		Steps.Add({ TEXT("museum drop ") + Name, [this, On]() -> float
		{
			FWTAView V;
			V.Location = On + FVector(0.f, 0.f, 200.f);
			V.Yaw = -90.f; V.Pitch = 0.f; V.bValid = true;
			CloseAll();
			StandAt(V);
			return 0.8f;
		} });
		Steps.Add({ TEXT("museum rests ") + Name, [this, On, Name]() -> float
		{
			const AWTACharacter* Me = Player();
			const float Z = Me != nullptr ? Me->GetActorLocation().Z : -1.f;
			const float Above = Z - On.Z;
			// resting = floor + the capsule's half height (90); 70..110 allows a step edge either way
			Report(TEXT("museum"), Above > 70.f && Above < 110.f ? EResult::Pass : EResult::Fail,
				FString::Printf(TEXT("the floor holds at the %s"), *Name),
				FString::Printf(TEXT("floor %.0f cm, resting at %.0f (%.0f above)"), On.Z, Z, Above));
			return 0.1f;
		} });
	}
	// The walk in: from the path, straight north with W held for 14 s (3 m/s: plenty for the 30 m to the lobby).
	{
		TSharedRef<int32> Polls = MakeShared<int32>(0);
		const FVector Start = CampusToUE(0.0f, 0.87f, 26.0f);
		Steps.Add({ TEXT("museum walk-in start"), [this, Start]() -> float
		{
			CloseAll();
			FWTAView V;
			V.Location = Start; V.Yaw = -90.f; V.Pitch = 0.f; V.bValid = true;
			StandAt(V);
			return 1.0f;
		} });
		Steps.Add({ TEXT("museum walk-in go"), [this, Polls]() -> float
		{
			*Polls = 0;
			KeyDown(EKeys::W);
			return 0.1f;
		} });
		Steps.Add({ TEXT("museum walk-in"), [this, Polls]() -> float
		{
			AWTACharacter* Me = Player();
			AWTAPlayerController* C = PC();
			if (C != nullptr)
			{
				C->SetControlRotation(FRotator(0.f, -90.f, 0.f));
			}
			if (Me != nullptr && *Polls % 20 == 0)
			{
				const FVector P = Me->GetActorLocation();
				UE_LOG(LogWTA, Display, TEXT("WTA_PLAY museum INFO walk-in %.1f s: campus z %.1f m, Z %.0f cm"), *Polls * 0.1f, P.Y / 100.f, P.Z);
				if (*Polls == 40 || *Polls == 80)
				{
					Shot(FString::Printf(TEXT("museum_walkin_%02ds"), *Polls / 10), false);
				}
			}
			if (++(*Polls) < 140)
			{
				return -0.1f;
			}
			KeyUp(EKeys::W);
			const FVector End = Me != nullptr ? Me->GetActorLocation() : FVector(-1.f);
			Report(TEXT("museum"), End.Y < -100.f ? EResult::Pass : EResult::Fail, TEXT("you can walk in from the path to the lobby"),
				FString::Printf(TEXT("after 14 s walking north from the path: campus (%.1f, %.1f), Z %.0f cm - the lobby arch is at z 0"),
					End.X / 100.f, End.Y / 100.f, End.Z));
			return 0.3f;
		} });
	}
	// The navmesh (walk-to-view) from the path to the lobby.
	Steps.Add({ TEXT("museum navmesh"), [this]() -> float
	{
		UNavigationSystemV1* Nav = UNavigationSystemV1::GetCurrent(GetWorld());
		const FVector A = CampusToUE(0.0f, -0.75f, 24.0f), B = CampusToUE(0.0f, 0.0f, -3.0f);
		const UNavigationPath* Path = Nav ? Nav->FindPathToLocationSynchronously(GetWorld(), A, B) : nullptr;
		const bool bOk = Path != nullptr && Path->IsValid() && !Path->IsPartial();
		Report(TEXT("museum"), bOk ? EResult::Pass : EResult::Info, TEXT("navmesh path from the forecourt to the lobby"),
			FString::Printf(TEXT("%s, %.0f cm"), bOk ? TEXT("found") : TEXT("not found"), Path != nullptr ? Path->GetPathLength() : 0.f));
		return 0.1f;
	} });
}

void UWTAPlayTest::AddDoorsPhase()
{
	// Every doorway a visitor walks through, as a pair of points either side of it (campus metres, feet on the
	// floor). From A: a no-HUD shot looking at the door, then W held toward B until there or out of time. The walk
	// must arrive within 60 cm of B, and the feet must never rise more than 12 cm above where they started: a kerb,
	// a sill or a plinth across a door is a thing to climb, and nothing should be. Then the same from B back to A.
	struct FDoor { const TCHAR* Name; FVector A; FVector B; };
	const FDoor Doors[] = {
		{ TEXT("front door"),     CampusToUE( 0.0f,  0.00f,  14.0f), CampusToUE( 0.0f,  0.0f,   9.0f) },
		{ TEXT("lobby arch"),     CampusToUE( 0.0f,  0.00f,   2.5f), CampusToUE( 0.0f,  0.0f,  -2.5f) },
		{ TEXT("west hall door"), CampusToUE(-3.0f,  0.00f,  -3.0f), CampusToUE(-8.5f,  0.0f,  -3.0f) },
		{ TEXT("east hall door"), CampusToUE( 3.0f,  0.00f,  -3.0f), CampusToUE( 8.5f,  0.0f,  -3.0f) },
		{ TEXT("library door"),   CampusToUE(-8.5f,  0.00f,  -3.0f), CampusToUE(-15.0f, 0.0f,  -3.0f) },
		{ TEXT("school door"),    CampusToUE( 8.5f,  0.00f,  -3.0f), CampusToUE( 15.0f, 0.0f,  -3.0f) },
		{ TEXT("room 101"),       CampusToUE(19.0f,  0.00f,  -3.0f), CampusToUE( 19.0f, 0.0f,  -7.0f) },
		{ TEXT("room 102"),       CampusToUE(29.0f,  0.00f,  -3.0f), CampusToUE( 29.0f, 0.0f,  -7.0f) },
		{ TEXT("room 103"),       CampusToUE(19.0f,  0.00f,  -3.0f), CampusToUE( 19.0f, 0.0f,   1.0f) },
		{ TEXT("room 104"),       CampusToUE(29.0f,  0.00f,  -3.0f), CampusToUE( 29.0f, 0.0f,   1.0f) },
		{ TEXT("yard door"),      CampusToUE(31.0f,  0.00f,  -3.0f), CampusToUE( 37.0f, 0.0f,  -3.0f) },
		{ TEXT("gallery doors"),  CampusToUE( 0.0f,  0.00f,  -9.0f), CampusToUE(  0.0f, 0.0f, -27.0f) },
		{ TEXT("wax hall door"),  CampusToUE( 0.0f,  0.00f, -39.5f), CampusToUE(  0.0f, 0.0f, -43.9f) },
	};
	for (const FDoor& D : Doors)
	{
		for (int32 Dir = 0; Dir < 2; ++Dir)
		{
			const FString Name = D.Name;
			const FVector From = Dir == 0 ? D.A : D.B;
			const FVector To = Dir == 0 ? D.B : D.A;
			const FString Leg = FString::Printf(TEXT("%s %s"), *Name, Dir == 0 ? TEXT("in") : TEXT("out"));
			const FString ShotName = FString::Printf(TEXT("door_%s_%s"), *Name.Replace(TEXT(" "), TEXT("_")), Dir == 0 ? TEXT("in") : TEXT("out"));
			TSharedRef<int32> Polls = MakeShared<int32>(0);
			TSharedRef<float> StartZ = MakeShared<float>(0.f);
			TSharedRef<float> MaxRise = MakeShared<float>(0.f);
			TSharedRef<float> MaxDrop = MakeShared<float>(0.f);
			Steps.Add({ TEXT("doors at ") + Leg, [this, From, To]() -> float
			{
				CloseAll();
				StandAt(LookFrom(From + FVector(0.f, 0.f, 162.f), To + FVector(0.f, 0.f, 150.f)));
				return 1.2f;
			} });
			Steps.Add({ TEXT("doors shot ") + Leg, [this, ShotName]() -> float
			{
				Shot(ShotName, false);
				return 0.1f;
			} });
			Steps.Add({ TEXT("doors go ") + Leg, [this, Polls, StartZ, MaxRise, MaxDrop]() -> float
			{
				*Polls = 0; *MaxRise = 0.f; *MaxDrop = 0.f;
				const AWTACharacter* Me = Player();
				*StartZ = Me != nullptr ? Me->GetActorLocation().Z : 0.f;
				KeyDown(EKeys::W);
				return 0.1f;
			} });
			const int32 MaxPolls = int32((FVector::Dist2D(From, To) / 300.f + 2.0f) * 10.f);
			Steps.Add({ TEXT("doors walk ") + Leg, [this, Leg, From, To, Polls, StartZ, MaxRise, MaxDrop, MaxPolls]() -> float
			{
				AWTACharacter* Me = Player();
				AWTAPlayerController* C = PC();
				if (Me == nullptr || C == nullptr)
				{
					KeyUp(EKeys::W);
					Report(TEXT("doors"), EResult::Fail, Leg, TEXT("no player"));
					return 0.1f;
				}
				const FVector P = Me->GetActorLocation();
				const FVector Heading = (To - P).GetSafeNormal2D();
				C->SetControlRotation(FRotator(0.f, Heading.Rotation().Yaw, 0.f));
				*MaxRise = FMath::Max(*MaxRise, P.Z - *StartZ);
				*MaxDrop = FMath::Max(*MaxDrop, *StartZ - P.Z);
				const float Left = FVector::Dist2D(P, To);
				if (Left > 60.f && ++(*Polls) < MaxPolls)
				{
					return -0.1f;
				}
				KeyUp(EKeys::W);
				const bool bThere = Left <= 60.f;
				const bool bFlat = *MaxRise < 12.f;
				Report(TEXT("doors"), bThere && bFlat ? EResult::Pass : EResult::Fail, TEXT("the way through the ") + Leg + TEXT(" is clear"),
					FString::Printf(TEXT("%s after %.1f s: %.0f cm short of the far side at campus (%.1f, %.1f), feet rose %.0f cm, dropped %.0f cm%s"),
						bThere ? TEXT("arrived") : TEXT("stopped"), *Polls * 0.1f, Left, P.X / 100.f, P.Y / 100.f, *MaxRise, *MaxDrop,
						bFlat ? TEXT("") : TEXT(" - something to climb in the doorway")));
				return 0.3f;
			} });
		}
	}
}

// --- attract ---------------------------------------------------------------------------------

void UWTAPlayTest::AddAttractPhase()
{
	UWorld* World = GetWorld();
	if (World == nullptr)
	{
		return;
	}
	// Every exhibit that knows where you are meant to stand to look at it.
	TArray<AWTAExhibitActor*> Lit;
	for (TActorIterator<AWTAExhibitActor> It(World); It; ++It)
	{
		FWTAView View;
		if (It->Attract != nullptr && IWTAInteractable::Execute_GetViewSpot(*It, View) && View.bValid)
		{
			Lit.Add(*It);
		}
	}
	if (Lit.Num() < 2)
	{
		Report(TEXT("attract"), EResult::Skip, TEXT("exhibits with a view spot"),
			FString::Printf(TEXT("found %d, need 2"), Lit.Num()));
		return;
	}
	// A spread of six rather than all of them: the behaviour is one component's, not each exhibit's.
	const int32 Stride = FMath::Max(1, Lit.Num() / 6);
	for (int32 i = 0; i < Lit.Num(); i += Stride)
	{
		AWTAExhibitActor* Near = Lit[i];
		// The one furthest from it, to prove the light falls off as well as rises.
		AWTAExhibitActor* Far = nullptr;
		float Best = 0.f;
		for (AWTAExhibitActor* Other : Lit)
		{
			const float D = FVector::Dist(Other->GetActorLocation(), Near->GetActorLocation());
			if (D > Best) { Best = D; Far = Other; }
		}
		if (Far == nullptr || Best < 3000.f)
		{
			continue;
		}
		const FString Name = Near->ItemId.ToString();
		FWTAView View;
		IWTAInteractable::Execute_GetViewSpot(Near, View);
		Steps.Add({ TEXT("attract at ") + Name, [this, View]() -> float
		{
			CloseAll();
			StandAt(View);
			return 1.6f;   // longer than the component's smoothing, so the swell has finished
		} });
		Steps.Add({ TEXT("attract shot ") + Name, [this, Name]() -> float
		{
			Shot(TEXT("attract_") + Name, false);
			return 0.1f;
		} });
		Steps.Add({ TEXT("attract check ") + Name, [this, Name, Near, Far, Best]() -> float
		{
			if (!IsValid(Near) || !IsValid(Far) || Near->Attract == nullptr || Far->Attract == nullptr)
			{
				return 0.f;
			}
			const float HereA = Near->Attract->GetAttention();
			const float HereI = Near->Attract->GetIntensity();
			const float ThereA = Far->Attract->GetAttention();
			const bool bUp = HereA > 0.5f && HereI > Near->Attract->RestIntensity;
			const bool bDown = ThereA < 0.1f;
			Report(TEXT("attract"), bUp && bDown ? EResult::Pass : EResult::Fail,
				Name + TEXT(" lights up as you reach it"),
				FString::Printf(TEXT("here %s; %s (%.0f m away) attention %.2f"),
					*Near->Attract->Describe(), *Far->ItemId.ToString(), Best / 100.f, ThereA));
			return 0.1f;
		} });
	}
}

// --- wax -------------------------------------------------------------------------------------

void UWTAPlayTest::AddWaxPhase()
{
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	if (Content == nullptr)
	{
		return;
	}
	int32 Index = 0;
	for (const FName& SceneName : Content->GetRowNames(EWTATable::WaxScenes))
	{
		const FWTAWaxSceneRow* Row = Content->FindWaxScene(SceneName);
		if (Row == nullptr)
		{
			continue;
		}
		// The shot tour's spot: the aisle, 4.2 m in front of the stage, looking at the reenactors.
		FWTAView View;
		View.Location = Row->StageLocation + FRotator(0.f, Row->StageYaw, 0.f).Vector() * 420.f;
		View.Location.Z = 162.f;
		View.Yaw = Row->StageYaw + 180.f;
		View.Pitch = -8.f;
		View.bValid = true;
		const FName Story = Row->ItemId.IsNone() ? SceneName : Row->ItemId;
		const FString Name = SceneName.ToString();
		const int32 I = Index++;
		Steps.Add({ TEXT("wax ") + Name, [this, View]() -> float
		{
			CloseAll();
			StandAt(View);
			return 0.8f;
		} });
		Steps.Add({ TEXT("wax plaque ") + Name, [this, Name, Story]() -> float
		{
			const AWTAPlayerController* Controller = PC();
			const FName Active = Controller != nullptr ? Controller->GetActiveStageStory() : NAME_None;
			const bool bHover = Controller != nullptr && Controller->Interaction != nullptr && Controller->Interaction->HasHover();
			Report(TEXT("wax"), Active == Story ? EResult::Pass : EResult::Fail, Name + TEXT(" plaque when you walk up"),
				FString::Printf(TEXT("active scene story %s%s"), *Active.ToString(), bHover ? TEXT(", something under the crosshair") : TEXT("")));
			// What a visitor sees from the aisle, 0.8 s after arriving (the figures' LODs have just changed).
			Shot(TEXT("wax_stage_") + Name);
			return 0.1f;
		} });
		AddTap(TEXT("wax E ") + Name, EKeys::E, 0.7f);
		Steps.Add({ TEXT("wax open ") + Name, [this, Name, Story, I]() -> float
		{
			const AWTAPlayerController* Controller = PC();
			const bool bOpen = Controller != nullptr && Controller->Panel != nullptr && Controller->Panel->IsOpen()
				&& Controller->Panel->GetMode() == EWTAPanelMode::Exhibit && Controller->Panel->GetCurrentId() == Story;
			Report(TEXT("wax"), bOpen ? EResult::Pass : EResult::Fail, Name + TEXT(" E opens the scene's story"),
				bOpen ? TEXT("story card open") : TEXT("not open"));
			if (I < 2 || !bOpen)
			{
				Shot(TEXT("wax_story_") + Name);
			}
			return 0.2f;
		} });
		// The museum reads the card aloud: the clip exists, starts and is still playing a moment later.
		Steps.Add({ TEXT("wax listen ") + Name, [this, Name, Story]() -> float
		{
			UWTAVoiceSubsystem* Voice = UWTAVoiceSubsystem::Get(this);
			static const FName Exhibit(TEXT("exhibit"));
			if (Voice == nullptr || !Voice->HasClip(Exhibit, Story))
			{
				Report(TEXT("wax"), EResult::Fail, Name + TEXT(" has a narration clip"),
					FString::Printf(TEXT("no %s"), *UWTAVoiceSubsystem::ClipPath(Exhibit, Story)));
				return 0.f;
			}
			Voice->Read(Exhibit, Story);
			return 0.4f;
		} });
		Steps.Add({ TEXT("wax reading ") + Name, [this, Name, Story]() -> float
		{
			const UWTAVoiceSubsystem* Voice = UWTAVoiceSubsystem::Get(this);
			static const FName Exhibit(TEXT("exhibit"));
			const bool bReading = Voice != nullptr && Voice->IsReadingCard(Exhibit, Story);
			Report(TEXT("wax"), bReading ? EResult::Pass : EResult::Fail, Name + TEXT(" reads its card aloud"),
				bReading ? TEXT("reading") : TEXT("not reading"));
			return 0.1f;
		} });
		AddTap(TEXT("wax esc ") + Name, EKeys::Escape, 0.4f);
		// The props in hands: each meets the palm of the hand its key names (within 25 cm of the wrist) and that
		// hand is closed on it; a close-up of the first held one, from a free camera on a side of the hand that
		// nothing blocks, shows the grip. The camera is aimed again in the frame the shot is taken, since the
		// hand moves while the stream settles.
		TSharedRef<bool> HeldOne = MakeShared<bool>(false);
		TSharedRef<int32> HeldIndex = MakeShared<int32>(INDEX_NONE);
		auto FindStage = [this, SceneName]() -> AWTAWaxStageActor*
		{
			for (TActorIterator<AWTAWaxStageActor> It(GetWorld()); It; ++It)
			{
				if (It->SceneId == SceneName)
				{
					return *It;
				}
			}
			return nullptr;
		};
		auto AimAtHand = [this](AWTAWaxStageActor* Stage, int32 Index)
		{
			FVector Prop, Wrist, Figure;
			float Grip = 0.f;
			FName Socket;
			FTransform Palm;
			UWorld* World = GetWorld();
			if (World == nullptr || Stage == nullptr || !Stage->PropInHand(Index, Prop, Wrist, Figure, Grip, Socket, Palm))
			{
				return;
			}
			if (FaceCamera == nullptr)
			{
				FActorSpawnParameters Params;
				Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
				FaceCamera = World->SpawnActor<ACameraActor>(FVector::ZeroVector, FRotator::ZeroRotator, Params);
				if (FaceCamera != nullptr && FaceCamera->GetCameraComponent() != nullptr)
				{
					FaceCamera->GetCameraComponent()->SetFieldOfView(45.f);
					FaceCamera->GetCameraComponent()->SetConstraintAspectRatio(false);
				}
			}
			if (FaceCamera == nullptr)
			{
				return;
			}
			const FVector F = Palm.GetUnitAxis(EAxis::X), N = Palm.GetUnitAxis(EAxis::Y), Z = Palm.GetUnitAxis(EAxis::Z);
			const FVector Look = Palm.GetLocation() + F * 3.f + N * 4.f;
			const FVector Away = (Palm.GetLocation() - (Figure + FVector(0.f, 0.f, 130.f))).GetSafeNormal2D();
			const FVector Side = FVector::CrossProduct(Away, FVector::UpVector).GetSafeNormal();
			// Candidate views, each a direction from the prop, a distance and how much it is preferred when clear:
			// over either shoulder, the way the person sees what they hold (the screen, the thumb, the fingers);
			// high three-quarter views from either edge of the hand; then the older set - the open side of the
			// palm, the edges and the end - for a hand the stance does not place.
			struct FView { FVector Dir; float Dist; float Base; };
			TArray<FView> Views;
			for (float S : { 1.f, -1.f })
			{
				const FVector Over = -Away * 55.f + FVector::UpVector * 50.f + Side * (32.f * S);
				Views.Add({ Over.GetSafeNormal(), static_cast<float>(Over.Size()), 1.0f });
			}
			for (float S : { 1.f, -1.f })
			{
				Views.Add({ (Z * S + FVector::UpVector * 0.9f + N * 0.3f + Away * 0.4f).GetSafeNormal(), 70.f, 0.7f });
			}
			for (const FVector& Dir : { (N - Z + F * 0.4f).GetSafeNormal(), (N + Z + F * 0.4f).GetSafeNormal(), (N + F).GetSafeNormal(), N,
				(N - Z).GetSafeNormal(), (N + Z).GetSafeNormal(), F, (F + Z).GetSafeNormal(), (F - Z).GetSafeNormal(), Z, -Z, (N - F).GetSafeNormal(), -N })
			{
				Views.Add({ Dir, 70.f, 0.f });
			}
			FCollisionQueryParams Params(FName(TEXT("WTAHandCamera")), true);
			Params.AddIgnoredActor(Stage);
			FVector Eye = Look + N * 70.f;
			float Best = -10.f;
			int32 Order = 0;
			for (const FView& View : Views)
			{
				const FVector Try = Look + View.Dir * View.Dist;
				FHitResult Hit;
				const bool bBlocked = World->LineTraceSingleByChannel(Hit, Look + View.Dir * 6.f, Try, ECC_Visibility, Params);
				// a clear view, preferred ones first, away from the figure's chest, of the palm's open side, not
				// from under the hand, earlier in the list on a tie
				const float Score = (bBlocked ? -4.f : 0.f) + View.Base + 0.5f * static_cast<float>(FVector::DotProduct(View.Dir, Away)) + 0.3f * static_cast<float>(FVector::DotProduct(View.Dir, N))
					- 0.8f * FMath::Max(0.f, -static_cast<float>(View.Dir.Z)) - 0.02f * Order;
				++Order;
				if (Score > Best)
				{
					Best = Score;
					Eye = bBlocked ? Look + View.Dir * FMath::Max(25.f, Hit.Distance * 0.8f) : Try;
				}
			}
			FaceCamera->SetActorLocationAndRotation(Eye, (Look - Eye).Rotation());
		};
		TSharedRef<int32> Polls = MakeShared<int32>(0);
		Steps.Add({ TEXT("wax hands ") + Name, [this, Name, HeldOne, HeldIndex, Polls, FindStage, AimAtHand]() -> float
		{
			*HeldOne = false;
			*HeldIndex = INDEX_NONE;
			AWTAWaxStageActor* Stage = FindStage();
			if (Stage == nullptr)
			{
				return 0.f;
			}
			// wait for a moment when a prop sits in a hand and will stay there through the close-up (one loop at most)
			bool bSettled = false;
			for (int32 i = 0; i < Stage->NumProps() && !bSettled; ++i)
			{
				FVector Prop, Wrist, Figure;
				float Grip = 0.f;
				FName Socket;
				FTransform PalmOf;
				bSettled = Stage->PropInHand(i, Prop, Wrist, Figure, Grip, Socket, PalmOf) && Stage->PropSecondsBeforeLeaving(i) > 1.2f && Grip > 0.95f;
			}
			if (!bSettled && (*Polls)++ < 70)
			{
				return -0.25f;
			}
			int32 Held = 0, Placed = 0, Closed = 0;
			FString Notes;
			for (int32 i = 0; i < Stage->NumProps(); ++i)
			{
				FVector Prop, Wrist, Figure;
				float Grip = 0.f;
				FName Socket;
				FTransform PalmOf;
				if (!Stage->PropInHand(i, Prop, Wrist, Figure, Grip, Socket, PalmOf))
				{
					continue;
				}
				const float Gap = static_cast<float>(FVector::Dist(Prop, Wrist));
				// a prop with a stance: the arm must have brought the hand to it (within 3 cm and 10 degrees)
				float ArmCm = 0.f, ArmDeg = 0.f, ArmWeight = 0.f;
				const bool bStance = Stage->ArmOnTarget(i, ArmCm, ArmDeg, ArmWeight);
				const bool bReached = !bStance || (ArmWeight > 0.95f && ArmCm < 3.f && ArmDeg < 10.f);
				const bool bPlaced = Gap < 25.f && bReached, bClosed = Grip > 0.2f;
				Held += 1; Placed += bPlaced ? 1 : 0; Closed += bClosed ? 1 : 0;
				if (Held == 1) { *HeldIndex = i; }
				Notes += FString::Printf(TEXT("%s prop %d %.0f cm from the wrist, grip %.2f"), *Socket.ToString(), i, Gap, Grip);
				if (bStance)
				{
					Notes += FString::Printf(TEXT(", arm %.2f at %.1f cm / %.0f deg from its stance"), ArmWeight, ArmCm, ArmDeg);
				}
				Notes += TEXT("; ");
				Report(TEXT("wax"), EResult::Info, Name + TEXT(" hold"), Stage->DescribeHold(i));
			}
			if (Held == 0)
			{
				return 0.f;                              // nothing in a hand at this moment of the loop
			}
			*HeldOne = true;
			Report(TEXT("wax"), Placed == Held && Closed == Held ? EResult::Pass : EResult::Fail, Name + TEXT(" holds its props"), Notes);
			AimAtHand(Stage, *HeldIndex);
			if (AWTAPlayerController* C = PC())
			{
				if (FaceCamera != nullptr)
				{
					C->SetViewTargetWithBlend(FaceCamera, 0.f);
				}
			}
			return 0.5f;
		} });
		Steps.Add({ TEXT("wax hands take ") + Name, [this, Name, HeldOne, HeldIndex, FindStage, AimAtHand]() -> float
		{
			if (*HeldOne)
			{
				AimAtHand(FindStage(), *HeldIndex);
				Shot(TEXT("wax_hand_") + Name, false);
			}
			return 0.1f;
		} });
		Steps.Add({ TEXT("wax hands back ") + Name, [this, HeldOne]() -> float
		{
			AWTAPlayerController* C = PC();
			if (*HeldOne && C != nullptr && C->GetPawn() != nullptr)
			{
				C->SetViewTargetWithBlend(C->GetPawn(), 0.f);
			}
			return 0.1f;
		} });
	}
}

// --- seats -----------------------------------------------------------------------------------

void UWTAPlayTest::AddSeatsPhase()
{
	// Every seat: stand in front of it, the crosshair must say Sit, E must sit the player down with the eye at
	// the seated height over the sit point and the view ahead clear, then Space must stand them back up on the
	// floor where they stood. A shot of the view from the first seat in each room.
	TArray<AWTASeatActor*> Seats;
	for (TActorIterator<AWTASeatActor> It(GetWorld()); It; ++It)
	{
		if (*It != nullptr && !(*It)->IsHidden())
		{
			Seats.Add(*It);
		}
	}
	Seats.Sort([](const AWTASeatActor& A, const AWTASeatActor& B) { return A.SeatId.LexicalLess(B.SeatId); });
	// A few per room: the auditorium and the theatre hold a hundred seats each, built from one chair.
	constexpr int32 MaxPerRoom = 6;
	{
		TMap<FString, int32> PerRoom;
		TArray<AWTASeatActor*> Kept;
		for (AWTASeatActor* Seat : Seats)
		{
			FString Room, Rest;
			if (!Seat->SeatId.ToString().Split(TEXT("_"), &Room, &Rest))
			{
				Room = Seat->SeatId.ToString();
			}
			int32& Count = PerRoom.FindOrAdd(Room);
			if (Count < MaxPerRoom)
			{
				Kept.Add(Seat);
				++Count;
			}
		}
		Seats = Kept;
	}
	Steps.Add({ TEXT("seats start"), [this, Count = Seats.Num()]() -> float
	{
		Report(TEXT("seats"), Count > 0 ? EResult::Info : EResult::Fail, TEXT("seats"), FString::Printf(TEXT("%d to sit on (up to %d a room)"), Count, MaxPerRoom));
		return 0.f;
	} });
	TSet<FString> RoomsShot;
	int32 Index = 0;
	for (AWTASeatActor* Seat : Seats)
	{
		const TWeakObjectPtr<AWTASeatActor> Weak(Seat);
		const FString Name = FString::Printf(TEXT("seat %s"), *Seat->SeatId.ToString());
		// the room is the seat id's first word (lib_chair_03 -> lib)
		FString Room, Rest;
		if (!Seat->SeatId.ToString().Split(TEXT("_"), &Room, &Rest))
		{
			Room = Seat->SeatId.ToString();
		}
		const bool bShot = !RoomsShot.Contains(Room);
		RoomsShot.Add(Room);
		const FString ShotName = FString::Printf(TEXT("seat_%02d_%s"), Index++, *Room);
		const TSharedRef<bool> Ok = MakeShared<bool>(false);
		const TSharedRef<FVector> StoodAt = MakeShared<FVector>(FVector::ZeroVector);

		Steps.Add({ Name + TEXT(" stand"), [this, Weak, Name, Ok, StoodAt]() -> float
		{
			*Ok = false;
			AWTASeatActor* Target = Weak.Get();
			AWTACharacter* Me = Player();
			if (Target == nullptr || Me == nullptr)
			{
				Report(TEXT("seats"), EResult::Skip, Name, TEXT("gone"));
				return 0.f;
			}
			CloseAll();
			if (Me->IsSeated())
			{
				Me->StandUp(false);
			}
			FWTAView View;
			if (!IWTAInteractable::Execute_GetViewSpot(Target, View) || !View.bValid)
			{
				Report(TEXT("seats"), EResult::Fail, Name, TEXT("no view spot"));
				return 0.f;
			}
			StandAt(View);
			*StoodAt = Me->GetActorLocation();
			*Ok = true;
			return 0.5f;
		} });
		Steps.Add({ Name + TEXT(" hover"), [this, Weak, Name, Ok]() -> float
		{
			AWTASeatActor* Target = Weak.Get();
			AWTAPlayerController* Controller = PC();
			if (!*Ok || Target == nullptr || Controller == nullptr || Controller->Interaction == nullptr)
			{
				return 0.f;
			}
			if (Controller->Interaction->GetHovered() != Target)
			{
				FWTAView Aim;
				if (FindAimView(Target, Aim))
				{
					StandAt(Aim);
					return 0.45f;
				}
			}
			return 0.f;
		} });
		Steps.Add({ Name + TEXT(" E"), [this, Weak, Name, Ok, StoodAt]() -> float
		{
			AWTASeatActor* Target = Weak.Get();
			AWTAPlayerController* Controller = PC();
			if (!*Ok || Target == nullptr || Controller == nullptr || Controller->Interaction == nullptr)
			{
				return 0.f;
			}
			const AActor* Hovered = Controller->Interaction->GetHovered();
			const FString Label = Hovered != nullptr && Hovered->Implements<UWTAInteractable>() ? IWTAInteractable::Execute_GetInteractLabel(Hovered).ToString() : FString();
			if (Hovered != Target || Label != TEXT("Sit"))
			{
				*Ok = false;
				Report(TEXT("seats"), EResult::Fail, Name + TEXT(" says Sit"), FString::Printf(TEXT("the crosshair has \"%s\" on %s; %s"), *Label, Hovered != nullptr ? *Hovered->GetName() : TEXT("nothing"), *DescribeAim(Target)));
				return 0.f;
			}
			if (AWTACharacter* Me = Player())
			{
				*StoodAt = Me->GetActorLocation();       // the hover step may have moved the player: this is where they sit down from
			}
			KeyDown(EKeys::E);
			return 0.12f;
		} });
		Steps.Add({ Name + TEXT(" E up"), [this, Ok]() -> float
		{
			if (*Ok)
			{
				KeyUp(EKeys::E);
			}
			return 0.6f;
		} });
		Steps.Add({ Name + TEXT(" seated"), [this, Weak, Name, Ok, bShot, ShotName]() -> float
		{
			AWTASeatActor* Target = Weak.Get();
			AWTACharacter* Me = Player();
			if (!*Ok || Target == nullptr || Me == nullptr)
			{
				return 0.f;
			}
			const FVector Eye = Me->GetEyeLocation();
			const FVector Sit = Target->GetSitPoint();
			const float Over = static_cast<float>(Eye.Z - Sit.Z);
			const float Off = static_cast<float>(FVector::Dist2D(Eye, Sit));
			// the view ahead: nothing solid within a metre of the eyes in the direction the seat faces (the camera
			// channel, which the pick boxes of exhibits and seats do not block)
			const FVector Forward = FRotator(0.f, Target->SeatYaw, 0.f).Vector();
			FHitResult Hit;
			FCollisionQueryParams Params(FName(TEXT("WTASeatView")), false, Me);
			Params.AddIgnoredActor(Target);
			const bool bBlocked = GetWorld()->LineTraceSingleByChannel(Hit, Eye, Eye + Forward * 100.f, ECC_Camera, Params);
			const bool bSeated = Me->IsSeated() && Me->GetSeat() == Target;
			const bool bHeight = FMath::Abs(Over - Me->SeatEyeHeight) < 6.f;
			const bool bOnIt = Off < 12.f;
			*Ok = bSeated && bHeight && bOnIt && !bBlocked;
			Report(TEXT("seats"), *Ok ? EResult::Pass : EResult::Fail, Name + TEXT(" sits you down"),
				FString::Printf(TEXT("%s, eye %.0f cm over the seat (wanted %.0f), %.0f cm off its middle, the view ahead %s"),
					bSeated ? TEXT("seated") : TEXT("not seated"), Over, Me->SeatEyeHeight, Off,
					bBlocked ? *FString::Printf(TEXT("blocked at %.0f cm by %s"), Hit.Distance, Hit.GetActor() != nullptr ? *Hit.GetActor()->GetName() : TEXT("something")) : TEXT("clear")));
			if (*Ok && bShot)
			{
				Shot(ShotName, false);
				return 0.3f;
			}
			return 0.f;
		} });
		Steps.Add({ Name + TEXT(" look"), [this, Weak, Ok]() -> float
		{
			// look around from the seat: a turn to the side still works while seated
			AWTASeatActor* Target = Weak.Get();
			AWTAPlayerController* Controller = PC();
			if (!*Ok || Target == nullptr || Controller == nullptr)
			{
				return 0.f;
			}
			Controller->SetControlRotation(FRotator(-10.f, Target->SeatYaw + 50.f, 0.f));
			return 0.25f;
		} });
		Steps.Add({ Name + TEXT(" space"), [this, Ok]() -> float
		{
			if (*Ok)
			{
				KeyDown(EKeys::SpaceBar);
			}
			return 0.12f;
		} });
		Steps.Add({ Name + TEXT(" space up"), [this, Ok]() -> float
		{
			if (*Ok)
			{
				KeyUp(EKeys::SpaceBar);
			}
			return 0.6f;
		} });
		Steps.Add({ Name + TEXT(" stood"), [this, Weak, Name, Ok, StoodAt]() -> float
		{
			AWTASeatActor* Target = Weak.Get();
			AWTACharacter* Me = Player();
			if (!*Ok || Target == nullptr || Me == nullptr)
			{
				return 0.f;
			}
			const FVector P = Me->GetActorLocation();
			const float Away = static_cast<float>(FVector::Dist2D(P, *StoodAt));
			const float Rise = static_cast<float>(P.Z - StoodAt->Z);
			const bool bStanding = !Me->IsSeated() && Me->GetCharacterMovement() != nullptr && Me->GetCharacterMovement()->MovementMode == MOVE_Walking;
			const bool bBack = Away < 15.f && FMath::Abs(Rise) < 15.f;
			Report(TEXT("seats"), bStanding && bBack ? EResult::Pass : EResult::Fail, Name + TEXT(" Space stands you up"),
				FString::Printf(TEXT("%s, %.0f cm from where you sat down from, %.0f cm %s"), bStanding ? TEXT("standing") : TEXT("not standing"), Away, FMath::Abs(Rise), Rise >= 0.f ? TEXT("higher") : TEXT("lower")));
			return 0.f;
		} });
	}
}

// --- ui --------------------------------------------------------------------------------------

void UWTAPlayTest::AddUIPhase()
{
	const TSharedRef<FVector> Before = MakeShared<FVector>(FVector::ZeroVector);
	const TSharedRef<int32> Polls = MakeShared<int32>(0);
	auto StandAtSpawn = [this]()
	{
		CloseAll();
		const UWTASettings* Settings = UWTASettings::Get();
		if (Settings != nullptr && Settings->SpawnView.bValid)
		{
			StandAt(Settings->SpawnView);
		}
	};

	// Tour: T starts it and walks to stop 1, T walks to stop 2, Esc ends it.
	Steps.Add({ TEXT("ui tour stand"), [StandAtSpawn]() -> float
	{
		StandAtSpawn();
		return 0.5f;
	} });
	Steps.Add({ TEXT("ui tour before"), [this, Before]() -> float
	{
		if (const AWTACharacter* Character = Player())
		{
			*Before = Character->GetActorLocation();
		}
		return 0.f;
	} });
	for (int32 Stop = 0; Stop < 2; ++Stop)
	{
		AddTap(FString::Printf(TEXT("ui T %d"), Stop + 1), EKeys::T, 0.4f);
		Steps.Add({ FString::Printf(TEXT("ui tour stop %d"), Stop + 1), [this, Before, Polls, Stop]() -> float
		{
			UWTATourSubsystem* Tour = UWTATourSubsystem::Get(this);
			const AWTACharacter* Character = Player();
			if (Tour == nullptr || !Tour->IsTouring())
			{
				Report(TEXT("ui"), EResult::Fail, Stop == 0 ? TEXT("T starts the tour") : TEXT("T goes to the next stop"), TEXT("no tour running"));
				*Polls = 0;
				return 0.f;
			}
			// Let the walk finish (up to 15 s).
			if (Character != nullptr && Character->IsAutoWalking() && ++*Polls < 60)
			{
				return -0.25f;
			}
			*Polls = 0;
			const double Walked = Character != nullptr ? FVector::Dist2D(*Before, Character->GetActorLocation()) : 0.0;
			FWTATourStopRow Row;
			Tour->GetCurrentStop(Row);
			const bool bPass = Tour->GetIndex() == Stop && (Stop == 0 || Walked > 100.0);
			Report(TEXT("ui"), bPass ? EResult::Pass : EResult::Fail,
				Stop == 0 ? TEXT("T starts the tour and walks to the first stop") : TEXT("T walks on to the next stop"),
				FString::Printf(TEXT("stop %d of %d \"%s\", walked %.0f cm"), Tour->GetIndex() + 1, Tour->GetNumStops(), *Row.Title.ToString(), Walked));
			if (Character != nullptr)
			{
				*Before = Character->GetActorLocation();
			}
			return 1.0f;
		} });
		Steps.Add({ FString::Printf(TEXT("ui tour shot %d"), Stop + 1), [this, Stop]() -> float
		{
			Shot(FString::Printf(TEXT("tour_stop%d"), Stop + 1));
			return 0.3f;
		} });
	}
	AddTap(TEXT("ui tour esc"), EKeys::Escape, 0.4f);
	Steps.Add({ TEXT("ui tour end"), [this]() -> float
	{
		const UWTATourSubsystem* Tour = UWTATourSubsystem::Get(this);
		const bool bTouring = Tour != nullptr && Tour->IsTouring();
		Report(TEXT("ui"), bTouring ? EResult::Fail : EResult::Pass, TEXT("Esc ends the tour"), bTouring ? TEXT("still touring") : TEXT("ended"));
		CloseAll();
		return 0.3f;
	} });

	// Enter: the chat with the room's staff (Margaret in the lobby); Esc closes it.
	Steps.Add({ TEXT("ui chat stand"), [this, StandAtSpawn]() -> float
	{
		StandAtSpawn();
		return 0.6f;
	} });
	AddTap(TEXT("ui enter"), EKeys::Enter, 0.8f);
	Steps.Add({ TEXT("ui chat"), [this]() -> float
	{
		const AWTAPlayerController* Controller = PC();
		const bool bOpen = Controller != nullptr && Controller->Chat != nullptr && Controller->Chat->IsOpen();
		Report(TEXT("ui"), bOpen ? EResult::Pass : EResult::Fail, TEXT("Enter opens the chat with the room's staff"),
			bOpen ? FString::Printf(TEXT("chat with %s"), *Controller->Chat->GetStaffId().ToString()) : FString(TEXT("not open")));
		Shot(TEXT("chat_enter"));
		return 0.2f;
	} });
	AddTap(TEXT("ui chat esc"), EKeys::Escape, 0.45f);
	Steps.Add({ TEXT("ui chat closed"), [this]() -> float
	{
		const AWTAPlayerController* Controller = PC();
		const bool bOpen = Controller != nullptr && Controller->IsAnyPanelOpen();
		Report(TEXT("ui"), bOpen ? EResult::Fail : EResult::Pass, TEXT("Esc closes the chat"), bOpen ? TEXT("still open") : TEXT("closed"));
		CloseAll();
		return 0.2f;
	} });

	// Badges.
	Steps.Add({ TEXT("ui badges"), [this]() -> float
	{
		CloseAll();
		if (AWTAPlayerController* Controller = PC())
		{
			Controller->OpenBadges();
		}
		return 0.6f;
	} });
	Steps.Add({ TEXT("ui badges check"), [this]() -> float
	{
		const AWTAPlayerController* Controller = PC();
		const bool bOpen = Controller != nullptr && Controller->Panel != nullptr && Controller->Panel->IsOpen() && Controller->Panel->GetMode() == EWTAPanelMode::Badges;
		Report(TEXT("ui"), bOpen ? EResult::Pass : EResult::Fail, TEXT("badges panel"), bOpen ? TEXT("open") : TEXT("not open"));
		Shot(TEXT("badges"));
		return 0.2f;
	} });
	AddTap(TEXT("ui badges esc"), EKeys::Escape, 0.4f);
	Steps.Add({ TEXT("ui badges closed"), [this]() -> float
	{
		const AWTAPlayerController* Controller = PC();
		const bool bOpen = Controller != nullptr && Controller->IsAnyPanelOpen();
		Report(TEXT("ui"), bOpen ? EResult::Fail : EResult::Pass, TEXT("Esc closes the badges panel"), bOpen ? TEXT("still open") : TEXT("closed"));
		CloseAll();
		return 0.2f;
	} });
}

// --- graphics --------------------------------------------------------------------------------

void UWTAPlayTest::AddGraphicsPhase()
{
	Steps.Add({ TEXT("graphics save"), [this]() -> float
	{
		UGameUserSettings* Settings = GEngine != nullptr ? GEngine->GetGameUserSettings() : nullptr;
		if (Settings != nullptr)
		{
			SavedQuality[0] = Settings->GetViewDistanceQuality();
			SavedQuality[1] = Settings->GetAntiAliasingQuality();
			SavedQuality[2] = Settings->GetShadowQuality();
			SavedQuality[3] = Settings->GetGlobalIlluminationQuality();
			SavedQuality[4] = Settings->GetReflectionQuality();
			SavedQuality[5] = Settings->GetPostProcessingQuality();
			SavedQuality[6] = Settings->GetTextureQuality();
			SavedQuality[7] = Settings->GetVisualEffectQuality();
			SavedQuality[8] = Settings->GetFoliageQuality();
			SavedQuality[9] = Settings->GetShadingQuality();
			SavedQuality[10] = Settings->GetLandscapeQuality();
		}
		const IConsoleVariable* Resolution = IConsoleManager::Get().FindConsoleVariable(TEXT("sg.ResolutionQuality"));
		SavedResolutionScale = Resolution != nullptr ? Resolution->GetFloat() : 100.f;
		Report(TEXT("graphics"), EResult::Info, TEXT("levels at start"), FString::Printf(TEXT("overall %d (%s), shadows %d, resolution %.0f%%"),
			UWTAGraphicsLibrary::GetQualityPreset(), *UWTAGraphicsLibrary::GetQualityPresetLabel(UWTAGraphicsLibrary::GetQualityPreset()).ToString(),
			SavedQuality[2], SavedResolutionScale));
		CloseAll();
		StandAt(PlaceView(this, TEXT("library")));
		return 2.f;
	} });
	for (const int32 Level : { 1, 3 })
	{
		Steps.Add({ TEXT("graphics apply"), [Level]() -> float
		{
			// What the menu's preset buttons run.
			UWTAGraphicsLibrary::ApplyQualityPreset(Level);
			return 3.f;
		} });
		Steps.Add({ TEXT("graphics check"), [this, Level]() -> float
		{
			const int32 Now = UWTAGraphicsLibrary::GetQualityPreset();
			const IConsoleVariable* Shadows = IConsoleManager::Get().FindConsoleVariable(TEXT("sg.ShadowQuality"));
			const int32 ShadowLevel = Shadows != nullptr ? Shadows->GetInt() : -1;
			const FString Label = UWTAGraphicsLibrary::GetQualityPresetLabel(Level).ToString();
			Report(TEXT("graphics"), (Now == Level && ShadowLevel == Level) ? EResult::Pass : EResult::Fail, Label + TEXT(" preset applies"),
				FString::Printf(TEXT("overall %d, sg.ShadowQuality %d"), Now, ShadowLevel));
			Shot(TEXT("graphics_") + Label.ToLower());
			return 0.3f;
		} });
	}
	Steps.Add({ TEXT("graphics restore"), [this]() -> float
	{
		UGameUserSettings* Settings = GEngine != nullptr ? GEngine->GetGameUserSettings() : nullptr;
		if (Settings != nullptr)
		{
			Settings->SetViewDistanceQuality(SavedQuality[0]);
			Settings->SetAntiAliasingQuality(SavedQuality[1]);
			Settings->SetShadowQuality(SavedQuality[2]);
			Settings->SetGlobalIlluminationQuality(SavedQuality[3]);
			Settings->SetReflectionQuality(SavedQuality[4]);
			Settings->SetPostProcessingQuality(SavedQuality[5]);
			Settings->SetTextureQuality(SavedQuality[6]);
			Settings->SetVisualEffectQuality(SavedQuality[7]);
			Settings->SetFoliageQuality(SavedQuality[8]);
			Settings->SetShadingQuality(SavedQuality[9]);
			Settings->SetLandscapeQuality(SavedQuality[10]);
			Settings->SetResolutionScaleValueEx(SavedResolutionScale);
			Settings->ApplySettings(false);
			Settings->SaveSettings();
		}
		Report(TEXT("graphics"), EResult::Info, TEXT("levels restored"), FString::Printf(TEXT("overall %d, shadows %d"),
			UWTAGraphicsLibrary::GetQualityPreset(), Settings != nullptr ? Settings->GetShadowQuality() : -1));
		return 1.f;
	} });
}

// --- fps -------------------------------------------------------------------------------------

void UWTAPlayTest::AddFpsPhase()
{
	for (const TCHAR* Place : { TEXT("lobby"), TEXT("library"), TEXT("school"), TEXT("wax"), TEXT("yard") })
	{
		const FString Name(Place);
		Steps.Add({ TEXT("fps ") + Name, [this, Name]() -> float
		{
			CloseAll();
			StandAt(PlaceView(this, *Name));
			return 2.5f;
		} });
		Steps.Add({ TEXT("fps measure ") + Name, [this]() -> float
		{
			bMeasuring = true;
			MeasureSeconds = 0.f;
			MeasureFrames = 0;
			WorstFrame = 0.f;
			return 3.f;
		} });
		Steps.Add({ TEXT("fps report ") + Name, [this, Name]() -> float
		{
			bMeasuring = false;
			const float Average = MeasureSeconds > 0.f ? MeasureFrames / MeasureSeconds : 0.f;
			Report(TEXT("fps"), Average >= 30.f ? EResult::Pass : EResult::Fail, Name,
				FString::Printf(TEXT("%.0f fps average, worst frame %.1f ms, %d frames"), Average, WorstFrame * 1000.f, MeasureFrames));
			return 0.f;
		} });
	}
}

// --- adapt -----------------------------------------------------------------------------------

void UWTAPlayTest::AddAdaptPhase()
{
	// Walking (or travelling) in from the sunny yard: the camera's auto exposure has to come down from an outdoor
	// level to an indoor one. Shots (no HUD) 0.5, 2, 5 and 8 s after arriving show how long a room looks dark.
	for (const TCHAR* Place : { TEXT("studio"), TEXT("lab"), TEXT("wax"), TEXT("library") })
	{
		const FString Name(Place);
		Steps.Add({ TEXT("adapt yard ") + Name, [this]() -> float
		{
			CloseAll();
			StandAt(PlaceView(this, TEXT("yard")));
			return 5.f;
		} });
		Steps.Add({ TEXT("adapt go ") + Name, [this, Name]() -> float
		{
			StandAt(PlaceView(this, *Name));
			return 0.5f;
		} });
		float Elapsed = 0.5f;
		for (const float At : { 0.5f, 2.f, 5.f, 8.f })
		{
			const float Wait = At - Elapsed;
			Elapsed = At;
			Steps.Add({ FString::Printf(TEXT("adapt shot %s %.1f"), *Name, At), [this, Name, At, Wait]() -> float
			{
				// The wait before this shot: zero for the first one.
				if (Wait > 0.f && !bAdaptWaited)
				{
					bAdaptWaited = true;
					return -Wait;
				}
				bAdaptWaited = false;
				Shot(FString::Printf(TEXT("adapt_%s_%04.1fs"), *Name, At), false);
				return 0.05f;
			} });
		}
	}
	// On foot: from the yard through the school's back door (3400, -300) into its hall, the way a visitor comes in.
	Steps.Add({ TEXT("adapt walk start"), [this]() -> float
	{
		CloseAll();
		FWTAView View;
		View.Location = FVector(3800.f, -300.f, 162.f);
		View.Yaw = 180.f;
		View.Pitch = -3.f;
		View.bValid = true;
		StandAt(View);
		return 5.f;
	} });
	Steps.Add({ TEXT("adapt walk go"), [this]() -> float { KeyDown(EKeys::W); return 2.5f; } });
	Steps.Add({ TEXT("adapt walk stop"), [this]() -> float
	{
		KeyUp(EKeys::W);
		const AWTACharacter* Character = Player();
		Report(TEXT("adapt"), EResult::Info, TEXT("walked in from the yard"), Character != nullptr ? Character->GetActorLocation().ToCompactString() : TEXT("no player"));
		Shot(TEXT("adapt_walkin_00.0s"), false);
		return 1.5f;
	} });
	Steps.Add({ TEXT("adapt walk 1.5"), [this]() -> float { Shot(TEXT("adapt_walkin_01.5s"), false); return 2.f; } });
	Steps.Add({ TEXT("adapt walk 3.5"), [this]() -> float { Shot(TEXT("adapt_walkin_03.5s"), false); return 2.5f; } });
	Steps.Add({ TEXT("adapt walk 6"), [this]() -> float { Shot(TEXT("adapt_walkin_06.0s"), false); return 0.1f; } });
	Steps.Add({ TEXT("adapt done"), [this]() -> float
	{
		Report(TEXT("adapt"), EResult::Info, TEXT("eye adaptation shots"), TEXT("yard to studio, lab, wax hall and library at 0.5, 2, 5 and 8 s; walked in at 0 to 6 s"));
		return 0.f;
	} });
}

// --- people ----------------------------------------------------------------------------------

void UWTAPlayTest::FindPeople(TArray<TPair<FString, TWeakObjectPtr<AActor>>>& Out) const
{
	UWorld* World = GetWorld();
	if (World == nullptr)
	{
		return;
	}
	auto Keep = [this](const FString& Name)
	{
		if (PeopleFilter.Num() == 0)
		{
			return true;
		}
		for (const FString& Part : PeopleFilter)
		{
			if (Name.Contains(Part))
			{
				return true;
			}
		}
		return false;
	};
	for (TActorIterator<AWTAStaffNPC> It(World); It; ++It)
	{
		AActor* Child = It->MetaHumanChild != nullptr ? It->MetaHumanChild->GetChildActor() : nullptr;
		const FString Name = TEXT("staff_") + It->StaffId.ToString();
		if (Child != nullptr && Keep(Name))
		{
			Out.Emplace(Name, Child);
		}
	}
	for (TActorIterator<AWTAWaxStageActor> It(World); It; ++It)
	{
		for (int32 i = 0; i < It->Figures.Num(); ++i)
		{
			AActor* Figure = It->Figures[i];
			if (!IsValid(Figure))
			{
				continue;
			}
			// BP_<person>_C -> <person>
			FString Person = Figure->GetClass()->GetName();
			Person.RemoveFromStart(TEXT("BP_"));
			Person.RemoveFromEnd(TEXT("_C"));
			const FString Name = FString::Printf(TEXT("%s_%d_%s"), *It->SceneId.ToString(), i + 1, *Person);
			if (Keep(Name))
			{
				Out.Emplace(Name, Figure);
			}
		}
	}
}

void UWTAPlayTest::AddPeoplePhase()
{
	struct FSample
	{
		FString Name;
		TWeakObjectPtr<AActor> Person;
		FVector Hand = FVector::ZeroVector;
	};
	const TSharedRef<TArray<FSample>> Samples = MakeShared<TArray<FSample>>();
	Steps.Add({ TEXT("people sample"), [this, Samples]() -> float
	{
		TArray<TPair<FString, TWeakObjectPtr<AActor>>> People;
		FindPeople(People);
		Samples->Reset();
		int32 Staff = 0;
		for (const TPair<FString, TWeakObjectPtr<AActor>>& Person : People)
		{
			// Staff only animate while on screen: the faces phase checks them with the camera on them.
			if (Person.Key.StartsWith(TEXT("staff_")))
			{
				++Staff;
				continue;
			}
			FSample Sample;
			Sample.Name = Person.Key;
			Sample.Person = Person.Value;
			Sample.Hand = BoneInComponent(UWTAPeopleLibrary::FindBody(Person.Value.Get()), TEXT("hand_r"));
			Samples->Add(Sample);
		}
		Report(TEXT("people"), Samples->Num() + Staff > 0 ? EResult::Info : EResult::Fail, TEXT("people found"),
			FString::Printf(TEXT("%d wax figures (checked here), %d staff (checked on screen by the faces phase)"), Samples->Num(), Staff));
		return 1.5f;
	} });
	Steps.Add({ TEXT("people check"), [this, Samples]() -> float
	{
		for (const FSample& Sample : *Samples)
		{
			AActor* Person = Sample.Person.Get();
			USkeletalMeshComponent* Body = UWTAPeopleLibrary::FindBody(Person);
			if (Body == nullptr)
			{
				Report(TEXT("people"), EResult::Fail, Sample.Name, TEXT("no body mesh"));
				continue;
			}
			const FVector Hand = BoneInComponent(Body, TEXT("hand_r"));
			const FVector Thigh = BoneInComponent(Body, TEXT("thigh_r"));
			const double Moved = FVector::Dist(Hand, Sample.Hand);
			const double HandToThigh = FVector::Dist(Hand, Thigh);
			// The face must sit on the body's head; a face left in its reference pose under a posed head sags.
			float FaceGap = 0.f;
			const bool bFaceOn = UWTAPeopleLibrary::IsFaceOnBody(Person, FaceGap);
			// No bone the current LODs draw with may be left at the feet (it drags the jaw and lips, or the fingers,
			// down to the floor).
			FString Loose;
			const int32 Collapsed = UWTAPeopleLibrary::CountCollapsedBones(Body, &Loose)
				+ UWTAPeopleLibrary::CountCollapsedBones(UWTAPeopleLibrary::FindFace(Person), &Loose);
			// A wax figure: frozen, in a held pose - any pose but the bind pose (the reenactors freeze wherever
			// their scene stood when the visitor walked away, arms up included) - face on.
			const bool bFrozen = Body->bNoSkeletonUpdate;
			const double OffBind = FVector::Dist(Hand, BoneInRefPose(Body, TEXT("hand_r")));
			const bool bHeld = OffBind > 8.0;
			Report(TEXT("people"), (bFrozen && bHeld && bFaceOn && Collapsed == 0) ? EResult::Pass : EResult::Fail, Sample.Name + TEXT(" wax pose"),
				FString::Printf(TEXT("%s, right hand %.0f cm from the thigh, %.0f cm off the bind pose (%s), moved %.2f cm; face %.2f cm off the head; %d bones at the feet%s"),
					bFrozen ? TEXT("frozen") : TEXT("NOT frozen"), HandToThigh, OffBind, bHeld ? TEXT("held pose") : TEXT("BIND POSE"), Moved, FaceGap,
					Collapsed, Collapsed > 0 ? *(TEXT(" (") + Loose + TEXT(")")) : TEXT("")));
		}
		return 0.f;
	} });
}

// --- faces -----------------------------------------------------------------------------------

void UWTAPlayTest::AddFacesPhase()
{
	TArray<TPair<FString, TWeakObjectPtr<AActor>>> People;
	FindPeople(People);
	Steps.Add({ TEXT("faces camera"), [this, Count = People.Num()]() -> float
	{
		CloseAll();
		UWorld* World = GetWorld();
		if (World != nullptr && FaceCamera == nullptr)
		{
			FActorSpawnParameters Params;
			Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			FaceCamera = World->SpawnActor<ACameraActor>(FVector::ZeroVector, FRotator::ZeroRotator, Params);
			if (FaceCamera != nullptr && FaceCamera->GetCameraComponent() != nullptr)
			{
				FaceCamera->GetCameraComponent()->SetFieldOfView(40.f);
				FaceCamera->GetCameraComponent()->SetConstraintAspectRatio(false);
			}
		}
		Report(TEXT("faces"), FaceCamera != nullptr ? EResult::Info : EResult::Fail, TEXT("close-ups"), FString::Printf(TEXT("%d people"), Count));
		return 0.f;
	} });
	for (const TPair<FString, TWeakObjectPtr<AActor>>& Person : People)
	{
		const FString Name = Person.Key;
		const TWeakObjectPtr<AActor> Weak = Person.Value;
		const TSharedRef<FVector> Hand = MakeShared<FVector>(FVector::ZeroVector);
		const TSharedRef<bool> bPlaced = MakeShared<bool>(false);
		Steps.Add({ TEXT("face ") + Name, [this, Name, Weak, bPlaced]() -> float
		{
			*bPlaced = false;
			AActor* Who = Weak.Get();
			USkeletalMeshComponent* Face = FindFace(Who);
			AWTAPlayerController* Controller = PC();
			if (Who == nullptr || Face == nullptr || FaceCamera == nullptr || Controller == nullptr)
			{
				Report(TEXT("faces"), EResult::Skip, Name, TEXT("no face mesh"));
				return 0.f;
			}
			// The head joint sits about level with the tip of the nose: 3 cm above it is the middle of the face,
			// and the 40-degree lens takes in chin to forehead from 75 cm.
			const FVector Head = Face->GetBoneIndex(TEXT("head")) != INDEX_NONE ? Face->GetSocketLocation(TEXT("head")) : Face->Bounds.Origin;
			const FVector Centre = Head + FVector(0.f, 0.f, 3.f);
			// MetaHuman Blueprints face their own +Y (the people are spawned turned by -90 to face forward).
			const FVector Facing = Who->GetActorRightVector().GetSafeNormal2D();
			FVector CameraAt = Centre + Facing * 75.f + FVector(0.f, 0.f, 2.f);
			// A prop between the face and the lens (a stage set piece): come in front of it. The person, what they
			// wear or hold (a headset), a staff member's NPC actor around them (its capsule) and the player are not.
			FCollisionQueryParams Params(FName(TEXT("WTAPlayFace")), false, Who);
			Params.AddIgnoredActor(Controller->GetPawn());
			if (AActor* Holder = Who->GetParentActor())
			{
				Params.AddIgnoredActor(Holder);
			}
			TArray<AActor*> Worn;
			Who->GetAttachedActors(Worn, true, true);
			Params.AddIgnoredActors(Worn);
			// (From 25 cm out: anything closer to the face than that is worn, like a headset prop.)
			FHitResult Hit;
			if (GetWorld()->LineTraceSingleByChannel(Hit, Centre + Facing * 25.f, CameraAt, ECC_Visibility, Params))
			{
				const float Distance = FMath::Max(30.f, static_cast<float>(FVector::Dist(Centre, Hit.ImpactPoint)) - 8.f);
				CameraAt = Centre + Facing * Distance + FVector(0.f, 0.f, 2.f);
			}
			FaceCamera->SetActorLocationAndRotation(CameraAt, (Centre - CameraAt).Rotation());
			Controller->SetViewTargetWithBlend(FaceCamera, 0.f);
			// Staff turn toward the player: stand the player behind the camera so they look into it.
			if (Name.StartsWith(TEXT("staff_")))
			{
				if (const AWTACharacter* Character = Player())
				{
					FWTAView View;
					View.Location = Centre + Facing * 150.f;
					View.Location.Z = Centre.Z + 3.f;
					View.Yaw = static_cast<float>((-Facing).Rotation().Yaw);
					View.bValid = true;
					StandAt(View);
				}
			}
			*bPlaced = true;
			return 1.0f;
		} });
		// Staff: where the right hand is now, to see the idle move while the camera is on them.
		Steps.Add({ TEXT("face idle ") + Name, [this, Weak, Hand, bPlaced]() -> float
		{
			if (!*bPlaced)
			{
				return 0.f;
			}
			*Hand = BoneInComponent(UWTAPeopleLibrary::FindBody(Weak.Get()), TEXT("hand_r"));
			return 0.8f;
		} });
		// The shot, and what it shows: the face on the head, no bone left at the feet (the drooping face), the LODs.
		Steps.Add({ TEXT("face shot ") + Name, [this, Name, Weak, Hand, bPlaced]() -> float
		{
			if (!*bPlaced)
			{
				return 0.f;
			}
			Shot(Name, false);
			AActor* Who = Weak.Get();
			USkeletalMeshComponent* Body = UWTAPeopleLibrary::FindBody(Who);
			USkeletalMeshComponent* Face = FindFace(Who);
			if (Who == nullptr || Body == nullptr || Face == nullptr)
			{
				Report(TEXT("faces"), EResult::Skip, Name, TEXT("gone"));
				return 0.35f;
			}
			float Gap = 0.f;
			const bool bFaceOn = UWTAPeopleLibrary::IsFaceOnBody(Who, Gap);
			FString Loose;
			const int32 Collapsed = UWTAPeopleLibrary::CountCollapsedBones(Face, &Loose) + UWTAPeopleLibrary::CountCollapsedBones(Body, &Loose);
			const bool bStaff = Name.StartsWith(TEXT("staff_"));
			const double Moved = FVector::Dist(*Hand, BoneInComponent(Body, TEXT("hand_r")));
			const bool bPass = bFaceOn && Collapsed == 0 && (!bStaff || Moved > 0.02);
			Report(TEXT("faces"), bPass ? EResult::Pass : EResult::Fail, Name + TEXT(" on screen"),
				FString::Printf(TEXT("face %.2f cm off the head, %d bones at the feet%s%s; %s"), Gap, Collapsed,
					Collapsed > 0 ? *(TEXT(" (") + Loose + TEXT(")")) : TEXT(""),
					bStaff ? *FString::Printf(TEXT(", idle: right hand moved %.2f cm in 0.8 s"), Moved) : TEXT(""),
					*UWTAPeopleLibrary::DescribeMeshes(Who)));
			return 0.35f;
		} });
	}
	Steps.Add({ TEXT("faces end"), [this]() -> float
	{
		if (AWTAPlayerController* Controller = PC())
		{
			Controller->SetViewTargetWithBlend(Controller->GetPawn(), 0.f);
		}
		if (FaceCamera != nullptr)
		{
			FaceCamera->Destroy();
			FaceCamera = nullptr;
		}
		return 0.3f;
	} });
}

// ---------------------------------------------------------------------------
// talks: every talk and class
// ---------------------------------------------------------------------------

void UWTAPlayTest::AddQuizSteps(const FString& Phase, const FString& Name, FName TalkId, const TArray<FWTAQuizQuestion>& Quiz, const TSharedRef<bool>& Ok, const FString& Tag)
{
	for (int32 Q = 0; Q < Quiz.Num(); ++Q)
	{
		const int32 Right = Quiz[Q].Answer;
		Steps.Add({ Name + FString::Printf(TEXT(" answer %d"), Q + 1), [this, Ok, TalkId, Q, Right]() -> float
		{
			AWTAPlayerController* Controller = PC();
			if (!*Ok || Controller == nullptr || Controller->Panel == nullptr)
			{
				return 0.f;
			}
			Controller->Panel->HandleAction(FName(TEXT("Answer")), TalkId, Right);
			return Q == 0 ? 0.5f : 0.2f;
		} });
		if (Q == 0)
		{
			Steps.Add({ Name + TEXT(" answered shot"), [this, Ok, Tag]() -> float
			{
				if (*Ok)
				{
					Shot(FString::Printf(TEXT("talk_%s_answered"), *Tag), true);
					return 0.3f;
				}
				return 0.f;
			} });
		}
		Steps.Add({ Name + FString::Printf(TEXT(" next %d"), Q + 1), [this, Ok, TalkId, Q]() -> float
		{
			AWTAPlayerController* Controller = PC();
			if (!*Ok || Controller == nullptr || Controller->Panel == nullptr)
			{
				return 0.f;
			}
			Controller->Panel->HandleAction(FName(TEXT("QuizNext")), TalkId, Q + 1);
			return 0.3f;
		} });
	}
	Steps.Add({ Name + TEXT(" result"), [this, Phase, Ok, Name, Tag, TalkId, Total = Quiz.Num()]() -> float
	{
		AWTAPlayerController* Controller = PC();
		if (!*Ok || Controller == nullptr || Controller->Panel == nullptr)
		{
			return 0.f;
		}
		UWTAPanelWidget* Panel = Controller->Panel;
		const int32 Score = Panel->QuizScore();
		const bool bNameBox = Panel->NameBox != nullptr;
		*Ok = Panel->IsOpen() && Panel->GetMode() == EWTAPanelMode::Quiz && Score == Total && bNameBox;
		Report(*Phase, *Ok ? EResult::Pass : EResult::Fail, Name + TEXT(" scores the quiz"),
			FString::Printf(TEXT("%d of %d right; %s"), Score, Total, bNameBox ? TEXT("the name box is up") : TEXT("no name box (not a pass?)")));
		if (*Ok)
		{
			Panel->NameBox->SetText(FText::FromString(TEXT("QA Visitor")));
			Shot(FString::Printf(TEXT("talk_%s_passed"), *Tag), true);
			return 0.4f;
		}
		return 0.f;
	} });
	Steps.Add({ Name + TEXT(" certificate"), [this, Ok, TalkId]() -> float
	{
		AWTAPlayerController* Controller = PC();
		if (!*Ok || Controller == nullptr || Controller->Panel == nullptr)
		{
			return 0.f;
		}
		Controller->Panel->HandleAction(FName(TEXT("Certificate")), TalkId, -1);
		return 0.9f;
	} });
	Steps.Add({ Name + TEXT(" certificate shows"), [this, Phase, Ok, Name, Tag, TalkId]() -> float
	{
		AWTAPlayerController* Controller = PC();
		if (!*Ok || Controller == nullptr)
		{
			return 0.f;
		}
		const UWTAContentSubsystem* Data = UWTAContentSubsystem::Get(this);
		const FWTATalkRow* Class = Data ? Data->FindTalk(TalkId) : nullptr;
		const UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this);
		const bool bOpen = Controller->Certificate != nullptr && Controller->Certificate->IsOpen();
		const bool bKept = Progress != nullptr && Progress->HasCertificate(TalkId) && Progress->CertificateName(TalkId) == TEXT("QA Visitor");
		const bool bBadge = Class == nullptr || Class->BadgeId.IsNone() || (Progress != nullptr && Progress->HasBadge(Class->BadgeId));
		FString Picture;
		if (bOpen)
		{
			Picture = Controller->Certificate->SavePicture();
		}
		const bool bPicture = !Picture.IsEmpty() && IFileManager::Get().FileSize(*Picture) > 10000;
		*Ok = bOpen && bKept && bBadge && bPicture;
		Report(*Phase, *Ok ? EResult::Pass : EResult::Fail, Name + TEXT(" gives a certificate"),
			FString::Printf(TEXT("%s; kept in progress: %s; badge %s: %s; picture %s"), bOpen ? TEXT("shown") : TEXT("not shown"),
				bKept ? TEXT("yes") : TEXT("no"), Class != nullptr ? *Class->BadgeId.ToString() : TEXT("-"), bBadge ? TEXT("yes") : TEXT("no"),
				bPicture ? *Picture : TEXT("not written")));
		if (bOpen)
		{
			Shot(FString::Printf(TEXT("talk_%s_certificate"), *Tag), true);
			return 0.4f;
		}
		return 0.f;
	} });
}


void UWTAPlayTest::AddTalksPhase()
{
	TArray<AWTATalkActor*> Talks;
	for (TActorIterator<AWTATalkActor> It(GetWorld()); It; ++It)
	{
		if (*It != nullptr)
		{
			Talks.Add(*It);
		}
	}
	Talks.Sort([](const AWTATalkActor& A, const AWTATalkActor& B) { return A.TalkId.LexicalLess(B.TalkId); });
	Steps.Add({ TEXT("talks start"), [this, Count = Talks.Num()]() -> float
	{
		Report(TEXT("talks"), Count > 0 ? EResult::Info : EResult::Fail, TEXT("talks"), FString::Printf(TEXT("%d talks and classes in the level"), Count));
		return 0.f;
	} });

	for (AWTATalkActor* Talk : Talks)
	{
		const TWeakObjectPtr<AWTATalkActor> Weak(Talk);
		const FString Id = Talk->TalkId.ToString();
		const FString Name = FString::Printf(TEXT("talk %s"), *Id);
		const FString Tag = Id.Replace(TEXT("-"), TEXT("_"));
		const TSharedRef<bool> Ok = MakeShared<bool>(false);
		const TSharedRef<TWeakObjectPtr<AWTASeatActor>> Seat = MakeShared<TWeakObjectPtr<AWTASeatActor>>();

		// 1. The venue is built: a row, screens, a speaker; the title slide is up. A shot of the speaker at rest.
		Steps.Add({ Name + TEXT(" venue"), [this, Weak, Name, Ok, Seat, Tag]() -> float
		{
			*Ok = false;
			AWTATalkActor* Target = Weak.Get();
			if (Target == nullptr)
			{
				Report(TEXT("talks"), EResult::Skip, Name, TEXT("gone"));
				return 0.f;
			}
			CloseAll();
			if (AWTACharacter* Me = Player())
			{
				if (Me->IsSeated())
				{
					Me->StandUp(false);
				}
			}
			const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
			const FWTATalkRow* Row = Content ? Content->FindTalk(Target->TalkId) : nullptr;
			if (!Target->HasRow() || Row == nullptr)
			{
				Report(TEXT("talks"), EResult::Fail, Name + TEXT(" has a row"), TEXT("no DT_Talks row"));
				return 0.f;
			}
			// one of the venue's seats, the first by name
			TArray<AWTASeatActor*> Seats;
			for (TActorIterator<AWTASeatActor> It(GetWorld()); It; ++It)
			{
				if (*It != nullptr && AWTATalkActor::VenueOfSeat((*It)->SeatId) == Target->GetVenue())
				{
					Seats.Add(*It);
				}
			}
			Seats.Sort([](const AWTASeatActor& A, const AWTASeatActor& B) { return A.SeatId.LexicalLess(B.SeatId); });
			*Seat = Seats.Num() > 0 ? Seats[Seats.Num() / 2] : nullptr;
			const AActor* Speaker = Target->GetSpeaker();
			const bool bScreens = Target->NumScreens() > 0;
			const bool bSeats = Seats.Num() > 0;
			*Ok = bScreens && bSeats;
			Report(TEXT("talks"), *Ok ? EResult::Pass : EResult::Fail, Name + TEXT(" venue is built"),
				FString::Printf(TEXT("'%s' in %s: %d slides, %d screens, %d seats, speaker %s (%s), state %d"), *Row->Title.ToString(),
					*Target->GetVenue().ToString(), Target->NumSlides(), Target->NumScreens(), Seats.Num(),
					Speaker != nullptr ? *Speaker->GetName() : TEXT("none"), Row->Staff.IsNone() ? *Row->Person.ToString() : *Row->Staff.ToString(),
					static_cast<int32>(Target->GetState())));
			if (Speaker == nullptr)
			{
				Report(TEXT("talks"), EResult::Info, Name + TEXT(" speaker"), TEXT("no speaker on the spot (the person is not built, or the staff member is not in the level)"));
			}
			// the speaker from a few steps in front, looking back at the lectern, no HUD
			FWTAView View;
			const FVector Forward = FRotator(0.f, Target->SpeakerYaw, 0.f).Vector();
			View.Location = Target->GetSpot() + Forward * 260.f + FVector(0.f, 0.f, 150.f);
			View.Yaw = Target->SpeakerYaw + 180.f;
			View.Pitch = -4.f;
			View.bValid = true;
			StandAt(View);
			return 0.8f;
		} });
		Steps.Add({ Name + TEXT(" speaker shot"), [this, Ok, Tag]() -> float
		{
			if (*Ok)
			{
				Shot(FString::Printf(TEXT("talk_%s_speaker"), *Tag), false);
				return 0.3f;
			}
			return 0.f;
		} });

		// 2. Sit on a seat of the venue: the talk starts.
		Steps.Add({ Name + TEXT(" to a seat"), [this, Ok, Seat, Name]() -> float
		{
			AWTASeatActor* Target = Seat->Get();
			if (!*Ok || Target == nullptr)
			{
				return 0.f;
			}
			FWTAView View;
			if (!IWTAInteractable::Execute_GetViewSpot(Target, View) || !View.bValid)
			{
				*Ok = false;
				Report(TEXT("talks"), EResult::Fail, Name + TEXT(" seat"), TEXT("the seat has no view spot"));
				return 0.f;
			}
			StandAt(View);
			return 0.5f;
		} });
		Steps.Add({ Name + TEXT(" hover"), [this, Ok, Seat]() -> float
		{
			AWTASeatActor* Target = Seat->Get();
			AWTAPlayerController* Controller = PC();
			if (!*Ok || Target == nullptr || Controller == nullptr || Controller->Interaction == nullptr)
			{
				return 0.f;
			}
			if (Controller->Interaction->GetHovered() != Target)
			{
				FWTAView Aim;
				if (FindAimView(Target, Aim))
				{
					StandAt(Aim);
					return 0.45f;
				}
			}
			return 0.f;
		} });
		const TSharedRef<bool> KeyWasDown = MakeShared<bool>(false);
		Steps.Add({ Name + TEXT(" sit"), [this, Ok, Seat, KeyWasDown]() -> float
		{
			AWTASeatActor* Target = Seat->Get();
			AWTAPlayerController* Controller = PC();
			*KeyWasDown = false;
			if (!*Ok || Target == nullptr || Controller == nullptr)
			{
				return 0.f;
			}
			// E when the crosshair is on the seat; through the seat itself when it missed (the seats phase checks hovering)
			if (Controller->Interaction != nullptr && Controller->Interaction->GetHovered() == Target)
			{
				KeyDown(EKeys::E);
				*KeyWasDown = true;
				return 0.12f;
			}
			IWTAInteractable::Execute_Interact(Target, Controller);
			return 0.12f;
		} });
		Steps.Add({ Name + TEXT(" sit up"), [this, KeyWasDown]() -> float
		{
			if (*KeyWasDown)
			{
				KeyUp(EKeys::E);
			}
			return 1.2f;
		} });
		Steps.Add({ Name + TEXT(" playing"), [this, Weak, Ok, Seat, Name, Tag]() -> float
		{
			AWTATalkActor* Target = Weak.Get();
			AWTACharacter* Me = Player();
			if (!*Ok || Target == nullptr || Me == nullptr)
			{
				return 0.f;
			}
			const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
			const FWTATalkRow* Row = Content ? Content->FindTalk(Target->TalkId) : nullptr;
			UWTAVoiceSubsystem* Voice = UWTAVoiceSubsystem::Get(this);
			const bool bSeated = Me->IsSeated() && Me->GetSeat() == Seat->Get();
			const bool bPlaying = Target->GetState() == EWTATalkState::Playing && Target->GetSlideIndex() == 0;
			const FName Clip = Row != nullptr && Row->Slides.Num() > 0 ? Row->Slides[0].Clip : NAME_None;
			const bool bHasClip = Voice != nullptr && !Clip.IsNone() && Voice->HasClip(AWTATalkActor::VoiceKindTalk, Clip);
			const bool bReading = bHasClip && Voice->IsReadingCard(AWTATalkActor::VoiceKindTalk, Clip);
			*Ok = bSeated && bPlaying && (!bHasClip || bReading);
			Report(TEXT("talks"), *Ok ? EResult::Pass : EResult::Fail, Name + TEXT(" starts when you sit"),
				FString::Printf(TEXT("%s; state %d, slide %d; narration %s"), bSeated ? TEXT("seated") : TEXT("not seated"),
					static_cast<int32>(Target->GetState()), Target->GetSlideIndex() + 1,
					bHasClip ? (bReading ? TEXT("reading") : TEXT("imported but silent")) : TEXT("not imported (the slide runs on its clock)")));
			if (*Ok)
			{
				Shot(FString::Printf(TEXT("talk_%s_seated"), *Tag), true);
				return 0.4f;
			}
			return 0.f;
		} });
		Steps.Add({ Name + TEXT(" next slide"), [this, Weak, Ok]() -> float
		{
			if (!*Ok || Weak.Get() == nullptr)
			{
				return 0.f;
			}
			Weak->GoToSlide(1);
			return 1.0f;
		} });
		Steps.Add({ Name + TEXT(" slide 2"), [this, Weak, Ok, Name, Tag]() -> float
		{
			AWTATalkActor* Target = Weak.Get();
			if (!*Ok || Target == nullptr)
			{
				return 0.f;
			}
			const bool bOn = Target->GetState() == EWTATalkState::Playing && Target->GetSlideIndex() == 1;
			Report(TEXT("talks"), bOn ? EResult::Pass : EResult::Fail, Name + TEXT(" moves on to its next slide"),
				FString::Printf(TEXT("state %d, slide %d of %d"), static_cast<int32>(Target->GetState()), Target->GetSlideIndex() + 1, Target->NumSlides()));
			Shot(FString::Printf(TEXT("talk_%s_slide2"), *Tag), false);
			return 0.4f;
		} });

		// 3. A class: straight to its end, the quiz opens, answer every question right, the certificate.
		const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
		const FWTATalkRow* Row = Content ? Content->FindTalk(Talk->TalkId) : nullptr;
		if (Row != nullptr && Row->IsClass() && Row->Quiz.Num() > 0)
		{
			const FName TalkId = Talk->TalkId;
			Steps.Add({ Name + TEXT(" to the end"), [this, Weak, Ok]() -> float
			{
				if (!*Ok || Weak.Get() == nullptr)
				{
					return 0.f;
				}
				Weak->GoToSlide(Weak->NumSlides());
				return 2.6f;                                      // the quiz opens 1.5 s after the last line
			} });
			Steps.Add({ Name + TEXT(" quiz opens"), [this, Weak, Ok, Name, Tag, TalkId]() -> float
			{
				AWTATalkActor* Target = Weak.Get();
				AWTAPlayerController* Controller = PC();
				if (!*Ok || Target == nullptr || Controller == nullptr || Controller->Panel == nullptr)
				{
					return 0.f;
				}
				const bool bDone = Target->GetState() == EWTATalkState::Done;
				const bool bQuiz = Controller->Panel->IsOpen() && Controller->Panel->GetMode() == EWTAPanelMode::Quiz && Controller->Panel->GetCurrentId() == TalkId;
				const UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this);
				const bool bHeard = Progress != nullptr && Progress->HasHeardTalk(TalkId) && Progress->HasBadge(WTABadge::Listener());
				*Ok = bDone && bQuiz;
				Report(TEXT("talks"), *Ok ? EResult::Pass : EResult::Fail, Name + TEXT(" ends in its quiz"),
					FString::Printf(TEXT("state %d; the panel shows %s; heard and the Listener badge: %s"), static_cast<int32>(Target->GetState()),
						bQuiz ? TEXT("the quiz") : TEXT("something else"), bHeard ? TEXT("yes") : TEXT("no")));
				if (*Ok)
				{
					Shot(FString::Printf(TEXT("talk_%s_quiz"), *Tag), true);
					return 0.4f;
				}
				return 0.f;
			} });
			AddQuizSteps(TEXT("talks"), Name, TalkId, Row->Quiz, Ok, Tag);
		}

		// 4. Stand up: the talk stops and the caption goes.
		Steps.Add({ Name + TEXT(" stand"), [this, Weak, Ok]() -> float
		{
			CloseAll();
			if (!*Ok || Weak.Get() == nullptr)
			{
				return 0.f;
			}
			if (AWTACharacter* Me = Player())
			{
				if (Me->IsSeated())
				{
					Me->StandUp(true);
				}
			}
			return 0.5f;
		} });
		Steps.Add({ Name + TEXT(" stopped"), [this, Weak, Ok, Name]() -> float
		{
			AWTATalkActor* Target = Weak.Get();
			if (!*Ok || Target == nullptr)
			{
				return 0.f;
			}
			const bool bStopped = Target->GetState() != EWTATalkState::Playing && Target->GetState() != EWTATalkState::Waiting;
			const UWTAVoiceSubsystem* Voice = UWTAVoiceSubsystem::Get(this);
			const bool bQuiet = Voice == nullptr || !Voice->IsReading();
			Report(TEXT("talks"), bStopped && bQuiet ? EResult::Pass : EResult::Fail, Name + TEXT(" stops when you stand up"),
				FString::Printf(TEXT("state %d, the voice %s"), static_cast<int32>(Target->GetState()), bQuiet ? TEXT("quiet") : TEXT("still reading")));
			return 0.f;
		} });
	}
}

// ---------------------------------------------------------------------------
// quiz: every class's quiz and certificate, opened straight from the table (no venue needed)
// ---------------------------------------------------------------------------

void UWTAPlayTest::AddStationsPhase()
{
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	TArray<FName> Ids = Content != nullptr ? Content->GetRowNames(EWTATable::Stations) : TArray<FName>();
	Ids.Sort([](const FName& A, const FName& B) { return A.LexicalLess(B); });
	Steps.Add({ TEXT("stations start"), [this, Count = Ids.Num()]() -> float
	{
		Report(TEXT("stations"), Count > 0 ? EResult::Info : EResult::Fail, TEXT("stations"), FString::Printf(TEXT("%d stations in DT_Stations"), Count));
		return 0.f;
	} });
	bool bShot = false;
	for (const FName& StationId : Ids)
	{
		const FWTAStationRow* Row = Content->FindStation(StationId);
		if (Row == nullptr)
		{
			continue;
		}
		const FString Name = FString::Printf(TEXT("station %s"), *StationId.ToString());
		const int32 NumSteps = Row->Steps.Num();
		const TSharedRef<bool> Ok = MakeShared<bool>(false);
		const bool bTakeShot = !bShot;
		bShot = true;
		Steps.Add({ Name + TEXT(" open"), [this, Ok, Name, StationId, NumSteps]() -> float
		{
			*Ok = false;
			AWTAPlayerController* Controller = PC();
			if (Controller == nullptr || Controller->Panel == nullptr)
			{
				return 0.f;
			}
			CloseAll();
			Controller->OpenStation(StationId);
			UWTAPanelWidget* Panel = Controller->Panel;
			const bool bOpen = Panel->IsOpen() && Panel->GetMode() == EWTAPanelMode::Station && Panel->GetCurrentId() == StationId && Panel->GetCurrentPage() == 0;
			*Ok = bOpen && NumSteps > 0;
			Report(TEXT("stations"), *Ok ? EResult::Pass : EResult::Fail, Name + TEXT(" opens"),
				bOpen ? FString::Printf(TEXT("the overview, %d steps"), NumSteps) : TEXT("the station card did not open on its overview"));
			return *Ok ? 0.3f : 0.f;
		} });
		for (int32 Step = 1; Step <= NumSteps; ++Step)
		{
			const FText Title = Row->Steps[Step - 1];
			Steps.Add({ FString::Printf(TEXT("%s step %d"), *Name, Step), [this, Ok, Name, StationId, Step, NumSteps, Title, bTakeShot]() -> float
			{
				AWTAPlayerController* Controller = PC();
				if (!*Ok || Controller == nullptr || Controller->Panel == nullptr)
				{
					return 0.f;
				}
				UWTAPanelWidget* Panel = Controller->Panel;
				Panel->HandleAction(FName("StationStep"), StationId, Step);
				const bool bOn = Panel->IsOpen() && Panel->GetMode() == EWTAPanelMode::Station && Panel->GetCurrentPage() == Step;
				if (!bOn)
				{
					*Ok = false;
					Report(TEXT("stations"), EResult::Fail, FString::Printf(TEXT("%s shows step %d"), *Name, Step),
						FString::Printf(TEXT("the card is on page %d"), Panel->GetCurrentPage()));
					return 0.f;
				}
				if (Step == 1 || Step == NumSteps)
				{
					Report(TEXT("stations"), EResult::Pass, FString::Printf(TEXT("%s shows step %d"), *Name, Step),
						FString::Printf(TEXT("'%s' of %d"), *Title.ToString(), NumSteps));
				}
				return bTakeShot && Step == 1 ? 0.5f : 0.15f;
			} });
			if (bTakeShot && Step == 1)
			{
				// a frame or two after the card is built, so the wrapped text has its height before the picture
				Steps.Add({ Name + TEXT(" step 1 shot"), [this, Ok, StationId]() -> float
				{
					if (*Ok)
					{
						Shot(FString::Printf(TEXT("station_%s_step1"), *StationId.ToString()), true);
						return 0.3f;
					}
					return 0.f;
				} });
			}
		}
		Steps.Add({ Name + TEXT(" finish"), [this, Ok, Name, StationId]() -> float
		{
			AWTAPlayerController* Controller = PC();
			UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this);
			if (!*Ok || Controller == nullptr || Controller->Panel == nullptr || Progress == nullptr)
			{
				return 0.f;
			}
			UWTAPanelWidget* Panel = Controller->Panel;
			Panel->HandleAction(FName("StationFinish"), StationId, 0);
			const bool bDone = Progress->HasFinishedStation(StationId);
			const bool bOverview = Panel->IsOpen() && Panel->GetMode() == EWTAPanelMode::Station && Panel->GetCurrentPage() == 0;
			*Ok = bDone && bOverview;
			Report(TEXT("stations"), *Ok ? EResult::Pass : EResult::Fail, Name + TEXT(" finishes"),
				FString::Printf(TEXT("remembered as finished: %s; back on the overview: %s"), bDone ? TEXT("yes") : TEXT("no"), bOverview ? TEXT("yes") : TEXT("no")));
			CloseAll();
			return 0.3f;
		} });
	}
}

void UWTAPlayTest::AddCoursePhase()
{
	// Every DT_Talks row of kind course: its desk in the level (an AWTACourseActor with the lead at it), the card
	// (OpenCourse), each of its stations finished through the station card, the card again with every station
	// ticked and the quiz button up, the quiz answered right, the certificate, then the card once more saying so.
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	TArray<FName> Courses;
	if (Content != nullptr)
	{
		for (const FName& Id : Content->GetRowNames(EWTATable::Talks))
		{
			const FWTATalkRow* Row = Content->FindTalk(Id);
			if (Row != nullptr && Row->IsCourse())
			{
				Courses.Add(Id);
			}
		}
	}
	Courses.Sort([](const FName& A, const FName& B) { return A.LexicalLess(B); });
	Steps.Add({ TEXT("course start"), [this, Count = Courses.Num()]() -> float
	{
		Report(TEXT("course"), Count > 0 ? EResult::Info : EResult::Fail, TEXT("courses"), FString::Printf(TEXT("%d courses in DT_Talks"), Count));
		return 0.f;
	} });
	for (const FName& TalkId : Courses)
	{
		const FWTATalkRow* Row = Content->FindTalk(TalkId);
		const FString Name = FString::Printf(TEXT("course %s"), *TalkId.ToString());
		const FString Tag = TalkId.ToString().Replace(TEXT("-"), TEXT("_"));
		const TArray<FName> Stations = Row->Stations;
		const FName Venue = Row->Venue;
		const TSharedRef<bool> Ok = MakeShared<bool>(false);
		Steps.Add({ Name + TEXT(" desk"), [this, Name, Venue]() -> float
		{
			AWTACourseActor* Desk = AWTACourseActor::FindForVenue(this, Venue);
			if (Desk == nullptr)
			{
				Report(TEXT("course"), EResult::Info, Name + TEXT(" desk"), FString::Printf(TEXT("no course desk at venue '%s' (its wing's builder has not run); the card still works"), *Venue.ToString()));
				return 0.f;
			}
			const FString Label = IWTAInteractable::Execute_GetInteractLabel(Desk).ToString();
			const bool bLabel = Label.StartsWith(TEXT("Course"));
			Report(TEXT("course"), bLabel ? EResult::Pass : EResult::Fail, Name + TEXT(" desk"),
				FString::Printf(TEXT("%s at %s says \"%s\"; lead %s"), *Desk->GetName(), *Venue.ToString(), *Label,
					Desk->GetLead() != nullptr ? *Desk->GetLead()->GetName() : TEXT("not built (person missing)")));
			return 0.f;
		} });
		Steps.Add({ Name + TEXT(" open"), [this, Ok, Name, TalkId, Total = Stations.Num()]() -> float
		{
			*Ok = false;
			AWTAPlayerController* Controller = PC();
			if (Controller == nullptr || Controller->Panel == nullptr)
			{
				return 0.f;
			}
			CloseAll();
			Controller->OpenCourse(TalkId);
			UWTAPanelWidget* Panel = Controller->Panel;
			const bool bOpen = Panel->IsOpen() && Panel->GetMode() == EWTAPanelMode::Course && Panel->GetCurrentId() == TalkId;
			*Ok = bOpen && Total > 0;
			Report(TEXT("course"), *Ok ? EResult::Pass : EResult::Fail, Name + TEXT(" opens"),
				bOpen ? FString::Printf(TEXT("%d of %d stations ticked"), Panel->GetCurrentPage(), Total) : TEXT("the course card did not open"));
			return *Ok ? 0.5f : 0.f;
		} });
		Steps.Add({ Name + TEXT(" card shot"), [this, Ok, Tag]() -> float
		{
			if (*Ok)
			{
				Shot(FString::Printf(TEXT("course_%s_card"), *Tag), true);
				return 0.3f;
			}
			return 0.f;
		} });
		for (const FName& StationId : Stations)
		{
			Steps.Add({ FString::Printf(TEXT("%s finish %s"), *Name, *StationId.ToString()), [this, Ok, Name, StationId]() -> float
			{
				AWTAPlayerController* Controller = PC();
				UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this);
				if (!*Ok || Controller == nullptr || Controller->Panel == nullptr || Progress == nullptr)
				{
					return 0.f;
				}
				UWTAPanelWidget* Panel = Controller->Panel;
				// the Go button's action, then the station's own Finish
				Panel->HandleAction(WTAAction::OpenStation(), StationId, -1);
				const bool bStation = Panel->IsOpen() && Panel->GetMode() == EWTAPanelMode::Station && Panel->GetCurrentId() == StationId;
				if (bStation)
				{
					Panel->HandleAction(FName("StationFinish"), StationId, 0);
				}
				const bool bDone = Progress->HasFinishedStation(StationId);
				if (!bStation || !bDone)
				{
					*Ok = false;
				}
				Report(TEXT("course"), bStation && bDone ? EResult::Pass : EResult::Fail, FString::Printf(TEXT("%s finishes %s"), *Name, *StationId.ToString()),
					bStation ? (bDone ? TEXT("Go opened the station; finished") : TEXT("the station opened but is not remembered as finished")) : TEXT("Go did not open the station card"));
				return 0.2f;
			} });
		}
		Steps.Add({ Name + TEXT(" all ticked"), [this, Ok, Name, TalkId, Total = Stations.Num()]() -> float
		{
			AWTAPlayerController* Controller = PC();
			if (!*Ok || Controller == nullptr || Controller->Panel == nullptr)
			{
				return 0.f;
			}
			CloseAll();
			Controller->OpenCourse(TalkId);
			UWTAPanelWidget* Panel = Controller->Panel;
			const int32 Done = Panel->GetCurrentPage();
			*Ok = Panel->IsOpen() && Panel->GetMode() == EWTAPanelMode::Course && Done == Total;
			Report(TEXT("course"), *Ok ? EResult::Pass : EResult::Fail, Name + TEXT(" ticks every station"),
				FString::Printf(TEXT("%d of %d ticked on the card"), Done, Total));
			return *Ok ? 0.5f : 0.f;
		} });
		Steps.Add({ Name + TEXT(" ticked shot"), [this, Ok, Tag]() -> float
		{
			if (*Ok)
			{
				Shot(FString::Printf(TEXT("course_%s_ticked"), *Tag), true);
				return 0.3f;
			}
			return 0.f;
		} });
		Steps.Add({ Name + TEXT(" quiz"), [this, Ok, Name, TalkId]() -> float
		{
			AWTAPlayerController* Controller = PC();
			if (!*Ok || Controller == nullptr || Controller->Panel == nullptr)
			{
				return 0.f;
			}
			UWTAPanelWidget* Panel = Controller->Panel;
			Panel->HandleAction(WTAAction::OpenQuiz(), TalkId, -1);        // the card's "Take the quiz" button
			*Ok = Panel->IsOpen() && Panel->GetMode() == EWTAPanelMode::Quiz && Panel->GetCurrentId() == TalkId;
			Report(TEXT("course"), *Ok ? EResult::Pass : EResult::Fail, Name + TEXT(" opens its quiz"), *Ok ? TEXT("question 1 is up") : TEXT("the quiz card did not open from the course card"));
			return *Ok ? 0.4f : 0.f;
		} });
		AddQuizSteps(TEXT("course"), Name, TalkId, Row->Quiz, Ok, Tag);
		Steps.Add({ Name + TEXT(" certified"), [this, Ok, Name, TalkId]() -> float
		{
			AWTAPlayerController* Controller = PC();
			const UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this);
			if (!*Ok || Controller == nullptr || Controller->Panel == nullptr || Progress == nullptr)
			{
				return 0.f;
			}
			CloseAll();
			Controller->OpenCourse(TalkId);
			UWTAPanelWidget* Panel = Controller->Panel;
			const bool bCard = Panel->IsOpen() && Panel->GetMode() == EWTAPanelMode::Course && Panel->GetCurrentId() == TalkId;
			const bool bCert = Progress->HasCertificate(TalkId);
			*Ok = bCard && bCert;
			Report(TEXT("course"), *Ok ? EResult::Pass : EResult::Fail, Name + TEXT(" card says certified"),
				FString::Printf(TEXT("card %s; certificate kept: %s"), bCard ? TEXT("open") : TEXT("not open"), bCert ? TEXT("yes") : TEXT("no")));
			return *Ok ? 0.5f : 0.f;
		} });
		Steps.Add({ Name + TEXT(" certified shot"), [this, Ok, Tag]() -> float
		{
			if (*Ok)
			{
				Shot(FString::Printf(TEXT("course_%s_certified"), *Tag), true);
			}
			CloseAll();
			return 0.3f;
		} });
	}
}

void UWTAPlayTest::AddQuizPhase()
{
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	TArray<FName> Classes;
	if (Content != nullptr)
	{
		for (const FName& Id : Content->GetRowNames(EWTATable::Talks))
		{
			const FWTATalkRow* Row = Content->FindTalk(Id);
			if (Row != nullptr && Row->IsClass() && Row->Quiz.Num() > 0)
			{
				Classes.Add(Id);
			}
		}
	}
	Classes.Sort([](const FName& A, const FName& B) { return A.LexicalLess(B); });
	Steps.Add({ TEXT("quiz start"), [this, Count = Classes.Num()]() -> float
	{
		Report(TEXT("quiz"), Count > 0 ? EResult::Info : EResult::Fail, TEXT("classes"), FString::Printf(TEXT("%d classes with a quiz in DT_Talks"), Count));
		return 0.f;
	} });
	for (const FName& TalkId : Classes)
	{
		const FWTATalkRow* Row = Content->FindTalk(TalkId);
		const FString Name = FString::Printf(TEXT("quiz %s"), *TalkId.ToString());
		const FString Tag = TalkId.ToString().Replace(TEXT("-"), TEXT("_"));
		const TSharedRef<bool> Ok = MakeShared<bool>(false);
		Steps.Add({ Name + TEXT(" open"), [this, Ok, Name, Tag, TalkId]() -> float
		{
			*Ok = false;
			AWTAPlayerController* Controller = PC();
			if (Controller == nullptr || Controller->Panel == nullptr)
			{
				return 0.f;
			}
			CloseAll();
			Controller->OpenQuiz(TalkId);
			const bool bQuiz = Controller->Panel->IsOpen() && Controller->Panel->GetMode() == EWTAPanelMode::Quiz && Controller->Panel->GetCurrentId() == TalkId;
			*Ok = bQuiz;
			Report(TEXT("quiz"), *Ok ? EResult::Pass : EResult::Fail, Name + TEXT(" opens"), bQuiz ? TEXT("question 1 is up") : TEXT("the quiz card did not open"));
			if (*Ok)
			{
				Shot(FString::Printf(TEXT("quiz_%s_q1"), *Tag), true);
				return 0.4f;
			}
			return 0.f;
		} });
		AddQuizSteps(TEXT("quiz"), Name, TalkId, Row->Quiz, Ok, Tag);
		Steps.Add({ Name + TEXT(" close"), [this]() -> float { CloseAll(); return 0.3f; } });
	}
}
