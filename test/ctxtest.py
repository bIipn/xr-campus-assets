"""Lose and restore the WebGL context. Desktop should keep rendering; phones (freed canvases) should reload.
Usage: CAMPUS_GFX=medium python3 ctxtest.py [desktop|mobile]"""
import asyncio, os, sys, json
from harness import *

async def run(mode):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, mode, True)
        page.set_default_timeout(600000)
        await (page.click('#bEnter') if mode == 'desktop' else page.tap('#bEnter'))
        await page.wait_for_timeout(600)
        await page.evaluate("() => window.__test.goView({ x:32.5, z:-3, yaw:1.5708, pitch:0.05 })")
        await page.wait_for_timeout(1200)
        await page.screenshot(path=os.path.join(OUT, 'ctx-' + mode[0] + '-before.jpg'), type='jpeg', quality=80)
        await page.evaluate("() => { window.__mark = 1; const gl = window.__test.renderer.getContext(); window.__lc = gl.getExtension('WEBGL_lose_context'); window.__lc.loseContext(); }")
        await page.wait_for_timeout(800)
        await page.evaluate("() => window.__lc.restoreContext()")
        await page.wait_for_timeout(4000)
        st = await page.evaluate("() => ({ reloaded: window.__mark !== 1, intro: !!document.querySelector('#intro') && !document.querySelector('#intro').hidden, lost: window.__test ? window.__test.renderer.getContext().isContextLost() : null })")
        print(mode, 'after restore', st, flush=True)
        if not st['reloaded']:
            await page.evaluate("() => window.__test.goView({ x:29, z:-5.9, yaw:0.35, pitch:-0.1 })")
            await page.wait_for_timeout(1500)
        await page.screenshot(path=os.path.join(OUT, 'ctx-' + mode[0] + '-after.jpg'), type='jpeg', quality=80)
        print(errs(logs))
        await b.close()

asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else 'desktop'))
