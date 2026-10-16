import asyncio, os, sys, json, time
from harness import *
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', False)
        page.set_default_timeout(60000)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        await page.evaluate("() => { const T = window.__test; window.__noBody = true; T.openStation('pendulum'); T.pend.step = 1; T.stRender(); }"); await page.wait_for_timeout(800)
        await page.evaluate("() => { const T = window.__test; T.pend.run = true; T.pend.t = 0; T.pend.swings = 0; T.PD.disp.set('0.000 s', 'SWING 0 OF 10'); T.stRender(); }")
        for k in range(6):
            r0 = await page.evaluate("() => ({ f:window.__test.renderer.info.render.frame, t:performance.now(), pt:window.__test.pend.t })")
            await page.wait_for_timeout(1000)
            r1 = await page.evaluate("() => ({ f:window.__test.renderer.info.render.frame, t:performance.now(), pt:window.__test.pend.t })")
            print('frames/s', round((r1['f'] - r0['f']) / ((r1['t'] - r0['t']) / 1000)), 'pend.t advanced', round(r1['pt'] - r0['pt'], 3), flush=True)
        await b.close()
asyncio.run(run())
