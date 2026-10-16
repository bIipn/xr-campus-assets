"""Clean teaser stills of the campus (no interface) for sharing."""
import asyncio, os, math
from playwright.async_api import async_playwright
import harness
from harness import ARGS

OUTD = os.path.join(harness.SP, 'teaser')
os.makedirs(OUTD, exist_ok=True)
HIDE = '.hud,#plan,#hint,#tag,#toast,#askBtn,#award,#guide,#fade{display:none!important}'

async def main():
    html = harness.wrapper()
    async with async_playwright() as p:
        b = await p.chromium.launch(args=ARGS)
        ctx = await b.new_context(viewport={'width': 1280, 'height': 720}, device_scale_factor=1.25, reduced_motion='reduce')
        page = await ctx.new_page()
        page.set_default_timeout(240000)
        async def route(r):
            url = r.request.url
            if url.startswith('http://campus.test/'):
                return await r.fulfill(status=200, content_type='text/html', body=html)
            if 'three.min.js' in url:
                return await r.fulfill(status=200, content_type='application/javascript', path=os.path.join(harness.NM, 'three/build/three.min.js'))
            if url.startswith('https://fonts.googleapis.com/'):
                return await r.fulfill(status=200, content_type='text/css', body=harness.CSS)
            if url.startswith('https://fonts.gstatic.com/local/'):
                return await r.fulfill(status=200, content_type='font/woff2', path=os.path.join(harness.NM, '@fontsource', url.split('/local/')[1]))
            return await r.abort()
        await page.route('**/*', route)
        await page.goto('http://campus.test/index.html')
        await page.wait_for_function("!document.querySelector('#bEnter').disabled", timeout=90000)
        await page.click('#bEnter')
        await page.wait_for_timeout(500)
        await page.add_style_tag(content=HIDE)
        views = {
            'yard': "window.__test.PLACES.find(p => p.id === 'yard').view()",
            'coaster': "window.__test.PLACES.find(p => p.id === 'coaster').view()",
            'lobby': "window.__test.lobbyView()",
            'library': "window.__test.PLACES.find(p => p.id === 'library').view()",
            'yard-wide': "({ x: 47, z: 4.5, yaw: 2.5, pitch: 0.06 })",
            'plaza': "({ x: 54, z: 6.5, yaw: 0.05, pitch: 0.16 })",
        }
        for name, expr in views.items():
            try:
                v = await page.evaluate('() => ' + expr)
            except Exception as e:
                print(name, 'skip', e); continue
            await page.evaluate("(v) => window.__test.goView(v)", v)
            await page.wait_for_timeout(900)
            path = os.path.join(OUTD, name + '.jpg')
            await page.screenshot(path=path, type='jpeg', quality=88)
            print(name, os.path.getsize(path))
        await b.close()

asyncio.run(main())
