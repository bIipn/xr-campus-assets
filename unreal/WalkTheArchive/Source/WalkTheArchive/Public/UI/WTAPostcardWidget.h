// Walk the Archive - the postcard frame (photo mode, built in C++, no widget asset).
//
// Press P and the view becomes a postcard: a cream mat around the picture with a brass hairline inside it and
// a caption band along the bottom - the campus and the client as a kicker, the place in the serif, the date on
// the right - and the frame is written with the view into Saved/Postcards/<place>_<time>.png (a screenshot
// with the UI on, the HUD hidden for the moment the picture is taken). AWTAPlayerController::TakePostcard runs
// it; this widget only draws the frame.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "WTAPostcardWidget.generated.h"

class UTextBlock;

UCLASS()
class WALKTHEARCHIVE_API UWTAPostcardWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** The mat's width and the caption band's height, pixels at 1080p (scaled with the viewport by UMG). */
	static constexpr float MatWidth = 28.f;
	static constexpr float BandHeight = 118.f;

	/** Build the frame once (hidden). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Build();

	/** Fill the caption and show the frame: Place in the serif, Kicker above it (the room's wing), Date on the right. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Show(const FText& Place, const FText& Kicker, const FString& Date, const FString& Client, const FString& Campus);

	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Hide();

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsShowing() const { return bShowing; }

protected:
	bool bShowing = false;

	UPROPERTY(Transient) TObjectPtr<UTextBlock> CampusText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> PlaceText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> KickerText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> DateText;
};
