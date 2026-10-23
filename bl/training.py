"""The Training Wing: a vocational training room for the dialysis technician course (XR Libraries' Project SANDI),
built in Blender (bpy) at campus coordinates, for Unreal.

Where: a new room north of the Workshop School and east of the auditorium, x 21.2..32.0, z -27.0..-13.6 (floor 0,
ceiling 3.6), entered from the auditorium's cross-aisle through a door in its east wall (bl/auditorium.py cuts it,
EAST_DOOR, z -16.2..-15.0, through the 0.45 m wall) and from the yard through a double doorway in the east wall under
a canopy. The outer faces, the roof, the holes for the yard door and the four windows and the canopy are bl/exterior.py's
(SHELLS 'training', OPENINGS, WINDOWS, SHELL_CUTS); the east wall stands on the yard fence's line, which runs on inside
it (content/refits.json clips the fence out of the doorway). This script builds the room: walls with a white dado rail
and skirting, a grey resilient floor, an acoustic-tile ceiling on a T-grid with eight 2 x 4 panel lights, the window
frames, glass and reveals, the yard door's leaves standing open, and the five stations, each with a free standing spot
in front:

  dx-hygiene   the sink unit on the south wall by the west door: a stainless sink in a white cabinet, a tall tap, the
               soap and paper-towel dispensers, a glove-box holder, a pedal bin
  dx-machine   the dialysis machine beside the treatment chair: a white cabinet on castors, a tilted lit screen, the
               blood-pump module with its round door, two blood lines to a dialyzer in a side holder, an IV pole
  dx-chair     the reclining treatment chair (pale blue vinyl) with the machine at its left, a BP monitor on a rolling
               stand at its right and a floor scale by the wall
  dx-water     the water panel on the north wall: two carbon tanks, an RO unit, a wall cabinet with the conductivity
               meter and the chlorine test kit on its shelf, the log on its hook
  dx-charting  the charting desk by the south-east corner: monitor, keyboard, task chair, filing cabinet, corkboard

and the course desk: a standing desk mid-way along the west wall facing east, the checklist board behind it, and
spot__training_f0 behind it where the course lead stands. Four chairs along the south wall (seat__training_c1_f270 ..
c4, facing north into the room) and the task chair (seat__training_desk_f90) are the seats. layout.json gives the room,
the doors and windows, each station's anchor and view (web camera convention: yaw 0 looks toward -z, -pi/2 toward +x),
the course desk and its spot, and the seats; lights.json the eight panels (AREA) and the two strips (screen).

Campus axes: x east, y up, z south.  Blender: X = x, Y = -z, Z = y.
Usage (Blender 5.2 or bpy 5.2.2):   python bl/training.py [--render] [--quick] [--views=a,b]
Writes assets/training/training.blend, unreal/Pipeline/out/training/Training.glb, lights.json and layout.json, and
preview renders (with the prepared grounds, auditorium and yard around it when they are in out/ue). Then
prepare_for_unreal.py -- Training.
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
from neo import face_uv, lathe, run_boxes, wall_with_openings   # noqa: E402

SP = L.SP
OUT = os.path.join(SP, 'assets', 'training')
PIPE = os.path.join(SP, 'unreal', 'Pipeline', 'out', 'training')
TEX = os.path.join(SP, 'assets', 'tex')
FONTS = os.path.join(HERE, 'fonts')
RENDER = '--render' in sys.argv
QUICK = '--quick' in sys.argv
os.makedirs(OUT, exist_ok=True); os.makedirs(PIPE, exist_ok=True)

# ---------------------------------------------------------------- the plan (campus metres)
RX0, RX1, RZN, RZS, RH = 21.2, 32.0, -27.0, -13.6, 3.6
WALL_T = 0.45                                     # the shell walls: the room's faces to the outer faces
AUD_X = 20.75                                     # the auditorium's east wall (bl/auditorium.py AX1)
WEST_DOOR = (-16.2, -15.0, 2.2)                   # z0, z1, h: from the auditorium's cross-aisle (its EAST_DOOR)
YARD_DOOR = (-26.7, -24.9, 2.4)                   # z0, z1, h: the double doorway to the yard (bl/exterior.py OPENINGS)
WIN_Y0, WIN_Y1 = 1.15, 2.35                       # the windows' sill and head (the sill clears the fence rail in the wall)
EAST_WINDOWS = ((-21.9, -20.5), (-17.5, -16.1))   # z0, z1 (bl/exterior.py WINDOWS)
NORTH_WINDOWS = ((27.5, 28.9), (29.9, 31.3))      # x0, x1
DADO_Y, SKIRT_H = 0.9, 0.10
SINK = (23.4, -13.9)                              # the sink unit's centre along the south wall, 0.6 m deep
CHAIRS_X = (25.6, 26.2, 26.8, 27.4); CHAIRS_Z = -14.05
TCHAIR = (30.4, -19.0)                            # the treatment chair, facing west
MACHINE = (30.95, -17.75)                         # the dialysis machine, at the chair's left by its back
IV_POLE = (30.5, -16.95)
BP_STAND = (30.9, -20.35)
SCALE = (31.6, -22.9)                             # the floor scale, its post against the east wall
TANKS = ((23.2, -26.44), (24.05, -26.44))         # the two carbon tanks
RO_UNIT = (25.6, -26.55)                          # the RO unit's centre, 0.8 x 0.4 in plan
CABINET = (26.2, 27.3, 1.4, 2.1)                  # the wall cabinet: x0, x1, y0, y1
SHELF_Y = 1.0
DESK = (30.1, -14.25)                             # the charting desk, 1.4 x 0.7, against the south wall
FILING = (31.6, -13.9)
COURSE_DESK = (22.55, -20.5)                      # the standing desk, facing east
SPOT = (21.95, -20.5)
BOARD = (-20.5, 2.4, 1.2, 1.35)                   # centre z, width, height, bottom y on the west wall
CLOCK = (26.5, 2.75)                              # x, centre y on the south wall
SIGN = (-25.8, 1.4, 0.35, 2.58)                   # centre z, width, height, bottom y: over the yard door
PANELS_X = (24.2, 29.0); PANELS_Z = (-24.9, -21.9, -18.9, -15.9)
GRID = 0.6                                        # the ceiling grid's pitch


def setup_materials():
    material('trn_floor', color=(0.30, 0.31, 0.33, 1), roughness=0.55)                  # grey resilient sheet
    material('trn_wall', color=(0.68, 0.655, 0.61, 1), roughness=0.85)                  # pale warm-grey paint
    material('trn_ceiling', color=(0.86, 0.86, 0.84, 1), roughness=0.95)                # acoustic tile
    material('trn_white', color=(0.90, 0.90, 0.885, 1), roughness=0.45)                 # satin white: trim, frames, doors
    material('trn_cabinet', color=(0.92, 0.92, 0.90, 1), roughness=0.35)                # white laminate
    material('trn_enamel', color=(0.93, 0.94, 0.95, 1), roughness=0.22)                 # appliance white
    material('trn_steel', color=(0.60, 0.61, 0.63, 1), roughness=0.35, metallic=1.0)    # brushed stainless
    material('trn_chrome', color=(0.85, 0.86, 0.88, 1), roughness=0.12, metallic=1.0)   # chrome poles and bases
    material('trn_vinyl', color=(0.40, 0.58, 0.72, 1), roughness=0.5)                   # the treatment chair, pale blue
    material('trn_oak', 'oak_col', 'oak_rgh', 'oak_nrm', roughness=0.4)                 # desk tops
    material('trn_fabric', color=(0.16, 0.17, 0.20, 1), roughness=0.9)                  # the task chair
    material('trn_shell', color=(0.78, 0.80, 0.82, 1), roughness=0.5)                   # the four chairs' moulded shells
    material('trn_black', color=(0.02, 0.02, 0.022, 1), roughness=0.5)                  # plastics, castors, bezels
    material('trn_grey', color=(0.33, 0.34, 0.36, 1), roughness=0.5)                    # painted steel
    material('trn_blue', color=(0.06, 0.20, 0.42, 1), roughness=0.35)                   # the carbon tanks' fibreglass
    material('trn_red', color=(0.50, 0.015, 0.015, 1), roughness=0.3)                   # blood lines, the dialyzer's caps
    material('trn_paper', color=(0.93, 0.93, 0.91, 1), roughness=0.9)                   # paper, the glove box, fibres
    material('trn_cork', 'training_cork', roughness=0.9)
    material('trn_glass', color=(0.85, 0.92, 0.98, 1), roughness=0.05, alpha=0.18)
    material('trn_bag', color=(0.90, 0.93, 0.96, 1), roughness=0.3, alpha=0.55)         # the saline bag
    material('trn_lamp_e', color=(1, 1, 1, 1), emission=(1.0, 0.97, 0.92, 1), emission_strength=3.0)   # the panels' diffusers
    material('trn_led_e', color=(0.2, 1.0, 0.4, 1), emission=(0.2, 1.0, 0.4, 1), emission_strength=4.0)
    material('trn_screen_e', 'training_machine', emission=True, emission_strength=1.2)   # the machine's screen
    material('trn_bp_e', 'training_bp', emission=True, emission_strength=1.2)
    material('trn_record_e', 'training_record', emission=True, emission_strength=1.0)
    material('trn_tablet_e', color=(0.80, 0.88, 0.95, 1), emission=(0.80, 0.88, 0.95, 1), emission_strength=1.0)
    material('trn_board', 'training_board', roughness=0.6)
    material('trn_sign', 'training_sign', roughness=0.6)
    material('trn_labels', 'training_labels', roughness=0.6)
    material('trn_clock', 'training_clock', roughness=0.5)
    material('trn_sheet', 'training_sheet', roughness=0.9)
    material('trn_mark', color=(0.2, 0.2, 0.2, 1), roughness=0.9)


B = {}
def builder(name, mat, tile=1.0, smooth_deg=None):
    if name not in B: B[name] = Builder(name, mat, tile=tile, lightmap=False, vcol=False, smooth=smooth_deg)
    return B[name]


LIGHTS = []        # (kind, (x, y, z), colour, watts, area size or None)
PREVIEW_LIGHTS = []
UV01 = [(0, 0), (1, 0), (1, 1), (0, 1)]


# ---------------------------------------------------------------- geometry helpers
def circle(r, n=8):
    return [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def tube(b, pts, r, n=8, caps=True):
    """A round tube along a campus polyline."""
    sweep(b, pts, circle(r, n), cap_start=caps, cap_end=caps)


def hexa(b, c):
    """Six faces of a hexahedron from its 8 campus corners: c[0..3] the bottom ring (counter-clockwise seen from
    above), c[4..7] the top ring above them."""
    pts = [P(*p) for p in c]
    centre = sum(pts, Vector((0, 0, 0))) / 8
    for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        q = [pts[i] for i in f]
        mid = sum(q, Vector((0, 0, 0))) / 4
        b.face(q, (mid - centre).normalized())


def disc(b, centre, n, r, k=24, tex=False):
    """A flat disc at campus `centre` facing the campus direction n (a tuple), as a fan; with tex=True the uvs map a
    square texture onto it the way a viewer facing it sees it (u to their right, v up)."""
    C = P(*centre); N = D(*n).normalized()
    up = Vector((0, 0, 1))
    U = up.cross(N).normalized() if abs(N.z) < 0.9 else Vector((1, 0, 0))
    V = N.cross(U).normalized()
    for i in range(k):
        a0 = 2 * math.pi * i / k; a1 = 2 * math.pi * (i + 1) / k
        p0 = C + U * r * math.cos(a0) + V * r * math.sin(a0); p1 = C + U * r * math.cos(a1) + V * r * math.sin(a1)
        if tex:
            face_uv(b, [C, p0, p1], N, [(0.5, 0.5), (0.5 + 0.5 * math.cos(a0), 0.5 + 0.5 * math.sin(a0)), (0.5 + 0.5 * math.cos(a1), 0.5 + 0.5 * math.sin(a1))])
        else:
            b.face([C, p0, p1], N)


def facing(f):
    """For something that faces the campus direction f (unit 2D): the viewer-right direction, and the box yaw that
    puts a box's local +x along f."""
    rx, rz = -f[1], f[0]
    return (rx, rz), math.atan2(-f[1], f[0])


WALLS = {'S': (RZS, (0, -1), -1), 'N': (RZN, (0, 1), 1), 'W': (RX0, (1, 0), -1), 'E': (RX1, (-1, 0), 1)}


def wall_pts(wall, c, w, y0, y1, out_d=0.0):
    """The four corners (bottom-left, bottom-right, top-right, top-left as a viewer facing the wall sees them) of a
    rectangle on a room wall, centred at the campus coordinate c along it (x on N/S, z on E/W), standing out_d off
    the wall; and the wall's normal."""
    fixed, n, s = WALLS[wall]
    left, right = c - s * w / 2, c + s * w / 2
    if wall in ('N', 'S'):
        z = fixed + n[1] * out_d
        pts = [P(left, y0, z), P(right, y0, z), P(right, y1, z), P(left, y1, z)]
    else:
        x = fixed + n[0] * out_d
        pts = [P(x, y0, left), P(x, y0, right), P(x, y1, right), P(x, y1, left)]
    return pts, D(n[0], 0, n[1])


def plate(b, wall, c, w, y0, y1, out_d=0.0, uvs=None):
    """A textured upright rectangle on a wall (uv (0, 0) at the viewer's bottom-left)."""
    pts, n = wall_pts(wall, c, w, y0, y1, out_d)
    face_uv(b, pts, n, uvs or UV01)


def wall_box(b, wall, c, w, y0, y1, depth, off=0.0, faces=None):
    """A box standing against a wall (its back face left out unless off > 0), centred at c along it."""
    fixed, n, s = WALLS[wall]
    if wall in ('N', 'S'):
        cx, cz, sx, sz = c, fixed + n[1] * (off + depth / 2), w, depth
        back = 'Z' if wall == 'S' else 'z'
    else:
        cx, cz, sx, sz = fixed + n[0] * (off + depth / 2), c, depth, w
        back = 'x' if wall == 'W' else 'X'
    if faces is None: faces = 'xXyYzZ' if off > 1e-6 else 'xXyYzZ'.replace(back, '')
    b.box(cx, (y0 + y1) / 2, cz, sx, y1 - y0, sz, faces=faces)


def label(b, wall, c, w, y0, y1, row, out_d=0.012):
    """One of the station plates: row `row` of assets/tex/training_labels.png (six rows), 4:1."""
    v0, v1 = 1 - (row + 1) / 6, 1 - row / 6
    plate(b, wall, c, w, y0, y1, out_d, uvs=[(0, v0), (1, v0), (1, v1), (0, v1)])


# ---------------------------------------------------------------- the textures (PIL)
def font(names, size):
    from PIL import ImageFont
    for n in names:
        for p in (os.path.join(FONTS, n), '/usr/share/fonts/opentype/inter/' + n, '/usr/share/fonts/truetype/dejavu/' + n):
            if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()


NAVY = (31, 58, 82); GOLD = (236, 186, 74); INK = (28, 34, 40); TEAL = (18, 110, 118); PALE = (242, 240, 234)
STATIONS = [('dx-hygiene', 'Hand hygiene and gloving', 'the sink'),
            ('dx-machine', 'The dialysis machine', 'set-up and priming'),
            ('dx-chair', 'The treatment chair', 'the patient and their vitals'),
            ('dx-water', 'Water treatment', 'carbon tanks and the RO unit'),
            ('dx-charting', 'Charting', 'the treatment record')]


def make_textures():
    from PIL import Image, ImageDraw
    import clientpack
    client = clientpack.get('client', 'XR Libraries')
    bold = lambda s: font(['Inter-Bold.otf', 'DejaVuSans-Bold.ttf'], s)
    semi = lambda s: font(['Inter-SemiBold.otf', 'DejaVuSans-Bold.ttf'], s)
    reg = lambda s: font(['Inter-Regular.otf', 'DejaVuSans.ttf'], s)
    med = lambda s: font(['Inter-Medium.otf', 'DejaVuSans.ttf'], s)
    mono = lambda s: font(['DejaVuSansMono-Bold.ttf'], s)
    # the course board (2.4 x 1.2 m): the header band, the five stations as a checklist, the footer
    W, H = 1920, 960
    im = Image.new('RGB', (W, H), PALE); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 200), fill=NAVY)
    d.text((70, 44), 'DIALYSIS TECHNICIAN · FOUNDATIONS', font=mono(40), fill=GOLD)
    d.text((70, 96), 'The Training Wing', font=bold(78), fill=(255, 255, 255))
    d.text((W - 70, 70), client.upper() + ' · PROJECT SANDI', font=mono(30), fill=(170, 190, 205), anchor='ra')
    y = 250
    for k, (sid, name, where) in enumerate(STATIONS, 1):
        d.rectangle((80, y + 6, 80 + 64, y + 70), outline=INK, width=5, fill=(255, 255, 255))
        d.text((180, y - 2), '%d' % k, font=bold(58), fill=TEAL)
        d.text((250, y + 2), name, font=semi(52), fill=INK)
        d.text((250 + d.textlength(name, font=semi(52)) + 30, y + 18), '— ' + where, font=reg(36), fill=(95, 100, 108))
        y += 118
    d.line((70, 848, W - 70, 848), fill=(190, 186, 176), width=3)
    d.text((80, 870), 'Finish all five, then take the quiz at this desk.', font=med(44), fill=NAVY)
    d.text((W - 80, 878), 'certificate on passing', font=mono(30), fill=TEAL, anchor='ra')
    im.save(os.path.join(TEX, 'training_board.png'), optimize=True)
    # the sign over the yard door, in the School's door-sign style (navy plate, gold mono kicker, white name), 4:1
    W, H = 1600, 400
    im = Image.new('RGB', (W, H), NAVY); d = ImageDraw.Draw(im)
    d.text((70, 60), 'DIALYSIS TECHNICIAN COURSE · FIVE STATIONS · QUIZ · CERTIFICATE', font=mono(40), fill=GOLD)
    d.text((70, 150), 'The Training Wing', font=bold(150), fill=(255, 255, 255))
    d.text((W - 70, 150), 'YARD ▸', font=bold(120), fill=GOLD, anchor='ra')
    im.save(os.path.join(TEX, 'training_sign.png'), optimize=True)
    # the station plates: six rows (the five stations and the course desk), each 4:1, navy with a numbered tab
    W, RH_ = 1024, 160
    im = Image.new('RGB', (W, RH_ * 6), NAVY); d = ImageDraw.Draw(im)
    rows = [('%d' % k, name.upper(), where) for k, (sid, name, where) in enumerate(STATIONS, 1)] + [('✓', 'COURSE DESK', 'checklist and quiz')]
    for r, (num, name, where) in enumerate(rows):
        y0 = r * RH_
        d.rectangle((0, y0, 150, y0 + RH_ - 1), fill=TEAL)
        d.text((75, y0 + 80), num, font=bold(96), fill=(255, 255, 255), anchor='mm')
        d.text((190, y0 + 30), name, font=bold(58), fill=(255, 255, 255))
        d.text((192, y0 + 104), where, font=mono(28), fill=GOLD)
    im.save(os.path.join(TEX, 'training_labels.png'), optimize=True)
    # the machine's screen (4:3): a treatment running
    W, H = 1024, 768
    im = Image.new('RGB', (W, H), (8, 16, 24)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 96), fill=(14, 42, 58))
    d.text((40, 24), 'HEMODIALYSIS', font=bold(44), fill=(255, 255, 255))
    d.text((W - 40, 30), 'TREATMENT RUNNING  ●', font=mono(34), fill=(90, 230, 140), anchor='ra')
    vals = [('Blood flow', '300', 'mL/min'), ('Arterial pressure', '-120', 'mmHg'), ('Venous pressure', '+140', 'mmHg'),
            ('UF rate', '0.80', 'L/h'), ('UF goal', '2.4', 'L'), ('Dialysate', '37.0', '°C'), ('Conductivity', '14.0', 'mS/cm'), ('Time left', '2:35', 'h:mm')]
    for k, (nm, v, u) in enumerate(vals):
        cx, cy = 40 + (k % 2) * 500, 130 + (k // 2) * 140
        d.rectangle((cx, cy, cx + 460, cy + 118), fill=(16, 30, 42), outline=(40, 70, 90), width=2)
        d.text((cx + 20, cy + 14), nm.upper(), font=mono(24), fill=(130, 170, 190))
        d.text((cx + 20, cy + 46), v, font=bold(60), fill=(210, 240, 255))
        d.text((cx + 20 + d.textlength(v, font=bold(60)) + 14, cy + 70), u, font=reg(28), fill=(130, 170, 190))
    d.rectangle((40, 700, W - 40, 732), fill=(16, 30, 42)); d.rectangle((40, 700, 40 + int((W - 80) * 0.38), 732), fill=(60, 180, 120))
    d.text((40, 740), 'TREATMENT 1:30 OF 4:05', font=mono(20), fill=(130, 170, 190))
    im.save(os.path.join(TEX, 'training_machine.png'), optimize=True)
    # the BP monitor's readout (4:3)
    W, H = 512, 384
    im = Image.new('RGB', (W, H), (6, 12, 18)); d = ImageDraw.Draw(im)
    d.text((24, 16), 'NIBP  mmHg', font=mono(26), fill=(120, 160, 180))
    d.text((24, 48), '122/78', font=bold(110), fill=(230, 240, 250))
    d.text((24, 180), 'PULSE  bpm', font=mono(26), fill=(120, 160, 180))
    d.text((24, 210), '72', font=bold(90), fill=(90, 230, 140))
    d.text((W - 24, 180), 'SpO₂', font=mono(26), fill=(120, 160, 180), anchor='ra')
    d.text((W - 24, 210), '98%', font=bold(90), fill=(110, 190, 250), anchor='ra')
    im.save(os.path.join(TEX, 'training_bp.png'), optimize=True)
    # the charting monitor (16:9): the treatment record
    W, H = 1024, 576
    im = Image.new('RGB', (W, H), (246, 247, 248)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 70), fill=NAVY)
    d.text((30, 18), 'TREATMENT RECORD', font=bold(34), fill=(255, 255, 255))
    d.text((W - 30, 22), 'patient · chair 3 · session 14', font=mono(22), fill=(170, 190, 205), anchor='ra')
    cols = ['TIME', 'BP', 'PULSE', 'BFR', 'AP', 'VP', 'UF', 'TMP', 'NOTE']
    xs = [30, 150, 270, 380, 480, 580, 680, 790, 880]
    for x, c in zip(xs, cols): d.text((x, 90), c, font=mono(22), fill=(90, 96, 104))
    d.line((30, 122, W - 30, 122), fill=(200, 204, 210), width=2)
    rows = [('07:30', '128/82', '74', '300', '-110', '+130', '0.0', '45', 'started'), ('08:00', '124/80', '72', '300', '-120', '+140', '0.4', '48', ''),
            ('08:30', '122/78', '72', '300', '-120', '+140', '0.8', '50', ''), ('09:00', '', '', '', '', '', '', '', '')]
    for r, row in enumerate(rows):
        y = 140 + r * 56
        for x, v in zip(xs, row): d.text((x, y), v, font=reg(26), fill=INK if v else (160, 164, 170))
        d.line((30, y + 44, W - 30, y + 44), fill=(225, 228, 232), width=1)
    d.rectangle((30, 420, 300, 470), fill=TEAL); d.text((165, 445), 'SAVE ENTRY', font=bold(26), fill=(255, 255, 255), anchor='mm')
    d.text((330, 432), 'next vitals due 09:00', font=mono(22), fill=(90, 96, 104))
    im.save(os.path.join(TEX, 'training_record.png'), optimize=True)
    # the corkboard (12:7): pinned sheets
    W, H = 1200, 700
    im = Image.new('RGB', (W, H), (158, 112, 70)); d = ImageDraw.Draw(im)
    import random
    r = random.Random(7)
    for i in range(1400):
        x, y = r.randrange(W), r.randrange(H); c = r.randrange(-18, 18)
        d.point((x, y), fill=(158 + c, 112 + c, 70 + c))
    sheets = [((60, 60, 380, 460), 'Station checklist', ['1  Hand hygiene', '2  Machine set-up', '3  The chair', '4  Water', '5  Charting']),
              ((430, 90, 760, 330), 'Shift roster', ['Mon  Nia · Okafor', 'Tue  Rae · Hale', 'Wed  open']),
              ((800, 60, 1140, 400), 'Alarm limits', ['Arterial  -250 .. -50', 'Venous   +50 .. +250', 'TMP      < 300', 'Cond.    13.8 .. 14.2']),
              ((460, 380, 1140, 640), 'Water log · chlorine < 0.1 ppm, checked every shift', ['06:00  0.00   RO 98%', '14:00  0.00   RO 98%', '22:00  0.00   RO 97%'])]
    for (box, title, lines) in sheets:
        d.rectangle((box[0] + 6, box[1] + 8, box[2] + 6, box[3] + 8), fill=(120, 84, 50))
        d.rectangle(box, fill=(252, 251, 246))
        d.text((box[0] + 24, box[1] + 22), title, font=semi(30), fill=INK)
        for k, ln in enumerate(lines): d.text((box[0] + 24, box[1] + 74 + k * 42), ln, font=reg(28), fill=(60, 64, 70))
        d.ellipse((box[0] + (box[2] - box[0]) // 2 - 12, box[1] - 10, box[0] + (box[2] - box[0]) // 2 + 12, box[1] + 14), fill=(200, 40, 50))
    im.save(os.path.join(TEX, 'training_cork.png'), optimize=True)
    # the clock face (square)
    S = 512
    im = Image.new('RGB', (S, S), (250, 250, 248)); d = ImageDraw.Draw(im)
    c = S / 2
    for k in range(60):
        a = 2 * math.pi * k / 60; r0 = c - (36 if k % 5 == 0 else 22); r1 = c - 12
        d.line((c + r0 * math.sin(a), c - r0 * math.cos(a), c + r1 * math.sin(a), c - r1 * math.cos(a)), fill=INK, width=8 if k % 5 == 0 else 3)
    for k in range(12):
        a = 2 * math.pi * k / 12; rr = c - 84
        d.text((c + rr * math.sin(a), c - rr * math.cos(a)), '12' if k == 0 else str(k), font=semi(54), fill=INK, anchor='mm')
    for (frac, ln, wd) in ((9.25 / 12, 120, 16), (15 / 60, 180, 10)):
        a = 2 * math.pi * frac
        d.line((c, c, c + ln * math.sin(a), c - ln * math.cos(a)), fill=INK, width=wd)
    d.line((c, c, c + 200 * math.sin(2 * math.pi * 42 / 60), c - 200 * math.cos(2 * math.pi * 42 / 60)), fill=(200, 40, 50), width=4)
    d.ellipse((c - 14, c - 14, c + 14, c + 14), fill=INK)
    im.save(os.path.join(TEX, 'training_clock.png'), optimize=True)
    # the log sheet on the clipboard (portrait 3:4)
    W, H = 600, 800
    im = Image.new('RGB', (W, H), (252, 251, 246)); d = ImageDraw.Draw(im)
    d.text((40, 36), 'WATER TREATMENT LOG', font=bold(36), fill=NAVY)
    d.text((40, 84), 'RO permeate · chlorine · conductivity', font=mono(20), fill=(90, 96, 104))
    for x, cname in zip((40, 150, 290, 440), ('SHIFT', 'Cl ppm', 'COND', 'INIT')): d.text((x, 140), cname, font=mono(22), fill=(90, 96, 104))
    d.line((40, 172, W - 40, 172), fill=INK, width=2)
    for r_ in range(13):
        y = 190 + r_ * 44
        d.line((40, y + 36, W - 40, y + 36), fill=(205, 208, 212), width=1)
        if r_ < 5:
            for x, v in zip((40, 150, 290, 440), (('06', '14', '22', '06', '14')[r_], '0.00', ('14.0', '14.1', '14.0', '13.9', '14.0')[r_], 'NO')):
                d.text((x, y), v, font=reg(26), fill=(50, 54, 60))
    im.save(os.path.join(TEX, 'training_sheet.png'), optimize=True)


# ---------------------------------------------------------------- the room
def room():
    fl = builder('trn_floor', 'trn_floor', tile=2.0); wl = builder('trn_walls', 'trn_wall', tile=3.0)
    ce = builder('trn_ceiling', 'trn_ceiling', tile=1.2); wh = builder('trn_trim', 'trn_white')
    # the floor, and its thresholds through both doorways
    fl.grid(P(RX0, 0.0, RZS), P(RX1, 0.0, RZS) - P(RX0, 0.0, RZS), P(RX0, 0.0, RZN) - P(RX0, 0.0, RZS), D(0, 1, 0), 4, 5)
    z0, z1, _ = WEST_DOOR
    fl.face([P(AUD_X, 0.0, z1), P(RX0, 0.0, z1), P(RX0, 0.0, z0), P(AUD_X, 0.0, z0)], D(0, 1, 0))
    z0, z1, _ = YARD_DOOR
    fl.face([P(RX1, 0.0, z1), P(RX1 + WALL_T, 0.0, z1), P(RX1 + WALL_T, 0.0, z0), P(RX1, 0.0, z0)], D(0, 1, 0))
    # the ceiling (acoustic tile), the T-grid 15 mm under it
    ce.grid(P(RX0, RH, RZN), P(RX1, RH, RZN) - P(RX0, RH, RZN), P(RX0, RH, RZS) - P(RX0, RH, RZN), D(0, -1, 0), 4, 5)
    z = RZN + GRID
    while z < RZS - 0.05:
        wh.box((RX0 + RX1) / 2, RH - 0.0075, z, RX1 - RX0, 0.015, 0.024, faces='yzZ'); z += GRID
    x = RX0 + GRID
    while x < RX1 - 0.05:
        wh.box(x, RH - 0.0075, (RZN + RZS) / 2, 0.024, 0.015, RZS - RZN, faces='yxX'); x += GRID
    # the walls: one face each, holes for the doors and windows (their reveals below); the dado rail and skirting
    # stop at the doors
    wd0, wd1, wdh = WEST_DOOR; yd0, yd1, ydh = YARD_DOOR
    wall_with_openings(wl, (RX0, 0.0, RZS), (0, 0, -1), (0, 1, 0), (1, 0, 0), 0.0, RZS - RZN, RH, [(RZS - wd1, RZS - wd0, 0.0, wdh)], solid=False)
    ops = [(z0 - RZN, z1 - RZN, WIN_Y0, WIN_Y1) for (z0, z1) in EAST_WINDOWS] + [(yd0 - RZN, yd1 - RZN, 0.0, ydh)]
    wall_with_openings(wl, (RX1, 0.0, RZN), (0, 0, 1), (0, 1, 0), (-1, 0, 0), 0.0, RZS - RZN, RH, ops, solid=False)
    ops = [(x0 - RX0, x1 - RX0, WIN_Y0, WIN_Y1) for (x0, x1) in NORTH_WINDOWS]
    wall_with_openings(wl, (RX0, 0.0, RZN), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.0, RX1 - RX0, RH, ops, solid=False)
    wl.grid(P(RX1, 0.0, RZS), P(RX0, 0.0, RZS) - P(RX1, 0.0, RZS), P(RX1, RH, RZS) - P(RX1, 0.0, RZS), D(0, 0, -1), 4, 2)
    trim = [(0.0, SKIRT_H, 0.012), (DADO_Y - 0.03, DADO_Y + 0.03, 0.018)]
    for (a, c, out) in (((RX1, RZS), (RX0, RZS), (0, -1)), ((RX0, RZN), (RX1, RZN), (0, 1)),
                        ((RX0, RZS), (RX0, wd1 + 0.09), (1, 0)), ((RX0, wd0 - 0.09), (RX0, RZN), (1, 0)),
                        ((RX1, RZN), (RX1, yd0 - 0.09), (-1, 0)), ((RX1, yd1 + 0.09), (RX1, RZS), (-1, 0))):
        run_boxes(wh, a, c, out, trim, seg=3.0)
    # the west door: a white architrave on this side (the reveal is the auditorium's walnut, bl/auditorium.py)
    for zz in (wd0 - 0.045, wd1 + 0.045):
        wh.box(RX0 + 0.009, wdh / 2 + 0.045, zz, 0.018, wdh + 0.09, 0.09, faces='XyYzZ')
    wh.box(RX0 + 0.009, wdh + 0.045, (wd0 + wd1) / 2, 0.018, 0.09, wd1 - wd0, faces='XyYzZ')
    # the yard doorway: white reveals through the wall, an architrave, the two leaves standing open into the room
    rv = builder('trn_reveals', 'trn_white')
    for (zz, nz) in ((yd0, 1), (yd1, -1)):
        rv.face([P(RX1, 0.0, zz), P(RX1 + WALL_T, 0.0, zz), P(RX1 + WALL_T, ydh, zz), P(RX1, ydh, zz)], D(0, 0, nz))
    rv.face([P(RX1, ydh, yd0), P(RX1, ydh, yd1), P(RX1 + WALL_T, ydh, yd1), P(RX1 + WALL_T, ydh, yd0)], D(0, -1, 0))
    for zz in (yd0 - 0.045, yd1 + 0.045):
        wh.box(RX1 - 0.009, ydh / 2 + 0.045, zz, 0.018, ydh + 0.09, 0.09, faces='xyYzZ')
    wh.box(RX1 - 0.009, ydh + 0.045, (yd0 + yd1) / 2, 0.018, 0.09, yd1 - yd0, faces='xyYzZ')
    door_leaf((RX1 - 0.05, yd1), 180.0, ydh, -1)         # the south leaf, folded flat against the wall
    door_leaf((RX1 - 0.05, yd0), 105.0, ydh, 1)          # the north leaf, held open by the corner
    # the windows
    for (z0, z1) in EAST_WINDOWS: window('E', z0, z1)
    for (x0, x1) in NORTH_WINDOWS: window('N', x0, x1)
    # the panel lights: a white frame hanging 35 mm under the ceiling, its diffuser lit
    fr = builder('trn_fixtures', 'trn_white'); lp = builder('trn_lamps', 'trn_lamp_e')
    for x in PANELS_X:
        for z in PANELS_Z:
            fr.box(x, RH - 0.0175, z, 1.2, 0.035, 0.6, faces='xXzZ')
            lp.face([P(x - 0.58, RH - 0.035, z - 0.28), P(x + 0.58, RH - 0.035, z - 0.28), P(x + 0.58, RH - 0.035, z + 0.28), P(x - 0.58, RH - 0.035, z + 0.28)], D(0, -1, 0))
            LIGHTS.append(('panel', (x, RH - 0.06, z), (1.0, 0.97, 0.92), 160, (1.2, 0.6)))
    # LED strips: over the water panel and over the course board (the engine lights them as 'screen' bulbs)
    for (cx, cz, sx, sz) in ((24.95, RZN + 0.35, 4.7, 0.05), (RX0 + 0.35, BOARD[0], 0.05, 2.6)):
        fr.box(cx, RH - 0.06, cz, sx, 0.04, sz, faces='xXzZ')
        lp.face([P(cx - sx / 2, RH - 0.08, cz - sz / 2), P(cx + sx / 2, RH - 0.08, cz - sz / 2), P(cx + sx / 2, RH - 0.08, cz + sz / 2), P(cx - sx / 2, RH - 0.08, cz + sz / 2)], D(0, -1, 0))
        LIGHTS.append(('screen', (cx, RH - 0.15, cz), (1.0, 0.98, 0.95), 110, None))
    # the clock on the south wall, the sign over the yard door, the course board on the west wall
    ck = builder('trn_clock', 'trn_clock'); st = builder('trn_steel', 'trn_steel', smooth_deg=50)
    cx, cy = CLOCK
    tube(st, [(cx, cy, RZS - 0.0), (cx, cy, RZS - 0.045)], 0.165, n=28, caps=False)
    disc(st, (cx, cy, RZS - 0.045), (0, 0, -1), 0.165, k=28)
    disc(ck, (cx, cy, RZS - 0.049), (0, 0, -1), 0.15, k=28, tex=True)
    sz_, sw, sh, sy = SIGN
    plate(builder('trn_sign', 'trn_sign'), 'E', sz_, sw, sy, sy + sh, 0.012)
    al = builder('trn_alu', 'trn_steel')
    for (c, w, y0, y1) in ((sz_, sw + 0.04, sy - 0.02, sy), (sz_, sw + 0.04, sy + sh, sy + sh + 0.02), (sz_ - sw / 2 - 0.01, 0.02, sy, sy + sh), (sz_ + sw / 2 + 0.01, 0.02, sy, sy + sh)):
        wall_box(al, 'E', c, w, y0, y1, 0.016)
    bz, bw, bh, by = BOARD
    plate(builder('trn_board', 'trn_board'), 'W', bz, bw, by, by + bh, 0.024)
    wall_box(builder('trn_board_back', 'trn_white'), 'W', bz, bw + 0.04, by - 0.02, by + bh + 0.02, 0.02)
    for (c, w, y0, y1) in ((bz, bw + 0.06, by - 0.03, by), (bz, bw + 0.06, by + bh, by + bh + 0.03), (bz - bw / 2 - 0.015, 0.03, by, by + bh), (bz + bw / 2 + 0.015, 0.03, by, by + bh)):
        wall_box(al, 'W', c, w, y0, y1, 0.026)
    # a pen tray under the board
    al.box(RX0 + 0.04, by - 0.05, bz, 0.08, 0.012, 1.0, faces='xXyYzZ')
    al.box(RX0 + 0.075, by - 0.035, bz, 0.01, 0.03, 1.0, faces='xXyYzZ')


def door_leaf(hinge, open_deg, h, toward):
    """One leaf of the yard's double door, hinged at campus (x, z) a little off the room side of the east wall.
    Closed, it would run along the wall from the hinge in the direction `toward` (+1 south, -1 north: into the
    opening); it has swung open_deg into the room (180 lies folded flat against the wall)."""
    lf = builder('trn_doors', 'trn_white'); gl = builder('trn_glass', 'trn_glass'); st = builder('trn_steel', 'trn_steel', smooth_deg=50)
    hx, hz = hinge
    a = math.radians(open_deg)
    w, t = 0.88, 0.045
    d = (-math.sin(a), toward * math.cos(a))       # along the leaf, hinge to free edge
    n = (-d[1], d[0])                              # a normal to its faces
    side = -toward                                 # n * side faces the room
    ry = math.atan2(-d[1], d[0])
    cx, cz = hx + d[0] * w / 2, hz + d[1] * w / 2
    lf.box(cx, h / 2 - 0.01, cz, w, h - 0.04, t, ry=ry)
    # a vision panel either side (1 mm proud), a push bar on the room side
    for s in (-1, 1):
        px, pz = cx + n[0] * s * (t / 2 + 0.004), cz + n[1] * s * (t / 2 + 0.004)
        u0, u1 = -0.12, 0.12
        pts = [P(px + d[0] * u0, 1.0, pz + d[1] * u0), P(px + d[0] * u1, 1.0, pz + d[1] * u1), P(px + d[0] * u1, 1.8, pz + d[1] * u1), P(px + d[0] * u0, 1.8, pz + d[1] * u0)]
        gl.face(pts, D(n[0] * s, 0, n[1] * s))
    bx, bz = cx + n[0] * side * (t / 2 + 0.05), cz + n[1] * side * (t / 2 + 0.05)
    bar(st, (bx + d[0] * -0.34, 1.0, bz + d[1] * -0.34), (bx + d[0] * 0.34, 1.0, bz + d[1] * 0.34), 0.03)
    for u in (-0.3, 0.3):
        bar(st, (bx + d[0] * u, 1.0, bz + d[1] * u), (bx + d[0] * u - n[0] * side * 0.05, 1.0, bz + d[1] * u - n[1] * side * 0.05), 0.02)


def window(wall, u0, u1):
    """A window in the east or north wall: white reveals through the wall, a frame with a transom at mid-thickness,
    the glass (both faces), a sill board inside and a rolled-up blind at the head."""
    rv = builder('trn_reveals', 'trn_white'); fr = builder('trn_trim', 'trn_white'); gl = builder('trn_glass', 'trn_glass')
    bl = builder('trn_blinds', 'trn_cabinet', smooth_deg=60)
    y0, y1 = WIN_Y0, WIN_Y1
    if wall == 'E':
        xi, xo = RX1, RX1 + WALL_T; xm = (xi + xo) / 2
        for (zz, nz) in ((u0, 1), (u1, -1)):
            rv.face([P(xi, y0, zz), P(xo, y0, zz), P(xo, y1, zz), P(xi, y1, zz)], D(0, 0, nz))
        rv.face([P(xi, y0, u0), P(xi, y0, u1), P(xo, y0, u1), P(xo, y0, u0)], D(0, 1, 0))
        rv.face([P(xi, y1, u0), P(xo, y1, u0), P(xo, y1, u1), P(xi, y1, u1)], D(0, -1, 0))
        f = 0.06; cz = (u0 + u1) / 2; w = u1 - u0
        for (cy, czz, sy, szz) in ((y0 + f / 2, cz, f, w), (y1 - f / 2, cz, f, w), ((y0 + y1) / 2, u0 + f / 2, y1 - y0, f), ((y0 + y1) / 2, u1 - f / 2, y1 - y0, f), ((y0 + y1) / 2, cz, 0.04, w)):
            fr.box(xm, cy, czz, 0.09, sy, szz)
        pts = [P(xm, y0 + f, u0 + f), P(xm, y0 + f, u1 - f), P(xm, y1 - f, u1 - f), P(xm, y1 - f, u0 + f)]
        gl.face(pts, D(-1, 0, 0)); gl.face(list(reversed(pts)), D(1, 0, 0))
        fr.box(xi - 0.04, y0 - 0.015, cz, 0.08 + 0.02, 0.03, w + 0.12)
        tube(bl, [(xi + 0.05, y1 - 0.045, u0 + 0.02), (xi + 0.05, y1 - 0.045, u1 - 0.02)], 0.035, n=14)
    else:
        zi, zo = RZN, RZN - WALL_T; zm = (zi + zo) / 2
        for (xx, nx) in ((u0, 1), (u1, -1)):
            rv.face([P(xx, y0, zi), P(xx, y0, zo), P(xx, y1, zo), P(xx, y1, zi)], D(nx, 0, 0))
        rv.face([P(u0, y0, zi), P(u1, y0, zi), P(u1, y0, zo), P(u0, y0, zo)], D(0, 1, 0))
        rv.face([P(u0, y1, zi), P(u0, y1, zo), P(u1, y1, zo), P(u1, y1, zi)], D(0, -1, 0))
        f = 0.06; cx = (u0 + u1) / 2; w = u1 - u0
        for (cy, cxx, sy, sxx) in ((y0 + f / 2, cx, f, w), (y1 - f / 2, cx, f, w), ((y0 + y1) / 2, u0 + f / 2, y1 - y0, f), ((y0 + y1) / 2, u1 - f / 2, y1 - y0, f), ((y0 + y1) / 2, cx, 0.04, w)):
            fr.box(cxx, cy, zm, sxx, sy, 0.09)
        pts = [P(u0 + f, y0 + f, zm), P(u1 - f, y0 + f, zm), P(u1 - f, y1 - f, zm), P(u0 + f, y1 - f, zm)]
        gl.face(pts, D(0, 0, 1)); gl.face(list(reversed(pts)), D(0, 0, -1))
        fr.box(cx, y0 - 0.015, zi + 0.04, w + 0.12, 0.03, 0.08 + 0.02)
        tube(bl, [(u0 + 0.02, y1 - 0.045, zi - 0.05), (u1 - 0.02, y1 - 0.045, zi - 0.05)], 0.035, n=14)


# ---------------------------------------------------------------- the chairs
def chair(cx, cz, seat_name, yaw_face=0.0, shell='trn_shell'):
    """A moulded-shell chair on a four-leg steel frame (the classroom's), the tagged seat its seat pan.
    Facing +x when yaw_face = 0."""
    sh = builder(seat_name, shell)
    back = builder('trn_chair_backs', shell, smooth_deg=35)
    st = builder('trn_grey', 'trn_grey')
    cr, sr = math.cos(yaw_face), math.sin(yaw_face)
    def W(u, v): return (cx + u * cr - v * sr, cz + u * sr + v * cr)
    sy = 0.43
    sh.box(cx, sy + 0.015, cz, 0.42, 0.03, 0.44, ry=-yaw_face)
    n = 8; R = 0.55; half = 0.21
    for i in range(n):
        a0 = -half / R + (2 * half / R) * i / n; a1 = -half / R + (2 * half / R) * (i + 1) / n
        pts = []
        for (a, y) in ((a0, 0.52), (a1, 0.52), (a1, 0.84), (a0, 0.84)):
            lean = (y - 0.52) * 0.18
            u = -0.21 - lean - (R - R * math.cos(a)) * 0.6
            v = R * math.sin(a)
            x_, z_ = W(u, v)
            pts.append(P(x_, y, z_))
        nm = D(math.cos(yaw_face), 0.0, math.sin(yaw_face))
        back.face(pts, nm)
        back.face(list(reversed([p + D(-math.cos(yaw_face), 0, -math.sin(yaw_face)) * 0.012 for p in pts])), -nm)
    for (u, v) in ((0.17, -0.18), (0.17, 0.18), (-0.17, -0.18), (-0.19, 0.18)):
        x_, z_ = W(u, v)
        st.box(x_, sy / 2, z_, 0.022, sy, 0.022, ry=-yaw_face)
    for (u0, v0, u1, v1) in ((0.17, -0.18, 0.17, 0.18), (-0.17, -0.18, -0.17, 0.18), (0.17, -0.18, -0.17, -0.18), (0.17, 0.18, -0.17, 0.18)):
        a = W(u0, v0); c = W(u1, v1)
        bar(st, (a[0], sy - 0.012, a[1]), (c[0], sy - 0.012, c[1]), 0.02)
    for v in (-0.15, 0.15):
        a = W(-0.19, v); c = W(-0.24, v)
        bar(st, (a[0], sy - 0.012, a[1]), (c[0], 0.60, c[1]), 0.02)


def task_chair(cx, cz, seat_name, f):
    """An office task chair facing the campus direction f: a five-star base on castors, a gas column, the seat pan
    (tagged), a leaning backrest on a spine, two armrests."""
    ch = builder('trn_chrome', 'trn_chrome', smooth_deg=50); bk = builder('trn_black', 'trn_black', smooth_deg=50)
    se = builder(seat_name, 'trn_fabric'); fb = builder('trn_fabric', 'trn_fabric')
    (rx, rz), ry = facing(f)
    def W(u, v): return (cx + u * f[0] + v * rx, cz + u * f[1] + v * rz)
    for k in range(5):
        a = 2 * math.pi * k / 5 + math.pi / 2
        tip = (cx + 0.30 * math.cos(a), 0.06, cz + 0.30 * math.sin(a))
        bar(bk, (cx, 0.10, cz), tip, 0.04, 0.03)
        lathe(bk, tip[0], tip[2], [(0.0, 0.0), (0.0, 0.025), (0.05, 0.025), (0.05, 0.0)], n=8, cap_top=False)
    lathe(ch, cx, cz, [(0.08, 0.03), (0.30, 0.03), (0.30, 0.022), (0.43, 0.022)], n=12, cap_top=True)
    bk.box(cx, 0.445, cz, 0.30, 0.03, 0.30, ry=ry)
    se.box(cx, 0.49, cz, 0.47, 0.06, 0.47, ry=ry)                                          # the sitting surface at 0.52
    # the spine and the backrest, leaning 12 degrees
    a_, c_ = W(-0.22, 0.0), W(-0.30, 0.0)
    bar(bk, (a_[0], 0.47, a_[1]), (c_[0], 0.72, c_[1]), 0.05, 0.03)
    lean = math.tan(math.radians(12))
    corners = []
    for (y, uu) in ((0.62, -0.26), (1.02, -0.26 - 0.40 * lean)):
        for (u, v) in ((uu + 0.05, -0.21), (uu + 0.05, 0.21), (uu - 0.0, 0.21), (uu - 0.0, -0.21)):
            x_, z_ = W(u, v); corners.append((x_, y, z_))
    hexa(fb, corners)
    for s in (-1, 1):
        a_ = W(0.0, s * 0.26); c_ = W(0.0, s * 0.26)
        bar(bk, (a_[0], 0.50, a_[1]), (c_[0], 0.70, c_[1]), 0.03)
        a_ = W(-0.12, s * 0.26); c_ = W(0.14, s * 0.26)
        bar(bk, (a_[0], 0.72, a_[1]), (c_[0], 0.72, c_[1]), 0.05, 0.03)


def chairs():
    names = []
    for k, x in enumerate(CHAIRS_X, 1):
        name = 'seat__training_c%d_f%d' % (k, seat_yaw(0.0, -1.0))
        chair(x, CHAIRS_Z, name, yaw_face=-math.pi / 2)     # facing north (-z)
        names.append(name)
    return names


# ---------------------------------------------------------------- dx-hygiene: the sink unit
def sink_unit():
    cx, cz = SINK
    w, dpt, top = 1.6, 0.6, 0.86
    cb = builder('trn_cabinets', 'trn_cabinet'); st = builder('trn_steel', 'trn_steel', smooth_deg=50)
    bk = builder('trn_black', 'trn_black', smooth_deg=50); wh = builder('trn_appliances', 'trn_enamel', smooth_deg=45)
    pp = builder('trn_paper', 'trn_paper')
    # the cabinet on a recessed black kick, two door fronts with bar handles
    bk.box(cx, 0.05, cz, w - 0.08, 0.10, dpt - 0.06, faces='xXz')
    cb.box(cx, 0.10 + (top - 0.10) / 2, cz, w, top - 0.10, dpt, faces='xXyz')
    for s in (-1, 1):
        cb.box(cx + s * 0.4, 0.10 + (top - 0.10) / 2, cz - dpt / 2 - 0.009, 0.76, top - 0.14, 0.018, faces='xXyYz')
        bar(st, (cx + s * 0.08, 0.60, cz - dpt / 2 - 0.04), (cx + s * 0.08, 0.72, cz - dpt / 2 - 0.04), 0.012)
    # a stainless counter with an upstand, the basin let into it
    bx, bz, bw, bd, bdeep = cx - 0.1, cz, 0.5, 0.4, 0.17
    x0, x1, z0, z1 = cx - w / 2, cx + w / 2, cz - dpt / 2 - 0.02, cz + dpt / 2
    bx0, bx1, bz0, bz1 = bx - bw / 2, bx + bw / 2, bz - bd / 2, bz + bd / 2
    yt = top + 0.04
    for (xa, xb, za, zb) in ((x0, bx0, z0, z1), (bx1, x1, z0, z1), (bx0, bx1, z0, bz0), (bx0, bx1, bz1, z1)):
        st.face([P(xa, yt, zb), P(xb, yt, zb), P(xb, yt, za), P(xa, yt, za)], D(0, 1, 0))
    st.box(cx, top + 0.02, cz - 0.01, w, 0.04, dpt + 0.02, faces='xXz')
    st.box(cx, yt + 0.05, z1 - 0.02, w, 0.10, 0.04, faces='xXzY')          # the upstand against the wall
    st.face([P(bx0, yt - bdeep, bz0), P(bx1, yt - bdeep, bz0), P(bx1, yt - bdeep, bz1), P(bx0, yt - bdeep, bz1)], D(0, 1, 0))
    for (pa, pb, n) in (((bx0, bz0), (bx1, bz0), (0, 1)), ((bx1, bz0), (bx1, bz1), (-1, 0)), ((bx1, bz1), (bx0, bz1), (0, -1)), ((bx0, bz1), (bx0, bz0), (1, 0))):
        st.face([P(pa[0], yt - bdeep, pa[1]), P(pb[0], yt - bdeep, pb[1]), P(pb[0], yt, pb[1]), P(pa[0], yt, pa[1])], D(n[0], 0, n[1]))
    lathe(bk, bx, bz, [(yt - bdeep + 0.001, 0.0), (yt - bdeep + 0.001, 0.03)], n=12)      # the drain
    # a tall gooseneck tap with two lever handles
    tx, tz = bx, bz1 + 0.07
    lathe(st, tx, tz, [(yt, 0.035), (yt + 0.02, 0.03), (yt + 0.03, 0.02)], n=12)
    pts = [(tx, yt + 0.02, tz)]
    for k in range(9):
        a = math.pi / 2 * k / 8
        pts.append((tx, yt + 0.24 + 0.14 * math.sin(a), tz - 0.14 + 0.14 * math.cos(a)))
    pts.append((tx, yt + 0.19, tz - 0.14))
    tube(st, pts, 0.012, n=10)
    for s in (-1, 1):
        lathe(st, tx + s * 0.07, tz, [(yt, 0.022), (yt + 0.025, 0.018)], n=10)
        bar(st, (tx + s * 0.07, yt + 0.025, tz), (tx + s * 0.07, yt + 0.045, tz + 0.06), 0.012)
    # on the wall: the soap dispenser, the paper-towel dispenser with its tongue, the glove-box holder
    wall_box(wh, 'S', cx + 0.55, 0.10, 1.18, 1.36, 0.10)
    bk.box(cx + 0.55, 1.17, RZS - 0.09, 0.08, 0.02, 0.04)
    wall_box(wh, 'S', cx - 0.55, 0.30, 1.30, 1.66, 0.12)
    bk.box(cx - 0.55, 1.33, RZS - 0.122, 0.22, 0.03, 0.004, faces='z')
    pp.face([P(cx - 0.47, 1.32, RZS - 0.11), P(cx - 0.63, 1.32, RZS - 0.11), P(cx - 0.63, 1.22, RZS - 0.10), P(cx - 0.47, 1.22, RZS - 0.10)], D(0, 0, -1))
    gx, gy = cx, 1.42
    pp.box(gx, gy, RZS - 0.07, 0.24, 0.12, 0.09)
    wh.box(gx, gy + 0.005, RZS - 0.07, 0.241, 0.03, 0.091, faces='xXzZ')
    bk.box(gx, gy + 0.02, RZS - 0.119, 0.10, 0.025, 0.002, faces='z')
    for (ax, az) in ((gx - 0.13, RZS - 0.02), (gx + 0.13, RZS - 0.02)):
        bar(st, (ax, gy - 0.07, az), (ax, gy - 0.07, az - 0.10), 0.006)
        bar(st, (ax, gy - 0.07, az - 0.10), (ax, gy + 0.07, az - 0.10), 0.006)
        bar(st, (ax, gy + 0.07, az - 0.10), (ax, gy + 0.07, az), 0.006)
    bar(st, (gx - 0.13, gy - 0.07, RZS - 0.115), (gx + 0.13, gy - 0.07, RZS - 0.115), 0.006)
    # the pedal bin at the cabinet's east end
    px, pz = cx + w / 2 + 0.22, cz
    lathe(st, px, pz, [(0.0, 0.13), (0.42, 0.13)], n=16, cap_top=False, cap_bot=False)
    lathe(bk, px, pz, [(0.42, 0.135), (0.45, 0.135), (0.47, 0.12), (0.47, 0.0)], n=16, cap_top=True)
    bk.box(px, 0.015, pz - 0.16, 0.08, 0.03, 0.06)
    label(builder('trn_labels', 'trn_labels'), 'S', cx, 0.6, 2.05, 2.2, 0)


# ---------------------------------------------------------------- dx-machine and dx-chair
def dialysis_machine():
    cx, cz = MACHINE
    sx, sz = 0.55, 0.50
    wh = builder('trn_appliances', 'trn_enamel', smooth_deg=45); bk = builder('trn_black', 'trn_black', smooth_deg=50)
    gy = builder('trn_grey', 'trn_grey'); st = builder('trn_steel', 'trn_steel', smooth_deg=50)
    rd = builder('trn_red', 'trn_red', smooth_deg=60); gl = builder('trn_glass', 'trn_glass')
    pp = builder('trn_paper', 'trn_paper'); led = builder('trn_leds', 'trn_led_e')
    xf = cx - sx / 2                                  # the front face (toward the room, -x)
    # the chassis on four castors, the cabinet, a darker control band
    bk.box(cx, 0.10, cz, sx - 0.04, 0.08, sz - 0.04)
    for (dx, dz) in ((-0.2, -0.18), (0.2, -0.18), (-0.2, 0.18), (0.2, 0.18)):
        lathe(bk, cx + dx, cz + dz, [(0.0, 0.0), (0.0, 0.04), (0.06, 0.04), (0.06, 0.0)], n=10, cap_top=False)
    wh.box(cx, 0.14 + 1.08 / 2, cz, sx, 1.08, sz, faces='xXyYzZ')
    gy.box(xf - 0.006, 0.60, cz, 0.012, 0.36, sz - 0.08)
    # the blood-pump module: a round door with a dark rim and a clear window, a lever handle
    for (dz, r, dy) in ((-0.10, 0.10, 0.70), (0.12, 0.07, 0.70)):
        tube(bk, [(xf, dy, cz + dz), (xf - 0.03, dy, cz + dz)], r, n=20, caps=False)
        disc(bk, (xf - 0.03, dy, cz + dz), (-1, 0, 0), r, k=20)
        disc(gl, (xf - 0.034, dy, cz + dz), (-1, 0, 0), r * 0.75, k=20)
        disc(wh, (xf - 0.025, dy, cz + dz), (-1, 0, 0), r * 0.55, k=12)
    bar(st, (xf - 0.035, 0.70, cz - 0.10), (xf - 0.06, 0.78, cz - 0.10), 0.012)
    # keys and indicator lights on the band, a drip tray lip, the screen on its tilted arm
    for k in range(5):
        gy.box(xf - 0.016, 0.46, cz - 0.12 + k * 0.06, 0.008, 0.03, 0.04, faces='xyYzZ')
    led.face([P(xf - 0.004, 1.16, cz - 0.14), P(xf - 0.004, 1.16, cz - 0.06), P(xf - 0.004, 1.19, cz - 0.06), P(xf - 0.004, 1.19, cz - 0.14)], D(-1, 0, 0))
    wh.box(xf - 0.02, 0.985, cz, 0.04, 0.03, sz - 0.1, faces='xyYzZ')
    tilt = math.radians(22)
    sw, sh = 0.40, 0.30
    n = (-math.cos(tilt), math.sin(tilt), 0.0)                     # the screen faces the room and up
    up = (math.sin(tilt), math.cos(tilt), 0.0)
    c = (xf + 0.10, 1.42, cz)
    bar(bk, (cx - 0.05, 1.22, cz), (c[0] - n[0] * 0.03, c[1] - n[1] * 0.03, cz), 0.04, 0.03)
    def corner(u, v, w_):
        return (c[0] + n[0] * w_ + up[0] * v, c[1] + n[1] * w_ + up[1] * v, c[2] + u)
    bottom = [corner(-sw / 2 - 0.02, -sh / 2 - 0.02, -0.03), corner(sw / 2 + 0.02, -sh / 2 - 0.02, -0.03), corner(sw / 2 + 0.02, sh / 2 + 0.02, -0.03), corner(-sw / 2 - 0.02, sh / 2 + 0.02, -0.03)]
    front = [corner(-sw / 2 - 0.02, -sh / 2 - 0.02, 0.0), corner(sw / 2 + 0.02, -sh / 2 - 0.02, 0.0), corner(sw / 2 + 0.02, sh / 2 + 0.02, 0.0), corner(-sw / 2 - 0.02, sh / 2 + 0.02, 0.0)]
    hexa(bk, bottom + front)
    # seen from the room (looking +x) the viewer's left is -z
    sc = builder('trn_screen', 'trn_screen_e')
    pts = [P(*corner(-sw / 2, -sh / 2, 0.004)), P(*corner(sw / 2, -sh / 2, 0.004)), P(*corner(sw / 2, sh / 2, 0.004)), P(*corner(-sw / 2, sh / 2, 0.004))]
    face_uv(sc, pts, D(*n), UV01)
    # the dialyzer in a holder on the chair side (north face), its blood lines to the pump and to the venous chamber
    hz = cz - sz / 2
    dx_, dz_ = cx - 0.05, hz - 0.06
    for y in (0.88, 1.12):
        wh.box(dx_ + 0.01, y, hz - 0.035, 0.05, 0.02, 0.07, faces='xXyYz')
    lathe(gl, dx_, dz_, [(0.86, 0.03), (1.14, 0.03)], n=14, cap_top=False, cap_bot=False)
    lathe(pp, dx_, dz_, [(0.86, 0.024), (1.14, 0.024)], n=12, cap_top=True, cap_bot=True)
    for (ya, yb) in ((0.84, 0.86), (1.14, 1.16)):
        lathe(rd, dx_, dz_, [(ya, 0.032), (yb, 0.032)], n=14, cap_top=True, cap_bot=True)
    # the venous chamber on the front, with its level
    tube(gl, [(xf - 0.02, 0.86, cz + 0.17), (xf - 0.02, 1.02, cz + 0.17)], 0.018, n=12)
    tube(rd, [(xf - 0.02, 0.861, cz + 0.17), (xf - 0.02, 0.95, cz + 0.17)], 0.014, n=12)
    wh.box(xf - 0.01, 1.03, cz + 0.17, 0.03, 0.02, 0.05, faces='xyYzZ')
    # the blood circuit: the arterial line from the patient's arm (on the armrest nearest the machine) up into the
    # pump; from the pump round the cabinet's corner to the dialyzer's bottom port; from its top port round to the
    # venous chamber; and the venous line from the chamber back down to the arm
    ax, az = TCHAIR[0] - 0.05, TCHAIR[1] + 0.36
    tube(rd, [(ax - 0.03, 0.80, az + 0.02), (ax + 0.10, 0.75, az + 0.04), (ax + 0.27, 0.49, az + 0.13), (xf - 0.12, 0.47, cz - 0.08), (xf - 0.06, 0.58, cz - 0.11), (xf - 0.03, 0.62, cz - 0.10)], 0.005, n=6)
    tube(rd, [(xf - 0.03, 0.78, cz - 0.17), (xf - 0.08, 0.84, cz - 0.23), (dx_ - 0.05, 0.76, dz_ + 0.02), (dx_, 0.80, dz_), (dx_, 0.835, dz_)], 0.005, n=6)
    tube(rd, [(dx_, 1.165, dz_), (dx_ - 0.02, 1.22, dz_ - 0.04), (xf - 0.035, 1.21, dz_), (xf - 0.075, 1.14, cz + 0.05), (xf - 0.05, 1.08, cz + 0.17), (xf - 0.02, 1.045, cz + 0.17)], 0.005, n=6)
    tube(rd, [(xf - 0.02, 0.845, cz + 0.17), (xf - 0.03, 0.70, cz + 0.12), (ax + 0.25, 0.52, az + 0.10), (ax + 0.08, 0.76, az + 0.02), (ax - 0.05, 0.80, az)], 0.005, n=6)
    # the IV pole with a saline bag on a hook, its line to the machine
    px, pz = IV_POLE
    for k in range(5):
        a = 2 * math.pi * k / 5
        bar(st, (px, 0.05, pz), (px + 0.26 * math.cos(a), 0.03, pz + 0.26 * math.sin(a)), 0.025, 0.02)
        lathe(bk, px + 0.26 * math.cos(a), pz + 0.26 * math.sin(a), [(0.0, 0.0), (0.0, 0.02), (0.035, 0.02), (0.035, 0.0)], n=8, cap_top=False)
    lathe(st, px, pz, [(0.03, 0.014), (1.85, 0.014), (1.85, 0.0)], n=10, cap_top=False)
    for s in (-1, 1):
        bar(st, (px, 1.85, pz), (px + s * 0.12, 1.85, pz), 0.012)
        bar(st, (px + s * 0.12, 1.85, pz), (px + s * 0.12, 1.78, pz), 0.012)
    bg = builder('trn_bags', 'trn_bag', smooth_deg=60)
    bg.box(px + 0.12, 1.66, pz, 0.12, 0.22, 0.045)
    pp.face([P(px + 0.07, 1.62, pz - 0.026), P(px + 0.17, 1.62, pz - 0.026), P(px + 0.17, 1.72, pz - 0.026), P(px + 0.07, 1.72, pz - 0.026)], D(0, 0, -1))
    gl.face([P(px + 0.12 - 0.015, 1.52, pz - 0.02), P(px + 0.12 + 0.015, 1.52, pz - 0.02), P(px + 0.12 + 0.015, 1.55, pz - 0.02), P(px + 0.12 - 0.015, 1.55, pz - 0.02)], D(0, 0, -1))
    tube(gl, [(px + 0.12, 1.55, pz), (px + 0.12, 1.30, pz + 0.02), (px + 0.3, 1.10, pz - 0.2), (xf - 0.02, 1.00, cz + 0.22), (xf - 0.02, 1.02, cz + 0.17)], 0.004, n=6)
    label(builder('trn_labels', 'trn_labels'), 'E', cz - 0.2, 0.5, 2.5, 2.625, 1)


def treatment_chair():
    cx, cz = TCHAIR
    f = (-1.0, 0.0)                                  # facing west
    (rx, rz), ry = facing(f)
    def W(u, v): return (cx + u * f[0] + v * rx, cz + u * f[1] + v * rz)
    vn = builder('trn_vinyl', 'trn_vinyl'); ch = builder('trn_chrome', 'trn_chrome', smooth_deg=50); bk = builder('trn_black', 'trn_black', smooth_deg=50)
    lathe(ch, cx + 0.05, cz, [(0.0, 0.32), (0.03, 0.32), (0.05, 0.22), (0.07, 0.08), (0.40, 0.08)], n=20, cap_top=False)
    bk.box(cx + 0.05, 0.42, cz, 0.55, 0.04, 0.55, ry=ry)
    vn.box(cx, 0.49, cz, 0.58, 0.10, 0.64, ry=ry)                                  # the seat, its top at 0.54
    # the backrest leans back 24 degrees from the seat's back edge, a headrest at its top
    lean = math.radians(24)
    def slab(u0, y0, length, width, thick, ang):
        """A padded slab from (u0, y0) rising `length` along a line tilted `ang` back from vertical."""
        su, sy = -math.sin(ang), math.cos(ang)                   # along the slab (u, y), leaning toward -u (behind)
        nu, ny = math.cos(ang), math.sin(ang)                    # its front normal (u, y)
        ring = lambda w_, l_: [(u0 + su * l_ + nu * w_, y0 + sy * l_ + ny * w_, v) for v in (-width / 2, width / 2)]
        b0 = ring(-thick, 0.0); f0 = ring(0.0, 0.0); b1 = ring(-thick, length); f1 = ring(0.0, length)
        def pt(p): x_, z_ = W(p[0], p[2]); return (x_, p[1], z_)
        hexa(vn, [pt(b0[0]), pt(b0[1]), pt(f0[1]), pt(f0[0]), pt(b1[0]), pt(b1[1]), pt(f1[1]), pt(f1[0])])
    slab(-0.29, 0.54, 0.72, 0.62, 0.11, lean)
    slab(-0.29 - 0.72 * math.sin(lean) + 0.02, 0.54 + 0.72 * math.cos(lean), 0.20, 0.32, 0.09, lean)
    # armrests on chrome posts, the leg rest raised 18 degrees on a chrome strut
    for s in (-1, 1):
        a_ = W(-0.05, s * 0.36)
        vn.box(a_[0], 0.76, a_[1], 0.48, 0.05, 0.09, ry=ry)
        for u in (-0.20, 0.12):
            p_ = W(u, s * 0.36)
            bar(ch, (p_[0], 0.50, p_[1]), (p_[0], 0.735, p_[1]), 0.025)
    rise = math.radians(18)
    def legrest(u0, y0, length, width, thick, ang):
        su, sy = math.cos(ang), math.sin(ang)
        nu, ny = -math.sin(ang), math.cos(ang)
        ring = lambda w_, l_: [(u0 + su * l_ + nu * w_, y0 + sy * l_ + ny * w_, v) for v in (-width / 2, width / 2)]
        b0 = ring(-thick, 0.0); t0 = ring(0.0, 0.0); b1 = ring(-thick, length); t1 = ring(0.0, length)
        def pt(p): x_, z_ = W(p[0], p[2]); return (x_, p[1], z_)
        hexa(vn, [pt(b0[0]), pt(b0[1]), pt(b1[1]), pt(b1[0]), pt(t0[0]), pt(t0[1]), pt(t1[1]), pt(t1[0])])
    legrest(0.29, 0.50, 0.62, 0.50, 0.09, rise)
    a_ = W(0.30, 0.0); c_ = W(0.80, 0.0)
    bar(ch, (a_[0], 0.40, a_[1]), (c_[0], 0.54, c_[1]), 0.03)
    label(builder('trn_labels', 'trn_labels'), 'E', cz - 0.3, 0.5, 2.5, 2.625, 2)


def bp_monitor():
    cx, cz = BP_STAND
    ch = builder('trn_chrome', 'trn_chrome', smooth_deg=50); bk = builder('trn_black', 'trn_black', smooth_deg=50)
    wh = builder('trn_appliances', 'trn_enamel', smooth_deg=45); gy = builder('trn_grey', 'trn_grey')
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.3
        bar(ch, (cx, 0.05, cz), (cx + 0.27 * math.cos(a), 0.03, cz + 0.27 * math.sin(a)), 0.025, 0.02)
        lathe(bk, cx + 0.27 * math.cos(a), cz + 0.27 * math.sin(a), [(0.0, 0.0), (0.0, 0.02), (0.035, 0.02), (0.035, 0.0)], n=8, cap_top=False)
    lathe(ch, cx, cz, [(0.03, 0.014), (1.22, 0.014)], n=10, cap_top=True)
    # a basket for the cuff, the monitor on top tilted toward the chair (west), its readout lit
    gy.box(cx, 0.85, cz, 0.22, 0.02, 0.16)
    for (dx, dz) in ((-0.1, 0), (0.1, 0)):
        bar(gy, (cx + dx, 0.85, cz - 0.08), (cx + dx, 0.95, cz - 0.08), 0.008); bar(gy, (cx + dx, 0.85, cz + 0.08), (cx + dx, 0.95, cz + 0.08), 0.008)
        bar(gy, (cx + dx, 0.95, cz - 0.08), (cx + dx, 0.95, cz + 0.08), 0.008)
    tube(gy, [(cx - 0.09, 0.90, cz), (cx + 0.09, 0.90, cz)], 0.045, n=10)                   # the cuff, rolled
    tube(gy, [(cx + 0.09, 0.90, cz), (cx + 0.14, 0.95, cz), (cx + 0.06, 1.10, cz + 0.02), (cx - 0.08, 1.20, cz)], 0.005, n=6)
    tilt = math.radians(15)
    n = (-math.cos(tilt), math.sin(tilt), 0.0); up = (math.sin(tilt), math.cos(tilt), 0.0)
    c = (cx - 0.02, 1.32, cz)
    def corner(u, v, w_): return (c[0] + n[0] * w_ + up[0] * v, c[1] + n[1] * w_ + up[1] * v, c[2] + u)
    sw, sh = 0.20, 0.15
    hexa(wh, [corner(-0.11, -0.085, -0.08), corner(0.11, -0.085, -0.08), corner(0.11, 0.085, -0.08), corner(-0.11, 0.085, -0.08),
              corner(-0.11, -0.085, 0.0), corner(0.11, -0.085, 0.0), corner(0.11, 0.085, 0.0), corner(-0.11, 0.085, 0.0)])
    sc = builder('trn_bp', 'trn_bp_e')
    face_uv(sc, [P(*corner(-0.09, -0.065, 0.004)), P(*corner(0.09, -0.065, 0.004)), P(*corner(0.09, 0.065, 0.004)), P(*corner(-0.09, 0.065, 0.004))], D(*n), UV01)


def floor_scale():
    cx, cz = SCALE
    gy = builder('trn_grey', 'trn_grey'); bk = builder('trn_black', 'trn_black'); led = builder('trn_leds', 'trn_led_e')
    gy.box(cx, 0.03, cz, 0.36, 0.06, 0.42)
    bk.box(cx, 0.062, cz, 0.32, 0.004, 0.38, faces='Y')
    gy.box(cx + 0.15, 0.70, cz, 0.04, 1.28, 0.05)
    gy.box(cx + 0.06, 1.34, cz, 0.22, 0.10, 0.16)
    led.face([P(cx - 0.054, 1.30, cz - 0.07), P(cx - 0.054, 1.30, cz + 0.07), P(cx - 0.054, 1.38, cz + 0.07), P(cx - 0.054, 1.38, cz - 0.07)], D(-1, 0, 0))


# ---------------------------------------------------------------- dx-water: the water panel
def water_panel():
    bl = builder('trn_blue', 'trn_blue', smooth_deg=60); bk = builder('trn_black', 'trn_black', smooth_deg=50)
    wh = builder('trn_appliances', 'trn_enamel', smooth_deg=45); st = builder('trn_steel', 'trn_steel', smooth_deg=50)
    gy = builder('trn_grey', 'trn_grey'); pp = builder('trn_paper', 'trn_paper'); cb = builder('trn_cabinets', 'trn_cabinet')
    pv = builder('trn_pipes', 'trn_white', smooth_deg=60); gl = builder('trn_glass', 'trn_glass'); led = builder('trn_leds', 'trn_led_e')
    # two carbon tanks with domed tops and valve heads, piped together
    for (tx, tz) in TANKS:
        lathe(bl, tx, tz, [(0.0, 0.25), (0.03, 0.27), (1.15, 0.27), (1.32, 0.22), (1.42, 0.13), (1.46, 0.06)], n=20, cap_top=True, cap_bot=False)
        bk.box(tx, 1.53, tz, 0.16, 0.14, 0.16)
        lathe(bk, tx, tz, [(1.60, 0.05), (1.64, 0.055), (1.66, 0.0)], n=12, cap_top=True)
        bar(gy, (tx - 0.09, 1.56, tz), (tx + 0.09, 1.56, tz), 0.03)
    (t0x, t0z), (t1x, t1z) = TANKS
    rx, rz = RO_UNIT
    w, d, h = 0.80, 0.40, 1.30
    tube(pv, [(t0x + 0.08, 1.53, t0z), (t1x - 0.08, 1.53, t1z)], 0.02, n=10)                       # tank to tank
    tube(pv, [(t1x + 0.08, 1.53, t1z), (t1x + 0.42, 1.53, t1z), (t1x + 0.42, 1.28, t1z), (rx - w / 2 - 0.07, 1.28, rz + 0.06)], 0.02, n=10)   # on to the RO unit
    tube(pv, [(t0x - 0.08, 1.53, t0z), (t0x - 0.36, 1.53, t0z), (t0x - 0.36, 0.30, t0z), (t0x - 0.36, 0.30, RZN - 0.01)], 0.02, n=10)        # the feed, from the wall
    # the RO unit: a white steel frame, two membrane housings lying along x, a pump, two gauges facing the room
    for (dx, dz) in ((-w / 2, -d / 2), (w / 2, -d / 2), (-w / 2, d / 2), (w / 2, d / 2)):
        bar(wh, (rx + dx, 0.0, rz + dz), (rx + dx, h, rz + dz), 0.03)
    for y in (0.08, h):
        bar(wh, (rx - w / 2, y, rz - d / 2), (rx + w / 2, y, rz - d / 2), 0.03); bar(wh, (rx - w / 2, y, rz + d / 2), (rx + w / 2, y, rz + d / 2), 0.03)
        bar(wh, (rx - w / 2, y, rz - d / 2), (rx - w / 2, y, rz + d / 2), 0.03); bar(wh, (rx + w / 2, y, rz - d / 2), (rx + w / 2, y, rz + d / 2), 0.03)
    for y in (0.78, 1.06):
        tube(wh, [(rx - w / 2 + 0.02, y, rz + 0.06), (rx + w / 2 - 0.02, y, rz + 0.06)], 0.058, n=16)
        for s in (-1, 1):
            tube(bk, [(rx + s * (w / 2 - 0.02), y, rz + 0.06), (rx + s * (w / 2 + 0.01), y, rz + 0.06)], 0.062, n=16)
    tube(pv, [(rx + w / 2 + 0.01, 0.78, rz + 0.06), (rx + w / 2 + 0.07, 0.78, rz + 0.06), (rx + w / 2 + 0.07, 1.06, rz + 0.06), (rx + w / 2 + 0.01, 1.06, rz + 0.06)], 0.012, n=8)
    tube(pv, [(rx - w / 2 - 0.01, 1.06, rz + 0.06), (rx - w / 2 - 0.07, 1.06, rz + 0.06), (rx - w / 2 - 0.07, 1.27, rz + 0.06)], 0.012, n=8)
    gy.box(rx - 0.15, 0.30, rz, 0.26, 0.22, 0.24)
    tube(gy, [(rx - 0.02, 0.33, rz), (rx + 0.28, 0.33, rz)], 0.09, n=14)
    gy.box(rx + 0.1, 0.60, rz, 0.5, 0.03, 0.34)
    zf = rz + d / 2                                                 # the unit's front, toward the room (+z)
    for gx in (rx - 0.18, rx + 0.18):
        tube(st, [(gx, 1.20, zf), (gx, 1.20, zf + 0.03)], 0.05, n=16, caps=False)
        disc(pp, (gx, 1.20, zf + 0.03), (0, 0, 1), 0.05, k=16)
        bar(bk, (gx, 1.20, zf + 0.034), (gx - 0.025, 1.235, zf + 0.034), 0.004)
        bar(bk, (gx, 1.20, zf + 0.034), (gx + 0.012, 1.18, zf + 0.034), 0.004)
    led.face([P(rx - 0.05, 1.20, zf + 0.02), P(rx + 0.05, 1.20, zf + 0.02), P(rx + 0.05, 1.24, zf + 0.02), P(rx - 0.05, 1.24, zf + 0.02)], D(0, 0, 1))
    # the wall cabinet, the shelf under it with the conductivity meter and the chlorine test kit, the log on its hook
    x0, x1, y0, y1 = CABINET
    cx = (x0 + x1) / 2
    wall_box(cb, 'N', cx, x1 - x0, y0, y1, 0.32)
    for s in (-1, 1):
        cb.box(cx + s * (x1 - x0) / 4, (y0 + y1) / 2, RZN + 0.32 + 0.009, (x1 - x0) / 2 - 0.02, y1 - y0 - 0.03, 0.018, faces='xXyYZ')
        bar(st, (cx + s * 0.04, (y0 + y1) / 2 - 0.08, RZN + 0.36), (cx + s * 0.04, (y0 + y1) / 2 + 0.08, RZN + 0.36), 0.012)
    wall_box(builder('trn_desk_tops', 'trn_oak', tile=0.9), 'N', cx, x1 - x0, SHELF_Y - 0.03, SHELF_Y, 0.32)
    for s in (-1, 1):
        bar(gy, (cx + s * 0.45, SHELF_Y - 0.03, RZN + 0.30), (cx + s * 0.45, SHELF_Y - 0.28, RZN + 0.02), 0.025)
    mx = x0 + 0.22
    gy.box(mx, SHELF_Y + 0.07, RZN + 0.18, 0.12, 0.14, 0.16)
    led.face([P(mx - 0.04, SHELF_Y + 0.08, RZN + 0.264), P(mx + 0.04, SHELF_Y + 0.08, RZN + 0.264), P(mx + 0.04, SHELF_Y + 0.12, RZN + 0.264), P(mx - 0.04, SHELF_Y + 0.12, RZN + 0.264)], D(0, 0, 1))
    tube(bk, [(mx + 0.06, SHELF_Y + 0.06, RZN + 0.18), (mx + 0.16, SHELF_Y + 0.02, RZN + 0.12), (mx + 0.24, SHELF_Y + 0.08, RZN + 0.12)], 0.003, n=6)
    lathe(gl, mx + 0.24, RZN + 0.12, [(SHELF_Y, 0.03), (SHELF_Y + 0.08, 0.032)], n=12, cap_top=False, cap_bot=True)
    kx = x1 - 0.28
    pp.box(kx, SHELF_Y + 0.045, RZN + 0.17, 0.24, 0.09, 0.16)
    bl.box(kx, SHELF_Y + 0.045, RZN + 0.17 + 0.0835, 0.20, 0.03, 0.001, faces='Z')
    for (dx, r) in ((-0.07, 0.016), (0.0, 0.016), (0.07, 0.016)):
        lathe(wh, kx + dx, RZN + 0.30, [(SHELF_Y + 0.09, r), (SHELF_Y + 0.15, r), (SHELF_Y + 0.165, r * 0.6), (SHELF_Y + 0.18, r * 0.6)], n=10)
    hx = x1 + 0.12
    bar(st, (hx, 1.10, RZN), (hx, 1.10, RZN + 0.03), 0.008); bar(st, (hx, 1.10, RZN + 0.03), (hx, 1.13, RZN + 0.03), 0.008)
    wall_box(gy, 'N', hx, 0.23, 0.76, 1.08, 0.012, off=0.01, faces='xXyYZ')
    plate(builder('trn_sheet', 'trn_sheet'), 'N', hx, 0.21, 0.77, 1.05, 0.026)
    st.box(hx, 1.07, RZN + 0.027, 0.10, 0.03, 0.012)
    label(builder('trn_labels', 'trn_labels'), 'N', 24.8, 0.6, 2.3, 2.45, 3)


# ---------------------------------------------------------------- dx-charting: the desk
def charting_desk():
    cx, cz = DESK
    w, dd, top = 1.40, 0.70, 0.74
    tp = builder('trn_desk_tops', 'trn_oak', tile=0.9); st = builder('trn_grey', 'trn_grey'); bk = builder('trn_black', 'trn_black', smooth_deg=50)
    tp.box(cx, top - 0.015, cz, w, 0.03, dd)
    for dx in (-w / 2 + 0.04, w / 2 - 0.04):
        for dz in (-dd / 2 + 0.04, dd / 2 - 0.04):
            st.box(cx + dx, (top - 0.03) / 2, cz + dz, 0.04, top - 0.03, 0.04)
    st.box(cx, 0.45, cz + dd / 2 - 0.06, w - 0.16, 0.40, 0.015)
    # a monitor on a stand at the back, the keyboard and mouse, a tray of notes
    mx, mz = cx + 0.05, cz + 0.20
    lathe(bk, mx, mz, [(top, 0.11), (top + 0.015, 0.11), (top + 0.02, 0.03)], n=14)
    bar(bk, (mx, top, mz), (mx, top + 0.26, mz), 0.04, 0.03)
    sw, sh = 0.53, 0.31
    bk.box(mx, top + 0.26, mz + 0.01, sw + 0.02, sh + 0.02, 0.025)
    sc = builder('trn_record', 'trn_record_e')
    face_uv(sc, [P(mx + sw / 2, top + 0.26 - sh / 2, mz - 0.0065), P(mx - sw / 2, top + 0.26 - sh / 2, mz - 0.0065), P(mx - sw / 2, top + 0.26 + sh / 2, mz - 0.0065), P(mx + sw / 2, top + 0.26 + sh / 2, mz - 0.0065)], D(0, 0, -1), UV01)
    bk.box(mx - 0.05, top + 0.008, cz - 0.12, 0.44, 0.016, 0.15)
    lathe(bk, mx + 0.30, cz - 0.12, [(top, 0.0), (top, 0.03), (top + 0.025, 0.028), (top + 0.035, 0.0)], n=10, cap_top=True)
    pp = builder('trn_paper', 'trn_paper')
    pp.box(cx - 0.48, top + 0.01, cz + 0.12, 0.22, 0.02, 0.30)
    # the task chair, the filing cabinet in the corner, the corkboard on the wall above the desk
    task_chair(cx, cz - 0.75, 'seat__training_desk_f%d' % seat_yaw(0.0, 1.0), (0.0, 1.0))
    fx, fz = FILING
    st.box(fx, 0.65, fz, 0.45, 1.30, 0.60)
    for k in range(4):
        y = 0.20 + k * 0.30
        st.box(fx, y, fz - 0.305, 0.41, 0.26, 0.01, faces='xXyYz')
        bar(builder('trn_steel', 'trn_steel', smooth_deg=50), (fx - 0.06, y + 0.06, fz - 0.33), (fx + 0.06, y + 0.06, fz - 0.33), 0.012)
    plate(builder('trn_cork', 'trn_cork'), 'S', cx + 0.05, 1.2, 1.45, 2.15, 0.018)
    fr = builder('trn_desk_tops', 'trn_oak', tile=0.9)
    for (c, w_, y0, y1) in ((cx + 0.05, 1.26, 1.42, 1.45), (cx + 0.05, 1.26, 2.15, 2.18), (cx + 0.05 - 0.615, 0.03, 1.45, 2.15), (cx + 0.05 + 0.615, 0.03, 1.45, 2.15)):
        wall_box(fr, 'S', c, w_, y0, y1, 0.025)
    label(builder('trn_labels', 'trn_labels'), 'S', cx + 0.05, 0.6, 2.3, 2.45, 4)


# ---------------------------------------------------------------- the course desk and the spot
def course_desk():
    cx, cz = COURSE_DESK
    wd = builder('trn_desk_body', 'trn_oak', tile=0.9); cb = builder('trn_cabinets', 'trn_cabinet'); bk = builder('trn_black', 'trn_black')
    # an oak pedestal with a white top at lectern height, a shelf inside, a lip at the back edge
    wd.box(cx, 0.50, cz, 0.42, 1.00, 0.70, faces='xXzZ')
    wd.box(cx, 0.60, cz, 0.38, 0.025, 0.66, faces='Y')
    cb.box(cx, 1.015, cz, 0.52, 0.03, 0.90)
    wd.box(cx - 0.25, 1.05, cz, 0.02, 0.04, 0.90)
    # a tablet on a stand, lit, and the desk card
    tilt = math.radians(28)
    n = (-math.sin(tilt), math.cos(tilt), 0.0); up = (math.cos(tilt), math.sin(tilt), 0.0)
    c = (cx - 0.02, 1.03 + 0.10, cz)
    def corner(u, v, w_): return (c[0] + n[0] * w_ + up[0] * v, c[1] + n[1] * w_ + up[1] * v, c[2] + u)
    hexa(bk, [corner(-0.14, -0.10, -0.01), corner(0.14, -0.10, -0.01), corner(0.14, 0.10, -0.01), corner(-0.14, 0.10, -0.01),
              corner(-0.14, -0.10, 0.0), corner(0.14, -0.10, 0.0), corner(0.14, 0.10, 0.0), corner(-0.14, 0.10, 0.0)])
    tb = builder('trn_tablet', 'trn_tablet_e')
    tb.face([P(*corner(-0.13, -0.09, 0.004)), P(*corner(0.13, -0.09, 0.004)), P(*corner(0.13, 0.09, 0.004)), P(*corner(-0.13, 0.09, 0.004))], D(*n))
    bar(bk, (cx - 0.05, 1.03, cz), (cx - 0.08, 1.11, cz), 0.03, 0.01)
    lb = builder('trn_labels', 'trn_labels')
    v0, v1 = 0.0, 1 / 6
    x_ = cx + 0.24                                   # a card at the front edge, leaning back; seen from the east its left is +z
    face_uv(lb, [P(x_, 1.03, cz + 0.12), P(x_, 1.03, cz - 0.12), P(x_ - 0.02, 1.09, cz - 0.12), P(x_ - 0.02, 1.09, cz + 0.12)], D(0.95, 0.3, 0), [(0, v0), (1, v0), (1, v1), (0, v1)])


def spot():
    sp = builder('spot__training_f%d' % seat_yaw(1.0, 0.0), 'trn_mark')
    x, z = SPOT
    sp.face([P(x - 0.15, 0.01, z - 0.15), P(x + 0.15, 0.01, z - 0.15), P(x + 0.15, 0.01, z + 0.15), P(x - 0.15, 0.01, z + 0.15)], D(0, 1, 0))


# ---------------------------------------------------------------- output
def web_yaw(frm, to):
    """The web camera yaw (radians; 0 looks toward -z, -pi/2 toward +x) from a point to another, in plan."""
    dx, dz = to[0] - frm[0], to[1] - frm[1]
    return math.atan2(-dx, -dz)


def write_json(seats):
    with open(os.path.join(PIPE, 'lights.json'), 'w') as f:
        json.dump({'source': 'bl/training.py', 'units': 'metres, three.js campus axes (y up)',
                   'lights': [{'name': k, 'type': 'AREA' if size else 'POINT', 'campus_pos_m': [round(v, 3) for v in pos], 'campus_dir': [0, -1, 0],
                               'blender_watts': w, 'color_linear': [round(c, 3) for c in col], 'radius_m': 0.06,
                               'area_size_m': list(size) if size else None} for (k, pos, col, w, size) in LIGHTS]}, f, indent=1)
    EYE = 1.62
    def ue_yaw(yaw):
        d = (-90.0 - math.degrees(yaw)) % 360.0
        return round(d - 360.0 if d > 180.0 else d, 3)
    def view(frm, to, pitch):
        """Where a visitor stands and looks, in both conventions (as layout/layout.json's station views)."""
        yaw = web_yaw(frm, to)
        return {'three': {'x': round(frm[0], 3), 'z': round(frm[1], 3), 'eye_y': EYE, 'yaw_rad': round(yaw, 6), 'pitch_rad': pitch},
                'ue': {'location_cm': [round(frm[0] * 100, 1), round(frm[1] * 100, 1), round(EYE * 100, 1)],
                       'rotation_deg': {'pitch': round(math.degrees(pitch), 3), 'yaw': ue_yaw(yaw), 'roll': 0.0}}}
    def station(sid, anchor, frm, pitch):
        return {'id': sid, 'room': 'training', 'anchor_m': [round(v, 3) for v in anchor],
                'ue_location_cm': [round(anchor[0] * 100, 1), round(anchor[2] * 100, 1), round(anchor[1] * 100, 1)],
                'view': view(frm, (anchor[0], anchor[2]), pitch)}
    wd0, wd1, wdh = WEST_DOOR; yd0, yd1, ydh = YARD_DOOR
    layout = {
        'source': 'bl/training.py', 'units': 'campus metres (x east, y up, z south); Unreal = (x*100, z*100, y*100)',
        'venue': 'training',
        'rooms': [{'id': 'training', 'label': 'The Training Wing', 'x0': RX0, 'x1': RX1, 'z0': RZN, 'z1': RZS, 'floor_y': 0.0, 'ceiling_y': RH}],
        'entries': [{'what': "the door from the auditorium's cross-aisle, through its east wall", 'x': round((AUD_X + RX0) / 2, 3), 'y': 0.0,
                     'z': round((wd0 + wd1) / 2, 3), 'width': round(wd1 - wd0, 3), 'height': wdh},
                    {'what': 'the double doorway to the yard, in the east wall', 'x': round(RX1 + WALL_T / 2, 3), 'y': 0.0,
                     'z': round((yd0 + yd1) / 2, 3), 'width': round(yd1 - yd0, 3), 'height': ydh}],
        'windows': [{'wall': 'E', 'x': RX1, 'z0': z0, 'z1': z1, 'y0': WIN_Y0, 'y1': WIN_Y1} for (z0, z1) in EAST_WINDOWS] +
                   [{'wall': 'N', 'z': RZN, 'x0': x0, 'x1': x1, 'y0': WIN_Y0, 'y1': WIN_Y1} for (x0, x1) in NORTH_WINDOWS],
        'stations': [
            station('dx-hygiene', (SINK[0] - 0.1, 0.9, SINK[1]), (SINK[0] - 0.1, -15.3), -0.25),
            station('dx-machine', (MACHINE[0], 1.4, MACHINE[1]), (29.4, MACHINE[1]), -0.05),
            station('dx-chair', (TCHAIR[0], 0.6, TCHAIR[1]), (28.7, -19.9), -0.2),
            station('dx-water', (24.6, 1.2, RZN + 0.5), (24.6, -24.7), -0.05),
            station('dx-charting', (DESK[0], 0.9, DESK[1]), (DESK[0], -15.9), -0.2),
        ],
        'course_desk': {'anchor_m': [COURSE_DESK[0], 1.05, COURSE_DESK[1]], 'faces': [1, 0, 0],
                        'ue_location_cm': [round(COURSE_DESK[0] * 100, 1), round(COURSE_DESK[1] * 100, 1), 105.0],
                        'spot': {'x': SPOT[0], 'y': 0.0, 'z': SPOT[1], 'yaw': seat_yaw(1.0, 0.0), 'mesh': 'spot__training_f%d' % seat_yaw(1.0, 0.0)},
                        'board': {'wall': 'W', 'x': RX0, 'z': BOARD[0], 'width': BOARD[1], 'height': BOARD[2], 'y0': BOARD[3]},
                        'view': view((SPOT[0] + 1.7, COURSE_DESK[1]), (RX0, BOARD[0]), -0.05)},
        'speaker_spot': {'x': SPOT[0], 'y': 0.0, 'z': SPOT[1], 'yaw': seat_yaw(1.0, 0.0)},
        'place_view': view((28.0, -16.0), (24.6, RZN), -0.05),
        'camera': {'eye': [31.4, 1.55, -25.5], 'target': [24.5, 1.1, -18.0]},
        'seats': len(seats), 'seat_names': seats,
    }
    with open(os.path.join(PIPE, 'layout.json'), 'w') as f:
        json.dump(layout, f, indent=1)


def export_glb():
    for m in (MATS['trn_glass'], MATS['trn_bag']):
        m.surface_render_method = 'BLENDED'
    obs = [o for o in bpy.data.objects if o.type == 'MESH' and not o.get('preview_only')]
    select_only(obs)
    fp = os.path.join(PIPE, 'Training.glb')
    bpy.ops.export_scene.gltf(filepath=fp, export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
                              export_texcoords=True, export_normals=True, export_tangents=True, export_materials='EXPORT',
                              export_image_format='AUTO', export_vertex_color='NONE', export_lights=False, export_cameras=False)
    print('exported', fp, os.path.getsize(fp), 'bytes', flush=True)


def preview_scene():
    """The prepared grounds, auditorium and yard around the room (when out/ue has them), the room's own fixtures as
    lights, and the sun through the windows, for the previews only."""
    ue = os.path.join(SP, 'unreal', 'Pipeline', 'out', 'ue')
    for name in ('Outside', 'Auditorium', 'Yard'):
        fp = os.path.join(ue, name + '.glb')
        if not os.path.exists(fp) or '--bare' in sys.argv: continue
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=fp)
        for o in bpy.data.objects:
            if o not in before: o['preview_only'] = 1
    for (kind, (x, y, z), col, watts, size) in LIGHTS + PREVIEW_LIGHTS:
        if size:
            ld = bpy.data.lights.new(kind, 'AREA'); ld.shape = 'RECTANGLE'; ld.size, ld.size_y = size
        else:
            ld = bpy.data.lights.new(kind, 'POINT'); ld.shadow_soft_size = 0.1
        ld.energy = watts * 1.3; ld.color = col
        ob = bpy.data.objects.new(kind, ld); ob.location = P(x, y, z); ob['preview_only'] = 1
        bpy.context.scene.collection.objects.link(ob)
    sd = bpy.data.lights.new('Sun', 'SUN'); sd.energy = 4.0; sd.angle = math.radians(1.5); sd.color = (1.0, 0.95, 0.88)
    sun = bpy.data.objects.new('Sun', sd); sun['preview_only'] = 1; bpy.context.scene.collection.objects.link(sun)
    sun.rotation_euler = Vector((-0.5, -0.35, -0.8)).normalized().to_track_quat('-Z', 'Y').to_euler()
    w = bpy.data.worlds.new('World'); bpy.context.scene.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes['Background']
    sky = nt.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'MULTIPLE_SCATTERING'; sky.sun_disc = False; sky.sun_elevation = math.radians(48); sky.sun_rotation = math.radians(200)
    nt.links.new(sky.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.35


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
    room()
    seats = chairs()
    sink_unit()
    dialysis_machine()
    treatment_chair()
    bp_monitor()
    floor_scale()
    water_panel()
    charting_desk()
    seats.append('seat__training_desk_f%d' % seat_yaw(0.0, 1.0))
    course_desk()
    spot()
    for name, b in B.items():
        if b.count == 0: continue
        b.finish()
    write_json(seats)
    obs = [o for o in sc.objects if o.type == 'MESH']
    print('objects', len(obs), 'seats', len(seats), 'lights', len(LIGHTS), 'tris ~', sum(len(o.data.polygons) * 2 for o in obs),
          'built in %.0f s' % (time.time() - t0), flush=True)
    export_glb()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'training.blend'))
    if RENDER:
        preview_scene()
        for o in bpy.data.objects:                       # the spot is never shown, as in the engine
            if o.name.startswith('spot__'): o.hide_render = True
        views = {'room': ((31.4, 1.55, -25.5), (24.5, 1.1, -18.0), 82),
                 'chair': ((28.2, 1.45, -20.6), (30.8, 0.9, -18.0), 70),
                 'desk': ((25.2, 1.5, -19.2), (21.3, 1.5, -20.6), 66),
                 'water': ((25.6, 1.6, -23.2), (24.9, 1.1, -26.9), 72),
                 'sink': ((23.8, 1.5, -16.0), (23.3, 1.0, -13.7), 62),
                 'charting': ((28.6, 1.55, -16.3), (30.5, 1.0, -13.9), 66),
                 'yard': ((34.3, 1.6, -25.3), (31.4, 1.8, -26.3), 78),
                 'aisle': ((19.6, 1.55, -17.9), (21.6, 1.3, -15.3), 70)}
        want = [a.split('=')[1].split(',') for a in sys.argv if a.startswith('--views=')]
        for name in (want[0] if want else views):
            eye, target, fov = views[name]
            render(name, eye, target, fov=fov)
    print('done in %.0f s' % (time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
