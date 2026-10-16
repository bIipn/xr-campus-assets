/* ================================================================
   Room 101: the 3D Art Studio. Brushes, shapes, symmetry, a turntable
   and a blank canvas, all painted in the air
   ================================================================ */
const PAINT_COLORS = ['#ff5a8a', '#ff8f3d', '#ffd166', '#b8f35a', '#5ee6c8', '#7aa8ff', '#c38bff', '#ff7ad9', '#ffffff', '#9aa1a6', '#24262b', '#8a5a3a'];
const PAINT_SIZES = [0.012, 0.024, 0.05, 0.09];
const STAMP_SIZES = [0.08, 0.16, 0.3, 0.5];
const BRUSHES = [
  { id:'neon', name:'Neon' }, { id:'paint', name:'Paint' }, { id:'ribbon', name:'Ribbon' }, { id:'chrome', name:'Chrome' },
  { id:'rainbow', name:'Rainbow' }, { id:'beads', name:'Beads' }, { id:'sparkle', name:'Sparkle' }
];
const SHAPES = [
  { id:'cube', name:'Cube' }, { id:'sphere', name:'Sphere' }, { id:'cone', name:'Cone' }, { id:'cylinder', name:'Cylinder' },
  { id:'torus', name:'Ring' }, { id:'star', name:'Star' }, { id:'heart', name:'Heart' }, { id:'pyramid', name:'Pyramid' }
];
const PAINT_KEY = 'xr-campus-paint-v1';
const PAINT_SPOT = { x:19, z:-6.4, yaw:0, pitch:0.06 };
const STUDIO_BOX = { x0:14.15, x1:23.85, y0:0.04, y1:3.5, z0:-12.85, z1:-4.9 };
const PAINT_C = { x:19, z:-8.9 };   /* the middle of the room: mirror line, ×6 axis and turntable */
const PAINT_VERTS = 1600000;
const paint = { on:false, look:false, color:PAINT_COLORS[0], brush:'neon', shape:null, sizeI:1, sym:'', canvas:'room', spin:false, spinA:0, dist:2.0,
  strokes:[], meshes:[], cur:null, curObj:null, root:null, group:null, matCache:{}, geoCache:{}, tip:null, voids:{}, pending:false };

function paintSize(){ return paint.shape ? STAMP_SIZES[paint.sizeI] : PAINT_SIZES[paint.sizeI]; }
function finishOf(b){ return b === 'sparkle' ? 'neon' : b === 'beads' ? 'gloss' : b === 'ribbon' ? 'satin' : b || 'paint'; }
function paintMat(fin, color){
  const k = fin + '|' + (fin === 'rainbow' || fin === 'rainbowI' ? '' : color);
  if (paint.matCache[k]) return paint.matCache[k];
  const col = new THREE.Color(parseInt(String(color || '#ffffff').slice(1), 16));
  let m;
  if (fin === 'neon') m = new THREE.MeshBasicMaterial({ color:col.multiplyScalar(2.4), toneMapped:false });
  else if (fin === 'rainbow') m = new THREE.MeshBasicMaterial({ color:new THREE.Color(1.5, 1.5, 1.5), vertexColors:true, toneMapped:false });
  else if (fin === 'rainbowI') m = new THREE.MeshBasicMaterial({ color:new THREE.Color(1.5, 1.5, 1.5), toneMapped:false });
  else if (fin === 'chrome') m = new THREE.MeshStandardMaterial({ color:col.lerp(new THREE.Color(1, 1, 1), 0.35), metalness:1, roughness:0.13 });
  else if (fin === 'satin') m = new THREE.MeshStandardMaterial({ color:col, roughness:0.42, metalness:0.08, side:THREE.DoubleSide, emissive:col.clone().multiplyScalar(0.2) });
  else if (fin === 'gloss') m = new THREE.MeshStandardMaterial({ color:col, roughness:0.15, metalness:0.12 });
  else m = new THREE.MeshStandardMaterial({ color:col, roughness:0.6 });
  return (paint.matCache[k] = m);
}

/* ---------- Geometry ---------- */
function mergeIndexed(geos){
  let nv = 0, ni = 0; const hasC = geos.every((g) => g.attributes.color);
  for (const g of geos){ nv += g.attributes.position.count; ni += g.index ? g.index.count : g.attributes.position.count; }
  const pos = new Float32Array(nv * 3), nor = new Float32Array(nv * 3), col = hasC ? new Float32Array(nv * 3) : null, idx = new Uint32Array(ni);
  let ov = 0, oi = 0;
  for (const g of geos){
    const n = g.attributes.position.count;
    pos.set(g.attributes.position.array, ov * 3); nor.set(g.attributes.normal.array, ov * 3); if (col) col.set(g.attributes.color.array, ov * 3);
    if (g.index){ const a = g.index.array; for (let i = 0; i < a.length; i++) idx[oi + i] = a[i] + ov; oi += a.length; }
    else { for (let i = 0; i < n; i++) idx[oi + i] = ov + i; oi += n; }
    ov += n;
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.BufferAttribute(pos, 3)); out.setAttribute('normal', new THREE.BufferAttribute(nor, 3));
  if (col) out.setAttribute('color', new THREE.BufferAttribute(col, 3));
  out.setIndex(new THREE.BufferAttribute(idx, 1));
  return out;
}
function symMats(sym){
  const out = [new THREE.Matrix4()];
  if (sym === 'x') out.push(new THREE.Matrix4().makeTranslation(2 * PAINT_C.x, 0, 0).multiply(new THREE.Matrix4().makeScale(-1, 1, 1)));
  else if (sym === 'r6') for (let k = 1; k < 6; k++) out.push(new THREE.Matrix4().makeTranslation(PAINT_C.x, 0, PAINT_C.z).multiply(new THREE.Matrix4().makeRotationY(k * Math.PI / 3)).multiply(new THREE.Matrix4().makeTranslation(-PAINT_C.x, 0, -PAINT_C.z)));
  return out;
}
/* Symmetry is baked into one mesh per stroke, so a mirrored stroke costs one draw call, not six */
function bakeSym(g, sym){
  const mats = symMats(sym); if (mats.length === 1) return g;
  const parts = mats.map((M, i) => {
    if (!i) return g;
    const c = g.clone(); c.applyMatrix4(M);
    if (M.determinant() < 0){ const a = c.index.array; for (let j = 0; j < a.length; j += 3){ const t = a[j + 1]; a[j + 1] = a[j + 2]; a[j + 2] = t; } }
    return c;
  });
  const out = mergeIndexed(parts); for (const p of parts) p.dispose();
  return out;
}
function symInstances(list, sym){
  const mats = symMats(sym); if (mats.length === 1) return list;
  const out = list.slice(), flipL = new THREE.Matrix4().makeScale(-1, 1, 1);
  for (let k = 1; k < mats.length; k++) for (const M of list){ const m = mats[k].clone().multiply(M); if (mats[k].determinant() < 0) m.multiply(flipL); out.push(m); }
  return out;
}
function strokePts(st){ const P = st.p, a = []; for (let i = 0; i + 2 < P.length; i += 3) a.push(new THREE.Vector3(P[i], P[i + 1], P[i + 2])); return a; }
function hueCol(h){ return new THREE.Color().setHSL(((h % 1) + 1) % 1, 1, 0.5); }
function paintColorize(g, h){
  const n = g.attributes.position.count, c = new Float32Array(n * 3), col = hueCol(h);
  for (let i = 0; i < n; i++){ c[i * 3] = col.r; c[i * 3 + 1] = col.g; c[i * 3 + 2] = col.b; }
  g.setAttribute('color', new THREE.BufferAttribute(c, 3));
}
function tubeGeo(pts, r, hue){
  const parts = [], radial = r > 0.04 ? 12 : 8;
  let hEnd = hue;
  if (pts.length >= 2){
    const curve = new THREE.CatmullRomCurve3(pts, false, 'centripetal'), seg = Math.max(2, Math.min(360, pts.length * 2));
    const tube = new THREE.TubeGeometry(curve, seg, r, radial, false);
    tube.deleteAttribute('uv');
    if (hue != null){
      const L = curve.getLength(), n = tube.attributes.position.count, c = new Float32Array(n * 3), col = new THREE.Color();
      for (let v = 0; v < n; v++){ const ring = Math.floor(v / (radial + 1)); col.copy(hueCol(hue + ring / seg * L / 2.4)); c[v * 3] = col.r; c[v * 3 + 1] = col.g; c[v * 3 + 2] = col.b; }
      tube.setAttribute('color', new THREE.BufferAttribute(c, 3)); hEnd = hue + L / 2.4;
    }
    parts.push(tube);
  }
  const cap = (p, h) => { const s = new THREE.SphereGeometry(r, radial, Math.max(6, radial / 2 + 2)); s.deleteAttribute('uv'); s.translate(p.x, p.y, p.z); if (hue != null) paintColorize(s, h); return s; };
  parts.push(cap(pts[0], hue));
  if (pts.length >= 2) parts.push(cap(pts[pts.length - 1], hEnd));
  const out = mergeIndexed(parts); for (const p of parts) p.dispose();
  return out;
}
function ribbonGeo(st, pts){
  const w = st.s * 2.6, f = new THREE.Vector3().fromArray(st.f || [0, 0, -1]); f.y = 0; if (f.lengthSq() < 1e-6) f.set(0, 0, -1); f.normalize();
  let P = pts;
  if (pts.length >= 2) P = new THREE.CatmullRomCurve3(pts, false, 'centripetal').getSpacedPoints(Math.max(2, Math.min(300, pts.length * 2)));
  else P = [pts[0].clone().addScaledVector(new THREE.Vector3(f.z, 0, -f.x), -0.01), pts[0].clone().addScaledVector(new THREE.Vector3(f.z, 0, -f.x), 0.01)];
  const n = P.length, pos = new Float32Array(n * 6), nor = new Float32Array(n * 6), idx = [];
  const t = new THREE.Vector3(), s = new THREE.Vector3(), nn = new THREE.Vector3(), prev = new THREE.Vector3();
  for (let i = 0; i < n; i++){
    t.subVectors(P[Math.min(n - 1, i + 1)], P[Math.max(0, i - 1)]); if (t.lengthSq() < 1e-10) t.set(1, 0, 0); t.normalize();
    s.crossVectors(t, f); if (s.lengthSq() < 1e-6) s.copy(prev.lengthSq() ? prev : new THREE.Vector3(0, 1, 0)); s.normalize();
    if (i && s.dot(prev) < 0) s.negate(); prev.copy(s);
    const hw = w / 2 * Math.min(1, (i + 1) / 4, (n - i) / 4);
    nn.crossVectors(s, t).normalize();
    pos[i * 6] = P[i].x + s.x * hw; pos[i * 6 + 1] = P[i].y + s.y * hw; pos[i * 6 + 2] = P[i].z + s.z * hw;
    pos[i * 6 + 3] = P[i].x - s.x * hw; pos[i * 6 + 4] = P[i].y - s.y * hw; pos[i * 6 + 5] = P[i].z - s.z * hw;
    nor.set([nn.x, nn.y, nn.z, nn.x, nn.y, nn.z], i * 6);
    if (i < n - 1){ const a = i * 2; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
  }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('normal', new THREE.BufferAttribute(nor, 3)); g.setIndex(new THREE.BufferAttribute(new Uint32Array(idx), 1));
  return g;
}
function samplePath(pts, step){
  if (pts.length < 2) return [pts[0].clone()];
  const curve = new THREE.CatmullRomCurve3(pts, false, 'centripetal'), n = Math.max(1, Math.min(400, Math.floor(curve.getLength() / step)));
  const out = []; for (let i = 0; i <= n; i++) out.push(curve.getPointAt(i / n)); return out;
}
function shapeGeo(id){
  if (paint.geoCache[id]) return paint.geoCache[id];
  let g;
  if (id === 'bead') g = new THREE.SphereGeometry(1, 16, 12);
  else if (id === 'cube') g = new THREE.BoxGeometry(1, 1, 1);
  else if (id === 'sphere') g = new THREE.SphereGeometry(0.5, 28, 18);
  else if (id === 'cone') g = new THREE.ConeGeometry(0.5, 1, 28);
  else if (id === 'cylinder') g = new THREE.CylinderGeometry(0.5, 0.5, 1, 28);
  else if (id === 'torus') g = new THREE.TorusGeometry(0.36, 0.14, 16, 40);
  else if (id === 'pyramid'){ g = new THREE.ConeGeometry(0.62, 1, 4); g.rotateY(Math.PI / 4); }
  else {
    const s = new THREE.Shape();
    if (id === 'heart'){ s.moveTo(0, -0.42); s.bezierCurveTo(-0.08, -0.32, -0.5, -0.06, -0.5, 0.17); s.bezierCurveTo(-0.5, 0.42, -0.2, 0.5, 0, 0.29); s.bezierCurveTo(0.2, 0.5, 0.5, 0.42, 0.5, 0.17); s.bezierCurveTo(0.5, -0.06, 0.08, -0.32, 0, -0.42); }
    else for (let i = 0; i < 10; i++){ const a = Math.PI / 2 + i * Math.PI / 5, rad = i % 2 ? 0.21 : 0.5; if (i) s.lineTo(Math.cos(a) * rad, Math.sin(a) * rad); else s.moveTo(Math.cos(a) * rad, Math.sin(a) * rad); }
    g = new THREE.ExtrudeGeometry(s, { depth:0.18, bevelEnabled:true, bevelThickness:0.05, bevelSize:0.035, bevelSegments:2, curveSegments:14 });
    g.center();
  }
  g.userData.shared = true;
  return (paint.geoCache[id] = g);
}
function instObject(geo, mat, mats, cols){
  const m = new THREE.InstancedMesh(geo, mat, mats.length);
  mats.forEach((M, i) => m.setMatrixAt(i, M)); m.instanceMatrix.needsUpdate = true;
  if (cols){ cols.forEach((c, i) => m.setColorAt(i, c)); m.instanceColor.needsUpdate = true; }
  m.computeBoundingSphere();
  return m;
}
function dotsObject(st, pts){
  const sparkle = st.b === 'sparkle', r = st.s, P = samplePath(pts, r * (sparkle ? 3.4 : 2.3)), rr = rnd(P.length * 7 + 3), q = new THREE.Quaternion(), e = new THREE.Euler();
  const list = P.map((p) => { if (sparkle) q.setFromEuler(e.set(rr() * 6.28, rr() * 6.28, rr() * 6.28)); else q.identity(); const k = sparkle ? r * (2.2 + rr() * 1.4) : r * 1.1; return new THREE.Matrix4().compose(p, q, new THREE.Vector3(k, k, k)); });
  return instObject(shapeGeo(sparkle ? 'star' : 'bead'), paintMat(sparkle ? 'neon' : 'gloss', st.c), symInstances(list, st.m));
}
function stampObject(st, pts){
  const size = st.s, P = pts.length > 1 ? samplePath(pts, size * 1.15) : [pts[0]];
  const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(0, st.y || 0, 0)), sc = new THREE.Vector3(size, size, size);
  const list = P.map((p) => new THREE.Matrix4().compose(p, q, sc)), mats = symInstances(list, st.m), fin = finishOf(st.fb);
  if (fin === 'rainbow') return instObject(shapeGeo(st.sh), paintMat('rainbowI'), mats, mats.map((M, i) => hueCol((st.h || 0) + (i % list.length) * 0.09)));
  return instObject(shapeGeo(st.sh), paintMat(fin, st.c), mats);
}
function strokeObject(st, live){
  const pts = strokePts(st); if (!pts.length) return null;
  const sym = live ? '' : st.m || '';
  if (st.sh) return stampObject(Object.assign({}, st, { m:sym }), pts);
  if (st.b === 'beads' || st.b === 'sparkle') return dotsObject(Object.assign({}, st, { m:sym }), pts);
  if (st.b === 'ribbon') return new THREE.Mesh(bakeSym(ribbonGeo(st, pts), sym), paintMat('satin', st.c));
  const rainbow = st.b === 'rainbow';
  return new THREE.Mesh(bakeSym(tubeGeo(pts, st.s, rainbow ? st.h || 0 : null), sym), rainbow ? paintMat('rainbow') : paintMat(finishOf(st.b), st.c));
}
/* While drawing, symmetric copies are cheap clones that share the stroke's geometry */
function previewObject(st){
  const base = strokeObject(st, true); if (!base) return null;
  const mats = symMats(st.m); if (mats.length === 1) return base;
  const g = new THREE.Group(); g.add(base);
  for (let k = 1; k < mats.length; k++){ const c = base.clone(); c.matrixAutoUpdate = false; c.matrix.copy(mats[k]); g.add(c); }
  return g;
}
function objVerts(o){ let n = 0; o.traverse((m) => { if (m.geometry && !m.geometry.userData.shared) n += m.geometry.attributes.position.count; else if (m.isInstancedMesh) n += m.count * 40; }); return n; }
function disposeObj(o){ o.traverse((m) => { if (m.geometry && !m.geometry.userData.shared) m.geometry.dispose(); if (m.isInstancedMesh) m.dispose(); }); }
function normStroke(st){
  if (!st || !Array.isArray(st.p) || st.p.length < 3) return null;
  if (!st.b && !st.sh) st.b = st.g === false ? 'paint' : 'neon';
  delete st.g;
  if (typeof st.c !== 'string' || !/^#[0-9a-f]{6}$/i.test(st.c)) st.c = '#ffffff';
  if (!(st.s > 0 && st.s < 1)) st.s = 0.024;
  return st;
}

/* ---------- The studio, the turntable and the blank canvases ---------- */
function initPaint(){
  paint.root = new THREE.Group(); paint.root.position.set(PAINT_C.x, 0, PAINT_C.z); paint.root.userData.noMerge = true; scene.add(paint.root);
  paint.group = new THREE.Group(); paint.group.position.set(-PAINT_C.x, 0, -PAINT_C.z); paint.root.add(paint.group);
  const tipMat = new THREE.MeshBasicMaterial({ color:0xffffff, toneMapped:false, transparent:true, opacity:0.75, depthTest:false });
  paint.tip = new THREE.Mesh(new THREE.SphereGeometry(1, 16, 10), tipMat); paint.tip.visible = false; paint.tip.renderOrder = 10; scene.add(paint.tip);
  buildSample();
  let saved = null;
  try { saved = JSON.parse(localStorage.getItem(PAINT_KEY) || 'null'); } catch (_) { saved = null; }
  if (Array.isArray(saved)) for (const raw of saved){ const st = normStroke(raw); if (!st) continue; const o = strokeObject(st); if (!o) continue; o.userData.verts = objVerts(o); paint.strokes.push(st); paint.meshes.push(o); paint.group.add(o); }
}
function savePaint(){
  let list = paint.strokes.slice(-250);
  for (let k = 0; k < 4; k++){
    try { localStorage.setItem(PAINT_KEY, JSON.stringify(list)); return; } catch (_) { if (list.length < 2) return; list = list.slice(Math.floor(list.length / 2)); }
  }
}
function buildSample(){
  const cx = 21.6, cz = -10.2, sample = [], g = new THREE.Group();
  const ribbon = (fn, n, c, s, b) => { const p = []; for (let i = 0; i <= n; i++){ const v = fn(i / n); p.push(+v[0].toFixed(3), +v[1].toFixed(3), +v[2].toFixed(3)); } sample.push({ c, s, b:b || 'neon', p }); };
  ribbon((t) => { const a = t * Math.PI * 6; return [cx + Math.cos(a) * (0.55 - t * 0.25), 0.25 + t * 2.0, cz + Math.sin(a) * (0.55 - t * 0.25)]; }, 160, '#5ee6c8', 0.022);
  for (const side of [-1, 1]){
    ribbon((t) => { const a = t * Math.PI * 2; return [cx + side * (0.05 + 0.32 * Math.sin(a) * Math.sin(a / 2 + 0.2)), 2.05 + 0.26 * Math.sin(a), cz + 0.02 * Math.cos(a)]; }, 80, '#ff8f3d', 0.02);
    ribbon((t) => { const a = t * Math.PI * 2; return [cx + side * (0.04 + 0.2 * Math.sin(a) * Math.sin(a / 2 + 0.2)), 1.82 - 0.18 * Math.sin(a), cz + 0.02 * Math.cos(a)]; }, 60, '#ffd166', 0.018);
  }
  ribbon((t) => [cx, 1.78 + t * 0.42, cz], 10, '#24262b', 0.02, 'paint');
  for (let f = 0; f < 3; f++){
    const fx = cx - 0.55 + f * 0.55, fz = cz + 0.55, col = ['#ff5a8a', '#c38bff', '#7aa8ff'][f];
    ribbon((t) => [fx, 0.1 + t * 0.55, fz], 12, '#4fbf6a', 0.012, 'paint');
    ribbon((t) => { const a = t * Math.PI * 2; const rr = 0.09 + 0.05 * Math.cos(a * 5); return [fx + Math.cos(a) * rr, 0.7 + Math.sin(a) * rr, fz]; }, 60, col, 0.014);
  }
  for (const st of sample){ const o = strokeObject(st); if (o) g.add(o); }
  (WING.school || scene).add(g);
}
function voidCanvas(stops){
  const c = mk(16, 512), ctx = c.getContext('2d'), gr = ctx.createLinearGradient(0, 0, 0, 512);
  for (const [k, col] of stops) gr.addColorStop(k, col);
  ctx.fillStyle = gr; ctx.fillRect(0, 0, 16, 512); return c;
}
function voidGrid(bg, line, glow){
  const S = 256, c = mk(S, S), ctx = c.getContext('2d');
  ctx.fillStyle = bg; ctx.fillRect(0, 0, S, S);
  ctx.strokeStyle = line; ctx.lineWidth = glow ? 3 : 2; if (glow){ ctx.shadowColor = line; ctx.shadowBlur = 6; }
  ctx.strokeRect(1, 1, S - 2, S - 2);
  return c;
}
function buildVoid(kind){
  if (paint.voids[kind]) return paint.voids[kind];
  const g = new THREE.Group(), night = kind === 'night', R = 14;
  g.position.set(PAINT_C.x, 0, PAINT_C.z); g.visible = false; g.userData.noMerge = true;
  const skyC = night ? voidCanvas([[0, '#05071a'], [0.42, '#141a44'], [0.5, '#3a2a6a'], [0.53, '#0b0e24'], [1, '#05060f']]) : voidCanvas([[0, '#dfe7ef'], [0.47, '#f7f9fb'], [0.5, '#ffffff'], [0.53, '#eef1f4'], [1, '#e2e6ea']]);
  const sky = new THREE.Mesh(new THREE.SphereGeometry(R, 48, 32), new THREE.MeshBasicMaterial({ map:tex(skyC), side:THREE.BackSide, depthWrite:false, fog:false, toneMapped:false, color:night ? 0xffffff : new THREE.Color(1.1, 1.1, 1.1) }));
  sky.renderOrder = -1; sky.userData.noAO = true; g.add(sky);
  const gt = repTex(night ? voidGrid('#090c20', 'rgba(94,230,200,0.55)', true) : voidGrid('#f4f6f8', 'rgba(120,135,150,0.35)'), R * 2, R * 2);
  const floorMat = night ? new THREE.MeshBasicMaterial({ map:gt, fog:false }) : new THREE.MeshStandardMaterial({ map:gt, roughness:0.92 });
  const floor = new THREE.Mesh(new THREE.CircleGeometry(R, 64), floorMat); floor.rotation.x = -Math.PI / 2; floor.position.y = 0.003; floor.userData.floor = true; g.add(floor); floors.push(floor);
  if (night){
    const N = 700, pos = new Float32Array(N * 3), r = rnd(31);
    for (let i = 0; i < N; i++){ const a = r() * Math.PI * 2, y = 0.05 + r() * 0.95, rad = Math.sqrt(1 - y * y) * (R - 0.4); pos[i * 3] = Math.cos(a) * rad; pos[i * 3 + 1] = y * (R - 0.4); pos[i * 3 + 2] = Math.sin(a) * rad; }
    const sg = new THREE.BufferGeometry(); sg.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.add(new THREE.Points(sg, new THREE.PointsMaterial({ color:0xffffff, size:2.2, sizeAttenuation:false, fog:false, toneMapped:false })));
  }
  scene.add(g); paint.voids[kind] = g;
  return g;
}
function paintVoidOn(){ return paint.on && paint.canvas !== 'room'; }
function setPaintCanvas(kind){
  paint.canvas = kind;
  if (kind !== 'room') buildVoid(kind);
  wake();
}
/* Faint guides show where Mirror and ×6 repeat your strokes */
function buildGuides(){
  const teal = (o) => new THREE.MeshBasicMaterial({ color:0x5ee6c8, transparent:true, opacity:o, depthWrite:false, side:THREE.DoubleSide, toneMapped:false });
  const L = STUDIO_BOX.z1 - STUDIO_BOX.z0, Hh = STUDIO_BOX.y1 - STUDIO_BOX.y0, zc = (STUDIO_BOX.z0 + STUDIO_BOX.z1) / 2;
  const x = new THREE.Group(), plane = new THREE.Mesh(new THREE.PlaneGeometry(L, Hh), teal(0.05)); plane.rotation.y = Math.PI / 2; plane.position.set(PAINT_C.x, STUDIO_BOX.y0 + Hh / 2, zc); x.add(plane);
  const edge = new THREE.LineSegments(new THREE.EdgesGeometry(plane.geometry), new THREE.LineBasicMaterial({ color:0x5ee6c8, transparent:true, opacity:0.4, toneMapped:false })); edge.rotation.y = Math.PI / 2; edge.position.copy(plane.position); x.add(edge);
  const r = new THREE.Group(), axis = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, Hh, 8), teal(0.55)); axis.position.set(PAINT_C.x, STUDIO_BOX.y0 + Hh / 2, PAINT_C.z); r.add(axis);
  for (let k = 0; k < 6; k++){ const sp = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.012), teal(0.35)); sp.rotation.x = -Math.PI / 2; sp.rotation.z = k * Math.PI / 3; sp.position.set(PAINT_C.x + Math.cos(k * Math.PI / 3) * 0.45, 0.012, PAINT_C.z - Math.sin(k * Math.PI / 3) * 0.45); r.add(sp); }
  for (const g of [x, r]){ g.visible = false; g.traverse((o) => { o.renderOrder = 2; o.userData.noAO = true; }); paint.group.add(g); }
  paint.guides = { x, r6:r };
}
function paintFrame(dt){
  if (!paint.root) return false;
  if (!paint.guides) buildGuides();
  paint.guides.x.visible = paint.on && paint.sym === 'x'; paint.guides.r6.visible = paint.on && paint.sym === 'r6';
  const vo = paintVoidOn();
  for (const k in paint.voids) paint.voids[k].visible = vo && paint.canvas === k;
  paint.root.visible = vo || !!(WING.school && WING.school.visible);
  if (paint.spin && paint.root.visible && !REDUCED){ paint.spinA = (paint.spinA + dt * 0.55) % (Math.PI * 2); paint.root.rotation.y = paint.spinA; return true; }
  return false;
}

/* ---------- Drawing with the pointer ---------- */
function planeHit(cx, cy){
  const rect = ui.scene.getBoundingClientRect();
  const ndc = new THREE.Vector2(((cx - rect.left) / rect.width) * 2 - 1, -((cy - rect.top) / rect.height) * 2 + 1);
  /* Use where the player is right now, even if a frame hasn't drawn since they moved */
  camera.position.set(cam.x, eyeY(), cam.z); camera.rotation.set(cam.pitch, cam.yaw, 0); camera.updateMatrixWorld();
  raycaster.setFromCamera(ndc, camera);
  const f = new THREE.Vector3(-Math.sin(cam.yaw), 0, -Math.cos(cam.yaw));
  const p0 = new THREE.Vector3(cam.x, EYE, cam.z).addScaledVector(f, paint.dist);
  const pl = new THREE.Plane().setFromNormalAndCoplanarPoint(f.clone().negate(), p0);
  const hit = new THREE.Vector3();
  if (!raycaster.ray.intersectPlane(pl, hit)) return null;
  hit.x = clamp(hit.x, STUDIO_BOX.x0, STUDIO_BOX.x1); hit.y = clamp(hit.y, STUDIO_BOX.y0, STUDIO_BOX.y1); hit.z = clamp(hit.z, STUDIO_BOX.z0, STUDIO_BOX.z1);
  return hit;
}
function toCanvas(h){ paint.root.updateMatrixWorld(true); return paint.group.worldToLocal(h.clone()); }
function inStudio(){ return roomAt(cam.x, cam.z).id === 'studio'; }
function paintDown(cx, cy){
  const h = planeHit(cx, cy); if (!h) return;
  const p = toCanvas(h), f = new THREE.Vector3(-Math.sin(cam.yaw - paint.spinA), 0, -Math.cos(cam.yaw - paint.spinA));
  const st = { c:paint.color, s:paintSize(), m:paint.sym, p:[+p.x.toFixed(3), +p.y.toFixed(3), +p.z.toFixed(3)] };
  if (paint.shape){ st.sh = paint.shape; st.fb = paint.brush; st.y = +(cam.yaw - paint.spinA).toFixed(3); }
  else st.b = paint.brush;
  if (paint.brush === 'ribbon' && !paint.shape) st.f = [+f.x.toFixed(3), 0, +f.z.toFixed(3)];
  if (paint.brush === 'rainbow') st.h = +((paint.strokes.length * 0.17) % 1).toFixed(3);
  paint.cur = st; showTip(h); refreshCur(); wake();
}
function paintMove(cx, cy){
  const h = planeHit(cx, cy); if (!h) return;
  showTip(h);
  const c = paint.cur; if (!c) return;
  const p = toCanvas(h), n = c.p.length, lx = c.p[n - 3], ly = c.p[n - 2], lz = c.p[n - 1];
  const minStep = c.sh ? c.s * 0.25 : 0.012;
  if (Math.hypot(p.x - lx, p.y - ly, p.z - lz) < minStep || n >= 1800) return;
  c.p.push(+p.x.toFixed(3), +p.y.toFixed(3), +p.z.toFixed(3));
  if ((c.p.length / 3) % 2 === 0 || c.sh) refreshCur();
  wake();
}
function paintUp(){
  const c = paint.cur; if (!c) return;
  paint.cur = null;
  if (paint.curObj){ paint.group.remove(paint.curObj); disposeObj(paint.curObj); paint.curObj = null; }
  const o = strokeObject(c); if (!o) return;
  o.userData.verts = objVerts(o);
  paint.group.add(o); paint.meshes.push(o); paint.strokes.push(c);
  let total = 0; for (const m of paint.meshes) total += m.userData.verts || 0;
  while (paint.meshes.length > 1 && (paint.strokes.length > 250 || total > PAINT_VERTS)){ const old = paint.meshes.shift(); paint.strokes.shift(); total -= old.userData.verts || 0; paint.group.remove(old); disposeObj(old); }
  savePaint(); updatePaintButtons(); award('artist'); wake();
}
function refreshCur(){
  if (paint.curObj){ paint.group.remove(paint.curObj); disposeObj(paint.curObj); paint.curObj = null; }
  const o = previewObject(paint.cur); if (o){ paint.curObj = o; paint.group.add(o); }
}
function showTip(h){
  if (!paint.tip) return;
  paint.tip.visible = paint.on && !paint.look; paint.tip.position.copy(h);
  paint.tip.scale.setScalar(paint.shape ? paintSize() * 0.5 : paintSize() * 1.15);
  paint.tip.material.color.set(paint.color === '#24262b' ? '#ffffff' : paint.color);
}
function undoPaint(){ const o = paint.meshes.pop(); if (!o) return; paint.strokes.pop(); paint.group.remove(o); disposeObj(o); savePaint(); updatePaintButtons(); wake(); }
function clearPaint(){ while (paint.meshes.length){ const o = paint.meshes.pop(); paint.group.remove(o); disposeObj(o); } paint.strokes = []; paint.spinA = 0; if (paint.root) paint.root.rotation.y = 0; savePaint(); updatePaintButtons(); wake(); }

/* ---------- Little icons for the tool chips ---------- */
function paintIcon(id){
  const S = 48, c = mk(S, S), ctx = c.getContext('2d');
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  const wave = (w, col) => { ctx.strokeStyle = col; ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(7, 32); ctx.bezierCurveTo(16, 6, 26, 44, 41, 15); ctx.stroke(); };
  const bone = '#efe7d5';
  if (id === 'neon'){ ctx.shadowColor = '#ff5a8a'; ctx.shadowBlur = 8; wave(6, '#ff8fb1'); ctx.shadowBlur = 0; wave(2.5, '#ffffff'); }
  else if (id === 'paint') wave(8, '#ff8f3d');
  else if (id === 'ribbon'){ ctx.fillStyle = '#5ee6c8'; ctx.beginPath(); ctx.moveTo(6, 30); ctx.bezierCurveTo(16, 2, 26, 40, 42, 10); ctx.lineTo(42, 20); ctx.bezierCurveTo(28, 48, 18, 14, 6, 38); ctx.closePath(); ctx.fill(); ctx.fillStyle = 'rgba(0,0,0,0.22)'; ctx.fillRect(21, 18, 5, 14); }
  else if (id === 'chrome'){ const g = ctx.createLinearGradient(0, 8, 0, 40); g.addColorStop(0, '#ffffff'); g.addColorStop(0.45, '#8d969e'); g.addColorStop(0.55, '#3a4248'); g.addColorStop(1, '#d9dee2'); wave(8, g); }
  else if (id === 'rainbow'){ for (let i = 0; i < 6; i++){ ctx.strokeStyle = 'hsl(' + i * 58 + ',90%,60%)'; ctx.lineWidth = 7; ctx.beginPath(); const t0 = i / 6, t1 = (i + 1) / 6; for (let k = 0; k <= 8; k++){ const t = t0 + (t1 - t0) * k / 8, x = 7 + t * 34, y = 24 + Math.sin(t * Math.PI * 2.2) * 11; if (k) ctx.lineTo(x, y); else ctx.moveTo(x, y); } ctx.stroke(); } }
  else if (id === 'beads'){ for (let i = 0; i < 4; i++){ const x = 10 + i * 9.5, y = 26 + Math.sin(i * 1.4) * 9, g = ctx.createRadialGradient(x - 2, y - 2, 1, x, y, 6); g.addColorStop(0, '#ffffff'); g.addColorStop(0.35, '#c38bff'); g.addColorStop(1, '#5a3a8a'); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, 5.5, 0, Math.PI * 2); ctx.fill(); } }
  else if (id === 'sparkle'){ ctx.fillStyle = '#ffd166'; ctx.shadowColor = '#ffd166'; ctx.shadowBlur = 6; for (const [x, y, r] of [[14, 30, 8], [32, 16, 7], [36, 36, 5]]){ ctx.beginPath(); for (let i = 0; i < 10; i++){ const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * 0.42 : r; ctx.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); } ctx.closePath(); ctx.fill(); } }
  else {
    ctx.strokeStyle = bone; ctx.fillStyle = 'rgba(239,231,213,0.18)'; ctx.lineWidth = 2.4;
    const P = (pts, fill) => { ctx.beginPath(); pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath(); if (fill) ctx.fill(); ctx.stroke(); };
    if (id === 'cube'){ P([[24, 8], [39, 16], [24, 24], [9, 16]], true); P([[9, 16], [24, 24], [24, 41], [9, 33]]); P([[24, 24], [39, 16], [39, 33], [24, 41]]); }
    else if (id === 'sphere'){ const g = ctx.createRadialGradient(19, 18, 2, 24, 24, 16); g.addColorStop(0, '#ffffff'); g.addColorStop(1, 'rgba(239,231,213,0.25)'); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(24, 24, 15, 0, Math.PI * 2); ctx.fill(); ctx.stroke(); }
    else if (id === 'cone'){ P([[24, 7], [38, 36], [10, 36]], true); ctx.beginPath(); ctx.ellipse(24, 36, 14, 4.5, 0, 0, Math.PI * 2); ctx.stroke(); }
    else if (id === 'cylinder'){ ctx.beginPath(); ctx.ellipse(24, 12, 12, 4.5, 0, 0, Math.PI * 2); ctx.fill(); ctx.stroke(); ctx.beginPath(); ctx.moveTo(12, 12); ctx.lineTo(12, 36); ctx.ellipse(24, 36, 12, 4.5, 0, Math.PI, 0, true); ctx.lineTo(36, 12); ctx.stroke(); }
    else if (id === 'torus'){ ctx.lineWidth = 7; ctx.beginPath(); ctx.ellipse(24, 24, 13, 13, 0, 0, Math.PI * 2); ctx.stroke(); ctx.lineWidth = 2; ctx.strokeStyle = 'rgba(0,0,0,0.35)'; ctx.beginPath(); ctx.ellipse(24, 24, 13, 13, 0, 0, Math.PI * 2); ctx.stroke(); }
    else if (id === 'star'){ const pts = []; for (let i = 0; i < 10; i++){ const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? 7 : 16; pts.push([24 + Math.cos(a) * rr, 25 + Math.sin(a) * rr]); } P(pts, true); }
    else if (id === 'heart'){ ctx.beginPath(); ctx.moveTo(24, 40); ctx.bezierCurveTo(20, 36, 7, 28, 7, 18); ctx.bezierCurveTo(7, 9, 19, 7, 24, 15); ctx.bezierCurveTo(29, 7, 41, 9, 41, 18); ctx.bezierCurveTo(41, 28, 28, 36, 24, 40); ctx.closePath(); ctx.fill(); ctx.stroke(); }
    else if (id === 'pyramid'){ P([[24, 7], [40, 36], [24, 41], [8, 36]], true); ctx.beginPath(); ctx.moveTo(24, 7); ctx.lineTo(24, 41); ctx.stroke(); }
  }
  return c;
}
