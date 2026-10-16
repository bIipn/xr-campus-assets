#!/usr/bin/env node
/* ================================================================
   extract_content.mjs
   Pulls every content dataset out of the XRLibraries Campus (three.js) source
   and writes one JSON file per dataset for the Unreal Engine 5 port
   (DataTables / FTableRowBase structs; see ../spec/content.md).

   Strategy: no rendering code is executed. Pure data files (data.js, bpdata.js,
   books.js, waxscenes.js) run whole inside node:vm with tiny stubs. Mixed files
   (people.js, progress.js, engine.js, ui.js, nav.js, rides.js, ...) have their
   `const NAME = ...` initializers (or single functions) sliced out of the source
   by a string/regex/comment-aware bracket scanner and evaluated in isolation.
   Closures (view(), act()) are either resolved against stubs that return
   "@ref" markers, or kept as source text.

   Usage: node extract_content.mjs [repoRoot] [outDir]
   ================================================================ */
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(process.argv[2] || path.join(HERE, '..', '..', '..'));
const OUT = path.resolve(process.argv[3] || path.join(HERE, '..', 'content'));
const PARTS = path.join(ROOT, 'parts');
fs.mkdirSync(OUT, { recursive: true });

const read = (f) => fs.readFileSync(path.join(PARTS, f), 'utf8');
const lineOf = (src, idx) => src.slice(0, idx).split('\n').length;
const hex6 = (n) => (typeof n === 'number' ? '#' + n.toString(16).padStart(6, '0') : n);

/* ---------------- a small JS-aware scanner ---------------- */
/* Walks src from i, skipping strings, template literals, comments and regex
   literals; calls onChar(c, j, depth) for structural chars. Returns the index
   where `stop(c, depth, j)` first returns true. */
function walk(src, i, stop) {
  const openers = { '{': '}', '[': ']', '(': ')' };
  const stack = [];
  const n = src.length;
  let j = i;
  const prevSig = (k) => { let m = k - 1; while (m >= 0 && /\s/.test(src[m])) m--; return m >= 0 ? src[m] : ''; };
  while (j < n) {
    const c = src[j];
    if (c === '/' && src[j + 1] === '/') { j = src.indexOf('\n', j); if (j < 0) j = n; continue; }
    if (c === '/' && src[j + 1] === '*') { j = src.indexOf('*/', j); j = j < 0 ? n : j + 2; continue; }
    if (c === "'" || c === '"') { const q = c; j++; while (j < n && src[j] !== q) { if (src[j] === '\\') j++; j++; } j++; continue; }
    if (c === '`') { j++; while (j < n && src[j] !== '`') { if (src[j] === '\\') j++; j++; } j++; continue; }
    if (c === '/') {
      const p = prevSig(j);
      const kw = /(?:^|[^\w$])(return|typeof|case|else|in|of|do)\s*$/.test(src.slice(Math.max(0, j - 12), j));
      if (p === '' || '(,=:[!&|?{};+-*%<>~^'.includes(p) || kw) {
        j++; let cls = false;
        while (j < n) { const d = src[j]; if (d === '\\') { j += 2; continue; } if (d === '[') cls = true; else if (d === ']') cls = false; else if (d === '/' && !cls) break; else if (d === '\n') break; j++; }
        j++; while (j < n && /[dgimsuyv]/.test(src[j])) j++; continue;
      }
    }
    if (openers[c]) stack.push(openers[c]);
    else if (c === '}' || c === ']' || c === ')') { const want = stack.pop(); if (want !== c) throw new Error('bracket mismatch at line ' + lineOf(src, j) + ': expected ' + want + ' got ' + c); }
    if (stop(c, stack.length, j)) return j;
    j++;
  }
  throw new Error('walk: ran off the end');
}
/* The initializer expression of `const NAME = ...;` (up to the ; at depth 0) */
function sliceInit(src, name) {
  const m = new RegExp('(?:^|\\n)\\s*(?:const|let|var)\\s+' + name + '\\s*=\\s*').exec(src);
  if (!m) throw new Error('const ' + name + ' not found');
  const start = m.index + m[0].length;
  const end = walk(src, start, (c, depth) => c === ';' && depth === 0);
  return { src: src.slice(start, end), start, end, line0: lineOf(src, start), line1: lineOf(src, end) };
}
/* A whole `function NAME(...){...}` */
function sliceFunction(src, name) {
  const m = new RegExp('(?:^|\\n)function\\s+' + name + '\\s*\\(').exec(src);
  if (!m) throw new Error('function ' + name + ' not found');
  const start = m.index + (m[0].startsWith('\n') ? 1 : 0);
  const brace = src.indexOf('{', src.indexOf(')', start));
  const end = walk(src, brace, (c, depth) => c === '}' && depth === 0) + 1;
  return { src: src.slice(start, end), start, end, line0: lineOf(src, start), line1: lineOf(src, end) };
}
/* An `OBJ.key = {...};` assignment block */
function sliceAssign(src, lhs) {
  const m = new RegExp('(?:^|\\n)' + lhs.replace(/[.$]/g, '\\$&') + '\\s*=\\s*').exec(src);
  if (!m) throw new Error(lhs + ' not found');
  const start = m.index + m[0].length;
  const end = walk(src, start, (c, depth) => c === ';' && depth === 0);
  return { src: src.slice(start, end), start, end, line0: lineOf(src, start), line1: lineOf(src, end) };
}
const baseCtx = () => ({ Math, Object, Array, String, Number, Boolean, JSON, RegExp, Set, Map, parseInt, parseFloat, Float32Array, Infinity, NaN, undefined, console });
function evalExpr(expr, ctx) { return vm.runInNewContext('(' + expr + '\n)', Object.assign(baseCtx(), ctx || {}), { timeout: 5000 }); }
function runFile(src, ctx, tail) { return vm.runInNewContext(src + '\n;(' + tail + ')', Object.assign(baseCtx(), ctx || {}), { timeout: 5000 }); }
const fnSrc = (f) => (typeof f === 'function' ? f.toString() : null);

const manifest = [];
function emit(file, data, meta) {
  const p = path.join(OUT, file);
  fs.writeFileSync(p, JSON.stringify(data, null, 2) + '\n');
  const count = meta.count != null ? meta.count : Array.isArray(data) ? data.length : Object.keys(data).length;
  manifest.push(Object.assign({ file, count }, meta, { count }));
  return count;
}

/* ================================================================
   1. data.js: SOURCES, GALLERIES, KIND, ITEMS, FREEDOM, FACTS, SUBJECTS, BOOKS
   ================================================================ */
const dataSrc = read('data.js');
const D = runFile(dataSrc, {}, '{ SOURCES, GALLERIES, KIND, ITEMS, FREEDOM, FACTS, SUBJECTS, BOOKS }');
const L = (name, src = dataSrc) => { const s = sliceInit(src, name); return s.line0 + '-' + s.line1; };

emit('sources.json', Object.entries(D.SOURCES).map(([id, s]) => ({ id, label: s.label, url: s.url })), { source: 'parts/data.js:' + L('SOURCES'), var: 'SOURCES', drives: 'Citation chips on exhibit/scene cards; staff srcLine()' });
emit('galleries.json', D.GALLERIES.map((g, i) => Object.assign({ index: i }, g, { wall: hex6(g.wall) })), { source: 'parts/data.js:' + L('GALLERIES'), var: 'GALLERIES', drives: 'Gallery wall labels, wall colour per gallery, map/search grouping' });
emit('exhibit_kinds.json', Object.entries(D.KIND).map(([id, label]) => ({ id, label })), { source: 'parts/data.js:' + L('KIND'), var: 'KIND', drives: 'Kind label printed on exhibit cards and search rows' });
const exhibits = D.ITEMS.map((it) => Object.assign({ location: 'gallery' }, it)).concat([Object.assign({ location: 'library', g: null }, D.FREEDOM)]);
emit('exhibits.json', exhibits, { source: 'parts/data.js:' + L('ITEMS') + ' (ITEMS) and ' + L('FREEDOM') + ' (FREEDOM)', var: 'ITEMS + FREEDOM', drives: 'Museum wall frames, exhibit catalog cards, tour stops, search, staff knowledge base (KB kind=item)' });
emit('facts.json', D.FACTS, { source: 'parts/data.js:' + L('FACTS'), var: 'FACTS', drives: 'Staff knowledge base (KB kind=fact) and the AI system prompt' });
emit('subjects.json', D.SUBJECTS, { source: 'parts/data.js:' + L('SUBJECTS'), var: 'SUBJECTS', drives: 'The eight library stacks (side N/S, slot 0-3, spine colour), shelf views, section places' });

/* books: data.js BOOKS + worldroom.js WB_BOOK (pushed at runtime) */
const wrSrc = read('worldroom.js');
const WB = sliceInit(wrSrc, 'WB_BOOK');
const wbBook = evalExpr(WB.src);
const books = D.BOOKS.concat([wbBook]).map((b) => Object.assign({}, b, { pageCount: b.pages.length }));
emit('books.json', books, { source: 'parts/data.js:' + L('BOOKS') + ' (14 books) + parts/worldroom.js:' + WB.line0 + '-' + WB.line1 + ' (WB_BOOK, pushed by BOOKS.push at worldroom.js:279)', var: 'BOOKS', drives: 'Readable books on the featured table and stack ends, the reader panel, Rosa\'s recommendations, KB kind=page' });

/* ================================================================
   2. bpdata.js: BP_INFO / BP_ORDER (+ BP_PLACE from blueprints.js)
   ================================================================ */
const bpSrc = read('bpdata.js');
const BP = runFile(bpSrc, {}, '{ BP_INFO, BP_ORDER }');
const blSrc = read('blueprints.js');
const BPP = sliceInit(blSrc, 'BP_PLACE');
const bpPlace = evalExpr(BPP.src);
const blueprints = BP.BP_ORDER.map((id, i) => Object.assign({ id, order: i }, BP.BP_INFO[id], { place: bpPlace[id], parts: BP.BP_INFO[id].parts.map((p, j) => Object.assign({ index: j + 1 }, p)) }));
emit('blueprints.json', blueprints, { source: 'parts/bpdata.js:' + L('BP_INFO', bpSrc) + ' (BP_INFO), :96 (BP_ORDER); parts/blueprints.js:' + BPP.line0 + '-' + BPP.line1 + ' (BP_PLACE)', var: 'BP_INFO, BP_ORDER, BP_PLACE', drives: 'Room 103 wall boards, blueprint viewer part callouts (12 parts each), KB kind=part, search', count: blueprints.length, parts: blueprints.reduce((a, b) => a + b.parts.length, 0) });

/* ================================================================
   3. waxscenes.js: WAX_SCENES (12) -> wax_scenes.json (+ cast from build source)
   ================================================================ */
const wxSrc = read('waxscenes.js');
const WX = runFile(wxSrc, { WAX_POSE: {} }, '{ WAX_SCENES, WAX_POSE }');
const WAX_SKIN = { light: 0xf0c9ab, fair: 0xe4b08c, olive: 0xcf9e74, medium: 0xc08660, tan: 0xa66f4a, brown: 0x80522f, deep: 0x5a3622 }; /* parts/waxfig.js:20 */
const COLOR_KEYS = new Set(['skin', 'hair', 'top', 'bottom', 'collar', 'lanyard', 'shoes', 'eyes', 'socks', 'jacket', 'cap', 'tights', 'sleevesColor', 'apron', 'hem', 'beardColor']);
function castOf(buildSrc) {
  const out = [];
  const re = /(?:(?:const|let)\s+(\w+)\s*=\s*)?S\.fig\((\{[^{}]*\}),\s*\[([^\]]*)\],\s*(-?[\d.]+)\)/g;
  let m;
  while ((m = re.exec(buildSrc))) {
    const look = evalExpr(m[2], { WAX_SKIN });
    for (const k of Object.keys(look)) if (COLOR_KEYS.has(k) && typeof look[k] === 'number') look[k] = hex6(look[k]);
    out.push({ var: m[1] || null, avatar: look.av || null, look, at: m[3].split(',').map((v) => parseFloat(v)), ry: parseFloat(m[4]) });
  }
  return out;
}
const WAX_ITEM_LIST = [];
const waxScenes = WX.WAX_SCENES.map((sc) => {
  const bsrc = fnSrc(sc.build) || '';
  const item = Object.assign({ id: sc.id, kind: 'reenactment', hall: 'The Wax Hall · Scene ' + sc.n + ' of 12', sceneId: sc.id, year: parseInt(String(sc.year).replace(/\D/g, ''), 10) || null }, sc.item); /* as waxhall.js:446-447 does */
  WAX_ITEM_LIST.push(item);
  const propsUsed = [...new Set([...bsrc.matchAll(/WP\.(\w+)\(/g)].map((x) => x[1]))];
  const headsets = (bsrc.match(/waxHeadset\(\)/g) || []).length;
  return { id: sc.id, n: sc.n, year: sc.year, yearNum: item.year, title: sc.title, backdrop: sc.backdrop, floor: sc.floor, loopSeconds: sc.loop, lines: sc.lines.map(([t, text]) => ({ t, text })), item, cast: castOf(bsrc), propsUsed, headsetProps: headsets, hasTick: /S\.tick\(/.test(bsrc), buildSrcLines: bsrc.split('\n').length };
});
const WXS = sliceInit(wxSrc, 'WAX_SCENES');
emit('wax_scenes.json', waxScenes, { source: 'parts/waxscenes.js:' + WXS.line0 + '-' + WXS.line1 + ' (WAX_SCENES); cards assembled at parts/waxhall.js:445-449 (WAX_ITEMS)', var: 'WAX_SCENES / WAX_ITEMS', drives: 'The 12 Wax Hall stages: backdrop painting, floor, caption rail lines (timed), catalog card (item), figure cast (Rocketbox avatar id + outfit colours), loop length', castTotal: waxScenes.reduce((a, s) => a + s.cast.length, 0) });
emit('wax_poses.json', Object.entries(WX.WAX_POSE).map(([id, p]) => Object.assign({ id }, p)), { source: 'parts/waxscenes.js:34-44 (Object.assign(WAX_POSE,...)); base poses live in parts/waxfig.js:515+ (not extracted: animation data)', var: 'WAX_POSE (scene additions only)', drives: 'Named arm/elbow/hand/head pose presets referenced by scene keyframes (degrees)' });

/* ================================================================
   4. people.js: STAFF (4)  + ui.js GREET/CHIPS + engine.js JOKES/help/fallback/greeting
   ================================================================ */
const lookYaw = (fx, fz, tx, tz) => Math.atan2(-(tx - fx), -(tz - fz)); /* parts/outdoor.js:12 */
const peSrc = read('people.js');
const ST = sliceInit(peSrc, 'STAFF');
const STAFF = evalExpr(ST.src, { lookYaw });
const uiSrc = read('ui.js');
const enSrc = read('engine.js');
const GREET = evalExpr(sliceInit(uiSrc, 'GREET').src);
const CHIPS = evalExpr(sliceInit(uiSrc, 'CHIPS').src);
const JOKES = evalExpr(sliceInit(enSrc, 'JOKES').src);
const helpers = runFile([sliceFunction(enSrc, 'greetingShort').src, sliceFunction(enSrc, 'helpText').src, sliceFunction(enSrc, 'fallbackText').src].join('\n'), {}, '{ greetingShort, helpText, fallbackText }');
const staffRulesSrc = sliceFunction(uiSrc, 'staffRules').src;
const COASTER_STATS = evalExpr(sliceInit(read('outdoor.js'), 'COASTER').src, { THREE: {} }).stats; /* { height:19, kmh:62, mph:39, loop:10, length:170 } */
const DROP = evalExpr(sliceInit(read('outdoor.js'), 'DROP').src);
const DOME = evalExpr(sliceInit(read('outdoor.js'), 'DOME').src);
const itemWhere = (it) => (it.sceneId ? 'Wax Hall · Scene ' + it.scene_n : it.g ? 'Gallery ' + it.g : 'Library');
const SUBJ = {}; D.SUBJECTS.forEach((s) => (SUBJ[s.id] = s));
/* PLACES first (needed by staffRules) */
const PL = sliceInit(enSrc, 'PLACES');
const STATIONS_STUB = {}; for (const k of ['sieve', 'titration', 'pendulum', 'bench', 'diorama']) STATIONS_STUB[k] = { view: () => '@station:' + k };
const SHELF_VIEWS = new Proxy({}, { get: (_, k) => '@shelf:' + String(k) });
const placesRaw = evalExpr(PL.src, { STAFF, STATIONS: STATIONS_STUB, SHELF_VIEWS, bpViewFor: (id) => '@blueprint:' + id, lookYaw, SUBJECTS: D.SUBJECTS });
const places = placesRaw.map((p) => { let v = null, ref = null; try { v = p.view(); } catch (e) { ref = '@error:' + e.message; } if (typeof v === 'string') { ref = v; v = null; } return { id: p.id, label: p.label, say: p.say || null, names: p.names, view: v, viewRef: ref, viewSrc: fnSrc(p.view) }; });
emit('places.json', places, { source: 'parts/engine.js:' + PL.line0 + '-' + PL.line1 + ' (34 literal places + 8 generated from SUBJECTS)', var: 'PLACES', drives: 'Staff "take me to" navigation targets and search Places group; each has a camera view (x,z,yaw,pitch) or a reference to a live view' });

const staff = Object.values(STAFF).map((s) => {
  const look = Object.assign({}, s.look); for (const k of Object.keys(look)) if (typeof look[k] === 'number') look[k] = hex6(look[k]);
  let aiPrompt = null;
  try {
    aiPrompt = runFile(staffRulesSrc, { COASTER: { stats: COASTER_STATS }, DROP, TOKENS: { length: 11 }, BADGES: { length: 15 }, FACTS: D.FACTS, ITEMS: D.ITEMS, FREEDOM: D.FREEDOM, WAX_ITEMS: WAX_ITEM_LIST.map((it, i) => Object.assign({}, it, { scene_n: i + 1 })), itemWhere, BOOKS: books, SUBJ, PLACES: placesRaw }, 'staffRules(' + JSON.stringify(s.id) + ')');
  } catch (e) { aiPrompt = '@error:' + e.message; }
  return { id: s.id, name: s.name, role: s.role, mono: s.mono, color: s.color, rooms: s.rooms, track: s.track || null, pos: s.pos, face: s.face, look, view: s.view, greeting: GREET[s.id], greetingShort: helpers.greetingShort(s.id), help: helpers.helpText(s.id), fallback: helpers.fallbackText(s.id), joke: JOKES[s.id], chips: CHIPS[s.id], aiSystemPrompt: aiPrompt };
});
emit('staff.json', staff, { source: 'parts/people.js:' + ST.line0 + '-' + ST.line1 + ' (STAFF); parts/ui.js:203-214 (CHIPS, GREET); parts/engine.js:153-158 (JOKES), 314-326 (greetingShort/helpText/fallbackText); parts/ui.js:322-355 (staffRules, rendered here)', var: 'STAFF (+GREET, CHIPS, JOKES, staffRules)', drives: 'The four virtual staff NPCs: Rocketbox avatar id, outfit colours, standing position/facing, chat greeting, suggestion chips, joke, help/fallback lines and the full LLM system prompt' });

/* ================================================================
   5. engine.js: LESSONS, RX, presetAnswer branches, ride texts  -> lessons.json, staff_answers.json
   ================================================================ */
const LS = sliceInit(enSrc, 'LESSONS');
const lessons = evalExpr(LS.src).map((l, i) => Object.assign({ id: 'lesson-' + (i + 1) }, l));
emit('lessons.json', lessons, { source: 'parts/engine.js:' + LS.line0 + '-' + LS.line1, var: 'LESSONS', drives: 'What the lab, bench and layer table teach; KB kind=lesson so Mr. Hale can answer station questions; search Workshops group' });

const RXs = sliceInit(enSrc, 'RX');
const RX = evalExpr(RXs.src);
const rxRows = Object.entries(RX).map(([id, r]) => ({ id, pattern: r.source, flags: r.flags }));
const PA = sliceFunction(enSrc, 'presetAnswer');
const branches = [];
PA.src.split('\n').forEach((ln, i) => {
  let idx = 0, k;
  while ((k = ln.indexOf('return reply(', idx)) >= 0) {
    const open = k + 'return reply'.length;
    const end = walk(ln, open, (c, depth) => c === ')' && depth === 0);
    const args = ln.slice(open + 1, end);
    const comma = (() => { try { return walk(args, 0, (c, depth) => c === ',' && depth === 0); } catch (_) { return -1; } })();
    const first = (comma >= 0 ? args.slice(0, comma) : args).trim(), extra = comma >= 0 ? args.slice(comma + 1).trim() : null;
    const condM = /^\s*(?:(?:const|let)\s+[^;]+;\s*)?if\s*\(/.exec(ln);
    let cond = null;
    if (condM) { const o = ln.indexOf('(', condM.index + condM[0].length - 1); const ce = walk(ln, o, (c, depth) => c === ')' && depth === 0); cond = ln.slice(o + 1, ce); }
    const rxUsed = [...new Set([...ln.matchAll(/RX\.(\w+)/g)].map((m) => m[1]))];
    const staffOnly = [...new Set([...ln.matchAll(/staffId === '(\w+)'/g)].map((m) => m[1]))];
    const staffNot = [...new Set([...ln.matchAll(/staffId !== '(\w+)'/g)].map((m) => m[1]))];
    let staticText = null;
    if (/^'(?:[^'\\]|\\.)*'$/.test(first)) staticText = evalExpr(first);
    const action = (extra && /action:\s*'([^']+)'/.exec(extra)) ? /action:\s*'([^']+)'/.exec(extra)[1] : null;
    branches.push({ order: branches.length + 1, line: PA.line0 + i, conditionSrc: cond, rulesUsed: rxUsed, staffOnly, staffNot, staticText, replySrc: first, extraSrc: extra, action, cardsSrc: extra && /cards:\s*(\[[^\]]*\])/.exec(extra) ? /cards:\s*(\[[^\]]*\])/.exec(extra)[1] : null });
    idx = end;
  }
});
const rideFns = runFile([sliceFunction(enSrc, 'dropKmh').src, sliceFunction(enSrc, 'rideAbout').src, sliceFunction(enSrc, 'rideStats').src, sliceFunction(enSrc, 'rideSafety').src].join('\n'), { COASTER: { stats: COASTER_STATS }, DROP }, '{ rideAbout, rideStats, rideSafety, dropKmh }');
const dirFn = runFile(sliceFunction(enSrc, 'directions').src, {}, 'directions');
const directions = placesRaw.map((p) => ({ placeId: p.id, text: dirFn(p) }));
emit('staff_answers.json', { rules: rxRows, presetBranches: branches, directions, kbSearch: { stopWordsSrc: sliceInit(enSrc, 'STOP').src.slice(0, 120) + '…', keep2: evalExpr(sliceInit(enSrc, 'KEEP2').src), note: 'searchKB(): TF-IDF over sentence-split KB (items, facts, pages, parts, lessons); staff-specific kind bias in searchAnswer() engine.js:281-307; qtype() when/num/who boosts in bestSentence()' } }, { source: 'parts/engine.js:' + RXs.line0 + '-' + RXs.line1 + ' (RX), ' + PA.line0 + '-' + PA.line1 + ' (presetAnswer), 266-280 (directions), 4-66 (search engine)', var: 'RX, presetAnswer, directions', drives: 'Offline staff chat: regex intent rules (43), ordered preset reply branches (text + cards + actions), walking directions per place, and the KB search fallback', count: rxRows.length, presetBranches: branches.length, directions: directions.length });

/* ride texts (rides.js rideText/rideNote + engine.js rideAbout/rideStats/rideSafety) */
const rdSrc = read('rides.js');
const RD = sliceInit(rdSrc, 'RIDES');
const RIDES = evalExpr(RD.src, { lookYaw });
const rdText = runFile([sliceFunction(rdSrc, 'rideText').src, sliceFunction(rdSrc, 'rideNote').src].join('\n'), { COASTER: { stats: COASTER_STATS } }, '{ rideText, rideNote }');
const rides = Object.entries(RIDES).map(([id, r]) => ({ id, name: r.name, kick: r.kick, exitView: r.exit, badge: r.badge, cardText: rdText.rideText(id), cardNote: rdText.rideNote(id), staffAbout: rideFns.rideAbout(id), staffStats: rideFns.rideStats(id), staffSafety: rideFns.rideSafety(id) }));
emit('rides.json', { rides, coasterStats: COASTER_STATS, dropTower: DROP, diveDome: DOME, dropFreefallKmh: rideFns.dropKmh() }, { source: 'parts/rides.js:' + RD.line0 + '-' + RD.line1 + ' (RIDES), 16-26 (rideText/rideNote); parts/engine.js:166-182 (rideAbout/rideStats/rideSafety); parts/outdoor.js:6-7,456 (DROP, DOME, COASTER.stats)', var: 'RIDES', drives: 'Ride cards (title, text, note, Gentle option), exit camera view after a ride, badge awarded, and what staff say about each ride', count: rides.length });

/* ================================================================
   6. progress.js: BADGES, TOKENS
   ================================================================ */
const prSrc = read('progress.js');
const BD = sliceInit(prSrc, 'BADGES'), TK = sliceInit(prSrc, 'TOKENS');
emit('badges.json', evalExpr(BD.src), { source: 'parts/progress.js:' + BD.line0 + '-' + BD.line1, var: 'BADGES', drives: 'Achievement list (award(id) calls scattered through stations/rides/progress; icon drawn procedurally in drawBadgeIcon progress.js:120-142)' });
emit('tokens.json', evalExpr(TK.src), { source: 'parts/progress.js:' + TK.line0 + '-' + TK.line1, var: 'TOKENS', drives: 'The 11 hidden collectible XR tokens: world position [x,y,z] in metres (three.js, y up), or a ride anchor resolved at runtime (tokenPos progress.js:45-50)' });

/* ================================================================
   7. ui.js: STOPS (tour), STATION_CARDS, MAP_ROOMS, MAP_GO
   ================================================================ */
const SO = sliceInit(uiSrc, 'STOPS');
const PAINT_SPOT = evalExpr(sliceInit(read('paint.js'), 'PAINT_SPOT').src);
const BOOK = {}; books.forEach((b) => (BOOK[b.id] = b));
const stopsRaw = evalExpr(SO.src, { ITEMS: D.ITEMS, WAX_ITEMS: WAX_ITEM_LIST, BOOKS: books, BOOK, lobbyView: () => '@lobbyView', PAINT_SPOT, openBook() {}, endTour() {}, startPaint() {}, openStation() {}, openBp() {}, openRide() {} });
const tour = stopsRaw.map((s, i) => {
  let v = null, ref = null; if (s.view) { v = s.view(); if (typeof v === 'string') { ref = v; v = null; } }
  return { index: i + 1, kind: s.kind, itemId: s.item ? s.item.id : null, title: s.item ? s.item.title : s.title, date: s.item ? s.item.date : s.date, text: s.item ? s.item.desc : s.text, view: v, viewRef: s.item ? '@itemView:' + s.item.id : ref, openLabel: s.open || (s.item ? (s.item.sceneId ? 'Open scene card' : 'Open exhibit') : null), actSrc: fnSrc(s.act) };
});
emit('tour.json', tour, { source: 'parts/ui.js:' + SO.line0 + '-' + SO.line1 + ' (STOPS; item stops expanded from ITEMS and WAX_ITEMS), showStop() 142-158', var: 'STOPS', drives: 'The guided tour: 36 ordered stops with title/date/text, camera view (or item view), and an optional action button' });

const SC = sliceInit(uiSrc, 'STATION_CARDS');
const stationCards = evalExpr(SC.src);
/* station panel copy: paragraphs / buttons / toasts inside each STATIONS.x block */
function stationText(src, file, keys) {
  const rows = [];
  for (const k of keys) {
    const blk = sliceAssign(src, 'STATIONS.' + k);
    const b = blk.src;
    const titleM = /title\(\)\s*\{\s*return\s*(\[[^\]]*\])/.exec(b);
    const titles = titleM ? evalExpr(titleM[1]) : null;
    const texts = [];
    for (const m of b.matchAll(/stEl\('(p|h3)', '(st\w+)', '((?:[^'\\]|\\.)*)'\)/g)) texts.push({ kind: m[2], text: evalExpr("'" + m[3] + "'") });
    const buttons = [...new Set([...b.matchAll(/stBtn\('((?:[^'\\]|\\.)*)'/g)].map((m) => evalExpr("'" + m[1] + "'")))];
    const toasts = [...new Set([...b.matchAll(/toast\('((?:[^'\\]|\\.)*)'\)/g)].map((m) => evalExpr("'" + m[1] + "'")))];
    const kick = /kick:\s*'([^']*)'/.exec(b), room = /room:\s*'([^']*)'/.exec(b), hands = /hands:\s*true/.test(b);
    rows.push({ id: k, file, lines: blk.line0 + '-' + blk.line1, room: room ? room[1] : null, kick: kick ? kick[1] : null, usesHands: hands, stepTitles: titles, panelTexts: texts, buttonLabels: buttons, toasts });
  }
  return rows;
}
const labSrc = read('lab.js');
const stationBlocks = stationText(labSrc, 'parts/lab.js', ['sieve', 'titration', 'pendulum']).concat(stationText(blSrc, 'parts/blueprints.js', ['bench']), stationText(wrSrc, 'parts/worldroom.js', ['diorama']));
const stations = Object.entries(stationCards).map(([id, c]) => Object.assign({ id, card: c }, stationBlocks.find((b) => b.id === id)));
emit('stations.json', stations, { source: 'parts/ui.js:' + SC.line0 + '-' + SC.line1 + ' (STATION_CARDS); STATIONS.sieve lab.js:329+, STATIONS.titration lab.js:572+, STATIONS.pendulum lab.js:694+, STATIONS.bench blueprints.js:361+, STATIONS.diorama worldroom.js:131+ (text literals only; the step logic/state machines are code)', var: 'STATION_CARDS + STATIONS.*', drives: 'The five hands-on stations: chat/search card text, docked panel kicker, room, step titles, explanatory paragraphs, button labels and toasts. Simulation logic (psd/titr/pend/bench state) is NOT data and must be reimplemented.' });

const DS = sliceInit(wrSrc, 'DIO_STEPS');
emit('world_layers.json', evalExpr(DS.src).map((s, i) => Object.assign({ index: i + 1 }, s)), { source: 'parts/worldroom.js:' + DS.line0 + '-' + DS.line1, var: 'DIO_STEPS', drives: 'Room 104 layer table: nine build layers (title, description, handbook page to open) and the pipeline banner' });
const BK = sliceInit(blSrc, 'BENCH_KITS');
const kits = Object.entries(evalExpr(BK.src)).map(([id, k]) => ({ id, name: k.name, steps: k.steps.map((s, i) => Object.assign({ index: i + 1 }, s)) }));
emit('bench_kits.json', kits, { source: 'parts/blueprints.js:' + BK.line0 + '-' + BK.line1 + '; result strings benchDrive()/benchShakeText() 427-436', var: 'BENCH_KITS', drives: 'Room 103 model bench: two kits with ordered steps (title, instruction, why-it-works, parts to show, action label, test flag)', count: kits.length, steps: kits.reduce((a, k) => a + k.steps.length, 0) });
const SV = sliceInit(labSrc, 'SIEVES');
emit('sieves.json', evalExpr(SV.src).map(([mesh, micron, afs], i) => ({ index: i, mesh, openingMicrons: micron, afsMultiplier: afs })), { source: 'parts/lab.js:' + SV.line0 + '-' + SV.line1, var: 'SIEVES', drives: 'Sieve stack definition (US mesh number, opening in micrometres, AFS GFN multiplier) for the Room 102 sieve analysis' });

const MR = sliceInit(uiSrc, 'MAP_ROOMS'), MG = sliceInit(uiSrc, 'MAP_GO');
const mapGo = evalExpr(MG.src);
emit('map_rooms.json', evalExpr(MR.src).map((r) => Object.assign({}, r, { goPlace: mapGo[r.id] || null })), { source: 'parts/ui.js:' + MR.line0 + '-' + MR.line1 + ' (MAP_ROOMS), ' + MG.line0 + '-' + MG.line1 + ' (MAP_GO); MAP bounds x -33..92, z -82..26', var: 'MAP_ROOMS + MAP_GO', drives: 'The corner minimap: rectangles/rounds with labels, and which PLACES entry a tap on each one walks to' });

/* ================================================================
   8. nav.js: ROOMS, ROOM_INFO, DOORS, NOGO; rooms.js ROOM_NAMES/SCHOOL_DOORS; waxhall.js WH
   ================================================================ */
const nvSrc = read('nav.js');
const RM = sliceInit(nvSrc, 'ROOMS'), RI = sliceInit(nvSrc, 'ROOM_INFO'), DR = sliceInit(nvSrc, 'DOORS'), NG = sliceInit(nvSrc, 'NOGO');
const roomInfo = evalExpr(RI.src);
const rooms = evalExpr(RM.src).map((r) => Object.assign({}, r, { info: roomInfo[r.id] || null }));
emit('rooms.json', rooms, { source: 'parts/nav.js:' + RM.line0 + '-' + RM.line1 + ' (ROOMS, walkable AABBs in metres), ' + RI.line0 + '-' + RI.line1 + ' (ROOM_INFO: HUD room tag kicker/name/sub)', var: 'ROOMS + ROOM_INFO', drives: 'roomAt() lookup, walkable area, wing visibility, the HUD room tag text, staff home rooms' });
emit('doors.json', { doors: evalExpr(DR.src), noGo: evalExpr(NG.src), wallThickness: 0.45, schoolDoors: evalExpr(sliceInit(read('rooms.js'), 'SCHOOL_DOORS').src), roomNames: evalExpr(sliceInit(read('rooms.js'), 'ROOM_NAMES').src), waxHall: evalExpr(sliceInit(read('waxhall.js'), 'WH').src) }, { source: 'parts/nav.js:' + DR.line0 + '-' + DR.line1 + ' (DOORS), ' + NG.line0 + '-' + NG.line1 + ' (NOGO), 4 (M_WALL); parts/rooms.js:7-8; parts/waxhall.js:7 (WH)', var: 'DOORS, NOGO, SCHOOL_DOORS, ROOM_NAMES, WH', drives: 'Door openings between rooms (axis, position, centre, width, band), no-walk rectangles, school door x-positions, room number names, Wax Hall layout constants', count: 14 });

/* ================================================================
   9. dive.js, paint.js, phys.js, art.js, worldroom.js SCREENS/TOOLS, gfx.js QUALITY
   ================================================================ */
const dvSrc = read('dive.js');
const DF = sliceInit(dvSrc, 'DIVE_FACTS');
emit('dive_facts.json', { facts: evalExpr(DF.src).map((f, i) => Object.assign({ index: i }, f)), creatures: Object.entries(evalExpr(sliceInit(dvSrc, 'DIVE_CREATURES').src)).map(([factIndex, name]) => ({ factIndex: +factIndex, name })), pathPoints: evalExpr(sliceInit(dvSrc, 'DIVE_PTS').src), origin: evalExpr(sliceInit(dvSrc, 'DV').src) }, { source: 'parts/dive.js:' + DF.line0 + '-' + DF.line1 + ' (DIVE_FACTS), 449 (DIVE_CREATURES), 6 (DIVE_PTS), 4 (DV)', var: 'DIVE_FACTS, DIVE_CREATURES, DIVE_PTS', drives: 'Ocean Dive ride: timed/positioned caption facts, which creature the camera looks at, tappable creature names, the 14-point swim path (local to DV origin x=420)', count: 9 });
const ptSrc = read('paint.js');
emit('paint_tools.json', { brushes: evalExpr(sliceInit(ptSrc, 'BRUSHES').src), shapes: evalExpr(sliceInit(ptSrc, 'SHAPES').src), colors: evalExpr(sliceInit(ptSrc, 'PAINT_COLORS').src), brushSizes: evalExpr(sliceInit(ptSrc, 'PAINT_SIZES').src), stampSizes: evalExpr(sliceInit(ptSrc, 'STAMP_SIZES').src), paintSpot: PAINT_SPOT, studioBox: evalExpr(sliceInit(ptSrc, 'STUDIO_BOX').src), centre: evalExpr(sliceInit(ptSrc, 'PAINT_C').src) }, { source: 'parts/paint.js:5-19', var: 'BRUSHES, SHAPES, PAINT_COLORS, PAINT_SIZES, STAMP_SIZES, PAINT_SPOT, STUDIO_BOX, PAINT_C', drives: 'Room 101 3D Art Studio palette: 7 brushes, 8 stamp shapes, 12 colours, 4 sizes, where you stand, room bounds, symmetry centre', count: 7 });
const phSrc = read('phys.js');
emit('physics_props.json', { balls: evalExpr(sliceInit(phSrc, 'BALL_DEFS').src), blockTower: evalExpr(sliceInit(phSrc, 'TOWER').src), blockColors: evalExpr(sliceInit(phSrc, 'BLOCK_COLS').src), goal: evalExpr(sliceInit(phSrc, 'GOAL').src), swing: evalExpr(sliceInit(phSrc, 'SWING').src), spinner: evalExpr(sliceInit(phSrc, 'SPIN').src) }, { source: 'parts/phys.js:12-21, 335, 366', var: 'BALL_DEFS, TOWER, BLOCK_COLS, GOAL, SWING, SPIN', drives: 'Recess Yard physics props: balls (radius, mass, restitution, drag, spin lift, rolling resistance, start position, skin), foam block tower words/colours, soccer goal size, swing/merry-go-round params', count: 4 });
const PC = sliceInit(read('art.js'), 'PLAYBOOK_CATS');
emit('playbook_categories.json', evalExpr(PC.src).map((name, i) => ({ index: i, name })), { source: 'parts/art.js:' + PC.line0 + '-' + PC.line1, var: 'PLAYBOOK_CATS', drives: 'Category list painted on the XR Playbooks exhibit object cover (drawPlaybookCover)' });
const SCR = sliceInit(wrSrc, 'SCREENS'), TL = sliceInit(wrSrc, 'TOOLS');
const CK = '#c792ea', CF = '#82aaff', CS = '#c3e88d', CN = '#f78c6c', CT = '#e6edf3', CC = '#5c6c80'; /* worldroom.js:196 */
const screens = evalExpr(SCR.src, { CK, CF, CS, CN, CT, CC }).map((s) => ({ file: s.file, handbookPage: s.page, codeLines: s.lines.map((l) => l.map((t) => t[0]).join('')), tokens: s.lines }));
emit('world_screens_tools.json', { codeScreens: screens, toolboxes: evalExpr(TL.src).map(([name, color, bg], i) => ({ index: i, name, color, bg, handbookPage: 2 })) }, { source: 'parts/worldroom.js:' + SCR.line0 + '-' + SCR.line1 + ' (SCREENS), ' + TL.line0 + '-' + TL.line1 + ' (TOOLS)', var: 'SCREENS, TOOLS', drives: 'Room 104 desk monitors (syntax-coloured code snippets that open a handbook page) and the toolkit shelf boxes', count: 3, tools: 9 });
const QG = sliceInit(read('gfx.js'), 'QUALITY');
emit('quality_tiers.json', Object.entries(evalExpr(QG.src)).map(([id, q]) => Object.assign({ id }, q)), { source: 'parts/gfx.js:' + QG.line0 + '-' + QG.line1, var: 'QUALITY', drives: 'Graphics tiers (web-specific; maps to UE Scalability groups, not a content table)' });

/* ================================================================
   10. body.html UI copy; books.js (orphan, not assembled)
   ================================================================ */
const body = fs.readFileSync(path.join(PARTS, 'body.html'), 'utf8');
const uiStrings = [];
for (const m of body.matchAll(/<(h1|h2|h3|p|button|span|label|li|summary|a|small)\b([^>]*)>([\s\S]*?)<\/\1>/g)) {
  const idm = /id="([^"]+)"/.exec(m[2]); const txt = m[3].replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
  if (txt.length > 1) uiStrings.push({ tag: m[1], id: idm ? idm[1] : null, line: lineOf(body, m.index), text: txt.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>') });
}
emit('ui_strings.json', uiStrings, { source: 'parts/body.html (all element text nodes); page <title> set in assemble.py:33,40', var: '(HTML)', drives: 'Intro/About panel copy, button labels, panel headings. Candidate for a UE StringTable rather than a DataTable' });
const lgSrc = read('books.js');
const LG = runFile(lgSrc, {}, '{ SUBJECTS, BOOKS }');
emit('books_legacy_pine_hollow.json', { note: 'parts/books.js is NOT in assemble.py PARTS (the live BOOKS/SUBJECTS are in parts/data.js). It is an older Pine Hollow-themed edition kept in the repo; 6 of its 14 books overlap by id with data.js (reading-past, first-job, water-cycle, code, ai, oral-history) with slightly different text.', subjects: LG.SUBJECTS, books: LG.BOOKS }, { source: 'parts/books.js:4-13 (SUBJECTS), 16-266 (BOOKS) — ORPHAN, not assembled', var: 'SUBJECTS/BOOKS (legacy)', drives: 'Nothing at runtime. Kept for reference only.', count: LG.BOOKS.length });

/* ================================================================
   Manifest + validation
   ================================================================ */
/* Expected record counts, verified by hand against the source (grep of record openers per declaration) */
const EXPECT = { 'sources.json': 22, 'galleries.json': 4, 'exhibit_kinds.json': 9, 'exhibits.json': 16, 'facts.json': 15, 'subjects.json': 8, 'books.json': 15, 'blueprints.json': 5, 'wax_scenes.json': 12, 'wax_poses.json': 9, 'places.json': 42, 'staff.json': 4, 'lessons.json': 11, 'staff_answers.json': 43, 'rides.json': 3, 'badges.json': 15, 'tokens.json': 11, 'tour.json': 35, 'stations.json': 5, 'world_layers.json': 9, 'bench_kits.json': 2, 'sieves.json': 12, 'map_rooms.json': 17, 'rooms.json': 15, 'doors.json': 14, 'dive_facts.json': 9, 'paint_tools.json': 7, 'physics_props.json': 4, 'playbook_categories.json': 12, 'world_screens_tools.json': 3, 'quality_tiers.json': 3, 'ui_strings.json': null, 'books_legacy_pine_hollow.json': 14 };
let ok = true;
const report = [];
for (const m of manifest) {
  const txt = fs.readFileSync(path.join(OUT, m.file), 'utf8');
  let parsed; try { parsed = JSON.parse(txt); } catch (e) { ok = false; report.push('PARSE FAIL ' + m.file + ': ' + e.message); continue; }
  const exp = EXPECT[m.file];
  const good = exp == null || exp === m.count;
  if (!good) ok = false;
  report.push((good ? 'ok   ' : 'FAIL ') + m.file.padEnd(32) + ' count=' + String(m.count).padStart(3) + (exp != null ? ' expected=' + exp : '') + '  ' + (txt.length / 1024).toFixed(1) + ' KB');
}
const extra = { blueprintParts: manifest.find((m) => m.file === 'blueprints.json').parts, waxCast: manifest.find((m) => m.file === 'wax_scenes.json').castTotal, bookPages: books.reduce((a, b) => a + b.pages.length, 0), presetBranches: branches.length, benchSteps: manifest.find((m) => m.file === 'bench_kits.json').steps };
fs.writeFileSync(path.join(OUT, '_manifest.json'), JSON.stringify({ generated: new Date().toISOString(), repo: ROOT, threeVersion: '0.170.0', datasets: manifest, totals: extra }, null, 2) + '\n');
console.log(report.join('\n'));
console.log('totals:', JSON.stringify(extra));
console.log(ok ? 'ALL DATASETS VALID' : 'VALIDATION FAILED');
process.exit(ok ? 0 : 1);
