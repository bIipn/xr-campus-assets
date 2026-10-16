// Walk the Archive - shared base of the four pick-box actors (exhibit, book, station, ride).
//
// The root is a UBoxComponent named PickBox that blocks ECC_Visibility only (QueryOnly, object type WorldDynamic,
// every other channel Ignore), so hover traces hit it and the player walks through it. OnConstruction applies
// PickExtent (half size in cm), which the editor Python sets as `pick_extent` on every subclass.
// Subclasses fill Label and ViewSpot in RefreshFromData() from their DataTable row and override Interact.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Data/WTATypes.h"
#include "Interaction/WTAInteractable.h"
#include "WTAPickActor.generated.h"

class UBoxComponent;

UCLASS(Abstract, Blueprintable)
class WALKTHEARCHIVE_API AWTAPickActor : public AActor, public IWTAInteractable
{
	GENERATED_BODY()

public:
	AWTAPickActor();

	/** Root pick volume; blocks Visibility traces only. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	TObjectPtr<UBoxComponent> PickBox;

	/** Half size of the pick volume in cm (editor Python: pick_extent). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FVector PickExtent = FVector(50.f, 50.f, 50.f);

	virtual void OnConstruction(const FTransform& Transform) override;

	// IWTAInteractable
	virtual FText GetInteractLabel_Implementation() const override;
	virtual void Interact_Implementation(AWTAPlayerController* Controller) override;
	virtual bool GetViewSpot_Implementation(FWTAView& OutView) const override;

	/** Re-read the row this actor points at (called from BeginPlay; call again after changing the id). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void RefreshFromData();

protected:
	virtual void BeginPlay() override;

	/** Subclasses fill Label and ViewSpot here. The base clears both. */
	virtual void ReadRow();

	/** Hover label shown under the crosshair. */
	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FText Label;

	/** Where to stand to look at this (bValid false = none). */
	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FWTAView ViewSpot;
};
