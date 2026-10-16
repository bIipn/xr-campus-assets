/* ================================================================
   Hands-on stations: a docked panel that walks you through an activity
   while the 3D view stays centered on the equipment
   ================================================================ */
const STN = { cur:null, id:null, el:{ panel:$('#station'), kick:$('#stKick'), title:$('#stTitle'), step:$('#stStep'), body:$('#stBody'), btns:$('#stBtns'), close:$('#stClose') } };
/* On phones the button row scrolls sideways: fade its edge while more buttons are out of view */
function stMore(){ const b = STN.el.btns; b.classList.toggle('more', b.scrollWidth - b.scrollLeft - b.clientWidth > 4); }
STN.el.btns.addEventListener('scroll', stMore, { passive:true });
addEventListener('resize', stMore);
const STATIONS = {};
function openStation(id, opts){
  const S = STATIONS[id]; if (!S || !THREEOK) return;
  opts = opts || {};
  if (introOpen) closeIntro();
  closeSearch(); closeViewer(); closeBook(); if (typeof closeBp === 'function') closeBp(); closeBadges(); closeRideCard();
  if (tourIdx >= 0 && !opts.tour) endTour();
  stopPaint(); closeStaff();
  if (STN.cur && STN.cur !== S && STN.cur.leave) STN.cur.leave();
  STN.cur = S; STN.id = id; S.arrived = roomAt(cam.x, cam.z).id === S.room;
  STN.el.panel.hidden = false; document.body.classList.add('station-open');
  if (S.enter) S.enter(opts);
  stRender();
  if (opts.walk !== false) goView(S.view());
  applyProjection(); hideHint(); ui.tag.hidden = true; wake();
  if (!opts.keepFocus) STN.el.close.focus({ preventScroll:true });
}
function closeStation(){
  if (!STN.cur) return;
  if (STN.cur.leave) STN.cur.leave();
  STN.cur = null; STN.id = null;
  STN.el.panel.hidden = true; document.body.classList.remove('station-open');
  applyProjection(); ui.scene.focus({ preventScroll:true }); wake();
}
function stRender(){
  const S = STN.cur; if (!S) return;
  const E = STN.el;
  E.kick.textContent = S.kick; E.title.textContent = typeof S.title === 'function' ? S.title() : S.title;
  const st = S.stepText ? S.stepText() : ''; E.step.textContent = st; E.step.hidden = !st;
  const keep = E.body.scrollTop; E.body.textContent = ''; E.btns.textContent = '';
  S.render(E.body, E.btns);
  stMore();
  if (S.keepScroll) E.body.scrollTop = keep; else E.body.scrollTop = 0;
  S.keepScroll = false;
}
function stationFrame(dt){
  let a = false;
  if (STN.cur && !STN.cur.arrived && roomAt(cam.x, cam.z).id === STN.cur.room) STN.cur.arrived = true;
  for (const id in STATIONS){ const S = STATIONS[id]; if (S.tick && S.tick(dt)) a = true; }
  return a;
}
/* Small builders for panel content */
function stEl(tag, cls, text){ const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
function stBtn(label, fn, primary, disabled){ const b = stEl('button', 'btn' + (primary ? ' primary' : ''), label); b.type = 'button'; if (disabled) b.disabled = true; b.addEventListener('click', fn); return b; }
function stToggle(label, on, fn){ const b = stBtn(label, fn); b.setAttribute('aria-pressed', String(!!on)); b.classList.add('tog'); return b; }
function stTable(head, rows, cls){
  const t = stEl('table', 'sttable' + (cls ? ' ' + cls : '')), th = stEl('thead'), tr = stEl('tr');
  for (const h of head) tr.appendChild(stEl('th', null, h));
  th.appendChild(tr); t.appendChild(th);
  const tb = stEl('tbody');
  for (const r of rows){ const row = stEl('tr', r.cls || null); for (const c of r.cells || r) row.appendChild(stEl('td', null, c)); tb.appendChild(row); }
  t.appendChild(tb); return t;
}
function stKV(pairs){ const dl = stEl('dl', 'stkv'); for (const [k, v, cls] of pairs){ dl.appendChild(stEl('dt', null, k)); dl.appendChild(stEl('dd', cls || null, v)); } return dl; }
function stSteps(list, cur){ const ol = stEl('ol', 'ststeps'); list.forEach((s, i) => { const li = stEl('li', i < cur ? 'done' : i === cur ? 'now' : '', s); ol.appendChild(li); }); return ol; }
function stCanvas(w, h){ const c = mk(w, h); c.className = 'stchart'; return c; }
function stSlider(label, min, max, step, val, fmt, fn){
  const wrap = stEl('label', 'stslider'), span = stEl('span', null, label), out = stEl('b', null, fmt(val)), inp = document.createElement('input');
  inp.type = 'range'; inp.min = min; inp.max = max; inp.step = step; inp.value = val; inp.setAttribute('aria-label', label);
  inp.addEventListener('input', () => { out.textContent = fmt(+inp.value); fn(+inp.value); });
  wrap.append(span, inp, out); return wrap;
}
STN.el.close.addEventListener('click', closeStation);

/* Keep the 3D view centered in the part of the screen the panel leaves open */
function applyProjection(){
  if (!THREEOK) return;
  const w = window.innerWidth, h = window.innerHeight, base = w / h < 0.8 ? 80 : 66;
  camera.fov = base; camera.aspect = w / h; camera.clearViewOffset();
  const P = STN.el.panel, bar = $('#paintbar');
  const panel = STN.cur && P && !P.hidden ? P : paint.on && bar && !bar.hidden ? bar : null;
  if (panel){
    const r = panel.getBoundingClientRect();
    if (narrow()){
      const off = Math.max(0, h - r.top);
      if (off > 40 && off < h * 0.8){ const fh = h + off; camera.fov = 2 * Math.atan(Math.tan(base * Math.PI / 360) * fh / h) * 180 / Math.PI; camera.aspect = w / fh; camera.setViewOffset(w, fh, 0, off, w, h); }
    } else if (r.left > w / 2){
      /* Docked on the right: keep the 3D view centered in what's left */
      const off = Math.max(0, w - r.left);
      if (off > 40 && off < w * 0.7){ const fw = w + off; camera.aspect = fw / h; camera.setViewOffset(fw, h, off, 0, w, h); }
    } else {
      /* Docked on the left */
      const off = Math.max(0, r.right);
      if (off > 40 && off < w * 0.7){ const fw = w + off; camera.aspect = fw / h; camera.setViewOffset(fw, h, 0, 0, w, h); }
    }
  }
  camera.updateProjectionMatrix();
  wake();
}
