import asyncio, os, sys, json
from harness import *
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', False)
        page.set_default_timeout(600000)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
        await page.evaluate("() => { const T = window.__test; T.openStation('sieve'); T.hkWant('hands'); }")
        for k in range(60):
            if await page.evaluate("() => !!(window.__test.HANDS.fig && window.__test.HANDS.fig.mesh)"): break
            await page.wait_for_timeout(200)
        await page.evaluate("""() => { const T = window.__test; T.psd.step = 2; T.psd.splitting = 2; T.SV.frac = 0.25; T.stRender(); T.goView(T.STATIONS.sieve.view()); for (let i = 0; i < 150; i++) T.simStep(1/30); }""")
        await page.evaluate("""() => { const b = [...document.querySelectorAll('#stBtns button')].find((x) => x.textContent.trim() === 'Dry it in the oven'); b.click(); }""")
        for t in range(0, 40):
            r = await page.evaluate("""() => { const T = window.__test, H = T.HANDS; for (let i = 0; i < 6; i++) T.simStep(1/30);
              const C = H.clip; const d = (a) => (a * 57.3).toFixed(0);
              return [C ? H.t.toFixed(2) : 'idle', C && C.waitArrive ? 'walk' : '', 'cam', T.cam.x.toFixed(2), T.cam.z.toFixed(2), 'yaw', d(T.cam.yaw), 'pitch', d(T.cam.pitch), 'face', T.faceYaw == null ? '-' : d(T.faceYaw), T.facePitch == null ? '-' : d(T.facePitch), 'body', d(H.yaw), 'tw', d(H.twist), 'fpt', H.fpt ? [H.fpt.x.toFixed(2), H.fpt.y.toFixed(2), H.fpt.z.toFixed(2)].join(',') : '-', 'L', H.h.L.w.toFixed(2), 'lean', H.lean.toFixed(0), (H.crouch||0).toFixed(2), 'camx', [T.CAMX.x.toFixed(2), T.CAMX.y.toFixed(2), T.CAMX.z.toFixed(2)].join(',')]; }""")
            print(' '.join(map(str, r)), flush=True)
            if r[0] == 'idle' and t > 5: break
        await b.close()
asyncio.run(run())
