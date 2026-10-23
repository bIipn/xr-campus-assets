// Walk the Archive - one person in a guided visit.

#include "Core/WTAPlayerState.h"
#include "Core/WTAText.h"
#include "Net/UnrealNetwork.h"
#include "UI/WTAUIStyle.h"

FLinearColor AWTAPlayerState::GetVisitColor() const
{
	if (bGuide)
	{
		return WTAStyle::FromHex(0xc9a45c);                       // brass, the campus's own accent
	}
	// Muted museum colours that stay apart from each other and from brass.
	static const uint32 Palette[] = { 0x3e7cb1, 0xc0583f, 0x4e9a6a, 0x8d5fa8, 0xd08c2e, 0x2f8c8c, 0xb0476e, 0x6f7f3a,
		0x5a6fb8, 0x9c6b4e, 0x4f9fc2, 0xa65f5f };
	const int32 Count = UE_ARRAY_COUNT(Palette);
	return WTAStyle::FromHex(Palette[(FMath::Max(Slot, 1) - 1) % Count]);
}

FString AWTAPlayerState::GetVisitName() const
{
	if (bNamed && !GetPlayerName().IsEmpty())
	{
		return GetPlayerName();
	}
	return bGuide ? WTAText(TEXT("Guide")).ToString() : FText::Format(WTAText(TEXT("Visitor {0}")), FText::AsNumber(FMath::Max(Slot, 1))).ToString();
}

void AWTAPlayerState::SetVisitName(const FString& Name)
{
	FString Clean = Name.TrimStartAndEnd().Replace(TEXT("\n"), TEXT(" ")).Replace(TEXT("\r"), TEXT(" "));
	if (Clean.Len() > 24)
	{
		Clean = Clean.Left(24).TrimEnd();
	}
	if (Clean.IsEmpty())
	{
		return;
	}
	SetPlayerName(Clean);
	bNamed = true;
	ForceNetUpdate();
}

void AWTAPlayerState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(AWTAPlayerState, bGuide);
	DOREPLIFETIME(AWTAPlayerState, Slot);
	DOREPLIFETIME(AWTAPlayerState, bNamed);
}
