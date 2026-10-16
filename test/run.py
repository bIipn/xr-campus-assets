import asyncio, base64, os, sys, json
from playwright.async_api import async_playwright

SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST = os.path.join(SP, 'test')
OUT = os.path.join(TEST, 'shots')
os.makedirs(OUT, exist_ok=True)
NM = os.path.join(TEST, 'node_modules')

src = open(os.path.join(SP, 'pine-hollow-remembers.html'), encoding='utf-8').read()
src = src.replace('const ART = {};', 'const ART = window.__ART = {};')
src = src.replace('boot();\n})();', 'window.__test = { walkTo, update, safeTarget, cam, ITEMS, viewFor, lobbyView, OBST, get path(){ return path; } };\nboot();\n})();')
assert 'window.__test' in src
wrapper = ('<!doctype html><html><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
           '<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
           'body{margin:0;font:14px system-ui}img{max-width:100%}[hidden]{display:none!important}</style></head><body>'
           + src + '</body></html>')

FONTS = [
  ('Old Standard TT', 'normal', 400, 'old-standard-tt/files/old-standard-tt-latin-400-normal.woff2'),
  ('Old Standard TT', 'normal', 700, 'old-standard-tt/files/old-standard-tt-latin-700-normal.woff2'),
  ('Old Standard TT', 'italic', 400, 'old-standard-tt/files/old-standard-tt-latin-400-italic.woff2'),
  ('UnifrakturMaguntia', 'normal', 400, 'unifrakturmaguntia/files/unifrakturmaguntia-latin-400-normal.woff2'),
  ('Libre Franklin', 'normal', 400, 'libre-franklin/files/libre-franklin-latin-400-normal.woff2'),
  ('Libre Franklin', 'normal', 500, 'libre-franklin/files/libre-franklin-latin-500-normal.woff2'),
  ('Libre Franklin', 'normal', 600, 'libre-franklin/files/libre-franklin-latin-600-normal.woff2'),
  ('Courier Prime', 'normal', 400, 'courier-prime/files/courier-prime-latin-400-normal.woff2'),
  ('Courier Prime', 'normal', 700, 'courier-prime/files/courier-prime-latin-700-normal.woff2'),
]
css = ''.join("@font-face{font-family:'%s';font-style:%s;font-weight:%d;src:url(https://fonts.gstatic.com/local/%s) format('woff2');font-display:swap}" % (f, s, w, p) for f, s, w, p in FONTS)

async def route(r):
    url = r.request.url
    if url.startswith('http://museum.test/'):
        return await r.fulfill(status=200, content_type='text/html', body=wrapper)
    if 'three.min.js' in url:
        return await r.fulfill(status=200, content_type='application/javascript', path=os.path.join(NM, 'three/build/three.min.js'))
    if url.startswith('https://fonts.googleapis.com/'):
        return await r.fulfill(status=200, content_type='text/css', body=css)
    if url.startswith('https://fonts.gstatic.com/local/'):
        return await r.fulfill(status=200, content_type='font/woff2', path=os.path.join(NM, '@fontsource', url.split('/local/')[1]))
    return await r.abort()

ARGS = ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']

async def open_page(p, mode, reduced):
    b = await p.chromium.launch(args=ARGS)
    opts = dict(reduced_motion='reduce' if reduced else 'no-preference')
    if mode == 'desktop':
        ctx = await b.new_context(viewport={'width': 1280, 'height': 800}, device_scale_factor=1, **opts)
    elif mode == 'tiny':
        ctx = await b.new_context(viewport={'width': 320, 'height': 240}, device_scale_factor=1, **opts)
    else:
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True, **opts)
    page = await ctx.new_page()
    logs = []
    page.on('console', lambda m: logs.append(m.type + ': ' + m.text))
    page.on('pageerror', lambda e: logs.append('PAGEERROR: ' + str(e)))
    await page.route('**/*', route)
    await page.goto('http://museum.test/index.html')
    await page.wait_for_function("!document.querySelector('#bEnter').disabled || !document.querySelector('#nogl').hidden", timeout=30000)
    return b, page, logs

async def shots(mode):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, mode, True)
        await page.wait_for_timeout(300)
        await page.screenshot(path=f'{OUT}/{mode}-01-intro.png')
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        await page.screenshot(path=f'{OUT}/{mode}-02-lobby.png')
        await page.click('#bTour'); await page.wait_for_timeout(300)
        await page.screenshot(path=f'{OUT}/{mode}-03-stop1.png')
        want = {2, 3, 4, 8, 10, 16, 17} if mode == 'desktop' else {2, 4, 16}
        for stop in range(2, 18):
            await page.click('#tNext'); await page.wait_for_timeout(150)
            if stop in want:
                await page.wait_for_timeout(250)
                await page.screenshot(path=f'{OUT}/{mode}-04-stop{stop:02d}.png')
            if stop == 8:
                await page.click('#tOpen'); await page.wait_for_timeout(250)
                await page.screenshot(path=f'{OUT}/{mode}-05-viewer-oral.png')
                await page.click('#vClose')
        await page.click('#tNext')
        await page.click('#bSearch'); await page.fill('#q', '1929'); await page.wait_for_timeout(200)
        await page.screenshot(path=f'{OUT}/{mode}-06-search.png')
        await page.click('.result >> nth=0'); await page.wait_for_timeout(300)
        await page.screenshot(path=f'{OUT}/{mode}-07-viewer-news.png')
        print(mode, '\n'.join(l for l in logs if 'error' in l.lower() or 'warn' in l.lower()) or 'no console errors')
        await b.close()

SIM = r"""
() => {
  const T = window.__test, out = [];
  const ok = (x, z) => {
    if (x < -5.56 || x > 5.56 || z > -0.44 || z < -41.56) return 'outside';
    for (const zp of [-6, -18, -30]) if (Math.abs(z - zp) < 0.16 && Math.abs(x) > 1.5) return 'wall at ' + zp;
    for (const o of T.OBST) if (Math.hypot(x - o.x, z - o.z) < o.r - 0.05) return 'obstacle';
    return null;
  };
  const run = (label, v) => {
    T.walkTo({ x:v.x, z:v.z }, { yaw:v.yaw, pitch:v.pitch });
    let bad = null, steps = 0;
    while ((T.path.length || steps < 5) && steps < 4000){ T.update(1/60); steps++; const e = ok(T.cam.x, T.cam.z); if (e && !bad) bad = e + ' @ ' + T.cam.x.toFixed(2) + ',' + T.cam.z.toFixed(2); }
    for (let i = 0; i < 200; i++) T.update(1/60);
    const err = Math.hypot(T.cam.x - v.x, T.cam.z - v.z), yawErr = v.yaw == null ? 0 : Math.abs(Math.atan2(Math.sin(T.cam.yaw - v.yaw), Math.cos(T.cam.yaw - v.yaw)));
    out.push([label, steps, +err.toFixed(3), +yawErr.toFixed(3), bad]);
  };
  T.cam.x = 0; T.cam.z = -0.7; T.cam.yaw = 0;
  run('lobby', T.lobbyView());
  for (const it of T.ITEMS) run(it.id, T.viewFor(it));
  run('back to lobby', { x:0, z:-2, yaw:0, pitch:0 });
  for (const it of [...T.ITEMS].reverse()) run('rev ' + it.id, T.viewFor(it));
  const rnd = (s => () => (s = (s * 16807) % 2147483647) / 2147483647)(7);
  for (let i = 0; i < 40; i++){ const v = T.safeTarget({ x:(rnd() - 0.5) * 12, z:-0.3 - rnd() * 41.4 }); run('rand' + i, v); }
  return out;
}
"""

async def sim():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'tiny', False)
        res = await page.evaluate(SIM)
        bad = [r for r in res if r[4] or r[2] > 0.05]
        for r in res[:18]: print(r)
        print('total', len(res), 'problems', len(bad))
        for r in bad: print('BAD', r)
        await b.close()

which = sys.argv[1] if len(sys.argv) > 1 else 'all'
if which in ('all', 'sim'): asyncio.run(sim())
if which in ('all', 'desktop'): asyncio.run(shots('desktop'))
if which in ('all', 'phone'): asyncio.run(shots('phone'))
