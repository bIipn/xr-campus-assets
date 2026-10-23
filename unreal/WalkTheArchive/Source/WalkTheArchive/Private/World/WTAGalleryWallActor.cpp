// Walk the Archive - the visitors' own wall.

#include "World/WTAGalleryWallActor.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "HAL/FileManager.h"
#include "ImageUtils.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	const TCHAR* PlanePath = TEXT("/Engine/BasicShapes/Plane.Plane");
	const TCHAR* PlainPath = TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial");
	const TCHAR* UnlitPath = TEXT("/Game/WTA/Materials/M_WTA_Unlit.M_WTA_Unlit");
	constexpr float GapCm = 24.f;
	constexpr float MatCm = 6.f;
	const FLinearColor MatColour(0.95f, 0.91f, 0.84f);
	const FLinearColor InkColour(0.17f, 0.14f, 0.10f);
	const FLinearColor BrassColour(0.80f, 0.66f, 0.38f);

	/** The engine plane (100 x 100 cm in XY, facing +Z) stood against the wall: facing the actor's +X, its width
	    along -Y (the viewer's right when looking at the wall), its V down the wall. */
	const FRotator PlaneOnWall(0.f, -90.f, 90.f);

	/** "The_Forecourt_Theatre_20261022-161153" -> "The Forecourt Theatre"; a file next to it, <name>.txt, wins. */
	FString NameFromFile(const FString& File)
	{
		FString Base = FPaths::GetBaseFilename(File);
		// Photo mode's names end in _yyyymmdd-hhmmss.
		int32 Cut = INDEX_NONE;
		if (Base.Len() > 16 && Base.FindLastChar(TEXT('_'), Cut) && Base.Len() - Cut == 16 && Base[Cut + 9] == TEXT('-'))
		{
			Base = Base.Left(Cut);
		}
		return Base.Replace(TEXT("_"), TEXT(" ")).TrimStartAndEnd();
	}
}

AWTAGalleryWallActor::AWTAGalleryWallActor()
{
	PickExtent = FVector(60.f, 300.f, 150.f);
	Title = FText::FromString(TEXT("Your pictures"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Plane(PlanePath);
	if (Plane.Succeeded())
	{
		PlaneMesh = Plane.Object;
	}
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> Plain(PlainPath);
	if (Plain.Succeeded())
	{
		PlainMaterial = Plain.Object;
	}
}

TArray<FString> AWTAGalleryWallActor::PictureFolders()
{
	return { FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Postcards")), FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Maker")) };
}

TArray<AWTAGalleryWallActor::FPicture> AWTAGalleryWallActor::FindPictures(int32 Max)
{
	TArray<FPicture> Found;
	for (const FString& Folder : PictureFolders())
	{
		for (const TCHAR* Pattern : { TEXT("*.png"), TEXT("*.jpg"), TEXT("*.jpeg") })
		{
			TArray<FString> Names;
			IFileManager::Get().FindFiles(Names, *FPaths::Combine(Folder, Pattern), true, false);
			for (const FString& Name : Names)
			{
				const FString Path = FPaths::Combine(Folder, Name);
				Found.Add({ Path, IFileManager::Get().GetTimeStamp(*Path) });
			}
		}
	}
	Found.Sort([](const FPicture& A, const FPicture& B) { return A.Time > B.Time; });
	if (Found.Num() > Max)
	{
		Found.SetNum(Max);
	}
	return Found;
}

FString AWTAGalleryWallActor::CaptionFor(const FString& File, const FDateTime& Time)
{
	FString Caption;
	const FString Beside = FPaths::ChangeExtension(File, TEXT("txt"));
	if (FFileHelper::LoadFileToString(Caption, *Beside))
	{
		Caption = Caption.TrimStartAndEnd();
	}
	if (Caption.IsEmpty())
	{
		Caption = NameFromFile(File);
	}
	static const TCHAR* Months[] = { TEXT("January"), TEXT("February"), TEXT("March"), TEXT("April"), TEXT("May"), TEXT("June"),
		TEXT("July"), TEXT("August"), TEXT("September"), TEXT("October"), TEXT("November"), TEXT("December") };
	const FDateTime Local = Time;
	return FString::Printf(TEXT("%s\n%d %s %d"), *Caption, Local.GetDay(), Months[FMath::Clamp(Local.GetMonth() - 1, 0, 11)], Local.GetYear());
}

void AWTAGalleryWallActor::ReadRow()
{
	Super::ReadRow();
	Label = FText::Format(FText::FromString(TEXT("{0} · {1}")), Title, FText::AsNumber(Hung));
	ViewSpot.Location = GetActorLocation() + GetActorForwardVector() * 300.f + FVector(0.f, 0.f, 162.f - FloorBelowCm);
	ViewSpot.Yaw = GetActorRotation().Yaw + 180.f;
	ViewSpot.Pitch = -2.f;
	ViewSpot.bValid = true;
}

void AWTAGalleryWallActor::BeginPlay()
{
	Super::BeginPlay();
	Refresh();
}

void AWTAGalleryWallActor::Clear()
{
	for (USceneComponent* Comp : Made)
	{
		if (Comp != nullptr)
		{
			Comp->DestroyComponent();
		}
	}
	Made.Reset();
	Textures.Reset();
	Hung = 0;
}

UStaticMeshComponent* AWTAGalleryWallActor::MakePlane(const FVector& Local, float WidthCm, float HeightCm, float OutCm, UMaterialInterface* Material, UTexture2D* Texture, const FLinearColor& Colour)
{
	if (PlaneMesh == nullptr || Material == nullptr)
	{
		return nullptr;
	}
	UStaticMeshComponent* Comp = NewObject<UStaticMeshComponent>(this);
	Comp->SetStaticMesh(PlaneMesh);
	Comp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Comp->SetCastShadow(false);
	Comp->SetupAttachment(GetRootComponent());
	Comp->SetRelativeLocationAndRotation(Local + FVector(OutCm, 0.f, 0.f), PlaneOnWall);
	Comp->SetRelativeScale3D(FVector(WidthCm / 100.f, HeightCm / 100.f, 1.f));
	UMaterialInstanceDynamic* Mid = UMaterialInstanceDynamic::Create(Material, this);
	if (Mid != nullptr)
	{
		if (Texture != nullptr)
		{
			Mid->SetTextureParameterValue(TEXT("BaseColorTexture"), Texture);
			Mid->SetScalarParameterValue(TEXT("Luminance"), 0.8f);
			Mid->SetVectorParameterValue(TEXT("BaseColorFactor"), FLinearColor::White);
		}
		else
		{
			Mid->SetVectorParameterValue(TEXT("Color"), Colour);
		}
		Comp->SetMaterial(0, Mid);
	}
	Comp->RegisterComponent();
	Made.Add(Comp);
	return Comp;
}

UTextRenderComponent* AWTAGalleryWallActor::MakeText(const FVector& Local, const FString& Text, float SizeCm, const FLinearColor& Colour)
{
	UTextRenderComponent* Comp = NewObject<UTextRenderComponent>(this);
	Comp->SetupAttachment(GetRootComponent());
	Comp->SetRelativeLocationAndRotation(Local + FVector(3.f, 0.f, 0.f), FRotator::ZeroRotator);   // a text render faces its +X
	Comp->SetText(FText::FromString(Text));
	Comp->SetWorldSize(SizeCm);
	Comp->SetTextRenderColor(Colour.ToFColor(true));
	Comp->SetHorizontalAlignment(EHTA_Center);
	Comp->SetVerticalAlignment(EVRTA_TextTop);
	Comp->SetCastShadow(false);
	Comp->RegisterComponent();
	Made.Add(Comp);
	return Comp;
}

int32 AWTAGalleryWallActor::Refresh()
{
	Clear();
	if (UnlitMaterial == nullptr)
	{
		UnlitMaterial = Cast<UMaterialInterface>(FSoftObjectPath(UnlitPath).TryLoad());
	}
	const TArray<FPicture> Pictures = FindPictures(FMath::Max(MaxPictures, 1));

	// The title plate above the row.
	MakePlane(FVector(0.f, 0.f, RowHeightCm + PictureHeightCm / 2.f + 46.f), 190.f, 22.f, 1.f, PlainMaterial, nullptr, BrassColour);
	MakeText(FVector(0.f, 0.f, RowHeightCm + PictureHeightCm / 2.f + 54.f), Title.ToString().ToUpper(), 9.f, InkColour);

	if (Pictures.Num() == 0 || UnlitMaterial == nullptr)
	{
		MakePlane(FVector(0.f, 0.f, RowHeightCm), 240.f, 90.f, 1.f, PlainMaterial, nullptr, MatColour);
		MakeText(FVector(0.f, 0.f, RowHeightCm + 24.f), TEXT("Your pictures hang here.\nPress P anywhere on the campus\nfor a postcard of where you stand."), 8.f, InkColour);
		if (UnlitMaterial == nullptr)
		{
			UE_LOG(LogWTA, Warning, TEXT("%s: %s is missing (run the lighting step); nothing hangs"), *GetName(), UnlitPath);
		}
		ReadRow();
		return 0;
	}

	// Load, measure, fit the row to the wall.
	struct FHung { UTexture2D* Texture; float Width; FString Caption; };
	TArray<FHung> Row;
	for (const FPicture& P : Pictures)
	{
		UTexture2D* Texture = FImageUtils::ImportFileAsTexture2D(P.File);
		if (Texture == nullptr)
		{
			UE_LOG(LogWTA, Warning, TEXT("%s: could not read %s"), *GetName(), *P.File);
			continue;
		}
		Textures.Add(Texture);
		const float Aspect = Texture->GetSizeY() > 0 ? float(Texture->GetSizeX()) / float(Texture->GetSizeY()) : 1.5f;
		Row.Add({ Texture, PictureHeightCm * Aspect, CaptionFor(P.File, P.Time) });
	}
	if (Row.Num() == 0)
	{
		ReadRow();
		return 0;
	}
	float Total = GapCm * (Row.Num() - 1);
	for (const FHung& H : Row)
	{
		Total += H.Width;
	}
	const float Fit = Total > WallWidthCm ? WallWidthCm / Total : 1.f;
	const float Height = PictureHeightCm * Fit;

	// Newest in the middle, then out to either side: ... 3 1 0 2 4 ...
	TArray<int32> Left, Right;
	for (int32 i = 0; i < Row.Num(); ++i)
	{
		if (i % 2 == 1) { Left.Insert(i, 0); }
		else            { Right.Add(i); }
	}
	TArray<int32> Order = Left;
	Order.Append(Right);
	float Cursor = -Total * Fit / 2.f;
	for (const int32 Index : Order)
	{
		const FHung& H = Row[Index];
		const float W = H.Width * Fit;
		const float Centre = Cursor + W / 2.f;
		// Along the wall is the actor's -Y when you face it from +X, so the first picture is on the viewer's left.
		const FVector At(0.f, -Centre, RowHeightCm);
		MakePlane(At, W + 2.f * MatCm * Fit, Height + 2.f * MatCm * Fit, 1.5f, PlainMaterial, nullptr, MatColour);
		MakePlane(At, W, Height, 2.5f, UnlitMaterial, H.Texture, FLinearColor::White);
		MakeText(At - FVector(0.f, 0.f, Height / 2.f + MatCm * Fit + 4.f), H.Caption, 6.f * FMath::Max(Fit, 0.75f), InkColour);
		Cursor += W + GapCm * Fit;
	}
	Hung = Row.Num();
	ReadRow();
	UE_LOG(LogWTA, Display, TEXT("WTA gallery wall %s: %d pictures"), *GetName(), Hung);
	return Hung;
}

void AWTAGalleryWallActor::Interact_Implementation(AWTAPlayerController* Controller)
{
	const int32 Before = Hung;
	const int32 Now = Refresh();
	if (Controller != nullptr)
	{
		const FString Message = Now == 0
			? TEXT("Nothing hangs here yet. Press P anywhere on the campus for a postcard; it will appear on this wall.")
			: (Now > Before ? FString::Printf(TEXT("%d new picture%s hung. Press P anywhere for another."), Now - Before, Now - Before == 1 ? TEXT("") : TEXT("s"))
			                : FString::Printf(TEXT("%d picture%s on the wall, the newest in the middle. Press P anywhere for another."), Now, Now == 1 ? TEXT("") : TEXT("s")));
		Controller->ShowToast(FText::FromString(Message), 5.f);
	}
}
