// Walk the Archive - the interactable interface.
//
// The three functions are BlueprintNativeEvents on a UINTERFACE. For interfaces the Unreal Header Tool emits the
// default <Name>_Implementation bodies inline in WTAInteractable.generated.h (empty label, no-op Interact, false
// view spot), so there is nothing to define here; defining them again would be a redefinition. Actors override
// the _Implementation functions (see World/WTAPickActor.h) and callers go through the Execute_ statics.

#include "Interaction/WTAInteractable.h"
