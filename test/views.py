import asyncio, sys
from harness import *

VIEWS = [
  ('v01-lobby-left', {'x':0, 'z':-2.5, 'yaw':1.25, 'pitch':0.05}),
  ('v02-lobby-right', {'x':0, 'z':-2.5, 'yaw':-1.25, 'pitch':0.05}),
  ('v03-lobby-back', 'lobby'),
  ('v04-hall-lib', {'x':-6.8, 'z':-3, 'yaw':1.5708, 'pitch':0.04}),
  ('v05-library', 'place:library'),
  ('v06-desk', 'place:desk'),
  ('v07-featured', 'place:featured'),
  ('v08-aisle', {'x':-23.6, 'z':-3, 'yaw':1.5708, 'pitch':0.1}),
  ('v09-stack', 'shelf:basics'),
  ('v10-window', 'place:window'),
  ('v11-lib-back', {'x':-29.5, 'z':-3, 'yaw':-1.5708, 'pitch':0.12}),
  ('v12-freedom', 'place:freedomBoard'),
  ('v13-school', 'place:school'),
  ('v14-studio', 'place:studio'),
  ('v15-hale', {'x':18.7, 'z':-7.6, 'yaw':0.42, 'pitch':0}),
  ('v16-sculpture', 'place:sculpture'),
]

async def run(mode, which):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, mode, True)
        await page.click('#bEnter') if mode == 'desktop' else await page.tap('#bEnter')
        await page.wait_for_timeout(300)
        page.set_default_timeout(120000)
        for name, v in VIEWS:
            if which and not any(w in name for w in which): continue
            if v == 'lobby': vv = await page.evaluate("window.__test.lobbyView()")
            elif isinstance(v, str) and v.startswith('place:'): vv = await page.evaluate("(id) => window.__test.PLACES.find(p => p.id === id).view()", v[6:])
            elif isinstance(v, str) and v.startswith('shelf:'): vv = await page.evaluate("(id) => window.__test.SHELF_VIEWS[id]", v[6:])
            else: vv = v
            await view(page, vv, 450)
            info = await page.evaluate("() => { const r = window.__test.renderer; return [r.info.render.calls, r.info.render.triangles]; }")
            print(name, info)
            await shot(page, mode[0] + '-' + name)
        print(mode, errs(logs))
        await b.close()

which = sys.argv[2:] if len(sys.argv) > 2 else None
asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else 'desktop', which))
