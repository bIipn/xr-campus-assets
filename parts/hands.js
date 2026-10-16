/* ================================================================
   Hands-on stations. At a bench you see your own arms: they reach out,
   pick things up, pour, press buttons and set things down. A clip moves
   the equipment along smooth paths and your hands follow it by IK onto
   grips (where each palm touches a thing). Fingers open on the way in and
   close on contact, and you lean in and turn toward what you work on.
   ================================================================ */
const HANDS = { fig:null, S:1, eyeF:0.09, yaw:0, twist:0, sp:0, ph:0, pp:null, dense:new Float32Array(WAX_N), lean:0, cx:false, e0:null,
  clip:null, t:0, h:{}, look:-1e9, reach:0.6, sh:null, piv:null, eyeL:null, spot:null, fpt:null };
const _hdv = new THREE.Vector3(), _hv2 = new THREE.Vector3(), _hv3 = new THREE.Vector3(), _hv4 = new THREE.Vector3(), _hv5 = new THREE.Vector3();
const _hdq = new THREE.Quaternion(), _hq2 = new THREE.Quaternion(), _hm = new THREE.Matrix4(), _hm2 = new THREE.Matrix4(), _hs = new THREE.Vector3(), _he = new THREE.Euler(), _hone = new THREE.Vector3(1, 1, 1);
const hsm = (u) => { u = clamp(u, 0, 1); return u * u * u * (u * (u * 6 - 15) + 10); };
const H_SIDES = ['L', 'R'];

/* Your body for the stations: the same person you are in the yard, head hidden because the camera is in it */
function handsBuild(){
  if (HANDS.fig) return HANDS.fig;
  const RB = hkRig('sm04'), S = EYE / RB.eyeMid.y, P = RB.P;
  const f = makeHuman({ av:'sm04', scale:S, lazy:'hands', noAO:true });
  f.onMesh.push((mesh) => {
    mesh.material = mesh.material.map((m) => { if (!(m.isMeshPhysicalMaterial || m.alphaTest > 0)) return m; const c = m.clone(); c.colorWrite = false; c.depthWrite = false; return c; });
  });
  f.root.userData.noMerge = true; f.root.visible = false; scene.add(f.root);
  HANDS.fig = f; HANDS.S = S; HANDS.eyeF = RB.eyeMid.z * S;
  const ua = P[HB.L_UpperArm], fa = P[HB.L_Forearm], hd = P[HB.L_Hand];
  HANDS.reach = (ua.distanceTo(fa) + fa.distanceTo(hd) + 0.055) * S;
  HANDS.piv = P[HB.Spine].clone().multiplyScalar(S);
  HANDS.sh = { L:ua.clone().multiplyScalar(S), R:P[HB.R_UpperArm].clone().multiplyScalar(S) };
  HANDS.eyeL = RB.eyeMid.clone().sub(P[HB.Head]).multiplyScalar(S);
  for (const s of H_SIDES) HANDS.h[s] = { w:0, pos:new THREE.Vector3(), quat:new THREE.Quaternion(), curl:0.12, point:0, seg:null, prev:null, tp:new THREE.Vector3(), tpOn:false,
    fp:new THREE.Vector3(), fq:new THREE.Quaternion(), fw:0, fc:0.12, fpt:0 };
  return f;
}

/* ---------- Writing a clip: equipment moves, hands go to grips, events fire on time ---------- */
/* spot: where you stand { x, z, yaw, pitch, bench } (camera yaw/pitch, bench = height of the bench top) */
function hClip(spot){ return { t:0, T:0, spot, obj:[], L:[], R:[], ev:[], ei:0, fx:[], anim:[], rate:1 }; }
function hEnd(C, d){ C.T = Math.max(C.T, C.t + (d || 0)); return C; }
function hNext(C, d, keep){ hEnd(C, d); if (!keep) C.t += d; return C; }
/* One hand goes to a target: { o, g, off } (a grip on a thing, off(t) shifts it in the thing's frame), { p, q }, or { fn(t, pos, quat) } */
function hTo(C, s, tgt, d, opt){ C[s].push(Object.assign({ t0:C.t, t1:C.t + d, tgt }, opt)); return hNext(C, d, opt && opt.keep); }
/* Both hands (or the ones named in grips) take hold of a thing */
function hGrab(C, o, grips, d, opt){ for (const s in grips) C[s].push(Object.assign({ t0:C.t, t1:C.t + d, tgt:{ o, g:grips[s], off:opt && opt.off } }, opt)); return hNext(C, d, opt && opt.keep); }
/* Let go and bring the hands back down */
function hRest(C, sides, d, opt){ for (const s of sides) C[s].push({ t0:C.t, t1:C.t + d, tgt:null }); return hNext(C, d, opt && opt.keep); }
/* A thing moves to { parent, p, r (degrees) | q } over d seconds, with an optional lift arc; it ends up a child of parent */
function hMove(C, o, to, d, opt){ C.obj.push(Object.assign({ o, t0:C.t, t1:C.t + d, to }, opt)); return hNext(C, d, opt && opt.keep); }
function hWait(C, d){ C.t += d; return hEnd(C, 0); }
function hAt(C, fn){ C.ev.push({ t:C.t, fn }); return C; }
/* Walk to another spot partway through a clip (whatever your hands hold should ride on your body meanwhile) */
function hWalk(C, spot){ return hAt(C, () => { HANDS.spot = spot; C.spot = spot; goView(spot); C.waitArrive = true; }); }
/* A callback every frame for d seconds, with u running 0..1 (it always gets its u = 1 call) */
function hAnim(C, d, fn){ C.anim.push({ t0:C.t, t1:C.t + d, fn }); return hEnd(C, d); }
/* A stream of grains from fn() (a world point, re-read every frame) falling to height y0 */
function hStream(C, fn, y0, d, opt){ C.fx.push(Object.assign({ t0:C.t, t1:C.t + d, fn, y0, acc:0 }, opt)); return hNext(C, d, opt && opt.keep); }
/* Body-relative frames for carrying things while you walk */
function hBody(p, r){ return { body:true, p, r }; }

function handsPlay(C, done){
  if (!THREEOK) { if (done) done(); return; }
  if (HANDS.clip) handsFinish();
  handsBuild();
  C.done = done; HANDS.clip = C; HANDS.t = 0;
  if (C.spot){ HANDS.spot = C.spot; if (Math.hypot(cam.x - C.spot.x, cam.z - C.spot.z) > 0.25 || path.length){ goView(C.spot); C.waitArrive = true; } }
  for (const e of C.ev) if (e.t > C.T) C.T = e.t;
  C.ev.sort((a, b) => a.t - b.t);
  wake();
}
function handsBusy(){ return !!HANDS.clip; }
function handsDone(){ const C = HANDS.clip; if (!C) return; HANDS.clip = null; HANDS.t = 0; if (C.done) C.done(); wake(); }
/* Skip to the end of the clip: everything lands where it was going */
function handsFinish(){
  const C = HANDS.clip; if (!C) return;
  HANDS.t = C.T + 1; HANDS.dt = 0; handsClipTick();
  for (const s of H_SIDES){ const H = HANDS.h[s]; if (H){ H.w = 0; H.seg = null; H.curl = 0.12; H.point = 0; H.tpOn = false; } }
  if (HANDS.clip === C) handsDone();
}

/* ---------- Playing a clip ---------- */
function handsFrameOf(to, out){
  let P = to.parent || scene;
  if (to.body) P = HANDS.fig.all[HB.Spine2];
  P.updateWorldMatrix(true, false);
  if (!to.lq){ to.lq = to.q ? to.q.clone() : new THREE.Quaternion().setFromEuler(_he.set((to.r ? to.r[0] : 0) * D2R, (to.r ? to.r[1] : 0) * D2R, (to.r ? to.r[2] : 0) * D2R)); to.lp = new THREE.Vector3().fromArray(to.p); }
  return out.compose(to.lp, to.lq, _hone).premultiply(P.matrixWorld);
}
function handsObj(m, t){
  const o = m.o, to = m.to;
  if (!m.go){ m.go = true; o.updateWorldMatrix(true, false); scene.attach(o); m.fp = o.position.clone(); m.fq = o.quaternion.clone(); if (m.start) m.start(); }
  handsFrameOf(to, _hm).decompose(_hdv, _hdq, _hs);
  const u = clamp((t - m.t0) / Math.max(1e-3, m.t1 - m.t0), 0, 1), k = m.lin ? u : hsm(u);
  o.position.lerpVectors(m.fp, _hdv, k); if (m.lift) o.position.y += m.lift * Math.sin(Math.PI * k);
  o.quaternion.slerpQuaternions(m.fq, _hdq, k);
  if (u >= 1 && !m.done){
    m.done = true;
    const P = to.body ? HANDS.fig.all[HB.Spine2] : (to.parent || scene); P.attach(o); o.position.copy(to.lp); o.quaternion.copy(to.lq);
    if (m.end) m.end();
  }
  o.updateMatrixWorld(true);
}
function handsClipTick(){
  const C = HANDS.clip; if (!C) return;
  const t = HANDS.t;
  while (C.ei < C.ev.length && C.ev[C.ei].t <= t) C.ev[C.ei++].fn();
  if (HANDS.clip !== C) return;
  for (const m of C.obj) if (!m.done && t >= m.t0) handsObj(m, t);
  for (const a of C.anim) if (!a.fired && t >= a.t0){ const u = clamp((t - a.t0) / Math.max(1e-3, a.t1 - a.t0), 0, 1); a.fn(u, t); if (u >= 1) a.fired = true; }
  for (const x of C.fx) if (t >= x.t0 && t < x.t1) handsSpawn(x, t);
  if (t >= C.T) handsDone();
}
/* Where a target puts the palm right now */
function handsTgt(T, t, pos, quat){
  if (T.fn){ T.fn(t, pos, quat); return; }
  if (T.o){
    T.o.updateWorldMatrix(true, false);
    let M = T.o.matrixWorld;
    if (T.off){ const v = T.off(t); M = _hm2.multiplyMatrices(M, _hm.makeTranslation(v[0], v[1], v[2])); }
    _hm.multiplyMatrices(M, gripMatrix(T.g)).decompose(pos, quat, _hs);
    return;
  }
  pos.copy(T.p); quat.copy(T.q);
}
function handsHand(s, t, dt){
  const H = HANDS.h[s], C = HANDS.clip, f = HANDS.fig;
  let g = null;
  if (C) for (const x of C[s]){ if (x.t0 <= t) g = x; else break; }
  if (g !== H.seg){
    if (H.w < 0.02) hkPalmWorld(f, s, H.fp, H.fq); else { H.fp.copy(H.pos); H.fq.copy(H.quat); }
    H.fw = H.w; H.fc = H.curl; H.fpt = H.point; H.seg = g;
  }
  if (!g){ H.w = Math.max(0, H.w - dt * 2.5); H.curl = lerp(H.curl, 0.12, 1 - Math.exp(-dt * 6)); H.point = Math.max(0, H.point - dt * 3); H.tpOn = false; return; }
  const u = clamp((t - g.t0) / Math.max(1e-3, g.t1 - g.t0), 0, 1), k = hsm(u);
  if (g.tgt){
    handsTgt(g.tgt, t, _hdv, _hdq); H.tp.copy(_hdv); H.tpOn = true;
    H.pos.lerpVectors(H.fp, _hdv, k); H.quat.slerpQuaternions(H.fq, _hdq, k);
    if (g.arc) H.pos.y += g.arc * Math.sin(Math.PI * k);
    H.w = lerp(H.fw, 1, k);
    const G = g.tgt.g || g.tgt, c1 = G.curl == null ? 0.3 : G.curl, p1 = G.point || 0, op = Math.min(H.fc, p1 > 0 ? 0.45 : -0.2);
    H.curl = g.keepHand ? lerp(H.fc, c1, k) : u < 0.55 ? lerp(H.fc, op, hsm(u / 0.55)) : lerp(op, c1, hsm((u - 0.55) / 0.45));
    H.point = lerp(H.fpt, p1, hsm(u * 1.4));
  } else {
    /* Letting go: the hand drifts down and back toward you while the arm settles */
    _hv2.set(0, 0, -1).applyQuaternion(f.root.quaternion);
    H.pos.copy(H.fp).addScaledVector(_hv2, 0.14 * k); H.pos.y -= 0.12 * k; H.quat.copy(H.fq);
    H.w = H.fw * (1 - k);
    H.curl = lerp(H.fc, 0.12, hsm(u * 2)); H.point = lerp(H.fpt, 0, hsm(u * 2)); H.tpOn = false;
  }
}
/* How far forward you must bend (degrees) and crouch (0..1) to reach p with hand s */
function handsLeanFor(s, p, out){
  const f = HANDS.fig, q = f.root.worldToLocal(_hv2.copy(p));
  const piv = HANDS.piv, sh = HANDS.sh[s], dy = sh.y - piv.y, dz = sh.z - piv.z, R = HANDS.reach * 0.97;
  /* You only crouch for things that are low; for the rest you lean, and the arm stretches the last few centimetres */
  const crMax = p.y < 0.78 ? 1 : 0;
  for (let cr = 0; cr <= crMax + 0.001; cr += 0.1){
    for (let deg = 0; deg <= 40; deg += 2){
      const a = deg * D2R, c = Math.cos(a), n = Math.sin(a), py = piv.y - 0.26 * cr, pz = piv.z + 0.06 * cr;
      if (Math.hypot(q.x - sh.x, q.y - (py + dy * c - dz * n), q.z - (pz + dy * n + dz * c)) <= R){ out.lean = deg; out.crouch = cr; return out; }
    }
  }
  out.lean = 40; out.crouch = crMax; return out;
}
const _hneed = { lean:0, crouch:0 }, _hneed2 = { lean:0, crouch:0 };

/* ---------- Grains: sand pouring from a pan or a sieve ---------- */
const HGR = { pts:null, n:220, p:null, v:null, y0:null, live:null, i:0, on:0 };
function handsGrains(){
  if (HGR.pts) return HGR.pts;
  const g = new THREE.BufferGeometry(), n = HGR.n;
  HGR.p = new Float32Array(n * 3); HGR.v = new Float32Array(n * 3); HGR.y0 = new Float32Array(n); HGR.live = new Uint8Array(n);
  for (let i = 0; i < n; i++) HGR.p[i * 3 + 1] = -99;
  g.setAttribute('position', new THREE.BufferAttribute(HGR.p, 3));
  const c = mk(32, 32), x = c.getContext('2d'), gr = x.createRadialGradient(16, 16, 2, 16, 16, 15); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); x.fillStyle = gr; x.fillRect(0, 0, 32, 32);
  const m = new THREE.PointsMaterial({ color:srgb(0xe8d6a0), size:0.011, map:tex(c), transparent:true, alphaTest:0.3, depthWrite:false });
  HGR.pts = new THREE.Points(g, m); HGR.pts.frustumCulled = false; HGR.pts.userData.noMerge = true; scene.add(HGR.pts);
  return HGR.pts;
}
function handsSpawn(x, t){
  handsGrains();
  x.acc += (x.rate || 160) * HANDS.dt * (x.amt ? x.amt(t) : 1);
  const p = x.fn(t, _hdv), sp = x.spread || 0.02;
  while (x.acc >= 1){
    x.acc -= 1; const i = HGR.i = (HGR.i + 1) % HGR.n;
    HGR.p[i * 3] = p.x + (Math.random() - 0.5) * sp; HGR.p[i * 3 + 1] = p.y; HGR.p[i * 3 + 2] = p.z + (Math.random() - 0.5) * sp * (x.sz == null ? 1 : x.sz);
    HGR.v[i * 3] = (x.vx || 0) + (Math.random() - 0.5) * 0.05; HGR.v[i * 3 + 1] = -0.1 - Math.random() * 0.15; HGR.v[i * 3 + 2] = (x.vz || 0) + (Math.random() - 0.5) * 0.05;
    HGR.y0[i] = x.y0; HGR.live[i] = 1; HGR.on++;
  }
}
function handsGrainsTick(dt){
  if (!HGR.pts || !HGR.on) return false;
  let any = 0;
  for (let i = 0; i < HGR.n; i++){
    if (!HGR.live[i]) continue;
    const j = i * 3; HGR.v[j + 1] -= 9.8 * dt;
    HGR.p[j] += HGR.v[j] * dt; HGR.p[j + 1] += HGR.v[j + 1] * dt; HGR.p[j + 2] += HGR.v[j + 2] * dt;
    if (HGR.p[j + 1] <= HGR.y0[i]){ HGR.live[i] = 0; HGR.p[j + 1] = -99; } else any++;
  }
  HGR.on = any;
  HGR.pts.geometry.attributes.position.needsUpdate = true;
  return any > 0;
}

/* ---------- Every frame ---------- */
function handsFrame(dt){
  if (window.__noHands) return false;
  const St = STN.cur, want = !!(St && St.hands && !ride.on && !paint.on && roomAt(cam.x, cam.z).id === St.room);
  /* Your body loads as soon as you're in the school, so it's ready before you reach a bench */
  if (!HK.want.hands && !HANDS.fig){ const r = roomAt(cam.x, cam.z).id; if (want || r === 'school' || r === 'lab' || r === 'blueprint' || r === 'studio' || r === 'world'){ handsBuild(); hkWant('hands'); } }
  if (want && !HANDS.fig) handsBuild();
  const f = HANDS.fig; if (!f) return false;
  if (want) hkWant('hands');
  let busy = handsGrainsTick(dt);
  const C = HANDS.clip;
  if (C){
    busy = true;
    const away = C.spot && HANDS.spot && !path.length && Math.hypot(cam.x - HANDS.spot.x, cam.z - HANDS.spot.z) > 0.8;
    if (!want || away || REDUCED){ handsFinish(); }
    else if (C.waitArrive){ if (!path.length && Math.hypot(cam.x - C.spot.x, cam.z - C.spot.z) < 0.3){ C.waitArrive = false; } }
    else { HANDS.dt = dt * (C.rate || 1); HANDS.t += HANDS.dt; handsClipTick(); }
  }
  const show = want && !!f.mesh && !window.__noBody;
  if (f.root.visible !== show){ f.root.visible = show; if (show){ HANDS.yaw = cam.yaw + Math.PI; HANDS.twist = 0; HANDS.pp = null; HANDS.lean = 0; HANDS.crouch = 0; HANDS.e0 = null; } }
  if (ptr && ptr.moved) HANDS.look = performance.now();
  if (!show){
    /* Not drawn yet (still loading, or you're away): keep the body where you are so anything carried on it stays with you */
    const yw = cam.yaw + Math.PI, sy0 = Math.sin(yw), cy0 = Math.cos(yw);
    f.root.position.set(cam.x - sy0 * HANDS.eyeF, PLAYER.y, cam.z - cy0 * HANDS.eyeF); f.root.rotation.set(0, yw, 0); f.root.updateMatrixWorld(true);
    if (HANDS.cx){ CAMX.x = CAMX.y = CAMX.z = 0; HANDS.cx = false; }
    return busy;
  }
  /* Walking, turning toward your work */
  if (HANDS.pp && dt > 0){ const v = Math.hypot(cam.x - HANDS.pp.x, cam.z - HANDS.pp.z) / dt; HANDS.sp = lerp(HANDS.sp, Math.min(v, 5), 1 - Math.exp(-dt * 8)); }
  HANDS.pp = { x:cam.x, z:cam.z };
  const spot = HANDS.spot && HANDS.clip ? HANDS.spot : St.spot ? St.spot() : null;
  const near = spot && Math.hypot(cam.x - spot.x, cam.z - spot.z) < 0.3;
  let tw = 0;
  if (near && HANDS.clip){
    let sx = 0, sz = 0, n = 0;
    for (const s of H_SIDES){ const H = HANDS.h[s]; if (H.tpOn){ sx += H.tp.x; sz += H.tp.z; n++; } }
    if (n){ const fy = spot.yaw + Math.PI, dx = sx / n - cam.x, dz = sz / n - cam.z; tw = clamp(angDiff(fy, Math.atan2(dx, dz)) * 0.75, -0.55, 0.55); }
  }
  HANDS.twist = lerp(HANDS.twist, tw, 1 - Math.exp(-dt * 3.5));
  const base = near ? spot.yaw + Math.PI : HANDS.sp > 0.25 ? cam.yaw + Math.PI : HANDS.yaw - HANDS.twist;
  HANDS.yaw = lerpAngle(HANDS.yaw, base + HANDS.twist, 1 - Math.exp(-dt * 7));
  if (HANDS.sp > 0.05) busy = true;
  /* Pose: standing or walking, bent forward as far as the reach needs */
  const o = HANDS.dense, S = HANDS.S; o.set(spD(BSPEC, 'stand', 1));
  const amp = clamp(HANDS.sp / 1.8, 0, 1);
  if (amp > 0.03){ HANDS.ph += dt * Math.PI * clamp(1.7 + 0.34 * HANDS.sp, 1.7, 3.6); spGait(o, HANDS.ph, amp, 0); }
  if (HANDS.lean > 0.05) spAdd(o, { spine:[HANDS.lean * 0.6, 0, 0], chest:[HANDS.lean * 0.4, 0, 0], head:[-HANDS.lean * 0.35, 0, 0], legL:[HANDS.lean * 0.12, 0, 0], legR:[HANDS.lean * 0.12, 0, 0] }, 1);
  if (HANDS.crouch > 0.01) spAdd(o, { legL:[44, 2, 0], legR:[44, 2, 0], knL:60, knR:60, footL:-14, footR:-14, spine:[6, 0, 0], dy:-0.24 }, HANDS.crouch);
  hkPose(f, o);
  const sy = Math.sin(HANDS.yaw), cy = Math.cos(HANDS.yaw);
  f.root.position.set(cam.x - sy * HANDS.eyeF, PLAYER.y + o[WR + 3] * S, cam.z - cy * HANDS.eyeF);
  f.root.rotation.set(0, HANDS.yaw, 0);
  f.root.updateMatrixWorld(true);
  /* Hands */
  for (const s of H_SIDES) handsHand(s, HANDS.t, dt);
  for (const s of H_SIDES){ const H = HANDS.h[s]; if (H.w > 0.002) hkArmIK(f, s, H.pos, H.quat, hkPole(f, s, 0.8, _hv3), H.w); }
  hkFingers(f, HANDS.h.L.curl, HANDS.h.R.curl, HANDS.h.L.point, HANDS.h.R.point);
  let need = 0, needC = 0;
  for (const s of H_SIDES){ const H = HANDS.h[s]; if (H.tpOn && H.w > 0.05){ handsLeanFor(s, H.tp, _hneed); const k = Math.min(1, H.w * 1.6); need = Math.max(need, _hneed.lean * k); needC = Math.max(needC, _hneed.crouch * k); } }
  HANDS.lean = lerp(HANDS.lean, need, 1 - Math.exp(-dt * 4.5));
  HANDS.crouch = lerp(HANDS.crouch || 0, needC, 1 - Math.exp(-dt * 4));
  if (HANDS.lean > 0.05 || need > 0 || HANDS.crouch > 0.01 || needC > 0) busy = true;
  /* The camera rides with your head as you lean in */
  const head = f.all[HB.Head], eL = f.root.worldToLocal(_hdv.copy(HANDS.eyeL).applyMatrix4(head.matrixWorld));
  if (HANDS.lean < 0.25 && HANDS.crouch < 0.01 && amp < 0.05) HANDS.e0 = (HANDS.e0 || new THREE.Vector3()).copy(eL);
  if (HANDS.e0 && (HANDS.lean >= 0.25 || HANDS.crouch >= 0.01)){
    const d = eL.sub(HANDS.e0).applyQuaternion(f.root.quaternion);
    CAMX.x = d.x; CAMX.y = d.y; CAMX.z = d.z; HANDS.cx = true;
  } else if (HANDS.cx){ CAMX.x = CAMX.y = CAMX.z = 0; HANDS.cx = false; }
  /* Keep what your hands are doing in view, unless you're looking around yourself */
  if (HANDS.clip && near && faceYaw == null && facePitch == null && performance.now() - HANDS.look > 2500){
    let sx = 0, sy2 = 0, sz = 0, n = 0;
    for (const s of H_SIDES){ const H = HANDS.h[s]; if (H.tpOn && H.w > 0.3){ sx += H.tp.x; sy2 += H.tp.y; sz += H.tp.z; n++; } }
    if (HANDS.clip.focus){ const p = HANDS.clip.focus(HANDS.t, _hv2); if (p){ sx += p.x * 2; sy2 += p.y * 2; sz += p.z * 2; n += 2; } }
    if (n){
      const ex = cam.x + CAMX.x, ey = eyeY() + CAMX.y, ez = cam.z + CAMX.z;
      const tx = sx / n, ty = sy2 / n, tz = sz / n;
      HANDS.fpt = HANDS.fpt || new THREE.Vector3(tx, ty, tz); HANDS.fpt.lerp(_hv2.set(tx, ty, tz), 1 - Math.exp(-dt * 3));
      const dx = HANDS.fpt.x - ex, dy = HANDS.fpt.y - ey, dz = HANDS.fpt.z - ez, hd = Math.hypot(dx, dz);
      const wy = Math.atan2(-dx, -dz), wp = Math.atan2(dy, hd), k = 1 - Math.exp(-dt * 2.4);
      const eyw = angDiff(cam.yaw, wy), ep = wp - cam.pitch, zy = 0.2, zp = 0.14;
      if (Math.abs(eyw) > zy) cam.yaw += (eyw - Math.sign(eyw) * zy) * k;
      if (Math.abs(ep) > zp) cam.pitch = clamp(cam.pitch + (ep - Math.sign(ep) * zp) * k, -1.05, 0.6);
    }
  } else HANDS.fpt = null;
  camera.position.set(cam.x + CAMX.x, eyeY() + CAMX.y, cam.z + CAMX.z); camera.rotation.set(cam.pitch, cam.yaw, 0);
  return busy;
}
