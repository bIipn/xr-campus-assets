"""A/B of the renderer's tone mapping (ACES vs AgX) at a few campus views -> shots2/tone_<name>.jpg (ACES left, AgX right)."""
import asyncio, os, io, sys
from harness import *
from PIL import Image
HIDE = '#hint,#tag,#toast,#award,#fade,#hud,#topbar,#map,#rosa{display:none!important}'
VIEWS = [
  ('lobby', {'x':0, 'z':-2.5, 'yaw':1.25, 'pitch':0.05}),
  ('hall-lib', {'x':-6.8, 'z':-3, 'yaw':1.5708, 'pitch':0.04}),
  ('window', {'x':-13.4, 'z':-3, 'yaw':1.5708, 'pitch':0.08}),
  ('stacks', {'x':-22.0, 'z':-2.0, 'yaw':2.356, 'pitch':-0.05}),
  ('school', 'place:school'),
  ('hale', {'x':18.7, 'z':-7.6, 'yaw':0.42, 'pitch':0}),
  ('sculpture', 'place:sculpture'),
]
SET = """(mode) => { const T = window.__test, THREE = T.THREE, r = T.renderer;
  r.toneMapping = mode === 'agx' ? THREE.AgXToneMapping : THREE.ACESFilmicToneMapping;
  T.scene.traverse((o) => { if (o.material){ const ms = Array.isArray(o.material) ? o.material : [o.material]; for (const m of ms) m.needsUpdate = true; } });
  for (let i = 0; i < 3; i++) T.frameOnce(); }"""
async def run(mode):
    async with async_playwright() as p:
        b, page, logs = await open_page(p, mode, False)
        page.set_default_timeout(600000)
        await page.click('#bEnter'); await page.wait_for_timeout(400)
        await page.add_style_tag(content=HIDE)
        await page.evaluate("() => { window.requestAnimationFrame = () => 0; }")
        await page.set_viewport_size({'width': 1100, 'height': 700})
        for k in range(300):
            st = await page.evaluate("() => { const r = window.__test.BK.rooms.lib; return r ? r.ready : 'none'; }")
            if st is True: break
            await page.wait_for_timeout(200)
        for name, v in VIEWS:
            if isinstance(v, str) and v.startswith('place:'): v = await page.evaluate("(id) => window.__test.PLACES.find(p => p.id === id).view()", v[6:])
            await page.evaluate("""(v) => { const T = window.__test; T.cam.x = v.x; T.cam.z = v.z; T.cam.yaw = v.yaw; T.cam.pitch = v.pitch || 0; for (let i = 0; i < 30; i++) T.simStep(1 / 30); T.frameOnce(); T.frameOnce(); }""", v)
            ims = []
            for tm in ('aces', 'agx'):
                await page.evaluate(SET, tm)
                await page.wait_for_timeout(300)
                await page.evaluate("() => { const T = window.__test; for (let i = 0; i < 3; i++) T.frameOnce(); }")
                ims.append(Image.open(io.BytesIO(await page.screenshot(type='png'))).convert('RGB'))
            sheet = Image.new('RGB', (ims[0].width * 2 + 8, ims[0].height), (20, 20, 20))
            sheet.paste(ims[0], (0, 0)); sheet.paste(ims[1], (ims[0].width + 8, 0))
            sheet.save(os.path.join(OUT, 'tone_%s.jpg' % name), quality=85)
            print(name, flush=True)
        print(errs(logs))
        await b.close()
asyncio.run(run('desktop'))
