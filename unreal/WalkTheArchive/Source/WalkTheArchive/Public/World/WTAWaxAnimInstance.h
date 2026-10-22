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
 * How a hand closes on a prop: for each finger (index, middle, ring, little) and the thumb, the rotation of its
 * three joints from the knuckle out, each a rotation vector in degrees about the joint's own axes (direction =
 * the axis, length = the angle). Applied over the body's reference pose, not the clip's fingers, so a hold looks
 * the same whatever the clip does with the hand. The same values fit both hands (the MetaHuman rig mirrors the
 * joint frames). AWTAWaxStageActor keeps a table of them per prop kind.
 */
struct FWTAHandPose
{
	FVector Joint[5][3] = {};

	bool IsSet() const
	{
		for (int32 f = 0; f < 5; ++f) { for (int32 j = 0; j < 3; ++j) { if (!Joint[f][j].IsNearlyZero()) { return true; } } }
		return false;
	}
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

	/**
	 * After the clips: every bone below a wrist keeps the reference pose's length (the retargeted clips squash
	 * the hands) and the metacarpals its rotation; each gripping hand's finger joints turn from the reference
	 * pose into Pose, blended by Grip (local space).
	 */
	void ApplyGrip(FPoseContext& Output) const;
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

	/** How far closed a hand was asked to be (for QA). */
	UFUNCTION(BlueprintPure, Category = "WTA|People")
	float GetGrip(bool bRightHand) const { return PendingGrip[bRightHand ? 1 : 0]; }

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
};
