import asyncio, os, sys, json
from harness import *
async def main():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        await page.click('#bEnter'); await page.wait_for_timeout(500)
        for name, v in [('hall', {'x': 23, 'z': -3, 'yaw': -1.5708, 'pitch': 0}), ('lab', {'x': 29, 'z': -7, 'yaw': 0, 'pitch': 0}), ('blueprint', {'x': 18, 'z': 1, 'yaw': 3.14, 'pitch': 0}), ('world', {'x': 29, 'z': 0.5, 'yaw': 3.14, 'pitch': 0}), ('studio', {'x': 19, 'z': -6.4, 'yaw': 0, 'pitch': 0}), ('lobby', {'x': 0, 'z': -2, 'yaw': 0, 'pitch': 0})]:
            await page.evaluate("(v) => window.__test.goView(v)", v)
            await page.wait_for_timeout(4000)
            r = await page.evaluate("""() => { const T = window.__test, d = 1 / 60, o = { raf:T.raf }; for (const k of ['trackHeads', 'spinTokens', 'stationFrame', 'yardAmbient', 'yardPhysics', 'updateLights', 'playerFrame', 'paintFrame']) { try { o[k] = !!T[k](d); } catch (e) { o[k] = 'err ' + e.message; } } try { o.update = !!T.update(d); } catch (e) { o.update = 'err ' + e.message; } o.gfxLive = T.gfxLive(); o.envFade = T.GFX.envFade; return o; }""")
            busy = {k: v for k, v in r.items() if v not in (False, 0, 1)}
            print(name.ljust(9), 'raf', r['raf'], 'busy:', busy, flush=True)
        print(errs(logs))
        await b.close()
asyncio.run(main())
