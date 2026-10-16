"""Guide answers about the Wax Hall and XRLibraries history."""
import asyncio, os, sys, json
from harness import *
QS = [('margaret', 'When did XRLibraries start?'), ('margaret', 'Take me to the Wax Hall'), ('margaret', 'what are the wax figures'), ('margaret', 'tell me the history of xrlibraries'),
      ('margaret', 'how many scenes are in the wax hall'), ('rosa', 'where is the living history hall'), ('margaret', 'where is the pollinators scene'), ('margaret', 'what happened in 2019')]
async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        for sid, q in QS:
            r = await page.evaluate("([s, q]) => { const r = window.__test.presetAnswer(s, q); return { t:r.text, c:r.conf, cards:(r.cards||[]).map(c => c.type + ':' + (c.id || (c.it && c.it.id) || (c.p && c.p.id) || '')), go:r.go ? (r.go.p ? r.go.p.id : r.go.it.id) : null }; }", [sid, q])
            print(f"[{sid}] {q!r} -> conf {r['c']} go {r['go']} cards {r['cards'][:4]}\n      {r['t'][:230]}", flush=True)
        hits = await page.evaluate("() => { const T = window.__test; T.openSearch('wax'); return [...document.querySelectorAll('#sResults li, #sList li, .sres li')].length; }")
        print('search "wax" results:', hits)
        print(errs(logs))
        await b.close()
asyncio.run(run())
