// Walk the Archive - a seat: a chair, a bench, a stool. Walk up, the crosshair says "Sit", E sits you down.
//
// The actor stands at the sit point (the top of the cushion, middle of the seat) and SeatYaw is the way a sitter
// faces. The editor Python places one on every seat__<id>_f<yaw> mesh the Blender builders export (actors.py).
// Sitting is the character's business (AWTACharacter::SitAt): the eye settles at a seated height, movement is
// locked, looking and every interaction still work. E on the seat you sit on, Space, or a move stands you up.

#pragma once

#include "CoreMinimal.h"
#include "World/WTAPickActor.h"
#include "WTASeatActor.generated.h"

UCLASS(Blueprintable)
class WALKTHEARCHIVE_API AWTASeatActor : public AWTAPickActor
{
	GENERATED_BODY()

public:
	AWTASeatActor();

	/** The seat's name (editor Python: seat_id), from the mesh it was placed on. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FName SeatId;

	/** World yaw a sitter faces (editor Python: seat_yaw). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	float SeatYaw = 0.f;

	/** The sit point: the actor's location (the cushion's top, its middle). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FVector GetSitPoint() const { return GetActorLocation(); }

	/** True while the player sits on this one. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsOccupied() const;

	virtual FText GetInteractLabel_Implementation() const override;
	virtual void Interact_Implementation(AWTAPlayerController* Controller) override;

protected:
	virtual void ReadRow() override;
};
