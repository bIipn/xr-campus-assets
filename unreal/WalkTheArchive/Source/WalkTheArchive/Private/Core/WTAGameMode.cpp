// Walk the Archive - game mode.

#include "Core/WTAGameMode.h"
#include "Core/WTACharacter.h"
#include "Core/WTAGameState.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "Core/WTAPlayerState.h"
#include "GameFramework/GameStateBase.h"
#include "NavigationSystem.h"
#include "NavMesh/RecastNavMesh.h"

AWTAGameMode::AWTAGameMode()
{
	DefaultPawnClass = AWTACharacter::StaticClass();
	PlayerControllerClass = AWTAPlayerController::StaticClass();
	GameStateClass = AWTAGameState::StaticClass();
	PlayerStateClass = AWTAPlayerState::StaticClass();
	// All UI is UMG owned by the controller, so no AHUD class.
	HUDClass = nullptr;
}

void AWTAGameMode::StartPlay()
{
	Super::StartPlay();
	BuildNavigationIfEmpty(GetWorld());
}

void AWTAGameMode::BuildNavigationIfEmpty(UWorld* World)
{
#if WITH_RECAST
	// The headless setup run cannot build the NavMesh (the editor still holds its async-load navigation lock), so the
	// saved level has the bounds volume but no tiles. The navigation system spawns the Default RecastNavMesh at load
	// without building it; with RuntimeGeneration=Dynamic one build here (well under a second for the campus) lets
	// click-to-walk and the tour walk instead of teleporting. A NavMesh built and saved in the editor is kept as is.
	UNavigationSystemV1* NavSys = World ? UNavigationSystemV1::GetCurrent(World) : nullptr;
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

void AWTAGameMode::PostLogin(APlayerController* NewPlayer)
{
	// Before Super: Super spawns and possesses the pawn, and the visitor's pawn is placed by its slot.
	AWTAPlayerState* Person = NewPlayer ? NewPlayer->GetPlayerState<AWTAPlayerState>() : nullptr;
	if (Person != nullptr)
	{
		if (NewPlayer->IsLocalController())
		{
			// The machine's own player: in a listen server (a guided visit) the guide.
			Person->bGuide = GetNetMode() == NM_ListenServer;
			Person->Slot = 0;
		}
		else
		{
			TSet<int32> Taken;
			if (GameState != nullptr)
			{
				for (APlayerState* Other : GameState->PlayerArray)
				{
					if (const AWTAPlayerState* OtherPerson = Cast<AWTAPlayerState>(Other))
					{
						if (OtherPerson != Person)
						{
							Taken.Add(OtherPerson->Slot);
						}
					}
				}
			}
			int32 Slot = 1;
			while (Taken.Contains(Slot))
			{
				++Slot;
			}
			Person->bGuide = false;
			Person->Slot = Slot;
			UE_LOG(LogWTA, Log, TEXT("WTA_VISIT joined slot %d (%s)"), Slot, *Person->GetPlayerName());
		}
	}
	Super::PostLogin(NewPlayer);
}

void AWTAGameMode::Logout(AController* Exiting)
{
	if (const AWTAPlayerState* Person = Exiting ? Exiting->GetPlayerState<AWTAPlayerState>() : nullptr)
	{
		if (!Person->bGuide)
		{
			UE_LOG(LogWTA, Log, TEXT("WTA_VISIT left slot %d (%s)"), Person->Slot, *Person->GetVisitName());
		}
	}
	Super::Logout(Exiting);
}
