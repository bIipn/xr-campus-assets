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
bl/exterior.py ──► out/exterior/Outside.glb, lights.json  (the grounds: terrain, path, fountain, trees, the other shells)
bl/props.py ──► out/props/HandProps.glb                    (the Wax Hall's held props: headset, tablet, phone, book, clipboard, box)
out/campus/*.glb + ReadingRoom.glb + Museum.glb + Outside.glb + HandProps.glb ──► blender/prepare_for_unreal.py ──► out/ue/<Asset>.glb   (what Unreal imports)
```

The Wax Hall's carried props leave the web export as a wing of their own: `web/export_campus.py` writes every
`S.carry` object as `prop__<scene>_<k>` of `out/campus/props.glb`, in its own frame, and where it rested at t = 0 to
`out/campus/props_rest.json` (committed); `data/build_data.py` turns the carries the acting data never moves into
`static` props standing where the web left them. The props the reenactors hold are modelled again by `bl/props.py`
(`out/ue/HandProps.glb`, one tagged mesh `prop__<kind>` each, in the frame the stage sets in a palm: +X along the
fingers, +Y out of the palm); `World/WTAWaxStageActor.cpp` rides them on the hand bones and closes the fingers round
them. Neither wing is scenery: `build_level.py` skips `prop__` meshes and the stages spawn them.

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
| Yard | 104 | 73k | Coaster, Sky Drop, dive dome, playground; `ride__` / `token__` tags |
| OceanDive | 76 | 134k | The reef 420 m east of the campus |

Left out on purpose: the sky dome, wind grass, particles, people (MetaHumans replace them), web-only invisible helpers,
and the web build's baked lighting.
