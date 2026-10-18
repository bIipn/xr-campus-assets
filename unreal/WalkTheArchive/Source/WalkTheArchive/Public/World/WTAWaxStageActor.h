// Walk the Archive - a Wax Hall stage.
//
// While the player stands inside Trigger (a Pawn-overlap box, half size TriggerExtent), the scene is live:
// PlayTime runs 0..LoopSeconds and loops, and each FWTAWaxLine whose Time has passed becomes the HUD caption
// (AWTAPlayerController::ShowCaption; empty text clears it on exit). After WatchSecondsForCredit seconds inside,
// UWTAProgressSubsystem::NoteWaxScene(SceneId) is called once per visit. The row's Sequence (Level Sequence) is
// played in phase 1; phase 0 only does captions. The editor Python places it at StageLocation/StageYaw and sets
// scene_id and trigger_extent.
// Reenactors: at BeginPlay every row Figure whose MetaHuman has been built (/Game/WTA/Characters/<Person>/
// BP_<Person>) is spawned on the stage floor at StageLocation + Offset (rotated by StageYaw), facing StageYaw + Yaw,
// posed on its own frame of FigurePose, and frozen about 1.5 seconds later like a wax figure. A frozen figure is
// posed again for a couple of frames whenever one of its meshes changes LOD (see UpdateFigureBones).

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Data/WTATypes.h"
#include "WTAWaxStageActor.generated.h"

class UAnimSequence;
class UBoxComponent;
class USkeletalMeshComponent;

UCLASS(Blueprintable)
class WALKTHEARCHIVE_API AWTAWaxStageActor : public AActor
{
	GENERATED_BODY()

public:
	AWTAWaxStageActor();

	/** DT_WaxScenes row (editor Python: scene_id). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FName SceneId;

	/** Half size of the watch zone in cm (editor Python: trigger_extent). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FVector TriggerExtent = FVector(400.f, 300.f, 220.f);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	TObjectPtr<UBoxComponent> Trigger;

	/** Seconds inside before the scene counts as watched (web: 5). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float WatchSecondsForCredit = 5.f;

	/** True while the player is inside the trigger. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsLive() const { return bPlayerInside; }

	/** Seconds into the current loop. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	float GetPlayTime() const { return PlayTime; }

	/** Idle the reenactors each hold one frame of (default: UWTAPeopleLibrary::DefaultIdlePath). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|People")
	TSoftObjectPtr<UAnimSequence> FigurePose;

	/** Added to every figure's yaw. MetaHuman Creator Blueprints face +Y; -90 turns them to the stage's +X. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|People")
	float FigureYawOffset = -90.f;

	/** The reenactors spawned at BeginPlay (destroyed at EndPlay). */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|People")
	TArray<TObjectPtr<AActor>> Figures;

	/** How many times a frozen figure on this stage has been posed again for a new LOD (QA). */
	UFUNCTION(BlueprintPure, Category = "WTA|People")
	int32 GetReposeCount() const { return NumReposes; }

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void NotifyActorBeginOverlap(AActor* OtherActor) override;
	virtual void NotifyActorEndOverlap(AActor* OtherActor) override;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void Tick(float DeltaSeconds) override;

	/** Spawn the row's Figures whose MetaHumans exist and pose them. */
	void SpawnFigures();

	/**
	 * Every frame, after the figures' LOD syncs pick this frame's LODs and before the figures' meshes tick:
	 * - a new figure evaluates for SettleSeconds (and MinFramesBeforeFreeze frames) until its face sits on its body
	 *   (UWTAPeopleLibrary::IsFaceOnBody), then freezes; after MaxSecondsBeforeFreeze it freezes anyway (warning);
	 * - a frozen figure whose mesh is about to change LOD thaws, so it evaluates at the new LOD in the same frame the
	 *   LOD is first drawn (each LOD skins with its own bones; unevaluated ones sit at the feet), and freezes again
	 *   two frames later;
	 * - a figure only freezes on a frame whose LODs match the frame it last evaluated.
	 */
	void UpdateFigureBones();

	/** A figure freezes no sooner than this many frames after it was spawned and posed. */
	UPROPERTY(EditAnywhere, Category = "WTA|People")
	int32 MinFramesBeforeFreeze = 10;

	/** ...and no sooner than this many seconds. */
	UPROPERTY(EditAnywhere, Category = "WTA|People")
	float SettleSeconds = 1.5f;

	/** Give up waiting for a face to settle after this many seconds and freeze anyway. */
	UPROPERTY(EditAnywhere, Category = "WTA|People")
	float MaxSecondsBeforeFreeze = 15.f;

	/** One reenactor's skeletal meshes and the LOD each was last evaluated at while frozen. */
	struct FFigureBones
	{
		TWeakObjectPtr<AActor> Figure;
		TArray<TWeakObjectPtr<USkeletalMeshComponent>> Meshes;
		TArray<int32> PosedLOD;
		bool bFrozen = false;
		bool bEverFrozen = false;
		/** Frames evaluated since it was spawned or last thawed. */
		int32 EvalFrames = 0;
	};
	TArray<FFigureBones> FigureBones;
	uint64 SpawnFrame = 0;
	double SpawnSeconds = 0.0;
	int32 NumReposes = 0;

	/** Copy of the row, read at BeginPlay. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA")
	FWTAWaxSceneRow Scene;

	bool bHasScene = false;
	bool bPlayerInside = false;
	bool bCredited = false;
	float PlayTime = 0.f;
	float WatchSeconds = 0.f;
	int32 LineIndex = -1;
	/** This stage was the one the player faces last tick (stages face each other across the aisle; only one speaks). */
	bool bWasActive = false;
};
