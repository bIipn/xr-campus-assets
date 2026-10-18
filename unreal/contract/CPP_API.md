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
| `FWTAPlaceRow` | `FText Label; TArray<FString> Aliases; FWTAView View; FText Directions` |
| `FWTATourStopRow` | `int32 Index; FName Kind, ItemId; FText Title, DateLabel, Body; FWTAView View; FText OpenLabel; FName Action, ActionArg` |
| `FWTAStaffRow` | `FText DisplayName, Role, Monogram; FLinearColor Color; TArray<FName> Rooms; FVector Location; float Yaw; FWTAView TalkView; FText Greeting, GreetingShort, Help, Fallback; TArray<FText> Chips; FName RocketboxId; FString LookNotes; TSoftClassPtr<AActor> MetaHuman` |
| `FWTAStaffRuleRow` | `int32 Order; FString Pattern; int32 MaxWords; TArray<FName> StaffOnly, StaffNot; FText Answer; FName Action, ActionArg` |
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
- `BP void RunAction(FName Action, FName Arg)` — GoPlace/OpenItem/OpenBook/OpenStation/OpenRide/StartTour/OpenBadges; OpenItem and OpenStation also walk to the row's View.
- `BP void GoToView(const FWTAView& View, bool bWalk)` — walk (NavMesh) then face, or teleport; ignores `bValid == false`. `BP void GoToPlace(FName PlaceId)`.
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
**`UP FName StaffId`**; `UP UStaticMeshComponent* PlaceholderBody; UChildActorComponent* MetaHumanChild; UTextRenderComponent* NameLabel; UBoxComponent* PickZone` (hover target over the body and the floating name, 80 × 80 × 215 cm, QueryOnly, blocks Visibility only); `UP float LookAtDistance=1200, TurnRate=4`; `UP(BlueprintReadOnly) FText DisplayName, StaffRole` (not `Role`: `AActor::Role` is already a reflected property), `FLinearColor Color; FWTAView TalkView`; `UP TSoftObjectPtr<UAnimSequence> IdleAnimation` (default `UWTAPeopleLibrary::DefaultIdlePath`), `UP float MetaHumanYawOffset = -90` (MetaHuman Creator Blueprints face +Y); `BP void ApplyStaffRow()`, `BP void Talk(const FText&)`, `BPpure bool IsTalking() const`. When `DT_Staff.MetaHuman` loads, the child gets yaw `MetaHumanYawOffset` and, in a game world, loops `IdleAnimation` (`UWTAPeopleLibrary::PlayPose`). Interact: `PC->OpenStaffChat(StaffId)` (its `Interact_Implementation` parameter is `InController`: `APawn::Controller` exists); ViewSpot = TalkView; label "Ask DisplayName".

### `UWTAPeopleLibrary : UBlueprintFunctionLibrary` (`World/WTAPeopleLibrary.h`)
MetaHuman people built by `Content/Python/wta_people`. `static const TCHAR* DefaultIdlePath` (`/Game/WTA/Characters/Common/Anims/AS_WTA_StandIdle`); `BPpure static FSoftClassPath MetaHumanClassPath(FName Person)` (`/Game/WTA/Characters/<Person>/BP_<Person>.BP_<Person>_C`); `BP static UClass* LoadMetaHumanClass(FName Person)` (null, without a load warning, while the package does not exist); `BP static USkeletalMeshComponent* FindBody(AActor*)` (component named `Body`, else the leader-pose mesh); `BP static bool PlayPose(AActor*, UAnimSequence*, bool bLoop, float StartTime)` (single-node; when not looping it holds the frame, and every mesh evaluates at LOD0 even off screen, through `ULODSyncComponent::ForcedLOD = 0` and `AlwaysTickPoseAndRefreshBones`); `BP static void Freeze(AActor*)` (`bNoSkeletonUpdate` on every skeletal mesh keeps the evaluated bones, the meshes keep ticking so LODs still switch, and LODSync goes back to automatic); `BPpure static float PersonPhase(FName)` (stable 0..1); `BP static bool SetAnimationSkeleton(UAnimSequence*, USkeleton*)` (editor only, `UAnimationAsset::ReplaceSkeleton`; false in a game build; the `idle` build step uses it to put the idle copy on the Common body skeleton).

### `AWTARoomVolume : AActor` (`World/WTARoomVolume.h`)
**`UP FName RoomId`**, **`UP FVector Extent`** (300,300,220); `UP UBoxComponent* Bounds` (root, overlaps Pawn only). `OnConstruction` applies Extent; `NotifyActorBeginOverlap` → `UWTARoomSubsystem::EnterRoom(RoomId)` for the player pawn.

### `AWTAWaxStageActor : AActor` (`World/WTAWaxStageActor.h`)
**`UP FName SceneId`**, **`UP FVector TriggerExtent`** (400,300,220); `UP UBoxComponent* Trigger`; `UP float WatchSecondsForCredit = 5`; `BPpure bool IsLive() const`, `BPpure float GetPlayTime() const`; overrides `OnConstruction`, `NotifyActorBeginOverlap/EndOverlap`, `BeginPlay`, `Tick`; protected `UP(Transient) FWTAWaxSceneRow Scene` + state. Inside: loops `Lines` as HUD captions (`PC->ShowCaption`), credits `NoteWaxScene` after 5 s. Entering / leaving the trigger calls `PC->SetStageStory(ItemId, true/false)` (the scene's walk-up plaque; E opens its card). Reenactors: `UP TSoftObjectPtr<UAnimSequence> FigurePose` (default `UWTAPeopleLibrary::DefaultIdlePath`), `UP float FigureYawOffset = -90` (MetaHuman Creator Blueprints face +Y), `UP(Transient) TArray<AActor*> Figures`; `BeginPlay` spawns every row `Figures` entry whose MetaHuman is built at `StageLocation + FRotator(0,StageYaw,0).RotateVector(Offset)`, yaw `StageYaw + Yaw + FigureYawOffset`, collision off, holding frame `PersonPhase(Person) * length` of `FigurePose`; `FreezeFigures` (timer, 1.5 s) freezes them with `UWTAPeopleLibrary::Freeze`; `EndPlay` destroys them.

## Systems
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
`USTRUCT FWTAReply { FText Text; FName Action; FName ActionArg; }` (BlueprintReadOnly).
`static Get(WorldContext)`; `BP FWTAReply Ask(FName StaffId, const FString& Question)`; `BPpure FText GetGreeting(FName StaffId, bool bShort) const; TArray<FText> GetChips(FName) const; FText GetHelp(FName) const`; `BP void RebuildIndex()`.
Order inside Ask: greeting → rules Order < 100 (`FRegexPattern`, `(?i)`, MaxWords/StaffOnly/StaffNot) → place alias → exhibit/book title → rules ≥ 100 → TF-IDF best sentence over Facts, Lessons, exhibits, book pages → staff Fallback. Protected `TryGreeting/TryRules/TryDirections/TryTitleMatch/TrySearch/Fallback`, `Tokenize/SplitSentences/CountWords`, `AddDoc`, `TArray<FWTASearchDoc> Docs; TMap<FString,int32> DocFrequency`. `FWTASearchDoc` (not reflected): `Title, Sentences, TermCounts, NumTerms, Action, ActionArg, Source` (Source = the attribution sentence appended to a search answer). Directions only fire when the question asks to go somewhere or where something is (web RX.go / RX.wh).

### `UWTARoomSubsystem : UWorldSubsystem` (`Systems/WTARoomSubsystem.h`)
Delegate `FWTARoomChanged(FName RoomId)`; `UP(BlueprintAssignable) OnRoomChanged`.
`static Get(WorldContext)`; `BP void EnterRoom(FName)`; `BPpure FName GetCurrentRoom() const; FName RoomAt(FVector) const; bool HasVisited(FName) const; bool IsFirstVisit() const` (true while handling OnRoomChanged for a first entry); `FName GetStaffForRoom(FName) const`.

### `UWTAGraphicsLibrary : UBlueprintFunctionLibrary` (`Systems/WTAGraphicsLibrary.h`)
`BP static void ApplyQualityPreset(int32 Level)` (0 Low … 4 Cinematic; `SetOverallScalabilityLevel` + `ApplySettings(false)` + `SaveSettings`), `BP static void RunAutoDetect()` (`RunHardwareBenchmark` + `ApplyHardwareBenchmarkResults`), `BPpure static int32 GetQualityPreset()` (-1 custom), `BPpure static FText GetQualityPresetLabel(int32)`.

## UI (all `UUserWidget`, trees built in `NativeOnInitialized`, created with `CreateWidget<UClass>(PC, UClass::StaticClass())`)
### `UWTAActionButton : UButton` (`UI/WTAActionButton.h`)
Delegate `FWTAActionButtonClicked(FName Action, FName Arg, int32 Index)`; `UP FName Action, Arg; int32 Index = -1; FString Payload`; `UP(BlueprintAssignable) OnAction`; `BP void Init(FName InAction, FName InArg, int32 InIndex)` (binds OnClicked → `HandleClicked` once). Internal verbs used by the widgets: `Prev, Next, Close, Page, Link, Reset, Send, Chip, Enter, Tour, Graphics, Quit, TourBack, TourNext, TourEnd, TourOpen`; anything else is a shared action passed to `AWTAPlayerController::RunAction`.

### `UWTAHudWidget` (`UI/WTAHudWidget.h`)
`BP void SetRoom(const FText& Kicker, const FText& Name, const FText& Sub); SetHoverLabel(const FText&); ShowToast(const FText&, float Seconds); ShowCaption(const FText&); ShowHint(const FText&, float Seconds); HideHint(); ShowTour(int32 Index, int32 Total, const FText& Title, const FText& DateLabel, const FText& Body, const FText& OpenLabel); HideTour(); SetTourVisible(bool); SetBadgeCount(int32 Count, int32 Total); SetCrosshairVisible(bool); ShowStory(const FText& Kicker, const FText& Year, const FText& Title, const FText& Summary, const FText& Hint); HideStory(); SetStoryVisible(bool)`; `BPpure bool IsTourShowing() const; bool IsStoryShowing() const`. The story plaque sits right-centre (brass-edged plate, 470 px), empty parts collapse, and it fades in over 0.2 s. Toasts queue (`FWTAToastEntry`). Tour buttons → `UWTATourSubsystem::Back/Next/End/OpenCurrent`.

### `UWTAPanelWidget` (`UI/WTAPanelWidget.h`)
`UENUM EWTAPanelMode { None, Exhibit, Book, Station, Ride, Badges, Places }`.
`BP void ShowExhibit(FName); ShowBook(FName, int32 Page); ShowStation(FName); ShowRide(FName); ShowBadges(); ShowPlaces(); Close()`; `BPpure bool IsOpen() const; EWTAPanelMode GetMode() const; FName GetCurrentId() const; int32 GetCurrentPage() const`. Arrow keys = Prev/Next (`NativeOnKeyDown`). Prev/Next on an exhibit → `PC->StepExhibit(±1)`; on a book → `PC->OpenBook(id, page±1)`; `Link` → `FPlatformProcess::LaunchURL`; `Reset` → `Progress->ResetProgress()`. Protected builders `BeginCard, EndCard, AddText, AddHeading, AddParagraph, AddQuote, AddNote, AddCode, AddList, AddBlock, AddSpacer, AddImage, AddButton, AddLink, SetHeaderExtras(Year, Subtitle), AddSection(Label), AddFact(Label, Value), AddSceneLines(const TArray<FWTAWaxLine>&), AddSourceChips(const TArray<FName>&), SetOpen`. The exhibit card reads like a museum label: kicker, big year (`YearText`), title, italic place line (`SubtitleText`), then sections "In this scene" (wax caption lines, numbered), "The story" (Description, More), the quote, "At a glance" (When, Where, Partners) and "Sources" (wrapping chips). Card width per mode (`CardSize`: Exhibit 900, Book 880, others 780); body text 18 pt with 1.3 line height.

### `UWTAChatWidget` (`UI/WTAChatWidget.h`)
`BP void Open(FName InStaffId); Close(); AddMessage(const FText&, bool bFromPlayer); SetChips(const TArray<FText>&); Send(const FString& Question); FocusInput()`; `BPpure bool IsOpen() const; FName GetStaffId() const`; `UP float ActionDelay = 0.55`. Greets once per staff; Send → `Dialogue->Ask`, `Progress->NoteQuestionAsked`, then `PC->RunAction` after ActionDelay (timer). `UFUNCTION() HandleTextCommitted(const FText&, ETextCommit::Type)`. Overrides `NativeOnKeyDown`: while the text box has focus every key but Escape is handled, so typed letters never reach the game's input actions.

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
