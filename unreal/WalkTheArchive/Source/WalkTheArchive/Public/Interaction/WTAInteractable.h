// Walk the Archive - the interface every pickable thing implements.
//
// Callers never cast to the interface; they go through the generated statics:
//   IWTAInteractable::Execute_GetInteractLabel(Actor)
//   IWTAInteractable::Execute_Interact(Actor, Controller)
//   IWTAInteractable::Execute_GetViewSpot(Actor, OutView)
// after checking Actor->Implements<UWTAInteractable>(). Implementers override the _Implementation functions.

#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "Data/WTATypes.h"
#include "WTAInteractable.generated.h"

class AWTAPlayerController;

UINTERFACE(BlueprintType, Blueprintable)
class WALKTHEARCHIVE_API UWTAInteractable : public UInterface
{
	GENERATED_BODY()
};

class WALKTHEARCHIVE_API IWTAInteractable
{
	GENERATED_BODY()

public:
	/** Short label under the crosshair, e.g. "Open · Mission" or "Ask Margaret". */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "WTA")
	FText GetInteractLabel() const;

	/** The player clicked / pressed E on this. The controller is the hub for whatever happens next. */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "WTA")
	void Interact(AWTAPlayerController* Controller);

	/** Where to stand to look at this (the exhibit's View, the station's View, the staff's TalkView). False = none. */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "WTA")
	bool GetViewSpot(FWTAView& OutView) const;
};
