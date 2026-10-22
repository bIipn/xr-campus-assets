// Walk the Archive - a talk or a class: a speaker with slides, in a venue the builders made.

#include "World/WTATalkActor.h"
#include "Animation/AnimSequence.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Core/WTACharacter.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Systems/WTAContentSubsystem.h"
#include "Systems/WTAProgressSubsystem.h"
#include "Systems/WTAVoiceSubsystem.h"
#include "TimerManager.h"
#include "UObject/SoftObjectPath.h"
#include "World/WTAPeopleLibrary.h"
#include "World/WTASeatActor.h"
#include "World/WTAStaffNPC.h"
#include "World/WTAWaxAnimInstance.h"

const FName AWTATalkActor::VoiceKindTalk(TEXT("talk"));
const FName AWTATalkActor::VoiceKindQuiz(TEXT("quiz"));

namespace
{
	/** The display-referred unlit master the lighting step builds (emissive.py): the slides show as drawn. */
	const TCHAR* UnlitMasterPath = TEXT("/Game/WTA/Materials/M_WTA_Unlit.M_WTA_Unlit");
	const TCHAR* AnimFolder = TEXT("/Game/WTA/Characters/Common/Anims/Mocap");
	/** MetaHuman Creator Blueprints face +Y; -90 turns them to the spot's yaw (as the stages and staff do). */
	constexpr float MetaHumanYawOffset = -90.f;
	/** What a speaker does while a line is read: a cycle of talking gestures, each for a few seconds. */
	const TCHAR* Gestures[] = { TEXT("talk"), TEXT("present"), TEXT("talk_two"), TEXT("point_fwd"), TEXT("talk"), TEXT("present_b"), TEXT("nod") };
	const TCHAR* IdleAction = TEXT("idle_b");
	constexpr float GestureSeconds = 5.5f;
	constexpr float MinCaptionSeconds = 1.3f;
	constexpr float QuizDelaySeconds = 1.5f;

	/** The player's eye position in Mesh's component space, for the speaker's look-at. */
	bool PlayerEyesIn(const USkeletalMeshComponent* Mesh, const UObject* World, FVector& OutCS)
	{
		const AWTACharacter* Player = Cast<AWTACharacter>(UGameplayStatics::GetPlayerPawn(World, 0));
		if (Mesh == nullptr || Player == nullptr)
		{
			return false;
		}
		OutCS = Mesh->GetComponentTransform().InverseTransformPosition(Player->GetEyeLocation());
		return true;
	}
}

AWTATalkActor::AWTATalkActor()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = true;
	PrimaryActorTick.TickInterval = 0.25f;
	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
}

AActor* AWTATalkActor::GetSpeaker() const
{
	if (Figure != nullptr)
	{
		return Figure;
	}
	return StaffSpeaker != nullptr ? StaffSpeaker->GetMetaHuman() : nullptr;
}

AWTATalkActor* AWTATalkActor::FindForVenue(const UObject* WorldContextObject, FName Venue)
{
	UWorld* World = WorldContextObject != nullptr ? WorldContextObject->GetWorld() : nullptr;
	if (World == nullptr || Venue.IsNone())
	{
		return nullptr;
	}
	for (TActorIterator<AWTATalkActor> It(World); It; ++It)
	{
		if (*It != nullptr && (*It)->bHasRow && (*It)->Row.Venue == Venue)
		{
			return *It;
		}
	}
	return nullptr;
}

FName AWTATalkActor::VenueOfSeat(FName SeatId)
{
	FString Venue, Rest;
	if (SeatId.IsNone() || !SeatId.ToString().Split(TEXT("_"), &Venue, &Rest) || Venue.IsEmpty())
	{
		return NAME_None;
	}
	return FName(*Venue);
}

// ---------------------------------------------------------------------------
// Lifetime
// ---------------------------------------------------------------------------

void AWTATalkActor::BeginPlay()
{
	Super::BeginPlay();

	bHasRow = false;
	if (const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this))
	{
		if (const FWTATalkRow* Found = Content->FindTalk(TalkId))
		{
			Row = *Found;
			bHasRow = true;
		}
	}
	if (!bHasRow)
	{
		UE_LOG(LogWTA, Warning, TEXT("%s: no DT_Talks row '%s'"), *GetName(), *TalkId.ToString());
		return;
	}
	FindScreens();
	SetUpSpeaker();
	ShowSlide(INDEX_NONE);
	if (UWTAVoiceSubsystem* Voice = UWTAVoiceSubsystem::Get(this))
	{
		Voice->OnClipFinished.AddDynamic(this, &AWTATalkActor::HandleClipFinished);
		Voice->OnVoiceChanged.AddDynamic(this, &AWTATalkActor::HandleVoiceChanged);
	}
	UE_LOG(LogWTA, Log, TEXT("%s: '%s' in %s: %d slides, %d screens, speaker %s"), *GetName(), *Row.Title.ToString(),
		*Row.Venue.ToString(), Row.Slides.Num(), Screens.Num(), GetSpeaker() != nullptr ? *GetSpeaker()->GetName() : TEXT("none"));
}

void AWTATalkActor::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(SlideTimer);
		World->GetTimerManager().ClearTimer(CaptionTimer);
		World->GetTimerManager().ClearTimer(GestureTimer);
		World->GetTimerManager().ClearTimer(QuizTimer);
	}
	if (UWTAVoiceSubsystem* Voice = UWTAVoiceSubsystem::Get(this))
	{
		Voice->OnClipFinished.RemoveDynamic(this, &AWTATalkActor::HandleClipFinished);
		Voice->OnVoiceChanged.RemoveDynamic(this, &AWTATalkActor::HandleVoiceChanged);
	}
	if (AWTACharacter* Player = BoundPlayer.Get())
	{
		Player->OnSeatChanged.RemoveDynamic(this, &AWTATalkActor::HandleSeatChanged);
	}
	if (StaffSpeaker != nullptr)
	{
		StaffSpeaker->StopTeaching();
	}
	if (IsValid(Figure))
	{
		Figure->Destroy();
	}
	Figure = nullptr;
	Super::EndPlay(EndPlayReason);
}

void AWTATalkActor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!bHasRow)
	{
		return;
	}
	BindPlayer();

	// Nobody listening and the player gone: back to the title slide, ready for the next visitor.
	if (SlideIndex != INDEX_NONE && State != EWTATalkState::Playing && State != EWTATalkState::Waiting && !IsPlayerSeatedHere())
	{
		if (const APawn* Player = UGameplayStatics::GetPlayerPawn(this, 0))
		{
			if (FVector::Dist(Player->GetActorLocation(), GetActorLocation()) > ResetDistance)
			{
				Stop();
				SlideIndex = INDEX_NONE;
				State = EWTATalkState::Idle;
				ShowSlide(INDEX_NONE);
			}
		}
	}

	// The speaker keeps an eye on the listener while speaking.
	if (bSpeakingNow)
	{
		if (UWTAWaxAnimInstance* Anim = SpeakerAnim())
		{
			FVector Eyes;
			if (PlayerEyesIn(Cast<USkeletalMeshComponent>(Anim->GetOwningComponent()), this, Eyes))
			{
				Anim->SetLookAt(0.65f, Eyes);
			}
		}
	}
}

void AWTATalkActor::BindPlayer()
{
	if (BoundPlayer.IsValid())
	{
		return;
	}
	AWTACharacter* Player = Cast<AWTACharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
	if (Player == nullptr)
	{
		return;
	}
	BoundPlayer = Player;
	Player->OnSeatChanged.AddDynamic(this, &AWTATalkActor::HandleSeatChanged);
	if (IsPlayerSeatedHere())
	{
		Resume();
	}
}

bool AWTATalkActor::IsPlayerSeatedHere() const
{
	const AWTACharacter* Player = BoundPlayer.Get();
	if (Player == nullptr || !Player->IsSeated())
	{
		return false;
	}
	const AWTASeatActor* Seat = Cast<AWTASeatActor>(Player->GetSeat());
	return Seat != nullptr && VenueOfSeat(Seat->SeatId) == Row.Venue;
}

void AWTATalkActor::HandleSeatChanged(AActor* Seat, bool bSeated)
{
	const AWTASeatActor* SeatActor = Cast<AWTASeatActor>(Seat);
	const bool bHere = SeatActor != nullptr && VenueOfSeat(SeatActor->SeatId) == Row.Venue;
	if (bSeated && bHere)
	{
		Resume();
	}
	else if (!bSeated && bHere)
	{
		Stop();
	}
}

// ---------------------------------------------------------------------------
// Screens
// ---------------------------------------------------------------------------

void AWTATalkActor::FindScreens()
{
	Screens.Reset();
	ScreenMaterials.Reset();
	UWorld* World = GetWorld();
	if (World == nullptr)
	{
		return;
	}
	const FString Exact = FString::Printf(TEXT("screen__%s"), *Row.Venue.ToString());
	const FString Prefix = Exact + TEXT("_");
	TArray<UStaticMeshComponent*> Found;
	for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
	{
		UStaticMeshComponent* Comp = *It != nullptr ? (*It)->GetStaticMeshComponent() : nullptr;
		const UStaticMesh* Mesh = Comp != nullptr ? Comp->GetStaticMesh() : nullptr;
		if (Mesh == nullptr)
		{
			continue;
		}
		const FString Name = Mesh->GetName();
		if (Name == Exact || Name.StartsWith(Prefix))
		{
			Found.Add(Comp);
		}
	}
	if (Found.Num() == 0)
	{
		UE_LOG(LogWTA, Warning, TEXT("%s: no screen mesh '%s' in the level (the venue's builder names it so)"), *GetName(), *Exact);
		return;
	}
	UMaterialInterface* Master = Cast<UMaterialInterface>(FSoftObjectPath(UnlitMasterPath).TryLoad());
	if (Master == nullptr)
	{
		UE_LOG(LogWTA, Warning, TEXT("%s: %s is missing (run the lighting step); the slides stay off the screens"), *GetName(), UnlitMasterPath);
		return;
	}
	for (UStaticMeshComponent* Comp : Found)
	{
		UMaterialInstanceDynamic* Mid = UMaterialInstanceDynamic::Create(Master, this);
		if (Mid == nullptr)
		{
			continue;
		}
		Mid->SetScalarParameterValue(TEXT("Luminance"), 1.f);
		Mid->SetVectorParameterValue(TEXT("BaseColorFactor"), FLinearColor::White);
		for (int32 Slot = 0; Slot < Comp->GetNumMaterials(); ++Slot)
		{
			Comp->SetMaterial(Slot, Mid);
		}
		Screens.Add(Comp);
		ScreenMaterials.Add(Mid);
	}
}

void AWTATalkActor::ShowSlide(int32 Index)
{
	const int32 Which = Row.Slides.IsValidIndex(Index) ? Index : 0;
	if (!Row.Slides.IsValidIndex(Which))
	{
		return;
	}
	UTexture2D* Texture = Row.Slides[Which].Slide.LoadSynchronous();
	if (Texture == nullptr)
	{
		UE_LOG(LogWTA, Verbose, TEXT("%s: slide %d has no texture (%s)"), *GetName(), Which + 1, *Row.Slides[Which].Slide.ToString());
	}
	ShownSlide = Texture;
	for (UMaterialInstanceDynamic* Mid : ScreenMaterials)
	{
		if (Mid != nullptr && Texture != nullptr)
		{
			Mid->SetTextureParameterValue(TEXT("BaseColorTexture"), Texture);
		}
	}
}

// ---------------------------------------------------------------------------
// The speaker
// ---------------------------------------------------------------------------

UAnimSequence* AWTATalkActor::LoadAction(FName Action)
{
	if (Action.IsNone())
	{
		return nullptr;
	}
	if (const TObjectPtr<UAnimSequence>* Cached = Clips.Find(Action))
	{
		return *Cached;
	}
	const FString Name = FString::Printf(TEXT("AS_WTA_%s"), *Action.ToString());
	UAnimSequence* Clip = Cast<UAnimSequence>(FSoftObjectPath(FString::Printf(TEXT("%s/%s.%s"), AnimFolder, *Name, *Name)).TryLoad());
	if (Clip == nullptr)
	{
		UE_LOG(LogWTA, Verbose, TEXT("%s: no clip for '%s'"), *GetName(), *Action.ToString());
	}
	Clips.Add(Action, Clip);
	return Clip;
}

void AWTATalkActor::SetUpSpeaker()
{
	UWorld* World = GetWorld();
	if (World == nullptr)
	{
		return;
	}
	// A staff member teaches it: the NPC is the speaker, and comes to the spot when the class runs.
	if (!Row.Staff.IsNone())
	{
		for (TActorIterator<AWTAStaffNPC> It(World); It; ++It)
		{
			if (*It != nullptr && (*It)->StaffId == Row.Staff)
			{
				StaffSpeaker = *It;
				break;
			}
		}
		if (StaffSpeaker == nullptr)
		{
			UE_LOG(LogWTA, Warning, TEXT("%s: staff '%s' is not in the level; nobody speaks"), *GetName(), *Row.Staff.ToString());
		}
		return;
	}
	UClass* Class = UWTAPeopleLibrary::LoadMetaHumanClass(Row.Person);
	if (Class == nullptr)
	{
		return;                                       // LoadMetaHumanClass logged it: the person is not built yet
	}
	FActorSpawnParameters Params;
	Params.Owner = this;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	AActor* Person = World->SpawnActor<AActor>(Class, GetActorLocation(), FRotator(0.f, SpeakerYaw + MetaHumanYawOffset, 0.f), Params);
	if (Person == nullptr)
	{
		return;
	}
	Person->SetActorEnableCollision(false);
	Figure = Person;
	TInlineComponentArray<USkeletalMeshComponent*> Meshes;
	Person->GetComponents(Meshes);
	for (USkeletalMeshComponent* Mesh : Meshes)
	{
		if (Mesh != nullptr)
		{
			Mesh->bEnableUpdateRateOptimizations = false;
		}
	}
	UWTAPeopleLibrary::Thaw(Person);
	if (USkeletalMeshComponent* Body = UWTAPeopleLibrary::FindBody(Person))
	{
		Body->SetAnimationMode(EAnimationMode::AnimationBlueprint);
		Body->SetAnimInstanceClass(UWTAWaxAnimInstance::StaticClass());
	}
	SetSpeaking(false);
}

UWTAWaxAnimInstance* AWTATalkActor::SpeakerAnim() const
{
	USkeletalMeshComponent* Body = UWTAPeopleLibrary::FindBody(GetSpeaker());
	return Body != nullptr ? Cast<UWTAWaxAnimInstance>(Body->GetAnimInstance()) : nullptr;
}

void AWTATalkActor::SetSpeaking(bool bSpeaking)
{
	UWorld* World = GetWorld();
	if (World == nullptr)
	{
		return;
	}
	World->GetTimerManager().ClearTimer(GestureTimer);
	bSpeakingNow = bSpeaking;

	if (StaffSpeaker != nullptr && bSpeaking)
	{
		// The staff member comes to the spot (once) and their body takes our animation instance for the gestures.
		StaffSpeaker->BeginTeaching(GetActorLocation(), SpeakerYaw);
	}
	UWTAWaxAnimInstance* Anim = SpeakerAnim();
	if (Anim == nullptr)
	{
		return;
	}
	if (!bSpeaking)
	{
		if (UAnimSequence* Idle = LoadAction(IdleAction))
		{
			Anim->PlayClip(Idle, true, 1.f, UWTAPeopleLibrary::PersonPhase(Row.Person.IsNone() ? Row.Staff : Row.Person) * Idle->GetPlayLength(), 0.6f);
		}
		Anim->SetLookAt(0.f, FVector::ZeroVector);
		return;
	}
	// Gestures: one now, the next every few seconds while the line runs.
	const int32 Count = UE_ARRAY_COUNT(Gestures);
	const FName Action(Gestures[GestureIndex % Count]);
	GestureIndex = (GestureIndex + 1) % Count;
	if (UAnimSequence* Clip = LoadAction(Action))
	{
		Anim->PlayClip(Clip, true, 1.f, 0.f, 0.5f);
	}
	World->GetTimerManager().SetTimer(GestureTimer, FTimerDelegate::CreateWeakLambda(this, [this]() { if (bSpeakingNow) { SetSpeaking(true); } }), GestureSeconds, false);
}

// ---------------------------------------------------------------------------
// Playing
// ---------------------------------------------------------------------------

void AWTATalkActor::Start()
{
	if (!bHasRow || Row.Slides.Num() == 0)
	{
		return;
	}
	bEverStarted = true;
	GoToSlide(0);
}

void AWTATalkActor::Resume()
{
	if (!bHasRow || Row.Slides.Num() == 0 || State == EWTATalkState::Playing || State == EWTATalkState::Waiting)
	{
		return;
	}
	if (State == EWTATalkState::Done || !Row.Slides.IsValidIndex(SlideIndex))
	{
		Start();
		return;
	}
	GoToSlide(SlideIndex);
}

void AWTATalkActor::GoToSlide(int32 Index)
{
	if (!bHasRow)
	{
		return;
	}
	UWorld* World = GetWorld();
	if (World != nullptr)
	{
		World->GetTimerManager().ClearTimer(SlideTimer);
		World->GetTimerManager().ClearTimer(QuizTimer);
	}
	ClearCaptions();
	if (Index >= Row.Slides.Num())
	{
		Finish();
		return;
	}
	SlideIndex = FMath::Max(0, Index);
	State = EWTATalkState::Playing;
	ShowSlide(SlideIndex);
	SetSpeaking(true);
	ReadSlide();
}

void AWTATalkActor::ReadSlide()
{
	UWorld* World = GetWorld();
	if (World == nullptr || !Row.Slides.IsValidIndex(SlideIndex))
	{
		return;
	}
	const FWTATalkSlide& Slide = Row.Slides[SlideIndex];
	UWTAVoiceSubsystem* Voice = UWTAVoiceSubsystem::Get(this);
	ReadingClip = NAME_None;
	float Seconds = FMath::Max(2.f, Slide.Seconds);
	if (Voice != nullptr && !Slide.Clip.IsNone() && Voice->Read(VoiceKindTalk, Slide.Clip))
	{
		ReadingClip = Slide.Clip;
		Seconds = FMath::Max(1.f, Voice->ClipSeconds(VoiceKindTalk, Slide.Clip));
	}
	else
	{
		// No clip: the slide runs on its own clock.
		World->GetTimerManager().SetTimer(SlideTimer, FTimerDelegate::CreateWeakLambda(this, [this]() { Advance(); }), Seconds, false);
	}
	StartCaptions(Slide.Say, Seconds);
}

void AWTATalkActor::Advance()
{
	if (State != EWTATalkState::Playing)
	{
		return;
	}
	GoToSlide(SlideIndex + 1);
}

void AWTATalkActor::Finish()
{
	UWorld* World = GetWorld();
	ClearCaptions();
	ReadingClip = NAME_None;
	State = EWTATalkState::Done;
	SlideIndex = Row.Slides.Num() - 1;
	ShowSlide(SlideIndex);
	SetSpeaking(false);
	if (UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(this))
	{
		Progress->NoteTalkHeard(TalkId);
	}
	UE_LOG(LogWTA, Log, TEXT("%s: '%s' heard through"), *GetName(), *Row.Title.ToString());
	if (Row.IsClass() && Row.Quiz.Num() > 0 && World != nullptr && IsPlayerSeatedHere())
	{
		World->GetTimerManager().SetTimer(QuizTimer, FTimerDelegate::CreateWeakLambda(this, [this]()
		{
			if (AWTAPlayerController* PC = Cast<AWTAPlayerController>(UGameplayStatics::GetPlayerController(this, 0)))
			{
				PC->OpenQuiz(TalkId);
			}
		}), QuizDelaySeconds, false);
	}
}

void AWTATalkActor::Stop()
{
	UWorld* World = GetWorld();
	if (World != nullptr)
	{
		World->GetTimerManager().ClearTimer(SlideTimer);
		World->GetTimerManager().ClearTimer(QuizTimer);
	}
	if (!ReadingClip.IsNone())
	{
		if (UWTAVoiceSubsystem* Voice = UWTAVoiceSubsystem::Get(this))
		{
			if (Voice->IsReadingCard(VoiceKindTalk, ReadingClip))
			{
				Voice->Stop();
			}
		}
	}
	ReadingClip = NAME_None;
	ClearCaptions();
	if (State == EWTATalkState::Playing || State == EWTATalkState::Waiting)
	{
		State = EWTATalkState::Idle;
	}
	SetSpeaking(false);
	if (StaffSpeaker != nullptr)
	{
		StaffSpeaker->StopTeaching();                 // back to their own spot and their own idle
	}
}

void AWTATalkActor::HandleClipFinished(FName Kind, FName Id)
{
	if (State == EWTATalkState::Playing && Kind == VoiceKindTalk && !ReadingClip.IsNone() && Id == ReadingClip)
	{
		ReadingClip = NAME_None;
		Advance();
	}
}

void AWTATalkActor::HandleVoiceChanged()
{
	UWTAVoiceSubsystem* Voice = UWTAVoiceSubsystem::Get(this);
	if (Voice == nullptr)
	{
		return;
	}
	if (State == EWTATalkState::Playing && !ReadingClip.IsNone() && Voice->IsReading() && !Voice->IsReadingCard(VoiceKindTalk, ReadingClip))
	{
		// Something else is being read: wait, and read the line again once the voice is free.
		State = EWTATalkState::Waiting;
		ReadingClip = NAME_None;
		ClearCaptions();
		SetSpeaking(false);
	}
	else if (State == EWTATalkState::Waiting && !Voice->IsReading() && IsPlayerSeatedHere())
	{
		State = EWTATalkState::Playing;
		SetSpeaking(true);
		ReadSlide();
	}
}

// ---------------------------------------------------------------------------
// Captions
// ---------------------------------------------------------------------------

void AWTATalkActor::StartCaptions(const FText& Line, float Seconds)
{
	ClearCaptions();
	const FString Full = Line.ToString();
	if (Full.IsEmpty())
	{
		return;
	}
	// Sentences: split after . ! ? followed by a space; short tails join the sentence before them.
	FString Current;
	for (int32 i = 0; i < Full.Len(); ++i)
	{
		const TCHAR C = Full[i];
		Current.AppendChar(C);
		const bool bEnd = (C == TEXT('.') || C == TEXT('!') || C == TEXT('?')) && (i + 1 >= Full.Len() || Full[i + 1] == TEXT(' '));
		if (bEnd)
		{
			Captions.Add(Current.TrimStartAndEnd());
			Current.Reset();
		}
	}
	if (!Current.TrimStartAndEnd().IsEmpty())
	{
		Captions.Add(Current.TrimStartAndEnd());
	}
	for (int32 i = Captions.Num() - 1; i > 0; --i)
	{
		if (Captions[i].Len() < 24)
		{
			Captions[i - 1] += TEXT(" ") + Captions[i];
			Captions.RemoveAt(i);
		}
	}
	CaptionSeconds = Seconds;
	CaptionIndex = 0;
	NextCaption();
}

void AWTATalkActor::NextCaption()
{
	UWorld* World = GetWorld();
	AWTAPlayerController* PC = Cast<AWTAPlayerController>(UGameplayStatics::GetPlayerController(this, 0));
	if (World == nullptr || PC == nullptr || !Captions.IsValidIndex(CaptionIndex))
	{
		return;
	}
	int32 TotalChars = 0;
	for (const FString& S : Captions)
	{
		TotalChars += S.Len();
	}
	const FString& Shown = Captions[CaptionIndex];
	PC->ShowCaption(FText::FromString(Shown));
	const float Share = TotalChars > 0 ? CaptionSeconds * static_cast<float>(Shown.Len()) / static_cast<float>(TotalChars) : CaptionSeconds;
	++CaptionIndex;
	if (Captions.IsValidIndex(CaptionIndex))
	{
		World->GetTimerManager().SetTimer(CaptionTimer, FTimerDelegate::CreateWeakLambda(this, [this]() { NextCaption(); }), FMath::Max(MinCaptionSeconds, Share), false);
	}
}

void AWTATalkActor::ClearCaptions()
{
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(CaptionTimer);
	}
	if (Captions.Num() > 0)
	{
		if (AWTAPlayerController* PC = Cast<AWTAPlayerController>(UGameplayStatics::GetPlayerController(this, 0)))
		{
			PC->ShowCaption(FText::GetEmpty());
		}
	}
	Captions.Reset();
	CaptionIndex = 0;
}
