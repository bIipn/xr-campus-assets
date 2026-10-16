# XRLibraries Campus — content inventory and Unreal DataTable spec

Source: `/home/user/xr-campus-assets/parts/*.js` (three.js r170 web build, assembled by `assemble.py`).
Extractor: `ue/tools/extract_content.mjs` (Node 22, `node:vm` sandbox, no rendering code executed).
Output: `ue/content/*.json` + `ue/content/_manifest.json` (file → count → source lines → what it drives).
All 33 files parse and match hand-verified record counts (`ALL DATASETS VALID`).

Read this together with `_manifest.json`; the manifest is generated and is the authority for line ranges.

---

## 0. Global conventions for the Unreal port

### 0.1 Which source is live
`assemble.py` concatenates this PARTS list: `helpers, data, art, world, rooms, bpdata, bpdraw, outdoor, nature, gfx, dive, nav, people, hkrig, humans, hkik, waxfig, waxpaint, waxprops, waxscenes, waxhall, stations, blueprints, lab, worldroom, paint, rides, phys, socpose, soccer, socplay, hands, baked, xr, progress, engine, ui`.
**`parts/books.js` is not in the list** — it is an orphaned, older "Pine Hollow" edition that also declares `SUBJECTS`/`BOOKS`. The live library is `parts/data.js`. The orphan is exported as `books_legacy_pine_hollow.json` for reference only.

Datasets are mutated at load time in this order (matters for counts):
- `worldroom.js:279` `BOOKS.push(WB_BOOK)` → BOOKS has **15** books at runtime (14 in data.js + the World Builder's Handbook).
- `waxhall.js:445-449` builds `WAX_ITEMS` (12) from `WAX_SCENES[i].item`, adding `id, kind:'reenactment', hall, scene, year`.
- `engine.js:104` appends 8 "section" places to `PLACES` (one per SUBJECT) → **42** places.
- `ui.js:128-139` expands `STOPS` with `...ITEMS` (15) and `...WAX_ITEMS` (12) → **35** tour stops.

### 0.2 Units, axes, rotations (must match `unreal/Pipeline`)
- Web data is in **metres, three.js axes: right-handed, +y up, −z = "into the museum"** (lobby at z∈[−6,0], Gallery 3 ends at z=−42, Wax Hall to z=−81, library at x<−12, school at x>12, yard x∈[34,92]).
- The repo's own UE convention (`unreal/Pipeline/blender/export_reading_room.py:18-20`): glTF/campus `(x, y, z)` m → Unreal `(X = x, Y = z, Z = y)` × 100 cm. Apply the **same** mapping to every position in these JSONs so DataTable rows line up with the imported `.glb` wings. Verify once on import against a tagged landmark (e.g. node `token__t-museum` vs `tokens.json` `[-5.35, 0.36, -41.35]`). I have not independently confirmed the importer's axis permutation; the pipeline doc asserts it.
- Camera/stand "views" are `{x, z, yaw, pitch}` (radians). Eye height is 1.62 m (`world-builder` handbook p.3). Yaw convention is defined by `lookYaw(fx,fz,tx,tz) = atan2(-(tx-fx), -(tz-fz))` (`outdoor.js:12`): yaw 0 faces −z. Forward vector in campus space is `(−sin yaw, 0, −cos yaw)`. Under the mapping above, the UE forward is `(X, Y) = (−sin yaw, −cos yaw)`, so **UE Yaw° = degrees(atan2(−cos yaw, −sin yaw))** (yaw 0 → −90°, i.e. facing −Y). Pitch is positive looking up in both → **UE Pitch° = degrees(pitch)**. Verify with one place (`PLACES.drop` looks up at the tower: pitch 0.32).
- 2-D boxes `{x0,x1,z0,z1}` are floor rectangles in campus x/z (→ UE X/Y).
- Colours arrive as `#rrggbb` strings (converted from three.js ints by the extractor) → `FColor::FromHex` / `FLinearColor` (sRGB). Some tables keep CSS `rgba()` only in code, not in data.

### 0.3 Type mapping used below
| JSON | USTRUCT field type | note |
|---|---|---|
| `id` / enum-like string | `FName` | row key; also the `Name` column of the DataTable |
| user-visible string | `FText` | localisable |
| raw/technical string (regex, source code, url) | `FString` | |
| number | `float` / `int32` | |
| `[x,y,z]` metres | `FVector` (cm, remapped per 0.2) | |
| `{x,z,yaw,pitch}` | `FCampusView` (nested USTRUCT: `FVector Location; FRotator Rotation; bool bValid`) | |
| `{x0,x1,z0,z1}` | `FBox2D` | or four floats |
| `#rrggbb` | `FLinearColor` | |
| list | `TArray<T>` | no `TArray<TArray<>>` — wrap in a struct |
| asset reference | `TSoftObjectPtr<UTexture2D>` / `TSoftObjectPtr<USkeletalMesh>` / `TSoftObjectPtr<ULevelSequence>` | filled in by the editor Python step |

Every row struct is `USTRUCT(BlueprintType) struct FXxxRow : public FTableRowBase` (`Engine/DataTable.h`). Nested structs are plain `USTRUCT(BlueprintType)`. All members `UPROPERTY(EditAnywhere, BlueprintReadOnly)`.

### 0.4 Import path (for the editor-Python step, not part of this task)
The JSON here is a faithful extraction (camelCase keys, as in the JS). A converter must emit UE-shaped JSON: an array of row objects each with a `"Name"` key (row name = `id`) and PascalCase property names matching the struct, `FVector` as `{"X":..,"Y":..,"Z":..}`, `FLinearColor` as `{"R":..,"G":..,"B":..,"A":1}`. Load with `UDataTableFunctionLibrary::FillDataTableFromJSONString(DataTable, JsonString)` (`Kismet/DataTableFunctionLibrary.h`; exposed to Python as `unreal.DataTableFunctionLibrary.fill_data_table_from_json_string` — confirm the exact Python name in the target UE version before relying on it). Create the asset with `unreal.DataTableFactory` (set its `struct` to the row USTRUCT) via `AssetToolsHelpers.get_asset_tools().create_asset(...)`. Long prose (`aiSystemPrompt`, book pages) is fine in DataTables; UI chrome strings (`ui_strings.json`) belong in a `UStringTable` instead.

---

## 1. Datasets

Each entry: **file** · JS variable · `source file:lines` · count · record shape · what it drives · USTRUCT.

### 1.1 `sources.json` — citations
`SOURCES` · `parts/data.js:4-27` · **22** records (object keyed by id → exported as array).
Shape: `{ id:string, label:string, url:string }`.
Drives: the "Source:" chips on every exhibit/scene card (`srcList()` data.js:387), `srcLine()` in staff answers (engine.js:185).
```cpp
USTRUCT(BlueprintType) struct FSourceRow : public FTableRowBase {
  UPROPERTY() FName Id; UPROPERTY() FText Label; UPROPERTY() FString Url; };
```

### 1.2 `galleries.json` — the four museum rooms
`GALLERIES` · `data.js:29-34` · **4** (index 0 = Lobby, 1–3 = galleries).
Shape: `{ index, label, name, years, z0, z1, wall:'#rrggbb' }`.
Drives: gallery name/years plaques, per-gallery wall colour, `itemWhere()` labels, search grouping.
```cpp
struct FGalleryRow : FTableRowBase { int32 Index; FText Label; FText Name; FText Years; float Z0; float Z1; FLinearColor WallColor; };
```

### 1.3 `exhibit_kinds.json` — kind labels
`KIND` · `data.js:35` · **9**: milestone, mission, object, event, program, story, resource, project, reenactment.
```cpp
struct FExhibitKindRow : FTableRowBase { FName Id; FText Label; };
```

### 1.4 `exhibits.json` — museum exhibits (+ Freedom to Read)
`ITEMS` (15) + `FREEDOM` (1) · `data.js:37-106`, `108-111` · **16**.
Shape: `{ id, location:'gallery'|'library', g:1|2|3|null, kind, title, date:string, year:int|null, where, partners, src:[sourceId], desc, more?, quote?, quoteBy?, place?:{wall:'L'|'R'|'P'|'E', z?, x?}, size?:[w,h] (metres), object?:'headset'|'book', art:{type, ...generator params} }`.
`place.wall`: L/R = left/right gallery wall at depth `z`; P = pedestal object at (x,z); E = end wall. `art.type` ∈ bignum, quote, headset, badge, sectors, story, playbook, episodes, shipyard, armap, scan, drawings, pollinators, freedom — each is a **procedural canvas painter** in `parts/art.js` / `art2.js` (`ART[type]`), with params (`num,l1,l2,kick,motif,dots,bg`) for `bignum`. The existing `unreal/Pipeline/web/export_campus.py` rasterises them to `out/campus/art/<id>.png`.
Drives: wall frames/pedestals (`world.js`), catalog card (title/kind/date/where/partners/desc/more/quote/sources), tour stops, search, KB (`buildKB` kind=item), AI prompt, badge `explorer` (5 opened).
```cpp
USTRUCT(BlueprintType) struct FExhibitPlacement { FName Wall; float X; float Z; };
USTRUCT(BlueprintType) struct FExhibitArt { FName Type; FString BigNumber; FText Line1; FText Line2; FText Kicker; FName Motif; int32 Dots; FLinearColor Background; TSoftObjectPtr<UTexture2D> Texture; };
USTRUCT(BlueprintType) struct FExhibitRow : public FTableRowBase {
  FName Id; FName Location; int32 Gallery; FName Kind; FText Title; FText DateLabel; int32 Year; FText Where; FText Partners;
  TArray<FName> Sources; FText Description; FText More; FText Quote; FText QuoteBy;
  bool bHasPlacement; FExhibitPlacement Placement; FVector2D FrameSize; FName PedestalObject; FExhibitArt Art; };
```

### 1.5 `facts.json` — what the staff know beyond the exhibits
`FACTS` · `data.js:114-130` · **15** (ids: what, who, team, wsl, freedom, environment, partners, sjsu, xrmarin, concept, yard, school, wax, history, wta).
Shape: `{ id, src:[sourceId], text }`. Drives: KB kind=fact, several preset answers (`RX.what/director/wax/history/wta`), AI prompt "Facts:" block.
```cpp
struct FFactRow : FTableRowBase { FName Id; TArray<FName> Sources; FText Text; };
```

### 1.6 `subjects.json` — library sections
`SUBJECTS` · `data.js:133-142` · **8** (basics, programs, careers, story | equity, environment, worlds, tech).
Shape: `{ id, name, side:'N'|'S', slot:0..3, color }`. Drives: the eight stacks and their spine colour (`world.js:384-438`, `SHELF_VIEWS`), "section" places, Rosa's `RX.sections` answer, search group label.
```cpp
struct FSubjectRow : FTableRowBase { FName Id; FText Name; FName Side; int32 Slot; FLinearColor Color; };
```

### 1.7 `books.json` — readable books
`BOOKS` · `data.js:145-384` (14) + `WB_BOOK` `worldroom.js:265-278` (1, `table:false`) · **15** books, **82** pages.
Shape: `{ id, subject, icon, title, sub, table?:false, pages:[{ h, b:[ block ] }], pageCount }`, block = `string | {li:[string]} | {q:string} | {note:string} | {code:string}` (`blockText()` data.js:386 flattens for search).
Icons used: headset, phone, checklist, case, camera, mic, ship, lens, wave, drop, globe, code, network (procedural cover art `drawBookCover`).
Drives: featured-table and stack-end book props, the reader panel, Rosa's `recommend()`, tour "Read a book", `BOOK['world-builder']` opened from Room 104 monitors (`hb` = page), badge `bookworm` (5 pages), KB kind=page, AI prompt "Books:" block.
```cpp
UENUM(BlueprintType) enum class EBookBlock : uint8 { Paragraph, List, Quote, Note, Code };
USTRUCT(BlueprintType) struct FBookBlock { EBookBlock Type; FText Text; TArray<FText> Items; };
USTRUCT(BlueprintType) struct FBookPage  { FText Heading; TArray<FBookBlock> Blocks; };
USTRUCT(BlueprintType) struct FBookRow : public FTableRowBase {
  FName Id; FName Subject; FName Icon; FText Title; FText Subtitle; bool bOnFeaturedTable; TArray<FBookPage> Pages; TSoftObjectPtr<UTexture2D> Cover; };
```

### 1.8 `blueprints.json` — Room 103 boards
`BP_INFO` + `BP_ORDER` · `bpdata.js:4-95, 96`; `BP_PLACE` · `blueprints.js:4-10` · **5** blueprints × **12** parts = 60 parts.
Shape: `{ id, order, title, dwg:'BP-0n', sub, spec, overview, build:[string×5], jobs, parts:[{index, name, short, what, fact, model}], place:{x,y,z,ry,wall} }`.
Drives: wall boards (board size 2.9 × 1.8125 m, `BP_BW/BP_BH`), the blueprint viewer with numbered callouts, KB kind=part (Mr. Hale), search "Blueprints" group, badge `engineer` (3 opened). The line drawings themselves are vector data in `bpdraw.js` (`BP_CAR … BP_COMPUTER`, 1280×800 canvas) — **not content; re-render to textures**.
```cpp
USTRUCT(BlueprintType) struct FBlueprintPart { int32 Index; FText Name; FText Short; FText What; FText Fact; FText Model; };
USTRUCT(BlueprintType) struct FBlueprintRow : public FTableRowBase {
  FName Id; int32 Order; FText Title; FString DrawingNumber; FText Subtitle; FText Spec; FText Overview; TArray<FText> BuildSteps; FText Jobs;
  TArray<FBlueprintPart> Parts; FVector BoardLocation; float BoardYawRad; FName BoardWall; TSoftObjectPtr<UTexture2D> BoardTexture; };
```

### 1.9 `wax_scenes.json` — the 12 living-history stages
`WAX_SCENES` · `waxscenes.js:46-605` (+ card assembly `waxhall.js:445-449`) · **12** scenes, **38** figures.
Shape: `{ id, n, year:string, yearNum, title, backdrop, floor, loopSeconds, lines:[{t, text}], item:{…exhibit card…}, cast:[{var, avatar, look:{…}, at:[x,z], ry:deg}], propsUsed:[WP.* names], headsetProps:int, hasTick, buildSrcLines }`.
- `backdrop` ∈ library, calmap, storyroom, reopening, shelter, catalog, farm, careers, forest360, shipyard, vrgallery, fair; `floor` ∈ carpet, boards, rug, tile, gym, office, grass, concrete, meeting, dock, grid, fair — both are **procedural paintings** (`waxpaint.js`) → textures/materials in UE.
- `cast[].avatar` = Microsoft Rocketbox id (`hk/` build; e.g. `fa12` female adult 12, `mc02` male child 02). `look` keys seen across the cast: av, scale, body, skin, hair, hairStyle, top, bottom, collar, lanyard, shoes, eyes, sleeves, legs, socks, jacket, glasses, cap, beard, dye, hem, tights, dress, scarf (colours are hex; `WAX_SKIN` presets resolved). Keep any key not modelled in `FWaxFigure` in `ExtraLookJson`.
- **37 unique Rocketbox avatars** are referenced by the wax cast (38 figures) plus staff: bf02 bf03 bm05 fa01 fa03 fa05 fa06 fa07 fa08 fa09 fa11 fa12 fa14 fa15 fa17 fc01 fc02 fp02 gm01 ma02 ma04 ma05 ma06 ma07 ma09 ma12 ma14 ma16 ma17 ma18 ma20 mc01 mc02 mf01 mm03 mm04 sf02 — this is the skeletal-mesh import list for the `hk/` build.
- Props placed per scene (`propsUsed`, from `WP.*` in `waxprops.js`): bookcase, butterfly, chair, crate, desk, fish, flower, mat, pc, screen, swim (animated fish), wire; plus the shared `waxHeadset()` prop (`headsetProps` per scene).
- Stage geometry: `WH` (`doors.json.waxHall`): bay 5.6 m wide, 3.9 m deep, stage 0.2 m high, rope at 4.45 m, five bays per side from z=−45.3, last two across the far wall.
- **Not extracted (animation, not content):** per-figure keyframes `S.keys(fig,[WK(t,{pose})…])`, prop carries `S.carry(prop, grips, [WCK…],[WCH…])`, `S.tick(t)` effects (map dots, whale, confetti, planet…). `cast[].var` + `buildSrcLines` tell you where to look (`waxscenes.js`). In UE these become per-scene Level Sequences / anim montages on the Rocketbox skeleton; `wax_poses.json` (9 scene poses) + `WAX_POSE` base set in `waxfig.js:515+` are the pose vocabulary (degrees, bones hips/spine/chest/neck/head/shL/elL/wrL/…).
Drives: the Wax Hall stages, reading-rail captions (timed to the loop), the scene catalog cards (also tour stops 18–29 and KB items), badge `historian` (6 scenes watched), `RX.wax/history` answers.
```cpp
USTRUCT(BlueprintType) struct FWaxLine { float Time; FText Text; };
USTRUCT(BlueprintType) struct FWaxFigure { FName Var; FName AvatarId; TSoftObjectPtr<USkeletalMesh> Avatar; float Scale; FName Body; FLinearColor Skin; FLinearColor Hair; FName HairStyle;
  FLinearColor Top; FLinearColor Bottom; FLinearColor Collar; FLinearColor Shoes; FLinearColor Eyes; FName Sleeves; FName Legs; bool bGlasses; FName Beard; FVector2D StagePos; float YawDeg; FString ExtraLookJson; };
USTRUCT(BlueprintType) struct FWaxSceneRow : public FTableRowBase {
  FName Id; int32 Number; FText YearLabel; int32 Year; FText Title; FName Backdrop; FName Floor; float LoopSeconds; TArray<FWaxLine> Lines;
  FName CardExhibitId /* row in exhibits-like table or duplicate the FExhibitRow fields */; TArray<FWaxFigure> Cast; TArray<FName> PropsUsed; int32 HeadsetProps;
  TSoftObjectPtr<ULevelSequence> Sequence; };
```
Recommended: put the 12 `item` cards into the same `FExhibitRow` table (Location = "wax", Gallery = 0) so cards/tour/search use one table, as the web build's `ITEMS.concat([FREEDOM], WAX_ITEMS)` does.

### 1.10 `staff.json` — the four virtual staff
`STAFF` · `people.js:4-21`; `GREET/CHIPS` · `ui.js:203-214`; `JOKES` · `engine.js:153-158`; `greetingShort/helpText/fallbackText` · `engine.js:314-326`; `staffRules()` · `ui.js:322-355` (rendered) · **4**.
Shape: `{ id, name, role, mono, color, rooms:[roomId], track:[roomId]|null, pos:{x,z}, face:{x,z}, look:{av, body, top, bottom, skin, hair, hairStyle, collar?, glasses?, apron?, mustache?, rolled?, cap?, whistle?}, view:{x,z,yaw,pitch}, greeting, greetingShort, help, fallback, joke, chips:[4], aiSystemPrompt }`.
Avatars: margaret `bf02`, rosa `fa14`, hale `ma05`, rae `sf02`. `rooms` = where that staff member is "yours" (`staffFor(roomId)`, people.js:118), `track` = rooms where the head tracks you. `aiSystemPrompt` (~20 KB each) is the exact text `staffRules()` builds from FACTS/exhibits/books/places — regenerate it from the tables in UE rather than storing it, or keep as a reference.
Drives: NPC spawn (Rocketbox + idle/blink/talk `staffIdleHuman`), floating name label, chat panel header/greeting/chips, fallback and help replies, joke, LLM prompt.
```cpp
USTRUCT(BlueprintType) struct FStaffRow : public FTableRowBase {
  FName Id; FText Name; FText Role; FString Monogram; FLinearColor Color; TArray<FName> Rooms; TArray<FName> TrackRooms;
  FVector Location; FVector FaceTarget; FName AvatarId; TSoftObjectPtr<USkeletalMesh> Avatar; FLinearColor Top; FLinearColor Bottom; FLinearColor Skin; FLinearColor Hair; FName HairStyle;
  bool bGlasses; bool bMustache; bool bWhistle; bool bApron; bool bRolledSleeves; FLinearColor Cap; FLinearColor Collar;
  FCampusView TalkView; FText Greeting; FText GreetingShort; FText Help; FText Fallback; FText Joke; TArray<FText> Chips; FString AiSystemPrompt; };
```

### 1.11 `staff_answers.json` — offline chat brain
`RX` (**43** regex intents) · `engine.js:108-152`; `presetAnswer()` (**45** ordered `return reply(...)` branches, 19 with a static string, 26 templated) · `engine.js:192-265`; `directions()` (**42**, one per place) · `engine.js:266-280`; search engine notes · `engine.js:4-66, 281-307`.
Shape: `{ rules:[{id, pattern, flags}], presetBranches:[{order, line, conditionSrc, rulesUsed, staffOnly, staffNot, staticText|null, replySrc, extraSrc, action, cardsSrc}], directions:[{placeId, text}], kbSearch:{…} }`.
`action` values: `paint`, `paintBlank`, `station:<id>`, `bp:<id>`, `workshops`, `paintOffer`, `ride:<id>`. Cards: `itemCard`, `bookCard`, `placeCard`, `rideCard`, `badgesCard`, `stationCard`, `bpCard`.
Templated (non-static) branches by order: 1 hi, 4 who, 5 help, 7 wta, 9 joke, 12 move, 15 startLab, 16 openBp, 23 what, 24 director, 25 rideNow, 26 tokens, 27 badges, 28 wax, 29 year lookup, 30 history, 31 go/where place, 32 oldest/newest, 33–37 counts (books/sections/rides/scenes/exhibits), 38 sections, 39 recommend, 41 ride safety, 42 ride stats, 44 ride about; the final fallthrough is `searchAnswer()`.
Templated branches depend on live state/tables (counts: `ITEMS.length`, `BOOKS.length`, `SUBJECTS` names, `COASTER.stats`, `DROP`, `prog.tokens.size`, year lookups, `recommend()`, `findPlace()`). They must be re-implemented as code; the JSON keeps the exact JS expression so nothing is lost.
Regex: the patterns are ECMAScript; UE's `FRegexPattern`/`FRegexMatcher` (`Internationalization/Regex.h`, ICU) accepts `\b`, groups, alternation, `(?:…)`, `\w`, `\s`, `\d`; check `'?s`-style literal quotes and `^\s*` anchors behave the same (`toks()`/`norm()` lower-case and strip punctuation first).
```cpp
struct FIntentRuleRow : FTableRowBase { FName Id; FString Pattern; FString Flags; };
struct FPresetReplyRow : FTableRowBase { int32 Order; TArray<FName> RulesUsed; TArray<FName> StaffOnly; TArray<FName> StaffNot; bool bStatic; FText StaticText; FString ConditionSource; FString ReplySource; FName Action; FString CardsSource; };
struct FDirectionRow : FTableRowBase { FName PlaceId; FText Text; };
```

### 1.12 `lessons.json` — what the stations teach
`LESSONS` · `engine.js:30-42` · **11** (sieve×5, titration×2, pendulum×1, bench×2, diorama×1).
Shape: `{ id, station, title, text }`. Drives: KB kind=lesson (Mr. Hale answers), search "Workshops" group.
```cpp
struct FLessonRow : FTableRowBase { FName Id; FName Station; FText Title; FText Text; };
```

### 1.13 `places.json` — navigation targets
`PLACES` · `engine.js:69-104` · **42** (34 literal + 8 `sec-<subject>`).
Shape: `{ id, label, say|null, names:[aliases], view:{x,z,yaw,pitch}|null, viewRef:'@station:<id>'|'@blueprint:<id>'|'@shelf:<subject>'|null, viewSrc }`. 24 have a static view; 18 reference a live view (station `view()` depends on step; `bpViewFor(id)`; `SHELF_VIEWS` computed in `world.js:438`).
Drives: `findPlace()` alias matching for "take me to …", `placeCard`, `directions`, search Places group, minimap taps (`MAP_GO`).
```cpp
struct FPlaceRow : FTableRowBase { FName Id; FText Label; FText SayAs; TArray<FString> Aliases; bool bHasView; FCampusView View; FName ViewRef; };
```

### 1.14 `tour.json` — guided tour
`STOPS` · `ui.js:128-139` · **35** stops: lobby, 15 exhibits, wax intro, 12 wax scenes, library, studio, lab, blueprint, world, yard.
Shape: `{ index, kind, itemId|null, title, date, text, view|null, viewRef:'@itemView:<id>'|'@lobbyView'|null, openLabel|null, actSrc|null }`.
Item stops take their view from `itemView(it)` (`ui.js:68`: frame view / `waxView(scene)`). `@lobbyView` is computed from the viewport (`world.js:137`, 3.4–5.4 m back from the door). `actSrc` maps to: open book `what-is-xr`, `startPaint()`, `openStation('sieve')`, `openBp('car')`, `openStation('diorama')`, `openRide('coaster')`.
```cpp
UENUM() enum class ETourAction : uint8 { None, OpenBook, StartPaint, OpenStation, OpenBlueprint, OpenRide };
struct FTourStopRow : FTableRowBase { int32 Index; FName Kind; FName ItemId; FText Title; FText DateLabel; FText Text; bool bHasView; FCampusView View; FName ViewRef; FText OpenLabel; ETourAction Action; FName ActionArg; };
```

### 1.15 `badges.json` / `tokens.json` — progress
`BADGES` · `progress.js:5-21` · **15**; `TOKENS` · `progress.js:23-35` · **11**.
Badge shape `{ id, name, how }`; icons are drawn procedurally (`drawBadgeIcon` progress.js:120-142) → 15 textures to author. Award triggers are code (`award('x')` in stations, rides, progress; thresholds: explorer 5 exhibits, bookworm 5 pages, engineer 3 blueprints, historian 6 wax scenes, first-steps 5 m walked, hunter all 11 tokens).
Token shape `{ id, place, hint, wing, at:[x,y,z]|absent, ride?:'coaster'|'drop'|'dive' }`; 8 have fixed positions, 3 are anchored to ride geometry at runtime (`tokenPos()` progress.js:45-50: coaster loop, drop top −2.75 x / +1.3 y, dive path). Persistence key `xr-campus-progress-v1` (localStorage) → `USaveGame`.
```cpp
struct FBadgeRow : FTableRowBase { FName Id; FText Name; FText How; TSoftObjectPtr<UTexture2D> Icon; };
struct FTokenRow : FTableRowBase { FName Id; FText Place; FText Hint; FName Wing; bool bFixed; FVector Location; FName RideAnchor; };
```

### 1.16 `rides.json` — Comet Coaster, Sky Drop, Ocean Dive
`RIDES` · `rides.js:4-8`; `rideText/rideNote` · `rides.js:16-26`; `rideAbout/rideStats/rideSafety/dropKmh` · `engine.js:166-182`; `COASTER.stats`, `DROP`, `DOME` · `outdoor.js:6-7, 456` · **3**.
Shape: `{ rides:[{id, name, kick, exitView, badge, cardText, cardNote, staffAbout, staffStats, staffSafety}], coasterStats:{height:19,kmh:62,mph:39,loop:10,length:170}, dropTower:{x:78,z:13,base:1,top:31,h:34}, diveDome:{x:54,z:16,r:4.2}, dropFreefallKmh }`.
Track geometry (`COASTER` spline, `DIVE_PTS`) is procedural; the dive path is in `dive_facts.json`.
```cpp
struct FRideRow : FTableRowBase { FName Id; FText Name; FText Kicker; FCampusView ExitView; FName BadgeId; FText CardText; FText CardNote; FText StaffAbout; FText StaffStats; FText StaffSafety; };
```

### 1.17 `dive_facts.json` — Ocean Dive captions
`DIVE_FACTS` · `dive.js:7-17` · **9**; `DIVE_CREATURES` (4 tappable), `DIVE_PTS` (14-point path, local to `DV` origin x=420, metres), `DV`.
Shape: facts `{ index, at:[x,y,z]|null, u?:0..1, look?:'anemone'|'turtle'|'school'|'shark'|'manta'|'jelly', text }`.
```cpp
struct FDiveFactRow : FTableRowBase { int32 Index; bool bAtPoint; FVector Location; float PathU; FName LookAt; FText Text; };
```

### 1.18 `stations.json` — the five hands-on stations
`STATION_CARDS` · `ui.js:305-311`; `STATIONS.*` blocks · `lab.js:329+, 572+, 694+`, `blueprints.js:361+`, `worldroom.js:131+` · **5**.
Shape: `{ id, card:{k,t,m,go}, file, lines, room, kick, usesHands, stepTitles|null, panelTexts:[{kind:'stp'|'stnote'|'sthint'|'stresult'|'stwarn'|'sth3', text}], buttonLabels:[], toasts:[] }`.
Only the **literal** copy was extracted. The simulations are code and must be rebuilt: sieve analysis (`psdNew()` random sample, `SIEVES` table, GFN/D50 maths), titration (`titrNew()` random molarity, meniscus readings), pendulum (`T = 2π√(L/g)`, 10-swing timer, T²–L fit), bench (hand animations `hands.js`), diorama (layer reveal). Dynamic result strings (`benchDrive` "It rolled N meters…", `benchShakeText`, pendulum "g = …") are in code.
```cpp
struct FStationTextItem { FName Kind; FText Text; };
struct FStationRow : FTableRowBase { FName Id; FName Room; FText Kicker; FText CardKicker; FText CardTitle; FText CardSub; FText CardGo; bool bUsesHands; TArray<FText> StepTitles; TArray<FStationTextItem> PanelTexts; TArray<FText> ButtonLabels; TArray<FText> Toasts; };
```

### 1.19 `world_layers.json`, `bench_kits.json`, `sieves.json`
- `DIO_STEPS` · `worldroom.js:6-16` · **9** `{ index, t, d, page }` → `FWorldLayerRow { int32 Index; FText Title; FText Description; int32 HandbookPage; }`.
- `BENCH_KITS` · `blueprints.js:251-271` · **2** kits, **15** steps `{ index, t, d, w, show:[partKey], act?, test? }` → `FBenchStep { int32 Index; FText Title; FText Instruction; FText Why; TArray<FName> ShowParts; FText ActionLabel; bool bTest; }`, `FBenchKitRow { FName Id; FText Name; TArray<FBenchStep> Steps; }`.
- `SIEVES` · `lab.js:40` · **12** `{ index, mesh, openingMicrons, afsMultiplier }` → `FSieveRow { int32 Index; FString Mesh; int32 OpeningMicrons; int32 AfsMultiplier; }`.

### 1.20 `rooms.json`, `doors.json`, `map_rooms.json` — layout
- `ROOMS` (**15** walkable AABBs) + `ROOM_INFO` (12 HUD tags) · `nav.js:5-21, 27-40` → `FRoomRow { FName Id; FBox2D Bounds; int32 Gallery; FText TagKicker; FText TagName; FText TagSub; }`.
- `DOORS` (**14**), `NOGO` (5), `M_WALL`=0.45, `SCHOOL_DOORS`, `ROOM_NAMES`, `WH` · `nav.js:23-25, 41-50`, `rooms.js:7-8`, `waxhall.js:7` → `FDoorRow { FName Axis; float At; float Center; float Width; float Band; }`; NOGO → `TArray<FBox2D>` on a level config asset.
- `MAP_ROOMS` (**17**) + `MAP_GO` · `ui.js:677-696` → `FMapRoomRow { FName Id; FBox2D Bounds; FText Label; FName AlsoRoom; bool bOutdoor; bool bRound; FName GoPlace; }` (minimap bounds x −33..92, z −82..26).
In UE these are navmesh/trigger-volume inputs, not gameplay text; keep them for parity checks and the room-tag HUD.

### 1.21 `paint_tools.json`, `physics_props.json`, `playbook_categories.json`, `world_screens_tools.json`, `quality_tiers.json`
- Paint: `BRUSHES` (7), `SHAPES` (8), `PAINT_COLORS` (12), sizes, `PAINT_SPOT`, `STUDIO_BOX`, `PAINT_C` · `paint.js:5-19` → small `UPrimaryDataAsset` (`UPaintStudioConfig`) rather than tables; `FBrushRow { FName Id; FText Name; }` if tabled.
- Physics: `BALL_DEFS` (4 balls: r, mass, bounce, cd[], cl, roll, start, skin, colours), `TOWER` (rows PLAY/LAB/XR/★), `BLOCK_COLS`, `GOAL` (5×2 m), `SWING`, `SPIN` · `phys.js:12-21, 335, 366` → `FBallRow { FName Id; FText Name; float Radius; float Mass; float Restitution; TArray<float> DragCoeffs; float SpinLift; float RollingResistance; FVector2D Start; FName Skin; TArray<FLinearColor> Colors; }` (map to Chaos physical materials).
- `PLAYBOOK_CATS` (12) · `art.js:258` → text for the XR Playbooks cover.
- `SCREENS` (3 monitors: file, handbook page, syntax-coloured code lines) + `TOOLS` (9 toolkit boxes: name, colour) · `worldroom.js:197-202` → `FCodeScreenRow`, `FToolBoxRow`.
- `QUALITY` (3) · `gfx.js:5-9` → web-only; translate to `Scalability.ini`/`DefaultEngine.ini` groups, not a table.

### 1.22 `ui_strings.json` — HTML chrome copy
`parts/body.html` · **83** text nodes `{ tag, id|null, line, text }` (intro, About panel, button labels, room tag defaults, reader/station/guide/badge panel headings, no-WebGL fallback). → `UStringTable` (CSV `Key,SourceString`) keyed by element id / slug; page title "XRLibraries Campus · Concept by Ev Holt" set in `assemble.py:40`.

### 1.23 `books_legacy_pine_hollow.json` — orphan
`parts/books.js` (not assembled) · 8 subjects, 14 books. Ignore for the port unless the Pine Hollow edition is wanted.

---

## 2. Content generated at runtime (must be code or pre-rendered in UE)

| Generator | Where | Output | UE plan |
|---|---|---|---|
| `buildKB()` / `searchKB()` / `bestSentence()` / `searchAnswer()` | engine.js:16-66, 281-307 | TF-IDF sentence index over items+facts+pages+parts+lessons; staff-specific kind bias; "when/num/who" boosts | Rebuild in C++ over the DataTables (or feed the same rows to an on-device retriever) |
| `presetAnswer()` templated branches (26) | engine.js:192-265 | counts, year lookups, ride stats, token/badge progress text, `recommend()` | Code; strings kept in `staff_answers.json.presetBranches[].replySrc` |
| `staffRules()` | ui.js:322-355 | LLM system prompt assembled from FACTS/exhibits/books/places + ride numbers | Regenerate from tables at runtime |
| `directions()` | engine.js:266-280 | route sentence per place (exported) | Table (`directions`) |
| `WAX_ITEMS` assembly, `waxView()` | waxhall.js:438-449 | cards + stand points for scenes | Table + computed from bay layout |
| `STOPS` expansion, `lobbyView()` | ui.js:128-139, world.js:137 | tour order; viewport-fit lobby view | Table (exported expanded) |
| `SHELF_VIEWS`, `bpViewFor()`, station `view()` | world.js:438, blueprints.js:39, lab.js | live camera targets | Resolve `viewRef` at runtime |
| Exhibit art `ART[type]` (14 painters), `drawPlaybookCover`, `drawBookCover`, `drawStaffLabel`, `drawLecternSign`, `drawTableCard` | art.js, art2.js, world.js | canvas textures | Pre-render (pipeline already emits `art/<id>.png`) or recreate in Substance/Photoshop |
| Blueprint drawings `BP_GEO` | bpdraw.js:63-412 | 5 vector drawings (1280×800) | Pre-render to 4K textures |
| Wax backdrops/floors (12 + 12) | waxpaint.js | painted scene backgrounds | Replace with real environment art per scene |
| Badge icons (15) | progress.js:120-142 | 88 px canvas icons | Author SVG/PNG |
| Room 104 `dioSketch`, `drawPipeline`, `drawCodeScreen`, `drawToolLabel` | worldroom.js:18-30, 183-222 | sketch, banner, monitors, box labels | Pre-render |
| Lab simulations `psdNew()`, `titrNew()`, pendulum fit, bench results | lab.js, blueprints.js:427-436 | randomised samples and result sentences | Code (UE Blueprint/C++), reuse `sieves.json` |
| Token ride anchors `tokenPos()` | progress.js:45-50 | 3 token positions | Attach to ride actors |
| Rocketbox figure dressing (`makeHuman`, `dye`, outfit colours) | humans.js, waxfig.js | tinted materials per figure | Material instances driven by the colour fields |

## 3. Sanity numbers
sources 22 · galleries 4 · kinds 9 · exhibits 16 (15 + Freedom) · facts 15 · subjects 8 · books 15 (82 pages) · blueprints 5 (60 parts) · wax scenes 12 (38 figures) · staff 4 · intents 43 · preset branches 45 · directions 42 · lessons 11 · places 42 · tour 35 · badges 15 · tokens 11 · rides 3 · dive facts 9 · stations 5 · world layers 9 · bench kits 2 (15 steps) · sieves 12 · rooms 15 · doors 14 · map rooms 17 · ui strings 83 · legacy books 14.
