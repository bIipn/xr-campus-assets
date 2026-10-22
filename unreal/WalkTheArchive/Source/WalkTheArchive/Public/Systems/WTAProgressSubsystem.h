// Walk the Archive - badges, tokens and what the player has seen.
//
// Backed by UWTASaveGame in the settings' slot (user 0). Load on Initialize, Save after every change that matters
// (badge, token, exhibit, page, wax scene) and on Deinitialize (distance is saved then and every 20 m).
// Badge rules (web progress.js, ids from DT_Badges):
//   first-steps  500 cm walked            explorer   5 exhibits opened (any, wax cards count)
//   bookworm     5 pages read             curious    any question asked
//   hunter       every DT_Tokens row      historian  6 wax scenes watched
// The other badges (artist, scientist, engineer, maker, worldbuilder, coaster, drop, diver, striker) are awarded by
// phase 1+ features through AwardBadge / NoteRideFinished / NoteStationFinished.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "WTAProgressSubsystem.generated.h"

class UWTASaveGame;

/** A badge was just unlocked (the controller toasts "Badge unlocked: <name>"). */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FWTABadgeAwarded, FName, BadgeId);

/** A token was just collected; Found/Total for the toast "Token 3 of 11". */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FWTATokenCollected, FName, TokenId, int32, Found, int32, Total);

/** Progress was wiped (tokens re-appear, badge counter resets). */
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FWTAProgressReset);

UCLASS()
class WALKTHEARCHIVE_API UWTAProgressSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category = "WTA", meta = (WorldContext = "WorldContextObject"))
	static UWTAProgressSubsystem* Get(const UObject* WorldContextObject);

	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	// --- Events that change progress (each returns true when something new was recorded) ---

	/** Collect a token; broadcasts OnTokenCollected and may award "hunter". False if already collected. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	bool CollectToken(FName TokenId);

	/** Award a badge by id; broadcasts OnBadgeAwarded. False if already owned or unknown. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	bool AwardBadge(FName BadgeId);

	/** An exhibit card was opened. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void NoteExhibit(FName ItemId);

	/** A book page (0-based) was shown. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void NotePage(FName BookId, int32 Page);

	/** A wax scene was watched for long enough. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void NoteWaxScene(FName SceneId);

	/** Distance walked this frame, cm (the character calls this). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void NoteDistance(float Cm);

	/** A staff member was asked something ("curious"). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void NoteQuestionAsked();

	/** A ride finished: awards DT_Rides[RideId].BadgeId (phase 1). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void NoteRideFinished(FName RideId);

	/** A station run finished: awards its badge (scientist, maker, worldbuilder, artist; phase 1+). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void NoteStationFinished(FName StationId);

	/** A talk or class was heard through to its last slide: the Listener badge. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void NoteTalkHeard(FName TalkId);

	/** A class's quiz was passed and a certificate made out to Name: the row's badge, and the certificate is kept. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void NoteCertificate(FName TalkId, const FString& Name);

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool HasHeardTalk(FName TalkId) const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool HasCertificate(FName TalkId) const;

	/** The name a class's certificate was made out to (empty when none). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FString CertificateName(FName TalkId) const;

	/** The name the visitor last gave for a certificate (empty until they do). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FString GetVisitorName() const;

	UFUNCTION(BlueprintCallable, Category = "WTA")
	void SetVisitorName(const FString& Name);

	// --- Queries ---

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool HasToken(FName TokenId) const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool HasBadge(FName BadgeId) const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool HasSeenExhibit(FName ItemId) const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool HasReadPage(FName BookId, int32 Page) const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool HasWatchedWaxScene(FName SceneId) const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 NumBadges() const;

	/** Rows in DT_Badges. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 TotalBadges() const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 NumTokens() const;

	/** Rows in DT_Tokens. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 TotalTokens() const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 NumExhibitsSeen() const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 NumPagesRead() const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 NumWaxScenesWatched() const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	float GetWalkedCm() const;

	// --- Persistence ---

	/** Wipe everything, save, broadcast OnProgressReset. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ResetProgress();

	/** Write the save slot now. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Save();

	/** Read the save slot (creates an empty save when none exists or the version differs). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Load();

	UPROPERTY(BlueprintAssignable, Category = "WTA")
	FWTABadgeAwarded OnBadgeAwarded;

	UPROPERTY(BlueprintAssignable, Category = "WTA")
	FWTATokenCollected OnTokenCollected;

	UPROPERTY(BlueprintAssignable, Category = "WTA")
	FWTAProgressReset OnProgressReset;

	// Thresholds (web progress.js).
	static constexpr float FirstStepsCm = 500.f;
	static constexpr int32 ExplorerExhibits = 5;
	static constexpr int32 BookwormPages = 5;
	static constexpr int32 HistorianScenes = 6;
	static constexpr float SaveDistanceEveryCm = 2000.f;

protected:
	/** Re-check every threshold rule and award what is due. */
	void CheckBadges();

	/** "<book>:<page>" key for the Pages array. */
	static FName PageKey(FName BookId, int32 Page);

	UPROPERTY(Transient)
	TObjectPtr<UWTASaveGame> SaveData;

	/** Distance walked since the last save. */
	float UnsavedWalkCm = 0.f;
};
