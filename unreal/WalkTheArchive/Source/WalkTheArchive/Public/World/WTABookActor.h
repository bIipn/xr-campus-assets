// Walk the Archive - a book on the featured table or a stack end.
// Interact: open the reader at page 0. Label: "Read - <Title>". Editor Python sets book_id and pick_extent.

#pragma once

#include "CoreMinimal.h"
#include "World/WTAPickActor.h"
#include "WTABookActor.generated.h"

UCLASS(Blueprintable)
class WALKTHEARCHIVE_API AWTABookActor : public AWTAPickActor
{
	GENERATED_BODY()

public:
	AWTABookActor();

	/** DT_Books row (editor Python: book_id). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	FName BookId;

	/** Page to open at (0 = first page; monitors in Room 104 can point at a later page). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WTA")
	int32 OpenPage = 0;

	virtual void Interact_Implementation(AWTAPlayerController* Controller) override;

protected:
	virtual void ReadRow() override;
};
