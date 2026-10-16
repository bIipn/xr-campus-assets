/* ================================================================
   Campus art: book covers, signs, textures, front pages
   ================================================================ */
const GOLD = '#d9b56c';
function shade(hex, k){
  const n = parseInt(hex.slice(1), 16), r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
  const f = (v) => Math.round(clamp(k >= 0 ? v + (255 - v) * k : v * (1 + k), 0, 255));
  return 'rgb(' + f(r) + ',' + f(g) + ',' + f(b) + ')';
}
function bookColor(b){ return SUBJ[b.subject].color; }

/* Gold line icons for covers */
function drawIcon(ctx, kind, cx, cy, s, col){
  ctx.save(); ctx.translate(cx, cy); ctx.scale(s / 100, s / 100);
  ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = 5; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  const L = (pts) => { ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]); ctx.stroke(); };
  const C = (x, y, r, a0, a1) => { ctx.beginPath(); ctx.arc(x, y, r, a0 == null ? 0 : a0, a1 == null ? Math.PI * 2 : a1); ctx.stroke(); };
  switch (kind){
    case 'lens': C(-12, -12, 30); L([[10, 10], [42, 42]]); ctx.lineWidth = 9; L([[24, 24], [42, 42]]); break;
    case 'train':
      ctx.strokeRect(-46, -14, 56, 30); ctx.strokeRect(10, -36, 30, 52); L([[-36, -14], [-36, -34], [-26, -34], [-26, -14]]);
      C(-30, 26, 10); C(-2, 26, 10); C(26, 26, 12); L([[-60, 40], [60, 40]]); L([[-46, 16], [-58, 34]]); break;
    case 'capitol':
      L([[-48, -18], [0, -46], [48, -18], [-48, -18]]); L([[-48, 40], [48, 40]]); L([[-52, 48], [52, 48]]);
      for (const x of [-36, -12, 12, 36]) L([[x, -12], [x, 34]]); break;
    case 'scroll':
      ctx.strokeRect(-34, -40, 68, 80); C(-34, -40, 9, Math.PI * 0.5, Math.PI * 2); C(34, 40, 9, Math.PI * 1.5, Math.PI * 3);
      for (let i = 0; i < 4; i++) L([[-20, -20 + i * 14], [20 - (i % 2) * 10, -20 + i * 14]]); break;
    case 'coin':
      C(0, 0, 42); C(0, 0, 32); ctx.font = '700 46px ' + F.display; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('$', 0, 3); break;
    case 'case':
      ctx.strokeRect(-46, -20, 92, 58); L([[-16, -20], [-16, -34], [16, -34], [16, -20]]); L([[-46, 4], [46, 4]]); ctx.fillRect(-7, -2, 14, 12); break;
    case 'drop':
      ctx.beginPath(); ctx.moveTo(0, -46); ctx.bezierCurveTo(30, -10, 34, 6, 34, 16); ctx.arc(0, 16, 34, 0, Math.PI); ctx.bezierCurveTo(-34, 6, -30, -10, 0, -46); ctx.stroke();
      C(0, 16, 18, Math.PI * 0.15, Math.PI * 0.85); break;
    case 'hourglass':
      L([[-34, -46], [34, -46]]); L([[-34, 46], [34, 46]]); L([[-28, -46], [-28, -36], [0, 0], [-28, 36], [-28, 46]]); L([[28, -46], [28, -36], [0, 0], [28, 36], [28, 46]]);
      ctx.beginPath(); ctx.moveTo(-18, 40); ctx.lineTo(18, 40); ctx.lineTo(0, 20); ctx.closePath(); ctx.fill(); break;
    case 'code':
      L([[-20, -30], [-48, 0], [-20, 30]]); L([[20, -30], [48, 0], [20, 30]]); L([[10, -40], [-10, 40]]); break;
    case 'network':
      { const P = [[-36, -28], [30, -36], [0, 4], [-34, 36], [36, 30]];
        for (const [a, b] of [[0, 2], [1, 2], [2, 3], [2, 4], [0, 1], [3, 4]]) L([P[a], P[b]]);
        for (const p of P){ ctx.beginPath(); ctx.arc(p[0], p[1], 9, 0, Math.PI * 2); ctx.fill(); } } break;
    case 'moon':
      ctx.beginPath(); ctx.arc(-6, 4, 36, Math.PI * 0.35, Math.PI * 1.65); ctx.arc(10, -6, 30, Math.PI * 1.45, Math.PI * 0.55, true); ctx.closePath(); ctx.fill();
      for (const [x, y, r] of [[34, -30, 7], [40, 22, 5], [16, 40, 4]]){ ctx.beginPath(); for (let k = 0; k < 10; k++){ const a = k * Math.PI / 5 - Math.PI / 2, rr = k % 2 ? r * 0.45 : r; ctx.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); } ctx.closePath(); ctx.fill(); } break;
    case 'pine':
      L([[0, -48], [-30, -10], [-14, -10], [-40, 22], [40, 22], [14, -10], [30, -10], [0, -48]]); L([[0, 22], [0, 46]]); break;
    case 'mic':
      ctx.strokeRect(-14, -46, 28, 52); L([[-28, -8], [-28, 4]]); C(0, 4, 28, 0, Math.PI); L([[28, -8], [28, 4]]); L([[0, 32], [0, 46]]); L([[-18, 46], [18, 46]]); break;
    case 'quill':
      ctx.beginPath(); ctx.moveTo(-34, 44); ctx.quadraticCurveTo(-10, -10, 40, -46); ctx.quadraticCurveTo(10, 0, -34, 44); ctx.stroke(); L([[-34, 44], [-44, 52]]); L([[-6, 4], [16, -18]]); break;
  }
  ctx.restore();
}

function drawBookCover(b, W, H){
  W = W || 512; H = H || 700;
  const c = mk(W, H), ctx = c.getContext('2d'), r = rnd(b.id.length * 131 + b.title.length);
  const base = bookColor(b);
  const g = ctx.createLinearGradient(0, 0, W, H); g.addColorStop(0, shade(base, 0.12)); g.addColorStop(1, shade(base, -0.28));
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 2600; i++){ ctx.fillStyle = r() < 0.5 ? 'rgba(255,255,255,0.035)' : 'rgba(0,0,0,0.06)'; ctx.fillRect(r() * W, r() * H, 1 + r() * 2, 1 + r() * 2); }
  ctx.fillStyle = 'rgba(0,0,0,0.22)'; ctx.fillRect(0, 0, 22, H);
  ctx.strokeStyle = GOLD; ctx.lineWidth = 3; ctx.strokeRect(44, 36, W - 80, H - 72); ctx.lineWidth = 1.2; ctx.strokeRect(54, 46, W - 100, H - 92);
  ctx.fillStyle = GOLD; ctx.textAlign = 'center';
  ctx.font = '700 19px ' + F.type; ctx.fillText(SUBJ[b.subject].name.toUpperCase(), W / 2 + 11, 96);
  ctx.fillStyle = '#f3e7cc';
  let size = 58; ctx.font = '400 ' + size + 'px ' + F.display;
  let lines = wrap(ctx, b.title, W - 150);
  while (lines.length > 3 && size > 34){ size -= 4; ctx.font = '400 ' + size + 'px ' + F.display; lines = wrap(ctx, b.title, W - 150); }
  let y = 180;
  for (const l of lines){ ctx.fillText(l, W / 2 + 11, y); y += size * 1.08; }
  ctx.fillStyle = 'rgba(243,231,204,0.82)'; ctx.font = 'italic 400 25px ' + F.display;
  for (const l of wrap(ctx, b.sub, W - 170).slice(0, 2)){ ctx.fillText(l, W / 2 + 11, y + 14); y += 31; }
  drawIcon(ctx, b.icon, W / 2 + 11, H * 0.7, 150, GOLD);
  ctx.fillStyle = GOLD; ctx.font = '700 16px ' + F.type; ctx.fillText('PINE HOLLOW LIBRARY', W / 2 + 11, H - 70);
  return c;
}

/* Signs */
function signBase(W, H, bg){
  const c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = bg || '#101814'; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = 'rgba(205,169,97,0.85)'; ctx.lineWidth = 3; ctx.strokeRect(14, 14, W - 28, H - 28);
  return [c, ctx];
}
function drawWingSign(name, sub){
  const [c, ctx] = signBase(1300, 220);
  ctx.textAlign = 'center'; ctx.fillStyle = '#efe7d5'; fit(ctx, name, F.display, '400', 84, 1100); ctx.fillText(name, 650, 118);
  ctx.fillStyle = '#cda961'; ctx.font = '400 30px ' + F.type; ctx.fillText(sub.toUpperCase(), 650, 172);
  return c;
}
function drawSubjectSign(s){
  const [c, ctx] = signBase(560, 200, '#17110b');
  ctx.textAlign = 'center'; ctx.fillStyle = '#cda961'; ctx.font = '700 22px ' + F.type; ctx.fillText('SECTION', 280, 62);
  ctx.fillStyle = '#efe7d5'; fit(ctx, s.name, F.display, '400', 60, 480); ctx.fillText(s.name, 280, 138);
  return c;
}
function drawHangSign(){
  const [c, ctx] = signBase(1400, 380, '#13201b');
  ctx.textAlign = 'center';
  ctx.fillStyle = '#cda961'; ctx.font = '400 34px ' + F.type; ctx.fillText('PINE HOLLOW PUBLIC LIBRARY', 700, 96);
  ctx.fillStyle = '#efe7d5'; ctx.font = '400 150px ' + F.display; ctx.fillText('Reading Room', 700, 250);
  ctx.fillStyle = 'rgba(239,231,213,0.75)'; ctx.font = 'italic 400 38px ' + F.display; ctx.fillText('Open to everyone since 1958', 700, 318);
  return c;
}
function drawTableCard(top, bottom, bg, fg){
  const c = mk(900, 200), ctx = c.getContext('2d');
  ctx.fillStyle = bg || '#efe5cf'; ctx.fillRect(0, 0, 900, 200);
  ctx.strokeStyle = fg || '#3a2810'; ctx.lineWidth = 3; ctx.strokeRect(12, 12, 876, 176);
  ctx.fillStyle = fg || '#3a2810'; ctx.textAlign = 'center';
  ctx.font = '700 44px ' + F.type; ctx.fillText(top, 450, 92);
  ctx.font = 'italic 400 36px ' + F.display; ctx.fillText(bottom, 450, 150);
  return c;
}
function drawRoomSign(num, name, status, open){
  const c = mk(700, 300), ctx = c.getContext('2d');
  ctx.fillStyle = open ? '#1d3b52' : '#2d3a40'; ctx.fillRect(0, 0, 700, 300);
  ctx.fillStyle = '#ffffff'; ctx.textAlign = 'left'; ctx.font = '600 92px ' + F.ui; ctx.fillText(num, 40, 112);
  ctx.font = '600 44px ' + F.ui; fit(ctx, name, F.ui, '600', 46, 620); ctx.fillText(name, 40, 196);
  ctx.fillStyle = open ? '#f2c14e' : '#b9c4c8'; ctx.font = '700 30px ' + F.type; ctx.fillText(status.toUpperCase(), 40, 258);
  return c;
}
function drawStaffLabel(c, name, role){
  const ctx = c.getContext('2d'), W = c.width, H = c.height;
  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = 'rgba(21,34,30,0.94)'; rrect(ctx, 6, 6, W - 12, H - 40, 18); ctx.fill();
  ctx.strokeStyle = '#cda961'; ctx.lineWidth = 3; rrect(ctx, 6, 6, W - 12, H - 40, 18); ctx.stroke();
  ctx.fillStyle = 'rgba(21,34,30,0.94)'; ctx.beginPath(); ctx.moveTo(W/2 - 18, H - 36); ctx.lineTo(W/2, H - 8); ctx.lineTo(W/2 + 18, H - 36); ctx.closePath(); ctx.fill();
  ctx.textAlign = 'center'; ctx.fillStyle = '#efe7d5'; ctx.font = '400 62px ' + F.display; ctx.fillText(name, W/2, 80);
  ctx.fillStyle = '#cda961'; fit(ctx, role.toUpperCase() + ' · TAP TO ASK', F.type, '700', 27, W - 60); ctx.fillText(role.toUpperCase() + ' · TAP TO ASK', W/2, 126);
}
function drawPoster(kind){
  const W = 600, H = 820, c = mk(W, H), ctx = c.getContext('2d');
  if (kind === 'read'){
    ctx.fillStyle = '#e9dcbc'; ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = '#c4572f'; ctx.beginPath(); ctx.arc(W/2, 430, 210, Math.PI, 0); ctx.fill();
    ctx.strokeStyle = '#c4572f'; ctx.lineWidth = 10; for (let i = 0; i < 11; i++){ const a = Math.PI + i * Math.PI / 10; ctx.beginPath(); ctx.moveTo(W/2 + Math.cos(a) * 230, 430 + Math.sin(a) * 230); ctx.lineTo(W/2 + Math.cos(a) * 290, 430 + Math.sin(a) * 290); ctx.stroke(); }
    ctx.fillStyle = '#25384a'; ctx.beginPath(); ctx.moveTo(90, 520); ctx.quadraticCurveTo(200, 470, 300, 520); ctx.quadraticCurveTo(400, 470, 510, 520); ctx.lineTo(510, 600); ctx.quadraticCurveTo(400, 550, 300, 600); ctx.quadraticCurveTo(200, 550, 90, 600); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#25384a'; ctx.textAlign = 'center'; ctx.font = '700 150px ' + F.display; ctx.fillText('READ', W/2, 190);
    ctx.font = '700 30px ' + F.type; ctx.fillText('EVERY BOOK IS A DOOR', W/2, 690);
    ctx.font = 'italic 400 28px ' + F.display; ctx.fillText('Pine Hollow Public Library', W/2, 740);
  } else if (kind === 'card'){
    ctx.fillStyle = '#f1e8d2'; ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = '#b7473a'; ctx.lineWidth = 3; ctx.strokeRect(30, 30, W - 60, H - 60);
    ctx.fillStyle = '#2b2419'; ctx.textAlign = 'center'; ctx.font = '700 34px ' + F.type; ctx.fillText('LIBRARY CARD', W/2, 104);
    ctx.font = 'italic 400 26px ' + F.display; ctx.fillText('Pine Hollow Public Library', W/2, 146);
    ctx.strokeStyle = 'rgba(60,90,140,0.45)'; ctx.lineWidth = 1.5;
    for (let y = 200; y < H - 70; y += 44){ ctx.beginPath(); ctx.moveTo(56, y); ctx.lineTo(W - 56, y); ctx.stroke(); }
    ctx.beginPath(); ctx.moveTo(200, 170); ctx.lineTo(200, H - 70); ctx.stroke();
    const rows = [['SEP 12 1958','M. Ostrow'],['OCT 3 1958','R. Alder'],['NOV 19 1961','T. Reyes'],['MAR 2 1966','E. Marsh'],['JUN 30 1972','H. Fenn'],['AUG 14 1974','J. Dunning'],['JAN 9 1981','R. Alder'],['MAY 5 2004','T. Reyes'],['OCT 13 2026','You?']];
    ctx.fillStyle = '#2b2419'; ctx.font = '400 24px ' + F.type; ctx.textAlign = 'left';
    rows.forEach(([d, n], i) => { ctx.fillText(d, 62, 232 + i * 44); ctx.font = 'italic 400 30px ' + F.display; ctx.fillText(n, 216, 232 + i * 44); ctx.font = '400 24px ' + F.type; });
  } else if (kind === 'workshop'){
    ctx.fillStyle = '#f2c14e'; ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = '#1d3b52'; ctx.textAlign = 'center';
    ctx.font = '700 64px ' + F.ui; ['EVERY', 'CLASS IS A', 'WORKSHOP'].forEach((l, i) => ctx.fillText(l, W/2, 150 + i * 78));
    ctx.fillStyle = '#c4572f'; for (let i = 0; i < 5; i++){ ctx.beginPath(); ctx.arc(110 + i * 95, 470, 32, 0, Math.PI * 2); ctx.fill(); }
    ctx.fillStyle = '#1d3b52'; ctx.font = '600 30px ' + F.ui; ['Write it.', 'Draw it.', 'Build it.', 'Print it.'].forEach((l, i) => ctx.fillText(l, W/2, 590 + i * 46));
  } else {
    ctx.fillStyle = '#1d3b52'; ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = '#f2c14e'; ctx.beginPath(); ctx.moveTo(60, 120); ctx.lineTo(W - 60, 200); ctx.lineTo(60, 280); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#1d3b52'; ctx.font = '700 46px ' + F.ui; ctx.textAlign = 'left'; ctx.fillText('PINE HOLLOW', 84, 216);
    ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center'; ctx.font = '700 72px ' + F.display; ctx.fillText('Workshop', W/2, 450); ctx.fillText('School', W/2, 530);
    ctx.font = '400 30px ' + F.type; ctx.fillStyle = '#f2c14e'; ctx.fillText('HOME OF THE WOODPECKERS', W/2, 640);
  }
  return c;
}
function drawFlyer(i){
  const W = 360, H = 460, c = mk(W, H), ctx = c.getContext('2d');
  const set = [
    ['#fdf6e3', '#c4572f', 'SIGN UP', ['Map Makers', 'workshop opens', 'next month']],
    ['#e6f0f5', '#1d3b52', 'SCIENCE FAIR', ['Projects due', 'Friday', 'Room 104']],
    ['#fff1c9', '#6b4a12', 'LOST & FOUND', ['One mitten', 'Two pencils', 'A good idea']],
    ['#f3e3ea', '#7a2e4a', 'BAND', ['Practice moved', 'to the gym', 'Thursdays']]
  ][i % 4];
  ctx.fillStyle = set[0]; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = set[1]; ctx.fillRect(0, 0, W, 90);
  ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center'; ctx.font = '700 40px ' + F.ui; fit(ctx, set[2], F.ui, '700', 40, W - 40); ctx.fillText(set[2], W/2, 62);
  ctx.fillStyle = set[1]; ctx.font = '600 38px ' + F.ui; set[3].forEach((l, k) => ctx.fillText(l, W/2, 190 + k * 70));
  return c;
}

/* Surfaces */
function canvasWood(base, seed, n){
  const S = 1024, c = mk(S, S), ctx = c.getContext('2d'), r = rnd(seed || 41);
  n = n || 8; const pw = S / n;
  for (let i = 0; i < n; i++){
    let y = -r() * 300;
    while (y < S){
      const len = 220 + r() * 380, k = (r() - 0.5) * 0.18;
      ctx.fillStyle = shade(base, k); ctx.fillRect(i * pw, y, pw, len);
      ctx.strokeStyle = 'rgba(30,16,8,0.2)'; ctx.lineWidth = 1;
      for (let q = 0; q < 8; q++){ const x0 = i * pw + 6 + r() * (pw - 12); ctx.beginPath(); ctx.moveTo(x0, y); for (let t = 0; t <= len; t += 24) ctx.lineTo(x0 + Math.sin((t + q * 40) * 0.02) * 3, y + t); ctx.stroke(); }
      ctx.fillStyle = 'rgba(20,10,4,0.6)'; ctx.fillRect(i * pw, y, pw, 2);
      y += len;
    }
    ctx.fillStyle = 'rgba(20,10,4,0.65)'; ctx.fillRect(i * pw, 0, 2, S);
  }
  return c;
}
function canvasRunner(){
  const W = 256, H = 1024, c = mk(W, H), ctx = c.getContext('2d'), r = rnd(9);
  ctx.fillStyle = '#20392f'; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 6000; i++){ ctx.fillStyle = r() < 0.5 ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.08)'; ctx.fillRect(r() * W, r() * H, 2, 2); }
  ctx.fillStyle = '#8a6a32'; ctx.fillRect(14, 0, 8, H); ctx.fillRect(W - 22, 0, 8, H);
  ctx.fillStyle = '#5a1f1c'; ctx.fillRect(30, 0, 6, H); ctx.fillRect(W - 36, 0, 6, H);
  ctx.strokeStyle = 'rgba(138,106,50,0.55)'; ctx.lineWidth = 3;
  for (let y = 64; y < H; y += 128){ ctx.beginPath(); ctx.moveTo(W/2, y - 34); ctx.lineTo(W/2 + 34, y); ctx.lineTo(W/2, y + 34); ctx.lineTo(W/2 - 34, y); ctx.closePath(); ctx.stroke(); }
  return c;
}
function canvasCoffer(){
  const S = 512, c = mk(S, S), ctx = c.getContext('2d');
  ctx.fillStyle = '#3a342b'; ctx.fillRect(0, 0, S, S);
  const g = ctx.createLinearGradient(0, 0, S, S); g.addColorStop(0, '#4a4136'); g.addColorStop(1, '#2c2620');
  ctx.fillStyle = g; ctx.fillRect(40, 40, S - 80, S - 80);
  ctx.strokeStyle = 'rgba(205,169,97,0.35)'; ctx.lineWidth = 4; ctx.strokeRect(40, 40, S - 80, S - 80);
  ctx.strokeStyle = 'rgba(0,0,0,0.35)'; ctx.lineWidth = 10; ctx.strokeRect(20, 20, S - 40, S - 40);
  return c;
}
function canvasSky(h){
  const W = 512, H = h || 512, c = mk(W, H), ctx = c.getContext('2d'), r = rnd(23);
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#9cc3e4'); g.addColorStop(1, '#eef4f6');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 14; i++){ const x = r() * W, y = r() * H * 0.6, s = 30 + r() * 60; const cg = ctx.createRadialGradient(x, y, 0, x, y, s); cg.addColorStop(0, 'rgba(255,255,255,0.7)'); cg.addColorStop(1, 'rgba(255,255,255,0)'); ctx.fillStyle = cg; ctx.fillRect(x - s, y - s, s * 2, s * 2); }
  return c;
}
function drawWindowView(W, H, seed){
  const c = mk(W, H), ctx = c.getContext('2d'), r = rnd(seed || 5);
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#8fb8db'); g.addColorStop(0.62, '#dce9ee'); g.addColorStop(1, '#f2efe2');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 18; i++){ const x = r() * W, y = r() * H * 0.45, s = W * (0.04 + r() * 0.08); const cg = ctx.createRadialGradient(x, y, 0, x, y, s); cg.addColorStop(0, 'rgba(255,255,255,0.75)'); cg.addColorStop(1, 'rgba(255,255,255,0)'); ctx.fillStyle = cg; ctx.fillRect(x - s, y - s, s * 2, s * 2); }
  ctx.fillStyle = '#9fb1a6'; ctx.beginPath(); ctx.moveTo(0, H * 0.7); for (let x = 0; x <= W; x += W / 12) ctx.lineTo(x, H * (0.62 + r() * 0.06)); ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath(); ctx.fill();
  for (let i = 0; i < 46; i++){
    const x = r() * W, base = H * (0.76 + r() * 0.2), th = H * (0.08 + r() * 0.14), tw = th * 0.42;
    ctx.fillStyle = r() < 0.5 ? '#2f4a3b' : '#3b5a46';
    ctx.beginPath(); ctx.moveTo(x, base - th); ctx.lineTo(x + tw / 2, base); ctx.lineTo(x - tw / 2, base); ctx.closePath(); ctx.fill();
  }
  ctx.fillStyle = '#6f8a5a'; ctx.fillRect(0, H * 0.94, W, H * 0.06);
  return c;
}
function canvasPoolShape(){
  const W = 256, H = 256, c = mk(W, H), ctx = c.getContext('2d');
  const g = ctx.createLinearGradient(0, 0, W, 0); g.addColorStop(0, 'rgba(255,244,220,0.95)'); g.addColorStop(1, 'rgba(255,244,220,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  const v = ctx.createLinearGradient(0, 0, 0, H); v.addColorStop(0, 'rgba(0,0,0,1)'); v.addColorStop(0.18, 'rgba(0,0,0,0)'); v.addColorStop(0.82, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,1)');
  ctx.globalCompositeOperation = 'destination-out'; ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
  return c;
}
function canvasBookBands(){
  const W = 32, H = 128, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = 'rgba(255,236,190,1)'; ctx.fillRect(0, 12, W, 3); ctx.fillRect(0, 19, W, 2); ctx.fillRect(0, H - 22, W, 3);
  ctx.fillStyle = 'rgba(0,0,0,0.12)'; ctx.fillRect(0, 0, 3, H); ctx.fillRect(W - 3, 0, 3, H);
  return c;
}
function canvasLino(a, b){
  const S = 512, c = mk(S, S), ctx = c.getContext('2d'), r = rnd(31), n = 4, t = S / n;
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++){
    ctx.fillStyle = (i + j) % 2 ? a : b; ctx.fillRect(i * t, j * t, t, t);
    for (let k = 0; k < 160; k++){ ctx.fillStyle = r() < 0.5 ? 'rgba(0,0,0,0.07)' : 'rgba(255,255,255,0.12)'; ctx.fillRect(i * t + r() * t, j * t + r() * t, 2 + r() * 3, 2 + r() * 2); }
    ctx.strokeStyle = 'rgba(0,0,0,0.12)'; ctx.lineWidth = 2; ctx.strokeRect(i * t + 1, j * t + 1, t - 2, t - 2);
  }
  return c;
}
function canvasSchoolWall(){
  const W = 64, H = 512, c = mk(W, H), ctx = c.getContext('2d');
  const split = Math.round(H * (1 - 1.15 / 3.6));
  ctx.fillStyle = '#ece6d6'; ctx.fillRect(0, 0, W, split);
  ctx.fillStyle = '#2f6b6b'; ctx.fillRect(0, split, W, H - split);
  ctx.fillStyle = '#f2c14e'; ctx.fillRect(0, split - 6, W, 6);
  return c;
}
function canvasLocker(){
  const W = 128, H = 512, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#2f5d7a'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = 'rgba(0,0,0,0.35)'; ctx.fillRect(0, 0, 3, H); ctx.fillRect(W - 3, 0, 3, H);
  ctx.fillStyle = 'rgba(255,255,255,0.08)'; ctx.fillRect(8, 8, W - 16, H - 16);
  ctx.fillStyle = 'rgba(0,0,0,0.45)'; for (let i = 0; i < 6; i++) ctx.fillRect(30, 34 + i * 12, W - 60, 5);
  for (let i = 0; i < 6; i++) ctx.fillRect(30, H - 104 + i * 12, W - 60, 5);
  ctx.fillStyle = '#c9ced2'; ctx.fillRect(W - 34, H * 0.48, 10, 46);
  ctx.fillStyle = 'rgba(255,255,255,0.7)'; ctx.font = '700 20px ' + F.ui; ctx.textAlign = 'center'; ctx.fillText('', W/2, 26);
  return c;
}
function canvasCork(){
  const S = 512, c = mk(S, S), ctx = c.getContext('2d'), r = rnd(12);
  ctx.fillStyle = '#b8875a'; ctx.fillRect(0, 0, S, S);
  for (let i = 0; i < 9000; i++){ ctx.fillStyle = r() < 0.5 ? 'rgba(90,55,25,0.35)' : 'rgba(230,190,140,0.3)'; ctx.fillRect(r() * S, r() * S, 1 + r() * 3, 1 + r() * 3); }
  return c;
}
function canvasTile(){
  const S = 256, c = mk(S, S), ctx = c.getContext('2d'), r = rnd(3);
  ctx.fillStyle = '#e9e6de'; ctx.fillRect(0, 0, S, S);
  for (let i = 0; i < 1600; i++){ ctx.fillStyle = 'rgba(80,80,80,0.12)'; ctx.fillRect(r() * S, r() * S, 2, 2); }
  ctx.strokeStyle = 'rgba(120,120,120,0.5)'; ctx.lineWidth = 3; ctx.strokeRect(0, 0, S, S);
  return c;
}
function drawChalkboard(){
  const W = 1800, H = 640, c = mk(W, H), ctx = c.getContext('2d'), r = rnd(8);
  ctx.fillStyle = '#25372f'; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 30; i++){ ctx.fillStyle = 'rgba(255,255,255,0.025)'; ctx.beginPath(); ctx.ellipse(r() * W, r() * H, 80 + r() * 200, 20 + r() * 60, r() * 3, 0, Math.PI * 2); ctx.fill(); }
  ctx.fillStyle = 'rgba(245,242,230,0.92)'; ctx.textAlign = 'left';
  ctx.font = '400 40px ' + F.type; ctx.fillText('TODAY’S WORKSHOP', 90, 110);
  ctx.font = '400 104px ' + F.display; ctx.fillText('Make the Front Page', 90, 220);
  const steps = ['Pick your paper: 1897, 1945 or today', 'Write a headline and your story', 'Draw the picture (or add a photo)', 'Print it and pin it to the class wall'];
  ctx.font = '400 44px ' + F.ui; steps.forEach((s, i) => { ctx.fillText((i + 1) + '.  ' + s, 110, 320 + i * 72); });
  ctx.strokeStyle = 'rgba(245,242,230,0.85)'; ctx.lineWidth = 4;
  ctx.strokeRect(1340, 120, 330, 430); ctx.font = '400 30px ' + F.black; ctx.fillText('The Courier', 1380, 170);
  for (let i = 0; i < 3; i++){ ctx.beginPath(); ctx.moveTo(1370, 210 + i * 26); ctx.lineTo(1640, 210 + i * 26); ctx.stroke(); }
  ctx.strokeRect(1370, 300, 270, 150); ctx.beginPath(); ctx.moveTo(1380, 440); ctx.lineTo(1460, 360); ctx.lineTo(1520, 410); ctx.lineTo(1560, 380); ctx.lineTo(1630, 440); ctx.stroke();
  for (let i = 0; i < 3; i++){ ctx.beginPath(); ctx.moveTo(1370, 480 + i * 22); ctx.lineTo(1640, 480 + i * 22); ctx.stroke(); }
  ctx.font = 'italic 400 34px ' + F.display; ctx.fillText('— Mr. Hale', 1420, 610);
  return c;
}
function drawClock(){
  const S = 256, c = mk(S, S), ctx = c.getContext('2d');
  ctx.fillStyle = '#fbfaf4'; ctx.beginPath(); ctx.arc(S/2, S/2, S/2 - 4, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = '#222'; ctx.lineWidth = 8; ctx.stroke();
  ctx.fillStyle = '#222'; for (let i = 0; i < 12; i++){ const a = i * Math.PI / 6; ctx.fillRect(S/2 + Math.cos(a) * 100 - 3, S/2 + Math.sin(a) * 100 - 3, 6, 6); }
  ctx.lineCap = 'round'; ctx.lineWidth = 9; ctx.beginPath(); ctx.moveTo(S/2, S/2); ctx.lineTo(S/2 - 50, S/2 - 34); ctx.stroke();
  ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(S/2, S/2); ctx.lineTo(S/2 + 64, S/2 - 50); ctx.stroke();
  return c;
}
function drawMural(){
  const W = 1600, H = 1100, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#1d3b52'; ctx.fillRect(0, 0, W, H);
  const cols = ['#f2c14e', '#c4572f', '#5aa08c', '#e8e1cf', '#8fb8db'];
  for (let i = 0; i < 9; i++){ ctx.fillStyle = cols[i % cols.length]; ctx.beginPath(); ctx.arc(140 + i * 165, 940 + (i % 2) * 40, 90 + (i % 3) * 20, 0, Math.PI * 2); ctx.fill(); }
  ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center'; ctx.font = '700 150px ' + F.ui;
  ctx.fillText('EVERY CLASS', W/2, 300); ctx.fillText('IS A WORKSHOP', W/2, 470);
  ctx.fillStyle = '#f2c14e'; ctx.font = '600 52px ' + F.ui; ctx.fillText('Write it · Draw it · Build it · Record it · Print it', W/2, 600);
  return c;
}
function drawPressPlaque(){ return drawTableCard('1890s JOB PRESS', 'On loan from the Courier', '#e9dcbc', '#3a2810'); }

/* Doodles for the sample class-wall pages */
function doodle(kind, W, H){
  const c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, W, H);
  ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.lineWidth = 6; ctx.strokeStyle = '#1d1a16';
  const S = (x, y) => [x * W, y * H];
  const line = (pts, col, lw) => { ctx.strokeStyle = col || '#1d1a16'; ctx.lineWidth = lw || 6; ctx.beginPath(); ctx.moveTo(...S(pts[0][0], pts[0][1])); for (let i = 1; i < pts.length; i++) ctx.lineTo(...S(pts[i][0], pts[i][1])); ctx.stroke(); };
  const circ = (x, y, rr, col, fill) => { ctx.beginPath(); ctx.arc(x * W, y * H, rr * H, 0, Math.PI * 2); if (fill){ ctx.fillStyle = fill; ctx.fill(); } ctx.strokeStyle = col || '#1d1a16'; ctx.lineWidth = 6; ctx.stroke(); };
  if (kind === 'dog'){
    line([[0.05, 0.9], [0.95, 0.9]], '#6b8f3a', 8);
    circ(0.5, 0.58, 0.22, null, '#e1a95f'); circ(0.5, 0.34, 0.17, null, '#e1a95f');
    line([[0.37, 0.27], [0.32, 0.46]], '#7a4a1e', 14); line([[0.63, 0.27], [0.68, 0.46]], '#7a4a1e', 14);
    circ(0.45, 0.32, 0.02, null, '#1d1a16'); circ(0.55, 0.32, 0.02, null, '#1d1a16'); circ(0.5, 0.39, 0.03, null, '#1d1a16');
    line([[0.35, 0.5], [0.65, 0.68]], '#b5473a', 14);
    ctx.fillStyle = '#1d1a16'; ctx.fillRect(0.42 * W, 0.04 * H, 0.16 * W, 0.12 * H); ctx.fillRect(0.38 * W, 0.15 * H, 0.24 * W, 0.03 * H);
    line([[0.72, 0.62], [0.86, 0.5]], '#e1a95f', 10);
  } else if (kind === 'book'){
    ctx.fillStyle = '#6e2a22'; ctx.fillRect(0.2 * W, 0.3 * H, 0.42 * W, 0.5 * H); ctx.strokeRect(0.2 * W, 0.3 * H, 0.42 * W, 0.5 * H);
    line([[0.26, 0.42], [0.56, 0.42]], '#d9b56c', 5); line([[0.26, 0.5], [0.5, 0.5]], '#d9b56c', 5);
    circ(0.76, 0.36, 0.2, null, '#fbfaf4'); line([[0.76, 0.36], [0.76, 0.22]]); line([[0.76, 0.36], [0.84, 0.42]]);
    for (const x of [0.12, 0.3, 0.5]) line([[x, 0.12], [x + 0.06, 0.06]], '#c4572f', 4);
  } else if (kind === 'snow'){
    circ(0.8, 0.22, 0.13, null, '#f2c14e');
    for (const [x, y] of [[0.2, 0.25], [0.4, 0.45], [0.15, 0.65], [0.55, 0.2], [0.62, 0.62], [0.35, 0.78], [0.85, 0.7]]){ for (let k = 0; k < 3; k++){ const a = k * Math.PI / 3; line([[x - Math.cos(a) * 0.05, y - Math.sin(a) * 0.075], [x + Math.cos(a) * 0.05, y + Math.sin(a) * 0.075]], '#2a4a7a', 5); } }
    line([[0.02, 0.92], [0.98, 0.92]], '#5aa08c', 8);
  } else if (kind === 'robot'){
    ctx.fillStyle = '#c9ced2'; ctx.fillRect(0.36 * W, 0.12 * H, 0.22 * W, 0.24 * H); ctx.strokeRect(0.36 * W, 0.12 * H, 0.22 * W, 0.24 * H);
    ctx.fillRect(0.32 * W, 0.4 * H, 0.3 * W, 0.36 * H); ctx.strokeRect(0.32 * W, 0.4 * H, 0.3 * W, 0.36 * H);
    circ(0.43, 0.23, 0.03, null, '#2a4a7a'); circ(0.51, 0.23, 0.03, null, '#2a4a7a'); line([[0.47, 0.12], [0.47, 0.04]]); circ(0.47, 0.03, 0.02, null, '#c4572f');
    line([[0.62, 0.5], [0.76, 0.42]]); ctx.fillStyle = '#f2c14e'; ctx.beginPath(); ctx.moveTo(0.76 * W, 0.42 * H); ctx.lineTo(0.92 * W, 0.3 * H); ctx.lineTo(0.92 * W, 0.56 * H); ctx.closePath(); ctx.fill(); ctx.stroke();
    line([[0.38, 0.76], [0.38, 0.92]]); line([[0.56, 0.76], [0.56, 0.92]]);
    for (const [x, y] of [[0.14, 0.3], [0.2, 0.5], [0.1, 0.62]]){ line([[x, y], [x, y - 0.1]], '#1d1a16', 4); circ(x - 0.02, y, 0.03, null, '#1d1a16'); }
  } else {
    line([[0.02, 0.86], [0.98, 0.7]], '#6b8f3a', 8);
    circ(0.55, 0.55, 0.26, null, '#e07b2a'); line([[0.48, 0.32], [0.48, 0.78]], '#b85a1a', 4); line([[0.62, 0.32], [0.62, 0.78]], '#b85a1a', 4);
    line([[0.55, 0.29], [0.57, 0.18]], '#4a6b2a', 9);
    for (const y of [0.45, 0.55, 0.65]) line([[0.08, y], [0.22, y]], '#1d1a16', 4);
    ctx.fillStyle = '#fbfaf4'; ctx.fillRect(0.74 * W, 0.12 * H, 0.18 * W, 0.2 * H); ctx.strokeRect(0.74 * W, 0.12 * H, 0.18 * W, 0.2 * H);
  }
  return c;
}

/* Front page printer */
function eraDate(style){
  const now = new Date(), year = style === '1897' ? 1897 : style === '1945' ? 1945 : now.getFullYear();
  const d = new Date(year, now.getMonth(), now.getDate());
  let wd = '', md = '';
  try { wd = d.toLocaleDateString('en-US', { weekday:'long' }); md = d.toLocaleDateString('en-US', { month:'long', day:'numeric' }); } catch (_) { wd = ''; md = ''; }
  return { year, text:(wd ? wd + ', ' : '') + md + ', ' + year };
}
function coverDraw(ctx, src, x, y, w, h){
  const sw = src.width, sh = src.height, k = Math.max(w / sw, h / sh), dw = sw * k, dh = sh * k;
  ctx.save(); ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip();
  ctx.drawImage(src, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh);
  ctx.restore();
}
function printPic(src, w, h, mode){
  const c = mk(Math.round(w), Math.round(h)), x = c.getContext('2d');
  x.fillStyle = '#ffffff'; x.fillRect(0, 0, c.width, c.height);
  coverDraw(x, src, 0, 0, c.width, c.height);
  if (mode === 'color') return c;
  const img = x.getImageData(0, 0, c.width, c.height), d = img.data;
  if (mode === 'halftone'){
    const lum = new Float32Array(c.width * c.height);
    for (let i = 0, p = 0; i < d.length; i += 4, p++) lum[p] = (0.299 * d[i] + 0.587 * d[i+1] + 0.114 * d[i+2]) / 255;
    x.fillStyle = '#efe5cd'; x.fillRect(0, 0, c.width, c.height);
    x.fillStyle = 'rgba(28,22,15,0.92)';
    const cell = 5;
    for (let yy = 0; yy < c.height; yy += cell) for (let xx = (yy / cell) % 2 ? cell / 2 : 0; xx < c.width; xx += cell){
      const v = lum[Math.min(c.height - 1, yy | 0) * c.width + Math.min(c.width - 1, xx | 0)];
      const rr = cell * 0.62 * Math.sqrt(clamp(1 - v, 0, 1));
      if (rr > 0.25){ x.beginPath(); x.arc(xx, yy, rr, 0, Math.PI * 2); x.fill(); }
    }
    return c;
  }
  for (let i = 0; i < d.length; i += 4){
    const l = (0.299 * d[i] + 0.587 * d[i+1] + 0.114 * d[i+2]) / 255, v = Math.pow(l, 1.6);
    d[i] = 28 + (239 - 28) * v; d[i+1] = 22 + (229 - 22) * v; d[i+2] = 15 + (205 - 15) * v;
  }
  x.putImageData(img, 0, 0);
  return c;
}
function splitHead(ctx, text, family, weight, maxW, maxSize, minSize, maxLines){
  const words = text.trim().split(/\s+/).filter(Boolean);
  if (!words.length) return { lines:[''], size:maxSize };
  let best = null;
  for (let n = 1; n <= Math.min(maxLines, words.length); n++){
    const per = Math.ceil(words.length / n), lines = [];
    for (let i = 0; i < words.length; i += per) lines.push(words.slice(i, i + per).join(' '));
    let size = maxSize;
    for (const l of lines){ ctx.font = weight + ' ' + size + 'px ' + family; while (ctx.measureText(l).width > maxW && size > minSize){ size -= 2; ctx.font = weight + ' ' + size + 'px ' + family; } }
    const score = size * (n === 1 ? 1.08 : 1);
    if (!best || score > best.score) best = { lines, size, score };
  }
  return best;
}
function storyParas(story){
  const s = String(story || '').trim();
  if (!s) return ['Our reporter is still at the scene. Full story in the next edition.'];
  const parts = s.split(/\n\s*\n|\n/).map((p) => p.trim()).filter(Boolean);
  if (parts.length > 1) return parts;
  const sent = s.match(/[^.!?]+[.!?]+["”’)]*\s*|[^.!?]+$/g) || [s];
  const out = []; let cur = '';
  for (const t of sent){ cur += t; if (cur.length > 140){ out.push(cur.trim()); cur = ''; } }
  if (cur.trim()) out.push(cur.trim());
  return out;
}
function drawFrontPage(a, k){
  k = k || 1;
  if (a.style === 'today') return drawModernPage(a, k);
  const W = 900, H = 1188, c = mk(W * k, H * k), ctx = c.getContext('2d'), r = rnd(a.seed || 7);
  ctx.scale(k, k);
  const extra = a.style === '1945';
  paper(ctx, W, H, '#e7dcc1', r, { stains:5, edge:0.3 });
  const M = 34, INK = 'rgba(28,22,15,0.94)', date = eraDate(a.style);
  ctx.fillStyle = INK; ctx.textBaseline = 'alphabetic';
  ctx.font = '700 10.5px ' + F.display;
  ctx.textAlign = 'left'; ctx.fillText('ALL THE NEWS OF THE HOLLOW', M, M + 11);
  ctx.textAlign = 'right'; ctx.fillText(extra ? 'EXTRA EDITION' : 'PRICE FIVE CENTS', W - M, M + 11);
  ctx.textAlign = 'center';
  const mt = 'The Pine Hollow Courier', ms = fit(ctx, mt, F.black, '400', 78, W - 2*M - 170);
  ctx.fillText(mt, W/2, M + 8 + ms * 0.84);
  let y = M + 8 + ms + 8;
  hl(ctx, M, W - M, y, 2.6); hl(ctx, M, W - M, y + 5, 0.9); y += 12;
  ctx.font = '400 11.5px ' + F.display;
  ctx.textAlign = 'left'; ctx.fillText(extra ? 'VOL. LV — EXTRA' : 'VOL. VII — STUDENT EDITION', M, y + 12);
  ctx.textAlign = 'center'; ctx.fillText(('Pine Hollow, ' + date.text).toUpperCase(), W/2, y + 12);
  ctx.textAlign = 'right'; ctx.fillText('ROOM 101 PRESS', W - M, y + 12);
  y += 19; hl(ctx, M, W - M, y, 0.9); hl(ctx, M, W - M, y + 5, 2.6); y += 16;
  ctx.textAlign = 'center';
  if (extra){ ctx.font = '700 30px ' + F.display; ctx.fillText('★  EXTRA  ★', W/2, y + 26); y += 38; }
  const head = (a.head || 'Your Headline Here').toUpperCase();
  const sh = splitHead(ctx, head, F.display, '700', W - 2*M, extra ? 150 : 74, 30, 3);
  ctx.font = '700 ' + sh.size + 'px ' + F.display;
  for (const line of sh.lines){ ctx.fillText(line, W/2, y + sh.size * 0.8); y += sh.size * (extra ? 0.9 : 0.98); }
  y += 10;
  ctx.font = 'italic 400 19px ' + F.display;
  const deck = 'By ' + (a.byline || 'a Pine Hollow student') + ', Special Correspondent';
  for (const l of wrap(ctx, deck, W - 2*M - 140)){ ctx.fillText(l, W/2, y + 17); y += 23; }
  y += 5; hl(ctx, W/2 - 50, W/2 + 50, y, 0.9); y += 9;
  y += 2; hl(ctx, M, W - M, y, 1.4); y += 12;
  const cols = 5, gap = 14, colW = (W - 2*M - gap*(cols - 1)) / cols, top = y, bottom = H - M;
  for (let i = 1; i < cols; i++) vl(ctx, M + i*(colW + gap) - gap/2, top, bottom, 0.7);
  const artX = M + 2*(colW + gap), artW = 3*colW + 2*gap, artH = Math.round(artW * 0.64);
  if (a.pic){
    ctx.drawImage(printPic(a.pic, artW, artH, a.photo ? 'halftone' : 'ink'), artX, top, artW, artH);
    ctx.strokeStyle = INK; ctx.lineWidth = 1.4; ctx.strokeRect(artX + 0.5, top + 0.5, artW - 1, artH - 1);
  } else engraving(ctx, artX, top, artW, artH, 'library', r);
  ctx.fillStyle = INK; ctx.font = 'italic 400 12.5px ' + F.display; ctx.textAlign = 'center';
  ctx.fillText(a.pic ? 'Drawn for the Courier by ' + (a.byline || 'a Pine Hollow student') + '.' : 'The library on Second Street.', artX + artW/2, top + artH + 17);
  const flow = [{ h:'Our Correspondent Reports', big:true }];
  storyParas(a.story).forEach((p) => flow.push({ p }));
  const order = BRIEFS.map((b, i) => i).sort(() => r() - 0.5);
  for (let q = 0; q < order.length * 3; q++){ const b = BRIEFS[order[q % order.length]]; flow.push({ h:b[0] }, { p:b[1] }); }
  const colTop = (i) => i >= 2 ? top + artH + 32 : top;
  let col = 0, cy = colTop(0); const LH = 15.4;
  outer:
  for (const it of flow){
    if (it.h){
      ctx.font = '700 ' + (it.big ? 15 : 12.5) + 'px ' + F.display; ctx.textAlign = 'center';
      const lines = wrap(ctx, it.h.toUpperCase(), colW - 4);
      const need = lines.length * (it.big ? 18 : 15) + 22 + LH * 2;
      if (cy + need > bottom){ col++; if (col >= cols) break outer; cy = colTop(col); }
      if (cy > colTop(col) + 2) cy += 7;
      const cx = M + col*(colW + gap) + colW/2;
      for (const l of lines){ ctx.fillText(l, cx, cy + 12); cy += it.big ? 18 : 15; }
      cy += 3; hl(ctx, cx - 18, cx + 18, cy, 0.8); cy += 9;
    } else {
      ctx.font = '400 12.6px ' + F.display; ctx.textAlign = 'left';
      const lines = wrap(ctx, it.p, colW - 10);
      for (let li = 0; li < lines.length; li++){
        if (cy + LH > bottom){ col++; if (col >= cols) break outer; cy = colTop(col); }
        ctx.fillText(lines[li], M + col*(colW + gap) + (li === 0 ? 8 : 0), cy + 11.5);
        cy += LH;
      }
      cy += 2;
    }
  }
  const fy = H * 0.5, g = ctx.createLinearGradient(0, fy - 12, 0, fy + 12);
  g.addColorStop(0, 'rgba(80,60,30,0)'); g.addColorStop(0.5, 'rgba(80,60,30,0.14)'); g.addColorStop(1, 'rgba(255,250,240,0)');
  ctx.fillStyle = g; ctx.fillRect(0, fy - 12, W, 24);
  return c;
}
function drawModernPage(a, k){
  const W = 900, H = 1188, c = mk(W * k, H * k), ctx = c.getContext('2d');
  ctx.scale(k, k);
  ctx.fillStyle = '#f7f5ef'; ctx.fillRect(0, 0, W, H);
  const M = 44, INK = '#1b1c1e', date = eraDate('today');
  ctx.fillStyle = INK; ctx.textAlign = 'center';
  fit(ctx, 'The Pine Hollow Post', F.display, '700', 84, W - 2*M); ctx.fillText('The Pine Hollow Post', W/2, 118);
  ctx.fillStyle = '#b5473a'; ctx.fillRect(M, 140, W - 2*M, 4);
  ctx.fillStyle = INK; ctx.font = '600 13px ' + F.ui; ctx.textAlign = 'left'; ctx.fillText(date.text.toUpperCase(), M, 166);
  ctx.textAlign = 'right'; ctx.fillText('PINE HOLLOW, CALIFORNIA · STUDENT EDITION', W - M, 166);
  ctx.fillStyle = 'rgba(27,28,30,0.25)'; ctx.fillRect(M, 178, W - 2*M, 1);
  ctx.fillStyle = INK; ctx.textAlign = 'left';
  const sh = splitHead(ctx, a.head || 'Your Headline Here', F.display, '700', W - 2*M, 66, 30, 3);
  let y = 196;
  ctx.font = '700 ' + sh.size + 'px ' + F.display;
  for (const l of sh.lines){ ctx.fillText(l, M, y + sh.size * 0.82); y += sh.size * 1.04; }
  y += 8;
  ctx.font = '600 15px ' + F.ui; ctx.fillStyle = '#b5473a'; ctx.fillText(('By ' + (a.byline || 'a Pine Hollow student')).toUpperCase(), M, y + 14);
  ctx.fillStyle = '#6a6a6a'; ctx.font = '400 14px ' + F.ui; ctx.fillText('Student reporter, Room 101', M, y + 34); y += 52;
  const picH = 400;
  if (a.pic){ ctx.drawImage(printPic(a.pic, W - 2*M, picH, 'color'), M, y); }
  else { ctx.fillStyle = '#d9d4c8'; ctx.fillRect(M, y, W - 2*M, picH); }
  ctx.strokeStyle = 'rgba(0,0,0,0.15)'; ctx.lineWidth = 1; ctx.strokeRect(M + 0.5, y + 0.5, W - 2*M - 1, picH - 1);
  y += picH + 22;
  ctx.fillStyle = '#6a6a6a'; ctx.font = 'italic 400 14px ' + F.display; ctx.fillText(a.pic ? 'Illustration by ' + (a.byline || 'a Pine Hollow student') + ' for the Post.' : 'Photo coming soon.', M, y); y += 24;
  const side = 220, colGap = 26, colW = (W - 2*M - side - colGap * 2) / 2, top = y, bottom = H - 70;
  ctx.fillStyle = INK; ctx.font = '400 17px ' + F.display;
  const paras = storyParas(a.story);
  let col = 0, cy = top; const LH = 25;
  let first = true;
  outer2:
  for (const p of paras){
    const lines = wrap(ctx, p, colW);
    for (let li = 0; li < lines.length; li++){
      if (cy + LH > bottom){ col++; if (col >= 2) break outer2; cy = top; }
      const x = M + col * (colW + colGap);
      if (first && li === 0){ ctx.font = '700 17px ' + F.display; first = false; ctx.fillText(lines[li], x, cy + 18); ctx.font = '400 17px ' + F.display; }
      else ctx.fillText(lines[li], x, cy + 18);
      cy += LH;
    }
    cy += 10;
  }
  const sx = W - M - side;
  ctx.fillStyle = '#efe9da'; ctx.fillRect(sx, top - 6, side, bottom - top + 6);
  ctx.fillStyle = '#b5473a'; ctx.font = '700 13px ' + F.ui; ctx.fillText('INSIDE TODAY', sx + 16, top + 22);
  const inside = [['Library', '14 books open to read at the featured table'], ['Museum', 'The 1937 flood, told by Ruth Alder'], ['School', 'Map Makers workshop opens next'], ['Weather', 'Clear skies, 68° in the reading room']];
  let iy = top + 50;
  for (const [h, t] of inside){
    ctx.fillStyle = INK; ctx.font = '700 15px ' + F.ui; ctx.fillText(h, sx + 16, iy);
    ctx.font = '400 14px ' + F.ui; ctx.fillStyle = '#444';
    for (const l of wrap(ctx, t, side - 32)){ iy += 19; ctx.fillText(l, sx + 16, iy); }
    iy += 30;
  }
  ctx.fillStyle = 'rgba(27,28,30,0.25)'; ctx.fillRect(M, H - 52, W - 2*M, 1);
  ctx.fillStyle = '#6a6a6a'; ctx.font = '400 13px ' + F.ui; ctx.textAlign = 'center';
  ctx.fillText('Made at the Front Page Workshop · Room 101 · Pine Hollow Workshop School', W/2, H - 28);
  return c;
}
function drawEmptySlot(){
  const W = 900, H = 1188, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#f4efe2'; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = '#b5473a'; ctx.lineWidth = 8; ctx.setLineDash([28, 18]); ctx.strokeRect(40, 40, W - 80, H - 80); ctx.setLineDash([]);
  ctx.fillStyle = '#3a2810'; ctx.textAlign = 'center';
  ctx.font = '700 46px ' + F.type; ctx.fillText('YOUR FRONT PAGE', W/2, 470); ctx.fillText('GOES HERE', W/2, 530);
  ctx.font = 'italic 400 44px ' + F.display; ctx.fillText('Tap the worktable to start', W/2, 640);
  return c;
}
