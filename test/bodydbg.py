import asyncio, os, sys, json, time
from harness import *
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        page.set_default_timeout(60000)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        async def ev(expr, t=30):
            t0 = time.time()
            try: return await asyncio.wait_for(page.evaluate(expr), t)
            except asyncio.TimeoutError: print('EVAL TIMEOUT after', round(time.time() - t0, 1), 's:', expr[:60], flush=True); raise
        await ev("() => window.__test.openStation('sieve')"); await page.wait_for_timeout(500)
        for k in range(40):
            r = await ev("() => { const T = window.__test; return { fig:!!T.HANDS.fig, mesh:!!(T.HANDS.fig && T.HANDS.fig.mesh), want:T.HK.want.hands, assets:[...T.HK.assets.keys()], frame:T.renderer.info.render.frame, tri:T.renderer.info.render.triangles, raf:T.raf }; }")
            print(k, r, flush=True)
            if r['mesh']: break
            await page.wait_for_timeout(1000)
        for k in range(6):
            t0 = time.time()
            r = await ev("() => { const T = window.__test; T.frameOnce(); return { frame:T.renderer.info.render.frame, tri:T.renderer.info.render.triangles, vis:T.HANDS.fig.root.visible }; }", 120)
            print('frame', k, round(time.time() - t0, 2), 's', r, flush=True)
        print(errs(logs))
        await b.close()
asyncio.run(run())
