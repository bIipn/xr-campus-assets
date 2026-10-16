import asyncio, os, sys, json
from harness import *
async def main():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        r = await page.evaluate("""() => { const T = window.__test, tri = (g) => g.index ? g.index.count / 3 : g.attributes.position.count / 3;
          const figs = T.WAX.figs.map((f) => ({ c:tri(f.cloth.geometry), s:tri(f.body.geometry), v:f.cloth.geometry.attributes.position.count + f.body.geometry.attributes.position.count }));
          const sumT = figs.reduce((a, f) => a + f.c + f.s, 0), sumV = figs.reduce((a, f) => a + f.v, 0);
          let meshes = 0, tris = 0, figMeshes = 0, inst = 0, shadow = 0; const perStage = [];
          T.WING.wax.traverse((o) => { if (!o.isMesh || (o.material && o.material.visible === false)) return; meshes++; tris += tri(o.geometry) * (o.isInstancedMesh ? o.count : 1); if (o.isSkinnedMesh) figMeshes++; if (o.isInstancedMesh) inst++; if (o.castShadow) shadow++; });
          for (const sc of T.WAX_SCENES){ let n = 0, t = 0; sc.stage.root ? sc.stage.root.traverse((o) => { if (o.isMesh && o.material.visible !== false){ n++; t += tri(o.geometry); } }) : 0; perStage.push(n + '/' + Math.round(t / 1000) + 'k'); }
          return { figs:figs.length, figTrisAvg:Math.round(sumT / figs.length), figTrisMax:Math.max(...figs.map((f) => f.c + f.s)), figVertsAvg:Math.round(sumV / figs.length), figTrisTotal:sumT, waxMeshes:meshes, waxTris:Math.round(tris), skinned:figMeshes, castShadow:shadow, perStage, stageKeys:Object.keys(T.WAX_SCENES[0].stage).join(',') }; }""")
        print(json.dumps(r, indent=1))
        await b.close()
asyncio.run(main())
