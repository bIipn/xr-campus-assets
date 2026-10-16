import asyncio, os, sys, json
from harness import *
QS = [('rae', 'can I kick the ball?'), ('rae', 'where is the soccer goal'), ('rae', 'take me to the block tower'), ('margaret', 'what are the goals of xrlibraries'),
      ('rae', 'how do the swings work'), ('hale', 'how do I move around'), ('rae', 'is there physics'), ('rosa', 'do you have books about blocks')]
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        for sid, q in QS:
            r = await page.evaluate("([s, q]) => { const r = window.__test.presetAnswer(s, q); return { t:r.text, c:r.conf, cards:(r.cards||[]).map(c => c.type + ':' + (c.id || (c.it && c.it.id) || (c.b && c.b.id) || (c.p && c.p.id) || '')), go:r.go ? (r.go.p ? r.go.p.id : r.go.it.id) : null }; }", [sid, q])
            print('[%s] %r -> %s go=%s\n      %s' % (sid, q, r['cards'], r['go'], r['t'][:220]))
        print(errs(logs))
        await b.close()
asyncio.run(run())
