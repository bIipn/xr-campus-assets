# Photoreal, animatable humans for the UE5 port of "Walk the Archive / XRLibraries Campus"

Research date: 2026-10-16. Scope: MetaHuman (creation, animation, clothing, performance, license, scripting), body animation stack, conversational NPC lip-sync, hand interaction, and a keep/drop verdict on the user's pasted list of open-source human repos.

Method note: in this container, direct fetches of dev.epicgames.com, metahuman.com, unrealengine.com, docs.nvidia.com and GitHub were refused by the egress proxy (403 CONNECT), so every claim below comes from web-search excerpts of those primary pages plus secondary coverage. Where only a secondary source exists, or where I could not confirm a name/number, it is marked **[unverified]**. Nothing below is an invented API, plugin, class or cvar name: every identifier in `code` was seen in an Epic/NVIDIA page excerpt or in a file in this repo.

---

## 0. Executive verdict

1. **Target Unreal Engine 5.8.x.** UE 5.8 shipped 17 June 2026 (State of Unreal, Chicago) and Epic says it is the last planned 5.x major (5.9 not ruled out). Hotfixes 5.8.1/5.8.2/5.8.3 exist. The MetaHuman Character **Python API requires 5.8+**, and MetaHuman Crowds (needed for the 12 reenactor scenes) is 5.8+. Do not target 5.6/5.7.
2. **MetaHuman replaces Rocketbox for every human in the project.** Since UE 5.6 (June 2025) MetaHuman Creator runs inside the editor, is covered by the ordinary Unreal Engine EULA (free under US$1M revenue, usable in any engine/DCC), and ships a parametric scanned-data body, presets, Mesh-to-MetaHuman (head 5.6, body 5.8), Outfit assets that auto-resize, and grooms. Rocketbox (MIT) stays only as a fallback or for reference; it is visually ~2010-era.
3. **Animation:** Game Animation Sample (GASP, Fab, free, UE-only but commercial OK; 5.7 update adds experimental Mover + ~400 new animations) for player/staff locomotion via motion matching; IK Retargeter with Auto Retarget Chains / Auto Align for Mixamo or Rocketbox clips; Control Rig Full Body IK (`FRigUnit_PBIK`) for hands-on benches and VR arms. Keep `CharacterMovementComponent`; **Mover is still Experimental** in 5.7/5.8.
4. **Talking staff:** MetaHuman's own audio-driven facial animation is **editor-only** (offline `MetaHuman Performance` asset → baked AnimSequence; realtime via MetaHuman Audio Live Link source). For runtime, dynamic speech on Windows+NVIDIA, use NVIDIA ACE/Audio2Face-3D (UE plugin MIT; models under NVIDIA Open Model License, commercial OK; supported UE 5.5/5.6 only as of ACE plugin 2.5 — 5.7/5.8 **unconfirmed**). Practical plan: pre-bake the scripted answer bank offline with MetaHuman Animator; add ACE only on NVIDIA machines.
5. **Hands:** VR Template `GrabComponent` (Free/Snap/Custom) + Epic's `OpenXRHandTracking` plugin (`FXRHandTrackingState`, 5.5+) + Control Rig FBIK. On Quest, Meta recommends its Interaction SDK.
6. **Pasted repo list:** keep Blender, MediaPipe, Filament-as-reference-only; everything else is either **not needed** in a UE5 pipeline (MakeHuman, MB-Lab, PIFu/PIFuHD, instant-ngp, Animatable NeRF/NeuralBody) or a **license problem** for a public/commercial project (SMPL-X, MANO, OpenPose, PIFuHD CC-BY-NC, instant-ngp NVIDIA-NC, MB-Lab AGPL outputs). Details in section 6.

---

## 1. Engine/version landscape (as of Oct 2026)

| Version | Date | Human-relevant headline |
|---|---|---|
| UE 5.6 | 3 June 2025 | MetaHuman leaves early access; **MetaHuman Creator inside the editor**; parametric body (blend/sculpt from scans); Outfit asset; MetaHuman Animator realtime from **mono webcam/phone and audio**; licensing moved to UE EULA; MetaHumans allowed in other engines/DCCs. |
| UE 5.7 | Nov 2025 | GASP updated with **Mover (Experimental)** + 400 anims; MetaHuman body conform accepts any pose A-pose→T-pose, UV-space vertex correspondence; Blueprint interface for MetaHuman Live Link realtime animation; Calibration Diagnostics plugin (experimental). |
| UE 5.8 | 17 June 2026 | **MetaHuman Crowd plugin / MetaHuman Collections (Experimental, Mass-compatible, tens→thousands)**; Mesh-to-MetaHuman conforms **head + body** simultaneously, any topology; **single-camera markerless body capture (Experimental, Windows only, Fab plugin)**; new realtime audio model (procedural blinks, emotion detection); unbaked textures/materials; **MetaHuman Character Python API**; OpenRigLogic (RigLogic + DNA libs) open-sourced under MIT; MegaLights, Live Link Hub production-ready; Lumen Lite; built-in MCP server plugin. Last planned UE5 release. |

Sources: Epic 5.6 news/forum post; CG Channel 5.6; Epic 5.7 GASP tech blog; MetaHuman 5.7 release notes; MetaHuman 5.8 release notes; GameFromScratch / 80.lv / WN Hub 5.8 coverage (see §9).

---

## 2. MetaHuman

### 2.1 Where Creator lives and what it needs

- **In-editor since UE 5.6.** "Creating a MetaHuman Character asset requires an Unreal Engine 5.6 (or later) project", an **Epic Games account**, the **MetaHuman Core Data** additional content installed, and the **MetaHuman Creator plugin** enabled (Epic docs "Creating a character").
- **Internet:** Epic's Mesh-to-MetaHuman page says the identity solve "submit[s] the template mesh to the backend"; a secondary guide says autorigging and texture synthesis also run on Epic's servers while the editing session is local **[unverified for 5.8]**. Plan on: account + internet for conform/autorig/texture-synthesis steps; everything else offline.
- **Hardware (Epic "MetaHuman hardware requirements"):** for MetaHuman Creator and MetaHuman Animator Epic recommends ≥16 physical high-performance cores, 32 GB RAM, and at least **NVIDIA RTX 3070 / AMD RX 6800 XT / Apple M2 Ultra with 8 GB VRAM**; on Windows a DirectX 12 card with default RHI = DX12. Memory can exceed 32 GB when assembling characters with large textures or with Virtual Textures enabled.
- **Platform matrix (same page + 5.8 notes):** Creator: Windows and macOS (Apple silicon listed). Animator: Windows has the full workflow; realtime mono-video/audio is "only supported on Windows and macOS"; Identity/Performance asset creation is disabled on Mac and Linux (5.7 note); Linux realtime only via Live Link Face; markerless body capture **Windows only**. **Implication for Cowork on an unknown Mac/PC:** a Mac can author MetaHumans and do realtime previews; offline Performance solves and body capture need a Windows box.

### 2.2 How to create MetaHumans

| Route | Status | Notes |
|---|---|---|
| **Presets + blending** | Shipping (5.6+) | Preset Library ships with Epic presets; initialise from one preset or blend between a selection; face and body both blend (Epic "MetaHuman Presets" page). |
| **Parametric body** | Shipping (5.6+) | 5.6 replaced the 18 fixed body types with a body built "on scanned data that you can sculpt and blend between"; sliders (height, chest, waist, leg length etc. **[slider names from secondary source]**). |
| **Sculpting** | Shipping | Face landmark manipulation and body sculpting in the Character editor; also exposed to Python (see §2.7). |
| **Mesh to MetaHuman (scan)** | Shipping; body conform 5.6→much improved 5.8 | Build a MetaHuman Identity from a static/skeletal mesh of **any topology**; create/track a Neutral Pose; run Identity Solve; backend returns a template; in 5.6+ you finish with **Conform from Identity** in the MetaHuman Character editor (no web Creator). 5.7: any pose between A- and T-pose. 5.8: head and body conform at once, output adopts MetaHuman topology + rig. Known 5.8 issue: conformed height can drift (forum). Scans: Epic's RealityScan app or RealityCapture; even neutral lighting, hair back, no facial hair/accessories (university guide, secondary). |
| **From photos** | **No official single-photo route.** | Epic's closest is MetaHuman Animator identity from three frames of video **plus depth** (iPhone TrueDepth or stereo HMC). Third-party: KeenTools FaceBuilder (3–8 photos, paid), Fab "AI MetaHuman generator" listings, free Blender add-on MetahumanModeler (approximate likeness). **Not needed for this project**: reenactors are generic people, never likenesses. |
| **From video performance** | Shipping | MetaHuman Animator can create the identity from the capture footage used for animation (iPhone 12+ / stereo HMC). |

### 2.3 MetaHuman Animator inputs (facial + body)

| Input | Realtime | Offline (high fidelity) | Requirements / notes |
|---|---|---|---|
| iPhone/iPad TrueDepth via **Live Link Face** app | Yes (iPhone 12+, 16/16 Pro recommended; iPad 8th gen+) | Yes (depth data; needs neutral take for Identity) | Depth-based animation not on Android; Android realtime limited to certain Qualcomm chipsets. |
| Stereo head-mounted camera (HMC) | — | Yes | Needs calibration take with calibration board. |
| **Mono video / webcam / most smartphones** | Yes since 5.6 (MetaHuman Live Link plugin → Live Link window → MetaHuman Video Source + Subject → select subject on character BP) | Yes: ingest via **Capture Manager in Live Link Hub** with Mono Video / Live Link Face / Take Archive device | Windows + macOS only. |
| **Audio** | Yes: "MetaHuman Audio Live Link Source"; realtime solver produces no head motion; 5.8 model adds procedural blinks and emotion detection when none specified | Yes: SoundWave asset → **MetaHuman Performance** asset, input type = Audio → Process; 5.6 added generated head movement and optional blinks | Offline solve ≠ realtime solve (Epic docs). |
| **Body, single camera (markerless)** | — | Yes, 5.8 **Experimental**; batch processed locally | Requires MetaHuman Animator plugin + **Markerless Motion Capture plugin from Fab**; **Windows only**; input = one video camera or Live Link Face using a non-TrueDepth camera. |

**Runtime caveat (important for "staff that talk"):** the MetaHuman 5.8 release notes describe realtime MetaHuman Animator as an **"Editor-only solution; not a runtime or player-facing feature."** Forum reports (UE 5.8.1) show packaged builds crashing on `Create Video Subject` because an editor-only module's struct is exposed through a runtime Blueprint function, and `MetaHumanLiveLink.uplugin` lacking proper `SupportedTargetPlatforms`. Treat all of MetaHuman Animator as an **authoring** tool: bake AnimSequences, ship those.

### 2.4 Clothing, outfits, grooms

- **Outfit asset** (5.6+): UE "Outfit asset that resizes automatically to fit characters' body shapes." Engine API: `UChaosOutfitAsset` (plugin `ChaosOutfitAssetEngine`, marked **Experimental**), `UChaosOutfit`, `FChaosOutfitPiece`, `FChaosSizedOutfitSource` (input for a single sized outfit). The 5.6 Chaos Cloth "Cloth Panel Editor" was **Beta**, adding Outfit Asset resizing/refitting, cloth-to-cloth constraints and simulation morph targets. 5.8 brought Chaos Cloth/Hair/Flesh performance and simulation updates (secondary).
- **Plugins to enable for parametric wardrobe:** MetaHuman Creator plugin + **Chaos Cloth Asset** + **Chaos Cloth Asset Editor** (Epic "Parametric asset setup for MetaHuman", UE 5.6+; editor restart required).
- **Sources of clothes:** Fab wardrobe items; your own ("Tailoring your own wardrobe items" doc); Marvelous Designer 2025.2 USD garments → Outfit asset (UE 5.6+; **not** 5.5). Vendor packs on Fab list "UE 5.8 or higher" Chaos Cloth setups.
- **Grooms:** Groom + Groom Binding assets from Fab or authored in UE / Maya / Houdini exporters; strands at LOD0 (50 000 strands listed), cards/meshes at lower LODs. Hair strands are costly (ray-traced/path-traced note in Epic docs).
- For 12 historical scenes you will need period costume: Fab (check per-listing license) or Marvelous Designer. Budget this; it is the biggest art cost in the human pipeline.

### 2.5 LODs and per-MetaHuman cost

Epic "Platform support and LOD specifications" and "Controlling MetaHuman LODs":

| Part | LODs | Vertices (LOD0 → last) |
|---|---|---|
| Head (face) | 8 | 24 000 → 12 000 → 6 000 → 2 500 → 1 300 → 560 → 270 → 130 |
| Body (and feet/legs/torso) | 4 | 30 500 → 7 600 → 3 350 → 1 507 |
| Hair strands | — | 50 000 strands at LOD0; cards/meshes below |

- Everything above the neck has 8 LODs, below the neck 4: "for every two LOD quality changes above the neck, only one happens below it." `Num LODs` default 8; `Forced LOD` 0 = best. Epic warns forcing LOD 0/1 on many MetaHumans (a crowd) hurts performance.
- Cost levers (MetaHuman Component doc): **body correctives run only at LOD0** by default (disable = first lever); **facial animation threshold defaults to LOD 2** (lower it so only LOD0/1 animate faces); neck settings have the biggest impact. `FMetaHumanLODProperties` (plugin `MetaHumanDefaultEditorPipeline`) is the assembly-time LOD config struct.
- No official ms/VRAM-per-character number exists. A course site's "500 MB–1 GB VRAM per LOD0 MetaHuman" and "~260K tris LOD0" are **[unverified]** and do not match Epic's vertex data; measure in-editor (Statistics panel, `stat gpu`/`stat anim`).
- For ~40 humans: run **6–8 "hero" MetaHumans** (staff you talk to) at full quality near the camera, and build the **12 reenactor scenes (and background visitors) as MetaHuman Collections / Crowd** (§3.7) or with facial animation limited to LOD0-1. Pair with the **Animation Budget Allocator** plugin (fixed ms budget on the game thread, significance-based throttling/interpolation, leader-pose).

### 2.6 License (MetaHuman)

- **5.6 and later: the Unreal Engine EULA applies.** The separate MetaHuman Creator EULA "continues to apply to users of the cloud-based version of MetaHuman Creator on Unreal Engine 5.5 or any earlier version." (metahuman.com/license; unrealengine.com/eula/mhc.)
- "MetaHuman is included as part of your standard Unreal Engine license" and "MetaHumans can be used with any engine or creative software" (metahuman.com). Trade press (CG Channel, Digital Production, June 2025): usable in Unity/Godot/Maya/Houdini/Blender incl. commercial projects; Epic treats MetaHuman characters/animation as **"Non-Engine Products"** so rendering them in other engines triggers no royalty **[wording seen only via a Reddit quote; confirm in live EULA]**.
- **Money:** UE is free for anyone under US$1M. Games: 5 % royalty above US$1M **lifetime gross per product**. Non-game use (linear, visualization, "immersive experiences") by companies over US$1M **annual** revenue: **US$1,850 per seat per year** (Epic pricing, March 2024; includes Twinmotion + RealityCapture). A free public museum/library concept project is well inside the free tier.
- **Restrictions:** EULA change-log update 20 bans using the Engine as training/prompt input for generative AI; **update 21 adds a MetaHuman-specific ban** on using MetaHuman characters/animation curves (or renders that replicate them) to build or train AI datasets/models. No "likeness" problem here because reenactors are generic, but note MetaHuman's own terms do not grant rights to any real person's likeness you scan.
- **Open components:** **OpenRigLogic** (github.com/EpicGames/openriglogic): DNA read/write + RigLogic realtime rig evaluation with Python bindings, **MIT** (MetaHuman DevKit docs; 5.8).
- **Verdict:** free public concept project — fine; later commercial use — fine under the UE EULA tiers; other engines — allowed; AI training on MetaHumans — prohibited.

### 2.7 Scripting MetaHuman creation (Python)

- Epic "MetaHuman Creator Python scripting in Unreal Engine": the **MetaHuman Character Python API** covers "create, edit, conform, sculpt, assemble, and export MetaHuman Character assets from scripts and Editor Utility Blueprints." **Prerequisites: UE 5.8 or later, MetaHuman Character plugin, Python scripting enabled.**
- Two surfaces: the `MetaHumanCharacter` asset (skin, eyes, makeup, viewport settings settable without opening the editor) and `unreal.MetaHumanCharacterEditorSubsystem` (required for face-landmark manipulation, body sculpting, conform, texture and auto-rig requests, assembly).
- Workflow and confirmed method names: `try_add_object_to_edit(character)` → edit → commit each change → `remove_object_from_edit(character)`.
- Reference scripts ship at `Engine/Plugins/MetaHuman/MetaHumanCharacter/Content/Python/` (`examples/`, e.g. `examples/example_conform_head.py`, plus broader `test_*.py`). **Read these on the user's machine before writing any automation; I could not retrieve the texture-synthesis/auto-rig request signatures.**
- Known 5.8.0 gap: `UMetaHumanCharacterEditorSubsystem::RemoveBodyRig` not exposed to Python (Epic targeting 5.8.2 hotfix, not guaranteed).
- Also exists: `IMetaHumanImportAutomationHandle` in `MetaHumanSDKEditor` (import automation) — purpose not confirmed beyond its name.
- Backend-dependent steps (conform/autorig/texture synthesis) still need the Epic account + internet from a script.
- **Plan for Cowork:** a Python editor script that loads N presets, blends/randomises body and face within ranges, assigns outfits/grooms, requests autorig + textures, assembles, and saves `MHC_<role>_<n>` assets; then a second script builds a MetaHuman Collection for the crowd scenes. Keep the staff hero characters hand-tuned.

---

## 3. Body animation stack

### 3.1 Game Animation Sample Project (GASP)
- Epic sample, first shipped with UE 5.4 (June 2024, 500+ animations), updated each release; **5.7 update adds the Mover plugin (Experimental) and ~400 new animations**; download on **Fab**, free. Lets you "import your own character and migrate its animation assets and systems into your own project."
- Motion matching is built on Epic's Pose Search plugin (not re-verified this session; it is what the GASP docs describe).
- **License:** CG Channel (June 2024): "only licensed for use with Unreal Engine, but can be used in commercial projects"; Epic sample content is governed by the Epic Content License / Fab terms — **confirm on the Fab listing**. Fine for this project.
- Use: player locomotion (first/third person) and staff/visitor NPC locomotion.

### 3.2 Mover
- Epic docs: "modular actor movement with rollback networking using the Network Prediction Plugin or Chaos' Networked Physics"; **Experimental, APIs/data formats subject to change**; intended eventually to replace `CharacterMovementComponent`. Enable `Mover` + `Mover Examples`, set Network Prediction "Preferred Ticking Policy" = Fixed; README at `Engine/Plugins/Experimental/Mover/`. 5.8 forum posts: still Experimental, "steps toward Beta".
- **Recommendation:** stay on `CharacterMovementComponent` for the campus (single-player walkable, VR). Revisit when Mover is Beta/production.

### 3.3 Control Rig and Full Body IK
- Epic "Control Rig Full Body IK": node built on a **Position Based IK** solver (`FRigUnit_PBIK`, plugin `PBIK`), per-bone settings, preferred angles, squash/stretch; set root (pelvis), add one effector per control (head, hands, feet) with Bone + Transform from `Get Transform`; effector fields `PositionAlpha` (0–1, default 1), `RotationAlpha`, `PullChainAlpha`, `ChainDepth`; `FPBIKEffector`/`FEffectorSettings`. Use for: reaching to bench objects, holding tools, VR arm solving from head+hand targets.

### 3.4 IK Retargeter (Rocketbox / Mixamo → MetaHuman)
- Epic "Auto Retargeting": retarget directly from the Content Browser by selecting two Animation Sequences on different skeletons; **Auto Retarget Chains** (IK Rig editor) matches bone chains to templates by bone names (exact names not required); **Auto Align** (IK Retargeter editor) aligns retarget poses per skeleton or per bone; Python `IKRetargeterController` and `BatchRetargetSettings` exist. Batch auto-generation is "limited to common, predefined skeleton types."
- MetaHuman: target IK Rig ships pre-built; Epic "Create a custom IK Retargeter" doc for assembled MetaHumans.
- **Rocketbox** uses 3ds Max Biped naming (`Bip01_Pelvis`, `Bip01_Spine..Spine2`, `Bip01_L_UpperArm`, `Bip01_L_Finger0..42`, facial `Bip01_MJaw` etc. — see `hk/names.json`, 80 bones). Auto chains may partially match; expect to hand-map chains and set the retarget pose once. No published Rocketbox→UE guide found.
- **Mixamo:** third-party "Mixamo Animation Retargeting 2" (Fab, v2.3.0 for UE 5.6; auto-builds IK Rig/Retargeter incl. a MetaHuman base skeleton) or do it manually with the above. Mixamo assets are under Adobe's terms (royalty-free in projects, no standalone redistribution) **[not re-verified this session]**.

### 3.5 ML Deformer
- Epic "ML Deformer Framework": plugin + models (**Neural Morph Model** — separate plugin, CPU network outputs morph weights, local/global modes; **Nearest Neighbor Model**); trains on deformation data generated externally (Maya/Houdini). High effort, no MetaHuman-specific 5.6/5.7 doc found. **Not needed for v1.**

### 3.6 Chaos Cloth
- See §2.4. Cloth Panel Editor Beta (5.6), Outfit asset Experimental, 5.8 perf/sim updates. Use Outfit assets for staff; for crowds rely on Collections' baked clothing.

### 3.7 Crowds (12 reenactor scenes, background visitors)
- **MetaHuman Crowd plugin / MetaHuman Collections** (5.8, **Experimental**, "still in active development"): you supply source MetaHumans, hairstyles, clothing; the system builds optimised versions, spawns, manages LOD and animates; **Mass-compatible**, tens→thousands; swaps between full Actors and **Instanced Skeletal Meshes** by camera distance; Nanite or dynamic LOD; compose collections by hand or with Blueprints; runs on all UE target platforms (Epic claims hundreds on mobile, thousands on high-end — marketing figures). Known forum issues: untextured white heads in generated collections, head/body misalignment with custom characters.
- **Animation Budget Allocator** (Epic doc): per-platform ms budget, significance ranking, throttling/interpolation, leader-pose. Enable plugin, restart.
- Mass AI / MassCrowd / ZoneGraph are the underlying systems; third-party MIT plugin "MaaassParticle" (Fab, 5.6) shows an AnimToTexture + Mass path if Collections prove too immature.
- For wax-figure reenactors that mostly hold poses, a cheap alternative is forced-LOD MetaHumans with facial animation disabled above LOD0 — decide after profiling.

---

## 4. Conversational NPCs (lip sync from audio)

### 4.1 Epic-native
- **Offline:** SoundWave → `MetaHuman Performance` asset (input type Audio) → Process → export AnimSequence. 5.6+ adds head motion generation and optional blinks; many solve options. **This is the right tool for a scripted answer bank** (pre-generate TTS lines, solve once, ship AnimSequences).
- **Realtime:** MetaHuman Audio Live Link Source (MetaHuman Live Link plugin), 5.8 model with blinks/emotion. **Editor-only per Epic's 5.8 notes**; packaged-build crashes reported. Not a shipping solution for dynamic LLM answers.
- Blueprint interface for Live Link realtime animation added in 5.7 (editor context).

### 4.2 NVIDIA ACE / Audio2Face-3D
- **ACE Unreal plugin 2.5** (docs.nvidia.com): adds UE 5.6, drops 5.4; officially tested for **UE 5.5 and 5.6 on Win64 and Linux**; other versions "may build but unsupported." **No 2.6 / UE 5.7 / 5.8 support found.** 2.4 introduced six plugins that run Audio2Face-3D **locally** (`NvAudio2FaceClaire/James/Mark` variants); local inference needs **NVIDIA Ampere/Ada/Blackwell GPU on Windows, ~2.9–4.4 GiB VRAM, driver ≥ 551.78**; or remote via NVCF (`https://grpc.nvcf.nvidia.com:443`). Output: blendshape coefficients via Live Link to MetaHuman (ARKit-style set **[set not confirmed]**). Also includes a local LLM (GPT) component.
- **Audio2Face-3D open-sourced (Sept 2025):** SDK (C++/Python) **MIT**; Maya and **Unreal Engine 5 plugin MIT (UE 5.4–5.6 per third-party listing)**; training framework Apache-2.0; pretrained models (`nvidia/Audio2Face-3D-v3.0`, v2.3 Mark etc. on Hugging Face) under the **NVIDIA Open Model License** — which NVIDIA states permits commercial use (latest text: NVIDIA Open Model Agreement, 2 April 2026); the NIM container is under NVIDIA's commercial AI product terms.
- **Constraint:** NVIDIA-GPU only, Windows/Linux. **On a Mac this path does not exist.**

### 4.3 Recommended architecture for staff dialogue
1. Text: Claude (or any LLM) answers from the archive's knowledge base.
2. Voice: TTS service of choice.
3. Face: (a) **scripted/common answers** → offline MetaHuman Performance solve, shipped as AnimSequences keyed by answer ID; (b) **dynamic answers on Windows+NVIDIA** → ACE/Audio2Face-3D local plugin driving the MetaHuman via Live Link preset applied at runtime (NVIDIA's own docs note the Live Link Source window is unavailable in packaged builds; save a `LiveLinkPreset` and apply it at runtime); (c) **fallback everywhere** → viseme/phoneme timings from the TTS provider mapped to MetaHuman facial curves (ARKit-compatible curve names on the MetaHuman face rig; OpenRigLogic MIT documents the rig) — this needs a small custom AnimBP/curve-injection layer and is the only portable runtime route. Community tutorials ("MetaHuman AI lip sync with local TTS in UE 5.6+") use third-party "Runtime" plugins for exactly this **[quality unverified]**.

---

## 5. Hand interaction (desktop + VR)

- **VR Template (Epic doc "VR Template in Unreal Engine")**: `GrabComponent` Blueprint with `Grab Type` enum **Free** (keeps relative transform), **Snap** (object positioned/oriented to the controller, e.g. pistol), **Custom** (your logic via `OnGrabbed`/`OnDropped` events, `bIsHeld`, examples: two-handed, dials, levers); `OnGrabHaptic Effect` variable. Add the component to any actor to make it grabbable — this maps 1:1 to the workshop benches.
- **OpenXR hand tracking:** Epic plugin **`OpenXRHandTracking`** (module `IOpenXRHandTrackingModule`, settings `UOpenXRHandTrackingSettings` with `bUseMoreSpecificMotionSourceNames` → motion sources `[Left|Right][Keypoint]`, `bSupportLegacyControllerMotionSources`). Data via `Get Motion Controller Data` (`HandKeyPositions`/`HandKeyRotations`, indexed by `EHandKeypoint`), and from **UE 5.5** the split structs `FXRMotionControllerState` / `FXRHandTrackingState` (`GetHandTrackingState()`), replacing the combined `FXRMotionControllerData`. Running two hand-tracking providers at once returns whichever is found first (SenseGlove doc) — enable only one. Epic's older "Making Interactive XR Experiences" page still says OpenXR hand tracking is unsupported and routes Quest through the Oculus plugin — **stale**; Meta's current (Mar 2026) guidance is to use the **Meta XR Interaction SDK** on Quest, warning that custom interactions make store approval harder.
- **Arms/body for the player:** Control Rig FBIK (§3.3) with head + two hand effectors; in VR the MetaHuman body (or arms only) solved from HMD + hand poses; on desktop a first-person MetaHuman with Two-Bone/FBIK reach to bench targets. Grab = `GrabComponent` (Snap for tools so the hand pose is authored once per tool).

---

## 6. Verdict on the pasted open-source list

| Repo | License (as found) | Verdict for the UE5 project | Where it could fit |
|---|---|---|---|
| **MakeHuman** | App AGPL-3.0; since Sept 2020 assets default CC0 and **exports are CC0** (official FAQ) | **Not needed** — MetaHuman is better in every axis; rig/topology isn't MetaHuman-compatible | Could produce a scan-free custom body mesh for Mesh-to-MetaHuman, but presets/sculpt already cover that |
| **MB-Lab** | GPL-3 + AGPL-3 code; **generated models default AGPL-3** (needs custom-character workaround for closed projects); project discontinued, repo archived Jul 2024 | **Not needed / license problem** (AGPL outputs) | None |
| **Blender** | GPL-2.0-or-later; your outputs are your own copyright (Blender FAQ) | **Keep** — already your bake pipeline (`bl/*.py`); use for scan cleanup, outfit prep, FBX/USD/glTF fixes | Mesh cleanup before Mesh-to-MetaHuman; prop/costume modelling |
| **PIFu** | MIT (original PIFu repo) | Not needed | — |
| **PIFuHD** | **CC-BY-NC 4.0** (code + `pifuhd.pt`) | **License problem for anything commercial; not needed** anyway (single-image static mesh, no rig) | At most: offline research scan → Mesh-to-MetaHuman; not worth it |
| **SMPL-X** | Non-commercial research/education/artistic only; commercial via Meshcapade (sales@meshcapade.com; datasets €4 000–€18 900) | **License problem**; also not needed — MetaHuman's parametric body replaces it | None unless you buy a Meshcapade commercial license |
| **MANO** | Same MPI non-commercial license; commercial via ps-licensing@tue.mpg.de / Meshcapade (conflicting pointers) | **License problem**; MetaHuman hands + OpenXR hand tracking replace it | None |
| **MediaPipe** | Apache-2.0 | **Keep as optional tool** (webcam hand/face/pose landmarks) — but UE already covers webcam face via MetaHuman Animator mono video and body via 5.8 markerless capture | Only for browser/companion-app experiments or custom pose capture; not in the UE runtime |
| **OpenPose** | CMU "academic or non-profit noncommercial research use only"; commercial license reportedly US$25k/yr **[unverified]**, sports carve-out | **License problem; not needed** | None |
| **instant-ngp** | NVIDIA Source Code License (non-commercial per third-party summary; commercial "needs to be licensed") | **Not needed** (NeRF, not an animatable asset); **license problem** for commercial | None; for photoreal rooms you already bake PBR; UE can import Gaussian splats via third-party plugins if ever needed |
| **Animatable NeRF / NeuralBody (zju3dv)** | GitHub shows license "other"; ZJU-MoCap data research-only; builds on SMPL (non-commercial) | **Not needed; license problem** (research code, depends on SMPL) | None |
| **Filament** | Apache-2.0 | **Not needed** in UE (UE has its own PBR renderer); keep only as a PBR reference | Reference reading for material authoring |
| **Microsoft Rocketbox** (current web build) | **MIT** (`hk/ROCKETBOX-LICENSE.txt`) | **Replace with MetaHumans**; keep as fallback/placeholder and for retargeting tests | Rocketbox animations can be retargeted to MetaHumans via IK Retargeter (hand-mapped Bip01 chains) |

---

## 7. Human pipeline proposal for this project (UE 5.8)

| Group | Count | Build | Animation | Face |
|---|---|---|---|---|
| Virtual staff (librarian, docent, workshop instructors) | ~6–8 | Hand-tuned MetaHumans from presets (Python-assisted), Outfit assets, strand grooms, full 8 LODs | GASP motion matching + Control Rig FBIK for gestures/handing objects | Offline MetaHuman Performance solves for the answer bank; optional ACE A2F for live answers on NVIDIA PCs |
| Wax-hall reenactors (12 scenes) | ~20–25 | Scripted preset blends (generic, no likenesses), period Outfits, baked clothing | Mostly held poses / short loops; MetaHuman Collections (Crowd) or forced-LOD actors after profiling | Face anim off above LOD0 |
| Goalkeeper | 1 | MetaHuman athletic body | Mixamo/Rocketbox keeper clips retargeted via IK Retargeter; GASP for locomotion | Minimal |
| Player arms/body | 1 | MetaHuman body (first-person arms) | Control Rig FBIK from camera/hand targets; VR: OpenXRHandTracking + GrabComponent | n/a |
| Background visitors | 0–100s | MetaHuman Collections | Mass crowd | n/a |

Hardware guidance for Cowork: Windows + NVIDIA RTX (Ampere or newer, ≥8 GB) unlocks everything (Creator, Animator offline + body capture, ACE). Apple-silicon Mac: Creator + realtime previews only; no Performance-asset solves, no body capture, no ACE.

---

## 8. Open points / unverified items

- Exact Python signatures for MetaHuman texture-synthesis / auto-rig / assembly requests (read shipped `test_*.py`).
- Whether MetaHuman Creator's backend steps (autorig, texture synthesis) are still cloud-only in 5.8 (secondary source only).
- ACE plugin support for UE 5.7/5.8; Audio2Face-3D open-source UE plugin version range (listed 5.4–5.6 by a third party).
- Precise MetaHuman "Non-Engine Product" and AI-training clause wording in the live UE EULA (seen only via change-log summary and third-party quotes).
- GASP Fab listing license text (CG Channel summary only).
- NeuralBody / Animatable NeRF LICENSE file text.
- Mixamo current terms.

---

## 9. Sources

Epic / MetaHuman (primary)
- UE 5.6 release: https://forums.unrealengine.com/t/unreal-engine-5-6-released/2538952/1 ; https://www.unrealengine.com/news/unreal-engine-5-6-is-now-available
- MetaHuman 5.6 announcement: https://metahuman.com/news/metahuman-leaves-early-access-with-a-feature-packed-new-release
- MetaHuman 5.7 release notes: https://dev.epicgames.com/documentation/metahuman/metahuman-5-7-release-notes ; https://www.metahuman.com/releases/metahuman-5-7-is-now-available
- MetaHuman 5.8 release notes: https://dev.epicgames.com/documentation/metahuman/metahuman-5-8-release-notes-in-unreal-engine ; https://www.metahuman.com/news/metahuman-5-8-is-now-available
- UE 5.8 release notes: https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes
- MetaHuman license: https://www.metahuman.com/en-US/license ; MHC EULA: https://www.unrealengine.com/eula/mhc ; UE EULA change log: https://www.unrealengine.com/en-US/eula-change-log/unreal ; Unreal FAQ: https://gateway.unrealengine.com/en-US/faq
- Creating a character: https://dev.epicgames.com/documentation/en-us/metahuman/creating-a-character ; Presets: https://dev.epicgames.com/documentation/metahuman/metahuman-presets-in-unreal-engine ; From mesh: https://dev.epicgames.com/documentation/en-us/metahuman/from-mesh ; Body conform examples: https://dev.epicgames.com/documentation/metahuman/body-conform-examples
- Hardware requirements: https://dev.epicgames.com/documentation/metahuman/metahuman-hardware-requirements-in-unreal-engine
- MetaHuman Animator: https://dev.epicgames.com/documentation/en-us/metahuman/metahuman-animator-in-unreal-engine ; audio-driven: https://dev.epicgames.com/documentation/en-us/metahuman/audio-driven-animation ; mono video: https://dev.epicgames.com/documentation/metahuman/metahuman-animation-from-mono-video-capture-in-unreal-engine ; capture devices: https://dev.epicgames.com/documentation/metahuman/metahuman-animator-capture-device-requirements ; realtime via Live Link: https://dev.epicgames.com/documentation/metahuman/realtime-animation-using-live-link
- Python scripting: https://dev.epicgames.com/documentation/metahuman/metahuman-creator-python-scripting-in-unreal-engine ; https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MetaHumanCharacterEditorSubsystem ; forum (RemoveBodyRig): https://forums.unrealengine.com/t/metahuman-python-api-add-ability-to-edit-metahuman-creator-assets-in-place/2763639
- LODs: https://dev.epicgames.com/documentation/metahuman/platform-support-and-lod-specifications-for-metahumans ; https://dev.epicgames.com/documentation/metahuman/controlling-metahuman-levels-of-detail-lods-in-unreal-engine ; MetaHuman Component: https://dev.epicgames.com/documentation/metahuman/the-metahuman-component-for-unreal-engine
- Wardrobe/outfits: https://dev.epicgames.com/documentation/metahuman/tailoring-your-own-wardrobe-items ; https://dev.epicgames.com/documentation/metahuman/parametric-asset-setup-for-metahuman ; Chaos Outfit API: https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/ChaosOutfitAssetEngine/UChaosOutfitAsset ; Chaos Cloth 5.6 tutorial: https://forums.unrealengine.com/t/2555686 ; Marvelous Designer → MetaHuman: https://support.marvelousdesigner.com/hc/en-us/articles/52699135975705
- Crowds: https://dev.epicgames.com/documentation/metahuman/metahuman-crowds-in-unreal-engine ; Animation Budget Allocator: https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-budget-allocator-in-unreal-engine ; crowd issue threads: https://forums.unrealengine.com/t/metahuman-crowd-collection-generates-white-untextured-heads/2745480
- GASP: https://dev.epicgames.com/documentation/en-us/unreal-engine/game-animation-sample-project-in-unreal-engine ; 5.7 update: https://www.unrealengine.com/en-US/tech-blog/explore-the-updates-to-the-game-animation-sample-project-in-ue-5-7
- Mover: https://dev.epicgames.com/documentation/en-us/unreal-engine/mover-in-unreal-engine ; https://dev.epicgames.com/documentation/unreal-engine/mover-examples-in-unreal-engine
- Full Body IK: https://dev.epicgames.com/documentation/en-us/unreal-engine/control-rig-full-body-ik-in-unreal-engine ; https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/PBIK/FRigUnit_PBIK
- Auto retargeting: https://dev.epicgames.com/documentation/en-us/unreal-engine/auto-retargeting-in-unreal-engine ; https://dev.epicgames.com/documentation/unreal-engine/ik-rig-animation-retargeting-in-unreal-engine ; MetaHuman custom IK Retargeter: https://dev.epicgames.com/documentation/metahuman/create-a-custom-ik-retargeter ; Python: https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/IKRetargeterController
- ML Deformer: https://dev.epicgames.com/documentation/en-us/unreal-engine/ml-deformer-framework-in-unreal-engine ; https://dev.epicgames.com/documentation/en-us/unreal-engine/how-to-use-the-machine-learning-deformer-in-unreal-engine
- VR Template: https://dev.epicgames.com/documentation/unreal-engine/vr-template-in-unreal-engine ; OpenXRHandTracking API: https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/OpenXRHandTracking/IOpenXRHandTrackingModule ; https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/OpenXRHandTracking/UOpenXRHandTrackingSettings ; (stale) XR guide: https://dev.epicgames.com/documentation/unreal-engine/making-interactive-xr-experiences-in-unreal-engine
- OpenRigLogic: https://github.com/EpicGames/openriglogic ; DevKit: https://dev.epicgames.com/documentation/metahuman/metahuman-devkit-in-unreal-engine
- Packaged-build Live Link issues: https://forums.unrealengine.com/t/metahuman-live-link-create-video-subject-crashes-packaged-windows-build-when-using-monocular-animation-pipeline-models/2745310 ; https://forums.unrealengine.com/t/we-think-metahumanlivelink-uplugin-is-missing-a-proper-list-of-supportedtargetplatforms/2731850

NVIDIA
- ACE Unreal plugin 2.5 docs: https://docs.nvidia.com/ace/ace-unreal-plugin/2.5/index.html ; changelog: https://docs.nvidia.com/ace/ace-unreal-plugin/2.5/ace-unreal-plugin-changelog.html ; install/support matrix: https://docs.nvidia.com/ace/ace-unreal-plugin/2.5/ace-unreal-plugin-install.html ; A2F page: https://docs.nvidia.com/ace/ace-unreal-plugin/2.5/ace-unreal-plugin-audio2face.html ; ACE for Games: https://developer.nvidia.com/ACE ; Unreal Fest 2024 blog: https://developer.nvidia.com/blog/simplify-and-scale-ai-powered-metahuman-deployment-with-nvidia-ace-and-unreal-engine-5
- Audio2Face-3D open source: https://arxiv.org/abs/2508.16401v1 ; https://huggingface.co/nvidia/Audio2Face-3D-v3.0 ; NVIDIA Open Model Agreement: https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-agreement/ ; A2F Live Link packaging note: https://docs.omniverse.nvidia.com/audio2face/latest/user-manual/livelink-ue-plugin.html

Third-party hardware/vendor/trade press
- Varjo hand tracking (Get Motion Controller Data): https://developer.varjo.com/docs/unreal/ue5/hand-tracking-with-unreal5 ; SenseGlove (5.5 struct split): https://unreal.docs.senseglove.com/2.6/advanced-topics/openxr/ ; Meta Unreal hand tracking: https://developers.meta.com/horizon/documentation/unreal/unreal-hand-tracking-overview
- Mixamo Animation Retargeting 2: https://unamedia.com/ue5-mixamo/docs/retarget-mixamo-to-metahuman/
- UE 5.8 coverage: https://gamefromscratch.com/unreal-engine-5-8-released/ ; https://80.lv/articles/unreal-engine-5-8-is-out-today-with-big-optimization-improvements-and-mesh-terrain ; https://wnhub.io/news/engines/item-51157 ; GamesBeat MetaHuman 5.8: https://gamesbeat.com/epic-games-launches-metahuman-5-8-to-create-real-time-game-character-crowds/ ; Digital Production markerless mocap: https://digitalproduction.com/2026/06/23/metahuman-gets-markerless-mocap/
- MetaHuman licensing coverage: https://www.cgchannel.com/?p=167592 ; https://digitalproduction.com/2025/06/05/metahumans-graduate-ready-for-unity-godot-and-the-fab-cash-register/ ; UE seat pricing (Mar 2024): https://www.cgchannel.com/2024/03/new-pricing-for-unreal-engine-twinmotion-and-realitycapture ; https://www.engadget.com/epic-will-charge-non-game-developers-1850-per-seat-to-use-unreal-engine-162015997.html ; EULA clause summaries (non-authoritative): https://conductatlas.com/platform/unreal-engine/unreal-engine-eula/provision/CA-P-059499/prohibition-on-using-metahuman-for-ai-database-building/
- GASP license coverage: https://www.cgchannel.com/2024/06/get-500-free-game-ready-animations-for-use-in-unreal-engine ; Fab license coverage: https://www.cgchannel.com/2024/11/epic-games-to-share-new-free-assets-on-fab-every-two-weeks
- Mover status discussion: https://forums.unrealengine.com/t/any-roadmap-updates-on-mover/2833898 ; https://forums.unrealengine.com/t/question-about-the-next-steps-for-chaos-mover/2743117
- Beginner guide (secondary; internet requirement claim): https://medium.com/@Jamesroha/a-beginners-guide-to-metahumans-in-unreal-engine-5-6-and-5-7-e9b14fadbf3d

Repo licenses
- SMPL-X: https://smpl-x.is.tue.mpg.de/modellicense.html ; MANO: https://mano.is.tue.mpg.de/license.html ; Meshcapade datasets: https://meshcapade.com/assets/datasets
- MakeHuman FAQ: https://static.makehumancommunity.org/oldsite/faq/what_changed_regarding_the_license_in_2020.html ; https://static.makehumancommunity.org/oldsite/faq/can_i_sell_models_created_with_makehuman.html
- MB-Lab: https://en.wikipedia.org/wiki/MB-Lab ; https://www.cgchannel.com/2020/08/create-free-facially-rigged-cg-characters-with-mb-lab-1-7-5 ; https://alternativeto.net/software/mb-lab/about
- Blender FAQ: https://www.blender.org/support/faq/
- PIFuHD CC-BY-NC: https://cvssp.org/data/self-shadowing/license.txt ; PIFu MIT: https://github.com/maorp/PIFu
- instant-ngp license comparison: https://radiancefields.com/radiance-field-license-comparison
- OpenPose license (quoted): https://hn.nuxtjs.org/item/23360997 ; https://community.vuo.org/t/have-you-seen-openpose/6070
- NeuralBody / Animatable NeRF metadata: https://awesome.ecosyste.ms/projects/236127 ; https://awesome.ecosyste.ms/projects/github.com%2Fzju3dv%2Fanimatable_nerf
- MediaPipe: https://en.wikipedia.org/wiki/MediaPipe ; https://awesome.ecosyste.ms/projects/github.com%2Fgoogle-ai-edge%2Fmediapipe ; Filament: https://summary.ecosyste.ms/projects/369864 ; https://www.phoronix.com/news/Google-Filament-PBR-Engine
- Rocketbox: `hk/ROCKETBOX-LICENSE.txt` (MIT, Microsoft 2020); bone list `hk/names.json`

---

## Critic notes (2026-10-16, completeness critic; see `../critic.md`)

1. Engine target 5.8.x agrees with every other report. The MetaHuman Character Python API "requires 5.8+" claim, `unreal.MetaHumanCharacterEditorSubsystem`, `try_add_object_to_edit` / `remove_object_from_edit`, MetaHuman Crowds/Collections (Experimental) and all maturity labels remain **UNVERIFIED-HERE** (metahuman.com and dev.epicgames.com are blocked from this container; search budget exhausted). They stay in the probe-job list; nothing in the first-playable phase depends on them.
2. **OpenRigLogic is MIT — verified** from `github.com/EpicGames/openriglogic` README (fetched 2026-10-16, saved in `dl2/`). Sample content on Fab is under the Fab Standard License.
3. `UChaosOutfitAsset`, `FRigUnit_PBIK` (plugin `PBIK`), `FXRHandTrackingState`, `UOpenXRHandTrackingSettings`, `FMetaHumanLODProperties`: plausible, not re-verified; probe with `hasattr(unreal, …)` / a grep of `Engine/Plugins` on the machine.
4. The user's machine is **unknown** (see `critic.md` §1.2); the hardware guidance in §2.1/§7 must be expressed as runbook branches, not assumptions. A Mac can author MetaHumans and realtime previews; offline Performance solves, body capture and ACE need Windows.
5. ACE/Audio2Face support for UE 5.7/5.8 is unconfirmed → optional phase-3 item only on Windows+NVIDIA; v1 ships preset answers + pre-baked AnimSequence bank, which needs no runtime plugin.
6. Naming contract adopted by the critic for the C++ port: `FXR*` structs, `FXRView`, DataTables `DT_Staff`, `DT_WaxScenes`, `DT_DialogueRules`, … (full list in `critic.md` §1.9).
