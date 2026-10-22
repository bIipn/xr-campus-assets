// Walk the Archive - a Wax Hall stage: the reenactors act while you are near it, and are wax when you are not.

#include "World/WTAWaxStageActor.h"
#include "Animation/AnimSequence.h"
#include "Components/BoxComponent.h"
#include "Components/LODSyncComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "Engine/EngineTypes.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Systems/WTAContentSubsystem.h"
#include "Systems/WTAProgressSubsystem.h"
#include "TimerManager.h"
#include "World/WTAPeopleLibrary.h"
#include "World/WTAWaxAnimInstance.h"

namespace
{
	AWTAPlayerController* WaxFindController(const UObject* WorldContext)
	{
		return Cast<AWTAPlayerController>(UGameplayStatics::GetPlayerController(WorldContext, 0));
	}

	/** The body bone a prop key's Socket names. */
	FName WaxSocketBone(FName Socket)
	{
		static const FName Head(TEXT("head"));
		static const FName HandL(TEXT("hand_l"));
		static const FName HandR(TEXT("hand_r"));
		static const FName Chest(TEXT("chest"));
		static const FName Spine(TEXT("spine_05"));
		if (Socket == Chest)
		{
			return Spine;
		}
		if (Socket == Head || Socket == HandL || Socket == HandR)
		{
			return Socket;
		}
		return Spine;
	}

	/**
	 * A stand-in for a prop of this kind when no modelled mesh is imported: a block of SizeCm in the socket's
	 * frame (Offset/Rotation apply to the head and chest; a hand uses the grip table below). Worn: the block
	 * sits over the eyes the way the web draws it from across the aisle.
	 */
	struct FWaxPropKind
	{
		const TCHAR* Mesh;
		FVector SizeCm;
		FVector Offset;
		FRotator Rotation;
		const TCHAR* Material;
	};

	const FWaxPropKind* WaxPropKind(FName Kind)
	{
		static const TCHAR* Cube = TEXT("/Engine/BasicShapes/Cube.Cube");
		static const TCHAR* Dark = TEXT("/Game/WTA/Materials/M_WTA_PropDark.M_WTA_PropDark");
		static const TCHAR* Paper = TEXT("/Game/WTA/Materials/M_WTA_PropPaper.M_WTA_PropPaper");
		static const TCHAR* Card = TEXT("/Game/WTA/Materials/M_WTA_PropCard.M_WTA_PropCard");
		static const TMap<FName, FWaxPropKind> Kinds = {
			{ FName(TEXT("headset")),   { Cube, FVector(11.f, 20.f, 9.f), FVector(9.f, 0.f, 4.f), FRotator(0.f, 0.f, 0.f), Dark } },
			{ FName(TEXT("tablet")),    { Cube, FVector(1.2f, 24.f, 17.f), FVector(9.f, 0.f, 1.f), FRotator(0.f, 0.f, 0.f), Dark } },
			{ FName(TEXT("clipboard")), { Cube, FVector(1.f, 23.f, 32.f), FVector(8.f, 0.f, 2.f), FRotator(0.f, 0.f, 0.f), Paper } },
			{ FName(TEXT("book")),      { Cube, FVector(4.f, 26.f, 18.f), FVector(0.f, 0.f, 0.f), FRotator(0.f, 0.f, 0.f), Paper } },
			{ FName(TEXT("box")),       { Cube, FVector(32.f, 40.f, 28.f), FVector(0.f, 0.f, 0.f), FRotator(0.f, 0.f, 0.f), Card } },
			{ FName(TEXT("phone")),     { Cube, FVector(1.f, 7.5f, 15.f), FVector(6.f, 0.f, 0.f), FRotator(0.f, 0.f, 0.f), Dark } },
		};
		return Kinds.Find(Kind);
	}

	/**
	 * How a modelled prop (bl/props.py) sits in a hand, and how that hand closes on it. The prop's own frame is
	 * put in the palm: +X along the fingers, +Y out of the palm, +Z across it (see PalmFrame); Hold is the prop's
	 * transform in that frame, for the right hand (the left is its mirror in Z). Pose is the finger pose of the
	 * hold (UWTAWaxAnimInstance::SetGrip).
	 *
	 * One hold for everything: the fingers lie flat and the prop rests on them, 2.5 cm out from the palm bones,
	 * with the thumb pressed on its top near its near edge - a tablet, clipboard or phone held by one end, an
	 * open book on the hand. The headset hangs by its top strap: the strap's tube lies across the flat fingers
	 * under the thumb, and the rest of the headset hangs from it the way the world's down says, so it dangles
	 * below the hand however the arm is held (bHang; the tube's point and axes are in the prop's own frame).
	 *
	 * Designed offline against the body's reference pose and the prop meshes by unreal/Tools/holds/design_holds.py
	 * (the joints from Tools/holds/probe_palm.py): the fingers' flesh tops lie within a millimetre of the prop's
	 * underside and the thumb's pad within a millimetre of its top. Rerun it after changing a prop model.
	 */
	struct FWaxGrip
	{
		FTransform Hold;
		FWTAHandPose Pose;
		bool bHang = false;
		FVector HangPoint = FVector::ZeroVector;         // the strap tube's top, prop frame
		FVector HangTangent = FVector::ForwardVector;    // along that tube, prop frame
		FVector HangUp = FVector::UpVector;              // the prop's axis that points from its body to the tube
		FVector Tube = FVector::ZeroVector;              // where the tube lies in the palm, right hand
		/** The prop as a box in its own frame (centre, half extents), for the fingers to close on; a hanging prop is its tube. */
		FVector BoxCentre = FVector::ZeroVector;
		FVector BoxHalf = FVector::ZeroVector;
		/**
		 * Where a person holds this to use it: the palm's origin from the middle of the shoulders (forward, toward
		 * the holding side, up; cm), with the palm turned so the prop faces the eyes, and the point of the prop the
		 * eyes go to (prop frame). bArm false leaves the arm to the clip (a headset carried by its strap goes
		 * wherever the hand goes). bTwoHands: carried at the chest with a hand flat on each side (the box).
		 */
		bool bArm = false;
		FVector Stance = FVector::ZeroVector;
		bool bLook = false;
		FVector LookPoint = FVector::ZeroVector;
		bool bTwoHands = false;
	};

	/** The fingers laid flat (index, middle, ring, little), as rotation vectors in degrees per joint. */
	void WaxFlatFingers(FWTAHandPose& Pose)
	{
		static const FVector Flat[4][3] = {
			{ FVector(-1.3, -2.7, 12.9), FVector(-5.8, -8.5, 20.5), FVector(0.0, 0.0, 5.0) },
			{ FVector(-0.5, -1.1, 5.1), FVector(-9.6, -14.3, 34.3), FVector(0.0, 0.0, 10.2) },
			{ FVector(-0.5, -1.1, 5.2), FVector(-7.7, -11.4, 27.3), FVector(0.0, 0.0, 10.6) },
			{ FVector(-1.3, -2.6, 12.8), FVector(-5.6, -8.3, 19.9), FVector(0.0, 0.0, 8.7) },
		};
		for (int32 f = 0; f < 4; ++f)
		{
			for (int32 j = 0; j < 3; ++j)
			{
				Pose.Joint[f][j] = Flat[f][j];
			}
		}
	}

	FWaxGrip WaxSlabGrip(float Lift, const FVector& Thumb1, const FVector& Thumb2, const FVector& Thumb3, const FVector& BoxCentre, const FVector& BoxHalf)
	{
		FWaxGrip Grip;
		Grip.Hold = FTransform(FQuat::Identity, FVector(0.f, Lift, 0.f));
		WaxFlatFingers(Grip.Pose);
		Grip.Pose.Joint[4][0] = Thumb1;
		Grip.Pose.Joint[4][1] = Thumb2;
		Grip.Pose.Joint[4][2] = Thumb3;
		Grip.BoxCentre = BoxCentre;
		Grip.BoxHalf = BoxHalf;
		return Grip;
	}

	FWaxGrip& WaxStance(FWaxGrip& Grip, const FVector& Stance, const FVector& LookPoint)
	{
		Grip.bArm = true;
		Grip.Stance = Stance;
		Grip.bLook = true;
		Grip.LookPoint = LookPoint;
		return Grip;
	}

	const FWaxGrip* WaxGrip(FName Kind)
	{
		static TMap<FName, FWaxGrip> Grips;
		if (Grips.Num() == 0)
		{
			// each prop: how it lies in the palm, the thumb's swing over it, its box, and where a person holds it
			// to use it (the palm from the middle of the shoulders, and the point the eyes go to)
			FWaxGrip Phone = WaxSlabGrip(2.58f, FVector(-10.7, -7.8, -8.2), FVector(20.9, -20.9, -20.9), FVector(15.7, -15.7, -15.7), FVector(8.5, 0.45, 0.0), FVector(7.5, 0.45, 3.8));
			Grips.Add(FName(TEXT("phone")),     WaxStance(Phone, FVector(24.f, 8.f, -22.f), FVector(8.5, 1.0, 0.0)));
			FWaxGrip Tablet = WaxSlabGrip(2.47f, FVector(-28.0, 7.7, -8.9), FVector(22.6, -22.6, -22.6), FVector(16.0, -16.0, -16.0), FVector(10.5, 0.4, 0.0), FVector(12.0, 0.4, 8.5));
			Grips.Add(FName(TEXT("tablet")),    WaxStance(Tablet, FVector(28.f, 10.f, -32.f), FVector(11.0, 1.0, 0.0)));
			FWaxGrip Clipboard = WaxSlabGrip(2.60f, FVector(-29.5, 9.2, -8.9), FVector(22.9, -22.9, -22.9), FVector(16.0, -16.0, -16.0), FVector(13.0, 0.5, 0.0), FVector(16.0, 0.6, 11.5));
			Grips.Add(FName(TEXT("clipboard")), WaxStance(Clipboard, FVector(28.f, 8.f, -32.f), FVector(14.0, 1.0, 0.0)));
			FWaxGrip Book = WaxSlabGrip(2.50f, FVector(-35.4, 27.8, -11.9), FVector(12.9, -12.9, -12.9), FVector(18.3, -18.3, -18.3), FVector(9.5, 1.2, 0.0), FVector(10.0, 1.2, 13.4));
			Grips.Add(FName(TEXT("book")),      WaxStance(Book, FVector(26.f, 6.f, -36.f), FVector(9.5, 3.0, 0.0)));
			// the box is carried at the chest with a hand flat on each side (SetKeyGrip); in one hand it would rest like a slab
			FWaxGrip Box = WaxSlabGrip(2.50f, FVector(-28.0, 7.7, -8.9), FVector(22.6, -22.6, -22.6), FVector(16.0, -16.0, -16.0), FVector::ZeroVector, FVector(16.0, 20.0, 14.0));
			Box.bTwoHands = true;
			Grips.Add(FName(TEXT("box")), Box);
			FWaxGrip Headset = WaxSlabGrip(0.f, FVector(-5.4, -7.7, -11.8), FVector(15.7, -15.7, -15.7), FVector(11.2, -11.2, -11.2), FVector(-9.6, 0.0, 0.0), FVector(14.8, 9.9, 12.0));
			Headset.bHang = true;
			Headset.HangPoint = FVector(-12.f, 0.f, 10.6f);     // the top strap's top: 12 cm behind the visor, 10.6 above the band
			Headset.HangTangent = FVector::ForwardVector;      // the top strap runs front to back
			Headset.HangUp = FVector::UpVector;
			Headset.Tube = FVector(3.f, 3.35f, 1.f);            // resting on the flat fingers' flesh, under the thumb
			// a fallback for a hand whose palm frame can't be built: the hanging frame itself, palm down
			Headset.Hold = FTransform(FMatrix(FVector(0, 0, 1), FVector(-1, 0, 0), FVector(0, -1, 0), FVector::ZeroVector));
			Headset.Hold.SetLocation(Headset.Tube - Headset.Hold.TransformVector(Headset.HangPoint));
			Grips.Add(FName(TEXT("headset")), Headset);
		}
		return Grips.Find(Kind);
	}

	/** The right hand's hold mirrored for the left: Z across the palm flips, so the translation's Z and the rotation's sense do. */
	FTransform WaxMirrorHold(const FTransform& Hold)
	{
		const FQuat Q = Hold.GetRotation();
		FVector T = Hold.GetLocation();
		T.Z = -T.Z;
		return FTransform(FQuat(-Q.X, -Q.Y, Q.Z, Q.W), T);
	}

	/**
	 * A prop in a hand, in world space: Palm is the hand's palm frame (PalmFrame) and bRight which hand. A
	 * hanging prop's tube lies across the palm at Grip.Tube and the prop hangs from it toward the world's down,
	 * swung SwingRad about the tube (its pendulum, FWaxSwing).
	 */
	FTransform WaxHeldTransform(const FWaxGrip& Grip, const FTransform& Palm, bool bRight, float SwingRad)
	{
		if (!Grip.bHang)
		{
			return (bRight ? Grip.Hold : WaxMirrorHold(Grip.Hold)) * Palm;
		}
		FVector Tube = Grip.Tube;
		if (!bRight)
		{
			Tube.Z = -Tube.Z;
		}
		const FVector TubeWorld = Palm.TransformPosition(Tube);
		// the tube runs across the palm, toward the little finger on both hands
		const FVector Along = Palm.GetUnitAxis(EAxis::Z) * (bRight ? 1.f : -1.f);
		FVector Down = -FVector::UpVector;
		Down -= Along * FVector::DotProduct(Down, Along);
		if (!Down.Normalize(KINDA_SMALL_NUMBER))
		{
			Down = Palm.GetUnitAxis(EAxis::X);               // the tube is vertical: hang along the fingers
		}
		else if (!FMath::IsNearlyZero(SwingRad))
		{
			// swung about the tube, in the plane square to it
			const FVector Side = FVector::CrossProduct(Along, Down);
			Down = (Down * FMath::Cos(SwingRad) + Side * FMath::Sin(SwingRad)).GetSafeNormal();
		}
		// the prop's frame: HangTangent along the tube, HangUp against the hang, the third axis square to both
		const FVector Up = -Down;
		const FVector Third = FVector::CrossProduct(Up, Along).GetSafeNormal();
		// rows of a matrix that takes the prop's (tangent, third, up) to (Along, Third, Up): build it as the
		// prop frame's basis in world, then account for which prop axes those are
		const FMatrix World(Along, Third, Up, FVector::ZeroVector);
		const FMatrix Local(Grip.HangTangent, FVector::CrossProduct(Grip.HangUp, Grip.HangTangent).GetSafeNormal(), Grip.HangUp, FVector::ZeroVector);
		const FMatrix Rotation = Local.GetTransposed() * World;      // prop -> world (Local's rows are the prop axes)
		FTransform Out(Rotation);
		Out.SetLocation(TubeWorld - Out.TransformVector(Grip.HangPoint));
		return Out;
	}

	/**
	 * The palm, in world space, from the hand bone's own axes this frame: +X runs from the wrist toward the
	 * fingers (the rig's -X on the right hand, +X on the left), +Y is the palm's normal (the rig's +Y on the
	 * right, -Y on the left), +Z = X x Y across the palm, and the origin is 7 cm along the fingers from the wrist
	 * (mid-palm). The bone's axes, not the finger joints, so no finger pose can turn the frame over. Z runs toward
	 * the little finger on the right hand and the index on the left, so a right-hand hold mirrored in Z fits the
	 * left (WaxMirrorHold). False when the body has no such hand.
	 */
	bool PalmFrame(const USkeletalMeshComponent* Body, bool bRight, FTransform& Out)
	{
		static const FName HandL(TEXT("hand_l"));
		static const FName HandR(TEXT("hand_r"));
		const FName Wrist = bRight ? HandR : HandL;
		if (Body == nullptr || Body->GetBoneIndex(Wrist) == INDEX_NONE)
		{
			return false;
		}
		const FTransform Hand = Body->GetSocketTransform(Wrist, RTS_World);
		const float Sign = bRight ? 1.f : -1.f;
		const FVector F = (Hand.GetUnitAxis(EAxis::X) * -Sign).GetSafeNormal();
		FVector N = Hand.GetUnitAxis(EAxis::Y) * Sign;
		N = (N - F * FVector::DotProduct(N, F)).GetSafeNormal();
		if (F.IsNearlyZero() || N.IsNearlyZero())
		{
			return false;
		}
		Out = FTransform(FMatrix(F, N, FVector::CrossProduct(F, N), Hand.GetLocation() + F * 7.f));
		return true;
	}

	/** The hand bone's transform (world) whose palm frame is Palm: PalmFrame the other way round. */
	FTransform WaxHandFromPalm(const FTransform& Palm, bool bRight)
	{
		const float Sign = bRight ? 1.f : -1.f;
		const FVector F = Palm.GetUnitAxis(EAxis::X);
		const FVector N = Palm.GetUnitAxis(EAxis::Y);
		const FVector Z = Palm.GetUnitAxis(EAxis::Z);
		return FTransform(FMatrix(F * -Sign, N * Sign, -Z, Palm.GetLocation() - F * 7.f));
	}

	/** The prop's shape in the palm frame of one hand, from its hold, for the fingers to close on. */
	void WaxShapeFor(const FWaxGrip& Grip, bool bRight, FWTAHandPose& Pose)
	{
		Pose.bContact = true;
		if (Grip.bHang)
		{
			FVector Tube = Grip.Tube;
			if (!bRight) { Tube.Z = -Tube.Z; }
			Pose.Shape.Kind = FWTAHoldShape::Tube;
			Pose.Shape.Frame = FTransform(FQuat::Identity, Tube);      // the tube runs along the palm's Z
			Pose.Shape.Radius = 0.85f;
			return;
		}
		const FTransform Hold = bRight ? Grip.Hold : WaxMirrorHold(Grip.Hold);
		Pose.Shape.Kind = FWTAHoldShape::Box;
		Pose.Shape.Frame = FTransform(FQuat::Identity, Grip.BoxCentre) * Hold;
		Pose.Shape.Half = Grip.BoxHalf;
	}

	/**
	 * The person's frame this frame, from the shoulders: S the middle of the two shoulder joints, Forward and
	 * Right level, Up the world's. The shoulders follow the clip's torso, so a held prop turns with the body.
	 */
	bool WaxChestFrame(const USkeletalMeshComponent* Body, const AActor* Figure, float YawOffset, FVector& OutS, FVector& OutForward, FVector& OutRight)
	{
		static const FName UpperL(TEXT("upperarm_l"));
		static const FName UpperR(TEXT("upperarm_r"));
		if (Body == nullptr || Figure == nullptr || Body->GetBoneIndex(UpperL) == INDEX_NONE || Body->GetBoneIndex(UpperR) == INDEX_NONE)
		{
			return false;
		}
		const FVector L = Body->GetSocketLocation(UpperL);
		const FVector R = Body->GetSocketLocation(UpperR);
		OutS = (L + R) * 0.5f;
		const FVector Facing = FRotator(0.f, Figure->GetActorRotation().Yaw - YawOffset, 0.f).Vector();
		FVector Right = R - L;
		Right.Z = 0.f;
		if (!Right.Normalize(KINDA_SMALL_NUMBER))
		{
			Right = FVector::CrossProduct(FVector::UpVector, Facing);     // Up x Forward = Right
		}
		FVector Forward = FVector::CrossProduct(Right, FVector::UpVector);  // Right x Up = Forward
		if (FVector::DotProduct(Forward, Facing) < 0.f)
		{
			Forward = -Forward;
			Right = -Right;
		}
		OutForward = Forward;
		OutRight = Right;
		return true;
	}

	/** Where the eyes are: a little ahead of and above the head bone. */
	FVector WaxEyes(const USkeletalMeshComponent* Body, const FVector& S, const FVector& Forward)
	{
		static const FName Head(TEXT("head"));
		if (Body != nullptr && Body->GetBoneIndex(Head) != INDEX_NONE)
		{
			return Body->GetSocketLocation(Head) + Forward * 8.f + FVector::UpVector * 9.f;
		}
		return S + Forward * 8.f + FVector::UpVector * 26.f;
	}

	/**
	 * The palm frame (world) that holds a prop where its stance says, turned so the prop's face points at the
	 * eyes: +Y (out of the palm, the prop's face) toward Eyes, +X (the fingers) as far forward as that allows.
	 */
	FTransform WaxStancePalm(const FWaxGrip& Grip, bool bRight, const FVector& S, const FVector& Forward, const FVector& Right, const FVector& Eyes)
	{
		const float Side = bRight ? 1.f : -1.f;
		const FVector O = S + Forward * Grip.Stance.X + Right * (Grip.Stance.Y * Side) + FVector::UpVector * Grip.Stance.Z;
		FVector N = (Eyes - O).GetSafeNormal();
		if (N.IsNearlyZero())
		{
			N = FVector::UpVector;
		}
		FVector F = Forward - N * FVector::DotProduct(Forward, N);
		if (!F.Normalize(KINDA_SMALL_NUMBER))
		{
			F = FVector::CrossProduct(N, Right).GetSafeNormal();
		}
		return FTransform(FMatrix(F, N, FVector::CrossProduct(F, N), O));
	}

	/**
	 * One step of a hanging prop's pendulum: Pivot is where its tube is this frame and Along the tube's axis.
	 * The prop (its centre L below the tube) swings under gravity and the hand's acceleration, damped, in the
	 * plane square to the tube. Dt 0 leaves it as it is.
	 */
	void WaxSwingStep(AWTAWaxStageActor::FWaxSwing& Swing, const FVector& Pivot, const FVector& Along, float Dt)
	{
		constexpr float L = 12.f;            // cm from the strap's top to the headset's middle
		constexpr float Damping = 2.5f;      // per second: a strap on fingers swings a few times, no more
		constexpr float G = 981.f;
		if (Dt <= 0.f)
		{
			return;
		}
		Dt = FMath::Min(Dt, 0.1f);
		FVector Accel = FVector::ZeroVector;
		if (Swing.Frames >= 2)
		{
			const FVector V = (Pivot - Swing.Pivot) / Dt;
			Accel = ((V - Swing.Velocity) / Dt).GetClampedToMaxSize(3000.f);
			Swing.Velocity = V;
		}
		else if (Swing.Frames == 1)
		{
			Swing.Velocity = (Pivot - Swing.Pivot) / Dt;
		}
		Swing.Pivot = Pivot;
		Swing.Frames = FMath::Min(Swing.Frames + 1, 2);

		FVector Down = -FVector::UpVector;
		Down -= Along * FVector::DotProduct(Down, Along);
		if (!Down.Normalize(KINDA_SMALL_NUMBER))
		{
			Swing.Angle = 0.f;
			Swing.Rate = 0.f;
			return;
		}
		const FVector Side = FVector::CrossProduct(Along, Down);
		const float ADown = FVector::DotProduct(Accel, Down);
		const float ASide = FVector::DotProduct(Accel, Side);
		float Left = Dt;
		while (Left > 0.f)
		{
			const float H = FMath::Min(Left, 0.01f);
			Left -= H;
			// a pendulum under the effective gravity G*Down - Accel, in the pivot's frame
			const float AngAccel = -((G - ADown) / L) * FMath::Sin(Swing.Angle) - (ASide / L) * FMath::Cos(Swing.Angle) - Damping * Swing.Rate;
			Swing.Rate += AngAccel * H;
			Swing.Angle += Swing.Rate * H;
		}
		const float Limit = FMath::DegreesToRadians(80.f);
		if (Swing.Angle > Limit) { Swing.Angle = Limit; Swing.Rate = FMath::Min(Swing.Rate, 0.f); }
		if (Swing.Angle < -Limit) { Swing.Angle = -Limit; Swing.Rate = FMath::Max(Swing.Rate, 0.f); }
	}

	/** A campus mesh by wing and name, where the Interchange import files them (import_meshes.py). */
	UStaticMesh* FindCampusMesh(const TCHAR* Wing, const FString& Name)
	{
		const FString Paths[2] = {
			FString::Printf(TEXT("/Game/WTA/Campus/%s/%s/StaticMeshes/%s.%s"), Wing, Wing, *Name, *Name),
			FString::Printf(TEXT("/Game/WTA/Campus/%s/StaticMeshes/%s.%s"), Wing, *Name, *Name),
		};
		for (const FString& Path : Paths)
		{
			if (UStaticMesh* Mesh = Cast<UStaticMesh>(FSoftObjectPath(Path).TryLoad()))
			{
				return Mesh;
			}
		}
		return nullptr;
	}
}

UWTAWaxPropTick::UWTAWaxPropTick()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
	PrimaryComponentTick.TickGroup = TG_PostUpdateWork;
}

void UWTAWaxPropTick::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	if (AWTAWaxStageActor* Stage = Cast<AWTAWaxStageActor>(GetOwner()))
	{
		Stage->PlaceProps(DeltaTime);
	}
}

AWTAWaxStageActor::AWTAWaxStageActor()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = true;
	LateTick = CreateDefaultSubobject<UWTAWaxPropTick>(TEXT("LateTick"));

	// The watch zone: overlaps pawns only.
	Trigger = CreateDefaultSubobject<UBoxComponent>(TEXT("Trigger"));
	SetRootComponent(Trigger);
	Trigger->SetBoxExtent(TriggerExtent);
	Trigger->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Trigger->SetCollisionObjectType(ECC_WorldDynamic);
	Trigger->SetCollisionResponseToAllChannels(ECR_Ignore);
	Trigger->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	Trigger->SetGenerateOverlapEvents(true);
	Trigger->SetCanEverAffectNavigation(false);
	Trigger->CanCharacterStepUpOn = ECB_No;
	Trigger->SetHiddenInGame(true);

	FigurePose = TSoftObjectPtr<UAnimSequence>(FSoftObjectPath(UWTAPeopleLibrary::DefaultIdlePath));
}

void AWTAWaxStageActor::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

	if (Trigger != nullptr)
	{
		Trigger->SetBoxExtent(TriggerExtent, false);
	}
}

void AWTAWaxStageActor::BeginPlay()
{
	Super::BeginPlay();

	bHasScene = false;
	if (const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this))
	{
		if (const FWTAWaxSceneRow* Row = Content->FindWaxScene(SceneId))
		{
			Scene = *Row;
			bHasScene = true;
		}
	}
	if (!bHasScene)
	{
		UE_LOG(LogWTA, Warning, TEXT("%s: no DT_WaxScenes row '%s'"), *GetName(), *SceneId.ToString());
		return;
	}
	SpawnFigures();
}

void AWTAWaxStageActor::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	FigureBones.Reset();
	Plays.Reset();
	for (AActor* Figure : Figures)
	{
		if (IsValid(Figure))
		{
			Figure->Destroy();
		}
	}
	Figures.Reset();
	Super::EndPlay(EndPlayReason);
}

UAnimSequence* AWTAWaxStageActor::LoadAction(FName Action)
{
	if (Action.IsNone())
	{
		return nullptr;
	}
	if (const TObjectPtr<UAnimSequence>* Found = Clips.Find(Action))
	{
		return *Found;
	}
	const FString Name = FString::Printf(TEXT("AS_WTA_%s"), *Action.ToString());
	const FSoftObjectPath Path(FString::Printf(TEXT("%s/%s.%s"), *AnimFolder, *Name, *Name));
	UAnimSequence* Clip = Cast<UAnimSequence>(Path.TryLoad());
	if (Clip == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("%s: no clip for action '%s' (%s): the figure holds its pose instead"),
			*GetName(), *Action.ToString(), *Path.ToString());
	}
	Clips.Add(Action, Clip);
	return Clip;
}

void AWTAWaxStageActor::SpawnFigures()
{
	UWorld* World = GetWorld();
	if (World == nullptr || Scene.Figures.Num() == 0)
	{
		return;
	}
	UAnimSequence* Idle = FigurePose.LoadSynchronous();
	const FRotator StageRotation(0.f, Scene.StageYaw, 0.f);
	int32 NotBuilt = 0;
	for (int32 FigureIndex = 0; FigureIndex < Scene.Figures.Num(); ++FigureIndex)
	{
		const FWTAWaxFigure& Figure = Scene.Figures[FigureIndex];
		UClass* Class = UWTAPeopleLibrary::LoadMetaHumanClass(Figure.Person);
		if (Class == nullptr)
		{
			++NotBuilt;
			continue;
		}
		const FVector Location = Scene.StageLocation + StageRotation.RotateVector(Figure.Offset);
		// The web could put a figure's back to the camera, which sat behind the scene; here the visitor stands in
		// the aisle, and a wax figure facing the back wall is a figure you cannot see. Turn it back toward the
		// aisle, no further than it was already turned.
		const float Facing = FMath::ClampAngle(Figure.Yaw, -MaxTurnFromAisle, MaxTurnFromAisle);
		const float BaseYaw = Scene.StageYaw + Facing + FigureYawOffset;
		FActorSpawnParameters Params;
		Params.Owner = this;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		AActor* Person = World->SpawnActor<AActor>(Class, Location, FRotator(0.f, BaseYaw, 0.f), Params);
		if (Person == nullptr)
		{
			continue;
		}
		// Wax figures stand behind the rope: nothing to collide with or hover.
		Person->SetActorEnableCollision(false);
		Figures.Add(Person);

		// Every mesh evaluates, at whatever LOD it is drawn at, never skipped by the update rate optimizer: the
		// frame before a freeze has to be a full pose (see UWTAPeopleLibrary::Freeze).
		TInlineComponentArray<USkeletalMeshComponent*> Meshes;
		Person->GetComponents(Meshes);
		for (USkeletalMeshComponent* Mesh : Meshes)
		{
			if (Mesh != nullptr)
			{
				Mesh->bEnableUpdateRateOptimizations = false;
			}
		}
		UWTAPeopleLibrary::Thaw(Person);

		// The body runs our own animation instance; the face, clothes and grooms follow it as before.
		FFigurePlay& Play = Plays.AddDefaulted_GetRef();
		Play.Figure = Person;
		Play.FigureIndex = FigureIndex;
		Play.Feet = Location;
		Play.BaseYaw = BaseYaw;
		if (USkeletalMeshComponent* Body = UWTAPeopleLibrary::FindBody(Person))
		{
			Body->SetAnimationMode(EAnimationMode::AnimationBlueprint);
			Body->SetAnimInstanceClass(UWTAWaxAnimInstance::StaticClass());
			UWTAWaxAnimInstance* Anim = Cast<UWTAWaxAnimInstance>(Body->GetAnimInstance());
			Play.Anim = Anim;
			if (Anim != nullptr)
			{
				// Stand in a frame of this figure's own first beat, so a sleeping stage is a tableau of the
				// scene rather than a row of people in the same idle.
				UAnimSequence* First = Figure.Beats.Num() > 0 ? LoadAction(Figure.Beats[0].Action) : Idle;
				if (First == nullptr)
				{
					First = Idle;
				}
				if (First != nullptr)
				{
					const float Phase = UWTAPeopleLibrary::PersonPhase(Figure.Person) * First->GetPlayLength();
					Anim->PlayClip(First, true, 1.f, Phase, 0.f);
				}
				Anim->Hold(true);
			}
		}
	}
	if (NotBuilt > 0)
	{
		UE_LOG(LogWTA, Log, TEXT("%s: %d of %d reenactors not built yet"), *GetName(), NotBuilt, Scene.Figures.Num());
	}

	// Props ride the figures' sockets; they hang off the stage so a figure's own LOD never moves them. A prop
	// shows the modelled object of its kind (HandProps, bl/props.py), else the web's own model for it
	// (Props.glb, prop__<scene>_<WebIndex>), else a block of its kind's size.
	PropModelled.Reset();
	for (const FWTAWaxProp& Prop : Scene.Props)
	{
		const FWaxPropKind* Kind = WaxPropKind(Prop.Kind);
		UStaticMesh* Mesh = nullptr;
		if (Kind != nullptr)
		{
			Mesh = FindCampusMesh(TEXT("HandProps"), FString::Printf(TEXT("prop__%s"), *Prop.Kind.ToString()));
		}
		if (Mesh == nullptr && Prop.WebIndex >= 0)
		{
			Mesh = FindCampusMesh(TEXT("Props"), FString::Printf(TEXT("prop__%s_%d"), *SceneId.ToString().Replace(TEXT("-"), TEXT("_")), Prop.WebIndex));
		}
		const bool bModelled = Mesh != nullptr;
		if (Mesh == nullptr && Kind != nullptr)
		{
			Mesh = Cast<UStaticMesh>(FSoftObjectPath(Kind->Mesh).TryLoad());
		}
		if (Mesh == nullptr)
		{
			UE_LOG(LogWTA, Warning, TEXT("%s: prop '%s' has no mesh (kind '%s', web %d)"), *GetName(), *Prop.Id.ToString(), *Prop.Kind.ToString(), Prop.WebIndex);
			PropParts.Add(nullptr);
			PropModelled.Add(false);
			continue;
		}
		UStaticMeshComponent* Part = NewObject<UStaticMeshComponent>(this);
		Part->SetStaticMesh(Mesh);
		if (!bModelled)
		{
			if (UMaterialInterface* Material = Cast<UMaterialInterface>(FSoftObjectPath(Kind->Material).TryLoad()))
			{
				for (int32 Slot = 0; Slot < Part->GetNumMaterials(); ++Slot)
				{
					Part->SetMaterial(Slot, Material);
				}
			}
		}
		Part->SetMobility(EComponentMobility::Movable);
		Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Part->SetCanEverAffectNavigation(false);
		Part->bCastDynamicShadow = true;
		if (!bModelled && !Kind->SizeCm.IsNearlyZero())
		{
			// The engine's cube is a metre across, so a size in cm is the scale over a hundred.
			const FVector Bounds = Mesh->GetBounds().BoxExtent * 2.f;
			Part->SetWorldScale3D(FVector(
				Bounds.X > KINDA_SMALL_NUMBER ? Kind->SizeCm.X / Bounds.X : 1.f,
				Bounds.Y > KINDA_SMALL_NUMBER ? Kind->SizeCm.Y / Bounds.Y : 1.f,
				Bounds.Z > KINDA_SMALL_NUMBER ? Kind->SizeCm.Z / Bounds.Z : 1.f));
		}
		Part->RegisterComponent();
		Part->AttachToComponent(GetRootComponent(), FAttachmentTransformRules::KeepWorldTransform);
		PropParts.Add(Part);
		PropModelled.Add(bModelled);
	}

	SpawnFrame = GFrameCounter;
	SpawnSeconds = World->GetTimeSeconds();
	FigureBones.Reset();
	for (AActor* Person : Figures)
	{
		FFigureBones& Bones = FigureBones.AddDefaulted_GetRef();
		Bones.Figure = Person;
		TInlineComponentArray<USkeletalMeshComponent*> Meshes;
		Person->GetComponents(Meshes);
		for (USkeletalMeshComponent* Mesh : Meshes)
		{
			if (Mesh != nullptr)
			{
				Bones.Meshes.Add(Mesh);
				Bones.PosedLOD.Add(INDEX_NONE);
				// This stage decides each frame whether the mesh evaluates, so it ticks before the mesh...
				Mesh->PrimaryComponentTick.AddPrerequisite(this, PrimaryActorTick);
			}
		}
		// ...and after the figure's LOD sync, which picks the frame's LOD for every mesh it syncs.
		if (ULODSyncComponent* Sync = Person->FindComponentByClass<ULODSyncComponent>())
		{
			PrimaryActorTick.AddPrerequisite(Sync, Sync->PrimaryComponentTick);
		}
	}
	UpdateProps(0.f);
}

void AWTAWaxStageActor::SetActing(bool bWake)
{
	if (bActing == bWake)
	{
		return;
	}
	bActing = bWake;
	for (FFigurePlay& Play : Plays)
	{
		if (UWTAWaxAnimInstance* Anim = Play.Anim.Get())
		{
			// Waking carries on from the frame the figure stopped at, so nothing jumps either way.
			Anim->Hold(!bWake);
		}
	}
	if (bWake)
	{
		for (AActor* Person : Figures)
		{
			UWTAPeopleLibrary::Thaw(Person);
		}
		for (FFigureBones& Bones : FigureBones)
		{
			Bones.bFrozen = false;
			Bones.EvalFrames = 0;
		}
	}
	else
	{
		// The settle clock starts again, so a figure only freezes once it has evaluated its held pose.
		SpawnFrame = GFrameCounter;
		SpawnSeconds = GetWorld() != nullptr ? GetWorld()->GetTimeSeconds() : 0.0;
	}
}

void AWTAWaxStageActor::UpdateBeats(float DeltaSeconds)
{
	float LoopSeconds = Scene.LoopSeconds;
	if (LoopSeconds <= 0.f)
	{
		LoopSeconds = 14.f;
	}
	ActTime += DeltaSeconds;
	if (ActTime >= LoopSeconds)
	{
		ActTime = FMath::Fmod(ActTime, LoopSeconds);
	}

	for (FFigurePlay& Play : Plays)
	{
		AActor* Person = Play.Figure.Get();
		if (!IsValid(Person) || !Scene.Figures.IsValidIndex(Play.FigureIndex))
		{
			continue;
		}
		const TArray<FWTAWaxBeat>& Beats = Scene.Figures[Play.FigureIndex].Beats;
		if (Beats.Num() > 0)
		{
			// The beat running now is the last one whose time has passed; before the first, the last beat of the
			// loop is still going, which is what makes the loop join without a seam.
			int32 Want = Beats.Num() - 1;
			for (int32 i = 0; i < Beats.Num(); ++i)
			{
				if (Beats[i].Time <= ActTime)
				{
					Want = i;
				}
			}
			if (Want != Play.BeatIndex)
			{
				const FWTAWaxBeat& Beat = Beats[Want];
				const FName WasAction = Beats.IsValidIndex(Play.BeatIndex) ? Beats[Play.BeatIndex].Action : NAME_None;
				const float Blend = FMath::Max(0.08f, Beat.Blend);
				if (Beat.Action != WasAction)
				{
					if (UAnimSequence* Clip = LoadAction(Beat.Action))
					{
						if (UWTAWaxAnimInstance* Anim = Play.Anim.Get())
						{
							// Each figure enters a clip at its own phase, so two people doing the same thing are
							// never in lockstep.
							const float Phase = UWTAPeopleLibrary::PersonPhase(Scene.Figures[Play.FigureIndex].Person) * Clip->GetPlayLength();
							Anim->PlayClip(Clip, true, FMath::Max(0.05f, Beat.Rate), Phase, Blend);
						}
					}
				}
				// A beat that only turns the figure (same clip, new yaw) just turns it.
				Play.YawFrom = Play.YawTo;
				Play.YawTo = Beat.Yaw;
				Play.LiftFrom = Play.LiftTo;
				Play.LiftTo = Beat.Lift;
				Play.TurnSeconds = 0.f;
				Play.TurnLength = Blend;
				Play.BeatIndex = Want;
			}
		}

		if (Play.TurnSeconds < Play.TurnLength)
		{
			Play.TurnSeconds = FMath::Min(Play.TurnLength, Play.TurnSeconds + DeltaSeconds);
		}
		const float Alpha = Play.TurnLength > 0.f ? FMath::SmoothStep(0.f, 1.f, Play.TurnSeconds / Play.TurnLength) : 1.f;
		const float Yaw = FMath::Lerp(Play.YawFrom, Play.YawTo, Alpha);
		const float Lift = FMath::Lerp(Play.LiftFrom, Play.LiftTo, Alpha);
		Person->SetActorRotation(FRotator(0.f, Play.BaseYaw + Yaw, 0.f));
		Person->SetActorLocation(Play.Feet + FVector(0.f, 0.f, Lift));
	}
}

const AWTAWaxStageActor::FFigurePlay* AWTAWaxStageActor::FindPlay(FName Figure) const
{
	// The key names the figure by the short name the scene uses ("teen"), which is the row person id with the
	// scene id taken off the front.
	const FString Short = FString::Printf(TEXT("%s-%s"), *SceneId.ToString(), *Figure.ToString());
	for (const FFigurePlay& Play : Plays)
	{
		if (!Scene.Figures.IsValidIndex(Play.FigureIndex))
		{
			continue;
		}
		const FString Person = Scene.Figures[Play.FigureIndex].Person.ToString();
		if (Person == Short || Person == Figure.ToString())
		{
			return &Play;
		}
	}
	return nullptr;
}

bool AWTAWaxStageActor::HandPalm(const FWTAWaxPropKey& Key, FTransform& OutPalm, bool& bOutRight) const
{
	static const FName HandL(TEXT("hand_l"));
	static const FName HandR(TEXT("hand_r"));
	if (Key.Socket != HandL && Key.Socket != HandR)
	{
		return false;
	}
	const FFigurePlay* Play = FindPlay(Key.Figure);
	AActor* Figure = Play != nullptr ? Play->Figure.Get() : nullptr;
	const USkeletalMeshComponent* Body = IsValid(Figure) ? UWTAPeopleLibrary::FindBody(Figure) : nullptr;
	bOutRight = Key.Socket == HandR;
	return Body != nullptr && PalmFrame(Body, bOutRight, OutPalm);
}

bool AWTAWaxStageActor::PropKeyTransform(const FWTAWaxPropKey& Key, FName Kind, bool bModelled, FTransform& Out, float SwingRad) const
{
	if (Key.Figure.IsNone() || Key.Figure.ToString().IsEmpty())
	{
		// Standing in the stage's own frame (the web's carries rest where the web left them).
		const FRotator StageRotation(0.f, Scene.StageYaw, 0.f);
		Out = FTransform(FRotator(StageRotation.Pitch + Key.Rotation.Pitch, StageRotation.Yaw + Key.Rotation.Yaw, StageRotation.Roll + Key.Rotation.Roll),
			Scene.StageLocation + StageRotation.RotateVector(Key.Offset));
		return true;
	}
	// Riding a figure.
	const FFigurePlay* Play = FindPlay(Key.Figure);
	AActor* Figure = Play != nullptr ? Play->Figure.Get() : nullptr;
	USkeletalMeshComponent* Body = IsValid(Figure) ? UWTAPeopleLibrary::FindBody(Figure) : nullptr;
	if (Body == nullptr)
	{
		return false;
	}
	const FName Bone = WaxSocketBone(Key.Socket);
	if (Body->GetBoneIndex(Bone) == INDEX_NONE)
	{
		return false;
	}
	FTransform Frame = Body->GetSocketTransform(Bone, RTS_World);
	// A hand's prop sits in the palm, in the prop's own frame (+X along the fingers, +Y out of the palm), and
	// its kind says how; one on the head or chest sits square to the person, because the skull and spine
	// bones point whichever way the rig author chose and a headset has to face forward.
	static const FName HandL(TEXT("hand_l"));
	static const FName HandR(TEXT("hand_r"));
	static const FName Head(TEXT("head"));
	if (Key.Socket == HandL || Key.Socket == HandR)
	{
		const bool bRight = Key.Socket == HandR;
		FTransform Palm;
		if (PalmFrame(Body, bRight, Palm))
		{
			Frame = Palm;
		}
		if (const FWaxGrip* Grip = WaxGrip(Kind))
		{
			Frame = WaxHeldTransform(*Grip, Frame, bRight, SwingRad);
		}
	}
	else
	{
		// The MetaHuman Blueprint faces +Y, which FigureYawOffset turns to the actor's +X: the person looks
		// along the actor's yaw less that offset.
		Frame = FTransform(FRotator(0.f, Figure->GetActorRotation().Yaw - FigureYawOffset, 0.f), Frame.GetLocation());
		if (bModelled && Key.Socket == Head)
		{
			// the modelled headset is centred on its visor: the gasket meets the face 8.5 cm ahead of the head bone
			static const FName Headset(TEXT("headset"));
			if (Kind == Headset)
			{
				Frame = FTransform(FRotator::ZeroRotator, FVector(14.5f, 0.f, 4.f)) * Frame;
			}
		}
	}
	Out = FTransform(Key.Rotation, Key.Offset) * Frame;
	return true;
}

bool AWTAWaxStageActor::PropInHand(int32 Index, FVector& OutProp, FVector& OutWrist, FVector& OutFigure, float& OutGrip, FName& OutSocket, FTransform& OutPalm) const
{
	static const FName HandL(TEXT("hand_l"));
	static const FName HandR(TEXT("hand_r"));
	if (!Scene.Props.IsValidIndex(Index) || !PropParts.IsValidIndex(Index) || PropParts[Index] == nullptr)
	{
		return false;
	}
	const FWTAWaxProp& Prop = Scene.Props[Index];
	int32 Resting = INDEX_NONE, Arriving = INDEX_NONE;
	float Alpha = 0.f;
	PropKeysAt(Prop, Resting, Arriving, Alpha);
	if (!Prop.Keys.IsValidIndex(Resting) || Arriving != INDEX_NONE)
	{
		return false;                            // not there yet, or on its way somewhere else
	}
	const FWTAWaxPropKey& Key = Prop.Keys[Resting];
	if (Key.Socket != HandL && Key.Socket != HandR)
	{
		return false;
	}
	const FFigurePlay* Play = FindPlay(Key.Figure);
	AActor* Figure = Play != nullptr ? Play->Figure.Get() : nullptr;
	const USkeletalMeshComponent* Body = IsValid(Figure) ? UWTAPeopleLibrary::FindBody(Figure) : nullptr;
	if (Body == nullptr)
	{
		return false;
	}
	OutWrist = Body->GetSocketLocation(Key.Socket);
	OutFigure = Figure->GetActorLocation();
	if (!PalmFrame(Body, Key.Socket == HandR, OutPalm))
	{
		OutPalm = Body->GetSocketTransform(Key.Socket, RTS_World);
	}
	// where the prop meets the hand: a hanging prop's tube, otherwise the point of it the palm frame holds
	OutProp = PropParts[Index]->GetComponentLocation();
	if (const FWaxGrip* Grip = WaxGrip(Prop.Kind))
	{
		FVector Contact = Grip->bHang ? Grip->Tube : Grip->Hold.GetLocation();
		if (Key.Socket != HandR)
		{
			Contact.Z = -Contact.Z;
		}
		OutProp = OutPalm.TransformPosition(Contact);
	}
	OutGrip = Play->Anim.IsValid() ? Play->Anim->GetGrip(Key.Socket == HandR) : 0.f;
	OutSocket = Key.Socket;
	return true;
}

FString AWTAWaxStageActor::DescribeHold(int32 Index) const
{
	static const FName HandR(TEXT("hand_r"));
	FVector Prop, Wrist, Figure;
	float Grip = 0.f;
	FName Socket;
	FTransform Palm;
	if (!PropInHand(Index, Prop, Wrist, Figure, Grip, Socket, Palm) || !Scene.Props.IsValidIndex(Index) || !PropParts.IsValidIndex(Index) || PropParts[Index] == nullptr)
	{
		return FString();
	}
	const FWTAWaxPropKey* Key = nullptr;
	{
		int32 Resting = INDEX_NONE, Arriving = INDEX_NONE;
		float Alpha = 0.f;
		PropKeysAt(Scene.Props[Index], Resting, Arriving, Alpha);
		Key = Scene.Props[Index].Keys.IsValidIndex(Resting) ? &Scene.Props[Index].Keys[Resting] : nullptr;
	}
	const FFigurePlay* Play = Key != nullptr ? FindPlay(Key->Figure) : nullptr;
	AActor* Actor = Play != nullptr ? Play->Figure.Get() : nullptr;
	const USkeletalMeshComponent* Body = IsValid(Actor) ? UWTAPeopleLibrary::FindBody(Actor) : nullptr;
	auto InPalm = [&Palm](const FVector& World) { return Palm.InverseTransformPosition(World); };
	auto Fmt = [](const FVector& V) { return FString::Printf(TEXT("(%.1f, %.1f, %.1f)"), V.X, V.Y, V.Z); };
	const FTransform PropWorld = PropParts[Index]->GetComponentTransform();
	FTransform Expected;
	const float Swing = PropSwing.IsValidIndex(Index) ? PropSwing[Index].Angle : 0.f;
	const bool bExpected = Key != nullptr && PropKeyTransform(*Key, Scene.Props[Index].Kind, PropModelled.IsValidIndex(Index) && PropModelled[Index], Expected, Swing);
	FString Out = FString::Printf(TEXT("%s %s grip %.2f: prop origin %s X %s Y %s, placed %.1f cm from where the hand is now; "), *Scene.Props[Index].Kind.ToString(), *Socket.ToString(), Grip,
		*Fmt(InPalm(PropWorld.GetLocation())), *Fmt(Palm.InverseTransformVectorNoScale(PropWorld.GetUnitAxis(EAxis::X))), *Fmt(Palm.InverseTransformVectorNoScale(PropWorld.GetUnitAxis(EAxis::Y))),
		bExpected ? FVector::Dist(PropWorld.GetLocation(), Expected.GetLocation()) : -1.f);
	if (Body != nullptr && Play->Anim.IsValid())
	{
		// the arm: how far it is given to its target and how far the hand bone still is from it; the head's look
		const bool bRight = Socket == HandR;
		const FWTAHandTarget& Target = Play->Anim->GetHandTarget(bRight);
		if (Target.Weight > 0.f)
		{
			const FTransform TargetWorld = Target.Hand * Body->GetComponentTransform();
			const FTransform HandWorld = Body->GetSocketTransform(Socket, RTS_World);
			Out += FString::Printf(TEXT("arm ik %.2f, hand %.1f cm and %.0f deg from its target; "), Play->Anim->GetEasedIK(bRight),
				FVector::Dist(HandWorld.GetLocation(), TargetWorld.GetLocation()), FMath::RadiansToDegrees(HandWorld.GetRotation().AngularDistance(TargetWorld.GetRotation())));
		}
		else
		{
			Out += TEXT("arm from the clip; ");
		}
		static const FName HeadBone(TEXT("head"));
		if (Play->Anim->GetLookWeight() > 0.f && Body->GetBoneIndex(HeadBone) != INDEX_NONE)
		{
			const FVector LookWorld = Body->GetComponentTransform().TransformPosition(Play->Anim->GetLookTarget());
			const FVector Eyes = Body->GetSocketLocation(HeadBone);
			Out += FString::Printf(TEXT("look %.2f at %s (%.0f cm from the head); "), Play->Anim->GetEasedLook(), *Fmt(InPalm(LookWorld)), FVector::Dist(Eyes, LookWorld));
		}
	}
	if (Body != nullptr)
	{
		const TCHAR* Side = Socket == HandR ? TEXT("r") : TEXT("l");
		for (const TCHAR* Finger : { TEXT("index"), TEXT("middle"), TEXT("thumb") })
		{
			Out += Finger;
			for (int32 j = 1; j <= 3; ++j)
			{
				const FName Bone(*FString::Printf(TEXT("%s_%02d_%s"), Finger, j, Side));
				if (Body->GetBoneIndex(Bone) != INDEX_NONE)
				{
					Out += TEXT(" ") + Fmt(InPalm(Body->GetSocketLocation(Bone)));
				}
			}
			Out += TEXT("; ");
		}
		Out += FString::Printf(TEXT("lod %d, %d bones in the pose"), Body->GetPredictedLODLevel(), Body->GetNumComponentSpaceTransforms());
	}
	return Out;
}

float AWTAWaxStageActor::PropSecondsBeforeLeaving(int32 Index) const
{
	if (!Scene.Props.IsValidIndex(Index) || Scene.Props[Index].Keys.Num() < 2)
	{
		return 1.e6f;
	}
	const FWTAWaxProp& Prop = Scene.Props[Index];
	int32 Resting = INDEX_NONE, Arriving = INDEX_NONE;
	float Alpha = 0.f;
	PropKeysAt(Prop, Resting, Arriving, Alpha);
	if (Arriving != INDEX_NONE)
	{
		return 0.f;
	}
	float LoopSeconds = Scene.LoopSeconds > 0.f ? Scene.LoopSeconds : 14.f;
	const int32 Next = (Resting + 1) % Prop.Keys.Num();
	float Leaves = Prop.Keys[Next].Time - FMath::Max(0.05f, Prop.Keys[Next].Blend);
	if (Leaves < ActTime)
	{
		Leaves += LoopSeconds;
	}
	return Leaves - ActTime;
}

void AWTAWaxStageActor::SetKeyGrip(const FWTAWaxPropKey& Key, FName Kind, float Scale) const
{
	static const FName HandL(TEXT("hand_l"));
	static const FName HandR(TEXT("hand_r"));
	static const FName Chest(TEXT("chest"));
	static const FName UpperL(TEXT("upperarm_l"));
	static const FName UpperR(TEXT("upperarm_r"));
	const bool bHand = Key.Socket == HandL || Key.Socket == HandR;
	if (!bHand && Key.Socket != Chest)
	{
		return;
	}
	const FFigurePlay* Play = FindPlay(Key.Figure);
	UWTAWaxAnimInstance* Anim = Play != nullptr ? Play->Anim.Get() : nullptr;
	AActor* Figure = Play != nullptr ? Play->Figure.Get() : nullptr;
	USkeletalMeshComponent* Body = IsValid(Figure) ? UWTAPeopleLibrary::FindBody(Figure) : nullptr;
	if (Anim == nullptr || Body == nullptr)
	{
		return;
	}
	const FWaxGrip* Grip = WaxGrip(Kind);
	const FTransform& Comp = Body->GetComponentTransform();
	FVector S, Forward, Right;
	const bool bFrame = WaxChestFrame(Body, Figure, FigureYawOffset, S, Forward, Right);

	// the arm: the hand bone to Hand (world), the elbow out and down from the shoulder, in component space
	auto AimArm = [&](bool bRight, const FTransform& Hand)
	{
		const FName Shoulder = bRight ? UpperR : UpperL;
		const FVector Joint = Body->GetBoneIndex(Shoulder) != INDEX_NONE ? Body->GetSocketLocation(Shoulder) : S;
		const FVector Elbow = Joint - FVector::UpVector * 45.f + Right * (bRight ? 20.f : -20.f) - Forward * 15.f;
		Anim->SetHandTarget(bRight, Scale, Hand.GetRelativeTransform(Comp), Comp.InverseTransformPosition(Elbow));
	};

	if (bHand)
	{
		const bool bRight = Key.Socket == HandR;
		if (Grip == nullptr)
		{
			static const FWTAHandPose Open;
			Anim->SetGrip(bRight, 0.f, Open);
			return;
		}
		FWTAHandPose Pose = Grip->Pose;
		WaxShapeFor(*Grip, bRight, Pose);
		Anim->SetGrip(bRight, Scale, Pose);
		if (Grip->bArm && bFrame)
		{
			const FTransform Palm = WaxStancePalm(*Grip, bRight, S, Forward, Right, WaxEyes(Body, S, Forward));
			AimArm(bRight, WaxHandFromPalm(Palm, bRight));
			if (Grip->bLook)
			{
				const FVector Look = WaxHeldTransform(*Grip, Palm, bRight, 0.f).TransformPosition(Grip->LookPoint);
				Anim->SetLookAt(Scale, Comp.InverseTransformPosition(Look));
			}
		}
		return;
	}

	// At the chest, carried in both hands: a hand flat on each side of the box, the fingers forward and a
	// little down, the thumbs up its sides, each palm 2.6 cm (the fingers' flesh) out from the face.
	FTransform BoxWorld;
	if (Grip == nullptr || !Grip->bTwoHands || !bFrame || !PropKeyTransform(Key, Kind, true, BoxWorld))
	{
		return;
	}
	for (int32 Hand = 0; Hand < 2; ++Hand)
	{
		const bool bRight = Hand == 1;
		const FVector Toward = Right * (bRight ? 1.f : -1.f);
		// the box's level face that looks most toward this hand's side
		FVector Outward = FVector::ZeroVector;
		float Half = 0.f;
		float Best = -2.f;
		for (int32 Axis = 0; Axis < 2; ++Axis)
		{
			for (float Sign = -1.f; Sign <= 1.f; Sign += 2.f)
			{
				const FVector Dir = BoxWorld.GetUnitAxis(Axis == 0 ? EAxis::X : EAxis::Y) * Sign;
				const float Score = FVector::DotProduct(Dir, Toward);
				if (Score > Best)
				{
					Best = Score;
					Outward = Dir;
					Half = Axis == 0 ? Grip->BoxHalf.X : Grip->BoxHalf.Y;
				}
			}
		}
		const FVector O = BoxWorld.GetLocation() + Outward * (Half + 2.6f) - FVector::UpVector * 4.f;
		const FVector N = -Outward;
		FVector F = Forward * FMath::Cos(FMath::DegreesToRadians(30.f)) - FVector::UpVector * FMath::Sin(FMath::DegreesToRadians(30.f));
		F -= N * FVector::DotProduct(F, N);
		if (!F.Normalize(KINDA_SMALL_NUMBER))
		{
			F = -FVector::UpVector;
		}
		const FTransform Palm(FMatrix(F, N, FVector::CrossProduct(F, N), O));
		FWTAHandPose Pose;
		WaxFlatFingers(Pose);
		Pose.bContact = true;
		Pose.Shape.Kind = FWTAHoldShape::Box;
		Pose.Shape.Frame = FTransform(FQuat::Identity, Grip->BoxCentre) * BoxWorld.GetRelativeTransform(Palm);
		Pose.Shape.Half = Grip->BoxHalf;
		Anim->SetGrip(bRight, Scale, Pose);
		AimArm(bRight, WaxHandFromPalm(Palm, bRight));
	}
}

void AWTAWaxStageActor::PropKeysAt(const FWTAWaxProp& Prop, int32& Resting, int32& Arriving, float& Alpha) const
{
	float LoopSeconds = Scene.LoopSeconds;
	if (LoopSeconds <= 0.f)
	{
		LoopSeconds = 14.f;
	}
	// Where it is sitting: the last key whose time has passed (before the first, the last key of the loop).
	Resting = Prop.Keys.Num() - 1;
	for (int32 k = 0; k < Prop.Keys.Num(); ++k)
	{
		if (Prop.Keys[k].Time <= ActTime)
		{
			Resting = k;
		}
	}
	// It travels to a key over that key's Blend seconds, arriving exactly on the key's time.
	Arriving = INDEX_NONE;
	Alpha = 0.f;
	for (int32 k = 0; k < Prop.Keys.Num() && Arriving == INDEX_NONE; ++k)
	{
		const float Travel = FMath::Max(0.05f, Prop.Keys[k].Blend);
		const float Leaves = Prop.Keys[k].Time - Travel;
		float Since = ActTime - Leaves;
		if (Leaves < 0.f && ActTime > Prop.Keys[k].Time)
		{
			// The window straddles the loop's join.
			Since = ActTime - (Leaves + LoopSeconds);
		}
		if (Since >= 0.f && Since < Travel && k != Resting)
		{
			Arriving = k;
			Alpha = Since / Travel;
		}
	}
}

void AWTAWaxStageActor::PlaceProps(float DeltaSeconds)
{
	if (bHasScene && bActing && Plays.Num() > 0)
	{
		UpdateProps(DeltaSeconds);
	}
}

void AWTAWaxStageActor::UpdateProps(float DeltaSeconds)
{
	// Every hand opens, every arm and head goes back to the clip, unless a prop below claims it this frame.
	for (const FFigurePlay& Play : Plays)
	{
		if (UWTAWaxAnimInstance* Anim = Play.Anim.Get())
		{
			static const FWTAHandPose Open;
			Anim->SetGrip(false, 0.f, Open);
			Anim->SetGrip(true, 0.f, Open);
			Anim->SetHandTarget(false, 0.f, FTransform::Identity, FVector::ZeroVector);
			Anim->SetHandTarget(true, 0.f, FTransform::Identity, FVector::ZeroVector);
			Anim->SetLookAt(0.f, FVector::ZeroVector);
		}
	}
	if (PropSwing.Num() != Scene.Props.Num())
	{
		PropSwing.SetNum(Scene.Props.Num());
	}
	for (int32 i = 0; i < PropParts.Num() && i < Scene.Props.Num(); ++i)
	{
		UStaticMeshComponent* Part = PropParts[i];
		const FWTAWaxProp& Prop = Scene.Props[i];
		if (Part == nullptr || Prop.Keys.Num() == 0)
		{
			continue;
		}
		const bool bModelled = PropModelled.IsValidIndex(i) && PropModelled[i];
		const FWaxPropKind* Kind = bModelled ? nullptr : WaxPropKind(Prop.Kind);

		int32 Resting = INDEX_NONE, Arriving = INDEX_NONE;
		float Alpha = 0.f;
		PropKeysAt(Prop, Resting, Arriving, Alpha);

		// A prop hanging from a hand swings on its strap: once a frame, with the bones where they are after
		// the clip (the late tick), its pendulum takes the hand's motion; a new key starts it afresh.
		FWaxSwing& Swing = PropSwing[i];
		{
			const FWaxGrip* Grip = WaxGrip(Prop.Kind);
			FTransform Palm;
			bool bRight = false;
			if (Grip != nullptr && Grip->bHang && HandPalm(Prop.Keys[Resting], Palm, bRight))
			{
				if (Swing.Key != Resting)
				{
					Swing = FWaxSwing();
					Swing.Key = Resting;
				}
				FVector Tube = Grip->Tube;
				if (!bRight) { Tube.Z = -Tube.Z; }
				WaxSwingStep(Swing, Palm.TransformPosition(Tube), Palm.GetUnitAxis(EAxis::Z) * (bRight ? 1.f : -1.f), DeltaSeconds);
			}
			else if (Swing.Key != INDEX_NONE)
			{
				Swing = FWaxSwing();
			}
		}

		FTransform Where;
		if (Arriving == INDEX_NONE)
		{
			if (!PropKeyTransform(Prop.Keys[Resting], Prop.Kind, bModelled, Where, Swing.Angle))
			{
				continue;
			}
			SetKeyGrip(Prop.Keys[Resting], Prop.Kind, 1.f);
		}
		else
		{
			FTransform From;
			FTransform To;
			if (!PropKeyTransform(Prop.Keys[Resting], Prop.Kind, bModelled, From, Swing.Angle) || !PropKeyTransform(Prop.Keys[Arriving], Prop.Kind, bModelled, To))
			{
				continue;
			}
			// A hand-over: the prop leaves one pair of hands and arrives in the other without snapping; the
			// giving hand opens as the taking one closes.
			const float Smooth = FMath::SmoothStep(0.f, 1.f, Alpha);
			Where.Blend(From, To, Smooth);
			SetKeyGrip(Prop.Keys[Resting], Prop.Kind, 1.f - Smooth);
			SetKeyGrip(Prop.Keys[Arriving], Prop.Kind, Smooth);
		}
		if (Kind != nullptr)
		{
			// a stand-in block: its kind's offset puts it over the eyes or in front of the chest
			static const FName HandL(TEXT("hand_l"));
			static const FName HandR(TEXT("hand_r"));
			const FName Socket = Prop.Keys[Arriving == INDEX_NONE ? Resting : Arriving].Socket;
			if (Socket != HandL && Socket != HandR)
			{
				Where = FTransform(Kind->Rotation, Kind->Offset) * Where;
			}
		}
		Part->SetWorldLocationAndRotation(Where.GetLocation(), Where.GetRotation());
	}
}

void AWTAWaxStageActor::UpdateFigureBones()
{
	const UWorld* World = GetWorld();
	if (World == nullptr || FigureBones.Num() == 0)
	{
		return;
	}
	if (bActing)
	{
		// Acting: every mesh evaluates every frame, so there is nothing to freeze or repose.
		return;
	}
	// A slow start (first launch: shaders compiling, meshes streaming) can fit only a frame or two into the settle
	// time; a face frozen before it copied the body's head and neck keeps its reference pose under a posed head and
	// sags. So a figure freezes after SettleSeconds and MinFramesBeforeFreeze frames, once its face sits on its
	// body, or after MaxSecondsBeforeFreeze whatever the face says.
	const double Age = World->GetTimeSeconds() - SpawnSeconds;
	const bool bSettleTimeOver = Age >= SettleSeconds && GFrameCounter - SpawnFrame >= static_cast<uint64>(MinFramesBeforeFreeze);
	const bool bOutOfTime = Age > MaxSecondsBeforeFreeze;
	for (FFigureBones& Bones : FigureBones)
	{
		AActor* Figure = Bones.Figure.Get();
		if (!IsValid(Figure))
		{
			continue;
		}
		if (Bones.bFrozen)
		{
			// About to be drawn at a LOD its bones were not evaluated at: evaluate this frame (the meshes tick after
			// this stage), and a couple more, then freeze again.
			bool bLODChange = false;
			for (int32 i = 0; i < Bones.Meshes.Num() && !bLODChange; ++i)
			{
				const USkeletalMeshComponent* Mesh = Bones.Meshes[i].Get();
				bLODChange = Mesh != nullptr && UWTAPeopleLibrary::NextLOD(Mesh) != Bones.PosedLOD[i];
			}
			if (bLODChange)
			{
				UWTAPeopleLibrary::Thaw(Figure);
				Bones.bFrozen = false;
				Bones.EvalFrames = 0;
				++NumReposes;
			}
			continue;
		}

		// Evaluating: the frame before this one posed every mesh at its LOD of that frame (GetPredictedLODLevel,
		// which this frame's tick has not updated yet).
		++Bones.EvalFrames;
		float Gap = 0.f;
		const bool bFaceOn = UWTAPeopleLibrary::IsFaceOnBody(Figure, Gap);
		const bool bReady = Bones.bEverFrozen ? (Bones.EvalFrames >= 2 && (bFaceOn || Bones.EvalFrames > 30))
			: ((bSettleTimeOver && bFaceOn) || bOutOfTime);
		if (!bReady)
		{
			continue;
		}
		// Freeze only when this frame keeps every mesh at the LOD it was just posed at.
		bool bSteady = true;
		for (int32 i = 0; i < Bones.Meshes.Num() && bSteady; ++i)
		{
			const USkeletalMeshComponent* Mesh = Bones.Meshes[i].Get();
			bSteady = Mesh == nullptr || UWTAPeopleLibrary::NextLOD(Mesh) == Mesh->GetPredictedLODLevel();
		}
		if (!bSteady)
		{
			continue;
		}
		for (int32 i = 0; i < Bones.Meshes.Num(); ++i)
		{
			const USkeletalMeshComponent* Mesh = Bones.Meshes[i].Get();
			Bones.PosedLOD[i] = Mesh != nullptr ? Mesh->GetPredictedLODLevel() : INDEX_NONE;
		}
		if (!bFaceOn)
		{
			UE_LOG(LogWTA, Warning, TEXT("%s: %s froze with its face %.1f cm off its head"), *GetName(), *Figure->GetName(), Gap);
		}
		UWTAPeopleLibrary::Freeze(Figure);
		Bones.bFrozen = true;
		Bones.bEverFrozen = true;
	}
}

FString AWTAWaxStageActor::DescribeActing() const
{
	FString Out = FString::Printf(TEXT("%s %s t=%.1f"), *SceneId.ToString(), bActing ? TEXT("acting") : TEXT("wax"), ActTime);
	for (const FFigurePlay& Play : Plays)
	{
		if (!Scene.Figures.IsValidIndex(Play.FigureIndex))
		{
			continue;
		}
		const UWTAWaxAnimInstance* Anim = Play.Anim.Get();
		const UAnimSequence* Clip = Anim != nullptr ? Anim->GetClip() : nullptr;
		Out += FString::Printf(TEXT("; %s %s %.1fs%s"), *Scene.Figures[Play.FigureIndex].Person.ToString(),
			Clip != nullptr ? *Clip->GetName() : TEXT("(no clip)"), Anim != nullptr ? Anim->GetClipTime() : 0.f,
			Anim != nullptr && Anim->IsBlending() ? TEXT(" blending") : TEXT(""));
	}
	for (int32 i = 0; i < PropParts.Num() && i < Scene.Props.Num(); ++i)
	{
		const FWTAWaxProp& Prop = Scene.Props[i];
		if (PropParts[i] == nullptr)
		{
			Out += FString::Printf(TEXT("; %s NO MESH"), *Prop.Id.ToString());
			continue;
		}
		int32 Resting = Prop.Keys.Num() - 1;
		for (int32 k = 0; k < Prop.Keys.Num(); ++k)
		{
			if (Prop.Keys[k].Time <= ActTime)
			{
				Resting = k;
			}
		}
		const FVector At = PropParts[i]->GetComponentLocation();
		const FVector Size = PropParts[i]->Bounds.BoxExtent * 2.f;
		Out += FString::Printf(TEXT("; %s key %d %s %s at %s %.0fx%.0fx%.0f cm%s"), *Prop.Id.ToString(), Resting,
			Prop.Keys.IsValidIndex(Resting) ? *Prop.Keys[Resting].Figure.ToString() : TEXT("-"),
			Prop.Keys.IsValidIndex(Resting) ? *Prop.Keys[Resting].Socket.ToString() : TEXT("-"),
			*At.ToCompactString(), Size.X, Size.Y, Size.Z,
			PropParts[i]->IsVisible() ? TEXT("") : TEXT(" HIDDEN"));
	}
	return Out;
}

void AWTAWaxStageActor::NotifyActorBeginOverlap(AActor* OtherActor)
{
	Super::NotifyActorBeginOverlap(OtherActor);

	const APawn* Pawn = Cast<APawn>(OtherActor);
	if (Pawn == nullptr || !Pawn->IsPlayerControlled())
	{
		return;
	}

	// A fresh caption loop every visit, like the web: the scene wakes when you walk up to it.
	bPlayerInside = true;
	bCredited = false;
	PlayTime = 0.f;
	WatchSeconds = 0.f;
	LineIndex = -1;

	// Walking up to a scene shows its museum plaque; E opens the full story.
	if (bHasScene)
	{
		if (AWTAPlayerController* PC = WaxFindController(this))
		{
			PC->SetStageStory(Scene.ItemId.IsNone() ? SceneId : Scene.ItemId, true);
		}
	}
}

void AWTAWaxStageActor::NotifyActorEndOverlap(AActor* OtherActor)
{
	Super::NotifyActorEndOverlap(OtherActor);

	const APawn* Pawn = Cast<APawn>(OtherActor);
	if (Pawn == nullptr || !Pawn->IsPlayerControlled())
	{
		return;
	}

	bPlayerInside = false;
	LineIndex = -1;
	if (AWTAPlayerController* PC = WaxFindController(this))
	{
		PC->ShowCaption(FText::GetEmpty());
		if (bHasScene)
		{
			PC->SetStageStory(Scene.ItemId.IsNone() ? SceneId : Scene.ItemId, false);
		}
	}
}

void AWTAWaxStageActor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// The scene comes to life as the player walks up the aisle toward it, and is wax again once they are well
	// past: the slack keeps it from flickering on the boundary.
	if (bHasScene && Plays.Num() > 0)
	{
		const APawn* Pawn = UGameplayStatics::GetPlayerPawn(this, 0);
		if (Pawn != nullptr)
		{
			const float Distance = static_cast<float>(FVector::Dist(Pawn->GetActorLocation(), Scene.StageLocation));
			SetActing(bPlayerInside || Distance <= (bActing ? WakeDistance + SleepDistanceSlack : WakeDistance));
		}
		if (bActing)
		{
			UpdateBeats(DeltaSeconds);
			UpdateProps(0.f);
		}
	}

	UpdateFigureBones();

	if (!bPlayerInside || !bHasScene)
	{
		bWasActive = false;
		return;
	}

	// Scenes face each other across the aisle, so the player can stand in two triggers at once: only the scene
	// the camera faces speaks, and it starts its narration from the first line when the player turns to it.
	const AWTAPlayerController* Watcher = WaxFindController(this);
	const FName MyStory = Scene.ItemId.IsNone() ? SceneId : Scene.ItemId;
	if (Watcher != nullptr && Watcher->GetActiveStageStory() != MyStory)
	{
		bWasActive = false;
		return;
	}
	if (!bWasActive)
	{
		bWasActive = true;
		PlayTime = 0.f;
		LineIndex = -1;
	}

	PlayTime += DeltaSeconds;
	WatchSeconds += DeltaSeconds;

	// Loop length: the row's LoopSeconds, else a little past the last line.
	float LoopSeconds = Scene.LoopSeconds;
	if (LoopSeconds <= 0.f)
	{
		LoopSeconds = 5.f;
		for (const FWTAWaxLine& Line : Scene.Lines)
		{
			LoopSeconds = FMath::Max(LoopSeconds, Line.Time + 5.f);
		}
	}
	if (PlayTime >= LoopSeconds)
	{
		PlayTime = FMath::Fmod(PlayTime, LoopSeconds);
		LineIndex = -1;
	}

	// The caption is the last line whose time has passed.
	int32 NewIndex = -1;
	for (int32 i = 0; i < Scene.Lines.Num(); ++i)
	{
		if (Scene.Lines[i].Time <= PlayTime)
		{
			NewIndex = i;
		}
	}
	if (NewIndex != LineIndex)
	{
		LineIndex = NewIndex;
		if (AWTAPlayerController* PC = WaxFindController(this))
		{
			PC->ShowCaption(LineIndex >= 0 ? Scene.Lines[LineIndex].Text : FText::GetEmpty());
		}
	}

	// Watching for a while counts the scene (Living Historian).
	if (!bCredited && WatchSeconds >= WatchSecondsForCredit)
	{
		bCredited = true;
		if (UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this))
		{
			Progress->NoteWaxScene(SceneId);
		}
	}
}
