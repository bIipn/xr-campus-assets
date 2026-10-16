/* ================================================================
   Ocean Dive: a made-up reef with fish schools and sea creatures
   ================================================================ */
const DV = { x:420, z:0 };
const DIVE = { root:null, uTime:{ value:0 }, path:null, len:0, schools:[], clowns:null, clownData:[], manta:null, turtle:null, shark:null, sharkTail:null, jellies:[], tentacles:null, bubbles:null, bub:[], snow:null, caustic:null, surface:null, fans:[], rays:[], t:0, tokenAt:null, facts:[], camLocal:new THREE.Vector3(), breath:0 };
const DIVE_PTS = [[-36, -4.5, 6], [-28, -8, 2.5], [-20, -10.8, -0.5], [-12, -11.8, 1.5], [-5, -12.2, 2], [3, -11, 0], [10, -10.6, -2.8], [17.5, -10.5, 0.8], [23.5, -9.6, 6.5], [27, -8.2, 12.5], [28, -7, 18.5], [23.5, -5.6, 24.5], [15.5, -3.9, 27.5], [8, -2.6, 28]];
const DIVE_FACTS = [
  { at:null, u:0, text:'Welcome to the reef. Coral reefs cover less than 1% of the ocean floor, but about a quarter of all ocean species live on them.' },
  { at:[-14, -12, 1], look:'anemone', text:'Clownfish live among sea anemones. A slimy coating keeps the anemone’s sting from hurting them.' },
  { at:[-5, -10, 8.5], look:'turtle', text:'A sea turtle! Sea turtles have swum in the oceans for more than 100 million years.' },
  { at:[6, -10.5, -1.5], text:'You’re in a kelp forest. Giant kelp can grow about 60 cm (2 feet) in a single day.' },
  { at:[21, -10, 2.4], look:'school', text:'Fish swim in schools to stay safe. In a big group, it’s hard for a hunter to catch any one fish.' },
  { at:[25.8, -9, 9.6], look:'shark', text:'Look down! Whale sharks are the biggest fish in the sea, and they eat tiny plankton.' },
  { at:[28, -7, 17.5], look:'manta', text:'Manta rays glide by flapping their wide fins like wings.' },
  { at:[21, -5, 25.6], look:'jelly', text:'Jellyfish have no brain, no heart and no bones.' },
  { at:null, u:0.93, text:'This reef is made up for the campus, inspired by ocean VR like Hydrous, a partner listed by XRLibraries. Read “Oceans in VR” in the library.' }
];
function floorY(x, z){
  let y = -18 + 0.8 * Math.sin(x * 0.08) * Math.cos(z * 0.07) + 0.45 * Math.sin(x * 0.21 + z * 0.13);
  const d = Math.hypot(x + 19, z - 1); y += 3.6 * Math.exp(-(d * d) / 162);
  const d2 = Math.hypot(x - 32, z - 21.5); y += 2.2 * Math.exp(-(d2 * d2) / 24.5);
  return y;
}
function shaderTweak(mat, key, vertexHead, beginVertex){
  mat.onBeforeCompile = (sh) => { sh.uniforms.uTime = DIVE.uTime; sh.vertexShader = 'uniform float uTime;\n' + vertexHead + '\n' + sh.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\n' + beginVertex); };
  mat.customProgramCacheKey = () => key;
  return mat;
}

/* ---------------- Underwater textures ---------------- */
function canvasSand(){
  const S = 256, c = mk(S, S), ctx = c.getContext('2d'), r = rnd(61);
  ctx.fillStyle = '#d2bf93'; ctx.fillRect(0, 0, S, S);
  for (let i = 0; i < 26; i++){ const y = r() * S; ctx.strokeStyle = 'rgba(150,130,90,0.16)'; ctx.lineWidth = 3; ctx.beginPath(); for (let x = -10; x <= S + 10; x += 8){ const yy = y + Math.sin(x / S * Math.PI * 4 + i) * 6; x < 0 ? ctx.moveTo(x, yy) : ctx.lineTo(x, yy); } ctx.stroke(); }
  for (let i = 0; i < 4200; i++){ ctx.fillStyle = r() < 0.5 ? 'rgba(90,70,40,0.14)' : 'rgba(255,250,235,0.18)'; ctx.fillRect(r() * S, r() * S, 1 + r() * 1.5, 1 + r() * 1.5); }
  return c;
}
function canvasCaustics(){
  const S = 128, c = mk(S, S), ctx = c.getContext('2d'), r = rnd(17), pts = [];
  for (let i = 0; i < 22; i++) pts.push([r() * S, r() * S]);
  const img = ctx.createImageData(S, S);
  for (let y = 0; y < S; y++) for (let x = 0; x < S; x++){
    let f1 = 1e9, f2 = 1e9;
    for (const [px, py] of pts) for (const ox of [-S, 0, S]) for (const oy of [-S, 0, S]){ const dx = x - px - ox, dy = y - py - oy, d = dx * dx + dy * dy; if (d < f1){ f2 = f1; f1 = d; } else if (d < f2) f2 = d; }
    const e = Math.sqrt(f2) - Math.sqrt(f1), v = Math.max(0, 1 - e / 5), k = (y * S + x) * 4, b = Math.pow(v, 3.0) * 255;
    img.data[k] = b; img.data[k + 1] = b; img.data[k + 2] = b; img.data[k + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
  return c;
}
function canvasFish(sp){
  const W = 128, H = 128, c = mk(W, H), ctx = c.getContext('2d');
  const C = { tang:['#173a9e', '#2a63d8', '#78a6f2', '#f6d23a'], yellow:['#d9a91c', '#f6d33b', '#fbe88c', '#f6d33b'], sardine:['#2b4a62', '#a8bccb', '#f1f5f7', '#8ea3b3'], clown:['#e2600f', '#ff7b1c', '#ffa25c', '#ff7b1c'] }[sp];
  const g = ctx.createLinearGradient(0, 0, W, 0);
  g.addColorStop(0, C[1]); g.addColorStop(0.25, C[2]); g.addColorStop(0.5, C[1]); g.addColorStop(0.75, C[0]); g.addColorStop(1, C[1]);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H * 0.88);
  ctx.fillStyle = C[3]; ctx.fillRect(0, H * 0.88, W, H * 0.12);
  if (sp === 'tang'){ ctx.fillStyle = '#0b1530'; for (const cx of [0, W / 2, W]){ ctx.beginPath(); ctx.ellipse(cx, H * 0.5, W * 0.11, H * 0.22, 0, 0, Math.PI * 2); ctx.fill(); } }
  if (sp === 'sardine'){ ctx.fillStyle = 'rgba(20,40,60,0.55)'; for (const cx of [W * 0.06, W * 0.56]) ctx.fillRect(cx - 2, H * 0.1, 4, H * 0.7); }
  if (sp === 'clown'){ for (const by of [0.22, 0.5, 0.78]){ ctx.fillStyle = '#111'; ctx.fillRect(0, H * by - 9, W, 18); ctx.fillStyle = '#fff'; ctx.fillRect(0, H * by - 6, W, 12); } }
  ctx.fillStyle = '#0a0d12'; for (const cx of [2, W / 2, W - 2]){ ctx.beginPath(); ctx.arc(cx, H * 0.1, 4, 0, Math.PI * 2); ctx.fill(); }
  return c;
}
function canvasBrain(){
  const S = 256, c = mk(S, S), ctx = c.getContext('2d'), r = rnd(5);
  ctx.fillStyle = '#b9a771'; ctx.fillRect(0, 0, S, S);
  ctx.strokeStyle = 'rgba(70,60,30,0.55)'; ctx.lineWidth = 4; ctx.lineCap = 'round';
  for (let i = 0; i < 70; i++){ let x = r() * S, y = r() * S, a = r() * 6.28; ctx.beginPath(); ctx.moveTo(x, y); for (let k = 0; k < 14; k++){ a += (r() - 0.5) * 1.4; x += Math.cos(a) * 8; y += Math.sin(a) * 8; ctx.lineTo(x, y); } ctx.stroke(); }
  return c;
}
function canvasFan(){
  const W = 256, H = 256, c = mk(W, H), ctx = c.getContext('2d'), r = rnd(8);
  ctx.strokeStyle = '#fff'; ctx.lineCap = 'round';
  const br = (x, y, a, len, w, d) => { if (d > 6 || len < 6) return; const x2 = x + Math.cos(a) * len, y2 = y + Math.sin(a) * len; ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x2, y2); ctx.stroke(); br(x2, y2, a - 0.32 - r() * 0.2, len * 0.78, w * 0.75, d + 1); br(x2, y2, a + 0.32 + r() * 0.2, len * 0.78, w * 0.75, d + 1); };
  br(W / 2, H, -Math.PI / 2, 60, 9, 0);
  ctx.globalAlpha = 0.5; ctx.lineWidth = 1.2; for (let i = 0; i < 40; i++){ ctx.beginPath(); ctx.arc(W / 2, H, 30 + i * 5, Math.PI, 2 * Math.PI); ctx.stroke(); }
  return c;
}
function canvasKelp(){
  const W = 64, H = 512, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#5b5a1d'; ctx.fillRect(W / 2 - 2, 0, 4, H);
  for (let y = 18; y < H - 10; y += 22){
    for (const s of [-1, 1]){ const g = ctx.createLinearGradient(W / 2, y, W / 2 + s * 30, y - 20); g.addColorStop(0, '#7a6a1c'); g.addColorStop(1, '#a8902c'); ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(W / 2, y + 4); ctx.quadraticCurveTo(W / 2 + s * 30, y - 2, W / 2 + s * 28, y - 22); ctx.quadraticCurveTo(W / 2 + s * 10, y - 10, W / 2, y - 2); ctx.closePath(); ctx.fill(); }
  }
  return c;
}
function canvasShark(){
  const W = 512, H = 256, c = mk(W, H), ctx = c.getContext('2d'), r = rnd(4);
  const g = ctx.createLinearGradient(0, 0, W, 0);
  g.addColorStop(0, '#3a4f66'); g.addColorStop(0.25, '#e6ecef'); g.addColorStop(0.5, '#3a4f66'); g.addColorStop(0.75, '#26384b'); g.addColorStop(1, '#3a4f66');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = 'rgba(235,242,246,0.9)';
  for (let i = 0; i < 520; i++){ const x = r() * W, y = r() * H, u = x / W; if (u > 0.15 && u < 0.35) continue; ctx.beginPath(); ctx.arc(x, y, 1.6 + r() * 2.4, 0, Math.PI * 2); ctx.fill(); }
  ctx.strokeStyle = 'rgba(235,242,246,0.55)'; ctx.lineWidth = 2;
  for (let y = 40; y < H; y += 28){ ctx.beginPath(); ctx.moveTo(W * 0.38, y); ctx.lineTo(W * 0.62, y); ctx.stroke(); ctx.beginPath(); ctx.moveTo(W * 0.88, y); ctx.lineTo(W, y); ctx.moveTo(0, y); ctx.lineTo(W * 0.12, y); ctx.stroke(); }
  return c;
}
function canvasShell(){
  const S = 256, c = mk(S, S), ctx = c.getContext('2d');
  ctx.fillStyle = '#5d4a24'; ctx.fillRect(0, 0, S, S);
  ctx.strokeStyle = '#d8b56a'; ctx.lineWidth = 5;
  for (let y = -32; y < S + 32; y += 52) for (let x = -32; x < S + 32; x += 56){ const ox = (Math.round(y / 52) % 2) * 28; ctx.fillStyle = 'rgba(140,100,40,0.55)'; ctx.beginPath(); for (let k = 0; k < 6; k++){ const a = k / 6 * Math.PI * 2; ctx.lineTo(x + ox + Math.cos(a) * 26, y + Math.sin(a) * 24); } ctx.closePath(); ctx.fill(); ctx.stroke(); }
  return c;
}
function canvasRay(){
  const W = 64, H = 256, c = mk(W, H), ctx = c.getContext('2d');
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, 'rgba(255,255,255,0.95)'); g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  const h = ctx.createLinearGradient(0, 0, W, 0); h.addColorStop(0, 'rgba(0,0,0,1)'); h.addColorStop(0.5, 'rgba(0,0,0,0)'); h.addColorStop(1, 'rgba(0,0,0,1)');
  ctx.globalCompositeOperation = 'destination-out'; ctx.fillStyle = h; ctx.fillRect(0, 0, W, H);
  return c;
}
function canvasSurface(){
  const S = 128, src = canvasCaustics(), c = mk(S, S), ctx = c.getContext('2d');
  ctx.fillStyle = '#6dbdd3'; ctx.fillRect(0, 0, S, S);
  ctx.filter = 'blur(1.5px)'; ctx.globalAlpha = 0.3; ctx.drawImage(src, 0, 0); ctx.globalAlpha = 1; ctx.filter = 'none';
  return c;
}

/* ---------------- Geometry helpers ---------------- */
function mergeFlat(geos0){
  const geos = geos0.map((g) => g.index ? g.toNonIndexed() : g);
  let n = 0; for (const g of geos) n += g.attributes.position.count;
  const pos = new Float32Array(n * 3), nor = new Float32Array(n * 3), uv = new Float32Array(n * 2); let o = 0;
  for (const g of geos){ if (!g.attributes.normal) g.computeVertexNormals(); pos.set(g.attributes.position.array, o * 3); nor.set(g.attributes.normal.array, o * 3); if (g.attributes.uv) uv.set(g.attributes.uv.array, o * 2); o += g.attributes.position.count; }
  const out = new THREE.BufferGeometry(); out.setAttribute('position', new THREE.BufferAttribute(pos, 3)); out.setAttribute('normal', new THREE.BufferAttribute(nor, 3)); out.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  return out;
}
function fishGeo(len, h, w){
  const body = new THREE.SphereGeometry(1, 14, 9); body.rotateX(Math.PI / 2); body.scale(w, h, len * 0.5);
  const tz = -len * 0.4, te = -len * 0.78, th = h * 0.95;
  const tail = new THREE.BufferGeometry();
  tail.setAttribute('position', new THREE.BufferAttribute(new Float32Array([0, 0, tz, 0, th, te, 0, -th, te, 0, 0, tz, 0, -th, te, 0, th, te]), 3));
  tail.setAttribute('uv', new THREE.BufferAttribute(new Float32Array([0.5, 0.08, 0.5, 0.02, 0.5, 0.02, 0.5, 0.08, 0.5, 0.02, 0.5, 0.02]), 2));
  tail.computeVertexNormals();
  const top = new THREE.BufferGeometry();
  top.setAttribute('position', new THREE.BufferAttribute(new Float32Array([0, h * 0.9, len * 0.18, 0, h * 1.35, -len * 0.05, 0, h * 0.8, -len * 0.3, 0, h * 0.9, len * 0.18, 0, h * 0.8, -len * 0.3, 0, h * 1.35, -len * 0.05]), 3));
  top.setAttribute('uv', new THREE.BufferAttribute(new Float32Array([0.75, 0.3, 0.75, 0.5, 0.75, 0.6, 0.75, 0.3, 0.75, 0.6, 0.75, 0.5]), 2));
  top.computeVertexNormals();
  return mergeFlat([body, tail, top]);
}
function fishMat(sp, len){
  const t = tex(canvasFish(sp));
  const m = new THREE.MeshLambertMaterial({ map:t, emissive:0x2a2a2a, emissiveMap:t, side:THREE.DoubleSide });
  return shaderTweak(m, 'dive-fish-' + len.toFixed(3), 'attribute float aPhase;', 'float sw = 1.0 - smoothstep(-0.8, 0.15, position.z / ' + len.toFixed(3) + ');\ntransformed.x += sin(uTime * 10.0 + aPhase + position.z * 14.0) * ' + (0.11 * len).toFixed(4) + ' * sw;');
}

/* ---------------- Build ---------------- */
function buildDive(M){
  const root = new THREE.Group(); root.position.set(DV.x, 0, DV.z); scene.add(root); DIVE.root = root;
  const add = (o) => { root.add(o); return o; };
  const r = rnd(808);
  const path = new THREE.CatmullRomCurve3(DIVE_PTS.map((p) => new THREE.Vector3(p[0], p[1], p[2])), false, 'centripetal');
  path.arcLengthDivisions = 2000; DIVE.path = path; DIVE.len = path.getLength();
  const samples = path.getSpacedPoints(400);
  const nearU = (x, y, z) => { let bi = 0, bd = Infinity; samples.forEach((p, i) => { const d = (p.x - x) ** 2 + (p.y - y) ** 2 + (p.z - z) ** 2; if (d < bd){ bd = d; bi = i; } }); return bi / 400; };
  const pathDist = (x, z) => { let bd = Infinity; for (const p of samples){ const d = (p.x - x) ** 2 + (p.z - z) ** 2; if (d < bd) bd = d; } return Math.sqrt(bd); };
  DIVE.facts = DIVE_FACTS.map((f) => ({ text:f.text, look:f.look || null, u:f.at ? Math.max(0, nearU(f.at[0], f.at[1], f.at[2]) - 0.035) : f.u })).sort((a, b) => a.u - b.u);
  DIVE.tokenAt = path.getPointAt(0.2).clone().add(new THREE.Vector3(DV.x, 0, DV.z));

  /* Sea floor with moving light */
  const fg = new THREE.PlaneGeometry(170, 170, 85, 85); fg.rotateX(-Math.PI / 2);
  const fp = fg.attributes.position; for (let i = 0; i < fp.count; i++) fp.setY(i, floorY(fp.getX(i), fp.getZ(i)));
  fg.computeVertexNormals();
  const caus = repTex(canvasCaustics(), 64, 64); DIVE.caustic = caus;
  add(new THREE.Mesh(fg, new THREE.MeshLambertMaterial({ map:repTex(canvasSand(), 26, 26), emissive:srgb(0x3c6f80), emissiveMap:caus })));
  /* Water surface seen from below */
  const sTex = repTex(canvasSurface(), 96, 96); DIVE.surface = sTex;
  const surf = new THREE.Mesh(new THREE.PlaneGeometry(260, 260), new THREE.MeshBasicMaterial({ map:sTex, color:0xc4ecf8, toneMapped:false })); surf.rotation.x = Math.PI / 2; surf.position.y = -0.05; add(surf);
  /* Rocks */
  const rocks = new MatBatch(), rockGeo = new THREE.DodecahedronGeometry(1, 0), m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), v = new THREE.Vector3(), sc = new THREE.Vector3();
  const rockAt = (x, z, s) => { e.set(r() * 3, r() * 3, r() * 3); q.setFromEuler(e); v.set(x, floorY(x, z) + s * 0.3, z); sc.set(s * (1 + r() * 0.6), s * (0.6 + r() * 0.4), s * (1 + r() * 0.5)); rocks.add(m4.compose(v, q, sc), shade('#6d756c', (r() - 0.5) * 0.3)); };
  for (let i = 0; i < 40; i++){ const x = -40 + r() * 80, z = -18 + r() * 52; if (pathDist(x, z) < 3) continue; rockAt(x, z, 0.5 + r() * 1.4); }
  for (let i = 0; i < 9; i++) rockAt(32 + (r() - 0.5) * 5, 21.5 + (r() - 0.5) * 5, 0.9 + r() * 1.2);
  const rockMesh = rocks.build(rockGeo, new THREE.MeshStandardMaterial({ flatShading:true, roughness:0.95 })); root.add(rockMesh);

  /* Coral reef */
  const reef = (n, fn) => { for (let i = 0; i < n; i++){ const a = r() * Math.PI * 2, d = Math.sqrt(r()) * 13, x = -19 + Math.cos(a) * d * 1.3, z = 1 + Math.sin(a) * d; if (pathDist(x, z) < 1.4) continue; fn(x, z); } };
  const branches = new MatBatch(), yAx = new THREE.Vector3(0, 1, 0), corals = ['#ff7aa8', '#ff8a3d', '#a77bff', '#ff6f61', '#ffd35c', '#5ee6c8'];
  reef(70, (x, z) => {
    const col = corals[(r() * corals.length) | 0], base = floorY(x, z), nb = 6 + (r() * 6 | 0);
    for (let k = 0; k < nb; k++){ const dir = new THREE.Vector3((r() - 0.5) * 1.1, 1, (r() - 0.5) * 1.1).normalize(), len = 0.4 + r() * 0.8, p0 = new THREE.Vector3(x + (r() - 0.5) * 0.3, base, z + (r() - 0.5) * 0.3); q.setFromUnitVectors(yAx, dir); branches.add(m4.compose(p0.clone().addScaledVector(dir, len / 2), q, sc.set(1, len, 1)), shade(col, (r() - 0.5) * 0.3)); }
  });
  root.add(branches.build(new THREE.CylinderGeometry(0.035, 0.07, 1, 6), new THREE.MeshLambertMaterial({ emissive:0x1a1a1a })));
  const brains = new MatBatch();
  reef(26, (x, z) => { const s = 0.4 + r() * 0.6; e.set(0, r() * 6, 0); q.setFromEuler(e); brains.add(m4.compose(v.set(x, floorY(x, z) - 0.05, z), q, sc.set(s, s * 0.8, s)), shade(['#c7b27a', '#9ab07a', '#d98f6a'][(r() * 3) | 0], (r() - 0.5) * 0.2)); });
  root.add(brains.build(new THREE.SphereGeometry(1, 18, 10, 0, Math.PI * 2, 0, Math.PI / 2), new THREE.MeshLambertMaterial({ map:tex(canvasBrain()) })));
  const tables = new MatBatch(), stems = new MatBatch();
  reef(12, (x, z) => { const s = 0.7 + r() * 0.7, by = floorY(x, z), h = 0.4 + r() * 0.6; q.identity(); tables.add(m4.compose(v.set(x, by + h, z), q, sc.set(s, 1, s)), shade(['#d9a07a', '#b8c27a', '#e0b3d9'][(r() * 3) | 0], 0)); stems.add(m4.compose(v.set(x, by + h / 2, z), q, sc.set(1, h, 1))); });
  root.add(tables.build(new THREE.CylinderGeometry(1, 0.8, 0.12, 16), new THREE.MeshLambertMaterial()));
  root.add(stems.build(new THREE.CylinderGeometry(0.1, 0.16, 1, 8), new THREE.MeshLambertMaterial({ color:srgb(0x8a7a5a) })));
  const tubes = new MatBatch();
  reef(20, (x, z) => { const col = ['#ff9f43', '#c38bff', '#ffd35c'][(r() * 3) | 0], by = floorY(x, z); for (let k = 0; k < 4; k++){ const h = 0.5 + r() * 0.9, ox = (r() - 0.5) * 0.5, oz = (r() - 0.5) * 0.5; q.identity(); tubes.add(m4.compose(v.set(x + ox, by + h / 2, z + oz), q, sc.set(1, h, 1)), col); } });
  root.add(tubes.build(new THREE.CylinderGeometry(0.13, 0.1, 1, 10, 1, true), new THREE.MeshLambertMaterial({ side:THREE.DoubleSide })));
  const fanTex = tex(canvasFan());
  DIVE.fans = [];
  reef(14, (x, z) => { const fan = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 1.5), new THREE.MeshLambertMaterial({ map:fanTex, color:srgb(['#b04aa8', '#d2462f', '#ff8fb1'][(r() * 3) | 0]), alphaTest:0.4, side:THREE.DoubleSide })); fan.position.set(x, floorY(x, z) + 0.7, z); fan.rotation.y = r() * 3; fan.userData.ph = r() * 6; add(fan); DIVE.fans.push(fan); });
  /* Anemones with swaying arms */
  const arms = new MatBatch(), anem = [[-14, -3], [-16.5, 5], [-10, -3.6], [-21.5, 5.6], [-12, 5.6], [-24, -3]];
  DIVE.anem = anem.map(([ax, az]) => new THREE.Vector3(ax, floorY(ax, az) + 0.5, az));
  for (const [ax, az] of anem){ const by = floorY(ax, az); for (let k = 0; k < 44; k++){ const a = r() * Math.PI * 2, rr2 = Math.sqrt(r()) * 0.45, dir = new THREE.Vector3(Math.cos(a) * 0.5, 1, Math.sin(a) * 0.5).normalize(), len = 0.35 + r() * 0.3; q.setFromUnitVectors(yAx, dir); arms.add(m4.compose(v.set(ax + Math.cos(a) * rr2, by + 0.1, az + Math.sin(a) * rr2).addScaledVector(dir, len / 2), q, sc.set(1, len, 1)), shade('#ff9ec4', (r() - 0.5) * 0.25)); } }
  const armMat = shaderTweak(new THREE.MeshLambertMaterial({ emissive:0x3a1f2a }), 'dive-arm', '', 'vec4 ip = instanceMatrix[3];\ntransformed.x += sin(uTime * 1.7 + ip.x * 3.1 + ip.z * 2.3) * 0.09 * (position.y + 0.5);\ntransformed.z += cos(uTime * 1.3 + ip.x * 2.2) * 0.06 * (position.y + 0.5);');
  root.add(arms.build(new THREE.CylinderGeometry(0.008, 0.03, 1, 5), armMat));
  /* Clownfish around the anemones */
  const clownLen = 0.2, cg = fishGeo(clownLen, 0.05, 0.03), nC = anem.length * 2, cph = new Float32Array(nC);
  for (let i = 0; i < nC; i++) cph[i] = r() * 6;
  cg.setAttribute('aPhase', new THREE.InstancedBufferAttribute(cph, 1));
  DIVE.clowns = new THREE.InstancedMesh(cg, fishMat('clown', clownLen), nC); DIVE.clowns.frustumCulled = false; add(DIVE.clowns);
  DIVE.clownData = []; for (let i = 0; i < nC; i++){ const [ax, az] = anem[i >> 1]; DIVE.clownData.push({ x:ax, z:az, y:floorY(ax, az) + 0.55 + r() * 0.3, rad:0.45 + r() * 0.35, sp:(0.7 + r() * 0.6) * (i % 2 ? 1 : -1), ph:r() * 6 }); }

  /* Kelp forest */
  const kelps = new MatBatch();
  let placed = 0;
  for (let i = 0; i < 400 && placed < 90; i++){
    const x = r() * 18, z = -13 + r() * 23; if (pathDist(x, z) < 2.6) continue;
    const by = floorY(x, z), H = 9 + r() * 7;
    for (const rot of [0, Math.PI / 2]){ e.set(0, rot + r() * 0.5, 0); q.setFromEuler(e); kelps.add(m4.compose(v.set(x, by, z), q, sc.set(1, H, 1))); }
    placed++;
  }
  const kg = new THREE.PlaneGeometry(0.62, 1, 1, 14); kg.translate(0, 0.5, 0);
  const kelpMat = shaderTweak(new THREE.MeshLambertMaterial({ map:tex(canvasKelp()), alphaTest:0.45, side:THREE.DoubleSide, emissive:0x1a1a08 }), 'dive-kelp', '', 'vec4 kp = instanceMatrix[3];\nfloat kh = position.y;\ntransformed.x += sin(uTime * 0.8 + kp.x * 0.37 + kp.z * 0.61 + kh * 2.0) * 0.06 * kh * kh * 8.0;\ntransformed.z += cos(uTime * 0.6 + kp.z * 0.5) * 0.04 * kh * kh * 8.0;');
  root.add(kelps.build(kg, kelpMat));

  /* Fish schools */
  DIVE.schools = [
    makeSchool('tang', 46, 0.42, 0.13, 0.045, [-19, -11.2, 2], [6, 1.2, 5], { sep:0.5, nb:1.8, minV:0.7, maxV:2.0 }, r),
    makeSchool('yellow', 38, 0.36, 0.12, 0.04, [-9, -11.6, 5], [5, 1, 4], { sep:0.45, nb:1.6, minV:0.6, maxV:1.8 }, r),
    makeSchool('sardine', 150, 0.3, 0.05, 0.035, [23, -10.2, -1.6], [1.5, 0.8, 1.5], { sep:0.32, nb:1.3, minV:1.4, maxV:3.0, orbit:0.9, home:0.9 }, r),
    makeSchool('tang', 30, 0.42, 0.13, 0.045, [24, -8, 22], [5, 1.2, 4], { sep:0.5, nb:1.8, minV:0.7, maxV:2.0 }, r)
  ];
  for (const S of DIVE.schools) add(S.mesh);

  /* Sea turtle */
  const turtle = new THREE.Group();
  const shell = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 14), new THREE.MeshLambertMaterial({ map:tex(canvasShell()) })); shell.scale.set(0.55, 0.22, 0.72); turtle.add(shell);
  const skin = new THREE.MeshLambertMaterial({ color:srgb(0x8a8a5a) }), belly = new THREE.MeshLambertMaterial({ color:srgb(0xe2d29a) });
  const plast = new THREE.Mesh(new THREE.SphereGeometry(1, 18, 10), belly); plast.scale.set(0.5, 0.12, 0.64); plast.position.y = -0.06; turtle.add(plast);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.15, 16, 12), skin); head.scale.set(1, 0.85, 1.3); head.position.set(0, 0.02, 0.82); turtle.add(head);
  const fl = [];
  for (const [sx, sz, len, w] of [[-1, 0.38, 0.75, 0.2], [1, 0.38, 0.75, 0.2], [-1, -0.5, 0.32, 0.14], [1, -0.5, 0.32, 0.14]]){
    const pv = new THREE.Group(); pv.position.set(sx * 0.42, -0.02, sz);
    const f = new THREE.Mesh(new THREE.SphereGeometry(1, 12, 8), skin); f.scale.set(len / 2, 0.035, w / 2); f.position.x = sx * len / 2; pv.add(f); turtle.add(pv); fl.push({ pv, sx, front:sz > 0 });
  }
  turtle.userData.creature = 2; [shell, plast, head].forEach((m) => { m.userData.creature = 2; pickItems.push(m); });
  add(turtle); DIVE.turtle = { g:turtle, fl, c:[-5, -9.6, 8.5], r:3.6, sp:0.22 };

  /* Whale shark */
  const shark = new THREE.Group();
  const bodyGeo = new THREE.SphereGeometry(1, 30, 18); bodyGeo.rotateX(Math.PI / 2); bodyGeo.scale(1.05, 0.85, 4.4);
  const bp = bodyGeo.attributes.position; for (let i = 0; i < bp.count; i++){ const z = bp.getZ(i); if (z > 2.3){ const k = (z - 2.3) / 2.1; bp.setY(i, bp.getY(i) * (1 - 0.3 * k)); bp.setX(i, bp.getX(i) * (1 + 0.12 * k)); } if (bp.getY(i) < 0) bp.setY(i, bp.getY(i) * 0.82); }
  bodyGeo.computeVertexNormals();
  const sharkMat = shaderTweak(new THREE.MeshLambertMaterial({ map:tex(canvasShark()) }), 'dive-shark', '', 'float sb = 1.0 - smoothstep(-4.4, 1.5, position.z);\ntransformed.x += sin(uTime * 1.1 - position.z * 0.45) * 0.3 * sb * sb;');
  const sbody = new THREE.Mesh(bodyGeo, sharkMat); shark.add(sbody);
  const finMat = new THREE.MeshLambertMaterial({ color:srgb(0x34485e), side:THREE.DoubleSide });
  const shape = (pts) => { const s = new THREE.Shape(); s.moveTo(pts[0][0], pts[0][1]); for (const p of pts.slice(1)) s.lineTo(p[0], p[1]); s.closePath(); return new THREE.ShapeGeometry(s); };
  const dorsal = new THREE.Mesh(shape([[0.6, 0], [-1.0, 0], [-0.6, 1.0]]), finMat); dorsal.geometry.rotateY(-Math.PI / 2); dorsal.position.set(0, 0.62, -0.9); shark.add(dorsal);
  for (const sx of [-1, 1]){ const pf = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.06, 0.62), finMat); pf.position.set(sx * 1.45, -0.42, 1.1); pf.rotation.set(0, sx * 0.55, sx * -0.32); shark.add(pf); }
  const tailPv = new THREE.Group(); tailPv.position.set(0, 0, -4.2);
  const tail = new THREE.Mesh(shape([[0.3, 0], [-1.0, 2.0], [-0.55, 0.2], [-0.85, -1.05]]), finMat); tail.geometry.rotateY(-Math.PI / 2); tailPv.add(tail); shark.add(tailPv);
  const mouth = new THREE.Mesh(new THREE.SphereGeometry(1, 16, 8), new THREE.MeshBasicMaterial({ color:0x0c1218 })); mouth.scale.set(0.7, 0.08, 0.2); mouth.position.set(0, -0.12, 4.32); shark.add(mouth);
  [sbody, dorsal].forEach((m) => { m.userData.creature = 5; pickItems.push(m); });
  add(shark); DIVE.shark = { g:shark, tail:tailPv, c:[28, -14.2, 7.5], r:9.5, sp:0.11 };

  /* Manta ray */
  const mg = new THREE.PlaneGeometry(4.2, 3.0, 30, 16); mg.rotateX(-Math.PI / 2);
  const mp = mg.attributes.position;
  for (let i = 0; i < mp.count; i++){
    const x = mp.getX(i), z = mp.getZ(i), t = clamp((z + 1.5) / 2.6, 0, 1), hw = Math.max(z > 0.55 ? 0.42 : 0, 2.1 * Math.pow(Math.sin(Math.PI * t), 1.35));
    const nx = x / 2.1 * hw, bulge = 0.16 * Math.max(0, 1 - Math.abs(nx) / 0.6) * (z > -1.1 && z < 1.3 ? 1 : 0);
    mp.setXYZ(i, nx, bulge, z - 0.55 * Math.pow(Math.abs(nx) / 2.1, 2));
  }
  mg.computeVertexNormals();
  const flap = 'float ax = abs(position.x);\ntransformed.y += sin(uTime * 1.5 - ax * 0.9) * 0.34 * ax * ax / 4.4;';
  const manta = new THREE.Group();
  const mTop = new THREE.Mesh(mg, shaderTweak(new THREE.MeshLambertMaterial({ color:srgb(0x26303b) }), 'dive-manta-top', '', flap));
  const mBot = new THREE.Mesh(mg, shaderTweak(new THREE.MeshLambertMaterial({ color:srgb(0xd9dee2), side:THREE.BackSide }), 'dive-manta-bot', '', flap));
  manta.add(mTop, mBot);
  for (const sx of [-1, 1]){ const cf = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.05, 0.42), new THREE.MeshLambertMaterial({ color:srgb(0x26303b) })); cf.position.set(sx * 0.33, -0.05, 1.62); cf.rotation.x = 0.4; manta.add(cf); }
  const mt = new THREE.Mesh(new THREE.CylinderGeometry(0.01, 0.04, 1.6, 6), new THREE.MeshLambertMaterial({ color:srgb(0x26303b) })); mt.rotation.x = Math.PI / 2; mt.position.set(0, 0, -2.2); manta.add(mt);
  [mTop, mBot].forEach((m) => { m.userData.creature = 6; pickItems.push(m); });
  add(manta); DIVE.manta = { g:manta, c:[31, -10.8, 21], r:6.2, sp:0.16 };

  /* Jellyfish */
  const jcols = [0xf2a7ff, 0xffc6a8, 0xa8d8ff, 0xd0b8ff];
  DIVE.jellies = [];
  for (let i = 0; i < 9; i++){
    let x = 0, z = 0, tries = 0; do { x = 14 + r() * 16; z = 19 + r() * 12; } while (pathDist(x, z) < 1.8 && tries++ < 20);
    const g = new THREE.Group(); g.position.set(x, -8 + r() * 6, z);
    const col = jcols[i % jcols.length];
    const bell = new THREE.Mesh(new THREE.SphereGeometry(0.34, 22, 10, 0, Math.PI * 2, 0, Math.PI / 2), new THREE.MeshBasicMaterial({ color:col, transparent:true, opacity:0.45, blending:THREE.AdditiveBlending, depthWrite:false, side:THREE.DoubleSide }));
    const core = new THREE.Mesh(new THREE.SphereGeometry(0.16, 14, 8, 0, Math.PI * 2, 0, Math.PI / 2), new THREE.MeshBasicMaterial({ color:col, transparent:true, opacity:0.6, blending:THREE.AdditiveBlending, depthWrite:false }));
    core.position.y = 0.02; g.add(bell, core); bell.userData.creature = 7; pickItems.push(bell);
    add(g); DIVE.jellies.push({ g, bell, ph:r() * 6, vy:0.1 + r() * 0.08, y0:g.position.y });
  }
  const nTen = DIVE.jellies.length * 6 * 12 * 2;
  const tg = new THREE.BufferGeometry(); tg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(nTen * 3), 3));
  DIVE.tentacles = new THREE.LineSegments(tg, new THREE.LineBasicMaterial({ color:0xf6d6ff, transparent:true, opacity:0.45, blending:THREE.AdditiveBlending, depthWrite:false }));
  DIVE.tentacles.frustumCulled = false; add(DIVE.tentacles);

  /* Light rays from the surface */
  const rayTex = tex(canvasRay());
  DIVE.rays = [];
  for (let i = 0; i < 16; i++){
    const u = i / 15, p = path.getPointAt(Math.min(0.98, u)), ry = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 2.6, 24, 16, 1, true), new THREE.MeshBasicMaterial({ map:rayTex, color:0xcff4ff, transparent:true, opacity:0.12, blending:THREE.AdditiveBlending, depthWrite:false, side:THREE.DoubleSide }));
    ry.position.set(p.x + (r() - 0.5) * 14, -12, p.z + (r() - 0.5) * 14); ry.rotation.z = 0.12 + (r() - 0.5) * 0.1; ry.userData.ph = r() * 6; add(ry); DIVE.rays.push(ry);
  }

  /* Bubbles */
  const nB = 160;
  DIVE.bubbles = new THREE.InstancedMesh(new THREE.SphereGeometry(1, 8, 6), new THREE.MeshBasicMaterial({ color:0xe8f8ff, transparent:true, opacity:0.5, depthWrite:false }), nB);
  DIVE.bubbles.frustumCulled = false; add(DIVE.bubbles);
  const vents = [[-17, 3], [-23, -2], [12, 4], [26, 16]];
  DIVE.bub = [];
  for (let i = 0; i < nB; i++){ const vt = vents[i % vents.length], diver = i >= 80; DIVE.bub.push({ x:vt[0], y:floorY(vt[0], vt[1]) + r() * 16, z:vt[1], s:0.02 + r() * 0.05, vx:vt[0], vz:vt[1], diver, life:diver ? 0 : 1, ph:r() * 6 }); }

  /* Drifting specks */
  const nS = 1400, sp = new Float32Array(nS * 3);
  for (let i = 0; i < nS; i++){ sp[i * 3] = (r() - 0.5) * 30; sp[i * 3 + 1] = (r() - 0.5) * 30; sp[i * 3 + 2] = (r() - 0.5) * 30; }
  const sgeo = new THREE.BufferGeometry(); sgeo.setAttribute('position', new THREE.BufferAttribute(sp, 3));
  DIVE.snow = new THREE.Points(sgeo, new THREE.ShaderMaterial({
    uniforms:{ uTime:DIVE.uTime, uCam:{ value:new THREE.Vector3() }, uSize:{ value:3.0 * Math.min(window.devicePixelRatio || 1, 2) } },
    vertexShader:'uniform float uTime; uniform vec3 uCam; uniform float uSize; varying float vA;\nvoid main(){ vec3 p = position; p.y -= uTime * 0.07; p.x += sin(uTime * 0.2 + position.z) * 0.3; p = mod(p - uCam + 15.0, 30.0) - 15.0 + uCam; vec4 mv = modelViewMatrix * vec4(p, 1.0); gl_Position = projectionMatrix * mv; gl_PointSize = uSize * (6.0 / max(0.5, -mv.z)); vA = clamp(1.0 - (-mv.z) / 18.0, 0.0, 1.0); }',
    fragmentShader:'varying float vA;\nvoid main(){ vec2 c = gl_PointCoord - 0.5; float d = length(c); if (d > 0.5) discard; gl_FragColor = vec4(0.86, 0.95, 1.0, (0.5 - d) * 1.3 * vA * 0.7); }',
    transparent:true, depthWrite:false
  }));
  DIVE.snow.frustumCulled = false; add(DIVE.snow);

  /* Starfish on the sand */
  const starShape = new THREE.Shape();
  for (let k = 0; k <= 10; k++){ const a = k / 10 * Math.PI * 2 - Math.PI / 2, rr2 = k % 2 ? 0.07 : 0.2; k ? starShape.lineTo(Math.cos(a) * rr2, Math.sin(a) * rr2) : starShape.moveTo(Math.cos(a) * rr2, Math.sin(a) * rr2); }
  const starGeo = new THREE.ShapeGeometry(starShape); starGeo.rotateX(-Math.PI / 2);
  const stars = new MatBatch();
  for (let i = 0; i < 18; i++){ const x = -30 + r() * 62, z = -10 + r() * 36; e.set(0, r() * 6, 0); q.setFromEuler(e); stars.add(m4.compose(v.set(x, floorY(x, z) + 0.06, z), q, sc.set(1.4, 1, 1.4)), ['#ff6f61', '#ff9f43', '#c94f8a'][(r() * 3) | 0]); }
  root.add(stars.build(starGeo, new THREE.MeshLambertMaterial({ side:THREE.DoubleSide })));
}
function makeSchool(sp, n, len, h, w, base, wander, o, r){
  const geo = fishGeo(len, h, w), ph = new Float32Array(n);
  for (let i = 0; i < n; i++) ph[i] = r() * 6.28;
  geo.setAttribute('aPhase', new THREE.InstancedBufferAttribute(ph, 1));
  const mesh = new THREE.InstancedMesh(geo, fishMat(sp, len), n); mesh.frustumCulled = false;
  const pos = new Float32Array(n * 3), vel = new Float32Array(n * 3);
  for (let i = 0; i < n; i++){ pos[i * 3] = base[0] + (r() - 0.5) * 4; pos[i * 3 + 1] = base[1] + (r() - 0.5) * 1.5; pos[i * 3 + 2] = base[2] + (r() - 0.5) * 4; vel[i * 3] = (r() - 0.5); vel[i * 3 + 2] = (r() - 0.5); }
  return Object.assign({ mesh, n, pos, vel, base, wander, ph:r() * 6, hx:base[0], hy:base[1], hz:base[2], home:0.35 }, o);
}

/* ---------------- Animate ---------------- */
const _dm = new THREE.Matrix4(), _dx = new THREE.Vector3(), _dy = new THREE.Vector3(), _dz = new THREE.Vector3(), _dp = new THREE.Vector3(), _dup = new THREE.Vector3(0, 1, 0), _dsc = new THREE.Vector3(1, 1, 1), _dq = new THREE.Quaternion();
function orientTo(m, px, py, pz, vx, vy, vz, s){
  _dz.set(vx, vy, vz); if (_dz.lengthSq() < 1e-8) _dz.set(0, 0, 1); _dz.normalize();
  _dx.crossVectors(_dup, _dz); if (_dx.lengthSq() < 1e-6) _dx.set(1, 0, 0); _dx.normalize();
  _dy.crossVectors(_dz, _dx);
  m.makeBasis(_dx.multiplyScalar(s), _dy.multiplyScalar(s), _dz.multiplyScalar(s)); m.setPosition(px, py, pz);
  return m;
}
function stepSchool(S, dt, t, cam){
  const { n, pos, vel } = S, sep2 = S.sep * S.sep, nb2 = S.nb * S.nb;
  S.hx = S.base[0] + Math.sin(t * 0.13 + S.ph) * S.wander[0];
  S.hy = S.base[1] + Math.sin(t * 0.21 + S.ph * 2) * S.wander[1];
  S.hz = S.base[2] + Math.cos(t * 0.11 + S.ph) * S.wander[2];
  for (let i = 0; i < n; i++){
    const i3 = i * 3, ix = pos[i3], iy = pos[i3 + 1], iz = pos[i3 + 2];
    let sx = 0, sy = 0, sz = 0, ax = 0, ay = 0, az = 0, cx = 0, cy = 0, cz = 0, cnt = 0;
    for (let j = 0; j < n; j++){
      if (j === i) continue;
      const j3 = j * 3, dx = pos[j3] - ix, dy = pos[j3 + 1] - iy, dz = pos[j3 + 2] - iz, d2 = dx * dx + dy * dy + dz * dz;
      if (d2 > nb2) continue;
      cnt++; ax += vel[j3]; ay += vel[j3 + 1]; az += vel[j3 + 2]; cx += dx; cy += dy; cz += dz;
      if (d2 < sep2 && d2 > 1e-6){ const k = 1 / d2; sx -= dx * k; sy -= dy * k; sz -= dz * k; }
    }
    let fx = sx * 0.12, fy = sy * 0.12, fz = sz * 0.12;
    if (cnt){ fx += (ax / cnt - vel[i3]) * 1.2 + cx / cnt * 0.9; fy += (ay / cnt - vel[i3 + 1]) * 1.2 + cy / cnt * 0.9; fz += (az / cnt - vel[i3 + 2]) * 1.2 + cz / cnt * 0.9; }
    fx += (S.hx - ix) * S.home; fy += (S.hy - iy) * S.home * 1.6; fz += (S.hz - iz) * S.home;
    if (S.orbit){ const ox = ix - S.hx, oz = iz - S.hz; fx += -oz * S.orbit; fz += ox * S.orbit; }
    const fl = floorY(ix, iz) + 1.1; if (iy < fl) fy += (fl - iy) * 5;
    if (iy > -1.6) fy -= (iy + 1.6) * 5;
    const ddx = ix - cam.x, ddy = iy - cam.y, ddz = iz - cam.z, dd2 = ddx * ddx + ddy * ddy + ddz * ddz;
    if (dd2 < 7.3){ const k = (7.3 - dd2) * 1.6 / Math.sqrt(dd2 + 0.02); fx += ddx * k; fy += ddy * k; fz += ddz * k; }
    let vx = vel[i3] + fx * dt, vy = vel[i3 + 1] + fy * dt, vz = vel[i3 + 2] + fz * dt;
    let sp = Math.hypot(vx, vy, vz);
    if (sp > S.maxV){ vx *= S.maxV / sp; vy *= S.maxV / sp; vz *= S.maxV / sp; sp = S.maxV; }
    else if (sp < S.minV && sp > 1e-5){ vx *= S.minV / sp; vy *= S.minV / sp; vz *= S.minV / sp; sp = S.minV; }
    const hz = Math.hypot(vx, vz); if (Math.abs(vy) > hz * 0.6){ vy = Math.sign(vy) * hz * 0.6; }
    vel[i3] = vx; vel[i3 + 1] = vy; vel[i3 + 2] = vz;
  }
  for (let i = 0; i < n; i++){
    const i3 = i * 3; pos[i3] += vel[i3] * dt; pos[i3 + 1] += vel[i3 + 1] * dt; pos[i3 + 2] += vel[i3 + 2] * dt;
    S.mesh.setMatrixAt(i, orientTo(_dm, pos[i3], pos[i3 + 1], pos[i3 + 2], vel[i3], vel[i3 + 1], vel[i3 + 2], 1));
  }
  S.mesh.instanceMatrix.needsUpdate = true;
}
function circlePose(o, t, g, bob){
  const a = t * o.sp + (o.a0 || 0), x = o.c[0] + Math.cos(a) * o.r, z = o.c[2] + Math.sin(a) * o.r, y = o.c[1] + Math.sin(t * 0.3) * (bob || 0.6);
  g.position.set(x, y, z);
  const tx = -Math.sin(a) * Math.sign(o.sp), tz = Math.cos(a) * Math.sign(o.sp);
  g.rotation.set(0, Math.atan2(tx, tz), 0);
  return a;
}
function animateDive(dt, camWorld){
  if (!DIVE.root) return;
  DIVE.t += dt; DIVE.uTime.value = DIVE.t;
  const t = DIVE.t, cam = DIVE.camLocal.set(camWorld.x - DV.x, camWorld.y, camWorld.z - DV.z);
  if (DIVE.caustic){ DIVE.caustic.offset.set(t * 0.012, t * 0.008); }
  if (DIVE.surface){ DIVE.surface.offset.set(t * 0.01, -t * 0.006); }
  const sdt = Math.min(dt, 0.05);
  for (const S of DIVE.schools) stepSchool(S, sdt, t, cam);
  DIVE.clownData.forEach((c, i) => { const a = t * c.sp + c.ph, x = c.x + Math.cos(a) * c.rad, z = c.z + Math.sin(a) * c.rad, y = c.y + Math.sin(t * 1.3 + c.ph) * 0.1; DIVE.clowns.setMatrixAt(i, orientTo(_dm, x, y, z, -Math.sin(a) * c.sp, 0, Math.cos(a) * c.sp, 1)); });
  if (DIVE.clowns) DIVE.clowns.instanceMatrix.needsUpdate = true;
  const tu = DIVE.turtle; if (tu){ circlePose(tu, t, tu.g, 0.4); tu.fl.forEach((f) => { const s = Math.sin(t * (f.front ? 1.2 : 1.4) + (f.front ? 0 : 1.2)); f.pv.rotation.z = f.sx * (f.front ? 0.45 : 0.2) * s; f.pv.rotation.y = f.sx * 0.25 * s; }); }
  const sh = DIVE.shark; if (sh){ circlePose(sh, t, sh.g, 0.5); const ph = t * 1.1 + 4.3 * 0.45; sh.tail.position.x = Math.sin(ph) * 0.3; sh.tail.rotation.y = Math.cos(ph) * 0.35; }
  const mn = DIVE.manta; if (mn){ circlePose(mn, t, mn.g, 0.8); mn.g.rotation.z = Math.sin(t * 0.4) * 0.08; }
  for (const f of DIVE.fans) f.rotation.x = Math.sin(t * 0.9 + f.userData.ph) * 0.12;
  for (const ry of DIVE.rays){ const d = Math.hypot(ry.position.x - cam.x, ry.position.z - cam.z); ry.material.opacity = (0.08 + 0.05 * (0.5 + 0.5 * Math.sin(t * 0.5 + ry.userData.ph))) * clamp(1.15 - d / 30, 0, 1); ry.visible = d < 36; }
  const tp = DIVE.tentacles.geometry.attributes.position; let k = 0;
  for (const j of DIVE.jellies){
    const pulse = Math.sin(t * 2.0 + j.ph), jd = j.g.position.distanceTo(cam), jf = clamp(1.25 - jd / 22, 0, 1);
    j.g.visible = jf > 0; j.bell.material.opacity = 0.45 * jf; j.g.children[1].material.opacity = 0.6 * jf;
    j.g.position.y += (j.vy * (0.6 + 0.8 * Math.max(0, pulse))) * dt;
    if (j.g.position.y > -1.6) j.g.position.y = -8.5;
    j.bell.scale.set(1 - 0.12 * pulse, 1 + 0.16 * pulse, 1 - 0.12 * pulse);
    const gx = j.g.position.x, gy = j.g.position.y, gz = j.g.position.z;
    for (let a = 0; a < 6; a++){
      const ang = a / 6 * Math.PI * 2, bx = gx + Math.cos(ang) * 0.24 * (1 - 0.12 * pulse), bz = gz + Math.sin(ang) * 0.24 * (1 - 0.12 * pulse);
      let px = bx, py = gy, pz = bz;
      for (let s = 1; s <= 12; s++){
        const nx = bx + Math.sin(t * 1.4 + s * 0.5 + a + j.ph) * 0.03 * s, ny = gy - s * 0.13, nz = bz + Math.cos(t * 1.2 + s * 0.45 + a) * 0.03 * s;
        tp.setXYZ(k++, px, py, pz); tp.setXYZ(k++, nx, ny, nz); px = nx; py = ny; pz = nz;
      }
    }
  }
  tp.needsUpdate = true;
  DIVE.breath -= dt;
  const spawn = DIVE.breath <= 0; if (spawn) DIVE.breath = 3.6;
  let spawned = 0;
  DIVE.bub.forEach((b, i) => {
    if (b.diver){
      if (spawn && b.life <= 0 && spawned < 12){ b.x = cam.x + (Math.random() - 0.5) * 0.3; b.y = cam.y - 0.35; b.z = cam.z + (Math.random() - 0.5) * 0.3; b.life = 6; spawned++; }
      if (b.life <= 0){ DIVE.bubbles.setMatrixAt(i, _dm.makeScale(0, 0, 0)); return; }
      b.life -= dt; b.y += (0.9 + b.s * 8) * dt; b.x += Math.sin(t * 3 + b.ph) * 0.006;
    } else {
      b.y += (0.6 + b.s * 6) * dt; b.x = b.vx + Math.sin(t * 2 + b.ph) * 0.12; b.z = b.vz + Math.cos(t * 2.3 + b.ph) * 0.12;
      if (b.y > -0.3) b.y = floorY(b.vx, b.vz) + 0.2;
    }
    if (b.y > -0.2) b.life = 0;
    _dsc.setScalar(b.s); _dp.set(b.x, b.y, b.z); _dq.identity(); DIVE.bubbles.setMatrixAt(i, _dm.compose(_dp, _dq, _dsc));
  });
  DIVE.bubbles.instanceMatrix.needsUpdate = true;
  DIVE.snow.material.uniforms.uCam.value.copy(cam);
}
const DIVE_CREATURES = { 2:'Green sea turtle', 5:'Whale shark', 6:'Manta ray', 7:'Jellyfish' };
function diveLookAt(kind, cam){
  let best = null, bd = Infinity;
  const near = (p) => { const d = p.distanceTo(cam); if (d < bd){ bd = d; best = p; } };
  if (kind === 'anemone') DIVE.anem.forEach(near);
  else if (kind === 'turtle') near(DIVE.turtle.g.position);
  else if (kind === 'shark') near(DIVE.shark.g.position);
  else if (kind === 'manta') near(DIVE.manta.g.position);
  else if (kind === 'jelly') DIVE.jellies.forEach((j) => near(j.g.position));
  else if (kind === 'school'){ const S = DIVE.schools[2]; near(new THREE.Vector3(S.hx, S.hy, S.hz)); }
  return best && bd < 22 ? best : null;
}
