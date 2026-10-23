// Walk the Archive - a framed exhibit, the Freedom to Read board, or a Wax Hall reading card.

#include "World/WTAExhibitActor.h"
#include "Core/WTAText.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "Systems/WTAContentSubsystem.h"
#include "Systems/WTAProgressSubsystem.h"
#include "CollisionQueryParams.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/SoftObjectPath.h"

AWTAExhibitActor::AWTAExhibitActor()
{
}

void AWTAExhibitActor::BeginPlay()
{
	Super::BeginPlay();
	HangSeasonPicture();
}

bool AWTAExhibitActor::HangSeasonPicture()
{
	if (SeasonPlane != nullptr)
	{
		SeasonPlane->DestroyComponent();
		SeasonPlane = nullptr;
	}
	// This season's picture over the frame: the engine plane (100 x 100 cm, facing +Z) stood on the wall at the row's
	// artwork, its width along the wall and its V down it, a few centimetres out so it covers the baked art.
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	const FWTAExhibitRow* Row = Content ? Content->FindExhibit(ItemId) : nullptr;
	UTexture2D* Picture = (Content != nullptr && Row != nullptr) ? Content->SeasonTexture(ItemId) : nullptr;
	if (Picture == nullptr || Row->Size.X <= 0.f || Row->Size.Y <= 0.f)
	{
		return false;
	}
	UStaticMesh* Plane = Cast<UStaticMesh>(FSoftObjectPath(TEXT("/Engine/BasicShapes/Plane.Plane")).TryLoad());
	UMaterialInterface* Unlit = Cast<UMaterialInterface>(FSoftObjectPath(TEXT("/Game/WTA/Materials/M_WTA_Unlit.M_WTA_Unlit")).TryLoad());
	if (Plane == nullptr || Unlit == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("%s: no plane or M_WTA_Unlit for the season's picture"), *GetName());
		return false;
	}
	// Keep the picture's proportions inside the frame's size.
	const float Aspect = static_cast<float>(Picture->GetSizeX()) / FMath::Max(1.f, static_cast<float>(Picture->GetSizeY()));
	float Width = Row->Size.X;
	float Height = Width / Aspect;
	if (Height > Row->Size.Y)
	{
		Height = Row->Size.Y;
		Width = Height * Aspect;
	}
	const FRotator Facing(0.f, Row->Yaw, 0.f);
	// The baked frame stands proud of the wall by a few centimetres (the row's Location is the artwork's centre on
	// the wall): a line from the view spot finds the frame's face, and the picture hangs a centimetre in front of it.
	float OutCm = 4.f;
	if (Row->View.bValid && GetWorld() != nullptr)
	{
		FHitResult Hit;
		FCollisionQueryParams Params(SCENE_QUERY_STAT(WTASeasonPicture), false, this);
		if (GetWorld()->LineTraceSingleByChannel(Hit, Row->View.Location, Row->Location - Facing.Vector() * 10.f, ECC_Visibility, Params))
		{
			OutCm = FMath::Clamp(FVector::DotProduct(Hit.ImpactPoint - Row->Location, Facing.Vector()) + 1.f, 1.f, 30.f);
		}
	}
	SeasonPlane = NewObject<UStaticMeshComponent>(this, TEXT("SeasonPicture"));
	SeasonPlane->SetStaticMesh(Plane);
	SeasonPlane->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	SeasonPlane->SetCastShadow(false);
	SeasonPlane->SetupAttachment(GetRootComponent());
	SeasonPlane->SetWorldLocationAndRotation(Row->Location + Facing.Vector() * OutCm, Facing + FRotator(0.f, -90.f, 90.f));
	SeasonPlane->SetWorldScale3D(FVector(Width / 100.f, Height / 100.f, 1.f));
	if (UMaterialInstanceDynamic* Mid = UMaterialInstanceDynamic::Create(Unlit, this))
	{
		Mid->SetTextureParameterValue(TEXT("BaseColorTexture"), Picture);
		Mid->SetScalarParameterValue(TEXT("Luminance"), 0.8f);
		Mid->SetVectorParameterValue(TEXT("BaseColorFactor"), FLinearColor::White);
		SeasonPlane->SetMaterial(0, Mid);
	}
	SeasonPlane->RegisterComponent();
	UE_LOG(LogWTA, Display, TEXT("WTA_SEASON %s hangs this season's picture (%.0f x %.0f cm), %.1f cm out from %s facing %.0f"),
		*ItemId.ToString(), Width, Height, OutCm, *Row->Location.ToString(), Row->Yaw);
	return true;
}

bool AWTAExhibitActor::IsAlreadySeen() const
{
	const UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this);
	return Progress != nullptr && !ItemId.IsNone() && Progress->HasSeenExhibit(ItemId);
}

void AWTAExhibitActor::ReadRow()
{
	Super::ReadRow();

	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	const FWTAExhibitRow* Row = Content ? Content->FindExhibit(ItemId) : nullptr;
	if (Row == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("%s: no DT_Exhibits row '%s'"), *GetName(), *ItemId.ToString());
		Label = WTAText(TEXT("Open"));
		return;
	}

	Label = FText::Format(WTAText(TEXT("Open \u00B7 {0}")), Row->Title);
	ViewSpot = Row->View;
}

void AWTAExhibitActor::Interact_Implementation(AWTAPlayerController* Controller)
{
	if (Controller == nullptr)
	{
		return;
	}

	// Walk to the viewing spot first, then open the card (the controller notes the exhibit as seen).
	if (ViewSpot.bValid)
	{
		Controller->GoToView(ViewSpot, true);
	}
	Controller->OpenExhibit(ItemId);
}
