import asyncio, sys, math
from harness import *

VIEWS = [
  ('y01-door-out', {'x':30.5, 'z':-3, 'yaw':-math.pi/2, 'pitch':0.04}),
  ('y02-yard', 'place:yard'),
  ('y03-coaster', 'place:coaster'),
  ('y04-drop', 'place:drop'),
  ('y05-dive', 'place:dive'),
  ('y06-rae', 'place:rae'),
  ('y07-school-back', {'x':57, 'z':-1.5, 'yaw':math.pi/2, 'pitch':0.1}),
  ('y08-play', {'x':47, 'z':4.5, 'yaw':2.5, 'pitch':0.02}),
  ('y09-east', {'x':88, 'z':-3, 'yaw':math.pi/2, 'pitch':0.12}),
  ('y10-plaza-n', {'x':54, 'z':2.5, 'yaw':0.25, 'pitch':0.25}),
]

async def run(mode, which):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, mode, True)
        await page.click('#bEnter') if mode == 'desktop' else await page.tap('#bEnter')
        await page.wait_for_timeout(300)
        page.set_default_timeout(120000)
        for name, v in VIEWS:
            if which and not any(w in name for w in which): continue
            if isinstance(v, str) and v.startswith('place:'): vv = await page.evaluate("(id) => window.__test.PLACES.find(p => p.id === id).view()", v[6:])
            else: vv = v
            await view(page, vv, 600)
            info = await page.evaluate("() => { const r = window.__test.renderer; return [r.info.render.calls, r.info.render.triangles]; }")
            print(name, info)
            await shot(page, mode[0] + '-' + name)
        print(mode, errs(logs))
        await b.close()

which = sys.argv[2:] if len(sys.argv) > 2 else None
asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else 'desktop', which))
