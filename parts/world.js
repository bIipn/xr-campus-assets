/* ================================================================
   3D world
   ================================================================ */
let THREEOK = false;
let renderer, scene, camera, raycaster;
const ART = {};
const pickItems = [], blockers = [], floors = [];
const OBST = [];
const PARTS = [-6, -18, -30];
const H_ROOM = 4.4, EYE = 1.62, H_HALL = 3.4, H_LIB = 7.6, H_SCHOOL = 3.6;
const cam = { x:0, z:-0.7, yaw:0, pitch:0.02 };
let ANISO = 4;

function srgb(hex){ return new THREE.Color(hex); }
/* Phones and headsets: once a picture is on the GPU, the canvas it was drawn on is freed.
   iOS Safari caps total canvas memory, and the campus paints a few hundred MB of signs, posters and floors. */
const LEAN_CANVAS = (() => { const ua = navigator.userAgent || ''; return COARSE || /Android|iPhone|iPad|Mobile|OculusBrowser|Quest|Pico/i.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1); })();
const CANVAS_FREE = { n:0, mb:0, gpu:0 };
/* Phones: no painted texture larger than this, and LEAN_K shrinks big ones further while it is below 1 */
const LEAN_MAX = 1024;
let LEAN_K = 1;
function keepCanvas(c){ c.__keep = true; return c; }
function texUploaded(t){
  t.onUpdate = null;
  const c = t.image;
  if (c && c.width > 1) CANVAS_FREE.gpu += c.width * c.height * 4 * (t.generateMipmaps ? 1.333 : 1) / 1e6;
  if (!c || c.__keep || --c.__users > 0) return;
  CANVAS_FREE.n++; CANVAS_FREE.mb += c.width * c.height * 4 / 1e6;
  c.__released = true; c.width = 1; c.height = 1;
}
let CANVAS_BOOT = true;
const CANVAS_PENDING = [], NRM_PRE = [];
function leanTex(t){
  const c = t.image;
  if (LEAN_CANVAS && c && c.getContext && !c.__keep){
    if (c.__released) console.warn('A freed canvas was used again');
    c.__users = (c.__users || 0) + 1; t.onUpdate = texUploaded;
    if (LEAN_K < 1 && !c.__leanK) c.__leanK = LEAN_K;
    if (CANVAS_BOOT) CANVAS_PENDING.push(t);
  }
  return t;
}
/* Upload what has been drawn so far and free those canvases, so boot never holds them all at once.
   Tiled textures get their normal maps made first, while the pixels still exist. */
function leanShrink(c, tiled){
  if (c.__shrunk) return; c.__shrunk = true;
  const m = Math.max(c.width, c.height), k = Math.min(LEAN_MAX / m, m > (tiled ? 512 : 384) ? (c.__leanK || 1) : 1);
  if (!(k < 0.999)) return;
  const w = Math.max(4, Math.round(c.width * k)), h = Math.max(4, Math.round(c.height * k)), tmp = mk(w, h);
  tmp.getContext('2d').drawImage(c, 0, 0, w, h);
  c.width = w; c.height = h; c.getContext('2d').drawImage(tmp, 0, 0); tmp.width = 1; tmp.height = 1;
}
function flushCanvases(){
  if (!LEAN_CANVAS || !renderer) return;
  for (const t of CANVAS_PENDING.splice(0)){
    const c = t.image;
    if (t.onUpdate !== texUploaded || !c || c.__released) continue;
    if (t.wrapS === THREE.RepeatWrapping && !NRM.has(c)){ const n = normalCanvas(c, 1.6); if (n) NRM_PRE.push(n); }
    leanShrink(c, t.wrapS === THREE.RepeatWrapping);
    renderer.initTexture(t);
  }
}
function tex(canvas, aniso){ const t = new THREE.CanvasTexture(canvas); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = aniso || ANISO; t.needsUpdate = true; return leanTex(t); }
function repTex(canvas, rx, ry){ const t = tex(canvas); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rx, ry); return t; }
function stdMat(hex, rough, metal, extra){ return new THREE.MeshStandardMaterial(Object.assign({ color:srgb(hex), roughness:rough == null ? 0.8 : rough, metalness:metal || 0 }, extra || {})); }
function basicMat(canvas, tint){ return new THREE.MeshBasicMaterial({ map:tex(canvas), toneMapped:false, color:tint == null ? 0xffffff : tint }); }
function glowMatOf(hex){ return new THREE.MeshBasicMaterial({ color:srgb(hex), toneMapped:false }); }
function addBox(w, h, d, mat, x, y, z, ry, parent){ const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); m.position.set(x, y, z); if (ry) m.rotation.y = ry; (parent || scene).add(m); return m; }
function addPlane(w, h, mat, x, y, z, ry, parent){ const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat); m.position.set(x, y, z); m.rotation.y = ry || 0; (parent || scene).add(m); return m; }
function addPool(w, d, x, y, z, opacity, canvas){
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, d), new THREE.MeshBasicMaterial({ map:tex(canvas || canvasPool()), transparent:true, opacity:opacity || 0.2, blending:THREE.AdditiveBlending, depthWrite:false, toneMapped:false }));
  m.rotation.x = -Math.PI / 2; m.position.set(x, y, z); scene.add(m); return m;
}

/* A wall along x (axis 'z', at z = at) or along z (axis 'x', at x = at), visible from the face side, with door notches and window holes. */
function addWall(o){
  const L = o.to - o.from, mid = (o.from + o.to) / 2, h = o.h;
  const s = o.axis === 'z' ? (o.face > 0 ? 1 : -1) : (o.face > 0 ? -1 : 1);
  const toU = (w) => s * (w - mid);
  const notches = (o.doors || []).map((d) => { const a = toU(d.a), b = toU(d.b); return { u0:Math.min(a, b), u1:Math.max(a, b), h:d.h }; }).sort((p, q) => p.u0 - q.u0);
  const shape = new THREE.Shape();
  shape.moveTo(-L/2, 0);
  for (const n of notches){ shape.lineTo(n.u0, 0); shape.lineTo(n.u0, n.h); shape.lineTo(n.u1, n.h); shape.lineTo(n.u1, 0); }
  shape.lineTo(L/2, 0); shape.lineTo(L/2, h); shape.lineTo(-L/2, h); shape.lineTo(-L/2, 0);
  for (const wd of (o.windows || [])){
    const a = toU(wd.a), b = toU(wd.b), u0 = Math.min(a, b), u1 = Math.max(a, b), p = new THREE.Path();
    p.moveTo(u0, wd.y0); p.lineTo(u1, wd.y0); p.lineTo(u1, wd.y1);
    if (wd.arch) p.absarc((u0 + u1) / 2, wd.y1, (u1 - u0) / 2, 0, Math.PI, false); else p.lineTo(u0, wd.y1);
    p.lineTo(u0, wd.y0);
    shape.holes.push(p);
  }
  const m = new THREE.Mesh(new THREE.ShapeGeometry(shape, 24), o.mat);
  if (o.axis === 'z'){ m.position.set(mid, 0, o.at); m.rotation.y = o.face > 0 ? 0 : Math.PI; }
  else { m.position.set(o.at, 0, mid); m.rotation.y = o.face > 0 ? Math.PI/2 : -Math.PI/2; }
  m.userData.blocker = true; scene.add(m); blockers.push(m);
  return m;
}
function addFloor(x0, x1, z0, z1, mat){ const m = new THREE.Mesh(new THREE.PlaneGeometry(x1 - x0, z1 - z0), mat); m.rotation.x = -Math.PI/2; m.position.set((x0 + x1) / 2, 0, (z0 + z1) / 2); m.userData.floor = true; scene.add(m); floors.push(m); return m; }
function addCeil(x0, x1, z0, z1, h, mat){ const m = new THREE.Mesh(new THREE.PlaneGeometry(x1 - x0, z1 - z0), mat); m.rotation.x = Math.PI/2; m.position.set((x0 + x1) / 2, h, (z0 + z1) / 2); scene.add(m); return m; }
function plasterMat(hex, tile){ const t = repTex(canvasPlaster(), 1 / (tile || 3), 1 / (tile || 3)); return new THREE.MeshStandardMaterial({ color:srgb(hex), map:t, roughness:0.95 }); }

class BoxBatch {
  constructor(){ this.a = []; }
  add(x, y, z, w, h, d, ry, rz, col){ this.a.push([x, y, z, w, h, d, ry || 0, rz || 0, col == null ? null : col]); }
  build(mat, colored){
    if (!this.a.length) return null;
    const mesh = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), mat, this.a.length);
    const m = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(0, 0, 0, 'YZX'), p = new THREE.Vector3(), s = new THREE.Vector3(), col = new THREE.Color();
    this.a.forEach((b, i) => {
      e.set(0, b[6], b[7]); q.setFromEuler(e); p.set(b[0], b[1], b[2]); s.set(b[3], b[4], b[5]); m.compose(p, q, s); mesh.setMatrixAt(i, m);
      if (colored){ col.set(b[8] || '#888888'); mesh.setColorAt(i, col); }
    });
    mesh.instanceMatrix.needsUpdate = true; if (colored && mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    const lo = new THREE.Vector3(Infinity, Infinity, Infinity), hi = new THREE.Vector3(-Infinity, -Infinity, -Infinity);
    for (const b of this.a){ const r = Math.max(b[3], b[4], b[5]) / 2; lo.min(new THREE.Vector3(b[0] - r, b[1] - r, b[2] - r)); hi.max(new THREE.Vector3(b[0] + r, b[1] + r, b[2] + r)); }
    const sph = new THREE.Sphere(); new THREE.Box3(lo, hi).getBoundingSphere(sph);
    mesh.geometry.boundingSphere = sph; mesh.frustumCulled = true;
    scene.add(mesh); return mesh;
  }
}

/* Stand far enough back that a frame fits the screen, on a phone or a laptop. */
function fitDist(halfW, halfH, minD){
  const v = THREE.MathUtils.degToRad(camera.fov), hf = 2 * Math.atan(Math.tan(v / 2) * camera.aspect);
  return Math.max(minD, halfW / Math.tan(hf / 2), halfH / Math.tan(v / 2));
}
function viewFor(it){
  const p = it.place;
  if (p.wall === 'L' || p.wall === 'R'){
    const d = clamp(fitDist(it.size[0] / 2 + 0.32, it.size[1] / 2 + 0.35, 2.75), 2.75, 5.6);
    return p.wall === 'L' ? { x:-6 + d, z:p.z, yaw:Math.PI/2, pitch:-0.14 } : { x:6 - d, z:p.z, yaw:-Math.PI/2, pitch:-0.14 };
  }
  if (p.wall === 'E'){ const d = clamp(fitDist(1.15, 1.15, 3.5), 3.5, 8); return { x:p.x || 0, z:-42 + d, yaw:0, pitch:-0.08 }; }
  const d = clamp(fitDist(0.5, 0.5, 2.0), 2.0, 3.2);
  return { x:p.x + (p.x < 0 ? d : -d), z:p.z, yaw:p.x < 0 ? Math.PI/2 : -Math.PI/2, pitch:-0.3 };
}
function lobbyView(){ const d = clamp(fitDist(1.95, 1.1, 3.4), 3.4, 5.4); return { x:0, z:-d, yaw:Math.PI, pitch:0.05 }; }

/* ---------------- Museum ---------------- */
function buildScene(){
  scene = new THREE.Scene();
  scene.background = srgb(0x0d1613);
  camera = new THREE.PerspectiveCamera(66, 1, 0.05, 260);
  camera.rotation.order = 'YXZ';
  raycaster = new THREE.Raycaster();
  ANISO = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  const mStart = new Set(scene.children);

  const fl = new THREE.Mesh(new THREE.PlaneGeometry(12, 42), new THREE.MeshStandardMaterial({ map:repTex(canvasFloor(), 10, 42 / 2.4), roughness:0.58 }));
  fl.rotation.x = -Math.PI/2; fl.position.set(0, 0, -21); fl.userData.floor = true; scene.add(fl); floors.push(fl);
  addCeil(-6, 6, -42, 0, H_ROOM, stdMat(0x3a3833, 1));

  const plaster = canvasPlaster();
  const wallMats = GALLERIES.map((g) => { const t = tex(plaster); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(4, 1.5); return new THREE.MeshStandardMaterial({ color:srgb(g.wall), map:t, roughness:0.95 }); });
  const wood = stdMat(0x2a1c12, 0.6);
  const brass = stdMat(0xb58f4c, 0.35, 0.35);
  const stone = stdMat(0xe4ddcf, 0.85);
  const glowMat = new THREE.MeshBasicMaterial({ color:0xffe9c8, toneMapped:false });
  const partMats = GALLERIES.map((g) => { const t = tex(plaster); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(1/3, 1/3); return new THREE.MeshStandardMaterial({ color:srgb(g.wall), map:t, roughness:0.95 }); });

  GALLERIES.forEach((g, i) => {
    const len = g.z0 - g.z1, zc = (g.z0 + g.z1) / 2;
    if (i > 0){
      const geo = new THREE.PlaneGeometry(len, H_ROOM);
      const L = new THREE.Mesh(geo, wallMats[i]); L.rotation.y = Math.PI/2; L.position.set(-6, H_ROOM/2, zc); L.userData.blocker = true; scene.add(L); blockers.push(L);
      const R = new THREE.Mesh(geo, wallMats[i]); R.rotation.y = -Math.PI/2; R.position.set(6, H_ROOM/2, zc); R.userData.blocker = true; scene.add(R); blockers.push(R);
      for (const s of [-1, 1]) addBox(0.04, 0.16, len, wood, s * (6 - 0.02), 0.08, zc);
    }
    const lp = new THREE.PointLight(0xffe2b9, i === 0 ? 0.75 : 0.9, 19, 1.6); lp.position.set(0, 3.9, zc); scene.add(lp);
    for (const dz of [-len/4, len/4]) for (const dx of [-2.4, 2.4]){ const d = new THREE.Mesh(new THREE.CircleGeometry(0.12, 20), glowMat); d.rotation.x = Math.PI/2; d.position.set(dx, H_ROOM - 0.01, zc + dz); scene.add(d); }
  });
  const back = new THREE.Mesh(new THREE.PlaneGeometry(12, H_ROOM), wallMats[0]); back.rotation.y = Math.PI; back.position.set(0, H_ROOM/2, 0); back.userData.blocker = true; scene.add(back); blockers.push(back);
  /* The end wall of Gallery 3 opens into the Wax Hall */
  const endShape = new THREE.Shape();
  endShape.moveTo(-6, 0); endShape.lineTo(-1.6, 0); endShape.lineTo(-1.6, 3.1); endShape.lineTo(1.6, 3.1); endShape.lineTo(1.6, 0);
  endShape.lineTo(6, 0); endShape.lineTo(6, H_ROOM); endShape.lineTo(-6, H_ROOM); endShape.lineTo(-6, 0);
  const end = new THREE.Mesh(new THREE.ShapeGeometry(endShape), wallMats[3]); end.position.set(0, 0, -42); end.userData.blocker = true; scene.add(end); blockers.push(end);

  const wallShape = new THREE.Shape();
  wallShape.moveTo(-6, 0); wallShape.lineTo(-1.6, 0); wallShape.lineTo(-1.6, 3.1); wallShape.lineTo(1.6, 3.1); wallShape.lineTo(1.6, 0);
  wallShape.lineTo(6, 0); wallShape.lineTo(6, H_ROOM); wallShape.lineTo(-6, H_ROOM); wallShape.lineTo(-6, 0);
  const wallGeo = new THREE.ShapeGeometry(wallShape);
  PARTS.forEach((zp, k) => {
    const front = new THREE.Mesh(wallGeo, partMats[k]); front.position.set(0, 0, zp + 0.15);
    const backFace = new THREE.Mesh(wallGeo, partMats[k + 1]); backFace.rotation.y = Math.PI; backFace.position.set(0, 0, zp - 0.15);
    for (const m of [front, backFace]){ m.userData.blocker = true; scene.add(m); blockers.push(m); }
    for (const s of [-1, 1]) addBox(0.1, 3.15, 0.38, wood, s * 1.65, 1.575, zp);
    addBox(3.4, 0.1, 0.38, wood, 0, 3.15, zp);
    addPlane(3.1, 0.53, basicMat(drawDoorSign(GALLERIES[k + 1], k + 1)), 0, 3.76, zp + 0.156);
  });

  const poolMat = new THREE.MeshBasicMaterial({ map:tex(canvasPool()), transparent:true, opacity:0.24, blending:THREE.AdditiveBlending, depthWrite:false, toneMapped:false });
  const matMat = stdMat(0xf1ece2, 0.9);
  const frameCol = { milestone:0x2a1d12, mission:0x6b4a2b, event:0x171412, program:0x3a2617, story:0x4d3a22, resource:0x2a1d12, project:0x171412 };

  function wallPanel(canvas, w, h, x, y, z, rotY, frameColor){
    const grp = new THREE.Group(); grp.position.set(x, 0, z); grp.rotation.y = rotY;
    if (frameColor != null) addBox(w + 0.08, h + 0.08, 0.04, stdMat(frameColor, 0.5, 0.3), 0, y, 0.02, 0, grp);
    addPlane(w, h, basicMat(canvas), 0, y, 0.042, 0, grp);
    scene.add(grp);
    return grp;
  }
  wallPanel(drawTitlePanel(), 3.6, 1.9, 0, 2.05, -0.005, Math.PI, 0xb58f4c);
  wallPanel(drawPlaque(), 2.0, 0.87, 4.3, 1.7, -0.005, Math.PI, null);
  wallPanel(drawPartnersPanel(), 3.0, 1.58, 3.8, 1.9, -6 + 0.155, 0, 0xb58f4c);
  wallPanel(drawDirectory(), 3.0, 1.6, -3.8, 1.9, -6 + 0.155, 0, 0xb58f4c);

  for (const it of ITEMS){
    const p = it.place;
    if (p.wall === 'P'){ buildPedestal(it, { wood, brass, stone }); continue; }
    const [w, h] = it.size;
    const grp = new THREE.Group();
    if (p.wall === 'L'){ grp.position.set(-6 + 0.005, 0, p.z); grp.rotation.y = Math.PI/2; }
    else if (p.wall === 'R'){ grp.position.set(6 - 0.005, 0, p.z); grp.rotation.y = -Math.PI/2; }
    else grp.position.set(p.x || 0, 0, -42 + 0.005);
    const cy = p.wall === 'E' ? 1.9 : 1.74;
    const pool = new THREE.Mesh(new THREE.PlaneGeometry(w + 1.7, h + 2.0), poolMat); pool.position.set(0, cy + 0.12, 0.004); grp.add(pool);
    const fw = w + 0.22, fh = h + 0.22;
    const frame = addBox(fw, fh, 0.05, stdMat(frameCol[it.kind] || 0x171412, 0.45, 0.15), 0, cy, 0.025, 0, grp);
    const mat = addPlane(w + 0.14, h + 0.14, matMat, 0, cy, 0.0505, 0, grp);
    const art = addPlane(w, h, new THREE.MeshBasicMaterial({ map:tex(ART[it.id]), toneMapped:false, color:0xf4efe6 }), 0, cy, 0.052, 0, grp);
    const bw = Math.min(w * 0.62, 1.1);
    addBox(bw, 0.035, 0.05, brass, 0, cy + fh/2 + 0.16, 0.2, 0, grp);
    addBox(0.02, 0.02, 0.2, brass, 0, cy + fh/2 + 0.16, 0.1, 0, grp);
    const glow = new THREE.Mesh(new THREE.PlaneGeometry(bw * 0.95, 0.014), glowMat); glow.rotation.x = Math.PI/2; glow.position.set(0, cy + fh/2 + 0.141, 0.2); grp.add(glow);
    const pl = addPlane(0.36, 0.204, basicMat(drawPlacard(it), 0xe9e3d8), fw/2 + 0.32, 1.2, 0.01, 0, grp);
    for (const m of [frame, mat, art, pl]){ m.userData.item = it; pickItems.push(m); }
    scene.add(grp);
  }

  const bench = new THREE.Group(); bench.position.set(0, 0, -35.4);
  addBox(1.8, 0.07, 0.46, stdMat(0x5a3b22, 0.55), 0, 0.45, 0, 0, bench);
  for (const sx of [-0.78, 0.78]) for (const sz of [-0.18, 0.18]) addBox(0.05, 0.42, 0.05, wood, sx, 0.21, sz, 0, bench);
  scene.add(bench); OBST.push({ x:0, z:-35.4, r:1.05 });

  const hemi = new THREE.HemisphereLight(0xfff1dc, 0x2a2118, 0.62), amb = new THREE.AmbientLight(0xffffff, 0.1);
  scene.add(hemi, amb);

  const M = { wood, brass, stone, glowMat, partMats };
  buildLobbySides(M);
  buildHall(-1, M); buildHall(1, M);
  /* The Wax Hall doorway: a wood frame through the wall, its sign, and a poster that points the way */
  for (const s of [-1, 1]) addBox(0.1, 3.15, 0.38, wood, s * 1.65, 1.575, -42.15);
  addBox(3.4, 0.1, 0.38, wood, 0, 3.15, -42.15);
  addPlane(3.1, 0.53, basicMat(drawWaxDoorSign()), 0, 3.76, -42 + 0.006);
  wallPanel(drawWaxTeaser(), 1.5, 1.5, 3.7, 1.86, -42 + 0.006, 0, 0x5e1a22);
  flushCanvases();
  WING.museum = new THREE.Group();
  for (const o of [...scene.children]) if (!mStart.has(o) && !o.isLight) WING.museum.add(o);
  scene.add(WING.museum);
  LIGHTS.hemi = hemi; LIGHTS.amb = amb;
  waxMats();
  /* The intro wall shows from both sides of the doorway, so it has its own group */
  LEAN_K = 0.75;
  WING.waxIntro = grouped(() => buildWaxEntry(M));
  WING.wax = grouped(() => buildWaxHall(M)); flushCanvases();
  LEAN_K = 1;
  LIGHTS.sun = new THREE.DirectionalLight(0xfff0d8, 0); LIGHTS.sun.position.set(SUN_DIR[0], SUN_DIR[1], SUN_DIR[2]); scene.add(LIGHTS.sun);
  WING.lib = grouped(() => buildLibrary(M)); flushCanvases();
  loadBakedRoom('lib', WING.lib);
  WING.school = grouped(() => { buildSchool(M); flushCanvases(); buildStudio(M); flushCanvases(); buildSchoolRooms(M); }); flushCanvases();
  WING.outside = grouped(() => buildExterior(M)); flushCanvases();
  WING.play = grouped(() => buildPlayground(M)); flushCanvases();
  WING.dive = grouped(() => buildDive(M)); WING.dive.visible = false; flushCanvases();
  buildStaff(M);
  WING.museum.add(STAFF.margaret.root); WING.lib.add(STAFF.rosa.root); WING.school.add(STAFF.hale.root); WING.play.add(STAFF.rae.root);
  buildTokens();
  for (const st of Object.values(STAFF)) st.root.userData.noMerge = true;
  if (NATURE.grass) NATURE.grass.userData.noShadow = true;
  gfxUpgradeScene(new Set([WING.dive]));
  for (const n of NRM_PRE) if (!n.__users){ n.__released = true; n.width = 1; n.height = 1; }
  NRM_PRE.length = 0;
  gfxLights();
  GFX.aoHide = [SKY, NATURE.grass].filter(Boolean);
  for (const k of ['museum', 'wax', 'lib', 'school', 'outside', 'play']) mergeStatic(WING[k]);
  for (const g of COASTER.cars.concat([YA.ring])) if (g) mergeStatic(g);
  if (!scene.fog) scene.fog = new THREE.Fog(0xd6e5e9, 80, 250);
}
/* Fewer draw calls: static meshes that share a material become one mesh */
function mergeStatic(root){
  root.updateMatrixWorld(true);
  const inv = new THREE.Matrix4().copy(root.matrixWorld).invert(), buckets = new Map(), drop = new Set(), baseHook = THREE.Material.prototype.onBeforeCompile;
  root.traverse((o) => {
    if (!o.isMesh || o.isInstancedMesh || !o.visible || o.renderOrder) return;
    const ud = o.userData, keys = Object.keys(ud);
    if (keys.some((k) => !['staff', 'ride', 'item'].includes(k)) || keys.length > 1) return;
    const m = o.material;
    if (!m || Array.isArray(m) || m.transparent || m.visible === false || m.onBeforeCompile !== baseHook || !o.geometry.attributes.uv) return;
    for (let p = o.parent; p && p !== root; p = p.parent) if (p.userData.noMerge || !p.visible || !p.matrixAutoUpdate) return;
    const tag = keys.length ? keys[0] + ':' + (ud[keys[0]].id || ud[keys[0]]) : '';
    const key = m.uuid + '|' + tag;
    let b = buckets.get(key); if (!b){ b = { m, ud, tagged:keys.length > 0, list:[] }; buckets.set(key, b); }
    b.list.push(o);
  });
  const mw = new THREE.Matrix4();
  for (const b of buckets.values()){
    if (b.list.length < 2) continue;
    const geos = b.list.map((o) => { const g = o.geometry.index ? o.geometry.toNonIndexed() : o.geometry.clone(); g.applyMatrix4(mw.multiplyMatrices(inv, o.matrixWorld)); return g; });
    const merged = new THREE.Mesh(mergeFlat(geos), b.m);
    merged.castShadow = b.list[0].castShadow; merged.receiveShadow = b.list[0].receiveShadow;
    if (b.tagged){ Object.assign(merged.userData, b.ud); pickItems.push(merged); }
    root.add(merged);
    for (const o of b.list){ o.parent.remove(o); drop.add(o); }
  }
  if (drop.size) for (let i = pickItems.length - 1; i >= 0; i--) if (drop.has(pickItems[i])) pickItems.splice(i, 1);
}
const WING = {};
function grouped(fn){
  const g = new THREE.Group(), before = new Set(scene.children);
  fn();
  for (const o of [...scene.children]) if (!before.has(o) && !o.isLight) g.add(o);
  scene.add(g); return g;
}

function buildPedestal(it, M){
  const { x, z } = it.place;
  const grp = new THREE.Group(); grp.position.set(x, 0, z);
  const parts = [];
  addBox(0.72, 0.06, 0.72, M.wood, 0, 0.03, 0, 0, grp);
  parts.push(addBox(0.62, 1.0, 0.62, M.stone, 0, 0.5, 0, 0, grp));
  addBox(0.66, 0.03, 0.66, M.wood, 0, 1.015, 0, 0, grp);
  const caseGeo = new THREE.BoxGeometry(0.6, 0.5, 0.6);
  const glass = new THREE.Mesh(caseGeo, new THREE.MeshStandardMaterial({ color:0xffffff, transparent:true, opacity:0.1, roughness:0.05, depthWrite:false }));
  glass.position.y = 1.28; grp.add(glass); parts.push(glass);
  const edges = new THREE.LineSegments(new THREE.EdgesGeometry(caseGeo), new THREE.LineBasicMaterial({ color:0xcda961 })); edges.position.y = 1.28; grp.add(edges);
  if (it.object === 'headset'){
    const hs = new THREE.Group(); hs.position.set(0, 1.16, 0); hs.rotation.y = x < 0 ? Math.PI/2 : -Math.PI/2; hs.rotation.x = -0.12;
    const white = stdMat(0xe9e9e6, 0.4), dark = stdMat(0x23262a, 0.3, 0.1), strap = stdMat(0x3a3f44, 0.7);
    parts.push(addBox(0.2, 0.105, 0.09, white, 0, 0, 0, 0, hs));
    parts.push(addBox(0.172, 0.08, 0.012, dark, 0, 0, 0.046, 0, hs));
    for (const s of [-1, 1]) parts.push(addBox(0.014, 0.03, 0.15, strap, s * 0.1, 0.005, -0.1, 0, hs));
    const band = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.012, 8, 24, Math.PI), strap); band.rotation.x = Math.PI/2; band.position.set(0, 0.005, -0.175); hs.add(band); parts.push(band);
    for (const [u, v] of [[-0.07, 0.025], [0.07, 0.025], [-0.07, -0.028], [0.07, -0.028]]){ const cm = new THREE.Mesh(new THREE.CircleGeometry(0.008, 12), new THREE.MeshBasicMaterial({ color:0x111111 })); cm.position.set(u, v, 0.0525); hs.add(cm); }
    for (const s of [-1, 1]){ const ctl = new THREE.Mesh(new THREE.TorusGeometry(0.035, 0.008, 6, 18), dark); ctl.position.set(s * 0.13, -0.07, 0.06); ctl.rotation.x = Math.PI / 2.4; grp.add(ctl); }
    grp.add(hs);
  } else {
    const coverTex = tex(drawPlaybookCover(512, 680));
    coverTex.center.set(0.5, 0.5); coverTex.rotation = Math.PI;
    const holder = new THREE.Group(); holder.position.y = 1.03; holder.rotation.y = x < 0 ? -Math.PI/2 : Math.PI/2; holder.scale.setScalar(1.75);
    const st = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.012, 0.16), M.wood); st.position.set(0, 0.05, 0); st.rotation.x = -0.55; holder.add(st);
    const book = new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.008, 0.2), [M.stone, M.stone, new THREE.MeshBasicMaterial({ map:coverTex, toneMapped:false, color:0xe6dfd2 }), M.stone, M.stone, M.stone]);
    book.position.set(0, 0.062, 0); book.rotation.x = -0.55; holder.add(book); parts.push(book);
    grp.add(holder);
  }
  const pl = addPlane(0.36, 0.204, basicMat(drawPlacard(it), 0xe9e3d8), x < 0 ? 0.312 : -0.312, 0.78, 0, x < 0 ? Math.PI/2 : -Math.PI/2, grp);
  parts.push(pl);
  for (const m of parts){ m.userData.item = it; pickItems.push(m); }
  scene.add(grp);
  OBST.push({ x, z, r:0.75 });
}

/* ---------------- Lobby doorways and halls ---------------- */
function buildLobbySides(M){
  const mat = M.partMats[0];
  for (const sx of [-1, 1]){
    addWall({ axis:'x', at:sx * 6, from:-6, to:0, h:H_ROOM, face:-sx, mat, doors:[{ a:-4.2, b:-1.8, h:3.1 }] });
    addBox(0.04, 0.16, 1.8, M.wood, sx * (6 - 0.02), 0.08, -0.9);
    addBox(0.04, 0.16, 1.8, M.wood, sx * (6 - 0.02), 0.08, -5.1);
    for (const zz of [-4.25, -1.75]) addBox(0.38, 3.15, 0.1, M.wood, sx * 6, 1.575, zz);
    addBox(0.38, 0.1, 2.6, M.wood, sx * 6, 3.15, -3);
  }
  addPlane(2.7, 0.46, basicMat(drawWingSign('The Library', 'Reading room · Reference desk')), -6 + 0.012, 3.62, -3, Math.PI/2);
  addPlane(2.7, 0.46, basicMat(drawWingSign('Workshop School', 'Rooms 101–104 · Recess Yard')), 6 - 0.012, 3.62, -3, -Math.PI/2);
}
function buildHall(sx, M){
  const x0 = sx < 0 ? -12 : 6, x1 = sx < 0 ? -6 : 12, xm = (x0 + x1) / 2;
  const hallMat = plasterMat(sx < 0 ? 0x2a4438 : 0x2f4f63);
  addFloor(x0, x1, -4.6, -1.4, new THREE.MeshStandardMaterial({ map:repTex(canvasFloor(), 6 / 1.2, 3.2 / 2.4), roughness:0.58 }));
  addCeil(x0, x1, -4.6, -1.4, H_HALL, stdMat(0x3a3833, 1));
  addWall({ axis:'z', at:-4.6, from:x0, to:x1, h:H_HALL, face:1, mat:hallMat });
  addWall({ axis:'z', at:-1.4, from:x0, to:x1, h:H_HALL, face:-1, mat:hallMat });
  addWall({ axis:'x', at:sx * 6.002, from:-4.6, to:-1.4, h:H_HALL, face:sx, mat:hallMat, doors:[{ a:-4.2, b:-1.8, h:3.1 }] });
  for (const zz of [-4.6 + 0.02, -1.4 - 0.02]) addBox(x1 - x0, 0.16, 0.04, M.wood, xm, 0.08, zz);
  const lamp = new THREE.Mesh(new THREE.CircleGeometry(0.22, 24), M.glowMat); lamp.rotation.x = Math.PI/2; lamp.position.set(xm, H_HALL - 0.01, -3); scene.add(lamp);
  addPool(3.2, 2.6, xm, 0.006, -3, 0.12);
  const posters = sx < 0 ? ['read', 'vr'] : ['workshop', 'school'];
  addBox(0.84, 1.12, 0.03, M.wood, xm, 1.75, -4.6 + 0.015);
  addPlane(0.75, 1.025, basicMat(drawPoster(posters[0]), 0xeee8de), xm, 1.75, -4.6 + 0.032, 0);
  addBox(0.84, 1.12, 0.03, M.wood, xm, 1.75, -1.4 - 0.015);
  addPlane(0.75, 1.025, basicMat(drawPoster(posters[1]), 0xeee8de), xm, 1.75, -1.4 - 0.032, Math.PI);
}

/* ---------------- Library ---------------- */
const BOOK_COLS = ['#7a2a22','#5e1f1c','#2f4a33','#4d5a2e','#24324f','#2a5555','#5a3b22','#a58a5c','#d3c4a2','#1e1b18','#a07a2a','#4a2b3d','#8b4a2b','#3c4f63'];
function fillRow(books, r, o, s0, s1, yb, rowH){
  let s = s0 + 0.01;
  while (s < s1 - 0.03){
    if (r() < 0.03){ s += 0.06 + r() * 0.2; continue; }
    const w = 0.026 + r() * 0.042, h = Math.min(rowH - 0.05, rowH * (0.6 + r() * 0.32)), d = o.depth * (0.66 + r() * 0.24);
    if (s + w > s1 - 0.01) break;
    let rz = 0; if (r() < 0.025 && s + w + 0.14 < s1) rz = (0.18 + r() * 0.22) * (r() < 0.5 ? 1 : -1);
    const sc = s + w / 2, t = o.depth - 0.015 - d / 2;
    books.add(o.x + o.dir[0] * sc + o.n[0] * t, yb + 0.0125 + h / 2 * Math.cos(rz), o.z + o.dir[1] * sc + o.n[1] * t, w, h, d, o.ry, rz, shade(BOOK_COLS[(r() * BOOK_COLS.length) | 0], (r() - 0.5) * 0.25));
    s += w + (rz ? 0.14 : 0.0015);
  }
}
function bookcase(W8, books, r, o){
  o.ry = Math.atan2(-o.dir[1], o.dir[0]);
  const Ht = o.rows * o.rowH + 0.06;
  const P = (s, t, y) => [o.x + o.dir[0] * s + o.n[0] * t, y, o.z + o.dir[1] * s + o.n[1] * t];
  let q = P(o.len / 2, 0.012, o.y0 + Ht / 2); W8.add(q[0], q[1], q[2], o.len, Ht, 0.024, o.ry);
  q = P(o.len / 2, o.depth / 2, o.y0 + Ht + 0.03); W8.add(q[0], q[1], q[2], o.len + 0.08, 0.06, o.depth + 0.04, o.ry);
  const nDiv = Math.max(1, Math.round(o.len / 0.95)), seg = o.len / nDiv;
  for (let k = 0; k <= nDiv; k++){ q = P(k * seg, o.depth / 2, o.y0 + Ht / 2); W8.add(q[0], q[1], q[2], 0.045, Ht, o.depth, o.ry); }
  for (let i = 0; i <= o.rows; i++){ q = P(o.len / 2, o.depth / 2, o.y0 + i * o.rowH); W8.add(q[0], q[1], q[2], o.len, 0.025, o.depth, o.ry); }
  for (let i = 0; i < o.rows; i++) for (let k = 0; k < nDiv; k++) fillRow(books, r, o, k * seg + 0.025, (k + 1) * seg - 0.025, o.y0 + i * o.rowH, o.rowH);
}
const SHELF_VIEWS = {};
let LIB_LIGHT = null;
function buildLibrary(M){
  const X0 = -32, X1 = -12, Z0 = -13, Z1 = 7, H = H_LIB, r = rnd(4242);
  /* The room itself is a baked model (parts/baked.js); these invisible planes keep taps and walking working */
  const ghost = new THREE.MeshBasicMaterial({ visible:false });
  addFloor(X0, X1, Z0, Z1, ghost);
  addWall({ axis:'x', at:X1, from:Z0, to:Z1, h:H, face:-1, mat:ghost, doors:[{ a:-4.6, b:-1.4, h:H_HALL }] });
  addWall({ axis:'z', at:Z0, from:X0, to:X1, h:H, face:1, mat:ghost });
  addWall({ axis:'z', at:Z1, from:X0, to:X1, h:H, face:-1, mat:ghost });
  addWall({ axis:'x', at:X0, from:Z0, to:Z1, h:H, face:1, mat:ghost, windows:[{ a:-5.2, b:-0.8, y0:1.0, y1:4.6, arch:true }] });
  LIB_LIGHT = new THREE.PointLight(0xffe2b9, 0.95, 26, 1.3); LIB_LIGHT.position.set(-17.5, 6.4, -3); scene.add(LIB_LIGHT);

  /* The stacks: subject signs and the books you can open, on the ends of the baked cases */
  const coverBooks = new BoxBatch();
  for (const subj of SUBJECTS){
    const sx = -24.0 - 2.2 * subj.slot, north = subj.side === 'N';
    const za = north ? -12.4 : -0.4, zb = north ? -5.6 : 6.4, len = zb - za, zc = (za + zb) / 2;
    const ze = north ? zb + 0.045 : za - 0.045, face = north ? 0 : Math.PI, sgn = north ? 1 : -1;
    addPlane(0.56, 0.2, basicMat(drawSubjectSign(subj)), sx, 2.08, ze + sgn * 0.001, face);
    const list = BOOKS.filter((b) => b.subject === subj.id);
    list.forEach((b, i) => {
      const ox = list.length === 1 ? 0 : (i === 0 ? -0.135 : 0.135);
      const cv = new THREE.Mesh(new THREE.PlaneGeometry(0.2, 0.274), basicMat(drawBookCover(b, 384, 526), 0xe2dace));
      cv.rotation.set(-0.22, face, 0, 'YXZ'); cv.position.set(sx + ox * (north ? 1 : -1), 1.16, ze + sgn * 0.075);
      cv.userData.book = b; scene.add(cv); pickItems.push(cv);
      coverBooks.add(sx + ox * (north ? 1 : -1), 1.155, ze + sgn * 0.06, 0.2, 0.274, 0.02, face, 0, SUBJ[b.subject].color);
    });
    const proxy = new THREE.Mesh(new THREE.BoxGeometry(0.62, 2.3, len + 0.1), new THREE.MeshBasicMaterial({ visible:false }));
    proxy.position.set(sx, 1.15, zc); proxy.userData.shelf = subj.id; scene.add(proxy); pickItems.push(proxy);
    SHELF_VIEWS[subj.id] = north ? { x:sx, z:-2.6, yaw:0, pitch:-0.12 } : { x:sx, z:-3.4, yaw:Math.PI, pitch:-0.12 };
  }

  /* Reference desk, reading tables: the furniture is baked; keep the card and the walking obstacles */
  addPlane(1.5, 0.333, basicMat(drawTableCard('REFERENCE DESK', 'Ask Rosa anything'), 0xe9e3d8), -17.2, 0.62, -6.9 + 0.402, 0);
  OBST.push({ x:-18.2, z:-6.9, r:0.75 }, { x:-17.2, z:-6.9, r:0.75 }, { x:-16.2, z:-6.9, r:0.75 });
  for (const tz of [-10.8, 4.6]) for (const lx of [-18.7, -17.5, -16.3]) OBST.push({ x:lx, z:tz, r:1.05 });

  /* Featured table: every readable book */
  const perRow = Math.ceil(BOOKS.length / 2);
  BOOKS.forEach((b, i) => {
    const row = i < perRow ? 0 : 1, k = row ? i - perRow : i, n = row ? BOOKS.length - perRow : perRow, x = -15.0 + (k - (n - 1) / 2) * Math.min(0.42, 2.9 / Math.max(1, n - 1)), y = row ? 1.13 : 0.95, z = row ? 1.15 : 0.62;
    const cv = new THREE.Mesh(new THREE.PlaneGeometry(0.24, 0.33), basicMat(drawBookCover(b, 384, 526), 0xe2dace));
    cv.rotation.set(-0.25, Math.PI, 0, 'YXZ'); cv.position.set(x, y, z - 0.012); cv.userData.book = b; scene.add(cv); pickItems.push(cv);
    coverBooks.add(x, y, z + 0.004, 0.24, 0.33, 0.03, Math.PI, 0, SUBJ[b.subject].color);
  });
  coverBooks.build(stdMat(0xffffff, 0.8), true);
  addPlane(1.4, 0.31, basicMat(drawTableCard('FEATURED BOOKS', 'Tap any book to read it'), 0xe9e3d8), -15.0, 0.46, 0.9 - 0.452, Math.PI);
  OBST.push({ x:-16.1, z:0.9, r:0.75 }, { x:-15.0, z:0.9, r:0.75 }, { x:-13.9, z:0.9, r:0.75 });

  /* Freedom to Read board (its frame is baked) */
  const fb = new THREE.Group(); fb.position.set(-21.4, 0, 1.0); fb.rotation.y = Math.PI / 2;
  const fp = addPlane(1.3, 0.975, basicMat(ART.freedom, 0xece6da), 0, 1.35, 0.03, 0, fb);
  fp.userData.item = FREEDOM; pickItems.push(fp);
  scene.add(fb); OBST.push({ x:-21.4, z:1.0, r:0.65 });
  OBST.push({ x:-21.3, z:-9.2, r:0.5 });

  /* Hanging sign */
  const hs = addPlane(3.2, 0.87, basicMat(drawHangSign()), -14.4, 5.4, -3, Math.PI/2);
  for (const dz of [-1.3, 1.3]) addBox(0.02, H - 5.83, 0.02, M.brass, -14.4, (H + 5.83) / 2, -3 + dz);
  hs.userData.blockLabel = true;
}

/* ---------------- School ---------------- */
function lockerRun(x0, x1, zw, face){
  const len = x1 - x0;
  const front = new THREE.MeshStandardMaterial({ map:repTex(canvasLocker(), len / 0.4, 1), roughness:0.5, metalness:0.2 });
  const side = stdMat(0x2a4f66, 0.5, 0.2);
  const m = new THREE.Mesh(new THREE.BoxGeometry(len, 1.8, 0.42), [side, side, side, side, front, side]);
  m.position.set((x0 + x1) / 2, 0.98, zw + face * 0.21); m.rotation.y = face > 0 ? 0 : Math.PI; scene.add(m);
  addBox(len, 0.08, 0.38, stdMat(0x1b2a33, 0.6), (x0 + x1) / 2, 0.04, zw + face * 0.21);
}
function closedDoor(x, zw, s, num, name){
  const door = stdMat(0x7a5a3a, 0.55), frame = stdMat(0x4a3a2a, 0.5), steel = stdMat(0xb9c0c6, 0.3, 0.6);
  const zf = zw + s * 0.03, ry = s > 0 ? 0 : Math.PI;
  addBox(1.0, 2.2, 0.05, door, x, 1.1, zf);
  addPlane(0.26, 0.7, new THREE.MeshBasicMaterial({ color:srgb(0x23394a), toneMapped:false }), x + 0.22 * s, 1.55, zw + s * 0.058, ry);
  addBox(0.12, 0.03, 0.04, steel, x - 0.36 * s, 1.05, zw + s * 0.07);
  for (const dx of [-0.54, 0.54]) addBox(0.08, 2.3, 0.08, frame, x + dx, 1.15, zw + s * 0.03);
  addBox(1.16, 0.08, 0.08, frame, x, 2.3, zw + s * 0.03);
  addPlane(0.5, 0.214, basicMat(drawRoomSign(num, name, 'Opening next', false)), x - 0.88 * s, 1.62, zw + s * 0.012, ry);
}
function buildSchool(M){
  const X0 = 12, X1 = 34, Z0 = -4.75, Z1 = -1.25, H = H_SCHOOL;
  const wallMat = new THREE.MeshStandardMaterial({ map:repTex(canvasSchoolWall(), 1, 1 / 3.6), roughness:0.9 });
  addFloor(X0, X1, Z0, Z1, new THREE.MeshStandardMaterial({ map:repTex(canvasLino('#e6dfcc', '#b9d0cc'), 22 / 1.2, 3.5 / 1.2), roughness:0.45 }));
  addCeil(X0, X1, Z0, Z1, H, new THREE.MeshStandardMaterial({ map:repTex(canvasTile(), 22 / 0.6, 3.5 / 0.6), roughness:0.95 }));
  addWall({ axis:'z', at:Z0, from:X0, to:X1, h:H, face:1, mat:wallMat, doors:[{ a:18.1, b:19.9, h:2.6 }, { a:28.1, b:29.9, h:2.6 }] });
  addWall({ axis:'z', at:Z1, from:X0, to:X1, h:H, face:-1, mat:wallMat, doors:[{ a:18.1, b:19.9, h:2.6 }, { a:28.1, b:29.9, h:2.6 }] });
  addWall({ axis:'x', at:X0, from:Z0, to:Z1, h:H, face:1, mat:wallMat, doors:[{ a:-4.6, b:-1.4, h:H_HALL }] });
  addWall({ axis:'x', at:X1, from:Z0, to:Z1, h:H, face:-1, mat:wallMat, doors:[{ a:-4.2, b:-1.8, h:2.7 }] });
  for (const [a, b] of [[12.8, 17.8], [21.4, 27.8], [30.2, 33.6]]){ lockerRun(a, b, Z0, 1); }
  for (const [a, b] of [[12.8, 17.6], [20.2, 27.6], [30.2, 33.6]]){ lockerRun(a, b, Z1, -1); }
  /* All four workshop rooms are open: door frames, signs over the doors and blade signs */
  buildSchoolDoors(Z0, Z1);
  const cork = repTex(canvasCork(), 2, 1);
  for (const [zw, s, n] of [[Z0, 1, 3], [Z1, -1, 2]]){
    const ry = s > 0 ? 0 : Math.PI;
    addBox(2.4, 1.0, 0.03, new THREE.MeshStandardMaterial({ map:cork, roughness:0.95 }), 24, 2.5, zw + s * 0.015);
    for (let i = 0; i < n; i++) addPlane(0.36, 0.46, basicMat(drawFlyer(i + (s < 0 ? 3 : 0)), 0xeeeeee), 24 - (n - 1) * 0.36 + i * 0.72, 2.5, zw + s * 0.034, ry);
  }
  const lightMat = new THREE.MeshBasicMaterial({ color:0xfffaf0, toneMapped:false });
  for (let x = 14; x <= 32; x += 4) addBox(1.2, 0.03, 0.5, lightMat, x, H - 0.02, -3);
  addPlane(2.3, 0.506, basicMat(drawExitSign()), X1 - 0.012, 3.1, -3, -Math.PI/2);
  const pl = new THREE.PointLight(0xfff5e8, 0.85, 26, 1.4); pl.position.set(23, 3.3, -3); scene.add(pl);
}

/* ---------------- Room 101: 3D Paint Studio ---------------- */
let EASEL = null;
function buildStudio(M){
  const X0 = 14, X1 = 24, Z0 = -13, Z1 = -4.75, H = H_SCHOOL;
  const wallMat = plasterMat(0xe9e4da);
  addFloor(X0, X1, Z0, Z1, new THREE.MeshStandardMaterial({ map:repTex(canvasFloor([118, 90, 62], 55), 10 / 1.2, 8.25 / 2.4), roughness:0.55 }));
  addCeil(X0, X1, Z0, Z1, H, new THREE.MeshStandardMaterial({ map:repTex(canvasTile(), 10 / 0.6, 8.25 / 0.6), roughness:0.95 }));
  addWall({ axis:'z', at:Z1 - 0.012, from:X0, to:X1, h:H, face:-1, mat:wallMat, doors:[{ a:18.1, b:19.9, h:2.6 }] });
  addWall({ axis:'z', at:Z0, from:X0, to:X1, h:H, face:1, mat:wallMat });
  addWall({ axis:'x', at:X0, from:Z0, to:Z1, h:H, face:1, mat:wallMat });
  addWall({ axis:'x', at:X1, from:Z0, to:Z1, h:H, face:-1, mat:wallMat, windows:[{ a:-11.9, b:-10.5, y0:1.0, y1:2.7 }, { a:-9.6, b:-8.2, y0:1.0, y1:2.7 }, { a:-7.3, b:-5.9, y0:1.0, y1:2.7 }] });
  addPlane(9, 4.2, basicMat(drawWindowView(1600, 760, 13)), X1 + 0.8, 1.9, -8.9, -Math.PI/2);
  const frame = stdMat(0xf4f1ea, 0.5);
  for (const zc of [-11.2, -8.9, -6.6]){
    addBox(0.1, 0.06, 1.5, frame, X1 - 0.03, 1.0, zc); addBox(0.1, 0.06, 1.5, frame, X1 - 0.03, 2.7, zc);
    addBox(0.1, 1.76, 0.06, frame, X1 - 0.03, 1.85, zc - 0.72); addBox(0.1, 1.76, 0.06, frame, X1 - 0.03, 1.85, zc + 0.72); addBox(0.08, 1.7, 0.04, frame, X1 - 0.03, 1.85, zc);
    addPool(2.2, 1.6, X1 - 1.3, 0.007, zc, 0.12, canvasPoolShape());
  }
  for (const zz of [Z0 + 0.02]) addBox(X1 - X0, 0.12, 0.04, stdMat(0x8a8478, 0.7), (X0 + X1) / 2, 0.06, zz);
  addBox(5.8, 2.2, 0.06, stdMat(0x5a3b22, 0.6), 19, 1.85, Z0 + 0.03);
  addPlane(5.6, 2.0, basicMat(drawChalkboard(), 0xe8e8e8), 19, 1.85, Z0 + 0.065, 0);
  addBox(5.6, 0.04, 0.12, stdMat(0x5a3b22, 0.6), 19, 0.83, Z0 + 0.1);
  const clock = new THREE.Mesh(new THREE.CircleGeometry(0.2, 32), basicMat(drawClock())); clock.position.set(19, 3.2, Z0 + 0.02); scene.add(clock);
  addBox(1.6, 0.74, 0.8, stdMat(0x6b4a2b, 0.5), 16.4, 0.37, -11.6);
  addBox(1.66, 0.04, 0.86, stdMat(0x8a6a48, 0.45), 16.4, 0.76, -11.6);
  addBox(0.4, 0.03, 0.3, stdMat(0xf4f1ea, 0.9), 16.1, 0.79, -11.6, 0.2);
  OBST.push({ x:16.4, z:-11.6, r:0.95 });
  addPlane(2.4, 1.6, basicMat(drawPaintPoster(), 0xeeeeee), X0 + 0.032, 1.85, -9.2, Math.PI/2);
  addBox(2.5, 1.7, 0.04, stdMat(0x1b1b1f, 0.5), X0 + 0.005, 1.85, -9.2, Math.PI/2);
  /* Easel: tap to start painting */
  const e = new THREE.Group(); e.position.set(15.6, 0, -6.4); e.rotation.y = 0.75;
  const ew = stdMat(0x8a6a48, 0.6), parts = [];
  for (const s of [-1, 1]){ const leg = addBox(0.04, 1.9, 0.04, ew, s * 0.32, 0.95, 0, 0, e); leg.rotation.z = -s * 0.1; parts.push(leg); }
  const back = addBox(0.04, 1.8, 0.04, ew, 0, 0.9, -0.32, 0, e); back.rotation.x = 0.18; parts.push(back);
  parts.push(addBox(0.84, 0.05, 0.08, ew, 0, 0.82, 0.03, 0, e));
  const board = addPlane(0.8, 0.6, basicMat(drawEaselCard()), 0, 1.18, 0.05, 0, e); board.rotation.x = -0.1; parts.push(board);
  for (const m of parts){ m.userData.paint = true; pickItems.push(m); }
  scene.add(e); EASEL = e;
  OBST.push({ x:15.6, z:-6.4, r:0.6 });
  const plat = new THREE.Mesh(new THREE.CylinderGeometry(0.9, 0.95, 0.08, 40), stdMat(0x2b2b30, 0.4, 0.2)); plat.position.set(21.6, 0.04, -10.2); scene.add(plat);
  const ringG = new THREE.Mesh(new THREE.TorusGeometry(0.92, 0.015, 6, 48), glowMatOf(0x8fd3ff)); ringG.rotation.x = Math.PI/2; ringG.position.set(21.6, 0.085, -10.2); scene.add(ringG);
  OBST.push({ x:21.6, z:-10.2, r:1.0 });
  addPlane(0.9, 0.2, basicMat(drawTableCard('SAMPLE SCULPTURE', 'Painted in the air'), 0xe9e3d8), 21.6, 0.3, -9.2, 0).rotation.x = -0.5;
  const lightMat = new THREE.MeshBasicMaterial({ color:0xfffaf0, toneMapped:false });
  for (const zc of [-10.8, -7.0]) addBox(1.2, 0.03, 0.5, lightMat, 19, H - 0.02, zc);
  const pl = new THREE.PointLight(0xfff3e2, 0.8, 18, 1.4); pl.position.set(19, 3.2, -9); scene.add(pl);
}
function drawEaselCard(){
  const W = 800, H = 600, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#14161c'; ctx.fillRect(0, 0, W, H);
  const cols = ['#ff5a8a', '#ffd166', '#5ee6c8', '#7aa8ff', '#c38bff'];
  ctx.lineCap = 'round'; ctx.lineWidth = 14;
  cols.forEach((col, i) => { ctx.strokeStyle = col; ctx.shadowColor = col; ctx.shadowBlur = 24; ctx.beginPath(); for (let t = 0; t <= 60; t++){ const x = 60 + t * 11, y = 180 + i * 40 + Math.sin(t * 0.18 + i) * 50; t ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.stroke(); });
  ctx.shadowBlur = 0; ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center'; ctx.font = '700 64px ' + F.ui; ctx.fillText('TAP TO PAINT', W/2, 470); ctx.fillText('IN 3D', W/2, 540);
  return c;
}
function drawPaintPoster(){
  const W = 1200, H = 800, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#101218'; ctx.fillRect(0, 0, W, H);
  const cols = ['#ff5a8a', '#ffd166', '#5ee6c8', '#7aa8ff'];
  ctx.lineCap = 'round';
  cols.forEach((col, i) => { ctx.strokeStyle = col; ctx.shadowColor = col; ctx.shadowBlur = 30; ctx.lineWidth = 10 + i * 3; ctx.beginPath(); for (let t = 0; t <= 120; t++){ const a = t * 0.09 + i, rr = 80 + t * 2.2; const x = W * 0.62 + Math.cos(a) * rr, y = H * 0.48 + Math.sin(a * 1.3) * rr * 0.6; t ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.stroke(); });
  ctx.shadowBlur = 0; ctx.fillStyle = '#ffffff'; ctx.textAlign = 'left'; ctx.font = '400 92px ' + F.display; ctx.fillText('Light,', 70, 220); ctx.fillText('ribbon,', 70, 320); ctx.fillText('space.', 70, 420);
  ctx.fillStyle = '#ffd166'; ctx.font = '400 30px ' + F.type; ctx.fillText('PAINT IN 3D · ROOM 101', 74, H - 80);
  return c;
}
