"""Smoke test and stills for the four workshop rooms. Usage: CAMPUS_GFX=medium python3 rooms.py [desktop|mobile] [names...]"""
import asyncio, os, sys, time
from harness import *

HIDE = '.hud,#plan,#hint,#tag,#toast,#askBtn,#award,#fade{display:none!important}'

async def snap(page, name, mode):
    await page.wait_for_timeout(250)
    await page.screenshot(path=os.path.join(OUT, 'rm-' + mode[0] + '-' + name + '.jpg'), type='jpeg', quality=84)

async def go(page, v, wait=900):
    await page.evaluate("(v) => window.__test.goView(v)", v)
    await page.wait_for_timeout(wait)

async def run(mode, which):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, mode, True)
        page.set_default_timeout(300000)
        await (page.click('#bEnter') if mode == 'desktop' else page.tap('#bEnter'))
        await page.wait_for_timeout(500)
        await page.add_style_tag(content=HIDE)
        want = lambda n: not which or n in which
        t0 = time.time()
        if want('hall'):
            await go(page, {'x': 13.2, 'z': -3, 'yaw': -1.5708, 'pitch': 0.05}); await snap(page, 'hall', mode)
            await go(page, {'x': 32.5, 'z': -3, 'yaw': 1.5708, 'pitch': 0.05}); await snap(page, 'hall2', mode)
        if want('studio'):
            await page.evaluate("() => window.__test.startPaint()"); await page.wait_for_timeout(900)
            await snap(page, 'studio-bar', mode)
        if want('lab'):
            await page.evaluate("() => window.__test.stopPaint()")
            await go(page, {'x': 29, 'z': -5.9, 'yaw': 0, 'pitch': -0.06}); await snap(page, 'lab', mode)
            await go(page, {'x': 30.5, 'z': -6.2, 'yaw': -2.3, 'pitch': -0.12}); await snap(page, 'lab2', mode)
        if want('sieve'):
            await page.evaluate("() => window.__test.openStation('sieve')"); await page.wait_for_timeout(1200); await snap(page, 'sieve0', mode)
        if want('titration'):
            await page.evaluate("() => window.__test.openStation('titration')"); await page.wait_for_timeout(1200); await snap(page, 'titr0', mode)
        if want('pendulum'):
            await page.evaluate("() => window.__test.openStation('pendulum')"); await page.wait_for_timeout(1200); await snap(page, 'pend0', mode)
        if want('blueprint'):
            await page.evaluate("() => window.__test.closeStation()")
            await go(page, {'x': 18.1, 'z': 0.2, 'yaw': 3.1416, 'pitch': 0.03}); await snap(page, 'bplab', mode)
            await go(page, {'x': 21.5, 'z': 1.0, 'yaw': 2.4, 'pitch': 0.0}); await snap(page, 'bplab2', mode)
            for id in ['car', 'excavator', 'house', 'bridge', 'computer']:
                v = await page.evaluate("(id) => window.__test.bpViewFor(id)", id)
                await go(page, v, 700); await snap(page, 'board-' + id, mode)
            await page.evaluate("() => window.__test.openBp('car', null, { walk:false })"); await page.wait_for_timeout(400); await snap(page, 'bpview-car', mode)
            await page.evaluate("() => window.__test.openBp('excavator', 7, { walk:false })"); await page.wait_for_timeout(400); await snap(page, 'bpview-exc7', mode)
            await page.evaluate("() => window.__test.closeBp()")
        if want('bench'):
            await page.evaluate("() => window.__test.openStation('bench', { kit:'car' })"); await page.wait_for_timeout(1300); await snap(page, 'bench-car0', mode)
        if want('world'):
            await page.evaluate("() => window.__test.closeStation()")
            await go(page, {'x': 29, 'z': 0.2, 'yaw': 3.1416, 'pitch': -0.1}); await snap(page, 'world', mode)
            await go(page, {'x': 30.5, 'z': 3.3, 'yaw': 1.2, 'pitch': 0.0}); await snap(page, 'world2', mode)
            await page.evaluate("() => window.__test.openStation('diorama')"); await page.wait_for_timeout(1300); await snap(page, 'dio0', mode)
        print('time', round(time.time() - t0, 1), 's')
        print(errs(logs))
        await b.close()

which = sys.argv[2:] if len(sys.argv) > 2 else None
asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else 'desktop', which))
