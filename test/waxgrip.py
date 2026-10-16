"""Close-up stills of wax scenes through time, to check grips, reach and poses.
Usage: python3 waxgrip.py <scenes e.g. 1,2> [times e.g. 0,2,4] [tag]
One sheet per scene: first row a wide shot, then one row per figure; one column per time."""
import asyncio, os, sys, io, time, json
from harness import *
from PIL import Image, ImageDraw
CW, CH = 400, 330
HIDE = '.hud,#plan,#hint,#tag,#toast,#askBtn,#award,#fade,#cap,.cap,#waxCap{display:none!important}'
async def run(scenes, times, tag):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        page.set_default_timeout(600000)
        await page.click('#bEnter'); await page.wait_for_timeout(400)
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
        await page.add_style_tag(content=HIDE)
        await page.set_viewport_size({'width': CW, 'height': CH})
        await page.evaluate("() => { window.__test.hkWant('wax'); }")
        if os.environ.get('HANDS'): await page.evaluate("() => { window.__hands = true; }")
        if os.environ.get('VYAW'): await page.evaluate("(v) => { window.__viewYaw = v; }", json.loads(os.environ['VYAW']))
        for k in range(200):
            n = await page.evaluate("() => { const W = window.__test.WAX; return [W.figs.filter((f) => f.mesh).length, W.figs.length]; }")
            if n[0] == n[1] and n[1] > 0: break
            await page.wait_for_timeout(250)
        print('figures', n, flush=True)
        for sn in scenes:
            i = sn - 1
            v = await page.evaluate("(i) => window.__test.waxView(window.__test.WAX_SCENES[i])", i)
            await page.evaluate("(v) => { const T = window.__test; T.goView(v); T.frameOnce(); T.frameOnce(); }", v)
            await page.wait_for_timeout(250)
            nf = await page.evaluate("(i) => window.__test.WAX_SCENES[i].stage.figs.length", i)
            rows = 1 + nf
            sheet = Image.new('RGB', (CW * len(times), CH * rows + 24 * rows), (20, 20, 24))
            dr = ImageDraw.Draw(sheet)
            for c, t in enumerate(times):
                for r in range(rows):
                    await page.evaluate("""([i, t, r]) => { const T = window.__test, sc = T.WAX_SCENES[i], S = sc.stage;
                      S.t = t; for (const f of S.figs){ f.lt = t; T.waxSample(f, t); T.waxApply(f, false, 0); }
                      for (const fn of S.ticks) fn(t, 0, S);
                      S.g.updateMatrixWorld(true); T.waxResolve(S); S.g.updateMatrixWorld(true);
                      const VIEW_YAW = window.__viewYaw || {};
                      const V = THREE => 0;
                      const g = S.g, P = (x, y, z) => { const v = g.position.clone(); v.set(x, y, z); return g.localToWorld(v); };
                      let cam, at, fov;
                      if (r === 0){ cam = P(0, 1.7, 3.6); at = P(0, 1.0, -1.9); fov = 50; }
                      else { const f = S.figs[r - 1], sp = f.all ? f.all.find((b) => /Spine2$/.test(b.name)) : null;
                        const c = (sp || f.root).getWorldPosition(g.position.clone()); if (!sp) c.y += 1.1;
                        const q = f.root.getWorldQuaternion(f.root.quaternion.clone());
                        const fw = c.clone().set(0, 0, 1).applyQuaternion(q), side = c.clone().set(1, 0, 0).applyQuaternion(q);
                        const yaw = VIEW_YAW[r] == null ? 0.45 : VIEW_YAW[r];
                        const d = fw.clone().multiplyScalar(Math.cos(yaw)).addScaledVector(side, Math.sin(yaw)).multiplyScalar(1.45);
                        cam = c.clone().add(d); cam.y += 0.32; at = c.clone(); at.y -= 0.12; fov = 36;
                        if (window.__hands){ const hs = f.all.filter((b) => /_(L|R)_Hand$|^L_Hand$|^R_Hand$|Bip01_[LR]_Hand$/.test(b.name)); const hp = hs.length ? hs.map((b) => b.getWorldPosition(g.position.clone())) : [c.clone()];
                          const m = hp.reduce((a, b) => a.add(b), c.clone().set(0, 0, 0)).multiplyScalar(1 / hp.length);
                          const dd = fw.clone().multiplyScalar(Math.cos(yaw)).addScaledVector(side, Math.sin(yaw)).multiplyScalar(0.85);
                          cam = m.clone().add(dd); cam.y += 0.25; at = m; fov = 40; } }
                      T.renderFrom([cam.x, cam.y, cam.z], [at.x, at.y, at.z], fov); }""", [i, t, r])
                    png = await page.screenshot(type='png')
                    im = Image.open(io.BytesIO(png)).convert('RGB').resize((CW, CH))
                    y = r * (CH + 24)
                    sheet.paste(im, (c * CW, y + 24))
                    dr.text((c * CW + 6, y + 5), 'S%d t=%.2f %s' % (sn, t, 'wide' if r == 0 else 'fig%d' % r), fill=(240, 220, 160))
            out = os.path.join(OUT, 'grip-%s-s%02d.jpg' % (tag, sn))
            sheet.save(out, quality=82)
            print('sheet', out, flush=True)
        print(errs(logs))
        await b.close()
sc = [int(x) for x in (sys.argv[1] if len(sys.argv) > 1 else '1').split(',')]
tt = [float(x) for x in (sys.argv[2] if len(sys.argv) > 2 else '0,2,4,6,8,10,12').split(',')]
tag = sys.argv[3] if len(sys.argv) > 3 else 'a'
asyncio.run(run(sc, tt, tag))
