// Walk the Archive - the body in VR: the head on a floor-level origin, the two hands, the laser and its pointer.
//
// AWTACharacter makes one when the player controller goes into VR (StartVR) and drops it when it leaves (StopVR); it
// lives only on the machine whose player it is.
//   With a headset: Origin, a scene component on the floor under the capsule, carries the camera (locked to the
//   headset, no pawn control rotation) and both motion controllers (LeftGrip; RightAim, the pointing pose). Each frame
//   the capsule steps under the head (swept, so a wall holds the body back) and the origin steps back as far, so the
//   head stays where the visitor put it; the controller's control rotation follows the head, which is what the rest
//   of the game reads as where the player looks. Turning (SnapTurn) and arriving somewhere (StandHeadAt) turn the
//   body about the head. Sitting (SetSeated) lowers the origin so the eyes are at the seat's height whatever the
//   visitor's own height.
//   In the desktop simulation (-vrsim): the camera stays as it is (the mouse looks) and the hands ride low in front of
//   it, the right one aiming at what the middle of the view is on (SetSimAimTarget).
// The right hand's laser: a 3.5 mm beam from the wand's tip along the hand's aim (attached to the hand, so it moves
// with it), a dot where it lands and a label over the dot naming what is there; brass when it is on something to open
// or press, a dim bone otherwise. AWTAPlayerController::UpdateVRPointer drives it every frame (SetLaser, SetLabel) and
// hands the screens' pointer (a UWidgetInteractionComponent in Custom mode, GetPointer) its hit.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "WTAVRRig.generated.h"

class AWTACharacter;
class UMaterialInstanceDynamic;
class UMaterialInterface;
class USceneComponent;
class UStaticMesh;
class UStaticMeshComponent;
class UWidgetComponent;
class UWidgetInteractionComponent;

UCLASS(ClassGroup = (WTA))
class WALKTHEARCHIVE_API UWTAVRRig : public UActorComponent
{
	GENERATED_BODY()

public:
	UWTAVRRig();

	/** Set the rig up on the owning character: bHeadset = a real headset, else the desktop simulation. */
	void Start(bool bInHeadset);

	/** Take it all down and give the character its desktop camera back. */
	void Stop();

	UFUNCTION(BlueprintPure, Category = "WTA|VR")
	bool IsHeadset() const { return bHeadset; }

	/** The laser's ray: from the right wand's tip along the hand's aim. */
	void GetAimRay(FVector& OutStart, FVector& OutDirection) const;

	/** The simulation: aim the right hand at Target (what the middle of the view is on). */
	void SetSimAimTarget(const FVector& Target);

	/** Draw the laser to End: bHit = it lands on something (the dot shows), bActive = on something to open or press. */
	void SetLaser(const FVector& End, bool bHit, bool bActive);

	/** The label over the laser's dot; empty hides it. */
	void SetLabel(const FText& Text);

	/** The label's text now (empty when hidden). */
	FText GetLabel() const;

	/** The label's widget component (its draw size, for the play test). */
	UWidgetComponent* GetLabelComponent() const { return Label; }

	/** Hide the hands and the laser for a moment (a postcard is being taken). */
	void SetVisualsHidden(bool bHidden);

	/** The pointer for the VR screens (Custom hit testing). */
	UWidgetInteractionComponent* GetPointer() const { return Pointer; }

	/** Turn the body by Degrees about the head (the simulation turns the view). */
	void SnapTurn(float Degrees);

	/** Put the head over Floor (its own height above the floor kept), facing Yaw. */
	void StandHeadAt(const FVector& Floor, float Yaw);

	/** Turn the body about the head so the head faces Yaw. */
	void FaceYaw(float Yaw);

	/** The eye (the camera) and the way it faces. */
	FVector GetEyeLocation() const;
	float GetHeadYaw() const;
	FRotator GetHeadRotation() const;

	/** Sat down with the eyes to be at EyeZ (world), or stood up again (the origin back on the floor). */
	void SetSeated(bool bSeated, float EyeZ);

	/** The right hand (null before Start). */
	USceneComponent* GetRightHand() const { return RightHand; }

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

protected:
	AWTACharacter* Body() const;

	/** A name for a part made now, unique on the character. */
	FName UniqueName(const TCHAR* Base, const UClass* Class) const;

	/** One hand's wand: a dark handle and a brass ring at its front, along the hand's +X. */
	void MakeWand(USceneComponent* Hand, TObjectPtr<UStaticMeshComponent>& OutHandle, TObjectPtr<UStaticMeshComponent>& OutRing);

	UStaticMeshComponent* MakePart(const TCHAR* Name, UStaticMesh* Mesh, USceneComponent* Parent, UMaterialInterface* Look);

	/** The origin's height under the capsule centre when standing: on the floor the capsule stands on. */
	float StandingOriginZ() const;

	UPROPERTY(Transient) TObjectPtr<USceneComponent> Origin;
	UPROPERTY(Transient) TObjectPtr<USceneComponent> LeftHand;
	UPROPERTY(Transient) TObjectPtr<USceneComponent> RightHand;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> LeftHandle;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> LeftRing;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> RightHandle;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> RightRing;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Beam;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Dot;
	UPROPERTY(Transient) TObjectPtr<UWidgetComponent> Label;
	UPROPERTY(Transient) TObjectPtr<UWidgetInteractionComponent> Pointer;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> BeamLook;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> HandleLook;
	UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> RingLook;

	bool bStarted = false;
	bool bHeadset = false;
	bool bSeatedNow = false;
	bool bVisualsHidden = false;
	bool bLaserHit = false;
	bool bLabelShown = false;
	/** The label's draw size matches its text (AWTAVRScreenActor::FitToWidget, retried until it takes). */
	bool bLabelFitted = false;
	int32 LaserActive = -1;
	FVector LaserEnd = FVector::ZeroVector;
};
