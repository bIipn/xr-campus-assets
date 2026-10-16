import asyncio, os, sys, json
from harness import *
async def main():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        await page.click('#bEnter'); await page.wait_for_timeout(400)
        await page.evaluate("() => { window.__test.clearPaint(); window.__test.startPaint(); }")
        await page.wait_for_timeout(2500)
        r = await page.evaluate("""() => { const T = window.__test, c = T.camera;
          const out = { view:c.view, aspect:c.aspect, fov:c.fov, pos:c.position.toArray(), rot:[c.rotation.x, c.rotation.y, c.rotation.z], mw:Array.from(c.matrixWorld.elements).map(v=>+v.toFixed(3)), cam:[T.cam.x, T.cam.z, T.cam.yaw, T.cam.pitch], scene:document.querySelector('#scene').getBoundingClientRect().toJSON() };
          T.paintDown(640, 400); const st = T.paint.cur; out.p0 = st ? st.p.slice(0, 3) : null; T.paintUp();
          return out; }""")
        print(json.dumps(r, indent=0)[:1500])
        await b.close()
asyncio.run(main())
