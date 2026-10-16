# Runbook: set up Walk the Archive in Unreal Engine 5.8

This is the step-by-step for Claude (Cowork or Claude Code) working **on Ev's own computer**. Each step has
what to run, what success looks like, and what to do if it fails. Steps are safe to repeat.

> **Read this first, Claude.**
> - Since 6 Oct 2026, Cowork's own shell runs in Anthropic's cloud, not on this computer. Run commands on **this
>   machine** through a local terminal tool: Claude Code (local session), or Cowork with the Desktop Commander
>   extension (`start_process` / `read_process_output`). Use computer use only for GUI-only steps (Epic Games Launcher).
> - Ev signs in to accounts personally. Never type Ev's passwords or 2FA codes; pause and ask Ev.
> - Ask before installing software or anything needing admin rights. Ask before deleting anything.
> - Never push `.uasset`/`.umap` files to GitHub (they are ignored on purpose). Back up `WalkTheArchive/Content/` to a cloud drive or external disk instead.
> - After every step, report one line to Ev: step, result, and what's next. If something fails twice, stop and explain in plain words.
> - Paths below are relative to the repo root (`xr-campus-assets`). On Windows use PowerShell; on a Mac use Terminal (zsh/bash).

---

## Step 0 · Get the repo

```sh
git clone https://github.com/bIipn/xr-campus-assets.git
cd xr-campus-assets
git checkout unreal5-port
```

Use a short path with no spaces (e.g. `C:\dev\xr-campus-assets` or `~/dev/xr-campus-assets`). The clone is a few hundred MB.

**Success:** `unreal/WalkTheArchive/WalkTheArchive.uproject` exists.

## Step 1 · Check the computer (preflight)

| Windows | Mac |
|---|---|
| `powershell -ExecutionPolicy Bypass -File unreal\Tools\win\preflight.ps1` | `bash unreal/Tools/mac/preflight.sh` |

It prints the OS, CPU, RAM, GPU and VRAM, free disk space, and which tools are installed, then a verdict:

| Verdict | Meaning |
|---|---|
| **FULL** | NVIDIA RTX / AMD RX 6000+ with 8 GB+ VRAM: hardware ray-traced Lumen, MegaLights, the works |
| **STANDARD** | Works with software Lumen (older GPU or Apple M1). Looks very good, a bit less sharp in reflections |
| **NOT SUPPORTED** | e.g. Intel Mac or no DirectX 12 GPU. Stop and tell Ev |

Also needed: **250 GB free on an SSD** and 32 GB RAM recommended (16 GB minimum).

## Step 2 · Install the tools

| Windows | Mac |
|---|---|
| `powershell -ExecutionPolicy Bypass -File unreal\Tools\win\install_prereqs.ps1` | `bash unreal/Tools/mac/install_prereqs.sh` |

Installs (asks first): Git, Epic Games Launcher, Visual Studio 2026 Community with the Unreal C++ workload (Windows) or checks Xcode (Mac, from the App Store), and Blender 5.2.

Then the **manual part** (Ev, or Cowork computer use while Ev watches):
1. Open the **Epic Games Launcher** and sign in (Ev types the password).
2. **Unreal Engine → Library → + → choose 5.8.x (newest) → Install.** In *Options*, platform support for Windows (or Mac) is enough; skip Android/iOS/Linux to save space. This is a 40–60 GB download.
3. On a Mac: open Xcode once and accept the licence.

**Success:** `find_engine` prints the engine folder:
`python unreal/Tools/common/find_engine.py` (or `python3` on Mac). Any Python 3 works for this one script.

## Step 3 · Build the C++ code

| Windows | Mac |
|---|---|
| `powershell -ExecutionPolicy Bypass -File unreal\Tools\win\build_editor.ps1` | `bash unreal/Tools/mac/build_editor.sh` |

Generates project files and compiles the `WalkTheArchiveEditor` target (5–20 minutes the first time).

**Success:** ends with `BUILD SUCCEEDED` (or "Result: Succeeded") and exit code 0.

**If it fails:** open the log it names and find the first `error`. This code was written without being able to
compile it, so a few small errors are possible (a missing `#include`, an API renamed in 5.8). Fix them in
`unreal/WalkTheArchive/Source/` with the smallest possible change, keep `unreal/contract/CPP_API.md` in sync, and
re-run. Commit each fix (`git commit -am "Fix build: ..."`) so the fixes can be pushed back. If the same error
survives two fixes, stop and tell Ev.

## Step 4 · Build the campus (setup script)

| Windows | Mac |
|---|---|
| `powershell -ExecutionPolicy Bypass -File unreal\Tools\win\setup_project.ps1` | `bash unreal/Tools/mac/setup_project.sh` |

Runs Unreal headless with `unreal/WalkTheArchive/Scripts/setup_project.py`. The first run compiles thousands of shaders: **30–90 minutes**. The steps are:

| Step | What it does |
|---|---|
| `probe` | Checks the engine, Python and that the C++ module loaded |
| `import_meshes` | Imports the 9 campus meshes (`unreal/Pipeline/out/ue/*.glb`) with Nanite and walkable collision |
| `import_art` | Imports the exhibit artwork |
| `data_tables` | Builds the 17 data tables (exhibits, books, tour, staff answers, …) |
| `build_level` | Creates `/Game/WTA/Maps/L_Campus`, places the campus, player start and game mode |
| `lighting` | Sun, sky, clouds, fog, exposure, every interior light and the exhibit spotlights |
| `actors` | Rooms, exhibits, books, stations, rides, tokens, staff and Wax Hall stages |
| `navmesh` | Walkable area for click-to-walk |
| `project_settings` | Startup map and game mode |
| `verify` | Counts everything against the data and saves screenshots |

**Success:** the summary table shows every step `ok`, and the script exits 0. Results are also in `unreal/Tools/.cache/setup.log`.
To repeat only some steps: add `-Steps lighting,actors` (Windows) or `--steps lighting,actors` (Mac).

**If a step fails:** read its `WTA_RESULT` line (it carries the error). Most likely cause: a Python API name that
differs in this exact engine version. `probe` lists what exists. Fix the script in
`unreal/WalkTheArchive/Content/Python/wta_setup/`, re-run that step only, and commit the fix.

## Step 5 · First look

| Windows | Mac |
|---|---|
| `powershell -ExecutionPolicy Bypass -File unreal\Tools\win\play.ps1` | `bash unreal/Tools/mac/play.sh` |

Check with Ev, out loud, one by one:
- [ ] The menu shows; **Enter** starts in the lobby facing the galleries.
- [ ] Mouse looks around, WASD walks, Shift runs, Space jumps; walls and floors are solid.
- [ ] The room name changes in the top-left as you walk (Lobby → Gallery 1 …).
- [ ] Looking at an exhibit shows "Open …"; **E** or a click opens its catalog card with the artwork. **Esc** closes it.
- [ ] Books in the Reading Room open and turn pages. Light comes in through the arched window.
- [ ] **T** runs the tour; it walks you from stop to stop.
- [ ] Margaret answers "where is the library?" and offers to take you there.
- [ ] Tokens can be collected; the badge counter goes up and survives a restart.
- [ ] Graphics presets switch in the menu (try Epic and Medium).

Save 3 screenshots to the repo root, named `ue_lobby.png`, `ue_reading_room.png` and `ue_yard.png` (F9 in Play, or the `verify` step's shots in `unreal/WalkTheArchive/Saved/WTA_Shots/`) and show them to Ev.

## Step 6 · Make it photoreal (M2)

Follow `unreal/docs/LOOKDEV.md`, room by room, starting with the **Reading Room** and **Gallery 1**. Work in the
editor (`open_editor` script). Use Fab/Megascans (in-editor *Window → Fab*) and Poly Haven. Show Ev before/after
screenshots for each room. Save often; back up `WalkTheArchive/Content/` at the end of each session.

Unreal 5.8's **Model Context Protocol** plugin (Experimental) lets Claude drive the open editor directly.
`python unreal/Tools/common/configure_plugins.py --only mcp` enables it if your engine has it. Then start the editor
with `-ModelContextProtocolStartServer`, and the server listens on `http://127.0.0.1:8000/mcp`. It has no
authentication, so keep it on localhost.

## Step 7 · People (M3)

Follow `unreal/docs/HUMANS.md`: four MetaHuman staff first (Margaret, Rosa, Mr. Hale, Coach Rae).

## Step 8 · Package and share (M9)

| Windows | Mac |
|---|---|
| `powershell -ExecutionPolicy Bypass -File unreal\Tools\win\package_game.ps1` | `bash unreal/Tools/mac/package_game.sh` |

Output goes to `unreal/Packaged/<platform>/`. See `unreal/docs/DELIVERY.md` for itch.io, signing, and streaming from the Vercel site.

---

## Pushing fixes back

Code and script fixes (text files) can go to GitHub: `git push origin unreal5-port`. Never commit generated
content; `.gitignore` already blocks it. If `git push` asks for credentials, Ev signs in.

## When something is unclear

The full reasoning, research and specs are in `unreal/docs/` and `unreal/docs/reference/`, and the rules every file
follows are in `unreal/contract/CONTRACT.md`. Prefer those over guessing.
