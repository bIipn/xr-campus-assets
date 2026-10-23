// Walk the Archive - the visit log.

#include "Systems/WTAVisitLogSubsystem.h"
#include "Core/WTALog.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "HAL/FileManager.h"
#include "Misc/DateTime.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Systems/WTAProgressSubsystem.h"
#include "Systems/WTARoomSubsystem.h"
#include "TimerManager.h"

namespace
{
	double UtcSeconds()
	{
		return FDateTime::UtcNow().ToUnixTimestampDecimal();
	}

	/** A CSV field: quoted when it holds a comma, a quote or a newline. */
	FString Field(const FString& Value)
	{
		if (Value.Contains(TEXT(",")) || Value.Contains(TEXT("\"")) || Value.Contains(TEXT("\n")))
		{
			return TEXT("\"") + Value.Replace(TEXT("\""), TEXT("\"\"")) + TEXT("\"");
		}
		return Value;
	}
}

UWTAVisitLogSubsystem* UWTAVisitLogSubsystem::Get(const UObject* WorldContextObject)
{
	if (WorldContextObject == nullptr || GEngine == nullptr)
	{
		return nullptr;
	}
	UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull);
	return World ? World->GetSubsystem<UWTAVisitLogSubsystem>() : nullptr;
}

FString UWTAVisitLogSubsystem::VisitsDir()
{
	return FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Visits"));
}

bool UWTAVisitLogSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	// Only where someone plays: the game, PIE, standalone. Never the editor's own world or a preview.
	const UWorld* World = Cast<UWorld>(Outer);
	return World != nullptr && (World->WorldType == EWorldType::Game || World->WorldType == EWorldType::PIE);
}

void UWTAVisitLogSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);
	LogFile = FPaths::ConvertRelativePathToFull(FPaths::Combine(VisitsDir(),
		FString::Printf(TEXT("visit_%s.csv"), *FDateTime::Now().ToString(TEXT("%Y%m%d-%H%M%S")))));
	if (UWTARoomSubsystem* Rooms = InWorld.GetSubsystem<UWTARoomSubsystem>())
	{
		Rooms->OnRoomChanged.AddDynamic(this, &UWTAVisitLogSubsystem::HandleRoomChanged);
		if (!Rooms->GetCurrentRoom().IsNone())
		{
			HandleRoomChanged(Rooms->GetCurrentRoom());
		}
	}
	if (UWTAProgressSubsystem* Progress = UWTAProgressSubsystem::Get(&InWorld))
	{
		Progress->OnTokenCollected.AddDynamic(this, &UWTAVisitLogSubsystem::HandleTokenCollected);
		Progress->OnBadgeAwarded.AddDynamic(this, &UWTAVisitLogSubsystem::HandleBadgeAwarded);
	}
	Write(TEXT("start"), FDateTime::Now().ToString(TEXT("%Y-%m-%d %H:%M:%S")), FString(), FString());
	if (SampleSeconds > 0.f)
	{
		InWorld.GetTimerManager().SetTimer(SampleTimer, this, &UWTAVisitLogSubsystem::Sample, SampleSeconds, true, SampleSeconds);
	}
}

void UWTAVisitLogSubsystem::Deinitialize()
{
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(SampleTimer);
	}
	CloseRoom();
	if (!LogFile.IsEmpty())
	{
		Write(TEXT("end"), FString(), FString(), FString());
		UE_LOG(LogWTA, Display, TEXT("WTA visit log %s: %d lines"), *LogFile, LinesWritten);
	}
	Super::Deinitialize();
}

void UWTAVisitLogSubsystem::HandleRoomChanged(FName RoomId)
{
	CloseRoom();
	CurrentRoom = RoomId;
	RoomEnteredAt = UtcSeconds();
}

void UWTAVisitLogSubsystem::CloseRoom()
{
	if (CurrentRoom.IsNone())
	{
		return;
	}
	const double Now = UtcSeconds();
	Write(TEXT("room"), CurrentRoom.ToString(), FString::Printf(TEXT("%.0f"), RoomEnteredAt), FString::Printf(TEXT("%.1f"), Now - RoomEnteredAt));
	CurrentRoom = NAME_None;
}

void UWTAVisitLogSubsystem::HandleTokenCollected(FName TokenId, int32 Found, int32 Total)
{
	NoteToken(TokenId);
}

void UWTAVisitLogSubsystem::HandleBadgeAwarded(FName BadgeId)
{
	NoteBadge(BadgeId);
}

void UWTAVisitLogSubsystem::NoteCard(FName Kind, FName Id)
{
	// The same card again (a book's next page, a quiz's next question, a station's next step) is one open.
	if (Kind == LastCardKind && Id == LastCardId)
	{
		return;
	}
	LastCardKind = Kind;
	LastCardId = Id;
	Write(TEXT("card"), Kind.ToString(), Id.IsNone() ? FString() : Id.ToString(), FString());
}

void UWTAVisitLogSubsystem::NoteToken(FName TokenId)
{
	Write(TEXT("token"), TokenId.ToString(), FString(), FString());
}

void UWTAVisitLogSubsystem::NoteBadge(FName BadgeId)
{
	Write(TEXT("badge"), BadgeId.ToString(), FString(), FString());
}

void UWTAVisitLogSubsystem::Sample()
{
	UWorld* World = GetWorld();
	APlayerController* PC = World ? World->GetFirstPlayerController() : nullptr;
	const APawn* Pawn = PC ? PC->GetPawn() : nullptr;
	if (Pawn == nullptr)
	{
		return;
	}
	const FVector At = Pawn->GetActorLocation();
	Write(TEXT("pos"), CurrentRoom.IsNone() ? FString() : CurrentRoom.ToString(),
		FString::Printf(TEXT("%.2f"), At.X / 100.f), FString::Printf(TEXT("%.2f"), At.Y / 100.f));
}

void UWTAVisitLogSubsystem::Write(const TCHAR* Kind, const FString& A, const FString& B, const FString& C)
{
	if (LogFile.IsEmpty())
	{
		return;
	}
	if (LinesWritten == 0)
	{
		IFileManager::Get().MakeDirectory(*FPaths::GetPath(LogFile), true);
		FFileHelper::SaveStringToFile(TEXT("utc,kind,a,b,c\n"), *LogFile, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
	}
	const FString Line = FString::Printf(TEXT("%.0f,%s,%s,%s,%s\n"), UtcSeconds(), Kind, *Field(A), *Field(B), *Field(C));
	FFileHelper::SaveStringToFile(Line, *LogFile, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM, &IFileManager::Get(), FILEWRITE_Append);
	++LinesWritten;
}
