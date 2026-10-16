// Walk the Archive - a UButton that knows what it does.

#include "UI/WTAActionButton.h"

void UWTAActionButton::Init(FName InAction, FName InArg, int32 InIndex)
{
	Action = InAction;
	Arg = InArg;
	Index = InIndex;

	if (!bBound)
	{
		OnClicked.AddDynamic(this, &UWTAActionButton::HandleClicked);
		bBound = true;
	}
}

void UWTAActionButton::HandleClicked()
{
	OnAction.Broadcast(Action, Arg, Index);
}
