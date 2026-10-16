// Walk the Archive - the staff chat (built in C++, no widget asset).
//
// A dark panel: staff name + role header, a scroll box of messages (player right-aligned on brass, staff left on
// panel green), a wrap box of suggestion chips, a text box + Send, and Close. Open(StaffId) greets once per staff
// (the long Greeting the first time, GreetingShort after) and shows the staff's Chips. Send(Question) adds the
// player's line, asks UWTADialogueSubsystem, adds the reply, notes the question for the "curious" badge, and
// after ActionDelay seconds runs the reply's Action through AWTAPlayerController::RunAction (so the panel it opens
// appears after the answer, as on the web). Enter in the text box sends.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Types/SlateEnums.h"
#include "Input/Reply.h"
#include "Input/Events.h"
#include "Layout/Geometry.h"
#include "TimerManager.h"
#include "WTAChatWidget.generated.h"

class UBorder;
class UEditableTextBox;
class UScrollBox;
class UTextBlock;
class UVerticalBox;
class UWrapBox;
class UWTAActionButton;

UCLASS()
class WALKTHEARCHIVE_API UWTAChatWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Open for DT_Staff[StaffId]; switching staff keeps each staff's greeting state. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Open(FName StaffId);

	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Close();

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsOpen() const { return bOpen; }

	UFUNCTION(BlueprintPure, Category = "WTA")
	FName GetStaffId() const { return StaffId; }

	/** Append a message bubble and scroll to the end. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void AddMessage(const FText& Text, bool bFromPlayer);

	/** Replace the chip row. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void SetChips(const TArray<FText>& Chips);

	/** Ask the current staff (empty questions are ignored). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Send(const FString& Question);

	/** Keyboard focus to the text box (Enter key while open). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void FocusInput();

	/** Delay before a reply's action runs (web 0.55 s). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	float ActionDelay = 0.55f;

protected:
	virtual void NativeOnInitialized() override;

	/** While the text box has focus, key presses (other than Escape) stop here so T/M/WASD do not reach the game. */
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;

	/** Buttons: "Send", "Close", "Chip" (Index into the current chips). */
	UFUNCTION()
	void HandleAction(FName Action, FName Arg, int32 Index);

	/** Enter in the text box. */
	UFUNCTION()
	void HandleTextCommitted(const FText& Text, ETextCommit::Type CommitMethod);

	/** Timer callback: run PendingAction through the controller. */
	void RunPendingAction();

	UPROPERTY(Transient) TObjectPtr<UBorder> Scrim;
	UPROPERTY(Transient) TObjectPtr<UBorder> Card;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> NameText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> RoleText;
	UPROPERTY(Transient) TObjectPtr<UScrollBox> MessageScroll;
	UPROPERTY(Transient) TObjectPtr<UVerticalBox> MessageList;
	UPROPERTY(Transient) TObjectPtr<UWrapBox> ChipBox;
	UPROPERTY(Transient) TObjectPtr<UEditableTextBox> InputBox;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> SendButton;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> CloseButton;

	FName StaffId;
	bool bOpen = false;
	TSet<FName> Greeted;
	TArray<FText> CurrentChips;
	FTimerHandle ActionTimer;
	FName PendingAction;
	FName PendingArg;
};
