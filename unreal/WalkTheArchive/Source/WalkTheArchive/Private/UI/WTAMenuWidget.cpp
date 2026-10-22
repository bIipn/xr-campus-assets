// Walk the Archive - the intro / pause menu, built in code.

#include "UI/WTAMenuWidget.h"
#include "Core/WTASettings.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/SlateWrapperTypes.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Core/WTAPlayerController.h"
#include "Data/WTATypes.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Layout/Margin.h"
#include "Styling/SlateBrush.h"
#include "Systems/WTAGraphicsLibrary.h"
#include "Systems/WTATourSubsystem.h"
#include "UI/WTAActionButton.h"
#include "UI/WTAUIStyle.h"

namespace
{
	const FName NAME_MenuEnter(TEXT("Enter"));
	const FName NAME_MenuTour(TEXT("Tour"));
	const FName NAME_MenuGraphics(TEXT("Graphics"));
	const FName NAME_MenuQuit(TEXT("Quit"));

	/** A full-width menu button with centred text. */
	UWTAActionButton* MakeMenuButton(UWidgetTree* Tree, const FText& Label, FName Action, int32 Index,
		const FButtonStyle& Style, const FSlateFontInfo& Font, const FLinearColor& Color, UTextBlock** OutText = nullptr)
	{
		UWTAActionButton* Button = Tree->ConstructWidget<UWTAActionButton>(UWTAActionButton::StaticClass());
		Button->SetStyle(Style);
		Button->Init(Action, NAME_None, Index);
		UTextBlock* Text = WTAWidgets::MakeText(Tree, Label, Font, Color, false);
		Text->SetJustification(ETextJustify::Center);
		Button->AddChild(Text);
		if (OutText != nullptr)
		{
			*OutText = Text;
		}
		return Button;
	}
}

void UWTAMenuWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();

	UWidgetTree* Tree = WidgetTree;
	if (Tree == nullptr)
	{
		return;
	}

	// A darker scrim than the panels: this is the first thing the player sees.
	FLinearColor ScrimColor = WTAStyle::Ink();
	ScrimColor.A = 0.9f;
	Scrim = WTAWidgets::MakePlate(Tree, ScrimColor, FMargin(0.f));
	Scrim->SetHorizontalAlignment(HAlign_Center);
	Scrim->SetVerticalAlignment(VAlign_Center);
	Tree->RootWidget = Scrim;

	Card = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Card->SetBrush(WTAStyle::EdgedBrush(WTAStyle::Panel(), 14.f, WTAStyle::Brass()));
	Card->SetPadding(FMargin(40.f, 36.f, 40.f, 30.f));
	Scrim->SetContent(Card);

	USizeBox* CardWidth = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	CardWidth->SetWidthOverride(520.f);
	Card->SetContent(CardWidth);

	UVerticalBox* Column = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	CardWidth->SetContent(Column);

	// Kicker, title, subtitle.
	const UWTASettings* Settings = UWTASettings::Get();
	const FString ClientName = Settings != nullptr && !Settings->ClientName.IsEmpty() ? Settings->ClientName : TEXT("XR Libraries");
	const FString CampusTitle = Settings != nullptr && !Settings->CampusTitle.IsEmpty() ? Settings->CampusTitle : TEXT("Walk the Archive");
	UTextBlock* Kicker = WTAWidgets::MakeText(Tree, FText::FromString(ClientName.Replace(TEXT(" "), TEXT("")).ToUpper() + TEXT(" CAMPUS")), WTAStyle::Font(12, true), WTAStyle::Brass(), false);
	Column->AddChildToVerticalBox(Kicker)->SetPadding(FMargin(0.f, 0.f, 0.f, 6.f));

	TitleText = WTAWidgets::MakeText(Tree, FText::FromString(CampusTitle), WTAStyle::Font(34, true), WTAStyle::Bone(), true);
	Column->AddChildToVerticalBox(TitleText)->SetPadding(FMargin(0.f, 0.f, 0.f, 10.f));

	SubtitleText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(14), WTAStyle::BoneDim(), true);
	Column->AddChildToVerticalBox(SubtitleText)->SetPadding(FMargin(0.f, 0.f, 0.f, 22.f));

	// Enter / Resume, Take the tour.
	UTextBlock* EnterLabel = nullptr;
	EnterButton = MakeMenuButton(Tree, FText::FromString(TEXT("Enter")), NAME_MenuEnter, -1,
		WTAStyle::PrimaryButton(), WTAStyle::Font(16, true), WTAStyle::Ink(), &EnterLabel);
	EnterText = EnterLabel;
	EnterButton->OnAction.AddDynamic(this, &UWTAMenuWidget::HandleAction);
	Column->AddChildToVerticalBox(EnterButton)->SetPadding(FMargin(0.f, 0.f, 0.f, 10.f));

	TourButton = MakeMenuButton(Tree, FText::FromString(TEXT("Take the tour")), NAME_MenuTour, -1,
		WTAStyle::SecondaryButton(), WTAStyle::Font(15), WTAStyle::Bone());
	TourButton->OnAction.AddDynamic(this, &UWTAMenuWidget::HandleAction);
	Column->AddChildToVerticalBox(TourButton)->SetPadding(FMargin(0.f, 0.f, 0.f, 24.f));

	// Graphics presets.
	GraphicsLabel = WTAWidgets::MakeText(Tree, FText::FromString(TEXT("GRAPHICS")), WTAStyle::Font(12, true), WTAStyle::Brass(), false);
	Column->AddChildToVerticalBox(GraphicsLabel)->SetPadding(FMargin(0.f, 0.f, 0.f, 8.f));

	GraphicsRow = Tree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	{
		const TCHAR* Labels[] = { TEXT("Low"), TEXT("Medium"), TEXT("High"), TEXT("Epic"), TEXT("Cinematic"), TEXT("Auto") };
		const int32 Levels[] = { 0, 1, 2, 3, 4, -1 };
		for (int32 i = 0; i < 6; ++i)
		{
			UWTAActionButton* Button = MakeMenuButton(Tree, FText::FromString(Labels[i]), NAME_MenuGraphics, Levels[i],
				WTAStyle::SecondaryButton(), WTAStyle::Font(12), WTAStyle::Bone());
			Button->OnAction.AddDynamic(this, &UWTAMenuWidget::HandleAction);
			UHorizontalBoxSlot* ButtonSlot = GraphicsRow->AddChildToHorizontalBox(Button);
			ButtonSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
			ButtonSlot->SetPadding(FMargin(i == 0 ? 0.f : 3.f, 0.f, i == 5 ? 0.f : 3.f, 0.f));
		}
	}
	Column->AddChildToVerticalBox(GraphicsRow)->SetPadding(FMargin(0.f, 0.f, 0.f, 24.f));

	// Quit.
	QuitButton = MakeMenuButton(Tree, FText::FromString(TEXT("Quit")), NAME_MenuQuit, -1,
		WTAStyle::SecondaryButton(), WTAStyle::Font(14), WTAStyle::BoneDim());
	QuitButton->OnAction.AddDynamic(this, &UWTAMenuWidget::HandleAction);
	Column->AddChildToVerticalBox(QuitButton)->SetPadding(FMargin(0.f, 0.f, 0.f, 18.f));

	// Controls line.
	UTextBlock* Controls = WTAWidgets::MakeText(Tree,
		FText::FromString(TEXT("WASD walk \u00B7 mouse look \u00B7 Shift sprint \u00B7 E or click opens things \u00B7 Tab frees the cursor \u00B7 T tour \u00B7 M places \u00B7 Enter asks the staff \u00B7 Esc menu")),
		WTAStyle::Font(11), WTAStyle::BoneDim(), true);
	Controls->SetJustification(ETextJustify::Center);
	Column->AddChildToVerticalBox(Controls);

	bOpen = false;
	SetVisibility(ESlateVisibility::Collapsed);
}

void UWTAMenuWidget::Open(bool bInIntro)
{
	bIntro = bInIntro;

	if (EnterText != nullptr)
	{
		EnterText->SetText(FText::FromString(bIntro ? TEXT("Enter") : TEXT("Resume")));
	}
	if (SubtitleText != nullptr)
	{
		SubtitleText->SetText(FText::FromString(bIntro
			? TEXT("A walkable museum, library and workshop school about XRLibraries and the story of XR in public libraries. Walk in, open things, ask the staff.")
			: TEXT("The campus keeps running while this is open. Resume to carry on where you were.")));
	}
	RefreshGraphicsLabel();

	bOpen = true;
	SetVisibility(ESlateVisibility::SelfHitTestInvisible);
}

void UWTAMenuWidget::Close()
{
	bOpen = false;
	SetVisibility(ESlateVisibility::Collapsed);
}

void UWTAMenuWidget::RefreshGraphicsLabel()
{
	if (GraphicsLabel == nullptr)
	{
		return;
	}
	const int32 Level = UWTAGraphicsLibrary::GetQualityPreset();
	const FString Name = UWTAGraphicsLibrary::GetQualityPresetLabel(Level).ToString().ToUpper();
	GraphicsLabel->SetText(FText::FromString(FString::Printf(TEXT("GRAPHICS \u00B7 %s"), *Name)));
}

void UWTAMenuWidget::HandleAction(FName Action, FName Arg, int32 Index)
{
	AWTAPlayerController* PC = Cast<AWTAPlayerController>(GetOwningPlayer());

	if (Action == NAME_MenuEnter)
	{
		if (PC != nullptr)
		{
			PC->CloseTopPanel();
		}
		else
		{
			Close();
		}
	}
	else if (Action == NAME_MenuTour)
	{
		if (PC != nullptr)
		{
			PC->CloseTopPanel();
			PC->RunAction(WTAAction::StartTour(), NAME_None);
		}
		else
		{
			Close();
			if (UWTATourSubsystem* Tour = UWTATourSubsystem::Get(this))
			{
				Tour->Start();
			}
		}
	}
	else if (Action == NAME_MenuGraphics)
	{
		if (Index < 0)
		{
			UWTAGraphicsLibrary::RunAutoDetect();
		}
		else
		{
			UWTAGraphicsLibrary::ApplyQualityPreset(Index);
		}
		RefreshGraphicsLabel();
	}
	else if (Action == NAME_MenuQuit)
	{
		UKismetSystemLibrary::QuitGame(this, PC, EQuitPreference::Quit, false);
	}
}
