import asyncio, os, sys, json
from harness import *
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', False)
        page.set_default_timeout(600000)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
        r = await page.evaluate("""() => { const T = window.__test, S = T.scene, tr = T.SV.tray; const out = [];
          const v = new tr.position.constructor();
          out.push(['scene pos', S.position.toArray(), 'scale', S.scale.toArray(), 'auto', S.matrixAutoUpdate, S.matrixWorldAutoUpdate]);
          out.push(['g pos', T.SV.g.position.toArray(), T.SV.g.scale.toArray(), T.SV.g.matrixWorld.elements.slice(12, 15)]);
          out.push(['tray local', tr.position.toArray(), 'world', tr.getWorldPosition(v).toArray(), 'mat', tr.matrix.elements.slice(12, 15)]);
          tr.updateWorldMatrix(true, false); S.attach(tr);
          out.push(['after attach local', tr.position.toArray(), 'world', tr.getWorldPosition(v).toArray()]);
          T.SV.g.attach(tr);
          out.push(['back', tr.position.toArray()]);
          return out; }""")
        for x in r: print(x)
        await b.close()
asyncio.run(run())
