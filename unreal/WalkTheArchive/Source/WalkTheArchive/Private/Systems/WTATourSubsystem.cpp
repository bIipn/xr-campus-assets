// Walk the Archive - the guided tour.

#include "Systems/WTATourSubsystem.h"
#include "Core/WTAText.h"
#include "Systems/WTAContentSubsystem.h"
#include "Core/WTAPlayerController.h"
#include "Core/WTALog.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Subsystems/SubsystemCollection.h"

namespace
{
	AWTAPlayerController* ControllerOf(const UGameInstance* GameInstance)
	{
		if (GameInstance == nullptr)
		{
			return nullptr;
		}
		return Cast<AWTAPlayerController>(const_cast<UGameInstance*>(GameInstance)->GetFirstLocalPlayerController());
	}
}

UWTATourSubsystem* UWTATourSubsystem::Get(const UObject* WorldContextObject)
{
	if (WorldContextObject == nullptr || GEngine == nullptr)
	{
		return nullptr;
	}
	const UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull);
	if (World == nullptr)
	{
		return nullptr;
	}
	const UGameInstance* GameInstance = World->GetGameInstance();
	return GameInstance ? GameInstance->GetSubsystem<UWTATourSubsystem>() : nullptr;
}

void UWTATourSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	Collection.InitializeDependency(UWTAContentSubsystem::StaticClass());
	CacheStops();
}

bool UWTATourSubsystem::RefuseWhileFollowing() const
{
	if (!bFollowing)
	{
		return false;
	}
	if (AWTAPlayerController* PC = ControllerOf(GetGameInstance()))
	{
		PC->ShowToast(WTAText(TEXT("Your guide leads the tour. The next stop comes when they move on.")), 0.f);
	}
	return true;
}

void UWTATourSubsystem::Start()
{
	if (RefuseWhileFollowing())
	{
		return;
	}
	CacheStops();
	if (StopIds.Num() == 0)
	{
		UE_LOG(LogWTA, Warning, TEXT("Tour: DT_Tour has no stops"));
		return;
	}
	ShowStop(0);
}

void UWTATourSubsystem::Next()
{
	if (RefuseWhileFollowing())
	{
		return;
	}
	if (!IsTouring())
	{
		Start();
		return;
	}
	if (IsLastStop())
	{
		// The web's last stop: the bar goes away and you are on your own.
		if (AWTAPlayerController* PC = ControllerOf(GetGameInstance()))
		{
			PC->ShowToast(WTAText(TEXT("That's the end of the tour. Explore on your own.")), 0.f);
		}
		End();
		return;
	}
	ShowStop(Index + 1);
}

void UWTATourSubsystem::Back()
{
	if (RefuseWhileFollowing())
	{
		return;
	}
	if (!IsTouring())
	{
		return;
	}
	ShowStop(FMath::Max(0, Index - 1));
}

void UWTATourSubsystem::End()
{
	if (!IsTouring() || RefuseWhileFollowing())
	{
		return;
	}
	Index = -1;
	OnTourChanged.Broadcast(-1);
}

void UWTATourSubsystem::OpenCurrent()
{
	FWTATourStopRow Stop;
	if (!GetCurrentStop(Stop) || Stop.Action.IsNone())
	{
		return;
	}
	if (AWTAPlayerController* PC = ControllerOf(GetGameInstance()))
	{
		PC->RunAction(Stop.Action, Stop.ActionArg);
	}
}

bool UWTATourSubsystem::GetCurrentStop(FWTATourStopRow& OutStop) const
{
	if (!IsTouring() || !StopIds.IsValidIndex(Index))
	{
		return false;
	}
	const UWTAContentSubsystem* Content = GetGameInstance() ? GetGameInstance()->GetSubsystem<UWTAContentSubsystem>() : nullptr;
	const FWTATourStopRow* Row = Content ? Content->FindTourStop(StopIds[Index]) : nullptr;
	if (Row == nullptr)
	{
		return false;
	}
	OutStop = *Row;
	return true;
}

void UWTATourSubsystem::ShowStop(int32 NewIndex)
{
	if (StopIds.Num() == 0)
	{
		return;
	}
	Index = FMath::Clamp(NewIndex, 0, StopIds.Num() - 1);

	FWTAView View;
	if (GetStopView(Index, View))
	{
		if (AWTAPlayerController* PC = ControllerOf(GetGameInstance()))
		{
			PC->GoToView(View, true);
		}
		FWTATourStopRow Row;
		if (GetCurrentStop(Row))
		{
			UE_LOG(LogWTA, Log, TEXT("Tour: stop %d of %d (%s)"), Index + 1, StopIds.Num(), *Row.Title.ToString());
		}
	}
	OnTourChanged.Broadcast(Index);
}

bool UWTATourSubsystem::GetStopView(int32 StopIndex, FWTAView& OutView) const
{
	if (!StopIds.IsValidIndex(StopIndex))
	{
		return false;
	}
	const UWTAContentSubsystem* Content = GetGameInstance() ? GetGameInstance()->GetSubsystem<UWTAContentSubsystem>() : nullptr;
	const FWTATourStopRow* Row = Content ? Content->FindTourStop(StopIds[StopIndex]) : nullptr;
	if (Row == nullptr)
	{
		return false;
	}
	// Exhibit stops carry no view of their own; stand where the exhibit's View says.
	OutView = Row->View;
	if (!OutView.bValid && !Row->ItemId.IsNone())
	{
		if (const FWTAExhibitRow* Exhibit = Content->FindExhibit(Row->ItemId))
		{
			OutView = Exhibit->View;
		}
	}
	return OutView.bValid;
}

void UWTATourSubsystem::FollowStop(int32 NewIndex, const FWTAView& Spot, bool bWalk)
{
	CacheStops();
	if (!StopIds.IsValidIndex(NewIndex))
	{
		return;
	}
	bFollowing = true;
	Index = NewIndex;
	if (AWTAPlayerController* PC = ControllerOf(GetGameInstance()))
	{
		PC->GoToView(Spot, bWalk);
	}
	UE_LOG(LogWTA, Log, TEXT("Tour: following the guide to stop %d of %d"), Index + 1, StopIds.Num());
	OnTourChanged.Broadcast(Index);
}

void UWTATourSubsystem::StopFollowing()
{
	if (!bFollowing)
	{
		return;
	}
	bFollowing = false;
	if (Index >= 0)
	{
		Index = -1;
		OnTourChanged.Broadcast(-1);
	}
}

void UWTATourSubsystem::CacheStops()
{
	const UWTAContentSubsystem* Content = GetGameInstance() ? GetGameInstance()->GetSubsystem<UWTAContentSubsystem>() : nullptr;
	StopIds = Content ? Content->GetTourStopIds() : TArray<FName>();
}
