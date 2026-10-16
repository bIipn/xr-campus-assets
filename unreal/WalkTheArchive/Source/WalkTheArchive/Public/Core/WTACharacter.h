// Walk the Archive - the first-person player.
//
// Feel constants are ports of the web build (nav.js / world.js): eye at 162 cm, capsule 90 x 30, walk 300 cm/s,
// sprint 560, jump 520, gravity scale 1.63, head-bob 2.6 cm with a 155 cm stride, landing dip spring.
// WalkTo uses the NavMesh through UAIBlueprintHelperLibrary::SimpleMoveToLocation (adds a path-following
// component to the player controller) and raises MaxWalkSpeed to clamp(PathLength / 2.3, 240, 1200) while it walks.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "Engine/EngineTypes.h"
#include "Data/WTATypes.h"
#include "WTACharacter.generated.h"

class UCameraComponent;

UCLASS(Blueprintable)
class WALKTHEARCHIVE_API AWTACharacter : public ACharacter
{
	GENERATED_BODY()

public:
	AWTACharacter();

	/** First-person camera, relative Z = EyeHeight - capsule half height (72 cm) plus bob/dip. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	TObjectPtr<UCameraComponent> Camera;

	// --- Feel (cm, cm/s, seconds) --------------------------------------------

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float WalkSpeed = 300.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float SprintSpeed = 560.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float EyeHeight = 162.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float BobAmplitude = 2.6f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float BobStride = 155.f;

	/** Landing dip: impulse = -fall speed * this (web 0.1), spring (110, 15). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float LandingDipScale = 0.1f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float TravelSpeedMin = 240.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float TravelSpeedMax = 1200.f;

	/** Auto-walk stops within this distance of the goal. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float AutoWalkStopRadius = 10.f;

	// --- Movement API ----------------------------------------------------------

	/** Walk to a floor point on the NavMesh (click-to-walk, tour stops, places). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void WalkTo(FVector Dest);

	/** Cancel the current auto-walk (any manual move input also cancels it). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void StopWalking();

	/** True while a WalkTo path is being followed. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsAutoWalking() const;

	/** Put the player at View.Location (eye) facing View.Yaw/Pitch, no walk. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void TeleportToView(const FWTAView& View);

	/** The current eye position and control rotation as a view (bValid true). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FWTAView GetCurrentView() const;

	/** Camera world position. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FVector GetEyeLocation() const;

	/** Shift / left thumb: switches MaxWalkSpeed between WalkSpeed and SprintSpeed. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void SetSprinting(bool bOn);

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsSprinting() const { return bSprinting; }

	/** Move input from the controller: X = right, Y = forward, relative to the control yaw. Cancels auto-walk. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void AddMoveInput(FVector2D Axis);

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void Landed(const FHitResult& Hit) override;

	/** Head-bob + landing-dip camera offset (port of playerFrame, nav.js). */
	void UpdateCameraOffset(float DeltaSeconds);

	/** Adds the XY distance moved this frame to UWTAProgressSubsystem::NoteDistance. */
	void NoteDistanceWalked();

	float BobPhase = 0.f;
	/** 0..1 bob strength, eased toward the measured ground speed (web PLAYER.amp). */
	float BobAmount = 0.f;
	float DipOffset = 0.f;
	float DipVelocity = 0.f;
	bool bSprinting = false;
	bool bAutoWalking = false;
	FVector LastFrameLocation = FVector::ZeroVector;
	bool bHasLastFrameLocation = false;
};
