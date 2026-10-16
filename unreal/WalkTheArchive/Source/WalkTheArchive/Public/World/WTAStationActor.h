// Walk the Archive - a hands-on station (sieve, titration, pendulum, bench, diorama, easel).
// Phase 0: Interact walks to the row's View and opens the station panel (kicker, title, steps, intro text).
// The hands-on mechanics come in phase 1+. Label: "<GoLabel> - <Title>". Editor Python sets station_id, pick_extent.

#pragma once

#include "CoreMinimal.h"
#include "World/WTAPickActor.h"
#include "WTAStationActor.generated.h"

UCLASS(Blueprintable)
class WALKTHEARCHIVE_API AWTAStationActor : public AWTAPickActor
{
	GENERATED_BODY()

public:
	AWTAStationActor();

	/** DT_Stations row (editor Python: station_id). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FName StationId;

	virtual void Interact_Implementation(AWTAPlayerController* Controller) override;

protected:
	virtual void ReadRow() override;
};
