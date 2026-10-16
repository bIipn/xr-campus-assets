"""Render grip and IK test shots. Usage: python3 soctest.py <scenario.json> <prefix>"""
import asyncio, os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'test'))
from harness import async_playwright, ARGS, NM2
HK = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(HK)
OUTH = os.path.join(HK, 'out', 'h')
RIG = os.path.join(HK, 'out', 'rig.json')
SHOTS = os.path.join(HK, 'shots')
IMPORTMAP = json.dumps({'imports': {'three': 'https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js', 'three/addons/': 'https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/'}})

def page_html(scenario):
    parts = os.path.join(SP, 'parts')
    src = lambda f: open(os.path.join(parts, f), encoding='utf-8').read()
    test = open(os.path.join(HK, 'gripscene.js'), encoding='utf-8').read()
    rig = open(RIG, encoding='utf-8').read()
    js = ("import * as THREE from 'three';\nimport { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';\n"
          "const HK_RIG = " + rig + ";\nconst SCENARIO = " + json.dumps(scenario) + ";\n"
          "const GFX = { tier:'high' }; const QUALITY = { high:{ msaa:4 }, medium:{ msaa:0 }, low:{ msaa:0 } }; const LEAN_CANVAS = false;\n"
          "const clamp = (v, a, b) => Math.max(a, Math.min(b, v)); const lerp = (a, b, t) => a + (b - a) * t;\n"
          "const PICK_PROXY = new THREE.MeshBasicMaterial({ visible:false }); function wake(){}\n"
          + src('waxfig.js') + '\n' + src('humans.js') + '\n' + src('hkik.js') + '\n' + src('socpose.js') + '\n' + test)
    return ('<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0;background:#222}</style></head><body>'
            '<script type="importmap">' + IMPORTMAP + '</script><script type="module">\n' + js + '\n</script></body></html>')

async def main(scenario, prefix, w=1280, h=800):
    html = page_html(scenario)
    async with async_playwright() as p:
        b = await p.chromium.launch(args=ARGS)
        ctx = await b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1)
        page = await ctx.new_page()
        logs = []
        page.on('console', lambda m: logs.append(m.type + ': ' + m.text))
        page.on('pageerror', lambda e: logs.append('PAGEERROR: ' + str(e)))
        async def route(r):
            url = r.request.url
            if url == 'http://hk.test/index.html':
                return await r.fulfill(status=200, content_type='text/html', body=html)
            if url.startswith('http://hk.test/h/'):
                fp = os.path.join(OUTH, url.split('/h/')[1])
                if os.path.isfile(fp): return await r.fulfill(status=200, content_type='application/octet-stream', path=fp)
                return await r.fulfill(status=404, body='nf')
            if url.startswith('https://cdn.jsdelivr.net/npm/three@0.170.0/'):
                rel = url[len('https://cdn.jsdelivr.net/npm/three@0.170.0/'):]
                return await r.fulfill(status=200, content_type='application/javascript', path=os.path.join(NM2, 'three', rel))
            return await r.abort()
        await page.route('**/*', route)
        await page.goto('http://hk.test/index.html')
        try:
            await page.wait_for_function('window.__shots !== undefined', timeout=180000)
        except Exception:
            print('\n'.join(logs[-30:])); raise
        if scenario.get('info'):
            print(json.dumps(await page.evaluate('window.__info()')))
        n = await page.evaluate('window.__shots.length')
        for i in range(n):
            name = await page.evaluate('(i) => window.__shots[i]', i)
            await page.evaluate('(i) => window.__shot(i)', i)
            await page.wait_for_timeout(120)
            await page.screenshot(path=os.path.join(SHOTS, prefix + '_' + name + '.jpg'), type='jpeg', quality=86)
            print('shot', prefix + '_' + name, flush=True)
        print('\n'.join(l for l in logs if 'error' in l.lower() or 'warn' in l.lower()) or 'no console errors')
        await b.close()

if __name__ == '__main__':
    sc = json.load(open(sys.argv[1]))
    asyncio.run(main(sc, sys.argv[2] if len(sys.argv) > 2 else 'grip'))
