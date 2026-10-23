"""Find pictures that a wall, a pilaster or anything else covers: framed exhibits, posters, signs, book covers, any
flat picture on a wall. Run on the prepared GLBs:

    python3 unreal/Pipeline/blender/find_buried.py -- Museum School Classroom ReadingRoom LibraryShell [...]

A picture is a flat, upright face group (a quad or a few faces in one plane) of 0.02 to 8 m^2. From a grid of points
on its face, a ray goes out along the face's front normal; anything another mesh puts within REACH in front of a
point covers it (glass is let through). Prints one line per picture with any covered points, worst first: the
asset, the object, the covered share, the coverer(s) and where the picture is (campus metres and Unreal cm), then
exits 1 when any picture is more than MAX_COVER covered.
"""
import os
import sys
from collections import Counter, defaultdict

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
OUT = os.path.join(REPO, 'unreal', 'Pipeline', 'out', 'ue')
REACH = 0.30            # m in front of the face that has to be clear
EPS = 0.002             # m: rays start this far off the face
GRID = 7                # points along each side of a picture
MAX_COVER = 0.05        # a picture more than 5 % covered fails
MIN_AREA, MAX_AREA = 0.02, 8.0
SEE_THROUGH = ('glass', 'Glass', 'leafcard', 'M_glow')


def group_of(name):
    """item__mission_2 -> item__mission: the parts of one framed piece don't cover each other."""
    base = name.split('.')[0]
    for pre in ('item__', 'book__', 'token__', 'prop__'):
        if base.startswith(pre):
            parts = base[len(pre):].split('_')
            while parts and parts[-1].isdigit():
                parts.pop()
            return pre + '_'.join(parts)
    return base


def load(names):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs = []
    for name in names:
        fp = os.path.join(OUT, name + '.glb')
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=fp)
        for ob in bpy.data.objects:
            if ob not in before and ob.type == 'MESH' and len(ob.data.polygons):
                objs.append((name, ob))
    return objs


def world_mesh(ob):
    m = ob.matrix_world
    verts = [m @ v.co for v in ob.data.vertices]
    polys = [tuple(p.vertices) for p in ob.data.polygons]
    return verts, polys


def material_names(ob):
    return [s.material.name for s in ob.material_slots if s.material]


def planar_groups(ob, verts):
    """The object's faces gathered by plane (normal and offset), upright ones only, each with its area."""
    groups = defaultdict(list)
    for p in ob.data.polygons:
        vs = [verts[i] for i in p.vertices]
        n = (vs[1] - vs[0]).cross(vs[2] - vs[0])
        if n.length < 1e-9:
            continue
        n.normalize()
        if abs(n.z) > 0.25:
            continue                                   # Blender Z is up: floors, ceilings and table tops are no pictures
        key = (round(n.x, 2), round(n.y, 2), round(n.z, 2), round(n.dot(vs[0]), 2))
        groups[key].append((p, vs, n))
    return groups


def sample(vs_list, n):
    """Points on the faces of one plane group: a GRID x GRID raster over its extent, kept when inside a face."""
    pts = [v for vs in vs_list for v in vs]
    a = Vector((1, 0, 0)) if abs(n.x) < 0.9 else Vector((0, 1, 0))
    u = n.cross(a).normalized(); w = n.cross(u)
    us = [p.dot(u) for p in pts]; ws = [p.dot(w) for p in pts]
    u0, u1, w0, w1 = min(us), max(us), min(ws), max(ws)
    d = pts[0].dot(n)
    out = []
    for i in range(GRID):
        for j in range(GRID):
            uu = u0 + (u1 - u0) * (i + 0.5) / GRID
            ww = w0 + (w1 - w0) * (j + 0.5) / GRID
            q = u * uu + w * ww + n * d
            for vs in vs_list:
                if inside(q, vs, n):
                    out.append(q)
                    break
    return out, (u1 - u0, w1 - w0)


def inside(q, vs, n):
    k = len(vs)
    sign = 0
    for i in range(k):
        e = vs[(i + 1) % k] - vs[i]
        c = e.cross(q - vs[i]).dot(n)
        if abs(c) < 1e-9:
            continue
        s = 1 if c > 0 else -1
        if sign == 0:
            sign = s
        elif s != sign:
            return False
    return True


def main():
    names = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['Museum']
    objs = load(names)
    # one BVH per object, so a hit can be told apart by who made it
    trees = []
    for (asset, ob) in objs:
        verts, polys = world_mesh(ob)
        mats = ' '.join(material_names(ob))
        if any(s in ob.name or s in mats for s in SEE_THROUGH):
            continue
        lo = Vector((min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts)))
        hi = Vector((max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts)))
        trees.append((asset, ob.name, group_of(ob.name), BVHTree.FromPolygons(verts, polys, epsilon=0.0), lo, hi))
    print('meshes', len(trees))
    rows = []
    for (asset, ob) in objs:
        verts, _ = world_mesh(ob)
        if len(ob.data.polygons) > 40:
            continue                                   # a picture is a few faces, not a wall or a statue
        mine = group_of(ob.name)
        for key, faces in planar_groups(ob, verts).items():
            area = sum(f[0].area for f in faces) * ob.matrix_world.to_scale().x ** 2
            if area < MIN_AREA or area > MAX_AREA:
                continue
            n = faces[0][2]
            pts, (wu, ww) = sample([f[1] for f in faces], n)
            if not pts:
                continue
            covered = 0
            by = Counter()
            for q in pts:
                start = q + n * EPS
                hit_by = None; best = REACH
                for (a2, nm, grp, tree, lo, hi) in trees:
                    if grp == mine:
                        continue
                    # cheap reject: the ray's box against the mesh's box
                    end = start + n * REACH
                    if (max(start.x, end.x) < lo.x - 1e-3 or min(start.x, end.x) > hi.x + 1e-3 or
                            max(start.y, end.y) < lo.y - 1e-3 or min(start.y, end.y) > hi.y + 1e-3 or
                            max(start.z, end.z) < lo.z - 1e-3 or min(start.z, end.z) > hi.z + 1e-3):
                        continue
                    loc, nrm, idx, dist = tree.ray_cast(start, n, best)
                    if loc is not None and dist < best:
                        best = dist; hit_by = nm
                if hit_by is not None:
                    covered += 1
                    by[hit_by] += 1
            if covered:
                c = sum(pts, Vector()) / len(pts)
                rows.append((covered / len(pts), asset, ob.name, len(pts), by.most_common(3), c, n, wu, ww))
    rows.sort(key=lambda r: -r[0])
    bad = 0
    for (share, asset, name, npts, by, c, n, wu, ww) in rows:
        # Blender (x, y, z) = campus (x, -z, y); Unreal cm = (100 x, 100 z, 100 y)
        cx, cy, cz = c.x, c.z, -c.y
        print('%5.1f%%  %-10s %-34s %.2f x %.2f m  campus (%.2f, %.2f, %.2f)  UE (%.0f, %.0f, %.0f)  front (%.2f, %.2f)  by %s' % (
            100 * share, asset, name[:34], wu, ww, cx, cy, cz, 100 * cx, 100 * cz, 100 * cy, n.x, -n.y,
            ', '.join('%s x%d' % (nm[:28], k) for nm, k in by)))
        if share > MAX_COVER:
            bad += 1
    print('pictures covered over %d%%: %d' % (round(100 * MAX_COVER), bad))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
