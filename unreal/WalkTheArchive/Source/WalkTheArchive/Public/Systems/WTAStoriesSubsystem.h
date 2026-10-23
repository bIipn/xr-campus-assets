// Walk the Archive - Lost Stories: a visitor tells a story at the booth's mic; it is kept in their own voice,
// written down, and joins the story wall.
//
// Recording: the default microphone through Audio::FAudioCapture (AudioCaptureCore; the AudioCapture plugin, on by
// default, loads the platform's back end). The capture thread appends mono samples under a lock; Tick reads the
// peak for the meter and stops a take at MaxSeconds. Stop leaves the take waiting: ListenToTake plays it back,
// KeepTake writes <Saved>/Stories/New/<id>.wav (16-bit PCM, mono, the device's rate; quiet takes lifted to -3 dB)
// and <id>.json, DiscardTake throws it away.
//
// Writing down: whisper.cpp's whisper-cli (MIT; a ggml model such as ggml-base.bin) runs on the WAV in the
// background (one at a time) when it is found: UWTASettings::WhisperFolder, else the WTA_WHISPER environment
// variable, else <Project>/ThirdParty/whisper (Tools/win/get_whisper.ps1 fills it). Its JSON gives the spoken
// language and the timed lines: the transcript and the captions. Without whisper the story is kept unwritten and
// written down on a later start that has it.
//
// The wall: <Saved>/Stories/Wall holds the stories everyone sees. New ones wait in Stories/New until a librarian
// moves the two files into Wall (UWTASettings::bStoriesNeedReview; off, they go straight to Wall). The teller sees
// their own new stories on the wall for the rest of the visit.
//
// Listening: Play(Id) streams the WAV through a USoundWaveProcedural and steps the story's lines through the
// HUD's caption plate; walking out of the story's room (or Stop) ends it.

#pragma once

#include "CoreMinimal.h"
#include "HAL/CriticalSection.h"
#include "HAL/PlatformProcess.h"
#include "Subsystems/WorldSubsystem.h"
#include "WTAStoriesSubsystem.generated.h"

class UAudioComponent;
class USoundWaveProcedural;

namespace Audio { class FAudioCapture; }

/** One timed line of a story's transcript (whisper's segments), seconds from the start. */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAStoryLine
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	float From = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	float To = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FString Text;
};

/** A kept story: <Stories>/<New|Wall>/<Id>.wav and <Id>.json. */
USTRUCT(BlueprintType)
struct WALKTHEARCHIVE_API FWTAStory
{
	GENERATED_BODY()

	/** story_<yyyymmdd-hhmmss>. */
	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FString Id;

	/** What the teller called it; empty = the first words of the transcript (DisplayTitle). */
	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FString Title;

	/** The teller's first name, when they gave one. */
	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FString Teller;

	/** Local time it was recorded. */
	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FDateTime Recorded;

	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	float Seconds = 0.f;

	/** The spoken language whisper heard ("en", "es"); empty until written down. */
	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FString Language;

	/** True once whisper has written it down (Transcript and Lines). */
	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	bool bTranscribed = false;

	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FString Transcript;

	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	TArray<FWTAStoryLine> Lines;

	/** True when it is in Stories/Wall (a librarian has put it up). */
	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	bool bOnWall = false;

	/** True when it was told during this visit. */
	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	bool bThisVisit = false;

	/** The folder its two files are in. */
	UPROPERTY(BlueprintReadOnly, Category = "WTA")
	FString Folder;

	FString WavFile() const;
	FString JsonFile() const;

	/** Title, else the transcript's first sentence (cut at about 60 characters), else "A story told on <date>". */
	FText DisplayTitle() const;

	/** "Rosa · 22 October 2026 · 1:23" (the teller only when given). */
	FText Byline() const;
};

/** Where the booth is: Idle (ready to record), Recording, Take (a take waits: listen, keep, again, delete). */
UENUM(BlueprintType)
enum class EWTABoothState : uint8
{
	Idle,
	Recording,
	Take
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FWTAStoriesChanged);

UCLASS()
class WALKTHEARCHIVE_API UWTAStoriesSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category = "WTA|Stories", meta = (WorldContext = "WorldContextObject"))
	static UWTAStoriesSubsystem* Get(const UObject* WorldContextObject);

	/** <Saved>/Stories; New and Wall under it. */
	static FString StoriesDir();
	static FString NewDir();
	static FString WallDir();

	// --- Recording ---------------------------------------------------------------

	/** Opens the default microphone and starts a take (an earlier take waiting is thrown away). False when no
	    microphone opens. */
	UFUNCTION(BlueprintCallable, Category = "WTA|Stories")
	bool StartRecording();

	/** Ends the take: it waits for Keep, Listen, Again or Delete. A take under half a second is dropped. */
	UFUNCTION(BlueprintCallable, Category = "WTA|Stories")
	void StopRecording();

	UFUNCTION(BlueprintPure, Category = "WTA|Stories")
	EWTABoothState GetBoothState() const { return BoothState; }

	/** Seconds recorded so far (Recording) or the take's length (Take). */
	UFUNCTION(BlueprintPure, Category = "WTA|Stories")
	float GetTakeSeconds() const;

	/** The input level, 0..1, smoothed for a meter. */
	UFUNCTION(BlueprintPure, Category = "WTA|Stories")
	float GetLevel() const { return Level; }

	/** True when the take so far is all but silent (the microphone may be muted or blocked). */
	UFUNCTION(BlueprintPure, Category = "WTA|Stories")
	bool IsTakeSilent() const;

	/** The microphone's name, once one has opened. */
	UFUNCTION(BlueprintPure, Category = "WTA|Stories")
	FString GetDeviceName() const { return DeviceName; }

	/** Plays the waiting take back (again: stops). */
	UFUNCTION(BlueprintCallable, Category = "WTA|Stories")
	void ListenToTake();

	/** Keeps the waiting take: writes its WAV and JSON, starts writing it down. Returns the story's id (empty when
	    there was no take). Title and Teller may be empty. */
	UFUNCTION(BlueprintCallable, Category = "WTA|Stories")
	FString KeepTake(const FString& Title, const FString& Teller);

	/** Throws the waiting take away. */
	UFUNCTION(BlueprintCallable, Category = "WTA|Stories")
	void DiscardTake();

	/** QA and tools: a WAV file (16-bit PCM, any rate, mono or stereo) becomes the waiting take, as if recorded. */
	UFUNCTION(BlueprintCallable, Category = "WTA|Stories")
	bool LoadTakeFromWav(const FString& WavFile);

	// --- Stories -----------------------------------------------------------------

	/** The stories on the wall, newest first: Stories/Wall, and this visit's own from Stories/New. */
	UFUNCTION(BlueprintCallable, Category = "WTA|Stories")
	TArray<FWTAStory> GetWallStories() const;

	UFUNCTION(BlueprintCallable, Category = "WTA|Stories")
	bool FindStory(const FString& Id, FWTAStory& OutStory) const;

	/** Deletes a story told during this visit (its teller changed their mind). False for any other. */
	UFUNCTION(BlueprintCallable, Category = "WTA|Stories")
	bool DeleteOwnStory(const FString& Id);

	/** True while whisper is writing this one down (or it is queued to be). */
	UFUNCTION(BlueprintPure, Category = "WTA|Stories")
	bool IsWritingDown(const FString& Id) const;

	/** True when whisper-cli and a model were found. */
	UFUNCTION(BlueprintPure, Category = "WTA|Stories")
	bool CanWriteDown() const;

	/** whisper-cli's path and the model's ('' when not found). */
	void FindWhisper(FString& OutExe, FString& OutModel) const;

	/** Re-reads the folders (a librarian may have moved files) and tells the listeners. */
	UFUNCTION(BlueprintCallable, Category = "WTA|Stories")
	void Refresh();

	/** Fired when a story is kept, written down, deleted, or the folders were read again. */
	UPROPERTY(BlueprintAssignable, Category = "WTA|Stories")
	FWTAStoriesChanged OnStoriesChanged;

	/** Fired when the booth's state changes and when playback starts or ends. */
	UPROPERTY(BlueprintAssignable, Category = "WTA|Stories")
	FWTAStoriesChanged OnBoothChanged;

	// --- Listening ---------------------------------------------------------------

	/** Plays a story in the teller's voice with its lines as captions. False when its WAV will not load. */
	UFUNCTION(BlueprintCallable, Category = "WTA|Stories")
	bool Play(const FString& Id);

	UFUNCTION(BlueprintCallable, Category = "WTA|Stories")
	void StopPlayback();

	/** True while a story (Id) or the take (Id "take") plays; any when Id is empty. */
	UFUNCTION(BlueprintPure, Category = "WTA|Stories")
	bool IsPlaying(const FString& Id = TEXT("")) const;

	/** The caption showing now ('' when none). */
	UFUNCTION(BlueprintPure, Category = "WTA|Stories")
	FString GetCurrentCaption() const { return CurrentCaption; }

	/** Seconds into what is playing. */
	UFUNCTION(BlueprintPure, Category = "WTA|Stories")
	float GetPlaybackSeconds() const;

	// UTickableWorldSubsystem
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

protected:
	/** Reads one story's JSON (and notes whether the WAV is there). */
	static bool ReadStory(const FString& JsonFile, FWTAStory& Out);
	static bool WriteStory(const FWTAStory& Story);
	static bool WriteWav(const FString& File, const TArray<float>& Samples, int32 SampleRate);
	/** 16-bit PCM WAV -> mono floats; false for anything else. */
	static bool ReadWav(const FString& File, TArray<float>& OutSamples, int32& OutSampleRate);

	void ScanFolders();
	void CloseCapture();
	void QueueWritingDown(const FString& Id);
	void StartNextWritingDown();
	void PollWritingDown();
	void FinishWritingDown(const FString& InId, const FString& WhisperJson, bool bOk);
	void StartPlayback(const TArray<float>& Samples, int32 SampleRate, const FString& Id, const TArray<FWTAStoryLine>& Lines);
	void UpdateCaption();
	void SetBoothState(EWTABoothState NewState);

	EWTABoothState BoothState = EWTABoothState::Idle;

	// The capture: the device's thread appends under CaptureLock. Made on the first recording, deleted in Deinitialize.
	Audio::FAudioCapture* Capture = nullptr;
	FCriticalSection CaptureLock;
	TArray<float> CaptureSamples;
	int32 CaptureRate = 48000;
	float CapturePeak = 0.f;
	bool bCapturing = false;

	TArray<float> TakeSamples;
	int32 TakeRate = 48000;
	float RecordedSeconds = 0.f;
	float Level = 0.f;
	float TakePeak = 0.f;
	FString DeviceName;

	// Stories read from the folders, newest first.
	TArray<FWTAStory> Stories;
	TSet<FString> ThisVisit;

	// Writing down: one whisper at a time.
	TArray<FString> WriteQueue;
	FString WritingId;
	FProcHandle WritingProc;
	FString WritingOut;
	double WritingStarted = 0.0;
	double NextPoll = 0.0;

	// Playback.
	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> Player;

	UPROPERTY(Transient)
	TObjectPtr<USoundWaveProcedural> PlayerWave;

	FString PlayingId;
	TArray<FWTAStoryLine> PlayingLines;
	double PlayStarted = 0.0;
	float PlaySeconds = 0.f;
	FString CurrentCaption;
	FName PlayingRoom;
};
