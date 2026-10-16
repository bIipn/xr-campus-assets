import asyncio, os, sys, json
from harness import *
async def main():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        await page.click('#bEnter'); await page.wait_for_timeout(400)
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; window.__p0 = new Set(window.__test.renderer.info.programs.map((p) => p.cacheKey)); }")
        await page.evaluate("() => { const T = window.__test; T.goView({ x:0, z:-46.0, yaw:0, pitch:0.02 }); T.frameOnce(); T.frameOnce(); }")
        r = await page.evaluate("""() => { const T = window.__test, all = T.renderer.info.programs, old = all.filter((p) => window.__p0.has(p.cacheKey));
          const neu = all.filter((p) => !window.__p0.has(p.cacheKey));
          const users = new Map(); T.scene.traverse((o) => { const ms = o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : []; for (const m of ms){ const pr = T.renderer.properties.get(m); const progs = pr.programs ? [...pr.programs.values()] : []; for (const q of progs.concat(pr.currentProgram ? [pr.currentProgram] : [])) if (neu.includes(q)){ const u = users.get(q) || new Set(); u.add(m.type + (o.isSkinnedMesh ? '/skinned' : '') + (o.morphTargetInfluences ? '/morph' : '') + (o.isInstancedMesh ? '/inst' : '') + (m.name ? ':' + m.name : '')); users.set(q, u); } } });
          return neu.map((p) => { const who = [...(users.get(p) || [])].slice(0, 4).join(' '); const k = p.cacheKey.split(','); let best = null, bd = 1e9; for (const o of old){ if (o.name !== p.name) continue; const ok = o.cacheKey.split(','); let d = 0; const diff = []; for (let i = 0; i < Math.max(k.length, ok.length); i++) if (k[i] !== ok[i]){ d++; if (diff.length < 8) diff.push(i + ':' + ok[i] + '->' + k[i]); } if (d < bd){ bd = d; best = diff; } } return (who || '?') + ' | nearest diff ' + bd + ' ' + JSON.stringify(best); }); }""")
        print('\n'.join(r))
        await b.close()
asyncio.run(main())
