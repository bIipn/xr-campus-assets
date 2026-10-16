"""Soccer story shots: a kick seen from the side, a catch and roll-out, a goal and the fetch.
Usage: CAMPUS_GFX=medium python3 soccer2.py [kick|save|goal]"""
import asyncio, os, sys, json
from harness import *
WHICH = sys.argv[1] if len(sys.argv) > 1 else 'kick'
DEV = sys.argv[2] if len(sys.argv) > 2 else 'desktop'
from soccer import SETUP, AIM
PRE = 'soc2-' + WHICH + '-'
STEP = "(n) => { const T = window.__test; for (let i = 0; i < n; i++) T.stepFrame(1 / 60); const P = T.SOC.ball; return { k:T.KEEP.st, hold:T.KEEP.hold, ball:P.p1.toArray().map((v) => +v.toFixed(2)), score:T.SOC.score, cam:[+T.cam.x.toFixed(2), +T.cam.z.toFixed(2)] }; }"
async def shoot(page, aim, hold, catch=None):
    await page.evaluate(AIM, aim)
    await page.evaluate("(h) => { const T = window.__test; T.socChargeStart('key'); T.KICK.t0 = performance.now() - h * 1000; T.socChargeEnd(); T.KEEP.guess = 0; }", hold)
    if catch is not None:
        await page.evaluate("(c) => { window.__test.SOC.forceCatch = c; }", catch)
async def snap(page, name, cams):
    await page.screenshot(path=os.path.join(OUT, PRE + name + '.jpg'), type='jpeg', quality=85)
    for i, (p, t, f) in enumerate(cams):
        await page.evaluate("(a) => window.__test.renderFrom(a[0], a[1], a[2])", [p, t, f])
        await page.screenshot(path=os.path.join(OUT, PRE + name + '-c' + str(i) + '.jpg'), type='jpeg', quality=85)
    await page.evaluate("() => window.__test.stepFrame(0.0001)")
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, DEV, False)
        page.set_default_timeout(900000)
        await page.click('#bEnter'); await page.wait_for_timeout(400)
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
        await page.evaluate("() => document.head.insertAdjacentHTML('beforeend', '<style>.hud,#plan,#hint,#tag,#askBtn,#award,#fade{display:none!important}</style>')")
        print('setup', await page.evaluate(SETUP), flush=True)
        side = ([77.4, 1.25, 1.7], [79.0, 0.55, -2.0], 45)
        broad = ([81.0, 2.4, 5.2], [85.0, 0.9, -2.2], 46)
        if WHICH == 'kick':
            await shoot(page, [86.6, 0.6, -0.4], 0.62)
            for name, n in [('a', 6), ('b', 10), ('c', 6), ('d', 5), ('e', 5), ('f', 8), ('g', 14)]:
                st = await page.evaluate(STEP, n); print(name, json.dumps(st), flush=True)
                await snap(page, name, [side])
        elif WHICH == 'save':
            await shoot(page, [86.2, 1.1, -2.0], 0.42, catch=1)
            for name, n in [('a', 30), ('b', 14), ('c', 40), ('d', 50), ('e', 45), ('f', 40), ('g', 60)]:
                st = await page.evaluate(STEP, n); print(name, json.dumps(st), flush=True)
                await snap(page, name, [broad])
        else:
            await shoot(page, [86.6, 0.4, -4.1], 0.95)
            for name, n in [('a', 40), ('b', 50), ('c', 90), ('d', 90), ('e', 90), ('f', 90), ('g', 120)]:
                st = await page.evaluate(STEP, n); print(name, json.dumps(st), flush=True)
                await snap(page, name, [broad])
        print(errs(logs)); await b.close()
asyncio.run(run())
