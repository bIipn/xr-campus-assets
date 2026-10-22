// Walk the Archive - the animation instance a Wax Hall reenactor's body runs.

#include "World/WTAWaxAnimInstance.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimationPoseData.h"
#include "AnimationRuntime.h"
#include "BonePose.h"
#include "TwoBoneIK.h"

float FWTAHoldShape::Distance(const FVector& PalmPoint) const
{
	const FVector P = Frame.InverseTransformPosition(PalmPoint);
	switch (Kind)
	{
	case Box:
	{
		const FVector Q(FMath::Abs(P.X) - Half.X, FMath::Abs(P.Y) - Half.Y, FMath::Abs(P.Z) - Half.Z);
		const FVector Outside(FMath::Max(Q.X, 0.0), FMath::Max(Q.Y, 0.0), FMath::Max(Q.Z, 0.0));
		return static_cast<float>(Outside.Size() + FMath::Min(FMath::Max(Q.X, FMath::Max(Q.Y, Q.Z)), 0.0));
	}
	case Tube:
		return static_cast<float>(FMath::Sqrt(P.X * P.X + P.Y * P.Y)) - Radius;
	default:
		return 1.e6f;
	}
}

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
			Pose[Hand] = Instance->PendingPose[Hand];
		}
		// a hand closes or opens in about a quarter second; an arm goes to its target over the same time
		Grip[Hand] = FMath::FInterpConstantTo(Grip[Hand], GripTarget[Hand], 1.f, 4.f * DeltaSeconds);
		const float WantIK = FMath::Clamp(Instance->PendingHand[Hand].Weight, 0.f, 1.f);
		if (WantIK > KINDA_SMALL_NUMBER)
		{
			HandTarget[Hand] = Instance->PendingHand[Hand];
		}
		IKWeight[Hand] = FMath::FInterpConstantTo(IKWeight[Hand], WantIK, 1.f, 4.f * DeltaSeconds);
		Instance->EasedGrip[Hand] = Grip[Hand];
		Instance->EasedIK[Hand] = IKWeight[Hand];
	}
	LookWeightTarget = FMath::Clamp(Instance->PendingLookWeight, 0.f, 1.f);
	if (LookWeightTarget > KINDA_SMALL_NUMBER)
	{
		LookTarget = Instance->PendingLook;
	}
	LookWeight = FMath::FInterpConstantTo(LookWeight, LookWeightTarget, 1.f, 2.f * DeltaSeconds);
	Instance->EasedLook = LookWeight;

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
		ApplyArmIK(Output);
		ApplyLookAt(Output);
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
	ApplyArmIK(Output);
	ApplyLookAt(Output);
	return true;
}

void FWTAWaxAnimProxy::ApplyGrip(FPoseContext& Output) const
{
	// The MetaHuman body's finger joints: [hand][finger 0..3 = index, middle, ring, little; 4 = thumb][joint],
	// named once.
	static const TCHAR* Fingers[5] = { TEXT("index"), TEXT("middle"), TEXT("ring"), TEXT("pinky"), TEXT("thumb") };
	static const TCHAR* Sides[2] = { TEXT("l"), TEXT("r") };
	static FName Names[2][5][3];
	static FName Hands[2];
	static bool bNamed = false;
	if (!bNamed)
	{
		for (int32 Hand = 0; Hand < 2; ++Hand)
		{
			Hands[Hand] = FName(*FString::Printf(TEXT("hand_%s"), Sides[Hand]));
			for (int32 Finger = 0; Finger < 5; ++Finger)
			{
				for (int32 Joint = 0; Joint < 3; ++Joint)
				{
					Names[Hand][Finger][Joint] = FName(*FString::Printf(TEXT("%s_%02d_%s"), Fingers[Finger], Joint + 1, Sides[Hand]));
				}
			}
		}
		bNamed = true;
	}

	const FBoneContainer& Bones = Output.Pose.GetBoneContainer();
	FCompactPoseBoneIndex HandIndex[2] = { FCompactPoseBoneIndex(INDEX_NONE), FCompactPoseBoneIndex(INDEX_NONE) };
	for (int32 Hand = 0; Hand < 2; ++Hand)
	{
		const int32 MeshIndex = Bones.GetPoseBoneIndexForBoneName(Hands[Hand]);
		if (MeshIndex != INDEX_NONE)
		{
			HandIndex[Hand] = Bones.MakeCompactPoseIndex(FMeshPoseBoneIndex(MeshIndex));
		}
	}

	// The clips came through a retarget that squashes the hands (a metacarpal can land 3 cm from the wrist
	// instead of 9), so every bone below a wrist keeps the reference pose's length and scale, and the
	// metacarpals its rotation too: the hand keeps its shape whatever the clip does. The finger joints' own
	// rotations are the clip's unless a grip says otherwise, below.
	const int32 Num = Output.Pose.GetNumBones();
	for (int32 i = 0; i < Num; ++i)
	{
		const FCompactPoseBoneIndex Index(i);
		int32 Hand = INDEX_NONE;
		for (FCompactPoseBoneIndex Up = Bones.GetParentBoneIndex(Index); Up.GetInt() != INDEX_NONE; Up = Bones.GetParentBoneIndex(Up))
		{
			if (Up == HandIndex[0]) { Hand = 0; break; }
			if (Up == HandIndex[1]) { Hand = 1; break; }
		}
		if (Hand == INDEX_NONE)
		{
			continue;
		}
		const FTransform& Ref = Bones.GetRefPoseTransform(Index);
		FTransform& Bone = Output.Pose[Index];
		Bone.SetTranslation(Ref.GetTranslation());
		Bone.SetScale3D(Ref.GetScale3D());
		if (Bones.GetParentBoneIndex(Index) == HandIndex[Hand])
		{
			// a metacarpal (or the thumb's first joint, handled with the grip below if it is one)
			bool bFingerJoint = false;
			for (int32 Finger = 0; Finger < 5 && !bFingerJoint; ++Finger)
			{
				bFingerJoint = Bones.GetPoseBoneIndexForBoneName(Names[Hand][Finger][0]) == Bones.MakeMeshPoseIndex(Index).GetInt();
			}
			if (!bFingerJoint)
			{
				Bone.SetRotation(Ref.GetRotation());
			}
		}
	}

	// Each gripping hand's finger joints go from the clip's rotation toward the reference pose turned by the
	// pose's rotation vector (the hold was designed on the reference pose, so it lands where it was designed);
	// a pose with a shape first closes its fingers on that shape.
	for (int32 Hand = 0; Hand < 2; ++Hand)
	{
		if (Grip[Hand] <= KINDA_SMALL_NUMBER)
		{
			continue;
		}
		FWTAHandPose Fitted = Pose[Hand];
		if (Fitted.bContact && Fitted.Shape.Kind != FWTAHoldShape::None)
		{
			SolveContact(Bones, Hand, Fitted);
		}
		for (int32 Finger = 0; Finger < 5; ++Finger)
		{
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
				const FVector& Turn = Fitted.Joint[Finger][Joint];
				const float Degrees = static_cast<float>(Turn.Size());
				const FQuat Local = Degrees > KINDA_SMALL_NUMBER ? FQuat(Turn / Degrees, FMath::DegreesToRadians(Degrees)) : FQuat::Identity;
				const FQuat Target = Bones.GetRefPoseTransform(Index).GetRotation() * Local;
				FTransform& Bone = Output.Pose[Index];
				Bone.SetRotation(FQuat::Slerp(Bone.GetRotation(), Target, Grip[Hand]));
			}
		}
	}
}

namespace
{
	/** The MetaHuman finger joints' hinge axes in their own frames (unreal/Tools/holds/design_holds.py). */
	const FVector WaxFingerAxis[3] = { FVector(0.10, 0.20, -0.97).GetSafeNormal(), FVector(0.25, 0.37, -0.89).GetSafeNormal(), FVector(0.0, 0.0, -1.0) };
	const FVector WaxThumbAxis = FVector(0.58, -0.58, -0.58).GetSafeNormal();
	/** The flesh around each finger's bones, and how far its tip reaches past the last joint (cm). */
	const float WaxFingerRadius[5] = { 0.85f, 0.85f, 0.8f, 0.7f, 1.0f };
	const float WaxFingerTip[5] = { 2.3f, 2.4f, 2.3f, 2.0f, 2.6f };

	/** The palm frame in the hand bone's own space (the inverse of AWTAWaxStageActor's PalmFrame): a point in the palm frame to the hand bone. */
	FVector WaxPalmToHand(const FVector& PalmPoint, bool bRight)
	{
		// right: fingers along -X, palm normal +Y, across -Z, origin 7 cm along the fingers; left: +X, -Y, -Z
		return bRight ? FVector(-7.0 - PalmPoint.X, PalmPoint.Y, -PalmPoint.Z) : FVector(7.0 + PalmPoint.X, -PalmPoint.Y, -PalmPoint.Z);
	}
	FVector WaxHandToPalm(const FVector& HandPoint, bool bRight)
	{
		return bRight ? FVector(-7.0 - HandPoint.X, HandPoint.Y, -HandPoint.Z) : FVector(HandPoint.X - 7.0, -HandPoint.Y, -HandPoint.Z);
	}

	FQuat WaxTurn(const FVector& Vector)
	{
		const double Degrees = Vector.Size();
		return Degrees > KINDA_SMALL_NUMBER ? FQuat(Vector / Degrees, FMath::DegreesToRadians(Degrees)) : FQuat::Identity;
	}
}

void FWTAWaxAnimProxy::SolveContact(const FBoneContainer& Bones, int32 Hand, FWTAHandPose& InOut) const
{
	// The hand's bones in the hand bone's space, from the reference pose (the metacarpals are restored to it):
	// each finger is a chain hand -> metacarpal (none for the thumb) -> joint 1 -> 2 -> 3 -> tip. A joint's
	// rotation = its reference rotation times a turn about its hinge; the chain is run forward from the
	// knuckle and each joint curls, from open, until any flesh beyond it would enter the shape.
	static const TCHAR* Fingers[5] = { TEXT("index"), TEXT("middle"), TEXT("ring"), TEXT("pinky"), TEXT("thumb") };
	static const TCHAR* Sides[2] = { TEXT("l"), TEXT("r") };
	const bool bRight = Hand == 1;
	const FName HandBone(*FString::Printf(TEXT("hand_%s"), Sides[Hand]));
	const int32 HandMesh = Bones.GetPoseBoneIndexForBoneName(HandBone);
	if (HandMesh == INDEX_NONE)
	{
		return;
	}
	const FCompactPoseBoneIndex HandIndex = Bones.MakeCompactPoseIndex(FMeshPoseBoneIndex(HandMesh));
	if (HandIndex.GetInt() == INDEX_NONE)
	{
		return;
	}
	const FWTAHoldShape& Shape = InOut.Shape;

	for (int32 Finger = 0; Finger < 5; ++Finger)
	{
		// the chain's bones and their reference local transforms, hand -> ... -> joint 3
		FCompactPoseBoneIndex Joints[3] = { FCompactPoseBoneIndex(INDEX_NONE), FCompactPoseBoneIndex(INDEX_NONE), FCompactPoseBoneIndex(INDEX_NONE) };
		bool bOk = true;
		for (int32 j = 0; j < 3 && bOk; ++j)
		{
			const int32 Mesh = Bones.GetPoseBoneIndexForBoneName(FName(*FString::Printf(TEXT("%s_%02d_%s"), Fingers[Finger], j + 1, Sides[Hand])));
			Joints[j] = Mesh != INDEX_NONE ? Bones.MakeCompactPoseIndex(FMeshPoseBoneIndex(Mesh)) : FCompactPoseBoneIndex(INDEX_NONE);
			bOk = Joints[j].GetInt() != INDEX_NONE;
		}
		if (!bOk)
		{
			continue;
		}
		// joint 1's transform in hand space goes through whatever sits between (a metacarpal): walk up from it
		FTransform ToKnuckle = FTransform::Identity;
		for (FCompactPoseBoneIndex Up = Bones.GetParentBoneIndex(Joints[0]); Up.GetInt() != INDEX_NONE && Up != HandIndex; Up = Bones.GetParentBoneIndex(Up))
		{
			ToKnuckle = ToKnuckle * Bones.GetRefPoseTransform(Up);
		}
		const bool bThumb = Finger == 4;
		const FVector Axis[3] = { bThumb ? InOut.Joint[4][0].GetSafeNormal() : WaxFingerAxis[0], bThumb ? WaxThumbAxis : WaxFingerAxis[1], bThumb ? WaxThumbAxis : WaxFingerAxis[2] };
		// the open start and the furthest curl of each joint (degrees about its hinge, over the reference pose);
		// the thumb's first joint is the designed swing and does not move
		float Open[3] = { -38.f, -22.f, -16.f };
		float Most[3] = { 70.f, 95.f, 65.f };
		if (bThumb)
		{
			const float Swing = static_cast<float>(InOut.Joint[4][0].Size());
			Open[0] = Swing; Most[0] = Swing;
			Open[1] = static_cast<float>(InOut.Joint[4][1].Size()) - 30.f; Most[1] = Open[1] + 90.f;
			Open[2] = static_cast<float>(InOut.Joint[4][2].Size()) - 25.f; Most[2] = Open[2] + 80.f;
		}
		float Deg[3] = { Open[0], Open[1], Open[2] };
		const float Radius = WaxFingerRadius[Finger];

		// the chain forward from joint 1 with the given degrees: joint positions and the tip, in hand space
		auto Chain = [&](const float (&D)[3], FVector (&Out)[4])
		{
			FTransform T = ToKnuckle;
			FVector Previous = ToKnuckle.GetLocation();
			for (int32 j = 0; j < 3; ++j)
			{
				const FTransform& Ref = Bones.GetRefPoseTransform(Joints[j]);
				FTransform Local = Ref;
				Local.SetRotation(Ref.GetRotation() * FQuat(Axis[j], FMath::DegreesToRadians(D[j])));
				T = Local * T;
				Out[j] = T.GetLocation();
			}
			Out[3] = Out[2] + (Out[2] - Out[1]).GetSafeNormal() * WaxFingerTip[Finger];
		};
		// does any flesh from joint From outward enter the shape?
		auto Enters = [&](const float (&D)[3], int32 From) -> bool
		{
			FVector P[4];
			Chain(D, P);
			for (int32 k = From; k < 3; ++k)
			{
				for (int32 i = 1; i <= 4; ++i)
				{
					const FVector Q = FMath::Lerp(P[k], P[k + 1], i / 4.f);
					if (Shape.Distance(WaxHandToPalm(Q, bRight)) < Radius + 0.05f)
					{
						return true;
					}
				}
			}
			return false;
		};
		for (int32 j = (bThumb ? 1 : 0); j < 3; ++j)
		{
			if (Enters(Deg, j))
			{
				continue;                  // already touching with the joint open: it stays open
			}
			float Lo = Open[j], Hi = Most[j];
			Deg[j] = Hi;
			if (!Enters(Deg, j))
			{
				continue;                  // nothing to touch in reach: fully curled
			}
			for (int32 Step = 0; Step < 9; ++Step)
			{
				const float Mid = 0.5f * (Lo + Hi);
				Deg[j] = Mid;
				if (Enters(Deg, j)) { Hi = Mid; } else { Lo = Mid; }
			}
			Deg[j] = Lo;
		}
		for (int32 j = (bThumb ? 1 : 0); j < 3; ++j)
		{
			InOut.Joint[Finger][j] = Axis[j] * Deg[j];
		}
	}
}

void FWTAWaxAnimProxy::ApplyArmIK(FPoseContext& Output) const
{
	if (IKWeight[0] <= KINDA_SMALL_NUMBER && IKWeight[1] <= KINDA_SMALL_NUMBER)
	{
		return;
	}
	static const TCHAR* Sides[2] = { TEXT("l"), TEXT("r") };
	static const TCHAR* Links[3] = { TEXT("upperarm"), TEXT("lowerarm"), TEXT("hand") };
	const FBoneContainer& Bones = Output.Pose.GetBoneContainer();
	FCSPose<FCompactPose> CS;
	CS.InitPose(Output.Pose);
	for (int32 Hand = 0; Hand < 2; ++Hand)
	{
		const float W = IKWeight[Hand];
		if (W <= KINDA_SMALL_NUMBER)
		{
			continue;
		}
		FCompactPoseBoneIndex Chain[3] = { FCompactPoseBoneIndex(INDEX_NONE), FCompactPoseBoneIndex(INDEX_NONE), FCompactPoseBoneIndex(INDEX_NONE) };
		bool bOk = true;
		for (int32 i = 0; i < 3 && bOk; ++i)
		{
			const int32 Mesh = Bones.GetPoseBoneIndexForBoneName(FName(*FString::Printf(TEXT("%s_%s"), Links[i], Sides[Hand])));
			Chain[i] = Mesh != INDEX_NONE ? Bones.MakeCompactPoseIndex(FMeshPoseBoneIndex(Mesh)) : FCompactPoseBoneIndex(INDEX_NONE);
			bOk = Chain[i].GetInt() != INDEX_NONE;
		}
		const FCompactPoseBoneIndex Shoulder = bOk ? Bones.GetParentBoneIndex(Chain[0]) : FCompactPoseBoneIndex(INDEX_NONE);
		if (!bOk || Shoulder.GetInt() == INDEX_NONE)
		{
			continue;
		}
		// the chain in component space, solved so the hand lands on the target and takes its rotation
		const FTransform ShoulderCS = CS.GetComponentSpaceTransform(Shoulder);
		FTransform Upper = CS.GetComponentSpaceTransform(Chain[0]);
		FTransform Lower = CS.GetComponentSpaceTransform(Chain[1]);
		FTransform End = CS.GetComponentSpaceTransform(Chain[2]);
		const FWTAHandTarget& Target = HandTarget[Hand];
		AnimationCore::SolveTwoBoneIK(Upper, Lower, End, Target.Elbow, Target.Hand.GetLocation(), false, 1.0, 1.2);
		End.SetRotation(Target.Hand.GetRotation());
		// back to local rotations, blended by the weight; the bones keep the clip's lengths
		const FQuat LocalUpper = Upper.GetRelativeTransform(ShoulderCS).GetRotation();
		const FQuat LocalLower = Lower.GetRelativeTransform(Upper).GetRotation();
		const FQuat LocalEnd = End.GetRelativeTransform(Lower).GetRotation();
		const FQuat Solved[3] = { LocalUpper, LocalLower, LocalEnd };
		for (int32 i = 0; i < 3; ++i)
		{
			FTransform& Bone = Output.Pose[Chain[i]];
			Bone.SetRotation(FQuat::Slerp(Bone.GetRotation(), Solved[i], W));
		}
	}
}

void FWTAWaxAnimProxy::ApplyLookAt(FPoseContext& Output) const
{
	if (LookWeight <= KINDA_SMALL_NUMBER)
	{
		return;
	}
	const FBoneContainer& Bones = Output.Pose.GetBoneContainer();
	static const FName Links[3] = { FName(TEXT("neck_01")), FName(TEXT("neck_02")), FName(TEXT("head")) };
	static const float Share[3] = { 0.25f, 0.25f, 0.5f };
	FCompactPoseBoneIndex Chain[3] = { FCompactPoseBoneIndex(INDEX_NONE), FCompactPoseBoneIndex(INDEX_NONE), FCompactPoseBoneIndex(INDEX_NONE) };
	for (int32 i = 0; i < 3; ++i)
	{
		const int32 Mesh = Bones.GetPoseBoneIndexForBoneName(Links[i]);
		Chain[i] = Mesh != INDEX_NONE ? Bones.MakeCompactPoseIndex(FMeshPoseBoneIndex(Mesh)) : FCompactPoseBoneIndex(INDEX_NONE);
		if (Chain[i].GetInt() == INDEX_NONE)
		{
			return;
		}
	}
	FCSPose<FCompactPose> CS;
	CS.InitPose(Output.Pose);
	// The head's forward in its own frame: the MetaHuman body faces +Y in component space, and the reference
	// pose says which head axis that is.
	FTransform RefHead = FTransform::Identity;
	for (FCompactPoseBoneIndex Up = Chain[2]; Up.GetInt() != INDEX_NONE; Up = Bones.GetParentBoneIndex(Up))
	{
		RefHead = RefHead * Bones.GetRefPoseTransform(Up);
	}
	const FVector LocalForward = RefHead.InverseTransformVectorNoScale(FVector(0.f, 1.f, 0.f)).GetSafeNormal();
	const FTransform Head = CS.GetComponentSpaceTransform(Chain[2]);
	const FVector Now = Head.TransformVectorNoScale(LocalForward).GetSafeNormal();
	const FVector Wanted = (LookTarget - Head.GetLocation()).GetSafeNormal();
	if (Now.IsNearlyZero() || Wanted.IsNearlyZero())
	{
		return;
	}
	// no further than a neck turns: 70 degrees in all, shared down the neck
	FQuat Turn = FQuat::FindBetweenNormals(Now, Wanted);
	FVector Axis; double Angle;
	Turn.ToAxisAndAngle(Axis, Angle);
	Angle = FMath::Min(Angle, FMath::DegreesToRadians(70.0)) * LookWeight;
	if (Angle < KINDA_SMALL_NUMBER)
	{
		return;
	}
	// Each bone is carried by the one below it, then turns its own share about its own position.
	TArray<FBoneTransform> Moved;
	FTransform Parent = CS.GetComponentSpaceTransform(Chain[0]);
	FTransform ParentWas = Parent;
	for (int32 i = 0; i < 3; ++i)
	{
		const FTransform Was = CS.GetComponentSpaceTransform(Chain[i]);
		FTransform T = i == 0 ? Was : Was.GetRelativeTransform(ParentWas) * Parent;
		T.SetRotation(FQuat(Axis, Angle * Share[i]) * T.GetRotation());
		Moved.Add(FBoneTransform(Chain[i], T));
		ParentWas = Was;
		Parent = T;
	}
	CS.LocalBlendCSBoneTransforms(Moved, 1.f);
	FCSPose<FCompactPose>::ConvertComponentPosesToLocalPoses(MoveTemp(CS), Output.Pose);
}

void UWTAWaxAnimInstance::SetHandTarget(bool bRightHand, float Weight, const FTransform& HandCS, const FVector& ElbowCS)
{
	FWTAHandTarget& Target = PendingHand[bRightHand ? 1 : 0];
	Target.Weight = FMath::Clamp(Weight, 0.f, 1.f);
	if (Target.Weight > KINDA_SMALL_NUMBER)
	{
		Target.Hand = HandCS;
		Target.Elbow = ElbowCS;
	}
}

void UWTAWaxAnimInstance::SetLookAt(float Weight, const FVector& TargetCS)
{
	PendingLookWeight = FMath::Clamp(Weight, 0.f, 1.f);
	if (PendingLookWeight > KINDA_SMALL_NUMBER)
	{
		PendingLook = TargetCS;
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

void UWTAWaxAnimInstance::SetGrip(bool bRightHand, float Amount, const FWTAHandPose& InPose)
{
	const int32 Hand = bRightHand ? 1 : 0;
	PendingGrip[Hand] = FMath::Clamp(Amount, 0.f, 1.f);
	if (PendingGrip[Hand] > KINDA_SMALL_NUMBER)
	{
		PendingPose[Hand] = InPose;
	}
}
