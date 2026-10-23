# The campus in another language

A client pack names its language in `campus.json` (`"language": "es"`); `build_client.py` sets `WTA_LANG`, and
`data/build_data.py` then writes every DataTable in that language from this folder:

- `lang/<lang>/strings.json` — the engine's own words (buttons, kickers, toasts, hints, the certificate's lines,
  the months): `{"English key": "translation"}`. The keys are what the C++ writes (`WTAText("Close")`);
  `unreal/Tools/common/extract_strings.py` lists them all as `strings.en.json`, and `--check lang/es/strings.json`
  says which a language is missing. Patterns keep their `{0}` `{1}` slots. Becomes `DT_Strings`, read by
  `UWTAContentSubsystem::Tr`.
- `lang/<lang>/tables.json` — the content's words, in the rows' own shape: `{"DT_Exhibits": {"<row>": {"Title": ...,
  "Description": ...}}, "DT_Books": {"<row>": {"Pages": [{"Heading": ..., "Blocks": [{"Text": ...}]}]}}}`.
  `unreal/Tools/common/extract_tables.py` writes every Text field of every row as `tables.en.json` (the shape to
  fill), and `--check lang/es/tables.json` lists what is missing or still English. Arrays keep their positions
  (`null` for an item with nothing to translate). Staff rules carry their `Pattern` (a regex) too: a language
  needs its own question patterns, written as `(english|spanish)` alternatives so both are understood. Places
  carry their `Aliases` (what a visitor may type for the place): keep the English list and append the language's
  names; a longer list adds them. The staff fold accents when they read a question ("dónde" = "donde"), so one
  spelling is enough there; the regexes see the question as typed, so write them accent-tolerant (`d[oó]nde`).
- The seven question-shape regexes the staff use on their own (take me / where is / a greeting / show me / when /
  how many / who) and the list of stop words they ignore are keys in `strings.json` like any other (they begin
  with `\b` or `^`, and the stop list with `a an the and`): a language returns each with its own alternatives
  appended after the English, so the staff read the shape of a question in both.
- Voices: `unreal/Tools/voice/make_talk_voices.py --lang es` reads the built tables (DT_Talks, DT_Stations) in
  Kokoro's Spanish voices (ef_dora, em_alex) into `out/voice/es/`; the clip names stay the same, so the
  language's clips are imported in place of the English ones for that build.

- Slides: `bl/slides.py` draws them in the language too (the DT_Talks rows of `tables.json` over `talks.json`,
  slide for slide), and its own few words ("A talk", the venue names) come from `lang/<lang>/builders.json`
  (`{"English": "translation"}`).

One language per build: the tables, the voices and the slides are all in it. What stays English for now: the
words the other builders draw into textures (the room signs, the course board, the classroom board, the shop
screens; `builders.json` is where their words go once they read it) and the staff's regex macros
(`data/staff_rules_ue.py`), which a language extends with its own alternatives in `tables.json`.

## Spanish (`lang/es`)

The first language in: `es/strings.json` (all 193 of the engine's words, the seven question shapes and the stop
words with Spanish alternatives), `es/tables.json` (every row of the 18 tables, 2,582 strings; staff rule patterns
as `english|spanish`; Spanish aliases added to every place) and `es/builders.json` (the slide kickers). Neutral
Latin American Spanish, the visitor addressed as "tú"; names, product names, URLs and the ride names stay as they
are; "Mr. Hale" is "Sr. Hale", "Coach Rae" stays. A build in Spanish: `"language": "es"` in the pack's
`campus.json`, or `WTA_LANG=es` before `build_data.py`, `bl/slides.py` and `make_talk_voices.py`; the
`data_tables` setup step then writes DT_Strings with 179 rows (the 14 keys that are only slots and marks stay as
they are) and the rest of the tables in Spanish. Checks: `extract_strings.py --check lang/es/strings.json` and
`extract_tables.py --check lang/es/tables.json` both report 0 missing.
