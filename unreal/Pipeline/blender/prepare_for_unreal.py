"""
Make the exported wings import cleanly into Unreal Engine as plain static meshes.

Unreal's asset import keeps each glTF mesh in its own local space (node transforms are not applied
when you import meshes as assets). So before Unreal sees them, this pass:
  * bakes every object's world transform into its vertices (so every mesh sits at the origin and
    lands in the right place when spawned at Unreal (0, 0, 0)),
  * joins untagged meshes that share a material into one mesh per material (fewer, bigger meshes:
    ideal for Nanite and quick to place),
  * keeps tagged interactive pieces (item__, token__, ride__, staff__, station__, book__, bp__, seat__, the
    talk venues' screen__ slide screens and spot__ speaker marks, the pop-up books' popup__ pieces and the visit
    figure's figure__ parts) as their own meshes with their tag as the name,
  * applies content/refits.json to the web-exported wings it names (meshes dropped, groups moved, faces clipped
    out of a box), e.g. the School's Room 104 becoming the XR Classroom, the yard fence cut where the Training
    Wing's doorway opens through it,
  * drops vertex colours that only carried baked lighting,
  * names materials M_<Asset>_... and textures T_<Asset>_... so Unreal's Content Browser is readable.

Run from the repo root with Blender 5.2 (or bpy 5.2.2):
    python unreal/Pipeline/blender/prepare_for_unreal.py
Reads  unreal/Pipeline/out/campus/<wing>.glb, unreal/Pipeline/out/reading_room/ReadingRoom.glb, and the Blender-built
       museum and grounds (out/museum/Museum.glb, out/exterior/Outside.glb)
Writes unreal/Pipeline/out/ue/<Name>.glb and unreal/Pipeline/out/ue/manifest.json
"""
import json
import os
import re
import sys

import bpy

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
OUT = os.path.join(REPO, 'unreal', 'Pipeline', 'out', 'ue')
SOURCES = [
    ('Museum', 'unreal/Pipeline/out/museum/Museum.glb'),        # bl/museum.py (was out/campus/museum.glb, the web export)
    ('WaxIntro', 'unreal/Pipeline/out/campus/waxIntro.glb'),
    ('WaxHall', 'unreal/Pipeline/out/campus/wax.glb'),
    ('LibraryShell', 'unreal/Pipeline/out/campus/lib.glb'),
    ('School', 'unreal/Pipeline/out/campus/school.glb'),
    ('Outside', 'unreal/Pipeline/out/exterior/Outside.glb'),    # bl/exterior.py (was out/campus/outside.glb)
    ('Yard', 'unreal/Pipeline/out/campus/play.glb'),
    ('OceanDive', 'unreal/Pipeline/out/campus/dive.glb'),
    ('ReadingRoom', 'unreal/Pipeline/out/reading_room/ReadingRoom.glb'),
    ('Props', 'unreal/Pipeline/out/campus/props.glb'),          # the Wax Hall's carried props, one mesh each, in their own frames
    ('HandProps', 'unreal/Pipeline/out/props/HandProps.glb'),   # bl/props.py: the held props as real objects, one mesh per kind
    ('Seats', 'unreal/Pipeline/out/props/Seats.glb'),           # bl/seats.py: settees for the Wax Hall aisle, each seat a tagged mesh
    ('Auditorium', 'unreal/Pipeline/out/auditorium/Auditorium.glb'),   # bl/auditorium.py: the talks wing (foyer + auditorium)
    ('Classroom', 'unreal/Pipeline/out/classroom/Classroom.glb'),      # bl/classroom.py: Room 104's smartboard, desks, chairs
    ('Training', 'unreal/Pipeline/out/training/Training.glb'),         # bl/training.py: the Training Wing (the dialysis course's room)
    ('Maker', 'unreal/Pipeline/out/maker/Maker.glb'),                  # bl/maker.py: the 360 storytelling course in Room 101
    ('Stories', 'unreal/Pipeline/out/stories/Stories.glb'),            # bl/stories.py: the Lost Stories cabin at the end of the path
    ('PopUp', 'unreal/Pipeline/out/popup/PopUp.glb'),                  # bl/popup.py: the pop-up books on the Reading Room's south table
    ('People', 'unreal/Pipeline/out/people/People.glb'),               # bl/figure.py: a guided visit's people (AWTACharacter's figure)
]
TAG = re.compile(r'^(item|token|ride|staff|station|book|bp|prop|seat|screen|spot|popup|figure)__')
REFITS = os.path.join(REPO, 'unreal', 'Pipeline', 'content', 'refits.json')


def tag_of(o):
    p = o
    while p is not None:
        if TAG.match(p.name):
            return p.name.split('.')[0]
        p = p.parent
    return None


def clean_name(s):
    return re.sub(r'[^A-Za-z0-9_]+', '_', s).strip('_')[:60] or 'Mesh'


def load_refit(name):
    try:
        with open(REFITS) as f:
            return json.load(f).get(name)
    except (OSError, ValueError):
        return None


def apply_refit(name, meshes):
    """content/refits.json for this asset, on meshes already baked to world space: drop, then move groups, then
    clip (faces lying wholly inside a campus box go, e.g. the yard fence where the Training Wing's doorway is).
    Returns the meshes that remain and a short report."""
    import math
    import bmesh
    from mathutils import Matrix, Vector
    spec = load_refit(name)
    if not spec:
        return meshes, None
    def matches(o, pats):
        base = o.name
        return any(re.fullmatch(p, base) for p in pats)
    dropped = [o for o in meshes if matches(o, spec.get('drop', []))]
    dropped_names = sorted(o.name for o in dropped)
    keep = [o for o in meshes if o not in dropped]
    for o in dropped:
        bpy.data.objects.remove(o, do_unlink=True)
    moved = []
    for mv in spec.get('move', []):
        group = [o for o in keep if matches(o, [re.escape(m) for m in mv['meshes']])]
        px, pz = mv['pivot']; tx, tz = mv['to']
        # campus (x, z) -> Blender (x, -z); a turn about campus +y is the same angle about Blender +Z
        m = (Matrix.Translation(Vector((tx, -tz, mv.get('dy', 0.0)))) @ Matrix.Rotation(math.radians(mv.get('rotate_deg', 0.0)), 4, 'Z')
             @ Matrix.Translation(Vector((-px, pz, 0.0))))
        for o in group:
            o.data.transform(m)
        moved.append('%s: %d of %d' % (mv.get('what', mv['meshes'][0]), len(group), len(mv['meshes'])))
    clipped = []
    for cp in spec.get('clip', []):
        x0, y0, z0, x1, y1, z1 = cp['box']                     # campus metres: x0, y0, z0, x1, y1, z1
        lo = Vector((x0 - 1e-4, -z1 - 1e-4, y0 - 1e-4)); hi = Vector((x1 + 1e-4, -z0 + 1e-4, y1 + 1e-4))
        n = 0
        for o in keep:
            if cp.get('meshes') and not matches(o, [re.escape(m) for m in cp['meshes']]):
                continue
            me = o.data
            inside = [all(lo[i] <= v.co[i] <= hi[i] for i in range(3)) for v in me.vertices]
            gone = [p.index for p in me.polygons if all(inside[i] for i in p.vertices)]
            if not gone:
                continue
            bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[bm.faces[i] for i in gone], context='FACES')
            bm.to_mesh(me); bm.free()
            n += len(gone)
        clipped.append('%s: %d faces' % (cp.get('what', 'box'), n))
    out = {'dropped': dropped_names, 'moved': moved}
    if clipped:
        out['clipped'] = clipped
    return keep, out


def process(name, rel):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(REPO, rel))
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    tags = {o: tag_of(o) for o in meshes}
    # Bake world transforms into the vertices, and unparent
    for o in meshes:
        mw = o.matrix_world.copy()
        o.parent = None
        if o.data.users > 1:
            o.data = o.data.copy()
        o.data.transform(mw)
        o.matrix_world.identity()
        for ca in list(o.data.color_attributes):
            o.data.color_attributes.remove(ca)
    for o in [o for o in bpy.data.objects if o.type != 'MESH']:
        bpy.data.objects.remove(o, do_unlink=True)
    meshes, refit = apply_refit(name, meshes)
    if refit:
        print(name, 'refit:', refit)
    # Group: tagged objects by tag; untagged by (first) material
    groups = {}
    for o in meshes:
        t = tags[o]
        if t:
            key = t
        else:
            mat = o.data.materials[0] if o.data.materials else None
            key = 'M_' + clean_name(mat.name if mat else 'none') + ('_%d' % len(o.data.materials) if len(o.data.materials) > 1 else '')
        groups.setdefault(key, []).append(o)
    used = set()
    for key, objs in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        if len(objs) > 1:
            bpy.ops.object.join()
        o = bpy.context.view_layer.objects.active
        nm = clean_name(key.replace('__', '__'))
        base, i = nm, 1
        while nm in used:
            i += 1
            nm = '%s_%d' % (base, i)
        used.add(nm)
        o.name = nm
        o.data.name = nm
    # Readable asset names in Unreal: M_<Asset>_<n> materials and T_<Asset>_<material>_<n> textures
    # (canvas textures from the web export have no names, which would import as image_0 ... image_442)
    for i, m in enumerate(sorted({m for o in bpy.data.objects if o.type == 'MESH' for m in o.data.materials if m}, key=lambda m: m.name)):
        base = clean_name(m.name) if not m.name.lower().startswith(('material', 'mat_')) else 'Mat'
        m.name = 'M_%s_%s_%03d' % (name, base[:24], i)
        if m.node_tree:
            for k, n in enumerate([n for n in m.node_tree.nodes if getattr(n, 'image', None)]):
                n.image.name = 'T_%s_%s_%03d_%d' % (name, base[:24], i, k) if n.image.users <= 1 else n.image.name
    for k, img in enumerate(bpy.data.images):
        if not img.name.startswith('T_'):
            img.name = 'T_%s_shared_%03d' % (name, k)
    fp = os.path.join(OUT, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=fp, export_format='GLB', export_yup=True, export_apply=False, export_texcoords=True,
                              export_normals=True, export_tangents=True, export_materials='EXPORT', export_image_format='AUTO',
                              export_vertex_color='NONE', export_lights=False, export_cameras=False)
    objs = [o for o in bpy.data.objects if o.type == 'MESH']
    tris = 0
    for o in objs:
        o.data.calc_loop_triangles()
        tris += len(o.data.loop_triangles)
    out = {'file': name + '.glb', 'source': rel, 'meshes': len(objs), 'tagged': sorted(o.name for o in objs if TAG.match(o.name)),
           'triangles': tris, 'bytes': os.path.getsize(fp)}
    if refit:
        out['refit'] = refit
    return out


UNITS = ('metres in glTF (Y up); Unreal import maps glTF (x, y, z) m -> UE (X=x, Y=z, Z=y) cm. '
         'Every mesh is baked in world space: spawn at UE (0,0,0), rotation 0, scale 1.')


def main():
    """Name assets on the command line to re-prepare just those, e.g.

        blender -b --python unreal/Pipeline/blender/prepare_for_unreal.py -- ReadingRoom

    The exported wings under out/campus are too big to keep in the repo, so after a fresh clone only the
    prepared out/ue copies exist. Naming one asset lets it be rebuilt on its own; the manifest is merged
    rather than replaced, and a source that is not on disk is reported and skipped instead of failing."""
    os.makedirs(OUT, exist_ok=True)
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    wanted = {a for a in argv if not a.startswith('-')}
    man_path = os.path.join(OUT, 'manifest.json')
    man = {'units': UNITS, 'assets': {}}
    if os.path.exists(man_path):
        with open(man_path) as f:
            man = json.load(f)
        man.setdefault('units', UNITS)
        man.setdefault('assets', {})
    done = 0
    for name, rel in SOURCES:
        if wanted and name not in wanted:
            continue
        if not os.path.exists(os.path.join(REPO, rel.replace('/', os.sep))):
            print('skip', name, '- no', rel)
            continue
        man['assets'][name] = process(name, rel)
        a = man['assets'][name]
        print(name, a['meshes'], 'meshes', a['triangles'], 'tris', a['bytes'], 'bytes')
        done += 1
    with open(man_path, 'w') as f:
        json.dump(man, f, indent=1)
    print('prepared', done, 'of', len(wanted) if wanted else len(SOURCES))


if __name__ == '__main__':
    main()
