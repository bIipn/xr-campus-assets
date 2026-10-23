// Walk the Archive - badges, tokens and what the player has seen (port of the web progress.js).

#include "Systems/WTAProgressSubsystem.h"
#include "Systems/WTASaveGame.h"
#include "Systems/WTAContentSubsystem.h"
#include "Core/WTASettings.h"
#include "Core/WTALog.h"
#include "Data/WTATypes.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/SaveGame.h"
#include "Kismet/GameplayStatics.h"
#include "Subsystems/SubsystemCollection.h"

namespace
{
	constexpr int32 SaveUserIndex = 0;

	FString SlotName()
	{
		const UWTASettings* Settings = UWTASettings::Get();
		return (Settings != nullptr && !Settings->SaveSlotName.IsEmpty()) ? Settings->SaveSlotName : FString(TEXT("WalkTheArchive"));
	}
}

UWTAProgressSubsystem* UWTAProgressSubsystem::Get(const UObject* WorldContextObject)
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
	return GameInstance ? GameInstance->GetSubsystem<UWTAProgressSubsystem>() : nullptr;
}

void UWTAProgressSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	// The badge rules read DT_Badges and DT_Tokens, so make sure the content subsystem exists first.
	Collection.InitializeDependency(UWTAContentSubsystem::StaticClass());
	Load();
}

void UWTAProgressSubsystem::Deinitialize()
{
	Save();
	Super::Deinitialize();
}

// --- Events ---------------------------------------------------------------

bool UWTAProgressSubsystem::CollectToken(FName TokenId)
{
	if (TokenId.IsNone() || SaveData == nullptr || SaveData->Tokens.Contains(TokenId))
	{
		return false;
	}
	SaveData->Tokens.Add(TokenId);
	Save();
	OnTokenCollected.Broadcast(TokenId, NumTokens(), TotalTokens());
	CheckBadges();
	return true;
}

bool UWTAProgressSubsystem::AwardBadge(FName BadgeId)
{
	if (BadgeId.IsNone() || SaveData == nullptr || SaveData->Badges.Contains(BadgeId))
	{
		return false;
	}
	// Unknown ids are refused when the badge table is loaded (a typo would otherwise count toward the total).
	const UWTAContentSubsystem* Content = GetGameInstance() ? GetGameInstance()->GetSubsystem<UWTAContentSubsystem>() : nullptr;
	if (Content != nullptr && Content->GetTable(EWTATable::Badges) != nullptr && Content->FindBadge(BadgeId) == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("Progress: unknown badge '%s'"), *BadgeId.ToString());
		return false;
	}
	SaveData->Badges.Add(BadgeId);
	Save();
	UE_LOG(LogWTA, Log, TEXT("Progress: badge '%s' awarded (%d so far)"), *BadgeId.ToString(), SaveData->Badges.Num());
	OnBadgeAwarded.Broadcast(BadgeId);
	return true;
}

void UWTAProgressSubsystem::NoteExhibit(FName ItemId)
{
	if (ItemId.IsNone() || SaveData == nullptr || SaveData->Exhibits.Contains(ItemId))
	{
		return;
	}
	SaveData->Exhibits.Add(ItemId);
	Save();
	CheckBadges();
}

void UWTAProgressSubsystem::NotePage(FName BookId, int32 Page)
{
	if (BookId.IsNone() || Page < 0 || SaveData == nullptr)
	{
		return;
	}
	const FName Key = PageKey(BookId, Page);
	if (SaveData->Pages.Contains(Key))
	{
		return;
	}
	SaveData->Pages.Add(Key);
	Save();
	CheckBadges();
}

void UWTAProgressSubsystem::NoteWaxScene(FName SceneId)
{
	if (SceneId.IsNone() || SaveData == nullptr || SaveData->WaxScenes.Contains(SceneId))
	{
		return;
	}
	SaveData->WaxScenes.Add(SceneId);
	Save();
	CheckBadges();
}

void UWTAProgressSubsystem::NoteTalkHeard(FName TalkId)
{
	if (TalkId.IsNone() || SaveData == nullptr)
	{
		return;
	}
	if (!SaveData->TalksHeard.Contains(TalkId))
	{
		SaveData->TalksHeard.Add(TalkId);
		Save();
	}
	AwardBadge(WTABadge::Listener());
}

void UWTAProgressSubsystem::NoteCertificate(FName TalkId, const FString& Name)
{
	if (TalkId.IsNone() || SaveData == nullptr)
	{
		return;
	}
	const int32 Index = SaveData->Certificates.IndexOfByKey(TalkId);
	if (Index == INDEX_NONE)
	{
		SaveData->Certificates.Add(TalkId);
		SaveData->CertificateNames.Add(Name);
	}
	else if (SaveData->CertificateNames.IsValidIndex(Index))
	{
		SaveData->CertificateNames[Index] = Name;
	}
	if (!Name.IsEmpty())
	{
		SaveData->VisitorName = Name;
	}
	Save();
	const UWTAContentSubsystem* Content = GetGameInstance() ? GetGameInstance()->GetSubsystem<UWTAContentSubsystem>() : nullptr;
	const FWTATalkRow* Row = Content != nullptr ? Content->FindTalk(TalkId) : nullptr;
	if (Row != nullptr && !Row->BadgeId.IsNone())
	{
		AwardBadge(Row->BadgeId);
	}
}

bool UWTAProgressSubsystem::HasHeardTalk(FName TalkId) const
{
	return SaveData != nullptr && SaveData->TalksHeard.Contains(TalkId);
}

bool UWTAProgressSubsystem::HasFinishedStation(FName StationId) const
{
	return SaveData != nullptr && SaveData->StationsFinished.Contains(StationId);
}

bool UWTAProgressSubsystem::HasCertificate(FName TalkId) const
{
	return SaveData != nullptr && SaveData->Certificates.Contains(TalkId);
}

FString UWTAProgressSubsystem::CertificateName(FName TalkId) const
{
	if (SaveData == nullptr)
	{
		return FString();
	}
	const int32 Index = SaveData->Certificates.IndexOfByKey(TalkId);
	return SaveData->CertificateNames.IsValidIndex(Index) ? SaveData->CertificateNames[Index] : FString();
}

FString UWTAProgressSubsystem::GetVisitorName() const
{
	return SaveData != nullptr ? SaveData->VisitorName : FString();
}

void UWTAProgressSubsystem::SetVisitorName(const FString& Name)
{
	if (SaveData != nullptr && SaveData->VisitorName != Name)
	{
		SaveData->VisitorName = Name;
		Save();
	}
}

void UWTAProgressSubsystem::NoteDistance(float Cm)
{
	if (SaveData == nullptr || !FMath::IsFinite(Cm) || Cm <= 0.f)
	{
		return;
	}
	SaveData->WalkedCm += Cm;
	UnsavedWalkCm += Cm;
	if (SaveData->WalkedCm >= FirstStepsCm && !HasBadge(WTABadge::FirstSteps()))
	{
		AwardBadge(WTABadge::FirstSteps());
	}
	// Distance alone is saved every 20 m, not every frame.
	if (UnsavedWalkCm >= SaveDistanceEveryCm)
	{
		Save();
	}
}

void UWTAProgressSubsystem::NoteQuestionAsked()
{
	AwardBadge(WTABadge::Curious());
}

void UWTAProgressSubsystem::NoteRideFinished(FName RideId)
{
	const UWTAContentSubsystem* Content = GetGameInstance() ? GetGameInstance()->GetSubsystem<UWTAContentSubsystem>() : nullptr;
	const FWTARideRow* Ride = Content ? Content->FindRide(RideId) : nullptr;
	if (Ride != nullptr && !Ride->BadgeId.IsNone())
	{
		AwardBadge(Ride->BadgeId);
	}
}

void UWTAProgressSubsystem::NoteStationFinished(FName StationId)
{
	if (StationId.IsNone() || SaveData == nullptr)
	{
		return;
	}
	if (!SaveData->StationsFinished.Contains(StationId))
	{
		SaveData->StationsFinished.Add(StationId);
		Save();
	}
	// Station -> badge, by the room the station is in (DT_Stations.Room), with the web's station ids as a fallback.
	const UWTAContentSubsystem* Content = GetGameInstance() ? GetGameInstance()->GetSubsystem<UWTAContentSubsystem>() : nullptr;
	const FWTAStationRow* Station = Content ? Content->FindStation(StationId) : nullptr;
	FName Badge;
	const FName Room = Station ? Station->Room : NAME_None;
	if (Station != nullptr && !Station->BadgeId.IsNone()) { Badge = Station->BadgeId; }       // the row names its own
	else if (Room == FName(TEXT("lab")))        { Badge = FName(TEXT("scientist")); }
	else if (Room == FName(TEXT("blueprint")))  { Badge = FName(TEXT("maker")); }
	else if (Room == FName(TEXT("world")))      { Badge = FName(TEXT("worldbuilder")); }
	else if (Room == FName(TEXT("studio")))     { Badge = FName(TEXT("artist")); }
	else if (Room == FName(TEXT("training")))   { Badge = FName(TEXT("trainee")); }
	else if (StationId == FName(TEXT("sieve")) || StationId == FName(TEXT("titration")) || StationId == FName(TEXT("pendulum"))) { Badge = FName(TEXT("scientist")); }
	else if (StationId == FName(TEXT("bench")))   { Badge = FName(TEXT("maker")); }
	else if (StationId == FName(TEXT("diorama"))) { Badge = FName(TEXT("worldbuilder")); }
	else if (StationId == FName(TEXT("easel")))   { Badge = FName(TEXT("artist")); }
	if (!Badge.IsNone())
	{
		AwardBadge(Badge);
	}
}

// --- Queries --------------------------------------------------------------

bool UWTAProgressSubsystem::HasToken(FName TokenId) const
{
	return SaveData != nullptr && SaveData->Tokens.Contains(TokenId);
}

bool UWTAProgressSubsystem::HasBadge(FName BadgeId) const
{
	return SaveData != nullptr && SaveData->Badges.Contains(BadgeId);
}

bool UWTAProgressSubsystem::HasSeenExhibit(FName ItemId) const
{
	return SaveData != nullptr && SaveData->Exhibits.Contains(ItemId);
}

bool UWTAProgressSubsystem::HasReadPage(FName BookId, int32 Page) const
{
	return SaveData != nullptr && SaveData->Pages.Contains(PageKey(BookId, Page));
}

bool UWTAProgressSubsystem::HasWatchedWaxScene(FName SceneId) const
{
	return SaveData != nullptr && SaveData->WaxScenes.Contains(SceneId);
}

int32 UWTAProgressSubsystem::NumBadges() const
{
	return SaveData ? SaveData->Badges.Num() : 0;
}

int32 UWTAProgressSubsystem::TotalBadges() const
{
	const UWTAContentSubsystem* Content = GetGameInstance() ? GetGameInstance()->GetSubsystem<UWTAContentSubsystem>() : nullptr;
	return Content ? Content->GetRowNames(EWTATable::Badges).Num() : 0;
}

int32 UWTAProgressSubsystem::NumTokens() const
{
	return SaveData ? SaveData->Tokens.Num() : 0;
}

int32 UWTAProgressSubsystem::TotalTokens() const
{
	const UWTAContentSubsystem* Content = GetGameInstance() ? GetGameInstance()->GetSubsystem<UWTAContentSubsystem>() : nullptr;
	return Content ? Content->GetRowNames(EWTATable::Tokens).Num() : 0;
}

int32 UWTAProgressSubsystem::NumExhibitsSeen() const
{
	return SaveData ? SaveData->Exhibits.Num() : 0;
}

int32 UWTAProgressSubsystem::NumPagesRead() const
{
	return SaveData ? SaveData->Pages.Num() : 0;
}

int32 UWTAProgressSubsystem::NumWaxScenesWatched() const
{
	return SaveData ? SaveData->WaxScenes.Num() : 0;
}

float UWTAProgressSubsystem::GetWalkedCm() const
{
	return SaveData ? SaveData->WalkedCm : 0.f;
}

// --- Persistence ----------------------------------------------------------

void UWTAProgressSubsystem::ResetProgress()
{
	SaveData = Cast<UWTASaveGame>(UGameplayStatics::CreateSaveGameObject(UWTASaveGame::StaticClass()));
	Save();
	UE_LOG(LogWTA, Log, TEXT("Progress: reset"));
	OnProgressReset.Broadcast();
}

void UWTAProgressSubsystem::Save()
{
	if (SaveData == nullptr)
	{
		return;
	}
	if (!UGameplayStatics::SaveGameToSlot(SaveData, SlotName(), SaveUserIndex))
	{
		UE_LOG(LogWTA, Warning, TEXT("Progress: could not write save slot '%s'"), *SlotName());
	}
	UnsavedWalkCm = 0.f;
}

void UWTAProgressSubsystem::Load()
{
	SaveData = nullptr;
	const FString Slot = SlotName();
	if (UGameplayStatics::DoesSaveGameExist(Slot, SaveUserIndex))
	{
		USaveGame* Loaded = UGameplayStatics::LoadGameFromSlot(Slot, SaveUserIndex);
		UWTASaveGame* Typed = Cast<UWTASaveGame>(Loaded);
		if (Typed != nullptr && Typed->Version == 1)
		{
			SaveData = Typed;
			UE_LOG(LogWTA, Log, TEXT("Progress: loaded slot '%s' (%d badges, %d tokens, %.0f cm walked)"),
				*Slot, Typed->Badges.Num(), Typed->Tokens.Num(), Typed->WalkedCm);
		}
		else
		{
			UE_LOG(LogWTA, Warning, TEXT("Progress: save slot '%s' is missing or of another version; starting fresh"), *Slot);
		}
	}
	if (SaveData == nullptr)
	{
		SaveData = Cast<UWTASaveGame>(UGameplayStatics::CreateSaveGameObject(UWTASaveGame::StaticClass()));
	}
	UnsavedWalkCm = 0.f;
}

// --- Rules ----------------------------------------------------------------

void UWTAProgressSubsystem::CheckBadges()
{
	if (SaveData == nullptr)
	{
		return;
	}
	if (SaveData->WalkedCm >= FirstStepsCm)
	{
		AwardBadge(WTABadge::FirstSteps());
	}
	if (NumExhibitsSeen() >= ExplorerExhibits)
	{
		AwardBadge(WTABadge::Explorer());
	}
	if (NumPagesRead() >= BookwormPages)
	{
		AwardBadge(WTABadge::Bookworm());
	}
	if (NumWaxScenesWatched() >= HistorianScenes)
	{
		AwardBadge(WTABadge::Historian());
	}
	// Hunter: every token in DT_Tokens (ids not in the table do not count).
	const UWTAContentSubsystem* Content = GetGameInstance() ? GetGameInstance()->GetSubsystem<UWTAContentSubsystem>() : nullptr;
	if (Content != nullptr)
	{
		const TArray<FName> AllTokens = Content->GetRowNames(EWTATable::Tokens);
		if (AllTokens.Num() > 0)
		{
			bool bAll = true;
			for (const FName& Token : AllTokens)
			{
				if (!SaveData->Tokens.Contains(Token))
				{
					bAll = false;
					break;
				}
			}
			if (bAll)
			{
				AwardBadge(WTABadge::Hunter());
			}
		}
	}
}

FName UWTAProgressSubsystem::PageKey(FName BookId, int32 Page)
{
	return FName(*FString::Printf(TEXT("%s:%d"), *BookId.ToString(), Page));
}
