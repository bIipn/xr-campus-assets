// Walk the Archive - the content tables.
//
// Loads every DataTable from UWTASettings on Initialize (LoadSynchronous; a missing table logs a LogWTA warning and
// its getters return null). Typed getters return pointers into the table; callers copy what they keep.
// Row order is the converter's order (web order), so GetRowNames gives galleries, tour stops etc. in sequence.
//
// The season folder, <Saved>/Season: a library changes content without a rebuild. A <DT_Name>.json there (DT_Exhibits.json,
// DT_Facts.json, ...; the row shape of Data/*.json, "Name" plus the fields that change) is read at start: a row with a
// known Name is replaced field by field (the fields left out keep the built values), a new Name is added. The table in
// memory is a copy, so the built asset is never changed. Season/art/<row>.png (or .jpg) is the season's picture for an
// exhibit: the card shows it and the exhibit's frame on the wall is covered with it.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Engine/DataTable.h"
#include "Data/WTATypes.h"
#include "WTAContentSubsystem.generated.h"

class UTexture2D;

/** One value per table in UWTASettings. */
UENUM(BlueprintType)
enum class EWTATable : uint8
{
	Exhibits,
	Books,
	Sources,
	Galleries,
	Subjects,
	Rooms,
	Places,
	Tour,
	Staff,
	StaffRules,
	Facts,
	Lessons,
	Badges,
	Tokens,
	WaxScenes,
	Stations,
	Rides,
	Talks,
	Strings
};

UCLASS()
class WALKTHEARCHIVE_API UWTAContentSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	/** The subsystem of the game instance that owns WorldContextObject (null outside play). */
	UFUNCTION(BlueprintPure, Category = "WTA", meta = (WorldContext = "WorldContextObject"))
	static UWTAContentSubsystem* Get(const UObject* WorldContextObject);

	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/** Load (or reload) all tables from the settings, then the season folder over them. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ReloadTables();

	/** <Saved>/Season: the folder a library drops this season's rows and pictures in. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	static FString SeasonDir();

	/** Rows added or replaced from the season folder by the last ReloadTables. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 NumSeasonRows() const { return SeasonRows; }

	/** The season's picture for a row (Season/art/<row>.png or .jpg), loaded once; null when there is none. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	UTexture2D* SeasonTexture(FName RowId) const;

	/** The loaded table or null. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	UDataTable* GetTable(EWTATable Table) const;

	/** Row names of a table in table order (empty when not loaded). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	TArray<FName> GetRowNames(EWTATable Table) const;

	/** True when the table has that row. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	bool HasRow(EWTATable Table, FName RowName) const;

	// --- Typed getters (C++) -------------------------------------------------

	const FWTAExhibitRow*   FindExhibit(FName Id) const   { return FindRowIn<FWTAExhibitRow>(ExhibitsTable, Id); }
	const FWTABookRow*      FindBook(FName Id) const      { return FindRowIn<FWTABookRow>(BooksTable, Id); }
	const FWTASourceRow*    FindSource(FName Id) const    { return FindRowIn<FWTASourceRow>(SourcesTable, Id); }
	const FWTAGalleryRow*   FindGallery(FName Id) const   { return FindRowIn<FWTAGalleryRow>(GalleriesTable, Id); }
	const FWTASubjectRow*   FindSubject(FName Id) const   { return FindRowIn<FWTASubjectRow>(SubjectsTable, Id); }
	const FWTARoomRow*      FindRoom(FName Id) const      { return FindRowIn<FWTARoomRow>(RoomsTable, Id); }
	const FWTAPlaceRow*     FindPlace(FName Id) const     { return FindRowIn<FWTAPlaceRow>(PlacesTable, Id); }
	const FWTATourStopRow*  FindTourStop(FName Id) const  { return FindRowIn<FWTATourStopRow>(TourTable, Id); }
	const FWTAStaffRow*     FindStaff(FName Id) const     { return FindRowIn<FWTAStaffRow>(StaffTable, Id); }
	const FWTAStaffRuleRow* FindStaffRule(FName Id) const { return FindRowIn<FWTAStaffRuleRow>(StaffRulesTable, Id); }
	const FWTAFactRow*      FindFact(FName Id) const      { return FindRowIn<FWTAFactRow>(FactsTable, Id); }
	const FWTALessonRow*    FindLesson(FName Id) const    { return FindRowIn<FWTALessonRow>(LessonsTable, Id); }
	const FWTABadgeRow*     FindBadge(FName Id) const     { return FindRowIn<FWTABadgeRow>(BadgesTable, Id); }
	const FWTATokenRow*     FindToken(FName Id) const     { return FindRowIn<FWTATokenRow>(TokensTable, Id); }
	const FWTAWaxSceneRow*  FindWaxScene(FName Id) const  { return FindRowIn<FWTAWaxSceneRow>(WaxScenesTable, Id); }
	const FWTAStationRow*   FindStation(FName Id) const   { return FindRowIn<FWTAStationRow>(StationsTable, Id); }
	const FWTARideRow*      FindRide(FName Id) const      { return FindRowIn<FWTARideRow>(RidesTable, Id); }
	const FWTATalkRow*      FindTalk(FName Id) const      { return FindRowIn<FWTATalkRow>(TalksTable, Id); }

	/** The engine's own words in the pack's language: DT_Strings[English].Text, else the English itself. Static so
	    the widgets' free helpers (PanelText, WTAText) can call it; it reads the table the last content subsystem to
	    load filled in (one game instance at a time). */
	static FText Tr(const FString& English);
	static FText Tr(const TCHAR* English) { return Tr(FString(English)); }

	/** How many words DT_Strings holds (0 = English). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 NumStrings() const;

	/** The talk or class held in a venue (the first DT_Talks row whose Venue matches), or none. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FName FindTalkForVenue(FName Venue) const;

	/** Gallery exhibit ids (bWax false: the 15 exhibits + the Freedom board) in table order. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	TArray<FName> GetGalleryExhibitIds() const;

	/** Wax Hall card ids (bWax true) in table order. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	TArray<FName> GetWaxExhibitIds() const;

	/** Tour stop row names sorted by Index. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	TArray<FName> GetTourStopIds() const;

	// --- Blueprint copies of the rows used by UI --------------------------------

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool GetExhibit(FName Id, FWTAExhibitRow& OutRow) const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool GetBook(FName Id, FWTABookRow& OutRow) const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool GetRoom(FName Id, FWTARoomRow& OutRow) const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool GetPlace(FName Id, FWTAPlaceRow& OutRow) const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool GetStaff(FName Id, FWTAStaffRow& OutRow) const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool GetStation(FName Id, FWTAStationRow& OutRow) const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool GetRide(FName Id, FWTARideRow& OutRow) const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool GetTourStop(FName Id, FWTATourStopRow& OutRow) const;

protected:
	/** The season file for a table (DT_<Name>.json or <Name>.json in SeasonDir) laid over a copy of the table; returns
	    the table to use (the copy when the file changed anything, else the table itself). */
	UDataTable* ApplySeason(UDataTable* Table, const TCHAR* Name);

	UPROPERTY(Transient) mutable TMap<FName, TObjectPtr<UTexture2D>> SeasonTextures;
	mutable TSet<FName> SeasonTextureMisses;
	int32 SeasonRows = 0;

	template <typename TRow>
	const TRow* FindRowIn(const UDataTable* Table, FName Id) const
	{
		if (Table == nullptr || Id.IsNone())
		{
			return nullptr;
		}
		return Table->FindRow<TRow>(Id, TEXT("WTA"), false);
	}

	UPROPERTY(Transient) TObjectPtr<UDataTable> ExhibitsTable;
	UPROPERTY(Transient) TObjectPtr<UDataTable> BooksTable;
	UPROPERTY(Transient) TObjectPtr<UDataTable> SourcesTable;
	UPROPERTY(Transient) TObjectPtr<UDataTable> GalleriesTable;
	UPROPERTY(Transient) TObjectPtr<UDataTable> SubjectsTable;
	UPROPERTY(Transient) TObjectPtr<UDataTable> RoomsTable;
	UPROPERTY(Transient) TObjectPtr<UDataTable> PlacesTable;
	UPROPERTY(Transient) TObjectPtr<UDataTable> TourTable;
	UPROPERTY(Transient) TObjectPtr<UDataTable> StaffTable;
	UPROPERTY(Transient) TObjectPtr<UDataTable> StaffRulesTable;
	UPROPERTY(Transient) TObjectPtr<UDataTable> FactsTable;
	UPROPERTY(Transient) TObjectPtr<UDataTable> LessonsTable;
	UPROPERTY(Transient) TObjectPtr<UDataTable> BadgesTable;
	UPROPERTY(Transient) TObjectPtr<UDataTable> TokensTable;
	UPROPERTY(Transient) TObjectPtr<UDataTable> WaxScenesTable;
	UPROPERTY(Transient) TObjectPtr<UDataTable> StationsTable;
	UPROPERTY(Transient) TObjectPtr<UDataTable> RidesTable;
	UPROPERTY(Transient) TObjectPtr<UDataTable> TalksTable;
	UPROPERTY(Transient) TObjectPtr<UDataTable> StringsTable;
};
