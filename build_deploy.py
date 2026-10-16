"""Build the Vercel version of the campus.

The full page (CSS, body markup, app JS) is minified, gzip-compressed with
zopfli and split into small content-hashed chunks under /c/. A tiny
index.html shows a loading screen, fetches the chunks, decompresses them
in the browser (DecompressionStream) and mounts the page.

Run after assemble.py. Output: deploy/site/ (what gets deployed) and
deploy/b64/ (base64 of each chunk, for the upload API).
"""
import base64, hashlib, json, os, re, shutil, subprocess, sys
import zopfli.gzip

SP = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(SP, 'tools', 'minify')
SRC = os.path.join(SP, 'deploy', 'src')
BUILD = os.path.join(SP, 'deploy', 'build')
SITE = os.path.join(SP, 'deploy', 'site')
B64 = os.path.join(SP, 'deploy', 'b64')
CHUNK = int(os.environ.get('CHUNK', '12000'))
SEP = '\x01'

for d in (BUILD, SITE, B64):
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)

def node(*args):
    r = subprocess.run(['node', os.path.join(TOOLS, 'minify.mjs'), *args], cwd=TOOLS, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr)
    print(r.stdout.strip())

node('js', os.path.join(SRC, 'app.js'), os.path.join(BUILD, 'app.min.js'))
node('css', os.path.join(SRC, 'style.css'), os.path.join(BUILD, 'style.min.css'))
js = open(os.path.join(BUILD, 'app.min.js'), encoding='utf-8').read()
css = open(os.path.join(BUILD, 'style.min.css'), encoding='utf-8').read()
body = open(os.path.join(SRC, 'body.html'), encoding='utf-8').read()
assert '<script' not in body and '<pre' not in body and '<textarea' not in body
body = re.sub(r'\s+', ' ', body).strip()
for part in (css, body, js):
    assert SEP not in part

payload = (css + SEP + body + SEP + js).encode('utf-8')
gz = zopfli.gzip.compress(payload, numiterations=40)
print('payload', len(payload), 'gzip', len(gz))

chunks = []
for i in range(0, len(gz), CHUNK):
    data = gz[i:i + CHUNK]
    sha = hashlib.sha1(data).hexdigest()
    name = 'c/%s.bin' % sha[:12]
    os.makedirs(os.path.join(SITE, 'c'), exist_ok=True)
    open(os.path.join(SITE, name), 'wb').write(data)
    b = base64.b64encode(data).decode('ascii')
    open(os.path.join(B64, '%02d.txt' % len(chunks)), 'w').write(b)
    chunks.append({'file': name, 'sha': sha, 'size': len(data), 'b64': len(b)})

urls = ','.join("'/%s'" % c['file'] for c in chunks)
page = open(os.path.join(SP, 'parts', 'loader.html'), encoding='utf-8').read()
assert page.count('/*CHUNKS*/') == 1
page = page.replace('/*CHUNKS*/', urls)
imap = open(os.path.join(SRC, 'importmap.json'), encoding='utf-8').read().strip()
three_url = json.loads(imap)['imports']['three']
assert page.count('<!--IMPORTMAP-->') == 1
page = page.replace('<!--IMPORTMAP-->', '<script type="importmap">' + imap + '</script>\n<link rel="modulepreload" href="' + three_url + '" crossorigin>')
open(os.path.join(SITE, 'index.html'), 'w', encoding='utf-8').write(page)
shutil.copy(os.path.join(SP, 'parts', 'vercel.json'), os.path.join(SITE, 'vercel.json'))

for f in ('index.html', 'vercel.json'):
    data = open(os.path.join(SITE, f), 'rb').read()
    chunks.append({'file': f, 'sha': hashlib.sha1(data).hexdigest(), 'size': len(data)})
json.dump(chunks, open(os.path.join(SP, 'deploy', 'manifest.json'), 'w'), indent=1)
for c in chunks:
    print(c)
