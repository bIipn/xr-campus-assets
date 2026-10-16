"""Clean stills of the hands-on stations (no debug overlay): a 2x2 sheet for Ev.
Usage: python3 stills.py  -> shots2/classrooms_hands.jpg"""
import asyncio, os, io
from harness import *
from PIL import Image
HIDE = '#hint,#tag,#toast,#award,#fade{display:none!important}'

async def click(page, label):
    ok = await page.evaluate("""(label) => { const b = [...document.querySelectorAll('#stBtns button')].find((x) => x.textContent.trim() === label); if (!b) return 'missing: ' + label + ' | have: ' + [...document.querySelectorAll('#stBtns button')].map((x) => x.textContent.trim() + (x.disabled ? '(off)' : '')).join(', '); if (b.disabled) return 'disabled: ' + label; b.click(); return 'ok'; }""", label)
    if ok != 'ok': print('  !!', ok, flush=True)
    return ok == 'ok'

async def step(page, dt):
    await page.evaluate("""(dt) => { const T = window.__test; const n = Math.max(1, Math.round(dt * 30)); for (let i = 0; i < n; i++) T.simStep(1 / 30); T.frameOnce(); }""", dt)

async def skip(page, label):
    """Click a clip button, then let the clip finish instantly (what the Skip ahead button does)"""
    if not await click(page, label): return
    await step(page, 0.2)
    await page.evaluate("() => { const T = window.__test; T.handsFinish(); }")
    await step(page, 0.6)

async def shoot(page, label, t):
    if not await click(page, label): return None
    await step(page, t)
    return Image.open(io.BytesIO(await page.screenshot(type='png'))).convert('RGB')

async def body(page, station):
    await page.evaluate("(s) => { const T = window.__test; if (T.handsBusy()) T.handsFinish(); T.openStation(s); }", station)
    for k in range(200):
        ok = await page.evaluate("() => { window.__test.simStep(1 / 30); return !!(window.__test.HANDS.fig && window.__test.HANDS.fig.mesh); }")
        if ok: break
        await page.wait_for_timeout(150)
    await step(page, 1.5)

async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', False)
        page.set_default_timeout(600000)
        await page.click('#bEnter'); await page.wait_for_timeout(400)
        await page.add_style_tag(content=HIDE)
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
        shots = {}
        ONLY = os.environ.get('ONLY')
        if ONLY:
            for k in ['sieve', 'bench', 'titr', 'pend']:
                fp = os.path.join(OUT, 'still_%s.jpg' % k)
                if k != ONLY and os.path.isfile(fp): shots[k] = Image.open(fp).convert('RGB')
        if not ONLY or ONLY == 'sieve':
          # Sieve: pour the split, dried, weighed sample onto the stacked sieves
          await body(page, 'sieve')
          await click(page, 'Start the test'); await step(page, 2.5)
          await skip(page, 'Pour it through the splitter'); await skip(page, 'Split it again')
          await click(page, 'Next: dry and weigh'); await step(page, 2.0)
          await skip(page, 'Dry it in the oven'); await skip(page, 'Tare the balance'); await skip(page, 'Pour the sample into the dish')
          await click(page, 'Next: stack the sieves'); await step(page, 2.0)
          await skip(page, 'Stack the sieves')
          await click(page, 'Next: shake'); await step(page, 2.5)
          shots['sieve'] = await shoot(page, 'Pour the sample onto the top sieve', 4.4)
        if not ONLY or ONLY == 'bench':
          # Bench: the balsa house on the shake table
          await body(page, 'bench')
          await page.evaluate("() => { window.__test.STATIONS.bench.act('house'); }"); await step(page, 3.0)
          await click(page, 'Start building'); await step(page, 0.5)
          for lab in ['Set down the base', 'Glue in the columns', 'Add the beams and floor', 'Build the second story', 'Glue on the bracing']:
              await skip(page, lab); await click(page, 'Next step'); await step(page, 0.3)
          shots['bench'] = await shoot(page, 'Shake the table', 2.2)
        if not ONLY or ONLY == 'titr':
          # Titration: turning the stopcock
          await body(page, 'titration')
          await click(page, 'Start'); await step(page, 2.5)
          await skip(page, 'Set it up')
          await click(page, 'Next: titrate'); await step(page, 2.0)
          for _ in range(6): await skip(page, '+1 mL')
          shots['titr'] = await shoot(page, '+1 mL', 1.0)
        if not ONLY or ONLY == 'pend':
          # Pendulum: pulling the bob back
          await body(page, 'pendulum')
          await click(page, 'Start'); await step(page, 3.0)
          print('pend', await page.evaluate("() => { const T = window.__test; return { run:T.pend.run, busy:T.handsBusy(), btns:[...document.querySelectorAll('#stBtns button')].map((x) => x.textContent.trim() + (x.disabled ? '(off)' : '')) }; }"))
          await page.evaluate("() => { window.__test.pend.run = false; }"); await step(page, 0.5)
          shots['pend'] = await shoot(page, 'Pull back and release', float(os.environ.get('PT', '2.0')))
        print(errs(logs))
        await b.close()
    order = ['sieve', 'bench', 'titr', 'pend']
    W, H = 640, 400
    sheet = Image.new('RGB', (W * 2 + 6, H * 2 + 6), (18, 18, 22))
    for i, k in enumerate(order):
        im = shots.get(k)
        if im is None: continue
        im.resize((W, H), Image.LANCZOS)
        sheet.paste(im.resize((W, H), Image.LANCZOS), ((i % 2) * (W + 6), (i // 2) * (H + 6)))
        im.save(os.path.join(OUT, 'still_%s.jpg' % k), quality=88)
    fn = os.path.join(OUT, 'classrooms_hands.jpg'); sheet.save(fn, quality=88); print('sheet', fn)
asyncio.run(run())
