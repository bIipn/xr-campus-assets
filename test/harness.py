import asyncio, os, sys, json
from playwright.async_api import async_playwright

SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST = os.path.join(SP, 'test')
OUT = os.path.join(TEST, 'shots2')
os.makedirs(OUT, exist_ok=True)
NM = os.path.join(TEST, 'node_modules')
NM2 = os.path.join(TEST, 'nm2', 'node_modules')
GFX_TIER = os.environ.get('CAMPUS_GFX', 'low')
HKDIR = os.environ.get('HK_DIR', os.path.join(SP, 'hk', 'out', 'h'))

def load_src():
    src = open(os.path.join(SP, 'xrlibraries-campus.html'), encoding='utf-8').read()
    src = src.replace('const ART = {};', 'const ART = window.__ART = {};')
    exports = ('window.__test = { walkTo, update, safeTarget, cam, ITEMS, BOOKS, viewFor, lobbyView, OBST, ROOMS, DOORS, STAFF, PLACES, SHELF_VIEWS, '
               'freeAt, walkable, roomAt, presetAnswer, chat, paint, startPaint, stopPaint, goView, openStaff, sendStaff, openBook, NAV, planPath, '
               'ride, openRide, startRide, endRide, COASTER, DIVE, DROP, WING, prog, collectToken, award, TOKENS, BADGES, TOKEN_MESH, openBadges, closeBadges, amb, YA, LIGHTS, coasterFrame, updateWings, '
               'rideUpdate, animateDive, lineFree, closeRideCard, openItem, pickItems, mergeStatic, BK, BAKED, loadBakedRoom, '
               'sim(sec){ const n = Math.round(sec * 60); for (let i = 0; i < n; i++){ if (!ride.on){ update(1 / 60); camera.position.set(cam.x, eyeY(), cam.z); camera.rotation.set(cam.pitch, cam.yaw, 0); } if (i % 10 === 0) updateWings(); yardPhysics(1 / 60); } }, timeRender(){ const t0 = performance.now(); gfxRender(); renderer.getContext().finish(); const t1 = performance.now(); yardPhysics(1 / 60); return [t1 - t0, performance.now() - t1]; }, GFX, NATURE, QUALITY, gfxApplyTier, PHYS, PLAYER, JOY, SWING, SPIN, kickProp, requestJump, pushSwing, spinSpinner, GOAL, TOWER, trackHeads, spinTokens, stationFrame, yardAmbient, yardPhysics, updateLights, gfxFrame, gfxLive, natureFrame, playerFrame, openStation, closeStation, STN, STATIONS, stRender, applyProjection, openBp, closeBp, bpv, bpBoardPart, bpViewFor, BP_INFO, BP_ORDER, BOARDS, BENCH, benchSt, BENCH_KITS, DIO, DIO_STEPS, dioApply, dioDrop, psd, titr, pend, SV, TT, PD, psdCalc, titrAdd, pendSetLen, HANDS, handsPlay, handsFinish, handsBusy, handsFrame, LAMPS, setPaintCanvas, paintDown, paintMove, paintUp, undoPaint, clearPaint, paintFrame, updatePaintButtons, LESSONS, KB, R102, R103, R104, CANVAS_FREE, LEAN_CANVAS, ART, fillViewer, openSearch, closeSearch, WAX_SCENES, WAX_ITEMS, WAX, waxView, waxFrame, waxSample, waxApply, waxResolve, HK, hkWant, hkAsset, HK_RIG, itemView, STOPS, showStop, startTour, MAP, drawPlan, frameOnce(dt){ frame(performance.now()); }, stepFrame(dt){ last = performance.now() - dt * 1000; frame(performance.now()); }, simStep(dt){ update(dt); camera.position.set(cam.x + CAMX.x, eyeY() + CAMX.y, cam.z + CAMX.z); camera.rotation.set(cam.pitch, cam.yaw, 0); stationFrame(dt); handsFrame(dt); }, renderFrom(p, t, fov){ const f0 = camera.fov; camera.position.set(p[0], p[1], p[2]); camera.lookAt(t[0], t[1], t[2]); if (fov){ camera.fov = fov; camera.updateProjectionMatrix(); } camera.updateMatrixWorld(); gfxRender(); if (fov){ camera.fov = f0; camera.updateProjectionMatrix(); } }, physReset, toastText(){ return document.getElementById("toast").hidden ? "" : document.getElementById("toast").textContent; }, get raf(){ return raf; }, get chain(){ return chain; }, GOAL, TOWER, SOC, KICK, KEEP, BODY, CAMX, socChargeStart, socChargeEnd, socFrame, keeperFrame, bodyFrame, kickPlan, socSim, socInRange, keeperPlan, keeperGo, SPEC:{ K:KSPEC, B:BSPEC }, get THREE(){ return THREE; }, get scene(){ return scene; }, get renderer(){ return renderer; }, get camera(){ return camera; }, get path(){ return path; }, get faceYaw(){ return faceYaw; }, get facePitch(){ return facePitch; } };\n')
    head, tail = src.rsplit('\nboot();\n', 1)
    src = head + '\n' + exports + 'boot();\n' + tail
    if os.environ.get('CAMPUS_MIN'):
        # Same terser settings as the Vercel build, to prove minification is safe
        import subprocess, tempfile
        a = src.rindex('<script type="module">\n') + len('<script type="module">\n')
        b = src.rindex('</script>')
        tools = os.path.join(os.path.dirname(SP), 'tools')
        with tempfile.TemporaryDirectory() as td:
            i, o = os.path.join(td, 'in.js'), os.path.join(td, 'out.js')
            open(i, 'w', encoding='utf-8').write(src[a:b])
            subprocess.run(['node', os.path.join(tools, 'minify.mjs'), 'js', i, o], cwd=tools, check=True, capture_output=True)
            src = src[:a] + open(o, encoding='utf-8').read() + '\n' + src[b:]
    return src

FONTS = [
  ('Old Standard TT', 'normal', 400, 'old-standard-tt/files/old-standard-tt-latin-400-normal.woff2'),
  ('Old Standard TT', 'normal', 700, 'old-standard-tt/files/old-standard-tt-latin-700-normal.woff2'),
  ('Old Standard TT', 'italic', 400, 'old-standard-tt/files/old-standard-tt-latin-400-italic.woff2'),
  ('Libre Franklin', 'normal', 400, 'libre-franklin/files/libre-franklin-latin-400-normal.woff2'),
  ('Libre Franklin', 'normal', 500, 'libre-franklin/files/libre-franklin-latin-500-normal.woff2'),
  ('Libre Franklin', 'normal', 600, 'libre-franklin/files/libre-franklin-latin-600-normal.woff2'),
  ('Libre Franklin', 'normal', 700, 'libre-franklin/files/libre-franklin-latin-700-normal.woff2'),
  ('Courier Prime', 'normal', 400, 'courier-prime/files/courier-prime-latin-400-normal.woff2'),
  ('Courier Prime', 'normal', 700, 'courier-prime/files/courier-prime-latin-700-normal.woff2'),
]
CSS = ''.join("@font-face{font-family:'%s';font-style:%s;font-weight:%d;src:url(https://fonts.gstatic.com/local/%s) format('woff2');font-display:swap}" % (f, s, w, p) for f, s, w, p in FONTS)

ESM = 'https://cdn.jsdelivr.net/npm/three@0.170.0/'
def esm_addon(rel):
    """Mimic jsDelivr's /+esm: bare 'three' and relative imports become absolute /+esm URLs."""
    import re, posixpath
    fp = os.path.join(NM2, 'three', 'examples', 'jsm', rel)
    src = open(fp, encoding='utf-8').read()
    base = posixpath.dirname(rel)
    def fix(m):
        spec = m.group(2)
        if spec == 'three': return m.group(1) + ESM + '+esm' + m.group(3)
        if spec.startswith('.'): return m.group(1) + ESM + 'examples/jsm/' + posixpath.normpath(posixpath.join(base, spec)) + '/+esm' + m.group(3)
        return m.group(0)
    return re.sub(r"(from\s*['\"])([^'\"]+)(['\"])", fix, src)

def wrapper():
    if os.environ.get('CAMPUS_NOMAP'):
        import re
        body = re.sub(r'<script type="importmap">.*?</script>', '', load_src(), count=1, flags=re.S)
        return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
            '<style>:root{color-scheme:light}body{margin:0;font:14px system-ui}img{max-width:100%}[hidden]{display:none!important}</style></head><body>'
            + body + '</body></html>')
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
            '<style>:root{color-scheme:light}body{margin:0;font:14px system-ui}img{max-width:100%}[hidden]{display:none!important}</style></head><body>'
            + load_src() + '</body></html>')

ARGS = ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-gpu-watchdog']

async def open_page(p, mode, reduced=True, init_script=None):
    html = wrapper()
    async def route(r):
        url = r.request.url
        if url.startswith('http://campus.test/h/'):
            fp = os.path.join(HKDIR, url.split('/h/', 1)[1].split('?')[0])
            if os.path.isfile(fp):
                return await r.fulfill(status=200, content_type='application/octet-stream', path=fp)
            return await r.fulfill(status=404, body='not found')
        if url.startswith('http://campus.test/lib/'):
            fp = os.path.join(SP, 'assets', 'lib', url.split('/lib/', 1)[1].split('?')[0])
            if os.path.isfile(fp):
                return await r.fulfill(status=200, content_type='application/octet-stream', path=fp)
            return await r.fulfill(status=404, body='not found')
        if url.startswith('http://campus.test/'):
            return await r.fulfill(status=200, content_type='text/html', body=html)
        if 'three.min.js' in url:
            return await r.fulfill(status=200, content_type='application/javascript', path=os.path.join(NM, 'three/build/three.min.js'))
        if os.environ.get('CAMPUS_NORAPIER') and 'rapier' in url:
            return await r.abort()
        if url.startswith(ESM) and url.endswith('/+esm'):
            rel = url[len(ESM):-len('/+esm')]
            if rel == '':
                return await r.fulfill(status=200, content_type='application/javascript', path=os.path.join(NM2, 'three', 'build', 'three.module.js'))
            if rel.startswith('examples/jsm/'):
                return await r.fulfill(status=200, content_type='application/javascript', body=esm_addon(rel[len('examples/jsm/'):]))
        if url.startswith('https://cdn.jsdelivr.net/npm/'):
            rel = url[len('https://cdn.jsdelivr.net/npm/'):].split('?')[0]
            pkg, _, rest = rel.partition('/') if not rel.startswith('@') else ('/'.join(rel.split('/')[:2]), None, '/'.join(rel.split('/')[2:]))
            name = pkg.rsplit('@', 1)[0]
            fp = os.path.join(NM2, name, rest)
            if os.path.isfile(fp):
                return await r.fulfill(status=200, content_type='application/javascript', path=fp)
        if url.startswith('https://fonts.googleapis.com/'):
            return await r.fulfill(status=200, content_type='text/css', body=CSS)
        if url.startswith('https://fonts.gstatic.com/local/'):
            return await r.fulfill(status=200, content_type='font/woff2', path=os.path.join(NM, '@fontsource', url.split('/local/')[1]))
        return await r.abort()
    b = await p.chromium.launch(args=ARGS)
    opts = dict(reduced_motion='reduce' if reduced else 'no-preference')
    if mode == 'desktop':
        ctx = await b.new_context(viewport={'width': 1280, 'height': 800}, device_scale_factor=1, **opts)
    elif mode == 'teaser':
        ctx = await b.new_context(viewport={'width': 1280, 'height': 720}, device_scale_factor=1.25, **opts)
    elif mode == 'small':
        ctx = await b.new_context(viewport={'width': 800, 'height': 500}, device_scale_factor=1, **opts)
    elif mode == 'tiny':
        ctx = await b.new_context(viewport={'width': 320, 'height': 240}, device_scale_factor=1, **opts)
    else:
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True, **opts)
    page = await ctx.new_page()
    logs = []
    page.on('console', lambda m: logs.append(m.type + ': ' + m.text))
    page.on('pageerror', lambda e: logs.append('PAGEERROR: ' + str(e)))
    await page.add_init_script("try { localStorage.setItem('xr-campus-gfx', %r); localStorage.setItem('xr-campus-gfx2', %r); } catch (e) {}" % (GFX_TIER, GFX_TIER))
    if init_script: await page.add_init_script(init_script)
    await page.route('**/*', route)
    await page.goto('http://campus.test/index.html')
    try:
        await page.wait_for_function("!document.querySelector('#bEnter').disabled || !document.querySelector('#nogl').hidden", timeout=int(os.environ.get('BOOT_TIMEOUT', '90000')))
    except Exception:
        print('BOOT TIMEOUT. Console:\n' + '\n'.join(logs[-30:]))
        raise
    return b, page, logs

def errs(logs):
    return '\n'.join(l for l in logs if 'error' in l.lower() or 'warn' in l.lower()) or 'no console errors'

async def view(page, v, wait=350):
    await page.evaluate("(v) => window.__test.goView(v)", v)
    await page.wait_for_timeout(wait)

async def shot(page, name):
    await page.screenshot(path=os.path.join(OUT, name + '.png'))
