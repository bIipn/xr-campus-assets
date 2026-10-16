"""Render clean stills of key views for visual review. Usage: CAMPUS_GFX=high python3 look.py [mode] [names...]"""
import asyncio, os, sys, time
from harness import *

VIEWS = [
  ('lobby', "window.__test.lobbyView()"),
  ('g1', "window.__test.PLACES.find(p => p.id === 'g1').view()"),
  ('library', "window.__test.PLACES.find(p => p.id === 'library').view()"),
  ('school', "({ x: 20, z: -3, yaw: -Math.PI / 2, pitch: 0.02 })"),
  ('studio', "window.__test.PLACES.find(p => p.id === 'studio').view()"),
  ('yard', "window.__test.PLACES.find(p => p.id === 'yard').view()"),
  ('coaster', "window.__test.PLACES.find(p => p.id === 'coaster').view()"),
  ('plaza', "({ x: 54, z: 6.5, yaw: 0.05, pitch: 0.16 })"),
  ('lawn', "({ x: 62, z: 14, yaw: 2.2, pitch: -0.12 })"),
  ('drop', "window.__test.PLACES.find(p => p.id === 'drop').view()"),
]
HIDE = '.hud,#plan,#hint,#tag,#toast,#askBtn,#award,#guide,#fade{display:none!important}'

async def run(mode, which):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, mode, True)
        page.set_default_timeout(300000)
        await (page.click('#bEnter') if mode == 'desktop' else page.tap('#bEnter'))
        await page.wait_for_timeout(400)
        await page.add_style_tag(content=HIDE)
        for name, expr in VIEWS:
            if which and name not in which: continue
            v = await page.evaluate('() => ' + expr)
            await page.evaluate("(v) => window.__test.goView(v)", v)
            await page.wait_for_timeout(700)
            t0 = time.time()
            await page.screenshot(path=os.path.join(OUT, 'look-' + mode[0] + '-' + name + '.jpg'), type='jpeg', quality=85)
            print(name, round(time.time() - t0, 1), 's')
        print(errs(logs))
        await b.close()

which = sys.argv[2:] if len(sys.argv) > 2 else None
asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else 'desktop', which))
