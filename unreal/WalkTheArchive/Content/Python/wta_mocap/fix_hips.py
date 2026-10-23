"""Puts the retargeted clips' pelvis back where the hips are.

The Mixamo -> MetaHuman retarget (build.py) leaves every clip's pelvis bone about 17 cm above the hips: the
pelvis's children (spine_01 and the two thighs) are keyed that much further down from it than the body's
reference pose has them (spine_01 15 cm below the pelvis instead of 2 cm above, the thighs 20 cm below instead
of 3), so the chain still reaches the floor while the pelvis floats up inside the belly. On a body that is
invisible in the skeleton but not in the skin: everything weighted to the pelvis - the hips, the waistband, a
jacket's hem - rides 17 cm up into the torso, and the wax figures' jackets bunch at the waist.

The fix keeps every bone where the clip puts it and moves only the pelvis: at each key, the pelvis moves by the
mean of its children's offset errors (in its own frame), and the children take the reference offsets, so the
spine and legs stay put and the hips come down to them. The error is the same in every clip (a retarget
constant), standing or sitting; a clip whose children already sit where the reference has them (the staff's
idle) is left alone.

    import wta_mocap.fix_hips as h; h.run()             # from the editor's Python; build.run() calls it last
    h.run(dry=True)                                     # report only

A fixed clip carries the metadata tag WTA_HIPS_FIXED, so a second run leaves it alone. Logs WTA_FIX_HIPS; with
report=<path> also writes per clip how far the pelvis moved and how far any child ended up from where it was.
"""
import unreal

from . import fix_feet

MOCAP_DIR = '/Game/WTA/Characters/Common/Anims/Mocap'
CHILDREN = ['spine_01', 'thigh_l', 'thigh_r']
OFF_CM = 2.0                                            # a mean child offset error below this is no error
MARK = 'WTA_HIPS_FIXED'


def _ref_offsets():
    """The body's reference translation of each of the pelvis's children (its parent-space offset)."""
    mesh = unreal.load_asset(fix_feet.BODY)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, -10000))
    comp = actor.get_editor_property('skeletal_mesh_component')
    if hasattr(comp, 'set_skeletal_mesh_asset'):
        comp.set_skeletal_mesh_asset(mesh)
    else:
        comp.set_editor_property('skeletal_mesh', mesh)
    out = {b: comp.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_PARENT_BONE_SPACE).translation for b in CHILDREN}
    actor.destroy_actor()
    return out


def _clips():
    """Every retargeted clip: the AnimSequences in MOCAP_DIR."""
    return sorted(p.split('.')[0] for p in unreal.EditorAssetLibrary.list_assets(MOCAP_DIR, recursive=False, include_folder=False)
                  if p.rsplit('/', 1)[-1].startswith('AS_WTA_'))


def _is_fixed(seq):
    try:
        return unreal.EditorAssetLibrary.get_metadata_tag(seq, MARK) not in (None, '')
    except Exception:
        return False


def _sub(a, b):
    return unreal.Vector(a.x - b.x, a.y - b.y, a.z - b.z)


def _len(v):
    return (v.x * v.x + v.y * v.y + v.z * v.z) ** 0.5


def _rotate(q, v):
    """v turned by the unit quaternion q: v + w t + q x t, t = 2 q x v."""
    tx = 2.0 * (q.y * v.z - q.z * v.y)
    ty = 2.0 * (q.z * v.x - q.x * v.z)
    tz = 2.0 * (q.x * v.y - q.y * v.x)
    return unreal.Vector(v.x + q.w * tx + (q.y * tz - q.z * ty),
                         v.y + q.w * ty + (q.z * tx - q.x * tz),
                         v.z + q.w * tz + (q.x * ty - q.y * tx))


def run(dry=False, report=None):
    lines = []
    ref = _ref_offsets()
    lines.append('reference offsets: ' + ', '.join('%s (%.1f %.1f %.1f)' % (b, v.x, v.y, v.z) for b, v in ref.items()))
    fixed = []
    for path in _clips():
        seq = unreal.load_asset(path)
        name = path.rsplit('/', 1)[-1]
        if not isinstance(seq, unreal.AnimSequence):
            continue
        if _is_fixed(seq):
            lines.append('%s: already fixed' % name)
            continue
        pelvis = fix_feet._keys(seq, 'pelvis')
        kids = {b: fix_feet._keys(seq, b) for b in CHILDREN}
        n = len(pelvis[0])
        moved, worst = [], 0.0
        new_pos = []
        for k in range(n):
            errs = [_sub(kids[b][0][k], ref[b]) for b in CHILDREN]
            d = unreal.Vector(sum(e.x for e in errs) / 3.0, sum(e.y for e in errs) / 3.0, sum(e.z for e in errs) / 3.0)
            for e in errs:
                worst = max(worst, _len(_sub(e, d)))
            shift = _rotate(pelvis[1][k], d)
            moved.append(shift)
            p = pelvis[0][k]
            new_pos.append(unreal.Vector(p.x + shift.x, p.y + shift.y, p.z + shift.z))
        mean = unreal.Vector(sum(v.x for v in moved) / n, sum(v.y for v in moved) / n, sum(v.z for v in moved) / n)
        if _len(mean) < OFF_CM:
            lines.append('%s: hips already in place (pelvis would move %.1f cm), left alone' % (name, _len(mean)))
            continue
        lines.append('%s: pelvis moves (%.1f %.1f %.1f) cm on average; a child lands at most %.2f cm from where it was' % (
            name, mean.x, mean.y, mean.z, worst))
        if dry:
            continue
        ok = bool(seq.controller.set_bone_track_keys('pelvis', new_pos, pelvis[1], pelvis[2], False))
        for b in CHILDREN:
            ok = bool(seq.controller.set_bone_track_keys(b, [ref[b]] * n, kids[b][1], kids[b][2], False)) and ok
        if not ok:
            lines.append('FAILED %s: the keys did not take, not saved' % name)
            continue
        unreal.EditorAssetLibrary.set_metadata_tag(seq, MARK, '%.1f %.1f %.1f' % (mean.x, mean.y, mean.z))
        unreal.EditorAssetLibrary.save_loaded_asset(seq, False)
        fixed.append(name)
    if report:
        with open(report, 'w') as fh:
            fh.write('\n'.join(lines) + '\n')
    unreal.log('WTA_FIX_HIPS %s: %d clips fixed' % ('dry run' if dry else 'done', len(fixed)))
    return fixed
