"""Walk every hands-on station from start to finish. Usage: CAMPUS_GFX=low python3 stationtest.py [desktop|mobile] [shots]"""
import asyncio, os, sys, time, json
from harness import *

HIDE = '#hint,#tag,#toast,#award,#fade{display:none!important}'
SHOTS = 'shots' in sys.argv

# The page's own frame loop depends on the headless compositor, which stalls under swiftshader, so the test drives frames itself
async def steps(page, n, render=True):
    await page.evaluate("([n, r]) => { const T = window.__test; for (let i = 0; i < n; i++) T.simStep(1 / 30); if (r) T.frameOnce(); }", [n, render])

async def click(page, label, scope='#stBtns'):
    ok = await page.evaluate("""([label, scope]) => { const b = [...document.querySelectorAll(scope + ' button')].find((x) => x.textContent.trim() === label); if (!b) return 'missing: ' + label + ' | have: ' + [...document.querySelectorAll(scope + ' button')].map((x) => x.textContent.trim()).join(', '); if (b.disabled) return 'disabled: ' + label; b.click(); return 'ok'; }""", [label, scope])
    if ok != 'ok': print('  !!', ok)
    await steps(page, 4)
    return ok == 'ok'

async def settle(page, ms=400):
    await steps(page, max(2, ms // 33))

async def fresh(p, mode):
    b, page, logs = await open_page(p, mode, True)
    page.set_default_timeout(300000)
    await (page.click('#bEnter') if mode == 'desktop' else page.tap('#bEnter'))
    await page.wait_for_timeout(400)
    await page.add_style_tag(content=HIDE)
    await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
    await steps(page, 3)
    return b, page, logs

async def mem(page, tag):
    m = await page.evaluate("() => ({ js: performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1e6) : -1, geo: window.__test.renderer.info.memory.geometries, tex: window.__test.renderer.info.memory.textures, t: Math.round(performance.now() / 1000) })")
    print('  [' + tag + ']', m, flush=True)

async def snap(page, mode, name):
    if not SHOTS: return
    await page.wait_for_timeout(1300)
    await page.screenshot(path=os.path.join(OUT, 'st-' + mode[0] + '-' + name + '.jpg'), type='jpeg', quality=84)

async def title(page):
    return await page.evaluate("() => document.querySelector('#stTitle').textContent + ' | ' + document.querySelector('#stStep').textContent")

async def run(mode):
    async with async_playwright() as p:
        b, page, logs = await fresh(p, mode)
        await mem(page, 'start')
        # ---- Sieve (reduced motion: every hands clip finishes at once)
        async def until(expr, ms=90000):
            t0 = time.time()
            while True:
                if await asyncio.wait_for(page.evaluate('() => { const T = window.__test; return !!(' + expr + '); }'), 60): return
                if time.time() - t0 > ms / 1000: raise TimeoutError('until: ' + expr)
                await steps(page, 6, False)
        await page.evaluate("() => window.__test.openStation('sieve')"); await settle(page)
        await snap(page, mode, 'sieve0')
        await click(page, 'Start the test'); await settle(page, 300)
        await click(page, 'Pour it through the splitter'); await until('T.psd.splitting >= 1'); await settle(page, 300)
        await click(page, 'Split it again'); await until('T.psd.splitting >= 2'); await settle(page, 300)
        await snap(page, mode, 'sieve1')
        await click(page, 'Next: dry and weigh'); await settle(page, 300)
        await click(page, 'Dry it in the oven'); await until('T.psd.dried'); await settle(page, 300)
        await click(page, 'Tare the balance'); await until('T.psd.tared'); await settle(page, 300)
        await click(page, 'Pour the sample into the dish'); await until('T.psd.weighed'); await settle(page, 300)
        await snap(page, mode, 'sieve2')
        await click(page, 'Next: stack the sieves'); await settle(page, 300)
        await click(page, 'Stack the sieves'); await until('T.psd.stacked >= 12'); await settle(page, 300)
        await click(page, 'Next: shake'); await settle(page, 300)
        await click(page, 'Pour the sample onto the top sieve'); await until('T.psd.poured'); await settle(page, 300)
        await click(page, 'Put the cover on and clamp it'); await until('T.psd.covered'); await settle(page, 300)
        await click(page, 'Press START'); await until('T.psd.shaken && !T.SV.run'); await settle(page, 300)
        await snap(page, mode, 'sieve4')
        await click(page, 'Next: weigh each sieve'); await settle(page, 300)
        await click(page, 'Weigh the next sieve'); await until('T.psd.weighedN >= 1 && !T.handsBusy()'); await settle(page, 300)
        await click(page, 'Weigh the rest'); await until('T.psd.weighedN >= 12 && !T.handsBusy()'); await settle(page, 300)
        await snap(page, mode, 'sieve5')
        await click(page, 'See the results'); await settle(page)
        await mem(page, 'sieve')
        print('sieve:', await title(page))
        res = await page.evaluate("() => { const T = window.__test, C = T.psdCalc(T.psd.sample); return { mass:T.psd.sample.mass, total:C.total, lossPct:C.lossPct, d10:C.d10, d50:C.d50, d60:C.d60, d90:C.d90, gfn:C.gfn, rows:C.rows.map(r => [r.name, r.g, +r.pct.toFixed(2), +r.cum.toFixed(2), +r.pass.toFixed(2)]) }; }")
        print('  ', json.dumps(res)[:900])
        await snap(page, mode, 'sieve6')
        # ---- Titration
        await page.evaluate("() => window.__test.openStation('titration')"); await settle(page)
        await click(page, 'Start'); await settle(page, 300)
        await click(page, 'Set it up'); await until('T.titr.set && !T.handsBusy()'); await settle(page, 300)
        await click(page, 'Next: titrate'); await settle(page, 400)
        veq = await page.evaluate("() => { const T = window.__test; return T.titr.Ca * T.titr.Vacid / T.titr.Cb; }")
        n1 = int(veq) - 1
        async def add(label, target):
            await click(page, label)
            try: await until('Math.abs(T.titr.added - ' + str(target) + ') < 0.004 && !(T.HANDS.clip && T.HANDS.clip.T < 1e5)')
            except Exception as e:
                print('ADD FAILED', label, target, await page.evaluate("() => { const T = window.__test; return { added:T.titr.added, step:T.titr.step, clipT:T.HANDS.clip && T.HANDS.clip.T, t:T.HANDS.t, raf:T.raf, frame:T.renderer.info.render.frame, lost:T.renderer.getContext().isContextLost(), reduced:matchMedia('(prefers-reduced-motion: reduce)').matches, spot:T.HANDS.spot, cam:[T.cam.x, T.cam.z], path:T.path.length, wait:T.HANDS.clip && T.HANDS.clip.waitArrive }; }"), flush=True)
                raise
            await settle(page, 60)
        # Each hands-on addition renders a few hundred frames in reduced motion, and the headless GPU wedges after about twenty of them,
        # so the test adds the first milliliters directly and only works the last ones by hand
        added = 0.0
        for _ in range(n1): added = round(added + 1, 2); await add('+1 mL', added)
        await snap(page, mode, 'titr2a')
        for _ in range(40):
            if added >= veq - 0.25: break
            added = round(added + 0.1, 2); await add('+0.1 mL', added)
        for _ in range(12):
            if added > veq + 1e-6: break   # exactly at equivalence the pH is 7, so the indicator is still clear
            added = round(added + 0.05, 2); await add('+1 drop', added)
        await snap(page, mode, 'titr2b')
        await click(page, 'Record endpoint'); await settle(page)
        await mem(page, 'titration')
        print('titration:', await title(page), 'veq', round(veq, 3), await page.evaluate("() => window.__test.titr.ended"))
        await snap(page, mode, 'titr3')
        # ---- Pendulum
        await page.evaluate("() => window.__test.openStation('pendulum')"); await settle(page)
        await click(page, 'Start'); await settle(page, 300)
        for i, L in enumerate([0.5, 1.0, 1.5]):
            await page.evaluate("(L) => window.__test.pendSetLen(L)", L)
            await click(page, 'Pull back and release'); await until('T.pend.rows.length >= ' + str(i + 1) + ' && !T.pend.run'); await settle(page, 300)
        await mem(page, 'pendulum')
        print('pendulum:', await title(page), await page.evaluate("() => window.__test.pend.rows.map(r => [r.L, +r.T.toFixed(4), +r.g.toFixed(3)])"))
        await snap(page, mode, 'pend')
        # ---- Model bench: car
        await page.evaluate("() => window.__test.openStation('bench', { kit:'car' })"); await settle(page)
        await click(page, 'Start building'); await settle(page, 200)
        for i, lab in enumerate(['Set the chassis on the stand', 'Tape on the straws', 'Slide in the axles', 'Push on the wheels', 'Hook up the rubber band', 'Set on the body']):
            await click(page, lab); await until('T.benchSt.built >= ' + str(i + 1) + ' && !T.handsBusy()'); await settle(page, 200)
            await click(page, 'Next step'); await settle(page, 200)
        await snap(page, mode, 'bench-car6')
        await click(page, 'Wind it up and let go'); await until('T.benchSt.result && !T.BENCH.drive && !T.handsBusy()'); await settle(page, 300)
        await mem(page, 'car')
        print('bench car:', await title(page), await page.evaluate("() => window.__test.benchSt.result"))
        await snap(page, mode, 'bench-car7')
        # ---- Model bench: house
        await click(page, 'Switch kit'); await settle(page)
        await click(page, 'Start building'); await settle(page, 200)
        for i, lab in enumerate(['Set down the base', 'Glue in the columns', 'Add the beams and floor', 'Build the second story', 'Glue on the bracing']):
            await click(page, lab); await until('T.benchSt.built >= ' + str(i + 1) + ' && !T.handsBusy()'); await settle(page, 200)
            await click(page, 'Next step'); await settle(page, 200)
        await click(page, 'Shake the table'); await until('T.benchSt.result && !T.handsBusy()'); await settle(page, 300)
        await snap(page, mode, 'bench-house')
        await click(page, 'Remove bracing'); await settle(page, 300)
        await click(page, 'Shake it again'); await until('!T.handsBusy()'); await settle(page, 300)
        await mem(page, 'house')
        print('bench house:', await title(page), await page.evaluate("() => window.__test.benchSt.result"))
        await snap(page, mode, 'bench-house-unbraced')
        # ---- Diorama
        await page.evaluate("() => window.__test.openStation('diorama')"); await settle(page)
        names = []
        for i in range(8):
            await click(page, 'Add the next layer'); await settle(page, 250)
            names.append(await title(page))
            if i in (0, 1, 3, 5, 7): await snap(page, mode, 'dio%d' % (i + 2))
        await click(page, 'X-ray triangles'); await settle(page, 300)
        await snap(page, mode, 'dio-xray')
        await mem(page, 'diorama')
        print('diorama:', names)
        badges = await page.evaluate("() => [...window.__test.prog.badges]")
        print('badges:', badges)
        # idle check: after closing everything, the loop should stop
        await page.evaluate("() => { window.__test.closeStation(); window.__test.goView({ x:23, z:-3, yaw:-1.5708, pitch:0 }); }")
        await steps(page, 90)
        print('idle raf (0 = asleep):', await page.evaluate("() => window.__test.raf"))
        print('who is busy:', await page.evaluate("() => { const T = window.__test, d = 1 / 60, o = {}; for (const k of ['trackHeads', 'spinTokens', 'stationFrame', 'yardAmbient', 'updateLights', 'playerFrame']) { try { o[k] = !!T[k](d); } catch (e) { o[k] = 'err ' + e.message; } } o.gfxLive = T.gfxLive(); o.path = T.path.length; return o; }"))
        print(errs(logs))
        await b.close()

asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in ('desktop', 'mobile') else 'desktop'))
