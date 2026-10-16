/* HumanKit asset build.
   Pulls Microsoft Rocketbox avatars (MIT License, (c) 2020 Microsoft) from GitHub at a pinned
   commit, converts each rigged FBX into a compact mesh (meshopt-encoded) and downsized WebP
   textures, and writes one container per avatar per quality tier plus the rig data the app
   embeds. Runs locally and on Vercel's build machines (Node only).
   Usage: node build.mjs <outDir> [--rig <rig.json>] [--only id,id] [--src <local repo root>] */
import fs from 'fs';
import path from 'path';
import * as THREE from 'three';
import { FBXLoader } from 'three/examples/jsm/loaders/FBXLoader.js';
import sharp from 'sharp';
import { MeshoptEncoder } from 'meshoptimizer';

const COMMIT = '0943055db6ec570bcef9f2c8b41c9e5467c808f9';
const RAW = 'https://raw.githubusercontent.com/microsoft/Microsoft-Rocketbox/' + COMMIT + '/';
/* jsDelivr mirrors the same commit: the fallback when GitHub rate-limits a shared build machine */
const MIRROR = 'https://cdn.jsdelivr.net/gh/microsoft/Microsoft-Rocketbox@' + COMMIT + '/';
export const AVATARS = {
  fa01:'Adults/Female_Adult_01', fa03:'Adults/Female_Adult_03', fa05:'Adults/Female_Adult_05', fa06:'Adults/Female_Adult_06', fa07:'Adults/Female_Adult_07',
  fa08:'Adults/Female_Adult_08', fa09:'Adults/Female_Adult_09', fa11:'Adults/Female_Adult_11', fa12:'Adults/Female_Adult_12', fa14:'Adults/Female_Adult_14',
  fa15:'Adults/Female_Adult_15', fa17:'Adults/Female_Adult_17', fp02:'Adults/Female_Party_02',
  ma02:'Adults/Male_Adult_02', ma04:'Adults/Male_Adult_04', ma05:'Adults/Male_Adult_05', ma06:'Adults/Male_Adult_06', ma07:'Adults/Male_Adult_07',
  ma09:'Adults/Male_Adult_09', ma12:'Adults/Male_Adult_12', ma14:'Adults/Male_Adult_14', ma16:'Adults/Male_Adult_16',
  ma17:'Adults/Male_Adult_17', ma18:'Adults/Male_Adult_18', ma20:'Adults/Male_Adult_20',
  fc01:'Children/Female_Child_01', fc02:'Children/Female_Child_02', mc01:'Children/Male_Child_01', mc02:'Children/Male_Child_02',
  bf02:'Professions/Business_Female_02', bf03:'Professions/Business_Female_03', bm05:'Professions/Business_Male_05',
  mf01:'Professions/Medical_Female_01', mm03:'Professions/Medical_Male_03', mm04:'Professions/Medical_Male_04',
  gm01:'Professions/Gardener_Male_01', sf02:'Professions/Sports_Female_02', sm02:'Professions/Sports_Male_02', sm04:'Professions/Sports_Male_04'
};
/* Texture sizes per tier: [head, body, hair, normal] */
const TIERS = { lo:[512, 512, 256, 256], hi:[1024, 1024, 512, 512] };

const args = process.argv.slice(2);
const OUT = args[0] || 'dist/h';
const opt = (k) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : null; };
const RIG_OUT = opt('--rig');
const ONLY = opt('--only') ? opt('--only').split(',') : null;
const SRC = opt('--src');
/* The app embeds the bone list; a build whose skeleton order differs would deform everyone, so it stops instead */
const EXPECT = opt('--expect');
const JOBS = Math.max(1, +(opt('--jobs') || 1));

THREE.TextureLoader.prototype.load = function (url){ const t = new THREE.Texture(); t.userData.url = url; return t; };
const quiet = console.warn; console.warn = () => {};

const CACHE = process.env.HK_CACHE || null;
async function get(rel){
  if (SRC){ const p = path.join(SRC, rel); if (fs.existsSync(p)) return fs.readFileSync(p); }
  if (CACHE){ const p = path.join(CACHE, rel); if (fs.existsSync(p)) return fs.readFileSync(p); const b = await fetchRaw(rel); fs.mkdirSync(path.dirname(p), { recursive:true }); fs.writeFileSync(p, b); return b; }
  return fetchRaw(rel);
}
async function fetchRaw(rel){
  const tail = rel.split('/').map(encodeURIComponent).join('/');
  for (let a = 0; a < 8; a++){
    const url = (a % 2 ? MIRROR : RAW) + tail;
    try {
      const r = await fetch(url);
      if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + url);
      const b = Buffer.from(await r.arrayBuffer());
      if (a) console.log('  (' + rel + ': fetched on try ' + (a + 1) + ')');
      return b;
    } catch (e){ if (a === 7) throw e; if (a % 2) await new Promise((res) => setTimeout(res, 1500 * (a + 1))); }
  }
}

/* Uncompressed or RLE true-colour TGA -> { w, h, ch, data (RGB/RGBA, top row first) } */
function decodeTGA(buf){
  const idLen = buf[0], type = buf[2], w = buf.readUInt16LE(12), h = buf.readUInt16LE(14), bpp = buf[16], desc = buf[17];
  if (type !== 2 && type !== 10) throw new Error('TGA type ' + type);
  const px = bpp / 8, ch = px === 4 ? 4 : 3, out = Buffer.alloc(w * h * ch), topFirst = (desc & 0x20) !== 0;
  let p = 18 + idLen + (buf[1] ? buf.readUInt16LE(5) * (buf[7] >> 3) : 0), i = 0;
  const put = (o) => { const row = Math.floor(i / w), col = i % w, y = topFirst ? row : h - 1 - row, d = (y * w + col) * ch;
    out[d] = buf[o + 2]; out[d + 1] = buf[o + 1]; out[d + 2] = buf[o]; if (ch === 4) out[d + 3] = buf[o + 3]; i++; };
  if (type === 2){ while (i < w * h){ put(p); p += px; } }
  else while (i < w * h){
    const c = buf[p++], n = (c & 0x7f) + 1;
    if (c & 0x80){ for (let k = 0; k < n; k++) put(p); p += px; } else { for (let k = 0; k < n; k++){ put(p); p += px; } }
  }
  return { w, h, ch, data:out };
}

/* Transparent hair pixels take the average hair colour so filtering never pulls in a fringe */
function bleed(img){
  const { data, w, h } = img; let r = 0, g = 0, b = 0, n = 0;
  for (let i = 0; i < w * h; i++){ const a = data[i * 4 + 3]; if (a > 200){ r += data[i * 4]; g += data[i * 4 + 1]; b += data[i * 4 + 2]; n++; } }
  if (!n) return;
  r = Math.round(r / n); g = Math.round(g / n); b = Math.round(b / n);
  for (let i = 0; i < w * h; i++) if (data[i * 4 + 3] < 24){ data[i * 4] = r; data[i * 4 + 1] = g; data[i * 4 + 2] = b; }
}
async function webp(img, size, q, alpha){
  return sharp(img.data, { raw:{ width:img.w, height:img.h, channels:img.ch } })
    .resize(size, size, { kernel:'lanczos3' })
    .webp(alpha ? { quality:q, alphaQuality:92, effort:5 } : { quality:q, effort:5 }).toBuffer();
}

let CANON = null;
async function buildAvatar(id, rel){
  const name = rel.split('/')[1];
  const fbx = await get('Assets/Avatars/' + rel + '/Export/' + name + '.fbx');
  const mgr = new THREE.LoadingManager();
  mgr.addHandler(/\.(tga|dds|psd|tif+)$/i, { setPath(){ return this; }, load(url){ const t = new THREE.Texture(); t.userData.url = url; return t; } });
  const root = new FBXLoader(mgr).parse(fbx.buffer.slice(fbx.byteOffset, fbx.byteOffset + fbx.byteLength), '');
  root.updateMatrixWorld(true);
  let mesh = null; root.traverse((o) => { if (o.isSkinnedMesh && !mesh) mesh = o; });
  if (!mesh) throw new Error('no skinned mesh in ' + rel);
  const sk = mesh.skeleton;
  for (const b of sk.bones) b.name = b.name.replace(/^Bip0\d_/, 'Bip01_');
  const names = sk.bones.map((b) => b.name);
  if (!CANON){
    CANON = { names, parents:sk.bones.map((b) => names.indexOf(b.parent && b.parent.name)) };
  }
  /* Extra bones (a weighted root, twist helpers) fold into their nearest known ancestor */
  const remap = sk.bones.map((b) => {
    let o = b;
    while (o && o.isBone){ const k = CANON.names.indexOf(o.name); if (k >= 0) return k; o = o.parent; }
    return 0;
  });
  /* Joints in skinning space, metres */
  const joints = new Float32Array(CANON.names.length * 3), M = new THREE.Matrix4(), jp = new THREE.Vector3();
  const seen = new Set();
  names.forEach((n, i) => { if (CANON.names.indexOf(n) < 0) return; M.copy(sk.boneInverses[i]).invert(); jp.setFromMatrixPosition(M).multiplyScalar(0.01); const k = remap[i]; joints[k * 3] = jp.x; joints[k * 3 + 1] = jp.y; joints[k * 3 + 2] = jp.z; seen.add(k); });
  /* A canonical bone this avatar lacks sits on its parent */
  for (let k = 0; k < CANON.names.length; k++) if (!seen.has(k)){
    let p = CANON.parents[k]; while (p >= 0 && !seen.has(p)) p = CANON.parents[p];
    if (p >= 0){ joints[k * 3] = joints[p * 3]; joints[k * 3 + 1] = joints[p * 3 + 1]; joints[k * 3 + 2] = joints[p * 3 + 2]; }
    console.log('  ' + id + ' lacks ' + CANON.names[k]);
  }

  /* Materials: skin (the head), alpha (hair, lashes, glasses), cloth (everything else); one texture each */
  const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
  const MI = mats.map((m) => {
    const file = m.map && m.map.userData.url ? m.map.userData.url.split(/[\\/]/).pop() : null;
    const kind = /opacity|hair|lash/i.test(m.name) || (m.alphaMap && m.alphaMap.userData.url) ? 'alpha' : /head/i.test(m.name) ? 'skin' : 'cloth';
    return { name:m.name, kind, file, body:kind === 'cloth' && /_body$/i.test(m.name) };
  });
  const g = mesh.geometry, P = g.attributes.position, N = g.attributes.normal, UV = g.attributes.uv, SI = g.attributes.skinIndex, SW = g.attributes.skinWeight;
  const B = mesh.bindMatrix, NB = new THREE.Matrix3().getNormalMatrix(B);
  const tris = [];
  const groups = g.groups.length ? g.groups : [{ start:0, count:P.count, materialIndex:0 }];
  for (const gr of groups) for (let i = gr.start; i < gr.start + gr.count; i += 3) tris.push([gr.materialIndex || 0, i]);
  tris.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  /* Weld identical corners into an indexed mesh */
  const VS = 24, keyMap = new Map(), verts = [], idx = [], counts = MI.map(() => 0);
  const v = new THREE.Vector3(), n = new THREE.Vector3();
  let mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9];
  const corner = (i) => {
    v.fromBufferAttribute(P, i).applyMatrix4(B).multiplyScalar(0.01); n.fromBufferAttribute(N, i).applyMatrix3(NB).normalize();
    const px = Math.round(v.x * 10000), py = Math.round(v.y * 10000), pz = Math.round(v.z * 10000);
    const nx = Math.round(n.x * 127), ny = Math.round(n.y * 127), nz = Math.round(n.z * 127);
    const u = Math.round(Math.min(1, Math.max(0, UV.getX(i))) * 65535), w = Math.round(Math.min(1, Math.max(0, 1 - UV.getY(i))) * 65535);
    const inf = [];
    for (let k = 0; k < 4; k++){ const wt = SW.getComponent(i, k); if (wt > 0) inf.push([remap[SI.getComponent(i, k)], wt]); }
    inf.sort((a, b) => b[1] - a[1]);
    const tot = inf.reduce((s, e) => s + e[1], 0) || 1;
    let q = inf.map((e) => Math.round(e[1] / tot * 255)), diff = 255 - q.reduce((s, e) => s + e, 0);
    if (q.length) q[0] += diff; else { inf.push([0, 1]); q = [255]; }
    const si = [0, 0, 0, 0], sw = [0, 0, 0, 0];
    inf.forEach((e, k) => { if (k < 4){ si[k] = e[0]; sw[k] = q[k]; } });
    const key = [px, py, pz, nx, ny, nz, u, w, ...si, ...sw].join(',');
    let id2 = keyMap.get(key);
    if (id2 == null){
      id2 = verts.length; keyMap.set(key, id2); verts.push([px, py, pz, nx, ny, nz, u, w, si, sw]);
      mn = mn.map((m2, k) => Math.min(m2, [v.x, v.y, v.z][k])); mx = mx.map((m2, k) => Math.max(m2, [v.x, v.y, v.z][k]));
    }
    return id2;
  };
  for (const [slot, i] of tris){ idx.push(corner(i), corner(i + 1), corner(i + 2)); counts[slot] += 3; }
  if (verts.length > 65535) throw new Error(id + ': too many vertices');
  /* Pack, reorder for the vertex cache, encode */
  const vb = Buffer.alloc(verts.length * VS);
  verts.forEach((t, i) => {
    const o = i * VS;
    vb.writeInt16LE(t[0], o); vb.writeInt16LE(t[1], o + 2); vb.writeInt16LE(t[2], o + 4);
    vb.writeInt8(t[3], o + 6); vb.writeInt8(t[4], o + 7); vb.writeInt8(t[5], o + 8);
    vb.writeUInt16LE(t[6], o + 10); vb.writeUInt16LE(t[7], o + 12);
    for (let k = 0; k < 4; k++){ vb[o + 14 + k] = t[8][k]; vb[o + 18 + k] = t[9][k]; }
  });
  await MeshoptEncoder.ready;
  /* Reorder per material range so the ranges stay contiguous */
  const ib = new Uint32Array(idx);
  const remapV = new Uint32Array(verts.length).fill(0xffffffff);
  let next = 0; const order = [];
  for (let i = 0; i < ib.length; i++){ const a = ib[i]; if (remapV[a] === 0xffffffff){ remapV[a] = next++; order.push(a); } ib[i] = remapV[a]; }
  const vb2 = Buffer.alloc(vb.length);
  order.forEach((old, nw) => vb.copy(vb2, nw * VS, old * VS, old * VS + VS));
  const ib16 = new Uint16Array(ib);
  const encI = Buffer.from(MeshoptEncoder.encodeIndexBuffer(new Uint8Array(ib16.buffer), ib16.length, 2));
  const encV = Buffer.from(MeshoptEncoder.encodeVertexBuffer(new Uint8Array(vb2.buffer, vb2.byteOffset, vb2.length), verts.length, VS));
  const height = mx[1] - mn[1];

  /* Textures: one per material (sizes by kind and tier), plus a normal map for the body cloth */
  const texRel = (file) => 'Assets/Avatars/' + rel + '/Textures/' + file;
  const SIZES = { lo:{ skin:512, body:512, cloth:256, alpha:256, nrm:256 }, hi:{ skin:1024, body:1024, cloth:512, alpha:512, nrm:512 } };
  const imgs = new Map();
  const load = async (file) => {
    if (!file) return null;
    if (imgs.has(file)) return imgs.get(file);
    let im = null;
    try { im = decodeTGA(await get(texRel(file))); if (im.ch === 4) bleed(im); }
    catch (e){ console.log('  (' + id + ': no texture ' + file + ': ' + e.message + ')'); }
    imgs.set(file, im); return im;
  };
  const used = [];
  for (const m of MI){
    m.img = await load(m.file);
    if (m.body){ const nf = m.file ? m.file.replace(/_body_color[^.]*\.tga$/i, '_body_normal.tga') : null; m.nimg = nf && nf !== m.file ? await load(nf) : null; }
  }
  const out = {};
  for (const tier of ['lo', 'hi']){
    const Z = SIZES[tier], blobs = [], texOut = [], matsOut = [];
    let off = 0;
    const addBlob = (b) => { const o = off; blobs.push(b); off += b.length; const pad = (4 - (b.length % 4)) % 4; if (pad){ blobs.push(Buffer.alloc(pad)); off += pad; } return o; };
    const encV2 = encV, encI2 = encI;
    const vbAt = [addBlob(encV2), encV2.length], ibAt = [addBlob(encI2), encI2.length];
    const texIndex = new Map();
    const putTex = async (img, size, q, key) => {
      if (!img) return -1;
      const k = key + '@' + size; if (texIndex.has(k)) return texIndex.get(k);
      const b = await webp(img, size, q, img.ch === 4);
      texOut.push([addBlob(b), b.length]); texIndex.set(k, texOut.length - 1); return texOut.length - 1;
    };
    for (let i = 0; i < MI.length; i++){
      const m = MI[i], size = m.kind === 'skin' ? Z.skin : m.kind === 'alpha' ? Z.alpha : m.body ? Z.body : Z.cloth;
      const t = await putTex(m.img, size, m.kind === 'alpha' ? 84 : 81, m.file);
      const nm = m.nimg ? await putTex(m.nimg, Z.nrm, 90, 'nrm:' + m.file) : -1;
      matsOut.push({ k:m.kind, n:counts[i], t, nm, b:m.body ? 1 : 0 });
    }
    const head = { id, v:2, vc:verts.length, ic:ib16.length, vs:VS, h:+height.toFixed(4), vb:vbAt, ib:ibAt, mats:matsOut, tex:texOut };
    let hj = Buffer.from(JSON.stringify(head)); const hp = (4 - ((8 + hj.length) % 4)) % 4; hj = Buffer.concat([hj, Buffer.alloc(hp, 32)]);
    const pre = Buffer.alloc(8); pre.write('HK01', 0, 'ascii'); pre.writeUInt32LE(hj.length, 4);
    const file = Buffer.concat([pre, hj, ...blobs]);
    fs.writeFileSync(path.join(OUT, id + '.' + tier + '.hk'), file);
    out[tier] = file.length;
  }
  return { joints, height, verts:verts.length, tris:ib16.length / 3, groups:MI.map((m, i) => m.kind[0] + (counts[i] / 3)), out };
}

fs.mkdirSync(OUT, { recursive:true });
const rig = { commit:COMMIT, avatars:{} };
const ids = Object.keys(AVATARS).filter((id) => !ONLY || ONLY.includes(id));
let total = 0;
const one = async (id) => {
  const t0 = Date.now();
  const r = await buildAvatar(id, AVATARS[id]);
  rig.avatars[id] = { h:+r.height.toFixed(3), j:Array.from(r.joints, (x) => Math.round(x * 1000)) };
  total += r.out.lo + r.out.hi;
  console.log(id.padEnd(5), String(r.verts).padStart(5), 'v', String(r.tris).padStart(5), 't', r.groups.join('/'), 'h', r.height.toFixed(2), 'lo', (r.out.lo / 1024).toFixed(0) + 'K', 'hi', (r.out.hi / 1024).toFixed(0) + 'K', ((Date.now() - t0) / 1000).toFixed(1) + 's');
};
/* The first avatar sets the canonical skeleton, so it goes alone; the rest can build side by side */
await one(ids[0]);
if (EXPECT){
  const want = JSON.parse(fs.readFileSync(EXPECT, 'utf8'));
  if (JSON.stringify(want) !== JSON.stringify(CANON.names)){ console.error('Skeleton order differs from the app\'s rig; stopping.'); process.exit(1); }
}
const queue = ids.slice(1);
await Promise.all(Array.from({ length:JOBS }, async () => { while (queue.length) await one(queue.shift()); }));
rig.names = CANON.names; rig.parents = CANON.parents;
/* The MIT notice travels with the converted avatars */
fs.writeFileSync(path.join(OUT, 'ROCKETBOX-LICENSE.txt'), await get('LICENSE.md'));
if (RIG_OUT) fs.writeFileSync(RIG_OUT, JSON.stringify(rig));
console.log('done', ids.length, 'avatars', (total / 1048576).toFixed(1) + ' MB total');
console.warn = quiet;
