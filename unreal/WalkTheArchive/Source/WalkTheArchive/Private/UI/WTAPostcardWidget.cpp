// Walk the Archive - the postcard frame (photo mode).

#include "UI/WTAPostcardWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "UI/WTAUIStyle.h"

namespace
{
	constexpr float RuleWidth = 2.f;

	/** A solid strip in the canvas: Anchors + Offsets as UMG takes them (position and size on an unstretched axis, margins on a stretched one). */
	UBorder* Strip(UWidgetTree* Tree, UCanvasPanel* Canvas, const FLinearColor& Fill, const FAnchors& Anchors, const FMargin& Offsets)
	{
		UBorder* Plate = WTAWidgets::MakePlate(Tree, Fill, FMargin(0.f));
		Plate->SetVisibility(ESlateVisibility::HitTestInvisible);
		UCanvasPanelSlot* Slot = Canvas->AddChildToCanvas(Plate);
		Slot->SetAnchors(Anchors);
		Slot->SetAlignment(FVector2D(0.f, 0.f));
		Slot->SetOffsets(Offsets);
		return Plate;
	}

	FText Upper(const FString& Text)
	{
		return FText::FromString(Text.ToUpper());
	}
}

void UWTAPostcardWidget::Build()
{
	UWidgetTree* Tree = WidgetTree;
	if (Tree == nullptr || Tree->RootWidget != nullptr)
	{
		return;
	}
	const float F = MatWidth;
	const float B = BandHeight;
	const FLinearColor Mat = WTAStyle::Card();
	const FLinearColor Rule = WTAStyle::BrassDark();

	UCanvasPanel* Canvas = Tree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass());
	Canvas->SetVisibility(ESlateVisibility::HitTestInvisible);
	Tree->RootWidget = Canvas;

	// The mat: three strips and the caption band along the bottom.
	Strip(Tree, Canvas, Mat, FAnchors(0.f, 0.f, 1.f, 0.f), FMargin(0.f, 0.f, 0.f, F));            // top
	Strip(Tree, Canvas, Mat, FAnchors(0.f, 0.f, 0.f, 1.f), FMargin(0.f, 0.f, F, 0.f));            // left
	Strip(Tree, Canvas, Mat, FAnchors(1.f, 0.f, 1.f, 1.f), FMargin(-F, 0.f, F, 0.f));             // right
	UBorder* Band = Strip(Tree, Canvas, Mat, FAnchors(0.f, 1.f, 1.f, 1.f), FMargin(0.f, -B, 0.f, B));   // bottom band

	// A brass hairline just inside the mat, the way a print is matted.
	Strip(Tree, Canvas, Rule, FAnchors(0.f, 0.f, 1.f, 0.f), FMargin(F, F, F, RuleWidth));
	Strip(Tree, Canvas, Rule, FAnchors(0.f, 0.f, 0.f, 1.f), FMargin(F, F, RuleWidth, B));
	Strip(Tree, Canvas, Rule, FAnchors(1.f, 0.f, 1.f, 1.f), FMargin(-F - RuleWidth, F, RuleWidth, B));
	Strip(Tree, Canvas, Rule, FAnchors(0.f, 1.f, 1.f, 1.f), FMargin(F, -B - RuleWidth, F, RuleWidth));

	// The caption: campus and client small on the left over the place in the serif; the date on the right.
	UHorizontalBox* Caption = Tree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	Band->SetPadding(FMargin(F + 12.f, 16.f, F + 12.f, 14.f));
	Band->SetContent(Caption);

	UVerticalBox* Left = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	UHorizontalBoxSlot* LeftSlot = Caption->AddChildToHorizontalBox(Left);
	LeftSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	LeftSlot->SetVerticalAlignment(VAlign_Center);
	CampusText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Kicker(12), WTAStyle::BrassDark(), false);
	Left->AddChildToVerticalBox(CampusText)->SetPadding(FMargin(0.f, 0.f, 0.f, 6.f));
	PlaceText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Serif(34, true), WTAStyle::CardInk(), false);
	Left->AddChildToVerticalBox(PlaceText);

	UVerticalBox* Right = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	UHorizontalBoxSlot* RightSlot = Caption->AddChildToHorizontalBox(Right);
	RightSlot->SetSize(FSlateChildSize(ESlateSizeRule::Automatic));
	RightSlot->SetVerticalAlignment(VAlign_Center);
	KickerText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Kicker(12), WTAStyle::BrassDark(), false);
	KickerText->SetJustification(ETextJustify::Right);
	Right->AddChildToVerticalBox(KickerText)->SetPadding(FMargin(0.f, 0.f, 0.f, 6.f));
	DateText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::SerifItalic(22), WTAStyle::CardInkDim(), false);
	DateText->SetJustification(ETextJustify::Right);
	Right->AddChildToVerticalBox(DateText);

	SetVisibility(ESlateVisibility::Collapsed);
}

void UWTAPostcardWidget::Show(const FText& Place, const FText& Kicker, const FString& Date, const FString& Client, const FString& Campus)
{
	Build();
	if (CampusText != nullptr)
	{
		const FString Line = Client.IsEmpty() || Client == Campus ? Campus : FString::Printf(TEXT("%s  ·  %s"), *Campus, *Client);
		CampusText->SetText(Upper(Line));
	}
	if (PlaceText != nullptr)
	{
		PlaceText->SetText(Place.IsEmpty() ? FText::FromString(Campus) : Place);
	}
	if (KickerText != nullptr)
	{
		KickerText->SetText(Upper(Kicker.ToString()));
		KickerText->SetVisibility(Kicker.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
	}
	if (DateText != nullptr)
	{
		DateText->SetText(FText::FromString(Date));
	}
	bShowing = true;
	SetVisibility(ESlateVisibility::HitTestInvisible);
}

void UWTAPostcardWidget::Hide()
{
	bShowing = false;
	SetVisibility(ESlateVisibility::Collapsed);
}
