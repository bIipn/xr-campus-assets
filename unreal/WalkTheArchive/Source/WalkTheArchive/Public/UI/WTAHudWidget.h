// Walk the Archive - the always-on HUD (built in C++ in NativeOnInitialized, no widget asset).
//
// Layout (a UCanvasPanel root): room label top-left (kicker / name / sub on a translucent plate), badge counter
// top-right, crosshair dot at the centre with the hover label just under it, caption line lower-centre (wax
// scenes), toast line above the caption, hint line bottom-left, tour bar bottom-centre (step, title, date, body,
// Back / Next / End and the stop's Open button). Toasts queue; each shows for its seconds then the next one.
// The tour bar's buttons call UWTATourSubsystem (Back/Next/End) and OpenCurrent (Open).

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "WTAHudWidget.generated.h"

class UBorder;
class UCanvasPanel;
class UTextBlock;
class UWTAActionButton;

/** One queued toast. */
struct FWTAToastEntry
{
	FText Text;
	float Seconds = 0.f;
};

UCLASS()
class WALKTHEARCHIVE_API UWTAHudWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Room label: kicker ("Room 102"), name ("Science Lab"), sub ("Sieve test - Titration - Pendulum"). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void SetRoom(const FText& Kicker, const FText& Name, const FText& Sub);

	/** Label under the crosshair; empty hides it. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void SetHoverLabel(const FText& Label);

	/** Queue a toast for Seconds. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowToast(const FText& Text, float Seconds);

	/** Caption line (wax scenes); empty hides it. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowCaption(const FText& Text);

	/** Hint line for Seconds (room tips). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowHint(const FText& Text, float Seconds);

	UFUNCTION(BlueprintCallable, Category = "WTA")
	void HideHint();

	/** Fill and show the tour bar. Index is 0-based; the bar prints "Stop Index+1 of Total". OpenLabel empty hides Open. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowTour(int32 Index, int32 Total, const FText& Title, const FText& DateLabel, const FText& Body, const FText& OpenLabel);

	UFUNCTION(BlueprintCallable, Category = "WTA")
	void HideTour();

	/** Collapse/restore the bar without losing its content (while a panel is open). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void SetTourVisible(bool bVisible);

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsTourShowing() const { return bTourShowing; }

	/** "3 / 15" badge counter. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void SetBadgeCount(int32 Count, int32 Total);

	/** Hide the crosshair while the cursor is free or a panel is open. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void SetCrosshairVisible(bool bVisible);

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	/** Tour bar buttons (Action "TourBack", "TourNext", "TourEnd", "TourOpen"). */
	UFUNCTION()
	void HandleAction(FName Action, FName Arg, int32 Index);

	/** Pop the next toast when the current one expires. */
	void AdvanceToasts(float DeltaSeconds);

	UPROPERTY(Transient) TObjectPtr<UCanvasPanel> Canvas;
	UPROPERTY(Transient) TObjectPtr<UBorder> RoomPlate;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> RoomKickerText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> RoomNameText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> RoomSubText;
	UPROPERTY(Transient) TObjectPtr<UBorder> CrosshairDot;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> HoverLabelText;
	UPROPERTY(Transient) TObjectPtr<UBorder> ToastPlate;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> ToastText;
	UPROPERTY(Transient) TObjectPtr<UBorder> CaptionPlate;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> CaptionText;
	UPROPERTY(Transient) TObjectPtr<UBorder> HintPlate;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> HintText;
	UPROPERTY(Transient) TObjectPtr<UBorder> BadgePlate;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> BadgeText;
	UPROPERTY(Transient) TObjectPtr<UBorder> TourPlate;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> TourStepText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> TourTitleText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> TourDateText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> TourBodyText;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> TourBackButton;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> TourNextButton;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> TourNextText;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> TourEndButton;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> TourOpenButton;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> TourOpenText;

	TArray<FWTAToastEntry> ToastQueue;
	float ToastTimeLeft = 0.f;
	float HintTimeLeft = 0.f;
	bool bTourShowing = false;
};
