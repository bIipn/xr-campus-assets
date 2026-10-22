"""Headless probe: which static meshes sit around a world point in L_Campus, and what one actor is.

    run_py.ps1 -Script C:\\dev\\xr-campus-assets\\unreal\\Tools\\common\\probe_point.py -Pattern WTA_PROBE
    env WTA_PROBE_POINT="971,-2643,3" (cm)  WTA_PROBE_RADIUS=150  WTA_PROBE_ACTOR=StaticMeshActor_695

Prints WTA_PROBE lines: the named actor's mesh and bounds, then every static mesh actor whose bounds come within
the radius of the point, nearest first.
"""
import os

import unreal

point = [float(v) for v in os.environ.get("WTA_PROBE_POINT", "0,0,0").split(",")]
radius = float(os.environ.get("WTA_PROBE_RADIUS", "150"))
wanted = os.environ.get("WTA_PROBE_ACTOR", "")

world = unreal.EditorLevelLibrary.get_editor_world()
if world is None or not world.get_name().startswith("L_Campus"):
    unreal.EditorLevelLibrary.load_level("/Game/WTA/Maps/L_Campus")
    world = unreal.EditorLevelLibrary.get_editor_world()

p = unreal.Vector(*point)
rows = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    comp = actor.static_mesh_component
    mesh = comp.static_mesh if comp is not None else None
    origin, extent = actor.get_actor_bounds(False)
    lo = origin - extent
    hi = origin + extent
    dx = max(lo.x - p.x, 0.0, p.x - hi.x)
    dy = max(lo.y - p.y, 0.0, p.y - hi.y)
    dz = max(lo.z - p.z, 0.0, p.z - hi.z)
    d = (dx * dx + dy * dy + dz * dz) ** 0.5
    name = actor.get_name()
    if name == wanted:
        unreal.log("WTA_PROBE actor %s mesh=%s bounds=(%.0f,%.0f,%.0f)-(%.0f,%.0f,%.0f) collision=%s"
                   % (name, mesh.get_name() if mesh else None, lo.x, lo.y, lo.z, hi.x, hi.y, hi.z,
                      comp.get_collision_enabled() if comp is not None else None))
    if d <= radius:
        rows.append((d, name, mesh.get_name() if mesh else None, lo, hi))
rows.sort(key=lambda r: r[0])
for d, name, mesh, lo, hi in rows[:25]:
    unreal.log("WTA_PROBE near %.0f cm: %s mesh=%s bounds=(%.0f,%.0f,%.0f)-(%.0f,%.0f,%.0f)" % (d, name, mesh, lo.x, lo.y, lo.z, hi.x, hi.y, hi.z))
unreal.log("WTA_PROBE done %d within %.0f cm of (%.0f, %.0f, %.0f)" % (len(rows), radius, p.x, p.y, p.z))
