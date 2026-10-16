"""Step 7: spawn the WalkTheArchive C++ actors from the DataTable JSON (contract table 4.5).

  AWTARoomVolume     one per Rooms.json row, centre and half extent from BoundsMin/Max
  AWTAExhibitActor   one per Exhibits.json row at Location/Yaw, PickExtent (8, w/2, h/2)
  AWTABookActor      one per Books.json row at the book__<id> mesh bounds (skipped with a warning if absent)
  AWTAStationActor   one per Stations.json row, extent 80
  AWTARideActor      one per Rides.json row, extent 300
  AWTATokenActor     one per Tokens.json row at the token__<id> mesh centre, else Location
  AWTAStaffNPC       one per Staff.json row, capsule centre = floor + 90
  AWTAWaxStageActor  one per WaxScenes.json row, trigger (280, 200, 200) in front of the stage
Properties are set with set_editor_property using the snake_case names from the contract. Every actor is
tagged WTA_Setup / WTA_actors and filed under WTA/<Kind>.
"""
import unreal

from . import log
from . import paths
from . import util

STEP = "actors"
CAPSULE_HALF_HEIGHT = 90.0


def spawn_wta(class_name, location, yaw, label, folder, props):
    cls = util.load_wta_class(class_name)
    if cls is None:
        raise RuntimeError("class %s not loaded (build_editor first)" % paths.script_class(class_name))
    actor = util.spawn_class(cls, location, (0.0, float(yaw), 0.0), step=STEP, label=label, folder="WTA/" + folder)
    failed = util.set_props(actor, props, label=label)
    return actor, failed


def half_extent(ex, ey, ez):
    return unreal.Vector(float(ex), float(ey), float(ez))


def spawn_rooms(report):
    failed_props, count = [], 0
    for row in util.data_rows("Rooms.json"):
        mn, mx = util.xyz(row["BoundsMin"]), util.xyz(row["BoundsMax"])
        ext = [max((mx[i] - mn[i]) / 2.0, 0.0) for i in range(3)]
        if ext[2] < 50.0:
            ext[2] = 250.0   # the yard has no ceiling in the data: give the volume some height
        centre = [mn[i] + ext[i] for i in range(3)]
        _a, failed = spawn_wta("WTARoomVolume", centre, 0.0, "Room_%s" % row["Name"], "Rooms", {
            "room_id": row["Name"],
            "extent": half_extent(*ext),
        })
        failed_props += failed
        count += 1
    report["rooms"] = count
    return failed_props


def spawn_exhibits(report):
    failed_props, count = [], 0
    for row in util.data_rows("Exhibits.json"):
        loc = util.xyz(row["Location"])
        size = row.get("Size", {"X": 100.0, "Y": 100.0})
        w, h = float(size.get("X", 100.0)), float(size.get("Y", 100.0))
        _a, failed = spawn_wta("WTAExhibitActor", loc, row.get("Yaw", 0.0), "Exhibit_%s" % row["Name"], "Exhibits", {
            "item_id": row["Name"],
            "pick_extent": half_extent(8.0, w / 2.0, h / 2.0),
        })
        failed_props += failed
        count += 1
    report["exhibits"] = count
    return failed_props


def spawn_books(report):
    failed_props, count, skipped = [], 0, []
    folders = [paths.campus_asset_path("LibraryShell"), paths.campus_asset_path("School"), paths.CAMPUS_PATH]
    for row in util.data_rows("Books.json"):
        _path, mesh = util.find_tagged_mesh("book", row["Name"], folders)
        bounds = util.mesh_bounds(mesh) if mesh is not None else None
        if bounds is None:
            skipped.append(row["Name"])
            log.warn("book mesh book__%s not found; AWTABookActor %s skipped" % (row["Name"].replace("-", "_"), row["Name"]))
            continue
        centre, ext = bounds
        pick = [max(e + 6.0, 12.0) for e in ext]
        _a, failed = spawn_wta("WTABookActor", centre, 0.0, "Book_%s" % row["Name"], "Books", {
            "book_id": row["Name"],
            "pick_extent": half_extent(*pick),
        })
        failed_props += failed
        count += 1
    report["books"] = count
    report["books_skipped"] = skipped
    return failed_props


def spawn_stations(report):
    failed_props, count = [], 0
    for row in util.data_rows("Stations.json"):
        _a, failed = spawn_wta("WTAStationActor", util.xyz(row["Location"]), 0.0, "Station_%s" % row["Name"], "Stations", {
            "station_id": row["Name"],
            "pick_extent": half_extent(80.0, 80.0, 80.0),
        })
        failed_props += failed
        count += 1
    report["stations"] = count
    return failed_props


def spawn_rides(report):
    failed_props, count = [], 0
    for row in util.data_rows("Rides.json"):
        _a, failed = spawn_wta("WTARideActor", util.xyz(row["Location"]), 0.0, "Ride_%s" % row["Name"], "Rides", {
            "ride_id": row["Name"],
            "pick_extent": half_extent(300.0, 300.0, 300.0),
        })
        failed_props += failed
        count += 1
    report["rides"] = count
    return failed_props


def spawn_tokens(report):
    failed_props, count, from_mesh = [], 0, 0
    for row in util.data_rows("Tokens.json"):
        loc = util.xyz(row["Location"])
        _path, mesh = util.find_tagged_mesh("token", row["Name"])
        bounds = util.mesh_bounds(mesh) if mesh is not None else None
        if bounds is not None:
            loc = bounds[0]
            from_mesh += 1
        _a, failed = spawn_wta("WTATokenActor", loc, 0.0, "Token_%s" % row["Name"], "Tokens", {
            "token_id": row["Name"],
        })
        failed_props += failed
        count += 1
    report["tokens"] = count
    report["tokens_from_mesh"] = from_mesh
    return failed_props


def spawn_staff(report):
    failed_props, count = [], 0
    for row in util.data_rows("Staff.json"):
        loc = list(util.xyz(row["Location"]))
        loc[2] += CAPSULE_HALF_HEIGHT
        _a, failed = spawn_wta("WTAStaffNPC", loc, row.get("Yaw", 0.0), "Staff_%s" % row["Name"], "Staff", {
            "staff_id": row["Name"],
        })
        failed_props += failed
        count += 1
    report["staff"] = count
    return failed_props


def spawn_wax_stages(report):
    failed_props, count = [], 0
    for row in util.data_rows("WaxScenes.json"):
        stage = util.xyz(row["StageLocation"])
        yaw = float(row.get("StageYaw", 0.0))
        fwd = util.forward_from_yaw(yaw)
        # Trigger box centred 2 m in front of the rope, 1.8 m up, so the aisle in front of the stage counts.
        centre = (stage[0] + 200.0 * fwd[0], stage[1] + 200.0 * fwd[1], stage[2] + 180.0)
        _a, failed = spawn_wta("WTAWaxStageActor", centre, yaw, "WaxStage_%s" % row["Name"], "WaxStages", {
            "scene_id": row["Name"],
            "trigger_extent": half_extent(280.0, 200.0, 200.0),
        })
        failed_props += failed
        count += 1
    report["wax_stages"] = count
    return failed_props


def run():
    util.wait_for_asset_registry()
    util.ensure_level_loaded()
    report = {"removed_previous": util.delete_setup_actors(STEP)}
    failed = []
    for fn in (spawn_rooms, spawn_exhibits, spawn_books, spawn_stations, spawn_rides, spawn_tokens,
               spawn_staff, spawn_wax_stages):
        failed += fn(report)
    report["failed_props"] = sorted(set(failed))
    report["actors_total"] = len(util.find_actors(tag=util.step_tag(STEP)))
    report["saved"] = util.save_level()
    errors = []
    if report["failed_props"]:
        errors.append("properties not settable (check contract 4.5 names): %s" % ", ".join(report["failed_props"]))
    if not report["saved"]:
        errors.append("level save reported failure")
    report["ok"] = not errors
    if errors:
        report["error"] = "; ".join(errors)
    return report
