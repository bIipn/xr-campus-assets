// Walk the Archive - game mode.
// Wires the framework classes together: pawn = AWTACharacter, controller = AWTAPlayerController, no HUD class
// (all UI is UMG owned by the controller). At start it builds the NavMesh when the level has none built.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "WTAGameMode.generated.h"

UCLASS(Blueprintable)
class WALKTHEARCHIVE_API AWTAGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AWTAGameMode();

	/** Builds the default NavMesh once when it uses runtime generation and has no tiles yet. */
	virtual void StartPlay() override;
};
