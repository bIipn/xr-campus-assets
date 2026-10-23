// Walk the Archive - the name over a person's figure in a guided visit (built in C++, no widget asset).
//
// A small dark plate with the person's colour as a dot and their name; the guide's has a brass edge and a GUIDE
// kicker. AWTACharacter shows it in screen space over other people's figures (UWidgetComponent).

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "WTANameTagWidget.generated.h"

class UBorder;
class UTextBlock;

UCLASS()
class WALKTHEARCHIVE_API UWTANameTagWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void SetPerson(const FText& Name, bool bGuide, const FLinearColor& Color);

protected:
	virtual void NativeOnInitialized() override;

	UPROPERTY(Transient) TObjectPtr<UBorder> Plate;
	UPROPERTY(Transient) TObjectPtr<UBorder> Dot;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> KickerText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> NameText;
};
