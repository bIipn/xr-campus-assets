// Walk the Archive - graphics presets.

#include "Systems/WTAGraphicsLibrary.h"
#include "Core/WTAText.h"
#include "Core/WTALog.h"
#include "Engine/Engine.h"
#include "GameFramework/GameUserSettings.h"

namespace
{
	UGameUserSettings* UserSettings()
	{
		return GEngine ? GEngine->GetGameUserSettings() : nullptr;
	}
}

void UWTAGraphicsLibrary::ApplyQualityPreset(int32 Level)
{
	UGameUserSettings* Settings = UserSettings();
	if (Settings == nullptr)
	{
		return;
	}
	const int32 Clamped = FMath::Clamp(Level, 0, 4);
	Settings->SetOverallScalabilityLevel(Clamped);
	Settings->ApplySettings(false);
	Settings->SaveSettings();
	UE_LOG(LogWTA, Log, TEXT("Graphics preset %d (%s) applied"), Clamped, *GetQualityPresetLabel(Clamped).ToString());
}

void UWTAGraphicsLibrary::RunAutoDetect()
{
	UGameUserSettings* Settings = UserSettings();
	if (Settings == nullptr)
	{
		return;
	}
	// The benchmark takes a moment (it renders a few test frames); the menu calls this from a button press.
	Settings->RunHardwareBenchmark();
	Settings->ApplyHardwareBenchmarkResults();
	Settings->ApplySettings(false);
	Settings->SaveSettings();
	UE_LOG(LogWTA, Log, TEXT("Graphics auto-detect done: overall level %d"), Settings->GetOverallScalabilityLevel());
}

int32 UWTAGraphicsLibrary::GetQualityPreset()
{
	const UGameUserSettings* Settings = UserSettings();
	return Settings ? Settings->GetOverallScalabilityLevel() : -1;
}

FText UWTAGraphicsLibrary::GetQualityPresetLabel(int32 Level)
{
	switch (Level)
	{
	case 0: return WTAText(TEXT("Low"));
	case 1: return WTAText(TEXT("Medium"));
	case 2: return WTAText(TEXT("High"));
	case 3: return WTAText(TEXT("Epic"));
	case 4: return WTAText(TEXT("Cinematic"));
	default: return WTAText(TEXT("Custom"));
	}
}
