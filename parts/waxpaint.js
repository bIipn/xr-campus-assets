/* ================================================================
   Living History: painted stage floors and backdrops
   ================================================================ */
function waxFloorCanvas(kind){
  const W = 512, H = 360, c = mk(W, H), ctx = c.getContext('2d'), r = rnd(kind.length * 31 + 7);
  const speck = (n, a, col) => { for (let i = 0; i < n; i++){ ctx.fillStyle = col || (r() > 0.5 ? 'rgba(255,255,255,' + a + ')' : 'rgba(0,0,0,' + a + ')'); ctx.fillRect(r() * W, r() * H, 2 + r() * 2, 2 + r() * 2); } };
  const boards = (b0, b1, rows) => {
    const h = H / rows;
    for (let j = 0; j < rows; j++){
      let x = -r() * 200;
      while (x < W){ const len = 120 + r() * 200, v = r(); ctx.fillStyle = 'rgb(' + [b0[0] + (b1[0] - b0[0]) * v, b0[1] + (b1[1] - b0[1]) * v, b0[2] + (b1[2] - b0[2]) * v].map(Math.round).join(',') + ')'; ctx.fillRect(x, j * h, len, h); ctx.fillStyle = 'rgba(20,10,4,0.45)'; ctx.fillRect(x, j * h, 2, h); x += len; }
      ctx.fillStyle = 'rgba(20,10,4,0.5)'; ctx.fillRect(0, j * h, W, 1.5);
    }
    speck(1400, 0.04);
  };
  switch (kind){
    case 'carpet': ctx.fillStyle = '#2f4f52'; ctx.fillRect(0, 0, W, H); speck(5000, 0.05); ctx.strokeStyle = 'rgba(255,255,255,0.05)'; for (let x = 0; x < W; x += 32){ ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); } break;
    case 'rug':
      boards([150, 104, 66], [176, 126, 82], 9);
      for (const [rr, col] of [[150, '#d0523f'], [128, '#f2c14e'], [104, '#2a9d8f'], [80, '#3b6ea8'], [54, '#e76f51'], [28, '#f4e9d4']]){ ctx.fillStyle = col; ctx.beginPath(); ctx.ellipse(W / 2, H * 0.56, rr * 1.5, rr, 0, 0, Math.PI * 2); ctx.fill(); }
      break;
    case 'tile': for (let i = 0; i < 16; i++) for (let j = 0; j < 12; j++){ ctx.fillStyle = (i + j) % 2 ? '#e8e2d4' : '#3a3a3e'; ctx.fillRect(i * 32, j * 30, 32, 30); } speck(800, 0.04); break;
    case 'gym':
      boards([196, 152, 98], [216, 172, 116], 12);
      ctx.strokeStyle = '#c0392b'; ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(W * 0.5, H * 1.1, 180, Math.PI, Math.PI * 2); ctx.stroke();
      ctx.strokeStyle = '#1d4e89'; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(0, H * 0.25); ctx.lineTo(W, H * 0.25); ctx.stroke(); break;
    case 'office': for (let i = 0; i < 8; i++) for (let j = 0; j < 6; j++){ ctx.fillStyle = (i + j) % 2 ? '#5d6066' : '#666a70'; ctx.fillRect(i * 64, j * 60, 64, 60); } speck(3000, 0.05); break;
    case 'grass': {
      ctx.fillStyle = '#5f8a3a'; ctx.fillRect(0, 0, W, H);
      for (let i = 0; i < 9000; i++){ const g = 90 + r() * 80; ctx.fillStyle = 'rgba(' + Math.round(g * 0.55) + ',' + Math.round(g) + ',' + Math.round(g * 0.35) + ',0.5)'; ctx.fillRect(r() * W, r() * H, 1.5, 3 + r() * 4); }
      ctx.fillStyle = 'rgba(150,118,72,0.75)'; ctx.beginPath(); ctx.ellipse(W * 0.3, H * 0.62, 120, 60, 0.2, 0, Math.PI * 2); ctx.fill(); speck(600, 0.06); break;
    }
    case 'concrete': ctx.fillStyle = '#8d8a84'; ctx.fillRect(0, 0, W, H); speck(7000, 0.05); ctx.strokeStyle = 'rgba(0,0,0,0.18)'; ctx.lineWidth = 2; for (let x = 0; x < W; x += 128){ ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); } break;
    case 'meeting': ctx.fillStyle = '#3d4a5c'; ctx.fillRect(0, 0, W, H); speck(6000, 0.05); for (let y = 0; y < H; y += 24){ ctx.fillStyle = 'rgba(255,255,255,0.025)'; ctx.fillRect(0, y, W, 12); } break;
    case 'dock': boards([108, 92, 74], [132, 112, 90], 10); speck(2600, 0.07); break;
    case 'grid': {
      ctx.fillStyle = '#0b0d1a'; ctx.fillRect(0, 0, W, H);
      ctx.strokeStyle = 'rgba(120,170,255,0.55)'; ctx.lineWidth = 2;
      for (let x = 0; x <= W; x += 40){ ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
      for (let y = 0; y <= H; y += 40){ ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); } break;
    }
    case 'fair': {
      ctx.fillStyle = '#6d8d3e'; ctx.fillRect(0, 0, W, H);
      for (let i = 0; i < 6000; i++){ ctx.fillStyle = r() > 0.6 ? 'rgba(214,180,96,0.6)' : 'rgba(70,110,40,0.5)'; ctx.fillRect(r() * W, r() * H, 1.5, 4 + r() * 5); }
      break;
    }
    default: boards([168, 120, 78], [190, 142, 96], 9);
  }
  return c;
}

/* Backdrops: soft, painterly scenery behind the figures, like a museum diorama */
function waxBackdrop(kind, L){
  const W = 1024, H = Math.round(1024 * 3.55 / L), c = mk(W, H), ctx = c.getContext('2d'), r = rnd(kind.length * 13 + 5);
  const grad = (y0, y1, stops) => { const g = ctx.createLinearGradient(0, y0, 0, y1); stops.forEach(([o, col]) => g.addColorStop(o, col)); return g; };
  const vignette = (a) => { const g = ctx.createRadialGradient(W / 2, H * 0.45, H * 0.2, W / 2, H * 0.5, W * 0.75); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,' + a + ')'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); };
  const shelves = (x, y, w, h, rows) => {
    ctx.fillStyle = '#5a3a22'; ctx.fillRect(x, y, w, h);
    const rh = h / rows;
    for (let j = 0; j < rows; j++){
      let bx = x + 8;
      while (bx < x + w - 14){ const bw = 7 + r() * 12, bh = rh * (0.6 + r() * 0.32); ctx.fillStyle = ['#8c2f2f', '#2f5d7c', '#d8b25a', '#3f6b3f', '#6b4a8a', '#c4693a', '#e8e0cc', '#2a4a4a'][Math.floor(r() * 8)]; ctx.fillRect(bx, y + j * rh + rh - bh - 6, bw, bh); bx += bw + 1.5; }
      ctx.fillStyle = '#3e2716'; ctx.fillRect(x, y + j * rh + rh - 6, w, 6);
    }
    ctx.strokeStyle = '#3e2716'; ctx.lineWidth = 8; ctx.strokeRect(x, y, w, h);
  };
  const ridge = (y, amp, col, seed) => { ctx.fillStyle = col; ctx.beginPath(); ctx.moveTo(0, H); for (let x = 0; x <= W; x += 16) ctx.lineTo(x, y - amp * (0.5 + 0.5 * Math.sin(x * 0.006 + seed) * Math.cos(x * 0.013 + seed * 2))); ctx.lineTo(W, H); ctx.closePath(); ctx.fill(); };
  const sign = (text, x, y, w, h, bg, fg, font) => { ctx.fillStyle = bg; ctx.fillRect(x - w / 2, y - h / 2, w, h); ctx.fillStyle = fg; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; fit(ctx, text, font || F.ui, '700', h * 0.56, w * 0.88); ctx.fillText(text, x, y + 2); };
  switch (kind){
    case 'library': {
      ctx.fillStyle = grad(0, H, [[0, '#d9c7a4'], [1, '#b89c74']]); ctx.fillRect(0, 0, W, H);
      shelves(30, H * 0.18, 300, H * 0.78, 6); shelves(W - 330, H * 0.18, 300, H * 0.78, 6);
      ctx.fillStyle = '#e8f1f5'; ctx.fillRect(400, H * 0.16, 224, H * 0.42); ctx.fillStyle = grad(H * 0.16, H * 0.58, [[0, '#9cc9e4'], [1, '#d9eef7']]); ctx.fillRect(410, H * 0.17, 204, H * 0.4);
      ctx.fillStyle = '#7da35d'; ctx.beginPath(); ctx.ellipse(470, H * 0.55, 90, 40, 0, Math.PI, 0); ctx.fill(); ctx.strokeStyle = '#efe7d5'; ctx.lineWidth = 10; ctx.strokeRect(405, H * 0.165, 214, H * 0.41); ctx.beginPath(); ctx.moveTo(512, H * 0.165); ctx.lineTo(512, H * 0.575); ctx.stroke();
      sign('VR STATION · TRY IT TODAY', W / 2, H * 0.08, 520, 54, '#1d3b52', '#f2c14e');
      vignette(0.35); break;
    }
    case 'calmap': {
      ctx.fillStyle = grad(0, H, [[0, '#13283c'], [1, '#0c1824']]); ctx.fillRect(0, 0, W, H);
      ctx.strokeStyle = 'rgba(255,255,255,0.05)'; for (let x = 0; x < W; x += 40){ ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
      /* California, roughly: the 3D lights sit on top of this outline */
      ctx.save(); ctx.translate(W * 0.5, H * 0.52); ctx.scale(H / 640, H / 640);
      ctx.fillStyle = '#e9dcc0'; ctx.strokeStyle = '#cda961'; ctx.lineWidth = 4;
      ctx.beginPath(); const P = WAX_CA; ctx.moveTo(P[0][0], P[0][1]); for (const p of P) ctx.lineTo(p[0], p[1]); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.restore();
      ctx.fillStyle = '#f2c14e'; ctx.font = '700 44px ' + F.display; ctx.textAlign = 'left'; ctx.fillText('VR stations across California', 40, 70);
      ctx.fillStyle = 'rgba(239,231,213,0.8)'; ctx.font = '400 26px ' + F.type; ctx.fillText('MORE THAN 90 LIBRARIES · 2017', 42, 112);
      vignette(0.3); break;
    }
    case 'storyroom': {
      ctx.fillStyle = grad(0, H, [[0, '#24315e'], [0.7, '#3a4f8a'], [1, '#5a6eae']]); ctx.fillRect(0, 0, W, H);
      for (let i = 0; i < 70; i++){ const x = r() * W, y = r() * H * 0.6, s = 1 + r() * 3; ctx.fillStyle = 'rgba(255,240,200,' + (0.4 + r() * 0.6) + ')'; ctx.beginPath(); ctx.arc(x, y, s, 0, Math.PI * 2); ctx.fill(); }
      ctx.fillStyle = '#f7e7b0'; ctx.beginPath(); ctx.arc(W * 0.8, H * 0.2, 60, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = '#24315e'; ctx.beginPath(); ctx.arc(W * 0.8 + 26, H * 0.2 - 12, 54, 0, Math.PI * 2); ctx.fill();
      ridge(H * 0.78, 50, '#2c6b5a', 1); ridge(H * 0.86, 30, '#3f8a6a', 3);
      shelves(40, H * 0.55, 220, H * 0.42, 3);
      sign('STORY TIME', W * 0.5, H * 0.1, 360, 64, '#f2c14e', '#24315e', F.display);
      vignette(0.3); break;
    }
    case 'reopening': {
      ctx.fillStyle = grad(0, H, [[0, '#e2d6bf'], [1, '#c9b48e']]); ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = grad(H * 0.15, H * 0.6, [[0, '#8fb9d6'], [1, '#e8d2b0']]); for (const x of [90, 380, 670]) ctx.fillRect(x, H * 0.18, 260, H * 0.42);
      for (const x of [90, 380, 670]){ ctx.fillStyle = '#a08a6a'; ctx.beginPath(); ctx.moveTo(x, H * 0.6); for (let k = 0; k <= 260; k += 20) ctx.lineTo(x + k, H * 0.5 - 40 * Math.abs(Math.sin(k * 0.02 + x))); ctx.lineTo(x + 260, H * 0.6); ctx.fill(); ctx.strokeStyle = '#efe7d5'; ctx.lineWidth = 10; ctx.strokeRect(x, H * 0.18, 260, H * 0.42); }
      sign('GRAND RE-OPENING', W / 2, H * 0.08, 600, 70, '#9a2f33', '#fff4e0', F.display);
      for (let i = 0; i < 14; i++){ const x = 40 + r() * (W - 80), y = H * 0.66 + r() * H * 0.1, col = ['#e63946', '#f2c14e', '#2a9d8f', '#3b6ea8', '#f4a261'][i % 5]; ctx.strokeStyle = 'rgba(80,60,40,0.5)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(x, y + 30); ctx.lineTo(x + (r() - 0.5) * 30, H); ctx.stroke(); ctx.fillStyle = col; ctx.beginPath(); ctx.ellipse(x, y, 24, 30, 0, 0, Math.PI * 2); ctx.fill(); }
      vignette(0.28); break;
    }
    case 'shelter': {
      ctx.fillStyle = '#c9c3b6'; ctx.fillRect(0, 0, W, H);
      for (let y = 0; y < H; y += 34) for (let x = (y / 34) % 2 ? -40 : 0; x < W; x += 80){ ctx.strokeStyle = 'rgba(80,72,60,0.35)'; ctx.lineWidth = 2; ctx.strokeRect(x, y, 80, 34); }
      ctx.fillStyle = '#1d4e89'; ctx.fillRect(0, H * 0.72, W, 10);
      ctx.fillStyle = '#efe9dc'; ctx.fillRect(W * 0.5 - 90, H * 0.12, 180, 120); ctx.strokeStyle = '#c0392b'; ctx.lineWidth = 6; ctx.strokeRect(W * 0.5 - 50, H * 0.12 + 50, 100, 70);
      ctx.strokeStyle = '#e67e22'; ctx.lineWidth = 7; ctx.beginPath(); ctx.ellipse(W * 0.5, H * 0.12 + 136, 46, 12, 0, 0, Math.PI * 2); ctx.stroke();
      sign('WELCOME · COMMUNITY CENTER', W * 0.5, H * 0.04 + 6, 560, 48, '#2f5d7c', '#fff', F.ui);
      for (let k = 0; k < 6; k++){ ctx.fillStyle = '#6b7178'; ctx.fillRect(40 + k * 12, H * 0.5 + k * 8, 120, 10); ctx.fillRect(40 + k * 12, H * 0.5 + k * 8, 8, 120); }
      vignette(0.3); break;
    }
    case 'catalog': {
      ctx.fillStyle = grad(0, H, [[0, '#d3cbb8'], [1, '#b7ab92']]); ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = '#2a4258'; ctx.fillRect(W * 0.42, H * 0.12, W * 0.52, H * 0.46);
      ctx.strokeStyle = 'rgba(205,230,255,0.25)'; ctx.lineWidth = 1.5;
      for (let i = 1; i < 8; i++){ ctx.beginPath(); ctx.moveTo(W * 0.42, H * 0.12 + i * H * 0.0575); ctx.lineTo(W * 0.94, H * 0.12 + i * H * 0.0575); ctx.stroke(); }
      ctx.fillStyle = '#7fa37a';
      for (const [x, y, w, h] of [[0.48, 0.2, 0.12, 0.12], [0.53, 0.33, 0.06, 0.14], [0.66, 0.18, 0.18, 0.14], [0.72, 0.33, 0.06, 0.08], [0.82, 0.36, 0.07, 0.07]]){ ctx.beginPath(); ctx.ellipse(W * (x + w / 2), H * (y + h / 2), W * w / 2, H * h / 2, 0.3, 0, Math.PI * 2); ctx.fill(); }
      sign('A CATALOG FOR THE WORLD’S LIBRARIES', W * 0.68, H * 0.07, 520, 44, '#5e1a22', '#f4e9d4');
      for (let i = 0; i < 5; i++) for (let j = 0; j < 7; j++){ ctx.fillStyle = (i + j) % 2 ? '#7a5032' : '#86593a'; ctx.fillRect(40 + i * 64, H * 0.2 + j * 56, 60, 52); ctx.fillStyle = '#d9b56c'; ctx.fillRect(40 + i * 64 + 22, H * 0.2 + j * 56 + 22, 16, 6); ctx.fillStyle = '#efe7d5'; ctx.fillRect(40 + i * 64 + 18, H * 0.2 + j * 56 + 8, 24, 10); }
      vignette(0.3); break;
    }
    case 'farm': {
      ctx.fillStyle = grad(0, H * 0.6, [[0, '#7fb3e0'], [1, '#f2dcae']]); ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = 'rgba(255,255,255,0.8)'; for (const [x, y] of [[180, 90], [640, 60], [860, 120]]){ for (let k = 0; k < 5; k++){ ctx.beginPath(); ctx.ellipse(x + k * 34, y + (k % 2) * 10, 42, 22, 0, 0, Math.PI * 2); ctx.fill(); } }
      ridge(H * 0.56, 70, '#c9a660', 0.5); ridge(H * 0.66, 40, '#b39048', 2.1);
      ctx.fillStyle = '#9b2f2a'; ctx.fillRect(W * 0.62, H * 0.38, 230, 180); ctx.beginPath(); ctx.moveTo(W * 0.62 - 20, H * 0.38); ctx.lineTo(W * 0.62 + 115, H * 0.38 - 90); ctx.lineTo(W * 0.62 + 250, H * 0.38); ctx.fill();
      ctx.fillStyle = '#f2ead8'; ctx.fillRect(W * 0.62 + 80, H * 0.38 + 80, 70, 100); ctx.strokeStyle = '#f2ead8'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(W * 0.62 + 80, H * 0.38 + 80); ctx.lineTo(W * 0.62 + 150, H * 0.38 + 180); ctx.moveTo(W * 0.62 + 150, H * 0.38 + 80); ctx.lineTo(W * 0.62 + 80, H * 0.38 + 180); ctx.stroke();
      ctx.fillStyle = '#7a9a48'; ctx.fillRect(0, H * 0.74, W, H * 0.26);
      ctx.fillStyle = '#5a3a22'; for (let x = 0; x < W; x += 90){ ctx.fillRect(x, H * 0.66, 10, 90); } ctx.fillRect(0, H * 0.69, W, 8); ctx.fillRect(0, H * 0.76, W, 8);
      vignette(0.22); break;
    }
    case 'careers': {
      ctx.fillStyle = grad(0, H, [[0, '#dfe3e6'], [1, '#c4cad0']]); ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = grad(H * 0.12, H * 0.62, [[0, '#86b4d9'], [0.7, '#e8c9a0'], [1, '#d4a574']]); ctx.fillRect(60, H * 0.12, W - 120, H * 0.5);
      ctx.fillStyle = '#b07a5a'; ctx.beginPath(); ctx.moveTo(60, H * 0.62); for (let x = 60; x <= W - 60; x += 20) ctx.lineTo(x, H * 0.48 - 60 * Math.abs(Math.sin(x * 0.008 + 1)) - 20 * Math.sin(x * 0.03)); ctx.lineTo(W - 60, H * 0.62); ctx.fill();
      ctx.strokeStyle = '#eef1f3'; ctx.lineWidth = 12; ctx.strokeRect(60, H * 0.12, W - 120, H * 0.5); for (const x of [W * 0.36, W * 0.64]){ ctx.beginPath(); ctx.moveTo(x, H * 0.12); ctx.lineTo(x, H * 0.62); ctx.stroke(); }
      sign('CAREER EXPLORATION LAB', W / 2, H * 0.06, 520, 50, '#1d3b52', '#ffffff');
      const icons = ['TRADES', 'HEALTHCARE', 'IT', 'MANUFACTURING', 'LOGISTICS'];
      icons.forEach((t, i) => { const x = 110 + i * ((W - 220) / 4); ctx.fillStyle = ['#e07b2a', '#c0392b', '#2a9d8f', '#3b6ea8', '#6a4a8a'][i]; ctx.beginPath(); ctx.arc(x, H * 0.74, 34, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = '#2b2b2b'; ctx.font = '700 20px ' + F.ui; ctx.textAlign = 'center'; ctx.fillText(t, x, H * 0.74 + 62); });
      vignette(0.25); break;
    }
    case 'forest360': {
      ctx.fillStyle = grad(0, H, [[0, '#d8dee2'], [1, '#bfc6cc']]); ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = grad(H * 0.1, H * 0.7, [[0, '#9ec4dd'], [1, '#dfe9ee']]); ctx.fillRect(80, H * 0.1, W - 160, H * 0.6);
      ctx.fillStyle = '#f4f7f9'; ctx.beginPath(); ctx.moveTo(W * 0.45, H * 0.45); ctx.lineTo(W * 0.62, H * 0.18); ctx.lineTo(W * 0.8, H * 0.45); ctx.fill();
      ctx.fillStyle = '#8fa3b3'; ctx.beginPath(); ctx.moveTo(W * 0.45, H * 0.45); ctx.lineTo(W * 0.56, H * 0.3); ctx.lineTo(W * 0.62, H * 0.36); ctx.lineTo(W * 0.69, H * 0.28); ctx.lineTo(W * 0.8, H * 0.45); ctx.fill();
      for (let i = 0; i < 26; i++){ const x = 80 + r() * (W - 160), h = 80 + r() * 130, y = H * 0.7; ctx.fillStyle = r() > 0.5 ? '#21452f' : '#2c5a3b'; ctx.beginPath(); ctx.moveTo(x, y - h); ctx.lineTo(x - h * 0.22, y); ctx.lineTo(x + h * 0.22, y); ctx.fill(); }
      ctx.strokeStyle = '#eef1f3'; ctx.lineWidth = 14; ctx.strokeRect(80, H * 0.1, W - 160, H * 0.6);
      vignette(0.25); break;
    }
    case 'shipyard': {
      ctx.fillStyle = grad(0, H * 0.7, [[0, '#2b2d52'], [0.55, '#c0605a'], [1, '#f2b26b']]); ctx.fillRect(0, 0, W, H);
      ridge(H * 0.6, 70, '#3d3048', 1.4);
      ctx.fillStyle = '#26202c';
      for (const x of [130, 520, 860]){ ctx.fillRect(x, H * 0.18, 18, H * 0.48); ctx.fillRect(x - 90, H * 0.18, 220, 14); ctx.beginPath(); ctx.moveTo(x + 9, H * 0.18); ctx.lineTo(x + 120, H * 0.18 + 14); ctx.lineTo(x + 9, H * 0.3); ctx.fill(); ctx.strokeStyle = '#26202c'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x - 70, H * 0.18 + 14); ctx.lineTo(x - 70, H * 0.36); ctx.stroke(); }
      ctx.fillStyle = '#332a36'; ctx.beginPath(); ctx.moveTo(220, H * 0.58); ctx.lineTo(820, H * 0.58); ctx.lineTo(780, H * 0.7); ctx.lineTo(260, H * 0.7); ctx.fill(); ctx.fillRect(420, H * 0.48, 120, H * 0.1);
      ctx.fillStyle = '#1f2a3a'; ctx.fillRect(0, H * 0.7, W, H * 0.3);
      ctx.fillStyle = 'rgba(242,178,107,0.35)'; for (let i = 0; i < 40; i++) ctx.fillRect(r() * W, H * 0.72 + r() * H * 0.25, 40 + r() * 80, 2);
      ctx.fillStyle = 'rgba(255,220,170,0.85)'; ctx.font = '700 30px ' + F.type; ctx.textAlign = 'left'; ctx.fillText('WORLD WAR II SHIPYARDS · MARIN CITY', 36, 52);
      vignette(0.3); break;
    }
    case 'vrgallery': {
      ctx.fillStyle = grad(0, H, [[0, '#090b18'], [1, '#1a1f3d']]); ctx.fillRect(0, 0, W, H);
      ctx.strokeStyle = 'rgba(120,160,255,0.22)'; ctx.lineWidth = 1.5;
      for (let i = -12; i <= 12; i++){ ctx.beginPath(); ctx.moveTo(W / 2 + i * 22, H * 0.62); ctx.lineTo(W / 2 + i * 120, H); ctx.stroke(); }
      for (let k = 0; k < 8; k++){ const y = H * 0.62 + Math.pow(k / 8, 1.8) * H * 0.38; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
      for (let i = 0; i < 9; i++){ const x = 70 + i * 110, y = H * 0.22 + (i % 2) * 30; ctx.fillStyle = 'rgba(255,240,210,0.08)'; ctx.fillRect(x - 6, y - 6, 92, 116); ctx.strokeStyle = 'rgba(255,230,180,0.5)'; ctx.lineWidth = 2; ctx.strokeRect(x, y, 80, 104); }
      ctx.fillStyle = 'rgba(160,190,255,0.85)'; ctx.font = '700 28px ' + F.type; ctx.textAlign = 'center'; ctx.fillText('A SHARED WORLD IN THE BROWSER', W / 2, 52);
      break;
    }
    case 'fair': {
      ctx.fillStyle = grad(0, H * 0.75, [[0, '#2c3e6b'], [0.6, '#e08a5a'], [1, '#f6c27a']]); ctx.fillRect(0, 0, W, H);
      ctx.strokeStyle = '#2b2233'; ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(W * 0.78, H * 0.38, 170, 0, Math.PI * 2); ctx.stroke();
      for (let i = 0; i < 12; i++){ const a = i / 12 * Math.PI * 2; ctx.beginPath(); ctx.moveTo(W * 0.78, H * 0.38); ctx.lineTo(W * 0.78 + Math.cos(a) * 170, H * 0.38 + Math.sin(a) * 170); ctx.stroke(); ctx.fillStyle = '#2b2233'; ctx.fillRect(W * 0.78 + Math.cos(a) * 170 - 12, H * 0.38 + Math.sin(a) * 170, 24, 18); }
      ctx.beginPath(); ctx.moveTo(W * 0.78, H * 0.38); ctx.lineTo(W * 0.7, H * 0.8); ctx.moveTo(W * 0.78, H * 0.38); ctx.lineTo(W * 0.86, H * 0.8); ctx.stroke();
      for (const [x, col] of [[120, '#c0392b'], [330, '#2a9d8f'], [520, '#f2c14e']]){ ctx.fillStyle = col; ctx.beginPath(); ctx.moveTo(x - 110, H * 0.62); ctx.lineTo(x, H * 0.44); ctx.lineTo(x + 110, H * 0.62); ctx.fill(); ctx.fillStyle = '#f4ead8'; ctx.fillRect(x - 100, H * 0.62, 200, H * 0.16); for (let k = 0; k < 5; k++){ ctx.fillStyle = col; ctx.fillRect(x - 100 + k * 40, H * 0.62, 20, H * 0.16); } }
      ctx.strokeStyle = 'rgba(40,30,40,0.6)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(0, H * 0.12); ctx.quadraticCurveTo(W / 2, H * 0.26, W, H * 0.12); ctx.stroke();
      for (let i = 0; i <= 20; i++){ const t = i / 20, x = t * W, y = H * 0.12 + Math.sin(t * Math.PI) * H * 0.14 * 0.5 * 2 * 0.5; ctx.fillStyle = ['#ffd27a', '#ff8a7a', '#9de1ff'][i % 3]; ctx.beginPath(); ctx.arc(x, y + 4, 7, 0, Math.PI * 2); ctx.fill(); }
      ctx.fillStyle = '#6d8d3e'; ctx.fillRect(0, H * 0.78, W, H * 0.22);
      ctx.fillStyle = 'rgba(255,235,200,0.95)'; ctx.font = '700 30px ' + F.type; ctx.textAlign = 'left'; ctx.fillText('MARIN COUNTY FAIR · 2025', 34, 50);
      vignette(0.22); break;
    }
    default: ctx.fillStyle = '#3a2a2a'; ctx.fillRect(0, 0, W, H);
  }
  return c;
}
/* A rough outline of California for the statewide map, in backdrop pixels around its centre */
const WAX_CA = [[-190, -258], [-10, -258], [-10, -52], [196, 140], [206, 196], [178, 228], [168, 262], [52, 262], [30, 226], [-34, 188], [-90, 150], [-124, 104], [-152, 46], [-178, -10], [-190, -72], [-214, -160], [-208, -222]];
