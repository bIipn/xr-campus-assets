"""The grounds, built for real: everything outside the museum that the Outside asset carries, in Blender (bpy) at
campus coordinates, for Unreal.

The terrain (a lawn that dips into a wildflower meadow in front of the museum's steps); the Forecourt Theatre, an
open-air talk space at the foot of the steps (a stepped stage with a lectern, two framed slide screens either side
of it, and a cavea of curved limestone tiers with teak-capped seats, a passage through its middle and an aisle with
steps in each half, a balustrade with urns along the back); a flagstone path from the theatre to the fountain, now
further out on the grounds, and on;
trees along it and around the campus, bronze lamp posts, the horizon hills, and the stone shells of the other
buildings: the Wax Hall annex, the Reading Room, the two halls, the Workshop School, and the talks wing (the
auditorium and its foyer, bl/auditorium.py), in the same limestone order as the museum (pilasters, entablature,
parapet). The school's east facade pieces from the web (door frame, canopy, lettering, windows, mural, lamps,
rooftop plant) and the Wax Hall's 'LIVING HISTORY' letters are imported from unreal/Pipeline/out/exterior/
web_pieces.glb and kept.

The museum building itself - gallery block, rotunda, portico, steps - is bl/museum.py's; the two scripts share the
plan constants and ground_height() so steps, terrain and path agree.

Usage (Blender 5.2 or bpy 5.2.2):   python bl/exterior.py [--quick] [--render]
Writes assets/exterior/exterior.blend, unreal/Pipeline/out/exterior/Outside.glb (+ lights.json), preview renders.
Then: blender -b --python unreal/Pipeline/blender/prepare_for_unreal.py -- Outside
"""
import json
import math
import os
import random
import sys
import time

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import library as L                                              # noqa: E402
from library import P, D, Builder, bar, prism, material, MATS, frange, select_only, seat_yaw   # noqa: E402
import neo                                                       # noqa: E402
from neo import lathe, annulus, wall_with_door, run_boxes, entablature, pilaster, urn, tree, blob, lantern, smooth, face_uv, ENT_H   # noqa: E402
import museum as M                                               # noqa: E402  (the plan: constants and ground_height)

SP = L.SP
OUT = os.path.join(SP, 'assets', 'exterior')
PIPE = os.path.join(SP, 'unreal', 'Pipeline', 'out', 'exterior')
PIECES = os.path.join(PIPE, 'web_pieces.glb')
QUICK = '--quick' in sys.argv
RENDER = '--render' in sys.argv
os.makedirs(OUT, exist_ok=True); os.makedirs(PIPE, exist_ok=True)
rnd = random.Random(2026)

gh = M.ground_height
PATH_W = 3.2
PATH_Z0 = M.STY_Z1 + (M.STEPS - 1) * M.TREAD      # the foot of the steps
PATH_Z1 = 70.0
FOUNTAIN = (0.0, 50.0)                            # moved out beyond the theatre (it stood at z 34)

# the Forecourt Theatre: a stage at the foot of the museum's steps, the speaker facing the grounds (+z) with the
# portico behind, two slide screens either side, and a cavea of tiers in arcs about the stage
TH_C = (0.0, 20.4)                                # the stage's centre; the tiers are arcs about it
TH_Y = M.FORECOURT_Y                              # the forecourt floor (-0.75)
TH_R0 = 6.6                                       # the orchestra's edge: the first riser
TH_D, TH_H, TH_N = 1.0, 0.38, 6                   # tier depth, tier rise, tiers: each tier's front edge is a row of seats
TH_RO = TH_R0 + TH_N * TH_D                       # the back of the cavea (12.6)
TH_A = math.radians(55.0)                         # the cavea spans 55 degrees either side of +z
TH_GAP = PATH_W / 2                               # the passage through the middle at ground level, where the path runs
TH_AISLE, TH_AISLE_W = math.radians(30.0), 1.2    # an aisle with steps in each half
SEAT_D, SEAT_T = 0.42, 0.045                      # a seat: the front of a tier, capped with a teak board
TH_SEG = ((0, 14), (1, 2), (2, 12))               # cells along each arc: (segment, samples) for seats, aisle, seats
BAL_H = 0.98                                      # the balustrade round the top tier: its rail's top above the tier
PED_W = 0.50                                      # the balustrade's pedestals, and the pilasters under them
STAGE_R, STAGE_BACK = 3.0, 18.95                  # the stage: a half disc about TH_C with a straight back
STAGE_TOP = TH_Y + 0.40
SPEAKER = (0.0, 20.65)                            # the speaker's feet, facing +z
LECTERN = (0.0, 21.25)
SCREEN_W = 4.0; SCREEN_H = SCREEN_W * 9 / 16
SCREEN_X, SCREEN_Z, SCREEN_TURN = 7.0, 20.9, math.radians(22.0)
SCREEN_Y0 = 0.62                                  # the image's bottom edge

# the other buildings' shells (campus metres, from the web layout), each with its own parapet height
SHELLS = {
    # each 15 cm outside the web building's own outer faces (WaxHall x +-8.70; the Reading Room's green
    # walls x -32.45..-11.55, z -13.45..7.45; the School z -13.40), so the ashlar reads and never z-fights
    'wax':     dict(x0=-8.85, x1=8.85, z0=-81.3, z1=-42.0, h=5.4),
    'library': dict(x0=-32.6, x1=-11.4, z0=-13.6, z1=7.6, h=7.9),
    'hallL':   dict(x0=-11.8, x1=-6.2, z0=-4.8, z1=-1.2, h=3.65),
    'hallR':   dict(x0=6.2, x1=11.8, z0=-4.8, z1=-1.2, h=3.65),
    'school':  dict(x0=11.8, x1=34.2, z0=-13.6, z1=7.2, h=4.3),
    # the talks wing (bl/auditorium.py builds the rooms): the foyer between the galleries and the School, north of
    # Hall R, and the auditorium behind it, its south face against the School's north face
    'foyer':      dict(x0=6.3, x1=11.75, z0=-13.65, z1=-4.8, h=4.95),
    'auditorium': dict(x0=6.3, x1=21.2, z0=-31.45, z1=-13.65, h=7.4),
}
# faces that stand against another building get no wall; where a lower neighbour leaves the top of a face in view,
# that face is built from the height given (no plinth or pilasters, the order's entablature still runs)
SHELL_SKIP = {('hallL', 'W'), ('hallL', 'E'), ('hallR', 'W'), ('hallR', 'E'), ('hallR', 'N'), ('wax', 'S'),
              ('foyer', 'W'), ('foyer', 'N'), ('auditorium', 'W')}
SHELL_FROM = {('foyer', 'E'): 4.5, ('foyer', 'S'): 3.7, ('auditorium', 'S'): 4.6}
# openings in those shells: (shell, wall, u0, u1, h) - 'E' east wall x1, 'W' west wall x0 (u along z)
OPENINGS = [('library', 'E', -4.8, -1.2, 3.65), ('school', 'W', -4.8, -1.2, 3.65), ('school', 'E', -4.6, -1.4, 3.0),
            ('wax', 'S', -1.9, 1.9, 3.3)]
# web tree positions kept (parts/outdoor.js), minus the two that stood where the rotunda and forecourt now are
# (the ones at (9, -9.5), (9, -17), (9, -25), (9, -34), (19, -17.5) and (14, -25) gave way to the talks wing)
CAMPUS_TREES = [(9, 3.8), (16, 11.5), (24.5, 12.5), (-20, 12), (-28.5, 11), (27, -18.5),
                (-8.5, -20), (-9, -31), (-22, -18), (-30, -21), (25.0, -27.5), (24.5, -33.0)]
YARD_TREES = [(47.5, 23.4), (54, 23.8), (60.5, 23.2), (71.5, 23.6), (78, 23.2), (84.5, 23.6), (90, 22), (89.8, 15.5), (90, 8), (89.6, 1.2),
              (89.8, -5.5), (61.2, 11.6), (69.5, 1.6), (84.8, 7.4), (46.7, 8.4), (69.5, 16.6), (58.2, -6.2), (37.2, 6.4)]
# new: an allee either side of the path, and groves on the meadow
# (the allee's first two pairs, z 24 and 31, gave way to the theatre's tiers)
PATH_TREES = [(s * 8.5, z) for z in (39.0, 47.0, 55.0) for s in (-1, 1)] + \
             [(-17.0, 26.0), (-21.0, 36.0), (-15.5, 46.0), (-24.0, 52.0), (17.5, 27.0), (22.0, 38.0), (16.0, 48.0), (25.0, 55.0),
              (-12.0, 60.0), (13.0, 61.0), (-30.0, 20.0), (31.0, 22.0)]


def setup_materials():
    material('grass', 'grass_col', 'grass_rgh', 'grass_nrm', roughness=0.9)
    material('meadow', 'meadow_col', 'meadow_rgh', 'meadow_nrm', roughness=0.92)
    material('flag', 'flag_col', 'flag_rgh', 'flag_nrm', roughness=0.85)
    material('ashlar', 'ashlar_col', 'ashlar_rgh', 'ashlar_nrm', roughness=0.75)
    material('lime', 'lime_col', 'lime_rgh', 'lime_nrm', roughness=0.7)
    material('bark', 'bark_col', 'bark_rgh', 'bark_nrm', roughness=0.9)
    material('leaf', 'leaf_col', 'leaf_rgh', 'leaf_nrm', roughness=0.8)
    material('stone', 'marblew_col', 'marblew_rgh', 'marblew_nrm', roughness=0.3)
    material('bronze', color=(0.40, 0.26, 0.13, 1), roughness=0.42, metallic=1.0)
    material('lamp_e', color=(1, 1, 1, 1), emission=(1.0, 0.86, 0.62, 1), emission_strength=14.0)
    material('roof', color=(0.36, 0.37, 0.38, 1), roughness=0.8)
    material('glass', color=(0.9, 0.95, 1.0, 1), roughness=0.05, alpha=0.12)
    material('water', color=(0.55, 0.72, 0.78, 1), roughness=0.03, metallic=0.1)
    material('hills', color=(0.30, 0.42, 0.24, 1), roughness=0.95)
    material('teak', 'oak_col', 'oak_rgh', 'oak_nrm', roughness=0.55)                    # the theatre's seat boards
    material('th_tier', 'lime_col', 'lime_rgh', 'lime_nrm', roughness=0.75)              # the cavea's tiers and the stage's sides
    material('th_marble', 'marblew_col', 'marblew_rgh', 'marblew_nrm', roughness=0.3)    # stage top, copings, lectern, the orchestra's band
    material('gilt', color=(1.0, 0.78, 0.38, 1), roughness=0.32, metallic=1.0)
    material('th_black', color=(0.012, 0.012, 0.014, 1), roughness=0.45)                 # the screens' bezels
    material('th_mark', color=(0.2, 0.2, 0.2, 1), roughness=0.9)                        # the speaker's spot (never shown)
    material('screen_forecourt', color=(0.04, 0.04, 0.045, 1), roughness=0.3)          # the engine puts the slides on it
    material('farleaf', color=(0.16, 0.30, 0.12, 1), roughness=0.9)
    # leaf cards: alpha-masked (the Greater Than node is what the glTF exporter turns into alphaMode MASK)
    m = bpy.data.materials.new('leafcard'); m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = L.image('leafcard_col'); tex.location = (-500, 0)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.5; gt.location = (-250, -200)
    nt.links.new(tex.outputs['Alpha'], gt.inputs[0]); nt.links.new(gt.outputs[0], bsdf.inputs['Alpha'])
    bsdf.inputs['Roughness'].default_value = 0.75
    m.surface_render_method = 'DITHERED'
    MATS['leafcard'] = m


B = {}
def builder(name, mat, tile=1.0, seg=0.0):
    if name not in B: B[name] = Builder(name, mat, tile=tile, lightmap=False, vcol=False, seg=seg)
    return B[name]

LIGHTS = []


# ---------------------------------------------------------------- terrain
# The ground has a hole under the auditorium (bl/auditorium.py sinks its rows to an orchestra 1.6 m below grade; the
# hall's own floor, walls and shell close it): the hall's inner footprint, so the grass still runs under its walls.
GROUND_HOLES = [(6.75, 20.75, -31.0, -14.10)]


def cell_minus_holes(xa, xb, za, zb):
    """The parts of the cell (xa..xb, za..zb) outside GROUND_HOLES, as rectangles."""
    parts = [(xa, xb, za, zb)]
    for (hx0, hx1, hz0, hz1) in GROUND_HOLES:
        out = []
        for (x0, x1, z0, z1) in parts:
            if x1 <= hx0 or x0 >= hx1 or z1 <= hz0 or z0 >= hz1:
                out.append((x0, x1, z0, z1)); continue
            if x0 < hx0: out.append((x0, hx0, z0, z1))                    # the strip west of the hole
            if x1 > hx1: out.append((hx1, x1, z0, z1))                    # east of it
            mx0, mx1 = max(x0, hx0), min(x1, hx1)
            if z0 < hz0: out.append((mx0, mx1, z0, hz0))                  # south of it (between the strips)
            if z1 > hz1: out.append((mx0, mx1, hz1, z1))                  # north of it
        parts = out
    return parts


def build_terrain():
    """An inner grid (2 m cells) over the campus with the forecourt bowl shaped into it, and a coarse flat apron out
    to 320 m. Cells in the bowl take the meadow material; cells over a GROUND_HOLE keep only what lies outside it."""
    gr = builder('ground', 'grass', tile=3.0); md = builder('meadow', 'meadow', tile=3.0)
    X0, X1, Z0, Z1, C = -70.0, 130.0, -110.0, 90.0, 2.0
    nx, nz = int((X1 - X0) / C), int((Z1 - Z0) / C)
    for i in range(nx):
        for j in range(nz):
            xa, za = X0 + i * C, Z0 + j * C
            for (x0, x1, z0, z1) in cell_minus_holes(xa, xa + C, za, za + C):
                pts = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
                hs = [gh(x, z) for (x, z) in pts]
                b = md if min(hs) < -0.05 else gr
                b.face([P(x, h - 0.012, z) for ((x, z), h) in zip(pts, hs)][::-1], D(0, 1, 0))
    # the apron: eight flat panels around the inner grid, out to the far edge
    far = builder('ground', 'grass', tile=3.0)
    FX0, FX1, FZ0, FZ1 = -290.0, 350.0, -328.0, 312.0
    for (xa, xb, za, zb) in ((FX0, X0, FZ0, FZ1), (X1, FX1, FZ0, FZ1), (X0, X1, FZ0, Z0), (X0, X1, Z1, FZ1)):
        far.grid(P(xa, -0.012, zb), P(xb, -0.012, zb) - P(xa, -0.012, zb), P(xa, -0.012, za) - P(xa, -0.012, zb), Vector((0, 0, 1)), 4, 4)


def path_height(z):
    return gh(0.0, z)


def build_path():
    """Flagstones: a plaza at the foot of the steps and the theatre's orchestra (build_theatre), the passage through
    the cavea, the walk out to the fountain's round plaza, and a gentle curve beyond it."""
    fl = builder('path', 'flag', tile=2.4)
    def centre_x(z):
        if z < FOUNTAIN[1] + 8.0: return 0.0
        t = (z - FOUNTAIN[1] - 8.0) / 12.0
        return -4.0 * math.sin(min(t, 1.0) * math.pi / 2) * 1.0 if t < 1.0 else -4.0 + 2.5 * math.sin((z - FOUNTAIN[1] - 20.0) / 7.0)
    def strip(z0, z1, half, step=0.5):
        z = z0
        while z < z1 - 1e-6:
            zb = min(z + step, z1)
            xa, xb = centre_x(z), centre_x(zb)
            fl.face([P(xa - half, gh(xa, z) + 0.02, z), P(xa + half, gh(xa, z) + 0.02, z), P(xb + half, gh(xb, zb) + 0.02, zb), P(xb - half, gh(xb, zb) + 0.02, zb)], D(0, 1, 0))
            z = zb
    z_pass = TH_C[1] + TH_RO + 0.4                                # the passage through the cavea ends here
    strip(z_pass, FOUNTAIN[1] - 7.0, PATH_W / 2)
    strip(FOUNTAIN[1] + 7.0, PATH_Z1, PATH_W / 2)
    # the round plaza: an annulus around the fountain basin
    fx, fz = FOUNTAIN
    n = 48
    for k in range(n):
        a0 = 2 * math.pi * k / n; a1 = 2 * math.pi * (k + 1) / n
        for (r0, r1) in ((3.0, 5.0), (5.0, 7.2)):
            pts = [(fx + r0 * math.cos(a0), fz + r0 * math.sin(a0)), (fx + r1 * math.cos(a0), fz + r1 * math.sin(a0)),
                   (fx + r1 * math.cos(a1), fz + r1 * math.sin(a1)), (fx + r0 * math.cos(a1), fz + r0 * math.sin(a1))]
            fl.face([P(x, gh(x, z) + 0.02, z) for (x, z) in pts], D(0, 1, 0))
    # a low stone kerb around the plaza
    kb = builder('kerbs', 'stone', tile=2.0)
    for k in range(n):
        a0 = 2 * math.pi * k / n; a1 = 2 * math.pi * (k + 1) / n
        if abs(math.sin((a0 + a1) / 2)) > 0.92: continue          # gaps where the path enters and leaves
        x0, z0 = fx + 7.3 * math.cos(a0), fz + 7.3 * math.sin(a0); x1, z1 = fx + 7.3 * math.cos(a1), fz + 7.3 * math.sin(a1)
        y = gh((x0 + x1) / 2, (z0 + z1) / 2)
        bar(kb, (x0, y + 0.12, z0), (x1, y + 0.12, z1), 0.3, 0.3)
    fountain()


def fountain():
    fx, fz = FOUNTAIN
    y = gh(fx, fz)
    st = builder('fountain', 'stone', tile=2.0); wt = builder('water', 'water')
    lathe(st, fx, fz, [(y - 0.3, 3.0), (y + 0.55, 3.0), (y + 0.65, 3.1), (y + 0.72, 3.0), (y + 0.72, 2.75), (y + 0.3, 2.7)], n=48)
    annulus(wt, fx, fz, y + 0.5, 0.0, 2.72, 0, 2 * math.pi, n=48)
    # a pedestal with an urn, and a smaller upper bowl
    lathe(st, fx, fz, [(y + 0.3, 0.9), (y + 0.4, 0.9), (y + 0.45, 0.7), (y + 1.4, 0.6), (y + 1.5, 0.75), (y + 1.55, 0.85)], n=32)
    lathe(st, fx, fz, [(y + 1.55, 0.4), (y + 1.75, 1.4), (y + 1.95, 1.5), (y + 2.0, 1.35), (y + 1.85, 1.1)], n=40, cap_top=False)
    annulus(wt, fx, fz, y + 1.9, 0.0, 1.3, 0, 2 * math.pi, n=32)
    urn(st, fx, fz, y + 1.95, h=1.4, s=1.0)


# ---------------------------------------------------------------- the Forecourt Theatre
def th_pt(r, th, side):
    """A point of the cavea: radius r about the stage centre, th radians from +z toward the side (+1 east, -1 west)."""
    return (TH_C[0] + side * r * math.sin(th), TH_C[1] + r * math.cos(th))


def th_bounds(r, margin=0.0):
    """The angles (from +z) where, at radius r, the passage edge, the aisle's two edges and the cavea's end lie.
    margin pulls the seat segments in from those edges (for the teak boards)."""
    g = math.asin(min(0.999, (TH_GAP + margin) / r))
    w = TH_AISLE_W / 2 + margin
    return g, TH_AISLE - math.asin(min(0.999, w / r)), TH_AISLE + math.asin(min(0.999, w / r)), TH_A - margin / r


def th_angles(r):
    """The angles at radius r where the back wall's chords meet, from the passage edge to the cavea's end: the tiers'
    own cell samples, so a course laid along the wall follows it exactly."""
    g, a0, a1, e = th_bounds(r)
    out = []
    for (seg, n), (lo, hi) in zip(TH_SEG, ((g, a0), (a0, a1), (a1, e))):
        out += [lo + (hi - lo) * i / n for i in range(n + (1 if seg == 2 else 0))]
    return out


def arc_band(b, side, r0, r1, y0, y1, top=False, bottom=False, inner=False, outer=True, ends=False):
    """A course round the cavea's back between radii r0 and r1, from y0 to y1, on the wall's chords; its ends lie in
    the passage's plane and the cavea's end plane."""
    p0 = [th_pt(r0, a, side) for a in th_angles(r0)]; p1 = [th_pt(r1, a, side) for a in th_angles(r1)]
    for i in range(len(p0) - 1):
        a0, b0, a1, b1 = p0[i], p0[i + 1], p1[i], p1[i + 1]
        n = D((a1[0] + b1[0]) / 2 - TH_C[0], 0, (a1[1] + b1[1]) / 2 - TH_C[1]).normalized()
        if top: b.face([P(a0[0], y1, a0[1]), P(b0[0], y1, b0[1]), P(b1[0], y1, b1[1]), P(a1[0], y1, a1[1])], D(0, 1, 0))
        if bottom: b.face([P(a0[0], y0, a0[1]), P(b0[0], y0, b0[1]), P(b1[0], y0, b1[1]), P(a1[0], y0, a1[1])], D(0, -1, 0))
        if outer: b.face([P(a1[0], y0, a1[1]), P(b1[0], y0, b1[1]), P(b1[0], y1, b1[1]), P(a1[0], y1, a1[1])], n)
        if inner: b.face([P(a0[0], y0, a0[1]), P(b0[0], y0, b0[1]), P(b0[0], y1, b0[1]), P(a0[0], y1, a0[1])], -n)
    if ends:
        for k, nrm in ((0, D(-side, 0, 0)), (-1, D(side * math.cos(TH_A), 0, -math.sin(TH_A)))):
            a, c = p0[k], p1[k]
            b.face([P(a[0], y0, a[1]), P(c[0], y0, c[1]), P(c[0], y1, c[1]), P(a[0], y1, a[1])], nrm)


def arc_piece(b, side, r0, r1, lo, hi, y0, y1, faces='tbioLH'):
    """A block on the cavea's back between radii r0 and r1, from angle lo(r) to hi(r) (functions of the radius, so
    an end can lie in the passage's plane), from y0 to y1. faces: t top, b bottom, i inner, o outer, L/H the ends."""
    a0, b0 = th_pt(r0, lo(r0), side), th_pt(r0, hi(r0), side)
    a1, b1 = th_pt(r1, lo(r1), side), th_pt(r1, hi(r1), side)
    am = (lo(r1) + hi(r1)) / 2
    n = D(side * math.sin(am), 0, math.cos(am)); t = D(side * math.cos(am), 0, -math.sin(am))
    if 't' in faces: b.face([P(a0[0], y1, a0[1]), P(b0[0], y1, b0[1]), P(b1[0], y1, b1[1]), P(a1[0], y1, a1[1])], D(0, 1, 0))
    if 'b' in faces: b.face([P(a0[0], y0, a0[1]), P(b0[0], y0, b0[1]), P(b1[0], y0, b1[1]), P(a1[0], y0, a1[1])], D(0, -1, 0))
    if 'o' in faces: b.face([P(a1[0], y0, a1[1]), P(b1[0], y0, b1[1]), P(b1[0], y1, b1[1]), P(a1[0], y1, a1[1])], n)
    if 'i' in faces: b.face([P(a0[0], y0, a0[1]), P(b0[0], y0, b0[1]), P(b0[0], y1, b0[1]), P(a0[0], y1, a0[1])], -n)
    if 'L' in faces: b.face([P(a0[0], y0, a0[1]), P(a1[0], y0, a1[1]), P(a1[0], y1, a1[1]), P(a0[0], y1, a0[1])], -t)
    if 'H' in faces: b.face([P(b0[0], y0, b0[1]), P(b1[0], y0, b1[1]), P(b1[0], y1, b1[1]), P(b0[0], y1, b0[1])], t)


# a stone baluster from the bottom of its foot block: (height, radius) of the turned part, between square blocks
BALUSTER = [(0.05, 0.050), (0.075, 0.056), (0.095, 0.040), (0.13, 0.042), (0.20, 0.060), (0.27, 0.066), (0.34, 0.060),
            (0.42, 0.044), (0.50, 0.030), (0.56, 0.026), (0.60, 0.032), (0.62, 0.044), (0.65, 0.044), (0.68, 0.036)]


def cavea_back(side, base):
    """The cavea's back, seen from the grounds, in the campus's order: an ashlar plinth course, pilasters, a lime
    cornice level with the top tier; and on the top tier, a marble balustrade (a base, turned balusters, a rail)
    with pedestals over the pilasters - at the passage, at the aisle's head, between, and at the cavea's end - and
    urns on the end pedestals."""
    ash = builder('th_walls', 'ashlar', tile=2.4); lime = builder('th_cornice', 'lime', tile=3.0)
    mb = builder('th_coping', 'th_marble', tile=2.0); bal = builder('th_balusters', 'th_marble', tile=1.0)
    R = TH_RO
    hp = TH_Y + TH_N * TH_H                               # the top tier, the cornice's top, the balustrade's foot
    y_pl = TH_Y + 0.48                                    # the plinth's top
    y_co = hp - 0.26                                      # the cornice's underside
    # the plinth course and the cornice (three steps out)
    arc_band(ash, side, R, R + 0.08, base - 0.2, TH_Y + 0.40, ends=True)
    arc_band(ash, side, R, R + 0.12, TH_Y + 0.40, y_pl, top=True, bottom=True, ends=True)
    for (y0, y1, d, last) in ((y_co, hp - 0.18, 0.06, False), (hp - 0.18, hp - 0.08, 0.12, False), (hp - 0.08, hp, 0.20, True)):
        arc_band(lime, side, R, R + d, y0, y1, top=last, bottom=True, ends=True)
    # where the pedestals stand: (lo(r), hi(r)) for each; the ends lie in the passage's plane and the cavea's end
    def at_passage(w):
        return lambda r: math.asin(min(0.999, (TH_GAP + w) / r))
    def at_end(w):
        return lambda r: TH_A + w / R
    def centred(c, w):
        return (lambda r: c - w / (2 * R)), (lambda r: c + w / (2 * R))
    lo_aisle = TH_AISLE - PED_W / (2 * R)
    c1 = (at_passage(PED_W)(R) + lo_aisle) / 2
    c2 = (TH_AISLE + PED_W / (2 * R) + TH_A - PED_W / R) / 2
    spans = [(at_passage(0.0), at_passage(PED_W))] + [centred(c, PED_W) for c in (c1, TH_AISLE, c2)] + [(at_end(-PED_W), at_end(0.0))]
    def grown(k, w):
        """span k widened by w each side (a passage or end face moves out with it)."""
        lo, hi = spans[k]
        if k == 0: return at_passage(-w), at_passage(PED_W + w)
        if k == len(spans) - 1: return at_end(-PED_W - w), at_end(w)
        c = (lo(R) + hi(R)) / 2
        return centred(c, PED_W + 2 * w)
    # pilasters under the pedestals, from the plinth to the cornice: a base, the shaft, a capital
    for k in range(len(spans)):
        lo, hi = spans[k]
        arc_piece(ash, side, R - 0.01, R + 0.14, lo, hi, y_pl, y_co - 0.18, faces='oLH')
        blo, bhi = grown(k, 0.04)
        arc_piece(ash, side, R - 0.01, R + 0.18, blo, bhi, y_pl, y_pl + 0.22, faces='tboLH')
        arc_piece(lime, side, R - 0.01, R + 0.18, blo, bhi, y_co - 0.18, y_co, faces='tboLH')
    # the balustrade: a base and a rail round the top tier's back (their ends run into the end pedestals)
    arc_band(mb, side, R - 0.32, R, hp, hp + 0.12, top=True, inner=True)
    arc_band(mb, side, R - 0.34, R + 0.02, hp + BAL_H - 0.14, hp + BAL_H, top=True, bottom=True, inner=True)
    for k in range(len(spans)):
        lo, hi = spans[k]
        arc_piece(mb, side, R - 0.38, R + 0.04, lo, hi, hp, hp + BAL_H, faces='ioLH')
        clo, chi = grown(k, 0.05)
        arc_piece(mb, side, R - 0.43, R + 0.09, clo, chi, hp + BAL_H, hp + BAL_H + 0.09, faces='tbioLH')
        if k in (0, len(spans) - 1):
            am = (lo(R - 0.17) + hi(R - 0.17)) / 2
            ux, uz = th_pt(R - 0.17, am, side)
            urn(builder('th_urns', 'th_marble', tile=1.0), ux, uz, hp + BAL_H + 0.09, h=0.62, s=0.6, n=16)
    # turned balusters between the pedestals, on the base's middle line
    rb = R - 0.16
    for k in range(len(spans) - 1):
        a0, a1 = spans[k][1](rb), spans[k + 1][0](rb)
        L_ = rb * (a1 - a0) - 0.30
        m = max(1, int(L_ // 0.25) + 1)
        for q in range(m):
            a = a0 + (0.15 + L_ * q / max(1, m - 1)) / rb
            bx, bz = th_pt(rb, a, side)
            yb = hp + 0.12
            ry = a * side
            bal.box(bx, yb + 0.025, bz, 0.12, 0.05, 0.12, ry=ry, faces='xXYzZ')
            lathe(bal, bx, bz, [(yb + y, r) for (y, r) in BALUSTER], n=10, cap_top=False)
            bal.box(bx, yb + 0.70, bz, 0.10, 0.04, 0.10, ry=ry, faces='xXyzZ')


def build_theatre():
    """The cavea: tiers in arcs about the stage, TH_D deep and TH_H high, from the orchestra's edge (TH_R0) to the
    back wall (TH_RO), each half running from the central passage (|x| = TH_GAP, where the path runs through at ground
    level) out to TH_A; in each half an aisle steps up at half-tier rises. Each tier's front edge is a row of seats,
    capped with teak boards, the sitter's feet on the tier below; a marble balustrade runs along the back (cavea_back). Then the stage, the
    lectern, the two screens, the orchestra and the passage floor."""
    tr = builder('th_treads', 'th_tier', tile=2.0); rs = builder('th_risers', 'th_tier', tile=2.0)
    wl = builder('th_walls', 'ashlar', tile=2.4)
    teak_seats = 0
    NR = 2 * TH_N                                       # half-tier rings
    rings = [TH_R0 + k * TH_D / 2 for k in range(NR + 1)]
    SEG = TH_SEG
    def seg_angles(r, seg):
        g, a0, a1, e = th_bounds(r)
        lo, hi = ((g, a0), (a0, a1), (a1, e))[seg]
        n = dict(SEG)[seg]
        return [lo + (hi - lo) * i / n for i in range(n + 1)]
    def height(k, seg):
        if seg == 1: return TH_Y + (k + 1) * TH_H / 2
        return TH_Y + (k // 2 + 1) * TH_H
    base = TH_Y - 0.06
    for side in (-1, 1):
        for seg, n in SEG:
            for k in range(NR):
                h = height(k, seg)
                A = seg_angles(rings[k], seg); Bn = seg_angles(rings[k + 1], seg)
                for i in range(n):
                    p00 = th_pt(rings[k], A[i], side); p01 = th_pt(rings[k], A[i + 1], side)
                    p11 = th_pt(rings[k + 1], Bn[i + 1], side); p10 = th_pt(rings[k + 1], Bn[i], side)
                    tr.face([P(p00[0], h, p00[1]), P(p01[0], h, p01[1]), P(p11[0], h, p11[1]), P(p10[0], h, p10[1])], D(0, 1, 0))
                    # the riser in front of this cell, where it stands above the cell in front (or the orchestra)
                    lower = base if k == 0 else height(k - 1, seg)
                    if h - lower > 1e-4:
                        mid = th_pt(rings[k], (A[i] + A[i + 1]) / 2, side)
                        out = (TH_C[0] - mid[0], TH_C[1] - mid[1])
                        rs.face([P(p00[0], lower, p00[1]), P(p01[0], lower, p01[1]), P(p01[0], h, p01[1]), P(p00[0], h, p00[1])], D(out[0], 0, out[1]).normalized())
                # the faces along the segment's sides
                if seg == 0:                             # the passage wall, facing the passage
                    a = th_pt(rings[k], A[0], side); c = th_pt(rings[k + 1], Bn[0], side)
                    wl.face([P(a[0], base, a[1]), P(c[0], base, c[1]), P(c[0], h, c[1]), P(a[0], h, a[1])], D(-side, 0, 0))
                if seg == 2:                             # the cavea's end, facing outward
                    a = th_pt(rings[k], A[-1], side); c = th_pt(rings[k + 1], Bn[-1], side)
                    nrm = D(side * math.cos(TH_A), 0, -math.sin(TH_A))
                    wl.face([P(a[0], base, a[1]), P(c[0], base, c[1]), P(c[0], h, c[1]), P(a[0], h, a[1])], nrm)
                if seg == 1:                             # where the aisle runs half a tier below the seats beside it
                    hs = height(k, 0)
                    if hs - h > 1e-4:
                        for (edge, toward) in ((0, 1), (-1, -1)):
                            a = th_pt(rings[k], A[edge], side); c = th_pt(rings[k + 1], Bn[edge], side)
                            # the face looks into the aisle: along the arc toward the aisle's middle
                            ang = (A[edge] + Bn[edge]) / 2
                            tang = (side * math.cos(ang) * toward, -math.sin(ang) * toward)
                            rs.face([P(a[0], h, a[1]), P(c[0], h, c[1]), P(c[0], hs, c[1]), P(a[0], hs, a[1])], D(tang[0], 0, tang[1]).normalized())
            # the back wall's outside, from below grade to the top tier (cavea_back() dresses it and puts the
            # balustrade on top)
            A = seg_angles(TH_RO, seg)
            hp = height(NR - 1, seg)
            for i in range(n):
                a = th_pt(TH_RO, A[i], side); c = th_pt(TH_RO, A[i + 1], side)
                mid = th_pt(TH_RO, (A[i] + A[i + 1]) / 2, side)
                out = (mid[0] - TH_C[0], mid[1] - TH_C[1])
                wl.face([P(a[0], base - 0.2, a[1]), P(c[0], base - 0.2, c[1]), P(c[0], hp, c[1]), P(a[0], hp, a[1])], D(out[0], 0, out[1]).normalized())
        cavea_back(side, base)
        # the seats: teak boards on the front of each tier, cut in pieces about 0.9 m long, each a tagged mesh
        for j in range(1, TH_N + 1):
            rj = TH_R0 + (j - 1) * TH_D
            y = TH_Y + j * TH_H
            r_in, r_out = rj - 0.03, rj + SEAT_D
            for seg in (0, 2):
                bi, bo = th_bounds(r_in, 0.12), th_bounds(r_out, 0.12)
                lo_in, hi_in = (bi[0], bi[1]) if seg == 0 else (bi[2], bi[3])
                lo_out, hi_out = (bo[0], bo[1]) if seg == 0 else (bo[2], bo[3])
                rm = (r_in + r_out) / 2
                arc = rm * (hi_in - lo_in)
                pieces = max(1, int(round(arc / 0.9)))
                for q in range(pieces):
                    t0, t1 = q / pieces, (q + 1) / pieces
                    gap = 0.0075 / arc                   # a 1.5 cm joint between boards
                    t0 += gap if q > 0 else 0.0; t1 -= gap if q < pieces - 1 else 0.0
                    ai0, ai1 = lo_in + (hi_in - lo_in) * t0, lo_in + (hi_in - lo_in) * t1
                    ao0, ao1 = lo_out + (hi_out - lo_out) * t0, lo_out + (hi_out - lo_out) * t1
                    thc = (ai0 + ai1 + ao0 + ao1) / 4
                    cx, cz = th_pt(rm, thc, side)
                    yaw = seat_yaw(TH_C[0] - cx, TH_C[1] - cz)
                    name = 'seat__forecourt_%s%d%s%02d_f%d' % ('w' if side < 0 else 'e', j, 'ab'[seg // 2], q + 1, yaw)
                    tb = builder(name, 'teak', tile=1.0)
                    teak_board(tb, side, r_in, r_out, ai0, ai1, ao0, ao1, y, y + SEAT_T)
                    teak_seats += 1
    theatre_floor()
    stage()
    screens()
    return teak_seats


def teak_board(b, side, r_in, r_out, ai0, ai1, ao0, ao1, y0, y1, n=4):
    """A curved board between radii r_in and r_out, its ends along the given angles, from y0 to y1."""
    ins = [th_pt(r_in, ai0 + (ai1 - ai0) * i / n, side) for i in range(n + 1)]
    outs = [th_pt(r_out, ao0 + (ao1 - ao0) * i / n, side) for i in range(n + 1)]
    for i in range(n):
        b.face([P(ins[i][0], y1, ins[i][1]), P(ins[i + 1][0], y1, ins[i + 1][1]), P(outs[i + 1][0], y1, outs[i + 1][1]), P(outs[i][0], y1, outs[i][1])], D(0, 1, 0))
        mi = ((ins[i][0] + ins[i + 1][0]) / 2, (ins[i][1] + ins[i + 1][1]) / 2)
        toward = (TH_C[0] - mi[0], TH_C[1] - mi[1])
        b.face([P(ins[i][0], y0 - 0.006, ins[i][1]), P(ins[i + 1][0], y0 - 0.006, ins[i + 1][1]), P(ins[i + 1][0], y1, ins[i + 1][1]), P(ins[i][0], y1, ins[i][1])], D(toward[0], 0, toward[1]).normalized())
        b.face([P(outs[i + 1][0], y0, outs[i + 1][1]), P(outs[i][0], y0, outs[i][1]), P(outs[i][0], y1, outs[i][1]), P(outs[i + 1][0], y1, outs[i + 1][1])], D(-toward[0], 0, -toward[1]).normalized())
    # the overhang's underside (3 cm in front of the riser) and the two ends
    for (k, sgn) in ((0, -1), (n, 1)):
        a, c = ins[k], outs[k]
        ux, uz = c[0] - a[0], c[1] - a[1]
        nrm = D(-uz * sgn * side, 0, ux * sgn * side)
        b.face([P(a[0], y0, a[1]), P(c[0], y0, c[1]), P(c[0], y1, c[1]), P(a[0], y1, a[1])], nrm.normalized())
    lip = [th_pt(r_in + 0.03, ai0 + (ai1 - ai0) * i / n, side) for i in range(n + 1)]
    for i in range(n):
        b.face([P(ins[i][0], y0 - 0.006, ins[i][1]), P(lip[i][0], y0 - 0.006, lip[i][1]), P(lip[i + 1][0], y0 - 0.006, lip[i + 1][1]), P(ins[i + 1][0], y0 - 0.006, ins[i + 1][1])], D(0, -1, 0))


def theatre_floor():
    """Flagstones: a plaza from the foot of the steps to the stage's centre line, the orchestra (a half disc to the
    first riser, with a marble band along it), and the passage through the cavea out to the path."""
    fl = builder('path', 'flag', tile=2.4); bd = builder('th_band', 'th_marble', tile=2.0)
    y = TH_Y + 0.02
    cx, cz = TH_C
    x0, x1 = -9.6, 9.6
    z0 = PATH_Z0 - 0.05
    # the plaza, in 1.2 m strips
    zz = z0
    while zz < cz - 1e-6:
        zb = min(zz + 1.2, cz)
        fl.face([P(x0, y, zz), P(x1, y, zz), P(x1, y, zb), P(x0, y, zb)], D(0, 1, 0))
        zz = zb
    # the orchestra: radial sectors from the centre to the band, the band to the riser
    n = 64
    for k in range(n):
        a0 = -math.pi / 2 + math.pi * k / n; a1 = -math.pi / 2 + math.pi * (k + 1) / n
        for (r0, r1, b) in ((0.0, TH_R0 - 0.45, fl), (TH_R0 - 0.45, TH_R0, bd)):
            pts = [(cx + r0 * math.sin(a0), cz + r0 * math.cos(a0)), (cx + r1 * math.sin(a0), cz + r1 * math.cos(a0)),
                   (cx + r1 * math.sin(a1), cz + r1 * math.cos(a1)), (cx + r0 * math.sin(a1), cz + r0 * math.cos(a1))]
            if r0 < 1e-6: pts = pts[:3]
            b.face([P(px, y, pz) for (px, pz) in pts], D(0, 1, 0))
    # the passage: from the orchestra's arc out past the back of the cavea
    zend = TH_C[1] + TH_RO + 0.4
    m = 8
    for i in range(m):
        xa = -TH_GAP + 2 * TH_GAP * i / m; xb = -TH_GAP + 2 * TH_GAP * (i + 1) / m
        za = cz + math.sqrt(TH_R0 ** 2 - xa ** 2); zb_ = cz + math.sqrt(TH_R0 ** 2 - xb ** 2)
        fl.face([P(xa, y, za), P(xb, y, zb_), P(xb, y, zend), P(xa, y, zend)], D(0, 1, 0))


def stage():
    """A stepped stone stage: a step 0.2 high and 0.55 wide round a platform 0.4 high, both a half disc about the
    stage centre with a straight back toward the museum's steps; marble on top. A lectern stands at its front, the
    speaker's spot behind it."""
    side_b = builder('th_stage_sides', 'th_tier', tile=2.0); top_b = builder('th_stage_top', 'th_marble', tile=2.0)
    cx, cz = TH_C
    for (r, ytop, ybot) in ((STAGE_R + 0.55, TH_Y + 0.20, TH_Y - 0.05), (STAGE_R, STAGE_TOP, TH_Y + 0.20)):
        n = 40
        rim = [(cx + r * math.sin(-math.pi / 2 + math.pi * k / n), cz + r * math.cos(-math.pi / 2 + math.pi * k / n)) for k in range(n + 1)]
        outline = [(cx - r, STAGE_BACK)] + rim + [(cx + r, STAGE_BACK)]
        # top: a fan from the middle of the back edge
        c0 = (cx, (STAGE_BACK + cz) / 2)
        for k in range(len(outline) - 1):
            a, c = outline[k], outline[k + 1]
            top_b.face([P(c0[0], ytop, c0[1]), P(a[0], ytop, a[1]), P(c[0], ytop, c[1])], D(0, 1, 0))
        top_b.face([P(c0[0], ytop, c0[1]), P(outline[-1][0], ytop, outline[-1][1]), P(outline[0][0], ytop, outline[0][1])], D(0, 1, 0))
        # sides all round, the step's down below the floor, the platform's down to the step (their straight backs
        # share a plane, so they must not overlap)
        ring = outline + [outline[0]]
        for k in range(len(ring) - 1):
            a, c = ring[k], ring[k + 1]
            mx, mz = (a[0] + c[0]) / 2, (a[1] + c[1]) / 2
            if k == len(ring) - 2: nrm = D(0, 0, -1)
            elif k == 0 or k == len(ring) - 3: nrm = D(-1 if k == 0 else 1, 0, 0) if abs(a[1] - c[1]) > abs(a[0] - c[0]) else D(mx - cx, 0, mz - cz)
            else: nrm = D(mx - cx, 0, mz - cz)
            side_b.face([P(a[0], ybot, a[1]), P(c[0], ybot, c[1]), P(c[0], ytop, c[1]), P(a[0], ytop, a[1])], nrm.normalized())
    # the lectern: a stone pedestal with a sloping bronze desk, the speaker's spot behind it
    lx, lz = LECTERN
    pd = builder('th_lectern', 'th_marble', tile=1.0); bz = builder('bronze', 'bronze')
    pd.box(lx, STAGE_TOP + 0.06, lz, 0.62, 0.12, 0.48)
    pd.box(lx, STAGE_TOP + 0.12 + 0.40, lz, 0.46, 0.80, 0.34)
    pd.box(lx, STAGE_TOP + 0.95, lz, 0.56, 0.06, 0.42)
    # the desk slopes down toward the speaker (-z), 1.0 m above the stage at its low edge
    hz = 0.24; y_lo, y_hi = STAGE_TOP + 1.04, STAGE_TOP + 1.16
    bz.face([P(lx - 0.33, y_lo, lz - hz), P(lx + 0.33, y_lo, lz - hz), P(lx + 0.33, y_hi, lz + hz), P(lx - 0.33, y_hi, lz + hz)], D(0, 0.9, -0.45).normalized())
    bz.face([P(lx - 0.33, y_lo - 0.03, lz - hz), P(lx - 0.33, y_hi - 0.03, lz + hz), P(lx + 0.33, y_hi - 0.03, lz + hz), P(lx + 0.33, y_lo - 0.03, lz - hz)], D(0, -0.9, 0.45).normalized())
    for (xa, xb, za, zb, ya, yb) in ((lx - 0.33, lx + 0.33, lz - hz, lz - hz, y_lo - 0.03, y_lo), (lx - 0.33, lx + 0.33, lz + hz, lz + hz, y_hi - 0.03, y_hi)):
        bz.face([P(xa, ya, za), P(xb, ya, zb), P(xb, yb, zb), P(xa, yb, za)], D(0, 0, -1 if za < lz else 1))
    for xs in (lx - 0.33, lx + 0.33):
        bz.face([P(xs, y_lo - 0.03, lz - hz), P(xs, y_hi - 0.03, lz + hz), P(xs, y_hi, lz + hz), P(xs, y_lo, lz - hz)], D(1 if xs > lx else -1, 0, 0))
    bz.box(lx, STAGE_TOP + 1.0, lz + 0.05, 0.08, 0.10, 0.08)
    # the speaker's spot (the engine never shows it)
    sp = builder('spot__forecourt_f%d' % seat_yaw(0.0, 1.0), 'th_mark')
    x, z = SPEAKER
    sp.face([P(x - 0.15, STAGE_TOP + 0.01, z - 0.15), P(x + 0.15, STAGE_TOP + 0.01, z - 0.15), P(x + 0.15, STAGE_TOP + 0.01, z + 0.15), P(x - 0.15, STAGE_TOP + 0.01, z + 0.15)], D(0, 1, 0))


def screens():
    """Two slide screens in stone frames either side of the stage, turned toward the cavea: a plinth, two pilasters,
    an entablature and a low pediment round a black bezel; the image (screen__forecourt_l / _r) 4 mm in front of
    the bezel. The local axes: u to the audience's right, v up, w toward the audience."""
    st = builder('th_frames', 'th_tier', tile=2.0); pl = builder('th_plinths', 'ashlar', tile=2.4)
    bk = builder('th_bezel', 'th_black'); gold = builder('th_gilt', 'gilt')
    out = []
    for side in (-1, 1):
        ry = -side * SCREEN_TURN
        ux, uz = math.cos(ry), -math.sin(ry)             # u: the audience's right
        wx, wz = math.sin(ry), math.cos(ry)              # w: the way the screen faces
        cx, cz = side * SCREEN_X, SCREEN_Z
        def W(u, v, w): return P(cx + ux * u + wx * w, v, cz + uz * u + wz * w)
        def box(b, u, v, w, su, sv, sw, faces='all'):
            b.box(cx + ux * u + wx * w, v, cz + uz * u + wz * w, su, sv, sw, ry, faces=faces)
        hw = SCREEN_W / 2
        y0, y1 = SCREEN_Y0, SCREEN_Y0 + SCREEN_H
        # plinth from below grade to y 0.45, a moulded top course
        box(pl, 0, (TH_Y - 0.2 + 0.40) / 2, -0.05, SCREEN_W + 1.3, 0.40 - (TH_Y - 0.2), 0.80)
        box(st, 0, 0.47, -0.05, SCREEN_W + 1.42, 0.08, 0.90)
        # the back panel and the bezel the image sits in
        box(st, 0, (0.51 + y1 + 0.30) / 2, -0.30, SCREEN_W + 1.06, y1 + 0.30 - 0.51, 0.30, faces='xXYz')     # ends inside the pilasters
        box(bk, 0, (y0 + y1) / 2, -0.06, SCREEN_W + 0.16, SCREEN_H + 0.16, 0.12, faces='xXyYZ')
        # pilasters either side, standing proud of the back panel
        for su in (-1, 1):
            box(st, su * (hw + 0.38), (0.51 + y1 + 0.18) / 2, -0.06, 0.34, y1 + 0.18 - 0.51, 0.24, faces='xXYzZ')
            box(st, su * (hw + 0.38), y1 + 0.24, -0.04, 0.42, 0.12, 0.30)
        # the entablature and a low pediment
        ye = y1 + 0.30
        box(st, 0, ye + 0.10, -0.06, SCREEN_W + 1.30, 0.20, 0.36)
        box(st, 0, ye + 0.28, -0.04, SCREEN_W + 1.46, 0.16, 0.42)
        box(gold, 0, ye + 0.10, 0.125, SCREEN_W + 0.60, 0.03, 0.01, faces='Z')
        pw, ph = SCREEN_W / 2 + 0.70, 0.62
        yb = ye + 0.36
        for (wf, nz) in ((0.17, 1), (-0.25, -1)):
            pts = [W(-pw, yb, wf), W(pw, yb, wf), W(0, yb + ph, wf)]
            if nz < 0: pts = list(reversed(pts))
            st.face(pts, D(wx * nz, 0, wz * nz))
        for su in (-1, 1):
            a, c = W(su * pw, yb, 0.17), W(0, yb + ph, 0.17)
            a2, c2 = W(su * pw, yb, -0.25), W(0, yb + ph, -0.25)
            nrm = D(ux * su * ph, pw, uz * su * ph).normalized()
            q = [a, c, c2, a2] if su > 0 else [c, a, a2, c2]
            st.face(q, nrm)
        # the image
        sc = builder('screen__forecourt_%s' % ('l' if side < 0 else 'r'), 'screen_forecourt')
        wq = 0.004
        face_uv(sc, [W(-hw, y0, wq), W(hw, y0, wq), W(hw, y1, wq), W(-hw, y1, wq)], D(wx, 0, wz), [(0, 0), (1, 0), (1, 1), (0, 1)])
        out.append({'name': 'screen__forecourt_%s' % ('l' if side < 0 else 'r'),
                    'centre': [round(cx + wx * wq, 3), round((y0 + y1) / 2, 3), round(cz + wz * wq, 3)],
                    'size_m': [SCREEN_W, round(SCREEN_H, 4)], 'faces': [round(wx, 4), 0, round(wz, 4)]})
    THEATRE['screens'] = out


THEATRE = {}


# ---------------------------------------------------------------- buildings
def build_shells():
    ash = builder('shells', 'ashlar', tile=2.4); ent = builder('entablature', 'lime', tile=3.0); den = builder('dentils', 'lime', tile=3.0)
    rf = builder('roofs', 'roof', tile=2.0); gl = builder('glass', 'glass')
    for name, s in SHELLS.items():
        x0, x1, z0, z1, h = s['x0'], s['x1'], s['z0'], s['z1'], s['h']
        order = h >= 5.0                    # the big blocks carry the full order; the halls only a cornice
        top = h - (ENT_H if order else 0.4)
        walls = {'W': ((x0, z1), (x0, z0), (-1, 0)), 'E': ((x1, z0), (x1, z1), (1, 0)), 'N': ((x0, z0), (x1, z0), (0, -1)), 'S': ((x1, z1), (x0, z1), (0, 1))}
        for key, (a, c, out) in walls.items():
            # the halls meet the museum and the big blocks: skip the faces that would sit inside another shell
            # (the wax hall's south wall is the museum's end wall; the talks wing leans on the galleries and the School)
            if (name, key) in SHELL_SKIP: continue
            ops = [o for o in OPENINGS if o[0] == name and o[1] == key]
            y_from = SHELL_FROM.get((name, key))
            if y_from is not None:
                A0 = P(a[0], y_from, a[1]); C0 = P(c[0], y_from, c[1]); A1 = P(a[0], h, a[1])
                ash.grid(A0, C0 - A0, A1 - A0, D(out[0], 0, out[1]), 6, 2)
                if order: entablature(ent, den, a, c, out, top)
                else: run_boxes(ent, a, c, out, [(h - 0.40, h - 0.30, 0.10), (h - 0.30, h - 0.12, 0.18), (h - 0.12, h, 0.26)], seg=3.0)
                continue
            if ops:
                _n, _w, u0, u1, oh = ops[0]
                ux, uz = c[0] - a[0], c[1] - a[1]; Ln = math.hypot(ux, uz); ux, uz = ux / Ln, uz / Ln
                # u along the run from a; the opening's u0..u1 are campus z (walls E/W) or x (walls N/S)
                ua = (u0 - a[1]) * uz if key in ('E', 'W') else (u0 - a[0]) * ux
                ub = (u1 - a[1]) * uz if key in ('E', 'W') else (u1 - a[0]) * ux
                ua, ub = min(ua, ub), max(ua, ub)
                wall_with_door(ash, (a[0], -1.0, a[1]), (ux, 0, uz), (0, 1, 0), (out[0], 0, out[1]), 0.0, Ln, h + 1.0, ua, ub, oh + 1.0, solid=False)
                # the plinth course stops either side of the door: across it, it was a 50 cm kerb to jump
                run_boxes(ash, a, (a[0] + ux * ua, a[1] + uz * ua), out, [(-1.0, 0.5, 0.10), (0.5, 0.6, 0.14)], seg=3.0)
                run_boxes(ash, (a[0] + ux * ub, a[1] + uz * ub), c, out, [(-1.0, 0.5, 0.10), (0.5, 0.6, 0.14)], seg=3.0)
            else:
                A0 = P(a[0], -1.0, a[1]); C0 = P(c[0], -1.0, c[1]); A1 = P(a[0], h, a[1])
                ash.grid(A0, C0 - A0, A1 - A0, D(out[0], 0, out[1]), 6, 3)
                run_boxes(ash, a, c, out, [(-1.0, 0.5, 0.10), (0.5, 0.6, 0.14)], seg=3.0)
            if order:
                entablature(ent, den, a, c, out, top)
                ux, uz = c[0] - a[0], c[1] - a[1]; Ln = math.hypot(ux, uz); ux, uz = ux / Ln, uz / Ln
                sx = 0.6
                while sx <= Ln - 0.5:
                    pilaster(ash, ent, ash, (a[0] + ux * sx, a[1] + uz * sx), out, 0.7, top, depth=0.2)
                    sx += 6.0 if Ln > 12 else Ln - 1.2
            else:
                run_boxes(ent, a, c, out, [(h - 0.40, h - 0.30, 0.10), (h - 0.30, h - 0.12, 0.18), (h - 0.12, h, 0.26)], seg=3.0)
        rf.box((x0 + x1) / 2, h + 0.04, (z0 + z1) / 2, x1 - x0, 0.12, z1 - z0, faces='Y')     # above the rooms' own ceilings
        ash.box((x0 + x1) / 2, h + 0.25, (z0 + z1) / 2, x1 - x0 + 0.1, 0.5, z1 - z0 + 0.1, faces='xXzZY')      # parapet
    # the Reading Room's roof lantern (over the laylight x -30..-14, z -3.9..-2.1)
    lb = builder('shells', 'ashlar', tile=2.4)
    lb.box(-22.0, 7.9 + 0.5, -3.0, 17.0, 1.0, 3.2, faces='xXzZ')
    gl.face([P(-30.4, 8.95, -4.5), P(-13.6, 8.95, -4.5), P(-13.6, 8.95, -1.5), P(-30.4, 8.95, -1.5)], D(0, 1, 0))
    lb.box(-22.0, 9.0, -3.0, 17.4, 0.12, 3.6, faces='xXzZY')
    # a canopy over the school's back door is kept from the web; nothing more to add there


# ---------------------------------------------------------------- planting, lamps, horizon
def build_trees():
    bt = builder('trunks', 'bark', tile=1.0); bl = builder('leaves', 'leaf', tile=1.5); bc = builder('leafcards', 'leafcard')
    k = 0
    for (x, z) in CAMPUS_TREES + YARD_TREES + PATH_TREES:
        s = 1.05 + 0.5 * rnd.random()
        tree(bt, bl, x, z, s=s, seed=k, ground=gh(x, z) - 0.02, bc=bc); k += 1
    # far trees: cheaper, bigger, scattered beyond the campus box (the web's rule, re-seeded)
    ft = builder('far_trunks', 'bark', tile=1.0); fl = builder('far_leaves', 'farleaf')
    r = random.Random(99)
    n = 0
    while n < 140:
        x = -84 + 228 * r.random(); z = -96 + 168 * r.random()
        if (-40 < x < 97 and -50 < z < 70) or (-14 < x < 14 and -86 < z < -40): continue     # the campus box, and the Wax Hall
        s = 1.3 + 1.4 * r.random()
        far_tree(ft, fl, x, z, s, n); n += 1


def far_tree(bt, bl, x, z, s, seed):
    r = random.Random(seed)
    h = 3.0 * s
    lathe(bt, x, z, [(0.0, 0.22 * s), (h, 0.1 * s)], n=6, cap_top=True)
    blob(bl, x, h + 1.3 * s, z, 2.2 * s, seed, squash=0.8, n=8, rings=4)
    blob(bl, x + 1.1 * s, h + 0.4 * s, z - 0.6 * s, 1.5 * s, seed + 500, squash=0.85, n=8, rings=4)


def build_lamps():
    bz = builder('bronze', 'bronze'); lp = builder('lamps', 'lamp_e')
    # along the path (none inside the theatre now), round the fountain, at the passage's back entrance and at the
    # cavea's back corners
    posts = [(s * (PATH_W / 2 + 0.9), z) for z in (37.6, 61.0) for s in (-1, 1)] + [(s * 6.9, FOUNTAIN[1] + s2 * 4.0) for s in (-1, 1) for s2 in (-1, 1)]
    posts = [(x, z, 'post') for (x, z) in posts]
    # the theatre's own lamps ('theatre': the lighting step counts them with the outside)
    posts += [(s * (TH_GAP + 0.75), TH_C[1] + TH_RO + 0.9, 'theatre') for s in (-1, 1)]
    a = TH_A + math.radians(3.0)
    posts += [(s * (TH_RO + 0.7) * math.sin(a), TH_C[1] + (TH_RO + 0.7) * math.cos(a), 'theatre') for s in (-1, 1)]
    for (x, z, kind) in posts:
        y = gh(x, z)
        lathe(bz, x, z, [(y, 0.28), (y + 0.08, 0.28), (y + 0.12, 0.16), (y + 0.5, 0.09), (y + 3.0, 0.06), (y + 3.05, 0.10), (y + 3.12, 0.06)], n=12)
        lantern(bz, lp, x, y + 3.12, z, s=1.0)
        LIGHTS.append((kind, (x, y + 3.45, z), (1.0, 0.82, 0.58), 150, None))


def build_horizon():
    """Rolling hills around the grounds, 150 to 230 m out, their crests lifted by a slow noise; a dark tree line
    inside them is the far trees' job."""
    hb = builder('hills', 'hills', tile=20.0)
    cx, cz = 30.0, -8.0
    n = 72
    rings = [(150.0, 0.0), (175.0, None), (205.0, None), (235.0, 0.0)]
    def crest(a, k):
        return (10.0 + 8.0 * math.sin(3 * a + 1.0) + 5.0 * math.sin(7 * a + 2.0) + 3.0 * math.sin(13 * a)) * (1.0 if k == 1 else 1.3)
    pts = []
    for (r, y) in rings:
        row = []
        for i in range(n):
            a = 2 * math.pi * i / n
            yy = y if y is not None else crest(a, rings.index((r, y)))
            row.append(P(cx + r * math.cos(a), yy, cz + r * math.sin(a)))
        pts.append(row)
    for k in range(len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n
            hb.face([pts[k][i], pts[k][j], pts[k + 1][j], pts[k + 1][i]], D(0, 1, 0))


# ---------------------------------------------------------------- the web pieces, lights, export
def import_pieces():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=PIECES)
    return len([o for o in bpy.data.objects if o not in before and o.type == 'MESH'])


def add_lights():
    for (kind, (x, y, z), col, watts, size) in LIGHTS:
        ld = bpy.data.lights.new(kind, 'POINT'); ld.shadow_soft_size = 0.08
        ob = bpy.data.objects.new(kind, ld); ob.location = P(x, y, z)
        ld.energy = watts; ld.color = col
        bpy.context.scene.collection.objects.link(ob)
    sd = bpy.data.lights.new('Sun', 'SUN'); sd.energy = 6.0; sd.angle = math.radians(1.0); sd.color = (1.0, 0.95, 0.88)
    sun = bpy.data.objects.new('Sun', sd); bpy.context.scene.collection.objects.link(sun)
    d = Vector((-0.5, -0.35, -0.8)).normalized()
    sun.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    w = bpy.data.worlds.new('World'); bpy.context.scene.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes['Background']
    sky = nt.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'MULTIPLE_SCATTERING'; sky.sun_disc = False; sky.sun_elevation = math.radians(48); sky.sun_rotation = math.radians(200)
    nt.links.new(sky.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.6


def write_lights_json():
    out = [{'name': kind, 'type': 'POINT', 'campus_pos_m': [round(v, 3) for v in pos], 'campus_dir': [0, -1, 0], 'blender_watts': watts,
            'color_linear': [round(c, 3) for c in col], 'radius_m': 0.08, 'area_size_m': None} for (kind, pos, col, watts, size) in LIGHTS]
    with open(os.path.join(PIPE, 'lights.json'), 'w') as f:
        json.dump({'source': 'bl/exterior.py', 'units': 'metres, three.js campus axes (y up)', 'lights': out}, f, indent=1)


def write_theatre_layout(seats):
    x_out = (TH_RO + 0.3) * math.sin(TH_A)
    layout = {
        'source': 'bl/exterior.py', 'units': 'campus metres (x east, y up, z south); Unreal = (x*100, z*100, y*100)',
        'venue': 'forecourt',
        'rooms': [{'id': 'theatre', 'label': 'The Forecourt Theatre', 'x0': round(-max(x_out, 9.6), 2), 'x1': round(max(x_out, 9.6), 2),
                   'z0': round(PATH_Z0 - 0.05, 2), 'z1': round(TH_C[1] + TH_RO + 0.4, 2), 'floor_y': TH_Y, 'outdoor': True}],
        'entries': [{'what': 'from the museum steps', 'x': 0.0, 'y': TH_Y, 'z': round(PATH_Z0 + 0.4, 2)},
                    {'what': 'the passage through the cavea, from the grounds', 'x': 0.0, 'y': TH_Y, 'z': round(TH_C[1] + TH_RO + 0.3, 2)}],
        'speaker_spot': {'x': SPEAKER[0], 'y': round(STAGE_TOP, 3), 'z': SPEAKER[1], 'yaw': seat_yaw(0.0, 1.0)},
        'lectern': {'x': LECTERN[0], 'z': LECTERN[1]},
        'stage': {'centre': list(TH_C), 'radius': STAGE_R, 'back_z': STAGE_BACK, 'top_y': round(STAGE_TOP, 3)},
        'cavea': {'centre': list(TH_C), 'r0': TH_R0, 'r_back': TH_RO, 'tiers': TH_N, 'tier_depth': TH_D, 'tier_rise': TH_H,
                  'half_angle_deg': round(math.degrees(TH_A), 1), 'passage_half_width': TH_GAP,
                  'aisles_deg': [-round(math.degrees(TH_AISLE), 1), round(math.degrees(TH_AISLE), 1)], 'aisle_width': TH_AISLE_W},
        'screens': THEATRE.get('screens', []),
        'fountain': list(FOUNTAIN),
        'camera': {'eye': [0.0, round(TH_Y + TH_N * TH_H + 1.65, 2), round(TH_C[1] + TH_RO - 0.6, 2)], 'target': [0.0, 1.0, TH_C[1] - 1.0]},
        'seats': seats,
    }
    with open(os.path.join(PIPE, 'theatre_layout.json'), 'w') as f:
        json.dump(layout, f, indent=1)


def render(name, eye, target, fov=70):
    sc = bpy.context.scene
    cam = bpy.data.cameras.new('Cam' + name); cam.lens_unit = 'FOV'; cam.angle = math.radians(fov)
    co = bpy.data.objects.new('Cam' + name, cam); sc.collection.objects.link(co)
    co.location = P(*eye)
    co.rotation_euler = (P(*target) - P(*eye)).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = co
    sc.render.resolution_x = 960 if QUICK else 1280; sc.render.resolution_y = 600 if QUICK else 800; sc.render.resolution_percentage = 100
    sc.cycles.samples = 16 if QUICK else 64
    sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 88
    sc.render.filepath = os.path.join(OUT, 'preview_%s.jpg' % name)
    t = time.time(); bpy.ops.render.render(write_still=True); print('preview', name, 'in %.0f s' % (time.time() - t), flush=True)


def export_glb():
    for o in bpy.data.objects:
        if o.type == 'MESH':
            for m in o.data.materials:
                if m and m.name == 'glass': m.surface_render_method = 'BLENDED'
    obs = [o for o in bpy.data.objects if o.type == 'MESH' and not o.get('preview_only')]
    select_only(obs)
    fp = os.path.join(PIPE, 'Outside.glb')
    bpy.ops.export_scene.gltf(filepath=fp, export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
                              export_texcoords=True, export_normals=True, export_tangents=True, export_materials='EXPORT',
                              export_image_format='AUTO', export_vertex_color='NONE', export_lights=False, export_cameras=False)
    print('exported', fp, os.path.getsize(fp), 'bytes', flush=True)


def main():
    t0 = time.time()
    sc = L.reset()
    setup_materials()
    build_terrain()
    build_path()
    seats = build_theatre()
    build_shells()
    build_trees()
    build_lamps()
    build_horizon()
    pieces = import_pieces()
    for name, b in B.items():
        if b.count == 0: continue
        ob = b.finish()
        if name in ('trunks', 'far_trunks', 'fountain', 'bronze', 'lamps', 'hills', 'ground', 'meadow', 'th_balusters', 'th_urns'): smooth(ob, 50.0)
        if name in ('leaves', 'far_leaves'): smooth(ob, 89.0)
    add_lights()
    write_lights_json()
    write_theatre_layout(seats)
    obs = [o for o in sc.objects if o.type == 'MESH']
    print('objects', len(obs), 'web pieces', pieces, 'lights', len(LIGHTS), 'theatre seats', seats, 'tris ~', sum(len(o.data.polygons) * 2 for o in obs), 'built in %.0f s' % (time.time() - t0), flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'exterior.blend'))
    if RENDER:
        # the museum building (bl/museum.py's export) joins the previews, but not the Outside asset
        for o in bpy.data.objects:                       # the speaker's mark is never shown, as in the engine
            if o.name.startswith('spot__'): o.hide_render = True
        mg = os.path.join(SP, 'unreal', 'Pipeline', 'out', 'museum', 'Museum.glb')
        if os.path.exists(mg):
            before = set(bpy.data.objects)
            bpy.ops.import_scene.gltf(filepath=mg)
            for o in bpy.data.objects:
                if o not in before: o['preview_only'] = 1
        views = {'approach': ((-5.5, 1.6, 66.0), (0.5, 6.5, 12.0), 64), 'fountain': ((-6.0, 1.3, 58.0), (0.0, 2.5, 46.0), 72),
                 'side': ((-26.0, 1.6, 20.0), (0.0, 6.0, 0.0), 76), 'school': ((44.0, 1.6, 4.0), (30.0, 4.0, -3.0), 76),
                 'theatre': ((0.0, 3.6, 32.4), (0.0, 1.2, 19.0), 72), 'seats': ((-3.0, 0.9, 18.6), (2.0, 0.5, 30.0), 80),
                 'stage': ((5.5, 0.8, 27.6), (-1.0, 1.2, 19.5), 70), 'portico': ((0.0, 0.9, 13.2), (0.0, 0.5, 30.0), 80),
                 'wing': ((36.0, 1.7, -38.0), (18.0, 4.5, -22.0), 70), 'wing_n': ((14.0, 1.7, -46.0), (14.0, 4.0, -26.0), 76),
                 'cavea': ((-4.0, 1.0, 40.0), (-6.5, 1.3, 31.0), 66)}
        want = [a.split('=')[1].split(',') for a in sys.argv if a.startswith('--views=')]
        for name in (want[0] if want else views):
            eye, target, fov = views[name]
            render(name, eye, target, fov=fov)
    export_glb()
    print('done in %.0f s' % (time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
