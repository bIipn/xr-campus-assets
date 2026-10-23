"""Turns the retargeted Wax Hall clips' feet the right way.

The Mixamo -> MetaHuman retarget (build.py) leaves the standing clips' feet pointing straight down, en pointe: the
foot -> ball vector of a standing idle is (0, -1, -13) cm where the body's bind pose has (2, 12.5, -6), so from the
front a shoe shows its heel and reads as a foot put on backwards. The error is the same turn in each foot's own frame
in every standing clip (64 to 70 degrees about the foot's local Z, clip after clip), so every key of foot_l / foot_r
in those clips gets one correction: L' = L * K, K a turn about the axis that takes the idle's foot onto the bind
pose's, by the median over the clips of the angle that brings the toes back to the bind pose's drop below the ankle.
Seated, kneeling, crouching and floor clips are left as they are: their ankles ride high, so turned feet would hang
in the air (as they are, the toes reach the floor).

    import wta_mocap.fix_feet as f; f.run()            # from the editor's Python; build.run() calls it last
    f.run(dry=True)                                    # report only

A fixed clip carries the metadata tag WTA_FEET_FIXED, so a second run leaves it alone. Logs WTA_FIX_FEET; with
report=<path> also writes the per-clip angles there.
"""
import math
import unreal

MOCAP = '/Game/WTA/Characters/Common/Anims/Mocap/AS_WTA_'
BODY = '/Game/WTA/Characters/wax-2016-teen/Body/SKM_MHC_wax-2016-teen_BodyMesh'
STANDING = ['idle', 'idle_b', 'idle_happy', 'look_around', 'think', 'talk', 'talk_two', 'present', 'present_b', 'nod',
            'point', 'point_fwd', 'clap', 'cheer', 'wave', 'reach', 'pick_one', 'carry', 'tablet', 'phone', 'shelf']
# other standing clips the people play: the staff's idle (UWTAPeopleLibrary::DefaultIdlePath)
EXTRA = ['/Game/WTA/Characters/Common/Anims/AS_WTA_StandIdle.AS_WTA_StandIdle']
EN_POINTE = -9.5                                        # cm: a mean toe drop below this is a foot pointing down
CHAIN = {'l': ['root', 'pelvis', 'thigh_l', 'calf_l', 'foot_l', 'ball_l'],
         'r': ['root', 'pelvis', 'thigh_r', 'calf_r', 'foot_r', 'ball_r']}
MARK = 'WTA_FEET_FIXED'


def _bind():
    """The body's bind pose: each foot's local transform, and foot -> ball in component space."""
    mesh = unreal.load_asset(BODY)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, -10000))
    comp = actor.get_editor_property('skeletal_mesh_component')
    if hasattr(comp, 'set_skeletal_mesh_asset'):
        comp.set_skeletal_mesh_asset(mesh)
    else:
        comp.set_editor_property('skeletal_mesh', mesh)
    out = {}
    for side in ('l', 'r'):
        out['foot_' + side] = comp.get_socket_transform('foot_' + side, unreal.RelativeTransformSpace.RTS_PARENT_BONE_SPACE)
        f = comp.get_socket_location('foot_' + side)
        b = comp.get_socket_location('ball_' + side)
        out['drop_' + side] = b.z - f.z
        out['vec_' + side] = (b.x - f.x, b.y - f.y, b.z - f.z)
    actor.destroy_actor()
    return out


def _local(seq, bone, t):
    return unreal.AnimationLibrary.get_bone_pose_for_time(seq, bone, t, False)


def _foot_vec(seq, side, t, rot=None):
    """foot -> ball in component space at time t, the foot's local rotation replaced by rot if given."""
    xf = None
    pts = []
    for b in CHAIN[side]:
        local = _local(seq, b, t)
        if rot is not None and b == 'foot_' + side:
            fixed = unreal.Transform()
            fixed.translation = local.translation
            fixed.rotation = rot
            fixed.scale3d = local.scale3d
            local = fixed
        xf = local if xf is None else local.multiply(xf)
        pts.append(xf.translation)
    f, b = pts[4], pts[5]
    return (b.x - f.x, b.y - f.y, b.z - f.z)


def _turn(axis, deg):
    h = math.radians(deg) / 2.0
    s = math.sin(h)
    return unreal.Quat(axis.x * s, axis.y * s, axis.z * s, math.cos(h))


def _mean_drop(seq, side, axis, deg, times):
    k = _turn(axis, deg)
    return sum(_foot_vec(seq, side, t, _local(seq, 'foot_' + side, t).rotation * k)[2] for t in times) / len(times)


def _solve(seq, side, axis, want, times):
    """The turn about axis (degrees, 0 to -110) that brings the clip's mean toe drop to want, by bisection."""
    lo, hi = -110.0, 0.0
    f_lo = _mean_drop(seq, side, axis, lo, times) - want
    f_hi = _mean_drop(seq, side, axis, hi, times) - want
    if f_lo * f_hi > 0:
        return None
    for _ in range(24):
        mid = (lo + hi) / 2
        f_mid = _mean_drop(seq, side, axis, mid, times) - want
        if f_mid * f_lo <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2


def _is_fixed(seq):
    try:
        return unreal.EditorAssetLibrary.get_metadata_tag(seq, MARK) not in (None, '')
    except Exception:
        return False


def run(dry=False, report=None):
    lines = []
    bind = _bind()
    idle = unreal.load_asset(MOCAP + 'idle')
    t_mid = idle.get_play_length() * 0.5
    axes = {}
    for side in ('l', 'r'):
        k = _local(idle, 'foot_' + side, t_mid).rotation.inversed() * bind['foot_' + side].rotation
        axes[side] = k.get_rotation_axis()
        lines.append('axis %s (%.3f %.3f %.3f), idle-to-bind turn %.1f deg; bind foot->ball %s' % (
            side, axes[side].x, axes[side].y, axes[side].z, math.degrees(k.get_angle()), tuple(round(c, 1) for c in bind['vec_' + side])))
    angles = {'l': [], 'r': []}
    seqs = {}
    for name in STANDING + EXTRA:
        seq = unreal.load_asset(name if name.startswith('/') else MOCAP + name)
        if seq is None:
            lines.append('%s: missing' % name)
            continue
        if _is_fixed(seq):
            lines.append('%s: already fixed' % name)
            continue
        times = [seq.get_play_length() * (i + 0.5) / 8 for i in range(8)]
        drops = [_mean_drop(seq, side, axes[side], 0.0, times) for side in ('l', 'r')]
        if max(drops) > EN_POINTE:
            lines.append('%s: feet already flat (toe drop %.1f, %.1f cm), left alone' % (name, drops[0], drops[1]))
            continue
        seqs[name] = seq
        for side in ('l', 'r'):
            a = _solve(seq, side, axes[side], bind['drop_' + side], times)
            if a is not None:
                angles[side].append(a)
            lines.append('%s %s: angle %s' % (name, side, 'none' if a is None else '%.1f' % a))
    med = {}
    for side in ('l', 'r'):
        v = sorted(angles[side])
        med[side] = v[len(v) // 2] if v else None
        lines.append('median angle %s: %s' % (side, med[side]))
    fixed = []
    if not dry and med['l'] is not None and med['r'] is not None:
        for name, seq in seqs.items():
            ok = True
            for side in ('l', 'r'):
                bone = 'foot_' + side
                pos, rot, scl = unreal.AnimationLibrary.get_raw_track_data(seq, bone)
                k = _turn(axes[side], med[side])
                ok = seq.controller.set_bone_track_keys(bone, pos, [q * k for q in rot], scl, True) and ok
            unreal.EditorAssetLibrary.set_metadata_tag(seq, MARK, 'l %.2f r %.2f' % (med['l'], med['r']))
            unreal.EditorAssetLibrary.save_loaded_asset(seq, False)
            t = seq.get_play_length() * 0.5
            after = [_foot_vec(seq, s, t) for s in ('l', 'r')]
            lines.append('fixed %s (%s): foot->ball now l %s r %s' % (name, ok, tuple(round(c, 1) for c in after[0]), tuple(round(c, 1) for c in after[1])))
            fixed.append(name)
    if report:
        with open(report, 'w') as fh:
            fh.write('\n'.join(lines) + '\n')
    unreal.log('WTA_FIX_FEET %s: %d clips fixed, median angles l %s r %s' % ('dry run' if dry else 'done', len(fixed), med['l'], med['r']))
    return fixed
