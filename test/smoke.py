import asyncio, sys
from harness import *

async def main():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        print('nogl hidden:', await page.evaluate("document.querySelector('#nogl').hidden"))
        print(errs(logs))
        info = await page.evaluate("""() => { const r = window.__test.renderer; return { calls: r.info.render.calls, tris: r.info.render.triangles, geos: r.info.memory.geometries, tex: r.info.memory.textures, free: window.__test.NAV.free.reduce((a,b)=>a+b,0) }; }""")
        print('render info', info)
        await page.wait_for_timeout(300)
        await shot(page, 'd-01-intro')
        await page.click('#bEnter'); await page.wait_for_timeout(500)
        await shot(page, 'd-02-lobby')
        info = await page.evaluate("""() => { const r = window.__test.renderer; return { calls: r.info.render.calls, tris: r.info.render.triangles }; }""")
        print('render info lobby', info)
        await b.close()

asyncio.run(main())
