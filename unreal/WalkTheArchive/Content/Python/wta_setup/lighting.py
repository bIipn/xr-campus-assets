"""Step 6: photoreal lighting for L_Campus (Lumen, physical units, no light build).

Units and exposure, decided here and consistent with docs/reference/render.md section 10:
  * Every light is physical. DirectionalLight intensity is always lux; point, spot and rect lights are set
    to lumens. The sun is SUN_LUX (75 000 lux: clear sky at 51 deg elevation, slightly below the 100 klx
    textbook value so the galleries' roof glass does not blow out), with the SkyAtmosphere driven by it
    and a real-time captured SkyLight.
  * With physical lights an outdoor view meters at about EV100 13-15 and a lamp-lit interior at EV100 5-9,
    so the PostProcessVolume uses histogram auto exposure clamped to EV100 PPV_MIN_EV..PPV_MAX_EV (4..15),
    local exposure contrast 0.8 (windows versus rooms), subtle bloom and vignette, film grain off.
    The histogram aims the average at mid grey, which shows white-walled rooms as grey ones, so the
    Workshop School gets an exposure compensation volume (WING_EXPOSURE_BIAS).
  * Interior lights come from Pipeline/out/campus/lights.json (three.js lamps, by wing) and
    Pipeline/out/reading_room/lights.json (Blender lamps and pendants). three.js intensities and Blender
    watts are not photometric, so the lumen values are chosen per fixture type (assets.md section 1.6):
    gallery and hall ceiling lights 8000 lm, wax hall ceiling lights 6000 lm, reading lamps 900 lm,
    pendants 9000 lm, plus a RectLight under the Reading Room laylight.
  * The Workshop School is lit like a real school: one RectLight under every ceiling panel listed in
    layout.json emissive_fixtures (PANEL_LUMENS each, pointing down, the panel's own size) instead of the
    single three.js fill lamp per room, which lit the rooms from mid-air and left the panels dark. The
    museum's ceiling discs become real downlights too (DOWNLIGHT_LUMENS each, a wide SpotLight).
  * Self-lit surfaces (the web's glows and unlit pictures) are calibrated by emissive.py: physical
    luminance for light fixtures, display referred for windows, screens and labels.
  * One SpotLight per gallery exhibit (600 lm, 30 degree cone) 180 cm out from the wall and 100 cm above
    the art, aimed at the art, and one per Wax Hall stage. These picture lights carry most of the realism.
All lights are movable, tagged WTA_Setup / WTA_lighting, and live in Outliner folders Lighting/<wing>.
"""
import re

import unreal

from . import emissive
from . import log
from . import paths
from . import util

STEP = "lighting"

SUN_LUX = 75000.0
SUN_COLOR_SRGB = "#fff0dc"
PPV_MIN_EV = 4.0
PPV_MAX_EV = 15.0
ART_SPOT_LUMENS = 600.0
ART_SPOT_CONE = 30.0
STAGE_SPOT_LUMENS = 1500.0
STAGE_SPOT_CONE = 45.0

# Ceiling panels (layout.json emissive_fixtures ids): a 1.2 x 0.5 m LED troffer gives about 3000-4000 lm.
PANEL_FIXTURES = ("school-hall-troffers", "studio-troffers", "lab-panels", "blueprint-panels", "world-panels")
PANEL_LUMENS = 3500.0
PANEL_RADIUS = 900.0
PANEL_WINGS = ("school",)   # wings whose three.js fill lamps the panel lights replace

# Museum ceiling discs (layout.json emissive_fixtures): wide downlights under each disc.
DOWNLIGHT_FIXTURES = ("museum-ceiling-discs",)
DOWNLIGHT_LUMENS = 2000.0
DOWNLIGHT_CONE = 55.0       # outer half angle (degrees)
DOWNLIGHT_RADIUS = 900.0

# Exposure compensation (EV) on a PostProcessVolume around a wing's rooms (layout.json wings / rooms).
WING_EXPOSURE_BIAS = {"school": 0.7}
WING_PPV_BLEND_CM = 150.0
BRUSH_SIZE = 200.0          # a volume spawned from its class has the default 200 cm cube brush

# Lumens per fixture family (see the module docstring).
LUMENS = {
    "museum": 8000.0,
    "wax": 6000.0,
    "lib": 9000.0,
    "school": 6000.0,           # only used when layout.json lists no school ceiling panels
    "reading_lamp": 900.0,
    "reading_pendant": 9000.0,
    "laylight": 8000.0,
}


def light_component(actor):
    for name in ("light_component", "sky_light_component"):
        comp = util.get_prop(actor, name)
        if comp is not None:
            return comp
    return None


def make_movable(comp):
    mob = util.enum_value("ComponentMobility", "MOVABLE")
    if comp is None or mob is None:
        return
    try:
        comp.set_mobility(mob)
    except Exception:
        try:
            comp.set_editor_property("mobility", mob)
        except Exception:
            pass


def set_light_color(comp, rgb_srgb):
    try:
        comp.set_light_color(unreal.LinearColor(rgb_srgb[0], rgb_srgb[1], rgb_srgb[2], 1.0), True)
        return
    except Exception:
        pass
    try:
        comp.set_editor_property("light_color", unreal.Color(int(rgb_srgb[0] * 255), int(rgb_srgb[1] * 255),
                                                            int(rgb_srgb[2] * 255), 255))
    except Exception as exc:
        log.warn("light colour not settable: %s" % exc)


def set_lumens(comp, lumens, radius_cm, source_radius_cm=2.0):
    """Units first, then intensity: changing the unit converts the stored intensity.

    source_radius_cm=None skips the property (RectLights have no source radius).
    """
    units = util.enum_value("LightUnits", "LUMENS")
    if units is not None:
        util.set_props(comp, {"intensity_units": units}, label="light")
    props = {
        "intensity": float(lumens),
        "attenuation_radius": float(radius_cm),
        "cast_shadows": True,
    }
    if source_radius_cm is not None:
        props["source_radius"] = float(source_radius_cm)
    util.set_props(comp, props, label="light")


def spawn_light(cls_name, location, rotation, label, folder):
    cls = getattr(unreal, cls_name, None)
    if cls is None:
        raise RuntimeError("unreal.%s missing" % cls_name)
    actor = util.spawn_class(cls, location, rotation, step=STEP, label=label, folder="Lighting/" + folder)
    comp = light_component(actor)
    make_movable(comp)
    return actor, comp


def sun_rotation():
    try:
        layout = paths.read_json(paths.LAYOUT_JSON)
        for light in layout.get("lights", []):
            if light.get("id") == "sun":
                r = light.get("ue_rotation_deg", {})
                return float(r.get("pitch", -51.1)), float(r.get("yaw", -143.1))
    except Exception as exc:
        log.warn("layout sun unreadable: %s" % exc)
    return -51.1, -143.1


def build_sky(report):
    pitch, yaw = sun_rotation()
    sun, comp = spawn_light("DirectionalLight", (0.0, 0.0, 2000.0), (pitch, yaw, 0.0), "Sun", "Sky")
    failed = util.set_props(comp, {
        "intensity": SUN_LUX,
        "atmosphere_sun_light": True,
        "cast_shadows": True,
        "dynamic_shadow_distance_movable_light": 20000.0,
        "cascade_distribution_exponent": 3.0,
    }, label="Sun")
    set_light_color(comp, util.hex_rgb(SUN_COLOR_SRGB))
    report["sun"] = {"pitch": pitch, "yaw": yaw, "lux": SUN_LUX, "failed_props": failed}

    util.spawn_class(unreal.SkyAtmosphere, (0.0, 0.0, 0.0), None, step=STEP, label="SkyAtmosphere", folder="Lighting/Sky")

    sky, sky_comp = spawn_light("SkyLight", (0.0, 0.0, 1000.0), (0.0, 0.0, 0.0), "SkyLight", "Sky")
    report["skylight_failed_props"] = util.set_props(sky_comp, {
        "real_time_capture": True,
        "lower_hemisphere_is_black": False,
    }, label="SkyLight")

    if util.has("VolumetricCloud"):
        util.spawn_class(unreal.VolumetricCloud, (0.0, 0.0, 0.0), None, step=STEP, label="VolumetricCloud", folder="Lighting/Sky")
        report["clouds"] = True
    else:
        report["clouds"] = False

    fog = util.spawn_class(unreal.ExponentialHeightFog, (0.0, 0.0, 0.0), None, step=STEP, label="HeightFog", folder="Lighting/Sky")
    fog_comp = util.get_prop(fog, "component")
    if fog_comp is not None:
        # C++ bEnableVolumetricFog is enable_volumetric_fog in Python; older notes say volumetric_fog.
        if util.set_props(fog_comp, {"enable_volumetric_fog": True}, label="HeightFog"):
            util.set_props(fog_comp, {"volumetric_fog": True}, label="HeightFog")
        report["fog_failed_props"] = util.set_props(fog_comp, {
            "fog_density": 0.008,
            "fog_height_falloff": 0.1,
            "start_distance": 0.0,
            "volumetric_fog_extinction_scale": 1.0,
        }, label="HeightFog")


def build_post_process(report):
    ppv = util.spawn_class(unreal.PostProcessVolume, (0.0, 0.0, 0.0), None, step=STEP, label="PPV_Campus", folder="Lighting")
    util.set_props(ppv, {"unbound": True, "priority": 1.0}, label="PPV")
    settings = util.get_prop(ppv, "settings")
    if settings is None:
        report["ppv"] = "settings struct unreachable"
        return
    gi = util.enum_value("DynamicGlobalIlluminationMethod", "LUMEN")
    refl = util.enum_value("ReflectionMethod", "LUMEN")
    hist = util.enum_value("AutoExposureMethod", "AEM_HISTOGRAM")
    props = {}

    def want(flag, name, value):
        if value is None:
            return
        props[flag] = True
        props[name] = value

    want("override_dynamic_global_illumination_method", "dynamic_global_illumination_method", gi)
    want("override_reflection_method", "reflection_method", refl)
    want("override_auto_exposure_method", "auto_exposure_method", hist)
    want("override_auto_exposure_min_brightness", "auto_exposure_min_brightness", PPV_MIN_EV)
    want("override_auto_exposure_max_brightness", "auto_exposure_max_brightness", PPV_MAX_EV)
    want("override_auto_exposure_bias", "auto_exposure_bias", 0.0)
    want("override_auto_exposure_speed_up", "auto_exposure_speed_up", 3.0)
    want("override_auto_exposure_speed_down", "auto_exposure_speed_down", 1.0)
    want("override_local_exposure_highlight_contrast_scale", "local_exposure_highlight_contrast_scale", 0.8)
    want("override_local_exposure_shadow_contrast_scale", "local_exposure_shadow_contrast_scale", 0.8)
    want("override_film_grain_intensity", "film_grain_intensity", 0.0)
    want("override_bloom_intensity", "bloom_intensity", 0.3)
    want("override_vignette_intensity", "vignette_intensity", 0.25)
    want("override_motion_blur_amount", "motion_blur_amount", 0.0)
    failed = util.set_props(settings, props, label="PostProcessSettings")
    if "local_exposure_highlight_contrast_scale" in failed:
        # UE 5.0 spelling of the local exposure knob.
        util.set_props(settings, {"override_local_exposure_contrast_scale": True,
                                  "local_exposure_contrast_scale": 0.8}, label="PostProcessSettings")
    if "film_grain_intensity" in failed:
        util.set_props(settings, {"override_grain_intensity": True, "grain_intensity": 0.0}, label="PostProcessSettings")
    # Structs come back as copies: write the modified copy back.
    util.set_props(ppv, {"settings": settings}, label="PPV")
    report["ppv_failed_props"] = failed


def campus_lamps():
    """Point lights from Pipeline/out/campus/lights.json (three.js metres, Y up) as UE cm tuples."""
    out = []
    try:
        doc = paths.read_json(paths.CAMPUS_LIGHTS_JSON)
    except Exception as exc:
        log.warn("campus lights unreadable: %s" % exc)
        return out
    for i, lamp in enumerate(doc.get("lamps", [])):
        x, y, z = lamp.get("pos_m", [0, 0, 0])
        wing = lamp.get("wing", "museum")
        out.append({
            "label": "Lamp_%s_%02d" % (wing, i),
            "wing": wing,
            "loc": (100.0 * x, 100.0 * z, 100.0 * y),
            "rgb": util.hex_rgb(lamp.get("color_srgb", "#ffe2b9")),
            "lumens": LUMENS.get(wing, 6000.0),
            "radius": 100.0 * float(lamp.get("distance_m", 22)),
            "source_radius": 6.0,
        })
    return out


def reading_room_lamps():
    """Point lights from Pipeline/out/reading_room/lights.json (Blender watts -> lumens by fixture type)."""
    out = []
    try:
        doc = paths.read_json(paths.READING_ROOM_LIGHTS_JSON)
    except Exception as exc:
        log.warn("reading room lights unreadable: %s" % exc)
        return out
    for light in doc.get("lights", []):
        if light.get("type") != "POINT":
            continue
        x, y, z = light.get("campus_pos_m", [0, 0, 0])
        watts = float(light.get("blender_watts", 18.0))
        pendant = watts >= 100.0
        col = light.get("color_linear", [1.0, 0.8, 0.6])
        out.append({
            "label": "RR_%s_%s" % ("Pendant" if pendant else "Lamp", light.get("name", "L")),
            "wing": "lib",
            "loc": (100.0 * x, 100.0 * z, 100.0 * y),
            "rgb": (col[0] ** (1 / 2.2), col[1] ** (1 / 2.2), col[2] ** (1 / 2.2)),
            "lumens": LUMENS["reading_pendant"] if pendant else LUMENS["reading_lamp"],
            "radius": 1500.0 if pendant else 600.0,
            "source_radius": 8.0 if pendant else 2.0,
        })
    return out


def build_point_lights(report, skip_wings=()):
    count, skipped = 0, 0
    for lamp in campus_lamps() + reading_room_lamps():
        if lamp["wing"] in skip_wings:
            skipped += 1
            continue
        _actor, comp = spawn_light("PointLight", lamp["loc"], (0.0, 0.0, 0.0), lamp["label"], lamp["wing"])
        set_lumens(comp, lamp["lumens"], lamp["radius"], lamp["source_radius"])
        set_light_color(comp, lamp["rgb"])
        count += 1
    report["point_lights"] = count
    report["point_lights_replaced_by_panels"] = skipped


def layout_fixtures(ids):
    """[(id, shape, colour, [(x, y, z) three.js metres, ...]), ...] for these layout.json emissive_fixtures."""
    out = []
    try:
        fixtures = paths.read_json(paths.LAYOUT_JSON).get("emissive_fixtures", [])
    except Exception as exc:
        log.warn("layout emissive_fixtures unreadable: %s" % exc)
        return out
    for fx in fixtures:
        if fx.get("id") in ids and fx.get("positions_m"):
            out.append((fx["id"], fx.get("shape", ""), fx.get("color", "#fffaf0"), fx["positions_m"]))
    return out


def build_panel_lights(report):
    """One RectLight just under each ceiling panel's lower face, pointing down, as large as the panel.

    three.js boxes are w (x) by h (y) by d (z). With pitch -90 the light's local Y stays along world Y (the
    panel's d side) and local Z lies along world X (the w side), as for the laylight.
    """
    count = 0
    for fid, shape, colour, positions in layout_fixtures(PANEL_FIXTURES):
        m = re.match(r"box\s+([\d.]+)x([\d.]+)x([\d.]+)", shape)
        if not m:
            log.warn("panel fixture %s has no box shape (%s)" % (fid, shape))
            continue
        w, h, d = (float(v) for v in m.groups())
        for i, (x, y, z) in enumerate(positions):
            loc = (100.0 * x, 100.0 * z, 100.0 * (y - h / 2.0) - 1.0)
            _actor, comp = spawn_light("RectLight", loc, (-90.0, 0.0, 0.0), "Panel_%s_%02d" % (fid, i), "school")
            set_lumens(comp, PANEL_LUMENS, PANEL_RADIUS, None)
            util.set_props(comp, {"source_width": 100.0 * d, "source_height": 100.0 * w}, label="Panel_" + fid)
            set_light_color(comp, util.hex_rgb(colour))
            count += 1
    report["panel_lights"] = count
    return count


def build_downlights(report):
    """A wide SpotLight just under each museum ceiling disc, pointing straight down."""
    count = 0
    for fid, _shape, colour, positions in layout_fixtures(DOWNLIGHT_FIXTURES):
        for i, (x, y, z) in enumerate(positions):
            loc = (100.0 * x, 100.0 * z, 100.0 * y - 3.0)
            _actor, comp = spawn_light("SpotLight", loc, (-90.0, 0.0, 0.0), "Downlight_%s_%02d" % (fid, i), "museum")
            set_lumens(comp, DOWNLIGHT_LUMENS, DOWNLIGHT_RADIUS, 5.0)
            util.set_props(comp, {"inner_cone_angle": DOWNLIGHT_CONE * 0.6, "outer_cone_angle": DOWNLIGHT_CONE},
                           label="Downlight_" + fid)
            set_light_color(comp, util.hex_rgb(colour))
            count += 1
    report["downlights"] = count
    return count


def build_wing_exposure(report):
    """A PostProcessVolume around each wing in WING_EXPOSURE_BIAS (its rooms' union) with that compensation."""
    try:
        layout = paths.read_json(paths.LAYOUT_JSON)
    except Exception as exc:
        log.warn("layout unreadable, no exposure volumes: %s" % exc)
        return 0
    rooms = dict((r.get("id"), r) for r in layout.get("rooms", []))
    count = 0
    for wing, bias in WING_EXPOSURE_BIAS.items():
        boxes = [rooms[i]["ue_bounds_cm"] for i in layout.get("wings", {}).get(wing, [])
                 if rooms.get(i, {}).get("ue_bounds_cm")]
        if not boxes:
            log.warn("wing %s has no room bounds; no exposure volume" % wing)
            continue
        lo = [min(b["min"][k] for b in boxes) for k in range(3)]
        hi = [max(b["max"][k] for b in boxes) for k in range(3)]
        centre = tuple((lo[k] + hi[k]) / 2.0 for k in range(3))
        ppv = util.spawn_class(unreal.PostProcessVolume, centre, None, step=STEP, label="PPV_Exposure_" + wing,
                               folder="Lighting")
        ppv.set_actor_scale3d(unreal.Vector(*[(hi[k] - lo[k]) / BRUSH_SIZE for k in range(3)]))
        util.set_props(ppv, {"unbound": False, "priority": 2.0, "blend_radius": WING_PPV_BLEND_CM}, label="PPV_" + wing)
        settings = util.get_prop(ppv, "settings")
        if settings is None or util.set_props(settings, {"override_auto_exposure_bias": True,
                                                         "auto_exposure_bias": float(bias)}, label="PPV_" + wing):
            log.warn("exposure bias not settable on the %s volume" % wing)
            continue
        util.set_props(ppv, {"settings": settings}, label="PPV_" + wing)
        count += 1
    report["exposure_volumes"] = count
    return count


def build_laylight(report):
    """RectLight under the Reading Room laylight: 16 x 1.8 m panel at the ceiling, pointing down."""
    try:
        lib = paths.read_json(paths.LAYOUT_JSON).get("library", {})
        x0, x1, z0, z1 = lib.get("blender_shell", {}).get("laylight", [-30, -14, -3.9, -2.1])
        ceiling = float(lib.get("ceiling_m", 7.6))
    except Exception:
        x0, x1, z0, z1, ceiling = -30, -14, -3.9, -2.1, 7.6
    cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
    loc = (100.0 * cx, 100.0 * cz, 100.0 * ceiling - 20.0)
    _actor, comp = spawn_light("RectLight", loc, (-90.0, 0.0, 0.0), "RR_Laylight", "lib")
    set_lumens(comp, LUMENS["laylight"], 1600.0, None)
    # With pitch -90 the light's local Y stays along world Y (the 1.8 m side) and local Z along world X.
    util.set_props(comp, {
        "source_width": 100.0 * abs(z1 - z0),
        "source_height": 100.0 * abs(x1 - x0),
        "barn_door_angle": 85.0,
    }, label="RR_Laylight")
    if util.set_props(comp, {"use_temperature": True, "temperature": 5000.0}, label="RR_Laylight"):
        set_light_color(comp, (0.88, 0.93, 1.0))
    report["rect_lights"] = 1


def aimed_spot(label, folder, light_pos, target, lumens, cone):
    pitch, yaw = util.look_at(light_pos, target)
    _actor, comp = spawn_light("SpotLight", light_pos, (pitch, yaw, 0.0), label, folder)
    set_lumens(comp, lumens, 1200.0, 3.0)
    util.set_props(comp, {"inner_cone_angle": cone * 0.6, "outer_cone_angle": cone}, label=label)
    set_light_color(comp, util.hex_rgb("#fff1d6"))


def build_art_lights(report):
    count = 0
    for row in util.data_rows("Exhibits.json"):
        if row.get("bWax"):
            continue
        loc = util.xyz(row.get("Location"))
        yaw = float(row.get("Yaw", 0.0))
        fwd = util.forward_from_yaw(yaw)
        light_pos = (loc[0] + 180.0 * fwd[0], loc[1] + 180.0 * fwd[1], loc[2] + 100.0)
        wing = "lib" if int(row.get("Gallery", 0)) == 0 else "museum"
        aimed_spot("ArtLight_%s" % row["Name"], wing, light_pos, loc, ART_SPOT_LUMENS, ART_SPOT_CONE)
        count += 1
    report["art_spots"] = count


def build_stage_lights(report):
    count = 0
    for row in util.data_rows("WaxScenes.json"):
        stage = util.xyz(row.get("StageLocation"))
        yaw = float(row.get("StageYaw", 0.0))
        fwd = util.forward_from_yaw(yaw)
        # In front of the rope, high up, looking back and down at the middle of the stage.
        light_pos = (stage[0] + 150.0 * fwd[0], stage[1] + 150.0 * fwd[1], stage[2] + 330.0)
        target = (stage[0] - 150.0 * fwd[0], stage[1] - 150.0 * fwd[1], stage[2] + 90.0)
        aimed_spot("StageLight_%s" % row["Name"], "wax", light_pos, target, STAGE_SPOT_LUMENS, STAGE_SPOT_CONE)
        count += 1
    report["stage_spots"] = count


def run():
    util.wait_for_asset_registry()
    util.ensure_level_loaded()
    report = {"removed_previous": util.delete_setup_actors(STEP)}
    build_sky(report)
    build_post_process(report)
    panels = build_panel_lights(report)
    build_point_lights(report, skip_wings=PANEL_WINGS if panels else ())
    build_downlights(report)
    build_laylight(report)
    build_art_lights(report)
    build_stage_lights(report)
    build_wing_exposure(report)
    errors = emissive.run(report)
    report["lights_total"] = len(util.find_actors(tag=util.step_tag(STEP)))
    report["saved"] = util.save_level()
    if report.get("point_lights", 0) == 0:
        errors.append("no point lights created (lights.json missing?)")
    if not panels:
        errors.append("no school ceiling panel lights created (layout.json emissive_fixtures missing?)")
    if report.get("art_spots", 0) == 0:
        errors.append("no art spotlights created (Exhibits.json missing?)")
    if not report["saved"]:
        errors.append("level save reported failure")
    report["ok"] = not errors
    if errors:
        report["error"] = "; ".join(errors)
    return report
