// Walk the Archive - graphics presets for the menu (Low, Medium, High, Epic, Cinematic, Auto).
// Wraps UGameUserSettings: SetOverallScalabilityLevel + ApplySettings(false) + SaveSettings, and the hardware
// benchmark (RunHardwareBenchmark + ApplyHardwareBenchmarkResults) for Auto.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "WTAGraphicsLibrary.generated.h"

UCLASS()
class WALKTHEARCHIVE_API UWTAGraphicsLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/** Apply one overall scalability level: 0 Low, 1 Medium, 2 High, 3 Epic, 4 Cinematic (clamped). */
	UFUNCTION(BlueprintCallable, Category = "WTA|Graphics")
	static void ApplyQualityPreset(int32 Level);

	/** Run the hardware benchmark and apply its recommendation. */
	UFUNCTION(BlueprintCallable, Category = "WTA|Graphics")
	static void RunAutoDetect();

	/** The current overall level (0..4), or -1 when the groups differ (custom). */
	UFUNCTION(BlueprintPure, Category = "WTA|Graphics")
	static int32 GetQualityPreset();

	/** "Low" .. "Cinematic", "Custom" for -1. */
	UFUNCTION(BlueprintPure, Category = "WTA|Graphics")
	static FText GetQualityPresetLabel(int32 Level);
};
