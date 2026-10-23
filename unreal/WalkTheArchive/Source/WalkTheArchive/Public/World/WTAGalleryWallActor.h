// Walk the Archive - the visitors' own wall: the pictures they took hang here.
//
// The maker room's wall for what visitors make themselves. At BeginPlay (and whenever E refreshes it) the actor
// reads the newest pictures from Saved/Postcards (photo mode's postcards) and Saved/Maker (anything a visitor
// or a librarian drops there: a PNG or JPG, with an optional <name>.txt beside it for the caption), hangs up to
// MaxPictures of them in a row on the wall it stands against (a cream mat behind each, the caption under it),
// newest nearest the middle. Empty, it says how to fill it. The actor's X axis points out from the wall; the
// editor Python places one against the wall, FloorBelowCm (150) above the floor, its yaw facing the room, so
// the pick box that is its root sits on the pictures.

#pragma once

#include "CoreMinimal.h"
#include "World/WTAPickActor.h"
#include "WTAGalleryWallActor.generated.h"

class UStaticMeshComponent;
class UTextRenderComponent;
class UMaterialInterface;
class UTexture2D;

UCLASS(Blueprintable)
class WALKTHEARCHIVE_API AWTAGalleryWallActor : public AWTAPickActor
{
	GENERATED_BODY()

public:
	AWTAGalleryWallActor();

	/** The wall's usable width, cm; the row of pictures is scaled to fit it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	float WallWidthCm = 560.f;

	/** A picture's height on the wall, cm (its width follows the file). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	float PictureHeightCm = 70.f;

	/** Height of the row's middle above the actor, cm. The actor sits FloorBelowCm above the floor, at the wall,
	    so its pick box (the root) is centred on the pictures. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	float RowHeightCm = 10.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	float FloorBelowCm = 150.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	int32 MaxPictures = 6;

	/** The wall's title, on a small plate above the row. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FText Title;

	/** Read the folders again and hang what is there. Returns how many pictures hang. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	int32 Refresh();

	UFUNCTION(BlueprintPure, Category = "WTA")
	int32 NumPictures() const { return Hung; }

	/** The folders read, in order: <Saved>/Postcards, <Saved>/Maker. */
	static TArray<FString> PictureFolders();

	virtual void Interact_Implementation(AWTAPlayerController* Controller) override;

protected:
	virtual void BeginPlay() override;
	virtual void ReadRow() override;

	struct FPicture { FString File; FDateTime Time; };
	static TArray<FPicture> FindPictures(int32 Max);
	static FString CaptionFor(const FString& File, const FDateTime& Time);

	void Clear();
	UStaticMeshComponent* MakePlane(const FVector& Local, float WidthCm, float HeightCm, float OutCm, UMaterialInterface* Material, UTexture2D* Texture, const FLinearColor& Colour);
	UTextRenderComponent* MakeText(const FVector& Local, const FString& Text, float SizeCm, const FLinearColor& Colour);

	UPROPERTY(Transient) TArray<TObjectPtr<USceneComponent>> Made;
	UPROPERTY(Transient) TArray<TObjectPtr<UTexture2D>> Textures;
	UPROPERTY(Transient) TObjectPtr<UStaticMesh> PlaneMesh;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> PlainMaterial;
	UPROPERTY(Transient) TObjectPtr<UMaterialInterface> UnlitMaterial;
	int32 Hung = 0;
};
