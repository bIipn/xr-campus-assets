"""Editor-Python setup pipeline for Walk the Archive (Unreal Engine 5.8).

Each step module exposes run() -> dict with an 'ok' key. pipeline.run(steps) runs them in
contract order and prints exactly one 'WTA_RESULT {json}' line per step.
Run through Scripts/setup_project.py inside UnrealEditor-Cmd (see contract section 6).
"""

VERSION = "0.1.0"

# Step order fixed by the contract (section 6).
STEPS = [
    "probe",
    "import_meshes",
    "import_art",
    "data_tables",
    "build_level",
    "lighting",
    "actors",
    "navmesh",
    "project_settings",
    "verify",
]
