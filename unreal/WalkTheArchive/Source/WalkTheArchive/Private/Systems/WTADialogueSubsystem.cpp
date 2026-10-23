// Walk the Archive - staff answers (port of the web engine.js: toks/same/splitSents/searchKB/bestSentence,
// findPlace and the presetAnswer order). The regex intents live in DT_StaffRules; this file only runs them.

#include "Systems/WTADialogueSubsystem.h"
#include "Core/WTAText.h"
#include "Systems/WTAContentSubsystem.h"
#include "Core/WTALog.h"
#include "Data/WTATypes.h"
#include "Engine/DataTable.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Internationalization/Regex.h"
#include "Misc/Char.h"
#include "Subsystems/SubsystemCollection.h"

namespace
{
	// --- Characters and words -------------------------------------------------

	bool IsAsciiLower(TCHAR C) { return C >= TEXT('a') && C <= TEXT('z'); }
	bool IsAsciiDigit(TCHAR C) { return C >= TEXT('0') && C <= TEXT('9'); }
	bool IsApostrophe(TCHAR C) { return C == TEXT('\'') || C == 0x2019; }

	/** A Latin-1 letter lower-cased with its accent dropped ('É' -> 'e', 'ñ' -> 'n', 'ü' -> 'u'), so a visitor's
	    "dónde" and "donde" are the same word to the staff; every other character comes back as it is. */
	TCHAR FoldChar(TCHAR C)
	{
		if (C >= TEXT('A') && C <= TEXT('Z'))
		{
			return C - TEXT('A') + TEXT('a');
		}
		if (C < 0xC0 || C > 0xFF)
		{
			return C;
		}
		const TCHAR Lower = (C >= 0xC0 && C <= 0xDE && C != 0xD7) ? C + 0x20 : C;   // the Latin-1 capitals sit 0x20 below their small letters
		if ((Lower >= 0xE0 && Lower <= 0xE5)) return TEXT('a');
		if (Lower == 0xE7) return TEXT('c');
		if (Lower >= 0xE8 && Lower <= 0xEB) return TEXT('e');
		if (Lower >= 0xEC && Lower <= 0xEF) return TEXT('i');
		if (Lower == 0xF1) return TEXT('n');
		if ((Lower >= 0xF2 && Lower <= 0xF6) || Lower == 0xF8) return TEXT('o');
		if (Lower >= 0xF9 && Lower <= 0xFC) return TEXT('u');
		if (Lower == 0xFD || Lower == 0xFF) return TEXT('y');
		return Lower;
	}

	/** The web's STOP list: words that never count as search terms. The list goes through the language layer
	    (one key, the whole English list), so a language's strings.json extends it with its own little words. */
	const TSet<FString>& StopWords()
	{
		static TSet<FString> Words;
		if (Words.Num() == 0)
		{
			const FString List = WTAText(TEXT("a an the and or but if of to in on at by for with from into onto over under about as is are was were be been being am do does did doing done have has had having i me my mine you your yours he him his she her hers it its we us our they them their this that these those there here what which who whom whose when where why how can could would should will shall may might must not no please tell show give get got find let lets like just some any much many more most very really also too so than then such thing things something anything stuff kind sort want wanted need know think say said go going went come came see look looking one ones ok okay hey hi hello whats wheres hows thats im youre theres does dont can cant")).ToString();
			TArray<FString> Parts;
			List.ParseIntoArrayWS(Parts);
			for (const FString& Part : Parts)
			{
				FString Folded;
				for (int32 i = 0; i < Part.Len(); ++i)
				{
					Folded.AppendChar(FoldChar(Part[i]));
				}
				Words.Add(Folded);
			}
		}
		return Words;
	}

	/** Two-letter words worth keeping (the web's KEEP2). */
	bool KeepShort(const FString& Word)
	{
		return Word == TEXT("vr") || Word == TEXT("ar") || Word == TEXT("xr") || Word == TEXT("ai") || Word == TEXT("mr") || Word == TEXT("3d") || Word == TEXT("it");
	}

	bool IsAllDigits(const FString& Word)
	{
		if (Word.IsEmpty())
		{
			return false;
		}
		for (int32 i = 0; i < Word.Len(); ++i)
		{
			if (!IsAsciiDigit(Word[i]))
			{
				return false;
			}
		}
		return true;
	}

	/** The web's toks(): lower-case letter/digit words (accents folded), apostrophes dropped, stop words removed. */
	void TokenizeImpl(const FString& Text, TArray<FString>& OutTokens)
	{
		OutTokens.Reset();
		FString Lower;
		Lower.Reserve(Text.Len());
		for (int32 i = 0; i < Text.Len(); ++i)
		{
			Lower.AppendChar(FoldChar(Text[i]));
		}
		FString Word;
		auto Flush = [&OutTokens, &Word]()
		{
			if (!Word.IsEmpty())
			{
				if (!StopWords().Contains(Word) && (Word.Len() > 2 || KeepShort(Word) || IsAllDigits(Word)))
				{
					OutTokens.Add(Word);
				}
				Word.Reset();
			}
		};
		for (int32 i = 0; i < Lower.Len(); ++i)
		{
			const TCHAR C = Lower[i];
			if (IsApostrophe(C))
			{
				continue; // "it's" -> "its", as on the web
			}
			if (IsAsciiLower(C) || IsAsciiDigit(C))
			{
				Word.AppendChar(C);
			}
			else
			{
				Flush();
			}
		}
		Flush();
	}

	int32 CountWordsImpl(const FString& Text)
	{
		int32 Count = 0;
		bool bInWord = false;
		for (int32 i = 0; i < Text.Len(); ++i)
		{
			const bool bSpace = FChar::IsWhitespace(Text[i]);
			if (!bSpace && !bInWord)
			{
				++Count;
			}
			bInWord = !bSpace;
		}
		return Count;
	}

	/** "Mr." / "Dr." / "U.S." before the dot at DotIndex: not a sentence end. */
	bool IsAbbreviationDot(const FString& Text, int32 DotIndex)
	{
		if (DotIndex >= 3 && Text.Mid(DotIndex - 3, 3) == TEXT("U.S"))
		{
			return true;
		}
		int32 Start = DotIndex;
		while (Start > 0 && FChar::IsAlpha(Text[Start - 1]))
		{
			--Start;
		}
		if (Start > 0 && FChar::IsAlnum(Text[Start - 1]))
		{
			return false; // "1st." is a word, not an abbreviation
		}
		const FString Word = Text.Mid(Start, DotIndex - Start);
		return Word == TEXT("Mr") || Word == TEXT("Mrs") || Word == TEXT("Ms") || Word == TEXT("Dr") || Word == TEXT("St");
	}

	bool IsTerminator(TCHAR C) { return C == TEXT('.') || C == TEXT('!') || C == TEXT('?'); }
	bool IsClosingQuote(TCHAR C) { return C == TEXT('"') || C == 0x201D || C == 0x2019 || C == TEXT(')'); }

	/** The web's splitSents(), keeping sentences of at least three words. */
	void SplitSentencesImpl(const FString& Text, TArray<FString>& OutSentences)
	{
		OutSentences.Reset();
		const int32 N = Text.Len();
		FString Current;
		auto Emit = [&OutSentences, &Current]()
		{
			const FString Trimmed = Current.TrimStartAndEnd();
			if (!Trimmed.IsEmpty() && CountWordsImpl(Trimmed) >= 3)
			{
				OutSentences.Add(Trimmed);
			}
			Current.Reset();
		};
		for (int32 i = 0; i < N; ++i)
		{
			const TCHAR C = Text[i];
			Current.AppendChar(C);
			if (!IsTerminator(C))
			{
				continue;
			}
			if (C == TEXT('.'))
			{
				const bool bDecimal = i > 0 && i + 1 < N && IsAsciiDigit(Text[i - 1]) && IsAsciiDigit(Text[i + 1]);
				if (bDecimal || IsAbbreviationDot(Text, i))
				{
					continue;
				}
			}
			while (i + 1 < N && IsTerminator(Text[i + 1]))
			{
				Current.AppendChar(Text[++i]);
			}
			while (i + 1 < N && IsClosingQuote(Text[i + 1]))
			{
				Current.AppendChar(Text[++i]);
			}
			Emit();
		}
		Emit();
		if (OutSentences.Num() == 0)
		{
			const FString Trimmed = Text.TrimStartAndEnd();
			if (!Trimmed.IsEmpty())
			{
				OutSentences.Add(Trimmed);
			}
		}
	}

	FString FirstSentences(const FString& Text, int32 Count)
	{
		TArray<FString> Sentences;
		SplitSentencesImpl(Text, Sentences);
		FString Out;
		for (int32 i = 0; i < Sentences.Num() && i < Count; ++i)
		{
			if (!Out.IsEmpty())
			{
				Out += TEXT(" ");
			}
			Out += Sentences[i];
		}
		return Out.IsEmpty() ? Text.TrimStartAndEnd() : Out;
	}

	/** The web's same(): equal, or one is a prefix of the other when both are 4+ letters and close in length. */
	bool SameTerm(const FString& A, const FString& B)
	{
		if (A == B)
		{
			return true;
		}
		const int32 Shorter = FMath::Min(A.Len(), B.Len());
		if (Shorter < 4 || FMath::Abs(A.Len() - B.Len()) > 3)
		{
			return false;
		}
		return A.StartsWith(B, ESearchCase::CaseSensitive) || B.StartsWith(A, ESearchCase::CaseSensitive);
	}

	bool AnySame(const FString& Term, const TMap<FString, int32>& Terms)
	{
		for (const TPair<FString, int32>& Pair : Terms)
		{
			if (SameTerm(Term, Pair.Key))
			{
				return true;
			}
		}
		return false;
	}

	bool AnySame(const FString& Term, const TArray<FString>& Terms)
	{
		for (const FString& Other : Terms)
		{
			if (SameTerm(Term, Other))
			{
				return true;
			}
		}
		return false;
	}

	/** The web's norm(): " lower-case words separated by single spaces ", accents folded, punctuation removed. */
	FString Normalize(const FString& Text)
	{
		FString Out(TEXT(" "));
		bool bLastSpace = true;
		for (int32 i = 0; i < Text.Len(); ++i)
		{
			const TCHAR C = FoldChar(Text[i]);
			if (IsApostrophe(C))
			{
				continue;
			}
			if (IsAsciiLower(C) || IsAsciiDigit(C))
			{
				Out.AppendChar(C);
				bLastSpace = false;
			}
			else if (!bLastSpace)
			{
				Out.AppendChar(TEXT(' '));
				bLastSpace = true;
			}
		}
		if (!bLastSpace)
		{
			Out.AppendChar(TEXT(' '));
		}
		return Out;
	}

	/** Case-insensitive ICU regex test (the pattern is wrapped in (?i)). */
	bool RegexMatch(const FString& Pattern, const FString& Text)
	{
		if (Pattern.IsEmpty())
		{
			return false;
		}
		const FRegexPattern Compiled(FString(TEXT("(?i)")) + Pattern);
		FRegexMatcher Matcher(Compiled, Text);
		return Matcher.FindNext();
	}

	/** A question-shape regex through the language layer: the English pattern is the key, and a language's
	    strings.json gives it back with the language's alternatives added ("(english|spanish)"), so the staff read
	    the question's shape in both. */
	bool ShapeMatch(const TCHAR* EnglishPattern, const FString& Question)
	{
		return RegexMatch(UWTAContentSubsystem::Tr(EnglishPattern).ToString(), Question);
	}

	// --- Question shape ---------------------------------------------------------

	bool ContainsYear(const FString& Text)
	{
		for (int32 i = 0; i + 3 < Text.Len(); ++i)
		{
			if (!IsAsciiDigit(Text[i]) || !IsAsciiDigit(Text[i + 1]) || !IsAsciiDigit(Text[i + 2]) || !IsAsciiDigit(Text[i + 3]))
			{
				continue;
			}
			const bool bBoundaryBefore = i == 0 || !FChar::IsAlnum(Text[i - 1]);
			const bool bBoundaryAfter = i + 4 >= Text.Len() || !FChar::IsAlnum(Text[i + 4]);
			const bool bPlausible = (Text[i] == TEXT('1') && (Text[i + 1] == TEXT('8') || Text[i + 1] == TEXT('9'))) || (Text[i] == TEXT('2') && Text[i + 1] == TEXT('0'));
			if (bBoundaryBefore && bBoundaryAfter && bPlausible)
			{
				return true;
			}
		}
		return false;
	}

	bool ContainsDigit(const FString& Text)
	{
		for (int32 i = 0; i < Text.Len(); ++i)
		{
			if (IsAsciiDigit(Text[i]))
			{
				return true;
			}
		}
		return false;
	}

	/** Two capitalised words in a row ("Ivan Sutherland"): probably a name. */
	bool ContainsCapitalizedPair(const FString& Text)
	{
		TArray<FString> Words;
		Text.ParseIntoArrayWS(Words);
		for (int32 i = 0; i + 1 < Words.Num(); ++i)
		{
			const FString& A = Words[i];
			const FString& B = Words[i + 1];
			if (A.Len() >= 2 && B.Len() >= 2 && FChar::IsUpper(A[0]) && FChar::IsLower(A[1]) && FChar::IsUpper(B[0]) && FChar::IsAlpha(B[1]))
			{
				return true;
			}
		}
		return false;
	}

	/** "when", "num", "who" or empty (the web's qtype), read with the language's shapes. */
	FString QuestionType(const FString& Question)
	{
		if (ShapeMatch(TEXT("^\\s*[¿¡]?\\s*when\\b|\\bwhat year\\b|\\bhow long ago\\b"), Question))
		{
			return TEXT("when");
		}
		if (ShapeMatch(TEXT("\\bhow (many|much)\\b|\\bnumber of\\b"), Question))
		{
			return TEXT("num");
		}
		if (ShapeMatch(TEXT("^\\s*[¿¡]?\\s*who\\b"), Question))
		{
			return TEXT("who");
		}
		return FString();
	}

	/** The web's RX.go: the player wants to be taken somewhere. */
	bool WantsToGo(const FString& Question)
	{
		return ShapeMatch(TEXT("\\b(take|bring|walk|lead) me\\b|\\bgo to\\b|\\bshow me the way\\b|\\bhow do i get to\\b|\\blets? go\\b|\\blet's go\\b"), Question);
	}

	/** The web's RX.wh: the player asks where something is. */
	bool AsksWhere(const FString& Question)
	{
		return ShapeMatch(TEXT("\\bwhere('?s| is| are| can i find| do i find)\\b|\\bwhich way\\b|\\bhow do i (get|find)\\b|\\bdirections?\\b"), Question);
	}

	/** The web's RX.hi. */
	bool IsGreeting(const FString& Question)
	{
		return ShapeMatch(TEXT("^\\s*[¿¡]?\\s*(hi|hello|hey|howdy|yo|good (morning|afternoon|evening))\\b"), Question);
	}

	FString TextOf(const FText& Text)
	{
		return Text.ToString();
	}

	/** Blocks of a book page as one string. */
	FString PageText(const FWTABookPage& Page)
	{
		FString Out;
		for (const FWTABookBlock& Block : Page.Blocks)
		{
			if (!Block.Text.IsEmpty())
			{
				Out += TextOf(Block.Text) + TEXT(" ");
			}
			for (const FText& Item : Block.Items)
			{
				Out += TextOf(Item);
				if (!TextOf(Item).EndsWith(TEXT(".")))
				{
					Out += TEXT(".");
				}
				Out += TEXT(" ");
			}
		}
		return Out.TrimStartAndEnd();
	}

	/** Where an exhibit hangs, for the "That's from ..." line (through the language layer). */
	FString ExhibitWhere(const FWTAExhibitRow& Row)
	{
		if (Row.bWax)
		{
			return WTAText(TEXT("in the Wax Hall")).ToString();
		}
		if (Row.Gallery <= 0)
		{
			return WTAText(TEXT("in the library")).ToString();
		}
		return FText::Format(WTAText(TEXT("in Gallery {0}")), FText::FromString(FString::FromInt(Row.Gallery))).ToString();
	}

	/** "That's from "<title>" <where>." and its kin, through the language layer. */
	FString Attribution(const TCHAR* Pattern, const FString& A, const FString& B)
	{
		return FText::Format(UWTAContentSubsystem::Tr(Pattern), FText::FromString(A), FText::FromString(B)).ToString();
	}

	const UWTAContentSubsystem* ContentOf(const UGameInstance* GameInstance)
	{
		return GameInstance ? GameInstance->GetSubsystem<UWTAContentSubsystem>() : nullptr;
	}

	const FName KindItem(TEXT("item"));
	const FName KindFact(TEXT("fact"));
	const FName KindPage(TEXT("page"));
	const FName KindLesson(TEXT("lesson"));
	const FName KindPart(TEXT("part"));

	/** The web's searchAnswer bias: each staff member prefers some kinds of document (x1.5, x1.25, x1, ...); others x0.8. */
	float KindBias(FName StaffId, FName Kind)
	{
		TArray<FName> Order;
		if (StaffId == FName(TEXT("rosa")))
		{
			Order = { KindPage, KindFact, KindItem };
		}
		else if (StaffId == FName(TEXT("hale")))
		{
			Order = { KindLesson, KindPart, KindFact, KindPage, KindItem };
		}
		else if (StaffId == FName(TEXT("rae")))
		{
			Order = { KindFact, KindPage, KindItem };
		}
		else
		{
			Order = { KindItem, KindFact, KindPage };
		}
		const int32 Index = Order.IndexOfByKey(Kind);
		return Index == INDEX_NONE ? 0.8f : 1.f + 0.25f * static_cast<float>(2 - Index);
	}

	/** The default label of the button under an answer that offers its action. */
	FText OfferLabel(FName Action)
	{
		if (Action == WTAAction::OpenItem())
		{
			return WTAText(TEXT("Show me the exhibit"));
		}
		if (Action == WTAAction::OpenBook())
		{
			return WTAText(TEXT("Open the book"));
		}
		if (Action == WTAAction::OpenStation())
		{
			return WTAText(TEXT("Take me to the station"));
		}
		if (Action == WTAAction::OpenRide())
		{
			return WTAText(TEXT("Show me the ride"));
		}
		if (Action == WTAAction::OpenBadges())
		{
			return WTAText(TEXT("Show me the badges"));
		}
		if (Action == WTAAction::GoPlace())
		{
			return WTAText(TEXT("Take me there"));
		}
		if (Action == WTAAction::StartTour())
		{
			return WTAText(TEXT("Start the tour"));
		}
		return WTAText(TEXT("Show me"));
	}

	/** The player asked to be shown or taken somewhere now, so an answer's action runs instead of waiting for its button. */
	bool WantsItNow(const FString& Question)
	{
		return WantsToGo(Question) || ShapeMatch(TEXT("\\bshow me\\b"), Question);
	}
}

// --- Subsystem -----------------------------------------------------------------

UWTADialogueSubsystem* UWTADialogueSubsystem::Get(const UObject* WorldContextObject)
{
	if (WorldContextObject == nullptr || GEngine == nullptr)
	{
		return nullptr;
	}
	const UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull);
	if (World == nullptr)
	{
		return nullptr;
	}
	const UGameInstance* GameInstance = World->GetGameInstance();
	return GameInstance ? GameInstance->GetSubsystem<UWTADialogueSubsystem>() : nullptr;
}

void UWTADialogueSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	Collection.InitializeDependency(UWTAContentSubsystem::StaticClass());
	// The index is built on the first Ask so a reload of the tables is picked up.
	bIndexBuilt = false;
}

FWTAReply UWTADialogueSubsystem::Ask(FName StaffId, const FString& Question)
{
	const FString Q = Question.TrimStartAndEnd();
	FWTAReply Reply;
	if (Q.IsEmpty())
	{
		return Fallback(StaffId);
	}
	if (TryGreeting(StaffId, Q, Reply))
	{
		return Reply;
	}
	if (TryRules(StaffId, Q, TNumericLimits<int32>::Lowest(), 99, Reply))
	{
		return Reply;
	}
	if (TryDirections(Q, Reply))
	{
		return Reply;
	}
	if (TryTitleMatch(Q, Reply))
	{
		return Reply;
	}
	if (TryRules(StaffId, Q, 100, TNumericLimits<int32>::Max(), Reply))
	{
		return Reply;
	}
	if (TrySearch(StaffId, Q, Reply))
	{
		return Reply;
	}
	return Fallback(StaffId);
}

FText UWTADialogueSubsystem::GetGreeting(FName StaffId, bool bShort) const
{
	const UWTAContentSubsystem* Content = ContentOf(GetGameInstance());
	const FWTAStaffRow* Staff = Content ? Content->FindStaff(StaffId) : nullptr;
	if (Staff == nullptr)
	{
		return WTAText(TEXT("Hello! What would you like to see?"));
	}
	if (bShort && !Staff->GreetingShort.IsEmpty())
	{
		return Staff->GreetingShort;
	}
	return Staff->Greeting.IsEmpty() ? Staff->GreetingShort : Staff->Greeting;
}

TArray<FText> UWTADialogueSubsystem::GetChips(FName StaffId) const
{
	const UWTAContentSubsystem* Content = ContentOf(GetGameInstance());
	const FWTAStaffRow* Staff = Content ? Content->FindStaff(StaffId) : nullptr;
	return Staff ? Staff->Chips : TArray<FText>();
}

FText UWTADialogueSubsystem::GetHelp(FName StaffId) const
{
	const UWTAContentSubsystem* Content = ContentOf(GetGameInstance());
	const FWTAStaffRow* Staff = Content ? Content->FindStaff(StaffId) : nullptr;
	return Staff ? Staff->Help : FText::GetEmpty();
}

void UWTADialogueSubsystem::RebuildIndex()
{
	Docs.Reset();
	DocFrequency.Reset();
	bIndexBuilt = true;

	const UWTAContentSubsystem* Content = ContentOf(GetGameInstance());
	if (Content == nullptr)
	{
		return;
	}

	// Exhibits (the web's 'item' docs): description, more, quote, where, partners.
	if (const UDataTable* Exhibits = Content->GetTable(EWTATable::Exhibits))
	{
		for (const TPair<FName, uint8*>& Pair : Exhibits->GetRowMap())
		{
			const FWTAExhibitRow* Row = reinterpret_cast<const FWTAExhibitRow*>(Pair.Value);
			if (Row == nullptr)
			{
				continue;
			}
			FString Body = TextOf(Row->Description) + TEXT(" ") + TextOf(Row->More);
			if (!Row->Quote.IsEmpty())
			{
				Body += TEXT(" ") + TextOf(Row->Quote) + TEXT(" ") + TextOf(Row->QuoteBy) + TEXT(".");
			}
			if (!Row->Where.IsEmpty())
			{
				Body += TEXT(" ") + Attribution(TEXT("Location: {0}."), TextOf(Row->Where), FString());
			}
			if (!Row->Partners.IsEmpty())
			{
				Body += TEXT(" ") + Attribution(TEXT("Partners: {0}."), TextOf(Row->Partners), FString());
			}
			AddDoc(TextOf(Row->Title), Body, WTAAction::OpenItem(), Pair.Key);
			Docs.Last().Kind = KindItem;
			Docs.Last().Source = Attribution(TEXT("That\u2019s from \u201C{0}\u201D {1}."), TextOf(Row->Title), ExhibitWhere(*Row));
		}
	}

	// Facts: the row id is the title ("what" reads as XRLibraries), the first source as the attribution.
	if (const UDataTable* Facts = Content->GetTable(EWTATable::Facts))
	{
		for (const TPair<FName, uint8*>& Pair : Facts->GetRowMap())
		{
			const FWTAFactRow* Row = reinterpret_cast<const FWTAFactRow*>(Pair.Value);
			if (Row == nullptr)
			{
				continue;
			}
			const FString Title = Pair.Key == FName(TEXT("what")) ? FString(TEXT("XRLibraries")) : Pair.Key.ToString();
			AddDoc(Title, TextOf(Row->Body), NAME_None, NAME_None);
			Docs.Last().Kind = KindFact;
			if (Row->Sources.Num() > 0)
			{
				if (const FWTASourceRow* Source = Content->FindSource(Row->Sources[0]))
				{
					Docs.Last().Source = Attribution(TEXT("(Source: {0}.)"), TextOf(Source->Label), FString());
				}
			}
		}
	}

	// Book pages: one doc per page, titled "<book> <heading>".
	if (const UDataTable* Books = Content->GetTable(EWTATable::Books))
	{
		for (const TPair<FName, uint8*>& Pair : Books->GetRowMap())
		{
			const FWTABookRow* Row = reinterpret_cast<const FWTABookRow*>(Pair.Value);
			if (Row == nullptr)
			{
				continue;
			}
			for (int32 PageIndex = 0; PageIndex < Row->Pages.Num(); ++PageIndex)
			{
				const FWTABookPage& Page = Row->Pages[PageIndex];
				// The answer names the page, so its button opens the book at that page ("<book>#<page index>").
				const FName PageArg(*FString::Printf(TEXT("%s#%d"), *Pair.Key.ToString(), PageIndex));
				AddDoc(TextOf(Row->Title) + TEXT(" ") + TextOf(Page.Heading), PageText(Page), WTAAction::OpenBook(), PageArg);
				Docs.Last().Kind = KindPage;
				Docs.Last().Source = Attribution(TEXT("That\u2019s in \u201C{0},\u201D page {1}."), TextOf(Row->Title), FString::FromInt(PageIndex + 1));
			}
		}
	}

	// Lessons: what the stations teach; the answer opens the station panel.
	if (const UDataTable* Lessons = Content->GetTable(EWTATable::Lessons))
	{
		for (const TPair<FName, uint8*>& Pair : Lessons->GetRowMap())
		{
			const FWTALessonRow* Row = reinterpret_cast<const FWTALessonRow*>(Pair.Value);
			if (Row == nullptr)
			{
				continue;
			}
			AddDoc(TextOf(Row->Title), TextOf(Row->Body), Row->Station.IsNone() ? NAME_None : WTAAction::OpenStation(), Row->Station);
			Docs.Last().Kind = KindLesson;
		}
	}

	UE_LOG(LogWTA, Log, TEXT("Dialogue: index built, %d documents, %d terms"), Docs.Num(), DocFrequency.Num());
}

// --- The tries, in order ----------------------------------------------------------

bool UWTADialogueSubsystem::TryGreeting(FName StaffId, const FString& Question, FWTAReply& OutReply) const
{
	TArray<FString> Tokens;
	Tokenize(Question, Tokens);
	if (Tokens.Num() <= 2 && IsGreeting(Question))
	{
		OutReply.Text = GetGreeting(StaffId, true);
		OutReply.Action = NAME_None;
		OutReply.ActionArg = NAME_None;
		return true;
	}
	return false;
}

bool UWTADialogueSubsystem::TryRules(FName StaffId, const FString& Question, int32 MinOrder, int32 MaxOrder, FWTAReply& OutReply) const
{
	const UWTAContentSubsystem* Content = ContentOf(GetGameInstance());
	const UDataTable* Rules = Content ? Content->GetTable(EWTATable::StaffRules) : nullptr;
	if (Rules == nullptr)
	{
		return false;
	}
	// By Order, then by row name, so variants of one web branch (R132, R132a, R132b) run in a fixed order.
	TArray<TPair<FString, const FWTAStaffRuleRow*>> Sorted;
	for (const TPair<FName, uint8*>& Pair : Rules->GetRowMap())
	{
		const FWTAStaffRuleRow* Row = reinterpret_cast<const FWTAStaffRuleRow*>(Pair.Value);
		if (Row != nullptr && Row->Order >= MinOrder && Row->Order <= MaxOrder)
		{
			Sorted.Emplace(Pair.Key.ToString(), Row);
		}
	}
	Sorted.Sort([](const TPair<FString, const FWTAStaffRuleRow*>& A, const TPair<FString, const FWTAStaffRuleRow*>& B)
	{
		return A.Value->Order != B.Value->Order ? A.Value->Order < B.Value->Order : A.Key < B.Key;
	});

	TArray<FString> Tokens;
	Tokenize(Question, Tokens);
	for (const TPair<FString, const FWTAStaffRuleRow*>& Entry : Sorted)
	{
		const FWTAStaffRuleRow* Rule = Entry.Value;
		if (Rule->StaffOnly.Num() > 0 && !Rule->StaffOnly.Contains(StaffId))
		{
			continue;
		}
		if (Rule->StaffNot.Contains(StaffId))
		{
			continue;
		}
		// MaxWords counts search terms, as the web did (so "thank you very much" is still short).
		if (Rule->MaxWords > 0 && Tokens.Num() > Rule->MaxWords)
		{
			continue;
		}
		if (RegexMatch(Rule->Pattern, Question))
		{
			OutReply.Text = Rule->Answer;
			OutReply.Action = Rule->Action;
			OutReply.ActionArg = Rule->ActionArg;
			OutReply.bOffer = Rule->bOffer && !Rule->Action.IsNone();
			OutReply.OfferLabel = !OutReply.bOffer ? FText::GetEmpty()
				: (Rule->OfferLabel.IsEmpty() ? OfferLabel(Rule->Action) : Rule->OfferLabel);
			return true;
		}
	}
	return false;
}

bool UWTADialogueSubsystem::TryDirections(const FString& Question, FWTAReply& OutReply) const
{
	// Only when the question asks to go somewhere or where something is; "tell me about the lab" is not a trip.
	const bool bGo = WantsToGo(Question);
	const bool bWhere = AsksWhere(Question);
	if (!bGo && !bWhere)
	{
		return false;
	}
	const UWTAContentSubsystem* Content = ContentOf(GetGameInstance());
	const UDataTable* Places = Content ? Content->GetTable(EWTATable::Places) : nullptr;
	if (Places == nullptr)
	{
		return false;
	}
	const FString Norm = Normalize(Question);
	const FWTAPlaceRow* Best = nullptr;
	FName BestId;
	int32 BestLen = 0;
	for (const TPair<FName, uint8*>& Pair : Places->GetRowMap())
	{
		const FWTAPlaceRow* Row = reinterpret_cast<const FWTAPlaceRow*>(Pair.Value);
		if (Row == nullptr)
		{
			continue;
		}
		for (const FString& Alias : Row->Aliases)
		{
			const FString Needle = Normalize(Alias);
			if (Needle.Len() > 2 && Needle.Len() > BestLen && Norm.Contains(Needle, ESearchCase::CaseSensitive))
			{
				Best = Row;
				BestId = Pair.Key;
				BestLen = Needle.Len();
			}
		}
	}
	if (Best == nullptr)
	{
		return false;
	}
	if (bGo || Best->Directions.IsEmpty())
	{
		OutReply.Text = FText::Format(WTAText(TEXT("Follow me to {0}.")), FText::FromString(TextOf(Best->Say.IsEmpty() ? Best->Label : Best->Say)));
	}
	else
	{
		OutReply.Text = FText::Format(WTAText(TEXT("That\u2019s {0}")), FText::FromString(TextOf(Best->Directions)));
	}
	OutReply.Action = WTAAction::GoPlace();
	OutReply.ActionArg = BestId;
	// "Take me to ..." walks now; "Where is ...?" gets the directions and a button to walk there (the web's place card).
	OutReply.bOffer = !bGo && !Best->Directions.IsEmpty();
	OutReply.OfferLabel = OutReply.bOffer ? OfferLabel(WTAAction::GoPlace()) : FText::GetEmpty();
	return true;
}

bool UWTADialogueSubsystem::TryTitleMatch(const FString& Question, FWTAReply& OutReply) const
{
	const UWTAContentSubsystem* Content = ContentOf(GetGameInstance());
	if (Content == nullptr)
	{
		return false;
	}
	const FString Norm = Normalize(Question);
	int32 BestLen = 0;
	bool bFound = false;

	if (const UDataTable* Exhibits = Content->GetTable(EWTATable::Exhibits))
	{
		for (const TPair<FName, uint8*>& Pair : Exhibits->GetRowMap())
		{
			const FWTAExhibitRow* Row = reinterpret_cast<const FWTAExhibitRow*>(Pair.Value);
			if (Row == nullptr)
			{
				continue;
			}
			const FString Needle = Normalize(TextOf(Row->Title));
			if (Needle.Len() > 5 && Needle.Len() > BestLen && Norm.Contains(Needle, ESearchCase::CaseSensitive))
			{
				const FString Text = FirstSentences(TextOf(Row->Description), 2) + TEXT(" ") + Attribution(TEXT("That\u2019s \u201C{0}\u201D {1}."), TextOf(Row->Title), ExhibitWhere(*Row));
				OutReply.Text = FText::FromString(Text);
				OutReply.Action = WTAAction::OpenItem();
				OutReply.ActionArg = Pair.Key;
				BestLen = Needle.Len();
				bFound = true;
			}
		}
	}
	if (const UDataTable* Books = Content->GetTable(EWTATable::Books))
	{
		for (const TPair<FName, uint8*>& Pair : Books->GetRowMap())
		{
			const FWTABookRow* Row = reinterpret_cast<const FWTABookRow*>(Pair.Value);
			if (Row == nullptr)
			{
				continue;
			}
			const FString Needle = Normalize(TextOf(Row->Title));
			if (Needle.Len() > 5 && Needle.Len() > BestLen && Norm.Contains(Needle, ESearchCase::CaseSensitive))
			{
				const FString Sub = Row->Subtitle.IsEmpty() ? FString() : TextOf(Row->Subtitle) + TEXT(". ");
				OutReply.Text = FText::Format(WTAText(TEXT("{0}\u201C{1}\u201D is on our shelves. Want to read it?")), FText::FromString(Sub), FText::FromString(TextOf(Row->Title)));
				OutReply.Action = WTAAction::OpenBook();
				OutReply.ActionArg = Pair.Key;
				BestLen = Needle.Len();
				bFound = true;
			}
		}
	}
	if (bFound)
	{
		// Naming an exhibit or a book answers with it and offers it (the web's card); "show me ..." opens it now.
		OutReply.bOffer = !WantsItNow(Question);
		OutReply.OfferLabel = OutReply.bOffer ? OfferLabel(OutReply.Action) : FText::GetEmpty();
	}
	return bFound;
}

bool UWTADialogueSubsystem::TrySearch(FName StaffId, const FString& Question, FWTAReply& OutReply)
{
	if (!bIndexBuilt)
	{
		RebuildIndex();
	}
	if (Docs.Num() == 0)
	{
		return false;
	}

	// Unique query terms.
	TArray<FString> Raw;
	Tokenize(Question, Raw);
	TArray<FString> Terms;
	for (const FString& Term : Raw)
	{
		Terms.AddUnique(Term);
	}
	if (Terms.Num() == 0)
	{
		return false;
	}

	// IDF per term: log(1 + N / (df + 0.5)), df counting fuzzy (prefix) matches in body or title.
	const int32 N = Docs.Num();
	TArray<float> Idf;
	Idf.Reserve(Terms.Num());
	TArray<TArray<FString>> TitleTerms;
	TitleTerms.Reserve(Docs.Num());
	for (const FWTASearchDoc& Doc : Docs)
	{
		TArray<FString> T;
		Tokenize(Doc.Title, T);
		TitleTerms.Add(MoveTemp(T));
	}
	for (const FString& Term : Terms)
	{
		int32 Df = 0;
		for (int32 D = 0; D < Docs.Num(); ++D)
		{
			if (AnySame(Term, Docs[D].TermCounts) || AnySame(Term, TitleTerms[D]))
			{
				++Df;
			}
		}
		Idf.Add(FMath::Loge(1.f + static_cast<float>(N) / (static_cast<float>(Df) + 0.5f)));
	}

	// Score every document (the web's searchKB), weighted by what this staff member knows best (searchAnswer).
	int32 BestDoc = INDEX_NONE;
	float BestScore = 0.f;
	for (int32 D = 0; D < Docs.Num(); ++D)
	{
		const FWTASearchDoc& Doc = Docs[D];
		float Score = 0.f;
		for (int32 T = 0; T < Terms.Num(); ++T)
		{
			int32 Tf = 0;
			for (const TPair<FString, int32>& Pair : Doc.TermCounts)
			{
				if (SameTerm(Terms[T], Pair.Key))
				{
					Tf += Pair.Value;
				}
			}
			const bool bInTitle = AnySame(Terms[T], TitleTerms[D]);
			if (Tf > 0 || bInTitle)
			{
				Score += Idf[T] * (1.f + 0.3f * FMath::Min(3, FMath::Max(0, Tf - 1)));
				if (bInTitle)
				{
					Score += Idf[T] * 0.8f;
				}
			}
		}
		Score *= KindBias(StaffId, Doc.Kind);
		if (Score > BestScore)
		{
			BestScore = Score;
			BestDoc = D;
		}
	}
	if (BestDoc == INDEX_NONE)
	{
		return false;
	}

	// Best sentence of the best document (the web's bestSentence), with the question-type bonuses.
	const FWTASearchDoc& Doc = Docs[BestDoc];
	const FString Type = QuestionType(Question);
	float BestSentenceScore = -1.f;
	int32 BestIndex = 0;
	for (int32 S = 0; S < Doc.Sentences.Num(); ++S)
	{
		const FString& Sentence = Doc.Sentences[S];
		TArray<FString> SentenceTerms;
		Tokenize(Sentence, SentenceTerms);
		float Score = 0.f;
		for (const FString& Term : Terms)
		{
			if (AnySame(Term, SentenceTerms))
			{
				Score += 1.f;
			}
		}
		if (Type == TEXT("when") && ContainsYear(Sentence))
		{
			Score += 1.2f;
		}
		if (Type == TEXT("num") && ContainsDigit(Sentence))
		{
			Score += 1.f;
		}
		if (Type == TEXT("who") && ContainsCapitalizedPair(Sentence))
		{
			Score += 0.8f;
		}
		if (Score > BestSentenceScore)
		{
			BestSentenceScore = Score;
			BestIndex = S;
		}
	}
	FString Answer = Doc.Sentences.IsValidIndex(BestIndex) ? Doc.Sentences[BestIndex] : Doc.Title;
	if (Answer.Len() < 100 && Doc.Sentences.IsValidIndex(BestIndex + 1))
	{
		Answer += TEXT(" ") + Doc.Sentences[BestIndex + 1];
	}
	if (!Doc.Source.IsEmpty())
	{
		Answer += TEXT(" ") + Doc.Source;
	}
	OutReply.Text = FText::FromString(Answer);
	OutReply.Action = Doc.Action;
	OutReply.ActionArg = Doc.ActionArg;
	// A keyword match is a suggestion: offer it as a button (the web's card) unless the player asked to be shown.
	OutReply.bOffer = !Doc.Action.IsNone() && !WantsItNow(Question);
	OutReply.OfferLabel = OutReply.bOffer ? OfferLabel(Doc.Action) : FText::GetEmpty();
	return true;
}

FWTAReply UWTADialogueSubsystem::Fallback(FName StaffId) const
{
	FWTAReply Reply;
	const UWTAContentSubsystem* Content = ContentOf(GetGameInstance());
	const FWTAStaffRow* Staff = Content ? Content->FindStaff(StaffId) : nullptr;
	if (Staff != nullptr && !Staff->Fallback.IsEmpty())
	{
		Reply.Text = Staff->Fallback;
	}
	else
	{
		Reply.Text = WTAText(TEXT("I\u2019m not sure about that one. Try asking about the museum, the library, the workshop rooms or the Recess Yard."));
	}
	Reply.Action = NAME_None;
	Reply.ActionArg = NAME_None;
	return Reply;
}

// --- Text helpers (static) -----------------------------------------------------

void UWTADialogueSubsystem::Tokenize(const FString& Text, TArray<FString>& OutTokens)
{
	TokenizeImpl(Text, OutTokens);
}

void UWTADialogueSubsystem::SplitSentences(const FString& Text, TArray<FString>& OutSentences)
{
	SplitSentencesImpl(Text, OutSentences);
}

int32 UWTADialogueSubsystem::CountWords(const FString& Text)
{
	return CountWordsImpl(Text);
}

void UWTADialogueSubsystem::AddDoc(const FString& Title, const FString& Body, FName Action, FName ActionArg)
{
	FWTASearchDoc Doc;
	Doc.Title = Title;
	Doc.Action = Action;
	Doc.ActionArg = ActionArg;
	SplitSentences(Body, Doc.Sentences);
	TArray<FString> Terms;
	Tokenize(Body, Terms);
	Doc.NumTerms = Terms.Num();
	for (const FString& Term : Terms)
	{
		Doc.TermCounts.FindOrAdd(Term)++;
	}
	for (const TPair<FString, int32>& Pair : Doc.TermCounts)
	{
		DocFrequency.FindOrAdd(Pair.Key)++;
	}
	Docs.Add(MoveTemp(Doc));
}
