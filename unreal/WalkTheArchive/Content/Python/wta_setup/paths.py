"""Repo, project and content paths. Everything derives from this file's location; nothing is hard-coded.

Layout (contract section 1 and 3):
  <repo>/unreal/WalkTheArchive/Content/Python/wta_setup/paths.py   <- this file
  <repo>/unreal/WalkTheArchive/                                     <- PROJECT_DIR
  <repo>/unreal/Pipeline/out/ue/*.glb                               <- meshes
  <repo>/unreal/Pipeline/out/campus/art/*.png                       <- exhibit art
  <repo>/unreal/WalkTheArchive/Data/*.json                          <- DataTable rows
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))

_DERIVED_PROJECT_DIR = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))   # unreal/WalkTheArchive
UNREAL_DIR = os.path.abspath(os.path.join(_DERIVED_PROJECT_DIR, ".."))           # unreal
REPO_ROOT = os.path.abspath(os.path.join(UNREAL_DIR, ".."))                      # repo root

# WTA_PROJECT_DIR redirects the project (Config, Content, Saved, Data) to another folder; the tests use it
# so a run never touches the real project. The pipeline inputs always come from the repo this file is in.
PROJECT_DIR = os.path.abspath(os.environ.get("WTA_PROJECT_DIR") or _DERIVED_PROJECT_DIR)

PROJECT_NAME = "WalkTheArchive"
UPROJECT = os.path.join(PROJECT_DIR, PROJECT_NAME + ".uproject")
CONFIG_DIR = os.path.join(PROJECT_DIR, "Config")
DEFAULT_ENGINE_INI = os.path.join(CONFIG_DIR, "DefaultEngine.ini")
DEFAULT_GAME_INI = os.path.join(CONFIG_DIR, "DefaultGame.ini")
SAVED_DIR = os.path.join(PROJECT_DIR, "Saved")
SAVED_WTA_DIR = os.path.join(SAVED_DIR, "WTA")
SHOTS_DIR = os.path.join(SAVED_DIR, "WTA_Shots")
CONTENT_DIR = os.path.join(PROJECT_DIR, "Content")

DATA_DIR = os.path.join(PROJECT_DIR, "Data")                               # DataTable row JSON
PIPELINE_DIR = os.path.join(UNREAL_DIR, "Pipeline")
OUT_DIR = os.path.join(PIPELINE_DIR, "out")
MESH_DIR = os.path.join(OUT_DIR, "ue")                                       # <Asset>.glb + manifest.json
MESH_MANIFEST = os.path.join(MESH_DIR, "manifest.json")
ART_DIR = os.path.join(OUT_DIR, "campus", "art")                             # <id>.png
CAMPUS_LIGHTS_JSON = os.path.join(OUT_DIR, "campus", "lights.json")
READING_ROOM_LIGHTS_JSON = os.path.join(OUT_DIR, "reading_room", "lights.json")
LAYOUT_JSON = os.path.join(PIPELINE_DIR, "layout", "layout.json")
STRUCTS_JSON = os.path.join(UNREAL_DIR, "contract", "structs.json")

# Content paths (contract section 3). Created by the setup, never committed.
CONTENT_ROOT = "/Game/WTA"
CAMPUS_PATH = CONTENT_ROOT + "/Campus"
ART_PATH = CONTENT_ROOT + "/Art"
DATA_PATH = CONTENT_ROOT + "/Data"
MAPS_PATH = CONTENT_ROOT + "/Maps"
MATERIALS_PATH = CONTENT_ROOT + "/Materials"
LEVEL_NAME = "L_Campus"
LEVEL_PATH = MAPS_PATH + "/" + LEVEL_NAME                                    # /Game/WTA/Maps/L_Campus
LEVEL_UMAP = os.path.join(CONTENT_DIR, "WTA", "Maps", LEVEL_NAME + ".umap")

# Engine script paths for the C++ module (contract section 1).
SCRIPT_MODULE = "/Script/WalkTheArchive"
GAME_MODE_PATH = SCRIPT_MODULE + ".WTAGameMode"

# Fixed asset list from the contract; manifest.json is preferred when present.
DEFAULT_ASSETS = ["Museum", "WaxIntro", "WaxHall", "LibraryShell", "School", "Outside", "Yard", "OceanDive", "ReadingRoom"]

# Tag every actor the setup spawns so a re-run can delete and respawn it.
SETUP_TAG = "WTA_Setup"


def script_class(name):
    """'/Script/WalkTheArchive.WTAExhibitActor' for a C++ class name without its A/U prefix."""
    return SCRIPT_MODULE + "." + name


def script_struct(struct_name):
    """'/Script/WalkTheArchive.WTAExhibitRow' for an F-prefixed struct name."""
    if struct_name.startswith("F"):
        struct_name = struct_name[1:]
    return SCRIPT_MODULE + "." + struct_name


def campus_asset_path(asset):
    return CAMPUS_PATH + "/" + asset


def art_asset_name(art_id):
    """T_Art_<id> with '-' replaced by '_' (contract section 3)."""
    return "T_Art_" + art_id.replace("-", "_")


def art_asset_path(art_id):
    return ART_PATH + "/" + art_asset_name(art_id)


def table_asset_path(table):
    return DATA_PATH + "/" + table


def mesh_assets():
    """[(asset_name, glb_path), ...] from manifest.json, falling back to the contract list."""
    names = list(DEFAULT_ASSETS)
    try:
        with open(MESH_MANIFEST, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        listed = list(manifest.get("assets", {}).keys())
        if listed:
            names = listed
    except (OSError, ValueError):
        pass
    return [(n, os.path.join(MESH_DIR, n + ".glb")) for n in names]


def read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)
    return path
