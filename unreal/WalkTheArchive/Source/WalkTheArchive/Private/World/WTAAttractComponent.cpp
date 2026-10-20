// Walk the Archive - the thing that makes an exhibit call you over.

#include "World/WTAAttractComponent.h"
#include "World/WTAPickActor.h"
#include "Components/SpotLightComponent.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/Pawn.h"

UWTAAttractComponent::UWTAAttractComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	// A tenth of a second is far finer than the eye needs for a light that takes half a second to swell,
	// and it keeps a gallery of these off the frame budget.
	PrimaryComponentTick.TickInterval = 0.1f;

	Spot = CreateDefaultSubobject<USpotLightComponent>(TEXT("AttractSpot"));
	Spot->SetupAttachment(this);
	Spot->SetIntensityUnits(ELightUnits::Candelas);
	Spot->SetIntensity(0.f);
	Spot->SetAttenuationRadius(900.f);
	Spot->SetInnerConeAngle(22.f);
	Spot->SetOuterConeAngle(42.f);
	Spot->SetCastShadows(false);
	Spot->SetVisibility(false);
}

void UWTAAttractComponent::BeginPlay()
{
	Super::BeginPlay();

	Spot->SetLightColor(LightColor);

	// Spread the breathing out, so a row of frames on one wall does not pulse as one animal.
	const AActor* Owner = GetOwner();
	Phase = Owner != nullptr ? FMath::Frac(GetTypeHash(Owner->GetFName()) * 0.0001f) * BreathSeconds : 0.f;

	// Hang the light on the side the player is meant to stand, so it rakes the art rather than lighting the wall.
	// The owner has read its row by now (AWTAPickActor::BeginPlay calls RefreshFromData before components tick).
	FWTAView View;
	if (Owner != nullptr && IWTAInteractable::Execute_GetViewSpot(const_cast<AActor*>(Owner), View) && View.bValid)
	{
		AimFrom(View.Location);
	}
	else
	{
		AimFrom(GetComponentLocation() + FVector(0.f, 0.f, 1.f));
	}
}

void UWTAAttractComponent::AimFrom(const FVector& ViewerLocation)
{
	const FVector Here = GetComponentLocation();
	FVector Out = ViewerLocation - Here;
	Out.Z = 0.f;
	// Straight down when the viewer is directly above or there is no view spot to speak of.
	Out = Out.GetSafeNormal();

	const FVector LightPos = Here + Out * LightOut + FVector(0.f, 0.f, LightUp);
	Spot->SetWorldLocation(LightPos);
	Spot->SetWorldRotation((Here - LightPos).Rotation());
	Spot->SetAttenuationRadius(FMath::Max(600.f, (Here - LightPos).Size() * 2.6f));
}

float UWTAAttractComponent::GetIntensity() const
{
	return (Spot != nullptr && Spot->IsVisible()) ? Spot->Intensity : 0.f;
}

void UWTAAttractComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (!bEnabled)
	{
		if (Spot->IsVisible()) { Spot->SetVisibility(false); }
		Attention = 0.f;
		return;
	}

	const APawn* Player = UGameplayStatics::GetPlayerPawn(this, 0);
	if (Player == nullptr) { return; }

	// Nearness, eased so the swell is gentle at the far end and firm as you arrive.
	const float Dist = FVector::Dist(Player->GetActorLocation(), GetComponentLocation());
	const float Raw = 1.f - FMath::SmoothStep(NearDistance, FarDistance, Dist);
	Attention = FMath::FInterpTo(Attention, Raw, DeltaTime, 1.f / FMath::Max(0.05f, Smoothing));

	// Below this the light contributes nothing anyone can see, so stop paying for it.
	if (Attention < 0.01f)
	{
		if (Spot->IsVisible()) { Spot->SetVisibility(false); }
		return;
	}

	const AWTAPickActor* Owner = Cast<AWTAPickActor>(GetOwner());
	const bool bSeen = Owner != nullptr && Owner->IsAlreadySeen();

	Phase += DeltaTime;
	// Unseen exhibits breathe; once you have opened the card it holds steady and sits lower, so the room reads
	// as "these ones you have not looked at yet".
	const float Breath = bSeen ? 1.f
		: 1.f - BreathDepth * 0.5f * (1.f - FMath::Cos(2.f * PI * Phase / FMath::Max(0.5f, BreathSeconds)));
	const float Ceiling = PeakIntensity * (bSeen ? SeenScale : 1.f);
	const float Want = FMath::Lerp(RestIntensity, Ceiling, Attention) * Breath;

	if (!Spot->IsVisible()) { Spot->SetVisibility(true); }
	Spot->SetIntensity(Want);
}

FString UWTAAttractComponent::Describe() const
{
	const AWTAPickActor* Owner = Cast<AWTAPickActor>(GetOwner());
	return FString::Printf(TEXT("attention %.2f intensity %.0f seen %d"),
		Attention, GetIntensity(), (Owner != nullptr && Owner->IsAlreadySeen()) ? 1 : 0);
}
