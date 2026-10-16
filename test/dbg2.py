import asyncio, os, sys
import harness
from harness import *
async def main():
    async with async_playwright() as p:
        html = wrapper()
        # reuse open_page but catch the timeout
        try:
            b, page, logs = await open_page(p, 'desktop', True)
            print('BOOTED')
            print(errs(logs))
            await b.close()
        except Exception as e:
            print('TIMEOUT', str(e)[:200])
asyncio.run(main())
