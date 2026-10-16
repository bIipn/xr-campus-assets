"""Safe helpers around the unreal module.

Every helper probes for the UE 5.8 API first (subsystems) and falls back to the older libraries when a
name is missing, so a renamed function degrades to a warning instead of a crash. Functions that touch
actors tag them with SETUP_TAG plus a per-step tag so a re-run can delete exactly what it spawned.
"""
import json
import math
import os
import re

import unreal

from . import log
from . import paths

TAG_RE = re.compile(r"^(item|token|ride|staff|station|book|bp)__")

# ---------------------------------------------------------------------------
# Subsystems and libraries
# ---------------------------------------------------------------------------


def has(name):
    return hasattr(unreal, name)


def editor_subsystem(name):
    """unreal.get_editor_subsystem(unreal.<name>) or None when the class is missing."""
    cls = getattr(unreal, name, None)
    if cls is None:
        return None
    try:
        return unreal.get_editor_subsystem(cls)
    except Exception as exc:
        log.warn("get_editor_subsystem(%s) failed: %s" % (name, exc))
        return None


class Assets(object):
    """EditorAssetSubsystem with EditorAssetLibrary as the fallback (same method names)."""

    def __init__(self):
        self.sub = editor_subsystem("EditorAssetSubsystem")
        self.lib = getattr(unreal, "EditorAssetLibrary", None)
        if self.sub is None and self.lib is None:
            raise RuntimeError("neither EditorAssetSubsystem nor EditorAssetLibrary exists; enable the Editor Scripting Utilities plugin")

    def _call(self, name, *args, **kwargs):
        for target in (self.sub, self.lib):
            if target is None:
                continue
            fn = getattr(target, name, None)
            if fn is None:
                continue
            return fn(*args, **kwargs)
        raise AttributeError("no asset function named " + name)

    def exists(self, path):
        try:
            return bool(self._call("does_asset_exist", path))
        except Exception:
            return False

    def directory_exists(self, path):
        try:
            return bool(self._call("does_directory_exist", path))
        except Exception:
            return False

    def make_directory(self, path):
        try:
            return bool(self._call("make_directory", path))
        except Exception as exc:
            log.warn("make_directory(%s): %s" % (path, exc))
            return False

    def load(self, path):
        try:
            return self._call("load_asset", path)
        except Exception as exc:
            log.warn("load_asset(%s): %s" % (path, exc))
            return None

    def list(self, path, recursive=True):
        try:
            return [str(p) for p in self._call("list_assets", path, recursive, False)]
        except Exception:
            try:
                return [str(p) for p in self._call("list_assets", path, recursive)]
            except Exception as exc:
                log.warn("list_assets(%s): %s" % (path, exc))
                return []

    def save(self, obj, only_if_dirty=False):
        if obj is None:
            return False
        try:
            return bool(self._call("save_loaded_asset", obj, only_if_dirty))
        except Exception as exc:
            log.warn("save_loaded_asset: %s" % exc)
            return False

    def save_directory(self, path, only_if_dirty=True, recursive=True):
        try:
            return bool(self._call("save_directory", path, only_if_dirty, recursive))
        except Exception as exc:
            log.warn("save_directory(%s): %s" % (path, exc))
            return False

    def rename(self, src, dst):
        try:
            return bool(self._call("rename_asset", src, dst))
        except Exception as exc:
            log.warn("rename_asset(%s -> %s): %s" % (src, dst, exc))
            return False

    def delete(self, path):
        try:
            return bool(self._call("delete_asset", path))
        except Exception as exc:
            log.warn("delete_asset(%s): %s" % (path, exc))
            return False

    def find_asset_data(self, path):
        try:
            return self._call("find_asset_data", path)
        except Exception:
            return None


_ASSETS = None


def assets():
    global _ASSETS
    if _ASSETS is None:
        _ASSETS = Assets()
    return _ASSETS


def actor_subsystem():
    """EditorActorSubsystem (5.8) or the deprecated EditorLevelLibrary (same spawn/list/destroy names)."""
    sub = editor_subsystem("EditorActorSubsystem")
    if sub is not None:
        return sub
    lib = getattr(unreal, "EditorLevelLibrary", None)
    if lib is None:
        raise RuntimeError("EditorActorSubsystem missing (and no EditorLevelLibrary fallback)")
    return lib


def level_subsystem():
    sub = editor_subsystem("LevelEditorSubsystem")
    if sub is not None:
        return sub
    lib = getattr(unreal, "EditorLevelLibrary", None)
    if lib is None:
        raise RuntimeError("LevelEditorSubsystem missing (and no EditorLevelLibrary fallback)")
    return lib


def editor_world():
    sub = editor_subsystem("UnrealEditorSubsystem")
    if sub is not None and hasattr(sub, "get_editor_world"):
        return sub.get_editor_world()
    lib = getattr(unreal, "EditorLevelLibrary", None)
    if lib is not None and hasattr(lib, "get_editor_world"):
        return lib.get_editor_world()
    return None


def wait_for_asset_registry():
    """The registry may still be scanning in a fresh editor; block until it is complete."""
    try:
        reg = unreal.AssetRegistryHelpers.get_asset_registry()
    except Exception as exc:
        log.warn("asset registry unavailable: %s" % exc)
        return None
    for name in ("wait_for_completion",):
        fn = getattr(reg, name, None)
        if fn is not None:
            try:
                fn()
                return reg
            except Exception as exc:
                log.warn("%s: %s" % (name, exc))
    try:
        reg.search_all_assets(True)
    except Exception:
        pass
    return reg


def asset_registry():
    try:
        return unreal.AssetRegistryHelpers.get_asset_registry()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Asset discovery
# ---------------------------------------------------------------------------


def asset_data_class_name(ad):
    """Class name of an AssetData across the 5.1+ (asset_class_path) and older (asset_class) layouts."""
    try:
        cp = ad.get_editor_property("asset_class_path")
        name = getattr(cp, "asset_name", None)
        if name is not None:
            return str(name)
    except Exception:
        pass
    try:
        cp = getattr(ad, "asset_class_path", None)
        if cp is not None:
            return str(getattr(cp, "asset_name", cp))
    except Exception:
        pass
    try:
        return str(ad.get_editor_property("asset_class"))
    except Exception:
        pass
    try:
        return str(getattr(ad, "asset_class", ""))
    except Exception:
        return ""


def asset_data_object_path(ad):
    for getter in ("get_object_path_string", "get_soft_object_path"):
        fn = getattr(ad, getter, None)
        if fn is not None:
            try:
                return str(fn())
            except Exception:
                pass
    for prop in ("object_path", "package_name"):
        try:
            val = ad.get_editor_property(prop)
            if val is not None:
                return str(val)
        except Exception:
            pass
    return ""


_ASSET_CACHE = {}


def clear_asset_cache():
    _ASSET_CACHE.clear()


def find_assets(folder, class_name, recursive=True, cached=False):
    """[(object_path, loaded_object), ...] for every asset of class_name under folder.

    Uses the asset registry (no loading of other asset types) and falls back to listing + loading.
    cached=True reuses the last answer for the same folder (for the per-row mesh lookups).
    """
    key = (folder, class_name, recursive)
    if cached and key in _ASSET_CACHE:
        return _ASSET_CACHE[key]
    found = _find_assets(folder, class_name, recursive)
    if cached:
        _ASSET_CACHE[key] = found
    return found


def _find_assets(folder, class_name, recursive):
    found = []
    reg = asset_registry()
    if reg is not None and hasattr(reg, "get_assets_by_path"):
        try:
            datas = list(reg.get_assets_by_path(folder, recursive))
        except Exception as exc:
            log.warn("get_assets_by_path(%s): %s" % (folder, exc))
            datas = None
        if datas is not None:
            for ad in datas:
                if asset_data_class_name(ad) != class_name:
                    continue
                path = asset_data_object_path(ad)
                obj = None
                try:
                    obj = ad.get_asset()
                except Exception:
                    obj = assets().load(path)
                if obj is not None:
                    found.append((path, obj))
            if found:
                return found
    # Fallback: list and load everything, keep the matching class.
    cls = getattr(unreal, class_name, None)
    for path in assets().list(folder, recursive):
        obj = assets().load(path)
        if obj is None:
            continue
        ok = False
        try:
            ok = (cls is not None and isinstance(obj, cls)) or obj.get_class().get_name() == class_name
        except Exception:
            ok = False
        if ok:
            found.append((path, obj))
    return found


def static_meshes_under(folder, cached=False):
    return find_assets(folder, "StaticMesh", cached=cached)


def object_name(obj):
    try:
        return str(obj.get_name())
    except Exception:
        return str(obj)


def mesh_tag(name):
    """'item__ca_200' -> ('item', 'ca_200'); None for an untagged mesh."""
    m = TAG_RE.match(name)
    if not m:
        return None
    return m.group(1), name[len(m.group(1)) + 2:]


def find_tagged_mesh(prefix, ident, folders=None):
    """Look for the mesh named '<prefix>__<ident with - as _>' under the campus folders."""
    wanted = "%s__%s" % (prefix, ident.replace("-", "_"))
    folders = folders or [paths.CAMPUS_PATH]
    for folder in folders:
        for path, mesh in static_meshes_under(folder, cached=True):
            if object_name(mesh) == wanted:
                return path, mesh
    return None, None


# ---------------------------------------------------------------------------
# Maths and bounds
# ---------------------------------------------------------------------------


def vec(x=0.0, y=0.0, z=0.0):
    return unreal.Vector(float(x), float(y), float(z))


def rot(pitch=0.0, yaw=0.0, roll=0.0):
    # Rotator positional order is roll, pitch, yaw: always pass keywords.
    return unreal.Rotator(pitch=float(pitch), yaw=float(yaw), roll=float(roll))


def forward_from_yaw(yaw_deg):
    r = math.radians(yaw_deg)
    return (math.cos(r), math.sin(r), 0.0)


def look_at(src, dst):
    """(pitch, yaw) in degrees so that +X of the rotator points from src to dst."""
    dx, dy, dz = dst[0] - src[0], dst[1] - src[1], dst[2] - src[2]
    horiz = math.hypot(dx, dy)
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, horiz)) if horiz > 1e-6 else (-90.0 if dz < 0 else 90.0)
    return pitch, yaw


def xyz(v):
    """A plain float tuple from an unreal.Vector, a dict {X,Y,Z} or a list."""
    if v is None:
        return None
    if isinstance(v, dict):
        return (float(v.get("X", 0.0)), float(v.get("Y", 0.0)), float(v.get("Z", 0.0)))
    if isinstance(v, (list, tuple)):
        return (float(v[0]), float(v[1]), float(v[2]))
    return (float(v.x), float(v.y), float(v.z))


def mesh_bounds(mesh):
    """((cx, cy, cz), (ex, ey, ez)) in cm, or None if the engine gives no numbers."""
    try:
        b = mesh.get_bounds()
        origin = xyz(b.origin)
        extent = xyz(b.box_extent)
        return origin, extent
    except Exception:
        pass
    try:
        box = mesh.get_bounding_box()
        mn, mx = xyz(box.min), xyz(box.max)
        centre = tuple((mn[i] + mx[i]) / 2.0 for i in range(3))
        extent = tuple((mx[i] - mn[i]) / 2.0 for i in range(3))
        return centre, extent
    except Exception:
        return None


def srgb_to_linear(c):
    c = max(0.0, min(1.0, c))
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def hex_rgb(hex_str):
    """'#ffe2b9' -> (r, g, b) in 0..1 sRGB."""
    s = hex_str.strip().lstrip("#")
    if len(s) != 6:
        return (1.0, 1.0, 1.0)
    return tuple(int(s[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


def set_props(obj, props, label=None):
    """set_editor_property for each (name, value); returns the list of names that failed."""
    failed = []
    for name, value in props.items():
        try:
            obj.set_editor_property(name, value)
        except Exception as exc:
            failed.append(name)
            log.warn("%s.%s could not be set: %s" % (label or object_name(obj), name, exc))
    return failed


def get_prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return getattr(obj, name, default)


def enum_value(enum_name, member, default=None):
    enum = getattr(unreal, enum_name, None)
    if enum is None:
        return default
    return getattr(enum, member, default)


# ---------------------------------------------------------------------------
# Actors
# ---------------------------------------------------------------------------


def all_actors():
    try:
        return list(actor_subsystem().get_all_level_actors())
    except Exception as exc:
        log.warn("get_all_level_actors: %s" % exc)
        return []


def actor_tags(actor):
    try:
        return [str(t) for t in get_prop(actor, "tags", []) or []]
    except Exception:
        return []


def actor_class_name(actor):
    try:
        return str(actor.get_class().get_name())
    except Exception:
        return ""


def actor_label(actor):
    try:
        return str(actor.get_actor_label())
    except Exception:
        return ""


def step_tag(step):
    return "WTA_" + step


def delete_setup_actors(step=None):
    """Destroy actors tagged WTA_Setup (and WTA_<step> when a step is given). Returns the count."""
    sub = actor_subsystem()
    want = step_tag(step) if step else None
    count = 0
    for actor in all_actors():
        tags = actor_tags(actor)
        if paths.SETUP_TAG not in tags:
            continue
        if want is not None and want not in tags:
            continue
        try:
            sub.destroy_actor(actor)
            count += 1
        except Exception as exc:
            log.warn("destroy_actor(%s): %s" % (actor_label(actor), exc))
    return count


def mark_actor(actor, step, label=None, folder=None):
    """Tag, label and folder a spawned actor so verify and re-runs can find it."""
    tags = [paths.SETUP_TAG, step_tag(step)]
    try:
        actor.set_editor_property("tags", tags)
    except Exception:
        try:
            actor.tags = tags
        except Exception as exc:
            log.warn("could not tag actor %s: %s" % (label, exc))
    if label:
        try:
            actor.set_actor_label(str(label))
        except Exception:
            pass
    if folder:
        try:
            actor.set_folder_path(str(folder))
        except Exception:
            pass
    return actor


def spawn_class(cls, location, rotation=None, step="setup", label=None, folder=None):
    sub = actor_subsystem()
    loc = vec(*location)
    r = rot(*(rotation or (0.0, 0.0, 0.0)))
    actor = sub.spawn_actor_from_class(cls, loc, r)
    if actor is None:
        raise RuntimeError("spawn_actor_from_class returned None for %s" % (label or cls))
    return mark_actor(actor, step, label, folder)


def spawn_object(obj, location, rotation=None, step="setup", label=None, folder=None):
    sub = actor_subsystem()
    loc = vec(*location)
    r = rot(*(rotation or (0.0, 0.0, 0.0)))
    actor = sub.spawn_actor_from_object(obj, loc, r)
    if actor is None:
        raise RuntimeError("spawn_actor_from_object returned None for %s" % (label or object_name(obj)))
    return mark_actor(actor, step, label, folder)


def find_actors(tag=None, class_name=None, label_prefix=None):
    out = []
    for actor in all_actors():
        if tag is not None and tag not in actor_tags(actor):
            continue
        if class_name is not None and actor_class_name(actor) != class_name:
            continue
        if label_prefix is not None and not actor_label(actor).startswith(label_prefix):
            continue
        out.append(actor)
    return out


def load_wta_class(name):
    """unreal.load_class for '/Script/WalkTheArchive.<name>' or None when the module is not built."""
    try:
        return unreal.load_class(None, paths.script_class(name))
    except Exception as exc:
        log.warn("load_class(%s): %s" % (name, exc))
        return None


def load_wta_struct(struct_name):
    try:
        return unreal.load_object(None, paths.script_struct(struct_name))
    except Exception as exc:
        log.warn("load_object(%s): %s" % (struct_name, exc))
        return None


# ---------------------------------------------------------------------------
# Level
# ---------------------------------------------------------------------------


def current_level_path():
    world = editor_world()
    if world is None:
        return ""
    for getter in ("get_path_name", "get_full_name", "get_name"):
        fn = getattr(world, getter, None)
        if fn is None:
            continue
        try:
            return str(fn())
        except Exception:
            continue
    return ""


def level_is_loaded(level_path=paths.LEVEL_PATH):
    current = current_level_path()
    return level_path in current or current.endswith("." + level_path.rsplit("/", 1)[-1])


def ensure_level_loaded(level_path=paths.LEVEL_PATH):
    """Load L_Campus if it is not the current level. Raises when it does not exist yet."""
    if level_is_loaded(level_path):
        return True
    if not assets().exists(level_path):
        raise RuntimeError("%s does not exist: run the build_level step first" % level_path)
    les = level_subsystem()
    ok = les.load_level(level_path)
    if ok is False:
        raise RuntimeError("load_level(%s) returned False" % level_path)
    return True


def save_level():
    les = level_subsystem()
    for name in ("save_current_level", "save_all_dirty_levels"):
        fn = getattr(les, name, None)
        if fn is None:
            continue
        try:
            res = fn()
            if res is not False:
                return True
        except Exception as exc:
            log.warn("%s: %s" % (name, exc))
    return False


def data_rows(file_name):
    """The row list from WalkTheArchive/Data/<file>.json."""
    return paths.read_json(os.path.join(paths.DATA_DIR, file_name))


def env_flag(name, default=False):
    val = os.environ.get(name, "")
    if val == "":
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def write_json(path, data):
    paths.ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, default=str)
