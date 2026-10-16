/* ================================================================
   Living History: wax figures
   Generic reenactors, never likenesses of real people. Each figure is a
   smooth skinned body (clothes, hair, shoes) plus a waxy skinned layer
   (face, neck, hands, bare arms and legs) that can blink and talk.
   17 bones; poses are written in degrees and eased between keyframes.
   ================================================================ */
const WAXB = ['hips', 'spine', 'chest', 'neck', 'head', 'shL', 'elL', 'wrL', 'shR', 'elR', 'wrR', 'thL', 'knL', 'anL', 'thR', 'knR', 'anR'];
const WB = {}; WAXB.forEach((b, i) => { WB[b] = i; });
const WAX_ORD = ['YXZ', 'YXZ', 'YXZ', 'YXZ', 'YXZ', 'XZY', 'XYZ', 'XZY', 'XZY', 'XYZ', 'XZY', 'XZY', 'XYZ', 'XYZ', 'XZY', 'XYZ', 'XYZ'];
/* Body types in adult units; s scales the whole figure, head scales the head on top of that */
const WAX_BODY = {
  man:{ s:1, sh:0.19, hip:0.152, waist:0.138, chest:0.172, dep:1, bust:0, head:1, leg:1 },
  woman:{ s:0.95, sh:0.17, hip:0.172, waist:0.122, chest:0.15, dep:0.95, bust:1, head:1.01, leg:1.01 },
  boy:{ s:0.9, sh:0.17, hip:0.142, waist:0.13, chest:0.154, dep:0.93, bust:0, head:1.05, leg:0.99 },
  girl:{ s:0.88, sh:0.158, hip:0.156, waist:0.12, chest:0.142, dep:0.9, bust:0.45, head:1.06, leg:1 },
  kid:{ s:0.64, sh:0.166, hip:0.15, waist:0.148, chest:0.154, dep:1.04, bust:0, head:1.34, leg:0.9 },
  elder:{ s:0.95, sh:0.18, hip:0.158, waist:0.152, chest:0.168, dep:1.06, bust:0, head:1, leg:0.97 }
};
const WAX_SKIN = { light:0xf0c9ab, fair:0xe4b08c, olive:0xcf9e74, medium:0xc08660, tan:0xa66f4a, brown:0x80522f, deep:0x5a3622 };
const WAX = { figs:[], scenes:[], mats:null, live:new Set(), headset:null, lastT:0 };
const _wc = new THREE.Color(), _wc2 = new THREE.Color();
function wcol(hex){ return new THREE.Color(hex); }

/* ---------- Geometry builder: positions, normals, colors, skin weights, roughness, morphs ---------- */
class WaxGeo {
  constructor(){ this.P = []; this.N = []; this.C = []; this.SI = []; this.SW = []; this.R = []; this.I = []; this.MB = []; this.MT = []; }
  get n(){ return this.P.length / 3; }
  v(x, y, z, nx, ny, nz, c, w, rough, mb, mt){
    const i = this.P.length / 3;
    this.P.push(x, y, z); this.N.push(nx, ny, nz); this.C.push(c.r, c.g, c.b); this.R.push(rough == null ? 1 : rough);
    let sum = 0; for (const e of w) sum += e[1];
    for (let k = 0; k < 4; k++){ const e = w[k]; this.SI.push(e ? e[0] : 0); this.SW.push(e ? e[1] / sum : 0); }
    this.MB.push(mb ? mb[0] : 0, mb ? mb[1] : 0, mb ? mb[2] : 0); this.MT.push(mt ? mt[0] : 0, mt ? mt[1] : 0, mt ? mt[2] : 0);
    return i;
  }
  /* A triangle wound to face along its vertex normals */
  tri(a, b, c){
    const P = this.P, N = this.N;
    const ux = P[b * 3] - P[a * 3], uy = P[b * 3 + 1] - P[a * 3 + 1], uz = P[b * 3 + 2] - P[a * 3 + 2];
    const vx = P[c * 3] - P[a * 3], vy = P[c * 3 + 1] - P[a * 3 + 1], vz = P[c * 3 + 2] - P[a * 3 + 2];
    const fx = uy * vz - uz * vy, fy = uz * vx - ux * vz, fz = ux * vy - uy * vx;
    const nx = N[a * 3] + N[b * 3] + N[c * 3], ny = N[a * 3 + 1] + N[b * 3 + 1] + N[c * 3 + 1], nz = N[a * 3 + 2] + N[b * 3 + 2] + N[c * 3 + 2];
    if (fx * nx + fy * ny + fz * nz < 0) this.I.push(a, c, b); else this.I.push(a, b, c);
  }
  quad(a, b, c, d){ this.tri(a, b, c); this.tri(a, c, d); }
  build(morphs){
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(this.P, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(this.N, 3));
    g.setAttribute('color', new THREE.Float32BufferAttribute(this.C, 3));
    g.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(this.SI, 4));
    g.setAttribute('skinWeight', new THREE.Float32BufferAttribute(this.SW, 4));
    g.setAttribute('aRough', new THREE.Float32BufferAttribute(this.R, 1));
    g.setIndex(this.I);
    if (morphs){
      g.morphAttributes.position = [new THREE.Float32BufferAttribute(this.MB, 3), new THREE.Float32BufferAttribute(this.MT, 3)];
      g.morphTargetsRelative = true;
    }
    g.boundingSphere = new THREE.Sphere(new THREE.Vector3(0, 0.9, 0), 1.45);
    return g;
  }
}

/* Copy any indexed three.js geometry into a WaxGeo, transformed, with one bone set.
   col: a Color or fn(local position, normal) -> Color. morph(p) -> { b:[dx,dy,dz], t:[...] } in figure units. */
const _wm = new THREE.Matrix4(), _wn = new THREE.Matrix3(), _wv = new THREE.Vector3(), _wvn = new THREE.Vector3(), _wq = new THREE.Quaternion(), _we = new THREE.Euler();
function waxPart(G, geo, pos, rot, scl, col, w, rough, morph){
  _we.set(rot ? rot[0] : 0, rot ? rot[1] : 0, rot ? rot[2] : 0); _wq.setFromEuler(_we);
  _wm.compose(_wv.set(pos[0], pos[1], pos[2]), _wq, new THREE.Vector3(scl[0], scl[1], scl[2]));
  _wn.getNormalMatrix(_wm);
  const p = geo.attributes.position, nrm = geo.attributes.normal, base = G.n, loc = new THREE.Vector3();
  for (let i = 0; i < p.count; i++){
    loc.set(p.getX(i), p.getY(i), p.getZ(i));
    _wv.copy(loc).applyMatrix4(_wm); _wvn.set(nrm.getX(i), nrm.getY(i), nrm.getZ(i)).applyMatrix3(_wn).normalize();
    const c = typeof col === 'function' ? col(loc, _wv) : col, m = morph ? morph(loc, _wv) : null;
    G.v(_wv.x, _wv.y, _wv.z, _wvn.x, _wvn.y, _wvn.z, c, w, rough, m && m.b, m && m.t);
  }
  const idx = geo.index;
  if (idx) for (let i = 0; i < idx.count; i += 3) G.tri(base + idx.getX(i), base + idx.getX(i + 1), base + idx.getX(i + 2));
  else for (let i = 0; i < p.count; i += 3) G.tri(base + i, base + i + 1, base + i + 2);
  geo.dispose();
}

/* A smooth tube through horizontal rings (the bind pose stands upright, arms down).
   Ring: { x, y, z, rx, rz, c (Color), w (weights), m ('s' skin | 'c' cloth), r (roughness) }.
   A band takes the material of its upper ring; where the material changes, the band keeps the upper ring's color. */
function waxTube(G, rings, n, capTop, capBot){
  const L = rings.length, cache = [new Map(), new Map()];
  const slope = (i) => {
    const a = rings[Math.max(0, i - 1)], b = rings[Math.min(L - 1, i + 1)], dy = b.y - a.y;
    return Math.abs(dy) < 1e-5 ? 0 : ((b.rx + b.rz) - (a.rx + a.rz)) / 2 / dy;
  };
  const emit = (gi, i, cOver) => {
    const key = i + (cOver ? '|' + cOver.getHexString() : '');
    if (cache[gi].has(key)) return cache[gi].get(key);
    const R = rings[i], g = gi ? G.c : G.s, sl = slope(i), first = g.n, c = cOver || R.c;
    for (let j = 0; j <= n; j++){
      const a = j / n * Math.PI * 2, ca = Math.cos(a), sa = Math.sin(a);
      let nx = ca / R.rx, nz = sa / R.rz; const l = Math.hypot(nx, nz) || 1; nx /= l; nz /= l;
      const ny = -sl, k = 1 / Math.hypot(nx, ny, nz);
      g.v(R.x + R.rx * ca, R.y, R.z + R.rz * sa, nx * k, ny * k, nz * k, R.cf ? R.cf(ca, sa) : c, R.w, R.r);
    }
    cache[gi].set(key, first);
    return first;
  };
  for (let i = 0; i < L - 1; i++){
    const A = rings[i], B = rings[i + 1], gi = A.m === 'c' ? 1 : 0, g = gi ? G.c : G.s;
    const a = emit(gi, i), b = emit(gi, i + 1, B.m !== A.m ? A.c : null);
    for (let j = 0; j < n; j++) g.quad(a + j, a + j + 1, b + j + 1, b + j);
  }
  const cap = (R, dir) => {
    const gi = R.m === 'c' ? 1 : 0, g = gi ? G.c : G.s, d = (R.rx + R.rz) / 2 * (R.cap || 0.85), steps = 3;
    let prev = emit(gi, rings.indexOf(R));
    for (let s = 1; s <= steps; s++){
      const th = s / (steps + 1) * Math.PI / 2, k = Math.cos(th), first = g.n;
      for (let j = 0; j <= n; j++){
        const a = j / n * Math.PI * 2, ca = Math.cos(a), sa = Math.sin(a);
        const nx = ca * k, nz = sa * k, ny = dir * Math.sin(th);
        g.v(R.x + R.rx * k * ca, R.y + dir * d * Math.sin(th), R.z + R.rz * k * sa, nx, ny, nz, R.c, R.w, R.r);
      }
      for (let j = 0; j < n; j++) g.quad(prev + j, prev + j + 1, first + j + 1, first + j);
      prev = first;
    }
    const pole = g.v(R.x, R.y + dir * d, R.z, 0, dir, 0, R.c, R.w, R.r);
    for (let j = 0; j < n; j++) g.tri(prev + j, prev + j + 1, pole);
  };
  if (capTop) cap(rings[0], rings[0].y > rings[L - 1].y ? 1 : -1);
  if (capBot) cap(rings[L - 1], rings[L - 1].y < rings[0].y ? -1 : 1);
}
const wsm = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
function wmix(pairs){ return pairs.filter((e) => e[1] > 0.001); }

/* ---------- One figure ---------- */
/* look: { body, skin, hair, hairStyle, eyes, top, sleeves ('long'|'short'|'rolled'), jacket, bottom, legs ('pants'|'shorts'|'skirt'),
   hem (skirt length 0..1), shoes, socks, belt, collar, glasses, beard, lanyard, cap, scarf, stripe } */
function makeWaxFigure(look){
  /* A realistic reenactor when the scene names an avatar */
  if (look.av && HK_RIG.avatars[look.av]){
    const f = makeHuman(Object.assign({ wax:true, lazy:'wax' }, look));
    WAX.figs.push(f);
    return f;
  }
  const T = WAX_BODY[look.body] || WAX_BODY.man, S = T.s, L = T.leg, hs = T.head;
  const skin = wcol(look.skin || WAX_SKIN.medium), top = wcol(look.top || 0x3a5a78), jacket = look.jacket != null ? wcol(look.jacket) : null;
  const bottom = wcol(look.bottom || 0x2b2f38), shoes = wcol(look.shoes || 0x231c16), hair = wcol(look.hair || 0x2a1d14);
  const lip = skin.clone().lerp(wcol(0xa04a48), 0.38).multiplyScalar(0.92), cheek = skin.clone().lerp(wcol(0xd97a6c), 0.16);
  const shirt = jacket ? top : top, outer = jacket || top;
  const G = { s:new WaxGeo(), c:new WaxGeo() };
  const W = (b) => [[WB[b], 1]];

  /* Skeleton in the bind pose (adult units, scaled at the end) */
  const ank = 0.085, kne = ank + 0.42 * L, hipJ = kne + 0.42 * L, hipsY = hipJ + 0.04;
  const spineY = hipsY + 0.1, chestY = spineY + 0.2, neckY = chestY + 0.19, headY = neckY + 0.07;
  const shY = chestY + 0.162, shX = T.sh, elY = shY - 0.285, wrY = elY - 0.25;
  const J = {
    hips:[0, hipsY, 0], spine:[0, spineY, 0], chest:[0, chestY, 0], neck:[0, neckY, 0], head:[0, headY, 0.008],
    shL:[shX, shY, -0.012], elL:[shX + 0.02, elY, -0.016], wrL:[shX + 0.026, wrY, 0.0],
    shR:[-shX, shY, -0.012], elR:[-shX - 0.02, elY, -0.016], wrR:[-shX - 0.026, wrY, 0.0],
    thL:[0.088, hipJ, 0], knL:[0.092, kne, 0.004], anL:[0.092, ank, -0.012],
    thR:[-0.088, hipJ, 0], knR:[-0.092, kne, 0.004], anR:[-0.092, ank, -0.012]
  };
  const PAR = { spine:'hips', chest:'spine', neck:'chest', head:'neck', shL:'chest', elL:'shL', wrL:'elL', shR:'chest', elR:'shR', wrR:'elR', thL:'hips', knL:'thL', anL:'knL', thR:'hips', knR:'thR', anR:'knR' };

  /* --- Torso: ellipse rings from the crotch to the neck base --- */
  const d = T.dep, bust = T.bust, sweater = look.top != null;
  const waistY = hipJ + 0.15, beltY = waistY - 0.035;
  const prof = [
    [hipJ - 0.078, T.hip * 0.6, 0.078, -0.004], [hipJ - 0.045, T.hip * 0.86, 0.097, -0.01], [hipJ, T.hip * 0.97, 0.11, -0.014],
    [hipJ + 0.06, (T.hip + T.waist) / 2 + 0.004, 0.108, -0.008], [waistY, T.waist, 0.098, 0], [hipJ + 0.23, (T.waist + T.chest) / 2, 0.1 + bust * 0.008, 0.004 + bust * 0.006],
    [hipJ + 0.3, T.chest, 0.108 + bust * 0.022, 0.01 + bust * 0.016], [hipJ + 0.365, T.chest * 1.02, 0.108 + bust * 0.012, 0.01 + bust * 0.008],
    [hipJ + 0.43, T.sh * 0.93, 0.1, 0.002], [hipJ + 0.5, T.sh * 0.84, 0.09, -0.006], [hipJ + 0.535, T.sh * 0.66, 0.078, -0.008], [hipJ + 0.556, 0.09, 0.064, -0.006], [hipJ + 0.566, 0.066, 0.058, -0.004]
  ];
  const torsoW = (x, y) => {
    const out = [];
    const h = 1 - wsm(spineY - 0.05, spineY + 0.04, y), sp = wsm(spineY - 0.05, spineY + 0.04, y) * (1 - wsm(chestY - 0.06, chestY + 0.03, y));
    let ch = wsm(chestY - 0.06, chestY + 0.03, y) * (1 - wsm(neckY - 0.03, neckY + 0.01, y)), nk = wsm(neckY - 0.03, neckY + 0.01, y);
    /* Shoulder flesh follows the arm a little so raised arms don't tear the torso */
    const sideL = wsm(T.sh * 0.42, T.sh * 0.95, x) * wsm(shY - 0.12, shY - 0.02, y), sideR = wsm(T.sh * 0.42, T.sh * 0.95, -x) * wsm(shY - 0.12, shY - 0.02, y);
    const sl = ch * sideL * 0.4, sr = ch * sideR * 0.4; ch -= sl + sr;
    out.push([WB.hips, h], [WB.spine, sp], [WB.chest, ch], [WB.neck, nk], [WB.shL, sl], [WB.shR, sr]);
    return wmix(out).sort((a, b) => b[1] - a[1]).slice(0, 4);
  };
  /* The torso is drawn as a ring set whose vertices get weights per vertex, so it is built by hand here */
  {
    const n = 22, rows = [];
    const yTop = prof[prof.length - 1][0], yBot = prof[0][0];
    const lerpProf = (y) => { for (let i = 0; i < prof.length - 1; i++){ const a = prof[i], b = prof[i + 1]; if (y >= a[0] && y <= b[0]){ const t = (y - a[0]) / (b[0] - a[0]), k = t * t * (3 - 2 * t) * 0.5 + t * 0.5; return [a[1] + (b[1] - a[1]) * k, (a[2] + (b[2] - a[2]) * k) * d, a[3] + (b[3] - a[3]) * k]; } } return null; };
    const ys = []; for (let i = 0; i <= 26; i++) ys.push(yBot + (yTop - yBot) * i / 26);
    for (const extra of [beltY, beltY + 0.0005, waistY - 0.0005, waistY]) ys.push(extra);
    ys.sort((a, b) => a - b);
    const colAt = (y, ca, sa) => {
      const pants = look.legs === 'skirt' ? (look.dress ? outer : bottom) : bottom;
      if (look.belt != null && y > beltY && y < waistY && !look.dress) return wcol(look.belt);
      if (y <= beltY && !look.dress) return pants;
      if (jacket && sa > 0.55 && Math.abs(ca) < 0.24 && y < hipJ + 0.47) return shirt;
      if (look.stripe != null && y > hipJ + 0.26 && y < hipJ + 0.32) return wcol(look.stripe);
      return outer;
    };
    for (const y of ys){
      const pr = lerpProf(y); if (!pr) continue;
      rows.push({ y, rx:pr[0], rz:pr[1], cz:pr[2] });
    }
    const g = G.c, first = [];
    const sl = (i) => { const a = rows[Math.max(0, i - 1)], b = rows[Math.min(rows.length - 1, i + 1)], dy = b.y - a.y; return dy < 1e-5 ? 0 : ((b.rx + b.rz) - (a.rx + a.rz)) / 2 / dy; };
    rows.forEach((R, i) => {
      first.push(g.n);
      const s = sl(i);
      for (let j = 0; j <= n; j++){
        const a = j / n * Math.PI * 2, ca = Math.cos(a), sa = Math.sin(a);
        /* A slightly squarer section reads as a torso rather than a pipe */
        const sq = 1 + 0.07 * Math.pow(Math.abs(Math.sin(2 * a)), 2);
        const x = R.rx * ca * sq, z = R.cz + R.rz * sa * (sa > 0 ? 1 : 0.94) * sq;
        let nx = ca / R.rx, nz = sa / R.rz; const l = Math.hypot(nx, nz) || 1; nx /= l; nz /= l;
        const ny = -s, k = 1 / Math.hypot(nx, ny, nz);
        g.v(x, R.y, z, nx * k, ny * k, nz * k, colAt(R.y, ca, sa), torsoW(x, R.y), look.legs === 'skirt' && R.y < waistY ? 0.85 : 0.88);
      }
    });
    for (let i = 0; i < rows.length - 1; i++) for (let j = 0; j < n; j++) g.quad(first[i] + j, first[i] + j + 1, first[i + 1] + j + 1, first[i + 1] + j);
    /* Close the bottom with a small dome */
    const R0 = rows[0], b0 = first[0], pole = g.v(0, R0.y - 0.03, R0.cz, 0, -1, 0, bottom, W('hips'), 0.88);
    for (let j = 0; j < n; j++) g.tri(b0 + j, b0 + j + 1, pole);
  }

  /* --- Neck --- */
  {
    const y0 = hipJ + 0.53, y1 = headY + 0.06, rings = [];
    for (let i = 0; i <= 6; i++){
      const y = y0 + (y1 - y0) * i / 6, k = i / 6;
      const w = wmix([[WB.chest, 1 - wsm(0, 0.25, k)], [WB.neck, wsm(0, 0.25, k) * (1 - wsm(0.55, 0.95, k))], [WB.head, wsm(0.55, 0.95, k)]]);
      rings.push({ x:0, y, z:-0.006 + 0.01 * k, rx:0.061 - 0.008 * k, rz:0.059 - 0.006 * k, c:skin, w, m:'s', r:0.9 });
    }
    if (look.collar != null){
      const cc = wcol(look.collar);
      waxTube(G, [{ x:0, y:hipJ + 0.56, z:-0.004, rx:0.064, rz:0.062, c:cc, w:W('chest'), m:'c', r:0.88 }, { x:0, y:hipJ + 0.51, z:-0.004, rx:0.075, rz:0.068, c:cc, w:W('chest'), m:'c', r:0.88 }], 18);
    }
    waxTube(G, rings, 14);
  }

  /* --- Arms --- */
  for (const sd of [1, -1]){
    const s = sd > 0 ? 'L' : 'R', sh = J['sh' + s], el = J['el' + s], wr = J['wr' + s];
    const sleeve = look.sleeves || 'long', cuff = sleeve === 'short' ? 0.42 : sleeve === 'rolled' ? 1.12 : 1.93;
    const pts = [];
    const add = (u, rx, rz) => {
      const a = u <= 1 ? sh : el, b = u <= 1 ? el : wr, t = u <= 1 ? u : u - 1;
      const x = a[0] + (b[0] - a[0]) * t, y = a[1] + (b[1] - a[1]) * t, z = a[2] + (b[2] - a[2]) * t;
      const w = wmix([[WB.chest, 0.45 * (1 - wsm(0, 0.18, u))], [WB['sh' + s], (1 - wsm(0.86, 1.14, u)) * (1 - 0.45 * (1 - wsm(0, 0.18, u)))], [WB['el' + s], wsm(0.86, 1.14, u) * (1 - wsm(1.88, 2.0, u) * 0.6)], [WB['wr' + s], wsm(1.88, 2.0, u) * 0.6]]);
      const clothed = u < cuff, rr = clothed ? (jacket ? 1.08 : 1.04) : 1;
      pts.push({ x, y, z, rx:rx * rr, rz:rz * rr, c:clothed ? outer : skin, w, m:clothed ? 'c' : 's', r:clothed ? 0.88 : 0.9 });
    };
    for (const [u, rx, rz] of [[0, 0.054, 0.052], [0.2, 0.052, 0.05], [0.45, 0.046, 0.045], [0.7, 0.042, 0.041], [0.92, 0.037, 0.036], [1.0, 0.036, 0.035], [1.12, 0.038, 0.036], [1.3, 0.04, 0.037], [1.55, 0.035, 0.032], [1.8, 0.029, 0.026], [1.97, 0.026, 0.022]]) add(u, rx, rz);
    /* A cuff: two rings at the same height so the sleeve ends in a clean edge */
    const ci = pts.findIndex((p) => p.m === 's');
    if (ci > 0){
      const A = pts[ci - 1], B = pts[ci], t = (cuff - [0, 0.2, 0.45, 0.7, 0.92, 1.0, 1.12, 1.3, 1.55, 1.8, 1.97][ci - 1]) / ([0, 0.2, 0.45, 0.7, 0.92, 1.0, 1.12, 1.3, 1.55, 1.8, 1.97][ci] - [0, 0.2, 0.45, 0.7, 0.92, 1.0, 1.12, 1.3, 1.55, 1.8, 1.97][ci - 1]);
      const mid = { x:A.x + (B.x - A.x) * t, y:A.y + (B.y - A.y) * t, z:A.z + (B.z - A.z) * t, rx:(A.rx + (B.rx - A.rx) * t), rz:(A.rz + (B.rz - A.rz) * t), w:t < 0.5 ? A.w : B.w };
      pts.splice(ci, 0, Object.assign({}, mid, { c:outer, m:'c', r:0.88, rx:mid.rx * 1.06, rz:mid.rz * 1.06 }), Object.assign({}, mid, { y:mid.y - 0.0008, c:skin, m:'s', r:0.9, rx:mid.rx * 0.93, rz:mid.rz * 0.93 }));
    }
    pts[0].cap = 0.75;
    waxTube(G, pts, 12, true, true);
    /* Hand: palm, fingers and thumb, all on the wrist bone */
    const hw = W('wr' + s), hx = wr[0], hy = wr[1], hz = wr[2];
    waxPart(G.s, new THREE.SphereGeometry(1, 12, 10), [hx + sd * 0.002, hy - 0.058, hz + 0.004], [0, 0, 0], [0.023, 0.064, 0.048], skin, hw, 0.9);
    waxPart(G.s, new THREE.SphereGeometry(1, 12, 10), [hx + sd * 0.001, hy - 0.126, hz + 0.013], [-0.22, 0, 0], [0.0195, 0.054, 0.045], skin, hw, 0.9);
    waxPart(G.s, new THREE.SphereGeometry(1, 10, 8), [hx - sd * 0.011, hy - 0.056, hz + 0.041], [-0.35, 0, sd * 0.42], [0.014, 0.038, 0.0145], skin, hw, 0.9);
  }

  /* --- Legs --- */
  const legBare = look.legs === 'shorts' ? 0.42 : look.legs === 'skirt' ? 2.2 : 2.2;
  for (const sd of [1, -1]){
    const s = sd > 0 ? 'L' : 'R', th = J['th' + s], kn = J['kn' + s], an = J['an' + s];
    const pts = [], us = [];
    const skirtHemY = hipJ - 0.05 - (look.hem == null ? 0.45 : look.hem) * 0.62, underSkirt = (y) => look.legs === 'skirt' && y > skirtHemY + 0.03;
    const skirtCol = look.dress ? outer : bottom;
    const legCol = (u, y) => {
      if (underSkirt(y)) return skirtCol.clone().multiplyScalar(0.6);
      if (look.legs === 'skirt') return look.tights != null ? wcol(look.tights) : skin;
      if (u < legBare) return bottom;
      if (look.socks != null && u > 1.78) return wcol(look.socks);
      return skin;
    };
    const legMat = (u, y) => (underSkirt(y) ? 'c' : look.legs === 'skirt' ? (look.tights != null ? 'c' : 's') : (u < legBare || (look.socks != null && u > 1.78)) ? 'c' : 's');
    for (const [u, rx, rz] of [[0, 0.094, 0.096], [0.15, 0.09, 0.091], [0.4, 0.079, 0.079], [0.7, 0.065, 0.065], [0.92, 0.053, 0.054], [1.0, 0.051, 0.052], [1.15, 0.053, 0.057], [1.32, 0.055, 0.059], [1.55, 0.047, 0.048], [1.8, 0.038, 0.038], [1.96, 0.035, 0.035], [2.08, 0.033, 0.033]]){
      const a = u <= 1 ? th : kn, b = u <= 1 ? kn : an, t = u <= 1 ? u : u - 1;
      const x = a[0] + (b[0] - a[0]) * t, y = a[1] + (b[1] - a[1]) * t, z = a[2] + (b[2] - a[2]) * t;
      const w = wmix([[WB.hips, 0.4 * (1 - wsm(0, 0.2, u))], [WB['th' + s], (1 - wsm(0.86, 1.12, u)) * (1 - 0.4 * (1 - wsm(0, 0.2, u)))], [WB['kn' + s], wsm(0.86, 1.12, u) * (1 - wsm(1.86, 2.02, u))], [WB['an' + s], wsm(1.86, 2.02, u)]]);
      const m = legMat(u, y), loose = m === 'c' && look.legs !== 'skirt' ? 1.05 : underSkirt(y) ? 0.9 : 1;
      pts.push({ x, y, z:z + (u > 1.1 && u < 1.6 ? -0.006 : 0), rx:rx * loose, rz:rz * loose, c:legCol(u, y), w, m, r:0.9 }); us.push(u);
    }
    waxTube(G, pts, 12, true, false);
    /* Shoe: a rounded last with a flat sole on the ankle bone */
    const fw = W('an' + s);
    const shoe = new THREE.SphereGeometry(1, 18, 12), sp = shoe.attributes.position;
    for (let i = 0; i < sp.count; i++){ const z = sp.getZ(i), y = sp.getY(i); if (y < -0.6) sp.setY(i, -0.6); sp.setX(i, sp.getX(i) * (1 + 0.1 * z)); if (z > 0.3 && y > 0) sp.setY(i, y * (1 - 0.45 * (z - 0.3))); }
    shoe.computeVertexNormals();
    waxPart(G.c, shoe, [an[0] + sd * 0.004, an[1] - 0.046, an[2] + 0.046], [0, 0, 0], [0.05, 0.056, 0.126], shoes, fw, 0.6);
  }

  /* --- Skirt or dress: a flared tube from the waist that follows the thighs a little --- */
  if (look.legs === 'skirt'){
    const hemY = hipJ - 0.05 - (look.hem == null ? 0.45 : look.hem) * 0.62, n = 22, g = G.c, rows = 7, first = [];
    const sc = look.dress ? outer : bottom;
    for (let i = 0; i <= rows; i++){
      const k = i / rows, y = waistY - (waistY - hemY) * k, rx = T.waist * 1.08 + (T.hip * 1.32 - T.waist * 1.08) * Math.sqrt(k) + 0.03 * k, rz = 0.1 * d + 0.06 * k;
      first.push(g.n);
      for (let j = 0; j <= n; j++){
        const a = j / n * Math.PI * 2, ca = Math.cos(a), sa = Math.sin(a), x = rx * ca, z = -0.01 + rz * sa;
        const f = 0.55 * wsm(0.15, 1, k), side = x >= 0 ? 'thL' : 'thR', centre = 1 - Math.min(1, Math.abs(ca) * 2.2);
        const w = wmix([[WB.hips, 1 - f], [WB[side], f * (1 - centre * 0.5)], [WB[side === 'thL' ? 'thR' : 'thL'], f * centre * 0.5]]);
        g.v(x, y, z, ca, 0.25, sa, sc, w, 0.9);
      }
    }
    for (let i = 0; i < rows; i++) for (let j = 0; j < n; j++) g.quad(first[i] + j, first[i] + j + 1, first[i + 1] + j + 1, first[i + 1] + j);
    /* the inside of the skirt shows as a darker lining */
    const inner = sc.clone().multiplyScalar(0.55), f2 = g.n;
    for (let i = 0; i <= rows; i++) for (let j = 0; j <= n; j++){ const o = (first[i] + j) * 3; const pidx = first[i] + j; g.v(g.P[o] * 0.985, g.P[o + 1], g.P[o + 2] * 0.985 - 0.0001, -g.N[o], -g.N[o + 1], -g.N[o + 2], inner, [[g.SI[pidx * 4], g.SW[pidx * 4]], [g.SI[pidx * 4 + 1], g.SW[pidx * 4 + 1]], [g.SI[pidx * 4 + 2], g.SW[pidx * 4 + 2]]].filter((e) => e[1] > 0), 0.95); }
    for (let i = 0; i < rows; i++) for (let j = 0; j < n; j++) g.quad(f2 + i * (n + 1) + j, f2 + i * (n + 1) + j + 1, f2 + (i + 1) * (n + 1) + j + 1, f2 + (i + 1) * (n + 1) + j);
  }

  /* --- Head: a shaped egg with sockets, cheeks and a jaw --- */
  const HC = [0, headY + 0.094, 0.016], hr = [0.089, 0.118, 0.104];
  const hp = (x, y, z) => [HC[0] + x * hs, HC[1] + y * hs, HC[2] + z * hs];
  const eyes = [[0.0335, 0.016, 0.0795], [-0.0335, 0.016, 0.0795]];
  {
    const geo = new THREE.SphereGeometry(1, 34, 26), P = geo.attributes.position;
    for (let i = 0; i < P.count; i++){
      let x = P.getX(i), y = P.getY(i), z = P.getZ(i);
      if (y < -0.1){ const t = wsm(-0.1, -1, y); x *= 1 - 0.27 * t; if (z > 0) z *= 1 - 0.06 * t; }
      if (y < -0.72) y = -0.72 - (y + 0.72) * 0.75;
      if (z < 0 && y > -0.35) z *= 1.06;
      if (y < -0.55 && z > 0.2) { y -= 0.04 * (z - 0.2); }
      for (const ex of [-0.4, 0.4]){ const dd = Math.hypot(x - ex, (y - 0.14) * 1.25); if (z > 0.5) z -= 0.07 * Math.exp(-dd * dd / 0.035); }
      if (z > 0.55 && y > 0.18 && y < 0.42) z += 0.025 * Math.exp(-Math.pow((y - 0.3) / 0.08, 2));
      if (z > 0.45 && Math.abs(x) > 0.3 && y < 0 && y > -0.45) z += 0.03 * Math.exp(-Math.pow((y + 0.18) / 0.15, 2));
      P.setXYZ(i, x * hr[0], y * hr[1], z * hr[2]);
    }
    geo.computeVertexNormals();
    const jawTalk = (loc) => (loc.y < -0.062 && loc.z > 0.03 ? { t:[0, -0.0055 * hs * wsm(-0.062, -0.09, loc.y), 0] } : null);
    waxPart(G.s, geo, HC, [0, 0, 0], [hs, hs, hs], (loc) => {
      const k = Math.exp(-(Math.pow(Math.abs(loc.x) - 0.05, 2) + Math.pow(loc.y + 0.02, 2)) / 0.0006) * (loc.z > 0.04 ? 1 : 0);
      if (look.beard && loc.y < -0.035 && loc.z > -0.02 && !(loc.y > -0.075 && Math.abs(loc.x) < 0.03 && loc.z > 0.06)) return _wc2.copy(hair).lerp(skin, look.beard === 'stubble' ? 0.55 : 0.12).clone();
      return k > 0.02 ? _wc.copy(skin).lerp(cheek, Math.min(1, k)).clone() : skin;
    }, W('head'), 0.62, jawTalk);
    /* Ears and nose */
    for (const sx of [1, -1]) waxPart(G.s, new THREE.SphereGeometry(1, 10, 8), hp(sx * 0.083, 0.004, -0.006), [0, sx * 0.35, 0], [0.011 * hs, 0.028 * hs, 0.018 * hs], skin.clone().multiplyScalar(0.96), W('head'), 0.7);
    waxPart(G.s, new THREE.SphereGeometry(1, 12, 10), hp(0, -0.004, 0.096), [-0.3, 0, 0], [0.0108 * hs, 0.022 * hs, 0.0145 * hs], skin, W('head'), 0.6);
    waxPart(G.s, new THREE.SphereGeometry(1, 12, 8), hp(0, -0.024, 0.1015), [0, 0, 0], [0.0145 * hs, 0.0098 * hs, 0.0105 * hs], skin.clone().lerp(cheek, 0.4), W('head'), 0.6);
    /* Mouth: dark inside, then lips; talking drops the lower lip */
    waxPart(G.s, new THREE.SphereGeometry(1, 12, 6), hp(0, -0.047, 0.084), [0, 0, 0], [0.019 * hs, 0.0065 * hs, 0.008 * hs], wcol(0x3a1814), W('head'), 0.8, (loc) => (loc.y < 0 ? { t:[0, -0.0072 * hs, 0] } : null));
    waxPart(G.s, new THREE.SphereGeometry(1, 16, 8), hp(0, -0.0425, 0.0885), [0.15, 0, 0], [0.0215 * hs, 0.0048 * hs, 0.0068 * hs], lip, W('head'), 0.38);
    waxPart(G.s, new THREE.SphereGeometry(1, 16, 8), hp(0, -0.0515, 0.0875), [-0.12, 0, 0], [0.0195 * hs, 0.0058 * hs, 0.007 * hs], lip, W('head'), 0.38, () => ({ t:[0, -0.0082 * hs, -0.001 * hs] }));
    /* Eyes, irises and pupils; upper lids swing down to blink */
    const iris = wcol(look.eyes || 0x4a3020);
    for (const e of eyes){
      waxPart(G.s, new THREE.SphereGeometry(1, 14, 10), hp(e[0], e[1], e[2]), [0, 0, 0], [0.0128 * hs, 0.0128 * hs, 0.0128 * hs], wcol(0xf3efe7), W('head'), 0.18);
      waxPart(G.s, new THREE.SphereGeometry(1, 12, 8), hp(e[0], e[1], e[2] + 0.0112), [0, 0, 0], [0.0074 * hs, 0.0074 * hs, 0.0026 * hs], iris, W('head'), 0.18);
      waxPart(G.s, new THREE.SphereGeometry(1, 10, 6), hp(e[0], e[1], e[2] + 0.0128), [0, 0, 0], [0.0036 * hs, 0.0036 * hs, 0.0012 * hs], wcol(0x0d0a08), W('head'), 0.1);
      const lid = new THREE.SphereGeometry(1, 14, 6, 0, Math.PI * 2, 0, Math.PI * 0.36), c = hp(e[0], e[1], e[2]), rr = 0.0141 * hs, ang = 1.32;
      waxPart(G.s, lid, c, [0.32, 0, 0], [rr, rr, rr], skin.clone().multiplyScalar(0.97), W('head'), 0.6, (loc, wp) => {
        const y = wp.y - c[1], z = wp.z - c[2], ny = y * Math.cos(ang) - z * Math.sin(ang), nz = y * Math.sin(ang) + z * Math.cos(ang);
        return { b:[0, ny - y, nz - z] };
      });
      /* brow */
      const bx = e[0] * 1.04, sx = Math.sign(e[0]);
      waxPart(G.s, new THREE.CapsuleGeometry(1, 2.8, 3, 8), hp(bx, 0.041, 0.0868), [0, sx * -0.34, Math.PI / 2 + sx * 0.1], [0.0034 * hs, 0.0078 * hs, 0.0036 * hs], hair.clone().lerp(skin, 0.15), W('head'), 0.8);
    }
  }

  /* --- Hair --- */
  const hairStyle = look.hairStyle || 'short', hcol = hair, hw = W('head');
  const cap = (rot, scl, off, theta, bumps, color, rough) => {
    const g = new THREE.SphereGeometry(1, 30, 16, 0, Math.PI * 2, 0, theta || Math.PI * 0.5), P = g.attributes.position;
    const rimY = Math.cos(theta || Math.PI * 0.5);
    if (bumps) for (let i = 0; i < P.count; i++){ const x = P.getX(i), y = P.getY(i), z = P.getZ(i), edge = wsm(rimY, rimY + 0.35, y), k = 1 + bumps * edge * (Math.sin(x * 23 + y * 7) * Math.sin(z * 21 - y * 11) * 0.5 + Math.sin(x * 9 - z * 13) * 0.3); P.setXYZ(i, x * k, y * k, z * k); }
    g.computeVertexNormals();
    waxPart(G.c, g, hp(off[0], off[1], off[2]), rot, [scl[0] * hs, scl[1] * hs, scl[2] * hs], color || hcol, hw, rough || 0.62);
  };
  const blob = (pos, scl, rot, bumps) => {
    const g = new THREE.SphereGeometry(1, 18, 12), P = g.attributes.position;
    if (bumps) for (let i = 0; i < P.count; i++){ const x = P.getX(i), y = P.getY(i), z = P.getZ(i), k = 1 + bumps * Math.sin(x * 17 + z * 5) * Math.sin(y * 15 - x * 9); P.setXYZ(i, x * k, y * k, z * k); }
    g.computeVertexNormals();
    waxPart(G.c, g, hp(pos[0], pos[1], pos[2]), rot || [0, 0, 0], [scl[0] * hs, scl[1] * hs, scl[2] * hs], hcol, hw, 0.62);
  };
  if (hairStyle !== 'bald' && !look.scarf){
    if (hairStyle === 'crop') cap([-0.5, 0, 0], [0.095, 0.123, 0.112], [0, 0.009, -0.007], Math.PI * 0.5, 0.02);
    else if (hairStyle === 'curly') { cap([-0.42, 0, 0], [0.118, 0.134, 0.126], [0, 0.024, -0.018], Math.PI * 0.56, 0.11); }
    else if (hairStyle === 'balding'){
      const g = new THREE.SphereGeometry(1, 30, 10, Math.PI * 0.95, Math.PI * 1.1, Math.PI * 0.34, Math.PI * 0.22), P = g.attributes.position;
      for (let i = 0; i < P.count; i++){ const k = 1 + 0.03 * Math.sin(i * 2.3); P.setXYZ(i, P.getX(i) * k, P.getY(i), P.getZ(i) * k); }
      g.computeVertexNormals();
      waxPart(G.c, g, hp(0, 0.004, -0.006), [0, 0, 0], [0.095 * hs, 0.122 * hs, 0.114 * hs], hcol.clone().multiplyScalar(0.82), hw, 0.7);
    }
    else cap([hairStyle === 'short' ? -0.42 : -0.3, 0, 0], [0.098, 0.126, 0.115], [0, 0.012, -0.009], Math.PI * 0.52, 0.025);
    if (hairStyle === 'short' || hairStyle === 'crop') for (const sx of [1, -1]) waxPart(G.c, new THREE.SphereGeometry(1, 8, 8), hp(sx * 0.084, 0.012, 0.012), [0, 0, 0], [0.008 * hs, 0.03 * hs, 0.016 * hs], hcol, hw, 0.7);
    if (hairStyle === 'bob' || hairStyle === 'long'){
      const len = hairStyle === 'long' ? 0.25 : 0.11, g = new THREE.CylinderGeometry(1, 1.12, 1, 28, 3, true, Math.PI * 0.36, Math.PI * 1.28);
      const P = g.attributes.position; for (let i = 0; i < P.count; i++){ const y = P.getY(i); P.setY(i, y); P.setX(i, P.getX(i) * (1 + 0.04 * Math.sin(i * 1.7))); }
      g.computeVertexNormals();
      waxPart(G.c, g, hp(0, 0.03 - len / 2, -0.016), [0, 0, 0], [0.104 * hs, len * hs, 0.108 * hs], hcol, hw, 0.62);
      if (hairStyle === 'long') blob([0, -0.06, -0.075], [0.085, 0.13, 0.05], [0.15, 0, 0], 0.02);
    }
    if (hairStyle === 'ponytail'){ blob([0, 0.03, -0.108], [0.03, 0.03, 0.03]); blob([0, -0.06, -0.128], [0.028, 0.08, 0.026], [0.22, 0, 0], 0.03); }
    if (hairStyle === 'bun') blob([0, 0.098, -0.07], [0.047, 0.042, 0.047], [0, 0, 0], 0.04);
    if (hairStyle === 'puffs') for (const sx of [1, -1]) blob([sx * 0.085, 0.085, -0.03], [0.05, 0.05, 0.05], [0, 0, 0], 0.08);
    if (hairStyle === 'braids') for (const sx of [1, -1]) blob([sx * 0.06, -0.1, -0.075], [0.022, 0.12, 0.022], [0.12, 0, sx * -0.12], 0.06);
  }
  if (look.scarf != null){
    const sc = wcol(look.scarf), g = new THREE.SphereGeometry(1, 30, 18, Math.PI * 0.86, Math.PI * 1.28, 0, Math.PI * 0.74);
    g.computeVertexNormals();
    waxPart(G.c, g, hp(0, 0.006, -0.004), [0.08, 0, 0], [0.1 * hs, 0.128 * hs, 0.116 * hs], sc, hw, 0.85);
    const dr = new THREE.CylinderGeometry(0.75, 1.25, 1, 26, 2, true);
    waxPart(G.c, dr, hp(0, -0.125, -0.01), [0, 0, 0], [0.09 * hs, 0.09 * hs, 0.085 * hs], sc, wmix([[WB.neck, 0.6], [WB.head, 0.4]]), 0.85);
  }
  if (look.cap != null){
    const cc = wcol(look.cap);
    cap([-0.18, 0, 0], [0.098, 0.1, 0.11], [0, 0.034, -0.004], Math.PI * 0.5, 0, cc, 0.78);
    waxPart(G.c, new THREE.CylinderGeometry(1, 1, 1, 20, 1, false, -Math.PI * 0.42, Math.PI * 0.84), hp(0, 0.044, 0.094), [0.2, 0, 0], [0.086 * hs, 0.006 * hs, 0.072 * hs], cc, hw, 0.75);
    waxPart(G.c, new THREE.SphereGeometry(1, 8, 6), hp(0, 0.137, -0.002), [0, 0, 0], [0.008 * hs, 0.005 * hs, 0.008 * hs], cc, hw, 0.75);
  }
  if (look.glasses){
    const fr = wcol(typeof look.glasses === 'number' ? look.glasses : 0x2a221c);
    for (const e of eyes) waxPart(G.c, new THREE.TorusGeometry(1, 0.13, 6, 18), hp(e[0], e[1] - 0.001, e[2] + 0.018), [0, 0, 0], [0.0175 * hs, 0.0155 * hs, 0.0175 * hs], fr, hw, 0.35);
    waxPart(G.c, new THREE.BoxGeometry(1, 1, 1), hp(0, eyes[0][1] + 0.004, eyes[0][2] + 0.02), [0, 0, 0], [0.014 * hs, 0.003 * hs, 0.003 * hs], fr, hw, 0.35);
    for (const sx of [1, -1]) waxPart(G.c, new THREE.BoxGeometry(1, 1, 1), hp(sx * 0.0865, eyes[0][1] + 0.004, 0.036), [0, 0, 0], [0.003 * hs, 0.003 * hs, 0.088 * hs], fr, hw, 0.35);
  }
  if (look.lanyard != null){
    const lc = wcol(look.lanyard), cw = W('chest');
    for (const sx of [1, -1]) waxPart(G.c, new THREE.BoxGeometry(1, 1, 1), [sx * 0.035, hipJ + 0.43, 0.085 + T.bust * 0.02], [0.55, 0, sx * 0.32], [0.008, 0.15, 0.004], lc, cw, 0.8);
    waxPart(G.c, new THREE.BoxGeometry(1, 1, 1), [0, hipJ + 0.335, 0.122 + T.bust * 0.032], [-0.12, 0, 0], [0.05, 0.07, 0.004], wcol(0xf4f1ea), cw, 0.5);
  }

  /* Scale everything to the body type */
  for (const g of [G.s, G.c]) for (let i = 0; i < g.P.length; i++) g.P[i] *= S;
  for (const g of [G.s, G.c]) for (let i = 0; i < g.MB.length; i++){ g.MB[i] *= S; g.MT[i] *= S; }

  /* Bones */
  const root = new THREE.Group(), bones = [];
  for (const name of WAXB){
    const b = new THREE.Bone(); b.name = name; const j = J[name], pj = PAR[name] ? J[PAR[name]] : [0, 0, 0];
    b.position.set((j[0] - pj[0]) * S, (j[1] - pj[1]) * S, (j[2] - pj[2]) * S);
    b.rotation.order = WAX_ORD[bones.length];
    bones.push(b);
    if (PAR[name]) bones[WB[PAR[name]]].add(b); else root.add(b);
  }
  root.updateMatrixWorld(true);
  const skel = new THREE.Skeleton(bones);
  const cloth = new THREE.SkinnedMesh(G.c.build(false), WAX.mats.cloth), body = new THREE.SkinnedMesh(G.s.build(true), WAX.mats.skin);
  for (const m of [cloth, body]){ root.add(m); m.bind(skel); m.frustumCulled = true; m.castShadow = false; m.receiveShadow = false; m.userData.noMerge = true; }
  body.morphTargetInfluences = [0, 0];
  /* Fixed culling bounds (the pose changes, the bind-pose bounds would not), and a plain box for clicks */
  const tall = (HC[1] + 0.14) * S;
  for (const m of [cloth, body]) m.boundingSphere = new THREE.Sphere(new THREE.Vector3(0, tall * 0.5, 0), tall * 0.8);
  if (!WAX.pickGeo) WAX.pickGeo = new THREE.BoxGeometry(1, 1, 1);
  const pick = new THREE.Mesh(WAX.pickGeo, PICK_PROXY); pick.scale.set(0.6 * S, tall, 0.42 * S); pick.position.y = tall / 2; root.add(pick);
  const fig = { root, bones, skel, cloth, body, pick, look, S, hs, J, headC:HC.map((v) => v * S), eyesC:eyes, pose:new Float32Array(WAX_N), t:Math.random() * 10, blinkT:1 + Math.random() * 3 };
  root.userData.noMerge = true;
  WAX.figs.push(fig);
  return fig;
}

/* ---------- Materials: matte cloth with per-vertex roughness; waxy skin with a soft sheen ---------- */
function waxMats(){
  if (WAX.mats) return WAX.mats;
  const rough = (m, key) => {
    m.onBeforeCompile = (sh) => {
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute float aRough;\nvarying float vRough;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvRough = aRough;');
      sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying float vRough;').replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\nroughnessFactor = clamp(roughnessFactor * vRough, 0.04, 1.0);');
    };
    m.customProgramCacheKey = () => key;
    return m;
  };
  const cloth = rough(new THREE.MeshStandardMaterial({ vertexColors:true, roughness:1, metalness:0 }), 'wax-cloth');
  const skin = rough(new THREE.MeshPhysicalMaterial({ vertexColors:true, roughness:0.7, metalness:0, clearcoat:0.32, clearcoatRoughness:0.38, sheen:0.45, sheenRoughness:0.55, sheenColor:new THREE.Color(0xffc9ad) }), 'wax-skin');
  WAX.mats = { cloth, skin };
  return WAX.mats;
}

/* ---------- Poses ----------
   A dense pose: 17 bones x 3 Euler angles, then root x, z, yaw, drop, then talk and headset, then hand
   shapes (grip left/right: -1 open .. 1 fist; point left/right: 0..1). */
const WAX_N = 17 * 3 + 10, WR = 51;
const D2R = Math.PI / 180;
/* Named joints in degrees: hips/spine/chest [bend, side, twist]; neck/head [nod, tilt, turn];
   armL/armR [forward, out, twist]; elL/elR bend; handL/handR [bend, side, twist]; legL/legR [forward, out, twist];
   knL/knR bend; footL/footR up; at [x, z] on the stage; ry yaw in degrees; dy drop in metres */
function waxDense(p, out){
  const o = out || new Float32Array(WAX_N);
  o.fill(0);
  /* a relaxed stance underneath every pose */
  o[WB.shL * 3 + 2] = 6 * D2R; o[WB.shR * 3 + 2] = -6 * D2R; o[WB.elL * 3] = -9 * D2R; o[WB.elR * 3] = -9 * D2R;
  const tri = (b, v, mx, my, mz) => { if (!v) return; const i = WB[b] * 3; o[i] = v[0] * D2R * mx; o[i + 2] = (v[1] || 0) * D2R * mz; o[i + 1] = (v[2] || 0) * D2R * my; };
  /* trunk: x bend, z side, y twist */
  for (const k of ['hips', 'spine', 'chest']) tri(k, p[k], 1, 1, -1);
  if (p.neck) tri('neck', p.neck, 1, 1, -1);
  if (p.head) tri('head', p.head, 1, 1, -1);
  const arm = (b, v, s) => { if (!v) return; const i = WB[b] * 3; o[i] = -v[0] * D2R; o[i + 2] = s * (v[1] == null ? 6 : v[1]) * D2R; o[i + 1] = s * (v[2] || 0) * D2R; };
  arm('shL', p.armL, 1); arm('shR', p.armR, -1);
  if (p.elL != null) o[WB.elL * 3] = -p.elL * D2R;
  if (p.elR != null) o[WB.elR * 3] = -p.elR * D2R;
  const hand = (b, v, s) => { if (!v) return; const i = WB[b] * 3; o[i] = -v[0] * D2R; o[i + 2] = s * (v[1] || 0) * D2R; o[i + 1] = s * (v[2] || 0) * D2R; };
  hand('wrL', p.handL, 1); hand('wrR', p.handR, -1);
  const leg = (b, v, s) => { if (!v) return; const i = WB[b] * 3; o[i] = -v[0] * D2R; o[i + 2] = s * (v[1] || 0) * D2R; o[i + 1] = s * (v[2] || 0) * D2R; };
  leg('thL', p.legL, 1); leg('thR', p.legR, -1);
  if (p.knL != null) o[WB.knL * 3] = p.knL * D2R;
  if (p.knR != null) o[WB.knR * 3] = p.knR * D2R;
  if (p.footL != null) o[WB.anL * 3] = -p.footL * D2R;
  if (p.footR != null) o[WB.anR * 3] = -p.footR * D2R;
  if (p.at){ o[WR] = p.at[0]; o[WR + 1] = p.at[1]; }
  o[WR + 2] = (p.ry || 0) * D2R; o[WR + 3] = p.dy || 0; o[WR + 4] = p.talk || 0; o[WR + 5] = p.hs == null ? 0 : p.hs;
  o[WR + 6] = p.gripL || 0; o[WR + 7] = p.gripR || 0; o[WR + 8] = p.pointL || 0; o[WR + 9] = p.pointR || 0;
  return o;
}
/* Pose presets; a key can name one and override joints */
const WAX_POSE = {
  stand:{},
  ease:{ armL:[4, 8, 0], armR:[4, 8, 0], elL:14, elR:14, hips:[0, 1.5, 0], legL:[0, 2, 0], legR:[2, 3, 0], knR:5 },
  hold:{ armL:[28, 10, -20], armR:[28, 10, -20], elL:78, elR:78, handL:[0, 0, 40], handR:[0, 0, 40], gripL:0.75, gripR:0.75 },
  present:{ armR:[52, 18, -30], elR:42, handR:[0, 0, 70], armL:[6, 8, 0], elL:16, head:[4, 0, -8], gripR:-0.7 },
  point:{ armR:[78, 22, 0], elR:6, head:[-6, 0, 0], chest:[0, 0, -6], pointR:1 },
  wave:{ armR:[20, 74, 0], elR:96, handR:[0, 0, 0], head:[-2, 4, 0], gripR:-0.9 },
  cheer:{ armL:[150, 22, 0], armR:[150, 22, 0], elL:20, elR:20, head:[-12, 0, 0], chest:[-4, 0, 0], gripL:0.9, gripR:0.9 },
  clap:{ armL:[48, 6, -36], armR:[48, 6, -36], elL:84, elR:84, handL:[0, 0, 60], handR:[0, 0, 60], gripL:-0.8, gripR:-0.8 },
  faceHands:{ armL:[118, 20, -40], armR:[118, 20, -40], elL:128, elR:128, handL:[20, 0, 70], handR:[20, 0, 70], head:[-3, 0, 0] },
  reach:{ armR:[96, 10, 0], elR:14, armL:[30, 22, 0], elL:30, chest:[4, 0, -8], head:[-8, 0, -6], gripR:-0.5 },
  think:{ armR:[34, 4, -40], elR:138, handR:[30, 0, 40], armL:[22, 4, -60], elL:96, head:[4, 6, 0], gripR:0.5, gripL:0.3 },
  type:{ armL:[38, 4, -26], armR:[38, 4, -26], elL:64, elR:64, handL:[-18, 0, 80], handR:[-18, 0, 80], head:[22, 0, 0], chest:[6, 0, 0], gripL:0.35, gripR:0.35 },
  sit:{ legL:[86, 6, 0], legR:[86, 6, 0], knL:88, knR:88, footL:2, footR:2, dy:-0.43, armL:[30, 8, -20], armR:[30, 8, -20], elL:50, elR:50 },
  sitFloor:{ legL:[84, 32, 30], legR:[84, 32, 30], knL:142, knR:142, footL:20, footR:20, dy:-0.84, armL:[30, 14, -30], armR:[30, 14, -30], elL:60, elR:60, spine:[6, 0, 0] },
  kneel:{ legL:[96, 6, 0], knL:96, footL:0, legR:[-12, 4, 0], knR:96, footR:-40, dy:-0.38, spine:[4, 0, 0] },
  crouch:{ legL:[78, 8, 0], legR:[60, 10, 0], knL:110, knR:96, footL:20, footR:12, dy:-0.3, spine:[18, 0, 0], head:[-14, 0, 0] },
  lookUp:{ head:[-26, 0, 0], neck:[-8, 0, 0], chest:[-4, 0, 0] },
  tablet:{ armL:[60, 12, -40], armR:[60, 12, -40], elL:70, elR:70, handL:[-24, 0, 70], handR:[-24, 0, 70], head:[16, 0, 0], gripL:0.55, gripR:0.55 },
  tabletUp:{ armL:[88, 12, -40], armR:[88, 12, -40], elL:40, elR:40, handL:[-30, 0, 70], handR:[-30, 0, 70], head:[2, 0, 0], gripL:0.55, gripR:0.55 },
  walkPose:{}
};
function waxKeyDense(k){
  const merged = {};
  for (const name of (Array.isArray(k.p) ? k.p : k.p ? [k.p] : [])) Object.assign(merged, WAX_POSE[name]);
  for (const key in k) if (!['t', 'p', 'look'].includes(key)) merged[key] = k[key];
  return waxDense(merged);
}

/* ---------- Playing a figure's keys: eased, with walking, breathing, blinking and talk ---------- */
function waxTrack(keys, home){
  let at = home.at, ry = home.ry || 0;
  const tr = keys.map((k) => {
    const kk = Object.assign({}, k);
    if (!kk.at) kk.at = at; else at = kk.at;
    if (kk.ry == null) kk.ry = ry; else ry = kk.ry;
    return { t:k.t, d:waxKeyDense(kk), m:new Float32Array(WAX_N) };
  });
  waxTangents(tr);
  return tr;
}
/* Motion flows through the keys instead of stopping at each one: a monotone cubic per channel
   (Fritsch-Butland), so a joint keeps moving through a key on its way somewhere and only
   comes to rest where it turns around or holds, and never swings past a key */
function waxTangents(tr){
  for (let i = 1; i < tr.length - 1; i++){
    const A = tr[i - 1], B = tr[i], C = tr[i + 1], h0 = B.t - A.t, h1 = C.t - B.t;
    if (h0 < 1e-4 || h1 < 1e-4) continue;
    for (let j = 0; j < WAX_N; j++){
      const d0 = (B.d[j] - A.d[j]) / h0, d1 = (C.d[j] - B.d[j]) / h1;
      B.m[j] = d0 * d1 > 0 ? 3 * (h0 + h1) / ((2 * h1 + h0) / d0 + (h1 + 2 * h0) / d1) : 0;
    }
  }
}
const _wa = new Float32Array(WAX_N);
function waxSample(fig, t){
  const tr = fig.track, o = fig.pose;
  let i = 0; while (i < tr.length - 1 && tr[i + 1].t <= t) i++;
  const A = tr[i], B = tr[Math.min(i + 1, tr.length - 1)];
  if (A === B || t <= A.t){ o.set(A.d); return; }
  const h = B.t - A.t, u = clamp((t - A.t) / h, 0, 1), u2 = u * u, u3 = u2 * u;
  const h00 = 2 * u3 - 3 * u2 + 1, h10 = (u3 - 2 * u2 + u) * h, h01 = 3 * u2 - 2 * u3, h11 = (u3 - u2) * h;
  for (let j = 0; j < WAX_N; j++) o[j] = h00 * A.d[j] + h10 * A.m[j] + h01 * B.d[j] + h11 * B.m[j];
  /* Moving between keys means walking: legs and arms swing, the body faces where it goes */
  const dx = B.d[WR] - A.d[WR], dz = B.d[WR + 1] - A.d[WR + 1], dist = Math.hypot(dx, dz);
  if (dist > 0.18){
    const k = clamp(((o[WR] - A.d[WR]) * dx + (o[WR + 1] - A.d[WR + 1]) * dz) / (dist * dist), 0, 1);
    const e = wsm(0, 0.12, u) * (1 - wsm(0.88, 1, u)), ph = dist * k / (0.62 * fig.S) * Math.PI, sp = Math.sin(ph);
    const yawTo = Math.atan2(dx, dz), y0 = o[WR + 2];
    let dd = yawTo - y0; while (dd > Math.PI) dd -= Math.PI * 2; while (dd < -Math.PI) dd += Math.PI * 2;
    o[WR + 2] = y0 + dd * wsm(0, 0.2, u) * (1 - wsm(0.8, 1, u));
    o[WB.thL * 3] += -26 * D2R * e * sp; o[WB.thR * 3] += 26 * D2R * e * sp;
    o[WB.knL * 3] += 34 * D2R * e * Math.max(0, -Math.cos(ph - 0.4)); o[WB.knR * 3] += 34 * D2R * e * Math.max(0, Math.cos(ph - 0.4));
    o[WB.anL * 3] += 10 * D2R * e * sp; o[WB.anR * 3] += -10 * D2R * e * sp;
    o[WB.shL * 3] += 16 * D2R * e * sp; o[WB.shR * 3] += -16 * D2R * e * sp;
    o[WB.hips * 3 + 1] += 5 * D2R * e * sp; o[WB.chest * 3 + 1] -= 6 * D2R * e * sp;
    o[WR + 3] -= 0.022 * e * Math.abs(Math.cos(ph));
  }
}
function waxApply(fig, live, dt){
  const o = fig.pose, b = fig.bones;
  if (fig.rb){ waxApplyHuman(fig, live, dt); return; }
  if (live){
    /* Breathing, a slow weight shift and small head moves: only while the scene is live */
    fig.t += dt; const t = fig.t, br = Math.sin(t * 1.6);
    o[WB.chest * 3] += 1.1 * D2R * br; o[WB.shL * 3 + 2] += 0.8 * D2R * br; o[WB.shR * 3 + 2] -= 0.8 * D2R * br;
    o[WB.hips * 3 + 2] += 1.1 * D2R * Math.sin(t * 0.47 + fig.S * 7);
    o[WB.head * 3 + 1] += 2.2 * D2R * Math.sin(t * 0.37 + fig.S * 3); o[WB.head * 3] += 1.4 * D2R * Math.sin(t * 0.53 + 1.2);
    fig.blinkT -= dt; if (fig.blinkT < -0.14) fig.blinkT = 2 + Math.random() * 3.6;
    fig.body.morphTargetInfluences[0] = fig.blinkT < 0 ? Math.sin(-fig.blinkT / 0.14 * Math.PI) : 0;
    const talk = o[WR + 4];
    fig.body.morphTargetInfluences[1] = talk > 0.01 ? talk * clamp(0.5 + 0.5 * Math.sin(t * 15.5) * Math.sin(t * 4.3 + 1), 0, 1) : 0;
  } else { fig.body.morphTargetInfluences[0] = 0; fig.body.morphTargetInfluences[1] = 0; }
  for (let i = 0; i < 17; i++) b[i].rotation.set(o[i * 3], o[i * 3 + 1], o[i * 3 + 2]);
  fig.root.position.set(o[WR], o[WR + 3] * fig.S, o[WR + 1]);
  fig.root.rotation.y = o[WR + 2];
}
/* Realistic reenactors: the same pose language, plus lids, jaw, eyes and hands */
function waxApplyHuman(fig, live, dt){
  const o = fig.pose;
  if (live){
    fig.t += dt; const t = fig.t, br = Math.sin(t * 1.6);
    o[WB.chest * 3] += 1.1 * D2R * br; o[WB.shL * 3 + 2] += 0.8 * D2R * br; o[WB.shR * 3 + 2] -= 0.8 * D2R * br;
    o[WB.hips * 3 + 2] += 1.1 * D2R * Math.sin(t * 0.47 + fig.S * 7);
    o[WB.head * 3 + 1] += 2.2 * D2R * Math.sin(t * 0.37 + fig.S * 3); o[WB.head * 3] += 1.4 * D2R * Math.sin(t * 0.53 + 1.2);
    fig.blinkT -= dt; if (fig.blinkT < -0.16) fig.blinkT = 2 + Math.random() * 3.6;
    fig.blink = fig.blinkT < 0 ? Math.sin(-fig.blinkT / 0.16 * Math.PI) : 0;
    const talk = o[WR + 4];
    fig.talk = talk > 0.01 ? talk * clamp(0.45 + 0.55 * Math.sin(t * 15.5) * Math.sin(t * 4.3 + 1), 0, 1) * 0.75 : 0;
    fig.smile = talk > 0.01 ? 0.25 : 0.35;
    hkSaccade(fig, dt);
  } else { fig.blink = 0; fig.talk = 0; fig.smile = 0.2; }
  hkPose(fig, o);
  hkFingers(fig, o[WR + 6], o[WR + 7], o[WR + 8], o[WR + 9]);
  hkFace(fig);
  fig.root.position.set(o[WR], o[WR + 3] * fig.S, o[WR + 1]);
  fig.root.rotation.y = o[WR + 2];
}
/* A headset model, shared by every figure that wears one */
function waxHeadsetGeo(){
  if (WAX.headset) return WAX.headset;
  const white = new THREE.MeshStandardMaterial({ color:0xeceae6, roughness:0.38 }), black = new THREE.MeshStandardMaterial({ color:0x1d2024, roughness:0.32, metalness:0.1 }), strap = new THREE.MeshStandardMaterial({ color:0x3b4046, roughness:0.75 });
  const RB = XT.RoundedBoxGeometry;
  const body = RB ? new RB(0.19, 0.108, 0.1, 3, 0.03) : new THREE.BoxGeometry(0.19, 0.108, 0.1);
  const face = RB ? new RB(0.168, 0.086, 0.012, 2, 0.006) : new THREE.BoxGeometry(0.168, 0.086, 0.012);
  WAX.headset = { white, black, strap, body, face, band:new THREE.TorusGeometry(0.098, 0.011, 6, 26), top:new THREE.TorusGeometry(0.1, 0.009, 6, 20, Math.PI) };
  return WAX.headset;
}
function waxHeadset(){
  const H = waxHeadsetGeo(), g = new THREE.Group();
  const b = new THREE.Mesh(H.body, H.white); g.add(b);
  const f = new THREE.Mesh(H.face, H.black); f.position.z = 0.05; g.add(f);
  const band = new THREE.Mesh(H.band, H.strap); band.rotation.x = Math.PI / 2; band.position.set(0, 0.004, -0.088); band.scale.set(1, 1.15, 1); g.add(band);
  const top = new THREE.Mesh(H.top, H.strap); top.rotation.y = Math.PI / 2; top.position.set(0, 0.0, -0.075); g.add(top);
  return g;
}
