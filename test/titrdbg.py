"""Why does titration stall in the minified build? Usage: CAMPUS_MIN=1 CAMPUS_GFX=low python3 titrdbg.py"""
import asyncio, os, sys, json
from harness import *

STATE = """() => { const T = window.__test, t = T.titr; return { step:t.step, added:t.added, v0:t.v0, Ca:t.Ca, veq:+(t.Ca * t.Vacid / t.Cb).toFixed(3), ended:t.ended, title:document.querySelector('#stTitle').textContent,
  btns:[...document.querySelectorAll('#stBtns button')].map((b) => b.textContent.trim() + (b.disabled ? '(off)' : '')), toast:(document.querySelector('#toast') || {}).textContent }; }"""

async def click(page, label):
    return await page.evaluate("""(label) => { const b = [...document.querySelectorAll('#stBtns button')].find((x) => x.textContent.trim() === label); if (!b) return 'missing'; if (b.disabled) return 'disabled'; b.click(); return 'ok'; }""", label)

async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        await page.click('#bEnter'); await page.wait_for_timeout(400)
        await page.evaluate("() => window.__test.openStation('titration')"); await page.wait_for_timeout(500)
        print('open', json.dumps(await page.evaluate(STATE)))
        for lab in ['Start', 'Set it up', 'Next: titrate']:
            print(lab, await click(page, lab)); await page.wait_for_timeout(150)
        s = await page.evaluate(STATE); print('titrate', json.dumps(s))
        veq = s['veq']
        res = []
        for _ in range(int(veq) - 1): res.append(await click(page, '+1 mL')); await page.wait_for_timeout(60)
        print('after +1 mL x', len(res), set(res), json.dumps(await page.evaluate(STATE)))
        for _ in range(40):
            s = await page.evaluate(STATE)
            if s['added'] >= veq - 0.25: break
            r = await click(page, '+0.1 mL'); await page.wait_for_timeout(60)
            if r != 'ok': print('  +0.1', r)
        print('after +0.1', json.dumps(await page.evaluate(STATE)))
        for _ in range(12):
            s = await page.evaluate(STATE)
            if s['added'] >= veq: break
            r = await click(page, '+1 drop'); await page.wait_for_timeout(60)
            if r != 'ok': print('  drop', r)
        s = await page.evaluate(STATE); print('after drops', json.dumps(s))
        ph = await page.evaluate("() => window.__test.titr ? null : null")
        print('record', await click(page, 'Record endpoint')); await page.wait_for_timeout(300)
        print('final', json.dumps(await page.evaluate(STATE)))
        print(errs(logs))
        await b.close()
asyncio.run(run())
