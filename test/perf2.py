"""Draw calls and triangles per frame at key spots (all passes counted). Usage: CAMPUS_GFX=high python3 perf2.py"""
import asyncio, os, sys, json
from harness import *

SPOTS = [
  ('lobby', {'x': 0, 'z': -2.2, 'yaw': 0, 'pitch': 0.02}),
  ('hall-east', {'x': 13.2, 'z': -3, 'yaw': -1.5708, 'pitch': 0.05}),
  ('hall-west', {'x': 32.5, 'z': -3, 'yaw': 1.5708, 'pitch': 0.05}),
  ('studio', {'x': 19, 'z': -6.4, 'yaw': 0, 'pitch': 0.06}),
  ('lab', {'x': 29, 'z': -5.9, 'yaw': 0, 'pitch': -0.06}),
  ('lab-sieve', {'x': 32.15, 'z': -9.0, 'yaw': -1.5708, 'pitch': -0.24}),
  ('blueprint', {'x': 18.1, 'z': 0.2, 'yaw': 3.1416, 'pitch': 0.03}),
  ('world', {'x': 29, 'z': 0.2, 'yaw': 3.1416, 'pitch': -0.1}),
  ('yard', {'x': 38.6, 'z': -3, 'yaw': -1.5708, 'pitch': 0.06}),
]

async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        await page.click('#bEnter'); await page.wait_for_timeout(400)
        out = {}
        for name, v in SPOTS:
            await page.evaluate("(v) => window.__test.goView(v)", v)
            await page.wait_for_timeout(900)
            r = await page.evaluate("""() => { const T = window.__test, R = T.renderer; T.sim(1 / 60); T.updateLights(); R.info.autoReset = false; R.info.reset(); const t = T.timeRender(); const i = R.info.render; const res = { calls:i.calls, tris:i.triangles, ms:+t[0].toFixed(1), lamps:T.LAMPS.pool.filter(l => l.intensity > 0).length, school:T.WING.school.visible, museum:T.WING.museum.visible, lib:T.WING.lib.visible, outside:T.WING.outside.visible, play:T.WING.play.visible }; R.info.autoReset = true; return res; }""")
            out[name] = r
            print(name.ljust(10), json.dumps(r))
        mem = await page.evaluate("() => { const m = window.__test.renderer.info.memory; return { geometries:m.geometries, textures:m.textures, programs:window.__test.renderer.info.programs.length }; }")
        tex = await page.evaluate("""() => { const seen = new Set(), list = []; window.__test.scene.traverse((o) => { const ms = o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : []; for (const m of ms) for (const k of ['map', 'emissiveMap', 'normalMap', 'roughnessMap', 'alphaMap']) { const t = m[k]; if (t && t.image && !seen.has(t.image)) { seen.add(t.image); list.push([t.image.width || 0, t.image.height || 0, k]); } } }); const mb = list.reduce((s, [w, h]) => s + w * h * 4 * 1.33, 0) / 1e6; list.sort((a, b) => b[0] * b[1] - a[0] * a[1]); return { count:list.length, mb:+mb.toFixed(1), top:list.slice(0, 12).map((x) => x[0] + 'x' + x[1] + ' ' + x[2]) }; }""")
        print('textures', tex)
        print('memory', mem)
        print(errs(logs))
        await b.close()

asyncio.run(run())
