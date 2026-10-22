"""Benches for the rooms the web campus left bare of seating, built in the campus's own frame (metres, y up)
and tagged so Unreal seats a visitor on each: seat__<id>_f<yaw>, one mesh per sitting place, <yaw> the Unreal
yaw a sitter faces (atan2(dz, dx) in campus axes), the frames and backs untagged (joined by material).

    The Wax Hall: a double-sided settee in the middle of the aisle between each pair of facing stages, a seat
    toward each side, so a visitor can sit and watch a whole scene play from either side.

    python3 bl/seats.py   ->  unreal/Pipeline/out/props/Seats.glb  (then prepare_for_unreal.py -- Seats)
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import library as L                                              # noqa: E402
from library import Builder, material, prism, select_only        # noqa: E402

OUT = os.path.join(L.SP, 'unreal', 'Pipeline', 'out', 'props')

# The Wax Hall's stages face each other across the aisle in rows (WaxScenes.json, campus z); a settee goes
# between each pair of rows, on the hall's centre line.
WAX_ROWS = (-48.1, -54.0, -59.9, -65.8, -71.7)


def mats():
    material('settee_walnut', color=(0.22, 0.12, 0.07, 1), roughness=0.45)
    material('settee_leather', color=(0.30, 0.07, 0.09, 1), roughness=0.5)
    material('settee_brass', color=(0.78, 0.60, 0.30, 1), roughness=0.3, metallic=1.0)


def settee(name, x, z, length=1.7, seat_h=0.46):
    """A double-sided settee centred at campus (x, z), its length along z: a walnut frame on turned feet with
    brass shoes, a padded seat each side (tagged) and a shared padded back between them."""
    wd = Builder(name + '_walnut', 'settee_walnut', tile=1.0, lightmap=False, vcol=False, seg=0, smooth=40)
    br = Builder(name + '_brass', 'settee_brass', tile=0.3, lightmap=False, vcol=False, seg=0, smooth=40)
    depth = 1.04
    # the frame: a deck under both seats, aprons round it, four turned feet on brass shoes
    wd.box(x, seat_h - 0.095, z, depth, 0.05, length)                                   # deck
    for sx in (-1, 1): wd.box(x + sx * (depth / 2 - 0.03), seat_h - 0.11, z, 0.06, 0.10, length)   # long aprons
    for sz in (-1, 1): wd.box(x, seat_h - 0.11, z + sz * (length / 2 - 0.03), depth, 0.10, 0.06)   # end aprons
    for sx in (-1, 1):
        for sz in (-1, 1):
            fx, fz = x + sx * (depth / 2 - 0.09), z + sz * (length / 2 - 0.09)
            L.turned(wd, fx, 0.025, fz, seat_h - 0.145, 0.085, n=10, prof=[(0.0, 0.7), (0.25, 1.0), (0.55, 0.6), (0.8, 0.75), (1.0, 0.95)])
            prism(br, fx, 0.0, fz, 0.034, 0.025, n=12)                                  # brass shoe
    # the back: a panel down the middle, padded both sides, a brass bead along its top
    wd.box(x, seat_h + 0.26, z, 0.07, 0.52, length - 0.16)
    for sx in (-1, 1):
        pad = Builder(name + '_backpad%d' % (sx + 1), 'settee_leather', tile=0.5, lightmap=False, vcol=False, seg=0)
        pad.box(x + sx * 0.055, seat_h + 0.27, z, 0.04, 0.34, length - 0.24)
        pad.finish()
    br.box(x, seat_h + 0.53, z, 0.09, 0.02, length - 0.14)
    # the seats: one padded cushion a side, each its own tagged mesh so Unreal makes a seat of it
    for k, sx in enumerate((-1, 1)):
        yaw = int(round(math.degrees(math.atan2(0.0, float(sx))))) % 360               # a sitter faces out from the back
        cushion = Builder('seat__%s%s_f%d' % (name, 'ab'[k], yaw), 'settee_leather', tile=0.5, lightmap=False, vcol=False, seg=0)
        cushion.box(x + sx * 0.28, seat_h - 0.035, z, 0.48, 0.07, length - 0.12)
        cushion.finish()
    wd.finish(); br.finish()


def export():
    os.makedirs(OUT, exist_ok=True)
    obs = [o for o in bpy.data.objects if o.type == 'MESH']
    select_only(obs)
    fp = os.path.join(OUT, 'Seats.glb')
    bpy.ops.export_scene.gltf(filepath=fp, export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
                              export_texcoords=True, export_normals=True, export_tangents=False, export_materials='EXPORT',
                              export_vertex_color='NONE', export_lights=False, export_cameras=False)
    print('exported', fp, os.path.getsize(fp), 'bytes', flush=True)


def main():
    L.reset()
    mats()
    for i, (za, zb) in enumerate(zip(WAX_ROWS, WAX_ROWS[1:])):
        settee('wax%d' % (i + 1), 0.0, (za + zb) / 2)
    obs = [o for o in bpy.data.objects if o.type == 'MESH']
    print('objects', len(obs), 'seats', sum(1 for o in obs if o.name.startswith('seat__')), 'tris', sum(len(o.data.polygons) * 2 for o in obs), flush=True)
    export()


if __name__ == '__main__':
    main()
