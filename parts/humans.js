/* ================================================================
   Realistic people
   Bodies, faces, clothes and hair come from Microsoft Rocketbox
   (MIT License, Copyright (c) 2020 Microsoft): photo-textured avatars
   with an 80-bone rig that includes eyes, lids, jaw and lips. Each
   skeleton is rebuilt here so arms and legs hang straight at rest, the
   pose language the wax scenes are written in. Avatars load on demand;
   a figure's bones exist at once, so props can be attached right away.
   ================================================================ */
const HB = {}; HK_RIG.names.forEach((n, i) => { HB[n.replace(/^Bip01_/, '')] = i; });
const HK_N = HK_RIG.names.length;
/* b64: the Claude artifact host only serves web file types, so there the avatar files ship as base64 text (.hk.txt) */
const HK = { base:'h/', b64:false, assets:new Map(), rigs:new Map(), dec:null, figs:[], mats:new Map(), lazy:{}, want:{} };
/* The 17 control joints the wax poses drive, in WAXB order */
const HK_CTRL = ['Pelvis', 'Spine', 'Spine1', 'Neck', 'Head', 'L_UpperArm', 'L_Forearm', 'L_Hand', 'R_UpperArm', 'R_Forearm', 'R_Hand', 'L_Thigh', 'L_Calf', 'L_Foot', 'R_Thigh', 'R_Calf', 'R_Foot'];
/* A relaxed hand: degrees per joint for thumb, index, middle, ring, little */
const HK_CURL = [[6, 10, 8], [10, 14, 8], [13, 17, 10], [17, 18, 12], [21, 20, 14]];

function hkTier(){ return GFX.tier === 'high' && !LEAN_CANVAS ? 'hi' : 'lo'; }
function hkB64(s){
  s = s.replace(/\s+/g, '');
  if (Uint8Array.fromBase64) return Uint8Array.fromBase64(s).buffer;
  const bin = atob(s), n = bin.length, u = new Uint8Array(n);
  for (let i = 0; i < n; i++) u[i] = bin.charCodeAt(i);
  return u.buffer;
}
function hkDecoder(){
  if (!HK.dec) HK.dec = import('three/addons/libs/meshopt_decoder.module.js').then(async (m) => { await m.MeshoptDecoder.ready; return m.MeshoptDecoder; });
  return HK.dec;
}

/* ---------- One avatar's mesh and textures, shared by every figure that uses it ---------- */
function hkAsset(id){
  let p = HK.assets.get(id);
  if (p) return p;
  p = (async () => {
    const r = await fetch(HK.base + id + '.' + hkTier() + (HK.b64 ? '.hk.txt' : '.hk'));
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const buf = HK.b64 ? hkB64(await r.text()) : await r.arrayBuffer(), dv = new DataView(buf);
    if (dv.getUint32(0, true) !== 0x31304b48) throw new Error('not an avatar file');
    const hl = dv.getUint32(4, true), H = JSON.parse(new TextDecoder().decode(new Uint8Array(buf, 8, hl))), base = 8 + hl;
    const D = await hkDecoder(), n = H.vc, vs = H.vs;
    const vb = new Uint8Array(n * vs), ib = new Uint16Array(H.ic);
    D.decodeVertexBuffer(vb, n, vs, new Uint8Array(buf, base + H.vb[0], H.vb[1]));
    D.decodeIndexBuffer(new Uint8Array(ib.buffer), H.ic, 2, new Uint8Array(buf, base + H.ib[0], H.ib[1]));
    const v = new DataView(vb.buffer), pos = new Float32Array(n * 3), nrm = new Float32Array(n * 3), uv = new Float32Array(n * 2), si = new Uint8Array(n * 4), sw = new Uint8Array(n * 4);
    for (let i = 0; i < n; i++){
      const o = i * vs, a = i * 3;
      pos[a] = v.getInt16(o, true) / 10000; pos[a + 1] = v.getInt16(o + 2, true) / 10000; pos[a + 2] = v.getInt16(o + 4, true) / 10000;
      let nx = v.getInt8(o + 6), ny = v.getInt8(o + 7), nz = v.getInt8(o + 8); const l = Math.hypot(nx, ny, nz) || 1;
      nrm[a] = nx / l; nrm[a + 1] = ny / l; nrm[a + 2] = nz / l;
      uv[i * 2] = v.getUint16(o + 10, true) / 65535; uv[i * 2 + 1] = v.getUint16(o + 12, true) / 65535;
      for (let k = 0; k < 4; k++){ si[i * 4 + k] = vb[o + 14 + k]; sw[i * 4 + k] = vb[o + 18 + k]; }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('normal', new THREE.BufferAttribute(nrm, 3));
    g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    g.setAttribute('skinIndex', new THREE.BufferAttribute(si, 4));
    g.setAttribute('skinWeight', new THREE.BufferAttribute(sw, 4, true));
    g.setIndex(new THREE.BufferAttribute(ib, 1));
    let s = 0; H.mats.forEach((m, k) => { if (m.n) g.addGroup(s, m.n, k); s += m.n; });
    const isNrm = new Set(H.mats.map((m) => m.nm).filter((i) => i >= 0));
    const tex = await Promise.all(H.tex.map(async ([o, len], i) => {
      const bmp = await createImageBitmap(new Blob([new Uint8Array(buf, base + o, len)], { type:'image/webp' }), { premultiplyAlpha:'none', colorSpaceConversion:'none' });
      const t = new THREE.Texture(bmp);
      t.flipY = false; t.colorSpace = isNrm.has(i) ? THREE.NoColorSpace : THREE.SRGBColorSpace;
      t.anisotropy = LEAN_CANVAS ? 2 : 4; t.needsUpdate = true; t.userData.hk = true;
      /* Phones keep only the GPU copy; a lost context reloads the page anyway */
      if (LEAN_CANVAS) t.onUpdate = () => { const d = t.source.data; if (d && d.close){ d.close(); } t.onUpdate = null; };
      return t;
    }));
    return { id, geo:g, tex, mats:H.mats, h:H.h };
  })();
  HK.assets.set(id, p);
  p.catch((e) => { console.warn('A person could not load (' + id + '):', e && e.message); });
  return p;
}

/* ---------- Rig: straight arms and legs at rest, curl axes, face points ---------- */
function hkRig(id){
  let R = HK.rigs.get(id);
  if (R) return R;
  const A = HK_RIG.avatars[id], n = HK_N, par = HK_RIG.parents.slice();
  par[HB.L_Thigh] = HB.Pelvis; par[HB.R_Thigh] = HB.Pelvis;
  const J = []; for (let i = 0; i < n; i++) J.push(new THREE.Vector3(A.j[i * 3], A.j[i * 3 + 1], A.j[i * 3 + 2]).multiplyScalar(0.001));
  const Q = J.map(() => new THREE.Quaternion()), down = new THREE.Vector3(0, -1, 0), d = new THREE.Vector3(), q = new THREE.Quaternion();
  const below = (root) => { const out = []; for (let i = 0; i < n; i++){ let p = par[i]; while (p >= 0 && p !== root) p = par[p]; if (p === root) out.push(i); } return out; };
  const toDown = (a, b, base) => { d.subVectors(J[b], J[a]).normalize().applyQuaternion(base); return q.setFromUnitVectors(d, down).clone().multiply(base); };
  for (const s of ['L', 'R']){
    const ua = HB[s + '_UpperArm'], fa = HB[s + '_Forearm'], hd = HB[s + '_Hand'];
    Q[ua] = toDown(ua, fa, new THREE.Quaternion());
    Q[fa] = toDown(fa, hd, Q[ua]);
    Q[hd] = Q[fa].clone(); for (const k of below(hd)) Q[k] = Q[fa].clone();
    const th = HB[s + '_Thigh'], ca = HB[s + '_Calf'], ft = HB[s + '_Foot'];
    Q[th] = toDown(th, ca, new THREE.Quaternion());
    Q[ca] = toDown(ca, ft, Q[th]);
    Q[ft] = Q[ca].clone(); for (const k of below(ft)) Q[k] = Q[ca].clone();
  }
  const order = [], visit = (i) => { order.push(i); for (let k = 0; k < n; k++) if (par[k] === i) visit(k); };
  for (let i = 0; i < n; i++) if (par[i] < 0) visit(i);
  const P = J.map((j) => j.clone());
  for (const i of order){ const p = par[i]; if (p >= 0) P[i].copy(J[i]).sub(J[p]).applyQuaternion(Q[p]).add(P[p]); }
  /* Finger curl axes in the rest frame: bending moves a finger toward the palm */
  const curl = {};
  for (const s of ['L', 'R']){
    const f = (k, j) => HB[s + '_Finger' + k + (j ? j : '')];
    const across = new THREE.Vector3().subVectors(P[f(4)], P[f(1)]).normalize();
    const along = new THREE.Vector3().subVectors(P[f(2, 1)], P[f(2)]).normalize();
    const palm = new THREE.Vector3().crossVectors(across, along).normalize().multiplyScalar(s === 'L' ? 1 : -1);
    curl[s] = [0, 1, 2, 3, 4].map((k) => {
      const dir = new THREE.Vector3().subVectors(P[f(k, 1)], P[f(k)]).normalize();
      return new THREE.Vector3().crossVectors(dir, palm).normalize();
    });
  }
  /* Bind inverses (unscaled): rotate the A-pose mesh onto the straight rest pose */
  const inv = J.map((j, i) => new THREE.Matrix4().makeRotationFromQuaternion(Q[i]).multiply(new THREE.Matrix4().makeTranslation(-j.x, -j.y, -j.z)));
  const eyeMid = new THREE.Vector3().addVectors(P[HB.LEye], P[HB.REye]).multiplyScalar(0.5);
  R = { id, J, P, Q, par, order, inv, curl, h:A.h, eyeMid };
  HK.rigs.set(id, R);
  return R;
}

/* ---------- Materials ---------- */
/* Skin keeps a little light inside: wrapped diffuse with a warm scatter tint, plus a soft sheen */
function hkSkinPatch(m, wax){
  m.onBeforeCompile = (sh) => {
    sh.uniforms.hkWrap = { value:wax ? 0.5 : 0.38 };
    sh.uniforms.hkTint = { value:new THREE.Color(1.0, 0.62, 0.5) };
    sh.uniforms.hkMix = { value:wax ? 0.5 : 0.36 };
    const chunk = THREE.ShaderChunk.lights_physical_pars_fragment;
    const from = 'reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );';
    if (chunk.indexOf(from) < 0) return;
    const to = 'float hkW = saturate( ( dot( geometryNormal, directLight.direction ) + hkWrap ) / ( 1.0 + hkWrap ) );\n' +
      'reflectedLight.directDiffuse += mix( vec3( dotNL ), hkW * hkTint, hkMix ) * directLight.color * BRDF_Lambert( material.diffuseColor );';
    sh.fragmentShader = 'uniform float hkWrap;\nuniform vec3 hkTint;\nuniform float hkMix;\n' +
      sh.fragmentShader.replace('#include <lights_physical_pars_fragment>', chunk.replace(from, to));
  };
  m.customProgramCacheKey = () => 'hk-skin' + (wax ? '-wax' : '');
}
/* Clothes can be re-dyed: pixels near a source hue shift to a new hue (keeps folds and texture) */
function hkClothPatch(m, dye){
  m.userData.dye = dye;
  m.onBeforeCompile = (sh) => {
    sh.uniforms.hkDye = { value:new THREE.Vector4(dye ? dye[0] / 360 : 0, dye ? dye[1] / 360 : 0, dye ? dye[2] / 360 : 0, dye ? 1 : 0) };
    sh.uniforms.hkDyeSV = { value:new THREE.Vector2(dye && dye[3] != null ? dye[3] : 1, dye && dye[4] != null ? dye[4] : 1) };
    const rc = dye && dye[5] ? dye[5] : [0, 0, 1, 1], col = dye && dye[6];
    sh.uniforms.hkDyeRect = { value:new THREE.Vector4(rc[0], rc[1], rc[2], rc[3]) };
    /* Optional: tint the black, white and grey fabric (a kit's stripes) to a new colour, keeping its light and dark */
    sh.uniforms.hkCol = { value:new THREE.Vector4(col ? col[0] / 360 : 0, col ? col[1] : 0, col ? col[2] : 0, col ? col[3] : 0) };
    sh.fragmentShader = 'uniform vec4 hkDye;\nuniform vec2 hkDyeSV;\nuniform vec4 hkDyeRect;\nuniform vec4 hkCol;\n' +
      'vec3 hkRgb2Hsv(vec3 c){ vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0); vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g)); vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r)); float d = q.x - min(q.w, q.y); float e = 1.0e-10; return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x); }\n' +
      'vec3 hkHsv2Rgb(vec3 c){ vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0); vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www); return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y); }\n' +
      sh.fragmentShader.replace('#include <map_fragment>', '#include <map_fragment>\n' +
      'if (hkDye.w > 0.5 && vMapUv.x >= hkDyeRect.x && vMapUv.x <= hkDyeRect.z && vMapUv.y >= hkDyeRect.y && vMapUv.y <= hkDyeRect.w){ vec3 hsv = hkRgb2Hsv(diffuseColor.rgb); float dh = abs(fract(hsv.x - hkDye.x + 0.5) - 0.5); float k = (1.0 - smoothstep(hkDye.z * 0.6, hkDye.z, dh)) * smoothstep(0.12, 0.3, hsv.y); if (hkCol.w > 0.0){ float kk = 1.0 - smoothstep(0.07, 0.2, hsv.y); if (kk > 0.0) diffuseColor.rgb = mix(diffuseColor.rgb, hkHsv2Rgb(vec3(hkCol.x, hkCol.y, hkCol.z + hkCol.w * hsv.z)), kk); hsv = hkRgb2Hsv(diffuseColor.rgb); } hsv.x = fract(hsv.x + (hkDye.y - hkDye.x) * k); hsv.y = clamp(hsv.y * mix(1.0, hkDyeSV.x, k), 0.0, 1.0); hsv.z = clamp(hsv.z * mix(1.0, hkDyeSV.y, k), 0.0, 1.0); diffuseColor.rgb = hkHsv2Rgb(hsv); }');
  };
  m.customProgramCacheKey = () => 'hk-cloth' + (dye ? '-dye' : '');
}
function hkMaterials(A, look){
  const wax = !!look.wax, key = A.id + '|' + (wax ? 1 : 0) + '|' + (look.dye ? look.dye.join(',') : '');
  let M = HK.mats.get(key);
  if (M) return M;
  const msaa = !!(QUALITY[GFX.tier] && QUALITY[GFX.tier].msaa);
  M = A.mats.map((d) => {
    const map = d.t >= 0 ? A.tex[d.t] : null;
    let m;
    if (d.k === 'skin'){
      m = new THREE.MeshPhysicalMaterial({ map, roughness:wax ? 0.48 : 0.56, metalness:0, sheen:wax ? 0.35 : 0.22, sheenRoughness:0.5, sheenColor:new THREE.Color(0xffd2bf),
        clearcoat:wax ? 0.24 : 0.05, clearcoatRoughness:0.36, specularIntensity:0.55 });
      hkSkinPatch(m, wax);
    } else if (d.k === 'alpha'){
      m = new THREE.MeshStandardMaterial({ map, alphaTest:0.42, side:THREE.DoubleSide, roughness:0.6, metalness:0 });
      m.alphaToCoverage = msaa;
    } else {
      m = new THREE.MeshStandardMaterial({ map, normalMap:d.nm >= 0 ? A.tex[d.nm] : null, roughness:0.86, metalness:0 });
      if (d.nm >= 0) m.normalScale.set(0.9, -0.9);
      hkClothPatch(m, d.b ? look.dye || null : null);
    }
    m.userData.hk = true;
    return m;
  });
  HK.mats.set(key, M);
  return M;
}

/* ---------- A person ----------
   look: { av (avatar id), height (metres) or scale, wax, dye:[fromHue, toHue, width, sat, val] } */
const _hq = new THREE.Quaternion(), _hv = new THREE.Vector3();
function makeHuman(look){
  const id = look.av, R = hkRig(id), n = HK_N;
  const S = look.height ? look.height / R.h : (look.scale || 1);
  const root = new THREE.Group(), all = [];
  for (let i = 0; i < n; i++){ const b = new THREE.Bone(); b.name = HK_RIG.names[i]; all.push(b); }
  for (const i of R.order){
    const p = R.par[i], b = all[i];
    if (p >= 0){ b.position.copy(R.P[i]).sub(R.P[p]).multiplyScalar(S); all[p].add(b); }
    else { b.position.copy(R.P[i]).multiplyScalar(S); root.add(b); }
  }
  const bones = HK_CTRL.map((nm, k) => { const b = all[HB[nm]]; b.rotation.order = WAX_ORD[k]; return b; });
  const sc = new THREE.Matrix4().makeScale(S, S, S);
  const inv = R.inv.map((m) => sc.clone().multiply(m));
  const skel = new THREE.Skeleton(all, inv);
  const tall = R.h * S;
  if (!HK.pickGeo) HK.pickGeo = new THREE.BoxGeometry(1, 1, 1);
  const pick = new THREE.Mesh(HK.pickGeo, PICK_PROXY); pick.scale.set(0.55 * S, tall, 0.4 * S); pick.position.y = tall / 2; root.add(pick);
  const em = R.eyeMid;
  const fig = { rb:true, id, root, bones, all, skel, mesh:null, pick, look, S, hs:1, R,
    headC:[em.x * S, (em.y - 0.013) * S, (em.z - 0.05) * S], eyeY:em.y * S,
    pose:new Float32Array(WAX_N), t:Math.random() * 10, blinkT:1 + Math.random() * 3, blink:0, talk:0, gaze:new THREE.Vector2(), gazeT:0, gazeTo:new THREE.Vector2(),
    grip:null, onMesh:[] };
  hkFingers(fig, 0, 0, 0, 0);
  /* Lids and jaw keep their rest offsets so blinks and talk add to them */
  fig.lid = ['LEyeBlinkTop', 'REyeBlinkTop', 'LEyeBlinkBottom', 'REyeBlinkBottom', 'LMouthCorner', 'RMouthCorner'].map((nm) => { const b = all[HB[nm]]; return { b, p:b.position.clone() }; });
  HK.figs.push(fig);
  fig.realize = () => {
    if (fig.realizing) return; fig.realizing = true;
    hkAsset(id).then((A) => {
      const mesh = new THREE.SkinnedMesh(A.geo, hkMaterials(A, look));
      mesh.bind(skel, new THREE.Matrix4());
      mesh.boundingSphere = new THREE.Sphere(new THREE.Vector3(0, tall * 0.5, 0), tall * 0.75);
      mesh.frustumCulled = true; mesh.castShadow = !!look.shadow; mesh.receiveShadow = false;
      mesh.userData.noMerge = true; mesh.userData.hk = true; mesh.userData.noAO = !!look.noAO;
      root.add(mesh); fig.mesh = mesh;
      for (const fn of fig.onMesh) fn(mesh);
      hkWarm(mesh);
      if (typeof wake === 'function') wake();
    }).catch(() => {});
  };
  const g = look.lazy;
  if (!g || HK.want[g]) fig.realize(); else (HK.lazy[g] = HK.lazy[g] || []).push(fig);
  return fig;
}
/* Load a group of people that waited until they were needed (the wax hall, the yard) */
function hkWant(g){
  if (HK.want[g]) return;
  HK.want[g] = true;
  for (const f of HK.lazy[g] || []) f.realize();
  HK.lazy[g] = [];
}
/* Compile a new person's shaders before they first show, so walking up doesn't stutter */
function hkWarm(mesh){
  if (typeof renderer === 'undefined' || !renderer || !renderer.compile || typeof camera === 'undefined') return;
  const env = scene.environment, prev = renderer.getRenderTarget();
  try {
    if (typeof GFX !== 'undefined' && GFX.composer) renderer.setRenderTarget(GFX.composer.renderTarget1);
    if (!env && GFX.envIn) scene.environment = GFX.envIn;
    renderer.compile(mesh, camera, scene);
  } catch (e) {}
  finally { scene.environment = env; renderer.setRenderTarget(prev); }
}
function hkPose(fig, o){ const b = fig.bones; for (let i = 0; i < 17; i++) b[i].rotation.set(o[i * 3], o[i * 3 + 1], o[i * 3 + 2]); }

/* Fingers: a relaxed curl, a grip per hand (-1 open flat .. 0 relaxed .. 1 fist) and a point (index out) */
const HK_GRIP = [[16, 22, 18], [58, 70, 46], [60, 72, 48], [62, 74, 50], [64, 76, 52]];
function hkFingers(fig, gl, gr, pl, pr){
  const R = fig.R;
  if (fig.grip && fig.grip[0] === gl && fig.grip[1] === gr && fig.grip[2] === pl && fig.grip[3] === pr) return;
  for (const s of ['L', 'R']){
    const g0 = s === 'L' ? gl : gr, pt = s === 'L' ? pl : pr;
    for (let k = 0; k < 5; k++){
      const ax = R.curl[s][k], base = HK_CURL[k];
      /* pointing: the index straightens, the others close and the thumb tucks */
      const g = pt > 0 ? (k === 1 ? g0 + (-0.85 - g0) * pt : g0 + ((k === 0 ? 0.6 : 0.95) - g0) * pt) : g0;
      for (let j = 0; j < 3; j++){
        const b = fig.all[HB[s + '_Finger' + k + (j ? j : '')]]; if (!b) continue;
        const deg = g < 0 ? base[j] * (1 + g) : base[j] + g * HK_GRIP[k][j];
        b.quaternion.setFromAxisAngle(ax, deg * D2R);
      }
    }
  }
  fig.grip = [gl, gr, pl, pr];
}

/* Face: blinks close the lids, talk drops the jaw, eyes look (gaze x = yaw, y = pitch in radians) */
function hkFace(fig){
  const L = fig.lid, S = fig.S, bl = fig.blink, sm = fig.smile || 0;
  for (let k = 0; k < 6; k++){
    const e = L[k]; e.b.position.copy(e.p);
    if (k < 4){ if (bl > 0.001){ const top = k < 2; e.b.position.y += (top ? -0.0105 : 0.0022) * bl * S; e.b.position.z += (top ? 0.0016 : 0.0006) * bl * S; } }
    else if (sm > 0.001){ const sx = k === 4 ? 1 : -1; e.b.position.x += 0.0025 * sx * sm * S; e.b.position.y += 0.0032 * sm * S; e.b.position.z -= 0.0012 * sm * S; }
  }
  fig.all[HB.MJaw].rotation.x = fig.talk * 0.13;
  for (const nm of ['LEye', 'REye']) fig.all[HB[nm]].rotation.set(-fig.gaze.y, fig.gaze.x, 0, 'YXZ');
}
/* Small eye movements, so a still figure doesn't stare like a statue */
function hkSaccade(fig, dt){
  fig.gazeT -= dt;
  if (fig.gazeT <= 0){ fig.gazeT = 0.8 + Math.random() * 2.6; fig.gazeTo.set((Math.random() - 0.5) * 0.16, (Math.random() - 0.5) * 0.08); }
  fig.gaze.lerp(fig.gazeTo, 1 - Math.exp(-dt * 22));
}
