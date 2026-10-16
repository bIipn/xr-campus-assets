/* ================================================================
   Hidden XR tokens and badges
   ================================================================ */
const PROG_KEY = 'xr-campus-progress-v1';
const BADGES = [
  { id:'first-steps', name:'First Steps', how:'Walk around the campus' },
  { id:'explorer', name:'Museum Explorer', how:'Open 5 exhibits in the museum' },
  { id:'bookworm', name:'Bookworm', how:'Read 5 pages of library books' },
  { id:'curious', name:'Ask Away', how:'Ask any staff member a question' },
  { id:'artist', name:'3D Artist', how:'Make art in the air in Room 101' },
  { id:'scientist', name:'Lab Scientist', how:'Finish a lab test in Room 102' },
  { id:'engineer', name:'Engineer', how:'Explore 3 blueprints in Room 103' },
  { id:'maker', name:'Model Maker', how:'Build and test a model in Room 103' },
  { id:'worldbuilder', name:'World Builder', how:'Build a world on the layer table in Room 104' },
  { id:'coaster', name:'Coaster Rider', how:'Ride the Comet Coaster' },
  { id:'drop', name:'Sky Dropper', how:'Ride the Sky Drop' },
  { id:'diver', name:'Deep Diver', how:'Finish the Ocean Dive' },
  { id:'striker', name:'Striker', how:'Kick a ball into the yard’s soccer goal' },
  { id:'hunter', name:'Token Hunter', how:'Find every hidden XR token' },
  { id:'historian', name:'Living Historian', how:'Watch 6 scenes come to life in the Wax Hall' }
];
const BADGE = {}; BADGES.forEach((b) => BADGE[b.id] = b);
const TOKENS = [
  { id:'t-museum', place:'Museum', hint:'A far corner of Gallery 3', wing:'museum', at:[-5.35, 0.36, -41.35] },
  { id:'t-library', place:'Library', hint:'The sill of the big library window', wing:'lib', at:[-31.64, 1.2, -4.95] },
  { id:'t-school', place:'Workshop School', hint:'On top of the lockers by the back door', wing:'school', at:[33.0, 2.1, -4.52] },
  { id:'t-studio', place:'Room 101', hint:'The chalkboard ledge in the art studio', wing:'school', at:[21.6, 1.0, -12.86] },
  { id:'t-lab', place:'Room 102', hint:'On top of the glassware cabinet in the lab', wing:'school', at:[25.86, 2.32, -11.3] },
  { id:'t-blueprint', place:'Room 103', hint:'On top of the 3D printer', wing:'school', at:[23.25, 1.58, 0.0] },
  { id:'t-world', place:'Room 104', hint:'Up on the toolkit shelves', wing:'school', at:[24.26, 2.42, 5.2] },
  { id:'t-yard', place:'Recess Yard', hint:'Behind the Ocean Dive dome', wing:'play', at:[55.4, 0.4, 21.6] },
  { id:'t-coaster', place:'Comet Coaster', hint:'Ride through the loop', wing:'play', ride:'coaster' },
  { id:'t-drop', place:'Sky Drop', hint:'Ride the Sky Drop to the very top', wing:'play', ride:'drop' },
  { id:'t-dive', place:'Ocean Dive', hint:'Swim over the coral reef', wing:'dive', ride:'dive' }
];
const prog = { badges:new Set(), tokens:new Set(), exhibits:new Set(), pages:new Set(), bps:new Set(), wax:new Set(), walked:0, last:null };
const TOKEN_MESH = {};
function loadProg(){
  try { const d = JSON.parse(localStorage.getItem(PROG_KEY) || 'null'); if (d && typeof d === 'object') for (const k of ['badges', 'tokens', 'exhibits', 'pages', 'bps', 'wax']) if (Array.isArray(d[k])) d[k].forEach((x) => prog[k].add(String(x))); } catch (_) {}
}
function saveProg(){
  try { localStorage.setItem(PROG_KEY, JSON.stringify({ badges:[...prog.badges], tokens:[...prog.tokens], exhibits:[...prog.exhibits], pages:[...prog.pages], bps:[...prog.bps], wax:[...prog.wax] })); } catch (_) {}
}
function canvasGlow(){ const S = 128, c = mk(S, S), ctx = c.getContext('2d'), g = ctx.createRadialGradient(S / 2, S / 2, 0, S / 2, S / 2, S / 2); g.addColorStop(0, 'rgba(255,255,255,0.9)'); g.addColorStop(0.25, 'rgba(255,255,255,0.35)'); g.addColorStop(1, 'rgba(255,255,255,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, S, S); return c; }
function tokenPos(t){
  if (t.at) return new THREE.Vector3(t.at[0], t.at[1], t.at[2]);
  if (t.ride === 'coaster') return COASTER.tokenAt ? COASTER.tokenAt.clone() : null;
  if (t.ride === 'drop') return new THREE.Vector3(DROP.x - 2.75, DROP.top + 1.3, DROP.z);
  return DIVE.tokenAt ? DIVE.tokenAt.clone() : null;
}
function buildTokens(){
  loadProg();
  const gem = new THREE.OctahedronGeometry(0.13, 0), ring = new THREE.TorusGeometry(0.21, 0.014, 6, 36), proxyGeo = new THREE.SphereGeometry(0.4, 10, 8);
  const gemMat = new THREE.MeshStandardMaterial({ color:srgb(0x86f2ff), emissive:srgb(0x2fc9e6), emissiveIntensity:0.9, roughness:0.2, metalness:0.3, flatShading:true });
  const ringMat = glowMatOf(0xffd166), glowTex = tex(canvasGlow()), hidden = new THREE.MeshBasicMaterial({ visible:false });
  for (const t of TOKENS){
    const p = tokenPos(t); if (!p) continue;
    const g = new THREE.Group(); g.position.copy(p); g.userData.noMerge = true;
    const gm = new THREE.Mesh(gem, gemMat), rm = new THREE.Mesh(ring, ringMat); g.add(gm, rm);
    const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map:glowTex, color:0x9ff3ff, transparent:true, depthWrite:false, blending:THREE.AdditiveBlending, toneMapped:false })); sp.scale.set(0.95, 0.95, 1); g.add(sp);
    const px = new THREE.Mesh(proxyGeo, hidden); g.add(px);
    for (const m of [gm, px]){ m.userData.token = t.id; pickItems.push(m); }
    (WING[t.wing] || scene).add(g);
    g.visible = !prog.tokens.has(t.id);
    TOKEN_MESH[t.id] = { g, gm, rm, base:p.y, ph:Math.random() * 6, room:t.at ? roomAt(t.at[0], t.at[2]).id : null };
  }
}
function spinTokens(dt){
  if (REDUCED) return false;
  let any = false;
  const cp = camera.position, here = ride.on ? null : roomAt(cam.x, cam.z).id;
  for (const id in TOKEN_MESH){
    const T = TOKEN_MESH[id];
    if (!T.g.visible || !T.g.parent || !T.g.parent.visible) continue;
    const d2 = T.g.position.distanceToSquared(cp);
    /* Only spin tokens you could actually see: same room, or close by */
    if (d2 > 100 || (T.room && here && T.room !== here && d2 > 16)) continue;
    T.ph += dt; T.gm.rotation.y += dt * 1.8; T.rm.rotation.x = Math.PI / 2 + Math.sin(T.ph * 0.8) * 0.45; T.rm.rotation.y += dt * 0.9;
    T.g.position.y = T.base + Math.sin(T.ph * 1.6) * 0.05; any = true;
  }
  return any;
}
function collectToken(id){
  if (prog.tokens.has(id)) return false;
  prog.tokens.add(id); saveProg();
  const T = TOKEN_MESH[id]; if (T) T.g.visible = false;
  const n = prog.tokens.size, all = TOKENS.length;
  toast(n >= all ? 'You found all ' + all + ' XR tokens!' : 'XR token found! ' + n + ' of ' + all + '.');
  if (n >= all) award('hunter');
  updateBadgeBtn(); if (!bg.panel.hidden) renderBadges();
  wake();
  return true;
}

/* Badges */
const aw = { el:$('#award'), icon:$('#awIcon'), name:$('#awName'), q:[], busy:false };
const bg = { panel:$('#badges'), list:$('#bgList'), count:$('#bgCount'), tlist:$('#tkList'), tcount:$('#tkCount'), close:$('#bgClose'), reset:$('#bgReset'), btn:$('#bBadges'), bcount:$('#bCount') };
function award(id){
  if (!BADGE[id] || prog.badges.has(id)) return false;
  prog.badges.add(id); saveProg(); updateBadgeBtn(); if (!bg.panel.hidden) renderBadges();
  aw.q.push(BADGE[id]); if (!aw.busy) nextAward();
  return true;
}
function nextAward(){
  const b = aw.q.shift();
  if (!b){ aw.busy = false; return; }
  aw.busy = true; drawBadgeIcon(aw.icon, b.id, true); aw.name.textContent = b.name;
  aw.el.hidden = false; aw.el.classList.remove('show'); void aw.el.offsetWidth; aw.el.classList.add('show'); document.body.classList.add('awarding');
  setTimeout(() => { aw.el.hidden = true; document.body.classList.remove('awarding'); nextAward(); }, 3600);
}
function noteExhibit(it){ if (!it || !it.id) return; prog.exhibits.add(it.id); saveProg(); if (prog.exhibits.size >= 5) award('explorer'); }
function noteBlueprint(id){ if (!id) return; prog.bps.add(id); saveProg(); if (prog.bps.size >= 3) award('engineer'); }
function notePage(b, p){ if (!b || !p) return; prog.pages.add(b.id + ':' + p); saveProg(); if (prog.pages.size >= 5) award('bookworm'); }
function noteWalk(){
  if (ride.on || !entered){ prog.last = null; return; }
  if (prog.last) prog.walked += Math.hypot(cam.x - prog.last.x, cam.z - prog.last.z);
  prog.last = { x:cam.x, z:cam.z };
  if (prog.walked > 5) award('first-steps');
}
function drawBadgeIcon(c, id, on){
  const ctx = c.getContext('2d'), S = c.width;
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, S, S); ctx.scale(S / 88, S / 88);
  ctx.fillStyle = on ? '#1d3b52' : '#1f2a26'; ctx.beginPath(); ctx.arc(44, 44, 40, 0, Math.PI * 2); ctx.fill();
  ctx.lineWidth = 3.5; ctx.strokeStyle = on ? '#cda961' : 'rgba(205,169,97,0.35)'; ctx.stroke();
  const ink = on ? '#f2c14e' : 'rgba(239,231,213,0.32)';
  ctx.strokeStyle = ink; ctx.fillStyle = ink; ctx.lineWidth = 4; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  if (id === 'first-steps'){ ctx.beginPath(); ctx.ellipse(34, 50, 7, 11, -0.2, 0, Math.PI * 2); ctx.fill(); ctx.beginPath(); ctx.ellipse(54, 36, 7, 11, 0.2, 0, Math.PI * 2); ctx.fill(); for (const [x, y] of [[29, 34], [35, 33], [41, 35], [49, 20], [55, 19], [61, 21]]){ ctx.beginPath(); ctx.arc(x, y, 2.6, 0, Math.PI * 2); ctx.fill(); } }
  else if (id === 'explorer'){ ctx.strokeRect(24, 26, 40, 34); ctx.beginPath(); ctx.moveTo(28, 56); ctx.lineTo(40, 40); ctx.lineTo(48, 50); ctx.lineTo(53, 44); ctx.lineTo(60, 56); ctx.stroke(); ctx.beginPath(); ctx.arc(54, 34, 3.5, 0, Math.PI * 2); ctx.fill(); }
  else if (id === 'bookworm'){ ctx.beginPath(); ctx.moveTo(44, 30); ctx.quadraticCurveTo(34, 24, 22, 27); ctx.lineTo(22, 58); ctx.quadraticCurveTo(34, 55, 44, 61); ctx.quadraticCurveTo(54, 55, 66, 58); ctx.lineTo(66, 27); ctx.quadraticCurveTo(54, 24, 44, 30); ctx.lineTo(44, 61); ctx.stroke(); }
  else if (id === 'curious'){ ctx.beginPath(); ctx.moveTo(26, 28); ctx.lineTo(62, 28); ctx.quadraticCurveTo(66, 28, 66, 32); ctx.lineTo(66, 50); ctx.quadraticCurveTo(66, 54, 62, 54); ctx.lineTo(42, 54); ctx.lineTo(32, 63); ctx.lineTo(33, 54); ctx.lineTo(26, 54); ctx.quadraticCurveTo(22, 54, 22, 50); ctx.lineTo(22, 32); ctx.quadraticCurveTo(22, 28, 26, 28); ctx.stroke(); ctx.font = '700 20px ' + F.ui; ctx.textAlign = 'center'; ctx.fillText('?', 44, 48); }
  else if (id === 'artist'){ ctx.beginPath(); ctx.moveTo(22, 58); ctx.bezierCurveTo(30, 30, 46, 64, 52, 38); ctx.bezierCurveTo(56, 24, 66, 30, 64, 40); ctx.stroke(); ctx.beginPath(); ctx.arc(22, 58, 4, 0, Math.PI * 2); ctx.fill(); }
  else if (id === 'coaster'){ ctx.beginPath(); ctx.moveTo(18, 60); ctx.lineTo(34, 60); ctx.bezierCurveTo(42, 60, 40, 28, 50, 28); ctx.bezierCurveTo(62, 28, 62, 46, 52, 46); ctx.bezierCurveTo(44, 46, 46, 60, 58, 60); ctx.lineTo(70, 60); ctx.stroke(); }
  else if (id === 'drop'){ ctx.beginPath(); ctx.moveTo(44, 18); ctx.lineTo(44, 68); ctx.stroke(); ctx.strokeRect(34, 30, 20, 8); ctx.beginPath(); ctx.moveTo(60, 40); ctx.lineTo(60, 62); ctx.moveTo(54, 56); ctx.lineTo(60, 63); ctx.lineTo(66, 56); ctx.stroke(); }
  else if (id === 'diver'){ ctx.beginPath(); ctx.ellipse(42, 44, 16, 10, 0, 0, Math.PI * 2); ctx.fill(); ctx.beginPath(); ctx.moveTo(56, 44); ctx.lineTo(68, 34); ctx.lineTo(68, 54); ctx.closePath(); ctx.fill(); ctx.fillStyle = on ? '#1d3b52' : '#1f2a26'; ctx.beginPath(); ctx.arc(34, 41, 2.6, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = ink; for (const [x, y, r] of [[24, 30, 3], [20, 22, 2]]){ ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.stroke(); } }
  else if (id === 'striker'){ ctx.beginPath(); ctx.arc(44, 46, 18, 0, Math.PI * 2); ctx.stroke(); ctx.beginPath(); for (let i = 0; i < 5; i++){ const a = -Math.PI / 2 + i * Math.PI * 2 / 5; ctx.lineTo(44 + Math.cos(a) * 7, 46 + Math.sin(a) * 7); } ctx.closePath(); ctx.fill(); for (let i = 0; i < 5; i++){ const a = -Math.PI / 2 + i * Math.PI * 2 / 5; ctx.beginPath(); ctx.moveTo(44 + Math.cos(a) * 7, 46 + Math.sin(a) * 7); ctx.lineTo(44 + Math.cos(a) * 17, 46 + Math.sin(a) * 17); ctx.lineWidth = 2.5; ctx.stroke(); } ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(18, 22); ctx.lineTo(24, 26); ctx.moveTo(16, 32); ctx.lineTo(23, 33); ctx.stroke(); }
  else if (id === 'scientist'){ ctx.beginPath(); ctx.moveTo(37, 20); ctx.lineTo(37, 36); ctx.lineTo(24, 62); ctx.quadraticCurveTo(23, 66, 28, 66); ctx.lineTo(60, 66); ctx.quadraticCurveTo(65, 66, 64, 62); ctx.lineTo(51, 36); ctx.lineTo(51, 20); ctx.stroke(); ctx.beginPath(); ctx.moveTo(33, 20); ctx.lineTo(55, 20); ctx.stroke(); ctx.beginPath(); ctx.moveTo(29, 54); ctx.lineTo(59, 54); ctx.lineTo(63, 63); ctx.lineTo(25, 63); ctx.closePath(); ctx.fill(); }
  else if (id === 'engineer'){ ctx.strokeRect(20, 22, 48, 40); ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(28, 54); ctx.lineTo(28, 38); ctx.lineTo(44, 30); ctx.lineTo(60, 38); ctx.lineTo(60, 54); ctx.closePath(); ctx.stroke(); ctx.beginPath(); ctx.moveTo(38, 54); ctx.lineTo(38, 44); ctx.lineTo(48, 44); ctx.lineTo(48, 54); ctx.stroke(); ctx.beginPath(); ctx.arc(60, 26, 3, 0, Math.PI * 2); ctx.fill(); }
  else if (id === 'maker'){ ctx.fillRect(22, 40, 44, 12); ctx.beginPath(); ctx.moveTo(30, 40); ctx.lineTo(36, 30); ctx.lineTo(54, 30); ctx.lineTo(60, 40); ctx.closePath(); ctx.stroke(); for (const x of [32, 56]){ ctx.beginPath(); ctx.arc(x, 56, 7, 0, Math.PI * 2); ctx.stroke(); } }
  else if (id === 'worldbuilder'){ ctx.beginPath(); ctx.moveTo(44, 18); ctx.lineTo(68, 31); ctx.lineTo(44, 44); ctx.lineTo(20, 31); ctx.closePath(); ctx.stroke(); ctx.beginPath(); ctx.moveTo(20, 43); ctx.lineTo(44, 56); ctx.lineTo(68, 43); ctx.stroke(); ctx.beginPath(); ctx.moveTo(20, 55); ctx.lineTo(44, 68); ctx.lineTo(68, 55); ctx.stroke(); }
  else if (id === 'historian'){ ctx.beginPath(); ctx.arc(44, 29, 9, 0, Math.PI * 2); ctx.fill(); ctx.beginPath(); ctx.moveTo(27, 57); ctx.quadraticCurveTo(27, 41, 44, 41); ctx.quadraticCurveTo(61, 41, 61, 57); ctx.closePath(); ctx.fill(); ctx.fillRect(23, 60, 42, 6); }
  else if (id === 'hunter'){ ctx.beginPath(); ctx.moveTo(44, 20); ctx.lineTo(62, 40); ctx.lineTo(44, 66); ctx.lineTo(26, 40); ctx.closePath(); ctx.stroke(); ctx.beginPath(); ctx.moveTo(26, 40); ctx.lineTo(62, 40); ctx.moveTo(44, 20); ctx.lineTo(38, 40); ctx.lineTo(44, 66); ctx.lineTo(50, 40); ctx.lineTo(44, 20); ctx.lineWidth = 2.2; ctx.stroke(); }
}
function renderBadges(){
  bg.count.textContent = prog.badges.size + ' of ' + BADGES.length + ' unlocked';
  bg.list.textContent = '';
  for (const b of BADGES){
    const on = prog.badges.has(b.id), li = document.createElement('li'), c = mk(88, 88), tx = document.createElement('div'), nm = document.createElement('b'), hw = document.createElement('span');
    li.className = 'bgi' + (on ? ' on' : ''); c.className = 'bgic'; c.setAttribute('aria-hidden', 'true'); drawBadgeIcon(c, b.id, on);
    nm.textContent = b.name; hw.textContent = on ? 'Unlocked' : b.how; tx.append(nm, hw); li.append(c, tx); bg.list.appendChild(li);
  }
  bg.tcount.textContent = prog.tokens.size + ' of ' + TOKENS.length + ' found';
  bg.tlist.textContent = '';
  for (const t of TOKENS){
    const on = prog.tokens.has(t.id), li = document.createElement('li'), dot = document.createElement('span'), nm = document.createElement('b'), ht = document.createElement('span');
    li.className = on ? 'on' : ''; dot.className = 'tkdot'; dot.setAttribute('aria-hidden', 'true'); nm.textContent = t.place; ht.textContent = on ? 'Found' : 'Hint: ' + t.hint;
    li.append(dot, nm, ht); bg.tlist.appendChild(li);
  }
}
function openBadges(){ if (introOpen) closeIntro(); closeSearch(); closeStaff(); closeRideCard(); closeStation(); renderBadges(); bg.panel.hidden = false; bg.close.focus({ preventScroll:true }); hideHint(); }
function closeBadges(){ if (bg.panel.hidden) return; bg.panel.hidden = true; ui.scene.focus({ preventScroll:true }); }
function updateBadgeBtn(){ bg.bcount.textContent = prog.badges.size + '/' + BADGES.length; bg.btn.setAttribute('aria-label', 'Badges, ' + prog.badges.size + ' of ' + BADGES.length + ' unlocked'); }
bg.btn.addEventListener('click', () => bg.panel.hidden ? openBadges() : closeBadges());
bg.close.addEventListener('click', closeBadges);
let resetArmed = 0;
bg.reset.addEventListener('click', () => {
  if (Date.now() - resetArmed < 3000){ resetArmed = 0; bg.reset.textContent = 'Start over'; resetProgress(); return; }
  resetArmed = Date.now(); bg.reset.textContent = 'Tap again to start over';
  setTimeout(() => { if (resetArmed && Date.now() - resetArmed >= 3000){ resetArmed = 0; bg.reset.textContent = 'Start over'; } }, 3100);
});
function resetProgress(){
  for (const k of ['badges', 'tokens', 'exhibits', 'pages', 'bps', 'wax']) prog[k].clear();
  prog.walked = 0; prog.last = null; saveProg();
  for (const id in TOKEN_MESH) TOKEN_MESH[id].g.visible = true;
  updateBadgeBtn(); renderBadges(); toast('Progress cleared. Happy hunting!'); wake();
}
