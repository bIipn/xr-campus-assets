"""Find faces that would flicker in Unreal: two faces from different meshes lying in the same plane (within
1 cm) and overlapping in extent, like a hall wall built over a door reveal. Run on the prepared GLBs:

    python3 unreal/Pipeline/blender/find_flicker.py -- Museum ReadingRoom Outside [WaxHall School ...]

Prints one line per overlapping pair (object A, object B, plane, overlap area in m^2), biggest first, and exits
1 when any pair overlaps by more than MIN_AREA. Small meshes (props, books, letters) and hair-thin faces are
skipped: the flicker that matters is a wall or floor over another.
"""
import math
import os
import sys
from collections import defaultdict

import bpy
import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
OUT = os.path.join(REPO, 'unreal', 'Pipeline', 'out', 'ue')
MIN_AREA = 0.05            # m^2 of overlap worth reporting
PLANE_TOL = 0.0015         # m: two faces this close in their plane offset count as coplanar (1 cm apart never flickers)
MIN_FACE = 0.02            # m^2: faces smaller than this are ignored (trim, leaves, letters)
SKIP = ('M_books', 'M_leaf', 'leafcard', 'M_glow', 'item__', 'book__', 'token__', 'prop__', 'M_glass', 'M_bulb', 'M_shade')


def load(names):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    faces = []            # (asset, object, normal, offset, verts (3,3))
    for name in names:
        fp = os.path.join(OUT, name + '.glb')
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=fp)
        for ob in bpy.data.objects:
            if ob in before or ob.type != 'MESH' or any(s in ob.name for s in SKIP):
                continue
            me = ob.data
            if len(me.polygons) == 0:
                continue
            m = np.array(ob.matrix_world)
            co = np.array([v.co[:] for v in me.vertices], dtype=np.float64)
            co = co @ m[:3, :3].T + m[:3, 3]
            # glTF import is Blender Z-up already; keep Blender axes (x, y, z) for the geometry
            for p in me.polygons:
                idx = list(p.vertices)
                if len(idx) < 3:
                    continue
                tri = co[idx[:3]]
                n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
                ln = np.linalg.norm(n)
                if ln < 1e-9:
                    continue
                n /= ln
                area = p.area * abs(np.linalg.det(m[:3, :3])) ** (2 / 3)
                if area < MIN_FACE:
                    continue
                if n[2] < -0.9 and abs(tri[0][2]) < 0.002:
                    continue                      # the underside of something standing on the ground floor
                verts = co[idx]
                faces.append((name, ob.name, n, float(np.dot(n, tri[0])), verts, area))
    return faces


def plane_key(n, d):
    # the normal quantised to about 2 degrees, the offset to PLANE_TOL. Faces facing opposite ways (a shelf's
    # underside on a floor) never flicker, since only one of them ever faces the camera: same direction only.
    q = tuple(int(round(v * 30)) for v in n)
    return q, int(math.floor(d / PLANE_TOL))


def frame(n):
    a = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u = np.cross(n, a); u /= np.linalg.norm(u)
    v = np.cross(n, u)
    return u, v


def flat(verts, u, v):
    """The face's corners in a 2D frame of its plane, and their bounds."""
    pts = np.stack([verts @ u, verts @ v], axis=1)
    return pts, (pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max())


def ccw(poly):
    area = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]; x1, y1 = poly[(i + 1) % len(poly)]
        area += x0 * y1 - x1 * y0
    return poly if area >= 0 else poly[::-1]


def overlap_area(a, b):
    """Area of the intersection of two convex polygons (Sutherland-Hodgman: a clipped by b's edges)."""
    out = [tuple(p) for p in a]
    b = ccw([tuple(p) for p in b])
    for i in range(len(b)):
        if not out:
            return 0.0
        ex, ey = b[i]; fx, fy = b[(i + 1) % len(b)]
        def inside(p):
            return (fx - ex) * (p[1] - ey) - (fy - ey) * (p[0] - ex) >= -1e-12
        def cross(p, q):
            dx, dy = q[0] - p[0], q[1] - p[1]
            den = (fx - ex) * dy - (fy - ey) * dx
            if abs(den) < 1e-15:
                return q
            t = ((fx - ex) * (ey - p[1]) - (fy - ey) * (ex - p[0])) / den
            return (p[0] + t * dx, p[1] + t * dy)
        new = []
        prev = out[-1]
        for cur in out:
            if inside(cur):
                if not inside(prev):
                    new.append(cross(prev, cur))
                new.append(cur)
            elif inside(prev):
                new.append(cross(prev, cur))
            prev = cur
        out = new
    area = 0.0
    for i in range(len(out)):
        x0, y0 = out[i]; x1, y1 = out[(i + 1) % len(out)]
        area += x0 * y1 - x1 * y0
    return abs(area) / 2.0


def main(names):
    faces = load(names)
    print('faces considered:', len(faces), flush=True)
    buckets = defaultdict(list)
    for f in faces:
        q, k = plane_key(f[2], f[3])
        buckets[(q, k)].append(f)
        buckets[(q, k + 1)].append(f)          # a face near a bucket edge is checked against both neighbours
    # A face glued back to back onto another surface (a moulding's back against its wall) is never seen: it is
    # covered by a face in the same plane facing the other way. Such faces take no part in the pairing.
    hidden = set()
    for (q, k), group in buckets.items():
        back = tuple(-c for c in q)
        others = [f for kk in (-k - 2, -k - 1, -k, -k + 1) for f in buckets.get((back, kk), [])]
        if not others:
            continue
        u, v = frame(np.array(q, dtype=np.float64) / 30.0)
        flats = [flat(f[4], u, v) for f in group]
        oflats = [flat(f[4], u, v) for f in others]
        for i, fi in enumerate(group):
            if id(fi) in hidden:
                continue
            ri = flats[i][1]
            covered = 0.0
            for j, fj in enumerate(others):
                if abs(fi[3] + fj[3]) > PLANE_TOL:
                    continue
                rj = oflats[j][1]
                if min(ri[1], rj[1]) - max(ri[0], rj[0]) <= 0 or min(ri[3], rj[3]) - max(ri[2], rj[2]) <= 0:
                    continue
                covered += overlap_area(flats[i][0], oflats[j][0])
                if covered >= 0.9 * fi[5]:
                    hidden.add(id(fi))
                    break
    print('faces hidden back to back:', len(hidden), flush=True)

    pairs = {}
    biggest = {}
    for (q, k), group in buckets.items():
        if len(group) < 2:
            continue
        u, v = frame(np.array(q, dtype=np.float64) / 30.0)
        flats = [flat(f[4], u, v) for f in group]
        for i in range(len(group)):
            fi = group[i]
            if id(fi) in hidden:
                continue
            for j in range(i + 1, len(group)):
                fj = group[j]
                if id(fj) in hidden:
                    continue
                if fi[1] == fj[1] and fi[0] == fj[0]:
                    continue                                   # same material: two faces alike cannot flicker visibly
                if abs(fi[3] - fj[3]) > PLANE_TOL:
                    continue
                ri, rj = flats[i][1], flats[j][1]
                if min(ri[1], rj[1]) - max(ri[0], rj[0]) <= 0.02 or min(ri[3], rj[3]) - max(ri[2], rj[2]) <= 0.02:
                    continue                                   # bounds apart: no overlap
                area = overlap_area(flats[i][0], flats[j][0])
                if area < 0.0004:
                    continue                                   # touching along an edge, or a sliver
                key = tuple(sorted(((fi[0], fi[1]), (fj[0], fj[1]))))
                pairs[key] = pairs.get(key, 0.0) + area
                centre = (fi[4].mean(axis=0) + fj[4].mean(axis=0)) / 2
                if area > biggest.get(key, (0.0, None))[0]:
                    biggest[key] = (area, centre, fi[2])
    rows = sorted(pairs.items(), key=lambda kv: -kv[1])
    bad = 0
    for (a, b), area in rows:
        if area < MIN_AREA:
            continue
        bad += 1
        big, centre, n = biggest[(a, b)]
        # Blender axes (x, y, z) -> campus metres (x east, y up, z south) = (x, z, -y)
        print('FLICKER %7.2f m^2  %s/%s  with  %s/%s   largest piece %.2f m^2 at campus (%.1f, %.1f, %.1f) facing (%.1f, %.1f, %.1f)'
              % (area, a[0], a[1], b[0], b[1], big, centre[0], centre[2], -centre[1], n[0], n[2], -n[1]))
    print('%d overlapping pairs over %.2f m^2' % (bad, MIN_AREA))
    return 1 if bad else 0


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    sys.exit(main(args or ['Museum', 'ReadingRoom', 'Outside']))
