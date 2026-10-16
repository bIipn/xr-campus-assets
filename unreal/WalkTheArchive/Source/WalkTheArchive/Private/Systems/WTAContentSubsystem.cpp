// Walk the Archive - the content tables.

#include "Systems/WTAContentSubsystem.h"
#include "Core/WTASettings.h"
#include "Core/WTALog.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Subsystems/SubsystemCollection.h"
#include "UObject/SoftObjectPtr.h"

namespace
{
	/** LoadSynchronous one table reference; null (with a warning) when unset, missing or of the wrong row struct. */
	UDataTable* LoadTable(const TSoftObjectPtr<UDataTable>& Ref, const TCHAR* Name, const UScriptStruct* ExpectedRow)
	{
		if (Ref.IsNull())
		{
			UE_LOG(LogWTA, Warning, TEXT("Content: table %s is not set in Project Settings > Game > Walk the Archive"), Name);
			return nullptr;
		}
		UDataTable* Table = Ref.LoadSynchronous();
		if (Table == nullptr)
		{
			UE_LOG(LogWTA, Warning, TEXT("Content: table %s not found at %s (run the data_tables setup step)"), Name, *Ref.ToString());
			return nullptr;
		}
		if (ExpectedRow != nullptr && Table->GetRowStruct() != nullptr && !Table->GetRowStruct()->IsChildOf(ExpectedRow))
		{
			UE_LOG(LogWTA, Warning, TEXT("Content: table %s has row struct %s, expected %s; ignoring it"),
				Name, *Table->GetRowStruct()->GetName(), *ExpectedRow->GetName());
			return nullptr;
		}
		UE_LOG(LogWTA, Log, TEXT("Content: %s loaded, %d rows"), Name, Table->GetRowMap().Num());
		return Table;
	}
}

UWTAContentSubsystem* UWTAContentSubsystem::Get(const UObject* WorldContextObject)
{
	if (WorldContextObject == nullptr || GEngine == nullptr)
	{
		return nullptr;
	}
	const UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull);
	if (World == nullptr)
	{
		return nullptr;
	}
	const UGameInstance* GameInstance = World->GetGameInstance();
	return GameInstance ? GameInstance->GetSubsystem<UWTAContentSubsystem>() : nullptr;
}

void UWTAContentSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	ReloadTables();
}

void UWTAContentSubsystem::ReloadTables()
{
	const UWTASettings* Settings = UWTASettings::Get();
	if (Settings == nullptr)
	{
		return;
	}
	ExhibitsTable   = LoadTable(Settings->Exhibits,   TEXT("Exhibits"),   FWTAExhibitRow::StaticStruct());
	BooksTable      = LoadTable(Settings->Books,      TEXT("Books"),      FWTABookRow::StaticStruct());
	SourcesTable    = LoadTable(Settings->Sources,    TEXT("Sources"),    FWTASourceRow::StaticStruct());
	GalleriesTable  = LoadTable(Settings->Galleries,  TEXT("Galleries"),  FWTAGalleryRow::StaticStruct());
	SubjectsTable   = LoadTable(Settings->Subjects,   TEXT("Subjects"),   FWTASubjectRow::StaticStruct());
	RoomsTable      = LoadTable(Settings->Rooms,      TEXT("Rooms"),      FWTARoomRow::StaticStruct());
	PlacesTable     = LoadTable(Settings->Places,     TEXT("Places"),     FWTAPlaceRow::StaticStruct());
	TourTable       = LoadTable(Settings->Tour,       TEXT("Tour"),       FWTATourStopRow::StaticStruct());
	StaffTable      = LoadTable(Settings->Staff,      TEXT("Staff"),      FWTAStaffRow::StaticStruct());
	StaffRulesTable = LoadTable(Settings->StaffRules, TEXT("StaffRules"), FWTAStaffRuleRow::StaticStruct());
	FactsTable      = LoadTable(Settings->Facts,      TEXT("Facts"),      FWTAFactRow::StaticStruct());
	LessonsTable    = LoadTable(Settings->Lessons,    TEXT("Lessons"),    FWTALessonRow::StaticStruct());
	BadgesTable     = LoadTable(Settings->Badges,     TEXT("Badges"),     FWTABadgeRow::StaticStruct());
	TokensTable     = LoadTable(Settings->Tokens,     TEXT("Tokens"),     FWTATokenRow::StaticStruct());
	WaxScenesTable  = LoadTable(Settings->WaxScenes,  TEXT("WaxScenes"),  FWTAWaxSceneRow::StaticStruct());
	StationsTable   = LoadTable(Settings->Stations,   TEXT("Stations"),   FWTAStationRow::StaticStruct());
	RidesTable      = LoadTable(Settings->Rides,      TEXT("Rides"),      FWTARideRow::StaticStruct());
}

UDataTable* UWTAContentSubsystem::GetTable(EWTATable Table) const
{
	switch (Table)
	{
	case EWTATable::Exhibits:   return ExhibitsTable;
	case EWTATable::Books:      return BooksTable;
	case EWTATable::Sources:    return SourcesTable;
	case EWTATable::Galleries:  return GalleriesTable;
	case EWTATable::Subjects:   return SubjectsTable;
	case EWTATable::Rooms:      return RoomsTable;
	case EWTATable::Places:     return PlacesTable;
	case EWTATable::Tour:       return TourTable;
	case EWTATable::Staff:      return StaffTable;
	case EWTATable::StaffRules: return StaffRulesTable;
	case EWTATable::Facts:      return FactsTable;
	case EWTATable::Lessons:    return LessonsTable;
	case EWTATable::Badges:     return BadgesTable;
	case EWTATable::Tokens:     return TokensTable;
	case EWTATable::WaxScenes:  return WaxScenesTable;
	case EWTATable::Stations:   return StationsTable;
	case EWTATable::Rides:      return RidesTable;
	default:                    return nullptr;
	}
}

TArray<FName> UWTAContentSubsystem::GetRowNames(EWTATable Table) const
{
	const UDataTable* DataTable = GetTable(Table);
	return DataTable ? DataTable->GetRowNames() : TArray<FName>();
}

bool UWTAContentSubsystem::HasRow(EWTATable Table, FName RowName) const
{
	const UDataTable* DataTable = GetTable(Table);
	return DataTable != nullptr && !RowName.IsNone() && DataTable->GetRowMap().Contains(RowName);
}

TArray<FName> UWTAContentSubsystem::GetGalleryExhibitIds() const
{
	TArray<FName> Ids;
	if (ExhibitsTable == nullptr)
	{
		return Ids;
	}
	for (const TPair<FName, uint8*>& Pair : ExhibitsTable->GetRowMap())
	{
		const FWTAExhibitRow* Row = reinterpret_cast<const FWTAExhibitRow*>(Pair.Value);
		if (Row != nullptr && !Row->bWax)
		{
			Ids.Add(Pair.Key);
		}
	}
	return Ids;
}

TArray<FName> UWTAContentSubsystem::GetWaxExhibitIds() const
{
	TArray<FName> Ids;
	if (ExhibitsTable == nullptr)
	{
		return Ids;
	}
	for (const TPair<FName, uint8*>& Pair : ExhibitsTable->GetRowMap())
	{
		const FWTAExhibitRow* Row = reinterpret_cast<const FWTAExhibitRow*>(Pair.Value);
		if (Row != nullptr && Row->bWax)
		{
			Ids.Add(Pair.Key);
		}
	}
	return Ids;
}

TArray<FName> UWTAContentSubsystem::GetTourStopIds() const
{
	TArray<FName> Ids;
	if (TourTable == nullptr)
	{
		return Ids;
	}
	// Sort by Index, then by row name so equal indices stay stable.
	TArray<TPair<int32, FName>> Stops;
	for (const TPair<FName, uint8*>& Pair : TourTable->GetRowMap())
	{
		const FWTATourStopRow* Row = reinterpret_cast<const FWTATourStopRow*>(Pair.Value);
		if (Row != nullptr)
		{
			Stops.Emplace(Row->Index, Pair.Key);
		}
	}
	Stops.Sort([](const TPair<int32, FName>& A, const TPair<int32, FName>& B)
	{
		if (A.Key != B.Key)
		{
			return A.Key < B.Key;
		}
		return A.Value.LexicalLess(B.Value);
	});
	Ids.Reserve(Stops.Num());
	for (const TPair<int32, FName>& Stop : Stops)
	{
		Ids.Add(Stop.Value);
	}
	return Ids;
}

bool UWTAContentSubsystem::GetExhibit(FName Id, FWTAExhibitRow& OutRow) const
{
	if (const FWTAExhibitRow* Row = FindExhibit(Id))
	{
		OutRow = *Row;
		return true;
	}
	return false;
}

bool UWTAContentSubsystem::GetBook(FName Id, FWTABookRow& OutRow) const
{
	if (const FWTABookRow* Row = FindBook(Id))
	{
		OutRow = *Row;
		return true;
	}
	return false;
}

bool UWTAContentSubsystem::GetRoom(FName Id, FWTARoomRow& OutRow) const
{
	if (const FWTARoomRow* Row = FindRoom(Id))
	{
		OutRow = *Row;
		return true;
	}
	return false;
}

bool UWTAContentSubsystem::GetPlace(FName Id, FWTAPlaceRow& OutRow) const
{
	if (const FWTAPlaceRow* Row = FindPlace(Id))
	{
		OutRow = *Row;
		return true;
	}
	return false;
}

bool UWTAContentSubsystem::GetStaff(FName Id, FWTAStaffRow& OutRow) const
{
	if (const FWTAStaffRow* Row = FindStaff(Id))
	{
		OutRow = *Row;
		return true;
	}
	return false;
}

bool UWTAContentSubsystem::GetStation(FName Id, FWTAStationRow& OutRow) const
{
	if (const FWTAStationRow* Row = FindStation(Id))
	{
		OutRow = *Row;
		return true;
	}
	return false;
}

bool UWTAContentSubsystem::GetRide(FName Id, FWTARideRow& OutRow) const
{
	if (const FWTARideRow* Row = FindRide(Id))
	{
		OutRow = *Row;
		return true;
	}
	return false;
}

bool UWTAContentSubsystem::GetTourStop(FName Id, FWTATourStopRow& OutRow) const
{
	if (const FWTATourStopRow* Row = FindTourStop(Id))
	{
		OutRow = *Row;
		return true;
	}
	return false;
}
