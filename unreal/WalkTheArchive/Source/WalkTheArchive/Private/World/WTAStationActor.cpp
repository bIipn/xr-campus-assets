// Walk the Archive - a hands-on station (sieve, titration, pendulum, bench, diorama, easel).

#include "World/WTAStationActor.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "Systems/WTAContentSubsystem.h"

AWTAStationActor::AWTAStationActor()
{
}

void AWTAStationActor::ReadRow()
{
	Super::ReadRow();

	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	const FWTAStationRow* Row = Content ? Content->FindStation(StationId) : nullptr;
	if (Row == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("%s: no DT_Stations row '%s'"), *GetName(), *StationId.ToString());
		Label = FText::FromString(TEXT("Use"));
		return;
	}

	const FText GoLabel = Row->GoLabel.IsEmpty() ? FText::FromString(TEXT("Use")) : Row->GoLabel;
	Label = FText::Format(FText::FromString(TEXT("{0} \u00B7 {1}")), GoLabel, Row->Title);
	ViewSpot = Row->View;
}

void AWTAStationActor::Interact_Implementation(AWTAPlayerController* Controller)
{
	if (Controller == nullptr)
	{
		return;
	}

	if (ViewSpot.bValid)
	{
		Controller->GoToView(ViewSpot, true);
	}
	Controller->OpenStation(StationId);
}
