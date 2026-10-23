// Walk the Archive - a VR screen's content: the game's own widgets stacked as layers; the laser's label.

#include "UI/WTAVRRootWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/TextBlock.h"
#include "UI/WTAUIStyle.h"

void UWTAVRRootWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	UWidgetTree* Tree = WidgetTree;
	if (Tree == nullptr)
	{
		return;
	}
	UOverlay* Root = Tree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
	Tree->RootWidget = Root;

	Backing = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
	FLinearColor Fill = WTAStyle::Panel();
	Fill.A = 0.94f;
	FLinearColor Edge = WTAStyle::Brass();
	Edge.A = 0.55f;
	Backing->SetBrush(WTAStyle::EdgedBrush(Fill, 30.f, Edge, 3.f));
	Backing->SetVisibility(ESlateVisibility::Collapsed);
	if (UOverlaySlot* BackSlot = Root->AddChildToOverlay(Backing))
	{
		BackSlot->SetHorizontalAlignment(HAlign_Fill);
		BackSlot->SetVerticalAlignment(VAlign_Fill);
	}

	Layers = Tree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
	if (UOverlaySlot* LayerSlot = Root->AddChildToOverlay(Layers))
	{
		LayerSlot->SetHorizontalAlignment(HAlign_Fill);
		LayerSlot->SetVerticalAlignment(VAlign_Fill);
	}
}

void UWTAVRRootWidget::AddLayer(UUserWidget* Widget, int32 ZOrder)
{
	if (Widget == nullptr || Layers == nullptr)
	{
		return;
	}
	Widget->RemoveFromParent();
	Order.Add(TWeakObjectPtr<UUserWidget>(Widget), ZOrder);
	// After every layer at or under this z-order, as AddToViewport would stack them.
	int32 Index = 0;
	for (int32 i = 0; i < Layers->GetChildrenCount(); ++i)
	{
		const int32* Z = Order.Find(TWeakObjectPtr<UUserWidget>(Cast<UUserWidget>(Layers->GetChildAt(i))));
		if (Z != nullptr && *Z <= ZOrder)
		{
			Index = i + 1;
		}
	}
	if (UOverlaySlot* Placed = Cast<UOverlaySlot>(Layers->InsertChildAt(Index, Widget)))
	{
		Placed->SetHorizontalAlignment(HAlign_Fill);
		Placed->SetVerticalAlignment(VAlign_Fill);
	}
}

bool UWTAVRRootWidget::HasVisibleLayer() const
{
	if (Layers == nullptr)
	{
		return false;
	}
	for (int32 i = 0; i < Layers->GetChildrenCount(); ++i)
	{
		const UWidget* Child = Layers->GetChildAt(i);
		const ESlateVisibility Shown = Child != nullptr ? Child->GetVisibility() : ESlateVisibility::Collapsed;
		if (Shown != ESlateVisibility::Collapsed && Shown != ESlateVisibility::Hidden)
		{
			return true;
		}
	}
	return false;
}

void UWTAVRRootWidget::SetBacking(bool bOn)
{
	if (Backing != nullptr)
	{
		Backing->SetVisibility(bOn ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	}
}

// --- The laser's label ---------------------------------------------------------------------------

void UWTAVRLabelWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	UWidgetTree* Tree = WidgetTree;
	if (Tree == nullptr)
	{
		return;
	}
	// The HUD's hover plate (WTAHudWidget.cpp): reads on white walls, pale book covers and dark wood alike.
	Plate = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
	FLinearColor Fill = WTAStyle::Panel();
	Fill.A = 0.92f;
	Plate->SetBrush(WTAStyle::EdgedBrush(Fill, 6.f, WTAStyle::BrassDim(), 1.f));
	Plate->SetPadding(FMargin(10.f, 5.f, 10.f, 6.f));
	Plate->SetVisibility(ESlateVisibility::Collapsed);
	LabelText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(13, true), WTAStyle::Bone(), false);
	Plate->SetContent(LabelText);
	Tree->RootWidget = Plate;
}

void UWTAVRLabelWidget::SetLabel(const FText& Text)
{
	Shown = Text;
	if (LabelText != nullptr)
	{
		LabelText->SetText(Text);
	}
	if (Plate != nullptr)
	{
		Plate->SetVisibility(Text.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
	}
}
