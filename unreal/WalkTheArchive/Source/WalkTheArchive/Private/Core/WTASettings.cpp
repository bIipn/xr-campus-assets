// Walk the Archive - project settings defaults.
// DefaultGame.ini can override every value under [/Script/WalkTheArchive.WTASettings].

#include "Core/WTASettings.h"
#include "Engine/DataTable.h"
#include "UObject/SoftObjectPath.h"

namespace
{
	/** /Game/WTA/Data/DT_<Name>.DT_<Name> as a soft reference. */
	TSoftObjectPtr<UDataTable> TableRef(const TCHAR* Name)
	{
		const FString Path = FString::Printf(TEXT("/Game/WTA/Data/DT_%s.DT_%s"), Name, Name);
		return TSoftObjectPtr<UDataTable>(FSoftObjectPath(Path));
	}
}

UWTASettings::UWTASettings()
{
	Exhibits   = TableRef(TEXT("Exhibits"));
	Books      = TableRef(TEXT("Books"));
	Sources    = TableRef(TEXT("Sources"));
	Galleries  = TableRef(TEXT("Galleries"));
	Subjects   = TableRef(TEXT("Subjects"));
	Rooms      = TableRef(TEXT("Rooms"));
	Places     = TableRef(TEXT("Places"));
	Tour       = TableRef(TEXT("Tour"));
	Staff      = TableRef(TEXT("Staff"));
	StaffRules = TableRef(TEXT("StaffRules"));
	Facts      = TableRef(TEXT("Facts"));
	Lessons    = TableRef(TEXT("Lessons"));
	Badges     = TableRef(TEXT("Badges"));
	Tokens     = TableRef(TEXT("Tokens"));
	WaxScenes  = TableRef(TEXT("WaxScenes"));
	Stations   = TableRef(TEXT("Stations"));
	Rides      = TableRef(TEXT("Rides"));

	// The forecourt: on the stone path 6 m short of the museum's steps (the grounds lie 0.75 m below the floors),
	// looking north at the portico (web yaw 0 = UE yaw -90). DefaultGame.ini can override it.
	SpawnView.Location = FVector(0.f, 2400.f, 87.f);
	SpawnView.Yaw = -90.f;
	SpawnView.Pitch = 4.584f;
	SpawnView.bValid = true;
}
