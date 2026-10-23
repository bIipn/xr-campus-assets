// Walk the Archive - the certificate a class gives for passing its quiz.

#include "UI/WTACertificateWidget.h"
#include "Core/WTAText.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/BorderSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/SizeBox.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "Core/WTASettings.h"
#include "Engine/TextureRenderTarget2D.h"
#include "HAL/FileManager.h"
#include "ImageUtils.h"
#include "InputCoreTypes.h"
#include "Misc/Paths.h"
#include "Slate/WidgetRenderer.h"
#include "UI/WTAActionButton.h"
#include "UI/WTAUIStyle.h"

namespace
{
	const FName NAME_CertSave(TEXT("Save"));
	const FName NAME_CertDone(TEXT("Done"));
	constexpr float ScreenScale = 0.62f;

	/** The client's mark on the seal: a short all-caps first word ("XR"), else the initials. */
	FString Monogram(const FString& Client)
	{
		TArray<FString> Words;
		Client.ParseIntoArrayWS(Words);
		if (Words.Num() == 0)
		{
			return TEXT("WA");
		}
		if (Words[0].Len() <= 3 && Words[0].ToUpper() == Words[0])
		{
			return Words[0];
		}
		FString Out;
		for (int32 i = 0; i < Words.Num() && i < 2; ++i)
		{
			Out.AppendChar(Words[i][0]);
		}
		return WTAUpper(Out);
	}

	UTextBlock* CentredText(UWidgetTree* Tree, UVerticalBox* Column, const FText& Text, const FSlateFontInfo& Font, const FLinearColor& Colour, float Below)
	{
		UTextBlock* Block = WTAWidgets::MakeText(Tree, Text, Font, Colour, true);
		Block->SetJustification(ETextJustify::Center);
		UVerticalBoxSlot* Slot = Column->AddChildToVerticalBox(Block);
		Slot->SetHorizontalAlignment(HAlign_Fill);
		Slot->SetPadding(FMargin(0.f, 0.f, 0.f, Below));
		return Block;
	}

	void CertificateRule(UWidgetTree* Tree, UVerticalBox* Column, float Width, float Height, const FLinearColor& Colour, float Below)
	{
		USizeBox* Box = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		Box->SetWidthOverride(Width);
		Box->SetHeightOverride(Height);
		Box->SetContent(WTAWidgets::MakePlate(Tree, Colour, FMargin(0.f)));
		UVerticalBoxSlot* Slot = Column->AddChildToVerticalBox(Box);
		Slot->SetHorizontalAlignment(HAlign_Center);
		Slot->SetPadding(FMargin(0.f, 0.f, 0.f, Below));
	}

	/** A signature block: the line in the script face over a rule, a small caption under it. */
	UWidget* SignatureBlock(UWidgetTree* Tree, const FText& Line, const FSlateFontInfo& LineFont, const FText& Caption, float S)
	{
		UVerticalBox* Column = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
		CentredText(Tree, Column, Line, LineFont, WTAStyle::CardInk(), 4.f * S);
		CertificateRule(Tree, Column, 300.f * S, 1.5f * S, WTAStyle::CardInkDim(), 8.f * S);
		CentredText(Tree, Column, Caption, WTAStyle::Font(FMath::RoundToInt(15.f * S)), WTAStyle::CardInkDim(), 0.f);
		return Column;
	}
}

void UWTACertificateWidget::Build(const FWTATalkRow& Talk, FName InTalkId, const FString& Name, const FString& Date, bool bForPrint)
{
	Row = Talk;
	TalkId = InTalkId;
	VisitorName = Name;
	DateText = Date;
	bForPrintSheet = bForPrint;
	UWidgetTree* Tree = WidgetTree;
	if (Tree == nullptr)
	{
		return;
	}
	if (bForPrint)
	{
		Tree->RootWidget = MakeSheet(1.f);
		return;
	}

	SetIsFocusable(true);
	UBorder* Scrim = WTAWidgets::MakePlate(Tree, WTAStyle::Scrim(), FMargin(0.f));
	Tree->RootWidget = Scrim;

	// The sheet and its buttons sit in the middle of the screen (an overlay slot centres them, as the panel's card is).
	UOverlay* Layers = Tree->ConstructWidget<UOverlay>(UOverlay::StaticClass());
	Scrim->SetContent(Layers);
	UVerticalBox* Column = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	UOverlaySlot* ColumnSlot = Layers->AddChildToOverlay(Column);
	ColumnSlot->SetHorizontalAlignment(HAlign_Center);
	ColumnSlot->SetVerticalAlignment(VAlign_Center);

	UVerticalBoxSlot* SheetSlot = Column->AddChildToVerticalBox(MakeSheet(ScreenScale));
	SheetSlot->SetHorizontalAlignment(HAlign_Center);

	UHorizontalBox* Buttons = Tree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	UVerticalBoxSlot* ButtonsSlot = Column->AddChildToVerticalBox(Buttons);
	ButtonsSlot->SetHorizontalAlignment(HAlign_Center);
	ButtonsSlot->SetPadding(FMargin(0.f, 18.f, 0.f, 0.f));

	SaveButton = WTAWidgets::MakeButton(Tree, WTAText(TEXT("Save a picture")), NAME_CertSave, NAME_None, -1,
		WTAStyle::SecondaryButton(), WTAStyle::Font(15, true), WTAStyle::Bone());
	SaveButton->OnAction.AddDynamic(this, &UWTACertificateWidget::HandleAction);
	Buttons->AddChildToHorizontalBox(SaveButton)->SetPadding(FMargin(0.f, 0.f, 12.f, 0.f));

	DoneButton = WTAWidgets::MakeButton(Tree, WTAText(TEXT("Done")), NAME_CertDone, NAME_None, -1,
		WTAStyle::PrimaryButton(), WTAStyle::Font(15, true), WTAStyle::Ink());
	DoneButton->OnAction.AddDynamic(this, &UWTACertificateWidget::HandleAction);
	Buttons->AddChildToHorizontalBox(DoneButton);

	bOpen = true;
	SetVisibility(ESlateVisibility::SelfHitTestInvisible);
	SetKeyboardFocus();
}

UWidget* UWTACertificateWidget::MakeSheet(float S)
{
	UWidgetTree* Tree = WidgetTree;
	const UWTASettings* Settings = UWTASettings::Get();
	const FString Client = Settings != nullptr ? Settings->ClientName : FString(TEXT("Walk the Archive"));
	const FString Campus = Settings != nullptr ? Settings->CampusTitle : FString();
	const FText Org = !Row.Certificate.Org.IsEmpty() ? Row.Certificate.Org : FText::FromString(Client);

	USizeBox* Size = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	Size->SetWidthOverride(PrintWidth * S);
	Size->SetHeightOverride(PrintHeight * S);

	// The sheet: cream, a brass frame a little in from the edge, a hairline inside it.
	UBorder* Sheet = WTAWidgets::MakePlate(Tree, WTAStyle::Card(), FMargin(34.f * S));
	Size->SetContent(Sheet);
	UBorder* Frame = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Frame->SetBrush(WTAStyle::EdgedBrush(WTAStyle::Card(), 2.f * S, WTAStyle::Brass(), 3.f * S));
	Frame->SetPadding(FMargin(9.f * S));
	Sheet->SetContent(Frame);
	UBorder* Inner = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Inner->SetBrush(WTAStyle::EdgedBrush(WTAStyle::Card(), 1.f * S, WTAStyle::BrassDim(), 1.2f * S));
	Inner->SetPadding(FMargin(70.f * S, 56.f * S, 70.f * S, 44.f * S));
	Frame->SetContent(Inner);

	UVerticalBox* Column = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Inner->SetContent(Column);

	CentredText(Tree, Column, FText::FromString(WTAUpper(Org.ToString()) + (Campus.IsEmpty() ? FString() : TEXT("  ·  ") + WTAUpper(Campus))),
		WTAStyle::Kicker(FMath::RoundToInt(16.f * S)), WTAStyle::BrassDark(), 26.f * S);
	CentredText(Tree, Column, !Row.Certificate.Title.IsEmpty() ? Row.Certificate.Title : WTAText(TEXT("Certificate of Completion")),
		WTAStyle::Serif(FMath::RoundToInt(72.f * S)), WTAStyle::CardInk(), 10.f * S);
	CertificateRule(Tree, Column, 360.f * S, 3.f * S, WTAStyle::Brass(), 34.f * S);
	CentredText(Tree, Column, WTAText(TEXT("This certifies that")), WTAStyle::SerifItalic(FMath::RoundToInt(30.f * S)), WTAStyle::CardInkDim(), 6.f * S);
	CentredText(Tree, Column, FText::FromString(VisitorName.IsEmpty() ? TEXT("A Visitor") : VisitorName), WTAStyle::Script(FMath::RoundToInt(112.f * S)), WTAStyle::BrassDark(), 0.f);
	CertificateRule(Tree, Column, 760.f * S, 1.5f * S, WTAStyle::CardInkDim(), 18.f * S);
	CentredText(Tree, Column, !Row.Certificate.Line.IsEmpty() ? Row.Certificate.Line : WTAText(TEXT("has completed the class")),
		WTAStyle::SerifItalic(FMath::RoundToInt(30.f * S)), WTAStyle::CardInkDim(), 10.f * S);
	CentredText(Tree, Column, Row.Title, WTAStyle::Serif(FMath::RoundToInt(56.f * S), true), WTAStyle::CardInk(), 4.f * S);
	if (!Row.Certificate.Place.IsEmpty())
	{
		CentredText(Tree, Column, Row.Certificate.Place, WTAStyle::Font(FMath::RoundToInt(22.f * S)), WTAStyle::CardInkDim(), 0.f);
	}

	USpacer* Gap = Tree->ConstructWidget<USpacer>(USpacer::StaticClass());
	Column->AddChildToVerticalBox(Gap)->SetSize(FSlateChildSize(ESlateSizeRule::Fill));

	// The foot: the date, the seal, the signature.
	UHorizontalBox* Foot = Tree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	Column->AddChildToVerticalBox(Foot)->SetPadding(FMargin(0.f, 0.f, 0.f, 22.f * S));
	{
		UHorizontalBoxSlot* DateSlot = Foot->AddChildToHorizontalBox(SignatureBlock(Tree, FText::FromString(DateText), WTAStyle::Serif(FMath::RoundToInt(34.f * S)), WTAText(TEXT("Date")), S));
		DateSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		DateSlot->SetHorizontalAlignment(HAlign_Center);
		DateSlot->SetVerticalAlignment(VAlign_Bottom);
	}
	{
		// The seal: two brass rings round the client's mark.
		USizeBox* SealSize = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		SealSize->SetWidthOverride(170.f * S);
		SealSize->SetHeightOverride(170.f * S);
		UBorder* Outer = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Outer->SetBrush(WTAStyle::EdgedBrush(FLinearColor(0.f, 0.f, 0.f, 0.f), 85.f * S, WTAStyle::Brass(), 3.f * S));
		Outer->SetPadding(FMargin(10.f * S));
		UBorder* Ring = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Ring->SetBrush(WTAStyle::EdgedBrush(FLinearColor(0.f, 0.f, 0.f, 0.f), 75.f * S, WTAStyle::BrassDim(), 1.5f * S));
		Ring->SetHorizontalAlignment(HAlign_Center);
		Ring->SetVerticalAlignment(VAlign_Center);
		UTextBlock* Mark = WTAWidgets::MakeText(Tree, FText::FromString(Monogram(Client)), WTAStyle::Serif(FMath::RoundToInt(64.f * S), true), WTAStyle::Brass(), false);
		Mark->SetJustification(ETextJustify::Center);
		Ring->SetContent(Mark);
		Outer->SetContent(Ring);
		SealSize->SetContent(Outer);
		UHorizontalBoxSlot* SealSlot = Foot->AddChildToHorizontalBox(SealSize);
		SealSlot->SetHorizontalAlignment(HAlign_Center);
		SealSlot->SetVerticalAlignment(VAlign_Bottom);
		SealSlot->SetPadding(FMargin(20.f * S, 0.f));
	}
	{
		const FString Signer = Row.Certificate.Signer.IsEmpty() ? Row.Speaker.ToString() : Row.Certificate.Signer.ToString();
		const FString Role = Row.Certificate.SignerRole.IsEmpty() ? Row.SpeakerRole.ToString() : Row.Certificate.SignerRole.ToString();
		UHorizontalBoxSlot* SignSlot = Foot->AddChildToHorizontalBox(SignatureBlock(Tree, FText::FromString(Signer), WTAStyle::Script(FMath::RoundToInt(46.f * S)),
			FText::FromString(Role.IsEmpty() ? Signer : FString::Printf(TEXT("%s, %s"), *Signer, *Role)), S));
		SignSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		SignSlot->SetHorizontalAlignment(HAlign_Center);
		SignSlot->SetVerticalAlignment(VAlign_Bottom);
	}
	if (!Row.Certificate.Note.IsEmpty())
	{
		CentredText(Tree, Column, Row.Certificate.Note, WTAStyle::Font(FMath::RoundToInt(13.f * S)), WTAStyle::CardInkDim(), 0.f);
	}
	return Size;
}

FString UWTACertificateWidget::PicturePath(const FString& Name, FName TalkId)
{
	FString Safe;
	for (const TCHAR C : Name)
	{
		Safe.AppendChar(FChar::IsAlnum(C) ? C : TEXT('_'));
	}
	if (Safe.IsEmpty())
	{
		Safe = TEXT("visitor");
	}
	return FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Certificates"), FString::Printf(TEXT("%s_%s.png"), *Safe, *TalkId.ToString().Replace(TEXT("-"), TEXT("_"))));
}

FString UWTACertificateWidget::SavePicture()
{
	APlayerController* Owner = GetOwningPlayer();
	UWTACertificateWidget* Print = Owner != nullptr ? CreateWidget<UWTACertificateWidget>(Owner, UWTACertificateWidget::StaticClass()) : nullptr;
	if (Print == nullptr)
	{
		return FString();
	}
	Print->Build(Row, TalkId, VisitorName, DateText, true);
	const TSharedRef<SWidget> Slate = Print->TakeWidget();
	FWidgetRenderer Renderer(true, true);
	UTextureRenderTarget2D* Target = Renderer.DrawWidget(Slate, FVector2D(PrintWidth, PrintHeight));
	if (Target == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("Certificate: nothing drawn"));
		return FString();
	}
	// (the PNG export reads the target back, which waits for the draw itself)
	const FString Path = PicturePath(VisitorName, TalkId);
	IFileManager::Get().MakeDirectory(*FPaths::GetPath(Path), true);
	TUniquePtr<FArchive> Ar(IFileManager::Get().CreateFileWriter(*Path));
	if (!Ar.IsValid())
	{
		UE_LOG(LogWTA, Warning, TEXT("Certificate: could not write %s"), *Path);
		return FString();
	}
	const bool bOk = FImageUtils::ExportRenderTarget2DAsPNG(Target, *Ar);
	Ar->Close();
	if (!bOk)
	{
		UE_LOG(LogWTA, Warning, TEXT("Certificate: PNG export failed for %s"), *Path);
		return FString();
	}
	UE_LOG(LogWTA, Log, TEXT("Certificate: saved %s"), *Path);
	return Path;
}

void UWTACertificateWidget::Close()
{
	bOpen = false;
	SetVisibility(ESlateVisibility::Collapsed);
}

FReply UWTACertificateWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	if (InKeyEvent.GetKey() == EKeys::Escape || InKeyEvent.GetKey() == EKeys::Enter)
	{
		HandleAction(NAME_CertDone, NAME_None, -1);
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

void UWTACertificateWidget::HandleAction(FName Action, FName Arg, int32 Index)
{
	AWTAPlayerController* PC = Cast<AWTAPlayerController>(GetOwningPlayer());
	if (Action == NAME_CertSave)
	{
		const FString Path = SavePicture();
		if (PC != nullptr)
		{
			PC->ShowToast(FText::FromString(Path.IsEmpty() ? TEXT("The picture could not be saved.") : FString::Printf(TEXT("Saved to %s"), *FPaths::ConvertRelativePathToFull(Path))), 6.f);
		}
		return;
	}
	if (Action == NAME_CertDone)
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
}
