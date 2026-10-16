"""Step 9: make sure the project ini files point at the campus.

Config/DefaultEngine.ini  [/Script/EngineSettings.GameMapsSettings]  GameDefaultMap, EditorStartupMap,
                          GlobalDefaultGameMode (set); [/Script/NavigationSystem.RecastNavMesh]
                          RuntimeGeneration=Dynamic (added only when the project has not chosen a value).
Config/DefaultGame.ini    [/Script/WalkTheArchive.WTASettings] one DataTable path per table (only added when
                          missing, so the C++ defaults written there are never overwritten).
The ini is edited as text: keys are replaced in place, missing sections are appended, everything else is
kept byte for byte. Nothing here needs the editor, so the step also works outside Unreal.
"""
import os

from . import log
from . import paths

STEP = "project_settings"

LEVEL_REF = paths.LEVEL_PATH + "." + paths.LEVEL_NAME
GAME_MAPS_SECTION = "/Script/EngineSettings.GameMapsSettings"
RECAST_SECTION = "/Script/NavigationSystem.RecastNavMesh"
WTA_SETTINGS_SECTION = "/Script/WalkTheArchive.WTASettings"

ENGINE_KEYS = {
    "GameDefaultMap": LEVEL_REF,
    "EditorStartupMap": LEVEL_REF,
    "GlobalDefaultGameMode": paths.GAME_MODE_PATH,
}
NAV_KEYS = {"RuntimeGeneration": "Dynamic"}


def read_lines(path):
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8-sig") as fh:
        return fh.read().splitlines()


def write_lines(path, lines):
    paths.ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def section_bounds(lines, section):
    """(start, end) line indexes of '[section]' (end exclusive) or None."""
    header = "[%s]" % section
    start = None
    for i, line in enumerate(lines):
        if line.strip() == header:
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        s = lines[j].strip()
        if s.startswith("[") and s.endswith("]"):
            end = j
            break
    return start, end


def get_value(lines, section, key):
    b = section_bounds(lines, section)
    if b is None:
        return None
    for i in range(b[0] + 1, b[1]):
        s = lines[i].strip()
        if s.startswith(key + "="):
            return s[len(key) + 1:].strip()
    return None


def set_value(lines, section, key, value, only_if_missing=False):
    """Returns 'kept', 'replaced' or 'added'."""
    b = section_bounds(lines, section)
    if b is None:
        if lines and lines[-1].strip() != "":
            lines.append("")
        lines.append("[%s]" % section)
        lines.append("%s=%s" % (key, value))
        return "added"
    start, end = b
    for i in range(start + 1, end):
        s = lines[i].strip()
        if s.startswith(key + "="):
            if s[len(key) + 1:].strip() == value or only_if_missing:
                return "kept"
            lines[i] = "%s=%s" % (key, value)
            return "replaced"
    insert_at = end
    while insert_at > start + 1 and lines[insert_at - 1].strip() == "":
        insert_at -= 1
    lines.insert(insert_at, "%s=%s" % (key, value))
    return "added"


def table_settings():
    structs = paths.read_json(paths.STRUCTS_JSON).get("structs", {})
    out = {}
    for spec in structs.values():
        table = spec.get("table")
        if spec.get("row") and table:
            name = table[3:] if table.startswith("DT_") else table
            out[name] = "%s.%s" % (paths.table_asset_path(table), table)
    return out


def run():
    report = {"engine_ini": paths.DEFAULT_ENGINE_INI, "game_ini": paths.DEFAULT_GAME_INI, "changes": {}}

    lines = read_lines(paths.DEFAULT_ENGINE_INI)
    existed = bool(lines)
    before = {k: get_value(lines, GAME_MAPS_SECTION, k) for k in ENGINE_KEYS}
    changed = False
    for key, value in ENGINE_KEYS.items():
        state = set_value(lines, GAME_MAPS_SECTION, key, value)
        report["changes"][key] = state
        changed = changed or state != "kept"
    for key, value in NAV_KEYS.items():
        # Add-only: a value the project already chose (for example Static) is kept and reported.
        state = set_value(lines, RECAST_SECTION, key, value, only_if_missing=True)
        report["changes"]["RecastNavMesh." + key] = state
        changed = changed or state != "kept"
    report["nav_runtime_generation"] = get_value(lines, RECAST_SECTION, "RuntimeGeneration")
    if changed or not existed:
        write_lines(paths.DEFAULT_ENGINE_INI, lines)
    report["engine_ini_existed"] = existed
    report["before"] = before

    game_lines = read_lines(paths.DEFAULT_GAME_INI)
    game_existed = bool(game_lines)
    game_changed = False
    added = []
    try:
        for name, value in table_settings().items():
            state = set_value(game_lines, WTA_SETTINGS_SECTION, name, value, only_if_missing=True)
            if state != "kept":
                added.append(name)
                game_changed = True
    except Exception as exc:
        log.warn("could not read structs.json for WTASettings: %s" % exc)
    if game_changed or not game_existed:
        write_lines(paths.DEFAULT_GAME_INI, game_lines)
    report["wta_settings_added"] = added

    after = read_lines(paths.DEFAULT_ENGINE_INI)
    verified = {k: get_value(after, GAME_MAPS_SECTION, k) == v for k, v in ENGINE_KEYS.items()}
    report["verified"] = verified
    report["ok"] = all(verified.values())
    if not report["ok"]:
        report["error"] = "ini keys not verified: %s" % [k for k, v in verified.items() if not v]
    return report
