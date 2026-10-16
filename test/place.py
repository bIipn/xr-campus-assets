import asyncio, sys
sys.argv = ['x', 'none']
exec(open('run.py').read().split("which = sys.argv")[0])
wrapper = wrapper.replace('window.__test = { walkTo,', 'window.__test = { get guideRoot(){ return guideRoot; }, get guideHead(){ return guideHead; }, get camera(){ return camera; }, localAnswer, guide, walkTo,')

SPOTS = [(0.95, -3.6), (0.62, -3.8), (0.75, -4.3), (1.05, -4.9)]

async def main(mode):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, mode, True)
        await page.click('#bEnter') if mode == 'desktop' else await page.tap('#bEnter')
        await page.wait_for_timeout(300)
        for i, (x, z) in enumerate(SPOTS):
            await page.evaluate("""([x, z]) => { const r = window.__test.guideRoot; r.position.set(x, 0, z); r.rotation.y = Math.atan2(0 - x, -0.7 - z); window.__test.walkTo({x:0, z:-0.7}, {yaw:0, pitch:0.02}); }""", [x, z])
            await page.wait_for_timeout(350)
            await page.screenshot(path=f'{OUT}/place-{mode}-{i}.png')
        await b.close()

asyncio.run(main('desktop'))
asyncio.run(main('phone'))
