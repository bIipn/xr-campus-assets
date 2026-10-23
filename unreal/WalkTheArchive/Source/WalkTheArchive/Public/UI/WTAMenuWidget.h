// Walk the Archive - the intro / pause menu (built in C++, no widget asset).
//
// Title "Walk the Archive", a subtitle line, then: Enter (or Resume when paused), Take the tour, Visit together,
// Enter VR / Leave VR (only when a headset is connected, -vrsim was given, or VR is on), a Graphics row (Low, Medium,
// High, Epic, Cinematic, Auto; the current preset is printed next to it) and Quit, over a line of the controls (the
// headset's in VR).
// Buttons go through HandleAction: "Enter" closes the menu, "Tour" closes it and starts the tour, "Visit" opens the
// Visit together card (guided visits), "VR" closes it and goes into or out of VR (AWTAPlayerController::ToggleVR),
// "Graphics" applies Index (0..4) or runs auto-detect for -1, "Quit" calls UKismetSystemLibrary::QuitGame.

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
	/** Show the menu; bInIntro = first screen (Enter + subtitle) rather than the pause menu (Resume). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Open(bool bInIntro);

	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Close();

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsOpen() const { return bOpen; }

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsIntro() const { return bIntro; }

	/** Re-read the current preset into the graphics label. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void RefreshGraphicsLabel();

	/** Show or hide Enter VR / Leave VR, and the controls line, for the VR state now. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void RefreshVR();

protected:
	virtual void NativeOnInitialized() override;

	/** Buttons: "Enter", "Tour", "Visit", "VR", "Tunnel", "Seated", "Graphics" (Index), "Quit". */
	UFUNCTION()
	void HandleAction(FName Action, FName Arg, int32 Index);

	UPROPERTY(Transient) TObjectPtr<UBorder> Scrim;
	UPROPERTY(Transient) TObjectPtr<UBorder> Card;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> TitleText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> SubtitleText;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> EnterButton;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> EnterText;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> TourButton;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> VisitButton;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> VRButton;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> VRText;
	/** In VR: the comfort tunnel and seated play (a headset) on or off. */
	UPROPERTY(Transient) TObjectPtr<UHorizontalBox> ComfortRow;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> TunnelButton;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> TunnelText;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> SeatedButton;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> SeatedText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ControlsText;
	UPROPERTY(Transient) TObjectPtr<UHorizontalBox> GraphicsRow;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> GraphicsLabel;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> QuitButton;

	bool bOpen = false;
	bool bIntro = true;
};
