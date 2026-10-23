// Walk the Archive - the pop-up books on the Reading Room's south reading table.

#include "World/WTAPopUpBookActor.h"
#include "Components/BoxComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Core/WTACharacter.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "Core/WTAText.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "Systems/WTAContentSubsystem.h"
#include "Systems/WTAProgressSubsystem.h"
#include "Systems/WTAVisitLogSubsystem.h"
#include "TimerManager.h"
#include "World/WTAAttractComponent.h"
#include "World/WTASeatActor.h"

// Unity builds put several of these files into one: every helper here has a name of its own.
namespace
{
	// When each layer moves, as fractions of the animation: l1 (front), l2, l3 (back). Opening, the backdrop stands
	// up over the first half and the layers pop up behind it, back first; closing, the front layer folds first and
	// the backdrop comes down last, so every piece leans at least as far as the one behind it.
	constexpr float PopUpOpenBackEnd = 0.5f;
	constexpr float PopUpOpenDelay[3] = { 0.48f, 0.38f, 0.28f };
	constexpr float PopUpOpenSpan = 0.48f;
	constexpr float PopUpCloseDelay[3] = { 0.0f, 0.08f, 0.16f };
	constexpr float PopUpCloseSpan = 0.42f;
	constexpr float PopUpCloseBackStart = 0.2f;
	constexpr float PopUpHideLayersAt = 88.f;     // the backdrop this far down covers the layers lying under it
	constexpr float PopUpNearCm = 2500.f;         // the light is off with nobody nearer than this

	float PopUpEaseInOut(float T)
	{
		T = FMath::Clamp(T, 0.f, 1.f);
		return T < 0.5f ? 4.f * T * T * T : 1.f - FMath::Pow(-2.f * T + 2.f, 3.f) * 0.5f;
	}

	/** Ease out past the end and back (about 5 %): the card's snap as it comes upright. */
	float PopUpEaseOutBack(float T)
	{
		T = FMath::Clamp(T, 0.f, 1.f);
		constexpr float C1 = 1.2f;
		constexpr float C3 = C1 + 1.f;
		const float U = T - 1.f;
		return 1.f + C3 * U * U * U + C1 * U * U;
	}

	/** A piece folded AngleDeg about the axis through Hinge (toward the reader for positive angles), its thickness
	    along the reader direction squashed toward the hinge by Squash (1 = none). The mesh's vertices are in world
	    space, so world = Q * (S * (p - Hinge)) + Hinge, which is the transform (Q, Hinge - Q * (S * Hinge), S). */
	FTransform PopUpFold(const FVector& Hinge, const FVector& Axis, const FVector& ReaderDir, float AngleDeg, float Squash)
	{
		const FQuat Q(Axis, FMath::DegreesToRadians(AngleDeg));
		const FVector S = FVector::OneVector - (1.0 - Squash) * ReaderDir.GetAbs();
		return FTransform(Q, Hinge - Q.RotateVector(S * Hinge), S);
	}

	/** The least a layer may lean (degrees toward the reader) while the backdrop leans BackDeg. A layer that leans at
	    least as far as the backdrop never meets it above the page; one that leans less (still rising, or snapping
	    past upright) is fine while its top, seen from the spine, stays a degree in front of the backdrop. FromSpine
	    is the layer's back face's distance from the spine. */
	float PopUpClearOfBackdrop(float LayerDeg, float BackDeg, float FromSpine, float Height)
	{
		if (LayerDeg >= BackDeg)
		{
			return LayerDeg;
		}
		const float Rad = FMath::DegreesToRadians(LayerDeg);
		const float Top = FMath::RadiansToDegrees(FMath::Atan2(FromSpine + Height * FMath::Sin(Rad), Height * FMath::Cos(Rad)));
		return Top >= BackDeg + 1.f ? LayerDeg : BackDeg;
	}

	/** The meshes' name for a book: the DT_Books row with anything but letters, digits and '_' as '_' (as
	    prepare_for_unreal.py cleans names). */
	FString PopUpMeshKey(const FName& BookId)
	{
		FString Key = BookId.ToString();
		for (int32 i = 0; i < Key.Len(); ++i)
		{
			if (!FChar::IsAlnum(Key[i]) && Key[i] != TEXT('_'))
			{
				Key[i] = TEXT('_');
			}
		}
		return Key;
	}

	/** The first sentence of a text, at most about MaxChars (cut at a space, with an ellipsis). */
	FString PopUpFirstSentence(const FString& Text, int32 MaxChars)
	{
		FString S = Text.TrimStartAndEnd();
		for (int32 i = 12; i + 1 < S.Len(); ++i)
		{
			const TCHAR C = S[i];
			if ((C == TEXT('.') || C == TEXT('?') || C == TEXT('!')) && FChar::IsWhitespace(S[i + 1]))
			{
				S.LeftInline(i + 1);
				break;
			}
		}
		if (S.Len() > MaxChars)
		{
			S.LeftInline(MaxChars);
			int32 Space = INDEX_NONE;
			if (S.FindLastChar(TEXT(' '), Space) && Space > MaxChars / 2)
			{
				S.LeftInline(Space);
			}
			S += TEXT("…");
		}
		return S;
	}
}

AWTAPopUpBookActor::AWTAPopUpBookActor()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = false;
	PickExtent = FVector(30.f, 18.f, 16.f);

	// Over the reader's shoulder, aimed at the scene (PlaceLight puts it there): the layers' shadows on the ones
	// behind them are what make the paper read as a stage.
	BookLight = CreateDefaultSubobject<USpotLightComponent>(TEXT("BookLight"));
	BookLight->SetupAttachment(RootComponent);
	BookLight->SetMobility(EComponentMobility::Movable);
	BookLight->SetIntensityUnits(ELightUnits::Candelas);
	BookLight->SetIntensity(0.f);
	BookLight->SetAttenuationRadius(240.f);
	BookLight->SetInnerConeAngle(16.f);
	BookLight->SetOuterConeAngle(30.f);
	BookLight->SetSourceRadius(3.f);
	BookLight->SetSoftSourceRadius(6.f);
	BookLight->SetCastShadows(true);
	BookLight->SetVisibility(false);

	// A book on a table does not call people over with a picture light: the open scene and its own light do.
	if (Attract != nullptr)
	{
		Attract->bEnabled = false;
	}
}

void AWTAPopUpBookActor::BeginPlay()
{
	BuildPieces();
	Super::BeginPlay();   // reads the label and the view spot (they need the scene's middle)

	if (Spreads.Num() > 0)
	{
		BookIndex = 0;
		SpreadIndex = 0;
		ShowSpread(0, 0);
		const float Up[3] = { 0.f, 0.f, 0.f };
		const float Down[3] = { 90.f, 90.f, 90.f };
		State = bStartOpen ? EWTAPopUpState::Open : EWTAPopUpState::Closed;
		Pose(bStartOpen ? 0.f : 90.f, bStartOpen ? Up : Down);
		LightLevel = bStartOpen ? 1.f : 0.f;
	}
	PlaceLight();
	CheckPlayerNear();
	UpdateLight(0.f);
	SetActorTickEnabled(false);
	GetWorldTimerManager().SetTimer(NearTimer, this, &AWTAPopUpBookActor::CheckPlayerNear, 0.5f, true);
	UE_LOG(LogWTA, Display, TEXT("WTA_POPUP %s"), *Describe());
}

void AWTAPopUpBookActor::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	GetWorldTimerManager().ClearTimer(NearTimer);
	HideCaption();
	Super::EndPlay(EndPlayReason);
}

UStaticMeshComponent* AWTAPopUpBookActor::PieceComp(const FPiece& Piece) const
{
	return PieceComponents.IsValidIndex(Piece.Comp) ? PieceComponents[Piece.Comp].Get() : nullptr;
}

void AWTAPopUpBookActor::BuildPieces()
{
	for (UStaticMeshComponent* Old : PieceComponents)
	{
		if (Old != nullptr)
		{
			Old->DestroyComponent();
		}
	}
	PieceComponents.Reset();
	Spreads.Reset();
	BookOfSpreads.Reset();
	BaseComp = INDEX_NONE;

	Reader = FVector(ReaderDirection.X, ReaderDirection.Y, 0.f).GetSafeNormal();
	if (Reader.IsNearlyZero())
	{
		Reader = FVector(0.f, 1.f, 0.f);
	}
	FoldAxis = FVector::UpVector ^ Reader;   // a positive turn about it brings a standing piece's top toward the reader

	// The scene's middle: over the pages, a little above the paper (the chair looks there, the light aims there).
	FBox All(ForceInit);
	for (const UStaticMesh* Mesh : Meshes)
	{
		if (Mesh != nullptr)
		{
			All += Mesh->GetBoundingBox();
		}
	}
	bHaveScene = All.IsValid != 0;
	SceneCentre = bHaveScene ? FVector(All.GetCenter().X, All.GetCenter().Y, All.Min.Z + 0.4 * (All.Max.Z - All.Min.Z)) : GetActorLocation();
	PageZ = bHaveScene ? static_cast<float>(All.Min.Z) + 1.6f : static_cast<float>(GetActorLocation().Z);

	auto MakeComp = [this](UStaticMesh* Mesh) -> int32
	{
		UStaticMeshComponent* Comp = NewObject<UStaticMeshComponent>(this, MakeUniqueObjectName(this, UStaticMeshComponent::StaticClass(), Mesh->GetFName()));
		Comp->SetMobility(EComponentMobility::Movable);
		Comp->SetupAttachment(GetRootComponent());
		Comp->SetUsingAbsoluteLocation(true);
		Comp->SetUsingAbsoluteRotation(true);
		Comp->SetUsingAbsoluteScale(true);
		Comp->SetStaticMesh(Mesh);
		Comp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Comp->SetGenerateOverlapEvents(false);
		Comp->SetCanEverAffectNavigation(false);
		Comp->RegisterComponent();
		Comp->SetWorldTransform(FTransform::Identity);   // the vertices are where the builder put them
		return PieceComponents.Add(Comp);
	};
	auto MakePiece = [&](UStaticMesh* Mesh) -> FPiece
	{
		FPiece Piece;
		Piece.Comp = MakeComp(Mesh);
		const FBox Box = Mesh->GetBoundingBox();
		const FVector C = Box.GetCenter();
		const FVector E = Box.GetExtent();
		const double Front = FMath::Abs(Reader.X) * E.X + FMath::Abs(Reader.Y) * E.Y;
		// The hinge: the bottom edge on the reader's side, so nothing of the piece swings below it as it folds.
		Piece.Hinge = FVector(C.X, C.Y, Box.Min.Z) + Reader * Front;
		Piece.Height = static_cast<float>(Box.Max.Z - Box.Min.Z);
		Piece.Thickness = static_cast<float>(2.0 * Front);
		return Piece;
	};

	// popup__base, popup__<book>_s<n>_<back|floor|l1|l2|l3>
	TMap<FString, TMap<int32, TMap<FString, UStaticMesh*>>> Parts;
	UStaticMesh* BaseMesh = nullptr;
	int32 Unknown = 0;
	for (UStaticMesh* Mesh : Meshes)
	{
		if (Mesh == nullptr)
		{
			continue;
		}
		FString Name = Mesh->GetName();
		if (!Name.RemoveFromStart(TEXT("popup__")))
		{
			++Unknown;
			continue;
		}
		if (Name == TEXT("base"))
		{
			BaseMesh = Mesh;
			continue;
		}
		TArray<FString> Tokens;
		Name.ParseIntoArray(Tokens, TEXT("_"));
		if (Tokens.Num() < 3 || !Tokens[Tokens.Num() - 2].StartsWith(TEXT("s")) || !Tokens[Tokens.Num() - 2].Mid(1).IsNumeric())
		{
			++Unknown;
			continue;
		}
		const FString Part = Tokens.Last();
		const int32 Spread = FCString::Atoi(*Tokens[Tokens.Num() - 2].Mid(1));
		Tokens.SetNum(Tokens.Num() - 2);
		Parts.FindOrAdd(FString::Join(Tokens, TEXT("_"))).FindOrAdd(Spread).Add(Part, Mesh);
	}
	if (BaseMesh != nullptr)
	{
		BaseComp = MakeComp(BaseMesh);
		PageZ = static_cast<float>(BaseMesh->GetBoundingBox().Max.Z);
	}

	static const TCHAR* LayerNames[3] = { TEXT("l1"), TEXT("l2"), TEXT("l3") };
	for (int32 B = 0; B < Books.Num(); ++B)
	{
		const TMap<int32, TMap<FString, UStaticMesh*>>* BookParts = Parts.Find(PopUpMeshKey(Books[B].BookId));
		if (BookParts == nullptr)
		{
			UE_LOG(LogWTA, Warning, TEXT("WTA_POPUP %s: no popup__%s_s<n>_* meshes; the book is left out"), *GetName(), *PopUpMeshKey(Books[B].BookId));
			continue;
		}
		TArray<FSpread> List;
		for (int32 N = 0; ; ++N)
		{
			const TMap<FString, UStaticMesh*>* Pieces = BookParts->Find(N);
			UStaticMesh* const* Back = Pieces != nullptr ? Pieces->Find(TEXT("back")) : nullptr;
			if (Back == nullptr || *Back == nullptr)
			{
				break;
			}
			FSpread Spread;
			Spread.Back = MakePiece(*Back);
			if (UStaticMesh* const* Floor = Pieces->Find(TEXT("floor")))
			{
				Spread.Floor = MakePiece(*Floor);
			}
			for (int32 K = 0; K < 3; ++K)
			{
				if (UStaticMesh* const* Layer = Pieces->Find(LayerNames[K]))
				{
					FPiece& Piece = Spread.Layers[K];
					Piece = MakePiece(*Layer);
					Piece.FromSpine = static_cast<float>((Piece.Hinge - Spread.Back.Hinge) | Reader);
				}
			}
			List.Add(Spread);
		}
		if (List.Num() == 0)
		{
			UE_LOG(LogWTA, Warning, TEXT("WTA_POPUP %s: book %s has no spread with a backdrop; it is left out"), *GetName(), *Books[B].BookId.ToString());
			continue;
		}
		Spreads.Add(MoveTemp(List));
		BookOfSpreads.Add(B);
	}
	// Every spread starts hidden; ShowSpread shows one.
	for (int32 i = 0; i < PieceComponents.Num(); ++i)
	{
		if (i != BaseComp && PieceComponents[i] != nullptr)
		{
			PieceComponents[i]->SetVisibility(false);
		}
	}
	ShownBook = INDEX_NONE;
	ShownSpread = INDEX_NONE;
	if (Unknown > 0)
	{
		UE_LOG(LogWTA, Warning, TEXT("WTA_POPUP %s: %d meshes with names it does not know were left out"), *GetName(), Unknown);
	}
	if (Spreads.Num() == 0)
	{
		UE_LOG(LogWTA, Warning, TEXT("WTA_POPUP %s: nothing to show (%d meshes, %d books): run the actors step after import_meshes has the PopUp asset"),
			*GetName(), Meshes.Num(), Books.Num());
	}
}

void AWTAPopUpBookActor::ShowSpread(int32 Book, int32 Spread)
{
	// Hiding hides every piece; showing shows the backdrop and the near page, and Pose decides about the layers.
	auto SetShown = [this](int32 B, int32 S, bool bShow)
	{
		if (!Spreads.IsValidIndex(B) || !Spreads[B].IsValidIndex(S))
		{
			return;
		}
		const FSpread& Pieces = Spreads[B][S];
		const FPiece* All[5] = { &Pieces.Back, &Pieces.Floor, &Pieces.Layers[0], &Pieces.Layers[1], &Pieces.Layers[2] };
		for (int32 i = 0; i < 5; ++i)
		{
			UStaticMeshComponent* Comp = PieceComp(*All[i]);
			if (Comp != nullptr && (!bShow || i < 2))
			{
				Comp->SetVisibility(bShow);
			}
		}
	};
	if (ShownBook != Book || ShownSpread != Spread)
	{
		SetShown(ShownBook, ShownSpread, false);
	}
	SetShown(Book, Spread, true);
	ShownBook = Book;
	ShownSpread = Spread;
}

void AWTAPopUpBookActor::Pose(float BackDeg, const float LayerDeg[3])
{
	BackAngle = BackDeg;
	if (!Spreads.IsValidIndex(ShownBook) || !Spreads[ShownBook].IsValidIndex(ShownSpread))
	{
		return;
	}
	const FSpread& Spread = Spreads[ShownBook][ShownSpread];
	if (UStaticMeshComponent* Back = PieceComp(Spread.Back))
	{
		Back->SetWorldTransform(PopUpFold(Spread.Back.Hinge, FoldAxis, Reader, BackDeg, 1.f));
	}
	// Lying under a backdrop that is all but down, the layers cannot be seen: hidden, they cannot show through it.
	const bool bLayers = BackDeg < PopUpHideLayersAt;
	for (int32 K = 0; K < 3; ++K)
	{
		const FPiece& Piece = Spread.Layers[K];
		UStaticMeshComponent* Comp = PieceComp(Piece);
		if (Comp == nullptr)
		{
			continue;
		}
		const float Deg = PopUpClearOfBackdrop(FMath::Clamp(LayerDeg[K], -20.f, 90.f), BackDeg, Piece.FromSpine - Piece.Thickness, Piece.Height);
		LayerAngles[K] = Deg;
		// A layer's pieces step toward the reader so none hides another; lying down, that stack squashes flat.
		const float Squash = FMath::Lerp(1.f, 0.2f, FMath::SmoothStep(60.f, 90.f, Deg));
		Comp->SetWorldTransform(PopUpFold(Piece.Hinge, FoldAxis, Reader, Deg, Squash));
		Comp->SetVisibility(bLayers);
	}
}

void AWTAPopUpBookActor::StartAnimation(EWTAPopUpState NewState)
{
	State = NewState;
	Phase = 0.f;
	SetActorTickEnabled(true);
}

void AWTAPopUpBookActor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (State == EWTAPopUpState::Opening || State == EWTAPopUpState::Closing)
	{
		const bool bOpening = State == EWTAPopUpState::Opening;
		Phase = FMath::Min(1.f, Phase + DeltaSeconds / FMath::Max(0.05f, bOpening ? OpenSeconds : CloseSeconds));
		float LayerDeg[3];   // (AActor has a Layers of its own)
		float Back;
		if (bOpening)
		{
			Back = 90.f * (1.f - PopUpEaseInOut(Phase / PopUpOpenBackEnd));
			for (int32 K = 0; K < 3; ++K)
			{
				LayerDeg[K] = 90.f * (1.f - PopUpEaseOutBack((Phase - PopUpOpenDelay[K]) / PopUpOpenSpan));
			}
		}
		else
		{
			Back = 90.f * PopUpEaseInOut((Phase - PopUpCloseBackStart) / (1.f - PopUpCloseBackStart));
			for (int32 K = 0; K < 3; ++K)
			{
				LayerDeg[K] = 90.f * PopUpEaseInOut((Phase - PopUpCloseDelay[K]) / PopUpCloseSpan);
			}
		}
		Pose(Back, LayerDeg);
		if (Phase >= 1.f)
		{
			FinishAnimation();
		}
	}
	UpdateLight(DeltaSeconds);
	const bool bMoving = State == EWTAPopUpState::Opening || State == EWTAPopUpState::Closing;
	if (!bMoving && FMath::IsNearlyEqual(LightLevel, LightTarget(), 0.002f))
	{
		SetActorTickEnabled(false);
	}
}

void AWTAPopUpBookActor::FinishAnimation()
{
	const float Up[3] = { 0.f, 0.f, 0.f };
	const float Down[3] = { 90.f, 90.f, 90.f };
	if (State == EWTAPopUpState::Opening)
	{
		State = EWTAPopUpState::Open;
		Pose(0.f, Up);
		bTurning = false;
	}
	else if (State == EWTAPopUpState::Closing)
	{
		Pose(90.f, Down);
		if (bTurnAfterClose && Spreads.IsValidIndex(BookIndex) && Spreads[BookIndex].IsValidIndex(SpreadIndex + 1))
		{
			// A page turned: the next spread lies where this one closed, and opens.
			bTurnAfterClose = false;
			++SpreadIndex;
			ShowSpread(BookIndex, SpreadIndex);
			Pose(90.f, Down);
			StartAnimation(EWTAPopUpState::Opening);
			ShowSpreadCaption();
			NoteSpreadRead();
			return;
		}
		// The book is shut: the next one on the table shows its cover.
		bTurnAfterClose = false;
		bTurning = false;
		State = EWTAPopUpState::Closed;
		if (Spreads.Num() > 0)
		{
			BookIndex = (BookIndex + 1) % Spreads.Num();
			SpreadIndex = 0;
			ShowSpread(BookIndex, 0);
			Pose(90.f, Down);
		}
	}
	if (bPendingPress)
	{
		bPendingPress = false;
		Advance();
	}
}

void AWTAPopUpBookActor::Open()
{
	if (State != EWTAPopUpState::Closed || !Spreads.IsValidIndex(BookIndex))
	{
		return;
	}
	ShowSpread(BookIndex, SpreadIndex);
	bTurnAfterClose = false;
	bTurning = false;
	StartAnimation(EWTAPopUpState::Opening);
	ShowSpreadCaption();
	NoteSpreadRead();
}

void AWTAPopUpBookActor::TurnPage()
{
	if (State != EWTAPopUpState::Open || !Spreads.IsValidIndex(BookIndex) || !Spreads[BookIndex].IsValidIndex(SpreadIndex + 1))
	{
		return;
	}
	bTurnAfterClose = true;
	bTurning = true;
	HideCaption();
	StartAnimation(EWTAPopUpState::Closing);
}

void AWTAPopUpBookActor::Close()
{
	if (State != EWTAPopUpState::Open)
	{
		return;
	}
	bTurnAfterClose = false;
	bTurning = false;
	HideCaption();
	StartAnimation(EWTAPopUpState::Closing);
}

void AWTAPopUpBookActor::Advance()
{
	switch (State)
	{
	case EWTAPopUpState::Closed:
		Open();
		break;
	case EWTAPopUpState::Open:
		if (SpreadIndex + 1 < NumSpreads())
		{
			TurnPage();
		}
		else
		{
			Close();
		}
		break;
	default:
		bPendingPress = true;   // the paper is moving: once it stops
		break;
	}
}

FName AWTAPopUpBookActor::GetBookId() const
{
	return BookOfSpreads.IsValidIndex(BookIndex) && Books.IsValidIndex(BookOfSpreads[BookIndex]) ? Books[BookOfSpreads[BookIndex]].BookId : NAME_None;
}

int32 AWTAPopUpBookActor::NumSpreads() const
{
	return Spreads.IsValidIndex(BookIndex) ? Spreads[BookIndex].Num() : 0;
}

int32 AWTAPopUpBookActor::TotalSpreads() const
{
	int32 Total = 0;
	for (const TArray<FSpread>& Book : Spreads)
	{
		Total += Book.Num();
	}
	return Total;
}

FVector AWTAPopUpBookActor::GetSceneCentre() const
{
	return bHaveScene ? SceneCentre : GetActorLocation();
}

FVector AWTAPopUpBookActor::GetReaderLookAt() const
{
	if (!bHaveScene)
	{
		return GetActorLocation();
	}
	const FVector At = SceneCentre + Reader * 4.f;
	return FVector(At.X, At.Y, PageZ + 2.f);
}

FText AWTAPopUpBookActor::BookTitle(int32 Book) const
{
	const FName Id = BookOfSpreads.IsValidIndex(Book) && Books.IsValidIndex(BookOfSpreads[Book]) ? Books[BookOfSpreads[Book]].BookId : NAME_None;
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	const FWTABookRow* Row = Content != nullptr && !Id.IsNone() ? Content->FindBook(Id) : nullptr;
	return Row != nullptr ? Row->Title : FText::FromName(Id);
}

FText AWTAPopUpBookActor::GetCaption() const
{
	if (!BookOfSpreads.IsValidIndex(BookIndex) || !Books.IsValidIndex(BookOfSpreads[BookIndex]))
	{
		return FText::GetEmpty();
	}
	const FWTAPopUpBook& Book = Books[BookOfSpreads[BookIndex]];
	const int32 Page = Book.Pages.IsValidIndex(SpreadIndex) ? Book.Pages[SpreadIndex] : SpreadIndex;
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	const FWTABookRow* Row = Content != nullptr ? Content->FindBook(Book.BookId) : nullptr;
	if (Row == nullptr || !Row->Pages.IsValidIndex(Page))
	{
		return BookTitle(BookIndex);
	}
	const FWTABookPage& P = Row->Pages[Page];
	FString First;
	for (const FWTABookBlock& Block : P.Blocks)
	{
		First = Block.Text.ToString();
		if (First.IsEmpty() && Block.Items.Num() > 0)
		{
			First = Block.Items[0].ToString();
		}
		if (!First.IsEmpty())
		{
			break;
		}
	}
	First = PopUpFirstSentence(First, 170);
	if (First.IsEmpty())
	{
		return P.Heading;
	}
	return FText::Format(WTAText(TEXT("{0} — {1}")), P.Heading, FText::FromString(First));
}

void AWTAPopUpBookActor::ShowSpreadCaption()
{
	AWTAPlayerController* PC = Cast<AWTAPlayerController>(UGameplayStatics::GetPlayerController(this, 0));
	const FText Caption = GetCaption();
	if (PC == nullptr || Caption.IsEmpty())
	{
		return;
	}
	PC->ShowCaption(Caption);
	bCaptionUp = true;
	GetWorldTimerManager().SetTimer(CaptionTimer, this, &AWTAPopUpBookActor::HideCaption, FMath::Max(1.f, CaptionSeconds), false);
}

void AWTAPopUpBookActor::HideCaption()
{
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(CaptionTimer);
	}
	if (!bCaptionUp)
	{
		return;
	}
	bCaptionUp = false;
	if (AWTAPlayerController* PC = Cast<AWTAPlayerController>(UGameplayStatics::GetPlayerController(this, 0)))
	{
		PC->ShowCaption(FText::GetEmpty());
	}
}

void AWTAPopUpBookActor::NoteSpreadRead() const
{
	const FName Id = GetBookId();
	if (Id.IsNone())
	{
		return;
	}
	if (UWTAVisitLogSubsystem* Visits = UWTAVisitLogSubsystem::Get(this))
	{
		Visits->NoteCard(TEXT("popup"), Id);
	}
	const FWTAPopUpBook& Book = Books[BookOfSpreads[BookIndex]];
	if (UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this))
	{
		Progress->NotePage(Id, Book.Pages.IsValidIndex(SpreadIndex) ? Book.Pages[SpreadIndex] : SpreadIndex);
	}
}

AWTASeatActor* AWTAPopUpBookActor::FindReaderSeat() const
{
	if (!bSeatLooked || (!ReaderSeat.IsValid() && !ReaderSeatId.IsNone()))
	{
		bSeatLooked = true;
		ReaderSeat.Reset();
		if (!ReaderSeatId.IsNone() && GetWorld() != nullptr)
		{
			for (TActorIterator<AWTASeatActor> It(GetWorld()); It; ++It)
			{
				if (It->SeatId == ReaderSeatId)
				{
					ReaderSeat = *It;
					break;
				}
			}
		}
	}
	return ReaderSeat.Get();
}

bool AWTAPopUpBookActor::IsReaderSeated() const
{
	const AWTASeatActor* Seat = FindReaderSeat();
	if (Seat == nullptr)
	{
		return true;   // no chair to sit in: E works the book from where the visitor stands
	}
	const AWTACharacter* Player = Cast<AWTACharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
	return Player != nullptr && Player->IsSeated() && Player->GetSeat() == Seat;
}

void AWTAPopUpBookActor::ReadRow()
{
	Super::ReadRow();
	Label = WTAText(TEXT("Pop-up book"));
	// Where to stand to look at it: behind the reader's chair, 1.2 m back, the eye 162 cm over the floor traced
	// there (the table's 79 cm under the book when nothing answers), looking down at the scene.
	const FVector Centre = GetSceneCentre();
	const FVector Spot = Centre + Reader * 120.f;
	float FloorZ = static_cast<float>(Centre.Z) - 90.f;
	if (const UWorld* World = GetWorld())
	{
		FHitResult Hit;
		const FCollisionQueryParams Params(SCENE_QUERY_STAT(WTAPopUpFloor), false, this);
		if (World->LineTraceSingleByChannel(Hit, Spot + FVector(0.f, 0.f, 60.f), Spot - FVector(0.f, 0.f, 300.f), ECC_Visibility, Params))
		{
			FloorZ = static_cast<float>(Hit.ImpactPoint.Z);
		}
	}
	ViewSpot.Location = FVector(Spot.X, Spot.Y, FloorZ + 162.f);
	const FRotator Look = (Centre - ViewSpot.Location).Rotation();
	ViewSpot.Yaw = static_cast<float>(Look.Yaw);
	ViewSpot.Pitch = static_cast<float>(Look.Pitch);
	ViewSpot.bValid = true;
}

FText AWTAPopUpBookActor::GetInteractLabel_Implementation() const
{
	if (Spreads.Num() == 0)
	{
		return Label;
	}
	if (!IsReaderSeated())
	{
		return FText::Format(WTAText(TEXT("Read the pop-up book · {0}")), BookTitle(BookIndex));
	}
	const int32 Total = NumSpreads();
	auto Turn = [&](int32 To) -> FText
	{
		return To < Total ? FText::Format(WTAText(TEXT("Turn the page · {0} of {1}")), FText::AsNumber(To + 1), FText::AsNumber(Total))
			: WTAText(TEXT("Close the book"));
	};
	switch (State)
	{
	case EWTAPopUpState::Closed:
		return FText::Format(WTAText(TEXT("Open the pop-up book · {0}")), BookTitle(BookIndex));
	case EWTAPopUpState::Opening:
	case EWTAPopUpState::Open:
		return Turn(SpreadIndex + 1);
	case EWTAPopUpState::Closing:
		return bTurnAfterClose ? Turn(SpreadIndex + 2)
			: FText::Format(WTAText(TEXT("Open the pop-up book · {0}")), BookTitle((BookIndex + 1) % FMath::Max(1, Spreads.Num())));
	}
	return Label;
}

void AWTAPopUpBookActor::Interact_Implementation(AWTAPlayerController* Controller)
{
	if (Controller == nullptr || Spreads.Num() == 0)
	{
		return;
	}
	// The chair first, facing the book: the scene is made to be seen from there.
	AWTACharacter* Player = Controller->GetWTACharacter();
	AWTASeatActor* Seat = FindReaderSeat();
	if (Player != nullptr && Seat != nullptr && !(Player->IsSeated() && Player->GetSeat() == Seat))
	{
		Player->SitAt(Seat, Seat->GetSitPoint(), Seat->SeatYaw);
		Controller->SetControlRotation((GetReaderLookAt() - Player->GetEyeLocation()).Rotation());
		CheckPlayerNear();
		if (State == EWTAPopUpState::Open || State == EWTAPopUpState::Opening)
		{
			ShowSpreadCaption();
			NoteSpreadRead();
		}
		return;
	}
	Advance();
}

void AWTAPopUpBookActor::PlaceLight()
{
	if (BookLight == nullptr)
	{
		return;
	}
	const FVector Centre = GetSceneCentre();
	const FVector At = Centre + Reader * 55.f + FVector(0.f, 0.f, 75.f);
	BookLight->SetWorldLocation(At);
	BookLight->SetWorldRotation((Centre - At).Rotation());
	BookLight->SetLightColor(BookLightColor);
}

float AWTAPopUpBookActor::LightTarget() const
{
	// Up with the backdrop; between the spreads of a page turn it only dips, like a stage between scenes.
	const float Down = FMath::Clamp(BackAngle / 90.f, 0.f, 1.f);
	return Spreads.Num() == 0 ? 0.f : 1.f - Down * (bTurning ? 0.6f : 1.f);
}

void AWTAPopUpBookActor::UpdateLight(float DeltaSeconds)
{
	if (BookLight == nullptr)
	{
		return;
	}
	const float Target = LightTarget();
	LightLevel = DeltaSeconds > 0.f ? FMath::FInterpTo(LightLevel, Target, DeltaSeconds, 7.f) : LightLevel;
	if (FMath::IsNearlyEqual(LightLevel, Target, 0.002f))
	{
		LightLevel = Target;
	}
	const bool bOn = bPlayerNear && LightLevel > 0.005f;
	if (BookLight->IsVisible() != bOn)
	{
		BookLight->SetVisibility(bOn);
	}
	if (bOn)
	{
		BookLight->SetIntensity(BookLightIntensity * LightLevel);
	}
}

void AWTAPopUpBookActor::CheckPlayerNear()
{
	const APawn* Pawn = UGameplayStatics::GetPlayerPawn(this, 0);
	const bool bNear = Pawn == nullptr || FVector::Dist(Pawn->GetActorLocation(), GetSceneCentre()) < PopUpNearCm;
	if (bNear != bPlayerNear)
	{
		bPlayerNear = bNear;
		UpdateLight(0.f);
	}
	// The printed pages of every spread kept at full resolution while someone is near, so a spread that pops up is
	// sharp at once rather than streaming in from a blur (twenty-odd small textures).
	const UWorld* World = GetWorld();
	const double Now = World != nullptr ? World->GetTimeSeconds() : 0.0;
	if (bNear && Pawn != nullptr && Now - LastPrestream > 240.0)
	{
		LastPrestream = Now;
		for (UStaticMeshComponent* Comp : PieceComponents)
		{
			if (Comp != nullptr)
			{
				Comp->PrestreamTextures(600.f, false);
			}
		}
	}
}

FString AWTAPopUpBookActor::Describe() const
{
	static const TCHAR* StateNames[] = { TEXT("closed"), TEXT("opening"), TEXT("open"), TEXT("closing") };
	return FString::Printf(TEXT("book %s (%d of %d) spread %d of %d, %s, backdrop %.0f, layers %.0f %.0f %.0f, light %.2f%s, %d pieces"),
		*GetBookId().ToString(), BookIndex + 1, Spreads.Num(), SpreadIndex + 1, NumSpreads(), StateNames[static_cast<int32>(State)],
		BackAngle, LayerAngles[0], LayerAngles[1], LayerAngles[2], LightLevel, bPlayerNear ? TEXT("") : TEXT(" (nobody near)"),
		PieceComponents.Num());
}
