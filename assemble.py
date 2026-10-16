import json, os
P = 'parts'
THREE_V = '0.170.0'
CDN = 'https://cdn.jsdelivr.net/npm/three@%s/' % THREE_V
IMPORTMAP = json.dumps({'imports': {'three': CDN + 'build/three.module.min.js', 'three/addons/': CDN + 'examples/jsm/'}})
PARTS = ['helpers.js', 'data.js', 'art.js', 'world.js', 'rooms.js', 'bpdata.js', 'bpdraw.js', 'outdoor.js', 'nature.js', 'gfx.js', 'dive.js',
         'nav.js', 'people.js', 'hkrig.js', 'humans.js', 'hkik.js', 'waxfig.js', 'waxpaint.js', 'waxprops.js', 'waxscenes.js', 'waxhall.js', 'stations.js', 'blueprints.js', 'lab.js', 'worldroom.js', 'paint.js', 'rides.js', 'phys.js', 'socpose.js', 'soccer.js', 'socplay.js', 'hands.js', 'baked.js', 'xr.js', 'progress.js',
         'engine.js', 'ui.js']

css = open(os.path.join(P, 'style_old.css'), encoding='utf-8').read()
assert css.startswith('<style>') and css.rstrip().endswith('</style>')
css = css.replace('/* Layout: a full-bleed walkable gallery. The interface sits in brass-edged wall-label panels at the edges, and every item opens as a typed catalog card. */',
                  '/* Layout: a full-bleed walkable campus. The interface sits in brass-edged wall-label panels at the edges; exhibits open as catalog cards and books open in a reader. */')
a = '.plan canvas{display:block;width:176px;height:48px}'
assert css.count(a) == 1
css = css.replace(a, '.plan canvas{display:block;width:180px;height:150px}\n@media (max-width:520px){.plan canvas{width:138px;height:115px}.plan{padding:6px 8px 8px}}')
add = open(os.path.join(P, 'style_add.css'), encoding='utf-8').read()
assert css.count('/* No 3D */') == 1
css = css.replace('/* No 3D */', add + '\n/* No 3D */')
body = open(os.path.join(P, 'body.html'), encoding='utf-8').read()
prelude = open(os.path.join(P, 'prelude.js'), encoding='utf-8').read()
app = '\n'.join(open(os.path.join(P, f), encoding='utf-8').read() for f in PARTS)
js = prelude + "\n(() => {\n'use strict';\n\n" + app + "\n})();\n"
assert '</script' not in js.lower(), 'A literal </script> in the JS would end the inline script early'
fonts = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&family=Libre+Franklin:wght@400;500;600;700&family=Old+Standard+TT:ital,wght@0,400;0,700;1,400&display=swap">\n')
scripts = '\n<script type="importmap">' + IMPORTMAP + '</script>\n<script type="module">\n' + js + '</script>\n'

# Claude artifact
B64_ON = "const HK = { base:'h/', b64:true,"
assert scripts.count("const HK = { base:'h/', b64:false,") == 1
html = '<title>XRLibraries Campus</title>\n' + fonts + css + '\n\n' + body + scripts.replace("const HK = { base:'h/', b64:false,", B64_ON)
open('xrlibraries-campus.html', 'w', encoding='utf-8').write(html)
print('xrlibraries-campus.html', len(html))

# Standalone pages for hosting outside Claude (Vercel). Claude's skeleton hides [hidden] panels; standalone pages need that reset too.
RESET = 'body{margin:0}img{max-width:100%}[hidden]{display:none!important}\n'
os.makedirs('deploy/src', exist_ok=True)
title = '<title>XRLibraries Campus · Concept by Ev Holt</title>\n'
doc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
       '<meta name="robots" content="noindex, nofollow">\n'
       '<meta name="description" content="An unofficial concept by Ev Holt (Walk the Archive) for XRLibraries: a walkable 3D campus with a museum, a library, a workshop school and a recess yard. Not an official XRLibraries site.">\n'
       '<meta name="theme-color" content="#0d1613">\n'
       + title + fonts + css.replace('<style>', '<style>\n' + RESET, 1) + '\n</head>\n<body>\n' + body + scripts + '</body>\n</html>\n')
open('deploy/index.html', 'w', encoding='utf-8').write(doc)
inner = css.strip()
assert inner.startswith('<style>') and inner.endswith('</style>')
open('deploy/src/style.css', 'w', encoding='utf-8').write(RESET + inner[len('<style>'):-len('</style>')].strip() + '\n')
open('deploy/src/body.html', 'w', encoding='utf-8').write(body)
open('deploy/src/app.js', 'w', encoding='utf-8').write(js)
open('deploy/src/importmap.json', 'w', encoding='utf-8').write(IMPORTMAP)
print('deploy/index.html', len(doc))
