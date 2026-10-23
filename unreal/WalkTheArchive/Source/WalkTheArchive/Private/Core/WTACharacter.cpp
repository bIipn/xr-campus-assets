// Walk the Archive - the first-person player (port of the web nav.js player feel).

#include "Core/WTACharacter.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerState.h"
#include "Systems/WTAProgressSubsystem.h"
#include "UI/WTANameTagWidget.h"
#include "UI/WTAUIStyle.h"
#include "XR/WTAVRRig.h"
#include "XR/WTAVRScreenActor.h"
#include "XR/WTAXR.h"
#include "Components/StaticMeshComponent.h"
#include "Components/WidgetComponent.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Net/UnrealNetwork.h"
#include "UObject/ConstructorHelpers.h"
#include "UObject/SoftObjectPath.h"
#include "AITypes.h"
#include "Blueprint/AIBlueprintHelperLibrary.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Controller.h"
#include "NavigationData.h"
#include "Navigation/PathFollowingComponent.h"

namespace
{
	/** The path-following component SimpleMoveToLocation attaches to the controller (null before the first walk). */
	UPathFollowingComponent* PathFollowingOf(const AController* Controller)
	{
		return Controller ? Controller->FindComponentByClass<UPathFollowingComponent>() : nullptr;
	}

	constexpr float CapsuleRadius = 30.f;
	constexpr float CapsuleHalfHeight = 90.f;
	/** A seated capsule: 120 cm tall, standing on the floor at the sit point. */
	constexpr float SeatedHalfHeight = 60.f;

	/** A mesh of the designed figure (bl/figure.py), where the Interchange import files the People wing. */
	UStaticMesh* FindFigureMesh(const TCHAR* Name)
	{
		const FString Paths[2] = {
			FString::Printf(TEXT("/Game/WTA/Campus/People/People/StaticMeshes/%s.%s"), Name, Name),
			FString::Printf(TEXT("/Game/WTA/Campus/People/StaticMeshes/%s.%s"), Name, Name),
		};
		for (const FString& Path : Paths)
		{
			if (UStaticMesh* Mesh = Cast<UStaticMesh>(FSoftObjectPath(Path).TryLoad()))
			{
				return Mesh;
			}
		}
		return nullptr;
	}

	/** bl/figure.py's layout (cm over the figure's root, the floor): the seated body sits on a 45 cm seat, the head
	    and visor turn about the neck joint, the collar ring rings the neck's base under it. */
	constexpr float DesignedSeatZ = 45.f;
	constexpr float DesignedJointStanding = 150.f;
	constexpr float DesignedJointSeated = DesignedSeatZ + 63.f;
	constexpr float DesignedCollarDrop = 3.4f;

	/** Size Part's mesh by Scale and stand its bounds' bottom at BottomZ (cm over the figure's root, the floor).
	    The engine's basic shapes are 100 cm across; their bounds say where their pivot is. */
	void PlacePart(UStaticMeshComponent* Part, float BottomZ, const FVector& Scale, float Forward = 0.f)
	{
		if (Part == nullptr)
		{
			return;
		}
		Part->SetRelativeScale3D(Scale);
		FVector Offset(Forward, 0.f, BottomZ);
		if (const UStaticMesh* Mesh = Part->GetStaticMesh())
		{
			const FBoxSphereBounds Bounds = Mesh->GetBounds();
			Offset.X -= Bounds.Origin.X * Scale.X;
			Offset.Y -= Bounds.Origin.Y * Scale.Y;
			Offset.Z -= (Bounds.Origin.Z - Bounds.BoxExtent.Z) * Scale.Z;
		}
		Part->SetRelativeLocation(Offset);
	}
}

AWTACharacter::AWTACharacter()
{
	PrimaryActorTick.bCanEverTick = true;

	GetCapsuleComponent()->InitCapsuleSize(CapsuleRadius, CapsuleHalfHeight);

	// The camera sits at the eye: 162 cm above the floor = 72 cm above the capsule centre. Bob and dip move it.
	Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
	Camera->SetupAttachment(GetCapsuleComponent());
	Camera->SetRelativeLocation(FVector(0.f, 0.f, EyeHeight - CapsuleHalfHeight));
	Camera->bUsePawnControlRotation = true;
	Camera->SetFieldOfView(66.f);

	// The body turns with the camera yaw; pitch and roll stay on the camera only.
	bUseControllerRotationYaw = true;
	bUseControllerRotationPitch = false;
	bUseControllerRotationRoll = false;
	BaseEyeHeight = EyeHeight - CapsuleHalfHeight;

	// Web feel: walk 3 m/s, sprint 5.6, jump 5.2 m/s under 16 m/s^2, quick starts and stops, a little air control.
	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->MaxWalkSpeed = WalkSpeed;
	Move->JumpZVelocity = 520.f;
	Move->GravityScale = 1.63f;
	Move->MaxAcceleration = 3000.f;
	Move->BrakingDecelerationWalking = 4200.f;
	Move->BrakingFrictionFactor = 1.f;
	Move->AirControl = 0.25f;
	Move->bOrientRotationToMovement = false;
	Move->bUseControllerDesiredRotation = false;

	// No body mesh in phase 0: the player is a camera on a capsule.
	GetMesh()->SetVisibility(false);
	GetMesh()->SetOwnerNoSee(true);

	// Guided visits: everyone sees everyone wherever they are, and each machine has the say over its own player
	// (a trusted group on one network), so teleports and seats need no server correction.
	bAlwaysRelevant = true;
	Move->bServerAcceptClientAuthoritativePosition = true;
	Move->bIgnoreClientMovementErrorChecksAndCorrection = true;

	// The figure the others see, from the engine's basic shapes coloured per person (BasicShapeMaterial's Color).
	static ConstructorHelpers::FObjectFinder<UStaticMesh> ConeMesh(TEXT("/Engine/BasicShapes/Cone.Cone"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMesh(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> ShapeMaterial(TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));

	Figure = CreateDefaultSubobject<USceneComponent>(TEXT("Figure"));
	Figure->SetupAttachment(GetCapsuleComponent());
	Figure->SetRelativeLocation(FVector(0.f, 0.f, -CapsuleHalfHeight));

	auto MakePart = [this](const TCHAR* Name, UStaticMesh* PartMesh, USceneComponent* Parent)
	{
		UStaticMeshComponent* Part = CreateDefaultSubobject<UStaticMeshComponent>(Name);
		Part->SetupAttachment(Parent);
		Part->SetStaticMesh(PartMesh);
		if (ShapeMaterial.Succeeded())
		{
			Part->SetMaterial(0, ShapeMaterial.Object);
		}
		Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Part->SetGenerateOverlapEvents(false);
		Part->SetCanEverAffectNavigation(false);
		Part->SetOwnerNoSee(true);
		Part->SetHiddenInGame(true);
		Part->SetCastShadow(true);
		return Part;
	};
	ShapeLook = ShapeMaterial.Object;
	FigureBase = MakePart(TEXT("FigureBase"), CylinderMesh.Object, Figure);
	FigureBody = MakePart(TEXT("FigureBody"), ConeMesh.Object, Figure);
	FigureShoulders = MakePart(TEXT("FigureShoulders"), SphereMesh.Object, Figure);
	FigureNeck = CreateDefaultSubobject<USceneComponent>(TEXT("FigureNeck"));
	FigureNeck->SetupAttachment(Figure);
	FigureHead = MakePart(TEXT("FigureHead"), SphereMesh.Object, FigureNeck);
	FigureVisor = MakePart(TEXT("FigureVisor"), SphereMesh.Object, FigureNeck);
	FigureVisor->SetCastShadow(false);

	NameTag = CreateDefaultSubobject<UWidgetComponent>(TEXT("NameTag"));
	NameTag->SetupAttachment(Figure);
	NameTag->SetWidgetSpace(EWidgetSpace::Screen);
	NameTag->SetDrawAtDesiredSize(true);
	NameTag->SetPivot(FVector2D(0.5f, 1.f));
	NameTag->SetWidgetClass(UWTANameTagWidget::StaticClass());
	NameTag->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	NameTag->SetGenerateOverlapEvents(false);
	NameTag->SetHiddenInGame(true);

	LayoutFigure(false);
}

void AWTACharacter::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME_CONDITION(AWTACharacter, bSeatedPose, COND_SkipOwner);
}

void AWTACharacter::LayoutFigure(bool bSitting)
{
	bFigureLaidSeated = bSitting;
	const float Half = GetCapsuleComponent() ? GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight() : CapsuleHalfHeight;
	// Standing, the movement keeps the capsule a couple of centimetres over the floor (between its MIN_FLOOR_DIST and
	// MAX_FLOOR_DIST): the figure stands on the floor itself. Seated, the capsule is put down exactly.
	const float FloorGap = bSitting ? 0.f : 0.5f * (UCharacterMovementComponent::MIN_FLOOR_DIST + UCharacterMovementComponent::MAX_FLOOR_DIST);
	Figure->SetRelativeLocation(FVector(0.f, 0.f, -Half - FloorGap));
	if (bDesignedFigure)
	{
		const float JointZ = bSitting ? DesignedJointSeated : DesignedJointStanding;
		FigureBody->SetStaticMesh(bSitting ? SeatedMesh.Get() : StandingMesh.Get());
		FigureBody->SetRelativeLocation(FVector(0.f, 0.f, bSitting ? DesignedSeatZ : 0.f));
		FigureShoulders->SetRelativeLocation(FVector(0.f, 0.f, JointZ - DesignedCollarDrop));
		FigureNeck->SetRelativeLocation(FVector(0.f, 0.f, JointZ));
		FigureHead->SetRelativeLocation(FVector::ZeroVector);
		FigureVisor->SetRelativeLocation(FVector::ZeroVector);
		PlaceNameTags(FVector(0.f, 0.f, JointZ + 33.f));    // a hand over the crown (26 cm over the joint)
		return;
	}
	// Standing: a turned base, a tapered body to 1.23 m, shoulders, the head at 1.46 m (the eye is at 1.62).
	// Seated: no base, the body sitting on a 45 cm seat, the head at 1.27 m.
	const float BodyBottom = bSitting ? 45.f : 5.f;
	const float BodyHeight = bSitting ? 62.f : 118.f;
	const float NeckZ = BodyBottom + BodyHeight + (bSitting ? 15.f : 17.f);
	FigureBase->SetVisibility(!bSitting);
	PlacePart(FigureBase, 0.f, FVector(0.46f, 0.46f, 0.05f));
	PlacePart(FigureBody, BodyBottom, FVector(0.5f, 0.5f, BodyHeight / 100.f));
	PlacePart(FigureShoulders, BodyBottom + BodyHeight - 9.f, FVector(0.36f, 0.36f, 0.13f));
	FigureNeck->SetRelativeLocation(FVector(0.f, 0.f, NeckZ));
	PlacePart(FigureHead, -9.f, FVector(0.27f, 0.27f, 0.29f));
	PlacePart(FigureVisor, 2.f, FVector(0.07f, 0.19f, 0.075f), 11.f);
	PlaceNameTags(FVector(0.f, 0.f, NeckZ + 40.f));
}

void AWTACharacter::PlaceNameTags(const FVector& Relative)
{
	NameTag->SetRelativeLocation(Relative);
	if (NameTagWorld != nullptr)
	{
		NameTagWorld->SetRelativeLocation(Relative);
	}
}

UWidgetComponent* AWTACharacter::WorldNameTag()
{
	if (NameTagWorld == nullptr)
	{
		// The screen tag's widget and place, drawn in the world (M_WTA_WidgetScreen: over everything, so the wall check
		// in UpdateFigure decides when it shows, as for the screen tag); UpdateFigure turns it to the eye.
		NameTagWorld = NewObject<UWidgetComponent>(this, TEXT("NameTagWorld"));
		NameTagWorld->SetupAttachment(Figure);
		NameTagWorld->SetUsingAbsoluteRotation(true);
		NameTagWorld->SetUsingAbsoluteScale(true);
		NameTagWorld->SetWidgetSpace(EWidgetSpace::World);
		NameTagWorld->SetDrawAtDesiredSize(true);
		NameTagWorld->SetPivot(FVector2D(0.5f, 1.f));
		NameTagWorld->SetBlendMode(EWidgetBlendMode::Transparent);
		NameTagWorld->SetTwoSided(false);
		NameTagWorld->SetWindowFocusable(false);
		NameTagWorld->SetWidgetClass(UWTANameTagWidget::StaticClass());
		NameTagWorld->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		NameTagWorld->SetGenerateOverlapEvents(false);
		NameTagWorld->SetCastShadow(false);
		if (UMaterialInterface* Look = AWTAVRScreenActor::ScreenMaterial())
		{
			NameTagWorld->SetMaterial(0, Look);
		}
		NameTagWorld->SetRelativeLocation(NameTag->GetRelativeLocation());
		NameTagWorld->SetHiddenInGame(true);
		NameTagWorld->RegisterComponent();
	}
	return NameTagWorld;
}

UWidgetComponent* AWTACharacter::ActiveNameTag()
{
	return bTagInWorld ? WorldNameTag() : NameTag.Get();
}

void AWTACharacter::LoadFigureMeshes()
{
	if (bFigureMeshesTried)
	{
		return;
	}
	bFigureMeshesTried = true;
	UStaticMesh* Body = FindFigureMesh(TEXT("figure__body"));
	UStaticMesh* Seated = FindFigureMesh(TEXT("figure__seated"));
	UStaticMesh* Head = FindFigureMesh(TEXT("figure__head"));
	UStaticMesh* Visor = FindFigureMesh(TEXT("figure__visor"));
	UStaticMesh* Collar = FindFigureMesh(TEXT("figure__collar"));
	if (Body == nullptr || Seated == nullptr || Head == nullptr || Visor == nullptr || Collar == nullptr)
	{
		UE_LOG(LogWTA, Log, TEXT("Figure: the designed figure is not imported (Campus/People); the basic shapes stand in"));
		return;
	}
	StandingMesh = Body;
	SeatedMesh = Seated;
	FigureHead->SetStaticMesh(Head);
	FigureVisor->SetStaticMesh(Visor);
	FigureShoulders->SetStaticMesh(Collar);
	for (UStaticMeshComponent* Part : { FigureBody.Get(), FigureShoulders.Get(), FigureHead.Get(), FigureVisor.Get() })
	{
		Part->SetRelativeScale3D(FVector::OneVector);
	}
	FigureBase->SetVisibility(false);
	if (UMaterialInterface* Look = Cast<UMaterialInterface>(FSoftObjectPath(TEXT("/Game/WTA/Materials/M_WTA_Figure.M_WTA_Figure")).TryLoad()))
	{
		FigureLook = Look;
	}
	bDesignedFigure = true;
	FigureMaterial = nullptr;                        // the colours are made again on the new meshes
	ShownSlot = -1;
	LayoutFigure(bFigureLaidSeated);
}

void AWTACharacter::BeginPlay()
{
	Super::BeginPlay();
	GetCharacterMovement()->MaxWalkSpeed = bSprinting ? SprintSpeed : WalkSpeed;
	LastFrameLocation = GetActorLocation();
	bHasLastFrameLocation = true;

	// People in a visit walk through each other: a group at a stop never blocks itself or a doorway.
	for (TActorIterator<AWTACharacter> It(GetWorld()); It; ++It)
	{
		if (*It != this)
		{
			GetCapsuleComponent()->IgnoreActorWhenMoving(*It, true);
			It->GetCapsuleComponent()->IgnoreActorWhenMoving(this, true);
		}
	}
}

void AWTACharacter::OnRep_PlayerState()
{
	Super::OnRep_PlayerState();
	ShownSlot = -1;                                  // the look is read again on the next tick
}

void AWTACharacter::ShareSeated(bool bOn)
{
	if (GetNetMode() == NM_Standalone)
	{
		return;
	}
	if (HasAuthority())
	{
		bSeatedPose = bOn;                           // the guide's own pawn: the pose replicates from here
		ForceNetUpdate();
	}
	else if (IsLocallyControlled())
	{
		ServerSetSeated(bOn, GetActorLocation(), static_cast<float>(GetActorRotation().Yaw));
	}
}

void AWTACharacter::ServerSetSeated_Implementation(bool bOn, FVector_NetQuantize Location, float Yaw)
{
	bSeatedPose = bOn;
	UCapsuleComponent* Capsule = GetCapsuleComponent();
	UCharacterMovementComponent* Move = GetCharacterMovement();
	Capsule->SetCapsuleHalfHeight(bOn ? SeatedHalfHeight : CapsuleHalfHeight);
	if (bOn)
	{
		Move->DisableMovement();
	}
	SetActorLocationAndRotation(Location, FRotator(0.f, Yaw, 0.f), false, nullptr, ETeleportType::TeleportPhysics);
	if (!bOn)
	{
		Move->SetMovementMode(MOVE_Walking);
	}
	Move->Velocity = FVector::ZeroVector;
	ForceNetUpdate();
	LayoutFigure(bOn);
}

void AWTACharacter::OnRep_SeatedPose()
{
	// The others' copy: the capsule the owner has, so the figure stands (or sits) on the floor under it.
	GetCapsuleComponent()->SetCapsuleHalfHeight(bSeatedPose ? SeatedHalfHeight : CapsuleHalfHeight);
	LayoutFigure(bSeatedPose);
}

void AWTACharacter::RefreshFigureLook()
{
	const AWTAPlayerState* Person = GetPlayerState<AWTAPlayerState>();
	if (Person == nullptr)
	{
		return;
	}
	const FString Name = Person->GetVisitName();
	if (Name == ShownName && Person->Slot == ShownSlot && Person->bGuide == bShownGuide)
	{
		return;
	}
	ShownName = Name;
	ShownSlot = Person->Slot;
	bShownGuide = Person->bGuide;
	const FLinearColor Color = Person->GetVisitColor();
	UMaterialInterface* Base = FigureLook != nullptr ? FigureLook.Get() : ShapeLook.Get();
	if (FigureMaterial == nullptr && Base != nullptr)
	{
		FigureMaterial = UMaterialInstanceDynamic::Create(Base, this);
		HeadMaterial = UMaterialInstanceDynamic::Create(Base, this);
		VisorMaterial = UMaterialInstanceDynamic::Create(Base, this);
		CollarMaterial = UMaterialInstanceDynamic::Create(Base, this);
		FigureBase->SetMaterial(0, FigureMaterial);
		FigureBody->SetMaterial(0, FigureMaterial);
		FigureHead->SetMaterial(0, HeadMaterial);
		FigureVisor->SetMaterial(0, VisorMaterial);
		if (bDesignedFigure)
		{
			FigureBody->SetMaterial(1, HeadMaterial);    // the hands, in the head's warm neutral
			FigureShoulders->SetMaterial(0, CollarMaterial);
		}
		else
		{
			FigureShoulders->SetMaterial(0, FigureMaterial);
		}
	}
	if (FigureMaterial != nullptr)
	{
		// The robe in the person's colour with a soft sheen, the head and hands a warm neutral touched by it, the
		// visor dark glass, the collar a deeper shade of the robe (M_WTA_Figure's Roughness and Sheen; the basic
		// shape material only takes the colour).
		FigureMaterial->SetVectorParameterValue(TEXT("Color"), Color);
		FigureMaterial->SetScalarParameterValue(TEXT("Roughness"), 0.72f);
		FigureMaterial->SetScalarParameterValue(TEXT("Sheen"), 0.35f);
		HeadMaterial->SetVectorParameterValue(TEXT("Color"), bDesignedFigure ? FMath::Lerp(WTAStyle::FromHex(0xd6c4a8), Color, 0.08f)
			: FMath::Lerp(Color, WTAStyle::Bone(), 0.35f));
		HeadMaterial->SetScalarParameterValue(TEXT("Roughness"), 0.5f);
		HeadMaterial->SetScalarParameterValue(TEXT("Sheen"), 0.15f);
		VisorMaterial->SetVectorParameterValue(TEXT("Color"), WTAStyle::FromHex(bDesignedFigure ? 0x141c1a : 0x1b2622));
		VisorMaterial->SetScalarParameterValue(TEXT("Roughness"), 0.12f);
		VisorMaterial->SetScalarParameterValue(TEXT("Sheen"), 0.f);
		CollarMaterial->SetVectorParameterValue(TEXT("Color"), Color * 0.55f);
		CollarMaterial->SetScalarParameterValue(TEXT("Roughness"), 0.38f);
		CollarMaterial->SetScalarParameterValue(TEXT("Sheen"), 0.2f);
	}
	if (UWTANameTagWidget* Tag = Cast<UWTANameTagWidget>(ActiveNameTag()->GetUserWidgetObject()))
	{
		Tag->SetPerson(FText::FromString(Name), Person->bGuide, Color);
	}
	else
	{
		ShownSlot = -1;                              // the widget is made on the first draw: try again then
	}
}

void AWTACharacter::UpdateFigure(float DeltaSeconds)
{
	bool bShow = (GetNetMode() != NM_Standalone || bStandIn) && !IsLocallyControlled() && GetPlayerState() != nullptr;
	const APlayerController* Viewer = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	FVector Eye = FVector::ZeroVector;
	if (bShow && Viewer != nullptr)
	{
		FRotator EyeRotation;
		Viewer->GetPlayerViewPoint(Eye, EyeRotation);
		// Never inside the camera: a figure within arm's reach of the eye hides.
		const FVector Chest = Figure->GetComponentLocation() + FVector(0.f, 0.f, 110.f);
		if (FVector::Dist2D(Eye, Chest) < 65.f && FMath::Abs(Eye.Z - Chest.Z) < 120.f)
		{
			bShow = false;
		}
	}
	if (bShow != bFigureShown)
	{
		bFigureShown = bShow;
		if (bShow)
		{
			LoadFigureMeshes();
		}
		for (UStaticMeshComponent* Part : { FigureBase.Get(), FigureBody.Get(), FigureShoulders.Get(), FigureHead.Get(), FigureVisor.Get() })
		{
			Part->SetHiddenInGame(!bShow);
		}
		if (!bShow)
		{
			NameTag->SetHiddenInGame(true);
			if (NameTagWorld != nullptr)
			{
				NameTagWorld->SetHiddenInGame(true);
			}
			bTagHidden = true;
		}
	}
	if (!bShow)
	{
		return;
	}
	// In VR the name tag draws in the world: change over when the presentation does (the next check shows it).
	const bool bWorldTag = WTAXR::IsPresentationActive();
	if (bWorldTag != bTagInWorld)
	{
		NameTag->SetHiddenInGame(true);
		if (NameTagWorld != nullptr)
		{
			NameTagWorld->SetHiddenInGame(true);
		}
		bTagInWorld = bWorldTag;
		bTagHidden = true;
		SinceTagCheck = 1.f;
		ShownSlot = -1;                                  // the person goes onto the tag now in use
	}
	SinceLook += DeltaSeconds;
	if (ShownSlot < 0 || SinceLook > 0.5f)
	{
		SinceLook = 0.f;
		RefreshFigureLook();
	}
	if (bSeatedPose != bFigureLaidSeated)
	{
		LayoutFigure(bSeatedPose);
	}
	// The head follows the person's look up and down (the body already turns with it).
	const float Pitch = FMath::Clamp(static_cast<float>(FRotator::NormalizeAxis(GetBaseAimRotation().Pitch)), -35.f, 35.f);
	FigureNeck->SetRelativeRotation(FRotator(Pitch, 0.f, 0.f));

	// The name: within 30 m and not behind a wall (checked a few times a second).
	SinceTagCheck += DeltaSeconds;
	if (SinceTagCheck > 0.25f && Viewer != nullptr)
	{
		SinceTagCheck = 0.f;
		const FVector Head = FigureHead->GetComponentLocation();
		bool bHide = FVector::Dist(Eye, Head) > 3000.f;
		if (!bHide)
		{
			FCollisionQueryParams Params(FName(TEXT("WTANameTag")), false, this);
			Params.AddIgnoredActor(Viewer->GetPawn());
			FHitResult Hit;
			bHide = GetWorld()->LineTraceSingleByChannel(Hit, Eye, Head, ECC_Visibility, Params);
		}
		UWidgetComponent* Tag = ActiveNameTag();
		if (bHide != bTagHidden)
		{
			bTagHidden = bHide;
			Tag->SetHiddenInGame(bHide);
		}
		if (!bHide && !bTagLogged)
		{
			bTagLogged = true;
			const UUserWidget* TagWidget = Tag->GetUserWidgetObject();
			UE_LOG(LogWTA, Log, TEXT("WTA_FIGURE %s: %s figure, %s name tag %s (widget %s, slate %s, %.0f x %.0f)"), *ShownName,
				bDesignedFigure ? TEXT("designed") : TEXT("basic"), bTagInWorld ? TEXT("world") : TEXT("screen"), Tag->IsVisible() ? TEXT("visible") : TEXT("hidden"),
				TagWidget ? TEXT("made") : TEXT("missing"), TagWidget && TagWidget->GetCachedWidget().IsValid() ? TEXT("built") : TEXT("not built"),
				TagWidget ? TagWidget->GetDesiredSize().X : 0.f, TagWidget ? TagWidget->GetDesiredSize().Y : 0.f);
		}
	}
	// A tag in the world turns to the eye and keeps one size to it (about 0.05 degrees a pixel).
	if (bTagInWorld && !bTagHidden && NameTagWorld != nullptr)
	{
		const FVector Where = NameTagWorld->GetComponentLocation();
		NameTagWorld->SetWorldRotation((Eye - Where).Rotation());
		NameTagWorld->SetWorldScale3D(FVector(FMath::Clamp(static_cast<float>(FVector::Dist(Eye, Where)) * 0.0009f, 0.05f, 4.f)));
	}
}

void AWTACharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// An auto-walk ends when the path follower stops moving (arrived, blocked or aborted).
	if (bAutoWalking)
	{
		const UPathFollowingComponent* Following = PathFollowingOf(GetController());
		if (Following == nullptr || Following->GetStatus() != EPathFollowingStatus::Moving)
		{
			bAutoWalking = false;
			GetCharacterMovement()->MaxWalkSpeed = bSprinting ? SprintSpeed : WalkSpeed;
		}
	}

	if (IsLocallyControlled())
	{
		UpdateCameraOffset(DeltaSeconds);
		NoteDistanceWalked();
	}
	UpdateFigure(DeltaSeconds);
}

void AWTACharacter::Landed(const FHitResult& Hit)
{
	Super::Landed(Hit);
	// Landing dip: the faster the fall, the deeper the dip (web: dipV -= min(0.8 m/s, fall * 0.1)).
	const float FallSpeed = FMath::Max(0.f, static_cast<float>(-GetCharacterMovement()->Velocity.Z));
	DipVelocity -= FMath::Min(80.f, FallSpeed * LandingDipScale);
}

void AWTACharacter::WalkTo(FVector Dest)
{
	AController* OwnController = GetController();
	if (OwnController == nullptr)
	{
		return;
	}
	// Needs a NavMesh (the navmesh setup step). Without one the call logs a warning and nothing moves.
	UAIBlueprintHelperLibrary::SimpleMoveToLocation(OwnController, Dest);

	const UPathFollowingComponent* Following = PathFollowingOf(OwnController);
	if (Following != nullptr && Following->GetStatus() == EPathFollowingStatus::Moving)
	{
		float PathLength = static_cast<float>(FVector::Dist2D(GetActorLocation(), Dest));
		const FNavPathSharedPtr Path = Following->GetPath();
		if (Path.IsValid())
		{
			PathLength = static_cast<float>(Path->GetLength());
		}
		// Web: clamp(L / 2.3, 2.4, 12) m/s. Short hops stay slow, long trips move fast.
		GetCharacterMovement()->MaxWalkSpeed = FMath::Clamp(PathLength / 2.3f, TravelSpeedMin, TravelSpeedMax);
		bAutoWalking = true;
	}
	else
	{
		bAutoWalking = false;
		GetCharacterMovement()->MaxWalkSpeed = bSprinting ? SprintSpeed : WalkSpeed;
	}
}

void AWTACharacter::StopWalking()
{
	if (UPathFollowingComponent* Following = PathFollowingOf(GetController()))
	{
		if (Following->GetStatus() != EPathFollowingStatus::Idle)
		{
			Following->AbortMove(*this, FPathFollowingResultFlags::UserAbort);
		}
	}
	bAutoWalking = false;
	GetCharacterMovement()->MaxWalkSpeed = bSprinting ? SprintSpeed : WalkSpeed;
}

bool AWTACharacter::IsAutoWalking() const
{
	return bAutoWalking;
}

void AWTACharacter::SitAt(AActor* InSeat, const FVector& SeatTop, float Yaw)
{
	StopWalking();
	UCapsuleComponent* Capsule = GetCapsuleComponent();
	UCharacterMovementComponent* Move = GetCharacterMovement();
	if (Capsule == nullptr || Move == nullptr)
	{
		return;
	}
	if (!bSeated)
	{
		StandLocation = GetActorLocation();
	}
	bSeated = true;
	Seat = InSeat;

	// The floor under the seat: traced a knee's length in front of the sit point, where no cushion or frame is
	// in the way; a chair's 45 cm when nothing answers.
	const FVector Forward = FRotator(0.f, Yaw, 0.f).Vector();
	float FloorZ = SeatTop.Z - 45.f;
	FHitResult Hit;
	FCollisionQueryParams Params(FName(TEXT("WTASeatFloor")), false, this);
	if (InSeat != nullptr)
	{
		Params.AddIgnoredActor(InSeat);
	}
	if (GetWorld() != nullptr && GetWorld()->LineTraceSingleByChannel(Hit, SeatTop + Forward * 40.f - FVector(0.f, 0.f, 2.f), SeatTop + Forward * 40.f - FVector(0.f, 0.f, 160.f), ECC_Visibility, Params))
	{
		FloorZ = static_cast<float>(Hit.Location.Z);
	}

	// A seated capsule: 120 cm tall, standing on the floor at the sit point, with the eye at its seated height.
	Move->DisableMovement();
	Move->Velocity = FVector::ZeroVector;
	Capsule->SetCapsuleHalfHeight(SeatedHalfHeight);
	const FVector Centre(SeatTop.X, SeatTop.Y, FloorZ + SeatedHalfHeight + 1.f);
	SetActorLocation(Centre, false, nullptr, ETeleportType::TeleportPhysics);
	SeatedCameraZ = SeatTop.Z + SeatEyeHeight - Centre.Z;
	SeatedEyeZ = SeatTop.Z + SeatEyeHeight;
	Camera->SetRelativeLocation(FVector(0.f, 0.f, SeatedCameraZ));
	if (AController* OwnController = GetController())
	{
		OwnController->SetControlRotation(FRotator(-8.f, Yaw, 0.f));
	}
	SetActorRotation(FRotator(0.f, Yaw, 0.f));
	BobPhase = 0.f;
	BobAmount = 0.f;
	DipOffset = 0.f;
	DipVelocity = 0.f;
	LastFrameLocation = GetActorLocation();
	bHasLastFrameLocation = true;
	if (VRRig != nullptr)
	{
		// A headset: face the seat's way about the head, the eyes at the seated height whatever the visitor's own.
		VRRig->FaceYaw(Yaw);
		VRRig->SetSeated(true, SeatedEyeZ);
	}
	ShareSeated(true);
	OnSeatChanged.Broadcast(InSeat, true);
}

void AWTACharacter::StandUp(bool bReturn)
{
	if (!bSeated)
	{
		return;
	}
	bSeated = false;
	AActor* WasSeat = Seat.Get();
	Seat = nullptr;
	UCapsuleComponent* Capsule = GetCapsuleComponent();
	UCharacterMovementComponent* Move = GetCharacterMovement();
	if (Capsule != nullptr)
	{
		Capsule->SetCapsuleHalfHeight(CapsuleHalfHeight);
	}
	if (bReturn)
	{
		SetActorLocation(StandLocation, false, nullptr, ETeleportType::TeleportPhysics);
	}
	if (Move != nullptr)
	{
		Move->SetMovementMode(MOVE_Walking);
		Move->Velocity = FVector::ZeroVector;
	}
	if (AController* OwnController = GetController())
	{
		const FRotator Now = OwnController->GetControlRotation();
		OwnController->SetControlRotation(FRotator(0.f, Now.Yaw, 0.f));
	}
	Camera->SetRelativeLocation(FVector(0.f, 0.f, EyeHeight - CapsuleHalfHeight));
	if (VRRig != nullptr)
	{
		VRRig->SetSeated(false, 0.f);
	}
	LastFrameLocation = GetActorLocation();
	bHasLastFrameLocation = true;
	ShareSeated(false);
	OnSeatChanged.Broadcast(WasSeat, false);
}

void AWTACharacter::TeleportToView(const FWTAView& View)
{
	if (!View.bValid)
	{
		return;
	}
	if (bSeated)
	{
		StandUp(false);                            // a tour stop or a place: the seat is left behind
	}
	StopWalking();
	if (VRRig != nullptr && VRRig->IsHeadset())
	{
		// A headset: the head (not the capsule) over the view's floor point, facing its yaw; the pitch is the visitor's.
		VRRig->StandHeadAt(FVector(View.Location.X, View.Location.Y, View.Location.Z - EyeHeight), View.Yaw);
		LastFrameLocation = GetActorLocation();
		bHasLastFrameLocation = true;
		return;
	}
	// View.Location is the eye; the capsule centre sits EyeHeight below it plus the half height.
	FVector Location = View.Location;
	Location.Z = View.Location.Z - EyeHeight + GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	SetActorLocation(Location, false, nullptr, ETeleportType::TeleportPhysics);
	GetCharacterMovement()->Velocity = FVector::ZeroVector;
	if (AController* OwnController = GetController())
	{
		OwnController->SetControlRotation(FRotator(View.Pitch, View.Yaw, 0.f));
	}
	SetActorRotation(FRotator(0.f, View.Yaw, 0.f));
	BobPhase = 0.f;
	BobAmount = 0.f;
	DipOffset = 0.f;
	DipVelocity = 0.f;
	LastFrameLocation = GetActorLocation();
	bHasLastFrameLocation = true;
}

FWTAView AWTACharacter::GetCurrentView() const
{
	FWTAView View;
	View.Location = GetEyeLocation();
	const FRotator Rotation = GetControlRotation().GetNormalized();
	View.Yaw = static_cast<float>(Rotation.Yaw);
	View.Pitch = static_cast<float>(Rotation.Pitch);
	View.bValid = true;
	return View;
}

FVector AWTACharacter::GetEyeLocation() const
{
	return Camera ? Camera->GetComponentLocation() : GetActorLocation() + FVector(0.f, 0.f, EyeHeight - CapsuleHalfHeight);
}

void AWTACharacter::SetSprinting(bool bOn)
{
	bSprinting = bOn;
	if (!bAutoWalking)
	{
		GetCharacterMovement()->MaxWalkSpeed = bSprinting ? SprintSpeed : WalkSpeed;
	}
}

void AWTACharacter::AddMoveInput(FVector2D Axis)
{
	if (Axis.IsNearlyZero())
	{
		return;
	}
	if (bAutoWalking)
	{
		StopWalking();
	}
	const FRotator YawRotation(0.f, GetControlRotation().Yaw, 0.f);
	const FVector Forward = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X);
	const FVector Right = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::Y);
	AddMovementInput(Forward, Axis.Y);
	AddMovementInput(Right, Axis.X);
}

void AWTACharacter::UpdateCameraOffset(float DeltaSeconds)
{
	if (VRRig != nullptr && VRRig->IsHeadset())
	{
		return;                                    // the headset places the camera
	}
	if (bSeated)
	{
		Camera->SetRelativeLocation(FVector(0.f, 0.f, SeatedCameraZ));
		return;
	}
	if (Camera == nullptr || DeltaSeconds <= 0.f)
	{
		return;
	}
	if (VRRig != nullptr)
	{
		// The VR simulation: no bob or dip (in a headset nothing moves the head but the head).
		Camera->SetRelativeLocation(FVector(0.f, 0.f, EyeHeight - GetCapsuleComponent()->GetScaledCapsuleHalfHeight()));
		return;
	}
	const UCharacterMovementComponent* Move = GetCharacterMovement();
	const bool bOnGround = Move->IsMovingOnGround();
	const float Speed = static_cast<float>(GetVelocity().Size2D());

	// Head-bob: strength eases toward speed / walk speed while on the ground (web PLAYER.amp, k = 6).
	const float Want = (bOnGround && Speed > 40.f) ? FMath::Min(1.f, Speed / WalkSpeed) : 0.f;
	BobAmount = FMath::Lerp(BobAmount, Want, 1.f - FMath::Exp(-DeltaSeconds * 6.f));
	float Bob = 0.f;
	if (BobAmount > 0.002f)
	{
		BobPhase += DeltaSeconds * FMath::Max(Speed, 120.f) / BobStride;
		Bob = FMath::Sin(BobPhase * 2.f * UE_PI) * BobAmplitude * BobAmount;
	}
	else
	{
		BobPhase = 0.f;
		BobAmount = 0.f;
	}

	// Landing dip: a damped spring (110, 15) back to zero.
	if (DipOffset != 0.f || DipVelocity != 0.f)
	{
		DipVelocity += (-110.f * DipOffset - 15.f * DipVelocity) * DeltaSeconds;
		DipOffset += DipVelocity * DeltaSeconds;
		if (FMath::Abs(DipOffset) < 0.04f && FMath::Abs(DipVelocity) < 0.4f)
		{
			DipOffset = 0.f;
			DipVelocity = 0.f;
		}
	}

	const float HalfHeight = GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	Camera->SetRelativeLocation(FVector(0.f, 0.f, EyeHeight - HalfHeight + Bob + DipOffset));
}

void AWTACharacter::StartVR(bool bHeadset)
{
	if (VRRig != nullptr)
	{
		if (VRRig->IsHeadset() == bHeadset)
		{
			return;
		}
		StopVR();
	}
	VRRig = NewObject<UWTAVRRig>(this, MakeUniqueObjectName(this, UWTAVRRig::StaticClass(), TEXT("WTAVRRig")));
	VRRig->RegisterComponent();
	VRRig->Start(bHeadset);
	if (bSeated)
	{
		VRRig->SetSeated(true, SeatedEyeZ);
	}
	BobPhase = 0.f;
	BobAmount = 0.f;
	DipOffset = 0.f;
	DipVelocity = 0.f;
}

void AWTACharacter::StopVR()
{
	if (VRRig == nullptr)
	{
		return;
	}
	VRRig->Stop();
	VRRig->DestroyComponent();
	VRRig = nullptr;
	if (bSeated)
	{
		Camera->SetRelativeLocation(FVector(0.f, 0.f, SeatedCameraZ));
	}
}

void AWTACharacter::NoteDistanceWalked()
{
	const FVector Location = GetActorLocation();
	if (bHasLastFrameLocation && GetCharacterMovement()->IsMovingOnGround())
	{
		const float Moved = static_cast<float>(FVector::Dist2D(Location, LastFrameLocation));
		// Teleports do not count as walking.
		if (Moved > 0.f && Moved < 300.f)
		{
			if (UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this))
			{
				Progress->NoteDistance(Moved);
			}
		}
	}
	LastFrameLocation = Location;
	bHasLastFrameLocation = true;
}
