# Automation research: letting a Claude agent set up the UE5 "XRLibraries Campus" project on the user's computer

Date: 2026-10-16. Scope: (1) Claude Cowork capabilities, (2) driving Unreal Engine from an agent, (3) exact editor-Python APIs, (4) unattended toolchain install + command-line builds, (5) Fab / Megascans / free photoreal sources.

## 0. How this was researched, and how to read the confidence tags

Network conditions in the research container: the web-search tool budget was exhausted before this task started, and the egress proxy returned `403` for `dev.epicgames.com`, `docs.unrealengine.com`, `unrealengine.com`, `epicgames.com`, `fab.com`, `support.fab.com`, `quixel.com`, `forums.unrealengine.com`, `polyhaven.com`, `api.polyhaven.com`, `youtube.com`, `wikipedia.org`. Reachable: `support.claude.com`, `claude.com`, `learn.microsoft.com` (via the Microsoft Learn MCP), `github.com` / `raw.githubusercontent.com` (HTML + raw files + GitHub code search).

Consequently every Epic fact below is sourced either from (a) Epic-published GitHub artefacts, (b) two well-maintained community knowledge bases that were built directly from the UE 5.8 docs/source and that cite the official page URLs ("scenario-labs/skills" `scenario-unreal-expert`, retrieved docs dated 2026-09-24; "kevinpbuckley/unreal-engine-skills", engine-version 5.8, cites engine header line numbers), or (c) multiple independent public scripts that use the API in question. Tags:

- **[P]** primary source read directly (support.claude.com, learn.microsoft.com, Epic's own GitHub repos, winget/Homebrew manifests).
- **[S]** secondary but UE-5.8-specific source that cites the official doc or engine header (scenario-labs, kevinpbuckley). Treat as reliable; verify on the installed engine before relying on exact spellings marked `[verify]` by those authors.
- **[C]** confirmed by 2+ independent public scripts on GitHub (code search, 2025-2026 repos).
- **[M]** from my own knowledge only (cutoff mid-2026); could not be re-verified in this session. Cowork must verify on the machine (the `help(unreal.X)` / stub-grep step in §3.0 does this cheaply).

Nothing in this document was invented to fill a gap; where a name could not be confirmed it is marked [M] or explicitly "unknown".

---

## 1. Claude Cowork (what it is in October 2026, and what it can actually do on the user's PC)

### 1.1 Product shape (all [P], support.claude.com Cowork collection, 14 articles, and claude.com/product/cowork)

- Cowork = "Claude Code's agentic capabilities to knowledge work beyond coding": you describe an outcome, Claude runs a multi-step task. Requires a paid plan (Pro, Max, Team, Enterprise). Surfaces: **Claude Desktop for macOS and Windows** ("requires the latest version of Claude for Windows"), web (claude.ai, beta on Team/Enterprise), iOS/Android, Chrome side panel. Local file, browser and computer use **require the Desktop app open and connected**. The product is being folded into the main Claude experience ("Claude Cowork is now just Claude", article 16761823), so some menu names may differ.
- **Where code runs - this is the decisive fact for our runbook.** Since **6 October 2026** new Cowork sessions on Pro/Max run **in the cloud**: "Claude runs code and shell commands in an isolated environment on Anthropic's servers", "Execution happens in a sandboxed cloud environment, not on your computer"; the "Only on your computer" option was removed and "you can't switch back" (articles 13345190, 14479288, 15520349). The legacy local mode (tasks started before 6 Oct 2026, and some Enterprise deployments) ran code in a dedicated Linux VM (Apple Virtualization.framework on macOS, Hyper-V on Windows) - i.e. even then shell commands never ran on the host OS. Cloud sandboxes "can't reach your home or company network", outbound traffic is proxied to allow-listed destinations ("No network access is the default for Enterprise organizations").
- **Files:** "Claude can only read and write files in folders you've connected" (read/write via the Desktop app; a cloud session reaches those folders "only while the desktop app is open on that computer"). Deleting a file "requires your explicit permission" in every mode. Connected folders can carry "folder instructions" (project-specific context); Cowork **projects** can be created from a local folder and carry "Instructions" (stored in the account, not as a file - the article never mentions `CLAUDE.md`) plus project memory. "Projects are only available in Cowork, not in Claude Code." (14116274)
- **Approval modes** (13345190, 13364135): *Manually approve* (asks before actions), *Automatically approve* (read-only tools auto-approved; write/delete actions are safety-reviewed and unsafe ones blocked; recommended for sensitive work is Manual), *Skip all approvals* ("nothing checks its actions"; use only when every tool and input is trusted). Admins can disable persistent "always allow".
- **Built-in browser** (16607400): a separate browser in the Cowork side panel (own cookies/logins, can import cookies) - usable for the Epic Games account login step, Fab browsing, etc.
- **Computer use** (14128542, beta, **Pro and Max only**, "Team and Enterprise plans don't have access"; macOS and Windows; not on Linux beta): Claude "takes over your screen only when it has to" - order of preference is connectors, then browser, then screen. It can click, type, "open files, and run dev tools"; it asks permission "before accessing each application" (configurable to "Full control"); investment/trading apps blocked; "no sandbox between Claude and your applications"; computer must be awake and the Desktop app open; on macOS 15+ it can work in background windows. Enable via Settings > General > "Enable computer use".
- **Scheduled tasks** (13854387): all paid plans; cadences hourly / daily / weekly / weekdays / manual; created with `/schedule` or "Create with Claude" / "Set up manually" (name, prompt, approval mode, frequency, optional model and folder). They "run even when your computer is asleep" (cloud) **but** "If a scheduled task requires local files or apps, it will only run locally." Each run is its own Cowork session with the same connectors, skills and plugins.
- **Dispatch** (13947068, limited beta on some Pro/Max): message Claude from the phone, "Dispatch runs your tasks on your desktop, so your computer needs to be awake"; can "organize or process files in a specific folder on your computer". Single thread only.
- **Skills** (12512176, 12512180): "folders of instructions, scripts, and resources that Claude loads dynamically"; available on all plans incl. Free once *Settings > Capabilities > Code execution and file creation* is on; custom skills are uploaded as a **ZIP** from *Customize > Skills > + > Create skill > Upload a skill*; failure modes listed: ZIP too large, "Skill folder name doesn't match the skill name", "Missing required skill.md file", invalid characters. Format follows the open Agent Skills standard (agentskills.io) - i.e. a folder with `SKILL.md` front-matter `name`/`description` + optional `scripts/`, `references/`. Directory-installed skills are view-only (download, edit, re-upload to customise).
- **Plugins** (13837440, 14328846): "bundles skills, connectors, and sub-agents into a single package"; "Hooks and sub-agents run only in Cowork and Claude Code, not in chat"; all paid plans; installed from *Customize > Plugins > Discover*; marketplaces: built-in Knowledge Work marketplace, Anthropic-curated ones, or **any Git repository on github.com / gitlab.com / bitbucket.org** ("add one from a Git repository"); you can upload your own plugin file, and the "Plugin Create" plugin walks through authoring. Plugins "are saved to your account, so they also sync to Claude Code when you sign in with the same account".
- **MCP / connectors:** Cowork uses connectors (remote MCP) and **local MCP servers** via Claude Desktop "desktop extensions" (`.mcpb`, installed from Settings > Extensions, "Claude Desktop includes a built-in Node.js environment"; Node, Python and binary servers supported) [P, 10949351]. The safety article is explicit that local MCP servers "run on your computer with the same permissions as any other program you run" [P, 13364135], and the surfaces article says "Local connectors and plugins with local MCP servers work through the desktop app only" [P, 15520349]. Enterprise MDM keys `isLocalDevMcpEnabled` / `isDesktopExtensionEnabled` can disable them [P, 14479288].
- Monitoring: OpenTelemetry streaming and Compliance API for Team/Enterprise admins [P, 14477985, 14479288].

### 1.2 What this means for "Cowork installs Unreal and builds the project on the user's machine"

Cowork's own shell **cannot** launch `UnrealEditor-Cmd.exe`, the Visual Studio bootstrapper, `msiexec`, `brew`, or `xcodebuild` on the host - its shell is a cloud sandbox (or, in legacy mode, a Linux VM). Three host-execution routes exist, in order of robustness:

1. **Claude Code on the host** (CLI; macOS/Linux/WSL and "Windows (PowerShell)" installers; "Claude will always ask before changing a file or running a command", with Plan / Accept Edits / default modes) [P, 14552382; 11145838: Pro/Max plans include Claude Code in the terminal and supported IDEs]. This is the natural executor for everything in §4 and §2. Give it the repo's `CLAUDE.md` (Claude Code's project instruction file - [M], Claude Code docs) and the runbook.
2. **Cowork + a local MCP server that runs host processes.** The *Desktop Commander* plugin (present in this workspace's plugin list; its server description: "Terminal process tools support shell commands, REPLs, and long-running processes. `start_process` creates a process session; `interact_with_process` sends input; `read_process_output` reads later output; `force_terminate` ends a session"; filesystem tools scoped to `allowedDirectories`) gives Cowork a real host shell. Any other local MCP (`.mcpb`) with a shell tool works the same way. The session must be started from the desktop app and the app must stay open.
3. **Cowork computer use** for the GUI-only steps: Epic Games Launcher sign-in (Epic account + 2FA), clicking *Unreal Engine > Library > + > 5.8.x > Install*, accepting Xcode/VS installer prompts. Slow, beta, Pro/Max only, and it will ask per application.

Hand-off format that works with all three routes (and with scheduled/Dispatch tasks): a folder in the repo, connected to Cowork as a project, containing `RUNBOOK.md` (numbered idempotent steps, each with its verification command and expected output), `scripts/win/*.ps1`, `scripts/mac/*.sh`, `ue/python/*.py` (headless jobs that print one machine-readable `RESULT {...}` line), `ue.vsconfig`, and a `skills/xrcampus-ue/SKILL.md` ZIP for upload. Keep approval mode on *Manually approve* for installer steps and *Automatically approve* for file/Python steps; never *Skip*.

---

## 2. Driving Unreal from an agent

Current engine: **UE 5.8** is the shipping release in October 2026 (5.7 shipped Nov 2025; 5.9 is referenced in 5.8 deprecation notes) [S: scenario-labs ue-5.8-traps.md; kevinpbuckley skills "engine-version 5.8"; multiple 2026 READMEs "Unreal Engine 5.8.1 and Visual Studio 2026"]. Exact 5.8 release date: not verifiable here. Cowork should install the newest 5.8.x the Launcher offers.

### 2.1 Python Editor Script Plugin (headless and in-editor)

- Plugin: `PythonScriptPlugin` (Edit > Plugins > Scripting > "Python Editor Script Plugin"; `Engine/Plugins/Experimental/PythonScriptPlugin/`). Embedded **Python 3.11.8** in 5.8 (VFX Reference Platform CY2024); no separate install [S, kevinpbuckley]. Python 2 syntax in old Epic samples is a syntax error [S]. Python is editor-only; never in PIE/cooked games [S].
- Enable in `.uproject`: `"Plugins": [{"Name": "PythonScriptPlugin", "Enabled": true}, {"Name": "EditorScriptingUtilities", "Enabled": true}, ...]` [C, standard].
- **Three ways to run a script from the command line** (Epic doc "Scripting the Unreal Editor Using Python", § The Command Line, as summarised in [S]; command forms also [C] in 2025-26 scripts):
  ```
  REM Headless commandlet: loads NO level, fewer modules, fastest (imports, DataTables, asset creation)
  "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" "C:\dev\XRCampus\XRCampus.uproject" -run=pythonscript -script="C:\dev\XRCampus\ue\python\job.py" -unattended -nopause -nosplash -stdout -FullStdOutLogOutput

  REM Full editor init then run script and exit (needed when a level/world or viewport is required, e.g. spawning actors into a map, screenshots)
  "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" "C:\dev\XRCampus\XRCampus.uproject" -ExecutePythonScript="C:\dev\XRCampus\ue\python\build_level.py" -unattended -nopause -nosplash -stdout -FullStdOutLogOutput -ScriptErrorsAreFatal
  ```
  macOS (Launcher install path confirmed in a 2026 public script for UE_5.5; same layout expected for 5.8):
  ```
  "/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd" "/path/XRCampus/XRCampus.uproject" -unattended -stdout -FullStdOutLogOutput -ExecutePythonScript="/path/XRCampus/ue/python/build_level.py"
  ```
  Notes: `-ExecCmds="py script.py"` is discouraged (can run before the editor is ready) [S]. `-ScriptErrorsAreFatal` (5.5+) makes a failing `-ExecutePythonScript` return non-zero [S, rn55]. If `Engine.Python.IsEnabledByDefault` is false (5.6 lazy init) the commandlet/`-ExecutePythonScript` force-enable Python; otherwise pass `-EnablePython` [S]. Add `-NullRHI` for import-only jobs on machines without a usable GPU session (no rendering, so no screenshots). In the commandlet the Asset Registry may still be scanning: call `unreal.AssetRegistryHelpers.get_asset_registry().wait_for_completion()` before registry queries [S, 5.8 batch-processor sample]. Pass script arguments through environment variables or a JSON sidecar (pattern used by several 2026 pipelines: `set JOB=C:/out/job.json` then read it in the script) [C].
- **The open editor holds a write lock on loaded assets**: a headless job that saves must run while no editor has the project open; otherwise drive the open editor (Remote Execution / MCP) [S, Jamie Dale talk].
- Startup scripts: `[/Script/PythonScriptPlugin.PythonScriptPluginSettings]` `+StartupScripts=` and `+AdditionalPaths=` in `DefaultEngine.ini` (properties `StartupScripts`, `AdditionalPaths` in `PythonScriptPluginSettings.h`) [S]; any `Content/Python/init_unreal.py` auto-runs [S]. Developer Mode writes the stub `Intermediate/PythonStub/unreal.py` (~10 MB) - grep it to confirm every name in §3 [S].
- **Python Remote Execution** (drive a *running* editor, no extra plugin): Project Settings > Plugins > Python > "Enable Remote Execution"; UDP multicast discovery `239.0.0.1:6766`, TCP command channel `127.0.0.1:6776`; commands `ExecuteFile`, `ExecuteStatement`, `EvaluateStatement`; Epic ships the client `remote_execution.py` inside the plugin's `Content/Python` folder [S + C: runreal/unreal-mcp is built on it]. Corresponding ini keys (`bRemoteExecution=True`, `RemoteExecutionMulticastGroupEndpoint=239.0.0.1:6766`, `RemoteExecutionMulticastBindAddress=127.0.0.1`) [M - confirm in `PythonScriptPluginSettings.h`]. If the agent is on another machine, bind `0.0.0.0` (runreal README) [P].

### 2.2 Remote Control API (HTTP/WebSocket, running editor)

- Plugins: "Remote Control API" (+ "Remote Control Web Interface" optional). Server is off until `WebControl.StartServer` (or `WebControl.EnableServerOnStartup`); off in packaged/`-game` unless `-RCWebControlEnable -RCWebInterfaceEnable`; binds 127.0.0.1; **HTTP 30010, WebSocket 30020** [S, 5 official RC pages; ports also [C]].
- Endpoints [C: sam-david/unreal-mcp API survey; vimlesh1975/studiocg]: `PUT /remote/object/property` (get/set any UObject property), `PUT /remote/object/call` (call any BlueprintCallable UFUNCTION), `PUT /remote/batch`, `GET /remote/info`, preset endpoints `/remote/preset/...`. Body example: `{"objectPath": "/Game/Maps/L_Campus.L_Campus:PersistentLevel.PostProcessVolume_0", "functionName": "...", "parameters": {...}, "generateTransaction": true}`. Use C++ names (`bSweep`), object paths from `get_path_name()`, PIE objects carry `UEDPIE_0_` [S].
- **5.8 change:** remote UFUNCTION execution via `/remote/object/call` is **disabled by default** and must be re-allowed with an allow list in Remote Control project settings (setting names not verified) [S, rn58 § Motion Design / VP]. Property access is not described as affected. `[HTTPServer.Listeners] DefaultBindAddress=0.0.0.0` exposes the server on the LAN (and apparently the MCP listener too) [S].
- Verdict for this project: good for live tweaking (exposure, PPV values) from a dashboard; not needed for one-shot project generation - Python does that.

### 2.3 Epic's official MCP server (new in 5.8, Experimental)

- Plugin `ModelContextProtocol` (Experimental) plus **toolset plugins** that must be enabled separately ("it has no tools alone: enable All Toolsets"; the *Editor Toolset* plugin is "missing from the online documentation" per Epic's own webinar). "Auto Start Server" is false by default; launch flags `-ModelContextProtocolStartServer -ModelContextProtocolPort=8000`; endpoint `http://127.0.0.1:8000/mcp`, HTTP + SSE, **no auth**; tool calls run serially on the game thread; Tool Search exposes `list_toolsets`, `describe_toolset`, `call_tool`; `describe_toolset` payloads can be enormous (Niagara "almost a quarter of a million" tokens) [S: scenario-labs citing Epic doc "Unreal MCP" and Epic Education webinar "Getting Started with MCP in UE 5.8" (youtube.com/watch?v=k0tgmrBuIJc) and Unreal Fest Chicago 2026 "From Words to Worlds: Integrating MCP into the Unreal Editor" (youtube.com/watch?v=lDf_y-YPELo)]. db-lyon/ue-mcp wraps "Epic's 830 official Unreal tools" as `epic_*` actions on 5.8+ [P, README]. Epic's doc page could not be fetched (blocked) - Cowork should open "Unreal MCP" in the 5.8 docs for the plugin list and settings.
- Epic in-editor AI: UE 5.7 added an in-editor **AI Assistant panel** (not an MCP server) [S, rn57]. Nothing else official was confirmed.

### 2.4 Community Unreal MCP servers (status as of 2026-10-16, GitHub metadata [P])

| Repo | Stars | Last push | UE | Transport | Notes |
|---|---|---|---|---|---|
| chongdashu/unreal-mcp | 2.1k | **2025-04-22** (unmaintained) | 5.5+ | C++ plugin TCP 55557 + Python server (uv) | Actors, Blueprints, BP graph, editor camera; MIT; "EXPERIMENTAL, not for production" |
| flopperam/unreal-engine-mcp | 1.1k | 2026-06-26 | 5.5-5.7 | local plugin + Python, or hosted "Flop MCP" (API key) | acquired by Aura (tryaura.dev); local server basic |
| ChiR24/Unreal_mcp ("EngineWire") | 956 | 2026-10-16 | **5.0-5.8** | C++ plugin; native Streamable HTTP `127.0.0.1:3000/mcp` with `X-MCP-Capability-Token` (from `Saved/MCP/capability-token`), or stdio Node server over WS 8090 | 23 internal tools / "400 capabilities" incl. `manage_asset` (materials, textures, DataTables), `manage_level`, `system_control` (console, builds, Python); beta 0.6; MIT |
| db-lyon/ue-mcp | 426 | 2026-10-16 | 5.4-5.8 Win, 5.6+ mac/linux | `npx ue-mcp init` deploys + compiles a C++ bridge plugin, WS JSON-RPC | 29 category tools; filesystem reads work with editor closed; needs C++ toolchain; MIT |
| tumourlove/monolith | 334 | 2026-09-09 | **5.7 & 5.8** | native C++ HTTP server port 9316 + `monolith_proxy.exe` | **listens on all interfaces** (no bind option in `FHttpServerModule`) - firewall it; MIT |
| runreal/unreal-mcp | 116 | 2025-06-06 | 5.4+ | **Python Remote Execution only** (`npx -y @runreal/unreal-mcp`) | 20 tools incl. run-arbitrary-Python, screenshots, camera; zero engine-side code; MIT |
| GenOrca/unreal-mcp | 145 | 2026-07-07 | 5.x | Python + C++ | Apache-2.0; its `data_table_actions.py` is a good reference for DataTable Python |
| prajwalshettydev/UnrealGenAISupport | 675 | 2026-04-28 | 5.x | plugin w/ LLM APIs + MCP | MIT |
| kvick-games/UnrealMCP | 614 | 2025-06-22 | 5.x | - | stale |

Recommendation: for *building the project* use headless Python (deterministic, versionable, no extra plugin). For *interactive fix-up with the editor open*, prefer Epic's 5.8 `ModelContextProtocol` (first-party) or `runreal/unreal-mcp` (plugin-free). Do not install prebuilt community bridge binaries casually: they are engine-minor-locked, some bind 0.0.0.0, none authenticate except EngineWire.

---

## 3. Exact editor-Python APIs for the campus build

### 3.0 First job: probe the installed engine (cheap, removes all [M] uncertainty)

```python
# ue/python/probe.py  - run with -run=pythonscript
import unreal, json, os
out = {"engine": unreal.SystemLibrary.get_engine_version(), "has": {}}
for name in ["InterchangeManager", "ImportAssetParameters", "InterchangeGenericAssetsPipeline",
             "AssetImportTask", "LevelEditorSubsystem", "EditorActorSubsystem", "EditorAssetSubsystem",
             "SubobjectDataSubsystem", "DataTableFunctionLibrary", "DataTableFactory", "CSVImportFactory",
             "MaterialEditingLibrary", "MaterialInstanceConstantFactoryNew", "PostProcessVolume",
             "LevelInstance", "PackedLevelActor", "EditorLevelUtils", "WorldPartitionBlueprintLibrary",
             "BlueprintGraphEditor", "ModelContextProtocolSettings"]:
    out["has"][name] = hasattr(unreal, name)
out["new_level_doc"] = unreal.LevelEditorSubsystem.new_level.__doc__
print("RESULT " + json.dumps(out))
```
Also turn on *Project Settings > Plugins > Python > Developer Mode* once and grep `Intermediate/PythonStub/unreal.py` [S].

### 3.1 Importing glTF/GLB and FBX

Interchange is the default importer for glTF/GLB (since 5.0) **and for FBX in 5.8**; legacy FBX via cvar `Interchange.FeatureFlags.Import.FBX 0` (`.ToLevel 0` for scene import) [S kevinpbuckley + S scenario + C: SatisfactoryModLoader `DefaultEngine.ini` sets `Interchange.FeatureFlags.Import.FBX=0`].

Route A - `AssetImportTask` (simplest; Interchange picks the project-default pipeline stack) [C, many scripts]:
```python
import unreal
def import_file(src, dest="/Game/Campus/Meshes"):
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", src)
    t.set_editor_property("destination_path", dest)
    t.set_editor_property("automated", True)        # never show dialogs
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    return list(t.get_objects())                     # 5.8: .result is deprecated -> get_objects() [S]
```
Caveat [S, 5.8 py-ref]: under Interchange `destination_name` is ignored (names come from the pipeline) - import into a per-asset folder and rename with `EditorAssetSubsystem.rename_asset`.

Route B - `InterchangeManager` with an explicit pipeline (full control over Nanite, combine, materials) [C: genex-games, OpenDCAI/GameFactory-3A, oh-ashen-one, scenario-labs scripts]:
```python
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)

def make_pipeline(path="/Game/Campus/Pipelines/IP_CampusMesh"):
    # Duplicate Epic's default assets pipeline and tweak it; override_pipelines needs ASSET paths.
    if not EAS.does_asset_exist(path):
        EAS.duplicate_asset("/Interchange/Pipelines/DefaultAssetsPipeline", path)   # source path [M-verify in Content Browser: /Interchange/Pipelines/]
    p = EAS.load_asset(path)                                  # unreal.InterchangeGenericAssetsPipeline
    mesh = p.get_editor_property("mesh_pipeline")             # InterchangeGenericMeshPipeline [S: property names bBuildNanite, CombineStaticMeshesBehavior, bGenerateLightmapUVs, bCollision -> snake_case]
    mesh.set_editor_property("build_nanite", True)
    mesh.set_editor_property("generate_lightmap_uvs", False)  # Lumen only
    mesh.set_editor_property("combine_static_meshes_behavior", unreal.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE)  # enum name [M-verify]
    EAS.save_loaded_asset(p)
    return p

def interchange_import(src, dest_folder, pipeline):
    params = unreal.ImportAssetParameters()
    params.set_editor_property("is_automated", True)
    params.set_editor_property("replace_existing", True)
    params.set_editor_property("override_pipelines", [unreal.SoftObjectPath(pipeline.get_path_name())])
    source = unreal.InterchangeManager.create_source_data(src)
    mgr = unreal.InterchangeManager.get_interchange_manager_scripted()
    ok = mgr.import_asset(dest_folder, source, params)        # bool
    mgr.wait_until_all_tasks_done(False)                      # [C] - imports are async; the arg is bCancel (True cancels them)
    return ok
```
Verified names: `InterchangeManager.get_interchange_manager_scripted()`, `InterchangeManager.create_source_data(path)`, `ImportAssetParameters` (`is_automated`, `replace_existing`, `override_pipelines` list of `SoftObjectPath`), `manager.import_asset(content_path, source_data, params)`, `wait_until_all_tasks_done(bCancel)` [C] (verified on 5.8.3: pass False to wait, True cancels in-flight imports); `import_scene(...)` for level import exists in the C++ API (`ImportScene`) [S] - for a campus, import **assets**, then spawn actors from your own JSON layout (deterministic).
Texture import: PNG/TGA/JPEG/EXR/HDR/DDS/PSD via Interchange; normal maps auto-detected (`bDetectNormalMapTexture`), set `srgb=False` + `compression_settings=unreal.TextureCompressionSettings.TC_NORMALMAP` for data maps (names [C]).

### 3.2 Levels

```python
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
LES.new_level("/Game/Campus/Maps/L_Campus", is_partitioned_world=True)   # 5.8 signature per API ref [S]; param name [verify]
LES.new_level_from_template("/Game/Campus/Maps/L_Hall", "/Engine/Maps/Templates/OpenWorld")  # [M] template path
LES.load_level("/Game/Campus/Maps/L_Campus")      # closes current level WITHOUT saving [S]
LES.save_current_level(); LES.save_all_dirty_levels()
LES.editor_play_simulate(); LES.editor_request_end_play()
```
`new_level`, `load_level`, `save_current_level`, `save_all_dirty_levels`, `save_current_level_as` [C]. `unreal.EditorLevelLibrary` still works but is deprecated since 5.0 (`UE_DEPRECATED(5.0, ...)`) [S]. Build lighting: `LES.build_light_maps(quality, with_reflection_captures)` exists [M] but **is not needed** - see 3.7.

### 3.3 Spawning actors and setting properties

```python
EAS_ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sm = unreal.load_asset("/Game/Campus/Meshes/SM_Bookshelf")
a = EAS_ACTORS.spawn_actor_from_object(sm, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))   # StaticMeshActor from a mesh
b = EAS_ACTORS.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0,0,0), unreal.Rotator(0,0,0))
a.set_actor_label("Lib_Bookshelf_01"); a.set_folder_path("Library/Props"); a.tags = ["AgentCreated"]
a.set_actor_scale3d(unreal.Vector(1,1,1))
a.static_mesh_component.set_material(0, unreal.load_asset("/Game/Campus/Materials/MI_Wood"))
a.set_editor_property("mobility", unreal.ComponentMobility.STATIC)          # via root component in practice
EAS_ACTORS.get_all_level_actors(); EAS_ACTORS.destroy_actor(a); EAS_ACTORS.set_actor_selection_state(a, True)
```
`spawn_actor_from_class`, `spawn_actor_from_object`, `get_all_level_actors`, `destroy_actor` [S header line refs + C]. Rotator positional order is roll, pitch, yaw - **use keywords** `unreal.Rotator(pitch=, yaw=, roll=)` [S]. `set_editor_property` = a Details-panel edit (pre/post-edit, rebuilds); plain attribute assignment notifies nothing [S, Jamie Dale]. Structs come back as copies: get, modify, set back [S]. Wrap logical operations in `with unreal.ScopedEditorTransaction("Agent: place library"):` [S]. `get_all_level_actors()` only sees *loaded* World Partition cells [S].

Adding components to an actor/Blueprint from Python (5.1+): `unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)`; `k2_gather_subobject_data_for_instance(actor)` / `k2_gather_subobject_data_for_blueprint(bp)`; `add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=..., new_class=unreal.SplineComponent, blueprint_context=None))` returns `(handle, fail_reason)`; `rename_subobject(handle, unreal.Text(name))`; `unreal.SubobjectDataBlueprintFunctionLibrary.get_object(...)` [C: EpicGames/BlenderTools send2ue, CARLA, genex-games].

### 3.4 DataTables from CSV/JSON (for exhibit metadata, NPC rosters, station definitions)

Row struct: define in C++ `USTRUCT(BlueprintType) struct FExhibitRow : public FTableRowBase {...}` (module compiled before the Python job) or a Blueprint UserDefinedStruct asset. Load it as `unreal.load_object(None, "/Script/XRCampus.ExhibitRow")` (C++) or `unreal.load_asset("/Game/Campus/Data/S_Exhibit")` (BP struct).
```python
tools = unreal.AssetToolsHelpers.get_asset_tools()
factory = unreal.DataTableFactory()
factory.set_editor_property("struct", row_struct)                       # [C: GenOrca, AbhayAnandUCSD, Mercenaries-Fan-Build]
dt = tools.create_asset("DT_Exhibits", "/Game/Campus/Data", unreal.DataTable, factory)
ok = unreal.DataTableFunctionLibrary.fill_data_table_from_json_string(dt, json_text)   # whole-table replace; returns bool (older) or list of problems (newer) [C]
ok = unreal.DataTableFunctionLibrary.fill_data_table_from_csv_file(dt, "C:/data/exhibits.csv")   # [C]
unreal.EditorAssetLibrary.save_loaded_asset(dt)
```
Also [C]: `fill_data_table_from_csv_string`; `unreal.CSVImportFactory()` with `automated_import_settings = unreal.CSVImportSettings()` (`import_row_struct`, `import_type = unreal.CSVImportType.ECSV_DATA_TABLE`) inside an `AssetImportTask` for reimport-able CSVs; `fill_data_table_from_json_file` [M]. JSON shape: a list of objects, each with `"Name"` (row name) plus struct fields [C].

### 3.5 Materials and material instances

```python
tools = unreal.AssetToolsHelpers.get_asset_tools()
M = unreal.MaterialEditingLibrary
mat = tools.create_asset("M_CampusMaster", "/Game/Campus/Materials", unreal.Material, unreal.MaterialFactoryNew())
tex = M.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, -400, 0)
tex.set_editor_property("parameter_name", "BaseColor"); tex.set_editor_property("texture", unreal.load_asset("/Game/Campus/Textures/T_Default_D"))
M.connect_material_property(tex, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
rough = M.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -400, 300)
rough.set_editor_property("parameter_name", "Roughness"); rough.set_editor_property("default_value", 0.6)
M.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
M.recompile_material(mat); M.layout_material_expressions(mat)
mi = tools.create_asset("MI_Wood", "/Game/Campus/Materials", unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
M.set_material_instance_parent(mi, mat)
M.set_material_instance_texture_parameter_value(mi, "BaseColor", tex_asset)
M.set_material_instance_scalar_parameter_value(mi, "Roughness", 0.45)
M.update_material_instance(mi)
unreal.EditorAssetLibrary.save_directory("/Game/Campus/Materials")
```
`set_material_instance_parent`, `MaterialInstanceConstantFactoryNew`, `create_material_expression`, `connect_material_property`, `recompile_material` [C, 500+ hits]. **Substrate** is on by default for projects created in 5.7+ (legacy path for upgraded projects): under Substrate the Slab has no Metallic input (Diffuse Albedo / F0 / F90) and "Convert to Substrate" is one-way; read `r.Substrate` in `DefaultEngine.ini` before authoring; `MP_BASE_COLOR`-style property connections for Substrate materials need the Substrate node graph instead [S]. Safer plan: author one master material in the editor (or ship it as a `.uasset` in the repo), create only instances from Python.

### 3.6 PostProcessVolume (exposure, Lumen, grading)

```python
ppv = EAS_ACTORS.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0,0,0), unreal.Rotator(0,0,0))
ppv.set_editor_property("unbound", True)                                  # [C]
s = ppv.get_editor_property("settings")                                   # unreal.PostProcessSettings (copy!)
s.set_editor_property("override_dynamic_global_illumination_method", True)
s.set_editor_property("dynamic_global_illumination_method", unreal.DynamicGlobalIlluminationMethod.LUMEN)
s.set_editor_property("override_reflection_method", True)
s.set_editor_property("reflection_method", unreal.ReflectionMethod.LUMEN)
s.set_editor_property("override_auto_exposure_method", True)
s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)   # [M] enum value name
s.set_editor_property("override_auto_exposure_bias", True); s.set_editor_property("auto_exposure_bias", 1.0)
ppv.set_editor_property("settings", s)
```
Pattern `override_<x>` + `<x>` on `post_process_settings` [C: spear-sim uses exactly `override_dynamic_global_illumination_method` / `override_reflection_method`]; copy-modify-set-back [S]. "Exposure Compensation" is the UI name of `auto_exposure_bias` [S]. 5.8 unified pre-exposure cvar `r.EyeAdaptation.CachedLightingPreExposure` (default 4); 5.6+ Lumen cached-lighting range -8..24 EV with an on-screen warning when exceeded [S].

### 3.7 Lighting with Lumen - no light build

New 5.5+ templates set `r.AllowStaticLighting=False`; "Build Lighting" does not apply [S, rn55]. Project defaults for `Config/DefaultEngine.ini` `[/Script/Engine.RendererSettings]` (names [S]/[C]; MegaLights is Production Ready in 5.8):
```
r.DynamicGlobalIlluminationMethod=1
r.ReflectionMethod=1
r.Lumen.HardwareRayTracing=True
r.RayTracing=True
r.GenerateMeshDistanceFields=True
r.Shadow.Virtual.Enable=1
r.Nanite.ProjectEnabled=True
r.AllowStaticLighting=False
r.SkinCache.CompileShaders=True
r.AntiAliasingMethod=4
r.Substrate=1                       ; on by default for new 5.7+ projects
```
MegaLights and `r.MegaLights.*` project toggles: confirm the exact cvar in *Project Settings > Rendering* (the 5.8 notes only confirm `r.MegaLights.DirectionalLights 1`) [S]. 5.8 "deprecated cvars now ensure, warn or assert when used: do not set cvars from memory" [S] - set them via the Project Settings UI once, then commit the ini. Use `-DPCVars=` at launch to pre-set cvars for headless jobs [S].

### 3.8 World Partition vs Level Instances for a campus

- World Partition (one persistent level, spatial-hash grid, OFPA = one `.uasset` per actor under `__ExternalActors__`) is the default for new Games templates; streaming can be disabled while keeping WP/OFPA [S]. For a campus of a few hundred metres with ~5 buildings, WP mainly buys **OFPA** (parallel edits, agent-friendly per-actor files) and **Data Layers** (toggle "night mode", "exhibit set B"); HLOD is optional.
- **Level Instances** (`ALevelInstance`, embeds a `.umap` as a prefab; OFPA levels are *embedded* into the WP grid at runtime) and **Packed Level Actors** (`APackedLevelActor`, bake static meshes to ISMs) are the right unit for each building (Museum, Wax Hall, Library, Workshop, Recess Yard) [S]. Python: spawn `unreal.LevelInstance` with `EditorActorSubsystem.spawn_actor_from_class`, then `set_editor_property("world_asset", unreal.load_asset("/Game/Campus/Buildings/L_Library"))` [C: obilang/UE_CELevelImporter, bralkor recipe book, borlo11]. Author each building's `.umap` with its own headless job (new_level -> spawn -> save), then place instances in `L_Campus`.
- Legacy streaming sublevels (non-WP): `unreal.EditorLevelUtils.create_new_streaming_level(unreal.LevelStreamingAlwaysLoaded, "/Game/Campus/Sub/L_Library", False)` [C].
- Gotcha: any actor referenced from the Level Blueprint becomes Always Loaded [S]; keep gameplay in Blueprint/C++ classes.

---

## 4. Installing the toolchain unattended

### 4.1 Epic Games Launcher

- Windows: `winget install --id EpicGames.EpicGamesLauncher -e --accept-package-agreements --accept-source-agreements` - manifest 1.3.210.0 (ReleaseDate 2026-09-24), WiX MSI `EpicInstaller-20.3.3.msi`, `Scope: machine`, `ElevationRequirement: elevatesSelf`, default `%ProgramFiles(x86)%\Epic Games` [P, microsoft/winget-pkgs]. Direct MSI: `msiexec /i EpicInstaller-20.3.3.msi /qn /norestart` (standard MSI quiet switches; the MSI URL is `https://epicgames-download1.akamaized.net/Builds/UnrealEngineLauncher/Installers/Windows/EpicInstaller-20.3.3.msi`).
- macOS: `brew install --cask epic-games` (cask 20.3.3, DMG from the same CDN, `depends_on macos: :ventura`, `app "Epic Games Launcher.app"`) [P, Homebrew/homebrew-cask].
- **Login is manual**: Epic account + 2FA in the Launcher UI. Cowork can do it with computer use, or the user does it once; the Launcher keeps the session.

### 4.2 Installing the engine

- Only the Launcher installs binary UE builds; there is no official CLI. **Legendary** (derrod/legendary, 5.3k stars, actively released) is a games launcher replacement; its `list --include-ue` flag only *lists* "Unreal Engine content (Engine/Marketplace)" - the README gives no way to install the engine [P]. Do not plan on it.
- Launcher path (GUI, scriptable only via computer use): *Unreal Engine > Library > "+" > choose 5.8.x > Install*; in the version's *Options* deselect target platforms you do not need and tick "Editor symbols for debugging" only if you will debug (MS Learn documents that Options dialog) [P]. Default install dirs: `C:\Program Files\Epic Games\UE_5.8` and `/Users/Shared/Epic Games/UE_5.8` [C for Mac 5.5; Windows [M]].
- Disk: a Launcher install of UE 5.x is on the order of 40-60 GB without extra platforms, more with symbols and target platforms; Visual Studio with the C++ game workload ~15-25 GB; DDC/shader cache for a Lumen/Nanite project grows by tens of GB; Megascans content adds whatever you download. Budget **250 GB free** on an SSD [M - Epic's hardware page is blocked; verify].
- Finding the engine from a script: `Engine/Build/Build.version` (JSON with `MajorVersion/MinorVersion/PatchVersion`) [S]; Windows registry `HKLM\SOFTWARE\EpicGames\Unreal Engine\5.8\InstalledDirectory` and `C:\ProgramData\Epic\UnrealEngineLauncher\LauncherInstalled.dat` [M]; the `.uproject` `"EngineAssociation": "5.8"`.
- Alternative for full automation: the GitHub source build (Epic-linked GitHub account required: `Setup.bat` then `GenerateProjectFiles.bat` then build `UnrealEditor`), hours of compile and ~200+ GB - not recommended for this project [M].

### 4.3 Visual Studio on Windows

- UE 5.8 projects in 2026 are being built with **Visual Studio 2026** (VS 18.x) - multiple 2026 repos state "Install Unreal Engine 5.8.1 and Visual Studio 2026 with C++ game-development support" and link Epic's 5.8 "Setting Up Visual Studio" page; Epic's own 2026 EOS sample ships a UBT-generated `.vsconfig` requesting the **MSVC 14.50 (VS 2026)** toolset plus LLVM/Clang [P, EpicGames/EOS-Getting-Started]. Whether VS 2022 17.x is still accepted by 5.8's UBT is not verified here (older samples, e.g. CARLA, request MSVC 14.38 / VS 17.8). Safe choice: **VS 2026 Community** with the components below; if Epic's 5.8 page says otherwise, follow it.
- Component/workload IDs (confirmed in the VS 2026 component directory; "Game development with C++" = `Microsoft.VisualStudio.Workload.NativeGame`, with recommended `Component.Unreal.Ide` ("Visual Studio Tools for Unreal Engine"), `Component.Unreal.Debugger`, `Microsoft.Net.Component.4.6.2.TargetingPack`, optional `Microsoft.VisualStudio.Component.Unreal.TestAdapter`, `Component.Unreal` ("Unreal Engine installer"), `Microsoft.VisualStudio.Component.Windows11SDK.22621`) [P, learn.microsoft.com workload-component-id-vs-community]. Epic's EOS sample `.vsconfig` (verbatim) [P]:
  ```json
  {
    "version": "1.0",
    "components": [
      "Component.Unreal.Debugger",
      "Component.Unreal.Ide",
      "Microsoft.Net.Component.4.6.2.TargetingPack",
      "Microsoft.VisualStudio.Component.VC.14.50.18.0.ATL",
      "Microsoft.VisualStudio.Component.VC.14.50.18.0.x86.x64",
      "Microsoft.VisualStudio.Component.VC.Llvm.Clang",
      "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
      "Microsoft.VisualStudio.Component.Windows11SDK.22621",
      "Microsoft.VisualStudio.Workload.CoreEditor",
      "Microsoft.VisualStudio.Workload.ManagedDesktop",
      "Microsoft.VisualStudio.Workload.NativeDesktop",
      "Microsoft.VisualStudio.Workload.NativeGame"
    ]
  }
  ```
  **Does UE ship a `.vsconfig`?** UnrealBuildTool writes one next to the generated `.sln` (identical structure appears in Epic's EOS sample, CARLA, SpacetimeDB, RTI samples, all under the project root next to the solution) - treat as "UBT-generated on `-projectfiles`" [P evidence, inference]. The engine install itself was not inspectable here.
- Unattended install (command-line parameters page [P]):
  ```
  REM VS 2026 Community via winget + vsconfig
  winget install --id Microsoft.VisualStudio.Community -e --override "--passive --norestart --config C:\dev\XRCampus\cowork\ue.vsconfig"
  REM or the bootstrapper directly (latest Stable 18.x); --wait only works on the bootstrapper
  curl -L -o vs_community.exe https://aka.ms/vs/stable/vs_community.exe
  vs_community.exe --passive --norestart --wait --config C:\dev\XRCampus\cowork\ue.vsconfig
  REM VS 2022 equivalents: winget id Microsoft.VisualStudio.2022.Community ; bootstrapper https://aka.ms/vs/17/release/vs_community.exe
  REM modify an existing install:
  "C:\Program Files (x86)\Microsoft Visual Studio\Installer\setup.exe" modify --installPath "C:\Program Files\Microsoft Visual Studio\18\Community" --config C:\dev\XRCampus\cowork\ue.vsconfig --passive --norestart
  ```
  Exit codes: 0 ok, 3010 ok-needs-reboot, 1641 reboot initiated, 740 elevation required, 8010 OS unsupported [P]. The installer needs admin; `--quiet` is not available to standard users [P].
- .NET: UBT on Launcher builds uses the dotnet runtime bundled under `Engine/Binaries/ThirdParty/DotNet`; the 4.6.2 targeting pack above is what UBT asks for [M].
- Optional in-editor plugin for VS Blueprint debugging: `microsoft/vc-ue-extensions` (install via *Project > Configure Tools for Unreal Engine* in VS) [P].

### 4.4 macOS / Xcode

- UE 5.8 renders on **Apple Silicon only** (Intel rendering removed); Lumen SWRT/TSR on M1+, Nanite/VSM Beta on M2+, Lumen HWRT and MegaLights Experimental on M2+; path tracing via Metal ray shaders wants macOS 26.4+ [S, Epic macOS requirements page as of 2026-09-24].
- Xcode: Epic's 5.8 macOS page (as saved 2026-09-24) says **Xcode 26.0 minimum, 26.1.1 recommended, 26.4 not compatible**, while the 5.8 SDK table disagrees - unresolved in the source; Blueprint-only projects need no Xcode, a C++ project does [S]. Steps: install full Xcode from the App Store (not just CLT), `sudo xcode-select -s /Applications/Xcode.app`, `sudo xcodebuild -license accept`, launch Xcode once for components [M, standard].
- Mac binaries: `Engine/Binaries/Mac/UnrealEditor.app`, `UnrealEditor-Cmd`, `Engine/Build/BatchFiles/RunUAT.sh`, `Engine/Build/BatchFiles/Mac/Build.sh`; use POSIX paths and keep the project in a path **without spaces** (UAT/cook quoting issues) [S + C].

### 4.5 Command-line build / project files / cook (all paths assume Launcher install `UE_5.8`)

Generate project files [M, long-standing UBT syntax - verify once]:
```
REM Windows, Launcher ("Rocket") build:
"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\DotNET\UnrealBuildTool\UnrealBuildTool.exe" -projectfiles -project="C:\dev\XRCampus\XRCampus.uproject" -game -rocket -progress
REM or (same thing via the version selector):
"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealVersionSelector.exe" /projectfiles "C:\dev\XRCampus\XRCampus.uproject"
# macOS:
"/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/RunUBT.sh" -projectfiles -project="/Users/ev/dev/XRCampus/XRCampus.uproject" -game -rocket -progress
```
Build the editor target [M, standard]:
```
"C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat" XRCampusEditor Win64 Development -Project="C:\dev\XRCampus\XRCampus.uproject" -WaitMutex -FromMsBuild
"/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh" XRCampusEditor Mac Development -Project="/Users/ev/dev/XRCampus/XRCampus.uproject"
```
Cook + package with UAT (canonical, from the 5.8 docs via [S]):
```
"C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\RunUAT.bat" BuildCookRun -project="C:\dev\XRCampus\XRCampus.uproject" -noP4 -platform=Win64 -clientconfig=Development -build -cook -allmaps -stage -pak -iostore -archive -archivedirectory="C:\builds\XRCampus"
"/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/RunUAT.sh" BuildCookRun -project="/Users/ev/dev/XRCampus/XRCampus.uproject" -noP4 -platform=Mac -clientconfig=Development -build -cook -allmaps -stage -pak -iostore -archive -archivedirectory="/Users/ev/builds/XRCampus"
```
5.7/5.8 cook notes [S]: cooking inside the editor process is deprecated (removed in 5.9) - always cook via UAT/commandlet; Zen is the default cooked store for new 5.8 projects (set `[Zen.AutoLaunch] LimitProcessLifetime=false` for CI); `-cookincremental` (Beta) speeds iteration; `-RunAssetValidation -RunMapValidation -ValidationErrorsAreFatal` for gating; `-DDC=None` was removed in 5.8. First editor launch compiles thousands of shaders - expect 10-40 minutes before the first headless job returns on a fresh machine; run the probe job (§3.0) first to warm the DDC.

---

## 5. Fab, Quixel Megascans and free photoreal sources (October 2026)

Fab/Epic pages were unreachable from this container, so this section is [M] unless tagged. Cowork should confirm the current Fab license terms in the Fab plugin / fab.com before relying on them.

- Fab (launched 22 Oct 2024) replaced the UE Marketplace, Quixel, Sketchfab Store and ArtStation Marketplace. All Megascans were free to claim until 31 Dec 2024; **since 2025 Megascans are paid on Fab except a free subset**, and anything claimed before 2025 stays in your library. Fab's "Standard License" has *Personal* (revenue cap) and *Professional* tiers; some items are CC. Epic's own content (samples, Megascans Trees/Electric Dreams-style packs, "free for the month") is free under the UE EULA [M].
- In-editor: the **Fab plugin** ships with UE 5.5+ (Edit > Plugins > "Fab"; *Window > Fab*); drag-and-drop imports Megascans with Nanite; it replaced the Quixel Bridge plugin, and the standalone Bridge app was sunset [M]. There is no public Fab CLI; scripted bulk import is "download via the Fab panel, then Interchange-import the files" or use Fab's web library downloads.
- Verified free photoreal sources: **Poly Haven** - HDRIs, PBR texture sets, models, all **CC0** ("never require attribution"), API `https://api.polyhaven.com` with `/types`, `/assets`, `/search`, `/info/{id}`, `/files/{id}` (swagger in Poly-Haven/Public-API; "Powered by Poly Haven" credit required only when building on the live API) [P]. Others [M]: ambientCG (CC0 PBR), Smithsonian Open Access 3D (CC0 scans - museum-grade for the galleries), Three D Scans / Scan the World (CC0 / CC-BY statue scans), Sketchfab CC assets (check each license; BM collections are CC BY-NC-SA), KhronosGroup/glTF-Sample-Assets, Quaternius and Kenney (CC0 props), NASA 3D resources. Interchange imports GLB/glTF/FBX/OBJ directly (§3.1).

---

## 6. Open items Cowork must verify on the target machine (copy into the runbook)

1. Which OS/GPU: `systeminfo` / `dxdiag` or `sw_vers; sysctl -n machdep.cpu.brand_string; system_profiler SPDisplaysDataType`. Lumen HWRT/MegaLights need RTX-class or M2+.
2. Engine version offered by the Launcher (5.8.x) and the exact Epic docs pages: "Setting Up Visual Studio" (`?application_version=5.8`), "Hardware and Software Specifications", "macOS development requirements", "Unreal MCP".
3. Probe job output (§3.0): every name tagged [M] above, `new_level` signature, `Intermediate/PythonStub/unreal.py` present.
4. `.vsconfig` generated next to `XRCampus.sln` after `-projectfiles`; diff against `cowork/ue.vsconfig`.
5. Remote Control 5.8 allow-list setting names; `ModelContextProtocol` toolset plugin names.
6. Fab license text for any Megascans used; Poly Haven needs none.

## 7. Sources

Claude [P]: support.claude.com articles 13345190 (Get started with Claude Cowork), 14479288 (architecture overview), 13364135 (use safely), 14128542 (computer use), 15520349 (web/desktop/mobile), 13854387 (scheduled tasks), 13947068 (Dispatch), 14116274 (projects), 12512176 / 12512180 (skills), 13837440 / 14328846 (plugins, directory), 10949351 (local MCP servers / desktop extensions), 14552382 (Claude Code first day), 11145838 (Claude Code on Pro/Max); claude.com/product/cowork.
Microsoft [P]: learn.microsoft.com/visualstudio/install/workload-component-id-vs-community (VS 2026 directory), /visualstudio/install/use-command-line-parameters-to-install-visual-studio, /visualstudio/gamedev/unreal/get-started/vs-tools-unreal-install.
GitHub [P]: EpicGames/EOS-Getting-Started `OnlineSubsystemEOS/.vsconfig`; carla-simulator/carla `Unreal/CarlaUnreal/.vsconfig`; microsoft/winget-pkgs `manifests/e/EpicGames/EpicGamesLauncher/1.3.210.0`; Homebrew/homebrew-cask `Casks/e/epic-games.rb`; derrod/legendary README; Poly-Haven/Public-API README + swagger.yml; READMEs of chongdashu/unreal-mcp, flopperam/unreal-engine-mcp, ChiR24/Unreal_mcp, db-lyon/ue-mcp, tumourlove/monolith, runreal/unreal-mcp (GitHub repo metadata for stars/push dates).
UE 5.8 knowledge bases [S]: scenario-labs/skills `skills/game-engines/unreal/scenario-unreal-expert/references/{ue-5.8-traps,python-reliability,toolkit-map,sources}.md` (built from UE 5.8 doc pages retrieved 2026-09-24 and Epic talks incl. youtube k0tgmrBuIJc, lDf_y-YPELo, 0guOMTiwmhk); kevinpbuckley/unreal-engine-skills `skills/core/{ue-importing-content,ue-levels-and-world-partition,ue-editor-scripting-and-python,ue-packaging-and-deployment}/SKILL.md` (engine-version 5.8, cites engine headers and these official pages: dev.epicgames.com/documentation/unreal-engine/scripting-the-unreal-editor-using-python, .../PythonAPI, .../interchange-framework-in-unreal-engine, .../importing-assets-using-interchange-in-unreal-engine, .../world-partition-in-unreal-engine, .../level-instancing-in-unreal-engine, .../build-operations-cooking-packaging-deploying-and-running-projects-in-unreal-engine).
Code-search corroboration [C]: genex-games/genex-desktop, OpenDCAI/GameFactory-3A, oh-ashen-one/invincible, EpicGames/BlenderTools (send2ue), carla-simulator/carla, GenOrca/unreal-mcp, BellowAverage/OrionUnrealFramework, spear-sim/spear, obilang/UE_CELevelImporter, bralkor/unreal_python_recipe_book, linranff/GTA_SZ (Mac `UnrealEditor-Cmd` + `-ExecutePythonScript`), satisfactorymodding/SatisfactoryModLoader (`Interchange.FeatureFlags.Import.FBX`), Cosys-Lab/Cosys-AirSim and ToolTech/CSWUnreal (UE 5.8 + VS 2026).

---

## Critic notes (2026-10-16, completeness critic; see `../critic.md`)

1. **§1.1 Cowork execution model re-verified on support.claude.com (2026-10-16):** new Cowork sessions run code "in an isolated environment on Anthropic's servers"; local sessions exist only for tasks started before October 6 (Pro/Max); a cloud session reaches the computer only while the Claude Desktop app is open, only in connected folders, each local tool call permission-checked; "Local connectors and plugins that include local MCP servers work through the desktop app only"; computer use = Pro/Max, beta, macOS/Windows, asks per application, machine must stay awake; Claude Code installs via curl (macOS/Linux/WSL), PowerShell (Windows) or `brew install --cask claude-code` and "will always ask before changing a file or running a command". ⇒ **Runbook executor = Claude Code on the host (route 1)**; route 2 (Desktop Commander local MCP through the desktop app) is plausible per the surfaces article but must be tested on day 1; route 3 (computer use) for GUI-only steps.
2. §3.1 Interchange pipeline asset paths are **verified** from the saved 5.8 `BaseEngine.ini`: `/Interchange/Pipelines/DefaultAssetsPipeline.DefaultAssetsPipeline` (so the `[M-verify]` on `duplicate_asset(...)` source path is cleared), plus `DefaultGLTFAssetsPipeline`, `DefaultGLTFPipeline`, `DefaultFBXOBJAssetsPipeline`, `DefaultSceneAssetsPipeline`, `DefaultSceneLevelPipeline`, `DefaultGLTFSceneAssetsPipeline`, `DefaultTexturePipeline`, `DefaultMaterialPipeline`; `GenericPipelineClass=/Script/InterchangePipelines.InterchangeGenericAssetsPipeline`; translators `/Script/InterchangeImport.Interchange{GLTF,Fbx,OBJ,MaterialX}Translator`. `[Zen.AutoLaunch] LimitProcessLifetime` is a real key (default True in 5.8).
3. Corroborated from Epic's own `BlenderTools/send2ue/dependencies/unreal.py` (fetched 2026-10-16, `dl2/`): `unreal.AssetImportTask` with `automated` / `replace_existing` and `AssetToolsHelpers.get_asset_tools().import_asset_tasks`, `SubobjectDataSubsystem.add_new_subobject` + `k2_gather_subobject_data_for_blueprint`, `EditorActorSubsystem.spawn_actor_from_object`, `StaticMeshEditorSubsystem`, `set_editor_property`. send2ue does **not** use `InterchangeManager`, `ImportAssetParameters`, `get_objects()`, DataTable or Nanite-settings calls — those stay at [S]/[C] and go in the probe job. The runreal README confirms Remote Execution is a Python-plugin project setting with bind address 127.0.0.1 (0.0.0.0 to expose) but does not print the 6766/6776 ports.
4. dev.epicgames.com could not be reached from this container either (DNS), and GitHub code search is refused for this session, so none of the [M] items were upgraded. The probe job in §3.0 must additionally test: `LevelEditorSubsystem.new_level` signature, `ImportAssetParameters` field names, `InterchangeManager.*`, `DataTableFactory.struct`, `DataTableFunctionLibrary.fill_data_table_from_json_string` return type, `MaterialEditingLibrary.*`, `MeshNaniteSettings` + `StaticMeshEditorSubsystem.set_nanite_settings`, `AutomationLibrary.take_high_res_screenshot`, `register_ticker_callback`, `LevelInstance.world_asset`, `Rotator` order, the Python stub path, Remote Control 5.8 allow-list settings, MCP toolset plugin names, and the list of `*.uplugin` names (`MetaHuman*`, `ModelContextProtocol`, `GeometryScripting`, `PixelStreaming2`, `Interchange*`, `PBIK`, `IKRig`, `ControlRig`, `OpenXRHandTracking`, `Water`, `CommonUI`, `AnimationBudgetAllocator`, `PoseSearch`).
5. §4.3: MS Learn (fetched) confirms the VS 2026 (18.0) component directory entries used in the `.vsconfig` and that VS Tools for Unreal supports VS 2022 17.7+ and UE 5.0+; whether 5.8's UBT accepts VS 2022 is still unverified → default to VS 2026, follow Epic's 5.8 page on the machine.
6. `research/dl/*` (scenario-labs / kevinpbuckley) describe a **third-party toolkit** (`ue_run`, `ue_env`, `ue_review`, …) and *their author's* Mac (M5 Max, macOS 26.5.1). None of that exists in this project; the user's machine is unknown. Use those files as reference only; no script may call `ue_*` helpers.
