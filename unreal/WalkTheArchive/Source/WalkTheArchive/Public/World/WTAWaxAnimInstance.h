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
};
