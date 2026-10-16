"""Exercise the 3D Art Studio: every brush, shapes, symmetry, canvases. Usage: CAMPUS_GFX=medium python3 painttest.py [desktop|mobile]"""
import asyncio, os, sys, time, math
from harness import *

HIDE = '#hint,#tag,#toast,#award,#fade{display:none!important}'

async def snap(page, name, mode):
    await page.wait_for_timeout(1500)
    await page.screenshot(path=os.path.join(OUT, 'pt-' + mode[0] + '-' + name + '.jpg'), type='jpeg', quality=84)

async def stroke(page, pts):
    await page.evaluate("""(pts) => { const T = window.__test; T.paintDown(pts[0][0], pts[0][1]); for (const p of pts.slice(1)) T.paintMove(p[0], p[1]); T.paintUp(); }""", pts)

def wave(cx, cy, w, h, n=40, ph=0):
    return [[cx - w / 2 + w * i / n, cy + math.sin(i / n * math.pi * 2 + ph) * h] for i in range(n + 1)]

async def run(mode):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, mode, True)
        page.set_default_timeout(300000)
        await (page.click('#bEnter') if mode == 'desktop' else page.tap('#bEnter'))
        await page.wait_for_timeout(500)
        await page.add_style_tag(content=HIDE)
        await page.evaluate("() => { window.__test.clearPaint(); window.__test.startPaint(); }")
        await page.wait_for_timeout(1500)
        W, H = (1280, 800) if mode == 'desktop' else (390, 844)
        cx = W / 2; top = H * 0.18; span = H * 0.5
        brushes = ['neon', 'paint', 'ribbon', 'chrome', 'rainbow', 'beads', 'sparkle']
        await page.evaluate("() => { const P = window.__test.paint; P.sizeI = 2; }")
        for i, br in enumerate(brushes):
            await page.evaluate("(b) => { const P = window.__test.paint; P.brush = b; P.shape = null; P.color = ['#ff5a8a','#ffd166','#5ee6c8','#9aa1a6','#ffffff','#c38bff','#ffd166'][['neon','paint','ribbon','chrome','rainbow','beads','sparkle'].indexOf(b)]; window.__test.updatePaintButtons(); }", br)
            await stroke(page, wave(cx, top + span * i / 7, W * 0.55, span / 30, 50, i))
        await snap(page, 'brushes', mode)
        # shapes
        await page.evaluate("() => window.__test.clearPaint()")
        shapes = ['cube', 'sphere', 'cone', 'cylinder', 'torus', 'star', 'heart', 'pyramid']
        fins = ['paint', 'chrome', 'neon', 'rainbow', 'ribbon', 'neon', 'paint', 'beads']
        await page.evaluate("() => { window.__test.paint.sizeI = 1; }")
        for i, sh in enumerate(shapes):
            await page.evaluate("([s, f, c]) => { const P = window.__test.paint; P.shape = s; P.brush = f; P.color = c; window.__test.updatePaintButtons(); }", [sh, fins[i], ['#7aa8ff', '#ffffff', '#ff8f3d', '#ffffff', '#5ee6c8', '#ffd166', '#ff5a8a', '#c38bff'][i]])
            x = W * 0.2 + (W * 0.6) * (i % 4) / 3; y = H * (0.3 if i < 4 else 0.52)
            await stroke(page, [[x, y]])
        await page.evaluate("() => { const P = window.__test.paint; P.shape = 'star'; P.brush = 'rainbow'; P.sizeI = 0; }")
        await stroke(page, wave(cx, H * 0.7, W * 0.5, 20, 30))
        await snap(page, 'shapes', mode)
        # symmetry
        await page.evaluate("() => { window.__test.clearPaint(); const P = window.__test.paint; P.shape = null; P.brush = 'neon'; P.sym = 'x'; P.sizeI = 1; P.color = '#5ee6c8'; }")
        await stroke(page, [[W * 0.3 + 120 * math.cos(t / 20 * math.pi), H * 0.4 + 90 * math.sin(t / 20 * math.pi * 1.5)] for t in range(41)])
        await page.evaluate("() => { const P = window.__test.paint; P.sym = 'r6'; P.brush = 'rainbow'; }")
        await stroke(page, wave(cx, H * 0.55, W * 0.3, 30, 30))
        await snap(page, 'symmetry', mode)
        # canvases
        await page.evaluate("() => { window.__test.setPaintCanvas('blank'); window.__test.updatePaintButtons(); }")
        await page.wait_for_timeout(600)
        await snap(page, 'blank', mode)
        await page.evaluate("() => { window.__test.setPaintCanvas('night'); window.__test.updatePaintButtons(); }")
        await page.wait_for_timeout(600)
        await snap(page, 'night', mode)
        info = await page.evaluate("() => { const P = window.__test.paint; return { strokes:P.strokes.length, meshes:P.meshes.length, saved:(localStorage.getItem('xr-campus-paint-v1') || '').length, calls:window.__test.renderer.info.render.calls, tris:window.__test.renderer.info.render.triangles }; }")
        print(info)
        await page.evaluate("() => { window.__test.setPaintCanvas('room'); window.__test.stopPaint(); }")
        await page.wait_for_timeout(500)
        await snap(page, 'after', mode)
        print(errs(logs))
        await b.close()

if __name__ == "__main__": asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else 'desktop'))
