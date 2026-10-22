// Walk the Archive - the player controller is the hub of the game.
//
// DESIGN
// ------
// The web build had one `ui.js` that every system called into (open a card, toast, walk somewhere). In Unreal that
// role belongs to AWTAPlayerController. It owns the four widgets (HUD, Panel, Chat, Menu), owns the interaction
// component, creates the Enhanced Input objects in code, and exposes the UFUNCTIONs that actors and subsystems
// call: OpenExhibit, StepExhibit, OpenBook, OpenStation, OpenRide, OpenBadges, OpenQuiz, OpenCourse, OpenStaffChat, CloseTopPanel,
// ToggleMenu, ShowToast, ShowCaption, ShowHint, RunAction, GoToView, GoToPlace, SetUIMode, TakePostcard.
// Subsystems never touch widgets directly; they broadcast delegates and the controller updates the HUD.
//
// Panels are exclusive: opening one closes the others (chat closes the panel, the panel closes the chat, the menu
// sits above both). CloseTopPanel() closes in this order and returns true when it closed something:
//   Menu -> Chat -> Panel -> (end the tour). OnBack (Esc / gamepad B) calls it and opens the menu when nothing
// was open. The tour bar hides while a panel or the chat is open and comes back when they close.
//
// Input modes. SetUIMode(true) = FInputModeGameAndUI + visible cursor, movement and look input ignored.
// SetUIMode(false) = FInputModeGameOnly + captured mouse look, unless the cursor is free (Tab): then
// GameAndUI + cursor, the hover trace comes from the mouse, a click on an interactable interacts, a click on the
// floor walks there (NavMesh). UpdateInputMode() derives the real mode from IsAnyPanelOpen() || IsCursorFree().
//
// Enhanced Input is built in BeginPlay with NewObject (no assets): one UInputMappingContext and ten UInputActions.
//   Move (Axis2D)   W/S/A/D (Swizzle + Negate modifiers), Gamepad left stick
//   Look (Axis2D)   Mouse2D, Gamepad right stick (scaled by GamepadLookRate per second)
//   Jump            Space, Gamepad A         Sprint (bool, Started/Completed)  Left Shift, Gamepad left thumb
//   Interact        LMB, E, Gamepad X         Back        Escape, Gamepad B
//   ToggleCursor    Tab                       TourNext    T
//   Places          M                         Chat        Enter
// Handlers: OnMove/OnLook/OnJump/OnSprint/OnSprintEnd/OnInteract/OnBack/OnToggleCursor/OnTourNext/OnPlaces/OnChat/OnPhoto.
// Config/DefaultInput.ini must keep the engine defaults (EnhancedPlayerInput + EnhancedInputComponent).
//
// GoToView(View, bWalk=true) walks the character to the floor point under View.Location (SimpleMoveToLocation),
// remembers the view, and once the walk ends Tick eases the control rotation to View.Yaw/Pitch with
// 1 - exp(-4.5 dt) (the web's face-view easing). bWalk=false teleports (TeleportToView) instead.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "Data/WTATypes.h"
#include "WTAPlayerController.generated.h"

class AWTACharacter;
class UInputAction;
class UInputMappingContext;
class UWTACertificateWidget;
class UWTAPostcardWidget;
class UWTAChatWidget;
class UWTAHudWidget;
class UWTAInteractionComponent;
class UWTAMenuWidget;
class UWTAPanelWidget;
class UWTAPlayTest;
struct FInputActionValue;

/** Fired after SetUIMode: true when a panel, the chat or the menu is open. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FWTAUIModeChanged, bool, bPanelOpen);

UCLASS(Blueprintable)
class WALKTHEARCHIVE_API AWTAPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	AWTAPlayerController();

	// --- Components and widgets --------------------------------------------

	/** Per-frame hover trace and the interact dispatch. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	TObjectPtr<UWTAInteractionComponent> Interaction;

	/** Always-on overlay: room label, crosshair, hover label, toasts, tour bar, captions, badge count, hint. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|UI")
	TObjectPtr<UWTAHudWidget> Hud;

	/** The one modal panel: exhibit card, book reader, station panel, ride card, badges, places. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|UI")
	TObjectPtr<UWTAPanelWidget> Panel;

	/** Staff chat. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|UI")
	TObjectPtr<UWTAChatWidget> Chat;

	/** Intro / pause menu. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|UI")
	TObjectPtr<UWTAMenuWidget> Menu;

	/** The certificate a passed class shows (made on first use, replaced each time). */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|UI")
	TObjectPtr<UWTACertificateWidget> Certificate;

	/** The postcard frame photo mode shows for the moment the picture is taken (made on first use). */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|UI")
	TObjectPtr<UWTAPostcardWidget> Postcard;

	// --- Input objects (created in code, see the header comment) -----------

	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|Input")
	TObjectPtr<UInputMappingContext> MappingContext;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|Input")
	TObjectPtr<UInputAction> MoveAction;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|Input")
	TObjectPtr<UInputAction> LookAction;

	/** Gamepad right stick, kept apart from the mouse so it can be scaled by GamepadLookRate per second. */
	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|Input")
	TObjectPtr<UInputAction> LookStickAction;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|Input")
	TObjectPtr<UInputAction> JumpAction;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|Input")
	TObjectPtr<UInputAction> SprintAction;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|Input")
	TObjectPtr<UInputAction> InteractAction;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|Input")
	TObjectPtr<UInputAction> BackAction;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|Input")
	TObjectPtr<UInputAction> ToggleCursorAction;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|Input")
	TObjectPtr<UInputAction> TourNextAction;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|Input")
	TObjectPtr<UInputAction> PlacesAction;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|Input")
	TObjectPtr<UInputAction> ChatAction;

	UPROPERTY(Transient, BlueprintReadOnly, Category = "WTA|Input")
	TObjectPtr<UInputAction> PhotoAction;

	// --- Feel --------------------------------------------------------------

	/** Multiplier on mouse look (1 = engine default). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float MouseLookScale = 1.f;

	/** Flip if the mouse pitch feels inverted on the target machine. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	bool bInvertMouseY = false;

	/** Gamepad right stick: degrees per second at full deflection. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float GamepadLookRate = 120.f;

	/** Face-view easing rate after an auto-walk (web: 4.5). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Feel")
	float FaceViewRate = 4.5f;

	/** Broadcast from SetUIMode. */
	UPROPERTY(BlueprintAssignable, Category = "WTA")
	FWTAUIModeChanged OnUIModeChanged;

	// --- Panels (each closes the others, marks progress, calls SetUIMode) ---

	/** Open the catalog card for DT_Exhibits[ItemId] and note the exhibit as seen. Does not walk; callers do. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void OpenExhibit(FName ItemId);

	/** Prev/Next through the current exhibit's list (gallery exhibits or wax cards, wrapping), walking to the new one. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void StepExhibit(int32 Delta);

	/** Open the book reader. Page is 0-based into Pages; -1 shows the cover with the table of contents. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void OpenBook(FName BookId, int32 Page);

	/** Open the station panel (title, steps, intro paragraphs). Hands-on logic is phase 1+. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void OpenStation(FName StationId);

	/** Open the ride card (name, card text, note). Ride mechanics are phase 1. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void OpenRide(FName RideId);

	/** Open the badges list (all DT_Badges rows, unlocked or how-to, plus token hints). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void OpenBadges();

	/** Open the token hunt's library card (a stamp per token). RunAction("OpenHunt") does the same. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void OpenHunt();

	/** Open the places list (every DT_Places row as a "walk there" button). M key. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void OpenPlaces();

	/** Open the chat with DT_Staff[StaffId] (greets once per staff, shows the chips). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void OpenStaffChat(FName StaffId);

	/** Open a class's quiz (DT_Talks[TalkId].Quiz) from its first question. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void OpenQuiz(FName TalkId);

	/** Open a course's card (DT_Talks[TalkId] of kind course): the welcome, the station checklist, the quiz once
	    every station is finished. Course actors call it; so does RunAction("OpenCourse", TalkId). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void OpenCourse(FName TalkId);

	/** The class is passed: keep the certificate (progress, the row's badge) and show it made out to Name. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowCertificate(FName TalkId, const FString& Name);

	/** Today, the way a certificate writes it ("22 October 2026"). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	static FString CertificateDate();

	/** Photo mode (P): frame the view as a postcard of the room you are in and write it, with the frame, to
	    Saved/Postcards/<place>_<time>.png (the HUD hidden for that frame; a toast says where it went). Returns
	    the file it will write, or empty when a panel, the chat or the menu is open. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	FString TakePostcard();

	/** The last postcard written this run (empty until one is). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FString GetLastPostcard() const { return LastPostcard; }

	/** Close the top-most open thing (Menu, Chat, Panel, then end the tour). Returns true if something closed. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	bool CloseTopPanel();

	/** Open or close the menu (pause-style; the world keeps running). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ToggleMenu();

	/** True when the panel, the chat or the menu is open. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsAnyPanelOpen() const;

	// --- HUD messages ------------------------------------------------------

	/** Queue a toast line on the HUD (Seconds <= 0 uses the settings default). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowToast(const FText& Text, float Seconds = 0.f);

	/** Show a wax-scene caption line (empty text hides it). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowCaption(const FText& Text);

	/** Show a hint line (room first-visit tips) for the settings' HintSeconds. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowHint(const FText& Text);

	// --- Walk-up story plaque ----------------------------------------------

	/** Show DT_Exhibits[ItemId] as a museum plaque on the HUD (kicker, year, title, first lines, "E to read"). NAME_None hides it. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowStoryPlaque(FName ItemId);

	/** A Wax Hall stage reports the player stepping into (bInside) or out of its scene; E then opens that scene's card. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void SetStageStory(FName ItemId, bool bInside);

	/** The wax scene the player is watching: inside its trigger and, when several overlap, the one the camera faces. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FName GetActiveStageStory() const { return StageStoryId; }

	// --- Actions and travel ------------------------------------------------

	/** Run one action of the shared vocabulary (GoPlace, OpenItem, OpenBook, OpenStation, OpenRide, StartTour, OpenBadges,
	    OpenQuiz, OpenCourse, OpenHunt, StartTalk). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void RunAction(FName Action, FName Arg);

	/** Walk (bWalk) or teleport the player to a view, then face its yaw/pitch. Ignores views with bValid false. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void GoToView(const FWTAView& View, bool bWalk);

	/** Walk to DT_Places[PlaceId].View. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void GoToPlace(FName PlaceId);

	/** Switch the input mode: panel open = cursor + UI, otherwise captured mouse look (or free cursor). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void SetUIMode(bool bPanelOpen);

	/** Tab: free the cursor without opening a panel (click floor to walk, click things to interact). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void SetCursorFree(bool bFree);

	/** True while the cursor is free (Tab). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsCursorFree() const { return bCursorFree; }

	/** The possessed pawn as AWTACharacter (may be null before possession). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	AWTACharacter* GetWTACharacter() const;

	/**
	 * QA: closes the menu and panels, then visits every valid place view (DT_Places), every staff talk view (DT_Staff)
	 * and a view of every Wax Hall stage from the aisle (DT_WaxScenes). At each it waits SecondsPerShot (Lumen and
	 * exposure settle) and saves a screenshot with the HUD to Saved/Screenshots/<platform>/QA/<NN>_<name>.png.
	 * The player keeps walking mode (no ghosting). Console: WTAShotTour [Seconds]. Logs WTA_SHOTTOUR lines.
	 */
	UFUNCTION(Exec, BlueprintCallable, Category = "WTA|QA")
	void WTAShotTour(float SecondsPerShot = 5.f);

	/** QA: asks every staff member their own chips, then each line of Saved/QA/chat_questions.txt (or a short built-in
	 *  list); logs one WTA_CHAT line per answer (text, action, arg, offer label) and "WTA_CHAT done N questions". */
	UFUNCTION(Exec, BlueprintCallable, Category = "WTA|QA")
	void WTAChatTest();

	/**
	 * QA: for each line "<staff id> | <question>" of Saved/QA/chat_shots.txt (or a built-in set), stands the player at
	 * that staff member's talk view, opens a fresh chat, asks the question and, SecondsPerShot later, saves a
	 * screenshot with the UI to Saved/Screenshots/<platform>/QA/chat_<NN>_<staff>.png. A line ending in "| click" then
	 * clicks the answer's first offer button and saves chat_<NN>_<staff>_after.png. Logs WTA_CHATSHOT lines.
	 */
	UFUNCTION(Exec, BlueprintCallable, Category = "WTA|QA")
	void WTAChatShots(float SecondsPerShot = 2.5f);

	/**
	 * QA: plays the game like a player and logs a PASS / FAIL line per check (see UWTAPlayTest): the menu, walking into
	 * every wall of Saved/QA/walk_tests.txt, E on every interactable, the Wax Hall stories, the tour, chat, badges,
	 * graphics presets, frame rate, the people's poses and a close-up of every face. Console: WTAPlayTest [phases]
	 * ("all" or e.g. "faces people"). Logs WTA_PLAY lines and "WTA_PLAY done ...".
	 */
	UFUNCTION(Exec, BlueprintCallable, Category = "WTA|QA")
	void WTAPlayTest(const FString& Phases = TEXT("all"));

protected:
	/** The play test drives the input handlers directly when keys cannot be sent through Slate. */
	friend class UWTAPlayTest;

	virtual void BeginPlay() override;
	virtual void SetupInputComponent() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void OnPossess(APawn* InPawn) override;

	/** NewObject the mapping context and actions, map the keys, add the context to the local player subsystem. */
	void CreateInputObjects();

	/** CreateWidget the four widgets, add them to the viewport (HUD z 0, Panel 10, Chat 20, Menu 30), bind delegates. */
	void CreateWidgets();

	/** Apply the input mode derived from IsAnyPanelOpen() and bCursorFree. */
	void UpdateInputMode();

	/** Hide the tour bar while a panel/chat is open and show it again after. */
	void RefreshTourBar();

	/** Pick the plaque to show: the exhibit under the crosshair wins, else the wax scene the player stands in. */
	void RefreshStoryPlaque();

	/** Among the wax scenes the player stands in, make the one the camera faces the stage story. */
	void UpdateFacedStage();

	// Input handlers (bound in SetupInputComponent with UEnhancedInputComponent::BindAction).
	void OnMove(const FInputActionValue& Value);
	void OnLook(const FInputActionValue& Value);
	void OnLookStick(const FInputActionValue& Value);
	void OnJump(const FInputActionValue& Value);
	void OnJumpEnd(const FInputActionValue& Value);
	void OnSprint(const FInputActionValue& Value);
	void OnSprintEnd(const FInputActionValue& Value);
	void OnInteract(const FInputActionValue& Value);
	void OnBack(const FInputActionValue& Value);
	void OnToggleCursor(const FInputActionValue& Value);
	void OnTourNext(const FInputActionValue& Value);
	void OnPlaces(const FInputActionValue& Value);
	void OnChat(const FInputActionValue& Value);
	void OnPhoto(const FInputActionValue& Value);

	// Delegate sinks (subsystems and the interaction component broadcast; the controller updates the HUD).
	UFUNCTION()
	void HandleHoverChanged(const FText& Label);

	UFUNCTION()
	void HandleRoomChanged(FName RoomId);

	UFUNCTION()
	void HandleBadgeAwarded(FName BadgeId);

	UFUNCTION()
	void HandleTokenCollected(FName TokenId, int32 Found, int32 Total);

	UFUNCTION()
	void HandleTourChanged(int32 Index);

	UFUNCTION()
	void HandleProgressReset();

	/** View to face once the current auto-walk ends (GoToView with bWalk). */
	FWTAView PendingView;
	bool bHasPendingView = false;
	/** Long trips (> 4 m, web travelFace) turn the camera toward the direction of travel while walking. */
	bool bFaceTravelDirection = false;
	bool bCursorFree = false;
	bool bUIMode = false;
	/** A tour is running (last HandleTourChanged index >= 0). */
	bool bTourActive = false;
	/** The tour freed the cursor (so its bar's buttons can be clicked) and gives mouse look back when it ends. */
	bool bCursorFreedForTour = false;
	/** Story plaque sources: the exhibit under the crosshair and the wax scene the player stands in; what shows now. */
	FName HoverStoryId;
	FName StageStoryId;
	FName ShownStoryId;
	/** Every wax scene whose trigger the player is inside (scenes face each other across the aisle and overlap). */
	TArray<FName> InsideStageIds;

	/** WTAShotTour: teleport to the current view, then capture it after ShotTourSeconds and move on. */
	void ShotTourTeleport();
	void ShotTourCapture();
	TArray<TPair<FString, FWTAView>> ShotTourViews;
	int32 ShotTourIndex = INDEX_NONE;
	float ShotTourSeconds = 5.f;
	FTimerHandle ShotTourTimer;

	/** WTAChatShots: ask the current question in a fresh chat, capture it after ChatShotSeconds, optionally click its
	 *  first offer button and capture what that opens, then move on. */
	void ChatShotAsk();
	void ChatShotCapture();
	void ChatShotClick();
	TArray<TPair<FName, FString>> ChatShots;
	TArray<bool> ChatShotClicks;
	int32 ChatShotIndex = INDEX_NONE;
	float ChatShotSeconds = 2.5f;
	bool bChatShotClicked = false;
	FTimerHandle ChatShotTimer;

	/** TakePostcard: the frame comes down and the HUD comes back a few frames after the picture is requested. */
	void FinishPostcard();
	FTimerHandle PostcardTimer;
	FString LastPostcard;

	/** WTAPlayTest: the scripted play test, created on first use. */
	UPROPERTY(Transient)
	TObjectPtr<UWTAPlayTest> PlayTest;
};
