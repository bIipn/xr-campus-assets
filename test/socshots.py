"""A few soccer stills at chosen moments (sim in between, render only the stills).
Usage: CAMPUS_GFX=medium python3 socshots.py"""
import asyncio, os, sys, json
from harness import *
from soccer import SETUP
CAMS = {
  'broad': ([81.4, 2.2, 4.6], [85.4, 0.9, -2.2], 46),
  'close': ([83.6, 1.5, 1.4], [86.0, 0.9, -2.0], 46),
  'net':   ([84.0, 1.4, 2.6], [87.4, 0.7, -1.0], 50),
}
SHOOT = """(sc) => {
  const T = window.__test, g = T.GOAL, P = T.SOC.ball;
  T.physReset(P); if (P.body) P.body.wakeUp();
  T.KEEP.hold = false; T.keeperGo('ready'); T.KEEP.pos.x = g.x - 0.45; T.KEEP.pos.z = g.z; T.KEEP.plan = null; T.KEEP.after = '';
  T.SOC.shot = null; T.SOC.inGoal = false; T.SOC.forceCatch = sc.catch;
  T.cam.x = 77.75; T.cam.z = -2.0; T.sim(0.8);
  const eye = [T.cam.x, 1.62, T.cam.z], dx = sc.aim[0] - eye[0], dy = sc.aim[1] - eye[1], dz = sc.aim[2] - eye[2];
  T.cam.yaw = Math.atan2(-dx, -dz); T.cam.pitch = Math.atan2(dy, Math.hypot(dx, dz));
  T.socChargeStart('key'); T.KICK.t0 = performance.now() - sc.hold * 1000; T.socChargeEnd(); T.KEEP.guess = 0;
}"""
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'small', False)
        page.set_default_timeout(900000)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
        await page.evaluate("() => document.head.insertAdjacentHTML('beforeend', '<style>.hud,#plan,#hint,#tag,#askBtn,#award,#fade,#toast{display:none!important}</style>')")
        print('setup', await page.evaluate(SETUP), flush=True)
        plan = [
          ('save', {'aim': [86.2, 1.1, -2.0], 'hold': 0.42, 'catch': 1}, [(0.93, 'close'), (1.6, 'close'), (2.45, 'broad'), (2.62, 'broad')]),
          ('dive', {'aim': [86.6, 0.45, -0.4], 'hold': 0.6, 'catch': 1}, [(0.86, 'close'), (1.15, 'close'), (2.4, 'broad')]),
          ('goal', {'aim': [86.6, 1.6, -4.1], 'hold': 0.95, 'catch': 0}, [(0.82, 'close'), (1.05, 'net'), (3.3, 'broad'), (5.9, 'net'), (7.3, 'broad')]),
        ]
        for name, sc, marks in plan:
            await page.evaluate(SHOOT, sc)
            t = 0
            for at, cam in marks:
                await page.evaluate("(s) => window.__test.sim(s)", max(0, at - t)); t = at
                st = await page.evaluate("() => { const T = window.__test, P = T.SOC.ball; return [T.KEEP.st, T.KEEP.hold, P.p1.toArray().map((v) => +v.toFixed(2))]; }")
                c = CAMS[cam]
                await page.evaluate("(a) => window.__test.renderFrom(a[0], a[1], a[2])", list(c))
                fn = 'shot-%s-%.2f.jpg' % (name, at)
                await page.screenshot(path=os.path.join(OUT, fn), type='jpeg', quality=86)
                print(fn, st, flush=True)
        print(errs(logs)); await b.close()
asyncio.run(run())
