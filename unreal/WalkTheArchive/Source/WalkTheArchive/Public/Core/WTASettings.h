// Walk the Archive - project settings (Project Settings > Game > Walk the Archive).
//
// One soft reference per DataTable, named after the table without "DT_". Defaults point at
// /Game/WTA/Data/DT_<Name>.DT_<Name>; the editor setup writes the same values to
// Config/DefaultGame.ini under [/Script/WalkTheArchive.WTASettings].

#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "UObject/Class.h"
#include "UObject/SoftObjectPtr.h"
#include "Data/WTATypes.h"
#include "WTASettings.generated.h"

class UDataTable;

UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "Walk the Archive"))
class WALKTHEARCHIVE_API UWTASettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UWTASettings();

	/** The class default object: UWTASettings::Get()->Exhibits etc. */
	static const UWTASettings* Get() { return GetDefault<UWTASettings>(); }

	/** Shown under the "Game" heading of Project Settings. */
	virtual FName GetCategoryName() const override { return FName(TEXT("Game")); }

	// --- Data tables -------------------------------------------------------

	UPROPERTY(Config, EditAnywhere, Category = "Data Tables")
	TSoftObjectPtr<UDataTable> Exhibits;

	UPROPERTY(Config, EditAnywhere, Category = "Data Tables")
	TSoftObjectPtr<UDataTable> Books;

	UPROPERTY(Config, EditAnywhere, Category = "Data Tables")
	TSoftObjectPtr<UDataTable> Sources;

	UPROPERTY(Config, EditAnywhere, Category = "Data Tables")
	TSoftObjectPtr<UDataTable> Galleries;

	UPROPERTY(Config, EditAnywhere, Category = "Data Tables")
	TSoftObjectPtr<UDataTable> Subjects;

	UPROPERTY(Config, EditAnywhere, Category = "Data Tables")
	TSoftObjectPtr<UDataTable> Rooms;

	UPROPERTY(Config, EditAnywhere, Category = "Data Tables")
	TSoftObjectPtr<UDataTable> Places;

	UPROPERTY(Config, EditAnywhere, Category = "Data Tables")
	TSoftObjectPtr<UDataTable> Tour;

	UPROPERTY(Config, EditAnywhere, Category = "Data Tables")
	TSoftObjectPtr<UDataTable> Staff;

	UPROPERTY(Config, EditAnywhere, Category = "Data Tables")
	TSoftObjectPtr<UDataTable> StaffRules;

	UPROPERTY(Config, EditAnywhere, Category = "Data Tables")
	TSoftObjectPtr<UDataTable> Facts;

	UPROPERTY(Config, EditAnywhere, Category = "Data Tables")
	TSoftObjectPtr<UDataTable> Lessons;

	UPROPERTY(Config, EditAnywhere, Category = "Data Tables")
	TSoftObjectPtr<UDataTable> Badges;

	UPROPERTY(Config, EditAnywhere, Category = "Data Tables")
	TSoftObjectPtr<UDataTable> Tokens;

	UPROPERTY(Config, EditAnywhere, Category = "Data Tables")
	TSoftObjectPtr<UDataTable> WaxScenes;

	UPROPERTY(Config, EditAnywhere, Category = "Data Tables")
	TSoftObjectPtr<UDataTable> Stations;

	UPROPERTY(Config, EditAnywhere, Category = "Data Tables")
	TSoftObjectPtr<UDataTable> Rides;

	UPROPERTY(Config, EditAnywhere, Category = "Data Tables")
	TSoftObjectPtr<UDataTable> Talks;

	/** DT_Strings: the engine's words in the pack's language (empty = English). */
	UPROPERTY(Config, EditAnywhere, Category = "Data Tables")
	TSoftObjectPtr<UDataTable> Strings;

	// --- Player ------------------------------------------------------------

	/** Where the player stands when the game starts: the forecourt (0, 2400, 87), facing the museum's portico. */
	UPROPERTY(Config, EditAnywhere, Category = "Player")
	FWTAView SpawnView;

	/** Save-game slot for progress (badges, tokens, pages, distance). */
	UPROPERTY(Config, EditAnywhere, Category = "Player")
	FString SaveSlotName = TEXT("WalkTheArchive");

	// --- Client (clients/<name>/campus.json, written here by build_client.py) ---

	/** The client the campus is built for, on the intro menu's kicker ("XRLIBRARIES CAMPUS"). */
	UPROPERTY(Config, EditAnywhere, Category = "Client")
	FString ClientName = TEXT("XR Libraries");

	/** The campus's own name, the intro menu's title. */
	UPROPERTY(Config, EditAnywhere, Category = "Client")
	FString CampusTitle = TEXT("Walk the Archive");

	// --- UI ----------------------------------------------------------------

	/** Default toast time, seconds (web: 3.4). */
	UPROPERTY(Config, EditAnywhere, Category = "UI")
	float ToastSeconds = 3.4f;

	/** How long a room hint stays up, seconds. */
	UPROPERTY(Config, EditAnywhere, Category = "UI")
	float HintSeconds = 6.f;

	/** Show the intro menu on start (off for quick test runs). */
	UPROPERTY(Config, EditAnywhere, Category = "UI")
	bool bShowIntroMenu = true;
};
