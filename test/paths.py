import asyncio, os, sys, json
from harness import *
async def main(mode):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, mode, True)
        await (page.click('#bEnter') if mode == 'desktop' else page.tap('#bEnter')); await page.wait_for_timeout(400)
        r = await page.evaluate("""() => { const T = window.__test, out = [];
          const chk = (name, v) => { const p = T.planPath({ x:23, z:-3 }, v), last = p[p.length - 1]; out.push([name, T.freeAt(v.x, v.z, 0), Math.hypot(last.x - v.x, last.z - v.z) < 0.01, T.roomAt(v.x, v.z).id]); };
          for (let s = 0; s <= 6; s++){ T.psd.step = s; chk('sieve' + s, T.STATIONS.sieve.view()); } T.psd.step = 0;
          for (const k of ['titration', 'pendulum', 'bench', 'diorama']) chk(k, T.STATIONS[k].view());
          for (const id of T.BP_ORDER) chk('bp-' + id, T.bpViewFor(id));
          for (const p of T.PLACES) if (['lab', 'blueprints', 'worldroom', 'studio', 'sieve', 'titration', 'pendulum', 'modelbench', 'diorama'].includes(p.id) || p.id.startsWith('bp-')) chk('place-' + p.id, p.view());
          return out; }""")
        bad = [x for x in r if not (x[1] and x[2])]
        print(mode, 'checked', len(r), 'bad:', bad)
        await b.close()
asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else 'desktop'))
