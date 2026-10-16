/* ================================================================
   Workshop School: Rooms 102, 103 and 104
   ================================================================ */
const R102 = { x0:25.6, x1:34, z0:-13, z1:-4.75 };   /* Science Lab */
const R103 = { x0:12.2, x1:24, z0:-1.25, z1:7 };     /* Blueprint Lab */
const R104 = { x0:24, x1:34, z0:-1.25, z1:7 };       /* World Builder Studio */
const SCHOOL_DOORS = { 101:{ x:19, side:'s' }, 102:{ x:29, side:'s' }, 103:{ x:19, side:'n' }, 104:{ x:29, side:'n' } };
const ROOM_NAMES = { 101:'3D Art Studio', 102:'Science Lab', 103:'Blueprint Lab', 104:'World Builder Studio' };

/* ---------- Surfaces and signs ---------- */
function canvasBandWall(top, low, band, lowH){
  const W = 64, H = 512, c = mk(W, H), ctx = c.getContext('2d');
  const split = Math.round(H * (1 - lowH / 3.6));
  ctx.fillStyle = top; ctx.fillRect(0, 0, W, split);
  ctx.fillStyle = low; ctx.fillRect(0, split, W, H - split);
  if (band){ ctx.fillStyle = band; ctx.fillRect(0, split - 5, W, 5); }
  return c;
}
function canvasCarpet(){
  const S = 512, c = mk(S, S), ctx = c.getContext('2d'), r = rnd(71), n = 4, t = S / n;
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++){
    ctx.fillStyle = (i + j) % 2 ? '#2b3138' : '#30373f'; ctx.fillRect(i * t, j * t, t, t);
    ctx.strokeStyle = 'rgba(255,255,255,0.05)'; ctx.lineWidth = 2;
    for (let k = 0; k < 9; k++){ const y = j * t + 6 + k * (t - 12) / 8; ctx.beginPath(); if ((i + j) % 2){ ctx.moveTo(i * t + 4, y); ctx.lineTo(i * t + t - 4, y); } else { const x = i * t + 6 + k * (t - 12) / 8; ctx.moveTo(x, j * t + 4); ctx.lineTo(x, j * t + t - 4); } ctx.stroke(); }
    for (let k = 0; k < 900; k++){ ctx.fillStyle = r() < 0.5 ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.12)'; ctx.fillRect(i * t + r() * t, j * t + r() * t, 2, 2); }
  }
  return c;
}
function canvasFrosted(W, H, tint){
  const c = mk(W || 256, H || 256), ctx = c.getContext('2d'), w = c.width, h = c.height;
  const g = ctx.createLinearGradient(0, 0, 0, h); g.addColorStop(0, tint || '#f4f9fc'); g.addColorStop(1, '#d5e2ea');
  ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
  const r = rnd(4); for (let i = 0; i < 1400; i++){ ctx.fillStyle = 'rgba(255,255,255,' + (0.05 + r() * 0.08) + ')'; ctx.fillRect(r() * w, r() * h, 2, 2); }
  ctx.fillStyle = 'rgba(70,95,110,0.18)'; ctx.fillRect(0, h * 0.5 - 2, w, 4);
  return c;
}
function drawBladeSign(num, name, col){
  const W = 900, H = 330, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#16232b'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = col; ctx.fillRect(0, 0, 26, H);
  ctx.fillStyle = col; ctx.font = '700 118px ' + F.ui; ctx.textAlign = 'left'; ctx.fillText(num, 70, 140);
  ctx.fillStyle = '#ffffff'; fit(ctx, name, F.ui, '600', 70, W - 110); ctx.fillText(name, 70, 250);
  ctx.fillStyle = 'rgba(255,255,255,0.5)'; ctx.font = '700 30px ' + F.type; ctx.fillText('OPEN · COME IN', 72, 302);
  return c;
}
function drawLabBoard(){
  const W = 1500, H = 640, c = mk(W, H), ctx = c.getContext('2d'), r = rnd(19);
  ctx.fillStyle = '#f7f8f6'; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 18; i++){ ctx.fillStyle = 'rgba(120,130,140,0.04)'; ctx.beginPath(); ctx.ellipse(r() * W, r() * H, 60 + r() * 160, 14 + r() * 40, r() * 3, 0, Math.PI * 2); ctx.fill(); }
  ctx.fillStyle = '#1d3b52'; ctx.textAlign = 'left'; ctx.font = '700 34px ' + F.type; ctx.fillText('TODAY’S LABS · ROOM 102', 60, 82);
  ctx.font = '400 82px ' + F.display; ctx.fillText('Measure it for real', 60, 175);
  const labs = [['#c4572f', '1', 'Sieve analysis (PSD)', 'How big are the grains in a sand sample?'], ['#7a2e8a', '2', 'Acid–base titration', 'How concentrated is the mystery acid?'], ['#2f6b6b', '3', 'Pendulum', 'Measure gravity with a string and a weight']];
  labs.forEach(([col, n, t, s], i) => {
    const y = 270 + i * 118;
    ctx.fillStyle = col; ctx.beginPath(); ctx.arc(92, y - 14, 34, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center'; ctx.font = '700 40px ' + F.ui; ctx.fillText(n, 92, y);
    ctx.textAlign = 'left'; ctx.fillStyle = '#1b2a33'; ctx.font = '600 46px ' + F.ui; ctx.fillText(t, 150, y - 10);
    ctx.fillStyle = '#4b5b66'; ctx.font = '400 32px ' + F.ui; ctx.fillText(s, 150, y + 30);
  });
  ctx.strokeStyle = '#c4572f'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(1080, 470); for (let x = 0; x <= 320; x += 4){ const k = x / 320; ctx.lineTo(1080 + x, 470 - 300 / (1 + Math.exp(-(k - 0.5) * 11))); } ctx.stroke();
  ctx.strokeStyle = '#1b2a33'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(1070, 150); ctx.lineTo(1070, 480); ctx.lineTo(1420, 480); ctx.stroke();
  ctx.fillStyle = '#1b2a33'; ctx.font = '400 26px ' + F.type; ctx.fillText('% passing', 1080, 140); ctx.fillText('grain size →', 1240, 520);
  ctx.fillStyle = '#c4572f'; ctx.font = 'italic 400 34px ' + F.display; ctx.fillText('Goggles on before you start!', 1000, 600);
  return c;
}
function drawPeriodicTable(){
  const W = 1200, H = 760, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#0f1d26'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center'; ctx.font = '700 46px ' + F.ui; ctx.fillText('PERIODIC TABLE OF THE ELEMENTS', W / 2, 70);
  const S = [['H',1,1,0],['He',1,18,6],['Li',2,1,1],['Be',2,2,2],['B',2,13,5],['C',2,14,4],['N',2,15,4],['O',2,16,4],['F',2,17,7],['Ne',2,18,6],['Na',3,1,1],['Mg',3,2,2],['Al',3,13,3],['Si',3,14,5],['P',3,15,4],['S',3,16,4],['Cl',3,17,7],['Ar',3,18,6],
    ['K',4,1,1],['Ca',4,2,2],['Sc',4,3,8],['Ti',4,4,8],['V',4,5,8],['Cr',4,6,8],['Mn',4,7,8],['Fe',4,8,8],['Co',4,9,8],['Ni',4,10,8],['Cu',4,11,8],['Zn',4,12,8],['Ga',4,13,3],['Ge',4,14,5],['As',4,15,5],['Se',4,16,4],['Br',4,17,7],['Kr',4,18,6],
    ['Rb',5,1,1],['Sr',5,2,2],['Y',5,3,8],['Zr',5,4,8],['Nb',5,5,8],['Mo',5,6,8],['Tc',5,7,8],['Ru',5,8,8],['Rh',5,9,8],['Pd',5,10,8],['Ag',5,11,8],['Cd',5,12,8],['In',5,13,3],['Sn',5,14,3],['Sb',5,15,5],['Te',5,16,5],['I',5,17,7],['Xe',5,18,6],
    ['Cs',6,1,1],['Ba',6,2,2],['La',6,3,9],['Hf',6,4,8],['Ta',6,5,8],['W',6,6,8],['Re',6,7,8],['Os',6,8,8],['Ir',6,9,8],['Pt',6,10,8],['Au',6,11,8],['Hg',6,12,8],['Tl',6,13,3],['Pb',6,14,3],['Bi',6,15,3],['Po',6,16,3],['At',6,17,7],['Rn',6,18,6],
    ['Fr',7,1,1],['Ra',7,2,2],['Ac',7,3,9],['Rf',7,4,8],['Db',7,5,8],['Sg',7,6,8],['Bh',7,7,8],['Hs',7,8,8],['Mt',7,9,8],['Ds',7,10,8],['Rg',7,11,8],['Cn',7,12,8],['Nh',7,13,3],['Fl',7,14,3],['Mc',7,15,3],['Lv',7,16,3],['Ts',7,17,7],['Og',7,18,6]];
  const COL = ['#e8e8e8', '#f08a5d', '#f7c873', '#9ad3bc', '#8fc1e3', '#c3b1e1', '#f4a6c0', '#b8e994', '#d6c4a8', '#ffd3b6'];
  const cw = 60, ch = 72, x0 = (W - 18 * cw) / 2, y0 = 110;
  ctx.textBaseline = 'middle';
  for (const [sym, row, col, k] of S){
    const x = x0 + (col - 1) * cw, y = y0 + (row - 1) * ch;
    ctx.fillStyle = COL[k]; ctx.fillRect(x + 2, y + 2, cw - 4, ch - 4);
    ctx.fillStyle = '#10202a'; ctx.font = '700 26px ' + F.ui; ctx.fillText(sym, x + cw / 2, y + ch / 2 + 4);
  }
  ctx.fillStyle = 'rgba(255,255,255,0.7)'; ctx.font = '400 22px ' + F.type; ctx.textBaseline = 'alphabetic';
  ctx.fillText('Silicon (Si) + oxygen (O) = silica, SiO₂: the sand in the sieve test', W / 2, H - 70);
  ctx.fillText('Other lanthanides and actinides (Ce–Lu, Th–Lr) not shown', W / 2, H - 34);
  return c;
}
function drawSafetySign(top, lines, col){
  const W = 600, H = 420, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = col; ctx.fillRect(0, 0, W, 120);
  ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center'; fit(ctx, top, F.ui, '700', 64, W - 50); ctx.fillText(top, W / 2, 84);
  ctx.fillStyle = '#1b2a33'; ctx.font = '600 40px ' + F.ui; lines.forEach((l, i) => ctx.fillText(l, W / 2, 200 + i * 62));
  return c;
}
function drawPegboard(){
  const W = 1024, H = 320, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#c9a678'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = 'rgba(60,40,20,0.55)'; for (let y = 16; y < H; y += 26) for (let x = 16; x < W; x += 26){ ctx.beginPath(); ctx.arc(x, y, 3.4, 0, Math.PI * 2); ctx.fill(); }
  const tool = (fn) => { ctx.save(); fn(); ctx.restore(); };
  ctx.lineCap = 'round';
  tool(() => { ctx.translate(90, 40); ctx.fillStyle = '#c4572f'; ctx.fillRect(-18, 120, 36, 120); ctx.fillStyle = '#9aa3a8'; ctx.fillRect(-6, 0, 12, 130); ctx.fillRect(-40, 0, 80, 26); });
  tool(() => { ctx.translate(210, 50); ctx.fillStyle = '#2f5d7a'; ctx.fillRect(-14, 110, 28, 110); ctx.fillStyle = '#9aa3a8'; ctx.fillRect(-4, 0, 8, 120); });
  tool(() => { ctx.translate(320, 40); ctx.strokeStyle = '#9aa3a8'; ctx.lineWidth = 16; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, 200); ctx.stroke(); ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(0, 0, 26, 0, Math.PI * 2); ctx.stroke(); });
  tool(() => { ctx.translate(450, 60); ctx.fillStyle = '#f2c14e'; ctx.fillRect(-60, 0, 120, 70); ctx.fillStyle = '#222'; ctx.fillRect(-30, 70, 60, 120); ctx.fillStyle = '#555'; ctx.beginPath(); ctx.arc(0, 32, 18, 0, Math.PI * 2); ctx.fill(); });
  tool(() => { ctx.translate(600, 40); ctx.fillStyle = '#d9d9d9'; ctx.fillRect(-10, 0, 20, 230); ctx.fillStyle = '#1b2a33'; for (let i = 0; i < 22; i++) ctx.fillRect(-10, i * 10, i % 5 ? 8 : 14, 2); });
  tool(() => { ctx.translate(720, 50); ctx.strokeStyle = '#c4572f'; ctx.lineWidth = 12; ctx.beginPath(); ctx.arc(-18, 160, 26, 0, Math.PI * 2); ctx.stroke(); ctx.beginPath(); ctx.arc(18, 160, 26, 0, Math.PI * 2); ctx.stroke(); ctx.strokeStyle = '#9aa3a8'; ctx.lineWidth = 8; ctx.beginPath(); ctx.moveTo(-10, 140); ctx.lineTo(10, 0); ctx.moveTo(10, 140); ctx.lineTo(-10, 0); ctx.stroke(); });
  tool(() => { ctx.translate(850, 40); ctx.fillStyle = '#5aa08c'; ctx.fillRect(-40, 0, 80, 160); ctx.fillStyle = '#16232b'; ctx.fillRect(-28, 14, 56, 40); ctx.fillStyle = '#f2c14e'; ctx.font = '700 22px ' + F.type; ctx.textAlign = 'center'; ctx.fillText('8.8', 0, 44); ctx.fillStyle = '#c4572f'; ctx.fillRect(-30, 160, 8, 90); ctx.fillStyle = '#111'; ctx.fillRect(22, 160, 8, 90); });
  tool(() => { ctx.translate(960, 40); ctx.fillStyle = '#e07b2a'; ctx.fillRect(-26, 0, 52, 120); ctx.fillStyle = '#333'; ctx.fillRect(-10, 120, 20, 100); });
  return c;
}
function drawCuttingMat(){
  const W = 1024, H = 680, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#2f6b55'; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = 'rgba(255,255,255,0.18)'; ctx.lineWidth = 1;
  for (let x = 0; x <= W; x += 32){ ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
  for (let y = 0; y <= H; y += 32){ ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  ctx.strokeStyle = 'rgba(255,255,255,0.45)'; ctx.lineWidth = 2;
  for (let x = 0; x <= W; x += 160){ ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
  for (let y = 0; y <= H; y += 160){ ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  ctx.strokeStyle = 'rgba(242,193,78,0.6)'; ctx.beginPath(); ctx.moveTo(0, H); ctx.lineTo(H, 0); ctx.stroke();
  ctx.fillStyle = 'rgba(255,255,255,0.55)'; ctx.font = '700 22px ' + F.type; ctx.fillText('MODEL BENCH · ROOM 103', 24, H - 22);
  return c;
}
function drawScreenStats(){
  const W = 1280, H = 720, c = mk(W, H), ctx = c.getContext('2d');
  const g = ctx.createLinearGradient(0, 0, W, H); g.addColorStop(0, '#101826'); g.addColorStop(1, '#1b2b3f');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#5ee6c8'; ctx.font = '700 30px ' + F.type; ctx.fillText('THIS CAMPUS, BY THE NUMBERS', 70, 90);
  ctx.fillStyle = '#ffffff'; ctx.font = '400 64px ' + F.display; ctx.fillText('Built in a browser', 70, 175);
  const stats = [['1', 'web page holds the whole campus'], ['60', 'physics steps every second'], ['46,000', 'grass blades (at most) in one draw call'], ['4', 'virtual staff who answer questions'], ['0', 'game engines: just three.js + Rapier']];
  stats.forEach(([n, t], i) => {
    const y = 270 + i * 88;
    ctx.fillStyle = '#ffd166'; ctx.font = '700 58px ' + F.ui; ctx.textAlign = 'right'; ctx.fillText(n, 330, y);
    ctx.fillStyle = '#dfe8f0'; ctx.font = '400 36px ' + F.ui; ctx.textAlign = 'left'; ctx.fillText(t, 360, y);
  });
  ctx.strokeStyle = 'rgba(94,230,200,0.35)'; ctx.lineWidth = 3; ctx.strokeRect(30, 30, W - 60, H - 60);
  return c;
}

/* ---------- Shared builders ---------- */
function ceilPanel(x, z, w, d, mat){ addBox(w, 0.03, d, mat, x, H_SCHOOL - 0.02, z); }
function doorTrim(x, zw, mat){ for (const dx of [-0.95, 0.95]) addBox(0.1, 2.65, 0.24, mat, x + dx, 1.325, zw); addBox(2.0, 0.1, 0.24, mat, x, 2.65, zw); }
function stoolAt(B, x, z, h){ B.add(x, h, z, 0.36, 0.05, 0.36, 0); B.add(x, h / 2, z, 0.05, h, 0.05, 0); B.add(x, 0.02, z, 0.3, 0.04, 0.3, 0); }
function pickBox(w, h, d, x, y, z, ud, ry){ const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), PICK_PROXY); m.position.set(x, y, z); if (ry) m.rotation.y = ry; Object.assign(m.userData, ud); scene.add(m); pickItems.push(m); return m; }
function frostedWindow(axis, at, c, y0, y1, w, face, trim){
  /* A frosted pane set into a wall: daylight without showing the inside of the building shell */
  const pane = new THREE.MeshBasicMaterial({ map:tex(canvasFrosted(256, 256)), toneMapped:false });
  const m = addPlane(w, y1 - y0, pane, axis === 'x' ? at + face * -0.06 : c, (y0 + y1) / 2, axis === 'x' ? c : at + face * -0.06, axis === 'x' ? (face > 0 ? Math.PI / 2 : -Math.PI / 2) : (face > 0 ? 0 : Math.PI));
  m.userData.keepBasic = true;
  const T = 0.07;
  if (axis === 'x'){
    for (const dz of [-w / 2, w / 2]) addBox(0.1, y1 - y0 + T, T, trim, at, (y0 + y1) / 2, c + dz);
    for (const yy of [y0, y1]) addBox(0.1, T, w + T, trim, at, yy, c);
    addBox(0.05, y1 - y0, 0.04, trim, at - face * 0.02, (y0 + y1) / 2, c);
    addBox(0.22, 0.04, w + 0.14, trim, at + face * 0.08, y0 - 0.02, c);
  } else {
    for (const dx of [-w / 2, w / 2]) addBox(T, y1 - y0 + T, 0.1, trim, c + dx, (y0 + y1) / 2, at);
    for (const yy of [y0, y1]) addBox(w + T, T, 0.1, trim, c, yy, at);
  }
  return m;
}

/* ---------- Hallway: open doors, frames and signs ---------- */
function buildSchoolDoors(Z0, Z1){
  const frame = stdMat(0x4a3a2a, 0.5);
  const signCol = { 101:'#ff8f3d', 102:'#5ee6c8', 103:'#7aa8ff', 104:'#c38bff' };
  for (const num of ['101', '102', '103', '104']){
    const d = SCHOOL_DOORS[num], zw = d.side === 's' ? Z0 : Z1, s = d.side === 's' ? 1 : -1;
    doorTrim(d.x, zw, frame);
    addPlane(1.5, 0.643, basicMat(drawRoomSign(num, ROOM_NAMES[num], 'Open now · Come in', true)), d.x, 3.04, zw + s * 0.012, s > 0 ? 0 : Math.PI);
  }
  /* Blade signs stick out over the hall so every room can be found from the far end */
  for (const num of ['101', '102', '103', '104']){
    const d = SCHOOL_DOORS[num], zw = d.side === 's' ? Z0 : Z1, s = d.side === 's' ? 1 : -1, cv = drawBladeSign(num, ROOM_NAMES[num], signCol[num]);
    const g = new THREE.Group(); g.position.set(d.x + (num === '101' ? 1.2 : -1.25), 3.0, zw + s * 0.5); g.rotation.y = Math.PI / 2;
    addBox(0.82, 0.32, 0.03, stdMat(0x16232b, 0.5), 0, 0, 0, 0, g);
    addPlane(0.8, 0.293, basicMat(cv), 0, 0, 0.017, 0, g);
    addPlane(0.8, 0.293, basicMat(cv), 0, 0, -0.017, Math.PI, g);
    addBox(0.9, 0.03, 0.03, stdMat(0x9aa1a6, 0.4, 0.6), 0, 0.17, 0, 0, g);
    scene.add(g);
  }
}

/* ---------- Room 102: Science Lab ---------- */
function buildLabRoom(M){
  const { x0:X0, x1:X1, z0:Z0, z1:Z1 } = R102, H = H_SCHOOL;
  const wall = new THREE.MeshStandardMaterial({ map:repTex(canvasBandWall('#eef1ef', '#c8d4d8', '#2f8f9d', 1.0), 1, 1 / 3.6), roughness:0.9 });
  addFloor(X0, X1, Z0, Z1, new THREE.MeshStandardMaterial({ map:repTex(canvasLino('#e3e6e3', '#d2d9d7'), (X1 - X0) / 1.2, (Z1 - Z0) / 1.2), roughness:0.42 }));
  addCeil(X0, X1, Z0, Z1, H, new THREE.MeshStandardMaterial({ map:repTex(canvasTile(), (X1 - X0) / 0.6, (Z1 - Z0) / 0.6), roughness:0.95 }));
  addWall({ axis:'z', at:Z1 - 0.012, from:X0, to:X1, h:H, face:-1, mat:wall, doors:[{ a:28.1, b:29.9, h:2.6 }] });
  addWall({ axis:'z', at:Z0, from:X0, to:X1, h:H, face:1, mat:wall });
  addWall({ axis:'x', at:X0, from:Z0, to:Z1, h:H, face:1, mat:wall });
  addWall({ axis:'x', at:X1, from:Z0, to:Z1, h:H, face:-1, mat:wall, windows:[-11.4, -8.9, -6.4].map((c) => ({ a:c - 0.7, b:c + 0.7, y0:1.12, y1:2.62 })) });
  const trim = stdMat(0xe9e5dc, 0.6);
  for (const c of [-11.4, -8.9, -6.4]) frostedWindow('x', X1, c, 1.12, 2.62, 1.4, -1, trim);
  const glow = new THREE.MeshBasicMaterial({ color:0xf6fbff, toneMapped:false });
  for (const x of [28.2, 31.6]) for (const z of [-6.9, -10.8]) ceilPanel(x, z, 1.2, 0.6, glow);
  const pl = new THREE.PointLight(0xf2f7ff, 0.85, 18, 1.4); pl.position.set(29.8, 3.2, -8.9); scene.add(pl);
  addBox(X1 - X0, 0.1, 0.03, stdMat(0x5d6a70, 0.6), (X0 + X1) / 2, 0.05, Z0 + 0.015);

  const epoxy = stdMat(0x1d2124, 0.32, 0.05), cab = stdMat(0x9fb3bd, 0.55), cabDark = stdMat(0x6d808a, 0.6), steel = stdMat(0xb9c0c6, 0.3, 0.7);
  /* East bench: the sieve station */
  addBox(0.8, 0.86, 5.7, cab, X1 - 0.4, 0.43, -9.05);
  addBox(0.84, 0.04, 5.74, epoxy, X1 - 0.42, 0.88, -9.05);
  for (let z = -11.6; z <= -6.6; z += 0.95) addBox(0.02, 0.7, 0.86, cabDark, X1 - 0.81, 0.45, z);
  /* South bench: chemistry, with a fume hood and a sink */
  addBox(6.4, 0.86, 0.8, cab, 29.2, 0.43, Z0 + 0.4);
  addBox(6.44, 0.04, 0.84, epoxy, 29.2, 0.88, Z0 + 0.42);
  for (let x = 26.4; x <= 32.2; x += 0.95) addBox(0.86, 0.7, 0.02, cabDark, x, 0.45, Z0 + 0.81);
  const hoodW = stdMat(0xe3e7ea, 0.5), hood = new THREE.Group(); hood.position.set(26.95, 0.9, Z0 + 0.42);
  addBox(1.6, 0.12, 0.84, hoodW, 0, 1.38, 0, 0, hood);
  for (const s of [-1, 1]) addBox(0.08, 1.38, 0.84, hoodW, s * 0.76, 0.69, 0, 0, hood);
  addBox(1.6, 1.44, 0.03, stdMat(0x3a4248, 0.7), 0, 0.72, -0.4, 0, hood);
  addBox(1.44, 0.03, 0.3, glow, 0, 1.3, -0.1, 0, hood);
  const sash = new THREE.Mesh(new THREE.PlaneGeometry(1.44, 0.82), new THREE.MeshStandardMaterial({ color:0xcfe3ec, transparent:true, opacity:0.22, roughness:0.05, depthWrite:false })); sash.position.set(0, 0.95, 0.42); hood.add(sash);
  addBox(1.48, 0.05, 0.05, steel, 0, 0.54, 0.43, 0, hood);
  addPlane(0.9, 0.16, basicMat(drawTableCard('FUME HOOD', 'Sash down when not in use')), 0, 1.25, 0.425, 0, hood);
  scene.add(hood);
  addBox(0.62, 0.02, 0.46, stdMat(0x2c3236, 0.3, 0.6), 29.0, 0.905, Z0 + 0.42);
  addBox(0.54, 0.02, 0.38, stdMat(0x101315, 0.25, 0.4), 29.0, 0.91, Z0 + 0.42);
  const faucet = new THREE.Mesh(new THREE.TorusGeometry(0.11, 0.012, 8, 20, Math.PI), steel); faucet.position.set(29.0, 1.13, Z0 + 0.2); scene.add(faucet);
  addCyl(0.012, 0.012, 0.24, steel, 28.89, 1.02, Z0 + 0.2, 10);
  /* Shelf of reagent bottles over the chemistry bench */
  addBox(5.0, 0.03, 0.26, stdMat(0x8a6a48, 0.5), 30.2, 1.72, Z0 + 0.14);
  const bottles = new BoxBatch(), rb = rnd(77);
  for (let x = 27.9; x < 32.6; x += 0.17 + rb() * 0.06){ const h = 0.12 + rb() * 0.14; bottles.add(x, 1.735 + h / 2, Z0 + 0.13, 0.08, h, 0.08, 0, 0, ['#7a4a2a', '#2f4a63', '#e9e3d8', '#5a6e3a', '#b9c0c6'][(rb() * 5) | 0]); }
  bottles.build(stdMat(0xffffff, 0.3), true);
  /* Center island with stools */
  addBox(1.9, 0.86, 1.3, cab, 30.2, 0.43, -9.05);
  addBox(2.0, 0.04, 1.4, epoxy, 30.2, 0.88, -9.05);
  const stools = new BoxBatch();
  for (const [x, z] of [[29.65, -10.05], [30.75, -10.05], [29.65, -8.05], [30.75, -8.05]]) stoolAt(stools, x, z, 0.62);
  stools.build(stdMat(0x2d3438, 0.5, 0.3), false);
  /* Microscope and glassware on the island */
  const scope = new THREE.Group(); scope.position.set(29.65, 0.9, -9.05); scope.rotation.y = 0.6;
  addBox(0.18, 0.03, 0.24, stdMat(0x2b2f33, 0.4), 0, 0.015, 0, 0, scope);
  addBox(0.05, 0.22, 0.05, stdMat(0x2b2f33, 0.4), 0, 0.13, -0.08, 0, scope);
  const tube = addCyl(0.02, 0.022, 0.18, stdMat(0xe8e8e8, 0.3), 0, 0.27, -0.03, 14, scope); tube.rotation.x = -0.45;
  addBox(0.12, 0.012, 0.1, stdMat(0x2b2f33, 0.4), 0, 0.12, 0.02, 0, scope);
  scene.add(scope);
  const glass = new THREE.MeshStandardMaterial({ color:0xe8f4f8, transparent:true, opacity:0.3, roughness:0.05, metalness:0.1, depthWrite:false });
  for (const [x, z, r, h] of [[30.7, -8.7, 0.045, 0.12], [30.9, -9.3, 0.035, 0.09], [31.05, -8.9, 0.05, 0.16]]){ const b = addCyl(r, r, h, glass, x, 0.9 + h / 2, z, 18); b.userData.noAO = true; }
  OBST.push({ x:29.75, z:-9.05, r:0.95 }, { x:30.65, z:-9.05, r:0.95 });
  for (let z = -11.6; z <= -6.4; z += 1.0) OBST.push({ x:X1 - 0.4, z, r:0.55 });
  for (let x = 26.3; x <= 32.4; x += 1.0) OBST.push({ x, z:Z0 + 0.4, r:0.52 });
  /* Glassware cabinet, safety shower and eyewash, coats */
  addBox(0.5, 2.1, 1.4, stdMat(0xd5dde1, 0.5), X0 + 0.25, 1.05, -11.3);
  const cg = addPlane(1.3, 1.9, new THREE.MeshStandardMaterial({ color:0xd8ecf3, transparent:true, opacity:0.25, roughness:0.05, depthWrite:false }), X0 + 0.51, 1.05, -11.3, Math.PI / 2); cg.userData.noAO = true;
  const ware = new BoxBatch();
  for (const y of [0.45, 0.95, 1.45]) { ware.add(X0 + 0.27, y - 0.02, -11.3, 0.44, 0.02, 1.32, 0, 0, '#c9d1d5'); for (let k = 0; k < 6; k++) ware.add(X0 + 0.27, y + 0.07, -11.85 + k * 0.22, 0.09, 0.14, 0.09, 0, 0, '#e3eef2'); }
  ware.build(stdMat(0xffffff, 0.2, 0.05), true);
  OBST.push({ x:X0 + 0.4, z:-11.3, r:0.8 });
  const green = stdMat(0x1f8a4c, 0.5), yellow = stdMat(0xf2c14e, 0.5);
  addCyl(0.025, 0.025, 2.5, green, X0 + 0.32, 1.25, -5.55, 10);
  const head = addCyl(0.16, 0.05, 0.08, green, X0 + 0.32, 2.48, -5.55, 18);
  addBox(0.03, 0.4, 0.03, yellow, X0 + 0.5, 1.95, -5.55);
  addCyl(0.13, 0.08, 0.1, green, X0 + 0.3, 1.05, -5.55, 18);
  addPlane(0.5, 0.35, basicMat(drawSafetySign('SAFETY SHOWER', ['Eyewash below', 'Rinse 15 minutes'], '#1f8a4c')), X0 + 0.012, 1.7, -6.15, Math.PI / 2);
  OBST.push({ x:X0 + 0.35, z:-5.55, r:0.45 });
  addPlane(1.7, 1.077, basicMat(drawPeriodicTable(), 0xf2f2f2), X0 + 0.027, 1.75, -7.35, Math.PI / 2);
  addBox(0.03, 1.12, 1.74, stdMat(0x1b1b1f, 0.5), X0 + 0.005, 1.75, -7.35);
  for (const [x, col] of [[26.3, 0xf3f3f0], [26.75, 0xf3f3f0], [27.2, 0xdbe7f0]]) addBox(0.42, 0.9, 0.12, stdMat(col, 0.8), x, 1.55, Z1 - 0.12);
  addBox(1.3, 0.04, 0.06, steel, 26.75, 2.03, Z1 - 0.06);
  addCyl(0.08, 0.08, 0.5, stdMat(0xc4302b, 0.4), 27.62, 0.36, Z1 - 0.14, 16);
  addPlane(0.36, 0.24, basicMat(drawSafetySign('GOGGLES ON', ['In every lab', 'Every time'], '#c4572f')), 27.72, 1.8, Z1 - 0.014, Math.PI);
  /* Today's labs board */
  addBox(3.1, 1.36, 0.04, stdMat(0xb9c0c6, 0.4, 0.5), 31.6, 1.72, Z1 - 0.03);
  addPlane(3.0, 1.28, basicMat(drawLabBoard(), 0xf3f3f3), 31.6, 1.72, Z1 - 0.055, Math.PI);
  /* Stations: sieve shaker, titration and pendulum */
  buildSieveStation(M); buildTitrationStation(M); buildPendulumStation(M);
}

/* ---------- Room 103: Blueprint Lab ---------- */
function buildBlueprintRoom(M){
  const { x0:X0, x1:X1, z0:Z0, z1:Z1 } = R103, H = H_SCHOOL;
  const wall = new THREE.MeshStandardMaterial({ map:repTex(canvasBandWall('#e4eaef', '#24425e', '#f2c14e', 0.9), 1, 1 / 3.6), roughness:0.9 });
  addFloor(X0, X1, Z0, Z1, new THREE.MeshStandardMaterial({ map:repTex(canvasFloor([138, 104, 70], 23), (X1 - X0) / 1.2, (Z1 - Z0) / 2.4), roughness:0.55 }));
  addCeil(X0, X1, Z0, Z1, H, new THREE.MeshStandardMaterial({ map:repTex(canvasTile(), (X1 - X0) / 0.6, (Z1 - Z0) / 0.6), roughness:0.95 }));
  addWall({ axis:'z', at:Z0 + 0.012, from:X0, to:X1, h:H, face:1, mat:wall, doors:[{ a:18.1, b:19.9, h:2.6 }] });
  addWall({ axis:'z', at:Z1, from:X0, to:X1, h:H, face:-1, mat:wall });
  addWall({ axis:'x', at:X0, from:Z0, to:Z1, h:H, face:1, mat:wall });
  addWall({ axis:'x', at:X1 - 0.01, from:Z0, to:Z1, h:H, face:-1, mat:wall });
  /* Skylight under the roof glazing */
  const sky = new THREE.MeshBasicMaterial({ map:tex(canvasFrosted(512, 128, '#f7fbff')), toneMapped:false });
  const sl = new THREE.Mesh(new THREE.PlaneGeometry(6.0, 1.1), sky); sl.rotation.x = Math.PI / 2; sl.position.set(20.8, H - 0.015, 2.6); sl.userData.keepBasic = true; scene.add(sl);
  const wood = stdMat(0x5a3b22, 0.6);
  for (const s of [-1, 1]) addBox(6.1, 0.06, 0.06, wood, 20.8, H - 0.04, 2.6 + s * 0.58);
  const glow = new THREE.MeshBasicMaterial({ color:0xfffaf0, toneMapped:false });
  for (const [x, z] of [[14.6, 0.8], [14.6, 4.8], [18.1, 0.6], [18.1, 5.0]]) ceilPanel(x, z, 1.2, 0.5, glow);
  const pl = new THREE.PointLight(0xfff4e6, 0.85, 18, 1.4); pl.position.set(18.1, 3.2, 2.9); scene.add(pl);
  /* Pegboard of tools and a kit shelf on the south wall */
  addBox(3.6, 1.14, 0.03, stdMat(0x8a6a48, 0.6), 14.7, 1.85, Z0 + 0.03);
  addPlane(3.5, 1.09, basicMat(drawPegboard(), 0xeeeeee), 14.7, 1.85, Z0 + 0.05, 0);
  const shelf = new BoxBatch(), kits = new BoxBatch(), rk = rnd(5);
  for (const y of [0.4, 1.0, 1.6, 2.2]) shelf.add(22.0, y, Z0 + 0.24, 3.0, 0.03, 0.44, 0);
  for (const dx of [-1.5, 0, 1.5]) shelf.add(22.0 + dx, 1.3, Z0 + 0.24, 0.04, 1.9, 0.44, 0);
  for (const y of [0.4, 1.0, 1.6]) for (let x = 20.6; x < 23.4; x += 0.38 + rk() * 0.1){ const h = 0.18 + rk() * 0.2; kits.add(x, y + 0.015 + h / 2, Z0 + 0.25, 0.32, h, 0.34, 0, 0, ['#c4572f', '#2f5d7a', '#f2c14e', '#5aa08c', '#e9e3d8', '#7a2e4a'][(rk() * 6) | 0]); }
  shelf.build(wood, false); kits.build(stdMat(0xffffff, 0.75), true);
  OBST.push({ x:21.2, z:Z0 + 0.3, r:0.5 }, { x:22.8, z:Z0 + 0.3, r:0.5 });
  /* Drafting tables */
  const dwood = stdMat(0xc8a27a, 0.55), dsteel = stdMat(0x2f363c, 0.45, 0.4);
  for (const [x, z, ry] of [[13.5, 0.5, 0.5], [13.4, 5.4, 2.4]]){
    const g = new THREE.Group(); g.position.set(x, 0, z); g.rotation.y = ry;
    for (const s of [-1, 1]) addBox(0.05, 0.85, 0.05, dsteel, s * 0.5, 0.425, 0, 0, g);
    addBox(1.05, 0.05, 0.05, dsteel, 0, 0.15, 0, 0, g);
    const top = addBox(1.2, 0.03, 0.8, dwood, 0, 0.92, 0, 0, g); top.rotation.x = -0.3;
    const sheet = addPlane(0.62, 0.42, basicMat(drawMiniBlueprint(x > 13.45 ? 0 : 1)), 0, 0.94, 0.0, 0, g); sheet.rotation.x = -Math.PI / 2 - 0.3; sheet.position.y = 0.94;
    addCyl(0.012, 0.012, 0.6, dsteel, 0.52, 1.25, -0.3, 8, g);
    const lampHead = addCyl(0.03, 0.09, 0.1, stdMat(0x2f5d7a, 0.4), 0.38, 1.52, -0.2, 16, g); lampHead.rotation.z = 0.6;
    scene.add(g); OBST.push({ x, z, r:0.75 });
  }
  /* 3D printer on a cart */
  const pr = new THREE.Group(); pr.position.set(23.25, 0, 0.0);
  addBox(0.6, 0.75, 0.6, stdMat(0x2f363c, 0.5), 0, 0.375, 0, 0, pr);
  addBox(0.52, 0.6, 0.52, stdMat(0x1d2124, 0.4, 0.3), 0, 1.05, 0, 0, pr);
  const win = addPlane(0.4, 0.4, new THREE.MeshStandardMaterial({ color:0x9fc3d6, transparent:true, opacity:0.35, roughness:0.1, depthWrite:false }), -0.262, 1.07, 0, -Math.PI / 2, pr); win.userData.noAO = true;
  addBox(0.06, 0.06, 0.06, glowMatOf(0xff8f3d), -0.15, 0.9, 0.05, 0, pr);
  scene.add(pr); OBST.push({ x:23.25, z:0.0, r:0.55 });
  /* The five blueprints and the model bench */
  buildBlueprintBoards(M);
  buildModelBench(M);
}
function drawMiniBlueprint(k){
  const W = 512, H = 346, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#1f4f86'; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.lineWidth = 1; for (let x = 0; x < W; x += 16){ ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); } for (let y = 0; y < H; y += 16){ ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  ctx.strokeStyle = '#e8f4ff'; ctx.lineWidth = 3;
  if (k === 0){ ctx.strokeRect(120, 130, 270, 120); ctx.beginPath(); ctx.moveTo(110, 130); ctx.lineTo(255, 50); ctx.lineTo(400, 130); ctx.stroke(); ctx.strokeRect(160, 180, 50, 70); ctx.strokeRect(280, 160, 70, 50); }
  else { ctx.beginPath(); ctx.moveTo(60, 230); ctx.lineTo(450, 230); ctx.stroke(); for (let i = 0; i < 6; i++){ ctx.beginPath(); ctx.moveTo(60 + i * 65, 230); ctx.lineTo(92 + i * 65, 150); ctx.lineTo(125 + i * 65, 230); ctx.stroke(); } ctx.beginPath(); ctx.moveTo(92, 150); ctx.lineTo(417, 150); ctx.stroke(); }
  return c;
}

/* ---------- Room 104: World Builder Studio ---------- */
function buildWorldRoom(M){
  const { x0:X0, x1:X1, z0:Z0, z1:Z1 } = R104, H = H_SCHOOL;
  const wall = new THREE.MeshStandardMaterial({ map:repTex(canvasBandWall('#3a4654', '#26303b', '#5ee6c8', 0.9), 1, 1 / 3.6), roughness:0.9 });
  addFloor(X0, X1, Z0, Z1, new THREE.MeshStandardMaterial({ map:repTex(canvasCarpet(), (X1 - X0) / 2, (Z1 - Z0) / 2), roughness:1 }));
  addCeil(X0, X1, Z0, Z1, H, new THREE.MeshStandardMaterial({ map:repTex(canvasTile(), (X1 - X0) / 0.6, (Z1 - Z0) / 0.6), roughness:0.95, color:srgb(0x8a9098) }));
  addWall({ axis:'z', at:Z0 + 0.012, from:X0, to:X1, h:H, face:1, mat:wall, doors:[{ a:28.1, b:29.9, h:2.6 }] });
  addWall({ axis:'z', at:Z1, from:X0, to:X1, h:H, face:-1, mat:wall });
  addWall({ axis:'x', at:X0 + 0.01, from:Z0, to:Z1, h:H, face:1, mat:wall });
  addWall({ axis:'x', at:X1, from:Z0, to:Z1, h:H, face:-1, mat:wall, windows:[{ a:4.9, b:6.3, y0:1.12, y1:2.62 }] });
  frostedWindow('x', X1, 5.6, 1.12, 2.62, 1.4, -1, stdMat(0x2b333c, 0.6));
  /* LED strips along the top of the walls */
  const led = glowMatOf(0x5ee6c8), led2 = glowMatOf(0xc38bff);
  addBox(X1 - X0 - 0.2, 0.025, 0.025, led, (X0 + X1) / 2, H - 0.12, Z1 - 0.03);
  addBox(0.025, 0.025, Z1 - Z0 - 0.2, led2, X0 + 0.04, H - 0.12, (Z0 + Z1) / 2);
  addBox(0.025, 0.025, Z1 - Z0 - 0.2, led2, X1 - 0.03, H - 0.12, (Z0 + Z1) / 2);
  const glow = new THREE.MeshBasicMaterial({ color:0xf3f6ff, toneMapped:false });
  for (const [x, z] of [[26.4, 1.0], [31.6, 1.0], [26.4, 4.8], [31.6, 4.8]]) ceilPanel(x, z, 1.2, 0.5, glow);
  const pl = new THREE.PointLight(0xeef3ff, 0.8, 18, 1.4); pl.position.set(29.0, 3.2, 0.9); scene.add(pl);
  /* Desk with code monitors under the pipeline banner */
  const desk = stdMat(0x2b333c, 0.5), deskTop = stdMat(0xd9d4c8, 0.55);
  addBox(6.8, 0.04, 0.72, deskTop, 29.0, 0.75, Z1 - 0.42);
  for (const x of [25.7, 29.0, 32.3]) addBox(0.06, 0.73, 0.6, desk, x, 0.365, Z1 - 0.42);
  for (let x = 26.0; x <= 32.0; x += 1.4) OBST.push({ x, z:Z1 - 0.45, r:0.6 });
  const chairs = new BoxBatch();
  for (const x of [26.6, 29.0, 31.4]){ chairs.add(x, 0.48, Z1 - 1.25, 0.46, 0.06, 0.46, 0); chairs.add(x, 0.82, Z1 - 1.47, 0.46, 0.6, 0.05, 0); chairs.add(x, 0.24, Z1 - 1.25, 0.06, 0.46, 0.06, 0); }
  chairs.build(stdMat(0x1d2124, 0.6), false);
  /* Toolkit shelves on the west wall */
  const shelf = new BoxBatch();
  for (const y of [0.35, 0.95, 1.55, 2.15]) shelf.add(X0 + 0.24, y, 3.0, 0.44, 0.03, 4.6, 0);
  for (const dz of [-2.3, 0, 2.3]) shelf.add(X0 + 0.24, 1.25, 3.0 + dz, 0.44, 1.85, 0.04, 0);
  shelf.build(stdMat(0x1d2124, 0.5), false);
  for (let z = 1.0; z <= 5.2; z += 1.05) OBST.push({ x:X0 + 0.35, z, r:0.55 });
  /* Bean bags */
  const bag = (x, z, col) => { const m = new THREE.Mesh(new THREE.SphereGeometry(0.42, 24, 16), stdMat(col, 0.9)); m.scale.set(1, 0.6, 1); m.position.set(x, 0.24, z); scene.add(m); OBST.push({ x, z, r:0.5 }); };
  bag(33.2, -0.4, 0xc4572f); bag(32.3, -0.6, 0x2f5d7a);
  /* Stats screen on the east wall */
  addBox(0.06, 1.24, 2.16, stdMat(0x111418, 0.4), X1 - 0.04, 1.75, 2.1);
  addPlane(2.08, 1.17, basicMat(drawScreenStats()), X1 - 0.075, 1.75, 2.1, -Math.PI / 2).userData.keepBasic = true;
  buildWorldRoomContent(M);
}

/* ---------- Everything in the school wing beyond Room 101 ---------- */
function buildSchoolRooms(M){
  buildLabRoom(M); flushCanvases();
  buildBlueprintRoom(M); flushCanvases();
  buildWorldRoom(M);
}
