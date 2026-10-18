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
//   ui        T starts the tour and walks to the first stop, T walks on, Esc ends it; M places; Enter chat; badges
//   graphics  the menu's Medium and Epic presets apply (checked), then the levels found at the start come back
//   fps       average and worst frame time over 3 s at five places
//   people    wax figures are frozen in their held pose (hands down, not arms out), face on the head, and no bone
//             their current LOD draws with is left at the feet
//   faces     a close-up of every person's face (staff and reenactors) from 75 cm, no HUD; on screen: the face sits
//             on the head, no bone of the face or body is left at the feet (the drooping face), staff idles move
//   adapt     (only when named) from the sunny yard into a classroom, the lab, the Wax Hall and the library: no-HUD
//             shots 0.5, 2, 5 and 8 s after arriving, to see how long the auto exposure leaves a room dark
// Tokens: "only=<text>" keeps the people / interactables whose name contains <text>; "speeddown=<stops per second>"
// sets every post process volume's auto exposure Speed Down for this run (to compare adaptation speeds).

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Data/WTATypes.h"
#include "InputCoreTypes.h"
#include "WTAPlayTest.generated.h"

class ACameraActor;
class AWTACharacter;
class AWTAPlayerController;

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
