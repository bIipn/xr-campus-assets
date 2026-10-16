/* ================================================================
   Room 102: Science Lab stations
   ================================================================ */
function labMat(hex, rough, metal, extra){ return new THREE.MeshStandardMaterial(Object.assign({ color:srgb(hex), roughness:rough == null ? 0.6 : rough, metalness:metal || 0 }, extra || {})); }
function glassMat(op){ return new THREE.MeshStandardMaterial({ color:0xeaf6fb, transparent:true, opacity:op || 0.26, roughness:0.04, metalness:0.1, depthWrite:false, side:THREE.DoubleSide }); }
/* A little digital display: a canvas we can redraw */
function makeDisplay(w, h, W, H, color){
  const c = keepCanvas(mk(W || 256, H || 80)), t = tex(c), m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map:t, toneMapped:false }));
  m.userData.keepBasic = true;
  const D = { c, t, m, color:color || '#7dffb0', text:null, set(txt, sub){ const k = txt + '|' + (sub || ''); if (k === D.text) return; D.text = k; const ctx = c.getContext('2d'); ctx.fillStyle = '#0d1512'; ctx.fillRect(0, 0, c.width, c.height); ctx.fillStyle = D.color; ctx.textAlign = 'right'; ctx.textBaseline = 'middle'; ctx.font = '700 ' + Math.round(c.height * (sub ? 0.5 : 0.62)) + 'px ' + F.type; ctx.fillText(txt, c.width - 12, c.height * (sub ? 0.38 : 0.52)); if (sub){ ctx.font = '400 ' + Math.round(c.height * 0.24) + 'px ' + F.type; ctx.fillStyle = 'rgba(125,255,176,0.7)'; ctx.fillText(sub, c.width - 12, c.height * 0.8); } t.needsUpdate = true; wake(); } };
  D.set('');
  return D;
}
/* A simple chart on a canvas, styled for the dark station panel */
function drawChart(c, o){
  const ctx = c.getContext('2d'), W = c.width, H = c.height, L = 54, R = 16, T = 18, B = 44, pw = W - L - R, ph = H - T - B;
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = 'rgba(13,22,19,0.6)'; ctx.fillRect(0, 0, W, H);
  const lx = (v) => o.logx ? Math.log(v) : v;
  const X = (v) => L + (lx(v) - lx(o.x0)) / (lx(o.x1) - lx(o.x0)) * pw, Y = (v) => T + (1 - (v - o.y0) / (o.y1 - o.y0)) * ph;
  ctx.font = '400 13px ' + F.type; ctx.lineWidth = 1;
  for (const v of o.yt){ ctx.strokeStyle = 'rgba(239,231,213,0.12)'; ctx.beginPath(); ctx.moveTo(L, Y(v) + 0.5); ctx.lineTo(W - R, Y(v) + 0.5); ctx.stroke(); ctx.fillStyle = 'rgba(239,231,213,0.7)'; ctx.textAlign = 'right'; ctx.textBaseline = 'middle'; ctx.fillText(o.yf ? o.yf(v) : String(v), L - 7, Y(v)); }
  for (const [v, lab] of o.xt){ ctx.strokeStyle = 'rgba(239,231,213,0.12)'; ctx.beginPath(); ctx.moveTo(X(v) + 0.5, T); ctx.lineTo(X(v) + 0.5, H - B); ctx.stroke(); ctx.fillStyle = 'rgba(239,231,213,0.7)'; ctx.textAlign = 'center'; ctx.textBaseline = 'top'; ctx.fillText(lab, X(v), H - B + 6); }
  ctx.fillStyle = '#cda961'; ctx.textAlign = 'center'; ctx.textBaseline = 'bottom'; ctx.fillText(o.xl || '', L + pw / 2, H - 4);
  ctx.save(); ctx.translate(13, T + ph / 2); ctx.rotate(-Math.PI / 2); ctx.textBaseline = 'middle'; ctx.fillText(o.yl || '', 0, 0); ctx.restore();
  ctx.strokeStyle = 'rgba(239,231,213,0.45)'; ctx.strokeRect(L + 0.5, T + 0.5, pw, ph);
  ctx.save(); ctx.beginPath(); ctx.rect(L, T, pw, ph); ctx.clip();
  for (const s of o.series){
    if (s.bars){ ctx.fillStyle = s.color; for (const [a, b, v] of s.bars){ const x0 = X(a), x1 = X(b); ctx.fillRect(Math.min(x0, x1) + 1, Y(v), Math.abs(x1 - x0) - 2, Y(o.y0) - Y(v)); } continue; }
    if (s.vline != null){ ctx.strokeStyle = s.color; ctx.setLineDash([5, 4]); ctx.beginPath(); ctx.moveTo(X(s.vline), T); ctx.lineTo(X(s.vline), H - B); ctx.stroke(); ctx.setLineDash([]); if (s.label){ ctx.fillStyle = s.color; ctx.textAlign = 'left'; ctx.textBaseline = 'top'; ctx.fillText(s.label, X(s.vline) + 5, T + 4); } continue; }
    if (s.hline != null){ ctx.strokeStyle = s.color; ctx.setLineDash([5, 4]); ctx.beginPath(); ctx.moveTo(L, Y(s.hline)); ctx.lineTo(W - R, Y(s.hline)); ctx.stroke(); ctx.setLineDash([]); if (s.label){ ctx.fillStyle = s.color; ctx.textAlign = 'right'; ctx.textBaseline = 'bottom'; ctx.fillText(s.label, W - R - 4, Y(s.hline) - 3); } continue; }
    const P = s.pts.filter((p) => p[0] >= o.x0 * (o.logx ? 0.999 : 1) || !o.logx);
    if (s.line !== false && P.length > 1){ ctx.strokeStyle = s.color; ctx.lineWidth = s.w || 2.5; ctx.lineJoin = 'round'; ctx.beginPath(); P.forEach((p, i) => i ? ctx.lineTo(X(p[0]), Y(p[1])) : ctx.moveTo(X(p[0]), Y(p[1]))); ctx.stroke(); }
    if (s.dots){ ctx.fillStyle = s.color; for (const p of P){ ctx.beginPath(); ctx.arc(X(p[0]), Y(p[1]), s.r || 4, 0, Math.PI * 2); ctx.fill(); } }
  }
  ctx.restore();
}

/* ---------- 1. Sieve analysis (particle size distribution) ---------- */
const SIEVES = [['6', 3350, 3], ['12', 1700, 5], ['20', 850, 10], ['30', 600, 20], ['40', 425, 30], ['50', 300, 40], ['70', 212, 50], ['100', 150, 70], ['140', 106, 100], ['200', 75, 140], ['270', 53, 200], ['Pan', 0, 300]];
const SV = { x:33.58, z:-9.0, y:0.9, g:null, stack:null, sieves:[], arm:null, disp:null, bal:null, run:0, shakeT:0, dryT:-1, frac:1, dishF:0, pans:[0, 0] };
/* Where you stand for each part of the test, facing the bench */
const svSpot = (z, pitch) => ({ x:33.02 - (narrow() ? 0.06 : 0), z, yaw:-Math.PI / 2, pitch:pitch - (narrow() ? 0.1 : 0), bench:0.9 });
SV.spots = { splitter:() => svSpot(-7.85, -0.5), oven:() => svSpot(-6.95, -0.3), shaker:() => svSpot(-9.0, -0.46), balance:() => svSpot(-10.75, -0.52) };
/* Where things rest on the bench */
SV.home = { tray:[33.6, 0.9, -8.1], trayOven:[33.58, 0.9, -7.05], trayBal:[33.5, 0.9, -10.3], cover:[33.38, 0.9, -9.62], dish:[33.61, 0.998, -10.75], dishPark:[33.33, 0.9, -8.5], done:[33.38, 0.9, -11.35], pileA:[33.58, 0.9, -9.37], pileB:[33.58, 0.9, -8.63], ovenIn:[33.62, 0.96, -6.62] };
/* Hands on the equipment: where each palm touches, in the thing's own frame */
const SV_G = {
  sieve:{ L:{ p:[0, 0, -0.104], into:[0, 0, 1], fingers:[0, -1, 0.35], curl:0.55 }, R:{ p:[0, 0, 0.104], into:[0, 0, -1], fingers:[0, -1, 0.35], curl:0.55 } },
  cover:{ L:{ p:[0, 0, -0.106], into:[0, 0, 1], fingers:[0, -1, 0.35], curl:0.55 }, R:{ p:[0, 0, 0.106], into:[0, 0, -1], fingers:[0, -1, 0.35], curl:0.55 } },
  tray:{ L:{ p:[0, 0.012, -0.142], into:[0, 0, 1], fingers:[0, -1, 0.25], curl:0.6 }, R:{ p:[0, 0.012, 0.142], into:[0, 0, -1], fingers:[0, -1, 0.25], curl:0.6 } },
  pan:{ L:{ p:[0, 0.015, -0.062], into:[0, 0, 1], fingers:[0, -1, 0.25], curl:0.6 }, R:{ p:[0, 0.015, 0.062], into:[0, 0, -1], fingers:[0, -1, 0.25], curl:0.6 } },
  dish:{ L:{ p:[0, 0.012, -0.062], into:[0, 0, 1], fingers:[0, -1, 0.35], curl:0.62 }, R:{ p:[0, 0.012, 0.062], into:[0, 0, -1], fingers:[0, -1, 0.35], curl:0.62 } },
  clamp:{ L:{ p:[0, 0.02, -0.235], into:[0, -1, 0], fingers:[0, 0, 1], curl:0.5 }, R:{ p:[0, 0.02, 0.235], into:[0, -1, 0], fingers:[0, 0, -1], curl:0.5 } },
  handle:{ R:{ p:[-0.046, 0, -0.355], into:[1, 0, 0], fingers:[0, 0, 1], curl:0.7 } },
  /* An index finger on a button: pressed from the front, or down from above */
  pressF:{ R:{ p:[-0.105, 0.012, 0.012], into:[0, -1, 0], fingers:[1, 0, 0], curl:0.1, point:1, out:0.35 } },
  pressD:{ R:{ p:[-0.058, 0.09, 0.012], into:[-0.8, -0.6, 0], fingers:[0.6, -0.8, 0], curl:0.1, point:1, out:0.35 } }
};
const svCarry = (dy) => hBody([0, dy == null ? -0.12 : dy, 0.33], [0, -90, 0]);
function erf(x){ const s = Math.sign(x); x = Math.abs(x); const t = 1 / (1 + 0.3275911 * x); return s * (1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x)); }
function buildSieveStation(M){
  const g = new THREE.Group(); g.userData.noMerge = true; scene.add(g); SV.g = g;
  const green = labMat(0x3d5a50, 0.5, 0.2), brass = labMat(0xc9a65a, 0.32, 0.8), steel = labMat(0xb9c0c6, 0.3, 0.7), dark = labMat(0x23282b, 0.5), alu = labMat(0xc9ced2, 0.3, 0.6), sand = labMat(0xdccfa6, 0.95);
  /* The shaker: a base with a timer and a START button, two rods and a clamp bar that comes down on the cover */
  addBox(0.46, 0.3, 0.52, green, SV.x, SV.y + 0.15, SV.z, 0, g);
  addBox(0.47, 0.02, 0.53, dark, SV.x, SV.y + 0.3, SV.z, 0, g);
  SV.disp = makeDisplay(0.13, 0.045, 256, 88); SV.disp.m.position.set(SV.x - 0.232, SV.y + 0.19, SV.z + 0.13); SV.disp.m.rotation.y = -Math.PI / 2; g.add(SV.disp.m); SV.disp.set('10:00', 'TIMER');
  SV.btnStart = new THREE.Group(); SV.btnStart.position.set(SV.x - 0.232, SV.y + 0.1, SV.z + 0.13); g.add(SV.btnStart);
  addBox(0.012, 0.034, 0.05, labMat(0x2f9d5a, 0.4), -0.004, 0, 0, 0, SV.btnStart);
  addPlane(0.044, 0.02, basicMat(drawTableCard('START', ' ')), -0.0105, 0.003, 0, -Math.PI / 2, SV.btnStart);
  for (const s of [-1, 1]) addCyl(0.011, 0.011, 0.66, steel, SV.x, SV.y + 0.63, SV.z + s * 0.165, 12, g);
  addBox(0.08, 0.66, 0.08, dark, SV.x + 0.17, SV.y + 0.63, SV.z, 0, g);
  SV.clamp = new THREE.Group(); SV.clamp.position.set(SV.x, SV.y + 0.82, SV.z); g.add(SV.clamp);
  addBox(0.07, 0.03, 0.4, steel, 0, 0, 0, 0, SV.clamp);
  for (const s of [-1, 1]){ addCyl(0.02, 0.02, 0.05, dark, 0, 0.0, s * 0.165, 12, SV.clamp); addCyl(0.028, 0.028, 0.02, brass, 0, 0.03, s * 0.235, 12, SV.clamp); }
  const stack = new THREE.Group(); stack.position.set(SV.x, SV.y + 0.3, SV.z); g.add(stack); SV.stack = stack;
  const sGeo = new THREE.CylinderGeometry(0.102, 0.102, 0.026, 36), rGeo = new THREE.CylinderGeometry(0.1045, 0.1045, 0.004, 36), meshGeo = new THREE.CircleGeometry(0.098, 28);
  const meshMat = labMat(0x8a7a52, 0.6, 0.4), panMat = labMat(0xc0c6cb, 0.28, 0.75);
  SIEVES.forEach((s, i) => {
    const sg = new THREE.Group();
    sg.add(new THREE.Mesh(sGeo, i === SIEVES.length - 1 ? panMat : brass));
    const ring = new THREE.Mesh(rGeo, dark); ring.position.y = -0.012; sg.add(ring);
    const mesh = new THREE.Mesh(meshGeo, meshMat); mesh.rotation.x = -Math.PI / 2; mesh.position.y = 0.0135; sg.add(mesh);
    const lab = addPlane(0.05, 0.016, basicMat(drawTableCard(i === SIEVES.length - 1 ? 'PAN' : '#' + s[0], ' ')), -0.1025, 0.0, 0, -Math.PI / 2, sg); lab.userData.keepBasic = true;
    const held = new THREE.Mesh(new THREE.CylinderGeometry(0.097, 0.097, 0.006, 28), sand); held.position.y = 0.017; held.visible = false; sg.add(held); sg.userData.held = held;
    g.add(sg); SV.sieves.push({ g:sg, i });
  });
  const cover = new THREE.Group(); g.add(cover); SV.cover = cover;
  cover.add(new THREE.Mesh(new THREE.CylinderGeometry(0.104, 0.104, 0.014, 36), brass));
  const cork = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.012, 20), labMat(0x9c7a52, 0.9)); cork.position.y = 0.012; cover.add(cork);
  const arm = new THREE.Group(); arm.position.set(SV.x + 0.16, SV.y + 0.75, SV.z); g.add(arm); SV.arm = arm;
  addBox(0.2, 0.035, 0.05, dark, -0.1, 0, 0, 0, arm);
  addBox(0.05, 0.07, 0.05, steel, -0.16, -0.05, 0, 0, arm);
  /* Balance: a pan, a readout, a TARE button on top and an empty weighing dish on the pan */
  const bz = -10.75;
  addBox(0.34, 0.09, 0.38, labMat(0xe9e6df, 0.5), SV.x, SV.y + 0.045, bz, 0, g);
  addBox(0.1, 0.06, 0.2, labMat(0xd9d5cc, 0.5), SV.x - 0.12, SV.y + 0.06, bz, 0, g);
  addCyl(0.095, 0.095, 0.008, steel, SV.x + 0.03, SV.y + 0.094, bz, 32, g);
  SV.bal = makeDisplay(0.12, 0.04, 256, 84); SV.bal.m.position.set(SV.x - 0.172, SV.y + 0.062, bz); SV.bal.m.rotation.y = -Math.PI / 2; g.add(SV.bal.m); SV.bal.set('0.00 g');
  SV.btnTare = new THREE.Group(); SV.btnTare.position.set(SV.x - 0.12, SV.y + 0.09, bz - 0.13); g.add(SV.btnTare);
  addBox(0.04, 0.012, 0.03, labMat(0x2f6b9d, 0.4), 0, 0, 0, 0, SV.btnTare);
  addPlane(0.036, 0.016, basicMat(drawTableCard('TARE', ' ')), 0, 0.0065, 0, 0, SV.btnTare).rotation.x = -Math.PI / 2;
  SV.balTop = SV.y + 0.098; SV.balX = SV.x + 0.03; SV.balZ = bz;
  const dish = new THREE.Group(); g.add(dish); SV.dish = dish;
  const dw = new THREE.Mesh(new THREE.CylinderGeometry(0.062, 0.056, 0.03, 28, 1, true), new THREE.MeshStandardMaterial({ color:srgb(0xd4d8dc), roughness:0.35, metalness:0.6, side:THREE.DoubleSide })); dw.position.y = 0.015; dish.add(dw);
  const db = new THREE.Mesh(new THREE.CylinderGeometry(0.056, 0.056, 0.003, 28), alu); db.position.y = 0.0015; dish.add(db);
  SV.dishSand = new THREE.Mesh(new THREE.CylinderGeometry(0.054, 0.054, 0.014, 28), sand); SV.dishSand.position.y = 0.01; dish.add(SV.dishSand);
  /* The sample: a tray of dry sand */
  const tray = new THREE.Group(); g.add(tray); SV.tray = tray;
  addBox(0.22, 0.03, 0.28, alu, 0, 0.015, 0, 0, tray);
  SV.sandTop = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.014, 0.26), sand); SV.sandTop.position.y = 0.03; tray.add(SV.sandTop);
  /* Riffle splitter with two receiving pans */
  const rz = -7.6, splitter = new THREE.Group(); splitter.position.set(SV.x, SV.y, rz); g.add(splitter);
  addBox(0.26, 0.16, 0.3, steel, 0, 0.08, 0, 0, splitter);
  for (let i = 0; i < 10; i++){ const ch = addBox(0.24, 0.04, 0.012, i % 2 ? steel : dark, 0, 0.18, -0.135 + i * 0.03, 0, splitter); ch.rotation.x = i % 2 ? 0.35 : -0.35; }
  SV.rp = [-1, 1].map((s) => { const pan = new THREE.Group(); pan.position.set(SV.x, SV.y, rz + s * 0.25); g.add(pan); addBox(0.22, 0.04, 0.12, alu, 0, 0.02, 0, 0, pan); const pile = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.012, 0.1), sand); pile.position.set(0, 0.046, 0); pan.add(pile); pan.userData.pile = pile; return pan; });
  /* Drying oven: a shell you can see into, with a door hinged on the far side */
  const oz = -6.62, oven = labMat(0xd9dde1, 0.5), inner = labMat(0x3a3f43, 0.8);
  addBox(0.52, 0.03, 0.5, oven, SV.x, SV.y + 0.015, oz, 0, g); addBox(0.52, 0.03, 0.5, oven, SV.x, SV.y + 0.465, oz, 0, g);
  for (const s of [-1, 1]) addBox(0.52, 0.48, 0.03, oven, SV.x, SV.y + 0.24, oz + s * 0.235, 0, g);
  addBox(0.03, 0.48, 0.5, oven, SV.x + 0.245, SV.y + 0.24, oz, 0, g);
  addBox(0.44, 0.4, 0.42, inner, SV.x + 0.03, SV.y + 0.24, oz, 0, g);
  addBox(0.4, 0.004, 0.38, steel, SV.x + 0.03, SV.y + 0.05, oz, 0, g);
  for (const zz of [-0.12, 0, 0.12]) addBox(0.4, 0.006, 0.006, dark, SV.x + 0.03, SV.y + 0.054, oz + zz, 0, g);
  const od = makeDisplay(0.11, 0.035, 256, 80, '#ff9d4d'); od.m.position.set(SV.x - 0.262, SV.y + 0.43, oz + 0.14); od.m.rotation.y = -Math.PI / 2; g.add(od.m); od.set('110°C'); SV.oven = od;
  SV.door = new THREE.Group(); SV.door.position.set(SV.x - 0.262, SV.y + 0.22, oz + 0.2); g.add(SV.door);
  addBox(0.02, 0.36, 0.4, labMat(0xc5cace, 0.5), 0, 0, -0.2, 0, SV.door);
  addPlane(0.26, 0.14, new THREE.MeshStandardMaterial({ color:0x2a1f12, emissive:srgb(0xff7a2a), emissiveIntensity:0.35, roughness:0.3 }), -0.011, 0.04, -0.2, -Math.PI / 2, SV.door);
  addCyl(0.009, 0.009, 0.14, steel, -0.034, 0, -0.355, 10, SV.door); for (const y of [-0.06, 0.06]) addBox(0.03, 0.012, 0.012, steel, -0.02, y, -0.355, 0, SV.door);
  /* What you can click when you're at the bench */
  const act = (w, h, d, x, y, z, id) => pickBox(w, h, d, x, y, z, { station:'sieve', act:id });
  act(0.3, 0.1, 0.34, 33.6, 0.95, -8.1, 'split'); act(0.3, 0.3, 0.4, SV.x, SV.y + 0.15, rz, 'split');
  act(0.56, 0.52, 0.56, SV.x, SV.y + 0.26, oz, 'dry');
  act(0.12, 0.05, 0.1, SV.x - 0.12, SV.y + 0.1, bz - 0.13, 'tare'); act(0.4, 0.2, 0.44, SV.x, SV.y + 0.12, bz, 'weigh');
  act(0.24, 0.24, 0.24, SV.home.pileA[0], 1.0, SV.home.pileA[2], 'stack'); act(0.24, 0.24, 0.24, SV.home.pileB[0], 1.0, SV.home.pileB[2], 'stack');
  act(0.3, 0.5, 0.3, SV.x, SV.y + 0.55, SV.z, 'stackOrWeigh'); act(0.24, 0.1, 0.24, SV.home.cover[0], 0.95, SV.home.cover[2], 'cover');
  act(0.08, 0.1, 0.12, SV.x - 0.232, SV.y + 0.1, SV.z + 0.13, 'shake');
  pickBox(0.75, 1.1, 5.0, SV.x - 0.05, SV.y + 0.5, -9.0, { station:'sieve' });
  addPlane(0.62, 0.14, basicMat(drawTableCard('SIEVE ANALYSIS', 'Particle size distribution (PSD)')), SV.x - 0.42, SV.y - 0.12, SV.z, -Math.PI / 2);
  sieveReset();
}
const psd = { step:0, sample:null, tared:false, weighed:false, stacked:0, shaken:false, weighedN:0, splitting:0, dried:false, covered:false, clamped:false, poured:false };
function psdNew(){
  const r = Math.random, d50 = 235 + r() * 75, sg = 0.3 + r() * 0.14, mass = +(98 + r() * 6).toFixed(2);
  const fin = (d) => d <= 0 ? 0 : 0.5 * (1 + erf(Math.log(d / d50) / (sg * Math.SQRT2)));
  let prev = 1; const frac = SIEVES.map(([, um]) => { const f = um ? fin(um) : 0, v = Math.max(0, prev - f); prev = f; return v; });
  const lossPct = r() < 0.18 ? 0.32 + r() * 0.24 : 0.04 + r() * 0.22, keep = 1 - lossPct / 100;
  const grams = frac.map((f) => { const g = f * mass * keep; return g < 0.006 ? 0 : Math.max(0, +(g + (r() - 0.5) * 0.02).toFixed(2)); });
  return { mass, grams };
}
function psdCalc(P){
  const pct = P.grams.map((g) => g / P.mass * 100);
  let cum = 0; const rows = SIEVES.map(([name, um, mult], i) => { cum += pct[i]; return { name, um, mult, g:P.grams[i], pct:pct[i], cum, pass:Math.max(0, 100 - cum) }; });
  const total = P.grams.reduce((a, b) => a + b, 0), loss = P.mass - total, sumPct = pct.reduce((a, b) => a + b, 0);
  const gfn = pct.reduce((s, p, i) => s + p * SIEVES[i][2], 0) / sumPct;
  const pts = rows.filter((r) => r.um > 0).map((r) => [r.um, r.pass]).reverse();
  const D = (p) => { for (let i = 0; i < pts.length - 1; i++){ const [a, pa] = pts[i], [b, pb] = pts[i + 1]; if ((pa - p) * (pb - p) <= 0 && pa !== pb){ const t = (p - pa) / (pb - pa); return Math.exp(Math.log(a) + t * (Math.log(b) - Math.log(a))); } } return null; };
  return { rows, total, loss, lossPct:loss / P.mass * 100, gfn, d10:D(10), d50:D(50), d60:D(60), d90:D(90) };
}
/* Sand levels */
function svSand(){
  const f = SV.frac; SV.sandTop.visible = f > 0.01; SV.sandTop.scale.y = Math.max(0.05, f); SV.sandTop.position.y = 0.023 + 0.007 * SV.sandTop.scale.y;
  SV.dishSand.visible = SV.dishF > 0.01; SV.dishSand.scale.y = Math.max(0.05, SV.dishF); SV.dishSand.position.y = 0.003 + 0.007 * SV.dishSand.scale.y;
  SV.rp.forEach((pan, i) => { const p = pan.userData.pile, v = SV.pans[i]; p.visible = v > 0.01; p.scale.y = Math.max(0.05, v); p.position.y = 0.04 + 0.006 * p.scale.y; });
  wake();
}
const svPut = (o, p, r) => { SV.g.attach(o); o.position.fromArray(p); o.rotation.set((r ? r[0] : 0) * D2R, (r ? r[1] : 0) * D2R, (r ? r[2] : 0) * D2R); };
/* Everything back where it starts: sieves in two piles, the cover and dish on the bench, sand in the tray */
function sieveReset(){
  handsFinish();
  const H = SV.home;
  SV.sieves.forEach((s) => { const k = s.i >= 6 ? s.i - 6 : s.i, pile = s.i >= 6 ? H.pileA : H.pileB; svPut(s.g, [pile[0], pile[1] + 0.014 + k * 0.028, pile[2]]); s.g.userData.held.visible = false; });
  svPut(SV.cover, [H.cover[0], H.cover[1] + 0.007, H.cover[2]]);
  svPut(SV.dish, H.dish); svPut(SV.tray, H.tray);
  SV.clamp.position.set(SV.x, SV.y + 0.82, SV.z); SV.door.rotation.y = 0;
  SV.stack.position.set(SV.x, SV.y + 0.3, SV.z); SV.arm.rotation.z = 0;
  SV.frac = 1; SV.dishF = 0; SV.pans = [0, 0]; svSand();
  SV.bal.set('0.00 g'); SV.disp.set('10:00', 'TIMER'); SV.oven.set('110°C');
}
const SV_PRESS = { L:null };
/* The clips: your hands doing each part of the test */
function svClip(spot){ const C = hClip(SV.spots[spot]()); C.focus = null; return C; }
function svPour(C, obj, from, over, y0, d, onFrac, extra){
  /* Lift a container, tip it over something, let the sand run out, bring it back */
  hMove(C, obj, { parent:SV.g, p:over, r:[0, 0, -42] }, 0.9, { lift:0.1 });
  const lip = extra && extra.lip ? extra.lip : [0.105, 0.03, 0];
  hStream(C, (t, v) => v.fromArray(lip).applyMatrix4(obj.matrixWorld), y0, d, Object.assign({ rate:170, spread:0.015, sz:extra && extra.sz != null ? extra.sz : 8, vx:0.08, keep:true }, extra && extra.stream));
  hAnim(C, d, onFrac);
  hWait(C, d);
  hMove(C, obj, { parent:SV.g, p:from, r:[0, 0, 0] }, 0.9, { lift:0.08 });
  return C;
}
function svSplit(){
  const C = svClip('splitter'), H = SV.home, f0 = SV.frac;
  hGrab(C, SV.tray, SV_G.tray, 0.8);
  svPour(C, SV.tray, H.tray, [33.47, 1.2, -7.6], 1.08, 1.7, (u) => { SV.frac = f0 * (1 - u); SV.pans[0] = SV.pans[1] = f0 * u * 0.5; svSand(); }, { sz:12, stream:{ rate:220 } });
  hRest(C, ['L', 'R'], 0.5);
  /* Keep one half: pour the near pan back into the tray */
  hGrab(C, SV.rp[0], SV_G.pan, 0.7);
  svPour(C, SV.rp[0], [SV.x, SV.y, -7.85], [33.5, 1.12, -8.06], 0.93, 1.2, (u) => { SV.pans[0] = f0 * 0.5 * (1 - u); SV.frac = f0 * 0.5 * u; svSand(); }, { lip:[0.105, 0.04, 0], sz:6 });
  hRest(C, ['L', 'R'], 0.6);
  hAt(C, () => { psd.splitting++; SV.pans[1] = 0; svSand(); });
  handsPlay(C, () => { if (STN.id === 'sieve') stRender(); });
}
function svDry(){
  const C = svClip('splitter'), H = SV.home;
  hGrab(C, SV.tray, SV_G.tray, 0.8);
  hMove(C, SV.tray, svCarry(), 0.6, { lift:0.06 });
  hWalk(C, SV.spots.oven());
  hWait(C, 0.3);
  hMove(C, SV.tray, { parent:SV.g, p:H.trayOven }, 0.8, { lift:0.06 });
  hRest(C, ['L', 'R'], 0.5);
  const door = (open, d) => { hGrab(C, SV.door, SV_G.handle, 0.6); hAnim(C, d, (u) => { SV.door.rotation.y = (open ? hsm(u) : 1 - hsm(u)) * 1.75; }); hWait(C, d); hRest(C, ['R'], 0.45); };
  door(true, 0.7);
  hGrab(C, SV.tray, SV_G.tray, 0.6);
  hMove(C, SV.tray, { parent:SV.g, p:H.ovenIn }, 0.9, { lift:0.08 });
  hRest(C, ['L', 'R'], 0.5);
  door(false, 0.6);
  hAt(C, () => SV.oven.set('DRYING', '110°C'));
  hWait(C, 1.8);
  hAt(C, () => SV.oven.set('DRY', 'COOL IT'));
  door(true, 0.7);
  hGrab(C, SV.tray, SV_G.tray, 0.7);
  hMove(C, SV.tray, { parent:SV.g, p:H.trayOven }, 0.9, { lift:0.08 });
  hRest(C, ['L', 'R'], 0.4);
  door(false, 0.6);
  hAt(C, () => SV.oven.set('110°C'));
  hGrab(C, SV.tray, SV_G.tray, 0.6);
  hMove(C, SV.tray, svCarry(), 0.6, { lift:0.06 });
  hWalk(C, SV.spots.balance());
  hWait(C, 0.3);
  hMove(C, SV.tray, { parent:SV.g, p:H.trayBal }, 0.8, { lift:0.06 });
  hRest(C, ['L', 'R'], 0.5);
  hAt(C, () => { psd.dried = true; });
  handsPlay(C, () => { if (STN.id === 'sieve') stRender(); });
}
function svPress(C, btn, grip, after){
  hTo(C, 'R', { o:btn, g:grip.R }, 0.6, { arc:0.06 });
  hTo(C, 'R', { o:btn, g:grip.R, off:() => grip === SV_G.pressD ? [0, -0.006, 0] : [0.006, 0, 0] }, 0.14);
  if (after) hAt(C, after);
  hTo(C, 'R', { o:btn, g:grip.R }, 0.16);
  hRest(C, ['R'], 0.5);
}
function svTare(){
  const C = svClip('balance');
  svPress(C, SV.btnTare, SV_G.pressD, () => { psd.tared = true; SV.bal.set('0.00 g', 'TARE'); });
  handsPlay(C, () => { if (STN.id === 'sieve') stRender(); });
}
function svWeigh(){
  const C = svClip('balance'), H = SV.home, S = psd.sample, f0 = SV.frac;
  hGrab(C, SV.tray, SV_G.tray, 0.8);
  svPour(C, SV.tray, H.trayBal, [33.49, 1.11, -10.75], 1.0, 1.8, (u) => { SV.frac = f0 * (1 - u); SV.dishF = u; SV.bal.set((S.mass * hsm(u)).toFixed(2) + ' g', u < 1 ? '' : 'STABLE'); svSand(); }, { sz:3, stream:{ rate:200 } });
  hRest(C, ['L', 'R'], 0.6);
  hAt(C, () => { psd.weighed = true; SV.bal.set(S.mass.toFixed(2) + ' g', 'STABLE'); });
  handsPlay(C, () => { if (STN.id === 'sieve') stRender(); });
}
function svStack(){
  const C = svClip('shaker'), n = SIEVES.length;
  for (let k = psd.stacked; k < n; k++){
    const s = SV.sieves[n - 1 - k];
    hGrab(C, s.g, SV_G.sieve, k === psd.stacked ? 0.7 : 0.55);
    hMove(C, s.g, { parent:SV.stack, p:[0, 0.014 + k * 0.028, 0] }, 0.65, { lift:0.12 });
    hAt(C, () => { psd.stacked = k + 1; if (STN.id === 'sieve'){ STN.cur.keepScroll = true; stRender(); } });
    hWait(C, 0.08);
  }
  hRest(C, ['L', 'R'], 0.5);
  handsPlay(C, () => { if (STN.id === 'sieve') stRender(); });
}
function svPourIn(){
  const C = svClip('balance'), H = SV.home, top = 0.014 + (SIEVES.length - 1) * 0.028;
  hGrab(C, SV.dish, SV_G.dish, 0.8);
  hMove(C, SV.dish, svCarry(-0.1), 0.6, { lift:0.06 });
  hWalk(C, SV.spots.shaker());
  hWait(C, 0.3);
  svPour(C, SV.dish, H.dishPark, [33.53, SV.y + 0.3 + top + 0.1, -9.0], SV.y + 0.3 + top + 0.014, 1.5, (u) => { SV.dishF = 1 - u; SV.sieves[0].g.userData.held.visible = u > 0.05; SV.sieves[0].g.userData.held.scale.setScalar(Math.max(0.05, u)); svSand(); }, { lip:[0.058, 0.028, 0], sz:3, stream:{ rate:180 } });
  hRest(C, ['L', 'R'], 0.5);
  hAt(C, () => { psd.poured = true; });
  handsPlay(C, () => { if (STN.id === 'sieve') stRender(); });
}
function svCover(){
  const C = svClip('shaker'), top = 0.014 + SIEVES.length * 0.028 + 0.002;
  hGrab(C, SV.cover, SV_G.cover, 0.7);
  hMove(C, SV.cover, { parent:SV.stack, p:[0, top, 0] }, 0.8, { lift:0.14 });
  hRest(C, ['L', 'R'], 0.4);
  hGrab(C, SV.clamp, SV_G.clamp, 0.7);
  hMove(C, SV.clamp, { parent:SV.g, p:[SV.x, SV.y + 0.3 + top + 0.03, SV.z] }, 0.7);
  hRest(C, ['L', 'R'], 0.5);
  hAt(C, () => { psd.covered = true; psd.clamped = true; });
  handsPlay(C, () => { if (STN.id === 'sieve') stRender(); });
}
function svShake(){
  const C = svClip('shaker');
  svPress(C, SV.btnStart, SV_G.pressF, () => { SV.run = 1; SV.shakeT = 0; if (STN.id === 'sieve') stRender(); });
  handsPlay(C, () => { if (STN.id === 'sieve') stRender(); });
}
function svUncover(C){
  const top = 0.014 + SIEVES.length * 0.028 + 0.002;
  hGrab(C, SV.clamp, SV_G.clamp, 0.7);
  hMove(C, SV.clamp, { parent:SV.g, p:[SV.x, SV.y + 0.82, SV.z] }, 0.7);
  hRest(C, ['L', 'R'], 0.3);
  hGrab(C, SV.cover, SV_G.cover, 0.6);
  hMove(C, SV.cover, { parent:SV.g, p:[SV.home.cover[0], SV.home.cover[1] + 0.007, SV.home.cover[2]] }, 0.8, { lift:0.14 });
  hRest(C, ['L', 'R'], 0.4);
  hAt(C, () => { psd.covered = false; psd.clamped = false; });
}
function svWeighSieves(count, rate){
  const C = svClip('shaker'), H = SV.home, n = SIEVES.length;
  if (psd.covered) svUncover(C);
  const end = Math.min(n, psd.weighedN + count);
  for (let i = psd.weighedN; i < end; i++){
    const s = SV.sieves[i], done = i;
    hGrab(C, s.g, SV_G.sieve, 0.6);
    hMove(C, s.g, svCarry(-0.1), 0.55, { lift:0.1 });
    hWalk(C, SV.spots.balance());
    hWait(C, 0.25);
    hMove(C, s.g, { parent:SV.g, p:[SV.balX, SV.balTop + 0.014, SV.balZ] }, 0.65, { lift:0.06 });
    hRest(C, ['L', 'R'], 0.4);
    hAt(C, () => { SV.bal.set(psd.sample.grams[i].toFixed(2) + ' g', 'NET'); psd.weighedN = i + 1; if (STN.id === 'sieve'){ STN.cur.keepScroll = true; stRender(); } });
    hWait(C, 0.55);
    hGrab(C, s.g, SV_G.sieve, 0.5);
    hMove(C, s.g, { parent:SV.g, p:[H.done[0], H.done[1] + 0.014 + done * 0.028, H.done[2]] }, 0.65, { lift:0.1 });
    hRest(C, ['L', 'R'], 0.3);
    if (i + 1 < end){ hWalk(C, SV.spots.shaker()); hWait(C, 0.25); }
  }
  C.rate = rate || 1;
  handsPlay(C, () => { if (STN.id === 'sieve') stRender(); });
}
STATIONS.sieve = {
  id:'sieve', room:'lab', kick:'Room 102 · Science Lab', hands:true,
  title(){ return ['Sieve analysis (PSD)', 'Split the sample', 'Dry and weigh', 'Stack the sieves', 'Shake', 'Weigh each sieve', 'Results'][psd.step]; },
  stepText(){ return psd.step > 0 && psd.step < 6 ? 'Step ' + psd.step + ' of 5' : ''; },
  spot(){ return SV.spots[psd.step === 1 ? 'splitter' : psd.step === 2 ? (psd.dried ? 'balance' : 'oven') : psd.step === 4 ? (psd.poured ? 'shaker' : 'balance') : psd.step === 5 ? (psd.weighedN ? 'balance' : 'shaker') : 'shaker'](); },
  view(){ const s = this.spot(); return psd.step === 0 ? { x:32.1, z:-9.0, yaw:-Math.PI / 2, pitch:-0.28 } : { x:s.x, z:s.z, yaw:s.yaw, pitch:s.pitch }; },
  enter(){ if (!psd.sample) psd.sample = psdNew(); },
  leave(){ handsFinish(); },
  /* Clicking the equipment does the same as the panel's button for that step */
  act(id){
    const A = this.actions();
    const hit = A.find((a) => a.ids.includes(id) && !a.disabled);
    if (hit) hit.fn(); else if (A.length && A[0].hint) toast(A[0].hint);
  },
  actLabel(id){ const A = this.actions(); const a = A.find((x) => x.ids.includes(id) && !x.disabled); return a ? a.label : ''; },
  actions(){
    const busy = handsBusy(), S = psd.sample;
    if (psd.step === 1) return [{ ids:['split'], label:psd.splitting ? 'Split it again' : 'Pour it through the splitter', fn:svSplit, disabled:busy || psd.splitting >= 2, hint:'Pour the sand through the riffle splitter.' }];
    if (psd.step === 2){
      if (!psd.dried) return [{ ids:['dry', 'split', 'weigh', 'tare'], label:'Dry it in the oven', fn:svDry, disabled:busy, hint:'Dry the sample in the oven first.' }];
      return [{ ids:['tare'], label:'Tare the balance', fn:svTare, disabled:busy || psd.tared, hint:'Press TARE on the balance.' }, { ids:['weigh', 'split'], label:'Pour the sample into the dish', fn:svWeigh, disabled:busy || !psd.tared || psd.weighed, hint:psd.tared ? 'Pour the sand into the dish on the balance.' : 'Tare the balance first.' }];
    }
    if (psd.step === 3) return [{ ids:['stack', 'stackOrWeigh'], label:'Stack the sieves', fn:svStack, disabled:busy || psd.stacked >= SIEVES.length, hint:'Stack the sieves on the shaker, the pan first.' }];
    if (psd.step === 4){
      if (!psd.poured) return [{ ids:['weigh', 'stackOrWeigh', 'cover', 'shake'], label:'Pour the sample onto the top sieve', fn:svPourIn, disabled:busy, hint:'Bring the sample over and pour it onto the top sieve.' }];
      if (!psd.covered) return [{ ids:['cover', 'stackOrWeigh', 'shake'], label:'Put the cover on and clamp it', fn:svCover, disabled:busy, hint:'Put the cover on first.' }];
      return [{ ids:['shake', 'stackOrWeigh'], label:SV.run ? 'Shaking…' : psd.shaken ? 'Shake again' : 'Press START', fn:svShake, disabled:busy || !!SV.run, hint:'Press START on the shaker.' }];
    }
    if (psd.step === 5){
      const done = psd.weighedN >= SIEVES.length;
      return [{ ids:['stackOrWeigh', 'weigh'], label:'Weigh the next sieve', fn:() => svWeighSieves(1, 1), disabled:busy || done, hint:'Lift the top sieve onto the balance.' }, { ids:['tare'], label:'Weigh the rest', fn:() => svWeighSieves(SIEVES.length, 3), disabled:busy || done || psd.weighedN < 1, hint:'' }];
    }
    return [];
  },
  render(body, btns){
    const S = psd.sample, busy = handsBusy();
    const next = (lab, en) => btns.appendChild(stBtn(lab, () => { handsFinish(); psd.step++; stRender(); goView(STATIONS.sieve.view()); }, true, en === false || busy));
    const acts = () => { this.actions().forEach((a, i) => btns.appendChild(stBtn(a.label, a.fn, i === 0 && !a.disabled, a.disabled))); if (busy) btns.appendChild(stBtn('Skip ahead', () => { handsFinish(); stRender(); })); };
    if (psd.step === 0){
      body.appendChild(stEl('p', 'stp', 'A sieve analysis measures how big the grains in a sample are. Labs report it as the particle size distribution, or PSD. Sand plants, concrete labs and foundries rely on this test to check their materials.'));
      body.appendChild(stEl('p', 'stp', 'You’ll do it with your own hands: split a sample, dry and weigh it, stack the sieves, shake them, weigh what each sieve caught and turn the numbers into a curve. Use the buttons here, or ' + (COARSE ? 'tap' : 'click') + ' the equipment itself.'));
      body.appendChild(stSteps(['Split the sample', 'Dry and weigh', 'Stack the sieves', 'Shake', 'Weigh each sieve'], -1));
      next('Start the test');
    } else if (psd.step === 1){
      body.appendChild(stEl('p', 'stp', 'A pile of sand isn’t the same all the way through: big grains and fine grains separate. Pour it through the riffle splitter, which divides it into two matching halves, keep one half, and split again until you have about 100 grams.'));
      const why = stEl('p', 'stwhy'); why.appendChild(stEl('b', null, 'Why: ')); why.appendChild(document.createTextNode('a fair split makes your small sample represent the whole pile.')); body.appendChild(why);
      body.appendChild(stKV([['In the tray', Math.round(400 * SV.frac) + ' g' + (psd.splitting >= 2 ? ', about right' : psd.splitting === 1 ? ', still too much' : ''), psd.splitting >= 2 ? 'hi' : null]]));
      if (psd.splitting >= 2) body.appendChild(stEl('p', 'stresult', 'Done. Two splits took the pile down to one representative portion of about 100 grams.'));
      acts();
      next('Next: dry and weigh', psd.splitting >= 2);
    } else if (psd.step === 2){
      body.appendChild(stEl('p', 'stp', 'Dry the sample in the oven at about 110 °C until its mass stops changing, and let it cool. Then press TARE with the empty dish on the balance, so the reading only counts the sand, and pour the sample in.'));
      body.appendChild(stKV([['Oven', psd.dried ? 'dried and cooled' : 'not yet'], ['Balance', psd.weighed ? S.mass.toFixed(2) + ' g' : psd.tared ? '0.00 g (tared)' : 'not tared yet'], ['Starting dry mass', psd.weighed ? S.mass.toFixed(2) + ' g' : '—', psd.weighed ? 'hi' : null]]));
      acts();
      next('Next: stack the sieves', psd.weighed);
    } else if (psd.step === 3){
      body.appendChild(stEl('p', 'stp', 'Nest the sieves with the biggest openings on top and the finest at the bottom, with a pan underneath to catch the dust. Sieves are named by their US mesh number, roughly the number of openings per inch.'));
      body.appendChild(stTable(['Mesh', 'Opening'], SIEVES.map(([n, um], i) => ({ cells:[n === 'Pan' ? 'Pan' : '#' + n, um ? (um >= 1000 ? (um / 1000).toFixed(2) + ' mm' : um + ' µm') : 'catches the rest'], cls:SIEVES.length - 1 - i < psd.stacked ? 'hi' : null })), 'compact'));
      acts();
      next('Next: shake', psd.stacked >= SIEVES.length);
    } else if (psd.step === 4){
      body.appendChild(stEl('p', 'stp', 'Pour the sample onto the top sieve, put the cover on, clamp the stack and press START. The shaker swirls and taps the stack so every grain gets its chance to fall through. Labs often shake for 10 to 15 minutes; this run is sped up.'));
      if (psd.shaken && !SV.run) body.appendChild(stEl('p', 'stresult', 'Shaking finished. The grains have settled onto the sieves that were too fine for them to pass.'));
      acts();
      next('Next: weigh each sieve', psd.shaken && !SV.run);
    } else if (psd.step === 5){
      body.appendChild(stEl('p', 'stp', 'Lift the sieves off one at a time, from the top, and weigh what stayed on each. The balance is tared for each empty sieve, so it reads the retained mass.'));
      body.appendChild(stTable(['Sieve', 'Opening', 'Retained'], SIEVES.map(([n, um], i) => ({ cells:[n === 'Pan' ? 'Pan' : '#' + n, um ? um + ' µm' : '—', i < psd.weighedN ? S.grams[i].toFixed(2) + ' g' : '…'], cls:i === psd.weighedN - 1 ? 'hi' : null })), 'compact'));
      acts();
      next('See the results', psd.weighedN >= SIEVES.length);
    } else {
      const C = psdCalc(S), ok = C.lossPct <= 0.3;
      award('scientist');
      body.appendChild(stKV([['Starting dry mass', S.mass.toFixed(2) + ' g'], ['Total retained', C.total.toFixed(2) + ' g'], ['Loss', C.loss.toFixed(2) + ' g (' + C.lossPct.toFixed(2) + '%)', ok ? 'ok' : 'warn']]));
      body.appendChild(stEl('p', ok ? 'stresult' : 'stwarn', ok ? 'The loss is under 0.3%, the limit ASTM C136 uses for sieve tests, so this run is good.' : 'The loss is over 0.3%, the limit ASTM C136 uses for sieve tests, so this run shouldn’t be used. Check for spilled sand or grains stuck in the mesh, then run it again.'));
      const c = stCanvas(640, 330); body.appendChild(c);
      const curve = C.rows.filter((r) => r.um > 0).map((r) => [r.um, r.pass]).reverse();
      const bars = C.rows.filter((r) => r.um > 0 && r.um < 1700).map((r, i, a) => { const up = SIEVES[SIEVES.findIndex((s) => s[1] === r.um) - 1]; return [r.um, Math.min(1000, up ? up[1] : 1000), r.pct]; });
      drawChart(c, { logx:true, x0:45, x1:1000, y0:0, y1:100, yt:[0, 20, 40, 60, 80, 100], yf:(v) => v + '%', xt:[[53, '270'], [75, '200'], [106, '140'], [150, '100'], [212, '70'], [300, '50'], [425, '40'], [600, '30'], [850, '20']], xl:'US sieve mesh (opening gets bigger →)', yl:'% passing',
        series:[{ bars, color:'rgba(205,169,97,0.28)' }, { pts:curve, color:'#5ee6c8', dots:true }, C.d50 ? { vline:C.d50, color:'#ffd166', label:'D50 ' + Math.round(C.d50) + ' µm' } : null].filter(Boolean) });
      body.appendChild(stEl('p', 'stnote', 'Teal line: % passing each sieve. Gold bars: % retained on each sieve.'));
      const r = (v) => v ? Math.round(v) + ' µm' : 'off the chart';
      body.appendChild(stKV([['D10', r(C.d10)], ['D50 (median grain)', r(C.d50)], ['D90', r(C.d90)], ['Uniformity, D60 ÷ D10', C.d10 && C.d60 ? (C.d60 / C.d10).toFixed(2) : '—'], ['AFS grain fineness number', C.gfn.toFixed(1), 'hi']]));
      body.appendChild(stEl('p', 'stp', 'The AFS grain fineness number sums each sieve’s % retained times a multiplier, then divides by the total. A bigger number means finer sand. Plants compare it, and the whole curve, against each customer’s spec.'));
      body.appendChild(stTable(['Sieve', 'g', '% ret.', 'Cum. %', '% pass'], C.rows.map((x) => [x.name === 'Pan' ? 'Pan' : '#' + x.name, x.g.toFixed(2), x.pct.toFixed(1), x.cum.toFixed(1), x.name === 'Pan' ? '—' : x.pass.toFixed(1)]), 'compact num'));
      btns.appendChild(stBtn('Run a new sample', () => { Object.assign(psd, { step:1, sample:psdNew(), tared:false, weighed:false, stacked:0, shaken:false, weighedN:0, splitting:0, dried:false, covered:false, clamped:false, poured:false }); sieveReset(); stRender(); goView(STATIONS.sieve.view()); }, true));
      btns.appendChild(stBtn('Done', closeStation));
    }
  },
  tick(dt){
    let a = false;
    if (SV.run){
      a = true; SV.shakeT += dt;
      const dur = REDUCED ? 0.2 : 6, k = Math.min(1, SV.shakeT / dur), left = Math.max(0, 600 * (1 - k));
      SV.disp.set(Math.floor(left / 60) + ':' + String(Math.floor(left % 60)).padStart(2, '0'), 'RUNNING');
      const t = SV.shakeT, orb = REDUCED ? 0 : 0.006;
      SV.stack.position.x = SV.x + Math.cos(t * 29) * orb; SV.stack.position.z = SV.z + Math.sin(t * 29) * orb;
      const tap = Math.max(0, Math.sin(t * 15.7)); SV.arm.rotation.z = -tap * 0.12; SV.stack.position.y = SV.y + 0.3 + (tap > 0.95 ? -0.002 : 0);
      /* The sand works its way down: the top sieve's pile shrinks and every sieve keeps its share */
      const held0 = SV.sieves[0].g.userData.held; held0.scale.setScalar(Math.max(0.05, 1 - 0.75 * k));
      if (k >= 1){ SV.run = 0; psd.shaken = true; SV.stack.position.set(SV.x, SV.y + 0.3, SV.z); SV.arm.rotation.z = 0; SV.disp.set('0:00', 'DONE'); const mx = Math.max(...psd.sample.grams, 1); SV.sieves.forEach((s) => { const h = s.g.userData.held; h.visible = true; h.scale.setScalar(Math.max(0.12, Math.sqrt(psd.sample.grams[s.i] / mx))); }); if (STN.id === 'sieve') stRender(); }
    }
    return a;
  }
};
/* ---------- 2. Acid–base titration ---------- */
const TT = { x:31.0, z:-12.6, y:0.9, liquid:null, flaskLiq:null, liqMat:null, drop:null, bar:null, dropT:-1, flask:null, cock:null, bottles:{}, stream:null, pourT:0 };
const ttSpot = () => ({ x:TT.x, z:-12.02 - (narrow() ? 0.05 : 0), yaw:0, pitch:-0.28 - (narrow() ? 0.1 : 0), bench:0.9 });
const TT_G = {
  flask:{ L:{ p:[-0.016, 0.135, 0], into:[1, 0, 0], fingers:[0, -0.4, 1], curl:0.75, out:0.6 } },
  cock:{ R:{ p:[0.04, 0, 0.006], into:[0, 0, -1], fingers:[0.35, -1, 0], curl:0.7, out:0.4 } },
  bottleR:{ R:{ p:[0.041, 0.02, 0], into:[-1, 0, 0], fingers:[0, -0.2, -1], curl:0.7 } },
  bottleL:{ L:{ p:[-0.041, 0.02, 0], into:[1, 0, 0], fingers:[0, -0.2, -1], curl:0.7 } }
};
function buildTitrationStation(M){
  const g = new THREE.Group(); g.userData.noMerge = true; scene.add(g); TT.g = g;
  const steel = labMat(0xb9c0c6, 0.3, 0.7), dark = labMat(0x2b2f33, 0.5);
  addBox(0.18, 0.06, 0.18, labMat(0xe9ecee, 0.5), TT.x, TT.y + 0.03, TT.z, 0, g);
  addCyl(0.012, 0.012, 0.012, dark, TT.x + 0.05, TT.y + 0.03, TT.z + 0.092, 12, g).rotation.x = Math.PI / 2;
  addBox(0.17, 0.015, 0.26, dark, TT.x, TT.y + 0.0075, TT.z - 0.08, 0, g);
  addCyl(0.006, 0.006, 0.86, steel, TT.x, TT.y + 0.43, TT.z - 0.16, 10, g);
  addBox(0.02, 0.02, 0.17, steel, TT.x, TT.y + 0.66, TT.z - 0.08, 0, g);
  addBox(0.04, 0.03, 0.03, dark, TT.x, TT.y + 0.66, TT.z, 0, g);
  /* Burette: glass tube, liquid column, a stopcock you turn, and the tip */
  const bx = TT.x, bz = TT.z, bTop = TT.y + 0.82, bBot = TT.y + 0.26;
  const tube = addCyl(0.0078, 0.0078, bTop - bBot, glassMat(0.3), bx, (bTop + bBot) / 2, bz, 16, g); tube.renderOrder = 2;
  TT.liqMat = new THREE.MeshStandardMaterial({ color:0xd8ecff, transparent:true, opacity:0.55, roughness:0.1, depthWrite:false });
  TT.liquid = new THREE.Mesh(new THREE.CylinderGeometry(0.0062, 0.0062, 1, 12), TT.liqMat); TT.liquid.position.set(bx, 0, bz); g.add(TT.liquid);
  TT.bTop = bTop; TT.bBot = bBot;
  TT.cock = new THREE.Group(); TT.cock.position.set(bx, bBot - 0.006, bz); g.add(TT.cock);
  addBox(0.016, 0.014, 0.014, labMat(0x2f6b9d, 0.4), 0, 0, 0, 0, TT.cock);
  addBox(0.05, 0.006, 0.006, labMat(0x2f6b9d, 0.4), 0.03, 0, 0, 0, TT.cock);
  const tip = new THREE.Mesh(new THREE.ConeGeometry(0.004, 0.035, 10), glassMat(0.5)); tip.rotation.x = Math.PI; tip.position.set(bx, bBot - 0.03, bz); g.add(tip);
  const scale = mk(64, 1024), sctx = scale.getContext('2d');
  sctx.fillStyle = '#ffffff'; sctx.textAlign = 'left'; sctx.font = '700 22px ' + F.type;
  for (let i = 0; i <= 50; i++){ const y = 40 + i * (944 / 50), major = i % 5 === 0; sctx.fillRect(0, y - 1, major ? 26 : 14, 2); if (major && i % 10 === 0) sctx.fillText(String(i), 30, y + 8); }
  const st = new THREE.Mesh(new THREE.PlaneGeometry(0.03, 0.564), new THREE.MeshBasicMaterial({ map:tex(scale), transparent:true, toneMapped:false, depthWrite:false }));
  st.position.set(bx + 0.0105, bTop - 0.3, bz + 0.0072); g.add(st);
  /* Erlenmeyer flask with the acid: one group, so it swirls as a whole in your hand */
  const fl = new THREE.Group(); fl.position.set(TT.x, TT.y + 0.06, TT.z); g.add(fl); TT.flask = fl;
  const prof = [[0.0, 0], [0.052, 0], [0.056, 0.006], [0.054, 0.02], [0.016, 0.115], [0.015, 0.15], [0.018, 0.155]].map(([r, y]) => new THREE.Vector2(r, y));
  const flask = new THREE.Mesh(new THREE.LatheGeometry(prof, 32), glassMat(0.28)); flask.renderOrder = 3; fl.add(flask);
  const lp = [[0, 0.003], [0.05, 0.003], [0.0525, 0.008], [0.0515, 0.022], [0.042, 0.046], [0, 0.046]].map(([r, y]) => new THREE.Vector2(r, y));
  TT.flaskMat = new THREE.MeshStandardMaterial({ color:0xeef6f8, transparent:true, opacity:0.34, roughness:0.1, depthWrite:false });
  TT.flaskLiq = new THREE.Mesh(new THREE.LatheGeometry(lp, 32), TT.flaskMat); TT.flaskLiq.renderOrder = 2; fl.add(TT.flaskLiq);
  TT.bar = addBox(0.024, 0.006, 0.007, labMat(0xffffff, 0.4), 0, 0.006, 0, 0, fl);
  TT.drop = new THREE.Mesh(new THREE.SphereGeometry(0.0035, 8, 6), TT.liqMat); TT.drop.visible = false; g.add(TT.drop);
  TT.stream = new THREE.Mesh(new THREE.CylinderGeometry(0.003, 0.0025, 1, 8), TT.liqMat); TT.stream.visible = false; g.add(TT.stream);
  /* Bottles of NaOH and the mystery acid */
  for (const [k, x, col, lab] of [['naoh', TT.x - 0.32, 0xe9e3d8, 'NaOH 0.1000 M'], ['hcl', TT.x + 0.3, 0xc4572f, 'HCl ?']]){
    const b = new THREE.Group(); b.position.set(x, TT.y, TT.z + 0.05); g.add(b); TT.bottles[k] = b; b.userData.home = [x, TT.y, TT.z + 0.05];
    addCyl(0.04, 0.04, 0.16, labMat(0xf2f2ee, 0.25, 0, { transparent:true, opacity:0.7 }), 0, 0.08, 0, 18, b);
    addCyl(0.022, 0.022, 0.03, labMat(col, 0.5), 0, 0.175, 0, 14, b);
    addPlane(0.07, 0.035, basicMat(drawTableCard(lab, ' ')), 0, 0.09, 0.0415, 0, b);
  }
  pickBox(0.9, 1.0, 0.6, TT.x, TT.y + 0.5, TT.z + 0.05, { station:'titration' });
  pickBox(0.12, 0.08, 0.1, bx, bBot, bz, { station:'titration', act:'drop' });
  pickBox(0.14, 0.2, 0.14, TT.x, TT.y + 0.14, TT.z, { station:'titration', act:'flask' });
  addPlane(0.62, 0.14, basicMat(drawTableCard('TITRATION', 'Find the mystery acid')), TT.x, TT.y - 0.12, TT.z + 0.43, 0);
  titrVisual();
}
const titr = { step:0, Ca:0.1, Vacid:25.0, Cb:0.1, v0:0.4, added:0, flash:0, ended:null, pts:[], fill:0 };
function titrNew(){ titr.Ca = +(0.08 + Math.random() * 0.04).toFixed(4); titr.v0 = +(0.1 + Math.random() * 0.9).toFixed(2); titr.added = 0; titr.flash = 0; titr.ended = null; titr.pts = [[0, titrPH(0)]]; titr.fill = 0; titr.set = false; }
function titrPH(vb){
  const a = titr.Ca * titr.Vacid / 1000, b = titr.Cb * vb / 1000, V = (titr.Vacid + vb) / 1000, d = (a - b) / V, Kw = 1e-14;
  return -Math.log10((d + Math.sqrt(d * d + 4 * Kw)) / 2);
}
function titrVeq(){ return titr.Ca * titr.Vacid / titr.Cb; }
function titrColor(){
  const ph = titrPH(titr.added), k = clamp((ph - 8.2) / 1.6, 0, 1), f = Math.max(k, titr.flash * 0.75);
  return f;
}
function titrVisual(){
  /* The burette holds its reading; before the setup it is empty and so is the flask */
  const fillB = titr.set ? 1 : Math.max(0, titr.fill - 1), fillF = titr.set ? 1 : Math.min(1, titr.fill);
  const reading = titr.v0 + titr.added, topFull = TT.bTop - 0.04 - reading * (TT.bTop - 0.04 - TT.bBot) / 50, bot = TT.bBot, top = bot + (topFull - bot) * fillB;
  TT.liquid.visible = fillB > 0.01; TT.liquid.scale.y = Math.max(0.001, top - bot); TT.liquid.position.y = (top + bot) / 2;
  const f = titrColor(), pink = new THREE.Color(0xff3d8b), clear = new THREE.Color(0xeef6f8);
  TT.flaskMat.color.copy(clear).lerp(pink, Math.min(1, f * 1.15)); TT.flaskMat.opacity = 0.34 + f * 0.38;
  TT.flaskLiq.visible = fillF > 0.02; TT.flaskLiq.scale.y = fillF * (1 + titr.added * 0.012);
  wake();
}
/* Hands: hold the flask by its neck between additions */
function titrIdle(){
  if (STN.id !== 'titration' || titr.step !== 2) return;
  const C = hClip(ttSpot()); C.T = 1e6;
  hGrab(C, TT.flask, TT_G.flask, 0.7, { arc:0.03 });
  handsPlay(C);
}
/* Add base: turn the stopcock, let it run while you swirl the flask, close it */
function titrAdd(v){
  if (titr.step !== 2 || handsBusy() && HANDS.clip && HANDS.clip.T < 1e5) return;
  const before = titr.added, veq = titrVeq();
  let vv = v; if (before + vv + titr.v0 > 50) vv = +(50 - titr.v0 - before).toFixed(2); if (vv <= 0) return;
  const d = v >= 1 ? 1.0 : v >= 0.1 ? 0.35 : 0.2, home = [TT.x, TT.y + 0.06, TT.z];
  const C = hClip(ttSpot());
  hGrab(C, TT.flask, TT_G.flask, 0.01, { keep:true });
  hTo(C, 'R', { o:TT.cock, g:TT_G.cock.R }, 0.45, { arc:0.03 });
  hAnim(C, 0.22, (u) => { TT.cock.rotation.z = -Math.PI / 2 * hsm(u); }); hWait(C, 0.22);
  let last = -1;
  hAnim(C, d, (u) => {
    titr.added = +(before + vv * u).toFixed(3);
    const n = Math.floor(u * d / 0.11); if (n !== last){ last = n; TT.dropT = 0; }
    const sw = Math.min(1, u * 3) * Math.min(1, (1 - u) * 3), a = u * d * 14;
    TT.flask.position.set(home[0] + Math.cos(a) * 0.011 * sw, home[1], home[2] + Math.sin(a) * 0.011 * sw);
    titrVisual();
  });
  hWait(C, d);
  hAnim(C, 0.22, (u) => { TT.cock.rotation.z = -Math.PI / 2 * (1 - hsm(u)); }); hWait(C, 0.22);
  hAt(C, () => {
    titr.added = +(before + vv).toFixed(2); TT.flask.position.fromArray(home);
    titr.pts.push([titr.added, titrPH(titr.added)]);
    if (titr.added < veq && veq - titr.added < 1.2) titr.flash = 1 - (veq - titr.added) / 1.6;
    titrVisual();
    if (before < veq && titr.added >= veq) titr.passed = true;
    if (STN.id === 'titration'){ STN.cur.keepScroll = true; stRender(); }
  });
  hRest(C, ['R'], 0.4);
  handsPlay(C, () => { titrIdle(); if (STN.id === 'titration'){ STN.cur.keepScroll = true; stRender(); } });
}
/* Set up: pour the acid into the flask, then fill the burette from the base bottle */
function titrSetup(){
  const C = hClip(ttSpot()), hcl = TT.bottles.hcl, naoh = TT.bottles.naoh;
  const pour = (b, side, grips, over, from, d, onU, streamTo) => {
    hGrab(C, b, grips, 0.7, { arc:0.04 });
    hMove(C, b, { parent:TT.g, p:over, r:[0, 0, side * 72] }, 0.8, { lift:0.1 });
    hAnim(C, d, (u) => { onU(u); const m = TT.stream, a = _hdv.set(0, 0.17, 0).applyMatrix4(b.matrixWorld); m.visible = u < 0.97 && u > 0.03; m.position.set((a.x + streamTo[0]) / 2, (a.y + streamTo[1]) / 2, (a.z + streamTo[2]) / 2); m.scale.y = Math.max(0.001, Math.hypot(a.x - streamTo[0], a.y - streamTo[1], a.z - streamTo[2])); m.lookAt(streamTo[0], streamTo[1], streamTo[2]); m.rotateX(Math.PI / 2); if (u >= 0.97) m.visible = false; });
    hWait(C, d);
    hMove(C, b, { parent:TT.g, p:from, r:[0, 0, 0] }, 0.8, { lift:0.1 });
    hRest(C, [side > 0 ? 'R' : 'L'], 0.4);
  };
  pour(hcl, 1, TT_G.bottleR, [TT.x + 0.17, TT.y + 0.27, TT.z], hcl.userData.home, 1.6, (u) => { titr.fill = Math.min(1, u); titrVisual(); }, [TT.x, TT.y + 0.21, TT.z]);
  pour(naoh, -1, TT_G.bottleL, [TT.x - 0.17, TT.bTop - 0.02, TT.z], naoh.userData.home, 1.8, (u) => { titr.fill = 1 + Math.min(1, u); titrVisual(); }, [TT.x, TT.bTop, TT.z]);
  hAt(C, () => { titr.set = true; titrVisual(); });
  handsPlay(C, () => { if (STN.id === 'titration') stRender(); });
}
function titrStatus(){
  const ph = titrPH(titr.added), over = titr.added - titrVeq();
  if (ph >= 8.2 && over > 0.3) return ['warn', 'Dark pink: you went past the endpoint. Your answer will come out a little high. Record it anyway, or start over.'];
  if (ph >= 8.2) return ['ok', 'Faint pink that stays: that’s the endpoint! Record it.'];
  if (titr.flash > 0.25) return ['hi', 'Pink flashes, then fades as it mixes. You’re close: slow down to single drops.'];
  return ['', 'Still colorless: the flask is still acidic.'];
}
STATIONS.titration = {
  id:'titration', room:'lab', kick:'Room 102 · Science Lab', hands:true,
  title(){ return ['Acid–base titration', 'Set up', 'Titrate', 'Results'][titr.step]; },
  stepText(){ return titr.step === 1 || titr.step === 2 ? 'Step ' + titr.step + ' of 2' : ''; },
  spot(){ return ttSpot(); },
  view(){ const s = ttSpot(); return titr.step === 0 ? { x:TT.x - 0.05, z:-11.3, yaw:0, pitch:-0.14 } : { x:s.x, z:s.z, yaw:s.yaw, pitch:s.pitch }; },
  enter(){ if (!titr.pts.length) titrNew(); titrVisual(); if (titr.step === 2) titrIdle(); },
  leave(){ handsFinish(); TT.flask.position.set(TT.x, TT.y + 0.06, TT.z); },
  act(id){
    if (titr.step === 1 && !titr.set && !handsBusy()){ titrSetup(); return; }
    if (titr.step === 2){ if (id === 'drop') titrAdd(0.05); else toast('Turn the stopcock to add base: a milliliter, a tenth, or one drop.'); return; }
    if (titr.step === 0) toast('Press Start to begin.');
  },
  actLabel(id){ if (titr.step === 2) return id === 'drop' ? 'Add one drop' : 'Swirl'; if (titr.step === 1 && !titr.set) return 'Set it up'; return ''; },
  render(body, btns){
    const busy = handsBusy() && HANDS.clip && HANDS.clip.T < 1e5;
    if (titr.step === 0){
      body.appendChild(stEl('p', 'stp', 'A titration finds how concentrated a solution is by reacting it with another solution whose concentration you already know. Here, sodium hydroxide (a base) neutralizes a mystery hydrochloric acid.'));
      body.appendChild(stEl('p', 'stp', 'Phenolphthalein, the indicator, stays colorless in acid and turns pink once the solution turns slightly basic, at about pH 8.2.'));
      body.appendChild(stEl('p', 'stwarn', 'In a real lab: goggles on. Both chemicals can burn skin and eyes.'));
      btns.appendChild(stBtn('Start', () => { titr.step = 1; stRender(); goView(this.view()); }, true));
    } else if (titr.step === 1){
      body.appendChild(stEl('p', 'stp', 'Pour exactly 25.00 mL of the mystery acid into the flask and add 2 drops of phenolphthalein. Fill the burette with 0.1000 M sodium hydroxide, then read the starting volume at the bottom of the curved liquid surface, the meniscus, with your eye level with it.'));
      body.appendChild(stKV([['Acid in the flask', titr.set ? '25.00 mL HCl (unknown)' : '—'], ['Base in the burette', titr.set ? '0.1000 M NaOH' : '—'], ['Starting reading', titr.set ? titr.v0.toFixed(2) + ' mL' : '—', titr.set ? 'hi' : null]]));
      btns.appendChild(stBtn('Set it up', titrSetup, !titr.set, !!titr.set || busy));
      if (busy) btns.appendChild(stBtn('Skip ahead', () => { handsFinish(); stRender(); }));
      btns.appendChild(stBtn('Next: titrate', () => { titr.step = 2; stRender(); titrIdle(); }, !!titr.set, !titr.set || busy));
    } else if (titr.step === 2){
      body.appendChild(stEl('p', 'stp', 'Hold the flask and swirl it as the base runs in. Add base fast at first. When pink flashes start to linger, slow down and finish one drop at a time. The endpoint is the first drop that keeps the whole flask faint pink for 30 seconds.'));
      const [cls, msg] = titrStatus();
      body.appendChild(stKV([['Burette reading', (titr.v0 + titr.added).toFixed(2) + ' mL'], ['NaOH added', titr.added.toFixed(2) + ' mL'], ['pH (probe)', titrPH(titr.added).toFixed(2)]]));
      body.appendChild(stEl('p', cls === 'warn' ? 'stwarn' : cls === 'ok' ? 'stresult' : cls === 'hi' ? 'sthint' : 'stnote', msg));
      const c = stCanvas(640, 280); body.appendChild(c);
      drawChart(c, { x0:0, x1:Math.max(35, Math.ceil(titr.added / 5) * 5 + 5), y0:0, y1:14, yt:[0, 2, 4, 6, 8, 10, 12, 14], xt:[0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50].map((v) => [v, String(v)]), xl:'NaOH added (mL)', yl:'pH', series:[{ hline:8.2, color:'rgba(255,61,139,0.7)', label:'pink above 8.2' }, { pts:titr.pts, color:'#5ee6c8', dots:true, r:3 }] });
      for (const [lab, v] of [['+1 mL', 1], ['+0.1 mL', 0.1], ['+1 drop', 0.05]]) btns.appendChild(stBtn(lab, () => titrAdd(v), false, titr.added + titr.v0 >= 50 || busy));
      btns.appendChild(stBtn('Record endpoint', () => { if (titrPH(titr.added) < 8.2){ toast('No lasting pink yet. Keep adding base.'); return; } handsFinish(); titr.ended = titr.added; titr.step = 3; award('scientist'); stRender(); }, true, busy));
    } else {
      const V = titr.ended, mol = titr.Cb * V / 1000, Ca = mol / (titr.Vacid / 1000), err = (Ca - titr.Ca) / titr.Ca * 100;
      body.appendChild(stKV([['Starting reading', titr.v0.toFixed(2) + ' mL'], ['Final reading', (titr.v0 + V).toFixed(2) + ' mL'], ['NaOH used', V.toFixed(2) + ' mL'], ['Moles of NaOH', '0.1000 M × ' + (V / 1000).toFixed(5) + ' L = ' + mol.toFixed(6) + ' mol'], ['Moles of HCl', mol.toFixed(6) + ' mol (they react 1 to 1)'], ['Acid concentration', mol.toFixed(6) + ' mol ÷ 0.02500 L = ' + Ca.toFixed(4) + ' M', 'hi']]));
      body.appendChild(stEl('p', Math.abs(err) < 1.5 ? 'stresult' : 'stwarn', 'The true concentration was ' + titr.Ca.toFixed(4) + ' M, so you were ' + Math.abs(err).toFixed(1) + '% ' + (err >= 0 ? 'high' : 'low') + '. ' + (Math.abs(err) < 1.5 ? 'Great technique!' : 'Going past the endpoint makes the answer come out high; slow down to single drops near the end.')));
      const c = stCanvas(640, 280); body.appendChild(c);
      const full = []; for (let v = 0; v <= 50; v += 0.25) full.push([v, titrPH(v)]);
      const veq = titrVeq();
      drawChart(c, { x0:0, x1:50, y0:0, y1:14, yt:[0, 2, 4, 6, 8, 10, 12, 14], xt:[0, 10, 20, 30, 40, 50].map((v) => [v, String(v)]), xl:'NaOH added (mL)', yl:'pH', series:[{ pts:full, color:'#5ee6c8' }, { vline:veq, color:'#ffd166', label:'equivalence ' + veq.toFixed(2) + ' mL' }, { pts:titr.pts, color:'rgba(255,61,139,0.85)', dots:true, line:false, r:3 }] });
      body.appendChild(stEl('p', 'stnote', 'The pH jumps from about 4 to 10 within a drop or two of the equivalence point. That steep jump is why one indicator color change can pin down the answer so precisely.'));
      btns.appendChild(stBtn('Try a new acid', () => { titr.step = 1; titrNew(); titrVisual(); stRender(); goView(this.view()); }, true));
      btns.appendChild(stBtn('Done', closeStation));
    }
  },
  tick(dt){
    let a = false;
    if (TT.dropT >= 0){ a = true; TT.dropT += dt; const k = TT.dropT / 0.28; TT.drop.visible = k < 1 && !REDUCED; TT.drop.position.set(TT.x, TT.bBot - 0.05 - k * (TT.bBot - 0.05 - (TT.y + 0.11)), TT.z); if (k >= 1) TT.dropT = -1; }
    if (titr.flash > 0 && titrPH(titr.added) < 8.2){ a = true; titr.flash = Math.max(0, titr.flash - dt * 0.7); titrVisual(); if (titr.flash === 0 && STN.id === 'titration'){ STN.cur.keepScroll = true; stRender(); } }
    if (STN.id === 'titration' && titr.step === 2 && !REDUCED){ a = true; TT.bar.rotation.y += dt * 9; }
    return a;
  }
};

/* ---------- 3. Pendulum ---------- */
const PD = { x:25.9, y:2.62, z:-9.2, arm:null, str:null, bob:null, gate:null, rod:null, disp:null };
const pdSpot = () => ({ x:26.02, z:-8.48, yaw:0, pitch:-0.05, bench:0 });
const PD_G = { bob:{ R:{ p:[0, 0, 0.037], into:[0, 0, -1], fingers:[-1, 0, 0], curl:0.55, out:0.5 } } };
function buildPendulumStation(M){
  const g = new THREE.Group(); g.userData.noMerge = true; scene.add(g);
  const wood = labMat(0xc8a27a, 0.6), steel = labMat(0xb9c0c6, 0.3, 0.7), dark = labMat(0x2b2f33, 0.5);
  addBox(0.03, 2.4, 1.1, wood, 25.615, 1.5, PD.z, 0, g);
  const sc = mk(96, 1024), ctx = sc.getContext('2d');
  ctx.fillStyle = '#f6f1e4'; ctx.fillRect(0, 0, 96, 1024); ctx.fillStyle = '#1b2a33'; ctx.font = '700 22px ' + F.type; ctx.textAlign = 'left';
  for (let i = 0; i <= 200; i++){ const y = 12 + i * 5, major = i % 10 === 0; ctx.fillRect(0, y, major ? 34 : i % 5 === 0 ? 24 : 14, 2); if (major) ctx.fillText((i / 100).toFixed(1), 40, y + 8); }
  addPlane(0.1, 2.048, basicMat(sc), 25.633, PD.y - 1.0, PD.z + 0.4, Math.PI / 2, g);
  addBox(0.34, 0.04, 0.06, steel, 25.63 + 0.17, PD.y + 0.03, PD.z, 0, g);
  const pc = mk(256, 140), pctx = pc.getContext('2d');
  pctx.strokeStyle = '#1b2a33'; pctx.lineWidth = 2; pctx.beginPath(); pctx.arc(128, 6, 118, 0, Math.PI); pctx.stroke();
  for (let d = -60; d <= 60; d += 5){ const a = Math.PI / 2 + d * Math.PI / 180, r0 = d % 15 === 0 ? 96 : 106; pctx.beginPath(); pctx.moveTo(128 + Math.cos(a) * r0, 6 + Math.sin(a) * r0); pctx.lineTo(128 + Math.cos(a) * 118, 6 + Math.sin(a) * 118); pctx.stroke(); }
  pctx.fillStyle = '#1b2a33'; pctx.font = '700 16px ' + F.type; pctx.textAlign = 'center'; for (const d of [-15, 0, 15]){ const a = Math.PI / 2 + d * Math.PI / 180; pctx.fillText(Math.abs(d) + '°', 128 + Math.cos(a) * 80, 12 + Math.sin(a) * 80); }
  const prot = new THREE.Mesh(new THREE.PlaneGeometry(0.36, 0.197), new THREE.MeshBasicMaterial({ map:tex(pc), transparent:true, toneMapped:false, depthWrite:false }));
  prot.position.set(PD.x - 0.02, PD.y - 0.098, PD.z); prot.rotation.y = Math.PI / 2; g.add(prot);
  const arm = new THREE.Group(); arm.position.set(PD.x, PD.y, PD.z); g.add(arm); PD.arm = arm;
  PD.str = new THREE.Mesh(new THREE.CylinderGeometry(0.0014, 0.0014, 1, 6), labMat(0xf2efe6, 0.8)); arm.add(PD.str);
  PD.bob = new THREE.Mesh(new THREE.SphereGeometry(0.035, 24, 16), labMat(0xc9a65a, 0.3, 0.85)); arm.add(PD.bob);
  addCyl(0.008, 0.008, 0.03, steel, PD.x, PD.y, PD.z, 10, g).rotation.z = Math.PI / 2;
  const gate = new THREE.Group(); g.add(gate); PD.gate = gate;
  const gateMat = labMat(0x1f4f7a, 0.45);
  for (const s of [-1, 1]) addBox(0.024, 0.1, 0.036, gateMat, s * 0.065, 0.005, 0, 0, gate);
  addBox(0.154, 0.024, 0.036, gateMat, 0, -0.045, 0, 0, gate);
  for (const s of [-1, 1]) addBox(0.008, 0.008, 0.008, glowMatOf(0xff4040), s * 0.052, 0.03, 0, 0, gate);
  /* The gate hangs from a side stand so its rod doesn't hide behind the swing */
  PD.rod = addCyl(0.007, 0.007, 1, steel, 0, 0, 0, 8, g);
  PD.bar = addBox(1, 0.014, 0.014, steel, 0, 0, 0, 0, g);
  PD.foot = addCyl(0.09, 0.1, 0.02, dark, PD.x + 0.065, 0.01, PD.z + 0.26, 20, g);
  const box = addBox(0.04, 0.14, 0.26, dark, 25.65, 1.0, PD.z - 0.38, 0, g);
  PD.disp = makeDisplay(0.2, 0.075, 320, 120); PD.disp.m.position.set(25.672, 1.0, PD.z - 0.38); PD.disp.m.rotation.y = Math.PI / 2; g.add(PD.disp.m); PD.disp.set('0.000 s', 'PHOTOGATE');
  pickBox(0.7, 2.3, 1.2, 26.1, 1.4, PD.z, { station:'pendulum' });
  PD.bobPick = pickBox(0.16, 0.16, 0.16, PD.x, PD.y - 1, PD.z, { station:'pendulum', act:'bob' });
  addPlane(0.62, 0.14, basicMat(drawTableCard('PENDULUM', 'Measure gravity')), 25.64, 0.42, PD.z, Math.PI / 2);
  OBST.push({ x:26.2, z:PD.z, r:0.62 });
  pendSetLen(pend.L);
}
const pend = { step:0, L:1.0, deg:10, run:false, t:0, swings:0, tMeas:0, fast:false, rows:[] };
function pendPeriod(){ const g = 9.81, th = pend.deg * Math.PI / 180; return 2 * Math.PI * Math.sqrt(pend.L / g) * (1 + th * th / 16); }
function pendSetLen(L){
  pend.L = L;
  PD.str.scale.y = L; PD.str.position.y = -L / 2; PD.bob.position.y = -L;
  PD.gate.position.set(PD.x + 0.0, PD.y - L, PD.z);
  const gy = PD.y - L - 0.045; PD.rod.scale.y = Math.max(0.05, gy); PD.rod.position.set(PD.x + 0.065, gy / 2, PD.z + 0.26);
  PD.bar.scale.x = 0.26; PD.bar.rotation.y = Math.PI / 2; PD.bar.position.set(PD.x + 0.065, gy, PD.z + 0.13);
  PD.gate.visible = PD.rod.visible = PD.bar.visible = PD.foot.visible = PD.y - L > 0.12;
  if (PD.bobPick) PD.bobPick.position.y = PD.y - L;
  if (!pend.run) PD.arm.rotation.x = 0;
  wake();
}
/* Pull the bob back to the release angle with your hand, hold it still, and let go */
function pendRelease(){
  if (pend.run || handsBusy()) return;
  const C = hClip(pdSpot()), a0 = PD.arm.rotation.x, a1 = -pend.deg * Math.PI / 180;
  hGrab(C, PD.bob, PD_G.bob, 0.7, { arc:0.05 });
  hAnim(C, 0.9, (u) => { PD.arm.rotation.x = a0 + (a1 - a0) * hsm(u); wake(); }); hWait(C, 0.9);
  hWait(C, 0.5);
  hAt(C, () => { PD.arm.rotation.x = a1; pend.run = true; pend.t = 0; pend.swings = 0; PD.disp.set('0.000 s', 'SWING 0 OF 10'); if (STN.id === 'pendulum') stRender(); });
  hRest(C, ['R'], 0.45);
  handsPlay(C, () => { if (STN.id === 'pendulum') stRender(); });
}
STATIONS.pendulum = {
  id:'pendulum', room:'lab', kick:'Room 102 · Science Lab', hands:true,
  spot(){ return pdSpot(); },
  leave(){ handsFinish(); },
  act(id){ if (pend.step === 0){ toast('Press Start to begin.'); return; } if (pend.run){ toast('Let it finish its 10 swings.'); return; } pendRelease(); },
  actLabel(id){ return pend.step > 0 && !pend.run && !handsBusy() ? 'Pull back and release' : ''; },
  title(){ return pend.step === 0 ? 'Pendulum: measure gravity' : pend.run ? 'Timing 10 swings' : 'Set up a trial'; },
  stepText(){ return pend.rows.length ? pend.rows.length + (pend.rows.length === 1 ? ' trial' : ' trials') + ' recorded' : ''; },
  view(){ const s = pdSpot(); return pend.step === 0 ? { x:narrow() ? 28.7 : 28.25, z:PD.z, yaw:Math.PI / 2, pitch:narrow() ? 0.05 : 0.1 } : { x:s.x, z:s.z, yaw:s.yaw, pitch:s.pitch }; },
  render(body, btns){
    if (pend.step === 0){
      body.appendChild(stEl('p', 'stp', 'A pendulum’s swing time depends on its length and on gravity, but not on how heavy the bob is. Time 10 full swings, and you can work out the strength of gravity, g.'));
      body.appendChild(stEl('p', 'stp', 'The math: one swing takes T = 2π√(L ÷ g), so g = 4π²L ÷ T².'));
      btns.appendChild(stBtn('Start', () => { pend.step = 1; stRender(); goView(this.view()); }, true));
      return;
    }
    if (!pend.run){
      body.appendChild(stEl('p', 'stp', 'Set the length from the pivot to the center of the bob. Then take hold of the bob, pull it back to the release angle, keep it still and let go. The photogate counts 10 full swings (there and back).'));
      body.appendChild(stSlider('Length', 0.25, 2.0, 0.05, pend.L, (v) => v.toFixed(2) + ' m', (v) => pendSetLen(v)));
      body.appendChild(stSlider('Release angle', 5, 15, 1, pend.deg, (v) => v + '°', (v) => { pend.deg = v; wake(); }));
      btns.appendChild(stBtn('Pull back and release', pendRelease, true, handsBusy()));
      if (handsBusy()) btns.appendChild(stBtn('Skip ahead', () => { handsFinish(); stRender(); }));
    } else {
      body.appendChild(stEl('p', 'stp', 'Swinging… The photogate times each pass. Let it finish 10 full swings.'));
      body.appendChild(stKV([['Length', pend.L.toFixed(2) + ' m'], ['Swings', String(pend.swings) + ' of 10']]));
      btns.appendChild(stToggle(pend.fast ? 'Real speed' : 'Speed ×4', pend.fast, () => { pend.fast = !pend.fast; STN.cur.keepScroll = true; stRender(); }));
      btns.appendChild(stBtn('Stop', () => { pend.run = false; PD.arm.rotation.x = 0; stRender(); }));
    }
    if (pend.rows.length){
      body.appendChild(stEl('h3', 'sth3', 'Your data'));
      body.appendChild(stTable(['L (m)', '10 swings (s)', 'T (s)', 'g (m/s²)'], pend.rows.map((r) => [r.L.toFixed(2), r.t10.toFixed(3), r.T.toFixed(4), r.g.toFixed(2)]), 'compact num'));
      if (pend.rows.length >= 2){
        const sxx = pend.rows.reduce((s, r) => s + r.L * r.L, 0), sxy = pend.rows.reduce((s, r) => s + r.L * r.T * r.T, 0), k = sxy / sxx, gFit = 4 * Math.PI * Math.PI / k;
        const c = stCanvas(640, 280); body.appendChild(c);
        drawChart(c, { x0:0, x1:2.1, y0:0, y1:Math.max(9, Math.ceil(k * 2.1)), yt:[0, 2, 4, 6, 8], xt:[0, 0.5, 1, 1.5, 2].map((v) => [v, v.toFixed(1)]), xl:'length L (m)', yl:'T² (s²)', series:[{ pts:[[0, 0], [2.1, k * 2.1]], color:'rgba(255,209,102,0.8)', w:2 }, { pts:pend.rows.map((r) => [r.L, r.T * r.T]), color:'#5ee6c8', dots:true, line:false, r:5 }] });
        body.appendChild(stEl('p', 'stresult', 'From the slope of your line: g = ' + gFit.toFixed(2) + ' m/s². The accepted value is about 9.81 m/s² (' + Math.abs((gFit - 9.81) / 9.81 * 100).toFixed(1) + '% off).'));
      } else body.appendChild(stEl('p', 'sthint', 'Try two more lengths, like 0.50 m and 1.50 m. Plotting T² against L gives a straight line, and its slope gives g.'));
      if (!pend.run) btns.appendChild(stBtn('Clear data', () => { pend.rows = []; stRender(); }));
    }
    btns.appendChild(stBtn('Done', closeStation));
  },
  tick(dt){
    if (!pend.run) return false;
    const T = pendPeriod(), sp = REDUCED ? 200 : pend.fast ? 4 : 1;
    pend.t += dt * sp;
    const th0 = pend.deg * Math.PI / 180, decay = Math.exp(-pend.t * 0.004);
    PD.arm.rotation.x = -th0 * decay * Math.cos(2 * Math.PI * pend.t / T);
    const n = Math.min(10, Math.floor(pend.t / T));
    PD.disp.set(pend.t.toFixed(3) + ' s', 'SWING ' + n + ' OF 10');
    if (n !== pend.swings){ pend.swings = n; if (STN.id === 'pendulum'){ STN.cur.keepScroll = true; stRender(); } }
    if (n >= 10){
      const t10 = 10 * T + (Math.random() - 0.5) * 0.008, Tm = t10 / 10;
      pend.rows.push({ L:pend.L, t10, T:Tm, g:4 * Math.PI * Math.PI * pend.L / (Tm * Tm) });
      pend.run = false; PD.arm.rotation.x = 0; PD.disp.set(t10.toFixed(3) + ' s', '10 SWINGS');
      award('scientist');
      if (STN.id === 'pendulum') stRender();
    }
    return true;
  }
};
