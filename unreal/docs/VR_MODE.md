# VR mode

Walk the Archive in a PC VR headset through OpenXR (roadmap idea 17): Quest over Link or Air Link, Steam Link, or any
SteamVR / OpenXR headset. The same Windows build runs on a desktop and in a headset; nothing changes for desktop
players.

## Getting into VR

1. Install the headset's PC runtime and make it the active OpenXR runtime: the **Meta Quest Link** app (Quest over a
   cable or Air Link) or **SteamVR** (any SteamVR headset, Quest through Steam Link). Put the headset on and connect it.
2. Start Walk the Archive as usual and choose **Enter VR** in the menu (Esc); the item shows when a headset is
   connected. Or start it with `-headset` to go straight in. **Leave VR** in the menu goes back to the desktop.

Use `-headset`, not the engine's own `-vr`: `-vr` starts the headset before the game exists, and OpenXR only reads a
session's controller bindings as the session starts, so the controllers would do nothing.

Lumen and Nanite in VR are experimental in Unreal 5.8 (PC, DX12, deferred renderer only): choose the *Performance*
graphics preset in the menu if the headset stutters.

## In the headset

| Hand | Control | Does |
|---|---|---|
| Left | thumbstick (Vive: trackpad) | walk, the way you look |
| Right | thumbstick left / right | turn 30 degrees (once per push) |
| Right | trigger | point and pull: press a button on a card, open what the laser is on (an exhibit, a book, a seat, a staff member), close a card by pointing off it, or step to the floor where it points |
| Right | thumbstick up / down | scroll the card the laser is on |
| Right | A (Index: A; Vive, WMR: trackpad click) | the tour's next stop |
| Right | B (WMR, Vive: menu) | back: close the card, stand up from a seat, end the tour, the menu |
| Left | menu (Index: B) | the same as B |
| Left | Y (Index: A) | the places list |
| Left | X | a postcard of the view |

The right hand holds a slim wand with a brass ring; its laser is bone white over plain things and brass over
something it can open or press, and a small label over its dot names what that is. Cards (exhibits, books, staff
chat, the visit card, the menu, a certificate) open on a screen square in front of you at reading distance (1.15 m),
and the HUD (the room, your badges, toasts, captions, the tour bar with its buttons) floats 1.65 m ahead a little
below eye level and turns after you once you look 35 degrees away; it steps aside while a card is open. Both come
nearer, and smaller by as much, when a wall is in the way, so they never go into it. Long walks (a tour stop, a place
from the list, the walk to an exhibit's view spot) are a short fade instead of a walk. Sitting down puts your eyes at
a seated height whatever your own height. In a guided visit the other people's names float over them, facing you.
Text entry (typed chat questions, a visit name) waits for the headset's own keyboard: the chat's suggested questions
and every button work.

## How it is built (no module beyond the contract's list)

The game module does not link the headset modules (a changed module list rebuilds the build rules, which Smart App
Control may block on this PC), so the XR pieces are reached through Unreal's reflection, all of it in `XR/WTAXR`:

- `UHeadMountedDisplayFunctionLibrary` (XRBase plugin, `/Script/XRBase.HeadMountedDisplayFunctionLibrary`):
  `IsHeadMountedDisplayConnected`, `IsHeadMountedDisplayEnabled`, `EnableHMD`, `SetTrackingOrigin` (LocalFloor),
  `GetHMDDeviceName`, called by name with `ProcessEvent`.
- `UOpenXRInputFunctionLibrary::BeginXRSession` (OpenXR plugin): hands OpenXR the game's VR mapping context and starts
  the headset in one go (`WTAXR::BeginSession`).
- `UMotionControllerComponent` (`/Script/HeadMountedDisplay.MotionControllerComponent`): made with `NewObject` from
  its class, `MotionSource` set by name (`LeftGrip`, `RightAim`).
- The OpenXR controller keys are InputCore's (`EKeys::OculusTouch_*`, `ValveIndex_*`, `MixedReality_*`, `Vive_*`), in
  their own mapping context (`IMC_WalkTheArchive_VR`), added only in VR.
- The rest is UMG and Engine: `UWidgetComponent` screens, a `UWidgetInteractionComponent` (Custom hit testing) as the
  screens' pointer.

`UWTAVRRig` (on the player, made by `AWTACharacter::StartVR`): with a headset, an origin on the floor under the capsule
carries the camera (locked to the headset, no pawn control rotation) and both motion controllers; each frame the
capsule steps under the head (swept, so walls hold it) and the origin steps back as far, and the controller's control
rotation follows the head (what the rest of the game reads as where the player looks). Turns and arrivals turn the
body about the head. In the simulation the camera stays as it is and the hands ride low in front of it, the right one
aiming at what the middle of the view is on.

`AWTAPlayerController` in VR puts its widgets on two `AWTAVRScreenActor`s instead of the viewport (`AddToScreen`): the
card screen (Panel, Certificate, Chat, VisitCard, Menu) and the HUD screen, each a `UWidgetComponent` showing a
`UWTAVRRootWidget` that stacks the widgets in their viewport z-order. The cards' scrims go clear so the cards float.
`M_WTA_WidgetScreen` (built by the lighting step, `emissive.py`) draws them: unlit, translucent, display referred (the
widget's colours divided by the eye adaptation, so the campus's physical exposure leaves them as the desktop shows
them), depth tested so the hands and the laser show over them. `UpdateVRPointer` finds what the laser is on every
frame: a screen first (the card screen anywhere on its face, the HUD screen only on a button, found by a ray against
its plane, not collision, so a screen's empty parts never block the laser), then the world (the interaction component
traces along the laser, `SetRayOverride`).

`-vrsim` runs the same VR presentation on a desktop without a headset (the mouse looks and aims, the left button or E
is the trigger, the wheel scrolls): the play test's `vr` phase uses it (`WTAPlayTest vr`), and so can anyone checking
the VR screens on a desktop. `WTAVR [on|sim|off]` in the console switches it.

## Not yet

- Hand tracking, grabbing props, a seated / standing height calibration, a comfort vignette while the stick walks.
- The headset's own keyboard for typed chat questions and visit names.
- A standalone Quest build: the Quest has no Lumen or Nanite, so it is a separate, reduced build (`docs/DELIVERY.md`).
