// Walk the Archive - the one modal panel (built in C++, no widget asset).
//
// A dark scrim with a bone card in the middle: kicker + title header, a scroll box of content rows, and a footer
// with Prev / page label / Next / Close. Show* functions clear the content and rebuild it from the tables:
//   ShowExhibit  art image, kind, title, date, description, more, quote + quote-by, where, partners, source links
//                (Action "Link", Payload = url), Prev/Next step through the exhibit's list
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

	void SetOpen(bool bNewOpen);

	UPROPERTY(Transient) TObjectPtr<UBorder> Scrim;
	UPROPERTY(Transient) TObjectPtr<UBorder> Card;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> KickerText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> TitleText;
	UPROPERTY(Transient) TObjectPtr<UScrollBox> Scroll;
	UPROPERTY(Transient) TObjectPtr<UVerticalBox> Content;
	UPROPERTY(Transient) TObjectPtr<UHorizontalBox> Footer;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> PrevButton;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> NextButton;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> CloseButton;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> PageText;

	EWTAPanelMode Mode = EWTAPanelMode::None;
	FName CurrentId;
	int32 CurrentPage = -1;
	int32 NumPages = 0;
	bool bOpen = false;
};
