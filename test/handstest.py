"""Hands-on stations: play each clip frame by frame and photograph your hands at work.
Usage: python3 handstest.py sieve [desktop|mobile]  (shots land in shots2/hands-*.jpg)"""
import asyncio, os, sys, io, json, time
from harness import *
from PIL import Image, ImageDraw
HIDE = '#hint,#tag,#toast,#award,#fade{display:none!important}'
CW, CH = 480, 300

async def click(page, label):
    ok = await page.evaluate("""(label) => { const b = [...document.querySelectorAll('#stBtns button')].find((x) => x.textContent.trim() === label); if (!b) return 'missing: ' + label + ' | have: ' + [...document.querySelectorAll('#stBtns button')].map((x) => x.textContent.trim() + (x.disabled ? '(off)' : '')).join(', '); if (b.disabled) return 'disabled: ' + label; b.click(); return 'ok'; }""", label)
    if ok != 'ok': print('  !!', ok, flush=True)
    return ok == 'ok'

async def step(page, dt):
    """Advance the app by dt seconds in 1/30 s frames (walking, clips, physics), rendering only the last frame"""
    await page.evaluate("""(dt) => { const T = window.__test; const n = Math.max(1, Math.round(dt * 30)); for (let i = 0; i < n; i++) T.simStep(1 / 30); T.frameOnce(); }""", dt)

async def play(page, label, frames, out, tag, maxT=60):
    """Click a button that starts a clip, then shoot it as it plays: one cell per entry in frames (seconds after the click)"""
    ok = await click(page, label)
    if not ok: return
    sheet = Image.new('RGB', (CW * len(frames), CH + 22), (20, 20, 24)); dr = ImageDraw.Draw(sheet)
    t = 0.0
    for c, ft in enumerate(frames):
        await step(page, max(0, ft - t)); t = ft
        png = await page.screenshot(type='png')
        sheet.paste(Image.open(io.BytesIO(png)).convert('RGB').resize((CW, CH)), (c * CW, 22))
        info = await page.evaluate("() => { const T = window.__test, H = T.HANDS; return (H.clip ? 't=' + H.t.toFixed(1) : 'idle') + ' lean=' + H.lean.toFixed(0) + ' cr=' + (H.crouch || 0).toFixed(2) + ' L=' + H.h.L.w.toFixed(2) + ' R=' + H.h.R.w.toFixed(2); }")
        dr.text((c * CW + 6, 4), '%s +%.1fs  %s' % (label, ft, info), fill=(240, 220, 160))
    # run the clip out
    for _ in range(int(maxT * 2)):
        busy = await page.evaluate("() => window.__test.handsBusy() || window.__test.path.length > 0")
        if not busy: break
        await step(page, 0.5)
    fn = os.path.join(OUT, 'hands-%s-%s.jpg' % (out, tag)); sheet.save(fn, quality=84); print('sheet', fn, flush=True)

async def run(which, mode):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, mode, False)
        page.set_default_timeout(600000)
        await (page.click('#bEnter') if mode == 'desktop' else page.tap('#bEnter'))
        await page.wait_for_timeout(400)
        await page.add_style_tag(content=HIDE)
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
        if mode == 'desktop': await page.set_viewport_size({'width': 1280, 'height': 800})
        if which == 'mobile':
            await page.evaluate("() => window.__test.openStation('sieve')")
            for k in range(150):
                ok = await page.evaluate("() => { window.__test.simStep(1 / 30); return !!(window.__test.HANDS.fig && window.__test.HANDS.fig.mesh); }")
                if ok: break
                await page.wait_for_timeout(200)
            await click(page, 'Start the test'); await step(page, 3.0)
            await play(page, 'Pour it through the splitter', [1.0, 2.2, 5.5], 'mobile', '1split')
            await page.evaluate("() => window.__test.openStation('bench')"); await step(page, 2)
            await page.evaluate("() => { window.__test.STATIONS.bench.act('car'); }"); await step(page, 3.0)
            await click(page, 'Start building'); await step(page, 0.5)
            await play(page, 'Set the chassis on the stand', [0.6, 1.2, 1.9], 'mobile', 'c1chassis')
        if which == 'sieve':
            await page.evaluate("() => window.__test.openStation('sieve')")
            await step(page, 1.5)
            for k in range(150):
                ok = await page.evaluate("() => { window.__test.simStep(1 / 30); return !!(window.__test.HANDS.fig && window.__test.HANDS.fig.mesh); }")
                if ok: break
                await page.wait_for_timeout(200)
            print('body loaded', ok, flush=True)
            await click(page, 'Start the test'); await step(page, 3.0)
            await play(page, 'Pour it through the splitter', [0.5, 1.2, 2.2, 3.4, 4.6, 6.0, 7.0], 'sieve', '1split')
            await play(page, 'Split it again', [1.0, 2.4], 'sieve', '1split2')
            await click(page, 'Next: dry and weigh'); await step(page, 2.5)
            await play(page, 'Dry it in the oven', [0.6, 1.6, 3.0, 4.2, 5.0, 6.2, 8.5, 10.2, 11.6, 13.4], 'sieve', '2dry', 40)
            await play(page, 'Tare the balance', [0.4, 0.7, 1.2], 'sieve', '2tare')
            await play(page, 'Pour the sample into the dish', [0.6, 1.4, 2.4, 3.2, 4.4], 'sieve', '2weigh')
            await click(page, 'Next: stack the sieves'); await step(page, 2.5)
            await play(page, 'Stack the sieves', [0.5, 1.0, 1.6, 2.4, 4.0, 8.0, 12.0, 15.5], 'sieve', '3stack', 40)
            await click(page, 'Next: shake'); await step(page, 2.5)
            await play(page, 'Pour the sample onto the top sieve', [0.5, 1.2, 2.6, 3.6, 4.6, 5.6], 'sieve', '4pour')
            await play(page, 'Put the cover on and clamp it', [0.5, 1.2, 1.9, 2.6, 3.2], 'sieve', '4cover')
            await play(page, 'Press START', [0.4, 0.7, 1.4], 'sieve', '4start')
            await step(page, 7.0)
            await click(page, 'Next: weigh each sieve'); await step(page, 2.0)
            await play(page, 'Weigh the next sieve', [0.5, 1.3, 2.0, 2.6, 3.4, 4.2, 5.2, 6.2, 7.4, 8.4], 'sieve', '5weigh', 40)
            await play(page, 'Weigh the rest', [2.0, 6.0, 12.0, 20.0], 'sieve', '5rest', 90)
            st = await page.evaluate("() => ({ n:window.__test.psd.weighedN, step:window.__test.psd.step })")
            print('state', st)
            await click(page, 'See the results'); await step(page, 1.0)
            png = await page.screenshot(type='png'); Image.open(io.BytesIO(png)).convert('RGB').save(os.path.join(OUT, 'hands-sieve-6results.jpg'), quality=84)
        if which == 'bench':
            await page.evaluate("() => window.__test.openStation('bench')")
            for k in range(150):
                ok = await page.evaluate("() => { window.__test.simStep(1 / 30); return !!(window.__test.HANDS.fig && window.__test.HANDS.fig.mesh); }")
                if ok: break
                await page.wait_for_timeout(200)
            print('body loaded', ok, flush=True)
            await step(page, 1.0)
            await page.evaluate("() => { window.__test.STATIONS.bench.act('car'); }"); await step(page, 3.0)
            await click(page, 'Start building'); await step(page, 0.5)
            await play(page, 'Set the chassis on the stand', [0.4, 0.9, 1.4, 1.9], 'bench', 'c1chassis')
            await click(page, 'Next step'); await play(page, 'Tape on the straws', [0.4, 0.9, 1.5, 2.2, 2.9], 'bench', 'c2straws')
            await click(page, 'Next step'); await play(page, 'Slide in the axles', [0.5, 1.2, 2.0, 2.8], 'bench', 'c3axles')
            await click(page, 'Next step'); await play(page, 'Push on the wheels', [0.5, 1.2, 2.0, 3.0, 4.0, 5.0, 5.8], 'bench', 'c4wheels')
            await click(page, 'Next step'); await play(page, 'Hook up the rubber band', [0.4, 1.0, 1.5], 'bench', 'c5band')
            await click(page, 'Next step'); await play(page, 'Set on the body', [0.4, 1.0, 1.5, 2.0], 'bench', 'c6body')
            await click(page, 'Next step'); await play(page, 'Wind it up and let go', [0.5, 1.2, 1.8, 2.4, 3.0, 4.0], 'bench', 'c7drive')
            await step(page, 4.0)
            await click(page, 'Switch kit'); await step(page, 3.0)
            await click(page, 'Start building'); await step(page, 0.5)
            await play(page, 'Set down the base', [0.4, 0.9, 1.3, 1.8], 'bench', 'h1base')
            await click(page, 'Next step'); await play(page, 'Glue in the columns', [0.5, 1.1, 1.6, 2.2, 2.8], 'bench', 'h2cols')
            await click(page, 'Next step'); await play(page, 'Add the beams and floor', [0.5, 1.2, 2.0, 2.8, 3.6, 4.4], 'bench', 'h3beams')
            await click(page, 'Next step'); await play(page, 'Build the second story', [0.6, 1.6, 2.6, 3.6, 4.6, 5.6, 6.6], 'bench', 'h4story')
            await click(page, 'Next step'); await play(page, 'Glue on the bracing', [0.6, 1.4, 2.4, 3.4, 4.4, 5.2], 'bench', 'h5brace')
            await click(page, 'Next step'); await play(page, 'Shake the table', [0.5, 1.2, 2.0, 3.0, 4.5, 5.5], 'bench', 'h6shake')
            await click(page, 'Remove bracing'); await play(page, 'Shake it again', [1.5, 3.0], 'bench', 'h6shake2')
        if which == 'lab2':
            await page.evaluate("() => window.__test.openStation('titration')")
            for k in range(150):
                ok = await page.evaluate("() => { window.__test.simStep(1 / 30); return !!(window.__test.HANDS.fig && window.__test.HANDS.fig.mesh); }")
                if ok: break
                await page.wait_for_timeout(200)
            print('body loaded', ok, flush=True)
            await step(page, 1.0)
            await click(page, 'Start'); await step(page, 3.0)
            await play(page, 'Set it up', [0.5, 1.2, 2.0, 2.8, 3.8, 4.6, 5.4, 6.4], 'titr', '1setup')
            await click(page, 'Next: titrate'); await step(page, 2.0)
            await play(page, '+1 mL', [0.3, 0.6, 0.9, 1.3, 1.8, 2.3], 'titr', '2add1')
            for _ in range(8): await click(page, '+1 mL'); await step(page, 3.0)
            await play(page, '+1 drop', [0.3, 0.6, 0.9, 1.2], 'titr', '2drop')
            await page.evaluate("() => window.__test.openStation('pendulum')"); await step(page, 2.0)
            await click(page, 'Start'); await step(page, 3.0)
            await play(page, 'Pull back and release', [0.4, 0.9, 1.4, 1.9, 2.3, 2.8], 'pend', '1release')
            await step(page, 3.0)
            await page.evaluate("() => window.__test.pendSetLen(1.8)"); await step(page, 1.0)
            await page.evaluate("() => { window.__test.pend.run = false; }")
            await play(page, 'Pull back and release', [0.4, 0.9, 1.6, 2.3], 'pend', '2long')
        print(errs(logs))
        await b.close()
asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else 'sieve', sys.argv[2] if len(sys.argv) > 2 else 'desktop'))
