"""Phone at High: memory, draw calls, frame cost, captions, tap a figure. Usage: CAMPUS_GFX=high python3 waxmobile.py"""
import asyncio, os, sys, time, json
from harness import *
async def run():
    async with async_playwright() as p:
        t0 = time.time()
        b, page, logs = await open_page(p, 'mobile', True)
        print('boot', round(time.time() - t0, 1), 's', flush=True)
        page.set_default_timeout(900000)
        await page.tap('#bEnter'); await page.wait_for_timeout(500)
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
        info = await page.evaluate("""() => { const T = window.__test, r = T.renderer, m = r.info.memory;
          return { tier:T.GFX.tier, eased:!!T.GFX.eased, dpr:+r.getPixelRatio().toFixed(2), lean:T.LEAN_CANVAS, freed:T.CANVAS_FREE.n, freedMB:+T.CANVAS_FREE.mb.toFixed(0), gpuTexMB:+T.CANVAS_FREE.gpu.toFixed(0), textures:m.textures, geometries:m.geometries, programs:(r.info.programs || []).length, figs:T.WAX.figs.length }; }""")
        print('mem', json.dumps(info), flush=True)
        async def go(v):
            await page.evaluate("(v) => { const T = window.__test; T.goView(v); T.frameOnce(); }", v)
        async def cost(label, n=3):
            ms = []
            for _ in range(n):
                ms.append(await page.evaluate("() => { const T = window.__test, r = T.renderer; r.info.autoReset = false; r.info.reset(); T.waxFrame(1 / 30); const t = T.timeRender()[0]; window.__calls = [r.info.render.calls, r.info.render.triangles, (r.info.programs || []).length]; r.info.autoReset = true; return t; }"))
            calls = await page.evaluate("() => window.__calls")
            print('cost', label, 'ms', [round(x) for x in ms], 'calls/tris/programs', calls, flush=True)
        async def snap(name):
            await page.screenshot(path=os.path.join(OUT, 'waxm-' + name + '.jpg'), type='jpeg', quality=82)
        await go({'x': 0, 'z': -33.5, 'yaw': 0, 'pitch': 0.04}); await cost('g3-door'); await snap('door')
        await go({'x': 0, 'z': -46.0, 'yaw': 0, 'pitch': 0.02}); await cost('hall-front'); await snap('hall')
        for i in [0, 7, 10]:
            v = await page.evaluate("(i) => window.__test.waxView(window.__test.WAX_SCENES[i])", i)
            await go(v)
            await page.evaluate("(i) => { const T = window.__test, S = T.WAX_SCENES[i].stage; S.t = 0; S.live = false; for (let j = 0; j < 100; j++) T.waxFrame(1 / 12); }", i)
            await cost('scene%d' % (i + 1)); await page.evaluate("() => window.__test.frameOnce()"); await page.wait_for_timeout(300)
            cap = await page.evaluate("() => { const e = document.getElementById('waxCap'); const r = e.getBoundingClientRect(); return { on:e.classList.contains('on'), hidden:e.hidden, top:Math.round(r.top), h:Math.round(r.height), text:e.textContent.slice(0, 80) }; }")
            print('caption', cap, flush=True)
            await snap('s%02d' % (i + 1))
        # Tap the nearest figure: the card for that scene should open
        pt = await page.evaluate("""() => { const T = window.__test, sc = T.WAX_SCENES[10], f = sc.stage.figs[0], v = f.pick.position.clone(); f.pick.updateWorldMatrix(true, false); v.setFromMatrixPosition(f.pick.matrixWorld); v.project(T.camera);
          return { x:(v.x + 1) / 2 * innerWidth, y:(1 - v.y) / 2 * innerHeight, z:v.z, title:sc.item.title }; }""")
        print('tap figure at', {k: round(v, 1) if isinstance(v, float) else v for k, v in pt.items()}, flush=True)
        await page.touchscreen.tap(pt['x'], pt['y']); await page.wait_for_timeout(600)
        st = await page.evaluate("() => ({ open: !document.querySelector('#viewer').hidden, title: document.querySelector('#vTitle').textContent, hall: document.querySelector('#vGallery').textContent })")
        print('viewer after tap', st, flush=True)
        await snap('card')
        prog = await page.evaluate("() => ({ wax:[...window.__test.prog.wax], badges:[...window.__test.prog.badges] })")
        print('progress', prog, flush=True)
        print(errs(logs))
        await b.close()
asyncio.run(run())
