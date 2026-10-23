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
import urllib.parse
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UNREAL = os.path.abspath(os.path.join(HERE, '..', '..'))
CONTENT = os.path.join(UNREAL, 'Pipeline', 'content')
LAYOUT = os.path.join(UNREAL, 'Pipeline', 'layout', 'layout.json')
ART_DIR = os.path.join(UNREAL, 'Pipeline', 'out', 'campus', 'art')
SLIDES_DIR = os.path.join(UNREAL, 'Pipeline', 'out', 'slides')
STRUCTS = os.path.join(UNREAL, 'contract', 'structs.json')
OUT = os.path.join(UNREAL, 'WalkTheArchive', 'Data')
EYE_CM = 162.0


def load(name):
    with open(os.path.join(CONTENT, name), encoding='utf-8') as f:
        return json.load(f)


def load_out(name):
    """A file the exporters wrote under Pipeline/out (props_rest.json is committed; the GLBs are not)."""
    with open(os.path.join(UNREAL, 'Pipeline', 'out', name), encoding='utf-8') as f:
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
    """A web-style view {x, z, yaw, pitch} at eye height; 'y' is the floor the visitor stands on (0 unless the
    spot is up on the Reading Room gallery)."""
    if not v:
        return no_view()
    return {'Location': ue_pos(v['x'], float(v.get('y', 0.0)) + EYE_CM / 100.0, v['z']), 'Yaw': ue_yaw(v.get('yaw', 0.0)),
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
DEFAULT_PACK = os.path.join(UNREAL, '..', 'clients', 'xrlibraries')


def pack_dir():
    """The client pack: WTA_CLIENT (build_client.py sets it), else XR Libraries' own, so a plain run of this
    script writes the same tables the pack build does."""
    pack = os.environ.get('WTA_CLIENT') or DEFAULT_PACK
    return pack if os.path.isdir(pack) else ''


def catalogue():
    """The client pack's catalogue (clients/<pack>/catalogue.json): name, a search template with {q}, and records
    (source id -> the library's own record URL). Empty without a pack or the file."""
    pack = pack_dir()
    path = os.path.join(pack, 'catalogue.json') if pack else ''
    if not path or not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        cat = json.load(f)
    assert '{q}' in cat.get('search', '{q}'), 'catalogue.json: search needs a {q} for the words searched'
    return cat


def catalogue_search(cat, title):
    if not cat.get('search') or not title:
        return ''
    return cat['search'].replace('{q}', urllib.parse.quote(title))


def build_sources():
    records = catalogue().get('records') or {}
    rows = []
    for s in load('sources.json'):
        url = records.get(s['id']) or s['url']
        rows.append({'Name': s['id'], 'Label': txt(s['label']), 'Url': txt(url)})
    assert set(records) <= {s['id'] for s in load('sources.json')}, 'catalogue.json: a record names a source that is not in sources.json'
    return rows


def build_galleries():
    return [{'Name': 'G%d' % g['index'], 'Index': g['index'], 'Label': txt(g['label']), 'DisplayName': txt(g['name']),
             'Years': txt(g['years']), 'WallColor': color(g['wall'])} for g in load('galleries.json')]


def build_exhibits(L):
    kinds = {k['id']: k['label'] for k in load('exhibit_kinds.json')}
    lay = {e['id']: e for e in L['exhibits']}
    stages = {s['id']: s for s in L['wax_hall']['stages']}
    rows = []
    # exhibits.json is extracted from the web campus; library_fittings.json is written by hand for the Reading
    # Room's own furniture and fittings, which the web build never had cards for.
    for e in load('exhibits.json') + load('library_fittings.json'):
        le = lay.get(e['id'])
        if le:
            loc = vec(*le['ue_location_cm'])
            yaw = round(le['ue_yaw_deg'], 3)
            # pedestal objects (headset, playbooks) have no artwork size: use the glass case (0.62 x 1.0 m)
            sz = le.get('size_m') or [0.62, 1.0]
            size = {'X': round(100 * sz[0], 2), 'Y': round(100 * sz[1], 2)}
            view = view_from_layout(le['view'])
        elif e.get('lib'):
            # A Reading Room fitting: the 'lib' block gives the object's centre (campus metres), how deep it is
            # from that centre to the face the visitor sees, the pick slab's width and height, and where to stand.
            # The slab goes just in front of that face, turned to meet the visitor, because the hover is a plain
            # Visibility trace and the object's own mesh would catch it first anywhere else.
            lb = e['lib']
            ox, oy, oz = lb['loc']
            sx, sz_ = lb['stand']
            dx, dz = sx - ox, sz_ - oz
            run = math.hypot(dx, dz) or 1.0
            dx, dz = dx / run, dz / run
            off = float(lb.get('depth', 0.5)) + 0.06
            loc = ue_pos(ox + dx * off, oy, oz + dz * off)
            yaw = round(math.degrees(math.atan2(dz, dx)), 3)          # Unreal yaw: the slab's normal points at the visitor
            wh = lb.get('size') or [0.8, 1.0]
            size = {'X': round(100.0 * wh[0], 2), 'Y': round(100.0 * wh[1], 2)}
            view = view_from_web({'x': sx, 'z': sz_, 'y': float(lb.get('stand_y', 0.0)),
                                  'yaw': math.atan2(-(ox - sx), -(oz - sz_)), 'pitch': float(lb.get('pitch', -0.1))})
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
    cat = catalogue()
    label = ('Find it in %s' % cat['name']) if cat.get('name') else 'Find it in the catalogue'
    rows = []
    for b in load('books.json'):
        pages = [{'Heading': txt(p.get('h')), 'Blocks': [book_block(x) for x in p.get('b', [])]} for p in b['pages']]
        url = catalogue_search(cat, b['title'])
        rows.append({'Name': b['id'], 'Subject': b['subject'], 'Title': txt(b['title']), 'Subtitle': txt(b.get('sub')),
                     'Pages': pages, 'Cover': '', 'CatalogueUrl': url, 'CatalogueLabel': label if url else ''})
    return rows


# Rooms the Unreal campus changed from the web build (rooms.json is the web's, extracted from parts/*.js).
UE_ROOM_INFO = {'world': {'k': 'Room 104', 'n': 'XR Classroom', 'y': 'Take a seat: class, quiz, certificate · Layer table at the back'}}


def build_rooms(L):
    lay = {r['id']: r for r in L['rooms']}
    maps = {m['id']: m for m in load('map_rooms.json')}
    galleries = {g['index']: g for g in load('galleries.json')}
    staff = load('staff.json')
    rows = []
    for r in load('rooms.json'):
        lr = lay[r['id']]
        info = UE_ROOM_INFO.get(r['id']) or r.get('info') or {}
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
    # extra_rooms.json is written by hand for the rooms the Blender museum added (the rotunda, the forecourt);
    # their boxes are given in campus metres there.
    for r in load('extra_rooms.json'):
        info = r.get('info') or {}
        mn = ue_pos(r['x0'], r.get('y0', 0.0), r['z0']); mx = ue_pos(r['x1'], r.get('y1', 4.4), r['z1'])
        rows.append({'Name': r['id'], 'Kicker': txt(info.get('k')), 'DisplayName': txt(info.get('n')), 'Sub': txt(info.get('y')),
                     'Wing': r.get('wing') or 'None', 'BoundsMin': vec(mn['X'], mn['Y'], mn['Z']), 'BoundsMax': vec(mx['X'], mx['Y'], mx['Z']),
                     'bOutdoor': bool(r.get('outdoor')), 'StaffId': 'None', 'MapLabel': txt(r.get('label')), 'GoPlace': r.get('goPlace') or 'None'})
    return rows


# The blueprint boards in Room 103 (parts/blueprints.js BP_PLACE: web metres, the wall each hangs on).
BP_PLACE = {'car': (14.45, 6.97, 'n'), 'excavator': (18.1, 6.97, 'n'), 'bridge': (21.75, 6.97, 'n'),
            'house': (12.23, 2.875, 'w'), 'computer': (23.96, 2.875, 'e')}
BP_VIEW_DIST = 2.8   # the web fits the board to the screen between 2.4 and 3.2 m (bpViewFor)


def bp_view(board):
    """The web's bpViewFor(): stand BP_VIEW_DIST in front of the board, facing it, looking slightly up."""
    x, z, wall = BP_PLACE[board]
    if wall == 'n':
        return {'x': x, 'z': z - BP_VIEW_DIST, 'yaw': math.pi, 'pitch': 0.04}
    if wall == 'w':
        return {'x': x + BP_VIEW_DIST, 'z': z, 'yaw': math.pi / 2, 'pitch': 0.04}
    return {'x': x - BP_VIEW_DIST, 'z': z, 'yaw': -math.pi / 2, 'pitch': 0.04}


# How the staff name a place mid-sentence ("Follow me to the Reading Room.") where the web gave no 'say'.
UE_SAY = {'lobby': 'the lobby', 'library': 'the Reading Room', 'desk': 'the reference desk', 'featured': 'the featured books table',
          'freedomBoard': 'the Freedom to Read display', 'window': 'the library window', 'school': 'the Workshop School hall',
          'sculpture': 'the sample sculpture', 'yard': 'the Recess Yard', 'coaster': 'the Comet Coaster', 'drop': 'the Sky Drop',
          'dive': 'the Ocean Dive'}


def place_say(p):
    if p.get('say'):
        return p['say']
    if p['id'].startswith('sec-'):
        return 'the ' + p['label']
    return UE_SAY.get(p['id'], p['label'])


# Places the Unreal campus changed: Room 104 is a classroom you sit in, seen from the back-left corner (between the
# beanbags and the layer table bl/classroom.py's refit moved to the back) over the desks toward the board.
UE_PLACE = {'worldroom': {'label': 'Room 104: XR Classroom',
                          'names': ['xr classroom', 'classroom', 'class', 'room 104', 'intro to vr', 'quiz', 'certificate', 'course',
                                    'world builder studio', 'world builder', 'layer table'],
                          'view': {'x': 26.0, 'z': 0.8, 'yaw': -math.pi / 2 - 0.22, 'pitch': -0.04},
                          'directions': 'Room 104, the XR Classroom: through the doorway on the right side of the lobby and down '
                                        'the school hall. It is the second door on the right.'}}


def build_places(L):
    dirs = {d['placeId']: d['text'] for d in load('staff_answers.json')['directions']}
    stations = {s['id']: s for s in L['stations']}
    stacks = {s['subject']: s for s in L['library']['stacks']}
    rows = []
    for p in load('places.json'):
        if p['id'] in UE_PLACE:
            p = dict(p, **{k: v for k, v in UE_PLACE[p['id']].items() if k not in ('view', 'directions')}, view=UE_PLACE[p['id']]['view'])
        if p['id'] in UE_PLACE:
            v = view_from_web(p['view'])
        elif p['id'] in L['places']:
            v = view_from_layout(L['places'][p['id']])
        elif p.get('view'):
            v = view_from_web(p['view'])
        elif p.get('viewRef', '') and p['viewRef'].startswith('@station:') and p['viewRef'][9:] in stations:
            v = view_from_layout(stations[p['viewRef'][9:]]['view'])
        elif p.get('viewRef', '') and p['viewRef'].startswith('@shelf:') and p['viewRef'][7:] in stacks:
            v = view_from_layout(stacks[p['viewRef'][7:]]['shelf_view'])
        elif p.get('viewRef', '').startswith('@blueprint:') and p['viewRef'][11:] in BP_PLACE:
            v = view_from_web(bp_view(p['viewRef'][11:]))
        else:
            v = no_view()
        say = place_say(p)
        directions = txt(UE_PLACE.get(p['id'], {}).get('directions') or dirs.get(p['id']))
        if directions.startswith(p['label']):
            # the web's directions() opened with the label where it had no 'say' ("The Reading Room, through ...")
            directions = say + directions[len(p['label']):]
        rows.append({'Name': p['id'], 'Label': txt(p['label']), 'Aliases': [txt(n) for n in (p.get('names') or [])],
                     'View': v, 'Directions': directions, 'Say': txt(say)})
    for r in load('extra_rooms.json'):
        p = r.get('place')
        if not p:
            continue
        rows.append({'Name': r['goPlace'], 'Label': txt(p['label']), 'Aliases': [txt(n) for n in (p.get('names') or [])],
                     'View': view_from_web(p['view']), 'Directions': txt(p.get('directions')), 'Say': txt(p.get('say'))})
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


# Staff the Unreal campus moved: Mr. Hale teaches in Room 104, the XR Classroom (bl/classroom.py puts the
# teacher's spot at the board's left, facing the desks); you talk to him from the front row. Campus metres.
UE_STAFF = {'hale': {'pos': (33.0, 0.3), 'yaw_deg': 180.0, 'view': {'x': 32.0, 'z': 0.4, 'yaw': -math.pi / 2, 'pitch': 0.0}}}


def build_staff(L):
    lay = {s['id']: s for s in L['staff']}
    rows = []
    for s in load('staff.json'):
        ls = dict(lay[s['id']])
        if s['id'] in UE_STAFF:
            u = UE_STAFF[s['id']]
            ls['ue_location_cm'] = [u['pos'][0] * 100.0, u['pos'][1] * 100.0, ls['ue_location_cm'][2]]
            ls['ue_yaw_deg'] = u['yaw_deg']
            ls['view'] = {'ue': {'location_cm': [u['view']['x'] * 100.0, u['view']['z'] * 100.0, EYE_CM],
                                 'rotation_deg': {'pitch': round(math.degrees(u['view']['pitch']), 3), 'yaw': ue_yaw(u['view']['yaw']), 'roll': 0.0}}}
        look = s.get('look') or {}
        notes = 'Rocketbox %s; body %s; top %s; bottom %s; skin %s; hair %s %s%s' % (
            look.get('av'), look.get('body'), look.get('top'), look.get('bottom'), look.get('skin'), look.get('hair'),
            look.get('hairStyle'), '; glasses' if look.get('glasses') else '')
        rows.append({'Name': s['id'], 'DisplayName': txt(s['name']), 'Role': txt(s['role']), 'Monogram': txt(s.get('mono')),
                     'Color': color(s.get('color')), 'Rooms': list(s.get('rooms') or []), 'Location': vec(*ls['ue_location_cm']),
                     'Yaw': round(ls['ue_yaw_deg'], 3), 'TalkView': view_from_layout(ls['view']), 'Greeting': txt(s.get('greeting')),
                     'GreetingShort': txt(s.get('greetingShort')), 'Help': txt(s.get('help')), 'Fallback': txt(s.get('fallback')),
                     'Chips': [txt(c if isinstance(c, str) else c.get('q') or c.get('label') or c.get('text')) for c in (s.get('chips') or [])],
                     'RocketboxId': look.get('av') or 'None', 'LookNotes': notes, 'MetaHuman': built_metahuman(s['id'])})
    return rows


def built_metahuman(person):
    """The person's MetaHuman Blueprint class path once wta_people has built it (the .uasset exists), else ''."""
    asset = os.path.join(UNREAL, 'WalkTheArchive', 'Content', 'WTA', 'Characters', person, 'BP_%s.uasset' % person)
    return '/Game/WTA/Characters/%s/BP_%s.BP_%s_C' % (person, person, person) if os.path.isfile(asset) else ''


SIMPLE = re.compile(r"^RX\.(\w+)\.test\(s\)(?:\s*&&\s*words\s*<=\s*(\d+))?(\s*&&\s*!travel)?$")
RULE_ACTIONS = {'paint': ('GoPlace', 'studio'), 'paintBlank': ('GoPlace', 'studio'), 'station:bench': ('OpenStation', 'bench')}
# Web branches the C++ answers itself: the greeting (TryGreeting) and the directions (TryDirections).
CPP_BRANCHES = {1: 'greeting', 31: 'directions'}
# Mirror WantsToGo / AsksWhere in WTADialogueSubsystem.cpp (the web's RX.go / RX.wh plus a few more ways to ask).
UE_GO = r"\b(take|bring|walk|lead) me\b|\bgo to\b|\bshow me the way\b|\bhow do i get to\b|\blets? go\b|\blet's go\b"
UE_WH = r"\bwhere('?s| is| are| can i find| do i find)\b|\bwhich way\b|\bhow do i (get|find)\b|\bdirections?\b"
PLACEHOLDER = re.compile(r'\{(\w+)(?::([\w-]+))?\}')
STAFF_KEYS = ('name', 'role', 'help')
ACTION_TABLES = {'GoPlace': 'FWTAPlaceRow', 'OpenItem': 'FWTAExhibitRow', 'OpenBook': 'FWTABookRow',
                 'OpenStation': 'FWTAStationRow', 'OpenRide': 'FWTARideRow', 'StartTour': None, 'OpenBadges': None,
                 'OpenHunt': None, 'OpenQuiz': 'FWTATalkRow', 'OpenCourse': 'FWTATalkRow', 'StartTalk': 'FWTATalkRow'}


def rule_row(name, order, pattern, answer, max_words=0, staff_only=(), staff_not=(), action='None', arg='None',
             offer=False, offer_label=''):
    return {'Name': name, 'Order': int(order), 'Pattern': pattern, 'MaxWords': int(max_words), 'StaffOnly': list(staff_only),
            'StaffNot': list(staff_not), 'Answer': answer, 'Action': action or 'None', 'ActionArg': arg or 'None',
            'bOffer': bool(offer), 'OfferLabel': offer_label}


def compose(all_, not_):
    """One ICU regex: every pattern of all_ somewhere in the question and none of not_ anywhere."""
    if len(all_) == 1 and not not_:
        return all_[0]
    return '^' + ''.join('(?!.*(?:%s))' % p for p in not_) + ''.join('(?=.*?(?:%s))' % p for p in all_)


def english_list(names):
    return names[0] if len(names) == 1 else ', '.join(names[:-1]) + ' and ' + names[-1]


def year_answer(year, wax, ex):
    """The web's "From <year>, the campus shows ..." line (presetAnswer's year branch), word for word."""
    items = wax or ex
    n = len(items)
    names = ['“' + it['Title'] + (',”' if (i < n - 2 or (i == n - 1 and wax)) else '”')
             for i, it in enumerate(items)]
    joined = ' '.join(names[:-1]) + ' and ' + names[-1] if n > 1 else names[0]
    tail = (' each acted out in the Wax Hall.' if n > 1 else ' acted out in the Wax Hall.') if wax else ' in the museum.'
    return 'From %d, the campus shows %s%s' % (year, joined, tail)


def rule_context(tables, rx):
    """What the placeholders in staff_rules_ue.py can name, from the tables built before the rules."""
    gallery = [e for e in tables['FWTAExhibitRow'] if e['Gallery'] in (1, 2, 3)]
    dated = [e for e in gallery if e['Year']]
    oldest = min(dated, key=lambda e: e['Year'])   # min/max keep the first of equals, like the web's stable sort
    newest = max(dated, key=lambda e: e['Year'])
    when = lambda e: '“%s,” from %d' % (e['Title'], e['Year'])
    coaster = '(?:%s)' % rx['coaster']
    drop = r'(?:%s|\bdrop\b)' % rx['dropq']
    dive = r'(?:%s|\b(?:ocean|fish|reef|turtle|shark)\b)' % rx['diveq']
    return {
        'rx': rx,
        'fact': {f['Name']: f['Body'] for f in tables['FWTAFactRow']},
        'source': {s['Name']: s['Label'] for s in tables['FWTASourceRow']},
        'book': {b['Name']: b['Title'] for b in tables['FWTABookRow']},
        'ride_stats': {r['Name']: r['Stats'] for r in tables['FWTARideRow']},
        'n': {'tokens': len(tables['FWTATokenRow']), 'badges': len(tables['FWTABadgeRow']), 'books': len(tables['FWTABookRow']),
              'gallery_items': len(gallery), 'wax_scenes': len(tables['FWTAWaxSceneRow'])},
        'travel': '(?:%s|%s)' % (UE_GO, UE_WH), 'go': '(?:%s)' % UE_GO,
        'coaster': coaster, 'drop': drop, 'dive': dive, 'anyride': '(?:%s|%s|%s)' % (coaster, drop, dive),
        'subjects': english_list([s['DisplayName'] for s in tables['FWTASubjectRow']]),
        'galleries': english_list([g['DisplayName'] for g in tables['FWTAGalleryRow'] if g['Index'] in (1, 2, 3)]),
        'oldest': when(oldest), 'oldest_id': oldest['Name'], 'newest': when(newest), 'newest_id': newest['Name'],
    }


def fill(text, ctx, staff=None):
    """Replace the placeholders staff_rules_ue.py documents; anything else in braces (a regex {n}) is left alone."""
    def one(m):
        key, arg = m.group(1), m.group(2)
        if key in STAFF_KEYS and arg is None:
            assert staff is not None, '{%s} outside a PerStaff rule' % key
            return staff[key]
        if key not in ctx:
            return m.group(0)
        val = ctx[key]
        if isinstance(val, dict):
            assert arg in val, 'unknown placeholder {%s:%s}' % (key, arg)
            return str(val[arg])
        assert arg is None, 'placeholder {%s} takes no id' % key
        return str(val)
    return PLACEHOLDER.sub(one, text)


# The web's STOP words and the two-letter words it keeps (engine.js toks; WTADialogueSubsystem.cpp StopWords).
STOP = set(('a an the and or but if of to in on at by for with from into onto over under about as is are was were be been being am do '
            'does did doing done have has had having i me my mine you your yours he him his she her hers it its we us our they them '
            'their this that these those there here what which who whom whose when where why how can could would should will shall '
            'may might must not no please tell show give get got find let lets like just some any much many more most very really '
            'also too so than then such thing things something anything stuff kind sort want wanted need know think say said go '
            'going went come came see look looking one ones ok okay hey hi hello whats wheres hows thats im youre theres does dont '
            'can cant').split())
KEEP2 = {'vr', 'ar', 'xr', 'ai', 'mr', '3d', 'it'}
# Title and subtitle words too general to name a topic ("a good book", "a starter guide").
TOPIC_SKIP = {'book', 'books', 'read', 'reading', 'recommend', 'suggest', 'good', 'around', 'first', 'using', 'every', 'others',
              'anyone', 'before', 'keeping', 'finding', 'getting', 'guide', 'starter', 'look', 'open', 'double', 'check', 'stand',
              'place', 'try', 'train', 'make', 'campus'}


def web_toks(text):
    """The web's toks(): lower case, no apostrophes, words of 3+ letters (or vr/ar/xr/ai/mr/3d, or numbers), no STOP words."""
    text = re.sub(r"[\u2019']", '', text.lower())
    return [w for w in re.sub(r'[^a-z0-9\s]', ' ', text).split()
            if w not in STOP and (len(w) > 2 or w in KEEP2 or w.isdigit())]


def same_rx(word):
    """A regex for the question words the web's same() pairs with word: equal, or one a prefix of the other when both have
    at least 4 letters and their lengths differ by at most 3."""
    if len(word) < 4:
        return r'\b%s\b' % re.escape(word)
    alts = [word[:k] for k in range(max(4, len(word) - 3), len(word))] + [re.escape(word) + r'\w{0,3}']
    return r'\b(?:%s)\b' % '|'.join(alts)


def book_topic_rules(r, tables):
    """The web's recommend(): a book whose title, subtitle or section the question names; the first on the shelves wins."""
    subjects = {s['Name']: s['DisplayName'] for s in tables['FWTASubjectRow']}
    for i, b in enumerate(tables['FWTABookRow'], 1):
        words = [w for w in dict.fromkeys(web_toks(b['Title'] + ' ' + b['Subtitle'])) if w not in TOPIC_SKIP]
        section = subjects[b['Subject']]
        assert re.match(r'^[a-z0-9 ]+$', section.lower()), 'section name %r needs escaping' % section
        topic = '|'.join([same_rx(w) for w in words] + [r'\b%s\b' % section.lower()])
        title = b['Title']
        yield dict(r, Name='%s-%02d-%s' % (r['Name'], i, b['Name']),
                   Answer='Try \u201c%s%s\u201d in the library\u2019s %s section.' % (title, '' if title[-1] in '?!' else ',', section),
                   All=[r['All'][0], topic], Action='OpenBook', ActionArg=b['Name'], bOffer=True,
                   OfferLabel='Open \u201c%s\u201d' % title)


def year_rules(r, exhibits):
    """One rule per year of the wax scenes and dated gallery exhibits (the web's year branch, 2010 to 2029)."""
    wax_items = [e for e in exhibits if e['bWax']]
    gallery = [e for e in exhibits if e['Gallery'] in (1, 2, 3) and e['Year']]
    for y in sorted({e['Year'] for e in wax_items + gallery if 2010 <= e['Year'] <= 2029}):
        wax = [e for e in wax_items if str(y) in str(e['Year'])]
        ex = [e for e in gallery if e['Year'] == y]
        items = wax or ex
        yield dict(r, Name='%s-%d' % (r['Name'], y), Answer=year_answer(y, wax, ex),
                   All=[r'\b%d\b' % y, r'\bhappen|\bwhat\b|\b(in|during) %d\b' % y], Not=['{travel}', '{anyride}'],
                   Action='OpenItem', ActionArg=items[0]['Name'], bOffer=True,
                   OfferLabel='Show me the scene' if wax else 'Show me the exhibit')


def make_rule(r, ctx, staff=None):
    f = lambda s: fill(s, ctx, staff)
    return rule_row(r['Name'], r['Order'], compose([f(p) for p in r['All']], [f(p) for p in r.get('Not') or []]),
                    f(r['Answer']), r.get('MaxWords', 0), r.get('StaffOnly') or [], r.get('StaffNot') or [],
                    f(r.get('Action', 'None')), f(r.get('ActionArg', 'None')), r.get('bOffer', False), f(r.get('OfferLabel', '')))


def ue_rules(tables, rx):
    """staff_rules_ue.RULES as DT_StaffRules rows, and the web branches they stand for."""
    sys.path.insert(0, HERE)
    import staff_rules_ue
    ctx = rule_context(tables, rx)
    staff = [{'id': s['Name'], 'name': s['DisplayName'], 'role': s['Role'].lower(), 'help': s['Help']}
             for s in tables['FWTAStaffRow']]
    rows, webs = [], set()
    for r in staff_rules_ue.RULES:
        if r.get('Web') is not None:
            webs.add(int(r['Web']))
        if r.get('Generate') == 'years':
            rows.extend(make_rule(spec, ctx) for spec in year_rules(r, tables['FWTAExhibitRow']))
        elif r.get('Generate') == 'book_topics':
            rows.extend(make_rule(spec, ctx) for spec in book_topic_rules(r, tables))
        elif r.get('PerStaff'):
            for s in staff:
                if s['id'] not in (r.get('StaffNot') or []):
                    rows.append(make_rule(dict(r, Name='%s-%s' % (r['Name'], s['id']), StaffOnly=[s['id']], StaffNot=[]), ctx, s))
        else:
            rows.append(make_rule(r, ctx))
    return rows, webs


def check_rules(rows, tables):
    """Every pattern compiles, every placeholder is filled, every action names a real row."""
    staff = {s['Name'] for s in tables['FWTAStaffRow']}
    leftover = re.compile(r'\{(?:%s)(?::[\w-]+)?\}' % '|'.join(['rx', 'fact', 'source', 'book', 'n', 'ride_stats', 'travel', 'go',
                                                              'coaster', 'drop', 'dive', 'anyride', 'subjects', 'galleries',
                                                              'oldest', 'newest', 'oldest_id', 'newest_id'] + list(STAFF_KEYS)))
    for r in rows:
        where = 'StaffRules[%s]' % r['Name']
        try:
            re.compile(r['Pattern'], re.IGNORECASE)
        except re.error as exc:
            raise AssertionError('%s: bad regex (%s)' % (where, exc))
        left = leftover.search(' '.join([r['Pattern'], r['Answer'], r['ActionArg'], r['OfferLabel']]))
        assert not left, '%s: unfilled placeholder %s' % (where, left.group(0))
        assert r['Answer'], '%s: no answer' % where
        assert set(r['StaffOnly']) | set(r['StaffNot']) <= staff, '%s: unknown staff id' % where
        if r['Action'] != 'None':
            assert r['Action'] in ACTION_TABLES, '%s: unknown action %s' % (where, r['Action'])
            table = ACTION_TABLES[r['Action']]
            if table:
                assert r['ActionArg'].split('#')[0] in {x['Name'] for x in tables[table]}, \
                    '%s: %s has no row %s' % (where, table, r['ActionArg'])
        assert not r['bOffer'] or r['Action'] != 'None', '%s: offers no action' % where


def build_staff_rules(tables):
    """DT_StaffRules: the web's simple fixed-text branches, then staff_rules_ue.py (which replaces rows of the same Name).
    Returns (rows, names replaced by staff_rules_ue.py, web branch orders with no rule)."""
    sa = load('staff_answers.json')
    rx = {r['id']: r['pattern'] for r in sa['rules']}
    rows, covered = [], set()
    for b in sa['presetBranches']:
        m = SIMPLE.match((b.get('conditionSrc') or '').strip())
        if not b.get('staticText') or not (m and m.group(1) in rx):
            continue
        pattern = rx[m.group(1)]
        if m.group(3):
            # "&& !travel": not when the player asks the way or to be taken there (the directions answer that)
            pattern = compose([pattern], ['(?:%s|%s)' % (UE_GO, UE_WH)])
        act, arg = RULE_ACTIONS.get(b.get('action') or '', ('', 'None'))
        rows.append(rule_row('R%03d' % b['order'], b['order'], pattern, txt(b['staticText']), int(m.group(2) or 0),
                             b.get('staffOnly') or [], b.get('staffNot') or [], act, arg))
        covered.add(int(b['order']))
    ue, ue_webs = ue_rules(tables, rx)
    by_name = {r['Name']: r for r in rows}
    replaced = sorted(set(by_name) & {r['Name'] for r in ue})
    by_name.update((r['Name'], r) for r in ue)
    out = sorted(by_name.values(), key=lambda r: (r['Order'], r['Name']))
    check_rules(out, tables)
    branches = {int(b['order']) for b in sa['presetBranches']}
    return out, replaced, sorted(branches - covered - ue_webs - set(CPP_BRANCHES))


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


def wax_figure(scene_id, c):
    """Web cast member -> FWTAWaxFigure. The web places it at at=[x, z] metres in the stage group's frame (+z toward
    the walkway) turned ry degrees about +Y; in the stage frame of the contract that is X = z, Y = -x (cm), Yaw = -ry."""
    at = c.get('at') or [0.0, 0.0]
    return {'Person': '%s-%s' % (scene_id, c['var']), 'Offset': vec(100.0 * float(at[1]), -100.0 * float(at[0]), 0.0),
            'Yaw': round(-float(c.get('ry') or 0.0), 3)}


def wax_beat(b):
    """One acting beat of wax_acting.json -> FWTAWaxBeat."""
    return {'Time': float(b['t']), 'Action': b['a'], 'Yaw': float(b.get('y') or 0.0), 'Rate': float(b.get('r') or 1.0),
            'Blend': float(b.get('b') or 0.35), 'Lift': float(b.get('l') or 0.0)}


def wax_prop(scene_id, p):
    """One prop of wax_acting.json -> FWTAWaxProp. A key's figure is the scene's short name ("teen")."""
    keys = []
    for k in p.get('keys', []):
        who = k.get('f') or ''
        keys.append({'Time': float(k['t']), 'Figure': ('%s-%s' % (scene_id, who)) if who else '',
                     'Socket': k.get('s') or '', 'Offset': vec(*(k.get('o') or [0.0, 0.0, 0.0])),
                     'Rotation': {'Pitch': float((k.get('r') or [0, 0, 0])[0]), 'Yaw': float((k.get('r') or [0, 0, 0])[1]),
                                  'Roll': float((k.get('r') or [0, 0, 0])[2])},
                     'Blend': float(k.get('b') or 0.5)})
    return {'Id': p['id'], 'Kind': p['kind'], 'WebIndex': int(p.get('web', -1)), 'Keys': keys}


def ue_rotator_from_web_quat(q):
    """A three.js quaternion (x, y, z, w) in the web stage frame -> the UE rotator (Pitch, Yaw, Roll) in the contract's
    stage frame. Axes map X = z, Y = -x, Z = y (the figure mapping); the rotator follows FMatrix::Rotator()."""
    x, y, z, w = q
    # rotation matrix of q (rows), web axes
    R = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    C = [[0, 0, 1], [-1, 0, 0], [0, 1, 0]]      # UE row i = sum_j C[i][j] * web j
    def mul(A, B):
        return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    Ct = [[C[j][i] for j in range(3)] for i in range(3)]
    U = mul(mul(C, R), Ct)                         # the same rotation, UE axes
    # UE: the rotated X axis is column 0, etc. FMatrix::Rotator(): pitch and yaw from the X axis, roll from Y/Z
    import math
    X = [U[0][0], U[1][0], U[2][0]]; Y = [U[0][1], U[1][1], U[2][1]]; Z = [U[0][2], U[1][2], U[2][2]]
    pitch = math.degrees(math.atan2(X[2], math.hypot(X[0], X[1])))
    yaw = math.degrees(math.atan2(X[1], X[0]))
    # the Y axis of a rotator with that pitch and yaw and no roll
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    SY = [-sy, cy, 0.0]
    roll = math.degrees(math.atan2(sum(Z[i] * SY[i] for i in range(3)), sum(Y[i] * SY[i] for i in range(3))))
    return {'Pitch': round(pitch, 3), 'Yaw': round(yaw, 3), 'Roll': round(roll, 3)}


def wax_static_props(scene_id, acting_props, rest):
    """The web carries of a scene that the acting data does not ride: FWTAWaxProps of kind static, standing where
    the web left them at t = 0 (out/campus/props_rest.json, stage-local metres: X = z, Y = -x, Z = y cm)."""
    ridden = {int(p.get('web', -1)) for p in acting_props}
    rows = []
    for r in rest:
        if r['scene'] != scene_id or r['k'] in ridden:
            continue
        x, y, z = r['p']
        rows.append({'Id': 'web%d' % r['k'], 'Kind': 'static', 'WebIndex': int(r['k']),
                     'Keys': [{'Time': 0.0, 'Figure': '', 'Socket': '', 'Offset': vec(100.0 * z, -100.0 * x, 100.0 * y),
                               'Rotation': ue_rotator_from_web_quat(r['q']), 'Blend': 0.5}]})
    return rows


def build_wax(L):
    stages = {s['id']: s for s in L['wax_hall']['stages']}
    # What each reenactor acts out, hand-authored from the web's keyframes (see the file's own note).
    acting = load('wax_acting.json')['scenes']
    try:
        rest = load_out('campus/props_rest.json')['props']
    except (OSError, ValueError, KeyError):
        rest = []
    rows = []
    for w in load('wax_scenes.json'):
        st = stages[w['id']]
        act = acting.get(w['id'], {})
        beats = act.get('figures', {})
        figures = []
        for c in w.get('cast', []):
            figure = wax_figure(w['id'], c)
            figure['Beats'] = [wax_beat(b) for b in beats.get(c['var'], [])]
            figures.append(figure)
        rows.append({'Name': w['id'], 'Number': int(w['n']), 'Year': txt(w['year']), 'Title': txt(w['title']),
                     'LoopSeconds': float(w.get('loopSeconds') or 14), 'Lines': [{'Time': float(l['t']), 'Text': txt(l['text'])} for l in w['lines']],
                     'StageLocation': vec(*st['ue_origin_cm']), 'StageYaw': round(st['ue_yaw_deg'], 3), 'ItemId': w['item']['id'], 'Sequence': '',
                     'Figures': figures,
                     'Props': [wax_prop(w['id'], p) for p in act.get('props', [])] + wax_static_props(w['id'], act.get('props', []), rest)})
    return rows


# Stations the Unreal campus moved: the layer table stands at the back of Room 104 since the classroom refit
# (content/refits.json), seen from its south end, the beanbags behind you.
UE_STATION = {'diorama': {'pos': (25.9, 2.9), 'view': {'x': 25.9, 'z': 0.95, 'yaw': math.pi, 'pitch': -0.3}}}

# The Training Wing's stations come from its own builder's layout (bl/training.py -> out/training/layout.json:
# each station's anchor and view in the campus layout's shape), merged over the campus layout's stations.
TRAINING_LAYOUT = os.path.join(UNREAL, 'Pipeline', 'out', 'training', 'layout.json')


def extra_stations():
    if not os.path.exists(TRAINING_LAYOUT):
        return {}
    with open(TRAINING_LAYOUT, 'r', encoding='utf-8') as fh:
        return {s['id']: s for s in json.load(fh).get('stations', [])}


# The steps a visitor walks through at each station (the panel shows one at a time and reads it aloud; the last
# one finishes the station). The sieve and the titration have their own step titles and a paragraph per step in
# stations.json; the others are given theirs here: the pendulum's from its paragraphs, the model bench's from the
# car kit (bench_kits.json), the layer table's from the nine layers (world_layers.json), the easel's written here.
EASEL_STEPS = [
    ('Pick a brush', 'Seven brushes hang on the easel: neon, paint, ribbon, chrome, rainbow, beads and sparkle. Each leaves a different trail in the air. Start with paint.'),
    ('Paint in the air', 'Hold the trigger and move your hand: the stroke hangs where you drew it. Step round it. A stroke in the air has a front, a back and sides, like a sculpture.'),
    ('Add a shape', 'Stamp a cube, a sphere, a cone, a ring, a star or a heart, and switch on symmetry to mirror every stroke across the easel.'),
    ('Turn the turntable', 'Spin the turntable to see your piece from every side, then save a picture of it. Walk-around art is what XR studios make.'),
]
PENDULUM_STEPS = ['The pendulum', 'The math', 'Set the length and let go', 'Ten swings']


def station_steps(s):
    """(titles, texts) for a station, the same length, from stations.json or the overrides above."""
    paragraphs = [p['text'] for p in (s.get('panelTexts') or []) if p.get('kind') == 'stp']
    titles = s.get('stepTitles') or []
    if titles and len(titles) == len(paragraphs):
        return titles, paragraphs
    if s['id'] == 'pendulum':
        return PENDULUM_STEPS[:len(paragraphs)], paragraphs[:len(PENDULUM_STEPS)]
    if s['id'] == 'bench':
        kits = {k['id']: k for k in load('bench_kits.json')}
        steps = kits['car']['steps']
        return [st['t'] for st in steps], ['%s %s' % (st['d'], st.get('w', '')) for st in steps]
    if s['id'] == 'diorama':
        layers = load('world_layers.json')
        return [l['t'] for l in layers], [l['d'] for l in layers]
    return titles, paragraphs[:len(titles)]


def build_stations(L):
    lay = {s['id']: s for s in L['stations']}
    lay.update(extra_stations())
    rows = []
    for s in load('stations.json'):
        # the web's stations are in layout.json, the training wing's in its builder's layout; UE_STATION moves a few
        ls, card = dict(lay.get(s['id']) or {'ue_location_cm': [0.0, 0.0, 90.0], 'view': {}}), s.get('card') or {}
        assert s['id'] in lay or s['id'] in UE_STATION, 'station %s has no place: not in layout.json, the training layout nor UE_STATION' % s['id']
        if s['id'] in UE_STATION:
            u = UE_STATION[s['id']]
            ls['ue_location_cm'] = [u['pos'][0] * 100.0, u['pos'][1] * 100.0, ls['ue_location_cm'][2]]
            ls['view'] = {'ue': {'location_cm': [u['view']['x'] * 100.0, u['view']['z'] * 100.0, EYE_CM],
                                 'rotation_deg': {'pitch': math.degrees(u['view']['pitch']), 'yaw': ue_yaw(u['view']['yaw']), 'roll': 0.0}}}
        titles, texts = station_steps(s)
        assert len(titles) == len(texts) and titles, 'station %s: %d step titles, %d texts' % (s['id'], len(titles), len(texts))
        rows.append({'Name': s['id'], 'Room': s['room'], 'Kicker': txt(s.get('kick') or card.get('k')), 'Title': txt(card.get('t')),
                     'Subtitle': txt(card.get('m')), 'GoLabel': txt(card.get('go')), 'Steps': [txt(x) for x in titles],
                     'StepTexts': [txt(x.strip()) for x in texts],
                     # the panel's paragraphs, without the live status lines of a running test ("Swinging… The photogate ...")
                     'Panel': [txt(p['text']) for p in (s.get('panelTexts') or [])
                               if p.get('kind') == 'stp' and not re.match('^\\w+…', p['text'])][:6],
                     'bUsesHands': bool(s.get('usesHands')), 'Location': vec(*ls['ue_location_cm']), 'View': view_from_layout(ls['view'])})
    if 'easel' in lay and not any(r['Name'] == 'easel' for r in rows):
        ls = lay['easel']
        rows.append({'Name': 'easel', 'Room': 'studio', 'Kicker': 'Room 101 · 3D Art Studio', 'Title': '3D Art Studio',
                     'Subtitle': 'Paint in the air with brushes, shapes and symmetry', 'GoLabel': 'Start making art',
                     'Steps': [t for t, _ in EASEL_STEPS], 'StepTexts': [d for _, d in EASEL_STEPS],
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
        # The web's note ends with how to look around while riding ("Drag to look around ..."); riding is not in this build.
        note = re.sub(r'\s*Drag to look around[^.]*\.', '', txt(ride.get('cardNote'))).strip()
        rows.append({'Name': ride['id'], 'DisplayName': txt(ride['name']), 'Kicker': txt(ride.get('kick')), 'CardText': txt(ride.get('cardText')),
                     'CardNote': note, 'About': txt(ride.get('staffAbout')), 'Stats': txt(ride.get('staffStats')),
                     'Safety': txt(ride.get('staffSafety')), 'BadgeId': ride.get('badge') or 'None', 'Location': vec(f[0], f[1], f[2] + 120.0),
                     'ExitView': view_from_web(ride.get('exitView'))})
    return rows


# ---------- talks and classes (content/talks.json, or the client pack's own) ----------
def talks_source():
    pack = pack_dir()
    if pack and os.path.exists(os.path.join(pack, 'talks.json')):
        return os.path.join(pack, 'talks.json')
    return os.path.join(CONTENT, 'talks.json')


def slide_ref(talk_id, n):
    """/Game/WTA/Slides/T_Slide_<talk>_<nn> when bl/slides.py drew that slide (import_art imports them)."""
    name = 'T_Slide_%s_%02d' % (talk_id.replace('-', '_'), n)
    if os.path.exists(os.path.join(SLIDES_DIR, talk_id, '%02d.png' % n)):
        return '/Game/WTA/Slides/%s.%s' % (name, name)
    return ''


def build_talks():
    with open(talks_source(), encoding='utf-8') as f:
        talks = json.load(f)['talks']
    rows = []
    for t in talks:
        assert t['venue'] in ('forecourt', 'auditorium', 'classroom', 'training') or t['venue'].isidentifier(), t['venue']
        assert t.get('kind', 'talk') in ('talk', 'class', 'course'), t['id']
        sp = t.get('speaker') or {}
        slides = []
        for i, sl in enumerate(t['slides']):
            words = len(sl['say'].split())
            slides.append({'Title': txt(sl['title']), 'Points': [txt(x) for x in sl.get('points') or []], 'Say': txt(sl['say']),
                           'Slide': slide_ref(t['id'], i + 1), 'Clip': '%s-%02d' % (t['id'], i + 1),
                           # without a voice clip a slide stays up as long as reading it aloud would take
                           'Seconds': round(max(4.0, words / 2.6 + 1.0), 1)})
        quiz = t.get('quiz') or {}
        qs = []
        for i, q in enumerate(quiz.get('questions') or []):
            assert 0 <= int(q['answer']) < len(q['options']), '%s quiz %d: answer out of range' % (t['id'], i + 1)
            qs.append({'Question': txt(q['q']), 'Options': [txt(o) for o in q['options']], 'Answer': int(q['answer']),
                       'Why': txt(q.get('why')), 'Clip': '%s-%02d' % (t['id'], i + 1)})
        assert (t.get('kind') in ('class', 'course')) == bool(qs), '%s: a class or course has a quiz and a talk has none' % t['id']
        assert (t.get('kind') == 'course') == bool(t.get('stations')), '%s: a course has stations and nothing else does' % t['id']
        assert t.get('kind') != 'course' or not slides, '%s: a course has no slides' % t['id']
        c = t.get('certificate') or {}
        rows.append({'Name': t['id'], 'Venue': t['venue'], 'Kind': t.get('kind', 'talk'), 'Title': txt(t['title']),
                     'Subtitle': txt(t.get('subtitle')), 'Speaker': txt(sp.get('name')), 'SpeakerShort': txt(sp.get('short') or sp.get('name')),
                     'SpeakerRole': txt(sp.get('role')), 'Person': sp.get('person') or 'None', 'Staff': sp.get('staff') or 'None',
                     'Slides': slides, 'Quiz': qs, 'PassCount': int(quiz.get('pass', len(qs))),
                     'Certificate': {'Title': txt(c.get('title')), 'Line': txt(c.get('line')), 'Place': txt(c.get('place')),
                                     'Signer': txt(c.get('signer')), 'SignerRole': txt(c.get('signer_role')), 'Org': txt(c.get('org')),
                                     'Note': txt(c.get('note'))},
                     'BadgeId': t.get('badge') or 'None', 'Stations': list(t.get('stations') or []), 'Intro': txt(t.get('intro'))})
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
    elif typ == 'Rotator':
        assert isinstance(v, dict) and set(v) == {'Pitch', 'Yaw', 'Roll'}, '%s: bad Rotator %r' % (where, v)
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


# ---------- the pack's language (content/lang/<lang>/: strings.json for the engine's own words, tables.json for
# the content's) ----------
LANG_DIR = os.path.join(CONTENT, 'lang')


def language():
    """WTA_LANG (build_client.py sets it from the pack's campus.json "language"), else the pack's, else English."""
    lang = os.environ.get('WTA_LANG')
    if not lang and pack_dir():
        try:
            with open(os.path.join(pack_dir(), 'campus.json'), encoding='utf-8') as f:
                lang = json.load(f).get('language')
        except (OSError, ValueError):
            lang = ''
    lang = (lang or 'en').strip().lower()
    if lang != 'en':
        assert os.path.isdir(os.path.join(LANG_DIR, lang)), 'no content/lang/%s folder' % lang
    return lang


def lang_file(lang, name):
    path = os.path.join(LANG_DIR, lang, name)
    if lang == 'en' or not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def build_strings(lang):
    """DT_Strings: the engine's words (extract_strings.py lists the keys) in the pack's language; empty in English."""
    words = lang_file(lang, 'strings.json') or {}
    rows = [(k, v) for k, v in words.items() if str(v).strip() and v != k]
    # The row name cannot be the English (the importer drops spaces, commas and quotes from names): Key holds it.
    return [{'Name': 's%04d' % (i + 1), 'Key': k, 'Text': txt(v)} for i, (k, v) in enumerate(rows)]


def merge_lang(target, override, where):
    """The language's words over the English, by shape: dict keys over dict keys, list items by position (an
    override list may be shorter; a list of plain words such as a place's Aliases may be longer, and the extra
    words are added), scalars replaced. Only text should differ, and only fields the contract has."""
    if isinstance(override, dict):
        assert isinstance(target, dict), '%s: a dict over a %s' % (where, type(target).__name__)
        for k, v in override.items():
            assert k in target, '%s: no field %s' % (where, k)
            target[k] = merge_lang(target[k], v, '%s.%s' % (where, k))
        return target
    if isinstance(override, list):
        assert isinstance(target, list), '%s: a list over a %s' % (where, type(target).__name__)
        plain = all(isinstance(v, str) for v in target) and all(isinstance(v, str) for v in override)
        assert plain or len(override) <= len(target), '%s: %d items over %d' % (where, len(override), len(target))
        for i, v in enumerate(override):
            if i >= len(target):
                target.append(v)         # a longer list of plain words (a place's aliases): the extra ones are added
            elif v is not None:
                target[i] = merge_lang(target[i], v, '%s[%d]' % (where, i))
        return target
    assert isinstance(override, str) and isinstance(target, str), '%s: only text is translated' % where
    return override


def apply_language(tables, structs, lang):
    """tables.json: {"<DT table>": {"<row name>": {<fields in the row's shape>}}} merged over the built rows."""
    over = lang_file(lang, 'tables.json') or {}
    by_table = {structs[s]['table']: s for s in structs if structs[s].get('row')}
    count = 0
    for table, rows_over in over.items():
        if table.startswith('_'):
            continue
        assert table in by_table, 'tables.json: no table %s' % table
        rows = {r['Name']: r for r in tables[by_table[table]]}
        for name, fields in rows_over.items():
            assert name in rows, 'tables.json: %s has no row %s' % (table, name)
            merge_lang(rows[name], fields, '%s[%s]' % (table, name))
            count += 1
    return count


def main():
    with open(STRUCTS, encoding='utf-8') as f:
        structs = json.load(f)['structs']
    lang = language()
    with open(LAYOUT, encoding='utf-8') as f:
        L = json.load(f)
    tables = {
        'FWTASourceRow': build_sources(), 'FWTAGalleryRow': build_galleries(), 'FWTAExhibitRow': build_exhibits(L),
        'FWTASubjectRow': build_subjects(L), 'FWTABookRow': build_books(), 'FWTARoomRow': build_rooms(L),
        'FWTAPlaceRow': build_places(L), 'FWTATourStopRow': build_tour(L), 'FWTAStaffRow': build_staff(L),
        'FWTAStaffRuleRow': None, 'FWTAFactRow': build_facts(), 'FWTALessonRow': build_lessons(),
        'FWTABadgeRow': build_badges(), 'FWTATokenRow': build_tokens(L), 'FWTAWaxSceneRow': build_wax(L),
        'FWTAStationRow': build_stations(L), 'FWTARideRow': build_rides(L), 'FWTATalkRow': build_talks(),
    }
    # The staff rules come last: their placeholders read the other tables.
    tables['FWTAStaffRuleRow'], replaced, unruled = build_staff_rules(tables)
    tables['FWTAStringRow'] = build_strings(lang)
    translated = apply_language(tables, structs, lang)
    if lang != 'en':
        print('language %s: %d of the engine\'s words, %d rows with their words' % (lang, len(tables['FWTAStringRow']), translated))
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
    print('staff rules: %d; staff_rules_ue.py rewrites %s for this build' % (len(tables['FWTAStaffRuleRow']), ', '.join(replaced)))
    if unruled:
        print('web staff branches with no rule (the search answers them): %s' % ', '.join(map(str, unruled)))
    print('ALL TABLES MATCH THE CONTRACT')


if __name__ == '__main__':
    sys.exit(main())
