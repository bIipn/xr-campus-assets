// Walk the Archive - the always-on HUD, built in code.

#include "UI/WTAHudWidget.h"
#include "Blueprint/WidgetLayoutLibrary.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/PanelSlot.h"
#include "Components/SizeBox.h"
#include "Components/SlateWrapperTypes.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Widgets/Layout/Anchors.h"
#include "Layout/Margin.h"
#include "Styling/SlateBrush.h"
#include "Systems/WTATourSubsystem.h"
#include "UI/WTAActionButton.h"
#include "UI/WTAUIStyle.h"

namespace
{
	const FName NAME_HudTourBack(TEXT("TourBack"));
	const FName NAME_HudTourNext(TEXT("TourNext"));
	const FName NAME_HudTourEnd(TEXT("TourEnd"));
	const FName NAME_HudTourOpen(TEXT("TourOpen"));

	/** Put a widget on the canvas, auto-sized, at an anchor/alignment/position. */
	UCanvasPanelSlot* HudPlace(UCanvasPanel* Canvas, UWidget* Widget, const FAnchors& Anchors, const FVector2D& Alignment, const FVector2D& Position)
	{
		UCanvasPanelSlot* Slot = Canvas->AddChildToCanvas(Widget);
		Slot->SetAnchors(Anchors);
		Slot->SetAlignment(Alignment);
		Slot->SetPosition(Position);
		Slot->SetAutoSize(true);
		return Slot;
	}

	/** A text block inside a size box so long lines wrap at MaxWidth. */
	USizeBox* HudClampWidth(UWidgetTree* Tree, UWidget* Inner, float MaxWidth)
	{
		USizeBox* Box = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		Box->SetMaxDesiredWidth(MaxWidth);
		Box->SetContent(Inner);
		return Box;
	}

	/** Set a text block's text and collapse it when the text is empty. */
	void HudSetOptional(UTextBlock* Block, const FText& Text)
	{
		if (Block == nullptr)
		{
			return;
		}
		Block->SetText(Text);
		Block->SetVisibility(Text.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
	}
}

void UWTAHudWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	UWidgetTree* Tree = WidgetTree;
	if (Tree == nullptr)
	{
		return;
	}

	Canvas = Tree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass());
	Canvas->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
	Tree->RootWidget = Canvas;

	// --- Room label, top-left ---------------------------------------------------
	RoomPlate = WTAWidgets::MakePlate(Tree, WTAStyle::Plate(), FMargin(16.f, 12.f), 8.f);
	RoomPlate->SetVisibility(ESlateVisibility::Collapsed);
	{
		UVerticalBox* Box = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
		RoomKickerText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(11, true), WTAStyle::Brass(), false);
		RoomNameText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(21, true), WTAStyle::Bone(), false);
		RoomSubText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(12), WTAStyle::BoneDim(), false);
		Box->AddChildToVerticalBox(RoomKickerText)->SetPadding(FMargin(0.f, 0.f, 0.f, 2.f));
		Box->AddChildToVerticalBox(RoomNameText)->SetPadding(FMargin(0.f, 0.f, 0.f, 2.f));
		Box->AddChildToVerticalBox(RoomSubText);
		RoomPlate->SetContent(Box);
	}
	HudPlace(Canvas, RoomPlate, FAnchors(0.f, 0.f), FVector2D(0.f, 0.f), FVector2D(24.f, 24.f));

	// --- Badge counter, top-right ------------------------------------------------
	BadgePlate = WTAWidgets::MakePlate(Tree, WTAStyle::Plate(), FMargin(14.f, 8.f), 8.f);
	BadgePlate->SetVisibility(ESlateVisibility::HitTestInvisible);
	BadgeText = WTAWidgets::MakeText(Tree, FText::FromString(TEXT("Badges 0 / 0")), WTAStyle::Font(12, true), WTAStyle::Brass(), false);
	BadgePlate->SetContent(BadgeText);
	HudPlace(Canvas, BadgePlate, FAnchors(1.f, 0.f), FVector2D(1.f, 0.f), FVector2D(-24.f, 24.f));

	// --- Crosshair and hover label, centre -------------------------------------------
	CrosshairDot = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
	CrosshairDot->SetBrush(WTAStyle::EdgedBrush(WTAStyle::Bone(), 3.f, WTAStyle::Ink(), 1.f));
	CrosshairDot->SetPadding(FMargin(0.f));
	CrosshairDot->SetVisibility(ESlateVisibility::HitTestInvisible);
	{
		UCanvasPanelSlot* DotSlot = Canvas->AddChildToCanvas(CrosshairDot);
		DotSlot->SetAnchors(FAnchors(0.5f, 0.5f));
		DotSlot->SetAlignment(FVector2D(0.5f, 0.5f));
		DotSlot->SetPosition(FVector2D(0.f, 0.f));
		DotSlot->SetAutoSize(false);
		DotSlot->SetSize(FVector2D(6.f, 6.f));
	}

	// The label sits on a small dark plate with a thin dim-brass edge (the web's .tag), so it reads on white walls,
	// pale book covers and white hair alike.
	HoverPlate = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
	{
		FLinearColor Fill = WTAStyle::Panel();
		Fill.A = 0.92f;
		HoverPlate->SetBrush(WTAStyle::EdgedBrush(Fill, 6.f, WTAStyle::BrassDim(), 1.f));
	}
	HoverPlate->SetPadding(FMargin(10.f, 5.f, 10.f, 6.f));
	HoverPlate->SetVisibility(ESlateVisibility::Collapsed);
	HoverLabelText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(13, true), WTAStyle::Bone(), false);
	HoverPlate->SetContent(HoverLabelText);
	HudPlace(Canvas, HoverPlate, FAnchors(0.5f, 0.5f), FVector2D(0.5f, 0.f), FVector2D(0.f, 22.f));

	// --- Toast, top-centre ----------------------------------------------------------
	ToastPlate = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
	ToastPlate->SetBrush(WTAStyle::EdgedBrush(WTAStyle::Plate(), 8.f, WTAStyle::Brass()));
	ToastPlate->SetPadding(FMargin(18.f, 10.f));
	ToastPlate->SetVisibility(ESlateVisibility::Collapsed);
	// Fixed wrap widths (not auto-wrap): an auto-sized canvas slot gives auto-wrapped text no width to wrap at,
	// which squeezed these plates down to a word or two per line.
	ToastText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(15), WTAStyle::Bone(), false);
	ToastText->SetWrapTextAt(720.f);
	ToastText->SetJustification(ETextJustify::Center);
	ToastPlate->SetContent(HudClampWidth(Tree, ToastText, 720.f));
	HudPlace(Canvas, ToastPlate, FAnchors(0.5f, 0.f), FVector2D(0.5f, 0.f), FVector2D(0.f, 28.f));

	// --- Caption, lower-centre (wax scenes) -------------------------------------------
	CaptionPlate = WTAWidgets::MakePlate(Tree, FLinearColor(0.f, 0.f, 0.f, 0.72f), FMargin(20.f, 12.f), 6.f);
	CaptionPlate->SetVisibility(ESlateVisibility::Collapsed);
	CaptionText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(19), WTAStyle::Bone(), false);
	CaptionText->SetWrapTextAt(860.f);
	CaptionText->SetJustification(ETextJustify::Center);
	CaptionPlate->SetContent(HudClampWidth(Tree, CaptionText, 860.f));
	HudPlace(Canvas, CaptionPlate, FAnchors(0.5f, 1.f), FVector2D(0.5f, 1.f), FVector2D(0.f, -250.f));

	// --- Hint, bottom-left --------------------------------------------------------------
	HintPlate = WTAWidgets::MakePlate(Tree, WTAStyle::Plate(), FMargin(14.f, 10.f), 8.f);
	HintPlate->SetVisibility(ESlateVisibility::Collapsed);
	HintText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(14), WTAStyle::Bone(), false);
	HintText->SetWrapTextAt(460.f);
	HintPlate->SetContent(HudClampWidth(Tree, HintText, 460.f));
	HudPlace(Canvas, HintPlate, FAnchors(0.f, 1.f), FVector2D(0.f, 1.f), FVector2D(24.f, -24.f));

	// --- Story plaque, right side: the museum label that appears when you walk up to an exhibit or scene ---
	StoryPlate = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
	{
		// Nearly solid, like a printed museum label: a see-through plate let the busy stage behind it show through.
		FLinearColor Fill = WTAStyle::Panel();
		Fill.A = 0.95f;
		StoryPlate->SetBrush(WTAStyle::EdgedBrush(Fill, 10.f, WTAStyle::Brass()));
	}
	StoryPlate->SetPadding(FMargin(26.f, 22.f, 26.f, 20.f));
	StoryPlate->SetVisibility(ESlateVisibility::Collapsed);
	{
		USizeBox* Width = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		Width->SetWidthOverride(470.f);
		StoryPlate->SetContent(Width);

		UVerticalBox* Column = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
		Width->SetContent(Column);

		StoryKickerText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Kicker(11), WTAStyle::Brass(), true);
		StoryYearText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(34, true), WTAStyle::Brass(), true);
		StoryTitleText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(24, true), WTAStyle::Bone(), true);
		StorySummaryText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(16), WTAStyle::Bone(), true);
		StorySummaryText->SetLineHeightPercentage(1.25f);
		StoryHintText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(14, true), WTAStyle::Brass(), true);

		Column->AddChildToVerticalBox(StoryKickerText)->SetPadding(FMargin(0.f, 0.f, 0.f, 6.f));
		Column->AddChildToVerticalBox(StoryYearText);
		Column->AddChildToVerticalBox(StoryTitleText)->SetPadding(FMargin(0.f, 0.f, 0.f, 10.f));
		Column->AddChildToVerticalBox(StorySummaryText)->SetPadding(FMargin(0.f, 0.f, 0.f, 14.f));

		USizeBox* Rule = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		Rule->SetHeightOverride(1.f);
		FLinearColor RuleColor = WTAStyle::Brass();
		RuleColor.A = 0.5f;
		Rule->SetContent(WTAWidgets::MakePlate(Tree, RuleColor, FMargin(0.f)));
		Column->AddChildToVerticalBox(Rule)->SetPadding(FMargin(0.f, 0.f, 0.f, 10.f));
		Column->AddChildToVerticalBox(StoryHintText);
	}
	HudPlace(Canvas, StoryPlate, FAnchors(1.f, 0.5f), FVector2D(1.f, 0.5f), FVector2D(-32.f, -40.f));

	// --- Tour bar, bottom-centre ------------------------------------------------------------
	TourPlate = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
	TourPlate->SetBrush(WTAStyle::EdgedBrush(WTAStyle::Panel(), 10.f, WTAStyle::Brass()));
	TourPlate->SetPadding(FMargin(22.f, 16.f, 22.f, 18.f));
	TourPlate->SetVisibility(ESlateVisibility::Collapsed);
	{
		USizeBox* Width = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		Width->SetWidthOverride(680.f);
		TourPlate->SetContent(Width);

		UVerticalBox* Column = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
		Width->SetContent(Column);

		TourStepText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(11, true), WTAStyle::Brass(), false);
		TourTitleText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(20, true), WTAStyle::Bone(), true);
		TourDateText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(12), WTAStyle::BoneDim(), false);
		TourBodyText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(14), WTAStyle::Bone(), true);
		Column->AddChildToVerticalBox(TourStepText)->SetPadding(FMargin(0.f, 0.f, 0.f, 4.f));
		Column->AddChildToVerticalBox(TourTitleText)->SetPadding(FMargin(0.f, 0.f, 0.f, 2.f));
		Column->AddChildToVerticalBox(TourDateText)->SetPadding(FMargin(0.f, 0.f, 0.f, 8.f));
		Column->AddChildToVerticalBox(TourBodyText)->SetPadding(FMargin(0.f, 0.f, 0.f, 14.f));

		UHorizontalBox* Buttons = Tree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
		Column->AddChildToVerticalBox(Buttons);

		TourBackButton = WTAWidgets::MakeButton(Tree, FText::FromString(TEXT("Back")), NAME_HudTourBack, NAME_None, -1,
			WTAStyle::SecondaryButton(), WTAStyle::Font(13), WTAStyle::Bone());
		TourBackButton->OnAction.AddDynamic(this, &UWTAHudWidget::HandleAction);
		Buttons->AddChildToHorizontalBox(TourBackButton)->SetPadding(FMargin(0.f, 0.f, 8.f, 0.f));

		TourNextButton = Tree->ConstructWidget<UWTAActionButton>(UWTAActionButton::StaticClass());
		TourNextButton->SetStyle(WTAStyle::PrimaryButton());
		TourNextButton->Init(NAME_HudTourNext, NAME_None, -1);
		TourNextButton->OnAction.AddDynamic(this, &UWTAHudWidget::HandleAction);
		TourNextText = WTAWidgets::MakeText(Tree, FText::FromString(TEXT("Next (T)")), WTAStyle::Font(13, true), WTAStyle::Ink(), false);
		TourNextButton->AddChild(TourNextText);
		Buttons->AddChildToHorizontalBox(TourNextButton)->SetPadding(FMargin(0.f, 0.f, 8.f, 0.f));

		TourOpenButton = Tree->ConstructWidget<UWTAActionButton>(UWTAActionButton::StaticClass());
		TourOpenButton->SetStyle(WTAStyle::SecondaryButton());
		TourOpenButton->Init(NAME_HudTourOpen, NAME_None, -1);
		TourOpenButton->OnAction.AddDynamic(this, &UWTAHudWidget::HandleAction);
		TourOpenText = WTAWidgets::MakeText(Tree, FText::FromString(TEXT("Open")), WTAStyle::Font(13), WTAStyle::Brass(), false);
		TourOpenButton->AddChild(TourOpenText);
		TourOpenButton->SetVisibility(ESlateVisibility::Collapsed);
		Buttons->AddChildToHorizontalBox(TourOpenButton)->SetPadding(FMargin(0.f, 0.f, 8.f, 0.f));

		USpacer* Gap = Tree->ConstructWidget<USpacer>(USpacer::StaticClass());
		UHorizontalBoxSlot* GapSlot = Buttons->AddChildToHorizontalBox(Gap);
		GapSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

		TourEndButton = WTAWidgets::MakeButton(Tree, FText::FromString(TEXT("End tour")), NAME_HudTourEnd, NAME_None, -1,
			WTAStyle::SecondaryButton(), WTAStyle::Font(13), WTAStyle::BoneDim());
		TourEndButton->OnAction.AddDynamic(this, &UWTAHudWidget::HandleAction);
		Buttons->AddChildToHorizontalBox(TourEndButton);
	}
	HudPlace(Canvas, TourPlate, FAnchors(0.5f, 1.f), FVector2D(0.5f, 1.f), FVector2D(0.f, -24.f));
}

void UWTAHudWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	AdvanceToasts(InDeltaTime);

	// The story plaque fades in over a fifth of a second instead of popping.
	if (bStoryShowing && bStoryVisible && StoryPlate != nullptr && StoryFade < 1.f)
	{
		StoryFade = FMath::Min(1.f, StoryFade + InDeltaTime * 5.f);
		StoryPlate->SetRenderOpacity(StoryFade);
	}

	if (HintTimeLeft > 0.f)
	{
		HintTimeLeft -= InDeltaTime;
		if (HintTimeLeft <= 0.f)
		{
			HideHint();
		}
	}

	// With the crosshair hidden (free cursor) the hover label follows the mouse instead.
	if (HoverPlate != nullptr && CrosshairDot != nullptr && HoverPlate->GetVisibility() != ESlateVisibility::Collapsed)
	{
		if (UCanvasPanelSlot* LabelSlot = Cast<UCanvasPanelSlot>(HoverPlate->Slot))
		{
			if (CrosshairDot->GetVisibility() == ESlateVisibility::Collapsed)
			{
				const FVector2D Mouse = UWidgetLayoutLibrary::GetMousePositionOnViewport(this);
				LabelSlot->SetAnchors(FAnchors(0.f, 0.f));
				LabelSlot->SetAlignment(FVector2D(0.f, 0.f));
				LabelSlot->SetPosition(Mouse + FVector2D(16.f, 18.f));
			}
			else
			{
				LabelSlot->SetAnchors(FAnchors(0.5f, 0.5f));
				LabelSlot->SetAlignment(FVector2D(0.5f, 0.f));
				LabelSlot->SetPosition(FVector2D(0.f, 22.f));
			}
		}
	}
}

void UWTAHudWidget::SetRoom(const FText& Kicker, const FText& Name, const FText& Sub)
{
	if (RoomPlate == nullptr)
	{
		return;
	}
	if (Name.IsEmpty() && Kicker.IsEmpty())
	{
		RoomPlate->SetVisibility(ESlateVisibility::Collapsed);
		return;
	}
	RoomKickerText->SetText(FText::FromString(Kicker.ToString().ToUpper()));
	RoomKickerText->SetVisibility(Kicker.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
	RoomNameText->SetText(Name);
	RoomNameText->SetVisibility(Name.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
	RoomSubText->SetText(Sub);
	RoomSubText->SetVisibility(Sub.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
	RoomPlate->SetVisibility(ESlateVisibility::HitTestInvisible);
}

void UWTAHudWidget::SetHoverLabel(const FText& Label)
{
	if (HoverLabelText == nullptr || HoverPlate == nullptr)
	{
		return;
	}
	HoverLabelText->SetText(Label);
	HoverPlate->SetVisibility(Label.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
}

void UWTAHudWidget::ShowToast(const FText& Text, float Seconds)
{
	if (Text.IsEmpty())
	{
		return;
	}
	FWTAToastEntry Entry;
	Entry.Text = Text;
	Entry.Seconds = Seconds > 0.f ? Seconds : WTAStyle::ToastSeconds;
	ToastQueue.Add(Entry);

	if (ToastTimeLeft <= 0.f)
	{
		AdvanceToasts(0.f);
	}
}

void UWTAHudWidget::AdvanceToasts(float DeltaSeconds)
{
	if (ToastTimeLeft > 0.f)
	{
		ToastTimeLeft -= DeltaSeconds;
		if (ToastTimeLeft > 0.f)
		{
			return;
		}
	}

	if (ToastPlate == nullptr || ToastText == nullptr)
	{
		return;
	}

	if (ToastQueue.Num() > 0)
	{
		const FWTAToastEntry Next = ToastQueue[0];
		ToastQueue.RemoveAt(0);
		ToastText->SetText(Next.Text);
		ToastPlate->SetVisibility(ESlateVisibility::HitTestInvisible);
		ToastTimeLeft = Next.Seconds;
	}
	else if (ToastPlate->GetVisibility() != ESlateVisibility::Collapsed)
	{
		ToastPlate->SetVisibility(ESlateVisibility::Collapsed);
		ToastTimeLeft = 0.f;
	}
}

void UWTAHudWidget::ShowCaption(const FText& Text)
{
	if (CaptionPlate == nullptr || CaptionText == nullptr)
	{
		return;
	}
	CaptionText->SetText(Text);
	CaptionPlate->SetVisibility(Text.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
}

void UWTAHudWidget::ShowHint(const FText& Text, float Seconds)
{
	if (HintPlate == nullptr || HintText == nullptr || Text.IsEmpty())
	{
		return;
	}
	HintText->SetText(Text);
	HintPlate->SetVisibility(ESlateVisibility::HitTestInvisible);
	HintTimeLeft = Seconds > 0.f ? Seconds : 6.f;
}

void UWTAHudWidget::HideHint()
{
	HintTimeLeft = 0.f;
	if (HintPlate != nullptr)
	{
		HintPlate->SetVisibility(ESlateVisibility::Collapsed);
	}
}

void UWTAHudWidget::ShowTour(int32 Index, int32 Total, const FText& Title, const FText& DateLabel, const FText& Body, const FText& OpenLabel)
{
	if (TourPlate == nullptr)
	{
		return;
	}

	TourStepText->SetText(FText::Format(FText::FromString(TEXT("STOP {0} OF {1}")), FText::AsNumber(Index + 1), FText::AsNumber(Total)));
	TourTitleText->SetText(Title);
	TourDateText->SetText(DateLabel);
	TourDateText->SetVisibility(DateLabel.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
	TourBodyText->SetText(Body);
	TourBodyText->SetVisibility(Body.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);

	TourBackButton->SetIsEnabled(Index > 0);
	TourNextText->SetText(FText::FromString(Index >= Total - 1 ? TEXT("Explore on your own") : TEXT("Next (T)")));

	if (OpenLabel.IsEmpty())
	{
		TourOpenButton->SetVisibility(ESlateVisibility::Collapsed);
	}
	else
	{
		TourOpenText->SetText(OpenLabel);
		TourOpenButton->SetVisibility(ESlateVisibility::Visible);
	}

	bTourShowing = true;
	TourPlate->SetVisibility(ESlateVisibility::Visible);
}

void UWTAHudWidget::HideTour()
{
	bTourShowing = false;
	if (TourPlate != nullptr)
	{
		TourPlate->SetVisibility(ESlateVisibility::Collapsed);
	}
}

void UWTAHudWidget::SetTourVisible(bool bVisible)
{
	if (TourPlate == nullptr || !bTourShowing)
	{
		return;
	}
	TourPlate->SetVisibility(bVisible ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
}

void UWTAHudWidget::SetBadgeCount(int32 Count, int32 Total)
{
	if (BadgeText != nullptr)
	{
		BadgeText->SetText(FText::Format(FText::FromString(TEXT("Badges {0} / {1}")), FText::AsNumber(Count), FText::AsNumber(Total)));
	}
}

void UWTAHudWidget::SetCrosshairVisible(bool bVisible)
{
	if (CrosshairDot != nullptr)
	{
		CrosshairDot->SetVisibility(bVisible ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	}
}

void UWTAHudWidget::ShowStory(const FText& Kicker, const FText& Year, const FText& Title, const FText& Summary, const FText& Hint)
{
	if (StoryPlate == nullptr)
	{
		return;
	}
	// Re-showing the same story (e.g. looking away and back) keeps it on screen without a new fade.
	const bool bSameStory = bStoryShowing && StoryTitleText != nullptr && StoryTitleText->GetText().EqualTo(Title);

	HudSetOptional(StoryKickerText, FText::FromString(Kicker.ToString().ToUpper()));
	HudSetOptional(StoryYearText, Year);
	HudSetOptional(StoryTitleText, Title);
	HudSetOptional(StorySummaryText, Summary);
	HudSetOptional(StoryHintText, Hint);

	bStoryShowing = true;
	if (!bSameStory)
	{
		StoryFade = 0.f;
		StoryPlate->SetRenderOpacity(0.f);
	}
	StoryPlate->SetVisibility(bStoryVisible ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
}

void UWTAHudWidget::HideStory()
{
	bStoryShowing = false;
	if (StoryPlate != nullptr)
	{
		StoryPlate->SetVisibility(ESlateVisibility::Collapsed);
	}
}

void UWTAHudWidget::SetStoryVisible(bool bVisible)
{
	bStoryVisible = bVisible;
	if (StoryPlate != nullptr)
	{
		StoryPlate->SetVisibility(bStoryShowing && bStoryVisible ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	}
}

void UWTAHudWidget::HandleAction(FName Action, FName Arg, int32 Index)
{
	UWTATourSubsystem* Tour = UWTATourSubsystem::Get(this);
	if (Tour == nullptr)
	{
		return;
	}

	if (Action == NAME_HudTourBack)
	{
		Tour->Back();
	}
	else if (Action == NAME_HudTourNext)
	{
		Tour->Next();
	}
	else if (Action == NAME_HudTourEnd)
	{
		Tour->End();
	}
	else if (Action == NAME_HudTourOpen)
	{
		Tour->OpenCurrent();
	}
}
