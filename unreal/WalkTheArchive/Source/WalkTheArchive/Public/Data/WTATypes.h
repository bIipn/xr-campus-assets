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

// ---------------------------------------------------------------------------
// Table rows
// ---------------------------------------------------------------------------

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

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "WTA")
	FText Directions;
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
 * StaffOnly/StaffNot filter by staff id. Action: None | GoPlace | OpenItem | OpenBook | OpenStation | StartTour | OpenBadges.
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
 * stage faces (toward the aisle). Sequence = Level Sequence once authored (empty until then).
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
	/** Open the book reader; arg = DT_Books row. */
	inline FName OpenBook()    { static const FName N(TEXT("OpenBook"));    return N; }
	/** Open a station panel; arg = DT_Stations row. */
	inline FName OpenStation() { static const FName N(TEXT("OpenStation")); return N; }
	/** Open a ride card; arg = DT_Rides row. */
	inline FName OpenRide()    { static const FName N(TEXT("OpenRide"));    return N; }
	/** Start the guided tour; no arg. */
	inline FName StartTour()   { static const FName N(TEXT("StartTour"));   return N; }
	/** Open the badges list; no arg. */
	inline FName OpenBadges()  { static const FName N(TEXT("OpenBadges"));  return N; }
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
}
