import asyncio, sys, json
sys.argv = ['x', 'none']
exec(open('run.py').read().split("which = sys.argv")[0])

wrapper = wrapper.replace('window.__test = { walkTo,', 'window.__test = { get guideRoot(){ return guideRoot; }, get guideHead(){ return guideHead; }, get camera(){ return camera; }, localAnswer, guide, walkTo,')
assert 'get guideRoot' in wrapper

FAKE_AI = r"""
window.__calls = [];
window.claude = { use: async (name) => {
  if (name !== 'sample') return null;
  const mode = window.__fakeMode || 'ok';
  const f = async (input, opts) => {
    window.__calls.push({ input, opts: { modelTier: opts.modelTier, cache: opts.cache } });
    if (window.__fakeMode === 'deny') { const e = new Error('no'); e.code = 'not_granted'; throw e; }
    if (window.__fakeMode === 'rate') { const e = new Error('slow down'); e.code = 'rate_limited'; throw e; }
    const full = 'The oldest thing here is the very first Courier, from 1897. Follow me and I will show you.\nITEMS: courier-1897, plat-1899\nGO: courier-1897';
    let acc = '';
    for (const part of full.match(/[\s\S]{1,18}/g)) { acc += part; opts.onText && opts.onText({ text: acc, delta: part }); await new Promise(r => setTimeout(r, 20)); }
    return { text: full, truncated: false };
  };
  return f;
} };
"""

async def text(page, sel):
    return await page.evaluate("(s) => [...document.querySelectorAll(s)].map(e => e.innerText.replace(/\\s+/g, ' ').trim())", sel)

async def screen_of(page, expr):
    return await page.evaluate("""(expr) => {
      const T = window.__test, v = new THREE.Vector3();
      const o = expr === 'head' ? T.guideHead : T.guideRoot;
      o.getWorldPosition(v); if (expr === 'body') v.y = 1.1;
      v.project(T.camera);
      const r = document.querySelector('#scene').getBoundingClientRect();
      return { x: r.left + (v.x + 1) / 2 * r.width, y: r.top + (1 - v.y) / 2 * r.height };
    }""", expr)

async def search_mode_desktop():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'desktop', True)
        await page.click('#bEnter'); await page.wait_for_timeout(400)
        await page.screenshot(path=f'{OUT}/g-desktop-01-start.png')
        # hover Margaret
        pt = await screen_of(page, 'body')
        await page.mouse.move(pt['x'], pt['y']); await page.wait_for_timeout(300)
        print('hover tag:', await text(page, '#tag'))
        await page.screenshot(path=f'{OUT}/g-desktop-02-hover.png')
        # click Margaret in 3D
        await page.mouse.click(pt['x'], pt['y']); await page.wait_for_timeout(300)
        print('panel open after 3D click:', await page.evaluate("!document.querySelector('#guide').hidden"))
        print('msgs:', await text(page, '.msg'))
        print('chips:', await text(page, '.chip'))
        await page.screenshot(path=f'{OUT}/g-desktop-03-open.png')
        # chip: take me to the oldest
        await page.click('.chip >> nth=0'); await page.wait_for_timeout(900)
        print('after chip0 msgs:', (await text(page, '.msg'))[-1])
        print('cam:', await page.evaluate("[window.__test.cam.x.toFixed(2), window.__test.cam.z.toFixed(2)]"))
        await page.screenshot(path=f'{OUT}/g-desktop-04-oldest.png')
        for q in ['Who worked at the mill?', 'What happened in 1937?', 'where is the library?', 'dinosaurs', 'take me to the rialto', 'flood', 'hello', 'thanks!', 'are you a real person?', 'Show me the railroad', 'when do the workshops open', 'what was the rialto']:
            await page.fill('#gq', q); await page.press('#gq', 'Enter'); await page.wait_for_timeout(800)
            last = (await text(page, '.msg.guide'))[-1]
            print(f'Q {q!r} ->', last[:220])
        print('cam after rialto etc:', await page.evaluate("[window.__test.cam.x.toFixed(2), window.__test.cam.z.toFixed(2)]"))
        await page.fill('#gq', 'Who worked at the mill?'); await page.press('#gq', 'Enter'); await page.wait_for_timeout(500)
        await page.screenshot(path=f'{OUT}/g-desktop-05-mill.png')
        # Take me there button on a card
        await page.click('.msg.guide >> nth=-1 >> .gcard >> nth=0 >> text=Take me there'); await page.wait_for_timeout(800)
        print('cam after take me there:', await page.evaluate("[window.__test.cam.x.toFixed(2), window.__test.cam.z.toFixed(2)]"))
        await page.screenshot(path=f'{OUT}/g-desktop-06-there.png')
        # Escape closes
        await page.focus('#gq'); await page.keyboard.press('Escape'); await page.wait_for_timeout(200)
        print('panel hidden after Esc:', await page.evaluate("document.querySelector('#guide').hidden"))
        # Search panel closes guide
        await page.click('#askBtn'); await page.wait_for_timeout(200)
        await page.click('#bSearch'); await page.wait_for_timeout(200)
        print('guide hidden after search:', await page.evaluate("document.querySelector('#guide').hidden"))
        await page.keyboard.press('Escape')
        # walk back to lobby and look at directory
        await page.evaluate("window.__test.walkTo({x:-2.6,z:-1.6},{yaw:0.55,pitch:0.02})"); await page.wait_for_timeout(400)
        await page.screenshot(path=f'{OUT}/g-desktop-07-directory.png')
        # Head tracking: stand to the side and check head turned
        await page.evaluate("window.__test.walkTo({x:3.6,z:-1.2},{yaw:-0.6,pitch:0})"); await page.wait_for_timeout(1500)
        print('head rot:', await page.evaluate("window.__test.guideHead.rotation.y.toFixed(3)"))
        await page.screenshot(path=f'{OUT}/g-desktop-08-side.png')
        print('desktop', '\n'.join(l for l in logs if 'error' in l.lower() or 'warn' in l.lower()) or 'no console errors')
        await b.close()

async def ai_mode(mode):
    async with async_playwright() as p:
        b = await p.chromium.launch(args=ARGS)
        ctx = await b.new_context(viewport={'width': 1280, 'height': 800}, reduced_motion='reduce')
        page = await ctx.new_page()
        logs = []
        page.on('console', lambda m: logs.append(m.type + ': ' + m.text))
        page.on('pageerror', lambda e: logs.append('PAGEERROR: ' + str(e)))
        await page.add_init_script(FAKE_AI + (f"window.__fakeMode = '{mode}';"))
        await page.route('**/*', route)
        await page.goto('http://museum.test/index.html')
        await page.wait_for_function("!document.querySelector('#bEnter').disabled", timeout=30000)
        await page.wait_for_timeout(300)
        await page.click('#bEnter'); await page.wait_for_timeout(200)
        print(mode, 'guide mode:', await page.evaluate("window.__test.guide.mode"))
        await page.click('#askBtn'); await page.wait_for_timeout(200)
        print(mode, 'sub:', await text(page, '#gSub'), 'note:', await text(page, '#gNote'))
        print(mode, 'greeting:', (await text(page, '.msg'))[0])
        await page.fill('#gq', 'Take me to the oldest thing'); await page.press('#gq', 'Enter')
        await page.wait_for_timeout(120)
        print(mode, 'mid-stream:', (await text(page, '.msg.guide'))[-1], '| send btn:', await text(page, '#gSend'))
        await page.wait_for_timeout(1400)
        print(mode, 'final:', (await text(page, '.msg.guide'))[-1])
        print(mode, 'cam:', await page.evaluate("[window.__test.cam.x.toFixed(2), window.__test.cam.z.toFixed(2)]"), 'mode now:', await page.evaluate("window.__test.guide.mode"))
        calls = await page.evaluate("window.__calls")
        if calls:
            c = calls[0]
            print(mode, 'turns:', len(c['input']), 'roles:', [t['role'] for t in c['input']], 'opts:', c['opts'])
            print(mode, 'rules head:', c['input'][0]['content'][:160].replace('\n', ' / '))
            print(mode, 'rules len:', len(c['input'][0]['content']))
        await page.screenshot(path=f'{OUT}/g-ai-{mode}.png')
        if mode == 'ok':
            await page.fill('#gq', 'and the mill?'); await page.press('#gq', 'Enter'); await page.wait_for_timeout(1500)
            calls = await page.evaluate("window.__calls")
            print(mode, 'second call roles:', [t['role'] for t in calls[1]['input']])
        print(mode, '\n'.join(l for l in logs if 'error' in l.lower() or 'warn' in l.lower()) or 'no console errors')
        await b.close()

async def phone():
    async with async_playwright() as p:
        b, page, logs = await open_page(p, 'phone', True)
        await page.wait_for_timeout(300)
        await page.screenshot(path=f'{OUT}/g-phone-01-intro.png')
        await page.tap('#bEnter'); await page.wait_for_timeout(400)
        await page.screenshot(path=f'{OUT}/g-phone-02-start.png')
        await page.tap('#askBtn'); await page.wait_for_timeout(300)
        await page.screenshot(path=f'{OUT}/g-phone-03-open.png')
        await page.tap('.chip >> nth=2'); await page.wait_for_timeout(600)
        await page.screenshot(path=f'{OUT}/g-phone-04-mill.png')
        await page.tap('.msg.guide >> nth=-1 >> .gcard >> nth=0 >> text=Take me there'); await page.wait_for_timeout(800)
        print('phone panel hidden after go:', await page.evaluate("document.querySelector('#guide').hidden"))
        await page.screenshot(path=f'{OUT}/g-phone-05-there.png')
        # tap Margaret in 3D after walking back
        await page.evaluate("window.__test.walkTo({x:0,z:-0.9},{yaw:0,pitch:0.02})"); await page.wait_for_timeout(500)
        pt = await screen_of(page, 'body')
        await page.touchscreen.tap(pt['x'], pt['y']); await page.wait_for_timeout(400)
        print('phone panel open after 3D tap:', await page.evaluate("!document.querySelector('#guide').hidden"))
        await page.screenshot(path=f'{OUT}/g-phone-06-tap.png')
        print('phone', '\n'.join(l for l in logs if 'error' in l.lower() or 'warn' in l.lower()) or 'no console errors')
        await b.close()

which = sys.argv_real[1] if False else None
import os
W = os.environ.get('WHICH', 'all')
if W in ('all', 'desktop'): asyncio.run(search_mode_desktop())
if W in ('all', 'ai'):
    asyncio.run(ai_mode('ok'))
    asyncio.run(ai_mode('deny'))
    asyncio.run(ai_mode('rate'))
if W in ('all', 'phone'): asyncio.run(phone())
