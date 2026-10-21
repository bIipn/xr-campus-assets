// Walk the Archive - a Wax Hall stage.
//
// While the player stands inside Trigger (a Pawn-overlap box, half size TriggerExtent), the scene is live:
// PlayTime runs 0..LoopSeconds and loops, and each FWTAWaxLine whose Time has passed becomes the HUD caption
// (AWTAPlayerController::ShowCaption; empty text clears it on exit). After WatchSecondsForCredit seconds inside,
// UWTAProgressSubsystem::NoteWaxScene(SceneId) is called once per visit. The editor Python places the stage at
// StageLocation/StageYaw and sets scene_id and trigger_extent.
//
// Reenactors: at BeginPlay every row Figure whose MetaHuman has been built (/Game/WTA/Characters/<Person>/
// BP_<Person>) is spawned on the stage floor at StageLocation + Offset (rotated by StageYaw), facing StageYaw +
// Yaw, and its body is given a UWTAWaxAnimInstance.
//
// A figure acts while the player is within WakeDistance of the stage and is a wax figure otherwise:
//  - acting: ActTime runs and loops, and each FWTAWaxBeat whose Time has passed is the clip the body plays,
//    crossfading over the beat's Blend; the figure turns to the beat's Yaw over the same time. Props (headsets,
//    tablets, boxes) ride the sockets their keys name and travel between hands when a key hands them over; a
//    prop in a hand sits in the palm and that hand's fingers close round it (UWTAWaxAnimInstance::SetGrip).
//  - wax: the animation instance holds the frame it reached, so each figure freezes mid-gesture in a pose from
//    its own scene, and the meshes stop evaluating (UWTAPeopleLibrary::Freeze). A frozen figure is posed again
//    for a couple of frames whenever one of its meshes changes LOD (see UpdateFigureBones).

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Data/WTATypes.h"
#include "WTAWaxStageActor.generated.h"

class UAnimSequence;
class UBoxComponent;
class UStaticMesh;
class UStaticMeshComponent;
class USkeletalMeshComponent;
class UWTAWaxAnimInstance;

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

	/** Seconds into the current caption loop. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	float GetPlayTime() const { return PlayTime; }

	/** True while the reenactors are acting rather than standing as wax. */
	UFUNCTION(BlueprintPure, Category = "WTA|People")
	bool IsActing() const { return bActing; }

	/** Seconds into the acting loop. */
	UFUNCTION(BlueprintPure, Category = "WTA|People")
	float GetActTime() const { return ActTime; }

	/** The player wakes the scene from this far away, in cm: the hall is alive as you walk up the aisle. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|People")
	float WakeDistance = 1600.f;

	/** Added to WakeDistance before the scene goes back to sleep, so it does not flicker on the boundary. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|People")
	float SleepDistanceSlack = 250.f;

	/** Folder the beats' clips live in: <AnimFolder>/AS_WTA_<Action>. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|People")
	FString AnimFolder = TEXT("/Game/WTA/Characters/Common/Anims/Mocap");

	/** Idle a reenactor falls back to when it has no beats (default: UWTAPeopleLibrary::DefaultIdlePath). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|People")
	TSoftObjectPtr<UAnimSequence> FigurePose;

	/** Added to every figure's yaw. MetaHuman Creator Blueprints face +Y; -90 turns them to the stage's +X. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|People")
	float FigureYawOffset = -90.f;

	/**
	 * How far from facing the aisle a reenactor may be turned, in degrees. The web's camera sat behind the scene
	 * and some figures have their backs to the front; from the aisle that is a person you cannot see, so a bigger
	 * turn is clamped to this.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|People")
	float MaxTurnFromAisle = 100.f;

	/** The reenactors spawned at BeginPlay (destroyed at EndPlay). */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|People")
	TArray<TObjectPtr<AActor>> Figures;

	/** How many times a frozen figure on this stage has been posed again for a new LOD (QA). */
	UFUNCTION(BlueprintPure, Category = "WTA|People")
	int32 GetReposeCount() const { return NumReposes; }

	/** The clip each figure is playing and how far into it, for QA. */
	UFUNCTION(BlueprintPure, Category = "WTA|People")
	FString DescribeActing() const;

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void NotifyActorBeginOverlap(AActor* OtherActor) override;
	virtual void NotifyActorEndOverlap(AActor* OtherActor) override;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void Tick(float DeltaSeconds) override;

	/** Spawn the row's Figures whose MetaHumans exist, give each an animation instance, and build the props. */
	void SpawnFigures();

	/** The clip for a beat's Action, loaded once and kept (null, with one log line, when it has not been built). */
	UAnimSequence* LoadAction(FName Action);

	/** The stage's yaw from its row (the aisle is in front, along it). */
	UFUNCTION(BlueprintPure, Category = "WTA|Wax")
	float GetStageYaw() const { return Scene.StageYaw; }

	/** How many props the scene has (rows of Scene.Props). */
	UFUNCTION(BlueprintPure, Category = "WTA|Wax")
	int32 NumProps() const { return Scene.Props.Num(); }

	/**
	 * For QA: true when prop Index is in a figure's hand right now, with where the prop is, where that hand's
	 * wrist is, how closed the hand is (0..1) and which hand (hand_l / hand_r).
	 */
	UFUNCTION(BlueprintPure, Category = "WTA|Wax")
	bool PropInHand(int32 Index, FVector& OutProp, FVector& OutWrist, float& OutGrip, FName& OutSocket) const;

	/** Wakes the reenactors (bWake) or leaves them holding the frame they reached. */
	void SetActing(bool bWake);

	/** Advances ActTime, starts each figure's current beat, and turns figures toward their beat's yaw. */
	void UpdateBeats(float DeltaSeconds);

	/** Puts every prop where its keys say it is at ActTime. */
	void UpdateProps();

	/**
	 * World transform of one prop key: in a figure's hand (the prop's own frame set in the palm, see the .cpp),
	 * on its head or chest, or standing in the stage's frame. Kind picks how the prop sits in a hand.
	 */
	bool PropKeyTransform(const FWTAWaxPropKey& Key, FName Kind, bool bModelled, FTransform& Out) const;

	/** Closes (or opens) the hand a key names round a prop of Kind: 0 gives the hand back to its clip. */
	void SetKeyGrip(const FWTAWaxPropKey& Key, FName Kind, float Scale) const;

	/**
	 * Every frame, after the figures' LOD syncs pick this frame's LODs and before the figures' meshes tick:
	 * - while acting, every mesh evaluates (nothing is frozen);
	 * - a new wax figure evaluates for SettleSeconds (and MinFramesBeforeFreeze frames) until its face sits on its
	 *   body (UWTAPeopleLibrary::IsFaceOnBody), then freezes; after MaxSecondsBeforeFreeze it freezes anyway;
	 * - a frozen figure whose mesh is about to change LOD thaws, so it evaluates at the new LOD in the same frame
	 *   the LOD is first drawn (each LOD skins with its own bones; unevaluated ones sit at the component origin),
	 *   and freezes again two frames later;
	 * - a figure only freezes on a frame whose LODs match the frame it last evaluated.
	 */
	void UpdateFigureBones();

	/** A figure freezes no sooner than this many frames after it stopped acting. */
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

	/** One reenactor's acting: which beat it is on, and the turn it is part way through. */
	struct FFigurePlay
	{
		TWeakObjectPtr<AActor> Figure;
		TWeakObjectPtr<UWTAWaxAnimInstance> Anim;
		int32 FigureIndex = INDEX_NONE;
		int32 BeatIndex = INDEX_NONE;
		FVector Feet = FVector::ZeroVector;
		float BaseYaw = 0.f;
		float YawFrom = 0.f;
		float YawTo = 0.f;
		float LiftFrom = 0.f;
		float LiftTo = 0.f;
		float TurnSeconds = 0.f;
		float TurnLength = 0.f;
	};
	TArray<FFigurePlay> Plays;

	/** Clips already loaded, by action name (an action that failed to load is remembered as null). */
	UPROPERTY(Transient)
	TMap<FName, TObjectPtr<UAnimSequence>> Clips;

	/** One component per row prop, in the row's order. */
	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> PropParts;

	/** Per row prop: true when it shows a modelled mesh (HandProps or the web's own), false for a stand-in block. */
	TArray<bool> PropModelled;

	uint64 SpawnFrame = 0;
	double SpawnSeconds = 0.0;
	int32 NumReposes = 0;

	/** Copy of the row, read at BeginPlay. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA")
	FWTAWaxSceneRow Scene;

	bool bHasScene = false;
	bool bPlayerInside = false;
	bool bCredited = false;
	bool bActing = false;
	float PlayTime = 0.f;
	float ActTime = 0.f;
	float WatchSeconds = 0.f;
	int32 LineIndex = -1;
	/** This stage was the one the player faces last tick (stages face each other across the aisle; only one speaks). */
	bool bWasActive = false;
};
