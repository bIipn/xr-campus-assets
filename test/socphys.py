"""Ball physics checks: bounce, roll, flight, curl and the net. Usage: python3 socphys.py"""
import asyncio, os, sys, json
from harness import *
RUN = """async (spec) => {
  const T = window.__test, P = T.SOC.ball, b = P.body, R = [];
  const caps = T.KEEP.capDef; T.KEEP.capDef = []; T.KEEP.caps = [];
  T.physReset(P); T.SOC.dbg = [];
  const set = (p, v, w) => { if (b){ b.setTranslation({ x:p[0], y:p[1], z:p[2] }, true); b.setLinvel({ x:v[0], y:v[1], z:v[2] }, true); b.setAngvel({ x:w[0], y:w[1], z:w[2] }, true); } P.p1.set(p[0], p[1], p[2]); P.p0.copy(P.p1); };
  set(spec.p, spec.v, spec.w || [0, 0, 0]);
  const n = Math.round(spec.t * 60);
  let maxY = -1, lastVy = 0, bounces = [], maxBulge = 0;
  for (let i = 0; i < n; i++){
    T.sim(1 / 60);
    const p = P.p1, v = b ? b.linvel() : P.v;
    if (v.y > 0 && lastVy < -0.5 && p.y < 0.2) bounces.push(+(-lastVy).toFixed(2));
    lastVy = v.y; maxY = Math.max(maxY, p.y);
    for (const N of T.SOC.nets) maxBulge = Math.max(maxBulge, Math.abs(N.A || 0));
    if (i % (spec.every || 6) === 0) R.push([+(i / 60).toFixed(2), +p.x.toFixed(2), +p.y.toFixed(2), +p.z.toFixed(2), +Math.hypot(v.x, v.y, v.z).toFixed(2)]);
  }
  T.KEEP.capDef = caps;
  const p = P.p1;
  const dbg = T.SOC.dbg; T.SOC.dbg = null;
  return { dbg, end:[+p.x.toFixed(2), +p.y.toFixed(2), +p.z.toFixed(2)], maxY:+maxY.toFixed(2), bounces, maxBulge:+maxBulge.toFixed(2), trace:R };
}"""
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', False)
        page.set_default_timeout(600000)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
        await page.evaluate("""async () => { const T = window.__test; T.goView({ x:70, z:-2, yaw:-Math.PI / 2, pitch:0 }); for (let i = 0; i < 400 && T.path.length; i++) T.update(1 / 30); T.cam.x = 70; T.cam.z = -2;
          const t0 = performance.now(); while (performance.now() - t0 < 60000 && !T.PHYS.mode){ await new Promise((r) => setTimeout(r, 100)); T.sim(1 / 60); } T.sim(0.3); }""")
        print('mode', await page.evaluate("() => window.__test.PHYS.mode"))
        tests = [
          ('net centre 20m/s', {'p': [82, 0.6, -2], 'v': [20, 1.5, 0], 't': 1.6, 'every': 3}),
          ('net corner 22m/s', {'p': [82, 0.6, -2], 'v': [21, 4, -6], 't': 1.6, 'every': 3}),
          ('net corner high 25m/s', {'p': [80, 0.3, -2], 'v': [24, 5, 4], 't': 1.6, 'every': 3}),
          ('net low 15m/s', {'p': [83, 0.11, -1], 'v': [15, 0, 1], 't': 1.6, 'every': 3}),
          ('side net', {'p': [83.5, 0.11, -1.5], 'v': [12, 2.5, -6.5], 't': 1.6, 'every': 3}),
        ]
        for name, spec in tests:
            r = await page.evaluate(RUN, spec)
            print(name, json.dumps({k: v for k, v in r.items() if k not in ('trace', 'dbg')}))
            print('   ', r['trace'][17:34])
        print(errs(logs)); await b.close()
asyncio.run(run())
