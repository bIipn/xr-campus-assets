import asyncio, sys, base64
sys.argv = ['x', 'none']
exec(open('run.py').read().split("which = sys.argv")[0])
async def main():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        await page.click('#bEnter')
        for q, name in [('flood', 'q-flood')]:
            await page.click('#bSearch'); await page.fill('#q', q); await page.wait_for_timeout(150)
            await page.click('.result >> nth=0'); await page.wait_for_timeout(250)
            await page.screenshot(path=f'{OUT}/{name}-viewer.png')
            await page.click('#vClose'); await page.wait_for_timeout(250)
            await page.screenshot(path=f'{OUT}/{name}-scene.png')
        # hover tag over the frame in view
        await page.mouse.move(640, 300); await page.wait_for_timeout(300)
        await page.screenshot(path=f'{OUT}/q-hover.png')
        data = await page.evaluate("window.__ART['lantern-1900'].toDataURL('image/png')")
        open(f'{OUT}/art-lantern-1900.png', 'wb').write(base64.b64decode(data.split(',')[1]))
        print('\n'.join(l for l in logs if 'error' in l.lower()) or 'no errors')
        await b.close()
asyncio.run(main())
