// Walk the Archive - a screen in the world for VR (see XR/WTAVRScreenActor.h).

#include "XR/WTAVRScreenActor.h"
#include "Core/WTALog.h"
#include "Blueprint/UserWidget.h"
#include "Components/WidgetComponent.h"
#include "Materials/MaterialInterface.h"
#include "UObject/SoftObjectPath.h"
#include "Widgets/SWidget.h"

namespace
{
	const TCHAR* ScreenMaterialPath = TEXT("/Game/WTA/Materials/M_WTA_WidgetScreen.M_WTA_WidgetScreen");
}

UMaterialInterface* AWTAVRScreenActor::ScreenMaterial()
{
	static TWeakObjectPtr<UMaterialInterface> Cached;
	static bool bWarned = false;
	if (!Cached.IsValid())
	{
		Cached = Cast<UMaterialInterface>(FSoftObjectPath(ScreenMaterialPath).TryLoad());
		if (!Cached.IsValid() && !bWarned)
		{
			bWarned = true;
			UE_LOG(LogWTA, Warning, TEXT("WTA_VR no %s: VR screens draw with the engine's widget material, dark under the campus exposure (the lighting step builds it)"), ScreenMaterialPath);
		}
	}
	return Cached.Get();
}

void AWTAVRScreenActor::FitToWidget(UWidgetComponent* Component)
{
	UUserWidget* Content = Component != nullptr ? Component->GetUserWidgetObject() : nullptr;
	if (Content == nullptr)
	{
		return;
	}
	Content->TakeWidget();                                   // its Slate widget, if the component has not drawn it yet
	Content->ForceLayoutPrepass();
	const FVector2D Want = Content->GetDesiredSize();
	if (Want.X >= 1.0 && Want.Y >= 1.0)
	{
		Component->SetDrawSize(FVector2D(FMath::CeilToDouble(Want.X), FMath::CeilToDouble(Want.Y)));
	}
}

AWTAVRScreenActor::AWTAVRScreenActor()
{
	PrimaryActorTick.bCanEverTick = false;
	Screen = CreateDefaultSubobject<UWidgetComponent>(TEXT("Screen"));
	RootComponent = Screen;
	Screen->SetWidgetSpace(EWidgetSpace::World);
	Screen->SetDrawAtDesiredSize(false);
	Screen->SetPivot(FVector2D(0.5f, 0.5f));
	Screen->SetBlendMode(EWidgetBlendMode::Transparent);
	Screen->SetTwoSided(false);
	Screen->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Screen->SetGenerateOverlapEvents(false);
	Screen->SetCanEverAffectNavigation(false);
	Screen->SetCastShadow(false);
	Screen->SetHiddenInGame(true);
	SetActorEnableCollision(false);
}

void AWTAVRScreenActor::Init(UUserWidget* Content, FIntPoint DrawSize, float WidthCm)
{
	Size = FIntPoint(FMath::Max(DrawSize.X, 16), FMath::Max(DrawSize.Y, 16));
	CmPerPixel = FMath::Max(WidthCm, 1.f) / static_cast<float>(Size.X);
	// The widget is drawn in the component's Y-Z plane facing +X, one unit a pixel: scaled, a pixel is CmPerPixel.
	Screen->SetDrawSize(FVector2D(Size));
	SizeScale = 1.f;
	Screen->SetWorldScale3D(FVector(CmPerPixel));
	if (UMaterialInterface* Look = ScreenMaterial())
	{
		Screen->SetMaterial(0, Look);                       // the component makes its instance of it and sets SlateUI
	}
	Screen->SetWidget(Content);
}

void AWTAVRScreenActor::SetSizeScale(float Scale)
{
	const float Wanted = FMath::Clamp(Scale, 0.1f, 4.f);
	if (!FMath::IsNearlyEqual(Wanted, SizeScale, 0.001f))
	{
		SizeScale = Wanted;
		Screen->SetWorldScale3D(FVector(CmPerPixel * SizeScale));
	}
}

void AWTAVRScreenActor::PlaceFacing(const FVector& Eye, float Yaw, float Distance, float Drop)
{
	FVector Centre = Eye + FRotator(0.f, Yaw, 0.f).Vector() * Distance;
	Centre.Z = Eye.Z - Drop;
	// The face (+X) toward the eye, so the screen is square on to it.
	const FRotator Facing = (Eye - Centre).Rotation();
	SetActorLocationAndRotation(Centre, FRotator(Facing.Pitch, Facing.Yaw, 0.f));
	PlacedYaw = Yaw;
}

void AWTAVRScreenActor::SetShown(bool bShow)
{
	if (bShow == bShown)
	{
		return;
	}
	bShown = bShow;
	Screen->SetHiddenInGame(!bShow);
	if (bShow)
	{
		Screen->RequestRenderUpdate();
	}
}

bool AWTAVRScreenActor::Trace(const FVector& Start, const FVector& Direction, float MaxDistance, float& OutDistance, FVector2D& OutPixel) const
{
	if (!bShown || Screen == nullptr)
	{
		return false;
	}
	const FTransform& Transform = Screen->GetComponentTransform();
	const FVector Normal = Transform.GetUnitAxis(EAxis::X);
	const double Facing = FVector::DotProduct(Direction, Normal);
	if (Facing > -1.e-3)
	{
		return false;                                       // along the face, or from behind it
	}
	const double Distance = FVector::DotProduct(Transform.GetLocation() - Start, Normal) / Facing;
	if (Distance < 0.0 || Distance > MaxDistance)
	{
		return false;
	}
	// UWidgetComponent::GetLocalHitLocation's mapping: the widget's x runs along -Y, its y along -Z, from the pivot.
	const FVector Local = Transform.InverseTransformPosition(Start + Direction * Distance);
	const FVector2D Pixel(-Local.Y + Size.X * 0.5, -Local.Z + Size.Y * 0.5);
	if (Pixel.X < 0.0 || Pixel.Y < 0.0 || Pixel.X > Size.X || Pixel.Y > Size.Y)
	{
		return false;
	}
	OutDistance = static_cast<float>(Distance);
	OutPixel = Pixel;
	return true;
}

FVector AWTAVRScreenActor::PixelToWorld(const FVector2D& Pixel) const
{
	const FVector Local(0.0, Size.X * 0.5 - Pixel.X, Size.Y * 0.5 - Pixel.Y);
	return Screen->GetComponentTransform().TransformPosition(Local);
}

bool AWTAVRScreenActor::IsInteractiveAt(const FVector2D& Pixel) const
{
	if (!bShown || Screen == nullptr)
	{
		return false;
	}
	const TArray<FWidgetAndPointer> Path = Screen->GetHitWidgetPath(Pixel, false);
	for (const FWidgetAndPointer& Arranged : Path)
	{
		if (Arranged.Widget->IsInteractable())
		{
			return true;
		}
	}
	return false;
}
