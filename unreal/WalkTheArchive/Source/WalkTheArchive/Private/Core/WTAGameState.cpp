// Walk the Archive - what everybody in a guided visit shares.

#include "Core/WTAGameState.h"
#include "Core/WTAGameMode.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerState.h"
#include "Engine/World.h"
#include "Net/UnrealNetwork.h"
#include "Systems/WTAVisitSubsystem.h"

void AWTAGameState::BeginPlay()
{
	Super::BeginPlay();
	if (GetNetMode() == NM_Client)
	{
		// A visitor's machine has no game mode: build its own NavMesh here (click-to-walk and the stops walk on it).
		AWTAGameMode::BuildNavigationIfEmpty(GetWorld());
		// A gathering already in the state when this visitor arrives happened before them.
		if (UWTAVisitSubsystem* Visit = UWTAVisitSubsystem::Get(this))
		{
			Visit->NoteGatherSerial(GatherSerial);
		}
	}
}

void AWTAGameState::LeadStop(int32 Index)
{
	if (!HasAuthority())
	{
		return;
	}
	TourStop = Index;
	++TourSerial;
	ForceNetUpdate();
	UE_LOG(LogWTA, Log, TEXT("WTA_VISIT lead stop %d (serial %d)"), Index, TourSerial);
}

void AWTAGameState::Gather(const FVector& Floor, float Yaw)
{
	if (!HasAuthority())
	{
		return;
	}
	GatherFloor = Floor;
	GatherYaw = Yaw;
	++GatherSerial;
	ForceNetUpdate();
	UE_LOG(LogWTA, Log, TEXT("WTA_VISIT gather at %s yaw %.0f (serial %d)"), *Floor.ToCompactString(), Yaw, GatherSerial);
}

AWTAPlayerState* AWTAGameState::GetGuide() const
{
	for (APlayerState* Player : PlayerArray)
	{
		AWTAPlayerState* Person = Cast<AWTAPlayerState>(Player);
		if (Person != nullptr && Person->bGuide)
		{
			return Person;
		}
	}
	return nullptr;
}

int32 AWTAGameState::NumVisitors() const
{
	int32 Count = 0;
	for (APlayerState* Player : PlayerArray)
	{
		const AWTAPlayerState* Person = Cast<AWTAPlayerState>(Player);
		if (Person != nullptr && !Person->bGuide && !Person->IsInactive())
		{
			++Count;
		}
	}
	return Count;
}

void AWTAGameState::OnRep_Tour()
{
	if (UWTAVisitSubsystem* Visit = UWTAVisitSubsystem::Get(this))
	{
		Visit->HandleTourReplicated(TourStop, TourSerial);
	}
}

void AWTAGameState::OnRep_Gather()
{
	if (UWTAVisitSubsystem* Visit = UWTAVisitSubsystem::Get(this))
	{
		Visit->HandleGatherReplicated(GatherFloor, GatherYaw, GatherSerial);
	}
}

void AWTAGameState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AWTAGameState, TourStop);
	DOREPLIFETIME(AWTAGameState, TourSerial);
	DOREPLIFETIME(AWTAGameState, GatherSerial);
	DOREPLIFETIME(AWTAGameState, GatherFloor);
	DOREPLIFETIME(AWTAGameState, GatherYaw);
}
