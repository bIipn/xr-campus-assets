"""Open the campus, walk into the library, wait for the baked room, screenshot a few views and report draw calls."""
import asyncio, os, sys, io, json, time, math
from harness import *
HIDE = '#hint,#tag,#toast,#award,#fade{display:none!important}'
VIEWS = { 'window':dict(x=-13.4, z=-3, yaw=math.pi / 2, pitch=0.08), 'stacks':dict(x=-22.0, z=-2.0, yaw=math.pi * 0.75, pitch=-0.05),
          'desk':dict(x=-20.5, z=-4.0, yaw=-math.pi * 0.35, pitch=-0.1), 'table':dict(x=-14.5, z=-8.5, yaw=math.pi * 0.5, pitch=-0.18), 'up':dict(x=-18, z=-3, yaw=math.pi * 0.5, pitch=0.55) }
import math
async def run(mode):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, mode, False)
        page.set_default_timeout(600000)
        await (page.click('#bEnter') if mode == 'desktop' else page.tap('#bEnter'))
        await page.wait_for_timeout(500)
        await page.add_style_tag(content=HIDE)
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
        if mode == 'desktop': await page.set_viewport_size({'width': 1280, 'height': 800})
        t0 = time.time()
        for k in range(300):
            st = await page.evaluate("() => { const r = window.__test.BK.rooms.lib; return r ? r.ready : 'none'; }")
            if st is True: break
            await page.wait_for_timeout(200)
        print('baked room ready:', st, 'in %.1f s' % (time.time() - t0), flush=True)
        await page.evaluate("() => { const T = window.__test; T.cam.x = -13.4; T.cam.z = -3; T.cam.yaw = Math.PI / 2; T.cam.pitch = 0.08; for (let i = 0; i < 30; i++) T.simStep(1 / 30); T.frameOnce(); }")
        for name, v in VIEWS.items():
            await page.evaluate("""(v) => { const T = window.__test; T.cam.x = v.x; T.cam.z = v.z; T.cam.yaw = v.yaw; T.cam.pitch = v.pitch; for (let i = 0; i < 20; i++) T.simStep(1 / 30); T.frameOnce(); T.frameOnce(); }""", v)
            info = await page.evaluate("() => { const T = window.__test, i = T.renderer.info.render; return { calls:i.calls, tris:i.triangles, room:T.roomAt(T.cam.x, T.cam.z).id, tex:T.renderer.info.memory.textures, geo:T.renderer.info.memory.geometries }; }")
            print(name, info, flush=True)
            await page.screenshot(path=os.path.join(OUT, 'baked_%s_%s.jpg' % (mode, name)), type='jpeg', quality=86)
        print(errs(logs))
        await b.close()
asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else 'desktop'))
