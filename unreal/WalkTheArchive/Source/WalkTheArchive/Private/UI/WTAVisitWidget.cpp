// Walk the Archive - the "Visit together" card, built in code.

#include "UI/WTAVisitWidget.h"
#include "Core/WTAPlayerController.h"
#include "Core/WTAText.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/EditableTextBox.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Systems/WTATourSubsystem.h"
#include "Systems/WTAVisitSubsystem.h"
#include "UI/WTAActionButton.h"
#include "UI/WTAUIStyle.h"

namespace
{
	const FName NAME_VisitLead(TEXT("Lead"));
	const FName NAME_VisitJoin(TEXT("Join"));
	const FName NAME_VisitJoinAddress(TEXT("JoinAddress"));
	const FName NAME_VisitGather(TEXT("Gather"));
	const FName NAME_VisitTour(TEXT("Tour"));
	const FName NAME_VisitLeave(TEXT("Leave"));
	const FName NAME_VisitWalk(TEXT("Walk"));
	const FName NAME_VisitClose(TEXT("Close"));

	UTextBlock* SectionLabel(UWidgetTree* Tree, const FText& Label)
	{
		return WTAWidgets::MakeText(Tree, WTAUpper(Label), WTAStyle::Kicker(11), WTAStyle::Brass(), false);
	}

	/** A coloured dot and a name, for the people list. */
	UWidget* PersonRow(UWidgetTree* Tree, const FWTAVisitPerson& Person)
	{
		UHorizontalBox* Row = Tree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
		USizeBox* DotSize = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
		DotSize->SetWidthOverride(10.f);
		DotSize->SetHeightOverride(10.f);
		UBorder* Dot = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
		Dot->SetBrush(WTAStyle::RoundedBrush(Person.Color, 5.f));
		DotSize->SetContent(Dot);
		UHorizontalBoxSlot* DotSlot = Row->AddChildToHorizontalBox(DotSize);
		DotSlot->SetVerticalAlignment(VAlign_Center);
		DotSlot->SetPadding(FMargin(0.f, 1.f, 10.f, 0.f));
		FText Label = FText::FromString(Person.Name);
		if (Person.bGuide && Person.bYou)
		{
			Label = FText::Format(WTAText(TEXT("{0} (you, the guide)")), Label);
		}
		else if (Person.bGuide)
		{
			Label = FText::Format(WTAText(TEXT("{0} (the guide)")), Label);
		}
		else if (Person.bYou)
		{
			Label = FText::Format(WTAText(TEXT("{0} (you)")), Label);
		}
		UTextBlock* Name = WTAWidgets::MakeText(Tree, Label, WTAStyle::Font(14, Person.bGuide), WTAStyle::Bone(), false);
		Row->AddChildToHorizontalBox(Name)->SetVerticalAlignment(VAlign_Center);
		return Row;
	}
}

void UWTAVisitWidget::NativeOnInitialized()
{
	Super::NativeOnInitialized();
	UWidgetTree* Tree = WidgetTree;
	if (Tree == nullptr)
	{
		return;
	}

	FLinearColor ScrimColor = WTAStyle::Ink();
	ScrimColor.A = 0.78f;
	Scrim = WTAWidgets::MakePlate(Tree, ScrimColor, FMargin(0.f));
	Scrim->SetHorizontalAlignment(HAlign_Center);
	Scrim->SetVerticalAlignment(VAlign_Center);
	Tree->RootWidget = Scrim;

	UBorder* Card = Tree->ConstructWidget<UBorder>(UBorder::StaticClass());
	Card->SetBrush(WTAStyle::EdgedBrush(WTAStyle::Panel(), 14.f, WTAStyle::Brass()));
	Card->SetPadding(FMargin(38.f, 32.f, 38.f, 28.f));
	Scrim->SetContent(Card);

	USizeBox* Width = Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass());
	Width->SetWidthOverride(560.f);
	Card->SetContent(Width);

	UVerticalBox* Column = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Width->SetContent(Column);

	Column->AddChildToVerticalBox(SectionLabel(Tree, WTAText(TEXT("Guided visit"))))->SetPadding(FMargin(0.f, 0.f, 0.f, 6.f));
	TitleText = WTAWidgets::MakeText(Tree, WTAText(TEXT("Visit together")), WTAStyle::Font(30, true), WTAStyle::Bone(), true);
	Column->AddChildToVerticalBox(TitleText)->SetPadding(FMargin(0.f, 0.f, 0.f, 8.f));
	BodyText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(14), WTAStyle::BoneDim(), true);
	BodyText->SetLineHeightPercentage(1.15f);
	Column->AddChildToVerticalBox(BodyText)->SetPadding(FMargin(0.f, 0.f, 0.f, 18.f));

	// --- On your own: name, lead, the visits heard, join by address ---
	SoloBox = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Column->AddChildToVerticalBox(SoloBox);
	{
		SoloBox->AddChildToVerticalBox(SectionLabel(Tree, WTAText(TEXT("Your name"))))->SetPadding(FMargin(0.f, 0.f, 0.f, 6.f));
		NameBox = Tree->ConstructWidget<UEditableTextBox>(UEditableTextBox::StaticClass());
		NameBox->SetHintText(WTAText(TEXT("The name the others see over you")));
		SoloBox->AddChildToVerticalBox(NameBox)->SetPadding(FMargin(0.f, 0.f, 0.f, 12.f));

		UWTAActionButton* Lead = WTAWidgets::MakeButton(Tree, WTAText(TEXT("Lead a visit")), NAME_VisitLead, NAME_None, -1,
			WTAStyle::PrimaryButton(), WTAStyle::Font(15, true), WTAStyle::Ink());
		if (UTextBlock* LeadText = Cast<UTextBlock>(Lead->GetChildAt(0)))
		{
			LeadText->SetJustification(ETextJustify::Center);
		}
		Lead->OnAction.AddDynamic(this, &UWTAVisitWidget::HandleAction);
		SoloBox->AddChildToVerticalBox(Lead)->SetPadding(FMargin(0.f, 0.f, 0.f, 20.f));

		SoloBox->AddChildToVerticalBox(SectionLabel(Tree, WTAText(TEXT("Visits on this network"))))->SetPadding(FMargin(0.f, 0.f, 0.f, 8.f));
		FoundList = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
		SoloBox->AddChildToVerticalBox(FoundList)->SetPadding(FMargin(0.f, 0.f, 0.f, 16.f));

		SoloBox->AddChildToVerticalBox(SectionLabel(Tree, WTAText(TEXT("Or join by address"))))->SetPadding(FMargin(0.f, 0.f, 0.f, 6.f));
		UHorizontalBox* AddressRow = Tree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
		AddressBox = Tree->ConstructWidget<UEditableTextBox>(UEditableTextBox::StaticClass());
		AddressBox->SetHintText(WTAText(TEXT("The guide's address, e.g. 192.168.1.20")));
		UHorizontalBoxSlot* AddressSlot = AddressRow->AddChildToHorizontalBox(AddressBox);
		AddressSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		AddressSlot->SetVerticalAlignment(VAlign_Center);
		UWTAActionButton* JoinAddress = WTAWidgets::MakeButton(Tree, WTAText(TEXT("Join")), NAME_VisitJoinAddress, NAME_None, -1,
			WTAStyle::SecondaryButton(), WTAStyle::Font(13, true), WTAStyle::Bone());
		JoinAddress->OnAction.AddDynamic(this, &UWTAVisitWidget::HandleAction);
		UHorizontalBoxSlot* JoinSlot = AddressRow->AddChildToHorizontalBox(JoinAddress);
		JoinSlot->SetPadding(FMargin(8.f, 0.f, 0.f, 0.f));
		JoinSlot->SetVerticalAlignment(VAlign_Center);
		SoloBox->AddChildToVerticalBox(AddressRow)->SetPadding(FMargin(0.f, 0.f, 0.f, 8.f));
	}

	// --- In a visit: who is here, the addresses, the guide's or the visitor's buttons ---
	InVisitBox = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
	Column->AddChildToVerticalBox(InVisitBox);
	{
		InVisitBox->AddChildToVerticalBox(SectionLabel(Tree, WTAText(TEXT("Who is here"))))->SetPadding(FMargin(0.f, 0.f, 0.f, 8.f));
		PeopleList = Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass());
		InVisitBox->AddChildToVerticalBox(PeopleList)->SetPadding(FMargin(0.f, 0.f, 0.f, 14.f));

		AddressText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(13), WTAStyle::BoneDim(), true);
		InVisitBox->AddChildToVerticalBox(AddressText)->SetPadding(FMargin(0.f, 0.f, 0.f, 16.f));

		UHorizontalBox* Buttons = Tree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
		GatherButton = WTAWidgets::MakeButton(Tree, WTAText(TEXT("Gather everyone here (G)")), NAME_VisitGather, NAME_None, -1,
			WTAStyle::PrimaryButton(), WTAStyle::Font(14, true), WTAStyle::Ink());
		GatherButton->OnAction.AddDynamic(this, &UWTAVisitWidget::HandleAction);
		Buttons->AddChildToHorizontalBox(GatherButton)->SetPadding(FMargin(0.f, 0.f, 8.f, 0.f));
		TourButton = WTAWidgets::MakeButton(Tree, WTAText(TEXT("Start the tour")), NAME_VisitTour, NAME_None, -1,
			WTAStyle::SecondaryButton(), WTAStyle::Font(14), WTAStyle::Bone());
		TourButton->OnAction.AddDynamic(this, &UWTAVisitWidget::HandleAction);
		Buttons->AddChildToHorizontalBox(TourButton)->SetPadding(FMargin(0.f, 0.f, 8.f, 0.f));
		WalkButton = WTAWidgets::MakeButton(Tree, WTAText(TEXT("Walk to the guide (G)")), NAME_VisitWalk, NAME_None, -1,
			WTAStyle::PrimaryButton(), WTAStyle::Font(14, true), WTAStyle::Ink());
		WalkButton->OnAction.AddDynamic(this, &UWTAVisitWidget::HandleAction);
		Buttons->AddChildToHorizontalBox(WalkButton)->SetPadding(FMargin(0.f, 0.f, 8.f, 0.f));
		UHorizontalBoxSlot* Gap = Buttons->AddChildToHorizontalBox(Tree->ConstructWidget<USpacer>(USpacer::StaticClass()));
		Gap->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		LeaveButton = WTAWidgets::MakeButton(Tree, WTAText(TEXT("Leave the visit")), NAME_VisitLeave, NAME_None, -1,
			WTAStyle::SecondaryButton(), WTAStyle::Font(14), WTAStyle::BoneDim());
		LeaveButton->OnAction.AddDynamic(this, &UWTAVisitWidget::HandleAction);
		Buttons->AddChildToHorizontalBox(LeaveButton);
		InVisitBox->AddChildToVerticalBox(Buttons)->SetPadding(FMargin(0.f, 0.f, 0.f, 8.f));
	}

	StatusText = WTAWidgets::MakeText(Tree, FText::GetEmpty(), WTAStyle::Font(13, true), WTAStyle::Brass(), true);
	StatusText->SetVisibility(ESlateVisibility::Collapsed);
	Column->AddChildToVerticalBox(StatusText)->SetPadding(FMargin(0.f, 8.f, 0.f, 0.f));

	UHorizontalBox* Foot = Tree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
	UHorizontalBoxSlot* FootGap = Foot->AddChildToHorizontalBox(Tree->ConstructWidget<USpacer>(USpacer::StaticClass()));
	FootGap->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
	UWTAActionButton* CloseButton = WTAWidgets::MakeButton(Tree, WTAText(TEXT("Close")), NAME_VisitClose, NAME_None, -1,
		WTAStyle::SecondaryButton(), WTAStyle::Font(13), WTAStyle::BoneDim());
	CloseButton->OnAction.AddDynamic(this, &UWTAVisitWidget::HandleAction);
	Foot->AddChildToHorizontalBox(CloseButton);
	Column->AddChildToVerticalBox(Foot)->SetPadding(FMargin(0.f, 18.f, 0.f, 0.f));

	bOpen = false;
	SetVisibility(ESlateVisibility::Collapsed);
}

void UWTAVisitWidget::Open()
{
	UWTAVisitSubsystem* Visit = UWTAVisitSubsystem::Get(this);
	if (Visit != nullptr)
	{
		if (!bBound)
		{
			Visit->OnVisitChanged.AddDynamic(this, &UWTAVisitWidget::HandleVisitChanged);
			bBound = true;
		}
		if (!Visit->IsInVisit())
		{
			Visit->StartSearch();
		}
		if (NameBox != nullptr && NameBox->GetText().IsEmpty())
		{
			NameBox->SetText(FText::FromString(Visit->GetMyName()));
		}
	}
	ListedSignature.Reset();
	PeopleSignature.Reset();
	bOpen = true;
	SetVisibility(ESlateVisibility::Visible);
	Refresh();
}

void UWTAVisitWidget::Close()
{
	if (bOpen)
	{
		CommitName();
	}
	bOpen = false;
	SetVisibility(ESlateVisibility::Collapsed);
	if (UWTAVisitSubsystem* Visit = UWTAVisitSubsystem::Get(this))
	{
		Visit->StopSearch();
	}
}

void UWTAVisitWidget::SetNameText(const FString& Name)
{
	if (NameBox != nullptr)
	{
		NameBox->SetText(FText::FromString(Name));
	}
}

void UWTAVisitWidget::SetAddressText(const FString& Address)
{
	if (AddressBox != nullptr)
	{
		AddressBox->SetText(FText::FromString(Address));
	}
}

void UWTAVisitWidget::CommitName()
{
	UWTAVisitSubsystem* Visit = UWTAVisitSubsystem::Get(this);
	if (Visit != nullptr && NameBox != nullptr)
	{
		const FString Name = NameBox->GetText().ToString().TrimStartAndEnd();
		if (!Name.IsEmpty() && Name != Visit->GetMyName())
		{
			Visit->SetMyName(Name);
		}
	}
}

void UWTAVisitWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	if (!bOpen)
	{
		return;
	}
	SinceRefresh += InDeltaTime;
	if (SinceRefresh >= 0.5f)
	{
		SinceRefresh = 0.f;
		Refresh();
	}
}

void UWTAVisitWidget::HandleVisitChanged()
{
	if (bOpen)
	{
		Refresh();
	}
}

void UWTAVisitWidget::Refresh()
{
	UWTAVisitSubsystem* Visit = UWTAVisitSubsystem::Get(this);
	UWidgetTree* Tree = WidgetTree;
	if (Visit == nullptr || Tree == nullptr || SoloBox == nullptr)
	{
		return;
	}
	const EWTAVisitRole Role = Visit->GetRole();
	const bool bInVisit = Role != EWTAVisitRole::Solo;
	SoloBox->SetVisibility(bInVisit ? ESlateVisibility::Collapsed : ESlateVisibility::SelfHitTestInvisible);
	InVisitBox->SetVisibility(bInVisit ? ESlateVisibility::SelfHitTestInvisible : ESlateVisibility::Collapsed);

	if (Role == EWTAVisitRole::Solo)
	{
		TitleText->SetText(WTAText(TEXT("Visit together")));
		BodyText->SetText(WTAText(TEXT("A guide leads the tour and everyone's computer follows: the same stop, the same story, each of you at your own place round it. Between stops you are free to look around. Everyone needs to be on the same network.")));
		// The visits heard, rebuilt only when they change.
		const TArray<FWTAFoundVisit> Visits = Visit->GetFoundVisits();
		FString Signature;
		for (const FWTAFoundVisit& Found : Visits)
		{
			Signature += Found.Address + Found.GuideName + FString::FromInt(Found.People) + TEXT(";");
		}
		if (Signature != ListedSignature || FoundList->GetChildrenCount() == 0)
		{
			ListedSignature = Signature;
			ListedAddresses.Reset();
			FoundList->ClearChildren();
			if (Visits.Num() == 0)
			{
				UTextBlock* None = WTAWidgets::MakeText(Tree, Visit->IsSearching()
					? WTAText(TEXT("Looking for visits on this network ..."))
					: WTAText(TEXT("This computer cannot listen for visits here. Join by address instead.")),
					WTAStyle::Italic(14), WTAStyle::BoneDim(), true);
				FoundList->AddChildToVerticalBox(None);
			}
			for (int32 i = 0; i < Visits.Num(); ++i)
			{
				const FWTAFoundVisit& Found = Visits[i];
				ListedAddresses.Add(Found.Address);
				UHorizontalBox* Row = Tree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass());
				const FText Line = Found.People == 1
					? FText::Format(WTAText(TEXT("{0}'s visit \u00B7 the guide is waiting")), FText::FromString(Found.GuideName))
					: FText::Format(WTAText(TEXT("{0}'s visit \u00B7 {1} people")), FText::FromString(Found.GuideName), FText::AsNumber(Found.People));
				UTextBlock* Label = WTAWidgets::MakeText(Tree, Line, WTAStyle::Font(14, true), WTAStyle::Bone(), false);
				UHorizontalBoxSlot* LabelSlot = Row->AddChildToHorizontalBox(Label);
				LabelSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
				LabelSlot->SetVerticalAlignment(VAlign_Center);
				UWTAActionButton* Join = WTAWidgets::MakeButton(Tree, WTAText(TEXT("Join")), NAME_VisitJoin, NAME_None, i,
					WTAStyle::PrimaryButton(), WTAStyle::Font(13, true), WTAStyle::Ink());
				Join->OnAction.AddDynamic(this, &UWTAVisitWidget::HandleAction);
				Row->AddChildToHorizontalBox(Join)->SetVerticalAlignment(VAlign_Center);
				FoundList->AddChildToVerticalBox(Row)->SetPadding(FMargin(0.f, 0.f, 0.f, 6.f));
			}
		}
	}
	else
	{
		const FText Guide = FText::FromString(Visit->GetGuideName());
		if (Role == EWTAVisitRole::Guide)
		{
			TitleText->SetText(WTAText(TEXT("You are leading a visit")));
			BodyText->SetText(WTAText(TEXT("Start the tour and everyone follows you from stop to stop. Gather brings the group to wherever you stand.")));
			const TArray<FString> Addresses = Visit->GetLocalAddresses();
			AddressText->SetText(Addresses.Num() > 0
				? FText::Format(WTAText(TEXT("Visitors on this network find your visit on their own Visit together card, or type this computer's address: {0}")), FText::FromString(FString::Join(Addresses, TEXT("  \u00B7  "))))
				: WTAText(TEXT("Visitors on this network find your visit on their own Visit together card.")));
			AddressText->SetVisibility(ESlateVisibility::HitTestInvisible);
			const UWTATourSubsystem* Tour = UWTATourSubsystem::Get(this);
			TourButton->SetVisibility(Tour != nullptr && Tour->IsTouring() ? ESlateVisibility::Collapsed : ESlateVisibility::Visible);
			GatherButton->SetVisibility(ESlateVisibility::Visible);
			WalkButton->SetVisibility(ESlateVisibility::Collapsed);
			WTAWidgets::SetButtonLabel(LeaveButton, WTAText(TEXT("End the visit")));
		}
		else
		{
			TitleText->SetText(Guide.IsEmpty() ? WTAText(TEXT("You are in a visit")) : FText::Format(WTAText(TEXT("You are in {0}'s visit")), Guide));
			BodyText->SetText(WTAText(TEXT("At each stop you walk to your own place round it. Between stops, look around as you like; the next stop brings you back.")));
			AddressText->SetVisibility(ESlateVisibility::Collapsed);
			TourButton->SetVisibility(ESlateVisibility::Collapsed);
			GatherButton->SetVisibility(ESlateVisibility::Collapsed);
			WalkButton->SetVisibility(ESlateVisibility::Visible);
			WTAWidgets::SetButtonLabel(LeaveButton, WTAText(TEXT("Leave the visit")));
		}
		const TArray<FWTAVisitPerson> People = Visit->GetPeople();
		FString Signature;
		for (const FWTAVisitPerson& Person : People)
		{
			Signature += Person.Name + (Person.bGuide ? TEXT("*") : TEXT("")) + TEXT(";");
		}
		if (Signature != PeopleSignature)
		{
			PeopleSignature = Signature;
			PeopleList->ClearChildren();
			for (const FWTAVisitPerson& Person : People)
			{
				PeopleList->AddChildToVerticalBox(PersonRow(Tree, Person))->SetPadding(FMargin(0.f, 0.f, 0.f, 5.f));
			}
			if (People.Num() == 1)
			{
				PeopleList->AddChildToVerticalBox(WTAWidgets::MakeText(Tree, WTAText(TEXT("Nobody has joined yet.")), WTAStyle::Italic(13), WTAStyle::BoneDim(), true));
			}
		}
	}

	const FText Status = Visit->GetStatus();
	StatusText->SetText(Status);
	StatusText->SetVisibility(Status.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
}

void UWTAVisitWidget::HandleAction(FName Action, FName Arg, int32 Index)
{
	UWTAVisitSubsystem* Visit = UWTAVisitSubsystem::Get(this);
	AWTAPlayerController* PC = Cast<AWTAPlayerController>(GetOwningPlayer());
	if (Visit == nullptr)
	{
		return;
	}
	if (Action == NAME_VisitClose)
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
	CommitName();
	if (Action == NAME_VisitLead)
	{
		Visit->LeadVisit();
	}
	else if (Action == NAME_VisitJoin && ListedAddresses.IsValidIndex(Index))
	{
		Visit->JoinVisit(ListedAddresses[Index]);
	}
	else if (Action == NAME_VisitJoinAddress && AddressBox != nullptr)
	{
		const FString Address = AddressBox->GetText().ToString().TrimStartAndEnd();
		if (!Address.IsEmpty())
		{
			Visit->JoinVisit(Address);
		}
	}
	else if (Action == NAME_VisitGather)
	{
		if (PC != nullptr)
		{
			PC->CloseTopPanel();
		}
		Visit->GatherHere();
	}
	else if (Action == NAME_VisitTour)
	{
		if (PC != nullptr)
		{
			PC->CloseTopPanel();
			PC->RunAction(WTAAction::StartTour(), NAME_None);
		}
	}
	else if (Action == NAME_VisitWalk)
	{
		if (PC != nullptr)
		{
			PC->CloseTopPanel();
		}
		Visit->WalkToGuide();
	}
	else if (Action == NAME_VisitLeave)
	{
		Visit->LeaveVisit();
	}
	Refresh();
}
