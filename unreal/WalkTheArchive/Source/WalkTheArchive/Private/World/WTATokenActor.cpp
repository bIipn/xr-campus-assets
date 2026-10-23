// Walk the Archive - a hidden XR token: a small glowing sphere that spins and bobs when you are near.

#include "World/WTATokenActor.h"
#include "Core/WTAText.h"
#include "Components/SceneComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "Engine/EngineTypes.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/Material.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Systems/WTAContentSubsystem.h"
#include "Systems/WTAProgressSubsystem.h"
#include "UObject/ConstructorHelpers.h"

AWTATokenActor::AWTATokenActor()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = true;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	// Pick volume: Visibility traces only.
	PickSphere = CreateDefaultSubobject<USphereComponent>(TEXT("PickSphere"));
	PickSphere->SetupAttachment(Root);
	PickSphere->InitSphereRadius(40.f);
	PickSphere->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	PickSphere->SetCollisionObjectType(ECC_WorldDynamic);
	PickSphere->SetCollisionResponseToAllChannels(ECR_Ignore);
	PickSphere->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	PickSphere->SetGenerateOverlapEvents(false);
	PickSphere->SetCanEverAffectNavigation(false);
	PickSphere->CanCharacterStepUpOn = ECB_No;
	PickSphere->SetHiddenInGame(true);

	// The visible sphere (engine basic shape, 100 cm diameter, scaled to 25 cm).
	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	Mesh->SetupAttachment(Root);
	Mesh->SetRelativeScale3D(FVector(0.25f, 0.25f, 0.25f));
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mesh->SetGenerateOverlapEvents(false);
	Mesh->SetCanEverAffectNavigation(false);
	Mesh->SetCastShadow(false);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (SphereMesh.Succeeded())
	{
		Mesh->SetStaticMesh(SphereMesh.Object);
	}

	static ConstructorHelpers::FObjectFinder<UMaterial> BaseMaterial(TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	if (BaseMaterial.Succeeded())
	{
		Mesh->SetMaterial(0, BaseMaterial.Object);
	}
}

void AWTATokenActor::BeginPlay()
{
	Super::BeginPlay();

	// Spread the bob phase so neighbouring tokens do not move in lockstep.
	BobPhase = FMath::FRandRange(0.f, BobSeconds);

	if (const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this))
	{
		if (const FWTATokenRow* Row = Content->FindToken(TokenId))
		{
			RideGate = Row->RideGate;
		}
		else
		{
			UE_LOG(LogWTA, Warning, TEXT("%s: no DT_Tokens row '%s'"), *GetName(), *TokenId.ToString());
		}
	}

	// Brass glow. BasicShapeMaterial exposes "Color"; an emissive parameter is set too in case a
	// project material with one is swapped in. Unknown parameters are ignored.
	if (Mesh != nullptr && Mesh->GetMaterial(0) != nullptr)
	{
		GlowMaterial = Mesh->CreateAndSetMaterialInstanceDynamic(0);
		if (GlowMaterial != nullptr)
		{
			GlowMaterial->SetVectorParameterValue(TEXT("Color"), GlowColor);
			GlowMaterial->SetVectorParameterValue(TEXT("EmissiveColor"), GlowColor);
		}
	}

	if (UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this))
	{
		Progress->OnProgressReset.AddUniqueDynamic(this, &AWTATokenActor::HandleProgressReset);
		if (Progress->HasToken(TokenId))
		{
			SetCollected(true);
		}
	}
}

void AWTATokenActor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (bCollected || Mesh == nullptr)
	{
		return;
	}

	// Only animate near the player (the web did the same to save work).
	const APawn* Player = UGameplayStatics::GetPlayerPawn(this, 0);
	if (Player == nullptr)
	{
		return;
	}
	const float DistSq = static_cast<float>(FVector::DistSquared(Player->GetActorLocation(), GetActorLocation()));
	if (DistSq > AnimateWithin * AnimateWithin)
	{
		return;
	}

	BobPhase += DeltaSeconds;
	const float Period = FMath::Max(BobSeconds, 0.1f);
	const float Bob = BobAmplitude * FMath::Sin(BobPhase * 2.f * UE_PI / Period);
	const float Yaw = FMath::Fmod(BobPhase * SpinDegreesPerSecond, 360.f);
	Mesh->SetRelativeLocation(FVector(0.f, 0.f, Bob));
	Mesh->SetRelativeRotation(FRotator(0.f, Yaw, 0.f));
}

FText AWTATokenActor::GetInteractLabel_Implementation() const
{
	return WTAText(TEXT("Collect \u00B7 XR token"));
}

void AWTATokenActor::Interact_Implementation(AWTAPlayerController* Controller)
{
	if (bCollected)
	{
		return;
	}

	// Ride-gated tokens need that ride to be running. Rides are phase 1, so for now they stay out of reach.
	if (!RideGate.IsNone())
	{
		FText RideName = FText::FromName(RideGate);
		if (const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this))
		{
			if (const FWTARideRow* Ride = Content->FindRide(RideGate))
			{
				RideName = Ride->DisplayName;
			}
		}
		if (Controller != nullptr)
		{
			Controller->ShowToast(FText::Format(WTAText(TEXT("Ride the {0} to grab that one!")), RideName));
		}
		return;
	}

	if (UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this))
	{
		Progress->CollectToken(TokenId);
	}
	SetCollected(true);
}

bool AWTATokenActor::GetViewSpot_Implementation(FWTAView& OutView) const
{
	OutView = FWTAView();
	return false;
}

void AWTATokenActor::SetCollected(bool bInCollected)
{
	bCollected = bInCollected;
	SetActorHiddenInGame(bCollected);
	SetActorEnableCollision(!bCollected);
	SetActorTickEnabled(!bCollected);
}

void AWTATokenActor::HandleProgressReset()
{
	SetCollected(false);
}
