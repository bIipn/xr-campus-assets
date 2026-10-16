"""Step 10: verify the campus level against the data and take reference screenshots.

Checks: actor counts per WTA class versus the DataTable JSON, every DataTable non-empty, every imported
mesh folder and art texture present, L_Campus saved on disk. Screenshots (lobby, reading room, yard)
are requested through AutomationLibrary.take_high_res_screenshot into Saved/WTA_Shots/; they finish on
later editor ticks, so a headless run may exit before the files land. Set WTA_SHOTS=0 to skip them.
"""
import os

import unreal

from . import log
from . import paths
from . import util

STEP = "verify"

ACTOR_CLASSES = {
    "WTARoomVolume": "Rooms.json",
    "WTAExhibitActor": "Exhibits.json",
    "WTABookActor": "Books.json",
    "WTAStationActor": "Stations.json",
    "WTARideActor": "Rides.json",
    "WTATokenActor": "Tokens.json",
    "WTAStaffNPC": "Staff.json",
    "WTAWaxStageActor": "WaxScenes.json",
}

VIEWPOINTS = [("lobby", ["lobby"]), ("reading_room", ["library", "lib", "window"]), ("yard", ["yard", "field"])]


def expected_books():
    """Books whose book__<id> mesh exists (the actors step skips the others)."""
    folders = [paths.campus_asset_path("LibraryShell"), paths.campus_asset_path("School"), paths.CAMPUS_PATH]
    count = 0
    for row in util.data_rows("Books.json"):
        _p, mesh = util.find_tagged_mesh("book", row["Name"], folders)
        if mesh is not None:
            count += 1
    return count


def check_actors(report):
    counts = {}
    for actor in util.all_actors():
        name = util.actor_class_name(actor)
        counts[name] = counts.get(name, 0) + 1
    errors = []
    table = {}
    for cls, json_file in ACTOR_CLASSES.items():
        try:
            expected = expected_books() if cls == "WTABookActor" else len(util.data_rows(json_file))
        except Exception as exc:
            expected = -1
            errors.append("%s unreadable: %s" % (json_file, exc))
        actual = counts.get(cls, 0)
        table[cls] = {"expected": expected, "actual": actual}
        if expected >= 0 and actual != expected:
            errors.append("%s: %d actors, %d rows" % (cls, actual, expected))
    table["StaticMeshActor"] = {"actual": counts.get("StaticMeshActor", 0)}
    table["PlayerStart"] = {"actual": counts.get("PlayerStart", 0), "expected": 1}
    if counts.get("PlayerStart", 0) < 1:
        errors.append("no PlayerStart")
    table["lights"] = {"actual": len(util.find_actors(tag=util.step_tag("lighting")))}
    table["NavMeshBoundsVolume"] = {"actual": counts.get("NavMeshBoundsVolume", 0), "expected": 1}
    if counts.get("NavMeshBoundsVolume", 0) < 1:
        errors.append("no NavMeshBoundsVolume")
    report["actors"] = table
    return errors


def check_tables(report):
    errors = []
    tables = {}
    structs = paths.read_json(paths.STRUCTS_JSON).get("structs", {})
    for spec in structs.values():
        table = spec.get("table")
        if not (spec.get("row") and table):
            continue
        path = paths.table_asset_path(table)
        dt = util.assets().load(path) if util.assets().exists(path) else None
        rows = 0
        if dt is not None:
            try:
                rows = len(list(unreal.DataTableFunctionLibrary.get_data_table_row_names(dt)))
            except Exception:
                try:
                    rows = len(list(dt.get_row_names()))
                except Exception:
                    rows = -1
        tables[table] = rows
        if dt is None:
            errors.append("%s missing" % table)
        elif rows == 0:
            errors.append("%s is empty" % table)
    report["tables"] = tables
    return errors


def check_assets(report):
    errors = []
    meshes = {}
    for asset, _glb in paths.mesh_assets():
        n = len(util.static_meshes_under(paths.campus_asset_path(asset)))
        meshes[asset] = n
        if n == 0:
            errors.append("no meshes under %s" % paths.campus_asset_path(asset))
    report["meshes"] = meshes
    art_missing = []
    art_count = 0
    if os.path.isdir(paths.ART_DIR):
        for png in sorted(os.listdir(paths.ART_DIR)):
            if not png.lower().endswith(".png"):
                continue
            art_id = os.path.splitext(png)[0]
            if util.assets().exists(paths.art_asset_path(art_id)):
                art_count += 1
            else:
                art_missing.append(art_id)
    report["art"] = {"present": art_count, "missing": art_missing}
    if art_missing:
        errors.append("art textures missing: %s" % ", ".join(art_missing))
    report["level_asset"] = util.assets().exists(paths.LEVEL_PATH)
    report["level_umap"] = os.path.isfile(paths.LEVEL_UMAP)
    if not report["level_asset"]:
        errors.append("%s not registered" % paths.LEVEL_PATH)
    if not report["level_umap"]:
        errors.append("%s not on disk (level not saved)" % paths.LEVEL_UMAP)
    return errors


def check_token_alignment(report):
    """Contract section 2: imported token meshes must sit where their DT_Tokens rows say.

    Ride-gated tokens (RideGate set: t-coaster, t-drop, t-dive) are modelled on the ride itself while their
    row holds the ride location, so only the static tokens decide the verdict; the gated ones are reported.
    """
    checks = {}
    errors = []
    try:
        for row in util.data_rows("Tokens.json"):
            name = row["Name"]
            loc = util.xyz(row["Location"])
            gated = str(row.get("RideGate", "") or "") not in ("", "None")
            _p, mesh = util.find_tagged_mesh("token", name)
            bounds = util.mesh_bounds(mesh) if mesh is not None else None
            if bounds is None:
                checks[name] = {"mesh": "missing", "gated": gated}
                continue
            c = bounds[0]
            dist = ((c[0] - loc[0]) ** 2 + (c[1] - loc[1]) ** 2 + (c[2] - loc[2]) ** 2) ** 0.5
            checks[name] = {"mesh_centre": [round(v, 1) for v in c], "row": list(loc),
                            "distance_cm": round(dist, 1), "gated": gated}
            if not gated and dist > 150.0:
                errors.append("token__%s is %.0f cm from its DT_Tokens row: check the import axes"
                              % (name.replace("-", "_"), dist))
        static = [k for k, v in checks.items() if "distance_cm" in v and not v["gated"]]
        if not static:
            errors.append("no static token mesh found to check the import axes")
    except Exception as exc:
        checks["error"] = str(exc)
    report["token_check"] = checks
    return errors


def viewpoint(keys):
    places = paths.read_json(paths.LAYOUT_JSON).get("places", {})
    for key in keys:
        if key in places and "ue" in places[key]:
            ue = places[key]["ue"]
            r = ue.get("rotation_deg", {})
            return list(ue.get("location_cm", [0, 0, 162])), (float(r.get("pitch", 0)), float(r.get("yaw", 0)), 0.0)
    return None, None


def take_screenshots(report):
    if not util.env_flag("WTA_SHOTS", True):
        report["screenshots"] = "skipped (WTA_SHOTS=0)"
        return
    lib = getattr(unreal, "AutomationLibrary", None)
    ues = util.editor_subsystem("UnrealEditorSubsystem")
    if lib is None or ues is None or not hasattr(lib, "take_high_res_screenshot"):
        report["screenshots"] = "skipped (AutomationLibrary or UnrealEditorSubsystem missing)"
        return
    paths.ensure_dir(paths.SHOTS_DIR)
    shots = {}
    for name, keys in VIEWPOINTS:
        loc, rotd = viewpoint(keys)
        if loc is None:
            shots[name] = "no viewpoint in layout.json"
            continue
        out = os.path.join(paths.SHOTS_DIR, name + ".png")
        try:
            ues.set_level_viewport_camera_info(util.vec(*loc), util.rot(*rotd))
            lib.take_high_res_screenshot(1920, 1080, out)
            shots[name] = "requested: " + out
        except Exception as exc:
            shots[name] = "failed: %s" % exc
    report["screenshots"] = shots
    report["screenshot_note"] = "files land on later editor ticks; a headless run may exit first"


def run():
    util.wait_for_asset_registry()
    report = {}
    errors = []
    try:
        util.ensure_level_loaded()
    except Exception as exc:
        errors.append(str(exc))
    errors += check_assets(report)
    errors += check_tables(report)
    if not errors or report.get("level_asset"):
        errors += check_actors(report)
    errors += check_token_alignment(report)
    try:
        take_screenshots(report)
    except Exception as exc:
        report["screenshots"] = "failed: %s" % exc
    report["ok"] = not errors
    if errors:
        report["error"] = "; ".join(errors)[:1500]
        report["errors"] = errors
    return report
