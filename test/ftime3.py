import asyncio, os, sys, json, time
from harness import *
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        page.set_default_timeout(60000)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        async def ev(expr, t=60):
            return await asyncio.wait_for(page.evaluate(expr), t)
        async def tm(tag):
            r = await ev("() => { const T = window.__test; const out = []; for (let i = 0; i < 4; i++){ const t0 = performance.now(); T.frameOnce(); T.renderer.getContext().finish(); out.push(Math.round(performance.now() - t0)); } return out; }")
            print(tag, r, flush=True)
        await ev("() => { window.__noBody = true; window.__test.openStation('sieve'); }"); await page.wait_for_timeout(800); await tm('sieve')
        await ev("() => window.__test.openStation('titration')"); await page.wait_for_timeout(800); await tm('titration step0')
        await ev("() => { const T = window.__test; T.titr.step = 1; T.stRender(); T.goView(T.STATIONS.titration.view()); }"); await page.wait_for_timeout(500); await tm('titration spot')
        for name, js in [('no stream', "T.TT.stream.visible = false"), ('hide flask', "T.TT.flask.visible = false"), ('hide liquid', "T.TT.liquid.visible = false"), ('hide bottles', "for (const k in T.TT.bottles) T.TT.bottles[k].visible = false"), ('hide TT.g', "T.TT.g.visible = false"), ('hide hands fig', "T.HANDS.fig && (T.HANDS.fig.root.visible = false)")]:
            await ev("() => { const T = window.__test; " + js + "; }"); await tm(name)
        await ev("() => { const T = window.__test; T.TT.g.visible = true; T.TT.flask.visible = true; T.TT.liquid.visible = true; for (const k in T.TT.bottles) T.TT.bottles[k].visible = true; T.cam.pitch = 0.3; }"); await tm('look up')
        await ev("() => { const T = window.__test; T.cam.pitch = -0.28; T.cam.yaw = Math.PI; }"); await tm('look back')
        print(errs(logs))
        await b.close()
asyncio.run(run())
