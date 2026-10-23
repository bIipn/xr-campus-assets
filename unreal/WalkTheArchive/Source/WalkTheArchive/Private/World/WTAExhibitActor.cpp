// Walk the Archive - a framed exhibit, the Freedom to Read board, or a Wax Hall reading card.

#include "World/WTAExhibitActor.h"
#include "Core/WTAText.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "Systems/WTAContentSubsystem.h"
#include "Systems/WTAProgressSubsystem.h"

AWTAExhibitActor::AWTAExhibitActor()
{
}

bool AWTAExhibitActor::IsAlreadySeen() const
{
	const UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this);
	return Progress != nullptr && !ItemId.IsNone() && Progress->HasSeenExhibit(ItemId);
}

void AWTAExhibitActor::ReadRow()
{
	Super::ReadRow();

	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	const FWTAExhibitRow* Row = Content ? Content->FindExhibit(ItemId) : nullptr;
	if (Row == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("%s: no DT_Exhibits row '%s'"), *GetName(), *ItemId.ToString());
		Label = WTAText(TEXT("Open"));
		return;
	}

	Label = FText::Format(WTAText(TEXT("Open \u00B7 {0}")), Row->Title);
	ViewSpot = Row->View;
}

void AWTAExhibitActor::Interact_Implementation(AWTAPlayerController* Controller)
{
	if (Controller == nullptr)
	{
		return;
	}

	// Walk to the viewing spot first, then open the card (the controller notes the exhibit as seen).
	if (ViewSpot.bValid)
	{
		Controller->GoToView(ViewSpot, true);
	}
	Controller->OpenExhibit(ItemId);
}
