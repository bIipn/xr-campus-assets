// Walk the Archive - the keyboard a headset types with (see UI/WTAVRKeyboardWidget.h).

#include "UI/WTAVRKeyboardWidget.h"
#include "Core/WTAPlayerController.h"
#include "Core/WTAText.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/ButtonSlot.h"
#include "Components/EditableTextBox.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "UI/WTAActionButton.h"
#include "UI/WTAUIStyle.h"

namespace
{
	const FName NAME_KeyChar(TEXT("Key"));
	const FName NAME_KeyBack(TEXT("Back"));
	const FName NAME_KeyShift(TEXT("Shift"));
	const FName NAME_KeySpace(TEXT("Space"));
	const FName NAME_KeyEnter(TEXT("Enter"));
	const FName NAME_KeyHide(TEXT("Hide"));

	/** A key 80 px across (about 4 degrees at the keyboard's distance: easy to hold a laser on), 62 high, 8 apart. */
	constexpr float KeyWidth = 80.f;
	constexpr float KeyHeight = 62.f;
	constexpr float KeyGap = 8.f;
	/** The preview shows the end of a long text. */
	constexpr int32 PreviewChars = 70;

	/** Keys a step lighter than the HUD's buttons: the campus's exposure and tonemapping deepen dark tones on the
	    VR screens, and a key must stand clear of the plate it sits on. */
	FButtonStyle KeyStyle()
	{
		return WTAStyle::ButtonStyle(WTAStyle::FromHex(0x34493f), WTAStyle::FromHex(0x46604f), WTAStyle::FromHex(0x24352f));
	}
}

void UWTAVRKeyboardWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	UWidgetTree* Tree = WidgetTree;
	if (Tree == nullptr)
	{
		return;
	}

	// A solid ink plate with a brass edge, filling the screen: a keyboard is a thing, not a window.
	UBorder* Plate = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
	FLinearColor Edge = WTAStyle::Brass();
	Edge.A = 0.6f;
	Plate->SetBrush(WTAStyle::EdgedBrush(WTAStyle::Ink(), 18.f, Edge, 2.f));
	Plate->SetPadding(FMargin(16.f, 12.f, 16.f, 14.f));
	Tree->RootWidget = Plate;

	UVerticalBox* Column = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Plate->SetContent(Column);

	// What is being typed: the box's hint as a kicker, the text so far with a caret.
	UBorder* Preview = WTAWidgets::MakePlate(Tree, WTAStyle::Panel(), FMargin(16.f, 8.f, 16.f, 9.f), 10.f);
	UVerticalBox* PreviewColumn = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Preview->SetContent(PreviewColumn);
	HintText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Kicker(11), WTAStyle::Brass(), false);
	PreviewColumn->AddChildToVerticalBox(HintText)->SetPadding(FMargin(0.f, 0.f, 0.f, 2.f));
	TypedText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(21), WTAStyle::Bone(), false);
	PreviewColumn->AddChildToVerticalBox(TypedText);
	Column->AddChildToVerticalBox(Preview)->SetPadding(FMargin(0.f, 0.f, 0.f, 12.f));

	// Five rows, each centred; a typewriter's stagger from the wide keys at the ends.
	auto NewRow = [&](bool bLast)
	{
		UHorizontalBox* Row = Tree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
		UVerticalBoxSlot* RowSlot = Column->AddChildToVerticalBox(Row);
		RowSlot->SetHorizontalAlignment(HAlign_Center);
		RowSlot->SetPadding(FMargin(0.f, 0.f, 0.f, bLast ? 0.f : KeyGap));
		return Row;
	};
	auto AddChars = [&](UHorizontalBox* Row, const TCHAR* Chars)
	{
		for (const TCHAR* C = Chars; *C != 0; ++C)
		{
			UWTAActionButton* Key = AddKey(Row, FText::FromString(FString::Chr(*C)), NAME_KeyChar, static_cast<int32>(*C), KeyWidth, false);
			if (FChar::IsAlpha(*C))
			{
				LetterKeys.Add(Key);
			}
		}
	};
	UHorizontalBox* Row1 = NewRow(false);
	AddChars(Row1, TEXT("1234567890"));
	AddKey(Row1, WTAText(TEXT("Delete")), NAME_KeyBack, 0, 128.f, false);
	AddChars(NewRow(false), TEXT("qwertyuiop-"));
	AddChars(NewRow(false), TEXT("asdfghjkl':"));
	UHorizontalBox* Row4 = NewRow(false);
	ShiftKey = AddKey(Row4, WTAText(TEXT("Shift")), NAME_KeyShift, 0, 128.f, false);
	AddChars(Row4, TEXT("zxcvbnm,.?"));
	UHorizontalBox* Row5 = NewRow(true);
	AddKey(Row5, WTAText(TEXT("Hide")), NAME_KeyHide, 0, 168.f, false);
	AddKey(Row5, WTAText(TEXT("Space")), NAME_KeySpace, 0, 560.f, false);
	EnterKey = AddKey(Row5, WTAText(TEXT("Done")), NAME_KeyEnter, 0, 264.f, true);
	Refresh();
}

UWTAActionButton* UWTAVRKeyboardWidget::AddKey(UHorizontalBox* Row, const FText& Label, FName Action, int32 Char, float Width, bool bPrimary)
{
	UWidgetTree* Tree = WidgetTree;
	const bool bWord = Char == 0;
	UWTAActionButton* Key = WTAWidgets::MakeButton(Tree, Label, Action, NAME_None, Char,
		bPrimary ? WTAStyle::PrimaryButton() : KeyStyle(), bWord ? WTAStyle::Font(15, true) : WTAStyle::Font(21),
		bPrimary ? WTAStyle::Ink() : WTAStyle::Bone());
	Key->OnAction.AddDynamic(this, &UWTAVRKeyboardWidget::HandleAction);
	if (UButtonSlot* LabelSlot = Cast<UButtonSlot>(Key->GetContentSlot()))
	{
		LabelSlot->SetHorizontalAlignment(HAlign_Center);
		LabelSlot->SetVerticalAlignment(VAlign_Center);
	}
	USizeBox* KeyBox = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	KeyBox->SetWidthOverride(Width);
	KeyBox->SetHeightOverride(KeyHeight);
	KeyBox->SetContent(Key);
	UHorizontalBoxSlot* KeySlot = Row->AddChildToHorizontalBox(KeyBox);
	KeySlot->SetPadding(FMargin(Row->GetChildrenCount() > 1 ? KeyGap : 0.f, 0.f, 0.f, 0.f));
	return Key;
}

void UWTAVRKeyboardWidget::SetTarget(UEditableTextBox* Box, const FText& EnterLabel)
{
	Target = Box;
	if (EnterKey != nullptr && !EnterLabel.IsEmpty())
	{
		WTAWidgets::SetButtonLabel(EnterKey, EnterLabel);
	}
	bShift = Box != nullptr && ShouldAutoShift();
	Refresh();
}

void UWTAVRKeyboardWidget::Type(const FString& Characters)
{
	UEditableTextBox* Box = Target.Get();
	if (Box == nullptr)
	{
		return;
	}
	FString Text = Box->GetText().ToString();
	if (Text.Len() >= MaxLength)
	{
		return;
	}
	Text += Characters;
	Text.LeftInline(MaxLength);
	Box->SetText(FText::FromString(Text));
}

bool UWTAVRKeyboardWidget::ShouldAutoShift() const
{
	const UEditableTextBox* Box = Target.Get();
	if (Box == nullptr)
	{
		return false;
	}
	const FString Text = Box->GetText().ToString();
	const FString Trimmed = Text.TrimEnd();
	if (Trimmed.IsEmpty())
	{
		return true;
	}
	// A new sentence after ". ", "? " or "! " (not inside "192.168.": no space after the point).
	const TCHAR Last = Trimmed[Trimmed.Len() - 1];
	return Text.Len() > Trimmed.Len() && (Last == TEXT('.') || Last == TEXT('?') || Last == TEXT('!'));
}

void UWTAVRKeyboardWidget::HandleAction(FName Action, FName Arg, int32 Index)
{
	AWTAPlayerController* PC = Cast<AWTAPlayerController>(GetOwningPlayer());
	UEditableTextBox* Box = Target.Get();
	if (Action == NAME_KeyHide || Box == nullptr)
	{
		if (PC != nullptr)
		{
			PC->HideVRKeyboard();
		}
		return;
	}
	if (Action == NAME_KeyChar && Index > 0)
	{
		const TCHAR Char = static_cast<TCHAR>(Index);
		Type(FString::Chr(bShift ? FChar::ToUpper(Char) : Char));
		bShift = ShouldAutoShift();
	}
	else if (Action == NAME_KeySpace)
	{
		Type(TEXT(" "));
		bShift = ShouldAutoShift();
	}
	else if (Action == NAME_KeyBack)
	{
		FString Text = Box->GetText().ToString();
		if (!Text.IsEmpty())
		{
			Text.LeftChopInline(1);
			Box->SetText(FText::FromString(Text));
		}
		bShift = ShouldAutoShift();
	}
	else if (Action == NAME_KeyShift)
	{
		bShift = !bShift;
	}
	else if (Action == NAME_KeyEnter)
	{
		// As the Enter key: the box commits (the chat sends the question). The keyboard goes first, since the commit
		// may close the card or open another.
		const FText Text = Box->GetText();
		if (PC != nullptr)
		{
			PC->HideVRKeyboard();
		}
		Box->OnTextCommitted.Broadcast(Text, ETextCommit::OnEnter);
		return;
	}
	Refresh();
}

void UWTAVRKeyboardWidget::Refresh()
{
	for (UWTAActionButton* Key : LetterKeys)
	{
		if (Key != nullptr)
		{
			const TCHAR Char = static_cast<TCHAR>(Key->Index);
			WTAWidgets::SetButtonLabel(Key, FText::FromString(FString::Chr(bShift ? FChar::ToUpper(Char) : Char)));
		}
	}
	if (ShiftKey != nullptr)
	{
		ShiftKey->SetStyle(bShift ? WTAStyle::PrimaryButton() : KeyStyle());
		if (UTextBlock* Label = Cast<UTextBlock>(ShiftKey->GetChildAt(0)))
		{
			Label->SetColorAndOpacity(FSlateColor(bShift ? WTAStyle::Ink() : WTAStyle::Bone()));
		}
	}
	const UEditableTextBox* Box = Target.Get();
	if (HintText != nullptr)
	{
		HintText->SetText(Box != nullptr ? WTAUpper(Box->GetHintText()) : FText::GetEmpty());
	}
	if (TypedText != nullptr)
	{
		FString Shown = Box != nullptr ? Box->GetText().ToString() : FString();
		if (Shown.Len() > PreviewChars)
		{
			Shown = TEXT("…") + Shown.Right(PreviewChars - 1);
		}
		TypedText->SetText(FText::FromString(Shown + TEXT("|")));
	}
}
