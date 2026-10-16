/* ================================================================
   Art: exhibit posters, covers, signs and surfaces (all drawn in code)
   ================================================================ */
const GOLD = '#d9b56c', CREAM = '#efe7d5', BRASS = '#cda961';
function shade(hex, k){
  const n = parseInt(hex.slice(1), 16), r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
  const f = (v) => Math.round(clamp(k >= 0 ? v + (255 - v) * k : v * (1 + k), 0, 255));
  return 'rgb(' + f(r) + ',' + f(g) + ',' + f(b) + ')';
}
function noise(ctx, W, H, r, n, a){ for (let i = 0; i < n; i++){ ctx.fillStyle = r() < 0.5 ? 'rgba(255,255,255,' + a + ')' : 'rgba(0,0,0,' + (a * 1.6) + ')'; ctx.fillRect(r() * W, r() * H, 1 + r() * 2, 1 + r() * 2); } }
function posterBase(W, H, bg, seed){
  const c = mk(W, H), ctx = c.getContext('2d'), r = rnd(seed || 11);
  const g = ctx.createLinearGradient(0, 0, W, H); g.addColorStop(0, shade(bg, 0.1)); g.addColorStop(1, shade(bg, -0.3));
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  noise(ctx, W, H, r, Math.floor(W * H / 260), 0.025);
  ctx.strokeStyle = 'rgba(205,169,97,0.85)'; ctx.lineWidth = 3; ctx.strokeRect(26, 26, W - 52, H - 52);
  return [c, ctx, r];
}
function kicker(ctx, text, x, y, size, col){ ctx.fillStyle = col || BRASS; ctx.font = '400 ' + (size || 24) + 'px ' + F.type; ctx.textAlign = 'left'; ctx.fillText(text.toUpperCase(), x, y); }
function lines(ctx, text, x, y, maxW, lh, max){ const ls = wrap(ctx, text, maxW).slice(0, max || 99); ls.forEach((l, i) => ctx.fillText(l, x, y + i * lh)); return y + ls.length * lh; }
function headsetGlyph(ctx, x, y, w, col){
  const h = w * 0.58;
  ctx.fillStyle = col; rrect(ctx, x, y, w, h, h * 0.32); ctx.fill();
  ctx.fillStyle = 'rgba(0,0,0,0.45)'; ctx.beginPath(); ctx.arc(x + w * 0.3, y + h * 0.5, h * 0.2, 0, Math.PI * 2); ctx.arc(x + w * 0.7, y + h * 0.5, h * 0.2, 0, Math.PI * 2); ctx.fill();
}
const NEVADA = [[0,0],[1,0],[1,0.857],[0.975,0.875],[0.955,0.92],[0.93,0.96],[0.9,1.0],[0,0.43]];
function inPoly(px, py, P){ let ins = false; for (let i = 0, j = P.length - 1; i < P.length; j = i++){ const [xi, yi] = P[i], [xj, yj] = P[j]; if (((yi > py) !== (yj > py)) && (px < (xj - xi) * (py - yi) / (yj - yi) + xi)) ins = !ins; } return ins; }
function drawNevada(ctx, x, y, h, dots, r){
  const w = h * 0.67, P = NEVADA;
  ctx.beginPath(); P.forEach(([u, v], i) => (i ? ctx.lineTo : ctx.moveTo).call(ctx, x + u * w, y + v * h)); ctx.closePath();
  ctx.fillStyle = 'rgba(239,231,213,0.08)'; ctx.fill(); ctx.strokeStyle = BRASS; ctx.lineWidth = 3; ctx.stroke();
  let n = 0, guard = 0;
  while (n < dots && guard++ < 5000){
    const u = r(), v = r(); if (!inPoly(u, v, P) || !inPoly(u + 0.03, v + 0.03, P) || !inPoly(u - 0.03, v - 0.03, P)) continue;
    ctx.fillStyle = n % 7 === 0 ? CREAM : BRASS; ctx.beginPath(); ctx.arc(x + u * w, y + v * h, n % 7 === 0 ? 7 : 5, 0, Math.PI * 2); ctx.fill(); n++;
  }
}

/* Exhibit art */
function artBignum(a, W, H){
  const [c, ctx, r] = posterBase(W, H, a.bg, a.num.length * 7);
  kicker(ctx, a.kick, 70, 104, 24);
  ctx.fillStyle = CREAM; ctx.textAlign = 'left';
  const ns = fit(ctx, a.num, F.display, '400', 250, W * 0.5);
  ctx.fillText(a.num, 62, 140 + ns * 0.8);
  let y = 140 + ns * 0.8 + 70;
  ctx.font = '600 40px ' + F.ui; ctx.fillStyle = CREAM; y = lines(ctx, a.l1, 70, y, W * 0.48, 48, 2);
  ctx.font = '400 30px ' + F.ui; ctx.fillStyle = 'rgba(239,231,213,0.72)'; lines(ctx, a.l2, 70, y + 4, W * 0.48, 38, 2);
  const mx = W * 0.6, my = 90, mh = H - 180;
  if (a.motif === 'nevada') drawNevada(ctx, mx + 30, my, mh, a.dots, r);
  else {
    const cols = 10, rows = 20, gw = (W - mx - 80) / cols, gh = mh / rows;
    for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) headsetGlyph(ctx, mx + i * gw + gw * 0.12, my + j * gh + gh * 0.15, gw * 0.76, (i * 7 + j * 3) % 11 === 0 ? CREAM : 'rgba(205,169,97,0.78)');
  }
  return c;
}
function artQuote(a, it, W, H){
  const [c, ctx] = posterBase(W, H, a.bg, 21);
  for (let i = 0; i < 9; i++){ ctx.strokeStyle = 'rgba(205,169,97,' + (0.5 - i * 0.05) + ')'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(W * 0.86, H * 0.5, 60 + i * 46, Math.PI * 0.5, Math.PI * 1.5); ctx.stroke(); }
  kicker(ctx, 'MISSION · SINCE 2016', 70, 104, 24);
  ctx.fillStyle = BRASS; ctx.font = '400 180px ' + F.display; ctx.fillText('“', 56, 300);
  ctx.fillStyle = CREAM; ctx.font = '400 68px ' + F.display;
  const end = lines(ctx, it.quote, 80, 300, W * 0.62, 80, 4);
  ctx.fillStyle = 'rgba(239,231,213,0.75)'; ctx.font = 'italic 400 30px ' + F.display; ctx.fillText('— ' + it.quoteBy, 84, end + 40);
  return c;
}
function artProgram(W, H){
  const [c, ctx] = posterBase(W, H, '#25302a', 31);
  kicker(ctx, 'CONFERENCE TALKS', 80, 120, 28);
  ctx.fillStyle = CREAM; ctx.font = '400 84px ' + F.display; ctx.textAlign = 'left';
  ctx.fillText('Computers', 76, 230); ctx.fillText('in Libraries', 76, 316);
  const talks = [['2020', 'Integrating XR Tech & Programming in Libraries'], ['2022', 'Using XR to Discover “Lost Stories” & Pop-Up Books']];
  let y = 420;
  for (const [yr, t] of talks){
    ctx.fillStyle = 'rgba(239,231,213,0.08)'; ctx.fillRect(76, y, W - 152, 250);
    ctx.strokeStyle = 'rgba(205,169,97,0.6)'; ctx.lineWidth = 2; ctx.strokeRect(76, y, W - 152, 250);
    ctx.fillStyle = BRASS; ctx.font = '700 34px ' + F.type; ctx.fillText(yr, 110, y + 64);
    ctx.fillStyle = CREAM; ctx.font = '400 44px ' + F.display; lines(ctx, t, 110, y + 130, W - 240, 54, 3);
    y += 300;
  }
  ctx.fillStyle = 'rgba(239,231,213,0.6)'; ctx.font = '400 26px ' + F.ui; ctx.fillText('Session titles from the conference speaker page', 80, H - 70);
  return c;
}
function sectorIcon(ctx, k, x, y, s){
  ctx.save(); ctx.translate(x, y); ctx.scale(s / 100, s / 100); ctx.strokeStyle = CREAM; ctx.fillStyle = CREAM; ctx.lineWidth = 7; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  if (k === 0){ ctx.beginPath(); ctx.moveTo(-30, 30); ctx.lineTo(14, -14); ctx.stroke(); ctx.beginPath(); ctx.arc(22, -22, 16, Math.PI * 0.2, Math.PI * 1.75); ctx.stroke(); }
  else if (k === 1){ ctx.beginPath(); ctx.moveTo(0, 30); ctx.bezierCurveTo(-46, 0, -30, -36, 0, -14); ctx.bezierCurveTo(30, -36, 46, 0, 0, 30); ctx.stroke(); ctx.beginPath(); ctx.moveTo(-22, 0); ctx.lineTo(-8, 0); ctx.lineTo(-2, -10); ctx.lineTo(6, 10); ctx.lineTo(12, 0); ctx.lineTo(22, 0); ctx.stroke(); }
  else if (k === 2){ ctx.strokeRect(-34, -28, 68, 44); ctx.beginPath(); ctx.moveTo(-14, 30); ctx.lineTo(14, 30); ctx.moveTo(0, 16); ctx.lineTo(0, 30); ctx.stroke(); }
  else if (k === 3){ ctx.beginPath(); for (let i = 0; i < 16; i++){ const a = i * Math.PI / 8, rr = i % 2 ? 26 : 36; ctx.lineTo(Math.cos(a) * rr, Math.sin(a) * rr); } ctx.closePath(); ctx.stroke(); ctx.beginPath(); ctx.arc(0, 0, 10, 0, Math.PI * 2); ctx.stroke(); }
  else { ctx.strokeRect(-40, -18, 46, 34); ctx.beginPath(); ctx.moveTo(6, -6); ctx.lineTo(26, -6); ctx.lineTo(38, 8); ctx.lineTo(38, 16); ctx.lineTo(6, 16); ctx.stroke(); ctx.beginPath(); ctx.arc(-24, 22, 8, 0, Math.PI * 2); ctx.arc(26, 22, 8, 0, Math.PI * 2); ctx.fill(); }
  ctx.restore();
}
function artSectors(W, H){
  const [c, ctx] = posterBase(W, H, '#22304f', 41);
  kicker(ctx, 'NEVADA · BEGAN IN 2020', 70, 104, 24);
  ctx.fillStyle = CREAM; ctx.font = '400 96px ' + F.display; ctx.textAlign = 'left'; ctx.fillText('Project SANDI', 64, 200);
  ctx.fillStyle = 'rgba(239,231,213,0.75)'; ctx.font = 'italic 400 30px ' + F.display; ctx.fillText('Supporting and Advancing Nevada’s Dislocated Individuals', 70, 250);
  const names = ['Skilled trades', 'Healthcare', 'IT', 'Manufacturing', 'Logistics'];
  const gx = (W - 140) / 5;
  names.forEach((n, i) => {
    const cx = 70 + gx * i + gx / 2, cy = 400;
    ctx.fillStyle = 'rgba(205,169,97,0.22)'; ctx.beginPath(); ctx.arc(cx, cy, 70, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = BRASS; ctx.lineWidth = 3; ctx.stroke();
    sectorIcon(ctx, i, cx, cy, 100);
    ctx.fillStyle = CREAM; ctx.font = '600 26px ' + F.ui; ctx.textAlign = 'center'; ctx.fillText(n, cx, cy + 112);
  });
  ctx.textAlign = 'left'; ctx.fillStyle = BRASS; ctx.font = '400 30px ' + F.type; ctx.fillText('$13.8M FEDERAL GRANT · 1,000+ HEADSETS · 80+ LOCATIONS', 70, H - 70);
  return c;
}
function artStory(W, H){
  const c = mk(W, H), ctx = c.getContext('2d'), r = rnd(51);
  const g = ctx.createLinearGradient(0, 0, 0, H * 0.7); g.addColorStop(0, '#1c2140'); g.addColorStop(0.6, '#6b3f5e'); g.addColorStop(1, '#e8925a');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 70; i++){ ctx.fillStyle = 'rgba(255,255,255,' + (0.3 + r() * 0.6) + ')'; ctx.fillRect(r() * W, r() * H * 0.4, 2, 2); }
  ctx.fillStyle = '#3a2a2f'; ctx.beginPath(); ctx.moveTo(0, H * 0.7); for (let x = 0; x <= W; x += 60) ctx.lineTo(x, H * (0.62 + Math.sin(x * 0.01) * 0.03)); ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#241a1e'; ctx.fillRect(0, H * 0.74, W, H * 0.26);
  const houses = [[90, 1.0], [210, 1.25], [330, 0.9], [610, 1.1], [730, 0.95]];
  for (const [x, s] of houses){ const w = 90 * s, h = 60 * s, y = H * 0.74 - h; ctx.fillStyle = '#2e2226'; ctx.fillRect(x, y, w, h); ctx.beginPath(); ctx.moveTo(x - 8, y); ctx.lineTo(x + w / 2, y - 40 * s); ctx.lineTo(x + w + 8, y); ctx.closePath(); ctx.fill(); ctx.fillStyle = x === 330 ? '#ffd27a' : 'rgba(255,210,122,0.25)'; ctx.fillRect(x + w * 0.36, y + h * 0.3, w * 0.28, h * 0.3); }
  ctx.fillStyle = '#2e2226'; ctx.fillRect(470, H * 0.74 - 180, 10, 180); ctx.fillRect(520, H * 0.74 - 180, 10, 180); ctx.fillRect(450, H * 0.74 - 240, 100, 70);
  const glow = ctx.createRadialGradient(W * 0.5, H * 0.26, 10, W * 0.5, H * 0.26, 220); glow.addColorStop(0, 'rgba(255,214,140,0.55)'); glow.addColorStop(1, 'rgba(255,214,140,0)'); ctx.fillStyle = glow; ctx.fillRect(0, 0, W, H);
  headsetGlyph(ctx, W * 0.5 - 110, H * 0.17, 220, '#f3d9a4');
  ctx.fillStyle = CREAM; ctx.textAlign = 'center'; ctx.font = '400 66px ' + F.display; ctx.fillText('A town of 300', W / 2, H * 0.86);
  ctx.fillStyle = BRASS; ctx.font = '400 24px ' + F.type; ctx.fillText('A 12-WEEK DIALYSIS CERTIFICATION, IN VR', W / 2, H * 0.92);
  return c;
}
function artEpisodes(W, H){
  const [c, ctx] = posterBase(W, H, '#2a2440', 61);
  kicker(ctx, 'VIDEO SERIES · WITH GEORGE AND CAMILA', 70, 100, 22);
  ctx.fillStyle = CREAM; ctx.font = '400 74px ' + F.display; ctx.textAlign = 'left'; ctx.fillText('XR Showcase', 66, 180);
  const eps = ['Ecosphere', 'LP Bookspace', 'Tilt Brush', 'Moss & Uptale', 'Apollo 11 VR', 'Wander', 'Fujii', 'Gadgeteer', 'Yorescape'];
  const cols = ['#1d6b6b', '#7a3b6e', '#b5473a', '#2f5d7a', '#3b3550', '#5a7a2e', '#6e2a22', '#a07a2a', '#24324f'];
  const gx = 70, gy = 220, gw = (W - 140 - 40) / 3, gh = (H - gy - 70 - 40) / 3;
  eps.forEach((e, i) => {
    const x = gx + (i % 3) * (gw + 20), y = gy + Math.floor(i / 3) * (gh + 20);
    const g = ctx.createLinearGradient(x, y, x + gw, y + gh); g.addColorStop(0, shade(cols[i], 0.2)); g.addColorStop(1, shade(cols[i], -0.35));
    ctx.fillStyle = g; ctx.fillRect(x, y, gw, gh);
    ctx.fillStyle = 'rgba(255,255,255,0.9)'; ctx.beginPath(); ctx.moveTo(x + gw / 2 - 16, y + gh * 0.32 - 20); ctx.lineTo(x + gw / 2 + 22, y + gh * 0.32); ctx.lineTo(x + gw / 2 - 16, y + gh * 0.32 + 20); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center'; fit(ctx, e, F.ui, '600', 28, gw - 20); ctx.fillText(e, x + gw / 2, y + gh * 0.78);
    ctx.fillStyle = 'rgba(255,255,255,0.6)'; ctx.font = '400 16px ' + F.type; ctx.fillText('EPISODE ' + (i + 1), x + gw / 2, y + gh * 0.6);
  });
  return c;
}
function artShipyard(W, H){
  const c = mk(W, H), ctx = c.getContext('2d'), r = rnd(71);
  const g = ctx.createLinearGradient(0, 0, 0, H * 0.62); g.addColorStop(0, '#2b1d3f'); g.addColorStop(0.55, '#a34a4a'); g.addColorStop(1, '#f2a65a');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  const sun = ctx.createRadialGradient(W * 0.68, H * 0.58, 10, W * 0.68, H * 0.58, 120); sun.addColorStop(0, 'rgba(255,230,170,1)'); sun.addColorStop(1, 'rgba(255,230,170,0)'); ctx.fillStyle = sun; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#4a3550'; ctx.beginPath(); ctx.moveTo(0, H * 0.55); ctx.quadraticCurveTo(W * 0.25, H * 0.42, W * 0.5, H * 0.56); ctx.lineTo(W * 0.5, H * 0.62); ctx.lineTo(0, H * 0.62); ctx.closePath(); ctx.fill();
  const w = ctx.createLinearGradient(0, H * 0.62, 0, H); w.addColorStop(0, '#5a3a4a'); w.addColorStop(1, '#1d1828'); ctx.fillStyle = w; ctx.fillRect(0, H * 0.62, W, H * 0.38);
  for (let i = 0; i < 40; i++){ ctx.fillStyle = 'rgba(255,200,140,' + (0.1 + r() * 0.2) + ')'; ctx.fillRect(W * 0.55 + r() * 260, H * 0.64 + r() * H * 0.3, 40 + r() * 60, 2); }
  ctx.fillStyle = '#1a1420';
  ctx.beginPath(); ctx.moveTo(W * 0.1, H * 0.62); ctx.lineTo(W * 0.16, H * 0.5); ctx.lineTo(W * 0.62, H * 0.5); ctx.lineTo(W * 0.66, H * 0.62); ctx.closePath(); ctx.fill();
  ctx.fillRect(W * 0.3, H * 0.4, W * 0.12, H * 0.1); ctx.fillRect(W * 0.33, H * 0.33, W * 0.03, H * 0.07);
  for (const x of [0.08, 0.5, 0.78]){ ctx.fillRect(W * x, H * 0.18, 10, H * 0.44); ctx.fillRect(W * x - 50, H * 0.18, 150, 9); ctx.strokeStyle = '#1a1420'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(W * x + 100, H * 0.18); ctx.lineTo(W * x + 100, H * 0.34); ctx.stroke(); }
  ctx.fillStyle = 'rgba(255,240,215,0.9)'; ctx.font = '400 60px ' + F.display;
  [['♪', 0.42, 0.24], ['♫', 0.58, 0.16], ['♪', 0.7, 0.3], ['♫', 0.24, 0.2]].forEach(([n, x, y]) => ctx.fillText(n, W * x, H * y));
  ctx.fillStyle = 'rgba(255,240,215,0.92)'; ctx.font = '400 26px ' + F.type; ctx.textAlign = 'left'; ctx.fillText('MARIN CITY · WORLD WAR II · LOST STORIES', 50, H - 46);
  return c;
}
function artArMap(W, H){
  const c = mk(W, H), ctx = c.getContext('2d'), r = rnd(81);
  ctx.fillStyle = '#9fc3d6'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#ece4d2'; ctx.beginPath(); ctx.moveTo(W * 0.22, 0); ctx.lineTo(W * 0.86, 0); ctx.quadraticCurveTo(W * 0.9, H * 0.5, W * 0.62, H * 0.96); ctx.quadraticCurveTo(W * 0.4, H * 0.82, W * 0.2, H * 0.45); ctx.closePath(); ctx.fill();
  ctx.save(); ctx.clip();
  ctx.strokeStyle = 'rgba(120,110,95,0.55)'; ctx.lineWidth = 6;
  for (let x = 0; x < W; x += 70){ ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x + 40, H); ctx.stroke(); }
  for (let y = 0; y < H; y += 80){ ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y - 30); ctx.stroke(); }
  ctx.restore();
  const pins = [[0.4, 0.2], [0.58, 0.3], [0.48, 0.45], [0.66, 0.55], [0.55, 0.72]];
  ctx.strokeStyle = '#b5473a'; ctx.lineWidth = 6; ctx.setLineDash([16, 12]); ctx.beginPath(); pins.forEach(([x, y], i) => (i ? ctx.lineTo : ctx.moveTo).call(ctx, W * x, H * y)); ctx.stroke(); ctx.setLineDash([]);
  pins.forEach(([x, y], i) => { const px = W * x, py = H * y; ctx.fillStyle = '#b5473a'; ctx.beginPath(); ctx.arc(px, py - 26, 26, Math.PI, 0); ctx.lineTo(px, py + 10); ctx.closePath(); ctx.fill(); ctx.fillStyle = '#fff'; ctx.font = '700 26px ' + F.ui; ctx.textAlign = 'center'; ctx.fillText(String(i + 1), px, py - 18); });
  const px = W * 0.1, py = H * 0.5, pw = W * 0.34, ph = pw * 1.9;
  ctx.fillStyle = '#16181d'; rrect(ctx, px, py, pw, ph, 36); ctx.fill();
  const sx = px + 14, sy = py + 40, sw = pw - 28, sh = ph - 80;
  const sg = ctx.createLinearGradient(0, sy, 0, sy + sh); sg.addColorStop(0, '#c9b49a'); sg.addColorStop(1, '#7d6a58'); ctx.fillStyle = sg; ctx.fillRect(sx, sy, sw, sh);
  ctx.fillStyle = '#5b4a3c'; ctx.fillRect(sx + sw * 0.1, sy + sh * 0.35, sw * 0.8, sh * 0.5); ctx.fillStyle = '#e8d8a8'; for (let i = 0; i < 3; i++) ctx.fillRect(sx + sw * (0.18 + i * 0.25), sy + sh * 0.45, sw * 0.14, sh * 0.16);
  ctx.fillStyle = '#b5473a'; ctx.beginPath(); ctx.arc(sx + sw / 2, sy + sh * 0.18, 30, Math.PI, 0); ctx.lineTo(sx + sw / 2, sy + sh * 0.28); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#fff'; ctx.font = '700 22px ' + F.ui; ctx.textAlign = 'center'; ctx.fillText('STOP 3', sx + sw / 2, sy + sh * 0.94);
  ctx.fillStyle = '#16181d'; ctx.font = '400 30px ' + F.type; ctx.textAlign = 'left'; ctx.fillText('CHARLESTON · AR SCAVENGER HUNT', 40, H - 40);
  return c;
}
function artScan(W, H){
  const c = mk(W, H), ctx = c.getContext('2d'), r = rnd(91);
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#203a5c'); g.addColorStop(0.55, '#c98a5a'); g.addColorStop(0.56, '#6a7a4a'); g.addColorStop(1, '#3d4a2a');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  const ridge = (y0, amp, col, seed) => { const rr = rnd(seed); ctx.fillStyle = col; ctx.beginPath(); ctx.moveTo(0, H); for (let x = 0; x <= W; x += 20) ctx.lineTo(x, y0 + Math.sin(x * 0.006 + seed) * amp + rr() * 6); ctx.lineTo(W, H); ctx.closePath(); ctx.fill(); };
  ridge(H * 0.5, 30, '#7d6a4f', 3); ridge(H * 0.6, 40, '#5c6b3e', 7); ridge(H * 0.74, 26, '#43512d', 11);
  ctx.save(); ctx.beginPath(); ctx.rect(W * 0.5, 0, W * 0.5, H); ctx.clip();
  ctx.fillStyle = 'rgba(15,30,40,0.55)'; ctx.fillRect(W * 0.5, 0, W * 0.5, H);
  ctx.strokeStyle = 'rgba(120,230,220,0.75)'; ctx.lineWidth = 1.6;
  const pts = []; for (let i = 0; i < 16; i++) for (let j = 0; j < 9; j++){ const x = W * 0.5 + i * (W * 0.5 / 15), y = H * 0.48 + j * (H * 0.52 / 8) + Math.sin(i * 0.8) * 14 + (r() - 0.5) * 10; pts.push([x, y]); }
  for (let i = 0; i < 15; i++) for (let j = 0; j < 8; j++){ const a = pts[i * 9 + j], b = pts[(i + 1) * 9 + j], cc = pts[i * 9 + j + 1], d = pts[(i + 1) * 9 + j + 1]; ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.lineTo(d[0], d[1]); ctx.lineTo(cc[0], cc[1]); ctx.closePath(); ctx.stroke(); ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(d[0], d[1]); ctx.stroke(); }
  ctx.restore();
  const sy = H * 0.66; const sg = ctx.createLinearGradient(0, sy - 16, 0, sy + 16); sg.addColorStop(0, 'rgba(120,230,220,0)'); sg.addColorStop(0.5, 'rgba(160,255,240,0.85)'); sg.addColorStop(1, 'rgba(120,230,220,0)');
  ctx.fillStyle = sg; ctx.fillRect(W * 0.5, sy - 16, W * 0.5, 32);
  ctx.fillStyle = 'rgba(255,255,255,0.92)'; ctx.font = '400 24px ' + F.type; ctx.textAlign = 'left'; ctx.fillText('3D SCAN · BROWSER WORLD · LANGUAGE AND LAND', 46, H - 40);
  return c;
}
function crayon(ctx, pts, col, w, r){ ctx.strokeStyle = col; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; for (let k = 0; k < 3; k++){ ctx.lineWidth = w * (0.6 + r() * 0.5); ctx.globalAlpha = 0.55 + r() * 0.3; ctx.beginPath(); pts.forEach(([x, y], i) => (i ? ctx.lineTo : ctx.moveTo).call(ctx, x + (r() - 0.5) * 3, y + (r() - 0.5) * 3)); ctx.stroke(); } ctx.globalAlpha = 1; }
function artDrawings(W, H){
  const c = mk(W, H), ctx = c.getContext('2d'), r = rnd(101);
  ctx.fillStyle = '#e8e2d4'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#2b2419'; ctx.font = '400 24px ' + F.type; ctx.textAlign = 'left'; ctx.fillText('A 3D EXHIBITION OF CHILDREN’S ART', 50, 70);
  const fw = (W - 100 - 40) / 3, fh = (H - 140 - 20) / 2;
  for (let i = 0; i < 6; i++){
    const x = 50 + (i % 3) * (fw + 20), y = 100 + Math.floor(i / 3) * (fh + 20);
    ctx.fillStyle = '#5a3b22'; ctx.fillRect(x, y, fw, fh); ctx.fillStyle = '#fbfaf4'; ctx.fillRect(x + 14, y + 14, fw - 28, fh - 28);
    const cx = x + fw / 2, cy = y + fh / 2, s = Math.min(fw, fh) * 0.32;
    if (i === 0){ for (let k = 0; k < 12; k++){ const a = k * Math.PI / 6; crayon(ctx, [[cx, cy - s * 0.2], [cx + Math.cos(a) * s * 0.9, cy - s * 0.2 + Math.sin(a) * s * 0.9]], '#f2c14e', 10, r); } crayon(ctx, [[cx, cy + s * 0.2], [cx, cy + s * 1.3]], '#4a7a2e', 8, r); ctx.fillStyle = '#6b4a12'; ctx.beginPath(); ctx.arc(cx, cy - s * 0.2, s * 0.32, 0, Math.PI * 2); ctx.fill(); }
    else if (i === 1){ crayon(ctx, [[cx - s, cy + s], [cx - s, cy], [cx, cy - s * 0.8], [cx + s, cy], [cx + s, cy + s], [cx - s, cy + s]], '#b5473a', 8, r); crayon(ctx, [[cx - s * 0.2, cy + s], [cx - s * 0.2, cy + s * 0.4], [cx + s * 0.25, cy + s * 0.4], [cx + s * 0.25, cy + s]], '#2a4a7a', 6, r); ctx.fillStyle = '#f2c14e'; ctx.beginPath(); ctx.arc(cx + s * 1.1, cy - s * 1.0, s * 0.3, 0, Math.PI * 2); ctx.fill(); }
    else if (i === 2){ crayon(ctx, [[cx - s, cy], [cx - s * 0.3, cy - s * 0.4], [cx, cy], [cx + s * 0.3, cy - s * 0.4], [cx + s, cy]], '#2a4a7a', 7, r); crayon(ctx, [[cx - s * 0.2, cy + s * 0.2], [cx + s * 0.5, cy + s * 0.1]], '#4a7a2e', 6, r); crayon(ctx, [[cx - s * 1.1, cy + s * 0.9], [cx + s * 1.1, cy + s * 0.9]], '#8fb8db', 10, r); }
    else if (i === 3){ ['#b5473a', '#e07b2a', '#f2c14e', '#4a7a2e', '#2a4a7a'].forEach((col, k) => { const rr = s * (1.2 - k * 0.16); const pts = []; for (let t = 0; t <= 20; t++){ const a = Math.PI + t * Math.PI / 20; pts.push([cx + Math.cos(a) * rr, cy + s * 0.6 + Math.sin(a) * rr]); } crayon(ctx, pts, col, 9, r); }); }
    else if (i === 4){ crayon(ctx, [[cx, cy + s * 1.2], [cx, cy - s * 0.2]], '#6b4a2b', 12, r); for (let k = 0; k < 7; k++){ const a = r() * Math.PI * 2, d = r() * s * 0.7; ctx.fillStyle = 'rgba(74,122,46,0.75)'; ctx.beginPath(); ctx.arc(cx + Math.cos(a) * d, cy - s * 0.5 + Math.sin(a) * d * 0.7, s * 0.4, 0, Math.PI * 2); ctx.fill(); } }
    else { for (let k = 0; k < 4; k++){ const fx = cx - s + k * s * 0.66, fy = cy + s * 0.2; crayon(ctx, [[fx, fy], [fx, fy + s * 0.9]], '#4a7a2e', 6, r); ['#b5473a', '#f2c14e', '#7a3b6e', '#e07b2a'].forEach((col, q) => { if (q === k % 4){ ctx.fillStyle = col; for (let p = 0; p < 5; p++){ const a = p * Math.PI * 0.4; ctx.beginPath(); ctx.arc(fx + Math.cos(a) * 12, fy + Math.sin(a) * 12, 10, 0, Math.PI * 2); ctx.fill(); } } }); } }
  }
  return c;
}
function butterfly(ctx, x, y, s, a){
  ctx.save(); ctx.translate(x, y); ctx.rotate(a || 0); ctx.scale(s / 100, s / 100);
  const wing = (sx) => { ctx.fillStyle = '#e8862a'; ctx.beginPath(); ctx.moveTo(0, 0); ctx.bezierCurveTo(sx * 30, -60, sx * 90, -50, sx * 80, -6); ctx.bezierCurveTo(sx * 76, 10, sx * 30, 10, 0, 0); ctx.fill(); ctx.beginPath(); ctx.moveTo(0, 2); ctx.bezierCurveTo(sx * 40, 10, sx * 64, 40, sx * 40, 56); ctx.bezierCurveTo(sx * 20, 60, sx * 6, 30, 0, 2); ctx.fill(); ctx.strokeStyle = '#1d1a16'; ctx.lineWidth = 5; ctx.stroke(); ctx.fillStyle = '#fff'; for (let k = 0; k < 4; k++){ ctx.beginPath(); ctx.arc(sx * (70 - k * 8), -10 + k * 4, 2.5, 0, Math.PI * 2); ctx.fill(); } };
  wing(1); wing(-1);
  ctx.fillStyle = '#1d1a16'; ctx.fillRect(-4, -26, 8, 70); ctx.lineWidth = 3; ctx.strokeStyle = '#1d1a16'; ctx.beginPath(); ctx.moveTo(0, -24); ctx.lineTo(-12, -44); ctx.moveTo(0, -24); ctx.lineTo(12, -44); ctx.stroke();
  ctx.restore();
}
function flower(ctx, x, y, s, col){ ctx.strokeStyle = '#3f6b2a'; ctx.lineWidth = s * 0.08; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, y + s * 1.6); ctx.stroke(); ctx.fillStyle = col; for (let k = 0; k < 6; k++){ const a = k * Math.PI / 3; ctx.beginPath(); ctx.ellipse(x + Math.cos(a) * s * 0.42, y + Math.sin(a) * s * 0.42, s * 0.36, s * 0.22, a, 0, Math.PI * 2); ctx.fill(); } ctx.fillStyle = '#f2c14e'; ctx.beginPath(); ctx.arc(x, y, s * 0.24, 0, Math.PI * 2); ctx.fill(); }
function artPollinators(W, H){
  const c = mk(W, H), ctx = c.getContext('2d'), r = rnd(111);
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#9cc9e6'); g.addColorStop(0.5, '#dff0e4'); g.addColorStop(0.52, '#7fb05a'); g.addColorStop(1, '#4a7a2e');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 26; i++) flower(ctx, r() * W, H * 0.58 + r() * H * 0.36, 24 + r() * 26, ['#d94f7a', '#f2f2f2', '#b56ad9', '#e8a33a', '#e05a4a'][i % 5]);
  for (let i = 0; i < 5; i++) butterfly(ctx, 80 + r() * (W * 0.45), 80 + r() * H * 0.4, 60 + r() * 50, (r() - 0.5) * 0.6);
  const px = W * 0.56, py = H * 0.16, pw = W * 0.36, ph = pw * 1.95;
  ctx.fillStyle = '#16181d'; rrect(ctx, px, py, pw, ph, 40); ctx.fill();
  const sx = px + 16, sy = py + 46, sw = pw - 32, sh = ph - 92;
  ctx.save(); ctx.beginPath(); ctx.rect(sx, sy, sw, sh); ctx.clip();
  const sg = ctx.createLinearGradient(0, sy, 0, sy + sh); sg.addColorStop(0, '#a9d3ec'); sg.addColorStop(0.45, '#cfe6d2'); sg.addColorStop(0.46, '#86b866'); sg.addColorStop(1, '#4d7e33'); ctx.fillStyle = sg; ctx.fillRect(sx, sy, sw, sh);
  for (let i = 0; i < 7; i++) flower(ctx, sx + 30 + (i % 4) * (sw / 4), sy + sh * 0.55 + Math.floor(i / 4) * 90, 34, ['#d94f7a', '#b56ad9', '#e8a33a', '#e05a4a'][i % 4]);
  butterfly(ctx, sx + sw * 0.5, sy + sh * 0.25, 90, 0.2);
  ctx.restore();
  ctx.fillStyle = '#ffffff'; rrect(ctx, sx + sw * 0.2, sy + sh - 80, sw * 0.6, 52, 26); ctx.fill();
  ctx.fillStyle = '#2f5d2a'; ctx.font = '700 26px ' + F.ui; ctx.textAlign = 'center'; ctx.fillText('PLANT A FLOWER', sx + sw / 2, sy + sh - 45);
  ctx.fillStyle = '#16302a'; ctx.font = '400 30px ' + F.type; ctx.textAlign = 'left'; ctx.fillText('MARIN COUNTY FAIR 2025 · AR', 46, H - 40);
  return c;
}
function artHeadset(W, H){
  const [c, ctx] = posterBase(W, H, '#1a2422', 121);
  const cx = W / 2, cy = H * 0.46, w = W * 0.62, h = w * 0.5;
  ctx.strokeStyle = '#3a3f44'; ctx.lineWidth = 30; ctx.beginPath(); ctx.ellipse(cx, cy - h * 0.1, w * 0.62, h * 0.9, 0, Math.PI * 1.08, Math.PI * 1.92); ctx.stroke();
  const g = ctx.createLinearGradient(0, cy - h / 2, 0, cy + h / 2); g.addColorStop(0, '#f2f2f0'); g.addColorStop(1, '#bfc3c6');
  ctx.fillStyle = g; rrect(ctx, cx - w / 2, cy - h / 2, w, h, h * 0.34); ctx.fill();
  ctx.fillStyle = '#2b2f33'; rrect(ctx, cx - w / 2 + 24, cy - h / 2 + 24, w - 48, h - 48, h * 0.26); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.12)'; rrect(ctx, cx - w / 2 + 40, cy - h / 2 + 34, w * 0.5, h * 0.18, 20); ctx.fill();
  for (const [u, v] of [[-0.36, -0.2], [0.36, -0.2], [-0.36, 0.22], [0.36, 0.22]]){ ctx.fillStyle = '#111'; ctx.beginPath(); ctx.arc(cx + u * w, cy + v * h, 14, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = '#5a6a7a'; ctx.beginPath(); ctx.arc(cx + u * w - 3, cy + v * h - 3, 5, 0, Math.PI * 2); ctx.fill(); }
  ctx.fillStyle = CREAM; ctx.textAlign = 'center'; ctx.font = '400 54px ' + F.display; ctx.fillText('Standalone VR headset', cx, H * 0.8);
  ctx.fillStyle = BRASS; ctx.font = '400 24px ' + F.type; ctx.fillText('NO COMPUTER · NO CABLES · TRACKS HEAD AND HANDS', cx, H * 0.86);
  return c;
}
const PLAYBOOK_CATS = ['Astronomy', 'History', 'Life Science', 'Physical Science', 'Environment', 'Travel', 'Museums', 'Music', 'Mindfulness', 'Health', 'Simulation', 'Play'];
function drawPlaybookCover(W, H){
  W = W || 600; H = H || 800;
  const c = mk(W, H), ctx = c.getContext('2d');
  const g = ctx.createLinearGradient(0, 0, W, H); g.addColorStop(0, '#2f6b6b'); g.addColorStop(1, '#1d3b52'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#ffffff'; ctx.font = '700 58px ' + F.ui; ctx.textAlign = 'left'; ctx.fillText('XR', 40, 96); ctx.fillText('PLAYBOOK', 40, 156);
  ctx.fillStyle = '#f2c14e'; ctx.font = '600 24px ' + F.ui; ctx.fillText('Apps pre-installed for library programs', 40, 200);
  const cols = ['#f2c14e', '#e07b2a', '#5aa08c', '#8fb8db', '#d94f7a', '#b56ad9'];
  PLAYBOOK_CATS.forEach((n, i) => {
    const x = 40 + (i % 2) * ((W - 100) / 2 + 20), y = 240 + Math.floor(i / 2) * 88, w = (W - 100) / 2, h = 72;
    ctx.fillStyle = 'rgba(255,255,255,0.1)'; ctx.fillRect(x, y, w, h);
    ctx.fillStyle = cols[i % cols.length]; ctx.fillRect(x, y, 10, h);
    ctx.fillStyle = '#ffffff'; ctx.font = '600 26px ' + F.ui; ctx.fillText(n, x + 26, y + 46);
  });
  ctx.fillStyle = 'rgba(255,255,255,0.7)'; ctx.font = '400 20px ' + F.type; ctx.fillText('300+ APPS · CATEGORIES FROM XRLIBRARIES', 40, H - 34);
  return c;
}
function makeArt(it){
  const a = it.art, sz = it.size || [1, 1], W = sz[0] >= sz[1] ? (sz[0] / sz[1] > 1.2 ? 960 : 900) : 900, H = Math.round(W * sz[1] / sz[0]);
  switch (a.type){
    case 'bignum': return artBignum(a, W, H);
    case 'quote': return artQuote(a, it, W, H);
    case 'badge': return artProgram(W, H);
    case 'sectors': return artSectors(W, H);
    case 'story': return artStory(W, H);
    case 'episodes': return artEpisodes(W, H);
    case 'shipyard': return artShipyard(W, H);
    case 'armap': return artArMap(W, H);
    case 'scan': return artScan(W, H);
    case 'drawings': return artDrawings(W, H);
    case 'pollinators': return artPollinators(1000, 1000);
    case 'headset': return artHeadset(900, 900);
    case 'playbook': return drawPlaybookCover(600, 800);
  }
  return mk(4, 4);
}

/* Book covers */
function drawIcon(ctx, kind, cx, cy, s, col){
  ctx.save(); ctx.translate(cx, cy); ctx.scale(s / 100, s / 100);
  ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = 5; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  const L = (pts) => { ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]); ctx.stroke(); };
  const C = (x, y, r, a0, a1) => { ctx.beginPath(); ctx.arc(x, y, r, a0 == null ? 0 : a0, a1 == null ? Math.PI * 2 : a1); ctx.stroke(); };
  switch (kind){
    case 'headset': rrect(ctx, -48, -24, 96, 50, 18); ctx.stroke(); C(-20, 1, 11); C(20, 1, 11); L([[-48, -4], [-60, -10]]); L([[48, -4], [60, -10]]); break;
    case 'phone': rrect(ctx, -28, -48, 56, 96, 10); ctx.stroke(); L([[-8, 38], [8, 38]]); C(0, -6, 14); L([[0, -20], [0, -34]]); break;
    case 'checklist': for (let i = 0; i < 3; i++){ ctx.strokeRect(-40, -38 + i * 30, 18, 18); L([[-10, -29 + i * 30], [40, -29 + i * 30]]); } L([[-37, -30], [-31, -24], [-22, -36]]); break;
    case 'case': ctx.strokeRect(-46, -20, 92, 58); L([[-16, -20], [-16, -34], [16, -34], [16, -20]]); L([[-46, 4], [46, 4]]); break;
    case 'camera': C(0, 0, 40); C(0, 0, 16); L([[-40, 0], [-56, 0]]); L([[40, 0], [56, 0]]); ctx.beginPath(); ctx.ellipse(0, 0, 54, 18, 0, 0, Math.PI * 2); ctx.stroke(); break;
    case 'mic': ctx.strokeRect(-14, -46, 28, 52); L([[-28, -8], [-28, 4]]); C(0, 4, 28, 0, Math.PI); L([[28, -8], [28, 4]]); L([[0, 32], [0, 46]]); L([[-18, 46], [18, 46]]); break;
    case 'ship': L([[-50, 10], [50, 10], [36, 34], [-38, 34], [-50, 10]]); L([[-10, 10], [-10, -40]]); L([[-10, -40], [30, -6], [-10, -6]]); L([[-56, 46], [-30, 40], [0, 46], [30, 40], [56, 46]]); break;
    case 'lens': C(-12, -12, 30); L([[10, 10], [42, 42]]); break;
    case 'wave': for (let k = 0; k < 3; k++) L([[-50, -20 + k * 20], [-30, -32 + k * 20], [-10, -20 + k * 20], [10, -32 + k * 20], [30, -20 + k * 20], [50, -32 + k * 20]]); break;
    case 'drop': ctx.beginPath(); ctx.moveTo(0, -46); ctx.bezierCurveTo(30, -10, 34, 6, 34, 16); ctx.arc(0, 16, 34, 0, Math.PI); ctx.bezierCurveTo(-34, 6, -30, -10, 0, -46); ctx.stroke(); break;
    case 'globe': C(0, 0, 44); ctx.beginPath(); ctx.ellipse(0, 0, 18, 44, 0, 0, Math.PI * 2); ctx.stroke(); L([[-44, 0], [44, 0]]); L([[-38, -22], [38, -22]]); L([[-38, 22], [38, 22]]); break;
    case 'code': L([[-20, -30], [-48, 0], [-20, 30]]); L([[20, -30], [48, 0], [20, 30]]); L([[10, -40], [-10, 40]]); break;
    case 'network': { const P = [[-36, -28], [30, -36], [0, 4], [-34, 36], [36, 30]]; for (const [a, b] of [[0, 2], [1, 2], [2, 3], [2, 4], [0, 1], [3, 4]]) L([P[a], P[b]]); for (const p of P){ ctx.beginPath(); ctx.arc(p[0], p[1], 9, 0, Math.PI * 2); ctx.fill(); } } break;
  }
  ctx.restore();
}
function drawBookCover(b, W, H){
  W = W || 512; H = H || 700;
  const c = mk(W, H), ctx = c.getContext('2d'), r = rnd(b.id.length * 131 + b.title.length);
  const base = SUBJ[b.subject].color;
  const g = ctx.createLinearGradient(0, 0, W, H); g.addColorStop(0, shade(base, 0.12)); g.addColorStop(1, shade(base, -0.28));
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  noise(ctx, W, H, r, 2600, 0.035);
  ctx.fillStyle = 'rgba(0,0,0,0.22)'; ctx.fillRect(0, 0, 22, H);
  ctx.strokeStyle = GOLD; ctx.lineWidth = 3; ctx.strokeRect(44, 36, W - 80, H - 72); ctx.lineWidth = 1.2; ctx.strokeRect(54, 46, W - 100, H - 92);
  ctx.fillStyle = GOLD; ctx.textAlign = 'center'; ctx.font = '700 19px ' + F.type; ctx.fillText(SUBJ[b.subject].name.toUpperCase(), W / 2 + 11, 96);
  ctx.fillStyle = '#f3e7cc';
  let size = 58; ctx.font = '400 ' + size + 'px ' + F.display;
  let ls = wrap(ctx, b.title, W - 150);
  while (ls.length > 3 && size > 34){ size -= 4; ctx.font = '400 ' + size + 'px ' + F.display; ls = wrap(ctx, b.title, W - 150); }
  let y = 180;
  for (const l of ls){ ctx.fillText(l, W / 2 + 11, y); y += size * 1.08; }
  ctx.fillStyle = 'rgba(243,231,204,0.82)'; ctx.font = 'italic 400 25px ' + F.display;
  for (const l of wrap(ctx, b.sub, W - 170).slice(0, 2)){ ctx.fillText(l, W / 2 + 11, y + 14); y += 31; }
  drawIcon(ctx, b.icon, W / 2 + 11, H * 0.7, 150, GOLD);
  ctx.fillStyle = GOLD; ctx.font = '700 16px ' + F.type; ctx.fillText('XRLIBRARIES CAMPUS LIBRARY', W / 2 + 11, H - 70);
  return c;
}

/* Signs and wall graphics */
function signBase(W, H, bg){
  const c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = bg || '#101814'; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = 'rgba(205,169,97,0.85)'; ctx.lineWidth = 3; ctx.strokeRect(14, 14, W - 28, H - 28);
  return [c, ctx];
}
function panelBase(W, H){
  const c = mk(W, H), ctx = c.getContext('2d');
  const g = ctx.createLinearGradient(0, 0, W, H); g.addColorStop(0, '#203b33'); g.addColorStop(1, '#14261f'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = 'rgba(205,169,97,0.9)'; ctx.lineWidth = 3; ctx.strokeRect(36, 36, W - 72, H - 72);
  return [c, ctx];
}
function drawTitlePanel(){
  const W = 1600, H = 844, [c, ctx] = panelBase(W, H), M = 110;
  ctx.fillStyle = BRASS; ctx.font = '400 30px ' + F.type; ctx.textAlign = 'left'; ctx.fillText('A CONCEPT FOR XRLIBRARIES  ·  BY EV HOLT', M, 160);
  ctx.fillStyle = CREAM; fit(ctx, 'XRLibraries Campus', F.display, '400', 150, W - 2*M); ctx.fillText('XRLibraries Campus', M, 324);
  ctx.fillStyle = 'rgba(239,231,213,0.85)'; ctx.font = '400 40px ' + F.ui;
  wrap(ctx, 'Since 2016, XRLibraries has brought virtual reality into libraries and schools. Walk its story, read up on XR, make something in 3D, then head out to recess.', W - 2*M - 80).forEach((l, i) => ctx.fillText(l, M, 424 + i * 58));
  ctx.fillStyle = BRASS; ctx.font = '400 32px ' + F.type; ctx.fillText('MUSEUM  ·  LIBRARY  ·  WORKSHOP SCHOOL  ·  RECESS YARD', M, H - 120);
  return c;
}
function drawPartnersPanel(){
  const W = 1600, H = 844, [c, ctx] = panelBase(W, H), M = 110;
  ctx.fillStyle = BRASS; ctx.font = '400 30px ' + F.type; ctx.textAlign = 'left'; ctx.fillText('PARTNERS LISTED ON XRLIBRARIES.COM', M, 160);
  const names = ['Meta Quest', 'Pico', 'Hydrous', 'Washington State Library', 'Nevada State Library', 'California State Library', 'American Library Association', 'Internet Librarian', 'Marin County Office of Education', 'XRMarin', 'New Media Learning', 'FastForward', 'SJSU School of Information'];
  ctx.fillStyle = CREAM; ctx.font = '400 40px ' + F.display;
  const colW = (W - 2*M) / 2;
  names.forEach((n, i) => { const col = i < 7 ? 0 : 1, row = i < 7 ? i : i - 7; ctx.fillText(n, M + col * colW, 250 + row * 76); });
  return c;
}
function drawPlaque(){
  const W = 1200, H = 520, c = mk(W, H), ctx = c.getContext('2d');
  const g = ctx.createLinearGradient(0, 0, W, H); g.addColorStop(0, '#b38c48'); g.addColorStop(0.5, '#dcbd7e'); g.addColorStop(1, '#a37e3d'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = 'rgba(60,40,15,0.65)'; ctx.lineWidth = 3; ctx.strokeRect(22, 22, W - 44, H - 44);
  ctx.fillStyle = '#3a2810'; ctx.textAlign = 'center';
  ctx.font = '700 26px ' + F.type; ctx.fillText('AN UNOFFICIAL CONCEPT', W/2, 96);
  ctx.font = '400 34px ' + F.display;
  wrap(ctx, 'Made by Ev Holt with Walk the Archive as a concept for XRLibraries. Facts come from public sources such as xrlibraries.com. This is not an official XRLibraries site.', W - 200).forEach((l, i) => ctx.fillText(l, W/2, 172 + i * 48));
  ctx.font = 'italic 400 30px ' + F.display; ctx.fillText('Built by Ev Holt with Walk the Archive', W/2, H - 70);
  return c;
}
function drawDoorSign(gal, idx){
  const [c, ctx] = signBase(1400, 240);
  ctx.fillStyle = BRASS; ctx.font = '400 30px ' + F.type; ctx.textAlign = 'left'; ctx.fillText('GALLERY ' + idx, 60, 132);
  ctx.textAlign = 'right'; ctx.fillStyle = '#a9b8ae'; fit(ctx, gal.years.toUpperCase(), F.type, '400', 26, 300); ctx.fillText(gal.years.toUpperCase(), 1340, 132);
  ctx.textAlign = 'center'; ctx.fillStyle = CREAM; fit(ctx, gal.name, F.display, '400', 78, 1400 - 700); ctx.fillText(gal.name, 700, 148);
  return c;
}
function drawWingSign(name, sub){
  const [c, ctx] = signBase(1300, 220);
  ctx.textAlign = 'center'; ctx.fillStyle = CREAM; fit(ctx, name, F.display, '400', 84, 1100); ctx.fillText(name, 650, 118);
  ctx.fillStyle = BRASS; ctx.font = '400 30px ' + F.type; ctx.fillText(sub.toUpperCase(), 650, 172);
  return c;
}
function drawPlacard(it){
  const W = 600, H = 340, c = mk(W, H), ctx = c.getContext('2d');
  ctx.fillStyle = '#efe7d6'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#7a6a50'; ctx.font = '700 21px ' + F.type; ctx.textAlign = 'left'; ctx.fillText(KIND[it.kind].toUpperCase(), 34, 52);
  ctx.fillStyle = '#2b2419'; ctx.font = '700 34px ' + F.display;
  const ls = wrap(ctx, it.title, W - 68).slice(0, 2);
  ls.forEach((l, i) => ctx.fillText(l, 34, 108 + i * 40));
  const y = 108 + ls.length * 40 + 6;
  ctx.font = 'italic 400 25px ' + F.display; ctx.fillStyle = '#4c4232'; ctx.fillText(it.date, 34, y);
  ctx.fillStyle = '#7a6a50'; ctx.font = '400 19px ' + F.type; const s = srcList(it.src)[0]; ctx.fillText('Source: ' + (s ? s.label : 'XRLibraries'), 34, H - 34);
  return c;
}
function drawDirectory(){
  const W = 1500, H = 800, [c, ctx] = panelBase(W, H);
  ctx.fillStyle = BRASS; ctx.font = '400 30px ' + F.type; ctx.textAlign = 'left'; ctx.fillText('CAMPUS DIRECTORY', 90, 128);
  const rows = [['Museum', 'Three galleries plus the Wax Hall', 'OPEN · AHEAD'], ['Library', 'XR books and a reference desk', 'OPEN · LEFT'], ['Workshop School', 'Art, science, blueprints and world building', 'OPEN · RIGHT'], ['Recess Yard', 'Coaster, Sky Drop and Ocean Dive', 'PAST THE SCHOOL']];
  rows.forEach(([name, sub, status], i) => {
    const y = 238 + i * 140;
    ctx.fillStyle = 'rgba(205,169,97,0.45)'; ctx.fillRect(90, y - 68, W - 180, 2);
    ctx.textAlign = 'left'; ctx.fillStyle = CREAM; ctx.font = '400 56px ' + F.display; ctx.fillText(name, 90, y);
    ctx.fillStyle = 'rgba(239,231,213,0.75)'; ctx.font = '400 28px ' + F.ui; ctx.fillText(sub, 90, y + 46);
    ctx.textAlign = 'right'; ctx.font = '400 28px ' + F.type; ctx.fillStyle = BRASS; ctx.fillText(status, W - 90, y);
  });
  return c;
}
function drawLecternSign(){
  const W = 512, H = 190, c = mk(W, H), ctx = c.getContext('2d');
  const g = ctx.createLinearGradient(0, 0, W, H); g.addColorStop(0, '#b38c48'); g.addColorStop(0.5, '#dcbd7e'); g.addColorStop(1, '#a37e3d'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = 'rgba(60,40,15,0.6)'; ctx.lineWidth = 3; ctx.strokeRect(12, 12, W - 24, H - 24);
  ctx.fillStyle = '#3a2810'; ctx.textAlign = 'center'; ctx.font = '700 44px ' + F.type; ctx.fillText('ASK THE GUIDE', W/2, 92);
  ctx.font = 'italic 400 30px ' + F.display; ctx.fillText('Margaret will find it for you', W/2, 142);
  return c;
}
function drawStaffLabel(c, name, role){
  const ctx = c.getContext('2d'), W = c.width, H = c.height;
  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = 'rgba(21,34,30,0.94)'; rrect(ctx, 6, 6, W - 12, H - 40, 18); ctx.fill();
  ctx.strokeStyle = BRASS; ctx.lineWidth = 3; rrect(ctx, 6, 6, W - 12, H - 40, 18); ctx.stroke();
  ctx.fillStyle = 'rgba(21,34,30,0.94)'; ctx.beginPath(); ctx.moveTo(W/2 - 18, H - 36); ctx.lineTo(W/2, H - 8); ctx.lineTo(W/2 + 18, H - 36); ctx.closePath(); ctx.fill();
  ctx.textAlign = 'center'; ctx.fillStyle = CREAM; ctx.font = '400 62px ' + F.display; ctx.fillText(name, W/2, 80);
  const t = role.toUpperCase() + ' · TAP TO ASK'; ctx.fillStyle = BRASS; fit(ctx, t, F.type, '700', 27, W - 60); ctx.fillText(t, W/2, 126);
}
function drawSubjectSign(s){
  const [c, ctx] = signBase(560, 200, '#17110b');
  ctx.textAlign = 'center'; ctx.fillStyle = BRASS; ctx.font = '700 22px ' + F.type; ctx.fillText('SECTION', 280, 62);
  ctx.fillStyle = CREAM; fit(ctx, s.name, F.display, '400', 60, 480); ctx.fillText(s.name, 280, 138);
  return c;
}
function drawHangSign(){
  const [c, ctx] = signBase(1400, 380, '#13201b');
  ctx.textAlign = 'center';
  ctx.fillStyle = BRASS; ctx.font = '400 34px ' + F.type; ctx.fillText('XRLIBRARIES CAMPUS LIBRARY', 700, 96);
  ctx.fillStyle = CREAM; ctx.font = '400 150px ' + F.display; ctx.fillText('Reading Room', 700, 250);
  ctx.fillStyle = 'rgba(239,231,213,0.75)'; ctx.font = 'italic 400 38px ' + F.display; ctx.fillText('Free to read · No headset needed', 700, 318);
  return c;
}
function drawFreedomPanel(){
  const W = 1200, H = 900, [c, ctx] = panelBase(W, H), M = 90;
  ctx.fillStyle = BRASS; ctx.font = '400 26px ' + F.type; ctx.textAlign = 'left'; ctx.fillText('A SHARED WORLD · FRAMEVR', M, 130);
  ctx.fillStyle = CREAM; ctx.font = '400 100px ' + F.display; ctx.fillText('Freedom to Read', M, 240);
  ctx.fillStyle = 'rgba(239,231,213,0.88)'; ctx.font = '400 34px ' + F.ui;
  const y = lines(ctx, 'A VR environment that helps citizens, librarians and students fight book bans, and helps young people find challenged books that reflect their lives.', M, 320, W - 2 * M, 48, 4);
  ctx.fillStyle = BRASS; ctx.font = '400 24px ' + F.type; ctx.fillText('BUILT WITH', M, y + 40);
  ctx.fillStyle = CREAM; ctx.font = '400 34px ' + F.display; ['SJSU School of Information', 'Unite Against Book Bans', 'Little Free Library', 'Books Unbanned'].forEach((n, i) => ctx.fillText(n, M, y + 92 + i * 48));
  ctx.fillStyle = 'rgba(239,231,213,0.6)'; ctx.font = '400 22px ' + F.type; ctx.fillText('SOURCE: XRLIBRARIES.COM/METAVERSE', M, H - 70);
  return c;
}
function drawTableCard(top, bottom, bg, fg){
  const c = mk(900, 200), ctx = c.getContext('2d');
  ctx.fillStyle = bg || '#efe5cf'; ctx.fillRect(0, 0, 900, 200);
  ctx.strokeStyle = fg || '#3a2810'; ctx.lineWidth = 3; ctx.strokeRect(12, 12, 876, 176);
  ctx.fillStyle = fg || '#3a2810'; ctx.textAlign = 'center';
  fit(ctx, top, F.type, '700', 44, 820); ctx.fillText(top, 450, 92);
  ctx.font = 'italic 400 36px ' + F.display; ctx.fillText(bottom, 450, 150);
  return c;
}
function drawRoomSign(num, name, status, open){
  const c = mk(700, 300), ctx = c.getContext('2d');
  ctx.fillStyle = open ? '#1d3b52' : '#2d3a40'; ctx.fillRect(0, 0, 700, 300);
  ctx.fillStyle = '#ffffff'; ctx.textAlign = 'left'; ctx.font = '600 92px ' + F.ui; ctx.fillText(num, 40, 112);
  fit(ctx, name, F.ui, '600', 46, 620); ctx.fillText(name, 40, 196);
  ctx.fillStyle = open ? '#f2c14e' : '#b9c4c8'; ctx.font = '700 30px ' + F.type; ctx.fillText(status.toUpperCase(), 40, 258);
  return c;
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
    ctx.font = 'italic 400 28px ' + F.display; ctx.fillText('XRLibraries Campus Library', W/2, 740);
  } else if (kind === 'vr'){
    ctx.fillStyle = '#1d3b52'; ctx.fillRect(0, 0, W, H);
    for (let i = 0; i < 8; i++){ ctx.strokeStyle = 'rgba(242,193,78,' + (0.7 - i * 0.08) + ')'; ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(W/2, 360, 60 + i * 36, 0, Math.PI * 2); ctx.stroke(); }
    headsetGlyph(ctx, W/2 - 110, 300, 220, '#f2c14e');
    ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center'; ctx.font = '700 64px ' + F.ui; ctx.fillText('TRY VR', W/2, 140);
    ctx.font = '600 32px ' + F.ui; ['Ask at the desk.', 'Every headset is', 'cleaned after each turn.'].forEach((l, i) => ctx.fillText(l, W/2, 650 + i * 44));
  } else if (kind === 'workshop'){
    ctx.fillStyle = '#f2c14e'; ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = '#1d3b52'; ctx.textAlign = 'center';
    ctx.font = '700 64px ' + F.ui; ['EVERY', 'CLASS IS A', 'WORKSHOP'].forEach((l, i) => ctx.fillText(l, W/2, 150 + i * 78));
    ctx.fillStyle = '#c4572f'; for (let i = 0; i < 5; i++){ ctx.beginPath(); ctx.arc(110 + i * 95, 470, 32, 0, Math.PI * 2); ctx.fill(); }
    ctx.fillStyle = '#1d3b52'; ctx.font = '600 30px ' + F.ui; ['Paint it.', 'Film it.', 'Build it.', 'Share it.'].forEach((l, i) => ctx.fillText(l, W/2, 590 + i * 46));
  } else {
    ctx.fillStyle = '#1d3b52'; ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = '#f2c14e'; ctx.beginPath(); ctx.moveTo(60, 120); ctx.lineTo(W - 60, 200); ctx.lineTo(60, 280); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#1d3b52'; ctx.font = '700 46px ' + F.ui; ctx.textAlign = 'left'; ctx.fillText('XR CAMPUS', 84, 216);
    ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center'; ctx.font = '700 72px ' + F.display; ctx.fillText('Workshop', W/2, 450); ctx.fillText('School', W/2, 530);
    ctx.font = '400 30px ' + F.type; ctx.fillStyle = '#f2c14e'; ctx.fillText('HOME OF THE MAKERS', W/2, 640);
  }
  return c;
}
function drawFlyer(i){
  const W = 360, H = 460, c = mk(W, H), ctx = c.getContext('2d');
  const set = [
    ['#fdf6e3', '#c4572f', 'LAB DAY', ['Sieve test,', 'titration and', 'pendulum · 102']],
    ['#e6f0f5', '#1d3b52', 'SHOWCASE NIGHT', ['New VR apps', 'every month', 'in the library']],
    ['#fff1c9', '#6b4a12', 'LOST & FOUND', ['One controller', 'Two lanyards', 'A good idea']],
    ['#f3e3ea', '#7a2e4a', 'CLEAN IT', ['Wipe every', 'headset after', 'every turn']]
  ][i % 4];
  ctx.fillStyle = set[0]; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = set[1]; ctx.fillRect(0, 0, W, 90);
  ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center'; fit(ctx, set[2], F.ui, '700', 40, W - 40); ctx.fillText(set[2], W/2, 62);
  ctx.fillStyle = set[1]; ctx.font = '600 38px ' + F.ui; set[3].forEach((l, k) => ctx.fillText(l, W/2, 190 + k * 70));
  return c;
}
function drawChalkboard(){
  const W = 1800, H = 640, c = mk(W, H), ctx = c.getContext('2d'), r = rnd(8);
  ctx.fillStyle = '#25372f'; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 30; i++){ ctx.fillStyle = 'rgba(255,255,255,0.025)'; ctx.beginPath(); ctx.ellipse(r() * W, r() * H, 80 + r() * 200, 20 + r() * 60, r() * 3, 0, Math.PI * 2); ctx.fill(); }
  ctx.fillStyle = 'rgba(245,242,230,0.92)'; ctx.textAlign = 'left';
  ctx.font = '400 40px ' + F.type; ctx.fillText('TODAY’S WORKSHOP', 90, 110);
  ctx.font = '400 104px ' + F.display; ctx.fillText('Make art in 3D', 90, 220);
  const steps = ['Tap the easel to start', 'Pick a brush, or stamp a shape', 'Drag to draw in the air', 'Try Mirror, ×6 and a blank canvas'];
  ctx.font = '400 44px ' + F.ui; steps.forEach((s, i) => { ctx.fillText((i + 1) + '.  ' + s, 110, 320 + i * 72); });
  ctx.strokeStyle = 'rgba(245,242,230,0.85)'; ctx.lineWidth = 5;
  ctx.beginPath(); for (let t = 0; t < 200; t++){ const a = t * 0.12, rr = 6 + t * 0.9; const x = 1480 + Math.cos(a) * rr, y = 330 + Math.sin(a) * rr * 0.75; t ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.stroke();
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
  const mt = 'Art in 3D · Science Lab · Blueprints · World Building';
  ctx.fillStyle = '#f2c14e'; fit(ctx, mt, F.ui, '600', 52, W - 140); ctx.fillText(mt, W/2, 600);
  return c;
}

/* Surfaces */
function canvasFloor(base, seed){
  const S = 1024, c = mk(S, S), ctx = c.getContext('2d'), r = rnd(seed || 77), n = 8, pw = S / n;
  base = base || [98, 68, 44];
  for (let i = 0; i < n; i++){
    let y = -r() * 300;
    while (y < S){
      const len = 260 + r() * 420, b = [base[0] + r() * 20, base[1] + r() * 14, base[2] + r() * 10];
      ctx.fillStyle = 'rgb(' + b.map(Math.round).join(',') + ')'; ctx.fillRect(i * pw, y, pw, len);
      ctx.strokeStyle = 'rgba(60,35,18,0.22)'; ctx.lineWidth = 1;
      for (let k = 0; k < 9; k++){ const x0 = i * pw + 6 + r() * (pw - 12); ctx.beginPath(); ctx.moveTo(x0, y); for (let t = 0; t <= len; t += 24) ctx.lineTo(x0 + Math.sin((t + k * 40) * 0.02) * 3, y + t); ctx.stroke(); }
      ctx.fillStyle = 'rgba(25,14,6,0.65)'; ctx.fillRect(i * pw, y, pw, 2);
      y += len;
    }
    ctx.fillStyle = 'rgba(25,14,6,0.7)'; ctx.fillRect(i * pw, 0, 2, S);
  }
  return c;
}
function canvasPlaster(){
  const S = 512, c = mk(S, S), ctx = c.getContext('2d'), r = rnd(5);
  ctx.fillStyle = '#f1f1f1'; ctx.fillRect(0, 0, S, S);
  for (let i = 0; i < 9000; i++){ const v = 200 + r() * 55; ctx.fillStyle = 'rgba(' + v + ',' + v + ',' + v + ',0.08)'; ctx.fillRect(r() * S, r() * S, 2 + r() * 3, 2 + r() * 3); }
  return c;
}
function canvasPool(){
  const S = 256, c = mk(S, S), ctx = c.getContext('2d');
  const g = ctx.createRadialGradient(S/2, S * 0.42, 4, S/2, S/2, S/2);
  g.addColorStop(0, 'rgba(255,232,190,1)'); g.addColorStop(0.45, 'rgba(255,220,170,0.45)'); g.addColorStop(1, 'rgba(255,210,160,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, S, S);
  return c;
}
function canvasRunner(){
  const W = 1024, H = 256, c = mk(W, H), ctx = c.getContext('2d'), r = rnd(9);
  ctx.fillStyle = '#20392f'; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 6000; i++){ ctx.fillStyle = r() < 0.5 ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.08)'; ctx.fillRect(r() * W, r() * H, 2, 2); }
  ctx.fillStyle = '#8a6a32'; ctx.fillRect(0, 14, W, 8); ctx.fillRect(0, H - 22, W, 8);
  ctx.fillStyle = '#5a1f1c'; ctx.fillRect(0, 30, W, 6); ctx.fillRect(0, H - 36, W, 6);
  ctx.strokeStyle = 'rgba(138,106,50,0.55)'; ctx.lineWidth = 3;
  for (let x = 64; x < W; x += 128){ ctx.beginPath(); ctx.moveTo(x - 34, H/2); ctx.lineTo(x, H/2 - 34); ctx.lineTo(x + 34, H/2); ctx.lineTo(x, H/2 + 34); ctx.closePath(); ctx.stroke(); }
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
function canvasSky(){
  const W = 512, H = 256, c = mk(W, H), ctx = c.getContext('2d'), r = rnd(23);
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#9cc3e4'); g.addColorStop(1, '#eef4f6');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 14; i++){ const x = r() * W, y = r() * H * 0.8, s = 30 + r() * 60; const cg = ctx.createRadialGradient(x, y, 0, x, y, s); cg.addColorStop(0, 'rgba(255,255,255,0.7)'); cg.addColorStop(1, 'rgba(255,255,255,0)'); ctx.fillStyle = cg; ctx.fillRect(x - s, y - s, s * 2, s * 2); }
  return c;
}
function drawWindowView(W, H, seed){
  const c = mk(W, H), ctx = c.getContext('2d'), r = rnd(seed || 5);
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#8fb8db'); g.addColorStop(0.62, '#dce9ee'); g.addColorStop(1, '#f2efe2');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 18; i++){ const x = r() * W, y = r() * H * 0.45, s = W * (0.04 + r() * 0.08); const cg = ctx.createRadialGradient(x, y, 0, x, y, s); cg.addColorStop(0, 'rgba(255,255,255,0.75)'); cg.addColorStop(1, 'rgba(255,255,255,0)'); ctx.fillStyle = cg; ctx.fillRect(x - s, y - s, s * 2, s * 2); }
  ctx.fillStyle = '#9fb1a6'; ctx.beginPath(); ctx.moveTo(0, H * 0.7); for (let x = 0; x <= W; x += W / 12) ctx.lineTo(x, H * (0.62 + r() * 0.06)); ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath(); ctx.fill();
  for (let i = 0; i < 46; i++){ const x = r() * W, base = H * (0.76 + r() * 0.2), th = H * (0.08 + r() * 0.14), tw = th * 0.42; ctx.fillStyle = r() < 0.5 ? '#2f4a3b' : '#3b5a46'; ctx.beginPath(); ctx.moveTo(x, base - th); ctx.lineTo(x + tw / 2, base); ctx.lineTo(x - tw / 2, base); ctx.closePath(); ctx.fill(); }
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
