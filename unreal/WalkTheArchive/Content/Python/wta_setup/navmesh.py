"""Step 8: one NavMeshBoundsVolume over the walkable campus (rooms union plus the yard).

The volume spawned from the class comes with the default 200 cm cube brush, so the actor scale makes it
the right size. The editor rebuilds navigation automatically when a bounds volume changes; the step also
asks for a rebuild through the console when that command exists. The project ini sets runtime
generation to Dynamic (project_settings step), so walking works even if the editor build was cut short.
"""
import unreal

from . import log
from . import paths
from . import util

STEP = "navmesh"
BRUSH_SIZE = 200.0
MARGIN = 300.0


def walkable_bounds():
    """((minx, miny, minz), (maxx, maxy, maxz)) in cm from layout nav bounds, else the rooms union."""
    try:
        nav = paths.read_json(paths.LAYOUT_JSON)["global"]["player"]["nav_bounds_m"]
        return ((100.0 * nav["x0"], 100.0 * nav["z0"], -100.0), (100.0 * nav["x1"], 100.0 * nav["z1"], 800.0))
    except Exception:
        pass
    mins, maxs = [1e9, 1e9, 1e9], [-1e9, -1e9, -1e9]
    for row in util.data_rows("Rooms.json"):
        mn, mx = util.xyz(row["BoundsMin"]), util.xyz(row["BoundsMax"])
        for i in range(3):
            mins[i] = min(mins[i], mn[i])
            maxs[i] = max(maxs[i], mx[i])
    mins[2] -= 100.0
    maxs[2] = max(maxs[2], mins[2] + 800.0)
    return tuple(mins), tuple(maxs)


def request_build(report):
    nav = getattr(unreal, "NavigationSystemV1", None)
    world = util.editor_world()
    if nav is not None:
        for name in ("navigation_build", "build", "rebuild_all"):
            fn = getattr(nav, name, None)
            if fn is None:
                continue
            try:
                fn(world) if world is not None else fn()
                report["nav_build"] = "NavigationSystemV1." + name
                return
            except Exception:
                continue
    if world is not None:
        try:
            unreal.SystemLibrary.execute_console_command(world, "RebuildNavigation")
            report["nav_build"] = "console RebuildNavigation"
            return
        except Exception as exc:
            log.warn("RebuildNavigation console command failed: %s" % exc)
    report["nav_build"] = "runtime (Dynamic generation)"


def run():
    util.wait_for_asset_registry()
    util.ensure_level_loaded()
    report = {"removed_previous": util.delete_setup_actors(STEP)}
    mn, mx = walkable_bounds()
    size = [(mx[i] - mn[i]) + 2.0 * MARGIN for i in range(3)]
    centre = [(mx[i] + mn[i]) / 2.0 for i in range(3)]
    scale = [s / BRUSH_SIZE for s in size]
    actor = util.spawn_class(unreal.NavMeshBoundsVolume, centre, None, step=STEP, label="NavBounds_Campus", folder="Nav")
    try:
        actor.set_actor_scale3d(unreal.Vector(scale[0], scale[1], scale[2]))
    except Exception as exc:
        util.set_props(actor, {"actor_scale3d": unreal.Vector(scale[0], scale[1], scale[2])}, label="NavBounds")
        log.warn("set_actor_scale3d failed, tried the property instead: %s" % exc)
    report["bounds_min"] = list(mn)
    report["bounds_max"] = list(mx)
    report["centre"] = centre
    report["scale"] = scale
    request_build(report)
    report["note"] = ("the editor builds the navmesh on later ticks; with RuntimeGeneration=Static open "
                      "L_Campus in the editor once, let Build Paths finish and save")
    report["saved"] = util.save_level()
    report["ok"] = bool(report["saved"])
    if not report["ok"]:
        report["error"] = "level save reported failure"
    return report
