"""Every word the engine writes on its own (WTAText("..."), PanelText("...") in the C++), listed for the
translators as unreal/Pipeline/content/lang/strings.en.json: {"English key": "English key"}. A language's
strings.json (lang/<lang>/strings.json) has the same keys with the translations as values; build_data.py turns it
into DT_Strings (WTA_LANG=<lang>), and UWTAContentSubsystem::Tr shows the translation wherever the C++ wrote
the key. Patterns keep their {0} {1} slots. Run after changing the C++:

    python3 unreal/Tools/common/extract_strings.py [--check lang/es/strings.json]

--check lists the keys a language is missing and the ones it has that the C++ no longer writes.
"""
import argparse
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
SOURCE = os.path.join(ROOT, 'unreal', 'WalkTheArchive', 'Source', 'WalkTheArchive')
OUT = os.path.join(ROOT, 'unreal', 'Pipeline', 'content', 'lang', 'strings.en.json')

CALL = re.compile(r'\b(?:WTAText|PanelText)\s*\(')
LITERAL = re.compile(r'TEXT\("((?:[^"\\]|\\.)*)"\)')
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']


def unescape(text):
    """A C++ literal's escapes as the characters the engine writes."""
    def one(m):
        e = m.group(0)
        if e.startswith('\\u'):
            return chr(int(e[2:], 16))
        return {'\\n': '\n', '\\t': '\t', '\\"': '"', '\\\\': '\\', "\\'": "'"}.get(e, e)
    return re.sub(r'\\u[0-9A-Fa-f]{4}|\\.', one, text)


def call_args(text, start):
    """The text inside the parentheses that open at start (balanced)."""
    depth, i = 0, start
    while i < len(text):
        c = text[i]
        if c == '"':
            i += 1
            while i < len(text) and text[i] != '"':
                i += 2 if text[i] == '\\' else 1
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return text[start + 1:i]
        i += 1
    return text[start + 1:]


def extract():
    keys = {}
    for path in sorted(glob.glob(os.path.join(SOURCE, '**', '*.cpp'), recursive=True) + glob.glob(os.path.join(SOURCE, '**', '*.h'), recursive=True)):
        if 'WTAPlayTest' in path:
            continue
        text = open(path, 'r', encoding='utf-8').read()
        for m in CALL.finditer(text):
            inner = call_args(text, m.end() - 1)
            for lit in LITERAL.finditer(inner):
                key = unescape(lit.group(1))
                if key.strip() and key not in ('%s', '{0}'):
                    keys.setdefault(key, []).append(os.path.relpath(path, SOURCE))
    for month in MONTHS:
        keys.setdefault(month, ['Core/WTAPlayerController.cpp'])
    return keys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', default='', help='a language strings.json to compare with the keys')
    args = ap.parse_args()
    keys = extract()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as fh:
        json.dump({k: k for k in sorted(keys, key=lambda s: s.lower())}, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    print('%d keys -> %s' % (len(keys), os.path.relpath(OUT, ROOT)))
    if args.check:
        with open(args.check, 'r', encoding='utf-8') as fh:
            lang = json.load(fh)
        missing = [k for k in keys if k not in lang or not str(lang[k]).strip()]
        stale = [k for k in lang if k not in keys]
        for k in missing:
            print('MISSING: %r' % k)
        for k in stale:
            print('STALE:   %r' % k)
        print('%d missing, %d stale' % (len(missing), len(stale)))
        return 1 if missing else 0
    return 0


if __name__ == '__main__':
    sys.exit(main())
