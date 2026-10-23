// Walk the Archive - the Lost Stories booth's microphone: "Tell a story".
//
// Stands on the cabin's table over the teller's microphone (bl/stories.py writes where, out/stories/layout.json; the
// editor Python places it). E sits the player in the teller's chair (the AWTASeatActor whose SeatId is TellerSeatId,
// facing the mic) and opens the booth card (UWTAPanelWidget::ShowBooth): record, listen back, keep, again, delete.

#pragma once

#include "CoreMinimal.h"
#include "World/WTAPickActor.h"
#include "WTAStoryMicActor.generated.h"

UCLASS(Blueprintable)
class WALKTHEARCHIVE_API AWTAStoryMicActor : public AWTAPickActor
{
	GENERATED_BODY()

public:
	AWTAStoryMicActor();

	/** The teller's chair: the seat__<id>_f<yaw> mesh's id (editor Python: teller_seat_id). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FName TellerSeatId = TEXT("stories_teller");

	virtual FText GetInteractLabel_Implementation() const override;
	virtual void Interact_Implementation(AWTAPlayerController* Controller) override;

protected:
	virtual void ReadRow() override;
};
