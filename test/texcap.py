import asyncio, os, sys, json
from harness import *
async def main():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        await page.click('#bEnter'); await page.wait_for_timeout(400)
        r = await page.evaluate("""() => { const T = window.__test, seen = new Map();
          T.scene.traverse((o) => { const ms = o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : []; for (const m of ms) for (const k of ['map', 'emissiveMap', 'normalMap', 'roughnessMap', 'alphaMap']) { const t = m[k]; if (t && t.image && t.image.width) seen.set(t.image, { w:t.image.width, h:t.image.height, rep:t.wrapS === 1000 }); } });
          const imgs = [...seen.values()], MB = (px) => +(px * 4 * 1.333 / 1e6).toFixed(1);
          const capDim = (e, L) => { const k = Math.min(1, L / Math.max(e.w, e.h)); return Math.round(e.w * k) * Math.round(e.h * k); };
          const capArea = (e, A) => { const k = Math.min(1, Math.sqrt(A / (e.w * e.h))); return Math.round(e.w * k) * Math.round(e.h * k); };
          const sum = (f) => MB(imgs.reduce((s, e) => s + f(e), 0));
          const hist = {}; for (const e of imgs){ const m = Math.max(e.w, e.h), k = m > 1536 ? '>1536' : m > 1024 ? '1025-1536' : m > 768 ? '769-1024' : m > 512 ? '513-768' : '<=512'; hist[k] = (hist[k] || 0) + 1; }
          return { n:imgs.length, full:sum((e) => e.w * e.h), dim1024:sum((e) => capDim(e, 1024)), dim900:sum((e) => capDim(e, 900)), dim768:sum((e) => capDim(e, 768)), area600k:sum((e) => capArea(e, 600000)), area450k:sum((e) => capArea(e, 450000)), d1024a450:sum((e) => Math.min(capDim(e, 1024), capArea(e, 450000))), hist,
            top:imgs.sort((a, b) => b.w * b.h - a.w * a.h).slice(0, 12).map((e) => e.w + 'x' + e.h + (e.rep ? 'R' : '')) }; }""")
        print(json.dumps(r))
        await b.close()
asyncio.run(main())
