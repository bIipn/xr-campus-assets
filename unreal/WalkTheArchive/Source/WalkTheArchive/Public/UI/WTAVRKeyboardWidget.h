// Walk the Archive - the keyboard a headset types with: keys the laser presses, on a screen of its own (VR).
//
// A headset has no keys, and OpenXR on a PC offers no system keyboard, so VR brings its own. AWTAPlayerController
// shows it on a world screen under the card when the laser presses a text box (the staff chat's question, the visit's
// name and address, a certificate's name, a Lost Story's title and teller) and it types into that box directly
// (UEditableTextBox::SetText): no Slate focus is involved, so pressing a key never takes anything from the box. A
// preview line repeats the box's hint and what is typed so far, since the box itself may be out of view. Shift is
// one-shot and comes on by itself at the start of the text and of a sentence. Enter commits the box as the Enter key
// would (OnTextCommitted with OnEnter: the chat sends) and the keyboard goes; Hide only goes.
//
// Keys are UWTAActionButtons: Action "Key" with the character's code as Index (letters lower case), and "Back",
// "Shift", "Space", "Enter", "Hide".

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "WTAVRKeyboardWidget.generated.h"

class UEditableTextBox;
class UTextBlock;
class UWTAActionButton;

UCLASS()
class WALKTHEARCHIVE_API UWTAVRKeyboardWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Type into Box from now on (null: none); EnterLabel names the Enter key ("Send", "Done"). */
	void SetTarget(UEditableTextBox* Box, const FText& EnterLabel);

	/** The box being typed into, or null. */
	UEditableTextBox* GetTarget() const { return Target.Get(); }

	/** The longest text the keyboard types into a box. */
	static constexpr int32 MaxLength = 160;

	/** The layout size the keyboard is drawn at (its screen's pixels). */
	static FIntPoint DrawSize() { return FIntPoint(1100, 452); }

protected:
	virtual void NativeOnInitialized() override;

	UFUNCTION()
	void HandleAction(FName Action, FName Arg, int32 Index);

	/** One key of Width x 62 px in Row, labelled Label (a character key when Char is set). */
	UWTAActionButton* AddKey(class UHorizontalBox* Row, const FText& Label, FName Action, int32 Char, float Width, bool bPrimary);

	/** Add Characters at the end of the box's text (up to MaxLength). */
	void Type(const FString& Characters);

	/** Shift's own state from the text: on at the start and after a sentence's end. */
	bool ShouldAutoShift() const;

	/** The letters in the shift's case, Shift lit while on, the preview line. */
	void Refresh();

	TWeakObjectPtr<UEditableTextBox> Target;
	bool bShift = false;

	UPROPERTY(Transient) TObjectPtr<UTextBlock> HintText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> TypedText;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> ShiftKey;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> EnterKey;
	UPROPERTY(Transient) TArray<TObjectPtr<UWTAActionButton>> LetterKeys;
};
