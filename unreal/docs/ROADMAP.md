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
| **M8** | **VR** (moved to the end of M10 by Ev's call) | OpenXR mode: PC VR headsets (Quest Link/Air Link, SteamVR) with world-space UI and snap turn | 1 week |
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
| 5 | **Training wing**: step-by-step stations with a checklist, a quiz and a certificate (the dialysis course first) | workforce programs | the classes system, stations, badges, story cards | medium | **now** (the course runs in the engine: five stations, the checklist card at the lead's desk, the quiz, the certificate and two badges; the wing's room, desk and props are being built) |
| 6 | **Client content packs**: a library fills in a sheet and gets its own campus | every library system, tribe, school district | the data tables and builders, `build_client.py`, the sheet `clients/start.html` | medium | now (the pack and the sheet are in; the build runs on our side) |
| 7 | **Seasonal exhibits swapped without a rebuild** | every client | the JSON tables load at start | low | next |
| 8 | **Spanish and any language from the pack**: every string and voice line per language | Nevada and California libraries | the data tables, the voice pipeline | medium | next |
| 9 | **Catalogue links**: a card's source opens the library's own catalogue record | every client | exhibit sources | low | next |
| 10 | **Photo mode**: a framed postcard of where you stand, saved to share | visitors | the screenshot system | low | **in**: P frames the view as a matted postcard with the place and the date and writes it to `Saved/Postcards/` |
| 11 | **Kids' hunt with a library card**: tokens stamp a card, a prize at the desk | children's programs | tokens and badges | low | next |
| 12 | **Visit heatmaps and dwell times** exported for grant reports | the library's own reporting | the places list, the walk tour | low | next |
| 13 | **Lost Stories booth**: record an oral history at a mic; it is transcribed and becomes an exhibit a reenactor reads | tribes, local history, the Miwok archive | voice pipeline, exhibits, wax figures | medium | then |
| 14 | **Pop-up book room**: library books open as 3D scenes on the reading table | kids' programs | the book reader | medium | then |
| 15 | **Maker room**: visitors put their own photo and caption on a plinth; the XRMARIN content-creation course is the lesson | the creator academy | exhibits, uploads, the classes system | medium | then |
| 16 | **Docent-led visits**: one librarian leads a group of headsets through the tour | library programs, classes | the tour | high (networking) | then |
| 17 | **VR mode**: PC-VR through OpenXR first, then a Quest build | every headset they already own | the plugin is enabled, the walk and look are built | high | **last** (M8 moves here) |

## Order of work inside M1 (what the setup script does)

`probe → import_meshes → import_art → data_tables → build_level → lighting → actors → navmesh → project_settings → verify`

Every step is safe to re-run and prints one `WTA_RESULT {…}` line, so Claude can check the result without reading the whole log.

## Known gaps after M1 (by design)

- People are placeholders (a cylinder with a name) until M3.
- Stations, rides and the paint studio open their info panels but are not interactive yet (M5/M6).
- The greybox geometry and canvas-drawn textures come straight from the web build. They are accurate in size and layout but not yet photoreal; M2 replaces them.
- Blueprint-lab places (`bp-car` …) have no stand-to view in the data yet; the setup fills them from the blueprint board meshes when it can.
