import asyncio, os, sys, json, time
from harness import *
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        page.set_default_timeout(300000)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        T = 'window.__test'
        await page.evaluate(T + ".goView({ x:60.2, z:1.2, yaw:-Math.PI / 2 - 0.15, pitch:-0.05 })")
        await page.wait_for_function(T + ".PHYS.mode !== ''", timeout=120000)
        for i in range(3): print('render ms, phys ms', [round(v, 1) for v in await page.evaluate(T + '.timeRender()')])
        print(await page.evaluate("JSON.stringify(window.__test.renderer.info.render)"))
        await b.close()
asyncio.run(run())
