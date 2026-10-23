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
  needs its own question patterns, written as `(english|spanish)` alternatives so both are understood.
- Voices: `unreal/Tools/voice/make_talk_voices.py --lang es` reads the built tables (DT_Talks, DT_Stations) in
  Kokoro's Spanish voices (ef_dora, em_alex) into `out/voice/es/`; the clip names stay the same, so the
  language's clips are imported in place of the English ones for that build.

One language per build: the tables, the voices and the slides (`bl/slides.py` draws the pack's `talks.json`)
are all in it. What stays English for now: the words drawn into the builders' textures (signs, the course board,
the classroom board) and the staff's regex macros (`data/staff_rules_ue.py`), which a language extends with its
own alternatives in `tables.json`.
