import asyncio
from harness import *
async def main():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        for name, v in [('lobby', {'x':0,'z':-2.5,'yaw':0,'pitch':0.02}), ('lobby-left', {'x':0,'z':-2.5,'yaw':1.25,'pitch':0.05}), ('library', {'x':-13.4,'z':-3,'yaw':1.5708,'pitch':0.08})]:
            t = await page.evaluate("""(v) => { const T = window.__test; T.goView(v); T.cam.x = v.x; T.cam.z = v.z; T.cam.yaw = v.yaw; T.cam.pitch = v.pitch;
              const cam = T.camera; cam.position.set(v.x, 1.62, v.z); cam.rotation.set(v.pitch, v.yaw, 0); cam.updateMatrixWorld();
              const r = T.renderer; const gl = r.getContext(); const t0 = performance.now(); for (let i = 0; i < 3; i++){ r.render(r.__scene || window.__scene, cam); } gl.finish(); return performance.now() - t0; }""", v) if False else None
            await view(page, v, 100)
            t = await page.evaluate("""() => { const r = window.__test.renderer, gl = r.getContext(); const t0 = performance.now(); gl.finish(); return performance.now() - t0; }""")
            ms = await page.evaluate("""() => new Promise((res) => { const t0 = performance.now(); requestAnimationFrame(() => requestAnimationFrame(() => res(performance.now() - t0))); })""")
            info = await page.evaluate("() => { const r = window.__test.renderer; return [r.info.render.calls, r.info.render.triangles]; }")
            print(name, 'two-frame ms', round(ms), 'calls/tris', info)
        print(errs(logs))
        await b.close()
asyncio.run(main())
