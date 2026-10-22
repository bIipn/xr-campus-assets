"""The talks wing, built for real: the Auditorium and its Foyer in Blender (bpy) at campus coordinates, for Unreal.

Where: east of the galleries, north of Hall R. Hall R's new north door (bl/museum.py) opens into the FOYER (x 6.7 ..
11.35, z -13.65 .. -4.95 inside; marble floor with a verde border, limestone walls on a verde dado, pilasters, a
coffered ceiling, two chandeliers, a bench, framed posters, the door to the hall under a pediment), and the foyer's
north wall opens through a portal lettered AUDITORIUM into the back of the AUDITORIUM (x 6.75 .. 20.75, z -31.0 ..
-14.1 inside): a level cross-aisle at the entry, seven curved rows of upholstered theatre chairs stepping down 0.2 m a
row toward the stage, side aisles with step lights, a balustrade along the top row, an orchestra floor, a raised
stage with a curved front, steps up either side, a lectern at stage left, an 8 x 4.5 m screen on the north wall in a
black masking frame, velvet drapes and a valance, warm walnut slats on the walls under plaster, a ceiling with
acoustic clouds, downlights and a lighting truss, sconces, a booth window and an exit sign. The outer shell (the
limestone order on the east and north faces, the roof) is bl/exterior.py's (SHELLS 'foyer' and 'auditorium').

The talks system's marks (see unreal/Pipeline/README.md): screen__auditorium (the 16:9 quad the slides play on),
spot__auditorium_f90 (where the speaker stands, behind the lectern, facing the seats), and one tagged mesh per chair
seat__auditorium_r<row>c<n>_f<yaw> (the cushion; the yaw faces the rows' centre of curvature). The foyer bench is
seat__foyer_<a|b>_f0.

Campus axes: x east, y up, z south.  Blender: X = x, Y = -z, Z = y.
Usage (Blender 5.2 or bpy 5.2.2):   python bl/auditorium.py [--render] [--quick] [--views=a,b]
Writes assets/auditorium/auditorium.blend, unreal/Pipeline/out/auditorium/Auditorium.glb, lights.json, layout.json,
and preview renders. Then prepare_for_unreal.py -- Auditorium.
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
from library import P, D, Builder, bar, prism, material, MATS, select_only, seat_yaw   # noqa: E402
from neo import (face_uv, lathe, run_boxes, pilaster, coffered_flat, rosette_at, sconce, wall_with_door,       # noqa: E402
                 extrude_profile, smooth, DADO, DADO_H)
import museum as M                                               # noqa: E402  (Hall R's door, chandelier, slab)

SP = L.SP
OUT = os.path.join(SP, 'assets', 'auditorium')
PIPE = os.path.join(SP, 'unreal', 'Pipeline', 'out', 'auditorium')
TEX = os.path.join(SP, 'assets', 'tex')
FONTS = os.path.join(HERE, 'fonts')
RENDER = '--render' in sys.argv
QUICK = '--quick' in sys.argv
os.makedirs(OUT, exist_ok=True); os.makedirs(PIPE, exist_ok=True)

# ---------------------------------------------------------------- the plan (campus metres)
# the foyer
FX0, FX1 = 6.70, 11.35
FZS, FZN = M.FOYER_FACE, -13.65            # south face (Hall R's door), north face (the auditorium's portal)
FH = 4.6
FXC = (FX0 + FX1) / 2
HALL_DOOR = M.HALL_R_DOOR                  # (x0, x1, h)
PORTAL = (FXC - 1.3, FXC + 1.3, 3.2)       # the portal into the auditorium, through the 0.45 m wall
# the auditorium
AX0, AX1 = 6.75, 20.75
AZN, AZS = -31.0, -14.10
XC = (AX0 + AX1) / 2                       # 13.75
ZC = -42.0                                 # the rows' centre of curvature
RHO_S = 15.0                               # the stage's front edge
RHO_0 = 16.6                               # the first tier's front edge
TD, TR, NT = 0.95, 0.20, 7                 # tier depth, rise, number of rows
Y_ORCH = -1.6                              # the orchestra floor, one step below the first row
Y_STAGE = -0.8
RHO_B = RHO_0 + NT * TD                    # the back of the top row: the cross-aisle (y 0) begins here
CEIL = 6.6
PANEL_TOP = 3.2
SEAT_HALF = 4.6                            # the seat block: |x - XC| <= this
SEAT_PITCH = 0.575
SCREEN_W = 8.0; SCREEN_H = SCREEN_W * 9 / 16
SCREEN_Y0 = Y_STAGE + 1.45
SCREEN_Z = AZN + 0.064                     # the image; the masking frame's face 4 mm behind it
LECTERN = (18.6, -28.35)
SPEAKER = (18.6, -28.9)
NX = 56                                    # columns across the hall for the floors


def zarc(rho, x):
    """The z of the arc of radius rho (about the rows' centre) at x."""
    return ZC + math.sqrt(max(rho * rho - (x - XC) ** 2, 0.0))


def setup_materials():
    material('marble_w', 'marblew_col', 'marblew_rgh', 'marblew_nrm', roughness=0.14)
    material('marble_b', 'marbleb_col', 'marbleb_rgh', 'marbleb_nrm', roughness=0.12)
    material('verde', 'verde_col', 'verde_rgh', 'verde_nrm', roughness=0.13)
    material('lime', 'lime_col', 'lime_rgh', 'lime_nrm', roughness=0.7)
    material('stone', 'marblew_col', 'marblew_rgh', 'marblew_nrm', roughness=0.3)
    material('gilt', color=(1.0, 0.78, 0.38, 1), roughness=0.32, metallic=1.0)
    material('bronze', color=(0.40, 0.26, 0.13, 1), roughness=0.42, metallic=1.0)
    material('lamp_e', color=(1, 1, 1, 1), emission=(1.0, 0.86, 0.62, 1), emission_strength=14.0)
    material('aud_carpet', color=(0.20, 0.035, 0.045, 1), roughness=0.95)
    material('aud_seatfab', color=(0.34, 0.035, 0.05, 1), roughness=0.85)
    material('aud_velvet', color=(0.22, 0.015, 0.03, 1), roughness=0.75)
    material('aud_slats', 'walnut_col', 'walnut_rgh', 'walnut_nrm', roughness=0.4, nrm_strength=0.6)
    material('aud_floor', 'oak_floor_col', 'oak_floor_rgh', 'oak_floor_nrm', roughness=0.4)
    material('aud_stagedeck', 'walnut_col', 'walnut_rgh', 'walnut_nrm', roughness=0.35)
    material('aud_plaster', 'plaster_col', 'plaster_rgh', 'plaster_nrm', roughness=0.9)
    material('aud_backing', color=(0.028, 0.022, 0.018, 1), roughness=0.8)
    material('aud_fabric_dark', color=(0.022, 0.022, 0.026, 1), roughness=0.95)
    material('aud_black', color=(0.008, 0.008, 0.009, 1), roughness=0.9)
    material('aud_brass', color=(0.83, 0.62, 0.32, 1), roughness=0.3, metallic=1.0)
    material('aud_shell', color=(0.055, 0.045, 0.04, 1), roughness=0.5)
    material('aud_armwood', 'oak_col', 'oak_rgh', 'oak_nrm', roughness=0.35)
    material('aud_steel', color=(0.05, 0.05, 0.055, 1), roughness=0.4, metallic=0.6)
    material('aud_steplight_e', color=(1, 1, 1, 1), emission=(1.0, 0.82, 0.55, 1), emission_strength=6.0)
    material('aud_downlight_e', color=(1, 1, 1, 1), emission=(1.0, 0.93, 0.82, 1), emission_strength=12.0)
    material('aud_exit_e', color=(1, 1, 1, 1), emission=(0.15, 1.0, 0.35, 1), emission_strength=4.0)
    material('aud_glass', color=(0.02, 0.025, 0.03, 1), roughness=0.05, metallic=0.2)
    material('aud_mark', color=(0.2, 0.2, 0.2, 1), roughness=0.9)
    material('screen_auditorium', color=(0.04, 0.04, 0.045, 1), roughness=0.3)
    for k in (1, 2, 3):
        material('aud_poster_%d' % k, 'aud_poster_%d' % k, roughness=0.5)
    material('aud_inscription', 'aud_inscription', 'lime_rgh', roughness=0.7)


B = {}
def builder(name, mat, tile=1.0, smooth_deg=None):
    if name not in B: B[name] = Builder(name, mat, tile=tile, lightmap=False, vcol=False, smooth=smooth_deg)
    return B[name]


LIGHTS = []   # (kind, (x, y, z), colour, watts, area size or None)
PREVIEW_LIGHTS = []   # the same, for the Cycles previews only (not written to lights.json)


# ---------------------------------------------------------------- textures: the posters and the lettering
def make_textures():
    from PIL import Image, ImageDraw, ImageFont
    import clientpack
    client = clientpack.get('client', 'XR Libraries')
    def font(names, size):
        for n in names:
            for p in (os.path.join(FONTS, n), '/usr/share/fonts/opentype/inter/' + n, '/usr/share/fonts/truetype/dejavu/' + n):
                if os.path.exists(p): return ImageFont.truetype(p, size)
        return ImageFont.load_default()
    cinzel = lambda s: font(['Cinzel.ttf'], s)
    inter = lambda s, w='Regular': font(['Inter-%s.otf' % w, 'DejaVuSans.ttf'], s)
    W, H = 1200, 1720
    def wrap(d, text, f, width):
        words, lines, line = text.split(), [], ''
        for w in words:
            t = (line + ' ' + w).strip()
            if d.textlength(t, font=f) <= width: line = t
            else: lines.append(line); line = w
        if line: lines.append(line)
        return lines
    posters = [
        ((22, 46, 60), (214, 174, 96), 'TALKS', 'In the Auditorium',
         'Speakers, stories and slides. Take a seat and the talk begins.', 'Through the Foyer · Every day'),
        ((124, 52, 32), (246, 222, 176), 'CLASSES', 'Room 104 · XR Classroom',
         'Sit in on a class, then take the quiz and earn a certificate with your name on it.', 'Intro to Virtual Reality'),
        ((32, 78, 64), (238, 226, 190), 'UNDER THE SKY', 'The Forecourt Theatre',
         'A talk on the steps of the museum. Find a seat on the stone tiers.', 'Out the front doors'),
    ]
    for k, (bg, ink, kick, title, body, foot) in enumerate(posters, 1):
        im = Image.new('RGB', (W, H), bg)
        d = ImageDraw.Draw(im)
        m = 90
        d.rectangle((m - 30, m - 30, W - m + 30, H - m + 30), outline=ink, width=6)
        d.text((m, m + 20), client.upper(), font=inter(44, 'SemiBold'), fill=ink)
        # a quiet emblem: concentric arcs, a stage seen from above
        cx, cy = W // 2, 690
        for r in range(120, 420, 60):
            d.arc((cx - r, cy - r, cx + r, cy + r), 200, 340, fill=ink, width=10)
        d.rectangle((cx - 150, cy + 40, cx + 150, cy + 70), fill=ink)
        ks = 150
        while ks > 60 and d.textlength(kick, font=cinzel(ks)) > W - 2 * m: ks -= 6
        d.text((m, 1000 + (150 - ks) // 2), kick, font=cinzel(ks), fill=ink)
        y = 1190
        for ln in wrap(d, title, inter(76, 'Bold'), W - 2 * m):
            d.text((m, y), ln, font=inter(76, 'Bold'), fill=(255, 255, 255)); y += 92
        y += 24
        for ln in wrap(d, body, inter(46), W - 2 * m):
            d.text((m, y), ln, font=inter(46), fill=(235, 235, 230)); y += 60
        d.text((m, H - m - 70), foot, font=inter(48, 'SemiBold'), fill=ink)
        im.resize((600, 860), Image.LANCZOS).save(os.path.join(TEX, 'aud_poster_%d.png' % k), optimize=True)
    # the lettering over the portal: incised capitals on limestone
    lime = Image.open(os.path.join(TEX, 'lime_col.png')).convert('RGB')
    im = Image.new('RGB', (2400, 300))
    for x in range(0, 2400, lime.width):
        for y in range(0, 300, lime.height):
            im.paste(lime, (x, y))
    d = ImageDraw.Draw(im)
    f = cinzel(190)
    t = 'AUDITORIUM'
    tw = d.textlength(t, font=f)
    x0 = (2400 - tw) / 2
    d.text((x0 + 4, 52), t, font=f, fill=(150, 140, 122))          # the cut's lit lower edge
    d.text((x0, 46), t, font=f, fill=(62, 56, 48))
    im.resize((1200, 150), Image.LANCZOS).save(os.path.join(TEX, 'aud_inscription.png'), optimize=True)


# ---------------------------------------------------------------- helpers
def quad_box(b, c, nrm_hint=None):
    """Six faces of a hexahedron from its 8 campus corners: c[0..3] the bottom ring, c[4..7] the top ring above them."""
    pts = [P(*p) for p in c]
    centre = sum(pts, Vector((0, 0, 0))) / 8
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    for f in faces:
        q = [pts[i] for i in f]
        mid = sum(q, Vector((0, 0, 0))) / 4
        b.face(q, (mid - centre).normalized())


def wall_face(b, a, c, out, y0, y1, nu=2, nv=2):
    A0 = P(a[0], y0, a[1]); C0 = P(c[0], y0, c[1]); A1 = P(a[0], y1, a[1])
    b.grid(A0, C0 - A0, A1 - A0, D(out[0], 0, out[1]), nu, nv)


# ---------------------------------------------------------------- the foyer
def foyer():
    wl = builder('foyer_walls', 'lime', tile=3.0)
    bs = builder('foyer_mouldings', 'stone', tile=2.0); bc = builder('foyer_capitals', 'gilt'); bb = builder('foyer_bases', 'stone', tile=2.0)
    gold = builder('foyer_gilt', 'gilt'); dado = builder('foyer_dado', 'verde', tile=2.0)
    # floor: a verde border, the cream field, the thresholds through Hall R's door and the portal
    fw = builder('foyer_floor', 'marble_w', tile=2.4); fv = builder('foyer_floor_verde', 'verde', tile=2.0)
    BORD = 0.4
    M.slab(fv, FX0, FX1, FZN, FZN + BORD, nu=2); M.slab(fv, FX0, FX1, FZS - BORD, FZS, nu=2)
    M.slab(fv, FX0, FX0 + BORD, FZN + BORD, FZS - BORD, nv=4); M.slab(fv, FX1 - BORD, FX1, FZN + BORD, FZS - BORD, nv=4)
    M.slab(fw, FX0 + BORD, FX1 - BORD, FZN + BORD, FZS - BORD, nu=2, nv=6)
    M.slab(fw, HALL_DOOR[0], HALL_DOOR[1], FZS, -4.6)                       # Hall R's door: its reveal is the museum's
    M.slab(fw, PORTAL[0], PORTAL[1], AZS, FZN)                              # the portal, through the auditorium's wall
    # walls above the dado (the dado boxes are the wall below 1.0 m); the two short walls carry the doors
    y0 = DADO_H - 0.02
    wall_with_door(wl, (FX0, y0, FZS), (1, 0, 0), (0, 1, 0), (0, 0, -1), 0.0, FX1 - FX0, FH - y0,
                   HALL_DOOR[0] - FX0, HALL_DOOR[1] - FX0, HALL_DOOR[2] - y0, solid=False)
    wall_with_door(wl, (FX0, y0, FZN), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.0, FX1 - FX0, FH - y0,
                   PORTAL[0] - FX0, PORTAL[1] - FX0, PORTAL[2] - y0, solid=False)
    wall_face(wl, (FX0, FZS), (FX0, FZN), (1, 0), y0, FH, nu=4, nv=2)
    wall_face(wl, (FX1, FZN), (FX1, FZS), (-1, 0), y0, FH, nu=4, nv=2)
    for (a, c, out) in (((FX0, FZS), (HALL_DOOR[0] - 0.16, FZS), (0, -1)), ((HALL_DOOR[1] + 0.16, FZS), (FX1, FZS), (0, -1)),
                        ((FX0, FZN), (PORTAL[0] - 0.22, FZN), (0, 1)), ((PORTAL[1] + 0.22, FZN), (FX1, FZN), (0, 1)),
                        ((FX0, FZS), (FX0, FZN), (1, 0)), ((FX1, FZN), (FX1, FZS), (-1, 0))):
        run_boxes(dado, a, c, out, DADO, seg=3.0)
    # the cornice all round, and pilasters down the long walls
    corn = [(FH - 0.46, FH - 0.36, 0.06), (FH - 0.36, FH - 0.14, 0.10), (FH - 0.14, FH, 0.24)]
    for (a, c, out) in (((FX0, FZS), (FX1, FZS), (0, -1)), ((FX0, FZN), (FX1, FZN), (0, 1)), ((FX0, FZS), (FX0, FZN), (1, 0)), ((FX1, FZN), (FX1, FZS), (-1, 0))):
        run_boxes(bs, a, c, out, corn, seg=3.0)
    for z in (FZS - 0.6, (FZS + FZN) / 2, FZN + 0.6):
        for (x, out) in ((FX0, (1, 0)), (FX1, (-1, 0))):
            if x == FX0 and abs(z - (FZS + FZN) / 2) < 0.1: continue      # the bench and its poster stand there
            pilaster(bs, bc, bb, (x, z), out, 0.42, FH - 0.46, depth=0.10)
    coffered_flat(builder('foyer_ceiling', 'lime', tile=3.0), gold, FX0, FX1, FZN, FZS, FH, 3, 6, rib=0.26, depth=0.18, inset=0.09)
    # Hall R's door from this side: pilasters, an architrave and a pediment (the hall side has a plain surround)
    dx0, dx1, dh = HALL_DOOR
    for x in (dx0 - 0.08, dx1 + 0.08):                     # the architrave's jambs, from the floor
        bs.box(x, dh / 2, FZS - 0.05, 0.16, dh, 0.10, seg=1.5)
    for x in (dx0 - 0.36, dx1 + 0.36):
        pilaster(bs, bc, bb, (x, FZS), (0, -1), 0.36, dh + 0.30, depth=0.12)
    run_boxes(bs, (dx0 - 0.55, FZS), (dx1 + 0.55, FZS), (0, -1), [(dh + 0.30, dh + 0.46, 0.16), (dh + 0.46, dh + 0.56, 0.22)])
    apex, base, hw = dh + 1.38, dh + 0.56, (dx1 - dx0) / 2 + 0.62
    xm = (dx0 + dx1) / 2
    extrude_profile(bs, [(-hw + 0.22, base), (hw - 0.22, base), (0, apex - 0.16)], (xm, 0, FZS), (1, 0, 0), (0, 1, 0), (0, 0, -1), 0.10)
    for s in (-1, 1):
        bar(bs, (xm + s * hw, base - 0.02, FZS - 0.16), (xm, apex, FZS - 0.16), 0.26, 0.14)
    rosette_at(gold, (xm, base + 0.28, FZS - 0.11), D(-1, 0, 0), D(0, 1, 0), D(0, 0, -1), 0.17)
    # the portal: a lugged architrave, the lettered band, a cornice
    px0, px1, ph = PORTAL
    for x in (px0 - 0.11, px1 + 0.11):
        bs.box(x, ph / 2, FZN + 0.06, 0.22, ph, 0.12, seg=1.5)
    run_boxes(bs, (px0 - 0.28, FZN), (px1 + 0.28, FZN), (0, 1), [(ph, ph + 0.18, 0.12)])
    ins = builder('foyer_inscription', 'aud_inscription')
    iy0, iy1 = ph + 0.24, ph + 0.62
    zf = FZN + 0.012
    face_uv(ins, [P(px0 - 0.2, iy0, zf), P(px1 + 0.2, iy0, zf), P(px1 + 0.2, iy1, zf), P(px0 - 0.2, iy1, zf)], D(0, 0, 1), [(0, 0), (1, 0), (1, 1), (0, 1)])
    run_boxes(bs, (px0 - 0.36, FZN), (px1 + 0.36, FZN), (0, 1), [(iy1 + 0.02, iy1 + 0.12, 0.14), (iy1 + 0.12, iy1 + 0.20, 0.22)])
    # the portal's reveal through the auditorium's wall
    rv = builder('portal_reveal', 'stone', tile=1.5)
    for (x, n) in ((px0, 1), (px1, -1)):
        rv.face([P(x, 0.0, FZN), P(x, 0.0, AZS), P(x, ph, AZS), P(x, ph, FZN)], D(n, 0, 0))
    rv.face([P(px0, ph, FZN), P(px1, ph, FZN), P(px1, ph, AZS), P(px0, ph, AZS)], D(0, -1, 0))
    # two chandeliers on the axis, sconces on the pilasters' line
    pd = builder('bronze', 'bronze'); pb = builder('lamps', 'lamp_e')
    for z in (-7.4, -11.2):
        M.chandelier(pd, pb, FXC, z, FH, 3.35)
        LIGHTS.append(('foyer', (FXC, 3.6, z), (1.0, 0.86, 0.68), 700, None))
    # a marble bench against the west wall, facing the posters: two seats
    pe = builder('foyer_pedestals', 'verde', tile=2.0); zb = (FZS + FZN) / 2
    for dz in (-0.75, 0.75): pe.box(FX0 + 0.45, 0.2, zb + dz, 0.42, 0.4, 0.16, seg=0)
    for k, dz in enumerate((-0.48, 0.48)):
        t = builder('seat__foyer_%s_f%d' % ('ab'[k], seat_yaw(1.0, 0.0)), 'stone', tile=2.0)
        t.box(FX0 + 0.45, 0.44, zb + dz, 0.52, 0.08, 0.94, seg=0)
    # posters in gilt frames: two on the east wall, one over the bench
    for k, (x, z, out) in enumerate(((FX1, -6.9, (-1, 0)), (FX1, -11.7, (-1, 0)), (FX0, zb, (1, 0))), 1):
        poster(k, x, z, out)


def poster(k, x, z, out, w=0.9, h=1.29, yc=1.95):
    """A framed poster on a side wall (out = (+-1, 0), the way it faces)."""
    pb = builder('aud_poster_%d' % k, 'aud_poster_%d' % k)
    fr = builder('foyer_gilt', 'gilt')
    xo = x + out[0] * 0.035
    rz = -out[0]                          # the viewer's right, looking against `out`, runs along z by this sign
    zl, zr = z - rz * w / 2, z + rz * w / 2
    face_uv(pb, [P(xo, yc - h / 2, zl), P(xo, yc - h / 2, zr), P(xo, yc + h / 2, zr), P(xo, yc + h / 2, zl)],
            D(out[0], 0, 0), [(0, 0), (1, 0), (1, 1), (0, 1)])
    f = 0.06; xf = x + out[0] * 0.03
    for (cy, cz, sy, sz) in ((yc + h / 2 + f / 2, z, f, w + 2 * f), (yc - h / 2 - f / 2, z, f, w + 2 * f),
                             (yc, z + w / 2 + f / 2, h, f), (yc, z - w / 2 - f / 2, h, f)):
        fr.box(xf, cy, cz, 0.06, sy, sz, faces=('X' if out[0] > 0 else 'x') + 'yYzZ')


# ---------------------------------------------------------------- the auditorium: shell surfaces
def hall_walls():
    bk = builder('aud_backing', 'aud_backing'); sl = builder('aud_slats', 'aud_slats', tile=1.2)
    pl = builder('aud_plaster', 'aud_plaster', tile=3.0); rail = builder('aud_rail', 'aud_armwood', tile=1.0)
    fab = builder('aud_fabric', 'aud_fabric_dark', tile=2.0)
    ylo = Y_ORCH - 0.05
    # the side walls: dark backing behind walnut slats up to PANEL_TOP, a rail, plaster to the ceiling, a cornice
    for (x, out) in ((AX0, (1, 0)), (AX1, (-1, 0))):
        a, c = (x, AZS), (x, AZN)
        wall_face(bk, a, c, out, ylo, PANEL_TOP, nu=6, nv=2)
        wall_face(pl, a, c, out, PANEL_TOP, CEIL, nu=6, nv=2)
        z = AZS - 0.08
        while z > AZN + 0.06:
            sl.box(x + out[0] * 0.016, (ylo + PANEL_TOP) / 2, z, 0.03, PANEL_TOP - ylo, 0.045, faces=('X' if out[0] > 0 else 'x') + 'yYzZ')
            z -= 0.11
        run_boxes(rail, a, c, out, [(PANEL_TOP - 0.02, PANEL_TOP + 0.08, 0.07)])
        run_boxes(builder('aud_cornice', 'aud_plaster', tile=3.0), a, c, out, [(CEIL - 0.30, CEIL - 0.18, 0.08), (CEIL - 0.18, CEIL, 0.18)])
    # the north wall: dark acoustic fabric behind the stage
    wall_face(fab, (AX0, AZN), (AX1, AZN), (0, 1), Y_STAGE - 0.05, CEIL, nu=6, nv=3)
    run_boxes(builder('aud_cornice', 'aud_plaster', tile=3.0), (AX0, AZN), (AX1, AZN), (0, 1), [(CEIL - 0.30, CEIL - 0.18, 0.08), (CEIL - 0.18, CEIL, 0.18)])
    # the south wall: the portal, slats below the rail, plaster above, a booth window, the exit sign
    px0, px1, ph = PORTAL
    wall_with_door(bk, (AX1, 0.0, AZS), (-1, 0, 0), (0, 1, 0), (0, 0, -1), 0.0, AX1 - AX0, PANEL_TOP, AX1 - px1, AX1 - px0, ph, solid=False)
    wall_face(pl, (AX1, AZS), (AX0, AZS), (0, -1), PANEL_TOP, CEIL, nu=6, nv=2)
    x = AX0 + 0.08
    while x < AX1 - 0.06:
        if not (px0 - 0.03 < x < px1 + 0.03):
            sl.box(x, PANEL_TOP / 2, AZS - 0.016, 0.045, PANEL_TOP, 0.03, faces='xXyYz')
        elif ph < PANEL_TOP - 0.05:
            sl.box(x, (ph + PANEL_TOP) / 2, AZS - 0.016, 0.045, PANEL_TOP - ph, 0.03, faces='xXyYz')
        x += 0.11
    run_boxes(rail, (AX1, AZS), (AX0, AZS), (0, -1), [(PANEL_TOP - 0.02, PANEL_TOP + 0.08, 0.07)])
    run_boxes(builder('aud_cornice', 'aud_plaster', tile=3.0), (AX1, AZS), (AX0, AZS), (0, -1), [(CEIL - 0.30, CEIL - 0.18, 0.08), (CEIL - 0.18, CEIL, 0.18)])
    # the portal's casing on this side
    br = builder('aud_brass', 'aud_brass')
    for xx in (px0 - 0.05, px1 + 0.05):
        rail.box(xx, ph / 2, AZS - 0.04, 0.10, ph, 0.08)
    rail.box((px0 + px1) / 2, ph + 0.05, AZS - 0.04, px1 - px0 + 0.2, 0.10, 0.08)
    ex = builder('aud_exit', 'aud_exit_e')
    ex.box((px0 + px1) / 2, ph + 0.30, AZS - 0.05, 0.44, 0.16, 0.04, faces='xXyYz')
    gl = builder('aud_booth', 'aud_glass')
    gl.face([P(15.25, 4.1, AZS - 0.01), P(12.25, 4.1, AZS - 0.01), P(12.25, 5.0, AZS - 0.01), P(15.25, 5.0, AZS - 0.01)], D(0, 0, -1))
    for (cx, cy, sx, sy) in ((13.75, 4.07, 3.08, 0.06), (13.75, 5.03, 3.08, 0.06), (12.22, 4.55, 0.06, 0.9), (15.28, 4.55, 0.06, 0.9), (13.75, 4.55, 0.04, 0.9)):
        br.box(cx, cy, AZS - 0.03, sx, sy, 0.05, faces='xXyYz')
    # the ceiling: plaster, three acoustic clouds of walnut with downlights under them, a lighting truss
    ce = builder('aud_ceiling', 'aud_plaster', tile=3.0)
    ce.grid(P(AX0, CEIL, AZS), P(AX1, CEIL, AZS) - P(AX0, CEIL, AZS), P(AX0, CEIL, AZN) - P(AX0, CEIL, AZS), D(0, -1, 0), 6, 8)
    cl = builder('aud_clouds', 'aud_slats', tile=1.5); dl = builder('aud_downlights', 'aud_downlight_e'); st = builder('aud_steel', 'aud_steel')
    for zc in (-16.6, -20.3, -24.0):
        cl.box(XC, 6.12, zc, 11.2, 0.06, 2.4, faces='xXyzZ')
        for (xa, xb) in ((XC - 5.4, XC - 5.3), (XC + 5.3, XC + 5.4)):
            for dz in (-1.0, 1.0):
                bar(st, ((xa + xb) / 2, 6.15, zc + dz), ((xa + xb) / 2, CEIL, zc + dz), 0.012)
        for x_ in (XC - 4.2, XC - 1.4, XC + 1.4, XC + 4.2):
            lathe(dl, x_, zc, [(6.085, 0.0), (6.085, 0.085)], n=16, cap_top=False)
            lathe(st, x_, zc, [(6.088, 0.085), (6.088, 0.11), (6.09, 0.11)], n=16, cap_top=False)
            LIGHTS.append(('downlight', (x_, 6.0, zc), (1.0, 0.93, 0.82), 120, None))
    # the truss across the hall in front of the stage, with four stage lights on it
    zt = -27.0
    for dy in (5.95, 6.25):
        bar(st, (AX0 + 0.6, dy, zt), (AX1 - 0.6, dy, zt), 0.05)
    x_ = AX0 + 0.6
    while x_ < AX1 - 0.6:
        bar(st, (x_, 5.95, zt), (x_ + 0.4, 6.25, zt), 0.02); x_ += 0.4
    for x_ in (AX0 + 0.6, AX1 - 0.6):
        bar(st, (x_, 6.25, zt), (x_, CEIL, zt), 0.04)
    for x_ in (XC - 4.5, XC - 1.5, XC + 1.5, XC + 4.5):
        lathe(st, x_, zt + 0.12, [(5.62, 0.0), (5.62, 0.11), (5.9, 0.13), (5.92, 0.0)], n=12)
        lathe(dl, x_, zt + 0.12, [(5.615, 0.0), (5.615, 0.10)], n=12, cap_top=False)
    for x_ in (XC - 3.0, XC, XC + 3.0):
        LIGHTS.append(('stage', (x_, 5.5, zt - 0.6), (1.0, 0.9, 0.78), 350, None))
    # sconces on the side walls, over the slats
    bz = builder('bronze', 'bronze'); lp = builder('lamps', 'lamp_e')
    for z in (-16.3, -20.6, -24.9):
        for (x, out) in ((AX0, (1, 0)), (AX1, (-1, 0))):
            sconce(bz, lp, x, 4.35, z, out)
            LIGHTS.append(('sconce', (x + out[0] * 0.3, 4.4, z), (1.0, 0.84, 0.62), 120, None))


# ---------------------------------------------------------------- the floors: stage, orchestra, tiers, cross-aisle
def floors():
    cp = builder('aud_carpet', 'aud_carpet', tile=2.0); wd = builder('aud_floor', 'aud_floor', tile=2.4)
    dk = builder('aud_stagedeck', 'aud_stagedeck', tile=2.0); rs = builder('aud_stage_front', 'aud_shell', tile=1.5)
    br = builder('aud_brass', 'aud_brass'); sl = builder('aud_steplights', 'aud_steplight_e')
    xs = [AX0 + (AX1 - AX0) * i / NX for i in range(NX + 1)]
    def band(b, r_in, r_out, y, z_cap=None):
        for i in range(NX):
            xa, xb = xs[i], xs[i + 1]
            za0, zb0 = zarc(r_in, xa), zarc(r_in, xb)
            za1, zb1 = (zarc(r_out, xa), zarc(r_out, xb)) if r_out is not None else (z_cap, z_cap)
            b.face([P(xa, y, za0), P(xb, y, zb0), P(xb, y, zb1), P(xa, y, za1)], D(0, 1, 0))
    def riser(b, r, y0, y1, toward_centre=True):
        for i in range(NX):
            xa, xb = xs[i], xs[i + 1]
            za, zb = zarc(r, xa), zarc(r, xb)
            xm = (xa + xb) / 2; zm = (za + zb) / 2
            n = (XC - xm, ZC - zm) if toward_centre else (xm - XC, zm - ZC)
            b.face([P(xa, y0, za), P(xb, y0, zb), P(xb, y1, zb), P(xa, y1, za)], D(n[0], 0, n[1]).normalized())
    # the stage deck from the north wall to its curved front, and the front itself (dark panels, a brass nosing)
    for i in range(NX):
        xa, xb = xs[i], xs[i + 1]
        dk.face([P(xa, Y_STAGE, AZN), P(xb, Y_STAGE, AZN), P(xb, Y_STAGE, zarc(RHO_S, xb)), P(xa, Y_STAGE, zarc(RHO_S, xa))], D(0, 1, 0))
    riser(rs, RHO_S, Y_ORCH - 0.02, Y_STAGE - 0.03, toward_centre=False)
    for i in range(NX):
        xa, xb = xs[i], xs[i + 1]
        bar(br, (xa, Y_STAGE - 0.015, zarc(RHO_S, xa) + 0.012), (xb, Y_STAGE - 0.015, zarc(RHO_S, xb) + 0.012), 0.035, 0.03, caps=(i in (0, NX - 1)))
    # the orchestra, the rows, the cross-aisle
    band(wd, RHO_S, RHO_0, Y_ORCH)
    for k in range(1, NT + 1):
        r_in = RHO_0 + (k - 1) * TD
        y = Y_ORCH + k * TR
        band(cp, r_in, r_in + TD, y)
        riser(cp, r_in, y - TR, y)
    band(cp, RHO_B, None, 0.0, z_cap=AZS)
    riser(cp, RHO_B, -TR, 0.0)
    # step lights in the side aisles, one in each riser, and brass nosings along the aisle steps
    for k in range(1, NT + 2):
        r = RHO_0 + (k - 1) * TD
        y = Y_ORCH + k * TR
        for xa in (AX0 + 0.75, AX1 - 0.75):
            za = zarc(r, xa)
            n = (XC - xa, ZC - za); L_ = math.hypot(*n); n = (n[0] / L_, n[1] / L_)
            sl.box(xa + n[0] * 0.006, y - TR / 2 - 0.02, za + n[1] * 0.006, 0.34, 0.05, 0.01, ry=math.atan2(-n[1], n[0]) + math.pi / 2, faces='xXyYZz')
            LIGHTS.append(('step', (xa + n[0] * 0.08, y - TR / 2 - 0.03, za + n[1] * 0.08), (1.0, 0.82, 0.55), 4, None))
        for (xa, xb) in ((AX0 + 0.02, XC - SEAT_HALF - 0.3), (XC + SEAT_HALF + 0.3, AX1 - 0.02)):
            m_ = 6
            for i in range(m_):
                x0_ = xa + (xb - xa) * i / m_; x1_ = xa + (xb - xa) * (i + 1) / m_
                bar(br, (x0_, y - 0.010, zarc(r, x0_)), (x1_, y - 0.010, zarc(r, x1_)), 0.04, 0.026, caps=(i in (0, m_ - 1)))
    # steps up to the stage at both ends of the orchestra
    st = builder('aud_stage_steps', 'aud_stagedeck', tile=1.5); sr = builder('aud_stage_front', 'aud_shell', tile=1.5)
    for (x0, x1) in ((AX0 + 0.25, AX0 + 1.65), (AX1 - 1.65, AX1 - 0.25)):
        z_front = min(zarc(RHO_0, x0), zarc(RHO_0, x1)) - 0.03      # clear of the first row's arc across the flight
        for i in range(1, 4):
            ytop = Y_ORCH + i * 0.2
            zs = z_front - 0.32 * (i - 1)                     # the step's front (south) edge
            zn = z_front - 0.32 * i if i < 3 else min(zarc(RHO_S, x0), zarc(RHO_S, x1)) - 0.02
            st.face([P(x0, ytop, zs), P(x1, ytop, zs), P(x1, ytop, zn), P(x0, ytop, zn)], D(0, 1, 0))
            sr.face([P(x0, ytop - 0.2, zs), P(x1, ytop - 0.2, zs), P(x1, ytop, zs), P(x0, ytop, zs)], D(0, 0, 1))
            for (xx, nx) in ((x0, -1), (x1, 1)):
                sr.face([P(xx, Y_ORCH, zs), P(xx, Y_ORCH, zn), P(xx, ytop, zn), P(xx, ytop, zs)], D(nx, 0, 0))
    # a brass railing along the back of the top row, open at the side aisles, on an oak kerb: the rows stay in view
    # from the cross-aisle
    cap = builder('aud_rail', 'aud_armwood', tile=1.0); br = builder('aud_brass', 'aud_brass')
    rb = RHO_B + 0.12
    th0 = -math.asin((SEAT_HALF + 0.35) / rb); th1 = -th0
    arc_box(cap, rb - 0.06, rb + 0.06, th0, th1, -0.05, 0.14)
    def ap(a, y): return (XC + rb * math.sin(a), y, ZC + rb * math.cos(a))
    npost = int(round((th1 - th0) * rb / 1.1))
    for i in range(npost + 1):
        a = th0 + (th1 - th0) * i / npost
        p = ap(a, 0.0)
        prism(br, p[0], 0.14, p[2], 0.022, 0.80, n=10)
    n = 48
    for i in range(n):
        a0 = th0 + (th1 - th0) * i / n; a1 = th0 + (th1 - th0) * (i + 1) / n
        for (y_, w_) in ((0.955, 0.048), (0.52, 0.026)):
            bar(br, ap(a0, y_), ap(a1, y_), w_, caps=(i in (0, n - 1)))


def arc_box(b, r0, r1, a0, a1, y0, y1, n=24, top=True, bottom=False):
    """A curved slab about the rows' centre: radii r0..r1, angles a0..a1 (from +z, +x positive), heights y0..y1."""
    def pt(r, a, y): return P(XC + r * math.sin(a), y, ZC + r * math.cos(a))
    for i in range(n):
        t0 = a0 + (a1 - a0) * i / n; t1 = a0 + (a1 - a0) * (i + 1) / n; tm = (t0 + t1) / 2
        nin = D(-math.sin(tm), 0, -math.cos(tm))
        b.face([pt(r0, t0, y0), pt(r0, t1, y0), pt(r0, t1, y1), pt(r0, t0, y1)], nin)
        b.face([pt(r1, t1, y0), pt(r1, t0, y0), pt(r1, t0, y1), pt(r1, t1, y1)], -nin)
        if top: b.face([pt(r0, t0, y1), pt(r0, t1, y1), pt(r1, t1, y1), pt(r1, t0, y1)], D(0, 1, 0))
        if bottom: b.face([pt(r0, t0, y0), pt(r1, t0, y0), pt(r1, t1, y0), pt(r0, t1, y0)], D(0, -1, 0))
    for (a, sgn) in ((a0, -1), (a1, 1)):
        side = D(math.cos(a) * sgn, 0, -math.sin(a) * sgn)
        b.face([pt(r0, a, y0), pt(r1, a, y0), pt(r1, a, y1), pt(r0, a, y1)], side)


# ---------------------------------------------------------------- the seats
def chair(k, idx, x, z, y, f):
    """A theatre chair on the row at floor height y, facing f (unit campus x, z). The tagged mesh is the cushion."""
    r = (-f[1], f[0])                                   # the sitter's right
    def W(u, v, h): return (x + f[0] * u + r[0] * v, y + h, z + f[1] * u + r[1] * v)
    yaw = seat_yaw(f[0], f[1])
    ry = math.atan2(-f[1], f[0])                        # Builder.box: local x along f, local z along r
    cu = builder('seat__auditorium_r%dc%02d_f%d' % (k, idx, yaw), 'aud_seatfab', tile=0.6)
    cu.box(x, y + 0.40, z, 0.46, 0.10, 0.47, ry=ry)
    # the backrest: an upholstered pad with rounded top corners, leaning back 12 degrees, in a dark moulded shell
    bf = builder('aud_seatbacks', 'aud_seatfab', tile=0.6); bs = builder('aud_seatshells', 'aud_shell', tile=1.0)
    sn, cs = math.sin(math.radians(12.0)), math.cos(math.radians(12.0))
    S = (r[0], 0.0, r[1])                               # across the back, to the sitter's right
    T = (-f[0] * sn, cs, -f[1] * sn)                     # up the back, leaning away from the sitter
    N = (-f[0] * cs, -sn, -f[1] * cs)                    # out of the back, away from the sitter
    def outline(hw_b, hw_t, H, rc=0.085, n=5):
        pts = [(-hw_b, 0.0), (hw_b, 0.0), (hw_t, H - rc)]
        for i in range(1, n + 1):                        # the top right corner, then the top left
            a = math.pi / 2 * i / n
            pts.append((hw_t - rc + rc * math.cos(a), H - rc + rc * math.sin(a)))
        for i in range(0, n + 1):
            a = math.pi / 2 + math.pi / 2 * i / n
            pts.append((-hw_t + rc + rc * math.cos(a), H - rc + rc * math.sin(a)))
        return pts
    o = W(-0.22, 0.0, 0.47)
    extrude_profile(bf, outline(0.232, 0.218, 0.56), o, S, T, N, 0.07)
    o2 = (o[0] + N[0] * 0.075, o[1] + N[1] * 0.075, o[2] + N[2] * 0.075)
    extrude_profile(bs, outline(0.242, 0.228, 0.58), (o2[0] - T[0] * 0.01, o2[1] - T[1] * 0.01, o2[2] - T[2] * 0.01), S, T, N, 0.03)


def seats():
    count = 0
    sd = builder('aud_standards', 'aud_shell', tile=1.0); arm = builder('aud_armrests', 'aud_armwood', tile=0.6)
    for k in range(1, NT + 1):
        r_in = RHO_0 + (k - 1) * TD
        rho = r_in + 0.58                                   # the cushion's centre
        y = Y_ORCH + k * TR
        phi = math.asin(SEAT_HALF / rho)
        n = int(2 * phi * rho / SEAT_PITCH)
        for i in range(n):
            th = -phi + (i + 0.5) * 2 * phi / n
            x = XC + rho * math.sin(th); z = ZC + rho * math.cos(th)
            f = (-math.sin(th), -math.cos(th))
            chair(k, i + 1, x, z, y, f)
            count += 1
        # side standards with armrests between the chairs and at the row's ends
        for i in range(n + 1):
            th = -phi + i * 2 * phi / n
            f = (-math.sin(th), -math.cos(th))
            ry = math.atan2(-f[1], f[0])
            x = XC + (rho - 0.02) * math.sin(th); z = ZC + (rho - 0.02) * math.cos(th)
            sd.box(x, y + 0.31, z, 0.48, 0.62, 0.04, ry=ry)
            arm.box(x + f[0] * 0.03, y + 0.645, z + f[1] * 0.03, 0.46, 0.05, 0.075, ry=ry)
    return count


# ---------------------------------------------------------------- the stage: screen, drapes, lectern
def stage_dressing():
    # the black masking frame on the north wall and the screen 4 mm in front of it
    mk = builder('aud_masking', 'aud_black')
    m = 0.32
    mk.box(XC, SCREEN_Y0 + SCREEN_H / 2, (AZN + SCREEN_Z - 0.004) / 2 + 0.001, SCREEN_W + 2 * m, SCREEN_H + 2 * m, (SCREEN_Z - 0.004) - AZN - 0.002, faces='xXyYZ')
    br = builder('aud_brass', 'aud_brass')
    zt = SCREEN_Z - 0.004 + 0.008
    for (cx, cy, sx, sy) in ((XC, SCREEN_Y0 - m - 0.015, SCREEN_W + 2 * m + 0.06, 0.03), (XC, SCREEN_Y0 + SCREEN_H + m + 0.015, SCREEN_W + 2 * m + 0.06, 0.03),
                             (XC - SCREEN_W / 2 - m - 0.015, SCREEN_Y0 + SCREEN_H / 2, 0.03, SCREEN_H + 2 * m), (XC + SCREEN_W / 2 + m + 0.015, SCREEN_Y0 + SCREEN_H / 2, 0.03, SCREEN_H + 2 * m)):
        br.box(cx, cy, zt - 0.006, sx, sy, 0.03, faces='xXyYZ')
    sc = builder('screen__auditorium', 'screen_auditorium')
    x0, x1, y0, y1 = XC - SCREEN_W / 2, XC + SCREEN_W / 2, SCREEN_Y0, SCREEN_Y0 + SCREEN_H
    # seen from the seats (looking -z) the viewer's left is -x
    face_uv(sc, [P(x0, y0, SCREEN_Z), P(x1, y0, SCREEN_Z), P(x1, y1, SCREEN_Z), P(x0, y1, SCREEN_Z)], D(0, 0, 1), [(0, 0), (1, 0), (1, 1), (0, 1)])
    # velvet legs either side of the screen and a valance across the top, pleated
    vv = builder('aud_drapes', 'aud_velvet', tile=1.0, smooth_deg=70)
    def drape(xa, xb, ya, yb, zb, amp=0.07, period=0.32):
        n = max(2, int((xb - xa) / (period / 4)))
        pts = [(xa + (xb - xa) * i / n, zb + amp * math.sin(2 * math.pi * (xa + (xb - xa) * i / n) / period)) for i in range(n + 1)]
        for i in range(n):
            (pa, za), (pb_, zb_) = pts[i], pts[i + 1]
            nrm = D(-(zb_ - za), 0, (pb_ - pa)).normalized()
            vv.face([P(pa, ya, za), P(pb_, ya, zb_), P(pb_, yb, zb_), P(pa, yb, za)], nrm)
            vv.face([P(pb_, ya, zb_ - 0.012), P(pa, ya, za - 0.012), P(pa, yb, za - 0.012), P(pb_, yb, zb_ - 0.012)], -nrm)
    drape(AX0, XC - SCREEN_W / 2 - m - 0.35, Y_STAGE + 0.005, 5.95, AZN + 0.75)
    drape(XC + SCREEN_W / 2 + m + 0.35, AX1, Y_STAGE + 0.005, 5.95, AZN + 0.75)
    drape(AX0, AX1, 5.55, 6.55, AZN + 0.95, amp=0.05, period=0.28)
    bar(builder('aud_steel', 'aud_steel'), (AX0, 6.5, AZN + 0.95), (AX1, 6.5, AZN + 0.95), 0.03)
    # the lectern: a walnut body, a sloping top with a brass rail, a reading lamp and a microphone
    lx, lz = LECTERN
    wd = builder('aud_lectern', 'aud_stagedeck', tile=1.0)
    wd.box(lx, Y_STAGE + 0.03, lz, 0.70, 0.06, 0.52)
    wd.box(lx, Y_STAGE + 0.06 + 0.47, lz + 0.02, 0.60, 0.94, 0.40)
    # the top slopes down toward the speaker (-z)
    yl, yh = Y_STAGE + 1.03, Y_STAGE + 1.15
    hz = 0.25
    corners = [(lx - 0.36, yl - 0.04, lz - hz), (lx + 0.36, yl - 0.04, lz - hz), (lx + 0.36, yh - 0.04, lz + hz), (lx - 0.36, yh - 0.04, lz + hz),
               (lx - 0.36, yl, lz - hz), (lx + 0.36, yl, lz - hz), (lx + 0.36, yh, lz + hz), (lx - 0.36, yh, lz + hz)]
    # (bottom ring then top ring for quad_box: bottom = the slab's underside)
    quad_box(wd, corners)
    br.box(lx, yl + 0.02, lz - hz - 0.01, 0.70, 0.03, 0.02)
    st = builder('aud_steel', 'aud_steel')
    bar(st, (lx + 0.22, yh, lz + 0.18), (lx + 0.20, yh + 0.22, lz + 0.02), 0.012)
    bar(st, (lx + 0.20, yh + 0.22, lz + 0.02), (lx + 0.18, yh + 0.30, lz - 0.10), 0.012)
    lathe(st, lx + 0.18, lz - 0.12, [(yh + 0.28, 0.0), (yh + 0.28, 0.022), (yh + 0.33, 0.022), (yh + 0.34, 0.0)], n=10)
    bar(br, (lx - 0.25, yh, lz + 0.20), (lx - 0.25, yh + 0.26, lz + 0.20), 0.014)
    lathe(br, lx - 0.25, lz + 0.12, [(yh + 0.22, 0.0), (yh + 0.22, 0.07), (yh + 0.30, 0.05), (yh + 0.31, 0.0)], n=12)
    bar(br, (lx - 0.25, yh + 0.26, lz + 0.20), (lx - 0.25, yh + 0.27, lz + 0.12), 0.014)
    # the reading lamp's glowing underside; no fixture kind fits a 100 lm reading lamp, so it lights only the preview
    lp = builder('lamps', 'lamp_e')
    lp.face([P(lx - 0.25 + 0.055 * math.cos(2 * math.pi * i / 12), yh + 0.218, lz + 0.12 + 0.055 * math.sin(2 * math.pi * i / 12))
             for i in range(12)], D(0, -1, 0))
    PREVIEW_LIGHTS.append(('lectern', (lx - 0.25, yh + 0.17, lz + 0.10), (1.0, 0.85, 0.6), 15, None))
    sp = builder('spot__auditorium_f%d' % seat_yaw(0.0, 1.0), 'aud_mark')
    x, z = SPEAKER
    sp.face([P(x - 0.15, Y_STAGE + 0.01, z - 0.15), P(x + 0.15, Y_STAGE + 0.01, z - 0.15), P(x + 0.15, Y_STAGE + 0.01, z + 0.15), P(x - 0.15, Y_STAGE + 0.01, z + 0.15)], D(0, 1, 0))


# ---------------------------------------------------------------- outputs
def write_json(seat_count):
    with open(os.path.join(PIPE, 'lights.json'), 'w') as f:
        json.dump({'source': 'bl/auditorium.py', 'units': 'metres, three.js campus axes (y up)',
                   'lights': [{'name': k, 'type': 'AREA' if size else 'POINT', 'campus_pos_m': [round(v, 3) for v in pos], 'campus_dir': [0, -1, 0],
                               'blender_watts': w, 'color_linear': [round(c, 3) for c in col], 'radius_m': 0.06,
                               'area_size_m': list(size) if size else None} for (k, pos, col, w, size) in LIGHTS]}, f, indent=1)
    layout = {
        'source': 'bl/auditorium.py', 'units': 'campus metres (x east, y up, z south); Unreal = (x*100, z*100, y*100)',
        'venue': 'auditorium',
        'rooms': [
            {'id': 'foyer', 'label': 'The Foyer', 'x0': FX0, 'x1': FX1, 'z0': FZN, 'z1': FZS, 'floor_y': 0.0, 'ceiling_y': FH},
            {'id': 'auditorium', 'label': 'The Auditorium', 'x0': AX0, 'x1': AX1, 'z0': AZN, 'z1': AZS, 'floor_y': Y_ORCH,
             'entry_floor_y': 0.0, 'stage_y': Y_STAGE, 'ceiling_y': CEIL},
        ],
        'entries': [{'what': "Hall R's north door, into the foyer", 'x': round((HALL_DOOR[0] + HALL_DOOR[1]) / 2, 3), 'y': 0.0, 'z': -4.6, 'width': round(HALL_DOOR[1] - HALL_DOOR[0], 3)},
                    {'what': 'the portal from the foyer into the back of the auditorium', 'x': round(FXC, 3), 'y': 0.0, 'z': round((FZN + AZS) / 2, 3), 'width': round(PORTAL[1] - PORTAL[0], 3)}],
        'speaker_spot': {'x': SPEAKER[0], 'y': Y_STAGE, 'z': SPEAKER[1], 'yaw': seat_yaw(0.0, 1.0)},
        'lectern': {'x': LECTERN[0], 'z': LECTERN[1]},
        'screens': [{'name': 'screen__auditorium', 'centre': [XC, round(SCREEN_Y0 + SCREEN_H / 2, 3), round(SCREEN_Z, 3)],
                     'size_m': [SCREEN_W, SCREEN_H], 'faces': [0, 0, 1]}],
        'rows': {'centre': [XC, ZC], 'first_radius': RHO_0, 'depth': TD, 'rise': TR, 'count': NT, 'stage_front_radius': RHO_S, 'cross_aisle_radius': RHO_B},
        'camera': {'eye': [round(XC - 3.0, 3), 1.65, round(AZS - 1.2, 3)], 'target': [XC, 1.8, AZN]},
        'seats': seat_count, 'foyer_seats': 2,
    }
    with open(os.path.join(PIPE, 'layout.json'), 'w') as f:
        json.dump(layout, f, indent=1)


def export_glb():
    obs = [o for o in bpy.data.objects if o.type == 'MESH' and not o.get('preview_only')]
    select_only(obs)
    fp = os.path.join(PIPE, 'Auditorium.glb')
    bpy.ops.export_scene.gltf(filepath=fp, export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
                              export_texcoords=True, export_normals=True, export_tangents=True, export_materials='EXPORT',
                              export_image_format='AUTO', export_vertex_color='NONE', export_lights=False, export_cameras=False)
    print('exported', fp, os.path.getsize(fp), 'bytes', flush=True)


def add_preview_lights():
    for (kind, (x, y, z), col, watts, size) in LIGHTS + PREVIEW_LIGHTS:
        ld = bpy.data.lights.new(kind, 'POINT'); ld.shadow_soft_size = 0.1
        ld.energy = watts * 2.2; ld.color = col
        ob = bpy.data.objects.new(kind, ld); ob.location = P(x, y, z); ob['preview_only'] = 1
        bpy.context.scene.collection.objects.link(ob)
    w = bpy.data.worlds.new('World'); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.05
    m = MATS['screen_auditorium']
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Emission Color'].default_value = (0.18, 0.30, 0.42, 1); bsdf.inputs['Emission Strength'].default_value = 2.0


def render(name, eye, target, fov=70):
    sc = bpy.context.scene
    cam = bpy.data.cameras.new('Cam' + name); cam.lens_unit = 'FOV'; cam.angle = math.radians(fov)
    co = bpy.data.objects.new('Cam' + name, cam); sc.collection.objects.link(co)
    co.location = P(*eye)
    co.rotation_euler = (P(*target) - P(*eye)).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = co
    sc.render.resolution_x = 1280; sc.render.resolution_y = 800; sc.render.resolution_percentage = 100
    sc.cycles.samples = 24 if QUICK else 64
    sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 88
    sc.render.filepath = os.path.join(OUT, 'preview_%s.jpg' % name)
    t = time.time(); bpy.ops.render.render(write_still=True); print('preview', name, 'in %.0f s' % (time.time() - t), flush=True)


def main():
    t0 = time.time()
    sc = L.reset()
    make_textures()
    setup_materials()
    foyer()
    hall_walls()
    floors()
    seats_n = seats()
    stage_dressing()
    smooth_names = ('bronze', 'lamps', 'aud_drapes', 'foyer_capitals', 'aud_steel', 'aud_brass', 'aud_seatbacks', 'aud_seatshells')
    for name, b in B.items():
        if b.count == 0: continue
        ob = b.finish()
        if name in smooth_names: smooth(ob, 40.0)
    write_json(seats_n)
    obs = [o for o in sc.objects if o.type == 'MESH']
    print('objects', len(obs), 'seats', seats_n, 'lights', len(LIGHTS), 'tris ~', sum(len(o.data.polygons) * 2 for o in obs),
          'built in %.0f s' % (time.time() - t0), flush=True)
    export_glb()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'auditorium.blend'))
    if RENDER:
        add_preview_lights()
        for o in bpy.data.objects:                       # the speaker's mark is never shown, as in the engine
            if o.name.startswith('spot__'): o.hide_render = True
        views = {'entry': ((XC - 3.6, 1.62, AZS - 1.0), (XC + 0.5, 0.6, AZN), 80),
                 'stage': ((XC + 1.0, 0.2, -21.0), (XC, 2.2, AZN), 72),
                 'seats': ((LECTERN[0] - 0.3, Y_STAGE + 1.62, SPEAKER[1]), (XC - 2.0, -0.6, -18.0), 80),
                 'aisle': ((AX1 - 0.8, 1.0, -17.6), (AX1 - 1.4, -1.2, -27.5), 76),
                 'foyer': ((FXC + 0.6, 1.62, -5.6), (FXC - 0.4, 1.8, FZN), 76),
                 'foyer_s': ((FXC - 0.8, 1.62, -12.6), (FXC + 0.3, 2.0, FZS), 76)}
        want = [a.split('=')[1].split(',') for a in sys.argv if a.startswith('--views=')]
        for name in (want[0] if want else views):
            eye, target, fov = views[name]
            render(name, eye, target, fov=fov)
    print('done in %.0f s' % (time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
