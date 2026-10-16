// Walk the Archive - the guided tour.

#include "Systems/WTATourSubsystem.h"
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

void UWTATourSubsystem::Start()
{
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
			PC->ShowToast(FText::FromString(TEXT("That's the end of the tour. Explore on your own.")), 0.f);
		}
		End();
		return;
	}
	ShowStop(Index + 1);
}

void UWTATourSubsystem::Back()
{
	if (!IsTouring())
	{
		return;
	}
	ShowStop(FMath::Max(0, Index - 1));
}

void UWTATourSubsystem::End()
{
	if (!IsTouring())
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

	const UWTAContentSubsystem* Content = GetGameInstance() ? GetGameInstance()->GetSubsystem<UWTAContentSubsystem>() : nullptr;
	const FWTATourStopRow* Row = Content ? Content->FindTourStop(StopIds[Index]) : nullptr;
	if (Row != nullptr)
	{
		// Exhibit stops carry no view of their own; stand where the exhibit's View says.
		FWTAView View = Row->View;
		if (!View.bValid && !Row->ItemId.IsNone())
		{
			if (const FWTAExhibitRow* Exhibit = Content->FindExhibit(Row->ItemId))
			{
				View = Exhibit->View;
			}
		}
		if (AWTAPlayerController* PC = ControllerOf(GetGameInstance()))
		{
			PC->GoToView(View, true);
		}
		UE_LOG(LogWTA, Log, TEXT("Tour: stop %d of %d (%s)"), Index + 1, StopIds.Num(), *Row->Title.ToString());
	}
	OnTourChanged.Broadcast(Index);
}

void UWTATourSubsystem::CacheStops()
{
	const UWTAContentSubsystem* Content = GetGameInstance() ? GetGameInstance()->GetSubsystem<UWTAContentSubsystem>() : nullptr;
	StopIds = Content ? Content->GetTourStopIds() : TArray<FName>();
}
