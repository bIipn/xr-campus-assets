import fs from 'fs';
import * as THREE from 'three';
import { FBXLoader } from 'three/examples/jsm/loaders/FBXLoader.js';
THREE.TextureLoader.prototype.load = function (url) { const t = new THREE.Texture(); t.userData.url = url; return t; };
const origWarn = console.warn; console.warn = () => {};
const buf = fs.readFileSync(process.argv[2]);
const root = new FBXLoader().parse(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength), '');
root.updateMatrixWorld(true);
let mesh; root.traverse((o) => { if (o.isSkinnedMesh) mesh = o; });
console.log('mesh pos', mesh.position.toArray(), 'rot', mesh.rotation.toArray().slice(0,3).map(v=>v.toFixed(3)), 'scale', mesh.scale.toArray());
console.log('bindMatrix', mesh.bindMatrix.elements.map(v=>+v.toFixed(3)).join(','));
const sk = mesh.skeleton;
console.log('skeleton bones', sk.bones.length);
const B = new THREE.Matrix4(), p = new THREE.Vector3(), q = new THREE.Quaternion(), s = new THREE.Vector3();
for (const n of ['Bip01', 'Bip01_Pelvis', 'Bip01_Spine', 'Bip01_Head', 'Bip01_LEye', 'Bip01_L_Clavicle', 'Bip01_L_UpperArm', 'Bip01_L_Forearm', 'Bip01_L_Hand', 'Bip01_L_Finger1', 'Bip01_L_Finger12', 'Bip01_L_Thigh', 'Bip01_L_Calf', 'Bip01_L_Foot', 'Bip01_L_Toe0', 'Bip01_MJaw', 'Bip01_LEyeBlinkTop']){
  const i = sk.bones.findIndex((b) => b.name === n); if (i < 0){ console.log('missing', n); continue; }
  B.copy(sk.boneInverses[i]).invert(); B.decompose(p, q, s);
  const w = new THREE.Vector3(); sk.bones[i].getWorldPosition(w);
  console.log(n.padEnd(22), 'bind', p.toArray().map(v=>v.toFixed(2)).join(' '), ' scl', s.toArray().map(v=>v.toFixed(2)).join(' '), ' world', w.toArray().map(v=>v.toFixed(2)).join(' '));
}
const g = mesh.geometry, P = g.attributes.position, u = new THREE.Vector3(), mn = new THREE.Vector3(1e9,1e9,1e9), mx = new THREE.Vector3(-1e9,-1e9,-1e9);
for (let i = 0; i < P.count; i++){ u.fromBufferAttribute(P, i).applyMatrix4(mesh.bindMatrix); mn.min(u); mx.max(u); }
console.log('skinspace bbox', mn.toArray().map(v=>v.toFixed(1)), mx.toArray().map(v=>v.toFixed(1)));
// skin weight stats
const SI = g.attributes.skinIndex, SW = g.attributes.skinWeight; const used = new Set();
for (let i = 0; i < SI.count; i++) for (let k = 0; k < 4; k++) if (SW.getComponent(i, k) > 0) used.add(SI.getComponent(i, k));
console.log('bones used by weights', used.size, [...used].map((i) => sk.bones[i].name).filter(n=>!/Finger|Toe/.test(n)).join(' '));
