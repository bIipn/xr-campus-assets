/* ================================================================
   Campus layout and movement
   ================================================================ */
const M_WALL = 0.45;
const ROOMS = [
  { id:'lobby', x0:-6, x1:6, z0:-6, z1:0 },
  { id:'g1', x0:-6, x1:6, z0:-18, z1:-6, gal:1 },
  { id:'g2', x0:-6, x1:6, z0:-30, z1:-18, gal:2 },
  { id:'g3', x0:-6, x1:6, z0:-42, z1:-30, gal:3 },
  { id:'wax', x0:-8.5, x1:8.5, z0:-81, z1:-42.3 },
  { id:'hallL', x0:-12, x1:-6, z0:-4.6, z1:-1.4 },
  { id:'lib', x0:-23, x1:-12.45, z0:-12.55, z1:6.55 },
  { id:'libAisle', x0:-32, x1:-23, z0:-5.2, z1:-0.8 },
  { id:'hallR', x0:6, x1:12, z0:-4.6, z1:-1.4 },
  { id:'school', x0:12, x1:34, z0:-4.33, z1:-1.67 },
  { id:'studio', x0:14, x1:24, z0:-13, z1:-4.75 },
  { id:'lab', x0:25.6, x1:34, z0:-13, z1:-4.75 },
  { id:'blueprint', x0:12.2, x1:24, z0:-1.25, z1:7 },
  { id:'world', x0:24, x1:34, z0:-1.25, z1:7 },
  { id:'yard', x0:34, x1:92, z0:-34, z1:26 }
];
/* The coaster's ground outside; it starts at the school's back wall so the Science Lab stays walkable */
const NOGO = [{ x0:34, x1:94, z0:-36, z1:-8.15 },
  /* Wax Hall stages behind their ropes, and the intro wall */
  { x0:4.3, x1:9, z0:-74.85, z1:-45.0 }, { x0:-9, x1:-4.3, z0:-74.85, z1:-45.0 }, { x0:-9, x1:9, z0:-81.5, z1:-76.88 }, { x0:-3.25, x1:3.25, z0:-44.85, z1:-44.35 }];
const ROOM = {}; ROOMS.forEach((r) => ROOM[r.id] = r);
const ROOM_INFO = {
  lobby:{ k:'Lobby', n:'XRLibraries Campus', y:'Museum ahead · Library left · School right' },
  hallL:{ k:'Hall', n:'To the Library', y:'Reading room ahead' },
  lib:{ k:'Library', n:'The Reading Room', y:'Tap a book on display to read it' },
  libAisle:{ k:'Library', n:'The Stacks', y:'Eight sections · Books on every end' },
  hallR:{ k:'Hall', n:'To the Workshop School', y:'Every class is a workshop' },
  school:{ k:'Workshop School', n:'Main Hall', y:'Rooms 101–104 are open · Recess Yard out back' },
  studio:{ k:'Room 101', n:'3D Art Studio', y:'Brushes, shapes and a blank canvas' },
  lab:{ k:'Room 102', n:'Science Lab', y:'Sieve test · Titration · Pendulum' },
  blueprint:{ k:'Room 103', n:'Blueprint Lab', y:'Five blueprints · Model bench' },
  world:{ k:'Room 104', n:'World Builder Studio', y:'How a world like this gets built' },
  yard:{ k:'Recess Yard', n:'The Playground', y:'Coaster · Sky Drop · Ocean Dive' },
  wax:{ k:'Museum · Living History', n:'The Wax Hall', y:'Walk up to a scene and it comes to life' }
};
const DOORS = [
  { axis:'z', at:-6, c:0, w:3.2 }, { axis:'z', at:-18, c:0, w:3.2 }, { axis:'z', at:-30, c:0, w:3.2 }, { axis:'z', at:-42.15, c:0, w:3.2, band:0.75 },
  { axis:'x', at:-6, c:-3, w:2.4 }, { axis:'x', at:-12, c:-3, w:3.2, band:1.0 }, { axis:'x', at:-23, c:-3, w:4.4 },
  { axis:'x', at:6, c:-3, w:2.4 }, { axis:'x', at:12, c:-3, w:3.2 },
  { axis:'z', at:-4.75, c:19, w:1.8, band:1.0 },
  { axis:'z', at:-4.75, c:29, w:1.8, band:1.0 },
  { axis:'z', at:-1.25, c:19, w:1.8, band:1.0 },
  { axis:'z', at:-1.25, c:29, w:1.8, band:1.0 },
  { axis:'x', at:34, c:-3, w:2.4, band:1.0 }
];
function inRect(x, z, x0, x1, z0, z1){ return x >= x0 && x <= x1 && z >= z0 && z <= z1; }
function walkable(x, z){
  for (const g of NOGO) if (inRect(x, z, g.x0, g.x1, g.z0, g.z1)) return false;
  for (const r of ROOMS) if (inRect(x, z, r.x0 + M_WALL, r.x1 - M_WALL, r.z0 + M_WALL, r.z1 - M_WALL)) return true;
  for (const d of DOORS){
    const lo = d.c - d.w / 2 + 0.35, hi = d.c + d.w / 2 - 0.35, b = d.band || 0.6;
    if (d.axis === 'z' ? inRect(x, z, lo, hi, d.at - b, d.at + b) : inRect(x, z, d.at - b, d.at + b, lo, hi)) return true;
  }
  return false;
}
function freeAt(x, z, pad){
  if (!walkable(x, z)) return false;
  pad = pad || 0;
  for (const o of OBST){ const dx = x - o.x, dz = z - o.z, rr = o.r + pad; if (dx * dx + dz * dz < rr * rr) return false; }
  return true;
}
function roomAt(x, z){
  let best = ROOMS[0], bd = Infinity;
  for (const r of ROOMS){
    const dx = Math.max(r.x0 - x, 0, x - r.x1), dz = Math.max(r.z0 - z, 0, z - r.z1), d = Math.hypot(dx, dz);
    if (d < bd - 1e-9){ bd = d; best = r; }
  }
  return best;
}

/* Grid for path finding */
const NAV = { x0:-33, z0:-82, cs:0.25, nx:0, nz:0, free:null, run:0 };
function buildNav(){
  NAV.nx = Math.ceil((93 - NAV.x0) / NAV.cs); NAV.nz = Math.ceil((27 - NAV.z0) / NAV.cs);
  const N = NAV.nx * NAV.nz;
  NAV.free = new Uint8Array(N); NAV.g = new Float32Array(N); NAV.par = new Int32Array(N); NAV.stamp = new Uint32Array(N); NAV.closed = new Uint32Array(N);
  for (let j = 0; j < NAV.nz; j++) for (let i = 0; i < NAV.nx; i++){
    const x = NAV.x0 + (i + 0.5) * NAV.cs, z = NAV.z0 + (j + 0.5) * NAV.cs;
    NAV.free[j * NAV.nx + i] = freeAt(x, z, 0.08) ? 1 : 0;
  }
}
function cellIdx(x, z){ const i = Math.floor((x - NAV.x0) / NAV.cs), j = Math.floor((z - NAV.z0) / NAV.cs); if (i < 0 || j < 0 || i >= NAV.nx || j >= NAV.nz) return -1; return j * NAV.nx + i; }
function cellCenter(k){ const i = k % NAV.nx, j = (k / NAV.nx) | 0; return { x:NAV.x0 + (i + 0.5) * NAV.cs, z:NAV.z0 + (j + 0.5) * NAV.cs }; }
function freeGrid(x, z){ const k = cellIdx(x, z); return k >= 0 && NAV.free[k] === 1; }
function lineFree(a, b){
  const L = Math.hypot(b.x - a.x, b.z - a.z), n = Math.max(1, Math.ceil(L / 0.1));
  for (let k = 0; k <= n; k++){ const t = k / n; if (!freeGrid(a.x + (b.x - a.x) * t, a.z + (b.z - a.z) * t)) return false; }
  return true;
}
function nearestFree(x, z){
  const k0 = cellIdx(x, z);
  if (k0 >= 0 && NAV.free[k0]) return k0;
  const ci = Math.floor((x - NAV.x0) / NAV.cs), cj = Math.floor((z - NAV.z0) / NAV.cs);
  let best = -1, bd = Infinity;
  for (let rad = 1; rad <= 24 && best < 0; rad++){
    for (let dj = -rad; dj <= rad; dj++) for (let di = -rad; di <= rad; di++){
      if (Math.max(Math.abs(di), Math.abs(dj)) !== rad) continue;
      const i = ci + di, j = cj + dj; if (i < 0 || j < 0 || i >= NAV.nx || j >= NAV.nz) continue;
      const k = j * NAV.nx + i; if (!NAV.free[k]) continue;
      const c = cellCenter(k), d = (c.x - x) ** 2 + (c.z - z) ** 2; if (d < bd){ bd = d; best = k; }
    }
  }
  return best;
}
function astar(s, g){
  const nx = NAV.nx, run = ++NAV.run, G = NAV.g, P = NAV.par, S = NAV.stamp, C = NAV.closed, F = NAV.free;
  const gx = g % nx, gz = (g / nx) | 0;
  const h = (k) => { const dx = Math.abs(k % nx - gx), dz = Math.abs(((k / nx) | 0) - gz); return (dx + dz + (1.4142 - 2) * Math.min(dx, dz)); };
  const hk = [], hf = [];
  const push = (k, f) => { hk.push(k); hf.push(f); let i = hk.length - 1; while (i > 0){ const p = (i - 1) >> 1; if (hf[p] <= hf[i]) break; [hk[p], hk[i]] = [hk[i], hk[p]]; [hf[p], hf[i]] = [hf[i], hf[p]]; i = p; } };
  const pop = () => { const top = hk[0], lk = hk.pop(), lf = hf.pop(); if (hk.length){ hk[0] = lk; hf[0] = lf; let i = 0; for (;;){ const l = 2 * i + 1, r = l + 1; let m = i; if (l < hk.length && hf[l] < hf[m]) m = l; if (r < hk.length && hf[r] < hf[m]) m = r; if (m === i) break; [hk[m], hk[i]] = [hk[i], hk[m]]; [hf[m], hf[i]] = [hf[i], hf[m]]; i = m; } } return top; };
  G[s] = 0; S[s] = run; P[s] = -1; push(s, h(s));
  const DIRS = [[1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1], [1, 1, 1.4142], [1, -1, 1.4142], [-1, 1, 1.4142], [-1, -1, 1.4142]];
  let found = false, guard = 0;
  while (hk.length && guard++ < 200000){
    const cur = pop();
    if (C[cur] === run) continue;
    C[cur] = run;
    if (cur === g){ found = true; break; }
    const ci = cur % nx, cj = (cur / nx) | 0;
    for (const [di, dj, cost] of DIRS){
      const i = ci + di, j = cj + dj; if (i < 0 || j < 0 || i >= nx || j >= NAV.nz) continue;
      const k = j * nx + i; if (!F[k] || C[k] === run) continue;
      if (di && dj && (!F[cj * nx + i] || !F[j * nx + ci])) continue;
      const ng = G[cur] + cost;
      if (S[k] !== run || ng < G[k]){ S[k] = run; G[k] = ng; P[k] = cur; push(k, ng + h(k)); }
    }
  }
  if (!found) return null;
  const out = []; for (let k = g; k !== -1; k = P[k]) out.push(k);
  return out.reverse();
}
function planPath(from, to){
  const goal = { x:to.x, z:to.z };
  if (lineFree(from, goal)) return [goal];
  const s = nearestFree(from.x, from.z), g = nearestFree(goal.x, goal.z);
  if (s < 0 || g < 0) return [goal];
  const cells = astar(s, g);
  if (!cells) return [goal];
  const pts = cells.map(cellCenter);
  if (freeAt(goal.x, goal.z, 0)) pts.push(goal);
  const out = []; let anchor = { x:from.x, z:from.z }, last = pts[0];
  for (let i = 1; i < pts.length; i++){ if (!lineFree(anchor, pts[i])){ out.push(last); anchor = last; } last = pts[i]; }
  out.push(last);
  return out;
}
function safeTarget(t){
  if (freeAt(t.x, t.z, 0.05)) return { x:t.x, z:t.z };
  const k = nearestFree(t.x, t.z);
  return k >= 0 ? cellCenter(k) : { x:cam.x, z:cam.z };
}

let path = [], speed = 3, faceYaw = null, facePitch = null, travelFace = false;
const keys = new Set();
/* Player feel: smooth starts and stops, sprint, jump, landing dip and a little head bob */
const PLAYER = { vx:0, vz:0, y:0, vy:0, ground:true, jump:false, sprint:false, phase:0, amp:0, bob:0, dip:0, dipV:0, px:null, pz:null, sp:0 };
const JOY = { on:false, x:0, y:0 };
/* An extra camera offset: during a kick the camera rides with your head as it leans over the ball */
const CAMX = { x:0, y:0, z:0 };
const WALK_SP = 3.0, RUN_SP = 5.6, GRAV = 16, JUMP_V = 5.2;
function eyeY(){ return EYE + PLAYER.y + PLAYER.bob + PLAYER.dip; }
function requestJump(){ if (ride.on || paint.on || !THREEOK) return false; PLAYER.jump = true; wake(); return true; }
function playerFrame(dt){
  let active = false;
  if (PLAYER.jump){ PLAYER.jump = false; if (PLAYER.ground){ PLAYER.vy = JUMP_V; PLAYER.ground = false; } }
  if (!PLAYER.ground){
    active = true;
    PLAYER.vy -= GRAV * dt; PLAYER.y += PLAYER.vy * dt;
    if (PLAYER.y <= 0){ const hit = -PLAYER.vy; PLAYER.y = 0; PLAYER.vy = 0; PLAYER.ground = true; if (!REDUCED) PLAYER.dipV -= Math.min(0.8, hit * 0.1); }
  }
  if (PLAYER.dip || PLAYER.dipV){
    active = true;
    PLAYER.dipV += (-110 * PLAYER.dip - 15 * PLAYER.dipV) * dt; PLAYER.dip += PLAYER.dipV * dt;
    if (Math.abs(PLAYER.dip) < 0.0004 && Math.abs(PLAYER.dipV) < 0.004){ PLAYER.dip = 0; PLAYER.dipV = 0; }
  }
  /* Measured speed drives the bob, whichever way you are moving */
  if (PLAYER.px != null && dt > 0) PLAYER.sp = lerp(PLAYER.sp, Math.min(8, Math.hypot(cam.x - PLAYER.px, cam.z - PLAYER.pz) / dt), 1 - Math.exp(-dt * 10));
  PLAYER.px = cam.x; PLAYER.pz = cam.z;
  const want = !REDUCED && PLAYER.ground && PLAYER.sp > 0.4 ? Math.min(1, PLAYER.sp / WALK_SP) : 0;
  PLAYER.amp = lerp(PLAYER.amp, want, 1 - Math.exp(-dt * 6));
  if (PLAYER.amp > 0.002){ PLAYER.phase += dt * Math.max(PLAYER.sp, 1.2) / 1.55; PLAYER.bob = Math.sin(PLAYER.phase * Math.PI * 2) * 0.026 * PLAYER.amp; active = true; }
  else if (PLAYER.bob){ PLAYER.bob = 0; PLAYER.amp = 0; }
  return active;
}
function angDiff(a, b){ let d = b - a; while (d > Math.PI) d -= Math.PI * 2; while (d < -Math.PI) d += Math.PI * 2; return d; }
function lerpAngle(a, b, t){ return a + angDiff(a, b) * t; }
function remaining(){ let L = 0, px = cam.x, pz = cam.z; for (const p of path){ L += Math.hypot(p.x - px, p.z - pz); px = p.x; pz = p.z; } return L; }
function walkTo(target, opts){
  opts = opts || {};
  path = planPath(cam, target);
  const L = remaining();
  speed = clamp(L / 2.3, 2.4, 12);
  faceYaw = opts.yaw == null ? null : opts.yaw;
  facePitch = opts.pitch == null ? null : opts.pitch;
  travelFace = faceYaw != null && L > 4;
  if (REDUCED){ cam.x = target.x; cam.z = target.z; path = []; if (faceYaw != null) cam.yaw = faceYaw; if (facePitch != null) cam.pitch = facePitch; faceYaw = facePitch = null; }
  wake();
}
function goView(v){ if (v) walkTo({ x:v.x, z:v.z }, { yaw:v.yaw, pitch:v.pitch }); }
function constrain(px, pz, nx, nz){
  let x = nx, z = nz;
  if (!freeAt(x, z)){ if (freeAt(nx, pz)) z = pz; else if (freeAt(px, nz)) x = px; else { x = px; z = pz; } }
  return [x, z];
}
function update(dt){
  /* A kick's run-up moves you; the keys and stick wait until the strike is done */
  if (KICK.drive){ path.length = 0; PLAYER.vx = PLAYER.vz = 0; playerFrame(dt); return true; }
  let active = false;
  if (path.length){
    active = true;
    const rem = remaining();
    const sp = rem < 1.3 ? Math.max(0.7, speed * rem / 1.3) : speed;
    const tgt = path[0], dx = tgt.x - cam.x, dz = tgt.z - cam.z, d = Math.hypot(dx, dz), st = sp * dt;
    if (d <= st){ cam.x = tgt.x; cam.z = tgt.z; path.shift(); }
    else { cam.x += dx / d * st; cam.z += dz / d * st; }
    if (travelFace && rem > 1.8 && d > 0.05) cam.yaw = lerpAngle(cam.yaw, Math.atan2(-dx, -dz), 1 - Math.exp(-dt * 3));
  }
  if (faceYaw != null && (!travelFace || !path.length || remaining() < 1.8)){
    cam.yaw = lerpAngle(cam.yaw, faceYaw, 1 - Math.exp(-dt * 4.5)); active = true;
    if (!path.length && Math.abs(angDiff(cam.yaw, faceYaw)) < 0.002){ cam.yaw = faceYaw; faceYaw = null; }
  }
  if (facePitch != null){
    cam.pitch = lerp(cam.pitch, facePitch, 1 - Math.exp(-dt * 4.5)); active = true;
    if (!path.length && Math.abs(cam.pitch - facePitch) < 0.002){ cam.pitch = facePitch; facePitch = null; }
  }
  /* Keys and the touch stick set a target velocity; the body eases toward it */
  let f = 0, s = 0, t = 0;
  if (keys.size){
    if (keys.has('w') || keys.has('arrowup')) f += 1;
    if (keys.has('s') || keys.has('arrowdown')) f -= 1;
    if (keys.has('a')) s -= 1;
    if (keys.has('d')) s += 1;
    if (keys.has('arrowleft') || keys.has('q')) t += 1;
    if (keys.has('arrowright') || keys.has('e')) t -= 1;
    cam.yaw += t * 1.7 * dt;
    if (t) active = true;
  }
  if (JOY.on){ f -= JOY.y; s += JOY.x; }
  const mag = Math.min(1, Math.hypot(f, s));
  let tvx = 0, tvz = 0;
  if (mag > 0.04){
    path = []; faceYaw = facePitch = null; travelFace = false;
    const n = Math.hypot(f, s), top = (PLAYER.sprint || (JOY.on && mag > 0.97)) ? RUN_SP : WALK_SP;
    const fx = -Math.sin(cam.yaw), fz = -Math.cos(cam.yaw), rx = Math.cos(cam.yaw), rz = -Math.sin(cam.yaw);
    tvx = (fx * f + rx * s) / n * top * mag; tvz = (fz * f + rz * s) / n * top * mag;
  }
  if (mag > 0.04 || Math.abs(PLAYER.vx) + Math.abs(PLAYER.vz) > 0.01){
    active = true;
    const a = 1 - Math.exp(-dt * (PLAYER.ground ? (mag > 0.04 ? 10 : 14) : 2.5));
    PLAYER.vx += (tvx - PLAYER.vx) * a; PLAYER.vz += (tvz - PLAYER.vz) * a;
    if (Math.abs(PLAYER.vx) + Math.abs(PLAYER.vz) < 0.01 && mag <= 0.04){ PLAYER.vx = PLAYER.vz = 0; }
    else {
      const ox = cam.x, oz = cam.z;
      const [nx, nz] = constrain(cam.x, cam.z, cam.x + PLAYER.vx * dt, cam.z + PLAYER.vz * dt);
      cam.x = nx; cam.z = nz;
      if (Math.abs(nx - (ox + PLAYER.vx * dt)) > 1e-6) PLAYER.vx = 0;
      if (Math.abs(nz - (oz + PLAYER.vz * dt)) > 1e-6) PLAYER.vz = 0;
    }
  }
  if (playerFrame(dt)) active = true;
  return active;
}
