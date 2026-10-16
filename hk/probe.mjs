import fs from 'fs';
import * as THREE from 'three';
import { FBXLoader } from 'three/examples/jsm/loaders/FBXLoader.js';
// Stub texture loading in Node
THREE.TextureLoader.prototype.load = function (url) { const t = new THREE.Texture(); t.userData.url = url; return t; };
const file = process.argv[2];
const buf = fs.readFileSync(file);
const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
const root = new FBXLoader().parse(ab, '');
let bones = [], meshes = [];
root.traverse((o) => { if (o.isBone) bones.push(o); if (o.isMesh) meshes.push(o); });
root.updateMatrixWorld(true);
console.log('bones', bones.length);
console.log(bones.map((b) => b.name).join(' | '));
for (const m of meshes){
  const g = m.geometry;
  console.log('MESH', m.name, m.isSkinnedMesh, 'verts', g.attributes.position.count, 'tris', (g.index ? g.index.count : g.attributes.position.count) / 3, 'attrs', Object.keys(g.attributes).join(','), 'groups', g.groups.length, 'morphs', g.morphAttributes.position ? g.morphAttributes.position.length : 0);
  const mats = Array.isArray(m.material) ? m.material : [m.material];
  for (const mt of mats) console.log('  mat', mt.name, mt.type, mt.map && mt.map.userData.url, mt.normalMap && mt.normalMap.userData.url, mt.alphaMap && mt.alphaMap.userData.url, 'transparent', mt.transparent);
  if (g.morphAttributes.position) console.log('  morph names', Object.keys(m.morphTargetDictionary || {}).slice(0, 80).join(','));
  g.computeBoundingBox(); console.log('  bbox', g.boundingBox.min.toArray().map(v=>v.toFixed(3)), g.boundingBox.max.toArray().map(v=>v.toFixed(3)));
  console.log('  groups', JSON.stringify(g.groups));
}
const wp = new THREE.Vector3();
for (const n of ['Bip01', 'Bip01 Pelvis', 'Bip01 Head', 'Bip01 L UpperArm', 'Bip01 L Forearm', 'Bip01 L Hand', 'Bip01 L Thigh', 'Bip01 L Foot', 'Bip01 L Finger1']){ const b = bones.find((x) => x.name === n); if (b){ b.getWorldPosition(wp); console.log(n, wp.toArray().map(v=>v.toFixed(3))); } }
console.log('root scale', root.scale.toArray(), 'children', root.children.map(c=>c.type+':'+c.name).join(', '));
