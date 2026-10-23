// Walk the Archive - the Lost Stories wall.

#include "World/WTAStoryWallActor.h"
#include "Components/BoxComponent.h"
#include "Components/WidgetComponent.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "Core/WTAText.h"
#include "Engine/World.h"
#include "Materials/MaterialInterface.h"
#include "Systems/WTAStoriesSubsystem.h"
#include "UI/WTAStoryBoardWidget.h"
#include "World/WTAAttractComponent.h"

AWTAStoryWallActor::AWTAStoryWallActor()
{
	PickExtent = FVector(40.f, 120.f, 60.f);
	Board = CreateDefaultSubobject<UWidgetComponent>(TEXT("Board"));
	Board->SetupAttachment(RootComponent);
	Board->SetWidgetSpace(EWidgetSpace::World);
	Board->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Board->SetCastShadow(false);
	Board->SetDrawAtDesiredSize(false);
	Board->SetPivot(FVector2D(0.5f, 0.5f));
	Board->SetBlendMode(EWidgetBlendMode::Masked);
	Board->SetTwoSided(true);                            // drawn from both sides: the board's back is against the wall anyway
	Board->SetWindowFocusable(false);
	BoardMaterial = TSoftObjectPtr<UMaterialInterface>(FSoftObjectPath(TEXT("/Game/WTA/Materials/M_WTA_WidgetLit.M_WTA_WidgetLit")));
	if (Attract != nullptr)
	{
		Attract->bEnabled = false;
	}
}

void AWTAStoryWallActor::BeginPlay()
{
	Super::BeginPlay();
	const FVector2D Design = UWTAStoryBoardWidget::DesignSize();
	Board->SetDrawSize(Design);
	// The widget is drawn in the component's Y-Z plane, facing +X (out of the wall), one unit a pixel: scale it to
	// the board, a centimetre proud of it.
	Board->SetRelativeLocationAndRotation(FVector(1.f, 0.f, 0.f), FRotator::ZeroRotator);
	Board->SetRelativeScale3D(FVector(1.f, BoardWidthCm / Design.X, BoardHeightCm / Design.Y));
	if (UMaterialInterface* Paper = BoardMaterial.LoadSynchronous())
	{
		Board->SetMaterial(0, Paper);                       // the component makes its instance of it and sets SlateUI
	}
	else
	{
		UE_LOG(LogWTA, Warning, TEXT("WTA_STORY no board material %s: the cards draw unlit (the lighting step builds it)"), *BoardMaterial.ToString());
	}
	Board->SetTintColorAndOpacity(FLinearColor(Brightness, Brightness, Brightness, 1.f));
	Board->SetRedrawTime(0.25f);
	Face = CreateWidget<UWTAStoryBoardWidget>(GetWorld(), UWTAStoryBoardWidget::StaticClass());
	Board->SetWidget(Face);
	if (UWTAStoriesSubsystem* Stories = UWTAStoriesSubsystem::Get(this))
	{
		Stories->OnStoriesChanged.AddDynamic(this, &AWTAStoryWallActor::HandleStoriesChanged);
		Stories->OnBoothChanged.AddDynamic(this, &AWTAStoryWallActor::HandleStoriesChanged);
	}
	Refresh();
}

void AWTAStoryWallActor::HandleStoriesChanged()
{
	Refresh();
}

void AWTAStoryWallActor::Refresh()
{
	const UWTAStoriesSubsystem* Stories = UWTAStoriesSubsystem::Get(this);
	if (Face == nullptr || Stories == nullptr)
	{
		return;
	}
	const TArray<FWTAStory> List = Stories->GetWallStories();
	TSet<FString> Writing;
	FString PlayingId;
	for (const FWTAStory& Story : List)
	{
		if (Stories->IsWritingDown(Story.Id))
		{
			Writing.Add(Story.Id);
		}
		if (Stories->IsPlaying(Story.Id))
		{
			PlayingId = Story.Id;
		}
	}
	Face->ShowStories(List, PlayingId, Writing);
	Board->RequestRenderUpdate();
	ReadRow();
}

int32 AWTAStoryWallActor::NumCards() const
{
	return Face != nullptr ? Face->NumCards() : 0;
}

void AWTAStoryWallActor::ReadRow()
{
	Super::ReadRow();
	const UWTAStoriesSubsystem* Stories = UWTAStoriesSubsystem::Get(this);
	const int32 Count = Stories != nullptr ? Stories->GetWallStories().Num() : 0;
	Label = FText::Format(WTAText(TEXT("Stories from this place · {0}")), FText::AsNumber(Count));
	// Where to stand to read it: 2.4 m out, the eye 162 cm over the floor found under that spot (the builders hang a
	// board's middle 1.6 m up, so that is the guess when nothing is found), facing the board.
	const FVector Spot = GetActorLocation() + GetActorForwardVector() * 240.f;
	float FloorZ = GetActorLocation().Z - 160.f;
	if (const UWorld* World = GetWorld())
	{
		FHitResult Hit;
		const FCollisionQueryParams Params(SCENE_QUERY_STAT(WTAStoryWallFloor), false, this);
		if (World->LineTraceSingleByChannel(Hit, Spot + FVector(0.f, 0.f, 40.f), Spot - FVector(0.f, 0.f, 400.f), ECC_Visibility, Params))
		{
			FloorZ = Hit.ImpactPoint.Z;
		}
	}
	ViewSpot.Location = FVector(Spot.X, Spot.Y, FloorZ + 162.f);
	ViewSpot.Yaw = GetActorRotation().Yaw + 180.f;
	ViewSpot.Pitch = -3.f;
	ViewSpot.bValid = true;
}

FText AWTAStoryWallActor::GetInteractLabel_Implementation() const
{
	const UWTAStoriesSubsystem* Stories = UWTAStoriesSubsystem::Get(this);
	if (Stories != nullptr && Stories->IsPlaying() && !Stories->IsPlaying(TEXT("take")))
	{
		return WTAText(TEXT("Stop the story"));
	}
	return Label;
}

void AWTAStoryWallActor::Interact_Implementation(AWTAPlayerController* Controller)
{
	UWTAStoriesSubsystem* Stories = UWTAStoriesSubsystem::Get(this);
	if (Stories != nullptr && Stories->IsPlaying() && !Stories->IsPlaying(TEXT("take")))
	{
		Stories->StopPlayback();
		return;
	}
	if (Stories != nullptr)
	{
		Stories->Refresh();                                  // a librarian may have put new ones up
	}
	if (Controller != nullptr)
	{
		Controller->OpenStories(NAME_None);
	}
}
