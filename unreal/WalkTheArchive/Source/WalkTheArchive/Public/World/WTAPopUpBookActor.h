// Walk the Archive - the pop-up books on the Reading Room's south reading table.
//
// bl/popup.py builds every piece as its own mesh, in place and standing open (Unreal spawns them at the origin): for
// each book and spread a backdrop (popup__<book>_s<n>_back: a board on the spine, the scene printed on its reader
// side and the book's cover on the other), the near page's print (_floor) and three paper layers, back to front
// (_l3, _l2, _l1), plus the base they share (popup__base). The actors step hands this actor those meshes (Meshes) and
// the books (Books: the DT_Books row and, for each spread, the page it shows) from out/popup/layout.json.
//
// The actor gives every mesh a movable component and folds the pieces: each turns about its bottom edge on the
// reader's side (its hinge), toward the reader (ReaderDirection). Closed, the backdrop lies on the near page with the
// cover up and the layers are hidden. Opening raises the backdrop and pops the layers up in front of it, back to
// front, each with a little overshoot; closing folds them down ahead of the backdrop, so paper never passes through
// paper. A spot light over the reader's shoulder (BookLight) comes up with the scene, so the layers throw shadows on
// the ones behind them.
//
// E: the first press sits the visitor in the reader's chair (the AWTASeatActor whose SeatId is ReaderSeatId) facing
// the book and captions the spread; after that it opens a closed book, turns the page (the spread folds down and the
// next one pops up) and, after the last spread, closes the book; the next book on the table then shows its cover.
// The table starts with the first book open at its first spread, so it is a display from across the room.
#pragma once

#include "CoreMinimal.h"
#include "World/WTAPickActor.h"
#include "WTAPopUpBookActor.generated.h"

class AWTASeatActor;
class USpotLightComponent;
class UStaticMesh;
class UStaticMeshComponent;

/** One pop-up book: its DT_Books row and, per spread, the page of that book it shows (the caption's heading). */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAPopUpBook
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FName BookId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	TArray<int32> Pages;
};

UENUM(BlueprintType)
enum class EWTAPopUpState : uint8
{
	Closed,
	Opening,
	Open,
	Closing
};

UCLASS(Blueprintable)
class WALKTHEARCHIVE_API AWTAPopUpBookActor : public AWTAPickActor
{
	GENERATED_BODY()

public:
	AWTAPopUpBookActor();

	/** Every popup__ mesh (editor Python: meshes). Names say what each is: popup__base, popup__<book>_s<n>_back,
	    _floor, _l1 (front), _l2, _l3 (back); <book> is the DT_Books row with '-' as '_'. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	TArray<TObjectPtr<UStaticMesh>> Meshes;

	/** The books, in the order the table offers them (editor Python: books). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	TArray<FWTAPopUpBook> Books;

	/** Toward the reader, flat (editor Python: reader_direction). The pieces fold this way to close. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FVector ReaderDirection = FVector(0.f, 1.f, 0.f);

	/** The chair in front of the book (editor Python: reader_seat_id). None or no such seat: E never sits anyone. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FName ReaderSeatId = TEXT("lib10");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	float OpenSeconds = 1.6f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	float CloseSeconds = 0.9f;

	/** How long a spread's caption stays up. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	float CaptionSeconds = 9.f;

	/** The table starts with the first book open (a display); false starts it closed. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	bool bStartOpen = true;

	/** The light on the open scene, candelas at full; it is off while the book is closed or nobody is near. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	float BookLightIntensity = 260.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FLinearColor BookLightColor = FLinearColor(1.f, 0.9f, 0.78f);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	TObjectPtr<USpotLightComponent> BookLight;

	/** Open the book at its current spread (a closed book only). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Open();

	/** Fold this spread down and open the next one (an open book that has one). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void TurnPage();

	/** Close the book; the next book's cover then lies on the table. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Close();

	/** What E does once the visitor is in the chair: open, turn the page, or close after the last spread. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Advance();

	UFUNCTION(BlueprintPure, Category = "WTA")
	EWTAPopUpState GetState() const { return State; }

	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 GetBookIndex() const { return BookIndex; }

	UFUNCTION(BlueprintPure, Category = "WTA")
	FName GetBookId() const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 NumBooks() const { return Spreads.Num(); }

	/** The spread showing (0 = the first). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 GetSpread() const { return SpreadIndex; }

	/** Spreads in the current book. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 NumSpreads() const;

	/** Spreads in every book on the table. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 TotalSpreads() const;

	/** Meshes that became pieces (0: nothing to show; the log says why). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 NumPieces() const { return PieceComponents.Num(); }

	/** The caption of the spread showing: its page's heading and first sentence. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FText GetCaption() const;

	/** True when the local player sits in the reader's chair (or there is no chair to sit in). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsReaderSeated() const;

	/** The backdrop's fold now, degrees (0 standing, 90 closed). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	float GetBackdropAngle() const { return BackAngle; }

	/** The book light's brightness now, 0..1. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	float GetLightLevel() const { return LightLevel; }

	/** Where the open scene's middle is (the light aims there). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FVector GetSceneCentre() const;

	/** Where the reader's eye goes on sitting down: low on the scene, so the whole of it and the printed page sit
	    above the HUD's caption. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FVector GetReaderLookAt() const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	FString Describe() const;

	virtual FText GetInteractLabel_Implementation() const override;
	virtual void Interact_Implementation(AWTAPlayerController* Controller) override;
	virtual void Tick(float DeltaSeconds) override;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void ReadRow() override;

	/** One mesh as a piece: its component and, for the ones that fold, the hinge and its size. */
	struct FPiece
	{
		int32 Comp = INDEX_NONE;
		FVector Hinge = FVector::ZeroVector;
		float Height = 0.f;          // cm, bottom to top standing
		float Thickness = 0.f;       // cm along the reader direction (a layer's pieces step toward the reader)
		float FromSpine = 0.f;       // cm from the backdrop's hinge toward the reader
		bool IsValid() const { return Comp != INDEX_NONE; }
	};

	struct FSpread
	{
		FPiece Back;
		FPiece Floor;
		FPiece Layers[3];            // l1 (front), l2, l3 (back)
	};

	void BuildPieces();
	void ShowSpread(int32 Book, int32 Spread);
	void Pose(float BackDeg, const float LayerDeg[3]);
	void StartAnimation(EWTAPopUpState NewState);
	void FinishAnimation();
	void ShowSpreadCaption();
	void HideCaption();
	void CheckPlayerNear();
	void UpdateLight(float DeltaSeconds);
	float LightTarget() const;
	void PlaceLight();
	void NoteSpreadRead() const;
	FText BookTitle(int32 Book) const;
	UStaticMeshComponent* PieceComp(const FPiece& Piece) const;
	AWTASeatActor* FindReaderSeat() const;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> PieceComponents;

	TArray<TArray<FSpread>> Spreads;   // [book][spread]; books without a single whole spread are left out
	TArray<int32> BookOfSpreads;       // Spreads[i] is Books[BookOfSpreads[i]]
	int32 BaseComp = INDEX_NONE;
	FVector SceneCentre = FVector::ZeroVector;
	float PageZ = 0.f;                 // the near page's surface (the base's top)
	bool bHaveScene = false;

	EWTAPopUpState State = EWTAPopUpState::Closed;
	int32 BookIndex = 0;
	int32 SpreadIndex = 0;
	int32 ShownBook = INDEX_NONE;
	int32 ShownSpread = INDEX_NONE;
	float Phase = 0.f;                 // 0..1 through the animation running
	bool bTurnAfterClose = false;      // the closing running is a page turn: the next spread opens after it
	bool bTurning = false;             // a page turn is under way (its closing and its opening): the light only dips
	bool bPendingPress = false;        // E pressed while the paper moved: done when it stops
	float BackAngle = 90.f;
	float LayerAngles[3] = { 90.f, 90.f, 90.f };
	float LightLevel = 0.f;
	bool bPlayerNear = true;
	bool bCaptionUp = false;
	FVector Reader = FVector(0.f, 1.f, 0.f);
	FVector FoldAxis = FVector(-1.f, 0.f, 0.f);
	FTimerHandle CaptionTimer;
	FTimerHandle NearTimer;
	mutable TWeakObjectPtr<AWTASeatActor> ReaderSeat;
	mutable bool bSeatLooked = false;
};
