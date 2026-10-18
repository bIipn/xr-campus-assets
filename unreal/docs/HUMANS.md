# People: MetaHumans

**Short answer:** build every person as a MetaHuman inside Unreal 5.8. MetaHuman Creator has been part of the editor since 5.6, and it is covered by the normal Unreal licence, which is free for this project. It gives you photoreal faces, rigged bodies, clothing and hair grooms. Version 5.8 adds a Python API for MetaHuman characters and MetaHuman Crowds. Full research: `docs/reference/humans.md`.

## Cast

| Who | Where | Rocketbox stand-in today | MetaHuman brief (from the web build's `look`) | Priority |
|---|---|---|---|---|
| **Margaret**, museum guide | Lobby lectern | bf02 | Older woman, light-medium skin (#c99c7a), silver hair in a bun, glasses; deep teal top (#274a52), charcoal skirt | M3 |
| **Rosa**, reference librarian | Reading Room desk | fa14 | Adult woman, medium skin (#a8775a), dark brown hair in a top bun; ochre top (#b07d2a), navy trousers | M3 |
| **Mr. Hale**, workshop teacher | School hall by Room 101 | ma05 | Adult man, medium skin (#b98a68), short brown hair; pale blue shirt (#a8c0d8), grey trousers | M3 |
| **Coach Rae**, recess coach | Recess Yard plaza | sf02 | Athletic woman, deep brown skin (#8d5a3b), short black hair; red sports top (#d2462f), navy trousers | M3 |
| **You** (first-person body) | Everywhere | sm04 | Neutral athletic body, head hidden for the owner; casual clothes | M5–M6 |
| **The keeper** | Soccer goal | sm02 | Athletic man, lime keeper kit, gloves | M6 |
| **Wax Hall reenactors** | 12 scenes, 38 castings | 33 Rocketbox ids | Generic people, never likenesses of real people; everyday clothes of the scene's years (2016–2025). One MetaHuman per role (38), each a different preset blend with its own skin, hair and colours, posed and held still on the stage like a wax figure | M4 |

The exact per-person looks (skin and hair colours, garments, glasses, beard) are in `WalkTheArchive/Data/Staff.json` (`LookNotes`) and `Pipeline/content/wax_scenes.json` (`cast`).

## How they are made (scripted, `Content/Python/wta_people`)

Every person, the 4 staff and all 38 Wax Hall reenactors, is its own generic MetaHuman. Each is designed in `Content/Python/wta_people/people.json`: an Epic preset as the start, a face blend toward a second preset so nobody is a stock face, then skin tone, eye colour, height and build, hair, brows and beard grooms, and outfit colours taken from the cast briefs above. `wta_people/build.py` turns a person into `/Game/WTA/Characters/<id>/MHC_<id>` and builds `BP_<id>` next to it.

1. **One-time setup.** In the Epic Games Launcher, open Library, then UE 5.8 Options, and tick **MetaHuman Creator Core Data**. It adds about 5 GB of presets, grooms, the default outfit, idle animations and the texture-synthesis model. Without it MetaHuman Creator can't do much.
2. **Look (local, no account).** Run `python Tools/common/people_batch.py --steps look --batch 3`. It starts the editor for three people at a time, because each MetaHuman being edited holds a few GB and a 16 GB PC runs out of memory after a handful. It writes the face, body, skin, eyes and wardrobe, saves, and closes the editor.
3. **Rig, textures, build (Epic's servers).** Run `python Tools/common/people_batch.py --steps rig,textures,save --batch 3`, then `--steps build,idle,save --batch 1`. The first cloud request opens an Epic sign-in page in the browser, and Ev approves it within 10 minutes. After that the editor signs in by itself. Rigs are joints-only, because a full rig with blend shapes needs at least 10 GB of free memory. Textures are 2K. The build uses the UE Optimized pipeline at Medium quality and takes about 3 minutes per person. On 5.8 it logs a few "Cannot break link" notices while it copies the face Control Rigs into `Common`. They are harmless, and the build step accepts them once `BP_<id>` exists. The `idle` step copies Epic's neutral stand idle to `Common/Anims/AS_WTA_StandIdle` and moves it onto the shared body skeleton (`Common/Female/Medium/NormalWeight/Body/metahuman_base_skel`). Built Blueprints face +Y, so the staff and wax-stage actors turn them by -90°.
4. **Into the game.** Run `python3 Pipeline/data/build_data.py`. It fills `Staff.json` with each staff member's `MetaHuman` path once `BP_<id>` exists, and it writes every wax stage's `Figures` (from the web cast). Then run `setup_project` with steps `data_tables`. Staff swap their placeholder for the MetaHuman and loop a standing idle. Each Wax Hall stage spawns its built reenactors, gives each one its own frame of the idle, and freezes them like wax figures.

The bridge into a running editor is `Tools/common/ue_exec.py` (Python Remote Execution, localhost only). `people_batch.py` turns it on for the editors it starts.

**Known limits (Oct 2026):** Core Data ships one outfit (T-shirt, shorts, bare feet), so everyone wears it in their own colours until better outfits are added from Fab as MetaHuman wardrobe items (`.mhpkg`). MetaHuman has no child bodies, so the web build's "kid" roles are young-looking teenagers about 148 cm tall. There are no glasses or caps in Core Data.

**Hardware:** Epic recommends an RTX 3070 / RX 6800 XT / M2 Ultra-class GPU with 8 GB VRAM and 32 GB RAM for MetaHuman work. A Mac can create MetaHumans, but some MetaHuman Animator solves and body capture are Windows-only.

**Licence:** free for this project. MetaHumans may also be used in other engines. Not allowed: using MetaHumans to train AI models.

## The repos you sent

| Repo | Verdict | Why |
|---|---|---|
| Blender | **Keep** | Already the Reading Room pipeline (`bl/`); also for cleanup and props |
| MediaPipe | Optional | Apache-2.0 webcam tracking. Unreal already does webcam face capture (MetaHuman Animator) and 5.8 adds markerless body capture |
| MakeHuman | Not needed | MetaHuman is better in every way; its rig doesn't match MetaHuman |
| MB-Lab | Not needed | Archived in 2024; generated models default to AGPL |
| PIFu / PIFuHD | Not needed | Static, unrigged meshes from one photo; PIFuHD is non-commercial (CC-BY-NC) |
| SMPL-X, MANO | Not needed, licence problem | Non-commercial research licences; MetaHuman's body and hands replace them |
| OpenPose | Not needed, licence problem | Non-commercial; Unreal has its own capture |
| instant-ngp, Animatable NeRF / NeuralBody | Not needed, licence problem | Research NeRFs, not animatable game characters; non-commercial terms |
| Filament | Not needed | A separate renderer; Unreal has its own |
| Microsoft Rocketbox (today) | Fallback only | MIT; keep for placeholders and animation retarget tests |
