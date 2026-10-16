// Walk the Archive - game mode.

#include "Core/WTAGameMode.h"
#include "Core/WTACharacter.h"
#include "Core/WTAPlayerController.h"

AWTAGameMode::AWTAGameMode()
{
	DefaultPawnClass = AWTACharacter::StaticClass();
	PlayerControllerClass = AWTAPlayerController::StaticClass();
	// All UI is UMG owned by the controller, so no AHUD class.
	HUDClass = nullptr;
}
