/* Engine: modern three.js as ES modules from jsDelivr, plus post-processing add-ons.
   The import map names them; if a host ignores import maps, the same files load from
   jsDelivr's ready-made module URLs. If the engine cannot load at all, a stub keeps
   the page alive and the no-3D view takes over. */
let THREE = null;
const XT = {};
const THREE_CDN = 'https://cdn.jsdelivr.net/npm/three@0.170.0/';
const ADDONS = ['postprocessing/EffectComposer.js', 'postprocessing/RenderPass.js', 'postprocessing/OutputPass.js', 'postprocessing/UnrealBloomPass.js',
  'postprocessing/GTAOPass.js', 'postprocessing/ShaderPass.js', 'shaders/FXAAShader.js', 'geometries/RoundedBoxGeometry.js'];
async function loadEngine(viaMap){
  const three = await (viaMap ? import('three') : import(THREE_CDN + '+esm'));
  const mods = await Promise.allSettled(ADDONS.map((p) => viaMap ? import('three/addons/' + p) : import(THREE_CDN + 'examples/jsm/' + p + '/+esm')));
  for (const m of mods) if (m.status === 'fulfilled') Object.assign(XT, m.value);
  return three;
}
try { THREE = await loadEngine(true); }
catch (err) {
  try { THREE = await loadEngine(false); }
  catch (err2) { console.warn('3D engine unavailable', err2); THREE = null; }
}
const THREE_LOADED = !!THREE;
if (!THREE) THREE = new Proxy({}, { get: () => function Stub(){} });
