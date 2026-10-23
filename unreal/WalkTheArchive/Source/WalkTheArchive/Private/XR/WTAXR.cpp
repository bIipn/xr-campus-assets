// Walk the Archive - the headset, reached through Unreal's reflection (see XR/WTAXR.h).

#include "XR/WTAXR.h"
#include "Core/WTALog.h"
#include "Components/SceneComponent.h"
#include "InputMappingContext.h"
#include "Misc/CommandLine.h"
#include "CoreGlobals.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/Parse.h"
#include "UObject/Class.h"
#include "UObject/StructOnScope.h"
#include "UObject/UObjectGlobals.h"
#include "UObject/UnrealType.h"

namespace
{
	bool GPresentationActive = false;
	bool GGameBindings = false;

	/** The comfort options' section in GameUserSettings.ini (the player's own settings, not the progress save). */
	const TCHAR* ComfortSection = TEXT("/Script/WalkTheArchive.VRComfort");

	bool ComfortValue(const TCHAR* Key, bool bDefault)
	{
		bool bValue = bDefault;
		if (GConfig != nullptr)
		{
			GConfig->GetBool(ComfortSection, Key, bValue, GGameUserSettingsIni);
		}
		return bValue;
	}

	void SetComfortValue(const TCHAR* Key, bool bValue)
	{
		if (GConfig != nullptr)
		{
			GConfig->SetBool(ComfortSection, Key, bValue, GGameUserSettingsIni);
			GConfig->Flush(false, GGameUserSettingsIni);
		}
	}

	/** A class of a module the game does not link, found by its script path (loaded with the module or not at all). */
	UClass* ScriptClass(const TCHAR* Path)
	{
		UClass* Class = FindObject<UClass>(nullptr, Path);
		if (Class == nullptr)
		{
			Class = LoadObject<UClass>(nullptr, Path, nullptr, LOAD_Quiet | LOAD_NoWarn);
		}
		return Class;
	}

	UClass* LibraryClass()
	{
		static TWeakObjectPtr<UClass> Cached;
		if (!Cached.IsValid())
		{
			Cached = ScriptClass(TEXT("/Script/XRBase.HeadMountedDisplayFunctionLibrary"));
		}
		return Cached.Get();
	}

	/** Calls Library's static function Name: Setup fills its parameters, Read reads them (and the return value) after
	    the call. False when the function is not there. */
	bool CallOn(UClass* Library, const TCHAR* Name, TFunctionRef<void(UFunction&, uint8*)> Setup, TFunctionRef<void(UFunction&, uint8*)> Read)
	{
		UFunction* Function = Library != nullptr ? Library->FindFunctionByName(FName(Name)) : nullptr;
		if (Function == nullptr)
		{
			return false;
		}
		FStructOnScope Params(Function);
		Setup(*Function, Params.GetStructMemory());
		Library->GetDefaultObject()->ProcessEvent(Function, Params.GetStructMemory());
		Read(*Function, Params.GetStructMemory());
		return true;
	}

	bool CallLibrary(const TCHAR* Name, TFunctionRef<void(UFunction&, uint8*)> Setup, TFunctionRef<void(UFunction&, uint8*)> Read)
	{
		return CallOn(LibraryClass(), Name, Setup, Read);
	}

	bool ReturnedTrue(const UFunction& Function, const uint8* Params)
	{
		const FBoolProperty* Return = CastField<FBoolProperty>(Function.GetReturnProperty());
		return Return != nullptr && Return->GetPropertyValue_InContainer(Params);
	}

	bool CallForBool(const TCHAR* Name)
	{
		bool bResult = false;
		CallLibrary(Name, [](UFunction&, uint8*) {}, [&bResult](UFunction& Function, uint8* Params) { bResult = ReturnedTrue(Function, Params); });
		return bResult;
	}
}

namespace WTAXR
{
	bool IsHeadsetConnected()
	{
		return CallForBool(TEXT("IsHeadMountedDisplayConnected"));
	}

	bool IsHeadsetEnabled()
	{
		return CallForBool(TEXT("IsHeadMountedDisplayEnabled"));
	}

	bool EnableHeadset(bool bEnable)
	{
		bool bResult = false;
		const bool bCalled = CallLibrary(TEXT("EnableHMD"),
			[bEnable](UFunction& Function, uint8* Params)
			{
				if (FBoolProperty* Arg = CastField<FBoolProperty>(Function.FindPropertyByName(TEXT("bEnable"))))
				{
					Arg->SetPropertyValue_InContainer(Params, bEnable);
				}
			},
			[&bResult](UFunction& Function, uint8* Params) { bResult = ReturnedTrue(Function, Params); });
		UE_LOG(LogWTA, Log, TEXT("WTA_VR EnableHMD(%s): %s"), bEnable ? TEXT("true") : TEXT("false"),
			bCalled ? (bResult ? TEXT("took") : TEXT("refused")) : TEXT("no XR library"));
		return bCalled && bResult;
	}

	bool BeginSession(UInputMappingContext* Bindings)
	{
		// UOpenXRInputFunctionLibrary::BeginXRSession(const TSet<UInputMappingContext*>&): attaches the contexts to the
		// OpenXR input plugin, then EnableHMD(true).
		UClass* Library = ScriptClass(TEXT("/Script/OpenXRInput.OpenXRInputFunctionLibrary"));
		UFunction* Function = Library != nullptr ? Library->FindFunctionByName(TEXT("BeginXRSession")) : nullptr;
		if (Function == nullptr || Bindings == nullptr)
		{
			UE_LOG(LogWTA, Warning, TEXT("WTA_VR no OpenXR input library: the headset starts without the game's controller bindings"));
			return EnableHeadset(true);
		}
		bool bResult = false;
		CallOn(Library, TEXT("BeginXRSession"),
			[Bindings](UFunction& Fn, uint8* Params)
			{
				if (FSetProperty* Contexts = CastField<FSetProperty>(Fn.FindPropertyByName(TEXT("InputMappingContexts"))))
				{
					FScriptSetHelper Set(Contexts, Contexts->ContainerPtrToValuePtr<void>(Params));
					UInputMappingContext* Element = Bindings;
					Set.AddElement(&Element);
				}
			},
			[&bResult](UFunction& Fn, uint8* Params) { bResult = ReturnedTrue(Fn, Params); });
		UE_LOG(LogWTA, Log, TEXT("WTA_VR BeginXRSession with the VR controller bindings: %s"), bResult ? TEXT("took") : TEXT("refused"));
		GGameBindings = GGameBindings || bResult;
		return bResult;
	}

	bool HasGameBindings()
	{
		return GGameBindings;
	}

	void UseFloorTracking()
	{
		// EHMDTrackingOrigin::LocalFloor (5.8: View 0, LocalFloor 1, Local 2, Stage 3); the parameter is a byte enum.
		CallLibrary(TEXT("SetTrackingOrigin"),
			[](UFunction& Function, uint8* Params)
			{
				if (FByteProperty* Arg = CastField<FByteProperty>(Function.FindPropertyByName(TEXT("Origin"))))
				{
					Arg->SetPropertyValue_InContainer(Params, 1);
				}
				else if (FEnumProperty* EnumArg = CastField<FEnumProperty>(Function.FindPropertyByName(TEXT("Origin"))))
				{
					EnumArg->GetUnderlyingProperty()->SetIntPropertyValue(EnumArg->ContainerPtrToValuePtr<void>(Params), static_cast<int64>(1));
				}
			},
			[](UFunction&, uint8*) {});
	}

	FString HeadsetName()
	{
		FName Name = NAME_None;
		CallLibrary(TEXT("GetHMDDeviceName"), [](UFunction&, uint8*) {},
			[&Name](UFunction& Function, uint8* Params)
			{
				if (const FNameProperty* Return = CastField<FNameProperty>(Function.GetReturnProperty()))
				{
					Name = Return->GetPropertyValue_InContainer(Params);
				}
			});
		return Name.IsNone() ? FString(TEXT("none")) : Name.ToString();
	}

	USceneComponent* MakeMotionController(UObject* Owner, FName Name, FName Source)
	{
		UClass* Class = ScriptClass(TEXT("/Script/HeadMountedDisplay.MotionControllerComponent"));
		if (Owner == nullptr || Class == nullptr || !Class->IsChildOf(USceneComponent::StaticClass()))
		{
			UE_LOG(LogWTA, Warning, TEXT("WTA_VR no MotionControllerComponent class: the hands stay put"));
			return nullptr;
		}
		USceneComponent* Controller = NewObject<USceneComponent>(Owner, Class, Name);
		if (FNameProperty* Property = FindFProperty<FNameProperty>(Class, TEXT("MotionSource")))
		{
			Property->SetPropertyValue_InContainer(Controller, Source);
		}
		return Controller;
	}

	bool IsHeadsetRequested()
	{
		return FParse::Param(FCommandLine::Get(), TEXT("headset"));
	}

	bool IsSimulationRequested()
	{
		return FParse::Param(FCommandLine::Get(), TEXT("vrsim"));
	}

	bool IsPresentationActive()
	{
		return GPresentationActive;
	}

	void SetPresentationActive(bool bOn)
	{
		GPresentationActive = bOn;
	}

	bool IsComfortTunnel()
	{
		return ComfortValue(TEXT("ComfortTunnel"), true);
	}

	void SetComfortTunnel(bool bOn)
	{
		SetComfortValue(TEXT("ComfortTunnel"), bOn);
	}

	bool IsSeatedPlay()
	{
		return ComfortValue(TEXT("SeatedPlay"), false);
	}

	void SetSeatedPlay(bool bOn)
	{
		SetComfortValue(TEXT("SeatedPlay"), bOn);
	}
}
