# Roadmap

Each milestone ends with something you can walk around in and check. Sizes are rough: one person plus Claude, art not included.
The interactive systems are specified in detail in `docs/reference/systems.md` (web behaviour with file:line, and the Unreal class for each).

| # | Milestone | Done when | Size |
|---|---|---|---|
| **M0** | **Machine ready** | Preflight passes; Unreal 5.8, Visual Studio or Xcode, Git and Blender are installed; the editor target builds | ½ day |
| **M1** | **Playable campus in Unreal** (this package) | `setup_project` reports all steps ok. You can walk the whole campus with mouse and keys, lit by Lumen with sky, sun and exposure. Exhibits open catalog cards with their art, the books read, the 35-stop tour runs, staff answer questions, tokens and badges save, room names show, Wax Hall captions play | 1–2 days |
| **M2** | **Photoreal look-dev** | Every room gets real materials (Megascans/Fab or Poly Haven scans), hero props, tuned lights and exposure. Exterior gets a Landscape, Megascans trees and grass, and a sky that matches the sun. Benchmarks: 1440p 60 fps on an RTX 4070-class GPU with the Epic preset. See `LOOKDEV.md` | 1–2 weeks |
| **M3** | **MetaHuman staff** | Margaret, Rosa, Mr. Hale and Coach Rae are MetaHumans with idle animation, head and eye tracking, and talking animation on answers. See `HUMANS.md` | 3–5 days |
| **M4** | **Wax Hall** | The 12 scenes play as Level Sequences with MetaHuman reenactors in period outfits, triggered as you approach; captions in sync; Historian badge | 2–3 weeks |
| **M5** | **Workshop School** | Sieve analysis, titration, pendulum, model bench and diorama work hands-on (station panel + animated equipment). The 3D Art Studio paints in the air | 2–3 weeks |
| **M6** | **Recess Yard** | Comet Coaster (spline ride, G-forces), Sky Drop, Chaos physics props, swings, merry-go-round, soccer with keeper | 2–3 weeks |
| **M7** | **Ocean Dive** | Underwater ride with fog, caustics, fish schools and facts | 1–2 weeks |
| **M8** | **VR** (moved to the end of M10 by Ev's call; **in**, idea 17) | OpenXR mode: PC VR headsets (Quest Link/Air Link, SteamVR) with world-space UI and snap turn | 1 week |
| **M9** | **Ship it** | Signed Windows build on itch.io, a "UE5 edition" page on the Vercel site, optional live stream (Pixel Streaming 2). See `DELIVERY.md` | 3–5 days |

## M10 · XR Libraries platform: one campus, any client (Ev, Oct 22)

Ev's call: all fifteen ideas go in, the PC-VR mode comes last. The first three are being built now: the talks
auditorium as a new wing of the building, the forecourt turned into an open-air talk space with seats, and the
school classroom turned into a class you attend, with a quiz and a certificate at the end. All three run on one
talks-and-classes system (`content/talks.json`): slides, a speaker reenactor, the voice reading the script with
captions, sitting down starts it, and a class adds the quiz and the certificate. A course (kind `course` in the same
file) is a class taught by doing: stations to finish, then the quiz at the course lead's desk.

| # | Idea | Who it's for | Builds on | Size | Order |
|---|---|---|---|---|---|
| 1 | **Talks auditorium**: a speaker reenactor reads a script, slides on the wall; a new wing of the building | every client | wax figures, voice, seats | medium | **now** |
| 2 | **Outside talk space**: the forecourt becomes an open-air theatre with stone benches, a stage and a slide screen | every client | the same talks system | medium | **now** |
| 3 | **Classes you attend**: a teacher, a board, the Intro to VR class, a quiz at the end and a certificate | schools, libraries | stations, badges, voice | medium | **now** |
| 4 | **Sit, read, listen**: seats everywhere, cards read aloud, captions | accessibility, long visits | sitting, voice, captions | low | now (seats are in; the new rooms add more) |
| 5 | **Training wing**: step-by-step stations with a checklist, a quiz and a certificate (the dialysis course first) | workforce programs | the classes system, stations, badges, story cards | medium | **in**: the wing is built and seen in the engine (a clinical room east of the auditorium with windows onto the yard, the five stations round it, Nia at the course desk under the checklist board); the course runs end to end: stations, checklist card, quiz, certificate, two badges |
| 6 | **Client content packs**: a library fills in a sheet and gets its own campus | every library system, tribe, school district | the data tables and builders, `build_client.py`, the sheet `clients/start.html` | medium | now (the pack and the sheet are in; the build runs on our side) |
| 7 | **Seasonal exhibits swapped without a rebuild** | every client | the JSON tables load at start | low | built: `Saved/Season/DT_<Name>.json` rows laid over the tables at start, `Season/art/<row>.png` on the card and over the frame; QA phase `season` |
| 8 | **Spanish and any language from the pack**: every string and voice line per language | Nevada and California libraries | the data tables, the voice pipeline | medium | built: `Pipeline/content/lang/<lang>/` (`strings.json` for the engine's words → DT_Strings; `tables.json` for the content, merged over the English rows; `builders.json` for the slides), the staff read both languages (patterns `english|spanish`, accents folded, place aliases added); Spanish is in (`lang/es`, 193 engine strings, 2,582 content strings, Kokoro's ef_dora/em_alex voices); a pack sets `"language": "es"` |
| 9 | **Catalogue links**: a card's source opens the library's own catalogue record | every client | exhibit sources | low | **in**: `clients/<pack>/catalogue.json` gives the catalogue's search page and its records; every library book's cover gets "Find it in <catalogue>" and a source with a record links there instead of the web |
| 10 | **Photo mode**: a framed postcard of where you stand, saved to share | visitors | the screenshot system | low | **in**: P frames the view as a matted postcard with the place and the date and writes it to `Saved/Postcards/` |
| 11 | **Kids' hunt with a library card**: tokens stamp a card, a prize at the desk | children's programs | tokens and badges | low | **in**: the library card (Badges → My library card, or ask Margaret) shows a stamp per token, the hints still open, and with a full card "show it at the desk" plus a saved picture of it |
| 12 | **Visit heatmaps and dwell times** exported for grant reports | the library's own reporting | the places list, the walk tour | low | **in**: every play session writes `Saved/Visits/visit_<time>.csv` (rooms and seconds, cards opened, tokens, badges, a position every 2 s, no names); `unreal/Tools/common/visit_report.py` turns a folder of them into one page with the dwell times, the most opened cards and a heatmap over the campus plan |
| 13 | **Lost Stories booth**: record an oral history at a mic; it is transcribed and becomes an exhibit a reenactor reads | tribes, local history, the Miwok archive | voice pipeline, exhibits, wax figures | medium | **in**: a timber cabin where the path ends (`bl/stories.py`); E at the microphone sits you in the teller's chair and opens the booth: record (the default microphone, up to 5 minutes, a level meter), listen back, keep with a title and a first name, or delete; a kept story is its WAV and JSON in `Saved/Stories/New` (a librarian moves it to `Wall`; off with `bStoriesNeedReview`), whisper.cpp writes it down in the background in its own language, and the story board shows it as a paper card in the teller's own voice with the words as captions. The teller's voice is the record, so no reenactor reads it; promoting a story to an exhibit is a librarian's step for later |
| 14 | **Pop-up book room**: library books open as 3D scenes on the reading table | kids' programs | the book reader | medium | **in**: four library books as theatre pop-ups on the Reading Room's south reading table (`bl/popup.py`, nine spreads: the water cycle, the reef and coral bleaching, VR and AR, pollinators at the fair), every piece extruded paper; E sits you in the chair facing it, then opens the book, turns the page (the spread folds down and the next one pops up, back layer first, under its own light) and closes it, when the next book's cover lies there; each spread is captioned with its page's heading and first sentence, counts as a page read and is in the visit log |
| 15 | **Maker room**: visitors put their own photo and caption on a plinth; the XRMARIN content-creation course is the lesson | the creator academy | exhibits, uploads, the classes system | medium | **in**: the visitors' wall in the 3D Art Studio hangs the postcards they take (P) and any picture dropped into `Saved/Maker`; the content-creation course is Making a 360 Story (`bl/maker.py`): five stations round the studio, the course lead at the teacher desk, a quiz, a certificate and two badges |
| 16 | **Docent-led visits**: one librarian leads a group of headsets through the tour | library programs, classes | the tour | high (networking) | **in** (on desktops and in the VR mode, where the names float in the world): V, or *Visit together* in the menu, opens the visit card; *Lead a visit* makes the guide's campus the host (UDP 7777, announced on the local network on 47790) and visitors pick it from *Visits on this network* or type its address. Everyone sees everyone as a figure in their own colour (a robe, a headset's visor) with their name over it, the guide's brass with a GUIDE tag; every stop the guide shows walks each visitor to their own place round it, G gathers the group round the guide, and cards, books and rides stay each person's own. `docs/GUIDED_VISITS.md`; `Tools/win/visit_qa.ps1` plays a visit with two games on one computer (24 checks) |
| 17 | **VR mode**: PC-VR through OpenXR first, then a Quest build | every headset they already own | the plugin is enabled, the walk and look are built | high | **in** (PC-VR; checked in the desktop simulation, a real headset not yet: this PC has no OpenXR runtime): *Enter VR* in the menu (or `-headset`) starts the headset through OpenXR with the game's own controller bindings. The left stick walks, the right stick turns 30 degrees, and a wand in the right hand casts a laser that names what it is on and opens it, presses the buttons on a card, or steps to the floor it points at; A is the tour's next stop, B goes back. Cards float square in front of you at reading distance and the HUD a little lower further off, turning after you; both come nearer when a wall is close. In a guided visit the other people's names float over them. `docs/VR_MODE.md`; `WTAPlayTest vr` plays it in the `-vrsim` simulation (14 checks). A standalone Quest build is still to come |

## Order of work inside M1 (what the setup script does)

`probe → import_meshes → import_art → data_tables → build_level → lighting → actors → navmesh → project_settings → verify`

Every step is safe to re-run and prints one `WTA_RESULT {…}` line, so Claude can check the result without reading the whole log.

## Known gaps after M1 (by design)

- People are placeholders (a cylinder with a name) until M3.
- Stations, rides and the paint studio open their info panels but are not interactive yet (M5/M6).
- The greybox geometry and canvas-drawn textures come straight from the web build. They are accurate in size and layout but not yet photoreal; M2 replaces them.
- Blueprint-lab places (`bp-car` …) have no stand-to view in the data yet; the setup fills them from the blueprint board meshes when it can.
