"""Phones free canvases after upload: make sure nothing went blank. Usage: CAMPUS_GFX=medium python3 leancheck.py [mobile|desktop]"""
import asyncio, os, sys, json
from harness import *

VIEWS = [
  ('lobby', {'x': 0, 'z': -2.2, 'yaw': 0, 'pitch': 0.02}),
  ('gallery', {'x': 0, 'z': -14, 'yaw': 0, 'pitch': 0.05}),
  ('library', {'x': -24, 'z': -3, 'yaw': 1.5708, 'pitch': 0.05}),
  ('hall', {'x': 32.5, 'z': -3, 'yaw': 1.5708, 'pitch': 0.05}),
  ('studio', {'x': 19, 'z': -6.4, 'yaw': 0, 'pitch': 0.06}),
  ('lab', {'x': 29, 'z': -5.9, 'yaw': 0.35, 'pitch': -0.1}),
  ('blueprint', {'x': 21.4, 'z': 0.6, 'yaw': 2.45, 'pitch': 0.02}),
  ('world', {'x': 29, 'z': 0.35, 'yaw': 3.1416, 'pitch': -0.2}),
  ('yard', {'x': 38.6, 'z': -3, 'yaw': -1.5708, 'pitch': 0.06}),
]

async def run(mode):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, mode, True)
        page.set_default_timeout(600000)
        await (page.click('#bEnter') if mode == 'desktop' else page.tap('#bEnter'))
        await page.wait_for_timeout(600)
        info = await page.evaluate("""() => { const T = window.__test; let std = 0, nrm = 0, blank = 0; const seen = new Set();
          T.scene.traverse((o) => { const ms = o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : []; for (const m of ms){ if (seen.has(m)) continue; seen.add(m); if (m.isMeshStandardMaterial){ std++; if (m.normalMap) nrm++; } } });
          return { lean:T.LEAN_CANVAS, freed:T.CANVAS_FREE.n, freedMB:+T.CANVAS_FREE.mb.toFixed(1), std, nrm }; }""")
        print('materials', json.dumps(info), flush=True)
        await page.add_style_tag(content='.hud,#plan,#hint,#tag,#toast,#askBtn,#award,#fade{display:none!important}')
        for name, v in VIEWS:
            await page.evaluate("(v) => window.__test.goView(v)", v)
            await page.wait_for_timeout(1300)
            await page.screenshot(path=os.path.join(OUT, 'lean-' + mode[0] + '-' + name + '.jpg'), type='jpeg', quality=80)
        # The exhibit viewer redraws art whose canvas was freed
        r = await page.evaluate("""() => { const T = window.__test, it = T.ITEMS[0]; T.openItem(it); const c = document.querySelector('#vArt') || document.querySelector('canvas.vart'); if (!c) return 'no viewer canvas';
          const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let ink = 0; for (let i = 0; i < d.length; i += 4 * 97) if (d[i + 3] > 0) ink++;
          return { w:c.width, h:c.height, inked:ink, released:!!(T.ART[it.id] && T.ART[it.id].__released) }; }""")
        print('viewer', r, flush=True)
        await page.wait_for_timeout(600)
        await page.screenshot(path=os.path.join(OUT, 'lean-' + mode[0] + '-viewer.jpg'), type='jpeg', quality=80)
        await page.keyboard.press('Escape'); await page.wait_for_timeout(300)
        # Tier switches must not re-upload freed canvases
        for t in ['low', 'high', 'medium']:
            await page.evaluate("(t) => window.__test.gfxApplyTier(t)", t)
            await page.evaluate("(v) => window.__test.goView(v)", VIEWS[3][1])
            await page.wait_for_timeout(1200)
        await page.screenshot(path=os.path.join(OUT, 'lean-' + mode[0] + '-after-tiers.jpg'), type='jpeg', quality=80)
        print(errs(logs))
        await b.close()

asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else 'mobile'))
