"""Step 1: probe the installed engine.

Reports the engine and Python versions, which unreal classes exist (the list from
docs/reference/automation.md section 3.0 plus everything the later steps use), and whether the
WalkTheArchive C++ module is loaded. The step fails only when the C++ classes or row structs cannot be
loaded, which means build_editor was not run.
"""
import os
import platform
import sys

import unreal

from . import log
from . import paths
from . import util

STEP = "probe"

ENGINE_CLASSES = [
    # automation.md section 3.0
    "InterchangeManager", "ImportAssetParameters", "InterchangeGenericAssetsPipeline", "AssetImportTask",
    "LevelEditorSubsystem", "EditorActorSubsystem", "EditorAssetSubsystem", "SubobjectDataSubsystem",
    "DataTableFunctionLibrary", "DataTableFactory", "CSVImportFactory", "MaterialEditingLibrary",
    "MaterialInstanceConstantFactoryNew", "PostProcessVolume", "LevelInstance", "PackedLevelActor",
    "EditorLevelUtils", "WorldPartitionBlueprintLibrary", "BlueprintGraphEditor", "ModelContextProtocolSettings",
    # used by the later steps
    "UnrealEditorSubsystem", "StaticMeshEditorSubsystem", "EditorAssetLibrary", "EditorLevelLibrary",
    "AssetRegistryHelpers", "AssetToolsHelpers", "ScopedEditorTransaction", "AutomationLibrary",
    "StaticMeshActor", "PlayerStart", "DirectionalLight", "SkyLight", "SkyAtmosphere", "VolumetricCloud",
    "ExponentialHeightFog", "PointLight", "SpotLight", "RectLight", "NavMeshBoundsVolume", "NavigationSystemV1",
    "MeshNaniteSettings", "CollisionTraceFlag", "LightUnits", "AutoExposureMethod",
    "DynamicGlobalIlluminationMethod", "ReflectionMethod", "TextureGroup", "BlendMode", "ComponentMobility",
    "DataTable", "Texture2D", "StaticMesh", "WorldSettings", "GameplayStatics", "SystemLibrary",
]

WTA_CLASSES = [
    "WTAGameMode", "WTAPlayerController", "WTACharacter", "WTASettings",
    "WTAExhibitActor", "WTABookActor", "WTAStationActor", "WTARideActor", "WTATokenActor",
    "WTAStaffNPC", "WTARoomVolume", "WTAWaxStageActor",
]


def _engine_version():
    try:
        return str(unreal.SystemLibrary.get_engine_version())
    except Exception as exc:
        return "unknown (%s)" % exc


def _rhi_name():
    # No stable Python API for the RHI name; try the common cvars and give up quietly.
    for cvar in ("r.RHIName", "r.GraphicsRHI"):
        try:
            val = unreal.SystemLibrary.get_console_variable_string_value(cvar)
            if val:
                return str(val)
        except Exception:
            continue
    try:
        return str(unreal.GameplayStatics.get_platform_name())
    except Exception:
        return "unknown"


def _struct_names():
    try:
        structs = paths.read_json(paths.STRUCTS_JSON).get("structs", {})
        return sorted(structs.keys())
    except Exception as exc:
        log.warn("structs.json unreadable: %s" % exc)
        return ["FWTAExhibitRow", "FWTARoomRow", "FWTAView"]


def run():
    has = {}
    for name in ENGINE_CLASSES:
        has[name] = util.has(name)

    wta_classes = {}
    for name in WTA_CLASSES:
        wta_classes[name] = util.load_wta_class(name) is not None

    wta_structs = {}
    for name in _struct_names():
        wta_structs[name] = util.load_wta_struct(name) is not None

    new_level_doc = ""
    try:
        new_level_doc = str(unreal.LevelEditorSubsystem.new_level.__doc__ or "")
    except Exception:
        pass

    # The module counts as loaded when its core classes resolve; single missing names are reported as
    # warnings and the later steps fail per row instead.
    missing_classes = [k for k, v in wta_classes.items() if not v]
    missing_structs = [k for k, v in wta_structs.items() if not v]
    cpp_loaded = wta_classes.get("WTAGameMode", False) or wta_classes.get("WTAExhibitActor", False)
    if cpp_loaded and (missing_classes or missing_structs):
        log.warn("C++ module loaded but these names are missing: %s %s" % (missing_classes, missing_structs))

    data = {
        "engine": _engine_version(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "rhi": _rhi_name(),
        "project": paths.UPROJECT,
        "project_exists": os.path.isfile(paths.UPROJECT),
        "mesh_dir_exists": os.path.isdir(paths.MESH_DIR),
        "has": has,
        "missing_engine_classes": sorted(k for k, v in has.items() if not v),
        "wta_classes": wta_classes,
        "wta_structs": wta_structs,
        "new_level_accepts_partition_flag": "partitioned" in new_level_doc.lower(),
        "cpp_module_loaded": cpp_loaded,
        "missing_wta_classes": missing_classes,
        "missing_wta_structs": missing_structs,
    }
    try:
        util.write_json(os.path.join(paths.SAVED_WTA_DIR, "probe.json"), data)
    except Exception as exc:
        log.warn("could not write probe.json: %s" % exc)

    if not cpp_loaded:
        data["error"] = ("WalkTheArchive C++ module not loaded (%s does not resolve); run build_editor first"
                         % paths.script_class("WTAGameMode"))
    data["ok"] = cpp_loaded
    return data
