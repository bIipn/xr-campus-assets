/* ================================================================
   Graphics: quality levels, sun shadows, sky, image-based light,
   physically based materials and post effects
   ================================================================ */
const QUALITY = {
  high:   { label:'High',   dpr:1.5,  shadow:2048, ext:34, ao:true,  bloom:true,  msaa:4, fxaa:false, grass:46000, patch:46, leaves:30 },
  medium: { label:'Medium', dpr:1.35, shadow:1024, ext:26, ao:false, bloom:true,  msaa:0, fxaa:true,  grass:17000, patch:36, leaves:22 },
  low:    { label:'Low',    dpr:1.0,  shadow:0,    ext:0,  ao:false, bloom:false, msaa:0, fxaa:false, grass:5000,  patch:26, leaves:14 }
};
const GFX = { tier:'high', pref:'high', composer:null, passes:{}, pmrem:null, envOut:null, envIn:null, envMode:'', envFade:1,
  skyMat:null, t:0, slowT:0, sampleT:0, frames:0, w:1, h:1, dropped:false, scale:1 };
const SUN_I = 3.1, HEMI_OUT = 0.55, HEMI_IN = 0.32, ENV_OUT = 0.95, ENV_IN = 0.8, EXPOSURE = 1.0;
const SKY_COL = { zenith:[0.105, 0.30, 0.68], horizon:[0.62, 0.77, 0.88], ground:[0.40, 0.46, 0.40], sun:[1.0, 0.86, 0.64] };

/* High is the default on every device: phones and headsets included. The level never changes on its own;
   when frames run slow the renderer draws slightly fewer pixels instead (see gfxFrame).
   Choices saved before High became the default lived under the old key and are ignored, so everyone starts on High. */
const GFX_KEY = 'xr-campus-gfx2';
function gfxDefaultTier(){ return 'high'; }
/* High is the default. If the last visit in this tab ended in a crash or a lost GPU context,
   this visit starts one step lower so it cannot crash in a loop; the saved choice is left alone. */
const GFX_BEAT = 'xr-campus-beat', GFX_LOST = 'xr-campus-lost';
function gfxLoadPref(){
  try { const p = localStorage.getItem(GFX_KEY); if (p && QUALITY[p]) GFX.pref = p; } catch (_) {}
  GFX.tier = GFX.pref; GFX.eased = false;
  try {
    const beat = +sessionStorage.getItem(GFX_BEAT) || 0, lost = sessionStorage.getItem(GFX_LOST);
    sessionStorage.removeItem(GFX_LOST);
    if ((lost || (beat && Date.now() - beat < 90000)) && GFX.tier !== 'low'){ GFX.tier = GFX.tier === 'high' ? 'medium' : 'low'; GFX.eased = true; }
  } catch (_) {}
  gfxBeat();
  setInterval(gfxBeat, 4000);
  addEventListener('pagehide', () => { try { sessionStorage.removeItem(GFX_BEAT); } catch (_) {} });
  addEventListener('pageshow', gfxBeat);
}
function gfxBeat(){ try { sessionStorage.setItem(GFX_BEAT, String(Date.now())); } catch (_) {} }
function gfxLostReload(){ try { sessionStorage.setItem(GFX_LOST, '1'); sessionStorage.removeItem(GFX_BEAT); } catch (_) {} location.reload(); }
function gfxSavePref(p){ GFX.pref = p; try { localStorage.setItem(GFX_KEY, p); } catch (_) {} }
const Q = () => QUALITY[GFX.tier];

/* Renderer basics, right after it is created */
function gfxInitRenderer(){
  gfxLoadPref();
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = EXPOSURE;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  GFX.pmrem = new THREE.PMREMGenerator(renderer);
}

/* ---------- Sky: gradient, sun and drifting clouds ---------- */
const SKY_GLSL = `
uniform vec3 uSunDir; uniform float uTime; uniform vec3 uZenith; uniform vec3 uHorizon; uniform vec3 uGround; uniform vec3 uSunCol; uniform float uClouds;
varying vec3 vDir;
float h21(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
float vnoise(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(h21(i), h21(i + vec2(1.0, 0.0)), f.x), mix(h21(i + vec2(0.0, 1.0)), h21(i + vec2(1.0, 1.0)), f.x), f.y); }
float fbm(vec2 p){ float a = 0.5, s = 0.0; for (int i = 0; i < 5; i++){ s += a * vnoise(p); p = p * 2.03 + vec2(17.1, 9.2); a *= 0.5; } return s; }
vec3 skyColor(vec3 d){
  float h = d.y;
  vec3 c = mix(uHorizon, uZenith, pow(clamp(h, 0.0, 1.0), 0.5));
  c = mix(c, uGround, smoothstep(0.0, -0.12, h));
  float sd = max(dot(d, uSunDir), 0.0);
  c += uSunCol * (pow(sd, 900.0) * 40.0 + pow(sd, 24.0) * 0.45 + pow(sd, 4.0) * 0.12);
  if (h > 0.0 && uClouds > 0.0){
    vec2 uv = d.xz / (h + 0.12) * 0.85 + vec2(uTime * 0.006, uTime * 0.0025);
    float n = fbm(uv * 1.15), cov = smoothstep(0.50, 0.80, n) * uClouds;
    float lit = 0.72 + 0.4 * pow(sd, 3.0) + 0.18 * smoothstep(0.55, 0.9, fbm(uv * 1.15 + uSunDir.xz * 0.06));
    vec3 cc = vec3(0.92, 0.95, 1.0) * lit * 1.05;
    c = mix(c, cc, cov * smoothstep(0.0, 0.22, h) * 0.92);
  }
  return c;
}`;
function makeSkyMaterial(clouds){
  return new THREE.ShaderMaterial({
    uniforms:{ uSunDir:{ value:new THREE.Vector3(SUN_DIR[0], SUN_DIR[1], SUN_DIR[2]).normalize() }, uTime:{ value:0 },
      uZenith:{ value:new THREE.Vector3(...SKY_COL.zenith) }, uHorizon:{ value:new THREE.Vector3(...SKY_COL.horizon) },
      uGround:{ value:new THREE.Vector3(...SKY_COL.ground) }, uSunCol:{ value:new THREE.Vector3(...SKY_COL.sun) }, uClouds:{ value:clouds == null ? 1 : clouds } },
    vertexShader:'varying vec3 vDir;\nvoid main(){ vDir = position; vec4 p = projectionMatrix * modelViewMatrix * vec4(position, 1.0); gl_Position = p.xyww; }',
    fragmentShader:SKY_GLSL + '\nvoid main(){ gl_FragColor = vec4(skyColor(normalize(vDir)), 1.0);\n#include <tonemapping_fragment>\n#include <colorspace_fragment>\n}',
    side:THREE.BackSide, depthWrite:false, depthTest:false, fog:false
  });
}
function gfxSky(){
  if (!SKY) return;
  GFX.skyMat = makeSkyMaterial(1);
  SKY.material.dispose(); SKY.material = GFX.skyMat;
  const hz = SKY_COL.horizon, fc = new THREE.Color().setRGB(hz[0] * 0.96, hz[1] * 0.97, hz[2], THREE.LinearSRGBColorSpace);
  scene.fog = new THREE.Fog(fc, 70, 245);
}

/* ---------- Image-based light: the sky outdoors, a warm room indoors ---------- */
function gfxEnvMaps(){
  const pm = GFX.pmrem;
  const skyScene = new THREE.Scene(), skyBall = new THREE.Mesh(new THREE.SphereGeometry(50, 32, 16), makeSkyMaterial(0.6));
  skyBall.material.depthTest = true; skyScene.add(skyBall);
  const grd = new THREE.Mesh(new THREE.CircleGeometry(48, 32), new THREE.MeshBasicMaterial({ color:new THREE.Color().setRGB(0.16, 0.22, 0.11, THREE.LinearSRGBColorSpace) }));
  grd.rotation.x = -Math.PI / 2; grd.position.y = -2; skyScene.add(grd);
  GFX.envOut = pm.fromScene(skyScene, 0.02, 0.1, 200).texture;
  const room = new THREE.Scene(), lin = (r, g, b, k) => new THREE.MeshBasicMaterial({ color:new THREE.Color().setRGB(r * (k || 1), g * (k || 1), b * (k || 1), THREE.LinearSRGBColorSpace), side:THREE.BackSide });
  const box = new THREE.Mesh(new THREE.BoxGeometry(24, 9, 24), [lin(0.34, 0.27, 0.2), lin(0.34, 0.27, 0.2), lin(0.42, 0.37, 0.3), lin(0.12, 0.08, 0.05), lin(0.33, 0.27, 0.21), lin(0.33, 0.27, 0.21)]);
  box.position.y = 3.5; room.add(box);
  for (const [x, z] of [[-5, -5], [5, -5], [-5, 5], [5, 5], [0, 0]]){ const p = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 3.2), lin(1.0, 0.86, 0.68, 5.5)); p.rotation.x = Math.PI / 2; p.position.set(x, 7.9, z); room.add(p); }
  for (const s of [-1, 1]){ const wdw = new THREE.Mesh(new THREE.PlaneGeometry(7, 3.5), lin(0.75, 0.85, 1.0, 2.4)); wdw.position.set(s * 11.9, 4.2, 0); wdw.rotation.y = -s * Math.PI / 2; room.add(wdw); }
  GFX.envIn = pm.fromScene(room, 0.035, 0.1, 100).texture;
  skyBall.geometry.dispose(); skyBall.material.dispose(); box.geometry.dispose();
}
function gfxOutdoor(){
  if (ride.on && ride.on !== 'dive') return true;
  const r = roomAt(cam.x, cam.z).id;
  return r === 'yard' || (r === 'school' && cam.x > 31.5);
}
function gfxSetEnv(mode){
  if (GFX.envMode === mode) return;
  GFX.envMode = mode;
  scene.environment = mode === 'out' ? GFX.envOut : mode === 'in' ? GFX.envIn : null;
  GFX.envFade = 0.45;
}

/* ---------- Lights: physical units, the sun casts soft shadows ---------- */
const _sl = { dir:null, x:null, y:null, c:null };
/* Point lights behave like small glowing globes rather than infinitely small points */
function gfxSoftLights(){
  const k = 'lights_pars_begin', a = 'float distanceFalloff = 1.0 / max( pow( lightDistance, decayExponent ), 0.01 );';
  if (THREE.ShaderChunk && THREE.ShaderChunk[k] && THREE.ShaderChunk[k].includes(a))
    THREE.ShaderChunk[k] = THREE.ShaderChunk[k].replace(a, 'float distanceFalloff = 1.0 / ( pow( lightDistance, decayExponent ) + 0.64 );');
}
function gfxLights(){
  gfxSoftLights();
  scene.updateMatrixWorld(true);
  const solids = [], ray = new THREE.Raycaster(), up = new THREE.Vector3(0, 1, 0);
  scene.traverse((o) => { if (o.isMesh && o.visible && o.material && !o.material.transparent) solids.push(o); });
  scene.traverse((o) => {
    if (!o.isPointLight) return;
    /* A gentle 1/d falloff reads like a game's baked room light; true 1/d^2 burns walls near the lamp and leaves corners black */
    o.decay = 1; o.intensity = o.intensity * 10; o.distance = Math.max(o.distance, 22);
    /* Keep at least 1.1 m between a lamp and the ceiling above it so the ceiling doesn't burn white */
    ray.set(o.getWorldPosition(new THREE.Vector3()), up); ray.far = 4;
    const hit = ray.intersectObjects(solids, false)[0];
    if (hit && hit.distance < 1.1) o.position.y -= 1.1 - hit.distance;
  });
  gfxLampPool();
  if (LIGHTS.amb) LIGHTS.amb.intensity = 0;
  if (LIGHTS.hemi){ LIGHTS.hemi.color.set(0xd9e8ff); LIGHTS.hemi.groundColor.set(0x6a5a46); LIGHTS.hemi.intensity = HEMI_IN; }
  const s = LIGHTS.sun; if (!s) return;
  s.color.set(0xfff0dc); scene.add(s.target);
  s.shadow.camera.near = 1; s.shadow.camera.far = 320;
  s.shadow.bias = -0.0004; s.shadow.normalBias = 0.035;
  _sl.dir = new THREE.Vector3(SUN_DIR[0], SUN_DIR[1], SUN_DIR[2]).normalize();
  _sl.x = new THREE.Vector3().crossVectors(new THREE.Vector3(0, 1, 0), _sl.dir).normalize();
  _sl.y = new THREE.Vector3().crossVectors(_sl.dir, _sl.x).normalize();
  _sl.c = new THREE.Vector3();
  gfxShadowSize();
}
/* A fixed pool of lamps. Every lit pixel pays for every lamp in the scene, and changing how many
   lamps there are rebuilds shaders, so the campus keeps 8 and moves them to the rooms you can see. */
const LAMPS = { K:8, all:[], pool:[], key:'' };
function lampWing(x, z){
  const r = roomAt(x, z).id;
  if (r === 'wax' && z < -44.4) return 'wax';
  if (['lobby', 'g1', 'g2', 'g3', 'hallR', 'wax'].includes(r)) return 'museum';
  if (['hallL', 'lib', 'libAisle'].includes(r)) return 'lib';
  if (['school', 'studio', 'lab', 'blueprint', 'world'].includes(r)) return 'school';
  return 'play';
}
function gfxLampPool(){
  const lights = []; scene.traverse((o) => { if (o.isPointLight) lights.push(o); });
  LAMPS.all = lights.map((l) => { const p = l.getWorldPosition(new THREE.Vector3()); return { p, color:l.color.clone(), intensity:l.intensity, distance:l.distance, decay:l.decay, wing:lampWing(p.x, p.z) }; });
  LAMPS.pool = lights.slice(0, LAMPS.K);
  for (const l of lights.slice(LAMPS.K)) l.parent.remove(l);
  for (const l of LAMPS.pool) if (l.parent !== scene) scene.attach(l);
  LAMPS.key = '';
  gfxLampFrame(true);
}
function gfxLampFrame(force){
  if (!LAMPS.pool.length || !camera) return;
  const cp = camera.position, vis = (k) => !!(WING[k] && WING[k].visible);
  const key = Math.round(cp.x) + ',' + Math.round(cp.z) + '|' + (vis('museum') ? 1 : 0) + (vis('wax') ? 1 : 0) + (vis('lib') ? 1 : 0) + (vis('school') ? 1 : 0) + (vis('play') ? 1 : 0);
  if (!force && key === LAMPS.key) return;
  LAMPS.key = key;
  const ranked = LAMPS.all.map((L) => ({ L, s:L.p.distanceTo(cp) + (vis(L.wing) ? 0 : 200) })).sort((a, b) => a.s - b.s);
  LAMPS.pool.forEach((l, i) => {
    const r = ranked[i]; if (!r){ l.intensity = 0; return; }
    const L = r.L; l.position.copy(L.p); l.color.copy(L.color); l.intensity = L.intensity; l.distance = L.distance; l.decay = L.decay;
  });
}
function gfxShadowSize(){
  const s = LIGHTS.sun, q = Q(); if (!s) return;
  const on = q.shadow > 0;
  s.castShadow = on;
  if (!on) return;
  if (s.shadow.mapSize.x !== q.shadow){ s.shadow.mapSize.set(q.shadow, q.shadow); if (s.shadow.map){ s.shadow.map.dispose(); s.shadow.map = null; } }
  const c = s.shadow.camera; c.left = c.bottom = -q.ext; c.right = c.top = q.ext; c.updateProjectionMatrix();
}
/* Keep the shadow box centred a little ahead of the camera, snapped to whole shadow texels so edges don't crawl */
function gfxSunFollow(){
  const s = LIGHTS.sun; if (!s || !s.castShadow || !_sl.dir) return;
  const q = Q(), p = camera.position, ext = q.ext, fx = -Math.sin(camera.rotation.y), fz = -Math.cos(camera.rotation.y);
  const c = _sl.c.set(p.x + fx * ext * 0.4, Math.min(p.y, 6), p.z + fz * ext * 0.4);
  const texel = (2 * ext) / q.shadow, a = Math.round(c.dot(_sl.x) / texel) * texel, b = Math.round(c.dot(_sl.y) / texel) * texel, d = c.dot(_sl.dir);
  c.copy(_sl.x).multiplyScalar(a).addScaledVector(_sl.y, b).addScaledVector(_sl.dir, d);
  s.target.position.copy(c); s.position.copy(c).addScaledVector(_sl.dir, 150);
  s.target.updateMatrixWorld();
}

/* ---------- Materials: everything lit becomes physically based ---------- */
const NRM = new WeakMap();
function normalCanvas(src, strength){
  if (NRM.has(src)){ const c = NRM.get(src); return c && c.__released ? null : c; }
  if (src.__released) return null;
  let cv = src;
  if (src.width > 512 || src.height > 512){ const k = 512 / Math.max(src.width, src.height); cv = document.createElement('canvas'); cv.width = Math.max(4, Math.round(src.width * k)); cv.height = Math.max(4, Math.round(src.height * k)); cv.getContext('2d').drawImage(src, 0, 0, cv.width, cv.height); }
  const w = cv.width, h = cv.height;
  let data; try { data = cv.getContext('2d').getImageData(0, 0, w, h).data; } catch (_) { NRM.set(src, null); return null; }
  if (cv !== src){ cv.width = 1; cv.height = 1; }
  const H = new Float32Array(w * h);
  for (let i = 0, j = 0; i < H.length; i++, j += 4) H[i] = (data[j] * 0.299 + data[j + 1] * 0.587 + data[j + 2] * 0.114) / 255;
  const out = document.createElement('canvas'); out.width = w; out.height = h;
  const o = out.getContext('2d'), img = o.createImageData(w, h), d = img.data, k = strength * Math.max(w, h) / 128;
  for (let y = 0; y < h; y++){
    const yu = ((y - 1 + h) % h) * w, yd = ((y + 1) % h) * w, yr = y * w;
    for (let x = 0; x < w; x++){
      const xl = (x - 1 + w) % w, xr = (x + 1) % w;
      const dx = (H[yr + xr] - H[yr + xl]) * k, dy = (H[yd + x] - H[yu + x]) * k;
      const inv = 1 / Math.sqrt(dx * dx + dy * dy + 1), p = (yr + x) * 4;
      d[p] = (-dx * inv * 0.5 + 0.5) * 255; d[p + 1] = (dy * inv * 0.5 + 0.5) * 255; d[p + 2] = (inv * 0.5 + 0.5) * 255; d[p + 3] = 255;
    }
  }
  o.putImageData(img, 0, 0);
  NRM.set(src, out); return out;
}
function addNormalMap(m, strength){
  const t = m.map;
  if (m.normalMap || !t || !t.image || !(t.image instanceof HTMLCanvasElement) || t.wrapS !== THREE.RepeatWrapping) return;
  const cv = normalCanvas(t.image, strength || 1.6); if (!cv) return;
  const n = leanTex(new THREE.CanvasTexture(cv));
  n.wrapS = n.wrapT = THREE.RepeatWrapping; n.repeat.copy(t.repeat); n.offset.copy(t.offset); n.rotation = t.rotation; n.center.copy(t.center);
  n.anisotropy = t.anisotropy; n.colorSpace = THREE.NoColorSpace;
  m.normalMap = n; m.normalScale.set(0.85, 0.85); m.needsUpdate = true;
}
function gfxUpgradeScene(skip){
  const conv = new Map();
  const lam = (m) => {
    const n = new THREE.MeshStandardMaterial({ color:m.color, map:m.map, emissive:m.emissive, emissiveMap:m.emissiveMap, emissiveIntensity:m.emissiveIntensity,
      alphaTest:m.alphaTest, side:m.side, transparent:m.transparent, opacity:m.opacity, vertexColors:m.vertexColors, roughness:0.9, metalness:0 });
    return n;
  };
  const panel = (m) => new THREE.MeshStandardMaterial({ color:m.color, map:m.map, emissive:0xffffff, emissiveMap:m.map, emissiveIntensity:0.3,
    alphaTest:m.alphaTest, side:m.side, roughness:0.82, metalness:0 });
  const walk = (o) => {
    if (o === SKY || skip.has(o)) return;
    if (o.isMesh && o.material && !Array.isArray(o.material)){
      const m = o.material;
      let n = conv.get(m);
      if (!n){
        n = m;
        if (m.isMeshLambertMaterial && m.onBeforeCompile === THREE.Material.prototype.onBeforeCompile) n = lam(m);
        else if (m.isMeshBasicMaterial && m.map && !m.transparent && m.blending === THREE.NormalBlending && !o.userData.keepBasic) n = panel(m);
        else if (m.isMeshBasicMaterial && !m.map && !m.userData.boosted && m.blending === THREE.NormalBlending){
          const l = m.color.r * 0.2126 + m.color.g * 0.7152 + m.color.b * 0.0722;
          if (l > 0.45) m.color.multiplyScalar(3.2);
          m.userData.boosted = true;
        }
        if (n.isMeshStandardMaterial) addNormalMap(n);
        conv.set(m, n);
      }
      o.material = n;
      if (n.isMeshStandardMaterial){
        o.receiveShadow = true;
        if (!n.transparent && !o.userData.noShadow) o.castShadow = true;
      }
    }
    for (const c of o.children) walk(c);
  };
  walk(scene);
}

/* ---------- Post effects ---------- */
const GRADE_SHADER = {
  uniforms:{ tDiffuse:{ value:null }, uSat:{ value:1.12 }, uVig:{ value:0.32 }, uLift:{ value:0.012 } },
  vertexShader:'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  fragmentShader:'uniform sampler2D tDiffuse; uniform float uSat; uniform float uVig; uniform float uLift; varying vec2 vUv;\n' +
    'void main(){ vec4 c = texture2D(tDiffuse, vUv); float l = dot(c.rgb, vec3(0.2126, 0.7152, 0.0722)); c.rgb = max(mix(vec3(l), c.rgb, uSat), 0.0);\n' +
    ' vec2 d = vUv - 0.5; c.rgb *= 1.0 - uVig * dot(d, d) * 1.7; c.rgb += uLift * vec3(0.9, 0.95, 1.0); gl_FragColor = c; }'
};
function aoSkip(o){
  if (!o.isMesh || o.userData.noAO) return !!o.userData.noAO;
  const m = o.material;
  if (Array.isArray(m)) return m.some((x) => x.transparent || x.blending !== THREE.NormalBlending);
  return !m || m.transparent || m.blending !== THREE.NormalBlending || m.isShaderMaterial;
}
function gfxComposer(){
  const P = GFX.passes;
  if (GFX.composer){ GFX.composer.renderTarget1.dispose(); GFX.composer.renderTarget2.dispose(); for (const k in P) if (P[k] && P[k].dispose) P[k].dispose(); }
  GFX.composer = null; for (const k in P) delete P[k];
  const q = Q();
  if (GFX.tier === 'low' || !XT.EffectComposer) return;
  const rt = new THREE.WebGLRenderTarget(4, 4, { type:THREE.HalfFloatType, samples:q.msaa });
  const comp = new XT.EffectComposer(renderer, rt);
  P.render = new XT.RenderPass(scene, camera); comp.addPass(P.render);
  if (q.ao && XT.GTAOPass){
    P.ao = new XT.GTAOPass(scene, camera, 4, 4);
    P.ao.updateGtaoMaterial({ radius:0.55, distanceExponent:1.4, thickness:1.2, scale:1.0, samples:12, distanceFallOff:1.0, screenSpaceRadius:false });
    P.ao.updatePdMaterial({ lumaPhi:10, depthPhi:2, normalPhi:3, radius:5, rings:2, samples:12 });
    P.ao.blendIntensity = 0.85;
    /* Only solid surfaces cast ambient occlusion: sprites, glass, glows, sky and grass stay out of the depth pass */
    P.ao.overrideVisibility = function(){
      const cache = this._visibilityCache, hide = GFX.aoHide || [];
      this.scene.traverse((o) => { cache.set(o, o.visible); if (o.isPoints || o.isLine || o.isSprite || hide.includes(o) || aoSkip(o)) o.visible = false; });
    };
    comp.addPass(P.ao);
  }
  if (q.bloom && XT.UnrealBloomPass){ P.bloom = new XT.UnrealBloomPass(new THREE.Vector2(256, 256), 0.3, 0.42, 1.2); comp.addPass(P.bloom); }
  if (XT.ShaderPass){ P.grade = new XT.ShaderPass(GRADE_SHADER); comp.addPass(P.grade); }
  P.out = new XT.OutputPass(); comp.addPass(P.out);
  if (q.fxaa && XT.ShaderPass && XT.FXAAShader){ P.fxaa = new XT.ShaderPass(XT.FXAAShader); comp.addPass(P.fxaa); }
  GFX.composer = comp;
  gfxSize();
}
/* The lowest resolution scale: one rendered pixel per screen point, so text and edges never turn soft */
function gfxMinScale(){ return Math.min(1, 1 / Math.min(window.devicePixelRatio || 1, Q().dpr)); }
function gfxSize(){
  const q = Q(), w = window.innerWidth, h = window.innerHeight, pr = Math.min(window.devicePixelRatio || 1, q.dpr) * GFX.scale;
  GFX.w = w; GFX.h = h;
  renderer.setPixelRatio(pr); renderer.setSize(w, h, false);
  if (GFX.composer){
    GFX.composer.setPixelRatio(pr); GFX.composer.setSize(w, h);
    if (GFX.passes.bloom) GFX.passes.bloom.setSize(Math.round(w * pr / 2), Math.round(h * pr / 2));
    if (GFX.passes.fxaa) GFX.passes.fxaa.material.uniforms.resolution.value.set(1 / (w * pr), 1 / (h * pr));
  }
}
function gfxApplyTier(t){
  if (!QUALITY[t]) return;
  GFX.tier = t;
  gfxShadowSize();
  gfxComposer();
  if (typeof natureTier === 'function') natureTier();
  GFX.slowT = 0; GFX.sampleT = 0; GFX.frames = 0;
  gfxSize(); renderGfx();
  wake();
}

/* ---------- Every frame ---------- */
function gfxLive(){ return !!(WING.outside && WING.outside.visible) && !REDUCED && !document.hidden && ride.on !== 'dive'; }
function gfxFrame(dt, cont){
  GFX.t += dt;
  if (GFX.skyMat && !REDUCED) GFX.skyMat.uniforms.uTime.value = GFX.t;
  if (ride.on === 'dive') gfxSetEnv('none');
  else gfxSetEnv(gfxOutdoor() ? 'out' : 'in');
  let busy = false;
  if (GFX.envFade < 1){ GFX.envFade = Math.min(1, GFX.envFade + dt * 1.6); busy = true; }
  gfxSunFollow();
  gfxLampFrame(false);
  /* Like a game's dynamic resolution: while frames run slow (under ~30 per second), draw a few fewer
     pixels, never fewer than one per screen point, and creep back up when there's headroom. Effects,
     shadows and grass stay as chosen. Only measured while frames run back to back, so idle pauses don't count. */
  if (cont && dt > 0 && dt < 0.25 && !document.hidden){
    GFX.sampleT += dt; GFX.frames++;
    if (GFX.sampleT > 2){
      const avg = GFX.sampleT / GFX.frames, floor = gfxMinScale();
      GFX.sampleT = 0; GFX.frames = 0;
      if (avg > 1 / 30 && GFX.scale > floor + 0.005){ GFX.scale = Math.max(floor, GFX.scale * 0.88); gfxSize(); }
      else if (avg < 1 / 50 && GFX.scale < 1){ GFX.scale = Math.min(1, GFX.scale / 0.92); gfxSize(); }
    }
  }
  return busy || gfxLive();
}
function gfxRender(){
  if (XR.on) renderer.render(scene, camera);
  else if (GFX.composer) GFX.composer.render();
  else renderer.render(scene, camera);
}
