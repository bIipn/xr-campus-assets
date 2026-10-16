import asyncio, os, sys, json
import harness
from harness import *
_orig = harness.load_src
def patched():
    s = _orig()
    a = "function waxPart(G, geo, pos, rot, scl, col, w, rough, morph){"
    assert s.count(a) == 1
    s = s.replace(a, a + " { const W = window.__wt || (window.__wt = {}), pr = geo.parameters || {}, k = geo.type + ' ' + [pr.widthSegments, pr.heightSegments, pr.radialSegments, pr.tubularSegments].filter((x) => x != null).join('x'); W[k] = (W[k] || 0) + (geo.index ? geo.index.count / 3 : geo.attributes.position.count / 3); }")
    b = "function waxTube(G, rings, n, capTop, capBot){"
    assert s.count(b) == 1
    s = s.replace(b, b + " { const W = window.__wt || (window.__wt = {}), k = 'tube n=' + n; W[k] = (W[k] || 0) + (rings.length - 1) * n * 2; }")
    return s
harness.load_src = patched
async def main():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        r = await page.evaluate("() => { const W = window.__wt || {}, n = 38; return Object.entries(W).sort((a, b) => b[1] - a[1]).slice(0, 24).map(([k, v]) => k + ': ' + Math.round(v / n) + ' per fig'); }")
        print('\n'.join(r))
        tot = await page.evaluate("() => Math.round(Object.values(window.__wt || {}).reduce((a, b) => a + b, 0) / 38)")
        print('total per fig (approx)', tot)
        await b.close()
asyncio.run(main())
