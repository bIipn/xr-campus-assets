// Walk the Archive - a ride entrance (coaster, drop, dive).
// Phase 0: Interact opens the ride card (name, card text, note). Riding is phase 1.
// Label: "Ride - <DisplayName>". Editor Python sets ride_id and pick_extent.

#pragma once

#include "CoreMinimal.h"
#include "World/WTAPickActor.h"
#include "WTARideActor.generated.h"

UCLASS(Blueprintable)
class WALKTHEARCHIVE_API AWTARideActor : public AWTAPickActor
{
	GENERATED_BODY()

public:
	AWTARideActor();

	/** DT_Rides row (editor Python: ride_id). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FName RideId;

	virtual void Interact_Implementation(AWTAPlayerController* Controller) override;

protected:
	virtual void ReadRow() override;
};
