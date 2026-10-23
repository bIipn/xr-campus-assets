# Walk the Archive (Unreal Engine 5.8) — build contract

Every file in `unreal/` follows this contract. It fixes names, paths, data shapes and entry points so the C++,
the editor Python, the data converter, the tools and the docs agree without talking to each other.
`contract/structs.json` is the machine-readable half (data structs); this file is the rest.
If something here is wrong for UE 5.8, fix it here first, then everywhere it is used.

## 1. Names

| Thing | Value |
|---|---|
| Unreal project folder | `unreal/WalkTheArchive/` |
| Project file | `unreal/WalkTheArchive/WalkTheArchive.uproject`, `"EngineAssociation": "5.8"` |
| Runtime C++ module | `WalkTheArchive` (`Source/WalkTheArchive/`), API macro `WALKTHEARCHIVE_API` |
| Targets | `WalkTheArchive.Target.cs` (Game), `WalkTheArchiveEditor.Target.cs` (Editor); `DefaultBuildSettings = BuildSettingsVersion.Latest`, `IncludeOrderVersion = EngineIncludeOrderVersion.Latest` |
| Class prefix | `WTA` (`AWTAGameMode`, `UWTAContentSubsystem`, `FWTAExhibitRow`, `IWTAInteractable` …). Never `XR` (engine uses that prefix). |
| Content root | `/Game/WTA/` |
| Script name for engine `/Script/` paths | `/Script/WalkTheArchive.<ClassNameWithoutPrefixLetter>` e.g. `/Script/WalkTheArchive.WTAExhibitActor`, struct `/Script/WalkTheArchive.WTAExhibitRow` |

## 2. Units and axes

All positions in data files and in Unreal are **Unreal centimetres, Unreal axes** (X east, Y south, Z up).
The converter does the only conversion, from the web campus (three.js metres, Y up):
`UE = (100·x, 100·z, 100·y)`; yaw from a web yaw (radians, 0 = looking toward −z): `UE_yaw = (−90 − deg(yaw)) mod 360` normalised to (−180, 180];
pitch: `UE_pitch = deg(pitch)`. A web "view" `{x, z, yaw, pitch}` becomes `FWTAView{Location=(100x, 100z, 162), Yaw, Pitch, bValid=true}`.
Every imported mesh in `Pipeline/out/ue/*.glb` is baked in world space: spawn it at (0,0,0), rotation 0, scale 1.
Check on first import: the token mesh `token__t_coaster` (Yard) must sit near the `DT_Tokens` row `t-coaster` location.

## 3. Content paths (created by the editor setup, never committed as .uasset)

| Asset | Path |
|---|---|
| Imported campus meshes | `/Game/WTA/Campus/<Asset>/` for Asset in Museum, WaxIntro, WaxHall, LibraryShell, School, Outside, Yard, OceanDive, ReadingRoom (source `unreal/Pipeline/out/ue/<Asset>.glb`) |
| Exhibit art textures | `/Game/WTA/Art/T_Art_<id>` (id with `-` → `_`), source `unreal/Pipeline/out/campus/art/<id>.png` |
| Data tables | `/Game/WTA/Data/DT_<Table>` (see structs.json `table`), source `unreal/WalkTheArchive/Data/<File>.json` |
| Main level | `/Game/WTA/Maps/L_Campus` (not World Partition: the campus is small; Ocean Dive sits 420 m east in the same level) |
| Materials | `/Game/WTA/Materials/` |
| Characters (MetaHumans) | `/Game/WTA/Characters/<PersonId>/MHC_<PersonId>` (MetaHuman Character) and `BP_<PersonId>` (built actor), one folder per id in `Content/Python/wta_people/people.json` (staff ids and Wax Hall `<sceneId>-<role>`); shared build assets `/Game/WTA/Characters/Common/`, the idle `/Game/WTA/Characters/Common/Anims/AS_WTA_StandIdle` |

## 4. C++ classes (module `WalkTheArchive`)

Headers live in `Source/WalkTheArchive/Public/<Area>/`, sources in `Source/WalkTheArchive/Private/<Area>/`.
Include as `#include "Area/File.h"`. Areas: `Core`, `Data`, `Interaction`, `World`, `Systems`, `UI`.
Module dependencies (Build.cs, public): Core, CoreUObject, Engine, InputCore, EnhancedInput, UMG, Slate, SlateCore,
AIModule, NavigationSystem, DeveloperSettings. Nothing else in phase 0.

### 4.1 Data (`Data/WTATypes.h`)
Every struct in `contract/structs.json`, spelled exactly, all `USTRUCT(BlueprintType)`, rows derive `FTableRowBase`,
every member `UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")` with a default initialiser for numbers/bools.

### 4.2 Settings (`Core/WTASettings.h`)
`UWTASettings : UDeveloperSettings` (`UCLASS(Config = Game, DefaultConfig, meta = (DisplayName = "Walk the Archive"))`),
one `UPROPERTY(Config, EditAnywhere) TSoftObjectPtr<UDataTable>` per table, named after the table without `DT_`
(`Exhibits`, `Books`, `Sources`, `Galleries`, `Subjects`, `Rooms`, `Places`, `Tour`, `Staff`, `StaffRules`, `Facts`,
`Lessons`, `Badges`, `Tokens`, `WaxScenes`, `Stations`, `Rides`), defaulting to `/Game/WTA/Data/DT_<Name>.DT_<Name>`.
Values also written to `Config/DefaultGame.ini` section `[/Script/WalkTheArchive.WTASettings]`.

### 4.3 Game framework (`Core/`)
| Class | Parent | Must have |
|---|---|---|
| `AWTAGameMode` | `AGameModeBase` | DefaultPawnClass = `AWTACharacter`, PlayerControllerClass = `AWTAPlayerController`, HUDClass none |
| `AWTAPlayerController` | `APlayerController` | Builds Enhanced Input **in code** at BeginPlay (NewObject `UInputAction`/`UInputMappingContext`, no assets). PC-game controls: WASD move, mouse look (captured), Shift sprint, Space jump, LMB or E interact with what the crosshair points at, Tab = free cursor (click UI / click floor to walk), T tour next, Esc close top panel / open menu, M map/places, Enter = chat focus, P = a framed postcard of the view written to `Saved/Postcards/`. Gamepad: left stick move, right stick look, A jump, X interact, B back, Y postcard. Owns `UWTAInteractionComponent* Interaction`. `UFUNCTION(BlueprintCallable) void GoToView(const FWTAView& View, bool bWalk)`; `void SetUIMode(bool bPanelOpen)` |
| `AWTACharacter` | `ACharacter` | First-person camera at eye 162 cm (capsule half-height 90, radius 30), MaxWalkSpeed 300, sprint 560, JumpZVelocity 520, GravityScale 1.63, head-bob (2.6 cm, stride 155 cm). `UFUNCTION(BlueprintCallable) void WalkTo(FVector Dest)` (NavMesh, `UAIBlueprintHelperLibrary::SimpleMoveToLocation`), `void TeleportToView(const FWTAView& View)`, `bool IsAutoWalking() const` |

### 4.4 Interaction (`Interaction/`)
- `UWTAInteractable : UInterface` + `IWTAInteractable` (`UINTERFACE(BlueprintType)`), functions (all `BlueprintNativeEvent`):
  `FText GetInteractLabel() const;` `void Interact(AWTAPlayerController* Controller);` `bool GetViewSpot(FWTAView& OutView) const;`
  Callers use `IWTAInteractable::Execute_GetInteractLabel(Actor)` etc.
- `UWTAInteractionComponent : UActorComponent` on the controller: per-frame trace (screen centre, or mouse in cursor mode) on
  `ECC_Visibility` up to `MaxDistance = 1500` cm; `TWeakObjectPtr<AActor> Hovered`; `FText HoverLabel`; `bool TryInteract()`;
  delegate `FWTAHoverChanged OnHoverChanged` (`DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FWTAHoverChanged, const FText&, Label)`).

### 4.5 World actors (`World/`) — properties the editor Python sets (snake_case in Python)
All are `UCLASS(Blueprintable)`, implement `IWTAInteractable` unless noted, and apply their extents in `OnConstruction`.
The pick volume is a `UBoxComponent` named `PickBox` (root), collision preset that blocks `ECC_Visibility` only
(no pawn blocking), so traces hit it but you can walk through.

| Class | Python-set UPROPERTYs (`EditAnywhere`) | Interact does |
|---|---|---|
| `AWTAExhibitActor` | `FName ItemId`, `FVector PickExtent` (half size cm) | open the catalog card for `DT_Exhibits[ItemId]`, mark exhibit seen |
| `AWTABookActor` | `FName BookId`, `FVector PickExtent` | open the book reader at page 0 |
| `AWTAStationActor` | `FName StationId`, `FVector PickExtent` | open the station panel (title, steps, panel text; hands-on logic is phase 1+) |
| `AWTARideActor` | `FName RideId`, `FVector PickExtent` | open the ride card (ride mechanics are phase 1) |
| `AWTATokenActor` | `FName TokenId` (location: the `token__<id>` mesh centre when that mesh exists, else `DT_Tokens.Location`) | collect the token (hidden if already collected; spins and bobs; uses `/Engine/BasicShapes/Sphere` scaled 0.25 with an emissive dynamic material) |
| `AWTAStaffNPC` (parent `ACharacter`) | `FName StaffId` | open the staff chat. Placeholder body = capsule + `/Engine/BasicShapes/Cylinder` until `DT_Staff.MetaHuman` is set; then spawns that Blueprint as a child actor that loops the standing idle in game |
| `AWTARoomVolume` (not interactable) | `FName RoomId`, `FVector Extent` (half size cm) | on player overlap → `UWTARoomSubsystem::EnterRoom(RoomId)` |
| `AWTAWaxStageActor` (not interactable) | `FName SceneId`, `FVector TriggerExtent` | at BeginPlay spawns the row's built `Figures` (MetaHuman reenactors, posed and frozen like wax figures); while the player is inside: plays the scene's captions (`Lines`) on the HUD in a loop; later plays `Sequence` |
| `AWTAStatueActor` (not interactable) | `FName Person`, `FName Action`, `float Phase` | at BeginPlay spawns the person's MetaHuman held in the clip's pose, every surface in `M_WTA_Marble`, hair hidden: a marble statue (rows in `Pipeline/content/statues.json`, not a DataTable) |
| `AWTASeatActor` (parent `AWTAPickActor`) | `FName SeatId`, `float SeatYaw`, `FVector PickExtent` | sit the player down (`AWTACharacter::SitAt`: a 120 cm capsule on the floor under the sit point, the eye 75 cm over the seat, movement locked, looking and interacting still work); E on it again, Space or a move stands them up. One per `seat__<id>_f<yaw>` mesh (the Blender builders' cushions and bench seats), at the top of its bounds. A seat whose id starts with `<venue>_` belongs to that venue's talk |
| `AWTATalkActor` (not interactable) | `FName TalkId`, `float SpeakerYaw` | a talk or class (DT_Talks) in its venue: slides on the venue's `screen__<venue>` meshes, the speaker (a spawned reenactor, or the staff member who teaches it) on the spot, the talk running while a visitor sits on one of the venue's seats, the quiz and the certificate at the end of a class. One per Talks.json row, at the bottom of the `spot__<venue>_f<yaw>` mesh |
| `AWTAGalleryWallActor` (parent `AWTAPickActor`) | `float WallWidthCm`, `float PictureHeightCm`, `float RowHeightCm`, `float FloorBelowCm`, `int32 MaxPictures`, `FText Title`, `FVector PickExtent` | the visitors' own wall: the newest pictures from `Saved/Postcards` (photo mode) and `Saved/Maker` hung in a row with a mat and a caption each, newest in the middle; E hangs what is new. One per `content/gallery_walls.json` entry, against the wall at the row's height, facing the room |
| `AWTAPopUpBookActor` (parent `AWTAPickActor`) | `TArray<UStaticMesh*> Meshes`, `TArray<FWTAPopUpBook> Books` (`BookId`, `Pages`), `FVector ReaderDirection`, `FName ReaderSeatId`, `FVector PickExtent` | the pop-up books on the Reading Room's south table: spawns a component per `popup__` mesh and folds them; E sits the visitor in the reader's chair, then opens the book, turns the page (the spread folds down and the next pops up) and closes it after the last spread, when the next book's cover lies there. One, from `out/popup/layout.json` (`bl/popup.py`), over the book |
| `AWTACourseActor` (parent `AWTAPickActor`) | `FName TalkId`, `float SpeakerYaw`, `FVector PickExtent` | a course (DT_Talks row of kind course) at its venue's `spot__<venue>_f<yaw>` mesh: the course lead (the row's Person, a reenactor) idling at the desk, E opens the course card (`AWTAPlayerController::OpenCourse`): the welcome, the stations as a checklist with a Go button each, the quiz once every station is finished, the certificate and badge as a class. One per course row, where a talk row gets an `AWTATalkActor` |

### 4.6 Systems (`Systems/`)
| Class | Parent | Must have |
|---|---|---|
| `UWTAContentSubsystem` | `UGameInstanceSubsystem` | Loads every table from `UWTASettings` on Initialize (synchronous `LoadSynchronous`). Typed getters: `const FWTAExhibitRow* FindExhibit(FName) const` … one per row type, plus `TArray<FName> GetRowNames(<table>)`. |
| `UWTAProgressSubsystem` | `UGameInstanceSubsystem` | `UWTASaveGame` in slot `"WalkTheArchive"`, user 0. Tracks badges, tokens, exhibits seen, pages read, wax scenes watched, distance walked. `bool CollectToken(FName)`, `bool AwardBadge(FName)`, `void NoteExhibit(FName)`, `void NotePage(FName Book, int32 Page)`, `void NoteWaxScene(FName)`, `void NoteDistance(float Cm)`, `bool HasToken(FName) const`, `int32 NumBadges() const`, `void ResetProgress()`. Delegates `OnBadgeAwarded(FName)`, `OnTokenCollected(FName, int32 Found, int32 Total)`. Badge rules: ports of the web (first-steps after 50 m, curator after all 15 gallery exhibits, reader after 10 pages, historian after 12 wax scenes, token hunter after all tokens …; see `docs/reference/systems.md` §U) |
| `UWTATourSubsystem` | `UGameInstanceSubsystem` | `Start()`, `Next()`, `Back()`, `End()`, `bool IsTouring() const`, `int32 GetIndex() const`; each stop walks the player to its `View` (or the exhibit's View) and shows the tour bar |
| `UWTADialogueSubsystem` | `UGameInstanceSubsystem` | `FWTAReply Ask(FName StaffId, const FString& Question)` → greeting if the question is just hi/hello (`GreetingShort`), then rules with `Order < 100` (`FRegexPattern`, case-insensitive, respecting `MaxWords`, `StaffOnly`, `StaffNot`), then place directions (an alias contained in the question → `Directions` + `GoPlace`), then exhibit/book title match (→ `OpenItem`/`OpenBook`), then rules with `Order >= 100`, then keyword search over Facts, Lessons and exhibit text (simple TF-IDF, best sentence), then the staff `Fallback`. `USTRUCT FWTAReply { FText Text; FName Action; FName ActionArg; }` (not a row; declared in `Systems/WTADialogueSubsystem.h`) |
| `UWTARoomSubsystem` | `UWorldSubsystem` | `void EnterRoom(FName)`, `FName GetCurrentRoom() const`, `FName RoomAt(FVector) const` (from `DT_Rooms` boxes), delegate `OnRoomChanged(FName)`; first visit shows the room's `Sub` as a hint |
| `UWTAVisitLogSubsystem` | `UWorldSubsystem` | the visit log for the library's reports: `Saved/Visits/visit_<time>.csv` per play session (rooms left with seconds stayed, cards opened, tokens, badges, a position sample every 2 s; no names); `void NoteCard(FName Kind, FName Id)`, `NoteToken`, `NoteBadge`; `unreal/Tools/common/visit_report.py` makes the report page with the dwell times, the most opened cards and a heatmap over the DT_Rooms plan |
| `UWTASaveGame` | `USaveGame` | `TArray<FName>` Badges, Tokens, Exhibits, Pages (`"book:page"` as FName), WaxScenes; `float WalkedCm` |
| `UWTAGraphicsLibrary` | `UBlueprintFunctionLibrary` | `ApplyQualityPreset(int32 Level)` (0 Low … 4 Cinematic via `UGameUserSettings::SetOverallScalabilityLevel` + `ApplySettings`), `RunAutoDetect()` (`RunHardwareBenchmark` + `ApplyHardwareBenchmarkResults`), `GetQualityPreset()` |

### 4.7 UI (`UI/`) — UMG built entirely in C++ (no widget assets)
Each widget subclasses `UUserWidget` and builds its tree in `NativeOnInitialized()` with `WidgetTree->ConstructWidget<…>()`
and `WidgetTree->RootWidget = …`. Created with `CreateWidget<UClass>(PlayerController, UClass::StaticClass())`.
Fonts: engine default (`/Engine/EngineFonts/Roboto`) via `FSlateFontInfo`; palette from the web build
(ink #0d1613, panel #15221e, brass #cda961, bone #efe7d5, card #f2e9d7, card ink #2b2419).

| Widget | Shows |
|---|---|
| `UWTAHudWidget` | room kicker/name/sub (top-left), crosshair dot, hover label under the crosshair, toast line, tour bar (title, date, text, Back/Next/End), caption line (wax scenes), badge counter, hint line |
| `UWTAPanelWidget` | one modal panel for: exhibit catalog card (art image, kind, title, date, description, quote, sources, Prev/Next/Close), book reader (title, page heading, blocks, page x/y, Prev/Next/Close), station panel (kicker, title, steps, text, Close), ride card (name, text, note, Close), badges list. API: `ShowExhibit(FName)`, `ShowBook(FName, int32 Page)`, `ShowStation(FName)`, `ShowRide(FName)`, `ShowBadges()`, `Close()`, `bool IsOpen() const` |
| `UWTAChatWidget` | staff name/role, message list (scroll box), text box + Send, suggestion chips (buttons), Close |
| `UWTAMenuWidget` | the intro/pause menu: title "Walk the Archive", Enter / Take the tour / Graphics (Low, Medium, High, Epic, Cinematic, Auto) / Quit |

`AWTAPlayerController` owns one instance of each and switches input mode (`FInputModeGameAndUI` + cursor when any
panel/chat/menu is open; `FInputModeGameOnly` + no cursor otherwise).

### 4.8 Actions
One action vocabulary for tour stops, staff answers and buttons (`FName`, `None` = no action):
`GoPlace` (arg = place id), `OpenItem` (exhibit id), `OpenBook` (book id), `OpenStation` (station id), `OpenRide` (ride id),
`StartTour`, `OpenBadges`, `OpenHunt` (the token hunt's library card), `OpenQuiz` (talk id of a class), `OpenCourse` (talk id of a course), `StartTalk` (talk id). `AWTAPlayerController::RunAction(FName Action, FName Arg)` executes them.

## 5. Data files
- Converter: `unreal/Pipeline/data/build_data.py` (Python 3, stdlib only). Reads the raw web extraction
  `unreal/Pipeline/content/*.json` and the layout `unreal/Pipeline/layout/layout.json`, writes
  `unreal/WalkTheArchive/Data/<File>.json` (one per row struct, file name from structs.json) and validates every row
  against structs.json (exact field set, types). Row `Name` = the web id (exhibit ids keep their `-`).
- Book blocks: a string → `{Type: Para, Text}`; `{li:[…]}` → `{Type: List, Items}`; `{q}`→Quote; `{note}`→Note; `{code}`→Code.

## 6. Editor setup (Python inside Unreal)
- Package `unreal/WalkTheArchive/Content/Python/wta_setup/` (Content/Python is on Unreal's Python path).
- One entry script `unreal/WalkTheArchive/Scripts/setup_project.py`, run as
  `UnrealEditor-Cmd <uproject> -ExecutePythonScript=<abs path to setup_project.py> -unattended -nopause -nosplash -stdout -FullStdOutLogOutput`
  with an optional env var `WTA_STEPS` (comma list, default all) — steps in order:
  `probe`, `import_meshes`, `import_art`, `surfaces`, `data_tables`, `build_level`, `lighting`, `actors`, `navmesh`, `project_settings`, `verify`.
  Every step is idempotent (safe to re-run) and prints exactly one line `WTA_RESULT {json}` with `step`, `ok`, counts and errors.
- The repo root is found from the script path (`…/unreal/WalkTheArchive/Scripts/` → three levels up), never hard-coded.

## 7. Tools (`unreal/Tools/`)
Run with Unreal's bundled Python where Python is needed (`Engine/Binaries/ThirdParty/Python3/Win64/python.exe`,
`Engine/Binaries/ThirdParty/Python3/Mac/bin/python3`), so the user installs nothing extra.
`win/*.ps1` and `mac/*.sh`: `preflight`, `install_prereqs`, `find_engine`, `build_editor`, `setup_project`, `open_editor`, `play`, `package_game`.
`common/*.py`: `find_engine.py` (Launcher install dir from `LauncherInstalled.dat` / default paths), `configure_plugins.py`
(enables optional plugins only if their `.uplugin` exists in the engine), `check_results.py` (parses `WTA_RESULT` lines).

## 8. Docs
`unreal/README.md` (what this is, quick start), `unreal/COWORK.md` (the runbook), `unreal/COWORK_PROMPT.md` (paste into Cowork),
`unreal/CLAUDE.md` (instructions for a local Claude Code session in this folder), `unreal/docs/` (DECISIONS, ROADMAP,
HUMANS, DELIVERY, LOOKDEV) and `unreal/docs/reference/` (the research and spec files this build came from).
