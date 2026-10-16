/* ================================================================
   Room 103: blueprint boards, the blueprint viewer and the model bench
   ================================================================ */
const BP_PLACE = {
  car:{ x:14.45, y:1.75, z:7 - 0.03, ry:Math.PI, wall:'n' },
  excavator:{ x:18.1, y:1.75, z:7 - 0.03, ry:Math.PI, wall:'n' },
  bridge:{ x:21.75, y:1.75, z:7 - 0.03, ry:Math.PI, wall:'n' },
  house:{ x:12.2 + 0.03, y:1.75, z:2.875, ry:Math.PI / 2, wall:'w' },
  computer:{ x:24 - 0.04, y:1.75, z:2.875, ry:-Math.PI / 2, wall:'e' }
};
const BP_BW = 2.9, BP_BH = 1.8125;
const BOARDS = {};
function buildBlueprintBoards(M){
  const frame = stdMat(0x23282e, 0.45, 0.3), brass = M.brass, lamp = glowMatOf(0xfff3d6);
  for (const id of BP_ORDER){
    const P = BP_PLACE[id], g = new THREE.Group(); g.position.set(P.x, 0, P.z); g.rotation.y = P.ry;
    addBox(BP_BW + 0.1, BP_BH + 0.1, 0.04, frame, 0, P.y, 0.02, 0, g);
    const canvas = keepCanvas(drawBpBoard(id, null)), t = tex(canvas, ANISO);
    const board = addPlane(BP_BW, BP_BH, new THREE.MeshBasicMaterial({ map:t, toneMapped:false }), 0, P.y, 0.045, 0, g);
    board.userData.bp = id; pickItems.push(board);
    addBox(1.6, 0.035, 0.07, brass, 0, P.y + BP_BH / 2 + 0.16, 0.2, 0, g);
    addBox(0.02, 0.02, 0.2, brass, 0, P.y + BP_BH / 2 + 0.16, 0.1, 0, g);
    const bar = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 0.014), lamp); bar.rotation.x = Math.PI / 2; bar.position.set(0, P.y + BP_BH / 2 + 0.141, 0.2); g.add(bar);
    addPlane(0.9, 0.2, basicMat(drawTableCard(BP_INFO[id].dwg + ' · ' + BP_INFO[id].title.toUpperCase(), COARSE ? 'Tap the drawing to explore it' : 'Click the drawing to explore it'), 0xe9e3d8), 0, 0.62, 0.012, 0, g);
    scene.add(g);
    BOARDS[id] = { canvas, tex:t, mesh:board, sel:null };
  }
}
function refreshBoard(id, sel){
  const B = BOARDS[id]; if (!B || B.sel === sel) return;
  B.sel = sel; drawBpBoard(id, sel, B.canvas); B.tex.needsUpdate = true; wake();
}
function bpBoardPart(id, uv){
  if (!uv) return null;
  const x = uv.x * BP_BOARD.W, y = (1 - uv.y) * BP_BOARD.H;
  if (x >= BP_BOARD.lx - 8){ const i = Math.floor((y - 74) / 40); return i >= 0 && i < BP_INFO[id].parts.length && y < 560 ? i : null; }
  return bpHit(id, x - BP_BOARD.ox, y - BP_BOARD.oy);
}
function bpViewFor(id){
  const P = BP_PLACE[id], d = clamp(fitDist(BP_BW / 2 + 0.3, BP_BH / 2 + 0.3, 2.4), 2.4, 3.2);
  if (P.wall === 'n') return { x:P.x, z:P.z - d, yaw:Math.PI, pitch:0.04 };
  if (P.wall === 'w') return { x:P.x + d, z:P.z, yaw:Math.PI / 2, pitch:0.04 };
  return { x:P.x - d, z:P.z, yaw:-Math.PI / 2, pitch:0.04 };
}

/* ---------- Full-screen blueprint viewer ---------- */
const bpv = { el:$('#bp'), cv:$('#bpCanvas'), kind:$('#bpKind'), title:$('#bpTitle'), sub:$('#bpSub'), body:$('#bpBody'), chips:$('#bpParts'), prev:$('#bpPrev'), next:$('#bpNext'), over:$('#bpOver'), model:$('#bpModel'), close:$('#bpClose'), hint:$('#bpHint'), id:null, sel:null, last:null };
function openBp(id, sel, opts){
  opts = opts || {};
  if (!BP_INFO[id]) return;
  if (introOpen) closeIntro();
  closeSearch(); closeViewer(); closeBook(); closeStation(); stopPaint(); closeBadges(); closeRideCard(); if (narrow()) closeStaff();
  if (tourIdx >= 0 && !opts.tour) endTour();
  if (THREEOK && opts.walk !== false) goView(bpViewFor(id));
  if (bpv.id && bpv.id !== id) refreshBoard(bpv.id, null);
  bpv.id = id; bpv.sel = sel == null ? null : sel;
  if (bpv.el.hidden){ bpv.last = document.activeElement; bpv.el.hidden = false; }
  renderBp(); bpv.close.focus({ preventScroll:true }); hideHint();
  noteBlueprint(id);
}
function closeBp(){
  if (bpv.el.hidden) return;
  bpv.el.hidden = true; refreshBoard(bpv.id, null);
  if (tourIdx >= 0) ui.tour.hidden = false;
  if (bpv.last && bpv.last.focus) bpv.last.focus({ preventScroll:true }); else ui.scene.focus({ preventScroll:true });
}
function bpSelect(i){ bpv.sel = i; renderBp(); }
function renderBp(){
  const id = bpv.id, B = BP_INFO[id], sel = bpv.sel, n = B.parts.length;
  drawBpView(bpv.cv, id, sel); refreshBoard(id, sel);
  bpv.body.textContent = '';
  if (sel == null){
    bpv.kind.textContent = 'Blueprint ' + B.dwg; bpv.title.textContent = B.title; bpv.sub.textContent = B.sub;
    bpv.body.appendChild(stEl('p', 'desc', B.overview));
    bpv.body.appendChild(stEl('h3', null, id === 'computer' ? 'How you could build one' : 'Build a model of your own'));
    const ol = stEl('ol', 'bpsteps'); for (const s of B.build) ol.appendChild(stEl('li', null, s)); bpv.body.appendChild(ol);
    bpv.body.appendChild(stEl('h3', null, 'Jobs that use this'));
    bpv.body.appendChild(stEl('p', 'desc', B.jobs));
  } else {
    const p = B.parts[sel];
    bpv.kind.textContent = 'Part ' + (sel + 1) + ' of ' + n + ' · ' + B.title; bpv.title.textContent = p.name; bpv.sub.textContent = p.short;
    bpv.body.appendChild(stEl('p', 'desc', p.what));
    const f = stEl('p', 'bpfact'); f.appendChild(stEl('b', null, 'Did you know? ')); f.appendChild(document.createTextNode(p.fact)); bpv.body.appendChild(f);
    bpv.body.appendChild(stEl('h3', null, 'Build it in a model'));
    bpv.body.appendChild(stEl('p', 'desc', p.model));
  }
  bpv.chips.textContent = '';
  B.parts.forEach((p, i) => {
    const b = stEl('button', 'bpchip'); b.type = 'button'; b.setAttribute('aria-pressed', String(sel === i));
    b.appendChild(stEl('span', null, String(i + 1))); b.appendChild(document.createTextNode(p.name));
    b.addEventListener('click', () => bpSelect(i)); bpv.chips.appendChild(b);
  });
  bpv.prev.disabled = sel == null;
  bpv.prev.textContent = sel === 0 ? 'Overview' : 'Previous';
  bpv.next.textContent = sel == null ? 'Start with part 1' : sel === n - 1 ? 'Back to overview' : 'Next part';
  bpv.over.hidden = sel == null || sel === 0 || sel === n - 1;   /* the other buttons already lead back there */
  const kit = id === 'car' ? 'car' : id === 'house' ? 'house' : null;
  bpv.model.hidden = !kit || !THREEOK; bpv.model.textContent = kit === 'car' ? 'Build a model car' : 'Build a model building';
  bpv.hint.textContent = (COARSE ? 'Tap' : 'Click') + ' a numbered part on the drawing, or pick one below.';
  bpv.body.scrollTop = 0;
}
bpv.close.addEventListener('click', closeBp);
bpv.el.addEventListener('click', (e) => { if (e.target === bpv.el) closeBp(); });
bpv.prev.addEventListener('click', () => { if (bpv.sel == null) return; bpSelect(bpv.sel === 0 ? null : bpv.sel - 1); });
bpv.next.addEventListener('click', () => { const n = BP_INFO[bpv.id].parts.length; bpSelect(bpv.sel == null ? 0 : bpv.sel === n - 1 ? null : bpv.sel + 1); });
bpv.over.addEventListener('click', () => bpSelect(null));
bpv.model.addEventListener('click', () => { const kit = bpv.id === 'car' ? 'car' : 'house'; closeBp(); openStation('bench', { kit }); });
function bpCanvasPoint(e){ const r = bpv.cv.getBoundingClientRect(); return [(e.clientX - r.left) / r.width * BP_VIEW.W - BP_VIEW.ox, (e.clientY - r.top) / r.height * BP_VIEW.H - BP_VIEW.oy]; }
bpv.cv.addEventListener('click', (e) => { const [x, y] = bpCanvasPoint(e), i = bpHit(bpv.id, x, y); if (i != null) bpSelect(i === bpv.sel ? null : i); });
bpv.cv.addEventListener('mousemove', (e) => { const [x, y] = bpCanvasPoint(e); bpv.cv.style.cursor = bpHit(bpv.id, x, y) != null ? 'pointer' : 'default'; });

/* ---------- The model bench ---------- */
/* Two kits in bins at the front of the bench. You build with your hands: each part comes out of its bin
   and goes where the blueprint says, then you wind the car up and let it go, or shake the building. */
const BENCH = { x:18.1, z:2.4, y:0.925, root:null, car:null, house:null, sticks:[], t:0, drive:null, shake:false, shakeT:0, braced:true, parts:{}, bins:{} };
function benchMat(hex, rough){ return new THREE.MeshStandardMaterial({ color:srgb(hex), roughness:rough == null ? 0.7 : rough }); }
const benchSpot = (x) => ({ x, z:1.87 - (narrow() ? 0.06 : 0), yaw:Math.PI, pitch:-0.5 - (narrow() ? 0.1 : 0), bench:0.907 });
/* Pinch grips for small parts: a palm over the part, fingers across it */
const BG = {
  pinchTop:{ R:{ p:[0, 0.008, 0], into:[0, -1, 0], fingers:[0, 0, 1], curl:0.72, out:0.5 }, L:{ p:[0, 0.008, 0], into:[0, -1, 0], fingers:[0, 0, 1], curl:0.72, out:0.5 } },
  stick:{ R:{ p:[0, 0, -0.007], into:[0, 0, 1], fingers:[0, 1, 0], curl:0.72, out:0.5 }, L:{ p:[0, 0, -0.007], into:[0, 0, 1], fingers:[0, 1, 0], curl:0.72, out:0.5 } },
  beamX:{ R:{ p:[0, 0.007, 0], into:[0, -1, 0], fingers:[0, 0, 1], curl:0.72, out:0.5 }, L:{ p:[0, 0.007, 0], into:[0, -1, 0], fingers:[0, 0, 1], curl:0.72, out:0.5 } },
  beamZ:{ R:{ p:[0, 0.007, 0], into:[0, -1, 0], fingers:[1, 0, 0], curl:0.72, out:0.5 }, L:{ p:[0, 0.007, 0], into:[0, -1, 0], fingers:[1, 0, 0], curl:0.72, out:0.5 } },
  tube:{ R:{ p:[0, 0, -0.01], into:[0, 0, 1], fingers:[0, 1, 0], curl:0.7, out:0.5 } },
  wheel:{ R:{ p:[0, 0, 0.013], into:[0, 0, -1], fingers:[0, -1, 0], curl:0.6, out:0.5 } },
  band:{ R:{ p:[0.235, 0.1, 0], into:[0, -1, 0], fingers:[1, 0, 0], curl:0.75, out:0.5 } },
  chassis:{ L:{ p:[0.25, 0.08, 0], into:[-1, 0, 0], fingers:[0, -1, -0.3], curl:0.55 }, R:{ p:[-0.25, 0.08, 0], into:[1, 0, 0], fingers:[0, -1, -0.3], curl:0.55 } },
  body:{ L:{ p:[0.25, 0.06, 0], into:[-1, 0, 0], fingers:[0, -1, -0.2], curl:0.5 }, R:{ p:[-0.25, 0.06, 0], into:[1, 0, 0], fingers:[0, -1, -0.2], curl:0.5 } },
  card:{ L:{ p:[0.2, 0.006, 0.13], into:[0, -1, 0], fingers:[0, 0, 1], curl:0.6 }, R:{ p:[-0.2, 0.006, 0.13], into:[0, -1, 0], fingers:[0, 0, 1], curl:0.6 } },
  plate:{ L:{ p:[0.17, 0.003, 0.11], into:[0, -1, 0], fingers:[0, 0, 1], curl:0.6 }, R:{ p:[-0.17, 0.003, 0.11], into:[0, -1, 0], fingers:[0, 0, 1], curl:0.6 } },
  car:{ L:{ p:[0.2, 0.1, 0.09], into:[0, 0, -1], fingers:[0, -1, 0], curl:0.5 }, R:{ p:[-0.2, 0.1, 0.09], into:[0, 0, -1], fingers:[0, -1, 0], curl:0.5 } },
  table:{ L:{ p:[0.33, 0.012, -0.12], into:[0, -1, 0], fingers:[0, 0, 1], curl:0.5 }, R:{ p:[-0.33, 0.012, -0.12], into:[0, -1, 0], fingers:[0, 0, 1], curl:0.5 } }
};
function buildModelBench(M){
  const top = stdMat(0xc49a6c, 0.5), leg = stdMat(0x3a3f46, 0.45, 0.4);
  addBox(2.4, 0.06, 1.1, top, BENCH.x, BENCH.y - 0.055, BENCH.z);
  for (const sx of [-1.1, 1.1]) for (const sz of [-0.46, 0.46]) addBox(0.07, BENCH.y - 0.085, 0.07, leg, BENCH.x + sx, (BENCH.y - 0.085) / 2, BENCH.z + sz);
  addBox(2.2, 0.04, 0.9, leg, BENCH.x, 0.22, BENCH.z);
  addPlane(1.5, 1.0, basicMat(drawCuttingMat()), BENCH.x, BENCH.y - 0.024, BENCH.z, 0).rotation.x = -Math.PI / 2;
  /* Tools at the far end of the bench */
  addBox(0.32, 0.03, 0.04, stdMat(0xd9d9d9, 0.4, 0.6), BENCH.x + 1.0, BENCH.y - 0.01, BENCH.z + 0.3, 0.3);
  addBox(0.06, 0.05, 0.16, stdMat(0xe07b2a, 0.5), BENCH.x + 1.05, BENCH.y, BENCH.z - 0.05);
  addBox(0.4, 0.012, 0.03, stdMat(0xc8c8c8, 0.4, 0.5), BENCH.x + 0.95, BENCH.y - 0.018, BENCH.z + 0.46, -0.4);
  for (const x of [17.3, 18.1, 18.9]) OBST.push({ x, z:2.62, r:0.72 });
  pickBox(2.4, 0.6, 1.1, BENCH.x, BENCH.y + 0.2, BENCH.z, { station:'bench' });
  const root = new THREE.Group(); root.position.set(BENCH.x, BENCH.y - 0.018, BENCH.z); root.userData.noMerge = true; scene.add(root); BENCH.root = root;
  /* Bins: an open parts box for the car, a card rack and a stick tray for the building */
  const card = benchMat(0xb8916a, 0.9), rim = benchMat(0xa07a52, 0.9);
  const bin = new THREE.Group(); bin.position.set(-0.9, 0, -0.33); root.add(bin); BENCH.bins.car = bin;
  addBox(0.6, 0.01, 0.44, card, 0, 0.005, 0, 0, bin);
  for (const s of [-1, 1]){ addBox(0.6, 0.07, 0.01, rim, 0, 0.035, s * 0.215, 0, bin); addBox(0.01, 0.07, 0.44, rim, s * 0.295, 0.035, 0, 0, bin); }
  addPlane(0.3, 0.06, basicMat(drawTableCard('MODEL CAR KIT', ' ')), 0, 0.04, 0.221, 0, bin);
  const rack = new THREE.Group(); rack.position.set(-0.35, 0, -0.35); root.add(rack); BENCH.bins.rack = rack;
  addBox(0.62, 0.04, 0.2, benchMat(0x8a6a48, 0.6), 0, 0.02, 0, 0, rack);
  for (const z of [-0.075, -0.025, 0.025, 0.075]) addBox(0.62, 0.05, 0.012, benchMat(0x8a6a48, 0.6), 0, 0.065, z, 0, rack);
  const tray = new THREE.Group(); tray.position.set(0.58, 0, -0.3); root.add(tray); BENCH.bins.tray = tray;
  addBox(0.26, 0.008, 0.5, card, 0, 0.004, 0, 0, tray);
  for (const s of [-1, 1]){ addBox(0.26, 0.04, 0.008, rim, 0, 0.02, s * 0.246, 0, tray); addBox(0.008, 0.04, 0.5, rim, s * 0.126, 0.02, 0, 0, tray); }
  pickBox(0.6, 0.2, 0.44, BENCH.x - 0.9, BENCH.y + 0.05, BENCH.z - 0.33, { station:'bench', act:'car' });
  pickBox(0.62, 0.5, 0.2, BENCH.x - 0.35, BENCH.y + 0.2, BENCH.z - 0.35, { station:'bench', act:'house' });
  pickBox(0.26, 0.2, 0.5, BENCH.x + 0.58, BENCH.y + 0.05, BENCH.z - 0.3, { station:'bench', act:'house' });
  /* The shake table the building stands on */
  const tbl = new THREE.Group(); tbl.position.set(0.1, 0, 0.1); root.add(tbl); BENCH.table = tbl;
  addBox(0.7, 0.005, 0.54, benchMat(0xd9dde1, 0.4), 0, 0.0025, 0, 0, tbl);
  buildCarKit(root); buildHouseKit(root);
  benchReset();
}
/* Every part remembers where it goes in the model (fin) and where it waits in its bin (bin) */
function partPose(m, bin){ m.updateMatrix(); m.userData.fin = { p:m.position.clone(), q:m.quaternion.clone(), s:m.scale.clone() }; m.userData.bin = bin; }
function buildCarKit(root){
  const g = new THREE.Group(), P = {}; g.position.x = -0.55; root.add(g); BENCH.car = g;
  const card = benchMat(0xb8916a, 0.9), white = benchMat(0xf4f4f0, 0.4), wood = benchMat(0xd9b98a, 0.7), red = benchMat(0xc4302b, 0.45), yellow = benchMat(0xf2c14e, 0.75), dark = benchMat(0x1d2124, 0.3), rubber = benchMat(0xb07a3a, 0.8);
  const add = (key, mesh) => { (P[key] = P[key] || []).push(mesh); g.add(mesh); return mesh; };
  const B = (x, y, z, r) => ({ p:[-0.35 + x, y, -0.33 + z], r:r || [0, 0, 0] });
  /* A little wooden stand holds the chassis at wheel height while you build under it */
  const stand = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.068, 0.14), benchMat(0xc8a27a, 0.6)); stand.position.set(0, 0.034, 0); root.add(stand); stand.position.x = -0.55;
  const ch = add('chassis', new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.012, 0.2), card)); ch.position.set(0, 0.075, 0); partPose(ch, B(0.02, 0.016, -0.1));
  let k = 0;
  for (const x of [-0.17, 0.17]){
    const s = add('straws', new THREE.Mesh(new THREE.CylinderGeometry(0.009, 0.009, 0.22, 14), white)); s.rotation.x = Math.PI / 2; s.position.set(x, 0.06, 0); partPose(s, B(-0.22 + k * 0.04, 0.032, 0.03, [90, 0, 0]));
    const a = add('axles', new THREE.Mesh(new THREE.CylinderGeometry(0.0035, 0.0035, 0.31, 8), wood)); a.rotation.x = Math.PI / 2; a.position.set(x, 0.06, 0); partPose(a, B(0.22 - k * 0.04, 0.027, 0.0, [90, 0, 0]));
    for (const z of [-0.135, 0.135]){
      const w = new THREE.Group(); w.position.set(x, 0.06, z);
      const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.024, 28), red); cap.rotation.x = Math.PI / 2; w.add(cap);
      const dot = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.026, 18), white); dot.rotation.x = Math.PI / 2; w.add(dot);
      const mark = new THREE.Mesh(new THREE.BoxGeometry(0.01, 0.05, 0.027), dark); w.add(mark);
      add('wheels', w); partPose(w, B(-0.2 + (k * 2 + (z > 0 ? 1 : 0)) * 0.135, 0.022, 0.14, [-90, 0, 0]));
    }
    k++;
  }
  const curve = new THREE.CatmullRomCurve3([new THREE.Vector3(0.23, 0.09, 0), new THREE.Vector3(0.05, 0.075, 0.012), new THREE.Vector3(-0.15, 0.066, 0.008), new THREE.Vector3(-0.17, 0.05, -0.006), new THREE.Vector3(-0.19, 0.064, 0), new THREE.Vector3(-0.17, 0.072, 0.008)]);
  const band = add('band', new THREE.Mesh(new THREE.TubeGeometry(curve, 40, 0.0035, 6, false), rubber)); partPose(band, B(0.0, -0.035, 0.06));
  const clip = add('band', new THREE.Mesh(new THREE.TorusGeometry(0.012, 0.0025, 6, 16), benchMat(0xb9c0c6, 0.3))); clip.position.set(0.235, 0.09, 0); clip.rotation.y = Math.PI / 2; partPose(clip, B(0.235, 0.055, 0.06, [0, 90, 0]));
  const sh = new THREE.Shape(); sh.moveTo(-0.25, 0); sh.lineTo(0.25, 0); sh.lineTo(0.25, 0.045); sh.lineTo(0.13, 0.065); sh.lineTo(0.06, 0.125); sh.lineTo(-0.12, 0.128); sh.lineTo(-0.2, 0.07); sh.lineTo(-0.25, 0.062); sh.closePath();
  const bodyGeo = new THREE.ExtrudeGeometry(sh, { depth:0.17, bevelEnabled:false }); bodyGeo.translate(0, 0, -0.085);
  const body = add('body', new THREE.Mesh(bodyGeo, yellow)); body.position.set(0, 0.081, 0); partPose(body, B(0.02, 0.024, -0.1));
  const glassMat = new THREE.MeshStandardMaterial({ color:srgb(0x1d2124), roughness:0.25, side:THREE.DoubleSide });
  for (const z of [-0.0865, 0.0865]){ const wsh = new THREE.Shape(); wsh.moveTo(-0.1, -0.006); wsh.lineTo(0.04, -0.006); wsh.lineTo(0.05, 0.034); wsh.lineTo(-0.1, 0.036); wsh.closePath(); const wm = add('body', new THREE.Mesh(new THREE.ShapeGeometry(wsh), glassMat)); wm.position.set(0, 0.162, z); partPose(wm, B(0.02, 0.105, -0.1 + z)); }
  BENCH.parts.car = P;
  /* How each part is picked up: with both hands or pinched in one, and which parts ride along */
  BENCH.kit = BENCH.kit || {};
  BENCH.kit.car = { chassis:{ grips:BG.chassis, both:true, lift:0.12, follow:[] }, straws:{ grips:BG.tube, lift:0.08 }, axles:{ grips:BG.tube, lift:0.08 }, wheels:{ grips:BG.wheel, lift:0.1 }, band:{ grips:BG.band, lift:0.08, lead:0, follow:[1] }, body:{ grips:BG.body, both:true, lift:0.14, lead:0, follow:[1, 2] } };
}
function stickBetween(m, ax, ay, bx, by, z){
  const dx = bx - ax, dy = by - ay, L = Math.hypot(dx, dy);
  m.position.set((ax + bx) / 2, (ay + by) / 2, z); m.rotation.set(0, 0, -Math.atan2(dx, dy)); m.scale.set(1, L, 1);
}
function buildHouseKit(root){
  const g = new THREE.Group(), P = {}; g.position.set(0.1, 0.005, 0.1); root.add(g); BENCH.house = g;
  const card = benchMat(0xb8916a, 0.9), stick = benchMat(0xd9b98a, 0.75), gray = benchMat(0x9aa1a6, 0.85), plate = benchMat(0xe9e3d8, 0.85), brace = benchMat(0xc4572f, 0.7);
  const add = (key, mesh) => { (P[key] = P[key] || []).push(mesh); g.add(mesh); return mesh; };
  /* Rack slots (root frame): the base card up front, the two floor plates behind it */
  const R = (slot, y) => ({ p:[-0.35, 0.04 + y, -0.35 - 0.075 + slot * 0.05], r:[-90, 0, 0] });
  const base = add('base', new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.012, 0.38), card)); base.position.y = 0.006; partPose(base, R(0, 0.19));
  for (const [w, d, x, z] of [[0.44, 0.02, 0, -0.16], [0.44, 0.02, 0, 0.16], [0.02, 0.32, -0.21, 0], [0.02, 0.32, 0.21, 0]]){ const f = add('base', new THREE.Mesh(new THREE.BoxGeometry(w, 0.02, d), gray)); f.position.set(x, 0.022, z); partPose(f, { p:[-0.35 + x, 0.04 + 0.19 + z, -0.35 - 0.075 - 0.022], r:[-90, 0, 0] }); }
  BENCH.levels = [0.032, 0.232, 0.432];
  const unitStick = new THREE.BoxGeometry(0.012, 1, 0.012), S = BENCH.sticks = [];
  /* Stick tray (root frame): columns on top, beams under them, braces at the bottom, eight lanes across */
  const T = (lane, layer, zoff, ry) => ({ p:[0.58 - 0.105 + lane * 0.03, 0.01 + layer * 0.013, -0.3 + (zoff || 0)], r:ry ? [0, ry, 0] : [90, 0, 0] });
  let lane = 0;
  for (const lvl of [0, 1]){
    for (const [x, z] of [[-0.2, -0.15], [0.2, -0.15], [-0.2, 0.15], [0.2, 0.15]]){ const m = add(lvl ? 'col2' : 'col1', new THREE.Mesh(unitStick, stick)); S.push({ m, ax:x, bx:x, la:lvl, lb:lvl + 1, z }); m.userData.binPose = T(lane, 2, -0.1); lane++; }
  }
  lane = 0;
  for (const lvl of [0, 1]){
    for (const z of [-0.15, 0.15]){ const m = add(lvl ? 'beam2' : 'beam1', new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.012, 0.012), stick)); S.push({ m, beam:true, x:0, l:lvl + 1, y:0.006, z }); m.userData.binPose = { p:[0.58 - 0.105 + lane * 0.03, 0.023, -0.3], r:[0, 90, 0] }; lane++; }
    for (const x of [-0.2, 0.2]){ const m = add(lvl ? 'beam2' : 'beam1', new THREE.Mesh(new THREE.BoxGeometry(0.012, 0.012, 0.32), stick)); S.push({ m, beam:true, x, l:lvl + 1, y:0.006, z:0 }); m.userData.binPose = { p:[0.58 - 0.105 + lane * 0.03, 0.023, -0.3], r:[0, 0, 0] }; lane++; }
    const pl = add(lvl ? 'beam2' : 'beam1', new THREE.Mesh(new THREE.BoxGeometry(0.43, 0.006, 0.33), plate)); S.push({ m:pl, beam:true, x:0, l:lvl + 1, y:0.015, z:0 }); pl.userData.binPose = R(lvl + 1, 0.165);
  }
  lane = 0;
  for (const lvl of [0, 1]) for (const z of [-0.158, 0.158]) for (const [a, b] of [[-0.2, 0.2], [0.2, -0.2]]){ const m = add('brace', new THREE.Mesh(new THREE.BoxGeometry(0.008, 1, 0.008), brace)); S.push({ m, ax:a, bx:b, la:lvl, lb:lvl + 1, z }); m.userData.binPose = T(lane, 0); lane++; }
  BENCH.parts.house = P;
  benchPose(0, 0, 0);
  for (const s of S){ partPose(s.m, s.m.userData.binPose); }
  BENCH.kit.house = { base:{ grips:BG.card, both:true, lift:0.16, lead:0, follow:[1, 2, 3, 4] }, col1:{ grips:BG.stick, lift:0.1, pairs:true }, beam1:{ grips:null, lift:0.1, pairs:true, plate:BG.plate }, col2:{ grips:BG.stick, lift:0.1, pairs:true }, beam2:{ grips:null, lift:0.1, pairs:true, plate:BG.plate }, brace:{ grips:BG.stick, lift:0.12, pairs:true } };
}
function benchPose(g0, g1, g2){
  const off = [g0, g1, g2], L = BENCH.levels;
  for (const s of BENCH.sticks){
    if (!s.m.userData.placed && s.m.userData.fin) continue;
    if (s.beam){ s.m.position.set(s.x + off[s.l], L[s.l] + s.y, s.z); continue; }
    stickBetween(s.m, s.ax + off[s.la], L[s.la], s.bx + off[s.lb], L[s.lb], s.z);
  }
}
/* Put a part in its bin, or on the model */
function benchPut(m, where){
  const kit = m.parent === BENCH.car || BENCH.parts.car && Object.values(BENCH.parts.car).some((a) => a.includes(m)) ? BENCH.car : BENCH.house;
  if (where === 'fin'){ kit.attach(m); const f = m.userData.fin; m.position.copy(f.p); m.quaternion.copy(f.q); m.scale.copy(f.s); m.userData.placed = true; }
  else { BENCH.root.attach(m); const b = m.userData.bin; m.position.fromArray(b.p); m.rotation.set(b.r[0] * D2R, b.r[1] * D2R, b.r[2] * D2R); m.scale.copy(m.userData.fin.s); m.userData.placed = false; }
}
const BENCH_KITS = {
  car:{ name:'Model car', steps:[
    { t:'Gather materials', d:'Stiff cardboard or foam board, 2 drinking straws, 2 wooden skewers, 4 bottle caps, a rubber band, a paper clip, tape and glue. It’s all in the kit box.', w:'Good engineers start with a plan and a parts list.', show:[] },
    { t:'Chassis', d:'Take the cardboard rectangle, about 20 by 8 centimeters, and rest it on the little stand so you can work underneath. This is the chassis, the frame everything else attaches to.', w:'A stiff, light chassis wastes less energy bending.', show:['chassis'], act:'Set the chassis on the stand' },
    { t:'Bearings', d:'Tape the two straws across the bottom, one near each end. Keep them parallel or the car will curve.', w:'The straws are bearings: the axles spin inside them with very little friction.', show:['straws'], act:'Tape on the straws' },
    { t:'Axles', d:'Slide a skewer through each straw, leaving a little sticking out on both sides.', w:'Axles carry the wheels and let each pair turn together.', show:['axles'], act:'Slide in the axles' },
    { t:'Wheels', d:'Poke a hole in the center of each bottle cap and push one onto each axle end. A dab of glue keeps them on.', w:'Wheels that are centered and straight roll farther and wobble less.', show:['wheels'], act:'Push on the wheels' },
    { t:'Rubber-band motor', d:'Hook the rubber band on a paper clip taped to the front, and loop the other end around the rear axle.', w:'The stretched rubber band stores energy. As it unwinds it spins the rear axle: your engine and drivetrain in one.', show:['band'], act:'Hook up the rubber band' },
    { t:'Body', d:'Fold a body from card stock and set it over the chassis. Keep it light.', w:'Less weight lets the same stored energy push the car farther.', show:['body'], act:'Set on the body' },
    { t:'Test drive', d:'Roll the car backward to wind the band around the axle, set it down and let go!', w:'Real engineers test, measure, change one thing and test again.', show:[], test:true }
  ] },
  house:{ name:'Model building', steps:[
    { t:'Gather materials', d:'Craft sticks or wooden skewers, cardboard, glue (a hot glue gun works fast, with an adult’s help), and a tray to use as a shake table. The cards are in the rack and the sticks in the tray.', w:'Every structure starts with a plan.', show:[] },
    { t:'Foundation', d:'Take the cardboard base, with its strip of card glued around the edge, and set it on the shake table.', w:'The foundation carries the whole building’s weight down to the ground.', show:['base'], act:'Set down the base' },
    { t:'First-floor columns', d:'Glue a stick upright at each corner.', w:'Columns carry weight straight down, like the studs in a wall.', show:['col1'], act:'Glue in the columns' },
    { t:'Beams and floor', d:'Glue sticks across the tops of the columns, then set a piece of card on top as the second floor.', w:'Beams tie the columns together and hold up the floor.', show:['beam1'], act:'Add the beams and floor' },
    { t:'Second story and roof', d:'Repeat: four more columns, four beams and a card roof.', w:'Every story adds weight that the floors below have to carry.', show:['col2', 'beam2'], act:'Build the second story' },
    { t:'Cross-bracing', d:'Glue sticks in an X across the long sides of each story.', w:'Triangles can’t change shape, so cross-bracing stops the frame from leaning over, or racking, in an earthquake.', show:['brace'], act:'Glue on the bracing' },
    { t:'Shake test', d:'Hold the tray and slide it quickly back and forth, like an earthquake.', w:'Engineers test real buildings this way on giant shake tables. Compare your frame with and without its bracing.', show:[], test:true }
  ] }
};
const benchSt = { kit:null, step:0, result:null, built:0 };
/* The kit's parts go back in their bins (all of them, or only the ones from steps after `keep`) */
function benchReset(kit, keep){
  handsFinish();
  for (const k of kit ? [kit] : ['car', 'house']){
    const P = BENCH.parts[k], steps = BENCH_KITS[k].steps;
    steps.forEach((st, i) => { for (const key of st.show) for (const m of P[key]){ if (keep != null && i <= keep) continue; benchPut(m, 'bin'); } });
  }
  if (BENCH.car) BENCH.car.position.x = -0.55;
  if (BENCH.parts.car) for (const w of BENCH.parts.car.wheels) if (w.userData.placed) w.rotation.z = 0;
  if (BENCH.table){ BENCH.table.position.x = 0.1; BENCH.house.position.x = 0.1; benchPose(0, 0, 0); }
  BENCH.shake = false; BENCH.drive = null;
  wake();
}
function benchBraces(){ for (const m of BENCH.parts.house.brace) m.visible = BENCH.braced || !m.userData.placed; wake(); }
/* Your hands take the step's parts out of the bin and put them on the model */
function benchBuild(step){
  const kit = benchSt.kit, K = BENCH_KITS[kit], S = K.steps[step], P = BENCH.parts[kit], spec = BENCH.kit[kit];
  const C = hClip(benchSpot(kit === 'car' ? 17.55 : 18.25)), ms = [];
  for (const key of S.show){
    const sp = spec[key], list = P[key];
    if (sp.both){
      const lead = list[sp.lead || 0], fol = (sp.follow || []).map((i) => list[i]);
      hGrab(C, lead, sp.grips, 0.75, { arc:0.05 });
      for (const f of fol) hMove(C, f, { parent:BENCH[kit], p:f.userData.fin.p.toArray(), q:f.userData.fin.q }, 0.8, { lift:sp.lift, keep:true });
      hMove(C, lead, { parent:BENCH[kit], p:lead.userData.fin.p.toArray(), q:lead.userData.fin.q }, 0.8, { lift:sp.lift, end:() => { lead.userData.placed = true; for (const f of fol) f.userData.placed = true; } });
      hRest(C, Object.keys(sp.grips), 0.4);
      continue;
    }
    if (sp.pairs){
      for (let i = 0; i < list.length; i += 2){
        const pair = [list[i], list[i + 1]].filter(Boolean);
        if (pair.length === 1 && sp.plate){
          /* The floor card: both hands */
          const m = pair[0];
          hRest(C, ['L', 'R'], 0.3);
          hGrab(C, m, sp.plate, 0.7, { arc:0.05 });
          hMove(C, m, { parent:BENCH[kit], p:m.userData.fin.p.toArray(), q:m.userData.fin.q }, 0.8, { lift:0.14, end:() => { m.userData.placed = true; } });
          continue;
        }
        pair.forEach((m, j) => { const side = j === 0 ? 'R' : 'L', g = (sp.grips || benchGripFor(m))[side]; hTo(C, side, { o:m, g }, i === 0 ? 0.65 : 0.5, { keep:j < pair.length - 1, arc:0.04 }); });
        pair.forEach((m, j) => hMove(C, m, { parent:BENCH[kit], p:m.userData.fin.p.toArray(), q:m.userData.fin.q }, 0.7, { lift:sp.lift, keep:j < pair.length - 1, end:() => { m.userData.placed = true; } }));
        hWait(C, 0.08);
      }
      hRest(C, ['L', 'R'], 0.4);
      continue;
    }
    const lead = list[sp.lead || 0], fol = (sp.follow || []).map((i) => list[i]), items = sp.follow ? [lead] : list;
    for (const m of items){
      hTo(C, 'R', { o:m, g:sp.grips.R }, 0.55, { arc:0.05 });
      for (const f of fol) hMove(C, f, { parent:BENCH[kit], p:f.userData.fin.p.toArray(), q:f.userData.fin.q }, 0.7, { lift:sp.lift, keep:true });
      hMove(C, m, { parent:BENCH[kit], p:m.userData.fin.p.toArray(), q:m.userData.fin.q }, 0.7, { lift:sp.lift, end:() => { m.userData.placed = true; for (const f of fol) f.userData.placed = true; } });
      /* A little press to seat it */
      hTo(C, 'R', { o:m, g:sp.grips.R, off:() => [0, -0.004, 0] }, 0.12, { keepHand:true });
      hTo(C, 'R', { o:m, g:sp.grips.R }, 0.1, { keepHand:true });
    }
    hRest(C, ['R'], 0.4);
  }
  hAt(C, () => { benchSt.built = step; });
  handsPlay(C, () => { benchSt.built = step; if (STN.id === 'bench') stRender(); });
}
function benchGripFor(m){
  const g = m.geometry.parameters || {};
  if (g.width > g.depth) return BG.beamX;
  if (g.depth > g.width) return BG.beamZ;
  return BG.stick;
}
/* Wind the car up by rolling it back, then let it go */
function benchDriveClip(){
  const C = hClip(benchSpot(17.55)), car = BENCH.car;
  hGrab(C, car, BG.car, 0.8, { arc:0.06 });
  const x0 = car.position.x;
  hAnim(C, 0.9, (u) => { const s = -0.26 * hsm(u); car.position.x = x0 + s; for (const w of BENCH.parts.car.wheels) w.rotation.z = -s / 0.06; });
  hWait(C, 0.9);
  hWait(C, 0.35);
  hAt(C, () => benchDrive());
  hRest(C, ['L', 'R'], 0.3);
  handsPlay(C, () => { if (STN.id === 'bench') stRender(); });
}
/* Shake the table by hand for a few seconds */
function benchShakeClip(){
  const C = hClip(benchSpot(18.25));
  hGrab(C, BENCH.table, BG.table, 0.8, { arc:0.05 });
  hAt(C, () => { BENCH.shake = true; BENCH.shakeT = 0; benchSt.result = benchShakeText(); award('maker'); if (STN.id === 'bench'){ STN.cur.keepScroll = true; stRender(); } });
  hWait(C, 4.2);
  hAt(C, () => { BENCH.shake = false; BENCH.table.position.x = 0.1; BENCH.house.position.x = 0.1; benchPose(0, 0, 0); });
  hRest(C, ['L', 'R'], 0.5);
  handsPlay(C, () => { if (STN.id === 'bench') stRender(); });
}
STATIONS.bench = {
  id:'bench', room:'blueprint', kick:'Room 103 · Model bench', hands:true,
  title(){ return benchSt.kit ? 'Build a ' + BENCH_KITS[benchSt.kit].name.toLowerCase() : 'Build a model'; },
  stepText(){ if (!benchSt.kit) return ''; const n = BENCH_KITS[benchSt.kit].steps.length; return 'Step ' + (benchSt.step + 1) + ' of ' + n; },
  spot(){ return benchSpot(benchSt.kit === 'house' ? 18.25 : benchSt.kit === 'car' ? 17.55 : 18.1); },
  view(){ const s = this.spot(); return benchSt.kit ? { x:s.x, z:s.z, yaw:s.yaw, pitch:s.pitch } : { x:18.1, z:1.1, yaw:Math.PI, pitch:-0.32 }; },
  enter(opts){ if (opts && opts.kit && opts.kit !== benchSt.kit) this.pick(opts.kit); },
  leave(){ handsFinish(); BENCH.shake = false; if (BENCH.table){ BENCH.table.position.x = 0.1; BENCH.house.position.x = 0.1; } benchPose(0, 0, 0); },
  pick(k){ benchSt.kit = k; benchSt.step = 0; benchSt.result = null; benchSt.built = 0; BENCH.braced = true; benchReset(); benchBraces(); },
  act(id){
    if (!benchSt.kit){ if (id === 'car' || id === 'house'){ this.pick(id); stRender(); goView(this.view()); } return; }
    const A = this.actions(), a = A[0];
    if (a && !a.disabled) a.fn(); else if (a && a.hint) toast(a.hint);
  },
  actLabel(id){ if (!benchSt.kit) return id === 'car' ? 'Build · Model car' : 'Build · Model building'; const a = this.actions()[0]; return a && !a.disabled ? a.label : ''; },
  actions(){
    const K = BENCH_KITS[benchSt.kit], S = K.steps[benchSt.step], busy = handsBusy(), done = benchSt.built >= benchSt.step;
    if (S.test){
      if (benchSt.kit === 'car') return [{ label:BENCH.drive ? 'Driving…' : benchSt.result ? 'Wind it up and test again' : 'Wind it up and let go', fn:benchDriveClip, disabled:busy || !!BENCH.drive, hint:'' }];
      return [{ label:BENCH.shake ? 'Shaking…' : benchSt.result ? 'Shake it again' : 'Shake the table', fn:benchShakeClip, disabled:busy || BENCH.shake, hint:'' }];
    }
    if (benchSt.step === 0) return [];
    return [{ label:done ? 'Done: ' + S.act.toLowerCase() : S.act, fn:() => benchBuild(benchSt.step), disabled:busy || done, hint:'' }];
  },
  render(body, btns){
    const busy = handsBusy();
    if (!benchSt.kit){
      body.appendChild(stEl('p', 'stp', 'Pick a kit. You’ll build it with your own hands, one part at a time, the way you would with real materials, then test it.'));
      const row = stEl('div', 'stchoice');
      for (const k of ['car', 'house']){ const b = stEl('button', 'stbig'); b.type = 'button'; b.appendChild(stEl('b', null, BENCH_KITS[k].name)); b.appendChild(stEl('span', null, k === 'car' ? 'Rubber-band powered. Test how far it rolls.' : 'Two stories with cross-bracing. Shake-test it.')); b.addEventListener('click', () => { this.pick(k); stRender(); goView(this.view()); }); row.appendChild(b); }
      body.appendChild(row);
      body.appendChild(stEl('p', 'stnote', 'The Automobile and Building blueprints on the walls show the real versions of these parts.'));
      return;
    }
    const K = BENCH_KITS[benchSt.kit], S = K.steps[benchSt.step], last = benchSt.step === K.steps.length - 1, done = benchSt.built >= benchSt.step;
    body.appendChild(stSteps(K.steps.map((s) => s.t), benchSt.step));
    body.appendChild(stEl('h3', 'sth3', S.t));
    body.appendChild(stEl('p', 'stp', S.d));
    const why = stEl('p', 'stwhy'); why.appendChild(stEl('b', null, 'Why it works: ')); why.appendChild(document.createTextNode(S.w)); body.appendChild(why);
    if (S.test && benchSt.result) body.appendChild(stEl('p', 'stresult', benchSt.result));
    btns.appendChild(stBtn('Back', () => { if (benchSt.step > 0){ handsFinish(); benchSt.step--; benchSt.result = null; BENCH.shake = false; benchReset(benchSt.kit, benchSt.step); benchSt.built = Math.min(benchSt.built, benchSt.step); benchBraces(); stRender(); } }, false, benchSt.step === 0 || busy));
    for (const a of this.actions()) btns.appendChild(stBtn(a.label, a.fn, !a.disabled, a.disabled));
    if (busy) btns.appendChild(stBtn('Skip ahead', () => { handsFinish(); stRender(); }));
    if (!last) btns.appendChild(stBtn(benchSt.step === 0 ? 'Start building' : 'Next step', () => { handsFinish(); benchSt.step++; stRender(); }, benchSt.step === 0 || done, busy || !(benchSt.step === 0 || done)));
    else if (benchSt.kit === 'house') btns.appendChild(stToggle(BENCH.braced ? 'Remove bracing' : 'Put bracing back', !BENCH.braced, () => { BENCH.braced = !BENCH.braced; benchBraces(); if (BENCH.shake) benchSt.result = benchShakeText(); stRender(); }));
    btns.appendChild(stBtn('Switch kit', () => { handsFinish(); benchReset(benchSt.kit); this.pick(benchSt.kit === 'car' ? 'house' : 'car'); stRender(); goView(this.view()); }, false, busy));
  },
  tick(dt){
    let a = false;
    if (BENCH.drive){
      a = true; const D = BENCH.drive; D.t += dt;
      const T = D.T, k = Math.min(1, D.t / T), s = D.dist * (1 - Math.pow(1 - k, 2));
      BENCH.car.position.x = D.x0 + s;
      for (const w of BENCH.parts.car.wheels) w.rotation.z = D.w0 - s / 0.06;
      if (k >= 1 && D.t > T + 0.9){ BENCH.drive = null; BENCH.car.position.x = -0.55; for (const w of BENCH.parts.car.wheels) w.rotation.z = 0; if (STN.id === 'bench') stRender(); }
    }
    if (BENCH.shake){
      a = true; BENCH.t += dt; BENCH.shakeT += dt;
      const w = Math.PI * 2 * 1.6, A = 0.022 * Math.min(1, BENCH.shakeT / 0.6), br = BENCH.braced, g0 = A * Math.sin(w * BENCH.t);
      const d1 = br ? 0.0016 : 0.02, d2 = br ? 0.0035 : 0.038;
      BENCH.table.position.x = 0.1 + g0; BENCH.house.position.x = 0.1 + g0;
      benchPose(0, d1 * Math.sin(w * BENCH.t - 0.5), d2 * Math.sin(w * BENCH.t - 0.8));
    }
    return a;
  }
};
function benchDrive(){
  if (BENCH.drive) return;
  const m = 1.6 + Math.random() * 1.3;
  BENCH.drive = { t:0, T:REDUCED ? 0.01 : 2.4, dist:1.1 + (-0.55 - BENCH.car.position.x), x0:BENCH.car.position.x, w0:BENCH.parts.car.wheels[0].rotation.z };
  benchSt.result = 'It rolled ' + m.toFixed(1) + ' meters across the floor. Now change one thing at a time (more winds, bigger wheels or a lighter body) and test again to see what helps most.';
  award('maker'); if (STN.id === 'bench') stRender(); wake();
}
function benchShakeText(){
  return BENCH.braced ? 'With cross-bracing, the top floor barely moves: about 4 millimeters each way. The triangles hold the frame square.' : 'Without bracing, the frame racks into a leaning parallelogram, and the top floor sways about 4 centimeters each way, ten times more. That’s why real buildings use bracing, sheathing or shear walls.';
}
