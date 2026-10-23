# VR mode

Walk the Archive in a PC VR headset through OpenXR (roadmap idea 17): Quest over Link or Air Link, Steam Link, or any
SteamVR / OpenXR headset. The same Windows build runs on a desktop and in a headset; nothing changes for desktop
players.

## Getting into VR

1. Install the headset's PC runtime and make it the active OpenXR runtime: the **Meta Quest Link** app (Quest over a
   cable or Air Link) or **SteamVR** (any SteamVR headset, Quest through Steam Link). Put the headset on and connect it.
2. Start Walk the Archive with `-vr` (it starts in the headset), or start it as usual and choose **Enter VR** in the
   menu (Esc); the item shows when a headset is connected. **Leave VR** in the menu goes back to the desktop.

Lumen and Nanite in VR are experimental in Unreal 5.8 (PC, DX12, deferred renderer only): choose the *Performance*
graphics preset in the menu if the headset stutters.

## In the headset

| Hand | Control | Does |
|---|---|---|
| Left | thumbstick | walk, where you look |
| Right | thumbstick left / right | turn 30 degrees |
| Right | trigger | point and pull: open what the laser is on (an exhibit, a book, a seat, a staff member), press a button on a card, or, on the floor, step there |
| Right | thumbstick up / down | scroll the card the laser is on |
| Right | A (Index: A, Vive: trackpad) | the tour's next stop |
| Right | B | back: close the card, or stand up |
| Left | menu | the menu |
| Left | raise it | the guide tablet: the room you are in, your badges, the tour's stop with its buttons, the latest message |

Cards (exhibits, books, staff chat, the visit card, the menu) open on a screen in front of you, at reading distance;
the laser presses their buttons. Long walks (a tour stop, a place from the map) are a short fade rather than a walk.
Sitting down puts your eyes at a seated height whatever your own height. Text entry (typed chat questions, a visit
name) waits for the headset's keyboard: the chat's suggested questions and every button work.

## How it is built (no module beyond the contract's list)

The game module does not link the headset modules (a changed module list rebuilds the build rules, which Smart App
Control may block on this PC), so the XR pieces are reached through Unreal's reflection, all of it in `XR/WTAXR`:

- `UHeadMountedDisplayFunctionLibrary` (XRBase plugin, `/Script/XRBase.HeadMountedDisplayFunctionLibrary`):
  `IsHeadMountedDisplayConnected`, `IsHeadMountedDisplayEnabled`, `EnableHMD`, `SetTrackingOrigin` (LocalFloor),
  `GetHMDDeviceName`, called by name with `ProcessEvent`.
- `UMotionControllerComponent` (`/Script/HeadMountedDisplay.MotionControllerComponent`): made with `NewObject` from
  its class, `MotionSource` set by name (`LeftGrip`, `RightAim`).
- The OpenXR controller keys are InputCore's (`EKeys::OculusTouch_*`, `ValveIndex_*`, `MixedReality_*`, `Vive_*`).
- The rest is UMG and Engine: `UWidgetComponent` screens, `UWidgetInteractionComponent` on the right hand.

`AWTACharacter` in VR: `VROrigin` on the floor under the capsule carries the camera (locked to the headset, no pawn
control rotation) and both hands; each frame the capsule steps under the head (swept, so walls hold it) and the
origin steps back by the same amount; snap turns turn the pawn about the head; the left stick walks by the head's yaw.
`AWTAPlayerController` in VR puts its widgets on two world-space screens instead of the viewport (`AWTAVRScreenActor`
hosting `UWTAVRRootWidget`): the card screen in front of the head (shown while a card, the chat, the menu or the visit
card is open) and the guide tablet on the left hand (the HUD). The right hand's laser drives both the world
(`UWTAInteractionComponent::RaySource`) and the UI (`UWTAVRPointer`).

`-vrsim` runs the same VR presentation on a desktop without a headset (the hands ride in front of the camera, the
mouse looks and clicks): the play test's `vr` phase uses it.

## Not yet

- Rides in VR (the coaster, the Sky Drop and the dive keep the desktop view for now; the ride card says so).
- Hand tracking, grabbing props, a seated / standing height calibration, a comfort vignette.
- A standalone Quest build: the Quest has no Lumen or Nanite, so it is a separate, reduced build (`docs/DELIVERY.md`).
