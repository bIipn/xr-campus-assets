// Walk the Archive - the progress save (slot "WalkTheArchive", user index 0).
// Sets are stored as arrays. Pages entries are "<book>:<page>" FNames.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "WTASaveGame.generated.h"

UCLASS()
class WALKTHEARCHIVE_API UWTASaveGame : public USaveGame
{
	GENERATED_BODY()

public:
	/** Bump when the layout changes; old versions are discarded on load. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	int32 Version = 1;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FName> Badges;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FName> Tokens;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FName> Exhibits;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FName> Pages;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	TArray<FName> WaxScenes;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "WTA")
	float WalkedCm = 0.f;
};
