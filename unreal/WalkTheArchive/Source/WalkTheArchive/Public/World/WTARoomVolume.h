// Walk the Archive - a room box. When the player's pawn overlaps it, the room subsystem enters RoomId.
// Bounds = a UBoxComponent (root) that overlaps Pawn only (no blocking). OnConstruction applies Extent (half size).
// The editor Python spawns one per DT_Rooms row at the box centre and sets room_id and extent (plus 20 cm so
// neighbouring rooms overlap at doors; the last room entered stays current until a new overlap, as the web did).

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WTARoomVolume.generated.h"

class UBoxComponent;

UCLASS(Blueprintable)
class WALKTHEARCHIVE_API AWTARoomVolume : public AActor
{
	GENERATED_BODY()

public:
	AWTARoomVolume();

	/** DT_Rooms row (editor Python: room_id). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FName RoomId;

	/** Half size in cm (editor Python: extent). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FVector Extent = FVector(300.f, 300.f, 220.f);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	TObjectPtr<UBoxComponent> Bounds;

	virtual void OnConstruction(const FTransform& Transform) override;

	/** Player pawn entered: UWTARoomSubsystem::EnterRoom(RoomId). */
	virtual void NotifyActorBeginOverlap(AActor* OtherActor) override;
};
