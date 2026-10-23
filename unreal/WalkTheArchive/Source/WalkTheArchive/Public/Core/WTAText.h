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

/** A date as the campus writes it, "22 October 2026": the pattern "{0} {1} {2}" and the month go through DT_Strings,
    so a pack's language orders it its own way ("22 de octubre de 2026"). The day and year stay plain digits. */
inline FText WTADate(const FDateTime& When)
{
	static const TCHAR* Months[] = { TEXT("January"), TEXT("February"), TEXT("March"), TEXT("April"), TEXT("May"), TEXT("June"),
		TEXT("July"), TEXT("August"), TEXT("September"), TEXT("October"), TEXT("November"), TEXT("December") };
	return FText::Format(WTAText(TEXT("{0} {1} {2}")), FText::FromString(FString::FromInt(When.GetDay())),
		WTAText(Months[FMath::Clamp(When.GetMonth() - 1, 0, 11)]), FText::FromString(FString::FromInt(When.GetYear())));
}

/** Capitals for a kicker in any language: FText::ToUpper (ICU) turns "formación" into "FORMACIÓN", where
    FString::ToUpper only knows a to z. */
inline FString WTAUpper(const FString& Text)
{
	return FText::FromString(Text).ToUpper().ToString();
}

inline FText WTAUpper(const FText& Text)
{
	return Text.ToUpper();
}
