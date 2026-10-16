import asyncio
from harness import *
exec(open('func.py').read().split('QS = {')[0].split('from harness import *')[1])
async def main():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True, FAKE_AI)
        page.set_default_timeout(120000)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        await page.evaluate("window.__test.goView(window.__test.PLACES.find(p => p.id === 'rae').view())"); await page.wait_for_timeout(500)
        await page.click('#askBtn'); await page.wait_for_timeout(300)
        print('header:', await page.inner_text('#gSub'), '|', await page.inner_text('#gNote'))
        await page.fill('#gq', 'which ride has the best view of the campus?'); await page.click('#gSend'); await page.wait_for_timeout(2500)
        last = await page.evaluate("[...document.querySelectorAll('#gMsgs .msg.guide')].pop().innerText")
        print('AI reply:', last.replace('\n', ' | ')[:160])
        print('calls:', await page.evaluate("window.__calls.map(c => c.tier + '/' + c.cache + ' n=' + c.n)"), '| sys has yard:', await page.evaluate("window.__calls.length ? window.__calls[0].sys.slice(0, 60) : ''"))
        print('ride card after AI RIDE:', await page.evaluate("!document.querySelector('#rideCard').hidden"), await page.inner_text('#rcTitle'), '| guide closed:', await page.evaluate("document.querySelector('#guide').hidden"))
        await page.click('#rcCancel'); await page.wait_for_timeout(200)
        for mode in ['rate', 'deny']:
            await page.evaluate(f"window.__fakeMode = '{mode}'")
            if await page.evaluate("document.querySelector('#guide').hidden"): await page.click('#askBtn'); await page.wait_for_timeout(200)
            await page.fill('#gq', 'what would you pick if you were a fish, the coaster or the drop?'); await page.click('#gSend'); await page.wait_for_timeout(1200)
            last = await page.evaluate("[...document.querySelectorAll('#gMsgs .msg.guide')].pop().innerText")
            print(mode, '->', last.replace('\n', ' | ')[:170], '| ai on:', await page.evaluate("window.__test.chat.ai"))
        print(errs(logs))
        await b.close()
asyncio.run(main())
