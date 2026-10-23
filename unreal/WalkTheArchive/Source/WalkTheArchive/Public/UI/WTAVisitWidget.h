// Walk the Archive - the "Visit together" card (built in C++, no widget asset). V or the menu opens it.
//
// On your own: your name, Lead a visit, the visits heard on this network (each with Join) and Join by address.
// Leading: who is here (each person's colour and name), the addresses visitors can type, Gather everyone here,
// Start the tour, End the visit. Visiting: whose visit this is, who is here, Walk to the guide, Leave the visit.
// A status line says what is happening ("Joining 192.168.1.20 ...") or what went wrong. Everything is done by
// UWTAVisitSubsystem; the card listens to its OnVisitChanged and refreshes the lists twice a second while open.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "WTAVisitWidget.generated.h"

class UBorder;
class UEditableTextBox;
class UTextBlock;
class UVerticalBox;
class UWTAActionButton;

UCLASS()
class WALKTHEARCHIVE_API UWTAVisitWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Open();

	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Close();

	UFUNCTION(BlueprintPure, Category = "WTA")
	bool IsOpen() const { return bOpen; }

	/** Re-read the role, the people and the visits heard. */
	UFUNCTION(BlueprintCallable, Category = "WTA")
	void Refresh();

	/** QA and the play test: the name and address boxes. */
	void SetNameText(const FString& Name);
	void SetAddressText(const FString& Address);

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	/** Buttons: "Lead", "Join" (Index into the visits heard), "JoinAddress", "Gather", "Tour", "Leave", "Walk", "Close". */
	UFUNCTION()
	void HandleAction(FName Action, FName Arg, int32 Index);

	UFUNCTION()
	void HandleVisitChanged();

	/** The name in the box, remembered (and sent to the visit when in one). */
	void CommitName();

	UPROPERTY(Transient) TObjectPtr<UBorder> Scrim;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> TitleText;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> BodyText;
	UPROPERTY(Transient) TObjectPtr<UVerticalBox> SoloBox;
	UPROPERTY(Transient) TObjectPtr<UVerticalBox> InVisitBox;
	UPROPERTY(Transient) TObjectPtr<UEditableTextBox> NameBox;
	UPROPERTY(Transient) TObjectPtr<UEditableTextBox> AddressBox;
	UPROPERTY(Transient) TObjectPtr<UVerticalBox> FoundList;
	UPROPERTY(Transient) TObjectPtr<UVerticalBox> PeopleList;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> AddressText;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> GatherButton;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> TourButton;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> WalkButton;
	UPROPERTY(Transient) TObjectPtr<UWTAActionButton> LeaveButton;
	UPROPERTY(Transient) TObjectPtr<UTextBlock> StatusText;

	/** The addresses of the visits listed, by row. */
	TArray<FString> ListedAddresses;
	FString ListedSignature;
	FString PeopleSignature;
	float SinceRefresh = 0.f;
	bool bOpen = false;
	bool bBound = false;
};
