// Walk the Archive - a VR screen's content: the game's own widgets stacked as layers (built in C++, no widget asset).
//
// In VR the player controller's widgets cannot go to the viewport (the headset does not show it), so they go on two
// world-space screens instead (AWTAVRScreenActor): the card screen in front of the head (the exhibit and book cards,
// the chat, the visit card, the menu, the certificate) and the HUD screen a little further off (the HUD). Each screen
// shows one of these: an overlay that keeps its layers in their viewport z-order, every layer filling the screen. With
// SetBacking the screen has a rounded dark backing; without it, only what the layers draw shows.
//
// UWTAVRLabelWidget is the laser's label in VR: what the pointer is on ("Open: The 1985 Bookmobile"), on the HUD's
// hover-label plate (dark panel, dim brass edge, bone bold 13).

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "WTAVRRootWidget.generated.h"

class UBorder;
class UOverlay;
class UTextBlock;

UCLASS()
class WALKTHEARCHIVE_API UWTAVRRootWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Put Widget on this screen at ZOrder (the z-order it would have had in the viewport). */
	void AddLayer(UUserWidget* Widget, int32 ZOrder);

	/** True when any layer is showing (not collapsed or hidden). */
	bool HasVisibleLayer() const;

	/** A rounded dark backing under the layers. */
	void SetBacking(bool bOn);

protected:
	virtual void NativeOnInitialized() override;

	UPROPERTY(Transient)
	TObjectPtr<UOverlay> Layers;

	UPROPERTY(Transient)
	TObjectPtr<UBorder> Backing;

	/** Each layer's z-order, by widget, to insert new ones in order. */
	TMap<TWeakObjectPtr<UUserWidget>, int32> Order;
};

UCLASS()
class WALKTHEARCHIVE_API UWTAVRLabelWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** The label's text; empty hides the plate. */
	void SetLabel(const FText& Text);

	/** The text shown now. */
	const FText& GetLabel() const { return Shown; }

protected:
	virtual void NativeOnInitialized() override;

	UPROPERTY(Transient)
	TObjectPtr<UBorder> Plate;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> LabelText;

	FText Shown;
};
