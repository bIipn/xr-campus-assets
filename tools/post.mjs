/* glTF post-process for the baked rooms: lightmap into the occlusion slot (texCoord 1), single-sided materials,
   dedup/prune/weld, then KTX2 + Meshopt through the gltf-transform CLI.
   node tools/post.mjs assets/lib lib  ->  assets/lib/lib.glb */
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, prune, weld, flatten } from '@gltf-transform/functions';

const [,, dir, name] = process.argv;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const doc = await io.read(path.join(dir, name + '_raw.gltf'));
const root = doc.getRoot();

/* lightmap texture -> emissive slot (texCoord 1) of every material used by a mesh that has TEXCOORD_1; the
   campus moves it to lightMap at load. (The occlusion slot would be compressed to one channel and lose the
   light's colour; the emissive slot stays RGB + sRGB.) meta.json "lmaps" names materials with their own file. */
const meta = fs.existsSync(path.join(dir, 'meta.json')) ? JSON.parse(fs.readFileSync(path.join(dir, 'meta.json'), 'utf8')) : {};
const lmTex = {};
const lmFor = (file) => lmTex[file] || (lmTex[file] = doc.createTexture(file.replace(/\.png$/, '')).setImage(fs.readFileSync(path.join(dir, file))).setMimeType('image/png'));
const lmMats = new Set();
for (const mesh of root.listMeshes()) for (const prim of mesh.listPrimitives()){
  if (prim.getAttribute('TEXCOORD_1')) lmMats.add(prim.getMaterial());
  else if (prim.getAttribute('COLOR_0')) prim.getMaterial().setExtras({ ...prim.getMaterial().getExtras(), vc:1 });
}
for (const m of lmMats){
  const file = (meta.lmaps || {})[m.getName()] || 'lightmap.png';
  m.setEmissiveTexture(lmFor(file)); m.getEmissiveTextureInfo().setTexCoord(1); m.setEmissiveFactor([0, 0, 0]);
  m.setExtras({ ...m.getExtras(), lm:1 });
  console.log('lightmap', m.getName(), '<-', file);
}
for (const m of root.listMaterials()) m.setDoubleSided(false);
/* the window glass is seen from both sides of the pane when you stand in the reveal */
for (const m of root.listMaterials()) if (m.getName() === 'glass') m.setDoubleSided(true);

await doc.transform(dedup(), prune(), flatten(), weld());
const mid = path.join(dir, name + '_mid.glb');
await io.write(mid, doc);
console.log('structure done:', root.listMeshes().length, 'meshes', root.listMaterials().length, 'materials', root.listTextures().length, 'textures');

const cli = path.join(path.dirname(new URL(import.meta.url).pathname), 'node_modules', '.bin', 'gltf-transform');
const env = { ...process.env, PATH:path.resolve('ktx/usr/bin') + ':' + process.env.PATH, LD_LIBRARY_PATH:path.resolve('ktx/usr/lib') };
const run = (args) => { console.log('>', args.join(' ')); execFileSync(cli, args, { stdio:'inherit', env }); };
const a = path.join(dir, name + '_a.glb'), b = path.join(dir, name + '_b.glb'), out = path.join(dir, name + '.glb');
/* lightmap + normals: UASTC keeps gradients clean; colour/roughness/emissive: ETC1S is a quarter of the size */
run(['uastc', mid, a, '--pattern', '{lightmap*,*_nrm*}', '--level', '2', '--rdo', '--rdo-lambda', '2', '--zstd', '18', '--verbose']);
run(['etc1s', a, b, '--slots', '{baseColorTexture,emissiveTexture,metallicRoughnessTexture}', '--quality', '160', '--verbose']);
run(['meshopt', b, out, '--level', 'medium']);
for (const f of [mid, a, b]) fs.rmSync(f, { force:true });
console.log('wrote', out, (fs.statSync(out).size / 1e6).toFixed(2), 'MB');
