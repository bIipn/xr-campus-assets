import asyncio, os, sys, json
from harness import *
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        page.set_default_timeout(60000)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        await page.evaluate("() => window.__test.openStation('titration')"); await page.wait_for_timeout(600)
        async def click(label):
            r = await page.evaluate("""(label) => { const b = [...document.querySelectorAll('#stBtns button')].find((x) => x.textContent.trim() === label); if (!b) return 'missing ' + [...document.querySelectorAll('#stBtns button')].map((x) => x.textContent.trim() + (x.disabled ? '(off)' : '')).join(','); if (b.disabled) return 'disabled'; b.click(); return 'ok'; }""", label)
            print(label, '->', r, flush=True)
        await click('Start'); await page.wait_for_timeout(300)
        await click('Set it up'); await page.wait_for_timeout(800)
        print(await page.evaluate("() => { const T = window.__test; return { set:T.titr.set, busy:T.handsBusy(), clipT:T.HANDS.clip && T.HANDS.clip.T, fig:!!T.HANDS.fig, mesh:!!(T.HANDS.fig && T.HANDS.fig.mesh), raf:T.raf, reduced:matchMedia('(prefers-reduced-motion: reduce)').matches }; }"))
        await click('Next: titrate'); await page.wait_for_timeout(500)
        print(await page.evaluate("() => { const T = window.__test; return { step:T.titr.step, busy:T.handsBusy(), clipT:T.HANDS.clip && T.HANDS.clip.T, raf:T.raf }; }"))
        await click('+1 mL'); await page.wait_for_timeout(600)
        print(await page.evaluate("() => { const T = window.__test; return { added:T.titr.added, busy:T.handsBusy(), clipT:T.HANDS.clip && T.HANDS.clip.T, t:T.HANDS.t, raf:T.raf, wait:T.HANDS.clip && T.HANDS.clip.waitArrive, cam:[T.cam.x, T.cam.z], spot:T.HANDS.spot }; }"))
        print('frameOnce:', await page.evaluate("() => { try { window.__test.frameOnce(); return 'ok'; } catch (e) { return 'ERR ' + e.message + ' | ' + (e.stack || '').split('\\n').slice(0, 4).join(' / '); } }"))
        await page.wait_for_timeout(1500)
        print(await page.evaluate("() => { const T = window.__test; return { added:T.titr.added, busy:T.handsBusy(), clipT:T.HANDS.clip && T.HANDS.clip.T, t:T.HANDS.t, raf:T.raf }; }"))
        print(errs(logs))
        await b.close()
asyncio.run(run())
