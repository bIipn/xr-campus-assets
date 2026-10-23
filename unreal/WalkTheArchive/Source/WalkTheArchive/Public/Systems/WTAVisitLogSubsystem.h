// Walk the Archive - the visit log: what a visit did, for the library's own reports.
//
// One CSV per play session in Saved/Visits/visit_<yyyymmdd-hhmmss>.csv, appended as it happens so a crash loses
// nothing: a "room" line when a room is left (which room, when it was entered, for how many seconds), a "card"
// line when a card opens (an exhibit, a book, a station, a ride, a talk's quiz, a course, the badges, a staff
// chat), a "token" line for each token found, a "badge" line for each badge earned, and a "pos" line every
// SampleSeconds with where the visitor stands (room, x, y in metres) for the heatmap. No names: the file knows
// the session, not the person. unreal/Tools/common/visit_report.py turns a folder of these into a report with
// the dwell times per room, the most opened cards and a heatmap over the campus plan.
//
// Format: utc,kind,a,b,c  (utc = seconds since 1970; room: a = room id, b = seconds entered at, c = seconds
// stayed; card: a = kind, b = id; token/badge: a = id; pos: a = room id, b = x m, c = y m).

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "WTAVisitLogSubsystem.generated.h"

UCLASS()
class WALKTHEARCHIVE_API UWTAVisitLogSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category = "WTA", meta = (WorldContext = "WorldContextObject"))
	static UWTAVisitLogSubsystem* Get(const UObject* WorldContextObject);

	/** A card opened: Kind = exhibit, book, station, ride, quiz, course, badges, places, hunt, chat; Id = its row.
	    The same kind and id again in a row (a page turned, a step taken) counts as the same open. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void NoteCard(FName Kind, FName Id);

	UFUNCTION(BlueprintCallable, Category = "WTA")
	void NoteToken(FName TokenId);

	UFUNCTION(BlueprintCallable, Category = "WTA")
	void NoteBadge(FName BadgeId);

	/** The file this session writes (empty until the first line). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FString GetLogFile() const { return LogFile; }

	/** Lines written this session. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 GetLinesWritten() const { return LinesWritten; }

	/** Seconds between position samples (0 = none). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	float SampleSeconds = 2.f;

	/** Where the logs go: <Saved>/Visits. */
	static FString VisitsDir();

	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;
	virtual void Deinitialize() override;

protected:
	UFUNCTION()
	void HandleRoomChanged(FName RoomId);

	UFUNCTION()
	void HandleTokenCollected(FName TokenId, int32 Found, int32 Total);

	UFUNCTION()
	void HandleBadgeAwarded(FName BadgeId);

	void Sample();
	void CloseRoom();
	void Write(const TCHAR* Kind, const FString& A, const FString& B, const FString& C);

	FString LogFile;
	int32 LinesWritten = 0;
	FName LastCardKind;
	FName LastCardId;
	FName CurrentRoom;
	double RoomEnteredAt = 0.0;
	FTimerHandle SampleTimer;
};
