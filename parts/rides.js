/* ================================================================
   Rides: Comet Coaster, Sky Drop and Ocean Dive
   ================================================================ */
const RIDES = {
  coaster:{ name:'Comet Coaster', kick:'Recess Yard · Ride', exit:{ x:52, z:-6.4, yaw:0, pitch:0.14 }, badge:'coaster' },
  drop:{ name:'Sky Drop', kick:'Recess Yard · Ride', exit:{ x:68.6, z:6.6, yaw:lookYaw(68.6, 6.6, 78, 13), pitch:0.34 }, badge:'drop' },
  dive:{ name:'Ocean Dive', kick:'Recess Yard · Dive', exit:{ x:54, z:8.4, yaw:0, pitch:0.02 }, badge:'diver' }
};
const ride = { on:null, gentle:false, phase:'', t:0, s:0, v:0, y:1, u:0, paused:false, exiting:false, look:{ yaw:0, pitch:0, at:0 }, cap:null, stat:null, fact:-1, lift:0, dyaw:null, dpitch:null };
const amb = { t:0, train:{ phase:'dwell', t:0, s:0, v:0 }, drop:{ phase:'rest', t:0, y:1, v:0 } };
const rc = { card:$('#rideCard'), kick:$('#rcKick'), title:$('#rcTitle'), text:$('#rcText'), note:$('#rcNote'), go:$('#rcGo'), gentle:$('#rcGentle'), cancel:$('#rcCancel') };
const rh = { hud:$('#rideHud'), kick:$('#rhKick'), stat:$('#rhStat'), cap:$('#rhCap'), pause:$('#rhPause'), exit:$('#rhExit') };
const fadeEl = $('#fade');
let rcFor = null, rcFocus = null;

function rideText(id){
  const S = COASTER.stats;
  if (id === 'coaster') return 'Climb a ' + S.height + '-meter lift hill, drop at up to ' + S.kmh + ' km/h (' + S.mph + ' mph), then loop upside down.';
  if (id === 'drop') return 'Rise about 30 meters for a view of the whole campus, then drop back down.';
  return 'Swim past a coral reef and through a kelp forest, with fish schools, a sea turtle, a whale shark, a manta ray and jellyfish.';
}
function rideNote(id){
  if (id === 'coaster') return 'Fast and loopy. Gentle ride goes at half speed. Drag to look around.';
  if (id === 'drop') return 'A big drop. Gentle ride lowers you slowly. Drag to look around.';
  return 'A calm, guided swim that takes about a minute. Drag to look around, and tap sea creatures to learn about them.';
}
function openRide(id){
  if (!THREEOK || ride.on || !RIDES[id]) return;
  if (introOpen) closeIntro();
  closeSearch(); closeViewer(); closeBook(); closeBadges(); if (tourIdx >= 0) endTour(); closeStaff(); stopPaint();
  rcFor = id;
  const R = RIDES[id], isDive = id === 'dive';
  rc.kick.textContent = R.kick; rc.title.textContent = R.name; rc.text.textContent = rideText(id);
  rc.note.textContent = rideNote(id) + (REDUCED && !isDive ? ' Your device asks for less motion, so Gentle ride is a good pick.' : '');
  rc.go.textContent = isDive ? 'Start the dive' : 'Ride now';
  rc.gentle.hidden = isDive;
  if (rc.card.hidden) rcFocus = document.activeElement;
  rc.card.hidden = false; document.body.classList.add('ride-card');
  (REDUCED && !isDive ? rc.gentle : rc.go).focus({ preventScroll:true });
  hideHint();
}
function closeRideCard(){
  if (rc.card.hidden) return;
  rc.card.hidden = true; document.body.classList.remove('ride-card'); rcFor = null;
  if (rcFocus && rcFocus.focus && rcFocus !== document.body) rcFocus.focus({ preventScroll:true }); else ui.scene.focus({ preventScroll:true });
}
rc.go.addEventListener('click', () => { const id = rcFor; closeRideCard(); startRide(id, false); });
rc.gentle.addEventListener('click', () => { const id = rcFor; closeRideCard(); startRide(id, true); });
rc.cancel.addEventListener('click', closeRideCard);
rh.exit.addEventListener('click', () => endRide(false));
rh.pause.addEventListener('click', () => { ride.paused = !ride.paused; rh.pause.textContent = ride.paused ? 'Resume' : 'Pause'; wake(); });

function fadeTo(sea, fn){
  fadeEl.className = 'on' + (sea ? ' sea' : '');
  setTimeout(() => { fn(); requestAnimationFrame(() => { fadeEl.className = sea ? 'sea' : ''; }); }, REDUCED ? 60 : 380);
}
function setCap(t){ if (ride.cap === t) return; ride.cap = t; rh.cap.textContent = t; rh.cap.hidden = !t; }
function setStat(t){ if (ride.stat === t) return; ride.stat = t; rh.stat.textContent = t; }
function startRide(id, gentle){
  if (!THREEOK || ride.on || !RIDES[id]) return;
  fadeTo(id === 'dive', () => {
    Object.assign(ride, { on:id, gentle:!!gentle, phase:'board', t:0, paused:false, exiting:false, fact:-1, lift:0, dyaw:null, dpitch:null, cap:null, stat:null });
    ride.look.yaw = 0; ride.look.pitch = 0; ride.look.at = 0;
    path = []; faceYaw = facePitch = null; keys.clear();
    const ex = RIDES[id].exit; cam.x = ex.x; cam.z = ex.z;
    if (id === 'coaster'){ ride.s = 0; ride.v = 0; amb.train.phase = 'dwell'; amb.train.t = 0; placeTrain(0); }
    if (id === 'drop'){ ride.y = DROP.base; ride.v = 0; amb.drop.phase = 'rest'; amb.drop.t = 0; YA.ring.position.y = DROP.base; }
    if (id === 'dive'){ ride.u = 0; enterDive(); }
    gforceReset();
    document.body.classList.add('riding');
    rh.hud.hidden = false; rh.kick.textContent = RIDES[id].name + (ride.gentle ? ' · Gentle' : '');
    rh.pause.hidden = id !== 'dive'; rh.pause.textContent = 'Pause'; rh.exit.textContent = id === 'dive' ? 'Surface' : 'Exit ride';
    setStat(''); setCap(id === 'dive' ? '' : 'Hold on…');
    hideHint(); ui.tag.hidden = true;
    wake();
  });
}
function endRide(done){
  if (!ride.on || ride.exiting) return;
  ride.exiting = true;
  const id = ride.on, R = RIDES[id];
  fadeTo(id === 'dive', () => {
    if (id === 'dive') exitDive();
    if (id === 'coaster'){ amb.train.phase = 'dwell'; amb.train.t = 0; amb.train.s = 0; placeTrain(0); }
    if (id === 'drop'){ amb.drop.phase = 'rest'; amb.drop.t = 0; amb.drop.y = DROP.base; YA.ring.position.y = DROP.base; }
    ride.on = null; ride.exiting = false; ride.paused = false;
    if (Math.abs(camera.fov - GF.base) > 0.01){ camera.fov = GF.base; camera.updateProjectionMatrix(); }
    document.body.classList.remove('riding'); rh.hud.hidden = true;
    const ex = R.exit; cam.x = ex.x; cam.z = ex.z; cam.yaw = ex.yaw; cam.pitch = ex.pitch;
    if (done){ const fresh = award(R.badge); if (!fresh) toast(id === 'dive' ? 'Welcome back to the surface!' : 'Great ride! Tap the sign to go again.'); }
    ui.scene.focus({ preventScroll:true });
    wake();
  });
}
function rideKeys(dt){
  if (!keys.size) return;
  let t = 0, p = 0;
  if (keys.has('arrowleft') || keys.has('a') || keys.has('q')) t += 1;
  if (keys.has('arrowright') || keys.has('d') || keys.has('e')) t -= 1;
  if (keys.has('arrowup') || keys.has('w')) p += 1;
  if (keys.has('arrowdown') || keys.has('s')) p -= 1;
  ride.look.yaw = clamp(ride.look.yaw + t * 1.6 * dt, -2.6, 2.6); ride.look.pitch = clamp(ride.look.pitch + p * 1.2 * dt, -1.1, 1.0); ride.look.at = performance.now();
}
function rideUpdate(dt){
  if (!ride.on || ride.exiting) return;
  ride.t += dt;
  rideKeys(dt);
  if (performance.now() - ride.look.at > 2400 && !ptr){ const k = Math.exp(-dt * 1.4); ride.look.yaw *= k; ride.look.pitch *= k; }
  if (ride.on === 'coaster') coasterRide(dt);
  else if (ride.on === 'drop') dropRide(dt);
  else diveRide(dt);
}
const _rq = new THREE.Quaternion(), _rq2 = new THREE.Quaternion(), _rm = new THREE.Matrix4(), _rv = new THREE.Vector3(), _re = new THREE.Euler(0, 0, 0, 'YXZ'), _rf = { p:new THREE.Vector3(), t:new THREE.Vector3(), n:new THREE.Vector3(), b:new THREE.Vector3() };
/* G-forces you can feel: the view leans out of turns, sinks in dips, floats over hills, widens with speed and rumbles a little */
const GF = { pv:null, a:new THREE.Vector3(), v:new THREE.Vector3(), lean:0, pitch:0, dy:0, fov:0, base:66, t:0 };
const _gq = new THREE.Quaternion(), _ge = new THREE.Euler(0, 0, 0, 'YXZ');
function gforceReset(){ GF.pv = null; GF.lean = GF.pitch = GF.dy = GF.fov = 0; GF.base = camera.fov; }
function gforceApply(dt, vel, up, right, fwd, speed){
  const on = !REDUCED && !ride.gentle && dt > 0;
  if (on){
    if (GF.pv){ GF.a.subVectors(vel, GF.pv).divideScalar(dt); } else GF.a.set(0, 0, 0);
    GF.pv = (GF.pv || new THREE.Vector3()).copy(vel);
    const fx = GF.a.x, fy = GF.a.y + 9.81, fz = GF.a.z;
    const lat = fx * right.x + fy * right.y + fz * right.z, vert = fx * up.x + fy * up.y + fz * up.z, lon = GF.a.dot(fwd);
    const k = 1 - Math.exp(-dt * 4);
    GF.lean = lerp(GF.lean, clamp(lat * 0.011, -0.13, 0.13), k);
    GF.pitch = lerp(GF.pitch, clamp(lon * 0.006, -0.06, 0.06), k);
    GF.dy = lerp(GF.dy, clamp(-(vert - 9.81) * 0.0045, -0.11, 0.08), k);
    GF.fov = lerp(GF.fov, clamp((speed - 7) * 0.5, 0, 10), 1 - Math.exp(-dt * 2));
  } else { const k = 1 - Math.exp(-dt * 4); GF.lean *= 1 - k; GF.pitch *= 1 - k; GF.dy *= 1 - k; GF.fov *= 1 - k; GF.pv = null; }
  GF.t += dt;
  const rum = on ? Math.min(1, speed / 18) * 0.006 : 0;
  camera.position.addScaledVector(up, GF.dy + Math.sin(GF.t * 47) * Math.sin(GF.t * 31) * rum);
  _ge.set(GF.pitch, 0, GF.lean, 'YXZ'); _gq.setFromEuler(_ge); camera.quaternion.multiply(_gq);
  const want = GF.base + GF.fov;
  if (Math.abs(camera.fov - want) > 0.01){ camera.fov = want; camera.updateProjectionMatrix(); }
}
function trainSpeed(s, v, dt){
  const C = COASTER, sCrest = C.iCrest * C.ds;
  if (s < sCrest) return Math.min(3.2, v + 1.5 * dt);
  return Math.max(0.45, Math.min(coasterSpeedAt(s), Math.sqrt(2 * 4.0 * Math.max(0, C.L - s))));
}
function coasterRide(dt){
  const C = COASTER, k = ride.gentle ? 0.5 : 1, sCrest = C.iCrest * C.ds;
  if (ride.phase === 'board'){ if (ride.t > 1.6){ ride.phase = 'run'; ride.t = 0; setCap(''); } }
  else if (ride.phase === 'run'){
    ride.v = trainSpeed(ride.s, ride.v, dt * k);
    ride.s += ride.v * dt * k;
    if (ride.s > 5 && ride.s < sCrest - 2 && !ride.lift){ ride.lift = 1; setCap('Click, click, click… up the lift hill.'); }
    if (ride.s > sCrest - 1 && ride.lift === 1){ ride.lift = 2; setCap(''); }
    if (ride.s >= C.L - 0.03){ ride.s = C.L; ride.phase = 'done'; ride.t = 0; setCap('Welcome back!'); }
    if (C.tokenAt) checkRideToken('t-coaster', C.tokenAt);
  } else if (ride.phase === 'done'){ if (ride.t > 1.0) endRide(true); }
  placeTrain(ride.s);
  const f = coasterFrame(ride.s + 0.32, _rf);
  camera.position.copy(f.p).addScaledVector(f.n, 1.12);
  _rv.copy(f.t).negate(); _rm.makeBasis(f.b, f.n, _rv); _rq.setFromRotationMatrix(_rm);
  _re.set(ride.look.pitch, ride.look.yaw, 0, 'YXZ'); _rq2.setFromEuler(_re); _rq.multiply(_rq2);
  camera.quaternion.copy(_rq);
  const sp = ride.phase === 'run' ? ride.v * k : 0;
  gforceApply(dt, _rv.copy(f.t).multiplyScalar(sp), f.n, f.b, f.t, sp);
  setStat(Math.round(sp * 3.6) + ' km/h · ' + Math.max(0, Math.round(f.p.y)) + ' m up');
}
const DROP_UP = new THREE.Vector3(0, 1, 0), DROP_RIGHT = new THREE.Vector3(0, 0, -1), DROP_FWD = new THREE.Vector3(-1, 0, 0);
function dropRide(dt){
  const D = DROP;
  if (ride.phase === 'board'){ if (ride.t > 1.4){ ride.phase = 'up'; ride.t = 0; setCap('Going up…'); } }
  else if (ride.phase === 'up'){
    const T = 10, k = clamp(ride.t / T, 0, 1), e = k * k * (3 - 2 * k);
    ride.y = D.base + (D.top - D.base) * e; ride.v = (D.top - D.base) * 6 * k * (1 - k) / T;
    if (k >= 1){ ride.phase = 'hold'; ride.t = 0; ride.v = 0; setCap('About 30 meters up. Look around: you can see the whole campus!'); }
  } else if (ride.phase === 'hold'){
    if (ride.t > (ride.gentle ? 4.5 : 3.6)){ ride.phase = 'drop'; ride.t = 0; ride.v = 0; setCap(ride.gentle ? 'Coming down gently…' : ''); }
  } else if (ride.phase === 'drop'){
    if (ride.gentle){
      const T = 7, k = clamp(ride.t / T, 0, 1), e = k * k * (3 - 2 * k);
      ride.y = D.top - (D.top - D.base) * e; ride.v = (D.top - D.base) * 6 * k * (1 - k) / T;
      if (k >= 1){ ride.phase = 'done'; ride.t = 0; ride.v = 0; }
    } else {
      if (ride.y > 13) ride.v += 9.81 * dt; else ride.v = Math.max(2.2, ride.v - 26 * dt);
      ride.y -= ride.v * dt;
      if (ride.y <= D.base){ ride.y = D.base; ride.v = 0; ride.phase = 'done'; ride.t = 0; }
    }
  } else if (ride.phase === 'done'){ if (ride.t > 1.0) endRide(true); }
  YA.ring.position.y = ride.y;
  if (ride.y > D.top - 1.5) checkRideToken('t-drop', null);
  camera.position.set(D.x - 2.05, ride.y + 1.2, D.z);
  const hk = clamp((ride.y - D.base) / (D.top - D.base), 0, 1);
  _re.set(clamp(-0.05 - 0.22 * hk + ride.look.pitch, -1.2, 1.0), Math.PI / 2 + ride.look.yaw, 0, 'YXZ'); camera.quaternion.setFromEuler(_re);
  const dv = ride.phase === 'drop' && !ride.gentle ? -ride.v : ride.phase === 'up' ? ride.v : 0;
  gforceApply(dt, _rv.set(0, dv, 0), DROP_UP, DROP_RIGHT, DROP_FWD, Math.abs(dv));
  setStat(Math.round(ride.v * 3.6) + ' km/h · ' + Math.max(0, Math.round(ride.y)) + ' m up');
}
function diveRide(dt){
  const P = DIVE.path;
  if (ride.phase === 'board'){ if (ride.t > 0.8){ ride.phase = 'run'; ride.t = 0; } }
  else if (ride.phase === 'run' && !ride.paused){ ride.u = Math.min(1, ride.u + dt * 1.35 / DIVE.len); if (ride.u >= 1){ ride.phase = 'done'; ride.t = 0; } }
  else if (ride.phase === 'done'){ if (ride.t > 2.4) endRide(true); }
  const u = Math.min(0.999, ride.u), p = P.getPointAt(u), tn = P.getTangentAt(u);
  camera.position.set(p.x + DV.x, p.y + Math.sin(ride.t * 0.9) * 0.06, p.z + DV.z);
  let yaw = Math.atan2(-tn.x, -tn.z), pitch = clamp(Math.asin(clamp(tn.y, -1, 1)), -0.35, 0.35);
  const fc = DIVE.facts[ride.fact], tgt = fc && fc.look ? diveLookAt(fc.look, DIVE.camLocal.set(camera.position.x - DV.x, camera.position.y, camera.position.z - DV.z)) : null;
  if (tgt){ const dx = tgt.x - DIVE.camLocal.x, dy = tgt.y - DIVE.camLocal.y, dz = tgt.z - DIVE.camLocal.z; yaw = yaw + clamp(angDiff(yaw, Math.atan2(-dx, -dz)), -1.1, 1.1) * 0.8; pitch = clamp(lerp(pitch, Math.atan2(dy, Math.hypot(dx, dz)), 0.75), -0.7, 0.5); }
  ride.dyaw = ride.dyaw == null ? yaw : lerpAngle(ride.dyaw, yaw, 1 - Math.exp(-dt * 1.2));
  ride.dpitch = ride.dpitch == null ? pitch : lerp(ride.dpitch, pitch, 1 - Math.exp(-dt * 1.2));
  _re.set(clamp(ride.dpitch + ride.look.pitch, -1.3, 1.3), ride.dyaw + ride.look.yaw, 0, 'YXZ'); camera.quaternion.setFromEuler(_re);
  let fi = -1; DIVE.facts.forEach((f, i) => { if (ride.u >= f.u) fi = i; });
  if (fi !== ride.fact){ ride.fact = fi; setCap(fi >= 0 ? DIVE.facts[fi].text : ''); }
  if (DIVE.tokenAt && camera.position.distanceTo(DIVE.tokenAt) < 2.2) checkRideToken('t-dive', null);
  const depth = Math.max(0, Math.round(-p.y));
  setStat((ride.paused ? 'Paused · ' : '') + depth + ' m deep');
}
function checkRideToken(id, pos){ if (prog.tokens.has(id)) return; if (pos && camera.position.distanceTo(pos) > 1.6) return; collectToken(id); }

/* Underwater light and fog */
const DIVE_SAVE = {};
function enterDive(){
  DIVE_SAVE.fog = [scene.fog.color.getHex(), scene.fog.near, scene.fog.far];
  DIVE_SAVE.hemi = [LIGHTS.hemi.color.getHex(), LIGHTS.hemi.groundColor.getHex()];
  DIVE_SAVE.sun = LIGHTS.sun.color.getHex();
  scene.fog.color.setHex(0x0b4a63); scene.fog.near = 1.5; scene.fog.far = 34;
  scene.background = new THREE.Color(0x0b4a63);
  LIGHTS.hemi.color.setHex(0x9fdcff); LIGHTS.hemi.groundColor.setHex(0x0b2f44); LIGHTS.hemi.intensity = 2.9;
  LIGHTS.sun.color.setHex(0xbfeaff); LIGHTS.sun.intensity = 1.9; renderer.shadowMap.autoUpdate = false;
  DIVE.t = 0;
}
function exitDive(){
  if (!DIVE_SAVE.fog) return;
  scene.fog.color.setHex(DIVE_SAVE.fog[0]); scene.fog.near = DIVE_SAVE.fog[1]; scene.fog.far = DIVE_SAVE.fog[2];
  scene.background = srgb(0x0d1613);
  LIGHTS.hemi.color.setHex(DIVE_SAVE.hemi[0]); LIGHTS.hemi.groundColor.setHex(DIVE_SAVE.hemi[1]);
  LIGHTS.sun.color.setHex(DIVE_SAVE.sun);
}
function updateLights(dt){
  if (!LIGHTS.sun) return false;
  if (ride.on === 'dive') return false;
  const target = gfxOutdoor() ? 1 : 0;
  LIGHTS.k = lerp(LIGHTS.k, target, 1 - Math.exp(-dt * 3));
  if (Math.abs(LIGHTS.k - target) < 0.01) LIGHTS.k = target;
  LIGHTS.sun.intensity = SUN_I * LIGHTS.k;
  renderer.shadowMap.autoUpdate = LIGHTS.k > 0.01;
  LIGHTS.hemi.intensity = lerp(HEMI_IN, HEMI_OUT, LIGHTS.k);
  scene.environmentIntensity = lerp(ENV_IN, ENV_OUT, LIGHTS.k) * GFX.envFade;
  return LIGHTS.k !== target;
}

/* The yard keeps moving while you can see it */
function yardAmbient(dt){
  if (!WING.play || !WING.play.visible || REDUCED || document.hidden || ride.on === 'dive') return false;
  amb.t += dt;
  if (YA.portal) YA.portal.offset.set(amb.t * 0.03, amb.t * 0.05);
  const tr = amb.train, C = COASTER;
  if (ride.on !== 'coaster' && C.n){
    if (tr.phase === 'dwell'){ tr.t += dt; if (tr.t > 7){ tr.phase = 'run'; tr.s = 0; tr.v = 0; } }
    else { tr.v = trainSpeed(tr.s, tr.v, dt); tr.s += tr.v * dt; if (tr.s >= C.L - 0.03){ tr.s = 0; tr.phase = 'dwell'; tr.t = 0; } placeTrain(tr.s); }
  }
  const dr = amb.drop;
  if (ride.on !== 'drop' && YA.ring){
    dr.t += dt;
    if (dr.phase === 'rest'){ if (dr.t > 6){ dr.phase = 'up'; dr.t = 0; } }
    else if (dr.phase === 'up'){ const k = clamp(dr.t / 10, 0, 1); dr.y = DROP.base + (DROP.top - DROP.base) * k * k * (3 - 2 * k); if (k >= 1){ dr.phase = 'hold'; dr.t = 0; } }
    else if (dr.phase === 'hold'){ if (dr.t > 3){ dr.phase = 'drop'; dr.t = 0; dr.v = 0; } }
    else { if (dr.y > 13) dr.v += 9.81 * dt; else dr.v = Math.max(2.2, dr.v - 26 * dt); dr.y -= dr.v * dt; if (dr.y <= DROP.base){ dr.y = DROP.base; dr.phase = 'rest'; dr.t = 0; } }
    YA.ring.position.y = dr.y;
  }
  return true;
}

/* Which parts of the campus are worth drawing */
const _frus = new THREE.Frustum(), _fm = new THREE.Matrix4();
const PORTALS = {
  lobbyL:new THREE.Box3(new THREE.Vector3(-6.3, 0, -4.2), new THREE.Vector3(-5.7, 3.1, -1.8)),
  lobbyR:new THREE.Box3(new THREE.Vector3(5.7, 0, -4.2), new THREE.Vector3(6.3, 3.1, -1.8)),
  yard:new THREE.Box3(new THREE.Vector3(33.9, 0, -4.2), new THREE.Vector3(34.4, 2.7, -1.8)),
  waxDoor:new THREE.Box3(new THREE.Vector3(-1.6, 0, -42.35), new THREE.Vector3(1.6, 3.1, -41.8))
};
function updateWings(){
  if (!WING.museum) return;
  if (ride.on === 'dive'){ for (const k in WING) WING[k].visible = k === 'dive'; return; }
  /* A blank or night canvas in the art studio hides the whole campus */
  if (paint.on && paint.canvas !== 'room'){ for (const k in WING) WING[k].visible = false; return; }
  WING.dive.visible = false;
  camera.updateMatrixWorld(); _fm.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse); _frus.setFromProjectionMatrix(_fm);
  const r = roomAt(cam.x, cam.z).id, riding = !!ride.on, x = camera.position.x, low = camera.position.y < 4;
  const see = (k) => _frus.intersectsBox(PORTALS[k]), near = (k, d) => PORTALS[k].distanceToPoint(camera.position) < d;
  /* Inside a classroom, nothing beyond the school's walls can show */
  const inRoom = !riding && ['studio', 'lab', 'blueprint', 'world'].includes(r);
  const outside = riding || r === 'yard' || (!inRoom && x < 34 && see('yard'));
  WING.outside.visible = outside; WING.play.visible = riding || r === 'yard' || (!inRoom && x < 34 && see('yard') && near('yard', 36));
  WING.school.visible = ['hallR', 'school', 'studio', 'lab', 'blueprint', 'world'].includes(r) || (r === 'yard' && low && see('yard')) || (x < 6 && see('lobbyR'));
  WING.lib.visible = ['hallL', 'lib', 'libAisle'].includes(r) || (!inRoom && x > -6 && x < 34 && see('lobbyL'));
  /* The Wax Hall shows from inside, or from the end of Gallery 3 when you look through its door */
  if (WING.wax) WING.wax.visible = r === 'wax' || (r === 'g3' && camera.position.z < -35 && see('waxDoor'));
  WING.museum.visible = ['lobby', 'g1', 'g2', 'g3', 'hallL', 'hallR'].includes(r) || (r === 'wax' && camera.position.z > -47 && see('waxDoor')) || (x < -6 && see('lobbyL')) || (!inRoom && x > 6 && x < 34 && see('lobbyR')) || (r === 'yard' && low && near('yard', 12) && see('yard') && see('lobbyR'));
  if (WING.waxIntro) WING.waxIntro.visible = WING.museum.visible || WING.wax.visible;
}
