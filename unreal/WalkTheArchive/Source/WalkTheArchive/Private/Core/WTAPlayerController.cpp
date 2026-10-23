// Walk the Archive - the player controller: input, widgets, panels, travel.
//
// Enhanced Input is built here in code. The controller's InputComponent is a UEnhancedInputComponent only when
// Config/DefaultInput.ini sets DefaultInputComponentClass=/Script/EnhancedInput.EnhancedInputComponent (and
// DefaultPlayerInputClass=/Script/EnhancedInput.EnhancedPlayerInput); SetupInputComponent logs an error otherwise.

#include "Core/WTAPlayerController.h"
#include "Core/WTAText.h"
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
#include "Systems/WTAVisitSubsystem.h"
#include "Core/WTAPlayerState.h"
#include "UI/WTACertificateWidget.h"
#include "UI/WTAPostcardWidget.h"
#include "UI/WTAChatWidget.h"
#include "UI/WTAHudWidget.h"
#include "UI/WTAMenuWidget.h"
#include "UI/WTAPanelWidget.h"
#include "UI/WTAVisitWidget.h"
#include "UI/WTAVRRootWidget.h"
#include "World/WTAExhibitActor.h"
#include "XR/WTAVRRig.h"
#include "XR/WTAVRScreenActor.h"
#include "XR/WTAXR.h"
#include "Components/Border.h"
#include "Components/WidgetInteractionComponent.h"
#include "World/WTATalkActor.h"
#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/GameViewportClient.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Pawn.h"
#include "InputAction.h"
#include "InputActionValue.h"
#include "InputCoreTypes.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "InputTriggers.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
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

	/** VR: the card screen 1.15 m in front of the eye and 12 cm under it; the HUD screen 1.65 m off and 14 cm under. */
	constexpr float VRCardDistance = 115.f;
	constexpr float VRCardDrop = 12.f;
	constexpr float VRHudDistance = 165.f;
	constexpr float VRHudDrop = 14.f;
	/** The card screen is 1280 x 800 pixels on 1.12 m, the HUD screen 1600 x 900 on 1.85 m (the HUD's own layout). */
	const FIntPoint VRCardPixels(1280, 800);
	constexpr float VRCardWidth = 112.f;
	const FIntPoint VRHudPixels(1600, 900);
	constexpr float VRHudWidth = 185.f;
	/** How far the laser reaches, and the longest step it takes on the floor. */
	constexpr float VRLaserReach = 2000.f;
	constexpr float VRStepReach = 1200.f;

	/** A card's full-screen scrim (its root border) shows on the desktop and goes clear in VR, so the card floats. */
	void ShowScrim(UUserWidget* Widget, bool bShow)
	{
		UBorder* Root = Widget != nullptr && Widget->WidgetTree != nullptr ? Cast<UBorder>(Widget->WidgetTree->RootWidget) : nullptr;
		if (Root != nullptr)
		{
			Root->SetBrushColor(FLinearColor(1.f, 1.f, 1.f, bShow ? 1.f : 0.f));
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
	UWTAVisitSubsystem* Visit = UWTAVisitSubsystem::Get(this);
	if (Visit != nullptr)
	{
		Visit->OnVisitChanged.AddDynamic(this, &AWTAPlayerController::HandleVisitChanged);
		if (Visit->IsInVisit())
		{
			const FString Name = Visit->GetMyName();
			if (!Name.IsEmpty())
			{
				ServerSetVisitName(Name);
			}
		}
		FText Toast;
		if (Visit->TakePendingToast(Toast))
		{
			ShowToast(Toast, 6.f);
		}
		// QA: a play test that changed the map to lead or join a visit goes on here.
		FString Phases;
		if (Visit->TakePendingPlayTest(Phases))
		{
			FTimerHandle Handle;
			GetWorldTimerManager().SetTimer(Handle, FTimerDelegate::CreateWeakLambda(this, [this, Phases]() { WTAPlayTest(Phases); }), 2.f, false);
		}
		HandleVisitChanged();
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

	// The intro menu greets a new visit, not a map change made by a guided visit.
	const UWTASettings* Settings = UWTASettings::Get();
	const bool bVisitChange = bArrivedFromVisit || (Visit != nullptr && Visit->IsInVisit());
	if (Settings != nullptr && Settings->bShowIntroMenu && Menu != nullptr && !bVisitChange)
	{
		Menu->Open(true);
	}
	SetUIMode(IsAnyPanelOpen());

	// VR from the start: a headset still running (a guided visit changed the map), -headset, or -vrsim.
	if (WTAXR::IsHeadsetEnabled() || WTAXR::IsHeadsetRequested() || WTAXR::IsSimulationRequested())
	{
		VRStartTries = 0;
		StartVRWhenReady();
	}
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
	Input->BindAction(PhotoAction, ETriggerEvent::Started, this, &AWTAPlayerController::OnPhoto);
	Input->BindAction(VisitAction, ETriggerEvent::Started, this, &AWTAPlayerController::OnVisit);
	Input->BindAction(GatherAction, ETriggerEvent::Started, this, &AWTAPlayerController::OnGather);
	Input->BindAction(InteractAction, ETriggerEvent::Completed, this, &AWTAPlayerController::OnInteractEnd);
	Input->BindAction(VRSelectAction, ETriggerEvent::Started, this, &AWTAPlayerController::OnVRSelect);
	Input->BindAction(VRSelectAction, ETriggerEvent::Completed, this, &AWTAPlayerController::OnVRSelectEnd);
	Input->BindAction(VRTurnAction, ETriggerEvent::Triggered, this, &AWTAPlayerController::OnVRTurn);
	Input->BindAction(VRTurnAction, ETriggerEvent::Completed, this, &AWTAPlayerController::OnVRTurnEnd);
	Input->BindAction(VRScrollAction, ETriggerEvent::Triggered, this, &AWTAPlayerController::OnVRScroll);
	Input->BindAction(VRWheelAction, ETriggerEvent::Triggered, this, &AWTAPlayerController::OnVRWheel);
}

void AWTAPlayerController::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// Standing between two facing wax scenes: the plaque and the narration follow where the player looks.
	if (InsideStageIds.Num() > 1)
	{
		UpdateFacedStage();
	}

	// VR: the screens follow what is open and where the head is, and the laser does what the crosshair does.
	// Nothing walks the player there (GoToView travels by a fade), so the walking camera below has nothing to do.
	if (bVRMode)
	{
		UpdateVRScreens(DeltaSeconds);
		UpdateVRPointer();
		return;
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
	// A guided visit changes that: the machine's own player comes back where they stood before the map changed
	// for the visit, and a visitor joining the guide's machine starts at their place round the guide.
	const UWTASettings* Settings = UWTASettings::Get();
	AWTACharacter* PlayerCharacter = Cast<AWTACharacter>(InPawn);
	UWTAVisitSubsystem* Visit = UWTAVisitSubsystem::Get(this);
	FWTAView Start;
	bool bStart = false;
	if (IsLocalController())
	{
		bStart = Visit != nullptr && Visit->TakeRestoreView(Start);
		bArrivedFromVisit = bStart;
	}
	else if (Visit != nullptr)
	{
		bStart = Visit->ArrivalViewFor(GetPlayerState<AWTAPlayerState>(), Start);
	}
	if (!bStart && Settings != nullptr && Settings->SpawnView.bValid)
	{
		Start = Settings->SpawnView;
		bStart = true;
	}
	if (PlayerCharacter != nullptr && bStart)
	{
		PlayerCharacter->TeleportToView(Start);
		if (!IsLocalController())
		{
			ClientSetRotation(FRotator(Start.Pitch, Start.Yaw, 0.f), true);
		}
	}
	bHasPendingView = false;
	bFaceTravelDirection = false;
	// In VR a new pawn gets the rig too (a respawn keeps the headset view).
	if (bVRMode && PlayerCharacter != nullptr && IsLocalController())
	{
		PlayerCharacter->StartVR(bVRHeadset);
	}
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
	PhotoAction        = MakeAction(this, TEXT("IA_Photo"), EInputActionValueType::Boolean);
	VisitAction        = MakeAction(this, TEXT("IA_Visit"), EInputActionValueType::Boolean);
	GatherAction       = MakeAction(this, TEXT("IA_Gather"), EInputActionValueType::Boolean);

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
	MappingContext->MapKey(PhotoAction, EKeys::P);
	MappingContext->MapKey(PhotoAction, EKeys::Gamepad_FaceButton_Top);
	MappingContext->MapKey(VisitAction, EKeys::V);
	MappingContext->MapKey(GatherAction, EKeys::G);

	// --- VR ---------------------------------------------------------------------------------------
	// The controllers' keys live in their own context, added only in VR. OpenXR turns a context into an action set
	// and each action into an OpenXR action (named after the descriptions; identical descriptions are not allowed),
	// when a session starts: WTAXR::BeginSession hands it this one.
	VRSelectAction = MakeAction(this, TEXT("IA_VRSelect"), EInputActionValueType::Boolean);
	VRTurnAction   = MakeAction(this, TEXT("IA_VRTurn"), EInputActionValueType::Axis1D);
	VRScrollAction = MakeAction(this, TEXT("IA_VRScroll"), EInputActionValueType::Axis1D);
	VRWheelAction  = MakeAction(this, TEXT("IA_VRWheel"), EInputActionValueType::Axis1D);
	MoveAction->ActionDescription = FText::FromString(TEXT("Walk"));
	BackAction->ActionDescription = FText::FromString(TEXT("Back or menu"));
	TourNextAction->ActionDescription = FText::FromString(TEXT("Next tour stop"));
	PlacesAction->ActionDescription = FText::FromString(TEXT("Places"));
	PhotoAction->ActionDescription = FText::FromString(TEXT("Postcard"));
	VRSelectAction->ActionDescription = FText::FromString(TEXT("Point and select"));
	VRTurnAction->ActionDescription = FText::FromString(TEXT("Turn"));
	VRScrollAction->ActionDescription = FText::FromString(TEXT("Scroll"));
	VRWheelAction->ActionDescription = FText::FromString(TEXT("Scroll wheel"));

	// The simulation scrolls a card with the mouse wheel (nothing else in the game uses it).
	MappingContext->MapKey(VRWheelAction, EKeys::MouseWheelAxis);

	VRMappingContext = NewObject<UInputMappingContext>(this, FName(TEXT("IMC_WalkTheArchive_VR")));
	VRMappingContext->ContextDescription = FText::FromString(TEXT("Walk the Archive in VR"));
	// Left stick (Vive: trackpad) walks; right stick x turns, y scrolls; right trigger points and selects.
	for (const FKey& Key : { EKeys::OculusTouch_Left_Thumbstick_2D, EKeys::ValveIndex_Left_Thumbstick_2D, EKeys::MixedReality_Left_Thumbstick_2D, EKeys::Vive_Left_Trackpad_2D })
	{
		AddDeadZone(this, VRMappingContext->MapKey(MoveAction, Key));
	}
	for (const FKey& Key : { EKeys::OculusTouch_Right_Thumbstick_X, EKeys::ValveIndex_Right_Thumbstick_X, EKeys::MixedReality_Right_Thumbstick_X, EKeys::Vive_Right_Trackpad_X })
	{
		VRMappingContext->MapKey(VRTurnAction, Key);
	}
	for (const FKey& Key : { EKeys::OculusTouch_Right_Thumbstick_Y, EKeys::ValveIndex_Right_Thumbstick_Y, EKeys::MixedReality_Right_Thumbstick_Y, EKeys::Vive_Right_Trackpad_Y })
	{
		VRMappingContext->MapKey(VRScrollAction, Key);
	}
	for (const FKey& Key : { EKeys::OculusTouch_Right_Trigger_Click, EKeys::ValveIndex_Right_Trigger_Click, EKeys::MixedReality_Right_Trigger_Click, EKeys::Vive_Right_Trigger_Click })
	{
		VRMappingContext->MapKey(VRSelectAction, Key);
	}
	// A: the tour's next stop. B and the left menu button: back (close the card, stand up, the menu).
	for (const FKey& Key : { EKeys::OculusTouch_Right_A_Click, EKeys::ValveIndex_Right_A_Click, EKeys::MixedReality_Right_Trackpad_Click, EKeys::Vive_Right_Trackpad_Click })
	{
		VRMappingContext->MapKey(TourNextAction, Key);
	}
	for (const FKey& Key : { EKeys::OculusTouch_Right_B_Click, EKeys::ValveIndex_Right_B_Click, EKeys::MixedReality_Right_Menu_Click, EKeys::Vive_Right_Menu_Click,
		EKeys::OculusTouch_Left_Menu_Click, EKeys::ValveIndex_Left_B_Click, EKeys::MixedReality_Left_Menu_Click, EKeys::Vive_Left_Menu_Click })
	{
		VRMappingContext->MapKey(BackAction, Key);
	}
	// Left Y (Index: left A) the places list; left X a postcard.
	VRMappingContext->MapKey(PlacesAction, EKeys::OculusTouch_Left_Y_Click);
	VRMappingContext->MapKey(PlacesAction, EKeys::ValveIndex_Left_A_Click);
	VRMappingContext->MapKey(PhotoAction, EKeys::OculusTouch_Left_X_Click);
}

void AWTAPlayerController::CreateWidgets()
{
	if (Hud == nullptr)
	{
		Hud = CreateWidget<UWTAHudWidget>(this, UWTAHudWidget::StaticClass());
		if (Hud != nullptr)
		{
			AddToScreen(Hud, 0);
		}
	}
	if (Panel == nullptr)
	{
		Panel = CreateWidget<UWTAPanelWidget>(this, UWTAPanelWidget::StaticClass());
		if (Panel != nullptr)
		{
			AddToScreen(Panel, 10);
			Panel->Close();
		}
	}
	if (Chat == nullptr)
	{
		Chat = CreateWidget<UWTAChatWidget>(this, UWTAChatWidget::StaticClass());
		if (Chat != nullptr)
		{
			AddToScreen(Chat, 20);
			Chat->Close();
		}
	}
	if (VisitCard == nullptr)
	{
		VisitCard = CreateWidget<UWTAVisitWidget>(this, UWTAVisitWidget::StaticClass());
		if (VisitCard != nullptr)
		{
			AddToScreen(VisitCard, 25);
			VisitCard->Close();
		}
	}
	if (Menu == nullptr)
	{
		Menu = CreateWidget<UWTAMenuWidget>(this, UWTAMenuWidget::StaticClass());
		if (Menu != nullptr)
		{
			AddToScreen(Menu, 30);
			Menu->Close();
		}
	}
}

void AWTAPlayerController::UpdateInputMode()
{
	if (bVRMode)
	{
		// VR: no cursor; the laser is the pointer (and, simulated, the mouse looks even with a card open).
		FInputModeGameOnly Mode;
		Mode.SetConsumeCaptureMouseDown(false);
		SetInputMode(Mode);
		bShowMouseCursor = false;
		if (Interaction != nullptr)
		{
			Interaction->bUseMouseCursor = false;
		}
		if (Hud != nullptr)
		{
			Hud->SetCrosshairVisible(false);
		}
		return;
	}
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
		else if (VisitCard != nullptr && VisitCard->IsOpen())
		{
			Mode.SetWidgetToFocus(VisitCard->TakeWidget());
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

void AWTAPlayerController::OpenHunt()
{
	if (Panel == nullptr)
	{
		return;
	}
	if (Chat != nullptr && Chat->IsOpen())
	{
		Chat->Close();
	}
	Panel->ShowHunt();
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

void AWTAPlayerController::OpenQuiz(FName TalkId)
{
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	if (Panel == nullptr || Content == nullptr || Content->FindTalk(TalkId) == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("OpenQuiz: no talk '%s'"), *TalkId.ToString());
		return;
	}
	if (Chat != nullptr && Chat->IsOpen())
	{
		Chat->Close();
	}
	if (Certificate != nullptr && Certificate->IsOpen())
	{
		Certificate->Close();
	}
	Panel->ShowQuiz(TalkId);
	SetUIMode(true);
}

void AWTAPlayerController::OpenCourse(FName TalkId)
{
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	const FWTATalkRow* Talk = Content ? Content->FindTalk(TalkId) : nullptr;
	if (Panel == nullptr || Talk == nullptr || !Talk->IsCourse())
	{
		UE_LOG(LogWTA, Warning, TEXT("OpenCourse: no course '%s'"), *TalkId.ToString());
		return;
	}
	if (Chat != nullptr && Chat->IsOpen())
	{
		Chat->Close();
	}
	if (Certificate != nullptr && Certificate->IsOpen())
	{
		Certificate->Close();
	}
	Panel->ShowCourse(TalkId);
	SetUIMode(true);
}

FString AWTAPlayerController::CertificateDate()
{
	// The day and the year as plain digits (FText::AsNumber would write 2,026).
	return WTADate(FDateTime::Now()).ToString();
}

void AWTAPlayerController::OpenStoryBooth()
{
	if (Panel == nullptr)
	{
		return;
	}
	if (Chat != nullptr && Chat->IsOpen())
	{
		Chat->Close();
	}
	Panel->ShowBooth();
	SetUIMode(true);
}

void AWTAPlayerController::OpenStories(FName StoryId)
{
	if (Panel == nullptr)
	{
		return;
	}
	if (Chat != nullptr && Chat->IsOpen())
	{
		Chat->Close();
	}
	Panel->ShowStories(StoryId);
	SetUIMode(true);
}

void AWTAPlayerController::ShowCertificate(FName TalkId, const FString& Name)
{
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	const FWTATalkRow* Row = Content != nullptr ? Content->FindTalk(TalkId) : nullptr;
	if (Row == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("ShowCertificate: no talk '%s'"), *TalkId.ToString());
		return;
	}
	if (UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this))
	{
		Progress->NoteCertificate(TalkId, Name);
	}
	if (Panel != nullptr && Panel->IsOpen())
	{
		Panel->Close();
	}
	if (Chat != nullptr && Chat->IsOpen())
	{
		Chat->Close();
	}
	if (Certificate != nullptr)
	{
		Certificate->RemoveFromParent();
		Certificate = nullptr;
	}
	Certificate = CreateWidget<UWTACertificateWidget>(this, UWTACertificateWidget::StaticClass());
	if (Certificate == nullptr)
	{
		return;
	}
	Certificate->Build(*Row, TalkId, Name, CertificateDate(), false);
	AddToScreen(Certificate, 15);
	SetUIMode(true);
	UE_LOG(LogWTA, Log, TEXT("Certificate: '%s' made out to %s"), *Row->Title.ToString(), *Name);
}

bool AWTAPlayerController::CloseTopPanel()
{
	if (Menu != nullptr && Menu->IsOpen())
	{
		Menu->Close();
		SetUIMode(IsAnyPanelOpen());
		return true;
	}
	if (VisitCard != nullptr && VisitCard->IsOpen())
	{
		VisitCard->Close();
		SetUIMode(IsAnyPanelOpen());
		return true;
	}
	if (Certificate != nullptr && Certificate->IsOpen())
	{
		Certificate->Close();
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
		// A visitor following a guide's tour cannot end it: Esc goes on to the menu.
		if (Tour->IsTouring() && !Tour->IsFollowing())
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

void AWTAPlayerController::ToggleVisitCard()
{
	if (VisitCard == nullptr)
	{
		return;
	}
	if (VisitCard->IsOpen())
	{
		VisitCard->Close();
		SetUIMode(IsAnyPanelOpen());
		return;
	}
	if (Menu != nullptr && Menu->IsOpen())
	{
		Menu->Close();
	}
	if (Chat != nullptr && Chat->IsOpen())
	{
		Chat->Close();
	}
	if (Panel != nullptr && Panel->IsOpen())
	{
		Panel->Close();
	}
	VisitCard->Open();
	SetUIMode(true);
}

void AWTAPlayerController::ServerSetVisitName_Implementation(const FString& Name)
{
	if (AWTAPlayerState* Person = GetPlayerState<AWTAPlayerState>())
	{
		Person->SetVisitName(Name);
		UE_LOG(LogWTA, Log, TEXT("WTA_VISIT name slot %d: %s"), Person->Slot, *Person->GetVisitName());
	}
}

void AWTAPlayerController::HandleVisitChanged()
{
	const UWTAVisitSubsystem* Visit = UWTAVisitSubsystem::Get(this);
	if (Hud == nullptr || Visit == nullptr)
	{
		return;
	}
	const EWTAVisitRole VisitRole = Visit->GetRole();
	if (VisitRole == EWTAVisitRole::Solo)
	{
		Hud->SetVisitChip(FText::GetEmpty(), FText::GetEmpty());
	}
	else
	{
		const int32 Visitors = FMath::Max(0, Visit->GetPeople().Num() - 1);
		FText Line;
		if (VisitRole == EWTAVisitRole::Guide)
		{
			Line = Visitors == 0 ? WTAText(TEXT("You lead \u00B7 waiting for visitors"))
				: Visitors == 1 ? WTAText(TEXT("You lead \u00B7 1 visitor"))
				: FText::Format(WTAText(TEXT("You lead \u00B7 {0} visitors")), FText::AsNumber(Visitors));
		}
		else
		{
			Line = FText::Format(WTAText(TEXT("With {0} \u00B7 {1} in the group")), FText::FromString(Visit->GetGuideName()), FText::AsNumber(Visitors + 1));
		}
		Hud->SetVisitChip(WTAText(TEXT("Guided visit \u00B7 V")), Line);
	}
	if (VisitCard != nullptr && VisitCard->IsOpen())
	{
		VisitCard->Refresh();
	}
}

bool AWTAPlayerController::IsAnyPanelOpen() const
{
	return (Panel != nullptr && Panel->IsOpen()) || (Chat != nullptr && Chat->IsOpen()) || (Menu != nullptr && Menu->IsOpen())
		|| (Certificate != nullptr && Certificate->IsOpen()) || (VisitCard != nullptr && VisitCard->IsOpen());
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
	const FText Hint = bVRMode
		? WTAText(TEXT("Pull the trigger to read the full story"))
		: bCursorFree
		? WTAText(TEXT("Click to read the full story"))
		: WTAText(TEXT("Press E to read the full story"));
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
	else if (Action == WTAAction::OpenQuiz())
	{
		OpenQuiz(Arg);
	}
	else if (Action == WTAAction::OpenCourse())
	{
		OpenCourse(Arg);
	}
	else if (Action == WTAAction::OpenHunt())
	{
		OpenHunt();
	}
	else if (Action == WTAAction::StoryBooth())
	{
		OpenStoryBooth();
	}
	else if (Action == WTAAction::OpenStories())
	{
		OpenStories(Arg);
	}
	else if (Action == WTAAction::StartTalk())
	{
		const FWTATalkRow* Talk = Content ? Content->FindTalk(Arg) : nullptr;
		AWTATalkActor* Stage = Talk != nullptr ? AWTATalkActor::FindForVenue(this, Talk->Venue) : nullptr;
		if (Stage != nullptr)
		{
			Stage->Start();
		}
		else
		{
			UE_LOG(LogWTA, Warning, TEXT("RunAction: no talk actor for '%s'"), *Arg.ToString());
		}
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
	if (bVRMode)
	{
		// VR never walks the player (a camera moving on its own is what makes people sick): a short fade instead.
		bHasPendingView = false;
		bFaceTravelDirection = false;
		if (bWalk)
		{
			VRTravel(View);
		}
		else
		{
			PlayerCharacter->TeleportToView(View);
			if (CardScreen != nullptr && CardScreen->IsShown())
			{
				PlaceCardScreen();                     // the open card comes along
			}
		}
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
	if (bCursorFree == bFree || (bVRMode && bFree))
	{
		return;                                    // VR has no cursor: the laser points
	}
	bCursorFree = bFree;
	UpdateInputMode();
	if (bCursorFree && !bUIMode)
	{
		ShowToast(WTAText(TEXT("Cursor free: click the floor to walk, click things to open them. Tab goes back to mouse look.")), 0.f);
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

void AWTAPlayerController::WTAShotList(float SecondsPerShot, const FString& File)
{
	ShotTourViews.Reset();
	ShotTourSeconds = FMath::Max(SecondsPerShot, 1.f);
	TArray<FString> Lines;
	const FString Path = FPaths::ProjectSavedDir() / TEXT("QA") / (File.IsEmpty() ? FString(TEXT("shot_views.txt")) : FPaths::GetCleanFilename(File));
	if (!FFileHelper::LoadFileToStringArray(Lines, *Path))
	{
		UE_LOG(LogWTA, Warning, TEXT("WTA_SHOTTOUR no %s"), *Path);
		return;
	}
	for (const FString& Raw : Lines)
	{
		const FString Line = Raw.TrimStartAndEnd();
		if (Line.IsEmpty() || Line.StartsWith(TEXT("#")))
		{
			continue;
		}
		TArray<FString> Parts;
		Line.ParseIntoArray(Parts, TEXT("|"), true);
		if (Parts.Num() < 3)
		{
			UE_LOG(LogWTA, Warning, TEXT("WTA_SHOTTOUR bad line: %s"), *Line);
			continue;
		}
		TArray<FString> Xyz, Angles;
		Parts[1].TrimStartAndEnd().ParseIntoArrayWS(Xyz);
		Parts[2].TrimStartAndEnd().ParseIntoArrayWS(Angles);
		if (Xyz.Num() < 3 || Angles.Num() < 1)
		{
			UE_LOG(LogWTA, Warning, TEXT("WTA_SHOTTOUR bad line: %s"), *Line);
			continue;
		}
		FWTAView View;
		View.Location = FVector(FCString::Atof(*Xyz[0]), FCString::Atof(*Xyz[1]), FCString::Atof(*Xyz[2]));
		View.Yaw = FCString::Atof(*Angles[0]);
		View.Pitch = Angles.Num() > 1 ? FCString::Atof(*Angles[1]) : 0.f;
		View.bValid = true;
		ShotTourViews.Emplace(Parts[0].TrimStartAndEnd(), View);
	}
	while (CloseTopPanel())
	{
	}
	// No HUD in these pictures, but the rest of the UI layer (a guided visit's name tags over the people) stays.
	bShotTourNoHud = true;
	if (Hud != nullptr)
	{
		Hud->SetVisibility(ESlateVisibility::Collapsed);
	}
	ShotTourIndex = 0;
	UE_LOG(LogWTA, Display, TEXT("WTA_SHOTTOUR start %d views, %.1f s each"), ShotTourViews.Num(), ShotTourSeconds);
	ShotTourTeleport();
}

void AWTAPlayerController::WTAFigures(int32 Count, float X, float Y, float Yaw, int32 Seated)
{
	UWorld* World = GetWorld();
	if (World == nullptr)
	{
		return;
	}
	for (TActorIterator<AWTACharacter> It(World); It; ++It)
	{
		if (It->bStandIn)
		{
			if (APlayerState* State = It->GetPlayerState())
			{
				State->Destroy();
			}
			It->Destroy();
		}
	}
	AWTACharacter* Me = GetWTACharacter();
	if (Count <= 0)
	{
		return;
	}
	if (Me == nullptr)
	{
		if (FiguresTries++ < 40)
		{
			FTimerHandle Retry;
			GetWorldTimerManager().SetTimer(Retry, FTimerDelegate::CreateUObject(this, &AWTAPlayerController::WTAFigures, Count, X, Y, Yaw, Seated), 0.5f, false);
		}
		return;
	}
	FiguresTries = 0;
	FVector Eye;
	FRotator Look;
	GetPlayerViewPoint(Eye, Look);
	FVector Floor;
	float Facing = Yaw;
	if (X < -1.e8f)
	{
		Floor = UWTAVisitSubsystem::FloorUnder(World, Eye + FRotator(0.f, Look.Yaw, 0.f).Vector() * 420.f, Me->EyeHeight);
		Facing = Look.Yaw + 180.f;
	}
	else
	{
		Floor = UWTAVisitSubsystem::FloorUnder(World, FVector(X, Y, Eye.Z), Me->EyeHeight);
	}
	static const TCHAR* Names[] = { TEXT("Ms. Keller"), TEXT("Ana"), TEXT("Ben"), TEXT("Chloe"), TEXT("Diego"), TEXT("Eli"),
		TEXT("Fatima"), TEXT("Grace"), TEXT("Hiro"), TEXT("Isla"), TEXT("Jonah"), TEXT("Kai") };
	int32 Made = 0;
	for (int32 Slot = 0; Slot < Count; ++Slot)
	{
		const FWTAView Spot = UWTAVisitSubsystem::GroupSpot(World, Floor, Facing, 0.f, Slot, Me->EyeHeight);
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		AWTACharacter* Person = World->SpawnActor<AWTACharacter>(AWTACharacter::StaticClass(), Spot.Location, FRotator(0.f, Facing, 0.f), Params);
		AWTAPlayerState* State = World->SpawnActor<AWTAPlayerState>(AWTAPlayerState::StaticClass());
		if (Person == nullptr || State == nullptr)
		{
			continue;
		}
		State->Slot = Slot;
		State->bGuide = Slot == 0;
		State->SetVisitName(Names[Slot % UE_ARRAY_COUNT(Names)]);
		Person->bStandIn = true;
		Person->SetPlayerState(State);
		// They settle onto the floor, as a person does (with no controller the movement mode is only set when this is on
		// before the pawn's components initialise, so set it here too).
		Person->GetCharacterMovement()->bRunPhysicsWithNoController = true;
		Person->GetCharacterMovement()->SetDefaultMovementMode();
		Person->TeleportToView(Spot);
		Person->bSeatedPose = Slot >= Count - Seated;
		++Made;
	}
	UE_LOG(LogWTA, Display, TEXT("WTA_FIGURES %d stand-ins round (%.0f, %.0f, %.0f) facing %.0f, %d seated"), Made, Floor.X, Floor.Y, Floor.Z,
		Facing, FMath::Clamp(Seated, 0, Made));
	// Once they have settled: how far each figure's hem is over the floor under it (look-dev of the layout).
	FTimerHandle Settle;
	GetWorldTimerManager().SetTimer(Settle, FTimerDelegate::CreateWeakLambda(this, [this]()
	{
		UWorld* Here = GetWorld();
		for (TActorIterator<AWTACharacter> It(Here); It; ++It)
		{
			if (!It->bStandIn || It->Figure == nullptr)
			{
				continue;
			}
			const FVector Root = It->Figure->GetComponentLocation();
			FCollisionQueryParams Params(FName(TEXT("WTAFiguresFloor")), false, *It);
			FHitResult Hit;
			const bool bFloor = Here->LineTraceSingleByChannel(Hit, Root + FVector(0.f, 0.f, 50.f), Root - FVector(0.f, 0.f, 200.f), ECC_Visibility, Params);
			const APlayerState* State = It->GetPlayerState();
			UE_LOG(LogWTA, Display, TEXT("WTA_FIGURES %s: the figure's root %.1f cm over the floor (%s), movement mode %d"),
				State ? *State->GetPlayerName() : TEXT("?"), bFloor ? Root.Z - Hit.ImpactPoint.Z : -1.f, bFloor ? *GetNameSafe(Hit.GetActor()) : TEXT("no floor"),
				It->GetCharacterMovement() ? static_cast<int32>(It->GetCharacterMovement()->MovementMode.GetValue()) : -1);
		}
	}), 3.f, false);
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
		if (bShotTourNoHud && Hud != nullptr)
		{
			Hud->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
		}
		bShotTourNoHud = false;
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
	if (bVRMode ? bVRHeadset : (bUIMode || bCursorFree))
	{
		return;                                    // a headset looks with the head; the simulation's mouse aims the laser
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
	if (bVRMode ? bVRHeadset : bUIMode)
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
	if (bVRMode)
	{
		VRSelect(true);                            // the simulation's mouse and E are the trigger
		return;
	}
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
	if (CloseTopPanel())
	{
		return;
	}
	// VR: B stands up from a seat (there is no E or Space at hand), then opens the menu.
	AWTACharacter* Seated = bVRMode ? GetWTACharacter() : nullptr;
	if (Seated != nullptr && Seated->IsSeated())
	{
		Seated->StandUp(true);
		return;
	}
	ToggleMenu();
}

void AWTAPlayerController::OnToggleCursor(const FInputActionValue& Value)
{
	if (bUIMode || bVRMode)
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

void AWTAPlayerController::OnPhoto(const FInputActionValue& Value)
{
	TakePostcard();
}

void AWTAPlayerController::OnVisit(const FInputActionValue& Value)
{
	ToggleVisitCard();
}

void AWTAPlayerController::OnGather(const FInputActionValue& Value)
{
	UWTAVisitSubsystem* Visit = UWTAVisitSubsystem::Get(this);
	if (Visit == nullptr || IsAnyPanelOpen())
	{
		return;
	}
	switch (Visit->GetRole())
	{
	case EWTAVisitRole::Guide:
		Visit->GatherHere();
		break;
	case EWTAVisitRole::Visitor:
		if (!Visit->WalkToGuide())
		{
			ShowToast(WTAText(TEXT("Your guide is not in sight yet.")), 0.f);
		}
		break;
	default:
		break;
	}
}

FString AWTAPlayerController::TakePostcard()
{
	if (IsAnyPanelOpen() || (Postcard != nullptr && Postcard->IsShowing()))
	{
		return FString();
	}
	if (Postcard == nullptr)
	{
		Postcard = CreateWidget<UWTAPostcardWidget>(this, UWTAPostcardWidget::StaticClass());
		if (Postcard == nullptr)
		{
			return FString();
		}
		Postcard->Build();
		Postcard->AddToViewport(40);
	}
	const UWTASettings* Settings = UWTASettings::Get();
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	const UWTARoomSubsystem* Rooms = UWTARoomSubsystem::Get(this);
	const FWTARoomRow* Room = Content != nullptr && Rooms != nullptr ? Content->FindRoom(Rooms->GetCurrentRoom()) : nullptr;
	const FString Campus = Settings != nullptr ? Settings->CampusTitle : TEXT("Walk the Archive");
	const FString Client = Settings != nullptr ? Settings->ClientName : FString();
	const FText Place = Room != nullptr ? Room->DisplayName : FText::FromString(Campus);
	const FText Kicker = Room != nullptr ? Room->Kicker : FText::GetEmpty();

	// Saved/Postcards/<place>_<time>.png: the place as a file name, letters and digits only.
	FString Safe;
	for (const TCHAR C : Place.ToString())
	{
		if (FChar::IsAlnum(C)) { Safe.AppendChar(C); }
		else if ((C == TEXT(' ') || C == TEXT('-')) && !Safe.EndsWith(TEXT("_"))) { Safe.AppendChar(TEXT('_')); }
	}
	Safe = Safe.TrimChar(TEXT('_'));
	if (Safe.IsEmpty())
	{
		Safe = TEXT("postcard");
	}
	const FString File = FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Postcards"),
		FString::Printf(TEXT("%s_%s.png"), *Safe, *FDateTime::Now().ToString(TEXT("%Y%m%d-%H%M%S")))));
	IFileManager::Get().MakeDirectory(*FPaths::GetPath(File), true);

	Postcard->Show(Place, Kicker, CertificateDate(), Client, Campus);
	if (Hud != nullptr)
	{
		Hud->SetVisibility(ESlateVisibility::Collapsed);
	}
	if (UWTAVRRig* Rig = GetVRRig())
	{
		Rig->SetVisualsHidden(true);               // the hands and the laser stay out of the picture
	}
	FScreenshotRequest::RequestScreenshot(File, true, false);
	LastPostcard = File;
	UE_LOG(LogWTA, Display, TEXT("WTA postcard %s"), *File);
	GetWorldTimerManager().SetTimer(PostcardTimer, this, &AWTAPlayerController::FinishPostcard, 0.35f, false);
	return File;
}

void AWTAPlayerController::FinishPostcard()
{
	if (Postcard != nullptr)
	{
		Postcard->Hide();
	}
	if (Hud != nullptr)
	{
		Hud->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
	}
	if (UWTAVRRig* Rig = GetVRRig())
	{
		Rig->SetVisualsHidden(false);
	}
	ShowToast(FText::Format(WTAText(TEXT("Postcard saved to {0}")), FText::FromString(LastPostcard)), 6.f);
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
	ShowToast(FText::Format(WTAText(TEXT("Badge unlocked: {0}")), FText::FromString(Name)), 3.6f);
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
	const FText Message = (Total > 0 && Found >= Total)
		? FText::Format(WTAText(TEXT("You found all {0} XR tokens! Your library card is full: show it at the desk.")), Total)
		: FText::Format(WTAText(TEXT("XR token found! {0} of {1} stamped on your library card.")), Found, Total);
	ShowToast(Message, 0.f);
}

void AWTAPlayerController::HandleTourChanged(int32 Index)
{
	// A tour frees the cursor so its bar's Back / Next / End buttons can be clicked (T and Esc work too);
	// mouse look comes back when it ends, unless the player toggled the cursor with Tab in between.
	const bool bTouring = Index >= 0;
	UWTATourSubsystem* Tour = UWTATourSubsystem::Get(this);
	const bool bFollowing = Tour != nullptr && Tour->IsFollowing();
	const UWTAVisitSubsystem* Visit = UWTAVisitSubsystem::Get(this);
	const FText GuideName = Visit != nullptr ? FText::FromString(Visit->GetGuideName()) : FText::GetEmpty();
	if (bTouring && !bTourActive && bFollowing)
	{
		// A visitor's tour follows the guide: no buttons to click, so the mouse keeps looking around.
		ShowToast(FText::Format(WTAText(TEXT("{0} is starting the tour. You walk to each stop with the group.")), GuideName), 0.f);
	}
	else if (bTouring && !bTourActive && bVRMode)
	{
		// VR: the tour bar's buttons are pressed with the laser; nothing to free.
		ShowToast(WTAText(TEXT("Tour: press A or point at Next. B ends the tour.")), 0.f);
	}
	else if (bTouring && !bTourActive)
	{
		if (!bCursorFree)
		{
			bCursorFree = true;
			bCursorFreedForTour = true;
			UpdateInputMode();
		}
		ShowToast(WTAText(TEXT("Tour: click Next or press T. Tab looks around, Esc ends the tour.")), 0.f);
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
	FWTATourStopRow Stop;
	if (Index < 0 || Tour == nullptr || !Tour->GetCurrentStop(Stop))
	{
		Hud->HideTour();
		return;
	}
	Hud->SetTourFollowing(bFollowing, GuideName);
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
	ShowToast(WTAText(TEXT("Progress reset. The tokens are back in their hiding places.")), 0.f);
}

// --- VR ----------------------------------------------------------------------------------------

UWTAVRRig* AWTAPlayerController::GetVRRig() const
{
	const AWTACharacter* Me = GetWTACharacter();
	return Me != nullptr ? Me->GetVRRig() : nullptr;
}

bool AWTAPlayerController::CanEnterVR() const
{
	return bVRMode || WTAXR::IsHeadsetConnected() || WTAXR::IsSimulationRequested();
}

void AWTAPlayerController::AddToScreen(UUserWidget* Widget, int32 ZOrder)
{
	if (Widget == nullptr)
	{
		return;
	}
	// The postcard's frame (z 40) stays on the viewport: it is part of the picture taken of it.
	UWTAVRRootWidget* Root = (!bVRMode || ZOrder >= 40) ? nullptr : (ZOrder == 0 ? HudRoot.Get() : CardRoot.Get());
	if (Root != nullptr)
	{
		Root->AddLayer(Widget, ZOrder);
		ShowScrim(Widget, false);
		return;
	}
	Widget->RemoveFromParent();
	Widget->AddToViewport(ZOrder);
	ShowScrim(Widget, true);
}

void AWTAPlayerController::MoveWidgetsToScreens(bool bVR)
{
	UUserWidget* Widgets[] = { Hud.Get(), Panel.Get(), Certificate.Get(), Chat.Get(), VisitCard.Get(), Menu.Get() };
	const int32 Orders[] = { 0, 10, 15, 20, 25, 30 };
	for (int32 i = 0; i < 6; ++i)
	{
		if (Widgets[i] != nullptr)
		{
			AddToScreen(Widgets[i], Orders[i]);
		}
	}
	UE_LOG(LogWTA, Log, TEXT("WTA_VR widgets on the %s"), bVR ? TEXT("VR screens") : TEXT("viewport"));
}

bool AWTAPlayerController::EnterVR(bool bSimulate)
{
	AWTACharacter* Me = GetWTACharacter();
	UWorld* World = GetWorld();
	if (!IsLocalController() || Me == nullptr || World == nullptr)
	{
		return false;
	}
	if (bVRMode)
	{
		if (bVRHeadset == !bSimulate)
		{
			return true;
		}
		ExitVR();
	}
	CreateInputObjects();
	bool bHeadset = false;
	if (!bSimulate)
	{
		const bool bRunning = WTAXR::IsHeadsetEnabled();
		bHeadset = bRunning || WTAXR::BeginSession(VRMappingContext);
		if (!bHeadset)
		{
			ShowToast(WTAText(TEXT("No headset is running. Start Meta Quest Link or SteamVR, put the headset on, then choose Enter VR again.")), 7.f);
			UE_LOG(LogWTA, Warning, TEXT("WTA_VR no headset to go into (%s)"), *WTAXR::HeadsetName());
			return false;
		}
		if (bRunning && !WTAXR::HasGameBindings())
		{
			UE_LOG(LogWTA, Warning, TEXT("WTA_VR the headset started before the game (the engine's -vr), so the controllers have no bindings: start with -headset instead"));
		}
		WTAXR::UseFloorTracking();
	}
	bVRMode = true;
	bVRHeadset = bHeadset;
	WTAXR::SetPresentationActive(true);
	bCursorFree = false;
	bCursorFreedForTour = false;
	bTurnLatched = false;
	bHasPendingView = false;
	bFaceTravelDirection = false;
	if (ULocalPlayer* LocalPlayer = GetLocalPlayer())
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem = LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
		{
			Subsystem->AddMappingContext(VRMappingContext, 1);
		}
	}

	// The two screens, and the widgets onto them.
	FActorSpawnParameters Params;
	Params.Owner = this;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	CardRoot = CreateWidget<UWTAVRRootWidget>(this, UWTAVRRootWidget::StaticClass());
	HudRoot = CreateWidget<UWTAVRRootWidget>(this, UWTAVRRootWidget::StaticClass());
	CardScreen = World->SpawnActor<AWTAVRScreenActor>(AWTAVRScreenActor::StaticClass(), FTransform::Identity, Params);
	HudScreen = World->SpawnActor<AWTAVRScreenActor>(AWTAVRScreenActor::StaticClass(), FTransform::Identity, Params);
	if (CardScreen != nullptr)
	{
		CardScreen->Init(CardRoot, VRCardPixels, VRCardWidth);
	}
	if (HudScreen != nullptr)
	{
		HudScreen->Init(HudRoot, VRHudPixels, VRHudWidth);
	}
	MoveWidgetsToScreens(true);
	if (Hud != nullptr)
	{
		Hud->SetVRMode(true);
		Hud->SetHoverLabel(FText::GetEmpty());
	}
	Me->StartVR(bHeadset);
	if (Menu != nullptr)
	{
		Menu->RefreshVR();
	}
	if (!ShownStoryId.IsNone())
	{
		ShowStoryPlaque(ShownStoryId);              // the plaque's hint names the trigger now
	}
	UpdateInputMode();
	SetUIMode(IsAnyPanelOpen());
	ShowToast(WTAText(TEXT("VR: the left stick walks, the right stick turns, the trigger opens what the laser is on or steps where it points. B goes back.")), 7.f);
	UE_LOG(LogWTA, Display, TEXT("WTA_VR on: %s (%s)"), bHeadset ? TEXT("headset") : TEXT("desktop simulation"), *WTAXR::HeadsetName());
	return true;
}

void AWTAPlayerController::ExitVR()
{
	if (!bVRMode)
	{
		return;
	}
	if (bVRPressedScreen)
	{
		VRSelect(false);
	}
	if (AWTACharacter* Me = GetWTACharacter())
	{
		Me->StopVR();
	}
	bVRMode = false;
	WTAXR::SetPresentationActive(false);
	MoveWidgetsToScreens(false);
	for (AWTAVRScreenActor* Screen : { CardScreen.Get(), HudScreen.Get() })
	{
		if (Screen != nullptr)
		{
			Screen->Destroy();
		}
	}
	CardScreen = nullptr;
	HudScreen = nullptr;
	CardRoot = nullptr;
	HudRoot = nullptr;
	if (ULocalPlayer* LocalPlayer = GetLocalPlayer())
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem = LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
		{
			Subsystem->RemoveMappingContext(VRMappingContext);
		}
	}
	if (Interaction != nullptr)
	{
		Interaction->SetRayOverride(false);
	}
	bVRPointerOnScreen = false;
	bVRWorldHit = false;
	GetWorldTimerManager().ClearTimer(VRFadeTimer);
	if (PlayerCameraManager != nullptr)
	{
		PlayerCameraManager->StopCameraFade();
	}
	if (Hud != nullptr)
	{
		Hud->SetVRMode(false);
	}
	if (bVRHeadset)
	{
		WTAXR::EnableHeadset(false);
	}
	bVRHeadset = false;
	if (Menu != nullptr)
	{
		Menu->RefreshVR();
	}
	if (!ShownStoryId.IsNone())
	{
		ShowStoryPlaque(ShownStoryId);
	}
	UpdateInputMode();
	SetUIMode(IsAnyPanelOpen());
	UE_LOG(LogWTA, Display, TEXT("WTA_VR off"));
}

void AWTAPlayerController::ToggleVR()
{
	if (bVRMode)
	{
		ExitVR();
		return;
	}
	EnterVR(!WTAXR::IsHeadsetConnected() && WTAXR::IsSimulationRequested());
}

void AWTAPlayerController::WTAVR(const FString& Mode)
{
	const FString Word = Mode.TrimStartAndEnd().ToLower();
	if (Word == TEXT("off"))
	{
		ExitVR();
	}
	else if (Word == TEXT("sim"))
	{
		EnterVR(true);
	}
	else if (Word == TEXT("on") || Word == TEXT("headset"))
	{
		EnterVR(false);
	}
	else if (bVRMode)
	{
		ExitVR();
	}
	else
	{
		EnterVR(!WTAXR::IsHeadsetConnected());
	}
}

void AWTAPlayerController::StartVRWhenReady()
{
	if (bVRMode || !IsLocalController())
	{
		return;
	}
	if (GetWTACharacter() == nullptr)
	{
		if (VRStartTries++ < 40)
		{
			GetWorldTimerManager().SetTimer(VRStartTimer, this, &AWTAPlayerController::StartVRWhenReady, 0.25f, false);
		}
		return;
	}
	const bool bHeadset = WTAXR::IsHeadsetEnabled() || WTAXR::IsHeadsetRequested();
	if (bHeadset && EnterVR(false))
	{
		return;
	}
	if (WTAXR::IsSimulationRequested())
	{
		EnterVR(true);
	}
}

void AWTAPlayerController::UpdateVRScreens(float DeltaSeconds)
{
	const UWTAVRRig* Rig = GetVRRig();
	FVector Eye;
	float HeadYaw = 0.f;
	if (Rig != nullptr)
	{
		Eye = Rig->GetEyeLocation();
		HeadYaw = Rig->GetHeadYaw();
	}
	else
	{
		FRotator Look;
		GetPlayerViewPoint(Eye, Look);
		HeadYaw = static_cast<float>(Look.Yaw);
	}
	const bool bCards = IsAnyPanelOpen();
	if (CardScreen != nullptr)
	{
		if (bCards && !CardScreen->IsShown())
		{
			// A card appears square in front of the head at reading distance and stays put while cards are open.
			PlaceCardScreen();
			CardScreen->SetShown(true);
		}
		else if (!bCards && CardScreen->IsShown())
		{
			CardScreen->SetShown(false);
		}
	}
	if (HudScreen != nullptr)
	{
		if (!bCards && !HudScreen->IsShown())
		{
			HudYaw = HeadYaw;
			bHudTurning = false;
			HudScreen->SetShown(true);
		}
		else if (bCards && HudScreen->IsShown())
		{
			HudScreen->SetShown(false);                     // a card takes the view; the HUD comes back after
		}
		if (HudScreen->IsShown())
		{
			// Ahead and a little low, going where the head goes; it turns after the head once the head is 35 degrees
			// away, and settles in front of it again.
			const float Off = FMath::FindDeltaAngleDegrees(HudYaw, HeadYaw);
			if (FMath::Abs(Off) > 35.f)
			{
				bHudTurning = true;
			}
			if (bHudTurning)
			{
				HudYaw += Off * (1.f - FMath::Exp(-4.f * DeltaSeconds));
				if (FMath::Abs(FMath::FindDeltaAngleDegrees(HudYaw, HeadYaw)) < 2.f)
				{
					bHudTurning = false;
				}
			}
			// Nearer, and smaller by as much, when a wall is in the way: it looks the same and never goes into the wall.
			const float Distance = VRClearDistance(Eye, HudYaw, VRHudDistance, VRHudDrop, VRHudWidth);
			const float Shrink = Distance / VRHudDistance;
			HudScreen->SetSizeScale(Shrink);
			HudScreen->PlaceFacing(Eye, HudYaw, Distance, VRHudDrop * Shrink);
		}
	}
}

void AWTAPlayerController::UpdateVRPointer()
{
	AWTACharacter* Me = GetWTACharacter();
	UWTAVRRig* Rig = Me != nullptr ? Me->GetVRRig() : nullptr;
	UWorld* World = GetWorld();
	if (Rig == nullptr || World == nullptr)
	{
		return;
	}
	FCollisionQueryParams Params(FName(TEXT("WTAVRLaser")), false, Me);
	AWTAVRScreenActor* Screens[] = { CardScreen.Get(), HudScreen.Get() };
	// What a screen does with a ray: the card screen takes it anywhere on its face, the HUD screen only on a button.
	auto TraceScreens = [this, &Screens](const FVector& From, const FVector& Along, float& Reach, AWTAVRScreenActor*& OutScreen, FVector2D& OutPixel)
	{
		for (AWTAVRScreenActor* Screen : Screens)
		{
			float Distance = 0.f;
			FVector2D Pixel;
			if (Screen != nullptr && Screen->Trace(From, Along, Reach, Distance, Pixel) && (Screen == CardScreen || Screen->IsInteractiveAt(Pixel)))
			{
				Reach = Distance;
				OutScreen = Screen;
				OutPixel = Pixel;
			}
		}
	};
	// The screens draw over everything (no depth test), so a screen in the laser's way wins over the world, however
	// near a wall is.
	if (!bVRHeadset)
	{
		// The simulation: the right hand aims at what the middle of the view is on (a screen first).
		const FVector Eye = Me->GetEyeLocation();
		const FVector Look = GetControlRotation().Vector();
		float Reach = VRLaserReach;
		AWTAVRScreenActor* Seen = nullptr;
		FVector2D SeenPixel;
		TraceScreens(Eye, Look, Reach, Seen, SeenPixel);
		FHitResult EyeHit;
		if (Seen == nullptr && World->LineTraceSingleByChannel(EyeHit, Eye, Eye + Look * VRLaserReach, ECC_Visibility, Params))
		{
			Reach = EyeHit.Distance;
		}
		Rig->SetSimAimTarget(Eye + Look * Reach);
	}
	FVector Start;
	FVector Direction;
	Rig->GetAimRay(Start, Direction);
	float Reach = VRLaserReach;
	AWTAVRScreenActor* OnScreen = nullptr;
	FVector2D Pixel = FVector2D::ZeroVector;
	TraceScreens(Start, Direction, Reach, OnScreen, Pixel);
	bVRPointerOnScreen = OnScreen != nullptr;
	FHitResult WorldHit;
	bVRWorldHit = OnScreen == nullptr && World->LineTraceSingleByChannel(WorldHit, Start, Start + Direction * VRLaserReach, ECC_Visibility, Params);
	VRWorldHit = bVRWorldHit ? WorldHit : FHitResult();

	// The screens' pointer gets a hit on a screen, or none (its line still set, so it knows where it points).
	FHitResult PointerHit;
	PointerHit.TraceStart = Start;
	PointerHit.TraceEnd = Start + Direction * VRLaserReach;
	if (OnScreen != nullptr)
	{
		PointerHit.bBlockingHit = true;
		PointerHit.Distance = Reach;
		PointerHit.Location = Start + Direction * Reach;
		PointerHit.ImpactPoint = PointerHit.Location;
		PointerHit.Normal = OnScreen->GetActorForwardVector();
		PointerHit.ImpactNormal = PointerHit.Normal;
		PointerHit.Component = OnScreen->Screen.Get();
		PointerHit.HitObjectHandle = FActorInstanceHandle(OnScreen);
	}
	if (UWidgetInteractionComponent* Pointer = Rig->GetPointer())
	{
		Pointer->SetCustomHitResult(PointerHit);
	}
	// The world under the laser, unless a screen is in the way.
	if (Interaction != nullptr)
	{
		Interaction->SetRayOverride(true, Start, Direction, OnScreen != nullptr);
	}
	const bool bOnButton = OnScreen != nullptr && OnScreen->IsInteractiveAt(Pixel);
	const bool bOnThing = OnScreen == nullptr && Interaction != nullptr && Interaction->HasHover();
	const FVector End = OnScreen != nullptr ? FVector(PointerHit.ImpactPoint)
		: (bVRWorldHit ? FVector(WorldHit.ImpactPoint) : Start + Direction * VRLaserReach);
	Rig->SetLaser(End, OnScreen != nullptr || bVRWorldHit, bOnButton || bOnThing);
	Rig->SetLabel(bOnThing ? Interaction->HoverLabel : FText::GetEmpty());
}

void AWTAPlayerController::VRSelect(bool bPressed)
{
	UWTAVRRig* Rig = GetVRRig();
	UWidgetInteractionComponent* Pointer = Rig != nullptr ? Rig->GetPointer() : nullptr;
	if (!bPressed)
	{
		if (bVRPressedScreen && Pointer != nullptr)
		{
			Pointer->ReleasePointerKey(EKeys::LeftMouseButton);
		}
		bVRPressedScreen = false;
		return;
	}
	if (Rig == nullptr)
	{
		return;
	}
	// A button (or anywhere on a card's screen): the press goes there, and its release after it.
	if (bVRPointerOnScreen && Pointer != nullptr)
	{
		Pointer->PressPointerKey(EKeys::LeftMouseButton);
		bVRPressedScreen = true;
		return;
	}
	// Away from an open card: as a click outside it.
	if (IsAnyPanelOpen())
	{
		CloseTopPanel();
		return;
	}
	if (Interaction != nullptr && Interaction->TryInteract())
	{
		return;
	}
	// The floor: a step there.
	if (bVRWorldHit && VRWorldHit.ImpactNormal.Z > 0.7f)
	{
		VRStepToFloor(VRWorldHit.ImpactPoint);
		return;
	}
	// In a wax scene with nothing else under the laser: the scene's story, as E does.
	if (!StageStoryId.IsNone())
	{
		OpenExhibit(StageStoryId);
	}
}

void AWTAPlayerController::VRStepToFloor(const FVector& Point)
{
	AWTACharacter* Me = GetWTACharacter();
	UWTAVRRig* Rig = Me != nullptr ? Me->GetVRRig() : nullptr;
	if (Rig == nullptr || FVector::Dist2D(Rig->GetEyeLocation(), Point) > VRStepReach)
	{
		return;                                        // too far for one step
	}
	FVector Floor = Point;
	if (UNavigationSystemV1* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld()))
	{
		FNavLocation Projected;
		if (!Nav->ProjectPointToNavigation(Point, Projected, FVector(40.f, 40.f, 100.f)))
		{
			return;                                    // nowhere a person stands (a table top, a ledge)
		}
		Floor = Projected.Location;
	}
	const FRotator Head = Rig->GetHeadRotation();
	FWTAView View;
	View.Location = Floor + FVector(0.f, 0.f, Me->EyeHeight);
	View.Yaw = static_cast<float>(Head.Yaw);
	View.Pitch = static_cast<float>(Head.Pitch);
	View.bValid = true;
	UE_LOG(LogWTA, Log, TEXT("WTA_VR step to %s"), *Floor.ToCompactString());
	VRTravel(View);
}

void AWTAPlayerController::VRTravel(const FWTAView& View)
{
	// A tenth of a second to black, the move, then back in a fifth: quick enough to keep the place in mind.
	if (PlayerCameraManager != nullptr)
	{
		PlayerCameraManager->StartCameraFade(0.f, 1.f, 0.1f, FLinearColor::Black, false, true);
	}
	GetWorldTimerManager().SetTimer(VRFadeTimer, FTimerDelegate::CreateWeakLambda(this, [this, View]()
	{
		if (AWTACharacter* Me = GetWTACharacter())
		{
			Me->TeleportToView(View);
		}
		// An open card comes along (an exhibit's card opens as the player goes to its view spot).
		if (CardScreen != nullptr && CardScreen->IsShown())
		{
			PlaceCardScreen();
		}
		if (PlayerCameraManager != nullptr)
		{
			PlayerCameraManager->StartCameraFade(1.f, 0.f, 0.18f, FLinearColor::Black, false, false);
		}
	}), 0.1f, false);
}

void AWTAPlayerController::PlaceCardScreen()
{
	if (CardScreen == nullptr)
	{
		return;
	}
	const UWTAVRRig* Rig = GetVRRig();
	FVector Eye;
	float HeadYaw = 0.f;
	if (Rig != nullptr)
	{
		Eye = Rig->GetEyeLocation();
		HeadYaw = Rig->GetHeadYaw();
	}
	else
	{
		FRotator Look;
		GetPlayerViewPoint(Eye, Look);
		HeadYaw = static_cast<float>(Look.Yaw);
	}
	const float Distance = VRClearDistance(Eye, HeadYaw, VRCardDistance, VRCardDrop, VRCardWidth);
	const float Shrink = Distance / VRCardDistance;
	CardScreen->SetSizeScale(Shrink);
	CardScreen->PlaceFacing(Eye, HeadYaw, Distance, VRCardDrop * Shrink);
}

float AWTAPlayerController::VRClearDistance(const FVector& Eye, float Yaw, float Distance, float Drop, float WidthCm) const
{
	UWorld* World = GetWorld();
	if (World == nullptr)
	{
		return Distance;
	}
	// Three rays from the eye to the screen's middle and its two sides: the nearest wall along the way, less a hand.
	FCollisionQueryParams Params(FName(TEXT("WTAVRScreenRoom")), false, GetPawn());
	const FVector Forward = FRotator(0.f, Yaw, 0.f).Vector();
	const FVector Right = FRotator(0.f, Yaw + 90.f, 0.f).Vector();
	float Clear = Distance;
	for (const float Side : { 0.f, -0.5f, 0.5f })
	{
		const FVector Target = Eye + Forward * Distance + Right * (Side * WidthCm) - FVector(0.f, 0.f, Drop);
		FHitResult Hit;
		if (World->LineTraceSingleByChannel(Hit, Eye, Target, ECC_Visibility, Params))
		{
			Clear = FMath::Min(Clear, static_cast<float>(FVector::DotProduct(Hit.ImpactPoint - Eye, Forward)) - 8.f);
		}
	}
	return FMath::Clamp(Clear, 45.f, Distance);
}

void AWTAPlayerController::OnInteractEnd(const FInputActionValue& Value)
{
	if (bVRMode)
	{
		VRSelect(false);
	}
}

void AWTAPlayerController::OnVRSelect(const FInputActionValue& Value)
{
	if (bVRMode)
	{
		VRSelect(true);
	}
}

void AWTAPlayerController::OnVRSelectEnd(const FInputActionValue& Value)
{
	if (bVRMode)
	{
		VRSelect(false);
	}
}

void AWTAPlayerController::OnVRTurn(const FInputActionValue& Value)
{
	if (!bVRMode || bUIMode)
	{
		return;
	}
	// One 30 degree turn per push of the stick; it turns again once the stick has come back to the middle.
	const float X = Value.Get<float>();
	if (!bTurnLatched && FMath::Abs(X) > 0.7f)
	{
		bTurnLatched = true;
		if (UWTAVRRig* Rig = GetVRRig())
		{
			Rig->SnapTurn(X > 0.f ? 30.f : -30.f);
		}
	}
	else if (bTurnLatched && FMath::Abs(X) < 0.3f)
	{
		bTurnLatched = false;
	}
}

void AWTAPlayerController::OnVRTurnEnd(const FInputActionValue& Value)
{
	bTurnLatched = false;
}

void AWTAPlayerController::OnVRScroll(const FInputActionValue& Value)
{
	UWTAVRRig* Rig = bVRMode && bVRPointerOnScreen ? GetVRRig() : nullptr;
	UWidgetInteractionComponent* Pointer = Rig != nullptr ? Rig->GetPointer() : nullptr;
	const float Y = Value.Get<float>();
	if (Pointer != nullptr && FMath::Abs(Y) > 0.2f)
	{
		// Up scrolls up, as a wheel does: about ten notches a second at full tilt.
		const float DeltaSeconds = GetWorld() != nullptr ? GetWorld()->GetDeltaSeconds() : 0.016f;
		Pointer->ScrollWheel(Y * DeltaSeconds * 10.f);
	}
}

void AWTAPlayerController::OnVRWheel(const FInputActionValue& Value)
{
	UWTAVRRig* Rig = bVRMode && bVRPointerOnScreen ? GetVRRig() : nullptr;
	if (UWidgetInteractionComponent* Pointer = Rig != nullptr ? Rig->GetPointer() : nullptr)
	{
		Pointer->ScrollWheel(Value.Get<float>());
	}
}
