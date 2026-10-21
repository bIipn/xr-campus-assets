"""
Export the web campus (three.js) as glTF greybox geometry for Unreal Engine 5.

The campus outside the Reading Room is built procedurally in JavaScript at page load: walls,
floors, furniture, signs and posters painted on canvases. This script boots the real page in
headless Chromium (the same harness the web tests use), then saves every wing with three.js'
GLTFExporter, so Unreal starts from the exact same layout, sizes and artwork.

What is left out on purpose (Unreal replaces it with its own, better version):
  sky dome and other custom-shader meshes, wind grass, particles/lines/sprites, skinned people (MetaHumans replace them),
  invisible helper meshes (tap targets and walk blockers that only the web build needs) and anything
  hidden when the campus first loads (state toggles, ride extras); wing roots are switched on first,
  the baked Reading Room (exported from Blender by unreal/Pipeline/blender/export_reading_room.py).
Glows that the web build pushed past full brightness become emissive materials (Lumen lights the room with them).

Interactive pieces keep a name tag so Unreal setup scripts can find them:
  item__<id>     an exhibit (frame/art/placard) that opens a catalog card
  staff__<id>    where a staff member stands
  ride__<id>     ride geometry
  token__<id>    a hidden XR token
Lights are written separately (lights.json); Unreal spawns real lights there.

Needs: pip install playwright; npm deps for the web test harness (see unreal/Pipeline/README.md).
Run from the repo root:  python3 unreal/Pipeline/web/export_campus.py
Writes unreal/Pipeline/out/campus/<wing>.glb, art/<exhibit id>.png, lights.json, manifest.json
"""
import asyncio
import base64
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'test'))
os.environ.setdefault('CAMPUS_GFX', 'high')
os.environ.setdefault('BOOT_TIMEOUT', '240000')
import harness  # noqa: E402  (test/harness.py)
from playwright.async_api import async_playwright  # noqa: E402

OUT = os.path.join(REPO, 'unreal', 'Pipeline', 'out', 'campus')
WINGS = ['museum', 'waxIntro', 'wax', 'lib', 'school', 'outside', 'play', 'dive', 'props']

PREP = r"""
async () => {
  const T = window.__test, THREE = T.THREE;
  const mod = await import('https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/exporters/GLTFExporter.js/+esm');
  window.__GLTFExporter = mod.GLTFExporter;
  const scene = T.scene, W = T.WING;
  /* The baked Reading Room loads asynchronously; wait for it, then leave it out (Blender exports it) */
  for (let i = 0; i < 240 && T.BK && T.BK.rooms && T.BK.rooms.lib && !T.BK.rooms.lib.ready; i++) await new Promise((r) => setTimeout(r, 500));
  const report = { removed:{}, tagged:0 };
  const SLOTS = ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'emissiveMap', 'aoMap', 'alphaMap', 'lightMap', 'bumpMap'];
  const seen = new Map(), glow = new Map();
  /* GLTFExporter only takes images and canvases: data textures become canvases, anything else is dropped */
  const okTex = (t, rep) => {
    if (seen.has(t)) return seen.get(t);
    let out = t; const im = t.image;
    const good = im && ((typeof HTMLImageElement !== 'undefined' && im instanceof HTMLImageElement) || (typeof HTMLCanvasElement !== 'undefined' && im instanceof HTMLCanvasElement)
      || (typeof ImageBitmap !== 'undefined' && im instanceof ImageBitmap) || (typeof OffscreenCanvas !== 'undefined' && im instanceof OffscreenCanvas));
    if (t.isCompressedTexture || t.isCubeTexture || t.isRenderTargetTexture || t.isDepthTexture){ rep.removed.texture_dropped = (rep.removed.texture_dropped || 0) + 1; seen.set(t, null); return null; }
    if (good && !(im.width <= 1 && im.height <= 1)) { seen.set(t, t); return t; }
    if (t.isDataTexture && im && im.data && im.width > 1 && (im.data instanceof Uint8Array || im.data instanceof Uint8ClampedArray)){
      const c = document.createElement('canvas'); c.width = im.width; c.height = im.height;
      const ctx = c.getContext('2d'), id = ctx.createImageData(im.width, im.height), n = im.width * im.height, ch = im.data.length / n;
      for (let i = 0; i < n; i++){ const r = im.data[i * ch], g = ch > 1 ? im.data[i * ch + 1] : r, b = ch > 2 ? im.data[i * ch + 2] : r, a = ch > 3 ? im.data[i * ch + 3] : 255; id.data.set([r, g, b, a], i * 4); }
      ctx.putImageData(id, 0, 0);
      out = t.clone(); out.image = c; out.isDataTexture = false; rep.removed.datatex_converted = (rep.removed.datatex_converted || 0) + 1;
    } else { out = null; rep.removed.texture_dropped = (rep.removed.texture_dropped || 0) + 1; }
    seen.set(t, out); return out;
  };
  const drop = (o, why) => { report.removed[why] = (report.removed[why] || 0) + 1; o.parent && o.parent.remove(o); };
  const grass = T.NATURE && T.NATURE.grass;
  const staffRoots = new Set(Object.values(T.STAFF || {}).map((s) => s.root).filter(Boolean));
  let hidden = 0;
  for (const k of Object.keys(W)) W[k].traverse((o) => { if (o !== W[k] && o.visible === false) hidden++; });
  report.hidden_objects_kept = hidden;
  /* The Wax Hall's carried props (headsets, tablets, laptops, phones, a book, a box, a clipboard...) are
     posed by the web's reenactors, who are not exported; frozen where the web hands were at t = 0 they would
     float beside Unreal's own acting figures. They leave the hall and become a wing of their own, 'props':
     one object per carry in its own local frame, named prop__<scene id>_<index of the S.carry call>, so the
     Unreal stage can ride them on the sockets its acting data names. Where each sat at t = 0 (stage-local
     metres, three.js axes) goes out as props_rest for the ones that stay put on a desk. */
  const carried = new Map();
  for (const sc of (T.WAX_SCENES || [])){ const S = sc.stage; if (!S) continue; (S.carries || []).forEach((c, k) => carried.set(c.obj, { scene:sc.id, k, stage:S })); }
  const props = new THREE.Group(); props.name = 'props';
  const rest = [];
  const _inv = new THREE.Matrix4(), _loc = new THREE.Matrix4(), _P = new THREE.Vector3(), _Q = new THREE.Quaternion(), _S = new THREE.Vector3();
  for (const [obj, info] of carried){
    info.stage.g.updateMatrixWorld(true); obj.updateMatrixWorld(true);
    _inv.copy(info.stage.g.matrixWorld).invert(); _loc.multiplyMatrices(_inv, obj.matrixWorld); _loc.decompose(_P, _Q, _S);
    rest.push({ scene:info.scene, k:info.k, name:obj.name || '', p:[_P.x, _P.y, _P.z], q:[_Q.x, _Q.y, _Q.z, _Q.w], visible:obj.visible });
    const c = obj.clone(true);
    c.matrixAutoUpdate = true; c.matrix.identity(); c.position.set(0, 0, 0); c.quaternion.identity(); c.scale.set(1, 1, 1);
    c.name = 'prop__' + info.scene + '_' + info.k;
    c.traverse((o) => { o.visible = true; });
    props.add(c);
  }
  report.carried = carried.size;
  W.props = props;
  for (const k of Object.keys(W)){
    W[k].visible = true;
    const kill = [];
    W[k].traverse((o) => {
      if (o === grass) kill.push([o, 'grass']);
      else if (o.name && o.name.startsWith('baked-')) kill.push([o, 'baked_room']);
      else if (staffRoots.has(o)){ kill.push([o, 'staff']); }
      else if (carried.has(o)) kill.push([o, 'carried']);
      else if (o.isPoints || o.isLine || o.isSprite) kill.push([o, 'points/lines']);
      else if (o.isSkinnedMesh) kill.push([o, 'skinned']);
      else if (o.userData && (o.userData.baked || o.userData.bakedRoom)) kill.push([o, 'baked']);
      else if (o.isMesh){
        const ms = Array.isArray(o.material) ? o.material : [o.material];
        if (ms.some((m) => m && m.map && m.map.isCompressedTexture)) { kill.push([o, 'ktx2']); return; }
        if (o.isInstancedMesh && o.count > 2000) { kill.push([o, 'big_instanced']); return; }
        /* Custom shaders (the sky dome) have no glTF equivalent; Unreal's Sky Atmosphere replaces the sky */
        if (ms.some((m) => m && (m.isShaderMaterial || m.isRawShaderMaterial))) { kill.push([o, 'shader_mesh']); return; }
        /* Invisible helpers (tap targets, walk blockers, shelf proxies) are web-only; Unreal uses real collision */
        if (ms.every((m) => !m || m.visible === false)) { kill.push([o, 'invisible_helper']); return; }
        const fix = (m) => {
          if (!m) return m;
          /* Glows were brightened past 1.0 for the web bloom; in glTF a colour over 1 is invalid, so it becomes emission */
          if (m.color && Math.max(m.color.r, m.color.g, m.color.b) > 1.0001){
            if (glow.has(m)) return glow.get(m);
            const k = Math.max(m.color.r, m.color.g, m.color.b), c = m.color.clone().multiplyScalar(1 / k);
            const n = new THREE.MeshStandardMaterial({ color:0x000000, roughness:0.6, emissive:c, emissiveIntensity:k, emissiveMap:m.map || null,
              transparent:m.transparent, opacity:m.opacity, side:m.side, alphaTest:m.alphaTest, name:(m.name || 'glow') });
            report.removed.glow_to_emissive = (report.removed.glow_to_emissive || 0) + 1; glow.set(m, n); return n;
          }
          if (m.isShaderMaterial || m.isRawShaderMaterial){ report.removed.shader_swapped = (report.removed.shader_swapped || 0) + 1;
            return new THREE.MeshStandardMaterial({ color:0x808080, roughness:0.7, transparent:m.transparent, opacity:m.uniforms && m.uniforms.uOpacity ? m.uniforms.uOpacity.value : 1 }); }
          return m;
        };
        o.material = Array.isArray(o.material) ? o.material.map(fix) : fix(o.material);
        for (const m of (Array.isArray(o.material) ? o.material : [o.material])) if (m) for (const slot of Object.keys(m)) if (m[slot] && m[slot].isTexture) m[slot] = okTex(m[slot], report);
      }
      if (o.isMesh && o.geometry){
        /* Only standard vertex attributes go out (custom ones like fish phases have other lengths) */
        const keep = ['position', 'normal', 'uv', 'uv1', 'uv2', 'color', 'tangent'];
        let g = o.geometry, cloned = false;
        for (const name of Object.keys(g.attributes)) if (!keep.includes(name)){ if (!cloned){ g = g.clone(); cloned = true; } g.deleteAttribute(name); report.removed.attr_stripped = (report.removed.attr_stripped || 0) + 1; }
        const col = g.attributes.color;
        if (col && col.array && !col.normalized){ let bad = false; for (let i = 0; i < col.array.length; i++) if (col.array[i] > 1 || col.array[i] < 0){ bad = true; break; }
          if (bad){ if (!cloned){ g = g.clone(); cloned = true; } const a = g.attributes.color.array; for (let i = 0; i < a.length; i++) a[i] = Math.min(1, Math.max(0, a[i])); } }
        if (cloned) o.geometry = g;
      }
      /* glTF nodes must be translate/rotate/scale: bake a sheared or frozen matrix into the mesh */
      if (!o.matrixAutoUpdate){
        const P = new THREE.Vector3(), Q = new THREE.Quaternion(), S = new THREE.Vector3(), M = new THREE.Matrix4();
        o.matrix.decompose(P, Q, S); M.compose(P, Q, S);
        const same = M.elements.every((v, i) => Math.abs(v - o.matrix.elements[i]) < 1e-5);
        if (!same && o.isMesh && !o.children.length){ o.geometry = o.geometry.clone(); o.geometry.applyMatrix4(o.matrix); o.matrix.identity(); P.set(0, 0, 0); Q.identity(); S.set(1, 1, 1); report.removed.matrix_baked = (report.removed.matrix_baked || 0) + 1; }
        o.position.copy(P); o.quaternion.copy(Q); o.scale.copy(S); o.matrixAutoUpdate = true;
      }
      if (o.scale && (o.scale.x === 0 || o.scale.y === 0 || o.scale.z === 0)) o.scale.set(o.scale.x || 1e-4, o.scale.y || 1e-4, o.scale.z || 1e-4);
      const ud = o.userData || {};
      for (const tag of ['item', 'staff', 'ride', 'token', 'station', 'book', 'bp']){
        if (ud[tag] != null){ const id = ud[tag].id || ud[tag].key || (typeof ud[tag] === 'string' ? ud[tag] : ''); o.name = tag + '__' + id; report.tagged++; break; }
      }
    });
    for (const [o, why] of kill) drop(o, why);
  }
  const lamps = (T.LAMPS && T.LAMPS.all || []).map((L) => ({ pos_m:[L.p.x, L.p.y, L.p.z], color_srgb:'#' + L.color.getHexString(), intensity_threejs:L.intensity, distance_m:L.distance, decay:L.decay, wing:L.wing }));
  const sun = T.LIGHTS && T.LIGHTS.sun ? { dir_to_sun:[T.LIGHTS.sun.position.x, T.LIGHTS.sun.position.y, T.LIGHTS.sun.position.z] } : null;
  return { report, lamps, sun, wings:Object.keys(W), props_rest:rest };
}
"""

EXPORT = r"""
async (k) => {
  const W = window.__test.WING, root = W[k];
  if (!root) return { size:0 };
  const ex = new window.__GLTFExporter();
  /* The page hides wings you can't see from the camera; switch this one on just for the export */
  const was = root.visible; root.visible = true; root.updateMatrixWorld(true);
  const buf = await ex.parseAsync(root, { binary:true, onlyVisible:true, maxTextureSize:2048, includeCustomExtensions:false });
  root.visible = was;
  window.__glb = new Uint8Array(buf);
  return { size:window.__glb.length };
}
"""

CHUNK = r"""
([a, b]) => { const u = window.__glb.subarray(a, b); let s = ''; for (let i = 0; i < u.length; i += 0x8000) s += String.fromCharCode.apply(null, u.subarray(i, i + 0x8000)); return btoa(s); }
"""


async def main():
    os.makedirs(OUT, exist_ok=True)
    async with async_playwright() as p:
        b, page, logs = await harness.open_page(p, 'desktop')
        page.set_default_timeout(600000)
        info = await page.evaluate(PREP)
        manifest = {'source': 'three.js campus (parts/*.js) via test/harness.py', 'units': 'metres, three.js axes (y up)', 'prep': info['report'], 'wings': {}}
        for k in WINGS:
            if k not in info['wings']:
                continue
            r = await page.evaluate(EXPORT, k)
            n = r['size']
            if not n:
                continue
            data = bytearray()
            step = 4 << 20
            for a in range(0, n, step):
                data += base64.b64decode(await page.evaluate(CHUNK, [a, min(n, a + step)]))
            fp = os.path.join(OUT, k + '.glb')
            with open(fp, 'wb') as f:
                f.write(data)
            manifest['wings'][k] = {'file': k + '.glb', 'bytes': n}
            print('wrote', fp, n)
        # Exhibit artwork (posters drawn on canvases) as PNGs for the catalog cards in Unreal
        art_dir = os.path.join(OUT, 'art')
        os.makedirs(art_dir, exist_ok=True)
        keys = await page.evaluate("() => Object.keys(window.__test.ART).filter((k) => { const c = window.__test.ART[k]; return c && c.width > 1 && c.toDataURL; })")
        for key in keys:
            url = await page.evaluate("(k) => window.__test.ART[k].toDataURL('image/png')", key)
            with open(os.path.join(art_dir, key + '.png'), 'wb') as f:
                f.write(base64.b64decode(url.split(',', 1)[1]))
        manifest['art'] = sorted(keys)
        print('wrote', len(keys), 'exhibit art PNGs')
        with open(os.path.join(OUT, 'props_rest.json'), 'w') as f:
            json.dump({'units': 'stage-local metres, three.js axes (y up), relative to the stage group (StageLocation/StageYaw)',
                       'props': info.get('props_rest', [])}, f, indent=1)
        with open(os.path.join(OUT, 'lights.json'), 'w') as f:
            json.dump({'units': 'metres, three.js axes (y up)', 'lamps': info['lamps'], 'sun': info['sun']}, f, indent=1)
        with open(os.path.join(OUT, 'manifest.json'), 'w') as f:
            json.dump(manifest, f, indent=1)
        errs = [l for l in logs if 'PAGEERROR' in l or l.startswith('error')]
        print('console errors:', len(errs))
        for l in errs[:20]:
            print('  ', l[:300])
        await b.close()


if __name__ == '__main__':
    asyncio.run(main())
