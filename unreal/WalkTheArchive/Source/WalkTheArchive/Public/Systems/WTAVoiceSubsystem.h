// Walk the Archive - the museum reads a card aloud for you.
//
// Every catalog card, wax scene, station, ride, badge and fact has a narration clip at
// /Game/WTA/Audio/VO_<kind>_<id>, made from the very words on the card (Content/Python/wta_voice imports them;
// the voice is Kokoro-82M, Apache 2.0, run outside the editor). Read() finds a clip by kind and row id and plays
// it; opening another card, or pressing the button again, stops the one before, so two voices never overlap.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "WTAVoiceSubsystem.generated.h"

class UAudioComponent;
class USoundBase;

/** Fired when the voice starts, stops or reaches the end of a clip, so a Listen button can relabel itself. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FWTAVoiceChanged);

UCLASS()
class WALKTHEARCHIVE_API UWTAVoiceSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintAssignable, Category = "WTA|Voice")
	FWTAVoiceChanged OnVoiceChanged;

	UFUNCTION(BlueprintPure, Category = "WTA|Voice", meta = (WorldContext = "WorldContextObject"))
	static UWTAVoiceSubsystem* Get(const UObject* WorldContextObject);

	/** /Game/WTA/Audio/VO_<Kind>_<Id>, with the id's hyphens as underscores (an asset name cannot hold one). */
	UFUNCTION(BlueprintPure, Category = "WTA|Voice")
	static FString ClipPath(FName Kind, FName Id);

	/** True when that card has a clip: the Listen button only appears for cards that do. */
	UFUNCTION(BlueprintCallable, Category = "WTA|Voice")
	bool HasClip(FName Kind, FName Id);

	/** Reads the card aloud, stopping whatever was being read. False when there is no clip. */
	UFUNCTION(BlueprintCallable, Category = "WTA|Voice")
	bool Read(FName Kind, FName Id);

	/** Stops reading (no-op when nothing is). */
	UFUNCTION(BlueprintCallable, Category = "WTA|Voice")
	void Stop();

	UFUNCTION(BlueprintPure, Category = "WTA|Voice")
	bool IsReading() const;

	/** What is being read now ("exhibit", "ca-200"), or none. */
	UFUNCTION(BlueprintPure, Category = "WTA|Voice")
	bool IsReadingCard(FName Kind, FName Id) const;

	/** Reading volume, 0..1 (the menu's Voice slider once there is one). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Voice")
	float Volume = 1.f;

	virtual void Deinitialize() override;

protected:
	/** Bound to the voice component: the clip ran out on its own. */
	UFUNCTION()
	void HandleFinished();

	/** Clips looked up so far, by asset path; a card with no clip is remembered as null. */
	UPROPERTY(Transient)
	TMap<FString, TObjectPtr<USoundBase>> Clips;

	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> Voice;

	FName ReadingKind;
	FName ReadingId;
};
