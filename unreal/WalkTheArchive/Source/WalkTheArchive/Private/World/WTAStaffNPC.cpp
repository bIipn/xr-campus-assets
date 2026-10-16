// Walk the Archive - a virtual staff member with a placeholder body until a MetaHuman is assigned.

#include "World/WTAStaffNPC.h"
#include "Components/CapsuleComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/ChildActorComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "Engine/EngineTypes.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/Material.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Systems/WTAContentSubsystem.h"
#include "UObject/ConstructorHelpers.h"

AWTAStaffNPC::AWTAStaffNPC()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = true;

	// Staff stand still; no AI controller, no controller-driven rotation.
	AutoPossessAI = EAutoPossessAI::Disabled;
	bUseControllerRotationYaw = false;
	bUseControllerRotationPitch = false;
	bUseControllerRotationRoll = false;
	if (UCharacterMovementComponent* Movement = GetCharacterMovement())
	{
		Movement->bOrientRotationToMovement = false;
		Movement->bUseControllerDesiredRotation = false;
	}

	// The capsule keeps the Pawn preset (blocks the player) and additionally blocks Visibility so hover traces hit it.
	UCapsuleComponent* Capsule = GetCapsuleComponent();
	Capsule->InitCapsuleSize(30.f, 90.f);
	Capsule->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);

	// Hide the (empty) skeletal mesh slot; it has no asset in phase 0.
	if (USkeletalMeshComponent* Skel = GetMesh())
	{
		Skel->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	}

	// Placeholder: a 100 cm engine cylinder scaled to a 60 x 180 cm body, centred on the capsule.
	PlaceholderBody = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PlaceholderBody"));
	PlaceholderBody->SetupAttachment(Capsule);
	PlaceholderBody->SetRelativeLocation(FVector::ZeroVector);
	PlaceholderBody->SetRelativeScale3D(FVector(0.6f, 0.6f, 1.8f));
	PlaceholderBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	PlaceholderBody->SetGenerateOverlapEvents(false);
	PlaceholderBody->SetCanEverAffectNavigation(false);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMesh(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (CylinderMesh.Succeeded())
	{
		PlaceholderBody->SetStaticMesh(CylinderMesh.Object);
	}
	static ConstructorHelpers::FObjectFinder<UMaterial> BaseMaterial(TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	if (BaseMaterial.Succeeded())
	{
		PlaceholderBody->SetMaterial(0, BaseMaterial.Object);
	}

	// MetaHuman child (empty until DT_Staff.MetaHuman is set).
	MetaHumanChild = CreateDefaultSubobject<UChildActorComponent>(TEXT("MetaHumanChild"));
	MetaHumanChild->SetupAttachment(Capsule);
	MetaHumanChild->SetRelativeLocation(FVector::ZeroVector);

	// Floating name, 20 cm above the capsule top.
	NameLabel = CreateDefaultSubobject<UTextRenderComponent>(TEXT("NameLabel"));
	NameLabel->SetupAttachment(Capsule);
	NameLabel->SetRelativeLocation(FVector(0.f, 0.f, 110.f));
	NameLabel->SetHorizontalAlignment(EHTA_Center);
	NameLabel->SetVerticalAlignment(EVRTA_TextBottom);
	NameLabel->SetWorldSize(16.f);
	NameLabel->SetTextRenderColor(FColor(205, 169, 97));
	NameLabel->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	NameLabel->SetGenerateOverlapEvents(false);
	NameLabel->SetCanEverAffectNavigation(false);
	NameLabel->SetCastShadow(false);
}

void AWTAStaffNPC::BeginPlay()
{
	Super::BeginPlay();

	HomeRotation = GetActorRotation();
	ApplyStaffRow();
}

void AWTAStaffNPC::ApplyStaffRow()
{
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	const FWTAStaffRow* Row = Content ? Content->FindStaff(StaffId) : nullptr;
	if (Row == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("%s: no DT_Staff row '%s'"), *GetName(), *StaffId.ToString());
		if (NameLabel != nullptr)
		{
			NameLabel->SetText(FText::FromName(StaffId));
		}
		return;
	}

	DisplayName = Row->DisplayName;
	StaffRole = Row->Role;
	Color = Row->Color;
	TalkView = Row->TalkView;

	if (NameLabel != nullptr)
	{
		NameLabel->SetText(DisplayName);
	}

	// Tint the placeholder with the staff colour.
	if (PlaceholderBody != nullptr && PlaceholderBody->GetMaterial(0) != nullptr)
	{
		if (UMaterialInstanceDynamic* Tint = PlaceholderBody->CreateAndSetMaterialInstanceDynamic(0))
		{
			Tint->SetVectorParameterValue(TEXT("Color"), Color);
		}
	}

	// MetaHuman: spawn the row's Blueprint as a child actor and hide the placeholder.
	bool bHasMetaHuman = false;
	if (MetaHumanChild != nullptr)
	{
		UClass* MetaHumanClass = Row->MetaHuman.IsNull() ? nullptr : Row->MetaHuman.LoadSynchronous();
		if (MetaHumanClass != nullptr)
		{
			if (MetaHumanChild->GetChildActorClass() != MetaHumanClass)
			{
				MetaHumanChild->SetChildActorClass(MetaHumanClass);
			}
			if (AActor* Child = MetaHumanChild->GetChildActor())
			{
				// A Character Blueprint has its origin at the capsule centre; a plain actor has it at the feet.
				const bool bIsCharacter = Child->IsA<ACharacter>();
				const float HalfHeight = GetCapsuleComponent() ? GetCapsuleComponent()->GetScaledCapsuleHalfHeight() : 90.f;
				MetaHumanChild->SetRelativeLocation(bIsCharacter ? FVector::ZeroVector : FVector(0.f, 0.f, -HalfHeight));

				// Our capsule does all the colliding; the child must not block the player or steal hover traces.
				TInlineComponentArray<UPrimitiveComponent*> Prims;
				Child->GetComponents(Prims);
				for (UPrimitiveComponent* Prim : Prims)
				{
					if (Prim != nullptr)
					{
						Prim->SetCollisionEnabled(ECollisionEnabled::NoCollision);
					}
				}
				bHasMetaHuman = true;
			}
		}
		else if (MetaHumanChild->GetChildActorClass() != nullptr)
		{
			MetaHumanChild->SetChildActorClass(nullptr);
		}
	}

	if (PlaceholderBody != nullptr)
	{
		PlaceholderBody->SetVisibility(!bHasMetaHuman, true);
	}
}

void AWTAStaffNPC::Talk(const FText& Text)
{
	const UWorld* World = GetWorld();
	if (World == nullptr)
	{
		return;
	}
	const float Seconds = FMath::Clamp(static_cast<float>(Text.ToString().Len()) / 16.f, 1.2f, 7.f);
	TalkUntil = World->GetTimeSeconds() + Seconds;
}

bool AWTAStaffNPC::IsTalking() const
{
	const UWorld* World = GetWorld();
	return World != nullptr && TalkUntil > World->GetTimeSeconds();
}

void AWTAStaffNPC::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	const APawn* Player = UGameplayStatics::GetPlayerPawn(this, 0);

	// Face the player when near, otherwise drift back home. Exponential ease, yaw only.
	float TargetYaw = HomeRotation.Yaw;
	if (Player != nullptr)
	{
		FVector ToPlayer = Player->GetActorLocation() - GetActorLocation();
		ToPlayer.Z = 0.f;
		const float DistSq = ToPlayer.SizeSquared();
		if (DistSq > 1.f && DistSq < LookAtDistance * LookAtDistance)
		{
			TargetYaw = ToPlayer.Rotation().Yaw;
		}
	}
	const float CurrentYaw = GetActorRotation().Yaw;
	const float Delta = FRotator::NormalizeAxis(TargetYaw - CurrentYaw);
	const float Alpha = 1.f - FMath::Exp(-TurnRate * DeltaSeconds);
	SetActorRotation(FRotator(0.f, CurrentYaw + Delta * Alpha, 0.f));

	// The name label always faces the camera.
	if (NameLabel != nullptr)
	{
		if (const APlayerCameraManager* Camera = UGameplayStatics::GetPlayerCameraManager(this, 0))
		{
			FVector ToCamera = Camera->GetCameraLocation() - NameLabel->GetComponentLocation();
			ToCamera.Z = 0.f;
			if (ToCamera.SizeSquared() > 1.f)
			{
				NameLabel->SetWorldRotation(ToCamera.Rotation());
			}
		}
	}
}

FText AWTAStaffNPC::GetInteractLabel_Implementation() const
{
	if (DisplayName.IsEmpty())
	{
		return FText::FromString(TEXT("Ask"));
	}
	return FText::Format(FText::FromString(TEXT("Ask {0}")), DisplayName);
}

void AWTAStaffNPC::Interact_Implementation(AWTAPlayerController* Controller)
{
	if (Controller == nullptr)
	{
		return;
	}
	Controller->OpenStaffChat(StaffId);
}

bool AWTAStaffNPC::GetViewSpot_Implementation(FWTAView& OutView) const
{
	OutView = TalkView;
	return TalkView.bValid;
}
