// Walk the Archive - a talk or a class: a speaker with slides, in a venue the builders made.
//
// One per DT_Talks row, placed by the editor Python on the venue's speaker spot (the mesh spot__<venue>_f<yaw>).
// At BeginPlay it finds the venue's screens (the static meshes screen__<venue>, screen__<venue>_l, _r) and puts
// the title slide on them; the speaker stands at the spot - a MetaHuman reenactor (row Person) spawned here, or
// the staff member the row names (Staff), who walks over to the spot while the class runs and goes home after.
//
// The talk starts when the player sits on one of the venue's seats (seat__<venue>_*: the seat id's first word is
// the venue) and stops when they stand up; sitting again carries on from the slide it was on, or starts over
// once it has finished. Each slide stays up while the voice reads its line (VO_talk_<Clip>; OnClipFinished moves
// on), or for Seconds when there is no clip; the line's sentences run as captions on the HUD in time with the
// voice. If something else takes the voice (a card's Listen button) the talk waits and reads its line again when
// the voice is free. The speaker acts out a few talking gestures while speaking and idles between.
//
// The last slide heard through earns the Listener badge; a class then opens its quiz (AWTAPlayerController::
// OpenQuiz), and passing it earns the row's badge and a certificate.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Data/WTATypes.h"
#include "WTATalkActor.generated.h"

class AWTACharacter;
class AWTAStaffNPC;
class UAnimSequence;
class UMaterialInstanceDynamic;
class UStaticMeshComponent;
class UTexture2D;
class UWTAWaxAnimInstance;

UENUM(BlueprintType)
enum class EWTATalkState : uint8
{
	/** Nobody is listening; the title slide shows. */
	Idle,
	/** A slide is up and its line is being read. */
	Playing,
	/** Something else took the voice; the slide waits. */
	Waiting,
	/** The last line has been read; the last slide stays up. */
	Done
};

UCLASS(Blueprintable)
class WALKTHEARCHIVE_API AWTATalkActor : public AActor
{
	GENERATED_BODY()

public:
	AWTATalkActor();

	/** DT_Talks row (editor Python: talk_id). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FName TalkId;

	/** World yaw the speaker faces (editor Python: speaker_yaw, from the spot mesh's name). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	float SpeakerYaw = 0.f;

	/** The voice's kind for the slide lines: the clip is VO_talk_<Clip>. */
	static const FName VoiceKindTalk;
	/** The voice's kind for quiz questions: VO_quiz_<Clip>. */
	static const FName VoiceKindQuiz;

	/** Start from the first slide (or start over). */
	UFUNCTION(BlueprintCallable, Category = "WTA|Talk")
	void Start();

	/** Carry on from the current slide (Start when the talk is over or has not begun). */
	UFUNCTION(BlueprintCallable, Category = "WTA|Talk")
	void Resume();

	/** Stop reading; the slide stays where it is, the speaker idles. */
	UFUNCTION(BlueprintCallable, Category = "WTA|Talk")
	void Stop();

	/** Jump to a slide (0-based) and read its line; QA uses it to reach the end of a class quickly. */
	UFUNCTION(BlueprintCallable, Category = "WTA|Talk")
	void GoToSlide(int32 Index);

	UFUNCTION(BlueprintPure, Category = "WTA|Talk")
	EWTATalkState GetState() const { return State; }

	UFUNCTION(BlueprintPure, Category = "WTA|Talk")
	int32 GetSlideIndex() const { return SlideIndex; }

	UFUNCTION(BlueprintPure, Category = "WTA|Talk")
	int32 NumSlides() const { return Row.Slides.Num(); }

	UFUNCTION(BlueprintPure, Category = "WTA|Talk")
	bool HasRow() const { return bHasRow; }

	UFUNCTION(BlueprintPure, Category = "WTA|Talk")
	FName GetVenue() const { return Row.Venue; }

	/** The screens this talk puts its slides on (found at BeginPlay). */
	UFUNCTION(BlueprintPure, Category = "WTA|Talk")
	int32 NumScreens() const { return Screens.Num(); }

	/** The speaker on the spot: the spawned reenactor, or the staff NPC while it teaches (null before either). */
	UFUNCTION(BlueprintPure, Category = "WTA|Talk")
	AActor* GetSpeaker() const;

	/** Where the speaker's feet are. */
	UFUNCTION(BlueprintPure, Category = "WTA|Talk")
	FVector GetSpot() const { return GetActorLocation(); }

	/** The talk held in a venue, or null. */
	UFUNCTION(BlueprintCallable, Category = "WTA|Talk", meta = (WorldContext = "WorldContextObject"))
	static AWTATalkActor* FindForVenue(const UObject* WorldContextObject, FName Venue);

	/** The venue a seat belongs to: the first word of its id ("auditorium_r3s12" -> auditorium); none for a seat with no venue. */
	static FName VenueOfSeat(FName SeatId);

	/** How far the player must be before a talk nobody is sitting at goes back to its title slide, cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA|Talk")
	float ResetDistance = 3500.f;

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void Tick(float DeltaSeconds) override;

protected:
	/** Puts the slide's texture on every screen (the title slide for INDEX_NONE). */
	void ShowSlide(int32 Index);

	/** Reads the current slide's line, or starts its timer when there is no clip; runs the captions. */
	void ReadSlide();

	/** The next slide, or the end of the talk. */
	void Advance();

	/** The last line was read: badge, and the quiz for a class. */
	void Finish();

	/** Capture the venue's screens: dynamic unlit materials on each, kept for the slides. */
	void FindScreens();

	/** The speaker: spawn the row's Person here, or borrow the staff NPC. */
	void SetUpSpeaker();

	/** The speaker gestures (bSpeaking) or idles. */
	void SetSpeaking(bool bSpeaking);

	/** A gesture clip by action name (/Game/WTA/Characters/Common/Anims/Mocap/AS_WTA_<Action>), cached. */
	UAnimSequence* LoadAction(FName Action);

	/** The speaker's body animation instance (ours), or null. */
	UWTAWaxAnimInstance* SpeakerAnim() const;

	/** Bind to the player's seat changes once the player exists. */
	void BindPlayer();

	UFUNCTION()
	void HandleSeatChanged(AActor* Seat, bool bSeated);

	UFUNCTION()
	void HandleClipFinished(FName Kind, FName Id);

	UFUNCTION()
	void HandleVoiceChanged();

	/** Captions: the current line split into sentences, each shown for its share of the clip. */
	void StartCaptions(const FText& Line, float Seconds);
	void NextCaption();
	void ClearCaptions();

	/** The player is sitting on one of this venue's seats. */
	bool IsPlayerSeatedHere() const;

	FWTATalkRow Row;
	bool bHasRow = false;
	EWTATalkState State = EWTATalkState::Idle;
	int32 SlideIndex = INDEX_NONE;
	/** The clip being read for the current slide (none when the slide runs on its timer). */
	FName ReadingClip;
	FTimerHandle SlideTimer;
	FTimerHandle CaptionTimer;
	FTimerHandle GestureTimer;
	FTimerHandle QuizTimer;
	TArray<FString> Captions;
	int32 CaptionIndex = 0;
	float CaptionSeconds = 0.f;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> Screens;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UMaterialInstanceDynamic>> ScreenMaterials;

	UPROPERTY(Transient)
	TObjectPtr<UTexture2D> ShownSlide;

	/** The reenactor spawned for the row's Person (null when a staff member speaks). */
	UPROPERTY(Transient)
	TObjectPtr<AActor> Figure;

	/** The staff NPC teaching this class (null when a reenactor speaks). */
	UPROPERTY(Transient)
	TObjectPtr<AWTAStaffNPC> StaffSpeaker;

	UPROPERTY(Transient)
	TMap<FName, TObjectPtr<UAnimSequence>> Clips;

	TWeakObjectPtr<AWTACharacter> BoundPlayer;
	bool bSpeakingNow = false;
	int32 GestureIndex = 0;
	bool bEverStarted = false;
};
