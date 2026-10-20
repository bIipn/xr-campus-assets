// Walk the Archive - the one modal panel (built in C++, no widget asset).
//
// A dark scrim with a bone card in the middle: kicker / big year / title / italic place header, a scroll box of
// content rows, and a footer with Prev / page label / Next / Close. Show* functions clear the content and rebuild it:
//   ShowExhibit  museum-label card: art, "In this scene" numbered lines (wax scenes), "The story" (description,
//                more), quote, "At a glance" facts (when, where, partners), source chips (Action "Link"),
//                Prev/Next step through the exhibit's list (the 12 wax scenes form a timeline)
//   ShowBook     cover (Page -1: title, subtitle, TOC buttons Action "Page", "Start reading") or page N
//                (heading, blocks Para/List/Quote/Note/Code, "Page N of M", Prev/Next, "Contents" = Page -1)
//   ShowStation  kicker, title, subtitle, numbered steps, intro paragraphs, Close
//   ShowRide     kicker, name, card text, note, Close
//   ShowBadges   every DT_Badges row (name + "Unlocked" or How), token list with hints, "Start over" (Action "Reset")
//   ShowPlaces   every DT_Places row as a GoPlace button (M key)
// Buttons go through HandleAction: internal verbs (Prev, Next, Close, Page, Link, Reset) are handled here, anything
// else is passed to AWTAPlayerController::RunAction. Left/Right arrow keys = Prev/Next, Escape = Close.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Input/Reply.h"
#include "Input/Events.h"
#include "Layout/Geometry.h"
#include "Fonts/SlateFontInfo.h"
#include "Math/Color.h"
#include "UObject/SoftObjectPtr.h"
#include "Data/WTATypes.h"
#include "WTAPanelWidget.generated.h"

class UBorder;
class UHorizontalBox;
class UImage;
class UScrollBox;
class USizeBox;
class UTextBlock;
class UTexture2D;
class UVerticalBox;
class UWTAActionButton;

/** What the panel is showing. */
UENUM(BlueprintType)
enum class EWTAPanelMode : uint8
{
	None,
	Exhibit,
	Book,
	Station,
	Ride,
	Badges,
	Places
};

UCLASS()
class WALKTHEARCHIVE_API UWTAPanelWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Catalog card for DT_Exhibits[ItemId]. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowExhibit(FName ItemId);

	/** Book reader; Page -1 = cover with contents, 0..N-1 = pages. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowBook(FName BookId, int32 Page);

	/** Station panel for DT_Stations[StationId]. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowStation(FName StationId);

	/** Ride card for DT_Rides[RideId]. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowRide(FName RideId);

	/** Badges and token hints. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowBadges();

	/** Places list. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowPlaces();

	/** Hide the panel (does not touch the input mode; the controller does). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Close();

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsOpen() const { return bOpen; }

	UFUNCTION(BlueprintPure, Category = "WTA")
	EWTAPanelMode GetMode() const { return Mode; }

	/** Row id of what is showing (exhibit, book, station, ride) or NAME_None. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FName GetCurrentId() const { return CurrentId; }

	/** Book page showing (-1 cover) when Mode is Book. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 GetCurrentPage() const { return CurrentPage; }

protected:
	virtual void NativeOnInitialized() override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;

	/** All button clicks land here (see the header comment). */
	UFUNCTION()
	void HandleAction(FName Action, FName Arg, int32 Index);

	// --- Content builders (each appends one row to Content) ---

	/** Clear the content, set the header, remember Mode/CurrentId. */
	void BeginCard(EWTAPanelMode NewMode, FName Id, const FText& Kicker, const FText& Title);

	/** Show the footer (Prev/Next visible or not, page label) and make the panel visible. */
	void EndCard(bool bShowPrev, bool bShowNext, const FText& PageLabel);

	UTextBlock* AddText(const FText& Text, const FSlateFontInfo& Font, const FLinearColor& Color);
	void AddHeading(const FText& Text);
	void AddParagraph(const FText& Text);
	void AddQuote(const FText& Quote, const FText& By);
	void AddNote(const FText& Text);
	void AddCode(const FText& Text);
	void AddList(const TArray<FText>& Items);
	void AddBlock(const FWTABookBlock& Block);
	void AddSpacer(float Height);

	/** Loads the soft texture synchronously and adds it at MaxWidth keeping its aspect. Skips unset textures. */
	void AddImage(const TSoftObjectPtr<UTexture2D>& Texture, float MaxWidth);

	/** A button row entry; bPrimary = brass. Bound to HandleAction. */
	UWTAActionButton* AddButton(const FText& Label, FName Action, FName Arg, int32 Index, bool bPrimary);

	/** A clickable source link (Action "Link", Payload = Url). */
	void AddLink(const FText& Label, const FString& Url);

	/** Big year and an italic place line under the title; empty values hide them. */
	void SetHeaderExtras(const FText& Year, const FText& Subtitle);

	/** Small brass section label with a hairline under it ("In this scene", "The story", "Sources"). */
	void AddSection(const FText& Label);

	/** One "at a glance" row: brass label on the left, value on the right. Skips empty values. */
	void AddFact(const FText& Label, const FText& Value);

	/** A wax scene's caption lines as a numbered list. */
	void AddSceneLines(const TArray<FWTAWaxLine>& Lines);

	/** DT_Sources rows as compact chips that wrap (Action "Link", Arg = the source id). */
	void AddSourceChips(const TArray<FName>& SourceIds);

	void SetOpen(bool bNewOpen);

	/** The card's narration clip: "exhibit"/"station"/"ride" and CurrentId, or none when it cannot be read. */
	FName VoiceKind() const;

	/** Shows the Listen button when this card has a clip, labelled for whether it is being read. */
	UFUNCTION()
	void RefreshListenButton();

	UPROPERTY(Transient) TObjectPtr<UBorder> Scrim;
	UPROPERTY(Transient) TObjectPtr<UBorder> Card;
	/** Card width: wide reading cards for exhibits and books, compact for the rest. */
	UPROPERTY(Transient) TObjectPtr<USizeBox> CardSize;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> KickerText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> YearText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> TitleText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> SubtitleText;
	UPROPERTY(Transient) TObjectPtr<UScrollBox> Scroll;
	UPROPERTY(Transient) TObjectPtr<UVerticalBox> Content;
	UPROPERTY(Transient) TObjectPtr<UHorizontalBox> Footer;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> PrevButton;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> NextButton;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> ListenButton;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> CloseButton;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> PageText;

	EWTAPanelMode Mode = EWTAPanelMode::None;
	FName CurrentId;
	int32 CurrentPage = -1;
	int32 NumPages = 0;
	bool bOpen = false;
};
