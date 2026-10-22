"""Step: real surfaces on the built rooms (Pipeline/content/surfaces.json).

  * imports each listed CC0 texture set (ambientCG 2K JPG: Color, NormalDX, Roughness, AmbientOcclusion) from
    the textures folder (WTA_TEXTURES, else the json's path) to /Game/WTA/Surfaces/<Set>/
  * builds /Game/WTA/Materials/M_WTA_Surface once: world-aligned colour, normal, roughness and occlusion
    (the Engine's WorldAlignedTexture / WorldAlignedNormal functions), so every mesh takes a set at the right
    size whatever its UVs, with Tint, Metallic, RoughnessScale and SizeCm parameters
  * makes one instance per set (MI_<Set>) and sets it on every static mesh material slot under
    /Game/WTA/Campus/<Asset>/ whose material is named for a builder material listed under that asset
    (M_ReadingRoom_walnut_v_020 is "walnut_v"), saving the meshes
Idempotent: textures already imported are kept, the master is built once, instances are refreshed.
"""
import json
import os
import re

import unreal

from . import log
from . import paths
from . import util

STEP = "surfaces"
SURFACES_JSON = os.path.join(paths.PIPELINE_DIR, "content", "surfaces.json")
SURFACES_PATH = paths.CONTENT_ROOT + "/Surfaces"
MATERIALS_PATH = paths.CONTENT_ROOT + "/Materials"
MASTER_PATH = MATERIALS_PATH + "/M_WTA_Surface"
WORLD_ALIGNED_TEXTURE = "/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture.WorldAlignedTexture"
WORLD_ALIGNED_NORMAL = "/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedNormal.WorldAlignedNormal"
MAPS = {"Color": "Color", "Normal": "NormalDX", "Roughness": "Roughness", "AO": "AmbientOcclusion"}


def read_spec():
    with open(SURFACES_JSON, "r", encoding="utf-8") as fh:
        return json.load(fh)


def textures_dir(spec):
    return os.environ.get("WTA_TEXTURES") or spec.get("textures") or ""


def find_map_file(folder, set_name, suffix):
    """The jpg of one map in an ambientCG set folder: <Set>_2K-JPG_<suffix>.jpg (any resolution tag)."""
    if not os.path.isdir(folder):
        return None
    pat = re.compile(r"^%s_.*_%s\.(jpg|jpeg|png)$" % (re.escape(set_name), re.escape(suffix)), re.I)
    for name in sorted(os.listdir(folder)):
        if pat.match(name):
            return os.path.join(folder, name)
    return None


def import_texture(path, dest_folder, linear, normal):
    assets = util.assets()
    base = re.sub(r"[^A-Za-z0-9_]+", "_", os.path.splitext(os.path.basename(path))[0])
    existing = assets.load(dest_folder + "/" + base) if assets.exists(dest_folder + "/" + base) else None
    if existing is not None:
        return existing
    task = unreal.AssetImportTask()
    util.set_props(task, {
        "filename": path,
        "destination_path": dest_folder,
        "automated": True,
        "replace_existing": True,
        "save": False,
    }, label="AssetImportTask")
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex = None
    try:
        for obj in list(task.get_objects() or []):
            if isinstance(obj, unreal.Texture2D):
                tex = obj
    except Exception:
        pass
    if tex is None and assets.exists(dest_folder + "/" + base):
        tex = assets.load(dest_folder + "/" + base)
    if tex is None:
        return None
    props = {"srgb": not linear}
    if normal:
        props["compression_settings"] = util.enum_value("TextureCompressionSettings", "TC_NORMALMAP")
        props["lod_group"] = util.enum_value("TextureGroup", "TEXTUREGROUP_WORLD_NORMAL_MAP")
    elif linear:
        props["compression_settings"] = util.enum_value("TextureCompressionSettings", "TC_MASKS")
    props = {k: v for k, v in props.items() if v is not None}
    util.set_props(tex, props, label=base)
    assets.save(tex)
    return tex


def import_set(spec, set_name):
    """{'Color': tex, 'Normal': tex, 'Roughness': tex, 'AO': tex} (missing maps left out)."""
    folder = os.path.join(textures_dir(spec), set_name)
    dest = SURFACES_PATH + "/" + set_name
    assets = util.assets()
    if not assets.directory_exists(dest):
        assets.make_directory(dest)
    out = {}
    for key, suffix in MAPS.items():
        path = find_map_file(folder, set_name, suffix)
        if path is None:
            continue
        tex = import_texture(path, dest, linear=(key != "Color"), normal=(key == "Normal"))
        if tex is not None:
            out[key] = tex
    return out


def function_call(mel, mat, function_path, x, y):
    fn = unreal.load_asset(function_path)
    if fn is None:
        raise RuntimeError("material function %s not found" % function_path)
    call = mel.create_material_expression(mat, unreal.MaterialExpressionMaterialFunctionCall, x, y)
    call.set_editor_property("material_function", fn)
    return call


def build_master(first_set):
    """M_WTA_Surface, built once. first_set gives the parameters their default textures."""
    mel = unreal.MaterialEditingLibrary
    assets = util.assets()
    if assets.exists(MASTER_PATH):
        return assets.load(MASTER_PATH), False
    folder, name = MASTER_PATH.rsplit("/", 1)
    if not assets.directory_exists(folder):
        assets.make_directory(folder)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())
    if mat is None:
        raise RuntimeError("create_asset failed for " + MASTER_PATH)

    size = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -1500, -500)
    size.set_editor_property("parameter_name", "SizeCm")
    size.set_editor_property("default_value", 200.0)

    def tex_param(pname, y, default):
        p = mel.create_material_expression(mat, unreal.MaterialExpressionTextureObjectParameter, -1500, y)
        p.set_editor_property("parameter_name", pname)
        if default is not None:
            p.set_editor_property("texture", default)
        return p

    def aligned(pname, y, default, function):
        p = tex_param(pname, y, default)
        call = function_call(mel, mat, function, -1100, y)
        if not mel.connect_material_expressions(p, "", call, "TextureObject"):
            raise RuntimeError("%s -> TextureObject did not connect" % pname)
        if not mel.connect_material_expressions(size, "", call, "TextureSize"):
            raise RuntimeError("SizeCm -> TextureSize did not connect for " + pname)
        return call

    colour = aligned("Color", -300, first_set.get("Color"), WORLD_ALIGNED_TEXTURE)
    tint = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -800, -450)
    tint.set_editor_property("parameter_name", "Tint")
    tint.set_editor_property("default_value", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
    mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -500, -350)
    if not mel.connect_material_expressions(colour, "XYZ Texture", mul, "A"):
        raise RuntimeError("colour XYZ Texture output did not connect")
    mel.connect_material_expressions(tint, "", mul, "B")
    mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_BASE_COLOR)

    rough = aligned("Roughness", 0, first_set.get("Roughness"), WORLD_ALIGNED_TEXTURE)
    rscale = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -800, 100)
    rscale.set_editor_property("parameter_name", "RoughnessScale")
    rscale.set_editor_property("default_value", 1.0)
    rmul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -500, 0)
    mel.connect_material_expressions(rough, "XYZ Texture", rmul, "A")
    mel.connect_material_expressions(rscale, "", rmul, "B")
    mel.connect_material_property(rmul, "", unreal.MaterialProperty.MP_ROUGHNESS)

    metallic = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -800, 250)
    metallic.set_editor_property("parameter_name", "Metallic")
    metallic.set_editor_property("default_value", 0.0)
    mel.connect_material_property(metallic, "", unreal.MaterialProperty.MP_METALLIC)

    ao = aligned("AO", 300, first_set.get("AO"), WORLD_ALIGNED_TEXTURE)
    mel.connect_material_property(ao, "XYZ Texture", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)

    normal = aligned("Normal", 600, first_set.get("Normal"), WORLD_ALIGNED_NORMAL)
    if not mel.connect_material_property(normal, "XYZ Texture", unreal.MaterialProperty.MP_NORMAL):
        raise RuntimeError("normal XYZ Texture output did not connect")

    mel.recompile_material(mat)
    assets.save(mat)
    return mat, True


def make_instance(master, mi_name, set_name, textures, params):
    """MI_<mi_name> under the set's folder: the set's maps, its size, metallic, roughness scale and tint."""
    mel = unreal.MaterialEditingLibrary
    assets = util.assets()
    folder = SURFACES_PATH + "/" + set_name
    path = folder + "/MI_" + mi_name
    mi = assets.load(path) if assets.exists(path) else None
    if mi is None:
        mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset("MI_" + mi_name, folder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    if mi is None:
        raise RuntimeError("create_asset failed for " + path)
    mi.set_editor_property("parent", master)
    for key, tex in textures.items():
        mel.set_material_instance_texture_parameter_value(mi, key, tex)
    mel.set_material_instance_scalar_parameter_value(mi, "SizeCm", float(params.get("size_cm", 200)))
    mel.set_material_instance_scalar_parameter_value(mi, "Metallic", float(params.get("metallic", 0.0)))
    mel.set_material_instance_scalar_parameter_value(mi, "RoughnessScale", float(params.get("roughness_scale", 1.0)))
    tint = params.get("tint") or [1.0, 1.0, 1.0]
    mel.set_material_instance_vector_parameter_value(mi, "Tint", unreal.LinearColor(float(tint[0]), float(tint[1]), float(tint[2]), 1.0))
    mel.update_material_instance(mi)
    assets.save(mi)
    return mi


def instance_for(master, spec, imported, cache, set_name, use):
    """The instance for one use of a set: MI_<Set> as the set is listed, MI_<Set>_2, _3... for a use that tints
    or resizes it."""
    params = dict(spec["sets"].get(set_name, {}))
    params.update({k: v for k, v in use.items() if k != "set"})
    key = json.dumps([set_name, params], sort_keys=True)
    if key in cache:
        return cache[key]
    mi_name = set_name
    if params != spec["sets"].get(set_name, {}):
        others = [k for k in cache if json.loads(k)[0] == set_name]
        mi_name = "%s_%d" % (set_name, len(others) + 1)
    mi = make_instance(master, mi_name, set_name, imported[set_name], params)
    cache[key] = mi
    return mi


def assign(spec, master, imported, report):
    """Puts the instances on the campus meshes' material slots. Returns (slots changed, meshes saved)."""
    assets = util.assets()
    cache = {}
    changed, saved, missing = 0, 0, set()
    for asset, materials in spec.get("materials", {}).items():
        folder = paths.campus_asset_path(asset)
        wanted = {}
        for mat_name, use in materials.items():
            if use.get("set") not in imported:
                missing.add(use.get("set"))
                continue
            wanted[mat_name] = use
        if not wanted:
            continue
        for path, mesh in util.static_meshes_under(folder):
            try:
                slots = list(mesh.get_editor_property("static_materials"))
            except Exception as exc:
                log.warn("%s: static_materials: %s" % (path, exc))
                continue
            dirty = False
            for index, slot in enumerate(slots):
                current = slot.get_editor_property("material_interface")
                cname = util.object_name(current) if current is not None else ""
                for mat_name, use in wanted.items():
                    if ("_%s_" % mat_name) in cname or cname.endswith("_" + mat_name):
                        mi = instance_for(master, spec, imported, cache, use["set"], use)
                        if current is not mi:
                            mesh.set_material(index, mi)
                            changed += 1
                            dirty = True
                        break
            if dirty and assets.save(mesh):
                saved += 1
    report["instances"] = len(cache)
    if missing:
        report["sets_missing"] = sorted(s for s in missing if s)
    return changed, saved


def run():
    util.wait_for_asset_registry()
    spec = read_spec()
    report = {"textures_dir": textures_dir(spec)}
    imported = {}
    for set_name in spec.get("sets", {}):
        maps = import_set(spec, set_name)
        if "Color" in maps:
            imported[set_name] = maps
        else:
            log.warn("surface set %s: no Color map under %s" % (set_name, os.path.join(textures_dir(spec), set_name)))
    report["sets"] = {k: sorted(v.keys()) for k, v in imported.items()}
    if not imported:
        report["ok"] = False
        report["error"] = "no texture sets found under " + textures_dir(spec)
        return report
    first = imported[next(iter(imported))]
    master, built = build_master(first)
    report["master"] = MASTER_PATH
    report["master_built"] = built
    changed, saved = assign(spec, master, imported, report)
    report["slots_changed"] = changed
    report["meshes_saved"] = saved
    report["ok"] = True
    return report
