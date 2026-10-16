// Walk the Archive - a UButton that knows what it does.
//
// UButton::OnClicked carries no payload, so every button the C++ widgets build is a UWTAActionButton with an
// Action/Arg/Index/Payload. Init() binds OnClicked once; HandleClicked re-broadcasts OnAction(Action, Arg, Index)
// so one UFUNCTION per widget can serve every button (Prev/Next/Close, chips, TOC entries, source links,
// shared-vocabulary actions like OpenItem/GoPlace).

#pragma once

#include "CoreMinimal.h"
#include "Components/Button.h"
#include "WTAActionButton.generated.h"

/** The button was clicked: its Action, Arg and Index. Read Payload from the button itself if needed. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FWTAActionButtonClicked, FName, Action, FName, Arg, int32, Index);

UCLASS()
class WALKTHEARCHIVE_API UWTAActionButton : public UButton
{
	GENERATED_BODY()

public:
	/** Widget-internal verb ("Prev", "Close", "Chip", "Page", "Link", "Graphics") or a shared action (OpenItem ...). */
	UPROPERTY(BlueprintReadWrite, Category = "WTA")
	FName Action;

	/** Row id for shared actions, else NAME_None. */
	UPROPERTY(BlueprintReadWrite, Category = "WTA")
	FName Arg;

	/** Page number, chip index, quality level ... -1 when unused. */
	UPROPERTY(BlueprintReadWrite, Category = "WTA")
	int32 Index = -1;

	/** Free text (a URL for "Link", the chip question for "Chip"). */
	UPROPERTY(BlueprintReadWrite, Category = "WTA")
	FString Payload;

	UPROPERTY(BlueprintAssignable, Category = "WTA")
	FWTAActionButtonClicked OnAction;

	/** Set the fields and bind OnClicked (once). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Init(FName InAction, FName InArg, int32 InIndex);

protected:
	UFUNCTION()
	void HandleClicked();

	bool bBound = false;
};
