"""Crash safety: a leftover heartbeat (page died without pagehide) eases High to Medium for that visit only."""
import asyncio, os, sys, json
from harness import *
async def run():
    async with async_playwright() as p:
        # 1. Simulate a crash: the previous visit left a fresh heartbeat behind
        b, page, logs = await open_page(p, 'mobile', True, "try { if (!sessionStorage.getItem('__seeded')) { sessionStorage.setItem('__seeded', '1'); sessionStorage.setItem('xr-campus-beat', String(Date.now() - 5000)); } } catch (e) {}")
        st = await page.evaluate("() => ({ tier: window.__test.GFX.tier, pref: window.__test.GFX.pref, eased: window.__test.GFX.eased, saved: localStorage.getItem('xr-campus-gfx2') })")
        print('after crash leftover:', st, flush=True)
        await page.tap('#bEnter'); await page.wait_for_timeout(1500)
        print('toast:', await page.evaluate("() => { const t = document.querySelector('#toast'); return t.hidden ? '(hidden)' : t.textContent; }"), flush=True)
        # 2. A normal reload fires pagehide, so the next visit is back at the saved choice
        await page.reload()
        await page.wait_for_function("!document.querySelector('#bEnter').disabled", timeout=120000)
        st2 = await page.evaluate("() => ({ tier: window.__test.GFX.tier, eased: window.__test.GFX.eased })")
        print('after normal reload:', st2, flush=True)
        print(errs(logs))
        await b.close()
asyncio.run(run())
