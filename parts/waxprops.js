/* ================================================================
   Living History: props for the scenes (furniture, screens, holograms)
   All sizes in metres, in a stage's local frame.
   ================================================================ */
const WP = {};
/* Screens drawn once and shown on monitors, laptops and tablets */
function waxScreen(kind, w, h){
  w = w || 512; h = h || 320;
  const c = mk(w, h), ctx = c.getContext('2d'), r = rnd(kind.length * 7 + 3);
  const g = (y0, y1, a, b) => { const q = ctx.createLinearGradient(0, y0, 0, y1); q.addColorStop(0, a); q.addColorStop(1, b); return q; };
  switch (kind){
    case 'reef':
      ctx.fillStyle = g(0, h, '#1e6fa0', '#0a2a48'); ctx.fillRect(0, 0, w, h);
      for (let i = 0; i < 9; i++){ const x = r() * w, y = h * 0.2 + r() * h * 0.6, s = 10 + r() * 16; ctx.fillStyle = ['#f2a65a', '#f2e14e', '#7ad3f2', '#f27a9a'][i % 4]; ctx.beginPath(); ctx.ellipse(x, y, s, s * 0.5, 0, 0, Math.PI * 2); ctx.fill(); ctx.beginPath(); ctx.moveTo(x - s, y); ctx.lineTo(x - s * 1.6, y - s * 0.5); ctx.lineTo(x - s * 1.6, y + s * 0.5); ctx.fill(); }
      ctx.fillStyle = '#c96a4a'; for (let i = 0; i < 12; i++){ ctx.beginPath(); ctx.ellipse(r() * w, h - 8, 14 + r() * 20, 30 + r() * 30, 0, Math.PI, 0); ctx.fill(); }
      break;
    case 'marc': {
      ctx.fillStyle = '#f6f3ea'; ctx.fillRect(0, 0, w, h); ctx.fillStyle = '#1d3b52'; ctx.fillRect(0, 0, w, 34);
      ctx.fillStyle = '#fff'; ctx.font = '700 18px ' + F.type; ctx.fillText('CATALOG RECORD · VR', 14, 23);
      ctx.font = '400 15px ' + F.type; ctx.fillStyle = '#2b2419';
      ['245 10 $a Human heart : $b interactive 3D model', '256    $a Computer data (VR)', '300    $a 1 online resource', '538    $a Requires VR headset', '650  0 $a Anatomy $v Interactive', '655  4 $a Virtual reality'].forEach((l, i) => ctx.fillText(l, 14, 66 + i * 30));
      break;
    }
    case 'panorama': {
      ctx.fillStyle = g(0, h * 0.55, '#9cc6e2', '#e6eef2'); ctx.fillRect(0, 0, w, h);
      ctx.fillStyle = '#7f95a6'; ctx.beginPath(); ctx.moveTo(0, h * 0.55); for (let x = 0; x <= w; x += 16) ctx.lineTo(x, h * 0.42 - 30 * Math.abs(Math.sin(x * 0.012))); ctx.lineTo(w, h * 0.55); ctx.fill();
      for (let i = 0; i < 40; i++){ const x = r() * w, s = 20 + r() * 40; ctx.fillStyle = r() > 0.5 ? '#24482f' : '#2f5a3c'; ctx.beginPath(); ctx.moveTo(x, h * 0.62 - s); ctx.lineTo(x - s * 0.25, h * 0.62); ctx.lineTo(x + s * 0.25, h * 0.62); ctx.fill(); }
      ctx.fillStyle = '#5a7f9a'; ctx.fillRect(0, h * 0.62, w, h * 0.12); ctx.fillStyle = '#6b8a4a'; ctx.fillRect(0, h * 0.74, w, h * 0.26);
      break;
    }
    case 'farm360': {
      ctx.fillStyle = g(0, h * 0.5, '#8ec1e8', '#f0dcb0'); ctx.fillRect(0, 0, w, h);
      ctx.fillStyle = '#c9a660'; ctx.fillRect(0, h * 0.5, w, h * 0.5);
      ctx.fillStyle = '#9b2f2a'; ctx.fillRect(w * 0.3, h * 0.3, 90, 70); ctx.beginPath(); ctx.moveTo(w * 0.3 - 8, h * 0.3); ctx.lineTo(w * 0.3 + 45, h * 0.3 - 34); ctx.lineTo(w * 0.3 + 98, h * 0.3); ctx.fill();
      ctx.fillStyle = 'rgba(255,255,255,0.85)'; ctx.font = '700 16px ' + F.type; ctx.fillText('360° · FAMILY FARM', 12, 22);
      break;
    }
    case 'career': {
      ctx.fillStyle = '#0f2233'; ctx.fillRect(0, 0, w, h);
      ctx.fillStyle = '#63e2ff'; ctx.font = '700 22px ' + F.ui; ctx.fillText('Patient Care · Module 3', 16, 34);
      ctx.fillStyle = 'rgba(99,226,255,0.25)'; ctx.fillRect(16, 52, w - 32, 12); ctx.fillStyle = '#63e2ff'; ctx.fillRect(16, 52, (w - 32) * 0.7, 12);
      ctx.font = '400 17px ' + F.ui; ctx.fillStyle = '#d8f6ff'; ['✓ Check the machine', '✓ Prime the lines', '◻ Monitor the patient'].forEach((l, i) => ctx.fillText(l, 16, 100 + i * 30));
      break;
    }
    case 'gallery': {
      ctx.fillStyle = '#0b0d1a'; ctx.fillRect(0, 0, w, h);
      for (let i = 0; i < 5; i++){ const x = 20 + i * (w - 40) / 5; ctx.fillStyle = 'rgba(255,240,210,0.9)'; ctx.fillRect(x, h * 0.25, (w - 40) / 5 - 14, h * 0.45); ctx.fillStyle = ['#3b6ea8', '#f2c14e', '#c0392b', '#2a9d8f', '#6a4a8a'][i]; ctx.fillRect(x + 8, h * 0.25 + 8, (w - 40) / 5 - 30, h * 0.45 - 16); }
      break;
    }
    case 'model': {
      ctx.fillStyle = '#20262e'; ctx.fillRect(0, 0, w, h);
      ctx.strokeStyle = '#7ad3f2'; ctx.lineWidth = 2;
      for (let i = 0; i < 9; i++){ ctx.beginPath(); ctx.ellipse(w / 2, h * 0.55, 40 + i * 18, 14 + i * 5, 0, Math.PI, Math.PI * 2); ctx.stroke(); }
      ctx.fillStyle = '#7ad3f2'; ctx.font = '700 16px ' + F.type; ctx.fillText('SHIP HULL · VR MODEL', 12, 22);
      break;
    }
    case 'ar': {
      ctx.fillStyle = g(0, h, '#8fc06a', '#5a8a3a'); ctx.fillRect(0, 0, w, h);
      for (let i = 0; i < 6; i++){ const x = 30 + r() * (w - 60), y = h * 0.3 + r() * h * 0.5; ctx.fillStyle = ['#f2c14e', '#e76f51', '#c77dff'][i % 3]; for (let k = 0; k < 5; k++){ const a = k / 5 * Math.PI * 2; ctx.beginPath(); ctx.ellipse(x + Math.cos(a) * 8, y + Math.sin(a) * 8, 7, 4, a, 0, Math.PI * 2); ctx.fill(); } }
      ctx.fillStyle = '#f08a24'; ctx.beginPath(); ctx.ellipse(w * 0.6, h * 0.3, 18, 10, 0.4, 0, Math.PI * 2); ctx.fill(); ctx.beginPath(); ctx.ellipse(w * 0.6 + 18, h * 0.3 - 4, 18, 10, -0.4, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,0.8)'; ctx.lineWidth = 3; ctx.strokeRect(10, 10, w - 20, h - 20);
      break;
    }
    default: ctx.fillStyle = '#20262e'; ctx.fillRect(0, 0, w, h);
  }
  return c;
}
const _scr = {};
function waxScreenMat(kind){ if (!_scr[kind]) _scr[kind] = new THREE.MeshBasicMaterial({ map:tex(waxScreen(kind)), toneMapped:false }); return _scr[kind]; }

WP.desk = (S, x, z, w, d, h, ry, mat) => {
  const m = waxM(), g = S.grp(x, 0, z, ry || 0);
  S.box(w, 0.04, d, mat || m.wood, 0, h - 0.02, 0, 0, g);
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) S.box(0.04, h - 0.04, 0.04, m.dark, sx * (w / 2 - 0.05), (h - 0.04) / 2, sz * (d / 2 - 0.05), 0, g);
  return g;
};
WP.screen = (S, parent, x, y, z, ry, kind, w, h) => {
  const m = waxM(), g = S.grp(x, y, z, ry || 0, parent);
  S.box(w + 0.04, h + 0.04, 0.03, m.black, 0, h / 2 + 0.12, 0, 0, g);
  S.plane(w, h, waxScreenMat(kind), 0, h / 2 + 0.12, 0.016, 0, 0, g);
  S.box(0.05, 0.12, 0.04, m.black, 0, 0.06, -0.01, 0, g); S.box(0.22, 0.015, 0.16, m.black, 0, 0.007, 0, 0, g);
  return g;
};
WP.pc = (S, x, z, ry) => { const m = waxM(), g = S.grp(x, 0, z, ry || 0); S.box(0.2, 0.44, 0.44, m.black, 0, 0.22, 0, 0, g); S.box(0.02, 0.02, 0.01, m.glow, 0.05, 0.38, 0.222, 0, g); return g; };
WP.chair = (S, x, z, ry, h, mat) => {
  const m = waxM(), g = S.grp(x, 0, z, ry || 0), sh = h || 0.45;
  S.box(0.44, 0.04, 0.42, mat || m.wood, 0, sh, 0, 0, g); S.box(0.44, 0.42, 0.04, mat || m.wood, 0, sh + 0.23, -0.2, 0, g);
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) S.box(0.035, sh, 0.035, m.dark, sx * 0.19, sh / 2, sz * 0.18, 0, g);
  return g;
};
WP.crate = (S, x, z, ry, label, w, h, d) => {
  const m = waxM(), g = S.grp(x, 0, z, ry || 0); w = w || 0.7; h = h || 0.5; d = d || 0.5;
  S.box(w, h, d, m.pale, 0, h / 2, 0, 0, g);
  for (const yy of [0.04, h - 0.04]) S.box(w + 0.01, 0.05, d + 0.01, m.wood, 0, yy, 0, 0, g);
  if (label){ const c = mk(256, 96), ctx = c.getContext('2d'); ctx.fillStyle = '#efe4c8'; ctx.fillRect(0, 0, 256, 96); ctx.fillStyle = '#2b2419'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; fit(ctx, label, F.type, '700', 34, 236); ctx.fillText(label, 128, 50); S.plane(w * 0.7, w * 0.26, new THREE.MeshStandardMaterial({ map:tex(c), roughness:0.9 }), 0, h * 0.55, d / 2 + 0.003, 0, 0, g); }
  return g;
};
WP.mat = (S, x, z, r) => {
  const m = waxM(), g = S.grp(x, 0.004, z, 0, S.anim);
  const ring = new THREE.Mesh(new THREE.RingGeometry(r - 0.025, r, 48), m.holo); ring.rotation.x = -Math.PI / 2; ring.position.y = 0.01; g.add(ring);
  const pad = new THREE.Mesh(new THREE.CircleGeometry(r, 40), stdMat(0x2b3138, 0.9)); pad.rotation.x = -Math.PI / 2; g.add(pad);
  return g;
};
WP.bookcase = (S, x, z, w, h, ry) => {
  const m = waxM(), g = S.grp(x, 0, z, ry || 0), rows = Math.round(h / 0.36), r = rnd(Math.round(x * 100 + z * 10));
  S.box(w, h, 0.3, m.dark, 0, h / 2, -0.02, 0, g);
  const bb = new BoxBatch();
  for (let j = 0; j < rows; j++){
    let bx = -w / 2 + 0.05;
    while (bx < w / 2 - 0.08){ const bw = 0.025 + r() * 0.04, bh = 0.2 + r() * 0.1; bb.add(bx + bw / 2, 0.06 + j * (h / rows) + bh / 2, 0.06, bw, bh, 0.2, 0, 0, ['#8c2f2f', '#2f5d7c', '#d8b25a', '#3f6b3f', '#6b4a8a', '#c4693a', '#e8e0cc'][Math.floor(r() * 7)]); bx += bw + 0.004; }
  }
  const mesh = bb.build(new THREE.MeshStandardMaterial({ roughness:0.8 }), true);
  if (mesh){ scene.remove(mesh); g.add(mesh); }
  return g;
};
/* Small fish that swim around a headset wearer: what they see, shown to everyone */
WP.fish = (S, n) => {
  const out = [], body = new THREE.SphereGeometry(0.05, 10, 8), tail = new THREE.ConeGeometry(0.035, 0.06, 4);
  const cols = [0xf2a65a, 0xf2e14e, 0x7ad3f2, 0xf27a9a, 0x9df0ff];
  for (let i = 0; i < n; i++){
    const g = new THREE.Group(), mat = new THREE.MeshBasicMaterial({ color:cols[i % cols.length], transparent:true, opacity:0.85, toneMapped:false });
    const b = new THREE.Mesh(body, mat); b.scale.set(1.6, 0.8, 0.5); g.add(b);
    const t = new THREE.Mesh(tail, mat); t.rotation.z = Math.PI / 2; t.position.x = -0.1; g.add(t);
    g.visible = false; S.anim.add(g); out.push(g);
  }
  return out;
};
WP.swim = (fish, t, t0, t1, cx, cy, cz, rad) => {
  const on = t > t0 && t < t1, k = on ? Math.min(1, (t - t0) / 0.6, (t1 - t) / 0.6) : 0;
  fish.forEach((f, i) => {
    f.visible = k > 0.01; if (!f.visible) return;
    const a = t * (0.7 + i * 0.07) + i * 1.3, rr = rad * (0.75 + 0.25 * Math.sin(i * 2.1)), y = cy + 0.25 * Math.sin(t * 0.9 + i);
    f.position.set(cx + Math.cos(a) * rr, y, cz + Math.sin(a) * rr);
    f.rotation.y = -a - Math.PI / 2 * (i % 2 ? 1 : 1); f.scale.setScalar(k * (0.8 + 0.3 * (i % 3) / 2));
  });
};
/* Holograms are drawn as glowing cyan wireframes */
WP.wire = (S, geo, parent) => {
  const m = waxM(), g = new THREE.Group();
  const fill = new THREE.Mesh(geo, m.holo.clone()); fill.material.opacity = 0.16; g.add(fill);
  const line = new THREE.LineSegments(new THREE.EdgesGeometry(geo, 25), m.holoLine); g.add(line);
  (parent || S.anim).add(g); return g;
};
WP.butterfly = (S) => {
  const g = new THREE.Group(), wingC = mk(128, 128), ctx = wingC.getContext('2d');
  ctx.fillStyle = '#f08a24'; ctx.beginPath(); ctx.ellipse(64, 50, 54, 44, 0.3, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = '#1a1210'; ctx.lineWidth = 8; ctx.stroke(); ctx.lineWidth = 3; for (let i = 0; i < 4; i++){ ctx.beginPath(); ctx.moveTo(14, 64); ctx.lineTo(70 + i * 12, 14 + i * 20); ctx.stroke(); }
  ctx.fillStyle = '#fff'; for (let i = 0; i < 6; i++){ ctx.beginPath(); ctx.arc(30 + i * 15, 92 - Math.abs(i - 2.5) * 6, 3, 0, Math.PI * 2); ctx.fill(); }
  const mat = new THREE.MeshBasicMaterial({ map:tex(wingC), transparent:true, alphaTest:0.3, side:THREE.DoubleSide, toneMapped:false });
  for (const s of [-1, 1]){ const w = new THREE.Mesh(new THREE.PlaneGeometry(0.09, 0.09), mat); w.geometry.translate(0.045, 0, 0); w.scale.x = s; w.rotation.x = -Math.PI / 2; const pivot = new THREE.Group(); pivot.add(w); g.add(pivot); g.userData[s > 0 ? 'r' : 'l'] = pivot; }
  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, 0.06, 6), new THREE.MeshBasicMaterial({ color:0x1a1210 })); body.rotation.x = Math.PI / 2; g.add(body);
  S.anim.add(g); return g;
};
WP.flower = (S, x, z, col, h) => {
  const g = S.grp(x, 0, z, 0, S.anim), stem = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.008, h, 5), stdMat(0x3f7a3a, 0.8)); stem.position.y = h / 2; g.add(stem);
  const head = new THREE.Group(); head.position.y = h; g.add(head);
  const pm = stdMat(col, 0.6);
  for (let k = 0; k < 6; k++){ const p = new THREE.Mesh(new THREE.SphereGeometry(0.035, 8, 6), pm); const a = k / 6 * Math.PI * 2; p.position.set(Math.cos(a) * 0.035, 0, Math.sin(a) * 0.035); p.scale.set(1, 0.35, 0.6); p.rotation.y = -a; head.add(p); }
  const c = new THREE.Mesh(new THREE.SphereGeometry(0.022, 8, 6), stdMat(0x5a3a1a, 0.7)); c.scale.y = 0.6; head.add(c);
  for (let k = 0; k < 2; k++){ const lf = new THREE.Mesh(new THREE.SphereGeometry(0.04, 6, 4), stdMat(0x4a8a3a, 0.8)); lf.scale.set(1, 0.2, 0.45); lf.position.set(k ? 0.03 : -0.03, h * 0.4, 0); lf.rotation.z = k ? -0.5 : 0.5; g.add(lf); }
  return g;
};
