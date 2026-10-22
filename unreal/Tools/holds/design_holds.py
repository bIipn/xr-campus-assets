"""Design the Wax Hall holds: how a reenactor's hand closes on each prop (World/WTAWaxStageActor.cpp, the
FWaxGrip table) - numbers, not guesses.

Everything is in the stage's palm frame (PalmFrame): +X along the fingers from the wrist toward the middle
knuckle, +Y out of the palm on the thumb's side, +Z across the palm, the origin 7 cm along the fingers from the
wrist; centimetres; the right hand (the stage mirrors the left in Z). palm.json (probe_palm.py) holds the
MetaHuman body's finger joints in that frame from its reference pose, each with its own axes, and the props
are read from the prepared HandProps.glb (bl/props.py).

A joint turns about a rotation vector in its own frame (direction = axis, length = degrees), as
UWTAWaxAnimInstance::ApplyGrip applies it over the reference pose. The fingers are hinges: one axis per joint,
the hinge measured from the rig. The thumb's first joint turns freely (three numbers), its other two about
one measured axis.

The hold: the four fingers laid flat (solved so each finger's flesh top lies at FINGER_TOP = 2.5 cm out from
the palm bones), the prop lowered onto them (its lowest point over the fingers at FINGER_TOP), and the thumb
solved to press on the prop's top near its near edge without sinking into it (its flesh kept off the prop's
height field). The headset instead hangs by its top strap: the strap's tube lies across the flat fingers under
the thumb, and the stage turns the rest toward the world's down each frame.

    python3 unreal/Tools/holds/design_holds.py            prints the C++ table and writes holds.json
    python3 unreal/Tools/holds/design_holds.py --pictures also draws hold_<kind>.png beside this file

Needs numpy, scipy, trimesh and rtree (pip install).
"""
import json
import math
import os
import sys

import numpy as np
import trimesh
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
GLB = os.path.join(REPO, 'unreal', 'Pipeline', 'out', 'ue', 'HandProps.glb')

TIP = {"thumb": 2.6, "index": 2.3, "middle": 2.4, "ring": 2.3, "pinky": 2.0}        # cm beyond the last joint
RADIUS = {"thumb": 1.0, "index": 0.85, "middle": 0.85, "ring": 0.8, "pinky": 0.7}   # the flesh around the bone
FINGERS = ['index', 'middle', 'ring', 'pinky']
FINGER_TOP = 2.5

# the hinge each finger joint bends about, in its own frame (measured by the old probe_hands.py: the finger's
# direction crossed with the palm normal, expressed in the joint), and the thumb's second and third joints'
# hinge, found by search (it curls the thumb down and across the palm)
FINGER_AXES = [(0.10, 0.20, -0.97), (0.25, 0.37, -0.89), (0.0, 0.0, -1.0)]
THUMB_AXIS = (0.58, -0.58, -0.58)


# ---------------------------------------------------------------- vectors
def unit(a):
    n = math.sqrt(sum(c * c for c in a))
    return tuple(c / n for c in a) if n > 1e-9 else (0.0, 0.0, 0.0)

def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def add(a, b): return tuple(x + y for x, y in zip(a, b))
def mul(a, s): return tuple(x * s for x in a)
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def length(a): return math.sqrt(dot(a, a))

def rot(p, origin, axis, deg):
    """p turned about the line through origin along axis (unit) by deg."""
    r = sub(p, origin)
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    out = add(add(mul(r, c), mul(cross(axis, r), s)), mul(axis, dot(axis, r) * (1 - c)))
    return add(origin, out)

def fmt(p):
    return '(%5.1f, %5.1f, %5.1f)' % tuple(p)


# ---------------------------------------------------------------- the hand
class Hand:
    """The reference pose's finger joints and tips, posed by rotation vectors (forward kinematics)."""
    def __init__(self, side='r', path=os.path.join(HERE, 'palm.json')):
        data = json.load(open(path))
        hd = data['hands'][side]
        self.wrist = tuple(hd['wrist'])
        self.fingers = {}
        for name, joints in hd['fingers'].items():
            js = [{'bone': j['bone'], 'p': tuple(j['p']), 'axes': [tuple(a) for a in j['axes']]} for j in joints]
            last, prev = js[-1]['p'], js[-2]['p'] if len(js) > 1 else self.wrist
            tip = add(last, mul(unit(sub(last, prev)), TIP[name]))
            self.fingers[name] = (js, tip)

    @staticmethod
    def local_to_palm(joint, local):
        X, Y, Z = joint['axes']
        return unit(tuple(local[0] * X[i] + local[1] * Y[i] + local[2] * Z[i] for i in range(3)))

    def pose(self, finger, vectors):
        """Joint positions and the tip after turning joint j by rotation vector vectors[j] (degrees)."""
        js, tip = self.fingers[finger]
        pts = [j['p'] for j in js] + [tip]
        hinges, degs = [], []
        for j, v in zip(js, vectors):
            d = length(v)
            hinges.append(self.local_to_palm(j, unit(v)) if d > 1e-9 else (1.0, 0.0, 0.0))
            degs.append(d)
        for j in range(len(js)):
            if degs[j] < 1e-9:
                continue
            for k in range(j + 1, len(pts)):
                pts[k] = rot(pts[k], pts[j], hinges[j], degs[j])
            for k in range(j + 1, len(hinges)):
                hinges[k] = rot(hinges[k], (0, 0, 0), hinges[j], degs[j])
        return pts

    def samples(self, finger, vectors, per_seg=4):
        """Points along the finger's centre line from the knuckle to the tip."""
        pts = self.pose(finger, vectors)
        out = []
        for a, b in zip(pts[:-1], pts[1:]):
            for i in range(per_seg + 1):
                t = i / per_seg
                out.append(add(mul(a, 1 - t), mul(b, t)))
        return out


def finger_vectors(degs):
    return [tuple(c * d for c in unit(a)) for a, d in zip(FINGER_AXES, degs)]

def thumb_vectors(params):
    """params: the first joint's rotation vector (3) and the second and third joints' degrees about THUMB_AXIS."""
    return [tuple(params[:3]), tuple(c * params[3] for c in unit(THUMB_AXIS)), tuple(c * params[4] for c in unit(THUMB_AXIS))]


# ---------------------------------------------------------------- the props
class Placed:
    """A prop mesh in the palm: rotation R (columns = the prop's axes in palm space) and translation t."""
    _scene = None

    def __init__(self, kind, R=np.eye(3), t=(0.0, 0.0, 0.0)):
        if Placed._scene is None:
            Placed._scene = trimesh.load(GLB)
        parts = []
        for name, g in Placed._scene.geometry.items():
            if name == 'prop__' + kind or name.startswith('prop__' + kind + '_'):
                m = g.copy()
                v = m.vertices * 100.0
                m.vertices = np.stack([v[:, 0], v[:, 2], v[:, 1]], axis=1)    # glTF (x, y up, z) -> Unreal (X, Y, Z)
                parts.append(m)
        mesh = trimesh.util.concatenate(parts)
        self.R, self.t = np.asarray(R, dtype=float), np.asarray(t, dtype=float)
        mesh.vertices = (self.R @ mesh.vertices.T).T + self.t
        self.mesh = mesh

    def heights(self, xz, lo=-50.0):
        """The top surface's Y over each (x, z): the highest hit of a ray going down; lo where it misses."""
        xz = np.asarray(xz)
        origins = np.stack([xz[:, 0], np.full(len(xz), 60.0), xz[:, 1]], axis=1)
        dirs = np.tile([0.0, -1.0, 0.0], (len(xz), 1))
        locs, idx, _ = self.mesh.ray.intersects_location(origins, dirs, multiple_hits=True)
        out = np.full(len(xz), lo)
        for p, i in zip(locs, idx):
            out[i] = max(out[i], p[1])
        return out

    def bottom(self, region):
        """The lowest Y of the mesh inside the (x0, x1, z0, z1) region."""
        v = self.mesh.vertices
        x0, x1, z0, z1 = region
        sel = (v[:, 0] >= x0) & (v[:, 0] <= x1) & (v[:, 2] >= z0) & (v[:, 2] <= z1)
        return float(v[sel, 1].min() if sel.any() else v[:, 1].min())


FINGER_REGION = (1.5, 11.5, -4.0, 9.0)     # over the flat fingers


def rest_on_fingers(kind):
    """The prop lowered onto the flat fingers: its lowest point over them at FINGER_TOP."""
    p = Placed(kind)
    return Placed(kind, np.eye(3), (0.0, FINGER_TOP - p.bottom(FINGER_REGION), 0.0))


# ---------------------------------------------------------------- solving
def solve(cost, starts, bounds):
    best = None
    for start in starts:
        res = minimize(cost, np.array(start, dtype=float), method='Powell', bounds=bounds, options={'xtol': 0.05, 'ftol': 1e-6, 'maxfev': 20000})
        if best is None or res.fun < best.fun:
            best = res
    return best


def flat_fingers(hand):
    """Hinge degrees per finger laying its flesh top along Y = FINGER_TOP, never above."""
    out = {}
    for f in FINGERS:
        r = RADIUS[f]
        def cost(degs, f=f, r=r):
            c = 0.0
            for p in hand.samples(f, finger_vectors(degs))[2:]:
                d = (FINGER_TOP - r) - p[1]
                c += 40 * d * d if d < 0 else d * d
            return c + 0.002 * sum(x * x for x in degs)
        res = solve(cost, ((0, 0, 0), (-25, -15, 0), (-40, -30, -10)), ((-60, 95),) * 3)
        out[f] = tuple(res.x)
    return out


THUMB_BOUNDS = ((-90, 90), (-90, 90), (-90, 90), (0, 80), (0, 70))
THUMB_STARTS = ((-25, -33, -25, 10, 10), (-30, -40, -30, 30, 20), (-10, -40, -40, 20, 10), (-40, -20, -40, 40, 30), (0, 0, 0, 0, 0))


def thumb_on_top(hand, placed, target):
    """The thumb's tip at target with its flesh off the prop's top."""
    r = RADIUS['thumb']
    def cost(params):
        pts = hand.samples('thumb', thumb_vectors(params))
        c = length(sub(pts[-1], target)) ** 2
        hs = placed.heights(np.array([[p[0], p[2]] for p in pts[3:]]))
        for p, hgt in zip(pts[3:], hs):
            d = (p[1] - r) - hgt
            if d < 0:
                c += 40 * d * d
        return c + 0.0005 * sum(x * x for x in params)
    return solve(cost, THUMB_STARTS, THUMB_BOUNDS)


def thumb_clear_of(hand, placed, target):
    """The thumb's tip at target with its flesh clear of the mesh (for a prop beside the thumb, not under it)."""
    r = RADIUS['thumb']
    def cost(params):
        pts = hand.samples('thumb', thumb_vectors(params))
        c = length(sub(pts[-1], target)) ** 2
        _, dist, _ = trimesh.proximity.closest_point(placed.mesh, np.array(pts[3:]))
        for d in dist:
            e = d - r
            if e < 0:
                c += 40 * e * e
        return c + 0.0005 * sum(x * x for x in params)
    return solve(cost, THUMB_STARTS, THUMB_BOUNDS)


# ---------------------------------------------------------------- output
def cpp_vector(v):
    return 'FVector(%.1f, %.1f, %.1f)' % tuple(v)


def draw(name, hand, placed, flat, thumb, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(12, 5))
    for k, (ax_a, ax_b, lab) in enumerate(((0, 1, 'side: X fingers, Y out of palm'), (0, 2, 'top: X fingers, Z across'), (2, 1, 'end: Z across, Y out of palm'))):
        ax = fig.add_subplot(1, 3, k + 1)
        v = placed.mesh.vertices
        ax.scatter(v[:, ax_a], v[:, ax_b], s=1, c='tab:blue', alpha=0.4)
        for f in FINGERS:
            pts = hand.pose(f, finger_vectors(flat[f]))
            ax.plot([p[ax_a] for p in pts], [p[ax_b] for p in pts], '-o', c='tab:orange', lw=3, ms=3)
        pts = hand.pose('thumb', thumb_vectors(thumb))
        ax.plot([p[ax_a] for p in pts], [p[ax_b] for p in pts], '-o', c='tab:red', lw=3, ms=3)
        ax.plot([-7], [0], 'k^')
        ax.set_aspect('equal'); ax.grid(True, alpha=0.3); ax.set_title('%s %s' % (name, lab), fontsize=8)
        ax.set_xlim(-12, 26); ax.set_ylim(-6, 26) if ax_b == 1 else ax.set_ylim(-14, 18)
    fig.tight_layout(); fig.savefig(path, dpi=80); plt.close(fig)


def main():
    pictures = '--pictures' in sys.argv
    hand = Hand('r')
    flat = flat_fingers(hand)
    print('// the fingers laid flat (index, middle, ring, little): rotation vectors in degrees per joint')
    for f in FINGERS:
        vs = finger_vectors(flat[f])
        top = max(p[1] + RADIUS[f] for p in hand.samples(f, vs)[2:])
        print('   { %s },   // %s, flesh top at %.2f' % (', '.join(cpp_vector(v) for v in vs), f, top))
    out = {'flat': {f: list(flat[f]) for f in FINGERS}}

    print('// each prop resting on them, the thumb on its top')
    for kind in ('phone', 'tablet', 'clipboard', 'book'):
        placed = rest_on_fingers(kind)
        top = float(placed.heights(np.array([[3.5, -0.5]]))[0])
        res = thumb_on_top(hand, placed, (3.5, top + RADIUS['thumb'], -0.5))
        thumb = tuple(res.x)
        pts = hand.samples('thumb', thumb_vectors(thumb))
        hs = placed.heights(np.array([[p[0], p[2]] for p in pts[3:]]))
        gap = min(p[1] - RADIUS['thumb'] - hgt for p, hgt in zip(pts[3:], hs))
        print('   %-10s lift %.2f  thumb { %s }   // tip %s, top under it %.2f, flesh gap %.2f' % (
            kind, placed.t[1], ', '.join(cpp_vector(v) for v in thumb_vectors(thumb)), fmt(pts[-1]), top, gap))
        out[kind] = {'lift': float(placed.t[1]), 'thumb': [list(v) for v in thumb_vectors(thumb)]}
        if pictures:
            draw(kind, hand, placed, flat, thumb, os.path.join(HERE, 'hold_%s.png' % kind))

    # the headset: its top strap's top point (12 cm behind the visor, 10.6 above the band) lies across the
    # flat fingers under the thumb; here the body hangs out of the palm (+Y), the palm-down carry
    Xh, Zh = (0.0, 0.0, 1.0), (0.0, -1.0, 0.0)
    Yh = cross(Zh, Xh)
    R = np.stack([Xh, Yh, Zh], axis=1)
    grip = np.array([-12.0, 0.0, 10.6])
    tube = np.array([3.0, FINGER_TOP + 0.85, 1.0])
    placed = Placed('headset', R, tube - R @ grip)
    res = thumb_clear_of(hand, placed, (3.8, float(tube[1]) + 0.85 + RADIUS['thumb'], -0.6))
    thumb = tuple(res.x)
    pts = hand.samples('thumb', thumb_vectors(thumb))
    _, dist, _ = trimesh.proximity.closest_point(placed.mesh, np.array(pts[3:]))
    print('   %-10s tube %s  thumb { %s }   // tip %s, flesh gap %.2f' % (
        'headset', fmt(tube), ', '.join(cpp_vector(v) for v in thumb_vectors(thumb)), fmt(pts[-1]), dist.min() - RADIUS['thumb']))
    for f in FINGERS:
        _, dist, _ = trimesh.proximity.closest_point(placed.mesh, np.array(hand.samples(f, finger_vectors(flat[f]), per_seg=6)))
        print('      %-6s clear of the strap by %.2f' % (f, dist.min() - RADIUS[f]))
    out['headset'] = {'tube': tube.tolist(), 'grip': grip.tolist(), 'thumb': [list(v) for v in thumb_vectors(thumb)]}
    if pictures:
        draw('headset', hand, placed, flat, thumb, os.path.join(HERE, 'hold_headset.png'))
    json.dump(out, open(os.path.join(HERE, 'holds.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
