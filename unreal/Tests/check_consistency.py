"""
Cross-check the Unreal project's parts against each other, without Unreal.

The C++ headers, the DataTable JSON, the editor-Python setup and the config files were written separately, all
following unreal/contract/. This script finds the mismatches that would only show up on the user's machine:
  1. every row struct in contract/structs.json exists in Public/Data/WTATypes.h with the same fields, order and types
  2. every C++ class the contract names exists (UCLASS/UINTERFACE) in a public header
  3. every property the editor setup sets on a WTA actor exists as a UPROPERTY on that class or its parents
  4. every '/Script/WalkTheArchive.X' path used anywhere names a real class or struct
  5. the [/Script/WalkTheArchive.WTASettings] keys in Config/DefaultGame.ini match UWTASettings' properties
  6. Data/*.json rows still match the contract (re-runs the converter's validation)
Run: python3 unreal/Tests/check_consistency.py   (exit code 1 on any problem)
"""
import glob
import json
import os
import re
import subprocess
import sys

UNREAL = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PROJ = os.path.join(UNREAL, 'WalkTheArchive')
SRC = os.path.join(PROJ, 'Source', 'WalkTheArchive')
problems = []


def bad(msg):
    problems.append(msg)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()


def strip_comments(s):
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    return re.sub(r'//[^\n]*', '', s)


# ---------- C++ model ----------
headers = {p: strip_comments(read(p)) for p in glob.glob(os.path.join(SRC, '**', '*.h'), recursive=True)}
TYPE_DECL = re.compile(r'\b(UCLASS|USTRUCT|UINTERFACE)\s*\((?:[^()]|\((?:[^()]|\([^()]*\))*\))*\)\s*(?:class|struct)\s+(?:WALKTHEARCHIVE_API\s+)?(\w+)\s*(?:final\s*)?(?::\s*public\s+(\w+))?')
types = {}       # name -> (kind, parent, header, body)
for p, s in headers.items():
    for m in TYPE_DECL.finditer(s):
        name, parent = m.group(2), m.group(3)
        start = s.find('{', m.end())
        depth, i = 0, start
        while i < len(s):
            if s[i] == '{':
                depth += 1
            elif s[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        types[name] = (m.group(1), parent, p, s[start:i + 1])

PROP = re.compile(r'UPROPERTY\s*\((?:[^()]|\([^()]*\))*\)\s*([^;{]+?)\s+(\w+)\s*(?:=[^;]*|\{[^;]*\})?;')


def props_of(name):
    out = []
    t = types.get(name)
    while t:
        out = [(m.group(2), ' '.join(m.group(1).split())) for m in PROP.finditer(t[3])] + out
        t = types.get(t[1]) if t[1] else None
    return out


def snake(n):
    if re.match(r'^b[A-Z]', n):
        n = n[1:]
    return re.sub(r'(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', '_', n).lower()


# ---------- 1. structs ----------
structs = json.loads(read(os.path.join(UNREAL, 'contract', 'structs.json')))['structs']
CPP = {'Name': 'FName', 'Text': 'FText', 'String': 'FString', 'Int': 'int32', 'Float': 'float', 'Bool': 'bool', 'Vector': 'FVector',
       'Vector2D': 'FVector2D', 'Color': 'FLinearColor', 'View': 'FWTAView', 'SoftTexture': 'TSoftObjectPtr<UTexture2D>',
       'SoftClass': 'TSoftClassPtr<AActor>', 'SoftObject': 'FSoftObjectPath'}


def cpp_type(t):
    if t.startswith('Array<'):
        return 'TArray<%s>' % cpp_type(t[6:-1])
    return CPP.get(t, t)


if not headers:
    bad('no C++ headers found under %s' % SRC)
for sname, sd in structs.items():
    if sname not in types:
        bad('struct %s missing from C++' % sname)
        continue
    got = [(n, t.replace(' ', '')) for n, t in props_of(sname)]
    want = [(n, cpp_type(t).replace(' ', '')) for n, t in sd['fields']]
    if [n for n, _ in got] != [n for n, _ in want]:
        bad('struct %s fields %s != contract %s' % (sname, [n for n, _ in got], [n for n, _ in want]))
    for (gn, gt), (wn, wt) in zip(got, want):
        if gn == wn and gt != wt:
            bad('struct %s.%s type %s != contract %s' % (sname, gn, gt, wt))
    if sd['row'] and types[sname][1] != 'FTableRowBase':
        bad('row struct %s must derive FTableRowBase (has %s)' % (sname, types[sname][1]))

# ---------- 2. classes ----------
contract = read(os.path.join(UNREAL, 'contract', 'CONTRACT.md'))
wanted = sorted(set(re.findall(r'`([AU]WTA\w+)`', contract)) | {'UWTAInteractable'})
for c in wanted:
    if c not in types:
        bad('class %s (named in CONTRACT.md) missing from C++ headers' % c)

# ---------- 3. Python-set actor properties ----------
ACTOR_PROPS = {
    'AWTAExhibitActor': ['ItemId', 'PickExtent'], 'AWTABookActor': ['BookId', 'PickExtent'], 'AWTAStationActor': ['StationId', 'PickExtent'],
    'AWTARideActor': ['RideId', 'PickExtent'], 'AWTATokenActor': ['TokenId'], 'AWTAStaffNPC': ['StaffId'],
    'AWTARoomVolume': ['RoomId', 'Extent'], 'AWTAWaxStageActor': ['SceneId', 'TriggerExtent'],
}
for cls, ps in ACTOR_PROPS.items():
    have = {n for n, _ in props_of(cls)}
    for p in ps:
        if cls in types and p not in have:
            bad('%s lacks UPROPERTY %s (the editor setup sets %s)' % (cls, p, snake(p)))

py_files = glob.glob(os.path.join(PROJ, 'Content', 'Python', '**', '*.py'), recursive=True) + glob.glob(os.path.join(PROJ, 'Scripts', '*.py'))
py = {p: read(p) for p in py_files}
all_props = {snake(n) for t in types for n, _ in props_of(t)}
wta_snake = {snake(n) for cls in ACTOR_PROPS for n in ACTOR_PROPS[cls]}
for p, s in py.items():
    for m in re.finditer(r"""set_editor_property\(\s*['"](\w+)['"]""", s):
        n = m.group(1)
        if n in wta_snake and n not in all_props:
            bad('%s sets %s, which no C++ UPROPERTY provides' % (os.path.relpath(p, UNREAL), n))

# ---------- 4. /Script paths ----------
texts = dict(py)
for p in glob.glob(os.path.join(PROJ, 'Config', '*.ini')) + [os.path.join(PROJ, 'WalkTheArchive.uproject')]:
    if os.path.exists(p):
        texts[p] = read(p)
for p, s in texts.items():
    for m in re.finditer(r'/Script/WalkTheArchive\.(\w+)', s):
        n = m.group(1)
        if not any(t[1:] == n for t in types):
            bad('%s refers to /Script/WalkTheArchive.%s, which is not a C++ class or struct' % (os.path.relpath(p, UNREAL), n))

# ---------- 5. settings ini ----------
ini = os.path.join(PROJ, 'Config', 'DefaultGame.ini')
if os.path.exists(ini) and 'UWTASettings' in types:
    sec = re.search(r'\[/Script/WalkTheArchive\.WTASettings\](.*?)(?=^\[|\Z)', read(ini), flags=re.S | re.M)
    have = {n for n, _ in props_of('UWTASettings')}
    if not sec:
        bad('DefaultGame.ini has no [/Script/WalkTheArchive.WTASettings] section')
    else:
        for m in re.finditer(r'^\s*(\w+)\s*=', sec.group(1), flags=re.M):
            if m.group(1) not in have:
                bad('DefaultGame.ini WTASettings key %s is not a UWTASettings property' % m.group(1))
# cvars the critic marked unverified/experimental for v1 (docs/reference/critic.md section 2 rows 5-7)
UNVERIFIED_KEYS = ('r.Nanite.AllowTessellation', 'r.Nanite.Tessellation', 'r.MegaLights.Allowed', 'r.MegaLights.Allow',
                   'r.Lumen.TraceMeshSDFs')
for p in glob.glob(os.path.join(PROJ, 'Config', '**', '*.ini'), recursive=True):
    for i, line in enumerate(read(p).splitlines(), 1):
        if re.match(r'^\s*[^;#\[\s][^=]*=.*\s;\s', line):
            bad('%s:%d has a trailing inline comment (Unreal ini has none): %s' % (os.path.relpath(p, UNREAL), i, line.strip()[:80]))
        m = re.match(r'^\s*[+\-.!]?(?:CVars=)?([\w.]+)\s*=', line)
        if m and m.group(1) in UNVERIFIED_KEYS:
            bad('%s:%d sets %s, which is unverified for UE 5.8 v1 (critic.md section 2)' % (os.path.relpath(p, UNREAL), i, m.group(1)))

# ---------- 6. data ----------
r = subprocess.run([sys.executable, os.path.join(UNREAL, 'Pipeline', 'data', 'build_data.py')], capture_output=True, text=True)
if r.returncode != 0 or 'ALL TABLES MATCH THE CONTRACT' not in r.stdout:
    bad('build_data.py failed: ' + (r.stderr or r.stdout)[-400:])

print('C++ types found: %d; Python files: %d' % (len(types), len(py)))
for m in problems:
    print('PROBLEM', m)
print('OK: everything matches' if not problems else '%d problem(s)' % len(problems))
sys.exit(1 if problems else 0)
