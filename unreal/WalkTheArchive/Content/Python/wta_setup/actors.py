"""Step 7: spawn the WalkTheArchive C++ actors from the DataTable JSON (contract table 4.5).

  AWTARoomVolume     one per Rooms.json row, centre and half extent from BoundsMin/Max
  AWTAExhibitActor   one per Exhibits.json row at Location/Yaw, PickExtent (8, w/2, h/2)
  AWTABookActor      one per copy of each Books.json book (featured table, stack end, Room 104) at that cover
                     (util.book_copies); the whole book__<id> mesh bounds if the GLBs list none; skipped if absent
  AWTAStationActor   one per Stations.json row, extent 80
  AWTARideActor      one per Rides.json row, extent 300
  AWTATokenActor     one per Tokens.json row at the token__<id> mesh centre, else Location
  AWTAStaffNPC       one per Staff.json row, capsule centre = floor + 90
  AWTAWaxStageActor  one per WaxScenes.json row, trigger (280, 200, 200) in front of the stage
  AWTAStatueActor    one per Pipeline/content/statues.json entry (the marble statues: a MetaHuman held in a mocap
                     pose, every surface in M_WTA_Marble, which this step builds when missing)
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
    """One AWTABookActor per copy of each book (util.book_copies: the featured table, the stack end, Room 104),
    each picking only its own cover; a book with no copies in the GLBs falls back to its whole mesh's bounds."""
    failed_props, count, skipped = [], 0, []
    copies = util.book_copies()
    folders = [paths.campus_asset_path("LibraryShell"), paths.campus_asset_path("School"), paths.CAMPUS_PATH]
    for row in util.data_rows("Books.json"):
        spots = copies.get(row["Name"])
        if not spots:
            _path, mesh = util.find_tagged_mesh("book", row["Name"], folders)
            bounds = util.mesh_bounds(mesh) if mesh is not None else None
            if bounds is None:
                skipped.append(row["Name"])
                log.warn("book mesh book__%s not found; AWTABookActor %s skipped" % (row["Name"].replace("-", "_"), row["Name"]))
                continue
            spots = [bounds]
        for n, (centre, ext) in enumerate(spots, 1):
            pick = [max(e + 6.0, 12.0) for e in ext]
            label = "Book_%s" % row["Name"] if len(spots) == 1 else "Book_%s_%d" % (row["Name"], n)
            _a, failed = spawn_wta("WTABookActor", centre, 0.0, label, "Books", {
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


def build_marble_material():
    """M_WTA_Marble: white statuary marble - a warm off-white with the museum's own marble veining when its texture
    is in the project, subsurface shading so edges glow a little in the light, roughness of polished stone."""
    mel = unreal.MaterialEditingLibrary
    assets = util.assets()
    path = paths.MARBLE_MATERIAL
    if assets.exists(path):
        return assets.load(path)
    folder, name = path.rsplit("/", 1)
    if not assets.directory_exists(folder):
        assets.make_directory(folder)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())
    util.set_props(mat, {"shading_model": util.enum_value("MaterialShadingModel", "MSM_SUBSURFACE")}, label=name)
    tint = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -700, -200)
    tint.set_editor_property("parameter_name", "Tint")
    tint.set_editor_property("default_value", unreal.LinearColor(0.86, 0.84, 0.80, 1.0))
    colour = tint
    veins = next((ad.get_asset() for ad in unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_path(paths.CAMPUS_PATH, True)
                  if str(ad.asset_name).endswith("marble_w_0") and str(ad.asset_class_path.asset_name) == "Texture2D"), None)
    if veins is not None:
        sample = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -1000, 0)
        sample.set_editor_property("texture", veins)
        coords = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -1250, 0)
        coords.set_editor_property("u_tiling", 2.0)
        coords.set_editor_property("v_tiling", 2.0)
        mel.connect_material_expressions(coords, "", sample, "UVs")
        mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -450, -100)
        mel.connect_material_expressions(sample, "RGB", mul, "A")
        mel.connect_material_expressions(tint, "", mul, "B")
        colour = mul
    mel.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -700, 150)
    rough.set_editor_property("parameter_name", "Roughness")
    rough.set_editor_property("default_value", 0.38)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    sss = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -700, 350)
    sss.set_editor_property("parameter_name", "SubsurfaceColor")
    sss.set_editor_property("default_value", unreal.LinearColor(0.93, 0.88, 0.82, 1.0))
    mel.connect_material_property(sss, "", unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
    opacity = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -700, 500)
    opacity.set_editor_property("parameter_name", "Opacity")
    opacity.set_editor_property("default_value", 0.7)
    mel.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)
    for usage in ("MATUSAGE_SKELETAL_MESH", "MATUSAGE_MORPH_TARGETS", "MATUSAGE_CLOTHING"):
        try:
            setter = getattr(mel, "set_base_material_usage", None) or getattr(mel, "set_material_usage", None)
            setter(mat, getattr(unreal.MaterialUsage, usage))
        except Exception as exc:
            log.warn("marble usage %s: %s" % (usage, exc))
    mel.recompile_material(mat)
    assets.save(mat)
    return mat


def spawn_statues(report):
    """One AWTAStatueActor per statues.json entry, feet at pos_m, facing ue_yaw."""
    failed_props, count = [], 0
    try:
        doc = paths.read_json(paths.STATUES_JSON)
    except Exception as exc:
        log.warn("statues.json unreadable: %s" % exc)
        report["statues"] = 0
        return failed_props
    build_marble_material()
    for row in doc.get("statues", []):
        x, y, z = row.get("pos_m", [0, 0, 0])
        loc = (100.0 * x, 100.0 * z, 100.0 * y)
        _a, failed = spawn_wta("WTAStatueActor", loc, row.get("ue_yaw", 0.0), "Statue_%s" % row["id"], "Statues", {
            "person": row["person"],
            "action": row.get("action", "think"),
            "phase": float(row.get("phase", 0.3)),
        })
        failed_props += failed
        count += 1
    report["statues"] = count
    return failed_props


def run():
    util.wait_for_asset_registry()
    util.ensure_level_loaded()
    report = {"removed_previous": util.delete_setup_actors(STEP)}
    failed = []
    for fn in (spawn_rooms, spawn_exhibits, spawn_books, spawn_stations, spawn_rides, spawn_tokens,
               spawn_staff, spawn_wax_stages, spawn_statues):
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
