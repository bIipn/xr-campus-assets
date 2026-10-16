/* ================================================================
   Outside: sky, grass, building exteriors and the Recess Yard
   ================================================================ */
const SUN_DIR = [40, 62, 30];
const YARD = { x0:34, x1:92, z0:-34, z1:26, fenceZ:-8.6 };
const DROP = { x:78, z:13, base:1.0, top:31, h:34 };
const DOME = { x:54, z:16, r:4.2 };
const LIGHTS = { sun:null, hemi:null, amb:null, k:0 };
const YA = { swings:[], spinner:null, portal:null, ring:null, ringY:1.0 };
const PICK_PROXY = new THREE.MeshBasicMaterial({ visible:false });
let SKY = null;
function lookYaw(fx, fz, tx, tz){ return Math.atan2(-(tx - fx), -(tz - fz)); }
function scaleUV(geo, sx, sy){ const uv = geo.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) * sx, uv.getY(i) * sy); uv.needsUpdate = true; return geo; }
function wallMatOf(canvas, tw, th, tint, rough){ const t = tex(canvas); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(1 / tw, 1 / th); return new THREE.MeshStandardMaterial({ map:t, roughness:rough == null ? 0.9 : rough, color:tint == null ? 0xffffff : srgb(tint) }); }
function addCyl(rt, rb, h, mat, x, y, z, seg, parent){ const m = new THREE.Mesh(new THREE.CylinderGeometry(rt, rb, h, seg || 16), mat); m.position.set(x, y, z); (parent || scene).add(m); return m; }
function flat(geo, mat, x, y, z, ry){ const m = new THREE.Mesh(geo, mat); m.rotation.order = 'YXZ'; m.rotation.set(-Math.PI / 2, ry || 0, 0); m.position.set(x, y, z); scene.add(m); return m; }
function instBounds(mesh, pts, pad){
  const lo = new THREE.Vector3(Infinity, Infinity, Infinity), hi = new THREE.Vector3(-Infinity, -Infinity, -Infinity), v = new THREE.Vector3();
  for (const p of pts){ v.set(p[0], p[1], p[2]); lo.min(v); hi.max(v); }
  lo.subScalar(pad); hi.addScalar(pad);
  const s = new THREE.Sphere(); new THREE.Box3(lo, hi).getBoundingSphere(s); mesh.geometry.boundingSphere = s; mesh.frustumCulled = true;
}
/* Instances placed by full matrices */
class MatBatch {
  constructor(){ this.m = []; this.c = []; }
  add(m, col){ this.m.push(m.clone()); this.c.push(col || null); }
  build(geo, mat){
    if (!this.m.length) return null;
    const mesh = new THREE.InstancedMesh(geo, mat, this.m.length), col = new THREE.Color(), pts = [];
    this.m.forEach((m, i) => { mesh.setMatrixAt(i, m); pts.push([m.elements[12], m.elements[13], m.elements[14]]); if (this.c[i]){ col.set(this.c[i]); mesh.setColorAt(i, col); } });
    mesh.instanceMatrix.needsUpdate = true; if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    instBounds(mesh, pts, 3); scene.add(mesh); return mesh;
  }
}
function boxMatrix(p, xAxis, yAxis, zAxis, w, h, d){ const m = new THREE.Matrix4().makeBasis(xAxis.clone().multiplyScalar(w), yAxis.clone().multiplyScalar(h), zAxis.clone().multiplyScalar(d)); m.setPosition(p); return m; }

/* ---------------- Outdoor textures ---------------- */
function tileDraw(S, x, y, rad, fn){ for (const dx of [-S, 0, S]) for (const dy of [-S, 0, S]){ const X = x + dx, Y = y + dy; if (X + rad < 0 || X - rad > S || Y + rad < 0 || Y - rad > S) continue; fn(X, Y); } }
function canvasGrass(){
  const S = 256, c = mk(S, S), ctx = c.getContext('2d'), r = rnd(77);
  ctx.fillStyle = '#5b8a3a'; ctx.fillRect(0, 0, S, S);
  for (let i = 0; i < 44; i++){
    const x = r() * S, y = r() * S, rad = 14 + r() * 34, col = r() < 0.5 ? 'rgba(140,170,72,0.22)' : 'rgba(34,80,32,0.22)';
    tileDraw(S, x, y, rad, (X, Y) => { const g = ctx.createRadialGradient(X, Y, 0, X, Y, rad); g.addColorStop(0, col); g.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = g; ctx.fillRect(X - rad, Y - rad, rad * 2, rad * 2); });
  }
  for (let i = 0; i < 3200; i++){
    const x = r() * S, y = r() * S, l = 2 + r() * 4;
    ctx.strokeStyle = 'rgba(' + (48 + r() * 56 | 0) + ',' + (98 + r() * 84 | 0) + ',' + (26 + r() * 30 | 0) + ',' + (0.3 + r() * 0.45).toFixed(2) + ')';
    ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + (r() - 0.5) * 2, y - l); ctx.stroke();
  }
  return c;
}
function canvasBrick(){
  const W = 576, H = 512, c = mk(W, H), ctx = c.getContext('2d'), r = rnd(19), bw = 96, bh = 32;
  ctx.fillStyle = '#cfc4b3'; ctx.fillRect(0, 0, W, H);
  for (let row = 0; row < H / bh; row++){
    const off = row % 2 ? bw / 2 : 0;
    for (let k = 0; k < W / bw; k++){
      const x = k * bw + off, y = row * bh, t = r(), col = 'rgb(' + (150 + t * 34 | 0) + ',' + (68 + t * 18 + r() * 8 | 0) + ',' + (52 + t * 12 | 0) + ')', sh = (r() * 0.09).toFixed(3);
      for (const X of [x, x - W]){ ctx.fillStyle = col; ctx.fillRect(X + 3, y + 3, bw - 6, bh - 6); ctx.fillStyle = 'rgba(0,0,0,' + sh + ')'; ctx.fillRect(X + 3, y + bh - 10, bw - 6, 7); }
    }
  }
  for (let i = 0; i < 3200; i++){ ctx.fillStyle = r() < 0.5 ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.06)'; ctx.fillRect(r() * W, r() * H, 2, 2); }
  return c;
}
function canvasStone(){
  const S = 512, c = mk(S, S), ctx = c.getContext('2d'), r = rnd(23), rh = 128, bw = 256;
  ctx.fillStyle = '#b5ab99'; ctx.fillRect(0, 0, S, S);
  for (let row = 0; row < S / rh; row++){
    const off = row % 2 ? bw / 2 : 0;
    for (let k = 0; k < S / bw; k++){
      const x = k * bw + off, y = row * rh, t = r(), col = 'rgb(' + (208 + t * 20 | 0) + ',' + (200 + t * 18 | 0) + ',' + (184 + t * 16 | 0) + ')';
      for (const X of [x, x - S]){ ctx.fillStyle = col; ctx.fillRect(X + 2, y + 2, bw - 4, rh - 4); }
    }
  }
  for (let i = 0; i < 2600; i++){ ctx.fillStyle = r() < 0.5 ? 'rgba(90,80,60,0.07)' : 'rgba(255,255,255,0.08)'; const s = 1 + r() * 2; ctx.fillRect(r() * S, r() * S, s, s); }
  return c;
}
function canvasPavers(){
  const S = 256, c = mk(S, S), ctx = c.getContext('2d'), r = rnd(41), t = 64;
  ctx.fillStyle = '#958f84'; ctx.fillRect(0, 0, S, S);
  for (let y = 0; y < S; y += t) for (let x = 0; x < S; x += t){ const v = r(); ctx.fillStyle = 'rgb(' + (194 + v * 22 | 0) + ',' + (188 + v * 20 | 0) + ',' + (176 + v * 18 | 0) + ')'; ctx.fillRect(x + 2, y + 2, t - 4, t - 4); }
  for (let i = 0; i < 1800; i++){ ctx.fillStyle = r() < 0.5 ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.06)'; ctx.fillRect(r() * S, r() * S, 2, 2); }
  return c;
}
function canvasChips(){
  const S = 256, c = mk(S, S), ctx = c.getContext('2d'), r = rnd(9);
  ctx.fillStyle = '#6e4c2e'; ctx.fillRect(0, 0, S, S);
  for (let i = 0; i < 1500; i++){
    const x = r() * S, y = r() * S, w = 3 + r() * 7, h = 1.5 + r() * 2.5;
    ctx.save(); ctx.translate(x, y); ctx.rotate(r() * Math.PI); ctx.fillStyle = 'rgb(' + (112 + r() * 70 | 0) + ',' + (74 + r() * 46 | 0) + ',' + (42 + r() * 30 | 0) + ')'; ctx.fillRect(-w / 2, -h / 2, w, h); ctx.restore();
  }
  return c;
}
function canvasSkyDome(){
  const W = 1024, H = 512, c = mk(W, H), ctx = c.getContext('2d'), r = rnd(5), HZ = H / 2;
  const g = ctx.createLinearGradient(0, 0, 0, HZ);
  g.addColorStop(0, '#3b72b2'); g.addColorStop(0.5, '#6e9fd0'); g.addColorStop(0.86, '#b6d1e4'); g.addColorStop(1, '#d6e5e9');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, HZ);
  ctx.fillStyle = '#d6e5e9'; ctx.fillRect(0, HZ, W, H - HZ);
  const blob = (x, y, rx, ry, a) => { for (const dx of [-W, 0, W]){ ctx.save(); ctx.translate(x + dx, y); ctx.scale(rx, ry); const gg = ctx.createRadialGradient(0, 0, 0, 0, 0, 1); gg.addColorStop(0, 'rgba(255,255,255,' + a.toFixed(2) + ')'); gg.addColorStop(1, 'rgba(255,255,255,0)'); ctx.fillStyle = gg; ctx.beginPath(); ctx.arc(0, 0, 1, 0, Math.PI * 2); ctx.fill(); ctx.restore(); } };
  for (let i = 0; i < 24; i++){ const x = r() * W, y = 72 + r() * 150, s = 0.6 + r() * 0.9; for (let k = 0; k < 7; k++) blob(x + (r() - 0.5) * 120 * s, y + (r() - 0.5) * 14 * s, (40 + r() * 50) * s, (9 + r() * 9) * s, 0.32 + r() * 0.3); }
  const sd = new THREE.Vector3(SUN_DIR[0], SUN_DIR[1], SUN_DIR[2]).normalize(), th = Math.acos(sd.y), ph = Math.atan2(sd.z, -sd.x);
  const sx = ((ph / (Math.PI * 2)) % 1 + 1) % 1 * W, sy = th / Math.PI * H, k = 1 / Math.max(0.2, Math.sin(th));
  for (const dx of [-W, 0, W]){
    ctx.save(); ctx.translate(sx + dx, sy); ctx.scale(k, 1);
    const sg = ctx.createRadialGradient(0, 0, 0, 0, 0, 90); sg.addColorStop(0, 'rgba(255,252,240,1)'); sg.addColorStop(0.07, 'rgba(255,248,228,1)'); sg.addColorStop(0.2, 'rgba(255,240,205,0.35)'); sg.addColorStop(1, 'rgba(255,240,205,0)');
    ctx.fillStyle = sg; ctx.fillRect(-90, -90, 180, 180); ctx.restore();
  }
  const hill = (col, amp, base, seed) => {
    const rr = rnd(seed), fr = [1, 2, 3, 5, 7, 11, 17].map((f) => [f, rr() * Math.PI * 2, (0.5 + rr()) / Math.sqrt(f)]);
    ctx.fillStyle = col; ctx.beginPath(); ctx.moveTo(0, HZ + 2);
    for (let x = 0; x <= W; x += 4){ let y = 0; for (const [f, p, a] of fr) y += Math.sin(x / W * Math.PI * 2 * f + p) * a; ctx.lineTo(x, HZ - base - amp * Math.max(0, 0.55 + y * 0.32)); }
    ctx.lineTo(W, HZ + 2); ctx.closePath(); ctx.fill();
  };
  hill('#b4c7cb', 11, 1, 3); hill('#9fb6a8', 6, 0, 8);
  return c;
}
function canvasHopscotch(){
  const W = 1024, H = 280, c = mk(W, H), ctx = c.getContext('2d');
  ctx.clearRect(0, 0, W, H); ctx.strokeStyle = 'rgba(250,250,245,0.9)'; ctx.lineWidth = 7; ctx.fillStyle = 'rgba(250,250,245,0.9)'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.font = '700 70px ' + F.ui;
  const cols = [['1'], ['2', '3'], ['4'], ['5', '6'], ['7'], ['8', '9'], ['10']], cw = (W - 20) / cols.length;
  cols.forEach((col, i) => { const x = 10 + i * cw; col.forEach((t, j) => { const h = (H - 20) / col.length, y = 10 + j * h; ctx.strokeRect(x, y, cw, h); ctx.fillText(t, x + cw / 2, y + h / 2 + 4); }); });
  return c;
}
function drawYardSign(){
  const W = 1400, H = 280, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#1d3b52'; rrect(ctx, 0, 0, W, H, 36); ctx.fill();
  ctx.strokeStyle = '#f2c14e'; ctx.lineWidth = 8; rrect(ctx, 16, 16, W - 32, H - 32, 26); ctx.stroke();
  ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center'; ctx.font = '700 118px ' + F.ui; ctx.fillText('RECESS YARD', W / 2, 150);
  ctx.fillStyle = '#f2c14e'; ctx.font = '700 40px ' + F.type; ctx.fillText('COASTER · SKY DROP · OCEAN DIVE', W / 2, 222);
  return c;
}
function drawRideSign(name, lines, accent){
  const W = 640, H = 860, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#1d3b52'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = accent; ctx.fillRect(0, 0, W, 160);
  ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center'; fit(ctx, name.toUpperCase(), F.ui, '700', 72, W - 70); ctx.fillText(name.toUpperCase(), W / 2, 106);
  ctx.font = '400 38px ' + F.ui; lines.forEach((l, i) => ctx.fillText(l, W / 2, 262 + i * 60));
  ctx.fillStyle = '#f2c14e'; rrect(ctx, 80, H - 210, W - 160, 112, 56); ctx.fill();
  ctx.fillStyle = '#1d160a'; ctx.font = '700 46px ' + F.ui; ctx.fillText((COARSE ? 'TAP' : 'CLICK') + ' TO RIDE', W / 2, H - 138);
  return c;
}
function drawArrowBoard(text, dir, accent){
  const W = 900, H = 200, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#f4efe4'; ctx.beginPath();
  if (dir > 0){ ctx.moveTo(0, 0); ctx.lineTo(W - 110, 0); ctx.lineTo(W, H / 2); ctx.lineTo(W - 110, H); ctx.lineTo(0, H); }
  else { ctx.moveTo(W, 0); ctx.lineTo(110, 0); ctx.lineTo(0, H / 2); ctx.lineTo(110, H); ctx.lineTo(W, H); }
  ctx.closePath(); ctx.fill();
  ctx.fillStyle = accent; ctx.fillRect(dir > 0 ? 0 : W - 28, 0, 28, H);
  ctx.fillStyle = '#1d3b52'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; fit(ctx, text, F.ui, '700', 80, W - 230); ctx.fillText(text, W / 2 + (dir > 0 ? -40 : 40), H / 2 + 4);
  return c;
}
function drawStationSign(){
  const W = 1600, H = 220, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#1d3b52'; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = '#f2c14e'; ctx.lineWidth = 6; ctx.strokeRect(12, 12, W - 24, H - 24);
  const g = ctx.createLinearGradient(80, 0, 420, 0); g.addColorStop(0, 'rgba(242,193,78,0)'); g.addColorStop(1, 'rgba(242,193,78,1)');
  ctx.strokeStyle = g; ctx.lineWidth = 14; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(90, 150); ctx.quadraticCurveTo(250, 140, 400, 90); ctx.stroke();
  ctx.fillStyle = '#f2c14e'; ctx.beginPath(); ctx.arc(410, 86, 22, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center'; ctx.font = '700 110px ' + F.ui; ctx.fillText('COMET COASTER', W / 2 + 120, 150);
  return c;
}
function drawTowerBand(){
  const W = 2048, H = 200, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#1d3b52'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#f2c14e'; ctx.fillRect(0, 0, W, 10); ctx.fillRect(0, H - 10, W, 10);
  ctx.fillStyle = '#ffffff'; ctx.font = '700 110px ' + F.ui; ctx.textBaseline = 'middle';
  for (let i = 0; i < 3; i++){ ctx.textAlign = 'center'; ctx.fillText('SKY DROP', W / 3 * (i + 0.5), H / 2 + 6); }
  return c;
}
function canvasTower(){
  const W = 128, H = 512, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#e8ecef'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = 'rgba(40,60,80,0.18)'; for (let y = 0; y < H; y += 64) ctx.fillRect(0, y, W, 3);
  ctx.fillStyle = '#d2462f'; ctx.fillRect(0, 0, W, 22);
  return c;
}
function canvasDome(){
  const W = 1024, H = 384, c = mk(W, H), ctx = c.getContext('2d'), r = rnd(12);
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#4fb8c8'); g.addColorStop(1, '#16627a');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = 'rgba(255,255,255,0.22)'; ctx.lineWidth = 3;
  for (let y = 48; y < H; y += 56){ ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  for (let x = 0; x < W; x += 64){ ctx.beginPath(); ctx.moveTo(x, 40); ctx.lineTo(x, H); ctx.stroke(); }
  const fish = (x, y, s, col, dir) => { ctx.save(); ctx.translate(x, y); ctx.scale(s * dir, s); ctx.fillStyle = col; ctx.beginPath(); ctx.ellipse(0, 0, 30, 14, 0, 0, Math.PI * 2); ctx.fill(); ctx.beginPath(); ctx.moveTo(-24, 0); ctx.lineTo(-46, -14); ctx.lineTo(-46, 14); ctx.closePath(); ctx.fill(); ctx.fillStyle = '#10313d'; ctx.beginPath(); ctx.arc(16, -3, 3, 0, Math.PI * 2); ctx.fill(); ctx.restore(); };
  const cols = ['#ffd166', '#ff8f3d', '#ffffff', '#ff6f91'];
  for (let i = 0; i < 22; i++){ const x = r() * W; fish(x, 200 + r() * 150, 0.8 + r() * 0.9, cols[(r() * cols.length) | 0], r() < 0.5 ? 1 : -1); }
  ctx.fillStyle = 'rgba(255,255,255,0.35)'; for (let i = 0; i < 90; i++){ ctx.beginPath(); ctx.arc(r() * W, 120 + r() * 250, 2 + r() * 5, 0, Math.PI * 2); ctx.fill(); }
  return c;
}
function canvasPortal(){
  const S = 256, c = mk(S, S), ctx = c.getContext('2d'), r = rnd(3);
  ctx.fillStyle = '#0d4a66'; ctx.fillRect(0, 0, S, S);
  ctx.strokeStyle = 'rgba(160,230,255,0.45)'; ctx.lineWidth = 3;
  for (let i = 0; i < 26; i++){ const x = r() * S, y = r() * S, rad = 10 + r() * 30; tileDraw(S, x, y, rad, (X, Y) => { ctx.beginPath(); ctx.ellipse(X, Y, rad, rad * 0.55, r() * 3, 0, Math.PI * 2); ctx.stroke(); }); }
  return c;
}
function canvasWindowGlass(){
  const W = 128, H = 256, c = mk(W, H), ctx = c.getContext('2d');
  const g = ctx.createLinearGradient(0, 0, W, H); g.addColorStop(0, '#5d7f93'); g.addColorStop(0.45, '#2c4554'); g.addColorStop(0.55, '#3c5a6b'); g.addColorStop(1, '#22343f');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = 'rgba(255,255,255,0.12)'; ctx.beginPath(); ctx.moveTo(0, 60); ctx.lineTo(W, 0); ctx.lineTo(W, 30); ctx.lineTo(0, 100); ctx.fill();
  return c;
}
function drawExitSign(){
  const W = 1000, H = 220, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#1f6b45'; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 6; ctx.strokeRect(12, 12, W - 24, H - 24);
  ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center'; ctx.font = '700 92px ' + F.ui; ctx.fillText('RECESS YARD', W / 2, 118);
  ctx.font = '700 34px ' + F.type; ctx.fillText('COASTER · SKY DROP · OCEAN DIVE', W / 2, 178);
  return c;
}
function drawWallLetters(text, W, H){
  const c = mk(W, H), ctx = c.getContext('2d');
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; fit(ctx, text, F.ui, '700', H * 0.78, W * 0.97);
  ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.fillText(text, W / 2 + 4, H / 2 + 6);
  ctx.fillStyle = '#f7f3ea'; ctx.fillText(text, W / 2, H / 2 + 2);
  return c;
}

/* ---------------- Trees ---------------- */
function treeSet(){
  const T = [], C = [];
  return {
    add(x, z, s, r){
      const h = (1.7 + r() * 0.8) * s, g = 0.8 + r() * 0.45;
      T.push([x, h / 2, z, s, h]);
      C.push([x, h + 0.75 * s * g, z, 1.55 * s * g, 1.25 * s * g, shade('#4a7a36', (r() - 0.5) * 0.35), r() * 6]);
      C.push([x + (r() - 0.5) * 0.7 * s, h + 1.75 * s * g, z + (r() - 0.5) * 0.7 * s, 1.08 * s * g, 1.0 * s * g, shade('#5d8f43', (r() - 0.5) * 0.35), r() * 6]);
    },
    build(){ if (T.length) buildTreeMeshes(T, C); }
  };
}

/* ---------------- Ground, sky and building exteriors ---------------- */
function roofSlab(x0, x1, z0, z1, y, mat, edge, sides){
  sides = sides || 'nsew';
  const m = new THREE.Mesh(new THREE.PlaneGeometry(x1 - x0, z1 - z0), mat); m.rotation.x = -Math.PI / 2; m.position.set((x0 + x1) / 2, y, (z0 + z1) / 2); scene.add(m);
  const t = 0.3, hh = 0.34, yy = y + hh / 2 - 0.04, cx = (x0 + x1) / 2, cz = (z0 + z1) / 2;
  if (sides.includes('n')) addBox(x1 - x0 + t, hh, t, edge, cx, yy, z0);
  if (sides.includes('s')) addBox(x1 - x0 + t, hh, t, edge, cx, yy, z1);
  if (sides.includes('w')) addBox(t, hh, z1 - z0 + t, edge, x0, yy, cz);
  if (sides.includes('e')) addBox(t, hh, z1 - z0 + t, edge, x1, yy, cz);
}
/* A far tree line and rolling hills, so the world doesn't end at a flat edge */
function buildHorizon(){
  const ring = (R, N, base, top, bottomCol, topCol, wobble) => {
    const pos = new Float32Array((N + 1) * 6), col = new Float32Array((N + 1) * 6), idx = [];
    const c0 = new THREE.Color(bottomCol), c1 = new THREE.Color(topCol);
    for (let i = 0; i <= N; i++){
      const a = i / N * Math.PI * 2, r = R + wobble * Math.sin(a * 3 + 0.7), h = top(a, i);
      const x = 30 + Math.cos(a) * r, z = -8 + Math.sin(a) * r;
      pos.set([x, base, z, x, h, z], i * 6); col.set([c0.r, c0.g, c0.b, c1.r, c1.g, c1.b], i * 6);
      if (i < N){ const k = i * 2; idx.push(k, k + 1, k + 2, k + 1, k + 3, k + 2); }
    }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.BufferAttribute(col, 3)); g.setIndex(idx);
    const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ vertexColors:true, side:THREE.DoubleSide }));
    m.material.userData.boosted = true; m.userData.noShadow = true; m.userData.noAO = true; m.frustumCulled = false; scene.add(m); return m;
  };
  const hill = (a) => 13 + 6 * Math.sin(a * 2 + 1.1) + 4 * Math.sin(a * 5 + 0.3) + 2.2 * Math.sin(a * 11 + 2.4) + 1.2 * Math.sin(a * 23);
  ring(176, 240, -2, hill, 0x6f8a78, 0x8aa596, 6);
  /* Rounded crowns of uneven size, eight segments each */
  const hash = (n) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
  const crown = (a, i) => { const c = Math.floor(i / 8), u = (i % 8) / 8, b = Math.sqrt(Math.max(0, 1 - (2 * u - 1) ** 2)); return 6.6 + 1.4 * Math.sin(a * 5 + 0.4) + 0.8 * Math.sin(a * 13) + (1.3 + 2.2 * hash(c)) * b; };
  ring(142, 2400, -2, crown, 0x22392a, 0x35553c, 3);
}
function buildExterior(M){
  const gg = new THREE.PlaneGeometry(640, 640, 120, 120), gp = gg.attributes.position, gc = new Float32Array(gp.count * 3);
  for (let i = 0; i < gp.count; i++){
    const x = gp.getX(i), y = gp.getY(i), n1 = Math.sin(x * 0.045 + 1.3) * Math.cos(y * 0.038) * 0.6 + Math.sin(x * 0.11 + y * 0.07) * 0.4, n2 = Math.sin(x * 0.021 - y * 0.03 + 2.1);
    const k = 0.86 + 0.14 * n1; gc[i * 3] = k * (1 + 0.07 * n2); gc[i * 3 + 1] = k; gc[i * 3 + 2] = k * (0.92 - 0.04 * n2);
  }
  gg.setAttribute('color', new THREE.BufferAttribute(gc, 3));
  const ground = new THREE.Mesh(gg, new THREE.MeshStandardMaterial({ map:repTex(canvasGrass(), 640 / 3.2, 640 / 3.2), roughness:1, vertexColors:true }));
  ground.rotation.x = -Math.PI / 2; ground.position.set(30, -0.012, -8); ground.userData.floor = true; scene.add(ground); floors.push(ground);
  SKY = new THREE.Mesh(new THREE.SphereGeometry(205, 48, 24), new THREE.MeshBasicMaterial({ map:tex(canvasSkyDome()), side:THREE.BackSide, depthWrite:false, depthTest:false, fog:false, toneMapped:false }));
  SKY.renderOrder = -10; SKY.frustumCulled = false; scene.add(SKY);
  gfxSky();
  buildGrass();
  buildHorizon();

  const stone = wallMatOf(canvasStone(), 2.4, 2.4), stoneLib = wallMatOf(canvasStone(), 2.4, 2.4, 0xe2d3b6), brick = wallMatOf(canvasBrick(), 1.35, 1.2);
  const roof = stdMat(0x5d6164, 0.95), cap = stdMat(0xd8cfbf, 0.85), capB = stdMat(0xcdc4b4, 0.8);
  /* Museum */
  addWall({ axis:'x', at:6.2, from:-42.2, to:0.2, h:4.6, face:1, mat:stone, doors:[{ a:-4.8, b:-1.2, h:3.65 }] });
  addWall({ axis:'z', at:0.2, from:-6.2, to:6.2, h:4.6, face:1, mat:stone });
  roofSlab(-6.2, 6.2, -42.2, 0.2, 4.6, roof, cap);
  const glassRoof = stdMat(0x9fc3d6, 0.18, 0.4, { emissive:srgb(0x2a4656), emissiveIntensity:0.4 });
  addBox(2.6, 0.22, 36, glassRoof, 0, 4.7, -21);
  /* The Wax Hall: a taller annex behind the museum, with its name on the side facing the yard */
  addWall({ axis:'x', at:8.7, from:-81.3, to:-42.0, h:5.4, face:1, mat:stone });
  addWall({ axis:'z', at:-42.0, from:6.2, to:8.7, h:5.4, face:1, mat:stone });
  addBox(12.4, 0.8, 0.2, stone, 0, 5.0, -42.0);
  roofSlab(-8.7, 8.7, -81.3, -42.0, 5.4, roof, cap);
  const waxLetters = new THREE.MeshBasicMaterial({ map:tex(drawWallLetters('LIVING HISTORY', 1400, 170)), transparent:true, depthWrite:false, toneMapped:false });
  addPlane(7.2, 0.88, waxLetters, 8.72, 4.45, -61.5, Math.PI / 2);
  /* Library */
  addWall({ axis:'x', at:-11.8, from:-13.2, to:7.2, h:7.9, face:1, mat:stoneLib, doors:[{ a:-4.8, b:-1.2, h:3.65 }] });
  addWall({ axis:'z', at:7.2, from:-32.2, to:-11.8, h:7.9, face:1, mat:stoneLib });
  addWall({ axis:'z', at:-13.2, from:-32.2, to:-11.8, h:7.9, face:-1, mat:stoneLib });
  roofSlab(-32.2, -11.8, -13.2, 7.2, 7.9, roof, cap);
  addBox(10, 1.5, 3.2, stdMat(0xe2d3b6, 0.85), -22, 8.65, -3);
  addBox(10.2, 0.9, 3.0, glassRoof, -22, 8.7, -3);
  addBox(10.4, 0.16, 3.6, cap, -22, 9.45, -3);
  /* Halls */
  for (const [x0, x1] of [[-11.8, -6.2], [6.2, 11.8]]){
    addWall({ axis:'z', at:-4.8, from:x0, to:x1, h:3.65, face:-1, mat:stone });
    addWall({ axis:'z', at:-1.2, from:x0, to:x1, h:3.65, face:1, mat:stone });
    roofSlab(x0, x1, -4.8, -1.2, 3.65, roof, cap, 'ns');
  }
  /* School */
  addWall({ axis:'x', at:34.2, from:-13.2, to:7.2, h:4.3, face:1, mat:brick, doors:[{ a:-4.2, b:-1.8, h:2.7 }] });
  addWall({ axis:'z', at:7.2, from:11.8, to:34.2, h:4.3, face:1, mat:brick });
  addWall({ axis:'z', at:-13.2, from:11.8, to:34.2, h:4.3, face:-1, mat:brick });
  roofSlab(11.8, 34.2, -13.2, 7.2, 4.3, roof, capB);
  const metal = stdMat(0x9aa1a6, 0.45, 0.5);
  addBox(1.8, 1.0, 1.3, metal, 18, 4.8, 2.5); addBox(1.4, 0.9, 1.1, metal, 28, 4.75, -9.5); addBox(0.5, 0.5, 0.5, metal, 22, 4.55, 4.5);
  for (const zz of [-8.9, 2.6]) addBox(7, 0.12, 1.2, glassRoof, 21, 4.36, zz);
  /* School east facade: the back door to the Recess Yard */
  const steel = stdMat(0x2f363c, 0.45, 0.4), trim = stdMat(0xe9e5dc, 0.6), conc = stdMat(0xbdb6a8, 0.9);
  for (const zz of [-4.25, -1.75]) addBox(0.36, 2.75, 0.1, steel, 34.11, 1.375, zz);
  addBox(0.36, 0.1, 2.6, steel, 34.11, 2.75, -3);
  addBox(0.4, 0.02, 2.4, steel, 34.1, 0.01, -3);
  for (const [a, b] of [[-13.2, -4.32], [-1.68, 7.2]]) addBox(0.07, 0.42, b - a, conc, 34.235, 0.21, (a + b) / 2);
  addBox(1.5, 0.12, 3.6, stdMat(0x1d3b52, 0.6), 34.95, 3.0, -3);
  addBox(1.5, 0.04, 3.62, stdMat(0xf2c14e, 0.5), 34.95, 2.93, -3);
  const letters = new THREE.MeshBasicMaterial({ map:tex(drawWallLetters('WORKSHOP SCHOOL', 1400, 170)), transparent:true, depthWrite:false, toneMapped:false });
  addPlane(5.4, 0.66, letters, 34.22, 3.68, -3, Math.PI / 2);
  const glass = new THREE.MeshStandardMaterial({ map:tex(canvasWindowGlass()), roughness:0.15, metalness:0.3 });
  for (const zc of [-11.4, -8.9, -6.4, 5.6]){
    addPlane(1.5, 1.6, glass, 34.215, 1.85, zc, Math.PI / 2);
    for (const dz of [-0.78, 0.78]) addBox(0.06, 1.7, 0.08, trim, 34.23, 1.85, zc + dz);
    for (const yy of [1.02, 2.68]) addBox(0.06, 0.08, 1.64, trim, 34.23, yy, zc);
    addBox(0.06, 0.05, 1.5, trim, 34.23, 1.85, zc);
    addBox(0.16, 0.06, 1.7, conc, 34.27, 0.98, zc);
  }
  addPlane(4.2, 2.89, basicMat(drawMural(), 0xf0f0f0), 34.215, 1.95, 1.85, Math.PI / 2);
  for (const zz of [-0.32, 4.02]) addBox(0.06, 3.0, 0.08, trim, 34.23, 1.95, zz);
  const lampMat = glowMatOf(0xfff1c8);
  for (const zz of [-4.75, -1.25]){ addBox(0.12, 0.3, 0.16, steel, 34.28, 2.35, zz); addBox(0.08, 0.2, 0.12, lampMat, 34.35, 2.3, zz); }

  /* Trees around the campus */
  const far = treeSet(), rr = rnd(99);
  let tries = 0, placed = 0;
  while (placed < 140 && tries++ < 5000){
    const x = -84 + rr() * 228, z = -96 + rr() * 168;
    if (x > -40 && x < 97 && z > -50 && z < 31) continue;
    far.add(x, z, 1.3 + rr() * 1.4, rr); placed++;
  }
  for (const [x, z] of [[9, -9.5], [9, -17], [9, -25], [9, -34], [9, 3.8], [16, 11.5], [24.5, 12.5], [-2, 6], [-20, 12], [-28.5, 11], [27, -18.5], [19, -17.5], [14, -25], [-8.5, -20], [-9, -31], [-22, -18], [-30, -21], [2, 9.5]]) far.add(x, z, 1.1 + rr() * 0.5, rr);
  far.build();
}

/* ---------------- The Recess Yard ---------------- */
function buildPlayground(M){
  const r = rnd(2024);
  const paver = new THREE.MeshStandardMaterial({ map:repTex(canvasPavers(), 1, 1), roughness:0.85 });
  const strip = (x0, z0, x1, z1, w, y) => { const L = Math.hypot(x1 - x0, z1 - z0); return flat(scaleUV(new THREE.PlaneGeometry(L, w), L / 2, w / 2), paver, (x0 + x1) / 2, y || 0.004, (z0 + z1) / 2, Math.atan2(-(z1 - z0), x1 - x0)); };
  strip(34.05, -3, 46.2, -3, 2.4);
  flat(scaleUV(new THREE.CircleGeometry(6.5, 56), 6.5, 6.5), paver, 52, 0.006, -1.5);
  flat(new THREE.RingGeometry(6.5, 6.85, 64), stdMat(0x8d877c, 0.9), 52, 0.007, -1.5);
  strip(52, -7.4, 52, -9.4, 3.2, 0.005);
  strip(57.6, 1.3, 73.4, 10.3, 2.2, 0.005);
  strip(52.8, 4.6, 54, 11.1, 2.2, 0.005);
  strip(41.2, -1.9, 41.2, 10.2, 2.0, 0.005);
  const chips = new THREE.MeshStandardMaterial({ map:repTex(canvasChips(), 1, 1), roughness:1 });
  flat(scaleUV(new THREE.PlaneGeometry(10.6, 14), 10.6 / 2, 14 / 2), chips, 40.8, 0.005, 17);
  const edgeWood = stdMat(0x7a5536, 0.8);
  addBox(10.8, 0.14, 0.14, edgeWood, 40.8, 0.07, 10); addBox(10.8, 0.14, 0.14, edgeWood, 40.8, 0.07, 24);
  addBox(0.14, 0.14, 14, edgeWood, 35.5, 0.07, 17); addBox(0.14, 0.14, 14, edgeWood, 46.1, 0.07, 17);
  flat(new THREE.PlaneGeometry(3.6, 0.98), new THREE.MeshBasicMaterial({ map:tex(canvasHopscotch()), transparent:true, depthWrite:false, toneMapped:false }), 41.2, 0.012, -3);

  /* Entrance arch */
  const navy = stdMat(0x1d3b52, 0.55, 0.2), yellow = stdMat(0xf2c14e, 0.5, 0.2);
  for (const zz of [-4.6, -1.4]){ addCyl(0.09, 0.11, 3.3, navy, 36.2, 1.65, zz, 12); OBST.push({ x:36.2, z:zz, r:0.2 }); }
  addBox(0.1, 0.78, 3.5, navy, 36.2, 3.05, -3);
  const ys = basicMat(drawYardSign());
  addPlane(3.36, 0.67, ys, 36.145, 3.05, -3, -Math.PI / 2);
  addPlane(3.36, 0.67, ys, 36.255, 3.05, -3, Math.PI / 2);

  /* Signpost in the plaza */
  addCyl(0.07, 0.08, 3.1, navy, 52, 1.55, -1.5, 12);
  addCyl(0.12, 0.12, 0.08, yellow, 52, 3.14, -1.5, 12);
  OBST.push({ x:52, z:-1.5, r:0.45 });
  const boards = [['coaster', 'COMET COASTER', 51.6, -9, '#d2462f', 2.75], ['drop', 'SKY DROP', 78, 13, '#7a5cff', 2.3], ['dive', 'OCEAN DIVE', 54, 16, '#1f9bb6', 1.85]];
  for (const [id, label, tx, tz, accent, y] of boards){
    const ang = Math.atan2(-(tz + 1.5), tx - 52), g = new THREE.Group(); g.position.set(52, y, -1.5); g.rotation.y = ang;
    const f1 = addPlane(1.5, 0.333, new THREE.MeshBasicMaterial({ map:tex(drawArrowBoard(label, 1, accent)), alphaTest:0.5, toneMapped:false }), 0.84, 0, 0.026, 0, g);
    const f2 = addPlane(1.5, 0.333, new THREE.MeshBasicMaterial({ map:tex(drawArrowBoard(label, -1, accent)), alphaTest:0.5, toneMapped:false }), 0.84, 0, -0.026, Math.PI, g);
    const core = addBox(1.42, 0.3, 0.04, stdMat(0xe9e4d8, 0.8), 0.8, 0, 0, 0, g);
    for (const m of [f1, f2, core]){ m.userData.ride = id; pickItems.push(m); }
    scene.add(g);
  }

  /* Lamps, benches and tables */
  const lampPost = stdMat(0x23292e, 0.5, 0.4), globe = glowMatOf(0xfff3d6);
  for (const [x, z] of [[38.6, -5.1], [44.2, -0.9], [47.6, -8.0], [56.4, -8.0], [60.4, 3.9], [46.6, 5.0], [65.6, 9.2], [50.3, 9.6]]){
    addCyl(0.05, 0.07, 3.3, lampPost, x, 1.65, z, 10); const gb = new THREE.Mesh(new THREE.SphereGeometry(0.19, 16, 12), globe); gb.position.set(x, 3.42, z); scene.add(gb);
    OBST.push({ x, z, r:0.25 });
  }
  const slat = stdMat(0x9a6b43, 0.75), iron = stdMat(0x2b2f33, 0.5, 0.4);
  const bench = (x, z, ry) => {
    const g = new THREE.Group(); g.position.set(x, 0, z); g.rotation.y = ry;
    for (let i = 0; i < 3; i++) addBox(1.7, 0.04, 0.12, slat, 0, 0.45, -0.15 + i * 0.15, 0, g);
    for (let i = 0; i < 2; i++){ const b = addBox(1.7, 0.12, 0.035, slat, 0, 0.66 + i * 0.16, 0.25, 0, g); b.rotation.x = -0.18; }
    for (const sx of [-0.72, 0.72]){ addBox(0.06, 0.44, 0.44, iron, sx, 0.22, 0.02, 0, g); addBox(0.06, 0.42, 0.05, iron, sx, 0.66, 0.27, 0, g); }
    scene.add(g); OBST.push({ x, z, r:0.95 });
  };
  for (const a of [-0.8, -2.35, 0.2, 2.6]){ const x = 52 + Math.cos(a) * 7.7, z = -1.5 + Math.sin(a) * 7.7; bench(x, z, Math.atan2(-(52 - x), -(-1.5 - z)) + Math.PI); }
  const table = (x, z, ry) => {
    const g = new THREE.Group(); g.position.set(x, 0, z); g.rotation.y = ry;
    addBox(1.9, 0.06, 0.8, slat, 0, 0.75, 0, 0, g);
    for (const sz of [-0.62, 0.62]) addBox(1.9, 0.05, 0.28, slat, 0, 0.45, sz, 0, g);
    for (const sx of [-0.7, 0.7]){ const a = addBox(0.07, 0.95, 0.07, iron, sx, 0.4, 0, 0, g); a.rotation.x = 0.5; const b = addBox(0.07, 0.95, 0.07, iron, sx, 0.4, 0, 0, g); b.rotation.x = -0.5; addBox(0.07, 0.05, 1.5, iron, sx, 0.42, 0, 0, g); }
    scene.add(g); OBST.push({ x, z, r:1.25 });
  };
  table(63.2, -4.6, 0.3); table(67.4, -1.6, -0.2); table(48.8, 12.2, 1.4);

  /* Trees in the yard */
  const trees = treeSet();
  const yt = [[47.5, 23.4], [54, 23.8], [60.5, 23.2], [71.5, 23.6], [78, 23.2], [84.5, 23.6], [90, 22], [89.8, 15.5], [90, 8], [89.6, 1.2], [89.8, -5.5], [61.2, 11.6], [69.5, 1.6], [84.8, 7.4], [46.7, 8.4], [69.5, 16.6], [58.2, -6.2], [37.2, 6.4]];
  for (const [x, z] of yt){ trees.add(x, z, 1.05 + r() * 0.35, r); OBST.push({ x, z, r:0.75 }); }
  trees.build();

  /* Fences */
  const posts = new BoxBatch(), rails = new BoxBatch();
  const fence = (x0, z0, x1, z1, gap) => {
    const L = Math.hypot(x1 - x0, z1 - z0), n = Math.max(1, Math.round(L / 2.4)), ry = Math.atan2(-(z1 - z0), x1 - x0);
    const at = (t) => [x0 + (x1 - x0) * t, z0 + (z1 - z0) * t], inGap = (p) => gap && gap(p[0], p[1]);
    for (let i = 0; i <= n; i++){ const p = at(i / n); if (!inGap(p)) posts.add(p[0], 0.6, p[1], 0.08, 1.2, 0.08, ry); }
    for (let i = 0; i < n; i++){ const p = at((i + 0.5) / n); if (inGap(p) || inGap(at(i / n)) || inGap(at((i + 1) / n))) continue; for (const y of [0.55, 1.08]) rails.add(p[0], y, p[1], L / n, 0.05, 0.04, ry); }
  };
  fence(34.3, YARD.fenceZ, 91.9, YARD.fenceZ, (x) => x > 49.6 && x < 54.4);
  fence(91.9, -33.9, 91.9, 25.9); fence(34.1, 25.9, 91.9, 25.9); fence(32.2, -33.9, 91.9, -33.9);
  fence(32.2, -33.9, 32.2, -13.2); fence(34.1, 7.2, 34.1, 25.9);
  const fr = 4.6, fa0 = Math.atan2(10.3 - DROP.z, 73.4 - DROP.x);
  for (let i = 0; i < 18; i++){
    const a0 = i / 18 * Math.PI * 2, a1 = (i + 1) / 18 * Math.PI * 2;
    if (Math.abs(angDiff(a0 + (a1 - a0) / 2, fa0)) < 0.42) continue;
    fence(DROP.x + Math.cos(a0) * fr, DROP.z + Math.sin(a0) * fr, DROP.x + Math.cos(a1) * fr, DROP.z + Math.sin(a1) * fr);
  }
  const green = stdMat(0x2e4b3c, 0.55, 0.3);
  posts.build(green, false); rails.build(green, false);

  buildCoaster(M);
  buildDropTower(M);
  buildDiveDome(M);
  buildSwings(40.8, 13.6);
  buildSlide(41.4, 20.4);
  buildSpinner(66.5, 20);
  buildProps();
}

/* ---------------- Comet Coaster ---------------- */
const COASTER = { L:0, n:0, ds:0.1, P:null, T:null, N:null, B:null, V:null, iCrest:0, iLoopTop:0, loop:[0, 0], cars:[], stats:{ height:19, kmh:62, mph:39, loop:10, length:170 }, tokenAt:null };
function coasterPoints(){
  const pts = [], P = (x, y, z) => pts.push(new THREE.Vector3(x, y, z));
  P(54, 0.8, -11.5); P(57, 0.85, -11.5);
  P(60, 1.6, -11.5); P(63, 4.0, -11.5); P(70, 10.0, -11.5); P(76.5, 15.6, -11.5); P(79.5, 18.0, -11.5);
  P(82, 18.9, -11.6); P(85.6, 18.8, -12.9); P(87.9, 18.6, -15.8); P(87.9, 18.3, -19.2); P(85.6, 18.0, -22.1); P(82, 17.6, -23.4);
  P(79.2, 16.4, -23.5); P(76.6, 12.4, -23.5); P(74.2, 7.0, -23.5); P(71.8, 2.6, -23.5); P(69.2, 1.0, -23.5); P(66.8, 0.9, -23.5);
  const LC = { x:61.5, y:5.6, r:4.6 }, NL = 16;
  for (let i = 0; i <= NL; i++){ const ph = i / NL * Math.PI * 2; P(LC.x - LC.r * Math.sin(ph), LC.y - LC.r * Math.cos(ph), -23.5 - 3.0 * (i / NL)); }
  P(57, 1.1, -26.7); P(53.5, 3.0, -26.9); P(50.5, 6.0, -27); P(47.5, 6.6, -27); P(44.6, 4.6, -27); P(42, 2.2, -26.8);
  P(39, 1.7, -26.6); P(35.6, 1.6, -24.6); P(33.6, 1.6, -21.2); P(33.6, 1.6, -17.6); P(35.4, 1.5, -14.3); P(38.6, 1.2, -12.2);
  P(42, 1.0, -11.55); P(46, 0.85, -11.5); P(50, 0.8, -11.5);
  return pts;
}
const _cf = { p:new THREE.Vector3(), t:new THREE.Vector3(), n:new THREE.Vector3(), b:new THREE.Vector3() };
function coasterFrame(s, out){
  const C = COASTER; out = out || _cf;
  s = ((s % C.L) + C.L) % C.L;
  const f = s / C.ds, i = Math.floor(f) % C.n, j = (i + 1) % C.n, w = f - Math.floor(f);
  out.p.lerpVectors(C.P[i], C.P[j], w); out.t.lerpVectors(C.T[i], C.T[j], w).normalize();
  out.n.lerpVectors(C.N[i], C.N[j], w); out.n.addScaledVector(out.t, -out.n.dot(out.t)).normalize();
  out.b.crossVectors(out.t, out.n);
  return out;
}
function coasterSpeedAt(s){ const C = COASTER, f = clamp(s / C.ds, 0, C.n), i = Math.floor(f), w = f - i; return C.V[Math.min(i, C.n)] * (1 - w) + C.V[Math.min(i + 1, C.n)] * w; }
function buildCoaster(M){
  const curve = new THREE.CatmullRomCurve3(coasterPoints(), true, 'centripetal');
  curve.arcLengthDivisions = 6000;
  const L = curve.getLength(), n = Math.round(L / 0.1), ds = L / n, all = curve.getSpacedPoints(n);
  const P = all.slice(0, n), T = [], N = [], B = [];
  for (let i = 0; i < n; i++) T.push(P[(i + 1) % n].clone().sub(P[(i - 1 + n) % n]).normalize());
  const up = new THREE.Vector3(0, 1, 0), proj = (t) => up.clone().addScaledVector(t, -t.y).normalize();
  for (let i = 0; i < n; i++) N.push(proj(T[i]));
  let a = -1, b = -1;
  for (let i = 0; i < n; i++){ const p = P[i]; if (p.x > 55.6 && p.x < 67.4 && p.z < -22.8 && p.z > -27.2 && p.y > 1.3){ if (a < 0) a = i; b = i; } }
  if (a > 30 && b < n - 30){
    const s0 = a - 30, s1 = b + 30, cur = proj(T[s0]);
    for (let i = s0; i <= s1; i++){ const t = T[i]; cur.addScaledVector(t, -cur.dot(t)).normalize(); const w = i > b ? (i - b) / (s1 - b) : 0; N[i] = cur.clone().lerp(proj(t), w).normalize(); }
  }
  let ic = 0; for (let i = 0; i < n; i++) if (P[i].y > P[ic].y) ic = i;
  const V = new Float32Array(n + 1); let v = 3.2, vmax = 0;
  for (let i = 0; i <= n; i++){
    if (i < ic){ V[i] = 3.2; continue; }
    V[i] = v; vmax = Math.max(vmax, v);
    const p0 = P[i % n], p1 = P[(i + 1) % n];
    v = Math.sqrt(Math.max(v * v - 2 * 9.81 * (p1.y - p0.y) - 2 * (0.0035 * v * v + 0.1) * ds, 6.25));
  }
  const bank = new Float32Array(n);
  for (let i = 0; i < n; i++){
    if (a > 0 && i >= a - 30 && i <= b + 30) continue;
    const t0 = T[(i - 5 + n) % n], t1 = T[(i + 5) % n];
    if (Math.hypot(t0.x, t0.z) < 0.5 || Math.hypot(t1.x, t1.z) < 0.5) continue;
    const kap = angDiff(Math.atan2(t0.z, t0.x), Math.atan2(t1.z, t1.x)) / (10 * ds), vv = Math.min(V[i], 16);
    bank[i] = clamp(Math.atan(vv * vv * Math.abs(kap) / 9.81) * Math.sign(kap), -0.7, 0.7);
  }
  const K = 18;
  for (let i = 0; i < n; i++){
    let sm = 0; for (let k = -K; k <= K; k++) sm += bank[(i + k + n) % n]; sm /= 2 * K + 1;
    if (Math.abs(sm) > 1e-4){ const bb = new THREE.Vector3().crossVectors(T[i], N[i]); N[i] = N[i].clone().multiplyScalar(Math.cos(sm)).addScaledVector(bb, Math.sin(sm)).normalize(); }
    B.push(new THREE.Vector3().crossVectors(T[i], N[i]).normalize());
  }
  let it = a; if (a > 0) for (let i = a; i <= b; i++) if (P[i].y > P[it].y) it = i;
  Object.assign(COASTER, { L, n, ds, P, T, N, B, V, iCrest:ic, iLoopTop:it, loop:[a, b] });
  COASTER.stats = { height:Math.round(P[ic].y), kmh:Math.round(vmax * 3.6), mph:Math.round(vmax * 2.237), loop:Math.round(P[it].y + 0.4), length:Math.round(L) };
  if (a > 0) COASTER.tokenAt = P[it].clone().addScaledVector(N[it], 1.15);

  /* Rails, spine, ties and supports */
  const railMat = stdMat(0xd2462f, 0.38, 0.5), steel = stdMat(0xe6e1d6, 0.5, 0.3), footMat = stdMat(0xb9b2a5, 0.9);
  const tube = (sb, sn, rad, mat, seg) => {
    const arr = []; for (let i = 0; i < n; i += 3) arr.push(P[i].clone().addScaledVector(B[i], sb).addScaledVector(N[i], sn));
    const m = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(arr, true), arr.length, rad, seg, true), mat); scene.add(m); return m;
  };
  tube(-0.5, 0, 0.055, railMat, 7); tube(0.5, 0, 0.055, railMat, 7); tube(0, -0.42, 0.15, railMat, 9);
  const ties = new MatBatch(), webs = new MatBatch();
  for (let i = 0; i < n; i += 8){
    const p = P[i], tn = N[i], tb = B[i], tt = T[i];
    ties.add(boxMatrix(p.clone().addScaledVector(tn, -0.07), tb, tn, tt, 1.12, 0.07, 0.1));
    webs.add(boxMatrix(p.clone().addScaledVector(tn, -0.24), tb, tn, tt, 0.08, 0.34, 0.08));
  }
  const box1 = new THREE.BoxGeometry(1, 1, 1);
  ties.build(box1, steel); webs.build(box1, railMat);
  const cols = new MatBatch(), feet = new BoxBatch(), yAx = new THREE.Vector3(0, 1, 0);
  const leg = (from, to, rad) => { const d = to.clone().sub(from), len = d.length(), q = new THREE.Quaternion().setFromUnitVectors(yAx, d.clone().normalize()); const m = new THREE.Matrix4().compose(from.clone().add(to).multiplyScalar(0.5), q, new THREE.Vector3(rad, len, rad)); cols.add(m); };
  for (let i = 4; i < n; i += 30){
    if (a > 0 && i >= a - 8 && i <= b + 8) continue;
    const p = P[i]; if (N[i].y < 0.8) continue;
    const top = p.y - 0.42 - 0.15; if (top < 0.75) continue;
    let blocked = false;
    for (let j = 0; j < n && !blocked; j += 4){ const dj = Math.min(Math.abs(j - i), n - Math.abs(j - i)); if (dj < 40) continue; const q = P[j]; if (q.y < top - 0.4 && (q.x - p.x) ** 2 + (q.z - p.z) ** 2 < 2.4) blocked = true; }
    if (blocked) continue;
    const topP = new THREE.Vector3(p.x, top + 0.05, p.z);
    if (top > 7){
      const side = new THREE.Vector3(B[i].x, 0, B[i].z).normalize().multiplyScalar(Math.min(2.4, top * 0.16));
      for (const sg of [-1, 1]){ const base = new THREE.Vector3(p.x + side.x * sg, 0, p.z + side.z * sg); leg(base, topP, 1); feet.add(base.x, 0.08, base.z, 0.62, 0.16, 0.62, 0); }
      const mid = top * 0.5; leg(new THREE.Vector3(p.x - side.x * 0.5, mid, p.z - side.z * 0.5), new THREE.Vector3(p.x + side.x * 0.5, mid, p.z + side.z * 0.5), 0.6);
    } else { leg(new THREE.Vector3(p.x, 0, p.z), topP, 1); feet.add(p.x, 0.08, p.z, 0.6, 0.16, 0.6, 0); }
  }
  cols.build(new THREE.CylinderGeometry(0.15, 0.15, 1, 10), steel); feet.build(footMat, false);

  buildStation(M); buildTrain(); placeTrain(0);
}
function buildStation(M){
  const navy = stdMat(0x1d3b52, 0.55, 0.2), green = stdMat(0x2e4b3c, 0.55, 0.3), plat = stdMat(0xc4bcae, 0.9);
  flat(new THREE.PlaneGeometry(16, 5.2), stdMat(0x9a958c, 0.95), 50.9, 0.003, -11.0);
  addBox(13.6, 0.85, 1.85, plat, 50.9, 0.425, -9.8);
  addBox(13.6, 0.05, 0.14, stdMat(0xf2c14e, 0.6), 50.9, 0.87, -10.67);
  for (const x of [44.4, 50.9, 57.4]) for (const z of [-13.1, -8.95]) addBox(0.16, 3.8, 0.16, green, x, 1.9, z);
  addBox(14.4, 0.2, 4.8, green, 50.9, 3.9, -11.0);
  addBox(14.5, 0.12, 0.08, stdMat(0xf2c14e, 0.5), 50.9, 3.86, -8.56);
  addBox(14.0, 0.02, 4.4, stdMat(0xe6e1d6, 0.8), 50.9, 3.79, -11.0);
  const sign = addPlane(6.4, 0.88, basicMat(drawStationSign()), 50.9, 3.35, -8.86, 0);
  addBox(6.6, 0.98, 0.06, navy, 50.9, 3.35, -8.92);
  sign.userData.ride = 'coaster'; pickItems.push(sign);
  for (const x of [49.4, 54.6]){ addCyl(0.08, 0.08, 2.5, navy, x, 1.25, YARD.fenceZ, 10); }
  addBox(5.3, 0.1, 0.1, navy, 52, 2.5, YARD.fenceZ);
  const booth = new THREE.Group(); booth.position.set(49.1, 0, -7.7); booth.rotation.y = 0.35;
  addBox(1.08, 1.42, 0.08, navy, 0, 1.55, 0, 0, booth);
  const card = addPlane(1.0, 1.34, basicMat(drawRideSign('Comet Coaster', ['Lift hill ' + COASTER.stats.height + ' m', 'Up to ' + COASTER.stats.kmh + ' km/h', 'One loop', 'Gentle mode too'], '#d2462f')), 0, 1.55, 0.045, 0, booth);
  addCyl(0.05, 0.05, 0.9, navy, 0, 0.45, 0, 8, booth);
  card.userData.ride = 'coaster'; pickItems.push(card);
  scene.add(booth); OBST.push({ x:49.1, z:-7.7, r:0.5 });
}
function buildTrain(){
  const body = stdMat(0x27508f, 0.32, 0.25), trim = stdMat(0xe0b553, 0.35, 0.6), seat = stdMat(0x1d1f24, 0.7), chassis = stdMat(0x3b3f45, 0.5, 0.5), bar = stdMat(0xf2c14e, 0.4, 0.4), lamp = glowMatOf(0xfff3c8);
  COASTER.cars = [];
  for (let k = 0; k < 3; k++){
    const g = new THREE.Group(); g.matrixAutoUpdate = false; g.userData.noMerge = true;
    const picks = [];
    picks.push(addBox(1.26, 0.1, 1.86, chassis, 0, 0.16, 0, 0, g));
    picks.push(addBox(1.32, 0.46, 1.7, body, 0, 0.44, 0.04, 0, g));
    addBox(1.34, 0.07, 1.72, trim, 0, 0.64, 0.04, 0, g);
    for (const zz of [-0.36, 0.42]){
      addBox(1.1, 0.08, 0.42, seat, 0, 0.52, zz, 0, g);
      const back = addBox(1.1, 0.52, 0.08, seat, 0, 0.82, zz + 0.24, 0, g); back.rotation.x = -0.12;
      addBox(0.96, 0.05, 0.05, bar, 0, 0.86, zz - 0.3, 0, g);
    }
    if (k === 0){
      const nose = addBox(1.32, 0.34, 0.52, body, 0, 0.42, -0.98, 0, g); nose.rotation.x = 0.42; picks.push(nose);
      addBox(1.0, 0.07, 0.06, trim, 0, 0.56, -1.2, 0, g);
      for (const sx of [-0.42, 0.42]) addBox(0.16, 0.08, 0.04, lamp, sx, 0.38, -1.25, 0, g);
    }
    for (const sx of [-0.5, 0.5]) for (const sz of [-0.7, 0.7]) addBox(0.12, 0.16, 0.24, chassis, sx, 0.05, sz, 0, g);
    addBox(0.1, 0.08, 0.32, chassis, 0, 0.16, 1.08, 0, g);
    for (const m of picks){ m.userData.ride = 'coaster'; pickItems.push(m); }
    scene.add(g); COASTER.cars.push(g);
  }
}
const _tm = new THREE.Matrix4(), _tz = new THREE.Vector3();
function placeTrain(s){
  COASTER.cars.forEach((g, k) => {
    const f = coasterFrame(s - 2.15 * k);
    _tz.copy(f.t).negate(); _tm.makeBasis(f.b, f.n, _tz); _tm.setPosition(f.p);
    g.matrix.copy(_tm); g.matrixWorldNeedsUpdate = true;
  });
}

/* ---------------- Sky Drop ---------------- */
function buildDropTower(M){
  const { x, z, h } = DROP;
  const conc = stdMat(0xbdb6a8, 0.9), navy = stdMat(0x1d3b52, 0.55, 0.2), yellow = stdMat(0xf2c14e, 0.45, 0.3), seatMat = stdMat(0x1d1f24, 0.7);
  addCyl(2.3, 2.5, 0.5, conc, x, 0.25, z, 32);
  const colTex = repTex(canvasTower(), 1, h / 4);
  addCyl(0.72, 0.82, h, new THREE.MeshStandardMaterial({ map:colTex, roughness:0.5, metalness:0.2 }), x, h / 2, z, 28);
  const strip = glowMatOf(0xffd27a);
  for (let k = 0; k < 4; k++){ const a = Math.PI / 4 + k * Math.PI / 2; addBox(0.06, h - 3, 0.06, strip, x + Math.cos(a) * 0.76, (h - 3) / 2 + 1.5, z + Math.sin(a) * 0.76); }
  addCyl(1.25, 0.9, 1.5, navy, x, h + 0.75, z, 28);
  const band = new THREE.Mesh(new THREE.CylinderGeometry(1.28, 1.28, 0.9, 40, 1, true), new THREE.MeshBasicMaterial({ map:tex(drawTowerBand()), toneMapped:false }));
  band.position.set(x, h + 0.8, z); scene.add(band);
  addCyl(1.32, 1.32, 0.08, yellow, x, h + 1.55, z, 40);
  const beacon = new THREE.Mesh(new THREE.SphereGeometry(0.22, 16, 12), glowMatOf(0xff5a4a)); beacon.position.set(x, h + 1.8, z); scene.add(beacon);
  /* Ring of seats that rides the tower */
  const ring = new THREE.Group(); ring.position.set(x, DROP.base, z);
  addCyl(1.0, 1.0, 0.7, navy, 0, 0.35, 0, 28, ring);
  const torus = new THREE.Mesh(new THREE.TorusGeometry(1.5, 0.16, 10, 40), yellow); torus.rotation.x = Math.PI / 2; torus.position.y = 0.32; ring.add(torus);
  for (let k = 0; k < 8; k++){
    const a = k / 8 * Math.PI * 2, s = new THREE.Group();
    s.position.set(Math.cos(a) * 1.95, 0, Math.sin(a) * 1.95); s.rotation.y = Math.atan2(-Math.cos(a), -Math.sin(a));
    addBox(0.5, 0.08, 0.46, seatMat, 0, 0.42, 0, 0, s);
    addBox(0.5, 0.9, 0.08, seatMat, 0, 0.84, 0.24, 0, s);
    const barM = stdMat(0x2a3c4c, 0.4, 0.5);
    addBox(0.035, 0.035, 0.42, barM, -0.26, 0.98, 0.02, 0, s); addBox(0.035, 0.035, 0.42, barM, 0.26, 0.98, 0.02, 0, s);
    addBox(0.46, 0.035, 0.035, barM, 0, 0.7, -0.2, 0, s);
    ring.add(s);
  }
  ring.userData.noMerge = true; scene.add(ring); YA.ring = ring;
  const booth = new THREE.Group(); booth.position.set(70.3, 0, 11.1); booth.rotation.y = lookYaw(70.3, 11.1, 62, 5) + Math.PI;
  addBox(1.08, 1.42, 0.08, navy, 0, 1.55, 0, 0, booth);
  const card = addPlane(1.0, 1.34, basicMat(drawRideSign('Sky Drop', ['About 30 m up', 'See the whole campus', 'Then drop!', 'Gentle mode too'], '#7a5cff')), 0, 1.55, 0.045, 0, booth);
  addCyl(0.05, 0.05, 0.9, navy, 0, 0.45, 0, 8, booth);
  card.userData.ride = 'drop'; pickItems.push(card);
  scene.add(booth); OBST.push({ x:70.3, z:11.1, r:0.5 }, { x, z, r:4.9 });
}

/* ---------------- Ocean Dive dome ---------------- */
function buildDiveDome(M){
  const { x, z, r } = DOME;
  const conc = stdMat(0xbdb6a8, 0.9), teal = stdMat(0x1f6f8b, 0.5, 0.15), yellow = stdMat(0xf2c14e, 0.45, 0.3);
  const dome = new THREE.Mesh(new THREE.SphereGeometry(r, 48, 18, 0, Math.PI * 2, 0, Math.PI / 2), new THREE.MeshStandardMaterial({ map:tex(canvasDome()), roughness:0.35, metalness:0.12 }));
  dome.position.set(x, 0.3, z); scene.add(dome);
  addCyl(r + 0.1, r + 0.22, 0.34, conc, x, 0.17, z, 48);
  const glow = glowMatOf(0x9fe9ff);
  for (let k = 0; k < 7; k++){
    const a = Math.PI / 2 + 0.55 + k * 0.72, el = 0.5, d = new THREE.Vector3(Math.cos(a) * Math.cos(el), Math.sin(el), Math.sin(a) * Math.cos(el));
    const ph = new THREE.Mesh(new THREE.CircleGeometry(0.34, 24), glow); ph.position.set(x + d.x * (r + 0.02), 0.3 + d.y * (r + 0.02), z + d.z * (r + 0.02)); ph.lookAt(x + d.x * 10, 0.3 + d.y * 10, z + d.z * 10); scene.add(ph);
    const rim = new THREE.Mesh(new THREE.TorusGeometry(0.36, 0.05, 8, 24), yellow); rim.position.copy(ph.position); rim.quaternion.copy(ph.quaternion); scene.add(rim);
  }
  const zf = z - r - 1.25;
  addBox(2.7, 2.75, 1.9, teal, x, 1.375, z - r - 0.3);
  addBox(2.82, 0.14, 2.0, yellow, x, 2.8, z - r - 0.3);
  const portalTex = repTex(canvasPortal(), 1, 1); YA.portal = portalTex;
  const portal = addPlane(1.8, 2.0, new THREE.MeshBasicMaterial({ map:portalTex, toneMapped:false }), x, 1.1, zf - 0.01, Math.PI);
  for (const dx of [-0.96, 0.96]) addBox(0.12, 2.16, 0.12, yellow, x + dx, 1.08, zf - 0.02);
  addBox(2.04, 0.12, 0.12, yellow, x, 2.16, zf - 0.02);
  const sign = addPlane(2.4, 0.48, basicMat(drawTableCard('OCEAN DIVE', 'Swim with sea creatures', '#1d3b52', '#f2c14e')), x, 2.48, zf - 0.02, Math.PI);
  for (const m of [portal, sign]){ m.userData.ride = 'dive'; pickItems.push(m); }
  const booth = new THREE.Group(); booth.position.set(x - 2.6, 0, zf - 0.9); booth.rotation.y = Math.PI + 0.25;
  addBox(1.08, 1.42, 0.08, stdMat(0x1d3b52, 0.55, 0.2), 0, 1.55, 0, 0, booth);
  const card = addPlane(1.0, 1.34, basicMat(drawRideSign('Ocean Dive', ['Coral reef & kelp', 'Fish schools, turtle,', 'manta & whale shark', 'About a minute'], '#1f9bb6')), 0, 1.55, 0.045, 0, booth);
  addCyl(0.05, 0.05, 0.9, stdMat(0x1d3b52, 0.55, 0.2), 0, 0.45, 0, 8, booth);
  card.userData.ride = 'dive'; pickItems.push(card);
  scene.add(booth);
  OBST.push({ x, z, r:r + 0.5 }, { x, z:z - r - 0.3, r:1.7 }, { x:x - 2.6, z:zf - 0.9, r:0.5 });
}

/* ---------------- Swings, slide and spinner ---------------- */
function buildSwings(x, z){
  const red = stdMat(0xd2462f, 0.45, 0.35), chain = stdMat(0x8a9096, 0.4, 0.7), seat = stdMat(0x1d1f24, 0.7);
  for (const sx of [-2.5, 2.5]) for (const sz of [-0.95, 0.95]){ const l = addBox(0.09, 2.85, 0.09, red, x + sx, 1.36, z + sz * 0.5); l.rotation.x = -Math.sign(sz) * 0.33; OBST.push({ x:x + sx, z:z + sz, r:0.25 }); }
  const bar = addCyl(0.06, 0.06, 5.2, red, x, 2.7, z, 10); bar.rotation.z = Math.PI / 2;
  YA.swings = [];
  [-1.4, 0, 1.4].forEach((dx, k) => {
    const pv = new THREE.Group(); pv.position.set(x + dx, 2.66, z);
    for (const s of [-0.22, 0.22]) addBox(0.02, 2.1, 0.02, chain, s, -1.05, 0, 0, pv);
    addBox(0.52, 0.05, 0.22, seat, 0, -2.1, 0, 0, pv);
    const hit = addBox(0.7, 0.5, 0.5, PICK_PROXY, 0, -1.95, 0, 0, pv); hit.userData.swing = k; pickItems.push(hit);
    pv.userData.noMerge = true; scene.add(pv); YA.swings.push(pv);
  });
}
function buildSlide(x, z){
  const teal = stdMat(0x1f9bb6, 0.45, 0.2), yellow = stdMat(0xf2c14e, 0.45, 0.2), red = stdMat(0xd2462f, 0.45, 0.35);
  for (const sx of [-0.6, 0.6]) for (const sz of [-0.6, 0.6]) addBox(0.1, 2.6, 0.1, red, x + sx, 1.3, z + sz);
  addBox(1.3, 0.1, 1.3, yellow, x, 1.6, z);
  for (const sz of [-0.62, 0.62]) addBox(1.3, 0.06, 0.06, red, x, 2.5, z + sz);
  for (const sx of [-0.25, 0.25]) addBox(0.06, 1.6, 0.06, red, x - 0.95 + sx * 0, 0.8, z + sx * 1.6);
  for (let y = 0.3; y < 1.6; y += 0.3) addBox(0.06, 0.05, 0.8, yellow, x - 0.95, y, z);
  const ch = new THREE.Group(); ch.position.set(x + 0.62, 1.62, z); ch.rotation.z = -0.52;
  addBox(3.3, 0.05, 0.62, teal, 1.65, 0, 0, 0, ch);
  for (const sz of [-0.33, 0.33]) addBox(3.3, 0.22, 0.04, teal, 1.65, 0.1, sz, 0, ch);
  scene.add(ch);
  addBox(0.8, 0.05, 0.66, teal, x + 3.6, 0.05, z);
  OBST.push({ x, z, r:1.2 }, { x:x + 1.8, z, r:0.8 }, { x:x + 3.3, z, r:0.7 });
}
function buildSpinner(x, z){
  const g = new THREE.Group(); g.position.set(x, 0, z);
  const deck = new THREE.Mesh(new THREE.CylinderGeometry(1.6, 1.6, 0.12, 40), stdMat(0xf2c14e, 0.45, 0.2)); deck.position.y = 0.32; g.add(deck);
  const red = stdMat(0xd2462f, 0.45, 0.35), navy = stdMat(0x1d3b52, 0.55, 0.2);
  for (let k = 0; k < 6; k++){ const a = k / 6 * Math.PI * 2; const w = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.025, 0.5), k % 2 ? red : navy); w.position.set(Math.cos(a) * 0.8, 0.385, Math.sin(a) * 0.8); w.rotation.y = -a; g.add(w); addBox(0.05, 0.8, 0.05, stdMat(0xe6e1d6, 0.4, 0.5), Math.cos(a) * 1.25, 0.78, Math.sin(a) * 1.25, 0, g); }
  const rim = new THREE.Mesh(new THREE.TorusGeometry(1.25, 0.03, 6, 40), stdMat(0xe6e1d6, 0.4, 0.5)); rim.rotation.x = Math.PI / 2; rim.position.y = 1.18; g.add(rim);
  addCyl(0.12, 0.12, 0.9, stdMat(0x3b3f45, 0.5, 0.5), 0, 0.5, 0, 12, g);
  const hit = new THREE.Mesh(new THREE.CylinderGeometry(1.65, 1.65, 1.0, 20), PICK_PROXY); hit.position.y = 0.6; hit.userData.spin = true; g.add(hit); pickItems.push(hit);
  g.userData.noMerge = true; scene.add(g); YA.spinner = g; OBST.push({ x, z, r:1.9 });
}
