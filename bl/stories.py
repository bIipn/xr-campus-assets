"""The Lost Stories cabin: a small timber story house at the end of the grounds' path, past the fountain, where a
visitor sits at a microphone and tells a story about the place; it is kept in their own voice, written down, and goes
on the wall inside (UWTAStoriesSubsystem, AWTAStoryMicActor, AWTAStoryWallActor). Built in Blender (bpy) at campus
coordinates, for Unreal.

The cabin faces the museum down the length of the grounds: the path from the fountain ends at its porch steps.
  outside   board-and-batten cedar walls on a fieldstone plinth, cream trim, a charcoal standing-seam roof whose front
            runs on over a porch on two posts, the gable over the porch carrying the sign (LOST STORIES), a sliding
            barn door hung open on its rail, a window either side of the door and one in each side wall, a lantern by
            the door, a slatted bench and a planter on the porch, four steps down to the path
  inside    knotty pine walls and a cathedral ceiling on exposed rafters and two collar ties; the recording nook on
            the east side (two armchairs facing across a small round table with a microphone on a desk stand for
            each, the recorder and headphones, a reading lamp, fabric acoustic panels and an ON AIR sign); the story
            board on the back wall (a framed dark green felt board the story wall's cards are drawn on) with a
            listening bench under it; bookcases of archive boxes either side of the west window; a round rug and a
            runner; two pendant lamps; the "how it works" sign by the door

Seats (seat__<id>_f<yaw>): stories_teller (the teller's armchair, facing the mic), stories_guest, stories_bench,
stories_porch. layout.json gives the story wall (its face's centre, yaw, size), the microphone (the pick spot over
the teller's mic and the teller's seat), the room's box, the place views and the bounds the navmesh should cover;
lights.json the pendants, the reading lamp, the wall wash on the board and the porch lantern.

Campus axes: x east, y up, z south.  Blender: X = x, Y = -z, Z = y.
Usage (Blender 5.2 or bpy 5.2.2):   python bl/stories.py [--render] [--quick] [--views=a,b]
Writes assets/stories/stories.blend, unreal/Pipeline/out/stories/Stories.glb, layout.json and lights.json, the
cabin's textures in assets/tex/stories_*.png, and preview renders. Then prepare_for_unreal.py -- Stories.
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
from library import P, D, Builder, bar, material, MATS, select_only, seat_yaw   # noqa: E402
from neo import face_uv, lathe, wall_with_openings, extrude_profile, blob   # noqa: E402
import museum as M                                               # noqa: E402  (ground_height, shared with the grounds)

SP = L.SP
OUT = os.path.join(SP, 'assets', 'stories')
PIPE = os.path.join(SP, 'unreal', 'Pipeline', 'out', 'stories')
TEX = os.path.join(SP, 'assets', 'tex')
FONTS = os.path.join(HERE, 'fonts')
RENDER = '--render' in sys.argv
QUICK = '--quick' in sys.argv
os.makedirs(OUT, exist_ok=True); os.makedirs(PIPE, exist_ok=True)
gh = M.ground_height

# ---------------------------------------------------------------- the plan (campus metres)
# The path from the fountain curves to x -4 and ends at z 70 (bl/exterior.py build_path); the cabin stands on its
# line, the porch steps coming down onto the path's end.
CX = -4.0                         # the cabin's centre line
XW, XE = -7.2, -0.8               # the side walls' outer faces
ZF, ZB = 72.0, 77.0               # the front and back walls' outer faces
T = 0.14                          # wall thickness
XI0, XI1, ZI0, ZI1 = XW + T, XE - T, ZF + T, ZB - T      # the room inside
FY = 0.45                         # the floor's top (and the porch deck's)
EAVE = FY + 2.75                  # the side walls' top, at their outer face
PITCH = math.radians(38.0)
TP = math.tan(PITCH)
RIDGE_U = EAVE + (CX - XW) * TP   # the roof's underside at the ridge
RT = 0.12                         # the roof's thickness
RTV = RT / math.cos(PITCH)        # ... measured straight up
OVER = 0.42                       # the eaves' overhang
OVER_B = 0.35                     # the overhang at the back
ZP = 70.35                        # the porch deck's front edge
ROOF_Z0 = 70.12                   # the roof's front edge, over the porch
STEP_RISE, STEP_RUN, STEPS = 0.15, 0.30, 4
WALL_Y0 = FY - 0.06               # the walls start a little under the floor, on the plinth

DOOR = (-4.55, -3.45, 2.2)        # x0, x1 and height above the floor
WIN_FRONT = [(-6.75, -5.85), (-1.95, -1.15)]
WIN_Y = (0.95, 2.2)               # sill and head above the floor
WIN_WEST = (74.1, 75.1)           # z range on the west wall
WIN_EAST = (72.7, 73.7)           # ... and the east wall

TABLE = (-2.2, 74.6)              # the recording nook's round table
TELLER = (-3.05, 74.6)            # the teller's armchair (faces +x, the table and the guest)
GUEST = (-1.42, 74.6)             # the guest's armchair (faces -x)
TABLE_TOP = FY + 0.66
BOARD = (CX, FY + 1.6, 2.6, 1.3)  # the story board on the back wall: centre x, centre y, felt width and height
BENCH = (CX, ZI1 - 0.30)          # the listening bench under it
LAMP = (-2.72, 75.32)             # the reading lamp at the teller's right hand, clear of the board's sight lines
PENDANTS = [(CX, 73.62), (CX, 75.3)]
SHELVES = [(72.55, 73.75), (75.45, 76.65)]   # the bookcases' z ranges on the west wall
PORCH_BENCH = (-6.3, ZF - 0.32)

UV01 = [(0, 0), (1, 0), (1, 1), (0, 1)]
LIGHTS = []


def setup_materials():
    material('st_cedar', color=(0.46, 0.25, 0.15, 1), roughness=0.7)                    # the siding's boards (stained cedar)
    material('st_batten', color=(0.40, 0.21, 0.12, 1), roughness=0.7)                   # the battens, a shade darker
    material('st_trim', color=(0.86, 0.83, 0.75, 1), roughness=0.55)                    # cream trim, casings, fascia
    material('st_roof', color=(0.075, 0.08, 0.085, 1), roughness=0.42, metallic=0.5)    # charcoal standing-seam steel
    material('st_stone', color=(0.47, 0.45, 0.42, 1), roughness=0.85)                   # the fieldstone plinth
    material('st_deck', color=(0.42, 0.35, 0.28, 1), roughness=0.75)                    # porch deck, steps, bench slats
    material('st_pine', color=(0.80, 0.62, 0.42, 1), roughness=0.6)                     # knotty pine walls and ceiling
    material('st_beam', color=(0.30, 0.18, 0.10, 1), roughness=0.6)                     # rafters, collar ties, frames
    material('st_floor', color=(0.55, 0.38, 0.24, 1), roughness=0.45)                   # the floor's wide planks
    material('st_walnut', color=(0.24, 0.14, 0.08, 1), roughness=0.4)                   # the table, the board's frame
    material('st_teal', color=(0.08, 0.22, 0.20, 1), roughness=0.85)                    # the teller's armchair
    material('st_rust', color=(0.45, 0.17, 0.09, 1), roughness=0.85)                    # the guest's armchair
    material('st_felt', color=(0.07, 0.13, 0.11, 1), roughness=0.95)                    # the story board's felt
    material('st_panel_a', color=(0.42, 0.20, 0.12, 1), roughness=0.95)                 # acoustic panels
    material('st_panel_b', color=(0.35, 0.40, 0.30, 1), roughness=0.95)
    material('st_panel_c', color=(0.62, 0.48, 0.20, 1), roughness=0.95)
    material('st_rug', color=(0.46, 0.20, 0.13, 1), roughness=0.95)
    material('st_runner', color=(0.20, 0.27, 0.28, 1), roughness=0.95)
    material('st_black', color=(0.025, 0.025, 0.028, 1), roughness=0.45)
    material('st_iron', color=(0.04, 0.04, 0.04, 1), roughness=0.5, metallic=0.6)
    material('st_brass', color=(0.75, 0.56, 0.28, 1), roughness=0.3, metallic=1.0)
    material('st_green', color=(0.11, 0.22, 0.17, 1), roughness=0.5)                    # the door, the pendants' shades
    material('st_card', color=(0.82, 0.76, 0.64, 1), roughness=0.85)                    # archive boxes' board
    material('st_pot', color=(0.55, 0.30, 0.20, 1), roughness=0.8)
    material('st_leaf', color=(0.12, 0.30, 0.12, 1), roughness=0.8)
    material('glass', color=(0.9, 0.95, 1.0, 1), roughness=0.05, alpha=0.12)
    material('st_sign', 'stories_sign', roughness=0.6)
    material('st_how', 'stories_how', roughness=0.7)
    material('st_spines', 'stories_spines', roughness=0.8)
    material('st_photo', 'stories_photo', roughness=0.5)
    material('st_onair_e', 'stories_onair', emission=True, emission_strength=0.9)
    material('st_bulb_e', color=(1, 1, 1, 1), emission=(1.0, 0.82, 0.55, 1), emission_strength=4.0)
    material('st_shade_e', color=(0.95, 0.88, 0.75, 1), emission=(1.0, 0.80, 0.55, 1), emission_strength=1.2)
    material('st_led_e', color=(1, 0.1, 0.05, 1), emission=(1.0, 0.1, 0.05, 1), emission_strength=6.0)
    material('st_mark', color=(0.2, 0.2, 0.2, 1), roughness=0.9)


B = {}
def builder(name, mat, tile=1.0, smooth_deg=None):
    if name not in B: B[name] = Builder(name, mat, tile=tile, lightmap=False, vcol=False, smooth=smooth_deg)
    return B[name]


# ---------------------------------------------------------------- geometry helpers
def circle(r, n=8):
    return [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def quad_facing(b, centre, f, w, h, uvs=None, tilt=0.0):
    """A textured rectangle centred at campus `centre` whose front faces the plan direction f = (fx, fz), w wide and
    h high, its top leaning back by `tilt` radians; uv (0, 0) at the viewer's bottom-left. A viewer looking at the
    front looks along -f, so their right is up x f = (fz, 0, -fx)."""
    fx, fz = f
    n0 = Vector((fx, 0.0, fz)).normalized()
    right = Vector((fz, 0.0, -fx)).normalized()
    upv = Vector((0.0, 1.0, 0.0))
    if tilt:
        upv = (upv * math.cos(tilt) - n0 * math.sin(tilt)).normalized()
    n = right.cross(upv).normalized()
    c = Vector(centre)
    pts = [c - right * w / 2 - upv * h / 2, c + right * w / 2 - upv * h / 2, c + right * w / 2 + upv * h / 2, c - right * w / 2 + upv * h / 2]
    face_uv(b, [P(*p) for p in pts], D(*n), uvs or UV01)


def disc(b, centre, n, r, k=24):
    C = P(*centre); N = D(*n).normalized()
    up = Vector((0, 0, 1))
    U = up.cross(N).normalized() if abs(N.z) < 0.9 else Vector((1, 0, 0))
    V = N.cross(U).normalized()
    for i in range(k):
        a0 = 2 * math.pi * i / k; a1 = 2 * math.pi * (i + 1) / k
        b.face([C, C + U * r * math.cos(a0) + V * r * math.sin(a0), C + U * r * math.cos(a1) + V * r * math.sin(a1)], N)


def cylinder(b, a, c, r, n=12, caps=True):
    """A round bar between campus points a and c."""
    A, C = Vector(a), Vector(c)
    ax = C - A; Lg = ax.length
    if Lg < 1e-7: return
    ax /= Lg
    up = Vector((0.0, 1.0, 0.0)) if abs(ax.y) < 0.95 else Vector((1.0, 0.0, 0.0))
    u = ax.cross(up).normalized(); v = ax.cross(u).normalized()
    ring = [u * math.cos(2 * math.pi * i / n) + v * math.sin(2 * math.pi * i / n) for i in range(n)]
    for i in range(n):
        j = (i + 1) % n
        q = [A + ring[i] * r, A + ring[j] * r, C + ring[j] * r, C + ring[i] * r]
        b.face([P(*p) for p in q], D(*((ring[i] + ring[j]) / 2)))
    if caps:
        b.face([P(*(A + ring[i] * r)) for i in reversed(range(n))], D(*(-ax)))
        b.face([P(*(C + ring[i] * r)) for i in range(n)], D(*ax))


def ball(b, c, r, rings=6, k=12):
    for j in range(rings):
        t0 = math.pi * j / rings - math.pi / 2; t1 = math.pi * (j + 1) / rings - math.pi / 2
        for i in range(k):
            a0 = 2 * math.pi * i / k; a1 = 2 * math.pi * (i + 1) / k
            def pt(t, a): return (c[0] + r * math.cos(t) * math.cos(a), c[1] + r * math.sin(t), c[2] + r * math.cos(t) * math.sin(a))
            q = [pt(t0, a0), pt(t0, a1), pt(t1, a1), pt(t1, a0)]
            mid = Vector(sum((Vector(p) for p in q), Vector((0, 0, 0))) / 4) - Vector(c)
            b.face([P(*p) for p in q], D(*mid.normalized()))


def roof_under(x):
    """The roof's underside over campus x (both slopes)."""
    return RIDGE_U - abs(x - CX) * TP


# ---------------------------------------------------------------- textures (PIL)
def font(names, size):
    from PIL import ImageFont
    for n in names:
        for p in (os.path.join(FONTS, n), '/usr/share/fonts/opentype/inter/' + n, '/usr/share/fonts/truetype/dejavu/' + n):
            if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()


CREAM = (238, 228, 205); FOREST = (24, 52, 40); BRASS = (190, 150, 80); INK = (40, 34, 26); RED = (150, 28, 22)


def centred(d, y, text, f, fill, W, tracking=0):
    if tracking:
        widths = [d.textlength(ch, font=f) for ch in text]
        total = sum(widths) + tracking * (len(text) - 1)
        x = (W - total) / 2
        for ch, w in zip(text, widths):
            d.text((x, y), ch, font=f, fill=fill); x += w + tracking
    else:
        w = d.textlength(text, font=f)
        d.text(((W - w) / 2, y), text, font=f, fill=fill)


def make_textures():
    from PIL import Image, ImageDraw, ImageFilter
    import random
    import clientpack
    words = clientpack.get('stories', {}) or {}
    cinzel = lambda s: font(['Cinzel.ttf'], s)
    serif_i = lambda s: font(['CormorantGaramond-MediumItalic.ttf'], s)
    serif_b = lambda s: font(['CormorantGaramond-Bold.ttf'], s)
    sans_b = lambda s: font(['Inter-Bold.otf', 'DejaVuSans-Bold.ttf'], s)

    # the gable sign: cream board, forest border and brass rules, the name in Cinzel
    W, H = 2048, 512
    im = Image.new('RGB', (W, H), CREAM); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W - 1, H - 1), outline=FOREST, width=34)
    d.rectangle((52, 52, W - 53, H - 53), outline=BRASS, width=6)
    centred(d, 92, words.get('sign', 'LOST STORIES'), cinzel(214), FOREST, W, tracking=26)
    d.line((W * 0.30, 352, W * 0.70, 352), fill=BRASS, width=5)
    centred(d, 372, words.get('sign_sub', 'tell a story about this place'), serif_i(82), INK, W)
    im.save(os.path.join(TEX, 'stories_sign.png'))

    # the "how it works" sign by the door: three steps on cream, framed in walnut by the geometry
    W, H = 1024, 1366
    im = Image.new('RGB', (W, H), CREAM); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W - 1, 210), fill=FOREST)
    centred(d, 52, words.get('how_kicker', 'LOST STORIES'), cinzel(86), CREAM, W, tracking=10)
    centred(d, 236, words.get('how_title', 'How it works'), serif_b(104), INK, W)
    steps = words.get('how_steps') or ['Sit at the microphone.', 'Press Record and tell it your own way.',
                                       'Keep it, and it joins the wall in your own voice.']
    y = 420
    for i, s in enumerate(steps[:3]):
        d.ellipse((90, y, 210, y + 120), fill=BRASS)
        centred_x = 150
        n = str(i + 1); f = sans_b(78)
        d.text((centred_x - d.textlength(n, font=f) / 2, y + 12), n, font=f, fill=CREAM)
        # wrap the line into the column right of the number
        f2 = serif_b(62); words_ = s.split(); line = ''; ly = y + 4
        for w_ in words_:
            test = (line + ' ' + w_).strip()
            if d.textlength(test, font=f2) > W - 330 and line:
                d.text((250, ly), line, font=f2, fill=INK); ly += 72; line = w_
            else:
                line = test
        d.text((250, ly), line, font=f2, fill=INK)
        y = max(y + 200, ly + 110)
    d.line((90, H - 220, W - 90, H - 220), fill=BRASS, width=4)
    note = words.get('how_note', 'A librarian looks after every story kept here.')
    centred(d, H - 190, note, serif_i(58), INK, W)
    im.save(os.path.join(TEX, 'stories_how.png'))

    # ON AIR: red glass with the words lit
    W, H = 512, 192
    im = Image.new('RGB', (W, H), (40, 6, 5)); d = ImageDraw.Draw(im)
    d.rectangle((10, 10, W - 11, H - 11), outline=(90, 14, 10), width=6)
    centred(d, 38, 'ON AIR', sans_b(104), (255, 70, 50), W, tracking=8)
    im = im.filter(ImageFilter.GaussianBlur(0.8))
    im.save(os.path.join(TEX, 'stories_onair.png'))

    # book spines (top half) and archive box labels (bottom half)
    r = random.Random(7)
    W, H = 1024, 1024
    im = Image.new('RGB', (W, H), (70, 50, 35)); d = ImageDraw.Draw(im)
    x = 0
    cols = [(110, 40, 32), (34, 60, 52), (150, 120, 70), (60, 44, 70), (40, 52, 86), (120, 90, 50), (90, 30, 28), (200, 180, 140)]
    while x < W:
        w = r.randint(22, 46); c = r.choice(cols)
        d.rectangle((x, 0, x + w - 2, H // 2 - 2), fill=c)
        for yb in (40, H // 2 - 60):
            d.rectangle((x + 3, yb, x + w - 5, yb + 6), fill=BRASS)
        x += w
    lab = sans_b(40); small = serif_i(38)
    for k in range(4):
        x0 = (k % 2) * W // 2; y0 = H // 2 + (k // 2) * H // 4
        d.rectangle((x0, y0, x0 + W // 2 - 1, y0 + H // 4 - 1), fill=(214, 200, 170))
        d.rectangle((x0 + 60, y0 + 50, x0 + W // 2 - 60, y0 + H // 4 - 50), fill=(246, 240, 226), outline=INK, width=3)
        tag = ['ORAL HISTORIES', 'LETTERS', 'PHOTOGRAPHS', 'RECORDINGS'][k]
        d.text((x0 + (W // 2 - d.textlength(tag, font=lab)) / 2, y0 + 70), tag, font=lab, fill=INK)
        sub = ['box %d' % (k + 3), 'donated', 'unsorted', 'tapes'][k]
        d.text((x0 + (W // 2 - d.textlength(sub, font=small)) / 2, y0 + 128), sub, font=small, fill=INK)
    im.save(os.path.join(TEX, 'stories_spines.png'))

    # an old photograph: a sepia street of shopfronts under hills, in a cream mount (made up, like the rest)
    W, H = 768, 576
    im = Image.new('RGB', (W, H), (232, 222, 198)); d = ImageDraw.Draw(im)
    px0, py0, px1, py1 = 48, 48, W - 48, H - 48
    for yy in range(py0, py1):
        t = (yy - py0) / (py1 - py0)
        d.line((px0, yy, px1, yy), fill=(int(196 - 50 * t), int(176 - 50 * t), int(140 - 45 * t)))
    hz = py0 + int((py1 - py0) * 0.48)
    pts = [(px0, hz)] + [(px0 + i * 12, hz - 40 - int(28 * math.sin(i / 7.0)) - r.randint(0, 6)) for i in range((px1 - px0) // 12 + 1)] + [(px1, hz)]
    d.polygon(pts, fill=(150, 128, 98))
    x = px0
    while x < px1:
        w = r.randint(60, 110); h = r.randint(70, 130)
        d.rectangle((x, hz + 60 - h, x + w - 6, py1 - 70), fill=(120, 98, 72))
        for wx in range(x + 10, x + w - 20, 26):
            d.rectangle((wx, hz + 75 - h, wx + 12, hz + 95 - h), fill=(84, 66, 48))
        d.rectangle((x + 8, py1 - 130, x + w - 16, py1 - 74), fill=(70, 54, 40))
        x += w
    d.rectangle((px0, py1 - 70, px1, py1), fill=(170, 150, 118))
    im = im.filter(ImageFilter.GaussianBlur(1.2))
    d = ImageDraw.Draw(im)
    d.rectangle((px0, py0, px1, py1), outline=(120, 100, 76), width=2)
    im.save(os.path.join(TEX, 'stories_photo.png'))


# ---------------------------------------------------------------- the shell
def wall_faces(origin, U, N, w, h, openings, outer, inner, t=T, gable=None, inner_gable=None):
    """One wall: its outer face (builder `outer`, at origin + N t) and inner face (`inner`, at origin) with the
    openings [(u0, u1, v0, v1)], the reveals round each opening, and (gable = (apex_u, apex_v)) a triangle above."""
    V = (0.0, 1.0, 0.0)
    # outer face: origin on the inner plane, facing out along N
    wall_with_openings(outer, origin, U, V, N, t, w, h, openings, solid=False)
    # inner face: from the outer plane looking in
    o2 = (origin[0] + N[0] * t, origin[1], origin[2] + N[2] * t)
    Ni = (-N[0], -N[1], -N[2])
    hi = h if inner_gable is None else inner_gable[2]
    wall_with_openings(inner, o2, U, V, Ni, t, w, hi, openings, solid=False)
    if gable:
        au, av = gable
        extrude_profile(outer, [(0, h), (w, h), (au, av)], origin, U, V, N, t, front=True, back=False, sides=False)
    if inner_gable:
        u0, u1, v_base, au, av = inner_gable
        extrude_profile(inner, [(u0, v_base), (u1, v_base), (au, av)], o2, U, V, Ni, t, front=True, back=False, sides=False)
    # reveals: the four faces inside each opening, in trim
    tr = builder('st_trim', 'st_trim')
    def W(u, v, s): return (origin[0] + U[0] * u + N[0] * s, origin[1] + v, origin[2] + U[2] * u + N[2] * s)
    for (u0, u1, v0, v1) in openings:
        for (a, c, nrm) in (((u0, v0), (u0, v1), U), ((u1, v1), (u1, v0), (-U[0], 0, -U[2])),
                            ((u0, v1), (u1, v1), (0, -1, 0)), ((u1, v0), (u0, v0), (0, 1, 0))):
            if c == a: continue
            pts = [W(a[0], a[1], 0), W(c[0], c[1], 0), W(c[0], c[1], t), W(a[0], a[1], t)]
            tr.face([P(*p) for p in pts], D(*nrm))


def build_shell():
    sid = builder('st_cedar', 'st_cedar', tile=1.2)
    pine = builder('st_pine', 'st_pine', tile=1.2)
    h = EAVE - WALL_Y0
    ib = FY - WALL_Y0                                  # the inner faces start at the floor
    dz0, dz1, dh = DOOR
    # openings in the front wall, u east from XW, v up from WALL_Y0
    front_open = [(dz0 - XW, dz1 - XW, 0.0, ib + dh)] + [(a - XW, b - XW, ib + WIN_Y[0], ib + WIN_Y[1]) for (a, b) in WIN_FRONT]
    apex = (CX - XW, RIDGE_U - WALL_Y0)
    in_base = EAVE + T * TP - WALL_Y0                  # where the inner faces meet the roof's underside at the walls
    # front wall: inner plane z = ZF + T, outward -z
    wall_faces((XW, WALL_Y0, ZF + T), (1, 0, 0), (0, 0, -1), XE - XW, h, front_open, sid, pine,
               gable=apex, inner_gable=(T, XE - XW - T, in_base, apex[0], apex[1]))
    # back wall: inner plane z = ZB - T, outward +z (u runs west from XE so the outer face reads the right way)
    wall_faces((XE, WALL_Y0, ZB - T), (-1, 0, 0), (0, 0, 1), XE - XW, h, [], sid, pine,
               gable=(XE - CX, RIDGE_U - WALL_Y0), inner_gable=(T, XE - XW - T, in_base, XE - CX, RIDGE_U - WALL_Y0))
    # side walls between the front and back walls: west (outward -x, u south from ZF + T), east (outward +x)
    w_open = [(WIN_WEST[0] - (ZF + T), WIN_WEST[1] - (ZF + T), ib + WIN_Y[0], ib + WIN_Y[1])]
    wall_faces((XW + T, WALL_Y0, ZF + T), (0, 0, 1), (-1, 0, 0), ZB - ZF - 2 * T, h, w_open, sid, pine)
    e_open = [(WIN_EAST[0] - (ZF + T), WIN_EAST[1] - (ZF + T), ib + WIN_Y[0], ib + WIN_Y[1])]
    wall_faces((XE - T, WALL_Y0, ZF + T), (0, 0, 1), (1, 0, 0), ZB - ZF - 2 * T, h, e_open, sid, pine)
    # the side walls' inner faces rise to the roof line at the wall: one strip on top of each
    for x in (XI0, XI1):
        n = (1, 0, 0) if x == XI0 else (-1, 0, 0)
        pine.face([P(x, EAVE, ZI0), P(x, EAVE, ZI1), P(x, EAVE + T * TP, ZI1), P(x, EAVE + T * TP, ZI0)], D(*n))

    # battens over the boards, every 0.32 m, stopping at the openings and under the roof line
    bt = builder('st_batten', 'st_batten', tile=1.2)
    def battens(run, fixed, axis, out, holes, top_of):
        a, b_ = run
        u = a + 0.16
        while u < b_ - 0.1:
            spans = [(WALL_Y0 + 0.02, top_of(u))]
            for (h0, h1, y0, y1) in holes:
                if h0 - 0.03 < u < h1 + 0.03:
                    nxt = []
                    for (s0, s1) in spans:
                        if y0 > s0: nxt.append((s0, min(s1, y0 - 0.1)))
                        if y1 < s1: nxt.append((max(s0, y1 + 0.1), s1))
                    spans = nxt
            for (s0, s1) in spans:
                if s1 - s0 < 0.05: continue
                if axis == 'x':
                    bt.box(u, (s0 + s1) / 2, fixed + out * 0.011, 0.05, s1 - s0, 0.022, faces='xXyY' + ('z' if out < 0 else 'Z'))
                else:
                    bt.box(fixed + out * 0.011, (s0 + s1) / 2, u, 0.022, s1 - s0, 0.05, faces='zZyY' + ('x' if out < 0 else 'X'))
            u += 0.32
    gable_top = lambda u: min(roof_under(u) - 0.03, EAVE + (CX - XW) * TP)
    fr_holes = [(dz0 - 0.1, dz1 + 0.1, WALL_Y0, FY + dh + 0.12)] + [(a - 0.1, b + 0.1, FY + WIN_Y[0] - 0.12, FY + WIN_Y[1] + 0.12) for (a, b) in WIN_FRONT]
    battens((XW, XE), ZF, 'x', -1, fr_holes, gable_top)
    battens((XW, XE), ZB, 'x', 1, [], gable_top)
    battens((ZF, ZB), XW, 'z', -1, [(WIN_WEST[0] - 0.1, WIN_WEST[1] + 0.1, FY + WIN_Y[0] - 0.12, FY + WIN_Y[1] + 0.12)], lambda u: EAVE - 0.03)
    battens((ZF, ZB), XE, 'z', 1, [(WIN_EAST[0] - 0.1, WIN_EAST[1] + 0.1, FY + WIN_Y[0] - 0.12, FY + WIN_Y[1] + 0.12)], lambda u: EAVE - 0.03)

    # corner boards and a belly band of trim just above the plinth
    tr = builder('st_trim', 'st_trim')
    for (x, z) in ((XW, ZF), (XE, ZF), (XW, ZB), (XE, ZB)):
        sx = -1 if x == XW else 1; sz = -1 if z == ZF else 1
        tr.box(x + sx * 0.012, (WALL_Y0 + EAVE) / 2, z - sz * 0.07, 0.03, EAVE - WALL_Y0, 0.16)
        tr.box(x - sx * 0.07, (WALL_Y0 + EAVE) / 2, z + sz * 0.012, 0.16, EAVE - WALL_Y0, 0.03)
    # frieze boards under the eaves along the side walls
    for x, s in ((XW, -1), (XE, 1)):
        tr.box(x + s * 0.012, EAVE - 0.09, (ZF + ZB) / 2, 0.025, 0.18, ZB - ZF + 0.06)

    # the floor inside and the door's threshold
    fl = builder('st_floor', 'st_floor', tile=1.6)
    fl.box(CX, FY - 0.03, (ZI0 + ZI1) / 2, XI1 - XI0, 0.06, ZI1 - ZI0, faces='Y')
    fl.box((dz0 + dz1) / 2, FY - 0.03, ZF + T / 2, dz1 - dz0, 0.06, T, faces='Y')
    tr.box((dz0 + dz1) / 2, FY + 0.006, ZF + T / 2, dz1 - dz0, 0.012, T + 0.04, faces='Yzx X'.replace(' ', ''))

    # the fieldstone plinth under the side and back walls (the porch covers the front)
    st = builder('st_stone', 'st_stone', tile=1.0)
    def plinth(x0, x1, z0, z1):
        lo = min(gh(x, z) for x in (x0, x1) for z in (z0, z1)) - 0.12
        st.box((x0 + x1) / 2, (lo + WALL_Y0 + 0.02) / 2, (z0 + z1) / 2, x1 - x0, WALL_Y0 + 0.02 - lo, z1 - z0, faces='xXzZY')
    plinth(XW - 0.05, XW + 0.2, ZF, ZB + 0.05)
    plinth(XE - 0.2, XE + 0.05, ZF, ZB + 0.05)
    plinth(XW - 0.05, XE + 0.05, ZB - 0.2, ZB + 0.05)


def build_roof():
    rf = builder('st_roof', 'st_roof', tile=1.0)
    so = builder('st_pine', 'st_pine', tile=1.2)
    tr = builder('st_trim', 'st_trim')
    bm = builder('st_beam', 'st_beam', tile=1.0)
    z0, z1 = ROOF_Z0, ZB + OVER_B
    for s in (-1, 1):
        xe = CX + s * (CX - XW + OVER)                 # the eave's edge
        ye = roof_under(xe)
        top = [(CX, RIDGE_U + RTV, z0), (xe, ye + RTV, z0), (xe, ye + RTV, z1), (CX, RIDGE_U + RTV, z1)]
        bot = [(CX, RIDGE_U, z0), (xe, ye, z0), (xe, ye, z1), (CX, RIDGE_U, z1)]
        up = Vector((s * math.sin(PITCH), math.cos(PITCH), 0.0))
        rf.face([P(*p) for p in top], D(*up))
        so.face([P(*p) for p in bot], D(*(-up)))
        # fascia along the eave and rake boards along the front and back edges, in trim
        tr.face([P(xe, ye - 0.04, z0), P(xe, ye - 0.04, z1), P(xe, ye + RTV + 0.02, z1), P(xe, ye + RTV + 0.02, z0)], D(s, 0, 0))
        for z, nz in ((z0, -1), (z1, 1)):
            bar(tr, (CX, RIDGE_U + RTV / 2, z + nz * 0.012), (xe, ye + RTV / 2, z + nz * 0.012), 0.025, RTV + 0.1)
        # standing seams down the slope
        z = z0 + 0.22
        while z < z1 - 0.15:
            bar(rf, (CX - s * 0.06, RIDGE_U + RTV + 0.018, z), (xe + s * 0.02, ye + RTV + 0.018, z), 0.022, 0.036)
            z += 0.46
        # rafters under the boards, from the ridge out to the eave (their tails show under the overhang)
        z = ZF + 0.30
        while z < ZB - 0.2:
            bar(bm, (CX - s * 0.08, RIDGE_U - 0.08, z), (xe + s * 0.02, ye - 0.08, z), 0.06, 0.16)
            z += 0.62
        # rafters over the porch too
        for zz in (ROOF_Z0 + 0.25, ROOF_Z0 + 0.95, ZF - 0.12):
            bar(bm, (CX - s * 0.08, RIDGE_U - 0.08, zz), (xe + s * 0.02, ye - 0.08, zz), 0.06, 0.16)
    # the ridge cap, the ridge beam under it and two collar ties inside
    rf.box(CX, RIDGE_U + RTV + 0.03, (z0 + z1) / 2, 0.26, 0.06, z1 - z0)
    bm.box(CX, RIDGE_U - 0.13, (z0 + z1) / 2, 0.14, 0.26, z1 - z0)
    for z in (73.3, 75.75):
        y = FY + 3.45
        half = (RIDGE_U - y) / TP
        bm.box(CX, y, z, 2 * half, 0.18, 0.10)


def build_porch():
    dk = builder('st_deck', 'st_deck', tile=1.0)
    tr = builder('st_trim', 'st_trim')
    bm = builder('st_beam', 'st_beam')
    # deck boards running east-west, the front one with a nosing
    n = 12
    depth = ZF - ZP
    for i in range(n):
        za = ZP + depth * i / n; zb = ZP + depth * (i + 1) / n - 0.006
        dk.box(CX, FY - 0.02, (za + zb) / 2, XE - XW + 0.04, 0.04, zb - za)
    # skirting from the deck down to the ground, front and sides
    sk = builder('st_skirt', 'st_beam', tile=1.0)
    lo = min(gh(x, z) for x in (XW, XE) for z in (ZP, ZF)) - 0.1
    sk.box(CX, (lo + FY - 0.04) / 2, ZP + 0.02, XE - XW, FY - 0.04 - lo, 0.04, faces='zZ')
    for x in (XW + 0.02, XE - 0.02):
        sk.box(x, (lo + FY - 0.04) / 2, (ZP + ZF) / 2, 0.04, FY - 0.04 - lo, ZF - ZP, faces='xX')
    # two posts with knee braces, the beam across them, the porch gable over it
    py = (FY, EAVE - 0.22)
    for x in (XW + 0.14, XE - 0.14):
        tr.box(x, (py[0] + py[1]) / 2, ZP + 0.14, 0.16, py[1] - py[0], 0.16)
        tr.box(x, FY + 0.04, ZP + 0.14, 0.22, 0.08, 0.22)
        s = 1 if x < CX else -1
        bar(tr, (x + s * 0.06, py[1] - 0.55, ZP + 0.14), (x + s * 0.56, py[1] - 0.02, ZP + 0.14), 0.08, 0.08)
    tr.box(CX, EAVE - 0.11, ZP + 0.14, XE - XW + 0.1, 0.22, 0.18)
    # the gable over the porch: boards, battens and the sign
    zg = ROOF_Z0 + 0.10
    gw = builder('st_cedar', 'st_cedar', tile=1.2)
    apex_v = RIDGE_U - 0.02
    def half_at(y): return max(0.0, (apex_v - y) / TP)
    pts = [(-half_at(EAVE), EAVE), (half_at(EAVE), EAVE), (0.0, apex_v)]
    for f_off, nz in ((0.0, -1), (0.03, 1)):
        poly = [P(CX + u, v, zg + f_off) for (u, v) in pts]
        gw.face(poly, D(0, 0, nz))
    bt = builder('st_batten', 'st_batten', tile=1.2)
    u = -half_at(EAVE) + 0.16
    while u < half_at(EAVE) - 0.1:
        y1 = EAVE + (half_at(EAVE) - abs(u)) * TP - 0.04
        if y1 > EAVE + 0.06:
            bt.box(CX + u, (EAVE + y1) / 2, zg - 0.011, 0.05, y1 - EAVE, 0.022, faces='xXyYz')
        u += 0.32
    sg = builder('st_sign', 'st_sign')
    sw, sh = 2.9, 0.725
    sy = EAVE + 0.62
    tr.box(CX, sy, zg - 0.035, sw + 0.12, sh + 0.12, 0.04)
    quad_facing(sg, (CX, sy, zg - 0.057), (0, -1), sw, sh)
    # steps down to the path's end
    for k in range(1, STEPS + 1):
        top = FY - k * STEP_RISE
        z0, z1 = ZP - k * STEP_RUN, ZP - (k - 1) * STEP_RUN
        lo = min(gh(CX, z0), gh(CX, z1)) - 0.25
        dk.box(CX, (lo + top) / 2, (z0 + z1) / 2, 2.4, top - lo, z1 - z0 + 0.02)
    # porch side railings: a top and bottom rail with square balusters
    for x in (XW + 0.14, XE - 0.14):
        za, zb = ZP + 0.24, ZF - 0.04
        tr.box(x, FY + 0.92, (za + zb) / 2, 0.08, 0.06, zb - za)
        tr.box(x, FY + 0.14, (za + zb) / 2, 0.06, 0.05, zb - za)
        z = za + 0.08
        while z < zb - 0.04:
            tr.box(x, FY + 0.53, z, 0.035, 0.74, 0.035)
            z += 0.12


def build_openings():
    tr = builder('st_trim', 'st_trim')
    gl = builder('glass', 'glass')
    fr = builder('st_frame', 'st_trim')
    def window(axis, fixed, out, a, b_):
        y0, y1 = FY + WIN_Y[0], FY + WIN_Y[1]
        mid = fixed + out * (-T / 2)                   # the wall's middle plane (out points outward)
        if axis == 'x':                                # a wall facing out along z (a, b_ along x)
            # outside casing and sill
            tr.box((a + b_) / 2, y1 + 0.05, fixed + out * 0.015, b_ - a + 0.24, 0.10, 0.03)
            tr.box((a + b_) / 2, y1 + 0.115, fixed + out * 0.03, b_ - a + 0.30, 0.03, 0.06)
            for x in (a - 0.05, b_ + 0.05):
                tr.box(x, (y0 + y1) / 2, fixed + out * 0.015, 0.10, y1 - y0, 0.03)
            tr.box((a + b_) / 2, y0 - 0.03, fixed + out * 0.04, b_ - a + 0.20, 0.05, 0.10)
            # the sash frame, a mullion and a muntin, the glass
            for x in (a + 0.03, b_ - 0.03, (a + b_) / 2):
                fr.box(x, (y0 + y1) / 2, mid, 0.05, y1 - y0, 0.06)
            for y in (y0 + 0.03, y1 - 0.03, (y0 + y1) / 2):
                fr.box((a + b_) / 2, y, mid, b_ - a, 0.05, 0.06)
            quad_facing(gl, ((a + b_) / 2, (y0 + y1) / 2, mid), (0, out), b_ - a, y1 - y0)
            # inside: a stool and casing
            tr.box((a + b_) / 2, y0 - 0.01, fixed - out * (T + 0.04), b_ - a + 0.16, 0.03, 0.10)
            for x in (a - 0.04, b_ + 0.04):
                tr.box(x, (y0 + y1) / 2, fixed - out * (T + 0.01), 0.08, y1 - y0 + 0.08, 0.02)
            tr.box((a + b_) / 2, y1 + 0.04, fixed - out * (T + 0.01), b_ - a + 0.16, 0.08, 0.02)
        else:                                          # a wall facing out along x (a, b_ along z)
            tr.box(fixed + out * 0.015, y1 + 0.05, (a + b_) / 2, 0.03, 0.10, b_ - a + 0.24)
            tr.box(fixed + out * 0.03, y1 + 0.115, (a + b_) / 2, 0.06, 0.03, b_ - a + 0.30)
            for z in (a - 0.05, b_ + 0.05):
                tr.box(fixed + out * 0.015, (y0 + y1) / 2, z, 0.03, y1 - y0, 0.10)
            tr.box(fixed + out * 0.04, y0 - 0.03, (a + b_) / 2, 0.10, 0.05, b_ - a + 0.20)
            for z in (a + 0.03, b_ - 0.03, (a + b_) / 2):
                fr.box(mid, (y0 + y1) / 2, z, 0.06, y1 - y0, 0.05)
            for y in (y0 + 0.03, y1 - 0.03, (y0 + y1) / 2):
                fr.box(mid, y, (a + b_) / 2, 0.06, 0.05, b_ - a)
            quad_facing(gl, (mid, (y0 + y1) / 2, (a + b_) / 2), (out, 0), b_ - a, y1 - y0)
            tr.box(fixed - out * (T + 0.04), y0 - 0.01, (a + b_) / 2, 0.10, 0.03, b_ - a + 0.16)
            for z in (a - 0.04, b_ + 0.04):
                tr.box(fixed - out * (T + 0.01), (y0 + y1) / 2, z, 0.02, y1 - y0 + 0.08, 0.08)
            tr.box(fixed - out * (T + 0.01), y1 + 0.04, (a + b_) / 2, 0.02, 0.08, b_ - a + 0.16)
    for (a, b_) in WIN_FRONT:
        window('x', ZF, -1, a, b_)
    window('z', XW, -1, *WIN_WEST)
    window('z', XE, 1, *WIN_EAST)

    # the door: casing outside and in, the barn door slid open to the east on its rail
    dz0, dz1, dh = DOOR
    top = FY + dh
    for (z, s) in ((ZF - 0.015, 1), (ZF + T + 0.01, -1)):
        tr.box((dz0 + dz1) / 2, top + 0.06, z, dz1 - dz0 + 0.24, 0.12, 0.03)
        for x in (dz0 - 0.06, dz1 + 0.06):
            tr.box(x, (FY + top) / 2, z, 0.12, dh, 0.03)
    iron = builder('st_iron', 'st_iron')
    rail_y = top + 0.22
    iron.box((dz0 + dz1) / 2 + 0.6, rail_y, ZF - 0.05, 2.7, 0.05, 0.02)
    door = builder('st_door', 'st_green', tile=1.0)
    d0, d1 = dz1 + 0.04, dz1 + 0.04 + (dz1 - dz0) + 0.08
    dzc = ZF - 0.09
    door.box((d0 + d1) / 2, FY + (dh + 0.1) / 2 + 0.02, dzc, d1 - d0, dh + 0.1, 0.05)
    # its boards' frame and a Z brace, a shade darker, and the hangers' wheels on the rail
    for y in (FY + 0.12, FY + dh - 0.02, FY + dh / 2 + 0.06):
        door.box((d0 + d1) / 2, y, dzc - 0.03, d1 - d0 - 0.02, 0.10, 0.012)
    for x in (d0 + 0.05, d1 - 0.05):
        door.box(x, FY + dh / 2 + 0.06, dzc - 0.03, 0.10, dh - 0.12, 0.012)
    bar(door, (d0 + 0.1, FY + 0.17, dzc - 0.036), (d1 - 0.1, FY + dh / 2, dzc - 0.036), 0.09, 0.012)
    for x in (d0 + 0.18, d1 - 0.18):
        iron.box(x, rail_y - 0.12, ZF - 0.08, 0.04, 0.26, 0.012)
        cylinder(iron, (x, rail_y + 0.03, ZF - 0.055), (x, rail_y + 0.03, ZF - 0.035), 0.05, n=12)
    iron.box(d1 - 0.12, FY + 1.05, dzc - 0.045, 0.03, 0.30, 0.03)

    # the lantern by the door, west of it
    lx, ly, lz = dz0 - 0.38, FY + 1.95, ZF - 0.13
    iron.box(lx, ly + 0.05, ZF - 0.03, 0.08, 0.16, 0.04)
    iron.box(lx, ly + 0.12, (ZF - 0.03 + lz) / 2, 0.03, 0.03, 0.12)
    bulb = builder('st_bulb_e', 'st_bulb_e')
    bulb.box(lx, ly - 0.02, lz, 0.14, 0.2, 0.14)
    for sx in (-1, 1):
        for sz in (-1, 1):
            iron.box(lx + sx * 0.08, ly - 0.02, lz + sz * 0.08, 0.02, 0.24, 0.02)
    iron.box(lx, ly + 0.11, lz, 0.2, 0.03, 0.2)
    iron.box(lx, ly - 0.14, lz, 0.18, 0.03, 0.18)
    LIGHTS.append(('porch', (lx, ly - 0.02, lz), (1.0, 0.80, 0.55), 40, None))


# ---------------------------------------------------------------- inside
def armchair(cx, cz, f, fabric, seat_name):
    """An upholstered armchair facing the plan direction f (unit, along x or z): a base, a cushion (its own mesh, the
    seat), a back and two arms on short walnut legs."""
    fb = builder('st_chair_' + fabric, fabric, tile=0.6)
    lg = builder('st_walnut', 'st_walnut')
    fx, fz = f
    ry = math.atan2(-fz, fx)                           # local +x along f
    def at(u, w):                                      # u along f, w to the chair's left
        return (cx + fx * u - fz * w, cz + fz * u + fx * w)
    seat_y = FY + 0.44
    bx, bz = at(0.0, 0.0)
    fb.box(bx, FY + 0.27, bz, 0.66, 0.30, 0.66, ry=ry)                     # the base
    kx, kz = at(0.04, 0.0)
    cush = builder(seat_name, fabric, tile=0.6)
    cush.box(kx, seat_y - 0.03, kz, 0.56, 0.14, 0.54, ry=ry)              # the cushion
    ax, az = at(-0.27, 0.0)
    fb.box(ax, FY + 0.62, az, 0.14, 0.70, 0.78, ry=ry)                     # the back
    for w in (-1, 1):
        rx, rz = at(0.0, w * 0.33)
        fb.box(rx, FY + 0.48, rz, 0.66, 0.42, 0.13, ry=ry)                 # the arms
    for (u, w) in ((0.26, 0.28), (0.26, -0.28), (-0.26, 0.28), (-0.26, -0.28)):
        x, z = at(u, w)
        lg.box(x, FY + 0.06, z, 0.05, 0.12, 0.05)


def mic(x, z, toward, h=0.30):
    """A microphone on a desk stand on the table: a round base, a pole, a short boom out toward the speaker and the
    mic in a shock mount, a foam ball on its head."""
    bk = builder('st_black', 'st_black', smooth_deg=40)
    ir = builder('st_iron', 'st_iron')
    y0 = TABLE_TOP
    lathe(ir, x, z, [(y0, 0.075), (y0 + 0.012, 0.075), (y0 + 0.02, 0.02)], n=20)
    cylinder(ir, (x, y0 + 0.02, z), (x, y0 + h, z), 0.008, n=8)
    tx, tz = toward
    end = (x + tx * 0.16, y0 + h + 0.04, z + tz * 0.16)
    cylinder(ir, (x, y0 + h, z), end, 0.007, n=8)
    head = (end[0] + tx * 0.08, end[1] + 0.01, end[2] + tz * 0.08)
    cylinder(bk, (end[0] - tx * 0.03, end[1] - 0.005, end[2] - tz * 0.03), head, 0.024, n=12)
    ball(bk, (head[0] + tx * 0.02, head[1] + 0.002, head[2] + tz * 0.02), 0.034)
    return head


def build_nook():
    wl = builder('st_walnut', 'st_walnut', smooth_deg=40)
    tx, tz = TABLE
    lathe(wl, tx, tz, [(FY, 0.24), (FY + 0.03, 0.24), (FY + 0.05, 0.05), (TABLE_TOP - 0.06, 0.04), (TABLE_TOP - 0.05, 0.12),
                        (TABLE_TOP - 0.03, 0.36), (TABLE_TOP, 0.36)], n=32)
    armchair(*TELLER, (1, 0), 'st_teal', 'seat__stories_teller_f%d' % seat_yaw(1.0, 0.0))
    armchair(*GUEST, (-1, 0), 'st_rust', 'seat__stories_guest_f%d' % seat_yaw(-1.0, 0.0))
    teller_mic = mic(tx - 0.2, tz - 0.06, (-0.97, 0.24))
    mic(tx + 0.2, tz + 0.06, (0.97, -0.24))
    # the recorder between them, its record light on, and a pair of headphones
    bk = builder('st_black', 'st_black', smooth_deg=40)
    bk.box(tx + 0.02, TABLE_TOP + 0.025, tz + 0.12, 0.16, 0.05, 0.09)
    led = builder('st_led_e', 'st_led_e')
    led.box(tx - 0.03, TABLE_TOP + 0.052, tz + 0.10, 0.012, 0.006, 0.012)
    for s in (-1, 1):
        cylinder(bk, (tx + 0.06 + s * 0.07, TABLE_TOP + 0.005, tz - 0.14), (tx + 0.06 + s * 0.07, TABLE_TOP + 0.04, tz - 0.14), 0.04, n=14)
    bar(bk, (tx - 0.01, TABLE_TOP + 0.045, tz - 0.14), (tx + 0.13, TABLE_TOP + 0.045, tz - 0.14), 0.02, 0.01)
    # the reading lamp beside the teller
    lx, lz = LAMP
    ir = builder('st_iron', 'st_iron')
    lathe(ir, lx, lz, [(FY, 0.15), (FY + 0.02, 0.15), (FY + 0.03, 0.02)], n=20)
    cylinder(ir, (lx, FY + 0.03, lz), (lx, FY + 1.42, lz), 0.012, n=8)
    sh = builder('st_shade_e', 'st_shade_e', smooth_deg=50)
    lathe(sh, lx, lz, [(FY + 1.36, 0.22), (FY + 1.62, 0.17)], n=24, cap_top=False)
    LIGHTS.append(('lamp', (lx, FY + 1.42, lz), (1.0, 0.78, 0.52), 25, None))
    # the round rug under the nook and a runner from the door to the board
    rg = builder('st_rug', 'st_rug', tile=1.0)
    disc(rg, (TABLE[0] - 0.05, FY + 0.006, TABLE[1]), (0, 1, 0), 1.15, k=48)
    rn = builder('st_runner', 'st_runner', tile=1.0)
    rn.box(CX, FY + 0.005, (ZI0 + 0.25 + BENCH[1] - 0.35) / 2, 0.8, 0.01, BENCH[1] - 0.35 - ZI0 - 0.25, faces='Y')
    # acoustic panels and the ON AIR sign on the east wall behind the guest
    for k, mat in enumerate(('st_panel_a', 'st_panel_b', 'st_panel_c')):
        z = 74.3 + k * 0.65
        builder(mat, mat).box(XI1 - 0.03, FY + 1.55, z, 0.05, 0.85, 0.58)
    oa = builder('st_onair_e', 'st_onair_e')
    builder('st_black', 'st_black').box(XI1 - 0.04, FY + 2.32, GUEST[1], 0.05, 0.2, 0.52)
    quad_facing(oa, (XI1 - 0.068, FY + 2.32, GUEST[1]), (-1, 0), 0.48, 0.18)
    return teller_mic


def build_board():
    """The story board on the back wall: a walnut frame round a dark green felt panel (the cards are drawn on it in
    Unreal), a picture light over it and the listening bench below."""
    bx, by, bw, bh = BOARD
    wl = builder('st_walnut', 'st_walnut')
    fe = builder('st_felt', 'st_felt', tile=0.5)
    zf = ZI1 - 0.035
    fe.box(bx, by, zf, bw, bh, 0.03, faces='zxXyY')
    for (cx, cy, sx, sy) in ((bx, by + bh / 2 + 0.04, bw + 0.16, 0.08), (bx, by - bh / 2 - 0.04, bw + 0.16, 0.08),
                             (bx - bw / 2 - 0.04, by, 0.08, bh), (bx + bw / 2 + 0.04, by, 0.08, bh)):
        wl.box(cx, cy, ZI1 - 0.045, sx, sy, 0.07, faces='zxXyY')
    # a brass picture light over it
    br = builder('st_brass', 'st_brass')
    br.box(bx, by + bh / 2 + 0.22, ZI1 - 0.10, 1.2, 0.05, 0.08)
    bar(br, (bx - 0.4, by + bh / 2 + 0.12, ZI1 - 0.01), (bx - 0.4, by + bh / 2 + 0.22, ZI1 - 0.10), 0.02)
    bar(br, (bx + 0.4, by + bh / 2 + 0.12, ZI1 - 0.01), (bx + 0.4, by + bh / 2 + 0.22, ZI1 - 0.10), 0.02)
    LIGHTS.append(('wallwash', (bx, FY + 2.75, ZI1 - 0.9), (1.0, 0.86, 0.68), 30, (0.0, -0.75, 0.66)))
    # the listening bench
    ox = builder('st_walnut', 'st_walnut')
    bxz = BENCH
    seat = builder('seat__stories_bench_f%d' % seat_yaw(0.0, -1.0), 'st_deck', tile=1.0)
    seat.box(bxz[0], FY + 0.43, bxz[1], 2.0, 0.05, 0.40)
    for x in (bxz[0] - 0.85, bxz[0] + 0.85):
        ox.box(x, FY + 0.205, bxz[1], 0.06, 0.41, 0.36)
    ox.box(bxz[0], FY + 0.12, bxz[1], 1.7, 0.04, 0.06)


def bookcase(z0, z1, seed):
    """A bookcase against the west wall between z0 and z1: books, archive boxes, a photograph and a plant."""
    import random
    r = random.Random(seed)
    wl = builder('st_beam', 'st_beam', tile=1.0)
    d, x_back = 0.34, XI0
    xc = x_back + d / 2
    top = FY + 2.05
    wl.box(xc, (FY + top) / 2, z0 + 0.015, d, top - FY, 0.03)
    wl.box(xc, (FY + top) / 2, z1 - 0.015, d, top - FY, 0.03)
    wl.box(x_back + 0.01, (FY + top) / 2, (z0 + z1) / 2, 0.02, top - FY, z1 - z0)
    shelves = [FY + 0.08, FY + 0.55, FY + 1.0, FY + 1.45, top]
    for y in shelves:
        wl.box(xc, y - 0.015, (z0 + z1) / 2, d, 0.03, z1 - z0 - 0.06)
    sp = builder('st_spines', 'st_spines')
    cd = builder('st_card', 'st_card')
    for k, y in enumerate(shelves[:-1]):
        z = z0 + 0.05
        row_top = shelves[k + 1] - 0.05
        while z < z1 - 0.12:
            kind = r.random()
            if kind < 0.35 and z < z1 - 0.40:
                # an archive box, its label to the room
                w = 0.32; h = min(0.27, row_top - y - 0.01)
                cd.box(x_back + 0.17, y + h / 2, z + w / 2, 0.30, h, w, faces='yYzZx')
                lr = r.randint(0, 3)
                u0, v0 = (lr % 2) * 0.5, 0.5 - (lr // 2 + 1) * 0.25
                quad_facing(sp, (x_back + 0.321, y + h / 2, z + w / 2), (1, 0), w, h,
                            uvs=[(u0, v0), (u0 + 0.5, v0), (u0 + 0.5, v0 + 0.25), (u0, v0 + 0.25)])
                z += w + 0.02
            else:
                # a run of books, their spines a slice of the spines sheet
                w = r.uniform(0.25, 0.45); h = r.uniform(0.22, min(0.32, row_top - y - 0.01))
                if z + w > z1 - 0.04: w = z1 - 0.04 - z
                if w < 0.08: break
                cd.box(x_back + 0.15, y + h / 2, z + w / 2, 0.26, h, w, faces='yYzZx')
                u0 = r.uniform(0.0, 0.6)
                face_uv(sp, [P(x_back + 0.281, y, z), P(x_back + 0.281, y, z + w), P(x_back + 0.281, y + h, z + w), P(x_back + 0.281, y + h, z)],
                        D(1, 0, 0), [(u0, 0.5), (u0 + w * 0.9, 0.5), (u0 + w * 0.9, 0.5 + h * 1.4), (u0, 0.5 + h * 1.4)])
                z += w + 0.03
    # a framed photograph standing on the second shelf from the top and a plant on top
    ph = builder('st_photo', 'st_photo')
    fr = builder('st_walnut', 'st_walnut')
    py = shelves[3] + 0.17
    pz = (z0 + z1) / 2
    fr.box(x_back + 0.20, py, pz, 0.02, 0.27, 0.35)
    quad_facing(ph, (x_back + 0.212, py, pz), (1, 0), 0.32, 0.24, tilt=0.0)
    pot = builder('st_pot', 'st_pot', smooth_deg=40)
    lf = builder('st_leaf', 'st_leaf', smooth_deg=60)
    lathe(pot, xc, (z0 + z1) / 2, [(top, 0.10), (top + 0.18, 0.13), (top + 0.19, 0.12)], n=16)
    blob(lf, xc, top + 0.36, (z0 + z1) / 2, 0.22, seed=seed + 11, squash=0.9)


def build_room_details():
    # pendants on cords from the ridge beam: a dark green dome shade with a glowing bulb
    gr = builder('st_green', 'st_green', smooth_deg=50)
    bl_ = builder('st_bulb_e', 'st_bulb_e', smooth_deg=50)
    ir = builder('st_iron', 'st_iron')
    for (x, z) in PENDANTS:
        y = FY + 2.55
        cylinder(ir, (x, RIDGE_U - 0.26, z), (x, y + 0.22, z), 0.006, n=6)
        lathe(gr, x, z, [(y, 0.24), (y + 0.02, 0.235), (y + 0.12, 0.18), (y + 0.2, 0.08), (y + 0.23, 0.03)], n=28)
        ball(bl_, (x, y + 0.04, z), 0.06)
        LIGHTS.append(('pendant', (x, y + 0.02, z), (1.0, 0.80, 0.56), 60, None))
    for k, (z0, z1) in enumerate(SHELVES):
        bookcase(z0, z1, seed=31 + k)
    # the "how it works" sign on the front wall, west of the door
    hw = builder('st_how', 'st_how')
    fr = builder('st_walnut', 'st_walnut')
    sx = (WIN_FRONT[0][1] + DOOR[0]) / 2
    sy = FY + 1.55
    fr.box(sx, sy, ZI0 + 0.012, 0.66, 0.86, 0.025)
    quad_facing(hw, (sx, sy, ZI0 + 0.026), (0, 1), 0.6, 0.8)
    # a framed print on the back wall's west end and a coat rail with hooks east of the board
    ph = builder('st_photo', 'st_photo')
    px = (XI0 + BOARD[0] - BOARD[2] / 2) / 2 - 0.05
    fr.box(px, FY + 1.6, ZI1 - 0.012, 0.86, 0.66, 0.025)
    quad_facing(ph, (px, FY + 1.6, ZI1 - 0.026), (0, -1), 0.78, 0.585)
    rx = (BOARD[0] + BOARD[2] / 2 + XI1) / 2 + 0.05
    builder('st_beam', 'st_beam').box(rx, FY + 1.75, ZI1 - 0.015, 0.8, 0.12, 0.03)
    for k in range(4):
        bar(builder('st_brass', 'st_brass'), (rx - 0.3 + k * 0.2, FY + 1.73, ZI1 - 0.03), (rx - 0.3 + k * 0.2, FY + 1.79, ZI1 - 0.11), 0.018)
    # a knitted scarf over the second hook and a canvas tote on the last, so it reads as somewhere to hang things
    sc = builder('st_scarf', 'st_panel_c')
    hx = rx - 0.1
    sc.box(hx, FY + 1.765, ZI1 - 0.068, 0.17, 0.035, 0.06)                     # the fold over the hook
    sc.box(hx - 0.01, FY + 1.765 - 0.37, ZI1 - 0.092, 0.17, 0.74, 0.016)       # the front tail
    sc.box(hx + 0.015, FY + 1.765 - 0.30, ZI1 - 0.046, 0.17, 0.60, 0.016)      # the back tail, against the wall
    for k in range(5):                                                         # the fringe
        sc.box(hx - 0.07 + k * 0.035, FY + 1.765 - 0.775, ZI1 - 0.092, 0.012, 0.07, 0.01)
    tb = builder('st_tote', 'st_card')
    tx = rx + 0.3
    tb.box(tx, FY + 1.27, ZI1 - 0.065, 0.36, 0.40, 0.06)
    for dx in (-0.08, 0.08):
        bar(tb, (tx + dx, FY + 1.47, ZI1 - 0.075), (tx, FY + 1.775, ZI1 - 0.09), 0.009)


def build_porch_things():
    # a slatted bench against the front wall west of the door, and a planter east of the door's slide
    dk = builder('st_deck', 'st_deck', tile=1.0)
    ir = builder('st_iron', 'st_iron')
    bx, bz = PORCH_BENCH
    seat = builder('seat__stories_porch_f%d' % seat_yaw(0.0, -1.0), 'st_deck', tile=1.0)
    for k in range(4):
        seat.box(bx, FY + 0.44, bz - 0.15 + k * 0.1, 1.3, 0.035, 0.08)
    for k in range(2):
        dk.box(bx, FY + 0.6 + k * 0.12, bz + 0.2, 1.3, 0.08, 0.025)
    for x in (bx - 0.58, bx + 0.58):
        ir.box(x, FY + 0.22, bz - 0.12, 0.04, 0.44, 0.04)
        ir.box(x, FY + 0.38, bz + 0.2, 0.04, 0.76, 0.04)
        ir.box(x, FY + 0.42, bz + 0.04, 0.04, 0.04, 0.34)
    pot = builder('st_pot', 'st_pot', smooth_deg=40)
    lf = builder('st_leaf', 'st_leaf', smooth_deg=60)
    px, pz = XE - 0.5, ZF - 0.45
    lathe(pot, px, pz, [(FY, 0.17), (FY + 0.42, 0.24), (FY + 0.45, 0.25), (FY + 0.46, 0.23)], n=20)
    blob(lf, px, FY + 0.8, pz, 0.34, seed=5, squash=0.95)


# ---------------------------------------------------------------- output
def web_yaw(frm, to):
    """The web camera yaw (radians; 0 looks toward -z, -pi/2 toward +x) from a point to another, in plan."""
    dx, dz = to[0] - frm[0], to[1] - frm[1]
    return math.atan2(-dx, -dz)


def write_json(seats, teller_mic):
    EYE = 1.62
    def ue_yaw(yaw):
        d = (-90.0 - math.degrees(yaw)) % 360.0
        return round(d - 360.0 if d > 180.0 else d, 3)
    def view(frm, to, pitch, floor):
        yaw = web_yaw(frm, to)
        return {'three': {'x': round(frm[0], 3), 'z': round(frm[1], 3), 'y': round(floor, 3), 'eye_y': EYE, 'yaw_rad': round(yaw, 6), 'pitch_rad': pitch},
                'ue': {'location_cm': [round(frm[0] * 100, 1), round(frm[1] * 100, 1), round((floor + EYE) * 100, 1)],
                       'rotation_deg': {'pitch': round(math.degrees(pitch), 3), 'yaw': ue_yaw(yaw), 'roll': 0.0}}}
    bx, by, bw, bh = BOARD
    layout = {
        'source': 'bl/stories.py', 'units': 'campus metres (x east, y up, z south); Unreal = (x*100, z*100, y*100)',
        'room': {'id': 'stories', 'x0': XW - 0.1, 'x1': XE + 0.1, 'z0': ZP - 0.05, 'z1': ZB + 0.1, 'y0': -1.0, 'y1': RIDGE_U + 1.0},
        'floor_y': FY,
        # the board's face (the felt's front), the story wall actor's +X out of it: Unreal yaw -90 looks toward -z
        'story_wall': {'x': bx, 'y': round(by, 3), 'z': round(ZI1 - 0.052, 3), 'yaw': -90.0, 'width_m': bw, 'height_m': bh},
        'mic': {'x': round(teller_mic[0], 3), 'y': round(teller_mic[1], 3), 'z': round(teller_mic[2], 3), 'yaw': 180.0,
                'teller_seat': 'stories_teller'},
        'seats': seats,
        'views': {
            'outside': view((CX, ZP - 4.6), (CX, ZF), 0.04, gh(CX, ZP - 4.6)),
            'inside': view((CX - 0.2, ZI0 + 0.9), (TABLE[0], TABLE[1] + 0.6), -0.12, FY),
            'board': view((CX, ZI1 - 2.4), (CX, ZI1), -0.02, FY),
        },
        'nav_bounds_m': {'x0': XW - 3.0, 'x1': XE + 3.0, 'z0': ZP - 5.0, 'z1': ZB + 2.0},
    }
    with open(os.path.join(PIPE, 'layout.json'), 'w') as f:
        json.dump(layout, f, indent=1)
    lights = {'source': 'bl/stories.py', 'units': 'metres, three.js campus axes (y up)', 'lights': []}
    for (name, pos, col, watts, aim) in LIGHTS:
        e = {'name': name, 'type': 'SPOT' if aim else 'POINT', 'campus_pos_m': [round(v, 3) for v in pos],
             'campus_dir': list(aim) if aim else [0, -1, 0], 'blender_watts': watts, 'color_linear': list(col), 'radius_m': 0.04}
        lights['lights'].append(e)
    with open(os.path.join(PIPE, 'lights.json'), 'w') as f:
        json.dump(lights, f, indent=1)


def export_glb():
    obs = [o for o in bpy.data.objects if o.type == 'MESH' and not o.get('preview_only')]
    select_only(obs)
    fp = os.path.join(PIPE, 'Stories.glb')
    bpy.ops.export_scene.gltf(filepath=fp, export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
                              export_texcoords=True, export_normals=True, export_tangents=True, export_materials='EXPORT',
                              export_image_format='AUTO', export_vertex_color='NONE', export_lights=False, export_cameras=False)
    print('exported', fp, os.path.getsize(fp), 'bytes', flush=True)


def preview_scene():
    """The grounds around the cabin (when the prepared Outside is in out/ue), sun and sky, and the cabin's own lights,
    for the previews only."""
    ue = os.path.join(SP, 'unreal', 'Pipeline', 'out', 'ue')
    fp = os.path.join(ue, 'Outside.glb')
    if os.path.exists(fp) and '--bare' not in sys.argv:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=fp)
        for o in bpy.data.objects:
            if o not in before: o['preview_only'] = 1
    else:
        g = Builder('ground_preview', material('st_grass_p', color=(0.18, 0.30, 0.12, 1), roughness=0.9), tile=4.0, lightmap=False, vcol=False)
        g.box(CX, -0.05, 72.0, 60, 0.1, 40, faces='Y')
        ob = g.finish(); ob['preview_only'] = 1
    for (name, pos, col, watts, aim) in LIGHTS:
        ld = bpy.data.lights.new(name, 'SPOT' if aim else 'POINT'); ld.energy = watts; ld.color = col
        ld.shadow_soft_size = 0.05
        ob = bpy.data.objects.new(name, ld); ob.location = P(*pos); ob['preview_only'] = 1
        if aim:
            ld.spot_size = math.radians(70)
            ob.rotation_euler = D(*aim).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.scene.collection.objects.link(ob)
    sd = bpy.data.lights.new('Sun', 'SUN'); sd.energy = 3.2; sd.angle = math.radians(1.5); sd.color = (1.0, 0.95, 0.88)
    sun = bpy.data.objects.new('Sun', sd); sun['preview_only'] = 1; bpy.context.scene.collection.objects.link(sun)
    sun.rotation_euler = Vector((0.45, 0.55, -0.7)).normalized().to_track_quat('-Z', 'Y').to_euler()
    w = bpy.data.worlds.new('World'); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.45, 0.58, 0.78, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.8


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
    build_shell()
    build_roof()
    build_porch()
    build_openings()
    teller_mic = build_nook()
    build_board()
    build_room_details()
    build_porch_things()
    seats = sorted(n for n in B if n.startswith('seat__'))
    for name, b in B.items():
        if b.count == 0: continue
        b.finish()
    write_json(seats, teller_mic)
    obs = [o for o in sc.objects if o.type == 'MESH']
    print('objects', len(obs), 'seats', seats, 'tris ~', sum(len(o.data.polygons) * 2 for o in obs),
          'built in %.0f s' % (time.time() - t0), flush=True)
    export_glb()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'stories.blend'))
    if RENDER:
        preview_scene()
        for m in bpy.data.materials:
            if m.name == 'glass': m.surface_render_method = 'BLENDED'
        views = {'front': ((CX + 3.2, gh(CX, 63.5) + 1.7, 63.5), (CX, 2.4, ZF), 62),
                 'porch': ((CX - 1.6, FY + 1.62, ZP - 1.4), (CX + 0.3, FY + 1.2, ZF + 2.0), 74),
                 'room': ((CX - 1.9, FY + 1.62, ZI0 + 0.35), (TABLE[0] + 0.4, FY + 0.9, ZI1 - 0.6), 80),
                 'nook': ((TELLER[0] - 0.9, FY + 1.35, TELLER[1] - 1.1), (GUEST[0], FY + 1.0, GUEST[1]), 62),
                 'board': ((CX, FY + 1.62, ZI1 - 2.4), (CX, FY + 1.5, ZI1), 66),
                 'shelves': ((CX + 0.4, FY + 1.62, 74.6), (XI0, FY + 1.1, 74.6), 74)}
        want = [a.split('=')[1].split(',') for a in sys.argv if a.startswith('--views=')]
        for name in (want[0] if want else views):
            eye, target, fov = views[name]
            render(name, eye, target, fov=fov)
    print('done in %.0f s' % (time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
