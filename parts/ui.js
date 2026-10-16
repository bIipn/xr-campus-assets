/* ================================================================
   Interface
   ================================================================ */
const ui = {
  scene:$('#scene'), intro:$('#intro'), enter:$('#bEnter'), tourStart:$('#bTourStart'), introMeta:$('#introMeta'), controlsText:$('#controlsText'), srcList:$('#srcList'),
  roomK:$('#roomK'), roomN:$('#roomN'), roomY:$('#roomY'), hint:$('#hint'), tag:$('#tag'), toast:$('#toast'), plan:$('#plan'), planC:$('#planC'),
  viewer:$('#viewer'), vArt:$('#vArt'), vKind:$('#vKind'), vTitle:$('#vTitle'), vDate:$('#vDate'), vDesc:$('#vDesc'), vMore:$('#vMore'), vQuote:$('#vQuote'), vQnote:$('#vQnote'),
  vWhere:$('#vWhere'), vPartners:$('#vPartners'), vSource:$('#vSource'), vGallery:$('#vGallery'), vPrev:$('#vPrev'), vNext:$('#vNext'), vClose:$('#vClose'),
  tour:$('#tour'), tStep:$('#tStep'), tTitle:$('#tTitle'), tDate:$('#tDate'), tText:$('#tText'), tBack:$('#tBack'), tNext:$('#tNext'), tOpen:$('#tOpen'), tEnd:$('#tEnd'),
  search:$('#search'), q:$('#q'), sCount:$('#sCount'), sResults:$('#sResults'), sClose:$('#sClose'),
  reader:$('#reader'), rdBox:$('#rdBox'), rdCover:$('#rdCover'), rdPage:$('#rdPage'), rdKick:$('#rdKick'), rdTitle:$('#rdTitle'), rdBody:$('#rdBody'), rdPrev:$('#rdPrev'), rdNext:$('#rdNext'), rdCount:$('#rdCount'), rdClose:$('#rdClose'),
  nogl:$('#nogl'), browse:$('#bBrowse')
};
const verb = COARSE ? 'Tap' : 'Click';
ui.hint.textContent = COARSE ? 'Tap the floor or use the stick to walk · Drag to look around · Tap anything to open it' : 'Click the floor or use W A S D to walk · Drag to look around · Click anything to open it';
ui.controlsText.textContent = COARSE
  ? 'Tap the floor to walk or use the stick, drag to look around, and tap exhibits, books and staff. Out in the Recess Yard, take penalties against the keeper (hold Kick to power up, aim with your view), topple the block tower and push the swings.'
  : 'Click the floor to walk, drag to look around, and click exhibits, books and staff. Keys: W A S D to move, Shift to run, Space to jump, hold F by a ball to power up a kick. Out in the Recess Yard, take penalties against the keeper, topple the block tower and push the swings.';
for (const key in SOURCES){ const s = SOURCES[key], li = document.createElement('li'), a = document.createElement('a'); a.href = s.url; a.target = '_blank'; a.rel = 'noopener'; a.textContent = s.label; li.appendChild(a); ui.srcList.appendChild(li); }

let entered = false, introOpen = true, attract = !REDUCED, attractT = 0, lastFocus = null, readerFocus = null;
let current = null, tourIdx = -1, curRoomId = null, hintTimer = 0, toastTimer = 0, fabStaff = 'margaret';
document.body.classList.add('intro-open');

function toast(msg){ ui.toast.textContent = msg; ui.toast.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => { ui.toast.hidden = true; }, 3400); }
function hideHint(){ ui.hint.classList.add('gone'); }
function setRoom(){
  const r = roomAt(cam.x, cam.z);
  if (r.id === curRoomId) return;
  curRoomId = r.id;
  if (r.gal){ const g = GALLERIES[r.gal]; ui.roomK.textContent = g.label; ui.roomN.textContent = g.name; ui.roomY.textContent = g.years; }
  else { const info = ROOM_INFO[r.id]; ui.roomK.textContent = info.k; ui.roomN.textContent = info.n; ui.roomY.textContent = info.y; }
  updateFab();
  if (paint.on && r.id !== 'studio') stopPaint();
  if (STN.cur && STN.cur.arrived && r.id !== STN.cur.room) closeStation();
  if (r.id === 'yard' && !ride.on && !setRoom.yardSeen && entered){ setRoom.yardSeen = true; toast(verb + ' a ride’s sign to try it. XR tokens are hidden out here too.'); }
  const firstTip = { studio:verb + ' the easel to start making art.', lab:verb + ' the sieve shaker, the titration stand or the pendulum to run a lab.', blueprint:verb + ' any blueprint to explore its parts, or the bench to build a model.', world:verb + ' the layer table to build a world, one layer at a time.' }[r.id];
  setRoom.seen = setRoom.seen || {};
  if (firstTip && entered && !ride.on && !paint.on && !STN.cur && !setRoom.seen[r.id]){ setRoom.seen[r.id] = true; toast(firstTip); }
}
function updateFab(){ const st = staffFor(curRoomId || 'lobby'); fabStaff = st.id; gui.askMono.textContent = st.mono; gui.askMono.style.background = st.color; gui.askName.textContent = 'Ask ' + st.name; }

function closeIntro(){
  introOpen = false; attract = false; ui.intro.hidden = true; document.body.classList.remove('intro-open');
  if (!entered){ entered = true; ui.enter.textContent = 'Back to the campus'; cam.yaw = 0; if (GFX.eased) setTimeout(() => toast('Graphics eased to ' + QUALITY[GFX.tier].label + ' after the last visit closed unexpectedly. You can switch back in Graphics.'), 900); }
  ui.scene.focus({ preventScroll:true });
  wake();
}
function openIntro(){ closeSearch(); closeStaff(); introOpen = true; ui.intro.hidden = false; document.body.classList.add('intro-open'); ui.enter.focus(); }

/* Exhibit viewer */
function fillViewer(it){
  current = it;
  if (it.scene && !ART[it.id]) ART[it.id] = drawWaxCard(it.scene);
  const src = ART[it.id].__released ? (it.scene ? drawWaxCard(it.scene) : makeArt(it)) : ART[it.id];
  ui.vArt.width = src.width; ui.vArt.height = src.height; ui.vArt.getContext('2d').drawImage(src, 0, 0);
  ui.vKind.textContent = KIND[it.kind]; ui.vTitle.textContent = it.title; ui.vDate.textContent = it.date; ui.vDesc.textContent = it.desc;
  ui.vMore.textContent = it.more || ''; ui.vMore.hidden = !it.more;
  if (it.quote){ ui.vQuote.textContent = it.quote + '”'; ui.vQnote.textContent = '— ' + it.quoteBy; ui.vQuote.hidden = false; ui.vQnote.hidden = false; }
  else { ui.vQuote.hidden = true; ui.vQnote.hidden = true; }
  ui.vWhere.textContent = it.where || '—'; ui.vPartners.textContent = it.partners || '—';
  ui.vSource.textContent = '';
  srcList(it.src).forEach((s, i) => { if (i) ui.vSource.append(', '); const a = document.createElement('a'); a.href = s.url; a.target = '_blank'; a.rel = 'noopener'; a.textContent = s.label; ui.vSource.appendChild(a); });
  ui.vGallery.textContent = it.hall || (it.g ? 'Gallery ' + it.g + ' · ' + GALLERIES[it.g].name : 'The Reading Room');
  const inList = ITEMS.includes(it) || WAX_ITEMS.includes(it); ui.vPrev.hidden = !inList; ui.vNext.hidden = !inList;
  noteExhibit(it);
}
function itemView(it){ return it === FREEDOM ? PLACES.find((p) => p.id === 'freedomBoard').view() : it.scene ? waxView(it.scene) : viewFor(it); }
function openItem(it, opts){
  opts = opts || {};
  if (THREEOK && opts.walk) goView(itemView(it));
  fillViewer(it);
  if (ui.viewer.hidden){ lastFocus = document.activeElement; ui.viewer.hidden = false; ui.tour.hidden = true; }
  ui.vClose.focus(); hideHint();
}
function closeViewer(){
  if (ui.viewer.hidden) return;
  ui.viewer.hidden = true;
  if (tourIdx >= 0) ui.tour.hidden = false;
  if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll:true }); else ui.scene.focus({ preventScroll:true });
}
function stepItem(dir){ const list = WAX_ITEMS.includes(current) ? WAX_ITEMS : ITEMS, i = list.indexOf(current); if (i < 0) return; openItem(list[(i + dir + list.length) % list.length], { walk:true }); }

/* Book reader */
const rd = { book:null, page:0 };
function openBook(b, page){
  if (introOpen) closeIntro();
  rd.book = b; rd.page = clamp(page || 0, 0, b.pages.length);
  ui.rdCover.getContext('2d').drawImage(drawBookCover(b, 384, 526), 0, 0);
  if (ui.reader.hidden){ readerFocus = document.activeElement; ui.reader.hidden = false; }
  renderPage(); ui.rdClose.focus(); hideHint();
}
function blockEl(b){
  if (typeof b === 'string'){ const p = document.createElement('p'); p.textContent = b; return p; }
  if (b.li){ const ul = document.createElement('ul'); for (const t of b.li){ const li = document.createElement('li'); li.textContent = t; ul.appendChild(li); } return ul; }
  if (b.q){ const q = document.createElement('blockquote'); q.textContent = b.q; return q; }
  if (b.note){ const p = document.createElement('p'); p.className = 'note'; p.textContent = 'In plain words: ' + b.note; return p; }
  if (b.code){ const pre = document.createElement('pre'); pre.textContent = b.code; return pre; }
  return document.createElement('span');
}
function renderPage(){
  const b = rd.book, p = rd.page;
  ui.rdBox.classList.toggle('inside', p > 0);
  ui.rdKick.textContent = SUBJ[b.subject].name + (p ? ' · ' + b.title : '');
  ui.rdBody.textContent = '';
  if (p === 0){
    ui.rdTitle.textContent = b.title;
    const sub = document.createElement('p'); sub.className = 'sub'; sub.textContent = b.sub; ui.rdBody.appendChild(sub);
    const intro = document.createElement('p'); intro.className = 'note'; intro.textContent = 'A short primer from the XRLibraries Campus library. Contents:'; ui.rdBody.appendChild(intro);
    const toc = document.createElement('ul'); toc.className = 'toc';
    b.pages.forEach((pg, i) => { const li = document.createElement('li'), bt = document.createElement('button'), n = document.createElement('span'); bt.type = 'button'; n.textContent = String(i + 1); bt.append(n, document.createTextNode(pg.h)); bt.addEventListener('click', () => { rd.page = i + 1; renderPage(); ui.rdPage.focus({ preventScroll:true }); }); li.appendChild(bt); toc.appendChild(li); });
    ui.rdBody.appendChild(toc);
  } else {
    const pg = b.pages[p - 1];
    ui.rdTitle.textContent = pg.h;
    notePage(b, p);
    for (const blk of pg.b) ui.rdBody.appendChild(blockEl(blk));
  }
  ui.rdCount.textContent = p === 0 ? 'Contents' : 'Page ' + p + ' of ' + b.pages.length;
  ui.rdPrev.disabled = p === 0;
  ui.rdNext.textContent = p === 0 ? 'Start reading' : p === b.pages.length ? 'Close book' : 'Next page';
  ui.rdPage.scrollTop = 0;
}
function turnPage(d){ if (!rd.book) return; const n = rd.page + d; if (n > rd.book.pages.length){ closeBook(); return; } if (n < 0) return; rd.page = n; renderPage(); }
function closeBook(){ if (ui.reader.hidden) return; ui.reader.hidden = true; if (readerFocus && readerFocus.focus) readerFocus.focus({ preventScroll:true }); else ui.scene.focus({ preventScroll:true }); }

/* Tour */
const STOPS = [
  { kind:'lobby', title:'Welcome to the XRLibraries Campus', date:'Lobby', text:'Three galleries and the Wax Hall tell XRLibraries’ story. After the museum, the tour visits the reading room, the four workshop rooms of the school and the Recess Yard. Margaret, the guide by the door, answers questions anytime.', view:() => lobbyView() },
  ...ITEMS.map((it) => ({ kind:'item', item:it })),
  { kind:'wax', title:'The Wax Hall', date:'Living History', text:'Through the doorway at the end of Gallery 3, wax figures act out XRLibraries’ story in twelve scenes, from the first VR stations in 2016 to the 2025 Marin County Fair. Each scene comes to life as you walk up. The figures are reenactors, not likenesses of real people.', view:() => ({ x:0, z:-43.2, yaw:0, pitch:0.06 }) },
  ...WAX_ITEMS.map((it) => ({ kind:'item', item:it })),
  { kind:'library', title:'The Reading Room', date:'Library', text:'The library has ' + BOOKS.length + ' short books about XR and more, open to read on the featured table and on the ends of the stacks. Rosa at the reference desk answers questions from them.', view:() => ({ x:-13.4, z:-3, yaw:Math.PI / 2, pitch:0.08 }), open:'Read a book', act:() => openBook(BOOK['what-is-xr'], 0) },
  { kind:'studio', title:'Room 101: 3D Art Studio', date:'Workshop School', text:'Every class in the Workshop School is a hands-on workshop. Here you paint in the air with neon, chrome, ribbon and rainbow brushes, stamp 3D shapes, mirror your strokes and switch to a blank canvas.', view:() => PAINT_SPOT, open:'Start making art', act:() => { endTour(); startPaint(); } },
  { kind:'lab', title:'Room 102: Science Lab', date:'Workshop School', text:'A working lab with goggles on. Run a sieve analysis to measure the grain sizes in a sand sample, find the concentration of a mystery acid by titration, and measure gravity with a pendulum.', view:() => ({ x:29, z:-5.9, yaw:0, pitch:-0.06 }), open:'Start the sieve test', act:() => { endTour(); openStation('sieve'); } },
  { kind:'blueprint', title:'Room 103: Blueprint Lab', date:'Workshop School', text:'Five real-world blueprints: a car, an excavator, a house, a truss bridge and a computer. Tap any part to learn its name, what it does and how you could build a model, then build a model car or building at the bench.', view:() => ({ x:18.1, z:3.6, yaw:Math.PI, pitch:0.03 }), open:'Open the car blueprint', act:() => { endTour(); openBp('car', null); } },
  { kind:'world', title:'Room 104: World Builder Studio', date:'Workshop School', text:'How do you build a world like this campus? Build a mini world on the layer table one step at a time, from a sketch to a live website, and read the World Builder’s Handbook to start your own.', view:() => ({ x:29, z:0.6, yaw:Math.PI, pitch:-0.18 }), open:'Build a world', act:() => { endTour(); openStation('diorama'); } },
  { kind:'yard', title:'The Recess Yard', date:'Out the back of the school', text:'Recess is for fun in XR: ride the Comet Coaster, take the Sky Drop for a view of the whole campus, or go on an Ocean Dive with sea creatures. Coach Rae can help, and XR tokens are hidden all over the campus.', view:() => ({ x:38.6, z:-3, yaw:-Math.PI / 2, pitch:0.06 }), open:'Ride the coaster', act:() => { endTour(); openRide('coaster'); } }
];
function startTour(){ closeSearch(); closeViewer(); closeStaff(); stopPaint(); closeStation(); closeBp(); tourIdx = 0; document.body.classList.add('touring'); hideHint(); showStop(); }
function endTour(){ if (tourIdx < 0) return; tourIdx = -1; ui.tour.hidden = true; document.body.classList.remove('touring'); ui.scene.focus({ preventScroll:true }); }
function showStop(){
  const s = STOPS[tourIdx];
  ui.tour.hidden = false;
  ui.tStep.textContent = 'Stop ' + (tourIdx + 1) + ' of ' + STOPS.length;
  if (s.kind === 'item'){
    const it = s.item;
    ui.tTitle.textContent = it.title; ui.tDate.textContent = (it.scene ? 'Living History · Scene ' + it.scene.n : KIND[it.kind]) + ' · ' + it.date; ui.tText.textContent = it.desc;
    ui.tOpen.hidden = false; ui.tOpen.textContent = it.scene ? 'Open scene card' : 'Open exhibit';
    if (THREEOK) goView(itemView(it));
  } else {
    ui.tTitle.textContent = s.title; ui.tDate.textContent = s.date; ui.tText.textContent = s.text;
    ui.tOpen.hidden = !s.open; ui.tOpen.textContent = s.open || '';
    if (THREEOK) goView(s.view());
  }
  ui.tBack.disabled = tourIdx === 0;
  ui.tNext.textContent = tourIdx === STOPS.length - 1 ? 'Explore on your own' : 'Next stop';
}

/* Search across the campus */
function renderResults(){
  const raw = ui.q.value.trim(), q = raw.toLowerCase();
  const has = (txt) => !q || txt.toLowerCase().includes(q);
  const items = ITEMS.concat([FREEDOM], WAX_ITEMS).filter((it) => has([it.title, it.date, it.desc, it.more || '', it.where || '', it.partners || '', KIND[it.kind], it.quote || '', it.scene ? 'wax hall living history reenactment' : it.g ? GALLERIES[it.g].name : 'library'].join(' ')));
  const books = BOOKS.filter((b) => has([b.title, b.sub, SUBJ[b.subject].name, b.pages.map((p) => p.h + ' ' + p.b.map(blockText).join(' ')).join(' ')].join(' ')));
  const places = q.length > 2 ? PLACES.filter((p) => p.names.some((n) => n.includes(q) || q.includes(n)) || p.label.toLowerCase().includes(q)) : [];
  /* Blueprint parts and lab lessons, so “radiator” or “titration” finds the right room */
  const parts = [];
  if (q.length > 2) for (const id of BP_ORDER) BP_INFO[id].parts.forEach((p, i) => { if (has([p.name, p.short, p.what].join(' ')) && parts.length < 8) parts.push({ id, i, p }); });
  const labs = q.length > 2 ? Object.keys(STATION_CARDS).filter((k) => has([STATION_CARDS[k].t, STATION_CARDS[k].m, LESSONS.filter((L) => L.station === k).map((L) => L.title + ' ' + L.text).join(' ')].join(' '))) : [];
  ui.sResults.textContent = '';
  const n = items.length + books.length + places.length + parts.length + labs.length;
  ui.sCount.textContent = q ? n + (n === 1 ? ' match' : ' matches') : ITEMS.length + ' exhibits · ' + BOOKS.length + ' books';
  if (!n){ const li = document.createElement('li'); li.className = 'empty'; li.textContent = 'Nothing matches “' + raw + '”. Try VR, Nevada, 360 or ocean.'; ui.sResults.appendChild(li); return; }
  const group = (name, list, row) => {
    if (!list.length) return;
    const h = document.createElement('li'); h.className = 'sgroup'; h.textContent = name; ui.sResults.appendChild(h);
    for (const x of list){
      const [k, t, m, act] = row(x), li = document.createElement('li'), b = document.createElement('button');
      b.type = 'button'; b.className = 'result';
      const ks = document.createElement('span'); ks.className = 'rk'; ks.textContent = k;
      const ts = document.createElement('span'); ts.className = 'rt'; ts.textContent = t;
      const ms = document.createElement('span'); ms.className = 'rm'; ms.textContent = m;
      b.append(ks, ts, ms); b.addEventListener('click', () => { closeSearch(); if (tourIdx >= 0) endTour(); act(); });
      li.appendChild(b); ui.sResults.appendChild(li);
    }
  };
  group('Places', places, (p) => ['Place', p.label, 'Walk there', () => { if (THREEOK) goView(p.view()); }]);
  group('Workshops', labs, (k) => ['Hands-on', STATION_CARDS[k].t, STATION_CARDS[k].k, () => { if (THREEOK) openStation(k); }]);
  group('Blueprints', parts, (x) => ['Part ' + (x.i + 1), x.p.name, BP_INFO[x.id].title + ' blueprint · Room 103', () => openBp(x.id, x.i, { walk:THREEOK })]);
  group('Museum', items, (it) => [KIND[it.kind], it.title, itemWhere(it) + ' · ' + it.date, () => openItem(it, { walk:THREEOK })]);
  group('Library', books, (b) => [SUBJ[b.subject].name, b.title, b.sub, () => openBook(b, 0)]);
}
function openSearch(q){ if (introOpen && THREEOK) closeIntro(); closeStaff(); closeStation(); ui.search.hidden = false; if (typeof q === 'string') ui.q.value = q; renderResults(); ui.q.focus(); }
function closeSearch(){ ui.search.hidden = true; }

/* Virtual staff chat */
const AI_END = ['not_granted', 'sampling_disabled', 'not_declared', 'capability_disabled', 'capability_removed', 'session_expired', 'tools_unavailable'];
const chat = { active:'margaret', sample:null, ai:false, busy:false, ctl:null, state:{} };
for (const id in STAFF) chat.state[id] = { msgs:[], turns:[], greeted:false };
const gui = { panel:$('#guide'), msgs:$('#gMsgs'), chips:$('#gChips'), form:$('#gForm'), q:$('#gq'), send:$('#gSend'), close:$('#gClose'), name:$('#gName'), sub:$('#gSub'), mono:$('#gMono'), note:$('#gNote'), label:$('#gLabel'), ask:$('#askBtn'), askMono:$('#askMono'), askName:$('#askName') };
function aiOn(){ return chat.ai && !!chat.sample; }
const CHIPS = {
  margaret:['What is XRLibraries?', 'When did XRLibraries start?', 'Take me to the Wax Hall', 'What is Project SANDI?'],
  rosa:['What is the difference between VR and AR?', 'How do I make a 360 video?', 'Recommend a book', 'What is Freedom to Read?'],
  hale:['Start painting', 'Give me a blank canvas', 'What workshops are there?', 'How do blueprints work?'],
  rae:['Ride the coaster', 'What’s on the Ocean Dive?', 'Where are the hidden tokens?', 'Is it scary?']
};
const GREET = {
  margaret:'Welcome to the XRLibraries Campus! I’m Margaret, the museum guide. Ask me about XRLibraries’ story, any exhibit, or where to find the library and the paint studio.',
  rosa:'Hi, I’m Rosa, the reference librarian. Ask me a question and I’ll find the answer in our books, or name a topic and I’ll find you something to read.',
  hale:'Welcome to the Workshop School! I’m Mr. Hale. Room 101 is the 3D Art Studio, 102 is the Science Lab, 103 is the Blueprint Lab and 104 is the World Builder Studio. Ask me about any of them, or say “start painting.”',
  rae:'Hey, welcome to recess! I’m Coach Rae. Ride the Comet Coaster, take the Sky Drop, or go on an Ocean Dive. Ask me anything about the rides, or about the XR tokens hidden around the campus.'
};
function staffNote(id){ const n = STAFF[id].name; return aiOn() ? n + ' answers common questions right away. Harder ones use AI through your Claude account, after asking your permission.' : n + ' answers common questions from what this campus knows.'; }
function refreshStaffHeader(){ const st = STAFF[chat.active]; gui.sub.textContent = st.role + (aiOn() ? ' · AI' : ''); gui.note.textContent = staffNote(chat.active); }
function openStaff(id){
  id = id || fabStaff || 'margaret';
  if (introOpen) closeIntro();
  closeSearch(); if (tourIdx >= 0) endTour(); if (paint.on && id !== 'hale') stopPaint(); closeStation(); closeBp();
  if (chat.active !== id && chat.ctl) chat.ctl.abort();
  chat.active = id;
  const st = STAFF[id], S = chat.state[id];
  gui.name.textContent = st.name; gui.mono.textContent = st.mono; gui.mono.style.background = st.color; gui.label.textContent = 'Ask ' + st.name;
  gui.q.placeholder = id === 'rosa' ? 'Ask a question or name a topic' : id === 'hale' ? 'Ask about art, labs, blueprints or worlds' : id === 'rae' ? 'Ask about the rides' : 'Ask about XRLibraries or an exhibit';
  refreshStaffHeader();
  gui.panel.hidden = false; document.body.classList.add('guide-open'); hideHint();
  if (!S.greeted){ S.greeted = true; S.msgs.push({ who:'staff', text:GREET[id], cards:[] }); staffTalk(id, GREET[id]); }
  renderMsgs(); renderChips(S.msgs.length <= 1 ? id : null);
  if (!COARSE) gui.q.focus({ preventScroll:true });
}
function closeStaff(){
  if (gui.panel.hidden) return;
  if (chat.ctl) chat.ctl.abort();
  gui.panel.hidden = true; document.body.classList.remove('guide-open');
  ui.scene.focus({ preventScroll:true });
}
function narrow(){ return window.innerWidth <= 760; }
function renderChips(id){
  gui.chips.textContent = '';
  if (!id) return;
  for (const c of CHIPS[id]){ const b = document.createElement('button'); b.type = 'button'; b.className = 'chip'; b.textContent = c; b.addEventListener('click', () => sendStaff(c)); gui.chips.appendChild(b); }
}
function renderMsgs(){
  gui.msgs.textContent = '';
  const S = chat.state[chat.active];
  let lastYou = null;
  for (const m of S.msgs){ m.el = drawMsg(m); if (m.who === 'you') lastYou = m; }
  if (lastYou) showReply(lastYou); else gui.msgs.scrollTop = 0;
}
function drawMsg(m){
  const el = document.createElement('div'); el.className = 'msg ' + (m.who === 'you' ? 'you' : 'guide') + (m.pending ? ' pending' : '');
  const t = document.createElement('span'); t.className = 't'; t.textContent = m.text; el.appendChild(t); m.t = t;
  if (m.cards && m.cards.length) el.appendChild(cardsEl(m.cards));
  gui.msgs.appendChild(el); gui.msgs.scrollTop = gui.msgs.scrollHeight;
  return el;
}
function cardBtn(label, fn){ const b = document.createElement('button'); b.type = 'button'; b.className = 'btn'; b.textContent = label; b.addEventListener('click', fn); return b; }
function cardsEl(cards){
  const box = document.createElement('div'); box.className = 'gcards';
  for (const c of cards){
    const card = document.createElement('div'); card.className = 'gcard';
    const k = document.createElement('span'); k.className = 'rk';
    const t = document.createElement('span'); t.className = 'rt';
    const m = document.createElement('span'); m.className = 'rm';
    const row = document.createElement('div'); row.className = 'row';
    if (c.type === 'item'){
      k.textContent = KIND[c.it.kind]; t.textContent = c.it.title; m.textContent = itemWhere(c.it) + ' · ' + c.it.date;
      if (THREEOK) row.appendChild(cardBtn('Take me there', () => goToItem(c.it)));
      row.appendChild(cardBtn('Open', () => openItem(c.it, { walk:THREEOK })));
    } else if (c.type === 'book'){
      k.textContent = SUBJ[c.b.subject].name; t.textContent = c.b.title; m.textContent = c.page ? 'Page ' + c.page + ' of ' + c.b.pages.length : c.b.sub;
      row.appendChild(cardBtn(c.page ? 'Read page ' + c.page : 'Read', () => openBook(c.b, c.page || 0)));
      if (THREEOK) row.appendChild(cardBtn('Find the shelf', () => goToPlace({ view:() => SHELF_VIEWS[c.b.subject] })));
    } else if (c.type === 'place'){
      k.textContent = 'Place'; t.textContent = c.p.label; m.textContent = '';
      if (THREEOK) row.appendChild(cardBtn('Take me there', () => goToPlace(c.p)));
    } else if (c.type === 'action'){
      k.textContent = 'Workshop'; t.textContent = c.title; m.textContent = c.sub || '';
      row.appendChild(cardBtn(c.label, c.fn));
    } else if (c.type === 'station'){
      const S = STATION_CARDS[c.id] || {};
      k.textContent = S.k || 'Workshop'; t.textContent = S.t || c.id; m.textContent = S.m || '';
      if (THREEOK) row.appendChild(cardBtn(S.go || 'Start', () => { if (narrow()) closeStaff(); openStation(c.id, c.opts); }));
    } else if (c.type === 'bp'){
      const B = BP_INFO[c.id], p = c.part != null ? B.parts[c.part] : null;
      k.textContent = 'Blueprint ' + B.dwg; t.textContent = p ? p.name : B.title; m.textContent = p ? B.title + ' · Room 103' : 'Room 103 · ' + B.parts.length + ' parts';
      row.appendChild(cardBtn(p ? 'Show the part' : 'Open blueprint', () => { if (narrow()) closeStaff(); openBp(c.id, c.part == null ? null : c.part, { walk:THREEOK }); }));
    } else if (c.type === 'ride'){
      k.textContent = 'Ride'; t.textContent = RIDES[c.id].name; m.textContent = c.id === 'dive' ? 'Recess Yard · about a minute' : 'Recess Yard · Gentle mode too';
      if (THREEOK){ row.appendChild(cardBtn(c.id === 'dive' ? 'Start the dive' : 'Ride now', () => { if (narrow()) closeStaff(); openRide(c.id); })); row.appendChild(cardBtn('Take me there', () => goToPlace(PLACES.find((p) => p.id === c.id)))); }
    } else if (c.type === 'badges'){
      k.textContent = 'Recess rewards'; t.textContent = 'Badges and XR tokens'; m.textContent = prog.badges.size + ' of ' + BADGES.length + ' badges · ' + prog.tokens.size + ' of ' + TOKENS.length + ' tokens';
      row.appendChild(cardBtn('Open badges', openBadges));
    }
    card.append(k, t); if (m.textContent) card.appendChild(m); card.appendChild(row); box.appendChild(card);
  }
  return box;
}
function showReply(asked){ if (asked && asked.el) gui.msgs.scrollTop = Math.max(0, asked.el.offsetTop - 14); }
function goToItem(it){ if (!THREEOK){ openItem(it, { walk:false }); return; } if (tourIdx >= 0) endTour(); if (narrow()) closeStaff(); goView(itemView(it)); }
function goToPlace(p){ if (!THREEOK) return; if (tourIdx >= 0) endTour(); if (narrow()) closeStaff(); goView(p.view()); }
function setBusy(b){ chat.busy = b; gui.send.textContent = b ? 'Stop' : 'Ask'; gui.send.classList.toggle('primary', !b); }
function paintCard(){ return { type:'action', title:'3D Art Studio', sub:'Room 101', label:'Start making art', fn:() => { if (narrow()) closeStaff(); startPaint(); } }; }
const STATION_CARDS = {
  sieve:{ k:'Science Lab · Room 102', t:'Sieve analysis (PSD)', m:'Measure the grain sizes in sand', go:'Start the test' },
  titration:{ k:'Science Lab · Room 102', t:'Acid–base titration', m:'Find the concentration of a mystery acid', go:'Start titrating' },
  pendulum:{ k:'Science Lab · Room 102', t:'Pendulum', m:'Measure gravity with a string and a weight', go:'Start swinging' },
  bench:{ k:'Blueprint Lab · Room 103', t:'Model bench', m:'Build a model car or building', go:'Start building' },
  diorama:{ k:'World Builder Studio · Room 104', t:'Layer table', m:'Build a mini world, one layer at a time', go:'Build a world' }
};
function stationCard(id, opts){ return { type:'station', id, opts }; }
function bpCard(id, part){ return { type:'bp', id, part }; }
function afterReply(r){
  if (r.go) setTimeout(() => { if (r.go.type === 'item') goToItem(r.go.it); else goToPlace(r.go.p); }, 600);
  if (r.action === 'paint' || r.action === 'paintBlank') setTimeout(() => { if (narrow()) closeStaff(); startPaint(r.action === 'paintBlank' ? 'blank' : null); }, 500);
  if (r.action && r.action.startsWith('station:')) setTimeout(() => { if (narrow()) closeStaff(); openStation(r.action.slice(8)); }, 500);
  if (r.action && r.action.startsWith('bp:')) setTimeout(() => { if (narrow()) closeStaff(); openBp(r.action.slice(3), null); }, 500);
  const rideId = r.ride || (r.action && r.action.startsWith('ride:') ? r.action.slice(5) : null);
  if (rideId && RIDES[rideId]) setTimeout(() => { if (narrow()) closeStaff(); openRide(rideId); }, 600);
}
function staffRules(id){
  const role = id === 'rosa'
    ? 'You are Rosa, the virtual reference librarian in the campus library. Answer any question a student asks accurately and simply, the way a good reference librarian would, including general knowledge. When one of the books below covers the topic, recommend it.'
    : id === 'hale'
    ? 'You are Mr. Hale, the virtual workshop teacher in the Workshop School. Room 101 is the 3D Art Studio: visitors paint in the air with Neon, Paint, Ribbon, Chrome, Rainbow, Beads and Sparkle brushes, stamp 3D shapes, use Mirror or ×6 symmetry, spin their work on a turntable and switch to a blank or night canvas. Room 102 is the Science Lab, with a sieve analysis of sand (particle size distribution, PSD), an acid–base titration and a pendulum that measures gravity. Room 103 is the Blueprint Lab, with labeled blueprints of a car, an excavator, a house, a truss bridge and a computer, plus a bench for building a model car or building. Room 104 is the World Builder Studio, which shows how a 3D world like this campus is made, layer by layer. Help students with art ideas, science, engineering and making their own worlds, and explain things simply and accurately.'
    : id === 'rae'
    ? 'You are Coach Rae, the virtual recess coach in the Recess Yard behind the Workshop School. Help visitors pick a ride and stay comfortable (every ride has a Gentle mode and an Exit button), and give hints about the hidden XR tokens without naming exact spots.'
    : 'You are Margaret, the virtual museum guide at the museum door. Help visitors learn XRLibraries’ story and find exhibits.';
  return [
    role + ' You work in the XRLibraries Campus, an unofficial concept that Ev Holt made with Walk the Archive for XRLibraries. It is not an official XRLibraries site.',
    'Rules:',
    '- Reply in 1 to 3 short, warm, plain sentences' + (id === 'rosa' ? ' (up to 4 for hard questions)' : '') + '. No lists and no markdown.',
    '- You are a virtual staff member, not a person. Never claim to be human.',
    '- About XRLibraries, use only the facts and exhibits below. Never invent XRLibraries facts, numbers, people or dates. If you do not know, say so.',
    '- Keep everything suitable for students, and do not share personal opinions on politics.',
    '- After your reply, add these lines when they apply, each on its own line:',
    'ITEMS: up to 2 exhibit ids from the list, or none',
    'BOOKS: up to 2 book ids from the list, or none',
    'GO: one place id or exhibit id, only if the visitor asked to be taken somewhere',
    'RIDE: coaster, drop or dive, only if the visitor asked to ride or dive right now',
    '',
    'Recess Yard: the Comet Coaster (lift hill about ' + COASTER.stats.height + ' m, top speed about ' + COASTER.stats.kmh + ' km/h, one loop), the Sky Drop (a tower about ' + DROP.h + ' m tall; seats rise about 30 m) and the Ocean Dive (a made-up reef inspired by ocean VR like Hydrous, with a coral reef, kelp forest, fish schools, a sea turtle, a whale shark, a manta ray and jellyfish). There are ' + TOKENS.length + ' hidden XR tokens and ' + BADGES.length + ' badges to collect. These rides are part of this concept, not real XRLibraries programs.',
    '',
    'Facts:', FACTS.map((f) => '- ' + f.text).join('\n'),
    '',
    'Exhibits (id | location | title | date | description):',
    ITEMS.concat([FREEDOM], WAX_ITEMS).map((it) => [it.id, itemWhere(it), it.title, it.date, it.desc + (it.more ? ' ' + it.more : '')].join(' | ')).join('\n'),
    '',
    'Books (id | section | title | pages):',
    BOOKS.map((b) => [b.id, SUBJ[b.subject].name, b.title + ': ' + b.sub, b.pages.map((p) => p.h).join('; ')].join(' | ')).join('\n'),
    '',
    'Places (id | name):', PLACES.map((p) => p.id + ' | ' + p.label).join('\n')
  ].join('\n');
}
function visibleText(t){ return String(t).replace(/(^|\n)\s*(ITEMS|BOOKS|GO|RIDE)\s*:[\s\S]*$/i, '').trim(); }
function parseReply(t){
  const s = String(t), cards = [];
  const ids = (re) => { const m = s.match(re); return m ? m[1].split(/[\s,]+/).map((x) => x.trim().toLowerCase()).filter((x) => x && x !== 'none') : []; };
  for (const id of ids(/ITEMS\s*:\s*([^\n]*)/i).slice(0, 2)){ const it = ITEMS.concat(WAX_ITEMS).find((i) => i.id === id) || (id === 'freedom' ? FREEDOM : null); if (it) cards.push(itemCard(it)); }
  for (const id of ids(/BOOKS\s*:\s*([^\n]*)/i).slice(0, 2)){ if (BOOK[id]) cards.push(bookCard(BOOK[id])); }
  let go = null; const gm = s.match(/GO\s*:\s*([A-Za-z0-9-]+)/i);
  if (gm){ const g = gm[1].toLowerCase(), it = ITEMS.concat(WAX_ITEMS).find((i) => i.id === g), p = PLACES.find((x) => x.id.toLowerCase() === g); go = it ? { type:'item', it } : p ? { type:'place', p } : null; }
  const rm = s.match(/RIDE\s*:\s*(coaster|drop|dive)\b/i);
  return { text:visibleText(s) || 'Here’s what I found.', cards, go, ride:rm ? rm[1].toLowerCase() : null };
}
async function sendStaff(text){
  text = String(text || '').trim();
  if (!text || chat.busy) return;
  const id = chat.active, S = chat.state[id];
  gui.chips.textContent = ''; gui.q.value = '';
  const asked = { who:'you', text }; S.msgs.push(asked); asked.el = drawMsg(asked);
  award('curious');
  const local = presetAnswer(id, text);
  if (local.action === 'paintOffer'){ local.cards = (local.cards || []).concat([paintCard()]); }
  if (local.action === 'workshops'){ local.cards = [paintCard(), stationCard('sieve'), bpCard('car'), stationCard('diorama')]; }
  if (local.conf >= 0.6 || !aiOn()){
    const m = { who:'staff', text:local.text, cards:local.cards || [] }; S.msgs.push(m); m.el = drawMsg(m); showReply(asked); staffTalk(id, local.text);
    S.turns.push({ role:'user', content:text }, { role:'assistant', content:local.text });
    afterReply(local);
    return;
  }
  S.turns.push({ role:'user', content:text });
  const m = { who:'staff', text:'Thinking…', pending:true, cards:[] }; S.msgs.push(m); m.el = drawMsg(m);
  const ctl = new AbortController(); chat.ctl = ctl; setBusy(true);
  try {
    const res = await chat.sample([{ role:'user', content:staffRules(id) }].concat(S.turns.slice(-10)), {
      modelTier:'quick', cache:false, signal:ctl.signal,
      onText:({ text:t }) => { m.el.classList.remove('pending'); m.text = visibleText(t) || '…'; m.t.textContent = m.text; gui.msgs.scrollTop = gui.msgs.scrollHeight; }
    });
    const r = parseReply(res.text);
    m.pending = false; m.el.classList.remove('pending'); m.text = r.text; m.t.textContent = r.text; m.cards = r.cards; staffTalk(id, r.text);
    if (r.cards.length) m.el.appendChild(cardsEl(r.cards));
    S.turns.push({ role:'assistant', content:r.text });
    showReply(asked); afterReply(r);
  } catch (e) {
    const code = (e && e.code) || 'upstream_error';
    m.pending = false; m.el.classList.remove('pending');
    if (code === 'cancelled'){ const part = e.text ? visibleText(e.text) : ''; m.text = part || 'Stopped.'; m.t.textContent = m.text; S.turns.push({ role:'assistant', content:m.text }); }
    else {
      if (AI_END.includes(code)){ chat.ai = false; S.turns = []; if (chat.active === id) refreshStaffHeader(); } else S.turns.pop();
      m.text = (code === 'rate_limited' ? 'I’m a little busy, so here’s what I know. ' : '') + local.text; m.t.textContent = m.text; m.cards = local.cards || [];
      if (m.cards.length) m.el.appendChild(cardsEl(m.cards));
      showReply(asked); afterReply(local);
    }
  } finally { if (chat.ctl === ctl) chat.ctl = null; setBusy(false); }
}
gui.form.addEventListener('submit', (e) => { e.preventDefault(); if (chat.busy){ if (chat.ctl) chat.ctl.abort(); return; } sendStaff(gui.q.value); });
gui.close.addEventListener('click', closeStaff);
gui.ask.addEventListener('click', () => openStaff(fabStaff));
async function initAI(){
  if (!(window.claude && typeof window.claude.use === 'function')) return;
  try { const smp = await window.claude.use('sample'); if (smp){ chat.sample = smp; chat.ai = true; if (!gui.panel.hidden) refreshStaffHeader(); } } catch (_) {}
}

/* Paint studio controls */
const pb = { bar:$('#paintbar'), tools:$('#pbTools'), colors:$('#pbColors'), custom:$('#pbCustom'), customWrap:$('#pbCustomWrap'), size:$('#pbSize'), sym:$('#pbSym'), canvas:$('#pbCanvas'), spin:$('#pbSpin'), dist:$('#pbDist'), mode:$('#pbMode'), undo:$('#pbUndo'), clear:$('#pbClear'), save:$('#pbSave'), done:$('#pbDone'), told:false };
let downloadsCap = null, clearArmed = 0;
function buildPaintBar(){
  const lab = (t) => { const s = document.createElement('span'); s.className = 'pblab'; s.textContent = t; return s; };
  const chip = (id, name, kind) => {
    const b = document.createElement('button'); b.type = 'button'; b.className = 'pbt'; b.setAttribute('role', 'radio'); b.dataset.k = kind; b.dataset.id = id;
    const ic = paintIcon(id); ic.setAttribute('aria-hidden', 'true'); const sp = document.createElement('span'); sp.textContent = name; b.append(ic, sp);
    b.addEventListener('click', () => {
      if (kind === 'b'){ paint.brush = id; paint.shape = null; }
      else { if (!pb.told){ pb.told = true; toast('Shapes take your brush’s finish: Neon glows, Chrome shines, Rainbow changes color.'); } paint.shape = id; }
      updatePaintButtons();
    });
    return b;
  };
  pb.tools.appendChild(lab('Brushes'));
  for (const B of BRUSHES) pb.tools.appendChild(chip(B.id, B.name, 'b'));
  const sep = document.createElement('span'); sep.className = 'pbsep'; pb.tools.appendChild(sep);
  pb.tools.appendChild(lab('Shapes'));
  for (const S of SHAPES) pb.tools.appendChild(chip(S.id, S.name, 's'));
  PAINT_COLORS.forEach((c) => { const b = document.createElement('button'); b.type = 'button'; b.className = 'sw'; b.setAttribute('role', 'radio'); b.setAttribute('aria-label', 'Color ' + c); b.style.background = c; b.dataset.c = c; b.addEventListener('click', () => { paint.color = c; updatePaintButtons(); }); pb.colors.appendChild(b); });
  pb.custom.addEventListener('input', () => { paint.color = pb.custom.value.toLowerCase(); updatePaintButtons(); });
  pb.size.querySelectorAll('button').forEach((b) => b.addEventListener('click', () => { paint.sizeI = +b.dataset.i; updatePaintButtons(); }));
  pb.sym.querySelectorAll('button').forEach((b) => b.addEventListener('click', () => { paint.sym = b.dataset.v; updatePaintButtons(); if (paint.sym) toast(paint.sym === 'x' ? 'Mirror: every stroke repeats on the other side of the room’s center line.' : '×6: every stroke repeats six times around the middle of the room, like a snowflake.'); }));
  pb.canvas.querySelectorAll('button').forEach((b) => b.addEventListener('click', () => { setPaintCanvas(b.dataset.v); updatePaintButtons(); }));
  pb.spin.addEventListener('click', () => { paint.spin = !paint.spin; updatePaintButtons(); wake(); });
  pb.dist.addEventListener('input', () => { paint.dist = +pb.dist.value; });
  pb.mode.addEventListener('click', () => { paint.look = !paint.look; document.body.classList.toggle('looking', paint.look); if (paint.tip) paint.tip.visible = false; updatePaintButtons(); wake(); });
  pb.undo.addEventListener('click', undoPaint);
  pb.clear.addEventListener('click', () => { if (Date.now() - clearArmed < 3000){ clearArmed = 0; clearPaint(); pb.clear.textContent = 'Clear'; return; } clearArmed = Date.now(); pb.clear.textContent = 'Tap again'; setTimeout(() => { if (clearArmed && Date.now() - clearArmed >= 3000){ clearArmed = 0; pb.clear.textContent = 'Clear'; } }, 3100); });
  pb.save.addEventListener('click', savePicture);
  pb.done.addEventListener('click', stopPaint);
  updatePaintButtons();
}
function updatePaintButtons(){
  pb.tools.querySelectorAll('.pbt').forEach((b) => {
    const on = b.dataset.k === 'b' ? !paint.shape && paint.brush === b.dataset.id : paint.shape === b.dataset.id;
    b.setAttribute('aria-checked', String(on)); b.classList.toggle('fin', b.dataset.k === 'b' && !!paint.shape && paint.brush === b.dataset.id);
  });
  let preset = false;
  pb.colors.querySelectorAll('.sw').forEach((b) => { const on = b.dataset.c === paint.color; if (on) preset = true; b.setAttribute('aria-checked', String(on)); });
  pb.customWrap.classList.toggle('on', !preset);
  if (!preset && pb.custom.value !== paint.color) pb.custom.value = paint.color;
  pb.size.querySelectorAll('button').forEach((b) => b.setAttribute('aria-checked', String(+b.dataset.i === paint.sizeI)));
  pb.sym.querySelectorAll('button').forEach((b) => b.setAttribute('aria-checked', String(b.dataset.v === paint.sym)));
  pb.canvas.querySelectorAll('button').forEach((b) => b.setAttribute('aria-checked', String(b.dataset.v === paint.canvas)));
  pb.spin.setAttribute('aria-pressed', String(paint.spin)); pb.spin.textContent = paint.spin ? 'Spinning' : 'Spin';
  pb.mode.textContent = paint.look ? (narrow() ? 'Draw' : 'Back to drawing') : (narrow() ? 'Look' : 'Look around'); pb.mode.setAttribute('aria-pressed', String(paint.look));
  pb.undo.disabled = !paint.meshes.length; pb.clear.disabled = !paint.meshes.length;
}
function startPaint(canvasKind){
  if (!THREEOK) return;
  if (introOpen) closeIntro();
  closeSearch(); closeViewer(); closeBook(); closeStation(); closeBp(); if (tourIdx >= 0) endTour();
  if (narrow()) closeStaff();
  if (canvasKind) setPaintCanvas(canvasKind);
  if (inStudio() && Math.hypot(cam.x - PAINT_SPOT.x, cam.z - PAINT_SPOT.z) < 4.5){ enterPaint(); return; }
  paint.pending = true; goView(PAINT_SPOT);
  if (REDUCED) enterPaint();
}
function enterPaint(){
  paint.pending = false; paint.on = true; paint.look = false;
  pb.bar.hidden = false; document.body.classList.add('painting'); document.body.classList.remove('looking');
  updatePaintButtons(); hideHint(); ui.tag.hidden = true; applyProjection();
  toast(COARSE ? 'Drag to draw in the air. Pick a brush or a shape below. “Look” lets you move.' : 'Drag to draw in the air. Pick a brush or a shape below, and walk around to see your work from every side.');
  wake();
}
function stopPaint(){
  if (!paint.on && !paint.pending) return;
  if (paint.cur) paintUp();
  paint.on = false; paint.pending = false; pb.bar.hidden = true;
  document.body.classList.remove('painting', 'looking'); if (paint.tip) paint.tip.visible = false; applyProjection(); wake();
}
async function savePicture(){
  if (!downloadsCap || !THREEOK) return;
  if (paint.tip) paint.tip.visible = false;
  camera.position.set(cam.x, EYE, cam.z); camera.rotation.set(cam.pitch, cam.yaw, 0);
  /* Frame the picture on the whole screen, not just the part beside the tool panel */
  camera.clearViewOffset(); camera.aspect = window.innerWidth / window.innerHeight; camera.fov = camera.aspect < 0.8 ? 80 : 66; camera.updateProjectionMatrix();
  gfxRender();
  const blob = await new Promise((res) => { try { renderer.domElement.toBlob(res, 'image/png'); } catch (_) { res(null); } });
  applyProjection();
  if (!blob){ toast('Couldn’t capture the picture. Try again.'); return; }
  try { await downloadsCap.save({ filename:'my-3d-painting.png', data:blob }); toast('Saved your painting.'); }
  catch (e) { if (e && e.code === 'declined') return; if (e && e.code === 'rate_limited'){ toast('One moment, then try again.'); return; } pb.save.hidden = true; toast('Saving isn’t available here.'); }
}
async function initDownloads(){
  if (!(window.claude && typeof window.claude.use === 'function')){
    /* Hosted outside Claude: a normal browser download works */
    downloadsCap = { save: async ({ filename, data }) => { const url = URL.createObjectURL(data), a = document.createElement('a'); a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 5000); } };
    pb.save.hidden = false; return;
  }
  try { downloadsCap = await window.claude.use('downloads'); } catch (_) { downloadsCap = null; }
  pb.save.hidden = !downloadsCap;
}

$('#bSearch').addEventListener('click', () => ui.search.hidden ? openSearch() : closeSearch());
$('#bTour').addEventListener('click', () => tourIdx >= 0 ? endTour() : startTour());
$('#bAbout').addEventListener('click', openIntro);
ui.enter.addEventListener('click', () => { closeIntro(); if (curRoomId === 'lobby' || !curRoomId) ui.hint.classList.remove('gone'); clearTimeout(hintTimer); hintTimer = setTimeout(hideHint, 9000); });
ui.tourStart.addEventListener('click', () => { closeIntro(); startTour(); });
ui.vClose.addEventListener('click', closeViewer);
ui.vPrev.addEventListener('click', () => stepItem(-1));
ui.vNext.addEventListener('click', () => stepItem(1));
ui.viewer.addEventListener('click', (e) => { if (e.target === ui.viewer) closeViewer(); });
ui.rdClose.addEventListener('click', closeBook);
ui.rdPrev.addEventListener('click', () => turnPage(-1));
ui.rdNext.addEventListener('click', () => turnPage(1));
ui.reader.addEventListener('click', (e) => { if (e.target === ui.reader) closeBook(); });
ui.tNext.addEventListener('click', () => { if (tourIdx === STOPS.length - 1){ endTour(); return; } tourIdx++; showStop(); });
ui.tBack.addEventListener('click', () => { if (tourIdx > 0){ tourIdx--; showStop(); } });
ui.tOpen.addEventListener('click', () => { const s = STOPS[tourIdx]; if (!s) return; if (s.item) openItem(s.item, { walk:false }); else if (s.act) s.act(); });
ui.tEnd.addEventListener('click', endTour);
ui.q.addEventListener('input', renderResults);
ui.sClose.addEventListener('click', () => { closeSearch(); ui.scene.focus({ preventScroll:true }); });
ui.browse.addEventListener('click', () => { ui.search.hidden = false; renderResults(); ui.q.focus(); });

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape'){
    if (KICK.st === 'charge'){ socChargeEnd(true); e.preventDefault(); return; }
    if (!ui.viewer.hidden){ closeViewer(); e.preventDefault(); return; }
    if (!ui.reader.hidden){ closeBook(); e.preventDefault(); return; }
    if (!bpv.el.hidden){ closeBp(); e.preventDefault(); return; }
    if (!ui.search.hidden){ closeSearch(); ui.scene.focus({ preventScroll:true }); e.preventDefault(); return; }
    if (!rc.card.hidden){ closeRideCard(); e.preventDefault(); return; }
    if (!bg.panel.hidden){ closeBadges(); e.preventDefault(); return; }
    if (!gui.panel.hidden){ closeStaff(); e.preventDefault(); return; }
    if (ride.on){ endRide(false); e.preventDefault(); return; }
    if (STN.cur){ closeStation(); e.preventDefault(); return; }
    if (paint.on){ stopPaint(); e.preventDefault(); return; }
    if (tourIdx >= 0){ endTour(); return; }
    return;
  }
  if (!ui.viewer.hidden){ if (e.key === 'ArrowRight') stepItem(1); else if (e.key === 'ArrowLeft') stepItem(-1); return; }
  if (!ui.reader.hidden){ if (e.key === 'ArrowRight') turnPage(1); else if (e.key === 'ArrowLeft') turnPage(-1); return; }
  if (!bpv.el.hidden){ if (e.key === 'ArrowRight') bpv.next.click(); else if (e.key === 'ArrowLeft' && !bpv.prev.disabled) bpv.prev.click(); return; }
  const tgt = e.target;
  if (introOpen || (tgt && (tgt.tagName === 'INPUT' || tgt.tagName === 'TEXTAREA'))) return;
  if (tgt && tgt.tagName === 'BUTTON' && (e.key === ' ' || e.key === 'Enter')) return;
  if (paint.on && (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z'){ undoPaint(); e.preventDefault(); return; }
  const k = e.key.toLowerCase();
  PLAYER.sprint = e.shiftKey;
  if (k === ' ' || k === 'spacebar'){ if (!ride.on && !paint.on){ e.preventDefault(); if (!e.repeat) requestJump(); hideHint(); } return; }
  if (k === 'f'){ e.preventDefault(); if (!e.repeat) socChargeStart('key'); return; }
  if (['w', 'a', 's', 'd', 'q', 'e', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(k)){ keys.add(k); e.preventDefault(); hideHint(); wake(); }
});
document.addEventListener('keyup', (e) => { const k = e.key.toLowerCase(); keys.delete(k); PLAYER.sprint = e.shiftKey; if (k === 'f') socChargeEnd(); });
window.addEventListener('blur', () => { keys.clear(); PLAYER.sprint = false; socChargeEnd(true); });

/* Pointer: drag to look, tap to walk or open, drag to paint in the studio */
let ptr = null, hoverQueued = false, hoverPos = null;
function pick(cx, cy){
  const rect = ui.scene.getBoundingClientRect();
  const ndc = new THREE.Vector2(((cx - rect.left) / rect.width) * 2 - 1, -((cy - rect.top) / rect.height) * 2 + 1);
  raycaster.setFromCamera(ndc, camera);
  const hits = raycaster.intersectObjects(pickItems.concat(blockers, floors), false);
  for (const h of hits) if (shown(h.object)) return h;
  return null;
}
function shown(o){ while (o){ if (!o.visible) return false; o = o.parent; } return true; }
function handleTap(cx, cy){
  const hit = pick(cx, cy); if (!hit) return;
  const u = hit.object.userData;
  if (u.token){
    const td = TOKENS.find((t) => t.id === u.token);
    if (td && td.ride && ride.on !== td.ride){ toast(td.ride === 'coaster' ? 'Ride the Comet Coaster through the loop to grab that one!' : td.ride === 'drop' ? 'Ride the Sky Drop to the top to grab that one!' : 'Go on the Ocean Dive to grab that one!'); return; }
    collectToken(u.token); return;
  }
  if (ride.on){ if (u.creature != null && DIVE_FACTS[u.creature]) toast(DIVE_FACTS[u.creature].text); return; }
  if (u.ride){ openRide(u.ride); return; }
  if (u.prop){ kickProp(u.prop); hideHint(); return; }
  if (u.keeper){ keeperTalk(); return; }
  if (u.swing != null){ pushSwing(u.swing); hideHint(); return; }
  if (u.spin){ spinSpinner(); hideHint(); return; }
  if (u.staff){ openStaff(u.staff); return; }
  if (u.paint){ startPaint(); return; }
  if (u.station){ if (STN.id !== u.station) openStation(u.station); else if (u.act && STN.cur.act) STN.cur.act(u.act); return; }
  if (u.bp){ if (tourIdx >= 0) endTour(); openBp(u.bp, bpBoardPart(u.bp, hit.uv)); return; }
  if (u.hb != null){ openBook(BOOK['world-builder'], u.hb); return; }
  if (u.item){ if (tourIdx >= 0) endTour(); openItem(u.item, { walk:true }); return; }
  if (u.book){ openBook(u.book, 0); return; }
  if (u.shelf){ openSearch(SUBJ[u.shelf].name); return; }
  if (u.floor){ walkTo(safeTarget({ x:hit.point.x, z:hit.point.z })); hideHint(); return; }
  if (u.blocker){
    const dx = hit.point.x - cam.x, dz = hit.point.z - cam.z, L = Math.hypot(dx, dz);
    if (L > 1.4) walkTo(safeTarget({ x:hit.point.x - dx / L * 1.1, z:hit.point.z - dz / L * 1.1 }));
  }
}
ui.scene.addEventListener('pointerdown', (e) => {
  if (!THREEOK || ptr) return;
  const painting = paint.on && !paint.look && (e.pointerType !== 'mouse' || e.button === 0);
  ptr = { id:e.pointerId, x:e.clientX, y:e.clientY, lx:e.clientX, ly:e.clientY, t:performance.now(), moved:false, painting };
  try { ui.scene.setPointerCapture(e.pointerId); } catch (_) {}
  if (painting){ paintDown(e.clientX, e.clientY); hideHint(); }
  /* Press and hold on a ball you're standing at to power up a kick; drag to aim, let go to shoot */
  else if (SOC.vis && !ride.on && (e.pointerType !== 'mouse' || e.button === 0)){
    const hit = pick(e.clientX, e.clientY), id = hit && hit.object.userData.prop, P = id && PHYS.byId[id];
    if (P && P.kind === 'ball' && socInRange(P) && socChargeStart('ptr', P)){ KICK.ptr = e.pointerId; ptr.kick = true; }
  }
});
ui.scene.addEventListener('pointermove', (e) => {
  if (!THREEOK) return;
  if (ptr && e.pointerId === ptr.id){
    if (ptr.painting){ paintMove(e.clientX, e.clientY); return; }
    if (!ptr.moved && Math.hypot(e.clientX - ptr.x, e.clientY - ptr.y) > 7){ ptr.moved = true; ui.scene.classList.add('dragging'); ui.tag.hidden = true; }
    if (ptr.moved){
      if (KICK.st === 'run') KICK.trackOn = false;
      const k = e.pointerType === 'touch' ? 0.0058 : 0.0042;
      if (ride.on){ ride.look.yaw = clamp(ride.look.yaw + (e.clientX - ptr.lx) * k, -2.6, 2.6); ride.look.pitch = clamp(ride.look.pitch + (e.clientY - ptr.ly) * k, -1.1, 1.0); ride.look.at = performance.now(); wake(); }
      else { cam.yaw += (e.clientX - ptr.lx) * k; cam.pitch = clamp(cam.pitch + (e.clientY - ptr.ly) * k, -0.75, 0.6); faceYaw = null; facePitch = null; travelFace = false; hideHint(); wake(); }
    }
    ptr.lx = e.clientX; ptr.ly = e.clientY;
    return;
  }
  if (e.pointerType === 'mouse'){
    if (paint.on && !paint.look){ paintMove(e.clientX, e.clientY); wake(); return; }
    hoverPos = { x:e.clientX, y:e.clientY }; if (!hoverQueued){ hoverQueued = true; requestAnimationFrame(doHover); }
  }
});
function hoverLabel(u){
  if (u.token){ const td = TOKENS.find((t) => t.id === u.token); return td && td.ride && ride.on !== td.ride ? 'XR token · ride to collect' : 'Collect · XR token'; }
  if (u.ride) return (u.ride === 'dive' ? 'Dive · ' : 'Ride · ') + RIDES[u.ride].name;
  if (u.creature != null) return DIVE_CREATURES[u.creature] || 'Sea creature';
  if (ride.on) return '';
  if (u.prop){ const P = PHYS.byId[u.prop]; return P ? (P.kind === 'ball' ? (socInRange(P) ? 'Hold to power up · ' : 'Kick · ') + P.name : 'Shove · Foam block') : ''; }
  if (u.keeper) return 'Goalkeeper';
  if (u.swing != null) return 'Push · Swing';
  if (u.spin) return 'Spin · Merry-go-round';
  if (u.staff) return 'Ask ' + STAFF[u.staff].name;
  if (u.paint) return 'Start making art';
  if (u.station){ if (STN.id === u.station) return u.act && STN.cur.actLabel ? STN.cur.actLabel(u.act) : ''; return 'Use · ' + (STATION_CARDS[u.station] ? STATION_CARDS[u.station].t : 'Station'); }
  if (u.bp) return 'Explore · ' + BP_INFO[u.bp].title + ' blueprint';
  if (u.hb != null) return 'Read · World Builder’s Handbook';
  if (u.item) return 'Open · ' + u.item.title;
  if (u.book) return 'Read · ' + u.book.title;
  if (u.shelf) return 'Browse · ' + SUBJ[u.shelf].name;
  return '';
}
function doHover(){
  hoverQueued = false; if (!hoverPos || ptr || introOpen || paint.on){ ui.tag.hidden = true; return; }
  const hit = pick(hoverPos.x, hoverPos.y), label = hit ? hoverLabel(hit.object.userData) : '';
  ui.scene.classList.toggle('over-item', !!label);
  if (label){ ui.tag.textContent = label; ui.tag.style.left = hoverPos.x + 'px'; ui.tag.style.top = hoverPos.y + 'px'; ui.tag.hidden = false; }
  else ui.tag.hidden = true;
}
function endPointer(e, tap){
  if (!ptr || e.pointerId !== ptr.id) return;
  const was = ptr; ptr = null; ui.scene.classList.remove('dragging');
  if (was.painting){ paintUp(); return; }
  if (was.kick){ KICK.ptr = null; socChargeEnd(!tap); return; }
  if (tap && !was.moved && performance.now() - was.t < 650) handleTap(e.clientX, e.clientY);
}
ui.scene.addEventListener('pointerup', (e) => endPointer(e, true));
ui.scene.addEventListener('pointercancel', (e) => endPointer(e, false));
ui.scene.addEventListener('pointerleave', () => { ui.tag.hidden = true; if (paint.tip && !ptr) { paint.tip.visible = false; wake(); } });

/* Campus map */
const planCtx = ui.planC.getContext('2d');
const PDPR = Math.min(window.devicePixelRatio || 1, 2), PW = 180, PH = 150;
ui.planC.width = PW * PDPR; ui.planC.height = PH * PDPR;
const MAP = { x0:-33, x1:92, z0:-82, z1:26 };
const MAP_ROOMS = [
  { id:'lobby', x0:-6, x1:6, z0:-6, z1:0, label:'L' },
  { id:'g1', x0:-6, x1:6, z0:-18, z1:-6, label:'1' },
  { id:'g2', x0:-6, x1:6, z0:-30, z1:-18, label:'2' },
  { id:'g3', x0:-6, x1:6, z0:-42, z1:-30, label:'3' },
  { id:'wax', x0:-8.5, x1:8.5, z0:-81, z1:-42.3, label:'WAX HALL' },
  { id:'hallL', x0:-12, x1:-6, z0:-4.6, z1:-1.4 },
  { id:'lib', x0:-32, x1:-12, z0:-13, z1:7, label:'LIBRARY', also:'libAisle' },
  { id:'hallR', x0:6, x1:12, z0:-4.6, z1:-1.4 },
  { id:'school', x0:12, x1:34, z0:-4.75, z1:-1.25 },
  { id:'studio', x0:14, x1:24, z0:-13, z1:-4.75, label:'101' },
  { id:'lab', x0:25.6, x1:34, z0:-13, z1:-4.75, label:'102' },
  { id:'blueprint', x0:12.2, x1:24, z0:-1.25, z1:7, label:'103' },
  { id:'world', x0:24, x1:34, z0:-1.25, z1:7, label:'104' },
  { id:'yard', x0:34, x1:92, z0:-8.6, z1:26, label:'RECESS YARD', outdoor:true },
  { id:'coasterZone', x0:32, x1:92, z0:-34, z1:-8.6, label:'COASTER', outdoor:true },
  { id:'dropMap', x0:73.4, x1:82.6, z0:8.4, z1:17.6, label:'DROP', round:true },
  { id:'diveMap', x0:49.8, x1:58.2, z0:11.8, z1:20.2, label:'DIVE', round:true }
];
const MAP_GO = { lobby:'lobby', g1:'g1', g2:'g2', g3:'g3', wax:'wax', hallL:'library', lib:'library', hallR:'school', school:'school', studio:'studio', lab:'lab', blueprint:'blueprints', world:'worldroom', yard:'yard', coasterZone:'coaster', dropMap:'drop', diveMap:'dive' };
function mapScale(){ const s = Math.min((PW - 8) / (MAP.x1 - MAP.x0), (PH - 8) / (MAP.z1 - MAP.z0)); return { s, ox:(PW - (MAP.x1 - MAP.x0) * s) / 2, oy:(PH - (MAP.z1 - MAP.z0) * s) / 2 }; }
function drawPlan(){
  const ctx = planCtx, { s, ox, oy } = mapScale();
  ctx.setTransform(PDPR, 0, 0, PDPR, 0, 0); ctx.clearRect(0, 0, PW, PH);
  const X = (x) => ox + (x - MAP.x0) * s, Z = (z) => oy + (z - MAP.z0) * s;
  for (const r of MAP_ROOMS){
    const x = X(r.x0), y = Z(r.z0), w = (r.x1 - r.x0) * s, h = (r.z1 - r.z0) * s;
    const on = r.id === curRoomId || r.also === curRoomId;
    if (r.round){
      ctx.beginPath(); ctx.ellipse(x + w / 2, y + h / 2, w / 2, h / 2, 0, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(242,193,78,0.22)'; ctx.fill(); ctx.strokeStyle = 'rgba(242,193,78,0.8)'; ctx.lineWidth = 1; ctx.stroke();
      ctx.fillStyle = 'rgba(239,231,213,0.8)'; ctx.font = '6.5px ' + F.type; ctx.textAlign = 'center'; ctx.textBaseline = 'top'; ctx.fillText(r.label, x + w / 2, y + h + 1.5);
      continue;
    }
    ctx.fillStyle = on ? 'rgba(205,169,97,0.32)' : r.outdoor ? 'rgba(120,170,100,0.12)' : r.closed ? 'rgba(239,231,213,0.02)' : 'rgba(239,231,213,0.06)';
    ctx.fillRect(x, y, w, h);
    ctx.strokeStyle = r.outdoor ? 'rgba(150,196,128,0.6)' : r.closed ? 'rgba(205,169,97,0.3)' : 'rgba(205,169,97,0.75)'; ctx.lineWidth = 1;
    ctx.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
    if (r.label){ ctx.fillStyle = r.closed ? 'rgba(239,231,213,0.32)' : 'rgba(239,231,213,0.75)'; ctx.font = (r.label.length > 3 ? '7px ' : '8px ') + F.type; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(r.label, x + w / 2, y + h / 2 + (r.id === 'yard' ? -h * 0.3 : 0)); }
  }
  const px = X(cam.x), py = Z(cam.z), fx = -Math.sin(cam.yaw), fz = -Math.cos(cam.yaw), a = Math.atan2(fz, fx);
  ctx.fillStyle = 'rgba(205,169,97,0.55)'; ctx.beginPath(); ctx.moveTo(px, py); ctx.arc(px, py, 11, a - 0.55, a + 0.55); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#efe7d5'; ctx.beginPath(); ctx.arc(px, py, 2.6, 0, Math.PI * 2); ctx.fill();
}
ui.plan.addEventListener('click', (e) => {
  if (!THREEOK) return;
  let target = null;
  if (e.detail === 0){ const order = ['lobby', 'g1', 'g2', 'g3', 'wax', 'library', 'studio', 'lab', 'blueprints', 'worldroom', 'yard']; const cur = MAP_GO[curRoomId] || 'lobby'; target = order[(order.indexOf(cur) + 1) % order.length]; }
  else {
    const rect = ui.planC.getBoundingClientRect(), { s, ox, oy } = mapScale();
    const wx = MAP.x0 + ((e.clientX - rect.left) / rect.width * PW - ox) / s, wz = MAP.z0 + ((e.clientY - rect.top) / rect.height * PH - oy) / s;
    let best = null, bd = Infinity, ba = Infinity;
    for (const r of MAP_ROOMS){ if (r.closed || !MAP_GO[r.id]) continue; const dx = Math.max(r.x0 - wx, 0, wx - r.x1), dz = Math.max(r.z0 - wz, 0, wz - r.z1), d = Math.hypot(dx, dz), area = (r.x1 - r.x0) * (r.z1 - r.z0); if (d < bd - 0.01 || (Math.abs(d - bd) <= 0.01 && area < ba)){ bd = d; best = r; ba = area; } }
    if (!best || bd > 4) return;
    target = MAP_GO[best.id];
  }
  if (tourIdx >= 0) endTour();
  const p = PLACES.find((x) => x.id === target); if (p) goView(p.view());
  hideHint();
});

/* Touch stick and jump button */
const stick = $('#stick'), knob = $('#stickKnob'), jumpBtn = $('#bJump');
let stickId = null;
function stickSet(e){
  const r = stick.getBoundingClientRect(), R = r.width / 2, dx = e.clientX - (r.left + R), dy = e.clientY - (r.top + R), d = Math.hypot(dx, dy), m = Math.min(1, d / (R * 0.75)), k = d > 0 ? m / d : 0;
  JOY.x = dx * k; JOY.y = dy * k;
  knob.style.transform = 'translate(' + (JOY.x * R * 0.6).toFixed(1) + 'px,' + (JOY.y * R * 0.6).toFixed(1) + 'px)';
}
stick.addEventListener('pointerdown', (e) => { if (stickId != null || !THREEOK) return; stickId = e.pointerId; try { stick.setPointerCapture(e.pointerId); } catch (_) {} JOY.on = true; stick.classList.add('on'); stickSet(e); hideHint(); wake(); e.preventDefault(); });
stick.addEventListener('pointermove', (e) => { if (e.pointerId !== stickId) return; stickSet(e); wake(); });
function stickEnd(e){ if (e.pointerId !== stickId) return; stickId = null; JOY.on = false; JOY.x = JOY.y = 0; stick.classList.remove('on'); knob.style.transform = ''; wake(); }
stick.addEventListener('pointerup', stickEnd); stick.addEventListener('pointercancel', stickEnd);
stick.addEventListener('contextmenu', (e) => e.preventDefault());
jumpBtn.addEventListener('pointerdown', (e) => { e.preventDefault(); requestJump(); hideHint(); });
jumpBtn.addEventListener('click', (e) => { if (e.detail === 0) requestJump(); });

/* Graphics choice: High is the default everywhere and never steps down on its own */
const gfxSeg = $('#gfxSeg'), gfxNote = $('#gfxNote');
function renderGfx(){
  if (!gfxSeg) return;
  gfxSeg.textContent = '';
  const keys = ['high', 'medium', 'low'];
  for (const k of keys){
    const b = document.createElement('button'); b.type = 'button'; b.textContent = QUALITY[k].label; b.setAttribute('aria-pressed', String(GFX.tier === k));
    b.addEventListener('click', () => { gfxSavePref(k); GFX.scale = 1; gfxApplyTier(k); const nb = gfxSeg.children[keys.indexOf(k)]; if (nb) nb.focus(); });
    gfxSeg.appendChild(b);
  }
  gfxNote.textContent = { high:'Best look (default): shadows, glow, soft shading and thick grass', medium:'Shadows, glow and lighter grass', low:'Fastest, for older phones' }[GFX.tier];
}

/* Loop */
let raf = 0, last = 0, chain = false;
function wake(){ if (!THREEOK || raf || XR.on) return; last = performance.now(); chain = false; raf = requestAnimationFrame(frame); }
function frame(now){
  raf = 0;
  const cont = chain;
  /* rAF timestamps can trail performance.now(), so clamp both ends */
  const dt = Math.max(0, Math.min(0.1, (now - last) / 1000)); last = Math.max(last, now);
  if (XR.on) xrInput(dt);
  let active = ride.on ? true : update(dt);
  if (attract && introOpen){ attractT += dt; cam.yaw = Math.sin(attractT * 0.22) * 0.32; active = attractT < 60; }
  if (trackHeads(dt)) active = true;
  if (paint.pending && !path.length && inStudio()) enterPaint();
  if (ride.on) rideUpdate(dt);
  else if (XR.on) xrPlace();
  else { camera.position.set(cam.x + CAMX.x, eyeY() + CAMX.y, cam.z + CAMX.z); camera.rotation.set(cam.pitch, cam.yaw, 0); }
  if (ride.on === 'dive') animateDive(dt, camera.position);
  if (updateLights(dt)) active = true;
  updateWings();
  if (paintFrame(dt)) active = true;
  if (stationFrame(dt)) active = true;
  if (handsFrame(dt)) active = true;
  if (waxFrame(dt)) active = true;
  if (yardAmbient(dt)) active = true;
  if (yardPhysics(dt)) active = true;
  if (spinTokens(dt)) active = true;
  if (SKY && WING.outside && WING.outside.visible) SKY.position.copy(camera.position);
  if (gfxFrame(dt, cont)) active = true;
  natureFrame();
  gfxRender();
  setRoom(); if (!ride.on) drawPlan();
  noteWalk();
  if (XR.on) return;
  if (active || ptr || keys.size){ raf = requestAnimationFrame(frame); chain = true; } else chain = false;
}
function resize(){
  if (!THREEOK) return;
  const w = window.innerWidth, h = window.innerHeight;
  gfxSize();
  camera.aspect = w / h; camera.fov = w / h < 0.8 ? 80 : 66; camera.updateProjectionMatrix();
  applyProjection();
  if (!pb.bar.hidden) updatePaintButtons();
  wake();
}
window.addEventListener('resize', resize);

/* Boot */
function fontsReady(ms){
  if (!document.fonts || !document.fonts.load) return Promise.resolve();
  const faces = ['400 20px "Old Standard TT"', '700 20px "Old Standard TT"', 'italic 400 20px "Old Standard TT"', '400 20px "Courier Prime"', '700 20px "Courier Prime"', '400 20px "Libre Franklin"', '600 20px "Libre Franklin"', '700 20px "Libre Franklin"'];
  return Promise.race([Promise.all(faces.map((f) => document.fonts.load(f).catch(() => null))), new Promise((r) => setTimeout(r, ms))]);
}
function webglOK(){ try { const c = document.createElement('canvas'); return !!(window.WebGLRenderingContext && (c.getContext('webgl') || c.getContext('experimental-webgl'))); } catch (_) { return false; } }
async function boot(){
  await fontsReady(3000);
  for (const it of ITEMS) ART[it.id] = makeArt(it);
  ART.freedom = drawFreedomPanel();
  buildKB();
  if (THREE_LOADED && webglOK()){
    try {
      renderer = new THREE.WebGLRenderer({ canvas:ui.scene, antialias:false, powerPreference:'high-performance', stencil:false });
      gfxInitRenderer();
      /* Freed canvases cannot be re-uploaded after a lost GPU context, so start fresh instead */
      ui.scene.addEventListener('webglcontextrestored', () => { if (CANVAS_FREE.n) gfxLostReload(); });
      ui.scene.addEventListener('webglcontextlost', () => { if (CANVAS_FREE.n) setTimeout(() => { if (renderer.getContext().isContextLost()) gfxLostReload(); }, 4000); });
      buildScene();
      gfxEnvMaps();
      gfxComposer();
      xrInit();
      initPaint();
      buildNav();
      flushCanvases(); CANVAS_BOOT = false;
      waxWarm();
      THREEOK = true;
    } catch (err) { console.error(err); THREEOK = false; }
  }
  if (!THREEOK){
    ui.intro.hidden = true; document.body.classList.remove('intro-open');
    document.querySelector('.hud').hidden = true; ui.plan.hidden = true; ui.hint.hidden = true;
    ui.nogl.hidden = false; introOpen = false; return;
  }
  resize();
  ui.introMeta.textContent = '3 galleries · ' + ITEMS.length + ' exhibits · ' + WAX_SCENES.length + ' living-history scenes · ' + BOOKS.length + ' books · 4 workshops · 3 rides · 4 virtual staff';
  updateBadgeBtn();
  ui.enter.disabled = false; ui.tourStart.disabled = false; ui.enter.focus({ preventScroll:true });
  gui.ask.hidden = false; updateFab();
  if (COARSE){ stick.hidden = false; jumpBtn.hidden = false; document.body.classList.add('has-stick'); }
  socInitUi();
  renderGfx();
  buildPaintBar();
  initAI(); initDownloads();
  wake();
}
boot();
