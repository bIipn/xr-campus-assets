import asyncio, sys
sys.argv = ['x', 'none']
exec(open('run.py').read().split("which = sys.argv")[0])
wrapper = wrapper.replace('window.__test = { walkTo,', 'window.__test = { get guideRoot(){ return guideRoot; }, get guideHead(){ return guideHead; }, get camera(){ return camera; }, walkTo,')
async def main():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        await page.evaluate("window.__test.walkTo({x:3.0,z:-1.5},{yaw:0.748,pitch:-0.05})"); await page.wait_for_timeout(1800)
        print('head', await page.evaluate("window.__test.guideHead.rotation.y.toFixed(3)"))
        await page.screenshot(path=f'{OUT}/g-head-side.png')
        await page.evaluate("window.__test.walkTo({x:-1.2,z:-2.2},{yaw:-0.75,pitch:-0.05})"); await page.wait_for_timeout(1800)
        print('head', await page.evaluate("window.__test.guideHead.rotation.y.toFixed(3)"))
        await page.screenshot(path=f'{OUT}/g-head-left.png')
        print('\n'.join(l for l in logs if 'error' in l.lower()) or 'no errors')
        await b.close()
asyncio.run(main())
