// Walk the Archive - the guided tour (35 stops from DT_Tour, sorted by Index).
//
// Start/Next/Back/End move Index and broadcast OnTourChanged(Index) (-1 = ended). Each stop walks the player
// to its View (or, when the View is not valid, the exhibit's View via ItemId) through the controller's GoToView,
// and the controller fills the HUD tour bar ("Stop n of 35", title, date label, body, Open button).
// OpenCurrent() runs the stop's Action/ActionArg through AWTAPlayerController::RunAction. The last stop's
// Next ends the tour ("Explore on your own").

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Data/WTATypes.h"
#include "WTATourSubsystem.generated.h"

/** Index of the stop now showing, or -1 when the tour ended. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FWTATourChanged, int32, Index);

UCLASS()
class WALKTHEARCHIVE_API UWTATourSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category = "WTA", meta = (WorldContext = "WorldContextObject"))
	static UWTATourSubsystem* Get(const UObject* WorldContextObject);

	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/** Begin at stop 0 (restarts if already touring). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Start();

	/** Next stop; on the last stop ends the tour. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Next();

	/** Previous stop (stays on 0). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Back();

	/** Stop touring and hide the bar. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void End();

	/** Run the current stop's action (its Open button). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void OpenCurrent();

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsTouring() const { return Index >= 0; }

	/** 0-based stop index, -1 when not touring. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 GetIndex() const { return Index; }

	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 GetNumStops() const { return StopIds.Num(); }

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsLastStop() const { return Index >= 0 && Index == StopIds.Num() - 1; }

	/** Copy of the current stop row; false when not touring. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	bool GetCurrentStop(FWTATourStopRow& OutStop) const;

	UPROPERTY(BlueprintAssignable, Category = "WTA")
	FWTATourChanged OnTourChanged;

protected:
	/** Set Index, walk the player to the stop's view, broadcast. */
	void ShowStop(int32 NewIndex);

	/** Read DT_Tour row names sorted by Index. */
	void CacheStops();

	TArray<FName> StopIds;
	int32 Index = -1;
};
