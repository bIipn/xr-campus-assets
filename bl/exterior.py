"""The grounds, built for real: everything outside the museum that the Outside asset carries, in Blender (bpy) at
campus coordinates, for Unreal.

The terrain (a lawn that dips into a wildflower meadow in front of the museum's steps), a flagstone path from the
steps past a fountain into the grounds, trees along it and around the campus, bronze lamp posts, the horizon hills,
and the stone shells of the other buildings: the Wax Hall annex, the Reading Room, the two halls and the Workshop
School, in the same limestone order as the museum (pilasters, entablature, parapet). The school's east facade
pieces from the web (door frame, canopy, lettering, windows, mural, lamps, rooftop plant) and the Wax Hall's
'LIVING HISTORY' letters are imported from unreal/Pipeline/out/exterior/web_pieces.glb and kept.

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
from library import P, D, Builder, bar, prism, material, MATS, frange, select_only   # noqa: E402
import neo                                                       # noqa: E402
from neo import lathe, annulus, wall_with_door, run_boxes, entablature, pilaster, urn, tree, blob, lantern, smooth, ENT_H   # noqa: E402
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
PATH_Z1 = 64.0
FOUNTAIN = (0.0, 34.0)

# the other buildings' shells (campus metres, from the web layout), each with its own parapet height
SHELLS = {
    # each 15 cm outside the web building's own outer faces (WaxHall x +-8.70; the Reading Room's green
    # walls x -32.45..-11.55, z -13.45..7.45; the School z -13.40), so the ashlar reads and never z-fights
    'wax':     dict(x0=-8.85, x1=8.85, z0=-81.3, z1=-42.0, h=5.4),
    'library': dict(x0=-32.6, x1=-11.4, z0=-13.6, z1=7.6, h=7.9),
    'hallL':   dict(x0=-11.8, x1=-6.2, z0=-4.8, z1=-1.2, h=3.65),
    'hallR':   dict(x0=6.2, x1=11.8, z0=-4.8, z1=-1.2, h=3.65),
    'school':  dict(x0=11.8, x1=34.2, z0=-13.6, z1=7.2, h=4.3),
}
# openings in those shells: (shell, wall, u0, u1, h) - 'E' east wall x1, 'W' west wall x0 (u along z)
OPENINGS = [('library', 'E', -4.8, -1.2, 3.65), ('school', 'W', -4.8, -1.2, 3.65), ('school', 'E', -4.6, -1.4, 3.0),
            ('wax', 'S', -1.9, 1.9, 3.3)]
# web tree positions kept (parts/outdoor.js), minus the two that stood where the rotunda and forecourt now are
CAMPUS_TREES = [(9, -9.5), (9, -17), (9, -25), (9, -34), (9, 3.8), (16, 11.5), (24.5, 12.5), (-20, 12), (-28.5, 11), (27, -18.5),
                (19, -17.5), (14, -25), (-8.5, -20), (-9, -31), (-22, -18), (-30, -21)]
YARD_TREES = [(47.5, 23.4), (54, 23.8), (60.5, 23.2), (71.5, 23.6), (78, 23.2), (84.5, 23.6), (90, 22), (89.8, 15.5), (90, 8), (89.6, 1.2),
              (89.8, -5.5), (61.2, 11.6), (69.5, 1.6), (84.8, 7.4), (46.7, 8.4), (69.5, 16.6), (58.2, -6.2), (37.2, 6.4)]
# new: an allee either side of the path, and groves on the meadow
PATH_TREES = [(s * 8.5, z) for z in (24.0, 31.0, 39.0, 47.0, 55.0) for s in (-1, 1)] + \
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
def build_terrain():
    """An inner grid (2 m cells) over the campus with the forecourt bowl shaped into it, and a coarse flat apron out
    to 320 m. Cells in the bowl take the meadow material."""
    gr = builder('ground', 'grass', tile=3.0); md = builder('meadow', 'meadow', tile=3.0)
    X0, X1, Z0, Z1, C = -70.0, 130.0, -110.0, 90.0, 2.0
    nx, nz = int((X1 - X0) / C), int((Z1 - Z0) / C)
    for i in range(nx):
        for j in range(nz):
            xa, za = X0 + i * C, Z0 + j * C
            pts = [(xa, za), (xa + C, za), (xa + C, za + C), (xa, za + C)]
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
    """Flagstones from the foot of the steps to the far end of the grounds: a plaza at the steps, the walk, a round
    plaza with the fountain, and a gentle curve beyond it."""
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
    strip(PATH_Z0 - 0.05, PATH_Z0 + 3.2, 9.2)                   # the plaza at the foot of the steps
    strip(PATH_Z0 + 3.2, FOUNTAIN[1] - 7.0, PATH_W / 2)
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
            if name in ('hallL', 'hallR') and key in ('W', 'E'): continue
            if name == 'wax' and key == 'S': continue              # the wax hall's south wall is the museum's end wall
            ops = [o for o in OPENINGS if o[0] == name and o[1] == key]
            if ops:
                _n, _w, u0, u1, oh = ops[0]
                ux, uz = c[0] - a[0], c[1] - a[1]; Ln = math.hypot(ux, uz); ux, uz = ux / Ln, uz / Ln
                # u along the run from a; the opening's u0..u1 are campus z (walls E/W) or x (walls N/S)
                ua = (u0 - a[1]) * uz if key in ('E', 'W') else (u0 - a[0]) * ux
                ub = (u1 - a[1]) * uz if key in ('E', 'W') else (u1 - a[0]) * ux
                ua, ub = min(ua, ub), max(ua, ub)
                wall_with_door(ash, (a[0], -1.0, a[1]), (ux, 0, uz), (0, 1, 0), (out[0], 0, out[1]), 0.0, Ln, h + 1.0, ua, ub, oh + 1.0, solid=False)
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
        rf.box((x0 + x1) / 2, h - 0.06, (z0 + z1) / 2, x1 - x0, 0.12, z1 - z0, faces='Y')
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
        if -40 < x < 97 and -50 < z < 70: continue
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
    posts = [(s * (PATH_W / 2 + 0.9), z) for z in (22.0, 29.0, 45.0, 56.0) for s in (-1, 1)] + [(s * 6.9, FOUNTAIN[1] + s2 * 4.0) for s in (-1, 1) for s2 in (-1, 1)]
    for (x, z) in posts:
        y = gh(x, z)
        lathe(bz, x, z, [(y, 0.28), (y + 0.08, 0.28), (y + 0.12, 0.16), (y + 0.5, 0.09), (y + 3.0, 0.06), (y + 3.05, 0.10), (y + 3.12, 0.06)], n=12)
        lantern(bz, lp, x, y + 3.12, z, s=1.0)
        LIGHTS.append(('post', (x, y + 3.45, z), (1.0, 0.82, 0.58), 150, None))


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
    build_shells()
    build_trees()
    build_lamps()
    build_horizon()
    pieces = import_pieces()
    for name, b in B.items():
        if b.count == 0: continue
        ob = b.finish()
        if name in ('trunks', 'far_trunks', 'fountain', 'bronze', 'lamps', 'hills', 'ground', 'meadow'): smooth(ob, 50.0)
        if name in ('leaves', 'far_leaves'): smooth(ob, 89.0)
    add_lights()
    write_lights_json()
    obs = [o for o in sc.objects if o.type == 'MESH']
    print('objects', len(obs), 'web pieces', pieces, 'lights', len(LIGHTS), 'tris ~', sum(len(o.data.polygons) * 2 for o in obs), 'built in %.0f s' % (time.time() - t0), flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'exterior.blend'))
    if RENDER:
        # the museum building (bl/museum.py's export) joins the previews, but not the Outside asset
        mg = os.path.join(SP, 'unreal', 'Pipeline', 'out', 'museum', 'Museum.glb')
        if os.path.exists(mg):
            before = set(bpy.data.objects)
            bpy.ops.import_scene.gltf(filepath=mg)
            for o in bpy.data.objects:
                if o not in before: o['preview_only'] = 1
        views = {'approach': ((2.0, 0.9, 58.0), (0.0, 8.0, 12.0), 70), 'fountain': ((-6.0, 1.3, 44.0), (0.0, 2.5, 30.0), 72),
                 'side': ((-26.0, 1.6, 20.0), (0.0, 6.0, 0.0), 76), 'school': ((44.0, 1.6, 4.0), (30.0, 4.0, -3.0), 76)}
        want = [a.split('=')[1].split(',') for a in sys.argv if a.startswith('--views=')]
        for name in (want[0] if want else views):
            eye, target, fov = views[name]
            render(name, eye, target, fov=fov)
    export_glb()
    print('done in %.0f s' % (time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
