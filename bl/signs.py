"""Signs to the Lost Stories cabin: wayfinding for the story booth at the end of the grounds' path, so a visitor knows
it is there and how to get to it (Ev, Oct 23: keep the cabin, add signs). Built in Blender (bpy) at campus
coordinates, for Unreal.

  the portico    a two-sided exhibition stand on the museum's portico, west of the doors, in view from the forecourt
                 where a visit starts: the cabin's name, what it is, a plan of the grounds with the way from the stand
                 to the cabin, and three steps. Its back, for visitors coming out of the doors, has the same plan
                 turned the way they face.
  the rotunda    a framed notice on a bronze easel just inside the front doors, facing the lobby arch: for a visitor
                 on the way out, through these doors and down the garden path.
  the foyer      a framed poster on the auditorium foyer's west wall, by the door from Hall R (the talks wing is where
                 a visitor looking for a recording room goes): the story booth is in the garden, and the way there.
  the fountain   a garden fingerpost where the path meets the fountain's plaza: the cabin one way, the museum and the
                 theatre the other.

Every plan is heads-up (the way the reader faces is up) and drawn from the builders' own plan constants
(bl/museum.py, bl/exterior.py, bl/auditorium.py, bl/stories.py), so it stays true when a building moves. The words
come from the client pack's language (lang/<lang>/builders.json); the cabin's name is the pack's stories.sign, the
same as the cabin's own sign.

Campus axes: x east, y up, z south.  Blender: X = x, Y = -z, Z = y.
Usage (Blender 5.2 or bpy 5.2.2):   python bl/signs.py [--render] [--quick] [--views=a,b] [--textures]
Writes unreal/Pipeline/out/signs/Signs.glb, the signs' textures in assets/tex/signs_*.png and preview renders in
assets/signs/ (--textures: the textures and a contact sheet only). Then prepare_for_unreal.py -- Signs.
"""
import math
import os
import sys
import time

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import library as L                                              # noqa: E402
from library import P, D, Builder, material, select_only        # noqa: E402
from neo import face_uv, lathe                                   # noqa: E402
import museum as M                                               # noqa: E402  (the museum's plan, ground_height)
import exterior as X                                             # noqa: E402  (the theatre, the path, the fountain, the trees)
import auditorium as A                                           # noqa: E402  (the foyer)
import stories as S                                              # noqa: E402  (the cabin's plan; the text helpers its signs use)

SP = L.SP
OUT = os.path.join(SP, 'assets', 'signs')
PIPE = os.path.join(SP, 'unreal', 'Pipeline', 'out', 'signs')
TEX = os.path.join(SP, 'assets', 'tex')
RENDER = '--render' in sys.argv
QUICK = '--quick' in sys.argv
os.makedirs(OUT, exist_ok=True); os.makedirs(PIPE, exist_ok=True)
gh = M.ground_height


def unit(v):
    n = math.hypot(v[0], v[1])
    return (v[0] / n, v[1] / n)


# ---------------------------------------------------------------- where the signs stand (campus metres)
# Each sign: its plan position and the way its face looks (a unit plan vector). The reader stands in front of it,
# looking the other way, and the plan on it is drawn with that way up.
STAND = (-2.9, 14.4)              # the portico, between the front columns west of the doors (x -4.35 and -1.45 at z 15.4)
STAND_F = (0.0, 1.0)              # faces the forecourt; the back faces the doors
STAND_W, STAND_H, STAND_Y0 = 0.80, 1.10, 0.78       # the panel, and its bottom edge above the portico floor
EASEL = (-2.3, 8.4)               # the rotunda, west of the doors' axis, between the torchere (-1.82, 9.47) and the urn (-3.24, 9.04)
EASEL_F = unit((0.0 - EASEL[0], M.RC[1] - M.RI - EASEL[1]))   # faces the lobby arch (z 0.8)
EASEL_W, EASEL_H, EASEL_Y0, EASEL_TILT = 0.70, 1.00, 0.86, math.radians(10.0)
POSTER = (A.FX0, -6.9)            # the foyer's west wall, opposite the east wall's first poster (bl/auditorium.py)
POSTER_F = (1.0, 0.0)
POSTER_W, POSTER_H, POSTER_YC = 0.9, 1.29, 1.95     # the foyer posters' size and height
FINGER = (2.5, 41.9)              # beside the path where it meets the fountain's plaza, on the path lamps' line
ARM_L, ARM_P, ARM_H, ARM_T = 1.05, 0.17, 0.205, 0.036   # a fingerpost arm: length (with the point), point, height, thickness


def reader(o, f, d=1.3):
    """Where someone reading a sign at o, facing f, stands: d in front of it."""
    return (o[0] + f[0] * d, o[1] + f[1] * d)


def path_x(z):
    """The garden path's centre line (bl/exterior.py build_path): straight to the fountain, then a curve to x -4."""
    if z < X.FOUNTAIN[1] + 8.0:
        return 0.0
    t = (z - X.FOUNTAIN[1] - 8.0) / 12.0
    return -4.0 * math.sin(min(t, 1.0) * math.pi / 2) if t < 1.0 else -4.0 + 2.5 * math.sin((z - X.FOUNTAIN[1] - 20.0) / 7.0)


def route_from(points):
    """The way to the cabin from points (campus (x, z), the reader first): out through the theatre's middle passage,
    the path to the fountain, round its east side, and the path's curve to the porch steps."""
    fx, fz = X.FOUNTAIN
    out = list(points) + [(0.0, X.TH_C[1] + X.TH_R0), (0.0, fz - 7.6)]
    for a in range(-80, 81, 20):                               # round the basin at 5 m, the east side
        r = math.radians(a)
        out.append((fx + 5.0 * math.cos(r), fz + 5.0 * math.sin(r)))
    z = fz + 7.6
    while z < X.PATH_Z1:
        out.append((path_x(z), z)); z += 1.0
    out.append((S.CX, S.ZP + 0.3))
    return out


# the routes on each sign's plan (the reader's place first)
ROUTES = {
    'stand_s': route_from([reader(STAND, STAND_F), (-1.2, 17.2), (0.0, 18.4)]),
    'stand_n': route_from([reader(STAND, (0.0, -1.0), 1.0), (-1.6, 15.2), (-0.6, 17.2), (0.0, 18.4)]),
    'easel': route_from([reader(EASEL, EASEL_F), (-0.6, 10.6), (0.0, 12.6), (0.0, 18.4)]),
    'poster': route_from([reader(POSTER, POSTER_F, 1.2), (9.0, -5.8), (9.0, -3.0), (6.0, -3.0), (0.0, -3.0),
                          (0.0, 12.6), (0.0, 18.4)]),
}
# the way each plan has up: the way its reader faces
UPS = {'stand_s': (0.0, -1.0), 'stand_n': (0.0, 1.0), 'easel': (0.0, 1.0), 'poster': (-1.0, 0.0)}


# ---------------------------------------------------------------- textures (PIL)
CREAM, FOREST, BRASS, INK = S.CREAM, S.FOREST, S.BRASS, S.INK
SOFT = (222, 212, 188)            # body text on the forest
GOLD = (214, 186, 124)            # the footnote
LAWN = (204, 213, 182); LAWN_DK = (198, 208, 175)
PAVE = (241, 234, 216); PAVE_EDGE = (190, 178, 152)
BLDG = (226, 215, 192); BLDG_EDGE = (112, 98, 76); BLDG_TEXT = (92, 80, 62)
TIER = (218, 208, 186); TIER_LINE = (196, 184, 160)
WATER = (150, 188, 198); RIM = (206, 198, 180)
TREE = (140, 162, 114); TREE_EDGE = (106, 128, 86)
ROUTE = (168, 46, 30)
SS = 2                            # everything is painted at twice the size and scaled down (smooth edges)


def words():
    """(tr, the cabin's name): the pack language's words and the pack's own name for the cabin."""
    import clientpack
    lw = S.language_words()
    tr = lambda text: lw.get(text, text)
    pack = clientpack.get('stories', {}) or {}
    return tr, pack.get('sign', tr('LOST STORIES'))


def copy_for(tr, name):
    """Every sign's words, in the pack's language."""
    foot = tr('Or open Places and choose Lost Stories.')
    return {
        'stand_s': dict(title=tr('Tell your own story'),
                        body=tr('In the timber cabin at the end of the garden path, sit at the microphone and tell a '
                                'story about this place. It is kept in your own voice.'),
                        steps=[tr('Turn round and go down the steps'), tr("Walk through the theatre's middle passage"),
                               tr('Follow the path past the fountain to its end')], foot=foot),
        'stand_n': dict(title=tr('Tell your own story'),
                        body=tr('In the timber cabin at the end of the garden path, sit at the microphone and tell a '
                                'story about this place. It is kept in your own voice.'),
                        steps=[tr('Down the steps, straight ahead'), tr("Through the theatre's middle passage"),
                               tr('Follow the path past the fountain to its end')], foot=foot),
        'easel': dict(title=tr('Tell your own story'),
                      body=tr('In the timber cabin at the end of the garden path, sit at the microphone and tell a '
                              'story about this place. It is kept in your own voice.'),
                      steps=[tr('Out through the front doors ahead'), tr('Down the steps and through the theatre'),
                             tr('Follow the path past the fountain to its end')], foot=foot),
        'poster': dict(title=tr('The story booth is in the garden'),
                       body=tr('Tell a story about this place at the microphone in the timber cabin at the end of the '
                               'garden path. It is kept in your own voice.'),
                       steps=[tr('Back through Hall R to the lobby'), tr('Through the rotunda and out the front doors'),
                              tr('Down the steps, through the theatre and along the path past the fountain')], foot=foot),
    }


def fnt(kind, size):
    names = {'cinzel': ['Cinzel.ttf'], 'italic': ['CormorantGaramond-MediumItalic.ttf'],
             'semi': ['CormorantGaramond-SemiBold.ttf'], 'bold': ['CormorantGaramond-Bold.ttf'],
             'sans': ['Inter-Bold.otf', 'DejaVuSans-Bold.ttf']}[kind]
    return S.font(names, int(size))


def wrap(d, text, f, maxw):
    lines, line = [], ''
    for w in text.split():
        test = (line + ' ' + w).strip()
        if line and d.textlength(test, font=f) > maxw:
            lines.append(line); line = w
        else:
            line = test
    if line:
        lines.append(line)
    return lines


class Plan:
    """A heads-up plan of the grounds in a pixel box: `up` (a campus plan direction) points up the page, `centre`
    (campus x, z) is the box's middle, `scale` pixels to the metre."""
    def __init__(self, w, h, centre, scale, up):
        self.w, self.h = w, h
        self.c = centre; self.s = scale
        self.F = unit(up); self.R = (-self.F[1], self.F[0])     # the reader's right, seen from above
    def px(self, x, z):
        dx, dz = x - self.c[0], z - self.c[1]
        return (self.w / 2 + (dx * self.R[0] + dz * self.R[1]) * self.s, self.h / 2 - (dx * self.F[0] + dz * self.F[1]) * self.s)
    def poly(self, pts):
        return [self.px(x, z) for (x, z) in pts]
    def inside(self, x, z, m=0):
        u, v = self.px(x, z)
        return m <= u <= self.w - m and m <= v <= self.h - m
    def screen_dir(self, dx, dz):
        """A campus plan direction as a unit direction on the page (x right, y down)."""
        a = dx * self.R[0] + dz * self.R[1]; b = -(dx * self.F[0] + dz * self.F[1])
        n = math.hypot(a, b) or 1.0
        return a / n, b / n


def rect(x0, x1, z0, z1):
    return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]


def circle_pts(cx, cz, r, n=48, a0=0.0, a1=2 * math.pi):
    return [(cx + r * math.cos(a0 + (a1 - a0) * k / n), cz + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def buildings():
    """The buildings' footprints (campus plan polygons) the plan shows, from the builders' constants."""
    sh = X.SHELLS
    out = [rect(M.X0 - 0.3, M.X1 + 0.3, M.ZW - 0.3, 0.0),                     # the lobby and the galleries
           circle_pts(M.RC[0], M.RC[1], M.RO, 64),                            # the rotunda
           rect(M.PRO[0], M.PRO[1], M.PRO[2], M.PRO[3]),                      # the pronaos
           rect(-8.2, 8.2, M.PRO[3], M.STY_Z1)]                               # the portico
    for k in ('library', 'hallL', 'hallR', 'school', 'foyer', 'auditorium', 'training', 'wax'):
        s = sh[k]
        out.append(rect(s['x0'], s['x1'], s['z0'], s['z1']))
    return out


def paint_plan(key, w, h, tr, name, k=SS):
    """The plan for sign `key` as an RGB image w x h (already at the supersampled size, k pixels to a panel pixel):
    fitted to the way from the reader to the cabin, the names at sizes read from a step or two away."""
    from PIL import Image, ImageDraw, ImageFilter
    up = UPS[key]
    zs = [p[1] for p in ROUTES[key]]
    z0, z1 = min(zs) - 7.0, max(max(zs), S.ZB) + 4.5
    if up[0] == 0.0:                                  # north or south up: the route runs down (or up) the page
        scale = h / (z1 - z0)
    else:                                             # west up (the foyer): the route runs across the page
        scale = w / (z1 - z0)
    pl = Plan(w, h, (0.0, (z0 + z1) / 2), scale, up)
    im = Image.new('RGB', (w, h), LAWN); d = ImageDraw.Draw(im)
    lw = max(2, int(2.5 * k))
    # mown stripes across the lawn, faint
    for q in range(-40, 120, 4):
        d.polygon(pl.poly(rect(-90, 90, q, q + 2)), fill=LAWN_DK)
    # paving: the plaza at the steps' foot, the orchestra, the passage, the path, the fountain's plaza, the steps
    cx, cz = X.TH_C
    paving = [rect(-9.6, 9.6, M.STY_Z1, cz),
              [(cx - X.TH_R0, cz)] + [(cx + X.TH_R0 * math.sin(a), cz + X.TH_R0 * math.cos(a))
                                      for a in [-math.pi / 2 + math.pi * q / 48 for q in range(49)]],
              rect(-X.TH_GAP, X.TH_GAP, cz, cz + X.TH_RO + 0.4)]
    zz = [z / 2.0 for z in range(int((X.FOUNTAIN[1] + 6.0) * 2), int(X.PATH_Z1 * 2) + 1)]
    paving.append([(path_x(z) - X.PATH_W / 2, z) for z in zz] + [(path_x(z) + X.PATH_W / 2, z) for z in reversed(zz)])
    paving.append(rect(-X.PATH_W / 2, X.PATH_W / 2, cz + X.TH_RO, X.FOUNTAIN[1] - 6.0))
    d.ellipse(_box(pl, X.FOUNTAIN, 7.2), fill=PAVE, outline=PAVE_EDGE, width=lw)
    for p in paving:                                  # after the plaza, so the path runs on into it unbroken
        d.polygon(pl.poly(p), fill=PAVE)
    # the cavea's two halves: tiers either side of the passage, a line at each row
    for side in (-1, 1):
        a_out = X.TH_A
        def arc(r, a0, a1, n=24):
            return [(cx + side * r * math.sin(a0 + (a1 - a0) * q / n), cz + r * math.cos(a0 + (a1 - a0) * q / n)) for q in range(n + 1)]
        d.polygon(pl.poly(arc(X.TH_R0, math.asin(X.TH_GAP / X.TH_R0), a_out) + list(reversed(arc(X.TH_RO, math.asin(X.TH_GAP / X.TH_RO), a_out)))),
                  fill=TIER, outline=PAVE_EDGE)
        for q in range(1, X.TH_N):
            r = X.TH_R0 + q * X.TH_D
            d.line(pl.poly(arc(r, math.asin(X.TH_GAP / r), a_out)), fill=TIER_LINE, width=max(1, lw // 2))
    # the stage: its outer step, a half disc with a straight back
    sr = X.STAGE_R + 0.55
    stage = [(cx - sr, X.STAGE_BACK)] + [(cx + sr * math.sin(a), cz + sr * math.cos(a)) for a in [-math.pi / 2 + math.pi * q / 40 for q in range(41)]] + [(cx + sr, X.STAGE_BACK)]
    d.polygon(pl.poly(stage), fill=RIM, outline=PAVE_EDGE)
    d.polygon(pl.poly(rect(-8.2, 8.2, M.STY_Z1, M.STY_Z1 + M.STEPS * M.TREAD)), fill=PAVE)
    # the buildings, one outline round them all
    mask = Image.new('L', (w, h), 0); md = ImageDraw.Draw(mask)
    for b in buildings():
        md.polygon(pl.poly(b), fill=255)
    inner = mask.filter(ImageFilter.MinFilter(int(1.6 * k) * 2 + 1))
    im.paste(BLDG_EDGE, (0, 0), mask); im.paste(BLDG, (0, 0), inner)
    for (x, z) in M.PORT_COL:                         # the portico's columns
        d.ellipse(_box(pl, (x, z), 0.42), fill=BLDG_EDGE)
    # the fountain
    d.ellipse(_box(pl, X.FOUNTAIN, 3.1), fill=RIM, outline=PAVE_EDGE, width=lw)
    d.ellipse(_box(pl, X.FOUNTAIN, 2.7), fill=WATER)
    d.ellipse(_box(pl, X.FOUNTAIN, 0.9), fill=RIM)
    # trees
    for (x, z) in X.PATH_TREES + X.CAMPUS_TREES:
        d.ellipse(_box(pl, (x, z), 2.3), fill=TREE, outline=TREE_EDGE, width=lw)
    # the cabin and its porch, picked out in brass
    d.polygon(pl.poly(rect(S.XW, S.XE, S.ZP, S.ZF)), fill=PAVE, outline=FOREST, width=lw)
    d.polygon(pl.poly(rect(S.XW, S.XE, S.ZF, S.ZB)), fill=BRASS, outline=FOREST, width=lw * 2)
    # the route: a dashed line from the reader to the porch, a dot at its end
    route = pl.poly(ROUTES[key])
    rw = int(7 * k)
    _dashed(d, route, 19 * k, 12 * k, ROUTE, rw)
    ex, ey = route[-1]
    d.ellipse((ex - rw, ey - rw, ex + rw, ey + rw), fill=ROUTE)
    # the words, placed most important first, each where it is clear of the ones already down: you are here, the
    # cabin's name, the buildings, then the north rose in a clear corner
    taken = []
    yx, yy = route[0]
    r = 13 * k
    you, fy = tr('YOU ARE HERE'), fnt('sans', 25 * k)
    tw, th = _size(d, you, fy)
    gapx, gapy = r * 1.6 + tw / 2 + 12 * k, r * 1.6 + th / 2 + 12 * k   # clear of the dot's ring, with room
    taken.append((yx - r * 1.6, yy - r * 1.6, yx + r * 1.6, yy + r * 1.6))
    away = _away(route)
    first = 1.0 if away[0] >= 0 else -1.0                 # beside the dot, on the side the route does not leave by
    cands = [(yx + first * gapx, yy), (yx - first * gapx, yy), (yx, yy - gapy), (yx, yy + gapy)]
    u, v = _place(you, fy, cands, taken, w, h, k, d)
    d.ellipse((yx - r * 1.5, yy - r * 1.5, yx + r * 1.5, yy + r * 1.5), fill=CREAM)
    d.ellipse((yx - r, yy - r, yx + r, yy + r), fill=ROUTE)
    d.text((u, v), you, font=fy, fill=INK, anchor='mm', stroke_width=int(4 * k), stroke_fill=CREAM)
    _label(d, pl, name, (S.XE + 0.5, (S.ZF + S.ZB) / 2), (1.0, 0.0), fnt('cinzel', 33 * k), FOREST, taken, k=k, heavy=True)
    lab = fnt('cinzel', 27 * k)
    museum = ((-3.4, -10.5), None) if UPS[key][0] != 0.0 else ((M.PRO[1] + 0.4, (M.PRO[2] + M.PRO[3]) / 2), (1.0, 0.0))
    for (text, at, push) in ((tr('MUSEUM'),) + museum,
                             (tr('THEATRE'), (X.TH_RO * math.sin(X.TH_A) + 0.6, cz + X.TH_RO * math.cos(X.TH_A)), (1.0, 0.0)),
                             (tr('FOUNTAIN'), (X.FOUNTAIN[0] - 7.6, X.FOUNTAIN[1]), (-1.0, 0.0)),
                             (tr('LIBRARY'), (-22.0, -3.0), None), (tr('SCHOOL'), (23.0, -3.0), None)):
        _label(d, pl, text, at, push, lab, BLDG_TEXT, taken, k=k)
    # north: a rose in whichever corner is clear (top right first, bottom right when north is down the page)
    rr = 30 * k
    dx, dy = pl.screen_dir(0.0, -1.0)
    m = rr + 34 * k
    corners = [(w - m, m), (w - m, h - m), (m, m), (m, h - m)]
    if dy > 0.5:
        corners = [corners[1], corners[0], corners[3], corners[2]]
    for (nx, ny) in corners:
        box = (nx - rr * 2.2, ny - rr * 2.2, nx + rr * 2.2, ny + rr * 2.2)
        if not any(_overlap(box, t) for t in taken):
            break
    else:
        nx, ny = corners[0]
    taken.append((nx - rr * 2.2, ny - rr * 2.2, nx + rr * 2.2, ny + rr * 2.2))
    d.ellipse((nx - rr, ny - rr, nx + rr, ny + rr), fill=CREAM, outline=BLDG_EDGE, width=lw)
    tip = (nx + dx * rr * 0.80, ny + dy * rr * 0.80); tail = (nx - dx * rr * 0.62, ny - dy * rr * 0.62)
    px_, py_ = -dy, dx
    d.polygon([tip, (tail[0] + px_ * rr * 0.38, tail[1] + py_ * rr * 0.38), (nx - dx * rr * 0.25, ny - dy * rr * 0.25),
               (tail[0] - px_ * rr * 0.38, tail[1] - py_ * rr * 0.38)], fill=FOREST)
    d.text((nx + dx * rr * 1.6, ny + dy * rr * 1.6), 'N', font=fnt('cinzel', 30 * k), fill=FOREST, anchor='mm',
           stroke_width=int(4 * k), stroke_fill=LAWN)
    return im


def _box(pl, at, r):
    u, v = pl.px(*at); k = r * pl.s
    return (u - k, v - k, u + k, v + k)


def _dashed(d, pts, dash, gap, fill, width):
    """A dashed polyline with round ends, the pattern carried on round the corners."""
    on, left = True, dash
    for (a, b) in zip(pts, pts[1:]):
        ax, ay = a; bx, by = b
        seg = math.hypot(bx - ax, by - ay); t = 0.0
        while seg > 1e-6 and t < seg:
            step = min(left, seg - t)
            if on:
                x0, y0 = ax + (bx - ax) * t / seg, ay + (by - ay) * t / seg
                x1, y1 = ax + (bx - ax) * (t + step) / seg, ay + (by - ay) * (t + step) / seg
                d.line((x0, y0, x1, y1), fill=fill, width=width)
                for (x, y) in ((x0, y0), (x1, y1)):
                    d.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2), fill=fill)
            t += step; left -= step
            if left <= 1e-6:
                on = not on; left = dash if on else gap


def _size(d, text, f):
    bb = d.textbbox((0, 0), text, font=f, anchor='mm')
    return bb[2] - bb[0], bb[3] - bb[1]


def _overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _away(route):
    """The page direction the route leaves its start by (the you-are-here words go the other way first)."""
    x0, y0 = route[0]
    for (x, y) in route[1:]:
        if math.hypot(x - x0, y - y0) > 1e-3:
            n = math.hypot(x - x0, y - y0)
            return (-(x - x0) / n, -(y - y0) / n)
    return (1.0, 0.0)


def _place(text, f, cands, taken, w, h, k, d):
    """The first of the candidate centres where the words sit on the page clear of `taken` (else the first), and
    takes that box."""
    tw, th = _size(d, text, f)
    pad = 6 * k
    pick = None
    for (u, v) in cands:
        u = min(max(u, tw / 2 + 8 * k), w - tw / 2 - 8 * k)
        v = min(max(v, th / 2 + 8 * k), h - th / 2 - 8 * k)
        box = (u - tw / 2 - pad, v - th / 2 - pad, u + tw / 2 + pad, v + th / 2 + pad)
        if pick is None:
            pick = (u, v, box)
        if not any(_overlap(box, t) for t in taken):
            pick = (u, v, box)
            break
    taken.append(pick[2])
    return pick[0], pick[1]


def _label(d, pl, text, at, push, f, fill, taken, k=SS, heavy=False):
    """A name on the plan on a cream halo: centred on `at`, or (push, a campus direction) set just beyond it that
    way, or failing that the other way or to either side; left off when its anchor is not on the page."""
    if not pl.inside(at[0], at[1], 0):
        return
    u, v = pl.px(*at)
    tw, th = _size(d, text, f)
    if push:
        sx, sy = pl.screen_dir(*push)
        ox, oy = sx * (tw / 2 + 8 * k), sy * (th / 2 + 8 * k)
        cands = [(u + ox, v + oy), (u - ox, v - oy), (u + oy * 0 + ox * 0, v + th + 10 * k), (u, v - th - 10 * k)]
    else:
        cands = [(u, v), (u, v + th + 10 * k), (u, v - th - 10 * k)]
    u, v = _place(text, f, cands, taken, pl.w, pl.h, k, d)
    d.text((u, v), text, font=f, fill=CREAM, anchor='mm', stroke_width=int((6 if heavy else 4) * k), stroke_fill=CREAM)
    d.text((u, v), text, font=f, fill=fill, anchor='mm', stroke_width=int(1 * k) if heavy else 0, stroke_fill=fill)


def paint_panel(key, wm, hm, tr, name, words_):
    """A sign's face: the cabin's name, a line and a few words on what it is, the plan in a cream card, three steps
    and a footnote, on forest with a brass rule. wm x hm metres; returns the image at the panel's own proportions
    (1200 px wide, at SS times)."""
    from PIL import Image, ImageDraw
    W = 1200 * SS; H = int(round(1200 * hm / wm)) * SS
    im = Image.new('RGB', (W, H), FOREST); d = ImageDraw.Draw(im)
    k = SS
    d.rectangle((30 * k, 30 * k, W - 30 * k, H - 30 * k), outline=BRASS, width=4 * k)
    d.rectangle((40 * k, 40 * k, W - 40 * k, H - 40 * k), outline=(52, 86, 66), width=1 * k)
    y = 86 * k
    S.centred_fit(d, y, name, lambda s: fnt('cinzel', s), 112 * k, CREAM, W, W - 180 * k, tracking=14 * k)
    y += 148 * k
    d.line((W / 2 - 170 * k, y, W / 2 + 170 * k, y), fill=BRASS, width=3 * k)
    d.ellipse((W / 2 - 8 * k, y - 8 * k, W / 2 + 8 * k, y + 8 * k), fill=BRASS)
    y += 22 * k
    S.centred_fit(d, y, words_['title'], lambda s: fnt('italic', s), 86 * k, CREAM, W, W - 200 * k)
    y += 118 * k
    fb = fnt('semi', 45 * k)
    for line in wrap(d, words_['body'], fb, W - 230 * k):
        d.text((W / 2, y), line, font=fb, fill=SOFT, anchor='ma'); y += 56 * k
    y += 26 * k
    # the steps, measured first so the plan takes what is left
    fs = fnt('semi', 47 * k); fnum = fnt('cinzel', 40 * k)
    steps = [wrap(d, s, fs, W - 330 * k) for s in words_['steps'][:3]]
    steps_h = sum(max(1, len(s)) * 56 * k + 26 * k for s in steps)
    foot_h = 96 * k
    map_top = y; map_bot = H - 70 * k - foot_h - steps_h - 34 * k
    mx0, mx1 = 70 * k, W - 70 * k
    card_h = map_bot - map_top
    plan = paint_plan(key, int(mx1 - mx0 - 28 * k), int(card_h - 28 * k), tr, name, k)
    mask = Image.new('L', (int(mx1 - mx0), int(card_h)), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, mx1 - mx0 - 1, card_h - 1), radius=22 * k, fill=255)
    card = Image.new('RGB', mask.size, CREAM)
    card.paste(plan, (14 * k, 14 * k))
    cd = ImageDraw.Draw(card)
    cd.rectangle((14 * k, 14 * k, 14 * k + plan.size[0] - 1, 14 * k + plan.size[1] - 1), outline=PAVE_EDGE, width=2 * k)
    im.paste(card, (int(mx0), int(map_top)), mask)
    d.rounded_rectangle((mx0, map_top, mx1 - 1, map_bot - 1), radius=22 * k, outline=BRASS, width=3 * k)
    y = map_bot + 40 * k
    for i, lines in enumerate(steps):
        cxn, cyn = 128 * k, y + 28 * k
        d.ellipse((cxn - 31 * k, cyn - 31 * k, cxn + 31 * k, cyn + 31 * k), fill=BRASS)
        d.text((cxn, cyn + 2 * k), str(i + 1), font=fnum, fill=FOREST, anchor='mm')
        for j, line in enumerate(lines):
            d.text((190 * k, y + j * 56 * k), line, font=fs, fill=CREAM, anchor='la')
        y += max(1, len(lines)) * 56 * k + 26 * k
    S.centred_fit(d, H - 70 * k - 60 * k, words_['foot'], lambda s: fnt('italic', s), 40 * k, GOLD, W, W - 200 * k)
    return im


def paint_arms(tr, name):
    """The fingerpost's arms on one atlas, a row each (top to bottom): the cabin's arm with its point to the right, the
    same to the left, the museum's arm right, left. Cream boards with a forest line round them; the words sit on
    the board clear of the point."""
    from PIL import Image, ImageDraw
    W, Hr = 2048 * SS, 400 * SS
    rows = []
    for (big, small) in ((name, tr('tell your own story')), (tr('THE MUSEUM'), tr('and the Forecourt Theatre'))):
        for tip_right in (True, False):
            im = Image.new('RGB', (W, Hr), CREAM); d = ImageDraw.Draw(im)
            pr = W * (ARM_L - ARM_P) / ARM_L
            inset = 22 * SS
            if tip_right:
                shape = [(inset, inset), (pr - inset * 0.4, inset), (W - inset * 2.2, Hr / 2), (pr - inset * 0.4, Hr - inset), (inset, Hr - inset)]
                x0, x1 = inset * 3, pr - inset
            else:
                shape = [(W - inset, inset), (W - pr + inset * 0.4, inset), (inset * 2.2, Hr / 2), (W - pr + inset * 0.4, Hr - inset), (W - inset, Hr - inset)]
                x0, x1 = W - pr + inset, W - inset * 3
            d.line(shape + [shape[0]], fill=FOREST, width=9 * SS, joint='curve')
            mid = (x0 + x1) / 2
            fbig, _ = S.fitted(d, big, lambda s: fnt('cinzel', s), 150 * SS, (x1 - x0) - 60 * SS, tracking=10 * SS)
            widths = [d.textlength(ch, font=fbig) for ch in big]
            total = sum(widths) + 10 * SS * (len(big) - 1)
            x = mid - total / 2
            yb = Hr * 0.47 if small else Hr * 0.5
            for ch, cw in zip(big, widths):
                d.text((x, yb), ch, font=fbig, fill=FOREST, anchor='ls' if small else 'lm'); x += cw + 10 * SS
            if small:
                fsm = fnt('italic', 92 * SS)
                fsm, _ = S.fitted(d, small, lambda s: fnt('italic', s), 92 * SS, (x1 - x0) - 80 * SS)
                d.text((mid, Hr * 0.62), small, font=fsm, fill=INK, anchor='ma')
            rows.append(im)
    atlas = Image.new('RGB', (2048, 2048), CREAM)
    for i, im in enumerate(rows):
        atlas.paste(im.resize((2048, 512), Image.LANCZOS), (0, i * 512))
    return atlas


TEXTURES = {}                     # key -> file name in assets/tex


def make_textures():
    from PIL import Image
    tr, name = words()
    cp = copy_for(tr, name)
    sizes = {'stand_s': (STAND_W, STAND_H), 'stand_n': (STAND_W, STAND_H), 'easel': (EASEL_W, EASEL_H),
             'poster': (POSTER_W, POSTER_H)}
    sheet = []
    for key, (wm, hm) in sizes.items():
        im = paint_panel(key, wm, hm, tr, name, cp[key])
        sheet.append(im.resize((im.size[0] // (2 * SS), im.size[1] // (2 * SS)), Image.LANCZOS))
        # the panel's proportions are its own; the texture is 1024 x 2048 (a power of two, so it mips)
        fn = 'signs_%s.png' % key
        im.resize((1024, 2048), Image.LANCZOS).save(os.path.join(TEX, fn), optimize=True)
        TEXTURES[key] = fn
    arms = paint_arms(tr, name)
    arms.save(os.path.join(TEX, 'signs_arms.png'), optimize=True)
    TEXTURES['arms'] = 'signs_arms.png'
    # a contact sheet of the four faces and the arms, for review
    wsum = sum(s.size[0] for s in sheet) + 20 * (len(sheet) + 1)
    hmax = max(s.size[1] for s in sheet)
    contact = Image.new('RGB', (wsum, hmax + 40 + 512), (60, 60, 60))
    x = 20
    for s in sheet:
        contact.paste(s, (x, 20)); x += s.size[0] + 20
    contact.paste(arms.resize((1024, 1024)).crop((0, 0, 1024, 512)), (20, hmax + 30))
    contact.save(os.path.join(OUT, 'textures_sheet.jpg'), quality=90)
    print('textures', TEXTURES, flush=True)


# ---------------------------------------------------------------- materials and geometry
def setup_materials():
    material('sg_bronze', color=(0.40, 0.26, 0.13, 1), roughness=0.42, metallic=1.0)    # the museum's and the lamps' bronze
    material('sg_gilt', color=(1.0, 0.78, 0.38, 1), roughness=0.32, metallic=1.0)
    material('sg_forest', color=(0.03, 0.075, 0.055, 1), roughness=0.5)                   # the easel board's back
    material('sg_cream', color=(0.855, 0.776, 0.611, 1), roughness=0.6)                   # the arms' edges (the boards' cream)
    for key in ('stand_s', 'stand_n', 'easel', 'poster', 'arms'):
        material('sg_%s' % key, 'signs_%s' % key, roughness=0.62)


B = {}
def builder(name, mat, tile=1.0, smooth_deg=None):
    if name not in B:
        B[name] = Builder(name, mat, tile=tile, lightmap=False, vcol=False, smooth=smooth_deg)
    return B[name]


def lpt(o, f, u, y, w):
    """A campus point in a sign's frame: o its plan position, f the way it faces; u to the reader's right, y up, w
    toward the reader."""
    fx, fz = f
    return (o[0] + fz * u + fx * w, y, o[1] - fx * u + fz * w)


def lbox(b, o, f, u, y, w, su, sy, sw, faces='all'):
    """A box in a sign's frame (sizes along u, y, w)."""
    c = lpt(o, f, u, y, w)
    b.box(c[0], c[1], c[2], su, sy, sw, math.atan2(f[0], f[1]), faces=faces)


def obox(b, c, ex, ey, ez, sx, sy, sz):
    """A box at campus c with its edges along the unit campus vectors ex, ey, ez."""
    C = Vector(c); Xv = Vector(ex) * (sx / 2); Yv = Vector(ey) * (sy / 2); Zv = Vector(ez) * (sz / 2)
    def q(a, bb, cc): return P(*(C + Xv * a + Yv * bb + Zv * cc))
    for (n, pts) in ((Xv, [(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)]), (-Xv, [(-1, -1, 1), (-1, 1, 1), (-1, 1, -1), (-1, -1, -1)]),
                     (Yv, [(-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)]), (-Yv, [(-1, -1, 1), (-1, -1, -1), (1, -1, -1), (1, -1, 1)]),
                     (Zv, [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]), (-Zv, [(1, -1, -1), (-1, -1, -1), (-1, 1, -1), (1, 1, -1)])):
        b.face([q(*p) for p in pts], D(*n.normalized()))


def build_stand():
    """The portico's exhibition stand: two bronze posts on a stepped base, a cornice with gilt finials, and between
    the posts a two-sided panel in a gilt frame, its face to the forecourt, its back to the doors."""
    o, f = STAND, STAND_F
    br = builder('sg_bronze', 'sg_bronze'); gl = builder('sg_gilt', 'sg_gilt', smooth_deg=50)
    y0 = 0.0
    lbox(br, o, f, 0, y0 + 0.03, 0, 1.04, 0.06, 0.38, faces='xXYzZ')    # no underside: it would lie in the floor's plane
    lbox(br, o, f, 0, y0 + 0.075, 0, 0.96, 0.03, 0.30)
    top = STAND_Y0 + STAND_H + 0.16
    for s in (-1, 1):
        lbox(br, o, f, s * 0.455, (y0 + 0.09 + top) / 2, 0, 0.05, top - y0 - 0.09, 0.05)
    lbox(br, o, f, 0, STAND_Y0 - 0.09, 0, 0.86, 0.035, 0.035)
    lbox(br, o, f, 0, top + 0.025, 0, 1.06, 0.05, 0.12)
    lbox(br, o, f, 0, top + 0.06, 0, 0.98, 0.02, 0.09)
    for s in (-1, 1):
        cx, cy, cz = lpt(o, f, s * 0.455, top + 0.07, 0)
        lathe(gl, cx, cz, [(cy, 0.022), (cy + 0.02, 0.022)], n=12, cap_top=False)
        S.ball(gl, (cx, cy + 0.055, cz), 0.035, rings=6, k=12)
    # the panel: a 3 cm board, its two printed faces, a gilt frame proud of both
    yc = STAND_Y0 + STAND_H / 2
    S.quad_facing(builder('sg_stand_s', 'sg_stand_s'), lpt(o, f, 0, yc, 0.0155), f, STAND_W, STAND_H)
    S.quad_facing(builder('sg_stand_n', 'sg_stand_n'), lpt(o, f, 0, yc, -0.0155), (-f[0], -f[1]), STAND_W, STAND_H)
    fw = 0.035
    for (u, y, su, sy) in ((0, STAND_Y0 + STAND_H + fw / 2, STAND_W + 2 * fw, fw), (0, STAND_Y0 - fw / 2, STAND_W + 2 * fw, fw),
                           (-(STAND_W + fw) / 2, yc, fw, STAND_H), ((STAND_W + fw) / 2, yc, fw, STAND_H)):
        lbox(gl, o, f, u, y, 0, su, sy, 0.05)


def build_easel():
    """The rotunda's notice: a framed panel leaning back on a bronze easel (two front legs splayed out at the foot, a
    ledge the panel stands on, a back leg), its face to the lobby arch, the board's forest back to the doors."""
    o, f = EASEL, EASEL_F
    br = builder('sg_bronze_round', 'sg_bronze', smooth_deg=50); gl = builder('sg_gilt', 'sg_gilt', smooth_deg=50)
    t = EASEL_TILT
    fx, fz = f
    R = Vector((fz, 0.0, -fx)); Fv = Vector((fx, 0.0, fz)); Up = Vector((0.0, 1.0, 0.0))
    Ut = (Up * math.cos(t) - Fv * math.sin(t)).normalized()       # up the panel
    Nt = R.cross(Ut).normalized()                                  # out of its face
    base = Vector(lpt(o, f, 0, EASEL_Y0, 0.0))                     # the middle of the panel's bottom edge
    def on(u, v, w):                                               # a point in the panel's plane (+ w out of it)
        return base + R * u + Ut * v + Nt * w
    centre = on(0, EASEL_H / 2, 0)
    S.quad_facing(builder('sg_easel', 'sg_easel'), tuple(centre + Nt * 0.012), f, EASEL_W, EASEL_H, tilt=t)
    S.quad_facing(builder('sg_forest', 'sg_forest'), tuple(centre - Nt * 0.012), (-fx, -fz), EASEL_W + 0.09, EASEL_H + 0.09, tilt=-t)
    fw = 0.045
    for (u, v, su, sv) in ((0, EASEL_H + fw / 2, EASEL_W + 2 * fw, fw), (0, -fw / 2, EASEL_W + 2 * fw, fw),
                           (-(EASEL_W + fw) / 2, EASEL_H / 2, fw, EASEL_H), ((EASEL_W + fw) / 2, EASEL_H / 2, fw, EASEL_H)):
        obox(gl, tuple(on(u, v, 0.004)), tuple(R), tuple(Ut), tuple(Nt), su, sv, 0.04)
    # the legs: in the panel's plane, behind the board, from the floor to above the frame
    def plane_pt(u, y, back):                                      # the point at height y on the plane, `back` behind it
        v = (y - EASEL_Y0) / math.cos(t)
        p = on(u, v, -back)
        return (p.x, p.y, p.z)
    top_y = EASEL_Y0 + (EASEL_H + 0.17) * math.cos(t)
    for s in (-1, 1):
        S.cylinder(br, plane_pt(s * 0.27, 0.0, 0.05), plane_pt(s * 0.17, top_y, 0.05), 0.016, n=10)
        S.ball(br, plane_pt(s * 0.17, top_y + 0.01, 0.05), 0.024, rings=5, k=10)
    S.cylinder(br, plane_pt(-0.17, top_y - 0.04, 0.05), plane_pt(0.17, top_y - 0.04, 0.05), 0.012, n=8)
    S.cylinder(br, plane_pt(-0.25, 0.42, 0.05), plane_pt(0.25, 0.42, 0.05), 0.011, n=8)
    # the ledge the panel's frame stands on, and the back leg to the floor
    lb = builder('sg_bronze', 'sg_bronze')
    ledge = on(0, -fw - 0.012, 0.0)
    obox(lb, tuple(ledge), tuple(R), tuple(Ut), tuple(Nt), EASEL_W + 0.16, 0.024, 0.09)
    head = Vector(plane_pt(0.0, top_y - 0.04, 0.05))
    foot = Vector(lpt(o, f, 0.0, 0.0, -0.62))
    S.cylinder(br, tuple(head), tuple(foot), 0.015, n=10)


def build_poster():
    """The foyer's poster: the same size, height and gilt frame as the foyer's other three (bl/auditorium.py)."""
    x, z = POSTER
    pb = builder('sg_poster', 'sg_poster'); fr = builder('sg_gilt_box', 'sg_gilt')
    S.quad_facing(pb, (x + 0.035, POSTER_YC, z), POSTER_F, POSTER_W, POSTER_H)
    f_ = 0.06; xf = x + 0.03; yc = POSTER_YC; w, h = POSTER_W, POSTER_H
    for (cy, cz, sy, sz) in ((yc + h / 2 + f_ / 2, z, f_, w + 2 * f_), (yc - h / 2 - f_ / 2, z, f_, w + 2 * f_),
                             (yc, z + w / 2 + f_ / 2, h, f_), (yc, z - w / 2 - f_ / 2, h, f_)):
        fr.box(xf, cy, cz, 0.06, sy, sz, faces='XyYzZ')


def arm(b_face, b_edge, o, y, d, row):
    """One fingerpost arm: a board pointing along the plan direction d from the post at o, its middle at height y.
    Both faces carry the atlas `row` (0 the cabin's arm, 1 the museum's), each with the words reading left to right
    and the point on the side the arm points to."""
    dx, dz = d
    r0 = 0.055
    n = (dz, -dx)                                                  # a face's outward normal (and its opposite)
    def pt(s, yy, side):
        return (o[0] + dx * s + n[0] * side * ARM_T / 2, yy, o[1] + dz * s + n[1] * side * ARM_T / 2)
    yb, yt = y - ARM_H / 2, y + ARM_H / 2
    sr, st = r0 + ARM_L - ARM_P, r0 + ARM_L
    for side in (1, -1):
        m = (n[0] * side, n[1] * side)
        right = (m[1], -m[0])                                      # the reader's right, looking at this face
        tip_right = dx * right[0] + dz * right[1] > 0
        k = row * 2 + (0 if tip_right else 1)                      # the atlas row: a quarter of the texture each
        v0, v1 = 1.0 - (k + 1) / 4.0, 1.0 - k / 4.0
        def uv(s, yy):
            u = (s - r0) / ARM_L
            return ((u if tip_right else 1.0 - u), v0 + (yy - yb) / ARM_H * (v1 - v0))
        ring = [(r0, yb), (sr, yb), (st, y), (sr, yt), (r0, yt)]
        pts = [P(*pt(s, yy, side)) for (s, yy) in ring]
        face_uv(b_face, pts, D(m[0], 0, m[1]), [uv(s, yy) for (s, yy) in ring])
    # the edges: top, bottom, the point's two slopes, the root
    ring = [(r0, yb), (sr, yb), (st, y), (sr, yt), (r0, yt)]
    for (a, c) in zip(ring, ring[1:] + ring[:1]):
        (s0, y0_), (s1, y1_) = a, c
        tx, ty = s1 - s0, y1_ - y0_
        out_s, out_y = ty, -tx                                     # outward in the board's (s, y) plane (the ring runs anticlockwise)
        ln = math.hypot(out_s, out_y)
        nv = (dx * out_s / ln, out_y / ln, dz * out_s / ln)
        b_edge.face([P(*pt(s0, y0_, 1)), P(*pt(s1, y1_, 1)), P(*pt(s1, y1_, -1)), P(*pt(s0, y0_, -1))], D(*nv))


def build_fingerpost():
    """The fountain's fingerpost: a turned bronze post with a gilt ball on top and two cream arms, the cabin's
    pointing on down the path (south), the museum's back up it."""
    x, z = FINGER
    y0 = gh(x, z)
    br = builder('sg_bronze_round', 'sg_bronze', smooth_deg=50); gl = builder('sg_gilt', 'sg_gilt', smooth_deg=50)
    lathe(br, x, z, [(y0 - 0.05, 0.15), (y0 + 0.05, 0.15), (y0 + 0.09, 0.125), (y0 + 0.17, 0.09), (y0 + 0.32, 0.075),
                     (y0 + 0.35, 0.092), (y0 + 0.40, 0.092), (y0 + 0.43, 0.064), (y0 + 2.56, 0.05), (y0 + 2.59, 0.07),
                     (y0 + 2.64, 0.07), (y0 + 2.67, 0.04)], n=20)
    lathe(gl, x, z, [(y0 + 2.67, 0.026), (y0 + 2.71, 0.026)], n=12, cap_top=False)
    S.ball(gl, (x, y0 + 2.77, z), 0.065, rings=8, k=16)
    fa = builder('sg_arms', 'sg_arms'); ed = builder('sg_cream', 'sg_cream')
    for (h, d, row) in ((2.30, (0.0, 1.0), 0), (1.98, (0.0, -1.0), 1)):
        # a collar round the post where the arm is fixed
        lathe(br, x, z, [(y0 + h - 0.15, 0.06), (y0 + h - 0.13, 0.068), (y0 + h + 0.13, 0.068), (y0 + h + 0.15, 0.06)], n=20)
        arm(fa, ed, (x, z), y0 + h, d, row)


# ---------------------------------------------------------------- export and previews
def export_glb():
    obs = [o for o in bpy.data.objects if o.type == 'MESH' and not o.get('preview_only')]
    select_only(obs)
    fp = os.path.join(PIPE, 'Signs.glb')
    bpy.ops.export_scene.gltf(filepath=fp, export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
                              export_texcoords=True, export_normals=True, export_tangents=True, export_materials='EXPORT',
                              export_image_format='AUTO', export_vertex_color='NONE', export_lights=False, export_cameras=False)
    print('exported', fp, os.path.getsize(fp), 'bytes', flush=True)


VIEWS = {
    # name: (eye, target, fov, context glbs)
    'spawn': ((0.0, -0.75 + 1.62, 24.0), (0.0, 1.4, 12.0), 70, ('Museum', 'Outside')),
    'stand': ((-1.9, 0.0 + 1.62, 17.4), (STAND[0], 1.3, STAND[1]), 60, ('Museum', 'Outside')),
    'stand_back': ((-1.2, 1.62, 12.2), (STAND[0], 1.3, STAND[1]), 62, ('Museum', 'Outside')),
    'easel': ((0.0, 1.62, 1.4), (EASEL[0], 1.3, EASEL[1]), 62, ('Museum',)),
    'easel_near': (lpt(EASEL, EASEL_F, 0.0, 1.62, 1.5), (EASEL[0], 1.35, EASEL[1]), 55, ('Museum',)),
    'poster': ((9.0, 1.62, -5.4), (POSTER[0], 1.9, POSTER[1]), 62, ('Auditorium', 'Museum')),
    'finger': ((-0.4, -0.75 + 1.62, 37.0), (FINGER[0], 1.3, FINGER[1]), 60, ('Outside',)),
    'finger_near': ((0.6, -0.75 + 1.62, 41.0), (FINGER[0], 1.4, FINGER[1] + 0.3), 60, ('Outside',)),
}


def preview_scene(names):
    ue = os.path.join(SP, 'unreal', 'Pipeline', 'out', 'ue')
    for n in names:
        fp = os.path.join(ue, n + '.glb')
        if not os.path.exists(fp):
            continue
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=fp)
        for o in bpy.data.objects:
            if o not in before:
                o['preview_only'] = 1
    sd = bpy.data.lights.new('Sun', 'SUN'); sd.energy = 3.4; sd.angle = math.radians(1.5); sd.color = (1.0, 0.95, 0.88)
    sun = bpy.data.objects.new('Sun', sd); sun['preview_only'] = 1; bpy.context.scene.collection.objects.link(sun)
    sun.rotation_euler = Vector((0.35, 0.65, -0.68)).normalized().to_track_quat('-Z', 'Y').to_euler()
    w = bpy.data.worlds.new('World'); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.45, 0.58, 0.78, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
    for (nm, pos, watts) in (('rot', (0.0, 4.5, 5.8), 2500), ('rot2', (-1.0, 2.6, 6.5), 600), ('foyer', (9.0, 3.6, -7.4), 900),
                             ('foyer2', (9.0, 3.6, -11.2), 700)):
        ld = bpy.data.lights.new(nm, 'POINT'); ld.energy = watts; ld.color = (1.0, 0.88, 0.72); ld.shadow_soft_size = 0.4
        ob = bpy.data.objects.new(nm, ld); ob.location = P(*pos); ob['preview_only'] = 1
        bpy.context.scene.collection.objects.link(ob)


def render(name, eye, target, fov=60):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
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
    if '--textures' in sys.argv:
        return
    setup_materials()
    build_stand()
    build_easel()
    build_poster()
    build_fingerpost()
    for name, b in B.items():
        if b.count:
            b.finish()
    obs = [o for o in sc.objects if o.type == 'MESH']
    import bmesh
    for o in obs:                                      # the arms' five-sided faces and the lathes' caps: triangles, so
        bm = bmesh.new(); bm.from_mesh(o.data)         # the exporter can write tangents for every face
        ngons = [f for f in bm.faces if len(f.verts) > 4]
        if ngons:
            bmesh.ops.triangulate(bm, faces=ngons, quad_method='BEAUTY', ngon_method='BEAUTY')
            bm.to_mesh(o.data)
        bm.free()
    print('objects', len(obs), 'tris ~', sum(len(o.data.polygons) * 2 for o in obs), 'built in %.0f s' % (time.time() - t0), flush=True)
    export_glb()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'signs.blend'))
    if RENDER:
        want = [a.split('=')[1].split(',') for a in sys.argv if a.startswith('--views=')]
        names = want[0] if want else list(VIEWS)
        ctx = sorted(set(c for n in names for c in VIEWS[n][3]))
        preview_scene(ctx)
        for m in bpy.data.materials:
            if 'glass' in m.name.lower():
                m.surface_render_method = 'BLENDED'
        for n in names:
            eye, target, fov, _ = VIEWS[n]
            render(n, eye, target, fov=fov)
    print('done in %.0f s' % (time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
