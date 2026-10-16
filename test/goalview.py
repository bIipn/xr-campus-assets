import asyncio, os, sys
from harness import *
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        page.set_default_timeout(600000)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
        await page.evaluate("() => document.head.insertAdjacentHTML('beforeend', '<style>.hud,#plan,#hint,#tag,#toast,#askBtn,#award,#fade{display:none!important}</style>')")
        for name, v in [('goal', {'x': 77.6, 'z': -2.0, 'yaw': -1.5708, 'pitch': -0.06}), ('goalside', {'x': 82.0, 'z': 6.5, 'yaw': -2.4, 'pitch': -0.1}), ('field', {'x': 70.0, 'z': -2.0, 'yaw': -1.5708, 'pitch': -0.05})]:
            await page.evaluate("(v) => { const T = window.__test; T.goView(v); for (let i = 0; i < 600 && T.path.length; i++) T.update(1 / 30); T.sim(0.5); T.frameOnce(); T.frameOnce(); }", v)
            await page.wait_for_timeout(300)
            await page.screenshot(path=os.path.join(OUT, 'yard-' + name + '.jpg'), type='jpeg', quality=85)
        print(await page.evaluate("() => { const T = window.__test; return T.OBST.filter((o) => o.x > 70 && o.x < 93 && o.z > -9 && o.z < 8).map((o) => [o.x.toFixed(1), o.z.toFixed(1), o.r]) }"))
        print(errs(logs)); await b.close()
asyncio.run(run())
