import asyncio, os, sys, json, time
from harness import *
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        page.set_default_timeout(60000)
        page.on('framenavigated', lambda f: print('NAVIGATED', f.url, flush=True))
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        async def ev(expr, t=25):
            try: return await asyncio.wait_for(page.evaluate(expr), t)
            except asyncio.TimeoutError: print('EVAL TIMEOUT', flush=True); raise
        async def click(label):
            r = await ev("(() => { const label = " + json.dumps(label) + "; const b = [...document.querySelectorAll('#stBtns button')].find((x) => x.textContent.trim() === label); if (!b) return 'missing'; if (b.disabled) return 'disabled'; b.click(); return 'ok'; })()")
            return r
        if os.environ.get('NOBODY'): await ev("() => { window.__noBody = true; }")
        await ev("() => window.__test.openStation('titration')"); await page.wait_for_timeout(500)
        await click('Start'); await page.wait_for_timeout(300)
        await click('Set it up')
        for k in range(100):
            if await ev("() => { const T = window.__test; return T.titr.set && !T.handsBusy(); }"): break
            await page.wait_for_timeout(250)
        await click('Next: titrate'); await page.wait_for_timeout(400)
        t0 = time.time()
        for i in range(60):
            lab = '+1 mL' if i < 8 else '+0.1 mL' if i < 40 else '+1 drop'
            r = await click(lab)
            ok = False
            for k in range(60):
                st = await ev("() => { const T = window.__test; const gl = T.renderer.getContext(); const sz = T.renderer.getSize(new T.camera.position.constructor().constructor === Object ? null : new (T.camera.position.constructor.bind(null))() || {x:0,y:0}); return { added:T.titr.added, busy:!!(T.HANDS.clip && T.HANDS.clip.T < 1e5), lost:gl.isContextLost(), raf:T.raf, frame:T.renderer.info.render.frame, tri:T.renderer.info.render.triangles, calls:T.renderer.info.render.calls, scale:T.GFX.scale, kids:T.scene.children.length, canv:document.querySelectorAll('canvas').length, heap:performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1e6) : -1, geo:T.renderer.info.memory.geometries, tex:T.renderer.info.memory.textures, prog:T.renderer.info.programs.length }; }")
                if not st['busy']: ok = True; break
                await page.wait_for_timeout(250)
            who = await ev("() => { const T = window.__test, d = 1 / 60, o = {}; for (const k of ['trackHeads', 'spinTokens', 'stationFrame', 'yardAmbient', 'updateLights', 'playerFrame', 'handsFrame', 'waxFrame', 'yardPhysics']) { try { o[k] = !!T[k](d); } catch (e) { o[k] = 'err ' + e.message; } } for (const k in T.STATIONS){ try { o['st_' + k] = !!(T.STATIONS[k].tick && T.STATIONS[k].tick(d)); } catch (e) { o['st_' + k] = 'err ' + e.message; } } o.dropT = T.TT.dropT; o.flash = T.titr.flash; o.gfxLive = T.gfxLive(); o.path = T.path.length; o.raf = T.raf; o.chain = T.chain; o.face = T.faceYaw; o.fpitch = T.facePitch; return o; }")
            print(i, lab, r, round(time.time() - t0, 1), st['frame'], {k: v for k, v in who.items() if v}, flush=True)
            if not ok or st['lost']: break
        print(errs(logs))
        await b.close()
asyncio.run(run())
