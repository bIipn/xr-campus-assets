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
	 * How a modelled prop (bl/props.py) sits in a hand, and how far that hand closes on it. The prop's own frame
	 * is put in the palm: +X along the fingers, +Y out of the palm, +Z across it (see PalmFrame); Offset and
	 * Rotation move the prop in that frame. Fingers and Thumb are the grip (0..1) the hand holding it gets.
	 */
	struct FWaxGrip
	{
		FVector Offset;
		FRotator Rotation;
		float Fingers;
		float Thumb;
	};

	const FWaxGrip* WaxGrip(FName Kind)
	{
		static const TMap<FName, FWaxGrip> Grips = {
			// carried by its top strap: the headset (modelled for the head, +Z up) hangs below the palm, visor along the fingers
			{ FName(TEXT("headset")),   { FVector(3.f, 6.f, 0.f), FRotator(0.f, 0.f, 90.f), 0.6f, 0.5f } },
			{ FName(TEXT("tablet")),    { FVector::ZeroVector, FRotator::ZeroRotator, 0.35f, 0.6f } },
			{ FName(TEXT("clipboard")), { FVector::ZeroVector, FRotator::ZeroRotator, 0.35f, 0.6f } },
			{ FName(TEXT("book")),      { FVector::ZeroVector, FRotator::ZeroRotator, 0.30f, 0.5f } },
			{ FName(TEXT("phone")),     { FVector::ZeroVector, FRotator::ZeroRotator, 0.75f, 0.5f } },
			{ FName(TEXT("box")),       { FVector::ZeroVector, FRotator::ZeroRotator, 0.40f, 0.4f } },
		};
		return Grips.Find(Kind);
	}

	/**
	 * The palm, in world space, from the hand's own bones this frame: +X runs from the wrist toward the middle
	 * finger's knuckle, +Y is the palm's normal (square to the fingers, on the thumb's side of the hand's plane,
	 * where the thumb tip lies), +Z = X x Y across the palm, and the origin is 7 cm along the fingers from the
	 * wrist (mid-palm). One prop model fits both hands, since Z runs toward the little finger on the right hand
	 * and the index on the left. False when this LOD has no finger bones.
	 */
	bool PalmFrame(const USkeletalMeshComponent* Body, bool bRight, FTransform& Out)
	{
		const TCHAR* Side = bRight ? TEXT("r") : TEXT("l");
		const FName Wrist(*FString::Printf(TEXT("hand_%s"), Side));
		const FName Middle(*FString::Printf(TEXT("middle_01_%s"), Side));
		const FName Index(*FString::Printf(TEXT("index_01_%s"), Side));
		const FName Pinky(*FString::Printf(TEXT("pinky_01_%s"), Side));
		const FName Thumb(*FString::Printf(TEXT("thumb_03_%s"), Side));
		for (const FName& Bone : { Wrist, Middle, Index, Pinky, Thumb })
		{
			if (Body == nullptr || Body->GetBoneIndex(Bone) == INDEX_NONE)
			{
				return false;
			}
		}
		const FVector W0 = Body->GetSocketLocation(Wrist);
		const FVector F = (Body->GetSocketLocation(Middle) - W0).GetSafeNormal();
		const FVector Across = (Body->GetSocketLocation(Index) - Body->GetSocketLocation(Pinky)).GetSafeNormal();
		FVector N = FVector::CrossProduct(F, Across).GetSafeNormal();
		if (FVector::DotProduct(Body->GetSocketLocation(Thumb) - W0, N) < 0.f)
		{
			N = -N;
		}
		N = (N - F * FVector::DotProduct(N, F)).GetSafeNormal();
		if (F.IsNearlyZero() || N.IsNearlyZero())
		{
			return false;
		}
		Out = FTransform(FMatrix(F, N, FVector::CrossProduct(F, N), W0 + F * 7.f));
		return true;
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

AWTAWaxStageActor::AWTAWaxStageActor()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = true;

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
	UpdateProps();
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

bool AWTAWaxStageActor::PropKeyTransform(const FWTAWaxPropKey& Key, FName Kind, bool bModelled, FTransform& Out) const
{
	if (Key.Figure.IsNone() || Key.Figure.ToString().IsEmpty())
	{
		// Standing in the stage's own frame (the web's carries rest where the web left them).
		const FRotator StageRotation(0.f, Scene.StageYaw, 0.f);
		Out = FTransform(FRotator(StageRotation.Pitch + Key.Rotation.Pitch, StageRotation.Yaw + Key.Rotation.Yaw, StageRotation.Roll + Key.Rotation.Roll),
			Scene.StageLocation + StageRotation.RotateVector(Key.Offset));
		return true;
	}
	// Riding a figure: the key names the figure by the short name the scene uses ("teen"), which is the row
	// person id with the scene id taken off the front.
	for (const FFigurePlay& Play : Plays)
	{
		if (!Scene.Figures.IsValidIndex(Play.FigureIndex))
		{
			continue;
		}
		const FString Person = Scene.Figures[Play.FigureIndex].Person.ToString();
		const FString Short = FString::Printf(TEXT("%s-%s"), *SceneId.ToString(), *Key.Figure.ToString());
		if (Person != Short && Person != Key.Figure.ToString())
		{
			continue;
		}
		AActor* Figure = Play.Figure.Get();
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
			FTransform Palm;
			if (PalmFrame(Body, Key.Socket == HandR, Palm))
			{
				Frame = Palm;
			}
			if (const FWaxGrip* Grip = WaxGrip(Kind))
			{
				Frame = FTransform(Grip->Rotation, Grip->Offset) * Frame;
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
	return false;
}

bool AWTAWaxStageActor::PropInHand(int32 Index, FVector& OutProp, FVector& OutWrist, FVector& OutFigure, float& OutGrip, FName& OutSocket) const
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
	for (const FFigurePlay& Play : Plays)
	{
		if (!Scene.Figures.IsValidIndex(Play.FigureIndex))
		{
			continue;
		}
		const FString Person = Scene.Figures[Play.FigureIndex].Person.ToString();
		const FString Short = FString::Printf(TEXT("%s-%s"), *SceneId.ToString(), *Key.Figure.ToString());
		if (Person != Short && Person != Key.Figure.ToString())
		{
			continue;
		}
		AActor* Figure = Play.Figure.Get();
		const USkeletalMeshComponent* Body = IsValid(Figure) ? UWTAPeopleLibrary::FindBody(Figure) : nullptr;
		if (Body == nullptr)
		{
			return false;
		}
		OutProp = PropParts[Index]->GetComponentLocation();
		OutWrist = Body->GetSocketLocation(Key.Socket);
		OutFigure = Figure->GetActorLocation();
		OutGrip = Play.Anim.IsValid() ? Play.Anim->GetGrip(Key.Socket == HandR) : 0.f;
		OutSocket = Key.Socket;
		return true;
	}
	return false;
}

void AWTAWaxStageActor::SetKeyGrip(const FWTAWaxPropKey& Key, FName Kind, float Scale) const
{
	static const FName HandL(TEXT("hand_l"));
	static const FName HandR(TEXT("hand_r"));
	if (Key.Socket != HandL && Key.Socket != HandR)
	{
		return;
	}
	const FWaxGrip* Grip = WaxGrip(Kind);
	for (const FFigurePlay& Play : Plays)
	{
		if (!Scene.Figures.IsValidIndex(Play.FigureIndex))
		{
			continue;
		}
		const FString Person = Scene.Figures[Play.FigureIndex].Person.ToString();
		const FString Short = FString::Printf(TEXT("%s-%s"), *SceneId.ToString(), *Key.Figure.ToString());
		if (Person != Short && Person != Key.Figure.ToString())
		{
			continue;
		}
		if (UWTAWaxAnimInstance* Anim = Play.Anim.Get())
		{
			Anim->SetGrip(Key.Socket == HandR, Grip != nullptr ? Grip->Fingers * Scale : 0.f, Grip != nullptr ? Grip->Thumb * Scale : 0.f);
		}
		return;
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

void AWTAWaxStageActor::UpdateProps()
{
	// Every hand opens unless a prop below is in it this frame.
	for (const FFigurePlay& Play : Plays)
	{
		if (UWTAWaxAnimInstance* Anim = Play.Anim.Get())
		{
			Anim->SetGrip(false, 0.f, 0.f);
			Anim->SetGrip(true, 0.f, 0.f);
		}
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

		FTransform Where;
		if (Arriving == INDEX_NONE)
		{
			if (!PropKeyTransform(Prop.Keys[Resting], Prop.Kind, bModelled, Where))
			{
				continue;
			}
			SetKeyGrip(Prop.Keys[Resting], Prop.Kind, 1.f);
		}
		else
		{
			FTransform From;
			FTransform To;
			if (!PropKeyTransform(Prop.Keys[Resting], Prop.Kind, bModelled, From) || !PropKeyTransform(Prop.Keys[Arriving], Prop.Kind, bModelled, To))
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
			UpdateProps();
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
