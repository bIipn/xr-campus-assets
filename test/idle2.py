import asyncio, os, sys, json
from harness import *
INIT = "window.__rafN = 0; const __r = window.requestAnimationFrame.bind(window); window.requestAnimationFrame = (cb) => { window.__rafN++; window.__rafLast = (new Error()).stack.split('\\n').slice(2, 4).join(' | '); return __r(cb); };"
async def main(reduced):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', reduced, init_script=INIT)
        await page.click('#bEnter'); await page.wait_for_timeout(500)
        for name, v in [('hall-west', {'x': 23, 'z': -3, 'yaw': 1.5708, 'pitch': 0}), ('lab', {'x': 29, 'z': -7, 'yaw': 0, 'pitch': 0}), ('blueprint', {'x': 18, 'z': 1, 'yaw': 3.14, 'pitch': 0}), ('world', {'x': 29, 'z': 0.5, 'yaw': 3.14, 'pitch': 0}), ('museum-g2', {'x': 0, 'z': -24, 'yaw': 0, 'pitch': 0}), ('library', {'x': -18, 'z': -3, 'yaw': 1.57, 'pitch': 0})]:
            await page.evaluate("(v) => { const T = window.__test; T.cam.x = v.x; T.cam.z = v.z; T.cam.yaw = v.yaw; T.cam.pitch = v.pitch; T.PLAYER.amp = 0; T.PLAYER.bob = 0; T.PLAYER.sp = 0; T.PLAYER.px = v.x; T.PLAYER.pz = v.z; T.goView(v); }", v)
            await page.wait_for_timeout(9000)
            n0 = await page.evaluate("() => window.__rafN")
            await page.wait_for_timeout(3000)
            n1, last = await page.evaluate("() => [window.__rafN, window.__rafLast]")
            busy = await page.evaluate("() => { const T = window.__test, d = 1 / 60, o = {}; for (const k of ['trackHeads', 'spinTokens', 'stationFrame', 'yardAmbient', 'yardPhysics', 'updateLights', 'playerFrame']) { try { if (T[k](d)) o[k] = true; } catch (e) { o[k] = 'err'; } } if (T.gfxLive()) o.gfxLive = true; return o; }")
            last = json.dumps(busy)
            print('reduced' if reduced else 'motion ', name.ljust(9), 'frames in 3s:', n1 - n0, '|', (last or '')[:160], flush=True)
        await b.close()
asyncio.run(main(sys.argv[1] == 'reduced'))
