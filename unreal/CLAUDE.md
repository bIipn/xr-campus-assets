# Claude instructions for `unreal/` (Walk the Archive in Unreal Engine 5.8)

You are working on Ev's own computer to set up and grow the Unreal Engine 5.8 version of the Walk the Archive campus.
Follow `COWORK.md` step by step. It is the runbook, and every step has a success check.

## Where things are
- `contract/CONTRACT.md` + `contract/structs.json`: the rules every file follows (names, paths, data shapes). Read before changing code.
- `contract/CPP_API.md`: every C++ class, function and property.
- `WalkTheArchive/`: the Unreal project (`Source/` C++, `Config/` ini, `Content/Python/wta_setup/` editor setup, `Scripts/setup_project.py` entry, `Data/` DataTable JSON).
- `Pipeline/`: how the web campus was exported (already done; outputs committed in `Pipeline/out/ue/`).
- `Tools/`: preflight, install, build, setup, play and package scripts (`win/*.ps1`, `mac/*.sh`, `common/*.py`).
- `docs/`: decisions, roadmap, MetaHumans, delivery, look-dev; `docs/reference/` has the research and specs, with sources.

## Rules
- Run commands on this machine (Claude Code locally, or Cowork's local terminal tool). Use computer use only for GUI-only steps.
- Ev signs in to every account personally. Never type passwords or 2FA codes.
- Ask before installing software, before anything that needs admin rights, and before deleting files.
- Never commit generated Unreal content (`WalkTheArchive/Content/*` except `Content/Python`, `Binaries`, `Intermediate`, `Saved`, `DerivedDataCache`). `.gitignore` blocks them; don't force-add.
- Fix build or setup errors with the smallest change that follows the contract, keep `contract/CPP_API.md` in sync, commit each fix with a clear message, and push to `unreal5-port`.
- Prefer verifying an Unreal API on this machine (the `probe` step, `help(unreal.X)`, or the engine headers under `Engine/Source`) over guessing.
- Report progress to Ev in one or two plain sentences per step. Show screenshots after visual changes.
- Ev's style: neat, aesthetic results. When Ev asks a yes/no question, put "Yes" or "No" at the very top of the answer.
