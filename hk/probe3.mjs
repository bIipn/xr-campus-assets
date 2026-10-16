import fs from 'fs';
import * as THREE from 'three';
import { FBXLoader } from 'three/examples/jsm/loaders/FBXLoader.js';
console.warn = () => {};
for (const rel of process.argv.slice(2)){
  const name = rel.split('/')[1], p = '../mh/cache/Assets/Avatars/' + rel + '/Export/' + name + '.fbx';
  const buf = fs.readFileSync(fs.existsSync(p) ? p : '../mh/rb/Assets/Avatars/' + rel + '/Export/' + name + '.fbx');
  const mgr = new THREE.LoadingManager(); mgr.addHandler(/\.(tga|dds|psd|tif+)$/i, { setPath(){ return this; }, load(url){ const t = new THREE.Texture(); t.userData.url = url; return t; } });
  const root = new FBXLoader(mgr).parse(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength), '');
  let meshes = []; root.traverse((o) => { if (o.isMesh) meshes.push(o); });
  console.log('==', rel, 'meshes', meshes.length);
  for (const m of meshes){
    const mats = Array.isArray(m.material) ? m.material : [m.material];
    console.log('  mesh', m.name, m.isSkinnedMesh, 'bones', m.skeleton && m.skeleton.bones.length, 'groups', m.geometry.groups.length);
    for (const mt of mats) console.log('    mat', mt.name, '|', mt.map && mt.map.userData.url && mt.map.userData.url.split(/[\\/]/).pop(), '|', mt.alphaMap && mt.alphaMap.userData.url && mt.alphaMap.userData.url.split(/[\\/]/).pop(), mt.transparent);
    if (m.skeleton && /mc02|Male_Child_02/.test(rel)) console.log('    bones:', m.skeleton.bones.map(b=>b.name).join(' '));
  }
}
