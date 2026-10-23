// Walk the Archive - a seat.

#include "World/WTASeatActor.h"
#include "Core/WTAText.h"
#include "Components/BoxComponent.h"
#include "Core/WTACharacter.h"
#include "Core/WTAPlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "World/WTAAttractComponent.h"

#define LOCTEXT_NAMESPACE "WTASeat"

AWTASeatActor::AWTASeatActor()
{
	// a cushion's worth of pick volume: the editor Python widens it to the seat it sits on
	PickExtent = FVector(28.f, 28.f, 18.f);
	if (Attract != nullptr)
	{
		Attract->bEnabled = false;                 // a seat does not call you over like an exhibit does
	}
}

bool AWTASeatActor::IsOccupied() const
{
	const AWTACharacter* Player = Cast<AWTACharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
	return Player != nullptr && Player->IsSeated() && Player->GetSeat() == this;
}

FText AWTASeatActor::GetInteractLabel_Implementation() const
{
	return IsOccupied() ? WTAText(TEXT("Stand up")) : Label;
}

void AWTASeatActor::Interact_Implementation(AWTAPlayerController* Controller)
{
	AWTACharacter* Player = Controller != nullptr ? Controller->GetWTACharacter() : nullptr;
	if (Player == nullptr)
	{
		return;
	}
	if (Player->IsSeated() && Player->GetSeat() == this)
	{
		Player->StandUp(true);
		return;
	}
	Player->SitAt(this, GetSitPoint(), SeatYaw);
}

void AWTASeatActor::ReadRow()
{
	Label = WTAText(TEXT("Sit"));
	// where to stand to look at it: a step in front of the seat, facing it (the QA's interact phase and anyone
	// sent to it stand here)
	const FVector Forward = FRotator(0.f, SeatYaw, 0.f).Vector();
	ViewSpot.Location = GetSitPoint() + Forward * 110.f + FVector(0.f, 0.f, 120.f);
	ViewSpot.Yaw = SeatYaw + 180.f;
	ViewSpot.Pitch = -FMath::RadiansToDegrees(FMath::Atan2(115.f, 110.f));    // the crosshair lands just above the cushion
	ViewSpot.bValid = true;
}

#undef LOCTEXT_NAMESPACE
