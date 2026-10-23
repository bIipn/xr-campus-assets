"""Step 5: create or load /Game/WTA/Maps/L_Campus and place the campus meshes.

The level is a plain (non World Partition) level. One StaticMeshActor per imported StaticMesh is spawned
at the origin (every mesh is baked in world space), in the Outliner folder Campus/<Asset>. Tagged meshes
(item__, token__, book__ ...) keep their mesh name as the actor label so later steps can find them.
World Settings gets the WTAGameMode and a PlayerStart stands at the layout spawn.
"""
import os

import unreal

from . import log
from . import paths
from . import util

STEP = "build_level"
CAPSULE_HALF_HEIGHT = 90.0   # AWTACharacter capsule half height (contract 4.3)


def create_or_load_level():
    assets = util.assets()
    les = util.level_subsystem()
    if assets.exists(paths.LEVEL_PATH):
        if not util.level_is_loaded():
            if les.load_level(paths.LEVEL_PATH) is False:
                raise RuntimeError("load_level(%s) returned False" % paths.LEVEL_PATH)
        return "loaded"
    if not assets.directory_exists(paths.MAPS_PATH):
        assets.make_directory(paths.MAPS_PATH)
    created = None
    try:
        created = les.new_level(paths.LEVEL_PATH, is_partitioned_world=False)
        how = "new_level(is_partitioned_world=False)"
    except TypeError:
        created = les.new_level(paths.LEVEL_PATH)
        how = "new_level(path)"
    if created is False:
        raise RuntimeError("new_level(%s) returned False" % paths.LEVEL_PATH)
    return "created via " + how


def spawn_meshes():
    counts = {}
    labels_tagged = []
    spins = []
    for asset, _glb in paths.mesh_assets():
        folder = paths.campus_asset_path(asset)
        meshes = util.static_meshes_under(folder)
        counts[asset] = len(meshes)
        for _path, mesh in meshes:
            name = util.object_name(mesh)
            tag = util.mesh_tag(name)
            if tag and tag[0] in ("prop", "popup", "figure"):
                # the Wax Hall's props (Props, HandProps) stand in their own frames: the stages spawn them; the
                # pop-up books' pieces move, so AWTAPopUpBookActor spawns them (the actors step); a guided visit's
                # people (People, bl/figure.py) are AWTACharacter's figure, never placed
                counts[asset] -= 1
                continue
            label = name if tag else "%s_%s" % (asset, name)
            actor = util.spawn_object(mesh, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), step=STEP, label=label,
                                      folder="Campus/" + asset)
            if tag:
                labels_tagged.append(label)
            if tag and tag[0] == "spot":
                # a speaker's spot (spot__<venue>_f<yaw>) only tells the actors step where the speaker stands
                try:
                    actor.set_actor_hidden_in_game(True)
                    actor.set_actor_enable_collision(False)
                except Exception:
                    pass
            if tag and tag[0] == "spin":
                spins.append(make_spin(actor, mesh, label))
                continue
            # Static mobility keeps Nanite and Lumen happy; it is the StaticMeshActor default.
            try:
                comp = actor.get_editor_property("static_mesh_component")
                if comp is not None:
                    comp.set_mobility(unreal.ComponentMobility.STATIC)
            except Exception:
                pass
    if spins:
        log.info("%s: turning %s" % (STEP, ", ".join(spins)))
    return counts, labels_tagged


SPIN_DEG_PER_S = 24.0


def make_spin(actor, mesh, label):
    """A spin__ mesh (the museum's turning VR headset, bl/museum.py) turns about its own centre: the actor goes
    Movable and gets a RotatingMovementComponent whose pivot is the mesh's centre (the mesh is baked in world space
    and the actor stands at the origin, so the centre in the actor's frame is the world centre). Returns a word for
    the log: the label, or why it does not turn."""
    try:
        comp = actor.get_editor_property("static_mesh_component")
        comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        bounds = util.mesh_bounds(mesh)
        if bounds is None:
            return label + " (no bounds)"
        centre = bounds[0]
        sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        handles = sds.k2_gather_subobject_data_for_instance(actor)
        if not handles:
            return label + " (no subobjects)"
        params = unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=unreal.RotatingMovementComponent,
                                              blueprint_context=None)
        handle, fail = sds.add_new_subobject(params)
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        rot = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)
        if rot is None:
            return label + " (could not add a RotatingMovementComponent: %s)" % fail
        rot.set_editor_property("rotation_rate", unreal.Rotator(roll=0.0, pitch=0.0, yaw=SPIN_DEG_PER_S))
        rot.set_editor_property("pivot_translation", unreal.Vector(*centre))
        return label
    except Exception as exc:
        return "%s (%s)" % (label, exc)


def set_game_mode():
    gm = util.load_wta_class("WTAGameMode")
    if gm is None:
        return False, "WTAGameMode class not loaded"
    world = util.editor_world()
    ws = None
    if world is not None:
        for getter in ("get_world_settings", "k2_get_world_settings"):
            fn = getattr(world, getter, None)
            if fn is None:
                continue
            try:
                ws = fn()
                break
            except Exception:
                continue
    if ws is None:
        for actor in util.all_actors():
            if util.actor_class_name(actor) == "WorldSettings":
                ws = actor
                break
    if ws is None:
        return False, "world settings actor not reachable"
    failed = util.set_props(ws, {"default_game_mode": gm}, label="WorldSettings")
    if failed:
        return False, "default_game_mode not settable"
    return True, paths.GAME_MODE_PATH


def spawn_player_start():
    layout = paths.read_json(paths.LAYOUT_JSON)
    spawn = layout.get("spawn", {}).get("ue", {})
    loc = list(spawn.get("location_cm", [0.0, -70.0, 0.0]))
    rotd = spawn.get("rotation_deg", {"pitch": 0.0, "yaw": -90.0, "roll": 0.0})
    # PlayerStart location is the capsule centre: floor + 90 cm.
    loc[2] = float(loc[2]) + CAPSULE_HALF_HEIGHT
    actor = util.spawn_class(unreal.PlayerStart, loc, (0.0, float(rotd.get("yaw", -90.0)), 0.0),
                             step=STEP, label="PlayerStart_Lobby", folder="Campus")
    return {"location": loc, "yaw": float(rotd.get("yaw", -90.0)), "label": util.actor_label(actor)}


def run():
    util.wait_for_asset_registry()
    report = {"level": paths.LEVEL_PATH}
    report["level_state"] = create_or_load_level()
    removed = util.delete_setup_actors(STEP)
    report["removed_previous"] = removed

    counts, tagged = spawn_meshes()
    report["mesh_actors"] = counts
    report["mesh_actor_total"] = sum(counts.values())
    report["tagged_actors"] = len(tagged)

    ok_gm, gm_info = set_game_mode()
    report["game_mode"] = gm_info
    report["game_mode_set"] = ok_gm

    report["player_start"] = spawn_player_start()

    report["saved"] = util.save_level()
    report["umap_exists"] = os.path.isfile(paths.LEVEL_UMAP)

    errors = []
    if report["mesh_actor_total"] == 0:
        errors.append("no imported meshes found under %s (run import_meshes)" % paths.CAMPUS_PATH)
    if not ok_gm:
        errors.append("game mode: " + gm_info)
    if not report["saved"]:
        errors.append("level save reported failure")
    report["ok"] = not errors
    if errors:
        report["error"] = "; ".join(errors)
    return report
