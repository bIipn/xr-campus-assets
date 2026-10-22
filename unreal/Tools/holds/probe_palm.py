"""Dump the MetaHuman body's hands in the stage's palm frame (World/WTAWaxStageActor.cpp PalmFrame) as JSON:
for each finger joint, its position and its own frame's axes in palm coordinates (+X fingers, +Y palm normal,
+Z across; cm). design_holds.py designs the Wax Hall holds from it. Run headless in the editor:

    UnrealEditor-Cmd.exe <project>.uproject -ExecutePythonScript=<repo>/unreal/Tools/holds/probe_palm.py -unattended -nopause -nosplash

(or with -abslog; the output goes next to this file as palm.json). The first body under
/Game/WTA/Characters/wax-2016-man is used; every MetaHuman body shares the skeleton."""
import json
import math
import os
import unreal

reg = unreal.AssetRegistryHelpers.get_asset_registry()
body = None
for ad in reg.get_assets_by_path("/Game/WTA/Characters/wax-2016-man", recursive=True):
    if str(ad.asset_class_path.asset_name) == "SkeletalMesh" and "body" in str(ad.asset_name).lower():
        body = ad.get_asset()
        break

actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0))
comp = actor.skeletal_mesh_component
comp.set_skeletal_mesh_asset(body)
names = [str(comp.get_bone_name(i)) for i in range(comp.get_num_bones())]


def V(x, y, z):
    return unreal.Vector(x, y, z)

def sub(a, b):
    return V(a.x - b.x, a.y - b.y, a.z - b.z)

def add(a, b):
    return V(a.x + b.x, a.y + b.y, a.z + b.z)

def mul(a, s):
    return V(a.x * s, a.y * s, a.z * s)

def dot(a, b):
    return a.x * b.x + a.y * b.y + a.z * b.z

def cross(a, b):
    return V(a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x)

def unit(a):
    n = math.sqrt(dot(a, a))
    return V(a.x / n, a.y / n, a.z / n) if n > 1e-9 else V(0, 0, 0)

def frame(bone):
    return comp.get_socket_transform(bone, unreal.RelativeTransformSpace.RTS_COMPONENT)


out = {"body": str(body.get_path_name()), "hands": {}}
for side in ("r", "l"):
    hand = "hand_%s" % side
    W0 = frame(hand).translation
    mid = frame("middle_01_%s" % side).translation
    idx = frame("index_01_%s" % side).translation
    pky = frame("pinky_01_%s" % side).translation
    th3 = frame("thumb_03_%s" % side).translation
    # the same frame PalmFrame builds
    F = unit(sub(mid, W0))
    across = unit(sub(idx, pky))
    N = unit(cross(F, across))
    if dot(sub(th3, W0), N) < 0:
        N = mul(N, -1)
    N = unit(sub(N, mul(F, dot(N, F))))
    Z = cross(F, N)
    O = add(W0, mul(F, 7.0))
    def palm_p(p):
        r = sub(p, O)
        return [round(dot(r, F), 3), round(dot(r, N), 3), round(dot(r, Z), 3)]
    def palm_d(d):
        return [round(dot(d, F), 4), round(dot(d, N), 4), round(dot(d, Z), 4)]
    H = frame(hand)
    hd = {"wrist": palm_p(W0), "wrist_axes": [palm_d(H.transform_direction(V(1, 0, 0))), palm_d(H.transform_direction(V(0, 1, 0))), palm_d(H.transform_direction(V(0, 0, 1)))], "fingers": {}}
    for finger in ("thumb", "index", "middle", "ring", "pinky"):
        joints = []
        for j in (1, 2, 3):
            bone = "%s_0%d_%s" % (finger, j, side)
            if bone not in names:
                break
            T = frame(bone)
            joints.append({
                "bone": bone,
                "p": palm_p(T.translation),
                "axes": [palm_d(T.transform_direction(V(1, 0, 0))), palm_d(T.transform_direction(V(0, 1, 0))), palm_d(T.transform_direction(V(0, 0, 1)))],
            })
        hd["fingers"][finger] = joints
    out["hands"][side] = hd

actor.destroy_actor()
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "palm.json")
with open(path, "w") as f:
    json.dump(out, f, indent=1)
unreal.log_warning("WTA_PROBE wrote %s" % path)
