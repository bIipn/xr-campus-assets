// Walk the Archive - the certificate a class gives for passing its quiz (built in C++, no widget asset).
//
// A cream sheet with a double brass border: the campus's name as a kicker, "Certificate of Completion" in the
// serif, the visitor's name written by hand (the script face), the class, the date, a seal and the teacher's
// signature. Shown over a scrim with "Save a picture" and "Done" under it; SavePicture draws the sheet alone
// at print size (FWidgetRenderer) and writes Saved/Certificates/<name>_<class>.png.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Data/WTATypes.h"
#include "Input/Reply.h"
#include "WTACertificateWidget.generated.h"

class UBorder;
class USizeBox;
class UWTAActionButton;

UCLASS()
class WALKTHEARCHIVE_API UWTACertificateWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** The sheet's size at print, pixels (an A4 landscape ratio). */
	static constexpr float PrintWidth = 1600.f;
	static constexpr float PrintHeight = 1131.f;

	/** Build the sheet for Talk, made out to Name on Date; bForPrint = the sheet alone, at print size, no scrim or buttons. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Build(const FWTATalkRow& Talk, FName InTalkId, const FString& Name, const FString& Date, bool bForPrint);

	/** Draw this certificate at print size and write it as a PNG; returns the file written (empty on failure). */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	FString SavePicture();

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsOpen() const { return bOpen; }

	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Close();

	/** Where SavePicture writes: <Saved>/Certificates/<safe name>_<talk>.png. */
	static FString PicturePath(const FString& Name, FName TalkId);

protected:
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;

	UFUNCTION()
	void HandleAction(FName Action, FName Arg, int32 Index);

	/** The sheet itself (the part the picture shows), Scale times the print size. */
	UWidget* MakeSheet(float Scale);

	FWTATalkRow Row;
	FName TalkId;
	FString VisitorName;
	FString DateText;
	bool bOpen = false;
	bool bForPrintSheet = false;

	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> SaveButton;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> DoneButton;
};
