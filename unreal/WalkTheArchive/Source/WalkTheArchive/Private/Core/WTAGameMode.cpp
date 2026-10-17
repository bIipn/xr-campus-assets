// Walk the Archive - game mode.

#include "Core/WTAGameMode.h"
#include "Core/WTACharacter.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "NavigationSystem.h"
#include "NavMesh/RecastNavMesh.h"

AWTAGameMode::AWTAGameMode()
{
	DefaultPawnClass = AWTACharacter::StaticClass();
	PlayerControllerClass = AWTAPlayerController::StaticClass();
	// All UI is UMG owned by the controller, so no AHUD class.
	HUDClass = nullptr;
}

void AWTAGameMode::StartPlay()
{
	Super::StartPlay();

#if WITH_RECAST
	// The headless setup run cannot build the NavMesh (the editor still holds its async-load navigation lock), so the
	// saved level has the bounds volume but no tiles. The navigation system spawns the Default RecastNavMesh at load
	// without building it; with RuntimeGeneration=Dynamic one build here (well under a second for the campus) lets
	// click-to-walk and the tour walk instead of teleporting. A NavMesh built and saved in the editor is kept as is.
	UNavigationSystemV1* NavSys = UNavigationSystemV1::GetCurrent(GetWorld());
	if (NavSys == nullptr)
	{
		return;
	}
	const ARecastNavMesh* NavMesh = Cast<ARecastNavMesh>(NavSys->GetDefaultNavDataInstance(FNavigationSystem::Create));
	if (NavMesh == nullptr || NavMesh->GetRuntimeGenerationMode() != ERuntimeGenerationType::Dynamic || NavMesh->GetNumActiveTiles() > 0)
	{
		return;
	}
	UE_LOG(LogWTA, Log, TEXT("Navigation: %s has no tiles yet; building it"), *NavMesh->GetName());
	NavSys->Build();
#endif
}
