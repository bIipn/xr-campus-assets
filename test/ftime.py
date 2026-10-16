import asyncio, os, sys, json, time
from harness import *
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', False)
        page.set_default_timeout(300000)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        T = 'window.__test'
        await page.evaluate(T + ".goView({ x:60.2, z:1.2, yaw:-Math.PI / 2 - 0.15, pitch:-0.05 })")
        await page.wait_for_function(T + ".PHYS.mode !== ''", timeout=120000)
        for i in range(4):
            t0 = await page.evaluate(T + '.GFX.t'); w0 = time.time()
            await page.wait_for_timeout(2000)
            t1 = await page.evaluate(T + '.GFX.t')
            print('sim advanced', round(t1 - t0, 3), 'in', round(time.time() - w0, 2), 's; cam', await page.evaluate(T + '.cam.x'))
        await page.evaluate(T + ".kickProp('p1')")
        for i in range(3):
            await page.wait_for_timeout(1500)
            print('ball', await page.evaluate(T + ".PHYS.byId.p1.mesh.position.toArray().map(v => v.toFixed(2)).join(',') + ' sleeping ' + window.__test.PHYS.byId.p1.body.isSleeping() + ' acc ' + window.__test.PHYS.acc.toFixed(3) + ' t ' + window.__test.PHYS.t.toFixed(2)"))
        print(errs(logs))
        await b.close()
asyncio.run(run())
