/* ================================================================
   Preset answers: every staff member answers common questions on their own
   ================================================================ */
const STOP = new Set(('a an the and or but if of to in on at by for with from into onto over under about as is are was were be been being am do does did doing done have has had having i me my mine ' +
  'you your yours he him his she her hers it its we us our they them their this that these those there here what which who whom whose when where why how can could would should will shall may might must ' +
  'not no please tell show give get got find let lets like just some any much many more most very really also too so than then such thing things something anything stuff kind sort want wanted need know ' +
  'think say said go going went come came see look looking one ones ok okay hey hi hello whats wheres hows thats im youre theres does dont can cant').split(/\s+/));
const KEEP2 = new Set(['vr', 'ar', 'xr', 'ai', 'mr', '3d', 'it']);
function toks(s){ return String(s).toLowerCase().replace(/[’']/g, '').replace(/[^a-z0-9\s]/g, ' ').split(/\s+/).filter((w) => w && !STOP.has(w) && (w.length > 2 || KEEP2.has(w) || /^\d+$/.test(w))); }
function same(a, b){ if (a === b) return true; const n = Math.min(a.length, b.length); if (n < 4 || Math.abs(a.length - b.length) > 3) return false; return a.startsWith(b) || b.startsWith(a); }
function splitSents(t){
  const safe = String(t).replace(/(\d)\.(\d)/g, '$1\u00a7$2').replace(/\b(Mr|Mrs|Ms|Dr|St|U\.S)\./g, '$1\u00b6');
  return (safe.match(/[^.!?]+[.!?]+["”’)]*|[^.!?]+$/g) || [safe]).map((s) => s.replace(/\u00a7/g, '.').replace(/\u00b6/g, '.').trim()).filter(Boolean);
}

const KB = [];
function addKB(kind, ref, title, text){ const sents = splitSents(text).map((t) => ({ t, toks:toks(t) })); KB.push({ kind, ref, title, text, sents, toks:toks(text), ttoks:toks(title) }); }
function buildKB(){
  for (const it of ITEMS.concat([FREEDOM], WAX_ITEMS)) addKB('item', it, it.title, [it.desc, it.more || '', it.quote ? it.quote + ' ' + (it.quoteBy || '') + '.' : '', it.where ? 'Location: ' + it.where + '.' : '', it.partners ? 'Partners: ' + it.partners + '.' : ''].join(' '));
  for (const f of FACTS) addKB('fact', f, f.id === 'what' ? 'XRLibraries' : f.id, f.text);
  for (const b of BOOKS) b.pages.forEach((p, i) => addKB('page', { book:b, page:i }, b.title + ' ' + p.h, p.b.map(blockText).join(' ')));
  for (const id of BP_ORDER){
    const B = BP_INFO[id];
    addKB('part', { id, i:null }, B.title + ' blueprint', B.overview + ' ' + B.jobs);
    B.parts.forEach((p, i) => addKB('part', { id, i }, p.name + ' ' + B.title, [p.short + '.', p.what, p.fact, p.model].join(' ')));
  }
  for (const L of LESSONS) addKB('lesson', L, L.title, L.text);
}
/* What the lab, bench and layer table teach, so staff can answer questions about them */
const LESSONS = [
  { station:'sieve', title:'How a sieve test works: sieve analysis, particle size distribution, PSD', text:'A sieve analysis measures particle size distribution, or PSD: how much of a sample falls in each size range. You split out a representative sample, dry it and weigh it, then shake it through a stack of sieves, coarsest on top and finest at the bottom, and weigh what each sieve holds. Sand and gravel producers use sieve tests to check that their product meets its size specification.' },
  { station:'sieve', title:'Sieve mesh numbers and openings', text:'A sieve’s mesh number counts the openings per inch, so a bigger number means a finer sieve. A US number 20 sieve has 850 micrometer openings, a number 40 has 425 and a number 100 has 150. One micrometer is a thousandth of a millimeter.' },
  { station:'sieve', title:'Cumulative percent passing and D50', text:'For each sieve you work out the percent retained, add them up from the top to get the cumulative percent retained, and subtract from 100 to get the percent passing. D50 is the grain size that half the sample is finer than. D10 and D60 give the uniformity coefficient, Cu = D60 ÷ D10; a Cu near 1 means the grains are nearly all the same size.' },
  { station:'sieve', title:'AFS grain fineness number GFN', text:'The AFS grain fineness number, or GFN, multiplies the percent retained on each sieve by a factor for that sieve, adds them up and divides by the total percent retained. A higher number means finer sand. Foundries use it to describe molding sand.' },
  { station:'sieve', title:'Checking a finished sieve run for lost mass', text:'After a sieve test, the sieve weights should add back up to the starting weight. ASTM C136, a standard sieve test for aggregates, says that if the difference is more than 0.3 percent of the starting dry mass, the results should not be used for acceptance testing.' },
  { station:'titration', title:'Acid base titration', text:'In a titration you add a solution of known concentration from a burette, a little at a time, until it exactly reacts with your sample. An indicator such as phenolphthalein turns pink when the solution turns basic, which marks the endpoint. For an acid like HCl reacting with NaOH, moles of base equal moles of acid, so the acid’s molarity = base molarity × base volume ÷ acid volume.' },
  { station:'titration', title:'pH and the equivalence point', text:'pH measures how acidic a solution is: 7 is neutral, lower is acidic and higher is basic, and each step of 1 is a tenfold change. When a strong acid is titrated with a strong base, the pH jumps sharply near the equivalence point, where the moles of base added equal the moles of acid.' },
  { station:'pendulum', title:'Pendulum period and gravity', text:'A simple pendulum’s period, the time for one full swing out and back, is about T = 2π√(L/g) for small swings. It depends on the length, not the mass. Time 10 swings and divide by 10 for a better measurement. Plot T² against L for a few lengths, and the slope equals 4π²/g, so g = 4π² ÷ slope, about 9.8 meters per second squared on Earth.' },
  { station:'bench', title:'Rubber band car model', text:'A rubber-band car stores energy in a stretched rubber band. As the band unwinds, it turns the rear axle and drives the car forward. Drinking straws make good bearings, so the axles spin with little friction. Test it, change one thing at a time and test again.' },
  { station:'bench', title:'Cross bracing and shake tables', text:'Cross-bracing turns a frame’s rectangles into triangles, and a triangle can’t change shape unless a side changes length, so a braced frame resists racking in earthquakes and wind. Engineers test buildings and models on shake tables that move back and forth like an earthquake.' },
  { station:'diorama', title:'How to build a 3D world', text:'A 3D world gets built in layers: plan it, block it out with plain boxes, model the shapes, add materials, light it, add effects like glow and fog, add physics, add life like people and rides, then publish it and improve it. This campus runs in a web browser using three.js for 3D and the Rapier physics engine for the playground.' }
];
function searchKB(q, kinds){
  const Q = [...new Set(toks(q))]; if (!Q.length) return [];
  const N = KB.length, idf = Q.map((t) => Math.log(1 + N / (KB.filter((p) => p.toks.some((u) => same(t, u)) || p.ttoks.some((u) => same(t, u))).length + 0.5)));
  const total = idf.reduce((a, b) => a + b, 0) || 1;
  return KB.filter((p) => !kinds || kinds.includes(p.kind)).map((p) => {
    let sc = 0, cov = 0;
    Q.forEach((t, i) => { let tf = 0; for (const u of p.toks) if (same(t, u)) tf++; const inT = p.ttoks.some((u) => same(t, u)); if (tf || inT){ sc += idf[i] * (1 + 0.3 * Math.min(3, Math.max(0, tf - 1))) + (inT ? idf[i] * 0.8 : 0); cov += idf[i]; } });
    return { p, score:sc, cov:cov / total, Q };
  }).filter((x) => x.score > 0).sort((a, b) => b.score - a.score);
}
function qtype(q){ const s = q.toLowerCase(); if (/^\s*when\b|what year|how long ago/.test(s)) return 'when'; if (/how many|how much|number of/.test(s)) return 'num'; if (/^\s*who\b/.test(s)) return 'who'; return ''; }
function bestSentence(p, Q, qt){
  let best = -1, bi = 0;
  p.sents.forEach((s, i) => {
    let sc = 0; for (const t of Q) if (s.toks.some((u) => same(t, u))) sc += 1;
    if (qt === 'when' && /\b(1[89]\d\d|20\d\d)\b/.test(s.t)) sc += 1.2;
    if (qt === 'num' && /\d/.test(s.t)) sc += 1;
    if (qt === 'who' && /\b[A-Z][a-z]+ [A-Z][a-zA-Z]+/.test(s.t)) sc += 0.8;
    if (sc > best){ best = sc; bi = i; }
  });
  let t = p.sents[bi].t;
  if (t.length < 100 && p.sents[bi + 1]) t += ' ' + p.sents[bi + 1].t;
  return t;
}

/* Places staff can walk you to */
const PLACES = [
  { id:'lobby', label:'Lobby', names:['lobby', 'entrance', 'front door', 'start', 'directory', 'beginning'], view:() => ({ x:0, z:-2.2, yaw:0, pitch:0.02 }) },
  { id:'g1', label:'Gallery 1: Headsets in Libraries', names:['gallery 1', 'gallery one', 'first gallery', 'headsets in libraries', 'museum', 'galleries', 'exhibits'], view:() => ({ x:0, z:-8.4, yaw:0, pitch:0.02 }) },
  { id:'g2', label:'Gallery 2: Learning That Works', names:['gallery 2', 'gallery two', 'second gallery', 'learning that works'], view:() => ({ x:0, z:-20.4, yaw:0, pitch:0.02 }) },
  { id:'g3', label:'Gallery 3: Stories Worth Saving', names:['gallery 3', 'gallery three', 'third gallery', 'stories worth saving'], view:() => ({ x:0, z:-32.4, yaw:0, pitch:0.02 }) },
  { id:'library', label:'The Reading Room', names:['library', 'reading room', 'bookshelves', 'shelves', 'stacks', 'books'], view:() => ({ x:-13.4, z:-3, yaw:Math.PI / 2, pitch:0.08 }) },
  { id:'desk', label:'Reference desk', names:['reference desk', 'librarian', 'rosa', 'help desk', 'front desk'], view:() => STAFF.rosa.view },
  { id:'featured', label:'Featured books table', names:['featured books', 'featured table', 'display table', 'featured'], view:() => ({ x:-15, z:-0.9, yaw:Math.PI, pitch:-0.32 }) },
  { id:'freedomBoard', label:'Freedom to Read display', names:['freedom to read', 'book bans', 'banned books'], view:() => ({ x:-18.9, z:1.0, yaw:Math.PI / 2, pitch:-0.02 }) },
  { id:'window', label:'Library window', names:['window', 'big window'], view:() => ({ x:-29.5, z:-3, yaw:Math.PI / 2, pitch:0.14 }) },
  { id:'school', label:'Workshop School hall', names:['school', 'workshop school', 'hallway', 'classes', 'classrooms', 'lockers'], view:() => ({ x:12.9, z:-3, yaw:-Math.PI / 2, pitch:0.02 }) },
  { id:'studio', label:'Room 101: 3D Art Studio', names:['studio', 'art studio', 'paint studio', 'room 101', 'workshop', 'painting', 'art room', '3d art', 'blank canvas', 'mr hale', 'hale', 'teacher', 'easel'], view:() => ({ x:19, z:-5.7, yaw:0, pitch:0.02 }) },
  { id:'lab', label:'Room 102: Science Lab', names:['science lab', 'the lab', 'lab', 'room 102', 'laboratory', 'chemistry lab', 'physics lab', 'science room'], view:() => ({ x:29, z:-5.9, yaw:0, pitch:-0.06 }) },
  { id:'sieve', label:'Sieve shaker', say:'the sieve shaker', names:['sieve', 'sieves', 'sieve shaker', 'sieve test', 'sieve analysis', 'psd', 'particle size', 'grain size', 'sand test'], view:() => STATIONS.sieve.view() },
  { id:'titration', label:'Titration station', say:'the titration station', names:['titration', 'burette', 'acid base', 'chemistry'], view:() => STATIONS.titration.view() },
  { id:'pendulum', label:'Pendulum', say:'the pendulum', names:['pendulum', 'gravity experiment', 'physics experiment'], view:() => STATIONS.pendulum.view() },
  { id:'blueprints', label:'Room 103: Blueprint Lab', names:['blueprint lab', 'blueprints', 'blueprint', 'room 103', 'engineering room', 'engineering'], view:() => ({ x:18.1, z:3.6, yaw:Math.PI, pitch:0.03 }) },
  { id:'bp-car', label:'Automobile blueprint', say:'the automobile blueprint', names:['car blueprint', 'automobile blueprint', 'automobile'], view:() => bpViewFor('car') },
  { id:'bp-excavator', label:'Excavator blueprint', say:'the excavator blueprint', names:['excavator blueprint', 'excavator', 'heavy equipment', 'digger'], view:() => bpViewFor('excavator') },
  { id:'bp-house', label:'House blueprint', say:'the house blueprint', names:['house blueprint', 'building blueprint', 'house framing'], view:() => bpViewFor('house') },
  { id:'bp-bridge', label:'Truss bridge blueprint', say:'the bridge blueprint', names:['bridge blueprint', 'truss bridge', 'bridge'], view:() => bpViewFor('bridge') },
  { id:'bp-computer', label:'Computer blueprint', say:'the computer blueprint', names:['computer blueprint', 'pc blueprint', 'computer parts', 'motherboard'], view:() => bpViewFor('computer') },
  { id:'modelbench', label:'Model bench', say:'the model bench', names:['model bench', 'model car', 'shake table', 'bench'], view:() => STATIONS.bench.view() },
  { id:'worldroom', label:'Room 104: World Builder Studio', names:['world builder studio', 'world builder', 'room 104', 'world building', 'game design', 'game room'], view:() => ({ x:29, z:0.6, yaw:Math.PI, pitch:-0.18 }) },
  { id:'diorama', label:'Layer table', say:'the layer table', names:['layer table', 'diorama', 'mini world'], view:() => STATIONS.diorama.view() },
  { id:'sculpture', label:'Sample sculpture', names:['sculpture', 'sample sculpture', 'butterfly'], view:() => ({ x:21.6, z:-7.6, yaw:0, pitch:0.12 }) },
  { id:'margaret', label:'Margaret', names:['margaret', 'museum guide', 'greeter'], view:() => STAFF.margaret.view },
  { id:'wax', label:'The Wax Hall', say:'the Wax Hall', names:['wax hall', 'wax museum', 'wax figures', 'wax figure', 'living history', 'reenactments', 'reenactment', 'history hall', 'the wax'], view:() => ({ x:0, z:-46.4, yaw:0, pitch:0.02 }) },
  { id:'yard', label:'The Recess Yard', names:['recess yard', 'recess', 'playground', 'the yard', 'yard', 'outside', 'rides', 'play outside'], view:() => ({ x:38.6, z:-3, yaw:-Math.PI / 2, pitch:0.06 }) },
  { id:'coaster', label:'Comet Coaster', names:['comet coaster', 'roller coaster', 'rollercoaster', 'coaster'], view:() => ({ x:50.2, z:-3.4, yaw:lookYaw(50.2, -3.4, 58, -14), pitch:0.2 }) },
  { id:'drop', label:'Sky Drop', names:['sky drop', 'skydrop', 'drop tower', 'the tower'], view:() => ({ x:64.5, z:4.5, yaw:lookYaw(64.5, 4.5, 78, 13), pitch:0.32 }) },
  { id:'dive', label:'Ocean Dive', names:['ocean dive', 'the dive', 'dive dome', 'underwater', 'scuba', 'dive'], view:() => ({ x:54, z:4.2, yaw:Math.PI, pitch:0.1 }) },
  { id:'rae', label:'Coach Rae', names:['coach rae', 'rae', 'coach', 'recess coach'], view:() => STAFF.rae.view },
  { id:'field', label:'Soccer goal', say:'the soccer goal', names:['soccer goal', 'soccer field', 'ball field', 'the goal', 'goal', 'soccer', 'penalty', 'goalkeeper', 'keeper'], view:() => ({ x:77.75, z:-2.0, yaw:-Math.PI / 2, pitch:-0.1 }) },
  { id:'blocks', label:'Block tower', say:'the block tower', names:['block tower', 'foam blocks', 'tower of blocks', 'blocks'], view:() => ({ x:61.2, z:1.5, yaw:-Math.PI / 2, pitch:-0.08 }) }
].concat(SUBJECTS.map((s) => ({ id:'sec-' + s.id, label:s.name + ' section', names:[s.name.toLowerCase() + ' section', s.name.toLowerCase() + ' shelf', s.name.toLowerCase() + ' books'], view:() => SHELF_VIEWS[s.id] })));
function norm(q){ return ' ' + String(q).toLowerCase().replace(/[’']/g, '').replace(/[^a-z0-9\s]/g, ' ').replace(/\s+/g, ' ').trim() + ' '; }
function findPlace(q){ const s = norm(q); let best = null, bl = 0; for (const p of PLACES) for (const n of p.names){ if (s.includes(' ' + n + ' ') && n.length > bl){ best = p; bl = n.length; } } return best; }

const RX = {
  hi:/^\s*(hi|hello|hey|howdy|yo|good (morning|afternoon|evening))\b/,
  thanks:/\b(thanks|thank you|thx|appreciate it)\b/,
  bye:/\b(bye|goodbye|see you|see ya|later)\b/,
  who:/\b(who|what) are you\b|\byour name\b|\bare you (an? )?(ai|robot|bot|real|person|human)\b/,
  help:/\bhelp\b|what can you do|what do you do|how does this work/,
  where:/\bwhere am i\b|what is this place|whats this place|what is this\b|what am i looking at/,
  made:/\bwho (made|built|created) (this|it|the campus)\b|is this (official|real|xrlibraries)|\bofficial\b/,
  wta:/walk the archive/,
  go:/\b(take|bring|walk|lead) me\b|\bgo to\b|\bshow me the way\b|\bhow do i get to\b|\blets go\b/,
  wh:/\bwhere('?s| is| are| can i find| do i find)\b/,
  joke:/\bjoke\b|make me laugh|something funny/,
  hours:/\b(hours|open|close|closing)\b.*\b(when|what time|hours)\b|\bwhat time\b.*\b(open|close)\b/,
  bath:/\b(bathroom|restroom|toilet)\b/,
  move:/how do i (move|walk|look|turn|get around)|controls/,
  paint:/\b(paint|draw|tilt brush|brush|sculpt)\b/,
  startPaint:/^\s*(start|let'?s|begin) (painting|to paint|the workshop|workshop)|^\s*start painting\s*$|\bstart (the )?paint/,
  oldest:/\b(oldest|earliest|first)\b.*\b(exhibit|thing|item|here)\b|\b(newest|latest|most recent)\b/,
  count:/how many (exhibits|items|things|books|galleries|sections|rides|scenes|wax figures|figures)/,
  recommend:/recommend|suggest a book|what should i read|good book|something to read/,
  booksAbout:/\bbooks? (about|on)\b|do you have (a |any )?books?/,
  sections:/\b(sections|subjects|categories)\b/,
  what:/what (is|are|does) xr ?libraries|tell me about xr ?libraries|^\s*xr ?libraries\??\s*$|what do they do/,
  director:/\b(director|who runs|who leads|in charge|founder|ceo)\b/,
  workshops:/other (workshops|classes|rooms)|what (workshops|classes|rooms)|which (workshops|classes|rooms)|workshops are there|what can i (do|make|learn) (here|in the school)/,
  blank:/\bblank (canvas|page|room)\b|\bempty (canvas|room)\b|\bclean canvas\b|\bnew canvas\b/,
  startLab:/^\s*(start|begin|do|run|try|let'?s (do|try|run|start)|i want to (do|try|run))\s+(the |a |an )?(sieve( test| analysis)?|psd|titration|pendulum|lab test)/,
  openBp:/^\s*(open|show me|let'?s see|i want to see)\s+(the |a |an )?(car|automobile|excavator|digger|heavy equipment|house|building|bridge|computer|pc)\s+blueprint/,
  buildModel:/\b(build|make)\s+(a |an |my own )?(model|mini) (car|house|building)\b/,
  labq:/\b(science lab|room 102|lab work|experiments?|labs)\b/,
  bpq:/\bblueprints?\b|\broom 103\b/,
  worldq:/\b(world builder|room 104|build (a|my own|your own|a whole) (world|game)|make (a|my own|your own) (world|game|3d world)|game design|how (was|is|did) (this|the campus|you) (made|built|make|build)|how (do|can) (i|you) (make|build) (a world|a game|something like this|this))\b/,
  rideNow:/^\s*(ride|start|try|go on|let'?s (ride|go on|do|try|start)|i want to (ride|go on|try)|can i (ride|go on|try)|take me on)\b/,
  coaster:/\b(coaster|roller ?coaster|rollercoaster|comet)\b/,
  dropq:/\b(sky ?drop|drop tower|free ?fall)\b/,
  diveq:/\b(dive|diving|underwater|scuba|sea creatures?|manta|whale shark|jellyfish|sea turtle|clownfish|kelp)\b/,
  tokens:/\b(tokens?|easter eggs?|secrets?|collectibles?)\b|\bhidden (things|stuff|items|gems)\b/,
  badges:/\b(badges?|achievements?|rewards?|prizes?|trophies|trophy)\b/,
  safety:/\b(scary|scared|safe|safety|sick|dizzy|motion sick|nause\w*|afraid|too fast|slow down|gentle)\b/,
  recess:/\b(recess|playground|the yard|rides?|games?|have fun|play)\b/,
  play:/\b(balls?|kick\w*|soccer|football|foam blocks?|block tower|blocks|physics|swings?|swinging|merry[- ]?go[- ]?round|spinner)\b/,
  stats:/\bhow (fast|tall|high|long|big|deep)\b/,
  wax:/\bwax\b|living history|re-?enact\w*/,
  history:/\b(history|timeline)\b|\bwhen did (xr ?libraries|it|they) (start|begin|get started)\b|\bhow did (xr ?libraries|it|they) (start|begin|get started)\b|\bfrom the (very )?beginning\b/
};
const JOKES = {
  margaret:'Why do VR headsets make great museum guides? They always help you see the big picture.',
  rosa:'Why was the library so tall? It had a lot of stories.',
  hale:'Why did the engineer bring a ladder to the Blueprint Lab? To take the design to the next level.',
  rae:'Why did the roller coaster get good grades? It always stayed on track.'
};
function reply(text, extra){ return Object.assign({ text, cards:[], conf:1 }, extra || {}); }
function itemCard(it){ return { type:'item', it }; }
function bookCard(b, page){ return { type:'book', b, page:page || 0 }; }
function placeCard(p){ return { type:'place', p }; }
function rideCard(id){ return { type:'ride', id }; }
function badgesCard(){ return { type:'badges' }; }
function whichRide(s){ if (RX.coaster.test(s)) return 'coaster'; if (RX.dropq.test(s) || /\bdrop\b/.test(s)) return 'drop'; if (RX.diveq.test(s) || /\b(ocean|fish|reef|turtle|shark)\b/.test(s)) return 'dive'; return null; }
function dropKmh(){ return Math.round(Math.sqrt(2 * 9.81 * (DROP.top - 13)) * 3.6); }
function rideAbout(id){
  const S = COASTER.stats;
  if (id === 'coaster') return 'The Comet Coaster climbs a ' + S.height + '-meter lift hill, drops toward the grass at up to ' + S.kmh + ' km/h, then flips you through a loop. Want to ride?';
  if (id === 'drop') return 'The Sky Drop lifts you about 30 meters up, high enough to see the whole campus, then drops you back down.';
  return 'The Ocean Dive is a guided swim past a coral reef and a kelp forest, with fish schools, a sea turtle, a whale shark, a manta ray and jellyfish. It’s inspired by ocean VR like Hydrous, a partner listed by XRLibraries.';
}
function rideStats(id){
  const S = COASTER.stats;
  if (id === 'coaster') return 'The lift hill is about ' + S.height + ' meters tall, the loop is about ' + S.loop + ' meters tall, and the top speed is about ' + S.kmh + ' km/h (' + S.mph + ' mph). The track is about ' + S.length + ' meters long.';
  if (id === 'drop') return 'The Sky Drop tower is about ' + DROP.h + ' meters tall. The seats ride up to about 30 meters, then free-fall at up to about ' + dropKmh() + ' km/h before the brakes kick in.';
  return 'The dive goes down to about 12 meters deep and takes about a minute. It’s a calm, slow swim.';
}
function rideSafety(id){
  if (id === 'dive') return 'The Ocean Dive is calm and slow, and nothing down there will hurt you. You can pause or surface any time.';
  return 'It’s a virtual ride, so you’re safe, but it can feel fast. Pick Gentle ride for a slower version, and tap Exit ride any time.';
}
function tokenText(){ return 'There are ' + TOKENS.length + ' glowing XR tokens hidden around the campus: in the museum, the library, the school hall, every workshop room and the Recess Yard, plus one on each ride. Tap one to collect it. You’ve found ' + prog.tokens.size + ' so far. Badges at the top has hints.'; }
function badgeText(){ return 'You can unlock ' + BADGES.length + ' badges, like Museum Explorer, Bookworm, Coaster Rider and Deep Diver. You have ' + prog.badges.size + ' so far. Tap Badges at the top to see them all.'; }
function srcLine(keys){ const s = srcList(keys)[0]; return s ? ' (Source: ' + s.label + '.)' : ''; }
function recommend(q, n){
  const s = norm(q), hits = BOOKS.filter((b) => s.includes(' ' + SUBJ[b.subject].name.toLowerCase() + ' ') || toks(b.title + ' ' + b.sub).some((t) => toks(q).some((u) => same(t, u))));
  const pool = hits.length ? hits : BOOKS.filter((b, i) => i % 2 === 0);
  return pool.slice(0, n || 3);
}

function presetAnswer(staffId, q){
  const st = STAFF[staffId], s = q.toLowerCase().trim(), words = toks(q).length;
  if (RX.hi.test(s) && words <= 2) return reply(greetingShort(staffId));
  if (RX.thanks.test(s) && words <= 4) return reply('You’re welcome! Ask me anything else about the campus.');
  if (RX.bye.test(s) && words <= 3) return reply('Come back anytime. The campus never closes.');
  if (RX.who.test(s)) return reply('I’m ' + st.name + ', the ' + st.role.toLowerCase() + ' here. I’m a virtual staff member, not a real person. I answer common questions from what this campus knows' + (aiOn() ? ', and I can use AI for harder ones.' : '.'));
  if (RX.help.test(s)) return reply(helpText(staffId));
  if (RX.made.test(s)) return reply('This campus is an unofficial concept that Ev Holt made with Walk the Archive for XRLibraries. It is not an official XRLibraries site. The facts come from public sources like xrlibraries.com.');
  if (RX.wta.test(s)) return reply(FACTS.find((f) => f.id === 'wta').text);
  if (RX.where.test(s)) return reply('You’re in the XRLibraries Campus, a concept made by Ev Holt. The museum tells XRLibraries’ story, the library holds books about XR, the Workshop School has four hands-on rooms for art, science, blueprints and world building, and recess is out back in the Recess Yard.', { cards:[placeCard(PLACES.find((p) => p.id === 'library')), placeCard(PLACES.find((p) => p.id === 'school')), placeCard(PLACES.find((p) => p.id === 'yard'))] });
  if (RX.joke.test(s)) return reply(JOKES[staffId]);
  if (RX.bath.test(s)) return reply('Good news: nobody needs a restroom in a virtual campus. Anything else I can help with?');
  if (RX.hours.test(s)) return reply('The campus never closes. It’s open whenever you are, on a phone, a laptop or a library computer.');
  if (RX.move.test(s)) return reply(COARSE ? 'Tap the floor to walk or use the stick in the corner, drag to look around, and tap anything that looks interesting. The jump button hops. The campus map in the corner takes you to any room.' : 'Click the floor to walk, drag to look around, or use W A S D. Hold Shift to run and press Space to jump. The campus map in the corner takes you to any room.');
  if (RX.startPaint.test(s)) return reply('Let’s paint! I’ll take you to the easel. Drag to paint in the air, then walk around your work.', { action:'paint' });
  if (RX.blank.test(s)) return reply('Here’s a blank canvas: the room disappears and it’s just you and your art. Switch to Night for a starry sky, or back to Room any time.', { action:'paintBlank' });
  if (RX.startLab.test(s)){ const k = /titration/.test(s) ? 'titration' : /pendulum/.test(s) ? 'pendulum' : 'sieve'; return reply(k === 'sieve' ? 'Goggles on! Let’s run a sieve analysis on a sand sample.' : k === 'titration' ? 'Goggles on! Let’s find out how concentrated the mystery acid is.' : 'Let’s measure gravity with a pendulum.', { action:'station:' + k }); }
  if (RX.openBp.test(s)){ const w = s.match(RX.openBp)[3], id = /car|auto/.test(w) ? 'car' : /exca|digg|heavy/.test(w) ? 'excavator' : /house|build/.test(w) ? 'house' : /bridge/.test(w) ? 'bridge' : 'computer'; return reply('Here’s the ' + BP_INFO[id].title.toLowerCase() + ' blueprint. Tap any numbered part to learn what it does.', { action:'bp:' + id }); }
  if (RX.buildModel.test(s)) return reply('Head to the model bench in Room 103. You can build a rubber-band car or a two-story building with cross-bracing, one step at a time, then test it.', { action:'station:bench' });
  if (RX.workshops.test(s)) return reply('All four workshop rooms are open. Room 101 is the 3D Art Studio, Room 102 is the Science Lab, Room 103 is the Blueprint Lab and Room 104 is the World Builder Studio.', { action:'workshops' });
  const travel = RX.go.test(s) || RX.wh.test(s);
  if (RX.worldq.test(s) && !travel) return reply('Room 104, the World Builder Studio, shows how a world like this campus gets made. Build a mini world on the layer table one layer at a time, from a sketch to a live website, then read the World Builder’s Handbook to start your own.', { cards:[stationCard('diorama'), bookCard(BOOK['world-builder'])] });
  if (RX.labq.test(s) && !travel && !/\b(sieve|psd|titrat|pendulum)/.test(s)) return reply('The Science Lab in Room 102 has three hands-on labs: a sieve analysis that measures the grain sizes in sand, an acid–base titration that finds the concentration of a mystery acid, and a pendulum that measures gravity.', { cards:[stationCard('sieve'), stationCard('titration'), stationCard('pendulum')] });
  if (RX.bpq.test(s) && !travel && toks(q).length <= 4) return reply('A blueprint is a technical drawing of a design, with every part labeled. In the Blueprint Lab, Room 103, tap any numbered part on a car, excavator, house, bridge or computer blueprint to learn its name, what it does and how you could build one.', { cards:[bpCard('car'), bpCard('bridge'), stationCard('bench')] });
  if (RX.paint.test(s) && (staffId === 'hale' || /\b(3d|air|studio|tilt)\b/.test(s))) return reply('In the 3D Art Studio, you draw in the air with brushes like Neon, Ribbon, Chrome and Rainbow, or stamp 3D shapes like stars, hearts and cubes. Turn on Mirror or ×6 to make symmetric art, spin it on the turntable, and switch to a blank canvas to work with nothing else around. It’s inspired by VR art apps like Tilt Brush, which XR Showcase featured.', { action:'paintOffer' });
  if (RX.what.test(s)) { const f = FACTS.find((x) => x.id === 'what'); return reply(f.text + ' Its website is xrlibraries.com.', { cards:[itemCard(ITEM['ca-200']), itemCard(ITEM.mission)] }); }
  if (RX.director.test(s) && /xr|librar|run|lead|charge|director/.test(s)) return reply(FACTS.find((x) => x.id === 'who').text + srcLine(['sjsu']));
  if (RX.rideNow.test(s)){ const rd = whichRide(s); if (rd) return reply(rd === 'dive' ? 'Let’s dive! I’ll get you suited up.' : 'Let’s ride! Hold on tight.', { action:'ride:' + rd }); }
  if (RX.tokens.test(s)) return reply(tokenText(), { cards:[badgesCard()] });
  if (RX.badges.test(s)) return reply(badgeText(), { cards:[badgesCard()] });
  if (RX.wax.test(s) && !RX.go.test(s) && !RX.wh.test(s)) return reply(FACTS.find((x) => x.id === 'wax').text, { cards:[placeCard(PLACES.find((p) => p.id === 'wax')), itemCard(WAX_ITEMS[0])] });
  const yr = s.match(/\b(20[12]\d)\b/);
  if (yr && !travel && !whichRide(s) && /\bhappen|\bwhat\b|\b(in|during) 20[12]\d\b/.test(s)){
    const y = yr[1], wax = WAX_ITEMS.filter((it) => String(it.year).indexOf(y) >= 0), ex = ITEMS.filter((it) => String(it.year) === y);
    const list = wax.length ? wax : ex;
    if (list.length){
      const n = list.length, names = list.map((it, i) => '“' + it.title + ((i < n - 2 || (i === n - 1 && wax.length)) ? ',”' : '”'));
      const joined = n > 1 ? names.slice(0, -1).join(' ') + ' and ' + names[n - 1] : names[0];
      return reply('From ' + y + ', the campus shows ' + joined + (wax.length ? (n > 1 ? ' each acted out in the Wax Hall.' : ' acted out in the Wax Hall.') : ' in the museum.'), { cards:list.slice(0, 3).map((it) => itemCard(it)) });
    }
  }
  if (RX.history.test(s) && !RX.go.test(s) && !RX.wh.test(s) && !RX.wax.test(s)) return reply(FACTS.find((x) => x.id === 'history').text + ' The Wax Hall acts it all out, scene by scene.', { cards:[itemCard(WAX_ITEMS[0]), placeCard(PLACES.find((p) => p.id === 'wax'))] });
  const place = findPlace(q);
  if (place && (RX.go.test(s) || RX.wh.test(s))){
    const goNow = RX.go.test(s);
    return reply((goNow ? 'Follow me to ' : 'That’s ') + (goNow ? (place.say || place.label) + '.' : directions(place)), { cards:goNow ? [] : [placeCard(place)], go:goNow ? { type:'place', p:place } : null });
  }
  if (RX.oldest.test(s) && staffId !== 'hale'){
    const dated = ITEMS.filter((it) => it.year), old = !/newest|latest|most recent/.test(s);
    const it = dated.sort((a, b) => old ? a.year - b.year : b.year - a.year)[0];
    const goNow = RX.go.test(s) || /\bshow me\b/.test(s);
    return reply((goNow ? 'Follow me. ' : '') + 'The ' + (old ? 'earliest' : 'most recent') + ' dated exhibit is “' + it.title + ',” from ' + it.year + '.', { cards:[itemCard(it)], go:goNow ? { type:'item', it } : null });
  }
  if (RX.count.test(s)){
    if (/book/.test(s)) return reply('Thousands of books line the shelves, and ' + BOOKS.length + ' of them are open to read right now, on the featured table and on the ends of the stacks.', { cards:[placeCard(PLACES.find((p) => p.id === 'featured'))] });
    if (/section|categor/.test(s)) return reply('The library has eight sections: ' + SUBJECTS.map((x) => x.name).join(', ') + '.');
    if (/ride/.test(s)) return reply('The Recess Yard has three rides: the Comet Coaster, the Sky Drop and the Ocean Dive.', { cards:[rideCard('coaster'), rideCard('drop'), rideCard('dive')] });
    if (/scene|wax|figure/.test(s)) return reply('The Wax Hall has 12 living-history scenes, from 2016 to 2025, with wax figures that act each one out.', { cards:[placeCard(PLACES.find((p) => p.id === 'wax'))] });
    return reply('The museum has ' + ITEMS.length + ' exhibits in three galleries: Headsets in Libraries, Learning That Works, and Stories Worth Saving.', { cards:[placeCard(PLACES.find((p) => p.id === 'g1'))] });
  }
  if (RX.sections.test(s) && staffId === 'rosa') return reply('Our eight sections are ' + SUBJECTS.map((x) => x.name).join(', ') + '. Each stack has its featured books on the end facing the aisle.');
  if (RX.recommend.test(s) || (RX.booksAbout.test(s) && staffId !== 'margaret')){
    const list = recommend(q, 3);
    return reply(list.length === 1 ? 'Try this one:' : 'Here are a few good ones:', { cards:list.map((b) => bookCard(b)) });
  }
  if (RX.play.test(s) && !whichRide(s) && staffId !== 'hale' && !/\b(bearing|pendulum|swing time)\b/.test(s)) return reply('Out in the Recess Yard, the balls, the foam-block tower and the soccer goal all run on real physics. At the soccer goal by the east fence, walk up to the ball and hold to power up (hold F, press and hold on the ball, or use the Kick button), look where you want it to go and let go. A keeper dives for it, and a goal earns the Striker badge. Walk into a ball to dribble it. You can push the swings and spin the merry-go-round too.', { cards:[placeCard(PLACES.find((p) => p.id === 'field')), placeCard(PLACES.find((p) => p.id === 'blocks'))] });
  const rd = whichRide(s), complex = /\b(which|why|best|better|worst|compare|favou?rite|should i|would you|could you|if you were|what if)\b/.test(s) || words > 7, cf = complex ? 0.5 : 1;
  if (rd && RX.safety.test(s)) return reply(rideSafety(rd), { cards:[rideCard(rd)], conf:cf });
  if (rd && RX.stats.test(s)) return reply(rideStats(rd), { cards:[rideCard(rd)] });
  if (RX.safety.test(s) && (staffId === 'rae' || RX.recess.test(s))) return reply('Every ride has a Gentle mode that moves slower, and you can tap Exit any time. The Ocean Dive is the calmest ride.', { cards:[rideCard('dive')], conf:cf });
  if (rd) return reply(rideAbout(rd), { cards:[rideCard(rd)], conf:cf });
  if (RX.recess.test(s) && (staffId === 'rae' || /recess|playground|rides?\b/.test(s))) return reply('Recess has three rides: the Comet Coaster, the Sky Drop and the Ocean Dive. There are swings, a slide, a merry-go-round, a soccer goal and a block tower to knock down, plus hidden XR tokens to find.', { cards:[rideCard('coaster'), rideCard('drop'), rideCard('dive')], conf:cf });
  return searchAnswer(staffId, q);
}
function directions(place){
  const id = place.id;
  place = Object.assign({}, place, { label:place.say || place.label });
  if (['library', 'desk', 'featured', 'freedomBoard', 'window'].includes(id) || id.startsWith('sec-')) return place.label + ', through the doorway on the left side of the lobby and down the hall.';
  const hall = ', through the doorway on the right side of the lobby and down the school hall';
  if (['studio', 'sculpture'].includes(id)) return place.label + hall + '. It’s the first door on the left.';
  if (['lab', 'sieve', 'titration', 'pendulum'].includes(id)) return place.label + hall + '. It’s in Room 102, the second door on the left.';
  if (id === 'blueprints' || id === 'modelbench' || id.startsWith('bp-')) return place.label + hall + '. It’s in Room 103, the first door on the right.';
  if (['worldroom', 'diorama'].includes(id)) return place.label + hall + '. It’s in Room 104, the second door on the right.';
  if (id === 'school') return place.label + ', through the doorway on the right side of the lobby and down the hall.';
  if (['yard', 'coaster', 'drop', 'dive', 'rae', 'field', 'blocks'].includes(id)) return place.label + ', out the back door of the Workshop School. Take the doorway on the right side of the lobby and go all the way down the school hall.';
  if (['g1', 'g2', 'g3'].includes(id)) return place.label + ', straight ahead from the lobby.';
  if (id === 'wax') return place.label + ', straight ahead from the lobby through all three galleries and the doorway at the end of Gallery 3.';
  return place.label + '.';
}
function searchAnswer(staffId, q){
  const order = staffId === 'rosa' ? ['page', 'fact', 'item'] : staffId === 'hale' ? ['lesson', 'part', 'fact', 'page', 'item'] : staffId === 'rae' ? ['fact', 'page', 'item'] : ['item', 'fact', 'page'];
  const res = searchKB(q);
  if (!res.length) return reply(fallbackText(staffId), { conf:0 });
  const bias = (x) => { const oi = order.indexOf(x.p.kind); return x.score * (oi < 0 ? 0.8 : 1 + 0.25 * (2 - oi)); };
  res.sort((a, b) => bias(b) - bias(a));
  const top = res[0], qt = qtype(q), byTitle = top.p.kind === 'item' && !qt && top.Q.length && top.Q.every((t) => top.p.ttoks.some((u) => same(t, u)));
  const sent = byTitle ? splitSents(top.p.ref.desc).slice(0, 2).join(' ') : bestSentence(top.p, top.Q, qt);
  const conf = top.cov >= 0.66 && top.score >= 2.2 ? 1 : top.cov >= 0.5 && top.score >= 1.6 ? 0.6 : 0.25;
  const s = q.toLowerCase(), goNow = RX.go.test(s) || /\bshow me\b/.test(s);
  if (top.p.kind === 'item'){
    const it = top.p.ref, where = it === FREEDOM ? 'in the library' : it.scene ? 'in the Wax Hall, scene ' + it.scene.n : 'in Gallery ' + it.g;
    const more = res.filter((x) => x.p.kind === 'item' && x.p.ref !== it && x.score >= top.score * 0.6).slice(0, 1).map((x) => itemCard(x.p.ref));
    return reply(sent + ' That’s from “' + it.title + '” ' + where + '.', { cards:[itemCard(it)].concat(more), conf, go:goNow ? { type:'item', it } : null });
  }
  if (top.p.kind === 'part'){
    const { id, i } = top.p.ref, B = BP_INFO[id];
    return reply(sent + (i == null ? ' That’s on the ' + B.title.toLowerCase() + ' blueprint in Room 103.' : ' That’s the ' + B.parts[i].name.toLowerCase() + ' on the ' + B.title.toLowerCase() + ' blueprint in Room 103.'), { cards:[bpCard(id, i)], conf });
  }
  if (top.p.kind === 'lesson') return reply(sent, { cards:[stationCard(top.p.ref.station)], conf });
  if (top.p.kind === 'page'){
    const { book, page } = top.p.ref;
    return reply(sent + ' That’s in “' + book.title + ',” page ' + (page + 1) + '.', { cards:[bookCard(book, page + 1)], conf });
  }
  const f = top.p.ref;
  return reply(sent + srcLine(f.src), { conf, cards:relatedCards(f) });
}
function relatedCards(f){
  if (f.id === 'freedom') return [itemCard(FREEDOM)];
  if (f.id === 'environment') return [bookCard(BOOK['oceans-vr'])];
  if (f.id === 'wsl') return [bookCard(BOOK['making-360'])];
  return [];
}
function greetingShort(id){ return id === 'rosa' ? 'Hi there! What would you like to know?' : id === 'hale' ? 'Hey! What do you want to make today?' : id === 'rae' ? 'Hey! Ready for recess?' : 'Hello! What would you like to see?'; }
function helpText(id){
  if (id === 'rosa') return 'Ask me a question and I’ll find the answer in our books, or name a topic and I’ll recommend something. I can also walk you to any section.';
  if (id === 'hale') return 'I teach in all four workshop rooms. Say “start painting” or “give me a blank canvas,” “start the sieve test,” “open the car blueprint” or “build a model car,” or ask me how anything in the school works.';
  if (id === 'rae') return 'I run the Recess Yard. Say “ride the coaster,” “ride the Sky Drop” or “start the dive,” or ask me about the hidden XR tokens and badges.';
  return 'Ask me about XRLibraries, any exhibit, or a year, and I’ll show you where to find it. I can walk you to the Wax Hall, where wax figures act out XRLibraries’ story, or to the library, the Workshop School and the Recess Yard.';
}
function fallbackText(id){
  if (id === 'rosa') return 'That one isn’t on my shelves yet. Try asking about VR, AR, 360 video, careers, oceans or how computers work.';
  if (id === 'hale') return 'I’m not sure about that one. Ask me about 3D art, the science labs, the blueprints or how to build a world.';
  if (id === 'rae') return 'I’m not sure about that one. Ask me about the rides, the hidden XR tokens or the badges.';
  return 'I don’t see that in this museum yet. Try asking about Nevada’s headsets, Project SANDI, XR Playbooks or the Lost Stories projects.';
}
