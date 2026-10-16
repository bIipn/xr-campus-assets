"""Soccer test: a shot sequence from first person and a side camera, then shot statistics.
Usage: CAMPUS_GFX=medium python3 soccer.py [shots|stats|both] [desktop|mobile]"""
import asyncio, os, sys, json
from harness import *
MODE = sys.argv[1] if len(sys.argv) > 1 else 'both'
DEV = sys.argv[2] if len(sys.argv) > 2 else 'desktop'
PRE = 'soc-' + ('m' if DEV == 'mobile' else 'd') + '-'
SETUP = """async () => {
  const T = window.__test;
  T.goView({ x:77.75, z:-2.0, yaw:-Math.PI / 2, pitch:-0.1 });
  for (let i = 0; i < 400 && T.path.length; i++) T.update(1 / 30);
  T.cam.x = 77.75; T.cam.z = -2.0; T.cam.yaw = -Math.PI / 2; T.cam.pitch = -0.1;
  T.sim(0.3);
  const t0 = performance.now();
  while (performance.now() - t0 < 120000 && !(T.PHYS.mode && T.KEEP.fig && T.KEEP.fig.mesh && T.BODY.fig && T.BODY.fig.mesh)){ await new Promise((r) => setTimeout(r, 200)); T.sim(1 / 60); }
  T.sim(0.5);
  return { mode:T.PHYS.mode, keeper:!!(T.KEEP.fig && T.KEEP.fig.mesh), body:!!(T.BODY.fig && T.BODY.fig.mesh), ball:T.SOC.ball && T.SOC.ball.p1.toArray().map((v) => +v.toFixed(3)) };
}"""
AIM = """(a) => { const T = window.__test, eye = [T.cam.x, 1.62, T.cam.z], dx = a[0] - eye[0], dy = a[1] - eye[1], dz = a[2] - eye[2]; T.cam.yaw = Math.atan2(-dx, -dz); T.cam.pitch = Math.atan2(dy, Math.hypot(dx, dz)); return [T.cam.yaw, T.cam.pitch]; }"""
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, DEV, False)
        page.set_default_timeout(900000)
        await page.click('#bEnter'); await page.wait_for_timeout(400)
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
        await page.evaluate("() => document.head.insertAdjacentHTML('beforeend', '<style>.hud,#plan,#hint,#tag,#askBtn,#award,#fade{display:none!important}</style>')")
        print('setup', await page.evaluate(SETUP), flush=True)
        if MODE in ('shots', 'both'):
            await page.evaluate("() => { const T = window.__test; T.stepFrame(1 / 60); T.stepFrame(1 / 60); }")
            await page.screenshot(path=os.path.join(OUT, PRE + '0-setup.jpg'), type='jpeg', quality=85)
            await page.evaluate("() => window.__test.renderFrom([82.4, 1.5, 6.6], [84.5, 0.9, -2.0], 50)")
            await page.screenshot(path=os.path.join(OUT, PRE + '0-keeper.jpg'), type='jpeg', quality=85)
            print('aim', await page.evaluate(AIM, [86.6, 1.55, -3.9]))
            ok = await page.evaluate("() => { const T = window.__test; const r = T.socChargeStart('key'); for (let i = 0; i < 21; i++) T.stepFrame(1 / 30); return r; }")
            await page.screenshot(path=os.path.join(OUT, PRE + '1-charge.jpg'), type='jpeg', quality=85)
            info = await page.evaluate("() => { const T = window.__test; T.KICK.t0 = performance.now() - 760; T.socChargeEnd(); const pl = T.KICK.plan; return pl ? { T:pl.T, tc:pl.tc, v:pl.v.toArray().map((x) => +x.toFixed(2)), w:pl.w.toArray().map((x) => +x.toFixed(1)), th:+pl.th.toFixed(3), psi:+pl.psi.toFixed(3), C:pl.C, S0:pl.S0 } : null; }")
            print('plan', json.dumps(info), flush=True)
            t = 0.0
            marks = [('2-runup', 0.16), ('3-strike', info['tc'] + 0.005 if info else 0.4), ('4-flight', info['tc'] + 0.16 if info else 0.6), ('5-arrive', info['tc'] + 0.36 if info else 0.8), ('6-after', info['tc'] + 0.9 if info else 1.4), ('7-settle', info['tc'] + 2.2 if info else 2.6)]
            for name, at in marks:
                n = max(0, round((at - t) * 60))
                await page.evaluate("(n) => { const T = window.__test; for (let i = 0; i < n; i++) T.stepFrame(1 / 60); }", n)
                t += n / 60
                await page.screenshot(path=os.path.join(OUT, PRE + name + '.jpg'), type='jpeg', quality=85)
                st = await page.evaluate("() => { const T = window.__test, P = T.SOC.ball; return { keeper:T.KEEP.st, ball:P.p1.toArray().map((v) => +v.toFixed(2)), cam:[+T.cam.x.toFixed(2), +T.cam.z.toFixed(2), +T.cam.yaw.toFixed(2), +T.cam.pitch.toFixed(2)], toast:T.toastText(), score:T.SOC.score }; }")
                print(name, round(t, 3), json.dumps(st), flush=True)
                await page.evaluate("() => window.__test.renderFrom([83.2, 1.35, 6.2], [85.2, 0.9, -2.0], 50)")
                await page.screenshot(path=os.path.join(OUT, PRE + name + '-side.jpg'), type='jpeg', quality=85)
                await page.evaluate("() => { const T = window.__test; T.stepFrame(0.0001); }")
        if MODE in ('stats', 'both'):
            res = await page.evaluate("""async () => {
              const T = window.__test, out = [], targets = [];
              const g = T.GOAL, hw = g.w / 2;
              for (let i = 0; i < 36; i++){
                const zz = g.z + (Math.random() * 2 - 1) * (hw - 0.15), yy = 0.15 + Math.random() * 1.7, hold = 0.25 + Math.random() * 0.75;
                targets.push([zz, yy, hold]);
              }
              for (const [zz, yy, hold] of targets){
                const P = T.SOC.ball; T.physReset(P); if (P.body) P.body.wakeUp();
                T.KEEP.hold = false; T.keeperGo('ready'); T.KEEP.pos.x = g.x - 0.45; T.KEEP.pos.z = g.z; T.KEEP.plan = null; T.SOC.shot = null; T.SOC.inGoal = false;
                T.cam.x = 77.75; T.cam.z = -2.0; T.sim(0.6);
                const eye = [T.cam.x, 1.62, T.cam.z], dx = g.x - eye[0], dy = yy - eye[1], dz = zz - eye[2];
                T.cam.yaw = Math.atan2(-dx, -dz); T.cam.pitch = Math.atan2(dy, Math.hypot(dx, dz));
                const before = Object.assign({}, T.SOC.score);
                if (!T.socChargeStart('key')){ out.push('nostart'); continue; }
                T.KICK.t0 = performance.now() - hold * 1000; T.socChargeEnd();
                T.sim(4.2);
                const s = T.SOC.score;
                out.push(s.goals > before.goals ? 'goal' : s.saves > before.saves ? 'save' : s.shots > before.shots ? 'miss' : 'none');
              }
              return out;
            }""")
            from collections import Counter
            print('stats', Counter(res), res, flush=True)
        print(errs(logs)); await b.close()
if __name__ == "__main__":
    asyncio.run(run())
