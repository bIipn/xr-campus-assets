"""Room 104 becomes the XR Classroom: what the class sits at and looks at, in Blender (bpy) at campus coordinates,
for Unreal.

The room itself (walls, floor, ceiling, the 'How a world gets built' mural, the free-tools shelf, the token and the
window) stays the web School's; unreal/Pipeline/content/refits.json takes out the computers desk, its stools and
the 'Built in a browser' panel and moves the layer table, the beanbags and the World Builder book (prepare_for_
unreal.py applies it). This script builds what is new:

  * a wall-mounted smartboard on the east wall (x 34): screen__classroom, a 16:9 quad the engine plays the slides
    on, in a slim aluminium frame with a pen tray;
  * the teacher's desk at the front-right, by the window (the book lands on it), and the teacher's chair;
  * three rows of three two-seat student desks facing the board, each chair's seat a tagged mesh
    seat__classroom_r<row>d<desk><a|b>_f0 (the class faces +x: Unreal yaw 0);
  * spot__classroom_f180: where the teacher stands, at the front-left beside the board, facing the class;
  * the door sign on the hall side: '104 · XR Classroom', in the School's own sign style.

Campus axes: x east, y up, z south.  Blender: X = x, Y = -z, Z = y.
Usage (Blender 5.2 or bpy 5.2.2):   python bl/classroom.py [--render]
Writes assets/classroom/classroom.blend, unreal/Pipeline/out/classroom/Classroom.glb, lights.json and layout.json,
and preview renders (with the School around it). Then prepare_for_unreal.py -- School Classroom.
"""
import json
import math
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import library as L                                              # noqa: E402
from library import P, D, Builder, bar, material, MATS, select_only, seat_yaw   # noqa: E402
from neo import face_uv                                         # noqa: E402

SP = L.SP
OUT = os.path.join(SP, 'assets', 'classroom')
PIPE = os.path.join(SP, 'unreal', 'Pipeline', 'out', 'classroom')
TEX = os.path.join(SP, 'assets', 'tex')
RENDER = '--render' in sys.argv
QUICK = '--quick' in sys.argv
os.makedirs(OUT, exist_ok=True); os.makedirs(PIPE, exist_ok=True)

# ---------------------------------------------------------------- the room (the web School's Room 104)
RX0, RX1, RZ0, RZ1, RH = 24.0, 34.0, -1.25, 7.0, 3.6
DOOR = (28.1, 29.9)                     # the hall door in the z = -1.25 wall
BOARD_W = 3.0; BOARD_H = BOARD_W * 9 / 16
BOARD_Z = 2.6; BOARD_Y0 = 1.02          # centre along the wall, bottom edge (the pen tray clears the wall's light line)
BOARD_X = RX1 - 0.049                   # the screen's face; the backing's face 4 mm behind it
DESK_X = (31.0, 29.6, 28.2)             # rows, front to back
DESK_Z = (0.4, 2.6, 4.8)
DESK_W, DESK_D, DESK_TOP = 1.30, 0.60, 0.76
CHAIR_DX = 0.55                         # chair centre behind the desk centre (toward -x)
TEACH_DESK = (32.87, 5.3)               # centre; front edge (toward the class) at x 32.52
TEACH_SPOT = (33.0, 0.3)


def setup_materials():
    material('cls_screen', color=(0.03, 0.035, 0.04, 1), roughness=0.25)
    material('cls_alu', color=(0.78, 0.79, 0.80, 1), roughness=0.32, metallic=1.0)
    material('cls_black', color=(0.012, 0.012, 0.014, 1), roughness=0.5)
    material('cls_oak', 'oak_col', 'oak_rgh', 'oak_nrm', roughness=0.4)
    material('cls_steel', color=(0.08, 0.085, 0.09, 1), roughness=0.42, metallic=0.35)       # powder-coated frames
    material('cls_shell', color=(0.20, 0.36, 0.40, 1), roughness=0.5)                        # moulded chair shells, teal
    material('cls_walnut', 'walnut_col', 'walnut_rgh', 'walnut_nrm', roughness=0.38, nrm_strength=0.6)
    material('cls_pen_r', color=(0.55, 0.06, 0.05, 1), roughness=0.4)
    material('cls_pen_b', color=(0.04, 0.10, 0.45, 1), roughness=0.4)
    material('cls_pen_g', color=(0.05, 0.30, 0.12, 1), roughness=0.4)
    material('cls_sign', 'sign_room104', roughness=0.6)
    material('cls_blade', 'blade_room104', roughness=0.6)
    material('cls_mark', color=(0.2, 0.2, 0.2, 1), roughness=0.9)
    # the screen's placeholder: the engine puts the slides on it
    m = material('screen_classroom', color=(0.04, 0.04, 0.045, 1), roughness=0.3)


B = {}
def builder(name, mat, tile=1.0, smooth_deg=None):
    if name not in B: B[name] = Builder(name, mat, tile=tile, lightmap=False, vcol=False, smooth=smooth_deg)
    return B[name]


LIGHTS = []


# ---------------------------------------------------------------- the door sign texture
def make_sign():
    """The School's door-sign style (navy plate, gold mono kicker, white name, the big room number), 700 x 300."""
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1400, 600
    im = Image.new('RGB', (W, H), (31, 58, 82))
    d = ImageDraw.Draw(im)
    def font(paths, size):
        for p in paths:
            if os.path.exists(p): return ImageFont.truetype(p, size)
        return ImageFont.load_default()
    mono = font(['/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'], 40)
    bold = font(['/usr/share/fonts/opentype/inter/Inter-Bold.otf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'], 74)
    big = font(['/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf', '/usr/share/fonts/opentype/inter/Inter-Bold.otf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'], 190)
    d.text((80, 70), 'CLASS IN SESSION · TAKE A SEAT', font=mono, fill=(236, 186, 74))
    d.text((80, 160), 'XR Classroom', font=bold, fill=(255, 255, 255))
    d.text((74, 290), '104', font=big, fill=(255, 255, 255))
    im = im.resize((700, 300), Image.LANCZOS)
    im.save(os.path.join(TEX, 'sign_room104.png'), optimize=True)
    # the hall's blade sign, sticking out from the wall beside the door: the School's blade style (slate, a lilac
    # stripe on the wall side, grey kicker, white name, lilac number), 900 x 330
    W, H = 1800, 660
    im = Image.new('RGB', (W, H), (26, 35, 42))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 50, H), fill=(196, 140, 255))
    kick = font(['/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'], 44)
    name = font(['/usr/share/fonts/opentype/inter/Inter-Bold.otf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'], 118)
    num = font(['/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf', '/usr/share/fonts/opentype/inter/Inter-Bold.otf'], 210)
    d.text((140, 40), 'CLASS \u00b7 QUIZ \u00b7 CERTIFICATE', font=kick, fill=(150, 160, 168))
    d.text((140, 120), 'XR Classroom', font=name, fill=(255, 255, 255))
    d.text((134, 320), '104', font=num, fill=(196, 140, 255))
    im.resize((900, 330), Image.LANCZOS).save(os.path.join(TEX, 'blade_room104.png'), optimize=True)


# ---------------------------------------------------------------- the smartboard
def smartboard():
    x = BOARD_X; z0, z1 = BOARD_Z - BOARD_W / 2, BOARD_Z + BOARD_W / 2; y0, y1 = BOARD_Y0, BOARD_Y0 + BOARD_H
    # the screen: seen from the class (looking +x) left is -z, so bottom-left is (y0, z0)
    sc = builder('screen__classroom', 'screen_classroom')
    face_uv(sc, [P(x, y0, z0), P(x, y0, z1), P(x, y1, z1), P(x, y1, z0)], D(-1, 0, 0), [(0, 0), (1, 0), (1, 1), (0, 1)])
    # a black backing panel 4 mm behind the screen, a little larger, held 1 cm off the wall
    bk = builder('cls_board_back', 'cls_black')
    bk.box(x + 0.004 + 0.018, (y0 + y1) / 2, BOARD_Z, 0.036, BOARD_H + 0.04, BOARD_W + 0.04, faces='xyYzZ')
    # the aluminium frame round the screen's edge, standing 12 mm proud of it
    al = builder('cls_board_frame', 'cls_alu')
    f = 0.035; xd = 0.05; xc = x + 0.004 + 0.036 / 2 - 0.006
    for (cy, cz, sy, sz) in (((y0 + y1) / 2, z0 - f / 2, BOARD_H + 2 * f, f), ((y0 + y1) / 2, z1 + f / 2, BOARD_H + 2 * f, f),
                             (y0 - f / 2, BOARD_Z, f, BOARD_W), (y1 + f / 2, BOARD_Z, f, BOARD_W)):
        al.box(xc, cy, cz, xd, sy, sz, faces='xyYzZ')
    # the pen tray under it, and three markers in it
    al.box(RX1 - 0.055, y0 - f - 0.02, BOARD_Z, 0.09, 0.012, 1.1, faces='xyYzZ')
    al.box(RX1 - 0.099, y0 - f - 0.005, BOARD_Z, 0.008, 0.03, 1.1, faces='xXyYzZ')
    for k, (mat, dz) in enumerate((('cls_pen_r', -0.30), ('cls_pen_b', -0.22), ('cls_pen_g', 0.36))):
        pb = builder('cls_pens_%d' % k, mat, smooth_deg=50)
        pz = BOARD_Z + dz
        # a marker lying along z: a thin bar with a cap
        bar(pb, (RX1 - 0.06, y0 - f - 0.002, pz - 0.065), (RX1 - 0.06, y0 - f - 0.002, pz + 0.065), 0.018)
    LIGHTS.append(('screen', (RX1 - 1.0, RH - 0.15, BOARD_Z), (1.0, 0.95, 0.88), 120, None))


# ---------------------------------------------------------------- desks and chairs
def student_desk(cx, cz):
    top = builder('cls_desk_tops', 'cls_oak', tile=0.9)
    st = builder('cls_steel', 'cls_steel')
    th = 0.025
    top.box(cx, DESK_TOP - th / 2, cz, DESK_D, th, DESK_W)
    # a sled frame: two C-shaped steel sides (legs + foot + top rail), a stretcher, a modesty panel toward the board
    for s in (-1, 1):
        zz = cz + s * (DESK_W / 2 - 0.06)
        for dx in (-DESK_D / 2 + 0.05, DESK_D / 2 - 0.05):
            st.box(cx + dx, (DESK_TOP - th) / 2, zz, 0.03, DESK_TOP - th, 0.03)
        st.box(cx, 0.015, zz, DESK_D - 0.04, 0.03, 0.04)                       # foot
        st.box(cx, DESK_TOP - th - 0.02, zz, DESK_D - 0.08, 0.04, 0.025)        # top rail
    st.box(cx + DESK_D / 2 - 0.05, DESK_TOP - th - 0.03, cz, 0.025, 0.04, DESK_W - 0.15)
    st.box(cx + DESK_D / 2 - 0.07, 0.48, cz, 0.012, 0.36, DESK_W - 0.2)         # modesty panel (perforated steel, flat here)
    st.box(cx - DESK_D / 2 + 0.12, 0.18, cz, 0.025, 0.025, DESK_W - 0.15)       # footrest stretcher


def chair(cx, cz, seat_name, yaw_face=0.0):
    """A school chair: a moulded shell seat (the tagged seat mesh is its seat pan), a curved backrest and a
    four-leg steel frame. Facing +x when yaw_face = 0 (the back toward -x)."""
    sh = builder(seat_name, 'cls_shell')
    back = builder('cls_chair_backs', 'cls_shell', smooth_deg=35)
    st = builder('cls_steel', 'cls_steel')
    cr, sr = math.cos(yaw_face), math.sin(yaw_face)
    def W(u, v):  # chair-local (u forward, v right) -> campus x, z
        return (cx + u * cr - v * sr, cz + u * sr + v * cr)
    sy = 0.43
    # seat pan: 0.42 deep, 0.44 wide, 3 cm thick; its top (y 0.46) is the sitting surface
    sh.box(cx, sy + 0.015, cz, 0.42, 0.03, 0.44, ry=-yaw_face)
    # the backrest: a curved shell (an arc in plan) from the back of the seat up to 0.84
    n = 8; R = 0.55; half = 0.21
    for i in range(n):
        a0 = -half / R + (2 * half / R) * i / n; a1 = -half / R + (2 * half / R) * (i + 1) / n
        pts = []
        for (a, y) in ((a0, 0.52), (a1, 0.52), (a1, 0.84), (a0, 0.84)):
            lean = (y - 0.52) * 0.18                       # leans back a little
            u = -0.21 - lean - (R - R * math.cos(a)) * 0.6
            v = R * math.sin(a)
            x_, z_ = W(u, v)
            pts.append(P(x_, y, z_))
        nm = D(math.cos(yaw_face), 0.0, math.sin(yaw_face))
        back.face(pts, nm)
        back.face(list(reversed([p + D(-math.cos(yaw_face), 0, -math.sin(yaw_face)) * 0.012 for p in pts])), -nm)
    # steel: four legs, a ring under the seat, two uprights to the backrest
    for (u, v) in ((0.17, -0.18), (0.17, 0.18), (-0.17, -0.18), (-0.19, 0.18)):
        x_, z_ = W(u, v)
        st.box(x_, sy / 2, z_, 0.022, sy, 0.022, ry=-yaw_face)
    for (u0, v0, u1, v1) in ((0.17, -0.18, 0.17, 0.18), (-0.17, -0.18, -0.17, 0.18), (0.17, -0.18, -0.17, -0.18), (0.17, 0.18, -0.17, 0.18)):
        a = W(u0, v0); c = W(u1, v1)
        bar(st, (a[0], sy - 0.012, a[1]), (c[0], sy - 0.012, c[1]), 0.02)
    for v in (-0.15, 0.15):
        a = W(-0.19, v); c = W(-0.24, v)
        bar(st, (a[0], sy - 0.012, a[1]), (c[0], 0.60, c[1]), 0.02)


def desks():
    count = 0
    for r, dx in enumerate(DESK_X):
        for d, dz in enumerate(DESK_Z):
            student_desk(dx, dz)
            for k, s in enumerate((-1, 1)):
                name = 'seat__classroom_r%dd%d%s_f%d' % (r + 1, d + 1, 'ab'[k], seat_yaw(1.0, 0.0))
                chair(dx - CHAIR_DX, dz + s * 0.32, name)
                count += 1
    return count


def teacher_desk():
    cx, cz = TEACH_DESK
    w, dd, top = 1.40, 0.70, 0.765
    tb = builder('cls_teacher_top', 'cls_walnut', tile=1.2)
    tb.box(cx, top - 0.015, cz, dd, 0.03, w)
    wd = builder('cls_teacher_body', 'cls_walnut', tile=1.2)
    # a pedestal of drawers on the right (+z), a panel leg on the left, a modesty panel at the front (toward -x)
    wd.box(cx + 0.02, (top - 0.03) / 2, cz + w / 2 - 0.22, dd - 0.06, top - 0.03, 0.42, faces='xXyYzZ')
    wd.box(cx + 0.02, (top - 0.03) / 2, cz - w / 2 + 0.03, dd - 0.06, top - 0.03, 0.04)
    wd.box(cx - dd / 2 + 0.035, 0.42, cz - 0.10, 0.02, 0.62, w - 0.48)
    al = builder('cls_board_frame', 'cls_alu')
    for k in range(3):                       # drawer pulls on the teacher's side (+x)
        al.box(cx + dd / 2 - 0.02, 0.62 - k * 0.22, cz + w / 2 - 0.22, 0.02, 0.015, 0.16)
    # the teacher's chair behind the desk, turned to face the class (-x)
    chair(cx + 0.62, cz - 0.25, 'cls_teacher_chair', yaw_face=math.pi)


def spot():
    sp = builder('spot__classroom_f%d' % seat_yaw(-1.0, 0.0), 'cls_mark')
    x, z = TEACH_SPOT
    sp.face([P(x - 0.15, 0.01, z - 0.15), P(x + 0.15, 0.01, z - 0.15), P(x + 0.15, 0.01, z + 0.15), P(x - 0.15, 0.01, z + 0.15)], D(0, 1, 0))


def door_sign():
    """On the hall side of the z = -1.25 wall, over the door, where the web's own sign was (refits drops it)."""
    sg = builder('cls_door_sign', 'cls_sign')
    x0, x1, y0, y1, z = 28.25, 29.75, 2.72, 3.36, RZ0 - 0.012
    # seen from the hall (looking +z) left is +x, so the image's bottom-left corner is at (x1, y0)
    face_uv(sg, [P(x1, y0, z), P(x0, y0, z), P(x0, y1, z), P(x1, y1, z)], D(0, 0, -1), [(0, 0), (1, 0), (1, 1), (0, 1)])
    al = builder('cls_board_frame', 'cls_alu')
    f = 0.02
    for (cx, cy, sx, sy) in (((x0 + x1) / 2, y0 - f / 2, x1 - x0 + 2 * f, f), ((x0 + x1) / 2, y1 + f / 2, x1 - x0 + 2 * f, f),
                             (x0 - f / 2, (y0 + y1) / 2, f, y1 - y0), (x1 + f / 2, (y0 + y1) / 2, f, y1 - y0)):
        al.box(cx, cy, z - 0.004, sx, sy, 0.024, faces='xXyYz')


def blade_sign():
    """New faces for the hall's blade sign (the web's board and bracket stay; refits drops its two old faces): a
    0.8 x 0.294 m board standing out from the wall at x 27.75, its faces 2 mm proud of the board's sides."""
    bl = builder('cls_blade_sign', 'cls_blade')
    za, zb, y0, y1 = -1.35, -2.15, 2.853, 3.147      # za at the wall
    for (x, nx) in ((27.767, 1), (27.733, -1)):
        # seen from +x (looking west) the viewer's left is the wall side (+z); from -x it is the far end (-z)
        left, right = (za, zb) if nx > 0 else (zb, za)
        face_uv(bl, [P(x, y0, left), P(x, y0, right), P(x, y1, right), P(x, y1, left)], D(nx, 0, 0), [(0, 0), (1, 0), (1, 1), (0, 1)])


def lights():
    # two ceiling panels over the desks (the web's one ceiling panel and lamp stay)
    for z in (1.5, 3.7):
        LIGHTS.append(('panel', (29.6, RH - 0.20, z), (1.0, 0.97, 0.92), 160, (1.2, 0.6)))


def write_json(seats):
    with open(os.path.join(PIPE, 'lights.json'), 'w') as f:
        json.dump({'source': 'bl/classroom.py', 'units': 'metres, three.js campus axes (y up)',
                   'lights': [{'name': k, 'type': 'AREA' if size else 'POINT', 'campus_pos_m': [round(v, 3) for v in pos], 'campus_dir': [0, -1, 0],
                               'blender_watts': w, 'color_linear': [round(c, 3) for c in col], 'radius_m': 0.06,
                               'area_size_m': list(size) if size else None} for (k, pos, col, w, size) in LIGHTS]}, f, indent=1)
    layout = {
        'source': 'bl/classroom.py', 'units': 'campus metres (x east, y up, z south); Unreal = (x*100, z*100, y*100)',
        'venue': 'classroom',
        'rooms': [{'id': 'classroom', 'label': 'Room 104 · XR Classroom', 'x0': RX0, 'x1': RX1, 'z0': RZ0, 'z1': RZ1, 'floor_y': 0.0, 'ceiling_y': RH}],
        'entries': [{'what': 'the hall door', 'x': round((DOOR[0] + DOOR[1]) / 2, 3), 'y': 0.0, 'z': RZ0, 'width': round(DOOR[1] - DOOR[0], 3)}],
        'speaker_spot': {'x': TEACH_SPOT[0], 'y': 0.0, 'z': TEACH_SPOT[1], 'yaw': seat_yaw(-1.0, 0.0)},
        'screens': [{'name': 'screen__classroom', 'centre': [round(BOARD_X, 3), round(BOARD_Y0 + BOARD_H / 2, 3), BOARD_Z],
                     'size_m': [BOARD_W, round(BOARD_H, 4)], 'faces': [-1, 0, 0]}],
        'teacher_desk': {'x': TEACH_DESK[0], 'z': TEACH_DESK[1], 'top_y': 0.765},
        'camera': {'eye': [25.2, 1.55, 0.2], 'target': [34.0, 1.6, 3.2]},
        'seats': seats,
    }
    with open(os.path.join(PIPE, 'layout.json'), 'w') as f:
        json.dump(layout, f, indent=1)


def export_glb():
    obs = [o for o in bpy.data.objects if o.type == 'MESH' and not o.get('preview_only')]
    select_only(obs)
    fp = os.path.join(PIPE, 'Classroom.glb')
    bpy.ops.export_scene.gltf(filepath=fp, export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
                              export_texcoords=True, export_normals=True, export_tangents=True, export_materials='EXPORT',
                              export_image_format='AUTO', export_vertex_color='NONE', export_lights=False, export_cameras=False)
    print('exported', fp, os.path.getsize(fp), 'bytes', flush=True)


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


def preview_scene():
    """The prepared School (with the refit) around the new pieces, lit by the room's lamps, for the previews only."""
    fp = os.path.join(SP, 'unreal', 'Pipeline', 'out', 'ue', 'School.glb')
    if not os.path.exists(fp): return
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=fp)
    for o in bpy.data.objects:
        if o not in before: o['preview_only'] = 1
    # the web room's own lamp and ceiling panel, plus ours
    for (kind, (x, y, z), col, watts, size) in LIGHTS + [('lamp', (29.0, 2.5, 0.9), (0.93, 0.95, 1.0), 300, None), ('lamp', (29.0, 2.5, 4.5), (1.0, 0.95, 0.9), 200, None)]:
        if size:
            ld = bpy.data.lights.new(kind, 'AREA'); ld.shape = 'RECTANGLE'; ld.size, ld.size_y = size
        else:
            ld = bpy.data.lights.new(kind, 'POINT'); ld.shadow_soft_size = 0.1
        ld.energy = watts * 2.0; ld.color = col
        ob = bpy.data.objects.new(kind, ld); ob.location = P(x, y, z); ob['preview_only'] = 1
        bpy.context.scene.collection.objects.link(ob)
    # a stand-in slide on the screen so the board reads in the preview
    m = MATS['screen_classroom']
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Emission Color'].default_value = (0.20, 0.33, 0.45, 1); bsdf.inputs['Emission Strength'].default_value = 1.5
    w = bpy.data.worlds.new('World'); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.3


def main():
    t0 = time.time()
    sc = L.reset()
    make_sign()
    setup_materials()
    smartboard()
    seats = desks()
    teacher_desk()
    spot()
    door_sign()
    blade_sign()
    lights()
    for name, b in B.items():
        if b.count == 0: continue
        ob = b.finish()
    write_json(seats)
    obs = [o for o in sc.objects if o.type == 'MESH']
    print('objects', len(obs), 'seats', seats, 'tris ~', sum(len(o.data.polygons) * 2 for o in obs), 'built in %.0f s' % (time.time() - t0), flush=True)
    export_glb()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'classroom.blend'))
    if RENDER:
        preview_scene()
        for o in bpy.data.objects:                       # the speaker's mark is never shown, as in the engine
            if o.name.startswith('spot__'): o.hide_render = True
        views = {'class': ((25.0, 1.55, 0.0), (34.0, 1.5, 3.2), 74), 'board': ((30.2, 1.25, 1.6), (34.0, 1.6, 2.6), 70),
                 'teacher': ((31.6, 1.3, 6.6), (33.0, 0.9, 4.6), 70), 'door': ((29.0, 1.6, -3.6), (29.0, 2.6, -1.25), 60)}
        want = [a.split('=')[1].split(',') for a in sys.argv if a.startswith('--views=')]
        for name in (want[0] if want else views):
            eye, target, fov = views[name]
            render(name, eye, target, fov=fov)
    print('done in %.0f s' % (time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
