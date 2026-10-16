/* ================================================================
   Physics in the Recess Yard. Balls, a foam-block tower and a soccer
   goal run on Rapier, a real physics engine that loads on demand. If
   the browser blocks WebAssembly, a small built-in solver keeps the
   balls rolling. Swings are pendulums and the merry-go-round a flywheel.
   ================================================================ */
const RAPIER_URL = 'https://cdn.jsdelivr.net/npm/@dimforge/rapier3d-compat@0.14.0/rapier.es.js';
const PSTEP = 1 / 60;
const PHYS = { mode:'', loading:false, R:null, world:null, player:null, pp:null, acc:0, t:0, props:[], byId:{}, balls:[], boxes:[], circles:[], dome:null, goals:0, vis:false };
/* Real sizes and weights. cd: drag coefficient (the soccer ball's drops at speed, the "drag crisis"),
   cl: how strongly spin bends its flight, roll: grass rolling resistance in m/s² */
const BALL_DEFS = [
  { id:'soccer', name:'Soccer ball', r:0.11, mass:0.43, bounce:0.74, cd:[0.47, 0.22, 9, 15], cl:1.0, roll:1.0, at:[79.1, -2.0], skin:'soccer' },
  { id:'kick-red', name:'Kickball', r:0.125, mass:0.32, bounce:0.8, cd:[0.5], cl:0.7, roll:0.9, at:[61.6, 2.6], skin:'stripe', c:['#d9412b', '#f6e6cc'] },
  { id:'kick-blue', name:'Kickball', r:0.125, mass:0.32, bounce:0.8, cd:[0.5], cl:0.7, roll:0.9, at:[72.4, -6.5], skin:'stripe', c:['#2a6fd6', '#e6eef9'] },
  { id:'beach', name:'Beach ball', r:0.3, mass:0.11, bounce:0.66, cd:[0.5], cl:0.4, roll:0.7, at:[58.6, 8.0], skin:'beach' }
];
const TOWER = { x:64.5, z:1.5, s:0.45, rows:['PLAY', 'LAB', 'XR', '★'] };
const BLOCK_COLS = ['#e2462f', '#f29a2e', '#f2c14e', '#3fae5a', '#2f7de2', '#8a5cf0', '#e2559a', '#1fb5b0', '#f29a2e', '#e2462f'];
/* A youth-size goal, 5 m by 2 m, with a net that slopes back to the ground */
const GOAL = { x:86.6, z:-2.0, w:5.0, h:2.0, d:1.6, dt:0.62, pr:0.05 };

/* ---------- Looks ---------- */
function canvasBall(d){
  const W = 256, H = 128, c = mk(W, H), x = c.getContext('2d');
  if (d.skin === 'soccer'){
    x.fillStyle = '#f4f2ec'; x.fillRect(0, 0, W, H);
    x.fillStyle = '#1b1d22';
    const pent = (cx, cy, r) => { for (const ox of [-W, 0, W]){ x.beginPath(); for (let i = 0; i < 5; i++){ const a = -Math.PI / 2 + i * Math.PI * 2 / 5; x.lineTo(cx + ox + Math.cos(a) * r * 1.25, cy + Math.sin(a) * r); } x.closePath(); x.fill(); } };
    for (let i = 0; i < 5; i++){ pent((i + 0.5) * W / 5, H * 0.5, 13); pent(i * W / 5, H * 0.21, 10); pent(i * W / 5, H * 0.79, 10); }
    x.fillRect(0, 0, W, 7); x.fillRect(0, H - 7, W, 7);
    x.strokeStyle = 'rgba(40,40,46,0.45)'; x.lineWidth = 1.5;
    for (let i = 0; i < 10; i++){ x.beginPath(); x.moveTo(i * W / 10, H * 0.08); x.lineTo(i * W / 10 + W / 20, H * 0.35); x.lineTo(i * W / 10, H * 0.65); x.lineTo(i * W / 10 + W / 20, H * 0.92); x.stroke(); }
  } else if (d.skin === 'stripe'){
    x.fillStyle = d.c[0]; x.fillRect(0, 0, W, H);
    x.fillStyle = d.c[1]; x.fillRect(0, H * 0.42, W, H * 0.16);
    x.fillStyle = 'rgba(255,255,255,0.18)'; for (let i = 0; i < 8; i++) x.fillRect(i * W / 8, 0, 2, H);
  } else {
    ['#e2462f', '#f7f4ec', '#2f7de2', '#f2c14e', '#f7f4ec', '#3fae5a'].forEach((cc, i) => { x.fillStyle = cc; x.fillRect(i * W / 6, 0, W / 6 + 1, H); });
    x.fillStyle = '#f7f4ec'; x.fillRect(0, 0, W, H * 0.08); x.fillRect(0, H * 0.92, W, H * 0.08);
  }
  return c;
}
function canvasBlock(ch, col){
  const S = 128, c = mk(S, S), x = c.getContext('2d');
  x.fillStyle = col; x.fillRect(0, 0, S, S);
  x.strokeStyle = 'rgba(255,255,255,0.4)'; x.lineWidth = 6; x.strokeRect(11, 11, S - 22, S - 22);
  x.fillStyle = '#fffaf0'; x.font = '700 76px ' + F.ui; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(ch, S / 2, S / 2 + 5);
  return c;
}

function addProp(mesh, kind, name, mass, def){
  const P = { id:'p' + PHYS.props.length, kind, name, mass, def, mesh, home:mesh.position.clone(), homeQ:mesh.quaternion.clone(),
    p0:mesh.position.clone(), p1:mesh.position.clone(), q0:mesh.quaternion.clone(), q1:mesh.quaternion.clone(), v:new THREE.Vector3(), body:null, sleep:true, still:0, resetAt:0 };
  mesh.userData.prop = P.id; mesh.castShadow = true; mesh.receiveShadow = true;
  scene.add(mesh); pickItems.push(mesh);
  PHYS.props.push(P); PHYS.byId[P.id] = P;
  if (kind === 'ball') PHYS.balls.push(P);
  return P;
}
/* Built with the playground, so the props share its wing, lights and shadows */
function buildProps(){
  for (const d of BALL_DEFS){
    const soccer = d.skin === 'soccer';
    const m = new THREE.Mesh(new THREE.SphereGeometry(d.r, soccer ? 48 : 32, soccer ? 28 : 18), soccer ? socBallMaterial() : new THREE.MeshStandardMaterial({ map:tex(canvasBall(d)), roughness:d.skin === 'beach' ? 0.3 : 0.55 }));
    m.position.set(d.at[0], d.r, d.at[1]); m.rotation.set(0.3, d.at[0], 0.2);
    const P = addProp(m, 'ball', d.name, d.mass, d);
    /* A bigger invisible target, so a real-size ball is easy to tap */
    const hit = new THREE.Mesh(new THREE.SphereGeometry(Math.max(0.36, d.r + 0.12), 10, 8), PICK_PROXY); hit.userData.prop = P.id; m.add(hit); pickItems.push(hit);
    const blob = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ color:0x000000, map:socBlob(), transparent:true, depthWrite:false, toneMapped:false, opacity:0.75 }));
    blob.rotation.x = -Math.PI / 2; blob.position.set(d.at[0], 0.014, d.at[1]); blob.scale.setScalar(d.r * 2.4); blob.userData.noAO = true; blob.renderOrder = 1; scene.add(blob);
    P.blob = blob; P.w = new THREE.Vector3();
    if (soccer) SOC.ball = P;
  }
  const s = TOWER.s, geo = XT.RoundedBoxGeometry ? new XT.RoundedBoxGeometry(s, s, s, 3, 0.05) : new THREE.BoxGeometry(s, s, s);
  let k = 0;
  TOWER.rows.forEach((word, row) => {
    const chars = [...word];
    chars.forEach((ch, i) => {
      const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ map:tex(canvasBlock(ch, BLOCK_COLS[k % BLOCK_COLS.length])), roughness:0.7 }));
      m.position.set(TOWER.x, s / 2 + row * (s + 0.003), TOWER.z + (i - (chars.length - 1) / 2) * (s + 0.012));
      addProp(m, 'block', 'Foam block', 1.2, { s });
      k++;
    });
  });
  socBuildPitch(); socBuildGoal(); socBuildPeople();
  buildConfetti();
}
/* ---------- Goal confetti ---------- */
const CONF = { mesh:null, n:96, t:0, on:false, p:null, v:null, r:null, w:null };
const _cm = new THREE.Matrix4(), _cq = new THREE.Quaternion(), _ce = new THREE.Euler(), _cp = new THREE.Vector3(), _cs = new THREE.Vector3(1, 1, 1);
function buildConfetti(){
  const mat = new THREE.MeshBasicMaterial({ side:THREE.DoubleSide, toneMapped:false }); mat.userData.boosted = true;
  const m = new THREE.InstancedMesh(new THREE.PlaneGeometry(0.07, 0.11), mat, CONF.n);
  const cols = ['#e2462f', '#f2c14e', '#3fae5a', '#2f7de2', '#8a5cf0', '#e2559a', '#ffffff'].map((c) => new THREE.Color(c));
  for (let i = 0; i < CONF.n; i++) m.setColorAt(i, cols[i % cols.length]);
  m.frustumCulled = false; m.visible = false; m.userData.noAO = true; m.userData.noShadow = true;
  CONF.p = new Float32Array(CONF.n * 3); CONF.v = new Float32Array(CONF.n * 3); CONF.r = new Float32Array(CONF.n * 3); CONF.w = new Float32Array(CONF.n * 3);
  CONF.mesh = m; scene.add(m);
}
function confettiBurst(x, y, z){
  if (!CONF.mesh || REDUCED) return;
  const P = CONF.p, V = CONF.v, R = CONF.r, W = CONF.w, rr = Math.random;
  for (let i = 0; i < CONF.n; i++){
    const k = i * 3;
    P[k] = x + rr() * 0.5 - 0.25; P[k + 1] = y + rr() * 0.4; P[k + 2] = z + (rr() - 0.5) * 2.2;
    V[k] = -1.2 - rr() * 3.2; V[k + 1] = 3.8 + rr() * 3.6; V[k + 2] = (rr() - 0.5) * 5;
    for (let j = 0; j < 3; j++){ R[k + j] = rr() * 6.3; W[k + j] = (rr() - 0.5) * 16; }
  }
  CONF.t = 0; CONF.on = true; CONF.mesh.visible = true;
}
function confettiFrame(dt){
  if (!CONF.on) return false;
  CONF.t += dt;
  const P = CONF.p, V = CONF.v, R = CONF.r, W = CONF.w, drag = Math.exp(-dt * 1.6), s = Math.max(0, Math.min(1, (4.2 - CONF.t) / 0.8));
  _cs.setScalar(s);
  for (let i = 0; i < CONF.n; i++){
    const k = i * 3;
    if (P[k + 1] > 0.02){
      V[k + 1] -= 5.5 * dt; V[k] *= drag; V[k + 1] *= drag; V[k + 2] *= drag;
      P[k] += V[k] * dt; P[k + 1] += V[k + 1] * dt; P[k + 2] += V[k + 2] * dt;
      for (let j = 0; j < 3; j++) R[k + j] += W[k + j] * dt;
      if (P[k + 1] <= 0.02){ P[k + 1] = 0.02; R[k] = -Math.PI / 2; R[k + 1] = 0; }
    }
    _cm.compose(_cp.set(P[k], P[k + 1], P[k + 2]), _cq.setFromEuler(_ce.set(R[k], R[k + 1], R[k + 2])), _cs);
    CONF.mesh.setMatrixAt(i, _cm);
  }
  CONF.mesh.instanceMatrix.needsUpdate = true;
  if (CONF.t > 4.2){ CONF.on = false; CONF.mesh.visible = false; }
  return true;
}

/* ---------- Static shapes the balls can hit ---------- */
function physShapes(){
  const B = [], C = [];
  const box = (cx, cy, cz, hx, hy, hz, e, soft) => B.push({ cx, cy, cz, hx, hy, hz, e:e == null ? 0.35 : e, soft:!!soft });
  box(33.85, 3, 8.7, 0.15, 3, 17.6); box(92.05, 3, 8.7, 0.15, 3, 17.6); box(63, 3, 26.05, 29.2, 3, 0.15); box(63, 3, -8.75, 29.2, 3, 0.15);
  const ez = DOME.z - DOME.r - 0.3;
  box(DOME.x, 1.4, ez, 1.35, 1.4, 0.95);
  /* The posts and crossbar are hard; the net is handled as a soft spring (soccer.js) */
  const g = GOAL, hw = g.w / 2;
  B.push({ cx:g.x, cy:g.h, cz:g.z, hx:g.pr, hy:g.pr, hz:hw + g.pr, e:0.55, soft:false, bar:true });
  for (const s of [-1, 1]) C.push({ x:g.x, z:g.z + s * hw, r:g.pr, h:g.h, e:0.55 });
  for (const o of OBST){
    if (o.goal || o.x < 34 || o.z < -8.6) continue;
    if (Math.hypot(o.x - DOME.x, o.z - DOME.z) < 0.5 || Math.hypot(o.x - DOME.x, o.z - ez) < 0.6) continue;
    const big = o.r >= 3;
    C.push({ x:o.x, z:o.z, r:big ? o.r - 0.3 : Math.max(0.07, o.r - 0.3), h:big ? 3 : 2.6, e:0.35 });
  }
  PHYS.boxes = B; PHYS.circles = C;
  PHYS.dome = { x:DOME.x, y:0.3, z:DOME.z, r:DOME.r + 0.05 };
}

/* ---------- Loading: Rapier first, the simple solver if it can't run here ---------- */
function physLoad(){
  if (PHYS.loading) return;
  PHYS.loading = true;
  physShapes();
  import(RAPIER_URL).then(async (mod) => {
    const R = mod.default && mod.default.init ? mod.default : mod;
    await R.init();
    PHYS.R = R; rapierBuild(); PHYS.mode = 'rapier';
  }).catch(() => {
    console.info('The physics engine could not start here, so the balls use simple physics.');
    PHYS.mode = 'simple'; PHYS.world = null;
    for (const P of PHYS.props) P.body = null;
    /* Without the engine the tower stands still, so it becomes an obstacle like a bench */
    for (const P of PHYS.props) if (P.kind === 'block'){ const i = pickItems.indexOf(P.mesh); if (i >= 0) pickItems.splice(i, 1); }
    OBST.push({ x:TOWER.x, z:TOWER.z, r:1.15 }); buildNav();
  }).finally(() => wake());
}
function rapierBuild(){
  const R = PHYS.R, w = new R.World({ x:0, y:-9.81, z:0 });
  w.timestep = PSTEP;
  const MIN = R.CoefficientCombineRule ? R.CoefficientCombineRule.Min : null;
  w.createCollider(R.ColliderDesc.cuboid(45, 0.5, 45).setTranslation(63, -0.5, -4).setFriction(0.75).setRestitution(SOC_GE));
  for (const b of PHYS.boxes){
    if (b.bar){ w.createCollider(R.ColliderDesc.capsule(b.hz, b.hy).setTranslation(b.cx, b.cy, b.cz).setRotation({ x:Math.SQRT1_2, y:0, z:0, w:Math.SQRT1_2 }).setRestitution(b.e).setFriction(0.5)); continue; }
    const d = R.ColliderDesc.cuboid(b.hx, b.hy, b.hz).setTranslation(b.cx, b.cy, b.cz).setRestitution(b.e).setFriction(b.soft ? 1 : 0.6);
    if (b.soft && MIN != null && d.setRestitutionCombineRule) d.setRestitutionCombineRule(MIN);
    w.createCollider(d);
  }
  for (const c of PHYS.circles) w.createCollider(R.ColliderDesc.cylinder(c.h / 2, c.r).setTranslation(c.x, c.h / 2, c.z).setRestitution(c.e));
  const D = PHYS.dome; w.createCollider(R.ColliderDesc.ball(D.r).setTranslation(D.x, D.y, D.z).setRestitution(0.4));
  for (const P of PHYS.props){
    const ball = P.kind === 'ball', q = P.homeQ;
    /* Balls get their air drag, spin lift and grass rolling from soccer.js each step, so no damping here */
    const bd = R.RigidBodyDesc.dynamic().setTranslation(P.home.x, P.home.y, P.home.z).setRotation({ x:q.x, y:q.y, z:q.z, w:q.w })
      .setLinearDamping(ball ? 0 : 0.05).setAngularDamping(ball ? 0 : 0.2).setCcdEnabled(ball);
    if (!ball && bd.setSleeping) bd.setSleeping(true);
    P.body = w.createRigidBody(bd);
    const hs = ball ? 0 : P.def.s / 2, vol = ball ? 4 / 3 * Math.PI * P.def.r ** 3 : P.def.s ** 3;
    const cd = ball ? R.ColliderDesc.ball(P.def.r) : (R.ColliderDesc.roundCuboid ? R.ColliderDesc.roundCuboid(hs - 0.045, hs - 0.045, hs - 0.045, 0.045) : R.ColliderDesc.cuboid(hs, hs, hs));
    /* A ball is a hollow shell, which spins up and rolls differently from a solid one */
    const I = 2 / 3 * P.mass * (ball ? P.def.r * P.def.r : 0);
    if (ball && cd.setMassProperties) cd.setMassProperties(P.mass, { x:0, y:0, z:0 }, { x:I, y:I, z:I }, { x:0, y:0, z:0, w:1 }); else cd.setDensity(P.mass / vol);
    cd.setFriction(ball ? 0.6 : 0.85).setRestitution(ball ? P.def.bounce : 0.12);
    /* Your feet move balls (dribbling, in soccer.js); your body still knocks the tower over */
    if (ball && cd.setCollisionGroups) cd.setCollisionGroups(0x0004FFFD);
    w.createCollider(cd, P.body);
  }
  PHYS.player = w.createRigidBody(R.RigidBodyDesc.kinematicPositionBased().setTranslation(cam.x, -20, cam.z));
  const pc = R.ColliderDesc.capsule(0.55, 0.3).setRestitution(0.3).setFriction(0.3);
  if (pc.setCollisionGroups) pc.setCollisionGroups(0x0002FFFB);
  w.createCollider(pc, PHYS.player);
  PHYS.world = w;
}

/* ---------- Stepping ---------- */
function rapierStep(){
  const tx = cam.x, tz = cam.z, ty = ride.on ? -20 : 0.9 + PLAYER.y, pp = PHYS.pp;
  if (!pp || ride.on || Math.abs(tx - pp.x) + Math.abs(tz - pp.z) > 1.2) PHYS.player.setTranslation({ x:tx, y:ty, z:tz }, true);
  else PHYS.player.setNextKinematicTranslation({ x:tx, y:ty, z:tz });
  PHYS.pp = { x:tx, z:tz };
  socPreStep(PSTEP);
  PHYS.world.step();
  for (const P of PHYS.props){
    if (P.body.isSleeping()) continue;
    const t = P.body.translation(), r = P.body.rotation();
    P.p1.set(t.x, t.y, t.z); P.q1.set(r.x, r.y, r.z, r.w);
  }
  socPostStep(PSTEP);
}
const _sv = new THREE.Vector3(), _sq = new THREE.Quaternion(), _sa = new THREE.Vector3();
function sphereBox(p, v, r, b, e0){
  const qx = clamp(p.x, b.cx - b.hx, b.cx + b.hx), qy = clamp(p.y, b.cy - b.hy, b.cy + b.hy), qz = clamp(p.z, b.cz - b.hz, b.cz + b.hz);
  let nx = p.x - qx, ny = p.y - qy, nz = p.z - qz, d = Math.hypot(nx, ny, nz);
  if (d >= r) return false;
  if (d < 1e-5){
    const ox = b.hx - Math.abs(p.x - b.cx), oy = b.hy - Math.abs(p.y - b.cy), oz = b.hz - Math.abs(p.z - b.cz);
    nx = ny = nz = 0;
    if (ox <= oy && ox <= oz){ nx = Math.sign(p.x - b.cx) || 1; p.x = b.cx + nx * (b.hx + r); }
    else if (oy <= oz){ ny = Math.sign(p.y - b.cy) || 1; p.y = b.cy + ny * (b.hy + r); }
    else { nz = Math.sign(p.z - b.cz) || 1; p.z = b.cz + nz * (b.hz + r); }
  } else { nx /= d; ny /= d; nz /= d; p.x = qx + nx * r; p.y = qy + ny * r; p.z = qz + nz * r; }
  const vn = v.x * nx + v.y * ny + v.z * nz;
  if (vn < 0){ const e = b.soft ? 0.05 : Math.min(e0, b.e + 0.2); v.x -= (1 + e) * vn * nx; v.y -= (1 + e) * vn * ny; v.z -= (1 + e) * vn * nz; if (b.soft) v.multiplyScalar(0.55); }
  return true;
}
function simpleStep(h){
  PHYS.pp = { x:cam.x, z:cam.z };
  socPreStep(h);
  const balls = PHYS.balls;
  for (const P of balls){
    if (P.held || P.sleep) continue;
    const r = P.def.r, p = P.p1, v = P.v;
    v.y -= 9.81 * h;
    p.addScaledVector(v, h);
    let ground = false;
    if (p.y <= r){ p.y = r; if (v.y < 0){ v.y = -v.y * (P.def.bounce + SOC_GE) / 2; if (v.y < 0.4) v.y = 0; v.x *= 0.92; v.z *= 0.92; } ground = true; }
    for (const b of PHYS.boxes) sphereBox(p, v, r, b, P.def.bounce);
    for (const c of PHYS.circles){
      if (p.y - r > c.h) continue;
      const dx = p.x - c.x, dz = p.z - c.z, rr = c.r + r, d2 = dx * dx + dz * dz;
      if (d2 >= rr * rr) continue;
      const d = Math.sqrt(d2) || 1e-4, nx = dx / d, nz = dz / d; p.x = c.x + nx * rr; p.z = c.z + nz * rr;
      const vn = v.x * nx + v.z * nz; if (vn < 0){ const e = 1 + Math.min(P.def.bounce, c.e + 0.2); v.x -= e * vn * nx; v.z -= e * vn * nz; }
    }
    const D = PHYS.dome, ddx = p.x - D.x, ddy = p.y - D.y, ddz = p.z - D.z, rr = D.r + r, dd2 = ddx * ddx + ddy * ddy + ddz * ddz;
    if (dd2 < rr * rr && p.y > D.y - 0.1){ const d = Math.sqrt(dd2) || 1e-4, nx = ddx / d, ny = ddy / d, nz = ddz / d; p.set(D.x + nx * rr, D.y + ny * rr, D.z + nz * rr); const vn = v.x * nx + v.y * ny + v.z * nz; if (vn < 0){ v.x -= 1.5 * vn * nx; v.y -= 1.5 * vn * ny; v.z -= 1.5 * vn * nz; } }
    /* Spin while it flies, roll when it's on the grass */
    if (ground && Math.abs(v.y) < 0.01) P.w.set(v.z / r, 0, -v.x / r);
    const wl = P.w.length(); if (wl > 1e-3){ _sa.copy(P.w).divideScalar(wl); _sq.setFromAxisAngle(_sa, wl * h); P.q1.premultiply(_sq); }
    const sp = Math.hypot(v.x, v.z);
    if (p.y < r + 0.01 && sp < 0.06 && Math.abs(v.y) < 0.01){ P.still += h; if (P.still > 0.5){ P.sleep = true; v.set(0, 0, 0); P.w.set(0, 0, 0); } } else P.still = 0;
  }
  for (let i = 0; i < balls.length; i++) for (let j = i + 1; j < balls.length; j++){
    const A = balls[i], B = balls[j];
    if (A.sleep && B.sleep) continue;
    const rr = A.def.r + B.def.r; _sv.subVectors(B.p1, A.p1); const d2 = _sv.lengthSq(); if (d2 >= rr * rr) continue;
    const d = Math.sqrt(d2) || 1e-4; _sv.divideScalar(d);
    const ma = A.mass, mb = B.mass, pen = rr - d;
    A.p1.addScaledVector(_sv, -pen * mb / (ma + mb)); B.p1.addScaledVector(_sv, pen * ma / (ma + mb));
    const rel = (B.v.x - A.v.x) * _sv.x + (B.v.y - A.v.y) * _sv.y + (B.v.z - A.v.z) * _sv.z;
    if (rel < 0){ const e = (A.def.bounce + B.def.bounce) / 2, jn = -(1 + e) * rel / (1 / ma + 1 / mb); A.v.addScaledVector(_sv, -jn / ma); B.v.addScaledVector(_sv, jn / mb); A.sleep = B.sleep = false; A.still = B.still = 0; }
  }
}
function physReset(P){
  P.resetAt = 0; P.held = false; P.nside = null; P.nslack = null; P.kickT = 0; if (P.w) P.w.set(0, 0, 0);
  if (P === SOC.ball){ SOC.inGoal = false; KEEP.hold = false; } P.p0.copy(P.home); P.p1.copy(P.home); P.q0.copy(P.homeQ); P.q1.copy(P.homeQ); P.v.set(0, 0, 0); P.sleep = true; P.still = 0;
  P.mesh.position.copy(P.home); P.mesh.quaternion.copy(P.homeQ);
  if (P.body){ const q = P.homeQ; P.body.setTranslation({ x:P.home.x, y:P.home.y, z:P.home.z }, false); P.body.setRotation({ x:q.x, y:q.y, z:q.z, w:q.w }, false); P.body.setLinvel({ x:0, y:0, z:0 }, false); P.body.setAngvel({ x:0, y:0, z:0 }, false); P.body.sleep(); }
}
function physRules(){
  for (const P of PHYS.props){
    const p = P.p1;
    if (P.resetAt && PHYS.t >= P.resetAt){ physReset(P); if (P.body) P.body.wakeUp(); continue; }
    if (P.held) continue;
    if (p.y < -2 || p.x < 33.5 || p.x > 92.5 || p.z < -9.2 || p.z > 26.5){ physReset(P); continue; }
  }
}
function physFrame(dt){
  if (!PHYS.loading) physLoad();
  if (!PHYS.mode) return false;
  PHYS.acc = Math.min(PHYS.acc + dt, PSTEP * 4);
  let stepped = false;
  while (PHYS.acc >= PSTEP){
    PHYS.acc -= PSTEP; PHYS.t += PSTEP; stepped = true;
    for (const P of PHYS.props){ P.p0.copy(P.p1); P.q0.copy(P.q1); }
    if (PHYS.mode === 'rapier') rapierStep(); else simpleStep(PSTEP);
    physRules();
  }
  const a = PHYS.acc / PSTEP;
  let awake = false;
  for (const P of PHYS.props){
    const moving = P.body ? !P.body.isSleeping() : !P.sleep;
    if (moving || stepped){
      P.mesh.position.lerpVectors(P.p0, P.p1, a); P.mesh.quaternion.slerpQuaternions(P.q0, P.q1, a);
      if (P.blob){ const m = P.mesh.position, y = Math.max(0, m.y - P.def.r), k = clamp(1 - y / 1.6, 0, 1); P.blob.position.set(m.x, 0.014, m.z); P.blob.scale.setScalar(P.def.r * (2.4 + y * 1.4)); P.blob.material.opacity = 0.75 * k * k; P.blob.visible = k > 0.02; }
    }
    if (moving || P.resetAt) awake = true;
  }
  return awake;
}
/* Tap a ball to kick it, a block to shove it */
function kickProp(id){
  const P = PHYS.byId[id]; if (!P) return;
  if (P.kind === 'ball'){ socTap(P); hideHint(); return; }
  const pos = P.mesh.position, dx = pos.x - cam.x, dz = pos.z - cam.z, d = Math.hypot(dx, dz) || 1;
  if (d > 3.4){
    walkTo(safeTarget({ x:pos.x - dx / d * 1.5, z:pos.z - dz / d * 1.5 }), { yaw:Math.atan2(-dx, -dz) });
    if (!kickProp.told){ kickProp.told = true; toast(P.kind === 'ball' ? 'Walk right into it, or tap it again up close to kick.' : 'Walk into the tower to knock it down.'); }
    return;
  }
  if (!PHYS.mode){ physLoad(); toast('Warming up the physics…'); return; }
  const fx = -Math.sin(cam.yaw), fz = -Math.cos(cam.yaw);
  let kx = dx / d + fx, kz = dz / d + fz; const kl = Math.hypot(kx, kz) || 1; kx /= kl; kz /= kl;
  const beach = P.def.skin === 'beach', sp = P.kind === 'ball' ? (beach ? 5.2 : 8.2) : 3.4, up = P.kind === 'ball' ? (beach ? 4.4 : 3.1) : 1.1;
  if (P.body){ P.body.wakeUp(); const m = P.body.mass(); P.body.applyImpulse({ x:kx * sp * m, y:up * m, z:kz * sp * m }, true); }
  else { P.v.set(kx * sp, up, kz * sp); P.sleep = false; P.still = 0; }
  wake();
}

/* ---------- Swings and the merry-go-round ---------- */
const SWING = { th:[0.2, -0.14, 0.09], om:[0, 0, 0], L:2.1, pz:null, px:null };
function swingsFrame(dt){
  if (!YA.swings.length || dt <= 0) return false;
  const pvx = SWING.px == null ? 0 : (cam.x - SWING.px) / dt, pvz = SWING.pz == null ? 0 : (cam.z - SWING.pz) / dt;
  SWING.px = cam.x; SWING.pz = cam.z;
  const g = 9.81 / SWING.L, n = Math.max(1, Math.ceil(dt / 0.01)), h = dt / n;
  let moving = false;
  YA.swings.forEach((pv, i) => {
    let th = SWING.th[i], om = SWING.om[i];
    const seatZ = pv.position.z - SWING.L * Math.sin(th), seatY = pv.position.y - SWING.L * Math.cos(th);
    if (!ride.on && Math.abs(cam.x - pv.position.x) < 0.42 && Math.abs(cam.z - seatZ) < 0.42 && seatY < 1.5 + PLAYER.y && Math.abs(pvz) < 20){
      /* The seat can't pass through you: it takes on your speed (pushing) or bounces off (blocking) */
      const c = Math.max(0.3, Math.cos(th)), seatV = -SWING.L * c * om, side = Math.sign(cam.z - seatZ) || 1;
      if ((seatV - pvz) * side > 0) om = -(pvz + (pvz - seatV) * 0.3) / (SWING.L * c);
    }
    for (let k = 0; k < n; k++){
      const wind = REDUCED ? 0 : 0.012 * Math.sin(amb.t * 2.16 + i * 1.7);
      om += (-g * Math.sin(th) - 0.07 * om + wind) * h; th += om * h;
    }
    SWING.th[i] = th; SWING.om[i] = om; pv.rotation.x = th;
    if (Math.abs(om) > 0.003 || Math.abs(th) > 0.003) moving = true;
  });
  return moving;
}
function pushSwing(i){
  const pv = YA.swings[i]; if (!pv) return;
  const th = SWING.th[i], seatZ = pv.position.z - SWING.L * Math.sin(th), d = Math.hypot(cam.x - pv.position.x, cam.z - seatZ);
  if (d > 3.2){ const s = cam.z > pv.position.z ? 1 : -1; walkTo(safeTarget({ x:pv.position.x, z:pv.position.z + s * 1.5 }), { yaw:s > 0 ? 0 : Math.PI }); return; }
  SWING.om[i] += (cam.z > seatZ ? 1 : -1) * 1.15;
  wake();
}
const SPIN = { w:0.45 };
function spinnerFrame(dt){
  if (!YA.spinner) return false;
  const idle = REDUCED ? 0 : 0.4;
  SPIN.w += (idle - SPIN.w) * (1 - Math.exp(-dt * 0.16));
  YA.spinner.rotation.y += SPIN.w * dt;
  return Math.abs(SPIN.w) > 0.01;
}
function spinSpinner(){
  const sx = YA.spinner.position.x, sz = YA.spinner.position.z, d = Math.hypot(cam.x - sx, cam.z - sz);
  if (d > 4.6){ walkTo(safeTarget({ x:sx + (cam.x - sx) / d * 2.7, z:sz + (cam.z - sz) / d * 2.7 }), { yaw:Math.atan2(-(sx - cam.x), -(sz - cam.z)) }); return; }
  SPIN.w = Math.min(SPIN.w + 1.4, 4.2); wake();
}

/* Everything that moves in the yard, while you can see it. Leaving the yard tidies it up. */
function yardPhysics(dt){
  const vis = !!(WING.play && WING.play.visible) && ride.on !== 'dive' && !document.hidden;
  if (vis !== PHYS.vis){
    PHYS.vis = vis; PHYS.pp = null; SWING.px = SWING.pz = null;
    if (!vis){ for (const P of PHYS.props) physReset(P); CONF.on = false; if (CONF.mesh) CONF.mesh.visible = false; socHide(); }
  }
  if (!vis) return false;
  let a = false;
  /* The keeper's pose comes first, so the physics sees where his gloves are */
  if (socFrame(dt)) a = true;
  if (swingsFrame(dt)) a = true;
  if (spinnerFrame(dt)) a = true;
  if (physFrame(dt)) a = true;
  if (confettiFrame(dt)) a = true;
  return a;
}
