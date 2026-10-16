"""Staff answers, search and navigation for the new rooms. Usage: CAMPUS_GFX=low python3 func2.py"""
import asyncio, os, sys, json
from harness import *

QS = [
  ('hale', 'What workshops are there?'),
  ('hale', 'Give me a blank canvas'),
  ('hale', 'How do blueprints work?'),
  ('hale', 'What does a radiator do?'),
  ('hale', 'What is a swing bearing?'),
  ('hale', 'how does the sieve test work'),
  ('hale', 'what is the AFS grain fineness number'),
  ('hale', 'how does titration work'),
  ('hale', 'how do I measure gravity'),
  ('hale', 'start the sieve test'),
  ('hale', 'open the bridge blueprint'),
  ('hale', 'build a model car'),
  ('hale', 'how was this made'),
  ('hale', 'take me to the science lab'),
  ('hale', 'where is the blueprint lab'),
  ('hale', 'what does the GPU do'),
  ('hale', 'why do houses have headers over windows'),
  ('margaret', 'take me to room 104'),
  ('margaret', 'what can I do in the school'),
  ('rae', 'where are the hidden tokens?'),
  ('rosa', 'recommend a book about making games'),
]

async def run():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        await page.click('#bEnter'); await page.wait_for_timeout(400)
        for who, q in QS:
            r = await page.evaluate("([w, q]) => { const r = window.__test.presetAnswer(w, q); return { text:r.text, conf:r.conf, action:r.action || null, go:r.go ? (r.go.p ? r.go.p.id : r.go.it.id) : null, cards:(r.cards || []).map((c) => c.type + ':' + (c.id || (c.p && c.p.id) || (c.b && c.b.id) || (c.it && c.it.id) || '') + (c.part != null ? '#' + c.part : '')) }; }", [who, q])
            print(who.ljust(8), q.ljust(42), '->', r['text'][:150], '|', r['action'], r['go'], r['cards'], 'conf', r['conf'])
        # search
        for q in ['radiator', 'titration', 'pendulum', 'sieve', 'truss', 'blank', 'gpu']:
            await page.evaluate("(q) => window.__test.openSearch(q)", q)
            res = await page.evaluate("() => [...document.querySelectorAll('#sResults .result')].slice(0, 6).map((b) => b.querySelector('.rk').textContent + ' / ' + b.querySelector('.rt').textContent)")
            print('search', q.ljust(10), res)
        await page.evaluate("() => window.__test.closeSearch()")
        # paths into each room from the lobby
        for name, tgt in [('lab', {'x': 29, 'z': -8}), ('blueprint', {'x': 18, 'z': 4}), ('world', {'x': 29, 'z': 1}), ('sieve view', None), ('bench view', None), ('diorama view', None), ('pendulum view', None), ('titration view', None)]:
            if tgt is None:
                st = name.split()[0]
                tgt = await page.evaluate("(s) => window.__test.STATIONS[s].view()", st)
            r = await page.evaluate("(t) => { const T = window.__test; const p = T.planPath({ x:0, z:-2 }, t); const last = p[p.length - 1]; return { n:p.length, free:T.freeAt(t.x, t.z, 0), walk:T.walkable(t.x, t.z), end:[+last.x.toFixed(2), +last.z.toFixed(2)], room:T.roomAt(t.x, t.z).id }; }", tgt)
            print('path', name.ljust(14), json.dumps(tgt), r)
        # tokens reachable/tappable: distance to nearest free cell
        r = await page.evaluate("() => window.__test.TOKENS.filter(t => t.at).map(t => t.id + ':' + window.__test.roomAt(t.at[0], t.at[2]).id)")
        print('tokens', r)
        print(errs(logs))
        await b.close()

asyncio.run(run())
