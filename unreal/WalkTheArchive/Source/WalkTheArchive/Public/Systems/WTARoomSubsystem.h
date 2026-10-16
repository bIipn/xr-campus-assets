// Walk the Archive - which room the player is in.
//
// AWTARoomVolume calls EnterRoom on overlap; EnterRoom ignores re-entering the current room, otherwise sets
// CurrentRoom, sets bCurrentRoomFirstVisit (true the first time this run) and broadcasts OnRoomChanged. The
// controller then shows the room label and, on a first visit, the row's Sub as a hint. RoomAt(Location) answers
// from the DT_Rooms boxes (the containing box, else the nearest) for callers without overlaps.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "WTARoomSubsystem.generated.h"

/** The current room changed. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FWTARoomChanged, FName, RoomId);

UCLASS()
class WALKTHEARCHIVE_API UWTARoomSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category = "WTA", meta = (WorldContext = "WorldContextObject"))
	static UWTARoomSubsystem* Get(const UObject* WorldContextObject);

	/** The player entered a room (no-op when it is already current). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void EnterRoom(FName RoomId);

	UFUNCTION(BlueprintPure, Category = "WTA")
	FName GetCurrentRoom() const { return CurrentRoom; }

	/** Room whose DT_Rooms box contains Location, else the nearest box; NAME_None with no rooms. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FName RoomAt(FVector Location) const;

	/** True once the room has been entered this run. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	bool HasVisited(FName RoomId) const { return Visited.Contains(RoomId); }

	/** True while handling OnRoomChanged for a room entered for the first time. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsFirstVisit() const { return bCurrentRoomFirstVisit; }

	/** DT_Rooms[RoomId].StaffId (the "Ask <name>" staff for that room), or NAME_None. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FName GetStaffForRoom(FName RoomId) const;

	UPROPERTY(BlueprintAssignable, Category = "WTA")
	FWTARoomChanged OnRoomChanged;

protected:
	FName CurrentRoom;
	TSet<FName> Visited;
	bool bCurrentRoomFirstVisit = false;
};
