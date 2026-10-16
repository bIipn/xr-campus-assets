// Walk the Archive - the player controller is the hub of the game.
//
// DESIGN
// ------
// The web build had one `ui.js` that every system called into (open a card, toast, walk somewhere). In Unreal that
// role belongs to AWTAPlayerController. It owns the four widgets (HUD, Panel, Chat, Menu), owns the interaction
// component, creates the Enhanced Input objects in code, and exposes the UFUNCTIONs that actors and subsystems
// call: OpenExhibit, StepExhibit, OpenBook, OpenStation, OpenRide, OpenBadges, OpenStaffChat, CloseTopPanel,
// ToggleMenu, ShowToast, ShowCaption, ShowHint, RunAction, GoToView, GoToPlace, SetUIMode.
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
// Handlers: OnMove/OnLook/OnJump/OnSprint/OnSprintEnd/OnInteract/OnBack/OnToggleCursor/OnTourNext/OnPlaces/OnChat.
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
class UWTAChatWidget;
class UWTAHudWidget;
class UWTAInteractionComponent;
class UWTAMenuWidget;
class UWTAPanelWidget;
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

	/** Open the places list (every DT_Places row as a "walk there" button). M key. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void OpenPlaces();

	/** Open the chat with DT_Staff[StaffId] (greets once per staff, shows the chips). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void OpenStaffChat(FName StaffId);

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

	// --- Actions and travel ------------------------------------------------

	/** Run one action of the shared vocabulary (GoPlace, OpenItem, OpenBook, OpenStation, OpenRide, StartTour, OpenBadges). */
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

protected:
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
};
