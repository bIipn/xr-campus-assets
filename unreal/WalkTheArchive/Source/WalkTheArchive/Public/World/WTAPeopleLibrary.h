// Walk the Archive - helpers for the MetaHuman people (staff and Wax Hall reenactors).
//
// Every person is built by Content/Python/wta_people (MetaHuman Creator, UE 5.8) into
// /Game/WTA/Characters/<Person>/BP_<Person>, a plain actor whose "Body" skeletal mesh leads the face, clothes
// and grooms. These helpers find that Blueprint, pose its body with an animation (staff loop an idle; Wax Hall
// figures hold one frame of it) and freeze a held pose so it costs nothing per frame.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "UObject/SoftObjectPath.h"
#include "WTAPeopleLibrary.generated.h"

class AActor;
class UAnimSequence;
class USkeletalMeshComponent;
class USkeleton;

UCLASS()
class WALKTHEARCHIVE_API UWTAPeopleLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/** Idle every person plays: AS_MH_Neutral_Stand_Idle_Loop copied from MetaHuman Creator's optional content. */
	static const TCHAR* DefaultIdlePath;

	/** /Game/WTA/Characters/<Person>/BP_<Person>.BP_<Person>_C */
	UFUNCTION(BlueprintPure, Category = "WTA|People")
	static FSoftClassPath MetaHumanClassPath(FName Person);

	/** Loads the person's MetaHuman Blueprint class; null (and one log line) when it has not been built yet. */
	UFUNCTION(BlueprintCallable, Category = "WTA|People")
	static UClass* LoadMetaHumanClass(FName Person);

	/** The MetaHuman's body mesh: the skeletal mesh component named "Body", else the one the others follow. */
	UFUNCTION(BlueprintCallable, Category = "WTA|People")
	static USkeletalMeshComponent* FindBody(AActor* MetaHuman);

	/**
	 * Plays Anim on the body (single-node mode). bLoop: a living idle (staff). Otherwise the body holds the frame at
	 * StartTime seconds (a wax figure), and every mesh on the actor evaluates at LOD0 even off screen until Freeze.
	 * Returns false when there is no body or no animation.
	 */
	UFUNCTION(BlueprintCallable, Category = "WTA|People")
	static bool PlayPose(AActor* MetaHuman, UAnimSequence* Anim, bool bLoop, float StartTime);

	/**
	 * Holds the pose as last evaluated: every skeletal mesh on the actor skips further animation and bone updates
	 * (bNoSkeletonUpdate) but keeps ticking, so LODs still follow the camera.
	 */
	UFUNCTION(BlueprintCallable, Category = "WTA|People")
	static void Freeze(AActor* MetaHuman);

	/** A stable 0..1 value per person, used to give each figure its own frame of the idle. */
	UFUNCTION(BlueprintPure, Category = "WTA|People")
	static float PersonPhase(FName Person);

	/**
	 * Editor only: points Anim at Skeleton (same bone names, UAnimationAsset::ReplaceSkeleton) and marks it dirty.
	 * Used once to move Epic's idle onto the project's MetaHuman skeleton. Returns false in a game build.
	 */
	UFUNCTION(BlueprintCallable, Category = "WTA|People")
	static bool SetAnimationSkeleton(UAnimSequence* Anim, USkeleton* Skeleton);
};
