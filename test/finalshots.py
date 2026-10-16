"""Hero stills of the new rooms for the update message. Usage: CAMPUS_GFX=high python3 finalshots.py [desktop|mobile]"""
import asyncio, os, sys, math
from harness import *

HIDE = '.hud,#plan,#hint,#tag,#toast,#askBtn,#award,#fade{display:none!important}'

async def go(page, v, wait=1800):
    await page.evaluate("(v) => window.__test.goView(v)", v)
    await page.wait_for_timeout(wait)

async def shot(page, mode, name, wait=1500):
    await page.wait_for_timeout(wait)
    await page.screenshot(path=os.path.join(OUT, 'fin-' + mode[0] + '-' + name + '.jpg'), type='jpeg', quality=88)
    print('shot', name, flush=True)

async def run(mode):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, mode, True)
        page.set_default_timeout(600000)
        await (page.click('#bEnter') if mode == 'desktop' else page.tap('#bEnter'))
        await page.wait_for_timeout(500)
        await page.add_style_tag(content=HIDE)
        await go(page, {'x': 32.5, 'z': -3, 'yaw': 1.5708, 'pitch': 0.05}); await shot(page, mode, 'hall')
        await go(page, {'x': 29, 'z': -5.9, 'yaw': 0.35, 'pitch': -0.1}); await shot(page, mode, 'lab')
        await go(page, {'x': 21.4, 'z': 0.6, 'yaw': 2.45, 'pitch': 0.02}); await shot(page, mode, 'blueprint')
        # World Builder: build the whole diorama first
        await page.evaluate("() => { const T = window.__test; T.DIO.step = 8; T.dioApply(); }")
        await go(page, {'x': 29, 'z': 0.35, 'yaw': 3.1416, 'pitch': -0.2}); await shot(page, mode, 'world')
        # Art studio: a little night-canvas piece made with ×6 symmetry
        await page.evaluate("() => { const T = window.__test; T.clearPaint(); T.startPaint(); }")
        await page.wait_for_timeout(1500)
        W, H = (1280, 800) if mode == 'desktop' else (390, 844)
        cx = W * (0.62 if mode == 'desktop' else 0.5); cy = H * (0.42 if mode == 'desktop' else 0.36)
        await page.evaluate("() => { const T = window.__test, P = T.paint; T.setPaintCanvas('night'); P.sym = 'r6'; P.brush = 'neon'; P.shape = null; P.sizeI = 1; P.dist = 2.4; P.color = '#5ee6c8'; T.updatePaintButtons(); }")
        await page.wait_for_timeout(1500)
        async def stroke(pts):
            await page.evaluate("(pts) => { const T = window.__test; T.paintDown(pts[0][0], pts[0][1]); for (const q of pts.slice(1)) T.paintMove(q[0], q[1]); T.paintUp(); }", pts)
        r = 0.26 * min(W, H)
        await stroke([[cx + r * 0.9 * math.cos(t / 30 * math.pi * 2) * (0.5 + 0.5 * math.cos(t / 30 * math.pi * 6)), cy + r * 0.9 * math.sin(t / 30 * math.pi * 2) * (0.5 + 0.5 * math.cos(t / 30 * math.pi * 6))] for t in range(31)])
        await page.evaluate("() => { const P = window.__test.paint; P.brush = 'rainbow'; }")
        await stroke([[cx - r + 2 * r * t / 40, cy + r * 0.35 * math.sin(t / 40 * math.pi * 4)] for t in range(41)])
        await page.evaluate("() => { const P = window.__test.paint; P.shape = 'star'; P.brush = 'neon'; P.color = '#ffd166'; P.sizeI = 0; }")
        await stroke([[cx, cy - r * 1.05]])
        await shot(page, mode, 'night', 2500)
        await page.evaluate("() => { const T = window.__test; T.setPaintCanvas('room'); T.stopPaint(); T.clearPaint(); }")
        # Blueprint viewer
        await page.evaluate("() => window.__test.openBp('car', 0, { walk:false })")
        await shot(page, mode, 'bpview', 1200)
        await page.evaluate("() => window.__test.closeBp()")
        print(errs(logs))
        await b.close()

asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else 'desktop'))
