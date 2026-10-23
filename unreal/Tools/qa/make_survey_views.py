"""Camera lists for WTAShotList that survey the campus for the visual faults a person finds walking round: every
doorway from both sides (straight on and from either side, looking up at the head), every exhibit straight on and
from 35 degrees either way, every room toward each wall, the library's displayed books, the walls trees stand near,
and each Wax Hall stage from far and near, four frames each.

    python3 unreal/Tools/qa/make_survey_views.py      # -> survey_doors.txt, survey_walls.txt, survey_wax.txt,
                                                      #    survey_fixes.txt (Ev's Oct 23 list, checked) here

On the PC: copy one to WalkTheArchive/Saved/QA/ and run `WTAShotList 3 <file>` in -game.
"""
import json, math, os
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
EYE = 1.62
def ue(x, y, z): return (100 * x, 100 * z, 100 * y)
def line(name, x, y, z, yaw, pitch=0.0):
    X, Y, Z = ue(x, y, z)
    return '%s | %.0f %.0f %.0f | %.1f %.1f' % (name, X, Y, Z, yaw % 360, pitch)

# ---- doors: (name, axis, at, centre, width, height, floor y, distance on - side, distance on + side)
DOORS = [
 ('mus_lobby_g1', 'z', -6.0, 0.0, 3.2, 3.1, 0, 2.6, 2.6),
 ('mus_g1_g2', 'z', -18.0, 0.0, 3.2, 3.1, 0, 2.6, 2.6),
 ('mus_g2_g3', 'z', -30.0, 0.0, 3.2, 3.1, 0, 2.6, 2.6),
 ('mus_g3_wax', 'z', -42.15, 0.0, 3.2, 3.3, 0, 2.6, 2.6),
 ('lobby_hallL', 'x', -6.0, -3.0, 2.4, 3.1, 0, 2.6, 2.6),
 ('lobby_hallR', 'x', 6.0, -3.0, 2.4, 3.1, 0, 2.6, 2.6),
 ('hallL_library', 'x', -12.0, -3.0, 3.6, 3.65, 0, 2.6, 2.6),
 ('library_stacks', 'x', -23.0, -3.0, 4.4, 3.4, 0, 2.6, 2.6),
 ('hallR_school', 'x', 12.0, -3.0, 3.6, 3.65, 0, 2.6, 2.6),
 ('school_yard', 'x', 34.0, -3.0, 3.2, 3.0, 0, 2.6, 2.6),
 ('hallR_foyer', 'z', -4.775, 9.0, 2.2, 2.8, 0, 2.6, 1.6),
 ('foyer_aud', 'z', -13.875, 9.025, 2.6, 3.0, 0, 2.6, 2.6),
 ('aud_training', 'x', 20.975, -15.6, 1.2, 2.2, 0, 2.2, 2.2),
 ('training_yard', 'x', 32.225, -25.8, 1.8, 2.4, 0, 2.6, 2.6),
 ('lobby_rotunda', 'z', 0.0, 0.0, 3.2, 4.8, 0, 2.6, 2.6),
 ('front_door', 'z', 11.0, 0.0, 3.2, 5.2, 0, 3.4, 4.0),
 ('school_101', 'z', -4.75, 19.0, 1.8, 2.3, 0, 2.6, 2.2),
 ('school_102', 'z', -4.75, 29.0, 1.8, 2.3, 0, 2.6, 2.2),
 ('school_103', 'z', -1.25, 19.0, 1.8, 2.3, 0, 2.2, 2.6),
 ('school_104', 'z', -1.25, 29.0, 1.8, 2.3, 0, 2.2, 2.6),
 ('cabin', 'z', 72.07, -4.0, 1.1, 2.2, 0.45, 1.6, 2.4),
]
def door_views():
    out = []
    for (name, axis, at, c, w, h, fy, dneg, dpos) in DOORS:
        for side, d in (('a', -dneg), ('b', dpos)):
            # camera on the side at signed offset d along the axis; it looks back toward the door
            for tag, lat in (('c', 0.0), ('l', -1.3), ('r', 1.3)):
                if axis == 'z':
                    x, z = c + lat, at + d
                    yaw = 270.0 if d > 0 else 90.0          # +z (south) side looks north (UE -Y)
                    # turn toward the door centre
                    yaw = math.degrees(math.atan2((at - z), (c - x)))
                else:
                    x, z = at + d, c + lat
                    yaw = math.degrees(math.atan2((c - z), (at - x)))
                horiz = math.hypot(at - (z if axis == 'z' else x), lat)
                pitch = math.degrees(math.atan2(h + 0.2 - EYE, max(horiz, 0.5)))
                out.append(line('door_%s_%s%s' % (name, side, tag), x, fy + EYE, z, yaw, min(pitch, 42.0)))
    return out

def exhibit_views():
    out = []
    ex = json.load(open(os.path.join(REPO, 'WalkTheArchive/Data/Exhibits.json')))
    for r in ex:
        v = r.get('View') or {}
        if not v.get('bValid'):
            continue
        L = v['Location']
        out.append('ex_%s | %.0f %.0f %.0f | %.1f %.1f' % (r['Name'], L['X'], L['Y'], L['Z'], v['Yaw'], v.get('Pitch', 0)))
        # an oblique view from 2 m along the wall, so a column or a pilaster in front would show
        yaw = math.radians(v['Yaw'])
        # the exhibit's own location: look at it from 30 degrees off
        E = r['Location']
        for s in (-1, 1):
            ang = yaw + s * math.radians(35)
            dist = math.hypot(E['X'] - L['X'], E['Y'] - L['Y'])
            cx = E['X'] - math.cos(ang) * dist
            cy = E['Y'] - math.sin(ang) * dist
            out.append('ex_%s_o%s | %.0f %.0f %.0f | %.1f %.1f' % (r['Name'], 'l' if s < 0 else 'r', cx, cy, L['Z'], math.degrees(ang), v.get('Pitch', 0)))
    return out

def room_views():
    out = []
    rooms = json.load(open(os.path.join(REPO, 'Pipeline/content/rooms.json')))
    for r in rooms:
        if r['id'] in ('yard', 'wax'):
            continue
        cx, cz = (r['x0'] + r['x1']) / 2, (r['z0'] + r['z1']) / 2
        for yaw in (0, 90, 180, 270):
            out.append(line('room_%s_%03d' % (r['id'], yaw), cx, EYE, cz, yaw, 3.0))
    # the classroom from its back corners too
    for (n, x, z, yaw) in (('cls_back_l', 25.0, 6.3, 300), ('cls_back_r', 25.0, -0.6, 60), ('lab_corner', 26.3, -12.3, 330), ('studio_corner', 14.8, -12.2, 330), ('bp_corner', 13.0, 6.3, 300)):
        out.append(line('room_%s' % n, x, EYE, z, yaw, 3.0))
    return out

def library_views():
    out = []
    # the display table's covers (x -16.6..-13.4, z 0.57..1.18, tilted toward -z): from 1.2 m north of them, looking south
    for i, x in enumerate((-16.0, -15.0, -14.0)):
        out.append(line('lib_display_%d' % i, x, 1.55, -0.4, 90.0, -32.0))
    out.append(line('lib_display_wide', -15.0, EYE, -1.6, 90.0, -22.0))
    # the stacks' end covers at z -0.52 (facing -z) and -5.48 (facing +z)
    for x in (-24.0, -26.2, -28.4, -30.6):
        out.append(line('lib_stack_n_%d' % int(-x * 10), x, EYE, -2.0, 90.0, -12.0))
        out.append(line('lib_stack_s_%d' % int(-x * 10), x, EYE, -4.0, 270.0, -12.0))
    return out

def tree_views():
    out = []
    # galleries 2 and 3, west wall (trees at (-8.5, -20) and (-9, -31) stand outside it)
    for (n, z) in (('g2w', -20.0), ('g3w', -31.0)):
        out.append(line('tree_%s' % n, -1.0, EYE, z, 180.0, 12.0))
        out.append(line('tree_%s_up' % n, -3.0, EYE, z + 2.5, 200.0, 30.0))
    # training wing south wall (tree at (24, -30)), room 104 east wall (tree at (37.2, 6.4))
    out.append(line('tree_training_s', 24.0, EYE, -20.0, 90.0, 15.0))
    out.append(line('tree_room104_e', 29.0, EYE, 4.5, 0.0, 15.0))
    out.append(line('tree_rotunda_e', 1.5, EYE, 5.8, 0.0, 20.0))
    out.append(line('tree_library_n', -18.0, EYE, 4.0, 90.0, 15.0))
    out.append(line('tree_school_n', 20.0, EYE, 4.0, 90.0, 15.0))
    return out

def wax_views():
    out = []
    ws = json.load(open(os.path.join(REPO, 'WalkTheArchive/Data/WaxScenes.json')))
    for r in ws:
        S = r['StageLocation']; yaw = math.radians(r['StageYaw'])
        for tag, d, pitch in (('far', 430.0, -6.0), ('near', 270.0, -4.0)):
            cx = S['X'] + math.cos(yaw) * d; cy = S['Y'] + math.sin(yaw) * d
            look = (r['StageYaw'] + 180.0) % 360
            for k in range(4):
                out.append('wax_%s_%s_%d | %.0f %.0f %.0f | %.1f %.1f' % (r['Name'], tag, k, cx, cy, 162, look, pitch))
    return out

def look(name, eye, at):
    """A camera at eye looking at at (campus metres)."""
    dx, dy, dz = at[0] - eye[0], at[1] - eye[1], at[2] - eye[2]
    return line(name, eye[0], eye[1], eye[2], math.degrees(math.atan2(dz, dx)), math.degrees(math.atan2(dy, math.hypot(dx, dz))))

def fix_views():
    """Ev's Oct 23 list, checked: the museum's glass cases (the third one turning: three frames), the exhibits in
    their gilt panels, the museum's doorway heads, the library's display covers, the trees by the galleries, the Wax
    Hall's reading rails and the scenes whose acting changed (near, four frames each)."""
    out = []
    for (n, z) in (('headset', -12.0), ('playbooks', -24.0)):
        out.append(look('case_%s' % n, (-0.7, 1.65, z + 1.1), (-2.6, 1.3, z)))
    for k in range(3):
        out.append(look('case_spin_%d' % k, (-1.3, 1.55, -35.2), (-2.6, 1.4, -36.0)))
    ex = {r['Name']: r for r in json.load(open(os.path.join(REPO, 'WalkTheArchive/Data/Exhibits.json')))}
    for n in ('ca-200', 'nv-2017', 'dialysis', 'mission', 'cil-talks', 'ukraine'):
        v = ex[n]['View']; L = v['Location']
        out.append('ex_%s | %.0f %.0f %.0f | %.1f %.1f' % (n, L['X'], L['Y'], L['Z'], v['Yaw'], v.get('Pitch', 0)))
    out.append(look('gallery2_west', (1.5, EYE, -20.0), (-6.0, 2.6, -25.0)))
    doors = [d for d in door_views() if d.split(' ')[0].endswith(('ac', 'bc')) and '_mus_' in d.split(' ')[0]]
    out += doors + library_views()[:4] + tree_views()[:4]
    for (n, x, z, s) in (('2016', -4.42, -49.78, 1), ('2017a', 4.42, -46.42, -1)):
        out.append(look('rail_%s' % n, (x + 1.8 * s, 1.6, z + 1.2), (x, 0.92, z)))
    for (n, x) in (('2024', -2.66), ('2025', 5.64)):
        out.append(look('rail_%s' % n, (x, 1.6, -74.9), (x, 0.92, -76.92)))
    out += [w for w in wax_views() if '_near_' in w and 'wax-2018a' not in w]
    return out

OUT = os.path.dirname(os.path.abspath(__file__))
files = {'survey_fixes.txt': fix_views(), 'survey_doors.txt': door_views(), 'survey_walls.txt': exhibit_views() + room_views() + library_views() + tree_views(), 'survey_wax.txt': wax_views()}
for fn, ls in files.items():
    open(os.path.join(OUT, fn), "w").write('\n'.join(ls) + '\n')
    print(fn, len(ls))
