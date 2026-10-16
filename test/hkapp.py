"""Realistic people in the app: staff close-ups and wax scenes. Usage: CAMPUS_GFX=high python3 hkapp.py [desktop|mobile] [staff,scenes] [scene numbers]"""
import asyncio, os, sys, time
from harness import *
T_AT = float(os.environ.get('WAX_T', '9'))
async def run(mode, which, only):
    async with async_playwright() as p:
        t0 = time.time()
        b, page, logs = await open_page(p, mode, True)
        print('boot', round(time.time() - t0, 1), 's', flush=True)
        page.set_default_timeout(600000)
        await (page.click('#bEnter') if mode == 'desktop' else page.tap('#bEnter'))
        await page.wait_for_timeout(400)
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
        await page.evaluate("() => document.head.insertAdjacentHTML('beforeend', '<style>.hud,#plan,#hint,#tag,#toast,#askBtn,#award,#fade{display:none!important}</style>')")
        async def go(v, wait=200):
            await page.evaluate("(v) => { const T = window.__test; T.goView(v); for (let i = 0; i < 400 && T.path.length; i++) T.update(1 / 30); T.frameOnce(); T.frameOnce(); }", v)
            await page.wait_for_timeout(wait)
        async def snap(name):
            await page.screenshot(path=os.path.join(OUT, 'hk-' + mode[0] + '-' + name + '.jpg'), type='jpeg', quality=88)
            print('shot', name, flush=True)
        async def settle():
            await page.evaluate("async () => { const T = window.__test; await Promise.all([...T.HK.assets.values()].map((p) => p.catch(() => null))); }")
            for _ in range(3):
                await page.evaluate("() => window.__test.frameOnce()"); await page.wait_for_timeout(150)
        if 'staff' in which:
            await settle()
            for sid, v in [('margaret', {'x': 0.2, 'z': -2.6, 'yaw': 0.12, 'pitch': 0.02}), ('rosa', {'x': -17.2, 'z': -5.6, 'yaw': 0.0, 'pitch': 0.0}),
                           ('hale', {'x': 18.4, 'z': -8.2, 'yaw': 0.42, 'pitch': 0.0}), ('rae', {'x': 44.6, 'z': -0.6, 'yaw': -1.25, 'pitch': 0.0})]:
                await go(v, 300)
                await page.evaluate("() => { const T = window.__test; for (let i = 0; i < 40; i++) T.trackHeads(1 / 30); T.frameOnce(); }")
                await page.wait_for_timeout(300)
                await snap('staff-' + sid)
        if 'scenes' in which:
            await page.evaluate("() => window.__test.hkWant('wax')")
            await settle()
            info = await page.evaluate("() => { const T = window.__test; return { assets:T.HK.assets.size, figs:T.HK.figs.length, meshes:T.HK.figs.filter((f) => f.mesh).length } }")
            print(info, flush=True)
            for i in (only or range(12)):
                v = await page.evaluate("(i) => window.__test.waxView(window.__test.WAX_SCENES[i])", i)
                await go(v, 300)
                await page.evaluate("([i, tt]) => { const T = window.__test, S = T.WAX_SCENES[i].stage, k = matchMedia('(prefers-reduced-motion: reduce)').matches ? 0.6 : 1; S.t = 0; S.live = false; const n = Math.round(tt / k * 12); for (let j = 0; j < n; j++) T.waxFrame(1 / 12); }", [i, T_AT])
                await page.evaluate("() => window.__test.frameOnce()")
                await page.wait_for_timeout(400)
                await snap('s%02d' % (i + 1))
        print(errs(logs))
        await b.close()
mode = sys.argv[1] if len(sys.argv) > 1 else 'desktop'
which = sys.argv[2] if len(sys.argv) > 2 else 'staff,scenes'
only = [int(x) - 1 for x in sys.argv[3].split(',')] if len(sys.argv) > 3 else None
asyncio.run(run(mode, which, only))
