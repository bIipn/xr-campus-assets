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

Use a short path with no spaces (e.g. `C:\dev\xr-campus-assets` or `~/dev/xr-campus-assets`): `-ExecutePythonScript` (Step 4) and UAT cooks (Step 8) misread paths with spaces. The clone is a few hundred MB.

**Success:** `unreal/WalkTheArchive/WalkTheArchive.uproject` exists.

## Step 1 · Check the computer (preflight)

| Windows | Mac |
|---|---|
| `powershell -ExecutionPolicy Bypass -File unreal\Tools\win\preflight.ps1` | `bash unreal/Tools/mac/preflight.sh` |

It prints the OS, CPU, RAM, GPU and VRAM, free disk space, and which tools are installed, writes
`unreal/Tools/.cache/preflight.json`, and ends with a line `PREFLIGHT_VERDICT <verdict>`:

| Verdict | Exit | Meaning |
|---|---|---|
| **FULL** | 0 | Windows with NVIDIA RTX / AMD RX 6000+ and 8 GB+ VRAM: hardware ray-traced Lumen, MegaLights, the works |
| **STANDARD** | 0 | Software Lumen: an older Windows GPU, or any Apple Silicon Mac (Mac never reports FULL in 5.8). Looks very good, a bit less sharp in reflections |
| **NOT_SUPPORTED** | 2 | e.g. Intel Mac, macOS older than 14, Windows older than 10 1809, under 16 GB RAM, or a GPU under 4 GB VRAM. Stop and tell Ev |

Also needed: about **120 GB free on an SSD** (the preflight warns below that; 250 GB is comfortable) and 32 GB RAM recommended (16 GB minimum).

## Step 2 · Install the tools

| Windows | Mac |
|---|---|
| `powershell -ExecutionPolicy Bypass -File unreal\Tools\win\install_prereqs.ps1` | `bash unreal/Tools/mac/install_prereqs.sh` |

Ask Ev first. It installs only what is missing: on Windows, Git, the Epic Games Launcher, Visual Studio 2026 Community
with the Unreal C++ components (`-VS2022` for 2022) and Blender, via winget (UAC prompts); on a Mac it checks Xcode
(App Store only) and Homebrew, then runs `brew install --cask epic-games blender`. Options: `-Only git,vs`, `-Skip blender`,
`-DryRun` (Windows); `--only epic-games,blender`, `--skip blender`, `--dry-run` (Mac).

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

Generates project files and compiles the `WalkTheArchiveEditor` target (5–20 minutes the first time). Options:
`-Config DebugGame` / `--config DebugGame`, `-SkipProjectFiles` / `--skip-projectfiles`.

**Success:** exit code 0 and a final line `WTA_RESULT {"step": "build_editor", "ok": true, ...}` (UBT itself prints
"Result: Succeeded"). The log is `unreal/Tools/.cache/build_editor.log`.

**If it fails:** open the log it names and find the first `error`. This code was written without being able to
compile it, so a few small errors are possible (a missing `#include`, an API renamed in 5.8). Fix them in
`unreal/WalkTheArchive/Source/` with the smallest possible change, keep `unreal/contract/CPP_API.md` in sync, and
re-run. Commit each fix (`git commit -am "Fix build: ..."`) so the fixes can be pushed back. If the same error
survives two fixes, stop and tell Ev.

## Step 4 · Build the campus (setup script)

| Windows | Mac |
|---|---|
| `powershell -ExecutionPolicy Bypass -File unreal\Tools\win\setup_project.ps1` | `bash unreal/Tools/mac/setup_project.sh` |

First enables the optional plugins this engine has (`configure_plugins.py`) and builds the C++ module if it is missing,
then runs `UnrealEditor-Cmd <uproject> -ExecutePythonScript=unreal/WalkTheArchive/Scripts/setup_project.py -unattended
-nopause -nosplash -stdout -FullStdOutLogOutput -ScriptErrorsAreFatal`. The first run compiles thousands of shaders:
**30–90 minutes**. Each step prints one `WTA_RESULT {json}` line. The steps are:

| Step | What it does |
|---|---|
| `probe` | Checks the engine, Python and that the C++ module loaded |
| `import_meshes` | Imports the 9 campus meshes (`unreal/Pipeline/out/ue/*.glb`) with Nanite and walkable collision (double-sided, so no wall can be walked through from behind) |
| `import_art` | Imports the exhibit artwork |
| `data_tables` | Builds the 17 data tables (exhibits, books, tour, staff answers, …) |
| `build_level` | Creates `/Game/WTA/Maps/L_Campus`, places the campus, player start and game mode |
| `lighting` | Sun, sky, clouds, fog, exposure, every interior light (school ceiling panels and museum downlights included), the exhibit spotlights, and glowing fixtures, screens and windows calibrated to the camera exposure |
| `actors` | Rooms, exhibits, books, stations, rides, tokens, staff and Wax Hall stages |
| `navmesh` | Walkable area for click-to-walk (the game builds missing nav tiles at start: `RuntimeGeneration=Dynamic`) |
| `project_settings` | Startup map, game mode and the data-table settings in the ini files |
| `verify` | Counts everything against the data and requests screenshots into `unreal/WalkTheArchive/Saved/WTA_Shots/` (a headless run may exit before they land) |

**Success:** the results table shows `yes` for every step, the line `check_results: PASS` follows, and the script exits 0
with `WTA_RESULT {"step": "setup_project", "ok": true, ...}`. Logs: `unreal/Tools/.cache/setup.log` and the full engine
log `unreal/Tools/.cache/setup_editor_full.log`.
To repeat only some steps: add `-Steps lighting,actors` (Windows) or `--steps lighting,actors` (Mac). Other options:
`-NullRHI` / `--nullrhi` (no GPU session; no screenshots), `-NoBuild` / `--no-build`, `-SkipPlugins` / `--skip-plugins`,
`-Force` / `--force` (run although an editor has the project open). Environment: `WTA_FORCE=1` re-imports meshes and
art that already exist, `WTA_SHOTS=0` skips the screenshots.

**If a step fails:** read its `WTA_RESULT` line (it carries the error). Most likely cause: a Python API name that
differs in this exact engine version. `probe` lists what exists. Fix the script in
`unreal/WalkTheArchive/Content/Python/wta_setup/`, re-run that step only, and commit the fix.

## Step 5 · First look

| Windows | Mac |
|---|---|
| `powershell -ExecutionPolicy Bypass -File unreal\Tools\win\play.ps1` | `bash unreal/Tools/mac/play.sh` |

Starts the game from the editor binary (`-game`, 1920x1080 window). Options: `-ResX 2560 -ResY 1440`, `-Fullscreen`,
`-ShowLog`, `-Wait` (Windows); `--resx 2560 --resy 1440`, `--fullscreen`, `--log`, `--wait` (Mac).

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
editor (`unreal\Tools\win\open_editor.ps1` or `unreal/Tools/mac/open_editor.sh`). Use Fab/Megascans (in-editor *Window → Fab*) and Poly Haven. Show Ev before/after
screenshots for each room. Save often; back up `WalkTheArchive/Content/` at the end of each session.

Unreal 5.8's **Model Context Protocol** plugin (Experimental) lets Claude drive the open editor directly.
`python unreal/Tools/common/configure_plugins.py --only mcp` enables it (and its toolset plugins) if your engine has it.
Its *Auto Start Server* setting is off by default: turn it on in the plugin's project settings, restart the editor, and
the server listens on `http://127.0.0.1:8000/mcp`. It has no authentication, so keep it on localhost.

## Step 7 · People (M3)

Follow `unreal/docs/HUMANS.md`: four MetaHuman staff first (Margaret, Rosa, Mr. Hale, Coach Rae).

## Step 8 · Package and share (M9)

| Windows | Mac |
|---|---|
| `powershell -ExecutionPolicy Bypass -File unreal\Tools\win\package_game.ps1` | `bash unreal/Tools/mac/package_game.sh` |

Runs `RunUAT BuildCookRun -project=<uproject> -noP4 -platform=Win64|Mac -clientconfig=Development -build -cook -allmaps
-stage -pak -iostore -archive`. Options: `-Config Shipping`, `-Archive <dir>`, `-SkipBuild`, `-NoIoStore` (Windows);
`--config Shipping`, `--archive <dir>`, `--skip-build`, `--no-iostore` (Mac). The game lands in
`unreal/Packaged/Win64/Windows/WalkTheArchive.exe` or `unreal/Packaged/Mac/Mac/*.app`; the log is
`unreal/Tools/.cache/package_<Win64|Mac>_<Config>.log`. See `unreal/docs/DELIVERY.md` for itch.io, signing, and
streaming from the Vercel site.

---

## Troubleshooting the first build

The code was reviewed line by line but has never been compiled. These are the likeliest first-build hiccups and their fixes:

| Symptom | Fix |
|---|---|
| `C4458` / `C4456` / `-Wshadow`: a local or parameter hides a member | Rename the local (e.g. `Slot` → `ButtonSlot`). Never reuse engine member names (`Slot`, `Controller`, `Character`, `Pawn`, `Owner`). Don't lower the warning level |
| `C4244`: conversion from `double` to `float` | Add `static_cast<float>(…)` |
| Header not found: `Widgets/Layout/Anchors.h` | Delete that include line; `CanvasPanelSlot.h` already brings it in |
| `FSlateBrush::ImageSize` errors in `WTAPanelWidget.cpp` | Use `Brush.SetImageSize(…)` |
| Linker: unresolved `IWTAInteractable::…_Implementation` | Add empty default bodies in `Private/Interaction/WTAInteractable.cpp` |
| Enhanced Input warns that `MapKey` or `Mapping.Modifiers` is deprecated | Warnings are fine; check `Engine/Plugins/EnhancedInput/Source/EnhancedInput/Public/InputMappingContext.h` for the 5.8 form only if it's an error |
| Looking up and down is inverted | Flip the Negate modifier on the look axis in `AWTAPlayerController::CreateInputObjects` |
| Esc stops Play-in-Editor instead of closing a panel | Expected in the editor; test Back with gamepad B or in Standalone (`play` script) |
| Click-to-walk and the tour teleport instead of walking | The `navmesh` step didn't run or failed; re-run `setup_project` with `navmesh` |
| A setup step reports an unknown `unreal.*` name | Look it up in this engine (`help(unreal.X)` in the editor's Python console or the `probe` output) and use the 5.8 spelling; keep the `hasattr` fallback |

## Pushing fixes back

Code and script fixes (text files) can go to GitHub: `git push origin unreal5-port`. Never commit generated
content; `.gitignore` already blocks it. If `git push` asks for credentials, Ev signs in.

## When something is unclear

The full reasoning, research and specs are in `unreal/docs/` and `unreal/docs/reference/`, and the rules every file
follows are in `unreal/contract/CONTRACT.md`. Prefer those over guessing.
