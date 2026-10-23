"""The figure a person is in a guided visit: how the others see the guide and each visitor (AWTACharacter's Figure).

A calm, abstract person rather than a mannequin: a long robe that flares a little at the hem, narrow at the waist,
broader over the chest and shoulders, arms at the sides (the hands in the head's warm neutral), a short neck, an
egg-shaped head and a headset visor across the eyes (this is an XR library), with a strap round the back. The figure is drawn in one colour per person (AWTAPlayerState::GetVisitColor); the head
is a warm neutral, the visor dark glass, the collar ring brass on the guide.

Meshes (each its own tagged mesh, figure__<part>; nothing is placed in the level, AWTACharacter loads them):
  figure__body     standing: the floor at z 0, the neck's top at 1.55 m (the head's joint at 1.50 m)
  figure__seated   seated: the seat's top at z 0 (the figure root puts it 45 cm up), the torso, a lap and the shins
                   down to 40 cm under the seat; the neck's top at 0.673 m, the head's joint at 0.63 m
  figure__head     the joint (where the neck pitches it) at z 0, the eyes 12 cm over it, the crown at 0.256 m
  figure__visor    the headset's visor round the front of the head at the eyes and its strap round the back
  figure__collar   a ring round the neck's base, centred on z 0: placed 3.4 cm under the head's joint
Forward is +x (Unreal's +X), up +z; the cross-sections are ellipses, deeper than wide only in the head.
The eye height matches AWTACharacter::EyeHeight (162 cm standing) and SeatEyeHeight (75 cm over the seat).

Usage (Blender 5.2 or bpy 5.2.2):   python bl/figure.py [--render]
Writes unreal/Pipeline/out/people/People.glb (and assets/people/preview.png with --render).
Then: python unreal/Pipeline/blender/prepare_for_unreal.py -- People
"""
import math
import os
import sys

import bpy
import bmesh                                                     # noqa: E402  (bpy first: it provides bmesh)
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.abspath(os.path.join(HERE, '..'))
PIPE = os.path.join(SP, 'unreal', 'Pipeline', 'out', 'people')
OUT = os.path.join(SP, 'assets', 'people')
RENDER = '--render' in sys.argv
os.makedirs(PIPE, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

N = 48                      # segments round the body and the head
DEPTH = 0.74                # the body's depth over its width (a person is wider than deep)
HEAD_DEPTH = 1.06           # the head is a little deeper than wide

# --- profiles: (z, r) bottom to top, metres -------------------------------------------------------------------------
# Standing: a robe that narrows from the hem to the waist (0.95 m), a chest and shoulders broader than the hem (the
# shoulder points at 1.36 m, 44 cm across), the shoulders rolling over to a short neck (its base at 1.483 m); the chin
# rests at the head's joint (1.50 m), the eyes 12 cm over it at 1.62 m.
BODY = [
    (0.000, 0.000), (0.000, 0.190), (0.008, 0.201), (0.022, 0.206), (0.045, 0.205), (0.100, 0.200),
    (0.300, 0.186), (0.550, 0.172), (0.800, 0.160), (0.950, 0.152), (1.050, 0.158), (1.150, 0.176),
    (1.240, 0.198), (1.310, 0.213), (1.360, 0.219), (1.398, 0.215), (1.430, 0.200), (1.455, 0.170),
    (1.468, 0.130), (1.476, 0.090), (1.480, 0.066), (1.483, 0.056), (1.545, 0.050), (1.550, 0.000),
]
# Seated: hips on the seat (z 0), then the standing body from the waist up, a little shorter, so the neck's top is
# 0.673 m over the seat and the head's joint 0.63 m (the eyes 75 cm over the seat, SeatEyeHeight).
SEAT_SQUASH = 0.93
SEATED = [(0.000, 0.000), (0.000, 0.168), (0.012, 0.181), (0.035, 0.186), (0.070, 0.180), (0.100, 0.165)] + \
         [(0.12 + (z - 0.95) * SEAT_SQUASH, r) for (z, r) in BODY if z >= 0.95]
HEAD_JOINT_STANDING = 1.50
HEAD_JOINT_SEATED = 0.63

HEAD_C, HEAD_H, HEAD_R = 0.128, 0.130, 0.100      # the head's centre over the joint, half height, radius


def head_profile(rings=28):
    pts = [(HEAD_C - HEAD_H, 0.0)]
    for i in range(1, rings):
        a = -math.pi / 2 + math.pi * i / rings
        s = math.sin(a)
        taper = 1.0 - 0.13 * max(0.0, -s) ** 1.6         # a narrower chin: an egg, the small end down
        crown = 1.0 - 0.03 * max(0.0, s) ** 3            # a slightly flatter crown
        pts.append((HEAD_C + HEAD_H * s * crown, HEAD_R * math.cos(a) * taper))
    pts.append((HEAD_C + HEAD_H * 0.97, 0.0))
    return pts


def head_radius_at(z):
    """The head's radius (sideways) at height z over the joint, from its profile."""
    prof = head_profile(64)
    for (z0, r0), (z1, r1) in zip(prof, prof[1:]):
        if z0 <= z <= z1:
            t = 0.0 if z1 == z0 else (z - z0) / (z1 - z0)
            return r0 + (r1 - r0) * t
    return 0.0


# --- mesh helpers ------------------------------------------------------------------------------------------------------
def new_object(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def lathe(bm, prof, sx=1.0, sy=1.0, z0=0.0, n=N, uv=None):
    """Spin [(z, r)] round the vertical axis with the section an ellipse (sx forward, sy sideways). Profile points at
    r = 0 become single poles (caps)."""
    rings = []
    for (z, r) in prof:
        if r <= 1e-9:
            rings.append([bm.verts.new((0.0, 0.0, z0 + z))])
        else:
            rings.append([bm.verts.new((r * sx * math.cos(2 * math.pi * i / n), r * sy * math.sin(2 * math.pi * i / n), z0 + z))
                          for i in range(n)])
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for i in range(n):
                bm.faces.new((a[0], b[i], b[(i + 1) % n]))
        elif len(b) == 1:
            for i in range(n):
                bm.faces.new((a[i], b[0], a[(i + 1) % n]))
        else:
            for i in range(n):
                bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


def rounded_box(bm, x0, x1, y0, y1, z0, z1, radius, segs=4):
    """A box with every edge rounded (a bevelled cube)."""
    tmp = bmesh.new()
    bmesh.ops.create_cube(tmp, size=1.0)
    for v in tmp.verts:
        v.co = Vector(((x0 + x1) / 2 + v.co.x * (x1 - x0), (y0 + y1) / 2 + v.co.y * (y1 - y0), (z0 + z1) / 2 + v.co.z * (z1 - z0)))
    bmesh.ops.bevel(tmp, geom=list(tmp.edges) + list(tmp.verts), offset=radius, segments=segs, profile=0.5, affect='EDGES')
    me = bpy.data.meshes.new('_tmp')
    tmp.to_mesh(me)
    tmp.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)


def limb(bm, pts, radii, skin_from, n=20, per_seg=7):
    """A smooth arm through pts (Catmull-Rom) with the radius at each point, rounded caps at both ends. Segments from
    the point index skin_from on are the hand (material slot 1, the head's neutral); the rest is the sleeve."""
    P = [Vector(p) for p in pts]
    ext = [2 * P[0] - P[1]] + P + [2 * P[-1] - P[-2]]
    centres, rads, seg_of = [], [], []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        last = i == len(P) - 2
        for k in range(per_seg + (1 if last else 0)):
            t = k / per_seg
            c = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
            centres.append(c)
            rads.append(radii[i] + (radii[i + 1] - radii[i]) * (t * t * (3 - 2 * t)))
            seg_of.append(i)
    m = len(centres)
    tangents = [(centres[min(k + 1, m - 1)] - centres[max(k - 1, 0)]).normalized() for k in range(m)]
    ref = Vector((1.0, 0.0, 0.0)) if abs(tangents[0].x) < 0.9 else Vector((0.0, 1.0, 0.0))
    normal = (ref - tangents[0] * ref.dot(tangents[0])).normalized()
    frames = []
    for k in range(m):
        normal = (normal - tangents[k] * normal.dot(tangents[k])).normalized()
        frames.append((normal, tangents[k].cross(normal)))

    def ring(c, r, nrm, bin_):
        return [bm.verts.new(c + r * (math.cos(2 * math.pi * j / n) * nrm + math.sin(2 * math.pi * j / n) * bin_)) for j in range(n)]

    rings = [ring(centres[k], rads[k], *frames[k]) for k in range(m)]
    faces = []
    for k in range(m - 1):
        for j in range(n):
            f = bm.faces.new((rings[k][j], rings[k][(j + 1) % n], rings[k + 1][(j + 1) % n], rings[k + 1][j]))
            f.material_index = 1 if seg_of[k] >= skin_from else 0
            faces.append(f)
    # rounded ends: a quarter circle of rings closing to a pole, out along the tangent
    for end, sign in ((0, -1.0), (m - 1, 1.0)):
        c, r, (nrm, bin_), t = centres[end], rads[end], frames[end], tangents[end]
        prev = rings[end]
        mat = 1 if (end == m - 1 and seg_of[end] >= skin_from) else 0
        for q in range(1, 4):
            phi = math.radians(90.0 * q / 4)
            cur = ring(c + t * sign * r * math.sin(phi), r * math.cos(phi), nrm, bin_)
            for j in range(n):
                f = bm.faces.new((prev[j], prev[(j + 1) % n], cur[(j + 1) % n], cur[j]))
                f.material_index = mat
                faces.append(f)
            prev = cur
        pole = bm.verts.new(c + t * sign * r)
        for j in range(n):
            f = bm.faces.new((prev[j], prev[(j + 1) % n], pole))
            f.material_index = mat
            faces.append(f)
    bmesh.ops.recalc_face_normals(bm, faces=faces)


def arms(bm, pts, radii, skin_from):
    """Both arms: pts given for the left (+y) one, mirrored for the right."""
    limb(bm, pts, radii, skin_from)
    limb(bm, [(x, -y, z) for (x, y, z) in pts], radii, skin_from)


def material(name, color, roughness):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    return m


# --- the parts -----------------------------------------------------------------------------------------------------------
# The arms hang at the sides, a hand's breadth clear of the waist; seated, the forearms rest on the lap.
ARM_RADII = [0.053, 0.041, 0.032, 0.037, 0.025]                 # shoulder, elbow, wrist, palm, fingertips
ARM_STANDING = [(0.000, 0.192, 1.318), (0.015, 0.236, 1.045), (0.045, 0.229, 0.815), (0.054, 0.225, 0.762), (0.062, 0.219, 0.700)]
ARM_SEATED = [(0.000, 0.192, 0.462), (0.030, 0.238, 0.205), (0.235, 0.172, 0.168), (0.290, 0.152, 0.160), (0.345, 0.135, 0.152)]


def build_body(mat, skin):
    bm = bmesh.new()
    lathe(bm, BODY, sx=DEPTH)
    arms(bm, ARM_STANDING, ARM_RADII, 2)
    ob = new_object('figure__body', bm)
    ob.data.materials.append(mat)
    ob.data.materials.append(skin)
    return ob


def build_seated(mat, skin):
    bm = bmesh.new()
    lathe(bm, SEATED, sx=DEPTH)
    arms(bm, ARM_SEATED, ARM_RADII, 2)
    # the lap (both thighs as one, under the robe) and the shins down to the floor, a little narrower
    rounded_box(bm, 0.00, 0.43, -0.155, 0.155, 0.0, 0.130, 0.055)
    # the robe falls from the knees to the floor, flaring a little toward the hem
    drape = bmesh.new()
    rounded_box(drape, 0.335, 0.455, -0.145, 0.145, -0.40, 0.07, 0.045, segs=5)
    for v in drape.verts:
        f = min(1.0, max(0.0, (0.06 - v.co.z) / 0.46)) ** 1.4
        v.co.x = 0.395 + (v.co.x - 0.395) * (1.0 + 0.30 * f)
        v.co.y = v.co.y * (1.0 + 0.14 * f)
    me = bpy.data.meshes.new('_drape'); drape.to_mesh(me); drape.free(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    ob = new_object('figure__seated', bm)
    ob.data.materials.append(mat)
    ob.data.materials.append(skin)
    return ob


def build_head(mat):
    bm = bmesh.new()
    lathe(bm, head_profile(), sx=HEAD_DEPTH)
    ob = new_object('figure__head', bm)
    ob.data.materials.append(mat)
    return ob


def build_visor(mat):
    """A goggle band round the front of the head at the eyes (dark glass) and a strap round the back."""
    bm = bmesh.new()

    def shell(a0, a1, z0, z1, off_in, off_out, bulge, steps, shrink_ends):
        """A curved band on the head from angle a0 to a1 (0 = forward), height z0..z1 over the joint, standing off
        the head by off_in (its back) to off_out (its face) plus bulge * cos(a)^2 at the front."""
        zc = (z0 + z1) / 2
        grid_out, grid_in = [], []
        rows = 6
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            h = 1.0
            if shrink_ends:
                edge = min(a - a0, a1 - a) / math.radians(16.0)
                h = 0.62 + 0.38 * min(1.0, max(0.0, edge)) ** 0.5
            col_out, col_in = [], []
            for j in range(rows + 1):
                t = j / rows
                z = zc + (z0 - zc + (z1 - z0) * t) * h
                r = head_radius_at(z)
                fo = off_out + bulge * max(0.0, math.cos(a)) ** 2
                # round the band's top and bottom edges: the face meets the back in a curve
                k = math.sin(math.pi * t) ** 0.35
                ro = r + off_in + (fo - off_in) * k
                ri = r + off_in
                col_out.append(bm.verts.new(((ro) * HEAD_DEPTH * math.cos(a), ro * math.sin(a), z)))
                col_in.append(bm.verts.new(((ri) * HEAD_DEPTH * math.cos(a), ri * math.sin(a), z)))
            grid_out.append(col_out)
            grid_in.append(col_in)
        for i in range(steps):
            for j in range(rows):
                bm.faces.new((grid_out[i][j], grid_out[i + 1][j], grid_out[i + 1][j + 1], grid_out[i][j + 1]))
                bm.faces.new((grid_in[i][j + 1], grid_in[i + 1][j + 1], grid_in[i + 1][j], grid_in[i][j]))
        for i in range(steps):           # the top and bottom edges join the face to the back
            bm.faces.new((grid_out[i][rows], grid_out[i + 1][rows], grid_in[i + 1][rows], grid_in[i][rows]))
            bm.faces.new((grid_in[i][0], grid_in[i + 1][0], grid_out[i + 1][0], grid_out[i][0]))
        for i in (0, steps):             # the two ends
            for j in range(rows):
                bm.faces.new((grid_out[i][j], grid_out[i][j + 1], grid_in[i][j + 1], grid_in[i][j]))

    eye = 0.122
    shell(math.radians(-80.0), math.radians(80.0), eye - 0.029, eye + 0.029, 0.002, 0.009, 0.012, 40, True)
    shell(math.radians(78.0), math.radians(282.0), eye - 0.014, eye + 0.014, 0.001, 0.007, 0.0, 40, False)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = new_object('figure__visor', bm)
    ob.data.materials.append(mat)
    return ob


def build_collar(mat):
    """A ring round the neck's base, over the shoulders' dome (brass on the guide)."""
    bm = bmesh.new()
    R, rt, n, m = 0.064, 0.0105, 48, 14
    rings = []
    for i in range(n):
        a = 2 * math.pi * i / n
        ring = []
        for j in range(m):
            b = 2 * math.pi * j / m
            rr = R + rt * math.cos(b)
            ring.append(bm.verts.new((rr * DEPTH * 1.06 * math.cos(a), rr * math.sin(a), rt * math.sin(b))))
        rings.append(ring)
    for i in range(n):
        for j in range(m):
            a, b = rings[i], rings[(i + 1) % n]
            bm.faces.new((a[j], b[j], b[(j + 1) % m], a[(j + 1) % m]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = new_object('figure__collar', bm)
    ob.data.materials.append(mat)
    return ob


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    cloth = material('fig_cloth', (0.24, 0.48, 0.69, 1.0), 0.62)
    skin = material('fig_head', (0.72, 0.64, 0.52, 1.0), 0.55)
    glass = material('fig_visor', (0.02, 0.025, 0.025, 1.0), 0.18)
    brass = material('fig_brass', (0.62, 0.45, 0.18, 1.0), 0.35)
    parts = [build_body(cloth, skin), build_seated(cloth, skin), build_head(skin), build_visor(glass), build_collar(brass)]
    for ob in parts:
        print('%-16s %6d tris  z %.3f .. %.3f' % (ob.name, sum(len(p.vertices) - 2 for p in ob.data.polygons),
              min(v.co.z for v in ob.data.vertices), max(v.co.z for v in ob.data.vertices)), flush=True)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in parts:
        ob.select_set(True)
    fp = os.path.join(PIPE, 'People.glb')
    bpy.ops.export_scene.gltf(filepath=fp, export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
                              export_texcoords=True, export_normals=True, export_materials='EXPORT',
                              export_vertex_color='NONE', export_lights=False, export_cameras=False)
    print('exported', fp, os.path.getsize(fp), 'bytes', flush=True)
    if RENDER:
        preview(parts, cloth, skin, brass)


def preview(parts, cloth, skin, brass):
    """Three figures side by side (standing, the guide, seated) for a look before Unreal."""
    sc = bpy.context.scene
    body, seated, head, visor, collar = parts
    guide_cloth = material('fig_cloth_guide', (0.62, 0.45, 0.18, 1.0), 0.55)
    placed = []
    for k, (dx, sitting, mat, with_collar) in enumerate([(-0.75, False, cloth, False), (0.0, False, guide_cloth, True), (0.75, True, cloth, False)]):
        b = (seated if sitting else body).copy(); b.data = b.data.copy(); b.data.materials[0] = mat
        sc.collection.objects.link(b)
        b.location = (0.0, dx, 0.45 if sitting else 0.0)
        joint = (0.45 + HEAD_JOINT_SEATED) if sitting else HEAD_JOINT_STANDING
        for part in (head, visor) + ((collar,) if with_collar else ()):
            c = part.copy(); sc.collection.objects.link(c)
            c.location = (0.0, dx, joint - (0.034 if part is collar else 0.0))
            placed.append(c)
        placed.append(b)
    for ob in parts:
        ob.hide_render = True
    floor = bpy.data.meshes.new('floor'); bmf = bmesh.new()
    bmesh.ops.create_grid(bmf, x_segments=1, y_segments=1, size=4.0); bmf.to_mesh(floor); bmf.free()
    fo = bpy.data.objects.new('floor', floor); sc.collection.objects.link(fo)
    fo.data.materials.append(material('fig_floor', (0.55, 0.53, 0.50, 1), 0.7))
    st = bmesh.new(); rounded_box(st, -0.22, 0.22, 0.53, 0.97, 0.0, 0.45, 0.02)   # a stool under the seated one
    me = bpy.data.meshes.new('stool'); st.to_mesh(me); st.free()
    so = bpy.data.objects.new('stool', me); sc.collection.objects.link(so)
    so.data.materials.append(material('fig_wood', (0.30, 0.18, 0.09, 1), 0.5))
    key = bpy.data.lights.new('key', 'AREA'); key.energy = 400; key.size = 2.0
    ko = bpy.data.objects.new('key', key); sc.collection.objects.link(ko)
    ko.location = (3.0, -2.5, 3.5); ko.rotation_euler = (Vector((0, 0, 1.0)) - ko.location).to_track_quat('-Z', 'Y').to_euler()
    fill = bpy.data.lights.new('fill', 'AREA'); fill.energy = 150; fill.size = 3.0
    fl = bpy.data.objects.new('fill', fill); sc.collection.objects.link(fl)
    fl.location = (2.0, 3.0, 2.0); fl.rotation_euler = (Vector((0, 0, 1.0)) - fl.location).to_track_quat('-Z', 'Y').to_euler()
    w = bpy.data.worlds.new('World'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.75, 0.78, 0.82, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
    cam = bpy.data.cameras.new('cam'); cam.lens = 50
    co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co)
    co.location = (4.2, -1.1, 1.45)
    co.rotation_euler = (Vector((0.0, 0.0, 0.95)) - co.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = co
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 64; sc.cycles.device = 'CPU'
    sc.render.resolution_x, sc.render.resolution_y = 1200, 800
    sc.render.filepath = os.path.join(OUT, 'preview.png')
    bpy.ops.render.render(write_still=True)
    print('preview', sc.render.filepath, flush=True)


if __name__ == '__main__':
    main()
