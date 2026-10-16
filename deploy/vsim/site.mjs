/* Vercel build, step 1 of 2: rebuild the campus page.
   prev/c/*.bin are the previous preview's page chunks, reused by hash, so nothing large is uploaded twice.
   patch/*.bin is one zstd frame that uses the previous page as its dictionary. It holds the new page,
   the loading-screen template and the avatar build script. Step 2 (hk/build.mjs) converts the
   Microsoft Rocketbox avatars into public/h. */
import fs from 'node:fs';
import zlib from 'node:zlib';
import crypto from 'node:crypto';

const PREV = ['9b1ce9b98fd2', '14c6f11a18c8', '631e025380d0', 'f4a941f1c638', '433f038390cd', 'd0ccf05ecc7a', 'b452442670e5', '9d8f2a6d522f', 'dfc7954c0238', 'c82eb9067c1a', 'e730ffed8c5c'];
const PREV_SHA = 'c44754d6db894ddbe9f75e0da7f54dc44b5e6afd';
const PARTS = 4;
const CHUNK = 21000;
const sha1 = (b) => crypto.createHash('sha1').update(b).digest('hex');

console.log('Node ' + process.version);
const dict = zlib.gunzipSync(Buffer.concat(PREV.map((h) => fs.readFileSync('prev/c/' + h + '.bin'))));
if (sha1(dict) !== PREV_SHA) throw new Error('The previous page did not rebuild exactly');
if (typeof zlib.zstdDecompressSync !== 'function') throw new Error('This Node.js has no zstd; use Node 24');
const zst = Buffer.concat(Array.from({ length:PARTS }, (_, i) => fs.readFileSync('patch/' + i + '.bin')));
const bundle = zlib.zstdDecompressSync(zst, { dictionary:dict });
if (bundle.toString('latin1', 0, 4) !== 'XRB1') throw new Error('The patch is not a campus bundle');
const hl = bundle.readUInt32LE(4), head = JSON.parse(bundle.toString('utf8', 8, 8 + hl));
const got = {};
let at = 8 + hl;
for (const f of head.files){
  const b = bundle.subarray(at, at + f.size);
  at += f.size;
  if (sha1(b) !== f.sha) throw new Error('Patch file ' + f.name + ' did not match');
  got[f.name] = b;
  if (f.name.includes('/')){
    fs.mkdirSync(f.name.slice(0, f.name.lastIndexOf('/')), { recursive:true });
    fs.writeFileSync(f.name, b);
  }
}

/* The page ships as gzip chunks behind a small loading screen (the browser unzips them) */
const gz = zlib.gzipSync(got.payload, { level:9, memLevel:9 });
fs.mkdirSync('public/c', { recursive:true });
const urls = [];
for (let i = 0; i < gz.length; i += CHUNK){
  const b = gz.subarray(i, i + CHUNK), name = 'c/' + sha1(b).slice(0, 12) + '.bin';
  fs.writeFileSync('public/' + name, b);
  urls.push("'/" + name + "'");
}
const page = got['loader.html'].toString('utf8');
if (page.split('/*CHUNKS*/').length !== 2) throw new Error('Loader template');
fs.writeFileSync('public/index.html', page.replace('/*CHUNKS*/', urls.join(',')));
console.log('Page: ' + got.payload.length + ' bytes, ' + gz.length + ' gzipped, ' + urls.length + ' chunks');
