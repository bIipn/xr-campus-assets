// Walk the Archive - a Wax Hall stage: captions loop while the player stands in front of it.

#include "World/WTAWaxStageActor.h"
#include "Animation/AnimSequence.h"
#include "Components/BoxComponent.h"
#include "Components/LODSyncComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "Engine/EngineTypes.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Systems/WTAContentSubsystem.h"
#include "Systems/WTAProgressSubsystem.h"
#include "TimerManager.h"
#include "World/WTAPeopleLibrary.h"

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

	FigurePose = TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(UWTAPeopleLibrary::DefaultIdlePath));
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
		return;
	}
	SpawnFigures();
}

void AWTAWaxStageActor::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	FigureBones.Reset();
	for (AActor* Figure : Figures)
	{
		if (IsValid(Figure))
		{
			Figure->Destroy();
		}
	}
	Figures.Reset();
	Super::EndPlay(EndPlayReason);
}

void AWTAWaxStageActor::SpawnFigures()
{
	UWorld* World = GetWorld();
	if (World == nullptr || Scene.Figures.Num() == 0)
	{
		return;
	}
	UAnimSequence* Pose = FigurePose.LoadSynchronous();
	const FRotator StageRotation(0.f, Scene.StageYaw, 0.f);
	int32 NotBuilt = 0;
	for (const FWTAWaxFigure& Figure : Scene.Figures)
	{
		UClass* Class = UWTAPeopleLibrary::LoadMetaHumanClass(Figure.Person);
		if (Class == nullptr)
		{
			++NotBuilt;
			continue;
		}
		const FVector Location = Scene.StageLocation + StageRotation.RotateVector(Figure.Offset);
		const FRotator Rotation(0.f, Scene.StageYaw + Figure.Yaw + FigureYawOffset, 0.f);
		FActorSpawnParameters Params;
		Params.Owner = this;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		AActor* Person = World->SpawnActor<AActor>(Class, Location, Rotation, Params);
		if (Person == nullptr)
		{
			continue;
		}
		// Wax figures stand behind the rope: nothing to collide with or hover.
		Person->SetActorEnableCollision(false);
		if (Pose != nullptr)
		{
			UWTAPeopleLibrary::PlayPose(Person, Pose, false, UWTAPeopleLibrary::PersonPhase(Figure.Person) * Pose->GetPlayLength());
		}
		Figures.Add(Person);
	}
	if (NotBuilt > 0)
	{
		UE_LOG(LogWTA, Log, TEXT("%s: %d of %d reenactors not built yet"), *GetName(), NotBuilt, Scene.Figures.Num());
	}
	// Let the held pose evaluate (body, then the face, clothes and grooms that follow it; PlayPose makes that happen
	// even off screen), then freeze the bones (UpdateFigureBones, every frame from now on).
	SpawnFrame = GFrameCounter;
	SpawnSeconds = World->GetTimeSeconds();
	FigureBones.Reset();
	for (AActor* Person : Figures)
	{
		FFigureBones& Bones = FigureBones.AddDefaulted_GetRef();
		Bones.Figure = Person;
		TInlineComponentArray<USkeletalMeshComponent*> Meshes;
		Person->GetComponents(Meshes);
		for (USkeletalMeshComponent* Mesh : Meshes)
		{
			if (Mesh != nullptr)
			{
				Bones.Meshes.Add(Mesh);
				Bones.PosedLOD.Add(INDEX_NONE);
				// This stage decides each frame whether the mesh evaluates, so it ticks before the mesh...
				Mesh->PrimaryComponentTick.AddPrerequisite(this, PrimaryActorTick);
			}
		}
		// ...and after the figure's LOD sync, which picks the frame's LOD for every mesh it syncs.
		if (ULODSyncComponent* Sync = Person->FindComponentByClass<ULODSyncComponent>())
		{
			PrimaryActorTick.AddPrerequisite(Sync, Sync->PrimaryComponentTick);
		}
	}
}

void AWTAWaxStageActor::UpdateFigureBones()
{
	const UWorld* World = GetWorld();
	if (World == nullptr || FigureBones.Num() == 0)
	{
		return;
	}
	// A slow start (first launch: shaders compiling, meshes streaming) can fit only a frame or two into the settle
	// time; a face frozen before it copied the body's head and neck keeps its reference pose under a posed head and
	// sags. So a new figure freezes after SettleSeconds and MinFramesBeforeFreeze frames, once its face sits on its
	// body, or after MaxSecondsBeforeFreeze whatever the face says.
	const double Age = World->GetTimeSeconds() - SpawnSeconds;
	const bool bSettleTimeOver = Age >= SettleSeconds && GFrameCounter - SpawnFrame >= static_cast<uint64>(MinFramesBeforeFreeze);
	const bool bOutOfTime = Age > MaxSecondsBeforeFreeze;
	for (FFigureBones& Bones : FigureBones)
	{
		AActor* Figure = Bones.Figure.Get();
		if (!IsValid(Figure))
		{
			continue;
		}
		if (Bones.bFrozen)
		{
			// About to be drawn at a LOD its bones were not evaluated at: evaluate this frame (the meshes tick after
			// this stage), and a couple more, then freeze again.
			bool bLODChange = false;
			for (int32 i = 0; i < Bones.Meshes.Num() && !bLODChange; ++i)
			{
				const USkeletalMeshComponent* Mesh = Bones.Meshes[i].Get();
				bLODChange = Mesh != nullptr && UWTAPeopleLibrary::NextLOD(Mesh) != Bones.PosedLOD[i];
			}
			if (bLODChange)
			{
				UWTAPeopleLibrary::Thaw(Figure);
				Bones.bFrozen = false;
				Bones.EvalFrames = 0;
				++NumReposes;
			}
			continue;
		}

		// Evaluating: the frame before this one posed every mesh at its LOD of that frame (GetPredictedLODLevel,
		// which this frame's tick has not updated yet).
		++Bones.EvalFrames;
		float Gap = 0.f;
		const bool bFaceOn = UWTAPeopleLibrary::IsFaceOnBody(Figure, Gap);
		const bool bReady = Bones.bEverFrozen ? (Bones.EvalFrames >= 2 && (bFaceOn || Bones.EvalFrames > 30))
			: ((bSettleTimeOver && bFaceOn) || bOutOfTime);
		if (!bReady)
		{
			continue;
		}
		// Freeze only when this frame keeps every mesh at the LOD it was just posed at.
		bool bSteady = true;
		for (int32 i = 0; i < Bones.Meshes.Num() && bSteady; ++i)
		{
			const USkeletalMeshComponent* Mesh = Bones.Meshes[i].Get();
			bSteady = Mesh == nullptr || UWTAPeopleLibrary::NextLOD(Mesh) == Mesh->GetPredictedLODLevel();
		}
		if (!bSteady)
		{
			continue;
		}
		for (int32 i = 0; i < Bones.Meshes.Num(); ++i)
		{
			const USkeletalMeshComponent* Mesh = Bones.Meshes[i].Get();
			Bones.PosedLOD[i] = Mesh != nullptr ? Mesh->GetPredictedLODLevel() : INDEX_NONE;
		}
		if (!bFaceOn)
		{
			UE_LOG(LogWTA, Warning, TEXT("%s: %s froze with its face %.1f cm off its head"), *GetName(), *Figure->GetName(), Gap);
		}
		UWTAPeopleLibrary::Freeze(Figure);
		Bones.bFrozen = true;
		Bones.bEverFrozen = true;
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

	// Walking up to a scene shows its museum plaque; E opens the full story.
	if (bHasScene)
	{
		if (AWTAPlayerController* PC = WaxFindController(this))
		{
			PC->SetStageStory(Scene.ItemId.IsNone() ? SceneId : Scene.ItemId, true);
		}
	}
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
		if (bHasScene)
		{
			PC->SetStageStory(Scene.ItemId.IsNone() ? SceneId : Scene.ItemId, false);
		}
	}
}

void AWTAWaxStageActor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	UpdateFigureBones();

	if (!bPlayerInside || !bHasScene)
	{
		bWasActive = false;
		return;
	}

	// Scenes face each other across the aisle, so the player can stand in two triggers at once: only the scene
	// the camera faces speaks, and it starts its narration from the first line when the player turns to it.
	const AWTAPlayerController* Watcher = WaxFindController(this);
	const FName MyStory = Scene.ItemId.IsNone() ? SceneId : Scene.ItemId;
	if (Watcher != nullptr && Watcher->GetActiveStageStory() != MyStory)
	{
		bWasActive = false;
		return;
	}
	if (!bWasActive)
	{
		bWasActive = true;
		PlayTime = 0.f;
		LineIndex = -1;
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
