"""The visit report: a folder of the engine's visit logs (Saved/Visits/visit_*.csv, one per play session) into one
page a library can put in a grant report - how many visits, how long, where the time went room by room, which
cards were opened most, the tokens and badges, and a heatmap of where visitors stood drawn over the campus plan.

    python3 unreal/Tools/common/visit_report.py [--visits <folder>] [--rooms <Rooms.json>] [--out report.html]
                                                [--since 2026-10-01] [--until 2026-10-31] [--title "..."]

Defaults: --visits unreal/WalkTheArchive/Saved/Visits, --rooms unreal/WalkTheArchive/Data/Rooms.json,
--out <visits>/visit_report.html. No names are in the logs and none are in the report: sessions, not people.
The page is self-contained (the heatmap is inline SVG), so it mails or prints as it is.
"""
import argparse
import csv
import datetime as dt
import html
import json
import math
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
DEFAULT_VISITS = os.path.join(ROOT, 'unreal', 'WalkTheArchive', 'Saved', 'Visits')
DEFAULT_ROOMS = os.path.join(ROOT, 'unreal', 'WalkTheArchive', 'Data', 'Rooms.json')

CARD_KINDS = {'exhibit': 'Exhibit', 'book': 'Book', 'station': 'Station', 'ride': 'Ride', 'quiz': 'Quiz',
              'course': 'Course', 'badges': 'Badges', 'places': 'Places', 'hunt': 'Library card', 'chat': 'Staff chat'}


def utc_date(seconds):
    return dt.datetime.fromtimestamp(seconds, dt.timezone.utc).date()


def utc_text(seconds, fmt='%d %B %Y'):
    return dt.datetime.fromtimestamp(seconds, dt.timezone.utc).strftime(fmt)


def read_sessions(folder, since=None, until=None):
    """Every visit_*.csv as a session dict: file, start, end, rooms [(id, entered, seconds)], cards, tokens, badges, pos."""
    sessions = []
    for name in sorted(os.listdir(folder)):
        if not (name.startswith('visit_') and name.endswith('.csv')):
            continue
        path = os.path.join(folder, name)
        s = {'file': name, 'start': None, 'end': None, 'rooms': [], 'enters': [], 'cards': [], 'tokens': [], 'badges': [], 'pos': []}
        with open(path, 'r', encoding='utf-8', newline='') as fh:
            for row in csv.DictReader(fh):
                try:
                    t = float(row.get('utc') or 0)
                except ValueError:
                    continue
                kind, a, b, c = row.get('kind', ''), row.get('a', ''), row.get('b', ''), row.get('c', '')
                s['start'] = t if s['start'] is None else min(s['start'], t)
                s['end'] = t if s['end'] is None else max(s['end'], t)
                if kind == 'room' and a:
                    try:
                        s['rooms'].append((a, float(b), float(c)))
                    except ValueError:
                        pass
                elif kind == 'card' and a:
                    s['cards'].append((a, b))
                elif kind == 'token' and a:
                    s['tokens'].append(a)
                elif kind == 'badge' and a:
                    s['badges'].append(a)
                elif kind == 'enter' and a:
                    s['enters'].append((a, t))
                elif kind == 'pos':
                    try:
                        s['pos'].append((a, float(b), float(c)))
                    except ValueError:
                        pass
        if s['start'] is None:
            continue
        # A session that ended without closing its last room (the game was killed, or crashed): the time from
        # the last entry to the last line counts for that room, so a report never loses a visit's tail.
        closed_until = max((entered + seconds for _r, entered, seconds in s['rooms']), default=s['start'])
        if s['enters']:
            room, entered = s['enters'][-1]
            if entered >= closed_until - 1 and s['end'] > entered:
                s['rooms'].append((room, entered, s['end'] - entered))
        day = utc_date(s['start'])
        if since and day < since:
            continue
        if until and day > until:
            continue
        sessions.append(s)
    return sessions


def load_rooms(path):
    if not path or not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as fh:
        rows = json.load(fh)
    rooms = []
    for r in rows:
        mn, mx = r.get('BoundsMin', {}), r.get('BoundsMax', {})
        rooms.append({'id': r['Name'], 'name': r.get('DisplayName') or r['Name'], 'outdoor': bool(r.get('bOutdoor')),
                      'x0': mn.get('X', 0) / 100.0, 'y0': mn.get('Y', 0) / 100.0, 'x1': mx.get('X', 0) / 100.0, 'y1': mx.get('Y', 0) / 100.0})
    return rooms


def fmt_minutes(seconds):
    m = seconds / 60.0
    if m < 1:
        return '%d s' % round(seconds)
    if m < 60:
        return '%.1f min' % m
    return '%d h %02d min' % (int(m // 60), int(m % 60))


def heat_colour(t):
    """0..1 -> cream to brass to deep red, the card's own colours."""
    stops = [(0.0, (242, 233, 215)), (0.35, (205, 169, 97)), (0.7, (176, 88, 46)), (1.0, (92, 24, 24))]
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            k = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            return '#%02x%02x%02x' % tuple(int(round(c0[i] + (c1[i] - c0[i]) * k)) for i in range(3))
    return '#%02x%02x%02x' % stops[-1][1]


def heatmap_svg(sessions, rooms, cell=1.0, width=900):
    """Position samples binned on a cell-metre grid over the room boxes, as inline SVG (x east, y south: Unreal's Y down the page)."""
    counts = Counter()
    for s in sessions:
        for _room, x, y in s['pos']:
            counts[(math.floor(x / cell), math.floor(y / cell))] += 1
    if not counts and not rooms:
        return '<p class="muted">No positions logged yet.</p>'
    xs = [r['x0'] for r in rooms] + [r['x1'] for r in rooms] + [k[0] * cell for k in counts]
    ys = [r['y0'] for r in rooms] + [r['y1'] for r in rooms] + [k[1] * cell for k in counts]
    x0, x1 = min(xs) - 2, max(xs) + 2
    y0, y1 = min(ys) - 2, max(ys) + 2
    scale = width / (x1 - x0)
    height = (y1 - y0) * scale
    def X(x): return (x - x0) * scale
    def Y(y): return (y - y0) * scale
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.0f %.0f" width="100%%" role="img" aria-label="Where visitors stood">' % (width, height)]
    out.append('<rect x="0" y="0" width="%.0f" height="%.0f" fill="#f7f2e8"/>' % (width, height))
    for r in rooms:
        fill = '#e9efe0' if r['outdoor'] else '#ffffff'
        out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="#8a6d2f" stroke-width="1"/>' % (
            X(r['x0']), Y(r['y0']), (r['x1'] - r['x0']) * scale, (r['y1'] - r['y0']) * scale, fill))
    top = max(counts.values()) if counts else 1
    for (cx, cy), n in counts.items():
        t = math.log1p(n) / math.log1p(top)
        out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" fill-opacity="0.9"/>' % (
            X(cx * cell), Y(cy * cell), cell * scale, cell * scale, heat_colour(t)))
    for r in rooms:
        w = (r['x1'] - r['x0']) * scale
        if w < 40:
            continue
        size = 11 if w < 120 else 13
        out.append('<text x="%.1f" y="%.1f" font-family="Georgia, serif" font-size="%d" fill="#2b2419" text-anchor="middle">%s</text>' % (
            X((r['x0'] + r['x1']) / 2), Y(r['y0']) + size + 4, size, html.escape(r['name'])))
    out.append('</svg>')
    legend = ('<div class="legend"><span>quiet</span><i style="background:linear-gradient(90deg,%s,%s,%s,%s)"></i><span>busy</span>'
              '<span class="muted">&nbsp;·&nbsp; %d m cells, %d samples</span></div>' % (
                  heat_colour(0), heat_colour(0.35), heat_colour(0.7), heat_colour(1.0), cell, sum(counts.values())))
    return '\n'.join(out) + legend


def build_report(sessions, rooms, title):
    room_names = {r['id']: r['name'] for r in rooms}
    dwell = defaultdict(float)
    visits_per_room = Counter()
    for s in sessions:
        seen = set()
        for room, _entered, seconds in s['rooms']:
            dwell[room] += seconds
            if room not in seen:
                visits_per_room[room] += 1
                seen.add(room)
    total_seconds = sum((s['end'] - s['start']) for s in sessions)
    days = Counter(utc_date(s['start']) for s in sessions)
    cards = Counter((k, i) for s in sessions for k, i in s['cards'] if k not in ('badges', 'places'))
    tokens = Counter(t for s in sessions for t in s['tokens'])
    badges = Counter(b for s in sessions for b in s['badges'])
    first = min((s['start'] for s in sessions), default=None)
    last = max((s['end'] for s in sessions), default=None)
    span = ''
    if first is not None:
        span = '%s to %s' % (utc_text(first), utc_text(last))

    def tile(label, value, note=''):
        return '<div class="tile"><div class="label">%s</div><div class="value">%s</div><div class="note">%s</div></div>' % (
            html.escape(label), html.escape(str(value)), html.escape(note))

    tiles = ''.join([
        tile('Visits', len(sessions), 'play sessions logged'),
        tile('Days with visits', len(days), span),
        tile('Time on the campus', fmt_minutes(total_seconds), 'all visits together'),
        tile('A visit lasts', fmt_minutes(total_seconds / len(sessions)) if sessions else '-', 'on average'),
        tile('Cards opened', sum(cards.values()), 'exhibits, books, stations, rides, chats'),
        tile('Tokens found', sum(tokens.values()), '%d badges earned' % sum(badges.values())),
    ])

    room_rows = []
    total_dwell = sum(dwell.values()) or 1.0
    for room, seconds in sorted(dwell.items(), key=lambda kv: -kv[1]):
        share = 100.0 * seconds / total_dwell
        room_rows.append('<tr><td>%s</td><td class="num">%s</td><td class="num">%d</td><td class="num">%.0f%%</td>'
                         '<td><div class="bar"><i style="width:%.1f%%"></i></div></td></tr>' % (
                             html.escape(room_names.get(room, room)), fmt_minutes(seconds), visits_per_room[room], share, share))
    card_rows = []
    for (kind, ident), n in cards.most_common(20):
        card_rows.append('<tr><td>%s</td><td>%s</td><td class="num">%d</td></tr>' % (
            html.escape(CARD_KINDS.get(kind, kind)), html.escape(ident or '-'), n))
    token_rows = ''.join('<li>%s <span class="muted">× %d</span></li>' % (html.escape(t), n) for t, n in tokens.most_common())
    badge_rows = ''.join('<li>%s <span class="muted">× %d</span></li>' % (html.escape(b), n) for b, n in badges.most_common())

    return '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<style>
  :root { --bg:#f7f2e8; --card:#fffdf8; --ink:#2b2419; --dim:#6f655a; --brass:#8a6d2f; --rule:#e2d8c4; }
  body { margin:0; background:var(--bg); color:var(--ink); font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height:1.45; }
  main { max-width: 980px; margin: 0 auto; padding: 32px 20px 60px; }
  h1 { font-family: Georgia, "Times New Roman", serif; font-weight: 600; font-size: 34px; margin: 0 0 4px; }
  h2 { font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: var(--brass); border-bottom: 1px solid var(--rule); padding-bottom: 6px; margin: 34px 0 12px; }
  .kicker { font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: var(--brass); }
  .muted { color: var(--dim); }
  .tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-top: 18px; }
  .tile { background: var(--card); border: 1px solid var(--rule); border-radius: 10px; padding: 14px 16px; }
  .tile .label { font-size: 12px; color: var(--dim); } .tile .value { font-size: 26px; font-weight: 600; margin: 2px 0; } .tile .note { font-size: 12px; color: var(--dim); }
  table { width: 100%%; border-collapse: collapse; background: var(--card); border: 1px solid var(--rule); border-radius: 10px; overflow: hidden; }
  th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--rule); font-size: 14px; } th { font-size: 12px; color: var(--dim); font-weight: 600; }
  tr:last-child td { border-bottom: 0; } td.num, th.num { text-align: right; white-space: nowrap; }
  .bar { height: 8px; background: #efe7d6; border-radius: 4px; min-width: 120px; } .bar i { display: block; height: 100%%; background: #cda961; border-radius: 4px; }
  .cols { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; } @media (max-width: 640px) { .cols { grid-template-columns: 1fr; } }
  ul { margin: 0; padding-left: 18px; } li { font-size: 14px; }
  .map { background: var(--card); border: 1px solid var(--rule); border-radius: 10px; padding: 12px; }
  .legend { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--dim); margin-top: 8px; } .legend i { display: inline-block; width: 120px; height: 10px; border-radius: 5px; }
  footer { margin-top: 40px; font-size: 12px; color: var(--dim); }
</style></head>
<body><main>
  <div class="kicker">Walk the Archive · visit report</div>
  <h1>%(title)s</h1>
  <div class="muted">%(span)s · made %(made)s</div>
  <div class="tiles">%(tiles)s</div>
  <h2>Where the time went</h2>
  <table><thead><tr><th>Room</th><th class="num">Time</th><th class="num">Visits</th><th class="num">Share</th><th></th></tr></thead><tbody>%(room_rows)s</tbody></table>
  <h2>Where visitors stood</h2>
  <div class="map">%(heatmap)s</div>
  <h2>What was opened most</h2>
  <table><thead><tr><th>Kind</th><th>Card</th><th class="num">Opened</th></tr></thead><tbody>%(card_rows)s</tbody></table>
  <div class="cols">
    <div><h2>Tokens found</h2><ul>%(token_rows)s</ul></div>
    <div><h2>Badges earned</h2><ul>%(badge_rows)s</ul></div>
  </div>
  <footer>From the campus's own visit logs (one per play session, no names kept). Times are session clocks; a room's time is the time spent inside it.</footer>
</main></body></html>
''' % {'title': html.escape(title), 'span': html.escape(span or 'no visits yet'), 'made': dt.date.today().strftime('%d %B %Y'),
       'tiles': tiles, 'room_rows': ''.join(room_rows) or '<tr><td colspan="5" class="muted">no rooms logged yet</td></tr>',
       'heatmap': heatmap_svg(sessions, rooms), 'card_rows': ''.join(card_rows) or '<tr><td colspan="3" class="muted">nothing opened yet</td></tr>',
       'token_rows': token_rows or '<li class="muted">none yet</li>', 'badge_rows': badge_rows or '<li class="muted">none yet</li>'}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--visits', default=DEFAULT_VISITS)
    ap.add_argument('--rooms', default=DEFAULT_ROOMS)
    ap.add_argument('--out', default='')
    ap.add_argument('--since', default='', help='YYYY-MM-DD')
    ap.add_argument('--until', default='', help='YYYY-MM-DD')
    ap.add_argument('--title', default='XR Libraries Campus · visits')
    args = ap.parse_args()
    if not os.path.isdir(args.visits):
        print('no visits folder: %s' % args.visits)
        return 1
    since = dt.date.fromisoformat(args.since) if args.since else None
    until = dt.date.fromisoformat(args.until) if args.until else None
    sessions = read_sessions(args.visits, since, until)
    rooms = load_rooms(args.rooms)
    out = args.out or os.path.join(args.visits, 'visit_report.html')
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write(build_report(sessions, rooms, args.title))
    total = sum((s['end'] - s['start']) for s in sessions)
    print('%d sessions, %s, %d rooms on the plan -> %s' % (len(sessions), fmt_minutes(total), len(rooms), out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
