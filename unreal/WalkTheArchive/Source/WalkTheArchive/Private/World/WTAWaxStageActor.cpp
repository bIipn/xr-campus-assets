// Walk the Archive - a Wax Hall stage: captions loop while the player stands in front of it.

#include "World/WTAWaxStageActor.h"
#include "Components/BoxComponent.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "Engine/EngineTypes.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Systems/WTAContentSubsystem.h"
#include "Systems/WTAProgressSubsystem.h"

namespace
{
	AWTAPlayerController* WaxFindController(const UObject* WorldContext)
	{
		return Cast<AWTAPlayerController>(UGameplayStatics::GetPlayerController(WorldContext, 0));
	}
}

AWTAWaxStageActor::AWTAWaxStageActor()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = true;

	// The watch zone: overlaps pawns only.
	Trigger = CreateDefaultSubobject<UBoxComponent>(TEXT("Trigger"));
	SetRootComponent(Trigger);
	Trigger->SetBoxExtent(TriggerExtent);
	Trigger->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Trigger->SetCollisionObjectType(ECC_WorldDynamic);
	Trigger->SetCollisionResponseToAllChannels(ECR_Ignore);
	Trigger->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	Trigger->SetGenerateOverlapEvents(true);
	Trigger->SetCanEverAffectNavigation(false);
	Trigger->CanCharacterStepUpOn = ECB_No;
	Trigger->SetHiddenInGame(true);
}

void AWTAWaxStageActor::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

	if (Trigger != nullptr)
	{
		Trigger->SetBoxExtent(TriggerExtent, false);
	}
}

void AWTAWaxStageActor::BeginPlay()
{
	Super::BeginPlay();

	bHasScene = false;
	if (const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this))
	{
		if (const FWTAWaxSceneRow* Row = Content->FindWaxScene(SceneId))
		{
			Scene = *Row;
			bHasScene = true;
		}
	}
	if (!bHasScene)
	{
		UE_LOG(LogWTA, Warning, TEXT("%s: no DT_WaxScenes row '%s'"), *GetName(), *SceneId.ToString());
	}
}

void AWTAWaxStageActor::NotifyActorBeginOverlap(AActor* OtherActor)
{
	Super::NotifyActorBeginOverlap(OtherActor);

	const APawn* Pawn = Cast<APawn>(OtherActor);
	if (Pawn == nullptr || !Pawn->IsPlayerControlled())
	{
		return;
	}

	// A fresh loop every visit, like the web: the scene wakes when you walk up to it.
	bPlayerInside = true;
	bCredited = false;
	PlayTime = 0.f;
	WatchSeconds = 0.f;
	LineIndex = -1;
}

void AWTAWaxStageActor::NotifyActorEndOverlap(AActor* OtherActor)
{
	Super::NotifyActorEndOverlap(OtherActor);

	const APawn* Pawn = Cast<APawn>(OtherActor);
	if (Pawn == nullptr || !Pawn->IsPlayerControlled())
	{
		return;
	}

	bPlayerInside = false;
	LineIndex = -1;
	if (AWTAPlayerController* PC = WaxFindController(this))
	{
		PC->ShowCaption(FText::GetEmpty());
	}
}

void AWTAWaxStageActor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (!bPlayerInside || !bHasScene)
	{
		return;
	}

	PlayTime += DeltaSeconds;
	WatchSeconds += DeltaSeconds;

	// Loop length: the row's LoopSeconds, else a little past the last line.
	float LoopSeconds = Scene.LoopSeconds;
	if (LoopSeconds <= 0.f)
	{
		LoopSeconds = 5.f;
		for (const FWTAWaxLine& Line : Scene.Lines)
		{
			LoopSeconds = FMath::Max(LoopSeconds, Line.Time + 5.f);
		}
	}
	if (PlayTime >= LoopSeconds)
	{
		PlayTime = FMath::Fmod(PlayTime, LoopSeconds);
		LineIndex = -1;
	}

	// The caption is the last line whose time has passed.
	int32 NewIndex = -1;
	for (int32 i = 0; i < Scene.Lines.Num(); ++i)
	{
		if (Scene.Lines[i].Time <= PlayTime)
		{
			NewIndex = i;
		}
	}
	if (NewIndex != LineIndex)
	{
		LineIndex = NewIndex;
		if (AWTAPlayerController* PC = WaxFindController(this))
		{
			PC->ShowCaption(LineIndex >= 0 ? Scene.Lines[LineIndex].Text : FText::GetEmpty());
		}
	}

	// Watching for a while counts the scene (Living Historian).
	if (!bCredited && WatchSeconds >= WatchSecondsForCredit)
	{
		bCredited = true;
		if (UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this))
		{
			Progress->NoteWaxScene(SceneId);
		}
	}
}
