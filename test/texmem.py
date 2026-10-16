import asyncio, os, sys, json
from harness import *
async def main():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        await page.click('#bEnter'); await page.wait_for_timeout(400)
        r = await page.evaluate("""() => { const seen = new Map(); let texObjs = 0;
          window.__test.scene.traverse((o) => { const ms = o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : []; for (const m of ms) for (const k of ['map', 'emissiveMap', 'normalMap']) { const t = m[k]; if (t && t.image && t.image.width) { texObjs++; const e = seen.get(t.image) || { w:t.image.width, h:t.image.height, n:0 }; e.n++; seen.set(t.image, e); } } });
          const imgs = [...seen.values()], mb = (f) => +(imgs.reduce((s, e) => s + f(e), 0) / 1e6).toFixed(1);
          const cap = (e, L) => { const k = Math.min(1, L / Math.max(e.w, e.h)); return Math.round(e.w * k) * Math.round(e.h * k) * 4; };
          const domC = [...document.querySelectorAll('canvas')].reduce((s, c) => s + c.width * c.height * 4, 0) / 1e6;
          return { images:imgs.length, texObjs, canvasMB:mb((e) => e.w * e.h * 4), cap1024:mb((e) => cap(e, 1024)), cap768:mb((e) => cap(e, 768)), big:imgs.filter((e) => Math.max(e.w, e.h) > 1024).length, domCanvasMB:+domC.toFixed(1) }; }""")
        print(json.dumps(r))
        await b.close()
asyncio.run(main())
