/* ================================================================
   Small helpers
   ================================================================ */
const $ = (s) => document.querySelector(s);
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const REDUCED = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
const COARSE = !!(window.matchMedia && matchMedia('(pointer: coarse)').matches);
const F = {
  display:'"Old Standard TT", Georgia, "Times New Roman", serif',
  ui:'"Libre Franklin", "Helvetica Neue", Arial, sans-serif',
  type:'"Courier Prime", "Courier New", Courier, monospace'
};
function rnd(seed){ let a = seed >>> 0; return function(){ a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
function mk(w, h){ const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
function wrap(ctx, text, maxW){ const words = String(text).split(/\s+/); const out = []; let line = ''; for (const w of words){ const t = line ? line + ' ' + w : w; if (ctx.measureText(t).width > maxW && line){ out.push(line); line = w; } else line = t; } if (line) out.push(line); return out; }
function fit(ctx, text, family, weight, size, maxW, min){ let s = size; ctx.font = weight + ' ' + s + 'px ' + family; while (ctx.measureText(text).width > maxW && s > (min || 8)){ s -= 1; ctx.font = weight + ' ' + s + 'px ' + family; } return s; }
function rrect(ctx, x, y, w, h, r){ ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
