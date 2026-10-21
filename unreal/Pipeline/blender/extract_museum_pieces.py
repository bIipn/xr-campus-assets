"""
Keep the web campus pieces the Blender-built museum (bl/museum.py) and grounds (bl/exterior.py) build around.

The neoclassical museum replaces every wall, floor, ceiling, partition and lamp of the web export, but the
things that carry the content stay exactly where the catalog (Data/Exhibits.json) expects them: the framed
exhibits and vitrines (item__<id>), the hidden token, the title panel and plaque, the directory and partner
panels, the gallery door signs, the wing signs and the hall posters.

The same for the grounds: the school's east facade (door frame, canopy, lettering, windows, mural, lamps,
rooftop plant) and the Wax Hall's 'LIVING HISTORY' letters stay; the ground, shells, trees and horizon are rebuilt.

Run once, from the repo root, with the web exports in place (unreal/Pipeline/out/ue/Museum.glb and Outside.glb as
exported by prepare_for_unreal.py from the three.js campus):
    blender -b --python unreal/Pipeline/blender/extract_museum_pieces.py        (or: python3 ... with bpy)
Writes unreal/Pipeline/out/museum/web_pieces.glb (bl/museum.py imports it) and
unreal/Pipeline/out/exterior/web_pieces.glb (bl/exterior.py imports it).
"""
import os
import sys

import bpy

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
SRC = os.path.join(REPO, 'unreal', 'Pipeline', 'out', 'ue', 'Museum.glb')
OUT = os.path.join(REPO, 'unreal', 'Pipeline', 'out', 'museum', 'web_pieces.glb')
SRC_OUT = os.path.join(REPO, 'unreal', 'Pipeline', 'out', 'ue', 'Outside.glb')
OUT_OUT = os.path.join(REPO, 'unreal', 'Pipeline', 'out', 'exterior', 'web_pieces.glb')

# Untagged meshes of the web export worth keeping (names as prepare_for_unreal.py wrote them)
KEEP = {
    'M_glow': 'token glow',
    'M_Material_8': 'door sign lobby-g1', 'M_Material_10': 'door sign g1-g2', 'M_Material_12': 'door sign g2-g3',
    'M_Material_88': 'door sign g3-wax',
    'M_Material_13': 'title panel frame', 'M_Material_14': 'title panel', 'M_Material_15': 'plaque',
    'M_Material_16': 'directory frame', 'M_Material_17': 'directory', 'M_Material_18': 'partners frame', 'M_Material_19': 'partners',
    'M_Material_32': 'headset lens', 'M_Material_33': 'headset lens', 'M_Material_34': 'headset lens', 'M_Material_35': 'headset lens',
    'M_Material_74': 'wing sign library', 'M_Material_75': 'wing sign school',
    'M_Material_80': 'hall poster', 'M_Material_81': 'hall poster', 'M_Material_86': 'hall poster', 'M_Material_87': 'hall poster',
    'M_Material_89': 'g3 end panel frame', 'M_Material_90': 'g3 end panel',
}

KEEP_OUTSIDE = {
    'M_glow': 'school door lamp glow', 'M_Material_4': 'LIVING HISTORY letters', 'M_Material_8': 'school canopy',
    'M_Material_9': 'school canopy', 'M_Material_10': 'WORKSHOP SCHOOL letters', 'M_Material_11': 'school mural',
    'M_Material_19': 'rooftop units', 'M_Material_20': 'school door frame', 'M_Material_21': 'school plinths',
    'M_Material_22': 'school windows', 'M_Material_23': 'school wall lamps',
}


def extract(src, out, keep, least):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    kept, dropped = [], []
    for o in list(bpy.data.objects):
        if o.type != 'MESH':
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        base = o.name.split('.')[0]
        if base.startswith(('item__', 'token__')) or base in keep:
            kept.append(o.name)
        else:
            dropped.append(o.name)
            bpy.data.objects.remove(o, do_unlink=True)
    if len(kept) < least:
        raise SystemExit('only %d pieces found in %s; is it the web export?' % (len(kept), src))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_yup=True, export_apply=True, export_texcoords=True,
                              export_normals=True, export_materials='EXPORT', export_image_format='AUTO',
                              export_vertex_color='NONE', export_lights=False, export_cameras=False)
    print('kept', len(kept), 'pieces:', ', '.join(sorted(kept)))
    print('dropped', len(dropped), 'meshes')
    print('wrote', out, os.path.getsize(out), 'bytes')


def main():
    which = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    if not which or 'museum' in which:
        extract(SRC, OUT, KEEP, 20)
    if not which or 'outside' in which:
        extract(SRC_OUT, OUT_OUT, KEEP_OUTSIDE, 8)


if __name__ == '__main__':
    main()
