"""Step 3: import the exhibit art PNGs as /Game/WTA/Art/T_Art_<id> (sRGB, UI texture group), and the talks'
slides (Pipeline/out/slides/<talk>/<nn>.png, drawn by bl/slides.py) as /Game/WTA/Slides/T_Slide_<talk>_<nn>
(sRGB, BC7, no mips: a 2048 x 1024 picture the screens show whole).

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


def configure_texture(tex, bc7=False):
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
    if bc7:
        # slides: crisp text at 2 MB each, not the 8 MB of an uncompressed UI texture
        comp = util.enum_value("TextureCompressionSettings", "TC_BC7")
        if comp is not None:
            try:
                tex.set_editor_property("compression_settings", comp)
            except Exception:
                failed.append("compression_settings")
    return failed


def import_one(png_path, dest_folder, target_name, candidates, entry, report, bc7=False):
    """Import one PNG as dest_folder/target_name (rename after an Interchange import). True when it is there."""
    assets = util.assets()
    target_path = dest_folder + "/" + target_name
    try:
        objects = import_png(png_path, dest_folder, target_name)
    except Exception as exc:
        entry["error"] = str(exc)
        report["errors"].append("%s: %s" % (target_name, exc))
        return False
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
        imported_path, tex = find_texture(dest_folder, [target_name] + list(candidates))
    if tex is None:
        entry["error"] = "no Texture2D produced"
        report["errors"].append("%s: import produced no Texture2D" % target_name)
        return False
    if imported_path and imported_path != target_path:
        if assets.rename(imported_path, target_path):
            entry["renamed_from"] = imported_path
            try:
                if assets.exists(imported_path):
                    assets.delete(imported_path)
            except Exception:
                pass
            tex = assets.load(target_path) or tex
        else:
            entry["warning"] = "could not rename %s to %s" % (imported_path, target_path)
    entry["status"] = "imported"
    entry["config_failed"] = configure_texture(tex, bc7=bc7)
    assets.save(tex)
    return True


def import_slides(report, force):
    """Every talk's slides: Pipeline/out/slides/<talk>/<nn>.png -> /Game/WTA/Slides/T_Slide_<talk>_<nn>."""
    assets = util.assets()
    report["slides"] = {"imported": 0, "skipped": 0, "talks": {}}
    if not os.path.isdir(paths.SLIDES_DIR):
        report["slides"]["missing"] = paths.SLIDES_DIR
        return
    if not assets.directory_exists(paths.SLIDES_PATH):
        assets.make_directory(paths.SLIDES_PATH)
    for talk_id in sorted(os.listdir(paths.SLIDES_DIR)):
        folder = os.path.join(paths.SLIDES_DIR, talk_id)
        if not os.path.isdir(folder):
            continue
        pngs = sorted(f for f in os.listdir(folder) if f.lower().endswith(".png") and f[:2].isdigit())
        done = 0
        for png in pngs:
            number = int(os.path.splitext(png)[0])
            target_name = paths.slide_asset_name(talk_id, number)
            target_path = paths.slide_asset_path(talk_id, number)
            entry = {"source": "%s/%s" % (talk_id, png), "asset": target_path}
            if assets.exists(target_path) and not force:
                entry["status"] = "existed"
                report["slides"]["skipped"] += 1
                done += 1
                continue
            if import_one(os.path.join(folder, png), paths.SLIDES_PATH, target_name, [os.path.splitext(png)[0]], entry, report, bc7=True):
                report["slides"]["imported"] += 1
                done += 1
        report["slides"]["talks"][talk_id] = "%d/%d" % (done, len(pngs))
    assets.save_directory(paths.SLIDES_PATH, only_if_dirty=True, recursive=True)


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
    import_slides(report, force)
    report["count"] = len(pngs)
    report["force"] = force
    report["ok"] = not report["errors"] and len(pngs) > 0
    if not pngs:
        report["error"] = "no PNG files in " + paths.ART_DIR
    elif report["errors"]:
        report["error"] = "; ".join(report["errors"])[:1000]
    return report
