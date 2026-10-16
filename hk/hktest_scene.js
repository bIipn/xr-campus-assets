/* Test scene for realistic people (not part of the app) */
const renderer = new THREE.WebGLRenderer({ antialias:true });
renderer.setSize(innerWidth, innerHeight); renderer.setPixelRatio(1);
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x2a2522);
const pm = new THREE.PMREMGenerator(renderer); scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture; scene.environmentIntensity = 0.35;
const camera = new THREE.PerspectiveCamera(40, innerWidth / innerHeight, 0.05, 100);
scene.add(new THREE.HemisphereLight(0xfff1e0, 0x3a2e28, 0.5));
const key = new THREE.DirectionalLight(0xffe2c4, 2.2); key.position.set(2.5, 4, 3.5); scene.add(key);
const rim = new THREE.DirectionalLight(0xbcd4ff, 1.1); rim.position.set(-3, 3, -3); scene.add(rim);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(30, 30), new THREE.MeshStandardMaterial({ color:0x5a4636, roughness:0.8 })); floor.rotation.x = -Math.PI / 2; scene.add(floor);

const figs = [];
function pose(fig, p, extra){
  const d = waxKeyDense(Object.assign({ p }, extra || {}));
  for (let i = 0; i < 17; i++) fig.bones[i].rotation.set(d[i * 3], d[i * 3 + 1], d[i * 3 + 2]);
  fig.root.position.y = d[WR + 3] * fig.S;
}
const ids = SCENARIO.ids;
if (SCENARIO.name === 'basic'){
  const id = ids[0];
  ['ease', 'wave', 'point', 'clap', 'hold'].forEach((p, i) => {
    const f = makeHuman({ av:id, wax:true }); f.root.position.x = (i - 2) * 0.95; scene.add(f.root); pose(f, p); figs.push(f);
    if (p === 'hold') hkFingers(f, 1, 1);
  });
} else {
  ids.forEach((id, i) => { const f = makeHuman({ av:id, wax:false }); f.root.position.x = (i - (ids.length - 1) / 2) * 0.8; scene.add(f.root); pose(f, 'ease'); figs.push(f); });
}
const shots = [];
const full = () => { const w = Math.max(5, figs.length * (SCENARIO.name === 'basic' ? 0.95 : 0.8)); camera.fov = 32; camera.position.set(0, 1.0, w * 1.2); camera.lookAt(0, 0.9, 0); camera.updateProjectionMatrix(); };
shots.push(['full', () => { full(); }]);
shots.push(['face', () => { const f = figs[0], e = f.R.eyeMid.clone().multiplyScalar(f.S).add(f.root.position); camera.fov = 22; camera.position.set(e.x + 0.12, e.y + 0.02, e.z + 0.55); camera.lookAt(e.x, e.y - 0.03, e.z); camera.updateProjectionMatrix(); }]);
shots.push(['blink', () => { const f = figs[0]; f.blink = 1; f.talk = 1; f.smile = 0; hkFace(f); const e = f.R.eyeMid.clone().multiplyScalar(f.S).add(f.root.position); camera.fov = 22; camera.position.set(e.x + 0.12, e.y + 0.02, e.z + 0.55); camera.lookAt(e.x, e.y - 0.03, e.z); camera.updateProjectionMatrix(); }]);
shots.push(['hands', () => { const f = figs[figs.length - 1], h = new THREE.Vector3(); f.all[HB.R_Hand].getWorldPosition(h); camera.fov = 30; camera.position.set(h.x + 0.3, h.y + 0.1, h.z + 0.5); camera.lookAt(h.x, h.y - 0.05, h.z); camera.updateProjectionMatrix(); }]);
shots.push(['side', () => { camera.fov = 32; camera.position.set(6, 1.1, 1.5); camera.lookAt(0, 0.9, 0); camera.updateProjectionMatrix(); }]);
window.__shot = (i) => { shots[i][1](); renderer.render(scene, camera); };
/* Wait for every avatar to load, then announce the shot list */
Promise.all(ids.map((id) => hkAsset(id))).then(() => setTimeout(() => {
  for (const f of figs) f.root.updateMatrixWorld(true);
  window.__shots = shots.map((s) => s[0]);
}, 200)).catch((e) => { console.error('load failed', e && e.stack); window.__shots = []; });
