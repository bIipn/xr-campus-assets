/* ================================================================
   Virtual staff
   ================================================================ */
const STAFF = {
  margaret:{ id:'margaret', name:'Margaret', role:'Museum guide', mono:'M', color:'#cda961', rooms:['lobby','g1','g2','g3','wax'],
    pos:{ x:0.68, z:-4.0 }, face:{ x:0, z:-0.7 },
    look:{ av:'bf02', body:'skirt', top:0x274a52, bottom:0x2a292d, skin:0xc99c7a, hair:0xbdb6ab, hairStyle:'bun', glasses:true },
    view:{ x:-0.2, z:-2.0, yaw:-0.41, pitch:0 } },
  rosa:{ id:'rosa', name:'Rosa', role:'Reference librarian', mono:'R', color:'#5aa08c', rooms:['hallL','lib','libAisle'],
    pos:{ x:-17.2, z:-7.75 }, face:{ x:-13, z:-3 },
    look:{ av:'fa14', body:'pants', top:0xb07d2a, bottom:0x26304a, skin:0xa8775a, hair:0x2a1d16, hairStyle:'topbun', collar:0xf0ebe0 },
    view:{ x:-17.2, z:-5.0, yaw:0, pitch:0 } },
  hale:{ id:'hale', name:'Mr. Hale', role:'Workshop teacher', mono:'H', color:'#e07b2a', rooms:['hallR','school','studio','lab','blueprint','world'], track:['hallR','school','studio'],
    pos:{ x:17.4, z:-10.6 }, face:{ x:19, z:-4.75 },
    look:{ av:'ma05', body:'pants', top:0xa8c0d8, bottom:0x3a3f46, skin:0xb98a68, hair:0x4a3b2e, hairStyle:'short', apron:0x34383c, mustache:true, rolled:true, collar:0xa8c0d8 },
    view:{ x:18.7, z:-7.6, yaw:0.42, pitch:0 } },
  rae:{ id:'rae', name:'Coach Rae', role:'Recess coach', mono:'C', color:'#3a8fd8', rooms:['yard'],
    pos:{ x:46.4, z:0.4 }, face:{ x:38, z:-3 },
    look:{ av:'sf02', body:'pants', top:0xd2462f, bottom:0x26303f, skin:0x8d5a3b, hair:0x1b1410, hairStyle:'short', cap:0x1d3b52, whistle:true, collar:0xf2c14e },
    view:{ x:44.3, z:-0.45, yaw:lookYaw(44.3, -0.45, 46.4, 0.4), pitch:0 } }
};
/* A realistic person: a Rocketbox avatar with a name label, idling and looking at you */
function buildHumanStaff(st){
  const L = st.look, f = makeHuman({ av:L.av, shadow:true });
  const root = f.root; root.position.set(st.pos.x, 0, st.pos.z); root.rotation.y = Math.atan2(st.face.x - st.pos.x, st.face.z - st.pos.z);
  st.fig = f; st.dense = waxKeyDense({ p:'ease' }); st.cur = new Float32Array(WAX_N);
  hkPose(f, st.dense); hkFingers(f, 0, 0, 0, 0);
  if (L.whistle){
    const w = new THREE.Group(), cord = new THREE.Mesh(new THREE.TorusGeometry(0.075, 0.0025, 4, 24), stdMat(0xf2c14e, 0.6));
    cord.rotation.x = Math.PI / 2 - 0.35; cord.scale.set(1, 1.25, 1); w.add(cord);
    const body = new THREE.Mesh(new THREE.CylinderGeometry(0.011, 0.011, 0.045, 12), stdMat(0xc9ced2, 0.3, 0.8)); body.rotation.z = Math.PI / 2; body.position.set(0, -0.09, 0.07); w.add(body);
    const sp = f.all[HB.Spine2]; sp.add(w); w.position.set(0, 0.06, 0.035);
  }
  const lc = mk(640, 190); drawStaffLabel(lc, st.name, st.role);
  const label = new THREE.Sprite(new THREE.SpriteMaterial({ map:tex(lc), transparent:true, depthWrite:false, toneMapped:false }));
  const tall = f.R.h * f.S;
  label.scale.set(0.88, 0.26, 1); label.position.set(0, tall + 0.3, 0); root.add(label);
  for (const m of [f.pick, label]){ m.userData.staff = st.id; pickItems.push(m); }
  f.onMesh.push((mesh) => { mesh.userData.staff = st.id; });
  scene.add(root);
  st.root = root; st.head = f.bones[WB.head]; st.parts = [f.pick, label]; st.eyes = []; st.arms = [];
  st.look2 = { yaw:0, pitch:0 };
  return root;
}
function buildPerson(st){
  if (st.look.av && HK_RIG.avatars[st.look.av]) return buildHumanStaff(st);
  const L = st.look, parts = [];
  const root = new THREE.Group(); root.position.set(st.pos.x, 0, st.pos.z); root.rotation.y = Math.atan2(st.face.x - st.pos.x, st.face.z - st.pos.z);
  const top = stdMat(L.top), bottom = stdMat(L.bottom), skin = stdMat(L.skin, 0.65), hair = stdMat(L.hair, 0.95), collar = stdMat(L.collar || 0xece5d7);
  const shoe = stdMat(0x1d1712, 0.5), dark = stdMat(0x2a2420, 0.4), lip = stdMat(0x8a4a3c, 0.6), frame = stdMat(0x6b5a3a, 0.4);
  const add = (parent, geo, m, x, y, z, fn) => { const mesh = new THREE.Mesh(geo, m); mesh.position.set(x, y, z); if (fn) fn(mesh); parent.add(mesh); parts.push(mesh); return mesh; };
  const Cyl = (a, b, h, n) => new THREE.CylinderGeometry(a, b, h, n || 20), Sph = (r, a, b) => new THREE.SphereGeometry(r, a || 20, b || 14), Bx = (w, h, d) => new THREE.BoxGeometry(w, h, d);
  if (L.body === 'skirt'){
    for (const s of [-1, 1]){ add(root, Bx(0.09, 0.06, 0.2), shoe, s * 0.07, 0.03, 0.03); add(root, Cyl(0.035, 0.035, 0.22, 10), skin, s * 0.07, 0.16, 0); }
    add(root, Cyl(0.175, 0.24, 0.66, 32), bottom, 0, 0.56, 0);
  } else {
    for (const s of [-1, 1]){ add(root, Bx(0.1, 0.07, 0.24), shoe, s * 0.08, 0.035, 0.03); add(root, Cyl(0.064, 0.056, 0.8, 14), bottom, s * 0.08, 0.47, 0); }
    add(root, Cyl(0.165, 0.17, 0.22, 28), bottom, 0, 0.86, 0);
  }
  add(root, Cyl(0.165, 0.185, 0.48, 32), top, 0, 1.12, 0);
  add(root, Sph(0.17, 28, 18), top, 0, 1.33, 0, (m) => m.scale.set(1.18, 0.52, 0.86));
  add(root, Cyl(0.075, 0.09, 0.05, 20), collar, 0, 1.415, 0.005);
  add(root, Cyl(0.043, 0.048, 0.09, 16), skin, 0, 1.47, 0);
  let badgeZ = 0.158;
  if (L.apron){ const am = stdMat(L.apron, 0.9); add(root, Bx(0.32, 0.74, 0.016), am, 0, 0.98, 0.19); add(root, Bx(0.2, 0.025, 0.016), am, 0, 1.33, 0.165); badgeZ = 0.2; }
  add(root, new THREE.PlaneGeometry(0.075, 0.03), new THREE.MeshBasicMaterial({ color:0xd8b56a, toneMapped:false }), 0.075, 1.24, badgeZ);
  /* Arms hang from shoulder pivots so they can sway a little while the staff stand and breathe */
  st.arms = [];
  for (const s of [-1, 1]){
    const arm = new THREE.Group(); arm.position.set(s * 0.19, 1.33, 0.01); arm.userData.side = s; root.add(arm); st.arms.push(arm);
    add(arm, Cyl(0.048, 0.044, 0.27, 14), top, s * 0.015, -0.13, 0, (m) => { m.rotation.z = s * 0.12; });
    add(arm, Cyl(0.043, 0.038, 0.25, 14), L.rolled ? skin : top, s * 0.042, -0.38, 0.005, (m) => { m.rotation.z = s * 0.12; });
    add(arm, Sph(0.042, 14, 10), skin, s * 0.058, -0.515, 0.01);
  }
  const head = new THREE.Group(); head.position.set(0, 1.6, 0); root.add(head);
  add(head, Sph(0.1, 28, 20), skin, 0, 0, 0, (m) => m.scale.set(0.93, 1.1, 0.97));
  if (L.hairStyle === 'short'){
    add(head, new THREE.SphereGeometry(0.105, 28, 20, 0, Math.PI * 2, 0, Math.PI * 0.46), hair, 0, 0.018, -0.008, (m) => { m.rotation.x = -0.22; });
    for (const s of [-1, 1]) add(head, Bx(0.02, 0.05, 0.04), hair, s * 0.09, -0.005, -0.01);
  } else {
    add(head, new THREE.SphereGeometry(0.108, 28, 20, 0, Math.PI * 2, 0, Math.PI * 0.52), hair, 0, 0.012, -0.012, (m) => { m.rotation.x = -0.38; m.scale.set(1, 1.08, 1); });
    if (L.hairStyle === 'topbun') add(head, Sph(0.05, 18, 14), hair, 0, 0.12, -0.03); else add(head, Sph(0.048, 18, 14), hair, 0, 0.07, -0.095);
  }
  st.eyes = [];
  for (const s of [-1, 1]){
    st.eyes.push(add(head, Sph(0.011, 10, 8), dark, s * 0.036, 0.012, 0.094));
    if (L.glasses) add(head, new THREE.TorusGeometry(0.027, 0.0035, 6, 20), frame, s * 0.036, 0.012, 0.1);
  }
  if (L.glasses) add(head, Bx(0.02, 0.004, 0.004), frame, 0, 0.016, 0.104);
  if (L.mustache) add(head, Bx(0.062, 0.014, 0.012), hair, 0, -0.03, 0.094);
  if (L.cap){ const capM = stdMat(L.cap, 0.7); add(head, new THREE.SphereGeometry(0.112, 28, 14, 0, Math.PI * 2, 0, Math.PI * 0.42), capM, 0, 0.024, -0.004); add(head, Bx(0.15, 0.012, 0.09), capM, 0, 0.045, 0.1, (m) => { m.rotation.x = 0.12; }); }
  if (L.whistle){ add(root, Bx(0.012, 0.2, 0.01), stdMat(0xf2c14e, 0.6), 0, 1.33, 0.175); add(root, Cyl(0.014, 0.014, 0.06, 10), stdMat(0xc9ced2, 0.3, 0.8), 0, 1.22, 0.18, (m) => { m.rotation.z = Math.PI / 2; }); }
  add(head, new THREE.TorusGeometry(0.024, 0.0035, 6, 16, Math.PI), lip, 0, -0.045, 0.092, (m) => { m.rotation.z = Math.PI; });
  const lc = mk(640, 190); drawStaffLabel(lc, st.name, st.role);
  const label = new THREE.Sprite(new THREE.SpriteMaterial({ map:tex(lc), transparent:true, depthWrite:false, toneMapped:false }));
  label.scale.set(0.88, 0.26, 1); label.position.set(0, 2.06, 0); root.add(label); parts.push(label);
  for (const m of parts){ m.userData.staff = st.id; pickItems.push(m); }
  scene.add(root);
  st.root = root; st.head = head; st.parts = parts;
  return root;
}
function buildStaff(M){
  for (const id in STAFF) buildPerson(STAFF[id]);
  const mg = STAFF.margaret, root = mg.root;
  const stand = new THREE.Group(); stand.position.set(0.58, 0, 0.08); root.add(stand);
  const oak = stdMat(0x5b3c25, 0.55), extra = [];
  extra.push(addBox(0.4, 0.98, 0.3, oak, 0, 0.49, 0, 0, stand));
  extra.push(addBox(0.44, 0.04, 0.34, M.brass, 0, 0.02, 0, 0, stand));
  const top = addBox(0.5, 0.03, 0.38, oak, 0, 1.0, 0.02, 0, stand); top.rotation.x = 0.3; extra.push(top);
  extra.push(addPlane(0.36, 0.134, basicMat(drawLecternSign(), 0xe9e3d8), 0, 0.76, 0.151, 0, stand));
  for (const m of extra){ m.userData.staff = 'margaret'; pickItems.push(m); }
  const c = Math.cos(root.rotation.y), sn = Math.sin(root.rotation.y);
  OBST.push({ x:mg.pos.x + (0.58 * c + 0.08 * sn) / 2, z:mg.pos.z + (-0.58 * sn + 0.08 * c) / 2, r:0.85 });
  OBST.push({ x:STAFF.rosa.pos.x, z:STAFF.rosa.pos.z, r:0.55 });
  OBST.push({ x:STAFF.hale.pos.x, z:STAFF.hale.pos.z, r:0.55 });
  OBST.push({ x:STAFF.rae.pos.x, z:STAFF.rae.pos.z, r:0.55 });
}
function staffFor(roomId){ for (const id in STAFF) if (STAFF[id].rooms.includes(roomId)) return STAFF[id]; return STAFF.margaret; }
function trackHeads(dt){
  let active = false;
  const room = roomAt(cam.x, cam.z).id;
  for (const id in STAFF){
    const st = STAFF[id]; if (!st.head) continue;
    if (!st.home) st.home = roomAt(st.pos.x, st.pos.z).id;
    const dx = cam.x - st.root.position.x, dz = cam.z - st.root.position.z, dist = Math.hypot(dx, dz), near = dist < 12 && (st.track || st.rooms).includes(room) && (room === st.home || dist < 7);
    let rel = angDiff(st.root.rotation.y, Math.atan2(dx, dz));
    if (!near) rel = 0;
    rel = clamp(rel, -0.8, 0.8);
    if (st.fig){
      const f = st.fig, ey = f.eyeY, py = near ? clamp(Math.atan2(eyeY() - ey, Math.max(0.5, dist)), -0.35, 0.3) : 0;
      st.look2.yaw = lerp(st.look2.yaw, rel, 1 - Math.exp(-dt * 4));
      st.look2.pitch = lerp(st.look2.pitch, py, 1 - Math.exp(-dt * 4));
      const talking = st.talkUntil && performance.now() < st.talkUntil;
      if (near || talking){ staffIdleHuman(st, dt, near); active = true; }
      else if (Math.abs(st.look2.yaw) > 0.01 || f.blink || f.talk){ staffIdleHuman(st, dt, false); active = true; }
      continue;
    }
    st.head.rotation.y = lerp(st.head.rotation.y, rel, 1 - Math.exp(-dt * 5));
    if (Math.abs(st.head.rotation.y - rel) > 0.01) active = true;
    if (near && !REDUCED && staffIdle(st, dt)) active = true;
  }
  return active;
}
/* A real person stands, breathes, shifts weight, blinks, looks at you and talks when answering */
function staffIdleHuman(st, dt, near){
  const f = st.fig, o = st.cur;
  st.t = (st.t == null ? Math.random() * 20 : st.t) + dt;
  const t = st.t, m = REDUCED ? 0 : 1, br = Math.sin(t * 1.5) * m;
  o.set(st.dense);
  o[WB.chest * 3] += 1.4 * D2R * br; o[WB.shL * 3 + 2] += 0.9 * D2R * br; o[WB.shR * 3 + 2] -= 0.9 * D2R * br;
  const sway = Math.sin(t * 0.37) * m;
  o[WB.hips * 3 + 2] += 1.6 * D2R * sway; o[WB.chest * 3 + 2] -= 1.0 * D2R * sway;
  o[WB.knL * 3] += Math.max(0, sway) * 4 * D2R; o[WB.knR * 3] += Math.max(0, -sway) * 4 * D2R;
  o[WB.shL * 3] += 2.0 * D2R * Math.sin(t * 0.8 + 0.4) * m; o[WB.shR * 3] += 2.0 * D2R * Math.sin(t * 0.8 + 2.1) * m;
  /* Head turns most of the way toward you; the eyes do the rest */
  const yaw = st.look2.yaw, pitch = st.look2.pitch;
  o[WB.neck * 3 + 1] += yaw * 0.35; o[WB.head * 3 + 1] += yaw * 0.45; o[WB.chest * 3 + 1] += yaw * 0.1;
  o[WB.head * 3] -= pitch * 0.55; o[WB.head * 3] += 1.5 * D2R * Math.sin(t * 0.53 + 1.2);
  const talking = st.talkUntil && performance.now() < st.talkUntil;
  if (talking){ o[WB.head * 3] += 2.5 * D2R * Math.sin(t * 2.3); o[WB.head * 3 + 2] += 1.5 * D2R * Math.sin(t * 1.7); o[WB.elR * 3] -= 10 * D2R * (0.5 + 0.5 * Math.sin(t * 1.3)); o[WB.shR * 3] -= 6 * D2R * (0.5 + 0.5 * Math.sin(t * 1.3)); }
  hkPose(f, o);
  hkFingers(f, talking ? -0.3 : 0, talking ? -0.5 + 0.3 * Math.sin(t * 1.3) : 0, 0, 0);
  f.gazeTo.set(clamp(yaw * 0.25, -0.3, 0.3), clamp(-pitch * 0.45, -0.25, 0.25));
  f.gaze.lerp(f.gazeTo, 1 - Math.exp(-dt * 18));
  st.blinkT = (st.blinkT == null ? 1 + Math.random() * 3 : st.blinkT) - dt;
  if (st.blinkT < -0.15) st.blinkT = 2.2 + Math.random() * 3.5;
  f.blink = st.blinkT < 0 ? Math.sin(-st.blinkT / 0.15 * Math.PI) : 0;
  f.talk = talking ? clamp(0.4 + 0.6 * Math.sin(t * 14.5) * Math.sin(t * 3.9 + 1), 0, 1) * 0.7 : 0;
  f.smile = near ? (talking ? 0.3 : 0.55) : 0.2;
  hkFace(f);
  return true;
}
/* Talk for about as long as reading the reply aloud takes */
function staffTalk(id, text){
  const st = STAFF[id]; if (!st) return;
  const secs = clamp(String(text || '').length / 16, 1.2, 7);
  st.talkUntil = performance.now() + secs * 1000;
  if (typeof wake === 'function') wake();
}
/* Idle life: breathing, a slow weight shift, swaying arms and the odd blink */
function staffIdle(st, dt){
  st.t = (st.t == null ? Math.random() * 20 : st.t) + dt;
  const t = st.t, br = Math.sin(t * 1.55);
  st.root.scale.y = 1 + 0.007 * br;
  st.root.rotation.z = 0.011 * Math.sin(t * 0.41);
  st.head.rotation.x = 0.035 * Math.sin(t * 0.53 + 1.2) - 0.01 * br;
  for (const a of st.arms){ const s = a.userData.side; a.rotation.z = s * (0.025 + 0.012 * br); a.rotation.x = 0.045 * Math.sin(t * 0.8 + s * 0.9); }
  st.blinkT = (st.blinkT == null ? 1 + Math.random() * 3 : st.blinkT) - dt;
  if (st.blinkT < -0.13) st.blinkT = 2.2 + Math.random() * 3.5;
  const ey = st.blinkT < 0 ? 0.12 : 1;
  for (const e of st.eyes) e.scale.y = ey;
  return true;
}
