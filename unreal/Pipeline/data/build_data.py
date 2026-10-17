"""
Build the Unreal DataTable JSON files for Walk the Archive.

Reads the content extracted from the web campus (unreal/Pipeline/content/*.json, made by
content/extract_content.mjs from parts/*.js) and the campus layout (unreal/Pipeline/layout/layout.json),
converts every position to Unreal centimetres and axes, and writes one JSON file per row struct to
unreal/WalkTheArchive/Data/. Each file is an array of rows in the shape Unreal's
DataTableFunctionLibrary.fill_data_table_from_json_string expects: {"Name": <row id>, <Field>: <value>, ...}.

Every row is checked against unreal/contract/structs.json (exact field names, types and order), so the
C++ row structs, this converter and the editor import stay in step.

Run (Python 3.9+, standard library only), from anywhere:
    python3 unreal/Pipeline/data/build_data.py
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UNREAL = os.path.abspath(os.path.join(HERE, '..', '..'))
CONTENT = os.path.join(UNREAL, 'Pipeline', 'content')
LAYOUT = os.path.join(UNREAL, 'Pipeline', 'layout', 'layout.json')
ART_DIR = os.path.join(UNREAL, 'Pipeline', 'out', 'campus', 'art')
STRUCTS = os.path.join(UNREAL, 'contract', 'structs.json')
OUT = os.path.join(UNREAL, 'WalkTheArchive', 'Data')
EYE_CM = 162.0


def load(name):
    with open(os.path.join(CONTENT, name), encoding='utf-8') as f:
        return json.load(f)


# ---------- conversions (contract section 2) ----------
def vec(x, y, z):
    return {'X': round(x, 2), 'Y': round(y, 2), 'Z': round(z, 2)}


def ue_pos(x, y, z):
    """three.js campus metres (Y up) -> Unreal cm (X east, Y south, Z up)."""
    return vec(100.0 * x, 100.0 * z, 100.0 * y)


def ue_yaw(yaw_rad):
    """Web camera yaw (0 = looking toward -z) -> Unreal yaw in degrees, (-180, 180]."""
    d = (-90.0 - math.degrees(yaw_rad)) % 360.0
    return round(d - 360.0 if d > 180.0 else d, 3)


def view_from_web(v):
    if not v:
        return no_view()
    return {'Location': ue_pos(v['x'], EYE_CM / 100.0, v['z']), 'Yaw': ue_yaw(v.get('yaw', 0.0)),
            'Pitch': round(math.degrees(v.get('pitch', 0.0)), 3), 'bValid': True}


def view_from_layout(v):
    """layout.json views already carry {ue: {location_cm, rotation_deg}}."""
    if not v or 'ue' not in v:
        return no_view()
    u = v['ue']
    loc = u['location_cm']
    return {'Location': vec(*loc), 'Yaw': round(u['rotation_deg']['yaw'], 3), 'Pitch': round(u['rotation_deg']['pitch'], 3), 'bValid': True}


def no_view():
    return {'Location': vec(0, 0, 0), 'Yaw': 0.0, 'Pitch': 0.0, 'bValid': False}


def color(hex_str):
    """'#rrggbb' sRGB -> linear FLinearColor."""
    h = (hex_str or '#808080').lstrip('#')
    def lin(c):
        c = int(c, 16) / 255.0
        return round(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4, 5)
    return {'R': lin(h[0:2]), 'G': lin(h[2:4]), 'B': lin(h[4:6]), 'A': 1.0}


def txt(s):
    return '' if s is None else str(s)


def art_ref(item_id):
    name = 'T_Art_' + item_id.replace('-', '_')
    if os.path.exists(os.path.join(ART_DIR, item_id + '.png')):
        return '/Game/WTA/Art/%s.%s' % (name, name)
    return ''


# ---------- tables ----------
def build_sources():
    return [{'Name': s['id'], 'Label': txt(s['label']), 'Url': txt(s['url'])} for s in load('sources.json')]


def build_galleries():
    return [{'Name': 'G%d' % g['index'], 'Index': g['index'], 'Label': txt(g['label']), 'DisplayName': txt(g['name']),
             'Years': txt(g['years']), 'WallColor': color(g['wall'])} for g in load('galleries.json')]


def build_exhibits(L):
    kinds = {k['id']: k['label'] for k in load('exhibit_kinds.json')}
    lay = {e['id']: e for e in L['exhibits']}
    stages = {s['id']: s for s in L['wax_hall']['stages']}
    rows = []
    for e in load('exhibits.json'):
        le = lay.get(e['id'])
        if le:
            loc = vec(*le['ue_location_cm'])
            yaw = round(le['ue_yaw_deg'], 3)
            # pedestal objects (headset, playbooks) have no artwork size: use the glass case (0.62 x 1.0 m)
            sz = le.get('size_m') or [0.62, 1.0]
            size = {'X': round(100 * sz[0], 2), 'Y': round(100 * sz[1], 2)}
            view = view_from_layout(le['view'])
        elif e['id'] == 'freedom':
            # Freedom to Read board in the Reading Room: group at (-21.4, 0, 1.0) turned +90 deg, panel 1.3 x 0.975 m
            # 1.35 m up and 3 cm out in front, so it faces +x (east). parts/world.js:456-459
            loc = ue_pos(-21.4 + 0.03, 1.35, 1.0)
            yaw = 0.0
            size = {'X': 130.0, 'Y': 97.5}
            view = view_from_web({'x': -21.4 + 2.3, 'z': 1.0, 'yaw': math.pi / 2, 'pitch': -0.05})
        else:
            raise SystemExit('exhibit %s has no position in layout.json' % e['id'])
        rows.append({
            'Name': e['id'], 'KindId': e['kind'], 'Kind': txt(kinds.get(e['kind'], e['kind'])), 'Gallery': int(e.get('g') or 0),
            'Title': txt(e['title']), 'Date': txt(e.get('date')), 'Year': int(e.get('year') or 0), 'Description': txt(e.get('desc')),
            'More': txt(e.get('more')), 'Quote': txt(e.get('quote')), 'QuoteBy': txt(e.get('quoteBy')), 'Where': txt(e.get('where')),
            'Partners': txt(e.get('partners')), 'Sources': list(e.get('src') or []), 'Hall': '', 'bWax': False, 'WaxSceneId': 'None',
            'Art': art_ref(e['id']), 'Location': loc, 'Yaw': yaw, 'Size': size, 'View': view})
    # The 12 Wax Hall reenactment cards (their reading rail stands at the front edge of each stage)
    for w in load('wax_scenes.json'):
        it, st = w['item'], stages[w['id']]
        o = st['ue_origin_cm']
        rows.append({
            'Name': it['id'], 'KindId': it['kind'], 'Kind': txt(kinds.get(it['kind'], it['kind'])), 'Gallery': 4,
            'Title': txt(it['title']), 'Date': txt(it.get('date')), 'Year': int(it.get('year') or 0), 'Description': txt(it.get('desc')),
            'More': txt(it.get('more')), 'Quote': '', 'QuoteBy': '', 'Where': txt(it.get('where')), 'Partners': txt(it.get('partners')),
            'Sources': list(it.get('src') or []), 'Hall': txt(it.get('hall')), 'bWax': True, 'WaxSceneId': w['id'],
            'Art': '', 'Location': vec(o[0], o[1], 100.0), 'Yaw': round(st['ue_yaw_deg'], 3), 'Size': {'X': 60.0, 'Y': 40.0},
            'View': view_from_layout(st['view'])})
    return rows


def build_subjects(L):
    stacks = {s['subject']: s for s in L['library']['stacks']}
    return [{'Name': s['id'], 'DisplayName': txt(s['name']), 'Side': s['side'], 'Slot': int(s['slot']), 'Color': color(s['color']),
             'ShelfView': view_from_layout(stacks[s['id']]['shelf_view']) if s['id'] in stacks else no_view()} for s in load('subjects.json')]


def book_block(b):
    if isinstance(b, str):
        return {'Type': 'Para', 'Text': b, 'Items': []}
    if 'li' in b:
        return {'Type': 'List', 'Text': '', 'Items': [txt(x) for x in b['li']]}
    for key, typ in (('q', 'Quote'), ('quote', 'Quote'), ('note', 'Note'), ('code', 'Code'), ('p', 'Para')):
        if key in b:
            return {'Type': typ, 'Text': txt(b[key]), 'Items': []}
    raise SystemExit('unknown book block %r' % b)


def build_books():
    rows = []
    for b in load('books.json'):
        pages = [{'Heading': txt(p.get('h')), 'Blocks': [book_block(x) for x in p.get('b', [])]} for p in b['pages']]
        rows.append({'Name': b['id'], 'Subject': b['subject'], 'Title': txt(b['title']), 'Subtitle': txt(b.get('sub')),
                     'Pages': pages, 'Cover': ''})
    return rows


def build_rooms(L):
    lay = {r['id']: r for r in L['rooms']}
    maps = {m['id']: m for m in load('map_rooms.json')}
    galleries = {g['index']: g for g in load('galleries.json')}
    staff = load('staff.json')
    rows = []
    for r in load('rooms.json'):
        lr = lay[r['id']]
        info = r.get('info') or {}
        if r.get('gal') and r['gal'] in galleries:
            # Gallery rooms carry no info of their own; the web HUD (ui.js setRoom) shows the gallery's label,
            # name and years instead ("Gallery 1 of 3", "Headsets in Libraries", "2016 to 2022").
            g = galleries[r['gal']]
            info = {'k': g['label'], 'n': g['name'], 'y': g['years']}
        mn, mx = lr['ue_bounds_cm']['min'], lr['ue_bounds_cm']['max']
        if r['id'] == 'yard':
            mx = [mx[0], mx[1], max(mx[2], 3000.0)]
        sid = next((s['id'] for s in staff if r['id'] in (s.get('rooms') or [])), 'None')
        m = maps.get(r['id'], {})
        rows.append({'Name': r['id'], 'Kicker': txt(info.get('k')), 'DisplayName': txt(info.get('n')), 'Sub': txt(info.get('y')),
                     'Wing': lr.get('wing') or 'None', 'BoundsMin': vec(*mn), 'BoundsMax': vec(*mx), 'bOutdoor': r['id'] == 'yard',
                     'StaffId': sid, 'MapLabel': txt(m.get('label')), 'GoPlace': m.get('goPlace') or 'None'})
    return rows


def build_places(L):
    dirs = {d['placeId']: d['text'] for d in load('staff_answers.json')['directions']}
    stations = {s['id']: s for s in L['stations']}
    stacks = {s['subject']: s for s in L['library']['stacks']}
    rows = []
    for p in load('places.json'):
        if p['id'] in L['places']:
            v = view_from_layout(L['places'][p['id']])
        elif p.get('view'):
            v = view_from_web(p['view'])
        elif p.get('viewRef', '') and p['viewRef'].startswith('@station:') and p['viewRef'][9:] in stations:
            v = view_from_layout(stations[p['viewRef'][9:]]['view'])
        elif p.get('viewRef', '') and p['viewRef'].startswith('@shelf:') and p['viewRef'][7:] in stacks:
            v = view_from_layout(stacks[p['viewRef'][7:]]['shelf_view'])
        else:
            v = no_view()   # blueprint boards: the editor setup fills these from the bp__ meshes
        rows.append({'Name': p['id'], 'Label': txt(p['label']), 'Aliases': [txt(n) for n in (p.get('names') or [])],
                     'View': v, 'Directions': txt(dirs.get(p['id']))})
    return rows


ACT = re.compile(r"(openBook|openStation|openRide|openBp|startPaint)\(\s*(?:BOOK\[)?'?([\w-]*)'?")


def tour_action(src):
    if not src:
        return '', 'None'
    m = ACT.search(src)
    if not m:
        return '', 'None'
    fn, arg = m.group(1), m.group(2)
    if fn == 'openBook':
        return 'OpenBook', arg
    if fn == 'openStation':
        return 'OpenStation', arg
    if fn == 'openRide':
        return 'OpenRide', arg
    if fn == 'startPaint':
        return 'OpenStation', 'easel'
    if fn == 'openBp':
        return 'GoPlace', 'bp-' + arg
    return '', 'None'


def build_tour(L):
    stops = {str(s['n']): s for s in L['tour_stops']}
    rows = []
    for s in load('tour.json'):
        kind = s['kind']
        if kind == 'item':
            v, action, arg = no_view(), 'OpenItem', s['itemId']   # the exhibit's own View is used
        else:
            ls = next((x for x in L['tour_stops'] if x['kind'] == kind and 'view' in x), None)
            v = view_from_layout(ls['view']) if ls else view_from_web(s.get('view'))
            action, arg = tour_action(s.get('actSrc'))
            if kind == 'wax' and not v['bValid']:
                v = view_from_layout(L['places']['wax'])
        rows.append({'Name': 'S%02d' % s['index'], 'Index': s['index'], 'Kind': kind, 'ItemId': s.get('itemId') or 'None',
                     'Title': txt(s['title']), 'DateLabel': txt(s.get('date')), 'Body': txt(s.get('text')), 'View': v,
                     'OpenLabel': txt(s.get('openLabel')), 'Action': action or 'None', 'ActionArg': arg})
    return rows


def build_staff(L):
    lay = {s['id']: s for s in L['staff']}
    rows = []
    for s in load('staff.json'):
        ls = lay[s['id']]
        look = s.get('look') or {}
        notes = 'Rocketbox %s; body %s; top %s; bottom %s; skin %s; hair %s %s%s' % (
            look.get('av'), look.get('body'), look.get('top'), look.get('bottom'), look.get('skin'), look.get('hair'),
            look.get('hairStyle'), '; glasses' if look.get('glasses') else '')
        rows.append({'Name': s['id'], 'DisplayName': txt(s['name']), 'Role': txt(s['role']), 'Monogram': txt(s.get('mono')),
                     'Color': color(s.get('color')), 'Rooms': list(s.get('rooms') or []), 'Location': vec(*ls['ue_location_cm']),
                     'Yaw': round(ls['ue_yaw_deg'], 3), 'TalkView': view_from_layout(ls['view']), 'Greeting': txt(s.get('greeting')),
                     'GreetingShort': txt(s.get('greetingShort')), 'Help': txt(s.get('help')), 'Fallback': txt(s.get('fallback')),
                     'Chips': [txt(c if isinstance(c, str) else c.get('q') or c.get('label') or c.get('text')) for c in (s.get('chips') or [])],
                     'RocketboxId': look.get('av') or 'None', 'LookNotes': notes, 'MetaHuman': ''})
    return rows


SIMPLE = re.compile(r"^RX\.(\w+)\.test\(s\)(?:\s*&&\s*words\s*<=\s*(\d+))?(?:\s*&&\s*!travel)?$")
LITERAL = re.compile(r"^/(.+)/\.test\(s\)$")
RULE_ACTIONS = {'paint': ('GoPlace', 'studio'), 'paintBlank': ('GoPlace', 'studio'), 'station:bench': ('OpenStation', 'bench')}


def build_staff_rules():
    sa = load('staff_answers.json')
    rx = {r['id']: r['pattern'] for r in sa['rules']}
    rows, skipped = [], []
    for b in sa['presetBranches']:
        if not b.get('staticText'):
            continue
        cond = (b.get('conditionSrc') or '').strip()
        m, lit = SIMPLE.match(cond), LITERAL.match(cond)
        if m and m.group(1) in rx:
            pattern, maxw = rx[m.group(1)], int(m.group(2) or 0)
        elif lit:
            # bare word tests (/ride/, /scene|wax|figure/) were last-resort branches in the web; keep them late (Order >= 100)
            pattern, maxw = lit.group(1), 0
            b = dict(b, order=100 + int(b['order']))
        else:
            skipped.append(cond)
            continue
        act, arg = RULE_ACTIONS.get(b.get('action') or '', ('', 'None'))
        rows.append({'Name': 'R%03d' % b['order'], 'Order': int(b['order']), 'Pattern': pattern, 'MaxWords': maxw,
                     'StaffOnly': list(b.get('staffOnly') or []), 'StaffNot': list(b.get('staffNot') or []), 'Answer': txt(b['staticText']),
                     'Action': act or 'None', 'ActionArg': arg})
    return rows, skipped


def build_facts():
    return [{'Name': f['id'], 'Body': txt(f['text']), 'Sources': list(f.get('src') or [])} for f in load('facts.json')]


def build_lessons():
    return [{'Name': l['id'], 'Station': l['station'], 'Title': txt(l['title']), 'Body': txt(l['text'])} for l in load('lessons.json')]


def build_badges():
    return [{'Name': b['id'], 'DisplayName': txt(b['name']), 'How': txt(b['how'])} for b in load('badges.json')]


def build_tokens(L):
    lay = {t['id']: t for t in L['tokens']}
    feats = {f['id']: f for f in L['exterior']['features']}
    ride_at = {'coaster': feats['coaster'], 'drop': feats['drop-tower'], 'dive': feats['dive-dome']}
    rows = []
    for t in load('tokens.json'):
        if t['id'] in lay and 'ue_location_cm' in lay[t['id']]:
            loc = vec(*lay[t['id']]['ue_location_cm'])
        elif t.get('at'):
            loc = ue_pos(*t['at'])
        else:
            f = ride_at[t['ride']]['ue_location_cm']
            loc = vec(f[0], f[1], f[2] + 300.0)
        rows.append({'Name': t['id'], 'Place': txt(t['place']), 'Hint': txt(t['hint']), 'Wing': t.get('wing') or 'None',
                     'Location': loc, 'RideGate': t.get('ride') or 'None'})
    return rows


def build_wax(L):
    stages = {s['id']: s for s in L['wax_hall']['stages']}
    rows = []
    for w in load('wax_scenes.json'):
        st = stages[w['id']]
        rows.append({'Name': w['id'], 'Number': int(w['n']), 'Year': txt(w['year']), 'Title': txt(w['title']),
                     'LoopSeconds': float(w.get('loopSeconds') or 14), 'Lines': [{'Time': float(l['t']), 'Text': txt(l['text'])} for l in w['lines']],
                     'StageLocation': vec(*st['ue_origin_cm']), 'StageYaw': round(st['ue_yaw_deg'], 3), 'ItemId': w['item']['id'], 'Sequence': ''})
    return rows


def build_stations(L):
    lay = {s['id']: s for s in L['stations']}
    rows = []
    for s in load('stations.json'):
        ls, card = lay[s['id']], s.get('card') or {}
        rows.append({'Name': s['id'], 'Room': s['room'], 'Kicker': txt(s.get('kick') or card.get('k')), 'Title': txt(card.get('t')),
                     'Subtitle': txt(card.get('m')), 'GoLabel': txt(card.get('go')), 'Steps': [txt(x) for x in s.get('stepTitles') or []],
                     'Panel': [txt(p['text']) for p in (s.get('panelTexts') or []) if p.get('kind') == 'stp'][:6],
                     'bUsesHands': bool(s.get('usesHands')), 'Location': vec(*ls['ue_location_cm']), 'View': view_from_layout(ls['view'])})
    if 'easel' in lay and not any(r['Name'] == 'easel' for r in rows):
        ls = lay['easel']
        rows.append({'Name': 'easel', 'Room': 'studio', 'Kicker': 'Room 101 · 3D Art Studio', 'Title': '3D Art Studio',
                     'Subtitle': 'Paint in the air with brushes, shapes and symmetry', 'GoLabel': 'Start making art',
                     'Steps': ['Pick a brush', 'Paint in the air', 'Turn the turntable', 'Save a picture'],
                     'Panel': ['Paint in the air around the easel. Brushes, stamps, symmetry and a turntable let you build a 3D picture you can walk around.'],
                     'bUsesHands': False, 'Location': vec(*ls['ue_location_cm']), 'View': view_from_layout(ls['view'])})
    return rows


def build_rides(L):
    r = load('rides.json')
    feats = {f['id']: f for f in L['exterior']['features']}
    at = {'coaster': feats['coaster'], 'drop': feats['drop-tower'], 'dive': feats['dive-dome']}
    rows = []
    for ride in r['rides']:
        f = at[ride['id']]['ue_location_cm']
        rows.append({'Name': ride['id'], 'DisplayName': txt(ride['name']), 'Kicker': txt(ride.get('kick')), 'CardText': txt(ride.get('cardText')),
                     'CardNote': txt(ride.get('cardNote')), 'About': txt(ride.get('staffAbout')), 'Stats': txt(ride.get('staffStats')),
                     'Safety': txt(ride.get('staffSafety')), 'BadgeId': ride.get('badge') or 'None', 'Location': vec(f[0], f[1], f[2] + 120.0),
                     'ExitView': view_from_web(ride.get('exitView'))})
    return rows


# ---------- validation against the contract ----------
TYPES = {'Name': str, 'Text': str, 'String': str, 'Int': int, 'Float': (int, float), 'Bool': bool,
         'SoftTexture': str, 'SoftClass': str, 'SoftObject': str}


def check_value(v, typ, structs, where):
    if typ.startswith('Array<'):
        inner = typ[6:-1]
        assert isinstance(v, list), '%s: expected array' % where
        for i, x in enumerate(v):
            check_value(x, inner, structs, '%s[%d]' % (where, i))
    elif typ == 'Vector':
        assert isinstance(v, dict) and set(v) == {'X', 'Y', 'Z'}, '%s: bad Vector %r' % (where, v)
    elif typ == 'Vector2D':
        assert isinstance(v, dict) and set(v) == {'X', 'Y'}, '%s: bad Vector2D %r' % (where, v)
    elif typ == 'Color':
        assert isinstance(v, dict) and set(v) == {'R', 'G', 'B', 'A'}, '%s: bad Color %r' % (where, v)
    elif typ == 'View':
        check_struct(v, 'FWTAView', structs, where)
    elif typ in structs:
        check_struct(v, typ, structs, where)
    else:
        assert isinstance(v, TYPES[typ]) and not (typ in ('Int', 'Float') and isinstance(v, bool)), '%s: expected %s, got %r' % (where, typ, v)


def check_struct(row, sname, structs, where, is_row=False):
    fields = structs[sname]['fields']
    names = [f[0] for f in fields]
    keys = [k for k in row if not (is_row and k == 'Name')]
    assert keys == names, '%s: fields %s != contract %s' % (where, keys, names)
    for fname, ftype in fields:
        check_value(row[fname], ftype, structs, '%s.%s' % (where, fname))


def main():
    with open(STRUCTS, encoding='utf-8') as f:
        structs = json.load(f)['structs']
    with open(LAYOUT, encoding='utf-8') as f:
        L = json.load(f)
    rules, skipped = build_staff_rules()
    tables = {
        'FWTASourceRow': build_sources(), 'FWTAGalleryRow': build_galleries(), 'FWTAExhibitRow': build_exhibits(L),
        'FWTASubjectRow': build_subjects(L), 'FWTABookRow': build_books(), 'FWTARoomRow': build_rooms(L),
        'FWTAPlaceRow': build_places(L), 'FWTATourStopRow': build_tour(L), 'FWTAStaffRow': build_staff(L),
        'FWTAStaffRuleRow': rules, 'FWTAFactRow': build_facts(), 'FWTALessonRow': build_lessons(),
        'FWTABadgeRow': build_badges(), 'FWTATokenRow': build_tokens(L), 'FWTAWaxSceneRow': build_wax(L),
        'FWTAStationRow': build_stations(L), 'FWTARideRow': build_rides(L),
    }
    missing = [s for s, d in structs.items() if d['row'] and s not in tables]
    assert not missing, 'no builder for %s' % missing
    os.makedirs(OUT, exist_ok=True)
    for sname, rows in tables.items():
        names = [r['Name'] for r in rows]
        assert len(names) == len(set(names)), '%s: duplicate row names' % sname
        for r in rows:
            check_struct(r, sname, structs, '%s[%s]' % (sname, r['Name']), is_row=True)
        fn = structs[sname]['file']
        with open(os.path.join(OUT, fn), 'w', encoding='utf-8') as f:
            json.dump(rows, f, indent=1, ensure_ascii=False)
        print('%-20s %-18s %3d rows' % (fn, structs[sname]['table'], len(rows)))
    if skipped:
        print('staff answers kept for C++ (not fixed text or not a simple rule): %d' % len(skipped))
    print('ALL TABLES MATCH THE CONTRACT')


if __name__ == '__main__':
    sys.exit(main())
