"""Benches for the rooms the web campus left bare of seating, built in the campus's own frame (metres, y up)
and tagged so Unreal seats a visitor on each: seat__<id>_f<yaw>, one mesh per sitting place, <yaw> the Unreal
yaw a sitter faces (atan2(dz, dx) in campus axes), the frames and backs untagged (joined by material).

    The Wax Hall: a double-sided settee in the middle of the aisle between each pair of facing stages, a seat
    toward each side, so a visitor can sit and watch a whole scene play from either side.
    The Recess Yard: six park benches (cast-iron ends, painted slats) round the rim of the round plaza, each
    facing its middle, in the gaps between the paths that leave it.
    The Workshop School's hall: an oak bench on a steel frame against each long wall, between the room doors.

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


# The yard's plaza (the web's round paving, parts/outdoor.js): its centre and the rim the benches sit on, and the
# bearings (degrees, campus: 0 = +x east, 90 = +z south) of the paths that leave it, which the benches keep clear of.
PLAZA = (52.0, -1.5)
PLAZA_R = 6.0
PLAZA_PATHS = (180.0, -115.0, 0.0, 86.0, 134.0)        # the school door, the coaster, the pitch, the dive, the playground
BENCH_BEARINGS = (-80.0, -35.0, 43.0, 110.0, 157.0, 212.0)
# the school hall (x 12..34, z -4.8..-1.2; campus z runs south) and its doors (the studio and the lab through the north
# wall at x 19 and 29, the blueprint room and Room 104 through the south wall at the same x): a bench against each
# wall between the doors, facing into the hall
HALL_BENCHES = ((24.0, -4.45, (0.0, 1.0)), (24.0, -1.55, (0.0, -1.0)))


def mats():
    material('settee_walnut', color=(0.22, 0.12, 0.07, 1), roughness=0.45)
    material('settee_leather', color=(0.30, 0.07, 0.09, 1), roughness=0.5)
    material('settee_brass', color=(0.78, 0.60, 0.30, 1), roughness=0.3, metallic=1.0)
    material('bench_iron', color=(0.10, 0.10, 0.11, 1), roughness=0.55, metallic=0.8)
    material('bench_slat', color=(0.16, 0.27, 0.20, 1), roughness=0.6)                    # park green paint
    material('bench_oak', color=(0.55, 0.40, 0.25, 1), roughness=0.5)
    material('bench_steel', color=(0.35, 0.36, 0.38, 1), roughness=0.4, metallic=0.9)


def facing_ry(fx, fz):
    """Builder.box's ry so that the box's local +x points along the campus direction (fx, fz)."""
    return math.atan2(-fz, fx)


def park_bench(name, x, z, fx, fz, length=1.8, seat_h=0.45):
    """A park bench centred at campus (x, z), its sitter facing (fx, fz): cast-iron ends with a scrolled arm, three
    seat slats (one tagged mesh) and two back slats, painted park green."""
    ry = facing_ry(fx, fz)
    yaw = L.seat_yaw(fx, fz)
    fe = Builder(name + '_iron', 'bench_iron', tile=0.5, lightmap=False, vcol=False, seg=0, smooth=40)
    sl = Builder(name + '_slats', 'bench_slat', tile=0.6, lightmap=False, vcol=False, seg=0)
    seat = Builder('seat__%s_f%d' % (name, yaw), 'bench_slat', tile=0.6, lightmap=False, vcol=False, seg=0)
    hl = length / 2
    def B(b, lx, ly, lz, sx, sy, sz):
        # a box at local (lx, ly, lz): local x faces the sitter's way, local z along the bench
        cr, sr = math.cos(ry), math.sin(ry)
        wx = x + lx * cr + lz * sr; wz = z - lx * sr + lz * cr
        b.box(wx, ly, wz, sx, sy, sz, ry=ry)
    for sz_ in (-1, 1):
        ez = sz_ * (hl - 0.05)
        B(fe, 0.17, 0.21, ez, 0.05, 0.42, 0.05)                        # front leg
        B(fe, -0.19, 0.21, ez, 0.05, 0.42, 0.05)                       # back leg
        B(fe, -0.01, 0.405, ez, 0.44, 0.04, 0.06)                      # seat rail
        B(fe, -0.235, 0.66, ez, 0.05, 0.50, 0.05)                      # back post
        B(fe, 0.0, 0.645, ez, 0.42, 0.035, 0.06)                       # arm
        B(fe, 0.19, 0.53, ez, 0.04, 0.20, 0.04)                        # arm's front stay
    for k, lx in enumerate((-0.13, 0.0, 0.13)):
        B(seat, lx, seat_h - 0.02, 0.0, 0.11, 0.04, length)            # seat slats
    for ly in (0.63, 0.80):
        B(sl, -0.225, ly, 0.0, 0.035, 0.12, length)                    # back slats
    fe.finish(); sl.finish(); seat.finish()


def hall_bench(name, x, z, fx, fz, length=1.8, seat_h=0.45):
    """An oak bench on a steel frame against a wall, its sitter facing (fx, fz) away from it: three seat slats
    (one tagged mesh), a back board, square-tube legs and rails."""
    ry = facing_ry(fx, fz)
    yaw = L.seat_yaw(fx, fz)
    st = Builder(name + '_steel', 'bench_steel', tile=0.5, lightmap=False, vcol=False, seg=0)
    ok = Builder(name + '_oak', 'bench_oak', tile=0.8, lightmap=False, vcol=False, seg=0)
    seat = Builder('seat__%s_f%d' % (name, yaw), 'bench_oak', tile=0.8, lightmap=False, vcol=False, seg=0)
    hl = length / 2
    def B(b, lx, ly, lz, sx, sy, sz):
        cr, sr = math.cos(ry), math.sin(ry)
        wx = x + lx * cr + lz * sr; wz = z - lx * sr + lz * cr
        b.box(wx, ly, wz, sx, sy, sz, ry=ry)
    for sz_ in (-1, 1):
        ez = sz_ * (hl - 0.08)
        B(st, 0.17, 0.205, ez, 0.03, 0.41, 0.03)                       # front leg
        B(st, -0.18, 0.46, ez, 0.03, 0.92, 0.03)                       # back leg, up to the back board
        B(st, 0.0, 0.395, ez, 0.38, 0.03, 0.03)                        # seat rail
    B(st, -0.18, 0.12, 0.0, 0.03, 0.03, length - 0.16)                  # a stretcher between the back legs
    for lx in (-0.12, 0.0, 0.12):
        B(seat, lx, seat_h - 0.02, 0.0, 0.10, 0.04, length)
    B(ok, -0.175, 0.78, 0.0, 0.03, 0.26, length)                        # the back board
    st.finish(); ok.finish(); seat.finish()


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
    cx, cz = PLAZA
    for i, deg in enumerate(BENCH_BEARINGS):
        a = math.radians(deg)
        bx, bz = cx + PLAZA_R * math.cos(a), cz + PLAZA_R * math.sin(a)
        park_bench('yard_p%d' % (i + 1), bx, bz, -math.cos(a), -math.sin(a))             # facing the plaza's middle
    for i, (bx, bz, (fx, fz)) in enumerate(HALL_BENCHES):
        hall_bench('school_h%d' % (i + 1), bx, bz, fx, fz)
    obs = [o for o in bpy.data.objects if o.type == 'MESH']
    print('objects', len(obs), 'seats', sum(1 for o in obs if o.name.startswith('seat__')), 'tris', sum(len(o.data.polygons) * 2 for o in obs), flush=True)
    export()


if __name__ == '__main__':
    main()
