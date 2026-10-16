/* Lay out a Vercel PREVIEW deployment that reuses the previous preview's page chunks (by hash) and uploads
   only a small zstd patch. Run after build_deploy.py, with deploy/prev holding the previous preview's site.
   Output: deploy/vpatch/ (files + deploy.json for the API) and deploy/vsim/ (a local dry run of the build). */
import fs from 'node:fs';
import zlib from 'node:zlib';
import crypto from 'node:crypto';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const sha1 = (b) => crypto.createHash('sha1').update(b).digest('hex');
const chunksOf = (f) => JSON.parse(fs.readFileSync(f, 'utf8')).filter((c) => c.file.startsWith('c/'));
const sub = (s, a, b) => { const p = s.split(a); if (p.length !== 2) throw new Error('placeholder ' + a); return p.join(b); };
const PART = 21000;

const prev = chunksOf('deploy/prev/manifest.json');
const P0 = zlib.gunzipSync(Buffer.concat(prev.map((c) => fs.readFileSync('deploy/prev/' + c.file))));
const cur = chunksOf('deploy/manifest.json');
const P1 = zlib.gunzipSync(Buffer.concat(cur.map((c) => fs.readFileSync('deploy/site/' + c.file))));

/* Loading-screen template: the same substitution build_deploy.py makes, with the chunk list left open */
const imap = fs.readFileSync('deploy/src/importmap.json', 'utf8').trim();
let loader = sub(fs.readFileSync('parts/loader.html', 'utf8'), '<!--IMPORTMAP-->',
  '<script type="importmap">' + imap + '</script>\n<link rel="modulepreload" href="' + JSON.parse(imap).imports.three + '" crossorigin>');
if (sub(loader, '/*CHUNKS*/', cur.map((c) => "'/" + c.file + "'").join(',')) !== fs.readFileSync('deploy/site/index.html', 'utf8')) throw new Error('loader template drifted');

/* Bundle: XRB1 + header length + JSON header + file bytes */
const files = [['payload', P1], ['loader.html', Buffer.from(loader)], ['hk/build.mjs', fs.readFileSync('hk/build.mjs')], ['hk/names.json', fs.readFileSync('hk/names.json')],
  ['web/fetch_assets.mjs', fs.readFileSync('parts/fetch_assets.mjs')], ['web/assets.json', fs.readFileSync('deploy/assets.json')]];
const head = Buffer.from(JSON.stringify({ files:files.map(([name, b]) => ({ name, size:b.length, sha:sha1(b) })) }));
const pre = Buffer.alloc(8); pre.write('XRB1', 0, 'latin1'); pre.writeUInt32LE(head.length, 4);
const bundle = Buffer.concat([pre, head, ...files.map((f) => f[1])]);
const C = zlib.constants;
const zst = zlib.zstdCompressSync(bundle, { dictionary:P0, params:{ [C.ZSTD_c_compressionLevel]:22, [C.ZSTD_c_windowLog]:23, [C.ZSTD_c_enableLongDistanceMatching]:1 } });
if (!zlib.zstdDecompressSync(zst, { dictionary:P0 }).equals(bundle)) throw new Error('zstd round trip');
const nParts = Math.ceil(zst.length / PART), size = Math.ceil(zst.length / nParts);
const parts = Array.from({ length:nParts }, (_, i) => zst.subarray(i * size, (i + 1) * size));

const site = [['/*PREV*/', prev.map((c) => "'" + path.basename(c.file, '.bin') + "'").join(', ')], ['/*PREV_SHA*/', sha1(P0)], ['/*PARTS*/', String(nParts)]]
  .reduce((s, [a, b]) => sub(s, a, b), fs.readFileSync('parts/vsite.mjs', 'utf8'));
const cfg = JSON.parse(fs.readFileSync('parts/vercel.json', 'utf8'));
cfg.headers.push({ source:'/h/(.*)', headers:[{ key:'Cache-Control', value:'public, max-age=86400' }] });
cfg.headers.push({ source:'/lib/(.*)', headers:[{ key:'Cache-Control', value:'public, max-age=86400' }] });
const vercel = JSON.stringify(Object.assign({
  installCommand:'npm install --prefix hk --no-audit --no-fund',
  buildCommand:'node site.mjs && node web/fetch_assets.mjs && node hk/build.mjs public/h --expect hk/names.json --jobs 4',
  outputDirectory:'public'
}, cfg), null, 2) + '\n';
const inline = { 'site.mjs':site, 'vercel.json':vercel, 'package.json':'{ "name": "walk-the-archive", "private": true }\n', 'hk/package.json':fs.readFileSync('hk/package.json', 'utf8') };

/* deploy/vpatch: what goes to the API */
const OUT = 'deploy/vpatch';
fs.rmSync(OUT, { recursive:true, force:true }); fs.mkdirSync(OUT + '/b64', { recursive:true });
const api = [];
for (const c of prev) api.push({ file:'prev/' + c.file, sha:c.sha, size:c.size });
parts.forEach((b, i) => { fs.writeFileSync(OUT + '/b64/' + i + '.txt', b.toString('base64')); api.push({ file:'patch/' + i + '.bin', sha:sha1(b), size:b.length }); });
for (const [f, t] of Object.entries(inline)) api.push({ file:f, data:t });
fs.writeFileSync(OUT + '/deploy.json', JSON.stringify(api, null, 1));

/* deploy/vsim: run the build's first step locally and check the page it makes */
const SIM = 'deploy/vsim';
fs.rmSync(SIM, { recursive:true, force:true });
for (const c of prev) { fs.mkdirSync(SIM + '/prev/c', { recursive:true }); fs.copyFileSync('deploy/prev/' + c.file, SIM + '/prev/' + c.file); }
parts.forEach((b, i) => { fs.mkdirSync(SIM + '/patch', { recursive:true }); fs.writeFileSync(SIM + '/patch/' + i + '.bin', b); });
for (const [f, t] of Object.entries(inline)) { fs.mkdirSync(path.dirname(SIM + '/' + f), { recursive:true }); fs.writeFileSync(SIM + '/' + f, t); }
console.log(execFileSync('node', ['site.mjs'], { cwd:SIM, encoding:'utf8' }).trim());
const idx = fs.readFileSync(SIM + '/public/index.html', 'utf8');
const urls = [...idx.match(/const C = \[([^\]]*)\]/)[1].matchAll(/'\/(c\/[0-9a-f]{12}\.bin)'/g)].map((m) => m[1]);
const back = zlib.gunzipSync(Buffer.concat(urls.map((u) => fs.readFileSync(SIM + '/public/' + u))));
if (!back.equals(P1)) throw new Error('dry run page differs');
if (!fs.readFileSync(SIM + '/hk/build.mjs').equals(fs.readFileSync('hk/build.mjs'))) throw new Error('dry run build.mjs differs');
console.log('patch', zst.length, 'bytes in', nParts, 'parts', parts.map((b) => b.length).join('/'), '| base64', parts.reduce((n, b) => n + Math.ceil(b.length / 3) * 4, 0), '| inline', Object.values(inline).reduce((n, t) => n + t.length, 0), 'chars | dry run OK');
