// Walk the Archive - the intro / pause menu (built in C++, no widget asset).
//
// Title "Walk the Archive", a subtitle line, then: Enter (or Resume when paused), Take the tour, a Graphics row
// (Low, Medium, High, Epic, Cinematic, Auto; the current preset is printed next to it) and Quit.
// Buttons go through HandleAction: "Enter" closes the menu, "Tour" closes it and starts the tour, "Graphics"
// applies Index (0..4) or runs auto-detect for -1, "Quit" calls UKismetSystemLibrary::QuitGame.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "WTAMenuWidget.generated.h"

class UBorder;
class UHorizontalBox;
class UTextBlock;
class UWTAActionButton;

UCLASS()
class WALKTHEARCHIVE_API UWTAMenuWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Show the menu; bIntro = first screen (Enter + subtitle) rather than the pause menu (Resume). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Open(bool bIntro);

	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Close();

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsOpen() const { return bOpen; }

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsIntro() const { return bIntro; }

	/** Re-read the current preset into the graphics label. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void RefreshGraphicsLabel();

protected:
	virtual void NativeOnInitialized() override;

	/** Buttons: "Enter", "Tour", "Graphics" (Index), "Quit". */
	UFUNCTION()
	void HandleAction(FName Action, FName Arg, int32 Index);

	UPROPERTY(Transient) TObjectPtr<UBorder> Scrim;
	UPROPERTY(Transient) TObjectPtr<UBorder> Card;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> TitleText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> SubtitleText;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> EnterButton;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> EnterText;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> TourButton;
	UPROPERTY(Transient) TObjectPtr<UHorizontalBox> GraphicsRow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> GraphicsLabel;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> QuitButton;

	bool bOpen = false;
	bool bIntro = true;
};
