// Walk the Archive - the body in VR (see XR/WTAVRRig.h).

#include "XR/WTAVRRig.h"
#include "Core/WTACharacter.h"
#include "Core/WTALog.h"
#include "UI/WTAUIStyle.h"
#include "UI/WTAVRRootWidget.h"
#include "XR/WTAVRScreenActor.h"
#include "XR/WTAXR.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/WidgetComponent.h"
#include "Components/WidgetInteractionComponent.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Controller.h"
#include "GameFramework/PlayerController.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/SoftObjectPath.h"

namespace
{
	/** The laser starts this far ahead of the hand's origin: the wand's tip. */
	constexpr float TipCm = 2.5f;
	/** The longest the laser reaches (the interaction trace's 15 m and a little). */
	constexpr float LaserMaxCm = 2000.f;
	/** The simulation's hands, in front of the camera: low right and low left, inside a 66 degree view. */
	const FVector SimRightHand(40.f, 16.f, -13.f);
	const FVector SimLeftHand(40.f, -18.f, -14.f);

	/** The gap the walking movement keeps under the capsule (between MIN_FLOOR_DIST and MAX_FLOOR_DIST). */
	float FloorGap()
	{
		return 0.5f * (UCharacterMovementComponent::MIN_FLOOR_DIST + UCharacterMovementComponent::MAX_FLOOR_DIST);
	}

	template <typename T>
	T* LoadByPath(const TCHAR* Path)
	{
		return Cast<T>(FSoftObjectPath(Path).TryLoad());
	}
}

UWTAVRRig::UWTAVRRig()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
}

AWTACharacter* UWTAVRRig::Body() const
{
	return Cast<AWTACharacter>(GetOwner());
}

FName UWTAVRRig::UniqueName(const TCHAR* Base, const UClass* Class) const
{
	// Going into VR again makes the parts again while the last ones may still be waiting for the garbage collector.
	return MakeUniqueObjectName(GetOwner(), Class, FName(Base));
}

float UWTAVRRig::StandingOriginZ() const
{
	const AWTACharacter* Me = Body();
	const float Half = Me != nullptr ? Me->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() : 90.f;
	return -Half - FloorGap();
}

UStaticMeshComponent* UWTAVRRig::MakePart(const TCHAR* Name, UStaticMesh* Mesh, USceneComponent* Parent, UMaterialInterface* Look)
{
	UStaticMeshComponent* Part = NewObject<UStaticMeshComponent>(GetOwner(), UniqueName(Name, UStaticMeshComponent::StaticClass()));
	Part->SetStaticMesh(Mesh);
	if (Look != nullptr)
	{
		Part->SetMaterial(0, Look);
	}
	Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Part->SetGenerateOverlapEvents(false);
	Part->SetCanEverAffectNavigation(false);
	Part->SetCastShadow(false);
	Part->SetupAttachment(Parent);
	Part->RegisterComponent();
	return Part;
}

void UWTAVRRig::MakeWand(USceneComponent* Hand, TObjectPtr<UStaticMeshComponent>& OutHandle, TObjectPtr<UStaticMeshComponent>& OutRing)
{
	if (Hand == nullptr)
	{
		return;
	}
	UStaticMesh* Cylinder = LoadByPath<UStaticMesh>(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	// A slim handle held in the fist, 13 cm long and 3 cm across, its brass ring at the front where the laser leaves.
	// The basic cylinder stands along its Z: pitch -90 lays it along the hand's +X.
	const FString Side = Hand == LeftHand ? TEXT("Left") : TEXT("Right");
	OutHandle = MakePart(*(TEXT("WTAVR") + Side + TEXT("Handle")), Cylinder, Hand, HandleLook);
	OutHandle->SetRelativeLocationAndRotation(FVector(-4.5f, 0.f, 0.f), FRotator(-90.f, 0.f, 0.f));
	OutHandle->SetRelativeScale3D(FVector(0.03f, 0.03f, 0.13f));
	OutRing = MakePart(*(TEXT("WTAVR") + Side + TEXT("Ring")), Cylinder, Hand, RingLook);
	OutRing->SetRelativeLocationAndRotation(FVector(1.6f, 0.f, 0.f), FRotator(-90.f, 0.f, 0.f));
	OutRing->SetRelativeScale3D(FVector(0.034f, 0.034f, 0.008f));
}

void UWTAVRRig::Start(bool bInHeadset)
{
	AWTACharacter* Me = Body();
	if (bStarted || Me == nullptr || Me->Camera == nullptr)
	{
		return;
	}
	bStarted = true;
	bHeadset = bInHeadset;
	UCameraComponent* Camera = Me->Camera;

	// The looks: a dark lacquered handle and a brass ring (the figure's material, else the engine's basic one), the laser
	// display-referred like the campus's other self-lit things and drawn over the VR screens (M_WTA_Overlay: the screens'
	// after-motion-blur pass has no depth test, so an opaque laser would vanish behind a card it points at; else
	// M_WTA_Unlit, else lit).
	UMaterialInterface* Lit = LoadByPath<UMaterialInterface>(TEXT("/Game/WTA/Materials/M_WTA_Figure.M_WTA_Figure"));
	if (Lit == nullptr)
	{
		Lit = LoadByPath<UMaterialInterface>(TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	}
	UMaterialInterface* Glow = LoadByPath<UMaterialInterface>(TEXT("/Game/WTA/Materials/M_WTA_Overlay.M_WTA_Overlay"));
	if (Glow == nullptr)
	{
		Glow = LoadByPath<UMaterialInterface>(TEXT("/Game/WTA/Materials/M_WTA_Unlit.M_WTA_Unlit"));
	}
	if (Lit != nullptr)
	{
		HandleLook = UMaterialInstanceDynamic::Create(Lit, this);
		HandleLook->SetVectorParameterValue(TEXT("Color"), WTAStyle::FromHex(0x1b2622));
		HandleLook->SetScalarParameterValue(TEXT("Roughness"), 0.38f);
		HandleLook->SetScalarParameterValue(TEXT("Sheen"), 0.2f);
		RingLook = UMaterialInstanceDynamic::Create(Lit, this);
		RingLook->SetVectorParameterValue(TEXT("Color"), WTAStyle::Brass());
		RingLook->SetScalarParameterValue(TEXT("Roughness"), 0.3f);
		RingLook->SetScalarParameterValue(TEXT("Sheen"), 0.1f);
	}
	if (Glow != nullptr || Lit != nullptr)
	{
		BeamLook = UMaterialInstanceDynamic::Create(Glow != nullptr ? Glow : Lit, this);
	}

	if (bHeadset)
	{
		// The head and hands on the floor under the capsule, in the headset's floor-level tracking space.
		Origin = NewObject<USceneComponent>(Me, UniqueName(TEXT("WTAVROrigin"), USceneComponent::StaticClass()));
		Origin->SetupAttachment(Me->GetCapsuleComponent());
		Origin->SetRelativeLocation(FVector(0.f, 0.f, StandingOriginZ()));
		Origin->RegisterComponent();
		Camera->AttachToComponent(Origin, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
		Camera->SetRelativeTransform(FTransform::Identity);
		Camera->bUsePawnControlRotation = false;
		Camera->bLockToHmd = true;
		Me->bUseControllerRotationYaw = false;
		LeftHand = WTAXR::MakeMotionController(Me, UniqueName(TEXT("WTAVRLeftHand"), USceneComponent::StaticClass()), TEXT("LeftGrip"));
		RightHand = WTAXR::MakeMotionController(Me, UniqueName(TEXT("WTAVRRightHand"), USceneComponent::StaticClass()), TEXT("RightAim"));
		for (USceneComponent* Hand : { LeftHand.Get(), RightHand.Get() })
		{
			if (Hand != nullptr)
			{
				Hand->SetupAttachment(Origin);
				Hand->RegisterComponent();
			}
		}
	}
	if (LeftHand == nullptr || RightHand == nullptr)
	{
		// The simulation (or no motion controllers): the hands ride low in front of the camera.
		for (USceneComponent* Tracked : { LeftHand.Get(), RightHand.Get() })
		{
			if (Tracked != nullptr)
			{
				Tracked->DestroyComponent();
			}
		}
		LeftHand = NewObject<USceneComponent>(Me, UniqueName(TEXT("WTAVRLeftHand"), USceneComponent::StaticClass()));
		LeftHand->SetupAttachment(Camera);
		LeftHand->SetRelativeLocationAndRotation(SimLeftHand, FRotator(8.f, 14.f, 0.f));
		LeftHand->RegisterComponent();
		RightHand = NewObject<USceneComponent>(Me, UniqueName(TEXT("WTAVRRightHand"), USceneComponent::StaticClass()));
		RightHand->SetupAttachment(Camera);
		RightHand->SetRelativeLocationAndRotation(SimRightHand, FRotator(6.f, -10.f, 0.f));
		RightHand->RegisterComponent();
	}
	MakeWand(LeftHand, LeftHandle, LeftRing);
	MakeWand(RightHand, RightHandle, RightRing);

	// The laser, along the right hand's +X from the wand's tip; its dot where it lands.
	UStaticMesh* Cylinder = LoadByPath<UStaticMesh>(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	UStaticMesh* Sphere = LoadByPath<UStaticMesh>(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	Beam = MakePart(TEXT("WTAVRBeam"), Cylinder, RightHand, BeamLook);
	Beam->SetRelativeRotation(FRotator(-90.f, 0.f, 0.f));
	Dot = MakePart(TEXT("WTAVRDot"), Sphere, Me->GetRootComponent(), BeamLook);
	Dot->SetUsingAbsoluteLocation(true);
	Dot->SetUsingAbsoluteRotation(true);
	Dot->SetUsingAbsoluteScale(true);
	Dot->SetWorldScale3D(FVector(0.012f));
	Dot->SetVisibility(false);
	// After the screens (sort priority 0) and the label (5) in the after-motion-blur pass: over a card it points at.
	Beam->SetTranslucentSortPriority(10);
	Dot->SetTranslucentSortPriority(10);

	// The label over the dot.
	Label = NewObject<UWidgetComponent>(Me, UniqueName(TEXT("WTAVRLabel"), UWidgetComponent::StaticClass()));
	Label->SetupAttachment(Me->GetRootComponent());
	Label->SetUsingAbsoluteLocation(true);
	Label->SetUsingAbsoluteRotation(true);
	Label->SetUsingAbsoluteScale(true);
	Label->SetWidgetSpace(EWidgetSpace::World);
	Label->SetDrawAtDesiredSize(false);                      // sized to the widget by FitToWidget as the text changes
	Label->SetTranslucentSortPriority(5);                    // over the HUD screen where the two meet
	Label->SetPivot(FVector2D(0.5f, 1.f));
	Label->SetBlendMode(EWidgetBlendMode::Transparent);
	Label->SetTwoSided(false);
	Label->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Label->SetGenerateOverlapEvents(false);
	Label->SetCastShadow(false);
	Label->SetWindowFocusable(false);
	Label->SetWidgetClass(UWTAVRLabelWidget::StaticClass());
	if (UMaterialInterface* Screen = AWTAVRScreenActor::ScreenMaterial())
	{
		Label->SetMaterial(0, Screen);
	}
	Label->SetHiddenInGame(true);
	Label->RegisterComponent();

	// The screens' pointer: the controller hands it its hit (Custom), it sends the screens hover, press and scroll.
	Pointer = NewObject<UWidgetInteractionComponent>(Me, UniqueName(TEXT("WTAVRPointer"), UWidgetInteractionComponent::StaticClass()));
	Pointer->InteractionSource = EWidgetInteractionSource::Custom;
	Pointer->bEnableHitTesting = true;
	Pointer->InteractionDistance = LaserMaxCm;
	Pointer->SetupAttachment(RightHand);
	Pointer->RegisterComponent();

	LaserActive = -1;
	SetLaser(RightHand->GetComponentLocation() + RightHand->GetForwardVector() * 100.f, false, false);
	UE_LOG(LogWTA, Log, TEXT("WTA_VR rig up: %s, hands %s"), bHeadset ? TEXT("headset") : TEXT("desktop simulation"),
		Origin != nullptr && LeftHand->GetAttachParent() == Origin ? TEXT("tracked") : TEXT("in front of the camera"));
}

void UWTAVRRig::Stop()
{
	if (!bStarted)
	{
		return;
	}
	bStarted = false;
	AWTACharacter* Me = Body();
	if (Me != nullptr && Me->Camera != nullptr && Origin != nullptr)
	{
		// The desktop camera again: on the capsule at the eye, turned by the controller, facing where the head faced.
		const float HeadYaw = GetHeadYaw();
		UCameraComponent* Camera = Me->Camera;
		Camera->AttachToComponent(Me->GetCapsuleComponent(), FAttachmentTransformRules::SnapToTargetNotIncludingScale);
		Camera->SetRelativeLocationAndRotation(FVector(0.f, 0.f, Me->EyeHeight - Me->GetCapsuleComponent()->GetScaledCapsuleHalfHeight()), FRotator::ZeroRotator);
		Camera->bUsePawnControlRotation = true;
		Me->bUseControllerRotationYaw = true;
		if (AController* Controller = Me->GetController())
		{
			Controller->SetControlRotation(FRotator(0.f, HeadYaw, 0.f));
		}
		Me->SetActorRotation(FRotator(0.f, HeadYaw, 0.f));
	}
	for (UActorComponent* Part : TArray<UActorComponent*>{ Pointer.Get(), Label.Get(), Dot.Get(), Beam.Get(), LeftRing.Get(), LeftHandle.Get(),
		RightRing.Get(), RightHandle.Get(), LeftHand.Get(), RightHand.Get(), Origin.Get() })
	{
		if (Part != nullptr)
		{
			Part->DestroyComponent();
		}
	}
	Pointer = nullptr;
	Label = nullptr;
	Dot = nullptr;
	Beam = nullptr;
	LeftRing = LeftHandle = RightRing = RightHandle = nullptr;
	LeftHand = RightHand = Origin = nullptr;
	UE_LOG(LogWTA, Log, TEXT("WTA_VR rig down"));
}

void UWTAVRRig::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	Stop();
	Super::EndPlay(EndPlayReason);
}

void UWTAVRRig::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	AWTACharacter* Me = Body();
	if (!bStarted || !bHeadset || Me == nullptr || Origin == nullptr)
	{
		return;
	}
	// The body follows the head: the capsule steps under it (swept, so walls hold it back) and the origin steps back as
	// far, so the head stays where the visitor put it. A jump of over a metre is a move the game made: it is left alone.
	if (!bSeatedNow)
	{
		const FVector Head = Me->Camera->GetComponentLocation();
		const FVector Centre = Me->GetActorLocation();
		const FVector Step(Head.X - Centre.X, Head.Y - Centre.Y, 0.f);
		const double Size = Step.SizeSquared();
		if (Size > 1.0 && Size < FMath::Square(100.0))
		{
			FHitResult Hit;
			Me->SetActorLocation(Centre + Step, true, &Hit);
			const FVector Moved = Me->GetActorLocation() - Centre;
			Origin->AddWorldOffset(FVector(-Moved.X, -Moved.Y, 0.f));
		}
	}
	// Where the player looks, for the rest of the game (plaques, the facing wax scene, the visit's head tilt).
	if (AController* Controller = Me->GetController())
	{
		Controller->SetControlRotation(GetHeadRotation());
	}
}

void UWTAVRRig::GetAimRay(FVector& OutStart, FVector& OutDirection) const
{
	if (RightHand == nullptr)
	{
		const AWTACharacter* Me = Body();
		OutStart = Me != nullptr ? Me->GetEyeLocation() : FVector::ZeroVector;
		OutDirection = GetHeadRotation().Vector();
		return;
	}
	OutDirection = RightHand->GetForwardVector();
	OutStart = RightHand->GetComponentLocation() + OutDirection * TipCm;
}

void UWTAVRRig::SetSimAimTarget(const FVector& Target)
{
	if (RightHand == nullptr || bHeadset)
	{
		return;
	}
	const FVector Hand = RightHand->GetComponentLocation();
	if (FVector::DistSquared(Hand, Target) > 1.0)
	{
		RightHand->SetWorldRotation((Target - Hand).Rotation());
	}
}

void UWTAVRRig::SetLaser(const FVector& End, bool bHit, bool bActive, bool bOnScreen)
{
	if (Beam == nullptr || RightHand == nullptr)
	{
		return;
	}
	FVector Start;
	FVector Direction;
	GetAimRay(Start, Direction);
	const float Length = FMath::Clamp(static_cast<float>(FVector::DotProduct(End - Start, Direction)), 1.f, LaserMaxCm);
	Beam->SetRelativeLocation(FVector(TipCm + Length * 0.5f, 0.f, 0.f));
	Beam->SetRelativeScale3D(FVector(0.0035f, 0.0035f, Length / 100.f));
	LaserEnd = Start + Direction * Length;
	bLaserHit = bHit;
	if (Dot != nullptr)
	{
		// The same size to the eye wherever it lands: about half a degree on the world (8 mm at a metre, 2.4 cm at
		// three), a quarter on a screen, where it rests on text.
		const float Away = static_cast<float>(FVector::Dist(GetEyeLocation(), LaserEnd));
		const float Across = FMath::Clamp(Away * (bOnScreen ? 0.0045f : 0.008f), 0.4f, 8.f);
		Dot->SetWorldLocation(LaserEnd - Direction * (Across * 0.5f));
		Dot->SetWorldScale3D(FVector(Across / 100.f));    // the basic sphere is a metre across
		Dot->SetVisibility(bHit && !bVisualsHidden);
	}
	if (BeamLook != nullptr && LaserActive != (bActive ? 1 : 0))
	{
		LaserActive = bActive ? 1 : 0;
		// M_WTA_Unlit's BaseColorFactor and Luminance (display referred); a lit fallback takes Color.
		const FLinearColor Colour = bActive ? WTAStyle::Brass() : WTAStyle::Bone();
		BeamLook->SetVectorParameterValue(TEXT("BaseColorFactor"), Colour);
		BeamLook->SetScalarParameterValue(TEXT("Luminance"), bActive ? 1.8f : 0.55f);
		BeamLook->SetVectorParameterValue(TEXT("Color"), Colour);
	}
	if (Label != nullptr && bLabelShown)
	{
		// Over the dot, square on to the eye, a constant size to it (0.04 degrees a pixel: the desktop's hover label).
		const FVector Eye = GetEyeLocation();
		const FVector Where = LaserEnd + FVector(0.f, 0.f, 3.f) + (Eye - LaserEnd).GetSafeNormal() * 4.f;
		const float Away = static_cast<float>(FVector::Dist(Eye, Where));
		Label->SetWorldLocationAndRotation(Where, (Eye - Where).Rotation());
		Label->SetWorldScale3D(FVector(FMath::Clamp(Away * 0.0007f, 0.015f, 2.f)));
	}
}

void UWTAVRRig::SetLabel(const FText& Text)
{
	if (Label == nullptr)
	{
		return;
	}
	UWTAVRLabelWidget* Widget = Cast<UWTAVRLabelWidget>(Label->GetUserWidgetObject());
	if (Widget != nullptr && !Widget->GetLabel().EqualTo(Text))
	{
		Widget->SetLabel(Text);
		bLabelFitted = false;
	}
	// Hidden while empty (an empty plate collapses to nothing to draw).
	bLabelShown = !Text.IsEmpty() && !bVisualsHidden && Widget != nullptr;
	if (bLabelShown && !bLabelFitted)
	{
		bLabelFitted = AWTAVRScreenActor::FitToWidget(Label);
	}
	Label->SetHiddenInGame(!bLabelShown || !bLabelFitted);
}

FText UWTAVRRig::GetLabel() const
{
	const UWTAVRLabelWidget* Widget = Label != nullptr ? Cast<UWTAVRLabelWidget>(Label->GetUserWidgetObject()) : nullptr;
	return Widget != nullptr && bLabelShown ? Widget->GetLabel() : FText::GetEmpty();
}

void UWTAVRRig::SetVisualsHidden(bool bHidden)
{
	bVisualsHidden = bHidden;
	for (UStaticMeshComponent* Part : { LeftHandle.Get(), LeftRing.Get(), RightHandle.Get(), RightRing.Get(), Beam.Get() })
	{
		if (Part != nullptr)
		{
			Part->SetVisibility(!bHidden);
		}
	}
	if (Dot != nullptr)
	{
		Dot->SetVisibility(!bHidden && bLaserHit);
	}
	if (bHidden && Label != nullptr)
	{
		bLabelShown = false;
		Label->SetHiddenInGame(true);
	}
}

FVector UWTAVRRig::GetEyeLocation() const
{
	const AWTACharacter* Me = Body();
	return Me != nullptr ? Me->GetEyeLocation() : FVector::ZeroVector;
}

FRotator UWTAVRRig::GetHeadRotation() const
{
	const AWTACharacter* Me = Body();
	if (Me == nullptr)
	{
		return FRotator::ZeroRotator;
	}
	if (bHeadset && Me->Camera != nullptr)
	{
		return Me->Camera->GetComponentRotation();
	}
	return Me->GetControlRotation();
}

float UWTAVRRig::GetHeadYaw() const
{
	return static_cast<float>(GetHeadRotation().Yaw);
}

void UWTAVRRig::SnapTurn(float Degrees)
{
	AWTACharacter* Me = Body();
	if (Me == nullptr)
	{
		return;
	}
	if (!bHeadset)
	{
		if (AController* Controller = Me->GetController())
		{
			Controller->SetControlRotation(Controller->GetControlRotation() + FRotator(0.f, Degrees, 0.f));
		}
		return;
	}
	// About the head: turn the body, then put the head back where it was.
	const FVector Before = Me->Camera->GetComponentLocation();
	Me->SetActorRotation(Me->GetActorRotation() + FRotator(0.f, Degrees, 0.f));
	const FVector After = Me->Camera->GetComponentLocation();
	Me->SetActorLocation(Me->GetActorLocation() + FVector(Before.X - After.X, Before.Y - After.Y, 0.f), false, nullptr, ETeleportType::TeleportPhysics);
}

void UWTAVRRig::FaceYaw(float Yaw)
{
	AWTACharacter* Me = Body();
	if (Me == nullptr || !bHeadset)
	{
		return;
	}
	SnapTurn(FRotator::NormalizeAxis(Yaw - GetHeadYaw()));
}

void UWTAVRRig::StandHeadAt(const FVector& Floor, float Yaw)
{
	AWTACharacter* Me = Body();
	if (Me == nullptr || !bHeadset)
	{
		return;
	}
	FaceYaw(Yaw);
	// The body under the head, the head over Floor: the origin (the visitor's own floor) on Floor.
	const FVector Head = Me->Camera->GetComponentLocation();
	FVector Centre = Me->GetActorLocation() + FVector(Floor.X - Head.X, Floor.Y - Head.Y, 0.f);
	Centre.Z = Floor.Z - StandingOriginZ();
	Me->SetActorLocation(Centre, false, nullptr, ETeleportType::TeleportPhysics);
	Me->GetCharacterMovement()->Velocity = FVector::ZeroVector;
}

void UWTAVRRig::SetSeated(bool bSeated, float EyeZ)
{
	AWTACharacter* Me = Body();
	bSeatedNow = bSeated;
	if (Me == nullptr || Origin == nullptr || !bHeadset)
	{
		return;
	}
	FVector Relative = Origin->GetRelativeLocation();
	if (bSeated)
	{
		// The eyes at EyeZ: the origin as far under them as the head is over the origin now (the visitor's own height).
		const float HeadOverOrigin = static_cast<float>(Me->Camera->GetRelativeLocation().Z);
		Relative.Z = EyeZ - HeadOverOrigin - Me->GetActorLocation().Z;
	}
	else
	{
		Relative.Z = StandingOriginZ();
	}
	Origin->SetRelativeLocation(Relative);
}
