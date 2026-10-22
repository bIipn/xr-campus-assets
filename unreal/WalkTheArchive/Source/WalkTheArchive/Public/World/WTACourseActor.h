// Walk the Archive - a course desk: where a course (a DT_Talks row of kind course) is joined, checked off and
// finished. The training wing's builder marks the course lead's spot (spot__<venue>_f<yaw>); the editor Python
// puts one of these there for every course row, and the lead (the row's Person, a reenactor) stands at it.
// Walk up, the crosshair says "Course · <title>", E opens the course card (AWTAPlayerController::OpenCourse): the
// lead's welcome, the stations as a checklist ticked from the progress, a Go button to each, and once every
// station is finished, the quiz; passing it earns the certificate and the row's badge, as a class does.

#pragma once

#include "CoreMinimal.h"
#include "World/WTAPickActor.h"
#include "Data/WTATypes.h"
#include "WTACourseActor.generated.h"

UCLASS(Blueprintable)
class WALKTHEARCHIVE_API AWTACourseActor : public AWTAPickActor
{
	GENERATED_BODY()

public:
	AWTACourseActor();

	/** DT_Talks row of kind course (editor Python: talk_id). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FName TalkId;

	/** World yaw the course lead faces (editor Python: speaker_yaw, from the spot mesh's name). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	float SpeakerYaw = 0.f;

	/** The lead standing at the desk (spawned at BeginPlay; null when the person is not built). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	AActor* GetLead() const { return Lead; }

	/** The course actor for a venue, if one is in the level. */
	static AWTACourseActor* FindForVenue(const UObject* WorldContext, FName Venue);

	virtual void Interact_Implementation(AWTAPlayerController* Controller) override;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void ReadRow() override;

	void SpawnLead();

	UPROPERTY(Transient)
	TObjectPtr<AActor> Lead;

	FWTATalkRow Row;
	bool bHasRow = false;
};
