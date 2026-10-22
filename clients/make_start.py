#!/usr/bin/env python3
"""Rebuild clients/start.html (the sheet a library fills in to get its client pack) from start.template.html, with the
XR Libraries pack (clients/xrlibraries/campus.json + unreal/Pipeline/content/talks.json) inlined as the example the page
opens on. Run after changing either."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

campus = json.load(open(os.path.join(HERE, 'xrlibraries', 'campus.json'), encoding='utf-8'))
campus['slug'] = 'xrlibraries'
talks = json.load(open(os.path.join(ROOT, 'unreal', 'Pipeline', 'content', 'talks.json'), encoding='utf-8'))
example = json.dumps({'campus': campus, 'talks': talks}, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
template = open(os.path.join(HERE, 'start.template.html'), encoding='utf-8').read()
assert template.count('__EXAMPLE__') == 1
out = template.replace('__EXAMPLE__', example)
with open(os.path.join(HERE, 'start.html'), 'w', encoding='utf-8') as fh:
    fh.write(out)
print('clients/start.html', len(out), 'bytes')
