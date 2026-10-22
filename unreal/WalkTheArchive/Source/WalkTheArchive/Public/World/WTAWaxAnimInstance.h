// Walk the Archive - the animation instance a Wax Hall reenactor's body runs.
//
// A reenactor plays one motion capture clip at a time and crossfades to the next on its own beat (see
// AWTAWaxStageActor and Pipeline/content/wax_acting.json). That is all this needs to do, so rather than an
// Animation Blueprint it is a native UAnimInstance: it samples the outgoing clip and the incoming one and blends
// the two poses. Nothing to author in the editor, nothing to keep in step with the MetaHuman rig - the face,
// clothes and grooms follow the body exactly as they do when the body plays a single animation.

#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "Animation/AnimInstanceProxy.h"
#include "WTAWaxAnimInstance.generated.h"

class UAnimSequence;

/**
 * The shape of what a hand holds, in the hand's palm frame (+X along the fingers, +Y out of the palm, +Z across;
 * cm): a box (Frame = its centre and axes, Half = its half extents) or a tube along Frame's Z axis of Radius.
 * The fingers close on it until their flesh touches it (contact IK).
 */
struct FWTAHoldShape
{
	enum EKind : uint8 { None, Box, Tube };
	EKind Kind = None;
	FTransform Frame = FTransform::Identity;
	FVector Half = FVector::ZeroVector;
	float Radius = 0.f;

	/** Signed distance from a point in the palm frame to the shape's surface (negative inside). */
	float Distance(const FVector& PalmPoint) const;
};

/**
 * How a hand closes on a prop: for each finger (index, middle, ring, little) and the thumb, the rotation of its
 * three joints from the knuckle out, each a rotation vector in degrees about the joint's own axes (direction =
 * the axis, length = the angle). Applied over the body's reference pose, not the clip's fingers, so a hold looks
 * the same whatever the clip does with the hand. The same values fit both hands (the MetaHuman rig mirrors the
 * joint frames). AWTAWaxStageActor keeps a table of them per prop kind.
 *
 * With bContact and a Shape, the four fingers' vectors and the thumb's second and third are not used as given:
 * each joint, from the knuckle out, curls about its hinge from open until the flesh beyond it meets the shape,
 * so the hand fits the object whatever its size and whatever body it is (the thumb's first joint keeps its
 * designed vector, which swings the thumb over the prop).
 */
struct FWTAHandPose
{
	FVector Joint[5][3] = {};
	FWTAHoldShape Shape;
	bool bContact = false;

	bool IsSet() const
	{
		for (int32 f = 0; f < 5; ++f) { for (int32 j = 0; j < 3; ++j) { if (!Joint[f][j].IsNearlyZero()) { return true; } } }
		return bContact;
	}
};

/**
 * Where a hand should be: the hand bone's transform in the body's component space, and where the elbow should
 * point (the two-bone IK's joint target). Weight 0 leaves the arm to the clip.
 */
struct FWTAHandTarget
{
	FTransform Hand = FTransform::Identity;
	FVector Elbow = FVector::ZeroVector;
	float Weight = 0.f;
};

/** One clip being sampled: the sequence, where in it we are, how fast, and whether it wraps. */
struct FWTAWaxClip
{
	TWeakObjectPtr<UAnimSequence> Anim;
	float Time = 0.f;
	float Rate = 1.f;
	bool bLoop = true;

	bool IsValid() const { return Anim.IsValid(); }
	/** Advances Time by Seconds, wrapping (bLoop) or stopping at the last frame. */
	void Advance(float Seconds);
};

/**
 * Samples up to two clips and blends them. Everything is advanced in PreUpdate, on the game thread, so Evaluate
 * only reads: no copying between threads, and a frozen figure (Hold) costs one pose evaluation and then nothing.
 */
USTRUCT()
struct FWTAWaxAnimProxy : public FAnimInstanceProxy
{
	GENERATED_BODY()

	FWTAWaxAnimProxy() = default;
	explicit FWTAWaxAnimProxy(UAnimInstance* InAnimInstance) : FAnimInstanceProxy(InAnimInstance) {}

	virtual void PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds) override;
	virtual bool Evaluate(FPoseContext& Output) override;

	/** The clip playing now, and the one it is still blending away from. */
	FWTAWaxClip Current;
	FWTAWaxClip Previous;
	/** 1 = all Current. Climbs by BlendPerSecond while below 1. */
	float BlendAlpha = 1.f;
	float BlendPerSecond = 0.f;
	/** Set by Hold(): time stops, the pose stays where it is. */
	bool bHeld = false;
	/** Bumped by PlayClip; the proxy picks the change up in PreUpdate. */
	uint32 Serial = 0;

	/**
	 * A grip closes a hand's fingers round a prop on top of whatever the clip does with the arm: [0] the left
	 * hand, [1] the right. Pose is the hand's finger pose at a full grip, Grip how far toward it the hand is
	 * (0 = the clip's own fingers), eased so a hand-over closes and opens over a few frames.
	 */
	float Grip[2] = { 0.f, 0.f };
	float GripTarget[2] = { 0.f, 0.f };
	FWTAHandPose Pose[2];
	/** Where each hand is asked to be (component space) and how far the arm is given to it, eased like Grip. */
	FWTAHandTarget HandTarget[2];
	float IKWeight[2] = { 0.f, 0.f };
	/** What the head turns to look at (component space), and how far it is given to that, eased. */
	FVector LookTarget = FVector::ZeroVector;
	float LookWeight = 0.f;
	float LookWeightTarget = 0.f;

	/**
	 * After the clips: every bone below a wrist keeps the reference pose's length (the retargeted clips squash
	 * the hands) and the metacarpals its rotation; each gripping hand's finger joints turn from the reference
	 * pose into Pose, blended by Grip (local space); a pose with a shape closes the fingers on it (SolveContact).
	 */
	void ApplyGrip(FPoseContext& Output) const;
	/** Fills a hand pose's finger vectors by curling each joint from open until the flesh beyond it meets the shape. */
	void SolveContact(const FBoneContainer& Bones, int32 Hand, FWTAHandPose& InOut) const;
	/** Two-bone IK on each arm with a weighted hand target: upper arm and forearm turn so the hand lands on it, and takes its rotation. */
	void ApplyArmIK(FPoseContext& Output) const;
	/** Turns the neck and head toward LookTarget, by LookWeight (yaw and pitch limited to what a neck does). */
	void ApplyLookAt(FPoseContext& Output) const;
};

UCLASS()
class WALKTHEARCHIVE_API UWTAWaxAnimInstance : public UAnimInstance
{
	GENERATED_BODY()

public:
	/**
	 * Crossfades to Clip over BlendSeconds (0 = cut). StartTime is seconds into the clip; Rate scales playback.
	 * Call it on the game thread; the pose changes from the next evaluation.
	 */
	UFUNCTION(BlueprintCallable, Category = "WTA|People")
	void PlayClip(UAnimSequence* Clip, bool bLoop = true, float Rate = 1.f, float StartTime = 0.f, float BlendSeconds = 0.35f);

	/** Stops advancing time: the figure holds the pose it is in (a wax figure again). */
	UFUNCTION(BlueprintCallable, Category = "WTA|People")
	void Hold(bool bHold);

	/**
	 * Closes one hand round a prop: Pose is the finger pose at a full grip, Amount 0..1 how far toward it. Amount
	 * 0 gives the hand back to the clip. The proxy eases toward it over about a quarter second.
	 */
	void SetGrip(bool bRightHand, float Amount, const FWTAHandPose& Pose);

	/**
	 * Asks one arm to put its hand at HandCS (the hand bone's transform in the body's component space), the
	 * elbow pointing toward ElbowCS, with Weight 0..1 (0 = the clip's arm). Eased like the grip.
	 */
	void SetHandTarget(bool bRightHand, float Weight, const FTransform& HandCS, const FVector& ElbowCS);

	/** Asks the head to look at TargetCS (component space) with Weight 0..1. Eased. */
	void SetLookAt(float Weight, const FVector& TargetCS);

	/** How far closed a hand was asked to be (for QA). */
	UFUNCTION(BlueprintPure, Category = "WTA|People")
	float GetGrip(bool bRightHand) const { return PendingGrip[bRightHand ? 1 : 0]; }

	/** How far closed a hand is right now, after the easing (the stage blends a prop between the clip's hand and the held one by it). */
	UFUNCTION(BlueprintPure, Category = "WTA|People")
	float GetEasedGrip(bool bRightHand) const { return EasedGrip[bRightHand ? 1 : 0]; }

	/** How far an arm is given to its hand target right now, after the easing. */
	UFUNCTION(BlueprintPure, Category = "WTA|People")
	float GetEasedIK(bool bRightHand) const { return EasedIK[bRightHand ? 1 : 0]; }

	/** What a hand was last asked for (component space; Weight 0 = nothing), for QA. */
	const FWTAHandTarget& GetHandTarget(bool bRightHand) const { return PendingHand[bRightHand ? 1 : 0]; }

	/** How far the head was asked to look at its target, and where that is (component space), for QA. */
	float GetLookWeight() const { return PendingLookWeight; }
	const FVector& GetLookTarget() const { return PendingLook; }

	/** How far the head is given to its look target right now, after the easing. */
	UFUNCTION(BlueprintPure, Category = "WTA|People")
	float GetEasedLook() const { return EasedLook; }

	/** The clip playing now (null before the first PlayClip). */
	UFUNCTION(BlueprintPure, Category = "WTA|People")
	UAnimSequence* GetClip() const { return PendingClip.Get(); }

	/** Seconds into the current clip, for QA. */
	UFUNCTION(BlueprintPure, Category = "WTA|People")
	float GetClipTime() const { return Proxy.Current.Time; }

	/** True while two clips are still blending. */
	UFUNCTION(BlueprintPure, Category = "WTA|People")
	bool IsBlending() const { return Proxy.BlendAlpha < 1.f; }

protected:
	virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override { return &Proxy; }
	virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy) override {}

	friend struct FWTAWaxAnimProxy;

	UPROPERTY(Transient)
	FWTAWaxAnimProxy Proxy;

	/** What PlayClip asked for; the proxy reads it in PreUpdate when PendingSerial changes. */
	UPROPERTY(Transient)
	TWeakObjectPtr<UAnimSequence> PendingClip;
	float PendingRate = 1.f;
	float PendingStart = 0.f;
	float PendingBlend = 0.35f;
	bool bPendingLoop = true;
	bool bPendingHold = false;
	uint32 PendingSerial = 0;
	float PendingGrip[2] = { 0.f, 0.f };
	FWTAHandPose PendingPose[2];
	FWTAHandTarget PendingHand[2];
	float PendingLookWeight = 0.f;
	FVector PendingLook = FVector::ZeroVector;
	/** The proxy's eased values, copied back on the game thread each PreUpdate. */
	float EasedGrip[2] = { 0.f, 0.f };
	float EasedIK[2] = { 0.f, 0.f };
	float EasedLook = 0.f;
};
