// Walk the Archive - the staff chat, built in code.

#include "UI/WTAChatWidget.h"
#include "Core/WTAText.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/EditableTextBox.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/ScrollBox.h"
#include "Components/ScrollBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/SlateWrapperTypes.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/WrapBox.h"
#include "Components/WrapBoxSlot.h"
#include "Core/WTAPlayerController.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "InputCoreTypes.h"
#include "Layout/Margin.h"
#include "Styling/SlateBrush.h"
#include "Systems/WTAContentSubsystem.h"
#include "Systems/WTADialogueSubsystem.h"
#include "Systems/WTAVisitLogSubsystem.h"
#include "Systems/WTAProgressSubsystem.h"
#include "UI/WTAActionButton.h"
#include "UI/WTAUIStyle.h"
#include "World/WTAStaffNPC.h"

namespace
{
	const FName NAME_ChatSend(TEXT("Send"));
	const FName NAME_ChatClose(TEXT("Close"));
	const FName NAME_ChatChip(TEXT("Chip"));
	const FName NAME_ChatOffer(TEXT("Offer"));

	/** Let the staff NPC in the world know it is speaking (jaw/gesture hook for later phases). */
	void ChatTalkAs(UWorld* World, FName StaffId, const FText& Text)
	{
		if (World == nullptr || StaffId.IsNone())
		{
			return;
		}
		for (TActorIterator<AWTAStaffNPC> It(World); It; ++It)
		{
			if (It->StaffId == StaffId)
			{
				It->Talk(Text);
			}
		}
	}
}

void UWTAChatWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	UWidgetTree* Tree = WidgetTree;
	if (Tree == nullptr)
	{
		return;
	}

	// Scrim with a transparent close button under the card.
	Scrim = WTAWidgets::MakePlate(Tree, WTAStyle::Scrim(), FMargin(0.f));
	Scrim->SetHorizontalAlignment(HAlign_Fill);
	Scrim->SetVerticalAlignment(VAlign_Fill);
	Tree->RootWidget = Scrim;

	UOverlay* Layers = Tree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
	Scrim->SetContent(Layers);
	{
		UWTAActionButton* ScrimButton = Tree->ConstructWidget<UWTAActionButton>(UWTAActionButton::StaticClass());
		const FSlateBrush Clear = WTAStyle::SolidBrush(FLinearColor::Transparent);
		FButtonStyle ClearStyle;
		ClearStyle.SetNormal(Clear);
		ClearStyle.SetHovered(Clear);
		ClearStyle.SetPressed(Clear);
		ClearStyle.SetNormalPadding(FMargin(0.f));
		ClearStyle.SetPressedPadding(FMargin(0.f));
		ScrimButton->SetStyle(ClearStyle);
		ScrimButton->Init(NAME_ChatClose, NAME_None, -1);
		ScrimButton->OnAction.AddDynamic(this, &UWTAChatWidget::HandleAction);
		UOverlaySlot* ScrimSlot = Layers->AddChildToOverlay(ScrimButton);
		ScrimSlot->SetHorizontalAlignment(HAlign_Fill);
		ScrimSlot->SetVerticalAlignment(VAlign_Fill);
	}

	// Dark green card with a brass edge.
	Card = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Card->SetBrush(WTAStyle::EdgedBrush(WTAStyle::Panel(), 12.f, WTAStyle::Brass()));
	Card->SetPadding(FMargin(0.f));
	{
		UOverlaySlot* CardSlot = Layers->AddChildToOverlay(Card);
		CardSlot->SetHorizontalAlignment(HAlign_Center);
		CardSlot->SetVerticalAlignment(VAlign_Center);
	}

	USizeBox* CardWidth = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	CardWidth->SetWidthOverride(560.f);
	Card->SetContent(CardWidth);

	UVerticalBox* Column = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	CardWidth->SetContent(Column);

	// Header: name + role, Close.
	{
		UHorizontalBox* Header = Tree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
		UVerticalBox* Who = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
		NameText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(20, true), WTAStyle::Bone(), false);
		RoleText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(12), WTAStyle::Brass(), false);
		Who->AddChildToVerticalBox(NameText);
		Who->AddChildToVerticalBox(RoleText)->SetPadding(FMargin(0.f, 2.f, 0.f, 0.f));
		UHorizontalBoxSlot* WhoSlot = Header->AddChildToHorizontalBox(Who);
		WhoSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		WhoSlot->SetVerticalAlignment(VAlign_Center);

		CloseButton = WTAWidgets::MakeButton(Tree, WTAText(TEXT("Close")), NAME_ChatClose, NAME_None, -1,
			WTAStyle::SecondaryButton(), WTAStyle::Font(13), WTAStyle::Bone());
		CloseButton->OnAction.AddDynamic(this, &UWTAChatWidget::HandleAction);
		UHorizontalBoxSlot* CloseSlot = Header->AddChildToHorizontalBox(CloseButton);
		CloseSlot->SetVerticalAlignment(VAlign_Center);

		Column->AddChildToVerticalBox(Header)->SetPadding(FMargin(24.f, 20.f, 24.f, 12.f));

		USizeBox* Rule = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		Rule->SetHeightOverride(1.f);
		Rule->SetContent(WTAWidgets::MakePlate(Tree, WTAStyle::Brass(), FMargin(0.f)));
		Column->AddChildToVerticalBox(Rule)->SetPadding(FMargin(24.f, 0.f, 24.f, 0.f));
	}

	// Messages.
	{
		// Tall enough for a question, a long answer and its offer button without scrolling.
		USizeBox* ScrollHeight = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		ScrollHeight->SetHeightOverride(420.f);
		Column->AddChildToVerticalBox(ScrollHeight);

		MessageScroll = Tree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass());
		ScrollHeight->SetContent(MessageScroll);

		MessageList = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
		if (UScrollBoxSlot* ListSlot = Cast<UScrollBoxSlot>(MessageScroll->AddChild(MessageList)))
		{
			ListSlot->SetPadding(FMargin(24.f, 14.f, 24.f, 14.f));
		}
	}

	// Suggestion chips.
	ChipBox = Tree->ConstructWidget<UWrapBox>(UWrapBox::StaticClass());
	ChipBox->SetInnerSlotPadding(FVector2D(6.f, 6.f));
	Column->AddChildToVerticalBox(ChipBox)->SetPadding(FMargin(24.f, 0.f, 24.f, 12.f));

	// Text box + Send.
	{
		UHorizontalBox* InputRow = Tree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
		InputBox = Tree->ConstructWidget<UEditableTextBox>(UEditableTextBox::StaticClass());
		InputBox->SetHintText(WTAText(TEXT("Ask a question")));
		InputBox->OnTextCommitted.AddDynamic(this, &UWTAChatWidget::HandleTextCommitted);
		UHorizontalBoxSlot* InputSlot = InputRow->AddChildToHorizontalBox(InputBox);
		InputSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		InputSlot->SetVerticalAlignment(VAlign_Center);

		SendButton = WTAWidgets::MakeButton(Tree, WTAText(TEXT("Send")), NAME_ChatSend, NAME_None, -1,
			WTAStyle::PrimaryButton(), WTAStyle::Font(13, true), WTAStyle::Ink());
		SendButton->OnAction.AddDynamic(this, &UWTAChatWidget::HandleAction);
		UHorizontalBoxSlot* SendSlot = InputRow->AddChildToHorizontalBox(SendButton);
		SendSlot->SetPadding(FMargin(8.f, 0.f, 0.f, 0.f));
		SendSlot->SetVerticalAlignment(VAlign_Center);

		Column->AddChildToVerticalBox(InputRow)->SetPadding(FMargin(24.f, 0.f, 24.f, 22.f));
	}

	bOpen = false;
	SetVisibility(ESlateVisibility::Collapsed);
}

FReply UWTAChatWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	// Typed letters belong to the text box; Escape still goes through to the controller's Back action.
	if (bOpen && InputBox != nullptr && InputBox->HasKeyboardFocus() && InKeyEvent.GetKey() != EKeys::Escape)
	{
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

void UWTAChatWidget::Open(FName InStaffId)
{
	const UWTAContentSubsystem* Data = UWTAContentSubsystem::Get(this);
	const FWTAStaffRow* Row = Data ? Data->FindStaff(InStaffId) : nullptr;
	UWTADialogueSubsystem* Dialogue = UWTADialogueSubsystem::Get(this);
	if (UWTAVisitLogSubsystem* Visits = UWTAVisitLogSubsystem::Get(this))
	{
		Visits->NoteCard(FName(TEXT("chat")), InStaffId);
	}

	// A different staff member (or an empty list) starts a fresh conversation with a greeting.
	const bool bFresh = (InStaffId != StaffId) || MessageList == nullptr || MessageList->GetChildrenCount() == 0;
	StaffId = InStaffId;

	if (NameText != nullptr)
	{
		NameText->SetText(Row ? Row->DisplayName : FText::FromName(StaffId));
	}
	if (RoleText != nullptr)
	{
		RoleText->SetText(Row ? Row->Role : FText::GetEmpty());
	}

	if (bFresh)
	{
		if (MessageList != nullptr)
		{
			MessageList->ClearChildren();
		}
		Offers.Reset();
		const bool bShort = Greeted.Contains(StaffId);
		FText Greeting;
		if (Dialogue != nullptr)
		{
			Greeting = Dialogue->GetGreeting(StaffId, bShort);
		}
		else if (Row != nullptr)
		{
			Greeting = bShort ? Row->GreetingShort : Row->Greeting;
		}
		if (!Greeting.IsEmpty())
		{
			AddMessage(Greeting, false);
			ChatTalkAs(GetWorld(), StaffId, Greeting);
		}
		Greeted.Add(StaffId);
	}

	TArray<FText> Chips;
	if (Dialogue != nullptr)
	{
		Chips = Dialogue->GetChips(StaffId);
	}
	else if (Row != nullptr)
	{
		Chips = Row->Chips;
	}
	SetChips(Chips);

	bOpen = true;
	SetVisibility(ESlateVisibility::SelfHitTestInvisible);
	if (InputBox != nullptr)
	{
		InputBox->SetText(FText::GetEmpty());
	}
	FocusInput();
}

void UWTAChatWidget::Close()
{
	bOpen = false;
	SetVisibility(ESlateVisibility::Collapsed);
}

void UWTAChatWidget::ClearConversation()
{
	if (MessageList != nullptr)
	{
		MessageList->ClearChildren();
	}
	Offers.Reset();
	PendingAction = NAME_None;
	PendingArg = NAME_None;
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(ActionTimer);
	}
}

void UWTAChatWidget::AddMessage(const FText& Text, bool bFromPlayer)
{
	if (MessageList == nullptr || WidgetTree == nullptr || Text.IsEmpty())
	{
		return;
	}

	UBorder* Bubble = WTAWidgets::MakePlate(WidgetTree,
		bFromPlayer ? WTAStyle::Brass() : WTAStyle::FromHex(0x24352f), FMargin(14.f, 9.f), 10.f);
	UTextBlock* Line = WTAWidgets::MakeText(WidgetTree, Text, WTAStyle::Font(14),
		bFromPlayer ? WTAStyle::Ink() : WTAStyle::Bone(), true);
	USizeBox* Clamp = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	Clamp->SetMaxDesiredWidth(400.f);
	Clamp->SetContent(Line);
	Bubble->SetContent(Clamp);

	UVerticalBoxSlot* BubbleSlot = MessageList->AddChildToVerticalBox(Bubble);
	BubbleSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 8.f));
	BubbleSlot->SetHorizontalAlignment(bFromPlayer ? HAlign_Right : HAlign_Left);
	RequestScrollToEnd();
}

void UWTAChatWidget::SetChips(const TArray<FText>& Chips)
{
	CurrentChips = Chips;
	if (ChipBox == nullptr || WidgetTree == nullptr)
	{
		return;
	}
	ChipBox->ClearChildren();
	for (int32 i = 0; i < CurrentChips.Num(); ++i)
	{
		if (CurrentChips[i].IsEmpty())
		{
			continue;
		}
		UWTAActionButton* Chip = WTAWidgets::MakeButton(WidgetTree, CurrentChips[i], NAME_ChatChip, NAME_None, i,
			WTAStyle::SecondaryButton(), WTAStyle::Font(12), WTAStyle::Bone());
		Chip->Payload = CurrentChips[i].ToString();
		Chip->OnAction.AddDynamic(this, &UWTAChatWidget::HandleAction);
		ChipBox->AddChildToWrapBox(Chip);
	}
}

void UWTAChatWidget::Send(const FString& Question)
{
	const FString Trimmed = Question.TrimStartAndEnd();
	if (Trimmed.IsEmpty() || StaffId.IsNone())
	{
		return;
	}

	AddMessage(FText::FromString(Trimmed), true);

	FWTAReply Reply;
	if (UWTADialogueSubsystem* Dialogue = UWTADialogueSubsystem::Get(this))
	{
		Reply = Dialogue->Ask(StaffId, Trimmed);
	}
	else
	{
		Reply.Text = WTAText(TEXT("The staff are away from their desks right now."));
	}

	if (!Reply.Text.IsEmpty())
	{
		AddMessage(Reply.Text, false);
		ChatTalkAs(GetWorld(), StaffId, Reply.Text);
	}

	if (UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this))
	{
		Progress->NoteQuestionAsked();
	}

	// An offered action waits for its button; any other runs a beat later so its panel appears after the answer.
	if (!Reply.Action.IsNone() && Reply.bOffer)
	{
		AddOffer(Reply.OfferLabel, Reply.Action, Reply.ActionArg);
	}
	else if (!Reply.Action.IsNone())
	{
		PendingAction = Reply.Action;
		PendingArg = Reply.ActionArg;
		if (UWorld* World = GetWorld())
		{
			World->GetTimerManager().SetTimer(ActionTimer, this, &UWTAChatWidget::RunPendingAction, FMath::Max(ActionDelay, 0.01f), false);
		}
	}

	if (InputBox != nullptr)
	{
		InputBox->SetText(FText::GetEmpty());
	}
}

void UWTAChatWidget::FocusInput()
{
	if (InputBox != nullptr && bOpen)
	{
		InputBox->SetKeyboardFocus();
	}
}

void UWTAChatWidget::HandleAction(FName Action, FName Arg, int32 Index)
{
	if (Action == NAME_ChatSend)
	{
		if (InputBox != nullptr)
		{
			Send(InputBox->GetText().ToString());
		}
		FocusInput();
	}
	else if (Action == NAME_ChatClose)
	{
		if (AWTAPlayerController* PC = Cast<AWTAPlayerController>(GetOwningPlayer()))
		{
			PC->CloseTopPanel();
		}
		else
		{
			Close();
		}
	}
	else if (Action == NAME_ChatChip)
	{
		if (CurrentChips.IsValidIndex(Index))
		{
			Send(CurrentChips[Index].ToString());
		}
		FocusInput();
	}
	else if (Action == NAME_ChatOffer)
	{
		ClickOffer(Index);
	}
}

bool UWTAChatWidget::ClickOffer(int32 Index)
{
	if (!Offers.IsValidIndex(Index))
	{
		return false;
	}
	PendingAction = Offers[Index].Key;
	PendingArg = Offers[Index].Value;
	RunPendingAction();
	return true;
}

void UWTAChatWidget::AddOffer(const FText& Label, FName Action, FName Arg)
{
	if (MessageList == nullptr || WidgetTree == nullptr || Action.IsNone())
	{
		return;
	}
	const int32 Index = Offers.Emplace(Action, Arg);
	UWTAActionButton* Button = WTAWidgets::MakeButton(WidgetTree, Label.IsEmpty() ? WTAText(TEXT("Show me")) : Label,
		NAME_ChatOffer, NAME_None, Index, WTAStyle::SecondaryButton(), WTAStyle::Font(12), WTAStyle::Bone());
	Button->OnAction.AddDynamic(this, &UWTAChatWidget::HandleAction);
	UVerticalBoxSlot* ButtonSlot = MessageList->AddChildToVerticalBox(Button);
	ButtonSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 8.f));
	ButtonSlot->SetHorizontalAlignment(HAlign_Left);
	RequestScrollToEnd();
}

void UWTAChatWidget::RequestScrollToEnd()
{
	if (MessageScroll != nullptr)
	{
		MessageScroll->ScrollToEnd();
	}
	// A new bubble has no size until Slate's next layout pass, so scroll again over the next few frames.
	ScrollToEndFrames = 3;
}

void UWTAChatWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	if (ScrollToEndFrames > 0)
	{
		--ScrollToEndFrames;
		if (MessageScroll != nullptr)
		{
			MessageScroll->ScrollToEnd();
		}
	}
}

void UWTAChatWidget::HandleTextCommitted(const FText& Text, ETextCommit::Type CommitMethod)
{
	if (CommitMethod == ETextCommit::OnEnter)
	{
		Send(Text.ToString());
		FocusInput();
	}
	else if (CommitMethod == ETextCommit::OnCleared && bOpen)
	{
		// Escape in the text box: close like the Esc key would.
		if (AWTAPlayerController* PC = Cast<AWTAPlayerController>(GetOwningPlayer()))
		{
			PC->CloseTopPanel();
		}
	}
}

void UWTAChatWidget::RunPendingAction()
{
	const FName Action = PendingAction;
	const FName Arg = PendingArg;
	PendingAction = NAME_None;
	PendingArg = NAME_None;
	if (Action.IsNone())
	{
		return;
	}
	if (AWTAPlayerController* PC = Cast<AWTAPlayerController>(GetOwningPlayer()))
	{
		PC->RunAction(Action, Arg);
	}
}
