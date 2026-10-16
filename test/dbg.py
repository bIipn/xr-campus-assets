"""Debug a single view: CAMPUS_GFX=<tier> python3 dbg.py <viewname> [js-to-eval-before-shot]"""
import asyncio, os, sys, json, time
from harness import *

HIDE = '.hud,#plan,#hint,#tag,#toast,#askBtn,#award,#guide,#fade{display:none!important}'
VIEWS = {
  'lobby': "window.__test.lobbyView()",
  'library': "window.__test.PLACES.find(p => p.id === 'library').view()",
  'g1': "window.__test.PLACES.find(p => p.id === 'g1').view()",
  'studio': "window.__test.PLACES.find(p => p.id === 'studio').view()",
  'school': "({ x: 20, z: -3, yaw: -Math.PI / 2, pitch: 0.02 })",
  'yard': "window.__test.PLACES.find(p => p.id === 'yard').view()",
}

async def run(name, extra):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        page.set_default_timeout(300000)
        await page.click('#bEnter')
        await page.wait_for_timeout(400)
        await page.add_style_tag(content=HIDE)
        v = await page.evaluate('() => ' + VIEWS.get(name, name))
        await page.evaluate("(v) => window.__test.goView(v)", v)
        await page.wait_for_timeout(900)
        if extra:
            print(await page.evaluate(extra))
        t0 = time.time()
        await page.screenshot(path=os.path.join(OUT, 'dbg-' + os.environ.get('CAMPUS_GFX', 'low') + '-' + name + '.jpg'), type='jpeg', quality=85)
        print('shot', round(time.time() - t0, 1))
        print(errs(logs))
        await b.close()

asyncio.run(run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
