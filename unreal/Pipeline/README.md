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
out/campus/*.glb + ReadingRoom.glb ──► blender/prepare_for_unreal.py ──► out/ue/<Asset>.glb   (what Unreal imports)
```

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
python unreal/Pipeline/blender/prepare_for_unreal.py            # -> out/ue/*.glb
```

The web test harness needs `three@0.170.0` and the `@fontsource` packages in `test/node_modules`, plus
`three@0.170.0` and `@dimforge/rapier3d-compat@0.14.0` in `test/nm2/node_modules`.

## What is in `out/ue/`

| Asset | Meshes | Triangles | Notes |
|---|---|---|---|
| Museum | 64 | 3k | Lobby + 3 galleries; `item__<id>` = exhibits |
| WaxIntro | 4 | <1k | Intro wall at the Wax Hall door |
| WaxHall | 167 | 54k | 12 stages (figures come later as MetaHumans) |
| LibraryShell | 31 | 1k | Interactive bits of the Reading Room: book covers (`book__<id>`), signs, Freedom board |
| ReadingRoom | 16 | 187k | The Blender-modelled room: real books on every shelf, thick walls, PBR textures |
| School | 311 | 43k | Hall + rooms 101–104; `bp__<id>` = blueprint boards |
| Outside | 25 | 91k | Building shells, ground, trees, horizon |
| Yard | 104 | 73k | Coaster, Sky Drop, dive dome, playground; `ride__` / `token__` tags |
| OceanDive | 76 | 134k | The reef 420 m east of the campus |

Left out on purpose: the sky dome, wind grass, particles, people (MetaHumans replace them), web-only invisible helpers,
and the web build's baked lighting.
