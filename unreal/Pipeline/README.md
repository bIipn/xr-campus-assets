# Pipeline: from the web campus to Unreal

Everything Unreal imports is produced here from the existing web build, so the Unreal campus matches the web one
exactly in layout, sizes and content. The outputs are committed; you only re-run these scripts after changing the
web build (`parts/*.js`) or the Reading Room scene (`bl/library.py`).

```
parts/*.js ──► content/extract_content.mjs ──► content/*.json ──┐
                                                                 ├─► data/build_data.py ──► ../WalkTheArchive/Data/*.json (DataTables)
             layout/layout.json (campus layout, Unreal coords) ──┘
test/harness.py + web/export_campus.py ──► out/campus/*.glb, art/*.png, lights.json
bl/library.py --ue ──► assets/lib_ue/library.blend ──► blender/export_reading_room.py ──► out/reading_room/ReadingRoom.glb, lights.json
bl/museum.py ──► out/museum/Museum.glb, lights.json      (the neoclassical museum: galleries, lobby, halls, rotunda, portico)
bl/exterior.py ──► out/exterior/Outside.glb, lights.json, theatre_layout.json  (the grounds: terrain, the Forecourt Theatre, path,
                   fountain, trees, the other shells including the talks wing's)
bl/auditorium.py ──► out/auditorium/Auditorium.glb, lights.json, layout.json  (the talks wing: the foyer and the auditorium)
bl/classroom.py ──► out/classroom/Classroom.glb, lights.json, layout.json     (Room 104 as the XR Classroom: smartboard, desks, signs)
bl/training.py ──► out/training/Training.glb, lights.json, layout.json        (the Training Wing: the dialysis course's five stations)
bl/screens.py ──► assets/tex/screen_tablet.png, screen_phone.png   (the XR Libraries app mock the lit screens show)
bl/props.py ──► out/props/HandProps.glb                    (the Wax Hall's held props: headset, tablet, phone, book, clipboard, box)
bl/seats.py ──► out/props/Seats.glb                        (the Wax Hall settees, the yard's park benches)
out/campus/*.glb + ReadingRoom.glb + Museum.glb + Outside.glb + HandProps.glb + Seats.glb + Auditorium.glb + Classroom.glb + Training.glb
    ──► blender/prepare_for_unreal.py (+ content/refits.json) ──► out/ue/<Asset>.glb   (what Unreal imports)
```

The Wax Hall's carried props leave the web export as a wing of their own: `web/export_campus.py` writes every
`S.carry` object as `prop__<scene>_<k>` of `out/campus/props.glb`, in its own frame, and where it rested at t = 0 to
`out/campus/props_rest.json` (committed); `data/build_data.py` turns the carries the acting data never moves into
`static` props standing where the web left them. The props the reenactors hold are modelled again by `bl/props.py`
(`out/ue/HandProps.glb`, one tagged mesh `prop__<kind>` each, in the frame the stage sets in a palm: +X along the
fingers, +Y out of the palm); `World/WTAWaxStageActor.cpp` rides them on the hand bones and closes the fingers on
them the way `unreal/Tools/holds/design_holds.py` worked out from the body's finger joints (`Tools/holds/probe_palm.py`
-> `palm.json`) and these meshes: the fingers flat under the prop, the thumb pressed on its top, the headset hanging
by its top strap. Rerun the designer after changing a prop model and paste its table into the stage actor. Neither
wing is scenery: `build_level.py` skips `prop__` meshes and the stages spawn them. In the engine the hold is then
made real: each prop's box (or the strap's tube) is handed to the anim layer, which curls the fingers from the
designed pose until they touch it (so every body size closes right), the arm is IK'd to where a person holds that
thing to use it (a stance from the shoulders, the prop turned to face the eyes), the head looks at it, the box is
carried with a hand flat on each side, and the headset swings on its strap as a damped pendulum.

Seats: a sitting place is a mesh named `seat__<id>_f<yaw>` (a chair's cushion, half a bench's slab, a settee's
seat; `<yaw>` the Unreal yaw a sitter faces, `atan2(dz, dx)` in campus axes) - `bl/library.py` tags its reading
chairs, `bl/museum.py` its gallery benches, `bl/seats.py` the Wax Hall settees and six park benches round the yard's plaza (the school hall is lockers wall to wall, so none there) - and `wta_setup/actors.py`
puts an `AWTASeatActor` at the top of each such mesh, so there is no seat table to keep.

The talk venues: three places where a speaker gives a talk with slides, built so the talks-and-classes system can
find what it needs by name. Each has `screen__<venue>` slide screens (one 16:9 quad each, UV (0,0) at the bottom-left
as the audience sees it, its own material the engine replaces), a `spot__<venue>_f<yaw>` floor mark where the speaker
stands (a 0.3 m quad 1 cm above the floor; the yaw is the Unreal yaw the speaker faces; never shown), and seats named
`seat__<venue>_<id>_f<yaw>` so the venue knows its audience; `out/<builder>/layout.json` (the theatre's is
`out/exterior/theatre_layout.json`) gives the rooms, entries, the spot, the screens' centres and sizes, a camera and
the seat count, and `lights.json` the fixtures by the names the lighting step knows (`downlight`, `stage`, `step`,
`foyer`, `sconce`, `panel` (AREA), `screen`, `theatre`, `post`; the lectern's reading lamp is only a glowing shade;
the `stage` fixtures become aimed SpotLights, the rest bulbs). A room sunk below grade needs a hole in the grounds:
`GROUND_HOLES` in `bl/exterior.py` cuts the auditorium's footprint out of the terrain grid (the grass still runs
under its walls), or the lawn shows through its floor.
- **The Forecourt Theatre** (`forecourt`, `bl/exterior.py`): the fountain plaza became an open-air theatre at the foot
  of the museum's steps. A stepped stone stage (a half disc about (0, 20.4) with a straight back, top at -0.35) with a
  lectern; the speaker faces the grounds with the portico behind. Two slide screens (`screen__forecourt_l`, `_r`, 4 x
  2.25 m) in small pedimented stone frames either side, turned 22 degrees toward the seats, so the portico's middle
  stays in view. The cavea: six limestone tiers (1.0 m deep, 0.38 m high) in arcs about the stage from r 6.6 to 12.6,
  55 degrees either side of the axis; each tier's front edge is a row of seats capped with teak boards (74 tagged
  pieces), the sitter's feet on the tier below; the path runs through the middle at ground level (a 3.2 m passage),
  an aisle with half-tier steps climbs each half at 30 degrees; a marble balustrade with pedestals and urns runs along
  the back, over an ashlar wall in the campus's order (plinth, pilasters, cornice) that faces the grounds.
  The fountain moved out to z 50 with its round plaza; the allee's first trees and the path's first lamps gave way.
- **The talks wing** (`auditorium`, `bl/auditorium.py`; Hall R's door is `bl/museum.py`'s, the outer shells
  `bl/exterior.py`'s): Hall R's north wall has a 2.2 x 2.8 m door into a marble foyer (x 6.7..11.35, z -13.65..-4.95),
  and through a lettered portal the back of the auditorium (x 6.75..20.75, z -31.0..-14.1): a level cross-aisle at y 0,
  seven curved rows of upholstered chairs (112, each cushion tagged) stepping 0.2 m down to an orchestra at -1.6, a
  raised stage at -0.8 with a curved front and steps up at both ends, a lectern at stage left (the speaker at
  (18.6, -28.9)), an 8 x 4.5 m screen (`screen__auditorium`) in a black masking frame, velvet legs and a valance,
  walnut slats and plaster, acoustic clouds with downlights, a lighting truss, sconces, a booth window and an exit
  sign. The wing leans on the galleries' east face and the School's north face, so only its north and east faces and
  its top show outside; trees that stood in its footprint were dropped.
- **The XR Classroom** (`classroom`, Room 104 of the School): `content/refits.json` (applied by
  `prepare_for_unreal.py`) drops the computers desk with its stools, the "Built in a browser" panel and the old signs,
  and moves the layer table to the back, the beanbags to the back-left corner and the World Builder book onto the
  teacher's desk; `bl/classroom.py` adds a 3 m smartboard (`screen__classroom`) on the east wall, the teacher's desk
  and chair by the window, 3 rows of 3 two-seat desks with 18 chairs facing the board, the teacher's spot at the front
  left, and the door sign and blade sign reading "104 · XR Classroom".

The Training Wing (`training`, `bl/training.py`; its shell, the holes for its door and windows and the canopy are
`bl/exterior.py`'s SHELLS `'training'`, OPENINGS, WINDOWS and SHELL_CUTS; the door from the auditorium is
`bl/auditorium.py`'s EAST_DOOR): the dialysis technician course's room (XR Libraries' Project SANDI), a new wing east of
the auditorium and north of the School, x 21.2..32.0, z -27.0..-13.6, floor 0, ceiling 3.6, entered through a 1.2 x
2.2 m door in the auditorium's east wall at the cross-aisle (z -16.2..-15.0, a walnut surround on the hall side) and
from the yard through a 1.8 x 2.4 m double doorway at the north end of its east wall (z -26.7..-24.9, its leaves
standing open, a canopy and a lantern outside). The east wall stands on the yard fence's line, so the wing stops at
x 32.45, half a metre short of the coaster, and `content/refits.json` clips the fence out of the Yard asset where the
doorway opens through it (a `clip` refit: faces inside a campus box go). A clean clinical room: pale warm-grey walls
with a white dado rail, a grey resilient floor, an acoustic-tile ceiling on a T-grid with eight 2 x 4 panel lights
(`panel`, AREA) and LED strips over the course board and the water panel (`screen`), two windows on the east wall and
two on the north (frames, glass, reveals, rolled blinds), a clock, the wing's sign over the yard door. Five stations
round the room, each with a free standing spot in front and a numbered plate on the wall above: `dx-hygiene` (the
sink unit on the south wall by the west door), `dx-machine` (the dialysis machine beside the treatment chair: screen,
blood-pump module, the dialyzer in its side holder with the blood lines to the patient's arm, the IV pole),
`dx-chair` (the reclining treatment chair, the BP monitor on its rolling stand, the floor scale), `dx-water` (the two
carbon tanks, the RO unit, the wall cabinet with the conductivity meter and the chlorine test kit on its shelf, the log
on its hook) and `dx-charting` (the desk with the treatment record on its monitor, the task chair, the filing cabinet,
the corkboard). The course desk is a standing desk mid-way along the west wall facing east, with the checklist board
("DIALYSIS TECHNICIAN · FOUNDATIONS") on the wall behind it and `spot__training_f0` behind it where the course lead
stands; the seats are four chairs along the south wall (`seat__training_c1_f270` .. `c4`, facing north) and the task
chair (`seat__training_desk_f90`). `out/training/layout.json` gives the room, the doors and windows, each station's
anchor (`ue_location_cm`) and view (web and Unreal conventions), the course desk with its spot and board, a place
view and the seats; `lights.json` the fixtures. Materials are `trn_*` (`content/surfaces.json` has the Training block).

Surfaces: `content/surfaces.json` names the CC0 texture sets (ambientCG) and which builder material in which asset
takes which set; `wta_setup/surfaces.py` imports them from the textures folder on the machine and swaps the
campus meshes' materials for world-aligned instances. The textures stay out of the repo and the GLBs.

The Museum and Outside assets are no longer the web export: `bl/museum.py` rebuilds the museum in Blender (marble floors,
Corinthian columns, coffered vaults with glazed laylights, a domed rotunda and a six-column portico with steps down to
the grounds) around the web's own exhibits, signs and panels, which `blender/extract_museum_pieces.py` saved once into
`out/museum/web_pieces.glb` and `out/exterior/web_pieces.glb` (the school facade pieces). `bl/exterior.py` builds the
grounds and the other buildings' stone shells. Both share the plan constants in `bl/museum.py`, and `bl/neo.py` holds
the architectural vocabulary (columns, capitals, entablatures, vaults, domes, urns, trees). The textures come from
`bl/textures.py` (`limestone museum_marbles grass flagstone trees banners frieze`) and are committed under `assets/tex`.
`blender/cull_indoor_trees.py` only applies to the old web export.

`blender/find_flicker.py -- Museum ReadingRoom Outside` is the gate against walls that flicker: it loads the prepared
GLBs and lists every pair of faces from different meshes that lie in one plane (within 1.5 mm), face the same way and
overlap (true polygon overlap, not bounds), biggest first, with where the largest piece is in campus metres. Faces
glued back to back onto a surface and the undersides of things standing on the floor are left out. What it still
lists after a build is read with judgment: a pair buried inside a wall or on a roof top cannot be seen; one on a
jamb, a sill, a reveal or a ceiling can, and the builders are changed until it is gone.

## Coordinates

Web campus: metres, three.js axes (Y up, camera yaw 0 looks toward −Z). Unreal: centimetres, X east, Y south, Z up.

| | Formula |
|---|---|
| Position | `UE = (100·x, 100·z, 100·y)` |
| Yaw (web radians → UE degrees) | `UE_yaw = (−90 − deg(yaw)) mod 360` |
| Pitch | `UE_pitch = deg(pitch)` |
| Sun | `SUN_DIR = [40, 62, 30]` → Directional Light pitch −51.1°, yaw −143.1° |

The glTF files stay in three.js axes; Unreal's glTF importer applies the same mapping (glTF `(x, y, z)` m → UE `(X=x, Y=z, Z=y)` cm).
Every mesh in `out/ue/` has its world transform baked in: spawn at (0, 0, 0), rotation 0, scale 1.
Landmarks to check after the first import: library door on X = −1200, Y −460…−140; arched window on X = −3200;
token `t-museum` at about (−535, −4135, 36).

## Re-running (Linux or Mac with Node 22, Python 3, and Blender 5.2 or `pip install bpy==5.2.2`)

```sh
node unreal/Pipeline/content/extract_content.mjs                 # web content -> content/*.json
python3 unreal/Pipeline/data/build_data.py                       # -> WalkTheArchive/Data/*.json, validated against contract/structs.json
pip install playwright==1.56.0                                   # once; plus the web test deps (see test/harness.py)
python3 unreal/Pipeline/web/export_campus.py                     # boots the web campus headless, exports every wing
python bl/library.py --ue                                        # Reading Room for Unreal (real books, thick walls)
python unreal/Pipeline/blender/export_reading_room.py
python bl/museum.py [--render]                                   # the museum -> out/museum/Museum.glb (+ preview renders)
python bl/exterior.py [--render]                                 # the grounds -> out/exterior/Outside.glb
python unreal/Pipeline/blender/prepare_for_unreal.py [-- Museum Outside]   # -> out/ue/*.glb
```

The web test harness needs `three@0.170.0` and the `@fontsource` packages in `test/node_modules`, plus
`three@0.170.0` and `@dimforge/rapier3d-compat@0.14.0` in `test/nm2/node_modules`.

## Talks and classes

`content/talks.json` (or a client pack's own `talks.json`) holds every talk and class: its venue, its speaker, the slides
with what the speaker says on each, and for a class the quiz, the pass mark and the certificate. From it:
`bl/slides.py` draws the slides (`out/slides/<talk>/<nn>.png`, 2048 x 1024, in the campus's own look: the title slide,
content slides with the exhibit art or a line drawing beside the points, a closing slide), the `import_art` setup step
imports them as `/Game/WTA/Slides/T_Slide_<talk>_<nn>`; `unreal/Tools/voice/make_talk_voices.py` reads every line and
quiz question aloud in the speaker's Kokoro voice (`out/voice/VO_talk_<talk>_<nn>.wav`, `VO_quiz_<talk>_<nn>.wav`, copied
to the Unreal machine's voiceover folder and imported by `wta_voice`); `data/build_data.py` writes `DT_Talks`. In the
engine `AWTATalkActor` (placed by the `actors` step on the venue's `spot__<venue>_f<yaw>` mesh) puts the slides on the
venue's `screen__<venue>` meshes, stands the speaker on the spot (a reenactor, or the staff member who teaches), and
runs the talk while a visitor sits on one of the venue's seats (`seat__<venue>_*`): the line read aloud with its
sentences as captions, the speaker gesturing and looking at the listener; a class ends in its quiz and a certificate.
`build_client.py` runs the slides and (when the Kokoro model is on the machine) the voices with everything else.

A row of kind `course` is a class taught by doing rather than listening: no slides, but `stations` (ids from
`content/stations.json`, step-by-step cards in its room) and an `intro` the course lead says. The engine puts an
`AWTACourseActor` on its venue's spot instead of a talk actor: the lead (the row's `person`) idles at the desk, E opens
the course card with the welcome (`VO_talk_<id>_01`, the one talk clip a course has), the stations as a checklist with
a Go button each, and once every station is finished the quiz, the certificate and the badge, as for a class. The
first course is Dialysis Technician: Foundations in the Training Wing (`dx-*` stations, `certified-dialysis`).

## A client pack, and the sheet a library fills in

`clients/<name>/campus.json` holds what is the client's rather than the campus's (the names, the app on the lit
screens, the frieze lines, the open book, where its content lives) and, beside it, its own `talks.json` and,
optionally, `catalogue.json`: the library's catalogue name, its search page with `{q}` where the words go (every
library book's cover then carries "Find it in <name>", the title searched), and `records`, a source id from
`content/sources.json` mapped to the library's own catalogue record, which the card links instead of the web page.
XR Libraries' pack points at WorldCat, which every library can search. `data/build_data.py` reads the pack from
`WTA_CLIENT` (what `build_client.py` sets), else XR Libraries' own, so a plain run writes the same tables.
`clients/start.html` is the sheet a library fills in to get one: the words on the building, the talks and classes
with their slides, quizzes and certificates, a contact. It validates as they type and downloads `<folder>-pack.zip`
(`campus.json`, `talks.json`, a README), which goes into `clients/<folder>/`; then
`python3 build_client.py --client clients/<folder>` rebuilds everything from it. The page is self-contained (one
file; JSZip from cdnjs), opens from disk or any web host, and is also published as a Claude artifact with its
download capability. `clients/make_start.py` rebuilds it from `clients/start.template.html` with the XR Libraries
pack inlined as the example it opens on.

## What is in `out/ue/`

| Asset | Meshes | Triangles | Notes |
|---|---|---|---|
| Museum | 64 | 177k | Blender: rotunda, lobby, 3 vaulted galleries, halls, portico and steps; `item__<id>` = the web's exhibits |
| WaxIntro | 4 | <1k | Intro wall at the Wax Hall door |
| WaxHall | 167 | 54k | 12 stages (figures come later as MetaHumans) |
| LibraryShell | 31 | 1k | Interactive bits of the Reading Room: book covers (`book__<id>`), signs, Freedom board |
| ReadingRoom | 16 | 187k | The Blender-modelled room: real books on every shelf, thick walls, PBR textures |
| School | 311 | 43k | Hall + rooms 101–104; `bp__<id>` = blueprint boards |
| Outside | 26 | 140k | Blender: terrain with the forecourt meadow, flagstone path, fountain, trees, lamp posts, the other buildings' shells, horizon |
| Yard | 104 | 73k | Coaster, Sky Drop, dive dome, playground; `ride__` / `token__` tags; the fence clipped at the Training Wing's doorway |
| Training | 37 | 8k | Blender: the Training Wing's room and its five stations; `spot__training_f0`, `seat__training_*` |
| OceanDive | 76 | 134k | The reef 420 m east of the campus |

Left out on purpose: the sky dome, wind grass, particles, people (MetaHumans replace them), web-only invisible helpers,
and the web build's baked lighting.
