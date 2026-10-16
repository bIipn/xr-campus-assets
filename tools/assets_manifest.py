"""Write deploy/assets.json: the baked files the Vercel build downloads, pinned to the asset repo commit.
Usage: python3 tools/assets_manifest.py <asset repo clone path>"""
import hashlib, json, os, subprocess, sys
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
repo = sys.argv[1]
sha = subprocess.check_output(['git', '-C', repo, 'rev-parse', 'HEAD'], text=True).strip()
origin = subprocess.check_output(['git', '-C', repo, 'remote', 'get-url', 'origin'], text=True).strip()
owner_repo = origin.replace('https://github.com/', '').removesuffix('.git')
files = []
for rel in ['lib/lib.glb', 'lib/probe.hdr']:
    fp = os.path.join(repo, rel)
    data = open(fp, 'rb').read()
    files.append({ 'dest':rel, 'url':'https://raw.githubusercontent.com/%s/%s/%s' % (owner_repo, sha, rel), 'sha256':hashlib.sha256(data).hexdigest(), 'bytes':len(data) })
json.dump({ 'repo':owner_repo, 'commit':sha, 'files':files }, open(os.path.join(SP, 'deploy', 'assets.json'), 'w'), indent=1)
print(json.dumps(files, indent=1))
