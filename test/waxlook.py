"""Render a lineup of wax figures in isolation to tune their look. Usage: python3 waxlook.py [out.png] [scene-js-file]"""
import asyncio, os, sys
from playwright.async_api import async_playwright
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NM2 = os.path.join(SP, 'test', 'nm2', 'node_modules')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SP, 'test', 'shots2', 'wax-look.png')
SCENE = open(sys.argv[2]).read() if len(sys.argv) > 2 else ''
helpers = open(os.path.join(SP, 'parts', 'helpers.js'), encoding='utf-8').read()
fig = open(os.path.join(SP, 'parts', 'waxfig.js'), encoding='utf-8').read()
HTML = '''<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0;background:#222}canvas{display:block}</style>
<script type="importmap">{"imports":{"three":"http://t.test/three.module.js","three/addons/":"http://t.test/jsm/"}}</script></head><body>
<script type="module">
import * as THREE_ from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
const THREE = THREE_; const XT = { RoundedBoxGeometry };
''' + helpers + fig + '''
const W = 1400, H = 820;
const renderer = new THREE.WebGLRenderer({ antialias:true }); renderer.setSize(W, H); document.body.appendChild(renderer.domElement);
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.outputColorSpace = THREE.SRGBColorSpace;
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x231a1c);
const pm = new THREE.PMREMGenerator(renderer); scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture; scene.environmentIntensity = 0.55;
const cam = new THREE.PerspectiveCamera(30, W / H, 0.05, 100); cam.position.set(0, 1.35, 6.2); cam.lookAt(0, 1.0, 0);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(20, 20), new THREE.MeshStandardMaterial({ color:0x4a3a30, roughness:0.7 })); floor.rotation.x = -Math.PI / 2; scene.add(floor);
const key = new THREE.PointLight(0xffe2c0, 30, 30, 1.2); key.position.set(1.5, 3.6, 4); scene.add(key);
const fill = new THREE.PointLight(0xc8d8ff, 8, 30, 1.2); fill.position.set(-4, 2.5, 2); scene.add(fill);
scene.add(new THREE.HemisphereLight(0xfff1dc, 0x2a2118, 0.4));
waxMats();
window.__scene = scene; window.__cam = cam; window.__r = renderer;
window.__render = () => renderer.render(scene, cam);
''' + SCENE + '''
window.__render();
window.__done = true;
</script></body></html>'''
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        pg = await (await b.new_context(viewport={'width': 1400, 'height': 820})).new_page()
        logs = []
        pg.on('console', lambda m: logs.append(m.type + ': ' + m.text)); pg.on('pageerror', lambda e: logs.append('PAGEERROR: ' + str(e)))
        async def route(r):
            u = r.request.url
            if u == 'http://t.test/index.html': return await r.fulfill(status=200, content_type='text/html', body=HTML)
            if u == 'http://t.test/three.module.js': return await r.fulfill(status=200, content_type='application/javascript', path=os.path.join(NM2, 'three', 'build', 'three.module.js'))
            if u.startswith('http://t.test/jsm/'):
                src = open(os.path.join(NM2, 'three', 'examples', 'jsm', u[len('http://t.test/jsm/'):]), encoding='utf-8').read()
                return await r.fulfill(status=200, content_type='application/javascript', body=src)
            return await r.abort()
        await pg.route('**/*', route)
        await pg.goto('http://t.test/index.html')
        try: await pg.wait_for_function('window.__done === true', timeout=120000)
        except Exception: print('\n'.join(logs[-20:])); raise
        await pg.wait_for_timeout(300)
        await pg.screenshot(path=OUT)
        print('\n'.join(l for l in logs if 'error' in l.lower() or 'warn' in l.lower()) or 'no console errors')
        await b.close()
asyncio.run(main())
