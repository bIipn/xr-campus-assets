"""The maker room's lesson: the 360 storytelling course in the 3D Art Studio (Room 101), built in Blender (bpy) at
campus coordinates, for Unreal. The room itself is the School's (out/campus/school.glb: the walls, the chalkboard,
the teacher desk, the easel and the turntable); this script adds the course's five stations and its desk around
what is there, each with a free standing spot in front:

  cr-plan     the storyboard table west of the room's middle, in front of the paint poster: an oak table with the
              shot-list cards laid out in two rows, a cup of markers and a pad of sticky notes
  cr-camera   the 360 camera on a tripod in the middle of the room, at eye height, with a gear cart beside it
              (the camera case, spare batteries, a memory card wallet) and a tape cross on the floor under it
  cr-sound    the interview corner by the middle east window: two chairs angled toward each other, a low round
              table between them with a microphone on a desk stand, the recorder and a pair of headphones, and a
              softbox light on a stand
  cr-edit     the edit desk against the south wall east of the door: two monitors (the stitched picture flat as a
              world map, and the timeline), keyboard, mouse, two small speakers, the task chair (a seat)
  cr-share    the headset on a pedestal in front of the chalkboard, the archive box of originals beside it

and the course desk: the room's teacher desk with a tablet and a desk card on it, the course board on the west wall
and spot__studio_f90 behind the desk where the course lead (the 360 trainer) stands, facing the room. layout.json
gives each station's anchor and view (web camera convention: yaw 0 looks toward -z, -pi/2 toward +x), the course
desk and its spot, and the seat.

Campus axes: x east, y up, z south.  Blender: X = x, Y = -z, Z = y.
Usage (Blender 5.2 or bpy 5.2.2):   python bl/maker.py [--render] [--quick] [--views=a,b]
Writes assets/maker/maker.blend, unreal/Pipeline/out/maker/Maker.glb and layout.json, and preview renders (with the
prepared School around it when it is in out/ue). Then prepare_for_unreal.py -- Maker.
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
from library import P, D, Builder, bar, sweep, material, MATS, select_only, seat_yaw   # noqa: E402
from neo import face_uv, lathe                                   # noqa: E402

SP = L.SP
OUT = os.path.join(SP, 'assets', 'maker')
PIPE = os.path.join(SP, 'unreal', 'Pipeline', 'out', 'maker')
TEX = os.path.join(SP, 'assets', 'tex')
FONTS = os.path.join(HERE, 'fonts')
RENDER = '--render' in sys.argv
QUICK = '--quick' in sys.argv
os.makedirs(OUT, exist_ok=True); os.makedirs(PIPE, exist_ok=True)

# ---------------------------------------------------------------- the plan (campus metres)
# The studio: x 14..24, z -13..-4.75, ceiling 3.6 (layout/layout.json 'studio'). What is already there: the
# chalkboard on the north wall (x 16.1..21.9), the teacher desk (x 15.6..17.2, z -12.0..-11.2, top 0.78), the paint
# poster on the west wall (z -10.45..-7.95), the easel (15.6, -6.4), the turntable (x 20.65..22.55, z -11.15..-9.25),
# three east windows (z -11.9..-10.5, -9.6..-8.2, -7.3..-5.9), the visitors' wall on the south wall west of the
# door (x 18.1..19.9).
RX0, RX1, RZN, RZS = 14.0, 24.0, -13.0, -4.75
TEACHER_DESK = (16.4, -11.6, 0.78)                # centre x, z and the top's height
SPOT = (16.4, -12.38)                             # behind the desk, the lead facing the room (+z)
BOARD = (-11.8, 1.8, 1.1, 1.2)                    # the course board on the west wall: centre z, width, height, bottom y
PLAN = (15.25, -8.75)                             # the storyboard table, 0.9 (x) by 1.6 (z), top 0.76
CAMERA = (19.0, -8.7)                             # the tripod; the 360 camera's centre at 1.52 m
CART = (19.85, -9.15)                             # the gear cart beside it
SOUND_TABLE = (23.4, -8.65)                       # the low round table between the interview chairs
CHAIR_A = (23.15, -9.32, math.radians(160))       # x, z, the direction it faces (radians, from +x toward +z)
CHAIR_B = (23.15, -7.98, math.radians(200))
SOFTBOX = (23.45, -10.05)
EDIT_DESK = (22.4, -5.12)                         # 1.6 (x) by 0.7 (z), against the south wall, top 0.75
EDIT_CHAIR = (22.4, -6.02)
SHARE = (19.4, -12.3)                             # the pedestal, 0.42 square, 0.95 high
ARCHIVE = (20.05, -12.42)

STATIONS = [('cr-plan', 'Plan the story', 'the storyboard table'),
            ('cr-camera', 'Set up the 360 camera', 'the tripod'),
            ('cr-sound', 'Record clear sound', 'the interview corner'),
            ('cr-edit', 'Stitch and edit', 'the edit desk'),
            ('cr-share', 'Share it and keep it', 'the headset by the chalkboard')]

UV01 = [(0, 0), (1, 0), (1, 1), (0, 1)]


def setup_materials():
    material('mk_oak', 'oak_col', 'oak_rgh', 'oak_nrm', roughness=0.42)                    # table and desk tops
    material('mk_white', color=(0.90, 0.90, 0.885, 1), roughness=0.4)                    # white powder-coat, laminate
    material('mk_black', color=(0.025, 0.025, 0.028, 1), roughness=0.45)                 # plastics, rubber, the camera
    material('mk_grey', color=(0.30, 0.31, 0.33, 1), roughness=0.5)                      # painted steel, the cart
    material('mk_alu', color=(0.72, 0.73, 0.75, 1), roughness=0.3, metallic=1.0)         # aluminium tripod legs
    material('mk_fabric', color=(0.10, 0.27, 0.30, 1), roughness=0.9)                    # chair fabric, deep teal
    material('mk_shell', color=(0.80, 0.55, 0.28, 1), roughness=0.5)                     # the interview chairs' shells
    material('mk_paper', color=(0.94, 0.93, 0.90, 1), roughness=0.9)
    material('mk_yellow', color=(0.95, 0.80, 0.25, 1), roughness=0.8)                    # sticky notes, tape
    material('mk_red', color=(0.70, 0.08, 0.06, 1), roughness=0.4)
    material('mk_teal', color=(0.07, 0.42, 0.45, 1), roughness=0.4)
    material('mk_card', color=(0.62, 0.55, 0.45, 1), roughness=0.85)                     # the archive box's board
    material('mk_foam', color=(0.04, 0.04, 0.045, 1), roughness=0.95)                    # the mic's windscreen
    material('mk_lens', color=(0.02, 0.025, 0.035, 1), roughness=0.05, metallic=0.4)      # the fisheye lenses
    material('mk_mark', color=(0.2, 0.2, 0.2, 1), roughness=0.9)
    material('mk_board', 'maker_board', roughness=0.6)
    material('mk_labels', 'maker_labels', roughness=0.6)
    material('mk_cards', 'maker_cards', roughness=0.85)
    material('mk_archive', 'maker_archive', roughness=0.85)
    material('mk_edit_e', 'maker_edit', emission=True, emission_strength=1.1)            # the edit monitors
    material('mk_tablet_e', 'maker_tablet', emission=True, emission_strength=1.0)
    material('mk_rec_e', 'maker_recorder', emission=True, emission_strength=1.0)
    material('mk_soft_e', color=(1, 1, 1, 1), emission=(1.0, 0.96, 0.90, 1), emission_strength=2.5)   # the softbox's face
    material('mk_led_e', color=(1, 0.1, 0.05, 1), emission=(1.0, 0.1, 0.05, 1), emission_strength=6.0)


B = {}
def builder(name, mat, tile=1.0, smooth_deg=None):
    if name not in B: B[name] = Builder(name, mat, tile=tile, lightmap=False, vcol=False, smooth=smooth_deg)
    return B[name]


# ---------------------------------------------------------------- geometry helpers
def circle(r, n=8):
    return [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def tube(b, pts, r, n=8, caps=True):
    """A round tube along a campus polyline."""
    sweep(b, pts, circle(r, n), cap_start=caps, cap_end=caps)


def hexa(b, c):
    """Six faces of a hexahedron from its 8 campus corners: c[0..3] the bottom ring, c[4..7] the top ring."""
    pts = [P(*p) for p in c]
    centre = sum(pts, Vector((0, 0, 0))) / 8
    for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        q = [pts[i] for i in f]
        mid = sum(q, Vector((0, 0, 0))) / 4
        b.face(q, (mid - centre).normalized())


def disc(b, centre, n, r, k=24):
    """A flat disc at campus `centre` facing the campus direction n."""
    C = P(*centre); N = D(*n).normalized()
    up = Vector((0, 0, 1))
    U = up.cross(N).normalized() if abs(N.z) < 0.9 else Vector((1, 0, 0))
    V = N.cross(U).normalized()
    for i in range(k):
        a0 = 2 * math.pi * i / k; a1 = 2 * math.pi * (i + 1) / k
        b.face([C, C + U * r * math.cos(a0) + V * r * math.sin(a0), C + U * r * math.cos(a1) + V * r * math.sin(a1)], N)


def dome(b, centre, axis, r, rings=5, k=16):
    """A half-sphere bulging along the campus direction `axis` from `centre` (a fisheye lens)."""
    C = P(*centre); A = D(*axis).normalized()
    up = Vector((0, 0, 1))
    U = up.cross(A).normalized() if abs(A.z) < 0.9 else Vector((1, 0, 0))
    V = A.cross(U).normalized()
    def pt(t, a):          # t: 0 at the rim .. pi/2 at the pole
        return C + (U * math.cos(a) + V * math.sin(a)) * r * math.cos(t) + A * r * math.sin(t)
    for j in range(rings):
        t0 = (math.pi / 2) * j / rings; t1 = (math.pi / 2) * (j + 1) / rings
        for i in range(k):
            a0 = 2 * math.pi * i / k; a1 = 2 * math.pi * (i + 1) / k
            q = [pt(t0, a0), pt(t0, a1), pt(t1, a1), pt(t1, a0)]
            mid = sum(q, Vector((0, 0, 0))) / 4
            b.face(q, (mid - C).normalized())


def oriented_box(b, cx, cy, cz, sx, sy, sz, f, faces='all'):
    """A box whose local +x points along the campus plan direction f = (fx, fz)."""
    b.box(cx, cy, cz, sx, sy, sz, ry=math.atan2(-f[1], f[0]), faces=faces)


def quad_facing(b, centre, f, w, h, uvs=None, tilt=0.0):
    """A textured rectangle centred at campus `centre` whose front faces the plan direction f = (fx, fz), w wide
    and h high, its top leaning back (away from the viewer) by `tilt` radians; uv (0, 0) at the viewer's
    bottom-left. A viewer looking at the front looks along -f, so their right is up x f = (fz, 0, -fx)."""
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


def label_rows(r):
    """uvs of row r (0..5) of maker_labels.png, as UV01 is for the whole image."""
    v0, v1 = 1 - (r + 1) / 6, 1 - r / 6
    return [(0, v0), (1, v0), (1, v1), (0, v1)]


def tent_card(b, cx, y, cz, f, w, row):
    """A desk card (a tent of card standing on a surface at height y) whose label faces the plan direction f."""
    h = w / 4.0
    lean = math.radians(16)
    fx, fz = f
    # the front panel leans back from its bottom edge, which sits a little in front of the ridge
    c = (cx + fx * math.sin(lean) * h / 2, y + math.cos(lean) * h / 2, cz + fz * math.sin(lean) * h / 2)
    quad_facing(b, c, f, w, h, uvs=label_rows(row), tilt=lean)
    back = builder('mk_paper', 'mk_paper')
    c2 = (cx - fx * math.sin(lean) * h / 2, y + math.cos(lean) * h / 2, cz - fz * math.sin(lean) * h / 2)
    quad_facing(back, c2, (-fx, -fz), w, h, tilt=lean)


# ---------------------------------------------------------------- the textures (PIL)
def font(names, size):
    from PIL import ImageFont
    for n in names:
        for p in (os.path.join(FONTS, n), '/usr/share/fonts/opentype/inter/' + n, '/usr/share/fonts/truetype/dejavu/' + n):
            if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()


NAVY = (31, 58, 82); GOLD = (236, 186, 74); INK = (28, 34, 40); TEAL = (18, 110, 118); PALE = (242, 240, 234)
PLUM = (92, 54, 112)


def panorama(W, H, seed=3):
    """A stylised 360 picture flat as a world map (equirectangular): sky, a far ridge, a library's front and two
    trees, a path running to both edges, and the stretched floor at the bottom."""
    from PIL import Image, ImageDraw
    import random
    r = random.Random(seed)
    im = Image.new('RGB', (W, H), (0, 0, 0)); d = ImageDraw.Draw(im)
    hz = int(H * 0.55)
    for y in range(hz):
        t = y / hz
        d.line((0, y, W, y), fill=(int(110 + 90 * t), int(160 + 70 * t), int(220 + 25 * t)))
    for y in range(hz, H):
        t = (y - hz) / (H - hz)
        d.line((0, y, W, y), fill=(int(120 - 40 * t), int(150 - 50 * t), int(90 - 30 * t)))
    pts = [(0, hz)]
    for x in range(0, W + 40, 40):
        pts.append((x, hz - 30 - int(30 * math.sin(x / W * 6.28 * 2) + r.randint(0, 12))))
    pts.append((W, hz))
    d.polygon(pts, fill=(84, 110, 120))
    # the library's front, bent by the projection near the middle
    cx = W * 0.5
    for k in range(-6, 7):
        x0 = cx + k * W * 0.012; x1 = x0 + W * 0.009
        d.rectangle((x0, hz - 120 + abs(k) * 4, x1, hz), fill=(236, 230, 214))
    d.polygon([(cx - W * 0.085, hz - 120), (cx + W * 0.085, hz - 120), (cx, hz - 180)], fill=(220, 212, 194))
    d.rectangle((cx - W * 0.09, hz - 10, cx + W * 0.09, hz + 6), fill=(200, 194, 180))
    for tx in (0.2, 0.78):
        x = W * tx
        d.rectangle((x - 6, hz - 60, x + 6, hz + 10), fill=(80, 60, 40))
        d.ellipse((x - 70, hz - 180, x + 70, hz - 40), fill=(60, 110, 60))
    # the path, curving to both edges as a straight line does in a 360 picture
    for x in range(0, W, 6):
        y = hz + 30 + int(60 * (1 - math.cos((x / W) * 2 * math.pi)) / 2)
        d.line((x, y, x + 6, y), fill=(200, 186, 150), width=14)
    # the seam guide (where the two lenses meet) and the nadir patch at the bottom
    d.rectangle((0, H - 34, W, H), fill=(40, 46, 40))
    return im


def make_textures():
    from PIL import Image, ImageDraw
    import clientpack
    client = clientpack.get('client', 'XR Libraries')
    bold = lambda s: font(['Inter-Bold.otf', 'DejaVuSans-Bold.ttf'], s)
    semi = lambda s: font(['Inter-SemiBold.otf', 'DejaVuSans-Bold.ttf'], s)
    reg = lambda s: font(['Inter-Regular.otf', 'DejaVuSans.ttf'], s)
    med = lambda s: font(['Inter-Medium.otf', 'DejaVuSans.ttf'], s)
    mono = lambda s: font(['DejaVuSansMono-Bold.ttf'], s)
    # the course board (1.8 x 1.1 m): the header band, the five stations as a checklist, the footer
    W, H = 1800, 1100
    im = Image.new('RGB', (W, H), PALE); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 220), fill=PLUM)
    d.text((64, 44), '360 STORYTELLING · FIVE STATIONS · QUIZ · CERTIFICATE', font=mono(36), fill=GOLD)
    d.text((64, 100), 'Making a 360 Story', font=bold(84), fill=(255, 255, 255))
    d.text((W - 64, 62), client.upper() + ' · CREATOR COURSE', font=mono(28), fill=(214, 196, 226), anchor='ra')
    y = 270
    for k, (sid, name, where) in enumerate(STATIONS, 1):
        d.rectangle((70, y + 8, 70 + 62, y + 70), outline=INK, width=5, fill=(255, 255, 255))
        d.text((168, y - 2), '%d' % k, font=bold(60), fill=PLUM)
        d.text((236, y + 2), name, font=semi(54), fill=INK)
        d.text((236 + d.textlength(name, font=semi(54)) + 28, y + 20), '— ' + where, font=reg(36), fill=(95, 100, 108))
        y += 132
    d.line((64, 958, W - 64, 958), fill=(190, 186, 176), width=3)
    d.text((70, 984), 'Finish all five, then take the quiz at the teacher’s desk.', font=med(44), fill=PLUM)
    d.text((W - 70, 994), 'certificate on passing', font=mono(30), fill=TEAL, anchor='ra')
    im.save(os.path.join(TEX, 'maker_board.png'), optimize=True)
    # the station plates: six rows (the five stations and the course desk), each 4:1, plum with a numbered tab
    W, RH_ = 1024, 160
    im = Image.new('RGB', (W, RH_ * 6), PLUM); d = ImageDraw.Draw(im)
    rows = [('%d' % k, name.upper(), where) for k, (sid, name, where) in enumerate(STATIONS, 1)] + [('✓', 'COURSE DESK', 'checklist and quiz')]
    for r, (num, name, where) in enumerate(rows):
        y0 = r * RH_
        d.rectangle((0, y0, 150, y0 + RH_ - 1), fill=TEAL)
        d.text((75, y0 + 80), num, font=bold(96), fill=(255, 255, 255), anchor='mm')
        size = 58 if d.textlength(name, font=bold(58)) < W - 220 else 46
        d.text((190, y0 + 30), name, font=bold(size), fill=(255, 255, 255))
        d.text((192, y0 + 104), where, font=mono(28), fill=GOLD)
    im.save(os.path.join(TEX, 'maker_labels.png'), optimize=True)
    # the shot-list cards: six cards (3 x 2), each a sketch and a line
    CW, CH = 512, 384
    im = Image.new('RGB', (CW * 3, CH * 2), (250, 248, 240)); d = ImageDraw.Draw(im)
    cards = [('1  THE PLACE', 'the library steps, morning'), ('2  WHO SPEAKS', 'Mrs. Ortega, the oldest member'),
             ('3  NOTICE', 'the mural behind the desk'), ('4  SOUND', 'the bell, the kids reading'),
             ('5  SCENE LENGTH', '30 to 90 seconds each'), ('6  PERMISSION', 'signed, kept with the files')]
    for k, (head, line) in enumerate(cards):
        x0 = (k % 3) * CW; y0 = (k // 3) * CH
        d.rectangle((x0 + 10, y0 + 10, x0 + CW - 10, y0 + CH - 10), outline=(200, 196, 186), width=3)
        d.rectangle((x0 + 30, y0 + 30, x0 + CW - 30, y0 + 230), outline=INK, width=4)
        # a quick sketch: a horizon, a figure or a building, the camera's 360 circle
        hz = y0 + 160
        d.line((x0 + 30, hz, x0 + CW - 30, hz), fill=INK, width=3)
        if k in (0, 2):
            d.rectangle((x0 + 190, y0 + 80, x0 + 330, hz), outline=INK, width=4)
            d.polygon([(x0 + 180, y0 + 80), (x0 + 340, y0 + 80), (x0 + 260, y0 + 45)], outline=INK)
        elif k == 1:
            d.ellipse((x0 + 230, y0 + 70, x0 + 280, y0 + 120), outline=INK, width=4)
            d.line((x0 + 255, y0 + 120, x0 + 255, hz + 40), fill=INK, width=4)
        elif k == 3:
            for j in range(4): d.arc((x0 + 200 - j * 26, y0 + 90 - j * 26, x0 + 300 + j * 26, y0 + 190 + j * 26), 300, 60, fill=INK, width=4)
        elif k == 4:
            d.ellipse((x0 + 200, y0 + 70, x0 + 310, y0 + 180), outline=INK, width=4)
            d.line((x0 + 255, y0 + 125, x0 + 255, y0 + 85), fill=INK, width=4); d.line((x0 + 255, y0 + 125, x0 + 285, y0 + 140), fill=INK, width=4)
        else:
            d.line((x0 + 180, y0 + 150, x0 + 330, y0 + 150), fill=INK, width=3)
            d.line((x0 + 190, y0 + 140, x0 + 230, y0 + 100), fill=INK, width=4); d.line((x0 + 230, y0 + 100, x0 + 260, y0 + 130), fill=INK, width=4)
        d.text((x0 + 34, y0 + 252), head, font=bold(40), fill=PLUM)
        d.text((x0 + 34, y0 + 306), line, font=reg(30), fill=INK)
    im.save(os.path.join(TEX, 'maker_cards.png'), optimize=True)
    # the edit monitors (two 16:9 halves side by side): the stitched picture flat, and the timeline
    W, H = 2048, 576
    im = Image.new('RGB', (W, H), (16, 18, 22)); d = ImageDraw.Draw(im)
    pano = panorama(964, 482)
    im.paste(pano, (30, 60))
    d.text((30, 18), 'STITCH  ·  front and back lenses → one 360 picture', font=mono(24), fill=(160, 200, 210))
    d.line((30 + 482, 60, 30 + 482, 542), fill=(240, 90, 80), width=2)          # the seam guide
    d.text((30 + 490, 64), 'seam', font=mono(20), fill=(240, 90, 80))
    x0 = 1024
    d.rectangle((x0, 0, W, H), fill=(22, 24, 30))
    d.text((x0 + 30, 18), 'EDIT  ·  library_steps_v3', font=mono(24), fill=(160, 200, 210))
    thumb = pano.resize((300, 150))
    im.paste(thumb, (x0 + 30, 60)); im.paste(thumb, (x0 + 360, 60))
    d.rectangle((x0 + 690, 60, x0 + 994, 210), fill=(40, 44, 52))
    d.text((x0 + 842, 135), 'Te damos la bienvenida', font=semi(26), fill=(255, 255, 255), anchor='mm')
    d.text((x0 + 842, 170), 'captions · EN · ES', font=mono(18), fill=(160, 200, 210), anchor='mm')
    tracks = [('V1', [(0.0, 0.24, (70, 130, 170)), (0.26, 0.55, (70, 130, 170)), (0.57, 0.92, (70, 130, 170))]),
              ('T1', [(0.02, 0.18, (170, 120, 200)), (0.60, 0.80, (170, 120, 200))]),
              ('A1', [(0.0, 0.92, (90, 170, 120))]), ('A2', [(0.0, 0.92, (60, 120, 90))])]
    for k, (nm, clips) in enumerate(tracks):
        y = 250 + k * 68
        d.text((x0 + 30, y + 16), nm, font=mono(22), fill=(150, 156, 170))
        d.rectangle((x0 + 80, y, x0 + 994, y + 56), fill=(30, 33, 40))
        for (a, b_, col) in clips:
            d.rectangle((x0 + 80 + int(914 * a), y + 4, x0 + 80 + int(914 * b_), y + 52), fill=col)
        if nm.startswith('A'):
            for i in range(0, 900, 6):
                hh = 8 + int(14 * abs(math.sin(i * 0.07 + k)))
                d.line((x0 + 84 + i, y + 28 - hh, x0 + 84 + i, y + 28 + hh), fill=(200, 240, 210))
    d.line((x0 + 80 + int(914 * 0.41), 236, x0 + 80 + int(914 * 0.41), 530), fill=(240, 90, 80), width=3)
    d.text((x0 + 30, 536), '00:01:12:08', font=mono(24), fill=(240, 240, 240))
    im.save(os.path.join(TEX, 'maker_edit.png'), optimize=True)
    # the course tablet (4:3): the checklist
    W, H = 800, 600
    im = Image.new('RGB', (W, H), (248, 247, 244)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 90), fill=PLUM)
    d.text((30, 22), 'Making a 360 Story', font=bold(40), fill=(255, 255, 255))
    for k, (sid, name, where) in enumerate(STATIONS):
        y = 120 + k * 80
        d.rectangle((30, y, 80, y + 50), outline=INK, width=4)
        d.text((104, y + 4), name, font=semi(34), fill=INK)
    d.rectangle((30, 530, 330, 580), fill=TEAL); d.text((180, 555), 'QUIZ', font=bold(28), fill=(255, 255, 255), anchor='mm')
    im.save(os.path.join(TEX, 'maker_tablet.png'), optimize=True)
    # the recorder's little screen (2:1): levels
    W, H = 256, 128
    im = Image.new('RGB', (W, H), (10, 14, 18)); d = ImageDraw.Draw(im)
    d.text((10, 8), 'REC  00:04:31', font=mono(20), fill=(240, 80, 70))
    for k, lev in enumerate((0.62, 0.55)):
        y = 50 + k * 34
        d.rectangle((10, y, 246, y + 22), fill=(28, 34, 40))
        d.rectangle((10, y, 10 + int(236 * lev), y + 22), fill=(90, 220, 120))
    im.save(os.path.join(TEX, 'maker_recorder.png'), optimize=True)
    # the archive box's label (3:2)
    W, H = 600, 400
    im = Image.new('RGB', (W, H), (250, 249, 244)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 70), fill=NAVY)
    d.text((24, 18), 'LOCAL HISTORY · 360 STORIES', font=mono(26), fill=GOLD)
    for k, ln in enumerate(['Library steps — story 01', 'Original files (both lenses)', 'Shot list and notes', 'Signed permissions', 'Credits']):
        d.text((24, 96 + k * 56), ('▸ ' if k else '') + ln, font=(semi(34) if k == 0 else reg(30)), fill=INK)
    im.save(os.path.join(TEX, 'maker_archive.png'), optimize=True)


# ---------------------------------------------------------------- the course desk: the teacher desk's tablet and card, the board, the spot
def course_desk():
    cx, cz, top = TEACHER_DESK
    bk = builder('mk_black', 'mk_black')
    # a tablet on a little stand, leaning back, its screen facing the room (+z)
    tx, tz = cx - 0.38, cz + 0.05
    tilt = math.radians(25)
    # the stand: a wedge of two plates
    bar(bk, (tx, top, tz - 0.06), (tx, top + 0.12, tz - 0.02), 0.16, 0.012)
    bk.box(tx, top + 0.004, tz, 0.16, 0.008, 0.10)
    th = 0.20 * 0.75
    c = (tx, top + 0.015 + math.cos(tilt) * th / 2, tz - 0.035 + math.sin(tilt) * th / 2)
    quad_facing(bk, (c[0], c[1], c[2] - 0.004), (0, 1), 0.21, th + 0.012, tilt=tilt)
    tb = builder('mk_tablet', 'mk_tablet_e')
    quad_facing(tb, c, (0, 1), 0.20, th, tilt=tilt)
    lb = builder('mk_labels', 'mk_labels')
    tent_card(lb, cx + 0.45, top, cz + 0.30, (0, 1), 0.24, 5)


def course_board():
    zc, w, h, y0 = BOARD
    fr = builder('mk_board_frame', 'mk_oak', tile=0.6)
    bd = builder('mk_board', 'mk_board')
    x = RX0 + 0.012
    face_uv(bd, [P(x + 0.02, y0, zc + w / 2), P(x + 0.02, y0, zc - w / 2), P(x + 0.02, y0 + h, zc - w / 2), P(x + 0.02, y0 + h, zc + w / 2)], D(1, 0, 0), UV01)
    t = 0.05
    fr.box(x + 0.02, y0 - t / 2, zc, 0.04, t, w + 2 * t)
    fr.box(x + 0.02, y0 + h + t / 2, zc, 0.04, t, w + 2 * t)
    fr.box(x + 0.02, y0 + h / 2, zc - w / 2 - t / 2, 0.04, h, t)
    fr.box(x + 0.02, y0 + h / 2, zc + w / 2 + t / 2, 0.04, h, t)


def spot():
    sp = builder('spot__studio_f%d' % seat_yaw(0.0, 1.0), 'mk_mark')
    x, z = SPOT
    sp.face([P(x - 0.15, 0.01, z - 0.15), P(x + 0.15, 0.01, z - 0.15), P(x + 0.15, 0.01, z + 0.15), P(x - 0.15, 0.01, z + 0.15)], D(0, 1, 0))


# ---------------------------------------------------------------- cr-plan: the storyboard table
def plan_table():
    cx, cz = PLAN
    top = builder('mk_plan_top', 'mk_oak', tile=0.8); wh = builder('mk_white', 'mk_white')
    W_, L_, H_ = 0.9, 1.6, 0.76
    top.box(cx, H_ - 0.02, cz, W_, 0.04, L_)
    for sx in (-1, 1):
        for sz in (-1, 1):
            wh.box(cx + sx * (W_ / 2 - 0.06), (H_ - 0.04) / 2, cz + sz * (L_ / 2 - 0.08), 0.04, H_ - 0.04, 0.04)
    for sx in (-1, 1):
        wh.box(cx + sx * (W_ / 2 - 0.06), 0.15, cz, 0.03, 0.03, L_ - 0.2)
    wh.box(cx, H_ - 0.07, cz - (L_ / 2 - 0.08), W_ - 0.16, 0.05, 0.025)
    wh.box(cx, H_ - 0.07, cz + (L_ / 2 - 0.08), W_ - 0.16, 0.05, 0.025)
    # the six shot-list cards, read from the east side (the viewer's right is -z, the card's top is -x)
    cd = builder('mk_cards', 'mk_cards')
    cw, ch = 0.30, 0.225
    y = H_ + 0.002
    for k in range(6):
        col, row = k % 3, k // 3
        u0, u1 = col / 3, (col + 1) / 3
        v0, v1 = 1 - (row + 1) / 2, 1 - row / 2
        zc = cz + 0.42 - col * (cw + 0.06)
        xc = cx - 0.14 + row * (ch + 0.07)
        ang = math.radians((k * 37) % 7 - 3)
        def at(du, dv):          # du along the viewer's right (-z), dv away from the viewer (-x)
            return P(xc - dv * math.cos(ang) - du * math.sin(ang), y, zc - du * math.cos(ang) + dv * math.sin(ang))
        face_uv(cd, [at(-cw / 2, -ch / 2), at(cw / 2, -ch / 2), at(cw / 2, ch / 2), at(-cw / 2, ch / 2)], D(0, 1, 0),
                [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    # a cup of markers and a pad of sticky notes
    tl = builder('mk_teal', 'mk_teal', smooth_deg=40); bk = builder('mk_black', 'mk_black')
    mx, mz = cx + 0.28, cz - 0.62
    lathe(tl, mx, mz, [(H_, 0.0), (H_, 0.042), (H_ + 0.10, 0.045)], n=16, cap_top=False)
    for k, (dx, dz, lean) in enumerate(((0.012, 0.0, 0.10), (-0.01, 0.012, -0.12), (0.0, -0.014, 0.05))):
        mk = builder(('mk_red', 'mk_black', 'mk_teal')[k], ('mk_red', 'mk_black', 'mk_teal')[k])
        bar(mk, (mx + dx, H_ + 0.01, mz + dz), (mx + dx + lean * 0.12, H_ + 0.15, mz + dz + lean * 0.05), 0.014)
    ye = builder('mk_yellow', 'mk_yellow')
    ye.box(cx + 0.30, H_ + 0.008, cz + 0.62, 0.076, 0.016, 0.076, ry=0.2)
    lb = builder('mk_labels', 'mk_labels')
    tent_card(lb, cx + 0.36, H_, cz - 0.30, (1, 0), 0.24, 0)


# ---------------------------------------------------------------- cr-camera: the tripod, the 360 camera, the gear cart
def camera_rig():
    cx, cz = CAMERA
    al = builder('mk_alu', 'mk_alu', smooth_deg=50); bk = builder('mk_black', 'mk_black', smooth_deg=50)
    hub_y = 1.22
    for k in range(3):
        a = math.radians(90 + 120 * k)
        foot = (cx + 0.44 * math.cos(a), 0.02, cz + 0.44 * math.sin(a))
        top_ = (cx + 0.05 * math.cos(a), hub_y, cz + 0.05 * math.sin(a))
        mid = tuple(top_[i] + (foot[i] - top_[i]) * 0.55 for i in range(3))
        tube(al, [top_, mid], 0.012, n=8)
        tube(al, [mid, foot], 0.009, n=8)
        bk.box(mid[0], mid[1], mid[2], 0.03, 0.04, 0.03)                  # the leg lock
        lathe(bk, foot[0], foot[2], [(0.0, 0.0), (0.0, 0.016), (0.03, 0.012), (0.03, 0.0)], n=8, cap_top=True)
    lathe(bk, cx, cz, [(hub_y - 0.03, 0.0), (hub_y - 0.03, 0.055), (hub_y + 0.03, 0.055), (hub_y + 0.03, 0.0)], n=16, cap_top=True)
    tube(al, [(cx, hub_y, cz), (cx, 1.40, cz)], 0.011, n=10)
    lathe(bk, cx, cz, [(1.40, 0.0), (1.40, 0.02), (1.425, 0.02), (1.425, 0.0)], n=12, cap_top=True)
    # the 360 camera: a slim upright body, a lens bulging from each broad face (front -z, back +z)
    cam = builder('mk_camera', 'mk_black', smooth_deg=40)
    cam.box(cx, 1.50, cz, 0.046, 0.15, 0.026)
    ln = builder('mk_lens', 'mk_lens', smooth_deg=60)
    for s in (-1, 1):
        lathe(cam, cx, cz, [], n=4) if False else None
        ring_c = (cx, 1.545, cz + s * 0.013)
        dome(ln, ring_c, (0, 0, s), 0.019)
        disc(cam, (cx, 1.545, cz + s * 0.0131), (0, 0, s), 0.022, k=20)
    led = builder('mk_led', 'mk_led_e')
    led.box(cx, 1.47, cz - 0.0135, 0.006, 0.006, 0.002)
    # tape cross on the floor under the tripod: the nadir the camera hides in
    ye = builder('mk_yellow', 'mk_yellow')
    for a in (0.785, -0.785):
        ye.box(cx, 0.003, cz, 0.70, 0.004, 0.05, ry=a)
    # the gear cart: a small grey trolley with two shelves, the camera case, batteries, a card wallet
    gx, gz = CART
    gr = builder('mk_grey', 'mk_grey'); bk2 = builder('mk_black', 'mk_black', smooth_deg=50)
    w_, d_, h_ = 0.52, 0.40, 0.80
    for sx in (-1, 1):
        for sz in (-1, 1):
            gr.box(gx + sx * (w_ / 2 - 0.02), h_ / 2 + 0.04, gz + sz * (d_ / 2 - 0.02), 0.025, h_ - 0.08, 0.025)
            lathe(bk2, gx + sx * (w_ / 2 - 0.03), gz + sz * (d_ / 2 - 0.03), [(0.0, 0.0), (0.0, 0.03), (0.06, 0.03), (0.06, 0.0)], n=8, cap_top=True)
    for y in (0.22, h_):
        gr.box(gx, y, gz, w_, 0.02, d_)
        gr.box(gx, y + 0.03, gz - d_ / 2 + 0.005, w_, 0.04, 0.01)
        gr.box(gx, y + 0.03, gz + d_ / 2 - 0.005, w_, 0.04, 0.01)
    bk2.box(gx - 0.08, h_ + 0.07, gz, 0.30, 0.12, 0.22)                  # the camera case
    gr.box(gx - 0.08, h_ + 0.135, gz, 0.10, 0.012, 0.03)                  # its handle
    for k in range(3):
        bk2.box(gx + 0.15, h_ + 0.025, gz - 0.10 + k * 0.05, 0.06, 0.03, 0.035)   # spare batteries
    tl = builder('mk_teal', 'mk_teal')
    tl.box(gx + 0.16, h_ + 0.02, gz + 0.11, 0.10, 0.02, 0.07)            # the memory card wallet
    bk2.box(gx, 0.29, gz, 0.40, 0.12, 0.30)                              # a case on the lower shelf
    lb = builder('mk_labels', 'mk_labels')
    quad_facing(lb, (gx, 0.66, gz + d_ / 2 + 0.006), (0, 1), 0.36, 0.09, uvs=label_rows(1))


# ---------------------------------------------------------------- cr-sound: the interview corner
def shell_chair(cx, cz, f_ang):
    """A moulded-shell chair on four wooden legs facing the plan angle f_ang (radians from +x toward +z)."""
    sh = builder('mk_shell', 'mk_shell', smooth_deg=40); wd = builder('mk_chair_legs', 'mk_oak', tile=0.4)
    fx, fz = math.cos(f_ang), math.sin(f_ang)
    rx, rz = -fz, fx
    def W(u, v): return (cx + u * fx + v * rx, cz + u * fz + v * rz)
    sy = 0.45
    # the seat pan
    corners = []
    for y in (sy - 0.02, sy + 0.02):
        for (u, v) in ((0.22, -0.23), (0.22, 0.23), (-0.20, 0.23), (-0.20, -0.23)):
            x_, z_ = W(u, v); corners.append((x_, y, z_))
    hexa(sh, corners)
    # the back, curving round, leaning back
    n = 8; R = 0.5; half = 0.23
    for i in range(n):
        a0 = -half / R + (2 * half / R) * i / n; a1 = -half / R + (2 * half / R) * (i + 1) / n
        pts = []
        for (a, y) in ((a0, sy + 0.02), (a1, sy + 0.02), (a1, sy + 0.42), (a0, sy + 0.42)):
            lean = (y - sy) * 0.22
            u = -0.20 - lean - (R - R * math.cos(a)) * 0.5
            v = R * math.sin(a)
            x_, z_ = W(u, v)
            pts.append(P(x_, y, z_))
        nm = D(fx, 0.0, fz)
        sh.face(pts, nm)
        sh.face(list(reversed([p + D(-fx, 0, -fz) * 0.014 for p in pts])), -nm)
    for (u, v) in ((0.17, -0.18), (0.17, 0.18), (-0.16, -0.18), (-0.16, 0.18)):
        a = W(u, v); c = W(u * 1.25, v * 1.2)
        bar(wd, (a[0], sy - 0.02, a[1]), (c[0], 0.0, c[1]), 0.03)


def sound_corner():
    shell_chair(*CHAIR_A)
    shell_chair(*CHAIR_B)
    tx, tz = SOUND_TABLE
    wh = builder('mk_white', 'mk_white', smooth_deg=40); bk = builder('mk_black', 'mk_black', smooth_deg=45)
    top_y = 0.52
    lathe(wh, tx, tz, [(top_y - 0.025, 0.0), (top_y - 0.025, 0.27), (top_y, 0.27), (top_y, 0.0)], n=28, cap_top=True)
    tube(bk, [(tx, 0.02, tz), (tx, top_y - 0.025, tz)], 0.025, n=10)
    lathe(bk, tx, tz, [(0.0, 0.0), (0.0, 0.20), (0.02, 0.19), (0.02, 0.0)], n=20, cap_top=True)
    # the desk microphone: a round base, a short stand, the capsule in a foam windscreen, pointing at chair A
    mx, mz = tx - 0.06, tz - 0.04
    lathe(bk, mx, mz, [(top_y, 0.0), (top_y, 0.06), (top_y + 0.015, 0.055), (top_y + 0.015, 0.0)], n=16, cap_top=True)
    tube(bk, [(mx, top_y + 0.015, mz), (mx, top_y + 0.20, mz)], 0.007, n=8)
    ax, az = CHAIR_A[0] - mx, CHAIR_A[1] - mz
    L_ = math.hypot(ax, az); ax, az = ax / L_, az / L_
    a = (mx, top_y + 0.20, mz); c = (mx + ax * 0.10, top_y + 0.25, mz + az * 0.10)
    tube(bk, [a, c], 0.016, n=10)
    fm = builder('mk_foam', 'mk_foam', smooth_deg=60)
    lathe(fm, c[0], c[2], [(c[1] - 0.035, 0.0), (c[1] - 0.03, 0.022), (c[1], 0.035), (c[1] + 0.03, 0.022), (c[1] + 0.035, 0.0)], n=14, cap_top=False)
    # the recorder, lying on the table, its screen up
    rx_, rz_ = tx + 0.12, tz + 0.08
    bk.box(rx_, top_y + 0.014, rz_, 0.07, 0.028, 0.15, ry=0.4)
    rec = builder('mk_recorder', 'mk_rec_e')
    ang = 0.4
    def at(du, dv):
        return P(rx_ + du * math.cos(ang) + dv * math.sin(ang), top_y + 0.0285, rz_ - du * math.sin(ang) + dv * math.cos(ang))
    face_uv(rec, [at(-0.025, 0.03), at(0.025, 0.03), at(0.025, -0.02), at(-0.025, -0.02)], D(0, 1, 0), [(0, 0), (1, 0), (1, 1), (0, 1)])
    led = builder('mk_led', 'mk_led_e')
    led.box(rx_ + 0.01, top_y + 0.029, rz_ - 0.05, 0.008, 0.002, 0.008)
    # the headphones, lying: two cups and the band
    hx, hz = tx + 0.05, tz + 0.17
    for s in (-1, 1):
        lathe(bk, hx + s * 0.08, hz, [(top_y, 0.0), (top_y, 0.045), (top_y + 0.035, 0.045), (top_y + 0.035, 0.0)], n=14, cap_top=True)
    band = [(hx + 0.08 * math.cos(t), top_y + 0.018, hz - 0.11 * math.sin(t)) for t in [math.pi * i / 10 for i in range(11)]]
    tube(bk, band, 0.008, n=6)
    # the softbox on a light stand, angled at the two chairs
    sx_, sz_ = SOFTBOX
    st = builder('mk_stand', 'mk_black', smooth_deg=45)
    for k in range(3):
        a_ = math.radians(30 + 120 * k)
        tube(st, [(sx_, 0.35, sz_), (sx_ + 0.32 * math.cos(a_), 0.01, sz_ + 0.32 * math.sin(a_))], 0.009, n=6)
    tube(st, [(sx_, 0.02, sz_), (sx_, 1.70, sz_)], 0.014, n=8)
    tx2, tz2 = (CHAIR_A[0] + CHAIR_B[0]) / 2 - 0.3, (CHAIR_A[1] + CHAIR_B[1]) / 2
    fx_, fz_ = tx2 - sx_, tz2 - sz_
    L2 = math.hypot(fx_, fz_); fx_, fz_ = fx_ / L2, fz_ / L2
    box_c = (sx_ + fx_ * 0.18, 1.70, sz_ + fz_ * 0.18)
    sb = builder('mk_softbox', 'mk_black')
    oriented_box(sb, box_c[0], box_c[1], box_c[2], 0.30, 0.55, 0.55, (fx_, fz_), faces='xyYzZ')
    face = builder('mk_soft', 'mk_soft_e')
    quad_facing(face, (box_c[0] + fx_ * 0.152, box_c[1], box_c[2] + fz_ * 0.152), (fx_, fz_), 0.52, 0.52)
    lb = builder('mk_labels', 'mk_labels')
    tent_card(lb, tx - 0.16, top_y, tz + 0.06, (-1, 0), 0.20, 2)


# ---------------------------------------------------------------- cr-edit: the edit desk
def edit_desk():
    cx, cz = EDIT_DESK
    top = builder('mk_edit_top', 'mk_oak', tile=0.8); wh = builder('mk_white', 'mk_white'); bk = builder('mk_black', 'mk_black', smooth_deg=45)
    W_, D_, H_ = 1.6, 0.7, 0.75
    top.box(cx, H_ - 0.02, cz, W_, 0.04, D_)
    for sx in (-1, 1):
        wh.box(cx + sx * (W_ / 2 - 0.03), (H_ - 0.04) / 2, cz, 0.05, H_ - 0.04, D_ - 0.06)
    wh.box(cx, H_ - 0.12, cz + D_ / 2 - 0.04, W_ - 0.1, 0.14, 0.02)          # the modesty panel at the back
    # two monitors on a shared arm post at the back, angled in a little, screens facing north (-z)
    ed = builder('mk_edit', 'mk_edit_e')
    for k, (dx, turn, u0, u1) in enumerate(((-0.29, 0.12, 0.0, 0.5), (0.29, -0.12, 0.5, 1.0))):
        mxc, mzc = cx + dx, cz + 0.12
        f = (math.sin(turn), -math.cos(turn))                    # the screen's facing in plan, mostly -z
        lathe(bk, mxc, mzc + 0.08, [(H_, 0.0), (H_, 0.10), (H_ + 0.012, 0.10), (H_ + 0.012, 0.0)], n=16, cap_top=True)
        tube(bk, [(mxc, H_ + 0.012, mzc + 0.08), (mxc, 1.02, mzc + 0.06)], 0.02, n=8)
        oriented_box(bk, mxc, 1.10, mzc, 0.03, 0.34, 0.56, f)           # the monitor's body (thin along its facing)
        quad_facing(ed, (mxc + f[0] * 0.016, 1.10, mzc + f[1] * 0.016), f, 0.535, 0.30, uvs=[(u0, 0), (u1, 0), (u1, 1), (u0, 1)])
    # keyboard, mouse, two little speakers
    bk.box(cx - 0.05, H_ + 0.012, cz - 0.16, 0.44, 0.022, 0.14)
    gr = builder('mk_grey', 'mk_grey')
    gr.box(cx - 0.05, H_ + 0.024, cz - 0.16, 0.42, 0.004, 0.12)
    bk.box(cx + 0.32, H_ + 0.015, cz - 0.15, 0.06, 0.03, 0.10)
    for sx in (-1, 1):
        bk.box(cx + sx * 0.68, H_ + 0.10, cz + 0.14, 0.12, 0.20, 0.14)
        disc(gr, (cx + sx * 0.68, H_ + 0.08, cz + 0.069), (0, 0, -1), 0.035, k=16)
    # a coffee mug
    tl = builder('mk_teal', 'mk_teal', smooth_deg=40)
    lathe(tl, cx - 0.55, cz - 0.18, [(H_, 0.0), (H_, 0.04), (H_ + 0.095, 0.042)], n=16, cap_top=False)
    lb = builder('mk_labels', 'mk_labels')
    quad_facing(lb, (cx - 0.48, H_ - 0.10, cz - D_ / 2 - 0.004), (0, -1), 0.32, 0.08, uvs=label_rows(3))
    task_chair(EDIT_CHAIR[0], EDIT_CHAIR[1], 'seat__studio_edit_f%d' % seat_yaw(0.0, 1.0), (0.0, 1.0))


def task_chair(cx, cz, seat_name, f):
    """An office task chair facing the campus direction f: a five-star base on castors, a gas column, the seat pan
    (tagged), a leaning backrest on a spine, two armrests."""
    ch = builder('mk_alu', 'mk_alu', smooth_deg=50); bk = builder('mk_black', 'mk_black', smooth_deg=50)
    se = builder(seat_name, 'mk_fabric'); fb = builder('mk_fabric', 'mk_fabric')
    rx, rz = -f[1], f[0]
    ry = math.atan2(-f[1], f[0])
    def W(u, v): return (cx + u * f[0] + v * rx, cz + u * f[1] + v * rz)
    for k in range(5):
        a = 2 * math.pi * k / 5 + math.pi / 2
        tip = (cx + 0.30 * math.cos(a), 0.06, cz + 0.30 * math.sin(a))
        bar(bk, (cx, 0.10, cz), tip, 0.04, 0.03)
        lathe(bk, tip[0], tip[2], [(0.0, 0.0), (0.0, 0.025), (0.05, 0.025), (0.05, 0.0)], n=8, cap_top=False)
    lathe(ch, cx, cz, [(0.08, 0.03), (0.30, 0.03), (0.30, 0.022), (0.43, 0.022)], n=12, cap_top=True)
    bk.box(cx, 0.445, cz, 0.30, 0.03, 0.30, ry=ry)
    se.box(cx, 0.49, cz, 0.47, 0.06, 0.47, ry=ry)
    a_, c_ = W(-0.22, 0.0), W(-0.30, 0.0)
    bar(bk, (a_[0], 0.47, a_[1]), (c_[0], 0.72, c_[1]), 0.05, 0.03)
    lean = math.tan(math.radians(12))
    corners = []
    for (y, uu) in ((0.62, -0.26), (1.02, -0.26 - 0.40 * lean)):
        for (u, v) in ((uu + 0.05, -0.21), (uu + 0.05, 0.21), (uu - 0.0, 0.21), (uu - 0.0, -0.21)):
            x_, z_ = W(u, v); corners.append((x_, y, z_))
    hexa(fb, corners)
    for s in (-1, 1):
        a_ = W(0.0, s * 0.26)
        bar(bk, (a_[0], 0.50, a_[1]), (a_[0], 0.70, a_[1]), 0.03)
        a_ = W(-0.12, s * 0.26); c_ = W(0.14, s * 0.26)
        bar(bk, (a_[0], 0.72, a_[1]), (c_[0], 0.72, c_[1]), 0.05, 0.03)


# ---------------------------------------------------------------- cr-share: the headset on its pedestal, the archive box
def share_pedestal():
    cx, cz = SHARE
    wh = builder('mk_white', 'mk_white'); bk = builder('mk_black', 'mk_black', smooth_deg=45)
    s, h = 0.42, 0.95
    wh.box(cx, h / 2, cz, s, h, s)
    wh.box(cx, h + 0.01, cz, s + 0.04, 0.02, s + 0.04)
    # a headset on a display stand: a disc base, a post, a rounded head shape the headset sits on
    lathe(bk, cx, cz, [(h + 0.02, 0.0), (h + 0.02, 0.08), (h + 0.03, 0.08), (h + 0.03, 0.0)], n=18, cap_top=True)
    tube(bk, [(cx, h + 0.03, cz), (cx, h + 0.22, cz)], 0.012, n=8)
    hd = builder('mk_stand_head', 'mk_grey', smooth_deg=60)
    lathe(hd, cx, cz, [(h + 0.20, 0.0), (h + 0.21, 0.045), (h + 0.26, 0.06), (h + 0.31, 0.05), (h + 0.33, 0.0)], n=16, cap_top=False)
    hs = builder('mk_headset', 'mk_black', smooth_deg=40)
    hy, hzf = h + 0.27, cz + 0.07                                   # the visor faces the room (+z)
    hs.box(cx, hy, hzf, 0.19, 0.11, 0.09)
    hs.box(cx, hy, hzf + 0.047, 0.17, 0.09, 0.006)
    gl = builder('mk_lens', 'mk_lens')
    gl.box(cx, hy, hzf + 0.051, 0.15, 0.07, 0.002)
    band = [(cx + 0.095 * math.cos(t), hy + 0.01, cz + 0.035 - 0.12 * math.sin(t)) for t in [math.pi * i / 10 for i in range(11)]]
    tube(hs, band, 0.012, n=6)
    tube(hs, [(cx, hy + 0.055, hzf - 0.03), (cx, hy + 0.075, cz - 0.02), (cx, hy + 0.02, cz - 0.09)], 0.01, n=6)
    lb = builder('mk_labels', 'mk_labels')
    quad_facing(lb, (cx, 0.78, cz + s / 2 + 0.003), (0, 1), 0.34, 0.085, uvs=label_rows(4))
    # the archive box of originals on the floor beside it, its label to the room
    ax, az = ARCHIVE
    cb = builder('mk_archive_box', 'mk_card')
    cb.box(ax, 0.15, az, 0.40, 0.30, 0.30)
    cb.box(ax, 0.305, az, 0.42, 0.03, 0.32)
    ar = builder('mk_archive', 'mk_archive')
    quad_facing(ar, (ax, 0.15, az + 0.152), (0, 1), 0.24, 0.16)


# ---------------------------------------------------------------- output
def web_yaw(frm, to):
    """The web camera yaw (radians; 0 looks toward -z, -pi/2 toward +x) from a point to another, in plan."""
    dx, dz = to[0] - frm[0], to[1] - frm[1]
    return math.atan2(-dx, -dz)


def write_json(seats):
    EYE = 1.62
    def ue_yaw(yaw):
        d = (-90.0 - math.degrees(yaw)) % 360.0
        return round(d - 360.0 if d > 180.0 else d, 3)
    def view(frm, to, pitch):
        yaw = web_yaw(frm, to)
        return {'three': {'x': round(frm[0], 3), 'z': round(frm[1], 3), 'eye_y': EYE, 'yaw_rad': round(yaw, 6), 'pitch_rad': pitch},
                'ue': {'location_cm': [round(frm[0] * 100, 1), round(frm[1] * 100, 1), round(EYE * 100, 1)],
                       'rotation_deg': {'pitch': round(math.degrees(pitch), 3), 'yaw': ue_yaw(yaw), 'roll': 0.0}}}
    def station(sid, anchor, frm, pitch):
        return {'id': sid, 'room': 'studio', 'anchor_m': [round(v, 3) for v in anchor],
                'ue_location_cm': [round(anchor[0] * 100, 1), round(anchor[2] * 100, 1), round(anchor[1] * 100, 1)],
                'view': view(frm, (anchor[0], anchor[2]), pitch)}
    cx, cz, top = TEACHER_DESK
    zc, w, h, y0 = BOARD
    layout = {
        'source': 'bl/maker.py', 'units': 'campus metres (x east, y up, z south); Unreal = (x*100, z*100, y*100)',
        'venue': 'studio', 'room': 'studio',
        'stations': [
            station('cr-plan', (PLAN[0], 0.9, PLAN[1]), (PLAN[0] + 1.7, PLAN[1]), -0.35),
            station('cr-camera', (CAMERA[0], 1.3, CAMERA[1]), (CAMERA[0], CAMERA[1] + 1.85), -0.06),
            station('cr-sound', (SOUND_TABLE[0], 0.9, SOUND_TABLE[1]), (21.25, SOUND_TABLE[1]), -0.2),
            station('cr-edit', (EDIT_DESK[0], 1.05, EDIT_DESK[1]), (EDIT_DESK[0], -7.45), -0.12),
            station('cr-share', (SHARE[0], 1.1, SHARE[1]), (SHARE[0], -10.55), -0.18),
        ],
        'course_desk': {'anchor_m': [cx, top, cz], 'faces': [0, 0, 1],
                        'ue_location_cm': [round(cx * 100, 1), round(cz * 100, 1), round(top * 100, 1)],
                        'spot': {'x': SPOT[0], 'y': 0.0, 'z': SPOT[1], 'yaw': seat_yaw(0.0, 1.0), 'mesh': 'spot__studio_f%d' % seat_yaw(0.0, 1.0)},
                        'board': {'wall': 'W', 'x': RX0, 'z': zc, 'width': w, 'height': h, 'y0': y0},
                        'view': view((cx, SPOT[1] + 1.7), (cx, RZN), -0.05)},
        'speaker_spot': {'x': SPOT[0], 'y': 0.0, 'z': SPOT[1], 'yaw': seat_yaw(0.0, 1.0)},
        'seats': len(seats), 'seat_names': seats,
    }
    with open(os.path.join(PIPE, 'layout.json'), 'w') as f:
        json.dump(layout, f, indent=1)


def export_glb():
    obs = [o for o in bpy.data.objects if o.type == 'MESH' and not o.get('preview_only')]
    select_only(obs)
    fp = os.path.join(PIPE, 'Maker.glb')
    bpy.ops.export_scene.gltf(filepath=fp, export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
                              export_texcoords=True, export_normals=True, export_tangents=True, export_materials='EXPORT',
                              export_image_format='AUTO', export_vertex_color='NONE', export_lights=False, export_cameras=False)
    print('exported', fp, os.path.getsize(fp), 'bytes', flush=True)


def preview_scene():
    """The prepared School around the props (when out/ue has it), the room's light, for the previews only."""
    ue = os.path.join(SP, 'unreal', 'Pipeline', 'out', 'ue')
    fp = os.path.join(ue, 'School.glb')
    if os.path.exists(fp) and '--bare' not in sys.argv:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=fp)
        for o in bpy.data.objects:
            if o not in before: o['preview_only'] = 1
    for (x, z) in ((16.5, -10.5), (21.5, -10.5), (16.5, -7.0), (21.5, -7.0)):
        ld = bpy.data.lights.new('panel', 'AREA'); ld.shape = 'RECTANGLE'; ld.size, ld.size_y = 1.2, 0.6
        ld.energy = 260; ld.color = (1.0, 0.96, 0.9)
        ob = bpy.data.objects.new('panel', ld); ob.location = P(x, 3.5, z); ob['preview_only'] = 1
        bpy.context.scene.collection.objects.link(ob)
    sd = bpy.data.lights.new('Sun', 'SUN'); sd.energy = 3.0; sd.angle = math.radians(1.5); sd.color = (1.0, 0.95, 0.88)
    sun = bpy.data.objects.new('Sun', sd); sun['preview_only'] = 1; bpy.context.scene.collection.objects.link(sun)
    sun.rotation_euler = Vector((-0.8, 0.2, -0.6)).normalized().to_track_quat('-Z', 'Y').to_euler()
    w = bpy.data.worlds.new('World'); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.45, 0.55, 0.7, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.4


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
    course_desk()
    course_board()
    spot()
    plan_table()
    camera_rig()
    sound_corner()
    edit_desk()
    share_pedestal()
    seats = ['seat__studio_edit_f%d' % seat_yaw(0.0, 1.0)]
    for name, b in B.items():
        if b.count == 0: continue
        b.finish()
    write_json(seats)
    obs = [o for o in sc.objects if o.type == 'MESH']
    print('objects', len(obs), 'seats', len(seats), 'tris ~', sum(len(o.data.polygons) * 2 for o in obs),
          'built in %.0f s' % (time.time() - t0), flush=True)
    export_glb()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'maker.blend'))
    if RENDER:
        preview_scene()
        for o in bpy.data.objects:
            if o.name.startswith('spot__'): o.hide_render = True
        views = {'room': ((23.6, 1.7, -5.2), (16.5, 1.0, -11.0), 78),
                 'plan': ((16.95, 1.62, -8.75), (15.25, 0.76, -8.75), 62),
                 'camera': ((19.0, 1.62, -6.85), (19.2, 1.2, -8.9), 62),
                 'sound': ((21.25, 1.62, -8.65), (23.4, 0.9, -8.65), 62),
                 'edit': ((22.4, 1.62, -7.45), (22.4, 0.95, -5.0), 62),
                 'share': ((19.4, 1.62, -10.55), (19.6, 1.0, -12.4), 62),
                 'desk': ((16.4, 1.62, -10.65), (15.0, 1.4, -12.2), 70)}
        want = [a.split('=')[1].split(',') for a in sys.argv if a.startswith('--views=')]
        for name in (want[0] if want else views):
            eye, target, fov = views[name]
            render(name, eye, target, fov=fov)
    print('done in %.0f s' % (time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
