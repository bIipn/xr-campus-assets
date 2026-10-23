// Walk the Archive - Lost Stories: record, keep, write down, list and play the visitors' stories.

#include "Systems/WTAStoriesSubsystem.h"
#include "AudioCaptureCore.h"
#include "Components/AudioComponent.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "Core/WTASettings.h"
#include "Core/WTAText.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMisc.h"
#include "HAL/PlatformTime.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "Sound/SoundWaveProcedural.h"
#include "Systems/WTARoomSubsystem.h"

namespace
{
	constexpr float MinTakeSeconds = 0.5f;
	constexpr double WriteDownTimeout = 900.0;
	/** A take whose loudest moment is under this (about -40 dBFS) heard next to nothing. */
	constexpr float SilentPeak = 0.01f;

	FString StoryIdFor(const FDateTime& When)
	{
		return FString::Printf(TEXT("story_%s"), *When.ToString(TEXT("%Y%m%d-%H%M%S")));
	}

	/** "1:23" */
	FString StoryClockText(float Seconds)
	{
		const int32 S = FMath::Max(0, FMath::RoundToInt(Seconds));
		return FString::Printf(TEXT("%d:%02d"), S / 60, S % 60);
	}

	/** The first sentence, cut at a word near MaxChars. */
	FString FirstWords(const FString& Text, int32 MaxChars)
	{
		FString T = Text.TrimStartAndEnd();
		for (int32 i = 8; i < T.Len(); ++i)
		{
			const TCHAR C = T[i];
			if (C == TEXT('.') || C == TEXT('?') || C == TEXT('!'))
			{
				T = T.Left(i + (C == TEXT('.') ? 0 : 1));
				break;
			}
		}
		if (T.Len() > MaxChars)
		{
			const int32 Space = T.Left(MaxChars).Find(TEXT(" "), ESearchCase::CaseSensitive, ESearchDir::FromEnd);
			T = T.Left(Space > MaxChars / 3 ? Space : MaxChars).TrimEnd() + TEXT("…");
		}
		return T;
	}

	/** whisper marks what is not speech in brackets: "[BLANK_AUDIO]", "(music)", "[Applause]". */
	bool IsNonSpeech(const FString& Line)
	{
		const FString T = Line.TrimStartAndEnd();
		return T.IsEmpty() || ((T.StartsWith(TEXT("[")) && T.EndsWith(TEXT("]"))) || (T.StartsWith(TEXT("(")) && T.EndsWith(TEXT(")"))));
	}

	uint32 Read32(const TArray<uint8>& B, int32 At)
	{
		return uint32(B[At]) | (uint32(B[At + 1]) << 8) | (uint32(B[At + 2]) << 16) | (uint32(B[At + 3]) << 24);
	}

	uint16 Read16(const TArray<uint8>& B, int32 At)
	{
		return uint16(B[At]) | uint16(uint16(B[At + 1]) << 8);
	}

	bool TagIs(const TArray<uint8>& B, int32 At, const char* Tag)
	{
		return At + 4 <= B.Num() && FMemory::Memcmp(B.GetData() + At, Tag, 4) == 0;
	}

	AWTAPlayerController* LocalController(const UWorld* World)
	{
		return World != nullptr ? Cast<AWTAPlayerController>(World->GetFirstPlayerController()) : nullptr;
	}
}

// ---------------------------------------------------------------------------
// FWTAStory
// ---------------------------------------------------------------------------

FString FWTAStory::WavFile() const
{
	return FPaths::Combine(Folder, Id + TEXT(".wav"));
}

FString FWTAStory::JsonFile() const
{
	return FPaths::Combine(Folder, Id + TEXT(".json"));
}

FText FWTAStory::DisplayTitle() const
{
	if (!Title.IsEmpty())
	{
		return FText::FromString(Title);
	}
	if (!Transcript.IsEmpty())
	{
		return FText::FromString(FirstWords(Transcript, 60));
	}
	return FText::Format(WTAText(TEXT("A story told on {0}")), WTADate(Recorded));
}

FText FWTAStory::Byline() const
{
	const FText When = WTADate(Recorded);
	const FText Length = FText::FromString(StoryClockText(Seconds));
	return Teller.IsEmpty()
		? FText::Format(WTAText(TEXT("{0} · {1}")), When, Length)
		: FText::Format(WTAText(TEXT("{0} · {1} · {2}")), FText::FromString(Teller), When, Length);
}

// ---------------------------------------------------------------------------
// Lifetime
// ---------------------------------------------------------------------------

UWTAStoriesSubsystem* UWTAStoriesSubsystem::Get(const UObject* WorldContextObject)
{
	if (WorldContextObject == nullptr || GEngine == nullptr)
	{
		return nullptr;
	}
	UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull);
	return World != nullptr ? World->GetSubsystem<UWTAStoriesSubsystem>() : nullptr;
}

FString UWTAStoriesSubsystem::StoriesDir()
{
	return FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Stories")));
}

FString UWTAStoriesSubsystem::NewDir()
{
	return FPaths::Combine(StoriesDir(), TEXT("New"));
}

FString UWTAStoriesSubsystem::WallDir()
{
	return FPaths::Combine(StoriesDir(), TEXT("Wall"));
}

bool UWTAStoriesSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	// Only where someone plays: the game, PIE, standalone. Never the editor's own world, so the editor never
	// opens a microphone.
	const UWorld* World = Cast<UWorld>(Outer);
	return World != nullptr && (World->WorldType == EWorldType::Game || World->WorldType == EWorldType::PIE);
}

void UWTAStoriesSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	ScanFolders();
	FString Exe, Model;
	FindWhisper(Exe, Model);
	int32 Unwritten = 0;
	for (const FWTAStory& Story : Stories)
	{
		if (!Story.bTranscribed)
		{
			++Unwritten;
			if (!Exe.IsEmpty())
			{
				WriteQueue.Add(Story.Id);
			}
		}
	}
	UE_LOG(LogWTA, Display, TEXT("WTA_STORY %d stories (%d not written down yet); whisper %s"), Stories.Num(), Unwritten,
		Exe.IsEmpty() ? TEXT("not found") : *FString::Printf(TEXT("%s with %s"), *Exe, *FPaths::GetCleanFilename(Model)));
}

void UWTAStoriesSubsystem::Deinitialize()
{
	StopPlayback();
	CloseCapture();
	delete Capture;
	Capture = nullptr;
	if (WritingProc.IsValid())
	{
		if (FPlatformProcess::IsProcRunning(WritingProc))
		{
			FPlatformProcess::TerminateProc(WritingProc, true);   // it starts again on the next visit
		}
		FPlatformProcess::CloseProc(WritingProc);
	}
	WritingId.Reset();
	WriteQueue.Reset();
	Super::Deinitialize();
}

TStatId UWTAStoriesSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UWTAStoriesSubsystem, STATGROUP_Tickables);
}

void UWTAStoriesSubsystem::SetBoothState(EWTABoothState NewState)
{
	if (BoothState != NewState)
	{
		BoothState = NewState;
		OnBoothChanged.Broadcast();
	}
}

// ---------------------------------------------------------------------------
// Recording
// ---------------------------------------------------------------------------

bool UWTAStoriesSubsystem::StartRecording()
{
	StopPlayback();
	TakeSamples.Reset();
	if (Capture == nullptr)
	{
		Capture = new Audio::FAudioCapture();
	}
	if (!Capture->IsStreamOpen())
	{
		Audio::FCaptureDeviceInfo Info;
		if (Capture->GetCaptureDeviceInfo(Info))
		{
			DeviceName = Info.DeviceName;
		}
		// The default device at its own rate and channels; samples arrive as 32-bit floats.
		Audio::FAudioCaptureDeviceParams Params;
		Audio::FOnAudioCaptureFunction OnCapture = [this](const void* InAudio, int32 NumFrames, int32 NumChannels, int32 SampleRate, double StreamTime, bool bOverflow)
		{
			const float* In = static_cast<const float*>(InAudio);
			if (In == nullptr || NumFrames <= 0 || NumChannels <= 0)
			{
				return;
			}
			FScopeLock Lock(&CaptureLock);
			if (!bCapturing)
			{
				return;
			}
			CaptureRate = SampleRate > 0 ? SampleRate : CaptureRate;
			const int32 Start = CaptureSamples.AddUninitialized(NumFrames);
			float Peak = 0.f;
			for (int32 Frame = 0; Frame < NumFrames; ++Frame)
			{
				float Sum = 0.f;
				for (int32 Channel = 0; Channel < NumChannels; ++Channel)
				{
					Sum += In[Frame * NumChannels + Channel];
				}
				const float Sample = Sum / NumChannels;
				CaptureSamples[Start + Frame] = Sample;
				Peak = FMath::Max(Peak, FMath::Abs(Sample));
			}
			CapturePeak = FMath::Max(CapturePeak, Peak);
		};
		if (!Capture->OpenAudioCaptureStream(Params, MoveTemp(OnCapture), 1024))
		{
			UE_LOG(LogWTA, Warning, TEXT("WTA_STORY no microphone opened (%s)"), DeviceName.IsEmpty() ? TEXT("no capture device") : *DeviceName);
			return false;
		}
	}
	{
		FScopeLock Lock(&CaptureLock);
		CaptureSamples.Reset();
		CaptureSamples.Reserve(48000 * 60);
		CapturePeak = 0.f;
		bCapturing = true;
	}
	if (!Capture->IsCapturing() && !Capture->StartStream())
	{
		UE_LOG(LogWTA, Warning, TEXT("WTA_STORY the microphone opened but would not start (%s)"), *DeviceName);
		CloseCapture();
		return false;
	}
	TakePeak = 0.f;
	RecordedSeconds = 0.f;
	Level = 0.f;
	SetBoothState(EWTABoothState::Recording);
	UE_LOG(LogWTA, Display, TEXT("WTA_STORY recording from %s"), DeviceName.IsEmpty() ? TEXT("the default microphone") : *DeviceName);
	return true;
}

void UWTAStoriesSubsystem::StopRecording()
{
	if (BoothState != EWTABoothState::Recording)
	{
		return;
	}
	{
		FScopeLock Lock(&CaptureLock);
		bCapturing = false;
		TakeSamples = MoveTemp(CaptureSamples);
		CaptureSamples.Reset();
		TakeRate = CaptureRate;
	}
	CloseCapture();
	TakePeak = 0.f;
	for (const float Sample : TakeSamples)
	{
		TakePeak = FMath::Max(TakePeak, FMath::Abs(Sample));
	}
	const float Seconds = TakeRate > 0 ? TakeSamples.Num() / float(TakeRate) : 0.f;
	UE_LOG(LogWTA, Display, TEXT("WTA_STORY take %.1f s at %d Hz, peak %.3f"), Seconds, TakeRate, TakePeak);
	if (Seconds < MinTakeSeconds)
	{
		TakeSamples.Reset();
		SetBoothState(EWTABoothState::Idle);
		return;
	}
	SetBoothState(EWTABoothState::Take);
}

void UWTAStoriesSubsystem::CloseCapture()
{
	{
		FScopeLock Lock(&CaptureLock);
		bCapturing = false;
	}
	if (Capture != nullptr && Capture->IsStreamOpen())
	{
		Capture->StopStream();
		Capture->CloseStream();
	}
}

float UWTAStoriesSubsystem::GetTakeSeconds() const
{
	if (BoothState == EWTABoothState::Recording)
	{
		return RecordedSeconds;
	}
	return TakeRate > 0 ? TakeSamples.Num() / float(TakeRate) : 0.f;
}

bool UWTAStoriesSubsystem::IsTakeSilent() const
{
	return TakePeak < SilentPeak;
}

void UWTAStoriesSubsystem::ListenToTake()
{
	if (IsPlaying(TEXT("take")))
	{
		StopPlayback();
		return;
	}
	if (BoothState == EWTABoothState::Take && TakeSamples.Num() > 0)
	{
		StartPlayback(TakeSamples, TakeRate, TEXT("take"), TArray<FWTAStoryLine>());
	}
}

void UWTAStoriesSubsystem::DiscardTake()
{
	if (IsPlaying(TEXT("take")))
	{
		StopPlayback();
	}
	if (BoothState == EWTABoothState::Recording)
	{
		CloseCapture();
	}
	TakeSamples.Reset();
	TakePeak = 0.f;
	SetBoothState(EWTABoothState::Idle);
}

bool UWTAStoriesSubsystem::LoadTakeFromWav(const FString& WavFile)
{
	TArray<float> Samples;
	int32 Rate = 0;
	if (BoothState == EWTABoothState::Recording || !ReadWav(WavFile, Samples, Rate) || Samples.Num() < Rate * MinTakeSeconds)
	{
		return false;
	}
	StopPlayback();
	TakeSamples = MoveTemp(Samples);
	TakeRate = Rate;
	TakePeak = 0.f;
	for (const float Sample : TakeSamples)
	{
		TakePeak = FMath::Max(TakePeak, FMath::Abs(Sample));
	}
	SetBoothState(EWTABoothState::Take);
	return true;
}

FString UWTAStoriesSubsystem::KeepTake(const FString& Title, const FString& Teller)
{
	if (BoothState != EWTABoothState::Take || TakeSamples.Num() == 0 || TakeRate <= 0)
	{
		return FString();
	}
	StopPlayback();
	const bool bReview = UWTASettings::Get()->bStoriesNeedReview;
	FWTAStory Story;
	Story.Recorded = FDateTime::Now();
	Story.Id = StoryIdFor(Story.Recorded);
	Story.Folder = bReview ? NewDir() : WallDir();
	for (int32 Suffix = 2; FPaths::FileExists(Story.JsonFile()) || FPaths::FileExists(Story.WavFile()); ++Suffix)
	{
		Story.Id = FString::Printf(TEXT("%s-%d"), *StoryIdFor(Story.Recorded), Suffix);
	}
	Story.Title = Title.TrimStartAndEnd().Left(80);
	Story.Teller = Teller.TrimStartAndEnd().Left(40);
	Story.Seconds = TakeSamples.Num() / float(TakeRate);
	Story.bOnWall = !bReview;
	Story.bThisVisit = true;

	// A quiet take is lifted so its loudest moment sits at -3 dB (at most 12 dB up, so a hiss stays a hiss).
	if (TakePeak > 0.001f && TakePeak < 0.7f)
	{
		const float Gain = FMath::Min(0.7f / TakePeak, 4.f);
		for (float& Sample : TakeSamples)
		{
			Sample *= Gain;
		}
	}
	IFileManager::Get().MakeDirectory(*Story.Folder, true);
	if (!WriteWav(Story.WavFile(), TakeSamples, TakeRate) || !WriteStory(Story))
	{
		UE_LOG(LogWTA, Warning, TEXT("WTA_STORY could not write %s"), *Story.WavFile());
		return FString();
	}
	ThisVisit.Add(Story.Id);
	Stories.Insert(Story, 0);
	TakeSamples.Reset();
	TakePeak = 0.f;
	SetBoothState(EWTABoothState::Idle);
	UE_LOG(LogWTA, Display, TEXT("WTA_STORY kept %s (%.1f s) in %s"), *Story.Id, Story.Seconds, *Story.Folder);
	QueueWritingDown(Story.Id);
	OnStoriesChanged.Broadcast();
	return Story.Id;
}

// ---------------------------------------------------------------------------
// Files
// ---------------------------------------------------------------------------

bool UWTAStoriesSubsystem::WriteWav(const FString& File, const TArray<float>& Samples, int32 SampleRate)
{
	const uint32 DataBytes = uint32(Samples.Num()) * 2u;
	TArray<uint8> Bytes;
	Bytes.Reserve(44 + DataBytes);
	auto Put32 = [&Bytes](uint32 V) { Bytes.Add(V & 0xff); Bytes.Add((V >> 8) & 0xff); Bytes.Add((V >> 16) & 0xff); Bytes.Add((V >> 24) & 0xff); };
	auto Put16 = [&Bytes](uint16 V) { Bytes.Add(V & 0xff); Bytes.Add((V >> 8) & 0xff); };
	auto PutTag = [&Bytes](const char* Tag) { Bytes.Append(reinterpret_cast<const uint8*>(Tag), 4); };
	PutTag("RIFF");
	Put32(36u + DataBytes);
	PutTag("WAVE");
	PutTag("fmt ");
	Put32(16);
	Put16(1);                                   // PCM
	Put16(1);                                   // mono
	Put32(uint32(SampleRate));
	Put32(uint32(SampleRate) * 2u);             // bytes a second
	Put16(2);                                   // bytes a frame
	Put16(16);                                  // bits a sample
	PutTag("data");
	Put32(DataBytes);
	for (const float Sample : Samples)
	{
		const int16 Value = int16(FMath::Clamp(FMath::RoundToInt(Sample * 32767.f), -32768, 32767));
		Put16(uint16(Value));
	}
	return FFileHelper::SaveArrayToFile(Bytes, *File);
}

bool UWTAStoriesSubsystem::ReadWav(const FString& File, TArray<float>& OutSamples, int32& OutSampleRate)
{
	TArray<uint8> B;
	if (!FFileHelper::LoadFileToArray(B, *File) || B.Num() < 44 || !TagIs(B, 0, "RIFF") || !TagIs(B, 8, "WAVE"))
	{
		return false;
	}
	int32 Format = 0, Channels = 0, Rate = 0, Bits = 0;
	int32 DataAt = INDEX_NONE, DataSize = 0;
	int32 Pos = 12;
	while (Pos + 8 <= B.Num())
	{
		const uint32 Size = Read32(B, Pos + 4);
		if (TagIs(B, Pos, "fmt ") && Pos + 24 <= B.Num())
		{
			Format = Read16(B, Pos + 8);
			Channels = Read16(B, Pos + 10);
			Rate = int32(Read32(B, Pos + 12));
			Bits = Read16(B, Pos + 22);
			if (Format == 0xFFFE && Size >= 40 && Pos + 34 <= B.Num())
			{
				Format = Read16(B, Pos + 32);       // WAVE_FORMAT_EXTENSIBLE: the sub format's first two bytes
			}
		}
		else if (TagIs(B, Pos, "data"))
		{
			DataAt = Pos + 8;
			DataSize = int32(FMath::Min<int64>(Size, B.Num() - DataAt));
			break;
		}
		Pos += 8 + int32(Size) + int32(Size & 1u);
	}
	if (DataAt == INDEX_NONE || Channels <= 0 || Rate <= 0 || !((Format == 1 && Bits == 16) || (Format == 3 && Bits == 32)))
	{
		return false;
	}
	const int32 BytesPerSample = Bits / 8;
	const int32 Frames = DataSize / (BytesPerSample * Channels);
	OutSamples.SetNumUninitialized(Frames);
	const uint8* Data = B.GetData() + DataAt;
	for (int32 Frame = 0; Frame < Frames; ++Frame)
	{
		float Sum = 0.f;
		for (int32 Channel = 0; Channel < Channels; ++Channel)
		{
			const uint8* At = Data + (Frame * Channels + Channel) * BytesPerSample;
			if (Format == 1)
			{
				Sum += int16(uint16(At[0]) | uint16(uint16(At[1]) << 8)) / 32768.f;
			}
			else
			{
				float Value;
				FMemory::Memcpy(&Value, At, sizeof(float));
				Sum += Value;
			}
		}
		OutSamples[Frame] = Sum / Channels;
	}
	OutSampleRate = Rate;
	return Frames > 0;
}

bool UWTAStoriesSubsystem::ReadStory(const FString& JsonFile, FWTAStory& Out)
{
	FString Text;
	if (!FFileHelper::LoadFileToString(Text, *JsonFile))
	{
		return false;
	}
	TSharedPtr<FJsonObject> Root;
	const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Text);
	if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
	{
		UE_LOG(LogWTA, Warning, TEXT("WTA_STORY %s is not JSON"), *JsonFile);
		return false;
	}
	Out = FWTAStory();
	Out.Id = FPaths::GetBaseFilename(JsonFile);
	Out.Folder = FPaths::GetPath(JsonFile);
	Root->TryGetStringField(TEXT("title"), Out.Title);
	Root->TryGetStringField(TEXT("teller"), Out.Teller);
	FString When;
	if (!Root->TryGetStringField(TEXT("recorded"), When) || !FDateTime::ParseIso8601(*When, Out.Recorded))
	{
		Out.Recorded = IFileManager::Get().GetTimeStamp(*JsonFile);
	}
	double Seconds = 0.0;
	Root->TryGetNumberField(TEXT("seconds"), Seconds);
	Out.Seconds = float(Seconds);
	Root->TryGetStringField(TEXT("language"), Out.Language);
	Root->TryGetBoolField(TEXT("transcribed"), Out.bTranscribed);
	Root->TryGetStringField(TEXT("transcript"), Out.Transcript);
	const TArray<TSharedPtr<FJsonValue>>* Lines = nullptr;
	if (Root->TryGetArrayField(TEXT("lines"), Lines) && Lines != nullptr)
	{
		for (const TSharedPtr<FJsonValue>& Value : *Lines)
		{
			const TSharedPtr<FJsonObject> Line = Value.IsValid() ? Value->AsObject() : nullptr;
			if (!Line.IsValid())
			{
				continue;
			}
			FWTAStoryLine Entry;
			double From = 0.0, To = 0.0;
			Line->TryGetNumberField(TEXT("from"), From);
			Line->TryGetNumberField(TEXT("to"), To);
			Line->TryGetStringField(TEXT("text"), Entry.Text);
			Entry.From = float(From);
			Entry.To = float(To);
			Out.Lines.Add(Entry);
		}
	}
	return true;
}

bool UWTAStoriesSubsystem::WriteStory(const FWTAStory& Story)
{
	const TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("id"), Story.Id);
	Root->SetStringField(TEXT("title"), Story.Title);
	Root->SetStringField(TEXT("teller"), Story.Teller);
	Root->SetStringField(TEXT("recorded"), Story.Recorded.ToString(TEXT("%Y-%m-%dT%H:%M:%S")));   // local time, no zone
	Root->SetNumberField(TEXT("seconds"), FMath::RoundToFloat(Story.Seconds * 10.f) / 10.f);
	Root->SetStringField(TEXT("language"), Story.Language);
	Root->SetBoolField(TEXT("transcribed"), Story.bTranscribed);
	Root->SetStringField(TEXT("transcript"), Story.Transcript);
	TArray<TSharedPtr<FJsonValue>> Lines;
	for (const FWTAStoryLine& Line : Story.Lines)
	{
		const TSharedRef<FJsonObject> Entry = MakeShared<FJsonObject>();
		Entry->SetNumberField(TEXT("from"), FMath::RoundToFloat(Line.From * 100.f) / 100.f);
		Entry->SetNumberField(TEXT("to"), FMath::RoundToFloat(Line.To * 100.f) / 100.f);
		Entry->SetStringField(TEXT("text"), Line.Text);
		Lines.Add(MakeShared<FJsonValueObject>(Entry));
	}
	Root->SetArrayField(TEXT("lines"), Lines);
	Root->SetStringField(TEXT("campus"), UWTASettings::Get()->CampusTitle);
	FString Text;
	const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Text);
	if (!FJsonSerializer::Serialize(Root, Writer))
	{
		return false;
	}
	return FFileHelper::SaveStringToFile(Text, *Story.JsonFile(), FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
}

void UWTAStoriesSubsystem::ScanFolders()
{
	TArray<FWTAStory> Found;
	for (const FString& Dir : { WallDir(), NewDir() })
	{
		const bool bWall = Dir == WallDir();
		TArray<FString> Names;
		IFileManager::Get().FindFiles(Names, *FPaths::Combine(Dir, TEXT("*.json")), true, false);
		TSet<FString> Seen;
		for (const FString& Name : Names)
		{
			FWTAStory Story;
			if (!ReadStory(FPaths::Combine(Dir, Name), Story) || !FPaths::FileExists(Story.WavFile()))
			{
				continue;
			}
			Story.bOnWall = bWall;
			Story.bThisVisit = ThisVisit.Contains(Story.Id);
			Seen.Add(Story.Id);
			Found.Add(Story);
		}
		// A recording dropped in on its own (an archive's old interview): it gets a card of its own, named after the
		// file, and is written down like any other.
		TArray<FString> Wavs;
		IFileManager::Get().FindFiles(Wavs, *FPaths::Combine(Dir, TEXT("*.wav")), true, false);
		for (const FString& Wav : Wavs)
		{
			const FString Id = FPaths::GetBaseFilename(Wav);
			if (Seen.Contains(Id))
			{
				continue;
			}
			TArray<float> Samples;
			int32 Rate = 0;
			if (!ReadWav(FPaths::Combine(Dir, Wav), Samples, Rate))
			{
				UE_LOG(LogWTA, Warning, TEXT("WTA_STORY %s: only 16-bit PCM or 32-bit float WAV files play here"), *Wav);
				continue;
			}
			FWTAStory Story;
			Story.Id = Id;
			Story.Folder = Dir;
			Story.Title = Id.Replace(TEXT("_"), TEXT(" ")).Replace(TEXT("-"), TEXT(" ")).TrimStartAndEnd();
			Story.Recorded = IFileManager::Get().GetTimeStamp(*FPaths::Combine(Dir, Wav));
			Story.Seconds = Samples.Num() / float(FMath::Max(Rate, 1));
			Story.bOnWall = bWall;
			if (WriteStory(Story))
			{
				Found.Add(Story);
			}
		}
	}
	Found.Sort([](const FWTAStory& A, const FWTAStory& B) { return A.Recorded > B.Recorded; });
	Stories = MoveTemp(Found);
}

void UWTAStoriesSubsystem::Refresh()
{
	ScanFolders();
	if (CanWriteDown())
	{
		for (const FWTAStory& Story : Stories)
		{
			if (!Story.bTranscribed && Story.Id != WritingId && !WriteQueue.Contains(Story.Id))
			{
				WriteQueue.Add(Story.Id);
			}
		}
	}
	OnStoriesChanged.Broadcast();
}

TArray<FWTAStory> UWTAStoriesSubsystem::GetWallStories() const
{
	TArray<FWTAStory> Out;
	for (const FWTAStory& Story : Stories)
	{
		if (Story.bOnWall || Story.bThisVisit)
		{
			Out.Add(Story);
		}
	}
	return Out;
}

bool UWTAStoriesSubsystem::FindStory(const FString& Id, FWTAStory& OutStory) const
{
	for (const FWTAStory& Story : Stories)
	{
		if (Story.Id == Id)
		{
			OutStory = Story;
			return true;
		}
	}
	return false;
}

bool UWTAStoriesSubsystem::DeleteOwnStory(const FString& Id)
{
	const int32 Index = Stories.IndexOfByPredicate([&Id](const FWTAStory& Story) { return Story.Id == Id; });
	if (Index == INDEX_NONE || !ThisVisit.Contains(Id))
	{
		return false;
	}
	if (IsPlaying(Id))
	{
		StopPlayback();
	}
	if (WritingId == Id && WritingProc.IsValid())
	{
		FPlatformProcess::TerminateProc(WritingProc, true);
		FPlatformProcess::CloseProc(WritingProc);
		WritingId.Reset();
	}
	WriteQueue.Remove(Id);
	const FWTAStory Story = Stories[Index];
	IFileManager::Get().Delete(*Story.WavFile(), false, true, true);
	IFileManager::Get().Delete(*Story.JsonFile(), false, true, true);
	Stories.RemoveAt(Index);
	ThisVisit.Remove(Id);
	UE_LOG(LogWTA, Display, TEXT("WTA_STORY deleted %s (its teller's choice)"), *Id);
	OnStoriesChanged.Broadcast();
	return true;
}

// ---------------------------------------------------------------------------
// Writing down (whisper.cpp)
// ---------------------------------------------------------------------------

void UWTAStoriesSubsystem::FindWhisper(FString& OutExe, FString& OutModel) const
{
	OutExe.Reset();
	OutModel.Reset();
	TArray<FString> Folders;
	if (!UWTASettings::Get()->WhisperFolder.IsEmpty())
	{
		Folders.Add(UWTASettings::Get()->WhisperFolder);
	}
	const FString FromEnvironment = FPlatformMisc::GetEnvironmentVariable(TEXT("WTA_WHISPER"));
	if (!FromEnvironment.IsEmpty())
	{
		Folders.Add(FromEnvironment);
	}
	Folders.Add(FPaths::Combine(FPaths::ProjectDir(), TEXT("ThirdParty"), TEXT("whisper")));
#if PLATFORM_WINDOWS
	const FString ExeName = TEXT("whisper-cli.exe");
#else
	const FString ExeName = TEXT("whisper-cli");
#endif
	for (const FString& Raw : Folders)
	{
		const FString Folder = FPaths::ConvertRelativePathToFull(Raw);
		FString Exe;
		for (const FString& Candidate : { FPaths::Combine(Folder, ExeName), FPaths::Combine(Folder, TEXT("bin"), TEXT("Release"), ExeName),
			FPaths::Combine(Folder, TEXT("Release"), ExeName), FPaths::Combine(Folder, TEXT("bin"), ExeName) })
		{
			if (FPaths::FileExists(Candidate))
			{
				Exe = Candidate;
				break;
			}
		}
		if (Exe.IsEmpty())
		{
			continue;
		}
		for (const FString& Dir : { Folder, FPaths::Combine(Folder, TEXT("models")) })
		{
			const FString Base = FPaths::Combine(Dir, TEXT("ggml-base.bin"));
			if (FPaths::FileExists(Base))
			{
				OutExe = Exe;
				OutModel = Base;
				return;
			}
			TArray<FString> Models;
			IFileManager::Get().FindFiles(Models, *FPaths::Combine(Dir, TEXT("ggml-*.bin")), true, false);
			if (Models.Num() > 0)
			{
				Models.Sort();
				OutExe = Exe;
				OutModel = FPaths::Combine(Dir, Models[0]);
				return;
			}
		}
	}
}

bool UWTAStoriesSubsystem::CanWriteDown() const
{
	FString Exe, Model;
	FindWhisper(Exe, Model);
	return !Exe.IsEmpty();
}

bool UWTAStoriesSubsystem::IsWritingDown(const FString& Id) const
{
	return WritingId == Id || WriteQueue.Contains(Id);
}

void UWTAStoriesSubsystem::QueueWritingDown(const FString& Id)
{
	if (CanWriteDown() && WritingId != Id && !WriteQueue.Contains(Id))
	{
		WriteQueue.Add(Id);
		StartNextWritingDown();
	}
}

void UWTAStoriesSubsystem::StartNextWritingDown()
{
	while (WritingId.IsEmpty() && WriteQueue.Num() > 0)
	{
		const FString Id = WriteQueue[0];
		WriteQueue.RemoveAt(0);
		FWTAStory Story;
		if (!FindStory(Id, Story) || !FPaths::FileExists(Story.WavFile()))
		{
			continue;
		}
		FString Exe, Model;
		FindWhisper(Exe, Model);
		if (Exe.IsEmpty())
		{
			WriteQueue.Reset();
			return;
		}
		const FString WorkDir = FPaths::ConvertRelativePathToFull(FPaths::Combine(StoriesDir(), TEXT("Work")));
		IFileManager::Get().MakeDirectory(*WorkDir, true);
		WritingOut = FPaths::Combine(WorkDir, Id);                                  // whisper adds .json
		IFileManager::Get().Delete(*(WritingOut + TEXT(".json")), false, true, true);
		const int32 Threads = FMath::Clamp(FPlatformMisc::NumberOfCoresIncludingHyperthreads() / 2, 2, 8);
		const FString Args = FString::Printf(TEXT("-m \"%s\" -f \"%s\" -l auto -oj -of \"%s\" -np -t %d"),
			*Model, *FPaths::ConvertRelativePathToFull(Story.WavFile()), *WritingOut, Threads);
		uint32 ProcessId = 0;
		// Below normal priority: the campus keeps its frame rate while the story is written down.
		WritingProc = FPlatformProcess::CreateProc(*Exe, *Args, false, true, true, &ProcessId, -1, *FPaths::GetPath(Exe), nullptr, nullptr);
		if (!WritingProc.IsValid())
		{
			UE_LOG(LogWTA, Warning, TEXT("WTA_STORY could not start %s"), *Exe);
			WriteQueue.Reset();
			return;
		}
		WritingId = Id;
		WritingStarted = FPlatformTime::Seconds();
		UE_LOG(LogWTA, Display, TEXT("WTA_STORY writing down %s (%.0f s) with %s"), *Id, Story.Seconds, *FPaths::GetCleanFilename(Model));
		OnStoriesChanged.Broadcast();
	}
}

void UWTAStoriesSubsystem::PollWritingDown()
{
	if (WritingId.IsEmpty())
	{
		if (WriteQueue.Num() > 0)
		{
			StartNextWritingDown();
		}
		return;
	}
	const double Now = FPlatformTime::Seconds();
	if (Now < NextPoll)
	{
		return;
	}
	NextPoll = Now + 0.25;
	if (FPlatformProcess::IsProcRunning(WritingProc))
	{
		if (Now - WritingStarted > WriteDownTimeout)
		{
			FPlatformProcess::TerminateProc(WritingProc, true);
			FPlatformProcess::CloseProc(WritingProc);
			FinishWritingDown(WritingId, FString(), false);
		}
		return;
	}
	int32 ReturnCode = -1;
	FPlatformProcess::GetProcReturnCode(WritingProc, &ReturnCode);
	FPlatformProcess::CloseProc(WritingProc);
	FString Json;
	const bool bRead = FFileHelper::LoadFileToString(Json, *(WritingOut + TEXT(".json")));
	if (ReturnCode != 0)
	{
		UE_LOG(LogWTA, Warning, TEXT("WTA_STORY whisper ended with %d on %s"), ReturnCode, *WritingId);
	}
	FinishWritingDown(WritingId, Json, bRead);
}

void UWTAStoriesSubsystem::FinishWritingDown(const FString& InId, const FString& WhisperJson, bool bOk)
{
	const FString Id = InId;                                     // the callers pass WritingId itself, emptied next
	WritingId.Reset();
	IFileManager::Get().Delete(*(WritingOut + TEXT(".json")), false, true, true);
	FWTAStory* Story = Stories.FindByPredicate([&Id](const FWTAStory& S) { return S.Id == Id; });
	TSharedPtr<FJsonObject> Root;
	if (bOk && Story != nullptr)
	{
		const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(WhisperJson);
		bOk = FJsonSerializer::Deserialize(Reader, Root) && Root.IsValid();
	}
	if (bOk && Story != nullptr)
	{
		const TSharedPtr<FJsonObject>* Result = nullptr;
		if (Root->TryGetObjectField(TEXT("result"), Result) && Result != nullptr)
		{
			(*Result)->TryGetStringField(TEXT("language"), Story->Language);
		}
		Story->Lines.Reset();
		TArray<FString> Words;
		const TArray<TSharedPtr<FJsonValue>>* Segments = nullptr;
		if (Root->TryGetArrayField(TEXT("transcription"), Segments) && Segments != nullptr)
		{
			for (const TSharedPtr<FJsonValue>& Value : *Segments)
			{
				const TSharedPtr<FJsonObject> Segment = Value.IsValid() ? Value->AsObject() : nullptr;
				if (!Segment.IsValid())
				{
					continue;
				}
				FWTAStoryLine Line;
				Segment->TryGetStringField(TEXT("text"), Line.Text);
				Line.Text = Line.Text.TrimStartAndEnd();
				if (IsNonSpeech(Line.Text))
				{
					continue;
				}
				const TSharedPtr<FJsonObject>* Offsets = nullptr;
				if (Segment->TryGetObjectField(TEXT("offsets"), Offsets) && Offsets != nullptr)
				{
					double From = 0.0, To = 0.0;
					(*Offsets)->TryGetNumberField(TEXT("from"), From);
					(*Offsets)->TryGetNumberField(TEXT("to"), To);
					Line.From = float(From / 1000.0);
					Line.To = float(To / 1000.0);
				}
				Words.Add(Line.Text);
				Story->Lines.Add(Line);
			}
		}
		Story->Transcript = FString::Join(Words, TEXT(" "));
		Story->bTranscribed = true;
		WriteStory(*Story);
		UE_LOG(LogWTA, Display, TEXT("WTA_STORY written down %s: %d lines, language '%s', %d characters"), *Id, Story->Lines.Num(),
			*Story->Language, Story->Transcript.Len());
	}
	else
	{
		UE_LOG(LogWTA, Warning, TEXT("WTA_STORY could not write down %s"), *Id);
	}
	OnStoriesChanged.Broadcast();
	StartNextWritingDown();
}

// ---------------------------------------------------------------------------
// Listening
// ---------------------------------------------------------------------------

bool UWTAStoriesSubsystem::Play(const FString& Id)
{
	FWTAStory Story;
	if (!FindStory(Id, Story))
	{
		return false;
	}
	TArray<float> Samples;
	int32 Rate = 0;
	if (!ReadWav(Story.WavFile(), Samples, Rate))
	{
		UE_LOG(LogWTA, Warning, TEXT("WTA_STORY could not read %s"), *Story.WavFile());
		return false;
	}
	StartPlayback(Samples, Rate, Id, Story.Lines);
	return Player != nullptr;
}

void UWTAStoriesSubsystem::StartPlayback(const TArray<float>& Samples, int32 SampleRate, const FString& Id, const TArray<FWTAStoryLine>& Lines)
{
	StopPlayback();
	UWorld* World = GetWorld();
	if (World == nullptr || Samples.Num() == 0 || SampleRate <= 0)
	{
		return;
	}
	USoundWaveProcedural* Wave = NewObject<USoundWaveProcedural>(this);
	Wave->SetSampleRate(SampleRate);
	Wave->NumChannels = 1;
	Wave->SoundGroup = SOUNDGROUP_Voice;
	Wave->bLooping = false;
	// 16-bit PCM, queued a second at a time.
	TArray<int16> Chunk;
	for (int32 Start = 0; Start < Samples.Num(); Start += SampleRate)
	{
		const int32 Count = FMath::Min(SampleRate, Samples.Num() - Start);
		Chunk.SetNumUninitialized(Count);
		for (int32 i = 0; i < Count; ++i)
		{
			Chunk[i] = int16(FMath::Clamp(FMath::RoundToInt(Samples[Start + i] * 32767.f), -32768, 32767));
		}
		Wave->QueueAudio(reinterpret_cast<const uint8*>(Chunk.GetData()), Count * int32(sizeof(int16)));
	}
	Player = UGameplayStatics::CreateSound2D(World, Wave, 1.f, 1.f, 0.f, nullptr, false, false);
	if (Player == nullptr)
	{
		return;
	}
	Player->Play();
	PlayerWave = Wave;
	PlayingId = Id;
	PlayingLines = Lines;
	PlayStarted = FPlatformTime::Seconds();
	PlaySeconds = Samples.Num() / float(SampleRate);
	const UWTARoomSubsystem* Rooms = UWTARoomSubsystem::Get(this);
	PlayingRoom = Rooms != nullptr ? Rooms->GetCurrentRoom() : NAME_None;
	CurrentCaption.Reset();
	UE_LOG(LogWTA, Display, TEXT("WTA_STORY playing %s (%.1f s, %d lines)"), *Id, PlaySeconds, Lines.Num());
	OnBoothChanged.Broadcast();
}

void UWTAStoriesSubsystem::StopPlayback()
{
	const bool bWasPlaying = Player != nullptr;
	if (Player != nullptr)
	{
		Player->Stop();
		Player->DestroyComponent();
	}
	Player = nullptr;
	PlayerWave = nullptr;
	PlayingId.Reset();
	PlayingLines.Reset();
	if (!CurrentCaption.IsEmpty())
	{
		CurrentCaption.Reset();
		if (AWTAPlayerController* PC = LocalController(GetWorld()))
		{
			PC->ShowCaption(FText::GetEmpty());
		}
	}
	if (bWasPlaying)
	{
		OnBoothChanged.Broadcast();
	}
}

bool UWTAStoriesSubsystem::IsPlaying(const FString& Id) const
{
	return Player != nullptr && (Id.IsEmpty() || PlayingId == Id);
}

float UWTAStoriesSubsystem::GetPlaybackSeconds() const
{
	return Player != nullptr ? float(FPlatformTime::Seconds() - PlayStarted) : 0.f;
}

void UWTAStoriesSubsystem::UpdateCaption()
{
	const float T = GetPlaybackSeconds();
	FString Line;
	for (const FWTAStoryLine& Entry : PlayingLines)
	{
		if (T >= Entry.From && T < Entry.To + 0.4f)
		{
			Line = Entry.Text;                                   // the latest line that has begun
		}
	}
	if (Line != CurrentCaption)
	{
		CurrentCaption = Line;
		if (AWTAPlayerController* PC = LocalController(GetWorld()))
		{
			PC->ShowCaption(FText::FromString(Line));
		}
	}
}

// ---------------------------------------------------------------------------
// Tick
// ---------------------------------------------------------------------------

void UWTAStoriesSubsystem::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	if (BoothState == EWTABoothState::Recording)
	{
		float Peak = 0.f;
		int32 Samples = 0;
		int32 Rate = 48000;
		{
			FScopeLock Lock(&CaptureLock);
			Peak = CapturePeak;
			CapturePeak = 0.f;
			Samples = CaptureSamples.Num();
			Rate = CaptureRate;
		}
		TakePeak = FMath::Max(TakePeak, Peak);
		RecordedSeconds = Samples / float(FMath::Max(Rate, 1));
		// The meter on a decibel scale (-50 dB empty, 0 dB full): up at once, down at 1.5 a second.
		const float Decibels = 20.f * FMath::LogX(10.f, FMath::Max(Peak, 1e-5f));
		const float Target = FMath::Clamp((Decibels + 50.f) / 50.f, 0.f, 1.f);
		Level = Target > Level ? Target : FMath::Max(Target, Level - DeltaTime * 1.5f);
		if (RecordedSeconds >= FMath::Max(UWTASettings::Get()->StoryMaxSeconds, 10.f))
		{
			StopRecording();
		}
	}
	else
	{
		Level = FMath::Max(0.f, Level - DeltaTime * 2.f);
	}

	if (Player != nullptr)
	{
		const UWTARoomSubsystem* Rooms = UWTARoomSubsystem::Get(this);
		const bool bWalkedOut = PlayingRoom != NAME_None && Rooms != nullptr && Rooms->GetCurrentRoom() != NAME_None && Rooms->GetCurrentRoom() != PlayingRoom;
		if (GetPlaybackSeconds() > PlaySeconds + 0.3f || bWalkedOut)
		{
			StopPlayback();
		}
		else
		{
			UpdateCaption();
		}
	}

	PollWritingDown();
}
