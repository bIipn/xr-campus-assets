// Walk the Archive - game mode.
// Only wires the framework classes together: pawn = AWTACharacter, controller = AWTAPlayerController, no HUD class
// (all UI is UMG owned by the controller).

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
};
