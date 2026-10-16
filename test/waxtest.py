"""Wax Hall checks: boot, doorway view, hall views and every scene mid-performance. Usage: CAMPUS_GFX=medium python3 waxtest.py [desktop|mobile] [scenes]"""
import asyncio, os, sys, time
from harness import *
T_AT = float(os.environ.get('WAX_T', '9'))
HIDE = '.hud,#plan,#hint,#tag,#toast,#askBtn,#award,#fade{display:none!important}'
async def run(mode, which):
    async with async_playwright() as p:
        t0 = time.time()
        b, page, logs = await open_page(p, mode, True)
        print('boot', round(time.time() - t0, 1), 's', flush=True)
        page.set_default_timeout(600000)
        await (page.click('#bEnter') if mode == 'desktop' else page.tap('#bEnter'))
        await page.wait_for_timeout(400)
        # Drive frames by hand so the page doesn't render continuously in the background
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
        info = await page.evaluate("""() => { const T = window.__test; return { scenes:T.WAX_SCENES.length, figs:T.WAX.figs.length, items:T.WAX_ITEMS.length, wax:!!T.WING.wax, calls:T.renderer.info.render.calls } }""")
        print(info, flush=True)
        async def go(v, wait=200):
            await page.evaluate("(v) => { const T = window.__test; T.goView(v); T.frameOnce(); T.frameOnce(); }", v)
            await page.wait_for_timeout(wait)
        async def snap(name):
            await page.screenshot(path=os.path.join(OUT, 'wax-' + mode[0] + '-' + name + '.jpg'), type='jpeg', quality=85)
            print('shot', name, flush=True)
        if 'door' in which:
            await go({'x': 0, 'z': -33.5, 'yaw': 0, 'pitch': 0.04}); await snap('door')
            await go({'x': 0, 'z': -43.3, 'yaw': 0, 'pitch': 0.08}); await snap('intro')
            await go({'x': 3.6, 'z': -45.8, 'yaw': 0.12, 'pitch': 0.02}); await snap('hall')
        if 'scenes' in which:
            only = [int(x) - 1 for x in os.environ.get('WAX_ONLY', '').split(',') if x.strip()]
            for i in (only or range(12)):
                v = await page.evaluate("(i) => window.__test.waxView(window.__test.WAX_SCENES[i])", i)
                await go(v, 300)
                # play this scene from its start to WAX_T scene-seconds (reduced motion plays at 0.6x)
                await page.evaluate("([i, tt]) => { const T = window.__test, S = T.WAX_SCENES[i].stage, k = matchMedia('(prefers-reduced-motion: reduce)').matches ? 0.6 : 1; S.t = 0; S.live = false; const n = Math.round(tt / k * 12); for (let j = 0; j < n; j++) T.waxFrame(1 / 12); }", [i, T_AT])
                await page.evaluate("() => window.__test.frameOnce()")
                await page.wait_for_timeout(500)
                await snap('s%02d' % (i + 1))
        print(errs(logs))
        await b.close()
mode = sys.argv[1] if len(sys.argv) > 1 else 'desktop'
which = sys.argv[2] if len(sys.argv) > 2 else 'door,scenes'
asyncio.run(run(mode, which))
