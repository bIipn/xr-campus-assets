#!/usr/bin/env python3
"""Remove the trees that stand inside a building from unreal/Pipeline/out/ue/Outside.glb (in place).

The web campus scatters 140 random trees around the campus and keeps them out of the main campus box
only (parts/outdoor.js: x -40..97, z -50..31). The Wax Hall reaches south to z = -81, so two of those
trees grow inside it. In Unreal every wing shares one level, so their trunks and crowns show through
the hall. This pass deletes every tree whose trunk stands inside an indoor room of
WalkTheArchive/Data/Rooms.json (bOutdoor false), together with the crown triangles that belong to it,
and reports any crown triangle of a kept tree that still reaches into an indoor room.

The web build is left alone on purpose: changing its scatter would reshuffle every later tree.

Run after blender/prepare_for_unreal.py, from the repo root, with any Python 3.8+ (stdlib only):
    python unreal/Pipeline/blender/cull_indoor_trees.py [--dry-run]
Idempotent: a second run finds nothing to remove.
"""
import argparse
import json
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UNREAL = os.path.normpath(os.path.join(HERE, "..", ".."))
DEFAULT_GLB = os.path.join(UNREAL, "Pipeline", "out", "ue", "Outside.glb")
DEFAULT_ROOMS = os.path.join(UNREAL, "WalkTheArchive", "Data", "Rooms.json")
# prepare_for_unreal.py joins the tree parts by material: bark trunks, crown cores, leaf shells.
TRUNK_MESH = "M_Material_12"
CROWN_MESHES = ("M_Material_13", "M_Material_14")
CROWN_REACH_CM = 800.0          # a crown triangle further than this from every trunk is left alone
INDEX_TYPES = {5121: ("B", 1), 5123: ("H", 2), 5125: ("I", 4)}


class Glb:
    def __init__(self, path):
        data = open(path, "rb").read()
        magic, _version, _length = struct.unpack_from("<III", data, 0)
        if magic != 0x46546C67:
            raise SystemExit("not a GLB: " + path)
        json_len, _ = struct.unpack_from("<II", data, 12)
        self.doc = json.loads(data[20:20 + json_len].decode("utf-8"))
        off = 20 + json_len
        bin_len, _ = struct.unpack_from("<II", data, off)
        self.bin = bytearray(data[off + 8: off + 8 + bin_len])

    def _view(self, accessor_index):
        acc = self.doc["accessors"][accessor_index]
        view = self.doc["bufferViews"][acc["bufferView"]]
        return acc, view.get("byteOffset", 0) + acc.get("byteOffset", 0), view.get("byteStride")

    def positions(self, accessor_index):
        """Vertex positions in Unreal cm and axes (glTF (x, y, z) m -> UE (X=x, Y=z, Z=y) cm)."""
        acc, start, stride = self._view(accessor_index)
        stride = stride or 12
        out = []
        for i in range(acc["count"]):
            x, y, z = struct.unpack_from("<fff", self.bin, start + i * stride)
            out.append((x * 100.0, z * 100.0, y * 100.0))
        return out

    def indices(self, accessor_index):
        acc, start, _ = self._view(accessor_index)
        fmt, size = INDEX_TYPES[acc["componentType"]]
        return list(struct.unpack_from("<%d%s" % (acc["count"], fmt), self.bin, start))

    def write_indices(self, accessor_index, values):
        """Rewrite an index accessor with fewer indices, inside its own bytes."""
        acc, start, _ = self._view(accessor_index)
        if len(values) > acc["count"]:
            raise ValueError("can only shrink an index accessor")
        fmt, size = INDEX_TYPES[acc["componentType"]]
        struct.pack_into("<%d%s" % (len(values), fmt), self.bin, start, *values)
        acc["count"] = len(values)
        if values and "min" in acc:
            acc["min"], acc["max"] = [min(values)], [max(values)]

    def save(self, path):
        js = json.dumps(self.doc, separators=(",", ":")).encode("utf-8")
        js += b" " * ((4 - len(js) % 4) % 4)
        binc = bytes(self.bin) + b"\0" * ((4 - len(self.bin) % 4) % 4)
        total = 12 + 8 + len(js) + 8 + len(binc)
        with open(path, "wb") as fh:
            fh.write(struct.pack("<III", 0x46546C67, 2, total))
            fh.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
            fh.write(struct.pack("<II", len(binc), 0x004E4942) + binc)

    def mesh(self, name):
        for m in self.doc["meshes"]:
            if m.get("name") == name:
                return m
        raise SystemExit("mesh %s not in %s; pass --trunk/--crown with the tree mesh names" % (name, "Outside.glb"))


def islands(tri_list):
    """Group triangles (tuples of 3 vertex indices) that share vertices; returns lists of triangle ids."""
    parent = {}

    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a, b, c in tri_list:
        ra, rb, rc = find(a), find(b), find(c)
        parent[rb] = ra
        parent[find(rc)] = ra
    groups = {}
    for t, (a, _b, _c) in enumerate(tri_list):
        groups.setdefault(find(a), []).append(t)
    return list(groups.values())


def inside_xy(p, room):
    return room[0][0] <= p[0] <= room[1][0] and room[0][1] <= p[1] <= room[1][1]


def inside_xyz(p, room):
    return inside_xy(p, room) and room[0][2] <= p[2] <= room[1][2]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--glb", default=DEFAULT_GLB)
    ap.add_argument("--rooms", default=DEFAULT_ROOMS)
    ap.add_argument("--trunk", default=TRUNK_MESH)
    ap.add_argument("--crown", nargs="+", default=list(CROWN_MESHES))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    rooms = {}
    for r in json.load(open(args.rooms, encoding="utf-8")):
        if not r.get("bOutdoor", False):
            lo, hi = r["BoundsMin"], r["BoundsMax"]
            rooms[r["Name"]] = ((lo["X"], lo["Y"], lo["Z"]), (hi["X"], hi["Y"], hi["Z"]))

    glb = Glb(args.glb)

    # Trunks: each tree is a side island plus two caps around the same axis.
    trunk_prims = []
    axes = []                     # (x, y, removed?, room)
    for prim in glb.mesh(args.trunk)["primitives"]:
        pos = glb.positions(prim["attributes"]["POSITION"])
        idx = glb.indices(prim["indices"])
        tris = [tuple(idx[i:i + 3]) for i in range(0, len(idx), 3)]
        keep = [True] * len(tris)
        for group in islands(tris):
            verts = {v for t in group for v in tris[t]}
            xs = [pos[v][0] for v in verts]
            ys = [pos[v][1] for v in verts]
            zs = [pos[v][2] for v in verts]
            centre = ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
            room = next((n for n, box in rooms.items() if inside_xy(centre, box)), None)
            if room is not None:
                for t in group:
                    keep[t] = False
            if max(zs) - min(zs) > 100.0:            # the side, not a cap: one axis per tree
                axes.append((centre[0], centre[1], room is not None, room))
        trunk_prims.append((prim, tris, keep))
    if len(axes) < 20:
        raise SystemExit("%s does not look like the tree trunks (%d trunk sides); pass --trunk" % (args.trunk, len(axes)))

    removed_axes = [a for a in axes if a[2]]
    # Crowns: a triangle belongs to the nearest trunk; drop those whose nearest trunk was removed.
    cell = 1000.0
    grid = {}
    for a in axes:
        grid.setdefault((int(math.floor(a[0] / cell)), int(math.floor(a[1] / cell))), []).append(a)

    def nearest(x, y):
        gx, gy = int(math.floor(x / cell)), int(math.floor(y / cell))
        best, best_d = None, None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for a in grid.get((gx + dx, gy + dy), ()):
                    d = (a[0] - x) ** 2 + (a[1] - y) ** 2
                    if best_d is None or d < best_d:
                        best, best_d = a, d
        return best, (math.sqrt(best_d) if best_d is not None else None)

    crown_prims = []
    pokes = {}
    removed_crown = 0
    for name in args.crown:
        for prim in glb.mesh(name)["primitives"]:
            pos = glb.positions(prim["attributes"]["POSITION"])
            idx = glb.indices(prim["indices"])
            tris = [tuple(idx[i:i + 3]) for i in range(0, len(idx), 3)]
            keep = [True] * len(tris)
            for t, (a, b, c) in enumerate(tris):
                cx = (pos[a][0] + pos[b][0] + pos[c][0]) / 3.0
                cy = (pos[a][1] + pos[b][1] + pos[c][1]) / 3.0
                cz = (pos[a][2] + pos[b][2] + pos[c][2]) / 3.0
                owner, dist = nearest(cx, cy)
                if owner is not None and owner[2] and dist <= CROWN_REACH_CM:
                    keep[t] = False
                    removed_crown += 1
                    continue
                for room_name, box in rooms.items():
                    if inside_xyz((cx, cy, cz), box):
                        pokes[room_name] = pokes.get(room_name, 0) + 1
                        break
            crown_prims.append((prim, tris, keep))

    removed_trunk_tris = sum(k.count(False) for _p, _t, k in trunk_prims)
    print("cull_indoor_trees: %d trees, %d inside an indoor room%s" % (
        len(axes), len(removed_axes),
        "".join("\n  remove tree at (%.0f, %.0f) in %s" % (a[0], a[1], a[3]) for a in removed_axes)))
    print("  trunk triangles removed: %d; crown triangles removed: %d" % (removed_trunk_tris, removed_crown))
    if pokes:
        print("  crown triangles of kept trees still inside a room: " + ", ".join("%s %d" % kv for kv in sorted(pokes.items())))
    if not removed_axes:
        print("  nothing to do")
        return 0
    if args.dry_run:
        print("  dry run: %s unchanged" % args.glb)
        return 0
    for prim, tris, keep in trunk_prims + crown_prims:
        if all(keep):
            continue
        glb.write_indices(prim["indices"], [v for t, k in zip(tris, keep) if k for v in t])
    glb.save(args.glb)
    print("  wrote " + args.glb)
    return 0


if __name__ == "__main__":
    sys.exit(main())
