"""Headless soccer flow checks (no screenshots): save + roll-out, goal + fetch, wide + fetch, dribble.
Usage: CAMPUS_GFX=low python3 soclogic.py"""
import asyncio, os, sys, json
from harness import *
from soccer import SETUP
FLOW = """async (sc) => {
  const T = window.__test, g = T.GOAL, P = T.SOC.ball, log = [];
  T.physReset(P); if (P.body) P.body.wakeUp();
  T.KEEP.hold = false; T.keeperGo('ready'); T.KEEP.pos.x = g.x - 0.45; T.KEEP.pos.z = g.z; T.KEEP.plan = null; T.KEEP.after = '';
  T.SOC.shot = null; T.SOC.inGoal = false; T.SOC.forceCatch = sc.catch;
  T.cam.x = 77.75; T.cam.z = -2.0; T.sim(0.8);
  const eye = [T.cam.x, 1.62, T.cam.z], dx = sc.aim[0] - eye[0], dy = sc.aim[1] - eye[1], dz = sc.aim[2] - eye[2];
  T.cam.yaw = Math.atan2(-dx, -dz); T.cam.pitch = Math.atan2(dy, Math.hypot(dx, dz));
  T.socChargeStart('key'); T.KICK.t0 = performance.now() - sc.hold * 1000; T.socChargeEnd(); T.KEEP.guess = 0;
  let last = '';
  for (let i = 0; i < sc.t * 20; i++){
    T.sim(0.05);
    const st = T.KEEP.st + (T.KEEP.hold ? '+ball' : '');
    if (st !== last || i % 20 === 0){ log.push([+(i * 0.05).toFixed(2), st, P.p1.toArray().map((v) => +v.toFixed(2)), JSON.stringify(T.SOC.score)]); last = st; }
  }
  T.SOC.forceCatch = null;
  return { log, end:P.p1.toArray().map((v) => +v.toFixed(2)), player:[+T.cam.x.toFixed(2), +T.cam.z.toFixed(2)], toast:T.toastText() };
}"""
DRIBBLE = """async () => {
  const T = window.__test, P = T.SOC.ball, out = [];
  T.physReset(P); if (P.body) P.body.wakeUp();
  T.cam.x = 76.5; T.cam.z = -2.0; T.cam.yaw = -Math.PI / 2; T.cam.pitch = 0; T.sim(0.3);
  T.JOY.on = true; T.JOY.x = 0; T.JOY.y = -0.9;
  for (let i = 0; i < 50; i++){ T.sim(0.05); if (i % 5 === 0) out.push([+T.cam.x.toFixed(2), P.p1.toArray().map((v) => +v.toFixed(2))]); }
  T.JOY.on = false; T.JOY.y = 0; T.sim(0.5);
  return out;
}"""
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'tiny', False)
        page.set_default_timeout(900000)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
        print('setup', await page.evaluate(SETUP), flush=True)
        for name, sc in [('save', {'aim': [86.2, 1.1, -2.0], 'hold': 0.42, 'catch': 1, 't': 9}),
                         ('goal', {'aim': [86.6, 0.5, -4.1], 'hold': 0.95, 'catch': 0, 't': 14}),
                         ('wide', {'aim': [86.6, 0.4, 1.6], 'hold': 0.7, 'catch': 0, 't': 14})]:
            r = await page.evaluate(FLOW, sc)
            print('==', name, 'end', r['end'], 'player', r['player'], 'toast', r['toast'], flush=True)
            for row in r['log']: print('   ', row)
        print('dribble', await page.evaluate(DRIBBLE))
        print(errs(logs)); await b.close()
asyncio.run(run())
