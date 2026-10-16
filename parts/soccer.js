/* ================================================================
   Soccer in the Recess Yard. A size-5 ball flies with air drag and
   spin (it curls and dips), bounces and rolls like it does on grass,
   and the goal's net gives when it's hit. A keeper reads your shot
   and dives (socplay.js), and your own legs do the kicking.
   ================================================================ */
const SOC = { spot:{ x:79.1, z:-2.0 }, score:{ shots:0, goals:0, saves:0 }, shot:null, ball:null, nets:[], posts:[], board:null, t:0,
  pv:new THREE.Vector3(), pp:null, told:0, vis:false, postAt:0, ui:{}, inGoal:false };
const AIR_RHO = 1.2;
const _soA = new THREE.Vector3(), _soB = new THREE.Vector3(), _soC = new THREE.Vector3(), _soW = new THREE.Vector3(), _soP = new THREE.Vector3();
function socSm(a, b, x){ const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); }

/* ---------- The ball: a stitched 32-panel ball drawn in the shader, so it stays sharp up close ---------- */
function socBallMaterial(){
  const phi = (1 + Math.sqrt(5)) / 2, ico = [];
  for (const [a, b] of [[1, phi], [1, -phi], [-1, phi], [-1, -phi]]) ico.push(new THREE.Vector3(0, a, b), new THREE.Vector3(a, b, 0), new THREE.Vector3(b, 0, a));
  /* Pentagons sit on the icosahedron's corners, hexagons on its faces */
  const hex = [];
  for (let i = 0; i < 12; i++) for (let j = i + 1; j < 12; j++) for (let k = j + 1; k < 12; k++){
    const A = ico[i], B = ico[j], C = ico[k];
    if (Math.abs(A.distanceTo(B) - 2) < 1e-3 && Math.abs(A.distanceTo(C) - 2) < 1e-3 && Math.abs(B.distanceTo(C) - 2) < 1e-3) hex.push(new THREE.Vector3().add(A).add(B).add(C).normalize());
  }
  const pent = ico.map((v) => v.clone().normalize());
  const m = new THREE.MeshPhysicalMaterial({ color:0xffffff, roughness:0.42, metalness:0, clearcoat:0.28, clearcoatRoughness:0.35 });
  m.onBeforeCompile = (sh) => {
    sh.uniforms.uPent = { value:pent }; sh.uniforms.uHex = { value:hex };
    sh.vertexShader = 'varying vec3 vBallDir;\n' + sh.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\nvBallDir = position;');
    sh.fragmentShader = 'uniform vec3 uPent[12];\nuniform vec3 uHex[' + hex.length + '];\nvarying vec3 vBallDir;\n' + sh.fragmentShader
      .replace('#include <color_fragment>', `#include <color_fragment>
vec3 bdir = normalize(vBallDir);
float b1 = -2.0, b2 = -2.0, isPent = 0.0;
for (int i = 0; i < 12; i++){ float s = dot(bdir, uPent[i]) * 0.97418; if (s > b1){ b2 = b1; b1 = s; isPent = 1.0; } else if (s > b2) b2 = s; }
for (int i = 0; i < ${hex.length}; i++){ float s = dot(bdir, uHex[i]); if (s > b1){ b2 = b1; b1 = s; isPent = 0.0; } else if (s > b2) b2 = s; }
float edge = b1 - b2, fw = fwidth(edge);
float seam = 1.0 - smoothstep(0.0028, 0.0028 + max(fw * 1.6, 0.0035), edge);
vec3 panel = isPent > 0.5 ? vec3(0.03, 0.032, 0.036) : vec3(0.8, 0.79, 0.77);
diffuseColor.rgb *= panel * (1.0 - 0.58 * seam);`)
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\nroughnessFactor = mix(roughnessFactor, 0.85, seam);');
  };
  m.customProgramCacheKey = () => 'soc-ball';
  return m;
}
/* A soft dark spot under each ball, so it sits on the grass even without sun shadows */
function socBlob(){
  if (SOC.blobTex) return SOC.blobTex;
  const c = mk(64, 64), x = c.getContext('2d'), g = x.createRadialGradient(32, 32, 0, 32, 32, 32);
  g.addColorStop(0, 'rgba(0,0,0,0.5)'); g.addColorStop(0.55, 'rgba(0,0,0,0.22)'); g.addColorStop(1, 'rgba(0,0,0,0)');
  x.fillStyle = g; x.fillRect(0, 0, 64, 64);
  SOC.blobTex = new THREE.CanvasTexture(c);
  return SOC.blobTex;
}

/* ---------- Air and grass ---------- */
function socCd(d, s){ const c = d.cd; return c.length > 2 ? c[0] + (c[1] - c[0]) * socSm(c[2], c[3], s) : c[0]; }
/* Acceleration from the air: drag against the motion, and the Magnus lift that bends a spinning ball */
function socAero(d, v, w, out, noLift){
  const s = v.length(); out.set(0, 0, 0);
  if (s < 0.05) return out;
  const k = 0.5 * AIR_RHO * Math.PI * d.r * d.r / d.mass;
  out.copy(v).multiplyScalar(-k * socCd(d, s) * s);
  if (!noLift && w){
    _soA.crossVectors(w, v).multiplyScalar(k * d.cl * d.r);
    const cl = d.cl * d.r * w.length() / s;
    if (cl > 0.32) _soA.multiplyScalar(0.32 / cl);
    out.add(_soA);
  }
  return out;
}
/* Grass slows a rolling ball much more than the paved plaza and paths do */
function socGround(x, z){
  if ((x - 52) * (x - 52) + (z + 1.5) * (z + 1.5) < 47) return 0.32;
  if (x < 46.2 && z > -4.2 && z < -1.8) return 0.32;
  return 1;
}
function socRoll(d, p, v, w, h){
  const sp = Math.hypot(v.x, v.z);
  if (sp < 1e-5) return;
  const dec = (d.roll * socGround(p.x, p.z) + 0.05 * sp) * h, f = Math.max(0, sp - dec) / sp;
  v.x *= f; v.z *= f;
  if (w){ w.x *= f; w.z *= f; w.y *= Math.exp(-h * 3); }
}
const SOC_GE = 0.5;
/* Fly a ball forward without touching the real one: used to aim kicks and for the keeper's read */
function socSim(d, p0, v0, w0, maxT, noLift, fn){
  const p = _soP.copy(p0), v = _soB.copy(v0), w = _soW.copy(w0 || _soW.set(0, 0, 0)), h = 1 / 60, a = new THREE.Vector3(), e = (d.bounce + SOC_GE) / 2;
  for (let t = h; t <= maxT; t += h){
    const grounded = p.y < d.r + 0.012 && Math.abs(v.y) < 0.4;
    if (!grounded){ socAero(d, v, w, a, noLift); v.addScaledVector(a, h); v.y -= 9.81 * h; w.multiplyScalar(Math.exp(-h * 0.12)); }
    else { socAero(d, v, null, a, true); v.addScaledVector(a, h); socRoll(d, p, v, w, h); v.y = 0; }
    p.addScaledVector(v, h);
    if (p.y < d.r){ p.y = d.r; if (v.y < 0){ v.y = -v.y * e; if (v.y < 0.4) v.y = 0; v.x *= 0.9; v.z *= 0.9; } }
    if (fn(p, v, t)) return true;
    if (grounded && v.lengthSq() < 0.04) return false;
  }
  return false;
}

/* ---------- The pitch: chalk lines and mowing stripes in front of the goal ---------- */
function socBuildPitch(){
  const X0 = 70.5, X1 = 91.5, Z0 = -8.4, Z1 = 6.2, k = LEAN_CANVAS ? 36 : 48;
  const W = Math.round((X1 - X0) * k), H = Math.round((Z1 - Z0) * k), c = mk(W, H), x = c.getContext('2d');
  const P = (wx, wz) => [(wx - X0) * k, (wz - Z0) * k];
  for (let i = 0; i * 2.1 < X1 - X0; i++){ x.fillStyle = i % 2 ? 'rgba(236,255,200,0.075)' : 'rgba(10,40,6,0.085)'; x.fillRect(Math.round((X1 - X0 - (i + 1) * 2.1) * k), 0, Math.ceil(2.1 * k), H); }
  const g = GOAL;
  x.strokeStyle = 'rgba(250,250,242,0.92)'; x.lineWidth = 0.1 * k; x.lineJoin = 'miter';
  const rect = (ax, az, bx, bz) => { const [x0, y0] = P(ax, az), [x1, y1] = P(bx, bz); x.strokeRect(x0, y0, x1 - x0, y1 - y0); };
  x.beginPath(); x.moveTo(...P(g.x + 0.05, Z0 + 0.2)); x.lineTo(...P(g.x + 0.05, Z1 - 0.2)); x.stroke();
  rect(g.x - 2.2, g.z - 4.5, g.x + 0.05, g.z + 4.5);
  rect(g.x - 10, g.z - 6, g.x + 0.05, g.z + 6);
  const [sx, sy] = P(SOC.spot.x, SOC.spot.z);
  x.fillStyle = 'rgba(250,250,242,0.95)'; x.beginPath(); x.arc(sx, sy, 0.12 * k, 0, Math.PI * 2); x.fill();
  const ar = 4.6, a = Math.acos((g.x - 10 - SOC.spot.x) / ar);
  x.beginPath(); x.arc(sx, sy, ar * k, a, Math.PI * 2 - a); x.stroke();
  const t = tex(c, 8);
  const m = new THREE.Mesh(new THREE.PlaneGeometry(X1 - X0, Z1 - Z0), new THREE.MeshStandardMaterial({ map:t, transparent:true, depthWrite:false, roughness:0.9 }));
  m.rotation.x = -Math.PI / 2; m.position.set((X0 + X1) / 2, 0.009, (Z0 + Z1) / 2); m.receiveShadow = true; m.userData.noAO = true; m.renderOrder = -1;
  scene.add(m);
}

/* ---------- The goal: a white frame and a net that bulges where the ball hits ---------- */
function canvasNetCord(){
  const S = 64, c = mk(S, S), x = c.getContext('2d');
  x.strokeStyle = 'rgba(248,248,242,1)'; x.lineWidth = 4.2; x.strokeRect(0, 0, S, S);
  x.fillStyle = 'rgba(248,248,242,1)'; for (const [a, b] of [[0, 0], [S, 0], [0, S], [S, S]]){ x.beginPath(); x.arc(a, b, 4, 0, Math.PI * 2); x.fill(); }
  return c;
}
function socBuildGoal(){
  const g = GOAL, hw = g.w / 2, x0 = g.x, white = stdMat(0xf4f3ee, 0.32, 0.25);
  const bar = (ax, ay, az, bx, by, bz, r) => {
    const a = new THREE.Vector3(ax, ay, az), b = new THREE.Vector3(bx, by, bz), L = a.distanceTo(b);
    const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, L, r > 0.04 ? 16 : 10), white);
    m.position.copy(a).add(b).multiplyScalar(0.5); m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize());
    m.castShadow = true; scene.add(m); return m;
  };
  /* Posts and crossbar, then the frame that holds the net back */
  for (const s of [-1, 1]){
    bar(x0, 0, g.z + s * hw, x0, g.h, g.z + s * hw, g.pr);
    bar(x0, g.h, g.z + s * hw, x0 + g.dt, g.h, g.z + s * hw, 0.024);
    bar(x0 + g.dt, g.h, g.z + s * hw, x0 + g.d, 0.02, g.z + s * hw, 0.024);
    bar(x0, 0.02, g.z + s * hw, x0 + g.d, 0.02, g.z + s * hw, 0.02);
  }
  bar(x0, g.h, g.z - hw - g.pr, x0, g.h, g.z + hw + g.pr, g.pr);
  bar(x0 + g.dt, g.h, g.z - hw, x0 + g.dt, g.h, g.z + hw, 0.024);
  bar(x0 + g.d, 0.02, g.z - hw, x0 + g.d, 0.02, g.z + hw, 0.02);
  SOC.posts = [
    { a:new THREE.Vector3(x0, 0, g.z - hw), b:new THREE.Vector3(x0, g.h, g.z - hw) },
    { a:new THREE.Vector3(x0, 0, g.z + hw), b:new THREE.Vector3(x0, g.h, g.z + hw) },
    { a:new THREE.Vector3(x0, g.h, g.z - hw), b:new THREE.Vector3(x0, g.h, g.z + hw) }
  ];
  /* Net panels: back (sloped), top and two sides. Each knows its plane and where its edges are. */
  const cv = canvasNetCord(), cell = 0.12;
  const back = new THREE.Vector3(x0 + g.dt - (x0 + g.d), g.h, 0), bl = back.length();
  const panels = [
    { id:'back', o:new THREE.Vector3(x0 + g.d, 0, g.z), u:new THREE.Vector3(0, 0, 1), v:back.clone().normalize(), w:g.w, h:bl, u0:-hw, max:0.75, seg:[30, 13] },
    { id:'top', o:new THREE.Vector3(x0, g.h, g.z), u:new THREE.Vector3(0, 0, 1), v:new THREE.Vector3(1, 0, 0), w:g.w, h:g.dt, u0:-hw, max:0.45, seg:[30, 4] },
    { id:'sideA', o:new THREE.Vector3(x0, 0, g.z - hw), u:new THREE.Vector3(1, 0, 0), v:new THREE.Vector3(0, 1, 0), w:g.d, h:g.h, u0:0, max:0.45, seg:[10, 12], side:true },
    { id:'sideB', o:new THREE.Vector3(x0, 0, g.z + hw), u:new THREE.Vector3(1, 0, 0), v:new THREE.Vector3(0, 1, 0), w:g.d, h:g.h, u0:0, max:0.45, seg:[10, 12], side:true }
  ];
  for (const N of panels){
    N.n = new THREE.Vector3().crossVectors(N.u, N.v).normalize();
    /* Normals point out of the goal */
    const mid = new THREE.Vector3(x0 + g.d * 0.4, g.h * 0.45, g.z), toMid = mid.clone().sub(N.o);
    if (toMid.dot(N.n) > 0) N.n.negate();
    const [su, sv] = N.seg, geo = new THREE.PlaneGeometry(1, 1, su, sv), pos = geo.attributes.position, uv = geo.attributes.uv;
    N.base = new Float32Array(pos.count * 3); N.uvw = new Float32Array(pos.count * 3);
    for (let i = 0; i < pos.count; i++){
      let a = uv.getX(i) * N.w + N.u0, b = uv.getY(i) * N.h;
      /* Side panels are trapezoids: the back edge slopes in toward the top */
      if (N.side) a = uv.getX(i) * (g.d - (g.d - g.dt) * uv.getY(i));
      const p = N.o.clone().addScaledVector(N.u, a).addScaledVector(N.v, b);
      pos.setXYZ(i, p.x, p.y, p.z); N.base.set([p.x, p.y, p.z], i * 3);
      /* How far this vertex is from a fixed edge: the frame holds the net, so the bulge fades to zero there */
      const eu = N.side ? Math.min(a, (g.d - (g.d - g.dt) * uv.getY(i)) - a) : Math.min(a - N.u0, N.u0 + N.w - a), ev = Math.min(b, N.h - b);
      N.uvw[i * 3] = a; N.uvw[i * 3 + 1] = b; N.uvw[i * 3 + 2] = Math.min(eu, ev);
      uv.setXY(i, a / cell, b / cell);
    }
    geo.computeVertexNormals();
    const t = tex(cv); t.wrapS = t.wrapT = THREE.RepeatWrapping;
    const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ map:t, transparent:true, depthWrite:false, side:THREE.DoubleSide, roughness:0.9 }));
    mesh.userData.noAO = true; mesh.userData.noMerge = true; mesh.frustumCulled = false;
    scene.add(mesh);
    Object.assign(N, { mesh, A:0, Av:0, cu:0, cv:N.h * 0.5, pv:0, pt:-1, sgn:1, live:false });
  }
  SOC.nets = panels;
  /* Keep walkers out of the frame (you can still walk in through the mouth) */
  for (const s of [-1, 1]) for (let f = 0; f <= 1.001; f += 0.25) OBST.push({ x:x0 + g.d * f, z:g.z + s * hw, r:0.18, goal:1 });
  for (let f = -1; f <= 1.001; f += 0.2) OBST.push({ x:x0 + g.d, z:g.z + f * hw, r:0.18, goal:1 });
  socBuildBoard();
}
/* Where a point sits on a net panel, and whether it's inside the panel's outline */
function socNetLocal(N, p, out){
  _soC.subVectors(p, N.o);
  const a = _soC.dot(N.u), b = _soC.dot(N.v), dist = _soC.dot(N.n);
  let inside;
  if (N.side){ const g = GOAL, lim = g.d - (g.d - g.dt) * clamp(b / N.h, 0, 1); inside = b > -0.05 && b < N.h + 0.05 && a > -0.05 && a < lim + 0.05; }
  else inside = a > N.u0 - 0.05 && a < N.u0 + N.w + 0.05 && b > -0.05 && b < N.h + 0.05;
  out.a = a; out.b = b; out.d = dist; out.in = inside;
  return out;
}
const _soNL = { a:0, b:0, d:0, in:false };
/* The net is a stiff, damped spring that only pushes. It catches the ball and lets it drop. */
function socNetStep(P, p, v, w, h){
  /* The mesh stretches and stores a shot's energy, then goes slack: very little of it comes back */
  const r = P.def.r, K = 1200;
  if (!P.nside){ P.nside = SOC.nets.map(() => 0); P.nslack = SOC.nets.map(() => false); }
  let touched = false;
  SOC.nets.forEach((N, k) => {
    const L = socNetLocal(N, p, _soNL);
    if (!L.in || Math.abs(L.d) > r + N.max + 0.1){ P.nside[k] = 0; return; }
    if (!P.nside[k]) P.nside[k] = L.d < 0 ? -1 : 1;
    const s = P.nside[k], pen = s < 0 ? L.d + r : r - L.d;
    if (pen <= 0){ P.nslack[k] = false; return; }
    touched = true;
    /* vn: how fast the ball is going into the net. The push always points back the way it came. */
    const vn = -s * v.dot(N.n);
    if (vn <= 0) P.nslack[k] = true;
    let dv = (P.nslack[k] ? Math.max(0, 0.08 * K * pen + 40 * vn) : K * pen + 6 * vn) * h;
    /* At full stretch the ball stops; the spring never fires it back out in one step */
    if (!P.nslack[k] && dv > vn){ dv = Math.max(0, vn); P.nslack[k] = true; }
    v.addScaledVector(N.n, s * dv);
    if (pen > N.max){ p.addScaledVector(N.n, s * (pen - N.max)); const vv = -s * v.dot(N.n); if (vv > 0) v.addScaledVector(N.n, s * vv); }
    /* The mesh grips: sliding and spin die out quickly */
    const vnn = v.dot(N.n); _soA.copy(N.n).multiplyScalar(vnn); v.sub(_soA).multiplyScalar(Math.exp(-h * 22)).add(_soA);
    if (w) w.multiplyScalar(Math.exp(-h * 6));
    if (N.pt !== PHYS.t || pen > N.pv){ N.pv = pen; N.pt = PHYS.t; N.cu = L.a; N.cv = L.b; N.sgn = -s; }
    if (!P.netHit && Math.abs(vn) > 2.5){ P.netHit = true; sfxNet(Math.min(1, Math.abs(vn) / 18), p); }
  });
  if (!touched) P.netHit = false;
  return touched;
}
/* The bulge springs back with a little wobble after the ball drops out */
function socNetFrame(dt){
  let live = false;
  for (const N of SOC.nets){
    const target = PHYS.t - N.pt < PSTEP * 1.5 ? N.pv : 0;
    if (target > 0){ N.Av = (target - N.A) / Math.max(dt, 1e-3) * 0.5; N.A = target; }
    else if (Math.abs(N.A) > 1e-4 || Math.abs(N.Av) > 1e-3){ const n = Math.max(1, Math.ceil(dt / 0.008)), hh = dt / n; for (let i = 0; i < n; i++){ N.Av += (-900 * N.A - 20 * N.Av) * hh; N.A += N.Av * hh; } }
    else if (N.live){ N.A = 0; N.Av = 0; }
    const need = Math.abs(N.A) > 1e-4;
    if (!need && !N.live) continue;
    live = true; N.live = need;
    const pos = N.mesh.geometry.attributes.position, B = N.base, U = N.uvw, s2 = 2 * 0.36 * 0.36, nx = N.n.x * N.sgn, ny = N.n.y * N.sgn, nz = N.n.z * N.sgn;
    for (let i = 0; i < pos.count; i++){
      const du = U[i * 3] - N.cu, dv = U[i * 3 + 1] - N.cv, edge = Math.min(1, U[i * 3 + 2] / 0.3);
      const k = need ? N.A * Math.exp(-(du * du + dv * dv) / s2) * edge * edge * (3 - 2 * edge) : 0;
      pos.setXYZ(i, B[i * 3] + nx * k, B[i * 3 + 1] + ny * k, B[i * 3 + 2] + nz * k);
    }
    pos.needsUpdate = true;
  }
  return live;
}

/* ---------- Scoreboard by the goal ---------- */
function socBuildBoard(){
  const c = mk(512, 288), t = tex(c, 4);
  SOC.board = { c, t };
  const navy = stdMat(0x1d3b52, 0.55, 0.2), x = GOAL.x + 1.0, z = GOAL.z - GOAL.w / 2 - 2.8;
  for (const dz of [-0.55, 0.55]){ addCyl(0.04, 0.045, 2.35, navy, x, 1.175, z + dz, 10); }
  const back = addBox(0.05, 0.72, 1.3, navy, x + 0.03, 1.95, z);
  const face = addPlane(1.24, 0.66, new THREE.MeshBasicMaterial({ map:t, toneMapped:false }), x, 1.95, z, -Math.PI / 2);
  face.userData.keepBasic = true; back.castShadow = true;
  OBST.push({ x, z, r:0.75 });
  socDrawBoard();
}
function socDrawBoard(){
  const B = SOC.board; if (!B) return;
  const x = B.c.getContext('2d'), W = 512, H = 288, s = SOC.score;
  x.fillStyle = '#132a22'; x.fillRect(0, 0, W, H);
  x.strokeStyle = '#cda961'; x.lineWidth = 6; x.strokeRect(9, 9, W - 18, H - 18);
  x.fillStyle = '#cda961'; x.font = '700 30px ' + F.type; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.fillText('SHOOTOUT', W / 2, 46);
  const col = (cx, label, val, hue) => { x.fillStyle = hue; x.font = '700 104px ' + F.ui; x.fillText(String(val), cx, 150); x.fillStyle = '#efe7d5'; x.font = '600 26px ' + F.ui; x.fillText(label, cx, 228); };
  col(W * 0.27, 'GOALS', s.goals, '#f2c14e'); col(W * 0.73, 'SAVES', s.saves, '#9fd4ff');
  x.fillStyle = 'rgba(239,231,213,0.6)'; x.font = '400 21px ' + F.type; x.fillText(s.shots ? s.shots + (s.shots === 1 ? ' shot' : ' shots') : 'Penalty spot: 7.5 m', W / 2, 264);
  B.t.needsUpdate = true;
}

/* ---------- Sound: a kick's thump, bounces, the post's ring, the net, gloves, a whistle ---------- */
const SFX = { ctx:null, out:null, noise:null };
function sfxOn(){
  if (SFX.ctx){ if (SFX.ctx.state === 'suspended') SFX.ctx.resume().catch(() => {}); return SFX.ctx; }
  try {
    const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return null;
    const ctx = new AC(), out = ctx.createGain(); out.gain.value = 0.6;
    const comp = ctx.createDynamicsCompressor(); out.connect(comp); comp.connect(ctx.destination);
    const n = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate), d = n.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    Object.assign(SFX, { ctx, out, noise:n });
  } catch (e) { return null; }
  return SFX.ctx;
}
/* Quieter and panned the farther and more to the side it is */
function sfxAt(p){
  const ctx = SFX.ctx; if (!ctx || ctx.state !== 'running') return null;
  let g = 1, pan = 0;
  if (p){ const dx = p.x - cam.x, dz = p.z - cam.z, d = Math.hypot(dx, dz); g = 1 / (1 + d / 7); pan = clamp((dx * Math.cos(cam.yaw) - dz * Math.sin(cam.yaw)) / Math.max(1, d), -0.8, 0.8); }
  const gn = ctx.createGain(); gn.gain.value = g;
  if (ctx.createStereoPanner){ const sp = ctx.createStereoPanner(); sp.pan.value = pan; gn.connect(sp); sp.connect(SFX.out); } else gn.connect(SFX.out);
  return gn;
}
function sfxTone(dst, f0, f1, dur, vol, type, at){
  const ctx = SFX.ctx, t = ctx.currentTime + (at || 0), o = ctx.createOscillator(), g = ctx.createGain();
  o.type = type || 'sine'; o.frequency.setValueAtTime(f0, t); if (f1 !== f0) o.frequency.exponentialRampToValueAtTime(f1, t + dur);
  g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(vol, t + 0.004); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  o.connect(g); g.connect(dst); o.start(t); o.stop(t + dur + 0.02);
}
function sfxHiss(dst, f, q, dur, vol, kind, at){
  const ctx = SFX.ctx, t = ctx.currentTime + (at || 0), s = ctx.createBufferSource(), bp = ctx.createBiquadFilter(), g = ctx.createGain();
  s.buffer = SFX.noise; s.loop = true; bp.type = kind || 'bandpass'; bp.frequency.value = f; bp.Q.value = q;
  g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(vol, t + 0.006); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  s.connect(bp); bp.connect(g); g.connect(dst); s.start(t, Math.random() * 0.5); s.stop(t + dur + 0.02);
}
function sfxKick(p, at){ const d = sfxAt(at); if (!d) return; sfxTone(d, 150, 52, 0.12, 0.55 + 0.4 * p); sfxHiss(d, 1500, 1.1, 0.035, 0.18 + 0.32 * p); sfxHiss(d, 420, 0.9, 0.05, 0.2 + 0.2 * p); }
function sfxTap(at){ const d = sfxAt(at); if (!d) return; sfxTone(d, 120, 70, 0.07, 0.22); sfxHiss(d, 900, 1, 0.025, 0.08); }
function sfxBounce(k, at){ const d = sfxAt(at); if (!d) return; sfxTone(d, 115, 58, 0.09, 0.1 + 0.4 * k); sfxHiss(d, 700, 0.8, 0.03, 0.05 + 0.12 * k); }
function sfxPost(at){ const d = sfxAt(at); if (!d) return; for (const [f, v, t] of [[523, 0.22, 1.1], [1307, 0.12, 0.6], [2483, 0.07, 0.35], [3720, 0.04, 0.2]]) sfxTone(d, f, f * 0.995, t, v); sfxHiss(d, 3000, 0.7, 0.02, 0.2); }
function sfxNet(k, at){ const d = sfxAt(at); if (!d) return; sfxHiss(d, 3800, 0.5, 0.42, 0.06 + 0.2 * k, 'bandpass'); sfxHiss(d, 1200, 0.6, 0.18, 0.04 + 0.1 * k); }
function sfxGlove(k, at){ const d = sfxAt(at); if (!d) return; sfxHiss(d, 950, 0.8, 0.06, 0.2 + 0.3 * k); sfxTone(d, 190, 90, 0.07, 0.15 + 0.2 * k); }
function sfxWhistle(at){
  const d = sfxAt(at); if (!d) return;
  const ctx = SFX.ctx, t = ctx.currentTime, o = ctx.createOscillator(), lfo = ctx.createOscillator(), lg = ctx.createGain(), g = ctx.createGain();
  o.frequency.value = 2950; lfo.frequency.value = 26; lg.gain.value = 80; lfo.connect(lg); lg.connect(o.frequency);
  g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.09, t + 0.02); g.gain.setValueAtTime(0.09, t + 0.3); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.42);
  o.connect(g); g.connect(d); o.start(t); lfo.start(t); o.stop(t + 0.45); lfo.stop(t + 0.45);
}

/* ---------- Every physics step: air, grass, net, your feet, the keeper's hands ---------- */
const _soPP = new THREE.Vector3(), _soPV = new THREE.Vector3(), _soPW = new THREE.Vector3(), _soPA = new THREE.Vector3();
function socPreStep(h){
  for (const P of PHYS.balls){
    const b = P.body, d = P.def;
    if (b){ const t = b.translation(), lv = b.linvel(), av = b.angvel(); _soPP.set(t.x, t.y, t.z); _soPV.set(lv.x, lv.y, lv.z); _soPW.set(av.x, av.y, av.z); }
    else { _soPP.copy(P.p1); _soPV.copy(P.v); _soPW.copy(P.w || _soPW.set(0, 0, 0)); }
    if (P.held){
      const hp = keeperHoldPoint(); if (!hp){ P.held = false; continue; }
      _soPP.copy(hp); _soPV.set(0, 0, 0); _soPW.set(0, 0, 0);
      if (b){ b.setTranslation(_soPP, true); b.setLinvel(_soPV, true); b.setAngvel(_soPW, true); } else { P.p1.copy(_soPP); P.v.set(0, 0, 0); P.sleep = false; }
      continue;
    }
    const asleep = b ? b.isSleeping() : P.sleep;
    let changed = false;
    if (socBodyContact(P, _soPP, _soPV, _soPW, h)) changed = true;
    if (asleep && !changed) continue;
    const grounded = _soPP.y < d.r + 0.015 && Math.abs(_soPV.y) < 0.4;
    socAero(d, _soPV, grounded ? null : _soPW, _soPA, grounded);
    _soPV.addScaledVector(_soPA, h);
    if (grounded) socRoll(d, _soPP, _soPV, _soPW, h);
    else _soPW.multiplyScalar(Math.exp(-h * 0.12));
    if (_soPP.x > GOAL.x - 0.5 && _soPP.x < GOAL.x + GOAL.d + 1 && Math.abs(_soPP.z - GOAL.z) < GOAL.w / 2 + 1 && _soPP.y < GOAL.h + 1.2) socNetStep(P, _soPP, _soPV, _soPW, h);
    if (b){ if (changed) b.setTranslation(_soPP, true); b.setLinvel(_soPV, changed); b.setAngvel(_soPW, changed); }
    else { P.p1.copy(_soPP); P.v.copy(_soPV); if (!P.w) P.w = new THREE.Vector3(); P.w.copy(_soPW); if (changed){ P.sleep = false; P.still = 0; } }
  }
}
/* Walking into a ball nudges it ahead of you, which is how dribbling works */
function socBodyContact(P, p, v, w, h){
  if (ride.on || !SOC.vis || PLAYER.y > 0.6) return false;
  if (P.kickT && PHYS.t - P.kickT < 0.45) return false;
  if (KICK.st === 'run' && P === KICK.ball) return false;
  const r = P.def.r, R0 = 0.24, rr = r + R0, dx = p.x - cam.x, dz = p.z - cam.z, d2 = dx * dx + dz * dz;
  if (d2 > rr * rr || p.y - r > PLAYER.y + 1.6) return false;
  const d = Math.sqrt(d2) || 1e-4, nx = dx / d, nz = dz / d;
  p.x = cam.x + nx * rr; p.z = cam.z + nz * rr;
  const pvx = SOC.pv.x, pvz = SOC.pv.z, rel = (v.x - pvx) * nx + (v.z - pvz) * nz;
  if (rel < 0){
    v.x -= 1.3 * rel * nx; v.z -= 1.3 * rel * nz;
    const ps = Math.hypot(pvx, pvz);
    if (ps > 0.6){ const fx = pvx / ps, fz = pvz / ps, ahead = v.x * fx + v.z * fz, want = Math.min(ps * 1.22, 7); if (ahead < want && fx * nx + fz * nz > 0.3){ v.x += fx * (want - ahead); v.z += fz * (want - ahead); } }
    if (p.y < r + 0.05 && v.y < 0) v.y = 0;
    w.set(v.z / r, 0, -v.x / r);
    if (-rel > 0.7 && PHYS.t - (P.touchT || 0) > 0.22){ P.touchT = PHYS.t; bodyTouch(nx * Math.cos(cam.yaw) - nz * Math.sin(cam.yaw)); sfxTap(p); }
  }
  return true;
}
/* After each step: the keeper's body and gloves, goal-line checks, bounce and post sounds */
function socPostStep(h){
  for (const P of PHYS.balls){
    if (P.held) continue;
    const b = P.body;
    if (b && b.isSleeping()) continue;
    const lv = b ? b.linvel() : P.v;
    const p0 = P.p0, p1 = P.p1, r = P.def.r;
    if (KEEP.fig && KEEP.fig.mesh && KEEP.caps.length && p1.x > GOAL.x - 7 && Math.abs(p1.z - GOAL.z) < 6) keeperCollide(P, p0, p1, lv);
    /* Bounces */
    const vy = b ? b.linvel().y : P.v.y;
    if (P.lvy != null && P.lvy < -1.4 && vy > -0.05 && p1.y < r + 0.06) sfxBounce(Math.min(1, -P.lvy / 9), p1);
    P.lvy = vy;
    /* The posts and crossbar ring when they're hit */
    if (p1.x > GOAL.x - 0.6 && p1.x < GOAL.x + 0.6 && PHYS.t - SOC.postAt > 0.3){
      for (const s of SOC.posts){ if (socSegDist(p1, s.a, s.b) < r + GOAL.pr + 0.03){ SOC.postAt = PHYS.t; sfxPost(p1); if (SOC.shot && SOC.shot.P === P) SOC.shot.post = true; break; } }
    }
    /* Goal: the whole ball over the line, between the posts and under the bar */
    if (p0.x <= GOAL.x + r && p1.x > GOAL.x + r && Math.abs(p1.z - GOAL.z) < GOAL.w / 2 - 0.02 && p1.y < GOAL.h - 0.02) socGoal(P);
  }
}
function socSegDist(p, a, b){
  _soA.subVectors(b, a); const t = clamp(_soB.subVectors(p, a).dot(_soA) / _soA.lengthSq(), 0, 1);
  return _soC.copy(a).addScaledVector(_soA, t).distanceTo(p);
}

/* ---------- Shots, goals and saves ---------- */
function socShotStart(P, v){
  /* Will it reach the goal? Fly it forward to the goal line to find out */
  let hit = null;
  socSim(P.def, P.p1, v, P.kickW, 3, false, (p, vv, t) => { if (p.x >= GOAL.x){ hit = { z:p.z, y:p.y, t }; return true; } return false; });
  const on = !!hit && Math.abs(hit.z - GOAL.z) < GOAL.w / 2 + 1.6 && hit.y < GOAL.h + 1.6;
  SOC.shot = on ? { P, t0:SOC.t, hit, onTarget:Math.abs(hit.z - GOAL.z) < GOAL.w / 2 && hit.y < GOAL.h, post:false, touched:false, done:false } : null;
  return SOC.shot;
}
function socGoal(P){
  if (P !== SOC.ball){
    if (P.resetAt) return;
    P.resetAt = PHYS.t + 2.6; confettiBurst(GOAL.x + 0.3, 1.0, GOAL.z); toast('GOAL! Even with a ' + P.name.toLowerCase() + '.'); award('striker'); return;
  }
  if (SOC.inGoal) return;
  SOC.inGoal = true;
  const sh = SOC.shot;
  SOC.score.goals++; if (sh && !sh.done){ SOC.score.shots++; sh.done = true; }
  socDrawBoard();
  confettiBurst(GOAL.x + 0.3, 1.0, GOAL.z); sfxWhistle(); keeperBeaten();
  const s = SOC.score, line = s.goals + (s.goals === 1 ? ' goal' : ' goals') + ' from ' + s.shots + (s.shots === 1 ? ' shot' : ' shots') + '.';
  toast((sh && sh.post ? 'GOAL! In off the post. ' : sh && sh.touched ? 'GOAL! Through the keeper’s gloves. ' : 'GOAL! ') + line);
  award('striker');
  SOC.shot = null;
}
/* Decide how a shot ended once the ball has settled, gone wide or been saved */
function socShotFrame(){
  const sh = SOC.shot; if (!sh || sh.done) return;
  const P = sh.P, p = P.p1, b = P.body, v = b ? b.linvel() : P.v, sp = Math.hypot(v.x, v.y, v.z), age = SOC.t - sh.t0;
  let out = '';
  if (P.held) out = 'save';
  else if (sh.touched && (v.x < -0.5 || sp < 1.2 || age > 2.2)) out = 'save';
  else if (p.x > GOAL.x + P.def.r + 0.05 && !SOC.inGoal) out = p.y > GOAL.h - 0.1 && Math.abs(p.z - GOAL.z) < GOAL.w / 2 + 0.6 ? 'over' : 'wide';
  else if ((sp < 0.6 && age > 0.8) || age > 4.5) out = sh.post ? 'post' : 'short';
  if (!out) return;
  sh.done = true; SOC.shot = null; SOC.score.shots++;
  if (out === 'save'){ SOC.score.saves++; keeperSaved(); toast(P.held ? 'Saved! He held on to that one.' : 'Saved! He got a glove to it.'); }
  else if (out === 'over') toast(sh.post ? 'Off the bar and over!' : 'Over the bar.');
  else if (out === 'wide') toast(sh.post ? 'Off the post and wide!' : 'Just wide.');
  else if (out === 'post') toast('Off the post!');
  else toast('Not enough on it. Hit it harder.');
  socDrawBoard();
}
