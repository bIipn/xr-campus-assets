import asyncio, os, sys, json, math
from harness import *
from painttest import wave, stroke
async def main():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        await page.click('#bEnter'); await page.wait_for_timeout(400)
        await page.evaluate("() => { window.__test.clearPaint(); window.__test.startPaint(); }")
        await page.wait_for_timeout(1500)
        W, H = 1280, 800; cx = W / 2; top = H * 0.18; span = H * 0.5
        await page.evaluate("() => { const P = window.__test.paint; P.sizeI = 2; }")
        for i, br in enumerate(['neon', 'paint', 'ribbon']):
            await page.evaluate("(b) => { const P = window.__test.paint; P.brush = b; P.shape = null; window.__test.updatePaintButtons(); }", br)
            await stroke(page, wave(cx, top + span * i / 7, W * 0.55, span / 30, 50, i))
            r = await page.evaluate("""() => { const P = window.__test.paint; const o = P.meshes[P.meshes.length - 1]; if (!o) return 'none'; const bb = new window.__test.scene.constructor().constructor; return { n:P.meshes.length, strokes:P.strokes.length, type:o.type, verts:o.userData.verts, pts:P.strokes[P.strokes.length-1].p.length / 3, first:P.strokes[P.strokes.length-1].p.slice(0,6), b:P.strokes[P.strokes.length-1].b, s:P.strokes[P.strokes.length-1].s }; }""")
            print(br, r)
        await page.wait_for_timeout(2500)
        await page.screenshot(path=os.path.join(OUT, 'dbg-brush.jpg'), type='jpeg')
        st = await page.evaluate('() => [window.__test.raf, window.__test.paint.root.visible, window.__test.WING.school.visible, window.__test.paint.group.children.length]')
        print(st)
        print(errs(logs))
        await b.close()
asyncio.run(main())
