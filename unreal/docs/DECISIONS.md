# Decisions

Short answers first, reasons after. Sources for every fact are in `docs/reference/`.

| Question | Answer |
|---|---|
| Move off the web to get "newest PC game" graphics? | **Yes.** A browser (WebGL/WebGPU) has no hardware ray tracing, no virtualised geometry and a small memory budget. The look you want needs a native engine. |
| Unity? | **No.** Unity's high-end pipeline can't run in a browser either, and for photoreal people and lighting Unreal is ahead: MetaHuman, Lumen, Nanite, MegaLights. |
| Unreal Engine 5? | **Yes, 5.8** (5.8.3 is the current hotfix; Epic calls 5.8 the last planned 5.x release; UE6 early access is expected late 2027). |
| Can it still live on Vercel? | **Partly.** Vercel keeps the web campus and becomes the front door. The Unreal version reaches people as a download (Windows first) and, if wanted, as a live stream (Pixel Streaming 2) from a GPU server. Vercel cannot host the stream itself. See `DELIVERY.md`. |
| Rebuild from scratch or port? | **Port.** Every room, exhibit, book, tour stop and staff answer was extracted from the web build into data, and the geometry was exported as an exact greybox. The Unreal project rebuilds the same campus from that data, then the art gets upgraded room by room. |
| The open-source human repos you sent? | **Mostly not needed.** MetaHuman (free with Unreal, in-editor since 5.6) beats them for photoreal, fully rigged people. Keep Blender. MediaPipe is optional. SMPL-X, MANO, OpenPose, PIFuHD and instant-ngp have non-commercial licences. Full table in `HUMANS.md`. |
| Can Claude in this chat set it up on your computer? | **No.** This chat runs in a cloud container. Cowork's own shell also runs in the cloud since 6 Oct 2026. Something has to run **on your machine**: Claude Code (desktop or CLI, local) or Cowork with a local terminal tool and computer use. See `../COWORK.md`. |

## Engine and rendering

- **Unreal Engine 5.8.3**, DirectX 12 / Shader Model 6 on Windows, Metal SM6 on Apple-silicon Macs.
- **Lumen** global illumination and reflections, with **hardware ray tracing** and *Hit Lighting for Reflections* on RTX / RX 6000-class GPUs. No baked lightmaps: the web build's baked lighting is dropped and everything is lit in real time.
- **Nanite** for all static geometry (architecture, furniture, every book), **Virtual Shadow Maps**, **MegaLights** (production-ready in 5.8) for the many gallery lights, **Temporal Super Resolution** for anti-aliasing and upscaling, **Substrate** materials.
- **Sky Atmosphere + Volumetric Clouds + Sky Light (real-time capture) + Exponential Height Fog (volumetric)** outside; the same sun lights the Reading Room through its arched window.
- **Auto exposure in EV100 + Local Exposure**, so walking from the sunny yard into a dim library adapts like a real camera.
- Scalability presets **Low → Cinematic** (Medium uses 5.8's new Lumen Lite), plus an Auto button that benchmarks the PC.

Why the web build sparkles (for the record): tiny glowing strips pushed 3.2× past white feed a half-resolution bloom; auto-generated normal maps turn texture speckles into glints; grass and leaves use alpha test without coverage; ambient occlusion re-seeds when the resolution adapts; and only 8 lights get re-assigned as you walk. Unreal's TSR, Lumen, real lights and Nanite remove all of these. Details with file:line in `docs/reference/assets.md` §5.

## Project structure

- One C++ module (`WalkTheArchive`). All gameplay logic is in C++, because C++ is text: it can be written, reviewed and versioned here. Python only runs inside the editor (setup), never in the game.
- Content (`.uasset`, `.umap`) is **generated on your machine** by `Scripts/setup_project.py` from text sources in this repo, so GitHub never carries gigabytes of binaries.
- Data lives in DataTables (`/Game/WTA/Data`) built from `WalkTheArchive/Data/*.json`, so text and facts stay editable outside Unreal.
- The UI is built in C++ (no widget assets), styled like the web build: dark green panels, brass edges, cream catalog cards.
- Controls are PC-game standard (mouse look, WASD, E to interact, Tab for a free cursor), plus gamepad.

## What was changed from the web build on purpose

- Rocketbox avatars → MetaHumans (placeholders until they are made).
- Reading Room: real modelled books on every shelf tier (the web used flat painted strips up high) and thick walls so Lumen sees a closed room.
- Each gallery exhibit gets its own museum spotlight.
- Wing hiding, canvas memory tricks, light pooling and quality tiers from the web are dropped (Unreal handles them).
