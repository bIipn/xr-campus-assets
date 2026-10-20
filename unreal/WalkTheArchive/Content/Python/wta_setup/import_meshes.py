"""Step 2: import Pipeline/out/ue/<Asset>.glb into /Game/WTA/Campus/<Asset>/.

Interchange handles glTF; one AssetImportTask per file (automated, replace existing, save). After the import
every StaticMesh gets Nanite (opaque meshes only; glass and other blended or masked materials stay
non-Nanite) and double-sided complex-as-simple collision so the player walks on the architecture and
cannot pass through the one-sided wall planes from behind. Assets that already exist are not imported
again unless WTA_FORCE=1, but their Nanite and collision settings are still applied.
"""
import os

import unreal

from . import log
from . import paths
from . import util

STEP = "import_meshes"


def glb_non_opaque_meshes(glb_path):
    """Names of meshes in a GLB that use a BLEND or MASK material."""
    doc = util.glb_json(glb_path)
    if doc is None:
        return set()
    mats = doc.get("materials", [])
    non_opaque = set(i for i, m in enumerate(mats) if m.get("alphaMode", "OPAQUE") != "OPAQUE")
    names = set()
    for mesh in doc.get("meshes", []):
        for prim in mesh.get("primitives", []):
            if prim.get("material") in non_opaque:
                names.add(mesh.get("name", ""))
                break
    return names


def ue_mesh_is_translucent(mesh):
    """True when any material slot resolves to a translucent or masked blend mode (best effort)."""
    translucent = util.enum_value("BlendMode", "BLEND_TRANSLUCENT")
    masked = util.enum_value("BlendMode", "BLEND_MASKED")
    additive = util.enum_value("BlendMode", "BLEND_ADDITIVE")
    try:
        slots = list(mesh.get_editor_property("static_materials"))
    except Exception:
        return False
    for slot in slots:
        try:
            mi = slot.get_editor_property("material_interface")
            if mi is None:
                continue
            base = mi
            try:
                base = mi.get_base_material() or mi
            except Exception:
                pass
            mode = base.get_editor_property("blend_mode")
            if mode in (translucent, masked, additive) and mode is not None:
                return True
        except Exception:
            continue
    return False


def import_glb(glb_path, dest_folder):
    task = unreal.AssetImportTask()
    util.set_props(task, {
        "filename": glb_path,
        "destination_path": dest_folder,
        "automated": True,
        "replace_existing": True,
        "save": True,
    }, label="AssetImportTask")
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    tools.import_asset_tasks([task])
    objects = []
    for getter in ("get_objects", "imported_object_paths"):
        try:
            res = getattr(task, getter)
            res = res() if callable(res) else res
            objects = list(res or [])
            if objects:
                break
        except Exception:
            continue
    # Interchange imports are asynchronous internally; wait for the mesh builds to finish.
    # The argument is bCancel (UInterchangeManager::WaitUntilAllTasksDone): True would cancel every
    # import still in flight, so only the first GLB of a run would land.
    try:
        mgr = unreal.InterchangeManager.get_interchange_manager_scripted()
        mgr.wait_until_all_tasks_done(False)
    except Exception:
        pass
    return objects


def set_nanite(mesh, enabled):
    settings = util.get_prop(mesh, "nanite_settings")
    if settings is None:
        return False
    try:
        settings.set_editor_property("enabled", bool(enabled))
    except Exception as exc:
        log.warn("nanite settings 'enabled' not settable on %s: %s" % (util.object_name(mesh), exc))
        return False
    sub = util.editor_subsystem("StaticMeshEditorSubsystem")
    if sub is not None and hasattr(sub, "set_nanite_settings"):
        try:
            sub.set_nanite_settings(mesh, settings, True)
            return True
        except Exception as exc:
            log.warn("set_nanite_settings failed on %s, falling back: %s" % (util.object_name(mesh), exc))
    try:
        mesh.set_editor_property("nanite_settings", settings)
        return True
    except Exception as exc:
        log.warn("nanite_settings not settable on %s: %s" % (util.object_name(mesh), exc))
        return False


def set_complex_collision(mesh):
    """Complex-as-simple, double-sided collision.

    The web campus builds most walls as one-sided planes. One-sided triangle collision only blocks from the front,
    so without double-sided geometry the player walks through a wall from its back side.
    """
    flag = util.enum_value("CollisionTraceFlag", "CTF_USE_COMPLEX_AS_SIMPLE")
    body = util.get_prop(mesh, "body_setup")
    if body is None or flag is None:
        return False
    try:
        body.set_editor_property("collision_trace_flag", flag)
        body.set_editor_property("double_sided_geometry", True)
        return True
    except Exception as exc:
        log.warn("collision settings not settable on %s: %s" % (util.object_name(mesh), exc))
        return False


def triangle_count(mesh):
    for args in ((0,), ()):
        try:
            return int(mesh.get_num_triangles(*args))
        except Exception:
            continue
    return -1


def run():
    force = util.env_flag("WTA_FORCE")
    # WTA_ASSETS narrows the step to named wings, so one rebuilt wing can be re-imported on its own
    # instead of forcing all nine through Interchange again.
    only = set(s.strip() for s in os.environ.get("WTA_ASSETS", "").replace(";", ",").split(",") if s.strip())
    util.wait_for_asset_registry()
    assets = util.assets()
    report = {"assets": {}, "imported": 0, "skipped": 0, "meshes": 0, "nanite": 0, "collision": 0,
              "non_nanite": [], "errors": [], "only": sorted(only)}
    if not os.path.isdir(paths.MESH_DIR):
        report["ok"] = False
        report["error"] = "mesh folder missing: " + paths.MESH_DIR
        return report

    for asset, glb in paths.mesh_assets():
        if only and asset not in only:
            continue
        dest = paths.campus_asset_path(asset)
        entry = {"glb": glb, "dest": dest}
        report["assets"][asset] = entry
        if not os.path.isfile(glb):
            entry["error"] = "file missing"
            report["errors"].append("%s: %s not found" % (asset, glb))
            continue
        existing = util.static_meshes_under(dest)
        if existing and not force:
            entry["status"] = "existed"
            entry["meshes"] = len(existing)
            report["skipped"] += 1
            meshes = existing
        else:
            try:
                objects = import_glb(glb, dest)
            except Exception as exc:
                entry["error"] = "import failed: %s" % exc
                report["errors"].append("%s: %s" % (asset, exc))
                continue
            entry["status"] = "imported"
            entry["returned_objects"] = len(objects)
            report["imported"] += 1
            meshes = util.static_meshes_under(dest)
            entry["meshes"] = len(meshes)
            if not meshes:
                entry["error"] = "no StaticMesh found after import"
                report["errors"].append("%s: import produced no StaticMesh under %s" % (asset, dest))
                continue

        glass = glb_non_opaque_meshes(glb)
        nanite_on, collision_on, tagged = 0, 0, []
        for path, mesh in meshes:
            name = util.object_name(mesh)
            if util.mesh_tag(name):
                tagged.append(name)
            translucent = name in glass or ue_mesh_is_translucent(mesh)
            if set_nanite(mesh, not translucent) and not translucent:
                nanite_on += 1
            if translucent:
                report["non_nanite"].append(name)
            if set_complex_collision(mesh):
                collision_on += 1
            assets.save(mesh)
        entry["nanite"] = nanite_on
        entry["collision"] = collision_on
        entry["tagged"] = tagged
        report["meshes"] += len(meshes)
        report["nanite"] += nanite_on
        report["collision"] += collision_on

    assets.save_directory(paths.CAMPUS_PATH, only_if_dirty=True, recursive=True)
    util.clear_asset_cache()
    report["force"] = force
    report["ok"] = not report["errors"]
    if report["errors"]:
        report["error"] = "; ".join(report["errors"])[:1000]
    return report
