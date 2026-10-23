// Walk the Archive - every data struct the DataTables use.
//
// This file mirrors contract/structs.json exactly: same struct names, same field names,
// same field order, same types. The data converter (Pipeline/data/build_data.py) writes
// WalkTheArchive/Data/<File>.json against the same list, and the editor setup fills the
// DataTables from that JSON, so any change here must start in structs.json.
//
// Units: Unreal centimetres and Unreal axes (X east, Y south, Z up). Yaw/Pitch in degrees.
// Row Name = the web id (exhibit ids keep their '-'). "None" in JSON means an unset FName.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "Math/Color.h"
#include "Math/Vector.h"
#include "Math/Vector2D.h"
#include "UObject/SoftObjectPtr.h"
#include "UObject/SoftObjectPath.h"
#include "WTATypes.generated.h"

class UTexture2D;
class AActor;

// ---------------------------------------------------------------------------
// Plain structs (not table rows)
// ---------------------------------------------------------------------------

/** A place to stand and look from. Location is the player's EYE position in cm (floor + 162). */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAView
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FVector Location = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	float Yaw = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	float Pitch = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	bool bValid = false;
};

/** One block on a book page. Type is one of Para, List, Quote, Note, Code. */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTABookBlock
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Type;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Text;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FText> Items;
};

/** One page of a book: a heading and its blocks. */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTABookPage
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Heading;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FWTABookBlock> Blocks;
};

/** One timed caption line of a Wax Hall scene. Time is seconds into the loop. */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAWaxLine
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	float Time = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Text;
};

/**
 * One thing a reenactor does, from Time until the next beat (the last one runs to the end of the loop and
 * crossfades back into the first, so the scene loops without a seam). Action names an AnimSequence at
 * /Game/WTA/Characters/Common/Anims/Mocap/AS_WTA_<Action>, retargeted from Mixamo motion capture by
 * Content/Python/wta_mocap. Authored in Pipeline/content/wax_acting.json.
 */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAWaxBeat
{
	GENERATED_BODY()

	/** Seconds into the scene's loop. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	float Time = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Action;

	/** Degrees added to the figure's yaw while this beat plays; the figure turns over Blend seconds. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	float Yaw = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	float Rate = 1.f;

	/** Crossfade from the beat before, in seconds. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	float Blend = 0.35f;

	/** Centimetres added to the figure's height while this beat plays (seated clips sit at their own seat height). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	float Lift = 0.f;
};

/**
 * One reenactor standing on a Wax Hall stage. Person = id in Content/Python/wta_people/people.json; its MetaHuman
 * Blueprint is /Game/WTA/Characters/<Person>/BP_<Person>. Offset = feet position in the stage's frame in cm
 * (X toward the aisle along StageYaw, Y to the right of X, Z up from the stage floor). Yaw = degrees added to
 * StageYaw (0 = facing the aisle). Beats = what it acts out while the player is watching; with none it holds
 * one frame of the idle, as it did before the scenes were animated.
 */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAWaxFigure
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Person;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FVector Offset = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	float Yaw = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FWTAWaxBeat> Beats;
};

/**
 * Where a prop is at Time: held by Figure at Socket (head, hand_l, hand_r, chest) with Offset/Rotation in that
 * socket's frame, or standing in the stage's own frame when Figure is empty. Between two keys the prop travels
 * from one to the other over the second key's Blend seconds, so a headset passed from one pair of hands to
 * another moves with them.
 */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAWaxPropKey
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	float Time = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Figure;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Socket;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FVector Offset = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FRotator Rotation = FRotator::ZeroRotator;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	float Blend = 0.5f;
};

/** A prop on a Wax Hall stage: a headset, a tablet, a clipboard, a box, a book or a phone, and where it rides. */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAWaxProp
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Id;

	/** headset / tablet / clipboard / box / book / phone: how it sits in a hand, and the block to show when
	 *  the web's own model is not imported. "static": a web carry the acting never moves. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Kind;

	/** >= 0: the web's own model for this prop, the mesh prop__<scene>_<WebIndex> of Props.glb (its own frame). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	int32 WebIndex = -1;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FWTAWaxPropKey> Keys;
};

// ---------------------------------------------------------------------------
// Table rows
// ---------------------------------------------------------------------------

/** DT_Strings: the engine's own words in the pack's language. The row name is the English text the C++ writes
 *  (WTAText("Close")); Text is what shows instead. Empty table = English. Built by build_data.py from
 *  Pipeline/content/lang/<lang>/strings.json when WTA_LANG is set. */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAStringRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Text;
};

/** DT_Sources: a citation the catalog card links to. */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTASourceRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Label;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FString Url;
};

/** DT_Galleries: the lobby (0) and the three galleries (1..3). */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAGalleryRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	int32 Index = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Label;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Years;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FLinearColor WallColor = FLinearColor::White;
};

/**
 * DT_Exhibits: 15 gallery exhibits + the Freedom to Read board + the 12 Wax Hall cards (bWax).
 * Location = centre of the artwork; Yaw = direction the artwork faces; Size = width x height in cm.
 */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAExhibitRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName KindId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Kind;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	int32 Gallery = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Title;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Date;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	int32 Year = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Description;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText More;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Quote;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText QuoteBy;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Where;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Partners;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FName> Sources;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Hall;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	bool bWax = false;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName WaxSceneId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TSoftObjectPtr<UTexture2D> Art;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FVector Location = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	float Yaw = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FVector2D Size = FVector2D::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FWTAView View;
};

/** DT_Subjects: the eight library shelf subjects. */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTASubjectRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Side;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	int32 Slot = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FLinearColor Color = FLinearColor::White;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FWTAView ShelfView;
};

/** DT_Books: a library book with its pages. */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTABookRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Subject;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Title;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Subtitle;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FWTABookPage> Pages;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TSoftObjectPtr<UTexture2D> Cover;
	/** The client's catalogue search for this title (empty: no link), and the link's words ("Find it in WorldCat"). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FString CatalogueUrl;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText CatalogueLabel;
};

/** DT_Rooms: room boxes in cm (UE axes). Wing groups rooms (museum, wax, lib, school, play). */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTARoomRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Kicker;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Sub;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Wing;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FVector BoundsMin = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FVector BoundsMax = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	bool bOutdoor = false;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName StaffId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText MapLabel;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName GoPlace;
};

/** DT_Places: a named place with its aliases (for staff directions) and a view to walk to. */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAPlaceRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Label;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FString> Aliases;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FWTAView View;

	/** The answer to "where is it?", after "That's " ("the Wax Hall, straight ahead from the lobby ..."). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Directions;

	/** How staff name the place mid-sentence ("Follow me to the Wax Hall."); empty = Label. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Say;
};

/**
 * DT_Tour: one guided-tour stop. Row name = stop number zero-padded (S01..S35).
 * ItemId points at DT_Exhibits for exhibit stops. Action: None | OpenItem | OpenBook | OpenStation | OpenRide | GoPlace.
 */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTATourStopRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	int32 Index = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Kind;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName ItemId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Title;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText DateLabel;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Body;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FWTAView View;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText OpenLabel;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Action;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName ActionArg;
};

/**
 * DT_Staff: the four virtual staff. Location = feet position in cm; Yaw = facing.
 * MetaHuman is set once the MetaHuman Blueprint exists (/Game/WTA/Characters/<Id>/BP_<Id>.BP_<Id>_C).
 */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAStaffRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Role;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Monogram;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FLinearColor Color = FLinearColor::White;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FName> Rooms;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FVector Location = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	float Yaw = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FWTAView TalkView;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Greeting;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText GreetingShort;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Help;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Fallback;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FText> Chips;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName RocketboxId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FString LookNotes;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TSoftClassPtr<AActor> MetaHuman;
};

/**
 * DT_StaffRules: preset answers. Pattern is an ICU regex (case-insensitive) tested against the question.
 * Order = priority (lower first; < 100 runs before directions and title matches, >= 100 after).
 * StaffOnly/StaffNot filter by staff id. Ties in Order are broken by row name. Action: None | GoPlace | OpenItem | OpenBook
 * | OpenStation | OpenRide | StartTour | OpenBadges. bOffer = the action waits for a button under the answer (labelled
 * OfferLabel, or a default for the action) instead of running on its own.
 */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAStaffRuleRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	int32 Order = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FString Pattern;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	int32 MaxWords = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FName> StaffOnly;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FName> StaffNot;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Answer;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Action;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName ActionArg;

	/** true = Action is offered as a button under the answer (the web showed a card); false = it runs on its own. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	bool bOffer = false;

	/** The offer button's label; empty = the default for the action ("Take me there", "Open the book", ...). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText OfferLabel;
};

/** DT_Facts: a short fact about XRLibraries with its sources (feeds staff answers). */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAFactRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Body;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FName> Sources;
};

/** DT_Lessons: a lesson paragraph tied to a station (feeds staff answers). */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTALessonRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Station;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Title;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Body;
};

/** DT_Badges: a badge and the sentence that says how to earn it. */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTABadgeRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText How;
};

/** DT_Tokens: a hidden XR token. RideGate = ride id that must be running to collect it (None = always). */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTATokenRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Place;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Hint;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Wing;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FVector Location = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName RideGate;
};

/**
 * DT_WaxScenes: a Wax Hall scene. StageLocation = front-centre of the stage floor; StageYaw = direction the
 * stage faces (toward the aisle). Sequence = Level Sequence once authored (empty until then). Figures = the
 * reenactors on the stage (AWTAWaxStageActor spawns each one's MetaHuman once it has been built).
 */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAWaxSceneRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	int32 Number = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Year;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Title;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	float LoopSeconds = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FWTAWaxLine> Lines;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FVector StageLocation = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	float StageYaw = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName ItemId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FSoftObjectPath Sequence;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FWTAWaxFigure> Figures;

	/** Headsets, tablets and boxes the reenactors hold while the scene plays. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FWTAWaxProp> Props;
};

/**
 * DT_Stations: hands-on stations (sieve, titration, pendulum, bench, diorama, easel).
 * Steps = step titles; Panel = the intro paragraphs shown in the station panel.
 */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAStationRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Room;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Kicker;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Title;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Subtitle;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText GoLabel;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FText> Steps;

	/** One paragraph per step: what to do and why (the panel shows and reads one at a time). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FText> StepTexts;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FText> Panel;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	bool bUsesHands = false;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FVector Location = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FWTAView View;
};

/** DT_Rides: a ride card (coaster, drop, dive). ExitView = where the player stands after the ride. */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTARideRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Kicker;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText CardText;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText CardNote;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText About;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Stats;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Safety;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName BadgeId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FVector Location = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FWTAView ExitView;
};

/**
 * One slide of a talk or class: what the screens show while the speaker says Say. Slide = the slide image
 * (/Game/WTA/Slides/T_Slide_<talk>_<nn>, drawn by bl/slides.py); Clip = the line's voice id (the clip is
 * /Game/WTA/Audio/VO_talk_<Clip>); Seconds = how long the slide stays up when there is no clip.
 */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTATalkSlide
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Title;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FText> Points;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Say;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TSoftObjectPtr<UTexture2D> Slide;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Clip;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	float Seconds = 8.f;
};

/** One multiple-choice question of a class's quiz. Answer = index into Options; Why = shown after answering. */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAQuizQuestion
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Question;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FText> Options;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	int32 Answer = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Why;

	/** Voice id: the question read aloud is /Game/WTA/Audio/VO_quiz_<Clip>. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Clip;
};

/** The certificate a class gives for passing its quiz; the visitor's name goes between Title and Line. */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTACertificate
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Title;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Line;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Place;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Signer;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText SignerRole;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Org;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Note;
};

/**
 * DT_Talks: a talk or a class (Pipeline/content/talks.json, or the client pack's own). Venue = the room the
 * builders made: its screens are the meshes screen__<Venue>[_l|_r], the speaker stands on spot__<Venue>_f<yaw>,
 * its seats are seat__<Venue>_*. Kind = talk | class. Person = the MetaHuman who speaks (a wta_people id) and
 * Staff = a staff member who teaches it instead (the NPC walks to the spot while the class runs). A class has
 * a Quiz; PassCount right answers earn the Certificate and BadgeId. AWTATalkActor runs it when a visitor sits.
 */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTATalkRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Venue;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Kind;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Title;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Subtitle;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Speaker;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText SpeakerShort;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText SpeakerRole;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Person;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName Staff;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FWTATalkSlide> Slides;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FWTAQuizQuestion> Quiz;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	int32 PassCount = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FWTACertificate Certificate;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FName BadgeId;

	/** A course's stations (DT_Stations ids), all to be finished before its quiz opens at the course desk. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FName> Stations;

	/** What the course lead says at the desk (read aloud as VO_talk_<id>_01). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Intro;

	bool IsClass() const { return Kind == FName(TEXT("class")); }
	bool IsCourse() const { return Kind == FName(TEXT("course")); }
};

// ---------------------------------------------------------------------------
// The action vocabulary (CONTRACT.md section 4.8). Shared by tour stops, staff rules and buttons.
// Returned as functions so the FNames are built after the engine's name table exists.
// ---------------------------------------------------------------------------
namespace WTAAction
{
	/** Walk to a place; arg = DT_Places row. */
	inline FName GoPlace()     { static const FName N(TEXT("GoPlace"));     return N; }
	/** Open an exhibit card; arg = DT_Exhibits row. */
	inline FName OpenItem()    { static const FName N(TEXT("OpenItem"));    return N; }
	/** Open the book reader; arg = DT_Books row (on its cover), or "<row>#<page index>" to open at that page. */
	inline FName OpenBook()    { static const FName N(TEXT("OpenBook"));    return N; }
	/** Open a station panel; arg = DT_Stations row. */
	inline FName OpenStation() { static const FName N(TEXT("OpenStation")); return N; }
	/** Open a ride card; arg = DT_Rides row. */
	inline FName OpenRide()    { static const FName N(TEXT("OpenRide"));    return N; }
	/** Start the guided tour; no arg. */
	inline FName StartTour()   { static const FName N(TEXT("StartTour"));   return N; }
	/** Open the badges list; no arg. */
	inline FName OpenBadges()  { static const FName N(TEXT("OpenBadges"));  return N; }
	/** Open a class's quiz; arg = DT_Talks row. */
	inline FName OpenQuiz()    { static const FName N(TEXT("OpenQuiz"));    return N; }
	/** A course's card (DT_Talks row of kind course): Arg = the talk id. */
	inline FName OpenCourse()  { static const FName N(TEXT("OpenCourse"));  return N; }
	/** The token hunt's library card (the tokens as stamps). */
	inline FName OpenHunt()    { static const FName N(TEXT("OpenHunt"));    return N; }
	/** Start (or restart) a talk from its first slide; arg = DT_Talks row. Sitting in its venue does the same. */
	inline FName StartTalk()   { static const FName N(TEXT("StartTalk"));   return N; }
}

/** Badge ids from DT_Badges that the C++ awards itself (the rest are phase 1+ features). */
namespace WTABadge
{
	inline FName FirstSteps() { static const FName N(TEXT("first-steps")); return N; }
	inline FName Explorer()   { static const FName N(TEXT("explorer"));    return N; }
	inline FName Bookworm()   { static const FName N(TEXT("bookworm"));    return N; }
	inline FName Curious()    { static const FName N(TEXT("curious"));     return N; }
	inline FName Hunter()     { static const FName N(TEXT("hunter"));      return N; }
	inline FName Historian()  { static const FName N(TEXT("historian"));   return N; }
	/** Heard a talk through to its last slide. */
	inline FName Listener()   { static const FName N(TEXT("listener"));    return N; }
}
