// Walk the Archive - the name over a person's figure in a guided visit.

#include "UI/WTANameTagWidget.h"
#include "Core/WTAText.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "UI/WTAUIStyle.h"

void UWTANameTagWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	UWidgetTree* Tree = WidgetTree;
	if (Tree == nullptr)
	{
		return;
	}

	Plate = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
	{
		FLinearColor Fill = WTAStyle::Panel();
		Fill.A = 0.9f;
		Plate->SetBrush(WTAStyle::EdgedBrush(Fill, 7.f, WTAStyle::BrassDim(), 1.f));
	}
	Plate->SetPadding(FMargin(10.f, 5.f, 12.f, 6.f));
	Plate->SetVisibility(ESlateVisibility::HitTestInvisible);
	Tree->RootWidget = Plate;

	UVerticalBox* Column = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Plate->SetContent(Column);

	KickerText = WTAWidgets::MakeText(Tree, WTAUpper(WTAText(TEXT("Guide"))), WTAStyle::Kicker(9), WTAStyle::Brass(), false);
	KickerText->SetVisibility(ESlateVisibility::Collapsed);
	Column->AddChildToVerticalBox(KickerText)->SetPadding(FMargin(17.f, 0.f, 0.f, 1.f));

	UHorizontalBox* Row = Tree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	Column->AddChildToVerticalBox(Row);

	// The person's colour, the same as their figure's.
	USizeBox* DotSize = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	DotSize->SetWidthOverride(9.f);
	DotSize->SetHeightOverride(9.f);
	Dot = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Dot->SetBrush(WTAStyle::RoundedBrush(WTAStyle::Bone(), 4.5f));
	DotSize->SetContent(Dot);
	UHorizontalBoxSlot* DotSlot = Row->AddChildToHorizontalBox(DotSize);
	DotSlot->SetVerticalAlignment(VAlign_Center);
	DotSlot->SetPadding(FMargin(0.f, 1.f, 8.f, 0.f));

	NameText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(13, true), WTAStyle::Bone(), false);
	Row->AddChildToHorizontalBox(NameText)->SetVerticalAlignment(VAlign_Center);
}

void UWTANameTagWidget::SetPerson(const FText& Name, bool bGuide, const FLinearColor& Color)
{
	if (NameText != nullptr)
	{
		NameText->SetText(Name);
	}
	if (Dot != nullptr)
	{
		Dot->SetBrush(WTAStyle::RoundedBrush(Color, 4.5f));
	}
	if (KickerText != nullptr)
	{
		KickerText->SetVisibility(bGuide ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	}
	if (Plate != nullptr)
	{
		FLinearColor Fill = WTAStyle::Panel();
		Fill.A = 0.9f;
		Plate->SetBrush(WTAStyle::EdgedBrush(Fill, 7.f, bGuide ? WTAStyle::Brass() : WTAStyle::BrassDim(), bGuide ? 1.5f : 1.f));
	}
}
