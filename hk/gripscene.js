/* Grip / IK test scene (not part of the app): figures holding props with real hand contact */
const renderer = new THREE.WebGLRenderer({ antialias:true });
renderer.setSize(innerWidth, innerHeight); renderer.setPixelRatio(1);
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x9fb6c8);
const pm = new THREE.PMREMGenerator(renderer); scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture; scene.environmentIntensity = 0.45;
const camera = new THREE.PerspectiveCamera(30, innerWidth / innerHeight, 0.03, 100);
scene.add(new THREE.HemisphereLight(0xfff1e0, 0x3a4e28, 0.7));
const key = new THREE.DirectionalLight(0xffe2c4, 2.2); key.position.set(2.5, 6, 3.5); scene.add(key);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.MeshStandardMaterial({ color:0x6a5a4a, roughness:0.9 })); floor.rotation.x = -Math.PI / 2; scene.add(floor);
const SC = SCENARIO, cases = [];
const M = (hex, r, m) => new THREE.MeshStandardMaterial({ color:hex, roughness:r == null ? 0.6 : r, metalness:m || 0 });
function propOf(kind){
  const g = new THREE.Group();
  const add = (geo, mat, x, y, z) => { const o = new THREE.Mesh(geo, mat); o.position.set(x || 0, y || 0, z || 0); g.add(o); return o; };
  if (kind === 'box') add(new THREE.BoxGeometry(0.46, 0.34, 0.38), M(0xb08a5a, 0.9));
  else if (kind === 'clip'){ add(new THREE.BoxGeometry(0.22, 0.3, 0.012), M(0xb08a5a, 0.9)); add(new THREE.BoxGeometry(0.2, 0.26, 0.004), M(0xeeebe4, 0.5), 0, -0.01, 0.008); add(new THREE.BoxGeometry(0.08, 0.025, 0.02), M(0xb9c0c6, 0.3, 0.7), 0, 0.14, 0.01); }
  else if (kind === 'tablet'){ add(new THREE.BoxGeometry(0.24, 0.17, 0.012), M(0x1c1e21, 0.4)); add(new THREE.PlaneGeometry(0.21, 0.14), new THREE.MeshBasicMaterial({ color:0x3b6ea8 }), 0, 0, 0.0065); }
  else if (kind === 'phone'){ add(new THREE.BoxGeometry(0.075, 0.15, 0.01), M(0x1c1e21, 0.4)); add(new THREE.PlaneGeometry(0.065, 0.13), new THREE.MeshBasicMaterial({ color:0x2a9d8f }), 0, 0, 0.0055); }
  else if (kind === 'book'){ add(new THREE.BoxGeometry(0.26, 0.34, 0.012), M(0x2a9d8f, 0.6), -0.13, 0, 0); add(new THREE.BoxGeometry(0.26, 0.34, 0.012), M(0x2a9d8f, 0.6), 0.13, 0, 0); add(new THREE.PlaneGeometry(0.5, 0.32), M(0xf7f1e3, 0.85), 0, 0, 0.007); }
  else if (kind === 'headset'){ add(new THREE.BoxGeometry(0.19, 0.108, 0.1), M(0xeceae6, 0.38)); add(new THREE.BoxGeometry(0.168, 0.086, 0.012), M(0x1d2024, 0.32), 0, 0, 0.05); }
  else if (kind === 'sieve'){ const s = add(new THREE.CylinderGeometry(0.102, 0.102, 0.05, 36), M(0xc9a65a, 0.32, 0.8)); }
  scene.add(g);
  return g;
}
SC.cases.forEach((c, i) => {
  const f = makeHuman({ av:c.av, wax:false, height:c.h || null });
  scene.add(f.root);
  const x = i * 3;
  f.root.position.set(x, 0, 0); f.root.rotation.y = c.yaw || 0;
  const d = waxKeyDense({ p:c.pose || 'ease' });
  const prop = c.prop ? propOf(c.prop) : null;
  cases.push({ c, f, d, prop, x });
});
const _m = new THREE.Matrix4(), _q = new THREE.Quaternion(), _p = new THREE.Vector3(), _e = new THREE.Euler();
function solve(){
  for (const k of cases){
    const { c, f, d, prop } = k;
    hkPose(f, d); hkFingers(f, d[WR + 6], d[WR + 7], d[WR + 8], d[WR + 9]);
    f.root.position.y = d[WR + 3] * f.S;
    f.root.updateMatrixWorld(true);
    if (!prop) continue;
    if (c.anchor){
      /* prop sits in a palm */
      hkAnchorMatrix(f, c.anchor, c.grips[c.agrip], _m);
    } else {
      const bone = f.all[HB[c.bone || 'Spine2']];
      _e.set((c.r || [0, 0, 0])[0], (c.r || [0, 0, 0])[1], (c.r || [0, 0, 0])[2]);
      _m.compose(_p.fromArray(c.p).multiplyScalar(f.S), _q.setFromEuler(_e), new THREE.Vector3(1, 1, 1));
      _m.premultiply(bone.matrixWorld);
    }
    prop.matrixAutoUpdate = false; prop.matrix.copy(_m); prop.matrixWorldNeedsUpdate = true;
    for (const [s, gname] of c.hands || []){
      const g = c.grips[gname];
      hkGrip(f, s, _m, g, 1);
      hkFingers(f, s === 'L' ? g.curl : f.grip[0], s === 'R' ? g.curl : f.grip[1], 0, 0);
    }
  }
}
const shots = [];
shots.push(['sheet', () => {
  const W = innerWidth, H = innerHeight, n = cases.length, cw = Math.floor(W / n), ch = Math.floor(H / 2);
  renderer.setScissorTest(true);
  cases.forEach((k, i) => {
    cases.forEach((o, j) => { o.f.root.visible = i === j; if (o.prop) o.prop.visible = i === j; });
    for (const row of [0, 1]){
      const yaw = (k.c.yaw || 0) + (row ? (k.c.side || Math.PI / 2) : (k.c.front || 0.35)), dist = k.c.dist || 2.2, cy = k.c.cy || 1.15;
      camera.fov = 30; camera.aspect = cw / ch;
      camera.position.set(k.x + Math.sin(yaw) * dist, cy + 0.25, Math.cos(yaw) * dist);
      camera.lookAt(k.x, cy, 0); camera.updateProjectionMatrix();
      renderer.setViewport(i * cw, (1 - row) * ch, cw, ch); renderer.setScissor(i * cw, (1 - row) * ch, cw, ch);
      renderer.render(scene, camera);
    }
  });
  renderer.setScissorTest(false);
}]);
window.__shot = (i) => { shots[i][1](); };
Promise.all([...new Set(SC.cases.map((c) => c.av))].map((id) => hkAsset(id))).then(() => setTimeout(() => {
  solve();
  window.__shots = shots.map((s) => s[0]);
}, 300)).catch((e) => { console.error('load failed', e && e.stack); window.__shots = []; });
