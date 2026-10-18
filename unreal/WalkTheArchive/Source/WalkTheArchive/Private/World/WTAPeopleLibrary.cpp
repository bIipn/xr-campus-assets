// Walk the Archive - helpers for the MetaHuman people (staff and Wax Hall reenactors).

#include "World/WTAPeopleLibrary.h"
#include "Animation/AnimSequence.h"
#include "Animation/Skeleton.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Core/WTALog.h"
#include "GameFramework/Actor.h"
#include "LODSyncInterface.h"
#include "Misc/PackageName.h"
#include "ReferenceSkeleton.h"
#include "Rendering/SkeletalMeshLODRenderData.h"
#include "Rendering/SkeletalMeshRenderData.h"

const TCHAR* UWTAPeopleLibrary::DefaultIdlePath = TEXT("/Game/WTA/Characters/Common/Anims/AS_WTA_StandIdle.AS_WTA_StandIdle");

FSoftClassPath UWTAPeopleLibrary::MetaHumanClassPath(FName Person)
{
	if (Person.IsNone())
	{
		return FSoftClassPath();
	}
	const FString Id = Person.ToString();
	return FSoftClassPath(FString::Printf(TEXT("/Game/WTA/Characters/%s/BP_%s.BP_%s_C"), *Id, *Id, *Id));
}

UClass* UWTAPeopleLibrary::LoadMetaHumanClass(FName Person)
{
	const FSoftClassPath Path = MetaHumanClassPath(Person);
	if (Path.IsNull())
	{
		return nullptr;
	}
	// Check the package exists first so people that are not built yet do not spam "failed to load" warnings.
	if (!FPackageName::DoesPackageExist(Path.GetLongPackageName()))
	{
		UE_LOG(LogWTA, Verbose, TEXT("MetaHuman for '%s' not built yet (%s)"), *Person.ToString(), *Path.ToString());
		return nullptr;
	}
	UClass* Class = Path.TryLoadClass<AActor>();
	if (Class == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("MetaHuman for '%s' did not load (%s)"), *Person.ToString(), *Path.ToString());
	}
	return Class;
}

USkeletalMeshComponent* UWTAPeopleLibrary::FindBody(AActor* MetaHuman)
{
	if (MetaHuman == nullptr)
	{
		return nullptr;
	}
	TInlineComponentArray<USkeletalMeshComponent*> Meshes;
	MetaHuman->GetComponents(Meshes);
	for (USkeletalMeshComponent* Mesh : Meshes)
	{
		if (Mesh != nullptr && Mesh->GetFName() == TEXT("Body"))
		{
			return Mesh;
		}
	}
	// Fallback: the mesh the others follow (leader pose), else the first one.
	for (USkeletalMeshComponent* Mesh : Meshes)
	{
		if (Mesh == nullptr)
		{
			continue;
		}
		for (USkeletalMeshComponent* Other : Meshes)
		{
			if (Other != nullptr && Other != Mesh && Other->LeaderPoseComponent.Get() == Mesh)
			{
				return Mesh;
			}
		}
	}
	return Meshes.Num() > 0 ? Meshes[0] : nullptr;
}

USkeletalMeshComponent* UWTAPeopleLibrary::FindFace(AActor* MetaHuman)
{
	if (MetaHuman == nullptr)
	{
		return nullptr;
	}
	TInlineComponentArray<USkeletalMeshComponent*> Meshes;
	MetaHuman->GetComponents(Meshes);
	for (USkeletalMeshComponent* Mesh : Meshes)
	{
		if (Mesh != nullptr && Mesh->GetFName() == TEXT("Face"))
		{
			return Mesh;
		}
	}
	return nullptr;
}

bool UWTAPeopleLibrary::IsFaceOnBody(AActor* MetaHuman, float& OutGapCm)
{
	OutGapCm = 0.f;
	const USkeletalMeshComponent* Body = FindBody(MetaHuman);
	const USkeletalMeshComponent* Face = FindFace(MetaHuman);
	static const FName Head(TEXT("head"));
	if (Body == nullptr || Face == nullptr || Body->GetBoneIndex(Head) == INDEX_NONE || Face->GetBoneIndex(Head) == INDEX_NONE)
	{
		return true;
	}
	OutGapCm = static_cast<float>(FVector::Dist(Body->GetBoneLocation(Head), Face->GetBoneLocation(Head)));
	return OutGapCm < 0.5f;
}

bool UWTAPeopleLibrary::PlayPose(AActor* MetaHuman, UAnimSequence* Anim, bool bLoop, float StartTime)
{
	USkeletalMeshComponent* Body = FindBody(MetaHuman);
	if (Body == nullptr || Anim == nullptr)
	{
		return false;
	}
	if (Body->GetSkeletalMeshAsset() != nullptr && Body->GetSkeletalMeshAsset()->GetSkeleton() != Anim->GetSkeleton())
	{
		// Still plays (5.8 remaps bones by name), but the idle copy should be on the project skeleton.
		UE_LOG(LogWTA, Verbose, TEXT("%s: idle %s uses another skeleton asset"), *MetaHuman->GetName(), *Anim->GetName());
	}
	Body->SetAnimationMode(EAnimationMode::AnimationSingleNode);
	Body->PlayAnimation(Anim, bLoop);
	const float Length = Anim->GetPlayLength();
	if (Length > 0.f)
	{
		Body->SetPosition(FMath::Fmod(FMath::Max(StartTime, 0.f), Length), false);
	}
	if (!bLoop)
	{
		Body->Stop();
		// A held pose is evaluated, then frozen (Freeze). Evaluate it even while off screen, so a figure the player
		// has not seen yet does not keep its bind pose (arms out); every frame, at whatever LOD it is drawn at, and
		// never skipped or interpolated by the update rate optimizer, so the frame before a freeze is a full pose.
		TInlineComponentArray<USkeletalMeshComponent*> Meshes;
		MetaHuman->GetComponents(Meshes);
		for (USkeletalMeshComponent* Mesh : Meshes)
		{
			if (Mesh != nullptr)
			{
				Mesh->bEnableUpdateRateOptimizations = false;
			}
		}
		Thaw(MetaHuman);
	}
	return true;
}

void UWTAPeopleLibrary::Freeze(AActor* MetaHuman)
{
	if (MetaHuman == nullptr)
	{
		return;
	}
	TInlineComponentArray<USkeletalMeshComponent*> Meshes;
	MetaHuman->GetComponents(Meshes);
	for (USkeletalMeshComponent* Mesh : Meshes)
	{
		if (Mesh != nullptr)
		{
			// Keep the evaluated bones and skip all further animation work (body, face rig, clothes). The
			// component still ticks, so its LOD keeps following the camera (see the header: thaw on LOD changes).
			Mesh->bNoSkeletonUpdate = true;
			Mesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered;
		}
	}
}

void UWTAPeopleLibrary::Thaw(AActor* MetaHuman)
{
	if (MetaHuman == nullptr)
	{
		return;
	}
	TInlineComponentArray<USkeletalMeshComponent*> Meshes;
	MetaHuman->GetComponents(Meshes);
	for (USkeletalMeshComponent* Mesh : Meshes)
	{
		if (Mesh != nullptr)
		{
			Mesh->bNoSkeletonUpdate = false;
			Mesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
		}
	}
}

int32 UWTAPeopleLibrary::NextLOD(const USkeletalMeshComponent* Mesh)
{
	if (Mesh == nullptr || Mesh->GetSkeletalMeshAsset() == nullptr)
	{
		return INDEX_NONE;
	}
	const ILODSyncInterface* Sync = Cast<ILODSyncInterface>(Mesh);
	const int32 Forced = Sync != nullptr ? Sync->GetForceRenderedLOD() : INDEX_NONE;
	if (Forced < 0)
	{
		return Mesh->GetPredictedLODLevel();
	}
	const int32 MinLOD = Mesh->ComputeMinLOD();
	const int32 MaxLOD = FMath::Max(Mesh->GetNumLODs() - 1, MinLOD);
	int32 LOD = FMath::Clamp(Forced, MinLOD, MaxLOD);
	const int32 Best = Sync->GetBestAvailableLOD();
	if (Best >= 0)
	{
		LOD = FMath::Max(LOD, Best);
	}
	return LOD;
}

int32 UWTAPeopleLibrary::CountCollapsedBones(const USkeletalMeshComponent* Mesh, FString* OutNames)
{
	const USkeletalMesh* Asset = Mesh != nullptr ? Mesh->GetSkeletalMeshAsset() : nullptr;
	const FSkeletalMeshRenderData* RenderData = Asset != nullptr ? Asset->GetResourceForRendering() : nullptr;
	const int32 LOD = Mesh != nullptr ? Mesh->GetPredictedLODLevel() : INDEX_NONE;
	if (RenderData == nullptr || !RenderData->LODRenderData.IsValidIndex(LOD))
	{
		return 0;
	}
	const FReferenceSkeleton& Ref = Asset->GetRefSkeleton();
	const TArray<FTransform>& RefLocal = Ref.GetRefBonePose();
	const TArray<FTransform>& Pose = Mesh->GetComponentSpaceTransforms();
	const int32 Num = FMath::Min(Ref.GetNum(), Pose.Num());
	// The reference pose in component space (a parent always comes before its children).
	TArray<FTransform> RefPose;
	RefPose.SetNum(Num);
	for (int32 i = 0; i < Num; ++i)
	{
		const int32 Parent = Ref.GetParentIndex(i);
		RefPose[i] = (Parent >= 0 && Parent < i) ? RefLocal[i] * RefPose[Parent] : RefLocal[i];
	}
	int32 Count = 0;
	for (const FBoneIndexType Bone : RenderData->LODRenderData[LOD].ActiveBoneIndices)
	{
		if (Bone >= Num)
		{
			continue;
		}
		const FVector At = Pose[Bone].GetLocation();
		if (At.ContainsNaN() || (At.Size() < 3.0 && RefPose[Bone].GetLocation().Size() > 10.0))
		{
			if (OutNames != nullptr && Count < 4)
			{
				*OutNames += (OutNames->IsEmpty() ? TEXT("") : TEXT(", ")) + Ref.GetBoneName(Bone).ToString();
			}
			++Count;
		}
	}
	return Count;
}

FString UWTAPeopleLibrary::DescribeMeshes(AActor* MetaHuman)
{
	FString Out;
	if (MetaHuman == nullptr)
	{
		return Out;
	}
	TInlineComponentArray<USkeletalMeshComponent*> Meshes;
	MetaHuman->GetComponents(Meshes);
	for (const USkeletalMeshComponent* Mesh : Meshes)
	{
		if (Mesh == nullptr || Mesh->GetSkeletalMeshAsset() == nullptr)
		{
			continue;
		}
		const ILODSyncInterface* Sync = Cast<ILODSyncInterface>(Mesh);
		FString Names;
		const int32 Collapsed = CountCollapsedBones(Mesh, &Names);
		Out += FString::Printf(TEXT("%s%s LOD %d of %d (forced %d, streamed in %d, wants %d)%s%s"),
			Out.IsEmpty() ? TEXT("") : TEXT("; "), *Mesh->GetName(), Mesh->GetPredictedLODLevel(), Mesh->GetNumLODs(),
			Sync != nullptr ? Sync->GetForceRenderedLOD() : -1, Sync != nullptr ? Sync->GetBestAvailableLOD() : -1,
			Sync != nullptr ? Sync->GetDesiredSyncLOD() : -1, Mesh->bNoSkeletonUpdate ? TEXT(" frozen") : TEXT(""),
			Collapsed > 0 ? *FString::Printf(TEXT(" %d BONES AT THE FEET (%s)"), Collapsed, *Names) : TEXT(""));
	}
	return Out;
}

float UWTAPeopleLibrary::PersonPhase(FName Person)
{
	const uint32 Hash = GetTypeHash(Person.ToString());
	return static_cast<float>(Hash % 1000u) / 1000.f;
}

bool UWTAPeopleLibrary::SetAnimationSkeleton(UAnimSequence* Anim, USkeleton* Skeleton)
{
#if WITH_EDITOR
	if (Anim == nullptr || Skeleton == nullptr)
	{
		return false;
	}
	if (Anim->GetSkeleton() != Skeleton)
	{
		Anim->ReplaceSkeleton(Skeleton, false);  // remaps the tracks by bone name, marks the package dirty
	}
	return Anim->GetSkeleton() == Skeleton;
#else
	return false;
#endif
}
