// Walk the Archive - QA play test (console: WTAPlayTest [phases]).
//
// Drives the running game the way a player does and logs one line per check:
//   WTA_PLAY <phase> PASS|FAIL|SKIP|INFO <what> | <details>
// then "WTA_PLAY done <n> pass, <n> fail, <n> skip". Screenshots go to Saved/Screenshots/<platform>/QA/
// (play_<NN>_<name>.png with the HUD; face_<NN>_<person>.png without it).
//
// Keys go through Slate (FSlateApplication::ProcessKeyDownEvent / ProcessKeyUpEvent), so the real Enhanced Input
// bindings run: W + Left Shift walk, E interacts, Esc, T, M, Enter, and the arrow keys turn book pages. The "keys"
// phase checks the routing first (M opens the places list, Esc closes it); if keys do not arrive, the later phases
// call the controller's input handlers instead and say so.
//
// Phases, in this order ("all" runs every one; otherwise a list such as "faces people"):
//   menu      the intro menu is open at start; Enter (what its button runs) starts in the lobby facing the galleries;
//             Esc opens the pause menu and Esc closes it
//   keys      key routing check
//   walk      each line "<name> | <x> <y> | <yaw> | x|y <wall coordinate>" of Saved/QA/walk_tests.txt: stand there
//             facing the wall, hold W + Shift for 1.1 s, and check the player never crossed the wall's plane or fell
//   interact  every interactable: stand at its view spot (or in front of it), check the crosshair names it, press E,
//             check what opens (exhibit card, book, station, ride card, chat, token collected), turn a book's pages,
//             Esc closes it
//   wax       stand in front of each Wax Hall scene, press E with nothing under the crosshair: the scene's story opens
//   quiz      (only when named) every class's quiz straight from DT_Talks, no venue needed: opened, answered right,
//             the name typed, the certificate shown and saved
//   talks     every talk and class (DT_Talks): the speaker on the spot and the title slide on the screens; sit on a seat
//             of its venue, the talk starts (slide 1, the voice reading, a caption); the next slide shows; a class is
//             run to its end, the quiz opens, every question is answered right, a name is typed, the certificate
//             shows and saves its picture, the badges arrive; standing up stops it
//   ui        T starts the tour and walks to the first stop, T walks on, Esc ends it; M places; Enter chat; badges
//   graphics  the menu's Medium and Epic presets apply (checked), then the levels found at the start come back
//   fps       average and worst frame time over 3 s at five places
//   people    wax figures are frozen in their held pose (hands down, not arms out), face on the head, and no bone
//             their current LOD draws with is left at the feet
//   faces     a close-up of every person's face (staff and reenactors) from 75 cm, no HUD; on screen: the face sits
//             on the head, no bone of the face or body is left at the feet (the drooping face), staff idles move
//   adapt     (only when named) from the sunny yard into a classroom, the lab, the Wax Hall and the library: no-HUD
//             shots 0.5, 2, 5 and 8 s after arriving, to see how long the auto exposure leaves a room dark
//   group_lead / group_join  (only when named; two games, Tools/win visit_qa: one leads, one joins) a guided visit:
//             group_lead names the guide, reloads the campus as a listen server and goes on as group_guide: a visitor
//             joins and stands beside the guide as a figure with a name, the tour's first two stops bring the visitor
//             to their places round each stop, a gathering brings them to the guide, the tour ends, the visitor
//             leaves. group_join joins host=<address> (127.0.0.1) and goes on as group_guest: the visitor arrives at
//             the guide's side, follows both stops (T does not move the tour), comes when gathered, sees the tour
//             end, leaves, and (group_left) is back on their own campus. Shots: play_NN_group_guide_* / _guest_*.
//   vr        (only when named) VR on a desktop (the -vrsim presentation, entered if not on): the HUD on its screen in the
//             world; the laser on an exhibit names it and the trigger opens its card on the card screen; the laser
//             on the card's Close button closes it; B opens the menu there and its Resume button closes it; the
//             trigger on the floor steps there; the right stick turns 30 degrees; stand-in people show their names in
//             the world; the tour's Next button on the HUD screen moves the tour on; leaving VR puts every widget back
//             in the viewport. Shots: play_NN_vr_*.
// Tokens: "only=<text>" keeps the people / interactables whose name contains <text>; "speeddown=<stops per second>"
// sets every post process volume's auto exposure Speed Down for this run (to compare adaptation speeds);
// "host=<address>" is the guide group_join joins.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Data/WTATypes.h"
#include "InputCoreTypes.h"
#include "WTAPlayTest.generated.h"

class ACameraActor;
class AWTACharacter;
class AWTAPlayerController;
class UUserWidget;

UCLASS(ClassGroup = (WTA))
class WALKTHEARCHIVE_API UWTAPlayTest : public UActorComponent
{
	GENERATED_BODY()

public:
	UWTAPlayTest();

	/** Build the script for Phases ("all", or phase names separated by spaces or commas) and start it. */
	void Run(const FString& Phases);

	/** True while a script is running. */
	bool IsRunning() const { return Steps.IsValidIndex(StepIndex); }

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	/** One scripted step. Do() acts and returns the seconds to wait before the next step; a negative value waits
	 *  that long and runs the same step again (polling), the step itself decides when to stop. */
	struct FStep
	{
		FString Name;
		TFunction<float()> Do;
	};

	enum class EResult : uint8 { Pass, Fail, Skip, Info };

	AWTAPlayerController* PC() const;
	AWTACharacter* Player() const;

	void Report(const TCHAR* Phase, EResult Result, const FString& What, const FString& Details);
	void Shot(const FString& Name, bool bShowUI = true);

	/** Send a key through Slate (bKeysWork) or call the controller's handler for it (down only). */
	void KeyDown(const FKey& Key);
	void KeyUp(const FKey& Key);
	/** Append the two steps of a key tap (down, then up 0.12 s later), then wait After seconds. */
	void AddTap(const FString& Name, const FKey& Key, float After);
	/** Close the menu, the chat and the panel and end the tour. */
	void CloseAll();
	/** Stand at a view (teleport, no walking; also drops a view the camera was still turning toward). */
	void StandAt(const FWTAView& View);
	/** For a failure line: the camera, what the screen-centre ray hits first, and where Target is. */
	FString DescribeAim(const AActor* Target) const;

	void AddMenuPhase();
	void AddKeysPhase();
	void AddWalkPhase();
	void AddInteractPhase();
	void AddWaxPhase();
	/** Every seat (up to a few per room): the crosshair says Sit, E sits the player at the seated eye height with the view clear, Space stands them back up. */
	void AddSeatsPhase();
	/** Every talk and class: see the header. */
	void AddTalksPhase();
	/** Only when named: every class's quiz opened straight from DT_Talks (no venue needed), answered right, the certificate. */
	void AddQuizPhase();
	/** Every station: its card opens on the overview, Start shows step 1, every step follows, Finish notes it finished (ticked, badge). */
	void AddStationsPhase();
	/** course: each course's desk, card, stations finished through the card's Go buttons, quiz and certificate. */
	void AddCoursePhase();
	/** photo: P writes a framed postcard of the view; the frame is shot while it is up, then the file is checked. */
	void AddPhotoPhase();
	/** hunt: the library card opens with the tokens found as stamps, a collected token adds one, a full card's picture is written. */
	void AddHuntPhase();
	/** visits: this session's visit log is being written (rooms, cards, positions). */
	void AddVisitsPhase();
	/** wall: a postcard taken now hangs on the visitors' wall; a no-HUD shot of it. */
	void AddWallPhase();
	/** season: an exhibit's title and picture written to Saved/Season, read again without a rebuild; the card and the frame show them; the files are removed after. */
	void AddSeasonPhase();
	void AddStoriesPhase();
	void AddPopUpPhase();
	/** Guided visits across two games (see the header): the guide's side and the visitor's. */
	void AddGroupLeadPhase();
	void AddGroupGuidePhase();
	void AddGroupJoinPhase();
	void AddGroupGuestPhase();
	void AddGroupLeftPhase();
	/** vr: see the header. */
	void AddVRPhase();
	/** The centre, in the widget's own pixels, of Root's visible button whose action is Action (the smallest, when
	    several are: a scrim's close button fills the screen). */
	bool FindButtonPixel(UUserWidget* Root, FName Action, FVector2D& OutPixel) const;
	/** Turn the view to look at Target (the simulation's laser goes where the view looks). */
	void AimAt(const FVector& Target);
	/** The other person's pawn in a visit (the first one that is not this player's). */
	AWTACharacter* OtherPerson() const;
	/** The guide's pawn on this machine. */
	AWTACharacter* GuidePerson() const;
	/** Turn the camera to look at a person's head. */
	void LookAtPerson(const AWTACharacter* Person);
	/** The quiz steps shared by the talks and quiz phases: every question answered right, the result, the name, the certificate and its picture. */
	void AddQuizSteps(const FString& Phase, const FString& Name, FName TalkId, const TArray<FWTAQuizQuestion>& Quiz, const TSharedRef<bool>& Ok, const FString& Tag);
	/** Only when named: stands at each wax stage and watches a whole loop, for the acting shots and checks. */
	void AddActingPhase();
	/** Only when named: walks up to a spread of exhibits and checks each one's light rises as you arrive
	 *  and that a distant one stays dark. */
	void AddAttractPhase();
	/** Only when named: five viewpoints through the Reading Room, and the two second-storey checks -
	 *  that the gallery deck holds you up and that the spiral stair can be walked. */
	void AddLibraryPhase();
	void AddMuseumPhase();
	/** Only when named: a shot of every doorway from each side, then a walk through it with W held - the way
	 *  through must be clear (no kerb to step over, nothing to jump) and must arrive. */
	void AddDoorsPhase();
	void AddUIPhase();
	void AddGraphicsPhase();
	void AddFpsPhase();
	void AddPeoplePhase();
	void AddFacesPhase();
	void AddAdaptPhase();
	void AddWalkTest(const FString& Name, const FVector2D& XY, float Yaw, bool bAxisX, float WallAt);
	void AddInteractTest(AActor* Actor, int32 ClassIndex);

	/** Where to stand to look at Actor's centre from a clear spot with floor under it (24 directions, six distances).
	 *  OutWhy (optional) gets a count of why the spots failed when none works. */
	bool FindAimView(AActor* Actor, FWTAView& OutView, FString* OutWhy = nullptr) const;
	/** The people (MetaHuman actors) in the world: staff children and wax reenactors, with a readable name each. */
	void FindPeople(TArray<TPair<FString, TWeakObjectPtr<AActor>>>& Out) const;

	TArray<FStep> Steps;
	int32 StepIndex = INDEX_NONE;
	float WaitSeconds = 0.f;

	int32 NumPass = 0;
	int32 NumFail = 0;
	int32 NumSkip = 0;
	int32 ShotIndex = 0;
	int32 FaceIndex = 0;

	/** "only=<text>" phase tokens: the people and interact phases keep names containing one of these (empty = all). */
	TArray<FString> PeopleFilter;

	/** group_join: the guide's address ("host=<address>", else 127.0.0.1). */
	FString GroupHost;

	/** adapt phase: the step that is waiting before its shot. */
	bool bAdaptWaited = false;

	/** Keys reach the game through Slate (set by the keys phase). */
	bool bKeysWork = true;
	/** Fallback hold for W + Shift when keys do not arrive. */
	bool bHoldForward = false;

	/** fps phase. */
	bool bMeasuring = false;
	float MeasureSeconds = 0.f;
	int32 MeasureFrames = 0;
	float WorstFrame = 0.f;

	/** walk phase: tests that moved at least 50 cm (proves the keys moved the player). */
	int32 WalkMoved = 0;
	int32 WalkTests = 0;

	/** graphics phase: the levels found at the start. */
	int32 SavedQuality[11] = {};
	float SavedResolutionScale = 100.f;

	UPROPERTY(Transient)
	TObjectPtr<ACameraActor> FaceCamera;
};
