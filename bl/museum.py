"""The Museum, built for real: a neoclassical gallery hall in Blender (bpy) at campus coordinates, for Unreal.

What stays from the web campus: the plan (lobby z -6..0, three 12 x 12 m galleries to z = -42, the two halls at
x = +-6..12), every door at its old place and size, and the content - the framed exhibits, vitrines, title panel,
plaque, directory, door signs, posters and the hidden token - which are imported from
unreal/Pipeline/out/museum/web_pieces.glb exactly where the catalog (Data/Exhibits.json) expects them.

What is new: marble floors with verde borders, a dado and limestone walls, engaged Corinthian columns with gilt
capitals, a full entablature, coffered barrel vaults with glazed laylights down the crown, pedimented doorways,
statuary urns on pedestals, bronze sconces and torcheres, the orange exhibition banners, and at the front a
domed rotunda (coffered, an oculus) behind a six-column portico with steps down to the grounds.

Campus axes: x east, y up, z south.  Blender: X = x, Y = -z, Z = y.
Usage (Blender 5.2 or bpy 5.2.2):   python bl/museum.py [--quick] [--render]
Writes assets/museum/museum.blend, unreal/Pipeline/out/museum/Museum.glb (+ lights.json) and preview renders.
Then: blender -b --python unreal/Pipeline/blender/prepare_for_unreal.py -- Museum
"""
import json
import math
import os
import sys
import time

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import library as L                                              # noqa: E402
from library import P, D, Builder, bar, prism, poly_prism, bezier, material, MATS, frange, select_only   # noqa: E402
import neo                                                       # noqa: E402
from neo import lathe, annulus, face_uv, extrude_profile, arch_pts, wall_with_arch, wall_with_door, run_boxes, entablature, \
    column, capital, pilaster, coffered_flat, coffer_box, rosette_at, barrel_vault, lunette_pts, dome, urn, pedestal, \
    banner, torchere, sconce, lantern, smooth, ENT_H, DADO, DADO_H          # noqa: E402

SP = L.SP
OUT = os.path.join(SP, 'assets', 'museum')
PIPE = os.path.join(SP, 'unreal', 'Pipeline', 'out', 'museum')
PIECES = os.path.join(PIPE, 'web_pieces.glb')
QUICK = '--quick' in sys.argv
RENDER = '--render' in sys.argv
os.makedirs(OUT, exist_ok=True); os.makedirs(PIPE, exist_ok=True)

# ---------------------------------------------------------------- the plan (campus metres)
X0, X1 = -6.0, 6.0                # the hall's width
ZW = -42.0                        # the end wall, with the door to the Wax Hall
PARTS = (-6.0, -18.0, -30.0)      # partition centre lines (0.3 thick), each with a 3.2 x 3.1 door on the axis
GALS = ((-18.0, -6.0), (-30.0, -18.0), (-42.0, -30.0))
PT = 0.30                         # partition thickness
DOOR_W, DOOR_H = 3.2, 3.1
H_COL = 4.9                       # column height (floor to abacus)
H_ENT = H_COL + ENT_H             # 6.0: the vault springs here
VR = 8.223                        # the vault: a segmental arc through (+-6, 6.0) and (0, 8.6)
VCY = 8.6 - VR
WALL_T = 0.25                     # solid thickness given to the inner wall faces (Lumen wants closed rooms)
HALL_H = 3.4                      # the two side halls
HALL = ((-12.0, -6.0), (6.0, 12.0)); HZ0, HZ1 = -4.6, -1.4
# the halls' walls and ceiling start at the Reading Room's outer face (x -11.55): its door reveal fills the
# last 45 cm (bl/library.py), and two faces in one plane flicker. The floor still runs to -12.
HALL_WALLS = ((-11.55, -6.0), (6.0, 12.0))
SIDE_DOOR = (-4.2, -1.8)          # lobby -> halls, 2.4 x 3.1 at x = +-6
# the rotunda and the front
RC = (0.0, 5.8)                   # centre (x, z)
RI, RO = 5.0, 5.8                 # inner and outer radius
R_DRUM0, R_DRUM1 = H_ENT, 9.6     # the drum with the clerestory, then a cornice to the dome springing
R_DOME_Y = 9.6                    # the sphere's centre height; the coffered dome is its inside (radius RI)
DOME_K = 1.25                     # the outer dome is raised: an ellipsoid DOME_K times taller than it is wide
OCULUS = 15.0                     # degrees from the pole
LOBBY_ARCH = (3.2, 3.2)           # width, springing (apex 4.8) - the door between lobby and rotunda, at z = 0
FRONT_ARCH = (3.2, 3.6)           # the front door (apex 5.2) through the pronaos at z = 12.6
PRO = (-7.8, 7.8, 9.4, 12.6)      # the pronaos block x0, x1, z0, z1
STY_Z1 = 16.6                     # the stylobate (portico floor) runs from the pronaos face to here
PORT_COL = ((-7.25, 15.4), (-4.35, 15.4), (-1.45, 15.4), (1.45, 15.4), (4.35, 15.4), (7.25, 15.4), (-7.25, 13.5), (7.25, 13.5))
PORT_H = 6.8                      # portico column height; entablature to 7.9, pediment to 10.3
STEPS = 5; RISE = 0.15; TREAD = 0.30
FORECOURT_Y = -STEPS * RISE       # the grounds in front of the steps lie 0.75 m below the floor
ROOF_Y = 9.6                      # the gallery block's roof slab (the vault's apex is 8.6)


def ground_height(x, z):
    """The grounds: level with the floors everywhere except the forecourt bowl in front of the steps, which
    drops to FORECOURT_Y. Shared with bl/exterior.py so terrain, path and steps agree."""
    def smooth(t): t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)
    s = smooth((z - 12.4) / 3.0) * (1 - smooth((z - 62.0) / 14.0))
    w = 1 - smooth((abs(x) - 26.0) / 12.0)
    return FORECOURT_Y * s * w


# ---------------------------------------------------------------- materials
def setup_materials():
    material('marble_w', 'marblew_col', 'marblew_rgh', 'marblew_nrm', roughness=0.14)
    material('marble_b', 'marbleb_col', 'marbleb_rgh', 'marbleb_nrm', roughness=0.12)
    material('verde', 'verde_col', 'verde_rgh', 'verde_nrm', roughness=0.13)
    material('rosso', 'rosso_col', 'rosso_rgh', 'rosso_nrm', roughness=0.14)
    material('giallo', 'giallo_col', 'giallo_rgh', 'giallo_nrm', roughness=0.16)
    material('lime', 'lime_col', 'lime_rgh', 'lime_nrm', roughness=0.7)
    material('ashlar', 'ashlar_col', 'ashlar_rgh', 'ashlar_nrm', roughness=0.75)
    material('stone', 'marblew_col', 'marblew_rgh', 'marblew_nrm', roughness=0.3)       # columns, urns, pedestals
    material('gilt', color=(1.0, 0.78, 0.38, 1), roughness=0.32, metallic=1.0)
    material('bronze', color=(0.40, 0.26, 0.13, 1), roughness=0.42, metallic=1.0)
    material('dark', color=(0.05, 0.045, 0.04, 1), roughness=0.6)
    material('glass', color=(0.9, 0.95, 1.0, 1), roughness=0.05, alpha=0.12)
    material('laylight_e', color=(1, 1, 1, 1), emission=(0.93, 0.95, 1.0, 1), emission_strength=6.0)
    material('oculus_e', color=(1, 1, 1, 1), emission=(0.70, 0.84, 1.0, 1), emission_strength=9.0)
    material('lamp_e', color=(1, 1, 1, 1), emission=(1.0, 0.86, 0.62, 1), emission_strength=14.0)
    for key in ('main', 'g1', 'g2', 'g3'):
        material('banner_' + key, 'banner_%s_col' % key, 'banner_rgh', 'banner_nrm', roughness=0.92)
    material('frieze_portico', 'frieze_portico', 'lime_rgh', roughness=0.7)
    material('frieze_rotunda', 'frieze_rotunda', 'lime_rgh', roughness=0.7)
    material('roof', color=(0.36, 0.37, 0.38, 1), roughness=0.8)
    material('copper', color=(0.30, 0.45, 0.40, 1), roughness=0.5, metallic=0.6)       # the dome's weathered copper


# ---------------------------------------------------------------- builders shared across the rooms
B = {}
def builder(name, mat, tile=1.0, seg=0.0):
    if name not in B: B[name] = Builder(name, mat, tile=tile, lightmap=False, vcol=False, seg=seg)
    return B[name]

LIGHTS = []   # (kind, (x, y, z), colour, watts) -> Blender lights + lights.json


def slab(b, ax, bx, az, bz, y=0.0, nu=1, nv=1, up=True):
    o = P(ax, y, bz) if up else P(ax, y, az)
    du = P(bx, y, bz) - P(ax, y, bz)
    dv = (P(ax, y, az) - P(ax, y, bz)) if up else (P(ax, y, bz) - P(ax, y, az))
    b.grid(o, du, dv, Vector((0, 0, 1 if up else -1)), nu, nv)


# ---------------------------------------------------------------- floors
def build_floors():
    fw = builder('floor_light', 'marble_w', tile=2.4); fb = builder('floor_dark', 'marble_b', tile=2.4)
    fv = builder('floor_verde', 'verde', tile=2.0); fr = builder('floor_rosso', 'rosso', tile=2.0)
    BORD = 0.6
    # galleries and lobby: a cream field, a verde border along the walls, and down the axis a runner of
    # alternating cream and verde squares between verde bands
    for (za, zb) in list(GALS) + [(-6.0, 0.0)]:
        slab(fv, X0, X0 + BORD, za, zb, nv=4); slab(fv, X1 - BORD, X1, za, zb, nv=4)
        slab(fw, X0 + BORD, -1.8, za, zb, nu=2, nv=5); slab(fw, 1.8, X1 - BORD, za, zb, nu=2, nv=5)
        slab(fv, -1.8, -1.5, za, zb, nv=4); slab(fv, 1.5, 1.8, za, zb, nv=4)
        n = int(round((zb - za) / 0.75)); sz = (zb - za) / n
        for j in range(n):
            for i in range(4):
                xa = -1.5 + i * 0.75
                slab(fw if (i + j) % 2 == 0 else fb, xa, xa + 0.75, za + j * sz, za + (j + 1) * sz)
    # the halls: cream with a verde border
    for (xa, xb) in HALL:
        slab(fv, xa, xb, HZ0, HZ0 + 0.4); slab(fv, xa, xb, HZ1 - 0.4, HZ1)
        slab(fw, xa, xb, HZ0 + 0.4, HZ1 - 0.4, nu=3)
    # the rotunda: rings and eight verde spokes around a rosso centre
    cx, cz = RC
    annulus(fr, cx, cz, 0, 0.0, 1.3, 0, 2 * math.pi, n=32)
    annulus(fv, cx, cz, 0, 1.3, 1.55, 0, 2 * math.pi, n=32)
    for k in range(8):
        a0 = 2 * math.pi * k / 8; a1 = 2 * math.pi * (k + 1) / 8
        annulus(fw, cx, cz, 0, 1.55, 4.55, a0 + 0.045, a1 - 0.045, n=4)
        annulus(fv, cx, cz, 0, 1.55, 4.55, a1 - 0.045, a1 + 0.045, n=1)
    annulus(fv, cx, cz, 0, 4.55, RI, 0, 2 * math.pi, n=48)
    # the passages through the thick walls: lobby door (z 0 .. 0.8) and front door (z 10.8 .. 12.6)
    slab(fw, -1.6, 1.6, 0.0, RC[1] - RI + 0.01); slab(fw, -1.6, 1.6, RC[1] + RI - 0.01, PRO[3])
    # the stylobate (portico floor) and the steps down to the forecourt
    st = builder('stylobate', 'ashlar', tile=2.4, seg=2.0)
    st.box(0, -0.4, (PRO[3] + STY_Z1) / 2, 16.4, 0.8, STY_Z1 - PRO[3], faces='YxXZ')
    for k in range(1, STEPS):                       # four treads down; the forecourt itself is the last
        y = -RISE * k; z = STY_Z1 + TREAD * (k - 1)
        st.box(0, (y - 0.8) / 2, z + TREAD / 2, 16.4, 0.8 + y, TREAD, faces='YZxX')
    # cheek blocks beside the steps
    for s in (-1, 1):
        st.box(s * (8.2 + 0.45), -0.25, STY_Z1 + (STEPS - 1) * TREAD / 2, 0.9, 1.1, (STEPS - 1) * TREAD + 0.6)


# ---------------------------------------------------------------- walls and the order
def dado_run(a, c, out, tile=2.0):
    run_boxes(builder('dado', 'verde', tile=tile, seg=3.0), a, c, out, DADO)


def wall_face(b, a, c, out, y0, y1, nu=2, nv=2):
    """A plain wall surface from (x, z) a to c, facing `out`, between heights y0 and y1."""
    A0 = P(a[0], y0, a[1]); C0 = P(c[0], y0, c[1]); A1 = P(a[0], y1, a[1])
    b.grid(A0, C0 - A0, A1 - A0, D(out[0], 0, out[1]), nu, nv)


def gallery_walls():
    wl = builder('walls', 'lime', tile=3.0)
    bs = builder('columns', 'stone', tile=2.0); bc = builder('capitals', 'gilt'); bb = builder('bases', 'stone', tile=2.0)
    ent = builder('entablature', 'lime', tile=3.0); den = builder('dentils', 'lime', tile=3.0)
    gold = builder('gilt_trim', 'gilt')
    # long walls x = +-6 from the end wall to the lobby's back wall, above the dado
    for (x, out) in ((X0, (1, 0)), (X1, (-1, 0))):
        # from the end wall to the lobby partition; lobby() builds the lobby's own side walls, with the hall doors
        wall_face(wl, (x, ZW), (x, -6.0), out, DADO_H - 0.02, H_COL, nu=8, nv=2)
        dado_run((x, ZW), (x, -6.0), out)
        entablature(ent, den, (x, ZW), (x, 0.0), out, H_COL)
        # engaged columns: one each side of every partition and one at mid-gallery
        for (za, zb) in GALS:
            for z in (za + 0.55, (za + zb) / 2, zb - 0.55):
                column(bs, bc, bb, x + out[0] * 0.28, z, H_COL, r=0.32, flutes=20)
        # a gilt panel moulding around each exhibit bay, hung at the exhibits' height
        for z in frange(ZW + 3.0, 0.0, 6.0):
            if z > -6.0: continue
            px = x + out[0] * 0.04
            for (z0, z1, y0, y1) in ((z - 2.1, z + 2.1, 1.15, 1.15), (z - 2.1, z + 2.1, 4.35, 4.35), (z - 2.1, z - 2.1, 1.15, 4.35), (z + 2.1, z + 2.1, 1.15, 4.35)):
                bar(gold, (px, y0, z0), (px, y1, z1), 0.05, 0.035)
    # the end wall z = -42 with the Wax Hall door (3.2 x 3.1), facing +z into the gallery
    wall_with_door(wl, (X0, 0.0, ZW), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.0, X1 - X0, H_ENT, 6.0 - 1.6, 6.0 + 1.6, DOOR_H, solid=False)
    for (a, c) in (((X0, ZW), (-1.6, ZW)), ((1.6, ZW), (X1, ZW))):
        dado_run(a, c, (0, 1)); entablature(ent, den, a, c, (0, 1), H_COL)
    entablature(ent, den, (-1.6, ZW), (1.6, ZW), (0, 1), H_COL, dent=True)
    aedicule(ZW, (0, 1), face_offset=0.0)                       # against the wall itself, not a partition's face
    # the lunette above the end wall's entablature, up to the vault
    extrude_profile(wl, lunette_pts(VR, VCY, 6.0, H_ENT), (0.0, 0.0, ZW), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.0, back=False, sides=False)


def aedicule(z, out, face_offset=PT / 2):
    """The pedimented doorway on one face of a partition (or the end wall): flat pilasters either side, an
    architrave, the door sign's band, a cornice and a pediment with a gilt rosette in the tympanum."""
    bs = builder('aedicule', 'stone', tile=2.0); bc = builder('capitals', 'gilt'); bb = builder('bases', 'stone', tile=2.0)
    gold = builder('gilt_trim', 'gilt')
    zf = z + out[1] * face_offset
    for x in (-1.95, 1.95):
        pilaster(bs, bc, bb, (x, zf), out, 0.5, 4.35, depth=0.14)
    run_boxes(bs, (-2.25, zf), (2.25, zf), out, [(3.1, 3.3, 0.16), (3.3, 3.5, 0.20)])      # architrave over the door
    run_boxes(bs, (-2.25, zf), (2.25, zf), out, [(4.0, 4.1, 0.22), (4.1, 4.3, 0.30)])      # cornice over the sign band
    run_boxes(gold, (-1.55, zf), (1.55, zf), out, [(3.49, 3.52, 0.05), (3.98, 4.01, 0.05)])
    # pediment: raking cornices and the tympanum
    apex = 5.15; base = 4.3; hw = 2.45
    tym = builder('aedicule', 'stone', tile=2.0)
    extrude_profile(tym, [(-hw + 0.25, base), (hw - 0.25, base), (0, apex - 0.18)], (0, 0, zf), (1, 0, 0), (0, 1, 0), (0, 0, out[1]), 0.10)
    for s in (-1, 1):
        a = (s * hw, base - 0.02, zf + out[1] * 0.17); c = (0, apex, zf + out[1] * 0.17)
        bar(bs, a, c, 0.30, 0.16)
    rosette_at(gold, (0, base + 0.30, zf + out[1] * 0.11), D(1, 0, 0), D(0, 1, 0), D(0, 0, out[1]), 0.22)


def partitions():
    wl = builder('partitions', 'lime', tile=3.0)
    ent = builder('entablature', 'lime', tile=3.0); den = builder('dentils', 'lime', tile=3.0)
    for z in PARTS:
        z0, z1 = z - PT / 2, z + PT / 2
        # the wall itself: piers, lintel and lunette, as a solid PT thick
        wall_with_door(wl, (X0, 0.0, z0), (1, 0, 0), (0, 1, 0), (0, 0, 1), PT, X1 - X0, H_ENT, 6.0 - 1.6, 6.0 + 1.6, DOOR_H)
        extrude_profile(wl, lunette_pts(VR, VCY, 6.0, H_ENT), (0.0, 0.0, z0), (1, 0, 0), (0, 1, 0), (0, 0, 1), PT)
        for (zf, out) in ((z0, (0, -1)), (z1, (0, 1))):
            for (a, c) in (((X0, zf), (-1.6, zf)), ((1.6, zf), (X1, zf))):
                dado_run(a, c, out)
            entablature(ent, den, (X0, zf), (X1, zf), out, H_COL)
            aedicule(z, out)


def vaults():
    vb = builder('vault', 'lime', tile=3.0); gold = builder('gilt_trim', 'gilt'); ll = builder('laylight', 'laylight_e')
    for gi, (za, zb) in enumerate(GALS):
        z0, z1 = za + PT / 2, zb - PT / 2
        if za == ZW: z0 = ZW
        barrel_vault(vb, gold, ll, 0.0, VR, VCY, 6.0, z0, z1, 5, 5, rib=0.32, depth=0.26, inset=0.15, laylight=(2, (1, 2, 3)))
        # one area light per glazed coffer, just below the glass
        cd = ((z1 - z0) - 6 * 0.32) / 5
        for j in (1, 2, 3):
            zc = z0 + 0.32 + j * (cd + 0.32) + cd / 2
            LIGHTS.append(('laylight', (0.0, 8.6 + 0.26 - 0.05, zc), (0.93, 0.95, 1.0), 900, (2.2, cd - 0.3)))
        # banners either side of the axis at mid-gallery, hung from the vault on cables
        zm = (za + zb) / 2
        for s in (-1, 1):
            bf = builder('banner_g%d' % (gi + 1), 'banner_g%d' % (gi + 1))
            banner(bf, builder('bronze', 'bronze'), s * 3.5, 5.3, zm, w=1.2, h=3.0, facing='z')
            for dx in (-0.55, 0.55):
                xx = s * 3.5 + dx
                yv = VCY + math.sqrt(VR * VR - xx * xx)
                bar(builder('dark', 'dark'), (xx, 5.32, zm), (xx, yv, zm), 0.012)
        # sconces on the engaged columns, a bench and a pair of urns on pedestals at the partition piers
        for x_, out in ((X0, (1, 0)), (X1, (-1, 0))):
            for z in (za + 0.55, zm, zb - 0.55):
                sconce(builder('bronze', 'bronze'), builder('lamps', 'lamp_e'), x_ + out[0] * 0.60, 3.55, z, out)
                LIGHTS.append(('sconce', (x_ + out[0] * 0.78, 3.62, z), (1.0, 0.84, 0.62), 160, None))
        for s in (-1, 1):
            px, pz = s * 4.6, zb - 1.2
            pedestal(builder('pedestals', 'verde', tile=2.0), builder('stone', 'stone', tile=2.0), px, pz, 0.7, 1.1)
            urn(builder('urns', 'stone', tile=2.0), px, pz, 1.1, h=1.0, s=0.85)
        bench(2.6, zm)


def bench(x, z):
    b = builder('pedestals', 'verde', tile=2.0); t = builder('stone', 'stone', tile=2.0)
    for dz in (-0.7, 0.7): b.box(x, 0.2, z + dz, 0.5, 0.4, 0.16, seg=0)
    t.box(x, 0.44, z, 0.6, 0.08, 1.9, seg=0)


# ---------------------------------------------------------------- the lobby, the halls
def lobby():
    wl = builder('walls', 'lime', tile=3.0)
    ent = builder('entablature', 'lime', tile=3.0); den = builder('dentils', 'lime', tile=3.0)
    bs = builder('columns', 'stone', tile=2.0); bc = builder('capitals', 'gilt'); bb = builder('bases', 'stone', tile=2.0)
    gold = builder('gilt_trim', 'gilt')
    # side walls x = +-6 between z -6 and 0, with the 2.4 x 3.1 door to each hall
    for (x, out) in ((X0, (1, 0)), (X1, (-1, 0))):
        # door from SIDE_DOOR (z -4.2..-1.8): the wall's u runs from z = -6 toward 0
        wall_with_door(wl, (x, 0.0, -6.0), (0, 0, 1), (0, 1, 0), (out[0], 0, 0), 0.0, 6.0, H_COL, SIDE_DOOR[0] + 6.0, SIDE_DOOR[1] + 6.0, DOOR_H, solid=False)
        for (a, c) in (((x, -6.0), (x, SIDE_DOOR[0])), ((x, SIDE_DOOR[1]), (x, 0.0))):
            dado_run(a, c, out)
        entablature(ent, den, (x, -6.0), (x, 0.0), out, H_COL)
        for z in (-5.45, -0.55): column(bs, bc, bb, x + out[0] * 0.28, z, H_COL, r=0.32, flutes=20)
        # a moulded surround for the hall door, and the wing sign above it sits in a gilt frame
        run_boxes(bs, (x, SIDE_DOOR[0] - 0.2), (x, SIDE_DOOR[1] + 0.2), out, [(3.1, 3.3, 0.12), (3.9, 4.05, 0.16)])
        for z in (SIDE_DOOR[0] - 0.15, SIDE_DOOR[1] + 0.15): bs.box(x + out[0] * 0.06, 1.55, z, 0.12, 3.1, 0.14, seg=1.5)
    # the back wall z = 0: the arch into the rotunda, flanked by the title panel and the plaque. Its opening is
    # 5 cm wider all round than the drum's cut, which lines the passage from z = 0: the wall's own 25 cm of
    # thickness then steps back behind the archivolt instead of sharing the lining's planes (which flickered).
    w, sp = LOBBY_ARCH
    ZB = 0.0
    wall_with_arch(wl, (X0, 0.0, ZB), (1, 0, 0), (0, 1, 0), (0, 0, -1), 0.0, X1 - X0, H_COL, 6.0 - w / 2 - 0.05, 6.0 + w / 2 + 0.05, sp, solid=False)
    for (a, c) in (((X0, ZB), (-w / 2, ZB)), ((w / 2, ZB), (X1, ZB))):
        dado_run(a, c, (0, -1))
    entablature(ent, den, (X0, ZB), (X1, ZB), (0, -1), H_COL)
    archivolt((0.0, ZB), (0, -1), w, sp, bs, gold)
    # ceiling: flat, coffered, at the entablature's top
    coffered_flat(builder('ceiling', 'lime', tile=3.0), gold, X0, X1, -6.0, 0.0, H_ENT, 6, 3, rib=0.34, depth=0.26)
    # two chandeliers
    pd = builder('bronze', 'bronze'); pb = builder('lamps', 'lamp_e')
    for px in (-3.0, 3.0):
        chandelier(pd, pb, px, -3.0, H_ENT, 4.35)
        LIGHTS.append(('chandelier', (px, 4.55, -3.0), (1.0, 0.86, 0.68), 1500, None))


def archivolt(origin, out, w, spring, bs, gold, depth=0.12):
    """Mouldings around an arched opening at (x, z) origin (the arch's centre on the wall line), on a wall facing
    `out`: a ring of voussoir blocks `depth` proud of the wall with a gilt bead inside, a keystone and imposts."""
    ox, oz = origin
    R = w / 2
    n = 14
    O = D(out[0], 0, out[1])
    for i in range(n):
        a0 = math.pi * i / n; a1 = math.pi * (i + 1) / n
        for (rr0, rr1, dep, bld) in ((R + 0.02, R + 0.32, depth, bs), (R + 0.0, R + 0.06, depth * 0.4, gold)):
            def ring(a, r): return P(ox - r * math.cos(a), spring + r * math.sin(a), oz)
            p = [ring(a0, rr0) + O * dep, ring(a0, rr1) + O * dep, ring(a1, rr1) + O * dep, ring(a1, rr0) + O * dep]
            bld.face(p, O)
            am = (a0 + a1) / 2
            bld.face([ring(a0, rr0), ring(a1, rr0), p[3], p[0]], D(math.cos(am), -math.sin(am), 0))      # soffit
            bld.face([ring(a0, rr1), ring(a1, rr1), p[2], p[1]], D(-math.cos(am), math.sin(am), 0))      # extrados
    bs.box(ox + out[0] * (depth - 0.02), spring + R + 0.12, oz + out[1] * (depth - 0.02), 0.44, 0.52, 0.20, seg=0)
    for s_ in (-1, 1):
        bs.box(ox + s_ * (R + 0.18) + out[0] * (depth - 0.04), spring - 0.08, oz + out[1] * (depth - 0.04), 0.5, 0.16, 0.16, seg=0)


def chandelier(pd, pb, px, pz, ceil, hang):
    """library.chandelier, parametrised by the ceiling height and the body's hanging height."""
    prism(pd, px, ceil - 0.10, pz, 0.27, 0.10, n=12, r_top=0.20)
    y = hang + 0.66
    while y < ceil - 0.10 - 1e-6:
        h = min(0.5, ceil - 0.10 - y); prism(pd, px, y, pz, 0.035, h, n=8, cap_top=False, cap_bot=False); y += h
    L.turned(pd, px, hang, pz, 0.66, 0.30, n=12)
    prism(pd, px, hang - 0.19, pz, 0.13, 0.19, n=12, r_top=0.03)
    for (n, r, a_off, root_y, knee_y, cup_y, hoop) in ((6, 0.48, 0.0, 0.50, 0.34, 0.60, False), (10, 0.78, 0.31, 0.16, -0.04, 0.22, True)):
        for k in range(n):
            a = 2 * math.pi * k / n + a_off
            ca, sa = math.cos(a), math.sin(a)
            root = (px + 0.13 * ca, hang + root_y, pz + 0.13 * sa)
            knee = (px + r * 0.66 * ca, hang + knee_y, pz + r * 0.66 * sa)
            tip = (px + r * ca, hang + cup_y, pz + r * sa)
            bar(pd, root, knee, 0.038); bar(pd, knee, tip, 0.034)
            prism(pd, px + r * ca, hang + cup_y, pz + r * sa, 0.055, 0.05, n=8, r_top=0.034)
            pb.box(px + r * ca, hang + cup_y + 0.13, pz + r * sa, 0.05, 0.16, 0.05, seg=0)
        if hoop:
            for k in range(n):
                a0 = 2 * math.pi * k / n + a_off; a1 = 2 * math.pi * (k + 1) / n + a_off
                bar(pd, (px + r * math.cos(a0), hang + cup_y - 0.08, pz + r * math.sin(a0)), (px + r * math.cos(a1), hang + cup_y - 0.08, pz + r * math.sin(a1)), 0.028)


def halls():
    wl = builder('walls', 'lime', tile=3.0); gold = builder('gilt_trim', 'gilt')
    bs = builder('aedicule', 'stone', tile=2.0); bc = builder('capitals', 'gilt'); bb = builder('bases', 'stone', tile=2.0)
    for (xa, xb) in HALL_WALLS:
        for (z, out) in ((HZ0, (0, 1)), (HZ1, (0, -1))):
            wall_face(wl, (xa, z), (xb, z), out, DADO_H - 0.02, HALL_H, nu=3, nv=1)
            dado_run((xa, z), (xb, z), out)
            run_boxes(bs, (xa, z), (xb, z), out, [(HALL_H - 0.30, HALL_H - 0.22, 0.10), (HALL_H - 0.22, HALL_H - 0.12, 0.16), (HALL_H - 0.12, HALL_H, 0.22)])
            for x in (xa + 0.6, (xa + xb) / 2, xb - 0.6):
                pilaster(bs, bc, bb, (x, z), out, 0.36, HALL_H - 0.30, depth=0.10)
        coffered_flat(builder('ceiling', 'lime', tile=3.0), gold, xa, xb, HZ0, HZ1, HALL_H, 3, 2, rib=0.26, depth=0.18, inset=0.09)
        xm = (xa + xb) / 2
        for xl in (xm - 1.5, xm + 1.5):
            LIGHTS.append(('hall', (xl, HALL_H - 0.35, -3.0), (1.0, 0.88, 0.72), 300, None))
            lathe(builder('bronze', 'bronze'), xl, -3.0, [(HALL_H - 0.02, 0.0), (HALL_H - 0.02, 0.18), (HALL_H - 0.12, 0.16), (HALL_H - 0.14, 0.05), (HALL_H - 0.30, 0.04)], n=16, cap_top=False)
            lathe(builder('lamps', 'lamp_e'), xl, -3.0, [(HALL_H - 0.42, 0.0), (HALL_H - 0.42, 0.12), (HALL_H - 0.30, 0.13)], n=16, cap_top=False)


# ---------------------------------------------------------------- the rotunda
def cylinder_shell(name, mat, cx, cz, r0, r1, y0, y1, n=64, tile=3.0):
    """A closed ring wall (inner r0, outer r1) between y0 and y1, as its own mesh object: a boolean operand."""
    b = Builder(name, mat, tile=tile, lightmap=False, vcol=False)
    lathe(b, cx, cz, [(y0, r1), (y1, r1)], n=n, cap_top=False)
    lathe(b, cx, cz, [(y1, r0), (y0, r0)], n=n, cap_top=False)
    annulus(b, cx, cz, y1, r0, r1, 0, 2 * math.pi, n=n, up=True)
    annulus(b, cx, cz, y0, r0, r1, 0, 2 * math.pi, n=n, up=False)
    return b.finish()


def radial_cutter(b, cx, cz, phi, w, y0, y1, r_in, r_out, arch=False, spring=None):
    """A box (or round-topped slab) standing radially through the ring wall at azimuth phi, w wide."""
    ca, sa = math.cos(phi), math.sin(phi)
    origin = (cx + r_in * ca + w / 2 * sa, y0, cz + r_in * sa - w / 2 * ca)   # u runs along the wall (tangent), v up, N outward
    U = (-sa, 0, ca); V = (0, 1, 0); N = (ca, 0, sa)
    if arch:
        pts = [(0, 0), (w, 0)] + list(reversed(arch_pts(0, w, (spring or y1) - y0)))
        extrude_profile(b, pts, origin, U, V, N, r_out - r_in, centre=(w / 2, ((spring or y1) - y0) / 2))
    else:
        extrude_profile(b, [(0, 0), (w, 0), (w, y1 - y0), (0, y1 - y0)], origin, U, V, N, r_out - r_in)


def boolean_cut(wall, cutters):
    """Subtract each cutter object from the wall in turn (one operand per boolean is far more reliable than one
    joined operand with many parts), triangulate, and re-project the UVs."""
    for cutter in cutters:
        bpy.ops.object.select_all(action='DESELECT')
        wall.select_set(True); bpy.context.view_layer.objects.active = wall
        m = wall.modifiers.new('cut', 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.object = cutter; m.solver = 'EXACT'
        bpy.ops.object.modifier_apply(modifier='cut')
        bpy.data.objects.remove(cutter, do_unlink=True)
    import bmesh
    bm = bmesh.new(); bm.from_mesh(wall.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(wall.data); bm.free()
    box_uv(wall, 3.0)


def box_uv(ob, tile):
    """World-scale box projection (the same rule Builder uses) for every face of a mesh, e.g. after a boolean."""
    me = ob.data
    uv = me.uv_layers.active or me.uv_layers.new(name='uv')
    for poly in me.polygons:
        n = poly.normal; ax = max(range(3), key=lambda k: abs(n[k]))
        for li in poly.loop_indices:
            p = me.vertices[me.loops[li].vertex_index].co
            u, v = ((p.y, p.z) if ax == 0 else (p.x, p.z) if ax == 1 else (p.x, p.y))
            uv.data[li].uv = (u / tile, v / tile)


def rotunda():
    cx, cz = RC
    bs = builder('columns', 'stone', tile=2.0); bc = builder('capitals', 'gilt'); bb = builder('bases', 'stone', tile=2.0)
    ent = builder('entablature', 'lime', tile=3.0); den = builder('dentils', 'lime', tile=3.0); gold = builder('gilt_trim', 'gilt')
    # the ring wall, floor to the drum's top, then openings cut through it
    wall = cylinder_shell('rotunda_wall', 'lime', cx, cz, RI, RO, 0.0, R_DRUM1, n=96)
    cutters = []
    def cutter(phi, w, y0, y1, r_in, r_out, spring):
        b = Builder('cutter', 'lime')
        radial_cutter(b, cx, cz, phi, w, y0, y1, r_in, r_out, arch=True, spring=spring)
        cutters.append(b.finish())
    phi_n, phi_s = -math.pi / 2, math.pi / 2
    cutter(phi_n, LOBBY_ARCH[0], 0.0, LOBBY_ARCH[1] + LOBBY_ARCH[0] / 2, RI - 0.5, RO + 0.5, LOBBY_ARCH[1])
    cutter(phi_s, FRONT_ARCH[0], 0.0, FRONT_ARCH[1] + FRONT_ARCH[0] / 2, RI - 0.5, RO + 0.5, FRONT_ARCH[1])
    for phi in (0.0, math.pi):                                                   # east and west windows
        cutter(phi, 2.4, 1.0, 4.0 + 1.2, RI - 0.5, RO + 0.5, 4.0)
    for k in range(4):                                                           # diagonal niches, half the wall deep
        cutter(math.pi / 4 + k * math.pi / 2, 1.5, 0.9, 3.4 + 0.75, RI - 0.5, RI + 0.5, 3.4)
    for k in range(8):                                                           # the clerestory
        cutter(math.pi / 8 + k * math.pi / 4, 1.3, R_DRUM0 + 0.3, R_DRUM0 + 1.3 + 0.65, RI - 0.5, RO + 0.5, R_DRUM0 + 1.3)
    boolean_cut(wall, cutters)
    wall.data.materials.append(MATS['ashlar'])
    for poly in wall.data.polygons:
        c = poly.center; radial = Vector((c.x - cx, c.y + cz, 0.0)).normalized()
        if poly.normal.dot(radial) > 0.6: poly.material_index = 1
    # dado and entablature follow the ring
    n = 48
    for k in range(n):
        a0 = 2 * math.pi * k / n; a1 = 2 * math.pi * (k + 1) / n
        am = (a0 + a1) / 2
        gap = any(abs(((am - g + math.pi) % (2 * math.pi)) - math.pi) < hw for (g, hw) in ((phi_n, 0.33), (phi_s, 0.33), (0.0, 0.25), (math.pi, 0.25)))
        p0 = (cx + RI * math.cos(a0), cz + RI * math.sin(a0)); p1 = (cx + RI * math.cos(a1), cz + RI * math.sin(a1))
        out = (-math.cos(am), -math.sin(am))
        if not gap: dado_run(p0, p1, out)
        entablature(ent, den, p0, p1, out, H_COL, dent=(k % 2 == 0))
        # the drum's cornice under the dome
        run_boxes(ent, p0, p1, out, [(R_DRUM1 - 0.40, R_DRUM1 - 0.30, 0.12), (R_DRUM1 - 0.30, R_DRUM1 - 0.12, 0.22), (R_DRUM1 - 0.12, R_DRUM1 + 0.0, 0.30)], seg=3.0)
    # eight engaged columns between the openings
    for k in range(8):
        phi = math.pi / 8 + k * math.pi / 4
        column(bs, bc, bb, cx + (RI - 0.22) * math.cos(phi), cz + (RI - 0.22) * math.sin(phi), H_COL, r=0.33, flutes=20, a0=phi)
    # archivolts on the two doors (inside faces)
    archivolt((cx, cz - RI), (0, 1), LOBBY_ARCH[0], LOBBY_ARCH[1], builder('aedicule', 'stone', tile=2.0), gold, depth=0.42)
    archivolt((cx, cz + RI), (0, -1), FRONT_ARCH[0], FRONT_ARCH[1], builder('aedicule', 'stone', tile=2.0), gold, depth=0.42)
    # the frieze band carries the founding line in cut letters: a strip of faces on the frieze, uv along the ring
    fz = builder('frieze_rotunda', 'frieze_rotunda')
    # 3 cm proud of the frieze boxes: they stand on chords, whose middles reach 1 cm further in than their ends
    y0, y1 = H_COL + 0.49, H_COL + 0.78; rr = RI - 0.15
    for k in range(n):
        a0 = 2 * math.pi * k / n; a1 = 2 * math.pi * (k + 1) / n
        u0, u1 = k / n * 4.0, (k + 1) / n * 4.0
        face_uv(fz, [P(cx + rr * math.cos(a0), y0, cz + rr * math.sin(a0)), P(cx + rr * math.cos(a1), y0, cz + rr * math.sin(a1)),
                     P(cx + rr * math.cos(a1), y1, cz + rr * math.sin(a1)), P(cx + rr * math.cos(a0), y1, cz + rr * math.sin(a0))],
                D(-math.cos((a0 + a1) / 2), 0, -math.sin((a0 + a1) / 2)), [(u0, 0), (u1, 0), (u1, 1), (u0, 1)])
    # urns on pedestals before the four niches (a pedestal in the niche shared the sill's plane and flickered),
    # torcheres between the columns
    for k in range(4):
        phi = math.pi / 4 + k * math.pi / 2
        px, pz = cx + (RI - 0.42) * math.cos(phi), cz + (RI - 0.42) * math.sin(phi)
        pedestal(builder('pedestals', 'verde', tile=2.0), builder('stone', 'stone', tile=2.0), px, pz, 0.8, 0.92)
        urn(builder('urns', 'stone', tile=2.0), px, pz, 0.92, h=1.3, s=1.0)
    # pedestals before the east and west windows for the two marble statues (Pipeline/content/statues.json)
    for px in (-3.9, 3.9):
        pedestal(builder('pedestals', 'verde', tile=2.0), builder('stone', 'stone', tile=2.0), cx + px, cz, 0.9, 0.9)
    for phi in (-math.pi / 2 - 0.46, -math.pi / 2 + 0.46, math.pi / 2 - 0.46, math.pi / 2 + 0.46):
        tx, tz = cx + (RI - 0.9) * math.cos(phi), cz + (RI - 0.9) * math.sin(phi)
        torchere(builder('bronze', 'bronze'), builder('lamps', 'lamp_e'), tx, tz, h=2.3)
        LIGHTS.append(('torchere', (tx, 2.45, tz), (1.0, 0.84, 0.62), 400, None))
    # the dome and its oculus
    db = builder('dome', 'lime', tile=3.0); gl = builder('oculus', 'oculus_e')
    yo, ro = dome(db, gold, gl, cx, R_DOME_Y, cz, RI, 5, 24, 22.0, 86.0, rib_deg=2.2, depth=0.24, inset_deg=1.0, oculus_psi=OCULUS)
    LIGHTS.append(('oculus', (cx, yo - 0.3, cz), (0.80, 0.88, 1.0), 9000, (2 * ro, 2 * ro)))
    # a ring of flat quads closes the gap between the drum top and the dome's rim (the sphere's equator sits at R_DOME_Y)
    for k in range(48):
        a0 = 2 * math.pi * k / 48; a1 = 2 * math.pi * (k + 1) / 48
        db.face([P(cx + RI * math.cos(a0), R_DRUM1, cz + RI * math.sin(a0)), P(cx + RI * math.cos(a1), R_DRUM1, cz + RI * math.sin(a1)),
                 P(cx + RI * math.cos(a1), R_DOME_Y + RI * math.cos(math.radians(86.0)), cz + RI * math.sin(a1)), P(cx + RI * math.cos(a0), R_DOME_Y + RI * math.cos(math.radians(86.0)), cz + RI * math.sin(a0))],
                D(-math.cos((a0 + a1) / 2), 0, -math.sin((a0 + a1) / 2)))
    # glass in the windows and the clerestory
    gw = builder('glass', 'glass')
    for (phi, w, y0, y1) in [(0.0, 2.4, 1.0, 5.2), (math.pi, 2.4, 1.0, 5.2)] + [(math.pi / 8 + k * math.pi / 4, 1.3, R_DRUM0 + 0.3, R_DRUM0 + 1.95) for k in range(8)]:
        ca, sa = math.cos(phi), math.sin(phi); r = (RI + RO) / 2
        c = (cx + r * ca, cz + r * sa)
        gw.face([P(c[0] - w / 2 * sa, y0, c[1] + w / 2 * ca), P(c[0] + w / 2 * sa, y0, c[1] - w / 2 * ca), P(c[0] + w / 2 * sa, y1, c[1] - w / 2 * ca), P(c[0] - w / 2 * sa, y1, c[1] + w / 2 * ca)], D(-ca, 0, -sa))
    return wall


# ---------------------------------------------------------------- the front: pronaos, portico, doors, lanterns
def front():
    x0, x1, z0, z1 = PRO
    cx, cz = RC
    bs = builder('columns', 'stone', tile=2.0); bc = builder('capitals', 'gilt'); bb = builder('bases', 'stone', tile=2.0)
    ash = builder('exterior', 'ashlar', tile=2.4); ent = builder('ext_entablature', 'lime', tile=3.0); den = builder('dentils', 'lime', tile=3.0)
    gold = builder('gilt_trim', 'gilt'); bz = builder('bronze', 'bronze')
    H1 = PORT_H + 1.1                        # top of the entablature all round the pronaos and the portico
    # the pronaos block: a solid with the front door passage cut by leaving it out of the boxes
    w, sp = FRONT_ARCH
    # front face z = z1 (facing +z): piers and the spandrel over the arch
    wall_with_arch(ash, (x0, -1.0, z1), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.02, x1 - x0, H1 + 1.0, (x1 - x0) / 2 - w / 2, (x1 - x0) / 2 + w / 2, sp + 1.0)
    # sides and the top, and the back faces beside the rotunda (the drum passes through this block)
    ash.box(x0 + 0.01, (H1 - 1.0) / 2, (z0 + z1) / 2, 0.02, H1 + 1.0, z1 - z0, faces='x', seg=3.0)
    ash.box(x1 - 0.01, (H1 - 1.0) / 2, (z0 + z1) / 2, 0.02, H1 + 1.0, z1 - z0, faces='X', seg=3.0)
    # the back face and the top stop at the drum (the rotunda's inside must stay open)
    xe = math.sqrt(RO * RO - (z0 - cz) ** 2)
    for (xa, xb) in ((x0, -xe), (xe, x1)):
        ash.box((xa + xb) / 2, (H1 - 1.0) / 2, z0 + 0.01, xb - xa, H1 + 1.0, 0.02, faces='z', seg=3.0)
    cell = 0.4
    for xa in frange(x0, x1 - 1e-6, cell):
        for za in frange(z0, z1 - 1e-6, cell):
            corners = [(xa, za), (xa + cell, za), (xa, za + cell), (xa + cell, za + cell)]
            if all(math.hypot(px - cx, pz - cz) >= RO - 0.1 for (px, pz) in corners):
                ash.face([P(xa, H1, za), P(xa + cell, H1, za), P(xa + cell, H1, za + cell), P(xa, H1, za + cell)], D(0, 1, 0))
    # the passage through the pronaos: jambs, and the arched soffit from the drum's outer face (z = cz + RO; the
    # drum's own cut lines the passage from RI to RO, and two linings in one plane flicker) to z1
    pz0 = cz + RO
    for s in (-1, 1):
        ash.box(s * w / 2, (sp + 1.0) / 2 - 0.5, (pz0 + z1) / 2, 0.02, sp + 1.0, z1 - pz0, faces=('x' if s > 0 else 'X'), seg=2.0)
    arc = arch_pts(-w / 2, w / 2, sp, 16)
    for i in range(len(arc) - 1):
        a, b_ = arc[i], arc[i + 1]
        ash.face([P(a[0], a[1], pz0), P(b_[0], b_[1], pz0), P(b_[0], b_[1], z1), P(a[0], a[1], z1)], D(-(a[0] + b_[0]) / 2, -(a[1] + b_[1] - 2 * sp) / 2, 0).normalized())
    archivolt((0.0, z1), (0, 1), w, sp, builder('aedicule', 'stone', tile=2.0), gold)
    # the doors: two bronze leaves swung open into the passage (78 degrees), and a fanlight in the arch
    for s_ in (-1, 1):
        hx, hz = s_ * (w / 2 - 0.02), z1 - 0.3                     # the hinge
        leaf_w = w / 2 - 0.05
        ang = math.radians(78)
        dxl, dzl = -s_ * math.cos(ang), -math.sin(ang)             # the leaf's direction from the hinge
        bz.box(hx + dxl * leaf_w / 2, sp / 2, hz + dzl * leaf_w / 2, leaf_w, sp - 0.04, 0.08, ry=math.atan2(-dzl, dxl))
        for yy in (0.9, 2.3): bz.box(hx + dxl * leaf_w / 2, yy, hz + dzl * leaf_w / 2 + 0 * dxl, leaf_w - 0.3, 0.9, 0.11, ry=math.atan2(-dzl, dxl), seg=0)
    fan = builder('glass', 'glass')
    arc = arch_pts(-w / 2, w / 2, sp, 16)
    for i in range(len(arc) - 1):
        fan.face([P(0, sp, z1 - 0.3), P(arc[i][0], arc[i][1], z1 - 0.3), P(arc[i + 1][0], arc[i + 1][1], z1 - 0.3)], D(0, 0, 1))
    for i in range(1, 8, 2):
        a = math.pi * i / 8
        bar(bz, (0, sp, z1 - 0.3), (-w / 2 * math.cos(a), sp + w / 2 * math.sin(a), z1 - 0.3), 0.05)
    bar(bz, (-w / 2, sp, z1 - 0.3), (w / 2, sp, z1 - 0.3), 0.08, 0.14)
    # the portico: stylobate already laid; columns, entablature on three sides, pediment on the front
    for (px, pz) in PORT_COL:
        column(bs, bc, bb, px, pz, PORT_H, r=0.45, flutes=20)
    ZF = PORT_COL[0][1]
    for (a, c, out) in (((x0 - 0.4, ZF + 0.45), (x1 + 0.4, ZF + 0.45), (0, 1)), ((x0 - 0.4, ZF + 0.45), (x0 - 0.4, z1), (-1, 0)), ((x1 + 0.4, z1), (x1 + 0.4, ZF + 0.45), (1, 0))):
        entablature(ent, den, a, c, out, PORT_H)
    # the frieze band on the front carries the name
    fz = builder('frieze_portico', 'frieze_portico')
    y0, y1 = PORT_H + 0.49, PORT_H + 0.78; zf = ZF + 0.45 + 0.125
    face_uv(fz, [P(x0 - 0.4, y0, zf), P(x1 + 0.4, y0, zf), P(x1 + 0.4, y1, zf), P(x0 - 0.4, y1, zf)], D(0, 0, 1), [(0, 0), (1, 0), (1, 1), (0, 1)])
    # the entablature's underside (soffit) between the columns and the wall, coffered
    coffered_flat(builder('ext_ceiling', 'lime', tile=3.0), gold, x0 - 0.4, x1 + 0.4, z1, ZF + 0.45, PORT_H + 0.0, 8, 2, rib=0.34, depth=0.22)
    # pediment: tympanum (recessed), raking cornices, and the roof behind it
    base = H1; apex = H1 + 2.4; hw = (x1 - x0) / 2 + 0.4
    tym = builder('exterior', 'ashlar', tile=2.4)
    extrude_profile(tym, [(-hw, base), (hw, base), (0, apex)], (0, 0, ZF + 0.45 + 0.10), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.02)
    for s in (-1, 1):
        bar(ent, (s * (hw + 0.1), base - 0.02, ZF + 0.45 + 0.22), (0, apex + 0.12, ZF + 0.45 + 0.22), 0.44, 0.30)
    # a gilt emblem in the tympanum
    rosette_at(gold, (0, base + 0.9, ZF + 0.45 + 0.13), D(1, 0, 0), D(0, 1, 0), D(0, 0, 1), 0.55)
    # the pitched roof from the pediment back to the pronaos (a slab on each slope)
    rf = builder('roof', 'roof', tile=2.0)
    for s in (-1, 1):
        rf.face([P(s * hw, base, ZF + 0.45), P(0, apex, ZF + 0.45), P(0, apex, z1 - 0.2), P(s * hw, base, z1 - 0.2)], D(s, 0.6, 0))
    # lanterns beside the door, and the two campus banners between the columns
    for s in (-1, 1):
        lantern(bz, builder('lamps', 'lamp_e'), s * (w / 2 + 0.75), 2.6, z1 + 0.25, s=1.1)
        LIGHTS.append(('lantern', (s * (w / 2 + 0.75), 2.95, z1 + 0.25), (1.0, 0.80, 0.55), 200, None))
        bf = builder('banner_main', 'banner_main')
        banner(bf, bz, s * 2.9, PORT_H - 0.05, ZF + 0.05, w=1.5, h=3.9, facing='z')


# ---------------------------------------------------------------- the gallery block seen from outside
def exterior_shell():
    ash = builder('exterior', 'ashlar', tile=2.4); ent = builder('ext_entablature', 'lime', tile=3.0); den = builder('dentils', 'lime', tile=3.0)
    rf = builder('roof', 'roof', tile=2.0); cop = builder('copper', 'copper', tile=2.0); gl = builder('glass', 'glass')
    bs = builder('columns', 'stone', tile=2.0); bc = builder('capitals', 'gilt'); bb = builder('bases', 'stone', tile=2.0)
    cx, cz = RC
    XO0, XO1, ZO = X0 - 0.2, X1 + 0.2, ZW - 0.2
    H = ROOF_Y
    # the four outer walls of the gallery block, from below grade to the roof; the long walls open where the
    # halls pass through them (z -4.8..-1.2, 3.65 high), and the plinth course stops either side of that
    for (a, c, out) in (((XO0, 0.2), (XO0, ZO), (-1, 0)), ((XO1, ZO), (XO1, 0.2), (1, 0)), ((XO0, ZO), (XO1, ZO), (0, -1))):
        if out[0] != 0:
            ux, uz = 0.0, (c[1] - a[1]) / abs(c[1] - a[1])
            ua, ub = sorted(((-4.8 - a[1]) * uz, (-1.2 - a[1]) * uz))
            wall_with_door(ash, (a[0], -1.0, a[1]), (0, 0, uz), (0, 1, 0), (out[0], 0, 0), 0.0, abs(c[1] - a[1]), H + 1.0, ua, ub, 3.65 + 1.0, solid=False)
            for (za, zb) in ((0.2, -1.2), (-4.8, ZO)):
                run_boxes(ash, (a[0], za), (a[0], zb), out, [(-1.0, 0.6, 0.12), (0.6, 0.7, 0.16)], seg=3.0)
        else:
            # the north wall: the Wax Hall door (3.2 x 3.1 on the axis) goes through it too
            wall_with_door(ash, (a[0], -1.0, a[1]), (1, 0, 0), (0, 1, 0), (0, 0, -1), 0.0, c[0] - a[0], H + 1.0, -a[0] - 1.6, -a[0] + 1.6, DOOR_H + 1.0, solid=False)
            for (xa, xb) in ((a[0], -1.6), (1.6, c[0])):
                run_boxes(ash, (xa, a[1]), (xb, a[1]), out, [(-1.0, 0.6, 0.12), (0.6, 0.7, 0.16)], seg=3.0)   # plinth course
        entablature(ent, den, a, c, out, H - ENT_H - 0.9)
        run_boxes(ash, a, c, out, [(H - 0.9, H + 0.6, 0.0 + 0.02)], seg=3.0)                           # parapet face
        # pilasters every 6 m between the windows... the block has no windows: pilasters mark the bays
        ux, uz = c[0] - a[0], c[1] - a[1]; Ln = math.hypot(ux, uz); ux, uz = ux / Ln, uz / Ln
        # every 6 m along the long walls; the north wall's four flank its door
        spots = [min(max(s_, 0.6), Ln - 0.6) for s_ in frange(0.0, Ln + 1e-6, 6.0)] if out[0] != 0 else [0.6, 3.3, Ln - 3.3, Ln - 0.6]
        for sc in spots:
            pilaster(ash, ent, ash, (a[0] + ux * sc, a[1] + uz * sc), out, 0.8, H - ENT_H - 0.9, depth=0.22)
    # the south face beside the rotunda (x beyond the drum), facing +z
    for (xa, xb) in ((XO0, -RO + 0.2), (RO - 0.2, XO1)):
        wall_face(ash, (xa, 0.2), (xb, 0.2), (0, 1), -1.0, H, nu=2, nv=3)
        entablature(ent, den, (xa, 0.2), (xb, 0.2), (0, 1), H - ENT_H - 0.9)
    # roof slab, parapet, and the three raised skylights over each gallery's laylights
    rf.box(0, H + 0.1, (ZO + 0.2) / 2, XO1 - XO0, 0.2, 0.2 - ZO, faces='Y')
    ash.box(0, H + 0.4, (ZO + 0.2) / 2, XO1 - XO0 + 0.1, 0.6, 0.2 - ZO + 0.1, faces='xXzZY')
    for (za, zb) in GALS:
        z0, z1 = za + PT / 2, zb - PT / 2
        cd = ((z1 - z0) - 6 * 0.32) / 5
        for j in (1, 2, 3):
            zc = z0 + 0.32 + j * (cd + 0.32) + cd / 2
            ash.box(0, H + 0.45, zc, 2.8, 0.5, cd + 0.2, faces='xXzZ')
            gl.face([P(-1.3, H + 0.72, zc - cd / 2), P(1.3, H + 0.72, zc - cd / 2), P(1.3, H + 0.72, zc + cd / 2), P(-1.3, H + 0.72, zc + cd / 2)], D(0, 1, 0))
    # the rotunda outside: the drum with pilasters, a cornice, stepped rings and the copper dome with a lantern
    drum = builder('exterior', 'ashlar', tile=2.4)
    lathe(drum, cx, cz, [(-1.0, RO), (0.0, RO)], n=96, cap_top=False)      # the drum itself is the rotunda wall's outside
    # (the drum's north side stands inside the gallery block and its south side inside the pronaos: no mouldings
    # there, and none across the two doors, where a plinth would be a kerb in the passage)
    def hidden(x, z): return z < 0.3 or (z > PRO[2] and abs(x) < PRO[1])
    n = 48
    for k in range(n):
        a0 = 2 * math.pi * k / n; a1 = 2 * math.pi * (k + 1) / n; am = (a0 + a1) / 2
        p0 = (cx + RO * math.cos(a0), cz + RO * math.sin(a0)); p1 = (cx + RO * math.cos(a1), cz + RO * math.sin(a1))
        out = (math.cos(am), math.sin(am))
        mx, mz = cx + RO * math.cos(am), cz + RO * math.sin(am)
        if hidden(mx, mz): continue
        run_boxes(ash, p0, p1, out, [(-1.0, 0.6, 0.12), (0.6, 0.7, 0.16)], seg=3.0)
        entablature(ent, den, p0, p1, out, R_DRUM1 - 0.5 - ENT_H, dent=(k % 2 == 0))
    for k in range(n):      # the cornice under the dome runs all the way round (it clears both blocks)
        a0 = 2 * math.pi * k / n; a1 = 2 * math.pi * (k + 1) / n; am = (a0 + a1) / 2
        p0 = (cx + RO * math.cos(a0), cz + RO * math.sin(a0)); p1 = (cx + RO * math.cos(a1), cz + RO * math.sin(a1))
        run_boxes(ent, p0, p1, (math.cos(am), math.sin(am)), [(R_DRUM1 - 0.5, R_DRUM1 - 0.2, 0.30), (R_DRUM1 - 0.2, R_DRUM1 + 0.1, 0.50)], seg=3.0)
    for k in range(16):
        phi = k * math.pi / 8 + math.pi / 16
        px, pz = cx + RO * math.cos(phi), cz + RO * math.sin(phi)
        if hidden(px, pz): continue
        pilaster(drum, ent, drum, (px, pz), (math.cos(phi), math.sin(phi)), 0.7, R_DRUM1 - 0.5 - ENT_H, depth=0.2)
    # stepped rings then the dome: the outer sphere, radius RO about the same centre, from the equator to the lantern
    DY = R_DRUM1 + 0.4
    lathe(drum, cx, cz, [(R_DRUM1, RO + 0.5), (R_DRUM1 + 0.4, RO + 0.5), (R_DRUM1 + 0.4, RO + 0.2), (DY + 0.2, RO + 0.2), (DY + 0.2, RO + 0.0)], n=96, cap_top=False)
    def dome_pt(ps, dr=0.0): return (DY + DOME_K * (RO + dr) * math.cos(ps), (RO + dr) * math.sin(ps))
    prof = [dome_pt(math.radians(90 - 74 * i / 12)) for i in range(13)]
    lathe(cop, cx, cz, prof, n=96, cap_top=False)
    # ribs down the copper
    for k in range(24):
        phi = 2 * math.pi * k / 24
        pts = [dome_pt(math.radians(90 - 74 * i / 12), 0.06) for i in range(13)]
        for i in range(12):
            a = (cx + pts[i][1] * math.cos(phi), pts[i][0], cz + pts[i][1] * math.sin(phi)); c = (cx + pts[i + 1][1] * math.cos(phi), pts[i + 1][0], cz + pts[i + 1][1] * math.sin(phi))
            bar(cop, a, c, 0.12, 0.10)
    # the lantern over the oculus: a ring of eight small columns, an entablature and a little dome with a finial
    ly = DY + DOME_K * RO * math.cos(math.radians(16)); lr = RO * math.sin(math.radians(16))
    lathe(drum, cx, cz, [(ly - 0.1, lr + 0.4), (ly + 0.3, lr + 0.4), (ly + 0.3, lr + 0.2)], n=32)
    for k in range(8):
        phi = 2 * math.pi * k / 8
        column(bs, bc, bb, cx + (lr + 0.05) * math.cos(phi), cz + (lr + 0.05) * math.sin(phi), 2.2, r=0.14, flutes=16, plinth=False, y_base=ly + 0.3)
    lathe(drum, cx, cz, [(ly + 2.5, lr + 0.5), (ly + 2.9, lr + 0.5), (ly + 2.9, lr + 0.2)], n=32)
    prof = [(ly + 2.9 + (lr + 0.2) * math.cos(math.radians(90 - 90 * i / 8)), (lr + 0.2) * math.sin(math.radians(90 - 90 * i / 8))) for i in range(9)]
    lathe(cop, cx, cz, prof, n=32, cap_top=False)
    lathe(builder('gilt_trim', 'gilt'), cx, cz, [(ly + 2.9 + lr + 0.2, 0.08), (ly + 2.9 + lr + 0.6, 0.05), (ly + 2.9 + lr + 1.0, 0.16), (ly + 2.9 + lr + 1.3, 0.0)], n=12)
    gl_l = builder('glass', 'glass')
    lathe(gl_l, cx, cz, [(ly + 0.3, lr - 0.02), (ly + 2.5, lr - 0.02)], n=32, cap_top=False)


# ---------------------------------------------------------------- the content from the web campus
MOVES = {
    'M_Material_13': (-3.8, 0, -0.03), 'M_Material_14': (-3.8, 0, -0.03),     # title panel to the left of the arch
    'M_Material_15': (0, 0, -0.03),                                           # plaque
    'M_Material_88': (0, 0, 0.03), 'M_Material_89': (0, 0, 0.03), 'M_Material_90': (0, 0, 0.03),   # off the end wall
    'M_Material_74': (0.03, 0, 0), 'M_Material_75': (-0.03, 0, 0),           # wing signs off the lobby side walls
    'M_Material_80': (0, 0, 0.03), 'M_Material_86': (0, 0, 0.03), 'M_Material_81': (0, 0, -0.03), 'M_Material_87': (0, 0, -0.03),
}


def import_pieces():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=PIECES)
    new = [o for o in bpy.data.objects if o not in before]
    count = 0
    for o in new:
        if o.type != 'MESH':
            continue
        base = o.name.split('.')[0]
        mv = MOVES.get(base)
        if mv:
            o.location += D(*mv)
        count += 1
    # the bench slab the web left floating gets its supports
    return count


# ---------------------------------------------------------------- lights, renders, export
def add_lights():
    for (kind, (x, y, z), col, watts, size) in LIGHTS:
        if size:
            ld = bpy.data.lights.new(kind, 'AREA'); ld.shape = 'RECTANGLE'; ld.size, ld.size_y = size
            ob = bpy.data.objects.new(kind, ld); ob.location = P(x, y, z); ob.rotation_euler = (0, 0, 0)   # -Z down
        else:
            ld = bpy.data.lights.new(kind, 'POINT'); ld.shadow_soft_size = 0.06
            ob = bpy.data.objects.new(kind, ld); ob.location = P(x, y, z)
        ld.energy = watts; ld.color = col
        bpy.context.scene.collection.objects.link(ob)
    sd = bpy.data.lights.new('Sun', 'SUN'); sd.energy = 8.0; sd.angle = math.radians(1.0); sd.color = (1.0, 0.95, 0.88)
    sun = bpy.data.objects.new('Sun', sd); bpy.context.scene.collection.objects.link(sun)
    d = Vector((-0.5, -0.35, -0.8)).normalized()
    sun.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    w = bpy.data.worlds.new('World'); bpy.context.scene.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes['Background']
    sky = nt.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'MULTIPLE_SCATTERING'; sky.sun_disc = False; sky.sun_elevation = math.radians(48); sky.sun_rotation = math.radians(200)
    nt.links.new(sky.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.6


def write_lights_json():
    out = []
    for (kind, (x, y, z), col, watts, size) in LIGHTS:
        out.append({'name': kind, 'type': 'AREA' if size else 'POINT', 'campus_pos_m': [round(x, 3), round(y, 3), round(z, 3)],
                    'campus_dir': [0, -1, 0], 'blender_watts': watts, 'color_linear': [round(c, 3) for c in col],
                    'radius_m': 0.06, 'area_size_m': [round(size[0], 3), round(size[1], 3)] if size else None})
    with open(os.path.join(PIPE, 'lights.json'), 'w') as f:
        json.dump({'source': 'bl/museum.py', 'units': 'metres, three.js campus axes (y up)', 'lights': out}, f, indent=1)


def render(name, eye, target, fov=70):
    sc = bpy.context.scene
    cam = bpy.data.cameras.new('Cam' + name); cam.lens_unit = 'FOV'; cam.angle = math.radians(fov)
    co = bpy.data.objects.new('Cam' + name, cam); sc.collection.objects.link(co)
    co.location = P(*eye)
    d = P(*target) - P(*eye)
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
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
    obs = [o for o in bpy.data.objects if o.type == 'MESH']
    select_only(obs)
    fp = os.path.join(PIPE, 'Museum.glb')
    bpy.ops.export_scene.gltf(filepath=fp, export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
                              export_texcoords=True, export_normals=True, export_tangents=True, export_materials='EXPORT',
                              export_image_format='AUTO', export_vertex_color='NONE', export_lights=False, export_cameras=False)
    print('exported', fp, os.path.getsize(fp), 'bytes', flush=True)


def main():
    t0 = time.time()
    sc = L.reset()
    setup_materials()
    build_floors()
    gallery_walls()
    partitions()
    vaults()
    lobby()
    halls()
    rotunda()
    front()
    exterior_shell()
    pieces = import_pieces()
    smooth_names = ('columns', 'urns', 'bronze', 'lamps', 'copper', 'dome', 'bases', 'capitals')
    for name, b in B.items():
        if b.count == 0: continue
        ob = b.finish()
        if name in smooth_names: smooth(ob, 40.0)
        if name in ('walls', 'ceiling'):
            m = ob.modifiers.new('ue_thickness', 'SOLIDIFY'); m.thickness = WALL_T; m.offset = -1.0; m.use_even_offset = True
    add_lights()
    write_lights_json()
    obs = [o for o in sc.objects if o.type == 'MESH']
    print('objects', len(obs), 'web pieces', pieces, 'lights', len(LIGHTS), 'tris ~', sum(len(o.data.polygons) * 2 for o in obs), 'built in %.0f s' % (time.time() - t0), flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'museum.blend'))
    if RENDER:
        views = {'lobby': ((0.0, 1.62, -2.0), (0.0, 2.6, -14.0), 74), 'gallery': ((0.0, 1.62, -7.0), (0.0, 3.0, -20.0), 74),
                 'vault': ((-3.0, 1.62, -8.0), (2.0, 7.5, -15.0), 80), 'rotunda': ((0.0, 1.62, 9.8), (0.0, 4.0, 0.0), 80),
                 'dome': ((0.0, 1.62, 5.8), (0.3, 13.0, 5.6), 90), 'front': ((6.0, 1.0, 34.0), (0.0, 7.0, 12.0), 72),
                 'bay': ((-1.0, 1.62, -12.5), (-6.0, 2.2, -9.0), 70), 'portico': ((-4.0, 1.0, 22.0), (0.0, 5.0, 13.0), 76)}
        want = [a.split('=')[1].split(',') for a in sys.argv if a.startswith('--views=')]
        for name in (want[0] if want else views):
            eye, target, fov = views[name]
            render(name, eye, target, fov=fov)
    export_glb()
    print('done in %.0f s' % (time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
