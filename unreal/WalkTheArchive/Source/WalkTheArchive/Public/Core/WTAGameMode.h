// Walk the Archive - game mode.
// Wires the framework classes together: pawn = AWTACharacter, controller = AWTAPlayerController, game state =
// AWTAGameState, player state = AWTAPlayerState, the plain AHUD (all UI is UMG owned by the controller). At start it
// builds the NavMesh when the level has none built.
//
// Guided visits (UWTAVisitSubsystem): the guide's machine runs this as a listen server. PostLogin makes the guide's
// own player the guide (slot 0) and gives each visitor who joins the lowest free slot from 1; the visitor's pawn is
// then put at their place round the guide (AWTAPlayerController::OnPossess). Pawns always spawn (there is no
// PlayerStart: the engine falls back to the world origin, where the guide may be standing).

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

	/** Slots and the guide's flag before the new player's pawn is spawned. */
	virtual void PostLogin(APlayerController* NewPlayer) override;
	virtual void Logout(AController* Exiting) override;

	/** Always spawns (nudged out of the way where there is room): the campus has no PlayerStart, so every pawn starts
	 *  at the world origin before the controller moves it to its view, and a visitor joining must not fail to spawn
	 *  because someone stands there. */
	virtual APawn* SpawnDefaultPawnAtTransform_Implementation(AController* NewPlayer, const FTransform& SpawnTransform) override;

	/** One NavMesh build when the default one is runtime-generated and still has no tiles (also a visitor's machine). */
	static void BuildNavigationIfEmpty(UWorld* World);
};
