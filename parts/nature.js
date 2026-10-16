/* ================================================================
   Nature: wind-blown grass that follows the camera, leafy trees
   ================================================================ */
const NATURE = { grass:null, gU:null, leafU:null };
const WIND = { time:{ value:0 }, cam:{ value:null } };
const GRASS_RECT = { x0:27, z0:-40, w:74, h:72, ppm:4 };

function canvasLeaves(){
  const S = 256, c = mk(S, S), ctx = c.getContext('2d'), r = rnd(61);
  const greens = ['#3f7a2e', '#4f8c34', '#5f9c3c', '#3a6b2a', '#6aa845', '#2f5e24', '#78b04c'];
  for (let i = 0; i < 230; i++){
    const a = r() * Math.PI * 2, rad = Math.sqrt(r()) * S * 0.42, x = S / 2 + Math.cos(a) * rad, y = S / 2 + Math.sin(a) * rad * 0.92;
    const len = 9 + r() * 12, wid = len * (0.42 + r() * 0.15);
    ctx.save(); ctx.translate(x, y); ctx.rotate(r() * Math.PI * 2);
    ctx.fillStyle = greens[Math.floor(r() * greens.length)];
    ctx.beginPath(); ctx.ellipse(0, 0, len / 2, wid / 2, 0, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = 'rgba(20,40,12,0.35)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(-len / 2, 0); ctx.lineTo(len / 2, 0); ctx.stroke();
    if (r() < 0.35){ ctx.fillStyle = 'rgba(200,235,140,0.32)'; ctx.beginPath(); ctx.ellipse(-len * 0.1, -wid * 0.12, len * 0.28, wid * 0.22, 0, 0, Math.PI * 2); ctx.fill(); }
    ctx.restore();
  }
  return c;
}
function canvasBark(){
  const W = 128, H = 256, c = mk(W, H), ctx = c.getContext('2d'), r = rnd(77);
  ctx.fillStyle = '#5a4130'; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 90; i++){
    const x = r() * W, w = 1.5 + r() * 4, l = 30 + r() * 120, y = r() * H;
    ctx.fillStyle = r() < 0.5 ? 'rgba(40,28,20,0.55)' : 'rgba(120,96,74,0.35)';
    for (const dx of [-W, 0, W]) for (const dy of [-H, 0, H]) ctx.fillRect(x + dx, y + dy, w, l);
  }
  return c;
}

/* ---------- Trees: a bark trunk, a dense core and a shell of leaf cards ---------- */
function leafShellGeometry(n){
  const r = rnd(5150), pos = [], nrm = [], uv = [], idx = [];
  const v = new THREE.Vector3(), a = new THREE.Vector3(), b = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0);
  for (let i = 0; i < n; i++){
    const u = r() * 2 - 1, t = r() * Math.PI * 2, s = Math.sqrt(1 - u * u), rad = 0.62 + r() * 0.38;
    const c = new THREE.Vector3(s * Math.cos(t), u * 0.85 + 0.05, s * Math.sin(t)).multiplyScalar(rad);
    const nn = c.clone().normalize();
    a.crossVectors(nn, Math.abs(nn.y) > 0.9 ? new THREE.Vector3(1, 0, 0) : up).normalize();
    b.crossVectors(nn, a).normalize();
    const rot = r() * Math.PI * 2, ca = Math.cos(rot), sa = Math.sin(rot), size = 0.62 + r() * 0.3;
    const ax = a.clone().multiplyScalar(ca).addScaledVector(b, sa).multiplyScalar(size), bx = b.clone().multiplyScalar(ca).addScaledVector(a, -sa).multiplyScalar(size);
    const base = pos.length / 3;
    for (const [sx, sy, tu, tv] of [[-1, -1, 0, 0], [1, -1, 1, 0], [1, 1, 1, 1], [-1, 1, 0, 1]]){
      v.copy(c).addScaledVector(ax, sx).addScaledVector(bx, sy);
      pos.push(v.x, v.y, v.z);
      const vn = v.clone().normalize().lerp(nn, 0.35).normalize(); nrm.push(vn.x, vn.y, vn.z);
      uv.push(tu, tv);
    }
    idx.push(base, base + 1, base + 2, base, base + 2, base + 3);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  return g;
}
function windTweak(mat, key, amp){
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.uWindTime = WIND.time;
    sh.vertexShader = 'uniform float uWindTime;\n' + sh.vertexShader.replace('#include <begin_vertex>',
      '#include <begin_vertex>\n#ifdef USE_INSTANCING\nvec3 wp = instanceMatrix[3].xyz;\n#else\nvec3 wp = vec3(0.0);\n#endif\n' +
      'float wk = max(position.y + 0.6, 0.0) * ' + amp.toFixed(3) + ';\n' +
      'transformed.x += (sin(uWindTime * 1.35 + wp.x * 0.37 + wp.z * 0.21) + 0.45 * sin(uWindTime * 2.9 + position.x * 3.1 + wp.z)) * wk;\n' +
      'transformed.z += (cos(uWindTime * 1.1 + wp.z * 0.33) * 0.6 + 0.35 * sin(uWindTime * 3.3 + position.z * 2.7 + wp.x)) * wk;');
  };
  mat.customProgramCacheKey = () => key;
  return mat;
}
function buildTreeMeshes(T, C){
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), p = new THREE.Vector3(), sc = new THREE.Vector3(), col = new THREE.Color();
  const barkMat = new THREE.MeshStandardMaterial({ map:repTex(canvasBark(), 1, 1), color:0xb59a82, roughness:0.95 });
  const trunkGeo = new THREE.CylinderGeometry(0.1, 0.17, 1, 9, 3); const tp = trunkGeo.attributes.position;
  for (let i = 0; i < tp.count; i++){ const y = tp.getY(i); tp.setX(i, tp.getX(i) + Math.sin(y * 3.1) * 0.03); tp.setZ(i, tp.getZ(i) + Math.cos(y * 2.3) * 0.025); }
  trunkGeo.computeVertexNormals();
  const trunks = new THREE.InstancedMesh(trunkGeo, barkMat, T.length);
  T.forEach((t, i) => { p.set(t[0], t[1], t[2]); sc.set(t[3], t[4], t[3]); e.set(0, i * 1.7, 0); q.setFromEuler(e); m4.compose(p, q, sc); trunks.setMatrixAt(i, m4); });
  const coreMat = windTweak(new THREE.MeshStandardMaterial({ roughness:0.9, color:0xffffff }), 'tree-core', 0.025);
  const core = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(0.8, 1), coreMat, C.length);
  const leafMat = windTweak(new THREE.MeshStandardMaterial({ map:tex(canvasLeaves()), alphaTest:0.42, side:THREE.DoubleSide, roughness:0.72, color:0xffffff }), 'tree-leaf', 0.04);
  const shell = new THREE.InstancedMesh(leafShellGeometry(Q().leaves), leafMat, C.length);
  C.forEach((cc, i) => {
    p.set(cc[0], cc[1], cc[2]); sc.set(cc[3], cc[4], cc[3]); e.set(0, cc[6], 0); q.setFromEuler(e); m4.compose(p, q, sc);
    core.setMatrixAt(i, m4); shell.setMatrixAt(i, m4);
    col.set(cc[5]); core.setColorAt(i, col.clone().multiplyScalar(0.55)); shell.setColorAt(i, col.lerp(new THREE.Color(0xffffff), 0.35));
  });
  for (const mesh of [trunks, core, shell]){ mesh.instanceMatrix.needsUpdate = true; if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true; }
  instBounds(trunks, T, 4); instBounds(core, C, 6); instBounds(shell, C, 7);
  trunks.castShadow = core.castShadow = shell.castShadow = true;
  trunks.receiveShadow = core.receiveShadow = shell.receiveShadow = true;
  scene.add(trunks); scene.add(core); scene.add(shell);
}

/* ---------- Grass ---------- */
function grassMaskCanvas(){
  const R = GRASS_RECT, k = R.ppm, c = mk(R.w * k, R.h * k), ctx = c.getContext('2d');
  const X = (x) => (x - R.x0) * k, Z = (z) => (z - R.z0) * k;
  ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, c.width, c.height);
  /* Mowed lawn (grey = short grass) where the balls and blocks live */
  ctx.fillStyle = '#666';
  ctx.fillRect((70.5 - R.x0) * k, (-8.4 - R.z0) * k, 21 * k, 14.6 * k);
  ctx.beginPath(); ctx.arc((64.5 - R.x0) * k, (1.5 - R.z0) * k, 3.4 * k, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#000'; ctx.strokeStyle = '#000'; ctx.lineCap = 'butt';
  const rect = (x0, z0, x1, z1) => ctx.fillRect(X(x0), Z(z0), (x1 - x0) * k, (z1 - z0) * k);
  const circ = (x, z, rad) => { ctx.beginPath(); ctx.arc(X(x), Z(z), rad * k, 0, Math.PI * 2); ctx.fill(); };
  const strip = (x0, z0, x1, z1, w) => { ctx.lineWidth = (w + 0.25) * k; ctx.beginPath(); ctx.moveTo(X(x0), Z(z0)); ctx.lineTo(X(x1), Z(z1)); ctx.stroke(); };
  rect(-50, -60, 34.25, 60);
  strip(33.6, -3, 46.4, -3, 2.4); circ(52, -1.5, 7.05); strip(52, -6.8, 52, -9.6, 3.2); strip(57.3, 1.1, 73.7, 10.5, 2.2); strip(52.7, 4.3, 54.1, 11.4, 2.2); strip(41.2, -2.2, 41.2, 10.5, 2.0);
  rect(35.3, 9.8, 46.3, 24.2); rect(42.7, -13.8, 59.1, -8.2);
  circ(54, 16, 4.6); rect(52.4, 9.6, 55.6, 12.6); circ(78, 13, 2.75); circ(66.5, 20, 1.75);
  return c;
}
function grassGeometry(){
  const g = new THREE.BufferGeometry(), W = 0.075, L = [0, 0.36, 0.7];
  const pos = [], uv = [], nrm = [];
  for (const y of L){ const w = W * (1 - y * 0.78); pos.push(-w / 2, y, 0, w / 2, y, 0); uv.push(0, y, 1, y); nrm.push(0, 0, 1, 0, 0, 1); }
  pos.push(0, 1, 0); uv.push(0.5, 1); nrm.push(0, 0, 1);
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  g.setIndex([0, 1, 2, 2, 1, 3, 2, 3, 4, 4, 3, 5, 4, 5, 6]);
  return g;
}
function buildGrass(){
  const N = QUALITY.high.grass, r = rnd(4242), geo = grassGeometry(), blade = new Float32Array(N * 4);
  for (let i = 0; i < N; i++){ blade[i * 4] = r(); blade[i * 4 + 1] = r(); blade[i * 4 + 2] = r() * Math.PI * 2; blade[i * 4 + 3] = 0.22 + r() * r() * 0.42 + r() * 0.12; }
  geo.setAttribute('aBlade', new THREE.InstancedBufferAttribute(blade, 4));
  const mask = new THREE.CanvasTexture(grassMaskCanvas()); mask.colorSpace = THREE.NoColorSpace; mask.flipY = false;
  WIND.cam.value = new THREE.Vector3();
  const U = NATURE.gU = { uPatch:{ value:Q().patch }, uMask:{ value:mask }, uMaskRect:{ value:new THREE.Vector4(GRASS_RECT.x0, GRASS_RECT.z0, GRASS_RECT.w, GRASS_RECT.h) },
    uBaseCol:{ value:new THREE.Color(0x2d5a1c) }, uTipCol:{ value:new THREE.Color(0x9cc65a) } };
  const mat = new THREE.MeshStandardMaterial({ color:0xffffff, roughness:0.85, side:THREE.DoubleSide });
  mat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, U, { uWindTime:WIND.time, uCam:WIND.cam });
    sh.vertexShader = 'uniform float uWindTime; uniform vec3 uCam; uniform float uPatch; uniform sampler2D uMask; uniform vec4 uMaskRect;\nattribute vec4 aBlade;\nvarying float vTip; varying float vVar;\n' +
      sh.vertexShader.replace('#include <beginnormal_vertex>', '#include <beginnormal_vertex>\nobjectNormal = vec3(0.0, 1.0, 0.0);')
      .replace('#include <begin_vertex>', `#include <begin_vertex>
vec2 rel = mod(aBlade.xy * uPatch - uCam.xz + 0.5 * uPatch, uPatch) - 0.5 * uPatch;
vec2 gbase = uCam.xz + rel;
float msk = texture2D(uMask, (gbase - uMaskRect.xy) / uMaskRect.zw).r;
float fade = 1.0 - smoothstep(uPatch * 0.3, uPatch * 0.5, length(rel));
float hgt = aBlade.w * smoothstep(0.1, 1.0, msk) * fade;
float ca = cos(aBlade.z), sa = sin(aBlade.z), tip = position.y;
float bend = (sin(uWindTime * 1.6 + gbase.x * 0.31 + gbase.y * 0.2) * 0.55 + sin(uWindTime * 2.8 + gbase.x * 0.9 - gbase.y * 0.47) * 0.25 + 0.45);
vec3 q = vec3(position.x * ca, position.y * hgt, position.x * sa);
q.x += bend * tip * tip * hgt * 0.5; q.z += bend * tip * tip * hgt * 0.22;
transformed = vec3(gbase.x, 0.0, gbase.y) + q;
vTip = tip; vVar = fract(sin(dot(aBlade.xy, vec2(12.9898, 78.233))) * 43758.5453);`);
    sh.fragmentShader = 'uniform vec3 uBaseCol; uniform vec3 uTipCol;\nvarying float vTip; varying float vVar;\n' +
      sh.fragmentShader.replace('#include <color_fragment>', '#include <color_fragment>\ndiffuseColor.rgb *= mix(uBaseCol, uTipCol, vTip) * (0.78 + 0.42 * vVar);')
      .replace('#include <normal_fragment_begin>', '#include <normal_fragment_begin>\nnormal = normalize(vNormal);');
  };
  mat.customProgramCacheKey = () => 'grass-v1';
  const mesh = new THREE.InstancedMesh(geo, mat, N);
  mesh.count = Q().grass; mesh.frustumCulled = false; mesh.receiveShadow = true; mesh.castShadow = false;
  mesh.userData.noMerge = true;
  NATURE.grass = mesh; scene.add(mesh);
  return mesh;
}
function natureTier(){
  if (NATURE.grass){ NATURE.grass.count = Q().grass; NATURE.gU.uPatch.value = Q().patch; }
}
function natureFrame(){
  WIND.time.value = REDUCED ? 0 : GFX.t;
  if (WIND.cam.value) WIND.cam.value.copy(camera.position);
}
