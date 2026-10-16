"""Step 3: import the exhibit art PNGs as /Game/WTA/Art/T_Art_<id> (sRGB, UI texture group).

Interchange ignores destination_name, so the texture is imported under its file name and then renamed to
the contract name. Textures that already exist are skipped unless WTA_FORCE=1.
"""
import os

import unreal

from . import log
from . import paths
from . import util

STEP = "import_art"


def import_png(png_path, dest_folder, dest_name):
    task = unreal.AssetImportTask()
    util.set_props(task, {
        "filename": png_path,
        "destination_path": dest_folder,
        "destination_name": dest_name,   # ignored by Interchange, honoured by older importers
        "automated": True,
        "replace_existing": True,
        "save": True,
    }, label="AssetImportTask")
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    objects = []
    try:
        objects = list(task.get_objects() or [])
    except Exception:
        pass
    return objects


def configure_texture(tex):
    failed = []
    try:
        tex.set_editor_property("srgb", True)
    except Exception:
        failed.append("srgb")
    group = util.enum_value("TextureGroup", "TEXTUREGROUP_UI")
    if group is not None:
        try:
            tex.set_editor_property("lod_group", group)
        except Exception:
            failed.append("lod_group")
    return failed


def find_texture(dest_folder, candidates):
    """Load the first candidate name that exists as a Texture2D under dest_folder (any subfolder)."""
    assets = util.assets()
    for name in candidates:
        path = dest_folder + "/" + name
        if assets.exists(path):
            obj = assets.load(path)
            if obj is not None:
                return path, obj
    # Interchange may have put the texture in a subfolder: search by name.
    for path, obj in util.find_assets(dest_folder, "Texture2D"):
        if util.object_name(obj) in candidates:
            return path.split(".")[0], obj
    return None, None


def run():
    force = util.env_flag("WTA_FORCE")
    util.wait_for_asset_registry()
    assets = util.assets()
    report = {"textures": {}, "imported": 0, "skipped": 0, "errors": []}
    if not os.path.isdir(paths.ART_DIR):
        report["ok"] = False
        report["error"] = "art folder missing: " + paths.ART_DIR
        return report
    if not assets.directory_exists(paths.ART_PATH):
        assets.make_directory(paths.ART_PATH)

    pngs = sorted(f for f in os.listdir(paths.ART_DIR) if f.lower().endswith(".png"))
    for png in pngs:
        art_id = os.path.splitext(png)[0]
        target_name = paths.art_asset_name(art_id)
        target_path = paths.art_asset_path(art_id)
        entry = {"source": png, "asset": target_path}
        report["textures"][art_id] = entry
        if assets.exists(target_path) and not force:
            entry["status"] = "existed"
            report["skipped"] += 1
            tex = assets.load(target_path)
            if tex is not None:
                entry["config_failed"] = configure_texture(tex)
                assets.save(tex)
            continue
        try:
            objects = import_png(os.path.join(paths.ART_DIR, png), paths.ART_PATH, target_name)
        except Exception as exc:
            entry["error"] = str(exc)
            report["errors"].append("%s: %s" % (art_id, exc))
            continue
        tex = None
        imported_path = None
        for obj in objects:
            try:
                if isinstance(obj, unreal.Texture2D) or obj.get_class().get_name() == "Texture2D":
                    tex = obj
                    imported_path = str(obj.get_path_name()).split(".")[0]
                    break
            except Exception:
                continue
        if tex is None:
            imported_path, tex = find_texture(paths.ART_PATH, [target_name, art_id, art_id.replace("-", "_")])
        if tex is None:
            entry["error"] = "no Texture2D produced"
            report["errors"].append("%s: import produced no Texture2D" % art_id)
            continue
        if imported_path and imported_path != target_path:
            if assets.rename(imported_path, target_path):
                entry["renamed_from"] = imported_path
                # The rename leaves a redirector behind; nothing references it yet, so drop it.
                try:
                    if assets.exists(imported_path):
                        assets.delete(imported_path)
                except Exception:
                    pass
                tex = assets.load(target_path) or tex
            else:
                entry["warning"] = "could not rename %s to %s" % (imported_path, target_path)
        entry["status"] = "imported"
        entry["config_failed"] = configure_texture(tex)
        assets.save(tex)
        report["imported"] += 1

    assets.save_directory(paths.ART_PATH, only_if_dirty=True, recursive=True)
    report["count"] = len(pngs)
    report["force"] = force
    report["ok"] = not report["errors"] and len(pngs) > 0
    if not pngs:
        report["error"] = "no PNG files in " + paths.ART_DIR
    elif report["errors"]:
        report["error"] = "; ".join(report["errors"])[:1000]
    return report
