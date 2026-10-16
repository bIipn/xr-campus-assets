import asyncio, time, sys
sys.argv=['x']
exec(open('run.py').read().split("async def run(mode):")[0])
async def main():
    t=time.time()
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
        print('launched', round(time.time()-t,1), flush=True)
        ctx = await b.new_context(viewport={'width':1280,'height':800})
        page = await ctx.new_page()
        logs=[]
        page.on('console', lambda m: logs.append(m.type+': '+m.text))
        page.on('pageerror', lambda e: logs.append('PAGEERROR: '+str(e)))
        await page.route('**/*', route)
        await page.goto('http://museum.test/index.html', wait_until='domcontentloaded')
        print('loaded', round(time.time()-t,1), flush=True)
        for i in range(20):
            await page.wait_for_timeout(1000)
            st = await page.evaluate("[document.querySelector('#introMeta').textContent, !!window.THREE, document.fonts ? document.fonts.status : 'n/a', Object.keys(window.__ART||{}).length]")
            print(i, st, flush=True)
            if 'galleries' in st[0]: break
        print('\n'.join(logs[:20]))
        await page.screenshot(path='shots/diag.png')
        print('shot', round(time.time()-t,1))
        await b.close()
asyncio.run(main())
