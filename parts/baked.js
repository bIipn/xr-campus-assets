/* ================================================================
   Baked rooms: photoreal interiors modelled and lit in Blender (Cycles), shipped as glTF with
   KTX2 textures and Meshopt geometry. Lighting comes from the bake, not from the scene's lights:
   big surfaces carry a lightmap (glTF emissive slot, texCoord 1), small things carry it in their
   vertex colours, and a reflection probe rendered in the room gives the speculars.
   ================================================================ */
const BAKED = {
  lib:{ url:'lib/lib.glb', probe:'lib/probe.hdr', LM_SCALE:8, VC_SCALE:4, exposure:0.78 }
};
/* The campus renders through ACES, which saturates warm light more than Blender's AgX did when the room was
   lit; the baked light is pulled part-way toward neutral so the room reads like the reference render. */
const BK_SAT = 0.72;
const BK = { loaders:null, white:null, rooms:{} };

/* A MeshStandardMaterial that ignores every scene light: direct light loops are cut out of the shader
   (cheap on a headset) and the env map only adds speculars, so the bake is the only diffuse light. */
const BK_NOLIGHT = `
vec3 geometryPosition = - vViewPosition;
vec3 geometryNormal = normal;
vec3 geometryViewDir = ( isOrthographic ) ? vec3( 0, 0, 1 ) : normalize( vViewPosition );
vec3 geometryClearcoatNormal = vec3( 0.0 );
vec3 iblIrradiance = vec3( 0.0 );
vec3 irradiance = vec3( 0.0 );
vec3 radiance = vec3( 0.0 );
vec3 clearcoatRadiance = vec3( 0.0 );
`;
const BK_DESAT = (v) => 'mix( vec3( dot( ' + v + ', vec3( 0.2126, 0.7152, 0.0722 ) ) ), ' + v + ', ' + BK_SAT.toFixed(3) + ' )';
function bkHook(shader){
  shader.fragmentShader = shader.fragmentShader
    .replace('#include <lights_fragment_begin>', BK_NOLIGHT)
    .replace('#include <lights_fragment_maps>', '#include <lights_fragment_maps>\n\tiblIrradiance = vec3( 0.0 );\n\tirradiance = ' + BK_DESAT('irradiance') + ';')
    .replace('#include <color_fragment>', '#ifdef USE_COLOR\n\tdiffuseColor.rgb *= ' + BK_DESAT('vColor.rgb') + ';\n#endif');
}

function bkLoaders(){
  if (BK.loaders) return BK.loaders;
  BK.loaders = Promise.all([
    import('three/addons/loaders/GLTFLoader.js'), import('three/addons/loaders/KTX2Loader.js'),
    import('three/addons/loaders/RGBELoader.js'), import('three/addons/libs/meshopt_decoder.module.js')
  ]).then(async ([G, K, R, M]) => {
    await M.MeshoptDecoder.ready;
    const ktx = new K.KTX2Loader().setTranscoderPath(THREE_CDN + 'examples/jsm/libs/basis/').detectSupport(renderer);
    const gltf = new G.GLTFLoader().setKTX2Loader(ktx).setMeshoptDecoder(M.MeshoptDecoder);
    return { gltf, rgbe:new R.RGBELoader() };
  });
  return BK.loaders;
}
function bkWhite(){
  if (!BK.white){ BK.white = new THREE.DataTexture(new Uint8Array([255, 255, 255, 255]), 1, 1); BK.white.needsUpdate = true; }
  return BK.white;
}

/* Wire one material to its bake. Materials are shared by the room's meshes, so each is prepared once. */
function bkMaterial(m, cfg, env){
  if (m.userData.baked) return;
  m.userData.baked = true;
  if (m.userData.lm && m.emissiveMap){
    /* the lightmap travelled in the emissive slot (sRGB-encoded irradiance / LM_SCALE, texCoord 1) */
    const lm = m.emissiveMap; m.emissiveMap = null; m.emissive.setRGB(0, 0, 0);
    lm.colorSpace = THREE.SRGBColorSpace; lm.channel = 1; lm.anisotropy = Math.min(4, ANISO);
    m.lightMap = lm; m.lightMapIntensity = cfg.LM_SCALE * Math.PI * cfg.exposure;
  } else if (m.vertexColors){
    /* vertex colours hold irradiance / VC_SCALE; a white lightmap turns them into light */
    m.lightMap = bkWhite(); m.lightMap.channel = 0; m.lightMapIntensity = cfg.VC_SCALE * Math.PI * cfg.exposure;
  } else if (m.emissive && m.emissiveIntensity > 0){
    m.emissiveIntensity *= cfg.exposure;
  }
  if (env && m.isMeshStandardMaterial){ m.envMap = env; m.envMapIntensity = cfg.exposure; }
  if (m.isMeshStandardMaterial){ m.onBeforeCompile = bkHook; m.customProgramCacheKey = () => 'baked'; }
  m.needsUpdate = true;
}

/* Load a baked room and hang it under `parent` at campus coordinates (the glTF is already in them). */
function loadBakedRoom(key, parent, done){
  const cfg = BAKED[key]; if (!cfg || !THREE_LOADED || BK.rooms[key]) return BK.rooms[key];
  const room = BK.rooms[key] = { group:null, env:null, ready:false };
  /* The Claude artifact host serves only web file types, so there (HK.b64) the room files ship as base64 text */
  const grab = async (url) => {
    const r = await fetch(HK.b64 ? url + '.txt' : url);
    if (!r.ok) throw new Error(r.status + ' ' + url);
    return HK.b64 ? hkB64(await r.text()) : await r.arrayBuffer();
  };
  bkLoaders().then(async ({ gltf, rgbe }) => {
    let env = null;
    try {
      const td = rgbe.parse(await grab(cfg.probe));
      const hdr = new THREE.DataTexture(td.data, td.width, td.height, THREE.RGBAFormat, td.type);
      hdr.colorSpace = THREE.LinearSRGBColorSpace; hdr.minFilter = hdr.magFilter = THREE.LinearFilter;
      hdr.generateMipmaps = false; hdr.flipY = true; hdr.needsUpdate = true;
      hdr.mapping = THREE.EquirectangularReflectionMapping;
      env = GFX.pmrem.fromEquirectangular(hdr).texture; hdr.dispose();
    } catch (e) { console.warn('baked room: no probe', e); }
    const g = await gltf.parseAsync(await grab(cfg.url), cfg.url.slice(0, cfg.url.lastIndexOf('/') + 1));
    const grp = g.scene; grp.name = 'baked-' + key; grp.userData.noMerge = true;
    const mats = new Set();
    grp.traverse((o) => {
      if (!o.isMesh) return;
      o.castShadow = false; o.receiveShadow = false; o.matrixAutoUpdate = false; o.updateMatrix();
      const m = o.material; mats.add(m);
      if (m.transparent){ o.renderOrder = 2; m.depthWrite = false; }
      o.userData.baked = key;
    });
    for (const m of mats) bkMaterial(m, cfg, env);
    room.group = grp; room.env = env; room.ready = true;
    parent.add(grp);
    if (done) done(room);
  }).catch((e) => console.warn('baked room failed', key, e));
  return room;
}
