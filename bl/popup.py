"""The pop-up books on the Reading Room's south reading table: library books that open as paper scenes.

Run: python3 bl/popup.py [--render] [--quick] [--only=<book>]   (bpy 5.x as a module, like the other builders)

A pop-up book lies on the table between the two lamps, its spine across the table (campus x) and its near page
toward the reader in the middle chair on the south side (+z). Opened, the far page stands up as the backdrop and
three paper cut-outs stand between it and the reader, back to front, smaller toward the front: the classic
theatre pop-up. Each spread is one page of the book in the library (DT_Books), and its caption is printed on the
near page.

Every piece Unreal moves is its own mesh, built standing (open) and tagged
  popup__<book>_s<n>_back    the far page: a board, its art inside and the book's cover outside
  popup__<book>_s<n>_l1..l3  the paper layers, back (l3) to front (l1), each a collage of extruded paper pieces
  popup__<book>_s<n>_floor   the near page's printed art and caption
  popup__base                the book's base (the back cover and the page block), shared by every spread
AWTAPopUpBookActor spawns them, hinges each moving piece on its bottom edge and folds it toward the reader to
close the book (the backdrop's cover then lies face up). out/popup/layout.json says where the book is, which
books there are and which DT_Books page each spread shows.

Writes unreal/Pipeline/out/popup/PopUp.glb, layout.json; assets/tex/popup_*.png; previews in assets/popup/.
"""
import json
import math
import os
import sys
import time

import bpy                                                      # noqa: I001  (bpy first: it makes bmesh importable)
import bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import clientpack                                                # noqa: E402
import library as L                                              # noqa: E402
from library import P, D, material, MATS, select_only            # noqa: E402

SP = L.SP
OUT = os.path.join(SP, 'assets', 'popup')
PIPE = os.path.join(SP, 'unreal', 'Pipeline', 'out', 'popup')
TEX = os.path.join(SP, 'assets', 'tex')
FONTS = os.path.join(HERE, 'fonts')
LANG_DIR = os.path.join(SP, 'unreal', 'Pipeline', 'content', 'lang')
CONTENT = os.path.join(SP, clientpack.get('content', 'unreal/Pipeline/content'))   # the pack's books.json
READER_SEAT = 'lib10'            # bl/library.py's chair at the middle of the table's south side, facing the book
RENDER = '--render' in sys.argv
QUICK = '--quick' in sys.argv
ONLY = [a.split('=', 1)[1] for a in sys.argv if a.startswith('--only=')]
os.makedirs(OUT, exist_ok=True); os.makedirs(PIPE, exist_ok=True)

# ---------------------------------------------------------------- the book on the table (campus metres)
# bl/library.py: the south reading table's top is at y 0.79, centred on x -19.5, z 4.6; its lamps stand at x +-0.65
# from the middle, its chairs 0.85 m either side.
BX = -19.5                       # the book's middle (x)
TOP = 0.79                       # the table top
SPINE_Z = 4.50                   # the spine line (z); the near page runs from here toward the reader (+z)
PAGE_W = 0.52                    # the pages' width (x)
PAGE_D = 0.28                    # the near page's depth (z), and the backdrop's height
BASE_T = 0.016                   # the back cover and the page block under the near page
FLOOR_Y = TOP + BASE_T           # the near page's surface
HINGE_Y = FLOOR_Y + 0.003        # the backdrop's bottom edge (a little above, so it closes onto the page, not into it)
BOARD_T = 0.003                  # the backdrop board
PAPER_T = 0.0015                 # one layer of card
LAYERS = [(0.18, 0.090), (0.12, 0.150), (0.06, 0.205)]   # l1 (front), l2, l3 (back): distance from the spine, height
LAYER_W = 0.48                   # the cut-outs' width
READER = (0.0, 0.0, 1.0)         # toward the reader (campus +z)


def srgb(h):
    """'#rrggbb' -> linear (r, g, b, 1) for a material colour."""
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c) + (1.0,)


# ---------------------------------------------------------------- a mesh of several paper colours
class Part:
    """One tagged mesh: faces in campus coordinates, each with its material and (optionally) uvs."""
    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('uv')
        self.mats = []

    def _mi(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def poly(self, pts, normal, mat, uvs=None):
        """A polygon (campus points, any count, convex or not) facing `normal` (campus)."""
        n = D(*normal)
        vs = [self.bm.verts.new(P(*p)) for p in pts]
        try:
            f = self.bm.faces.new(vs)
        except ValueError:
            return None
        f.normal_update()
        if f.normal.dot(n) < 0:
            f.normal_flip()
        f.material_index = self._mi(mat)
        if uvs is not None:
            lookup = {v: uv for v, uv in zip(vs, uvs)}
            for loop in f.loops:
                loop[self.uv].uv = lookup[loop.vert]
        return f

    def prism(self, poly2d, frame, depth, mat):
        """poly2d (u, v metres) extruded `depth` along the frame's normal: frame = (origin, U, V, N) campus vectors."""
        O, U, V, N = frame
        pts = list(poly2d)
        area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
        if area < 0:
            pts.reverse()
        if len(pts) < 3 or abs(area) < 1e-9:
            return
        def at(u, v, w):
            return tuple(O[k] + U[k] * u + V[k] * v + N[k] * w for k in range(3))
        front = [at(u, v, depth) for u, v in pts]
        back = [at(u, v, 0.0) for u, v in pts]
        self.poly(front, N, mat)
        self.poly(back, tuple(-c for c in N), mat)
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            du, dv = pts[j][0] - pts[i][0], pts[j][1] - pts[i][1]
            out = tuple(U[k] * dv - V[k] * du for k in range(3))        # the outward side, for a ccw outline
            self.poly([back[i], back[j], front[j], front[i]], out, mat)

    def box(self, c, s, mat, faces='xXyYzZ'):
        """An axis box, centre c and size s (campus)."""
        (cx, cy, cz), (sx, sy, sz) = c, s
        x0, x1, y0, y1, z0, z1 = cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz - sz / 2, cz + sz / 2
        F = {'x': ([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], (-1, 0, 0)),
             'X': ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], (1, 0, 0)),
             'y': ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0)),
             'Y': ([(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)], (0, 1, 0)),
             'z': ([(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)], (0, 0, -1)),
             'Z': ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1))}
        for k in faces:
            self.poly(F[k][0], F[k][1], mat)

    def finish(self):
        # triangles now (ear clipping keeps the concave cut-outs right), so the exporter can write tangents
        bmesh.ops.triangulate(self.bm, faces=self.bm.faces[:], quad_method='BEAUTY', ngon_method='EAR_CLIP')
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(MATS[m])
        for p in me.polygons:
            p.use_smooth = False
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(ob)
        return ob


# ---------------------------------------------------------------- paper shapes (u across, v up, metres)
def arc(cu, cv, r, a0, a1, n=12):
    return [(cu + r * math.cos(a0 + (a1 - a0) * i / n), cv + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def circle(cu, cv, r, n=28):
    return arc(cu, cv, r, 0.0, 2 * math.pi, n)[:-1]


def ellipse(cu, cv, rx, ry, n=28, rot=0.0):
    c, s = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cu + x * c - y * s, cv + x * s + y * c))
    return out


def rect(u0, v0, u1, v1):
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def rrect(u0, v0, u1, v1, r, n=5):
    r = min(r, (u1 - u0) / 2, (v1 - v0) / 2)
    pts = []
    for (cu, cv, a0) in ((u1 - r, v0 + r, -math.pi / 2), (u1 - r, v1 - r, 0.0), (u0 + r, v1 - r, math.pi / 2), (u0 + r, v0 + r, math.pi)):
        pts += arc(cu, cv, r, a0, a0 + math.pi / 2, n)
    return pts


def ridge(u0, u1, top, n=48):
    """A ground strip: from v 0 up to the curve top(u) and back down."""
    pts = [(u0, 0.0)]
    for i in range(n + 1):
        u = u0 + (u1 - u0) * i / n
        pts.append((u, max(0.004, top(u))))
    pts.append((u1, 0.0))
    return pts


def hills(u0, u1, base, amp, waves, phase=0.0):
    return ridge(u0, u1, lambda u: base + amp * (0.5 + 0.5 * math.cos((u - u0) / (u1 - u0) * waves * 2 * math.pi + phase)))


def sea(u0, u1, base, amp, crests):
    """Scalloped wave crests along the top."""
    def top(u):
        t = (u - u0) / (u1 - u0) * crests
        f = t - math.floor(t)
        return base + amp * math.sin(math.pi * f) ** 0.6
    return ridge(u0, u1, top, n=crests * 10)


def peaks(u0, u1, base, tops):
    """A mountain range: (u, height) peaks joined by valleys at `base`, down to v 0."""
    pts = [(u0, 0.0), (u0, base)]
    for i, (u, h) in enumerate(tops):
        pts.append((u, h))
        nxt = tops[i + 1][0] if i + 1 < len(tops) else u1
        pts.append(((u + nxt) / 2, base + (h - base) * 0.35 if i + 1 < len(tops) else base))
    pts += [(u1, base), (u1, 0.0)]
    return pts


def snowcap(u, h, base, frac=0.3):
    """The white top of a peak at (u, h) whose slopes reach `base` half a span either side."""
    drop = (h - base) * frac
    w = drop * 0.9
    return [(u, h + 0.001), (u + w, h - drop), (u + w * 0.45, h - drop * 0.75), (u + w * 0.1, h - drop * 1.05),
            (u - w * 0.3, h - drop * 0.7), (u - w * 0.65, h - drop * 0.95), (u - w, h - drop)]


def puffs(circles, n=96):
    """The outline of overlapping round puffs [(u, v, r)], seen from their middle: a cloud, a tree's crown."""
    cu = sum(c[0] for c in circles) / len(circles)
    cv = sum(c[1] for c in circles) / len(circles)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        dx, dy = math.cos(a), math.sin(a)
        best = 0.0
        for (x, y, r) in circles:
            ox, oy = cu - x, cv - y
            b = ox * dx + oy * dy
            c = ox * ox + oy * oy - r * r
            disc = b * b - c
            if disc >= 0:
                best = max(best, -b + math.sqrt(disc))
        pts.append((cu + dx * best, cv + dy * best))
    return pts


def cloud(cu, cv, w, h, bumps=4):
    """A puffy cloud w wide and about h tall, its underside at cv: big puffs along the top, small ones below."""
    circles = []
    for i in range(bumps):
        t = (i + 0.5) / bumps
        r = h * (0.38 + 0.22 * math.sin(math.pi * t))
        circles.append((cu - w / 2 + w * t, cv + h * 0.42 + h * 0.18 * math.sin(math.pi * t), r))
    for i in range(bumps - 1):
        t = (i + 1) / bumps
        circles.append((cu - w / 2 + w * t, cv + h * 0.28, h * 0.27))
    circles.append((cu - w / 2 + h * 0.2, cv + h * 0.3, h * 0.24))
    circles.append((cu + w / 2 - h * 0.2, cv + h * 0.3, h * 0.24))
    return puffs(circles)


def pine(cu, base, h, w):
    tiers = 3
    pts = [(cu + w * 0.08, base), (cu + w * 0.08, base + h * 0.16)]
    for k in range(tiers):
        y0 = base + h * (0.16 + 0.26 * k)
        ww = w * (0.5 - 0.12 * k)
        pts += [(cu + ww, y0), (cu + w * 0.12 * (tiers - k) / tiers, y0 + h * 0.32)]
    pts.append((cu, base + h))
    left = [(2 * cu - u, v) for (u, v) in reversed(pts)]
    return pts + left[1:-1]


def round_tree(cu, base, h, w):
    """(trunk, crown) polygons: a trunk under a round, lumpy crown."""
    trunk = rect(cu - w * 0.07, base, cu + w * 0.07, base + h * 0.5)
    r = w * 0.3
    crown = puffs([(cu, base + h - r, r), (cu - w * 0.22, base + h * 0.55, r * 0.9), (cu + w * 0.22, base + h * 0.55, r * 0.9),
                   (cu, base + h * 0.5, r * 0.85)])
    return trunk, crown


def fish(cu, cv, length, facing=1.0):
    """A fish in profile, its head toward +u (facing 1) or -u: the body round the head, the tail at the back."""
    pts = []
    for i in range(29):
        a = math.radians(-155 + 310 * i / 28)
        pts.append((cu + facing * length * 0.5 * math.cos(a), cv + length * 0.24 * math.sin(a)))
    tx = cu - facing * length * 0.45
    pts += [(tx - facing * length * 0.25, cv + length * 0.22), (tx - facing * length * 0.16, cv), (tx - facing * length * 0.25, cv - length * 0.22)]
    return pts


def flower(cu, base, h, r, petals=6):
    stem = rect(cu - 0.0022, base, cu + 0.0022, base + h)
    head = []
    for i in range(petals * 8):
        a = 2 * math.pi * i / (petals * 8)
        rr = r * (0.62 + 0.38 * abs(math.cos(petals * a / 2)))
        head.append((cu + rr * math.cos(a), base + h + rr * math.sin(a)))
    leaf = ellipse(cu + r * 0.45, base + h * 0.42, r * 0.5, r * 0.18, n=16, rot=0.6)
    return stem, head, circle(cu, base + h, r * 0.32, n=16), leaf


def wings(cu, cv, s, tilt=0.0):
    """A butterfly's four wings and its body."""
    out = []
    for side in (-1, 1):
        out.append(ellipse(cu + side * s * 0.42, cv + s * 0.22, s * 0.46, s * 0.34, n=20, rot=side * (0.55 + tilt)))
        out.append(ellipse(cu + side * s * 0.3, cv - s * 0.22, s * 0.3, s * 0.24, n=18, rot=-side * (0.5 - tilt)))
    return out, ellipse(cu, cv, s * 0.07, s * 0.42, n=12)


def scaled(poly, k, cu, cv):
    return [(cu + (u - cu) * k, cv + (v - cv) * k) for (u, v) in poly]


# ---------------------------------------------------------------- the scenes
# A scene: what each layer holds, as [(colour, polygon)], plus how the backdrop and the near page are painted.
# Colours are sRGB hex; each distinct colour is one paper material.
def scene_water_0():
    """Water on the move: the sun over the sea, an ice sheet, a boat."""
    l3 = [('#d7ecf5', peaks(-0.24, 0.24, 0.07, [(-0.18, 0.19), (-0.07, 0.15), (0.05, 0.12)])),
          ('#ffffff', snowcap(-0.18, 0.19, 0.07)), ('#ffffff', snowcap(-0.07, 0.15, 0.07)),
          ('#5cb8d6', sea(-0.24, 0.24, 0.045, 0.012, 7))]
    l2 = [('#3a9cc8', sea(-0.24, 0.24, 0.05, 0.016, 6)),
          ('#8d6e63', [(0.03, 0.06), (0.13, 0.06), (0.115, 0.04), (0.045, 0.04)]),
          ('#fafafa', [(0.075, 0.064), (0.075, 0.14), (0.125, 0.07)]),
          ('#e0574b', [(0.07, 0.064), (0.07, 0.12), (0.035, 0.07)]),
          ('#5d4037', rect(0.072, 0.06, 0.076, 0.145))]
    l1 = [('#1f6f9e', sea(-0.24, 0.24, 0.045, 0.022, 5)), ('#e8f4f6', sea(-0.24, 0.24, 0.02, 0.012, 9))]
    return l3, l2, l1


def scene_water_1():
    """Evaporation and transpiration: vapour rising off the sea and off the trees."""
    l3 = [('#9ccc65', hills(-0.24, 0.24, 0.09, 0.05, 1.5, 0.4))]
    l2 = [('#33691e', pine(0.05, 0.0, 0.14, 0.07)), ('#33691e', pine(0.12, 0.0, 0.12, 0.06)),
          ('#558b2f', round_tree(0.19, 0.0, 0.13, 0.08)[1]), ('#6d4c41', round_tree(0.19, 0.0, 0.13, 0.08)[0]),
          ('#7cb342', hills(-0.02, 0.24, 0.035, 0.015, 1.0, 1.2)),
          ('#2f8fbf', sea(-0.24, 0.0, 0.04, 0.012, 4))]
    l1 = [('#1f6f9e', sea(-0.24, 0.24, 0.035, 0.02, 6)), ('#e8f4f6', sea(-0.24, 0.24, 0.016, 0.01, 10))]
    return l3, l2, l1


def scene_water_2():
    """Condensation: moist air rising and cooling into clouds over the hills."""
    l3 = [('#7b8fa6', peaks(-0.24, 0.24, 0.08, [(-0.15, 0.15), (0.02, 0.18), (0.16, 0.13)])),
          ('#ffffff', cloud(-0.02, 0.135, 0.3, 0.06)), ('#eceff1', cloud(0.14, 0.12, 0.16, 0.045, 3))]
    l2 = [('#fafafa', cloud(-0.12, 0.07, 0.2, 0.05, 3)), ('#8bc34a', hills(-0.24, 0.24, 0.06, 0.03, 1.2, 2.0))]
    l1 = [('#2f8fbf', sea(-0.24, 0.24, 0.03, 0.016, 7)), ('#7cb342', hills(0.02, 0.24, 0.014, 0.05, 1.0, math.pi))]
    return l3, l2, l1


def scene_water_3():
    """Precipitation and collection: rain and snow on the mountains, a river down to the lake."""
    l3 = [('#6d7f95', peaks(-0.24, 0.24, 0.09, [(-0.17, 0.2), (-0.04, 0.17), (0.1, 0.19), (0.2, 0.15)])),
          ('#ffffff', snowcap(-0.17, 0.2, 0.09, 0.4)), ('#ffffff', snowcap(-0.04, 0.17, 0.09, 0.4)),
          ('#ffffff', snowcap(0.1, 0.19, 0.09, 0.4)), ('#90a4ae', cloud(0.08, 0.145, 0.24, 0.05, 4))]
    l2 = [('#689f38', hills(-0.24, 0.24, 0.07, 0.04, 1.0, 0.8)),
          ('#4fa7d4', [(-0.01, 0.0), (0.03, 0.0), (0.02, 0.03), (0.05, 0.06), (0.04, 0.09), (0.03, 0.09), (0.035, 0.06), (0.005, 0.03)])]
    house = [('#f3e5ab', rect(-0.165, 0.0, -0.12, 0.045)), ('#c0392b', [(-0.172, 0.044), (-0.113, 0.044), (-0.1425, 0.07)]),
             ('#6d4c41', rect(-0.146, 0.0, -0.136, 0.022)), ('#8fcbe8', rect(-0.16, 0.026, -0.15, 0.036)),
             ('#8fcbe8', rect(-0.132, 0.026, -0.122, 0.036)), ('#8d6e63', rect(-0.126, 0.05, -0.12, 0.068)),
             ('#33691e', pine(0.17, 0.0, 0.085, 0.05)), ('#33691e', pine(0.205, 0.0, 0.07, 0.04))]
    l1 = [('#2b7fb3', sea(-0.24, 0.24, 0.03, 0.012, 6))] + house
    return l3, l2, l1


def coral_branch(cu, base, h, w, seed):
    import random
    r = random.Random(seed)
    polys = [rrect(cu - w * 0.09, base, cu + w * 0.09, base + h * 0.55, w * 0.08)]
    for k in range(4):
        a = math.radians(-50 + k * 33 + r.uniform(-8, 8))
        L_ = h * r.uniform(0.45, 0.62)
        x0, y0 = cu, base + h * 0.4
        x1, y1 = x0 + math.sin(a) * L_, y0 + math.cos(a) * L_
        t = w * 0.07
        nx, ny = math.cos(a) * t, -math.sin(a) * t
        polys.append([(x0 - nx, y0 - ny), (x0 + nx, y0 + ny), (x1 + nx * 0.8, y1 + ny * 0.8), (x1 - nx * 0.8, y1 - ny * 0.8)])
        polys.append(circle(x1, y1, t * 1.05, n=12))
    return polys


def coral_fan(cu, base, w, h):
    """A sea fan on a short stem."""
    pts = [(cu - 0.004, base), (cu + 0.004, base)]
    for i in range(17):
        a = 0.15 + (math.pi - 0.3) * i / 16
        pts.append((cu + w / 2 * math.cos(a), base + h * 0.25 + h * 0.75 * math.sin(a)))
    return pts


def turtle(cu, cv, s, facing=1.0):
    shell = ellipse(cu, cv, s * 0.5, s * 0.32, n=26)
    flippers = [ellipse(cu + facing * s * 0.25, cv + s * 0.32, s * 0.28, s * 0.09, n=14, rot=facing * 0.5),
                ellipse(cu + facing * s * 0.25, cv - s * 0.3, s * 0.26, s * 0.08, n=14, rot=-facing * 0.5),
                ellipse(cu - facing * s * 0.38, cv + s * 0.2, s * 0.14, s * 0.06, n=12, rot=-facing * 0.6),
                ellipse(cu - facing * s * 0.38, cv - s * 0.2, s * 0.14, s * 0.06, n=12, rot=facing * 0.6)]
    head = ellipse(cu + facing * s * 0.6, cv + s * 0.02, s * 0.15, s * 0.11, n=16)
    plates = [ellipse(cu + dx * s, cv + dy * s, s * 0.11, s * 0.08, n=12) for dx, dy in ((0, 0), (-0.22, 0.1), (0.2, 0.1), (-0.22, -0.11), (0.2, -0.11))]
    return shell, flippers + [head], plates


def manta(cu, cv, s):
    return [(cu - s * 0.5, cv + s * 0.05), (cu - s * 0.15, cv + s * 0.12), (cu - s * 0.05, cv + s * 0.2), (cu + s * 0.05, cv + s * 0.2),
            (cu + s * 0.15, cv + s * 0.12), (cu + s * 0.5, cv + s * 0.05), (cu + s * 0.12, cv - s * 0.06), (cu + s * 0.02, cv - s * 0.12),
            (cu + s * 0.006, cv - s * 0.45), (cu - s * 0.006, cv - s * 0.45), (cu - s * 0.02, cv - s * 0.12), (cu - s * 0.12, cv - s * 0.06)]


def kelp(cu, base, h, sway=0.02):
    left, right = [], []
    for i in range(13):
        t = i / 12
        x = cu + sway * math.sin(t * 5.0)
        w = 0.004 * (1 - 0.5 * t) + 0.0025
        left.append((x - w, base + h * t)); right.append((x + w, base + h * t))
    return left + right[::-1]


def scene_reef_0():
    """Visit the reef: turtles, a manta, corals and fish."""
    t_shell, t_body, t_plates = turtle(0.05, 0.1, 0.08)
    l3 = [('#2e7d6b', kelp(-0.15, 0.0, 0.18)), ('#2e7d6b', kelp(-0.11, 0.0, 0.15, -0.015)), ('#2e7d6b', kelp(0.19, 0.0, 0.19)),
          ('#37474f', manta(-0.04, 0.16, 0.16)), ('#37474f', rect(-0.0416, 0.0, -0.0384, 0.13)),
          ('#c8a165', ridge(-0.24, 0.24, lambda u: 0.03 + 0.012 * math.cos(u * 30)))]
    l2 = [('#7cb342', t_body[0]), ('#7cb342', t_body[1]), ('#7cb342', t_body[2]), ('#7cb342', t_body[3]), ('#7cb342', t_body[4]),
          ('#5d7c2f', t_shell)] + [('#8bae4d', p) for p in t_plates] + [
          ('#5d7c2f', rect(0.048, 0.0, 0.052, 0.08)),
          ('#9575cd', coral_fan(-0.14, 0.0, 0.12, 0.1)), ('#ff8a65', rrect(0.16, 0.0, 0.18, 0.07, 0.008)),
          ('#ff8a65', rrect(0.185, 0.0, 0.205, 0.05, 0.008)), ('#d9b380', ridge(-0.24, 0.24, lambda u: 0.022 + 0.01 * math.cos(u * 22 + 1)))]
    l1 = [('#f06292', p) for p in coral_branch(-0.17, 0.0, 0.08, 0.1, 3)] + \
         [('#ffd54f', p) for p in coral_branch(0.13, 0.0, 0.07, 0.09, 7)] + \
         [('#ffb300', fish(-0.03, 0.055, 0.05, 1.0)), ('#4fc3f7', fish(0.05, 0.035, 0.035, -1.0)),
          ('#ffb300', rect(-0.0305, 0.0, -0.0285, 0.05)), ('#4fc3f7', rect(0.0495, 0.0, 0.051, 0.03)),
          ('#e6c88f', ridge(-0.24, 0.24, lambda u: 0.016 + 0.006 * math.cos(u * 40)))]
    return l3, l2, l1


def scene_reef_1():
    """Coral bleaching: the same reef, colourful on one side and white where the water stayed too warm."""
    l3 = [('#2e7d6b', kelp(-0.2, 0.0, 0.17)), ('#c8a165', ridge(-0.24, 0.24, lambda u: 0.03 + 0.01 * math.cos(u * 26)))]
    l3 += [('#ff8a65', p) for p in coral_branch(-0.1, 0.0, 0.15, 0.16, 11)] + [('#f4f1ea', p) for p in coral_branch(0.11, 0.0, 0.15, 0.16, 12)]
    l2 = [('#9575cd', coral_fan(-0.17, 0.0, 0.11, 0.1)), ('#f4f1ea', coral_fan(0.17, 0.0, 0.11, 0.1)),
          ('#d9b380', ridge(-0.24, 0.24, lambda u: 0.022 + 0.008 * math.cos(u * 20)))]
    l1 = [('#f06292', p) for p in coral_branch(-0.13, 0.0, 0.075, 0.1, 5)] + [('#efeae0', p) for p in coral_branch(0.13, 0.0, 0.075, 0.1, 6)] + \
         [('#ffb300', fish(-0.03, 0.05, 0.045, 1.0)), ('#ffb300', rect(-0.0305, 0.0, -0.0285, 0.045)),
          ('#e6c88f', ridge(-0.24, 0.24, lambda u: 0.015 + 0.006 * math.cos(u * 36)))]
    return l3, l2, l1


def person_back(cu, base, s):
    """Someone seen from behind wearing a headset: shoulders, neck, head, the strap and the visor's edges."""
    shoulders = [(cu - s * 0.5, base), (cu + s * 0.5, base), (cu + s * 0.46, base + s * 0.28), (cu + s * 0.3, base + s * 0.4),
                 (cu - s * 0.3, base + s * 0.4), (cu - s * 0.46, base + s * 0.28)]
    neck = rect(cu - s * 0.09, base + s * 0.36, cu + s * 0.09, base + s * 0.52)
    head = ellipse(cu, base + s * 0.68, s * 0.19, s * 0.23, n=28)
    strap = rrect(cu - s * 0.21, base + s * 0.62, cu + s * 0.21, base + s * 0.69, s * 0.03)
    visor = [rrect(cu - s * 0.27, base + s * 0.6, cu - s * 0.17, base + s * 0.73, s * 0.03),
             rrect(cu + s * 0.17, base + s * 0.6, cu + s * 0.27, base + s * 0.73, s * 0.03)]
    return shoulders, neck, head, strap, visor


def castle(cu, base, w, h):
    """(a crenellated wall, two towers with roofs, a keep with its roof)."""
    n = 9
    seg = w / n
    wall = [(cu - w / 2, base), (cu + w / 2, base)]
    for i in range(n):
        xr = cu + w / 2 - seg * i
        top = base + h * (0.63 if i % 2 == 0 else 0.55)
        wall += [(xr, top), (xr - seg, top)]
    towers = []
    for dx in (-w / 2, w / 2):
        towers.append(rect(cu + dx - w * 0.08, base, cu + dx + w * 0.08, base + h * 0.8))
        towers.append([(cu + dx - w * 0.11, base + h * 0.8), (cu + dx + w * 0.11, base + h * 0.8), (cu + dx, base + h)])
    keep = [rect(cu - w * 0.12, base, cu + w * 0.12, base + h * 0.95), [(cu - w * 0.15, base + h * 0.95), (cu + w * 0.15, base + h * 0.95), (cu, base + h * 1.2)]]
    return wall, towers, keep


def scene_xr_1():
    """Virtual reality: a reader in a headset looking into a made-up world of floating islands and a castle."""
    wall, towers, keep = castle(0.08, 0.1, 0.16, 0.08)
    l3 = [('#7e57c2', peaks(-0.24, 0.24, 0.07, [(-0.16, 0.16), (-0.04, 0.12), (0.18, 0.14)])),
          ('#8bc34a', hills(-0.02, 0.2, 0.1, 0.006, 0.6)), ('#cfd8dc', wall)] + [('#cfd8dc', t) for t in towers[0::2]] + \
         [('#e57373', t) for t in towers[1::2]] + [('#b0bec5', keep[0]), ('#e57373', keep[1])]
    island = [(-0.16, 0.1), (-0.06, 0.1), (-0.08, 0.07), (-0.11, 0.05), (-0.13, 0.07)]
    l2 = [('#6d4c41', island), ('#8bc34a', rrect(-0.165, 0.098, -0.055, 0.11, 0.005)),
          ('#558b2f', round_tree(-0.11, 0.105, 0.04, 0.035)[1]), ('#6d4c41', rect(-0.112, 0.0, -0.108, 0.06)),
          ('#5e35b1', hills(-0.24, 0.24, 0.045, 0.025, 1.4, 2.4))]
    sh, nk, hd, st, vz = person_back(0.0, 0.0, 0.095)
    l1 = [('#3949ab', sh), ('#d7a17a', nk), ('#4e342e', hd), ('#263238', st)] + [('#263238', v) for v in vz]
    return l3, l2, l1


def dino(cu, base, s, facing=1.0):
    """A friendly T. rex in profile, facing +u (facing 1) or -u."""
    outline = [(-0.02, 0.0), (0.06, 0.0), (0.07, 0.1), (0.12, 0.1), (0.13, 0.0), (0.21, 0.0), (0.22, 0.08), (0.3, 0.16), (0.36, 0.3),
               (0.38, 0.42), (0.47, 0.48), (0.58, 0.47), (0.61, 0.41), (0.56, 0.36), (0.47, 0.35), (0.45, 0.3), (0.4, 0.29),
               (0.41, 0.24), (0.36, 0.26), (0.31, 0.2), (0.26, 0.18), (0.16, 0.24), (0.04, 0.24), (-0.1, 0.22), (-0.34, 0.27),
               (-0.12, 0.13)]
    return [(cu + facing * x * s, base + y * s) for (x, y) in outline]


def scene_xr_2():
    """Augmented and mixed reality: a dinosaur in the living room, seen through a phone."""
    sofa = [rrect(-0.2, 0.0, 0.0, 0.07, 0.012), rrect(-0.215, 0.0, -0.185, 0.085, 0.01), rrect(-0.015, 0.0, 0.015, 0.085, 0.01),
            rrect(-0.19, 0.06, -0.01, 0.12, 0.015)]
    lamp = [rect(0.15, 0.0, 0.154, 0.15), [(0.12, 0.15), (0.184, 0.15), (0.172, 0.19), (0.132, 0.19)], rect(0.135, 0.0, 0.17, 0.006)]
    l3 = [('#8e5a4a', p) for p in sofa] + [('#455a64', lamp[0]), ('#ffe082', lamp[1]), ('#455a64', lamp[2]),
                                           ('#c9a27a', rect(-0.24, 0.0, 0.24, 0.01))]
    l2 = [('#66bb6a', dino(0.02, 0.006, 0.22, -1.0)), ('#43a047', ridge(-0.24, 0.24, lambda u: 0.006))]
    phone = rrect(0.05, 0.02, 0.105, 0.088, 0.008)
    screen = rrect(0.055, 0.027, 0.1, 0.082, 0.004)
    hand = [(0.04, 0.0), (0.12, 0.0), (0.118, 0.03), (0.11, 0.05), (0.1, 0.035), (0.06, 0.035), (0.045, 0.05), (0.035, 0.03)]
    l1 = [('#263238', phone), ('#9fd3ea', screen), ('#66bb6a', dino(0.083, 0.033, 0.045, -1.0)), ('#e0a77e', hand)]
    return l3, l2, l1


def scene_fair_2():
    """Pollinators at the fair: a striped booth, flowers, monarchs drifting between them."""
    tent = [rect(-0.2, 0.0, -0.02, 0.12), [(-0.215, 0.12), (-0.005, 0.12), (-0.11, 0.19)]]
    stripes = [rect(-0.2 + 0.036 * k, 0.0, -0.2 + 0.036 * k + 0.018, 0.12) for k in range(5)]
    l3 = [('#fafafa', tent[0])] + [('#e53935', s) for s in stripes] + [('#e53935', tent[1]),
          ('#fdd835', [(-0.112, 0.185), (-0.108, 0.185), (-0.108, 0.203), (-0.084, 0.197), (-0.108, 0.19)]),
          ('#7cb342', hills(-0.24, 0.24, 0.025, 0.012, 1.5, 0.3)), ('#33691e', pine(0.15, 0.0, 0.16, 0.08)),
          ('#558b2f', round_tree(0.07, 0.0, 0.13, 0.08)[1]), ('#6d4c41', round_tree(0.07, 0.0, 0.13, 0.08)[0])]
    l2 = []
    for (cu, h, r, col) in ((-0.17, 0.09, 0.022, '#ff7043'), (-0.08, 0.11, 0.026, '#ec407a'), (0.02, 0.085, 0.022, '#ab47bc'),
                            (0.11, 0.1, 0.026, '#ffca28'), (0.19, 0.08, 0.02, '#ff7043')):
        stem, head, eye, leaf = flower(cu, 0.0, h, r)
        l2 += [('#558b2f', stem), ('#558b2f', leaf), (col, head), ('#5d4037', eye)]
    l2.append(('#689f38', ridge(-0.24, 0.24, lambda u: 0.012 + 0.006 * math.cos(u * 30))))
    l1 = []
    for (cu, h, r, col) in ((-0.12, 0.05, 0.018, '#ffca28'), (0.06, 0.045, 0.016, '#ec407a')):
        stem, head, eye, leaf = flower(cu, 0.0, h, r)
        l1 += [('#558b2f', stem), (col, head), ('#5d4037', eye)]
    for (cu, cv, s, stem_u) in ((-0.04, 0.07, 0.03, -0.04), (0.15, 0.06, 0.026, 0.15)):
        wing_polys, body = wings(cu, cv, s)
        l1 += [('#212121', scaled(w, 1.12, cu, cv)) for w in wing_polys] + [('#fb8c00', w) for w in wing_polys] + [('#212121', body)]
        l1.append(('#cfd8dc', rect(stem_u - 0.0008, 0.0, stem_u + 0.0008, cv - s * 0.35)))       # a clear stalk, as pop-ups use
    l1.append(('#7cb342', ridge(-0.24, 0.24, lambda u: 0.01 + 0.005 * math.cos(u * 44))))
    return l3, l2, l1


# Books, in the order the table offers them; each spread names the DT_Books page it shows.
BOOKS = [
    ('water-cycle', 'The Water Cycle', '#1f6f7a', [(0, scene_water_0), (1, scene_water_1), (2, scene_water_2), (3, scene_water_3)]),
    ('oceans-vr', 'Oceans in VR', '#1f5f8b', [(0, scene_reef_0), (1, scene_reef_1)]),
    ('what-is-xr', 'What Is XR?', '#2c3e7a', [(1, scene_xr_1), (2, scene_xr_2)]),
    ('ar-around-town', 'AR Around Town', '#7a2c4a', [(2, scene_fair_2)]),
]


# ---------------------------------------------------------------- printed pages (PIL)
def font(names, size):
    from PIL import ImageFont
    for n in names:
        for p in (os.path.join(FONTS, n), '/usr/share/fonts/opentype/inter/' + n, '/usr/share/fonts/truetype/dejavu/' + n):
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def language():
    """The pack's language (WTA_LANG, which build_client.py sets, else the pack's own "language")."""
    return (os.environ.get('WTA_LANG') or clientpack.get('language') or 'en').strip().lower()


def words(english):
    """lang/<lang>/builders.json's words for what this builder prints itself (English when it has none)."""
    p = os.path.join(LANG_DIR, language(), 'builders.json')
    if language() == 'en' or not os.path.exists(p):
        return english
    with open(p, 'r', encoding='utf-8') as fh:
        return json.load(fh).get(english, english)


def book_pages(book_id):
    """(title, page headings) of a book in the pack's books.json, in the pack's language when it has one
    (lang/<lang>/tables.json DT_Books); None when the pack has no such book (its pop-up is then not built)."""
    with open(os.path.join(CONTENT, 'books.json'), encoding='utf-8') as fh:
        books = json.load(fh)
    for bk in books:
        if bk.get('id') == book_id:
            heads = [p.get('h', '') for p in bk.get('pages', [])]
            title = bk.get('title', book_id)
            break
    else:
        return None
    lang = language()
    p = os.path.join(LANG_DIR, lang, 'tables.json')
    if lang != 'en' and os.path.exists(p):
        with open(p, encoding='utf-8') as fh:
            row = json.load(fh).get('DT_Books', {}).get(book_id, {})
        title = row.get('Title', title)
        for i, page in enumerate(row.get('Pages', [])):
            if i < len(heads) and page.get('Heading'):
                heads[i] = page['Heading']
    return title, heads


TW, TH = 1280, 690                # the printed pages, the near page's and the backdrop's proportions (0.52 x 0.28)


def hexrgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def gradient(im, top, bottom, y0=0, y1=None):
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    y1 = im.size[1] if y1 is None else y1
    a, b = hexrgb(top), hexrgb(bottom)
    for y in range(y0, y1):
        t = (y - y0) / max(1, (y1 - y0 - 1))
        d.line((0, y, im.size[0], y), fill=tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3)))


def paper_grain(im, seed, amount=6):
    import random
    from PIL import Image
    r = random.Random(seed)
    noise = Image.effect_noise(im.size, 18).convert('L')
    px = Image.merge('RGB', (noise, noise, noise))
    return Image.blend(im, Image.composite(im, px, Image.new('L', im.size, 255 - amount)), 0.5) if amount else im


BACKDROPS = {
    # sky top, sky bottom, extra printing
    'water-cycle_0': ('#8fcbe8', '#d9f0f7', 'sun'),
    'water-cycle_1': ('#8fcbe8', '#e3f3f7', 'sun_vapour'),
    'water-cycle_2': ('#9cbfd8', '#e6eff5', 'vapour'),
    'water-cycle_3': ('#7f93a8', '#c9d6df', 'rain'),
    'oceans-vr_0': ('#1d6fa3', '#7cc6df', 'rays'),
    'oceans-vr_1': ('#2a7fb0', '#9fd4e3', 'rays_warm'),
    'what-is-xr_1': ('#2b1d5c', '#7c5cc4', 'stars'),
    'what-is-xr_2': ('#e8dcc8', '#d9c7aa', 'room'),
    'ar-around-town_2': ('#8fd0ee', '#e4f5fb', 'fair'),
}
FLOORS = {
    'water-cycle_0': '#2b7fb3', 'water-cycle_1': '#3a8fbf', 'water-cycle_2': '#4a9a5c', 'water-cycle_3': '#3d7f4a',
    'oceans-vr_0': '#d8bf8a', 'oceans-vr_1': '#d8bf8a', 'what-is-xr_1': '#4a3a8a', 'what-is-xr_2': '#b07a52',
    'ar-around-town_2': '#6aa84f',
}


def paint_backdrop(key, path):
    from PIL import Image, ImageDraw
    top, bottom, extra = BACKDROPS[key]
    im = Image.new('RGB', (TW, TH)); gradient(im, top, bottom)
    d = ImageDraw.Draw(im, 'RGBA')
    import random
    r = random.Random(hash(key) & 0xffff)
    if extra.startswith('sun'):
        cx, cy, rad = int(TW * 0.8), int(TH * 0.22), int(TW * 0.06)
        for k in range(16):
            a = 2 * math.pi * k / 16
            d.polygon([(cx + math.cos(a - 0.08) * (rad + 14), cy + math.sin(a - 0.08) * (rad + 14)),
                       (cx + math.cos(a) * (rad + 70), cy + math.sin(a) * (rad + 70)),
                       (cx + math.cos(a + 0.08) * (rad + 14), cy + math.sin(a + 0.08) * (rad + 14))], fill=(255, 202, 40, 255))
        d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=(255, 213, 79, 255), outline=(255, 160, 0, 255), width=8)
        if extra == 'sun_vapour':
            for k in range(7):
                x0 = int(TW * (0.12 + 0.1 * k)); y = TH * 0.85
                pts = [(x0 + 22 * math.sin(t / 7.0), y - t * 9) for t in range(50)]
                d.line(pts, fill=(255, 255, 255, 150), width=7, joint='curve')
    if extra == 'vapour':
        # wisps rising from the lake and curling into the cloud base, in the gaps the paper leaves
        for k, x0 in enumerate((0.06, 0.13, 0.86, 0.93)):
            x0 = int(TW * x0); y = TH * 0.95
            pts = [(x0 + 18 * math.sin(t / 6.0 + k), y - t * 11) for t in range(46)]
            d.line(pts, fill=(255, 255, 255, 170), width=7, joint='curve')
    if extra == 'rain':
        d.ellipse((int(TW * 0.1), int(TH * 0.02), int(TW * 0.62), int(TH * 0.3)), fill=(110, 124, 140, 255))
        d.ellipse((int(TW * 0.4), int(TH * 0.0), int(TW * 0.9), int(TH * 0.26)), fill=(98, 112, 128, 255))
        for k in range(150):
            x = r.uniform(TW * 0.08, TW * 0.92); y = r.uniform(TH * 0.28, TH * 0.95)
            d.line((x, y, x - 10, y + 34), fill=(225, 235, 245, 200), width=4)
    if extra.startswith('rays'):
        for k in range(6):
            x = TW * (0.1 + 0.16 * k)
            d.polygon([(x, 0), (x + 70, 0), (x + 230, TH), (x + 120, TH)], fill=(255, 255, 255, 34))
        for k in range(9):
            fx, fy, s = r.uniform(80, TW - 80), r.uniform(TH * 0.15, TH * 0.6), r.uniform(16, 30)
            col = (20, 70, 110, 140)
            d.ellipse((fx - s, fy - s * 0.45, fx + s, fy + s * 0.45), fill=col)
            d.polygon([(fx - s * 0.9, fy), (fx - s * 1.6, fy - s * 0.5), (fx - s * 1.6, fy + s * 0.5)], fill=col)
    if extra == 'stars':
        for k in range(160):
            x, y, s = r.uniform(0, TW), r.uniform(0, TH * 0.8), r.uniform(1.5, 4.5)
            d.ellipse((x - s, y - s, x + s, y + s), fill=(255, 250, 220, 230))
        d.ellipse((int(TW * 0.74), int(TH * 0.1), int(TW * 0.74) + 150, int(TH * 0.1) + 150), fill=(255, 183, 77, 255))
        d.ellipse((int(TW * 0.7), int(TH * 0.1) + 58, int(TW * 0.74) + 210, int(TH * 0.1) + 92), outline=(255, 236, 179, 255), width=10)
        d.ellipse((int(TW * 0.12), int(TH * 0.12), int(TW * 0.12) + 70, int(TH * 0.12) + 70), fill=(129, 212, 250, 255))
    if extra == 'room':
        for k in range(0, TW, 96):
            d.rectangle((k, 0, k + 48, TH), fill=(255, 255, 255, 26))
        wx0, wy0 = int(TW * 0.36), int(TH * 0.12)
        d.rectangle((wx0, wy0, wx0 + 380, wy0 + 300), fill=(143, 203, 232, 255), outline=(255, 255, 255, 255), width=18)
        d.line((wx0 + 190, wy0, wx0 + 190, wy0 + 300), fill=(255, 255, 255, 255), width=12)
        d.line((wx0, wy0 + 150, wx0 + 380, wy0 + 150), fill=(255, 255, 255, 255), width=12)
        d.rectangle((int(TW * 0.08), int(TH * 0.16), int(TW * 0.08) + 200, int(TH * 0.16) + 150), fill=(255, 224, 178, 255), outline=(121, 85, 72, 255), width=14)
        d.polygon([(int(TW * 0.08) + 30, int(TH * 0.16) + 130), (int(TW * 0.08) + 100, int(TH * 0.16) + 50), (int(TW * 0.08) + 170, int(TH * 0.16) + 130)], fill=(102, 187, 106, 255))
    if extra == 'fair':
        for k in range(3):
            x = int(TW * (0.08 + 0.13 * k)); y = int(TH * 0.55)
            d.polygon([(x, y), (x + 150, y), (x + 75, y - 110)], fill=(255, 138, 101, 210))
            d.rectangle((x + 10, y, x + 140, y + 120), fill=(255, 241, 224, 210))
        cx, cy, rad = int(TW * 0.62), int(TH * 0.42), 210
        d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), outline=(120, 144, 156, 230), width=10)
        for k in range(12):
            a = 2 * math.pi * k / 12
            d.line((cx, cy, cx + math.cos(a) * rad, cy + math.sin(a) * rad), fill=(120, 144, 156, 200), width=5)
            d.ellipse((cx + math.cos(a) * rad - 18, cy + math.sin(a) * rad - 18, cx + math.cos(a) * rad + 18, cy + math.sin(a) * rad + 18),
                      fill=[(229, 57, 53, 255), (253, 216, 53, 255), (30, 136, 229, 255)][k % 3])
        d.polygon([(cx - 60, TH), (cx, cy), (cx + 60, TH)], outline=(120, 144, 156, 255), width=10)
    im = paper_grain(im, len(key))
    im.save(path)


def paint_floor(key, n, total, heading, path):
    from PIL import Image, ImageDraw
    base = FLOORS[key]
    im = Image.new('RGB', (TW, TH), hexrgb(base)); d = ImageDraw.Draw(im, 'RGBA')
    import random
    r = random.Random(len(key) * 7 + n)
    # a little texture in the ground or water: darker dabs and lighter streaks
    for k in range(260):
        x, y = r.uniform(0, TW), r.uniform(0, TH * 0.7)
        w = r.uniform(20, 90)
        d.ellipse((x - w, y - w * 0.2, x + w, y + w * 0.2), fill=(255, 255, 255, 14) if k % 2 else (0, 0, 0, 16))
    # the caption band along the reader's edge (the image's bottom), cream paper with a brass rule
    band = int(TH * 0.3)
    d.rectangle((0, TH - band, TW, TH), fill=(246, 239, 222, 255))
    d.line((60, TH - band + 18, TW - 60, TH - band + 18), fill=(190, 150, 80, 255), width=5)
    f = font(['CormorantGaramond-Bold.ttf'], 108)
    while d.textlength(heading, font=f) > TW - 220 and f.size > 40:
        f = font(['CormorantGaramond-Bold.ttf'], f.size - 6)
    w = d.textlength(heading, font=f)
    d.text(((TW - w) / 2, TH - band + 40), heading, font=f, fill=(40, 34, 26, 255))
    pg = '%d / %d' % (n + 1, total)
    f2 = font(['CormorantGaramond-MediumItalic.ttf'], 56)
    d.text((TW - 80 - d.textlength(pg, font=f2), TH - 82), pg, font=f2, fill=(110, 90, 60, 255))
    im = paper_grain(im, n)
    im.save(path)


def paint_cover(book_id, title, colour, path):
    from PIL import Image, ImageDraw
    im = Image.new('RGB', (TW, TH), hexrgb(colour)); d = ImageDraw.Draw(im, 'RGBA')
    d.rectangle((36, 36, TW - 37, TH - 37), outline=(214, 180, 106, 255), width=10)
    d.rectangle((62, 62, TW - 63, TH - 63), outline=(214, 180, 106, 160), width=3)
    f = font(['CormorantGaramond-Bold.ttf'], 150)
    while d.textlength(title, font=f) > TW - 260 and f.size > 60:
        f = font(['CormorantGaramond-Bold.ttf'], f.size - 8)
    w = d.textlength(title, font=f)
    d.text(((TW - w) / 2, TH * 0.28), title, font=f, fill=(246, 239, 222, 255))
    k = words('A POP-UP BOOK')
    fk = font(['Cinzel.ttf'], 54)
    while sum(d.textlength(ch, font=fk) for ch in k) + 12 * (len(k) - 1) > TW - 200 and fk.size > 30:
        fk = font(['Cinzel.ttf'], fk.size - 4)
    tw = sum(d.textlength(ch, font=fk) for ch in k) + 12 * (len(k) - 1)
    x = (TW - tw) / 2
    for ch in k:
        d.text((x, TH * 0.62), ch, font=fk, fill=(214, 180, 106, 255)); x += d.textlength(ch, font=fk) + 12
    im.save(path)


# ---------------------------------------------------------------- building a book
def ensure_materials(colours):
    material('pp_board', color=srgb('#efe6d2'), roughness=0.85)        # the boards' edges, the page block
    material('pp_base', color=srgb('#5a4632'), roughness=0.7)          # the back cover's cloth
    for c in colours:
        material('pp_' + c.lstrip('#'), color=srgb(c), roughness=0.88)


def textured(name, tex):
    if name not in MATS:
        material(name, col=tex, roughness=0.85)
    return name


def build_base():
    p = Part('popup__base')
    x0, x1 = BX - PAGE_W / 2 - 0.006, BX + PAGE_W / 2 + 0.006
    z0, z1 = SPINE_Z - 0.006, SPINE_Z + PAGE_D + 0.006
    p.box(((x0 + x1) / 2, TOP + 0.0015, (z0 + z1) / 2), (x1 - x0, 0.003, z1 - z0), 'pp_base')
    p.box(((x0 + x1) / 2, TOP + 0.003 + (BASE_T - 0.003) / 2, (z0 + z1) / 2 - 0.002), (PAGE_W, BASE_T - 0.003, PAGE_D), 'pp_board', faces='xXzZ')
    p.box((BX, FLOOR_Y - 0.0005, SPINE_Z + PAGE_D / 2), (PAGE_W, 0.001, PAGE_D), 'pp_board', faces='Y')
    # a cloth spine along the fold
    p.box((BX, TOP + BASE_T / 2, SPINE_Z - 0.006), (PAGE_W + 0.012, BASE_T, 0.008), 'pp_base', faces='xXyYz')
    return p.finish()


def build_spread(book_id, n, total, page_index, scene, title, heads, colour_cover):
    key = '%s_%d' % (book_id, page_index)
    tag = 'popup__%s_s%d' % (book_id, n)
    l3, l2, l1 = scene()
    ensure_materials(sorted({c for layer in (l3, l2, l1) for c, _ in layer}))
    # the printed pages
    back_png = 'popup_back_%s_s%d' % (book_id, n)
    floor_png = 'popup_floor_%s_s%d' % (book_id, n)
    cover_png = 'popup_cover_%s' % book_id
    paint_backdrop(key, os.path.join(TEX, back_png + '.png'))
    paint_floor(key, n, total, heads[page_index] if page_index < len(heads) else title, os.path.join(TEX, floor_png + '.png'))
    if not os.path.exists(os.path.join(TEX, cover_png + '.png')) or n == 0:
        paint_cover(book_id, title, colour_cover, os.path.join(TEX, cover_png + '.png'))
    textured('pp_' + back_png, back_png); textured('pp_' + floor_png, floor_png); textured('pp_' + cover_png, cover_png)
    obs = []
    # the backdrop: a board standing on the spine, its art toward the reader and the cover behind
    b = Part(tag + '_back')
    x0, x1 = BX - PAGE_W / 2, BX + PAGE_W / 2
    y0, y1 = HINGE_Y, HINGE_Y + PAGE_D
    zi, zo = SPINE_Z + BOARD_T / 2, SPINE_Z - BOARD_T / 2
    b.poly([(x0, y0, zi), (x1, y0, zi), (x1, y1, zi), (x0, y1, zi)], (0, 0, 1), 'pp_' + back_png,
           uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    b.poly([(x0, y0, zo), (x0, y1, zo), (x1, y1, zo), (x1, y0, zo)], (0, 0, -1), 'pp_' + cover_png,
           uvs=[(0, 1), (0, 0), (1, 0), (1, 1)])                     # the cover reads from the reader's side once closed
    b.box((BX, (y0 + y1) / 2, SPINE_Z), (PAGE_W, PAGE_D, BOARD_T), 'pp_board', faces='xXyY')
    obs.append(b.finish())
    # the near page's print
    f = Part(tag + '_floor')
    zn = SPINE_Z + PAGE_D
    f.poly([(x0, FLOOR_Y + 0.0004, zn), (x1, FLOOR_Y + 0.0004, zn), (x1, FLOOR_Y + 0.0004, SPINE_Z), (x0, FLOOR_Y + 0.0004, SPINE_Z)],
           (0, 1, 0), 'pp_' + floor_png, uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    obs.append(f.finish())
    # the layers, front (l1) to back (l3); the pieces of one layer step 0.35 mm toward the reader in the order listed
    for k, layer in enumerate((l1, l2, l3)):
        dz, h = LAYERS[k]
        part = Part('%s_l%d' % (tag, k + 1))
        O = (BX, FLOOR_Y + 0.0012, SPINE_Z + dz)
        frame = (O, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
        clipped = 0
        for i, (colour, poly) in enumerate(layer):
            top = max(v for _, v in poly)
            if top > h + 0.002:
                clipped += 1
            Oi = (O[0], O[1], O[2] + i * 0.00035)
            part.prism(poly, (Oi, frame[1], frame[2], frame[3]), PAPER_T, 'pp_' + colour.lstrip('#'))
        if clipped:
            print('  %s_l%d: %d pieces taller than the %.3f m the fold allows' % (tag, k + 1, clipped, h), flush=True)
        obs.append(part.finish())
    return obs


def write_layout(books):
    ue = lambda x, y, z: [round(x * 100, 2), round(z * 100, 2), round(y * 100, 2)]
    layout = {
        'source': 'bl/popup.py', 'units': 'campus metres; ue = Unreal cm (x*100, z*100, y*100)',
        'book': {'centre': [BX, FLOOR_Y, SPINE_Z + PAGE_D / 2], 'centre_ue': ue(BX, FLOOR_Y, SPINE_Z + PAGE_D / 2),
                 'spine_ue': ue(BX, HINGE_Y, SPINE_Z), 'reader_ue': [0.0, 1.0, 0.0], 'width_m': PAGE_W, 'depth_m': PAGE_D,
                 'height_m': PAGE_D},
        'reader_seat': READER_SEAT,
        'books': [{'id': bid, 'title': title, 'pages': [p for p, _ in spreads]} for (bid, title, _c, spreads) in books],
    }
    with open(os.path.join(PIPE, 'layout.json'), 'w') as fh:
        json.dump(layout, fh, indent=1)


def export_glb():
    obs = [o for o in bpy.data.objects if o.type == 'MESH' and not o.get('preview_only')]
    select_only(obs)
    fp = os.path.join(PIPE, 'PopUp.glb')
    bpy.ops.export_scene.gltf(filepath=fp, export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
                              export_texcoords=True, export_normals=True, export_tangents=True, export_materials='EXPORT',
                              export_image_format='JPEG', export_jpeg_quality=92, export_vertex_color='NONE',
                              export_lights=False, export_cameras=False)
    print('exported', fp, os.path.getsize(fp), 'bytes', flush=True)


def preview(objs_by_spread):
    sc = bpy.context.scene
    # a table top and the lamps' warm light, for the previews only
    tb = Part('preview_table'); material('pv_oak', color=srgb('#8a6a48'), roughness=0.5)
    tb.box((BX, TOP - 0.03, 4.6), (1.6, 0.06, 1.1), 'pv_oak'); t = tb.finish(); t['preview_only'] = 1
    for (x, z, e) in ((BX - 0.65, 4.6, 25), (BX + 0.65, 4.6, 25), (BX, 5.6, 60)):
        ld = bpy.data.lights.new('pv', 'POINT'); ld.energy = e; ld.color = (1.0, 0.85, 0.65); ld.shadow_soft_size = 0.1
        ob = bpy.data.objects.new('pv', ld); ob.location = P(x, TOP + 0.4 if e < 50 else 2.2, z); ob['preview_only'] = 1
        sc.collection.objects.link(ob)
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.3, 0.27, 0.23, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.5
    cam = bpy.data.cameras.new('C'); cam.lens_unit = 'FOV'; cam.angle = math.radians(44)
    co = bpy.data.objects.new('C', cam); sc.collection.objects.link(co); sc.camera = co
    eye = P(BX + 0.02, FLOOR_Y + 0.33, SPINE_Z + 0.72); tgt = P(BX, FLOOR_Y + 0.11, SPINE_Z + 0.08)
    co.location = eye; co.rotation_euler = (tgt - eye).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x = 960; sc.render.resolution_y = 600; sc.render.resolution_percentage = 100
    sc.cycles.samples = 16 if QUICK else 48
    sc.render.image_settings.file_format = 'JPEG'
    base = bpy.data.objects.get('popup__base')
    for key, obs in objs_by_spread.items():
        for o in bpy.data.objects:
            if o.name.startswith('popup__') and o is not base:
                o.hide_render = o not in obs
        sc.render.filepath = os.path.join(OUT, 'preview_%s.jpg' % key)
        t0 = time.time(); bpy.ops.render.render(write_still=True)
        print('preview', key, '%.0f s' % (time.time() - t0), flush=True)


def main():
    t0 = time.time()
    L.reset()
    ensure_materials([])
    build_base()
    by_spread = {}
    count = 0
    built = []
    for (book_id, title_en, colour, spreads) in BOOKS:
        found = book_pages(book_id)
        if found is None:
            print('  %s: not in %s, so no pop-up of it' % (book_id, os.path.join(CONTENT, 'books.json')), flush=True)
            continue
        title, heads = found
        for n, (page, scene) in enumerate(spreads):
            obs = build_spread(book_id, n, len(spreads), page, scene, title, heads, colour)
            by_spread['%s_s%d' % (book_id, n)] = obs
            count += len(obs)
        built.append((book_id, title, colour, spreads))
    write_layout(built)
    if not built:
        # A pack without these books: an empty layout tells the actors step there is no pop-up book to place.
        stale = os.path.join(PIPE, 'PopUp.glb')
        if os.path.exists(stale):
            os.remove(stale)
        print('no pop-up books for this pack', flush=True)
        return
    for o in bpy.data.objects:
        if o.type == 'MESH':
            o.data.calc_loop_triangles()
    tris = sum(len(o.data.loop_triangles) for o in bpy.data.objects if o.type == 'MESH')
    print('built %d meshes, %d triangles in %.1f s' % (count + 1, tris, time.time() - t0), flush=True)
    export_glb()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'popup.blend'))
    if RENDER:
        want = {k: v for k, v in by_spread.items() if not ONLY or any(k.startswith(o) for o in ONLY)}
        preview(want)
    print('done in %.0f s' % (time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
