"""Build Walk the Archive's people as MetaHumans (UE 5.8 MetaHuman Character Python API).

Run inside the open editor (started from the Epic Games Launcher, signed in):
    import wta_people.build as b
    b.run(["margaret"])                          # every step
    b.run(["margaret"], steps="look")            # local look only: create, face, body, skin, eyes, wardrobe
    b.run(["margaret"], steps="rig,textures,build,idle,save")
Steps, in order: create, face, body, skin, eyes, makeup, wardrobe, rig, textures, build, idle, save.
Each step prints one line: WTA_PEOPLE {"id", "step", "ok", ...}.

Looks come from people.json next to this file. Assets: /Game/WTA/Characters/<id>/MHC_<id>; the build
writes the assembled Blueprint under /Game/WTA/Characters/<id>/ and shared assets under
/Game/WTA/Characters/Common. The idle step makes Common/Anims/AS_WTA_StandIdle (the pose every person uses).
"""
from __future__ import annotations

import json
import os
import time

import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC_FILE = os.path.join(HERE, "people.json")
CHAR_ROOT = "/Game/WTA/Characters"
COMMON_FOLDER = CHAR_ROOT + "/Common"
PRESETS = "/MetaHumanCharacter/Optional/Presets"
GROOMS = "/MetaHumanCharacter/Optional/Grooms/Bindings"
CLOTHING = "/MetaHumanCharacter/Optional/Clothing"
# Outfits imported from Fab (.mhpkg), one folder each, e.g. /Game/Outfits/techwearOutfit/WI_OA_techwearOutfit
FAB_OUTFITS = "/Game/Outfits"
ALL_STEPS = ["create", "face", "body", "skin", "eyes", "makeup", "wardrobe", "rig", "textures", "build", "idle",
             "save"]
STEP_GROUPS = {
    "all": ALL_STEPS,
    "look": ["create", "face", "body", "skin", "eyes", "makeup", "wardrobe", "save"],
    "cloud": ["rig", "textures"],
}
# Steps that work on shared assets, outside the MetaHuman editing session.
NO_EDIT_STEPS = ("create", "idle", "save")
# The idle every person plays (C++ UWTAPeopleLibrary::DefaultIdlePath) and the body skeleton every build shares.
IDLE_SOURCE = "/MetaHumanCharacter/Optional/Animation/UEFNAnimPreset/Locomotion/AS_MH_Neutral_Stand_Idle_Loop"
IDLE_COPY = COMMON_FOLDER + "/Anims/AS_WTA_StandIdle"
BODY_SKELETON = COMMON_FOLDER + "/Female/Medium/NormalWeight/Body/metahuman_base_skel"
# people.json wardrobe key -> (slot name, folder of its Wardrobe Items)
WARDROBE = {
    "hair": ("Hair", GROOMS + "/Hair"),
    "eyebrows": ("Eyebrows", GROOMS + "/Eyebrows"),
    "beard": ("Beard", GROOMS + "/Beards"),
    "mustache": ("Mustache", GROOMS + "/Mustaches"),
    "eyelashes": ("Eyelashes", GROOMS + "/Eyelashes"),
    "peachfuzz": ("Peachfuzz", GROOMS + "/Peachfuzz"),
    "outfit": ("Outfits", CLOTHING),
}
# people.json groom colour keys -> instance parameter names (UMetaHumanDefaultGroomPipelineMaterialParameters)
GROOM_PARAMS = {"melanin": "Melanin", "redness": "Redness", "roughness": "Roughness",
                "whiteness": "Whiteness", "lightness": "Lightness"}
# people.json outfit colour keys -> instance parameter names, per outfit wardrobe item. An outfit entry may
# also carry "params": {<exact parameter name>: value} for anything not mapped here.
OUTFIT_PARAMS = {
    "WI_DefaultGarment": {"shirt": "PrimaryColorShirt", "shirt2": "SecondaryColorShirt",
                          "bottom": "PrimaryColorShort", "bottom2": "SecondaryColorShort"},
    # Epic's free MetaHuman Techwear Outfit (Fab): jacket, long pants, shoes
    "WI_OA_techwearOutfit": {"jacket": "JacketBodyColor", "yoke": "JacketYokeColor", "cuffs": "JacketCuffsColor",
                             "trim": "JacketTrimColor", "pants": "PantsPrimaryColor", "pants_cuffs": "PantsCuffsColor",
                             "shoes": "ShoesPrimaryColor", "shoes2": "ShoesSecondaryColor", "soles": "ShoesSoles"},
    # Street Wear 12 (Fab): hoodie, shorts, sneakers, fixed colours
    "WI_Street_Wear_12": {},
}
BODY_PARAMS = {"masculine_feminine": "Masculine/Feminine", "fat": "Fat", "muscularity": "Muscularity"}


# ---------------------------------------------------------------------------------------------
# helpers

def _sub():
    return unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)


def report(pid, step, ok=True, **extra):
    data = {"id": pid, "step": step, "ok": bool(ok)}
    data.update(extra)
    print("WTA_PEOPLE " + json.dumps(data, default=str))


def load_specs():
    with open(SPEC_FILE, encoding="utf-8") as fh:
        data = json.load(fh)
    defaults = data.get("defaults", {})
    people = {}
    for p in data["people"]:
        merged = dict(defaults)
        merged.update(p)
        people[p["id"]] = merged
    return people


def char_path(pid):
    return "%s/%s/MHC_%s" % (CHAR_ROOT, pid, pid)


def _srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_color(text):
    """'#rrggbb' (sRGB, as written in the briefs) -> LinearColor."""
    h = text.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return unreal.LinearColor(_srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b), 1.0)


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def skin_uv_from_hex(text):
    """Approximate MetaHuman skin tone (u, v) for a brief's sRGB skin colour.

    u follows CIELAB lightness (L* 85 -> 0.1 light, L* 25 -> 0.95 dark); v follows the hue angle
    (redder ~45 deg -> 0.85, yellower/olive ~70 deg -> 0.3). Eyeball the preview and adjust.
    """
    import math
    h = text.lstrip("#")
    rgb = [_srgb_to_linear(int(h[i:i + 2], 16)) for i in (0, 2, 4)]
    x = 0.4124 * rgb[0] + 0.3576 * rgb[1] + 0.1805 * rgb[2]
    y = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    z = 0.0193 * rgb[0] + 0.1192 * rgb[1] + 0.9505 * rgb[2]

    def f(t):
        return t ** (1.0 / 3.0) if t > 0.008856 else 7.787 * t + 16.0 / 116.0
    fx, fy, fz = f(x / 0.95047), f(y / 1.0), f(z / 1.08883)
    lightness = 116.0 * fy - 16.0
    a, b = 500.0 * (fx - fy), 200.0 * (fy - fz)
    hue = math.degrees(math.atan2(b, a))
    u = _clamp(0.1 + (85.0 - lightness) / 60.0 * 0.85, 0.02, 0.98)
    v = _clamp(0.85 - (hue - 45.0) / 25.0 * 0.55, 0.05, 0.95)
    return round(u, 3), round(v, 3)


class Editing:
    """Register a character with the MetaHuman subsystem for the duration of a block."""

    def __init__(self, character):
        self.character = character
        self.added = False

    def __enter__(self):
        sub = _sub()
        if sub.is_object_added_for_editing(self.character):
            return self.character
        unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).close_all_editors_for_asset(self.character)
        if not sub.try_add_object_to_edit(self.character):
            raise RuntimeError("cannot edit %s (open in another editor?)" % self.character.get_name())
        self.added = True
        return self.character

    def __exit__(self, *exc):
        if self.added and _sub().is_object_added_for_editing(self.character):
            _sub().remove_object_to_edit(self.character)
        return False


def _preset(name):
    return unreal.load_asset("%s/%s.%s" % (PRESETS, name, name))


def _coefficients(character):
    sub = _sub()
    if sub.is_object_added_for_editing(character):
        return list(sub.get_face_model_coefficients(character))
    if not sub.try_add_object_to_edit(character):
        raise RuntimeError("cannot read face of %s" % character.get_name())
    try:
        return list(sub.get_face_model_coefficients(character))
    finally:
        sub.remove_object_to_edit(character)


def _preset_cache_file():
    folder = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
    return os.path.join(folder, "WTA", "preset_face_coefficients.json")


_PRESET_FACES = {}


def preset_coefficients(name):
    """Face-model coefficients of an Epic preset, cached in Saved/WTA (opening a preset for edit is
    slow and holds a lot of memory, and the presets never change)."""
    if not _PRESET_FACES:
        try:
            with open(_preset_cache_file(), encoding="utf-8") as fh:
                _PRESET_FACES.update(json.load(fh))
        except (OSError, ValueError):
            pass
    if name not in _PRESET_FACES:
        _PRESET_FACES[name] = _coefficients(_preset(name))
        path = _preset_cache_file()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(_PRESET_FACES, fh)
    return _PRESET_FACES[name]


# ---------------------------------------------------------------------------------------------
# steps (each takes the person spec and the character; all but create need it open for editing)

def step_create(spec, _character=None):
    """Copy the preset into /Game/WTA/Characters/<id>/MHC_<id> once; later runs reuse it."""
    path = char_path(spec["id"])
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.load_asset(path), "exists"
    preset = spec.get("preset")
    if preset:
        src = "%s/%s" % (PRESETS, preset)
        character = unreal.EditorAssetLibrary.duplicate_asset(src, path)
        if character is None:
            raise RuntimeError("could not copy preset " + src)
        return character, "from preset " + preset
    character = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "MHC_" + spec["id"], "%s/%s" % (CHAR_ROOT, spec["id"]), unreal.MetaHumanCharacter,
        unreal.new_object(unreal.MetaHumanCharacterFactoryNew))
    return character, "new"


def step_face(spec, character):
    """Blend the face toward other presets: [["Sook-ja", 0.2], ...] (weights of the others)."""
    blend = spec.get("face_blend") or []
    if not blend:
        return "unchanged"
    # Start from the preset's own face (not the current one) so running the step again is harmless.
    base = list(preset_coefficients(spec["preset"])) if spec.get("preset") else list(_sub().get_face_model_coefficients(character))
    others = [(preset_coefficients(name), float(w)) for name, w in blend]
    keep = 1.0 - sum(w for _, w in others)
    out = []
    for i, b in enumerate(base):
        values = [c[i] for c, _ in others]
        if all(abs(v - b) < 1e-6 for v in values):
            out.append(b)  # layout entries (counts) are identical in every preset
        else:
            out.append(keep * b + sum(c[i] * w for c, w in others))
    _sub().set_face_model_coefficients(character, out)
    _sub().commit_face_state(character)
    return "blended " + ", ".join("%s %.0f%%" % (n, w * 100) for n, w in blend)


def step_body(spec, character):
    """Body: height_cm, plus masculine_feminine / fat / muscularity as 0..1 of the model range."""
    body = spec.get("body") or {}
    if not body:
        return "unchanged"
    sub = _sub()
    constraints = sub.get_body_constraints(character, False)
    by_name = {str(c.name): c for c in constraints}
    done = []
    if "height_cm" in body and "Height" in by_name:
        c = by_name["Height"]
        c.is_active = True
        c.target_measurement = _clamp(float(body["height_cm"]), c.min_measurement, c.max_measurement)
        done.append("height %.0f" % c.target_measurement)
    for key, name in BODY_PARAMS.items():
        if key in body and name in by_name:
            c = by_name[name]
            c.is_active = True
            c.target_measurement = c.min_measurement + (c.max_measurement - c.min_measurement) * _clamp(float(body[key]), 0.0, 1.0)
            done.append("%s %.2f" % (key, body[key]))
    for name, value in (body.get("measurements") or {}).items():
        if name in by_name:
            c = by_name[name]
            c.is_active = True
            c.target_measurement = _clamp(float(value), c.min_measurement, c.max_measurement)
            done.append("%s %.1f" % (name, value))
    sub.set_body_constraints(character, list(by_name.values()))
    sub.commit_body_state(character)
    return ", ".join(done)


def step_skin(spec, character):
    """Skin tone (u: 0 light..1 dark, v: 0 cool..1 red), texture variant, roughness, freckles."""
    skin = spec.get("skin") or {}
    if not skin:
        return "unchanged"
    settings = character.skin_settings
    props = settings.skin
    if "hex" in skin and "u" not in skin:
        skin = dict(skin)
        skin["u"], skin["v"] = skin_uv_from_hex(skin["hex"])
    for key in ("u", "v", "roughness", "face_texture_index", "body_texture_index", "show_top_underwear"):
        if key in skin:
            setattr(props, key, skin[key])
    settings.skin = props
    if "freckles" in skin:
        fr = settings.freckles
        for key, value in skin["freckles"].items():
            setattr(fr, key, value)
        settings.freckles = fr
    _sub().commit_skin_settings(character, settings)
    return "u %.2f v %.2f" % (props.u, props.v)


def step_eyes(spec, character):
    """Iris colour: u = 0 cool (blue/grey/green) .. 1 warm (brown/amber), v = 0 dark .. 1 light."""
    eyes = spec.get("eyes") or {}
    if not eyes:
        return "unchanged"
    settings = character.eyes_settings
    for side in ("eye_left", "eye_right"):
        eye = getattr(settings, side)
        iris = eye.iris
        iris.primary_color_u = eyes.get("u", iris.primary_color_u)
        iris.primary_color_v = eyes.get("v", iris.primary_color_v)
        iris.secondary_color_u = eyes.get("u2", eyes.get("u", iris.secondary_color_u))
        iris.secondary_color_v = eyes.get("v2", eyes.get("v", iris.secondary_color_v))
        eye.iris = iris
        setattr(settings, side, eye)
    _sub().commit_eyes_settings(character, settings)
    return "iris u %.2f v %.2f" % (eyes.get("u", -1), eyes.get("v", -1))


def step_makeup(spec, character):
    """Makeup: 'none' clears foundation/eyes/blush/lips; otherwise leaves the preset's."""
    makeup = spec.get("makeup")
    if makeup != "none":
        return "unchanged"
    settings = character.makeup_settings
    found = settings.foundation
    found.apply_foundation = False
    settings.foundation = found
    eyes = settings.eyes
    eyes.type = unreal.MetaHumanCharacterEyeMakeupType.NONE
    settings.eyes = eyes
    blush = settings.blush
    blush.type = unreal.MetaHumanCharacterBlushMakeupType.NONE
    settings.blush = blush
    lips = settings.lips
    lips.type = unreal.MetaHumanCharacterLipsMakeupType.NONE
    settings.lips = lips
    _sub().commit_makeup_settings(character, settings)
    return "none"


def _wardrobe_item(folder, name):
    """A wardrobe item by full path, by name in its Core Data folder, or by name under /Game/Outfits (Fab)."""
    if name.startswith("/"):
        asset = unreal.load_asset(name)
    else:
        asset = unreal.load_asset("%s/%s.%s" % (folder, name, name))
        if asset is None and unreal.EditorAssetLibrary.does_directory_exist(FAB_OUTFITS):
            for path in unreal.EditorAssetLibrary.list_assets(FAB_OUTFITS, recursive=True, include_folder=False):
                if path.split("/")[-1].split(".")[0] == name:
                    asset = unreal.load_asset(path)
                    break
    if asset is None:
        raise RuntimeError("wardrobe item not found: %s (looked in %s and %s)" % (name, folder, FAB_OUTFITS))
    return asset


def _item_key(collection, slot, item):
    keys = [k for k in collection.get_item_keys_for_wardrobe_item(item) if str(collection.get_item_slot_name(k)) == slot]
    if keys:
        return keys[0]
    return collection.try_add_item_from_wardrobe_item(slot, item)


def _set_params(params, values):
    """values: {param name: float | '#rrggbb' | bool}. Returns the names that were set."""
    done = []
    for p in params:
        name = str(p.name)
        if name not in values:
            continue
        v = values[name]
        if isinstance(v, bool):
            p.set_bool(v)
        elif isinstance(v, str) and v.startswith("#"):
            p.set_color(hex_color(v))
        else:
            p.set_float(float(v))
        done.append(name)
    return done


def step_wardrobe(spec, character):
    """Pick one item per slot (null clears the slot), then set groom colours and outfit colours."""
    sub = _sub()
    coll = character.internal_collection
    inst = coll.default_instance
    chosen = {}
    for key, (slot, folder) in WARDROBE.items():
        if key not in spec:
            continue
        entry = spec[key]
        if entry is None:
            inst.set_single_slot_selection(slot, unreal.MetaHumanPaletteItemKey())
            chosen[slot] = None
            continue
        name = entry["item"] if isinstance(entry, dict) else entry
        item_key = _item_key(coll, slot, _wardrobe_item(folder, name))
        inst.set_single_slot_selection(slot, item_key)
        chosen[slot] = (name, item_key, entry if isinstance(entry, dict) else {})

    # Instance parameters live on the subsystem's preview collection, which is copied from the asset
    # when the character is registered for editing: re-register so it sees the items added above.
    sub.remove_object_to_edit(character)
    if not sub.try_add_object_to_edit(character):
        raise RuntimeError("could not re-open %s for editing" % character.get_name())
    sub.assemble_for_preview(character)
    preview = sub.get_preview_collection(character)
    pinst = preview.default_instance
    set_names = []
    for slot, value in chosen.items():
        if not value:
            continue
        name, item_key, entry = value
        wanted = {}
        if slot == "Outfits":
            for k, pname in OUTFIT_PARAMS.get(name.split("/")[-1].split(".")[0], {}).items():
                if k in entry:
                    wanted[pname] = entry[k]
            wanted.update(entry.get("params", {}))
        else:
            for k, pname in GROOM_PARAMS.items():
                if k in entry:
                    wanted[pname] = entry[k]
            if "dye" in entry:
                wanted["DyeColor"] = entry["dye"]
        if not wanted:
            continue
        short = name.split("/")[-1].split(".")[0]
        keys = [k for k in preview.get_item_keys_for_slot(slot) if str(unreal.MetaHumanPaletteKeyBlueprintLibrary.to_asset_name_string(k)) == short]
        if not keys:
            report(spec["id"], "wardrobe", False, error="no preview item for " + name)
            continue
        params = pinst.get_instance_parameters(unreal.MetaHumanPaletteItemPath(item_key=keys[0]))
        set_names += ["%s.%s" % (slot, n) for n in _set_params(params, wanted)]
    sub.on_edit_preview_collection(character)
    return {"slots": {s: (v[0] if v else None) for s, v in chosen.items()}, "params": set_names}


def _log_file():
    folder = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_log_dir())
    return os.path.join(folder, unreal.SystemLibrary.get_game_name() + ".log")


def _log_mark():
    path = _log_file()
    return os.path.getsize(path) if os.path.exists(path) else 0


def _log_since(mark):
    """Editor log text written since _log_mark() (the cloud calls report results only there)."""
    unreal.SystemLibrary.execute_console_command(None, "FlushLog")
    path = _log_file()
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as fh:
        fh.seek(mark)
        return fh.read().decode("utf-8", "replace")


CLOUD_FAILURES = ("Auto-Rigging of Face failed", "Auto-Rigging failed", "Login failed",
                  "Download of source face textures failed", "Download of source body textures failed")


def _cloud_check(text, what):
    for line in text.splitlines():
        if any(f in line for f in CLOUD_FAILURES):
            raise RuntimeError("%s failed: %s" % (what, line.split("]", 2)[-1].strip()))


def step_rig(spec, character):
    """Epic's auto-rig service (needs the Epic sign-in; a browser page opens the first time)."""
    params = unreal.MetaHumanCharacterAutoRiggingRequestParams()
    params.blocking = True
    params.report_progress = False
    params.rig_type = getattr(unreal.MetaHumanRigType, spec.get("rig", "JOINTS_ONLY"))
    t0 = time.time()
    mark = _log_mark()
    _sub().request_auto_rigging(character, params)
    text = _log_since(mark)
    _cloud_check(text, "auto-rig")
    if "Auto-Rigging finished" not in text:
        report(spec["id"], "rig", True, warning="no 'Auto-Rigging finished' line in the log yet")
    return "%s in %.0fs" % (spec.get("rig", "JOINTS_ONLY"), time.time() - t0)


def step_textures(spec, character):
    """Download the 2K source textures from Epic's texture service."""
    params = unreal.MetaHumanCharacterTextureRequestParams()
    params.blocking = True
    params.report_progress = False
    t0 = time.time()
    mark = _log_mark()
    _sub().request_texture_sources(character, params)
    _cloud_check(_log_since(mark), "texture download")
    if not character.has_high_resolution_textures:
        raise RuntimeError("texture download finished without high-resolution textures")
    return "in %.0fs" % (time.time() - t0)


RIG_GRAPH_NOTICE = "Cannot break link"


def step_build(spec, character):
    sub = _sub()
    if not sub.can_build_meta_human(character, True):
        raise RuntimeError("not ready to build (needs rig + downloaded textures; see the log)")
    params = unreal.MetaHumanCharacterEditorBuildParameters()
    params.pipeline_type = unreal.MetaHumanDefaultPipelineType.OPTIMIZED
    params.pipeline_quality = getattr(unreal.MetaHumanQualityLevel, spec.get("quality", "MEDIUM"))
    params.absolute_build_path = CHAR_ROOT
    params.name_override = spec["id"]
    params.common_folder_path = COMMON_FOLDER
    t0 = time.time()
    note = ""
    try:
        sub.build_meta_human(character, params)
    except RuntimeError as exc:
        # The build copies Epic's face Control Rigs into Common and tidies their graphs. On 5.8 the
        # tidy-up logs "Cannot break link ..." for a few reroute nodes, and Python turns those log
        # errors into this exception after the build has finished. Accept it only when that is all
        # it says and the Blueprint was written.
        lines = [line.strip() for line in str(exc).splitlines() if line.strip()]
        blueprint = "%s/%s/BP_%s" % (CHAR_ROOT, spec["id"], spec["id"])
        if not (lines and all(RIG_GRAPH_NOTICE in line for line in lines)
                and unreal.EditorAssetLibrary.does_asset_exist(blueprint)):
            raise
        note = ", ignored %d Control Rig '%s' notices" % (len(lines), RIG_GRAPH_NOTICE)
    return "%s in %.0fs%s" % (spec.get("quality", "MEDIUM"), time.time() - t0, note)


def step_idle(spec, character):
    """Copy Epic's neutral stand idle next to the built people and move it onto their Common body skeleton,
    so nothing the game loads points into the MetaHuman Creator plugin. Needs one finished build."""
    eal = unreal.EditorAssetLibrary
    if not eal.does_asset_exist(BODY_SKELETON):
        raise RuntimeError("no %s yet; build someone first" % BODY_SKELETON)
    if not eal.does_asset_exist(IDLE_COPY) and eal.duplicate_asset(IDLE_SOURCE, IDLE_COPY) is None:
        raise RuntimeError("could not copy " + IDLE_SOURCE)
    anim = unreal.load_asset(IDLE_COPY)
    if not unreal.WTAPeopleLibrary.set_animation_skeleton(anim, unreal.load_asset(BODY_SKELETON)):
        raise RuntimeError("could not move %s onto %s" % (IDLE_COPY, BODY_SKELETON))
    eal.save_asset(IDLE_COPY, only_if_is_dirty=True)
    return "%s on %s (%.1fs)" % (IDLE_COPY.split("/")[-1], BODY_SKELETON.split("/")[-1], anim.get_play_length())


def step_save(spec, character):
    folder = "%s/%s" % (CHAR_ROOT, spec["id"])
    saved = unreal.EditorAssetLibrary.save_directory(folder, only_if_is_dirty=True, recursive=True)
    if unreal.EditorAssetLibrary.does_directory_exist(COMMON_FOLDER):
        unreal.EditorAssetLibrary.save_directory(COMMON_FOLDER, only_if_is_dirty=True, recursive=True)
    return "saved %s" % saved


STEPS = {"create": step_create, "face": step_face, "body": step_body, "skin": step_skin, "eyes": step_eyes,
         "makeup": step_makeup, "wardrobe": step_wardrobe, "rig": step_rig, "textures": step_textures,
         "build": step_build, "idle": step_idle, "save": step_save}


def _steps(steps):
    if isinstance(steps, str):
        names = []
        for part in steps.split(","):
            part = part.strip()
            names += STEP_GROUPS.get(part, [part])
        steps = names
    unknown = [s for s in steps if s not in STEPS]
    if unknown:
        raise ValueError("unknown steps %s (known: %s)" % (unknown, ALL_STEPS))
    return [s for s in ALL_STEPS if s in steps]


def run(ids=None, steps="all"):
    """Build the given people (default: everyone in people.json). Returns {id: ok}."""
    people = load_specs()
    ids = ids or list(people)
    order = _steps(steps)
    results = {}
    for pid in ids:
        spec = people[pid]
        ok = True
        character = None
        if "create" in order:
            try:
                character, note = step_create(spec)
                report(pid, "create", True, note=note)
            except Exception as exc:  # noqa: BLE001
                report(pid, "create", False, error=str(exc))
                results[pid] = False
                continue
        else:
            character = unreal.load_asset(char_path(pid))
            if character is None:
                report(pid, "load", False, error="no " + char_path(pid) + "; run the create step")
                results[pid] = False
                continue
        rest = [s for s in order if s not in NO_EDIT_STEPS]
        if rest:
            with Editing(character):
                for step in rest:
                    t0 = time.time()
                    try:
                        note = STEPS[step](spec, character)
                        report(pid, step, True, note=note, seconds=round(time.time() - t0, 1))
                    except Exception as exc:  # noqa: BLE001
                        report(pid, step, False, error=str(exc), seconds=round(time.time() - t0, 1))
                        ok = False
                        if "Login" in str(exc):
                            results[pid] = False
                            report(pid, "batch", False, error="Epic sign-in needed; stopping the batch")
                            return results
                        break
        if "idle" in order and ok:
            t0 = time.time()
            try:
                report(pid, "idle", True, note=step_idle(spec, character), seconds=round(time.time() - t0, 1))
            except Exception as exc:  # noqa: BLE001
                report(pid, "idle", False, error=str(exc))
                ok = False
        if "save" in order:
            try:
                report(pid, "save", True, note=step_save(spec, character))
            except Exception as exc:  # noqa: BLE001
                report(pid, "save", False, error=str(exc))
                ok = False
        results[pid] = ok
        character = None
        unreal.SystemLibrary.collect_garbage()  # each MetaHuman holds a few GB while edited
    return results


def describe(pid):
    """Print what a built character holds: selections, the colour parameters, skin and readiness."""
    character = unreal.load_asset(char_path(pid))
    sub = _sub()
    keylib = unreal.MetaHumanPaletteKeyBlueprintLibrary
    sel = unreal.MetaHumanPipelineSlotSelectionBlueprintLibrary
    out = {"skin": [round(character.skin_settings.skin.u, 3), round(character.skin_settings.skin.v, 3)],
           "high_res_textures": character.has_high_resolution_textures}
    with Editing(character):
        out["can_build"] = sub.can_build_meta_human(character, False)
        sub.assemble_for_preview(character)
        preview = sub.get_preview_collection(character)
        pinst = preview.default_instance
        slots = {}
        for d in pinst.get_slot_selection_data():
            s = d.selection
            slot = str(sel.get_selected_slot_name(s))
            key = sel.get_selected_item_key(s)
            name = str(keylib.to_asset_name_string(key))
            vals = {}
            for p in pinst.get_instance_parameters(unreal.MetaHumanPaletteItemPath(item_key=key)):
                t = str(p.type).upper()
                if "COLOR" in t:
                    c = p.get_color()
                    vals[str(p.name)] = "%.3f %.3f %.3f" % (c.r, c.g, c.b)
                elif "FLOAT" in t:
                    vals[str(p.name)] = round(p.get_float(), 3)
            slots[slot] = {"item": name, "params": {k: v for k, v in vals.items() if k in list(GROOM_PARAMS.values()) + list(OUTFIT_PARAMS.values())}}
        out["slots"] = slots
    print("WTA_PEOPLE_DESCRIBE " + json.dumps({pid: out}, default=str))
    return out
