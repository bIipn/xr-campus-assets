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
| Right | trigger | point and pull: press a button on a card, open what the laser is on (an exhibit, a book, a seat, a staff member), close a card by pointing off it, step to the floor where it points, or bring up the keyboard on a text box |
| Right | thumbstick up / down | scroll the card the laser is on |
| Right | A (Index: A; Vive, WMR: trackpad click) | the tour's next stop |
| Right | B (WMR, Vive: menu) | back: put the keyboard away, close the card, stand up from a seat, end the tour, the menu |
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

Typing: pull the trigger on a text box (a question for the staff, your name in a visit or on a certificate, a Lost
Story's title) and a keyboard comes up under the card, tilted toward you like a lectern's desk; the laser presses its
keys. It shows what you have typed at the top, starts a sentence with a capital, and its Send (Done for a name) does
what Enter does on a desktop: the staff answer the question. B or Hide puts it away; it goes by itself when its card
closes.

Comfort, in the menu while in VR (remembered on the computer, not in the visit's progress):
- **Comfort tunnel** (on unless you turn it off): while the stick walks, the edge of the view darkens into a soft
  tunnel, which eases the swimmy feeling of gliding; it opens again as soon as you stop. Walking about the room and
  the fades of a long move never close it.
- **Seated play** (headset only, off unless you turn it on): for a visitor in a chair. Turning it on measures how
  high your head is now and lifts the view to a standing person's eye height (1.62 m), so the cards, the exhibits and
  the doors are where a standing visitor sees them. Turn it on sitting the way you will play; turn it off to play standing.

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
them), after motion blur so the text stays crisp. The engine draws that pass with no depth buffer, so a screen shows
over everything: the controller keeps the screens in front of walls, the name tags hide behind walls by a line check,
and the laser and its dot (`M_WTA_Overlay`, a higher translucency sort priority) draw after the screens, so the laser
shows on a card it points at. The laser's label and the name tags are sized to their widget (`FitToWidget`), not by
the engine's draw-at-desired-size, which measured them far too tall. `UpdateVRPointer` finds what the laser is on every
frame: a screen first (the card screen anywhere on its face, the HUD screen only on a button, found by a ray against
its plane, not collision, so a screen's empty parts never block the laser), then the world (the interaction component
traces along the laser, `SetRayOverride`).

The keyboard (`UWTAVRKeyboardWidget`) is a third screen, shown by the controller when the trigger lands on a text box
on the card screen (`VRTextBoxAt`: the screen's hit-test path at the laser's pixel, matched against the cards' text
boxes). It types into that box directly (`UEditableTextBox::SetText`), so no Slate focus is involved, and its Enter
broadcasts the box's `OnTextCommitted` with `OnEnter`, which is what the desktop's Enter key does.

The comfort tunnel is `M_WTA_Vignette` (the lighting step, `emissive.py`), a post process on the camera after
tonemapping whose `Amount` the rig eases toward the body's walking speed each frame. Seated play raises the rig's
floor-level origin by the measured lift (`UWTAVRRig::SetSeatedPlay`); both options are `WTAXR` settings kept in
GameUserSettings.ini (`[/Script/WalkTheArchive.VRComfort]`).

`-vrsim` runs the same VR presentation on a desktop without a headset (the mouse looks and aims, the left button or E
is the trigger, the wheel scrolls): the play test's `vr` phase uses it (`WTAPlayTest vr`), and so can anyone checking
the VR screens on a desktop. `WTAVR [on|sim|off]` in the console switches it.

## Not yet

- Hand tracking and grabbing props.
- A standalone Quest build: the Quest has no Lumen or Nanite, so it is a separate, reduced build (`docs/DELIVERY.md`).
- A real headset run: everything above is checked in the desktop simulation (`WTAPlayTest vr`); the development PC
  has no OpenXR runtime yet.
