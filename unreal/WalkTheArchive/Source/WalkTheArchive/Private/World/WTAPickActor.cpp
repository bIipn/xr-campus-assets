// Walk the Archive - shared base of the pick-box actors.

#include "World/WTAPickActor.h"
#include "Components/BoxComponent.h"
#include "Engine/EngineTypes.h"

AWTAPickActor::AWTAPickActor()
{
	PrimaryActorTick.bCanEverTick = false;

	// The root is the pick volume. It answers Visibility traces only, so hover works and the player walks through.
	PickBox = CreateDefaultSubobject<UBoxComponent>(TEXT("PickBox"));
	SetRootComponent(PickBox);
	PickBox->SetBoxExtent(PickExtent);
	PickBox->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	PickBox->SetCollisionObjectType(ECC_WorldDynamic);
	PickBox->SetCollisionResponseToAllChannels(ECR_Ignore);
	PickBox->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	PickBox->SetGenerateOverlapEvents(false);
	PickBox->SetCanEverAffectNavigation(false);
	PickBox->CanCharacterStepUpOn = ECB_No;
	PickBox->SetHiddenInGame(true);
}

void AWTAPickActor::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

	if (PickBox != nullptr)
	{
		PickBox->SetBoxExtent(PickExtent, false);
	}
}

void AWTAPickActor::BeginPlay()
{
	Super::BeginPlay();
	RefreshFromData();
}

FText AWTAPickActor::GetInteractLabel_Implementation() const
{
	return Label;
}

void AWTAPickActor::Interact_Implementation(AWTAPlayerController* Controller)
{
	// Subclasses decide what opens.
}

bool AWTAPickActor::GetViewSpot_Implementation(FWTAView& OutView) const
{
	OutView = ViewSpot;
	return ViewSpot.bValid;
}

void AWTAPickActor::RefreshFromData()
{
	ReadRow();
}

void AWTAPickActor::ReadRow()
{
	Label = FText::GetEmpty();
	ViewSpot = FWTAView();
}
