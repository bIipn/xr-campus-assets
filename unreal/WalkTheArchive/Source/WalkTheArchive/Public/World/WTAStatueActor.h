// A marble statue: one of the campus's MetaHumans, held still in a pose from the mocap clips, every surface
// (skin, eyes, clothes) in white marble and the hair left out, the way a carved figure is. The museum's
// rotunda and steps carry four of them (Pipeline/content/statues.json, spawned by the actors step).
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WTAStatueActor.generated.h"

class UWTAWaxAnimInstance;
class UAnimSequence;

UCLASS(Blueprintable)
class WALKTHEARCHIVE_API AWTAStatueActor : public AActor
{
	GENERATED_BODY()

public:
	AWTAStatueActor();

	/** The person whose likeness this is: a MetaHuman id (/Game/WTA/Characters/<id>/BP_<id>). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FName Person;

	/** The pose: a Wax Hall action (AS_WTA_<action> under the mocap folder), held at Phase of its length. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FName Action = TEXT("think");

	/** Where in the clip (0..1) the figure holds. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA", meta = (ClampMin = "0", ClampMax = "1"))
	float Phase = 0.3f;

	/** The stone: a material applied to every slot of every skeletal mesh. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FSoftObjectPath Marble = FSoftObjectPath(TEXT("/Game/WTA/Materials/M_WTA_Marble.M_WTA_Marble"));

	/** Folder of the retargeted clips (as the Wax Hall stages use). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FString AnimFolder = TEXT("/Game/WTA/Characters/Common/Anims/Mocap");

	/** The spawned MetaHuman actor (none until BeginPlay, or when the person is not built). */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA")
	TObjectPtr<AActor> Figure;

	UFUNCTION(BlueprintCallable, Category = "WTA")
	FString Describe() const;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void Tick(float DeltaSeconds) override;

private:
	void SpawnFigure();
	void DressInMarble(AActor* Carved);

	TWeakObjectPtr<UWTAWaxAnimInstance> Anim;
	int32 FramesHeld = 0;
	bool bFrozen = false;
};
