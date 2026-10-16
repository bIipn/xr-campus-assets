// Walk the Archive - a framed exhibit, the Freedom to Read board, or a Wax Hall reading card.
// Interact: walk to the row's View and open the catalog card (the controller notes the exhibit as seen).
// Label: "Open - <Title>". Placed by the editor Python from the item__<id> meshes; it sets item_id and pick_extent.

#pragma once

#include "CoreMinimal.h"
#include "World/WTAPickActor.h"
#include "WTAExhibitActor.generated.h"

UCLASS(Blueprintable)
class WALKTHEARCHIVE_API AWTAExhibitActor : public AWTAPickActor
{
	GENERATED_BODY()

public:
	AWTAExhibitActor();

	/** DT_Exhibits row (editor Python: item_id). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FName ItemId;

	virtual void Interact_Implementation(AWTAPlayerController* Controller) override;

protected:
	virtual void ReadRow() override;
};
