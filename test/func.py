import asyncio, sys, json, math
from harness import *

FAKE_AI = r"""
window.__calls = [];
window.claude = { use: async (name) => {
  if (name === 'downloads') return { save: async () => ({}) };
  if (name !== 'sample') return null;
  return async (input, opts) => {
    window.__calls.push({ n: input.length, tier: opts.modelTier, cache: opts.cache, sys: input[0].content.slice(0, 120) });
    if (window.__fakeMode === 'deny') { const e = new Error('no'); e.code = 'not_granted'; throw e; }
    if (window.__fakeMode === 'rate') { const e = new Error('slow'); e.code = 'rate_limited'; throw e; }
    const full = 'Sure thing! The Sky Drop is a great pick if you like big views.\nITEMS: none\nBOOKS: none\nRIDE: drop';
    let acc = ''; for (const part of full.match(/[\s\S]{1,16}/g)) { acc += part; opts.onText && opts.onText({ text: acc, delta: part }); await new Promise(r => setTimeout(r, 10)); }
    return { text: full, truncated: false };
  };
} };
"""

QS = {
  'rae': ['hi', 'Ride the coaster', 'What’s on the Ocean Dive?', 'Where are the hidden tokens?', 'Is it scary?', 'how fast is the coaster', 'how tall is the sky drop', 'how many rides are there', 'what badges can I get', 'take me to the sky drop', 'what can I do at recess', 'tell me a joke', 'who are you', 'is the dive scary', 'start the dive', 'where is the library', 'what is XRLibraries'],
  'margaret': ['what is this place', 'take me to the playground', 'where is the roller coaster', 'how many exhibits are there', 'what is project sandi'],
  'rosa': ['recommend a book about oceans', 'where is the recess yard', 'what is the difference between VR and AR'],
  'hale': ['start painting', 'what other workshops are there', 'can I go on a ride']
}

async def main():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True, FAKE_AI)
        page.set_default_timeout(120000)
        await page.click('#bEnter'); await page.wait_for_timeout(300)
        # 1. Preset batteries
        for sid, qs in QS.items():
            for q in qs:
                r = await page.evaluate("([s, q]) => { const r = window.__test.presetAnswer(s, q); return { t:r.text, c:r.conf, cards:(r.cards||[]).map(c => c.type + ':' + (c.id || (c.it && c.it.id) || (c.b && c.b.id) || (c.p && c.p.id) || '')), a:r.action || null, go:r.go ? (r.go.p ? r.go.p.id : r.go.it.id) : null }; }", [sid, q])
                print(f"[{sid}] {q!r} -> conf {r['c']} action {r['a']} go {r['go']} cards {r['cards']}\n      {r['t'][:170]}")
        # 2. Nav: every place reachable from the lobby, and paths stay walkable
        res = await page.evaluate("""() => { const T = window.__test, out = []; const from = { x:0, z:-2.2 };
          for (const pl of T.PLACES){ const v = pl.view(); if (!v) { out.push(pl.id + ': no view'); continue; }
            const tgt = T.safeTarget({ x:v.x, z:v.z }), path = T.planPath(from, tgt); let ok = T.freeAt(tgt.x, tgt.z, 0), prev = from, bad = 0;
            for (const q of path){ const L = Math.hypot(q.x - prev.x, q.z - prev.z), n = Math.max(1, Math.ceil(L / 0.1)); for (let k = 0; k <= n; k++){ const x = prev.x + (q.x - prev.x) * k / n, z = prev.z + (q.z - prev.z) * k / n; if (!T.walkable(x, z)) bad++; } prev = q; }
            const end = path[path.length - 1], d = Math.hypot(end.x - tgt.x, end.z - tgt.z);
            if (!ok || bad || d > 0.3) out.push(pl.id + ': ok=' + ok + ' bad=' + bad + ' endgap=' + d.toFixed(2) + ' view=' + JSON.stringify([v.x, v.z]) + ' tgt=' + JSON.stringify([+tgt.x.toFixed(2), +tgt.z.toFixed(2)]));
          }
          return out; }""")
        print('NAV problems:', res or 'none')
        nogo = await page.evaluate("() => { const T = window.__test; return [T.walkable(52, -9.5), T.walkable(60, -20), T.walkable(52, -7.6), T.walkable(78, 13), T.walkable(36, -3), T.walkable(34, -3), T.walkable(33.2, -3)]; }")
        print('walkable checks [gate inside NOGO, coaster zone, plaza edge, tower(obst ignored), yard door, door band, corridor end]:', nogo)
        # 3. Simulated rides (no rendering), checking speeds, tokens and endings
        sim = await page.evaluate("""async () => { const T = window.__test, out = {};
          const run = async (id, gentle, maxT) => {
            T.startRide(id, gentle); await new Promise(r => setTimeout(r, 200));
            let t = 0, vmin = 99, vmax = 0, loopV = null, phases = new Set(); const C = T.COASTER, lt = C.iLoopTop * C.ds;
            while (T.ride.on && !T.ride.exiting && t < maxT){ T.rideUpdate(0.05); if (id === 'dive') T.animateDive(0.05, T.camera.position); t += 0.05; phases.add(T.ride.phase);
              if (id === 'coaster' && T.ride.phase === 'run' && T.ride.s > C.iCrest * C.ds + 2 && T.ride.s < C.L - 25){ vmin = Math.min(vmin, T.ride.v); vmax = Math.max(vmax, T.ride.v); if (loopV === null && T.ride.s >= lt) loopV = T.ride.v; } }
            await new Promise(r => setTimeout(r, 300));
            return { simTime:+t.toFixed(1), phases:[...phases], vmin:+vmin.toFixed(2), vmax:+vmax.toFixed(2), loopTopV:loopV && +loopV.toFixed(2), on:T.ride.on };
          };
          out.coaster = await run('coaster', false, 120);
          out.coasterGentle = await run('coaster', true, 200);
          out.drop = await run('drop', false, 60);
          out.dive = await run('dive', false, 200);
          out.tokens = [...T.prog.tokens]; out.badges = [...T.prog.badges]; out.cam = [T.cam.x, T.cam.z, T.roomAt(T.cam.x, T.cam.z).id];
          return out; }""")
        print('RIDES', json.dumps(sim, indent=1))
        # 4. Rae chat: chip -> ride card; AI path -> RIDE: drop
        await page.evaluate("window.__test.goView(window.__test.PLACES.find(p => p.id === 'rae').view())"); await page.wait_for_timeout(500)
        print('fab:', await page.inner_text('#askName'))
        await page.click('#askBtn'); await page.wait_for_timeout(300)
        print('greet:', (await page.inner_text('#gMsgs'))[:140].replace('\n', ' '))
        print('chips:', await page.evaluate("[...document.querySelectorAll('#gChips .chip')].map(c => c.textContent)"))
        await page.click('#gChips .chip >> nth=0'); await page.wait_for_timeout(1200)
        print('ride card open after chip:', await page.evaluate("!document.querySelector('#rideCard').hidden"), await page.inner_text('#rcTitle'))
        await shot(page, 'd-f01-ridecard-from-chat')
        await page.click('#rcCancel'); await page.wait_for_timeout(200)
        await page.click('#askBtn'); await page.wait_for_timeout(300)
        await page.fill('#gq', 'my friend says the dome is boring, which ride has the best view of the campus?'); await page.click('#gSend'); await page.wait_for_timeout(1800)
        last = await page.evaluate("[...document.querySelectorAll('#gMsgs .msg.guide')].pop().innerText")
        print('AI reply:', last.replace('\n', ' | ')[:200]); print('calls:', await page.evaluate('window.__calls.length'), await page.evaluate("window.__calls.map(c => c.tier + '/' + c.cache)"))
        print('ride card after AI RIDE:', await page.evaluate("!document.querySelector('#rideCard').hidden"), await page.inner_text('#rcTitle'))
        await page.keyboard.press('Escape'); await page.wait_for_timeout(200)
        for mode in ['rate', 'deny']:
            await page.evaluate(f"window.__fakeMode = '{mode}'")
            if await page.evaluate("document.querySelector('#guide').hidden"): await page.click('#askBtn'); await page.wait_for_timeout(200)
            await page.fill('#gq', 'what would you pick if you were a fish, the coaster or the drop?'); await page.click('#gSend'); await page.wait_for_timeout(900)
            last = await page.evaluate("[...document.querySelectorAll('#gMsgs .msg.guide')].pop().innerText")
            print(mode, '->', last.replace('\n', ' | ')[:160], '| ai on:', await page.evaluate("window.__test.chat.ai"))
        await page.keyboard.press('Escape'); await page.wait_for_timeout(200)
        # 5. Tokens by tapping and the badges panel
        await page.evaluate("window.__test.goView({ x:55.2, z:19.0, yaw:Math.PI, pitch:-0.45 })"); await page.wait_for_timeout(600)
        await shot(page, 'd-f02-yard-token')
        tok = await page.evaluate("""() => { const T = window.__test, g = T.TOKEN_MESH['t-yard'].g, v = g.position.clone().project(T.camera); return [(v.x + 1) / 2 * innerWidth, (1 - v.y) / 2 * innerHeight, g.visible]; }""")
        print('yard token on screen at', tok)
        await page.mouse.click(tok[0], tok[1]); await page.wait_for_timeout(500)
        print('t-yard collected:', await page.evaluate("window.__test.prog.tokens.has('t-yard')"), '| toast:', await page.inner_text('#toast'))
        await page.click('#bBadges'); await page.wait_for_timeout(300)
        await shot(page, 'd-f03-badges')
        await page.click('#bgClose'); await page.wait_for_timeout(200)
        # 6. Bookworm and explorer
        await page.evaluate("() => { const T = window.__test; T.openBook(T.BOOKS[0], 1); }"); await page.wait_for_timeout(200)
        for i in range(4): await page.click('#rdNext'); await page.wait_for_timeout(120)
        await page.click('#rdClose')
        for i in range(5): await page.evaluate(f"window.__test.openItem(window.__test.ITEMS[{i}], {{ walk:false }})")
        await page.click('#vClose'); await page.wait_for_timeout(200)
        print('badges now:', await page.evaluate("[...window.__test.prog.badges]"))
        # 7. Escape ends a ride
        await page.evaluate("window.__test.startRide('drop', true)"); await page.wait_for_timeout(300)
        print('riding:', await page.evaluate("window.__test.ride.on"), '| hud visible:', await page.evaluate("!document.querySelector('#rideHud').hidden"), '| hud hidden:', await page.evaluate("getComputedStyle(document.querySelector('.hud')).display"))
        await page.keyboard.press('Escape'); await page.wait_for_timeout(400)
        print('after Escape riding:', await page.evaluate("window.__test.ride.on"), '| cam room:', await page.evaluate("window.__test.roomAt(window.__test.cam.x, window.__test.cam.z).id"))
        print(errs(logs))
        await b.close()

asyncio.run(main())
