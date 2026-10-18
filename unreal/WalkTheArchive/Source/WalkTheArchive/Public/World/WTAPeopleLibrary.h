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

	/** The MetaHuman's face mesh: the skeletal mesh component named "Face" (null when there is none). */
	UFUNCTION(BlueprintCallable, Category = "WTA|People")
	static USkeletalMeshComponent* FindFace(AActor* MetaHuman);

	/**
	 * True once the face has caught up with the body's pose: its head joint sits on the body's head joint (within
	 * half a centimetre). The face copies the body's neck and head in its own anim graph, a frame or more after the
	 * body moves; a face frozen before that keeps its reference pose under a posed head, which pulls the face out of
	 * shape (the "drooping" look). Also true when either mesh or joint is missing (nothing to wait for).
	 */
	UFUNCTION(BlueprintCallable, Category = "WTA|People")
	static bool IsFaceOnBody(AActor* MetaHuman, float& OutGapCm);

	/**
	 * Plays Anim on the body (single-node mode). bLoop: a living idle (staff). Otherwise the body holds the frame at
	 * StartTime seconds (a wax figure), and every mesh on the actor evaluates even off screen (Thaw) until Freeze.
	 * Returns false when there is no body or no animation.
	 */
	UFUNCTION(BlueprintCallable, Category = "WTA|People")
	static bool PlayPose(AActor* MetaHuman, UAnimSequence* Anim, bool bLoop, float StartTime);

	/**
	 * Holds the pose as last evaluated: every skeletal mesh on the actor skips further animation and bone updates
	 * (bNoSkeletonUpdate) but keeps ticking, so LODs still follow the camera. Each LOD skins with its own set of
	 * bones and an evaluation only poses the current LOD's, so a frozen mesh drawn at a finer LOD than it was posed
	 * at has bones left at the component origin (they drag the jaw and lips down to the feet): whoever freezes a
	 * person must Thaw it for a frame or two whenever its LOD changes (AWTAWaxStageActor does).
	 */
	UFUNCTION(BlueprintCallable, Category = "WTA|People")
	static void Freeze(AActor* MetaHuman);

	/** Lets every skeletal mesh on the actor evaluate again, off screen too, until the next Freeze. */
	UFUNCTION(BlueprintCallable, Category = "WTA|People")
	static void Thaw(AActor* MetaHuman);

	/**
	 * The LOD the mesh will draw and evaluate this frame when called after its LOD sync ticked and before the mesh
	 * ticks: the LOD the sync forced, clamped the way USkinnedMeshComponent::UpdateLODStatus clamps it (the mesh's
	 * LOD range, nothing finer than is streamed in). A mesh nothing forces keeps last frame's LOD.
	 */
	static int32 NextLOD(const USkeletalMeshComponent* Mesh);

	/**
	 * Bones the mesh's current LOD skins with that sit at the component origin although the reference pose has them
	 * well away from it: bones that were never evaluated. OutNames (optional) gets the first few names.
	 */
	static int32 CountCollapsedBones(const USkeletalMeshComponent* Mesh, FString* OutNames = nullptr);

	/** One entry per skeletal mesh on the actor: its LOD (forced, best streamed in, wanted), frozen, collapsed bones. */
	static FString DescribeMeshes(AActor* MetaHuman);

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
