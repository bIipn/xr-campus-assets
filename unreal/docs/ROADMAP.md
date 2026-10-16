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
| **M8** | **VR** | OpenXR mode: PC VR headsets (Quest Link/Air Link, SteamVR) with world-space UI and snap turn | 1 week |
| **M9** | **Ship it** | Signed Windows build on itch.io, a "UE5 edition" page on the Vercel site, optional live stream (Pixel Streaming 2). See `DELIVERY.md` | 3–5 days |

## Order of work inside M1 (what the setup script does)

`probe → import_meshes → import_art → data_tables → build_level → lighting → actors → navmesh → project_settings → verify`

Every step is safe to re-run and prints one `WTA_RESULT {…}` line, so Claude can check the result without reading the whole log.

## Known gaps after M1 (by design)

- People are placeholders (a cylinder with a name) until M3.
- Stations, rides and the paint studio open their info panels but are not interactive yet (M5/M6).
- The greybox geometry and canvas-drawn textures come straight from the web build. They are accurate in size and layout but not yet photoreal; M2 replaces them.
- Blueprint-lab places (`bp-car` …) have no stand-to view in the data yet; the setup fills them from the blueprint board meshes when it can.
