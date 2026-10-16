import asyncio, os, sys, json, time
from harness import *
MODE = sys.argv[1] if len(sys.argv) > 1 else 'plain'
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        page.set_default_timeout(60000)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        async def ev(expr, t=25):
            t0 = time.time()
            try: return await asyncio.wait_for(page.evaluate(expr), t)
            except asyncio.TimeoutError: print('EVAL TIMEOUT after', round(time.time() - t0, 1), 's', flush=True); raise
        if MODE == 'nobody': await ev("() => { window.__noBody = true; }")
        for station in ['sieve', 'titration', 'pendulum', 'bench', 'titration', 'sieve', 'titration']:
            t0 = time.time()
            await ev("(s) => window.__test.openStation(s)".replace('(s)', '(() => ') + "('" + station + "'))" if False else "() => window.__test.openStation('" + station + "')")
            for k in range(8):
                await page.wait_for_timeout(500)
                r = await ev("() => { const T = window.__test; return { frame:T.renderer.info.render.frame, tri:T.renderer.info.render.triangles, vis:!!(T.HANDS.fig && T.HANDS.fig.root.visible), mesh:!!(T.HANDS.fig && T.HANDS.fig.mesh), raf:T.raf }; }")
            print(station, round(time.time() - t0, 1), 's', r, flush=True)
        print(errs(logs))
        await b.close()
asyncio.run(run())
