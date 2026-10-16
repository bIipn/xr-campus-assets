/* ================================================================
   Playing soccer. Hold to power up and look where you want the ball
   to go; on release your body runs up, plants and strikes it with the
   laces. A goalkeeper reads the shot after a human reaction time and
   dives, catches or tips it away, then rolls the ball back to you.
   ================================================================ */
const KICK = { st:'', t0:0, src:'', ball:null, ptr:null, plan:null, t:0, drive:false, trackOn:false };
const BODY = { fig:null, yaw:0, ph:0, sp:0, touch:0, touchS:1, dense:new Float32Array(WAX_N), contact:null, eyeF:0.09, S:1, lean:0 };
const KEEP = { fig:null, st:'ready', t:0, pos:{ x:GOAL.x - 0.45, z:GOAL.z }, v:{ x:0, z:0 }, com:new THREE.Vector3(GOAL.x - 0.45, 0.8, GOAL.z), prev:new THREE.Vector3(), vel:new THREE.Vector3(),
  yaw:-Math.PI / 2, roll:0, dense:new Float32Array(WAX_N), caps:[], plan:null, hold:false, react:-1, guess:0, guessAt:-1, setAt:-1, ph:0, way:[], after:'', blinkT:2, idle:0, drawn:false, near:false };
const KEEP_HOME = { x:GOAL.x - 0.45, z:GOAL.z };
const _kv = new THREE.Vector3(), _kq = new THREE.Quaternion(), _kq2 = new THREE.Quaternion(), _kc = new THREE.Vector3(), _kd = new THREE.Vector3(), _ke = new THREE.Vector3();
const AX_Y = new THREE.Vector3(0, 1, 0), AX_Z = new THREE.Vector3(0, 0, 1);
function gauss(){ let u = 0, v = 0; while (!u) u = Math.random(); while (!v) v = Math.random(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }

/* ---------- The people: your body (seen when you look down, and as your shadow) and the keeper ---------- */
function socBuildPeople(){
  const RB = hkRig('sm04'), S = EYE / RB.eyeMid.y;
  const f = makeHuman({ av:'sm04', scale:S, lazy:'yard', shadow:true, noAO:true });
  /* The camera sits inside the head: the head and hair draw nothing for you, but still cast your shadow */
  f.onMesh.push((mesh) => {
    mesh.material = mesh.material.map((m) => { if (!(m.isMeshPhysicalMaterial || m.alphaTest > 0)) return m; const c = m.clone(); c.colorWrite = false; c.depthWrite = false; return c; });
  });
  f.root.userData.noMerge = true; f.root.visible = false;
  BODY.fig = f; BODY.S = S; BODY.eyeF = RB.eyeMid.z * S;
  /* Where the laces meet the ball in the strike pose, measured on the real skeleton */
  const d = spD(BSPEC, 'contact', 1); hkPose(f, d); f.root.position.set(0, d[WR + 3] * S, 0); f.root.updateMatrixWorld(true);
  const a = new THREE.Vector3(), t = new THREE.Vector3(); f.all[HB.R_Foot].getWorldPosition(a); f.all[HB.R_Toe0].getWorldPosition(t);
  const dir = t.clone().sub(a), len = dir.length(); dir.normalize();
  const dors = new THREE.Vector3(0, dir.z, -dir.y).normalize(); if (dors.z < 0) dors.negate();
  BODY.contact = a.clone().addScaledVector(dir, len * 0.5).addScaledVector(dors, 0.032 * S);
  hkPose(f, spD(BSPEC, 'stand', 1)); hkFingers(f, 0.1, 0.1, 0, 0);
  scene.add(f.root);

  /* The keeper: a lime kit, big gloves */
  const K = makeHuman({ av:'sm02', scale:1, lazy:'yard', shadow:true, dye:[0, 0, 0.5, 1, 1, null, [74, 0.9, 0.24, 0.72]] });
  K.root.userData.noMerge = true; K.pick.userData.keeper = true; pickItems.push(K.pick);
  /* Gloves: every vertex the hand and finger bones move is painted as a padded glove, so it fits each
     finger; the hands are a touch bigger, as gloved hands are */
  for (const s of ['L', 'R']) K.all[HB[s + '_Hand']].scale.setScalar(1.12);
  K.onMesh.push((mesh) => {
    const g = mesh.geometry;
    if (!g.attributes.aGlove){
      const si = g.attributes.skinIndex, sw = g.attributes.skinWeight, n = si.count, out = new Float32Array(n);
      const isHand = HK_RIG.names.map((nm) => /_(Hand|Finger\d+)$/.test(nm) ? 1 : 0);
      for (let i = 0; i < n; i++) out[i] = sw.getX(i) * isHand[si.getX(i)] + sw.getY(i) * isHand[si.getY(i)] + sw.getZ(i) * isHand[si.getZ(i)] + sw.getW(i) * isHand[si.getW(i)];
      g.setAttribute('aGlove', new THREE.BufferAttribute(out, 1));
    }
    mesh.material = mesh.material.map((m) => {
      if (!('dye' in m.userData)) return m;
      const c = m.clone(); hkClothPatch(c, m.userData.dye);
      const base = c.onBeforeCompile;
      c.onBeforeCompile = (sh, r) => {
        base(sh, r);
        sh.vertexShader = 'attribute float aGlove;\nvarying float vGlove;\n' + sh.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\nvGlove = aGlove;');
        sh.fragmentShader = 'varying float vGlove;\n' + sh.fragmentShader.replace('#include <color_fragment>', '#include <color_fragment>\n' +
          'float gk = smoothstep(0.42, 0.7, vGlove); if (gk > 0.0){ float cuff = 1.0 - smoothstep(0.62, 0.8, vGlove); diffuseColor.rgb = mix(diffuseColor.rgb, mix(vec3(0.9, 0.92, 0.87), vec3(0.55, 0.82, 0.12), cuff), gk); }');
      };
      c.customProgramCacheKey = () => 'hk-cloth-dye-glove';
      return c;
    });
  });
  KEEP.fig = K;
  KEEP.capDef = [['L_Hand', 'L_Finger2', 0.078, 2.0, 'hand'], ['R_Hand', 'R_Finger2', 0.078, 2.0, 'hand'], ['L_Forearm', 'L_Hand', 0.05, 1, 'arm'], ['R_Forearm', 'R_Hand', 0.05, 1, 'arm'],
    ['L_UpperArm', 'L_Forearm', 0.065, 1, 'arm'], ['R_UpperArm', 'R_Forearm', 0.065, 1, 'arm'], ['Pelvis', 'Neck', 0.15, 1, 'body'], ['Neck', 'Head', 0.11, 2.3, 'body'],
    ['L_Thigh', 'L_Calf', 0.088, 1, 'leg'], ['R_Thigh', 'R_Calf', 0.088, 1, 'leg'], ['L_Calf', 'L_Foot', 0.062, 1, 'leg'], ['R_Calf', 'R_Foot', 0.062, 1, 'leg'],
    ['L_Foot', 'L_Toe0', 0.05, 1.3, 'leg'], ['R_Foot', 'R_Toe0', 0.05, 1.3, 'leg']].map(([a, b, r, k, kind]) => ({ ia:HB[a], ib:HB[b], r, k, kind, a:new THREE.Vector3(), b:new THREE.Vector3() }));
  KEEP.dense.set(spD(KSPEC, 'ready', 1)); keeperGround(KEEP.dense[WR + 3], 0); keeperGo('ready'); keeperApply(0);
  scene.add(K.root);
}

/* ---------- Kicking ---------- */
function socInRange(P, far){
  const pos = P.mesh.position, dx = pos.x - cam.x, dz = pos.z - cam.z, d = Math.hypot(dx, dz);
  if (d > (far || 2.5) || pos.y > 1.2 || P.held) return false;
  if (d < 0.6) return true;
  return (dx * -Math.sin(cam.yaw) + dz * -Math.cos(cam.yaw)) / d > 0.26;
}
function kickNearest(far){
  let best = null, bs = Infinity;
  for (const P of PHYS.balls){
    if (!socInRange(P, far)) continue;
    const pos = P.mesh.position, d = Math.hypot(pos.x - cam.x, pos.z - cam.z);
    if (d < bs){ bs = d; best = P; }
  }
  return best;
}
function socChargeStart(src, P){
  if (!THREEOK || ride.on || paint.on || introOpen || KICK.st || !SOC.vis || !PHYS.mode) return false;
  P = P || kickNearest();
  if (!P){ if (src === 'key' || src === 'btn') toast('Walk up to a ball to kick it.'); return false; }
  sfxOn();
  Object.assign(KICK, { st:'charge', ball:P, src, t0:performance.now() });
  SOC.ui.meter.hidden = false; SOC.ui.aim.hidden = false; socMeter(0, false);
  if (SOC.ui.btn) SOC.ui.btn.classList.add('on');
  hideHint(); wake();
  return true;
}
function socChargeEnd(cancel){
  if (KICK.st !== 'charge') return;
  const hold = (performance.now() - KICK.t0) / 1000;
  SOC.ui.meter.hidden = true; SOC.ui.aim.hidden = true; if (SOC.ui.btn) SOC.ui.btn.classList.remove('on');
  KICK.st = '';
  if (cancel) return;
  sfxOn();
  const p = hold < 0.18 ? 0.42 : clamp(hold / 0.85, 0.15, 1), err = 1 + Math.max(0, hold - 1.15) * 2.2;
  kickPlan(KICK.ball, p, err);
}
function socMeter(p, over){
  const m = SOC.ui.meter; if (!m) return;
  m.firstChild.style.width = (p * 100).toFixed(1) + '%';
  m.classList.toggle('over', !!over);
  if (SOC.ui.btn) SOC.ui.btn.style.setProperty('--p', p.toFixed(3));
}
/* What you're looking at: a spot in the goal, a spot on the grass, or far off in the air */
function kickTarget(eye, dir, r){
  const g = GOAL;
  if (dir.x > 0.15){
    const t = (g.x - eye.x) / dir.x;
    if (t > 0 && t < 45){ const hy = eye.y + dir.y * t, hz = eye.z + dir.z * t; if (Math.abs(hz - g.z) < g.w / 2 + 3 && hy > -1 && hy < g.h + 3) return new THREE.Vector3(g.x, Math.max(hy, r), hz); }
  }
  if (dir.y < -0.03){ const t = (eye.y - r) / -dir.y; if (t < 32) return new THREE.Vector3(eye.x + dir.x * t, r, eye.z + dir.z * t); }
  return eye.clone().addScaledVector(dir, 16);
}
function kickSpin(psi, th, curl, p){
  const back = th < 0.1 ? 2 : 4 + 22 * th;
  return new THREE.Vector3(-Math.cos(psi) * back, -curl * (8 + 26 * p), Math.sin(psi) * back);
}
/* Find the launch angle and direction that carry the ball to the target, with drag and spin included */
function kickSolve(P, B, speed, T, curl, p){
  const D = Math.max(0.5, Math.hypot(T.x - B.x, T.z - B.z)), ux = (T.x - B.x) / D, uz = (T.z - B.z) / D;
  let psi = Math.atan2(ux, uz), th = clamp(Math.atan2(T.y - B.y, D) + 0.06, 0.02, 0.9);
  const v = new THREE.Vector3();
  for (let it = 0; it < 6; it++){
    v.set(Math.sin(psi) * Math.cos(th), Math.sin(th), Math.cos(psi) * Math.cos(th)).multiplyScalar(speed);
    let res = null;
    socSim(P.def, B, v, kickSpin(psi, th, curl, p), 3.5, false, (pp) => { const a = (pp.x - B.x) * ux + (pp.z - B.z) * uz; if (a >= D){ res = { y:pp.y, lat:(pp.x - B.x) * uz - (pp.z - B.z) * ux }; return true; } return false; });
    if (!res){ th = Math.min(th + 0.1, 0.62); continue; }
    th = clamp(th + Math.atan2(T.y - res.y, D) * 0.9, 0, 1.05);
    psi -= Math.atan2(res.lat, D) * 0.9;
  }
  return { psi, th };
}
function kickPlan(P, p, err){
  const yaw = cam.yaw, pitch = cam.pitch, fx = -Math.sin(yaw), fz = -Math.cos(yaw), rx = Math.cos(yaw), rz = -Math.sin(yaw);
  const B = P.p1.clone(), lv = P.body ? P.body.linvel() : P.v, bv = new THREE.Vector3(lv.x, 0, lv.z), dx = B.x - cam.x, dz = B.z - cam.z, dist = Math.hypot(dx, dz);
  if (dist > 2.8){ toast('Get closer to the ball first.'); return false; }
  if ((dx * fx + dz * fz) < 0.05 && dist > 0.45){ toast('Face the ball to kick it.'); return false; }
  const curl = clamp((dx * rx + dz * rz) / 0.5, -1, 1) * 0.85;
  const eye = new THREE.Vector3(cam.x, eyeY(), cam.z), dir = new THREE.Vector3(fx * Math.cos(pitch), Math.sin(pitch), fz * Math.cos(pitch));
  const r = P.def.r, T = kickTarget(eye, dir, r);
  const speed = (7 + 17 * Math.pow(p, 1.25)) * (P.def.skin === 'beach' ? 0.55 : 1) * (1 + gauss() * 0.02);
  /* Where your body has to be so the laces meet the ball: the plant foot lands beside it. A rolling ball
     keeps going during the run-up, so the strike is planned where it will be. */
  const c = BODY.contact || new THREE.Vector3(-0.09, 0.1, 0.29), lx = c.x + curl * 0.03, lz = c.z + r * 0.95;
  let Bc = B.clone(), Cx = 0, Cz = 0, Tr = 0, psi = yaw + Math.PI;
  const body = () => {
    const sn = Math.sin(psi), cs = Math.cos(psi), Rx = Bc.x - (lx * cs + lz * sn), Rz = Bc.z - (-lx * sn + lz * cs);
    Cx = Rx + sn * BODY.eyeF; Cz = Rz + cs * BODY.eyeF;
    Tr = REDUCED ? 0 : clamp(0.2 + Math.hypot(Cx - cam.x, Cz - cam.z) * 0.2, 0.24, 0.6);
  };
  for (let it = 0; it < 3; it++){ body(); Bc = B.clone().addScaledVector(bv, (Tr + 0.09) * 0.92); }
  const sol = kickSolve(P, Bc, speed, T, curl, p);
  sol.psi += gauss() * (0.5 + 2.2 * p * p) * D2R * err;
  sol.th = clamp(sol.th + gauss() * (0.4 + 1.8 * p * p) * D2R * err, 0, 1.05);
  psi = sol.psi; body();
  const v = new THREE.Vector3(Math.sin(sol.psi) * Math.cos(sol.th), Math.sin(sol.th), Math.cos(sol.psi) * Math.cos(sol.th)).multiplyScalar(speed);
  const w = kickSpin(sol.psi, sol.th, curl, p);
  KICK.plan = { P, p, v, w, psi:sol.psi, th:sol.th, S0:{ x:cam.x, z:cam.z }, C:{ x:Cx, z:Cz }, T:Tr, tc:Tr + (REDUCED ? 0 : 0.09), done:false, loft:clamp((sol.th - 0.22) / 0.4, 0, 1), B:Bc };
  Object.assign(KICK, { st:'run', t:0, drive:true, trackOn:!REDUCED });
  path.length = 0; faceYaw = facePitch = null;
  keeperKickStart(P, KICK.plan.tc);
  wake();
  return true;
}
/* The run-up, the strike and the follow-through. Your head stays over the ball, then lifts to watch it. */
function kickFrame(dt){
  const K = KICK, pl = K.plan; if (!pl) { K.st = ''; K.drive = false; return; }
  K.t += dt;
  const t = K.t, fx = Math.sin(pl.psi), fz = Math.cos(pl.psi);
  if (K.drive){
    let x, z;
    if (t <= pl.T){ const u = pl.T ? t / pl.T : 1, e = u * u * (3 - 2 * u) * 0.35 + u * 0.65; x = lerp(pl.S0.x, pl.C.x, e); z = lerp(pl.S0.z, pl.C.z, e); }
    else { const f = 0.34 * socSm(pl.tc, pl.tc + 0.45, t); x = pl.C.x + fx * f; z = pl.C.z + fz * f; }
    const [nx, nz] = constrain(cam.x, cam.z, x, z); cam.x = nx; cam.z = nz;
    if (!REDUCED && t < pl.tc){
      const B = pl.P.mesh.position, hd = Math.max(0.15, Math.hypot(B.x - cam.x, B.z - cam.z)), look = clamp(Math.atan2(B.y - eyeY(), hd) + 0.12, -1.12, 0.2);
      cam.pitch = lerp(cam.pitch, look, 1 - Math.exp(-dt * 9)); cam.yaw = lerpAngle(cam.yaw, pl.psi - Math.PI, 1 - Math.exp(-dt * 8));
    }
    if (t >= pl.tc + 0.3) K.drive = false;
  }
  if (!pl.done && t >= pl.tc){ pl.done = true; kickContact(pl); }
  /* After the strike your eyes follow the ball until you look somewhere yourself */
  if (pl.done && K.trackOn && t < pl.tc + 1.25){
    const B = pl.P.mesh.position, dx = B.x - cam.x, dz = B.z - cam.z, hd = Math.hypot(dx, dz);
    if (hd > 0.6){
      const wantYaw = Math.atan2(-dx, -dz), d = clamp(angDiff(pl.psi - Math.PI, wantYaw), -0.75, 0.75), k = 1 - Math.exp(-dt * 7);
      cam.yaw = lerpAngle(cam.yaw, pl.psi - Math.PI + d, k);
      cam.pitch = lerp(cam.pitch, clamp(Math.atan2(B.y - eyeY(), hd), -0.6, 0.5), k);
    }
  }
  if (t >= pl.T + 0.9){ K.st = ''; K.drive = false; K.plan = null; }
}
function kickContact(pl){
  const P = pl.P, b = P.body;
  /* If the ball rolled away during the run-up, a fresh swing still finds it when it's close */
  if (P.mesh.position.distanceTo(pl.B) > 0.7) return;
  P.kickT = PHYS.t; P.kickW = pl.w.clone(); P.netHit = false; SOC.inGoal = false;
  if (b){ b.wakeUp(); b.setLinvel(pl.v, true); b.setAngvel(pl.w, true); }
  else { P.v.copy(pl.v); if (!P.w) P.w = new THREE.Vector3(); P.w.copy(pl.w); P.sleep = false; P.still = 0; }
  sfxKick(pl.p, P.p1);
  if (P === SOC.ball){ const sh = socShotStart(P, pl.v); keeperShot(sh); }
}

/* ---------- Your body ---------- */
function bodyTouch(){ if (KICK.st === 'run') return; BODY.touch = 0.3; BODY.touchS = -BODY.touchS; }
function bodyFrame(dt){
  const f = BODY.fig; if (!f) return false;
  const show = !ride.on && !paint.on && roomAt(cam.x, cam.z).id === 'yard';
  if (f.root.visible !== show) f.root.visible = show;
  if (!show || !f.mesh) return false;
  const o = BODY.dense, S = BODY.S, run = KICK.st === 'run' && KICK.plan;
  BODY.sp = lerp(BODY.sp, Math.hypot(SOC.pv.x, SOC.pv.z), 1 - Math.exp(-dt * 8));
  const tYaw = run ? KICK.plan.psi : cam.yaw + Math.PI;
  BODY.yaw = lerpAngle(BODY.yaw, tYaw, 1 - Math.exp(-dt * (run ? 30 : 10)));
  if (run){
    const pl = KICK.plan, t = KICK.t - pl.T, L = BSPEC;
    const seg = [[-0.17, 'approach'], [0, 'plant'], [0.09, 'contact'], [0.3, 'follow'], [0.52, 'land'], [0.88, 'stand']];
    if (t < -0.17){
      o.set(spD(L, 'stand', 1));
      const ph = Math.PI / 2 + (t + 0.17) * Math.PI * 3.4;
      spGait(o, ph, 1, 0.75);
      const w = socSm(-0.34, -0.17, t); if (w > 0) spBlend(o, o, spD(L, 'approach', 1), w);
    } else {
      let i = 0; while (i < seg.length - 2 && t >= seg[i + 1][0]) i++;
      const [t0, a] = seg[i], [t1, b] = seg[i + 1], u = clamp((t - t0) / (t1 - t0), 0, 1);
      spBlend(o, spD(L, a, 1), spD(L, b, 1), i === 1 ? u * u : spEase(u));
      if (pl.loft > 0) spAdd(o, { spine:[-12, 0, 0], legL:[-4, 0, 0] }, pl.loft * socSm(-0.1, 0.1, t) * (1 - socSm(0.4, 0.7, t)));
    }
  } else {
    o.set(spD(BSPEC, 'stand', 1));
    const sp = BODY.sp, amp = clamp(sp / 1.8, 0, 1);
    if (amp > 0.02){ BODY.ph += dt * Math.PI * clamp(1.7 + 0.34 * sp, 1.7, 3.6); spGait(o, BODY.ph, amp, clamp((sp - 3.2) / 2.4, 0, 1)); }
    if (BODY.touch > 0){ BODY.touch -= dt; const w = Math.sin(clamp(1 - BODY.touch / 0.3, 0, 1) * Math.PI); spBlend(o, o, spD(BSPEC, 'touch', BODY.touchS), w * 0.9); }
    if (PLAYER.y > 0.02) spAdd(o, { legL:[24, 0, 0], legR:[30, 0, 0], knL:40, knR:46, armL:[10, 20, 0], armR:[10, 20, 0] }, clamp(PLAYER.y / 0.3, 0, 1));
  }
  hkPose(f, o); hkFingers(f, 0.15, 0.15, 0, 0);
  const sy = Math.sin(BODY.yaw), cy = Math.cos(BODY.yaw);
  f.root.position.set(cam.x - sy * BODY.eyeF, PLAYER.y + o[WR + 3] * S, cam.z - cy * BODY.eyeF);
  f.root.rotation.set(0, BODY.yaw, 0);
  /* During a kick your head leans over the ball, so the camera follows the head */
  const want = run && !REDUCED ? 1 : 0; BODY.lean = lerp(BODY.lean, want, 1 - Math.exp(-dt * 10));
  if (BODY.lean > 0.002){
    f.root.updateMatrixWorld(true); f.all[HB.Neck].getWorldPosition(_kv);
    /* Eyes sit forward of the neck; over the ball they lean out a little more, so your chest stays at the very edge of view */
    const fe = (0.1 + 0.07 * BODY.lean) * S, ex = _kv.x + sy * fe, ey = _kv.y + 0.155 * S, ez = _kv.z + cy * fe;
    CAMX.x = (ex - cam.x) * BODY.lean; CAMX.y = (ey - eyeY()) * BODY.lean; CAMX.z = (ez - cam.z) * BODY.lean;
  } else if (CAMX.x || CAMX.y || CAMX.z){ CAMX.x = CAMX.y = CAMX.z = 0; }
  return run || BODY.sp > 0.05 || BODY.touch > 0 || BODY.lean > 0.002;
}

/* ---------- The keeper ---------- */
function keeperGo(st){ KEEP.st = st; KEEP.t = 0; }
function keeperSpot(B){
  const g = GOAL, hw = g.w / 2;
  if (!B || B.x > g.x - 0.3 || B.x < g.x - 34 || Math.abs(B.z - g.z) > 16) return { x:KEEP_HOME.x, z:g.z, alert:0 };
  const dx = B.x - g.x, dz = B.z - g.z, d = Math.hypot(dx, dz);
  const out = clamp(0.4 + (14 - d) * 0.075, 0.4, 1.7);
  return { x:Math.min(g.x + dx / d * out, g.x - 0.3), z:clamp(g.z + dz / d * out, g.z - hw + 0.4, g.z + hw - 0.4), alert:d < 24 ? 1 : 0 };
}
/* The kicker is running up: get set, and sometimes pick a side early */
function keeperKickStart(P, tc){
  const K = KEEP; if (!K.fig || P !== SOC.ball) return;
  const B = P.p1; if (B.x > GOAL.x - 0.3 || B.x < GOAL.x - 26) return;
  const still = (P.body ? Math.hypot(P.body.linvel().x, P.body.linvel().z) : Math.hypot(P.v.x, P.v.z)) < 0.3;
  K.setAt = SOC.t + tc - 0.3;
  K.guess = still && GOAL.x - B.x > 5 && Math.random() < 0.27 ? (Math.random() < 0.5 ? 1 : -1) : 0;
  K.guessAt = SOC.t + tc;
}
/* The shot is struck: read it after a human reaction time */
function keeperShot(sh){
  const K = KEEP; if (!K.fig) return;
  if (!sh){ K.guess = 0; return; }
  if (K.guess){ K.react = -1; return; }
  K.react = SOC.t + 0.17 + Math.random() * 0.11;
}
function keeperCanAct(){ return ['ready', 'set', 'watch'].includes(KEEP.st); }
function keeperDecide(){
  const K = KEEP, P = SOC.ball; if (!P || !keeperCanAct()) return;
  const b = P.body, lv = b ? b.linvel() : P.v, v = _kd.set(lv.x, lv.y, lv.z);
  if (v.x < 1) return;
  let res = null;
  socSim(P.def, P.p1, v, null, 2.2, true, (p, vv, t) => { if (p.x >= K.pos.x){ res = { t, y:p.y, z:p.z }; return true; } return false; });
  if (!res) return;
  res.z += gauss() * 0.1; res.y = Math.max(0.1, res.y + gauss() * 0.08);
  const g = GOAL;
  if (Math.abs(res.z - g.z) > g.w / 2 + 0.35 || res.y > g.h + 0.3){ keeperGo('watch'); return; }
  keeperPlan(res.z, res.y, Math.max(0.1, res.t));
}
function keeperPlan(z, y, T){
  const K = KEEP, S = K.fig.S, lat = z - K.pos.z, al = Math.abs(lat);
  const s = lat < 0 ? 1 : -1;
  let type = 'dive';
  if (al < 0.42 && y > 0.32 && y < 1.75) type = 'chest';
  else if (al < 0.6 && y <= 0.32) type = 'scoop';
  else if (al < 0.75 && y >= 1.75) type = 'jump';
  const pl = { type, s, t0:SOC.t, T, z, y, c0:K.com.clone(), c1:new THREE.Vector3(), th:0, z0:K.pos.z };
  if (type === 'dive'){
    const L = 1.08 * S, th = clamp(1.5 - 0.55 * y, 0.5, 1.48);
    const need = Math.max(0, al - L * Math.sin(th)), can = 0.25 + 4.6 * Math.max(0, T - 0.1), go = Math.min(need, can);
    pl.th = th; pl.c1.set(K.pos.x - 0.18, clamp(y - L * Math.cos(th), 0.3, 1.38), K.pos.z - s * go);
  }
  K.plan = pl; keeperGo('save');
}
/* Ground stance: pelvis height from the pose, plus any hop */
function keeperGround(dy, hop){ const K = KEEP; K.com.set(K.pos.x, (0.895 + dy) * K.fig.S + (hop || 0), K.pos.z); K.roll = 0; }
function keeperMove(tx, tz, vmax, dt, face){
  const K = KEEP, dx = tx - K.pos.x, dz = tz - K.pos.z, d = Math.hypot(dx, dz), want = d > 0.02 ? Math.min(vmax, d * 4) : 0;
  const k = 1 - Math.exp(-dt * 10), wx = d > 1e-4 ? dx / d * want : 0, wz = d > 1e-4 ? dz / d * want : 0;
  K.v.x += (wx - K.v.x) * k; K.v.z += (wz - K.v.z) * k;
  K.pos.x += K.v.x * dt; K.pos.z += K.v.z * dt;
  if (face && Math.hypot(K.v.x, K.v.z) > 0.25) K.yaw = lerpAngle(K.yaw, Math.atan2(K.v.x, K.v.z), 1 - Math.exp(-dt * 8));
  return d;
}
function keeperFace(x, z, dt, lim){
  const K = KEEP; let want = Math.atan2(x - K.pos.x, z - K.pos.z);
  if (lim) want = -Math.PI / 2 + clamp(angDiff(-Math.PI / 2, want), -lim, lim);
  K.yaw = lerpAngle(K.yaw, want, 1 - Math.exp(-dt * 6));
}
function keeperHoldPoint(){
  const K = KEEP, f = K.fig; if (!f || !K.hold) return null;
  const l = _ke, r = _kd;
  f.all[HB.L_Hand].getWorldPosition(l); f.all[HB.L_Finger2].getWorldPosition(_kv); l.lerp(_kv, 0.75);
  f.all[HB.R_Hand].getWorldPosition(r); f.all[HB.R_Finger2].getWorldPosition(_kv); r.lerp(_kv, 0.75);
  return _kc.addVectors(l, r).multiplyScalar(0.5);
}
function keeperBeaten(){ const K = KEEP; K.after = 'beaten'; if (keeperCanAct()) keeperGo('beaten'); }
function keeperSaved(){ const K = KEEP; if (!K.hold) K.after = 'cheer'; }
/* Every frame: decide, move and pose the keeper, then update the shapes the ball can hit */
function keeperFrame(dt){
  const K = KEEP, f = K.fig; if (!f) return false;
  const P = SOC.ball, B = P ? P.mesh.position : null, g = GOAL, S = f.S;
  const near = Math.hypot(cam.x - g.x, cam.z - g.z) < 42 || (P && Math.hypot(B.x - g.x, B.z - g.z) < 30);
  if (!near && !SOC.shot && K.st === 'ready' && K.drawn){ K.near = false; return false; }
  K.near = true; K.t += dt;
  const o = K.dense, sp = (n, side) => spD(KSPEC, n, side || 1);
  let alert = 1;
  switch (K.st){
    case 'ready': case 'set': case 'watch': {
      const spot = keeperSpot(B); alert = spot.alert;
      keeperMove(spot.x, spot.z, 2.4, dt, false);
      if (B) keeperFace(B.x, B.z, dt, 1.0);
      o.set(sp('ready'));
      if (alert < 1) spBlend(o, o, sp('stand'), 0.55);
      /* Little bounces on the toes, and side-steps when shuffling across */
      const lat = Math.abs(K.v.z) + Math.abs(K.v.x);
      K.ph += dt * (lat > 0.25 ? lat * 5.2 : 0);
      if (lat > 0.25){ const s = Math.sin(K.ph); spAdd(o, { legL:[0, 7 * s, 0], legR:[0, -7 * s, 0], knL:6 * Math.max(0, s), knR:6 * Math.max(0, -s) }); }
      let hop = alert ? 0.012 * Math.max(0, Math.sin(K.t * 11.3)) * (lat > 0.25 ? 0 : 1) : 0;
      if (K.setAt > 0 && SOC.t >= K.setAt){ const u = (SOC.t - K.setAt) / 0.3; if (u < 1) hop = 0.07 * Math.sin(u * Math.PI); else K.setAt = -1; }
      if (K.st === 'watch'){ if (K.t > 1.1) keeperGo('ready'); }
      keeperGround(o[WR + 3], hop);
      if (K.guess && K.guessAt > 0 && SOC.t >= K.guessAt && SOC.shot){ const s = K.guess; K.guess = 0; K.guessAt = -1; keeperPlan(K.pos.z - s * (1.2 + Math.random() * 1.0), 0.25 + Math.random() * 1.3, 0.38); }
      else if (K.react > 0 && SOC.t >= K.react){ K.react = -1; keeperDecide(); }
      else if (K.st === 'ready' && P && !P.held && !SOC.shot && keeperWantsBall(P)) { K.way = keeperRoute(B.x, B.z); keeperGo('fetch'); }
      break;
    }
    case 'save': {
      const pl = K.plan, u = clamp((SOC.t - pl.t0) / pl.T, 0, 1);
      if (pl.type === 'dive'){
        const e = 1 - Math.pow(1 - u, 2.2), low = pl.y < 0.55;
        K.com.lerpVectors(pl.c0, pl.c1, e); K.pos.x = K.com.x; K.pos.z = K.com.z;
        K.roll = pl.s * pl.th * socSm(0, 0.85, u);
        spBlend(o, sp('ready'), sp(low ? 'divelow' : 'dive', pl.s), socSm(0, 0.5, u));
        if (u >= 1){ K.fallV = (pl.c1.z - pl.c0.z) / pl.T * 0.45; keeperGo('fall'); }
      } else {
        const toZ = pl.z0 + clamp(pl.z - pl.z0, -0.5, 0.5);
        K.pos.z = lerp(pl.z0, toZ, socSm(0, 0.8, u));
        const n = pl.type === 'chest' ? 'chest' : pl.type;
        spBlend(o, sp('ready'), sp(n), socSm(0, 0.7, u));
        let hop = 0;
        if (pl.type === 'chest'){ const dy = pl.y - 1.15; spAdd(o, { armL:[dy * 55, 0, 0], armR:[dy * 55, 0, 0], spine:[Math.max(0, -dy) * 38, 0, 0], dy:-Math.max(0, -dy) * 0.32 }, socSm(0, 0.7, u)); }
        if (pl.type === 'jump'){ const jh = clamp(pl.y - 2.0, 0, 0.45) + 0.1; hop = jh * Math.sin(Math.min(1, (SOC.t - pl.t0) / (pl.T + 0.25)) * Math.PI); }
        keeperGround(o[WR + 3], hop);
        if (SOC.t - pl.t0 > pl.T + 0.4) keeperGo(K.hold ? 'hold' : K.after === 'beaten' ? 'beaten' : 'ready');
      }
      if (K.st === 'save' && B && pl.type !== 'dive') keeperFace(B.x, B.z, dt, 1.0);
      break;
    }
    case 'fall': {
      const pl = K.plan, u = clamp(K.t / 0.42, 0, 1);
      K.com.z += K.fallV * dt; K.fallV *= Math.exp(-dt * 5);
      K.com.y = lerp(K.com.y, 0.26, 1 - Math.exp(-dt * (6 + 10 * u)));
      K.roll = pl.s * lerp(pl.th, 1.52, socSm(0, 1, u));
      spBlend(o, sp(pl.y < 0.55 ? 'divelow' : 'dive', pl.s), sp('lie', pl.s), socSm(0.2, 1, u));
      K.pos.x = K.com.x; K.pos.z = K.com.z;
      if (K.t > 0.5){ K.lieY = K.com.y; keeperGo('down'); }
      break;
    }
    case 'down': {
      const pl = K.plan; o.set(sp('lie', pl.s)); K.roll = pl.s * 1.52;
      if (K.t > (K.hold ? 0.35 : 0.6)) keeperGo('getup');
      break;
    }
    case 'getup': {
      const pl = K.plan, u = clamp(K.t / 0.9, 0, 1), e = spEase(u);
      spBlend(o, sp('lie', pl.s), sp(K.hold ? 'hold' : 'stand'), e);
      K.roll = pl.s * 1.52 * (1 - e);
      K.com.set(K.pos.x, lerp(K.lieY || 0.26, (0.895 + o[WR + 3]) * S, socSm(0.15, 1, u)), K.pos.z);
      if (u >= 1){ K.roll = 0; keeperGo(K.hold ? 'hold' : K.after === 'beaten' ? 'beaten' : K.after === 'cheer' ? 'cheer' : 'ready'); }
      break;
    }
    case 'beaten': {
      o.set(sp('beaten')); spBlend(o, sp('stand'), o, socSm(0, 0.3, K.t) * (1 - socSm(1.2, 1.5, K.t)));
      keeperGround(o[WR + 3], 0); K.after = '';
      if (K.t > 1.5){ if (P && keeperWantsBall(P, true)){ K.way = keeperRoute(B.x, B.z); keeperGo('fetch'); } else keeperGo('ready'); }
      break;
    }
    case 'cheer': {
      spBlend(o, sp('stand'), sp('cheer'), Math.sin(clamp(K.t / 0.9, 0, 1) * Math.PI));
      keeperGround(o[WR + 3], 0); K.after = '';
      if (K.t > 0.9) keeperGo('ready');
      break;
    }
    case 'fetch': {
      if (!P || P.held){ keeperGo('ready'); break; }
      if (!keeperWantsBall(P, true)){ keeperGo('ready'); break; }
      while (K.way.length && Math.hypot(K.way[0].x - K.pos.x, K.way[0].z - K.pos.z) < 0.25) K.way.shift();
      const dx = B.x - K.pos.x, dz = B.z - K.pos.z, d = Math.hypot(dx, dz) || 1;
      const tgt = K.way.length ? K.way[0] : { x:B.x - dx / d * 0.42, z:B.z - dz / d * 0.42 };
      const left = keeperMove(tgt.x, tgt.z, d > 3 ? 3.0 : 1.8, dt, true);
      keeperWalkPose(o, 'stand', dt);
      keeperGround(o[WR + 3], 0);
      if (!K.way.length && left < 0.12){ keeperFace(B.x, B.z, dt * 3); if (d < 0.75) keeperGo('pick'); }
      break;
    }
    case 'pick': {
      const u = K.t;
      spBlend(o, sp('stand'), sp('pick'), socSm(0, 0.35, u)); if (u > 0.35) spBlend(o, o, sp('hold'), socSm(0.4, 0.75, u));
      keeperGround(o[WR + 3], 0);
      if (B) keeperFace(B.x, B.z, dt, 0);
      if (!K.hold && u > 0.33 && P && P.mesh.position.distanceTo(K.com) < 1.6){ K.hold = true; P.held = true; SOC.inGoal = false; sfxGlove(0.2, P.p1); }
      if (u > 0.4 && !K.hold){ keeperGo('ready'); break; }
      if (u > 0.8){ K.way = keeperRoute(KEEP_HOME.x, KEEP_HOME.z, true); keeperGo('carry'); }
      break;
    }
    case 'carry': {
      while (K.way.length && Math.hypot(K.way[0].x - K.pos.x, K.way[0].z - K.pos.z) < 0.25) K.way.shift();
      const tgt = K.way.length ? K.way[0] : KEEP_HOME;
      const left = keeperMove(tgt.x, tgt.z, 2.0, dt, true);
      keeperWalkPose(o, 'hold', dt);
      keeperGround(o[WR + 3], 0);
      if (!K.way.length && left < 0.1){ keeperGo('hold'); }
      break;
    }
    case 'hold': {
      o.set(sp('hold')); keeperGround(o[WR + 3], 0);
      const tg = keeperRollTarget(); keeperFace(tg.x, tg.z, dt, 1.1);
      if (K.t > 0.7) keeperGo('roll');
      break;
    }
    case 'roll': {
      const u = K.t;
      if (u < 0.5) spBlend(o, sp('hold'), sp('roll1'), spEase(u / 0.5));
      else if (u < 0.72) spBlend(o, sp('roll1'), sp('roll2'), spEase((u - 0.5) / 0.22));
      else spBlend(o, sp('roll2'), sp('ready'), spEase((u - 0.72) / 0.5));
      keeperGround(o[WR + 3], 0);
      if (K.hold && u >= 0.66) keeperRelease();
      if (u > 1.25) keeperGo('ready');
      break;
    }
  }
  /* Looking at the ball, and blinking */
  if (B && !['fall', 'down'].includes(K.st)){
    const rel = clamp(angDiff(K.yaw + K.roll * 0, Math.atan2(B.x - K.pos.x, B.z - K.pos.z)), -1.1, 1.1);
    o[WB.neck * 3 + 1] += rel * 0.3; o[WB.head * 3 + 1] += rel * 0.4;
  }
  K.blinkT -= dt; if (K.blinkT < -0.15) K.blinkT = 2 + Math.random() * 3;
  f.blink = K.blinkT < 0 ? Math.sin(-K.blinkT / 0.15 * Math.PI) : 0; f.talk = 0; f.smile = K.st === 'cheer' ? 0.6 : 0.1;
  keeperApply(dt);
  return true;
}
function keeperWalkPose(o, base, dt){
  const K = KEEP, sp = Math.hypot(K.v.x, K.v.z);
  o.set(spD(KSPEC, base, 1));
  K.ph += dt * Math.PI * clamp(1.6 + 0.4 * sp, 1.6, 3.4);
  const amp = clamp(sp / 1.4, 0, 1);
  if (amp > 0.02){
    if (base === 'hold'){ const keep = o.slice(WB.shL * 3, WB.wrR * 3 + 3); spGait(o, K.ph, amp, clamp((sp - 2.2) / 1.5, 0, 1)); o.set(keep, WB.shL * 3); }
    else spGait(o, K.ph, amp, clamp((sp - 2.2) / 1.5, 0, 1));
  }
}
function keeperApply(dt){
  const K = KEEP, f = K.fig, o = K.dense, S = f.S;
  hkPose(f, o); hkFingers(f, o[WR + 6], o[WR + 7], 0, 0); hkFace(f);
  _kq.setFromAxisAngle(AX_Y, K.yaw); if (K.roll) _kq.multiply(_kq2.setFromAxisAngle(AX_Z, K.roll));
  f.root.quaternion.copy(_kq);
  _kv.set(0, 0.895 * S, 0).applyQuaternion(_kq);
  f.root.position.set(K.com.x - _kv.x, K.com.y - _kv.y, K.com.z - _kv.z);
  if (dt > 0){ K.vel.subVectors(K.com, K.prev).divideScalar(dt); if (K.vel.lengthSq() > 100) K.vel.setLength(10); }
  K.prev.copy(K.com);
  f.root.updateMatrixWorld(true);
  for (const c of K.capDef){ f.all[c.ia].getWorldPosition(c.a); f.all[c.ib].getWorldPosition(c.b); if (c.k !== 1) c.b.sub(c.a).multiplyScalar(c.k).add(c.a); }
  K.caps = K.capDef; K.drawn = true;
}
/* Balls he'll go and get: slow ones in and around his goal, that you aren't already playing */
function keeperWantsBall(P, after){
  const g = GOAL, p = P.mesh.position, b = P.body, lv = b ? b.linvel() : P.v;
  if (Math.hypot(lv.x, lv.y, lv.z) > (after ? 4 : 2.6) || p.y > 0.6) return false;
  if (p.x < g.x - 5.5 || p.x > g.x + g.d + 3 || Math.abs(p.z - g.z) > g.w / 2 + 2.6) return false;
  if (Math.hypot(p.x - cam.x, p.z - cam.z) < 2.4 || (KICK.st && KICK.ball === P)) return false;
  return true;
}
/* Around the posts rather than through the net */
function keeperRoute(tx, tz, back){
  const g = GOAL, hw = g.w / 2, inBox = (x, z) => x > g.x - 0.1 && x < g.x + g.d && Math.abs(z - g.z) < hw;
  const behind = (x, z) => x > g.x + 0.05 && !inBox(x, z);
  const from = { x:KEEP.pos.x, z:KEEP.pos.z }, to = { x:tx, z:tz };
  const out = behind(to.x, to.z) ? to : behind(from.x, from.z) ? from : null;
  if (!out) return [];
  const s = Math.sign(out.z - g.z) || 1, w1 = { x:g.x - 0.5, z:g.z + s * (hw + 0.6) }, w2 = { x:g.x + 0.7, z:g.z + s * (hw + 0.6) };
  return out === to ? [w1, w2] : [w2, w1];
}
function keeperRollTarget(){
  const g = GOAL, d = Math.hypot(cam.x - g.x, cam.z - g.z);
  if (cam.x < g.x - 1.5 && d < 20 && roomAt(cam.x, cam.z).id === 'yard') return { x:cam.x - Math.sin(cam.yaw) * 0.5, z:cam.z - Math.cos(cam.yaw) * 0.5, you:true };
  return { x:SOC.spot.x, z:SOC.spot.z, you:false };
}
/* Bowl it out along the grass so it stops about where you are */
function keeperRelease(){
  const K = KEEP, P = SOC.ball; K.hold = false; if (!P) return;
  P.held = false;
  const f = K.fig; f.all[HB.R_Hand].getWorldPosition(_kv);
  const tg = keeperRollTarget(), dx = tg.x - _kv.x, dz = tg.z - _kv.z, d = Math.hypot(dx, dz) || 1;
  const sp = Math.min(9, Math.sqrt(0.5 + 2 * 1.25 * d) + (tg.you ? 0 : 0.4)), v = new THREE.Vector3(dx / d * sp, -0.4, dz / d * sp);
  const pos = new THREE.Vector3(_kv.x + dx / d * 0.15, Math.max(P.def.r, _kv.y - 0.05), _kv.z + dz / d * 0.15), w = new THREE.Vector3(v.z / P.def.r, 0, -v.x / P.def.r);
  if (P.body){ P.body.setTranslation(pos, true); P.body.setLinvel(v, true); P.body.setAngvel(w, true); }
  else { P.p1.copy(pos); P.p0.copy(pos); P.v.copy(v); if (!P.w) P.w = new THREE.Vector3(); P.w.copy(w); P.sleep = false; P.still = 0; }
  P.p1.copy(pos); P.kickT = PHYS.t - 0.3;
}
/* The ball against the keeper: swept, so even a hard shot can't slip between frames */
function keeperCollide(P, p0, p1, lv){
  const K = KEEP, r = P.def.r, L = p0.distanceTo(p1), n = Math.max(1, Math.ceil(L / 0.045));
  for (let k = 1; k <= n; k++){
    _kc.lerpVectors(p0, p1, k / n);
    for (const c of K.caps){
      _kd.subVectors(c.b, c.a); const t = clamp(_ke.subVectors(_kc, c.a).dot(_kd) / Math.max(1e-6, _kd.lengthSq()), 0, 1);
      _kv.copy(c.a).addScaledVector(_kd, t);
      const d = _kv.distanceTo(_kc);
      if (d < c.r + r){ keeperHit(P, c, _kc.clone(), _kv.clone(), d, lv); return; }
    }
  }
}
function keeperHit(P, c, at, q, d, lv){
  const K = KEEP, r = P.def.r, vb = new THREE.Vector3(lv.x, lv.y, lv.z);
  const nrm = d > 1e-4 ? at.clone().sub(q).normalize() : vb.clone().normalize().negate();
  const rel = vb.clone().sub(K.vel), vn = rel.dot(nrm);
  if (vn >= 0) return;
  const pos = q.clone().addScaledVector(nrm, c.r + r + 0.004), speed = rel.length();
  if (SOC.shot && SOC.shot.P === P) SOC.shot.touched = true;
  const catchable = P === SOC.ball && !K.hold && c.kind !== 'leg' && ['save', 'ready', 'set', 'watch', 'fall'].includes(K.st);
  if (catchable && speed < 17.5){
    const pc = SOC.forceCatch != null ? SOC.forceCatch : clamp((17.5 - speed) / 8.5, 0, 1) * (c.kind === 'hand' ? 1 : c.kind === 'body' ? 0.9 : 0.5);
    if (Math.random() < pc){
      K.hold = true; P.held = true; sfxGlove(Math.min(1, speed / 15), pos);
      const hp = keeperHoldPoint() || pos;
      if (P.body){ P.body.setTranslation(hp, true); P.body.setLinvel({ x:0, y:0, z:0 }, true); P.body.setAngvel({ x:0, y:0, z:0 }, true); } else { P.v.set(0, 0, 0); }
      P.p1.copy(hp);
      return;
    }
  }
  const e = c.kind === 'hand' ? 0.3 : 0.42;
  rel.addScaledVector(nrm, -(1 + e) * vn);
  _kd.copy(nrm).multiplyScalar(rel.dot(nrm)); _ke.copy(rel).sub(_kd).multiplyScalar(0.75); rel.copy(_kd).add(_ke);
  vb.copy(rel).add(K.vel);
  if (c.kind === 'hand'){ vb.x -= 1.0; vb.y += 1.2; vb.z += (Math.sign(pos.z - GOAL.z) || 1) * 1.6; sfxGlove(Math.min(1, speed / 18), pos); }
  else sfxBounce(Math.min(1, speed / 12), pos);
  const w = new THREE.Vector3(gauss() * 12, gauss() * 12, gauss() * 12);
  if (P.body){ P.body.setTranslation(pos, true); P.body.setLinvel(vb, true); P.body.setAngvel(w, true); }
  else { P.v.copy(vb); if (P.w) P.w.copy(w); }
  P.p1.copy(pos);
}

/* ---------- The frame: kick, keeper, body, net, shot result, buttons ---------- */
function socFrame(dt){
  SOC.t += dt;
  if (!SOC.vis){ SOC.vis = true; hkWant('yard'); }
  if (SOC.pp && dt > 0){ const dx = cam.x - SOC.pp.x, dz = cam.z - SOC.pp.z; if (Math.abs(dx) + Math.abs(dz) < 1.5) SOC.pv.set(dx / dt, 0, dz / dt).clampLength(0, 7); else SOC.pv.set(0, 0, 0); }
  SOC.pp = { x:cam.x, z:cam.z };
  let a = false;
  if (KICK.st === 'run'){ kickFrame(dt); a = true; }
  if (keeperFrame(dt)) a = true;
  if (bodyFrame(dt)) a = true;
  if (socNetFrame(dt)) a = true;
  socShotFrame();
  /* You can't walk through the keeper */
  if (KEEP.fig && !ride.on){ const dx = cam.x - KEEP.com.x, dz = cam.z - KEEP.com.z, d = Math.hypot(dx, dz); if (d < 0.5 && d > 1e-3 && KEEP.com.y > 0.5){ const [nx, nz] = constrain(cam.x, cam.z, KEEP.com.x + dx / d * 0.5, KEEP.com.z + dz / d * 0.5); cam.x = nx; cam.z = nz; } }
  socUiFrame();
  return a || !!KICK.st;
}
function socUiFrame(){
  const U = SOC.ui; if (!U.meter) return;
  if (KICK.st === 'charge'){
    const hold = (performance.now() - KICK.t0) / 1000;
    socMeter(clamp(hold / 0.85, 0, 1), hold > 1.15);
    if (!socInRange(KICK.ball, 3.2)) socChargeEnd(true);
  }
  const near = !ride.on && !paint.on && roomAt(cam.x, cam.z).id === 'yard' && !!kickNearest(2.6);
  if (U.btn && COARSE){ const show = near || KICK.st === 'charge'; if (U.btn.hidden === show) U.btn.hidden = !show; }
  if (near && !SOC.told && SOC.ball && kickNearest(2.6) === SOC.ball){
    SOC.told = 1;
    toast(COARSE ? 'Hold Kick to power up, look where you want the ball to go, then let go.' : 'Hold F, or press and hold on the ball, to power up. Look where you want it to go, then let go.');
  }
}
/* Leaving the yard tidies everything up */
function socHide(){
  if (!SOC.vis) return;
  SOC.vis = false;
  if (KICK.st === 'charge') socChargeEnd(true);
  KICK.st = ''; KICK.plan = null; KICK.drive = false; CAMX.x = CAMX.y = CAMX.z = 0;
  SOC.shot = null; SOC.inGoal = false;
  const K = KEEP; K.hold = false; K.plan = null; K.after = ''; K.guess = 0; K.react = -1; K.setAt = -1;
  K.pos.x = KEEP_HOME.x; K.pos.z = KEEP_HOME.z; K.v.x = K.v.z = 0; K.yaw = -Math.PI / 2; K.roll = 0; keeperGo('ready');
  if (SOC.ui.btn) SOC.ui.btn.hidden = true;
  if (BODY.fig) BODY.fig.root.visible = false;
}
/* Tap a ball that's out of reach and you walk up behind it (lined up on goal for the soccer ball) */
function socTap(P){
  const pos = P.mesh.position, dx = pos.x - cam.x, dz = pos.z - cam.z, d = Math.hypot(dx, dz) || 1;
  if (d > 2.5){
    let ux = dx / d, uz = dz / d;
    if (P === SOC.ball && pos.x < GOAL.x - 1.5){ const gx = GOAL.x - pos.x, gz = GOAL.z - pos.z, gl = Math.hypot(gx, gz); ux = gx / gl; uz = gz / gl; }
    walkTo(safeTarget({ x:pos.x - ux * 1.3, z:pos.z - uz * 1.3 }), { yaw:Math.atan2(-ux, -uz), pitch:-0.1 });
    return;
  }
  if (!PHYS.mode){ physLoad(); toast('Warming up the physics…'); return; }
  if (socChargeStart('tap', P)) socChargeEnd();
}
function socInitUi(){
  SOC.ui = { btn:document.getElementById('bKick'), meter:document.getElementById('kickMeter'), aim:document.getElementById('aimDot') };
  const b = SOC.ui.btn; if (!b) return;
  b.addEventListener('pointerdown', (e) => { e.preventDefault(); try { b.setPointerCapture(e.pointerId); } catch (_) {} socChargeStart('btn'); });
  b.addEventListener('pointerup', () => socChargeEnd());
  b.addEventListener('pointercancel', () => socChargeEnd(true));
  b.addEventListener('contextmenu', (e) => e.preventDefault());
  b.addEventListener('click', (e) => { if (e.detail === 0 && socChargeStart('btn')) socChargeEnd(); });
}
function keeperTalk(){
  const s = SOC.score;
  toast(s.shots ? 'The keeper has saved ' + s.saves + ' of your ' + s.shots + (s.shots === 1 ? ' shot' : ' shots') + '. Go again from the spot.' : 'The keeper is ready. Shoot from the penalty spot: pick a corner, hit it hard, or bend it.');
}
