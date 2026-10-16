"""Phone check: the Kick button appears by the ball, fills as you hold it, and shoots on release."""
import asyncio, os, sys, json
from harness import *
from soccer import SETUP
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'phone', False)
        page.set_default_timeout(900000)
        await page.tap('#bEnter'); await page.wait_for_timeout(400)
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
        print('setup', await page.evaluate(SETUP), flush=True)
        await page.evaluate("() => { const T = window.__test; T.stepFrame(1 / 60); T.stepFrame(1 / 60); }")
        print('kick button visible:', await page.evaluate("!document.getElementById('bKick').hidden"), '| told:', await page.evaluate("window.__test.SOC.told"))
        await page.screenshot(path=os.path.join(OUT, 'socm-1-near.jpg'), type='jpeg', quality=80)
        box = await page.evaluate("() => { const r = document.getElementById('bKick').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2, r.width]; }")
        print('button at', box)
        await page.evaluate("""(xy) => { const el = document.getElementById('bKick'); el.dispatchEvent(new PointerEvent('pointerdown', { bubbles:true, clientX:xy[0], clientY:xy[1], pointerId:7, pointerType:'touch', isPrimary:true })); }""", box)
        await page.evaluate("() => { const T = window.__test; T.KICK.t0 = performance.now() - 600; for (let i = 0; i < 2; i++) T.stepFrame(1 / 60); }")
        print('charging:', await page.evaluate("window.__test.KICK.st"), '| meter shown:', await page.evaluate("!document.getElementById('kickMeter').hidden"))
        await page.screenshot(path=os.path.join(OUT, 'socm-2-charge.jpg'), type='jpeg', quality=80)
        await page.evaluate("""(xy) => { const el = document.getElementById('bKick'); el.dispatchEvent(new PointerEvent('pointerup', { bubbles:true, clientX:xy[0], clientY:xy[1], pointerId:7, pointerType:'touch', isPrimary:true })); }""", box)
        st = await page.evaluate("() => window.__test.KICK.st")
        print('after release:', st)
        tc = await page.evaluate("() => window.__test.KICK.plan ? window.__test.KICK.plan.tc : -1")
        await page.evaluate("(n) => { const T = window.__test; T.sim((n - 1) / 60); T.stepFrame(1 / 60); }", max(1, round(tc * 60)))
        await page.screenshot(path=os.path.join(OUT, 'socm-3-strike.jpg'), type='jpeg', quality=80)
        await page.evaluate("() => { const T = window.__test; T.sim(0.3); T.stepFrame(1 / 60); }")
        await page.screenshot(path=os.path.join(OUT, 'socm-4-flight.jpg'), type='jpeg', quality=80)
        await page.evaluate("() => { const T = window.__test; T.sim(1.2); T.stepFrame(1 / 60); }")
        await page.screenshot(path=os.path.join(OUT, 'socm-5-result.jpg'), type='jpeg', quality=80)
        print('score', await page.evaluate("JSON.stringify(window.__test.SOC.score)"), '| toast:', await page.evaluate("window.__test.toastText()"))
        print(errs(logs)); await b.close()
asyncio.run(run())
