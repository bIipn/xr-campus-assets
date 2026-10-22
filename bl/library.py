"""The Reading Room, built for real: Blender (bpy) scene of the campus library at campus coordinates,
baked in Cycles, exported as glTF for the web campus.

Campus axes: x right, y up, z toward the viewer.  Blender: X = x, Y = -z, Z = y.
Room: x -32..-12, z -13..7, height 7.6. Door on the east wall (x=-12) at z -4.6..-1.4, 3.4 high.
Arched window on the west wall (x=-32) at z -5.2..-0.8, y 1.0..4.6 plus a half circle.

Usage: bl/bin/python bl/library.py [--quick] [--nobake] [--render] [--ue]
Outputs assets/lib/: lib_raw.gltf (+bin, textures), lightmap.exr, probe.hdr, preview renders.
--ue builds the Unreal Engine version instead (assets/lib_ue/library.blend, no bake): real books on every
shelf tier (no textured strips) and 0.45 m thick walls, floor and ceiling so Lumen sees a closed room.
"""
import bpy, bmesh, math, os, sys, time, json, random
from mathutils import Vector, Matrix
try:
    import numpy as np            # Blender's bundled numpy
except ImportError:               # some machines block its DLLs (Windows Application Control); only baking needs it
    np = None

def frange(a, b, step):
    """numpy-free arange: a, a+step, ... while below b."""
    out, x = [], a
    while x < b - 1e-9:
        out.append(x); x += step
    return out

SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(SP, 'assets', 'tex')
UE = '--ue' in sys.argv
OUT = os.path.join(SP, 'assets', 'lib_ue' if UE else 'lib')
os.makedirs(OUT, exist_ok=True)
QUICK = '--quick' in sys.argv
NOBAKE = '--nobake' in sys.argv or UE
RENDER = '--render' in sys.argv
LM_SIZE = 1024 if QUICK else 2048
SAMPLES_LM = 32 if QUICK else 160
SAMPLES_VC = 24 if QUICK else 128
VC_SCALE = 4.0     # vertex colors store irradiance / VC_SCALE (glTF COLOR_0 is 0..1)
rnd = random.Random(4242)

# campus -> blender
def P(x, y, z): return Vector((x, -z, y))
def D(dx, dy, dz): return Vector((dx, -dz, dy))   # the same mapping for a direction (no translation)

# ---------------------------------------------------------------- geometry helpers
# Builder.box covers anything axis-aligned with a yaw. These four cover what it cannot:
# bars that lean or spiral, round posts, turned balusters and curved outlines like a piano case.
def bar(b, a, c, w, h=None, caps=True):
    """A rectangular-section bar between two campus points a and c (x, y, z), section w x (h or w).
    The section stays upright (campus +y) except where the bar itself is near vertical."""
    A, C = P(*a), P(*c)
    ax = C - A; L = ax.length
    if L < 1e-7: return
    ax = ax / L
    up = Vector((0.0, 0.0, 1.0))
    if abs(ax.dot(up)) > 0.98: up = Vector((0.0, 1.0, 0.0))
    side = ax.cross(up).normalized(); sup = side.cross(ax).normalized()
    hw, hh = w / 2, (h if h is not None else w) / 2
    sec = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    r0 = [A + side * u + sup * v for (u, v) in sec]
    r1 = [C + side * u + sup * v for (u, v) in sec]
    for i in range(4):
        j = (i + 1) % 4
        n = side * (sec[i][0] + sec[j][0]) + sup * (sec[i][1] + sec[j][1])
        b.face([r0[i], r0[j], r1[j], r1[i]], n.normalized())
    if caps:
        b.face([r0[3], r0[2], r0[1], r0[0]], -ax)
        b.face([r1[0], r1[1], r1[2], r1[3]], ax)

def prism(b, cx, cy, cz, r, h, n=12, r_top=None, cap_top=True, cap_bot=True, a0=0.0):
    """An n-sided prism standing on y = cy: a round post, or a cone/vase segment when r_top differs."""
    rt = r if r_top is None else r_top
    ring = [a0 + 2 * math.pi * i / n for i in range(n)]
    low = [P(cx + r * math.cos(a), cy, cz + r * math.sin(a)) for a in ring]
    top = [P(cx + rt * math.cos(a), cy + h, cz + rt * math.sin(a)) for a in ring]
    for i in range(n):
        j = (i + 1) % n; am = (ring[i] + ring[j]) / 2
        b.face([low[i], low[j], top[j], top[i]], D(math.cos(am), 0, math.sin(am)))
    if cap_top:
        cen = P(cx, cy + h, cz)
        for i in range(n): b.face([cen, top[i], top[(i + 1) % n]], D(0, 1, 0))
    if cap_bot:
        cen = P(cx, cy, cz)
        for i in range(n): b.face([cen, low[(i + 1) % n], low[i]], D(0, -1, 0))

# a turned baluster's radius profile: (height fraction, width fraction) - square base, swell, neck, cap
BALUSTER = [(0.00, 1.00), (0.10, 1.00), (0.14, 0.74), (0.34, 1.00), (0.58, 0.64), (0.78, 0.76), (0.90, 0.60), (1.00, 0.88)]
def turned(b, cx, cy, cz, h, w, n=6, prof=None):
    """A turned baluster h tall and w across at its widest, as a stack of prism segments."""
    prof = prof or BALUSTER
    for (t0, s0), (t1, s1) in zip(prof, prof[1:]):
        if t1 <= t0: continue
        prism(b, cx, cy + h * t0, cz, w * s0 / 2, h * (t1 - t0), n=n, r_top=w * s1 / 2, cap_top=False, cap_bot=False)

def sweep(b, pts, prof, cap_start=True, cap_end=True):
    """One continuous bar along the campus polyline pts (x, y, z) with the section prof, a closed outline of
    (side, up) offsets in metres, counter-clockwise seen from the far end. The section stays upright, so a
    handrail keeps its flat underside level as it climbs and turns; there is no joint anywhere along it."""
    up = Vector((0.0, 0.0, 1.0))
    rings, centres = [], []
    n = len(pts)
    for i, p in enumerate(pts):
        a = P(*pts[max(i - 1, 0)]); c = P(*pts[min(i + 1, n - 1)])
        t = c - a
        if t.length < 1e-9: continue
        t.normalize()
        if abs(t.dot(up)) > 0.98: side = t.cross(Vector((0.0, 1.0, 0.0))).normalized()
        else: side = t.cross(up).normalized()
        sup = side.cross(t).normalized()
        o = P(*p)
        centres.append(o)
        rings.append([o + side * u + sup * v for (u, v) in prof])
    m = len(prof)
    for k, (r0, r1) in enumerate(zip(rings, rings[1:])):
        for i in range(m):
            j = (i + 1) % m
            mid = (r0[i] + r0[j] + r1[i] + r1[j]) / 4
            b.face([r0[i], r0[j], r1[j], r1[i]], (mid - (centres[k] + centres[k + 1]) / 2).normalized())
    if rings and cap_start:
        t = (centres[1] - centres[0]).normalized() if len(centres) > 1 else up
        for i in range(1, m - 1): b.face([rings[0][0], rings[0][i + 1], rings[0][i]], -t)
    if rings and cap_end:
        t = (centres[-1] - centres[-2]).normalized() if len(centres) > 1 else up
        for i in range(1, m - 1): b.face([rings[-1][0], rings[-1][i], rings[-1][i + 1]], t)

RAIL_W, RAIL_H = 0.064, 0.050   # the handrail's section: a mopstick, round over the top, flat underneath for the balusters
def rail_profile():
    """The handrail section about its centre line, which runs 0.02 above the flat underside."""
    r = RAIL_W / 2; top = RAIL_H - 0.020
    pts = [(r, -0.012)]
    for k in range(1, 12):                     # the round top, right side over to the left
        a = math.pi * k / 12
        pts.append((r * math.cos(a), -0.012 + (top + 0.012) * math.sin(a)))
    pts += [(-r, -0.012), (-r + 0.010, -0.020), (r - 0.010, -0.020)]
    return pts

# a baluster between its blocks: (height fraction, width fraction) of the turned part, a vase under a bead and a long taper
BALUSTER = [(0.00, 0.78), (0.05, 0.92), (0.14, 1.00), (0.30, 0.92), (0.40, 0.56), (0.47, 0.70), (0.52, 0.56), (0.80, 0.48), (0.90, 0.46), (1.00, 0.58)]
def baluster(wd, cx, cy, cz, h, w, n=12):
    """A turned baluster standing on y = cy and h tall to the rail's underside: a square base block, the turned
    length, and a square neck block the rail sits on, so it reads as joinery at both ends."""
    base, neck = 0.11, 0.055
    wd.box(cx, cy + base / 2, cz, w, base, w, seg=0)
    turned(wd, cx, cy + base, cz, h - base - neck, w, n=n)
    wd.box(cx, cy + h - neck / 2, cz, w * 0.62, neck, w * 0.62, seg=0)

def newel(wd, br, cx, cy, cz, h, w=0.14):
    """A square newel post standing on y = cy: the post, a moulded cap plate and a brass ball on top."""
    wd.box(cx, cy + h / 2, cz, w, h, w, seg=0)
    wd.box(cx, cy + 0.06, cz, w + 0.04, 0.12, w + 0.04, seg=0)                        # plinth block
    wd.box(cx, cy + h + 0.015, cz, w + 0.05, 0.03, w + 0.05, seg=0)                    # cap plate
    wd.box(cx, cy + h + 0.045, cz, w + 0.015, 0.03, w + 0.015, seg=0)                  # the cap's upper step
    prism(br, cx, cy + h + 0.06, cz, 0.035, 0.012, n=12)                               # a brass collar...
    for (t0, s0), (t1, s1) in zip([(0.0, 0.5), (0.3, 0.95), (0.6, 1.0), (0.85, 0.7), (1.0, 0.2)], [(0.3, 0.95), (0.6, 1.0), (0.85, 0.7), (1.0, 0.2), (1.0, 0.2)]):
        if t1 <= t0: continue
        prism(br, cx, cy + h + 0.072 + 0.09 * t0, cz, 0.048 * s0, 0.09 * (t1 - t0), n=12, r_top=0.048 * s1, cap_top=(t1 >= 1.0), cap_bot=False)   # ...and ball

def poly_prism(b, pts, cx, cy, cz, h, ry=0.0, top=True, bot=True, side=True):
    """Extrude a closed plan outline (list of (u, v) offsets, counter-clockwise) from y = cy up by h.
    Fan-triangulated from the centroid, so a concave outline such as a grand piano case is safe."""
    cr, sr = math.cos(ry), math.sin(ry)
    def W(u, v, y):
        x = u * cr + v * sr; z = -u * sr + v * cr
        return P(cx + x, y, cz + z)
    cu = sum(p[0] for p in pts) / len(pts); cv = sum(p[1] for p in pts) / len(pts)
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        if top: b.face([W(cu, cv, cy + h), W(pts[i][0], pts[i][1], cy + h), W(pts[j][0], pts[j][1], cy + h)], D(0, 1, 0))
        if bot: b.face([W(cu, cv, cy), W(pts[j][0], pts[j][1], cy), W(pts[i][0], pts[i][1], cy)], D(0, -1, 0))
        if side:
            du, dv = pts[j][0] - pts[i][0], pts[j][1] - pts[i][1]
            nx = dv * cr - du * sr; nz = -dv * sr - du * cr
            b.face([W(pts[i][0], pts[i][1], cy), W(pts[j][0], pts[j][1], cy),
                    W(pts[j][0], pts[j][1], cy + h), W(pts[i][0], pts[i][1], cy + h)], D(nx, 0, nz))

def bezier(p0, c, p1, n):
    """n+1 points along a quadratic bezier, for the piano case and the stair's curved nosing."""
    out = []
    for i in range(n + 1):
        t = i / n; k = 1 - t
        out.append((k * k * p0[0] + 2 * t * k * c[0] + t * t * p1[0], k * k * p0[1] + 2 * t * k * c[1] + t * t * p1[1]))
    return out

# ---------------------------------------------------------------- scene
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = SAMPLES_LM
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 4; sc.cycles.glossy_bounces = 3
    sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Base Contrast'
    sc.view_settings.exposure = -1.0
    sc.render.resolution_x = 1280; sc.render.resolution_y = 800
    return sc

# ---------------------------------------------------------------- materials
IMAGES = {}
def image(name, colorspace='sRGB'):
    if name in IMAGES: return IMAGES[name]
    fp = os.path.join(TEX, name + '.png')
    im = bpy.data.images.load(fp, check_existing=True)
    im.colorspace_settings.name = colorspace
    IMAGES[name] = im
    return im

MATS = {}
def material(name, col=None, rgh=None, nrm=None, color=(0.8, 0.8, 0.8, 1), roughness=0.5, metallic=0.0, emission=None, emission_strength=0.0,
             alpha=1.0, nrm_strength=1.0, uvmap='uv'):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nodes = nt.nodes; links = nt.links
    bsdf = nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    uvn = nodes.new('ShaderNodeUVMap'); uvn.uv_map = uvmap; uvn.location = (-900, 0)
    def tex(img_name, cs, y):
        t = nodes.new('ShaderNodeTexImage'); t.image = image(img_name, cs); t.location = (-600, y); t.interpolation = 'Linear'
        links.new(uvn.outputs['UV'], t.inputs['Vector']); return t
    if col:
        t = tex(col, 'sRGB', 300); links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
        if emission: links.new(t.outputs['Color'], bsdf.inputs['Emission Color'])
    if rgh:
        t = tex(rgh, 'Non-Color', 0); links.new(t.outputs['Color'], bsdf.inputs['Roughness'])
    if nrm:
        t = tex(nrm, 'Non-Color', -300); nm = nodes.new('ShaderNodeNormalMap'); nm.location = (-300, -300); nm.inputs['Strength'].default_value = nrm_strength
        nm.uv_map = uvmap
        links.new(t.outputs['Color'], nm.inputs['Color']); links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    if emission is not None and not col:
        bsdf.inputs['Emission Color'].default_value = emission
    bsdf.inputs['Emission Strength'].default_value = emission_strength
    if alpha < 1:
        bsdf.inputs['Alpha'].default_value = alpha
        m.blend_method = 'BLEND'
    MATS[name] = m
    return m

def setup_materials():
    material('floor', 'oak_floor_col', 'oak_floor_rgh', 'oak_floor_nrm', roughness=0.45)
    material('walnut', 'walnut_col', 'walnut_rgh', 'walnut_nrm', roughness=0.4, nrm_strength=0.6)
    material('walnut_v', 'walnut_col', 'walnut_rgh', 'walnut_nrm', roughness=0.4, nrm_strength=0.6)   # vertex-lit twin
    material('oak', 'oak_col', 'oak_rgh', 'oak_nrm', roughness=0.42)
    material('green', 'green_col', 'green_rgh', 'green_nrm', roughness=0.85)
    material('plaster', 'plaster_col', 'plaster_rgh', 'plaster_nrm', roughness=0.9)
    material('plaster_v', 'plaster_col', 'plaster_rgh', 'plaster_nrm', roughness=0.9)
    material('leather_v', 'leather_col', 'leather_rgh', 'leather_nrm', roughness=0.6)
    material('brass_v', 'brass_col', 'brass_rgh', roughness=0.35, metallic=1.0)
    material('books_v', 'books_col', 'books_rgh', roughness=0.75)
    material('shelfrow_v', 'shelfrow_col', roughness=0.8)
    material('rug', 'rug_col', 'rug_rgh', 'rug_nrm', roughness=0.95)
    material('marble', 'marble_col', 'marble_rgh', 'marble_nrm', roughness=0.25)
    material('marble_w', 'marblew_col', 'marblew_rgh', 'marblew_nrm', roughness=0.14)   # the hall floor's two stones
    material('marble_b', 'marbleb_col', 'marbleb_rgh', 'marbleb_nrm', roughness=0.12)
    material('stone_v', 'marblew_col', 'marblew_rgh', 'marblew_nrm', roughness=0.2)     # busts and plinths (vertex-lit)
    material('lacquer_v', color=(0.013, 0.013, 0.015, 1), roughness=0.07)               # the piano's polished case
    material('ivory_v', color=(0.86, 0.84, 0.77, 1), roughness=0.28)                    # its keys
    material('glass', color=(0.9, 0.95, 1.0, 1), roughness=0.05, alpha=0.12)
    material('shade_e', color=(0.06, 0.3, 0.14, 1), roughness=0.3, emission=(0.25, 0.9, 0.4, 1), emission_strength=2.5)
    material('bulb_e', color=(1, 1, 1, 1), emission=(1.0, 0.85, 0.6, 1), emission_strength=25.0)
    material('laylight_e', color=(1, 1, 1, 1), emission=(0.92, 0.95, 1.0, 1), emission_strength=7.0)
    material('view_e', 'window_view', color=(0, 0, 0, 1), emission=True, emission_strength=1.1)
    material('dark_v', color=(0.05, 0.04, 0.035, 1), roughness=0.7)
    material('ironblack_v', color=(0.03, 0.03, 0.03, 1), roughness=0.5, metallic=0.6)

# ---------------------------------------------------------------- mesh building
class Builder:
    """Collects boxes/quads into one mesh per (name, material). World-scale box UVs; optional lightmap uv layer."""
    def __init__(self, name, mat, tile=1.0, lightmap=False, vcol=True, seg=0.0, collection=None, smooth=None):
        self.name = name; self.mat = MATS[mat] if isinstance(mat, str) else mat; self.tile = tile
        self.lightmap = lightmap; self.vcol = vcol; self.seg = seg
        self.smooth = smooth      # degrees: faces meeting at less than this shade smooth (turned posts, swept rails)
        self.bm = bmesh.new(); self.uv = self.bm.loops.layers.uv.new('uv')
        self.count = 0
    def _quad(self, pts, normal, uvs=None, tile=None):
        bm = self.bm
        vs = [bm.verts.new(p) for p in pts]
        try: f = bm.faces.new(vs)
        except ValueError: return None
        f.normal_update()
        if f.normal.dot(normal) < 0: f.normal_flip()
        t = tile or self.tile
        for i, l in enumerate(f.loops):
            if uvs is not None: l[self.uv].uv = uvs[i]
            else:
                p = l.vert.co; n = f.normal
                ax = max(range(3), key=lambda k: abs(n[k]))
                if ax == 0: u, v = p.y, p.z
                elif ax == 1: u, v = p.x, p.z
                else: u, v = p.x, p.y
                l[self.uv].uv = (u / t, v / t)
        self.count += 1
        return f
    def face(self, pts, normal, uvs=None, tile=None):
        """One polygon (3-4 pts) with explicit or world uvs."""
        return self._quad(pts, normal, uvs, tile)
    def grid(self, origin, du, dv, normal, nu=1, nv=1, tile=None):
        """A rectangle origin + a*du + b*dv subdivided nu x nv."""
        for a in range(nu):
            for b in range(nv):
                p00 = origin + du * (a / nu) + dv * (b / nv); p10 = origin + du * ((a + 1) / nu) + dv * (b / nv)
                p11 = origin + du * ((a + 1) / nu) + dv * ((b + 1) / nv); p01 = origin + du * (a / nu) + dv * ((b + 1) / nv)
                self._quad([p00, p10, p11, p01], normal, tile=tile)
    def box(self, cx, cy, cz, sx, sy, sz, ry=0.0, faces='all', seg=None, tile=None):
        """Axis box in CAMPUS coords (center, size), rotated ry about the up axis. faces: subset of 'xXyYzZ' (campus axes)."""
        seg = self.seg if seg is None else seg
        c = P(cx, cy, cz)
        hx, hy, hz = sx / 2, sy / 2, sz / 2
        cr, sr = math.cos(ry), math.sin(ry)
        def W(dx, dy, dz):  # local campus offset -> blender world
            x = dx * cr + dz * sr; z = -dx * sr + dz * cr
            return c + Vector((x, -z, dy))
        def n(nx, ny, nz):
            x = nx * cr + nz * sr; z = -nx * sr + nz * cr
            return Vector((x, -z, ny))
        def segs(l): return max(1, int(math.ceil(l / seg))) if seg > 0 else 1
        want = faces if faces != 'all' else 'xXyYzZ'
        # each face: origin corner, du, dv, normal
        F = {
            'X':(W(hx, -hy, -hz), W(hx, -hy, hz) - W(hx, -hy, -hz), W(hx, hy, -hz) - W(hx, -hy, -hz), n(1, 0, 0), sz, sy),
            'x':(W(-hx, -hy, hz), W(-hx, -hy, -hz) - W(-hx, -hy, hz), W(-hx, hy, hz) - W(-hx, -hy, hz), n(-1, 0, 0), sz, sy),
            'Y':(W(-hx, hy, hz), W(hx, hy, hz) - W(-hx, hy, hz), W(-hx, hy, -hz) - W(-hx, hy, hz), n(0, 1, 0), sx, sz),
            'y':(W(-hx, -hy, -hz), W(hx, -hy, -hz) - W(-hx, -hy, -hz), W(-hx, -hy, hz) - W(-hx, -hy, -hz), n(0, -1, 0), sx, sz),
            'Z':(W(-hx, -hy, hz), W(hx, -hy, hz) - W(-hx, -hy, hz), W(-hx, hy, hz) - W(-hx, -hy, hz), n(0, 0, 1), sx, sy),
            'z':(W(hx, -hy, -hz), W(-hx, -hy, -hz) - W(hx, -hy, -hz), W(hx, hy, -hz) - W(hx, -hy, -hz), n(0, 0, -1), sx, sy),
        }
        for k in want:
            o, du, dv, nn, lu, lv = F[k]
            self.grid(o, du, dv, nn, segs(lu), segs(lv), tile)
    def finish(self, collection=None):
        bm = self.bm
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        if self.smooth is not None:
            # smooth across gentle angles, sharp where faces meet at a real edge (the exporter splits normals there)
            thr = math.radians(self.smooth)
            for f in bm.faces: f.smooth = True
            for e in bm.edges:
                if len(e.link_faces) == 2: e.smooth = e.calc_face_angle(0.0) < thr
                else: e.smooth = False
        me = bpy.data.meshes.new(self.name)
        bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(self.name, me)
        (collection or bpy.context.scene.collection).objects.link(ob)
        me.materials.append(self.mat)
        if self.lightmap:
            me.uv_layers.new(name='lm')
            ob['lm'] = 1
        if self.vcol:
            me.color_attributes.new(name='light', type='FLOAT_COLOR', domain='CORNER')
            me.color_attributes.active_color = me.color_attributes['light']
            ob['vc'] = 1
        # smooth shading only where asked for (keeps boxes crisp)
        if self.smooth is None:
            for p in me.polygons: p.use_smooth = False
        return ob

# ---------------------------------------------------------------- room pieces
X0, X1, Z0, Z1, H = -32.0, -12.0, -13.0, 7.0, 7.6
MEZZ = 3.6          # gallery slab centre height (0.22 thick)
MEZZ_D = 1.75       # how far the gallery juts from the wall: wide enough to walk once the upper cases are on it
DECK = MEZZ + 0.11  # the gallery's walking surface
HALL = (-7.0, 1.0)          # the checkered marble band: the entrance hall, running door to window past the stacks
STAIR = (-15.1, -9.6, 1.35) # spiral stair: centre x, z and outer radius; the radius meets the east gallery's edge
PIANO = (-15.4, 3.3)        # the grand piano, in the open south-east corner, keyboard turned to the room

def build_shell():
    """Floor, ceiling, walls with door and arched window, mezzanine slabs, coffers, crown. Lightmapped."""
    # floor: oak boards under the stacks and reading bays, and a checkered marble hall down the entrance aisle,
    # which is how these rooms are actually paved - the stone where the public walks, wood where people sit and read.
    HZ0, HZ1 = HALL
    fl = Builder('floor', 'floor', tile=2.0, lightmap=True, vcol=False)
    for (az, bz) in [(Z0, HZ0), (HZ1, Z1)]:
        fl.grid(P(X0, 0, bz), P(X1, 0, bz) - P(X0, 0, bz), P(X0, 0, az) - P(X0, 0, bz), Vector((0, 0, 1)), 4, 2)
    fl.finish()
    # the hall: a dark border band each side, then squares laid alternately in the two stones. Laying them as
    # separate quads (rather than painting a checker into one texture) gives every square its own veining.
    BORD = 0.55
    fb = Builder('floor_dark', 'marble_b', tile=2.4, lightmap=True, vcol=False)
    fw = Builder('floor_light', 'marble_w', tile=2.4, lightmap=True, vcol=False)
    def slab(b, ax, bx, az, bz, nu=1, nv=1):
        b.grid(P(ax, 0, bz), P(bx, 0, bz) - P(ax, 0, bz), P(ax, 0, az) - P(ax, 0, bz), Vector((0, 0, 1)), nu, nv)
    for (az, bz) in [(HZ0, HZ0 + BORD), (HZ1 - BORD, HZ1)]: slab(fb, X0, X1, az, bz, 10, 1)
    NX, NZ = 21, 7
    sx = (X1 - X0) / NX; sz = (HZ1 - BORD - HZ0 - BORD) / NZ
    for i in range(NX):
        for j in range(NZ):
            slab(fw if (i + j) % 2 == 0 else fb, X0 + i * sx, X0 + (i + 1) * sx, HZ0 + BORD + j * sz, HZ0 + BORD + (j + 1) * sz)
    fb.finish(); fw.finish()
    # ceiling plane with laylight hole (two strips + two end pieces)
    ce = Builder('ceiling', 'plaster', tile=3.0, lightmap=True, vcol=False)
    LX0, LX1, LZ0, LZ1 = -30.0, -14.0, -3.9, -2.1   # laylight opening
    for (ax, bx, az, bz) in [(X0, X1, Z0, LZ0), (X0, X1, LZ1, Z1), (X0, LX0, LZ0, LZ1), (LX1, X1, LZ0, LZ1)]:
        ce.grid(P(ax, H, az), P(bx, H, az) - P(ax, H, az), P(ax, H, bz) - P(ax, H, az), Vector((0, 0, -1)), 3, 3)
    ce.finish()
    # laylight: frame + glowing panel set 0.3 above the ceiling
    ll = Builder('laylight', 'laylight_e', tile=1.0, lightmap=False, vcol=False)
    ll.grid(P(LX0, H + 0.3, LZ0), P(LX1, H + 0.3, LZ0) - P(LX0, H + 0.3, LZ0), P(LX0, H + 0.3, LZ1) - P(LX0, H + 0.3, LZ0), Vector((0, 0, -1)))
    ll.finish()
    lf = Builder('laylight_frame', 'plaster_v', tile=3.0, lightmap=False, vcol=True, seg=1.0)
    # the frame lines the inside of the opening (outside it, its faces shared the ceiling slab's rim and flickered)
    lf.box((LX0 + LX1) / 2, H + 0.15, LZ0 + 0.1, LX1 - LX0, 0.3, 0.2); lf.box((LX0 + LX1) / 2, H + 0.15, LZ1 - 0.1, LX1 - LX0, 0.3, 0.2)
    lf.box(LX0 + 0.1, H + 0.15, (LZ0 + LZ1) / 2, 0.2, 0.3, LZ1 - LZ0); lf.box(LX1 - 0.1, H + 0.15, (LZ0 + LZ1) / 2, 0.2, 0.3, LZ1 - LZ0)
    # mullions across the laylight
    for x in frange(LX0 + 2.0, LX1 - 0.5, 2.0): lf.box(x, H + 0.15, (LZ0 + LZ1) / 2, 0.08, 0.3, LZ1 - LZ0)
    lf.finish()
    # walls (inside faces), with openings cut by leaving them out of the grid: built from rectangles
    wl = Builder('walls', 'green', tile=3.0, lightmap=True, vcol=False)
    # north wall z=Z0 (faces +z), south wall z=Z1 (faces -z)
    wl.grid(P(X0, 0, Z0), P(X1, 0, Z0) - P(X0, 0, Z0), P(X0, H, Z0) - P(X0, 0, Z0), Vector((0, -1, 0)), 4, 2)
    wl.grid(P(X1, 0, Z1), P(X0, 0, Z1) - P(X1, 0, Z1), P(X1, H, Z1) - P(X1, 0, Z1), Vector((0, 1, 0)), 4, 2)
    # east wall x=X1 (faces -x) with door z -4.6..-1.4 up to 3.4
    DZ0, DZ1, DH = -4.6, -1.4, 3.4
    for (az, bz, ay, by) in [(Z0, DZ0, 0, H), (DZ1, Z1, 0, H), (DZ0, DZ1, DH, H)]:
        wl.grid(P(X1, ay, bz), P(X1, ay, az) - P(X1, ay, bz), P(X1, by, bz) - P(X1, ay, bz), Vector((-1, 0, 0)), 2, 2)
    # west wall x=X0 (faces +x) with window z -5.2..-0.8, y 1.0..4.6 + arch to 6.8
    WZ0, WZ1, WY0, WY1 = -5.2, -0.8, 1.0, 4.6
    for (az, bz, ay, by) in [(Z0, WZ0, 0, H), (WZ1, Z1, 0, H), (WZ0, WZ1, 0, WY0)]:
        wl.grid(P(X0, ay, az), P(X0, ay, bz) - P(X0, ay, az), P(X0, by, az) - P(X0, ay, az), Vector((1, 0, 0)), 2, 2)
    # above the arch: a strip with the arch cut out (polygon fan)
    R = (WZ1 - WZ0) / 2; zc = (WZ0 + WZ1) / 2
    N = 16
    arc = [(zc - R * math.cos(math.pi * i / N), WY1 + R * math.sin(math.pi * i / N)) for i in range(N + 1)]
    # left/right spandrels + top: triangles from the arch to the rectangle corners
    top = [(WZ0, H), (WZ1, H)]
    pts = [(WZ0, WY1)] + arc + [(WZ1, WY1), (WZ1, H), (WZ0, H)]
    # triangulate the spandrel region as fan from top corners
    for i in range(len(arc) - 1):
        a, b = arc[i], arc[i + 1]
        apex = (WZ0, H) if (a[0] + b[0]) / 2 < zc else (WZ1, H)
        wl.face([P(X0, a[1], a[0]), P(X0, b[1], b[0]), P(X0, apex[1], apex[0])], Vector((1, 0, 0)))
    wl.face([P(X0, H, WZ0), P(X0, WY1 + R, zc), P(X0, H, WZ1)], Vector((1, 0, 0)))
    wl.finish()
    # door jamb reveal (wall thickness 0.45) and window reveal
    rv = Builder('reveals', 'plaster_v', tile=3.0, lightmap=False, vcol=True, seg=0.5)
    T = 0.45
    rv.box(X1 + T / 2, DH / 2, DZ0, T, DH, 0.02, faces='Z'); rv.box(X1 + T / 2, DH / 2, DZ1, T, DH, 0.02, faces='z')
    rv.box(X1 + T / 2, DH, (DZ0 + DZ1) / 2, T, 0.02, DZ1 - DZ0, faces='y')
    rv.box(X0 - T / 2, (WY0 + WY1) / 2, WZ0, T, WY1 - WY0, 0.02, faces='Z'); rv.box(X0 - T / 2, (WY0 + WY1) / 2, WZ1, T, WY1 - WY0, 0.02, faces='z')
    rv.finish()
    # gallery slabs (top faces + inner edge faces), MEZZ_D deep, centre height MEZZ, 0.22 thick; the west run
    # breaks at the window bay (z -5.6 .. -0.4) so the arched window is open to the room full height
    sl = Builder('mezz', 'plaster', tile=3.0, lightmap=True, vcol=False)
    d = MEZZ_D
    for (ax, bx, az, bz) in [(X0, X1, Z0, Z0 + d), (X0, X1, Z1 - d, Z1), (X0, X0 + d, Z0 + d, -5.6), (X0, X0 + d, -0.4, Z1 - d), (X1 - d, X1, Z0 + d, Z1 - d)]:
        sl.box((ax + bx) / 2, MEZZ, (az + bz) / 2, bx - ax, 0.22, bz - az, faces='Yy' + ('Z' if bz < 0 else '') + ('z' if az > 0 else ''), seg=1.0)
    sl.finish()
    # slab edge trim (walnut) + the inner slab edge faces for the two long slabs and the east slab
    tr = Builder('mezz_trim', 'walnut_v', tile=1.0, lightmap=False, vcol=True, seg=1.0)
    tr.box((X0 + X1) / 2, MEZZ, Z0 + d + 0.01, X1 - X0, 0.26, 0.04, faces='ZYy')
    tr.box((X0 + X1) / 2, MEZZ, Z1 - d - 0.01, X1 - X0, 0.26, 0.04, faces='zYy')
    tr.box(X0 + d + 0.01, MEZZ, (Z0 + d - 5.6) / 2 + 0, 0.04, 0.26, -5.6 - (Z0 + d), faces='XYy')
    tr.box(X0 + d + 0.01, MEZZ, (-0.4 + Z1 - d) / 2, 0.04, 0.26, (Z1 - d) + 0.4, faces='XYy')
    tr.box(X1 - d - 0.01, MEZZ, (Z0 + d + Z1 - d) / 2, 0.04, 0.26, (Z1 - d) - (Z0 + d), faces='xYy')
    tr.finish()
    # ceiling coffer beams (plaster), every 2.5 m, and crown moulding
    cf = Builder('coffers', 'plaster_v', tile=3.0, lightmap=False, vcol=True, seg=1.0)
    for x in frange(X0 + 2.5, X1 - 1.0, 2.5):
        for (az, bz) in [(Z0, LZ0 - 0.1), (LZ1 + 0.1, Z1)]:
            cf.box(x, H - 0.17, (az + bz) / 2, 0.28, 0.34, bz - az, faces='xXy')
    for z in frange(Z0 + 2.5, Z1 - 1.0, 2.5):
        if LZ0 - 0.3 < z < LZ1 + 0.3: continue
        cf.box((X0 + X1) / 2, H - 0.17, z, X1 - X0, 0.34, 0.28, faces='zZy')
    cf.box((X0 + X1) / 2, H - 0.2, Z0 + 0.14, X1 - X0, 0.4, 0.28, faces='Zy'); cf.box((X0 + X1) / 2, H - 0.2, Z1 - 0.14, X1 - X0, 0.4, 0.28, faces='zy')
    cf.box(X0 + 0.14, H - 0.2, (Z0 + Z1) / 2, 0.28, 0.4, Z1 - Z0, faces='Xy'); cf.box(X1 - 0.14, H - 0.2, (Z0 + Z1) / 2, 0.28, 0.4, Z1 - Z0, faces='xy')
    cf.finish()
    # window: frame, mullions, arch, sill, glass, backdrop
    wf = Builder('window_frame', 'walnut_v', tile=1.0, lightmap=False, vcol=True, seg=0.6)
    for z in [WZ0 + 0.04, WZ1 - 0.04]: wf.box(X0 - 0.12, (WY0 + WY1) / 2, z, 0.12, WY1 - WY0, 0.08)
    for y in [WY0 + 0.04, 2.4, 3.6, WY1 - 0.03]: wf.box(X0 - 0.12, y, zc, 0.12, 0.08, WZ1 - WZ0)
    for z in [zc - 1.1, zc, zc + 1.1]: wf.box(X0 - 0.1, (WY0 + WY1) / 2, z, 0.08, WY1 - WY0, 0.05)
    # arch pieces
    for i in range(N):
        a0 = math.pi * i / N; a1 = math.pi * (i + 1) / N
        p0 = (zc - R * math.cos(a0), WY1 + R * math.sin(a0)); p1 = (zc - R * math.cos(a1), WY1 + R * math.sin(a1))
        mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2); ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        L = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) + 0.02
        # a small rotated box: build via face() with explicit points (rotation in the z-y plane)
        c, s = math.cos(ang), math.sin(ang)
        def pt(u, v, dx): return P(X0 - 0.12 + dx, mid[1] + u * s + v * c, mid[0] + u * c - v * s)
        for dx in (-0.06, 0.06):
            wf.face([pt(-L / 2, -0.14, dx), pt(L / 2, -0.14, dx), pt(L / 2, 0.02, dx), pt(-L / 2, 0.02, dx)], Vector((1 if dx > 0 else -1, 0, 0)))
        wf.face([pt(-L / 2, -0.14, -0.06), pt(L / 2, -0.14, -0.06), pt(L / 2, -0.14, 0.06), pt(-L / 2, -0.14, 0.06)], Vector((0, 0, -1)))
    # arch radial spokes
    for i in range(1, 4):
        a = math.pi * i / 4
        pz, py = zc - (R - 0.08) * math.cos(a), WY1 + (R - 0.08) * math.sin(a)
        for dx in (-0.04, 0.04):
            wf.face([P(X0 - 0.1 + dx, WY1, zc - 0.03), P(X0 - 0.1 + dx, WY1, zc + 0.03), P(X0 - 0.1 + dx, py + 0.03 * math.cos(a), pz + 0.03 * math.sin(a)), P(X0 - 0.1 + dx, py - 0.03 * math.cos(a), pz - 0.03 * math.sin(a))], Vector((1 if dx > 0 else -1, 0, 0)))
    wf.box(X0 + 0.16, WY0 - 0.03, zc, 0.36, 0.06, WZ1 - WZ0 + 0.4)     # sill
    wf.finish()
    gl = Builder('window_glass', 'glass', tile=1.0, lightmap=False, vcol=False)
    gl.grid(P(X0 - 0.2, WY0, WZ0), P(X0 - 0.2, WY0, WZ1) - P(X0 - 0.2, WY0, WZ0), P(X0 - 0.2, WY1 + R, WZ0) - P(X0 - 0.2, WY0, WZ0), Vector((1, 0, 0)))
    glo = gl.finish(); glo.visible_shadow = False
    bd = Builder('window_view', 'view_e', tile=1.0, lightmap=False, vcol=False)
    # backdrop 2.5 m out, big enough to fill the window from any angle, uv 0..1
    bd.face([P(X0 - 2.5, -1.0, zc + 7), P(X0 - 2.5, -1.0, zc - 7), P(X0 - 2.5, 8.6, zc - 7), P(X0 - 2.5, 8.6, zc + 7)], Vector((1, 0, 0)), uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    bdo = bd.finish(); bdo.visible_shadow = False; bdo.visible_diffuse = False; bdo.visible_glossy = True
    # a red runner down the centre of the marble hall, laid as four rugs end to end (each gets uv 0..1, so the
    # border art stays the right way round instead of tiling through itself) with the stone showing either side
    rg = Builder('rugs', 'rug', tile=1.0, lightmap=True, vcol=False)
    for cx in (-14.8, -19.5, -24.2, -28.9):
        rg.face([P(cx - 2.3, 0.012, -2.05), P(cx + 2.3, 0.012, -2.05), P(cx + 2.3, 0.012, -3.95), P(cx - 2.3, 0.012, -3.95)], Vector((0, 0, 1)), uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])
    rg.finish()
    return dict(LZ=(LZ0, LZ1), LX=(LX0, LX1), door=(DZ0, DZ1, DH), win=(WZ0, WZ1, WY0, WY1, R, zc))

# ---------------------------------------------------------------- bookcases and books
BOOK_CELLS = 64
def fill_row(bk, o, s0, s1, yb, rowH):
    """Books along a shelf segment: o has x, z, dir (unit along), n (unit out of the case toward the aisle), depth.
    The row is laid out first so every book next to a gap gets its side faces."""
    items = []   # (s, w, h, d, lean) or None for a gap
    s = s0 + 0.01
    while s < s1 - 0.03:
        if rnd.random() < 0.03: s += 0.06 + rnd.random() * 0.2; items.append(None); continue
        w = 0.026 + rnd.random() * 0.042; h = min(rowH - 0.05, rowH * (0.6 + rnd.random() * 0.32)); d = o['depth'] * (0.66 + rnd.random() * 0.24)
        if s + w > s1 - 0.01: break
        lean = 0.0
        if rnd.random() < 0.025 and s + w + 0.14 < s1: lean = (0.18 + rnd.random() * 0.22) * (1 if rnd.random() < 0.5 else -1)
        items.append((s, w, h, d, lean))
        s += w + (0.14 if lean else 0.0015)
        if lean: items.append(None)
    for i, it in enumerate(items):
        if it is None: continue
        s, w, h, d, lean = it
        sides = i == 0 or i == len(items) - 1 or items[i - 1] is None or items[i + 1] is None or lean != 0
        sc = s + w / 2; t = o['depth'] - 0.015 - d / 2
        cx = o['x'] + o['dir'][0] * sc + o['n'][0] * t; cz = o['z'] + o['dir'][1] * sc + o['n'][1] * t
        bk.book(cx, yb + 0.0125, cz, w, h, d, o['ry'], lean, sides=sides)

class Books(Builder):
    def __init__(self, name):
        super().__init__(name, 'books_v', tile=1.0, lightmap=False, vcol=True)
    def book(self, cx, yb, cz, w, h, d, ry, lean, sides):
        """A book standing on the shelf: spine toward +n (facing the aisle = local -z... we take local +z as the spine)."""
        cell = rnd.randrange(BOOK_CELLS); cu, cv = (cell % 16) / 16.0, 1 - ((cell // 16) + 1) * 448 / 2048.0
        cw, ch = 1 / 16.0, 448 / 2048.0
        spine = [(cu, cv), (cu + cw / 2, cv), (cu + cw / 2, cv + ch), (cu, cv + ch)]
        cover = [(cu + cw / 2, cv), (cu + cw, cv), (cu + cw, cv + ch), (cu + cw / 2, cv + ch)]
        pages = [(0.0, 0.0), (0.2, 0.0), (0.2, 0.12), (0.0, 0.12)]
        c = P(cx, yb, cz); cr, sr = math.cos(ry), math.sin(ry)
        cl, sl_ = math.cos(lean), math.sin(lean)
        def W(dx, dy, dz):  # local: x along shelf, y up, z out toward the aisle (spine at +z); lean rotates about local z
            lx = dx * cl - dy * sl_; ly = dx * sl_ + dy * cl
            x = lx * cr + dz * sr; z = -lx * sr + dz * cr
            return c + Vector((x, -z, ly))
        hw, hd = w / 2, d / 2
        # spine (+z)
        self.face([W(-hw, 0, hd), W(hw, 0, hd), W(hw, h, hd), W(-hw, h, hd)], W(0, 0, 1) - W(0, 0, 0), uvs=spine)
        # top (+y): pages
        self.face([W(-hw, h, -hd), W(hw, h, -hd), W(hw, h, hd), W(-hw, h, hd)], W(0, 1, 0) - W(0, 0, 0), uvs=pages)
        if sides:
            self.face([W(hw, 0, hd), W(hw, 0, -hd), W(hw, h, -hd), W(hw, h, hd)], W(1, 0, 0) - W(0, 0, 0), uvs=cover)
            self.face([W(-hw, 0, -hd), W(-hw, 0, hd), W(-hw, h, hd), W(-hw, h, -hd)], W(-1, 0, 0) - W(0, 0, 0), uvs=cover)
        if lean:
            self.face([W(-hw, 0, hd), W(-hw, 0, -hd), W(hw, 0, -hd), W(hw, 0, hd)], W(0, -1, 0) - W(0, 0, 0), uvs=pages)

def bookcase(cases, books, rows_imp, o):
    """A bookcase: o = x, z (start corner), dir, n, len, y0, rows, rowH, depth, impostor(bool)."""
    o['ry'] = math.atan2(-o['dir'][1], o['dir'][0])
    Ht = o['rows'] * o['rowH'] + 0.06
    def Pt(s, t, y): return (o['x'] + o['dir'][0] * s + o['n'][0] * t, y, o['z'] + o['dir'][1] * s + o['n'][1] * t)
    q = Pt(o['len'] / 2, 0.012, o['y0'] + Ht / 2); cases.box(q[0], q[1], q[2], o['len'], Ht, 0.024, o['ry'])            # back
    ov = o.get('overhang', 0.04)
    q = Pt(o['len'] / 2, o['depth'] / 2, o['y0'] + Ht + 0.03); cases.box(q[0], q[1], q[2], o['len'] + 2 * ov, 0.06, o['depth'] + 0.04, o['ry'])  # top
    nDiv = max(1, round(o['len'] / 0.95)); seg = o['len'] / nDiv
    for k in range(nDiv + 1):
        q = Pt(k * seg, o['depth'] / 2, o['y0'] + Ht / 2); cases.box(q[0], q[1], q[2], 0.045, Ht, o['depth'], o['ry'])
    for i in range(o['rows'] + 1):
        q = Pt(o['len'] / 2, o['depth'] / 2, o['y0'] + i * o['rowH']); cases.box(q[0], q[1], q[2], o['len'], 0.025, o['depth'], o['ry'])
    for i in range(o['rows']):
        if o.get('impostor'):
            # one textured strip per row, 0.15 m in from the back, tile 4.8 m horizontally
            y = o['y0'] + i * o['rowH'] + 0.0125
            a = Pt(0.03, o['depth'] - 0.16, y); b = Pt(o['len'] - 0.03, o['depth'] - 0.16, y)
            nrm = Vector((o['n'][0], -o['n'][1], 0))
            u1 = o['len'] / 4.8; v1 = (o['rowH'] - 0.03) / 0.48
            rows_imp.face([P(*a), P(*b), P(b[0], y + o['rowH'] - 0.03, b[2]), P(a[0], y + o['rowH'] - 0.03, a[2])], nrm, uvs=[(0, 0), (u1, 0), (u1, v1), (0, v1)])
        else:
            for k in range(nDiv):
                fill_row(books, o, k * seg + 0.025, (k + 1) * seg - 0.025, o['y0'] + i * o['rowH'], o['rowH'])

def build_bookcases():
    cases = Builder('cases', 'walnut_v', tile=1.0, lightmap=False, vcol=True, seg=0.5)
    books = Books('books')
    imp = Builder('shelfrows', 'shelfrow_v', tile=1.0, lightmap=False, vcol=True)
    T1 = (0.1, 8, 0.41); T2 = (3.8, 6, 0.48)
    runs = [
        dict(x=-31.6, z=Z0, dir=(1, 0), n=(0, 1), len=19.2, tiers=[T1, T2]),
        dict(x=-12.4, z=Z1, dir=(-1, 0), n=(0, -1), len=19.2, tiers=[T1, T2]),
        dict(x=X0, z=6.6, dir=(0, -1), n=(1, 0), len=7.0, tiers=[T1, T2]),
        dict(x=X0, z=-5.6, dir=(0, -1), n=(1, 0), len=7.0, tiers=[T1, T2]),
        dict(x=X1, z=-12.6, dir=(0, 1), n=(-1, 0), len=7.4, tiers=[T1]),
        dict(x=X1, z=-0.8, dir=(0, 1), n=(-1, 0), len=7.4, tiers=[T1]),
        dict(x=X1, z=-12.6, dir=(0, 1), n=(-1, 0), len=19.2, tiers=[T2]),
    ]
    for run in runs:
        for (y0, rows, rowH) in run['tiers']:
            bookcase(cases, books, imp, dict(x=run['x'], z=run['z'], dir=run['dir'], n=run['n'], len=run['len'], y0=y0, rows=rows, rowH=rowH, depth=0.42, impostor=(y0 > 1) and not UE))
    # the stacks: 4 double-sided cases north and south of the aisle
    ends = Builder('case_ends', 'walnut_v', tile=1.0, lightmap=False, vcol=True, seg=0.5)
    for slot in range(4):
        sx = -24.0 - 2.2 * slot
        for north in (True, False):
            za, zb = (-12.4, -5.6) if north else (-0.4, 6.4)
            length = zb - za
            bookcase(cases, books, imp, dict(x=sx, z=zb, dir=(0, -1), n=(1, 0), len=length, y0=0.1, rows=4, rowH=0.5, depth=0.27, overhang=0))
            bookcase(cases, books, imp, dict(x=sx, z=za, dir=(0, 1), n=(-1, 0), len=length, y0=0.1, rows=4, rowH=0.5, depth=0.27, overhang=0))
            for zz in (za - 0.02, zb + 0.02): ends.box(sx, 1.15, zz, 0.6, 2.3, 0.04)
            ze = zb + 0.045 if north else za - 0.045; sgn = 1 if north else -1
            ends.box(sx, 1.0, ze + sgn * 0.06, 0.58, 0.03, 0.14)   # display ledge
    cases.finish(); books.finish(); imp.finish(); ends.finish()

# ---------------------------------------------------------------- furniture and lights
PARAPET_H = 0.95     # gallery deck to the top of the cap rail
PARAPET_T = 0.11
# The landing sits in the sector just PAST the top tread (south of the newel's centre line), never over the
# treads that climb to it: centred on the newel it would roof the last three treads with 15 cm to spare.
# Its north edge is the arrival, left open; the south and west edges are drops and get parapets.
SGAP = (STAIR[1] + 0.05, STAIR[1] + 1.60)   # the landing's z extent, and the opening in the east parapet

def _pbox(b, axis, s, y, c, la, sy, t, seg=None):
    """One box on a parapet run: s along the run, y up, c across it; la long, sy tall, t thick."""
    if axis == 'x': b.box(s, y, c, la, sy, t, seg=seg)
    else:           b.box(c, y, s, t, sy, la, seg=seg)

def parapet_run(wd, br, axis, a0, a1, c, out):
    """One straight length of the gallery front: plinth, panelled body, brass bead, moulded cap rail.
    axis is the run's direction, a0..a1 its extent, c the fixed coordinate across it, and out (+1/-1) the side
    the room is on, where the applied panel moulding goes. The bays divide themselves to suit the run's length."""
    y0, L, mid, T = DECK, a1 - a0, (a0 + a1) / 2, PARAPET_T
    if L <= 0.01: return
    _pbox(wd, axis, mid, y0 + 0.055, c, L, 0.11, T + 0.05, seg=1.0)                 # plinth
    _pbox(wd, axis, mid, y0 + PARAPET_H / 2, c, L, PARAPET_H, T, seg=1.0)           # panelled body
    _pbox(br, axis, mid, y0 + PARAPET_H - 0.13, c, L, 0.025, T + 0.045, seg=1.0)    # brass bead under the cap
    _pbox(wd, axis, mid, y0 + PARAPET_H - 0.045, c, L, 0.09, T + 0.08, seg=1.0)     # moulded cap rail
    f = c + out * (T / 2 + 0.013)
    n = max(1, int(round(L / 1.5))); bw = L / n
    pw, ph = bw - 0.36, PARAPET_H - 0.50
    cy = y0 + 0.17 + ph / 2
    if pw < 0.2: return
    for k in range(n):
        s = a0 + (k + 0.5) * bw
        for dy in (-ph / 2, ph / 2): _pbox(wd, axis, s, cy + dy, f, pw, 0.038, 0.026, seg=0)
        for ds in (-pw / 2, pw / 2): _pbox(wd, axis, s + ds, cy, f, 0.038, ph, 0.026, seg=0)

def build_rails():
    """The gallery front. A panelled walnut parapet rather than an open rail: that is how the reading rooms this
    is drawn from are built, and it reads far better across a room than a row of thin posts. The east run breaks
    where the spiral stair arrives, and the stair's landing carries its own two short runs."""
    wd = Builder('parapet', 'walnut_v', tile=1.0, lightmap=False, vcol=True, seg=1.0)
    br = Builder('parapet_brass', 'brass_v', tile=1.0, lightmap=False, vcol=True, seg=1.0)
    d = MEZZ_D
    cx, cz, R = STAIR
    gx = X1 - d
    parapet_run(wd, br, 'x', X0 + d, X1 - d, Z0 + d, +1)        # north gallery
    parapet_run(wd, br, 'x', X0 + d, X1 - d, Z1 - d, -1)        # south gallery
    parapet_run(wd, br, 'z', Z0 + d, -5.6, X0 + d, +1)          # west, north of the window bay
    parapet_run(wd, br, 'z', -0.4, Z1 - d, X0 + d, +1)          # west, south of it
    parapet_run(wd, br, 'z', Z0 + d, SGAP[0], gx, -1)           # east, up to the stair opening
    parapet_run(wd, br, 'z', SGAP[1], Z1 - d, gx, -1)           # east, on from it
    # the landing: north edge open (the top tread arrives through it), south and west edges railed
    parapet_run(wd, br, 'x', cx, gx, SGAP[1], +1)               # south edge
    parapet_run(wd, br, 'z', SGAP[0], SGAP[1], cx, -1)          # west edge, from the stair newel to the corner
    for (nx, nz) in ((gx - 0.07, SGAP[0]), (gx - 0.07, SGAP[1]), (cx, SGAP[1])):   # the three free corners
        newel(wd, br, nx, DECK, nz, PARAPET_H + 0.06)
    wd.finish(); br.finish()

def tread(b, cx, cz, y, a0, a1, r0, r1, th, steps=3):
    """One wedge tread of the spiral: top, soffit, the outer arc band and the two radial edges."""
    def pt(a, r, yy): return P(cx + r * math.cos(a), yy, cz + r * math.sin(a))
    angs = [a0 + (a1 - a0) * i / steps for i in range(steps + 1)]
    for i in range(steps):
        p, q = angs[i], angs[i + 1]; am = (p + q) / 2
        b.face([pt(p, r0, y), pt(q, r0, y), pt(q, r1, y), pt(p, r1, y)], D(0, 1, 0))
        b.face([pt(p, r0, y - th), pt(p, r1, y - th), pt(q, r1, y - th), pt(q, r0, y - th)], D(0, -1, 0))
        b.face([pt(p, r1, y - th), pt(q, r1, y - th), pt(q, r1, y), pt(p, r1, y)], D(math.cos(am), 0, math.sin(am)))
    for (a, sgn) in ((a0, -1.0), (a1, 1.0)):
        b.face([pt(a, r0, y - th), pt(a, r1, y - th), pt(a, r1, y), pt(a, r0, y)],
               D(-math.sin(a) * sgn, 0, math.cos(a) * sgn))

def build_stair(lights):
    """The spiral stair to the gallery: wedge treads winding round a brass newel, a turned baluster on every
    tread, and a handrail that climbs with them. The last riser is on to a square landing that meets the east
    gallery flush, which is how a spiral is actually finished - the arc alone would leave a crescent to fall down."""
    cx, cz, R = STAIR
    gx = X1 - MEZZ_D
    tw = Builder('stair', 'walnut_v', tile=1.0, lightmap=False, vcol=True, seg=0.6, smooth=40)
    br = Builder('stair_brass', 'brass_v', tile=0.35, lightmap=False, vcol=True, seg=0.6, smooth=40)   # fine grain on thin posts
    N = 20                           # risers to the gallery deck
    rise = DECK / N                  # 0.186 m rise against a 0.26 m going on the walking line: 2R + G = 0.63
    sweep_a = math.radians(300.0)    # just under a full turn, so no tread ever passes over another
    w = sweep_a / N
    # Balusters right out at the nosing. Further in they pinch the walking line: a visitor is a 60 cm capsule,
    # and at the natural line (85 cm from the newel) its rim reaches 1.15 m, which the swells and the handrail
    # must stay outside of. At R - 0.07 the swell's inner face is at 1.21 and the rail's at 1.25.
    rb = R - 0.07                    # the balustrade's radius
    BAL_H = 0.86                     # tread to the rail's underside
    def on_helix(a): return (cx + rb * math.cos(a), cz + rb * math.sin(a))
    def rail_y(a): return (a / w + N) * rise + BAL_H + 0.020      # the rail's centre line height at angle a
    for i in range(1, N):            # the last riser is on to the landing, so there is no tread for it
        a = (i - N) * w; y = i * rise
        tread(tw, cx, cz, y, a - w / 2, a + w / 2, 0.14, R, 0.055)
        bx, bz = on_helix(a)
        baluster(tw, bx, y, bz, BAL_H, 0.095)
    # landing: flush with the gallery deck and butted to its edge, in the sector past the top tread (SGAP)
    tw.box((cx + gx) / 2, DECK - 0.11, (SGAP[0] + SGAP[1]) / 2, gx - cx, 0.22, SGAP[1] - SGAP[0], seg=0.6)
    # newel, in segments so the vertex-colour bake has something to work with up its length
    y = 0.0
    while y < DECK + 1.0 - 1e-6:
        h = min(0.5, DECK + 1.0 - y)
        prism(br, cx, y, cz, 0.078, h, n=12, cap_top=False, cap_bot=(y < 1e-9)); y += h
    prism(br, cx, -0.012, cz, 0.26, 0.06, n=16)                              # base plate
    prism(br, cx, DECK + 1.0, cz, 0.078, 0.13, n=12, r_top=0.028)            # finial
    # The balustrade starts on a square newel at the foot of the stair, standing on the floor where the first
    # riser begins, and ends on the gallery's corner newel, which the helix arrives at by itself (the landing
    # corner sits on the stair's own radius). The handrail is one swept piece between them: it climbs the helix
    # over every baluster and eases up over the last two treads to arrive level with the parapet's cap.
    a_foot = -sweep_a
    fx, fz = on_helix(a_foot)
    newel(tw, br, fx, 0.0, fz, rail_y(a_foot) + 0.02 - 0.025)
    nx, nz = gx - 0.07, SGAP[0]                                              # the gallery corner newel (build_rails)
    a_end = -0.016                                                           # where the helix meets that newel's face
    y_end = DECK + PARAPET_H - 0.045                                         # the parapet cap rail's centre
    a_start = a_foot + 0.07 / rb                                             # off the foot newel's face
    path = []
    k = 0
    while True:
        a = a_start + k * (w / 5)
        if a >= a_end: break
        ease = max(0.0, (a - (a_end - 2 * w)) / (2 * w))                     # 0 until the last two treads, then 1 at the newel
        yy = rail_y(a) + (y_end - rail_y(a_end)) * (ease * ease * (3 - 2 * ease))
        path.append((on_helix(a)[0], yy, on_helix(a)[1])); k += 1
    ex, ez = on_helix(a_end)
    path.append((ex, y_end, ez))
    path.append((ex + (nx - ex) * 0.5, y_end, ez + (nz - ez) * 0.5))         # into the newel's face
    sweep(br, path, rail_profile())
    # the stair stands in a corner the chandeliers do not reach, so it gets light of its own
    lights.append(('point', (cx - 0.1, 2.30, cz), (1.0, 0.86, 0.66), 45))
    lights.append(('point', (cx + 0.9, DECK + 1.10, cz), (1.0, 0.86, 0.66), 40))
    tw.finish(); br.finish()

def lamp(brass, shade, bulb, x, y, z, ry=0.0):
    brass.box(x, y + 0.01, z, 0.16, 0.02, 0.11, ry); brass.box(x, y + 0.17, z, 0.016, 0.3, 0.016, ry, seg=0)
    brass.box(x, y + 0.3, z, 0.016, 0.016, 0.10, ry, seg=0)
    shade.box(x, y + 0.34, z, 0.34, 0.07, 0.15, ry)
    bulb.box(x, y + 0.305, z, 0.26, 0.012, 0.08, ry)

def build_furniture(lights):
    walnut = Builder('furniture', 'walnut_v', tile=1.0, lightmap=False, vcol=True, seg=0.4)
    tops = Builder('tabletops', 'oak', tile=1.0, lightmap=True, vcol=False)
    leather = Builder('seats', 'leather_v', tile=0.6, lightmap=False, vcol=True, seg=0.3)
    brass = Builder('lamp_brass', 'brass_v', tile=1.0, lightmap=False, vcol=True, seg=0.5)
    shade = Builder('lamp_shades', 'shade_e', tile=1.0, lightmap=False, vcol=False)
    bulb = Builder('lamp_bulbs', 'bulb_e', tile=1.0, lightmap=False, vcol=False)
    # The desk and the two reading tables sit a little west of where they used to, which leaves the east end of
    # the room clear for the spiral stair and the piano. RDX and TX are the only numbers that moved.
    RDX, TX = -18.6, -19.5
    # reference desk
    walnut.box(RDX, 0.5, -6.9, 3.0, 1.0, 0.8); tops.box(RDX, 1.025, -6.9, 3.12, 0.05, 0.92, faces='YxXzZ')
    walnut.box(RDX, 0.52, -6.9 + 0.41, 3.0, 0.08, 0.03)
    lamp(brass, shade, bulb, RDX - 1.1, 1.05, -7.0); lights.append(('point', (RDX - 1.1, 1.35, -7.0), (1.0, 0.75, 0.45), 18))
    for i in range(3): walnut.box(RDX + 1.2, 1.075 + i * 0.05, -6.95, 0.22, 0.05, 0.3, 0.1 * i)
    # reading tables with lamps and chairs
    for tz in (-10.8, 4.6):
        tops.box(TX, 0.76, tz, 3.6, 0.06, 1.1, faces='YxXzZ'); walnut.box(TX, 0.72, tz, 3.4, 0.05, 1.0)
        for lx in (-1.7, 1.7):
            for lz in (-0.47, 0.47): walnut.box(TX + lx, 0.365, tz + lz, 0.08, 0.73, 0.08)
        walnut.box(TX, 0.12, tz, 3.4, 0.05, 0.08)
        for lx in (TX - 1.2, TX, TX + 1.2):
            lamp(brass, shade, bulb, lx, 0.79, tz); lights.append(('point', (lx, 1.09, tz), (1.0, 0.75, 0.45), 18))
            for s in (-1, 1):
                cz = tz + s * 0.85
                leather.box(lx, 0.47, cz, 0.44, 0.06, 0.42); leather.box(lx, 0.74, cz + s * 0.2, 0.44, 0.5, 0.05)
                walnut.box(lx, 0.22, cz, 0.40, 0.44, 0.38, seg=0.2)
                for dx in (-0.19, 0.19): walnut.box(lx + dx, 0.75, cz + s * 0.2, 0.03, 0.56, 0.03)
    # featured table
    walnut.box(-15.0, 0.37, 0.9, 3.3, 0.74, 0.9); tops.box(-15.0, 0.765, 0.9, 3.4, 0.05, 1.0, faces='YxXzZ'); walnut.box(-15.0, 0.88, 1.18, 3.2, 0.18, 0.36)
    # freedom board frame
    walnut.box(-21.4, 1.35, 1.0, 0.05, 1.06, 1.4); walnut.box(-21.4, 0.42, 0.4, 0.05, 0.85, 0.05); walnut.box(-21.4, 0.42, 1.6, 0.05, 0.85, 0.05)
    # globe stand and ladder
    brass.box(-21.3, 0.45, -9.2, 0.04, 0.9, 0.04); brass.box(-21.3, 0.02, -9.2, 0.4, 0.04, 0.4)
    lad = Builder('ladder', 'walnut_v', tile=1.0, lightmap=False, vcol=True, seg=0.4)
    for s in (-0.24, 0.24): lad.box(-26 + s, 1.7, -12.15 + 0.35, 0.04, 3.4, 0.04)
    y = 0.3
    while y < 3.3: lad.box(-26, y, -12.15 + 0.35, 0.5, 0.03, 0.03); y += 0.3
    lad.finish()
    walnut.finish(); tops.finish(); leather.finish(); brass.finish(); shade.finish(); bulb.finish()
    # globe
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.28, segments=32, ring_count=20, location=P(-21.3, 1.15, -9.2))
    g = bpy.context.active_object; g.name = 'globe'
    gm = material('globe_v', color=(0.16, 0.35, 0.48, 1), roughness=0.45); g.data.materials.append(gm)
    g.data.color_attributes.new(name='light', type='FLOAT_COLOR', domain='CORNER'); g['vc'] = 1
    for p in g.data.polygons: p.use_smooth = True
    # chandeliers, four of them, one to a quadrant and all clear of the laylight down the middle of the ceiling
    pd = Builder('pendants', 'brass_v', tile=1.0, lightmap=False, vcol=True, seg=0.3)
    pb = Builder('pendant_bulbs', 'bulb_e', tile=1.0, lightmap=False, vcol=False)
    for (px, pz) in [(-27.5, -9.0), (-18.0, -9.0), (-27.5, 3.2), (-18.0, 3.2)]:
        chandelier(pd, pb, px, pz)
        lights.append(('point', (px, 5.60, pz), (1.0, 0.88, 0.72), 200))
    pd.finish(); pb.finish()

HANG = 5.30   # the height the chandeliers' bodies hang at

def chandelier(pd, pb, px, pz):
    """A two-tier brass chandelier: a stem down from a ceiling rose, a turned body, six arms above and ten below,
    each sweeping out and up to a candle, and a hoop linking the lower ring. Replaces the plain ring of bulbs,
    which read as a hoop of dots from across the room rather than as a light fitting."""
    prism(pd, px, H - 0.10, pz, 0.27, 0.10, n=12, r_top=0.20)        # ceiling rose
    y = HANG + 0.66
    while y < H - 0.10 - 1e-6:                                       # stem, in segments for the vertex-colour bake
        h = min(0.5, H - 0.10 - y); prism(pd, px, y, pz, 0.035, h, n=8, cap_top=False, cap_bot=False); y += h
    turned(pd, px, HANG, pz, 0.66, 0.30, n=12)                       # the body
    prism(pd, px, HANG - 0.19, pz, 0.13, 0.19, n=12, r_top=0.03)     # the drop finial below it
    for (n, r, a_off, root_y, knee_y, cup_y, hoop) in ((6, 0.48, 0.0, 0.50, 0.34, 0.60, False),
                                                       (10, 0.78, 0.31, 0.16, -0.04, 0.22, True)):
        for k in range(n):
            a = 2 * math.pi * k / n + a_off
            ca, sa = math.cos(a), math.sin(a)
            root = (px + 0.13 * ca, HANG + root_y, pz + 0.13 * sa)
            knee = (px + r * 0.66 * ca, HANG + knee_y, pz + r * 0.66 * sa)
            tip = (px + r * ca, HANG + cup_y, pz + r * sa)
            bar(pd, root, knee, 0.038); bar(pd, knee, tip, 0.034)
            prism(pd, px + r * ca, HANG + cup_y, pz + r * sa, 0.055, 0.05, n=8, r_top=0.034)
            pb.box(px + r * ca, HANG + cup_y + 0.13, pz + r * sa, 0.05, 0.16, 0.05)
        if hoop:
            for k in range(n):
                a0 = 2 * math.pi * k / n + a_off; a1 = 2 * math.pi * (k + 1) / n + a_off
                bar(pd, (px + r * math.cos(a0), HANG + cup_y - 0.08, pz + r * math.sin(a0)),
                        (px + r * math.cos(a1), HANG + cup_y - 0.08, pz + r * math.sin(a1)), 0.028)

def build_piano(lights):
    """A grand piano in the open south-east corner: a curved case taken from a real plan outline, a lid propped
    open on its stick, three tapered legs, a full keyboard, a music desk and a stool."""
    px, pz = PIANO
    lac = Builder('piano', 'lacquer_v', tile=1.0, lightmap=False, vcol=True, seg=0.5)
    key = Builder('piano_keys', 'ivory_v', tile=1.0, lightmap=False, vcol=True)
    drk = Builder('piano_dark', 'dark_v', tile=1.0, lightmap=False, vcol=True, seg=0.4)
    br = Builder('piano_brass', 'brass_v', tile=1.0, lightmap=False, vcol=True, seg=0.4)
    ry = math.radians(45.0)                        # tail into the corner, keyboard turned out to the room
    cr, sr = math.cos(ry), math.sin(ry)
    def C3(u, y, v): return (px + u * cr + v * sr, y, pz - u * sr + v * cr)   # piano-local -> campus
    BW, BL, CY, CT = 1.50, 2.26, 0.62, 0.27        # case width, length, underside height, thickness
    out = [(-BW / 2, 0.0), (BW / 2, 0.0), (BW / 2, 0.42)]
    out += bezier((BW / 2, 0.42), (BW / 2 + 0.09, 1.52), (0.17, BL), 7)[1:]   # the treble side curving away
    out += [(-BW / 2, BL)]
    poly_prism(lac, out, px, CY, pz, CT, ry)
    # the lid, hinged along the bass side and propped open: the one silhouette that says 'grand piano'
    phi = math.radians(29.0); hy = CY + CT + 0.012   # the angle a real prop stick holds the lid at
    def LC(u, v, n=0.0):
        du = u + BW / 2
        return C3(-BW / 2 + du * math.cos(phi) + n * math.sin(phi), hy + du * math.sin(phi) - n * math.cos(phi), v)
    def L3(u, v, n=0.0): return P(*LC(u, v, n))
    cu = sum(p[0] for p in out) / len(out); cv = sum(p[1] for p in out) / len(out)
    lid_up = (L3(cu, cv) - L3(cu, cv, 1.0)).normalized()      # the lid's own up, since it is tilted
    lid_mid = L3(cu, cv, 0.012)
    for i in range(len(out)):
        a, b = out[i], out[(i + 1) % len(out)]
        lac.face([L3(cu, cv), L3(a[0], a[1]), L3(b[0], b[1])], lid_up)
        lac.face([L3(cu, cv, 0.024), L3(b[0], b[1], 0.024), L3(a[0], a[1], 0.024)], -lid_up)
        # the edge band faces out of the lid, not up: hinting it with +y let half the band flip and stripe
        edge = L3((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0.012) - lid_mid
        lac.face([L3(a[0], a[1]), L3(b[0], b[1]), L3(b[0], b[1], 0.024), L3(a[0], a[1], 0.024)],
                 edge.normalized() if edge.length > 1e-6 else lid_up)
    bar(br, C3(BW / 2 - 0.14, CY + CT, 1.00), LC(0.58, 1.00, 0.03), 0.022)    # the prop stick
    # legs, taper to the floor
    for (lu, lv) in ((-BW / 2 + 0.24, 0.26), (BW / 2 - 0.24, 0.26), (0.12, BL - 0.28)):
        p = C3(lu, 0.0, lv); prism(lac, p[0], 0.0, p[2], 0.075, CY, n=8, r_top=0.055)
        drk.box(p[0], 0.012, p[2], 0.17, 0.024, 0.17)                         # castor plate
    # keyboard: white keys across the full compass, black keys in the usual pattern, under a fallboard
    KW, NW = 0.0234, 52
    for i in range(NW):
        u = -(NW * KW) / 2 + (i + 0.5) * KW
        p = C3(u, 0, 0.115); key.box(p[0], CY + CT - 0.025, p[2], KW - 0.0022, 0.016, 0.145, ry)
        if i % 7 in (0, 1, 3, 4, 5) and i < NW - 1:
            q = C3(u + KW / 2, 0, 0.085); drk.box(q[0], CY + CT - 0.008, q[2], KW * 0.56, 0.018, 0.092, ry)
    p = C3(0, 0, 0.255); lac.box(p[0], CY + CT + 0.035, p[2], BW - 0.07, 0.10, 0.14, ry)        # fallboard
    p = C3(0, 0, 0.022); lac.box(p[0], CY + CT - 0.03, p[2], BW - 0.07, 0.05, 0.05, ry)         # key slip
    p = C3(0, 0, 0.40); lac.box(p[0], CY + CT + 0.22, p[2], BW - 0.42, 0.30, 0.02, ry)          # music desk
    # stool
    p = C3(0, 0, -0.66)
    lac.box(p[0], 0.56, p[2], 0.62, 0.05, 0.34, ry)
    for (du, dv) in ((-0.26, -0.12), (0.26, -0.12), (-0.26, 0.12), (0.26, 0.12)):
        q = C3(du, 0, -0.66 + dv); lac.box(q[0], 0.27, q[2], 0.045, 0.54, 0.045, ry)
    # this corner sits outside every chandelier's throw, so the piano is lit for itself
    lights.append(('point', (px - 0.3, 2.45, pz - 0.6), (1.0, 0.84, 0.62), 60))
    lac.finish(); key.finish(); drk.finish(); br.finish()

def add_lights(lights):
    for kind, (x, y, z), col, watts in lights:
        ld = bpy.data.lights.new('L', 'POINT'); ld.energy = watts; ld.color = col; ld.shadow_soft_size = 0.08
        ob = bpy.data.objects.new('L', ld); ob.location = P(x, y, z); bpy.context.scene.collection.objects.link(ob)
    # the sun through the arched window, from the west
    sd = bpy.data.lights.new('Sun', 'SUN'); sd.energy = 26.0; sd.angle = math.radians(1.5); sd.color = (1.0, 0.93, 0.84)
    sun = bpy.data.objects.new('Sun', sd); bpy.context.scene.collection.objects.link(sun)
    # direction the light travels: from -x (west) going +x, downwards 28 deg, slightly toward -z
    d = Vector((1.0, 0.30, -math.tan(math.radians(19)) * 1.044)).normalized()   # blender axes: +x east, +y = -campus z, -z down
    sun.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    # sky
    w = bpy.data.worlds.new('World'); bpy.context.scene.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes['Background']
    sky = nt.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'MULTIPLE_SCATTERING'; sky.sun_disc = False; sky.sun_elevation = math.radians(19); sky.sun_rotation = math.radians(90)
    sky.altitude = 300; sky.air_density = 1.0; sky.aerosol_density = 1.5
    nt.links.new(sky.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 1.0

# ---------------------------------------------------------------- lightmap uvs + baking
def select_only(obs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs: o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]

def lightmap_uvs(obs):
    for o in obs: o.data.uv_layers.active = o.data.uv_layers['lm']
    select_only(obs)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM', rotate=True, scale=True, merge_overlap=False, margin_method='FRACTION', margin=0.004, shape_method='AABB')
    bpy.ops.object.mode_set(mode='OBJECT')
    for o in obs: o.data.uv_layers.active = o.data.uv_layers['uv']

def bake_lightmap(obs):
    sc = bpy.context.scene
    img = bpy.data.images.new('lightmap', LM_SIZE, LM_SIZE, float_buffer=True, alpha=False)
    img.colorspace_settings.name = 'Non-Color'
    # every lightmapped material gets an active image node pointing at the atlas, on the lm uv
    for m in {o.data.materials[0] for o in obs}:
        nt = m.node_tree
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; n.name = 'LM_BAKE'; n.location = (0, 500)
        uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = 'lm'; uvn.location = (-200, 500)
        nt.links.new(uvn.outputs['UV'], n.inputs['Vector'])
        nt.nodes.active = n
    for o in obs: o.data.uv_layers.active = o.data.uv_layers['lm']
    sc.cycles.samples = SAMPLES_LM
    sc.cycles.bake_type = 'DIFFUSE'
    b = sc.render.bake
    b.use_pass_direct = True; b.use_pass_indirect = True; b.use_pass_color = False
    b.target = 'IMAGE_TEXTURES'; b.margin = 16 if LM_SIZE > 1024 else 10; b.margin_type = 'EXTEND'; b.use_clear = True
    select_only(obs)
    t = time.time(); print('baking lightmap', LM_SIZE, 'x', SAMPLES_LM, 'samples for', [o.name for o in obs], flush=True)
    bpy.ops.object.bake(type='DIFFUSE')
    print('lightmap baked in %.0f s' % (time.time() - t), flush=True)
    img.filepath_raw = os.path.join(OUT, 'lightmap.exr'); img.file_format = 'OPEN_EXR'; img.save()
    for o in obs: o.data.uv_layers.active = o.data.uv_layers['uv']
    for m in {o.data.materials[0] for o in obs}:
        nt = m.node_tree
        for n in [n for n in nt.nodes if n.name.startswith('LM_BAKE')]: nt.nodes.remove(n)

def bake_vertex_colors(obs):
    if np is None:
        raise RuntimeError('vertex-colour baking needs numpy; Blender\'s copy failed to import (see the note at the top). '
                           'Build with --ue/--nobake, or unblock Blender\'s numpy DLLs.')
    sc = bpy.context.scene
    sc.cycles.samples = SAMPLES_VC
    sc.cycles.bake_type = 'DIFFUSE'
    b = sc.render.bake
    b.use_pass_direct = True; b.use_pass_indirect = True; b.use_pass_color = False
    b.target = 'VERTEX_COLORS'
    for o in obs: o.data.color_attributes.active_color = o.data.color_attributes['light']
    select_only(obs)
    t = time.time(); print('baking vertex colors for', len(obs), 'objects', sum(len(o.data.loops) for o in obs), 'corners', flush=True)
    bpy.ops.object.bake(type='DIFFUSE')
    print('vertex colors baked in %.0f s' % (time.time() - t), flush=True)
    # scale to 0..1 for glTF
    for o in obs:
        ca = o.data.color_attributes['light']
        n = len(ca.data); buf = np.empty(n * 4, np.float32); ca.data.foreach_get('color', buf)
        buf = buf.reshape(-1, 4); buf[:, :3] = np.clip(buf[:, :3] / VC_SCALE, 0, 1); buf[:, 3] = 1
        ca.data.foreach_set('color', buf.ravel())

def render_probe():
    """Equirect reflection probe from the room centre (campus -22, 1.6, -3) -> probe.exr"""
    sc = bpy.context.scene
    cam = bpy.data.cameras.new('Probe'); cam.type = 'PANO'; cam.panorama_type = 'EQUIRECTANGULAR'
    co = bpy.data.objects.new('Probe', cam); sc.collection.objects.link(co)
    co.location = P(-22.0, 1.6, -3.0); co.rotation_euler = (math.radians(90), 0, math.radians(-90))
    sc.camera = co
    sc.render.resolution_x = 1024; sc.render.resolution_y = 512; sc.render.resolution_percentage = 100
    sc.cycles.samples = 32 if QUICK else 128
    sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '16'
    sc.view_settings.view_transform = 'Standard'
    sc.render.filepath = os.path.join(OUT, 'probe.exr')
    t = time.time(); bpy.ops.render.render(write_still=True); print('probe rendered in %.0f s' % (time.time() - t), flush=True)
    sc.view_settings.view_transform = 'AgX'

def render_preview(name, x, y, z, yaw, pitch, fov=70):
    """A Cycles still from a campus viewpoint (yaw 0 looks toward -z; yaw pi/2 looks toward -x)."""
    sc = bpy.context.scene
    cam = bpy.data.cameras.new('Cam' + name); cam.lens_unit = 'FOV'; cam.angle = math.radians(fov)
    co = bpy.data.objects.new('Cam' + name, cam); sc.collection.objects.link(co)
    co.location = P(x, y, z)
    # campus look direction
    dx, dz = -math.sin(yaw) * math.cos(pitch), -math.cos(yaw) * math.cos(pitch); dy = math.sin(pitch)
    d = Vector((dx, -dz, dy))
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.camera = co
    sc.render.resolution_x = 1280; sc.render.resolution_y = 800; sc.render.resolution_percentage = 100
    sc.cycles.samples = 24 if QUICK else 96
    sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 88
    sc.render.filepath = os.path.join(OUT, 'preview_%s.jpg' % name)
    t = time.time(); bpy.ops.render.render(write_still=True); print('preview', name, 'in %.0f s' % (time.time() - t), flush=True)

def render_look(name, eye, target, fov=70):
    """render_preview, but aimed at a point instead of by yaw and pitch: easier to keep honest when the thing
    you want in shot has a known position."""
    dx, dy, dz = target[0] - eye[0], target[1] - eye[1], target[2] - eye[2]
    flat = math.hypot(dx, dz)
    render_preview(name, eye[0], eye[1], eye[2], math.atan2(-dx, -dz), math.atan2(dy, flat), fov)

def export(path):
    sc = bpy.context.scene
    # glass and emissive panels: keep; lights/cameras: not exported
    obs = [o for o in sc.objects if o.type == 'MESH']
    select_only(obs)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLTF_SEPARATE', use_selection=True, export_apply=True,
                              export_texcoords=True, export_normals=True, export_materials='EXPORT', export_image_format='AUTO',
                              export_vertex_color='ACTIVE', export_all_vertex_colors=False, export_active_vertex_color_when_no_material=False,
                              export_yup=True, export_extras=True, export_lights=False, export_cameras=False, export_animations=False)
    print('exported', path, flush=True)

def main():
    t0 = time.time()
    sc = reset()
    setup_materials()
    lights = []
    info = build_shell()
    build_bookcases()
    build_rails()
    build_stair(lights)
    build_furniture(lights)
    build_piano(lights)
    add_lights(lights)
    obs = [o for o in sc.objects if o.type == 'MESH']
    if UE:
        # Unreal: give the shell real thickness (outward), so Lumen and distance fields see a closed volume
        for o in obs:
            if o.name in ('walls', 'floor', 'floor_dark', 'floor_light', 'ceiling'):
                m = o.modifiers.new('ue_thickness', 'SOLIDIFY'); m.thickness = 0.45; m.offset = -1.0; m.use_even_offset = True
    lm = [o for o in obs if o.get('lm')]; vc = [o for o in obs if o.get('vc')]
    print('objects', len(obs), 'lightmapped', [o.name for o in lm], 'vertex-lit', len(vc), 'tris', sum(len(o.data.polygons) * 2 for o in obs), 'built in %.0f s' % (time.time() - t0), flush=True)
    lightmap_uvs(lm)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'library.blend'))
    if RENDER:
        render_preview('window', -13.4, 1.62, -3, math.pi / 2, 0.08)
        render_preview('stacks', -22.0, 1.62, -2.0, math.pi * 0.75, -0.05)
        render_look('hall', (-12.7, 1.62, -3.0), (-31.0, 2.6, -3.0), fov=76)
        render_look('stair', (-18.4, 1.62, -5.2), (-15.1, 2.3, -9.6), fov=72)
        render_look('piano', (-18.9, 1.55, 0.9), (-15.4, 1.05, 3.3), fov=68)
        render_look('gallery', (-13.1, 5.30, -10.2), (-25.0, 2.2, -0.5), fov=80)
    if not NOBAKE:
        bake_lightmap(lm)
        bake_vertex_colors(vc)
        render_probe()
    export(os.path.join(OUT, 'lib_raw.gltf'))
    json.dump(dict(VC_SCALE=VC_SCALE, LM_SIZE=LM_SIZE, lm=[o.name for o in lm], vc=[o.name for o in vc]), open(os.path.join(OUT, 'meta.json'), 'w'))
    print('done in %.0f s' % (time.time() - t0), flush=True)

if __name__ == '__main__':
    main()
