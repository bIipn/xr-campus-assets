// Walk the Archive - staff answers (port of the web engine.js, rules moved to DT_StaffRules).
//
// Ask(StaffId, Question) tries, in order, and returns the first hit:
//   1. greeting        the question is just hi/hello/hey (<= 2 words)             -> staff GreetingShort
//   2. rules < 100     DT_StaffRules by Order; FRegexPattern (case-insensitive, the pattern wrapped in (?i)),
//                      honouring MaxWords (0 = any), StaffOnly, StaffNot          -> Answer + Action/ActionArg
//   3. directions      a DT_Places alias contained in the question                -> Directions + GoPlace(place)
//   4. title match     an exhibit or book title contained in the question         -> Description/Subtitle + OpenItem/OpenBook
//   5. rules >= 100    as 2
//   6. search          TF-IDF over Facts, Lessons, exhibit Description/More and book pages; the best sentence of
//                      the best document (web searchKB/bestSentence)               -> that sentence (+ OpenItem/OpenBook)
//   7. fallback        the staff's Fallback text
// The chat widget shows Text and the controller runs Action/ActionArg after a short delay.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Data/WTATypes.h"
#include "WTADialogueSubsystem.generated.h"

/** One answer: text to show plus an optional action from the shared vocabulary. */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAReply
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FText Text;

	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FName Action;

	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FName ActionArg;
};

/** One searchable document of the keyword index (not reflected). */
struct FWTASearchDoc
{
	FString Title;
	TArray<FString> Sentences;
	TMap<FString, int32> TermCounts;
	int32 NumTerms = 0;
	FName Action;
	FName ActionArg;
	/** Sentence appended to a search answer ("That's from "Mission" in Gallery 1."); may be empty. */
	FString Source;
};

UCLASS()
class WALKTHEARCHIVE_API UWTADialogueSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category = "WTA", meta = (WorldContext = "WorldContextObject"))
	static UWTADialogueSubsystem* Get(const UObject* WorldContextObject);

	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/** Answer a question as StaffId (see the header comment for the order of tries). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	FWTAReply Ask(FName StaffId, const FString& Question);

	/** The staff's Greeting (long, first open) or GreetingShort. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FText GetGreeting(FName StaffId, bool bShort) const;

	/** The staff's suggestion chips. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	TArray<FText> GetChips(FName StaffId) const;

	/** The staff's Help text. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FText GetHelp(FName StaffId) const;

	/** Rebuild the keyword index from the content tables (done lazily on the first Ask). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void RebuildIndex();

protected:
	bool TryGreeting(FName StaffId, const FString& Question, FWTAReply& OutReply) const;
	bool TryRules(FName StaffId, const FString& Question, int32 MinOrder, int32 MaxOrder, FWTAReply& OutReply) const;
	bool TryDirections(const FString& Question, FWTAReply& OutReply) const;
	bool TryTitleMatch(const FString& Question, FWTAReply& OutReply) const;
	bool TrySearch(const FString& Question, FWTAReply& OutReply);
	FWTAReply Fallback(FName StaffId) const;

	/** Lower-case word tokens (letters and digits), stop words removed. */
	static void Tokenize(const FString& Text, TArray<FString>& OutTokens);

	/** Split on . ! ? keeping sentences of at least 3 words. */
	static void SplitSentences(const FString& Text, TArray<FString>& OutSentences);

	static int32 CountWords(const FString& Text);

	/** Add one document to the index. */
	void AddDoc(const FString& Title, const FString& Body, FName Action, FName ActionArg);

	TArray<FWTASearchDoc> Docs;
	TMap<FString, int32> DocFrequency;
	bool bIndexBuilt = false;
};
