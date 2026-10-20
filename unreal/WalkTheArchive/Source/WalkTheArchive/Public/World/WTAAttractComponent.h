// Walk the Archive - the thing that makes an exhibit call you over.
//
// Every pick actor gets one. It owns a picture light aimed at its own art from the side the player views it from,
// and raises that light as the player walks toward it: dark and quiet across the room, warm and bright when you
// are close enough to read the label. While an exhibit is still unseen the light also breathes - a slow swell of
// about a fifth of its brightness - which is what actually catches the eye across a gallery. Once the card has
// been opened the breathing stops and the light settles lower, so what is left glowing is what you have not read.
//
// The light never casts shadows and switches off entirely below a threshold, so a room full of these costs little.
// Everything is driven from Attention (0..1), which other code can read if it wants to move with the same curve.

#pragma once

#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "WTAAttractComponent.generated.h"

class USpotLightComponent;

UCLASS(ClassGroup = (WTA), meta = (BlueprintSpawnableComponent))
class WALKTHEARCHIVE_API UWTAAttractComponent : public USceneComponent
{
	GENERATED_BODY()

public:
	UWTAAttractComponent();

	/** Closer than this and the exhibit is at full attention (cm). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Attract")
	float NearDistance = 900.f;

	/** Further than this and it is asleep (cm). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Attract")
	float FarDistance = 2800.f;

	/** Candelas at rest and at full attention. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Attract")
	float RestIntensity = 420.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Attract")
	float PeakIntensity = 2600.f;

	/** What the light settles to once this exhibit has been opened (fraction of Peak). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Attract")
	float SeenScale = 0.45f;

	/** One breath, in seconds, while the exhibit is unseen. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Attract")
	float BreathSeconds = 3.6f;

	/** How much of the brightness the breath swings (0..1). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Attract")
	float BreathDepth = 0.22f;

	/** Seconds for the light to catch up with the player: slow enough that it swells rather than snaps. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Attract")
	float Smoothing = 0.55f;

	/** Where the light hangs relative to the art: out toward the viewer, and up. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Attract")
	float LightOut = 150.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Attract")
	float LightUp = 210.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Attract")
	FLinearColor LightColor = FLinearColor(1.f, 0.86f, 0.68f);

	/** Switch the whole thing off (the play test turns it off to measure anything else). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Attract")
	bool bEnabled = true;

	/** 0 when the player is away, 1 when they are on top of it. Smoothed. */
	UFUNCTION(BlueprintPure, Category = "WTA|Attract")
	float GetAttention() const { return Attention; }

	/** The light's current brightness in candelas (0 when it is switched off). */
	UFUNCTION(BlueprintPure, Category = "WTA|Attract")
	float GetIntensity() const;

	/** Aim the light from the side the player views this from. Called once the owner knows its view spot. */
	UFUNCTION(BlueprintCallable, Category = "WTA|Attract")
	void AimFrom(const FVector& ViewerLocation);

	/** One line for the logs and the play test: "attention 0.62 intensity 1840 seen 0". */
	FString Describe() const;

protected:
	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** The picture light. Never casts shadows: a gallery of these would be unaffordable if it did. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA|Attract")
	TObjectPtr<USpotLightComponent> Spot;

	/** Smoothed 0..1 nearness. */
	UPROPERTY(BlueprintReadOnly, Category = "WTA|Attract")
	float Attention = 0.f;

	/** Seconds since BeginPlay, offset per actor so a wall of exhibits does not breathe in lockstep. */
	float Phase = 0.f;
};
