"""Physics checks in the yard: CAMPUS_GFX=low python3 phystest.py [shots]"""
import asyncio, os, sys, json, time
from harness import *
HIDE = '.hud,#plan,#hint,#tag,#toast,#askBtn,#award,#guide,#fade{display:none!important}'
SHOTS = len(sys.argv) > 1
T = 'window.__test'

async def shot(page, name):
    if SHOTS:
        await page.wait_for_timeout(300)
        await page.screenshot(path=os.path.join(OUT, 'phys-' + name + '.jpg'), type='jpeg', quality=85)

async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        page.set_default_timeout(300000)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        await page.add_style_tag(content=HIDE)
        await page.evaluate(T + ".goView({ x:60.2, z:1.2, yaw:-Math.PI / 2 - 0.15, pitch:-0.05 })")
        await page.wait_for_function(T + ".PHYS.mode !== ''", timeout=120000)
        print('mode', await page.evaluate(T + '.PHYS.mode'))
        await page.evaluate(T + '.sim(1.5)')
        await shot(page, '1-tower')
        ok = True
        # kick the red ball
        before = await page.evaluate(T + ".PHYS.byId.p1.p1.toArray()")
        await page.evaluate(T + ".kickProp('p1')")
        await page.evaluate(T + '.sim(0.25)')
        mid = await page.evaluate(T + ".PHYS.byId.p1.p1.toArray()")
        await page.evaluate(T + '.sim(1.5)')
        after = await page.evaluate(T + ".PHYS.byId.p1.p1.toArray()")
        d = sum((x - y) ** 2 for x, y in zip(before, after)) ** 0.5
        print('red ball', [round(v, 2) for v in before], '-> air', [round(v, 2) for v in mid], '->', [round(v, 2) for v in after], 'moved', round(d, 2))
        ok &= d > 2 and mid[1] > 0.4
        # jump
        await page.evaluate(T + ".requestJump()")
        await page.evaluate(T + '.sim(0.2)')
        jy = await page.evaluate(T + '.PLAYER.y')
        await page.evaluate(T + '.sim(1.0)')
        ly, gr = await page.evaluate("[" + T + ".PLAYER.y, " + T + ".PLAYER.ground]")
        print('jump y', round(jy, 3), 'landed y', round(ly, 3), gr)
        ok &= jy > 0.4 and ly == 0 and gr
        # walk through the tower with the keys (no path planning around blocks)
        tb = await page.evaluate(T + ".PHYS.props.filter(P => P.kind === 'block').map(P => P.p1.toArray())")
        await page.evaluate(T + ".goView({ x:61.5, z:1.5, yaw:-Math.PI / 2, pitch:-0.05 })")
        await page.evaluate(T + '.sim(0.2)')
        await page.evaluate(T + ".JOY.on = true; " + T + ".JOY.x = 0; " + T + ".JOY.y = -0.9")
        await page.evaluate(T + '.sim(2.2)')
        await page.evaluate(T + ".JOY.on = false; " + T + ".JOY.y = 0")
        await page.evaluate(T + '.sim(2.0)')
        ta = await page.evaluate(T + ".PHYS.props.filter(P => P.kind === 'block').map(P => P.p1.toArray())")
        moved = sum(1 for a, c in zip(tb, ta) if sum((x - y) ** 2 for x, y in zip(a, c)) > 0.01)
        print('blocks moved', moved, 'of', len(tb), 'cam', await page.evaluate("[" + T + ".cam.x.toFixed(2), " + T + ".cam.z.toFixed(2)].join(',')"))
        ok &= moved >= 4 or (os.environ.get('CAMPUS_NORAPIER') and moved == 0)
        await page.evaluate(T + ".goView({ x:61.6, z:-1.8, yaw:-Math.PI / 2 - 0.45, pitch:-0.14 })")
        await page.evaluate(T + '.sim(0.5)')
        await shot(page, '2-toppled')
        # goal
        await page.evaluate(T + ".goView({ x:78.0, z:-2.0, yaw:-Math.PI / 2, pitch:-0.08 })")
        await page.evaluate(T + '.sim(0.3)')
        await shot(page, '3-goal-before')
        await page.evaluate(T + ".kickProp('p0')")
        await page.evaluate(T + '.sim(0.45)')
        await shot(page, '4-kick')
        await page.evaluate(T + '.sim(0.75)')
        await shot(page, '4b-confetti')
        await page.evaluate(T + '.sim(0.45)')
        g, st = await page.evaluate("[" + T + ".PHYS.goals, " + T + ".prog.badges.has('striker')]")
        print('goals', g, 'striker', st, 'ball', [round(v, 2) for v in await page.evaluate(T + ".PHYS.byId.p0.p1.toArray()")])
        ok &= g >= 1 and st
        await page.evaluate(T + '.sim(3.0)')
        print('ball after reset', [round(v, 2) for v in await page.evaluate(T + ".PHYS.byId.p0.p1.toArray()")])
        # swing
        await page.evaluate(T + ".goView({ x:40.8, z:16.2, yaw:0, pitch:0 })")
        await page.evaluate(T + '.sim(0.2)')
        th0 = await page.evaluate(T + '.SWING.th[1]')
        await page.evaluate(T + ".pushSwing(1)")
        await page.evaluate(T + '.sim(0.6)')
        th1 = await page.evaluate(T + '.SWING.th[1]')
        print('swing th', round(th0, 3), '->', round(th1, 3))
        ok &= abs(th1 - th0) > 0.3
        await shot(page, '5-swing')
        # spinner
        w0 = await page.evaluate(T + '.SPIN.w')
        await page.evaluate(T + ".goView({ x:66.5, z:16.8, yaw:0, pitch:-0.1 })")
        await page.evaluate(T + ".spinSpinner()")
        print('spin', round(w0, 2), '->', round(await page.evaluate(T + '.SPIN.w'), 2))
        # leaving the yard tidies up
        await page.evaluate(T + ".goView(window.__test.lobbyView())")
        await page.evaluate(T + '.sim(0.2)')
        home = await page.evaluate(T + ".PHYS.props.every(P => P.p1.distanceTo(P.home) < 1e-6)")
        print('reset on leave', home)
        ok &= home
        print('PASS' if ok else 'FAIL')
        print(errs(logs))
        await b.close()
asyncio.run(run())
