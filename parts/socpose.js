/* ================================================================
   Soccer poses: the goalkeeper and your own body, written in the wax
   figures' pose language (degrees per joint). Right-side versions are
   mirrored for the left.
   ================================================================ */
const SP_TRUNK = ['hips', 'spine', 'chest', 'neck', 'head'];
function spMirror(p){
  const o = {};
  for (const k in p){
    let v = p[k], key = k;
    if (/[a-z]L$/.test(k)) key = k.slice(0, -1) + 'R'; else if (/[a-z]R$/.test(k)) key = k.slice(0, -1) + 'L';
    if (SP_TRUNK.includes(k) && Array.isArray(v)) v = [v[0], -(v[1] || 0), -(v[2] || 0)];
    o[key] = v;
  }
  return o;
}
const SP_CACHE = new Map();
/* A named pose as a dense array; side -1 mirrors it */
function spD(lib, name, side){
  const key = lib.id + ':' + name + ':' + (side < 0 ? 'L' : 'R');
  let d = SP_CACHE.get(key);
  if (!d){ const p = lib[name]; d = waxDense(side < 0 ? spMirror(p) : p); SP_CACHE.set(key, d); }
  return d;
}
function spBlend(out, A, B, t){ for (let i = 0; i < WAX_N; i++) out[i] = A[i] + (B[i] - A[i]) * t; return out; }
function spEase(u){ u = clamp(u, 0, 1); return u * u * (3 - 2 * u); }
/* Add a partial spec on top of a dense pose (degrees, the same signs as waxDense) */
function spAdd(o, p, w){
  const s = w == null ? 1 : w;
  const tri = (b, v) => { if (!v) return; const i = WB[b] * 3; o[i] += v[0] * D2R * s; o[i + 2] -= (v[1] || 0) * D2R * s; o[i + 1] += (v[2] || 0) * D2R * s; };
  for (const k of SP_TRUNK) if (p[k]) tri(k, p[k]);
  const limb = (b, v, sd) => { if (!v) return; const i = WB[b] * 3; o[i] -= v[0] * D2R * s; o[i + 2] += sd * (v[1] || 0) * D2R * s; o[i + 1] += sd * (v[2] || 0) * D2R * s; };
  limb('shL', p.armL, 1); limb('shR', p.armR, -1); limb('thL', p.legL, 1); limb('thR', p.legR, -1);
  if (p.elL) o[WB.elL * 3] -= p.elL * D2R * s; if (p.elR) o[WB.elR * 3] -= p.elR * D2R * s;
  if (p.knL) o[WB.knL * 3] += p.knL * D2R * s; if (p.knR) o[WB.knR * 3] += p.knR * D2R * s;
  if (p.footL) o[WB.anL * 3] -= p.footL * D2R * s; if (p.footR) o[WB.anR * 3] -= p.footR * D2R * s;
  if (p.dy) o[WR + 3] += p.dy * s;
  return o;
}

/* ---------- The goalkeeper ---------- */
const KSPEC = {
  id:'k',
  stand:{ armL:[4, 9, 0], armR:[4, 9, 0], elL:16, elR:16, legL:[0, 3, 0], legR:[0, 3, 0] },
  ready:{ spine:[12, 0, 0], chest:[8, 0, 0], neck:[-6, 0, 0], head:[-14, 0, 0],
    armL:[40, 22, -20], armR:[40, 22, -20], elL:70, elR:70, handL:[-20, 0, 40], handR:[-20, 0, 40], gripL:-0.45, gripR:-0.45,
    legL:[26, 11, 0], legR:[26, 11, 0], knL:50, knR:50, footL:24, footR:24, dy:-0.08 },
  /* diving to his right: arms reach past the head, the push leg is long, the far leg trails */
  dive:{ spine:[2, -10, 6], chest:[0, -8, 6], neck:[0, -6, 0], head:[-6, -10, -14],
    armL:[164, 10, 0], armR:[166, 18, 0], elL:14, elR:10, handL:[0, 0, 0], handR:[0, 0, 0], gripL:-0.55, gripR:-0.55,
    legL:[22, 30, 0], legR:[6, 10, 0], knL:46, knR:12, footL:-20, footR:-26, dy:0 },
  divelow:{ spine:[14, -8, 10], chest:[6, -6, 8], neck:[0, -4, 0], head:[-10, -8, -12],
    armL:[150, 26, 0], armR:[132, 4, 0], elL:18, elR:16, handL:[0, 0, 30], handR:[0, 0, 30], gripL:-0.5, gripR:-0.5,
    legL:[30, 26, 0], legR:[16, 6, 0], knL:58, knR:24, footL:-14, footR:-20, dy:0 },
  jump:{ spine:[-4, 0, 0], chest:[-4, 0, 0], neck:[-6, 0, 0], head:[-22, 0, 0],
    armL:[168, 12, 0], armR:[168, 12, 0], elL:20, elR:20, handL:[-10, 0, 0], handR:[-10, 0, 0], gripL:-0.5, gripR:-0.5,
    legL:[56, 6, 0], legR:[2, 4, 0], knL:88, knR:8, footL:-10, footR:-34 },
  chest:{ spine:[10, 0, 0], chest:[4, 0, 0], head:[-8, 0, 0],
    armL:[58, 14, -24], armR:[58, 14, -24], elL:88, elR:88, handL:[-26, 0, 40], handR:[-26, 0, 40], gripL:-0.5, gripR:-0.5,
    legL:[16, 8, 0], legR:[16, 8, 0], knL:30, knR:30, footL:14, footR:14, dy:-0.04 },
  scoop:{ spine:[42, 0, 0], chest:[12, 0, 0], neck:[-8, 0, 0], head:[-20, 0, 0],
    armL:[56, 6, -10], armR:[56, 6, -10], elL:12, elR:12, handL:[-20, 0, 50], handR:[-20, 0, 50], gripL:-0.5, gripR:-0.5,
    legL:[74, 12, 0], legR:[74, 12, 0], knL:112, knR:112, footL:36, footR:36, dy:-0.4 },
  hold:{ spine:[4, 0, 0], head:[-4, 0, 0],
    armL:[46, 10, -34], armR:[46, 10, -34], elL:104, elR:104, handL:[-10, 0, 46], handR:[-10, 0, 46], gripL:0.45, gripR:0.45,
    legL:[0, 4, 0], legR:[0, 4, 0], knL:4, knR:4 },
  pick:{ spine:[46, 0, 0], chest:[10, 0, 0], neck:[-10, 0, 0], head:[-12, 0, 0],
    armL:[58, 8, -12], armR:[58, 8, -12], elL:14, elR:14, handL:[-14, 0, 46], handR:[-14, 0, 46], gripL:-0.1, gripR:-0.1,
    legL:[62, 10, 0], legR:[62, 10, 0], knL:96, knR:96, footL:30, footR:30, dy:-0.33 },
  /* an underarm roll: step in, crouch, swing the right arm through */
  roll1:{ spine:[24, 0, -10], chest:[6, 0, -10], head:[-14, 0, 0],
    armL:[40, 22, 0], armR:[-34, 12, 0], elL:30, elR:10, gripL:-0.3, gripR:0.4,
    legL:[40, 6, 0], legR:[-14, 6, 0], knL:62, knR:34, footL:22, footR:-6, dy:-0.17 },
  roll2:{ spine:[34, 0, 8], chest:[8, 0, 8], head:[-20, 0, 0],
    armL:[26, 26, 0], armR:[44, 8, 0], elL:30, elR:6, gripL:-0.3, gripR:-0.7,
    legL:[46, 6, 0], legR:[-20, 6, 0], knL:74, knR:40, footL:26, footR:-10, dy:-0.24 },
  beaten:{ spine:[6, 0, 0], neck:[10, 0, 0], head:[14, 0, 0],
    armL:[150, 46, 0], armR:[150, 46, 0], elL:128, elR:128, handL:[0, 0, 40], handR:[0, 0, 40], gripL:-0.2, gripR:-0.2,
    legL:[0, 5, 0], legR:[0, 5, 0] },
  cheer:{ spine:[-2, 0, 0], head:[-10, 0, 0], armR:[150, 18, 0], elR:40, gripR:1, armL:[18, 26, 0], elL:36, gripL:0.6,
    legL:[4, 5, 0], legR:[0, 5, 0], knL:6 },
  lie:{ spine:[6, -4, 4], chest:[2, -4, 4], head:[-4, -6, -10],
    armL:[150, 14, 0], armR:[150, 24, 0], elL:30, elR:24, gripL:-0.2, gripR:-0.2,
    legL:[30, 18, 0], legR:[14, 6, 0], knL:56, knR:26, footL:-10, footR:-14 }
};

/* ---------- Your body (right-footed) ---------- */
const BSPEC = {
  id:'b',
  stand:{ armL:[4, 9, 0], armR:[4, 9, 0], elL:18, elR:18, legL:[0, 3, 0], legR:[2, 3, 0], knR:4 },
  approach:{ spine:[10, 0, 0], hips:[0, 0, 6], chest:[0, 0, -6],
    armL:[24, 36, 0], armR:[-22, 16, 0], elL:32, elR:36,
    legL:[30, 4, 0], legR:[-22, 6, 0], knL:14, knR:64, footL:8, footR:-26, dy:-0.02 },
  plant:{ spine:[8, -10, 0], hips:[0, 0, -10], chest:[0, 0, 14],
    armL:[30, 62, 0], armR:[-24, 30, 0], elL:22, elR:30,
    legL:[10, 6, 0], legR:[-34, 8, 0], knL:22, knR:102, footL:14, footR:-30, dy:-0.04 },
  contact:{ spine:[14, -6, 0], hips:[0, 0, 8], chest:[0, 0, -6],
    armL:[24, 58, 0], armR:[8, 32, 0], elL:20, elR:26,
    legL:[6, 6, 0], legR:[35, 2, 0], knL:16, knR:38, footL:10, footR:-18, dy:-0.02 },
  follow:{ spine:[-4, 0, 0], hips:[0, 0, 10], chest:[0, 0, -10],
    armL:[10, 40, 0], armR:[30, 30, 0], elL:26, elR:30,
    legL:[0, 4, 0], legR:[70, 0, 0], knL:10, knR:22, footL:-16, footR:-12, dy:0.03 },
  land:{ spine:[6, 0, 0], armL:[10, 20, 0], armR:[10, 20, 0], elL:22, elR:22,
    legL:[-12, 4, 0], legR:[18, 4, 0], knL:18, knR:16, footR:4, dy:-0.03 },
  touch:{ legR:[24, 2, 0], knR:20, footR:-30, legL:[-4, 4, 0], knL:14, spine:[8, 0, 0] }
};

/* Walking and running legs: ph is the stride phase in radians, run 0..1 */
function spGait(o, ph, amp, run){
  const sn = Math.sin(ph), A = (20 + 16 * run) * amp, K = (32 + 46 * run) * amp;
  o[WB.thL * 3] += -A * D2R * sn; o[WB.thR * 3] += A * D2R * sn;
  o[WB.knL * 3] += K * D2R * Math.max(0, -Math.cos(ph - 0.5)); o[WB.knR * 3] += K * D2R * Math.max(0, Math.cos(ph - 0.5));
  o[WB.anL * 3] += 10 * D2R * amp * sn; o[WB.anR * 3] += -10 * D2R * amp * sn;
  o[WB.shL * 3] += (16 + 22 * run) * D2R * amp * sn; o[WB.shR * 3] += -(16 + 22 * run) * D2R * amp * sn;
  o[WB.elL * 3] -= (6 + 60 * run) * D2R * amp; o[WB.elR * 3] -= (6 + 60 * run) * D2R * amp;
  o[WB.hips * 3 + 1] += 5 * D2R * amp * sn; o[WB.chest * 3 + 1] -= 6 * D2R * amp * sn;
  o[WB.spine * 3] += (3 + 9 * run) * D2R * amp;
  o[WR + 3] -= (0.02 + 0.03 * run) * amp * Math.abs(Math.cos(ph));
  return o;
}
