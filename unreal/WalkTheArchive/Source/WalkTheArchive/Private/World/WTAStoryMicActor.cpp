// Walk the Archive - the Lost Stories booth's microphone.

#include "World/WTAStoryMicActor.h"
#include "Core/WTACharacter.h"
#include "Core/WTAPlayerController.h"
#include "Core/WTAText.h"
#include "EngineUtils.h"
#include "Systems/WTAStoriesSubsystem.h"
#include "World/WTAAttractComponent.h"
#include "World/WTASeatActor.h"

AWTAStoryMicActor::AWTAStoryMicActor()
{
	PickExtent = FVector(30.f, 30.f, 25.f);
	if (Attract != nullptr)
	{
		Attract->bEnabled = false;
	}
}

void AWTAStoryMicActor::ReadRow()
{
	Super::ReadRow();
	Label = WTAText(TEXT("Tell a story"));
}

FText AWTAStoryMicActor::GetInteractLabel_Implementation() const
{
	const UWTAStoriesSubsystem* Stories = UWTAStoriesSubsystem::Get(this);
	if (Stories != nullptr && Stories->GetBoothState() == EWTABoothState::Recording)
	{
		return WTAText(TEXT("Recording · E for the card"));
	}
	return Label;
}

void AWTAStoryMicActor::Interact_Implementation(AWTAPlayerController* Controller)
{
	if (Controller == nullptr)
	{
		return;
	}
	// Sit down facing the microphone first, unless already sitting there.
	AWTACharacter* Player = Controller->GetWTACharacter();
	if (Player != nullptr)
	{
		for (TActorIterator<AWTASeatActor> It(GetWorld()); It; ++It)
		{
			if (It->SeatId == TellerSeatId)
			{
				if (!(Player->IsSeated() && Player->GetSeat() == *It))
				{
					Player->SitAt(*It, It->GetSitPoint(), It->SeatYaw);
				}
				break;
			}
		}
	}
	Controller->OpenStoryBooth();
}
