// Walk the Archive - the headset, reached through Unreal's reflection.
//
// The game module does not link the XR modules (a changed module list rebuilds the build rules, which Smart App
// Control may block on the development PC; docs/VR_MODE.md). Everything VR needs from them is called by name:
// UHeadMountedDisplayFunctionLibrary (the XRBase plugin) and UOpenXRInputFunctionLibrary (the OpenXR plugin) through
// ProcessEvent, and UMotionControllerComponent (the HeadMountedDisplay module) made from its class with its
// MotionSource set by name. Without them (no XR plugin), every call answers "no headset" and the game stays on the
// desktop.
//
// OpenXR builds a session's controller bindings once, when the session starts, from the mapping contexts it is
// given: BeginSession hands it the game's VR mapping context and starts the headset in one go. The engine's own -vr
// switch starts the headset before the game exists, so the controllers would have no bindings; the game's -headset
// switch goes in through BeginSession instead.

#pragma once

#include "CoreMinimal.h"

class UInputMappingContext;
class UObject;
class USceneComponent;

namespace WTAXR
{
	/** A headset is plugged in and its OpenXR runtime is running (the menu's Enter VR shows). */
	WALKTHEARCHIVE_API bool IsHeadsetConnected();

	/** The game is drawing to the headset. */
	WALKTHEARCHIVE_API bool IsHeadsetEnabled();

	/** Start or stop drawing to the headset; true when it took. */
	WALKTHEARCHIVE_API bool EnableHeadset(bool bEnable);

	/** Start the headset with Bindings as the session's controller bindings (OpenXR reads them only as a session
	    starts); without the OpenXR input library, the headset starts without them. True when the headset started. */
	WALKTHEARCHIVE_API bool BeginSession(UInputMappingContext* Bindings);

	/** The running headset session was started by BeginSession with the game's bindings (this run of the game). */
	WALKTHEARCHIVE_API bool HasGameBindings();

	/** Floor-level tracking: z 0 of the tracking space is the floor the visitor stands on. */
	WALKTHEARCHIVE_API void UseFloorTracking();

	/** The headset system's name (e.g. "OpenXR"), or "none". */
	WALKTHEARCHIVE_API FString HeadsetName();

	/** A motion controller following Source ("LeftGrip", "RightAim"), made in Owner and not yet registered; null when
	    the XR module is not there. */
	WALKTHEARCHIVE_API USceneComponent* MakeMotionController(UObject* Owner, FName Name, FName Source);

	/** -headset: go into the headset as the game starts. */
	WALKTHEARCHIVE_API bool IsHeadsetRequested();

	/** -vrsim: the VR presentation on a desktop without a headset (the hands ride in front of the camera, the mouse
	    looks and clicks). */
	WALKTHEARCHIVE_API bool IsSimulationRequested();

	/** The VR presentation is on (a headset or -vrsim): world UI that would go to the viewport draws in the world
	    instead (the people's name tags in a guided visit). AWTAPlayerController sets it. */
	WALKTHEARCHIVE_API bool IsPresentationActive();
	WALKTHEARCHIVE_API void SetPresentationActive(bool bOn);
}
