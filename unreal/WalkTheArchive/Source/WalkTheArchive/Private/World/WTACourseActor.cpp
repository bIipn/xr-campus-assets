// Walk the Archive - a course desk.

#include "World/WTACourseActor.h"
#include "Core/WTAText.h"
#include "Animation/AnimSequence.h"
#include "Components/BoxComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Core/WTALog.h"
#include "Core/WTAPlayerController.h"
#include "EngineUtils.h"
#include "Systems/WTAContentSubsystem.h"
#include "World/WTAPeopleLibrary.h"
#include "World/WTAWaxAnimInstance.h"

namespace
{
	// MetaHuman blueprints face +Y in their own frame: a yaw of -90 turns the figure to face +X of the actor's yaw.
	constexpr float MetaHumanYawOffset = -90.f;
	const TCHAR* CourseAnimFolder = TEXT("/Game/WTA/Characters/Common/Anims/Mocap");
	const TCHAR* CourseIdleAction = TEXT("idle_b");
}

AWTACourseActor::AWTACourseActor()
{
	// the lead and the desk in front of them, so the crosshair finds the course from either
	PickExtent = FVector(90.f, 90.f, 110.f);
}

AWTACourseActor* AWTACourseActor::FindForVenue(const UObject* WorldContext, FName Venue)
{
	UWorld* World = WorldContext != nullptr ? WorldContext->GetWorld() : nullptr;
	if (World == nullptr || Venue.IsNone())
	{
		return nullptr;
	}
	for (TActorIterator<AWTACourseActor> It(World); It; ++It)
	{
		if (*It != nullptr && (*It)->bHasRow && (*It)->Row.Venue == Venue)
		{
			return *It;
		}
	}
	return nullptr;
}

void AWTACourseActor::ReadRow()
{
	Super::ReadRow();
	const UWTAContentSubsystem* Content = UWTAContentSubsystem::Get(this);
	const FWTATalkRow* Found = Content ? Content->FindTalk(TalkId) : nullptr;
	bHasRow = Found != nullptr;
	if (!bHasRow)
	{
		UE_LOG(LogWTA, Warning, TEXT("%s: no DT_Talks row '%s'"), *GetName(), *TalkId.ToString());
		Label = WTAText(TEXT("Course"));
		return;
	}
	Row = *Found;
	Label = FText::Format(WTAText(TEXT("Course · {0}")), Row.Title);
	// where to stand: in front of the desk, facing the lead
	const FVector Forward = FRotator(0.f, SpeakerYaw, 0.f).Vector();
	ViewSpot.Location = GetActorLocation() + Forward * 170.f + FVector(0.f, 0.f, 162.f);
	ViewSpot.Yaw = SpeakerYaw + 180.f;
	ViewSpot.Pitch = -6.f;
	ViewSpot.bValid = true;
}

void AWTACourseActor::BeginPlay()
{
	Super::BeginPlay();
	if (bHasRow)
	{
		SpawnLead();
	}
}

void AWTACourseActor::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (Lead != nullptr)
	{
		Lead->Destroy();
		Lead = nullptr;
	}
	Super::EndPlay(EndPlayReason);
}

void AWTACourseActor::SpawnLead()
{
	UWorld* World = GetWorld();
	if (World == nullptr || Row.Person.IsNone())
	{
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
	Lead = Person;
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
		if (UWTAWaxAnimInstance* Anim = Cast<UWTAWaxAnimInstance>(Body->GetAnimInstance()))
		{
			const FString Name = FString::Printf(TEXT("AS_WTA_%s"), CourseIdleAction);
			if (UAnimSequence* Idle = Cast<UAnimSequence>(FSoftObjectPath(FString::Printf(TEXT("%s/%s.%s"), CourseAnimFolder, *Name, *Name)).TryLoad()))
			{
				Anim->PlayClip(Idle, true, 1.f, UWTAPeopleLibrary::PersonPhase(Row.Person) * Idle->GetPlayLength(), 0.6f);
			}
		}
	}
}

void AWTACourseActor::Interact_Implementation(AWTAPlayerController* Controller)
{
	if (Controller == nullptr)
	{
		return;
	}
	if (ViewSpot.bValid)
	{
		Controller->GoToView(ViewSpot, true);
	}
	Controller->OpenCourse(TalkId);
}
