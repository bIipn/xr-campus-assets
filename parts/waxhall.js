/* ================================================================
   Living History: the Wax Hall, through the doorway at the end of Gallery 3.
   Twelve stages tell XRLibraries' story in date order, alternating left and
   right as you walk, with the last two across the far wall. A stage comes to
   life when you walk up to it and freezes again, like wax, when you leave.
   ================================================================ */
const WH = { x0:-8.5, x1:8.5, z0:-81, z1:-42.3, h:5.2, stage:0.2, depth:3.9, bay:5.6, gap:0.3, first:-45.3, rope:4.45, door:-42.15 };
const WAX_ITEMS = [];

/* Where each stage sits: side bays face the walkway, the end bays face back toward the door */
function waxBays(){
  const out = [];
  for (let k = 0; k < 5; k++){
    const zc = WH.first - WH.bay / 2 - k * (WH.bay + WH.gap);
    out.push({ side:'L', x:WH.x0 + WH.depth, z:zc, ry:Math.PI / 2, len:WH.bay });
    out.push({ side:'R', x:WH.x1 - WH.depth, z:zc, ry:-Math.PI / 2, len:WH.bay });
  }
  const ez = WH.z0 + WH.depth;
  out.push({ side:'E', x:-4.15, z:ez, ry:0, len:8.0 });
  out.push({ side:'E', x:4.15, z:ez, ry:0, len:8.0 });
  return out;
}
const WAX_BAYS = waxBays();

/* ---------- Painted pieces ---------- */
function canvasParquet(){
  const S = 512, c = mk(S, S), ctx = c.getContext('2d'), r = rnd(31), n = 8, w = S / n;
  for (let i = 0; i < n; i++) for (let j = 0; j < n * 2; j++){
    const v = 0.85 + r() * 0.3, b = [74 * v, 48 * v, 34 * v].map(Math.round);
    ctx.fillStyle = 'rgb(' + b.join(',') + ')';
    const odd = (i + j) % 2;
    if (odd) ctx.fillRect(i * w, j * w / 2, w, w / 2); else ctx.fillRect(i * w, j * w / 2, w / 2, w / 2), ctx.fillRect(i * w + w / 2, j * w / 2, w / 2, w / 2);
    ctx.strokeStyle = 'rgba(20,10,5,0.55)'; ctx.lineWidth = 1.5; ctx.strokeRect(i * w + 0.5, j * w / 2 + 0.5, w - 1, w / 2 - 1);
    ctx.strokeStyle = 'rgba(30,16,8,0.18)'; ctx.lineWidth = 1;
    for (let k = 0; k < 4; k++){ const y = j * w / 2 + 4 + r() * (w / 2 - 8); ctx.beginPath(); ctx.moveTo(i * w + 2, y); ctx.lineTo(i * w + w - 2, y + (r() - 0.5) * 4); ctx.stroke(); }
  }
  return c;
}
function canvasRunnerRed(){
  const W = 256, H = 512, c = mk(W, H), ctx = c.getContext('2d'), r = rnd(12);
  ctx.fillStyle = '#5e1a22'; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 4000; i++){ const v = r(); ctx.fillStyle = v > 0.5 ? 'rgba(255,200,170,0.035)' : 'rgba(0,0,0,0.06)'; ctx.fillRect(r() * W, r() * H, 2, 2); }
  ctx.fillStyle = '#c9a25c'; ctx.fillRect(10, 0, 6, H); ctx.fillRect(W - 16, 0, 6, H);
  ctx.fillStyle = 'rgba(201,162,92,0.5)'; ctx.fillRect(22, 0, 2, H); ctx.fillRect(W - 24, 0, 2, H);
  ctx.strokeStyle = 'rgba(201,162,92,0.35)'; ctx.lineWidth = 2;
  for (let y = 32; y < H; y += 128){ ctx.beginPath(); ctx.moveTo(W / 2, y); ctx.lineTo(W / 2 + 30, y + 30); ctx.lineTo(W / 2, y + 60); ctx.lineTo(W / 2 - 30, y + 30); ctx.closePath(); ctx.stroke(); }
  return c;
}
function canvasVelvet(){
  const W = 256, H = 256, c = mk(W, H), ctx = c.getContext('2d');
  const g = ctx.createLinearGradient(0, 0, W, 0);
  for (let i = 0; i <= 8; i++) g.addColorStop(i / 8, i % 2 ? '#3a0f16' : '#6a1c26');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  return c;
}
/* A year and title above each stage, like a theatre header */
function drawWaxHeader(sc){
  const W = 1200, H = 210, c = mk(W, H), ctx = c.getContext('2d');
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#1d1214'); g.addColorStop(1, '#2a191c');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = 'rgba(205,169,97,0.85)'; ctx.lineWidth = 4; ctx.strokeRect(10, 10, W - 20, H - 20);
  ctx.strokeStyle = 'rgba(205,169,97,0.35)'; ctx.lineWidth = 1.5; ctx.strokeRect(22, 22, W - 44, H - 44);
  ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
  ctx.fillStyle = '#d9b56c'; ctx.font = '700 104px ' + F.display; ctx.fillText(sc.year, 58, H / 2 + 6);
  const yw = ctx.measureText(sc.year).width;
  ctx.fillStyle = 'rgba(205,169,97,0.6)'; ctx.fillRect(58 + yw + 34, 52, 2, H - 104);
  ctx.fillStyle = '#efe7d5'; fit(ctx, sc.title, F.display, '400', 64, W - yw - 220); ctx.fillText(sc.title, 58 + yw + 66, H / 2 - 4);
  ctx.fillStyle = 'rgba(205,169,97,0.95)'; ctx.font = '700 26px ' + F.type; ctx.textAlign = 'right'; ctx.fillText('SCENE ' + sc.n + ' OF 12', W - 50, H - 40);
  return c;
}
/* The reading rail in front of each stage */
function drawWaxRail(sc){
  const W = 900, H = 560, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#efe7d6'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#5e1a22'; ctx.fillRect(0, 0, W, 14);
  ctx.textAlign = 'left'; ctx.fillStyle = '#7a6a50'; ctx.font = '700 22px ' + F.type; ctx.fillText('LIVING HISTORY · SCENE ' + sc.n, 44, 62);
  ctx.textAlign = 'right'; ctx.fillStyle = '#5e1a22'; ctx.font = '700 46px ' + F.display; ctx.fillText(sc.year, W - 44, 70);
  ctx.textAlign = 'left'; ctx.fillStyle = '#2b2419'; fit(ctx, sc.title, F.display, '700', 44, W - 88); ctx.fillText(sc.title, 44, 128);
  ctx.font = '400 25px ' + F.ui; ctx.fillStyle = '#3d3427';
  const lines = wrap(ctx, sc.item.desc, W - 88).slice(0, 10);
  lines.forEach((l, i) => ctx.fillText(l, 44, 184 + i * 34));
  ctx.fillStyle = '#7a6a50'; ctx.font = '400 20px ' + F.type;
  const s = srcList(sc.item.src).map((x) => x.label).join(' · ');
  wrap(ctx, 'Sources: ' + s, W - 88).slice(0, 2).forEach((l, i) => ctx.fillText(l, 44, H - 66 + i * 26));
  ctx.fillStyle = '#9a8a6c'; ctx.font = 'italic 400 19px ' + F.display; ctx.textAlign = 'right'; ctx.fillText('Figures are reenactors, not likenesses of real people', W - 44, H - 14);
  return c;
}
function drawWaxIntro(){
  const W = 1500, H = 900, c = mk(W, H), ctx = c.getContext('2d');
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#2a1519'); g.addColorStop(1, '#1a0f11');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = 'rgba(205,169,97,0.9)'; ctx.lineWidth = 5; ctx.strokeRect(24, 24, W - 48, H - 48);
  ctx.strokeStyle = 'rgba(205,169,97,0.35)'; ctx.lineWidth = 2; ctx.strokeRect(40, 40, W - 80, H - 80);
  ctx.textAlign = 'center';
  ctx.fillStyle = '#cda961'; ctx.font = '700 34px ' + F.type; ctx.fillText('LIVING HISTORY', W / 2, 150);
  ctx.fillStyle = '#efe7d5'; ctx.font = '400 128px ' + F.display; ctx.fillText('The Wax Hall', W / 2, 290);
  ctx.fillStyle = '#d9b56c'; ctx.fillRect(W / 2 - 160, 330, 320, 3);
  ctx.fillStyle = 'rgba(239,231,213,0.92)'; ctx.font = '400 40px ' + F.ui;
  ['XRLibraries’ story, acted out from the very beginning.', 'Walk up to a scene and the figures come to life.', 'Twelve scenes from 2016 to 2025, left and right as you go.'].forEach((l, i) => ctx.fillText(l, W / 2, 420 + i * 62));
  ctx.fillStyle = 'rgba(205,169,97,0.9)'; ctx.font = '400 30px ' + F.type; ctx.fillText('TAP A READING RAIL OR A FIGURE FOR SOURCES', W / 2, 670);
  ctx.fillStyle = 'rgba(239,231,213,0.55)'; ctx.font = 'italic 400 30px ' + F.display;
  ctx.fillText('The figures are reenactors made for this concept, not likenesses of real people.', W / 2, 770);
  return c;
}
function drawWaxTimeline(){
  const W = 1500, H = 900, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#1d1113'; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = 'rgba(205,169,97,0.8)'; ctx.lineWidth = 4; ctx.strokeRect(24, 24, W - 48, H - 48);
  ctx.textAlign = 'left'; ctx.fillStyle = '#cda961'; ctx.font = '700 30px ' + F.type; ctx.fillText('THE SCENES', 90, 112);
  WAX_SCENES.forEach((sc, i) => {
    const col = i < 6 ? 0 : 1, row = i % 6, x = 90 + col * 690, y = 190 + row * 112;
    ctx.fillStyle = '#d9b56c'; ctx.font = '700 46px ' + F.display; ctx.fillText(String(sc.n), x, y);
    ctx.fillStyle = '#cda961'; ctx.font = '700 26px ' + F.type; ctx.fillText(sc.year, x + 70, y - 18);
    ctx.fillStyle = '#efe7d5'; fit(ctx, sc.title, F.display, '400', 38, 560); ctx.fillText(sc.title, x + 70, y + 20);
  });
  return c;
}

/* ---------- Shared materials and props ---------- */
let WM = null;
function waxM(){
  if (WM) return WM;
  const S = (hex, r, m, e) => stdMat(hex, r == null ? 0.7 : r, m || 0, e);
  WM = {
    wood:S(0x6b4527, 0.55), dark:S(0x2c1d14, 0.5), pale:S(0xc9a77a, 0.6), white:S(0xeeebe4, 0.5), black:S(0x1c1e21, 0.4, 0.1), steel:S(0xa9b0b6, 0.35, 0.7),
    brass:S(0xb58f4c, 0.32, 0.55), plastic:S(0x2a2d31, 0.45), cream:S(0xe9e1cf, 0.8), red:S(0xa8323a, 0.6), green:S(0x3f7a4a, 0.7), blue:S(0x2e5f8a, 0.6),
    yellow:S(0xe2b43c, 0.6), orange:S(0xd8792c, 0.6), purple:S(0x6a4a8a, 0.6), teal:S(0x2a9188, 0.6), grey:S(0x7a7d80, 0.8), hay:S(0xc9a650, 0.95), cardboard:S(0xb08a5a, 0.9),
    velvet:new THREE.MeshStandardMaterial({ map:tex(canvasVelvet()), color:0xffffff, roughness:0.85 }),
    holo:new THREE.MeshBasicMaterial({ color:0x63e2ff, transparent:true, opacity:0.42, blending:THREE.AdditiveBlending, depthWrite:false, toneMapped:false, side:THREE.DoubleSide }),
    holoLine:new THREE.LineBasicMaterial({ color:0x9df0ff, transparent:true, opacity:0.85, blending:THREE.AdditiveBlending, depthWrite:false, toneMapped:false }),
    glow:new THREE.MeshBasicMaterial({ color:0xfff1d6, toneMapped:false }),
    screen:(canvas) => new THREE.MeshBasicMaterial({ map:tex(canvas), toneMapped:false })
  };
  WM.holo.userData.keep = true; WM.glow.userData.keep = true;
  return WM;
}

/* A stage's local frame: +z faces the walkway, y = 0 is the stage top, x runs along the stage */
class WaxStage {
  constructor(sc, bay){
    this.sc = sc; this.bay = bay;
    this.g = new THREE.Group(); this.g.position.set(bay.x, WH.stage, bay.z); this.g.rotation.y = bay.ry;
    this.figs = []; this.ticks = []; this.carries = []; this.anim = new THREE.Group(); this.anim.userData.noMerge = true; this.g.add(this.anim);
    this.t = 0; this.live = false; this.glow = 0;
  }
  m(){ return waxM(); }
  box(w, h, d, mat, x, y, z, ry, parent){ const o = addBox(w, h, d, mat, x, y, z, ry, parent || this.g); return o; }
  cyl(rt, rb, h, mat, x, y, z, seg, parent){ const o = new THREE.Mesh(new THREE.CylinderGeometry(rt, rb, h, seg || 16), mat); o.position.set(x, y, z); (parent || this.g).add(o); return o; }
  sph(r, mat, x, y, z, sx, sy, sz, parent){ const o = new THREE.Mesh(new THREE.SphereGeometry(r, 16, 12), mat); o.position.set(x, y, z); o.scale.set(sx || 1, sy || 1, sz || 1); (parent || this.g).add(o); return o; }
  plane(w, h, mat, x, y, z, ry, rx, parent){ const o = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat); o.position.set(x, y, z); o.rotation.set(rx || 0, ry || 0, 0); (parent || this.g).add(o); return o; }
  grp(x, y, z, ry, parent){ const o = new THREE.Group(); o.position.set(x, y, z); o.rotation.y = ry || 0; (parent || this.g).add(o); return o; }
  /* Moving props live under this.anim so they are never merged away */
  live3(x, y, z, ry){ return this.grp(x, y, z, ry, this.anim); }
  fig(look, at, ry, keys){
    const f = makeWaxFigure(look);
    f.home = { at, ry:(ry || 0) };
    this.anim.add(f.root);
    if (keys) this.keys(f, keys);
    f.track = f.track || waxTrack([{ t:0, p:'ease' }], f.home);
    this.figs.push(f); f.stage = this;
    for (const m of [f.cloth, f.body]) if (m) m.userData.wax = this.sc.id;
    if (f.rb) f.onMesh.push((mesh) => { mesh.userData.wax = this.sc.id; });
    return f;
  }
  keys(f, keys){ f.track = waxTrack(keys, f.home); }
  tick(fn){ this.ticks.push(fn); }
  /* A prop that is really held. It rests on a figure's bone (usually the chest, so it moves with the
     body), on the stage, or on a head, and glides between those. Hands that hold it reach it by IK.
     grips:{ name:{ p, into, fingers, curl, out, point } } in the prop's frame, in metres.
     keys:[{ t, blend, lift, fig, bone, p, r } | { t, blend, lift, at, r }] (r in degrees).
     holds:[{ fig, s:'L'|'R', grip, t0, t1, in, out, node }]: node is a child of the prop to grip instead. */
  carry(obj, grips, keys, holds){
    if (obj.parent !== this.anim) this.anim.add(obj);
    obj.matrixAutoUpdate = false;
    obj.traverse((o) => { o.userData.noMerge = true; });
    const c = { obj, grips, keys:keys.slice().sort((a, b) => a.t - b.t), holds:holds || [], M:new THREE.Matrix4() };
    this.carries.push(c);
    return c;
  }
}
/* Where a headset sits on a person's head, in the head bone's frame */
function waxHeadP(fig){
  const R = fig.R, em = R.eyeMid, H = R.P[HB.Head];
  return [em.x - H.x, em.y - H.y + 0.005, em.z - H.z + 0.035];
}
/* Frames for carried props */
const WC = {
  bone:(fig, bone, p, r) => ({ fig, bone, p, r:r || [0, 0, 0] }),
  chest:(fig, p, r) => ({ fig, bone:'Spine2', p, r:r || [0, 0, 0] }),
  head:(fig) => ({ fig, bone:'Head', p:waxHeadP(fig), r:[0, 0, 0] }),
  at:(x, y, z, r) => ({ at:[x, y, z], r:r || [0, 0, 0] }),
  /* In a hand, by one of the prop's grips: the prop follows that hand wherever its pose takes it */
  palm:(fig, s, grip) => ({ fig, palm:s, grip })
};
const WCK = (t, blend, frame, lift) => Object.assign({ t, blend:blend || 0, lift:lift || 0 }, frame);
const WCH = (fig, s, grip, t0, t1, io, extra) => Object.assign({ fig, s, grip, t0, t1, in:io == null ? 0.3 : io, out:io == null ? 0.3 : io }, extra || {});
/* A headset held by its sides: A is the +x side, B the -x side; m = fingers toward -z */
const HS_GRIPS = {
  A:{ p:[0.096, -0.006, -0.012], into:[-1, 0, 0], fingers:[0, 0.45, 1], curl:0.45 },
  B:{ p:[-0.096, -0.006, -0.012], into:[1, 0, 0], fingers:[0, 0.45, 1], curl:0.45 },
  Am:{ p:[0.096, -0.006, 0.0], into:[-1, 0, 0], fingers:[0, 0.45, -1], curl:0.45 },
  Bm:{ p:[-0.096, -0.006, 0.0], into:[1, 0, 0], fingers:[0, 0.45, -1], curl:0.45 }
};
const _cT = new THREE.Matrix4(), _cA = new THREE.Matrix4(), _cE = new THREE.Euler(), _cQ = new THREE.Quaternion(), _cQ2 = new THREE.Quaternion(), _cP = new THREE.Vector3(), _cP2 = new THREE.Vector3(), _cS = new THREE.Vector3(), _cInv = new THREE.Matrix4(), _cN = new THREE.Matrix4();
function waxFrameOf(S, K, out){
  if (K.palm) return hkAnchorMatrix(K.fig, K.palm, K.grip, out);
  _cE.set((K.r ? K.r[0] : 0) * D2R, (K.r ? K.r[1] : 0) * D2R, (K.r ? K.r[2] : 0) * D2R);
  _cQ.setFromEuler(_cE);
  if (K.bone){ out.compose(_cP.fromArray(K.p).multiplyScalar(K.fig.S), _cQ, _ik.one); return out.premultiply(K.fig.all[HB[K.bone]].matrixWorld); }
  out.compose(_cP.fromArray(K.at), _cQ, _ik.one);
  return out.premultiply(S.anim.matrixWorld);
}
function waxHoldW(h, t){
  const a = h.in, b = h.out, t1 = h.t1 == null ? 1e9 : h.t1;
  if (t < h.t0) return a > 0 ? wsm(h.t0 - a, h.t0, t) : 0;
  if (t <= t1) return 1;
  return b > 0 ? 1 - wsm(t1, t1 + b, t) : 0;
}
/* Place every carried prop for this moment, then bring the hands that hold them onto their grips */
function waxResolve(S){
  if (!S.carries.length) return;
  const t = S.t;
  S.anim.updateWorldMatrix(true, false);
  for (const f of S.figs) f.root.updateMatrixWorld(true);
  _cInv.copy(S.anim.matrixWorld).invert();
  for (const c of S.carries){
    const ks = c.keys; let i = 0; while (i < ks.length - 1 && ks[i + 1].t <= t) i++;
    const K = ks[i]; waxFrameOf(S, K, c.M);
    if (i > 0 && K.blend > 0 && t < K.t + K.blend){
      waxFrameOf(S, ks[i - 1], _cA);
      const u = clamp((t - K.t) / K.blend, 0, 1), k = u * u * u * (u * (u * 6 - 15) + 10);
      _cA.decompose(_cP, _cQ, _cS); c.M.decompose(_cP2, _cQ2, _cS);
      _cP.lerp(_cP2, k); if (K.lift) _cP.y += K.lift * Math.sin(Math.PI * k);
      _cQ.slerp(_cQ2, k); c.M.compose(_cP, _cQ, _ik.one);
    }
    c.obj.matrix.multiplyMatrices(_cInv, c.M); c.obj.matrixWorldNeedsUpdate = true;
  }
  for (const c of S.carries){
    let nodesFresh = false;
    for (const h of c.holds){
      const w = waxHoldW(h, t); if (w <= 0) continue;
      const g = c.grips[h.grip], f = h.fig;
      let M = c.M;
      if (h.node){ if (!nodesFresh){ c.obj.updateMatrixWorld(true); nodesFresh = true; } M = h.node.matrixWorld; }
      if (h.off){ const o = h.off(t); M = _cN.multiplyMatrices(M, _cT.makeTranslation(o[0], o[1], o[2])); }
      hkGrip(f, h.s, M, g, w);
      const L = h.s === 'L', cur = f.grip || [0, 0, 0, 0];
      const gl = L ? lerp(f.pose[WR + 6], g.curl, w) : cur[0], gr = L ? cur[1] : lerp(f.pose[WR + 7], g.curl, w);
      const pl = L ? (g.point || 0) * w : cur[2], pr = L ? cur[3] : (g.point || 0) * w;
      hkFingers(f, gl, gr, pl, pr);
    }
  }
}

/* ---------- Building the hall ---------- */
function buildWaxHall(M){
  const wm = waxM();
  const { x0, x1, z0, z1, h } = WH;
  /* Floor: dark parquet with a red runner down the middle */
  addFloor(x0, x1, z0, z1 + 0.2, new THREE.MeshStandardMaterial({ map:repTex(canvasParquet(), (x1 - x0) / 2.4, (z1 - z0) / 2.4), roughness:0.42, color:0xd8c8bc }));
  const run = new THREE.Mesh(new THREE.PlaneGeometry(3.2, WH.first - (z0 + WH.depth) + 2.6), new THREE.MeshStandardMaterial({ map:repTex(canvasRunnerRed(), 1, 9), roughness:0.92 }));
  run.rotation.x = -Math.PI / 2; run.position.set(0, 0.006, (WH.first + 0.6 + z0 + WH.depth) / 2); run.receiveShadow = true; scene.add(run);
  addCeil(x0, x1, z0, z1, h, stdMat(0x1a1416, 1));
  /* Walls: deep plum with a gilt rail */
  const plum = new THREE.MeshStandardMaterial({ color:srgb(0x3b1e28), map:repTex(canvasPlaster(), 3, 1.2), roughness:0.92 });
  for (const sx of [-1, 1]){
    const w = new THREE.Mesh(new THREE.PlaneGeometry(z1 - z0, h), plum); w.rotation.y = -sx * Math.PI / 2; w.position.set(sx * x1, h / 2, (z0 + z1) / 2); w.userData.blocker = true; scene.add(w); blockers.push(w);
    addBox(0.05, 0.08, z1 - z0, wm.brass, sx * (x1 - 0.03), 4.0, (z0 + z1) / 2);
  }
  const end = new THREE.Mesh(new THREE.PlaneGeometry(x1 - x0, h), plum); end.position.set(0, h / 2, z0); end.userData.blocker = true; scene.add(end); blockers.push(end);
  addBox(x1 - x0, 0.08, 0.05, wm.brass, 0, 4.0, z0 + 0.03);
  /* South wall around the doorway, seen from inside */
  const sw = new THREE.Shape();
  sw.moveTo(x0, 0); sw.lineTo(-1.6, 0); sw.lineTo(-1.6, 3.1); sw.lineTo(1.6, 3.1); sw.lineTo(1.6, 0); sw.lineTo(x1, 0); sw.lineTo(x1, h); sw.lineTo(x0, h); sw.lineTo(x0, 0);
  const south = new THREE.Mesh(new THREE.ShapeGeometry(sw), plum); south.rotation.y = Math.PI; south.position.set(0, 0, z1); south.userData.blocker = true; scene.add(south); blockers.push(south);
  /* Velvet curtains tied back at the doorway */
  for (const s of [-1, 1]){
    const cur = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.34, 3.1, 14, 1, false, 0, Math.PI), wm.velvet);
    cur.position.set(s * 1.85, 1.55, z1 - 0.12); cur.rotation.y = s > 0 ? -Math.PI / 2 : Math.PI / 2; scene.add(cur);
    addBox(0.06, 0.06, 0.4, wm.brass, s * 1.75, 1.2, z1 - 0.2);
  }
  addBox(4.2, 0.36, 0.22, wm.velvet, 0, 3.3, z1 - 0.13);

  /* Stages: platform, proscenium, header, backdrop, rope and reading rail */
  const fascia = stdMat(0x24161a, 0.6), trim = wm.brass, divider = new THREE.MeshStandardMaterial({ color:srgb(0x2c171d), map:repTex(canvasPlaster(), 1, 1), roughness:0.9 });
  WAX_SCENES.forEach((sc, i) => {
    const bay = WAX_BAYS[i], S = new WaxStage(sc, bay), L = bay.len, D = WH.depth;
    sc.stage = S; sc.bay = bay;
    scene.add(S.g);
    /* Platform top and front fascia */
    const top = new THREE.Mesh(new THREE.PlaneGeometry(L, D), new THREE.MeshStandardMaterial({ map:tex(waxFloorCanvas(sc.floor || 'boards')), roughness:0.75 }));
    top.rotation.x = -Math.PI / 2; top.position.set(0, 0, -D / 2); S.g.add(top);
    S.box(L, WH.stage, 0.04, fascia, 0, -WH.stage / 2, -0.02);
    S.box(L, 0.025, 0.05, trim, 0, -0.012, 0.0);
    /* Backdrop painted for the scene */
    const bd = S.plane(L, 3.55, new THREE.MeshStandardMaterial({ map:tex(waxBackdrop(sc.backdrop, L)), roughness:0.92, emissive:0xffffff, emissiveIntensity:0.0 }), 0, 3.55 / 2, -D + 0.02, 0);
    bd.material.emissiveMap = bd.material.map; bd.material.emissiveIntensity = 0.12; S.backdrop = bd;
    /* Header with the year and title */
    S.plane(L, L * 210 / 1200, basicMat(drawWaxHeader(sc)), 0, 3.55 + L * 105 / 1200 + 0.06, -D + 0.03, 0);
    S.box(L + 0.2, 0.06, 0.12, trim, 0, 3.6, -D + 0.08);
    /* Reading rail: a slanted card on brass legs at the rope line */
    const rail = S.grp(L * 0.3 * (bay.side === 'E' ? 0.62 : 1), 0, 0.12, 0);
    const card = drawWaxRail(sc), cm = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.56), basicMat(card, 0xe9e3d8));
    cm.position.set(0, 0.92 - WH.stage, 0.06); cm.rotation.x = -0.72; rail.add(cm);
    addBox(0.96, 0.03, 0.62, trim, 0, 0.9 - WH.stage - 0.02, 0.05, 0, rail).rotation.x = -0.72;
    for (const sx of [-0.36, 0.36]) addBox(0.04, 0.84, 0.04, trim, sx, (0.84 - WH.stage) / 2 - 0.04 + 0.0, -0.08, 0, rail);
    cm.userData.item = sc.item; pickItems.push(cm);
    S.rail = rail;
    /* Rope: brass posts with a velvet rope sagging between them */
    const posts = bay.side === 'E' ? [-L / 2 + 0.25, -L / 6, L / 6, L / 2 - 0.25] : [-L / 2 + 0.2, 0, L / 2 - 0.2];
    for (const px of posts){ S.cyl(0.022, 0.026, 0.9, trim, px, 0.45 - WH.stage, 0.18, 10); S.sph(0.04, trim, px, 0.92 - WH.stage, 0.18); S.cyl(0.13, 0.15, 0.03, trim, px, 0.015 - WH.stage, 0.18, 18); }
    for (let k = 0; k < posts.length - 1; k++){
      const a = posts[k], b = posts[k + 1], pts = [];
      for (let u = 0; u <= 12; u++){ const t = u / 12, x = a + (b - a) * t; pts.push(new THREE.Vector3(x, 0.86 - WH.stage - 0.16 * Math.sin(Math.PI * t), 0.18)); }
      const rope = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 16, 0.016, 6), wm.velvet); S.g.add(rope);
    }
    /* A warm pool of light on the stage that brightens when the scene is live */
    const pool = new THREE.Mesh(new THREE.PlaneGeometry(L * 0.95, D * 1.1), new THREE.MeshBasicMaterial({ map:WAX.poolTex || (WAX.poolTex = tex(canvasPool())), transparent:true, opacity:0.16, blending:THREE.AdditiveBlending, depthWrite:false, toneMapped:false }));
    pool.rotation.x = -Math.PI / 2; pool.position.set(0, 0.008, -D * 0.5); pool.renderOrder = 2; S.anim.add(pool); S.pool = pool;
    /* Spotlight cans on the header beam */
    for (const px of [-L * 0.28, L * 0.28]){
      const can = S.grp(px, 3.48, -D + 0.42, 0);
      const body = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.09, 0.2, 14), wm.black); body.rotation.x = 1.0; can.add(body);
      const lens = new THREE.Mesh(new THREE.CircleGeometry(0.075, 16), wm.glow); lens.position.set(0, -0.06, 0.09); lens.rotation.x = 1.0 - Math.PI / 2; can.add(lens);
    }
    /* Scene contents */
    sc.build(S);
    S.figs.forEach((f) => { waxSample(f, 0); waxApply(f, false, 0); });
    for (const fn of S.ticks) fn(0, 0, S);
    S.g.updateMatrixWorld(true); waxResolve(S);
    /* Clicking a figure opens the scene's card */
    S.figs.forEach((f) => { f.pick.userData.item = sc.item; pickItems.push(f.pick); });
    flushCanvases();
  });

  /* Dividers between side stages, with gilt edges */
  for (const sx of [-1, 1]){
    for (let k = 0; k <= 5; k++){
      const zc = k === 0 ? WH.first + 0.15 : WH.first - k * (WH.bay + WH.gap) + WH.gap / 2;
      addBox(WH.depth, 3.95, 0.3, divider, sx * (WH.x1 - WH.depth / 2), 1.975, zc);
      addBox(0.06, 3.95, 0.34, wm.brass, sx * (WH.x1 - WH.depth), 1.975, zc);
    }
  }
  addBox(0.3, 3.95, WH.depth - 0.2, divider, 0, 1.975, z0 + WH.depth / 2);
  addBox(0.34, 3.95, 0.06, wm.brass, 0, 1.975, z0 + WH.depth - 0.08);
  /* Track lights over the walkway and the lamps that light the hall */
  for (const sx of [-1, 1]) addBox(0.06, 0.06, WH.first - z0 - 2, wm.black, sx * 3.6, h - 0.35, (WH.first + z0) / 2 - 0.5);
  for (const zc of [-43.8, -48.1, -54.0, -59.9, -65.8, -71.7, -76.4]){
    const lp = new THREE.PointLight(0xffdcb2, 0.95, 19, 1.6); lp.position.set(0, h - 0.6, zc); scene.add(lp);
    const d = new THREE.Mesh(new THREE.CircleGeometry(0.2, 20), wm.glow); d.rotation.x = Math.PI / 2; d.position.set(0, h - 0.01, zc); scene.add(d);
  }
  /* Floor medallions number the scenes in order */
  WAX_SCENES.forEach((sc, i) => {
    const bay = WAX_BAYS[i], c = mk(256, 256), ctx = c.getContext('2d');
    ctx.fillStyle = '#b58f4c'; ctx.beginPath(); ctx.arc(128, 128, 122, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#2a171b'; ctx.beginPath(); ctx.arc(128, 128, 104, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#e3c27a'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.font = '700 96px ' + F.display; ctx.fillText(String(sc.n), 128, 120);
    ctx.font = '700 30px ' + F.type; ctx.fillText(sc.year, 128, 190);
    const md = new THREE.Mesh(new THREE.CircleGeometry(0.36, 32), new THREE.MeshStandardMaterial({ map:tex(c), roughness:0.35, metalness:0.3 }));
    md.rotation.x = -Math.PI / 2;
    if (bay.side === 'E') md.position.set(bay.x, 0.007, bay.z + 1.55);
    else md.position.set(Math.sign(bay.x) * 3.3, 0.007, bay.z + (bay.side === 'L' ? 1.9 : -1.9));
    scene.add(md);
  });
  /* Benches down the middle */
  for (const zc of [-56.95, -68.75]){
    const b = new THREE.Group(); b.position.set(0, 0, zc);
    addBox(0.5, 0.08, 2.2, stdMat(0x3a1d22, 0.7), 0, 0.46, 0, 0, b);
    for (const sz of [-0.9, 0.9]) addBox(0.42, 0.42, 0.08, wm.brass, 0, 0.21, sz, 0, b);
    scene.add(b); OBST.push({ x:0, z:zc, r:1.2 }); OBST.push({ x:0, z:zc - 0.6, r:0.6 }); OBST.push({ x:0, z:zc + 0.6, r:0.6 });
  }
}

/* The doorway at the end of Gallery 3 and the intro wall belong to the museum wing,
   so the view through the door always shows something even when the hall itself is hidden */
function buildWaxEntry(M){
  const wm = waxM();
  const intro = new THREE.Group(); intro.position.set(0, 0, -44.6);
  addBox(6.2, 3.6, 0.3, stdMat(0x2a1519, 0.85), 0, 1.8, 0, 0, intro);
  addPlane(5.4, 3.24, basicMat(drawWaxIntro()), 0, 1.86, 0.152, 0, intro);
  addPlane(5.4, 3.24, basicMat(drawWaxTimeline()), 0, 1.86, -0.152, Math.PI, intro);
  for (const s of [-1, 1]) addBox(0.06, 3.6, 0.34, wm.brass, s * 3.1, 1.8, 0, 0, intro);
  addBox(6.3, 0.06, 0.34, wm.brass, 0, 3.6, 0, 0, intro);
  scene.add(intro);
  const lp = new THREE.PointLight(0xffdcb2, 0.7, 14, 1.6); lp.position.set(0, 3.8, -43.4); scene.add(lp);
}

/* ---------- Every frame: wake the stage you're watching, freeze the rest ---------- */
const _wv3 = new THREE.Vector3();
function waxFrame(dt){
  if (!WING.wax || !WAX_SCENES.length) return false;
  /* The reenactors load once you head into the galleries (or a tour starts), well before the hall */
  if (!HK.want.wax && ((cam.z < -14 && Math.abs(cam.x) < 9) || tourIdx >= 0)) hkWant('wax');
  const inHall = WING.wax.visible && !ride.on && roomAt(cam.x, cam.z).id === 'wax';
  let busy = false, capSc = null, capD = Infinity;
  const fx = -Math.sin(cam.yaw), fz = -Math.cos(cam.yaw);
  for (const sc of WAX_SCENES){
    const S = sc.stage; if (!S) continue;
    const b = sc.bay, front = _wv3.set(0, 0, 1).applyAxisAngle(THREE.Object3D.DEFAULT_UP, b.ry);
    const ax = b.x + front.x * 1.2, az = b.z + front.z * 1.2, dx = b.x - cam.x, dz = b.z - cam.z, d = Math.hypot(ax - cam.x, az - cam.z);
    const want = inHall && d < (b.side === 'E' ? 8.5 : 6.6);
    const facing = (dx * fx + dz * fz) / Math.max(Math.hypot(dx, dz), 0.01);
    if (want) S.live = true;
    if (S.live || S.t > 0){
      /* Play to the end of the loop after you walk away, then rest on the first pose, still as wax */
      S.t += dt * (REDUCED ? 0.6 : 1);
      if (S.t >= sc.loop){ if (want) S.t -= sc.loop; else { S.t = 0; S.live = false; } }
      for (const f of S.figs){ f.lt = S.t; waxSample(f, S.t); waxApply(f, S.live, dt); }
      for (const fn of S.ticks) fn(S.t, dt, S);
      waxResolve(S);
      busy = true;
    }
    const g = S.live ? 1 : 0;
    if (Math.abs(S.glow - g) > 0.002){ S.glow = lerp(S.glow, g, 1 - Math.exp(-dt * 3)); busy = true; } else S.glow = g;
    if (S.pool) S.pool.material.opacity = 0.12 + 0.26 * S.glow;
    if (S.backdrop) S.backdrop.material.emissiveIntensity = 0.1 + 0.12 * S.glow;
    if (want && facing > 0.3 && d < capD){ capD = d; capSc = sc; }
  }
  if (capSc){ capSc.watch = (capSc.watch || 0) + dt; if (capSc.watch > 5 && !prog.wax.has(capSc.id)){ prog.wax.add(capSc.id); saveProg(); if (prog.wax.size >= 6) award('historian'); } }
  waxCaption(capSc);
  return busy;
}
/* Narration under the scene you're facing */
const waxCapEl = { el:null, sc:null, line:-1 };
function waxCaption(sc){
  if (!waxCapEl.el) waxCapEl.el = document.getElementById('waxCap');
  const el = waxCapEl.el; if (!el) return;
  if (!sc){ if (waxCapEl.sc){ el.classList.remove('on'); document.body.classList.remove('waxcap-on'); waxCapEl.sc = null; waxCapEl.line = -1; } return; }
  let li = 0; for (let i = 0; i < sc.lines.length; i++) if (sc.stage.t >= sc.lines[i][0]) li = i;
  if (waxCapEl.sc !== sc || waxCapEl.line !== li){
    waxCapEl.sc = sc; waxCapEl.line = li;
    el.querySelector('.wk').textContent = sc.year + ' · Scene ' + sc.n + ' of 12';
    el.querySelector('.wt').textContent = sc.lines[li][1];
    el.hidden = false; el.classList.add('on'); document.body.classList.add('waxcap-on');
  }
}
/* Where to stand to watch a scene */
function waxView(sc){
  const b = sc.bay, front = new THREE.Vector3(0, 0, 1).applyAxisAngle(THREE.Object3D.DEFAULT_UP, b.ry);
  if (b.side === 'E'){ const x = b.x * 0.62, z = b.z + 3.4; return { x, z, yaw:Math.atan2(x - b.x, z - (b.z - 1.6)), pitch:-0.04 }; }
  const d = 4.6, x = b.x + front.x * d, z = b.z + front.z * d;
  return { x, z, yaw:Math.atan2(front.x, front.z), pitch:-0.04 };
}

/* Each scene is also a catalog card, like the exhibits */
WAX_SCENES.forEach((sc) => {
  Object.assign(sc.item, { id:sc.id, kind:'reenactment', hall:'The Wax Hall · Scene ' + sc.n + ' of 12', scene:sc, year:parseInt(String(sc.year).replace(/\D/g, ''), 10) || null });
  WAX_ITEMS.push(sc.item);
});
function itemWhere(it){ return it.scene ? 'Wax Hall · Scene ' + it.scene.n : it.g ? 'Gallery ' + it.g : 'Library'; }
/* The card picture: the scene's painted backdrop with its year and title */
function drawWaxCard(sc){
  const W = 1000, H = 700, c = mk(W, H), ctx = c.getContext('2d');
  ctx.drawImage(waxBackdrop(sc.backdrop, 5.6), 0, 0, W, H);
  const g = ctx.createLinearGradient(0, H * 0.45, 0, H); g.addColorStop(0, 'rgba(20,10,12,0)'); g.addColorStop(1, 'rgba(20,10,12,0.92)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = 'rgba(205,169,97,0.9)'; ctx.lineWidth = 6; ctx.strokeRect(14, 14, W - 28, H - 28);
  ctx.textAlign = 'left'; ctx.fillStyle = '#d9b56c'; ctx.font = '700 28px ' + F.type; ctx.fillText('LIVING HISTORY · SCENE ' + sc.n + ' OF 12', 54, H - 190);
  ctx.fillStyle = '#efe7d5'; ctx.font = '700 96px ' + F.display; ctx.fillText(sc.year, 50, H - 96);
  ctx.font = '400 46px ' + F.display; fit(ctx, sc.title, F.display, '400', 46, W - 100); ctx.fillText(sc.title, 54, H - 46);
  return c;
}
function drawWaxDoorSign(){
  const [c, ctx] = signBase(1400, 240);
  ctx.fillStyle = BRASS; ctx.font = '400 30px ' + F.type; ctx.textAlign = 'left'; ctx.fillText('LIVING HISTORY', 60, 132);
  ctx.textAlign = 'right'; ctx.fillStyle = '#a9b8ae'; ctx.font = '400 26px ' + F.type; ctx.fillText('2016 TO 2025', 1340, 132);
  ctx.textAlign = 'center'; ctx.fillStyle = CREAM; fit(ctx, 'The Wax Hall', F.display, '400', 78, 700); ctx.fillText('The Wax Hall', 700, 148);
  return c;
}
function drawWaxTeaser(){
  const W = 900, H = 900, c = mk(W, H), ctx = c.getContext('2d');
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#3a1c24'); g.addColorStop(1, '#1d1013');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = 'rgba(205,169,97,0.85)'; ctx.lineWidth = 6; ctx.strokeRect(20, 20, W - 40, H - 40);
  ctx.textAlign = 'center'; ctx.fillStyle = '#cda961'; ctx.font = '700 34px ' + F.type; ctx.fillText('NEXT · THROUGH THIS DOOR', W / 2, 120);
  ctx.fillStyle = '#efe7d5'; ctx.font = '400 96px ' + F.display; ctx.fillText('Living', W / 2, 270); ctx.fillText('History', W / 2, 370);
  ctx.fillStyle = 'rgba(239,231,213,0.85)'; ctx.font = '400 38px ' + F.ui;
  ['Wax figures act out', 'XRLibraries’ story,', 'from 2016 to today.'].forEach((l, i) => ctx.fillText(l, W / 2, 480 + i * 54));
  ctx.fillStyle = '#d9b56c'; ctx.font = '700 120px ' + F.display; ctx.fillText('←', W / 2, 780);
  return c;
}

/* Compile the figure shaders while the welcome card is up, so the first look into the hall does not stutter */
function waxWarm(){
  if (!renderer || !renderer.compile || !WING.wax) return;
  const prev = renderer.getRenderTarget(), env = scene.environment;
  try {
    renderer.setRenderTarget(GFX.composer ? GFX.composer.renderTarget1 : null);
    if (!env && GFX.envIn) scene.environment = GFX.envIn;
    /* compileAsync only helps (and only stays quiet) where shaders can compile in parallel */
    const par = renderer.extensions && renderer.extensions.has('KHR_parallel_shader_compile');
    if (par) renderer.compileAsync(WING.wax, camera, scene).catch(() => {}); else renderer.compile(WING.wax, camera, scene);
  }
  catch (err) { console.warn(err); }
  finally { scene.environment = env; renderer.setRenderTarget(prev); }
}
