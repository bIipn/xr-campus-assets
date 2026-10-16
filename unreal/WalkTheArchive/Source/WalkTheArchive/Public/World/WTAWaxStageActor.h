// Walk the Archive - a Wax Hall stage.
//
// While the player stands inside Trigger (a Pawn-overlap box, half size TriggerExtent), the scene is live:
// PlayTime runs 0..LoopSeconds and loops, and each FWTAWaxLine whose Time has passed becomes the HUD caption
// (AWTAPlayerController::ShowCaption; empty text clears it on exit). After WatchSecondsForCredit seconds inside,
// UWTAProgressSubsystem::NoteWaxScene(SceneId) is called once per visit. The row's Sequence (Level Sequence) is
// played in phase 1; phase 0 only does captions. The editor Python places it at StageLocation/StageYaw and sets
// scene_id and trigger_extent.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Data/WTATypes.h"
#include "WTAWaxStageActor.generated.h"

class UBoxComponent;

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

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void NotifyActorBeginOverlap(AActor* OtherActor) override;
	virtual void NotifyActorEndOverlap(AActor* OtherActor) override;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	/** Copy of the row, read at BeginPlay. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA")
	FWTAWaxSceneRow Scene;

	bool bHasScene = false;
	bool bPlayerInside = false;
	bool bCredited = false;
	float PlayTime = 0.f;
	float WatchSeconds = 0.f;
	int32 LineIndex = -1;
};
