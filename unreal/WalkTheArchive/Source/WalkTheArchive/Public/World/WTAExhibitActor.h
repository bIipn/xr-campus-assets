// Walk the Archive - a framed exhibit, the Freedom to Read board, or a Wax Hall reading card.
// Interact: walk to the row's View and open the catalog card (the controller notes the exhibit as seen).
// Label: "Open - <Title>". Placed by the editor Python from the item__<id> meshes; it sets item_id and pick_extent.
// When the season folder has a picture for the row (Saved/Season/art/<id>.png), BeginPlay hangs it over the frame's
// baked artwork: an unlit plane the row's Size at its Location, facing its Yaw, so a swapped exhibit shows on the
// wall as well as on its card.

#pragma once

#include "CoreMinimal.h"
#include "World/WTAPickActor.h"
#include "WTAExhibitActor.generated.h"

class UStaticMeshComponent;

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

	/** An exhibit stops calling you over once its card has been opened. */
	virtual bool IsAlreadySeen() const override;

	/** Hang this season's picture over the frame (or take it down when the season has none). BeginPlay does it;
	    call it again after UWTAContentSubsystem::ReloadTables. Returns true when a picture hangs. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	bool HangSeasonPicture();

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool HasSeasonPicture() const { return SeasonPlane != nullptr; }

protected:
	virtual void BeginPlay() override;
	virtual void ReadRow() override;

	/** The season's picture over the frame (null when the season has none for this row). */
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> SeasonPlane;
};
