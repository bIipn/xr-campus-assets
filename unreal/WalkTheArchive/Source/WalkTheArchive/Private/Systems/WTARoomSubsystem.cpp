// Walk the Archive - which room the player is in.

#include "Systems/WTARoomSubsystem.h"
#include "Systems/WTAContentSubsystem.h"
#include "Core/WTALog.h"
#include "Data/WTATypes.h"
#include "Engine/DataTable.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

namespace
{
	const UWTAContentSubsystem* ContentOf(const UWorld* World)
	{
		const UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
		return GameInstance ? GameInstance->GetSubsystem<UWTAContentSubsystem>() : nullptr;
	}
}

UWTARoomSubsystem* UWTARoomSubsystem::Get(const UObject* WorldContextObject)
{
	if (WorldContextObject == nullptr || GEngine == nullptr)
	{
		return nullptr;
	}
	UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull);
	return World ? World->GetSubsystem<UWTARoomSubsystem>() : nullptr;
}

void UWTARoomSubsystem::EnterRoom(FName RoomId)
{
	if (RoomId.IsNone() || RoomId == CurrentRoom)
	{
		return;
	}
	CurrentRoom = RoomId;
	bCurrentRoomFirstVisit = !Visited.Contains(RoomId);
	Visited.Add(RoomId);
	UE_LOG(LogWTA, Verbose, TEXT("Room: entered '%s'%s"), *RoomId.ToString(), bCurrentRoomFirstVisit ? TEXT(" (first visit)") : TEXT(""));
	OnRoomChanged.Broadcast(RoomId);
}

FName UWTARoomSubsystem::RoomAt(FVector Location) const
{
	const UWTAContentSubsystem* Content = ContentOf(GetWorld());
	const UDataTable* Rooms = Content ? Content->GetTable(EWTATable::Rooms) : nullptr;
	if (Rooms == nullptr)
	{
		return NAME_None;
	}
	FName Nearest = NAME_None;
	float NearestDistSq = TNumericLimits<float>::Max();
	for (const TPair<FName, uint8*>& Pair : Rooms->GetRowMap())
	{
		const FWTARoomRow* Row = reinterpret_cast<const FWTARoomRow*>(Pair.Value);
		if (Row == nullptr)
		{
			continue;
		}
		const FBox Box(Row->BoundsMin, Row->BoundsMax);
		// Rooms are floor rectangles: test XY only so a jump never leaves the room.
		const bool bInsideXY = Location.X >= Box.Min.X && Location.X <= Box.Max.X && Location.Y >= Box.Min.Y && Location.Y <= Box.Max.Y;
		if (bInsideXY)
		{
			return Pair.Key;
		}
		const FVector Clamped(FMath::Clamp(Location.X, Box.Min.X, Box.Max.X), FMath::Clamp(Location.Y, Box.Min.Y, Box.Max.Y), Location.Z);
		const float DistSq = static_cast<float>(FVector::DistSquared2D(Clamped, Location));
		if (DistSq < NearestDistSq)
		{
			NearestDistSq = DistSq;
			Nearest = Pair.Key;
		}
	}
	return Nearest;
}

FName UWTARoomSubsystem::GetStaffForRoom(FName RoomId) const
{
	const UWTAContentSubsystem* Content = ContentOf(GetWorld());
	const FWTARoomRow* Row = Content ? Content->FindRoom(RoomId) : nullptr;
	return Row ? Row->StaffId : NAME_None;
}
