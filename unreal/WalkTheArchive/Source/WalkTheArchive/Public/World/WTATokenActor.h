// Walk the Archive - a hidden XR token.
//
// Mesh: /Engine/BasicShapes/Sphere at scale 0.25 with a dynamic instance of /Engine/BasicShapes/BasicShapeMaterial
// ("Color" parameter set to GlowColor, bright enough to bloom). Spins and bobs when the player is within
// AnimateWithin. Hidden at BeginPlay if the progress subsystem already has it. Interact: if the row's RideGate is set
// and that ride is not running (phase 0: never), toast "Ride the <ride> to grab that one!"; else CollectToken + hide.
// The editor Python places it at the token__<id> mesh centre (or DT_Tokens.Location) and sets token_id.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Math/Color.h"
#include "Interaction/WTAInteractable.h"
#include "WTATokenActor.generated.h"

class UMaterialInstanceDynamic;
class USceneComponent;
class USphereComponent;
class UStaticMeshComponent;

UCLASS(Blueprintable)
class WALKTHEARCHIVE_API AWTATokenActor : public AActor, public IWTAInteractable
{
	GENERATED_BODY()

public:
	AWTATokenActor();

	/** DT_Tokens row (editor Python: token_id). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FName TokenId;

	/** Root (the bob offset is applied to Mesh, not the root). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	TObjectPtr<USceneComponent> Root;

	/** Pick volume (radius 40 cm), blocks Visibility only. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	TObjectPtr<USphereComponent> PickSphere;

	/** The glowing sphere. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	TObjectPtr<UStaticMeshComponent> Mesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float SpinDegreesPerSecond = 103.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float BobAmplitude = 5.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float BobSeconds = 2.2f;

	/** Only animate when the player is closer than this (cm). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float AnimateWithin = 1000.f;

	/** Brass glow. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	FLinearColor GlowColor = FLinearColor(2.4f, 1.6f, 0.5f, 1.f);

	/** Created at BeginPlay from the mesh's material. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA")
	TObjectPtr<UMaterialInstanceDynamic> GlowMaterial;

	// IWTAInteractable
	virtual FText GetInteractLabel_Implementation() const override;
	virtual void Interact_Implementation(AWTAPlayerController* Controller) override;
	virtual bool GetViewSpot_Implementation(FWTAView& OutView) const override;

	/** Hide and disable collision (collected), or show again (progress reset). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void SetCollected(bool bInCollected);

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsCollected() const { return bCollected; }

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	/** Copied from the row at BeginPlay. */
	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FName RideGate;

	/** Progress was wiped (bound to UWTAProgressSubsystem::OnProgressReset): show the token again. */
	UFUNCTION()
	void HandleProgressReset();

	bool bCollected = false;
	float BobPhase = 0.f;
};
