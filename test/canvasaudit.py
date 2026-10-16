"""Who owns the canvas memory? Tracks every 2D canvas with its creator and texture use.
Usage: CAMPUS_GFX=medium python3 canvasaudit.py [desktop|mobile]"""
import asyncio, os, sys, json
from harness import *
ARGS.append('--js-flags=--expose-gc')

INIT = r"""
(() => {
  const list = window.__cv = [];
  const ce = Document.prototype.createElement;
  Document.prototype.createElement = function(tag, o){
    const el = ce.call(this, tag, o);
    if (String(tag).toLowerCase() === 'canvas'){
      const st = (new Error().stack || '').split('\n').slice(2, 7).map((l) => (l.trim().match(/at (?:new )?([\w$.<>]+)/) || [, '?'])[1]);
      list.push({ ref:new WeakRef(el), st });
    }
    return el;
  };
  const M = window.__cvMem = { live:0, peak:0 };
  const fr = new FinalizationRegistry((tok) => { M.live -= tok.px; });
  const gc = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function(k, o){
    if (!this.__ctx && k === '2d'){ const tok = this.__tok = { px:this.width * this.height }; M.live += tok.px; M.peak = Math.max(M.peak, M.live); fr.register(this, tok); }
    this.__ctx = this.__ctx || k; return gc.call(this, k, o); };
  for (const prop of ['width', 'height']){
    const d = Object.getOwnPropertyDescriptor(HTMLCanvasElement.prototype, prop);
    Object.defineProperty(HTMLCanvasElement.prototype, prop, { configurable:true, enumerable:true, get(){ return d.get.call(this); }, set(v){ d.set.call(this, v);
      const tok = this.__tok; if (tok){ const px = this.width * this.height; M.live += px - tok.px; tok.px = px; M.peak = Math.max(M.peak, M.live); } } });
  }
})();
"""

REPORT = r"""() => {
  if (window.gc) { gc(); gc(); }
  const T = window.__test, use = new Map();
  T.scene.traverse((o) => { const ms = o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : [];
    for (const m of ms) for (const k in m) { const t = m[k]; if (t && t.isTexture && t.image && t.image.tagName === 'CANVAS'){ const e = use.get(t.image) || { tex:new Set(), ver:0 }; e.tex.add(t); e.ver = Math.max(e.ver, t.version); use.set(t.image, e); } } });
  const groups = {}; let live = 0, total = 0, inScene = 0, n = 0, dyn = 0;
  for (const c of window.__cv){ const el = c.ref.deref(); if (!el || !el.__ctx || el.__ctx !== '2d') continue; n++;
    const mb = el.width * el.height * 4 / 1e6; total += mb; const u = use.get(el); if (u) inScene += mb; if (u && u.ver > 2) dyn += mb;
    const key = c.st.filter((s) => !/^(mk|Document|HTMLDocument|createElement|\?)$/.test(s)).slice(0, 2).join(' < ');
    const g = groups[key] || (groups[key] = { n:0, mb:0, maxW:0, maxH:0, scene:0, dyn:0, sizes:{} }); g.n++; g.mb += mb; if (u) g.scene++; if (u && u.ver > 2) g.dyn++;
    const sz = el.width + 'x' + el.height; g.sizes[sz] = (g.sizes[sz] || 0) + 1; }
  const top = Object.entries(groups).sort((a, b) => b[1].mb - a[1].mb).slice(0, 40).map(([k, g]) => [k, +g.mb.toFixed(1), g.n, g.scene, g.dyn, Object.entries(g.sizes).sort((a, b) => b[1] - a[1]).slice(0, 3).map((x) => x[0] + '*' + x[1]).join(' ')]);
  return { liveMB:+(window.__cvMem.live * 4 / 1e6).toFixed(1), peakMB:+(window.__cvMem.peak * 4 / 1e6).toFixed(1), lean:T.LEAN_CANVAS, freed:T.CANVAS_FREE.n, freedMB:+T.CANVAS_FREE.mb.toFixed(1), canvases:n, totalMB:+total.toFixed(1), inSceneMB:+inScene.toFixed(1), dynMB:+dyn.toFixed(1), top };
}"""

async def main(mode):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, mode, True, INIT)
        await (page.click('#bEnter') if mode == 'desktop' else page.tap('#bEnter'))
        await page.wait_for_timeout(800)
        r = await page.evaluate(REPORT)
        print('AFTER ENTER', json.dumps({k: v for k, v in r.items() if k != 'top'}))
        for row in r['top']: print('  ', row)
        # Visit each wing so anything built lazily exists, then open a station and the blueprint viewer
        for v in [{'x': 19, 'z': -6.4, 'yaw': 0, 'pitch': 0.06}, {'x': 29, 'z': -5.9, 'yaw': 0, 'pitch': -0.06}, {'x': 18.1, 'z': 0.2, 'yaw': 3.14, 'pitch': 0}, {'x': 29, 'z': 0.2, 'yaw': 3.14, 'pitch': 0}, {'x': 38.6, 'z': -3, 'yaw': -1.57, 'pitch': 0}, {'x': 0, 'z': 6, 'yaw': 0, 'pitch': 0}]:
            await page.evaluate("(v) => window.__test.goView(v)", v); await page.wait_for_timeout(700)
        await page.evaluate("() => window.__test.openBp('car', 0, { walk:false })"); await page.wait_for_timeout(900)
        await page.evaluate("() => window.__test.closeBp()")
        await page.evaluate("() => { const T = window.__test; T.startPaint(); }"); await page.wait_for_timeout(900)
        await page.evaluate("() => { const T = window.__test; T.stopPaint(); }")
        r = await page.evaluate(REPORT)
        print('AFTER TOUR', json.dumps({k: v for k, v in r.items() if k != 'top'}))
        for row in r['top'][:14]: print('  ', row)
        print(errs(logs))
        await b.close()

asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else 'desktop'))
