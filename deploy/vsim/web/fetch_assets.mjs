/* Vercel build, step 1b: the baked rooms (glTF + reflection probes) are too big to upload with the page,
   so the build downloads them from the public asset releases and checks every byte against a hash. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const ASSETS = JSON.parse(fs.readFileSync('web/assets.json', 'utf8'));
const sha256 = (b) => crypto.createHash('sha256').update(b).digest('hex');
let bytes = 0;
for (const a of ASSETS.files){
  const dest = path.join('public', a.dest);
  fs.mkdirSync(path.dirname(dest), { recursive:true });
  let buf = null;
  for (let attempt = 1; attempt <= 3 && !buf; attempt++){
    try {
      const r = await fetch(a.url, { redirect:'follow' });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const b = Buffer.from(await r.arrayBuffer());
      if (sha256(b) !== a.sha256) throw new Error('hash mismatch');
      buf = b;
    } catch (e) {
      console.warn('asset', a.dest, 'attempt', attempt, String(e));
      await new Promise((res) => setTimeout(res, 1500 * attempt));
    }
  }
  if (!buf) throw new Error('Could not fetch ' + a.url);
  fs.writeFileSync(dest, buf); bytes += buf.length;
  console.log('asset', a.dest, (buf.length / 1e6).toFixed(2), 'MB ok');
}
console.log('assets:', ASSETS.files.length, 'files,', (bytes / 1e6).toFixed(1), 'MB');
