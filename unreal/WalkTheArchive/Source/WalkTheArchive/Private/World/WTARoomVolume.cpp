// Walk the Archive - a room box; the player's pawn overlapping it enters the room.

#include "World/WTARoomVolume.h"
#include "Components/BoxComponent.h"
#include "Engine/EngineTypes.h"
#include "GameFramework/Pawn.h"
#include "Systems/WTARoomSubsystem.h"

AWTARoomVolume::AWTARoomVolume()
{
	PrimaryActorTick.bCanEverTick = false;

	// Overlaps pawns only; blocks nothing and never shows up in a trace.
	Bounds = CreateDefaultSubobject<UBoxComponent>(TEXT("Bounds"));
	SetRootComponent(Bounds);
	Bounds->SetBoxExtent(Extent);
	Bounds->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Bounds->SetCollisionObjectType(ECC_WorldDynamic);
	Bounds->SetCollisionResponseToAllChannels(ECR_Ignore);
	Bounds->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	Bounds->SetGenerateOverlapEvents(true);
	Bounds->SetCanEverAffectNavigation(false);
	Bounds->CanCharacterStepUpOn = ECB_No;
	Bounds->SetHiddenInGame(true);
}

void AWTARoomVolume::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

	if (Bounds != nullptr)
	{
		Bounds->SetBoxExtent(Extent, false);
	}
}

void AWTARoomVolume::NotifyActorBeginOverlap(AActor* OtherActor)
{
	Super::NotifyActorBeginOverlap(OtherActor);

	const APawn* Pawn = Cast<APawn>(OtherActor);
	if (Pawn == nullptr || !Pawn->IsPlayerControlled())
	{
		return;
	}

	if (UWTARoomSubsystem* Rooms = UWTARoomSubsystem::Get(this))
	{
		Rooms->EnterRoom(RoomId);
	}
}
