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
| **Wax Hall reenactors** | 12 scenes, 38 castings | 33 Rocketbox ids | Generic people, never likenesses of real people; period-appropriate clothes per scene (2016–2025). About 14 base MetaHumans varied by outfit, hair and skin. Wax look = MetaHuman skin with less subsurface and a light clearcoat | M4 |

The exact per-person looks (skin and hair colours, garments, glasses, beard) are in `WalkTheArchive/Data/Staff.json` (`LookNotes`) and `Pipeline/content/wax_scenes.json` (`cast`).

## How to make them (Cowork or you, in the editor)

1. Enable the MetaHuman plugins (`Tools/common/configure_plugins.py --only metahuman` enables whatever MetaHuman plugins the engine has, then restart the editor). Creating characters needs your Epic account to be signed in, and some steps (conform, auto-rig, texture synthesis) use Epic's servers.
2. For each staff member: Content Browser → `/Game/WTA/Characters/<id>/` → right-click → MetaHuman → **MetaHuman Character** → start from the closest preset, blend presets, sculpt to the brief, choose an Outfit and a groom → **Assemble** at "Cinematic" quality for staff → this creates `BP_<id>`.
3. Put the Blueprint path in `WalkTheArchive/Data/Staff.json` → `MetaHuman` (for example `/Game/WTA/Characters/margaret/BP_margaret.BP_margaret_C`), then run `setup_project` with steps `data_tables`. The staff actor swaps its placeholder for the MetaHuman automatically.
4. Animation: idle and gestures from the free **Game Animation Sample Project** (Fab, motion matching), retargeted with the IK Retargeter; head and eye look-at in the Animation Blueprint. Talking: pre-bake the fixed answers with MetaHuman Animator's audio-driven facial animation (editor-only), and use runtime lip-sync (NVIDIA ACE or MetaHuman realtime audio) later if live answers are added.
5. Scripted variants for the Wax Hall: on 5.8 read the examples shipped with the engine at `Engine/Plugins/MetaHuman/MetaHumanCharacter/Content/Python/examples/` first, then script preset blends for the 14 base reenactors.

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
