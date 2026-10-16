# XRLibraries Campus — asset migration spec for Unreal Engine 5 (photoreal)

Companion to `layout.md` (coordinates, floor plan), `content.md` (DataTables) and `systems.md` in this folder.
Everything below was read from `/home/user/xr-campus-assets` (file:line cited) or measured here with bpy 5.2.2
(`scratchpad/blvenv`) on the files in `unreal/Pipeline/out`. Engine facts come from the saved primary sources in
`scratchpad/ue/research/raw` (UE 5.7 `RendererSettings.h`, `EngineTypes.h`, `Version.h`; UE 5.8 packaged
`BaseEngine.ini`, `BaseScalability.ini`) and `research/dl/ue58traps.md`. The web (dev.epicgames.com, docs.blender.org,
GitHub) was unreachable from this container today, so every engine/API name I could not confirm from those files is
tagged **[verify]** and must be checked on the installed editor before a script relies on it. Nothing here was run in
Unreal.

Target: UE 5.7/5.8 (research holds 5.7 headers and 5.8 inis). Where it matters, Mac notes follow `ue58traps.md` §6
(5.8 on Apple silicon: Lumen SWRT and TSR on M1+, Nanite and VSM Beta on M2+, Lumen HWRT Experimental on M2+); the
research preflight recorded the user's Mac as an M5 Max on macOS 26.5.1, but a Windows PC is still possible, so the
plan does not depend on either.

---

## 0. Decisions in one table

| Asset class | Source today | Into UE as | Format / route | Photoreal treatment |
|---|---|---|---|---|
| Reading Room (hero room) | `assets/lib/library.blend` (+ `bake_work.blend`, baked twin), 28 meshes, 17 materials, 12 lights, 152,531 tris | 6 Nanite static meshes + 11 point lights + 1 directional, no lightmaps | **glTF (.glb) via Interchange**, exported by `unreal/Pipeline/blender/export_reading_room.py` (already produced `ReadingRoom.glb`, 55 MB). FBX only as fallback. | Lumen GI + reflections, VSM, master PBR materials fed from `assets/tex` originals regenerated at 4K (or Poly Haven CC0 / Megascans via Fab on the user's machine), real books on every tier (drop the shelf-row impostors), window opened to the real exterior |
| Rest of campus (museum, Wax Hall, halls, school, yard, dive) | procedural three.js (`parts/*.js`), canvas textures | per-wing greybox GLBs as layout truth + rebuilt thick shells + hero props | **Hybrid**: (a) headless Playwright + `GLTFExporter` (done: `unreal/Pipeline/web/export_campus.py`, 8 wings) for placement, sizes, tags and art; (b) `layout.json` → thick wall/floor/ceiling solids (bpy `Builder` from `bl/library.py` or UE Python); (c) Blender/bpy only for hero props | Replace every canvas "surface" texture with a real PBR set; keep canvas *art* (posters, signs, covers) as lit paper materials; Nanite on all opaque geometry; emissive glows become real lights |
| Canvas art (16 exhibits, ~100 signs/posters/covers/cards, chalkboard, murals) | drawn in `parts/art.js`, `art2.js`, `outdoor.js`, `rooms.js`, `waxpaint.js` with Google fonts | PNG textures (sRGB, non-tiling) + a UMG/render-target path for the few dynamic ones | `window.__test.ART[k].toDataURL()` already exports the 16 exhibits; extend to every `map.image` canvas (section 3) | Lit "paper/board" master material; frames, mats, glass as real geometry |
| People (40 Rocketbox avatars: 4 staff, 38 wax-figure castings, the player body, the keeper) | `hk/out/h/*.hk` (custom meshopt+WebP container) built from Microsoft Rocketbox FBX | MetaHumans for every close-up role; Rocketbox FBX skeletal meshes as fallback and crowd LOD | Rocketbox originals: `github.com/microsoft/Microsoft-Rocketbox` @ `0943055d…`, `Assets/Avatars/<group>/<Name>/Export/<Name>.fbx` (section 4) | MetaHuman Creator in the editor (5.6+), wax look as a skin material variant, poses/choreography exported from the web build as glTF animation and retargeted |

---

## 1. The Reading Room (Blender → UE5, no baked light)

### 1.1 What is in the .blend (verified with bpy on `assets/lib/library.blend`)

`bl/library.py` builds the room at campus coordinates (x −32..−12, z −13..7, H 7.6; `library.py:5-6,196`), with
`P(x,y,z) = Vector((x, −z, y))` (`library.py:29`). 28 mesh objects, 17 materials, 12 lights, 152,531 triangles.
`bake_work.blend` is the same scene after `bl/bake.py` and `bl/bake_rows.py` (lightmap UVs `lm`, vertex colour `light`,
`shelfrows` turned into a lightmapped object); use `library.blend` for Unreal — it is the pre-bake twin and
`export_reading_room.py:58-65` strips `lm`/`light` anyway.

| Object (`library.py` line) | Material | Tris | Web bake | UE static mesh (proposal) | Nanite | Notes |
|---|---|---|---|---|---|---|
| `floor` (202) | `floor` = oak_floor col/rgh/nrm, rough 0.45 | 32 | lightmap | `SM_RR_Shell` slot Floor | yes | 20×20 m, box UV tile 2 m |
| `ceiling` (206) | `plaster` | 72 | lightmap | `SM_RR_Shell` slot Plaster | yes | laylight hole −30..−14 × −3.9..−2.1 |
| `walls` (222) | `green` = green plaster col/rgh/nrm, rough 0.85 | 97 | lightmap | `SM_RR_Shell` slot Green | yes | inside faces only, zero thickness → see 1.4 |
| `mezz` (256) | `plaster` | 374 | lightmap | `SM_RR_Shell` | yes | 0.95 m deep slabs at 3.6 m |
| `coffers` (270) | `plaster_v` | 1,796 | vertex | `SM_RR_Shell` slot Plaster | yes | merge `_v` twin into `plaster` |
| `reveals` (249) | `plaster_v` | 74 | vertex | `SM_RR_Shell` | yes | door/window jambs, 0.45 m wall thickness |
| `laylight_frame` (215) | `plaster_v` | 460 | vertex | `SM_RR_Shell` | yes | |
| `mezz_trim` (262) | `walnut_v` | 438 | vertex | `SM_RR_Shell` slot Walnut | yes | |
| `window_frame` (281) | `walnut_v` | 716 | vertex | `SM_RR_Shell` | yes | arch, mullions, sill |
| `rails` (428) | `brass_v` = brass col/rgh, metallic 1.0, rough 0.35 | 6,820 | vertex | `SM_RR_Furniture` slot Brass | yes | balusters every 0.15 m |
| `cases` (396) | `walnut_v` | 57,544 | vertex | `SM_RR_Cases` | yes | 7 wall runs + 8 stack cases |
| `case_ends` (413) | `walnut_v` | 1,248 | vertex | `SM_RR_Cases` | yes | |
| `books` (397) | `books_v` = books atlas 2048² col + rgh, rough 0.75 | 76,304 | vertex | `SM_RR_Books` | yes | every book a box; ground tier only |
| `shelfrows` (398) | `shelfrow_v` = 4096×512 strip | 60 | own lightmap | **drop** | – | impostor strips for upper tiers; rebuild as real books (1.5) |
| `furniture` (449) | `walnut_v` | 2,564 | vertex | `SM_RR_Furniture` | yes | desk, tables, chairs, board frame |
| `tabletops` (450) | `oak` = oak col/rgh/nrm, rough 0.42 | 40 | lightmap | `SM_RR_Furniture` slot Oak | yes | |
| `seats` (451) | `leather_v` | 768 | vertex | `SM_RR_Furniture` slot Leather | yes | |
| `ladder` (479) | `walnut_v` | 372 | vertex | `SM_RR_Furniture` | yes | |
| `globe` (486) | `globe_v` colour 0.16/0.35/0.48 | 1,216 | vertex | `SM_RR_Furniture` slot Globe | yes | UV sphere; give it a real map texture |
| `lamp_brass` (452), `pendants` (492) | `brass_v` | 284 + 688 | vertex | `SM_RR_Furniture` slot Brass | yes | |
| `lamp_shades` (453) | `shade_e` emissive 0.25/0.9/0.4 ×2.5 | 84 | none | `SM_RR_Emissive` | yes | banker's-lamp green glass: translucent-ish emissive |
| `lamp_bulbs` (454), `pendant_bulbs` (493) | `bulb_e` emissive 1/0.85/0.6 ×25 | 84 + 384 | none | `SM_RR_Emissive` | yes | the real light comes from the point lights |
| `laylight` (212) | `laylight_e` emissive 0.92/0.95/1 ×7 | 2 | none | `SM_RR_Emissive` | no (2 tris) | 16×1.8 m panel; pair with a RectLight (1.6) |
| `window_glass` (305) | `glass` 0.9/0.95/1, rough 0.05, alpha 0.12 | 2 | none | `SM_RR_Glass` | **no** (translucent) | `export_reading_room.py:66-69` sets `surface_render_method='BLENDED'` so it exports as glTF BLEND |
| `window_view` (308) | `view_e` = window_view.png emissive ×1.1 | 2 | none | **drop** | – | 2.5 m-out backdrop; the real exterior replaces it (1.6) |
| `rugs` (313) | `rug` = rug col/rgh/nrm 2048×1024, rough 0.95 | 6 | lightmap | `SM_RR_Rugs` | no (coplanar risk) | 3 rugs at y 0.012; keep as separate mesh with a tiny z offset or make them 12 mm thick |
| lights `L`..`L.010`, `Sun` (503-512) | – | – | – | 11 `PointLight` + 1 `DirectionalLight` | – | positions/watts in `unreal/Pipeline/out/reading_room/lights.json` |

Materials defined but with no users (`library.py:104,110-111`) and therefore not saved in the .blend: `marble`,
`dark_v`, `ironblack_v`. Image sources are `//../tex/*.png` = `assets/tex` (the originals); `assets/lib/*_col/_nrm/_rgh.png`
are the **shrunk web copies** written by `bl/post.py:72-86` — never import those into UE.

### 1.2 Format: glTF (chosen), FBX, USD

| | glTF 2.0 (.glb / .gltf+bin) | FBX | USD |
|---|---|---|---|
| UE path | Interchange: `InterchangeGLTFTranslator` → `DefaultGLTFAssetsPipeline` + `DefaultGLTFPipeline` (assets) or `DefaultGLTFSceneAssetsPipeline` + `DefaultSceneLevelPipeline` (scene) — confirmed in `BaseEngine_UE5.8.ini:3328-3329` | Interchange `InterchangeFbxTranslator` → `DefaultFBXOBJAssetsPipeline` (same ini) | USD Importer plugin / USD Stage actor [verify current plugin name and whether Interchange handles USD in 5.8] |
| Material fidelity from Blender Principled | base colour, metallic, roughness (packed ORM), normal, emissive + `KHR_materials_emissive_strength`, alpha BLEND, double-sided — exactly what `library.py:60-89` uses | FBX carries Phong-style parameters; roughness/metallic textures are not round-tripped reliably from Blender's exporter → materials would be rebuilt by hand | UsdPreviewSurface carries all of it; Blender 5.2 exporter also writes MaterialX [verify option names in `bpy.ops.wm.usd_export`] |
| Units/axes | metres, Y-up, right-handed; UE converts to cm, Z-up | cm or m with file unit scale; Blender exporter option `apply_scale_options` | metres with `metersPerUnit`; UE USD stage handles scale |
| Already produced | yes: `unreal/Pipeline/out/reading_room/ReadingRoom.glb` (28 meshes, 17 mats, 41 images, 152,531 tris, bounds x −34.5..−11.5, z −13..7, y −1..8.6 — the backdrop quad sticks out west) | no | no |
| Verdict | **primary** | only for the Rocketbox avatars (they are FBX) | optional later, for layered editing |

Why 41 images: Blender's glTF exporter packs roughness (+metallic) into one `metallicRoughness` image per material and
re-encodes PNGs; the 2048² books atlas and the 4096×512 shelf strip make the file 55 MB. Two cleaner options:

1. Keep `.glb` for geometry/materials but let the UE Python step re-point every imported material instance at the
   original (or 4K) textures from `assets/tex` (section 1.3). Simplest; recommended.
2. Export `export_format='GLTF_SEPARATE'` with `export_keep_originals=True` so the glTF references the PNGs in
   `assets/tex` instead of embedding re-encoded copies [verify that keep_originals is honoured for a roughness map
   that the exporter would otherwise pack into ORM].

Exporter call that produced the file (`export_reading_room.py:72-86`): `bpy.ops.export_scene.gltf(export_format='GLB',
export_yup=True, export_apply=True, export_texcoords=True, export_normals=True, export_tangents=True,
export_materials='EXPORT', export_image_format='AUTO', export_vertex_color='NONE', export_lights=False,
export_cameras=False)`. Add `export_image_quality`/`export_jpeg_quality` only if JPEG is wanted (it is not: keep PNG).

### 1.3 Scale and axes

- Blender metres, Z-up. `export_yup=True` turns Blender `(x, −z, y)` into glTF `(x, y, z)` = three.js campus axes
  (`docs/realism-plan.md:25`, `bl/library.py:4,29`); this is why `lib/lib.glb` loads "already in campus coordinates"
  (`parts/baked.js:73`).
- UE import of glTF: metres → centimetres (×100) and Y-up right-handed → Z-up left-handed. The repo's stated map is
  glTF `(x, y, z)` m → UE `(X = x, Y = z, Z = y)` × 100 cm (`export_reading_room.py:18-20`, derived in `layout.md` §1 as a
  non-mirroring swap). **Verify on first import** with the door: campus `(−12, 0..3.4, −4.6..−1.4)` must land at UE
  `X=−1200, Y=−460..−140, Z=0..340`; the arched window at `X=−3200, Y=−520..−80`. If text on the exhibit posters reads
  mirrored, the importer's axis handling is wrong, not the data.
- If FBX is ever used for this room: `bpy.ops.export_scene.fbx(apply_scale_options='FBX_SCALE_UNITS',
  axis_forward='-Y', axis_up='Z', use_mesh_modifiers=True, mesh_smooth_type='FACE', use_tspace=True,
  path_mode='COPY', embed_textures=True)` — check a 1 m cube imports at 100 UU (these are long-standing io_scene_fbx
  parameter names; [verify] against Blender 5.2's `bpy.ops.export_scene.fbx` signature).

### 1.4 Material conversion (glTF PBR → UE)

Interchange creates one Material Instance per glTF material on top of Epic's glTF parent materials. For a photoreal
result do not keep those: build project master materials and re-parent/re-texture each instance in the editor Python step.

| glTF/Blender material | UE master | Parameters | Textures to feed (from `assets/tex`, regenerate at 4K first, see 1.7) |
|---|---|---|---|
| `floor` | `M_Campus_Opaque` (BaseColor, ORM or separate Roughness, Normal, UV tiling, triplanar switch) | rough 0.45 | `oak_floor_col/_rgh/_nrm` (2048² → 4096²) |
| `plaster`, `plaster_v` → one | same | rough 0.9 | `plaster_*` |
| `green` | same | rough 0.85 | `green_*` |
| `walnut_v` → `walnut` | same | rough 0.4, normal strength 0.6 (`library.py:93`) | `walnut_*` |
| `oak` | same | rough 0.42 | `oak_*` |
| `leather_v` → `leather` | same | rough 0.6 | `leather_*` |
| `brass_v` → `brass` | same, Metallic 1.0 | rough 0.35 | `brass_col/_rgh` (512² — regenerate at 2048²) |
| `books_v` → `books` | same | rough 0.75 | `books_col` 2048² atlas + `books_rgh` (make a 4096² atlas: `bl/textures.py:176-230` sizes are constants) |
| `rug` | same | rough 0.95 | `rug_*` 2048×1024 → 4096×2048 |
| `globe_v` | same | plain colour | add a real globe map (public domain) |
| `glass` | `M_Campus_Glass` translucent (Thin Translucent shading model if Substrate is off; Substrate slab with coverage otherwise) | opacity 0.12, rough 0.05 | – |
| `shade_e`, `bulb_e`, `laylight_e` | `M_Campus_Emissive` (Emissive colour × strength) | strengths 2.5 / 25 / 7 (`library.py:106-108`) | – |
| `view_e` | drop | | |

Normal-map convention: `bl/textures.py:34-42` writes **OpenGL +Y** (glTF convention). Interchange flips it for glTF
materials automatically [verify]; textures imported directly as PNG for the master materials must either be imported
with the green channel flipped (texture setting "Flip Green Channel" [verify the property name]) or regenerated with
`ny = -dy * strength` in `textures.py:38` as a `_nrm_dx` variant. Import flags: `_col` sRGB on; `_rgh`, `_nrm` sRGB off;
`_nrm` compression Normalmap; `_rgh` Masks/Grayscale.

Substrate: 5.7+ turns Substrate on for **new** projects (`ue58traps.md` §4, `RendererSettings_5.7.h:1220 r.Substrate`).
Decide once in `Config/DefaultEngine.ini` before authoring the master materials: Substrate materials render black with it
off and "Convert to Substrate" is one-way.

### 1.5 What to merge, and Nanite

- Merge by *role* not by material: a UE static mesh carries several material slots, so `SM_RR_Shell` (floor, ceiling,
  walls, mezz, coffers, reveals, laylight_frame, mezz_trim, window_frame), `SM_RR_Cases` (cases, case_ends),
  `SM_RR_Books`, `SM_RR_Furniture` (furniture, tabletops, seats, ladder, globe, lamp_brass, pendants, rails),
  `SM_RR_Emissive` (lamp_shades, lamp_bulbs, pendant_bulbs, laylight), `SM_RR_Glass`, `SM_RR_Rugs`. Do the joins in
  Blender (`bpy.ops.object.join` after selecting the group, in a copy of the scene) so the glTF carries 7 meshes, or
  import the 28 and join in UE with `StaticMeshEditorSubsystem.join_static_mesh_actors` [verify].
- Nanite on every opaque mesh: `unreal.MeshNaniteSettings` (C++ `FMeshNaniteSettings`, `EngineTypes_5.7.h:3040-3098`:
  bool enabled, PositionPrecision, NormalPrecision, TangentPrecision, KeepPercentTriangles, TargetMinimumResidencyInKB…)
  applied with `StaticMeshEditorSubsystem.set_nanite_settings(mesh, settings, apply_changes=True)` [verify signature;
  `research/dl/toolkit-map.md` §4 reads `nanite_settings.enabled` on StaticMesh]. Project flag
  `r.Nanite.ProjectEnabled` (`RendererSettings_5.7.h:693`). Not for `window_glass` (translucent) — Nanite does not
  rasterise translucent materials; masked/opaque are fine.
- Lumen needs **thickness and closed volumes**: the Blender walls are single inside faces (`library.py:221-247`) with
  no outside; the campus exterior shell (`outdoor.js:299-305`) builds the library's east/north/south stone walls but
  **no west wall**, so the arched window would look at nothing. Add in `library.py` (or the UE shell generator) a
  0.45 m-thick west wall with the arch cut, plus 0.45 m thick north/south/east walls so the Reading Room is a closed
  box joined to the hall. Also give `walls` back faces (or make the shell boxes) so Lumen's cards and the mesh
  distance field (`r.GenerateMeshDistanceFields`, `RendererSettings_5.7.h:679`) have a real volume.
- Real books on every tier: `bookcase(... impostor=(y0 > 1))` (`library.py:411`) swaps the mezzanine tiers for the
  4096×512 strip. Set `impostor=False` for all tiers and re-run `bl/library.py --nobake` (the only bake-free step; it
  writes a new `library.blend` in seconds). Expect `books` to grow from 76k to roughly 250-300k tris — trivial under
  Nanite, and it removes the one obviously fake surface in the hero room. Keep the `fill_row` seed (`library.py:26`)
  so the layout does not change.

### 1.6 Lights, emissives, the window (Lumen lights the room)

`unreal/Pipeline/out/reading_room/lights.json` holds 11 point lights + sun in campus metres (`export_reading_room.py:39-56`):
7 lamp bulbs at 18 W warm (1.0/0.75/0.45) above the desk (−18.3, 1.35, −7.0) and the two reading tables (−18.7/−17.5/−16.3
× z −10.8 and 4.6, y 1.09), 4 pendants at 200 W (1.0/0.88/0.72) at (−27.5|−16.5, 5.45, −9.5|3.5), radius 0.08 m.

- Blender point-light Watts are not photometric. Starting values for UE (then match by eye to
  `assets/lib/preview_window.jpg` / `preview_stacks.jpg`, the Cycles references): lamp bulbs ≈ 800-1000 lm (set the
  light's intensity unit to lumens), source radius 2 cm, soft source length for the 0.26 m tube; pendants ≈ 8-11 klm
  each (8 bulbs), source radius 8 cm. Temperature: use the RGB from the JSON or 2700 K / 3000 K.
- Laylight: the 16 × 1.8 m emissive panel (`library.py:212-213`, strength 7). Lumen does light from emissive surfaces,
  but a large soft source is better as a **RectLight** (16 × 1.8 m, ~5000 K, a few klm) under the panel, with the panel
  material emissive at ~2-3 for the look. Keep bulbs' emissive low (glow only, ~5) once the point lights exist, or Lumen
  double-lights.
- Sun: `library.py:508-512` = 26 W/m² from the west, 19° elevation, slightly toward −z; the campus sun is
  `SUN_DIR=[40,62,30]` (`outdoor.js:4`, rotator in `layout.md` §1). Use **one** DirectionalLight for the whole campus
  (the campus one) plus `SkyAtmosphere` + `SkyLight` (real-time capture); `bSupportSkyAtmosphere`
  (`RendererSettings_5.7.h:992`). The room's west window then gets the real sky. Exposure in EV100 with "Extend default
  luminance range" (`r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange`, `RendererSettings_5.7.h:809-810`).
- Reflections: `r.ReflectionMethod` Lumen (`RendererSettings_5.7.h:586`); the web probe (`probe.hdr`) is not needed.
  Add a SphereReflectionCapture at (−22, 1.6, −3) only as a fallback for Lumen-off scalability.
- Glass reflections: "High Quality Translucency Reflections"
  (`r.Lumen.TranslucencyReflections.FrontLayer.EnableForProject`, `RendererSettings_5.7.h:613`).

### 1.7 Textures for photorealism

`bl/textures.py` generates every map procedurally (FFT noise, periodic → tileable). Sizes are constants:
oak_floor 2048 (`:94`), walnut/oak/plaster/green/leather/marble 1024 (`:101,107,113,123,131,239`), brass 512 (`:233`),
rug 2048×1024 (`:141`), books 2048² (`:179`), shelfrow 4096×512 (`:280`), window_view 2048² (`:251`). For "brand-new AAA":

1. Regenerate at 4K: raise `n` (and `W,H`) ×2-×4; runtime is seconds-to-minutes per map (numpy FFT). Keep the seeds.
2. Better: on the user's machine Cowork can fetch CC0 photoscans from Poly Haven (api.polyhaven.com — the proxy blocks
   it here, `docs/realism-plan.md:17`, not there) for oak floor, walnut, plaster, leather, brass; and Quixel Megascans
   surfaces/props through the Fab plugin inside the editor (free for Unreal use — confirm the current Fab terms in the
   plugin). Map them onto the same master-material parameters; the generated set stays as the licence-clean fallback.
3. Use Virtual Texturing for 4K sets if memory bites [verify the 5.8 project setting name before scripting it].

---

## 2. The rest of the campus (procedural three.js → UE)

### 2.1 What exists, what exports, how the scene is exposed

`parts/*.js` do **not** expose the scene themselves (no `window.__test` anywhere in `parts/`). The debug hook is
injected by the Playwright harness: `test/harness.py:13-25` loads the assembled `xrlibraries-campus.html`, replaces
`const ART = {};` (`world.js:6`) with `window.__ART = {}` and splices a `window.__test = { … }` export block in front
of `boot();` exposing `scene`, `renderer`, `camera`, `WING`, `ART`, `LAMPS`, `LIGHTS`, `STAFF`, `NATURE`, `BK`, `HK`,
`WAX_SCENES`, `pickItems`, `mergeStatic`, etc. (line 16-24). Every CDN request is routed to local copies
(`harness.py:76-110`): three r170 from `test/nm2/node_modules`, Google fonts to `@fontsource` woff2 (so posters render
with Old Standard TT / Libre Franklin / Courier Prime), avatars from `hk/out/h`, the baked room from `assets/lib`.
Chromium is `/opt/pw-browsers/chromium-1194` launched with `--use-angle=swiftshader --enable-unsafe-swiftshader`
(`harness.py:73`): WebGL2 on SwiftShader, no GPU needed; boot at `CAMPUS_GFX=high` takes a few minutes
(`BOOT_TIMEOUT=240000` in `export_campus.py:34`).

`GLTFExporter` is injected at runtime (`export_campus.py:44-45`): `import('https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/exporters/GLTFExporter.js/+esm')`,
which the harness serves from `test/nm2/node_modules/three/examples/jsm/exporters/GLTFExporter.js` with its relative
imports rewritten (`harness.py:48-61`). Export is `parseAsync(WING[k], { binary:true, onlyVisible:false,
maxTextureSize:2048 })` (`export_campus.py:143`), pulled out of the page in 4 MB base64 chunks (`:149-172`).

Results (bpy import of each file, triangle counts after Blender's instancing expansion):

| Wing | File | Meshes | Tris | Materials | Bounds (campus m) | What it holds |
|---|---|---|---|---|---|---|
| museum | museum.glb 13.2 MB | 136 | 3,256 | 98 | x ±12, z −42.3..0, y 0..4.4 | lobby, 3 galleries, halls: walls/floors/ceilings (planes), frames, pedestals, 16 exhibits, signs |
| waxIntro | waxIntro.glb 0.5 MB | 6 | 52 | 4 | x ±3.2, z −44.8..−44.4 | the Wax Hall intro wall, both faces |
| wax | wax.glb 16.8 MB | 766 | 75,910 | 378 | x ±8.7, z −81.2..−42.1, y 0..5.2 | 12 stages with backdrops, floors, props |
| lib | lib.glb 8.5 MB | 89 | 1,211 | 56 | x −32..−12, z −13..7, y 0..7.6 | **only** the interactive layer: ghost collision walls/floor, book covers, subject signs, table cards, hanging sign, freedom board, shelf pick proxies (the room is Blender's) |
| school | school.glb 14.5 MB | 689 | 49,641 | 343 | x 0..34.1, z −13.4..7, y 0..4 | corridor, lockers, Rooms 101-104, stations, blueprint board, world room |
| outside | outside.glb 2.5 MB | 824 | 90,578 | 25 | x −290..350, z −328..312, y −2..23.5 | 640 m ground plane, horizon rings, building shells, roofs, trees (instanced), yard trees |
| play | play.glb 5.3 MB | 1,219 | 74,388 | 118 | x −0.3..95.3, z −33.9..27.9, y −0.4..36 | pavers, arch, signpost, benches, fences (instanced), coaster, drop tower, dive dome, swings, slide, spinner, soccer |
| dive | dive.glb 1.4 MB | 1,581 | 133,955 | 77 | x 290..550, z −130..130, y −24.3..2 | the Ocean Dive ride scene, parked 420 m east |
| (Reading Room) | reading_room/ReadingRoom.glb 55 MB | 28 | 152,531 | 17 | see 1.1 | |

What the PREP pass removed (`export_campus.py:70-130`, `manifest.json`): sky dome (shader mesh), grass, 43 points/lines/
sprites, 4 staff roots, every skinned mesh, the baked room, 6 custom attributes; 110 "boosted" glow materials became
black + emissive (`:90-96`); 226 nodes were tagged `item__ / staff__ / ride__ / token__ / station__ / book__ / bp__`
(`:124-127`). 16 exhibit PNGs and `lights.json` (18 point lamps + sun) were written alongside.

### 2.2 Three ways to get the campus into UE, and the recommendation

| | (a) Playwright + GLTFExporter greybox (exists) | (b) Rebuild from layout data in UE Python | (c) Re-model in Blender via bpy |
|---|---|---|---|
| What it gives | exact positions, sizes, rotations of ~5,000 meshes, art already placed, tags for gameplay, 443 canvas textures embedded | thick walls/floors/ceilings/doors/windows from `layout.json` (`gen_layout.py` here) as clean solids; nothing else | anything, at any quality; the `Builder` class in `bl/library.py:114-193` already makes thick boxes with world-scale UVs at campus coordinates |
| Cost | done; a v2 export is a few edits (2.3) | small script: ~15 rooms × 4 walls + openings | a rewrite of `world.js`, `rooms.js`, `waxhall.js`, `outdoor.js`, `rides.js`, `lab.js`, `worldroom.js`… (≈ 400 KB of JS) — weeks |
| Photoreal ceiling | low: planes with canvas textures, no thickness, `BoxGeometry` props | medium: correct architecture, but no props | high |
| Lumen-friendliness | poor (zero-thickness walls leak light, single-sided) | good | good |

**Recommendation: hybrid, in this order.**

1. Keep (a) as the **layout truth and the art carrier**. Import each wing with the Interchange *scene* pipeline
   (`DefaultGLTFSceneAssetsPipeline` + `DefaultSceneLevelPipeline`, `BaseEngine_UE5.8.ini:3329`) so every node becomes an
   actor with its name tag; park them in a `Greybox` sub-level that is hidden in the shipped game and used for
   collision/navigation blocking and as the reference the art pass must match.
2. Generate the **architecture** from `layout.json` as thick solids (walls 0.3-0.45 m, floors 0.3 m, ceilings 0.3 m,
   door and window cuts) — in Blender with the existing `Builder` (fast, one script, same coordinate convention as the
   Reading Room, exported as one glTF per wing, Nanite on) — or with UE Python spawning scaled engine cubes if Blender
   is unavailable on the machine. This is what makes Lumen behave: no light leaks, correct bounce, real door reveals.
3. Replace every **surface** material (plaster, floors, lino, tile, cork, brick, stone, pavers, grass, bark) with real
   PBR sets through the master materials; the greybox's canvas "surfaces" (`art.js:560-690` canvasFloor/Plaster/Lino/
   Tile/Cork/Locker/SchoolWall, `outdoor.js:39-118` grass/brick/stone/pavers/chips/sky) are discarded.
4. Replace repeated **props** with hero meshes: Megascans (benches, lockers, lamps, chairs, trees, rocks) and bpy-built
   bespoke pieces (the Comet Coaster track from `coasterPoints()` `outdoor.js:457-468` swept along the Catmull-Rom spline;
   the drop tower; the dive dome) — this is where (c) earns its keep, and only there.
5. Terrain: drop the 640 m ground plane and the two horizon rings (`outdoor.js:247-267,269-276`); use a Landscape
   with a grass material + Landscape Grass/PCG scatter and distant Megascans trees; `SkyAtmosphere` + volumetric clouds
   replace `canvasSkyDome` (`outdoor.js:95-118`) and the sky shader (`gfx.js:53-84`).
6. Trees: the web trees are 3 instanced meshes (trunk cylinder, icosahedron core, 30 leaf cards) (`nature.js:74-96`)
   — replace with real tree assets; `r.Nanite.Foliage` is still Experimental in 5.7 (`RendererSettings_5.7.h:1503`),
   so use non-Nanite masked foliage unless the probe says otherwise.

### 2.3 Required fixes for an export v2 (`unreal/Pipeline/web/export_campus.py`)

1. **Skip invisible materials.** `GLTFExporter` with `onlyVisible:false` exports meshes whose material has
   `visible:false` as normal grey meshes: the library ghost walls/floor (`world.js:413-418`), the shelf pick proxies
   (`world.js:436-437`), `PICK_PROXY` boxes on every figure (`humans.js:205`, `outdoor.js:10`). In UE they would be
   solid walls inside the Reading Room and 0.55 × 1.8 m boxes around every person. Add to the traverse:
   `if (ms.some(m => m && m.visible === false)) kill.push([o, 'invisible'])`.
2. **Name the textures.** Canvas textures have no `name`, so Interchange will import `image_0 … image_442`. Before
   export, for every material slot set `t.name = wingKey + '_' + (o.name || o.parent.name) + '_' + slot`; also give
   posters/signs a `userData.art` tag so the UE side can tell "paper" from "surface".
3. **Expand `InstancedMesh`** (fence posts/rails `outdoor.js:427-444`, cover books `world.js:422-454`, trees) into
   plain meshes before export unless Interchange's glTF translator is confirmed to read `EXT_mesh_gpu_instancing`
   [verify]; Blender read them, UE is unconfirmed.
4. **Export people and poses** instead of killing them (`:78-80`): a second pass walks `HK.figs` (`humans.js:214`) —
   id, `look.av`, root `matrixWorld`, and the 17-joint pose (`HK_CTRL`, `humans.js:15`) sampled over each wax scene's
   `loop` seconds as `THREE.QuaternionKeyframeTrack`s into an `AnimationClip`, then `parseAsync(fig.root, { animations:[clip] })`
   per figure. `GLTFExporter` handles `SkinnedMesh` + skeleton + animation, and the WebP `ImageBitmap` textures pass
   the `okTex` filter (`:53-68`). This preserves the authored choreography of `waxscenes.js` for retargeting (4.4).
5. **Write `staff.json`** from `STAFF` (`people.js:4-21`): margaret (0.68, −4.0) facing (0, −0.7); rosa (−17.2, −7.75)
   facing (−13, −3); hale (17.4, −10.6) facing (19, −4.75); rae (46.4, 0.4) facing (38, −3), with `view` stands.
6. Lights: `lights.json` sun is the *moved* shadow-camera position (`gfx.js:203`), not the direction; use `SUN_DIR`
   (`outdoor.js:4`). Lamps are correct (`LAMPS.all` is captured before the pool trims to 8, `gfx.js:168-171`).
7. Optional: `CAMPUS_NOMAP`/`CAMPUS_MIN` must stay unset; keep `CAMPUS_GFX=high` so `gfxUpgradeScene` has run and
   materials are `MeshStandardMaterial` (roughness/metalness survive; `gfx.js:242-277`).

### 2.4 Importing the wings (editor Python, names to verify on the installed engine)

`unreal.AssetImportTask()` with `filename`, `destination_path`, `automated=True`, `save=True`, `replace_existing=True`,
then `unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])` and `task.get_objects()`
(`AssetImportTask.result` is deprecated and `destination_name` is ignored when Interchange handles the file —
`ue58traps.md` §1). Interchange is the handler for `.glb`/`.fbx` (ini above). Pipeline overrides through
`InterchangeGenericAssetsPipeline` (`BaseEngine_UE5.8.ini:3332`) [verify how to pass it on `AssetImportTask.options`].
After import: Nanite on (1.5), simple collision from the greybox boxes, materials re-parented with
`unreal.MaterialEditingLibrary.set_material_instance_parent / set_material_instance_texture_parameter_value /
set_material_instance_scalar_parameter_value / update_material_instance` [verify these long-standing names still exist
in 5.8], actors spawned through `unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class`
(`ue58traps.md` §1 — not `EditorLevelLibrary`).

---

## 3. Canvas-drawn art → PNG textures

What is drawn in code: 16 museum exhibits (`art.js:40-293`, `makeArt` sizes 900-1000 px, playbook 600×800), 15 book
covers (`drawBookCover` 512×700 / 384×526 at use, `art.js:318-339`, `world.js:431,450`), signs and panels (title/partners/
directory 1600×844 and 1500×800, plaque 1200×520, door signs 1400×240, wing signs 1300×220, placards 600×340,
subject signs 560×200, hanging sign 1400×380, table cards 900×200, room signs 700×300, posters 600×820, flyers 360×460,
chalkboard 1800×640, clock 256², mural 1600×1100, yard/ride/arrow/station/tower signs `outdoor.js:126-220`, wax cards and
backdrops `waxpaint.js`), plus the dynamic ones (front pages `art2.js:445-578`, paint easel, staff labels
`art2.js:126-134`).

- **Already exported**: the 16 exhibits as `unreal/Pipeline/out/campus/art/<id>.png` via
  `window.__test.ART[k].toDataURL('image/png')` (`export_campus.py:177-186`; `ART` is filled at `ui.js:823`).
- **Extend** the same loop to every canvas in the scene: traverse all materials, collect `map.image` instances of
  `HTMLCanvasElement`, de-duplicate, `toDataURL`, name as in 2.3(2); write a sidecar JSON with `[w, h, meshName, wing,
  isRepeating(t.wrapS === RepeatWrapping), repeat.x/y]`. Repeating ones are the surfaces to discard; non-repeating are art.
  Desktop mode keeps `LEAN_CANVAS=false` (`world.js:17`), so nothing is shrunk or released.
- Resolution: posters at 900-1000 px over 0.9-1.3 m → ~1000 px/m, enough for a 4K screen at 1 m. If larger is wanted,
  only `drawFrontPage(a, k)` already takes a scale factor (`art2.js:445`); scaling `mk()` globally
  (`helpers.js:15`) breaks drawers that read `c.width` (e.g. `drawStaffLabel`), so re-render selected posters by
  temporarily patching `makeArt` sizes instead.
- Colour: canvases are sRGB (`tex()` sets `SRGBColorSpace`, `world.js:63`); import as sRGB, no mip bias; `TextureGroup`
  World or UI as appropriate. Fonts render correctly only through the harness (`harness.py:36-46` font routing).
- In UE these are **lit** (`M_Campus_Paper`: base colour = PNG, roughness 0.55-0.7, slight normal from a paper/board
  tile), inside real frames/mats/glass. The web used unlit `MeshBasicMaterial` + `toneMapped:false` (`world.js:66,221`)
  precisely because it had no good lighting; Lumen fixes that.
- Dynamic content (front-page printer, 3D paint, staff "TAP TO ASK" labels, station screens) → UMG widgets or
  `CanvasRenderTarget2D` drawn from the same data (`content.md`), not baked PNGs.

---

## 4. People: Rocketbox today, MetaHumans tomorrow

### 4.1 Where the originals are and how they are used

`hk/build.mjs:14-29`: pinned commit `0943055db6ec570bcef9f2c8b41c9e5467c808f9` of
`https://github.com/microsoft/Microsoft-Rocketbox` (MIT, `hk/ROCKETBOX-LICENSE.txt`; jsDelivr mirror at `:17`).
Each avatar: `Assets/Avatars/<Adults|Children|Professions>/<Name>/Export/<Name>.fbx` (`:99`) and
`Assets/Avatars/<…>/Textures/*.tga` (`:192`, body normal maps `_body_normal.tga` `:206`). The FBX are 3ds Max Biped
rigs in centimetres (`:121,147` × 0.01), 80 canonical bones `Bip01_*` including jaw, lips, eyes, lids (`hk/names.json`),
4-6.7k verts / 6.4-9.9k tris each (`hk/out/build.log`), 1-2k TGA textures. The GitHub repo could not be reached from
this container (not allowed for this session), but the build log proves all 40 downloaded from those paths at that
commit. `hk/out/h/*.hk` (and the base64 `hk/out/art/h/*.hk.txt`) are a custom container (`HK01` + JSON + meshopt +
WebP, `humans.js:36-73`) — not importable; go back to the FBX.

### 4.2 Who is who (40 ids)

| Role | Avatar id(s) → Rocketbox name | Where |
|---|---|---|
| Margaret, museum guide | `bf02` Business_Female_02 | `people.js:5-8` |
| Rosa, reference librarian | `fa14` Female_Adult_14 | `people.js:9-12` |
| Mr. Hale, workshop teacher | `ma05` Male_Adult_05 | `people.js:13-16` |
| Coach Rae, recess coach | `sf02` Sports_Female_02 | `people.js:17-20` |
| Your body (yard, stations) | `sm04` Sports_Male_04 | `socplay.js:17-19`, `hands.js:16-19` |
| The keeper (lime kit, dyed) | `sm02` Sports_Male_02 | `socplay.js:36` |
| Wax 1 *The First Headsets* 2016 | `fa12`, `ma02`, `mc02` | `waxscenes.js:62-64` |
| Wax 2 *VR Goes Statewide* 2017 | `ma12`, `bf03`, `ma06` | `:115-117` |
| Wax 3 *Story Time in 3D* 2017 | `fp02`, `mc01`, `fc02`, `ma16` | `:167-173` |
| Wax 4 *Nevada Opens Its Stations* 2018 | `fa15`, `bm05`, `fa09` | `:212-214` |
| Wax 5 *VR on the Road* 2019 | `ma14`, `mc01`, `ma18` | `:261-263` |
| Wax 6 *VR in the World's Catalog* 2019 | `fa07`, `ma04`, `fa06` | `:313-315` |
| Wax 7 *XR Marin and the XR Stars* 2019 | `fa03`, `ma17`, `fc01` | `:361-363` |
| Wax 8 *Project SANDI* 2020 | `mf01`, `mm03`, `mm04` | `:406-408` |
| Wax 9 *360° Stories in Washington* 2022 | `ma07`, `fa05`, `gm01` | `:442-444` |
| Wax 10 *Lost Stories* 2022 | `ma12`, `fa11`, `ma09` | `:481-483` |
| Wax 11 *Children Draw War, Not Flowers* 2024 | `fa08`, `fa01`, `fc01` | `:531-533` |
| Wax 12 *Pollinators at the Fair* 2025 | `mc02`, `mc01`, `ma20`, `fa17` | `:571-574` |

38 wax castings reuse 33 avatar ids; with staff/player/keeper the set is the 40 in `build.mjs`. Each casting carries a
`look` (skin tone, hair style, garment colours, glasses, beard, lanyard, dye) that the web applied as material
overrides (`humans.js:142-158` hue-shift dye) — these become the MetaHuman grooms/outfits brief.

### 4.3 MetaHuman plan

- Tooling: MetaHuman Creator runs **inside the Unreal Editor from UE 5.6** (mid-2025) through the MetaHuman plugins
  (enable everything under Edit > Plugins > "MetaHuman"; exact plugin identifiers [verify in the editor]). It needs an
  Epic account/online session for cloud-side pieces [verify what 5.8 still requires]. The 2025 MetaHuman licence change
  allows MetaHumans in any engine; for a UE project nothing extra is needed.
- Close-up roles get full MetaHumans: the 4 staff (conversational NPCs, see `systems.md`), the player body
  (`socplay.js:20-22` hides the head with `colorWrite=false`; in UE use a first-person body with the head component
  `Owner No See`), the keeper. Build them in Creator from the `look` tables (sex, age band, skin tone, hair, glasses,
  beard), export at the quality level that matches distance (cinematic faces for staff; optimized for the keeper).
- The 38 wax castings: 12 scenes play 14-16 s loops (`waxscenes.js:48-574 loop:`), so they are animated, not static.
  Make ~14 base MetaHumans (one per distinct body/face archetype) and vary clothing/hair/skin per casting; the
  **wax look** is a material instance of the MetaHuman skin with subsurface pulled down, clearcoat ~0.25-0.3 and sheen
  (what `hkSkinPatch`/`waxfig.js:474` did: clearcoat 0.32, sheen 0.45, warm wrap).
- Memory: MetaHumans are heavy; keep only the current scene's figures loaded (World Partition / level streaming per
  wing, `systems.md`), and use the Rocketbox meshes as the far LOD and for any background crowd.
- Rocketbox fallback import: FBX → Skeletal Mesh + Skeleton (`Bip01` hierarchy); hair/lashes/glasses as masked
  materials (alpha TGAs); skin with a subsurface profile; body normal maps on `_body` materials. Retarget with IK Rig +
  IK Retargeter from the UE5 Mannequin/MetaHuman skeleton for walk/idle; the 80-bone face has no blendshapes, so lip
  sync stays on MetaHumans.

### 4.4 Poses and choreography

The wax poses are 17-joint Euler keyframes (`HK_CTRL`, `WAX_ORD`, `humans.js:15,199`) driven by `waxscenes.js`. Two
routes to UE, both keeping the Rocketbox bone names: (1) the glTF skinned+animation export from the harness (2.3 item 4)
→ Interchange imports Skeletal Mesh + AnimSequence [verify glTF skeletal/animation support in the 5.8 Interchange
glTF translator] → IK Retargeter onto the MetaHuman skeleton; (2) a JSON of quaternions per frame built into an
AnimSequence by editor Python [verify a 5.8 Python path to author animation keys; if none, use route 1].

---

## 5. Why the web build shows glitches and "tiny particles" (file:line)

1. **Bloom fireflies from sub-pixel, un-tone-mapped glows.** `gfxUpgradeScene` multiplies any bright untextured
   `MeshBasicMaterial` by 3.2 (`gfx.js:260-263`); those materials are `toneMapped:false` (`world.js:67,158`), so their
   HDR value goes straight into `UnrealBloomPass(…, strength 0.3, radius 0.42, threshold 1.2)` (`gfx.js:314`) computed at
   half resolution (`gfx.js:329`). The sources are tiny: 0.12 m ceiling discs (`world.js:170`), 0.014 m-tall glow
   strips over every frame (`world.js:225`), 0.03 m tube lights (`world.js:509-510`), lamp globes (`outdoor.js:397-399`).
   A thin bright thing that covers less than a pixel pops in and out as the camera moves → sparkling dots.
2. **Specular glints from auto-generated normal maps.** Every repeating canvas texture gets a normal map derived from
   its own luminance at strength 1.6 (`gfx.js:209-241`), and the canvases are seeded with 1-3 px white/black speckles
   (`art.js:10,15` `noise()`, `art2.js:64`, floor/plaster/lino generators). Each speckle becomes a bump that catches the
   point lights as a bright pixel → "particles" on floors and walls.
3. **Alpha-test shimmer.** Tree leaf cards use `alphaTest:0.42`, double-sided, a 256² leaf sheet, no alpha-to-coverage
   (`nature.js:9,84`); grass blades are 0.075 m wide (`nature.js:118`) and wind-animated every frame (`:148-150`), far
   below a pixel at distance. Only hair uses `alphaToCoverage` (`humans.js:173`).
4. **GTAO noise.** 12 samples with a 2-ring denoiser (`gfx.js:303-305`); the pattern re-seeds whenever dynamic
   resolution rescales the buffers (`gfx.js:358-365`, steps of ×0.88), so corners "dance" after a frame-rate dip.
5. **Light pool popping.** Only 8 point lights exist; they are re-assigned to the nearest lamps whenever the camera's
   rounded x/z changes (`gfx.js:158-187`), so wall brightness jumps as you walk.
6. **Shadow box edge.** The 2048 sun shadow covers a 68 m box re-centred 40 % ahead of the camera (`gfx.js:197-205`);
   turning sweeps the shadow boundary across the floor. Bias −0.0004 / normalBias 0.035 (`gfx.js:149`) is fine.
7. **Z-fighting at distance.** Camera near 0.05 / far 260 (`world.js:143`) with 2-6 mm layer gaps: door signs 6 mm off
   partition faces (`world.js:184-189`), posters 2 mm off their frames (`world.js:377-380`), paver strips 1-3 mm apart
   (`outdoor.js:359-366`). Fine up close, flickers at 30 m+.
8. **Sky sun disc.** `pow(sd, 900) * 40` (`gfx.js:65`) is a 40× bright half-degree disc rendered without tone mapping
   of its own; where leaves or mullions cut it, MSAA leaves single hot samples that bloom.

None of this transfers to UE (TSR/TAA, VSM, Lumen, real lights, Nanite). For the web build, the quick wins are:
clamp or drop the ×3.2 boost, raise the bloom threshold, generate normal maps from a blurred height (not raw speckle),
turn on `alphaToCoverage` for leaves, and stop re-ranking lights per metre.

---

## 6. Hand-off checklist for Cowork (asset side only)

1. Rebuild the Reading Room scene once with `impostor=False` and a thick, closed shell (1.5), then run
   `unreal/Pipeline/blender/export_reading_room.py` (Blender 5.2 or the bpy venv). Regenerate `assets/tex` at 4K
   (1.7) or fetch CC0/Megascans equivalents on the machine.
2. Patch `export_campus.py` per 2.3 (invisible materials, texture names, instance expansion, figures + poses,
   staff.json, SUN_DIR) and re-export the 8 wings + all canvases (3).
3. Import: Reading Room as assets (Nanite, master materials, 11 point lights + RectLight, no window backdrop);
   wings as scenes into a hidden `Greybox` sub-level; architecture solids from `layout.json`; Landscape + SkyAtmosphere.
4. Verify axes with the door/window landmarks (1.3) and one tagged token (`content.md` §0.2) before anything else.
5. People: MetaHumans for staff/player/keeper first, Rocketbox FBX fallback imported in parallel, wax scenes last.
6. Every **[verify]** above goes into the probe job before the corresponding script runs.

---

## Critic notes (2026-10-16, completeness critic; see `../critic.md`)

1. **Target is UE 5.8.x only** (not "5.7/5.8"): every engine key cited from the 5.7 headers also exists in the 5.8 inis; `.uproject` `EngineAssociation` = "5.8".
2. **Correction — the user's machine is unknown.** The sentence "the research preflight recorded the user's Mac as an M5 Max on macOS 26.5.1" is a misreading of `research/dl/ue58traps.md` §6 / `toolkit-map.md`, which are a downloaded third-party skill describing *its author's* Mac (preflight of 2026-09-24). The task brief says OS and GPU are unknown; the runbook must detect them (`critic.md` §4 G2). Nothing in this spec should assume a Mac.
3. Coordinate map in §1.3 is consistent with `layout.md` §1 and `content.md` §0.2 (critic recomputed the sun rotator, spawn, stage and staff yaws from `layout.json`). The FBX route provably gives UE = (x, z, y)·100; the Interchange glTF route is expected to match (UE's glTF conversion swaps Y/Z and negates quaternion W — recollection, not re-verified). The door/window landmark test in §1.3 plus token `t-museum` at UE (−535, −4135, 36) cm is the pipeline gate; on a mirror, switch the Blender assets to FBX and apply the swap in `export_campus.py`, never edit `layout.json`.
4. §1.5 Nanite: `FMeshNaniteSettings` fields (`bEnabled`, `KeepPercentTriangles`, `TargetMinimumResidencyInKB`, …) verified in 5.7 `EngineTypes.h`; the Python wrapper `unreal.MeshNaniteSettings` / `StaticMeshEditorSubsystem.set_nanite_settings` stays [verify]. §2.4 Interchange pipeline asset paths are verified from 5.8 `BaseEngine.ini` (`critic.md` §3.1); `InterchangeGenericAssetsPipeline` is the class behind `/Interchange/Pipelines/DefaultAssetsPipeline`.
5. §1.6 light units: project default stays `r.DefaultFeature.LightUnits=1` (candela, `render.md`); per-light "lumens" is a per-light override — not a conflict. **Sun decision:** one global DirectionalLight at rotator (pitch −51.1°, yaw −143.1°, roll 0) from `SUN_DIR`; the Reading Room's 19° west sun becomes a local RectLight/SpotLight outside the arched window.
6. Repo state the build agent must handle: `unreal/Pipeline/out/campus/*.glb`, `manifest.json`, `bl/library.py`, `unreal/Pipeline/blender/export_reading_room.py` are modified and **uncommitted**; `unreal/Pipeline/README.md` does not exist. The v2 export (§2.3), all-canvas dump (§3) and the Reading Room rebuild (§1.5) need the Playwright harness / Blender on the user's machine — until then the committed GLBs/PNGs are the inputs.
7. Rocketbox FBX: downloading from GitHub at the pinned commit needs network on the machine (~2 GB of avatars/textures); list it as a runbook step with the 37 avatar ids from `content.md` §1.9.
