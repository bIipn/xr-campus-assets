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

	// The web lobby spawn: (0, -0.7) m looking into the museum (web yaw 0 = UE yaw -90), pitch 0.02 rad.
	SpawnView.Location = FVector(0.f, -70.f, 162.f);
	SpawnView.Yaw = -90.f;
	SpawnView.Pitch = 1.146f;
	SpawnView.bValid = true;
}
