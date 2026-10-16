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
        await page.evaluate("""() => { const T = window.__test; T.psd.step = 2; T.psd.splitting = 2; T.SV.frac = 0.25; T.stRender(); for (let i = 0; i < 90; i++) T.simStep(1/30); }""")
        await page.evaluate("""() => { const b = [...document.querySelectorAll('#stBtns button')].find((x) => x.textContent.trim() === 'Dry it in the oven'); b.click(); }""")
        for t in range(0, 60):
            r = await page.evaluate("""() => { const T = window.__test, H = T.HANDS; for (let i = 0; i < 15; i++) T.simStep(1/30);
              const v = new T.SV.tray.position.constructor(); T.SV.tray.getWorldPosition(v);
              return [H.clip ? H.t.toFixed(2) : 'idle', H.clip && H.clip.waitArrive ? 'walk' : '', T.cam.x.toFixed(2), T.cam.z.toFixed(2), T.path.length, 'tray', v.x.toFixed(2), v.y.toFixed(2), v.z.toFixed(2), T.SV.tray.parent === T.SV.g ? 'g' : T.SV.tray.parent.name || T.SV.tray.parent.type, 'L', H.h.L.w.toFixed(2), H.h.L.tp.x.toFixed(2), H.h.L.tp.y.toFixed(2), H.h.L.tp.z.toFixed(2), 'lean', H.lean.toFixed(0), (H.crouch||0).toFixed(2), 'door', T.SV.door.rotation.y.toFixed(2)]; }""")
            print(' '.join(map(str, r)), flush=True)
            if r[0] == 'idle' and t > 5: break
        print(errs(logs))
        await b.close()
asyncio.run(run())
