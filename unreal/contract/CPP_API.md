# Walk the Archive — C++ API (module `WalkTheArchive`)

Generated from the headers in `WalkTheArchive/Source/WalkTheArchive/Public/`. Implementers write the matching
`Private/<Area>/*.cpp`; the editor Python and reviewers rely on the names below. Every reflected type uses the
`WTA` prefix and `WALKTHEARCHIVE_API`. Categories are `"WTA"` unless shown. `BP` = `UFUNCTION(BlueprintCallable)`,
`BPpure` = `UFUNCTION(BlueprintPure)`, `UP` = `UPROPERTY`. Include as `#include "Area/File.h"`.
Shadowing is a compile error (UE builds treat it as one): parameters and locals never reuse a member name of the class or its engine parents
(`Slot` in widgets, `Controller` in pawns, `Character`/`Pawn` in controllers, `Owner` in actors); setters take `In<Name>`.

## Module files
| File | Content |
|---|---|
| `Source/WalkTheArchive.Target.cs`, `Source/WalkTheArchiveEditor.Target.cs` | Game / Editor targets, `BuildSettingsVersion.Latest`, `EngineIncludeOrderVersion.Latest`, module `WalkTheArchive` |
| `Source/WalkTheArchive/WalkTheArchive.Build.cs` | `UseExplicitOrSharedPCHs`; public deps Core, CoreUObject, Engine, InputCore, EnhancedInput, UMG, Slate, SlateCore, AIModule, NavigationSystem, DeveloperSettings |
| `WalkTheArchive.h/.cpp` | `IMPLEMENT_PRIMARY_GAME_MODULE(FDefaultGameModuleImpl, WalkTheArchive, "WalkTheArchive")` |
| `Public/Core/WTALog.h`, `Private/Core/WTALog.cpp` | `WALKTHEARCHIVE_API DECLARE_LOG_CATEGORY_EXTERN(LogWTA, Log, All)` / `DEFINE_LOG_CATEGORY(LogWTA)` |

## Data (`Data/WTATypes.h`)
Every struct of `structs.json`, same order, all `USTRUCT(BlueprintType)`, every field
`UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="WTA")`, numbers/bools/vectors default-initialised.

| Struct | Fields (in order) |
|---|---|
| `FWTAView` | `FVector Location; float Yaw; float Pitch; bool bValid` |
| `FWTABookBlock` | `FName Type; FText Text; TArray<FText> Items` |
| `FWTABookPage` | `FText Heading; TArray<FWTABookBlock> Blocks` |
| `FWTAWaxLine` | `float Time; FText Text` |
| `FWTAWaxFigure` | `FName Person; FVector Offset; float Yaw` (a reenactor: people.json id; feet in the stage frame, cm; yaw added to StageYaw) |
| `FWTASourceRow : FTableRowBase` | `FText Label; FString Url` |
| `FWTAGalleryRow` | `int32 Index; FText Label, DisplayName, Years; FLinearColor WallColor` |
| `FWTAExhibitRow` | `FName KindId; FText Kind; int32 Gallery; FText Title, Date; int32 Year; FText Description, More, Quote, QuoteBy, Where, Partners; TArray<FName> Sources; FText Hall; bool bWax; FName WaxSceneId; TSoftObjectPtr<UTexture2D> Art; FVector Location; float Yaw; FVector2D Size; FWTAView View` |
| `FWTASubjectRow` | `FText DisplayName; FName Side; int32 Slot; FLinearColor Color; FWTAView ShelfView` |
| `FWTABookRow` | `FName Subject; FText Title, Subtitle; TArray<FWTABookPage> Pages; TSoftObjectPtr<UTexture2D> Cover` |
| `FWTARoomRow` | `FText Kicker, DisplayName, Sub; FName Wing; FVector BoundsMin, BoundsMax; bool bOutdoor; FName StaffId; FText MapLabel; FName GoPlace` |
| `FWTAPlaceRow` | `FText Label; TArray<FString> Aliases; FWTAView View; FText Directions, Say` (Directions follows "That's "; Say names the place mid-sentence, "the Wax Hall") |
| `FWTATourStopRow` | `int32 Index; FName Kind, ItemId; FText Title, DateLabel, Body; FWTAView View; FText OpenLabel; FName Action, ActionArg` |
| `FWTAStaffRow` | `FText DisplayName, Role, Monogram; FLinearColor Color; TArray<FName> Rooms; FVector Location; float Yaw; FWTAView TalkView; FText Greeting, GreetingShort, Help, Fallback; TArray<FText> Chips; FName RocketboxId; FString LookNotes; TSoftClassPtr<AActor> MetaHuman` |
| `FWTAStaffRuleRow` | `int32 Order; FString Pattern; int32 MaxWords; TArray<FName> StaffOnly, StaffNot; FText Answer; FName Action, ActionArg; bool bOffer; FText OfferLabel` |
| `FWTAFactRow` | `FText Body; TArray<FName> Sources` |
| `FWTALessonRow` | `FName Station; FText Title, Body` |
| `FWTABadgeRow` | `FText DisplayName, How` |
| `FWTATokenRow` | `FText Place, Hint; FName Wing; FVector Location; FName RideGate` |
| `FWTAWaxSceneRow` | `int32 Number; FText Year, Title; float LoopSeconds; TArray<FWTAWaxLine> Lines; FVector StageLocation; float StageYaw; FName ItemId; FSoftObjectPath Sequence; TArray<FWTAWaxFigure> Figures` |
| `FWTAStationRow` | `FName Room; FText Kicker, Title, Subtitle, GoLabel; TArray<FText> Steps, Panel; bool bUsesHands; FVector Location; FWTAView View` |
| `FWTARideRow` | `FText DisplayName, Kicker, CardText, CardNote, About, Stats, Safety; FName BadgeId; FVector Location; FWTAView ExitView` |

Helpers (plain namespaces, not reflected): `WTAAction::GoPlace()/OpenItem()/OpenBook()/OpenStation()/OpenRide()/StartTour()/OpenBadges()`
return the action `FName`s; `WTABadge::FirstSteps()/Explorer()/Bookworm()/Curious()/Hunter()/Historian()` the badge ids C++ awards.

## Core
### `UWTASettings : UDeveloperSettings` (`Core/WTASettings.h`)
`UCLASS(Config=Game, DefaultConfig, meta=(DisplayName="Walk the Archive"))`, section `[/Script/WalkTheArchive.WTASettings]`.
- `static const UWTASettings* Get()`; `GetCategoryName()` = "Game".
- `UP(Config, EditAnywhere) TSoftObjectPtr<UDataTable>` **Exhibits, Books, Sources, Galleries, Subjects, Rooms, Places, Tour, Staff, StaffRules, Facts, Lessons, Badges, Tokens, WaxScenes, Stations, Rides** — constructor defaults `/Game/WTA/Data/DT_<Name>.DT_<Name>`.
- `UP(Config) FWTAView SpawnView` (default (0,-70,162) yaw -90 pitch 1.146 valid), `FString SaveSlotName = "WalkTheArchive"`, `float ToastSeconds = 3.4`, `float HintSeconds = 6`, `bool bShowIntroMenu = true`.

### `AWTAGameMode : AGameModeBase` (`Core/WTAGameMode.h`)
Constructor: `DefaultPawnClass = AWTACharacter`, `PlayerControllerClass = AWTAPlayerController`, `HUDClass = nullptr`.
`StartPlay()` override: when the default `ARecastNavMesh` uses `RuntimeGeneration=Dynamic` and has no active tiles (the headless setup run cannot build it: the editor holds its async-load navigation lock), calls `UNavigationSystemV1::Build()` once, so click-to-walk and the tour walk instead of teleporting. A NavMesh built and saved in the editor is kept.

### `AWTAPlayerController : APlayerController` (`Core/WTAPlayerController.h`) — the hub
Delegate `FWTAUIModeChanged(bool bPanelOpen)`; `UP(BlueprintAssignable) OnUIModeChanged`.
- Components/widgets: `UP TObjectPtr<UWTAInteractionComponent> Interaction` (created in constructor); `UP(Transient) TObjectPtr<UWTAHudWidget> Hud; UWTAPanelWidget* Panel; UWTAChatWidget* Chat; UWTAMenuWidget* Menu` (CreateWidget in BeginPlay, z-order 0/10/20/30).
- Input objects, all `UP(Transient)`, NewObject'd in `CreateInputObjects()`: `UInputMappingContext* MappingContext`; `UInputAction* MoveAction (Axis2D), LookAction (Axis2D, mouse), LookStickAction (Axis2D, gamepad right stick, scaled by GamepadLookRate per second), JumpAction, SprintAction, InteractAction, BackAction, ToggleCursorAction, TourNextAction, PlacesAction, ChatAction`.
  Keys: WASD / left stick → Move; Mouse2D / right stick → Look; Space / A → Jump; LShift / L3 → Sprint; LMB, E / X → Interact; Esc / B → Back; Tab → ToggleCursor; T → TourNext; M → Places; Enter → Chat.
- Feel: `UP float MouseLookScale = 1; bool bInvertMouseY = false; float GamepadLookRate = 120 (deg/s); float FaceViewRate = 4.5`.
- `BP void OpenExhibit(FName ItemId)` — closes chat, `Panel->ShowExhibit`, `Progress->NoteExhibit`, `SetUIMode(true)`.
- `BP void StepExhibit(int32 Delta)` — prev/next in the gallery list or wax list (wrap), walks to the new exhibit's View and opens it.
- `BP void OpenBook(FName BookId, int32 Page)` — Page -1 = cover/TOC, 0..N-1 pages; `NotePage` for real pages.
- `BP void OpenStation(FName StationId)`, `BP void OpenRide(FName RideId)`, `BP void OpenBadges()`, `BP void OpenPlaces()`, `BP void OpenStaffChat(FName StaffId)`.
- `BP bool CloseTopPanel()` — order Menu → Chat → Panel → end tour; true if something closed. `BP void ToggleMenu()`. `BPpure bool IsAnyPanelOpen() const`.
- `BP void ShowToast(const FText& Text, float Seconds = 0)` (0 = settings default), `BP void ShowCaption(const FText&)` (empty hides), `BP void ShowHint(const FText&)`.
- Walk-up story plaque: `BP void ShowStoryPlaque(FName ItemId)` (HUD museum label from `DT_Exhibits`: kicker = wax `Hall` or `Kind`, year = `Date`, title, the opening sentences of `Description`, hint "Press E to read the full story" or "Click to read the full story" in cursor mode; `NAME_None` hides), `BP void SetStageStory(FName ItemId, bool bInside)` (wax stages report the scene the player stands in). The hovered `AWTAExhibitActor` wins, else the stage scene (`RefreshStoryPlaque()`; state `FName HoverStoryId, StageStoryId, ShownStoryId`); exhibits show the plaque instead of the crosshair label. OnInteract with nothing hovered inside a stage opens that scene's card. `SetUIMode` hides the plaque while a panel is open.
- `BP void RunAction(FName Action, FName Arg)` — GoPlace/OpenItem/OpenBook/OpenStation/OpenRide/StartTour/OpenBadges; OpenItem and OpenStation also walk to the row's View. OpenBook's Arg is a book id (opens on the cover) or `<book>#<page index>` (opens at that page; a staff answer that names a page).
- `BP void GoToView(const FWTAView& View, bool bWalk)` — walk (NavMesh) then face, or teleport; ignores `bValid == false`. `BP void GoToPlace(FName PlaceId)`.
- QA: `UFUNCTION(Exec, BlueprintCallable) void WTAShotTour(float SecondsPerShot = 5)` — closes panels, then teleports (walking mode kept, unlike `BugItGo`, which switches to ghost) to every `DT_Places` view, every valid staff `TalkView` and a spot 4.2 m in front of every wax stage; after `SecondsPerShot` (lighting and exposure settle) it saves `Saved/Screenshots/<platform>/QA/NN_<place|staff|wax>_<id>.png`. Log lines `WTA_SHOTTOUR start`, one per file, `WTA_SHOTTOUR done`. Run as `-game -ExecCmds="WTAShotTour 5"`. Protected: `ShotTourTeleport()`, `ShotTourCapture()`; state `TArray<TPair<FString, FWTAView>> ShotTourViews; int32 ShotTourIndex; float ShotTourSeconds; FTimerHandle ShotTourTimer`.
- QA: `UFUNCTION(Exec, BlueprintCallable) void WTAChatTest()` — asks every staff member their own chips, then each line of `Saved/QA/chat_questions.txt` (blank lines and `#` lines skipped; a short built-in list if the file is missing) through `UWTADialogueSubsystem::Ask`, and logs one `WTA_CHAT <staff> | <question> -> <answer> [<action> <arg>< offered: label>]` line per answer, then `WTA_CHAT done N questions`.
- QA: `UFUNCTION(Exec, BlueprintCallable) void WTAChatShots(float SecondsPerShot = 2.5)` — for each line `<staff id> | <question>` of `Saved/QA/chat_shots.txt` (or four built-in questions) teleports to that staff member's `TalkView`, opens a fresh chat (`UWTAChatWidget::ClearConversation`), sends the question and, `SecondsPerShot` later, saves `Saved/Screenshots/<platform>/QA/chat_NN_<staff>.png` with the UI; a line ending in `| click` then clicks the first offer button (`UWTAChatWidget::ClickOffer(0)`) and saves `chat_NN_<staff>_after.png`. Log lines `WTA_CHATSHOT start`, one per file, `WTA_CHATSHOT click …`, `WTA_CHATSHOT done`. Protected `ChatShotAsk()`, `ChatShotCapture()`, `ChatShotClick()`; state `TArray<TPair<FName, FString>> ChatShots; TArray<bool> ChatShotClicks; int32 ChatShotIndex; float ChatShotSeconds; bool bChatShotClicked; FTimerHandle ChatShotTimer`.
- QA: `UFUNCTION(Exec, BlueprintCallable) void WTAPlayTest(const FString& Phases = "all")` — creates `UWTAPlayTest` (`Core/WTAPlayTest.h`, an actor component on the controller, `UP(Transient) PlayTest`) and runs its script: it plays like a player and logs `WTA_PLAY <phase> PASS|FAIL|SKIP|INFO <what> | <details>` lines, then `WTA_PLAY done <n> pass, <n> fail, <n> skip`. Keys go through Slate (`FSlateApplication::ProcessKeyDownEvent/ProcessKeyUpEvent`) so the real bindings run; when the window has no keyboard focus the script calls the input handlers instead (`friend class UWTAPlayTest`). Phases (in order; `all`, or names separated by spaces): `menu` (intro menu at start, Enter starts in the lobby facing the galleries, Esc opens and closes the pause menu), `keys` (M opens places, Esc closes), `walk` (each line `<name> | <x> <y> | <yaw> | x|y <wall coordinate>` of `Saved/QA/walk_tests.txt`: hold W + Shift into the wall for 1.1 s, fail if the player crossed the wall's plane or fell), `interact` (every `UWTAInteractable` actor: stand at its view spot or in front of it (teleports go through `GoToView(View, false)`, which also drops a pending camera turn), the crosshair must name it, E must open the right card, book, station, ride card or chat or collect the token, the right arrow turns a book page, Esc closes it; a token only a ride reaches must be out of reach on foot or stay uncollected; a failure line says what the screen-centre ray hits and why no spot to aim from was found), `wax` (each stage's plaque and a shot from the aisle, E with nothing hovered opens the scene's story), `ui` (T starts the tour and walks to stop 1, T walks on, Esc ends it; Enter opens the room's staff chat; badges panel), `graphics` (Medium and Epic presets apply, then the levels found at the start come back), `fps` (average and worst frame over 3 s at five places, pass at 30 fps), `people` (wax figures are frozen in their held pose, face on the head, no bone of the current LOD at the feet), `faces` (a 75 cm close-up of every person, no HUD, `QA/face_NN_<person>.png`; on screen: face on the head, no collapsed bones, staff idles move), `adapt` (only when named: no-HUD shots 0.5 to 8 s after travelling from the yard into four rooms, for the auto exposure). Tokens: `only=<text>` limits `people`, `faces` and `interact` to names containing the text; `speeddown=<x>` sets every post process volume's auto exposure Speed Down for the run. Screenshots: `Saved/Screenshots/<platform>/QA/play_NN_<name>.png`.
- `BP void SetUIMode(bool bPanelOpen)`, `BP void SetCursorFree(bool bFree)`, `BPpure bool IsCursorFree() const`, `BPpure AWTACharacter* GetWTACharacter() const`.
- Protected: `BeginPlay`, `SetupInputComponent`, `Tick`, `OnPossess`; `CreateInputObjects()`, `CreateWidgets()`, `UpdateInputMode()`, `RefreshTourBar()`; handlers `OnMove/OnLook/OnLookStick/OnJump/OnJumpEnd/OnSprint/OnSprintEnd/OnInteract/OnBack/OnToggleCursor/OnTourNext/OnPlaces/OnChat(const FInputActionValue&)`; `UFUNCTION()` sinks `HandleHoverChanged(const FText&)`, `HandleRoomChanged(FName)`, `HandleBadgeAwarded(FName)`, `HandleTokenCollected(FName, int32, int32)`, `HandleTourChanged(int32)`, `HandleProgressReset()`; state `FWTAView PendingView; bool bHasPendingView, bFaceTravelDirection, bCursorFree, bUIMode, bTourActive, bCursorFreedForTour`.
- Behaviour: panel open ⇒ `FInputModeGameAndUI` + cursor, Move/Look/Jump ignored; otherwise `FInputModeGameOnly`, unless cursor free (GameAndUI + cursor, keyboard focus on the game viewport, hover from mouse, click floor = `WalkTo`). OnBack: `if (!CloseTopPanel()) ToggleMenu()`. OnTourNext: `Next()` if touring else `Start()`. A tour frees the cursor while it runs (so the tour bar's Back / Next (T) / End can be clicked; T and Esc still work) and gives mouse look back when it ends, unless the player pressed Tab in between. OnChat: focus chat if open, else open the current room's staff.

### `AWTACharacter : ACharacter` (`Core/WTACharacter.h`)
- `UP TObjectPtr<UCameraComponent> Camera` (relative Z 72, FOV 66, uses pawn control rotation).
- `UP(EditAnywhere, "WTA|Feel") float WalkSpeed=300, SprintSpeed=560, EyeHeight=162, BobAmplitude=2.6, BobStride=155, LandingDipScale=0.1, TravelSpeedMin=240, TravelSpeedMax=1200, AutoWalkStopRadius=10`. Constructor: capsule 30/90, JumpZVelocity 520, GravityScale 1.63.
- `BP void WalkTo(FVector Dest)` (`UAIBlueprintHelperLibrary::SimpleMoveToLocation`, speed `clamp(PathLength/2.3, 240, 1200)`), `BP void StopWalking()`, `BPpure bool IsAutoWalking() const`, `BP void TeleportToView(const FWTAView&)`, `BPpure FWTAView GetCurrentView() const`, `BPpure FVector GetEyeLocation() const`, `BP void SetSprinting(bool)`, `BPpure bool IsSprinting() const`, `BP void AddMoveInput(FVector2D Axis)` (X right, Y forward; cancels auto-walk).
- Protected: `BeginPlay`, `Tick`, `Landed(const FHitResult&)`, `UpdateCameraOffset(float)`, `NoteDistanceWalked()` (→ `UWTAProgressSubsystem::NoteDistance`); state `BobPhase, BobAmount, DipOffset, DipVelocity, bSprinting, bAutoWalking, LastFrameLocation, bHasLastFrameLocation`.

## Interaction
### `UWTAInteractable` / `IWTAInteractable` (`Interaction/WTAInteractable.h`)
`UINTERFACE(BlueprintType, Blueprintable)`. All `UFUNCTION(BlueprintNativeEvent, BlueprintCallable)`:
`FText GetInteractLabel() const; void Interact(AWTAPlayerController* Controller); bool GetViewSpot(FWTAView& OutView) const;`
Call through `IWTAInteractable::Execute_GetInteractLabel(Actor)`, `Execute_Interact(Actor, PC)`, `Execute_GetViewSpot(Actor, OutView)` after `Actor->Implements<UWTAInteractable>()`. Implement as `<Name>_Implementation`.

### `UWTAInteractionComponent : UActorComponent` (`Interaction/WTAInteractionComponent.h`)
Delegates `FWTAHoverChanged(const FText& Label)`, `FWTAInteracted(AActor* Actor)`.
- `UP float MaxDistance = 1500`; `UP bool bUseMouseCursor`; `UP(BlueprintReadOnly) FText HoverLabel`; `TWeakObjectPtr<AActor> Hovered`; `UP(BlueprintAssignable) OnHoverChanged, OnInteracted`.
- `BP void UpdateHover()` (ECC_Visibility line trace from the camera/screen centre or the deprojected mouse), `BP bool TryInteract()`, `BPpure AActor* GetHovered() const`, `BPpure bool HasHover() const`, `const FHitResult& GetLastHit() const`, `BPpure bool GetLastHitLocation(FVector& OutLocation, FVector& OutNormal) const`.
- Protected: `TickComponent`, `ComputeTraceRay(FVector& Start, FVector& Dir) const`, `SetHovered(AActor*)`, `FHitResult LastHit`.

## World (editor-Python properties in bold; snake_case in Python)
### `AWTAPickActor : AActor, IWTAInteractable` (`World/WTAPickActor.h`, abstract base)
- `UP TObjectPtr<UBoxComponent> PickBox` (root; QueryOnly, WorldDynamic, blocks ECC_Visibility only); **`UP FVector PickExtent`** (50,50,50) applied in `OnConstruction`.
- Overrides `GetInteractLabel_Implementation` (returns `Label`), `Interact_Implementation` (empty), `GetViewSpot_Implementation` (returns `ViewSpot`).
- `BP void RefreshFromData()` (calls virtual `ReadRow()`; BeginPlay does too). Protected `UP(BlueprintReadOnly) FText Label; FWTAView ViewSpot`.

| Subclass | Python property | `Interact_Implementation` | Label |
|---|---|---|---|
| `AWTAExhibitActor` | **`FName ItemId`** | `PC->GoToView(View, true); PC->OpenExhibit(ItemId)` | "Open · Title" |
| `AWTABookActor` | **`FName BookId`**, `int32 OpenPage = 0` | `PC->OpenBook(BookId, OpenPage)` | "Read · Title" |
| `AWTAStationActor` | **`FName StationId`** | `PC->GoToView(View, true); PC->OpenStation(StationId)` | "GoLabel · Title" |
| `AWTARideActor` | **`FName RideId`** | `PC->OpenRide(RideId)` | "Ride · DisplayName" |

### `AWTATokenActor : AActor, IWTAInteractable` (`World/WTATokenActor.h`)
**`UP FName TokenId`**; `UP USceneComponent* Root; USphereComponent* PickSphere (r 40, Visibility only); UStaticMeshComponent* Mesh` (`/Engine/BasicShapes/Sphere`, scale 0.25); `UP float SpinDegreesPerSecond=103, BobAmplitude=5, BobSeconds=2.2, AnimateWithin=1000; FLinearColor GlowColor`; `UP(Transient) UMaterialInstanceDynamic* GlowMaterial`; `BP void SetCollected(bool)`, `BPpure bool IsCollected() const`; protected `UP(BlueprintReadOnly) FName RideGate`, `UFUNCTION() HandleProgressReset()` (bound to `UWTAProgressSubsystem::OnProgressReset`; the token shows again). Interact: ride-gated → toast, else `Progress->CollectToken` + hide. Label "Collect · XR token".

### `AWTAStaffNPC : ACharacter, IWTAInteractable` (`World/WTAStaffNPC.h`)
**`UP FName StaffId`**; `UP UStaticMeshComponent* PlaceholderBody; UChildActorComponent* MetaHumanChild; UTextRenderComponent* NameLabel; UBoxComponent* PickZone` (hover target over the body and the floating name, 80 × 80 × 215 cm, QueryOnly, blocks Visibility only); `UP float LookAtDistance=1200, TurnRate=4, NameHideDistance=400` (the name tag, 11 cm text that faces the camera, hides closer than this; the hover label "Ask DisplayName" names the person there); `UP(BlueprintReadOnly) FText DisplayName, StaffRole` (not `Role`: `AActor::Role` is already a reflected property), `FLinearColor Color; FWTAView TalkView`; `UP TSoftObjectPtr<UAnimSequence> IdleAnimation` (default `UWTAPeopleLibrary::DefaultIdlePath`), `UP float MetaHumanYawOffset = -90` (MetaHuman Creator Blueprints face +Y); `BP void ApplyStaffRow()`, `BP void Talk(const FText&)`, `BPpure bool IsTalking() const`. When `DT_Staff.MetaHuman` loads, the child gets yaw `MetaHumanYawOffset` and, in a game world, loops `IdleAnimation` (`UWTAPeopleLibrary::PlayPose`). Interact: `PC->OpenStaffChat(StaffId)` (its `Interact_Implementation` parameter is `InController`: `APawn::Controller` exists); ViewSpot = TalkView; label "Ask DisplayName".

### `UWTAPeopleLibrary : UBlueprintFunctionLibrary` (`World/WTAPeopleLibrary.h`)
MetaHuman people built by `Content/Python/wta_people`. `static const TCHAR* DefaultIdlePath` (`/Game/WTA/Characters/Common/Anims/AS_WTA_StandIdle`); `BPpure static FSoftClassPath MetaHumanClassPath(FName Person)` (`/Game/WTA/Characters/<Person>/BP_<Person>.BP_<Person>_C`); `BP static UClass* LoadMetaHumanClass(FName Person)` (null, without a load warning, while the package does not exist); `BP static USkeletalMeshComponent* FindBody(AActor*)` (component named `Body`, else the leader-pose mesh); `BP static bool PlayPose(AActor*, UAnimSequence*, bool bLoop, float StartTime)` (single-node; when not looping it holds the frame, turns the update rate optimizer off and `Thaw`s, so every mesh evaluates every frame even off screen); `BP static void Freeze(AActor*)` (`bNoSkeletonUpdate` on every skeletal mesh keeps the evaluated bones; the meshes keep ticking so LODs still switch, and since an evaluation only poses the current LOD's bones, whoever freezes a person thaws it when a LOD changes); `BP static void Thaw(AActor*)` (`bNoSkeletonUpdate` off, `AlwaysTickPoseAndRefreshBones`); `static int32 NextLOD(const USkeletalMeshComponent*)` (the LOD the mesh draws this frame when called between its LOD sync's tick and its own: the sync's forced LOD clamped like `UpdateLODStatus`, never finer than streamed in); `static int32 CountCollapsedBones(const USkeletalMeshComponent*, FString* OutNames)` (bones the current LOD skins with that sit at the component origin though the reference pose has them away from it: never evaluated; they drag a face's jaw and lips down to the feet); `static FString DescribeMeshes(AActor*)` (per mesh: LOD of N, forced, streamed in, wanted, frozen, collapsed bones); `BP static bool IsFaceOnBody(AActor*, float& OutGapCm)` (face `head` joint within 0.5 cm of the body's); `BPpure static float PersonPhase(FName)` (stable 0..1); `BP static bool SetAnimationSkeleton(UAnimSequence*, USkeleton*)` (editor only, `UAnimationAsset::ReplaceSkeleton`; false in a game build; the `idle` build step uses it to put the idle copy on the Common body skeleton).

### `AWTARoomVolume : AActor` (`World/WTARoomVolume.h`)
**`UP FName RoomId`**, **`UP FVector Extent`** (300,300,220); `UP UBoxComponent* Bounds` (root, overlaps Pawn only). `OnConstruction` applies Extent; `NotifyActorBeginOverlap` → `UWTARoomSubsystem::EnterRoom(RoomId)` for the player pawn.

### `UWTAWaxAnimInstance : UAnimInstance` (`World/WTAWaxAnimInstance.h`)
What a reenactor's body runs instead of an Animation Blueprint: it samples one clip, or two while crossfading, and blends the poses. `struct FWTAWaxClip { TWeakObjectPtr<UAnimSequence> Anim; float Time, Rate; bool bLoop; void Advance(float) }`; `USTRUCT FWTAWaxAnimProxy : FAnimInstanceProxy` holds `Current`, `Previous`, `BlendAlpha`, `BlendPerSecond`, `bHeld`, `Serial`, and does all its work in `PreUpdate` (game thread) so `Evaluate` only samples (`UAnimSequence::GetAnimationPose` into the pose contexts, then `FAnimationRuntime::BlendTwoPosesTogether` with a smoothstepped alpha). `BP void PlayClip(UAnimSequence*, bool bLoop = true, float Rate = 1, float StartTime = 0, float BlendSeconds = 0.35)` crossfades (0 = cut); `BP void Hold(bool)` stops time so the pose stays put (a wax figure); `BPpure UAnimSequence* GetClip() const`, `BPpure float GetClipTime() const`, `BPpure bool IsBlending() const`.

### `AWTAWaxStageActor : AActor` (`World/WTAWaxStageActor.h`)
**`UP FName SceneId`**, **`UP FVector TriggerExtent`** (400,300,220); `UP UBoxComponent* Trigger`; `UP float WatchSecondsForCredit = 5`; `BPpure bool IsLive() const`, `BPpure float GetPlayTime() const`; overrides `OnConstruction`, `NotifyActorBeginOverlap/EndOverlap`, `BeginPlay`, `Tick`; protected `UP(Transient) FWTAWaxSceneRow Scene` + state. Inside: loops `Lines` as HUD captions (`PC->ShowCaption`), credits `NoteWaxScene` after 5 s. Entering / leaving the trigger calls `PC->SetStageStory(ItemId, true/false)` (the scene's walk-up plaque; E opens its card).

Reenactors: `UP TSoftObjectPtr<UAnimSequence> FigurePose` (default `UWTAPeopleLibrary::DefaultIdlePath`, for a figure with no beats), `UP float FigureYawOffset = -90` (MetaHuman Creator Blueprints face +Y), `UP float MaxTurnFromAisle = 100` (the web's camera sat behind the scene, so a figure turned further than this is turned back: from the aisle a figure facing the back wall is one you cannot see), `UP(Transient) TArray<AActor*> Figures`. `BeginPlay` spawns every row `Figures` entry whose MetaHuman is built at `StageLocation + FRotator(0,StageYaw,0).RotateVector(Offset)`, yaw `StageYaw + ClampAngle(Yaw, ±MaxTurnFromAisle) + FigureYawOffset`, collision off, gives its body a `UWTAWaxAnimInstance` and starts it on frame `PersonPhase(Person) * length` of its first beat's clip, held.

Acting: `UP float WakeDistance = 1600` and `UP float SleepDistanceSlack = 250` — while the player is that near (or inside the trigger) the figures act, and otherwise they `Hold` the frame they reached, so a sleeping stage is a tableau of its own scene. `UP FString AnimFolder` (`/Game/WTA/Characters/Common/Anims/Mocap`) + `LoadAction(FName)` load `AS_WTA_<Action>` once each. `UpdateBeats` runs `ActTime` over `LoopSeconds` and, when the current `FWTAWaxBeat` changes, calls `PlayClip` with the beat's `Blend` and `Rate` (a beat that only changes `Yaw` keeps the clip playing) and turns and lifts the figure over the same seconds. `UpdateProps` puts each `FWTAWaxProp` where its keys say: `PropKeyTransform` reads the figure's `head`/`hand_l`/`hand_r`/`spine_05` socket, squaring head and chest props to the person's facing (hand props turn with the hand), and a prop travelling between two keys blends between them. Props are blocks with the materials `wta_mocap.props` makes. `BPpure FString DescribeActing() const` names every figure's clip and every prop's key (QA).

Wax: the stage ticks after each figure's `ULODSyncComponent` and before its meshes (tick prerequisites) and runs `UpdateFigureBones` every frame, which does nothing while acting; otherwise a figure freezes (`UWTAPeopleLibrary::Freeze`) after `UP SettleSeconds = 1.5` and `UP MinFramesBeforeFreeze = 10` once `IsFaceOnBody` (or after `UP MaxSecondsBeforeFreeze = 15`, with a warning), only on a frame whose LODs match the frame it last evaluated; a frozen figure whose mesh is about to change LOD (`NextLOD` differs from the LOD it was posed at) thaws, evaluates at the new LOD in the frame it is first drawn, and freezes again two frames later; `BPpure int32 GetReposeCount() const` counts those re-poses (QA); `EndPlay` destroys the figures.

## Systems
### `UWTAVoiceSubsystem : UGameInstanceSubsystem` (`Systems/WTAVoiceSubsystem.h`)
The museum reads a card aloud. One clip per card at `/Game/WTA/Audio/VO_<kind>_<id>` (the id's hyphens as underscores, since an asset name cannot hold one), imported by `Content/Python/wta_voice` from WAVs spoken by Kokoro-82M (Apache 2.0) outside the editor, from the words on the card itself. Kinds: `exhibit`, `wax`, `station`, `ride`, `fact`, `badge`.
- `static UWTAVoiceSubsystem* Get(const UObject*)` (BPpure, WorldContext); `BPpure static FString ClipPath(FName Kind, FName Id)`.
- `BP bool HasClip(FName Kind, FName Id)` (loads once and remembers, a card with no clip included, so a Listen button can ask every time it opens); `BP bool Read(FName Kind, FName Id)` (stops whatever was being read, then plays 2D at `UP float Volume = 1`); `BP void Stop()`; `BPpure bool IsReading() const`, `BPpure bool IsReadingCard(FName Kind, FName Id) const`.
- `BlueprintAssignable FWTAVoiceChanged OnVoiceChanged` fires when the voice starts, stops, or a clip ends on its own (the component's `OnAudioFinished`), so a Listen button relabels itself.

### `UWTAContentSubsystem : UGameInstanceSubsystem` (`Systems/WTAContentSubsystem.h`)
`UENUM EWTATable { Exhibits, Books, Sources, Galleries, Subjects, Rooms, Places, Tour, Staff, StaffRules, Facts, Lessons, Badges, Tokens, WaxScenes, Stations, Rides }`.
- `static UWTAContentSubsystem* Get(const UObject* WorldContextObject)` (BPpure, WorldContext); `Initialize` loads every table (`LoadSynchronous`); `BP void ReloadTables()`.
- `BPpure UDataTable* GetTable(EWTATable) const; TArray<FName> GetRowNames(EWTATable) const; bool HasRow(EWTATable, FName) const`.
- C++ getters (pointer into the table, null if missing): `FindExhibit, FindBook, FindSource, FindGallery, FindSubject, FindRoom, FindPlace, FindTourStop, FindStaff, FindStaffRule, FindFact, FindLesson, FindBadge, FindToken, FindWaxScene, FindStation, FindRide (FName) const`.
- `BPpure TArray<FName> GetGalleryExhibitIds() const` (bWax false, table order), `GetWaxExhibitIds() const`, `GetTourStopIds() const` (sorted by Index).
- BP copies: `bool GetExhibit/GetBook/GetRoom/GetPlace/GetStaff/GetStation/GetRide/GetTourStop(FName, F…Row& Out) const`.
- Protected `UP(Transient) TObjectPtr<UDataTable> <Name>Table` ×17, template `FindRowIn<TRow>(const UDataTable*, FName) const`.

### `UWTAProgressSubsystem : UGameInstanceSubsystem` (`Systems/WTAProgressSubsystem.h`)
Delegates `FWTABadgeAwarded(FName BadgeId)`, `FWTATokenCollected(FName TokenId, int32 Found, int32 Total)`, `FWTAProgressReset()`; `UP(BlueprintAssignable) OnBadgeAwarded, OnTokenCollected, OnProgressReset`.
- `static Get(WorldContext)`; `Initialize` (Load), `Deinitialize` (Save).
- `BP bool CollectToken(FName)`, `BP bool AwardBadge(FName)`, `BP void NoteExhibit(FName)`, `BP void NotePage(FName Book, int32 Page)`, `BP void NoteWaxScene(FName)`, `BP void NoteDistance(float Cm)`, `BP void NoteQuestionAsked()`, `BP void NoteRideFinished(FName RideId)`, `BP void NoteStationFinished(FName StationId)`.
- `BPpure bool HasToken/HasBadge/HasSeenExhibit/HasWatchedWaxScene(FName) const; bool HasReadPage(FName, int32) const; int32 NumBadges/TotalBadges/NumTokens/TotalTokens/NumExhibitsSeen/NumPagesRead/NumWaxScenesWatched() const; float GetWalkedCm() const`.
- `BP void ResetProgress()`, `BP void Save()`, `BP void Load()`.
- Rules: first-steps 500 cm, explorer 5 exhibits, bookworm 5 pages, curious 1 question, hunter all DT_Tokens, historian 6 scenes (`static constexpr FirstStepsCm, ExplorerExhibits, BookwormPages, HistorianScenes, SaveDistanceEveryCm = 2000`). Protected `CheckBadges()`, `static FName PageKey(FName, int32)` ("book:page"), `UP(Transient) UWTASaveGame* SaveData`.

### `UWTASaveGame : USaveGame` (`Systems/WTASaveGame.h`)
`UP int32 Version = 1; TArray<FName> Badges, Tokens, Exhibits, Pages, WaxScenes; float WalkedCm`.

### `UWTATourSubsystem : UGameInstanceSubsystem` (`Systems/WTATourSubsystem.h`)
Delegate `FWTATourChanged(int32 Index)` (-1 = ended); `UP(BlueprintAssignable) OnTourChanged`.
`static Get(WorldContext)`; `BP void Start(); Next(); Back(); End(); OpenCurrent()`; `BPpure bool IsTouring() const; int32 GetIndex() const; int32 GetNumStops() const; bool IsLastStop() const; bool GetCurrentStop(FWTATourStopRow& Out) const`. Protected `ShowStop(int32)` (walks via `PC->GoToView`, broadcasts), `CacheStops()`, `TArray<FName> StopIds; int32 Index = -1`.

### `UWTADialogueSubsystem : UGameInstanceSubsystem` (`Systems/WTADialogueSubsystem.h`)
`USTRUCT FWTAReply { FText Text; FName Action; FName ActionArg; bool bOffer; FText OfferLabel; }` (BlueprintReadOnly). `bOffer` = show Action as a button labelled `OfferLabel` under the answer instead of running it (what the web showed as a card).
`static Get(WorldContext)`; `BP FWTAReply Ask(FName StaffId, const FString& Question)`; `BPpure FText GetGreeting(FName StaffId, bool bShort) const; TArray<FText> GetChips(FName) const; FText GetHelp(FName) const`; `BP void RebuildIndex()`.
Order inside Ask: greeting → rules Order < 100 (`FRegexPattern`, `(?i)`, MaxWords/StaffOnly/StaffNot; equal Orders by row name) → place alias → exhibit/book title → rules ≥ 100 → TF-IDF best sentence over Facts, Lessons, exhibits, book pages (weighted by what each staff member knows best: Margaret exhibits, Rosa book pages, Mr. Hale lessons, Coach Rae facts) → staff Fallback. Offers: a rule's `bOffer`; "where is …" directions (a "take me / go to" question walks at once); an exhibit or book named by title and a search hit, unless the question says "show me" or asks to be taken there. A page hit's action is `OpenBook <book>#<page>`. Default offer labels by action: "Show me the exhibit", "Open the book", "Take me to the station", "Show me the ride", "Show me the badges", "Take me there", "Start the tour". Protected `TryGreeting/TryRules/TryDirections/TryTitleMatch/TrySearch/Fallback`, `Tokenize/SplitSentences/CountWords`, `AddDoc`, `TArray<FWTASearchDoc> Docs; TMap<FString,int32> DocFrequency`. `FWTASearchDoc` (not reflected): `Title, Sentences, TermCounts, NumTerms, Action, ActionArg, Source` (Source = the attribution sentence appended to a search answer). Directions only fire when the question asks to go somewhere or where something is (web RX.go / RX.wh).

### `UWTARoomSubsystem : UWorldSubsystem` (`Systems/WTARoomSubsystem.h`)
Delegate `FWTARoomChanged(FName RoomId)`; `UP(BlueprintAssignable) OnRoomChanged`.
`static Get(WorldContext)`; `BP void EnterRoom(FName)`; `BPpure FName GetCurrentRoom() const; FName RoomAt(FVector) const; bool HasVisited(FName) const; bool IsFirstVisit() const` (true while handling OnRoomChanged for a first entry); `FName GetStaffForRoom(FName) const`.

### `UWTAGraphicsLibrary : UBlueprintFunctionLibrary` (`Systems/WTAGraphicsLibrary.h`)
`BP static void ApplyQualityPreset(int32 Level)` (0 Low … 4 Cinematic; `SetOverallScalabilityLevel` + `ApplySettings(false)` + `SaveSettings`), `BP static void RunAutoDetect()` (`RunHardwareBenchmark` + `ApplyHardwareBenchmarkResults`), `BPpure static int32 GetQualityPreset()` (-1 custom), `BPpure static FText GetQualityPresetLabel(int32)`.

## UI (all `UUserWidget`, trees built in `NativeOnInitialized`, created with `CreateWidget<UClass>(PC, UClass::StaticClass())`)
### `UWTAActionButton : UButton` (`UI/WTAActionButton.h`)
Delegate `FWTAActionButtonClicked(FName Action, FName Arg, int32 Index)`; `UP FName Action, Arg; int32 Index = -1; FString Payload`; `UP(BlueprintAssignable) OnAction`; `BP void Init(FName InAction, FName InArg, int32 InIndex)` (binds OnClicked → `HandleClicked` once). Internal verbs used by the widgets: `Prev, Next, Close, Page, Link, Reset, Send, Chip, Offer, Enter, Tour, Graphics, Quit, TourBack, TourNext, TourEnd, TourOpen`; anything else is a shared action passed to `AWTAPlayerController::RunAction`.

### `UWTAHudWidget` (`UI/WTAHudWidget.h`)
`BP void SetRoom(const FText& Kicker, const FText& Name, const FText& Sub); SetHoverLabel(const FText&); ShowToast(const FText&, float Seconds); ShowCaption(const FText&); ShowHint(const FText&, float Seconds); HideHint(); ShowTour(int32 Index, int32 Total, const FText& Title, const FText& DateLabel, const FText& Body, const FText& OpenLabel); HideTour(); SetTourVisible(bool); SetBadgeCount(int32 Count, int32 Total); SetCrosshairVisible(bool); ShowStory(const FText& Kicker, const FText& Year, const FText& Title, const FText& Summary, const FText& Hint); HideStory(); SetStoryVisible(bool)`; `BPpure bool IsTourShowing() const; bool IsStoryShowing() const`. The hover label sits on its own small plate under the crosshair (`HoverPlate`: panel fill at 92 %, 1 px dim-brass edge `WTAStyle::BrassDim()`, like the web's `.tag`), so it reads on white walls and pale covers; with a free cursor the plate follows the mouse. The story plaque sits right-centre (nearly solid brass-edged plate, 470 px), empty parts collapse, and it fades in over 0.2 s. Toasts queue (`FWTAToastEntry`). Tour buttons → `UWTATourSubsystem::Back/Next/End/OpenCurrent`.

### `UWTAPanelWidget` (`UI/WTAPanelWidget.h`)
`UENUM EWTAPanelMode { None, Exhibit, Book, Station, Ride, Badges, Places }`.
`BP void ShowExhibit(FName); ShowBook(FName, int32 Page); ShowStation(FName); ShowRide(FName); ShowBadges(); ShowPlaces(); Close()`; `BPpure bool IsOpen() const; EWTAPanelMode GetMode() const; FName GetCurrentId() const; int32 GetCurrentPage() const`. Arrow keys = Prev/Next (`NativeOnKeyDown`). Prev/Next on an exhibit → `PC->StepExhibit(±1)`; on a book → `PC->OpenBook(id, page±1)`; `Link` → `FPlatformProcess::LaunchURL`; `Reset` → `Progress->ResetProgress()`. Protected builders `BeginCard, EndCard, AddText, AddHeading, AddParagraph, AddQuote, AddNote, AddCode, AddList, AddBlock, AddSpacer, AddImage, AddButton, AddLink, SetHeaderExtras(Year, Subtitle), AddSection(Label), AddFact(Label, Value), AddSceneLines(const TArray<FWTAWaxLine>&), AddSourceChips(const TArray<FName>&), SetOpen`. The exhibit card reads like a museum label: kicker, big year (`YearText`), title, italic place line (`SubtitleText`), then sections "In this scene" (wax caption lines, numbered), "The story" (Description, More), the quote, "At a glance" (When, Where, Partners) and "Sources" (wrapping chips). Card width per mode (`CardSize`: Exhibit 900, Book 880, others 780); body text 18 pt with 1.3 line height.

### `UWTAChatWidget` (`UI/WTAChatWidget.h`)
`BP void Open(FName InStaffId); Close(); AddMessage(const FText&, bool bFromPlayer); SetChips(const TArray<FText>&); Send(const FString& Question); ClearConversation(); bool ClickOffer(int32 Index); FocusInput()`; `BPpure bool IsOpen() const; FName GetStaffId() const`; `UP float ActionDelay = 0.55`. Greets once per staff; Send → `Dialogue->Ask`, `Progress->NoteQuestionAsked`, then either a left-aligned offer button under the answer (`FWTAReply::bOffer`; verb `Offer`, Index into `TArray<TPair<FName, FName>> Offers`, runs `PC->RunAction` when clicked) or `PC->RunAction` after ActionDelay (timer). `ClearConversation` empties the messages and offers and cancels a pending action, so the next Open greets again. `UFUNCTION() HandleTextCommitted(const FText&, ETextCommit::Type)`. Overrides `NativeOnKeyDown`: while the text box has focus every key but Escape is handled, so typed letters never reach the game's input actions.

### `UWTAMenuWidget` (`UI/WTAMenuWidget.h`)
`BP void Open(bool bInIntro); Close(); RefreshGraphicsLabel()`; `BPpure bool IsOpen() const; bool IsIntro() const`. Buttons Enter/Resume, Take the tour, Graphics (Low…Cinematic, Auto), Quit.

### `UI/WTAUIStyle.h` (header only)
`WTAStyle::Ink() Panel() Brass() Bone() Card() CardInk() BoneDim() CardInkDim() Scrim() Plate()`, `FromHex(uint32)`, `ToastSeconds = 3.4`, `Font(int32 Size, bool bBold=false)`, `Italic(Size)`, `Mono(Size)` (`FCoreStyle::GetDefaultFontStyle`), `Kicker(Size)` (bold, `LetterSpacing` 140: kickers and section labels), `SolidBrush(Color)`, `RoundedBrush(Color, Radius)`, `EdgedBrush(Color, Radius, Edge, EdgeWidth=1.5)` (rounded fill with an edge line), `BrassDark()`, `ButtonStyle(Fill, Hovered, Pressed)`, `PrimaryButton()`, `SecondaryButton()`, `CardButton()`.
`WTAWidgets::MakeText(UWidgetTree*, Text, Font, Color, bAutoWrap=true)`, `MakePlate(Tree, Fill, Padding, Radius=0)`, `MakeButton(Tree, Label, Action, Arg, Index, Style, Font, TextColor)`, `SetButtonLabel(Button, Label)`.

## Wiring summary (who calls whom)
- Actors → controller: `Execute_Interact(Actor, PC)` → `PC->OpenExhibit/OpenBook/OpenStation/OpenRide/OpenStaffChat`, `PC->GoToView`, `PC->ShowToast/ShowCaption`.
- Subsystems → controller: delegates only (`OnRoomChanged`, `OnBadgeAwarded`, `OnTokenCollected`, `OnTourChanged`); the controller updates the HUD.
- Widgets → controller: `GetOwningPlayer()` cast to `AWTAPlayerController` (`RunAction`, `StepExhibit`, `OpenBook`, `CloseTopPanel`) and the subsystems' static `Get(this)`.
- Controller → character: `GetWTACharacter()->WalkTo/TeleportToView/AddMoveInput/SetSprinting/Jump`.
- Config needed outside C++: `DefaultEngine.ini` `GlobalDefaultGameMode=/Script/WalkTheArchive.WTAGameMode`; `DefaultInput.ini` keeps `DefaultPlayerInputClass=/Script/EnhancedInput.EnhancedPlayerInput` and `DefaultInputComponentClass=/Script/EnhancedInput.EnhancedInputComponent`; `DefaultGame.ini` `[/Script/WalkTheArchive.WTASettings]` table paths.
