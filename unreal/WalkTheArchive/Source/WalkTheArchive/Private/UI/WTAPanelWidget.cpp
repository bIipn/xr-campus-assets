// Walk the Archive - the one modal panel: catalog card, book reader, station, ride, badges, places.

#include "UI/WTAPanelWidget.h"
#include "Blueprint/WidgetLayoutLibrary.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Image.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/PanelWidget.h"
#include "Components/ScrollBox.h"
#include "Components/ScrollBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/SlateWrapperTypes.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/WrapBox.h"
#include "Components/WrapBoxSlot.h"
#include "Core/WTAPlayerController.h"
#include "Engine/Texture2D.h"
#include "HAL/PlatformProcess.h"
#include "InputCoreTypes.h"
#include "Layout/Margin.h"
#include "Styling/SlateBrush.h"
#include "Systems/WTAContentSubsystem.h"
#include "Systems/WTAProgressSubsystem.h"
#include "UI/WTAActionButton.h"
#include "UI/WTAUIStyle.h"
#if WITH_EDITOR
#include "TextureCompiler.h"
#endif

namespace
{
	const FName NAME_PanelPrev(TEXT("Prev"));
	const FName NAME_PanelNext(TEXT("Next"));
	const FName NAME_PanelClose(TEXT("Close"));
	const FName NAME_PanelPage(TEXT("Page"));
	const FName NAME_PanelLink(TEXT("Link"));
	const FName NAME_PanelReset(TEXT("Reset"));

	const FName NAME_PanelBlockPara(TEXT("Para"));
	const FName NAME_PanelBlockList(TEXT("List"));
	const FName NAME_PanelBlockQuote(TEXT("Quote"));
	const FName NAME_PanelBlockNote(TEXT("Note"));
	const FName NAME_PanelBlockCode(TEXT("Code"));

	FText PanelUpper(const FText& Text)
	{
		return FText::FromString(Text.ToString().ToUpper());
	}

	FText PanelText(const TCHAR* Text)
	{
		return FText::FromString(Text);
	}

	/** Append a row to the content column. */
	UVerticalBoxSlot* PanelAddRow(UVerticalBox* Column, UWidget* Widget, const FMargin& Padding, EHorizontalAlignment HAlign = HAlign_Fill)
	{
		UVerticalBoxSlot* Slot = Column->AddChildToVerticalBox(Widget);
		Slot->SetPadding(Padding);
		Slot->SetHorizontalAlignment(HAlign);
		return Slot;
	}

	/** Card width per mode: wide reading cards for exhibits and books, compact for the rest. */
	float PanelCardWidth(EWTAPanelMode InMode)
	{
		switch (InMode)
		{
		case EWTAPanelMode::Exhibit: return 900.f;
		case EWTAPanelMode::Book:    return 880.f;
		default:                     return 780.f;
		}
	}

	/** Brass at partial opacity, for hairlines. */
	FLinearColor PanelHairline()
	{
		FLinearColor Color = WTAStyle::Brass();
		Color.A = 0.45f;
		return Color;
	}
}

void UWTAPanelWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	UWidgetTree* Tree = WidgetTree;
	if (Tree == nullptr)
	{
		return;
	}

	SetIsFocusable(true);

	// Scrim over the whole screen; a transparent button under the card closes on a click outside it.
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
		ScrimButton->Init(NAME_PanelClose, NAME_None, -1);
		ScrimButton->OnAction.AddDynamic(this, &UWTAPanelWidget::HandleAction);
		UOverlaySlot* ScrimSlot = Layers->AddChildToOverlay(ScrimButton);
		ScrimSlot->SetHorizontalAlignment(HAlign_Fill);
		ScrimSlot->SetVerticalAlignment(VAlign_Fill);
	}

	// The cream card.
	Card = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Card->SetBrush(WTAStyle::EdgedBrush(WTAStyle::Card(), 12.f, WTAStyle::Brass()));
	Card->SetPadding(FMargin(0.f));
	{
		UOverlaySlot* CardSlot = Layers->AddChildToOverlay(Card);
		CardSlot->SetHorizontalAlignment(HAlign_Center);
		CardSlot->SetVerticalAlignment(VAlign_Center);
		CardSlot->SetPadding(FMargin(0.f, 24.f));
	}

	CardSize = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	CardSize->SetWidthOverride(PanelCardWidth(EWTAPanelMode::None));
	Card->SetContent(CardSize);

	UVerticalBox* Column = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	CardSize->SetContent(Column);

	// Header, laid out like a museum label: kicker, big year, title, italic place line, then a brass rule.
	{
		UVerticalBox* Header = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
		KickerText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Kicker(12), WTAStyle::BrassDark(), true);
		YearText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(40, true), WTAStyle::BrassDark(), true);
		YearText->SetVisibility(ESlateVisibility::Collapsed);
		TitleText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(30, true), WTAStyle::CardInk(), true);
		TitleText->SetLineHeightPercentage(1.05f);
		SubtitleText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Italic(17), WTAStyle::CardInkDim(), true);
		SubtitleText->SetVisibility(ESlateVisibility::Collapsed);
		Header->AddChildToVerticalBox(KickerText)->SetPadding(FMargin(0.f, 0.f, 0.f, 8.f));
		Header->AddChildToVerticalBox(YearText);
		Header->AddChildToVerticalBox(TitleText);
		Header->AddChildToVerticalBox(SubtitleText)->SetPadding(FMargin(0.f, 6.f, 0.f, 0.f));
		Column->AddChildToVerticalBox(Header)->SetPadding(FMargin(40.f, 30.f, 40.f, 18.f));

		USizeBox* Rule = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		Rule->SetHeightOverride(2.f);
		Rule->SetContent(WTAWidgets::MakePlate(Tree, WTAStyle::Brass(), FMargin(0.f)));
		Column->AddChildToVerticalBox(Rule)->SetPadding(FMargin(40.f, 0.f, 40.f, 0.f));
	}

	// Scrolling content, height clamped in SetOpen from the viewport size.
	{
		USizeBox* ScrollHeight = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		ScrollHeight->SetMaxDesiredHeight(560.f);
		Column->AddChildToVerticalBox(ScrollHeight);

		Scroll = Tree->ConstructWidget<UScrollBox>(UScrollBox::StaticClass());
		ScrollHeight->SetContent(Scroll);

		Content = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
		if (UScrollBoxSlot* ContentSlot = Cast<UScrollBoxSlot>(Scroll->AddChild(Content)))
		{
			ContentSlot->SetPadding(FMargin(40.f, 22.f, 40.f, 22.f));
		}
	}

	// Footer: Prev, page label, Next, Close.
	{
		Footer = Tree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
		Column->AddChildToVerticalBox(Footer)->SetPadding(FMargin(40.f, 12.f, 40.f, 28.f));

		PrevButton = WTAWidgets::MakeButton(Tree, PanelText(TEXT("Previous")), NAME_PanelPrev, NAME_None, -1,
			WTAStyle::CardButton(), WTAStyle::Font(15, true), WTAStyle::CardInk());
		PrevButton->OnAction.AddDynamic(this, &UWTAPanelWidget::HandleAction);
		UHorizontalBoxSlot* PrevSlot = Footer->AddChildToHorizontalBox(PrevButton);
		PrevSlot->SetVerticalAlignment(VAlign_Center);

		PageText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(15), WTAStyle::CardInkDim(), false);
		PageText->SetJustification(ETextJustify::Center);
		UHorizontalBoxSlot* PageSlot = Footer->AddChildToHorizontalBox(PageText);
		PageSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		PageSlot->SetHorizontalAlignment(HAlign_Center);
		PageSlot->SetVerticalAlignment(VAlign_Center);
		PageSlot->SetPadding(FMargin(12.f, 0.f));

		NextButton = WTAWidgets::MakeButton(Tree, PanelText(TEXT("Next")), NAME_PanelNext, NAME_None, -1,
			WTAStyle::CardButton(), WTAStyle::Font(15, true), WTAStyle::CardInk());
		NextButton->OnAction.AddDynamic(this, &UWTAPanelWidget::HandleAction);
		UHorizontalBoxSlot* NextSlot = Footer->AddChildToHorizontalBox(NextButton);
		NextSlot->SetVerticalAlignment(VAlign_Center);
		NextSlot->SetPadding(FMargin(0.f, 0.f, 12.f, 0.f));

		CloseButton = WTAWidgets::MakeButton(Tree, PanelText(TEXT("Close")), NAME_PanelClose, NAME_None, -1,
			WTAStyle::PrimaryButton(), WTAStyle::Font(15, true), WTAStyle::Ink());
		CloseButton->OnAction.AddDynamic(this, &UWTAPanelWidget::HandleAction);
		UHorizontalBoxSlot* CloseSlot = Footer->AddChildToHorizontalBox(CloseButton);
		CloseSlot->SetVerticalAlignment(VAlign_Center);
	}

	bOpen = false;
	SetVisibility(ESlateVisibility::Collapsed);
}

FReply UWTAPanelWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	const FKey Key = InKeyEvent.GetKey();
	if (Key == EKeys::Left)
	{
		HandleAction(NAME_PanelPrev, NAME_None, -1);
		return FReply::Handled();
	}
	if (Key == EKeys::Right)
	{
		HandleAction(NAME_PanelNext, NAME_None, -1);
		return FReply::Handled();
	}
	if (Key == EKeys::Escape)
	{
		HandleAction(NAME_PanelClose, NAME_None, -1);
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

// ---------------------------------------------------------------------------
// Show*
// ---------------------------------------------------------------------------

void UWTAPanelWidget::ShowExhibit(FName ItemId)
{
	const UWTAContentSubsystem* Data = UWTAContentSubsystem::Get(this);
	const FWTAExhibitRow* Row = Data ? Data->FindExhibit(ItemId) : nullptr;
	CurrentPage = -1;
	NumPages = 0;

	if (Row == nullptr)
	{
		BeginCard(EWTAPanelMode::Exhibit, ItemId, PanelText(TEXT("Museum")), FText::FromName(ItemId));
		AddParagraph(PanelText(TEXT("This exhibit is not in the catalog yet.")));
		EndCard(false, false, FText::GetEmpty());
		return;
	}

	// Kicker: "Milestone - Gallery 1 of 3 - Headsets in Libraries", or the Wax Hall line for scene cards.
	FText Kicker = Row->Kind;
	if (Row->bWax)
	{
		if (!Row->Hall.IsEmpty())
		{
			Kicker = FText::Format(PanelText(TEXT("{0} \u00B7 {1}")), Row->Kind, Row->Hall);
		}
	}
	else
	{
		for (const FName& GalleryId : Data->GetRowNames(EWTATable::Galleries))
		{
			const FWTAGalleryRow* Gallery = Data->FindGallery(GalleryId);
			if (Gallery != nullptr && Gallery->Index == Row->Gallery)
			{
				Kicker = FText::Format(PanelText(TEXT("{0} \u00B7 {1} \u00B7 {2}")), Row->Kind, Gallery->Label, Gallery->DisplayName);
				break;
			}
		}
	}

	// Museum-label header: kicker, big year, title, and the place in italics under it.
	BeginCard(EWTAPanelMode::Exhibit, ItemId, Kicker, Row->Title);
	SetHeaderExtras(Row->Date, Row->Where);
	AddImage(Row->Art, 820.f);

	// A wax scene first says what the figures are acting out, then tells the story behind it.
	if (Row->bWax)
	{
		const FWTAWaxSceneRow* Scene = Data->FindWaxScene(Row->WaxSceneId.IsNone() ? ItemId : Row->WaxSceneId);
		if (Scene != nullptr && Scene->Lines.Num() > 0)
		{
			AddSection(PanelText(TEXT("In this scene")));
			AddSceneLines(Scene->Lines);
		}
	}
	if (!Row->Description.IsEmpty() || !Row->More.IsEmpty())
	{
		AddSection(PanelText(TEXT("The story")));
		AddParagraph(Row->Description);
		AddParagraph(Row->More);
	}
	AddQuote(Row->Quote, Row->QuoteBy);
	if (!Row->Where.IsEmpty() || !Row->Partners.IsEmpty())
	{
		AddSection(PanelText(TEXT("At a glance")));
		AddFact(PanelText(TEXT("When")), Row->Date);
		AddFact(PanelText(TEXT("Where")), Row->Where);
		AddFact(PanelText(TEXT("Partners")), Row->Partners);
	}
	if (Row->Sources.Num() > 0)
	{
		// Arg = the DT_Sources row; HandleAction looks the URL up again.
		AddSection(PanelText(TEXT("Sources")));
		AddSourceChips(Row->Sources);
	}

	// Position in the list for the footer and Prev/Next.
	const TArray<FName> List = Row->bWax ? Data->GetWaxExhibitIds() : Data->GetGalleryExhibitIds();
	const int32 Pos = List.IndexOfByKey(ItemId);
	FText PageLabel;
	if (Pos != INDEX_NONE)
	{
		PageLabel = FText::Format(PanelText(TEXT("{0} of {1}")), FText::AsNumber(Pos + 1), FText::AsNumber(List.Num()));
	}
	EndCard(List.Num() > 1, List.Num() > 1, PageLabel);
}

void UWTAPanelWidget::ShowBook(FName BookId, int32 Page)
{
	const UWTAContentSubsystem* Data = UWTAContentSubsystem::Get(this);
	const FWTABookRow* Row = Data ? Data->FindBook(BookId) : nullptr;

	if (Row == nullptr)
	{
		CurrentPage = -1;
		NumPages = 0;
		BeginCard(EWTAPanelMode::Book, BookId, PanelText(TEXT("Library")), FText::FromName(BookId));
		AddParagraph(PanelText(TEXT("This book is not on the shelf yet.")));
		EndCard(false, false, FText::GetEmpty());
		return;
	}

	NumPages = Row->Pages.Num();
	CurrentPage = FMath::Clamp(Page, -1, NumPages - 1);

	FText SubjectName = PanelText(TEXT("Library"));
	if (const FWTASubjectRow* Subject = Data->FindSubject(Row->Subject))
	{
		SubjectName = Subject->DisplayName;
	}

	if (CurrentPage < 0)
	{
		// Cover: subtitle, contents, Start reading.
		BeginCard(EWTAPanelMode::Book, BookId, FText::Format(PanelText(TEXT("Library \u00B7 {0}")), SubjectName), Row->Title);
		AddImage(Row->Cover, 320.f);
		if (!Row->Subtitle.IsEmpty())
		{
			AddText(Row->Subtitle, WTAStyle::Italic(17), WTAStyle::CardInk());
		}
		AddHeading(PanelText(TEXT("Contents")));
		for (int32 i = 0; i < NumPages; ++i)
		{
			const FText Label = FText::Format(PanelText(TEXT("{0}. {1}")), FText::AsNumber(i + 1), Row->Pages[i].Heading);
			AddButton(Label, NAME_PanelPage, NAME_None, i, false);
		}
		AddSpacer(10.f);
		if (NumPages > 0)
		{
			AddButton(PanelText(TEXT("Start reading")), NAME_PanelPage, NAME_None, 0, true);
		}
		EndCard(false, NumPages > 0, PanelText(TEXT("Cover")));
		return;
	}

	const FWTABookPage& BookPage = Row->Pages[CurrentPage];
	BeginCard(EWTAPanelMode::Book, BookId, FText::Format(PanelText(TEXT("{0} \u00B7 {1}")), SubjectName, Row->Title), BookPage.Heading);
	for (const FWTABookBlock& Block : BookPage.Blocks)
	{
		AddBlock(Block);
	}
	AddSpacer(10.f);
	AddButton(PanelText(TEXT("Contents")), NAME_PanelPage, NAME_None, -1, false);
	EndCard(true, true, FText::Format(PanelText(TEXT("Page {0} of {1}")), FText::AsNumber(CurrentPage + 1), FText::AsNumber(NumPages)));
	if (CurrentPage == NumPages - 1)
	{
		WTAWidgets::SetButtonLabel(NextButton, PanelText(TEXT("Close book")));
	}
}

void UWTAPanelWidget::ShowStation(FName StationId)
{
	const UWTAContentSubsystem* Data = UWTAContentSubsystem::Get(this);
	const FWTAStationRow* Row = Data ? Data->FindStation(StationId) : nullptr;
	CurrentPage = -1;
	NumPages = 0;

	if (Row == nullptr)
	{
		BeginCard(EWTAPanelMode::Station, StationId, PanelText(TEXT("Workshop School")), FText::FromName(StationId));
		AddParagraph(PanelText(TEXT("This station is not set up yet.")));
		EndCard(false, false, FText::GetEmpty());
		return;
	}

	BeginCard(EWTAPanelMode::Station, StationId, Row->Kicker, Row->Title);
	if (!Row->Subtitle.IsEmpty())
	{
		AddText(Row->Subtitle, WTAStyle::Italic(17), WTAStyle::CardInk());
	}
	if (Row->Steps.Num() > 0)
	{
		AddHeading(PanelText(TEXT("Steps")));
		for (int32 i = 0; i < Row->Steps.Num(); ++i)
		{
			AddText(FText::Format(PanelText(TEXT("{0}. {1}")), FText::AsNumber(i + 1), Row->Steps[i]), WTAStyle::Font(15), WTAStyle::CardInk());
		}
	}
	if (Row->Panel.Num() > 0)
	{
		AddHeading(PanelText(TEXT("About this station")));
		for (const FText& Paragraph : Row->Panel)
		{
			AddParagraph(Paragraph);
		}
	}
	AddNote(PanelText(TEXT("The hands-on version of this station is coming in a later build.")));
	EndCard(false, false, FText::GetEmpty());
}

void UWTAPanelWidget::ShowRide(FName RideId)
{
	const UWTAContentSubsystem* Data = UWTAContentSubsystem::Get(this);
	const FWTARideRow* Row = Data ? Data->FindRide(RideId) : nullptr;
	CurrentPage = -1;
	NumPages = 0;

	if (Row == nullptr)
	{
		BeginCard(EWTAPanelMode::Ride, RideId, PanelText(TEXT("Recess Yard")), FText::FromName(RideId));
		AddParagraph(PanelText(TEXT("This ride is not built yet.")));
		EndCard(false, false, FText::GetEmpty());
		return;
	}

	BeginCard(EWTAPanelMode::Ride, RideId, Row->Kicker, Row->DisplayName);
	AddParagraph(Row->CardText);
	if (!Row->Stats.IsEmpty())
	{
		AddParagraph(Row->Stats);
	}
	AddNote(Row->CardNote);
	AddNote(PanelText(TEXT("Riding comes in a later build. For now the sign tells you what it does.")));
	EndCard(false, false, FText::GetEmpty());
}

void UWTAPanelWidget::ShowBadges()
{
	const UWTAContentSubsystem* Data = UWTAContentSubsystem::Get(this);
	UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this);

	// CurrentPage doubles as the "Start over" confirmation state here (1 = asked to confirm).
	const bool bConfirmReset = (Mode == EWTAPanelMode::Badges && CurrentPage == 1);
	BeginCard(EWTAPanelMode::Badges, NAME_None, PanelText(TEXT("Progress")), PanelText(TEXT("Badges")));
	CurrentPage = bConfirmReset ? 1 : 0;
	NumPages = 0;

	int32 Unlocked = 0;
	int32 Total = 0;
	if (Data != nullptr)
	{
		for (const FName& BadgeId : Data->GetRowNames(EWTATable::Badges))
		{
			const FWTABadgeRow* Badge = Data->FindBadge(BadgeId);
			if (Badge == nullptr)
			{
				continue;
			}
			++Total;
			const bool bHas = Progress != nullptr && Progress->HasBadge(BadgeId);
			if (bHas)
			{
				++Unlocked;
			}

			UVerticalBox* Line = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
			UTextBlock* Name = WTAWidgets::MakeText(WidgetTree, Badge->DisplayName, WTAStyle::Font(15, true),
				bHas ? WTAStyle::BrassDark() : WTAStyle::CardInk(), true);
			UTextBlock* How = WTAWidgets::MakeText(WidgetTree,
				bHas ? PanelText(TEXT("Unlocked")) : Badge->How, WTAStyle::Font(13), WTAStyle::CardInkDim(), true);
			Line->AddChildToVerticalBox(Name);
			Line->AddChildToVerticalBox(How);
			PanelAddRow(Content, Line, FMargin(0.f, 0.f, 0.f, 10.f));
		}

		AddHeading(PanelText(TEXT("XR tokens")));
		const int32 Found = Progress ? Progress->NumTokens() : 0;
		const int32 TokenTotal = Progress ? Progress->TotalTokens() : Data->GetRowNames(EWTATable::Tokens).Num();
		AddText(FText::Format(PanelText(TEXT("{0} of {1} found. Each one is hidden somewhere on the campus.")),
			FText::AsNumber(Found), FText::AsNumber(TokenTotal)), WTAStyle::Font(14), WTAStyle::CardInkDim());
		for (const FName& TokenId : Data->GetRowNames(EWTATable::Tokens))
		{
			const FWTATokenRow* Token = Data->FindToken(TokenId);
			if (Token == nullptr)
			{
				continue;
			}
			const bool bHas = Progress != nullptr && Progress->HasToken(TokenId);
			const FText Line = FText::Format(PanelText(TEXT("{0} \u00B7 {1}")), Token->Place, bHas ? PanelText(TEXT("Found")) : Token->Hint);
			AddText(Line, WTAStyle::Font(14), bHas ? WTAStyle::BrassDark() : WTAStyle::CardInk());
		}
	}

	AddSpacer(14.f);
	if (bConfirmReset)
	{
		AddText(PanelText(TEXT("Clear every badge, token and page read on this computer?")), WTAStyle::Font(14, true), WTAStyle::CardInk());
		AddButton(PanelText(TEXT("Yes, start over")), NAME_PanelReset, NAME_None, 1, true);
		AddButton(PanelText(TEXT("Keep my progress")), NAME_PanelReset, NAME_None, 2, false);
	}
	else
	{
		AddButton(PanelText(TEXT("Start over")), NAME_PanelReset, NAME_None, 0, false);
	}

	EndCard(false, false, FText::Format(PanelText(TEXT("{0} / {1}")), FText::AsNumber(Unlocked), FText::AsNumber(Total)));
}

void UWTAPanelWidget::ShowPlaces()
{
	const UWTAContentSubsystem* Data = UWTAContentSubsystem::Get(this);
	CurrentPage = -1;
	NumPages = 0;

	BeginCard(EWTAPanelMode::Places, NAME_None, PanelText(TEXT("Map")), PanelText(TEXT("Places")));
	AddText(PanelText(TEXT("Pick a place and the campus walks you there.")), WTAStyle::Font(14), WTAStyle::CardInkDim());

	UWrapBox* Wrap = WidgetTree->ConstructWidget<UWrapBox>(UWrapBox::StaticClass());
	Wrap->SetInnerSlotPadding(FVector2D(8.f, 8.f));
	if (Data != nullptr)
	{
		for (const FName& PlaceId : Data->GetRowNames(EWTATable::Places))
		{
			const FWTAPlaceRow* PlaceRow = Data->FindPlace(PlaceId);
			if (PlaceRow == nullptr)
			{
				continue;
			}
			UWTAActionButton* Button = WTAWidgets::MakeButton(WidgetTree, PlaceRow->Label, WTAAction::GoPlace(), PlaceId, -1,
				WTAStyle::CardButton(), WTAStyle::Font(13), WTAStyle::CardInk());
			Button->OnAction.AddDynamic(this, &UWTAPanelWidget::HandleAction);
			Wrap->AddChildToWrapBox(Button);
		}
	}
	PanelAddRow(Content, Wrap, FMargin(0.f, 6.f, 0.f, 6.f));

	EndCard(false, false, FText::GetEmpty());
}

void UWTAPanelWidget::Close()
{
	SetOpen(false);
	Mode = EWTAPanelMode::None;
	CurrentId = NAME_None;
	CurrentPage = -1;
	NumPages = 0;
}

// ---------------------------------------------------------------------------
// Buttons
// ---------------------------------------------------------------------------

void UWTAPanelWidget::HandleAction(FName Action, FName Arg, int32 Index)
{
	AWTAPlayerController* PC = Cast<AWTAPlayerController>(GetOwningPlayer());

	if (Action == NAME_PanelClose)
	{
		if (PC != nullptr)
		{
			PC->CloseTopPanel();
		}
		else
		{
			Close();
		}
		return;
	}

	if (Action == NAME_PanelPrev)
	{
		if (PC == nullptr)
		{
			return;
		}
		if (Mode == EWTAPanelMode::Exhibit)
		{
			PC->StepExhibit(-1);
		}
		else if (Mode == EWTAPanelMode::Book && CurrentPage >= 0)
		{
			PC->OpenBook(CurrentId, CurrentPage - 1);
		}
		return;
	}

	if (Action == NAME_PanelNext)
	{
		if (PC == nullptr)
		{
			return;
		}
		if (Mode == EWTAPanelMode::Exhibit)
		{
			PC->StepExhibit(1);
		}
		else if (Mode == EWTAPanelMode::Book)
		{
			if (CurrentPage >= NumPages - 1)
			{
				PC->CloseTopPanel();
			}
			else
			{
				PC->OpenBook(CurrentId, CurrentPage + 1);
			}
		}
		return;
	}

	if (Action == NAME_PanelPage)
	{
		if (PC != nullptr && Mode == EWTAPanelMode::Book)
		{
			PC->OpenBook(CurrentId, Index);
		}
		return;
	}

	if (Action == NAME_PanelLink)
	{
		FString Url;
		if (const UWTAContentSubsystem* Data = UWTAContentSubsystem::Get(this))
		{
			if (const FWTASourceRow* Source = Data->FindSource(Arg))
			{
				Url = Source->Url;
			}
		}
		if (Url.IsEmpty())
		{
			Url = Arg.ToString();
		}
		if (Url.StartsWith(TEXT("http")))
		{
			FPlatformProcess::LaunchURL(*Url, nullptr, nullptr);
		}
		return;
	}

	if (Action == NAME_PanelReset)
	{
		if (Index == 0)
		{
			CurrentPage = 1;
			ShowBadges();
		}
		else if (Index == 1)
		{
			if (UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this))
			{
				Progress->ResetProgress();
			}
			CurrentPage = 0;
			ShowBadges();
			if (PC != nullptr)
			{
				PC->ShowToast(PanelText(TEXT("Progress cleared. The tokens are back in their hiding places.")));
			}
		}
		else
		{
			CurrentPage = 0;
			ShowBadges();
		}
		return;
	}

	// Anything else is a shared action (GoPlace from the places list, OpenItem from a book ...).
	if (PC != nullptr)
	{
		if (Mode == EWTAPanelMode::Places)
		{
			PC->CloseTopPanel();
		}
		PC->RunAction(Action, Arg);
	}
}

// ---------------------------------------------------------------------------
// Builders
// ---------------------------------------------------------------------------

void UWTAPanelWidget::BeginCard(EWTAPanelMode NewMode, FName Id, const FText& Kicker, const FText& Title)
{
	Mode = NewMode;
	CurrentId = Id;

	if (KickerText != nullptr)
	{
		KickerText->SetText(PanelUpper(Kicker));
		KickerText->SetVisibility(Kicker.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
	}
	if (TitleText != nullptr)
	{
		TitleText->SetText(Title);
	}
	SetHeaderExtras(FText::GetEmpty(), FText::GetEmpty());
	if (CardSize != nullptr)
	{
		CardSize->SetWidthOverride(PanelCardWidth(NewMode));
	}
	if (Content != nullptr)
	{
		Content->ClearChildren();
	}
	if (Scroll != nullptr)
	{
		Scroll->ScrollToStart();
	}
	WTAWidgets::SetButtonLabel(PrevButton, PanelText(TEXT("Previous")));
	WTAWidgets::SetButtonLabel(NextButton, PanelText(TEXT("Next")));
}

void UWTAPanelWidget::EndCard(bool bShowPrev, bool bShowNext, const FText& PageLabel)
{
	if (PrevButton != nullptr)
	{
		PrevButton->SetVisibility(bShowPrev ? ESlateVisibility::Visible : ESlateVisibility::Hidden);
	}
	if (NextButton != nullptr)
	{
		NextButton->SetVisibility(bShowNext ? ESlateVisibility::Visible : ESlateVisibility::Hidden);
	}
	if (PageText != nullptr)
	{
		PageText->SetText(PageLabel);
	}
	SetOpen(true);
}

UTextBlock* UWTAPanelWidget::AddText(const FText& Text, const FSlateFontInfo& Font, const FLinearColor& Color)
{
	if (Content == nullptr || Text.IsEmpty())
	{
		return nullptr;
	}
	UTextBlock* Block = WTAWidgets::MakeText(WidgetTree, Text, Font, Color, true);
	PanelAddRow(Content, Block, FMargin(0.f, 0.f, 0.f, 8.f));
	return Block;
}

void UWTAPanelWidget::AddHeading(const FText& Text)
{
	if (Content == nullptr || Text.IsEmpty())
	{
		return;
	}
	UTextBlock* Block = WTAWidgets::MakeText(WidgetTree, Text, WTAStyle::Font(21, true), WTAStyle::CardInk(), true);
	PanelAddRow(Content, Block, FMargin(0.f, 12.f, 0.f, 8.f));
}

void UWTAPanelWidget::AddParagraph(const FText& Text)
{
	if (Text.IsEmpty())
	{
		return;
	}
	// Reading size: 18 pt with open leading and a paragraph gap, so long histories stay easy on the eyes.
	if (UTextBlock* Block = AddText(Text, WTAStyle::Font(18), WTAStyle::CardInk()))
	{
		Block->SetLineHeightPercentage(1.3f);
		if (UVerticalBoxSlot* ParagraphSlot = Cast<UVerticalBoxSlot>(Block->Slot))
		{
			ParagraphSlot->SetPadding(FMargin(0.f, 0.f, 0.f, 14.f));
		}
	}
}

void UWTAPanelWidget::AddQuote(const FText& Quote, const FText& By)
{
	if (Content == nullptr || Quote.IsEmpty())
	{
		return;
	}
	UBorder* Plate = WTAWidgets::MakePlate(WidgetTree, WTAStyle::FromHex(0xe6dcc4), FMargin(22.f, 16.f), 8.f);
	UVerticalBox* Box = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	UTextBlock* QuoteText = WTAWidgets::MakeText(WidgetTree,
		FText::Format(PanelText(TEXT("\u201C{0}\u201D")), Quote), WTAStyle::Italic(19), WTAStyle::CardInk(), true);
	QuoteText->SetLineHeightPercentage(1.25f);
	Box->AddChildToVerticalBox(QuoteText);
	if (!By.IsEmpty())
	{
		UTextBlock* ByText = WTAWidgets::MakeText(WidgetTree,
			FText::Format(PanelText(TEXT("\u2014 {0}")), By), WTAStyle::Font(15), WTAStyle::CardInkDim(), true);
		Box->AddChildToVerticalBox(ByText)->SetPadding(FMargin(0.f, 6.f, 0.f, 0.f));
	}
	Plate->SetContent(Box);
	PanelAddRow(Content, Plate, FMargin(0.f, 4.f, 0.f, 12.f));
}

void UWTAPanelWidget::AddNote(const FText& Text)
{
	if (Content == nullptr || Text.IsEmpty())
	{
		return;
	}
	UBorder* Plate = WTAWidgets::MakePlate(WidgetTree, WTAStyle::FromHex(0xe4d8c0), FMargin(18.f, 12.f), 8.f);
	Plate->SetContent(WTAWidgets::MakeText(WidgetTree, Text, WTAStyle::Font(16), WTAStyle::CardInk(), true));
	PanelAddRow(Content, Plate, FMargin(0.f, 2.f, 0.f, 10.f));
}

void UWTAPanelWidget::AddCode(const FText& Text)
{
	if (Content == nullptr || Text.IsEmpty())
	{
		return;
	}
	UBorder* Plate = WTAWidgets::MakePlate(WidgetTree, WTAStyle::Ink(), FMargin(16.f, 12.f), 6.f);
	Plate->SetContent(WTAWidgets::MakeText(WidgetTree, Text, WTAStyle::Mono(13), WTAStyle::Bone(), true));
	PanelAddRow(Content, Plate, FMargin(0.f, 2.f, 0.f, 10.f));
}

void UWTAPanelWidget::AddList(const TArray<FText>& Items)
{
	if (Content == nullptr || Items.Num() == 0)
	{
		return;
	}
	UVerticalBox* Box = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	for (const FText& Item : Items)
	{
		UHorizontalBox* Line = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
		UTextBlock* Bullet = WTAWidgets::MakeText(WidgetTree, PanelText(TEXT("\u2022")), WTAStyle::Font(15), WTAStyle::BrassDark(), false);
		UHorizontalBoxSlot* BulletSlot = Line->AddChildToHorizontalBox(Bullet);
		BulletSlot->SetPadding(FMargin(4.f, 0.f, 10.f, 0.f));
		BulletSlot->SetVerticalAlignment(VAlign_Top);
		UTextBlock* ItemText = WTAWidgets::MakeText(WidgetTree, Item, WTAStyle::Font(17), WTAStyle::CardInk(), true);
		ItemText->SetLineHeightPercentage(1.2f);
		UHorizontalBoxSlot* ItemSlot = Line->AddChildToHorizontalBox(ItemText);
		ItemSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		Box->AddChildToVerticalBox(Line)->SetPadding(FMargin(0.f, 0.f, 0.f, 4.f));
	}
	PanelAddRow(Content, Box, FMargin(0.f, 0.f, 0.f, 8.f));
}

void UWTAPanelWidget::AddBlock(const FWTABookBlock& Block)
{
	if (Block.Type == NAME_PanelBlockList)
	{
		AddList(Block.Items);
	}
	else if (Block.Type == NAME_PanelBlockQuote)
	{
		AddQuote(Block.Text, FText::GetEmpty());
	}
	else if (Block.Type == NAME_PanelBlockNote)
	{
		AddNote(Block.Text);
	}
	else if (Block.Type == NAME_PanelBlockCode)
	{
		AddCode(Block.Text);
	}
	else
	{
		// Para and anything unknown.
		AddParagraph(Block.Text);
		if (Block.Type != NAME_PanelBlockPara && Block.Items.Num() > 0)
		{
			AddList(Block.Items);
		}
	}
}

void UWTAPanelWidget::AddSpacer(float Height)
{
	if (Content == nullptr)
	{
		return;
	}
	USpacer* Spacer = WidgetTree->ConstructWidget<USpacer>(USpacer::StaticClass());
	Spacer->SetSize(FVector2D(1.f, Height));
	PanelAddRow(Content, Spacer, FMargin(0.f));
}

void UWTAPanelWidget::AddImage(const TSoftObjectPtr<UTexture2D>& Texture, float MaxWidth)
{
	if (Content == nullptr || Texture.IsNull())
	{
		return;
	}
	UTexture2D* Loaded = Texture.LoadSynchronous();
	if (Loaded == nullptr)
	{
		return;
	}
#if WITH_EDITOR
	// Run from the editor binary (play.ps1, PIE), a texture that was just loaded can still be compiling and report
	// its 32 x 32 placeholder size, which would leave the art at thumbnail size on the first open. Finish it first.
	if (Loaded->IsCompiling())
	{
		UTexture* const ToFinish[] = { Loaded };
		FTextureCompilingManager::Get().FinishCompilation(MakeArrayView(ToFinish));
	}
#endif
	const float Width = static_cast<float>(Loaded->GetSizeX());
	const float Height = static_cast<float>(Loaded->GetSizeY());
	if (Width <= 0.f || Height <= 0.f)
	{
		return;
	}
	const float Scale = FMath::Min(1.f, MaxWidth / Width);

	FSlateBrush Brush;
	Brush.SetResourceObject(Loaded);
	Brush.ImageSize = FVector2D(Width * Scale, Height * Scale);
	Brush.DrawAs = ESlateBrushDrawType::Image;

	UImage* Image = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass());
	Image->SetBrush(Brush);
	PanelAddRow(Content, Image, FMargin(0.f, 0.f, 0.f, 14.f), HAlign_Center);
}

UWTAActionButton* UWTAPanelWidget::AddButton(const FText& Label, FName Action, FName Arg, int32 Index, bool bPrimary)
{
	if (Content == nullptr)
	{
		return nullptr;
	}
	UWTAActionButton* Button = WTAWidgets::MakeButton(WidgetTree, Label, Action, Arg, Index,
		bPrimary ? WTAStyle::PrimaryButton() : WTAStyle::CardButton(),
		WTAStyle::Font(15, bPrimary), bPrimary ? WTAStyle::Ink() : WTAStyle::CardInk());
	Button->OnAction.AddDynamic(this, &UWTAPanelWidget::HandleAction);
	PanelAddRow(Content, Button, FMargin(0.f, 2.f, 0.f, 6.f), HAlign_Left);
	return Button;
}

void UWTAPanelWidget::AddLink(const FText& Label, const FString& Url)
{
	// Arg carries the URL for links that are not DT_Sources rows; HandleAction falls back to it.
	if (UWTAActionButton* Button = AddButton(Label, NAME_PanelLink, FName(*Url), -1, false))
	{
		Button->Payload = Url;
	}
}

void UWTAPanelWidget::SetHeaderExtras(const FText& Year, const FText& Subtitle)
{
	if (YearText != nullptr)
	{
		YearText->SetText(Year);
		YearText->SetVisibility(Year.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
	}
	if (SubtitleText != nullptr)
	{
		SubtitleText->SetText(Subtitle);
		SubtitleText->SetVisibility(Subtitle.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
	}
}

void UWTAPanelWidget::AddSection(const FText& Label)
{
	if (Content == nullptr || Label.IsEmpty())
	{
		return;
	}
	UVerticalBox* Box = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	UTextBlock* LabelText = WTAWidgets::MakeText(WidgetTree, PanelUpper(Label), WTAStyle::Kicker(12), WTAStyle::BrassDark(), false);
	Box->AddChildToVerticalBox(LabelText)->SetPadding(FMargin(0.f, 0.f, 0.f, 6.f));

	USizeBox* Rule = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	Rule->SetHeightOverride(1.f);
	Rule->SetContent(WTAWidgets::MakePlate(WidgetTree, PanelHairline(), FMargin(0.f)));
	Box->AddChildToVerticalBox(Rule);

	// The first section sits close under the header rule; later ones get air above them.
	const float Top = Content->GetChildrenCount() > 0 ? 18.f : 2.f;
	PanelAddRow(Content, Box, FMargin(0.f, Top, 0.f, 12.f));
}

void UWTAPanelWidget::AddFact(const FText& Label, const FText& Value)
{
	if (Content == nullptr || Value.IsEmpty())
	{
		return;
	}
	UHorizontalBox* Line = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());

	USizeBox* LabelWidth = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	LabelWidth->SetWidthOverride(120.f);
	LabelWidth->SetContent(WTAWidgets::MakeText(WidgetTree, PanelUpper(Label), WTAStyle::Kicker(11), WTAStyle::BrassDark(), false));
	UHorizontalBoxSlot* LabelSlot = Line->AddChildToHorizontalBox(LabelWidth);
	LabelSlot->SetVerticalAlignment(VAlign_Top);
	LabelSlot->SetPadding(FMargin(0.f, 4.f, 12.f, 0.f));

	UTextBlock* ValueText = WTAWidgets::MakeText(WidgetTree, Value, WTAStyle::Font(17), WTAStyle::CardInk(), true);
	UHorizontalBoxSlot* ValueSlot = Line->AddChildToHorizontalBox(ValueText);
	ValueSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

	PanelAddRow(Content, Line, FMargin(0.f, 0.f, 0.f, 10.f));
}

void UWTAPanelWidget::AddSceneLines(const TArray<FWTAWaxLine>& Lines)
{
	if (Content == nullptr || Lines.Num() == 0)
	{
		return;
	}
	UVerticalBox* Box = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	int32 Number = 0;
	for (const FWTAWaxLine& SceneLine : Lines)
	{
		if (SceneLine.Text.IsEmpty())
		{
			continue;
		}
		++Number;
		UHorizontalBox* LineBox = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());

		USizeBox* NumberWidth = WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		NumberWidth->SetWidthOverride(34.f);
		NumberWidth->SetContent(WTAWidgets::MakeText(WidgetTree, FText::AsNumber(Number), WTAStyle::Font(18, true), WTAStyle::BrassDark(), false));
		UHorizontalBoxSlot* NumberSlot = LineBox->AddChildToHorizontalBox(NumberWidth);
		NumberSlot->SetVerticalAlignment(VAlign_Top);

		UTextBlock* LineText = WTAWidgets::MakeText(WidgetTree, SceneLine.Text, WTAStyle::Font(18), WTAStyle::CardInk(), true);
		LineText->SetLineHeightPercentage(1.2f);
		UHorizontalBoxSlot* LineSlot = LineBox->AddChildToHorizontalBox(LineText);
		LineSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

		Box->AddChildToVerticalBox(LineBox)->SetPadding(FMargin(0.f, 0.f, 0.f, 10.f));
	}
	PanelAddRow(Content, Box, FMargin(0.f, 0.f, 0.f, 4.f));
}

void UWTAPanelWidget::AddSourceChips(const TArray<FName>& SourceIds)
{
	if (Content == nullptr || SourceIds.Num() == 0)
	{
		return;
	}
	const UWTAContentSubsystem* Data = UWTAContentSubsystem::Get(this);
	UWrapBox* Wrap = WidgetTree->ConstructWidget<UWrapBox>(UWrapBox::StaticClass());
	Wrap->SetInnerSlotPadding(FVector2D(8.f, 8.f));
	for (int32 i = 0; i < SourceIds.Num(); ++i)
	{
		const FName SourceId = SourceIds[i];
		const FWTASourceRow* Source = Data != nullptr ? Data->FindSource(SourceId) : nullptr;
		const FText Label = (Source != nullptr && !Source->Label.IsEmpty()) ? Source->Label : FText::FromName(SourceId);
		UWTAActionButton* Chip = WTAWidgets::MakeButton(WidgetTree, Label, NAME_PanelLink, SourceId, i,
			WTAStyle::CardButton(), WTAStyle::Font(14), WTAStyle::CardInk());
		Chip->OnAction.AddDynamic(this, &UWTAPanelWidget::HandleAction);
		Wrap->AddChildToWrapBox(Chip);
	}
	PanelAddRow(Content, Wrap, FMargin(0.f, 0.f, 0.f, 8.f));
}

void UWTAPanelWidget::SetOpen(bool bNewOpen)
{
	bOpen = bNewOpen;
	SetVisibility(bOpen ? ESlateVisibility::SelfHitTestInvisible : ESlateVisibility::Collapsed);

	if (!bOpen)
	{
		return;
	}

	// Keep the card inside the viewport: the scroll area gets what is left after header and footer.
	if (Scroll != nullptr)
	{
		if (USizeBox* ScrollHeight = Cast<USizeBox>(Scroll->GetParent()))
		{
			const FVector2D Viewport = UWidgetLayoutLibrary::GetViewportSize(this);
			const float Scale = UWidgetLayoutLibrary::GetViewportScale(this);
			if (Viewport.Y > 0.f && Scale > 0.f)
			{
				// Header (kicker, year, title, place) and footer take about 360 px at reading sizes.
				ScrollHeight->SetMaxDesiredHeight(FMath::Max(220.f, static_cast<float>(Viewport.Y) / Scale - 360.f));
			}
		}
	}

	SetKeyboardFocus();
}
