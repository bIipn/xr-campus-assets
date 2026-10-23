// Walk the Archive - one person in a guided visit (the guide or a visitor).
//
// Solo play has one player state and nobody to show it to. In a guided visit (UWTAVisitSubsystem) every machine
// sees every person: the name (APlayerState's own, sent from the visit card through the controller's
// ServerSetVisitName), whether this person is the guide, and the slot that gives them their place round a stop and
// their colour - 0 is the guide, visitors 1, 2, ... in the order they came. AWTAGameMode::PostLogin hands the slots
// out; a slot freed by someone leaving goes to the next to arrive.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerState.h"
#include "WTAPlayerState.generated.h"

UCLASS()
class WALKTHEARCHIVE_API AWTAPlayerState : public APlayerState
{
	GENERATED_BODY()

public:
	/** The person leading the visit (the machine it is hosted on). */
	UPROPERTY(Replicated, BlueprintReadOnly, Category = "WTA")
	bool bGuide = false;

	/** 0 for the guide, 1.. for the visitors: their place round a stop (UWTAVisitSubsystem::GroupSpot) and colour. */
	UPROPERTY(Replicated, BlueprintReadOnly, Category = "WTA")
	int32 Slot = 0;

	/** The figure's and the name tag's colour: brass for the guide, then a palette by slot. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FLinearColor GetVisitColor() const;

	/** The name to show: the player name, or "Visitor <slot>" while it is still the machine's default. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FString GetVisitName() const;

	/** Server: the visit card's name (trimmed, at most 24 characters; empty keeps the old one). */
	void SetVisitName(const FString& Name);

	/** True once this person's own game sent a name (a visitor's game is then loaded and playing). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsNamed() const { return bNamed; }

	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
	/** True once a name came from the visit card (the engine's default is the computer's name). */
	UPROPERTY(Replicated)
	bool bNamed = false;
};
