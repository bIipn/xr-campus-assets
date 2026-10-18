// Walk the Archive - helpers for the MetaHuman people (staff and Wax Hall reenactors).

#include "World/WTAPeopleLibrary.h"
#include "Animation/AnimSequence.h"
#include "Animation/Skeleton.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Core/WTALog.h"
#include "GameFramework/Actor.h"
#include "Misc/PackageName.h"

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
			Mesh->SetComponentTickEnabled(false);
		}
	}
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
