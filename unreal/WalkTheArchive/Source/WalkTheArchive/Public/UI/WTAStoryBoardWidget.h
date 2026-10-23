// Walk the Archive - the Lost Stories wall's face: the stories as paper cards, drawn into the world by the story
// wall's widget component (AWTAStoryWallActor). Built in C++ like the panel, no widget asset.
//
// 2048 x 1024 units: a heading ("Stories from this place") over a grid of up to eight cards, four by two. A card is
// the story's byline (teller, date, length), its title (the teller's own, else the first words they said), a few
// words of it in italics, and what pressing E does ("Listen", "Playing", "Being written down"). Stories told this
// visit get a brass edge and a "New" tag. More than eight: the last card says how many more there are. None: one
// card asks for the first.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Systems/WTAStoriesSubsystem.h"
#include "WTAStoryBoardWidget.generated.h"

class UUniformGridPanel;
class UTextBlock;

UCLASS()
class WALKTHEARCHIVE_API UWTAStoryBoardWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** The board's design size; the widget component draws it at this many pixels. */
	static FVector2D DesignSize() { return FVector2D(2048.0, 1024.0); }

	/** Lays the cards out again: Stories newest first, PlayingId the one playing (''), Writing the ones being
	    written down. */
	void ShowStories(const TArray<FWTAStory>& Stories, const FString& PlayingId, const TSet<FString>& Writing);

	/** Cards on the board now (the "more" card and the empty card not counted). */
	int32 NumCards() const { return Cards; }

protected:
	virtual void NativeOnInitialized() override;

	UWidget* MakeCard(const FWTAStory& Story, bool bPlaying, bool bWriting);
	UWidget* MakeNoteCard(const FText& Title, const FText& Body);

	UPROPERTY(Transient) TObjectPtr<UUniformGridPanel> Grid;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> Heading;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> SubHeading;
	int32 Cards = 0;
};
