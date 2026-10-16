import asyncio, os, sys, json
from harness import *
SCAN = """() => { const T = window.__test, bad = []; let n = 0; T.scene.updateMatrixWorld(true); T.scene.traverse((o) => { n++; const e = o.matrixWorld.elements; for (let i = 0; i < 16; i++) if (!Number.isFinite(e[i])){ bad.push((o.name || o.type) + ' ' + (o.parent && (o.parent.name || o.parent.type))); return; } const s = o.scale; if (Math.abs(s.x) > 1e4 || Math.abs(s.y) > 1e4 || Math.abs(s.z) > 1e4) bad.push('bigscale ' + (o.name || o.type)); if (o.geometry && o.geometry.boundingSphere && !Number.isFinite(o.geometry.boundingSphere.radius)) bad.push('nanbs ' + (o.name || o.type)); }); return { n, bad:bad.slice(0, 10), info:T.renderer.info.render }; }"""
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        page.set_default_timeout(60000)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        if os.environ.get('NOHANDS'): await page.evaluate("() => { window.__noHands = true; }")
        if os.environ.get('HIDEFIRST'): await page.evaluate("() => { window.__noBody = true; }")
        async def ev(expr, t=20):
            return await asyncio.wait_for(page.evaluate(expr), t)
        async def click(label):
            r = await ev("""(label) => { const b = [...document.querySelectorAll('#stBtns button')].find((x) => x.textContent.trim() === label); if (!b) return 'missing ' + [...document.querySelectorAll('#stBtns button')].map((x) => x.textContent.trim() + (x.disabled ? '(off)' : '')).join(','); if (b.disabled) return 'disabled'; b.click(); return 'ok'; }""".replace('(label)', '((label) => ', 1) + ')(' + json.dumps(label) + ')' if False else "(() => { const label = " + json.dumps(label) + "; const b = [...document.querySelectorAll('#stBtns button')].find((x) => x.textContent.trim() === label); if (!b) return 'missing ' + [...document.querySelectorAll('#stBtns button')].map((x) => x.textContent.trim() + (x.disabled ? '(off)' : '')).join(','); if (b.disabled) return 'disabled'; b.click(); return 'ok'; })()")
            print(label, '->', r, flush=True)
        async def until(expr, ms=40000):
            for k in range(ms // 250):
                ok = await ev("() => { const T = window.__test; return " + expr + "; }")
                if ok: return True
                await page.wait_for_timeout(250)
            print('TIMEOUT waiting', expr, flush=True); return False
        async def scan(tag):
            r = await ev(SCAN); print('scan', tag, r, flush=True)
        await ev("() => window.__test.openStation('sieve')"); await page.wait_for_timeout(500)
        await click('Start the test'); await page.wait_for_timeout(300)
        await click('Pour it through the splitter'); await until('T.psd.splitting >= 1'); await scan('split1')
        await click('Split it again'); await until('T.psd.splitting >= 2'); await scan('split2')
        await click('Next: dry and weigh'); await page.wait_for_timeout(300)
        await click('Dry it in the oven'); await until('T.psd.dried'); await scan('dry')
        await click('Tare the balance'); await until('T.psd.tared'); await scan('tare')
        await click('Pour the sample into the dish'); await until('T.psd.weighed'); await scan('weigh')
        await click('Next: stack the sieves'); await page.wait_for_timeout(300)
        await click('Stack the sieves'); await until('T.psd.stacked >= 12'); await scan('stack')
        await click('Next: shake'); await page.wait_for_timeout(300)
        await click('Pour the sample onto the top sieve'); await until('T.psd.poured'); await scan('pour')
        await click('Put the cover on and clamp it'); await until('T.psd.covered'); await scan('cover')
        await click('Press START'); await until('T.psd.shaken && !T.SV.run'); await scan('shake')
        await click('Next: weigh each sieve'); await page.wait_for_timeout(300)
        await click('Weigh the next sieve'); await until('T.psd.weighedN >= 1 && !T.handsBusy()'); await scan('w1')
        await click('Weigh the rest'); await until('T.psd.weighedN >= 12 && !T.handsBusy()'); await scan('wrest')
        await click('See the results'); await page.wait_for_timeout(500); await scan('results')
        print('hands', await ev("() => { const T = window.__test, H = T.HANDS, f = H.fig, m = f.mesh; const fin = (v) => Number.isFinite(v); const flat = (o) => { const out = {}; for (const k in o){ const v = o[k]; if (typeof v === 'number') out[k] = fin(v) ? +v.toFixed(3) : 'BAD:' + v; else if (v && v.isVector3) out[k] = [v.x, v.y, v.z].map((x) => fin(x) ? +x.toFixed(3) : 'BAD'); } return out; }; return { H:flat(H), hL:flat(H.h.L), hR:flat(H.h.R), meshPos:m.position.toArray(), meshScale:m.scale.toArray(), bs:m.boundingSphere && [m.boundingSphere.radius, m.boundingSphere.center.toArray()], fc:m.frustumCulled, skelN:f.skel.bones.length, spineKids:f.all[5].children.length, rootKids:f.root.children.length, camPos:T.camera.position.toArray(), near:T.camera.near, proj:T.camera.projectionMatrix.elements.every(fin), view:T.camera.view && [T.camera.view.fullWidth, T.camera.view.offsetX, T.camera.view.width] }; }"), flush=True)
        print('bones', await ev("() => { const T = window.__test, f = T.HANDS.fig, bad = []; f.root.updateMatrixWorld(true); f.all.forEach((b, i) => { const e = b.matrixWorld.elements; for (let k = 0; k < 16; k++) if (!Number.isFinite(e[k])){ bad.push(b.name); break; } }); const bm = f.skel.boneMatrices; let nan = 0; for (let i = 0; i < bm.length; i++) if (!Number.isFinite(bm[i])) nan++; return { bad, nan, pose:[...f.pose].some((v) => !Number.isFinite(v)), lean:T.HANDS.lean, crouch:T.HANDS.crouch, camx:[T.CAMX.x, T.CAMX.y, T.CAMX.z], root:f.root.position.toArray(), h:['L','R'].map((s) => [T.HANDS.h[s].w, T.HANDS.h[s].curl, T.HANDS.h[s].point]) }; }"), flush=True)
        if os.environ.get('HIDEBODY'): await ev("() => { window.__noBody = true; }"); await page.wait_for_timeout(300)
        if os.environ.get('HIDEFIRST'): await ev("() => { window.__noBody = false; }"); await page.wait_for_timeout(300)
        await ev("() => window.__test.openStation('titration')"); await page.wait_for_timeout(500); await scan('titr-open')
        await click('Start'); await page.wait_for_timeout(300)
        await click('Set it up'); await until('T.titr.set && !T.handsBusy()'); await scan('setup')
        await click('Next: titrate'); await page.wait_for_timeout(400); await scan('titrate')
        await click('+1 mL'); await until('T.titr.added >= 1 && !(T.HANDS.clip && T.HANDS.clip.T < 1e5)'); await scan('add1')
        print(errs(logs))
        await b.close()
asyncio.run(run())
