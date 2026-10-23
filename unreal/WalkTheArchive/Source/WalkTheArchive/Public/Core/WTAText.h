// Walk the Archive - the engine's own words, in the pack's language.
//
// Every word the C++ shows a visitor (a button, a kicker, a toast, a hint, the certificate's lines) goes through
// WTAText("...") with the English as the key: DT_Strings, built from Pipeline/content/lang/<lang>/strings.json,
// gives the pack's language, and without a row the English shows. Patterns with {0} {1} go through FText::Format
// as usual: FText::Format(WTAText("{0} of {1} found"), Found, Total). unreal/Tools/common/extract_strings.py
// lists every key for the translators.

#pragma once

#include "CoreMinimal.h"
#include "Systems/WTAContentSubsystem.h"

/** The pack's words for this English, else the English (UWTAContentSubsystem::Tr). */
inline FText WTAText(const TCHAR* English)
{
	return UWTAContentSubsystem::Tr(English);
}

inline FText WTAText(const FString& English)
{
	return UWTAContentSubsystem::Tr(English);
}
