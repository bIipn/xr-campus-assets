"""The content's words, listed for the translators: every Text field of every DataTable row, in the row's own
shape, as unreal/Pipeline/content/lang/tables.en.json. A language's tables.json (lang/<lang>/tables.json) has
the same shape with the translations; build_data.py merges it over the English rows (WTA_LANG=<lang>), so a
pack in that language ships every card, book, station, talk, place, badge and staff line in it.

    python3 unreal/Tools/common/extract_tables.py [--check lang/es/tables.json] [--only Exhibits,Books]

Shape: {"<DT table>": {"<row name>": {"<Text field>": "...", "<array field>": [{...}, ...]}}}. Arrays keep every
item (null where an item has no text), so positions line up. Empty strings are left out. Staff rules carry their
Pattern (a regex) too, since a language needs its own question patterns; it is the one non-Text field here.
--check lists the rows and fields a language is missing and the ones it has that the tables no longer do.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
STRUCTS = os.path.join(ROOT, 'unreal', 'contract', 'structs.json')
DATA = os.path.join(ROOT, 'unreal', 'WalkTheArchive', 'Data')
OUT = os.path.join(ROOT, 'unreal', 'Pipeline', 'content', 'lang', 'tables.en.json')
ARRAY = re.compile(r'^Array<(.+)>$')
EXTRA_FIELDS = {'FWTAStaffRuleRow': ['Pattern']}    # non-Text fields a language still needs


def text_shape(value, ftype, structs, sname):
    """The translatable part of one field value in its shape, or None."""
    if ftype == 'Text':
        return value if isinstance(value, str) and value.strip() else None
    m = ARRAY.match(ftype)
    if m:
        inner = m.group(1)
        items = [text_shape(v, inner, structs, sname) for v in (value or [])]
        return items if any(i is not None for i in items) else None
    if ftype in structs:
        return row_shape(value, ftype, structs)
    return None


def row_shape(row, sname, structs):
    out = {}
    for fname, ftype in structs[sname]['fields']:
        if fname in EXTRA_FIELDS.get(sname, []):
            if row.get(fname):
                out[fname] = row[fname]
            continue
        shaped = text_shape(row.get(fname), ftype, structs, sname)
        if shaped is not None:
            out[fname] = shaped
    return out or None


def extract(only):
    with open(STRUCTS, encoding='utf-8') as fh:
        structs = json.load(fh)['structs']
    tables = {}
    for sname, spec in structs.items():
        if not spec.get('row') or spec['table'] == 'DT_Strings':
            continue
        if only and spec['table'] not in only and spec['table'].replace('DT_', '') not in only:
            continue
        path = os.path.join(DATA, spec['file'])
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as fh:
            rows = json.load(fh)
        shaped = {}
        for row in rows:
            r = row_shape(row, sname, structs)
            if r:
                shaped[row['Name']] = r
        if shaped:
            tables[spec['table']] = shaped
    return tables


def walk(value, path, out):
    if isinstance(value, dict):
        for k, v in value.items():
            walk(v, path + [k], out)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            walk(v, path + [i], out)
    elif isinstance(value, str) and value.strip():
        out['.'.join(map(str, path))] = value


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', default='')
    ap.add_argument('--only', default='', help='table names, comma separated (Exhibits,Books)')
    args = ap.parse_args()
    only = set(x.strip() for x in args.only.split(',') if x.strip())
    tables = extract(only)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as fh:
        json.dump(tables, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    flat = {}
    walk(tables, [], flat)
    words = sum(len(v.split()) for v in flat.values())
    print('%d tables, %d rows, %d strings, about %d words -> %s' % (
        len(tables), sum(len(r) for r in tables.values()), len(flat), words, os.path.relpath(OUT, ROOT)))
    for table, rows in tables.items():
        tflat = {}
        walk(rows, [], tflat)
        print('  %-14s %3d rows %5d strings %6d words' % (table, len(rows), len(tflat), sum(len(v.split()) for v in tflat.values())))
    if args.check:
        with open(args.check, encoding='utf-8') as fh:
            lang = json.load(fh)
        lflat = {}
        walk({k: v for k, v in lang.items() if not k.startswith('_')}, [], lflat)
        missing = [k for k in flat if k not in lflat]
        stale = [k for k in lflat if k not in flat]
        same = [k for k in flat if k in lflat and lflat[k] == flat[k] and len(flat[k]) > 3 and not flat[k].startswith('http')]
        for k in missing[:40]:
            print('MISSING: %s' % k)
        for k in stale[:40]:
            print('STALE:   %s' % k)
        print('%d missing, %d stale, %d left in English' % (len(missing), len(stale), len(same)))
        return 1 if missing else 0
    return 0


if __name__ == '__main__':
    sys.exit(main())
