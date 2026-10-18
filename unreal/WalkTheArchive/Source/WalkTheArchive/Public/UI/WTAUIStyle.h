// Walk the Archive - the UI palette, fonts and small widget builders (header only, no reflection).
//
// Colours are the web build's: ink #0d1613, panel #15221e, brass #cda961, bone #efe7d5, card #f2e9d7,
// card ink #2b2419. Fonts come from Slate's default composite font (Roboto) through FCoreStyle, which is
// packaged with every build, so no font asset is needed.
// The WTAWidgets builders take the owning widget's UWidgetTree and return widgets ready to add to a panel.

#pragma once

#include "CoreMinimal.h"
#include "Math/Color.h"
#include "Math/Vector4.h"
#include "Layout/Margin.h"
#include "Fonts/SlateFontInfo.h"
#include "Styling/CoreStyle.h"
#include "Styling/SlateBrush.h"
#include "Styling/SlateTypes.h"
#include "Brushes/SlateColorBrush.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/TextBlock.h"
#include "UI/WTAActionButton.h"

namespace WTAStyle
{
	/** sRGB hex (0xRRGGBB) to linear. */
	inline FLinearColor FromHex(uint32 Rgb)
	{
		const uint8 R = static_cast<uint8>((Rgb >> 16) & 0xFF);
		const uint8 G = static_cast<uint8>((Rgb >> 8) & 0xFF);
		const uint8 B = static_cast<uint8>(Rgb & 0xFF);
		return FLinearColor::FromSRGBColor(FColor(R, G, B, 255));
	}

	inline FLinearColor Ink()      { return FromHex(0x0d1613); }
	inline FLinearColor Panel()    { return FromHex(0x15221e); }
	inline FLinearColor Brass()    { return FromHex(0xcda961); }
	inline FLinearColor Bone()     { return FromHex(0xefe7d5); }
	inline FLinearColor Card()     { return FromHex(0xf2e9d7); }
	inline FLinearColor CardInk()  { return FromHex(0x2b2419); }

	/** Dimmed bone for secondary text on dark panels. */
	inline FLinearColor BoneDim()  { FLinearColor C = Bone(); C.A = 0.72f; return C; }

	/** Dimmed card ink for secondary text on cards. */
	inline FLinearColor CardInkDim() { FLinearColor C = CardInk(); C.A = 0.7f; return C; }

	/** Full-screen scrim behind modal panels. */
	inline FLinearColor Scrim()    { return FLinearColor(0.f, 0.f, 0.f, 0.55f); }

	/** Translucent HUD plate (room label, toasts, captions). */
	inline FLinearColor Plate()    { FLinearColor C = Ink(); C.A = 0.78f; return C; }

	/** Default toast time in seconds (web 3.4). */
	constexpr float ToastSeconds = 3.4f;

	/** Regular or bold Roboto at Size points. */
	inline FSlateFontInfo Font(int32 Size, bool bBold = false)
	{
		return FCoreStyle::GetDefaultFontStyle(bBold ? FName(TEXT("Bold")) : FName(TEXT("Regular")), Size);
	}

	/** Italic Roboto (quotes). */
	inline FSlateFontInfo Italic(int32 Size)
	{
		return FCoreStyle::GetDefaultFontStyle(FName(TEXT("Italic")), Size);
	}

	/** Monospace (code blocks). */
	inline FSlateFontInfo Mono(int32 Size)
	{
		return FCoreStyle::GetDefaultFontStyle(FName(TEXT("Mono")), Size);
	}

	/** Small caps for kickers and section labels: bold Roboto with wide letter spacing (museum-label style). */
	inline FSlateFontInfo Kicker(int32 Size)
	{
		FSlateFontInfo Info = Font(Size, true);
		Info.LetterSpacing = 140;
		return Info;
	}

	/** A solid-colour brush. */
	inline FSlateBrush SolidBrush(const FLinearColor& Color)
	{
		return FSlateColorBrush(Color);
	}

	/** A solid rounded-corner brush. */
	inline FSlateBrush RoundedBrush(const FLinearColor& Color, float Radius)
	{
		FSlateBrush Brush = SolidBrush(Color);
		Brush.DrawAs = ESlateBrushDrawType::RoundedBox;
		Brush.OutlineSettings.CornerRadii = FVector4(Radius, Radius, Radius, Radius);
		Brush.OutlineSettings.RoundingType = ESlateBrushRoundingType::FixedRadius;
		Brush.OutlineSettings.Width = 0.f;
		return Brush;
	}

	/** A solid rounded brush with a thin edge line (brass edges on the dark panels). */
	inline FSlateBrush EdgedBrush(const FLinearColor& Color, float Radius, const FLinearColor& Edge, float EdgeWidth = 1.5f)
	{
		FSlateBrush Brush = RoundedBrush(Color, Radius);
		Brush.OutlineSettings.Color = FSlateColor(Edge);
		Brush.OutlineSettings.Width = EdgeWidth;
		return Brush;
	}

	/** Dark brass for small text on the cream cards. */
	inline FLinearColor BrassDark() { return FromHex(0x8a6d2f); }

	/** Dim brass for thin edges on small dark plates (web --brass-dim). */
	inline FLinearColor BrassDim() { return FromHex(0x7d6840); }

	/** Button style: Fill at rest, a little lighter hovered, a little darker pressed. */
	inline FButtonStyle ButtonStyle(const FLinearColor& Fill, const FLinearColor& Hovered, const FLinearColor& Pressed)
	{
		FButtonStyle Style;
		Style.SetNormal(RoundedBrush(Fill, 6.f));
		Style.SetHovered(RoundedBrush(Hovered, 6.f));
		Style.SetPressed(RoundedBrush(Pressed, 6.f));
		Style.SetNormalPadding(FMargin(14.f, 8.f));
		Style.SetPressedPadding(FMargin(14.f, 9.f, 14.f, 7.f));
		return Style;
	}

	/** Brass primary button. */
	inline FButtonStyle PrimaryButton()
	{
		return ButtonStyle(Brass(), FromHex(0xdcbb75), FromHex(0xb8944f));
	}

	/** Quiet secondary button on dark panels. */
	inline FButtonStyle SecondaryButton()
	{
		return ButtonStyle(FromHex(0x24352f), FromHex(0x2f4540), FromHex(0x1b2925));
	}

	/** Chip button on cards. */
	inline FButtonStyle CardButton()
	{
		return ButtonStyle(FromHex(0xe4d8c0), FromHex(0xd9c9a9), FromHex(0xcdbd9c));
	}
}

namespace WTAWidgets
{
	/** A text block with font and colour set. Returns null without a tree. */
	inline UTextBlock* MakeText(UWidgetTree* Tree, const FText& Text, const FSlateFontInfo& Font, const FLinearColor& Color, bool bAutoWrap = true)
	{
		if (Tree == nullptr)
		{
			return nullptr;
		}
		UTextBlock* Block = Tree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		Block->SetText(Text);
		Block->SetFont(Font);
		Block->SetColorAndOpacity(FSlateColor(Color));
		Block->SetAutoWrapText(bAutoWrap);
		return Block;
	}

	/** A border with a solid (optionally rounded) fill and padding. */
	inline UBorder* MakePlate(UWidgetTree* Tree, const FLinearColor& Fill, const FMargin& Padding, float Radius = 0.f)
	{
		if (Tree == nullptr)
		{
			return nullptr;
		}
		UBorder* Border = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Border->SetBrush(Radius > 0.f ? WTAStyle::RoundedBrush(Fill, Radius) : WTAStyle::SolidBrush(Fill));
		Border->SetPadding(Padding);
		return Border;
	}

	/** An action button with a text label. The caller binds Button->OnAction. */
	inline UWTAActionButton* MakeButton(UWidgetTree* Tree, const FText& Label, FName Action, FName Arg, int32 Index,
		const FButtonStyle& Style, const FSlateFontInfo& Font, const FLinearColor& TextColor)
	{
		if (Tree == nullptr)
		{
			return nullptr;
		}
		UWTAActionButton* Button = Tree->ConstructWidget<UWTAActionButton>(UWTAActionButton::StaticClass());
		Button->SetStyle(Style);
		Button->Init(Action, Arg, Index);
		UTextBlock* Text = MakeText(Tree, Label, Font, TextColor, false);
		Button->AddChild(Text);
		return Button;
	}

	/** Change the label of a button made by MakeButton. */
	inline void SetButtonLabel(UWTAActionButton* Button, const FText& Label)
	{
		if (Button == nullptr)
		{
			return;
		}
		if (UTextBlock* Text = Cast<UTextBlock>(Button->GetChildAt(0)))
		{
			Text->SetText(Label);
		}
	}
}
