import asyncio, os, sys, json
from harness import *
async def main():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        await page.click('#bEnter'); await page.wait_for_timeout(400)
        r = await page.evaluate("""() => { const T = window.__test, out = {}, all = new Set();
          const walk = (root, name) => { const seen = new Set(); root.traverse((o) => { const ms = o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : []; for (const m of ms) for (const k of ['map', 'emissiveMap', 'normalMap', 'roughnessMap', 'alphaMap']) { const t = m[k]; if (t && t.image && t.image.width) seen.add(t.image); } });
            let px = 0, big = []; for (const im of seen){ if (all.has(im)) continue; all.add(im); px += im.width * im.height; if (im.width * im.height >= 400000) big.push(im.width + 'x' + im.height); }
            out[name] = { n:seen.size, gpuMB:+(px * 4 * 1.333 / 1e6).toFixed(1), big:big.length }; };
          for (const k of Object.keys(T.WING)) if (T.WING[k] && T.WING[k].traverse) walk(T.WING[k], k);
          walk(T.scene, 'rest');
          out.total = +Object.values(out).reduce((s, e) => s + e.gpuMB, 0).toFixed(1);
          return out; }""")
        print(json.dumps(r))
        print(errs(logs))
        await b.close()
asyncio.run(main())
