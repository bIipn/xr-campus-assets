import asyncio, os, sys, json
from harness import *
async def main():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        await page.click('#bEnter'); await page.wait_for_timeout(400)
        r = await page.evaluate("""() => { const T = window.__test, seen = new Map();
          for (const w of [T.WING.wax, T.WING.waxIntro]) w.traverse((o) => { const ms = o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : []; for (const m of ms) for (const k of ['map', 'emissiveMap', 'normalMap', 'roughnessMap', 'alphaMap']) { const t = m[k]; if (t && t.image && t.image.width) { const e = seen.get(t) || { w:t.image.width, h:t.image.height, k, rep:t.wrapS === 1000, mip:t.generateMipmaps, img:t.image }; seen.set(t, e); } } });
          const lean = (e) => { const m = Math.max(e.w, e.h), k = Math.min(1024 / m, m > 512 ? 0.75 : 1, 1); return Math.round(e.w * k) * Math.round(e.h * k); };
          const groups = {}; let full = 0, mob = 0; const imgs = new Set();
          for (const e of seen.values()){ const key = e.w + 'x' + e.h + (e.rep ? 'R' : '') + ':' + e.k; const g = groups[key] || (groups[key] = { n:0, mb:0, mobMB:0 }); g.n++; const px = e.w * e.h; g.mb += px * 5.33 / 1e6; g.mobMB += lean(e) * 5.33 / 1e6; full += px * 5.33 / 1e6; mob += lean(e) * 5.33 / 1e6; imgs.add(e.img); }
          const top = Object.entries(groups).sort((a, b) => b[1].mobMB - a[1].mobMB).slice(0, 16).map(([k, g]) => k + ' x' + g.n + ' = ' + g.mobMB.toFixed(1) + 'MB');
          return { textures:seen.size, images:imgs.size, fullMB:+full.toFixed(1), mobileMB:+mob.toFixed(1), top }; }""")
        print(json.dumps(r, indent=1))
        await b.close()
asyncio.run(main())
