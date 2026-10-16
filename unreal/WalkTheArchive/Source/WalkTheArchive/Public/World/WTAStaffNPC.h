// Walk the Archive - a virtual staff member (Margaret, Rosa, Mr. Hale, Coach Rae).
//
// Placeholder body = the character capsule + /Engine/BasicShapes/Cylinder tinted with the row's Color, until
// DT_Staff.MetaHuman is set; then MetaHumanChild spawns that Blueprint and the cylinder hides. The capsule keeps
// its Pawn preset, so the player cannot walk through staff and Visibility traces hit them (hover works).
// Tick: when the player is within LookAtDistance, yaw toward the player at TurnRate (exp ease); otherwise return
// to the row's Yaw. Interact: open the staff chat. GetViewSpot: the row's TalkView.
// The editor Python places it at the row's Location/Yaw and sets staff_id.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "Math/Color.h"
#include "Data/WTATypes.h"
#include "Interaction/WTAInteractable.h"
#include "WTAStaffNPC.generated.h"

class UChildActorComponent;
class UStaticMeshComponent;
class UTextRenderComponent;

UCLASS(Blueprintable)
class WALKTHEARCHIVE_API AWTAStaffNPC : public ACharacter, public IWTAInteractable
{
	GENERATED_BODY()

public:
	AWTAStaffNPC();

	/** DT_Staff row (editor Python: staff_id). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FName StaffId;

	/** Cylinder body shown until a MetaHuman is set. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	TObjectPtr<UStaticMeshComponent> PlaceholderBody;

	/** Spawns DT_Staff.MetaHuman when set. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	TObjectPtr<UChildActorComponent> MetaHumanChild;

	/** Floating name above the head, faces the camera. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	TObjectPtr<UTextRenderComponent> NameLabel;

	/** Turn toward the player within this distance (web: 12 m). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float LookAtDistance = 1200.f;

	/** Exponential turn rate (1/s). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float TurnRate = 4.f;

	// Copied from the row at BeginPlay (ApplyStaffRow).
	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FText DisplayName;

	/** The row's Role text (named StaffRole because AActor already has a reflected Role). */
	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FText StaffRole;

	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FLinearColor Color = FLinearColor::White;

	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FWTAView TalkView;

	/** Read DT_Staff[StaffId]: name label, colour, talk view, MetaHuman child. Safe to call again. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ApplyStaffRow();

	/** Mark the NPC as talking for clamp(len/16, 1.2, 7) seconds (animation hook for phase 2). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Talk(const FText& Text);

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsTalking() const;

	// IWTAInteractable
	virtual FText GetInteractLabel_Implementation() const override;
	virtual void Interact_Implementation(AWTAPlayerController* InController) override;
	virtual bool GetViewSpot_Implementation(FWTAView& OutView) const override;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	/** World time until which the NPC counts as talking. */
	float TalkUntil = 0.f;

	/** Rotation to return to when the player walks away. */
	FRotator HomeRotation = FRotator::ZeroRotator;
};
