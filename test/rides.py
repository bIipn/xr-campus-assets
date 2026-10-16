import asyncio, sys, math
from harness import *

async def hold(page, js, wait=500):
    await page.evaluate(js); await page.evaluate("window.__test.ride.phase = 'test'; window.dispatchEvent(new Event('resize'));"); await page.wait_for_timeout(wait)

async def run(mode, which):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, mode, True)
        page.set_default_timeout(120000)
        await page.click('#bEnter') if mode == 'desktop' else await page.tap('#bEnter')
        await page.wait_for_timeout(300)
        stats = await page.evaluate("() => { const C = window.__test.COASTER; return { L:C.L, n:C.n, crest:C.iCrest * C.ds, loopTop:C.iLoopTop * C.ds, stats:C.stats, vmax:Math.max(...C.V) }; }")
        print('coaster', stats)
        m = mode[0]
        if not which or 'coaster' in which:
            await page.evaluate("window.__test.openRide('coaster')"); await page.wait_for_timeout(200)
            await shot(page, m + '-r00-card')
            await page.click('#rcGo') if mode == 'desktop' else await page.tap('#rcGo')
            await page.wait_for_timeout(500)
            await shot(page, m + '-r01-board')
            L = stats['L']; crest = stats['crest']; lt = stats['loopTop']
            for name, s in [('r02-lift', crest * 0.55), ('r03-crest', crest + 1.0), ('r04-drop', crest + 14), ('r05-loop', lt), ('r06-hill', lt + 22), ('r07-turn', L - 18)]:
                await hold(page, f"window.__test.ride.s = {s}; window.__test.ride.v = 10;")
                await shot(page, m + '-' + name)
            await page.evaluate("window.__test.ride.look.yaw = 1.2; window.__test.ride.look.at = performance.now() + 1e9;")
            await hold(page, f"window.__test.ride.s = {crest - 0.5};")
            await shot(page, m + '-r08-look')
            await page.evaluate("window.__test.ride.look.yaw = 0; window.__test.ride.look.at = 0;")
            print('token coaster?', await page.evaluate("window.__test.prog.tokens.has('t-coaster')"))
            await page.evaluate("window.__test.endRide(true)"); await page.wait_for_timeout(400)
            await shot(page, m + '-r09-after')
        if not which or 'drop' in which:
            await page.evaluate("window.__test.startRide('drop', false)"); await page.wait_for_timeout(300)
            await hold(page, "window.__test.ride.y = 31;")
            await shot(page, m + '-r10-drop-top')
            await page.evaluate("window.__test.ride.look.yaw = -1.3; window.__test.ride.look.pitch = -0.5; window.__test.ride.look.at = performance.now() + 1e9;")
            await hold(page, "window.__test.ride.y = 31;")
            await shot(page, m + '-r11-drop-look')
            await page.evaluate("window.__test.ride.look.yaw = 0; window.__test.ride.look.pitch = 0;")
            await page.evaluate("window.__test.endRide(true)"); await page.wait_for_timeout(400)
        if not which or 'dive' in which:
            await page.evaluate("window.__test.startRide('dive', false)"); await page.wait_for_timeout(300)
            for name, u in [('r12-dive0', 0.04), ('r13-reef', 0.17), ('r14-turtle', 0.3), ('r15-kelp', 0.43), ('r16-school', 0.57), ('r17-shark', 0.66), ('r18-manta', 0.78), ('r19-jelly', 0.88)]:
                await hold(page, f"window.__test.ride.u = {u}; window.__test.ride.phase = 'run'; window.__test.ride.paused = true;", 900)
                await shot(page, m + '-' + name)
            await page.evaluate("window.__test.endRide(true)"); await page.wait_for_timeout(400)
        print('badges', await page.evaluate("[...window.__test.prog.badges]"), 'tokens', await page.evaluate("[...window.__test.prog.tokens]"))
        print(mode, errs(logs))
        await b.close()

which = sys.argv[2:] if len(sys.argv) > 2 else None
asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else 'desktop', which))
