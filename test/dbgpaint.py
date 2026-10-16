import asyncio, os, sys, json
from harness import *
async def main():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        await page.click('#bEnter'); await page.wait_for_timeout(400)
        await page.evaluate("() => { window.__test.clearPaint(); window.__test.startPaint(); }")
        await page.wait_for_timeout(800)
        r = await page.evaluate("""() => { const T = window.__test, P = T.paint;
          T.paintDown(500, 400); for (let i = 0; i < 20; i++) T.paintMove(500 + i * 10, 400 + Math.sin(i) * 20); T.paintUp();
          const o = P.meshes[P.meshes.length - 1];
          const chain = []; let q = o; while (q){ chain.push([q.type, q.visible]); q = q.parent; }
          o.geometry.computeBoundingBox();
          return { n:P.meshes.length, st:JSON.stringify(P.strokes[P.strokes.length-1]).slice(0, 300), chain, bb:o.geometry.boundingBox, cam:[T.cam.x, T.cam.z, T.cam.yaw], rootPos:P.root.position, grp:P.group.position, mat:o.material.type, col:o.material.color };
        }""")
        print(json.dumps(r, indent=1)[:2500])
        print(errs(logs))
        await b.close()
asyncio.run(main())
