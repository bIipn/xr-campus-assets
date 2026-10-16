/* ================================================================
   WebXR: a headset opens the same campus. "Enter VR" shows when the browser can run immersive VR
   (Quest Browser, PC VR browsers). The headset looks around, the left stick walks (with the campus's
   own collision and pathing), the right stick snap-turns. Rather than moving a rig, the campus moves
   the XR reference space so camera.position stays the true head position in world coordinates and
   everything that reads it (wings, lamps, shadows, sky) keeps working unchanged.
   ================================================================ */
const XR = { session:null, base:null, on:false, turn:0, snapped:false, btn:null, _q:null, _v:null, _p:null, lastKey:'' };

function xrInit(){
  if (!THREE_LOADED || !renderer || !navigator.xr) return;
  XR._q = new THREE.Quaternion(); XR._v = new THREE.Vector3(); XR._p = new THREE.Vector3();
  renderer.xr.enabled = true;
  renderer.xr.setReferenceSpaceType('local-floor');
  XR.btn = document.getElementById('bVR');
  navigator.xr.isSessionSupported('immersive-vr').then((ok) => {
    if (!ok || !XR.btn) return;
    XR.btn.hidden = false;
    XR.btn.addEventListener('click', () => { if (XR.on) XR.session.end(); else xrStart(); });
  }).catch(() => {});
}

async function xrStart(){
  try {
    const session = await navigator.xr.requestSession('immersive-vr', { optionalFeatures:['local-floor', 'bounded-floor', 'hand-tracking'] });
    session.addEventListener('end', xrEnded);
    await renderer.xr.setSession(session);
    XR.session = session; XR.base = renderer.xr.getReferenceSpace(); XR.on = true; XR.turn = cam.yaw; XR.snapped = false; XR.lastKey = '';
    document.body.classList.add('xr');
    if (XR.btn) XR.btn.textContent = 'Exit VR';
    if (raf){ cancelAnimationFrame(raf); raf = 0; }
    path = []; faceYaw = facePitch = null;
    xrPlace();
    last = performance.now();
    renderer.setAnimationLoop((t) => frame(t));
  } catch (e) {
    console.warn('VR could not start', e);
    if (typeof toast === 'function') toast('VR could not start here');
  }
}
function xrEnded(){
  XR.on = false; XR.session = null; XR.base = null;
  renderer.setAnimationLoop(null);
  document.body.classList.remove('xr');
  if (XR.btn) XR.btn.textContent = 'Enter VR';
  JOY.on = false; JOY.x = JOY.y = 0;
  camera.fov = 66; camera.updateProjectionMatrix();
  resize(); wake();
}

/* Before the campus updates: the head's yaw becomes the walking direction, the sticks become the touch stick */
function xrInput(dt){
  if (!XR.on) return;
  const f = XR._v.set(0, 0, -1).applyQuaternion(camera.quaternion);
  cam.yaw = Math.atan2(-f.x, -f.z);
  cam.pitch = Math.asin(Math.max(-1, Math.min(1, f.y)));
  let mx = 0, my = 0, any = false, tx = 0;
  for (const src of XR.session.inputSources){
    const gp = src.gamepad; if (!gp) continue;
    const ax = gp.axes, x = ax.length >= 4 ? ax[2] : (ax[0] || 0), y = ax.length >= 4 ? ax[3] : (ax[1] || 0);
    if (src.handedness === 'right'){ tx = x; if (Math.abs(y) > 0.5 && Math.abs(x) < 0.5){ my = y; any = true; } }
    else { mx = x; my = y; any = Math.hypot(x, y) > 0.1 || any; }
  }
  if (any && Math.hypot(mx, my) > 0.12){ JOY.on = true; JOY.x = mx; JOY.y = my; }
  else { JOY.on = false; JOY.x = JOY.y = 0; }
  if (Math.abs(tx) > 0.7){ if (!XR.snapped){ XR.turn -= Math.sign(tx) * Math.PI / 6; XR.snapped = true; } }
  else if (Math.abs(tx) < 0.3) XR.snapped = false;
}
/* Put the reference space's origin where the player stands, facing XR.turn (the headset adds its own pose on top) */
function xrPlace(){
  if (!XR.base) return;
  const key = cam.x.toFixed(3) + ',' + PLAYER.y.toFixed(3) + ',' + cam.z.toFixed(3) + ',' + XR.turn.toFixed(4);
  if (key === XR.lastKey) return;
  XR.lastKey = key;
  /* world = T * pose with T = translate(P) * rotY(turn); the offset space is T's inverse */
  const c = Math.cos(-XR.turn), s = Math.sin(-XR.turn);
  const px = -cam.x, py = -PLAYER.y, pz = -cam.z;
  const ox = c * px + s * pz, oz = -s * px + c * pz;
  const q = XR._q.setFromAxisAngle(XR._p.set(0, 1, 0), -XR.turn);
  const t = new XRRigidTransform({ x:ox, y:py, z:oz, w:1 }, { x:q.x, y:q.y, z:q.z, w:q.w });
  renderer.xr.setReferenceSpace(XR.base.getOffsetReferenceSpace(t));
}
