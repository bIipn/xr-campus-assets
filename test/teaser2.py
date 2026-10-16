"""Teaser stills with the new graphics and physics: CAMPUS_GFX=high python3 teaser2.py [names]"""
import asyncio, os, sys, time
from harness import *
OUTD = os.path.join(SP, 'teaser2'); os.makedirs(OUTD, exist_ok=True)
HIDE = '.hud,#plan,#hint,#tag,#toast,#askBtn,#award,#guide,#fade,.stick,.jumpbtn{display:none!important}'
T = 'window.__test'
VIEWS = [
  ('01-yard-blocks', "({ x:60.4, z:-0.6, yaw:-Math.PI / 2 - 0.42, pitch:-0.04 })", None),
  ('02-soccer-goal', "({ x:76.6, z:-3.5, yaw:-Math.PI / 2 - 0.13, pitch:-0.1 })", None),
  ('03-skydrop', "({ x:68.6, z:6.6, yaw:0, pitch:0 })", 'drop'),
  ('08-yard', "window.__test.PLACES.find(p => p.id === 'yard').view()", None),
  ('09-lobby', "window.__test.lobbyView()", None),
  ('04-library', "window.__test.PLACES.find(p => p.id === 'library').view()", None),
  ('05-gallery', "window.__test.PLACES.find(p => p.id === 'g1').view()", None),
  ('06-school', "({ x: 20, z: -3, yaw: -Math.PI / 2, pitch: 0.02 })", None),
  ('07-studio', "window.__test.PLACES.find(p => p.id === 'studio').view()", None),
]
async def run(which):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'teaser', True)
        page.set_default_timeout(400000)
        await page.click('#bEnter'); await page.wait_for_timeout(400)
        await page.add_style_tag(content=HIDE)
        for name, expr, _ in VIEWS:
            if which and not any(w in name for w in which): continue
            v = await page.evaluate('() => ' + expr)
            await page.evaluate("(v) => window.__test.goView(v)", v)
            await page.evaluate(T + '.sim(0.6)')
            if 'yard' in name or 'soccer' in name or 'plaza' in name:
                await page.wait_for_function(T + ".PHYS.mode !== ''", timeout=120000)
                await page.evaluate(T + '.sim(1.0)')
            if _ == 'drop':
                await page.evaluate(T + ".startRide('drop', false)")
                await page.wait_for_timeout(1500)
                await page.evaluate("const r = window.__test.ride; r.phase = 'hold'; r.y = 29.5; r.t = -100; r.look.yaw = -0.35; r.look.pitch = -0.05; r.look.at = performance.now() + 1e9; window.__test.rideUpdate(0.016)")
                await page.add_style_tag(content='#rideHud{display:none!important}')
            await page.wait_for_timeout(900)
            t0 = time.time()
            await page.screenshot(path=os.path.join(OUTD, name + '.jpg'), type='jpeg', quality=88)
            print(name, round(time.time() - t0, 1), 's')
        print(errs(logs))
        await b.close()
asyncio.run(run(sys.argv[1:]))
