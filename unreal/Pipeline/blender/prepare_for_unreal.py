"""
Make the exported wings import cleanly into Unreal Engine as plain static meshes.

Unreal's asset import keeps each glTF mesh in its own local space (node transforms are not applied
when you import meshes as assets). So before Unreal sees them, this pass:
  * bakes every object's world transform into its vertices (so every mesh sits at the origin and
    lands in the right place when spawned at Unreal (0, 0, 0)),
  * joins untagged meshes that share a material into one mesh per material (fewer, bigger meshes:
    ideal for Nanite and quick to place),
  * keeps tagged interactive pieces (item__, token__, ride__, staff__, station__, book__, bp__)
    as their own meshes with their tag as the name,
  * drops vertex colours that only carried baked lighting,
  * names materials M_<Asset>_... and textures T_<Asset>_... so Unreal's Content Browser is readable.

Run from the repo root with Blender 5.2 (or bpy 5.2.2):
    python unreal/Pipeline/blender/prepare_for_unreal.py
Reads  unreal/Pipeline/out/campus/<wing>.glb and unreal/Pipeline/out/reading_room/ReadingRoom.glb
Writes unreal/Pipeline/out/ue/<Name>.glb and unreal/Pipeline/out/ue/manifest.json
"""
import json
import os
import re

import bpy

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
OUT = os.path.join(REPO, 'unreal', 'Pipeline', 'out', 'ue')
SOURCES = [
    ('Museum', 'unreal/Pipeline/out/campus/museum.glb'),
    ('WaxIntro', 'unreal/Pipeline/out/campus/waxIntro.glb'),
    ('WaxHall', 'unreal/Pipeline/out/campus/wax.glb'),
    ('LibraryShell', 'unreal/Pipeline/out/campus/lib.glb'),
    ('School', 'unreal/Pipeline/out/campus/school.glb'),
    ('Outside', 'unreal/Pipeline/out/campus/outside.glb'),
    ('Yard', 'unreal/Pipeline/out/campus/play.glb'),
    ('OceanDive', 'unreal/Pipeline/out/campus/dive.glb'),
    ('ReadingRoom', 'unreal/Pipeline/out/reading_room/ReadingRoom.glb'),
]
TAG = re.compile(r'^(item|token|ride|staff|station|book|bp)__')


def tag_of(o):
    p = o
    while p is not None:
        if TAG.match(p.name):
            return p.name.split('.')[0]
        p = p.parent
    return None


def clean_name(s):
    return re.sub(r'[^A-Za-z0-9_]+', '_', s).strip('_')[:60] or 'Mesh'


def process(name, rel):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(REPO, rel))
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    tags = {o: tag_of(o) for o in meshes}
    # Bake world transforms into the vertices, and unparent
    for o in meshes:
        mw = o.matrix_world.copy()
        o.parent = None
        if o.data.users > 1:
            o.data = o.data.copy()
        o.data.transform(mw)
        o.matrix_world.identity()
        for ca in list(o.data.color_attributes):
            o.data.color_attributes.remove(ca)
    for o in [o for o in bpy.data.objects if o.type != 'MESH']:
        bpy.data.objects.remove(o, do_unlink=True)
    # Group: tagged objects by tag; untagged by (first) material
    groups = {}
    for o in meshes:
        t = tags[o]
        if t:
            key = t
        else:
            mat = o.data.materials[0] if o.data.materials else None
            key = 'M_' + clean_name(mat.name if mat else 'none') + ('_%d' % len(o.data.materials) if len(o.data.materials) > 1 else '')
        groups.setdefault(key, []).append(o)
    used = set()
    for key, objs in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        if len(objs) > 1:
            bpy.ops.object.join()
        o = bpy.context.view_layer.objects.active
        nm = clean_name(key.replace('__', '__'))
        base, i = nm, 1
        while nm in used:
            i += 1
            nm = '%s_%d' % (base, i)
        used.add(nm)
        o.name = nm
        o.data.name = nm
    # Readable asset names in Unreal: M_<Asset>_<n> materials and T_<Asset>_<material>_<n> textures
    # (canvas textures from the web export have no names, which would import as image_0 ... image_442)
    for i, m in enumerate(sorted({m for o in bpy.data.objects if o.type == 'MESH' for m in o.data.materials if m}, key=lambda m: m.name)):
        base = clean_name(m.name) if not m.name.lower().startswith(('material', 'mat_')) else 'Mat'
        m.name = 'M_%s_%s_%03d' % (name, base[:24], i)
        if m.node_tree:
            for k, n in enumerate([n for n in m.node_tree.nodes if getattr(n, 'image', None)]):
                n.image.name = 'T_%s_%s_%d' % (name, base[:24], k) if n.image.users <= 1 else n.image.name
    for k, img in enumerate(bpy.data.images):
        if not img.name.startswith('T_'):
            img.name = 'T_%s_shared_%03d' % (name, k)
    fp = os.path.join(OUT, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=fp, export_format='GLB', export_yup=True, export_apply=False, export_texcoords=True,
                              export_normals=True, export_tangents=True, export_materials='EXPORT', export_image_format='AUTO',
                              export_vertex_color='NONE', export_lights=False, export_cameras=False)
    objs = [o for o in bpy.data.objects if o.type == 'MESH']
    tris = 0
    for o in objs:
        o.data.calc_loop_triangles()
        tris += len(o.data.loop_triangles)
    return {'file': name + '.glb', 'source': rel, 'meshes': len(objs), 'tagged': sorted(o.name for o in objs if TAG.match(o.name)),
            'triangles': tris, 'bytes': os.path.getsize(fp)}


def main():
    os.makedirs(OUT, exist_ok=True)
    man = {'units': 'metres in glTF (Y up); Unreal import maps glTF (x, y, z) m -> UE (X=x, Y=z, Z=y) cm. Every mesh is baked in world space: spawn at UE (0,0,0), rotation 0, scale 1.',
           'assets': {}}
    for name, rel in SOURCES:
        man['assets'][name] = process(name, rel)
        a = man['assets'][name]
        print(name, a['meshes'], 'meshes', a['triangles'], 'tris', a['bytes'], 'bytes')
    with open(os.path.join(OUT, 'manifest.json'), 'w') as f:
        json.dump(man, f, indent=1)


if __name__ == '__main__':
    main()
