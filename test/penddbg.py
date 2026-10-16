import asyncio, os, sys, json, time
from harness import *
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        page.set_default_timeout(60000)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
        S = "([n]) => { const T = window.__test; for (let i = 0; i < n; i++) T.simStep(1 / 30); return { run:T.pend.run, busy:T.handsBusy(), clipT:T.HANDS.clip && T.HANDS.clip.T, t:T.HANDS.t, wait:T.HANDS.clip && T.HANDS.clip.waitArrive, cam:[+T.cam.x.toFixed(2), +T.cam.z.toFixed(2)], path:T.path.length, spot:T.HANDS.spot && [T.HANDS.spot.x, T.HANDS.spot.z], step:T.pend.step, fig:!!T.HANDS.fig, room:T.roomAt(T.cam.x, T.cam.z).id }; }"
        await page.evaluate("() => window.__test.openStation('pendulum')"); print(await page.evaluate(S, [3]))
        await page.evaluate("() => { const b = [...document.querySelectorAll('#stBtns button')].find((x) => x.textContent.trim() === 'Start'); b.click(); }"); print('start', await page.evaluate(S, [3]))
        r = await page.evaluate("() => { const b = [...document.querySelectorAll('#stBtns button')].find((x) => x.textContent.trim() === 'Pull back and release'); if (!b) return 'missing'; if (b.disabled) return 'disabled'; b.click(); return 'ok'; }"); print('click', r)
        for k in range(5): print(k, await page.evaluate(S, [2]))
        print(errs(logs))
        await b.close()
asyncio.run(run())
