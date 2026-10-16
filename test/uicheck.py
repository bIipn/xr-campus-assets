import asyncio, os, sys, json
from harness import *
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'mobile', True)
        await page.tap('#bEnter'); await page.wait_for_timeout(500)
        await page.evaluate("() => window.__test.openBp('car', 0, { walk:false })"); await page.wait_for_timeout(900)
        r = await page.evaluate("() => ['#bpPrev', '#bpNext', '#bpOver', '#bpModel'].map((s) => { const e = document.querySelector(s); return s + ':' + (e.hidden ? 'hidden' : e.textContent); })")
        print('bp sel 0', r)
        await page.screenshot(path=os.path.join(OUT, 'ui-m-bp0.jpg'), type='jpeg', quality=80)
        await page.evaluate("() => window.__test.closeBp()")
        await page.evaluate("() => { const T = window.__test; T.openStation('diorama'); }"); await page.wait_for_timeout(900)
        await page.evaluate("() => { const b = [...document.querySelectorAll('#stBtns button')].find((x) => x.textContent.trim() === 'Add the next layer'); b && b.click(); }"); await page.wait_for_timeout(600)
        r = await page.evaluate("() => { const b = document.querySelector('#stBtns'); return { more:b.classList.contains('more'), sw:b.scrollWidth, cw:b.clientWidth }; }")
        print('station row', r)
        await page.screenshot(path=os.path.join(OUT, 'ui-m-st.jpg'), type='jpeg', quality=80)
        await page.evaluate("() => { const b = document.querySelector('#stBtns'); b.scrollLeft = b.scrollWidth; }"); await page.wait_for_timeout(300)
        r = await page.evaluate("() => document.querySelector('#stBtns').classList.contains('more')")
        print('scrolled to end, still fading:', r)
        print(errs(logs))
        await b.close()
asyncio.run(run())
