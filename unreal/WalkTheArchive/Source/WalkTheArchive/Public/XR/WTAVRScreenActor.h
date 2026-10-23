// Walk the Archive - a screen in the world for VR: the player controller's widgets drawn where the headset sees them.
//
// One UWidgetComponent (world space, pivot at its centre, one-sided, no collision) showing a UWTAVRRootWidget, drawn
// with M_WTA_WidgetScreen (emissive.py: unlit, translucent, display referred, after motion blur: a pass with no depth
// buffer, so it shows over everything; the laser and its dot draw after it). Its face is the component's +X side:
// PlaceFacing turns it to face the eye. The player controller stands it nearer, and smaller by as much
// (SetSizeScale), when a wall is closer than it would be, so a wall never cuts through a card and the card looks the
// same size.
// The laser finds it with Trace (a ray against its plane) rather than collision, so a screen's empty parts never stop
// the laser on its way to the world: AWTAPlayerController asks which pixel the ray is on and whether a button is
// there (IsInteractiveAt), and hands the widget interaction component a hit on the screen only when it counts.
// Pixel (0, 0) is the screen's top-left corner, as the widget sees it.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WTAVRScreenActor.generated.h"

class UUserWidget;
class UWidgetComponent;

UCLASS(NotPlaceable, Transient)
class WALKTHEARCHIVE_API AWTAVRScreenActor : public AActor
{
	GENERATED_BODY()

public:
	AWTAVRScreenActor();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA|VR")
	TObjectPtr<UWidgetComponent> Screen;

	/** Show Content, laid out at DrawSize pixels, WidthCm across in the world. */
	void Init(UUserWidget* Content, FIntPoint DrawSize, float WidthCm);

	/** Stand the screen Distance in front of Eye along Yaw, its centre Drop below the eye, turned to face the eye. */
	void PlaceFacing(const FVector& Eye, float Yaw, float Distance, float Drop);

	/** Its size as a share of the width Init gave it (a screen brought nearer is made smaller by as much). */
	void SetSizeScale(float Scale);

	/** Show or hide the screen (hidden, it draws nothing and Trace misses it). */
	void SetShown(bool bShow);

	UFUNCTION(BlueprintPure, Category = "WTA|VR")
	bool IsShown() const { return bShown; }

	/** Where the ray from Start along Direction (a unit vector) meets the screen's face within MaxDistance: the
	    distance along the ray and the pixel there. False when it misses, comes from behind, or the screen is hidden. */
	bool Trace(const FVector& Start, const FVector& Direction, float MaxDistance, float& OutDistance, FVector2D& OutPixel) const;

	/** The world point of a pixel on the screen. */
	FVector PixelToWorld(const FVector2D& Pixel) const;

	/** True when a widget the pointer can press (a button, a text box) is under Pixel. */
	bool IsInteractiveAt(const FVector2D& Pixel) const;

	/** The yaw the screen was placed along (from the eye to the screen). */
	float GetPlacedYaw() const { return PlacedYaw; }

	/** The layout size in pixels. */
	FVector2D GetDrawSize() const { return FVector2D(Size); }

	/** M_WTA_WidgetScreen, the material every VR widget draws with (the laser's label and the visit's name tags too);
	    null before the lighting step has built it (logged once). */
	static class UMaterialInterface* ScreenMaterial();

	/** Size a world-space widget component to its widget's own desired size; call it when the widget's content
	    changes. (The engine's draw-at-desired-size measures the component's whole virtual window, which came out
	    far taller than one line of text: an 86 px plate round a 28 px label.) */
	static void FitToWidget(UWidgetComponent* Component);

protected:
	FIntPoint Size = FIntPoint(1280, 800);
	float CmPerPixel = 0.0875f;
	float SizeScale = 1.f;
	float PlacedYaw = 0.f;
	bool bShown = false;
};
