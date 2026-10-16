import asyncio, os, sys, json
from harness import *
from soccer import SETUP
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'small', False)
        page.set_default_timeout(900000)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
        await page.evaluate("() => document.head.insertAdjacentHTML('beforeend', '<style>.hud,#plan,#hint,#tag,#askBtn,#award,#fade,#toast{display:none!important}</style>')")
        print('setup', await page.evaluate(SETUP), flush=True)
        info = await page.evaluate("""() => { const T = window.__test, f = T.KEEP.fig, v = new f.root.position.constructor(); f.all[f.R ? 0 : 0]; const out = {};
          for (const n of ['L_Hand', 'R_Hand', 'Head']){ const b = f.all.find((x) => x.name === 'Bip01_' + n); b.getWorldPosition(v); out[n] = v.toArray().map((x) => +x.toFixed(3)); }
          const kids = []; f.all.find((x) => x.name === 'Bip01_R_Hand').children.forEach((c) => kids.push([c.type, c.isMesh ? c.geometry.type : '', c.position.toArray().map((x) => +x.toFixed(3)), c.visible])); out.kids = kids; return out; }""")
        print(json.dumps(info))
        h = info['R_Hand']
        for k, (pp, tt) in enumerate([([h[0] - 1.6, h[1] + 0.3, h[2] + 1.2], [h[0] + 0.3, h[1] - 0.1, h[2] + 0.27]), ([h[0] - 0.55, h[1] + 0.15, h[2] - 0.3], [h[0], h[1], h[2]]), ([h[0] - 0.55, h[1] + 0.15, h[2] - 0.3], [h[0], h[1], h[2]])]):
            r = await page.evaluate("(a) => { const T = window.__test; T.renderFrom(a[0], a[1], 40); return T.camera.position.toArray().map((x) => +x.toFixed(2)); }", [pp, tt])
            await page.screenshot(path=os.path.join(OUT, 'glove%d.jpg' % k), type='jpeg', quality=88)
        print(errs(logs)); await b.close()
asyncio.run(run())
