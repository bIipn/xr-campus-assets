// Walk the Archive - the Lost Stories wall's face.

#include "UI/WTAStoryBoardWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/SizeBox.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/UniformGridPanel.h"
#include "Components/UniformGridSlot.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Core/WTAText.h"
#include "UI/WTAUIStyle.h"

namespace
{
	constexpr int32 BoardColumns = 4;
	constexpr int32 BoardRows = 2;
	constexpr float BoardCardW = 452.f;
	constexpr float BoardCardH = 380.f;

	/** A few words of the story: up to MaxChars, cut at a word, with an ellipsis when cut. */
	FString BoardExcerpt(const FString& Text, int32 MaxChars)
	{
		FString T = Text.TrimStartAndEnd();
		if (T.Len() <= MaxChars)
		{
			return T;
		}
		const int32 Space = T.Left(MaxChars).Find(TEXT(" "), ESearchCase::CaseSensitive, ESearchDir::FromEnd);
		return T.Left(Space > MaxChars / 2 ? Space : MaxChars).TrimEnd() + TEXT("…");
	}

	UVerticalBoxSlot* BoardAddLine(UVerticalBox* Box, UWidget* Widget, float Bottom)
	{
		UVerticalBoxSlot* Slot = Box->AddChildToVerticalBox(Widget);
		Slot->SetPadding(FMargin(0.f, 0.f, 0.f, Bottom));
		return Slot;
	}
}

void UWTAStoryBoardWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	UWidgetTree* Tree = WidgetTree;
	if (Tree == nullptr)
	{
		return;
	}
	// Transparent round the cards, so the board's own fabric and frame show between them.
	UBorder* Root = WTAWidgets::MakePlate(Tree, FLinearColor::Transparent, FMargin(48.f, 30.f, 48.f, 30.f));
	Tree->RootWidget = Root;
	UVerticalBox* Column = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Root->SetContent(Column);

	Heading = WTAWidgets::MakeText(Tree, WTAUpper(WTAText(TEXT("Stories from this place"))), WTAStyle::Kicker(40), WTAStyle::Brass(), false);
	Heading->SetJustification(ETextJustify::Center);
	BoardAddLine(Column, Heading, 4.f)->SetHorizontalAlignment(HAlign_Center);
	SubHeading = WTAWidgets::MakeText(Tree, WTAText(TEXT("Told at the microphone here, in the tellers' own voices")), WTAStyle::SerifItalic(32), WTAStyle::Bone(), false);
	SubHeading->SetJustification(ETextJustify::Center);
	BoardAddLine(Column, SubHeading, 22.f)->SetHorizontalAlignment(HAlign_Center);

	Grid = Tree->ConstructWidget<UUniformGridPanel>(UUniformGridPanel::StaticClass());
	Grid->SetSlotPadding(FMargin(14.f));
	Grid->SetMinDesiredSlotWidth(BoardCardW);
	Grid->SetMinDesiredSlotHeight(BoardCardH);
	UVerticalBoxSlot* GridSlot = Column->AddChildToVerticalBox(Grid);
	GridSlot->SetHorizontalAlignment(HAlign_Center);
	GridSlot->SetVerticalAlignment(VAlign_Top);
	GridSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
}

UWidget* UWTAStoryBoardWidget::MakeCard(const FWTAStory& Story, bool bPlaying, bool bWriting)
{
	UWidgetTree* Tree = WidgetTree;
	USizeBox* Size = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	Size->SetWidthOverride(BoardCardW);
	Size->SetHeightOverride(BoardCardH);
	UBorder* Paper = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Paper->SetBrush(Story.bThisVisit ? WTAStyle::EdgedBrush(WTAStyle::Card(), 10.f, WTAStyle::Brass(), 5.f) : WTAStyle::RoundedBrush(WTAStyle::Card(), 10.f));
	Paper->SetPadding(FMargin(30.f, 26.f, 30.f, 24.f));
	Paper->SetClipping(EWidgetClipping::ClipToBounds);         // a long story never spills onto the felt
	Size->SetContent(Paper);
	UVerticalBox* Box = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Paper->SetContent(Box);

	const FText Byline = Story.bThisVisit
		? FText::Format(WTAText(TEXT("New · {0}")), Story.Byline())
		: Story.Byline();
	BoardAddLine(Box, WTAWidgets::MakeText(Tree, WTAUpper(Byline), WTAStyle::Kicker(15), WTAStyle::BrassDark(), true), 10.f);

	UTextBlock* Title = WTAWidgets::MakeText(Tree, Story.DisplayTitle(), WTAStyle::Serif(34, true), WTAStyle::CardInk(), true);
	Title->SetLineHeightPercentage(0.95f);
	BoardAddLine(Box, Title, 10.f);

	FText Words;
	if (!Story.Transcript.IsEmpty() && !Story.Title.IsEmpty())
	{
		Words = FText::Format(WTAText(TEXT("“{0}”")), FText::FromString(BoardExcerpt(Story.Transcript, 90)));
	}
	else if (!Story.Transcript.IsEmpty())
	{
		// The title is already its first words: the next ones.
		const FString Rest = Story.Transcript.Mid(FMath::Min(Story.Transcript.Len(), Story.DisplayTitle().ToString().Len()));
		Words = Rest.TrimStartAndEnd().Len() > 12 ? FText::Format(WTAText(TEXT("“…{0}”")), FText::FromString(BoardExcerpt(Rest, 90))) : FText::GetEmpty();
	}
	else if (bWriting)
	{
		Words = WTAText(TEXT("Being written down now; the words will be here in a minute or two."));
	}
	if (!Words.IsEmpty())
	{
		UTextBlock* Quote = WTAWidgets::MakeText(Tree, Words, WTAStyle::SerifItalic(24), WTAStyle::CardInkDim(), true);
		Quote->SetLineHeightPercentage(1.05f);
		BoardAddLine(Box, Quote, 0.f);
	}

	USpacer* Gap = Tree->ConstructWidget<USpacer>(USpacer::StaticClass());
	Box->AddChildToVerticalBox(Gap)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

	const FText Foot = bPlaying ? WTAText(TEXT("Playing now · E to stop")) : WTAText(TEXT("E to listen"));
	BoardAddLine(Box, WTAWidgets::MakeText(Tree, WTAUpper(Foot), WTAStyle::Kicker(16), bPlaying ? WTAStyle::FromHex(0x2f6b3a) : WTAStyle::BrassDark(), false), 0.f);
	return Size;
}

UWidget* UWTAStoryBoardWidget::MakeNoteCard(const FText& Title, const FText& Body)
{
	UWidgetTree* Tree = WidgetTree;
	USizeBox* Size = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	Size->SetWidthOverride(BoardCardW);
	Size->SetHeightOverride(BoardCardH);
	UBorder* Paper = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Paper->SetBrush(WTAStyle::EdgedBrush(WTAStyle::FromHex(0xe6dcc4), 10.f, WTAStyle::BrassDim(), 3.f));
	Paper->SetPadding(FMargin(30.f, 30.f));
	Size->SetContent(Paper);
	UVerticalBox* Box = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Paper->SetContent(Box);
	BoardAddLine(Box, WTAWidgets::MakeText(Tree, Title, WTAStyle::Serif(40, true), WTAStyle::CardInk(), true), 14.f);
	UTextBlock* Text = WTAWidgets::MakeText(Tree, Body, WTAStyle::SerifItalic(28), WTAStyle::CardInkDim(), true);
	Text->SetLineHeightPercentage(1.1f);
	BoardAddLine(Box, Text, 0.f);
	return Size;
}

void UWTAStoryBoardWidget::ShowStories(const TArray<FWTAStory>& Stories, const FString& PlayingId, const TSet<FString>& Writing)
{
	Cards = 0;
	if (Grid == nullptr)
	{
		return;
	}
	Grid->ClearChildren();
	if (Stories.Num() == 0)
	{
		UUniformGridSlot* EmptySlot = Grid->AddChildToUniformGrid(MakeNoteCard(WTAText(TEXT("No stories yet")),
			WTAText(TEXT("Sit at the microphone and tell the first one: a place here you remember, someone who mattered, something nobody wrote down."))), 0, 0);
		EmptySlot->SetHorizontalAlignment(HAlign_Fill);
		return;
	}
	const int32 Slots = BoardColumns * BoardRows;
	const bool bMore = Stories.Num() > Slots;
	const int32 Shown = bMore ? Slots - 1 : Stories.Num();
	for (int32 i = 0; i < Shown; ++i)
	{
		const FWTAStory& Story = Stories[i];
		Grid->AddChildToUniformGrid(MakeCard(Story, Story.Id == PlayingId, Writing.Contains(Story.Id)), i / BoardColumns, i % BoardColumns);
		++Cards;
	}
	if (bMore)
	{
		Grid->AddChildToUniformGrid(MakeNoteCard(FText::Format(WTAText(TEXT("And {0} more")), FText::AsNumber(Stories.Num() - Shown)),
			WTAText(TEXT("Press E at the wall for every story, newest first."))), BoardRows - 1, BoardColumns - 1);
	}
}
