import asyncio, os, sys, json, time
from harness import *
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        page.set_default_timeout(60000)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        async def ev(expr, t=25):
            t0 = time.time()
            try: return await asyncio.wait_for(page.evaluate(expr), t)
            except asyncio.TimeoutError: print('EVAL TIMEOUT after', round(time.time() - t0, 1), 's', flush=True); raise
        await ev("() => window.__test.openStation('titration')"); await page.wait_for_timeout(1500)
        steps = [
          ("step1", "() => { const T = window.__test; T.titr.step = 1; T.stRender(); T.goView(T.STATIONS.titration.view()); }"),
          ("setup", "() => { const T = window.__test; T.titr.set = true; T.titr.fill = 2; T.titrVisualX && 0; T.stRender(); }"),
          ("step2", "() => { const T = window.__test; T.titr.step = 2; T.stRender(); }"),
          ("idle", "() => { const T = window.__test; const b = [...document.querySelectorAll('#stBtns button')].find((x) => x.textContent.trim() === '+1 mL'); b && b.click(); }"),
          ("pitch", "() => { const T = window.__test; T.cam.pitch = -0.6; }"),
          ("pitch2", "() => { const T = window.__test; T.cam.pitch = -1.0; }"),
          ("yaw", "() => { const T = window.__test; T.cam.yaw = 0.6; }"),
        ]
        for name, js in steps:
            t0 = time.time(); await ev(js)
            for k in range(5):
                await page.wait_for_timeout(400)
                r = await ev("() => { const T = window.__test; return { frame:T.renderer.info.render.frame, tri:T.renderer.info.render.triangles, vis:!!(T.HANDS.fig && T.HANDS.fig.root.visible), added:T.titr.added, busy:T.handsBusy(), pitch:+T.cam.pitch.toFixed(2) }; }")
            print(name, round(time.time() - t0, 1), 's', r, flush=True)
        print(errs(logs))
        await b.close()
asyncio.run(run())
