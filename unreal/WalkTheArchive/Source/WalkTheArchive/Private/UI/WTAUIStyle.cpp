// Walk the Archive - the UI's own font files (everything else in WTAUIStyle.h is header-only).

#include "UI/WTAUIStyle.h"
#include "Fonts/CompositeFont.h"
#include "HAL/FileManager.h"
#include "Misc/Paths.h"

namespace
{
	/** A font file under <project>/Fonts as a Slate composite font, loaded once; null when the file is missing. */
	TSharedPtr<const FCompositeFont> FontFile(const TCHAR* FileName)
	{
		static TMap<FString, TSharedPtr<const FCompositeFont>> Cache;
		if (const TSharedPtr<const FCompositeFont>* Found = Cache.Find(FileName))
		{
			return *Found;
		}
		TSharedPtr<const FCompositeFont> Font;
		const FString Path = FPaths::Combine(FPaths::ProjectDir(), TEXT("Fonts"), FileName);
		if (IFileManager::Get().FileExists(*Path))
		{
			Font = MakeShared<FStandaloneCompositeFont>(FName(TEXT("Regular")), Path, EFontHinting::Default, EFontLoadingPolicy::LazyLoad);
		}
		Cache.Add(FileName, Font);
		return Font;
	}

	FSlateFontInfo FromFile(const TCHAR* FileName, int32 Size, const FSlateFontInfo& Fallback)
	{
		const TSharedPtr<const FCompositeFont> Font = FontFile(FileName);
		if (!Font.IsValid())
		{
			return Fallback;
		}
		return FSlateFontInfo(Font, static_cast<float>(Size), FName(TEXT("Regular")));
	}
}

namespace WTAStyle
{
	FSlateFontInfo Serif(int32 Size, bool bBold)
	{
		return FromFile(bBold ? TEXT("CormorantGaramond-Bold.ttf") : TEXT("CormorantGaramond-SemiBold.ttf"), Size, Font(Size, bBold));
	}

	FSlateFontInfo SerifItalic(int32 Size)
	{
		return FromFile(TEXT("CormorantGaramond-MediumItalic.ttf"), Size, Italic(Size));
	}

	FSlateFontInfo Script(int32 Size)
	{
		return FromFile(TEXT("GreatVibes-Regular.ttf"), Size, Italic(Size));
	}
}
