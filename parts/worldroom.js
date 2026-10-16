/* ================================================================
   Room 104: World Builder Studio
   A mini world on a table that you build up one layer at a time
   ================================================================ */
const DIO = { x:29.0, z:2.9, y:0.87, root:null, step:0, xray:false, mats:[], models:[], groups:{}, balls:[], people:[], t:0, water:null, car:null, flag:null, confetti:null };
const DIO_STEPS = [
  { t:'Plan', d:'Every world starts as an idea and a sketch. Who is it for, and what will they do there? This campus started as a list (a museum, a library, a school and a recess yard) and a rough map of how to walk between them.', page:1 },
  { t:'Block out', d:'Build the layout from plain boxes, then walk around it. Is the hall wide enough? Does the coaster fit? Fixing things now is cheap. Game studios call this a blockout, or graybox.', page:3 },
  { t:'Models', d:'Swap the boxes for real models. Artists build them in tools like Blender; this campus builds almost everything from code: boxes, cylinders, spheres and extruded shapes. Every model is a mesh of triangles. Turn on X-ray to see them.', page:4 },
  { t:'Materials', d:'Materials say what a surface is made of: its color, how rough or shiny it is, and whether it’s metal. Physically based materials (PBR) react to light the way real surfaces do. Many of the textures here are drawn by code as the campus loads.', page:5 },
  { t:'Light', d:'Light sells the scene. Outdoors, a sun casts shadows and the sky tints everything; indoors, lamps take over. Lights are expensive to draw, so this campus keeps just 8 lamps switched on and moves them to wherever you are.', page:6 },
  { t:'Effects', d:'Post effects are the finishing pass over the whole picture: glow (bloom) around bright lights, soft shading in corners (ambient occlusion) and color grading.', page:7 },
  { t:'Physics', d:'A physics engine moves things with gravity, mass and collisions. The Recess Yard runs a physics engine called Rapier, stepping the world 60 times a second. Drop some balls and watch them bounce.', page:8 },
  { t:'Life', d:'Life makes a world feel real: people who move, rides that run and things you can tap. Tapping works by casting a ray from your finger into the scene; walking uses A* (A-star) pathfinding on a grid.', page:9 },
  { t:'Publish', d:'Ship it! This whole campus is one web page, with no app store and no download, so it runs on phones, Chromebooks and laptops. Then watch real people use it, listen, and make it better.', page:12 }
];
function dioMat(hex, extra){ const m = new THREE.MeshStandardMaterial(Object.assign({ color:srgb(hex), roughness:0.75 }, extra || {})); DIO.mats.push(m); return m; }
function dioSketch(){
  const W = 1100, H = 700, c = mk(W, H), ctx = c.getContext('2d'), r = rnd(3);
  ctx.fillStyle = '#f4efe2'; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = 'rgba(80,110,160,0.18)'; ctx.lineWidth = 2; for (let y = 40; y < H; y += 34){ ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  const pencil = (fn) => { ctx.strokeStyle = 'rgba(40,40,48,0.78)'; ctx.lineWidth = 3; ctx.lineCap = 'round'; for (let k = 0; k < 2; k++){ ctx.save(); ctx.translate((r() - 0.5) * 3, (r() - 0.5) * 3); fn(); ctx.restore(); } };
  const X = (x) => (x + 1.0) / 2.0 * W, Z = (z) => (z + 0.6) / 1.2 * H;
  pencil(() => { ctx.strokeRect(X(-0.78), Z(-0.4), 0.36 / 2 * W, 0.5 / 1.2 * H); ctx.strokeRect(X(-0.7), Z(0.2), 0.3 / 2 * W, 0.3 / 1.2 * H); ctx.strokeRect(X(-0.3), Z(-0.5), 0.4 / 2 * W, 0.24 / 1.2 * H); });
  pencil(() => { ctx.beginPath(); for (let z = -0.6; z <= 0.6; z += 0.02){ const x = X(0.3 + Math.sin(z * 4) * 0.06); z === -0.6 ? ctx.moveTo(x - 40, Z(z)) : ctx.lineTo(x - 40, Z(z)); } ctx.stroke(); ctx.beginPath(); for (let z = -0.6; z <= 0.6; z += 0.02){ const x = X(0.3 + Math.sin(z * 4) * 0.06); z === -0.6 ? ctx.moveTo(x + 40, Z(z)) : ctx.lineTo(x + 40, Z(z)); } ctx.stroke(); });
  pencil(() => { ctx.beginPath(); ctx.arc(X(0.72), Z(0.28), 80, 0, Math.PI * 2); ctx.stroke(); ctx.beginPath(); ctx.moveTo(X(-0.42), Z(0.05)); ctx.quadraticCurveTo(X(0.0), Z(0.15), X(0.4), Z(0.0)); ctx.stroke(); });
  ctx.fillStyle = 'rgba(40,40,48,0.85)'; ctx.font = 'italic 400 40px ' + F.display; ctx.textAlign = 'center';
  ctx.fillText('museum', X(-0.6), Z(-0.12)); ctx.fillText('library', X(-0.55), Z(0.37)); ctx.fillText('school', X(-0.1), Z(-0.36)); ctx.fillText('river', X(0.3), Z(-0.5)); ctx.fillText('coaster?', X(0.72), Z(0.3)); ctx.fillText('path →', X(0.0), Z(0.2));
  ctx.font = '700 30px ' + F.type; ctx.fillStyle = '#c4572f'; ctx.textAlign = 'left'; ctx.fillText('IDEA: a campus you can walk through in a browser', 30, H - 30);
  return c;
}
function dioGroundCanvas(){
  const W = 1024, H = 640, c = mk(W, H), ctx = c.getContext('2d'), r = rnd(12);
  ctx.fillStyle = '#5f8f45'; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 9000; i++){ ctx.fillStyle = r() < 0.5 ? 'rgba(255,255,220,0.07)' : 'rgba(0,40,0,0.1)'; ctx.fillRect(r() * W, r() * H, 3, 3); }
  const X = (x) => (x + 1.0) / 2.0 * W, Z = (z) => (z + 0.6) / 1.2 * H;
  ctx.strokeStyle = '#d6c08a'; ctx.lineWidth = 26; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(X(-0.42), Z(0.05)); ctx.quadraticCurveTo(X(0.0), Z(0.15), X(0.42), Z(0.0)); ctx.lineTo(X(0.92), Z(0.0)); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(X(-0.1), Z(-0.26)); ctx.lineTo(X(-0.1), Z(0.1)); ctx.stroke();
  return c;
}
function dioBlob(){ const S = 128, c = mk(S, S), ctx = c.getContext('2d'), g = ctx.createRadialGradient(S / 2, S / 2, 0, S / 2, S / 2, S / 2); g.addColorStop(0, 'rgba(0,0,0,0.55)'); g.addColorStop(0.6, 'rgba(0,0,0,0.25)'); g.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, S, S); return c; }
function buildDiorama(){
  const root = new THREE.Group(); root.position.set(DIO.x, DIO.y, DIO.z); root.rotation.y = Math.PI; root.userData.noMerge = true; scene.add(root); DIO.root = root;
  const G = (k) => { const g = new THREE.Group(); root.add(g); DIO.groups[k] = g; return g; };
  const clay = dioMat(0xb9b8b2, { flatShading:true, roughness:0.85 });
  DIO.clay = clay;
  /* Step 0: the sketch on paper */
  const sk = G('sketch'); const sp = new THREE.Mesh(new THREE.PlaneGeometry(2.0, 1.2), new THREE.MeshStandardMaterial({ map:tex(dioSketch()), roughness:0.9 })); sp.rotation.x = -Math.PI / 2; sp.position.y = 0.004; sk.add(sp);
  /* The ground: gray at first, then grass with paths */
  DIO.groundGray = dioMat(0x9c9b96, { roughness:0.95 }); DIO.groundGrass = dioMat(0xffffff, { map:tex(dioGroundCanvas()), roughness:1 });
  const ground = new THREE.Mesh(new THREE.BoxGeometry(2.0, 0.03, 1.2), DIO.groundGray); ground.position.y = -0.012; root.add(ground); DIO.ground = ground;
  /* Step 1: blockout boxes */
  const bl = G('block');
  for (const [w, h, d, x, z] of [[0.36, 0.2, 0.5, -0.6, -0.15], [0.3, 0.26, 0.3, -0.55, 0.35], [0.4, 0.18, 0.24, -0.1, -0.38], [0.14, 0.006, 1.2, 0.3, 0], [0.26, 0.24, 0.26, 0.72, 0.28], [0.28, 0.04, 0.08, 0.3, 0.0]]){ const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), clay); m.position.set(x, h / 2, z); bl.add(m); }
  for (const [x, z] of [[0.62, -0.35], [0.85, -0.2], [-0.25, 0.42], [0.1, 0.45], [0.55, 0.5]]){ const m = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.16, 8), clay); m.position.set(x, 0.08, z); bl.add(m); }
  /* Step 2+: the models (shown in clay, then in color) */
  const md = G('models');
  const model = (geo, color, x, y, z, ry, extra) => { const col = dioMat(color, extra); const m = new THREE.Mesh(geo, clay); m.position.set(x, y, z); if (ry) m.rotation.y = ry; m.userData.col = col; md.add(m); DIO.models.push(m); return m; };
  const gable = (w, d, h) => { const s = new THREE.Shape(); s.moveTo(-w / 2, 0); s.lineTo(w / 2, 0); s.lineTo(0, h); s.closePath(); const g = new THREE.ExtrudeGeometry(s, { depth:d, bevelEnabled:false }); g.translate(0, 0, -d / 2); return g; };
  model(new THREE.BoxGeometry(0.36, 0.16, 0.5), 0xe4ddcf, -0.6, 0.08, -0.15);
  model(gable(0.4, 0.54, 0.1), 0x5d6164, -0.6, 0.16, -0.15, 0, { roughness:0.9 }).rotation.y = Math.PI / 2;
  for (let i = 0; i < 4; i++) model(new THREE.CylinderGeometry(0.012, 0.012, 0.15, 10), 0xf4efe2, -0.4, 0.075, -0.33 + i * 0.12);
  model(new THREE.BoxGeometry(0.3, 0.24, 0.3), 0xd8c9a8, -0.55, 0.12, 0.35);
  model(new THREE.BoxGeometry(0.32, 0.03, 0.32), 0x9fc3d6, -0.55, 0.255, 0.35, 0, { roughness:0.2, metalness:0.3 });
  model(new THREE.BoxGeometry(0.4, 0.15, 0.24), 0xb5634a, -0.1, 0.075, -0.38);
  model(new THREE.BoxGeometry(0.42, 0.02, 0.26), 0x5d6164, -0.1, 0.16, -0.38);
  const river = new THREE.Shape(); river.moveTo(0.22, -0.6); for (let z = -0.6; z <= 0.6; z += 0.05) river.lineTo(0.23 + Math.sin(z * 4) * 0.05, z); for (let z = 0.6; z >= -0.6; z -= 0.05) river.lineTo(0.37 + Math.sin(z * 4) * 0.05, z); river.closePath();
  const rg = new THREE.ShapeGeometry(river); rg.rotateX(-Math.PI / 2);
  DIO.water = model(rg, 0x3d7fb5, 0, 0.006, 0, 0, { roughness:0.15, metalness:0.1 });
  model(new THREE.BoxGeometry(0.3, 0.02, 0.09), 0x8a6a48, 0.3, 0.03, 0.0);
  for (const s of [-1, 1]) model(new THREE.BoxGeometry(0.3, 0.03, 0.006), 0x5a3b22, 0.3, 0.055, s * 0.042);
  const loop = model(new THREE.TorusGeometry(0.11, 0.01, 8, 40), 0xc4572f, 0.72, 0.13, 0.28, 0, { metalness:0.4, roughness:0.4 }); loop.rotation.y = Math.PI / 2 - 0.3;
  model(new THREE.BoxGeometry(0.36, 0.01, 0.03), 0xc4572f, 0.72, 0.02, 0.28, 0.3, { metalness:0.4, roughness:0.4 });
  const trees = [[0.62, -0.35], [0.85, -0.2], [-0.25, 0.42], [0.1, 0.45], [0.55, 0.5], [-0.9, 0.48], [-0.88, -0.5], [0.95, 0.52]];
  for (const [x, z] of trees){ model(new THREE.CylinderGeometry(0.012, 0.016, 0.07, 8), 0x6b4a2b, x, 0.035, z); model(new THREE.ConeGeometry(0.06, 0.15, 10), 0x3f7a35, x, 0.14, z); }
  DIO.lamps = [];
  for (const [x, z] of [[-0.3, 0.12], [0.05, 0.16], [0.55, 0.06]]){ model(new THREE.CylinderGeometry(0.004, 0.004, 0.12, 6), 0x2f363c, x, 0.06, z); const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.014, 12, 8), new THREE.MeshBasicMaterial({ color:0x333333, toneMapped:false })); bulb.position.set(x, 0.125, z); md.add(bulb); DIO.lamps.push(bulb); }
  DIO.windows = [];
  for (const [x, y, z, ry] of [[-0.42, 0.09, -0.02, Math.PI / 2], [-0.42, 0.09, -0.28, Math.PI / 2], [-0.4, 0.14, 0.35, Math.PI / 2], [-0.1, 0.08, -0.259, 0], [-0.22, 0.08, -0.259, 0], [0.02, 0.08, -0.259, 0]]){ const w = new THREE.Mesh(new THREE.PlaneGeometry(0.05, 0.05), new THREE.MeshBasicMaterial({ color:0x2a3138, toneMapped:false })); w.position.set(x, y, z); w.rotation.y = ry; md.add(w); DIO.windows.push(w); }
  /* Step 4: blob shadows and a sky backdrop */
  const sh = G('shadows'), blob = new THREE.MeshBasicMaterial({ map:tex(dioBlob()), transparent:true, depthWrite:false, toneMapped:false });
  for (const [x, z, s] of [[-0.6, -0.15, 0.62], [-0.55, 0.35, 0.44], [-0.1, -0.38, 0.5], [0.72, 0.28, 0.3]].concat(trees.map(([x, z]) => [x + 0.02, z + 0.02, 0.16]))){ const b = new THREE.Mesh(new THREE.PlaneGeometry(s, s), blob); b.rotation.x = -Math.PI / 2; b.position.set(x + 0.04, 0.003, z + 0.03); b.renderOrder = 1; sh.add(b); }
  const sky = mk(512, 256), sx = sky.getContext('2d'), sg = sx.createLinearGradient(0, 0, 0, 256); sg.addColorStop(0, '#5f97d6'); sg.addColorStop(0.75, '#cfe3ef'); sg.addColorStop(1, '#f4e8cf'); sx.fillStyle = sg; sx.fillRect(0, 0, 512, 256);
  sx.fillStyle = '#ffe9a8'; sx.beginPath(); sx.arc(400, 70, 26, 0, Math.PI * 2); sx.fill();
  const back = new THREE.Mesh(new THREE.CylinderGeometry(1.25, 1.25, 0.7, 40, 1, true, Math.PI - 0.9, 1.8), new THREE.MeshBasicMaterial({ map:tex(sky), side:THREE.BackSide, toneMapped:false }));
  back.position.set(0, 0.35, 0.55); sh.add(back); back.userData.keepBasic = true;
  /* Step 6: physics balls */
  const bg = G('balls');
  for (let i = 0; i < 4; i++){ const b = new THREE.Mesh(new THREE.SphereGeometry(0.03, 16, 12), dioMat([0xff5a8a, 0xffd166, 0x5ee6c8, 0x7aa8ff][i], { roughness:0.35 })); b.visible = false; bg.add(b); DIO.balls.push({ m:b, v:new THREE.Vector3(), on:false }); }
  /* Step 7: people, a coaster car and a flag */
  const lf = G('life'), skin = dioMat(0xc99c7a), shirts = [0xc4572f, 0x2f5d7a, 0xf2c14e, 0x5aa08c];
  const route = [[-0.42, 0.05], [0.0, 0.12], [0.42, 0.0], [0.9, 0.0], [0.42, 0.0], [0.0, 0.12]];
  for (let i = 0; i < 4; i++){ const p = new THREE.Group(); const body = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.014, 0.05, 8), dioMat(shirts[i])); body.position.y = 0.025; p.add(body); const hd = new THREE.Mesh(new THREE.SphereGeometry(0.01, 8, 6), skin); hd.position.y = 0.06; p.add(hd); lf.add(p); DIO.people.push({ g:p, s:i / 4, sp:0.05 + i * 0.012, route }); }
  DIO.car = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.02, 0.02), dioMat(0xffd166)); lf.add(DIO.car);
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.003, 0.003, 0.14, 6), dioMat(0xb9c0c6, { metalness:0.6 })); pole.position.set(-0.26, 0.23, -0.38); lf.add(pole);
  DIO.flag = new THREE.Mesh(new THREE.PlaneGeometry(0.06, 0.035), dioMat(0x5ee6c8, { side:THREE.DoubleSide })); DIO.flag.position.set(-0.23, 0.28, -0.38); lf.add(DIO.flag);
  /* Step 8: it's live */
  const lv = G('live');
  const sc = mk(512, 160), sctx = sc.getContext('2d'); sctx.fillStyle = '#16232b'; sctx.fillRect(0, 0, 512, 160); sctx.fillStyle = '#ff5a5a'; sctx.beginPath(); sctx.arc(56, 80, 20, 0, Math.PI * 2); sctx.fill(); sctx.fillStyle = '#ffffff'; sctx.font = '700 64px ' + F.ui; sctx.fillText('LIVE', 96, 102); sctx.font = '400 26px ' + F.type; sctx.fillStyle = '#5ee6c8'; sctx.fillText('on the web', 290, 100);
  const sign = new THREE.Mesh(new THREE.PlaneGeometry(0.42, 0.13), new THREE.MeshBasicMaterial({ map:tex(sc), toneMapped:false, side:THREE.DoubleSide })); sign.position.set(0, 0.48, -0.1); lv.add(sign); DIO.sign = sign; sign.userData.keepBasic = true;
  const cg = new THREE.BufferGeometry(), N = 160, cp = new Float32Array(N * 3), cc = new Float32Array(N * 3), cr = rnd(8);
  for (let i = 0; i < N; i++){ cp[i * 3] = (cr() - 0.5) * 1.6; cp[i * 3 + 1] = 0.2 + cr() * 0.5; cp[i * 3 + 2] = (cr() - 0.5) * 1.0; const col = new THREE.Color([0xff5a8a, 0xffd166, 0x5ee6c8, 0x7aa8ff, 0xc38bff][(cr() * 5) | 0]); cc[i * 3] = col.r; cc[i * 3 + 1] = col.g; cc[i * 3 + 2] = col.b; }
  cg.setAttribute('position', new THREE.BufferAttribute(cp, 3)); cg.setAttribute('color', new THREE.BufferAttribute(cc, 3));
  DIO.confetti = new THREE.Points(cg, new THREE.PointsMaterial({ size:0.02, vertexColors:true, toneMapped:false })); DIO.confetti.userData.base = cp.slice(); lv.add(DIO.confetti);
  dioApply();
}
function dioApply(){
  const s = DIO.step, G = DIO.groups;
  G.sketch.visible = s === 0; G.block.visible = s === 1; G.models.visible = s >= 2; G.shadows.visible = s >= 4; G.balls.visible = s >= 6; G.life.visible = s >= 7; G.live.visible = s >= 8;
  DIO.ground.visible = s >= 1;
  DIO.ground.material = s >= 3 ? DIO.groundGrass : DIO.groundGray;
  for (const m of DIO.models) m.material = s >= 3 ? m.userData.col : DIO.clay;
  const on = s >= 4, hot = s >= 5;
  for (const l of DIO.lamps) l.material.color.setHex(on ? (hot ? 0xfff0b0 : 0xbfae80) : 0x333333).multiplyScalar(hot ? 3.2 : 1);
  for (const w of DIO.windows) w.material.color.setHex(on ? 0xffd98a : 0x2a3138).multiplyScalar(hot ? 1.4 : 1);
  for (const m of DIO.mats) if (m.wireframe !== (DIO.xray && s >= 1)){ m.wireframe = DIO.xray && s >= 1; }
  if (s < 6) for (const b of DIO.balls){ b.on = false; b.m.visible = false; }
  wake();
}
function dioDrop(){
  const r = Math.random;
  DIO.balls.forEach((b, i) => { b.on = true; b.m.visible = true; b.m.position.set(-0.5 + r() * 1.2, 0.5 + i * 0.12, -0.35 + r() * 0.7); b.v.set((r() - 0.5) * 0.4, 0, (r() - 0.5) * 0.3); });
  wake();
}
function dioGroundAt(x, z){
  const boxes = [[-0.6, -0.15, 0.18, 0.25, 0.16], [-0.55, 0.35, 0.15, 0.15, 0.27], [-0.1, -0.38, 0.2, 0.12, 0.17]];
  for (const [bx, bz, hx, hz, h] of boxes) if (Math.abs(x - bx) < hx && Math.abs(z - bz) < hz) return h;
  return 0;
}
STATIONS.diorama = {
  id:'diorama', room:'world', kick:'Room 104 · Layer table',
  title(){ return (DIO.step + 1) + '. ' + DIO_STEPS[DIO.step].t; },
  stepText(){ return 'Layer ' + (DIO.step + 1) + ' of ' + DIO_STEPS.length; },
  view(){ return { x:DIO.x, z:DIO.z - (narrow() ? 2.2 : 1.85), yaw:Math.PI, pitch:narrow() ? -0.36 : -0.3 }; },
  render(body, btns){
    const S = DIO_STEPS[DIO.step];
    body.appendChild(stSteps(DIO_STEPS.map((x) => x.t), DIO.step));
    body.appendChild(stEl('p', 'stp', S.d));
    if (DIO.step === DIO_STEPS.length - 1) body.appendChild(stEl('p', 'stresult', 'You built a world, layer by layer. Every 3D game, film and XR app is made with these same layers.'));
    btns.appendChild(stBtn('Back', () => { DIO.step--; dioApply(); stRender(); }, false, DIO.step === 0));
    if (DIO.step < DIO_STEPS.length - 1) btns.appendChild(stBtn('Add the next layer', () => { DIO.step++; dioApply(); if (DIO.step === 6) dioDrop(); if (DIO.step === DIO_STEPS.length - 1) award('worldbuilder'); stRender(); }, true));
    if (DIO.step >= 6) btns.appendChild(stBtn('Drop balls', dioDrop));
    if (DIO.step >= 1) btns.appendChild(stToggle('X-ray triangles', DIO.xray, () => { DIO.xray = !DIO.xray; dioApply(); STN.cur.keepScroll = true; stRender(); }));
    btns.appendChild(stBtn('Read about it', () => { closeStation(); openBook(BOOK['world-builder'], S.page); }));
  },
  tick(dt){
    if (!DIO.root || !WING.school || !WING.school.visible || DIO.step < 5 || REDUCED) return false;
    if (roomAt(cam.x, cam.z).id !== 'world') return false;
    DIO.t += dt;
    if (DIO.water && DIO.water.material.map == null){ DIO.water.material.emissive = DIO.water.material.emissive || new THREE.Color(); }
    if (DIO.water) DIO.water.material.emissive.setRGB(0.02, 0.05 + 0.03 * Math.sin(DIO.t * 2.2), 0.09 + 0.04 * Math.sin(DIO.t * 1.7));
    for (const b of DIO.balls){
      if (!b.on) continue;
      b.v.y -= 9.81 * 0.35 * dt; b.m.position.addScaledVector(b.v, dt);
      const p = b.m.position, floor = dioGroundAt(p.x, p.z) + 0.03;
      if (p.y < floor){ p.y = floor; if (b.v.y < 0) b.v.y = -b.v.y * 0.62; b.v.x *= 0.96; b.v.z *= 0.96; if (Math.abs(b.v.y) < 0.05) b.v.y = 0; }
      if (Math.abs(p.x) > 0.97){ p.x = Math.sign(p.x) * 0.97; b.v.x *= -0.7; } if (Math.abs(p.z) > 0.57){ p.z = Math.sign(p.z) * 0.57; b.v.z *= -0.7; }
      b.m.rotation.z -= b.v.x * dt / 0.03; b.m.rotation.x += b.v.z * dt / 0.03;
    }
    if (DIO.step >= 7){
      for (const P of DIO.people){
        P.s = (P.s + dt * P.sp) % 1;
        const R = P.route, n = R.length, f = P.s * n, i = Math.floor(f), k = f - i, a = R[i], b = R[(i + 1) % n];
        P.g.position.set(a[0] + (b[0] - a[0]) * k, 0, a[1] + (b[1] - a[1]) * k + 0.02); P.g.rotation.y = Math.atan2(b[0] - a[0], b[1] - a[1]);
        P.g.position.y = Math.abs(Math.sin(DIO.t * 9 + P.sp * 40)) * 0.004;
      }
      const ang = DIO.t * 2.4, c = Math.cos(Math.PI / 2 - 0.3), s = Math.sin(Math.PI / 2 - 0.3);
      const lx = Math.cos(ang) * 0.11, ly = Math.sin(ang) * 0.11;
      DIO.car.position.set(0.72 + lx * c, 0.13 + ly, 0.28 - lx * s); DIO.car.rotation.set(0, Math.PI / 2 - 0.3, ang + Math.PI / 2);
      DIO.flag.rotation.y = Math.sin(DIO.t * 5) * 0.35; DIO.flag.scale.x = 1 + Math.sin(DIO.t * 7) * 0.06;
    }
    if (DIO.step >= 8){
      const pos = DIO.confetti.geometry.attributes.position, base = DIO.confetti.userData.base;
      for (let i = 0; i < pos.count; i++){ let y = base[i * 3 + 1] - ((DIO.t * 0.12 + i * 0.013) % 0.6); pos.setY(i, y < 0.03 ? y + 0.6 : y); pos.setX(i, base[i * 3] + Math.sin(DIO.t * 2 + i) * 0.02); }
      pos.needsUpdate = true; DIO.sign.position.y = 0.48 + Math.sin(DIO.t * 2) * 0.015;
    }
    return true;
  }
};

/* ---------- Monitors, toolkit and the pipeline banner ---------- */
function drawCodeScreen(file, lines){
  const W = 720, H = 440, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#0f1620'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#1b2533'; ctx.fillRect(0, 0, W, 44);
  for (const [i, col] of [[0, '#ff5f57'], [1, '#febc2e'], [2, '#28c840']]){ ctx.fillStyle = col; ctx.beginPath(); ctx.arc(24 + i * 22, 22, 7, 0, Math.PI * 2); ctx.fill(); }
  ctx.fillStyle = '#9fb3c8'; ctx.font = '400 20px ' + F.type; ctx.fillText(file, 100, 29);
  ctx.font = '400 21px ' + F.type;
  lines.forEach((l, i) => {
    const y = 84 + i * 30; ctx.fillStyle = '#4b5b6e'; ctx.textAlign = 'right'; ctx.fillText(String(i + 1), 40, y); ctx.textAlign = 'left';
    let x = 56; for (const [t, col] of l){ ctx.fillStyle = col; ctx.fillText(t, x, y); x += ctx.measureText(t).width; }
  });
  return c;
}
const CK = '#c792ea', CF = '#82aaff', CS = '#c3e88d', CN = '#f78c6c', CT = '#e6edf3', CC = '#5c6c80';
const SCREENS = [
  { file:'models.js', page:4, lines:[[['// a mesh = a shape + a material', CC]], [['const ', CK], ['box', CT], [' = ', CT], ['new ', CK], ['THREE', CT], ['.', CT], ['Mesh', CF], ['(', CT]], [['  new ', CK], ['THREE', CT], ['.', CT], ['BoxGeometry', CF], ['(', CT], ['1', CN], [', ', CT], ['1', CN], [', ', CT], ['1', CN], ['),', CT]], [['  new ', CK], ['THREE', CT], ['.', CT], ['MeshStandardMaterial', CF], ['({', CT]], [['    color: ', CT], ['\'#f2c14e\'', CS], [', roughness: ', CT], ['0.5', CN]], [['  })', CT]], [[');', CT]], [['box', CT], ['.position.', CT], ['set', CF], ['(', CT], ['0', CN], [', ', CT], ['0.5', CN], [', ', CT], ['0', CN], [');', CT]], [['scene', CT], ['.', CT], ['add', CF], ['(box);', CT]]] },
  { file:'lights.js', page:6, lines:[[['// a sun that casts shadows', CC]], [['const ', CK], ['sun', CT], [' = ', CT], ['new ', CK], ['THREE', CT], ['.', CT], ['DirectionalLight', CF], ['(', CT]], [['  ', CT], ['\'#fff0dc\'', CS], [', ', CT], ['3.1', CN], [');', CT]], [['sun', CT], ['.castShadow = ', CT], ['true', CK], [';', CT]], [['scene', CT], ['.', CT], ['add', CF], ['(sun);', CT]], [['', CT]], [['// sky light for soft reflections', CC]], [['scene', CT], ['.environment = ', CT], ['skyTexture', CT], [';', CT]]] },
  { file:'physics.js', page:8, lines:[[['// 60 physics steps every second', CC]], [['const ', CK], ['ball', CT], [' = ', CT], ['world', CT], ['.', CT], ['createRigidBody', CF], ['(', CT]], [['  RAPIER', CT], ['.', CT], ['RigidBodyDesc', CF], ['.', CT], ['dynamic', CF], ['()', CT]], [['    .', CT], ['setTranslation', CF], ['(', CT], ['0', CN], [', ', CT], ['3', CN], [', ', CT], ['0', CN], ['));', CT]], [['world', CT], ['.', CT], ['createCollider', CF], ['(', CT]], [['  RAPIER', CT], ['.', CT], ['ColliderDesc', CF], ['.', CT], ['ball', CF], ['(', CT], ['0.11', CN], ['), ball);', CT]], [['function ', CK], ['tick', CF], ['(){ world.', CT], ['step', CF], ['(); }', CT]]] }
];
const TOOLS = [['three.js', '#ffffff', '#16232b'], ['Blender', '#e07b2a', '#16232b'], ['Godot', '#7aa8ff', '#16232b'], ['Unity', '#e6edf3', '#16232b'], ['Unreal', '#e6edf3', '#16232b'], ['Krita', '#c38bff', '#16232b'], ['Audacity', '#5ee6c8', '#16232b'], ['VS Code', '#82aaff', '#16232b'], ['GitHub', '#e6edf3', '#16232b']];
function drawToolLabel(name, col){
  const c = mk(256, 96), ctx = c.getContext('2d');
  ctx.fillStyle = '#16232b'; ctx.fillRect(0, 0, 256, 96); ctx.fillStyle = col; ctx.fillRect(0, 0, 12, 96);
  ctx.fillStyle = col; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; fit(ctx, name, F.ui, '700', 40, 220); ctx.fillText(name, 134, 50);
  return c;
}
function drawPipeline(){
  const W = 2400, H = 330, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#16232b'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#5ee6c8'; ctx.font = '700 40px ' + F.type; ctx.textAlign = 'left'; ctx.fillText('HOW A WORLD GETS BUILT', 50, 70);
  ctx.fillStyle = 'rgba(239,231,213,0.6)'; ctx.font = '400 30px ' + F.ui; ctx.fillText('Try it layer by layer on the table · Tap any step', 620, 68);
  const cols = ['#f2c14e', '#b9b8b2', '#9fc3d6', '#5aa08c', '#ffd166', '#c38bff', '#ff8f3d', '#ff5a8a', '#5ee6c8'];
  DIO_STEPS.forEach((s, i) => {
    const x = 60 + i * 258, y = 120;
    ctx.fillStyle = cols[i]; ctx.beginPath(); ctx.arc(x + 56, y + 60, 46, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#16232b'; ctx.font = '700 48px ' + F.ui; ctx.textAlign = 'center'; ctx.fillText(String(i + 1), x + 56, y + 77);
    ctx.fillStyle = '#ffffff'; ctx.font = '600 36px ' + F.ui; ctx.fillText(s.t, x + 56, y + 160);
    if (i < DIO_STEPS.length - 1){ ctx.strokeStyle = 'rgba(239,231,213,0.5)'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(x + 118, y + 60); ctx.lineTo(x + 190, y + 60); ctx.stroke(); ctx.beginPath(); ctx.moveTo(x + 178, y + 50); ctx.lineTo(x + 192, y + 60); ctx.lineTo(x + 178, y + 70); ctx.stroke(); }
  });
  return c;
}
function buildWorldRoomContent(M){
  const { x0:X0, z1:Z1 } = R104;
  /* Layer table */
  const top = stdMat(0x2b333c, 0.5), rim = stdMat(0x8a6a48, 0.55);
  addBox(2.6, 0.06, 1.7, top, DIO.x, 0.79, DIO.z);
  for (const sx of [-1.2, 1.2]) for (const sz of [-0.75, 0.75]) addBox(0.08, 0.76, 0.08, top, DIO.x + sx, 0.38, DIO.z + sz);
  addBox(2.12, 0.05, 1.32, rim, DIO.x, 0.845, DIO.z);
  OBST.push({ x:DIO.x - 0.7, z:DIO.z, r:1.05 }, { x:DIO.x + 0.7, z:DIO.z, r:1.05 });
  pickBox(2.6, 0.8, 1.7, DIO.x, 1.2, DIO.z, { station:'diorama' });
  addPlane(0.8, 0.18, basicMat(drawTableCard('LAYER TABLE', 'Build a world, one layer at a time')), DIO.x, 0.62, DIO.z - 0.852, Math.PI);
  buildDiorama();
  /* Pipeline banner */
  const ban = addPlane(6.6, 0.91, basicMat(drawPipeline()), 29.0, 2.62, Z1 - 0.02, Math.PI); ban.userData.station = 'diorama'; pickItems.push(ban);
  /* Code monitors on the desk */
  SCREENS.forEach((s, i) => {
    const x = 26.6 + i * 2.4, g = new THREE.Group(); g.position.set(x, 0.77, Z1 - 0.42);
    addBox(0.08, 0.3, 0.06, stdMat(0x1d2124, 0.4), 0, 0.15, 0.06, 0, g);
    addBox(0.3, 0.02, 0.2, stdMat(0x1d2124, 0.4), 0, 0.01, 0.06, 0, g);
    addBox(0.96, 0.6, 0.04, stdMat(0x111418, 0.4), 0, 0.55, 0, 0, g);
    const scr = addPlane(0.92, 0.562, basicMat(drawCodeScreen(s.file, s.lines)), 0, 0.55, -0.021, Math.PI, g);
    scr.userData.hb = s.page; scr.userData.keepBasic = true; pickItems.push(scr);
    addBox(0.44, 0.015, 0.15, stdMat(0x2b333c, 0.5), 0, 0.008, -0.28, 0, g);
    scene.add(g);
  });
  /* Toolkit shelves */
  TOOLS.forEach(([name, col], i) => {
    const row = Math.floor(i / 3), k = i % 3, z = 1.2 + k * 1.5, y = 0.37 + (2 - row) * 0.6;
    const box = addBox(0.36, 0.32, 0.5, stdMat(0x1d2124, 0.6), X0 + 0.26, y + 0.16, z);
    const lab = addPlane(0.36, 0.135, basicMat(drawToolLabel(name, col)), X0 + 0.442, y + 0.16, z, Math.PI / 2);
    lab.userData.hb = 2; pickItems.push(lab);
  });
  addPlane(1.8, 0.32, basicMat(drawTableCard('FREE TOOLS TO START', 'Tap a box to learn what it does')), X0 + 0.012, 2.6, 3.0, Math.PI / 2);
  /* A copy of the World Builder’s Handbook on the desk */
  const hb = new THREE.Mesh(new THREE.PlaneGeometry(0.24, 0.33), basicMat(drawBookCover(WB_BOOK, 384, 526), 0xe2dace));
  hb.rotation.set(-0.3, Math.PI, 0, 'YXZ'); hb.position.set(27.8, 0.93, Z1 - 0.514); hb.userData.book = WB_BOOK; scene.add(hb); pickItems.push(hb);
  addBox(0.25, 0.34, 0.03, stdMat(0x3b3550, 0.7), 27.8, 0.93, Z1 - 0.485).rotation.x = 0.3;
  addBox(0.2, 0.02, 0.14, stdMat(0x1d2124, 0.5), 27.8, 0.78, Z1 - 0.45);
  addPlane(0.5, 0.11, basicMat(drawTableCard('THE HANDBOOK', 'Tap to read')), 27.8, 0.71, Z1 - 0.785, Math.PI);
}

/* ---------- The World Builder’s Handbook ---------- */
const WB_BOOK = { id:'world-builder', subject:'worlds', icon:'code', table:false, title:'World Builder’s Handbook', sub:'How to make 3D worlds and games like this campus', pages:[
  { h:'Start with why', b:['Before any 3D work, decide who your world is for and what they will do there. Write one sentence: “In this world, you can …”', 'This campus began as a list: a museum that tells a story, a library you can read in, a school where every class is hands-on and a recess yard for fun. Then came a rough map on paper showing how to walk from one to the next.', { note:'Start small. A single room that works beats a giant world that doesn’t.' }] },
  { h:'Free tools to start', b:['You can build real 3D worlds with free tools:', { li:['three.js: draws 3D in a web page. This campus runs on it.', 'Blender: free, professional software for modeling, sculpting and animation.', 'Godot: a free, open-source game engine.', 'Unity and Unreal Engine: the engines behind many games and XR apps; both are free to start learning.', 'Krita or GIMP: paint textures and images.', 'Audacity: record and edit sound.', 'VS Code: a free code editor.', 'Git and GitHub: save every version of your project and share it.', 'Hosting like Vercel, Netlify or itch.io: put your world online.'] }, { note:'Pick one tool and finish one small project before adding the next.' }] },
  { h:'Block it out', b:['Build the layout from plain boxes first, then walk through it. Studios call this a blockout or graybox.', 'Use real sizes. In this campus your eyes are 1.62 meters off the floor, doorways are 1.8 to 3.2 meters wide and ceilings are 3.4 to 7.6 meters high. You walk at 3 meters per second, about twice as fast as a real walk, because walking feels slow on a screen.', 'Move walls and rooms around until walking through feels good. Changing a box is quick; changing a finished building is not.'] },
  { h:'Models and meshes', b:['Every 3D model is a mesh: points in space (vertices) joined into triangles. A cube needs 12 triangles; a smooth sphere might use hundreds.', 'Artists usually model in Blender and export a file like glTF. This campus builds nearly everything from code instead: boxes, cylinders, spheres, lathed shapes like the lab flask and extruded shapes like roofs.', { code:'const box = new THREE.Mesh(\n  new THREE.BoxGeometry(1, 1, 1),\n  new THREE.MeshStandardMaterial({ color: \'#f2c14e\' })\n);\nscene.add(box);' }, { note:'When a scene needs thousands of copies of one thing, like grass blades or books, instancing draws them all at once.' }] },
  { h:'Materials', b:['A material describes a surface. Physically based rendering (PBR) uses a few simple dials:', { li:['Color (albedo): the surface’s own color.', 'Roughness: 0 is perfectly smooth and glossy (a mirror if it’s also metal), 1 is chalk.', 'Metalness: metal or not.', 'Normal map: fakes small bumps, like brick edges or wood grain, without extra triangles.'] }, 'Textures are images wrapped onto meshes. Most textures here, from the bricks to the blueprints, are drawn by code onto a canvas as the campus loads.'] },
  { h:'Light and shadow', b:['Light makes a scene believable. Common kinds:', { li:['Directional light: the sun. Parallel rays and crisp shadows.', 'Point lights: lamps that shine in every direction.', 'Image-based light: a picture of the sky or room that adds soft light and reflections.'] }, 'Shadows are drawn from the light’s point of view into a shadow map. Lights cost speed: every lamp adds work to every lit pixel. This campus keeps 8 lamps switched on at once and moves them to the rooms near you.'] },
  { h:'Effects', b:['Post effects run on the finished picture, like filters:', { li:['Bloom: bright lights glow and bleed softly.', 'Ambient occlusion: darkens corners and creases where light can’t reach.', 'Tone mapping: squeezes very bright and very dark light into what a screen can show.', 'Color grading: sets the mood, like a filter on a photo.'] }, 'Fog is different: it fades faraway things as each object is drawn, which hints at distance and hides the edge of the world.', { note:'Effects are seasoning. Set Graphics to Low in About to see the campus without bloom, ambient occlusion and grading.' }] },
  { h:'Physics', b:['A physics engine moves objects with gravity, mass, friction and collisions. Each object has a simple collider shape (a ball, a box or a capsule) that’s much cheaper to test than its full mesh.', 'The Recess Yard uses the Rapier physics engine and steps the world at a fixed 60 times per second, then smooths the motion between steps so it looks right at any frame rate.', { code:'import RAPIER from \'@dimforge/rapier3d-compat\';\nawait RAPIER.init();\nconst world = new RAPIER.World({ x: 0, y: -9.81, z: 0 });\nconst ball = world.createRigidBody(\n  RAPIER.RigidBodyDesc.dynamic().setTranslation(0, 3, 0)\n);\nworld.createCollider(RAPIER.ColliderDesc.ball(0.11), ball);\nworld.step();' }] },
  { h:'Interaction', b:['To know what you tapped, the campus casts a ray, an invisible line, from the camera through your finger into the scene and finds the first thing it hits.', 'To walk you somewhere, it lays a grid over the floors and uses A* (A-star) pathfinding to find the shortest route around walls and furniture.', 'The virtual staff answer common questions from what the campus knows, and can use AI for harder ones when it’s allowed.'] },
  { h:'Make it fast', b:['A smooth world draws a new frame about 60 times per second, which gives the computer about 16 milliseconds for each one.', { li:['Fewer draw calls: merge objects that share a material, and use instancing for repeats.', 'Hide what you can’t see: this campus only draws rooms that are in view.', 'Quality levels: lower settings for older phones.', 'Dynamic resolution: draw fewer pixels when frames run slow, like many console games do.'] }] },
  { h:'Your first world in 20 lines', b:['Paste this into a file named index.html and open it in a browser. You’ll see a spinning box on grass.', { code:'<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js"}}<\/script>\n<script type="module">\nimport * as THREE from \'three\';\nconst scene = new THREE.Scene();\nscene.background = new THREE.Color(\'#9cc3e4\');\nconst camera = new THREE.PerspectiveCamera(60, innerWidth / innerHeight, 0.1, 100);\ncamera.position.set(0, 1.6, 5);\nconst renderer = new THREE.WebGLRenderer({ antialias: true });\nrenderer.setSize(innerWidth, innerHeight);\ndocument.body.appendChild(renderer.domElement);\nscene.add(new THREE.HemisphereLight(\'#ffffff\', \'#445533\', 2));\nconst ground = new THREE.Mesh(new THREE.PlaneGeometry(20, 20), new THREE.MeshStandardMaterial({ color: \'#5d8f43\' }));\nground.rotation.x = -Math.PI / 2;\nscene.add(ground);\nconst box = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshStandardMaterial({ color: \'#f2c14e\' }));\nbox.position.y = 0.5;\nscene.add(box);\nrenderer.setAnimationLoop(() => { box.rotation.y += 0.01; renderer.render(scene, camera); });\n<\/script>' }, 'Now change the color, add a second box, or move the camera. That’s world building.'] },
  { h:'Ship it and keep going', b:['Put your world online so people can try it, then watch them use it. Where do they get stuck? What do they love? Fix one thing at a time.', 'A learning path that works: HTML, CSS and JavaScript, then three.js, then Blender basics, then a weekend game jam with friends.', 'Jobs in this world include game developer, technical artist, 3D artist, level designer, XR developer and graphics engineer.'] }
] };
BOOKS.push(WB_BOOK); BOOK[WB_BOOK.id] = WB_BOOK;
