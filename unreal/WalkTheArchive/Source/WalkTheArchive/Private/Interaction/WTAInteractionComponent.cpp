// Walk the Archive - hover trace and interact dispatch.

#include "Interaction/WTAInteractionComponent.h"
#include "Interaction/WTAInteractable.h"
#include "Core/WTAPlayerController.h"
#include "CollisionQueryParams.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"

UWTAInteractionComponent::UWTAInteractionComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
}

void UWTAInteractionComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	UpdateHover();
}

bool UWTAInteractionComponent::ComputeTraceRay(FVector& OutStart, FVector& OutDirection) const
{
	const APlayerController* PC = Cast<APlayerController>(GetOwner());
	if (PC == nullptr || !PC->IsLocalController())
	{
		return false;
	}
	if (bRayOverride)
	{
		OutStart = RayStart;
		OutDirection = RayDirection;
		return !bRayBlocked && !RayDirection.IsNearlyZero();
	}
	if (bUseMouseCursor)
	{
		FVector WorldLocation;
		FVector WorldDirection;
		if (PC->DeprojectMousePositionToWorld(WorldLocation, WorldDirection))
		{
			OutStart = WorldLocation;
			OutDirection = WorldDirection.GetSafeNormal();
			return !OutDirection.IsNearlyZero();
		}
		return false;
	}
	FVector ViewLocation;
	FRotator ViewRotation;
	PC->GetPlayerViewPoint(ViewLocation, ViewRotation);
	OutStart = ViewLocation;
	OutDirection = ViewRotation.Vector();
	return true;
}

void UWTAInteractionComponent::UpdateHover()
{
	FVector Start;
	FVector Direction;
	UWorld* World = GetWorld();
	if (World == nullptr || !ComputeTraceRay(Start, Direction))
	{
		LastHit = FHitResult();
		SetHovered(nullptr);
		return;
	}

	FCollisionQueryParams Params(FName(TEXT("WTAHover")), false);
	if (const APlayerController* PC = Cast<APlayerController>(GetOwner()))
	{
		if (const APawn* Pawn = PC->GetPawn())
		{
			Params.AddIgnoredActor(Pawn);
		}
	}

	FHitResult Hit;
	const FVector End = Start + Direction * MaxDistance;
	const bool bHit = World->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Params);
	LastHit = bHit ? Hit : FHitResult();

	AActor* NewHovered = nullptr;
	if (bHit)
	{
		AActor* HitActor = Hit.GetActor();
		if (HitActor != nullptr && HitActor->Implements<UWTAInteractable>())
		{
			NewHovered = HitActor;
		}
	}
	SetHovered(NewHovered);
}

bool UWTAInteractionComponent::TryInteract()
{
	AActor* Actor = Hovered.Get();
	if (Actor == nullptr || !Actor->Implements<UWTAInteractable>())
	{
		return false;
	}
	AWTAPlayerController* PC = Cast<AWTAPlayerController>(GetOwner());
	IWTAInteractable::Execute_Interact(Actor, PC);
	OnInteracted.Broadcast(Actor);
	return true;
}

AActor* UWTAInteractionComponent::GetHovered() const
{
	return Hovered.Get();
}

bool UWTAInteractionComponent::HasHover() const
{
	return Hovered.IsValid();
}

void UWTAInteractionComponent::SetRayOverride(bool bOn, const FVector& Start, const FVector& Direction, bool bBlocked)
{
	bRayOverride = bOn;
	bRayBlocked = bOn && bBlocked;
	RayStart = Start;
	RayDirection = Direction.GetSafeNormal();
}

bool UWTAInteractionComponent::GetLastHitLocation(FVector& OutLocation, FVector& OutNormal) const
{
	if (!LastHit.bBlockingHit)
	{
		return false;
	}
	OutLocation = LastHit.ImpactPoint;
	OutNormal = LastHit.ImpactNormal;
	return true;
}

void UWTAInteractionComponent::SetHovered(AActor* NewActor)
{
	AActor* Current = Hovered.Get();
	if (Current == NewActor && NewActor != nullptr)
	{
		// The same actor: its label can change while it is looked at (a seat taken, a story playing, a count).
		const FText Label = IWTAInteractable::Execute_GetInteractLabel(NewActor);
		if (!Label.ToString().Equals(HoverLabel.ToString(), ESearchCase::CaseSensitive))
		{
			HoverLabel = Label;
			OnHoverChanged.Broadcast(HoverLabel);
		}
		return;
	}
	// A destroyed actor under the crosshair reads as "nothing"; its stale label still has to go.
	if (Current == NewActor && HoverLabel.IsEmpty())
	{
		return;
	}
	Hovered = NewActor;
	HoverLabel = NewActor ? IWTAInteractable::Execute_GetInteractLabel(NewActor) : FText::GetEmpty();
	OnHoverChanged.Broadcast(HoverLabel);
}
