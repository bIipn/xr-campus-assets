"""The neoclassical vocabulary shared by the museum (bl/museum.py) and the grounds (bl/exterior.py): columns and
capitals, entablatures, coffered vaults and domes, arches, urns, pedestals, banners, trees. Everything is built from
campus coordinates (x east, y up, z south) through library.P, with library.Builder collecting the faces.

Each helper takes the Builder(s) it should draw into, so callers decide the material and the mesh grouping.
"""
import math
from mathutils import Vector

from library import P, D, Builder, bar, prism, poly_prism, bezier, material, MATS


# ---------------------------------------------------------------- surfaces of revolution
def lathe(b, cx, cz, prof, n=24, flute=None, cap_top=True, cap_bot=False, a0=0.0, twist=None):
    """Spin a profile [(y, r), ...] (bottom to top) around the vertical axis through campus (cx, cz).
    flute=(count, depth) scallops the radius: r * (1 - depth * (0.5 + 0.5 cos(count * theta))) so a shaft gets its
    channels; use n = 4 * count so each flute is sampled across. twist(y) -> extra angle per ring (optional)."""
    ring = [a0 + 2 * math.pi * i / n for i in range(n)]
    def mult(a):
        if not flute: return 1.0
        c, d = flute
        return 1.0 - d * (0.5 + 0.5 * math.cos(c * (a - a0)))
    rings = []
    for (y, r) in prof:
        tw = twist(y) if twist else 0.0
        rings.append([P(cx + r * mult(a) * math.cos(a + tw), y, cz + r * mult(a) * math.sin(a + tw)) for a in ring])
    for k in range(len(prof) - 1):
        (y0, r0), (y1, r1) = prof[k], prof[k + 1]
        dy, dr = y1 - y0, r1 - r0
        if abs(dy) < 1e-9 and abs(dr) < 1e-9: continue
        for i in range(n):
            j = (i + 1) % n; am = (ring[i] + ring[j]) / 2
            nrm = D(math.cos(am) * dy, -dr, math.sin(am) * dy)
            if nrm.length < 1e-9: nrm = D(math.cos(am), 0, math.sin(am))
            b.face([rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]], nrm.normalized())
    if cap_top and prof[-1][1] > 1e-6:
        cen = P(cx, prof[-1][0], cz); top = rings[-1]
        for i in range(n): b.face([cen, top[i], top[(i + 1) % n]], D(0, 1, 0))
    if cap_bot and prof[0][1] > 1e-6:
        cen = P(cx, prof[0][0], cz); low = rings[0]
        for i in range(n): b.face([cen, low[(i + 1) % n], low[i]], D(0, -1, 0))


def face_uv(b, pts, n, uvs):
    """A face with explicit uvs whose winding is made to match the normal first, so Builder never flips it
    (a flipped face would keep the uv order and mirror the texture)."""
    if (pts[1] - pts[0]).cross(pts[2] - pts[0]).dot(n) < 0:
        pts = list(reversed(pts)); uvs = list(reversed(uvs))
    return b.face(pts, n, uvs=uvs)


def annulus(b, cx, cz, y, r0, r1, a0, a1, n=8, up=True):
    """A flat ring sector in the floor plane (y), from radius r0 to r1 between angles a0..a1."""
    for i in range(n):
        t0 = a0 + (a1 - a0) * i / n; t1 = a0 + (a1 - a0) * (i + 1) / n
        pts = [P(cx + r0 * math.cos(t0), y, cz + r0 * math.sin(t0)), P(cx + r1 * math.cos(t0), y, cz + r1 * math.sin(t0)),
               P(cx + r1 * math.cos(t1), y, cz + r1 * math.sin(t1)), P(cx + r0 * math.cos(t1), y, cz + r0 * math.sin(t1))]
        if r0 < 1e-6: pts = [pts[0], pts[1], pts[2]]
        b.face(pts, D(0, 1 if up else -1, 0))


# ---------------------------------------------------------------- walls with profiles
def extrude_profile(b, pts, origin, U, V, N, t, front=True, back=True, sides=True, centre=None):
    """A flat shape (list of (u, v), counter-clockwise seen from +N) at campus `origin`, spanned by unit campus
    vectors U and V, extruded t along N (from origin to origin + N t). Fan-triangulated from the centroid, so the
    outline must be star-shaped around it (rectangles with an arch cut out of one edge are fine)."""
    O = P(*origin); Uv = D(*U); Vv = D(*V); Nv = D(*N)
    def W(u, v, w): return O + Uv * u + Vv * v + Nv * w
    cu, cv = centre if centre else (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        if front: b.face([W(cu, cv, t), W(pts[i][0], pts[i][1], t), W(pts[j][0], pts[j][1], t)], Nv)
        if back: b.face([W(cu, cv, 0), W(pts[j][0], pts[j][1], 0), W(pts[i][0], pts[i][1], 0)], -Nv)
        if sides:
            du, dv = pts[j][0] - pts[i][0], pts[j][1] - pts[i][1]
            nrm = Uv * dv - Vv * du
            b.face([W(pts[i][0], pts[i][1], 0), W(pts[j][0], pts[j][1], 0), W(pts[j][0], pts[j][1], t), W(pts[i][0], pts[i][1], t)], nrm.normalized())


def arch_pts(u0, u1, v_spring, n=16, rise=None):
    """Points along a round (or segmental, when rise < half the span) arch from (u0, v_spring) over to (u1, v_spring),
    left to right. For a wall outline the caller walks them in the direction it needs."""
    R = (u1 - u0) / 2; uc = (u0 + u1) / 2
    if rise is None or rise >= R - 1e-6:
        return [(uc - R * math.cos(math.pi * i / n), v_spring + R * math.sin(math.pi * i / n)) for i in range(n + 1)]
    # segmental: circle through the springing points with the given rise
    Rc = (R * R + rise * rise) / (2 * rise); vc = v_spring + rise - Rc
    a = math.asin(R / Rc)
    return [(uc - Rc * math.sin(a - 2 * a * i / n), vc + Rc * math.cos(a - 2 * a * i / n)) for i in range(n + 1)]


def wall_with_arch(b, origin, U, V, N, t, w, h, a_u0, a_u1, spring, rise=None, n=16, solid=True):
    """A wall slab w by h (in U, V from origin) with an arched opening from a_u0..a_u1 that springs at `spring`:
    two piers, and a spandrel piece above the arch (a rectangle with the arch cut from its lower edge).
    solid=False draws only the front face (for walls that get their thickness from a Solidify modifier)."""
    piers = [[(0, 0), (a_u0, 0), (a_u0, h), (0, h)], [(a_u1, 0), (w, 0), (w, h), (a_u1, h)]]
    for pts in piers:
        if pts[1][0] - pts[0][0] > 1e-6: extrude_profile(b, pts, origin, U, V, N, t, back=solid, sides=solid)
    arc = arch_pts(a_u0, a_u1, spring, n, rise)
    top = max(p[1] for p in arc)
    if h > top + 0.01:
        pts = [(a_u1, h), (a_u0, h)] + arc    # ccw: top-right, top-left, then along the arch left -> right
        extrude_profile(b, pts, origin, U, V, N, t, back=solid, sides=solid, centre=((a_u0 + a_u1) / 2, (top + h) / 2))


def wall_with_door(b, origin, U, V, N, t, w, h, d_u0, d_u1, d_h, solid=True):
    """A wall slab with a rectangular opening: two piers and a lintel piece (front face only when solid=False)."""
    for pts in ([(0, 0), (d_u0, 0), (d_u0, h), (0, h)], [(d_u1, 0), (w, 0), (w, h), (d_u1, h)], [(d_u0, d_h), (d_u1, d_h), (d_u1, h), (d_u0, h)]):
        if pts[2][1] - pts[0][1] > 1e-6 and pts[1][0] - pts[0][0] > 1e-6: extrude_profile(b, pts, origin, U, V, N, t, back=solid, sides=solid)


def wall_with_openings(b, origin, U, V, N, t, w, h, openings, solid=True):
    """A wall slab w by h with any number of rectangular openings [(u0, u1, v0, v1), ...] that do not overlap along
    u (a door from v0 = 0, a window above the floor): the piers between them and a piece below and above each. Front
    face only when solid=False (a room's inner face, or a shell face whose reveals the room's builder draws)."""
    pieces = []
    u = 0.0
    for (u0, u1, v0, v1) in sorted(openings):
        if u0 - u > 1e-6: pieces.append([(u, 0), (u0, 0), (u0, h), (u, h)])
        if v0 > 1e-6: pieces.append([(u0, 0), (u1, 0), (u1, v0), (u0, v0)])
        if h - v1 > 1e-6: pieces.append([(u0, v1), (u1, v1), (u1, h), (u0, h)])
        u = max(u, u1)
    if w - u > 1e-6: pieces.append([(u, 0), (w, 0), (w, h), (u, h)])
    for pts in pieces:
        extrude_profile(b, pts, origin, U, V, N, t, back=solid, sides=solid)


# ---------------------------------------------------------------- mouldings, columns, capitals
def run_boxes(b, a, c, out, prof, seg=None):
    """Mouldings along a wall from campus (x, z) `a` to `c`, each (y0, y1, depth) a box standing `depth` out of the
    wall plane in the 2D direction `out`."""
    ux, uz = c[0] - a[0], c[1] - a[1]; L = math.hypot(ux, uz)
    if L < 1e-6: return
    ux, uz = ux / L, uz / L
    ry = math.atan2(-uz, ux)
    mx, mz = (a[0] + c[0]) / 2, (a[1] + c[1]) / 2
    for (y0, y1, d) in prof:
        b.box(mx + out[0] * d / 2, (y0 + y1) / 2, mz + out[1] * d / 2, L, y1 - y0, d, ry, seg=seg)


# entablature profiles (y above the column top, depth out of the wall): architrave fasciae, frieze, cornice
ENTABLATURE = [(0.00, 0.12, 0.06), (0.12, 0.26, 0.09), (0.26, 0.42, 0.12), (0.42, 0.47, 0.15),   # architrave
               (0.47, 0.80, 0.12),                                                              # frieze
               (0.80, 0.86, 0.17), (0.86, 0.94, 0.24), (0.94, 1.04, 0.38), (1.04, 1.10, 0.42)]   # bed mould, corona, cyma
ENT_H = 1.10
DADO = [(0.00, 0.12, 0.07), (0.12, 0.95, 0.05), (0.95, 1.02, 0.08)]      # skirting, panel, cap
DADO_H = 1.02


def dentils(b, a, c, out, y0, y1, depth, pitch=0.22, w=0.11):
    ux, uz = c[0] - a[0], c[1] - a[1]; L = math.hypot(ux, uz)
    if L < 1e-6: return
    ux, uz = ux / L, uz / L
    ry = math.atan2(-uz, ux)
    s = pitch / 2
    while s + w / 2 < L:
        b.box(a[0] + ux * s + out[0] * depth / 2, (y0 + y1) / 2, a[1] + uz * s + out[1] * depth / 2, w, y1 - y0, depth, ry, seg=0)
        s += pitch


def entablature(b, bd, a, c, out, y, dent=True):
    """The full order's entablature along a run, its base at height y (the column tops)."""
    run_boxes(b, a, c, out, [(y + y0, y + y1, d) for (y0, y1, d) in ENTABLATURE], seg=3.0)
    if dent: dentils(bd, a, c, out, y + 0.80, y + 0.86, 0.22)


# a Corinthian column: plinth and base, fluted shaft with entasis, bell capital with two rows of leaves
def column(bs, bc, bb, cx, cz, h, r=0.32, flutes=24, plinth=True, a0=0.0, cap_h=None, y_base=0.0):
    """bs: shaft builder (stone, smooth), bc: capital (gilt), bb: base (stone). h: from y_base to the top of the abacus."""
    ch = cap_h or 1.9 * r
    base_h = 0.9 * r
    if plinth:
        bb.box(cx, y_base + base_h * 0.22, cz, 2.9 * r, base_h * 0.44, 2.9 * r, seg=0)
        lathe(bb, cx, cz, [(y_base + base_h * 0.44, 1.42 * r), (y_base + base_h * 0.62, 1.48 * r), (y_base + base_h * 0.78, 1.36 * r), (y_base + base_h * 0.9, 1.16 * r), (y_base + base_h, 1.06 * r)], n=24, a0=a0)
    y0 = y_base + (base_h if plinth else 0.0)
    y1 = y_base + h - ch
    # shaft: a slight swell a third of the way up, tapering to 0.85 r at the astragal
    prof = [(y0, 1.0 * r), (y0 + 0.08 * (y1 - y0), 1.02 * r), (y0 + 0.36 * (y1 - y0), 1.0 * r), (y1 - 0.12, 0.86 * r), (y1 - 0.06, 0.86 * r), (y1, 0.92 * r)]
    lathe(bs, cx, cz, prof, n=4 * flutes, flute=(flutes, 0.12), a0=a0, cap_top=False)
    capital(bc, cx, cz, y1, 0.86 * r, ch, a0=a0)


def capital(bc, cx, cz, y0, r0, h, a0=0.0):
    """A stylised Corinthian capital: a bell, eight leaves on two staggered rows, corner volutes and a concave-sided
    abacus. r0 is the shaft radius at the neck."""
    bell = [(y0, r0), (y0 + 0.18 * h, 1.04 * r0), (y0 + 0.50 * h, 1.22 * r0), (y0 + 0.72 * h, 1.50 * r0), (y0 + 0.80 * h, 1.62 * r0)]
    lathe(bc, cx, cz, bell, n=24, a0=a0)
    # leaves: a strip of three quads rising from the bell and curling out at the tip
    def leaf(a, yb, scale):
        sec = [(1.00 * r0, 0.00 * h, 0.50 * r0), (1.12 * r0, 0.20 * h, 0.62 * r0), (1.42 * r0, 0.36 * h, 0.54 * r0),
               (1.68 * r0, 0.40 * h, 0.30 * r0), (1.78 * r0, 0.34 * h, 0.06 * r0)]
        ca, sa = math.cos(a), math.sin(a)
        rows = []
        for (rr, hh, hw) in sec:
            rr *= scale; hh *= scale
            c = (cx + rr * ca, yb + hh, cz + rr * sa)
            rows.append([P(c[0] - hw * sa, c[1], c[2] + hw * ca), P(c[0] + hw * sa, c[1], c[2] - hw * ca)])
        for k in range(len(rows) - 1):
            bc.face([rows[k][0], rows[k][1], rows[k + 1][1], rows[k + 1][0]], D(ca, 0.35, sa).normalized())
    for k in range(8): leaf(a0 + 2 * math.pi * k / 8, y0 + 0.02 * h, 1.0)
    for k in range(8): leaf(a0 + 2 * math.pi * (k + 0.5) / 8, y0 + 0.30 * h, 1.05)
    # volutes under the abacus corners
    A = 1.55 * r0
    for k in range(4):
        a = a0 + math.pi / 4 + k * math.pi / 2
        ca, sa = math.cos(a), math.sin(a)
        p0 = (cx + 1.1 * r0 * ca, y0 + 0.62 * h, cz + 1.1 * r0 * sa)
        p1 = (cx + A * 1.30 * ca, y0 + 0.80 * h, cz + A * 1.30 * sa)
        bar(bc, p0, p1, 0.24 * r0)
        prism(bc, p1[0], p1[1] - 0.16 * r0, p1[2], 0.17 * r0, 0.32 * r0, n=10)
    # abacus: a square with its sides bowed in
    pts = []
    corners = [(A, A), (-A, A), (-A, -A), (A, -A)]
    for k in range(4):
        c0 = corners[k]; c1 = corners[(k + 1) % 4]
        mid = ((c0[0] + c1[0]) / 2 * 0.80, (c0[1] + c1[1]) / 2 * 0.80)
        pts += bezier(c0, mid, c1, 4)[:-1]
    # rotate the abacus with a0
    ca, sa = math.cos(a0), math.sin(a0)
    pts = [(u * ca - v * sa, u * sa + v * ca) for (u, v) in pts]
    poly_prism(bc, pts, cx, y0 + 0.80 * h, cz, 0.20 * h)


def pilaster(bs, bc, bb, origin, out, w, h, depth=0.14, r_cap=None):
    """A flat pilaster w wide standing `depth` out of a wall at campus (x, z) `origin`, its face normal `out`;
    a small capital block instead of the round one."""
    ox, oz = origin
    ry = math.atan2(-out[1], out[0]) + math.pi / 2
    bb.box(ox + out[0] * depth * 0.6, 0.16, oz + out[1] * depth * 0.6, w * 1.18, 0.32, depth * 1.2, ry, seg=0)
    bs.box(ox + out[0] * depth / 2, (0.32 + h - 0.42) / 2, oz + out[1] * depth / 2, w, h - 0.74, depth, ry, seg=2.0)
    bc.box(ox + out[0] * depth * 0.55, h - 0.30, oz + out[1] * depth * 0.55, w * 1.08, 0.24, depth * 1.1, ry, seg=0)
    bc.box(ox + out[0] * depth * 0.65, h - 0.09, oz + out[1] * depth * 0.65, w * 1.26, 0.18, depth * 1.3, ry, seg=0)


# ---------------------------------------------------------------- coffered ceilings
def coffered_flat(b, bg, x0, x1, z0, z1, y, nx, nz, rib=0.30, depth=0.22, inset=0.12, rosette=True):
    """A flat coffered ceiling seen from below: ribs at height y, each coffer a sloped recess `depth` up, with a
    gilt rosette (bg) in the middle."""
    cw = ((x1 - x0) - (nx + 1) * rib) / nx; cd = ((z1 - z0) - (nz + 1) * rib) / nz
    # rib strips along z and along x, as flat quads at y
    for i in range(nx + 1):
        xa = x0 + i * (cw + rib)
        b.face([P(xa, y, z0), P(xa + rib, y, z0), P(xa + rib, y, z1), P(xa, y, z1)], D(0, -1, 0))
    for j in range(nz + 1):
        za = z0 + j * (cd + rib)
        for i in range(nx):
            xa = x0 + rib + i * (cw + rib)
            b.face([P(xa, y, za), P(xa + cw, y, za), P(xa + cw, y, za + rib), P(xa, y, za + rib)], D(0, -1, 0))
    for i in range(nx):
        for j in range(nz):
            xa = x0 + rib + i * (cw + rib); za = z0 + rib + j * (cd + rib)
            coffer_box(b, bg, xa, xa + cw, za, za + cd, y, depth, inset, rosette)


def coffer_box(b, bg, xa, xb, za, zb, y, depth, inset, rosette=True):
    """One recess in a flat ceiling: four sloped sides up to a panel `depth` higher."""
    o = [P(xa, y, za), P(xb, y, za), P(xb, y, zb), P(xa, y, zb)]
    i_ = [P(xa + inset, y + depth, za + inset), P(xb - inset, y + depth, za + inset), P(xb - inset, y + depth, zb - inset), P(xa + inset, y + depth, zb - inset)]
    nrm = [D(0, -0.5, 1), D(-1, -0.5, 0), D(0, -0.5, -1), D(1, -0.5, 0)]
    for k in range(4):
        j = (k + 1) % 4
        b.face([o[k], o[j], i_[j], i_[k]], nrm[k].normalized())
    b.face([i_[3], i_[2], i_[1], i_[0]], D(0, -1, 0))
    if rosette:
        rosette_at(bg, ((xa + xb) / 2, y + depth, (za + zb) / 2), D(1, 0, 0), D(0, 0, 1), D(0, -1, 0), min(xb - xa, zb - za) * 0.16)


def rosette_at(bg, centre, U, V, N, r):
    """An eight-point gilt star with a raised boss, in the plane (U, V) facing N, centre a campus point."""
    C = P(*centre)
    star = []
    for k in range(16):
        a = 2 * math.pi * k / 16; rr = r if k % 2 == 0 else r * 0.45
        star.append(C + U * (rr * math.cos(a)) + V * (rr * math.sin(a)) + N * 0.02)
    for k in range(16):
        bg.face([C + N * 0.02, star[k], star[(k + 1) % 16]], N)
    lo = [C + U * (0.22 * r * math.cos(2 * math.pi * k / 8)) + V * (0.22 * r * math.sin(2 * math.pi * k / 8)) + N * 0.02 for k in range(8)]
    hi = [C + U * (0.22 * r * math.cos(2 * math.pi * k / 8)) + V * (0.22 * r * math.sin(2 * math.pi * k / 8)) + N * 0.07 for k in range(8)]
    for k in range(8):
        j = (k + 1) % 8
        bg.face([C + N * 0.07, hi[k], hi[j]], N)
        a = 2 * math.pi * (k + 0.5) / 8
        bg.face([lo[k], lo[j], hi[j], hi[k]], U * math.cos(a) + V * math.sin(a))


def barrel_vault(b, bg, bl, x_c, R, cy, half, z0, z1, na, nz, rib=0.30, depth=0.24, inset=0.14, laylight=None, rosette=True):
    """A coffered barrel vault along z: the inner surface is the cylinder of radius R about the axis (x_c, cy)
    spanning x in -half..half. na coffers across the arc, nz along z. `laylight` = (theta cell, z cells) whose
    panels become glazing drawn into bl instead."""
    alpha = math.asin(half / R)
    S = 2 * alpha * R
    cw = (S - (na + 1) * rib) / na; cd = ((z1 - z0) - (nz + 1) * rib) / nz
    def pt(s, z, dr=0.0):          # arc length s (from -S/2 at x = -half) and z -> campus point at radius R + dr
        th = s / R
        return P(x_c + (R + dr) * math.sin(th), cy + (R + dr) * math.cos(th), z)
    def nrm(s):
        th = s / R
        return D(-math.sin(th), -math.cos(th), 0)
    sub = 6
    # ribs along z (arc strips), subdivided along the arc
    for i in range(na + 1):
        sa = -S / 2 + i * (cw + rib)
        for k in range(sub):
            s0 = sa + rib * k / sub; s1 = sa + rib * (k + 1) / sub
            b.face([pt(s0, z0), pt(s1, z0), pt(s1, z1), pt(s0, z1)], nrm((s0 + s1) / 2))
    # ribs across (z strips), subdivided along the arc
    for j in range(nz + 1):
        za = z0 + j * (cd + rib)
        for i in range(na):
            sa = -S / 2 + rib + i * (cw + rib)
            for k in range(sub):
                s0 = sa + cw * k / sub; s1 = sa + cw * (k + 1) / sub
                b.face([pt(s0, za), pt(s1, za), pt(s1, za + rib), pt(s0, za + rib)], nrm((s0 + s1) / 2))
    for i in range(na):
        for j in range(nz):
            sa = -S / 2 + rib + i * (cw + rib); za = z0 + rib + j * (cd + rib)
            sb = sa + cw; zb = za + cd
            glazed = laylight is not None and i == laylight[0] and j in laylight[1]
            # four sloped sides from the rim (at R) to the recess (at R + depth), then the panel
            rim = [(sa, za), (sb, za), (sb, zb), (sa, zb)]
            inn = [(sa + inset, za + inset), (sb - inset, za + inset), (sb - inset, zb - inset), (sa + inset, zb - inset)]
            cmid = pt((sa + sb) / 2, (za + zb) / 2)
            for k in range(4):
                jn = (k + 1) % 4
                p = [pt(rim[k][0], rim[k][1]), pt(rim[jn][0], rim[jn][1]), pt(inn[jn][0], inn[jn][1], depth), pt(inn[k][0], inn[k][1], depth)]
                want = (cmid - (p[0] + p[1]) / 2) + nrm((sa + sb) / 2) * 0.6
                b.face(p, want.normalized())
            # the panel, curved: a few quads across the arc
            target = bl if glazed else b
            m = 4
            for k in range(m):
                s0 = inn[0][0] + (inn[1][0] - inn[0][0]) * k / m; s1 = inn[0][0] + (inn[1][0] - inn[0][0]) * (k + 1) / m
                target.face([pt(s0, inn[0][1], depth), pt(s1, inn[0][1], depth), pt(s1, inn[2][1], depth), pt(s0, inn[2][1], depth)], nrm((s0 + s1) / 2))
            if glazed:
                # gilt mullions: a cross through the glazing, just below it
                sm = (inn[0][0] + inn[1][0]) / 2; zm = (inn[0][1] + inn[2][1]) / 2
                for (u0, u1, v0, v1) in ((inn[0][0], inn[1][0], zm - 0.04, zm + 0.04), (sm - 0.04, sm + 0.04, inn[0][1], inn[2][1])):
                    for k in range(m):
                        s0 = u0 + (u1 - u0) * k / m; s1 = u0 + (u1 - u0) * (k + 1) / m
                        bg.face([pt(s0, v0, depth - 0.04), pt(s1, v0, depth - 0.04), pt(s1, v1, depth - 0.04), pt(s0, v1, depth - 0.04)], nrm((s0 + s1) / 2))
            elif rosette:
                sm = (inn[0][0] + inn[1][0]) / 2; zm = (inn[0][1] + inn[2][1]) / 2
                c = pt(sm, zm, depth)
                th = sm / R
                U = D(math.cos(th), -math.sin(th), 0); V = D(0, 0, 1); N = D(-math.sin(th), -math.cos(th), 0)
                rosette_at(bg, (c.x, c.z, -c.y), U, V, N, min(cw, cd) * 0.15)


def lunette_pts(R, cy, half, y_base, n=24):
    """Outline (x, y) of the wall piece between a vault's springing line y_base and its arc: counter-clockwise."""
    alpha = math.asin(half / R)
    pts = [(-half, y_base), (half, y_base)]
    for i in range(n + 1):
        th = alpha - 2 * alpha * i / n
        pts.append((R * math.sin(th), cy + R * math.cos(th)))
    return pts


def dome(b, bg, bl, cx, cy, cz, R, rows, around, psi0, psi1, rib_deg=2.2, depth=0.22, inset_deg=1.0, oculus_psi=15.0):
    """A coffered dome: the inside of the sphere (cx, cy, cz, R) from polar angle psi1 (near the rim, degrees from
    the pole) up to psi0, `rows` rings of `around` coffers; a flat collar to the oculus and glazing (bl) in it."""
    def pt(psi, phi, dr=0.0):
        ps, ph = math.radians(psi), math.radians(phi)
        return P(cx + (R + dr) * math.sin(ps) * math.cos(ph), cy + (R + dr) * math.cos(ps), cz + (R + dr) * math.sin(ps) * math.sin(ph))
    def nrm(psi, phi):
        ps, ph = math.radians(psi), math.radians(phi)
        return D(-math.sin(ps) * math.cos(ph), -math.cos(ps), -math.sin(ps) * math.sin(ph))
    span = psi1 - psi0
    ch = (span - (rows + 1) * rib_deg) / rows          # coffer height in degrees of polar angle
    aw = 360.0 / around; arib = 2.4; acw = aw - arib     # azimuth: coffer and rib widths in degrees
    sub = 3
    for r_ in range(rows + 1):
        pa = psi0 + r_ * (ch + rib_deg)                   # a horizontal rib ring, from pa to pa + rib
        for k in range(around * sub):
            f0 = k * aw / sub; f1 = (k + 1) * aw / sub
            b.face([pt(pa, f0), pt(pa, f1), pt(pa + rib_deg, f1), pt(pa + rib_deg, f0)], nrm(pa + rib_deg / 2, (f0 + f1) / 2))
    for r_ in range(rows):
        pa = psi0 + rib_deg + r_ * (ch + rib_deg); pb = pa + ch
        for k in range(around):
            fa = k * aw; fb = fa + arib
            for s in range(sub):      # the vertical rib between coffers
                q0 = pa + (pb - pa) * s / sub; q1 = pa + (pb - pa) * (s + 1) / sub
                b.face([pt(q0, fa), pt(q0, fb), pt(q1, fb), pt(q1, fa)], nrm((q0 + q1) / 2, (fa + fb) / 2))
            # the coffer: rim at R, panel at R + depth
            ca, cb = fa + arib, fa + aw
            rim = [(pa, ca), (pa, cb), (pb, cb), (pb, ca)]
            ins = inset_deg
            inn = [(pa + ins, ca + ins * 1.4), (pa + ins, cb - ins * 1.4), (pb - ins, cb - ins * 1.4), (pb - ins, ca + ins * 1.4)]
            cmid = pt((pa + pb) / 2, (ca + cb) / 2)
            for q in range(4):
                j = (q + 1) % 4
                p = [pt(*rim[q]), pt(*rim[j]), pt(inn[j][0], inn[j][1], depth), pt(inn[q][0], inn[q][1], depth)]
                want = (cmid - (p[0] + p[1]) / 2) + nrm((pa + pb) / 2, (ca + cb) / 2) * 0.6
                b.face(p, want.normalized())
            p = [pt(inn[3][0], inn[3][1], depth), pt(inn[2][0], inn[2][1], depth), pt(inn[1][0], inn[1][1], depth), pt(inn[0][0], inn[0][1], depth)]
            b.face(p, nrm((pa + pb) / 2, (ca + cb) / 2))
            c = pt((pa + pb) / 2, (ca + cb) / 2, depth)
            N = nrm((pa + pb) / 2, (ca + cb) / 2)
            U = (pt((pa + pb) / 2, (ca + cb) / 2 + 1) - c).normalized(); V = N.cross(U)
            rr = (R * math.radians(ch) * 0.12) * (0.8 + 0.4 * math.sin(math.radians((pa + pb) / 2)))
            rosette_at(bg, (c.x, c.z, -c.y), U, V, N, rr)
    # collar from the top rib to the oculus, and the glazing in the oculus
    pa = psi0 - 0.0
    for k in range(around * sub):
        f0 = k * aw / sub; f1 = (k + 1) * aw / sub
        b.face([pt(oculus_psi, f0), pt(oculus_psi, f1), pt(pa, f1), pt(pa, f0)], nrm((oculus_psi + pa) / 2, (f0 + f1) / 2))
    # oculus glazing: a flat disc in the plane of the oculus ring, slightly above it
    yo = cy + R * math.cos(math.radians(oculus_psi)) + 0.25; ro = R * math.sin(math.radians(oculus_psi))
    annulus(bl, cx, cz, yo, 0.0, ro, 0, 2 * math.pi, n=24, up=False)
    # a ring moulding around the oculus
    lathe(bg, cx, cz, [(yo - 0.30, ro + 0.02), (yo - 0.12, ro + 0.16), (yo - 0.02, ro + 0.18), (yo, ro + 0.05)], n=32, cap_top=False)
    return yo, ro


# ---------------------------------------------------------------- furnishings
URN = [(0.00, 0.26), (0.05, 0.26), (0.06, 0.16), (0.15, 0.15), (0.19, 0.22), (0.32, 0.36), (0.50, 0.41), (0.68, 0.36),
       (0.82, 0.25), (0.88, 0.22), (0.92, 0.31), (0.98, 0.33), (1.00, 0.26), (1.00, 0.0)]


def urn(b, cx, cz, y0, h=1.1, s=1.0, handles=True, n=32):
    prof = [(y0 + h * t, s * r) for (t, r) in URN]
    lathe(b, cx, cz, prof, n=n, cap_top=True)
    lathe(b, cx, cz, [(y0 + h, 0.0), (y0 + h, s * 0.08), (y0 + h * 1.12, s * 0.06), (y0 + h * 1.14, s * 0.11), (y0 + h * 1.17, s * 0.10), (y0 + h * 1.22, s * 0.02)], n=16)
    if handles:
        for side in (-1, 1):
            p0 = (cx + side * s * 0.40, y0 + h * 0.50, cz); p2 = (cx + side * s * 0.23, y0 + h * 0.86, cz)
            ctrl = (cx + side * s * 0.62, y0 + h * 0.86, cz)
            pts = bezier((p0[0], p0[1]), (ctrl[0], ctrl[1]), (p2[0], p2[1]), 6)
            for k in range(len(pts) - 1):
                bar(b, (pts[k][0], pts[k][1], cz), (pts[k + 1][0], pts[k + 1][1], cz), s * 0.05)


def pedestal(b, bt, cx, cz, w, h, top_mat=True):
    """A square pedestal: plinth, die with recessed panel, cap. bt draws the top slab (a different stone)."""
    b.box(cx, 0.08, cz, w, 0.16, w, seg=0)
    b.box(cx, 0.16 + 0.04, cz, w * 0.92, 0.08, w * 0.92, seg=0)
    b.box(cx, (0.24 + h - 0.16) / 2, cz, w * 0.80, h - 0.40, w * 0.80, seg=0)
    b.box(cx, h - 0.12, cz, w * 0.92, 0.08, w * 0.92, seg=0)
    (bt if top_mat else b).box(cx, h - 0.04, cz, w, 0.08, w, seg=0)


def banner(bf, br, x, y_top, z, w=1.2, h=3.0, facing='z', rod=True, uv_flip=False):
    """An exhibition banner hanging from a rod: a plane w by h (uv 0..1) facing the +z or +x side."""
    if facing == 'z':
        pts = [P(x - w / 2, y_top - h, z), P(x + w / 2, y_top - h, z), P(x + w / 2, y_top, z), P(x - w / 2, y_top, z)]
        n = D(0, 0, 1)
        if rod:
            bar(br, (x - w / 2 - 0.12, y_top + 0.02, z), (x + w / 2 + 0.12, y_top + 0.02, z), 0.04)
    else:
        pts = [P(x, y_top - h, z + w / 2), P(x, y_top - h, z - w / 2), P(x, y_top, z - w / 2), P(x, y_top, z + w / 2)]
        n = D(1, 0, 0)
        if rod:
            bar(br, (x, y_top + 0.02, z - w / 2 - 0.12), (x, y_top + 0.02, z + w / 2 + 0.12), 0.04)
    uvs = [(0, 0), (1, 0), (1, 1), (0, 1)] if not uv_flip else [(1, 0), (0, 0), (0, 1), (1, 1)]
    bf.face(pts, n, uvs=uvs)
    bf.face(list(reversed(pts)), -n, uvs=list(reversed(uvs)))


def torchere(bb, bg, x, z, h=2.2):
    """A floor-standing bronze torchère: tripod base, turned stem, a bowl with a glowing lamp (bg) in it."""
    lathe(bb, x, z, [(0.0, 0.30), (0.05, 0.30), (0.07, 0.20), (0.14, 0.18), (0.18, 0.09), (0.60, 0.06), (0.62, 0.10), (0.66, 0.06), (h - 0.50, 0.05), (h - 0.45, 0.12), (h - 0.40, 0.08)], n=16)
    lathe(bb, x, z, [(h - 0.40, 0.08), (h - 0.30, 0.26), (h - 0.12, 0.34), (h - 0.02, 0.33)], n=20, cap_top=False)
    lathe(bg, x, z, [(h - 0.20, 0.0), (h - 0.20, 0.28), (h - 0.08, 0.30), (h + 0.00, 0.0)], n=20)
    for k in range(3):
        a = 2 * math.pi * k / 3 + math.pi / 2
        bar(bb, (x + 0.30 * math.cos(a), 0.03, z + 0.30 * math.sin(a)), (x + 0.10 * math.cos(a), 0.30, z + 0.10 * math.sin(a)), 0.05)


def sconce(bb, bg, x, y, z, out):
    """A bronze half-bowl uplight on a wall or column at campus (x, y, z), its open side toward `out` (2D)."""
    ox, oz = out
    ry = math.atan2(-oz, ox)
    cx, cz = x + ox * 0.16, z + oz * 0.16
    lathe(bb, cx, cz, [(y - 0.30, 0.03), (y - 0.18, 0.12), (y - 0.04, 0.20), (y, 0.19)], n=16, cap_top=False)
    lathe(bg, cx, cz, [(y - 0.03, 0.0), (y - 0.03, 0.17)], n=16, cap_top=True)
    bb.box(x + ox * 0.03, y - 0.14, z + oz * 0.03, 0.16, 0.34, 0.06, ry, seg=0)
    bar(bb, (x + ox * 0.05, y - 0.28, z + oz * 0.05), (cx, y - 0.30, cz), 0.04)


def lantern(bb, bg, x, y, z, s=1.0):
    """A hanging/standing bronze lantern: cage of four posts, pyramid cap, glowing glass."""
    bg.box(x, y + 0.26 * s, z, 0.30 * s, 0.44 * s, 0.30 * s, seg=0)
    for sx in (-1, 1):
        for sz in (-1, 1):
            bb.box(x + sx * 0.16 * s, y + 0.26 * s, z + sz * 0.16 * s, 0.035 * s, 0.50 * s, 0.035 * s, seg=0)
    bb.box(x, y + 0.02 * s, z, 0.36 * s, 0.04 * s, 0.36 * s, seg=0)
    bb.box(x, y + 0.50 * s, z, 0.36 * s, 0.04 * s, 0.36 * s, seg=0)
    lathe(bb, x, z, [(y + 0.52 * s, 0.24 * s), (y + 0.68 * s, 0.05 * s), (y + 0.74 * s, 0.02 * s)], n=4, a0=math.pi / 4)


# ---------------------------------------------------------------- trees (for the grounds)
def tree(bt, bl, x, z, s=1.0, seed=0, ground=0.0, bc=None):
    """A broadleaf tree: a tapered trunk that leans a little, three or four limbs, and a crown of lumpy leaf clumps.
    bt: bark builder, bl: leaf builder; bc (optional): a builder for alpha-masked leaf cards crossed over each clump,
    which turn the clumps from topiary into foliage."""
    import random
    r = random.Random(seed)
    lean = r.uniform(-0.06, 0.06); lean_a = r.uniform(0, 2 * math.pi)
    h = 2.6 * s * r.uniform(0.9, 1.15)
    def twist(y): return 0.0
    prof = [(ground, 0.24 * s), (ground + 0.08, 0.17 * s), (ground + 0.25 * h, 0.15 * s), (ground + 0.7 * h, 0.11 * s), (ground + h, 0.08 * s)]
    lathe(bt, x, z, prof, n=10, a0=lean_a, cap_top=True)
    limbs = []
    n_l = 3 + (seed % 2)
    for k in range(n_l):
        a = 2 * math.pi * k / n_l + r.uniform(-0.4, 0.4)
        y0 = ground + h * r.uniform(0.55, 0.85)
        L = s * r.uniform(1.4, 2.2)
        tip = (x + L * math.cos(a) * 0.8, y0 + L * 0.65, z + L * math.sin(a) * 0.8)
        bar(bt, (x, y0, z), tip, 0.10 * s, caps=False)
        limbs.append(tip)
    # crown: clumps around the limb tips and the top, plus a few fillers between them
    clumps = [(x, ground + h + 0.7 * s, z, 1.6 * s)] + [(t[0], t[1] + 0.25 * s, t[2], 1.2 * s * r.uniform(0.85, 1.15)) for t in limbs]
    for k in range(3):
        a = r.uniform(0, 2 * math.pi); rr = s * r.uniform(0.6, 1.3)
        clumps.append((x + rr * math.cos(a), ground + h + s * r.uniform(-0.2, 1.1), z + rr * math.sin(a), s * r.uniform(0.8, 1.1)))
    for ci, (cx, cy, cz, cr) in enumerate(clumps):
        blob(bl, cx, cy, cz, cr * (0.82 if bc else 1.0), r.random() * 1000 + ci, squash=0.82, n=14, rings=7)
        if bc:
            for k in range(11):
                leaf_card(bc, (cx + r.uniform(-0.6, 0.6) * cr, cy + r.uniform(-0.45, 0.45) * cr, cz + r.uniform(-0.6, 0.6) * cr), cr * 1.15, r)


def leaf_card(bc, centre, size, r):
    """One square card, randomly tilted and spun, both faces uv 0..1."""
    n = Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-0.6, 0.6))).normalized()      # Blender axes: Z up
    helper = Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))
    u = n.cross(helper).normalized(); v = n.cross(u)
    spin = r.uniform(0, 2 * math.pi)
    u, v = u * math.cos(spin) + v * math.sin(spin), -u * math.sin(spin) + v * math.cos(spin)
    C = P(*centre); h = size / 2
    pts = [C - u * h - v * h, C + u * h - v * h, C + u * h + v * h, C - u * h + v * h]
    bc.face(pts, n, uvs=[(0, 0), (1, 0), (1, 1), (0, 1)])


def blob(b, cx, cy, cz, r, seed, squash=1.0, n=10, rings=5):
    """A lumpy ellipsoid built as a lathe with noisy radii: foliage."""
    import random
    rr = random.Random(seed)
    jit = [[rr.uniform(0.86, 1.12) for _ in range(n)] for _ in range(rings + 1)]
    pts = []
    for k in range(rings + 1):
        ps = math.pi * k / rings
        row = []
        for i in range(n):
            a = 2 * math.pi * i / n
            m = jit[k][i] if 0 < k < rings else 1.0
            row.append(P(cx + r * m * math.sin(ps) * math.cos(a), cy + r * squash * m * math.cos(ps), cz + r * m * math.sin(ps) * math.sin(a)))
        pts.append(row)
    for k in range(rings):
        for i in range(n):
            j = (i + 1) % n
            quad = [pts[k][i], pts[k][j], pts[k + 1][j], pts[k + 1][i]]
            c = sum(quad, Vector((0, 0, 0))) / 4
            nrm = (c - P(cx, cy, cz)).normalized()
            if k == 0: b.face([pts[k][i], pts[k + 1][j], pts[k + 1][i]], nrm)
            elif k == rings - 1: b.face([pts[k][i], pts[k][j], pts[k + 1][i]], nrm)
            else: b.face(quad, nrm)


def smooth(ob, angle=40.0):
    """Smooth shading with sharp edges kept by angle (a lathe object after Builder.finish)."""
    import bpy
    for p in ob.data.polygons: p.use_smooth = True
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))
    except Exception:
        pass
