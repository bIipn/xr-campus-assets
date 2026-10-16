"""A permissive fake 'unreal' module for running the wta_setup pipeline without Unreal.

Any attribute that is not defined here becomes a Stub class on first access; any attribute of a Stub is
another callable Stub, so the setup code can call whatever API name it likes. A handful of APIs are
simulated with real behaviour so the steps can check their own results:
  * an in-memory asset registry (does_asset_exist, list_assets, rename, create_asset, import tasks),
  * glTF imports that create one StaticMesh per mesh in the GLB, with bounds from the accessor min/max,
  * DataTables that remember their row names after fill_data_table_from_json_string,
  * an editor world with spawn / list / destroy actors and a current level that saves a fake .umap.
Set WTA_MOCK_NO_CPP=1 to make load_class/load_object return None for /Script/WalkTheArchive paths.
"""
import json
import os
import struct
import sys

_singletons = {}
_assets = {}          # package path -> object
_actors = []
_level = {"path": None}


def _log(prefix, msg):
    sys.stderr.write("%s %s\n" % (prefix, msg))


def log(msg):
    _log("LogPython:", msg)


def log_warning(msg):
    _log("LogPython: Warning:", msg)


def log_error(msg):
    _log("LogPython: Error:", msg)


def _package_path(path):
    path = str(path)
    head, _sep, tail = path.rpartition("/")
    if "." in tail:
        tail = tail.split(".")[0]
    return head + "/" + tail if head else tail


# ---------------------------------------------------------------------------
# Stub machinery
# ---------------------------------------------------------------------------


class StubMeta(type):
    def __getattr__(cls, name):
        if name.startswith("__"):
            raise AttributeError(name)
        value = Stub(_name="%s.%s" % (cls.__name__, name))
        setattr(cls, name, value)
        return value

    def get_name(cls):
        return cls.__name__

    def get_path_name(cls):
        return getattr(cls, "_ue_path", cls.__name__)


class Stub(metaclass=StubMeta):
    def __init__(self, *args, **kwargs):
        self._name = kwargs.pop("_name", type(self).__name__)
        self._args = args
        self._props = dict(kwargs)
        self._path = None
        self._label = self._name
        self._folder = ""

    def __call__(self, *args, **kwargs):
        return Stub(_name=self._name + "()")

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "get_name":
            return lambda: self._name
        if name in self._props:
            return self._props[name]
        return Stub(_name="%s.%s" % (self._name, name))

    def __iter__(self):
        return iter([])

    def __len__(self):
        return 0

    def __bool__(self):
        return True

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def __repr__(self):
        return "<%s %s>" % (type(self).__name__, self._name)

    def __str__(self):
        return self._name

    def get_editor_property(self, name):
        if name in self._props:
            return self._props[name]
        return Stub(_name="%s.%s" % (self._name, name))

    def set_editor_property(self, name, value):
        self._props[name] = value

    def get_class(self):
        return type(self)

    def get_path_name(self):
        return (self._path + "." + self._name) if self._path else self._name

    def get_full_name(self):
        return "%s %s" % (type(self).__name__, self.get_path_name())

    # Actor-ish helpers (harmless on other objects)
    def set_actor_label(self, label):
        self._label = str(label)

    def get_actor_label(self):
        return self._label

    def set_folder_path(self, folder):
        self._folder = str(folder)

    def get_folder_path(self):
        return self._folder

    def set_actor_scale3d(self, scale):
        self._props["actor_scale3d"] = scale

    def get_actor_location(self):
        return self._props.get("_location", Vector())


def __getattr__(name):
    """Module-level fallback: unknown names become Stub subclasses named after them."""
    if name.startswith("__"):
        raise AttributeError(name)
    cls = type(name, (Stub,), {})
    globals()[name] = cls
    return cls


# ---------------------------------------------------------------------------
# Core value types
# ---------------------------------------------------------------------------


class Vector(object):
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x, self.y, self.z = float(x), float(y), float(z)

    def __repr__(self):
        return "Vector(%.1f, %.1f, %.1f)" % (self.x, self.y, self.z)


class Rotator(object):
    def __init__(self, roll=0.0, pitch=0.0, yaw=0.0):
        self.roll, self.pitch, self.yaw = float(roll), float(pitch), float(yaw)

    def __repr__(self):
        return "Rotator(pitch=%.1f, yaw=%.1f, roll=%.1f)" % (self.pitch, self.yaw, self.roll)


class LinearColor(object):
    def __init__(self, r=0.0, g=0.0, b=0.0, a=1.0):
        self.r, self.g, self.b, self.a = r, g, b, a


class Color(object):
    def __init__(self, r=0, g=0, b=0, a=255):
        self.r, self.g, self.b, self.a = r, g, b, a


class Name(str):
    pass


class Text(str):
    pass


class BoxSphereBounds(object):
    def __init__(self, origin, box_extent, sphere_radius=0.0):
        self.origin, self.box_extent, self.sphere_radius = origin, box_extent, sphere_radius


class Box(object):
    def __init__(self, mn, mx):
        self.min, self.max = mn, mx


class TopLevelAssetPath(object):
    def __init__(self, package_name, asset_name):
        self.package_name, self.asset_name = package_name, asset_name


class AssetData(Stub):
    def __init__(self, path, obj):
        Stub.__init__(self, _name=obj._name)
        self._obj = obj
        self._props["asset_class_path"] = TopLevelAssetPath("/Script/Engine", type(obj).__name__)
        self._props["package_name"] = path

    def get_asset(self):
        return self._obj

    def get_object_path_string(self):
        return self._obj.get_path_name()


# ---------------------------------------------------------------------------
# Asset classes with simulated behaviour
# ---------------------------------------------------------------------------


class StaticMesh(Stub):
    def __init__(self, *args, **kwargs):
        Stub.__init__(self, *args, **kwargs)
        self._bounds = ((0.0, 0.0, 0.0), (50.0, 50.0, 50.0))
        self._tris = 100
        self._props.setdefault("static_materials", [])

    def get_bounds(self):
        c, e = self._bounds
        return BoxSphereBounds(Vector(*c), Vector(*e), max(e))

    def get_bounding_box(self):
        c, e = self._bounds
        return Box(Vector(c[0] - e[0], c[1] - e[1], c[2] - e[2]), Vector(c[0] + e[0], c[1] + e[1], c[2] + e[2]))

    def get_num_triangles(self, lod=0):
        return self._tris


class Texture2D(Stub):
    pass


class DataTable(Stub):
    def __init__(self, *args, **kwargs):
        Stub.__init__(self, *args, **kwargs)
        self._rows = []

    def get_row_names(self):
        return list(self._rows)


class World(Stub):
    def get_path_name(self):
        if _level["path"]:
            return _level["path"] + "." + _level["path"].rsplit("/", 1)[-1]
        return "/Temp/Untitled.Untitled"

    def get_world_settings(self):
        key = "WorldSettings"
        if key not in _singletons:
            _singletons[key] = WorldSettings(_name="WorldSettings")
        return _singletons[key]


class WorldSettings(Stub):
    pass


class Actor(Stub):
    pass


class StaticMeshActor(Actor):
    pass


class AssetImportTask(Stub):
    def __init__(self, *args, **kwargs):
        Stub.__init__(self, *args, **kwargs)
        self._objects = []

    def get_objects(self):
        return list(self._objects)


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------


def _register(path, obj):
    path = _package_path(path)
    obj._path = path
    obj._name = path.rsplit("/", 1)[-1]
    _assets[path] = obj
    return obj


def _glb_meshes(glb_path):
    """[(name, (centre_cm, extent_cm), triangles)] from the GLB JSON chunk; axes glTF Y-up -> UE cm."""
    with open(glb_path, "rb") as fh:
        magic, _v, _l = struct.unpack("<III", fh.read(12))
        if magic != 0x46546C67:
            raise ValueError("not a GLB")
        clen, _ct = struct.unpack("<II", fh.read(8))
        doc = json.loads(fh.read(clen).decode("utf-8"))
    acc = doc.get("accessors", [])
    out = []
    for mesh in doc.get("meshes", []):
        mins, maxs, tris = None, None, 0
        for prim in mesh.get("primitives", []):
            pa = prim.get("attributes", {}).get("POSITION")
            if pa is not None and pa < len(acc) and "min" in acc[pa] and "max" in acc[pa]:
                mn, mx = acc[pa]["min"], acc[pa]["max"]
                mins = mn if mins is None else [min(a, b) for a, b in zip(mins, mn)]
                maxs = mx if maxs is None else [max(a, b) for a, b in zip(maxs, mx)]
            idx = prim.get("indices")
            if idx is not None and idx < len(acc):
                tris += int(acc[idx].get("count", 0)) // 3
        if mins is None:
            bounds = ((0.0, 0.0, 0.0), (50.0, 50.0, 50.0))
        else:
            ue_min = (100.0 * mins[0], 100.0 * mins[2], 100.0 * mins[1])
            ue_max = (100.0 * maxs[0], 100.0 * maxs[2], 100.0 * maxs[1])
            centre = tuple((ue_min[i] + ue_max[i]) / 2.0 for i in range(3))
            extent = tuple((ue_max[i] - ue_min[i]) / 2.0 for i in range(3))
            bounds = (centre, extent)
        out.append((mesh.get("name", "Mesh"), bounds, tris))
    return out


class _AssetTools(object):
    def import_asset_tasks(self, tasks):
        for task in tasks:
            src = str(task._props.get("filename", ""))
            dest = str(task._props.get("destination_path", "/Game"))
            base = os.path.splitext(os.path.basename(src))[0]
            task._objects = []
            if src.lower().endswith(".glb"):
                try:
                    meshes = _glb_meshes(src)
                except Exception as exc:
                    log_warning("mock glb parse failed for %s: %s" % (src, exc))
                    meshes = [(base, ((0.0, 0.0, 0.0), (50.0, 50.0, 50.0)), 100)]
                for name, bounds, tris in meshes:
                    mesh = StaticMesh(_name=name)
                    mesh._bounds = bounds
                    mesh._tris = tris
                    _register(dest + "/" + name, mesh)
                    task._objects.append(mesh)
            elif src.lower().endswith((".png", ".jpg", ".tga", ".exr")):
                tex = Texture2D(_name=base)
                _register(dest + "/" + base, tex)   # Interchange ignores destination_name
                task._objects.append(tex)
            else:
                obj = Stub(_name=base)
                _register(dest + "/" + base, obj)
                task._objects.append(obj)

    def create_asset(self, name, folder, cls, factory):
        obj = cls(_name=name)
        if isinstance(obj, DataTable):
            obj._props["row_struct"] = factory._props.get("struct")
        return _register(folder + "/" + name, obj)


class AssetToolsHelpers(Stub):
    @staticmethod
    def get_asset_tools():
        return _singletons.setdefault("AssetTools", _AssetTools())


class _AssetRegistry(object):
    def wait_for_completion(self):
        return None

    def is_loading_assets(self):
        return False

    def search_all_assets(self, synchronous=True):
        return None

    def get_assets_by_path(self, path, recursive=True, include_only_on_disk=False):
        prefix = str(path).rstrip("/") + "/"
        out = []
        for key, obj in sorted(_assets.items()):
            if not key.startswith(prefix):
                continue
            if not recursive and "/" in key[len(prefix):]:
                continue
            out.append(AssetData(key, obj))
        return out


class AssetRegistryHelpers(Stub):
    @staticmethod
    def get_asset_registry():
        return _singletons.setdefault("AssetRegistry", _AssetRegistry())


class EditorAssetSubsystem(Stub):
    def does_asset_exist(self, path):
        return _package_path(path) in _assets

    def does_directory_exist(self, path):
        prefix = str(path).rstrip("/") + "/"
        return any(k.startswith(prefix) for k in _assets)

    def make_directory(self, path):
        return True

    def load_asset(self, path):
        return _assets.get(_package_path(path))

    def list_assets(self, path, recursive=True, include_folder=False):
        prefix = str(path).rstrip("/") + "/"
        return [k + "." + k.rsplit("/", 1)[-1] for k in sorted(_assets) if k.startswith(prefix)]

    def save_loaded_asset(self, obj, only_if_is_dirty=False):
        return True

    def save_loaded_assets(self, objs, only_if_is_dirty=False):
        return True

    def save_directory(self, path, only_if_is_dirty=True, recursive=True):
        return True

    def save_asset(self, path, only_if_is_dirty=True):
        return True

    def rename_asset(self, src, dst):
        src, dst = _package_path(src), _package_path(dst)
        obj = _assets.pop(src, None)
        if obj is None:
            return False
        _register(dst, obj)
        return True

    def delete_asset(self, path):
        return _assets.pop(_package_path(path), None) is not None

    def find_asset_data(self, path):
        obj = _assets.get(_package_path(path))
        return AssetData(_package_path(path), obj) if obj is not None else None


class EditorAssetLibrary(EditorAssetSubsystem):
    """The deprecated static library: same methods, usable without an instance."""

    _inst = None

    def __new__(cls, *args, **kwargs):
        return EditorAssetSubsystem.__new__(cls)


for _n in ("does_asset_exist", "does_directory_exist", "make_directory", "load_asset", "list_assets",
           "save_loaded_asset", "save_loaded_assets", "save_directory", "save_asset", "rename_asset",
           "delete_asset", "find_asset_data"):
    setattr(EditorAssetLibrary, _n, staticmethod(getattr(EditorAssetSubsystem(), _n)))


class EditorActorSubsystem(Stub):
    def spawn_actor_from_class(self, cls, location, rotation=None, transient=False):
        actor = cls(_name=cls.__name__)
        actor._props["_location"] = location
        actor._props["_rotation"] = rotation
        _actors.append(actor)
        return actor

    def spawn_actor_from_object(self, obj, location, rotation=None, transient=False):
        actor = StaticMeshActor(_name="SMA_" + getattr(obj, "_name", "mesh"))
        actor._props["_location"] = location
        actor._props["_mesh"] = obj
        _actors.append(actor)
        return actor

    def get_all_level_actors(self):
        return list(_actors)

    def destroy_actor(self, actor):
        if actor in _actors:
            _actors.remove(actor)
            return True
        return False


class EditorLevelLibrary(EditorActorSubsystem):
    pass


class LevelEditorSubsystem(Stub):
    def new_level(self, path, is_partitioned_world=False):
        _actors.clear()
        world = _register(path, World(_name=path.rsplit("/", 1)[-1]))
        _level["path"] = _package_path(path)
        self._write_umap()
        return True

    def load_level(self, path):
        if _package_path(path) not in _assets:
            return False
        _level["path"] = _package_path(path)
        return True

    def save_current_level(self):
        self._write_umap()
        return True

    def save_all_dirty_levels(self):
        self._write_umap()
        return True

    def _write_umap(self):
        if not _level["path"]:
            return
        try:
            from wta_setup import paths as _paths
            umap = _paths.LEVEL_UMAP
        except Exception:
            return
        d = os.path.dirname(umap)
        if not os.path.isdir(d):
            os.makedirs(d)
        with open(umap, "wb") as fh:
            fh.write(b"MOCK UMAP " + _level["path"].encode("utf-8"))


class UnrealEditorSubsystem(Stub):
    def get_editor_world(self):
        return _singletons.setdefault("World", World(_name="World"))


class DataTableFunctionLibrary(Stub):
    @staticmethod
    def fill_data_table_from_json_string(dt, text, import_row_struct=None):
        rows = json.loads(text)
        dt._rows = [str(r.get("Name", "")) for r in rows]
        return True

    @staticmethod
    def get_data_table_row_names(dt):
        return list(getattr(dt, "_rows", []))


class SystemLibrary(Stub):
    @staticmethod
    def get_engine_version():
        return "5.8.0-mock"

    @staticmethod
    def get_console_variable_string_value(name):
        return ""

    @staticmethod
    def execute_console_command(world, command):
        return None


class GameplayStatics(Stub):
    @staticmethod
    def get_platform_name():
        return "Mock"


# ---------------------------------------------------------------------------
# Module functions
# ---------------------------------------------------------------------------


def get_editor_subsystem(cls):
    key = cls.__name__
    if key not in _singletons:
        _singletons[key] = cls(_name=key)
    return _singletons[key]


def get_engine_subsystem(cls):
    return get_editor_subsystem(cls)


def _cpp_missing(path):
    return os.environ.get("WTA_MOCK_NO_CPP", "") in ("1", "true") and str(path).startswith("/Script/WalkTheArchive")


def load_class(outer, path):
    if _cpp_missing(path):
        return None
    name = str(path).rsplit(".", 1)[-1]
    cls = globals().get(name)
    if cls is None or not isinstance(cls, type):
        cls = type(name, (Actor,), {})
        globals()[name] = cls
    cls._ue_path = str(path)
    return cls


def load_object(outer, path):
    if _cpp_missing(path):
        return None
    pkg = _package_path(path)
    if pkg in _assets:
        return _assets[pkg]
    return Stub(_name=str(path).rsplit(".", 1)[-1])


def load_asset(path):
    return _assets.get(_package_path(path))


def find_object(outer, path):
    return load_object(outer, path)


def _reset():
    """Test helper: forget every asset and actor."""
    _assets.clear()
    _actors.clear()
    _level["path"] = None
    _singletons.clear()
