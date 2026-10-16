// Walk the Archive - a ride entrance (coaster, drop, dive). Phase 0 opens the ride card.

#include "World/WTARideActor.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "Systems/WTAContentSubsystem.h"

AWTARideActor::AWTARideActor()
{
}

void AWTARideActor::ReadRow()
{
	Super::ReadRow();

	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	const FWTARideRow* Row = Content ? Content->FindRide(RideId) : nullptr;
	if (Row == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("%s: no DT_Rides row '%s'"), *GetName(), *RideId.ToString());
		Label = FText::FromString(TEXT("Ride"));
		return;
	}

	Label = FText::Format(FText::FromString(TEXT("Ride \u00B7 {0}")), Row->DisplayName);
	// The ride card opens from wherever the player stands; ExitView is for after the ride (phase 1).
}

void AWTARideActor::Interact_Implementation(AWTAPlayerController* Controller)
{
	if (Controller == nullptr)
	{
		return;
	}
	Controller->OpenRide(RideId);
}
