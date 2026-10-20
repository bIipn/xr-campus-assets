// Walk the Archive - the museum reads a card aloud for you.

#include "Systems/WTAVoiceSubsystem.h"
#include "Components/AudioComponent.h"
#include "Core/WTALog.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "UObject/SoftObjectPath.h"

UWTAVoiceSubsystem* UWTAVoiceSubsystem::Get(const UObject* WorldContextObject)
{
	const UWorld* World = GEngine != nullptr ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull) : nullptr;
	const UGameInstance* GameInstance = World != nullptr ? World->GetGameInstance() : nullptr;
	return GameInstance != nullptr ? GameInstance->GetSubsystem<UWTAVoiceSubsystem>() : nullptr;
}

FString UWTAVoiceSubsystem::ClipPath(FName Kind, FName Id)
{
	if (Kind.IsNone() || Id.IsNone())
	{
		return FString();
	}
	const FString Name = FString::Printf(TEXT("VO_%s_%s"), *Kind.ToString(), *Id.ToString().Replace(TEXT("-"), TEXT("_")));
	return FString::Printf(TEXT("/Game/WTA/Audio/%s.%s"), *Name, *Name);
}

bool UWTAVoiceSubsystem::HasClip(FName Kind, FName Id)
{
	const FString Path = ClipPath(Kind, Id);
	if (Path.IsEmpty())
	{
		return false;
	}
	if (const TObjectPtr<USoundBase>* Found = Clips.Find(Path))
	{
		return *Found != nullptr;
	}
	USoundBase* Clip = Cast<USoundBase>(FSoftObjectPath(Path).TryLoad());
	Clips.Add(Path, Clip);
	if (Clip == nullptr)
	{
		UE_LOG(LogWTA, Verbose, TEXT("no narration at %s"), *Path);
	}
	return Clip != nullptr;
}

bool UWTAVoiceSubsystem::Read(FName Kind, FName Id)
{
	Stop();
	if (!HasClip(Kind, Id))
	{
		return false;
	}
	USoundBase* Clip = Clips.FindRef(ClipPath(Kind, Id));
	Voice = UGameplayStatics::SpawnSound2D(this, Clip, FMath::Clamp(Volume, 0.f, 1.f));
	if (Voice == nullptr)
	{
		return false;
	}
	Voice->bAutoDestroy = false;
	Voice->OnAudioFinished.AddDynamic(this, &UWTAVoiceSubsystem::HandleFinished);
	ReadingKind = Kind;
	ReadingId = Id;
	OnVoiceChanged.Broadcast();
	return true;
}

void UWTAVoiceSubsystem::Stop()
{
	const bool bWas = Voice != nullptr;
	if (Voice != nullptr)
	{
		Voice->OnAudioFinished.RemoveDynamic(this, &UWTAVoiceSubsystem::HandleFinished);
		Voice->Stop();
		Voice = nullptr;
	}
	ReadingKind = NAME_None;
	ReadingId = NAME_None;
	if (bWas)
	{
		OnVoiceChanged.Broadcast();
	}
}

void UWTAVoiceSubsystem::HandleFinished()
{
	Stop();
}

bool UWTAVoiceSubsystem::IsReading() const
{
	return Voice != nullptr && Voice->IsPlaying();
}

bool UWTAVoiceSubsystem::IsReadingCard(FName Kind, FName Id) const
{
	return IsReading() && ReadingKind == Kind && ReadingId == Id;
}

void UWTAVoiceSubsystem::Deinitialize()
{
	Stop();
	Clips.Reset();
	Super::Deinitialize();
}
