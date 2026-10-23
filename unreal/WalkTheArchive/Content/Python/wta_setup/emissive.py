"""Self-lit surfaces under physical exposure (run by the lighting step).

The web campus has two kinds of self-lit surface, and neither survives the move into a physically exposed
Unreal scene unchanged (lighting.py explains the exposure):
  * Glows. export_campus.py turns every web colour brighter than white into emissive (materials named
    *_glow): light fixtures, LED strips, badge rings. Their web strength is display referred, so 3.2 would be
    3.2 cd/m2 and render as unlit grey. They get physical luminance instead: GLOW_NITS per unit for white and
    warm fixtures (a ceiling panel about 3200 cd/m2, like a real LED troffer) and, indoors, GLOW_NITS_COLOURED
    for saturated ones, which would otherwise clip to white and lose their colour. Outdoors they keep the
    full value so they still show in daylight.
  * Unlit pictures. three.js MeshBasicMaterial becomes KHR_materials_unlit, and Interchange gives it
    MI_Unlit_*, whose emissive is the texture at 1 cd/m2: black at any real exposure (frosted windows,
    screens, labels, painted letters, the horizon). Those instances move onto M_WTA_Unlit (or its translucent
    twin), which divides by the eye adaptation so they show on screen as the web drew them. Faint blended
    decals (the web's fake light pools, alpha below UNLIT_POOL_ALPHA) stay as they are, because the real
    lights make those pools now. The horizon rings lost their vertex colours in the export and get the web's
    colours back (HORIZON_COLOURS).
Every glow and converted mesh stays out of Lumen's GI: small bright emitters only add noise there, and a
display-referred one would feed the exposure back into the lighting. Glows also cast no shadow.
It also builds M_WTA_WidgetLit, the lit paper a world-space widget is drawn as (the Lost Stories wall's cards).
"""
import os

import unreal

from . import log
from . import paths
from . import util

GLOW_NITS = 1000.0
GLOW_NITS_COLOURED = 100.0
GLOW_SATURATED = 0.6                    # 1 - min/max of the emissive colour above which a glow is coloured
OUTDOOR_ASSETS = ("Yard", "Outside")
GLOW_MARK = "_glow"                     # M_<Asset>_glow[_NNN]_<id>; the meshes are M_glow[_NNN]
# The Blender-built rooms' self-lit materials (bl/library.py, bl/museum.py, bl/exterior.py: names ending in _e),
# by the fixture: physical luminance in cd/m2, whatever strength Blender's preview used.
BLENDER_NITS = {
    "lamp_e": 3000.0,         # bulb glass in the sconces, torcheres, chandeliers, lanterns and posts
    "laylight_e": 2500.0,     # the glazing under the museum's laylights and the Reading Room's
    "oculus_e": 6000.0,       # the sky in the rotunda's oculus
    "bulb_e": 3000.0,
    "shade_e": 60.0,          # the reading lamps' green cased glass: a faint glow through it
    "shadein_e": 1500.0,      # their warm opal lining, lit by the tube under it
}

UNLIT_MASTER = paths.MATERIALS_PATH + "/M_WTA_Unlit"
UNLIT_MASTER_TRANSLUCENT = paths.MATERIALS_PATH + "/M_WTA_UnlitTranslucent"
# World-space widgets drawn as paper (the Lost Stories wall's cards; AWTAStoryWallActor::BoardMaterial)
WIDGET_LIT = paths.MATERIALS_PATH + "/M_WTA_WidgetLit"
INTERCHANGE_UNLIT = "/InterchangeAssets/gltf/MaterialInstances/MI_Unlit"
UNLIT_POOL_ALPHA = 0.3
WHITE_TEXTURE = "/Engine/EngineResources/WhiteSquareTexture.WhiteSquareTexture"
# parts/outdoor.js buildHorizon(): ring radius in metres -> the mean of its bottom and top vertex colours.
HORIZON_COLOURS = ((176.0, "#7d9787"), (142.0, "#2c4733"))
HORIZON_MIN_EXTENT_M = 50.0             # an untextured unlit mesh wider than this is a horizon ring


def glb_materials():
    """Material name -> facts from the GLBs: asset, glow strength, emissive colour, unlit, alpha, mesh extent (m)."""
    out = {}
    for asset, glb in paths.mesh_assets():
        doc = util.glb_json(glb) if os.path.isfile(glb) else None
        if doc is None:
            continue
        accessors = doc.get("accessors", [])
        extent = {}
        for mesh in doc.get("meshes", []):
            for prim in mesh.get("primitives", []):
                acc = accessors[prim["attributes"]["POSITION"]] if "POSITION" in prim.get("attributes", {}) else {}
                lo, hi = acc.get("min"), acc.get("max")
                if lo and hi:
                    size = [hi[k] - lo[k] for k in range(3)]
                    old = extent.get(prim.get("material"), [0.0, 0.0, 0.0])
                    extent[prim.get("material")] = [max(old[k], size[k]) for k in range(3)]
        for i, mat in enumerate(doc.get("materials", [])):
            ext = mat.get("extensions", {})
            pbr = mat.get("pbrMetallicRoughness", {})
            out[mat.get("name", "")] = {
                "asset": asset,
                "strength": ext.get("KHR_materials_emissive_strength", {}).get("emissiveStrength"),
                "emissive": mat.get("emissiveFactor") or [1.0, 1.0, 1.0],
                "unlit": "KHR_materials_unlit" in ext,
                "textured": "baseColorTexture" in pbr,
                "alpha": float(pbr.get("baseColorFactor", [1.0, 1.0, 1.0, 1.0])[3]),
                "extent_m": extent.get(i, [0.0, 0.0, 0.0]),
            }
    return out


def glow_nits(asset, strength, colour):
    """Target EmissiveStrength (cd/m2) for a web glow of this strength and emissive colour."""
    top = max(colour) if colour else 1.0
    saturation = 1.0 - (min(colour) / top) if colour and top > 0 else 0.0
    if saturation > GLOW_SATURATED and asset not in OUTDOOR_ASSETS:
        return strength * GLOW_NITS_COLOURED
    return strength * GLOW_NITS


def calibrate_glows(mis, facts, report):
    """EmissiveStrength = glow_nits() on every glow material instance (idempotent: computed from the GLB)."""
    mel = unreal.MaterialEditingLibrary
    done, unmatched, failed = [], [], []
    for name, mi in mis.items():
        blender = next((nits for key, nits in BLENDER_NITS.items() if ("_%s_" % key) in name or name.endswith("_" + key)), None)
        if GLOW_MARK not in name and blender is None:
            continue
        fact = facts.get(name)
        # A Blender fixture's luminance comes from BLENDER_NITS, so it needs no strength from the GLB (the exporter
        # writes none for a strength of 1 or less: the reading lamps' glass).
        if fact is None or (fact["strength"] is None and blender is None):
            unmatched.append(name)
            continue
        target = blender if blender is not None else glow_nits(fact["asset"], float(fact["strength"]), fact["emissive"])
        try:
            # The setter returns False in 5.8 even when it applied the value, so read the value back instead.
            mel.set_material_instance_scalar_parameter_value(mi, "EmissiveStrength", target)
            if abs(mel.get_material_instance_scalar_parameter_value(mi, "EmissiveStrength") - target) > 0.01:
                failed.append(name)
                continue
            mel.update_material_instance(mi)
            util.assets().save(mi)
            done.append(name)
        except Exception as exc:
            failed.append(name)
            log.warn("glow %s not calibrated: %s" % (name, exc))
    report["glow_materials"] = len(done)
    if unmatched:
        report["glow_materials_unmatched"] = unmatched
    if failed:
        report["glow_materials_failed"] = failed
    return set(done)


def _expression(mat, cls_name, x, y, props=None):
    expr = unreal.MaterialEditingLibrary.create_material_expression(mat, getattr(unreal, cls_name), x, y)
    if expr is None:
        raise RuntimeError("could not create %s" % cls_name)
    for key, value in (props or {}).items():
        expr.set_editor_property(key, value)
    return expr


def _connect(src, src_out, dst, dst_in):
    if not unreal.MaterialEditingLibrary.connect_material_expressions(src, src_out, dst, dst_in):
        raise RuntimeError("could not connect %s.%s -> %s.%s" % (util.object_name(src), src_out or "out",
                                                                  util.object_name(dst), dst_in))


def build_unlit_master(path, translucent):
    """Emissive = BaseColorTexture x BaseColorFactor x Luminance / EyeAdaptation (display referred).

    The parameter names match Interchange's MI_Unlit_* so a reparented instance keeps its texture and colour.
    The translucent twin takes its opacity from the texture alpha times the Opacity parameter.
    """
    mel = unreal.MaterialEditingLibrary
    assets = util.assets()
    if assets.exists(path):
        mat = assets.load(path)
        mel.delete_all_material_expressions(mat)
    else:
        folder, name = path.rsplit("/", 1)
        if not assets.directory_exists(folder):
            assets.make_directory(folder)
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, unreal.Material,
                                                                      unreal.MaterialFactoryNew())
    util.set_props(mat, {
        "shading_model": util.enum_value("MaterialShadingModel", "MSM_UNLIT"),
        "blend_mode": util.enum_value("BlendMode", "BLEND_TRANSLUCENT" if translucent else "BLEND_OPAQUE"),
        "two_sided": True,
    }, label=util.object_name(mat))
    tex = _expression(mat, "MaterialExpressionTextureSampleParameter2D", -1100, -150,
                      {"parameter_name": "BaseColorTexture", "texture": unreal.load_asset(WHITE_TEXTURE)})
    factor = _expression(mat, "MaterialExpressionVectorParameter", -1100, 200,
                         {"parameter_name": "BaseColorFactor", "default_value": unreal.LinearColor(1.0, 1.0, 1.0, 1.0)})
    lum = _expression(mat, "MaterialExpressionScalarParameter", -800, 300,
                      {"parameter_name": "Luminance", "default_value": 1.0})
    eye = _expression(mat, "MaterialExpressionEyeAdaptation", -800, 420)
    colour = _expression(mat, "MaterialExpressionMultiply", -800, 0)
    _connect(tex, "RGB", colour, "A")
    _connect(factor, "", colour, "B")
    scaled = _expression(mat, "MaterialExpressionMultiply", -550, 100)
    _connect(colour, "", scaled, "A")
    _connect(lum, "", scaled, "B")
    shown = _expression(mat, "MaterialExpressionDivide", -300, 150)
    _connect(scaled, "", shown, "A")
    _connect(eye, "", shown, "B")
    if not mel.connect_material_property(shown, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR):
        raise RuntimeError("could not connect the emissive output of " + path)
    if translucent:
        opacity = _expression(mat, "MaterialExpressionScalarParameter", -800, 600,
                              {"parameter_name": "Opacity", "default_value": 1.0})
        alpha = _expression(mat, "MaterialExpressionMultiply", -550, 550)
        _connect(tex, "A", alpha, "A")
        _connect(opacity, "", alpha, "B")
        if not mel.connect_material_property(alpha, "", unreal.MaterialProperty.MP_OPACITY):
            raise RuntimeError("could not connect the opacity output of " + path)
    else:
        # The opaque master shades the Nanite campus meshes (5.8 name first, then the deprecated one).
        setter = getattr(mel, "set_base_material_usage", None) or getattr(mel, "set_material_usage", None)
        try:
            setter(mat, unreal.MaterialUsage.MATUSAGE_NANITE)
        except Exception as exc:
            log.warn("Nanite usage not set on %s: %s" % (path, exc))
    mel.recompile_material(mat)
    assets.save(mat)
    return mat


def build_widget_material(path=WIDGET_LIT):
    """A lit, masked, two-sided material for a world-space widget, so what it draws is paper lit by the room.

    The engine's own widget materials are unlit at 1 cd/m2, black under physical exposure. The parameter names are
    the ones UWidgetComponent sets on its material instance: SlateUI (the widget's render target, as the base colour),
    TintColorAndOpacity (multiplies the colour; its alpha the mask) and OpacityFromTexture (how much the render
    target's alpha cuts the shape out).
    """
    mel = unreal.MaterialEditingLibrary
    assets = util.assets()
    if assets.exists(path):
        mat = assets.load(path)
        mel.delete_all_material_expressions(mat)
    else:
        folder, name = path.rsplit("/", 1)
        if not assets.directory_exists(folder):
            assets.make_directory(folder)
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, unreal.Material,
                                                                      unreal.MaterialFactoryNew())
    util.set_props(mat, {
        "shading_model": util.enum_value("MaterialShadingModel", "MSM_DEFAULT_LIT"),
        "blend_mode": util.enum_value("BlendMode", "BLEND_MASKED"),
        "two_sided": True,
        "opacity_mask_clip_value": 0.33,
    }, label=util.object_name(mat))
    tex = _expression(mat, "MaterialExpressionTextureSampleParameter2D", -1100, -150,
                      {"parameter_name": "SlateUI", "texture": unreal.load_asset(WHITE_TEXTURE)})
    tint = _expression(mat, "MaterialExpressionVectorParameter", -1100, 200,
                       {"parameter_name": "TintColorAndOpacity", "default_value": unreal.LinearColor(1.0, 1.0, 1.0, 1.0)})
    from_tex = _expression(mat, "MaterialExpressionScalarParameter", -1100, 450,
                           {"parameter_name": "OpacityFromTexture", "default_value": 1.0})
    # The render target holds the widget's colours gamma encoded (the first engine shots read them as albedo and came
    # out washed out: grey ink, pale brass), so they are decoded to linear here before the room lights them.
    decoded = _expression(mat, "MaterialExpressionPower", -850, -100, {"const_exponent": 2.2})
    _connect(tex, "RGB", decoded, "Base")
    colour = _expression(mat, "MaterialExpressionMultiply", -700, 0)
    _connect(decoded, "", colour, "A")
    _connect(tint, "", colour, "B")
    cut = _expression(mat, "MaterialExpressionLinearInterpolate", -700, 380, {"const_a": 1.0})
    _connect(tex, "A", cut, "B")
    _connect(from_tex, "", cut, "Alpha")
    mask = _expression(mat, "MaterialExpressionMultiply", -400, 400)
    _connect(cut, "", mask, "A")
    _connect(tint, "A", mask, "B")
    rough = _expression(mat, "MaterialExpressionConstant", -400, 150, {"r": 0.85})
    spec = _expression(mat, "MaterialExpressionConstant", -400, 250, {"r": 0.3})
    for expr, prop in ((colour, "MP_BASE_COLOR"), (rough, "MP_ROUGHNESS"), (spec, "MP_SPECULAR"), (mask, "MP_OPACITY_MASK")):
        if not mel.connect_material_property(expr, "", getattr(unreal.MaterialProperty, prop)):
            raise RuntimeError("could not connect %s of %s" % (prop, path))
    mel.recompile_material(mat)
    assets.save(mat)
    return mat


def horizon_colour(extent_m):
    """sRGB hex for the horizon ring this wide, or None."""
    width = max(extent_m[0], extent_m[2])
    if width < HORIZON_MIN_EXTENT_M:
        return None
    radius = width / 2.0
    return min(HORIZON_COLOURS, key=lambda rc: abs(rc[0] - radius))[1]


def convert_unlit(mis, facts, report):
    """Move Interchange's MI_Unlit_* instances onto the display-referred masters (idempotent)."""
    mel = unreal.MaterialEditingLibrary
    masters = {False: build_unlit_master(UNLIT_MASTER, False), True: build_unlit_master(UNLIT_MASTER_TRANSLUCENT, True)}
    done, pools, failed = [], [], []
    for name, mi in mis.items():
        parent = util.get_prop(mi, "parent")
        parent_path = parent.get_path_name() if parent is not None else ""
        ours = parent_path.startswith(UNLIT_MASTER)
        if not (ours or parent_path.startswith(INTERCHANGE_UNLIT)):
            continue
        translucent = "Blend" in parent_path or "Translucent" in parent_path
        fact = facts.get(name, {})
        alpha = float(fact.get("alpha", 1.0))
        if translucent and alpha < UNLIT_POOL_ALPHA:
            pools.append(name)
            continue
        try:
            if not ours:
                mel.set_material_instance_parent(mi, masters[translucent])
            if translucent:
                mel.set_material_instance_scalar_parameter_value(mi, "Opacity", alpha)
            hexcol = None if fact.get("textured", True) else horizon_colour(fact.get("extent_m", [0.0, 0.0, 0.0]))
            if hexcol is not None:
                r, g, b = (util.srgb_to_linear(c) for c in util.hex_rgb(hexcol))
                mel.set_material_instance_vector_parameter_value(mi, "BaseColorFactor", unreal.LinearColor(r, g, b, 1.0))
            mel.update_material_instance(mi)
            util.assets().save(mi)
            done.append(name)
        except Exception as exc:
            failed.append(name)
            log.warn("unlit %s not converted: %s" % (name, exc))
    report["unlit_materials"] = len(done)
    report["unlit_pools_left"] = len(pools)
    if failed:
        report["unlit_materials_failed"] = failed
    return set(done)


def quiet_emitters(glows, unlit, report):
    """Glow and converted unlit meshes stay out of Lumen's GI; glows also cast no shadow."""
    counts = {"glow": 0, "unlit": 0}
    for actor in util.find_actors(class_name="StaticMeshActor"):
        comp = util.get_prop(actor, "static_mesh_component")
        if comp is None:
            continue
        try:
            names = set(util.object_name(m) for m in comp.get_materials() if m is not None)
        except Exception:
            continue
        if names & glows:
            props, kind = {"cast_shadow": False, "affect_dynamic_indirect_lighting": False}, "glow"
        elif names & unlit:
            props, kind = {"affect_dynamic_indirect_lighting": False}, "unlit"
        else:
            continue
        if not util.set_props(comp, props, label=util.actor_label(actor)):
            counts[kind] += 1
    report["quiet_glow_meshes"] = counts["glow"]
    report["quiet_unlit_meshes"] = counts["unlit"]


def run(report):
    """Calibrate glows, convert unlit pictures and quiet their meshes. Fills report; returns a list of errors."""
    if getattr(unreal, "MaterialEditingLibrary", None) is None:
        return ["MaterialEditingLibrary missing (Editor Scripting Utilities)"]
    facts = glb_materials()
    mis = {}
    for _path, mi in util.find_assets(paths.CAMPUS_PATH, "MaterialInstanceConstant"):
        mis[util.object_name(mi)] = mi
    errors = []
    glows = calibrate_glows(mis, facts, report)
    if not glows:
        errors.append("no glow materials calibrated")
    try:
        unlit = convert_unlit(mis, facts, report)
    except Exception as exc:
        unlit = set()
        errors.append("unlit conversion failed: %s" % exc)
    quiet_emitters(glows, unlit, report)
    try:
        build_widget_material()
        report["widget_material"] = WIDGET_LIT
    except Exception as exc:
        errors.append("widget material failed: %s" % exc)
    return errors
