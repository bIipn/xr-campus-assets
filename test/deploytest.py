"""Test the Vercel build (deploy/site) exactly as it will be served."""
import asyncio, os, sys
from playwright.async_api import async_playwright
from harness import CSS, ARGS, NM, NM2, OUT, errs

SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.environ.get('DEPLOY_SITE') or os.path.join(SP, 'deploy', 'site')

async def open_site(p, mode, delay=0.0, break_chunk=False):
    async def route(r):
        url = r.request.url
        if url.startswith('http://campus.test/'):
            path = url[len('http://campus.test/'):].split('?')[0] or 'index.html'
            fp = os.path.join(SITE, path)
            if path.startswith('c/'):
                if delay: await asyncio.sleep(delay)
                if break_chunk and path == sorted(os.listdir(os.path.join(SITE, 'c')))[0].join(['c/', '']):
                    return await r.fulfill(status=404, body='missing')
            if os.path.isfile(fp):
                ct = 'text/html; charset=utf-8' if fp.endswith('.html') else 'application/octet-stream'
                return await r.fulfill(status=200, content_type=ct, path=fp)
            return await r.fulfill(status=404, body='missing')
        if url.startswith('https://cdn.jsdelivr.net/npm/'):
            rel = url[len('https://cdn.jsdelivr.net/npm/'):].split('?')[0]
            pkg, _, rest = rel.partition('/') if not rel.startswith('@') else ('/'.join(rel.split('/')[:2]), None, '/'.join(rel.split('/')[2:]))
            fp = os.path.join(NM2, pkg.rsplit('@', 1)[0], rest)
            if os.path.isfile(fp):
                return await r.fulfill(status=200, content_type='application/javascript', path=fp, headers={'access-control-allow-origin': '*'})
        if url.startswith('https://fonts.googleapis.com/'):
            return await r.fulfill(status=200, content_type='text/css', body=CSS)
        if url.startswith('https://fonts.gstatic.com/local/'):
            return await r.fulfill(status=200, content_type='font/woff2', path=os.path.join(NM, '@fontsource', url.split('/local/')[1]))
        return await r.abort()
    b = await p.chromium.launch(args=ARGS)
    if mode == 'desktop':
        ctx = await b.new_context(viewport={'width': 1280, 'height': 800}, device_scale_factor=1, reduced_motion='reduce')
    else:
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True, reduced_motion='reduce')
    await ctx.add_init_script("try { localStorage.setItem('xr-campus-gfx', 'low'); localStorage.setItem('xr-campus-gfx2', 'low'); } catch (e) {}")
    page = await ctx.new_page()
    logs = []
    page.on('console', lambda m: logs.append(m.type + ': ' + m.text))
    page.on('pageerror', lambda e: logs.append('PAGEERROR: ' + str(e)))
    await page.route('**/*', route)
    await page.goto('http://campus.test/')
    return b, page, logs

async def ask(page, q, tap):
    await page.fill('#gq', q)
    await page.press('#gq', 'Enter')
    await page.wait_for_timeout(900)
    return await page.evaluate("() => { const m = document.querySelectorAll('#gMsgs .msg'); return m.length ? m[m.length - 1].innerText.slice(0, 160) : document.querySelector('#gMsgs').innerText.slice(-200); }")

async def run(mode):
    tap = mode != 'desktop'
    async with async_playwright() as p:
        # 1. Loading screen (slow chunks)
        b, page, logs = await open_site(p, mode, delay=1.2)
        await page.wait_for_timeout(500)
        await page.screenshot(path=os.path.join(OUT, mode[0] + '-deploy-loading.png'))
        await page.wait_for_function("document.querySelector('#bEnter') && !document.querySelector('#bEnter').disabled", timeout=90000)
        info = await page.evaluate("""() => ({ title: document.title, boot: !!document.getElementById('boot'), bootcss: !!document.getElementById('bootcss'),
            bootvar: 'window.__boot' in window && window.__boot !== undefined, save: !document.querySelector('#pbSave').hidden, gl: document.querySelector('#nogl').hidden && !!document.querySelector('#scene').getContext('webgl2'),
            meta: document.getElementById('introMeta').textContent, robots: document.querySelector('meta[name=robots]').content })""")
        print(mode, info)
        await page.screenshot(path=os.path.join(OUT, mode[0] + '-deploy-intro.png'))
        await (page.tap('#bEnter') if tap else page.click('#bEnter'))
        await page.wait_for_timeout(900)
        await page.screenshot(path=os.path.join(OUT, mode[0] + '-deploy-lobby.png'))
        await (page.tap('#askBtn') if tap else page.click('#askBtn'))
        await page.wait_for_timeout(400)
        print(' note:', await page.evaluate("() => document.querySelector('#gNote').textContent"))
        for q in ['what is XRLibraries', 'who are you', 'take me to the recess yard']:
            print(' Q', q, '->', (await ask(page, q, tap)).replace('\n', ' | '))
        await page.wait_for_timeout(2500)
        await page.screenshot(path=os.path.join(OUT, mode[0] + '-deploy-after.png'))
        print(' ', errs(logs))
        await b.close()
        # 2. Broken chunk shows a friendly message
        b, page, logs = await open_site(p, mode, break_chunk=True)
        await page.wait_for_timeout(2500)
        print(' broken:', await page.evaluate("() => [document.getElementById('bootMsg') && document.getElementById('bootMsg').textContent, document.getElementById('bootTrack') && document.getElementById('bootTrack').hidden]"))
        await b.close()

asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else 'desktop'))
