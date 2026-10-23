// Walk the Archive - the Lost Stories wall: the stories told at the booth, as cards on the board.
//
// Stands against the board the cabin's builder made (bl/stories.py writes where, out/stories/layout.json; the
// editor Python places it), its X axis out from the wall. A widget component draws UWTAStoryBoardWidget on the
// board's face, BoardWidthCm by BoardHeightCm; the subsystem's changes redraw it. E opens every story in the panel
// (UWTAPanelWidget::ShowStories); while one plays, E stops it.

#pragma once

#include "CoreMinimal.h"
#include "World/WTAPickActor.h"
#include "WTAStoryWallActor.generated.h"

class UMaterialInterface;
class UWidgetComponent;
class UWTAStoryBoardWidget;

UCLASS(Blueprintable)
class WALKTHEARCHIVE_API AWTAStoryWallActor : public AWTAPickActor
{
	GENERATED_BODY()

public:
	AWTAStoryWallActor();

	/** The board's face, cm (editor Python: board_width_cm, board_height_cm). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	float BoardWidthCm = 240.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	float BoardHeightCm = 120.f;

	/** The cards are paper lit by the cabin (BoardMaterial): this scales how much light they reflect. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	float Brightness = 0.9f;

	/** The board's material: the lighting step's lit, masked M_WTA_WidgetLit, so the cards are paper under the picture
	    light. The engine's own widget material is unlit at 1 cd/m2, which physical exposure shows black. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	TSoftObjectPtr<UMaterialInterface> BoardMaterial;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	TObjectPtr<UWidgetComponent> Board;

	/** Draws the cards again from the subsystem. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Refresh();

	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 NumCards() const;

	virtual FText GetInteractLabel_Implementation() const override;
	virtual void Interact_Implementation(AWTAPlayerController* Controller) override;

protected:
	virtual void BeginPlay() override;
	virtual void ReadRow() override;

	UFUNCTION()
	void HandleStoriesChanged();

	UPROPERTY(Transient)
	TObjectPtr<UWTAStoryBoardWidget> Face;
};
