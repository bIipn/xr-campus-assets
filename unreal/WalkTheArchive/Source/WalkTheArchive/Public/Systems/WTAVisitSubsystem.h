// Walk the Archive - guided visits: one librarian leads a group of visitors, each on their own computer or
// headset, through the tour (roadmap idea 16).
//
// ROLES
// The role follows the world's net mode, so it can never disagree with what is really running:
//   Solo     a standalone game (everything as before)
//   Guide    a listen server: LeadVisit reloads the campus as one (OpenLevel ...?listen), the guide standing where
//            they stood; visitors join it on the game port (7777)
//   Visitor  a client of a guide: JoinVisit travels to "<address>:7777"
// Everyone else's world stays their own (cards, books, rides, the wax scenes run on each machine); what is shared
// is the people (AWTACharacter replicates, with a figure and a name tag for the others) and AWTAGameState: the stop
// the guide shows and the last gathering.
//
// FOLLOWING
// The guide's tour (UWTATourSubsystem) runs as always; every stop it shows goes to AWTAGameState::LeadStop. On a
// visitor's machine the stop arrives (HandleTourReplicated) and UWTATourSubsystem::FollowStop shows the same stop
// in the tour bar and walks the visitor to their own place round it: GroupSpot puts the guide (slot 0) on the stop's
// view and the visitors in two arcs behind and beside it, facing the same way, each place checked for floor and for
// a clear line to the stop. Between stops a visitor may wander; the next stop brings them back. GatherHere (the
// visit card, G) brings everyone to the guide wherever they stand, the same way.
// A visitor who joins mid-visit is put at their place round the guide (or the stop) as their pawn spawns.
//
// FINDING A VISIT
// While leading, the guide's machine broadcasts a small UDP beacon on BeaconPort every second
// ("WTAVISIT1|<guide>|<port>|<people>|<campus>"); the visit card listens while it is open and lists what it hears
// (StartSearch / GetFoundVisits). Joining by address works without it (other subnets, a blocked broadcast).
// -WTANoBeacon on the command line turns the beacon off (the two-instance QA run).
//
// LEAVING
// LeaveVisit: a visitor goes back to their own campus where they stood; the guide ends the visit for everyone. A
// visitor whose guide left (a network failure) comes back to their own campus where they last stood, with a toast.
// The view to stand at, a toast and (QA) the play test phases to continue with all carry over the map change here
// and are taken by the next controller (TakeRestoreView, TakePendingToast, TakePendingPlayTest).

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Containers/Ticker.h"
#include "Data/WTATypes.h"
#include "Engine/EngineBaseTypes.h"
#include "WTAVisitSubsystem.generated.h"

class AWTACharacter;
class AWTAGameState;
class AWTAPlayerController;
class AWTAPlayerState;
class FSocket;
class UNetDriver;

UENUM(BlueprintType)
enum class EWTAVisitRole : uint8
{
	Solo,
	Guide,
	Visitor
};

/** A visit heard on this network. */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAFoundVisit
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FString GuideName;

	/** ip:port to join. */
	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FString Address;

	/** Everyone in it, the guide included. */
	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	int32 People = 1;

	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FString Campus;

	double LastHeard = 0.0;
};

/** One person in the visit, for the card's list. */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAVisitPerson
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FString Name;

	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FLinearColor Color = FLinearColor::White;

	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	bool bGuide = false;

	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	bool bYou = false;
};

/** The role, the people or the list of visits heard changed. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FWTAVisitChanged);

UCLASS()
class WALKTHEARCHIVE_API UWTAVisitSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	/** The game port a guide listens on and the beacon's port. */
	static constexpr int32 GamePort = 7777;
	static constexpr int32 BeaconPort = 47790;

	UFUNCTION(BlueprintPure, Category = "WTA", meta = (WorldContext = "WorldContextObject"))
	static UWTAVisitSubsystem* Get(const UObject* WorldContextObject);

	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	// --- Who we are ----------------------------------------------------------------

	UFUNCTION(BlueprintPure, Category = "WTA")
	EWTAVisitRole GetRole() const;

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsInVisit() const { return GetRole() != EWTAVisitRole::Solo; }

	/** The name this visitor gives (the certificate's remembered name until one is typed on the visit card). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FString GetMyName() const;

	UFUNCTION(BlueprintCallable, Category = "WTA")
	void SetMyName(const FString& Name);

	/** The guide's name (empty in solo play). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FString GetGuideName() const;

	/** Everyone in the visit, the guide first, then the visitors by slot. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	TArray<FWTAVisitPerson> GetPeople() const;

	/** This machine's network addresses (IPv4, no loopback), for a guide to read out: "192.168.1.23". */
	UFUNCTION(BlueprintPure, Category = "WTA")
	TArray<FString> GetLocalAddresses() const;

	/** What is happening or what went wrong last ("Joining 192.168.1.20 ...", "Could not reach ..."). */
	UFUNCTION(BlueprintPure, Category = "WTA")
	FText GetStatus() const { return Status; }

	// --- Doing -------------------------------------------------------------------------

	/** Solo only: reload the campus as a listen server with this player as the guide, standing where they stand. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	bool LeadVisit();

	/** Solo only: join the guide at Address ("192.168.1.20" or "host:port"). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	bool JoinVisit(const FString& Address);

	/** A visitor leaves (back to their own campus where they stand); the guide ends the visit for everyone. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void LeaveVisit();

	/** Guide: everyone comes to where the guide stands. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	bool GatherHere();

	/** Visitor: walk to your place round the guide. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	bool WalkToGuide();

	// --- Finding visits -------------------------------------------------------------

	/** Listen for guides' beacons (the visit card opens). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void StartSearch();

	UFUNCTION(BlueprintCallable, Category = "WTA")
	void StopSearch();

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsSearching() const { return SearchSocket != nullptr; }

	/** Visits heard in the last few seconds, newest guide name order. */
	UFUNCTION(BlueprintPure, Category = "WTA")
	TArray<FWTAFoundVisit> GetFoundVisits() const;

	// --- Places round a spot -----------------------------------------------------------

	/**
	 * Where the person in Slot stands for a group spot (Floor, Yaw, Pitch): the guide (slot 0) on it, the visitors
	 * in two arcs behind and beside it facing the same way, so everyone sees past the guide. A place is kept only
	 * with floor under it (the NavMesh, else a trace) and a clear line from the spot; otherwise the next place round
	 * is tried, and the spot itself is the last resort. Returns an eye view (Location = eye).
	 */
	static FWTAView GroupSpot(UWorld* World, const FVector& Floor, float Yaw, float Pitch, int32 Slot, float EyeHeight);

	/** The floor point under an eye view (the NavMesh when there is one, else a trace down). */
	static FVector FloorUnder(UWorld* World, const FVector& Eye, float EyeHeight);

	/** Server: the eye view for a visitor who just joined - their place round the stop showing, else round the guide.
	    False when there is no guide pawn yet. */
	bool ArrivalViewFor(const AWTAPlayerState* Person, FWTAView& OutView) const;

	// --- From the game state (visitors' machines) ---------------------------------------

	void HandleTourReplicated(int32 Stop, int32 Serial);
	void HandleGatherReplicated(const FVector& Floor, float Yaw, int32 Serial);
	/** The game state began play on a visitor's machine: a gathering already in it is history, not a call. */
	void NoteGatherSerial(int32 Serial);

	// --- Carried over a map change -------------------------------------------------------

	bool TakeRestoreView(FWTAView& OutView);
	bool TakePendingToast(FText& OutText);
	void SetPendingPlayTest(const FString& Phases) { PendingPlayTest = Phases; }
	bool TakePendingPlayTest(FString& OutPhases);

	UPROPERTY(BlueprintAssignable, Category = "WTA")
	FWTAVisitChanged OnVisitChanged;

protected:
	bool TickVisit(float DeltaTime);

	UFUNCTION()
	void HandleTourChanged(int32 Index);

	void HandleNetworkFailure(UWorld* World, UNetDriver* NetDriver, ENetworkFailure::Type FailureType, const FString& Error);
	void HandleTravelFailure(UWorld* World, ETravelFailure::Type FailureType, const FString& Error);
	void HandlePostLoadMap(UWorld* World);

	UWorld* CurrentWorld() const;
	AWTAPlayerController* LocalController() const;
	AWTAGameState* VisitState() const;
	/** The local player's slot (0 when unknown). */
	int32 MySlot() const;
	/** The campus map's long package name, without a PIE prefix. */
	FString MapPath() const;
	/** Remember where the local player stands, to come back to after the next map change. */
	void KeepCurrentView();
	/** The local player walks (near) or is put (far) at View. */
	void MoveLocalPlayer(const FWTAView& View, float WalkWithin);

	void SendBeacon();
	void ReadBeacons();
	void CloseSocket(FSocket*& Socket);

	FTSTicker::FDelegateHandle TickHandle;
	FDelegateHandle NetworkFailureHandle;
	FDelegateHandle TravelFailureHandle;
	FDelegateHandle PostLoadMapHandle;

	FText Status;
	FString JoiningAddress;
	bool bJoining = false;
	/** LeadVisit reloaded the map as a listen server; a standalone world after it means listening failed. */
	bool bLeading = false;
	/** This machine was a visitor in the world that just went away (so a failure means the guide left). */
	bool bWasVisitor = false;
	bool bTourBound = false;

	FWTAView LastKnownView;
	FWTAView RestoreView;
	bool bRestoreView = false;
	FText PendingToast;
	FString PendingPlayTest;

	/** The serials this world has acted on (-1: none seen yet, so the first gather on joining is not acted on). */
	int32 LastTourSerial = -1;
	int32 LastGatherSerial = -1;

	/** A stop or a gathering that came before this visitor's pawn or slot did: the tick applies it then. */
	bool bPendingTour = false;
	int32 PendingTourStop = -1;
	int32 PendingTourSerial = 0;
	bool bPendingGather = false;
	FVector PendingGatherFloor = FVector::ZeroVector;
	float PendingGatherYaw = 0.f;
	int32 PendingGatherSerial = 0;

	/** NavMesh builds tried on this visitor's machine (BuildNavigationIfEmpty, up to three). */
	int32 ClientNavTries = 0;

	/** The people signature last broadcast (names and slots), to tell the HUD when someone comes or goes. */
	FString PeopleSignature;
	float SinceKeep = 0.f;
	float SinceBeacon = 0.f;
	float SincePeople = 0.f;

	FSocket* BeaconSocket = nullptr;
	FSocket* SearchSocket = nullptr;
	TMap<FString, FWTAFoundVisit> Found;
};
