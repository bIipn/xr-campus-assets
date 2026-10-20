// Walk the Archive - the animation instance a Wax Hall reenactor's body runs.

#include "World/WTAWaxAnimInstance.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimationPoseData.h"
#include "AnimationRuntime.h"

void FWTAWaxClip::Advance(float Seconds)
{
	const UAnimSequence* Sequence = Anim.Get();
	if (Sequence == nullptr)
	{
		return;
	}
	const float Length = Sequence->GetPlayLength();
	if (Length <= 0.f)
	{
		Time = 0.f;
		return;
	}
	Time += Seconds * Rate;
	if (bLoop)
	{
		Time = FMath::Fmod(Time, Length);
		if (Time < 0.f)
		{
			Time += Length;
		}
	}
	else
	{
		Time = FMath::Clamp(Time, 0.f, Length);
	}
}

void FWTAWaxAnimProxy::PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds)
{
	FAnimInstanceProxy::PreUpdate(InAnimInstance, DeltaSeconds);

	UWTAWaxAnimInstance* Instance = Cast<UWTAWaxAnimInstance>(InAnimInstance);
	if (Instance == nullptr)
	{
		return;
	}

	// A new clip: the one playing becomes the one we blend away from.
	if (Instance->PendingSerial != Serial)
	{
		Serial = Instance->PendingSerial;
		if (Current.IsValid() && Instance->PendingBlend > 0.f)
		{
			Previous = Current;
			BlendAlpha = 0.f;
			BlendPerSecond = 1.f / Instance->PendingBlend;
		}
		else
		{
			Previous = FWTAWaxClip();
			BlendAlpha = 1.f;
			BlendPerSecond = 0.f;
		}
		Current.Anim = Instance->PendingClip;
		Current.Time = Instance->PendingStart;
		Current.Rate = Instance->PendingRate;
		Current.bLoop = Instance->bPendingLoop;
	}
	bHeld = Instance->bPendingHold;

	if (bHeld)
	{
		return;
	}
	Current.Advance(DeltaSeconds);
	if (BlendAlpha < 1.f)
	{
		Previous.Advance(DeltaSeconds);
		BlendAlpha = FMath::Min(1.f, BlendAlpha + BlendPerSecond * DeltaSeconds);
		if (BlendAlpha >= 1.f)
		{
			Previous = FWTAWaxClip();
		}
	}
}

bool FWTAWaxAnimProxy::Evaluate(FPoseContext& Output)
{
	const UAnimSequence* CurrentAnim = Current.Anim.Get();
	if (CurrentAnim == nullptr)
	{
		Output.ResetToRefPose();
		return true;
	}

	FAnimationPoseData CurrentPose(Output);
	CurrentAnim->GetAnimationPose(CurrentPose, FAnimExtractContext(static_cast<double>(Current.Time), true, FDeltaTimeRecord(), Current.bLoop));

	const UAnimSequence* PreviousAnim = Previous.Anim.Get();
	if (PreviousAnim == nullptr || BlendAlpha >= 1.f)
	{
		return true;
	}

	// Still crossfading: sample the outgoing clip into a second pose and blend the two.
	FPoseContext Fading(Output);
	FAnimationPoseData FadingPose(Fading);
	PreviousAnim->GetAnimationPose(FadingPose, FAnimExtractContext(static_cast<double>(Previous.Time), true, FDeltaTimeRecord(), Previous.bLoop));

	FPoseContext Blended(Output);
	FAnimationPoseData BlendedPose(Blended);
	// Smoothstep, so a beat change has no corner at either end of the blend.
	const float Alpha = FMath::SmoothStep(0.f, 1.f, BlendAlpha);
	FAnimationRuntime::BlendTwoPosesTogether(CurrentPose, FadingPose, Alpha, BlendedPose);
	Output = Blended;
	return true;
}

void UWTAWaxAnimInstance::PlayClip(UAnimSequence* Clip, bool bLoop, float Rate, float StartTime, float BlendSeconds)
{
	if (Clip == nullptr)
	{
		return;
	}
	PendingClip = Clip;
	bPendingLoop = bLoop;
	PendingRate = Rate;
	PendingStart = FMath::Max(0.f, StartTime);
	PendingBlend = FMath::Max(0.f, BlendSeconds);
	++PendingSerial;
}

void UWTAWaxAnimInstance::Hold(bool bHold)
{
	bPendingHold = bHold;
}
