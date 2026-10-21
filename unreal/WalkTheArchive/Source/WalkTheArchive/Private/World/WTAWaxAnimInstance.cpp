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
	for (int32 Hand = 0; Hand < 2; ++Hand)
	{
		GripTarget[Hand] = FMath::Clamp(Instance->PendingGrip[Hand], 0.f, 1.f);
		if (GripTarget[Hand] > KINDA_SMALL_NUMBER)
		{
			FingerDeg[Hand] = Instance->PendingFingerDeg[Hand];
			ThumbDeg[Hand] = Instance->PendingThumbDeg[Hand];
		}
		// a hand closes or opens in about a quarter second
		Grip[Hand] = FMath::FInterpConstantTo(Grip[Hand], GripTarget[Hand], 1.f, 4.f * DeltaSeconds);
	}

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
		ApplyGrip(Output);
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
	ApplyGrip(Output);
	return true;
}

void FWTAWaxAnimProxy::ApplyGrip(FPoseContext& Output) const
{
	if (Grip[0] <= KINDA_SMALL_NUMBER && Grip[1] <= KINDA_SMALL_NUMBER)
	{
		return;
	}
	// The MetaHuman body's finger joints, and the axis each bends about in its own frame (measured from the
	// reference pose with C:\dev\wta_tools\probe_hands.py: the cross product of the finger's direction and the
	// palm's normal, expressed in the joint). The same on both hands.
	static const FVector FingerAxis[3] = { FVector(0.10f, 0.20f, -0.97f).GetSafeNormal(), FVector(0.25f, 0.37f, -0.89f).GetSafeNormal(), FVector(0.f, 0.f, -1.f) };
	static const FVector ThumbAxis[3] = { FVector(-0.014f, 0.906f, -0.423f).GetSafeNormal(), FVector(0.147f, 0.975f, -0.165f).GetSafeNormal(), FVector(0.f, 0.989f, -0.149f).GetSafeNormal() };
	static const TCHAR* Fingers[4] = { TEXT("index"), TEXT("middle"), TEXT("ring"), TEXT("pinky") };
	static const TCHAR* Sides[2] = { TEXT("l"), TEXT("r") };
	// bone names, built once: [hand][finger 0..3 = fingers, 4 = thumb][joint]
	static FName Names[2][5][3];
	static bool bNamed = false;
	if (!bNamed)
	{
		for (int32 Hand = 0; Hand < 2; ++Hand)
		{
			for (int32 Finger = 0; Finger < 5; ++Finger)
			{
				for (int32 Joint = 0; Joint < 3; ++Joint)
				{
					Names[Hand][Finger][Joint] = FName(*FString::Printf(TEXT("%s_%02d_%s"), Finger < 4 ? Fingers[Finger] : TEXT("thumb"), Joint + 1, Sides[Hand]));
				}
			}
		}
		bNamed = true;
	}

	const FBoneContainer& Bones = Output.Pose.GetBoneContainer();
	for (int32 Hand = 0; Hand < 2; ++Hand)
	{
		if (Grip[Hand] <= KINDA_SMALL_NUMBER)
		{
			continue;
		}
		for (int32 Finger = 0; Finger < 5; ++Finger)
		{
			const FVector& Deg = Finger < 4 ? FingerDeg[Hand] : ThumbDeg[Hand];
			for (int32 Joint = 0; Joint < 3; ++Joint)
			{
				const int32 MeshIndex = Bones.GetPoseBoneIndexForBoneName(Names[Hand][Finger][Joint]);
				if (MeshIndex == INDEX_NONE)
				{
					continue;
				}
				const FCompactPoseBoneIndex Index = Bones.MakeCompactPoseIndex(FMeshPoseBoneIndex(MeshIndex));
				if (Index.GetInt() == INDEX_NONE)
				{
					continue;                 // this LOD has no such bone
				}
				const FVector& Axis = Finger < 4 ? FingerAxis[Joint] : ThumbAxis[Joint];
				const float Degrees = Deg[Joint] * Grip[Hand];
				if (FMath::Abs(Degrees) < KINDA_SMALL_NUMBER)
				{
					continue;
				}
				FTransform& Bone = Output.Pose[Index];
				Bone.SetRotation(Bone.GetRotation() * FQuat(Axis, FMath::DegreesToRadians(Degrees)));
			}
		}
	}
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

void UWTAWaxAnimInstance::SetGrip(bool bRightHand, float Amount, FVector InFingerDeg, FVector InThumbDeg)
{
	const int32 Hand = bRightHand ? 1 : 0;
	PendingGrip[Hand] = FMath::Clamp(Amount, 0.f, 1.f);
	if (PendingGrip[Hand] > KINDA_SMALL_NUMBER)
	{
		PendingFingerDeg[Hand] = InFingerDeg;
		PendingThumbDeg[Hand] = InThumbDeg;
	}
}
