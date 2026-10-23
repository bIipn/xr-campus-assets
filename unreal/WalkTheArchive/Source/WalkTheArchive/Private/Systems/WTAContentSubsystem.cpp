// Walk the Archive - the content tables.

#include "Systems/WTAContentSubsystem.h"
#include "Core/WTASettings.h"
#include "Core/WTALog.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Subsystems/SubsystemCollection.h"
#include "UObject/SoftObjectPtr.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Engine/Texture2D.h"
#include "ImageUtils.h"
#include "JsonObjectConverter.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace
{
	/** DT_Strings as a map, English -> the pack's words (UWTAContentSubsystem::Tr). */
	TMap<FString, FText> GStrings;

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
	SeasonRows = 0;
	SeasonTextures.Reset();
	SeasonTextureMisses.Reset();
	ExhibitsTable   = ApplySeason(LoadTable(Settings->Exhibits,   TEXT("Exhibits"),   FWTAExhibitRow::StaticStruct()),   TEXT("Exhibits"));
	BooksTable      = ApplySeason(LoadTable(Settings->Books,      TEXT("Books"),      FWTABookRow::StaticStruct()),      TEXT("Books"));
	SourcesTable    = ApplySeason(LoadTable(Settings->Sources,    TEXT("Sources"),    FWTASourceRow::StaticStruct()),    TEXT("Sources"));
	GalleriesTable  = ApplySeason(LoadTable(Settings->Galleries,  TEXT("Galleries"),  FWTAGalleryRow::StaticStruct()),   TEXT("Galleries"));
	SubjectsTable   = ApplySeason(LoadTable(Settings->Subjects,   TEXT("Subjects"),   FWTASubjectRow::StaticStruct()),   TEXT("Subjects"));
	RoomsTable      = ApplySeason(LoadTable(Settings->Rooms,      TEXT("Rooms"),      FWTARoomRow::StaticStruct()),      TEXT("Rooms"));
	PlacesTable     = ApplySeason(LoadTable(Settings->Places,     TEXT("Places"),     FWTAPlaceRow::StaticStruct()),     TEXT("Places"));
	TourTable       = ApplySeason(LoadTable(Settings->Tour,       TEXT("Tour"),       FWTATourStopRow::StaticStruct()),  TEXT("Tour"));
	StaffTable      = ApplySeason(LoadTable(Settings->Staff,      TEXT("Staff"),      FWTAStaffRow::StaticStruct()),     TEXT("Staff"));
	StaffRulesTable = ApplySeason(LoadTable(Settings->StaffRules, TEXT("StaffRules"), FWTAStaffRuleRow::StaticStruct()), TEXT("StaffRules"));
	FactsTable      = ApplySeason(LoadTable(Settings->Facts,      TEXT("Facts"),      FWTAFactRow::StaticStruct()),      TEXT("Facts"));
	LessonsTable    = ApplySeason(LoadTable(Settings->Lessons,    TEXT("Lessons"),    FWTALessonRow::StaticStruct()),    TEXT("Lessons"));
	BadgesTable     = ApplySeason(LoadTable(Settings->Badges,     TEXT("Badges"),     FWTABadgeRow::StaticStruct()),     TEXT("Badges"));
	TokensTable     = ApplySeason(LoadTable(Settings->Tokens,     TEXT("Tokens"),     FWTATokenRow::StaticStruct()),     TEXT("Tokens"));
	WaxScenesTable  = ApplySeason(LoadTable(Settings->WaxScenes,  TEXT("WaxScenes"),  FWTAWaxSceneRow::StaticStruct()),  TEXT("WaxScenes"));
	StationsTable   = ApplySeason(LoadTable(Settings->Stations,   TEXT("Stations"),   FWTAStationRow::StaticStruct()),   TEXT("Stations"));
	RidesTable      = ApplySeason(LoadTable(Settings->Rides,      TEXT("Rides"),      FWTARideRow::StaticStruct()),      TEXT("Rides"));
	TalksTable      = ApplySeason(LoadTable(Settings->Talks,      TEXT("Talks"),      FWTATalkRow::StaticStruct()),      TEXT("Talks"));
	StringsTable    = Settings->Strings.IsNull() ? nullptr : ApplySeason(LoadTable(Settings->Strings, TEXT("Strings"), FWTAStringRow::StaticStruct()), TEXT("Strings"));
	if (SeasonRows > 0)
	{
		UE_LOG(LogWTA, Display, TEXT("WTA_SEASON %d rows from %s"), SeasonRows, *SeasonDir());
	}
	// The words the C++ writes, in the pack's language, for Tr(): keyed by the English text.
	GStrings.Reset();
	if (StringsTable != nullptr)
	{
		for (const TPair<FName, uint8*>& Pair : StringsTable->GetRowMap())
		{
			const FWTAStringRow* Row = reinterpret_cast<const FWTAStringRow*>(Pair.Value);
			if (Row != nullptr && !Row->Text.IsEmpty())
			{
				GStrings.Add(Pair.Key.ToString(), Row->Text);
			}
		}
	}
	if (GStrings.Num() > 0)
	{
		UE_LOG(LogWTA, Display, TEXT("Content: %d of the engine's words come from DT_Strings"), GStrings.Num());
	}
}

FText UWTAContentSubsystem::Tr(const FString& English)
{
	if (const FText* Found = GStrings.Find(English))
	{
		return *Found;
	}
	return FText::FromString(English);
}

int32 UWTAContentSubsystem::NumStrings() const
{
	return GStrings.Num();
}

FString UWTAContentSubsystem::SeasonDir()
{
	return FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Season"));
}

UDataTable* UWTAContentSubsystem::ApplySeason(UDataTable* Table, const TCHAR* Name)
{
	if (Table == nullptr || Table->GetRowStruct() == nullptr)
	{
		return Table;
	}
	FString File = FPaths::Combine(SeasonDir(), FString::Printf(TEXT("DT_%s.json"), Name));
	if (!FPaths::FileExists(File))
	{
		File = FPaths::Combine(SeasonDir(), FString::Printf(TEXT("%s.json"), Name));
		if (!FPaths::FileExists(File))
		{
			return Table;
		}
	}
	FString Json;
	if (!FFileHelper::LoadFileToString(Json, *File))
	{
		UE_LOG(LogWTA, Warning, TEXT("Season: could not read %s"), *File);
		return Table;
	}
	TArray<TSharedPtr<FJsonValue>> Rows;
	const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Json);
	if (!FJsonSerializer::Deserialize(Reader, Rows))
	{
		UE_LOG(LogWTA, Warning, TEXT("Season: %s is not a JSON list of rows (%s)"), *File, *Reader->GetErrorMessage());
		return Table;
	}

	// The season lies over a copy, so the built asset stays as it was.
	const UScriptStruct* RowStruct = Table->GetRowStruct();
	UDataTable* Copy = NewObject<UDataTable>(this, NAME_None, RF_Transient);
	Copy->RowStruct = const_cast<UScriptStruct*>(RowStruct);
	for (const TPair<FName, uint8*>& Pair : Table->GetRowMap())
	{
		Copy->AddRow(Pair.Key, Pair.Value, RowStruct);
	}
	int32 Replaced = 0, Added = 0;
	uint8* Buffer = static_cast<uint8*>(FMemory::Malloc(RowStruct->GetStructureSize()));
	for (const TSharedPtr<FJsonValue>& Value : Rows)
	{
		const TSharedPtr<FJsonObject>* Object = nullptr;
		FString RowName;
		if (!Value.IsValid() || !Value->TryGetObject(Object) || !(*Object)->TryGetStringField(TEXT("Name"), RowName) || RowName.IsEmpty())
		{
			UE_LOG(LogWTA, Warning, TEXT("Season: a row in %s has no \"Name\""), *File);
			continue;
		}
		const FName Id(*RowName);
		RowStruct->InitializeStruct(Buffer);
		const uint8* Existing = Copy->FindRowUnchecked(Id);
		if (Existing != nullptr)
		{
			RowStruct->CopyScriptStruct(Buffer, Existing);     // the fields the file leaves out keep the built values
		}
		if (!FJsonObjectConverter::JsonObjectToUStruct(Object->ToSharedRef(), RowStruct, Buffer, 0, 0))
		{
			UE_LOG(LogWTA, Warning, TEXT("Season: row %s in %s did not read; skipped"), *RowName, *File);
			RowStruct->DestroyStruct(Buffer);
			continue;
		}
		Copy->AddRow(Id, Buffer, RowStruct);
		RowStruct->DestroyStruct(Buffer);
		(Existing != nullptr ? Replaced : Added) += 1;
	}
	FMemory::Free(Buffer);
	SeasonRows += Replaced + Added;
	UE_LOG(LogWTA, Display, TEXT("WTA_SEASON DT_%s: %d replaced, %d added from %s"), Name, Replaced, Added, *FPaths::GetCleanFilename(File));
	return Copy;
}

UTexture2D* UWTAContentSubsystem::SeasonTexture(FName RowId) const
{
	if (RowId.IsNone())
	{
		return nullptr;
	}
	if (const TObjectPtr<UTexture2D>* Found = SeasonTextures.Find(RowId))
	{
		return *Found;
	}
	if (SeasonTextureMisses.Contains(RowId))
	{
		return nullptr;
	}
	const FString Folder = FPaths::Combine(SeasonDir(), TEXT("art"));
	for (const TCHAR* Ext : { TEXT("png"), TEXT("jpg"), TEXT("jpeg") })
	{
		const FString File = FPaths::Combine(Folder, FString::Printf(TEXT("%s.%s"), *RowId.ToString(), Ext));
		if (FPaths::FileExists(File))
		{
			UTexture2D* Texture = FImageUtils::ImportFileAsTexture2D(File);
			if (Texture != nullptr)
			{
				SeasonTextures.Add(RowId, Texture);
				UE_LOG(LogWTA, Display, TEXT("WTA_SEASON picture %s (%d x %d)"), *FPaths::GetCleanFilename(File), Texture->GetSizeX(), Texture->GetSizeY());
				return Texture;
			}
			UE_LOG(LogWTA, Warning, TEXT("Season: %s did not load as a picture"), *File);
		}
	}
	SeasonTextureMisses.Add(RowId);
	return nullptr;
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
	case EWTATable::Talks:      return TalksTable;
	case EWTATable::Strings:    return StringsTable;
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

FName UWTAContentSubsystem::FindTalkForVenue(FName Venue) const
{
	if (TalksTable == nullptr || Venue.IsNone())
	{
		return NAME_None;
	}
	for (const TPair<FName, uint8*>& Pair : TalksTable->GetRowMap())
	{
		const FWTATalkRow* Row = reinterpret_cast<const FWTATalkRow*>(Pair.Value);
		if (Row != nullptr && Row->Venue == Venue)
		{
			return Pair.Key;
		}
	}
	return NAME_None;
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
