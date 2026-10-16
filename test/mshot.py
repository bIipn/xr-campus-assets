"""Mobile UI screenshot with HUD visible. Usage: CAMPUS_GFX=medium python3 mshot.py <view> [name]"""
import asyncio, os, sys, time
from harness import *
async def run(v, name):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'mobile', True)
        page.set_default_timeout(300000)
        await page.tap('#bEnter')
        await page.wait_for_timeout(600)
        if v != 'none':
            vv = await page.evaluate('() => ' + v)
            await page.evaluate("(v) => window.__test.goView(v)", vv)
            await page.wait_for_timeout(1200)
        await page.screenshot(path=os.path.join(OUT, 'm-' + name + '.jpg'), type='jpeg', quality=80)
        print(errs(logs))
        await b.close()
asyncio.run(run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'ui'))
