// Walk the Archive - what everybody in a guided visit shares.
//
// In solo play nothing here changes. In a guided visit the guide's machine is the listen server and owns this: the
// tour stop the guide is showing (TourStop, -1 when no tour runs) and the last "gather round" (where the guide stood
// and which way they faced). Each comes with a serial, so showing the same stop again or gathering on the same
// spot still reaches everyone. On the visitors' machines the OnReps hand them to UWTAVisitSubsystem, which walks
// each visitor to their own place round the spot (UWTAVisitSubsystem::GroupSpot).
// The guide's tour (UWTATourSubsystem::OnTourChanged) calls LeadStop through the visit subsystem; its Gather button
// and the G key call Gather.
//
// On a visitor's machine the game mode does not exist, so BeginPlay builds that machine's own NavMesh (the visitors
// walk to the stops on it) the way AWTAGameMode::StartPlay does on the guide's.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameStateBase.h"
#include "WTAGameState.generated.h"

class AWTAPlayerState;

UCLASS()
class WALKTHEARCHIVE_API AWTAGameState : public AGameStateBase
{
	GENERATED_BODY()

public:
	/** The stop the guide shows (DT_Tour order, 0-based), -1 when no tour runs. */
	UPROPERTY(ReplicatedUsing = OnRep_Tour, BlueprintReadOnly, Category = "WTA")
	int32 TourStop = -1;

	/** Bumped by every LeadStop. */
	UPROPERTY(ReplicatedUsing = OnRep_Tour, BlueprintReadOnly, Category = "WTA")
	int32 TourSerial = 0;

	/** Bumped by every Gather; GatherFloor and GatherYaw say where. */
	UPROPERTY(ReplicatedUsing = OnRep_Gather, BlueprintReadOnly, Category = "WTA")
	int32 GatherSerial = 0;

	/** The floor point the guide stood on when they gathered the group (cm). */
	UPROPERTY(Replicated, BlueprintReadOnly, Category = "WTA")
	FVector GatherFloor = FVector::ZeroVector;

	/** The way the guide faced. */
	UPROPERTY(Replicated, BlueprintReadOnly, Category = "WTA")
	float GatherYaw = 0.f;

	/** Server: the guide shows stop Index (-1: the tour ended). */
	void LeadStop(int32 Index);

	/** Server: everyone comes to the guide, round Floor, facing Yaw's way. */
	void Gather(const FVector& Floor, float Yaw);

	/** The guide's player state (null in solo play). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	AWTAPlayerState* GetGuide() const;

	/** Everyone in the visit but the guide. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 NumVisitors() const;

	virtual void BeginPlay() override;
	virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
	UFUNCTION()
	void OnRep_Tour();

	UFUNCTION()
	void OnRep_Gather();
};
