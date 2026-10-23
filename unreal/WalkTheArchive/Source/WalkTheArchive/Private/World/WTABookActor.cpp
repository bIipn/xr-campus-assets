// Walk the Archive - a book on the featured table or a stack end.

#include "World/WTABookActor.h"
#include "Core/WTAText.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "Systems/WTAContentSubsystem.h"

AWTABookActor::AWTABookActor()
{
}

void AWTABookActor::ReadRow()
{
	Super::ReadRow();

	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	const FWTABookRow* Row = Content ? Content->FindBook(BookId) : nullptr;
	if (Row == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("%s: no DT_Books row '%s'"), *GetName(), *BookId.ToString());
		Label = WTAText(TEXT("Read"));
		return;
	}

	Label = FText::Format(WTAText(TEXT("Read \u00B7 {0}")), Row->Title);
	// Books have no viewing spot; the reader opens where the player stands.
}

void AWTABookActor::Interact_Implementation(AWTAPlayerController* Controller)
{
	if (Controller == nullptr)
	{
		return;
	}
	Controller->OpenBook(BookId, OpenPage);
}
