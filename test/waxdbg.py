import asyncio, os, sys, json
from harness import *
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
        r = await page.evaluate("""() => {
          const T = window.__test, sc = T.WAX_SCENES[10], v = T.waxView(sc); T.goView(v); T.frameOnce(); T.frameOnce();
          for (let k = 0; k < 108; k++) T.waxFrame(1 / 12);
          const S = sc.stage, out = { t:S.t, live:S.live, anim:S.anim.children.length, waxVis:T.WING.wax.visible };
          const THREE_ = S.g.position.constructor;
          out.kids = S.anim.children.slice(0, 40).map((c) => { const p = new THREE_(); c.getWorldPosition(p); return [c.type, c.visible, +p.x.toFixed(2), +p.y.toFixed(2), +p.z.toFixed(2), c.children.length, +c.scale.x.toFixed(2)]; });
          return out; }""")
        print(json.dumps(r)[:600])
        r2 = await page.evaluate("""() => { const T = window.__test, sc = T.WAX_SCENES[10], S = sc.stage, f = S.anim.children[1];
          const out = []; f.traverse((o) => { if (o.isMesh) out.push([o.material.type, o.material.visible, o.material.opacity, o.material.transparent, o.frustumCulled, o.geometry.type, o.renderOrder, o.layers.mask]); });
          return out; }""")
        print(r2)
        await page.evaluate("() => { const T = window.__test; T.goView({ x:-3.6, z:-75.6, yaw:0.2, pitch:0.05 }); T.frameOnce(); T.frameOnce(); }")
        await page.screenshot(path=os.path.join(OUT, 'wax-dbg.jpg'), type='jpeg', quality=80)
        print(errs(logs))
        await b.close()
asyncio.run(run())
