"""The Wax Hall's hand props as real objects: a VR headset, a tablet, a phone, an open book, a clipboard and a
cardboard box, one tagged mesh each (prop__<kind>, kept whole by prepare_for_unreal), for the reenactors to hold (Unreal rides them on the hand bones and curls the
fingers round them; World/WTAWaxStageActor.cpp).

Each prop stands in the frame the stage puts in a hand, in Unreal axes: +X runs along the fingers, +Y is the
palm's normal (out of the palm), +Z = X x Y across the palm. The origin is where the palm meets the prop. The
headset and the box are also worn and carried in the head's and the chest's squared frames (+X forward,
+Z up), so those two are modelled for that: the headset's visor looks along +X with the strap behind, the box
is a plain box about its centre.

Blender axes here: x = Unreal X, y = -Unreal Y (the palm normal points along -y), z = Unreal Z (the glTF export is
y-up and prepare_for_unreal maps glTF (x, y, z) to Unreal (X = x, Y = z, Z = y)).

    python3 bl/props.py   ->  unreal/Pipeline/out/props/HandProps.glb  (then prepare_for_unreal.py -- HandProps)
"""
import math
import os
import sys

import bpy
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import library as L                                              # noqa: E402
from library import material, select_only                        # noqa: E402

OUT = os.path.join(L.SP, 'unreal', 'Pipeline', 'out', 'props')


def mats():
    material('plastic', color=(0.055, 0.055, 0.06, 1), roughness=0.42)
    material('plastic_light', color=(0.82, 0.82, 0.80, 1), roughness=0.5)
    material('screen_e', color=(0.02, 0.02, 0.03, 1), emission=(0.62, 0.74, 0.92, 1), emission_strength=1.6, roughness=0.08)
    # the lit screens: the XR Libraries app mock (bl/screens.py), portrait, the top away from the hand
    material('screen_tablet_e', col='screen_tablet', emission=True, emission_strength=1.3, roughness=0.08, uvmap='UVMap')
    material('screen_phone_e', col='screen_phone', emission=True, emission_strength=1.3, roughness=0.08, uvmap='UVMap')
    material('glass_dark', color=(0.02, 0.02, 0.025, 1), roughness=0.06)
    material('paper', color=(0.93, 0.92, 0.88, 1), roughness=0.9)
    material('page', color=(0.96, 0.95, 0.90, 1), roughness=0.92)
    material('board', color=(0.42, 0.30, 0.18, 1), roughness=0.82)
    material('cover', color=(0.42, 0.07, 0.07, 1), roughness=0.55)
    material('metal', color=(0.72, 0.72, 0.74, 1), roughness=0.3, metallic=1.0)
    material('cardboard', color=(0.60, 0.45, 0.28, 1), roughness=0.92)
    material('tape', color=(0.74, 0.58, 0.33, 1), roughness=0.45)
    material('strap', color=(0.10, 0.10, 0.10, 1), roughness=0.9)
    material('foam', color=(0.04, 0.04, 0.04, 1), roughness=0.97)


PARTS = []


def box(name, cx, cy, cz, sx, sy, sz, mat, bevel=0.0, segs=3, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(cx, cy, cz), rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(scale=True)
    if bevel > 0:
        m = o.modifiers.new('bevel', 'BEVEL'); m.width = bevel; m.segments = segs; m.limit_method = 'NONE'
    o.data.materials.append(L.MATS[mat])
    PARTS.append(o)
    return o


def screen(name, cx, cy, cz, sx, sz, mat):
    """A lit screen: one quad at y = cy facing -y (out of the palm), sx along x and sz across, mapped so the
    texture's top is toward +x (away from the hand) and its right toward -z - portrait as the thing is held."""
    import bmesh
    bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')          # the cubes' own layer name, so it is UV0 after the join
    hx, hz = sx / 2, sz / 2
    corners = [((cx - hx, cy, cz + hz), (0, 0)), ((cx - hx, cy, cz - hz), (1, 0)), ((cx + hx, cy, cz - hz), (1, 1)), ((cx + hx, cy, cz + hz), (0, 1))]
    vs = [bm.verts.new(c) for c, _ in corners]
    f = bm.faces.new(vs)
    for l, (_, t) in zip(f.loops, corners): l[uv].uv = t
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(L.MATS[mat])
    PARTS.append(o)
    return o


def cyl(name, cx, cy, cz, r, depth, mat, axis='z', verts=32, rot_extra=(0, 0, 0)):
    rot = {'z': (0, 0, 0), 'x': (0, math.pi / 2, 0), 'y': (math.pi / 2, 0, 0)}[axis]
    rot = tuple(a + b for a, b in zip(rot, rot_extra))
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=(cx, cy, cz), rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(L.MATS[mat])
    PARTS.append(o)
    return o


def torus(name, cx, cy, cz, major, minor, mat, rot=(0, 0, 0), scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=40, minor_segments=10,
                                     location=(cx, cy, cz), rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(L.MATS[mat])
    PARTS.append(o)
    return o


def finish(name):
    """Join the parts made since the last finish into one object called name, shaded smooth where bevelled."""
    global PARTS
    for o in PARTS:
        select_only([o])
        for m in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=m.name)
    select_only(PARTS)
    bpy.ops.object.join()
    ob = bpy.context.active_object
    ob.name = name; ob.data.name = name
    ob.location = (0, 0, 0)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    PARTS = []
    return ob


# ---------------------------------------------------------------- the props (metres)
def phone():
    # 7.5 x 15 cm, 8 mm thick, long axis along the fingers; the screen faces out of the palm (-y here)
    box('body', 0.085, -0.004, 0.0, 0.150, 0.0080, 0.075, 'plastic', bevel=0.003, segs=4)
    screen('screen', 0.085, -0.0084, 0.0, 0.142, 0.067, 'screen_phone_e')
    box('camera', 0.150, 0.0002, -0.022, 0.012, 0.0012, 0.022, 'glass_dark', bevel=0.001, segs=2)
    return finish('prop__phone')


def tablet():
    # 24 x 17 cm held by one short edge: it runs out along the fingers from the palm, the screen out of the palm
    box('body', 0.105, -0.004, 0.0, 0.240, 0.0075, 0.170, 'plastic', bevel=0.004, segs=4)
    screen('screen', 0.105, -0.0081, 0.0, 0.224, 0.154, 'screen_tablet_e')
    box('button', 0.0, -0.0080, 0.0, 0.004, 0.0004, 0.014, 'plastic_light')
    return finish('prop__tablet')


def clipboard():
    # a 23 x 32 cm hardboard with a sheaf of paper and a clip at the far end, held like the tablet
    box('board', 0.130, -0.001, 0.0, 0.320, 0.0040, 0.230, 'board', bevel=0.002, segs=2)
    box('paper', 0.125, -0.0055, 0.0, 0.297, 0.0030, 0.210, 'paper')
    box('clip', 0.272, -0.010, 0.0, 0.030, 0.0120, 0.110, 'metal', bevel=0.003, segs=3)
    box('clip_lip', 0.258, -0.014, 0.0, 0.006, 0.004, 0.100, 'metal')
    return finish('prop__clipboard')


def book():
    # open on the palm: the spine along the fingers, the two halves fanned either side and tilted up 14 degrees,
    # each turning about its inner edge so the whole underside (spine and the covers' inner edges) is at y = 0
    for s in (-1, 1):
        tilt = s * math.radians(14)
        pivot = Vector((0.095, 0.0, 0.0))
        def tilted(local):
            v = Vector(local)
            v.rotate(Euler((tilt, 0.0, 0.0)))
            return pivot + v
        c = tilted((0.0, -0.00175, s * 0.069))
        box('cover', c.x, c.y, c.z, 0.198, 0.0035, 0.138, 'cover', bevel=0.0012, segs=2, rot=(tilt, 0, 0))
        c = tilted((0.0, -0.0035 - 0.009, s * 0.064))
        box('pages', c.x, c.y, c.z, 0.190, 0.018, 0.128, 'page', rot=(tilt, 0, 0))
    box('spine', 0.095, -0.006, 0.0, 0.198, 0.012, 0.016, 'cover', bevel=0.002, segs=2)
    return finish('prop__book')


def headset():
    # a VR headset, modelled for the head: the visor looks along +x, the strap circles behind; 17 cm wide
    box('visor', 0.0, 0.0, 0.0, 0.095, 0.170, 0.085, 'plastic', bevel=0.014, segs=5)
    box('faceplate', 0.046, 0.0, 0.0, 0.006, 0.150, 0.066, 'plastic_light', bevel=0.003, segs=3)
    for y in (-0.034, 0.034):
        cyl('lens', 0.050, y, 0.004, 0.017, 0.004, 'glass_dark', axis='x', verts=24)
    box('gasket', -0.052, 0.0, 0.0, 0.016, 0.168, 0.080, 'foam', bevel=0.007, segs=3)
    # the strap: a loop round the head behind the visor, a top strap over it
    # the head is longer than it is wide: the band is an ellipse 23 x 18.5 cm centred 12 cm behind the visor
    torus('strap', -0.120, 0.0, 0.0, 0.115, 0.009, 'strap', rot=(0, 0, 0), scale=(1.0, 0.80, 1.0))
    torus('top_strap', -0.120, 0.0, 0.0, 0.112, 0.008, 'strap', rot=(math.pi / 2, 0, 0), scale=(1.0, 1.0, 0.95))
    box('back_pad', -0.230, 0.0, -0.005, 0.022, 0.070, 0.060, 'foam', bevel=0.008, segs=3)
    return finish('prop__headset')


def carton():
    # a taped cardboard box about its own centre: 32 deep (x), 40 wide (y), 28 tall (z)
    box('box', 0.0, 0.0, 0.0, 0.320, 0.400, 0.280, 'cardboard', bevel=0.004, segs=2)
    box('tape', 0.0, 0.0, 0.1405, 0.322, 0.050, 0.0012, 'tape')
    box('tape_side', 0.0, 0.0, -0.1405, 0.322, 0.050, 0.0012, 'tape')
    return finish('prop__box')


def export():
    os.makedirs(OUT, exist_ok=True)
    obs = [o for o in bpy.data.objects if o.type == 'MESH']
    select_only(obs)
    fp = os.path.join(OUT, 'HandProps.glb')
    bpy.ops.export_scene.gltf(filepath=fp, export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
                              export_texcoords=True, export_normals=True, export_tangents=False, export_materials='EXPORT',
                              export_vertex_color='NONE', export_lights=False, export_cameras=False)
    print('exported', fp, os.path.getsize(fp), 'bytes', flush=True)


def main():
    L.reset()
    mats()
    for build in (phone, tablet, clipboard, book, headset, carton):
        ob = build()
        tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        d = ob.dimensions
        print('%-15s %6d tris  %.3f x %.3f x %.3f m' % (ob.name, tris, d.x, d.y, d.z), flush=True)
    export()


if __name__ == '__main__':
    main()
