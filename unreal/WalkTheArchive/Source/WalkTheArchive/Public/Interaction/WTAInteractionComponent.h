// Walk the Archive - hover trace and interact dispatch (lives on the player controller).
//
// Every tick: one line trace on ECC_Visibility up to MaxDistance from the camera through the screen centre, or
// from the mouse cursor when bUseMouseCursor is set (Tab / panel open). The first blocking actor that implements
// IWTAInteractable becomes Hovered and OnHoverChanged broadcasts its label (empty text when nothing is hovered).
// TryInteract() runs Execute_Interact on the hovered actor; LastHit keeps the full hit so the controller can walk
// to a clicked floor point when the cursor is free.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Engine/EngineTypes.h"
#include "UObject/WeakObjectPtrTemplates.h"
#include "WTAInteractionComponent.generated.h"

/** Hover label changed (empty when the crosshair leaves an interactable). */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FWTAHoverChanged, const FText&, Label);

/** An interactable was activated. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FWTAInteracted, AActor*, Actor);

UCLASS(ClassGroup = (WTA), meta = (BlueprintSpawnableComponent))
class WALKTHEARCHIVE_API UWTAInteractionComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UWTAInteractionComponent();

	/** Trace length in cm (web: 15 m). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	float MaxDistance = 1500.f;

	/** Trace from the mouse cursor instead of the screen centre. The controller sets this with the cursor state. */
	UPROPERTY(BlueprintReadWrite, Category = "WTA")
	bool bUseMouseCursor = false;

	/** Label of the hovered interactable, or empty. */
	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FText HoverLabel;

	/** The hovered interactable actor (weak: actors can be destroyed under the crosshair). */
	TWeakObjectPtr<AActor> Hovered;

	UPROPERTY(BlueprintAssignable, Category = "WTA")
	FWTAHoverChanged OnHoverChanged;

	UPROPERTY(BlueprintAssignable, Category = "WTA")
	FWTAInteracted OnInteracted;

	/** Run the trace now (TickComponent does this every frame). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void UpdateHover();

	/** Interact with the hovered actor. Returns false when nothing interactable is hovered. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	bool TryInteract();

	/** The hovered actor or null. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	AActor* GetHovered() const;

	/** True when an interactable is under the crosshair / cursor. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	bool HasHover() const;

	/** The last trace result, interactable or not (floor clicks use this). */
	const FHitResult& GetLastHit() const { return LastHit; }

	/** Blueprint-friendly view of the last blocking hit. Returns false when the last trace hit nothing. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	bool GetLastHitLocation(FVector& OutLocation, FVector& OutNormal) const;

protected:
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** Start point and direction for the trace (camera + screen centre, or deprojected mouse). False if no viewport. */
	bool ComputeTraceRay(FVector& OutStart, FVector& OutDirection) const;

	/** Update Hovered/HoverLabel and broadcast when the actor changed. */
	void SetHovered(AActor* NewActor);

	FHitResult LastHit;
};
