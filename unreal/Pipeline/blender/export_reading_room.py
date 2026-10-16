"""
Export the Reading Room from Blender for Unreal Engine 5.

Unreal lights the room in real time (Lumen), so the baked lighting from the web build is
stripped: the lightmap UV channel ('lm') and the baked vertex colours ('light') are removed and
only the PBR materials and geometry go out. Lights are written to a JSON file instead, so the
Unreal setup script can spawn proper Unreal lights in the same places.

First build the Unreal version of the scene (no bake, a minute or two):
    python bl/library.py --ue          (with Blender's Python / bpy 5.2.2)
Run (Blender 5.2, from the repo root):
    blender -b assets/lib_ue/library.blend --python unreal/Pipeline/blender/export_reading_room.py
or with Blender as a Python module (bpy 5.2.2):
    python unreal/Pipeline/blender/export_reading_room.py

Writes:
    unreal/Pipeline/out/reading_room/ReadingRoom.glb    geometry + PBR materials + textures
    unreal/Pipeline/out/reading_room/lights.json        the room's lights, in campus metres

Axes: Blender (X, Y, Z) = campus (x, -z, y). glTF is Y-up, so the .glb is in three.js campus
coordinates; Unreal's glTF importer maps glTF (x, y, z) m -> Unreal (X=x, Y=z, Z=y) cm, which is
the same mapping the rest of the Unreal project uses (see unreal/Pipeline/README.md).
"""
import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
# The Unreal build of the room (bl/library.py --ue: real books on every tier, thick walls) when it exists,
# else the web build's scene
SRC_UE = os.path.join(REPO, 'assets', 'lib_ue', 'library.blend')
SRC = SRC_UE if os.path.exists(SRC_UE) else os.path.join(REPO, 'assets', 'lib', 'library.blend')
OUT = os.path.join(REPO, 'unreal', 'Pipeline', 'out', 'reading_room')


def main():
    if os.path.abspath(bpy.data.filepath or '') != SRC:
        bpy.ops.wm.open_mainfile(filepath=SRC)
    os.makedirs(OUT, exist_ok=True)

    lights = []
    for o in list(bpy.data.objects):
        if o.type != 'LIGHT':
            continue
        L = o.data
        x, y, z = o.matrix_world.translation
        d = o.matrix_world.to_quaternion() @ __import__('mathutils').Vector((0, 0, -1))
        lights.append({
            'name': o.name,
            'type': L.type,                                   # POINT | SUN | AREA | SPOT
            'campus_pos_m': [round(x, 4), round(z, 4), round(-y, 4)],
            'campus_dir': [round(d.x, 4), round(d.z, 4), round(-d.y, 4)],
            'blender_watts': round(L.energy, 3),
            'color_linear': [round(c, 4) for c in L.color],
            'radius_m': round(getattr(L, 'shadow_soft_size', 0.0), 4),
            'area_size_m': [round(getattr(L, 'size', 0.0), 4), round(getattr(L, 'size_y', 0.0), 4)] if L.type == 'AREA' else None,
        })
        bpy.data.objects.remove(o, do_unlink=True)

    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        me = o.data
        for uv in [u for u in me.uv_layers if u.name == 'lm']:
            me.uv_layers.remove(uv)
        for ca in [c for c in me.color_attributes if c.name == 'light']:
            me.color_attributes.remove(ca)
        # Glass: keep it a real transparent material in Unreal (translucent, not dithered)
        for m in me.materials:
            if m and m.name == 'glass':
                m.surface_render_method = 'BLENDED'

    glb = os.path.join(OUT, 'ReadingRoom.glb')
    bpy.ops.export_scene.gltf(
        filepath=glb,
        export_format='GLB',
        export_yup=True,
        export_apply=True,
        export_texcoords=True,
        export_normals=True,
        export_tangents=True,
        export_materials='EXPORT',
        export_image_format='AUTO',
        export_vertex_color='NONE',
        export_lights=False,
        export_cameras=False,
        use_selection=False,
    )
    with open(os.path.join(OUT, 'lights.json'), 'w') as f:
        json.dump({'source': os.path.relpath(SRC, REPO), 'units': 'metres, three.js campus axes (y up)', 'lights': lights}, f, indent=1)
    print('wrote', glb, os.path.getsize(glb), 'bytes;', len(lights), 'lights')


if __name__ == '__main__':
    main()
