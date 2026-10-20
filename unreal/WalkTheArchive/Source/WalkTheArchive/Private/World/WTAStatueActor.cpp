#include "World/WTAStatueActor.h"
#include "Core/WTALog.h"
#include "World/WTAPeopleLibrary.h"
#include "World/WTAWaxAnimInstance.h"
#include "Animation/AnimSequence.h"
#include "Components/PrimitiveComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/World.h"
#include "Materials/MaterialInterface.h"

AWTAStatueActor::AWTAStatueActor()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = true;
	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
}

void AWTAStatueActor::BeginPlay()
{
	Super::BeginPlay();
	SpawnFigure();
}

void AWTAStatueActor::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (Figure != nullptr)
	{
		Figure->Destroy();
		Figure = nullptr;
	}
	Super::EndPlay(EndPlayReason);
}

void AWTAStatueActor::SpawnFigure()
{
	UWorld* World = GetWorld();
	UClass* Class = UWTAPeopleLibrary::LoadMetaHumanClass(Person);
	if (World == nullptr || Class == nullptr)
	{
		UE_LOG(LogWTA, Log, TEXT("%s: statue of '%s' has no built MetaHuman yet"), *GetName(), *Person.ToString());
		return;
	}
	FActorSpawnParameters Params;
	Params.Owner = this;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	// MetaHuman Blueprints face their own +Y: turned by -90 they face the actor's forward, like the staff.
	Figure = World->SpawnActor<AActor>(Class, GetActorLocation(), GetActorRotation() + FRotator(0.f, -90.f, 0.f), Params);
	if (Figure == nullptr)
	{
		return;
	}
	Figure->SetActorEnableCollision(false);     // the pedestal under it is the thing you bump into
	Figure->AttachToActor(this, FAttachmentTransformRules::KeepWorldTransform);

	TInlineComponentArray<USkeletalMeshComponent*> Meshes;
	Figure->GetComponents(Meshes);
	for (USkeletalMeshComponent* Mesh : Meshes)
	{
		if (Mesh != nullptr)
		{
			Mesh->bEnableUpdateRateOptimizations = false;
		}
	}
	UWTAPeopleLibrary::Thaw(Figure);
	DressInMarble(Figure);

	// The body runs the Wax Hall's animation instance: play the clip from Phase, then hold that frame.
	if (USkeletalMeshComponent* Body = UWTAPeopleLibrary::FindBody(Figure))
	{
		Body->SetAnimationMode(EAnimationMode::AnimationBlueprint);
		Body->SetAnimInstanceClass(UWTAWaxAnimInstance::StaticClass());
		UWTAWaxAnimInstance* Instance = Cast<UWTAWaxAnimInstance>(Body->GetAnimInstance());
		Anim = Instance;
		const FString Name = FString::Printf(TEXT("AS_WTA_%s"), *Action.ToString());
		UAnimSequence* Clip = Cast<UAnimSequence>(FSoftObjectPath(FString::Printf(TEXT("%s/%s.%s"), *AnimFolder, *Name, *Name)).TryLoad());
		if (Clip == nullptr)
		{
			Clip = Cast<UAnimSequence>(FSoftObjectPath(UWTAPeopleLibrary::DefaultIdlePath).TryLoad());
		}
		if (Instance != nullptr && Clip != nullptr)
		{
			Instance->PlayClip(Clip, true, 1.f, FMath::Clamp(Phase, 0.f, 1.f) * Clip->GetPlayLength(), 0.f);
			Instance->Hold(true);
		}
	}
}

void AWTAStatueActor::DressInMarble(AActor* Carved)
{
	UMaterialInterface* Stone = Cast<UMaterialInterface>(Marble.TryLoad());
	if (Stone == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("%s: no marble material at %s; the statue keeps its colours"), *GetName(), *Marble.ToString());
	}
	TInlineComponentArray<UPrimitiveComponent*> Parts;
	Carved->GetComponents(Parts);
	for (UPrimitiveComponent* Part : Parts)
	{
		if (Part == nullptr)
		{
			continue;
		}
		// Hair, brows, lashes and fuzz are groom components: a carved figure has none (the scalp is part of the face).
		if (Part->GetClass()->GetName().Contains(TEXT("Groom")))
		{
			Part->SetVisibility(false, true);
			Part->SetHiddenInGame(true, true);
			continue;
		}
		if (Stone != nullptr)
		{
			for (int32 Slot = 0; Slot < Part->GetNumMaterials(); ++Slot)
			{
				Part->SetMaterial(Slot, Stone);
			}
		}
		Part->SetCastShadow(true);
	}
}

void AWTAStatueActor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	// The figure is not frozen the way a sleeping Wax Hall stage freezes its reenactors: a frozen skeleton keeps
	// only the bones its LOD evaluated, and a statue is walked right up to. Holding the clip costs a few
	// evaluations a frame and is always right at every LOD. Nothing to do here after the first frames settle.
	if (++FramesHeld >= 12)
	{
		bFrozen = true;
		SetActorTickEnabled(false);
	}
}

FString AWTAStatueActor::Describe() const
{
	return FString::Printf(TEXT("%s: %s as %s at %.2f, %s"), *GetName(), *Person.ToString(), *Action.ToString(), Phase,
		Figure != nullptr ? (bFrozen ? TEXT("held") : TEXT("settling")) : TEXT("not built"));
}
