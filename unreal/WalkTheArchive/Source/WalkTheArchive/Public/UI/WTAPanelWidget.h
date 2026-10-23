// Walk the Archive - the one modal panel (built in C++, no widget asset).
//
// A dark scrim with a bone card in the middle: kicker / big year / title / italic place header, a scroll box of
// content rows, and a footer with Prev / page label / Next / Close. Show* functions clear the content and rebuild it:
//   ShowExhibit  museum-label card: art, "In this scene" numbered lines (wax scenes), "The story" (description,
//                more), quote, "At a glance" facts (when, where, partners), source chips (Action "Link"),
//                Prev/Next step through the exhibit's list (the 12 wax scenes form a timeline)
//   ShowBook     cover (Page -1: title, subtitle, TOC buttons Action "Page", "Start reading") or page N
//                (heading, blocks Para/List/Quote/Note/Code, "Page N of M", Prev/Next, "Contents" = Page -1)
//   ShowStation  kicker, title, subtitle, the intro paragraphs, the numbered steps (ticked once finished) and "Start"
//                (Action "StationStep" 1); ShowStationStep walks the steps one card at a time (title, its paragraph read
//                aloud as VO_station_<id>_<nn>, Back / Next step), the last one's "Finish" (Action "StationFinish")
//                notes the station finished (UWTAProgressSubsystem: badge, remembered) and returns to the overview
//   ShowRide     kicker, name, card text, note, Close
//   ShowBadges   every DT_Badges row (name + "Unlocked" or How), token list with hints, "Start over" (Action "Reset")
//   ShowPlaces   every DT_Places row as a GoPlace button (M key)
//   ShowCourse   a course (DT_Talks kind course): the lead's welcome read aloud, its stations as a checklist ticked
//                from the progress with a Go button each (Action "OpenStation"), "Take the quiz" (Action "OpenQuiz")
//                once all are finished, "Certified" once passed
//   ShowHunt     the token hunt's library card: a stamp per token, the hints still open, a picture to show at the desk
//   ShowQuiz     a class's quiz (DT_Talks), one question at a time: the options as buttons (Action "Answer"), then
//                the right answer marked and why, "Next question"; the result card scores it and, when passed, asks
//                for a name and makes the certificate (Action "Certificate" -> AWTAPlayerController::ShowCertificate)
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
class UEditableTextBox;

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
	Places,
	Quiz,
	Course,
	Hunt
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

	/** Station panel for DT_Stations[StationId]: the overview with its steps and Start. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowStation(FName StationId);

	/** One step of a station (1-based; 0 shows the overview): its title and paragraph, read aloud when there is a clip. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowStationStep(FName StationId, int32 Step);

	/** Ride card for DT_Rides[RideId]. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowRide(FName RideId);

	/** Badges and token hints. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowBadges();

	/** Places list. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowPlaces();

	/** A class's quiz from its first question (DT_Talks[TalkId].Quiz); earlier answers are forgotten. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowQuiz(FName TalkId);

	/** A course's card (DT_Talks[TalkId] of kind course): the lead's welcome, the stations as a checklist with a Go
	    button each (Action "OpenStation"), and "Take the quiz" (Action "OpenQuiz") once every station is finished. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowCourse(FName TalkId);

	/** The token hunt's library card: one round stamp per DT_Tokens row (brass once found), the hints of the ones
	    still hiding, and with every token found "show this at the desk" and a Save a picture button. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void ShowHunt();

	/** Question Index of the quiz: unanswered (Chosen -1) as option buttons, else marked with the right answer and why. */
	void ShowQuizQuestion(FName TalkId, int32 Index, int32 Chosen);

	/** The score, and the name box and certificate button when it is a pass. */
	void ShowQuizResult(FName TalkId);

	/** Right answers given so far. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 QuizScore() const;

	/** The name typed for the certificate (the result card), trimmed; empty when none. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FString QuizName() const;

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

	/** The card's title as shown. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FText GetTitle() const;

	/** Book page showing (-1 cover) when Mode is Book; stations finished on a course card; stamps on the library card. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 GetCurrentPage() const { return CurrentPage; }

	/** Pages of a book; stations of a course; tokens on the library card. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 GetNumPages() const { return NumPages; }

protected:
	friend class UWTAPlayTest;

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
	void AddImage(UTexture2D* Loaded, float MaxWidth);

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

	/** One checklist line (green and bold when done) with, when ButtonLabel is set, a compact button at its right
	    end bound to HandleAction (the course card's stations: "Go" opens the station). */
	void AddChecklistRow(const FText& Line, bool bDone, const FText& ButtonLabel, FName Action, FName Arg);

	/** DT_Sources rows as compact chips that wrap (Action "Link", Arg = the source id). */
	void AddSourceChips(const TArray<FName>& SourceIds);

	void SetOpen(bool bNewOpen);

	/** The card's narration clip: "exhibit"/"station"/"ride" and CurrentId, "quiz" and the question's clip, or none. */
	FName VoiceKind() const;
	FName VoiceId() const;

	/** Shows the Listen button when this card has a clip, labelled for whether it is being read. */
	UFUNCTION()
	void RefreshListenButton();

	/** HuntPicture: the toast after the screenshot of the card has been taken. */
	void HuntPictureSaved();
	FTimerHandle HuntPictureTimer;
	FString HuntPictureFile;

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
	/** The quiz result card's name box (null outside it). */
	UPROPERTY(Transient) TObjectPtr<UEditableTextBox> NameBox;
	/** The quiz: the answer chosen per question (-1 = not yet). */
	TArray<int32> QuizAnswers;

	EWTAPanelMode Mode = EWTAPanelMode::None;
	FName CurrentId;
	int32 CurrentPage = -1;
	int32 NumPages = 0;
	bool bOpen = false;
};
