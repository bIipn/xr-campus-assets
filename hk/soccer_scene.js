/* Soccer pose test scene (not part of the app) */
const renderer = new THREE.WebGLRenderer({ antialias:true });
renderer.setSize(innerWidth, innerHeight); renderer.setPixelRatio(1);
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x9fb6c8);
const pm = new THREE.PMREMGenerator(renderer); scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture; scene.environmentIntensity = 0.4;
const camera = new THREE.PerspectiveCamera(40, innerWidth / innerHeight, 0.05, 100);
scene.add(new THREE.HemisphereLight(0xfff1e0, 0x3a4e28, 0.7));
const key = new THREE.DirectionalLight(0xffe2c4, 2.2); key.position.set(2.5, 6, 3.5); scene.add(key);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshStandardMaterial({ color:0x4f7a3a, roughness:0.9 })); floor.rotation.x = -Math.PI / 2; scene.add(floor);
const grid = new THREE.GridHelper(20, 20, 0x335522, 0x335522); grid.position.y = 0.002; scene.add(grid);

const figs = [];
const SC = SCENARIO;
function place(fig, x, z, yaw, roll, comY){
  const q = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), yaw || 0);
  if (roll) q.multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), roll));
  fig.root.quaternion.copy(q);
  if (comY != null){
    const pel = new THREE.Vector3(0, 0.895 * fig.S, 0).applyQuaternion(q);
    fig.root.position.set(x - pel.x, comY - pel.y, z - pel.z);
  } else fig.root.position.set(x, 0, z);
}
function applyDense(fig, d){
  hkPose(fig, d); hkFingers(fig, d[WR + 6], d[WR + 7], d[WR + 8], d[WR + 9]);
  fig.root.position.y += d[WR + 3] * fig.S;
}
const list = SC.poses;
const shots = [];
list.forEach((pp, i) => {
  const f = makeHuman({ av:pp.av, wax:false, height:pp.h || null, dye:pp.dye || null }); scene.add(f.root); figs.push(f);
  const x = i * 8;
  const lib = pp.lib === 'b' ? BSPEC : KSPEC;
  let d;
  if (pp.mix){ d = spBlend(new Float32Array(WAX_N), spD(lib, pp.mix[0], pp.side || 1), spD(lib, pp.mix[1], pp.side || 1), pp.mix[2]); }
  else d = new Float32Array(spD(lib, pp.p, pp.side || 1));
  if (pp.gait) spGait(d, pp.gait[0], pp.gait[1], pp.gait[2]);
  place(f, x, 0, pp.yaw == null ? 0 : pp.yaw, pp.roll || 0, pp.com);
  applyDense(f, d);
  if (pp.nohead) f.all[HB.Head].scale.setScalar(0.001);
  if (pp.ball){ f.root.updateMatrixWorld(true); const b = new THREE.Mesh(new THREE.SphereGeometry(0.11, 32, 16), new THREE.MeshStandardMaterial({ color:0xf0f0f0, roughness:0.5 })); b.position.set(x + pp.ball[0], pp.ball[1], pp.ball[2]); scene.add(b); f.ball = b; }
});
/* First-person shots: the camera sits at the eyes and looks down at the ball */
for (const v of SC.fp || []){
  shots.push(['fp_' + v.name, () => {
    const f = figs[v.fig], h = new THREE.Vector3(); f.root.updateMatrixWorld(true); f.all[HB.Neck].getWorldPosition(h);
    renderer.setViewport(0, 0, innerWidth, innerHeight); renderer.setScissorTest(false);
    figs.forEach((g, j) => { g.root.visible = j === v.fig; });
    camera.fov = v.fov || 66; camera.aspect = innerWidth / innerHeight;
    camera.position.set(h.x, h.y + (v.up || 0.16), h.z + (v.fwd || 0.12));
    camera.rotation.set(v.pitch, Math.PI, 0, 'YXZ'); camera.updateProjectionMatrix();
    renderer.render(scene, camera);
  }]);
}
/* A contact sheet: every pose from the front (top row) and the side (bottom row) */
shots.push(['sheet', () => {
  const W = innerWidth, H = innerHeight, n = figs.length, cw = Math.floor(W / n), ch = Math.floor(H / 2);
  renderer.setScissorTest(true); renderer.setClearColor(0x9fb6c8);
  figs.forEach((f, i) => {
    figs.forEach((g, j) => { g.root.visible = i === j; });
    const pp = list[i], c = new THREE.Vector3(); f.all[HB.Pelvis].getWorldPosition(c);
    const cy = pp.com != null ? c.y : 0.85;
    for (const row of [0, 1]){
      camera.fov = 34; camera.aspect = cw / ch;
      const yaw = (pp.yaw || 0) + (row ? Math.PI / 2 : 0) + (SC.camYaw || 0), dist = 5.2;
      camera.position.set(c.x + Math.sin(yaw) * dist, cy + 0.35, c.z + Math.cos(yaw) * dist);
      camera.lookAt(c.x, cy, c.z); camera.updateProjectionMatrix();
      renderer.setViewport(i * cw, (1 - row) * ch, cw, ch); renderer.setScissor(i * cw, (1 - row) * ch, cw, ch);
      renderer.render(scene, camera);
    }
  });
  renderer.setScissorTest(false); figs.forEach((g) => { g.root.visible = true; });
}]);
window.__shot = (i) => { shots[i][1](); };
window.__info = () => figs.map((f) => { f.root.updateMatrixWorld(true); const g = (n) => { const v = new THREE.Vector3(); f.all[HB[n]].getWorldPosition(v); return [+v.x.toFixed(3), +v.y.toFixed(3), +v.z.toFixed(3)]; }; return { foot:g('R_Foot'), toe:g('R_Toe0'), lfoot:g('L_Foot'), ltoe:g('L_Toe0'), hand:g('R_Hand'), lhand:g('L_Hand'), head:g('Head'), pelvis:g('Pelvis') }; });
Promise.all([...new Set(list.map((p) => p.av))].map((id) => hkAsset(id))).then(() => setTimeout(() => {
  for (const f of figs) f.root.updateMatrixWorld(true);
  window.__shots = shots.map((s) => s[0]);
}, 200)).catch((e) => { console.error('load failed', e && e.stack); window.__shots = []; });
