/* ================================================================
   Living History: the twelve scenes, in date order.
   Every fact on a reading rail comes from a source listed in SOURCES.
   The figures are generic reenactors, not likenesses of real people.
   ================================================================ */
const WK = (t, o) => Object.assign({ t }, o || {});
/* Repeated little motions written as keys */
function waxClaps(t0, t1, extra){ const out = [], base = extra && extra.p; for (let t = t0, i = 0; t < t1; t += 0.32, i++){ const k = Object.assign({}, extra); k.p = base ? [base, i % 2 ? 'clapOpen' : 'clap'] : i % 2 ? 'clapOpen' : 'clap'; out.push(WK(t, k)); } return out; }
function waxWaves(t0, t1, extra){ const out = []; for (let t = t0, i = 0; t < t1; t += 0.36, i++) out.push(WK(t, Object.assign({ armR:[8, 88, 90], elR:i % 2 ? 72 : 112, head:[-4, 0, 0] }, extra))); return out; }
function waxTalk(t0, t1, pose){ return [WK(t0, Object.assign({}, pose, { talk:1 })), WK(t1, Object.assign({}, pose, { talk:0 }))]; }
/* Where hands go on the scenes' props, in each prop's own frame (metres) */
const CLIP_GRIPS = {
  L:{ p:[0.112, -0.03, 0.0], into:[-1, 0, 0.35], fingers:[0, 0.15, 1], curl:0.55 },
  R:{ p:[-0.112, -0.06, 0.0], into:[1, 0, 0.35], fingers:[0, 0.15, 1], curl:0.55 }
};
const BOX_GRIPS = {
  L:{ p:[0.252, -0.07, 0.02], into:[-1, 0, 0], fingers:[0, -0.45, 1], curl:0.18, out:0.7 },
  R:{ p:[-0.252, -0.07, 0.02], into:[1, 0, 0], fingers:[0, -0.45, 1], curl:0.18, out:0.7 }
};
/* A tablet held by its sides, screen on its -z face toward the holder, fingers round the back (+z);
   "tap" brings the right index fingertip to the screen */
const TAB_GRIPS = {
  L:{ p:[0.122, -0.01, -0.004], into:[-1, 0, 0.3], fingers:[0, 0.2, 1], curl:0.55 },
  R:{ p:[-0.122, -0.01, -0.004], into:[1, 0, 0.3], fingers:[0, 0.2, 1], curl:0.55 },
  tap:{ p:[-0.03, 0.0, -0.145], into:[0, -1, 0], fingers:[0, 0, 1], curl:0.1, point:1, out:0.3 }
};
/* A phone in the right hand, screen toward its owner */
const PHONE_GRIPS = { R:{ p:[0.0, -0.025, -0.012], into:[0, 0, 1], fingers:[-1, 0.35, 0], curl:0.62 } };
/* Typing: a palm hovering over keys, and a quick tap rhythm for its fingers */
const TYPE_GRIP = (x, y, z) => ({ p:[x, y, z], into:[0, -1, 0], fingers:[0, 0, -1], curl:0.38, out:0.65 });
const waxTyping = (ph) => (t) => [0, 0.009 * Math.max(0, Math.sin(t * 17 + ph)) * Math.max(0, Math.sin(t * 5.3 + ph * 2)), 0];
/* A tap on a screen: the fingertip pushes in and lifts off */
const waxTaps = (times) => (t) => { let d = 0; for (const a of times){ const u = (t - a) / 0.32; if (u > 0 && u < 1) d = Math.max(d, Math.sin(u * Math.PI)); } return [0, 0, 0.016 * d]; };
Object.assign(WAX_POSE, {
  clapOpen:{ armL:[42, 24, -24], armR:[42, 24, -24], elL:72, elR:72, handL:[0, 0, 60], handR:[0, 0, 60] },
  offer:{ armR:[58, 12, -24], elR:34, armL:[48, 10, -30], elL:42, handR:[0, 0, 50], handL:[0, 0, 50] },
  carry:{ armL:[42, 16, -72], armR:[42, 16, -72], elL:78, elR:78, spine:[4, 0, 0] },
  readBook:{ armL:[40, 24, -46], armR:[40, 24, -46], elL:84, elR:84, handL:[-10, 0, 40], handR:[-10, 0, 40], head:[22, 0, 0] },
  spot:{ armL:[34, 16, -20], armR:[34, 16, -20], elL:48, elR:48, chest:[6, 0, 0] },
  hipHands:{ armL:[-6, 40, -40], armR:[-6, 40, -40], elL:110, elR:110 },
  float:{ armL:[20, 72, 0], armR:[20, 72, 0], elL:14, elR:14, head:[-20, 0, 0], chest:[-6, 0, 0] },
  phone:{ armR:[72, 10, -36], elR:62, handR:[-20, 0, 70], armL:[10, 8, 0], elL:20, head:[8, 0, 0] },
  play:{ armL:[40, 10, -26], armR:[40, 10, -26], elL:70, elR:70, handL:[-24, 0, 80], handR:[-24, 0, 80], head:[18, 0, 0], chest:[4, 0, 0] }
});

const WAX_SCENES = [
/* ---------------------------------------------------------------- 1 */
{ id:'wax-2016', n:1, year:'2016', title:'The First Headsets', backdrop:'library', floor:'carpet', loop:14,
  lines:[[0, 'Marin County’s libraries open their first VR stations.'], [4.4, 'A teen volunteer helps a first-time visitor into a headset.'], [9.2, 'XRLibraries launches as the pilot’s coordinator.']],
  item:{ title:'The First Headsets', date:'2016', where:'Marin County Free Library, California', partners:'Califa, Marin County Free Library, XRLibraries', src:['cenic', 'lj2019', 'lj2017'],
    desc:'In 2016, libraries in Marin County, California, began offering virtual reality stations as the pilot for the California Virtual Reality Experience. XRLibraries launched that year as the project’s coordinator. Teen volunteers helped first-time visitors into headsets and guided them through their first worlds.',
    more:'Library Journal reported that four Marin County libraries had offered VR stations since 2016, with teens from the Marin WebStars volunteer program helping manage the stations and guide new users.' },
  build(S){
    const m = waxM();
    WP.bookcase(S, 2.25, -3.55, 1.0, 1.9, 0);
    const desk = WP.desk(S, -1.8, -3.1, 1.3, 0.62, 0.74, 0);
    WP.screen(S, desk, 0.12, 0.74, -0.1, 0, 'reef', 0.62, 0.38);
    S.box(0.44, 0.02, 0.15, m.black, -1.86, 0.755, -2.9);
    WP.pc(S, -2.62, -3.12, 0);
    WP.mat(S, 0.22, -2.0, 0.82);
    const fish = WP.fish(S, 8);
    const teen = S.fig({ av:'fa12', scale:0.93, body:'girl', skin:WAX_SKIN.medium, hair:0x2a1a12, hairStyle:'ponytail', top:0x1f7a72, bottom:0x2b3445, lanyard:0xf2c14e, shoes:0xe9e5dc, eyes:0x3a2416 }, [1.3, -1.75], -55);
    const man = S.fig({ av:'ma02', body:'man', skin:WAX_SKIN.fair, hair:0x6b4a2e, hairStyle:'short', top:0x6b7a4a, bottom:0x3a3f46, collar:0xe8e2d6, eyes:0x4a6a8a }, [0.22, -2.0], 15);
    const kid = S.fig({ av:'mc02', scale:0.88, body:'kid', skin:WAX_SKIN.tan, hair:0x1d1410, hairStyle:'puffs', top:0xd8573f, sleeves:'short', bottom:0x2f4a7a, legs:'shorts', socks:0xf4f0e6, shoes:0x3b6ea8 }, [-1.0, -1.35], 38);
    /* One headset: the teen hands it over lenses first, he puts it on, takes it off and hands it back */
    S.carry(waxHeadset(), HS_GRIPS, [
      WCK(0, 0, WC.chest(teen, [0, -0.13, 0.3], [0, 180, 0])),
      WCK(1.55, 0.75, WC.chest(man, [0, -0.08, 0.31])),
      WCK(2.75, 0.7, WC.head(man)),
      WCK(10.35, 0.7, WC.chest(man, [0, -0.08, 0.31])),
      WCK(11.8, 0.75, WC.chest(teen, [0, -0.13, 0.3], [0, 180, 0]))
    ], [
      WCH(teen, 'L', 'Bm', 0, 1.9), WCH(teen, 'R', 'Am', 0, 1.9),
      WCH(man, 'L', 'A', 1.8, 3.45), WCH(man, 'R', 'B', 1.8, 3.45),
      WCH(man, 'L', 'A', 10.35, 12.15), WCH(man, 'R', 'B', 10.35, 12.15),
      WCH(teen, 'L', 'Bm', 12.05, 99), WCH(teen, 'R', 'Am', 12.05, 99)
    ]);
    S.keys(man, [WK(0, { p:'ease', head:[0, 0, -30] }), WK(1.4, { armR:[44, 10, -20], elR:42, head:[6, 0, -34] }), WK(2.05, { armR:[34, 12, -40], elR:96, armL:[30, 12, -40], elL:90, head:[10, 0, -10] }),
      WK(2.8, { p:'faceHands' }), WK(3.3, { p:'faceHands' }), WK(4.2, { p:'ease', head:[-12, 0, 26] }), WK(5.6, { p:'reach' }), WK(7.0, { ry:48, head:[-14, 0, 20], armL:[46, 34, 0], elL:30, armR:[64, 12, 0], elR:18 }),
      WK(8.4, { ry:30, armL:[76, 36, 0], armR:[76, 36, 0], elL:24, elR:24, head:[-16, 0, 0], talk:1 }), WK(9.6, { ry:15, p:'ease', talk:0 }), WK(10.5, { p:'faceHands' }), WK(11.0, { p:'faceHands' }),
      WK(11.7, { armR:[34, 12, -40], elR:96, armL:[30, 12, -40], elL:90, talk:1, head:[0, 0, -36] }), WK(12.4, { armR:[56, 12, -20], elR:30, head:[0, 0, -40], talk:0 }), WK(12.5, { armR:[56, 12, -20], elR:30, head:[0, 0, -40] }), WK(14, { p:'ease', head:[0, 0, -30] })]);
    S.keys(teen, [WK(0, { p:'offer', head:[6, 0, 0], talk:1 }), WK(1.5, { p:'offer', armR:[64, 10, -24], elR:22, talk:0 }), WK(2.05, { p:'offer', armR:[64, 10, -24], elR:22 }), WK(2.7, { at:[1.45, -1.6], p:'spot', ry:-62 }),
      WK(5.0, { p:'spot', head:[-10, 0, 0], talk:1 }), WK(6.4, { p:'present', ry:-80, talk:0 }), WK(8.0, { p:'spot', ry:-62, head:[-6, 0, 0] }), WK(11.6, { p:'spot', ry:-58 }), WK(12.2, { at:[1.3, -1.75], armR:[64, 10, -24], elR:22, ry:-55 }), WK(12.5, { p:'offer', ry:-55 }), WK(14, { p:'offer', head:[6, 0, 0], talk:1 })]);
    S.keys(kid, [WK(0, { p:'ease', head:[-6, 0, 20] }), WK(3.4, { p:'ease', head:[-12, 0, 10], dy:-0.02 }), ...waxClaps(4.6, 6.8, { head:[-16, 0, 6] }), WK(7.0, { p:'point', head:[-24, 0, 0], ry:20 }),
      WK(8.8, { p:'faceHands', armL:[100, 30, -40], armR:[100, 30, -40], head:[-14, 0, 0], ry:30 }), WK(10.6, { p:'ease', head:[-8, 0, 16], ry:38 }), WK(12.4, { armL:[150, 20, 0], armR:[150, 20, 0], elL:20, elR:20, head:[-20, 0, 16] }), WK(13.4, { p:'ease', head:[-6, 0, 20] })]);
    S.tick((t) => WP.swim(fish, t, 4.3, 10.3, 0.22, 1.72, -2.0, 0.66));
  } },
/* ---------------------------------------------------------------- 2 */
{ id:'wax-2017a', n:2, year:'2017', title:'VR Goes Statewide', backdrop:'calmap', floor:'boards', loop:15,
  lines:[[0, 'VR stations ship to libraries across California.'], [5, 'More than 90 libraries join, from the north coast to the border.'], [10.5, 'The Marin pilot becomes a statewide project.']],
  item:{ title:'VR Goes Statewide', date:'2017', where:'More than 90 California libraries', partners:'California State Library, Oculus, Califa', src:['lj2017', 'lj2019', 'vive2018', 'about'],
    desc:'In June 2017 the California State Library, Oculus and the library consortium Califa partnered to bring VR-ready PCs with Rift headsets to more than 90 libraries across California, building on the Marin County pilot. XRLibraries, launched in 2016 as the project’s coordinator, also became a clearinghouse where libraries share what works with VR and AR.',
    more:'XRLibraries’ website counts more than 200 VR systems installed in California public libraries, and calls it the largest VR installation in public libraries.' },
  build(S){
    const m = waxM();
    /* Lights on the map come on one library at a time */
    const dots = [], dm = new THREE.MeshBasicMaterial({ color:0xffd27a, toneMapped:false });
    const r = rnd(2017), k = 3.55 / 640, cy = 3.55 * 0.52;
    const inCA = (px, py) => { let c = false; const P = WAX_CA; for (let i = 0, j = P.length - 1; i < P.length; j = i++){ if ((P[i][1] > py) !== (P[j][1] > py) && px < (P[j][0] - P[i][0]) * (py - P[i][1]) / (P[j][1] - P[i][1]) + P[i][0]) c = !c; } return c; };
    const dg = new THREE.SphereGeometry(0.018, 8, 6);
    while (dots.length < 92){ const px = -214 + r() * 420, py = -255 + r() * 520; if (!inCA(px, py)) continue; const d = new THREE.Mesh(dg, dm); d.position.set(px * k, cy - py * k, -3.86); d.visible = false; S.anim.add(d); dots.push({ d, at:1.2 + dots.length * 0.1 + r() * 0.3 }); }
    dots.sort((a, b) => a.d.position.y - b.d.position.y);
    WP.crate(S, -1.9, -2.9, 0.1, 'SACRAMENTO'); WP.crate(S, -1.85, -2.9, 0.1, '', 0.68, 0.46, 0.5).position.y = 0.5;
    WP.crate(S, 2.2, -2.6, -0.3, 'EUREKA');
    /* An open shipping crate: walls, packing foam, a hinged lid and a headset inside */
    const cr = S.grp(-0.9, 0, -2.2, 0);
    S.box(0.72, 0.03, 0.52, m.pale, 0, 0.015, 0, 0, cr);
    for (const sz of [-1, 1]) S.box(0.72, 0.5, 0.025, m.pale, 0, 0.25, sz * 0.2475, 0, cr);
    for (const sx of [-1, 1]) S.box(0.025, 0.5, 0.47, m.pale, sx * 0.3475, 0.25, 0, 0, cr);
    S.box(0.67, 0.26, 0.47, stdMat(0x4f555c, 0.95), 0, 0.16, 0, 0, cr);
    for (const sz of [-1, 1]) S.box(0.74, 0.03, 0.03, m.wood, 0, 0.49, sz * 0.26, 0, cr);
    for (const sx of [-1, 1]) S.box(0.03, 0.03, 0.5, m.wood, sx * 0.36, 0.49, 0, 0, cr);
    S.box(0.2, 0.36, 0.36, m.black, -1.62, 0.18, -2.62);
    const lid = S.live3(0, 0, 0), lt = new THREE.Mesh(new THREE.BoxGeometry(0.74, 0.04, 0.54), m.wood); lt.position.set(0, 0.02, 0.27); lid.add(lt);
    const tech = S.fig({ av:'ma12', body:'man', skin:WAX_SKIN.brown, hair:0x16100c, hairStyle:'crop', top:0x31506e, bottom:0x3a3530, cap:0x1d3b52, beard:'stubble', shoes:0x4a3a2a }, [-0.82, -1.58], 180);
    const lib = S.fig({ av:'bf03', body:'woman', skin:WAX_SKIN.light, hair:0xb07a3e, hairStyle:'bob', top:0xc04a3a, jacket:0x2f3a48, bottom:0x2a2d36, glasses:true }, [1.1, -1.6], -35);
    const mover = S.fig({ av:'ma06', body:'man', skin:WAX_SKIN.olive, hair:0x2a1d14, hairStyle:'short', top:0xd9a441, bottom:0x2b3445 }, [2.0, -1.2], -90);
    /* The lid swings up on its hinge; his fingers lift its front edge */
    const LID = { L:{ p:[-0.2, -0.004, 0.5], into:[0, 1, 0], fingers:[0, 0, -1], curl:0.45 }, R:{ p:[0.2, -0.004, 0.5], into:[0, 1, 0], fingers:[0, 0, -1], curl:0.45 } };
    S.carry(lid, LID, [WCK(0, 0, WC.at(-0.9, 0.5, -2.46)), WCK(0.6, 0.85, WC.at(-0.9, 0.5, -2.46, [-108, 0, 0])), WCK(12.75, 0.85, WC.at(-0.9, 0.5, -2.46))],
      [WCH(tech, 'L', 'L', 0.55, 1.1), WCH(tech, 'R', 'R', 0.55, 1.1), WCH(tech, 'L', 'L', 12.7, 13.55), WCH(tech, 'R', 'R', 12.7, 13.55)]);
    /* He lifts the headset out, shows it, points at the map with his free hand, and packs it again */
    S.carry(waxHeadset(), HS_GRIPS, [WCK(0, 0, WC.at(-0.9, 0.345, -2.2)), WCK(2.0, 0.6, WC.chest(tech, [0, -0.1, 0.3], [0, 180, 0])), WCK(11.85, 0.6, WC.at(-0.9, 0.345, -2.2))],
      [WCH(tech, 'L', 'Bm', 1.85, 12.5), WCH(tech, 'R', 'Am', 1.85, 7.55), WCH(tech, 'R', 'Am', 9.85, 12.5)]);
    const bend = { spine:[34, 0, 0], chest:[10, 0, 0], legL:[16, 4, 0], legR:[16, 4, 0], knL:28, knR:28, dy:-0.06, head:[12, 0, 0] };
    const bendIn = Object.assign({}, bend, { spine:[42, 0, 0], head:[18, 0, 0] });
    S.keys(tech, [WK(0, { p:'ease', ry:180 }), WK(0.5, Object.assign({}, bend)), WK(1.05, Object.assign({}, bend, { spine:[24, 0, 0] })), WK(1.5, { p:'ease', spine:[6, 0, 0], head:[-4, 0, 0] }),
      WK(1.95, Object.assign({}, bendIn)), WK(2.65, { p:'ease', head:[14, 0, 0] }), WK(3.6, { p:'ease', at:[-0.62, -1.42], ry:30, talk:1 }), WK(5.2, { p:'ease', ry:30, talk:0, head:[6, 0, 0] }),
      WK(6.6, { p:'ease', ry:10, head:[-10, 0, -20] }), WK(8.0, { p:'point', ry:-30, armR:[96, 20, 0], elR:6, head:[-18, 0, 0] }), WK(10.0, { p:'ease', ry:-10 }),
      WK(11.3, { p:'ease', at:[-0.82, -1.58], ry:180 }), WK(11.95, Object.assign({}, bendIn)), WK(12.7, Object.assign({}, bend, { spine:[30, 0, 0], head:[-10, 0, 0] })),
      WK(13.5, Object.assign({}, bend)), WK(14.3, { p:'ease' }), WK(15, { p:'ease' })]);
    /* The librarian checks the shipment off on her clipboard */
    const clip = S.live3(0, 0, 0); S.box(0.22, 0.3, 0.012, m.cardboard, 0, 0, 0, 0, clip); S.box(0.2, 0.26, 0.004, m.white, 0, -0.01, 0.008, 0, clip); S.box(0.08, 0.025, 0.02, m.steel, 0, 0.14, 0.01, 0, clip);
    S.carry(clip, CLIP_GRIPS, [WCK(0, 0, WC.chest(lib, [0.02, -0.13, 0.31], [-50, 0, 0]))], [WCH(lib, 'L', 'L', 0, 99), WCH(lib, 'R', 'R', 0, 5.0), WCH(lib, 'R', 'R', 9.1, 99)]);
    S.keys(lib, [WK(0, { p:'ease', head:[24, 0, 0] }), WK(2.0, { p:'ease', head:[26, 0, 6] }), WK(3.6, { p:'ease', ry:-60, head:[0, 0, 10], talk:1 }),
      WK(5.4, { p:'ease', ry:-30, armR:[100, 30, 10], elR:4, head:[-26, 0, 30], talk:0, pointR:1 }), WK(8.6, { p:'ease', ry:-10, armR:[100, 30, 10], elR:4, head:[-30, 0, 40], pointR:1 }), WK(10.6, { p:'ease', ry:-35, head:[24, 0, 0] }),
      WK(12.6, { p:'ease', ry:-20, head:[-8, 0, 20], talk:1 }), WK(13.9, { p:'ease', ry:-30, head:[10, 0, 10], talk:0 }), WK(15, { p:'ease', head:[24, 0, 0] })]);
    /* The mover sets a box down at the back, reads its label and takes it back to the Eureka pile */
    S.box(0.5, 0.36, 0.42, m.cardboard, 1.62, 0.18, -1.2);
    S.box(0.5, 0.36, 0.42, m.cardboard, -0.1, 0.18, -3.1);
    const box2 = S.live3(0, 0, 0); S.box(0.5, 0.36, 0.42, m.cardboard, 0, 0, 0, 0, box2);
    S.carry(box2, BOX_GRIPS, [WCK(0, 0, WC.at(1.62, 0.54, -1.2, [0, -90, 0])), WCK(0.35, 0.55, WC.chest(mover, [0, -0.26, 0.34]), 0.03), WCK(5.35, 0.55, WC.at(-0.1, 0.54, -3.1, [0, 180, 0])),
      WCK(11.05, 0.6, WC.chest(mover, [0, -0.26, 0.34]), 0.03), WCK(14.35, 0.55, WC.at(1.62, 0.54, -1.2, [0, -90, 0]))],
      [WCH(mover, 'L', 'L', 0, 6.0), WCH(mover, 'R', 'R', 0, 6.0), WCH(mover, 'L', 'L', 10.75, 99), WCH(mover, 'R', 'R', 10.75, 99)]);
    const lift = { spine:[30, 0, 0], chest:[8, 0, 0], legL:[30, 6, 0], legR:[30, 6, 0], knL:44, knR:44, dy:-0.12, head:[12, 0, 0] };
    S.keys(mover, [WK(0, Object.assign({ ry:-90 }, lift)), WK(0.9, { p:'carry', ry:-90 }), WK(4.6, { p:'carry', at:[-0.1, -2.72] }), WK(5.1, { p:'carry', at:[-0.1, -2.72], ry:180 }),
      WK(5.8, Object.assign({ at:[-0.1, -2.72], ry:180 }, lift)), WK(6.6, { p:'ease', at:[-0.1, -2.72], ry:180 }), WK(7.6, { p:'ease', at:[0.2, -2.55], ry:120, head:[-20, 0, -40] }),
      WK(9.6, { p:'hipHands', at:[0.2, -2.55], ry:150, head:[-22, 0, -30] }), WK(10.4, { p:'ease', at:[-0.1, -2.72], ry:180, head:[10, 0, 0] }), WK(11.1, Object.assign({ at:[-0.1, -2.72], ry:180 }, lift)),
      WK(11.9, { p:'carry', at:[-0.1, -2.72], ry:180 }), WK(14.0, { p:'carry', at:[2.0, -1.2], ry:-90 }), WK(15, Object.assign({ at:[2.0, -1.2], ry:-90 }, lift))]);
    S.tick((t) => { for (const d of dots) d.d.visible = t >= d.at && t < 14.4; });
  } },
/* ---------------------------------------------------------------- 3 */
{ id:'wax-2017b', n:3, year:'2017', title:'Story Time in 3D', backdrop:'storyroom', floor:'rug', loop:14,
  lines:[[0, 'Story time moves into virtual reality.'], [3, 'The youngest visitors hear stories inside 3D worlds.'], [10.6, 'Teens, meanwhile, head straight for the VR games.']],
  item:{ title:'Story Time in 3D', date:'2017', where:'California libraries', partners:'Libraries in the California Virtual Reality Experience', src:['lj2017', 'cenic'],
    desc:'Library Journal reported in 2017 that young children loved virtual reality story times, while teens gravitated to VR games. In Marin, children listened to stories inside three-dimensional worlds.' },
  build(S){
    const m = waxM();
    WP.chair(S, 0, -2.7, 0, 0.46, m.yellow);
    /* A big picture book with a whale that swims out of its pages */
    const book = S.live3(0, 0, 0);
    const coverL = new THREE.Group(), coverR = new THREE.Group(); book.add(coverL, coverR);
    const pc = mk(256, 256), px = pc.getContext('2d'); px.fillStyle = '#f7f1e3'; px.fillRect(0, 0, 256, 256); px.fillStyle = '#3b6ea8'; px.beginPath(); px.ellipse(128, 150, 90, 40, 0, 0, Math.PI * 2); px.fill(); px.fillStyle = '#2a4d78'; px.font = '700 30px ' + F.display; px.textAlign = 'center'; px.fillText('The Big Blue', 128, 60);
    const pageM = new THREE.MeshStandardMaterial({ map:tex(pc), roughness:0.85 }), coverM = stdMat(0x2a9d8f, 0.6);
    const hl = new THREE.Mesh(new THREE.BoxGeometry(0.26, 0.34, 0.012), [coverM, coverM, coverM, coverM, pageM, coverM]); hl.position.x = -0.13; coverL.add(hl);
    const hr = new THREE.Mesh(new THREE.BoxGeometry(0.26, 0.34, 0.012), [coverM, coverM, coverM, coverM, pageM, coverM]); hr.position.x = 0.13; coverR.add(hr);
    const reader = S.fig({ av:'fp02', body:'woman', skin:WAX_SKIN.deep, hair:0x120c0a, hairStyle:'puffs', top:0xf2c14e, bottom:0x3a2a5a, legs:'skirt', hem:0.8, eyes:0x2a1a10 }, [0, -2.62], 0);
    /* She holds the book open toward the children, a hand behind each cover */
    const BOOK = { L:{ p:[0.232, -0.1, -0.009], into:[0, 0, 1], fingers:[0.25, 1, 0], curl:0.32 }, R:{ p:[-0.232, -0.1, -0.009], into:[0, 0, 1], fingers:[-0.25, 1, 0], curl:0.32 } };
    S.carry(book, BOOK, [WCK(0, 0, WC.chest(reader, [0, -0.17, 0.34], [4, 0, 0]))], [WCH(reader, 'L', 'L', 0, 99, 0.3, { node:coverR }), WCH(reader, 'R', 'R', 0, 99, 0.3, { node:coverL })]);
    const k1 = S.fig({ av:'mc01', scale:0.88, body:'kid', skin:WAX_SKIN.light, hair:0xc98a4a, hairStyle:'short', top:0x3b6ea8, sleeves:'short', bottom:0x4a3a2a, legs:'shorts', socks:0xffffff }, [-0.85, -1.25], 25);
    const k2 = S.fig({ av:'fc02', scale:0.88, body:'kid', skin:WAX_SKIN.medium, hair:0x1a120c, hairStyle:'braids', top:0xe76f51, bottom:0x2a9d8f, legs:'skirt', hem:0.55 }, [0.55, -1.15], -20);
    const teen = S.fig({ av:'ma16', scale:0.92, body:'boy', skin:WAX_SKIN.fair, hair:0x2a1d14, hairStyle:'short', top:0x2b2f38, bottom:0x3a4a6a, eyes:0x4a6a3a }, [2.1, -2.4], -40);
    S.carry(waxHeadset(), HS_GRIPS, [WCK(0, 0, WC.head(teen))]);
    const whale = S.live3(0, 1.4, -2.0);
    const wb = new THREE.Mesh(new THREE.SphereGeometry(0.3, 18, 12), new THREE.MeshStandardMaterial({ color:0x3b6ea8, roughness:0.4, emissive:0x1d3b6a, emissiveIntensity:0.6 })); wb.scale.set(1.6, 0.7, 0.75); whale.add(wb);
    const wbel = new THREE.Mesh(new THREE.SphereGeometry(0.29, 16, 10), stdMat(0xe9e2d0, 0.6)); wbel.scale.set(1.5, 0.5, 0.65); wbel.position.y = -0.06; whale.add(wbel);
    const tail = new THREE.Mesh(new THREE.ConeGeometry(0.16, 0.36, 4), wb.material); tail.rotation.z = Math.PI / 2; tail.position.x = -0.62; tail.scale.set(1, 1, 0.25); whale.add(tail);
    for (const s of [-1, 1]){ const e = new THREE.Mesh(new THREE.SphereGeometry(0.03, 8, 6), stdMat(0x111111, 0.2)); e.position.set(0.32, 0.03, s * 0.18); whale.add(e); }
    const stars = []; for (let i = 0; i < 14; i++){ const st = new THREE.Mesh(new THREE.OctahedronGeometry(0.035), new THREE.MeshBasicMaterial({ color:0xffe7a0, toneMapped:false })); st.visible = false; S.anim.add(st); stars.push(st); }
    const readKeys = (t, ex) => WK(t, Object.assign({ p:'sit', armL:[40, 24, -46], armR:[40, 24, -46], elL:84, elR:84, handL:[-10, 0, 40], handR:[-10, 0, 40], head:[22, 0, 0] }, ex));
    S.keys(reader, [readKeys(0), readKeys(1.4, { talk:1 }), readKeys(2.4, { head:[0, 0, 0], talk:1 }), readKeys(4.0, { head:[-20, 0, -20], talk:1 }), readKeys(6.4, { head:[-24, 0, 20], talk:0 }), readKeys(8.4, { head:[-10, 0, 0], talk:1 }), readKeys(10.6, { head:[22, 0, 0], talk:1 }), readKeys(12.4, { talk:0 }), readKeys(14)]);
    const sitK = (t, ex) => WK(t, Object.assign({ p:'sitFloor', head:[-8, 0, 0] }, ex));
    S.keys(k1, [sitK(0), sitK(2.6, { head:[-30, 0, 10] }), sitK(4.4, { head:[-36, 0, -20], armR:[120, 30, 0], elR:20 }), sitK(6.0, { head:[-30, 0, 30], armR:[30, 14, -30], elR:60 }), ...waxClaps(8.0, 9.4, { p:'sitFloor', head:[-20, 0, 0] }), sitK(9.6, { head:[-26, 0, 20] }), sitK(12.6, { head:[-6, 0, 0] }), ...waxClaps(12.8, 13.8, { p:'sitFloor' }), sitK(14)]);
    S.keys(k2, [sitK(0, { head:[-8, 0, 10] }), sitK(2.8, { head:[-34, 0, 0] }), sitK(4.0, { head:[-30, 0, -30], armL:[140, 30, 0], armR:[140, 30, 0], elL:10, elR:10 }), sitK(6.2, { head:[-36, 0, 20], armL:[30, 14, -30], armR:[30, 14, -30] }), sitK(9.0, { head:[-20, 0, 0], p:'sitFloor' }), ...waxClaps(12.8, 13.8, { p:'sitFloor' }), sitK(14, { head:[-8, 0, 10] })]);
    S.keys(teen, [WK(0, { p:'play', ry:-40 }), WK(2.4, { p:'play', ry:-70, head:[4, 0, 20] }), WK(4.6, { p:'play', ry:-20, armR:[70, 20, -10], elR:30 }), WK(6.8, { p:'play', ry:-50, dy:-0.08, legL:[20, 6, 0], knL:30 }), WK(9.0, { p:'play', ry:-30 }), WK(11.2, { p:'cheer', ry:-40 }), WK(12.4, { p:'play', ry:-40 }), WK(14, { p:'play', ry:-40 })]);
    S.tick((t) => {
      const open = clamp(Math.min((t - 1.0) / 0.8, (12.6 - t) / 0.8), 0, 1), oe = open * open * (3 - 2 * open);
      coverL.rotation.y = -0.9 * (1 - oe); coverR.rotation.y = 0.9 * (1 - oe);
      const out = clamp(Math.min((t - 2.2) / 1.2, (11.4 - t) / 1.2), 0, 1), a = (t - 2.2) * 0.62;
      whale.visible = out > 0.01;
      whale.position.set(Math.sin(a) * 1.25 * out, 0.95 + 0.9 * out + 0.12 * Math.sin(t * 1.3), -2.0 + Math.cos(a) * 0.55 * out);
      whale.rotation.set(0, Math.atan2(Math.sin(a) * 0.55, Math.cos(a) * 1.25), 0.1 * Math.sin(t * 2)); whale.scale.setScalar(0.25 + 0.75 * out);
      tail.rotation.y = 0.4 * Math.sin(t * 4);
      stars.forEach((s, i) => { s.visible = out > 0.05; const b = i / stars.length * Math.PI * 2; s.position.set(Math.cos(b + t * 0.2) * (0.9 + (i % 3) * 0.35), 1.9 + 0.5 * Math.sin(i * 1.7 + t * 0.6), -2.1 + Math.sin(b + t * 0.2) * 0.6); s.rotation.y = t * 2 + i; s.scale.setScalar(out * (0.6 + 0.4 * Math.sin(t * 3 + i))); });
    });
  } },
/* ---------------------------------------------------------------- 4 */
{ id:'wax-2018a', n:4, year:'2018', title:'Nevada Opens Its Stations', backdrop:'reopening', floor:'tile', loop:14,
  lines:[[0, 'Carson City Library reopens with VR and AR stations.'], [2.6, 'Nevada’s pilot puts 22 headsets in 11 libraries.'], [6.6, 'A visitor floats among planets and stars.']],
  item:{ title:'Nevada Opens Its Stations', date:'2018', where:'Carson City Library and other Nevada libraries', partners:'Nevada State Library, XRLibraries', src:['working', 'carson2018'],
    desc:'Nevada’s state library set aside $22,000 of a 2017 budget increase for a VR pilot: 22 headsets loaded with STEM content in 11 libraries, modeled on Marin County’s program. In February 2018 the Carson City Library’s grand re-opening featured VR and AR stations, and XRLibraries’ founder presented in a webinar for librarians across the state.' },
  build(S){
    const m = waxM();
    /* A ribbon across two posts, cut with big scissors; the bow stays on the end that falls */
    S.cyl(0.03, 0.04, 1.0, m.brass, -2.25, 0.5, -1.3); S.cyl(0.03, 0.04, 1.0, m.brass, 0.35, 0.5, -1.3);
    const rib = (len) => { const g = new THREE.Mesh(new THREE.BoxGeometry(len, 0.08, 0.008), stdMat(0xc0392b, 0.45)); g.geometry.translate(len / 2, 0, 0); return g; };
    const rl = rib(1.3), rr = rib(1.3); rl.position.set(-2.25, 0.95, -1.3); rr.position.set(0.35, 0.95, -1.3); rr.rotation.y = Math.PI; S.anim.add(rl, rr);
    const bow = new THREE.Mesh(new THREE.SphereGeometry(0.08, 16, 12), stdMat(0xc0392b, 0.45)); bow.position.set(1.3, 0, 0.02); bow.scale.set(1.4, 0.8, 0.5); rl.add(bow);
    const conf = []; const cg = new THREE.PlaneGeometry(0.035, 0.022);
    for (let i = 0; i < 40; i++){ const c = new THREE.Mesh(cg, new THREE.MeshBasicMaterial({ color:[0xe63946, 0xf2c14e, 0x2a9d8f, 0x3b6ea8, 0xf4a261][i % 5], side:THREE.DoubleSide, toneMapped:false })); c.visible = false; S.anim.add(c); conf.push({ c, v:[(Math.random() - 0.5) * 1.6, 1.6 + Math.random() * 1.6, (Math.random() - 0.5) * 1.2] }); }
    const dir = S.fig({ av:'fa15', body:'woman', skin:WAX_SKIN.fair, hair:0x8a6a4a, hairStyle:'long', top:0x9a2f33, jacket:0x2b2f38, bottom:0x2b2f38, legs:'skirt', hem:0.5, tights:0x2a2228 }, [-0.95, -1.8], 0);
    const staff = S.fig({ av:'bm05', body:'man', skin:WAX_SKIN.medium, hair:0x1a120c, hairStyle:'short', top:0xe9e2d0, jacket:0x31506e, bottom:0x2a2d36, glasses:true }, [-2.1, -2.0], 30);
    const visitor = S.fig({ av:'fa09', body:'woman', skin:WAX_SKIN.light, hair:0xd8d2c8, hairStyle:'bob', top:0x8a5a9a, bottom:0x3a3a42, legs:'skirt', hem:0.75, glasses:true }, [1.5, -2.2], -20);
    const sc = S.live3(0, 0, 0); for (const s of [-1, 1]){ const blade = new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.2, 0.006), m.steel); blade.position.set(s * 0.012, 0.1, 0); blade.rotation.z = s * 0.15; sc.add(blade); const ring = new THREE.Mesh(new THREE.TorusGeometry(0.03, 0.008, 6, 12), stdMat(0xf2c14e, 0.5)); ring.position.set(s * 0.03, -0.02, 0); sc.add(ring); }
    /* Her fingers go through the scissor rings; she reaches out, cuts at the bow and brings them back */
    const SCG = { R:{ p:[-0.042, -0.034, 0.0], into:[1, 0, 0], fingers:[0, 0, 1], curl:0.74 } };
    S.carry(sc, SCG, [WCK(0, 0, WC.chest(dir, [-0.12, -0.34, 0.2], [80, 0, 0])), WCK(1.3, 0.6, WC.at(-0.95, 0.95, -1.43, [90, 0, 0])), WCK(2.25, 0.55, WC.chest(dir, [-0.12, -0.34, 0.2], [80, 0, 0]))], [WCH(dir, 'R', 'R', 0, 99)]);
    S.keys(dir, [WK(0, { p:'ease', armL:[10, 8, 0], head:[6, 0, 0], talk:1 }), WK(1.3, { p:'ease', head:[10, 0, 0], talk:0 }), WK(1.9, { p:'ease', spine:[6, 0, 0], head:[16, 0, 0] }),
      WK(2.6, { armL:[150, 20, 0], elL:20, head:[-10, 0, 0], gripL:0.9 }), WK(3.4, { armL:[126, 34, 0], elL:36, head:[-6, 0, 0], gripL:-0.6 }), WK(4.2, { armL:[148, 22, 0], elL:22, gripL:-0.6 }), WK(5.0, { armL:[126, 34, 0], elL:36, gripL:-0.6 }),
      WK(5.8, { p:'ease', ry:30, head:[0, 0, 30] }), WK(9.0, { ry:40, armL:[52, 18, -30], elL:42, handL:[0, 0, 70], gripL:-0.7, head:[4, 0, 8], talk:1 }), WK(11.0, { p:'ease', ry:20, talk:0 }), WK(13.2, { p:'ease', ry:0 }), WK(14, { p:'ease', armL:[10, 8, 0], head:[6, 0, 0], talk:1 })]);
    S.keys(staff, [WK(0, { p:'ease', head:[0, 0, -30] }), WK(2.4, { p:'ease', head:[-6, 0, -20] }), ...waxClaps(2.7, 5.2, { head:[-6, 0, -10] }), WK(5.6, { p:'think', ry:10, head:[6, 0, 10] }), WK(9.6, { p:'ease', ry:30, head:[0, 0, -20] }), WK(14, { p:'ease', head:[0, 0, -30] })]);
    /* She lifts the headset off at the end, smiles, and puts it back on */
    S.carry(waxHeadset(), HS_GRIPS, [WCK(0, 0, WC.head(visitor)), WCK(11.75, 0.65, WC.chest(visitor, [0, -0.02, 0.3])), WCK(13.15, 0.65, WC.head(visitor))],
      [WCH(visitor, 'L', 'A', 11.75, 13.8), WCH(visitor, 'R', 'B', 11.75, 13.8)]);
    S.keys(visitor, [WK(0, { p:'ease', head:[0, 0, -20] }), WK(3.0, { p:'ease', head:[-10, 0, 0] }), WK(4.6, { p:'float' }), WK(6.6, { p:'float', ry:20, head:[-26, 0, 20] }), WK(8.6, { p:'float', ry:-40, head:[-30, 0, -20], armL:[30, 80, 0], armR:[30, 80, 0] }),
      WK(10.6, { p:'float', ry:-20, talk:1 }), WK(11.5, { p:'ease', ry:-20, talk:0 }), WK(12.5, { p:'ease', ry:-20, head:[8, 0, -10], talk:1 }), WK(13.3, { p:'ease', ry:-20, talk:0 }), WK(14, { p:'ease', head:[0, 0, -20] })]);
    /* What the visitor sees: a ringed planet and drifting stars */
    const planet = S.live3(1.5, 2.3, -2.4), pm = new THREE.Mesh(new THREE.SphereGeometry(0.22, 20, 14), new THREE.MeshStandardMaterial({ color:0xd9a35a, emissive:0x6a3a10, emissiveIntensity:0.5, roughness:0.6 })); planet.add(pm);
    const ringP = new THREE.Mesh(new THREE.RingGeometry(0.3, 0.42, 40), new THREE.MeshBasicMaterial({ color:0xf2dca0, side:THREE.DoubleSide, transparent:true, opacity:0.7, toneMapped:false })); ringP.rotation.x = 1.2; planet.add(ringP);
    const spk = []; for (let i = 0; i < 18; i++){ const s = new THREE.Mesh(new THREE.OctahedronGeometry(0.025), new THREE.MeshBasicMaterial({ color:0xdde8ff, toneMapped:false })); S.anim.add(s); spk.push(s); }
    S.tick((t) => {
      /* The cut ends sag down; after the ceremony the ribbon is drawn back up */
      const sag = t < 2.0 ? 0 : t < 13.4 ? Math.min(1, (t - 2.0) / 0.5) : Math.max(0, 1 - (t - 13.4) / 0.6), se = sag * sag * (3 - 2 * sag);
      rl.rotation.z = -1.25 * se; rr.rotation.z = -1.25 * se;
      conf.forEach((q, i) => { const tt = t - 2.0; q.c.visible = tt > 0 && tt < 3.2; if (!q.c.visible) return; q.c.position.set(-0.95 + q.v[0] * tt, 1.0 + q.v[1] * tt - 2.2 * tt * tt * 0.5 + 0.0, -1.3 + q.v[2] * tt); if (q.c.position.y < 0.01) q.c.position.y = 0.01; q.c.rotation.set(tt * 5 + i, tt * 3, i); });
      const on = clamp(Math.min((t - 4.4) / 0.8, (11.8 - t) / 0.8), 0, 1);
      planet.visible = on > 0.01; planet.scale.setScalar(on); planet.rotation.y = t * 0.5; planet.position.y = 2.3 + 0.08 * Math.sin(t);
      spk.forEach((s, i) => { s.visible = on > 0.01; const a = i * 2.4 + t * 0.15; s.position.set(1.5 + Math.cos(a) * (0.6 + (i % 4) * 0.25), 1.2 + ((i * 0.37 + t * 0.12) % 1.6), -2.2 + Math.sin(a) * 0.5); s.scale.setScalar(on * (0.7 + 0.3 * Math.sin(t * 4 + i))); });
    });
  } },
/* ---------------------------------------------------------------- 5 */
{ id:'wax-2019a', n:5, year:'By 2019', title:'VR on the Road', backdrop:'shelter', floor:'gym', loop:15,
  lines:[[0, 'Marin’s VR program goes out into the community.'], [3.4, 'People displaced by deadly wildfires get a break.'], [9.4, 'Schools, senior centers and the county fair get visits too.']],
  item:{ title:'VR on the Road', date:'By 2019', where:'Marin County, California', partners:'Marin County Free Library', src:['cenic'],
    desc:'Marin’s VR program went out into the community: to schools, senior centers, the county fair, and people displaced by deadly wildfires.',
    quote:'It gave wildfire evacuees a few moments of being able to forget their own reality and have a good time.', quoteBy:'Sara Jones, director of the Marin County Free Library, speaking to CENIC in 2019' },
  build(S){
    const m = waxM();
    const cot = (x, z, ry, col) => { const g = S.grp(x, 0, z, ry); S.box(0.72, 0.05, 1.9, stdMat(0x3f5a3a, 0.8), 0, 0.4, 0, 0, g); for (const sx of [-1, 1]) for (const sz of [-1, 1]) S.box(0.04, 0.4, 0.04, m.steel, sx * 0.32, 0.2, sz * 0.88, 0, g); S.box(0.7, 0.06, 0.9, stdMat(col, 0.95), 0, 0.455, 0.42, 0, g); S.box(0.5, 0.1, 0.3, m.white, 0, 0.47, -0.72, 0, g); return g; };
    cot(-0.3, -2.4, Math.PI / 2, 0x7a3a3a); cot(1.9, -3.0, Math.PI / 2, 0x3a4f7a);
    S.box(0.5, 0.34, 0.3, stdMat(0x2b3a4a, 0.8), 2.4, 0.17, -1.9, 0.4);
    /* The VR kit: an open padded case on a folding table, the headset resting on its foam */
    WP.desk(S, -1.75, -1.6, 0.8, 0.55, 0.66, 0.3, m.steel);
    const kit = S.grp(-1.75, 0.66, -1.6, 0.3);
    S.box(0.6, 0.02, 0.42, m.black, 0, 0.01, 0, 0, kit);
    for (const sz of [-1, 1]) S.box(0.6, 0.22, 0.02, m.black, 0, 0.11, sz * 0.2, 0, kit);
    for (const sx of [-1, 1]) S.box(0.02, 0.22, 0.4, m.black, sx * 0.29, 0.11, 0, 0, kit);
    S.box(0.56, 0.08, 0.38, stdMat(0x5a5a5a, 0.95), 0, 0.06, 0, 0, kit);
    const lidG = S.grp(0, 0.22, -0.21, 0, kit); lidG.rotation.x = -1.9; S.box(0.6, 0.03, 0.42, m.black, 0, 0.015, 0.21, 0, lidG);
    const grandpa = S.fig({ av:'ma14', body:'elder', skin:WAX_SKIN.medium, hair:0xd8d2c8, hairStyle:'balding', top:0x5a6a7a, bottom:0x3a3530, glasses:true, beard:'stubble', shoes:0x3a2a1a }, [-0.4, -2.2], 0);
    const kid = S.fig({ av:'mc01', scale:0.88, dye:[215, 48, 28, 1.0, 1.35], body:'kid', skin:WAX_SKIN.medium, hair:0x1a120c, hairStyle:'short', top:0xf2c14e, sleeves:'short', bottom:0x2f4a7a, legs:'shorts', socks:0xffffff }, [0.3, -2.25], -10);
    const lib = S.fig({ av:'ma18', body:'man', skin:WAX_SKIN.deep, hair:0x0e0b09, hairStyle:'crop', top:0x2a9d8f, jacket:0x3a3f46, bottom:0x2b2f38, lanyard:0xcda961, beard:'full' }, [-1.95, -1.15], 156);
    /* The librarian takes the headset from the case and hands it to the grandfather, who puts it on;
       at the end it comes back and goes into the case again */
    S.carry(waxHeadset(), HS_GRIPS, [WCK(0, 0, WC.at(-1.75, 0.815, -1.6, [0, 17, 0])), WCK(0.75, 0.6, WC.chest(lib, [0, -0.1, 0.3], [0, 180, 0])),
      WCK(3.0, 0.7, WC.chest(grandpa, [0, -0.06, 0.3])), WCK(4.1, 0.6, WC.head(grandpa)), WCK(11.8, 0.6, WC.chest(grandpa, [0, -0.06, 0.3])),
      WCK(13.0, 0.7, WC.chest(lib, [0, -0.1, 0.3], [0, 180, 0])), WCK(14.45, 0.45, WC.at(-1.75, 0.815, -1.6, [0, 17, 0]))],
      [WCH(lib, 'L', 'Bm', 0.55, 3.35), WCH(lib, 'R', 'Am', 0.55, 3.35), WCH(grandpa, 'L', 'A', 3.2, 4.75), WCH(grandpa, 'R', 'B', 3.2, 4.75),
        WCH(grandpa, 'L', 'A', 11.8, 13.35), WCH(grandpa, 'R', 'B', 11.8, 13.35), WCH(lib, 'L', 'Bm', 13.25, 14.95), WCH(lib, 'R', 'Am', 13.25, 14.95)]);
    const sitG = (t, ex) => WK(t, Object.assign({ p:'sit', dy:-0.47, ry:0 }, ex));
    S.keys(grandpa, [sitG(0, { head:[10, 0, -20], armL:[20, 10, -30], elL:60, armR:[20, 10, -30], elR:60 }), sitG(2.6, { head:[0, 0, -40], armR:[50, 10, -20], elR:40 }), sitG(3.4, { armR:[34, 12, -40], elR:96, armL:[30, 12, -40], elL:90, head:[10, 0, -10] }),
      sitG(4.3, { p:'faceHands', dy:-0.47, legL:[86, 6, 0], legR:[86, 6, 0], knL:88, knR:88 }), sitG(5.4, { head:[-10, 0, 20] }),
      sitG(6.8, { head:[-20, 0, -30], armL:[50, 30, 0], elL:30 }), sitG(8.2, { head:[-14, 0, 10], armL:[70, 40, 0], armR:[70, 40, 0], elL:30, elR:30, talk:1 }), sitG(9.6, { head:[-6, 0, 0], talk:1 }), sitG(11.0, { talk:0 }),
      sitG(11.9, { p:'faceHands', dy:-0.47, legL:[86, 6, 0], legR:[86, 6, 0], knL:88, knR:88 }), sitG(12.6, { armR:[34, 12, -40], elR:96, armL:[30, 12, -40], elL:90, head:[0, 0, -30], talk:1 }), sitG(13.4, { armR:[50, 10, -20], elR:40, head:[0, 0, -40], talk:0 }), sitG(15, { head:[10, 0, -20], armL:[20, 10, -30], elL:60, armR:[20, 10, -30], elR:60 })]);
    S.keys(kid, [WK(0, { p:'sit', dy:-0.31, head:[10, 0, 30] }), WK(3.0, { p:'sit', dy:-0.31, head:[0, 0, 30] }), WK(5.6, { p:'sit', dy:-0.31, head:[-6, 0, 40], armL:[70, 10, -10], elL:40 }), ...waxClaps(8.2, 9.8, { p:'sit', dy:-0.31, head:[-10, 0, 30] }),
      WK(10.2, { p:'sit', dy:-0.31, armR:[60, 40, -40], elR:60, head:[0, 0, 40], spine:[0, -10, 0] }), WK(13.0, { p:'sit', dy:-0.31, head:[0, 0, 30] }), WK(15, { p:'sit', dy:-0.31, head:[10, 0, 30] })]);
    const bendK = { spine:[26, 0, 0], chest:[8, 0, 0], legL:[10, 4, 0], legR:[10, 4, 0], knL:16, knR:16, dy:-0.03, head:[16, 0, 0] };
    S.keys(lib, [WK(0, Object.assign({}, bendK)), WK(0.9, Object.assign({}, bendK, { spine:[14, 0, 0] })), WK(1.5, { p:'ease', head:[6, 0, 0] }),
      WK(2.5, { p:'ease', at:[-1.2, -1.72], ry:118, talk:1 }), WK(3.4, { p:'ease', ry:118, talk:0 }), WK(4.3, { p:'kneel', ry:100 }), WK(8.0, { p:'kneel', ry:100, head:[-10, 0, 0], talk:1 }),
      WK(9.4, { p:'kneel', ry:100, talk:0 }), WK(12.2, { p:'ease', ry:118 }), WK(13.5, { p:'ease', ry:118, talk:1 }), WK(14.3, { p:'ease', at:[-1.95, -1.15], ry:156, talk:0 }),
      WK(14.8, Object.assign({ at:[-1.95, -1.15], ry:156 }, bendK)), WK(15, Object.assign({ at:[-1.95, -1.15], ry:156 }, bendK))]);
    /* A calm meadow with birds, around the headset */
    const birds = []; for (let i = 0; i < 5; i++){ const b = new THREE.Group(); for (const s of [-1, 1]){ const w = new THREE.Mesh(new THREE.PlaneGeometry(0.12, 0.04), new THREE.MeshBasicMaterial({ color:0xf4f0e6, side:THREE.DoubleSide, toneMapped:false })); w.geometry.translate(0.06, 0, 0); w.scale.x = s; b.add(w); b.userData[s] = w; } b.visible = false; S.anim.add(b); birds.push(b); }
    S.tick((t) => {
      const on = clamp(Math.min((t - 4.8) / 0.8, (11.9 - t) / 0.8), 0, 1);
      birds.forEach((b, i) => { b.visible = on > 0.01; const a = t * 0.8 + i * 1.25; b.position.set(-0.4 + Math.cos(a) * 0.75, 1.65 + 0.15 * Math.sin(t * 1.3 + i), -2.2 + Math.sin(a) * 0.5); b.rotation.y = -a; b.scale.setScalar(on); const f = Math.sin(t * 9 + i) * 0.6; b.userData[1].rotation.z = f; b.userData[-1].rotation.z = -f; });
    });
  } },
/* ---------------------------------------------------------------- 6 */
{ id:'wax-2019b', n:6, year:'2019', title:'VR in the World’s Catalog', backdrop:'catalog', floor:'office', loop:14,
  lines:[[0, 'Librarians catalog VR so any library can find it.'], [4, 'Record by record, VR titles go into WorldCat.'], [9.8, 'More than 1,000 interactive 3D objects get cataloged.']],
  item:{ title:'VR in the World’s Catalog', date:'2019', where:'Carson City, Nevada', partners:'Nevada State Library, XRLibraries, Lifeliqe', src:['lj2019', 'goed2023', 'vive2018'],
    desc:'Nevada’s state library and its partner XRLibraries set out to catalog VR content so any library could find it. In 2019 Nevada librarians led a first-of-its-kind effort to catalog virtual reality in WorldCat, the world’s largest library catalog, and planned a cataloging hack-a-thon in Marin, California and Carson City, Nevada.',
    more:'Nevada’s Governor’s Office of Economic Development says a Carson City librarian cataloged the first VR course companion in WorldCat, and that the work produced a collection of more than 1,000 3D interactive VR objects.' },
  build(S){
    const m = waxM();
    const tbl = WP.desk(S, -0.6, -1.7, 2.0, 0.8, 0.74, 0, m.pale);
    /* Two laptops on the table, turned toward the chairs; hands type on their keyboards */
    const lap = (x, ry) => { const g = S.live3(-0.6 + x, 0.74, -1.75, ry); S.box(0.34, 0.016, 0.24, m.steel, 0, 0.008, 0.02, 0, g); S.box(0.3, 0.003, 0.11, m.black, 0, 0.0175, 0.045, 0, g); const sc = S.grp(0, 0.016, -0.1, 0, g); sc.rotation.x = -0.25; S.box(0.34, 0.22, 0.01, m.steel, 0, 0.11, 0, 0, sc); S.plane(0.31, 0.19, waxScreenMat('marc'), 0, 0.11, 0.006, 0, 0, sc); return g; };
    const lapA = lap(-0.5, Math.PI - 0.15), lapB = lap(0.5, Math.PI + 0.15);
    WP.chair(S, -1.1, -2.42, 0, 0.45); WP.chair(S, -0.1, -2.42, 0, 0.45);
    /* A wooden card catalog, and the world it now feeds */
    const cab = S.grp(-2.3, 0, -3.3, 0.3); S.box(0.9, 1.3, 0.5, m.wood, 0, 0.65, 0, 0, cab);
    for (let i = 0; i < 3; i++) for (let j = 0; j < 4; j++){ S.box(0.26, 0.26, 0.02, stdMat(0x8a5a32, 0.6), -0.29 + i * 0.29, 0.25 + j * 0.29, 0.26, 0, cab); S.box(0.06, 0.02, 0.03, m.brass, -0.29 + i * 0.29, 0.25 + j * 0.29, 0.28, 0, cab); }
    const globe = S.live3(1.85, 1.62, -2.6);
    const gg = WP.wire(S, new THREE.SphereGeometry(0.42, 18, 12), globe);
    S.cyl(0.05, 0.12, 1.2, m.brass, 1.85, 0.6, -2.6);
    const cards = []; for (let i = 0; i < 10; i++){ const c = new THREE.Mesh(new THREE.PlaneGeometry(0.1, 0.065), new THREE.MeshBasicMaterial({ color:0xfff4dc, side:THREE.DoubleSide, toneMapped:false })); c.visible = false; S.anim.add(c); cards.push(c); }
    const cnt = mk(256, 96), cctx = cnt.getContext('2d'), cntTex = keepCanvas(cnt), counter = new THREE.Mesh(new THREE.PlaneGeometry(0.66, 0.25), new THREE.MeshBasicMaterial({ map:tex(cntTex), toneMapped:false, transparent:true }));
    counter.position.set(1.85, 2.35, -2.55); S.anim.add(counter); let lastN = -1;
    const drawCount = (n) => { cctx.clearRect(0, 0, 256, 96); cctx.fillStyle = 'rgba(10,30,40,0.7)'; cctx.fillRect(0, 0, 256, 96); cctx.fillStyle = '#9df0ff'; cctx.textAlign = 'center'; cctx.font = '700 46px ' + F.ui; cctx.fillText(n.toLocaleString('en-US') + (n >= 1000 ? '+' : ''), 128, 52); cctx.font = '700 17px ' + F.type; cctx.fillText('VR OBJECTS CATALOGED', 128, 82); counter.material.map.needsUpdate = true; };
    const cat1 = S.fig({ av:'fa07', body:'woman', skin:WAX_SKIN.light, hair:0x6a4a2e, hairStyle:'bun', top:0xe2d6bf, jacket:0x6b3a4a, bottom:0x2b2f38, glasses:0x6b4a2a }, [-1.1, -2.4], 0);
    const cat2 = S.fig({ av:'ma04', body:'man', skin:WAX_SKIN.tan, hair:0x1a120c, hairStyle:'curly', top:0x3b6ea8, bottom:0x3a3530, beard:'stubble' }, [-0.1, -2.4], 0);
    const cat3 = S.fig({ av:'fa06', body:'woman', skin:WAX_SKIN.brown, hair:0x120c0a, scarf:0x2f6b5a, top:0x5a4a7a, bottom:0x2a2a30, legs:'skirt', hem:0.95, dress:true }, [1.05, -1.55], -30);
    const KEYS = { L:TYPE_GRIP(-0.075, 0.052, 0.085), R:TYPE_GRIP(0.075, 0.052, 0.085) };
    S.carry(lapA, KEYS, [WCK(0, 0, WC.at(-1.1, 0.74, -1.75, [0, 171.4, 0]))], [WCH(cat1, 'L', 'L', 0, 4.2, 0.35, { off:waxTyping(0) }), WCH(cat1, 'R', 'R', 0, 4.2, 0.35, { off:waxTyping(1.7) }),
      WCH(cat1, 'L', 'L', 5.8, 10.4, 0.35, { off:waxTyping(0.6) }), WCH(cat1, 'R', 'R', 5.8, 10.4, 0.35, { off:waxTyping(2.3) }), WCH(cat1, 'L', 'L', 13.2, 99, 0.35, { off:waxTyping(1.1) }), WCH(cat1, 'R', 'R', 13.2, 99, 0.35, { off:waxTyping(2.9) })]);
    S.carry(lapB, KEYS, [WCK(0, 0, WC.at(-0.1, 0.74, -1.75, [0, 188.6, 0]))], [WCH(cat2, 'L', 'L', 5.6, 10.4, 0.35, { off:waxTyping(0.3) }), WCH(cat2, 'R', 'R', 5.6, 10.4, 0.35, { off:waxTyping(2.0) })]);
    /* He looks the headset over, sets it on the table to type, and picks it up again */
    S.carry(waxHeadset(), HS_GRIPS, [WCK(0, 0, WC.chest(cat2, [0, -0.12, 0.32], [20, 0, 0])), WCK(4.75, 0.55, WC.at(0.32, 0.794, -1.6, [0, -20, 0])), WCK(12.85, 0.5, WC.chest(cat2, [0, -0.12, 0.32], [20, 0, 0]))],
      [WCH(cat2, 'L', 'A', 0, 5.35), WCH(cat2, 'R', 'B', 0, 5.35), WCH(cat2, 'L', 'A', 12.7, 99), WCH(cat2, 'R', 'B', 12.7, 99)]);
    const seat = (t, ex) => WK(t, Object.assign({ p:'sit', dy:-0.43 }, ex));
    const typeA = { armL:[46, 6, -20], armR:[46, 6, -20], elL:58, elR:58, handL:[-16, 0, 80], handR:[-16, 0, 80], head:[18, 0, 0] };
    S.keys(cat1, [seat(0, Object.assign({}, typeA)), seat(4.4, Object.assign({}, typeA, { head:[-6, 0, 30], talk:1 })), seat(5.6, Object.assign({}, typeA, { talk:0 })), seat(6.0, Object.assign({}, typeA)), seat(10.8, { armL:[150, 20, 0], armR:[150, 20, 0], elL:20, elR:20, head:[-12, 0, 0] }), seat(12.0, { armR:[80, 40, 0], elR:20, head:[0, 0, -30] }), seat(13.2, Object.assign({}, typeA)), seat(14, Object.assign({}, typeA))]);
    S.keys(cat2, [seat(0, { armR:[50, 10, -30], elR:80, head:[20, 0, 0] }), seat(1.6, { armR:[60, 14, -50], elR:90, armL:[40, 10, -40], elL:80, head:[26, 0, 0], talk:1 }), seat(3.6, { armR:[40, 10, -30], elR:90, head:[0, 0, 30], talk:1 }),
      seat(5.0, Object.assign({}, typeA, { head:[10, 0, 10] })), seat(5.8, Object.assign({}, typeA)), seat(10.8, { armL:[150, 20, 0], armR:[150, 20, 0], elL:20, elR:20, head:[-12, 0, 0] }), seat(12.0, { armL:[80, 40, 0], elL:20, head:[0, 0, 30] }), seat(13.2, { armR:[50, 10, -30], elR:80, head:[20, 0, 0] }), seat(14, { armR:[50, 10, -30], elR:80, head:[20, 0, 0] })]);
    S.keys(cat3, [WK(0, { p:'think', ry:-40 }), WK(2.4, { p:'point', ry:-10, armR:[110, 20, 0], elR:4, head:[-24, 0, 10], talk:1 }), WK(5.0, { p:'present', ry:-60, talk:1 }), WK(7.0, { p:'ease', ry:-20, head:[-20, 0, 20] }), ...waxClaps(10.6, 12.2, { ry:-50 }), WK(12.6, { p:'think', ry:-40 }), WK(14, { p:'think', ry:-40 })]);
    S.tick((t) => {
      globe.rotation.y = t * 0.4; gg.scale.setScalar(1 + 0.04 * Math.sin(t * 3));
      const n = t < 1.5 ? 0 : Math.min(1000, Math.round(Math.pow((t - 1.5) / 8.5, 1.4) * 1000)); if (n !== lastN && t < 13.6){ lastN = n; drawCount(n); }
      cards.forEach((c, i) => {
        const tt = (t - 1.6 - i * 0.85); c.visible = tt > 0 && tt < 1.4 && t < 11;
        if (!c.visible) return;
        const from = i % 2 ? [-0.1, 0.95, -1.75] : [-1.1, 0.95, -1.75], to = [1.85, 1.62, -2.6], k = tt / 1.4;
        c.position.set(from[0] + (to[0] - from[0]) * k, from[1] + (to[1] - from[1]) * k + Math.sin(k * Math.PI) * 0.7, from[2] + (to[2] - from[2]) * k); c.rotation.set(k * 4, k * 6, 0); c.scale.setScalar(1 - k * 0.6);
      });
    });
    drawCount(0);
  } },
/* ---------------------------------------------------------------- 7 */
{ id:'wax-2019c', n:7, year:'2019', title:'XR Marin and the XR Stars', backdrop:'farm', floor:'grass', loop:15,
  lines:[[0, 'XR Marin teams libraries with schools.'], [4, 'Teen “XR Stars” help patrons with the gear.'], [9, 'A camper borrows the cameras to film her family’s farm.']],
  item:{ title:'XR Marin and the XR Stars', date:'2019', where:'Marin County, California', partners:'Marin County Free Library, XRLibraries, Novato Unified School District, Marin County Office of Education', src:['cenic'],
    desc:'XR Marin brought together the Marin County Free Library, XRLibraries, Novato Unified School District and the Marin County Office of Education. Teens served as “XR Stars,” helping patrons use the equipment. Its programs let people make 3D models, design 3D games and produce 360-degree video tours, and one teen at a VR summer camp borrowed the cameras and filmed her family’s farm.' },
  build(S){
    const m = waxM();
    const hay = (x, z, ry) => { const g = S.grp(x, 0, z, ry); S.box(0.9, 0.42, 0.45, m.hay, 0, 0.21, 0, 0, g); for (const sx of [-0.25, 0.25]) S.box(0.02, 0.43, 0.46, stdMat(0x8a6a3a, 0.9), sx, 0.21, 0, 0, g); return g; };
    hay(2.1, -3.2, 0.2); hay(2.15, -3.2, 0.1).position.y = 0.42; hay(-2.3, -1.6, -0.4);
    for (let i = 0; i < 4; i++) S.box(0.08, 0.9, 0.08, m.wood, -2.6 + i * 0.9, 0.45, -3.55);
    S.box(3.0, 0.08, 0.05, m.wood, -1.25, 0.7, -3.52); S.box(3.0, 0.08, 0.05, m.wood, -1.25, 0.35, -3.52);
    /* A 360 camera on a tripod, recording */
    const tri = S.grp(-0.6, 0, -2.0); for (let k = 0; k < 3; k++){ const a = k / 3 * Math.PI * 2, l = S.box(0.025, 1.3, 0.025, m.black, Math.cos(a) * 0.22, 0.63, Math.sin(a) * 0.22, 0, tri); l.rotation.set(Math.sin(a) * 0.17, 0, -Math.cos(a) * 0.17); }
    S.box(0.05, 0.2, 0.05, m.black, 0, 1.36, 0, 0, tri);
    const cam360 = S.grp(0, 1.5, 0, 0, tri); S.box(0.045, 0.13, 0.03, m.black, 0, 0, 0, 0, cam360); for (const s of [-1, 1]) S.sph(0.022, stdMat(0x111820, 0.1, 0.4), 0, 0.03, s * 0.018, 1, 1, 0.6, cam360);
    const rec = new THREE.Mesh(new THREE.SphereGeometry(0.008, 8, 6), new THREE.MeshBasicMaterial({ color:0xff3030, toneMapped:false })); rec.position.set(0, -0.03, 0.017); cam360.add(rec); S.anim.attach(rec);
    /* A 3D printer making a little barn */
    const pr = S.grp(1.1, 0, -3.1, -0.3); S.box(0.6, 0.6, 0.5, stdMat(0xd8dde2, 0.5), 0, 0.3, 0, 0, pr); S.box(0.5, 0.06, 0.4, m.black, 0, 0.6, 0, 0, pr);
    const head3 = S.live3(1.1, 1.06, -3.1); S.box(0.08, 0.06, 0.08, m.orange, 0, 0, 0, 0, head3);
    const barn = S.live3(1.1, 0.64, -3.1); S.box(0.16, 0.12, 0.12, stdMat(0x9b2f2a, 0.6), 0, 0.06, 0, 0, barn); const roof = new THREE.Mesh(new THREE.ConeGeometry(0.12, 0.08, 4), stdMat(0x5a3a2a, 0.6)); roof.position.y = 0.16; roof.rotation.y = Math.PI / 4; barn.add(roof);
    const star = S.fig({ av:'fa03', scale:0.93, body:'girl', skin:WAX_SKIN.olive, hair:0x2a1d14, hairStyle:'long', top:0xf2c14e, sleeves:'short', bottom:0x3a4a6a, lanyard:0x1d3b52, shoes:0xe9e5dc }, [-0.1, -1.55], -60);
    const boy = S.fig({ av:'ma17', scale:0.92, body:'boy', skin:WAX_SKIN.brown, hair:0x0e0b09, hairStyle:'crop', top:0x2a9d8f, bottom:0x2b3445 }, [1.45, -2.4], -150);
    const kid = S.fig({ av:'fc01', scale:0.88, body:'kid', skin:WAX_SKIN.light, hair:0xd8a85a, hairStyle:'ponytail', top:0xc77dff, sleeves:'short', bottom:0x3a4a6a, legs:'shorts', socks:0xffffff }, [-1.6, -2.3], 30);
    S.carry(waxHeadset(), HS_GRIPS, [WCK(0, 0, WC.head(kid))]);
    /* An open laptop balanced on his left forearm while his right hand types and points */
    const laptop = S.live3(0, 0, 0); S.box(0.3, 0.015, 0.22, m.steel, 0, 0, 0, 0, laptop); S.box(0.27, 0.003, 0.1, m.black, 0, 0.009, 0.035, 0, laptop);
    const ls = S.grp(0, 0.008, -0.11, 0, laptop); ls.rotation.x = -0.32; S.box(0.3, 0.2, 0.01, m.steel, 0, 0.1, 0, 0, ls); S.plane(0.27, 0.17, waxScreenMat('farm360'), 0, 0.1, 0.006, 0, 0, ls);
    const LAP = { L:{ p:[-0.06, -0.012, -0.01], into:[0, 1, 0], fingers:[0.35, 0, -1], curl:0.12, out:0.3 }, R:TYPE_GRIP(0.07, 0.045, 0.075) };
    S.carry(laptop, LAP, [WCK(0, 0, WC.chest(boy, [0.06, -0.31, 0.29], [0, 180, 0]))],
      [WCH(boy, 'L', 'L', 0, 99), WCH(boy, 'R', 'R', 0, 5.6, 0.35, { off:waxTyping(0) }), WCH(boy, 'R', 'R', 8.6, 11.8, 0.35, { off:waxTyping(1) }), WCH(boy, 'R', 'R', 12.4, 99, 0.35, { off:waxTyping(2) })]);
    S.keys(star, [WK(0, { p:'crouch', ry:-60, armR:[90, 10, 0], elR:30, head:[-6, 0, 0] }), WK(1.6, { p:'crouch', ry:-60, armR:[100, 10, 0], elR:20, head:[-10, 0, 0] }), WK(2.4, { p:'ease', ry:-40, armR:[80, 10, 0], elR:20 }),
      WK(3.6, { at:[0.6, -1.25], p:'ease', ry:20 }), WK(5.0, { at:[0.6, -1.25], p:'present', ry:-40, talk:1 }), WK(7.0, { at:[0.6, -1.25], p:'wave', ry:-10, talk:0 }), ...waxWaves(7.3, 8.6, { at:[0.6, -1.25], ry:-10 }), WK(9.0, { at:[0.6, -1.25], p:'hipHands', ry:-40 }),
      WK(12.6, { at:[-0.1, -1.55], p:'ease', ry:-60 }), WK(14.2, { p:'crouch', ry:-60, armR:[90, 10, 0], elR:30 }), WK(15, { p:'crouch', ry:-60, armR:[90, 10, 0], elR:30, head:[-6, 0, 0] })]);
    S.keys(boy, [WK(0, { p:'ease', head:[26, 0, 0] }), WK(4.0, { p:'ease', head:[24, 0, -4] }),
      WK(6.0, { p:'ease', armR:[90, 20, 0], elR:10, head:[-10, 0, 30], talk:1, pointR:1 }), WK(8.4, { p:'ease', head:[24, 0, 0], talk:0 }), WK(12.0, { p:'ease', ry:-120, head:[10, 0, 0] }), WK(15, { p:'ease', head:[26, 0, 0] })]);
    S.keys(kid, [WK(0, { p:'ease', ry:30 }), WK(2.2, { p:'ease', ry:60, head:[-10, 0, 10] }), WK(4.0, { p:'point', ry:0, armR:[60, 10, 0], head:[20, 0, 0] }), WK(6.0, { p:'crouch', ry:-20, armR:[70, 10, 0], elR:10 }),
      WK(8.0, { p:'ease', ry:-60, head:[-6, 0, 0], talk:1 }), WK(10.0, { p:'cheer', ry:-30 }), WK(11.4, { p:'ease', ry:10 }), WK(15, { p:'ease', ry:30 })]);
    /* Little chickens, part of the farm the camper filmed */
    const hens = []; for (let i = 0; i < 3; i++){ const h = new THREE.Group(); const b = new THREE.Mesh(new THREE.SphereGeometry(0.09, 10, 8), stdMat(i === 1 ? 0x8a5a2a : 0xf2ede2, 0.8)); b.scale.set(1, 0.85, 1.25); h.add(b); const hd = new THREE.Mesh(new THREE.SphereGeometry(0.05, 8, 6), b.material); hd.position.set(0, 0.09, 0.09); h.add(hd); const cm = new THREE.Mesh(new THREE.BoxGeometry(0.015, 0.03, 0.04), stdMat(0xc0392b, 0.6)); cm.position.set(0, 0.145, 0.09); h.add(cm); const bk = new THREE.Mesh(new THREE.ConeGeometry(0.012, 0.035, 4), stdMat(0xe2a63c, 0.6)); bk.rotation.x = Math.PI / 2; bk.position.set(0, 0.085, 0.145); h.add(bk); S.anim.add(h); hens.push({ h, hd }); }
    S.tick((t) => {
      rec.visible = t > 1.8 && t < 13 && Math.sin(t * 6) > 0;
      const k = clamp((t - 1) / 11, 0, 1); barn.scale.set(1, Math.max(0.02, k), 1); barn.position.y = 0.64; head3.position.set(1.1 + 0.07 * Math.sin(t * 7), 0.72 + 0.16 * k, -3.1 + 0.05 * Math.cos(t * 9)); if (t >= 13.8) barn.scale.y = Math.max(0.02, 1 - (t - 13.8) / 0.8);
      hens.forEach((q, i) => { const a = t * 0.4 + i * 2.1; q.h.position.set(-1.6 + Math.cos(a) * (0.55 + i * 0.12), 0, -2.3 + Math.sin(a) * 0.45 + 0.2); q.h.rotation.y = -a; q.hd.position.y = 0.09 - 0.05 * Math.max(0, Math.sin(t * 5 + i * 2)); });
    });
  } },
/* ---------------------------------------------------------------- 8 */
{ id:'wax-2020', n:8, year:'2020', title:'Project SANDI', backdrop:'careers', floor:'concrete', loop:15,
  lines:[[0, 'Project SANDI brings VR job training to Nevada.'], [4, 'Trainees practice real tasks, like a dialysis technician’s.'], [9.6, 'It grows to more than 1,000 headsets at over 80 locations.']],
  item:{ title:'Project SANDI', date:'2020', where:'Nevada', partners:'Nevada Governor’s Office of Workforce Innovation, Governor’s Office of Economic Development, Nevada libraries and colleges', src:['goed2023', 'working', 'arborPod', 'about'],
    desc:'In October 2020 Nevada won a $13.8 million federal grant for Project SANDI (Supporting and Advancing Nevada’s Dislocated Individuals), which uses VR to explore careers in skilled trades, healthcare, IT, advanced manufacturing and logistics. It grew to more than 1,000 headsets at over 80 locations. XRLibraries’ executive director is a partner in the project.' },
  build(S){
    const m = waxM();
    WP.mat(S, -1.0, -2.0, 0.8); WP.mat(S, 1.3, -2.1, 0.8);
    /* Holograms: a dialysis machine and a valve to repair */
    const mach = S.live3(-1.0, 0, -2.85);
    WP.wire(S, new THREE.BoxGeometry(0.5, 1.2, 0.4), mach).position.y = 0.6;
    const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.36, 0.24), new THREE.MeshBasicMaterial({ map:waxScreenMat('career').map, toneMapped:false, transparent:true, opacity:0.9 })); scr.position.set(0, 1.0, 0.21); mach.add(scr);
    const tube = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([new THREE.Vector3(0.2, 0.8, 0.2), new THREE.Vector3(0.5, 1.0, 0.6), new THREE.Vector3(0.2, 1.3, 0.9)]), 20, 0.012, 6), waxM().holo); mach.add(tube);
    const check = mk(128, 128), cx = check.getContext('2d'); cx.strokeStyle = '#7dffb0'; cx.lineWidth = 16; cx.beginPath(); cx.moveTo(24, 66); cx.lineTo(54, 96); cx.lineTo(106, 32); cx.stroke();
    const ok = new THREE.Mesh(new THREE.PlaneGeometry(0.3, 0.3), new THREE.MeshBasicMaterial({ map:tex(check), transparent:true, toneMapped:false })); ok.position.set(0, 1.55, 0.2); mach.add(ok);
    const valve = S.live3(1.3, 1.0, -2.75);
    WP.wire(S, new THREE.CylinderGeometry(0.06, 0.06, 1.2, 12), valve).rotation.z = Math.PI / 2;
    const wheel = WP.wire(S, new THREE.TorusGeometry(0.16, 0.025, 6, 18), valve); wheel.position.set(0, 0.2, 0.05);
    const icons = []; const iconCols = [0xe07b2a, 0xc0392b, 0x2a9d8f, 0x3b6ea8, 0x6a4a8a];
    for (let i = 0; i < 5; i++){ const ic = new THREE.Mesh(i % 2 ? new THREE.OctahedronGeometry(0.09) : new THREE.TorusGeometry(0.07, 0.025, 8, 16), new THREE.MeshBasicMaterial({ color:iconCols[i], toneMapped:false, transparent:true, opacity:0.9 })); S.anim.add(ic); icons.push(ic); }
    const nurse = S.fig({ av:'mf01', body:'woman', skin:WAX_SKIN.tan, hair:0x1a120c, hairStyle:'bun', top:0x3a8a9a, bottom:0x3a8a9a, eyes:0x2a1a10 }, [-1.0, -2.0], 0);
    const coach = S.fig({ av:'mm03', body:'man', skin:WAX_SKIN.fair, hair:0x9a9088, hairStyle:'short', top:0x1d3b52, bottom:0x6b6252, glasses:true, beard:'full' }, [0.2, -1.2], -30);
    const tech = S.fig({ av:'mm04', body:'man', skin:WAX_SKIN.deep, hair:0x0e0b09, hairStyle:'crop', top:0xd8792c, jacket:0x3a3f46, bottom:0x2b3445, shoes:0x4a3a2a }, [1.3, -2.1], 0);
    S.carry(waxHeadset(), HS_GRIPS, [WCK(0, 0, WC.head(nurse))]); S.carry(waxHeadset(), HS_GRIPS, [WCK(0, 0, WC.head(tech))]);
    /* The coach holds his tablet in his left hand and taps through the lesson with his right */
    const tab = S.live3(0, 0, 0); S.box(0.24, 0.17, 0.012, m.black, 0, 0, 0, 0, tab); S.plane(0.21, 0.14, waxScreenMat('career'), 0, 0, -0.007, Math.PI, 0, tab);
    S.carry(tab, TAB_GRIPS, [WCK(0, 0, WC.chest(coach, [0.03, -0.12, 0.3], [40, 0, 0]))],
      [WCH(coach, 'L', 'L', 0, 99), WCH(coach, 'R', 'R', 0, 4.4), WCH(coach, 'R', 'tap', 0.5, 4.1, 0.3, { off:waxTaps([0.9, 1.6, 2.3, 3.1, 3.7]) }), WCH(coach, 'R', 'R', 12.4, 99), WCH(coach, 'R', 'tap', 13.4, 14.6, 0.25, { off:waxTaps([13.8, 14.3]) })]);
    S.keys(nurse, [WK(0, { p:'ease' }), WK(1.6, { armR:[70, 10, -10], elR:40, head:[10, 0, 0] }), WK(2.4, { armR:[66, 10, -10], elR:50, handR:[-30, 0, 0], head:[14, 0, 0] }), WK(3.4, { armR:[70, 20, -30], elR:60, armL:[60, 10, -30], elL:60, head:[14, 0, 10] }),
      WK(5.0, { armR:[60, 30, -30], elR:70, armL:[66, 10, -40], elL:50, head:[4, 0, 20] }), WK(6.6, { armR:[80, 10, -10], elR:30, head:[0, 0, 0] }), WK(8.0, { armR:[74, 10, -10], elR:46, handR:[-30, 0, 0] }), WK(9.6, { p:'ease', head:[-6, 0, 0], talk:1 }), WK(11.0, { p:'cheer', talk:0 }), WK(12.4, { p:'ease' }), WK(15, { p:'ease' })]);
    S.keys(coach, [WK(0, { p:'ease', head:[24, 0, 0] }), WK(3.0, { p:'ease', head:[24, 0, -4] }), WK(4.6, { p:'ease', ry:-60, head:[-4, 0, 10], talk:1 }),
      WK(6.6, { p:'ease', ry:-60, armR:[60, 10, 0], elR:20, gripR:-0.6, talk:1 }), WK(8.4, { p:'ease', ry:20, head:[0, 0, 0], talk:0 }), WK(10.6, { p:'ease', ry:-30, armR:[90, 30, 30], elR:100, handR:[0, 0, 0] }), WK(12.6, { p:'ease', head:[24, 0, 0] }), WK(15, { p:'ease', head:[24, 0, 0] })]);
    const wr = { armR:[70, 14, -20], elR:40, armL:[60, 14, -20], elL:50, head:[8, 0, 0] };
    const turning = []; for (let t = 1.4, i = 0; t < 9; t += 0.6, i++) turning.push(WK(t, Object.assign({}, wr, { handR:[0, 0, i % 2 ? 60 : -30], handL:[0, 0, i % 2 ? -30 : 60], gripL:0.6, gripR:0.6 })));
    S.keys(tech, [WK(0, { p:'ease' }), ...turning, WK(9.6, { p:'ease', head:[-4, 0, -20] }), WK(11.0, { armR:[90, 30, 30], elR:100 }), WK(12.6, { p:'ease' }), WK(15, { p:'ease' })]);
    S.tick((t) => {
      const on = clamp(Math.min((t - 0.8) / 0.6, (13.6 - t) / 0.6), 0, 1);
      mach.visible = on > 0.01; mach.scale.setScalar(Math.max(0.01, on)); ok.visible = t > 10.4 && t < 13.4;
      valve.visible = on > 0.01; valve.scale.setScalar(Math.max(0.01, on)); wheel.rotation.z = t < 9 ? t * 2.2 : 9 * 2.2;
      icons.forEach((ic, i) => { const a = t * 0.5 + i / 5 * Math.PI * 2; ic.position.set(0.15 + Math.cos(a) * 1.9, 2.75 + 0.12 * Math.sin(t * 1.5 + i), -2.3 + Math.sin(a) * 0.5); ic.rotation.set(t, t * 1.3, 0); ic.visible = t > 9.4 && t < 14.2; ic.scale.setScalar(clamp(Math.min(t - 9.4, 14.2 - t) * 2, 0, 1)); });
    });
  } },
/* ---------------------------------------------------------------- 9 */
{ id:'wax-2022a', n:9, year:'2022', title:'360° Stories in Washington', backdrop:'forest360', floor:'meeting', loop:15,
  lines:[[0, 'XRLibraries trains Washington librarians in 360° video.'], [4.6, 'Six libraries film 360° stories about their communities.'], [9.6, 'Put on a headset and you are standing in the story.']],
  item:{ title:'360° Stories in Washington', date:'2022', where:'Washington State', partners:'Washington State Library, IMLS', src:['wsl'],
    desc:'XRLibraries was the trainer for the Washington State Library’s VR 360 grant program. In 2022 it helped six libraries create 360-degree virtual reality stories about topics important to their communities. The program was open to public, tribal and academic libraries and funded by IMLS through the Library Services and Technology Act.' },
  build(S){
    const m = waxM();
    const tri = S.grp(-0.2, 0, -2.2); for (let k = 0; k < 3; k++){ const a = k / 3 * Math.PI * 2, l = S.box(0.025, 1.3, 0.025, m.black, Math.cos(a) * 0.22, 0.63, Math.sin(a) * 0.22, 0, tri); l.rotation.set(Math.sin(a) * 0.17, 0, -Math.cos(a) * 0.17); }
    S.box(0.05, 0.2, 0.05, m.black, 0, 1.36, 0, 0, tri); const c360 = S.grp(0, 1.5, 0, 0, tri); S.box(0.045, 0.13, 0.03, m.black, 0, 0, 0, 0, c360); for (const s of [-1, 1]) S.sph(0.022, stdMat(0x111820, 0.1, 0.4), 0, 0.03, s * 0.018, 1, 1, 0.6, c360);
    /* The 360 view, an inside-out globe of the forest */
    const pano = new THREE.Mesh(new THREE.SphereGeometry(0.55, 32, 18), new THREE.MeshBasicMaterial({ map:tex(waxScreen('panorama', 1024, 512)), side:THREE.DoubleSide, transparent:true, opacity:0.85, toneMapped:false }));
    const panoG = S.live3(-0.2, 2.45, -2.3); panoG.add(pano);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.6, 0.008, 6, 48), waxM().holo); ring.rotation.x = Math.PI / 2; panoG.add(ring);
    S.box(1.6, 1.0, 0.04, m.black, 2.0, 1.8, -3.6); S.plane(1.5, 0.9, waxScreenMat('panorama'), 2.0, 1.8, -3.575);
    const trainer = S.fig({ av:'ma07', body:'man', skin:WAX_SKIN.medium, hair:0x2a1d14, hairStyle:'short', top:0xe9e2d0, jacket:0x5a3a2a, bottom:0x2b2f38, glasses:true }, [0.75, -2.0], -50);
    const lib1 = S.fig({ av:'fa05', body:'woman', skin:WAX_SKIN.fair, hair:0xc98a4a, hairStyle:'long', top:0x2f6b5a, bottom:0x3a3f46 }, [-1.3, -1.6], 40);
    const lib2 = S.fig({ av:'gm01', body:'elder', skin:WAX_SKIN.brown, hair:0xc9c4bc, hairStyle:'crop', top:0x6a4a8a, bottom:0x3a3530, beard:'full' }, [-2.1, -2.6], 30);
    S.carry(waxHeadset(), HS_GRIPS, [WCK(0, 0, WC.head(lib2))]);
    /* She films with her phone: held low to check the shot, raised in front of her face to record */
    const ph = S.live3(0, 0, 0); S.box(0.075, 0.15, 0.01, m.black, 0, 0, 0, 0, ph); S.plane(0.065, 0.13, waxScreenMat('panorama'), 0, 0, 0.006, 0, 0, ph);
    S.carry(ph, PHONE_GRIPS, [WCK(0, 0, WC.chest(lib1, [-0.06, -0.17, 0.3], [50, 180, 0])), WCK(2.0, 0.55, WC.chest(lib1, [-0.03, 0.2, 0.33], [4, 180, 0])), WCK(10.1, 0.55, WC.chest(lib1, [-0.06, -0.17, 0.3], [50, 180, 0]))], [WCH(lib1, 'R', 'R', 0, 99)]);
    S.keys(trainer, [WK(0, { p:'present', ry:-50, talk:1 }), WK(2.0, { p:'point', ry:-90, armR:[70, 10, 0], head:[6, 0, 0], talk:1 }), WK(3.6, { p:'ease', ry:-60, talk:0 }), WK(4.6, { p:'present', ry:-30, armR:[110, 20, -30], elR:30, head:[-24, 0, 10], talk:1 }),
      WK(7.0, { p:'ease', ry:-70, talk:0, head:[0, 0, 0] }), WK(9.6, { p:'think', ry:-80 }), WK(11.6, { p:'present', ry:-60, talk:1 }), WK(13.4, { p:'ease', ry:-50, talk:0 }), WK(15, { p:'present', ry:-50, talk:1 })]);
    S.keys(lib1, [WK(0, { p:'ease', ry:40, head:[14, 0, -10] }), WK(2.4, { p:'ease', ry:60, head:[2, 0, 0] }), WK(4.2, { p:'ease', ry:80, head:[0, 0, 0] }), WK(6.4, { p:'ease', ry:20, head:[0, 0, 0] }), WK(8.6, { p:'ease', ry:50 }), WK(10.4, { p:'ease', ry:40, head:[0, 0, -30], talk:1 }), WK(12.4, { p:'ease', ry:40, head:[12, 0, -10], talk:0 }), WK(15, { p:'ease', ry:40, head:[14, 0, -10] })]);
    S.keys(lib2, [WK(0, { p:'ease', ry:30 }), WK(3.0, { p:'ease', ry:90, head:[-6, 0, 20] }), WK(6.0, { p:'ease', ry:200, head:[-10, 0, -10] }), WK(9.0, { p:'ease', ry:310, armL:[40, 30, 0], elL:30 }), WK(11.0, { p:'ease', ry:390, head:[-20, 0, 0], armL:[60, 40, 0], armR:[60, 40, 0], elL:20, elR:20, talk:1 }), WK(13.0, { p:'ease', ry:390, talk:0 }), WK(15, { p:'ease', ry:390 })]);
    S.tick((t) => { pano.rotation.y = t * 0.35; panoG.visible = t > 1 && t < 14.4; panoG.scale.setScalar(clamp(Math.min(t - 1, 14.4 - t) * 1.5, 0.01, 1)); });
  } },
/* ---------------------------------------------------------------- 10 */
{ id:'wax-2022b', n:10, year:'2022', title:'Lost Stories', backdrop:'shipyard', floor:'dock', loop:16,
  lines:[[0, 'Lost Stories: young people rebuild overlooked history in XR.'], [4.4, 'Marin City students model the World War II shipyards.'], [9.6, 'Their music honors the African-American workers who built the ships.']],
  item:{ title:'Lost Stories', date:'2022', where:'Marin City, California', partners:'The Marinovators, Marin City youth', src:['equity', 'cil'],
    desc:'In Marin City, students who call themselves the Marinovators built a VR experience of the World War II shipyards and life in Marin City, plus a musical tribute to the African-American workers whose stories were rarely told. XRLibraries’ director presented its Lost Stories work at Computers in Libraries in 2022.',
    more:'The project ran in three tracks: immersive storytelling, music and VR modeling.' },
  build(S){
    const m = waxM();
    /* A ship's hull, rib by rib, as a hologram */
    const ship = S.live3(0.2, 1.15, -2.9), ribs = [];
    for (let i = 0; i < 11; i++){ const k = i / 10, w = 0.45 * Math.sin(Math.PI * (0.12 + 0.76 * k)) + 0.08; const rib = WP.wire(S, new THREE.TorusGeometry(w, 0.012, 4, 16, Math.PI), ship); rib.rotation.set(0, Math.PI / 2, Math.PI); rib.position.set(-1.2 + k * 2.4, 0.2, 0); rib.visible = false; ribs.push(rib); }
    const keel = WP.wire(S, new THREE.BoxGeometry(2.5, 0.03, 0.03), ship); keel.position.y = 0.2 - 0.5;
    /* A keyboard on an X stand, played from behind so the player faces the room */
    const kb = S.live3(0, 0, 0); S.box(0.9, 0.08, 0.28, m.black, 0, 0.9, 0, 0, kb);
    const kc = mk(512, 64), kx = kc.getContext('2d'); kx.fillStyle = '#f4efe4'; kx.fillRect(0, 0, 512, 64); kx.fillStyle = '#9a948a'; for (let i = 1; i < 36; i++) kx.fillRect(Math.round(i * 512 / 36), 0, 2, 64);
    const keys = new THREE.Mesh(new THREE.BoxGeometry(0.86, 0.012, 0.13), [m.white, m.white, new THREE.MeshStandardMaterial({ map:tex(kc), roughness:0.45 }), m.white, m.white, m.white]); keys.position.set(0, 0.946, 0.065); kb.add(keys);
    const blk = new THREE.InstancedMesh(new THREE.BoxGeometry(0.0125, 0.012, 0.075), m.black, 25), bm = new THREE.Matrix4(); let nb = 0;
    for (let i = 0; i < 35 && nb < 25; i++){ if ([0, 1, 3, 4, 5].includes(i % 7)){ bm.makeTranslation(-0.43 + (i + 1) * 0.86 / 36, 0.957, 0.037); blk.setMatrixAt(nb++, bm); } }
    blk.count = nb; kb.add(blk);
    for (const sx of [-0.35, 0.35]){ const l = S.box(0.03, 0.92, 0.03, m.steel, sx, 0.45, 0, 0, kb); l.rotation.z = sx > 0 ? 0.3 : -0.3; }
    const notes = []; const nc = mk(64, 64), nx = nc.getContext('2d'); nx.fillStyle = '#ffd27a'; nx.font = '700 56px serif'; nx.textAlign = 'center'; nx.fillText('♪', 32, 50);
    const nm = new THREE.SpriteMaterial({ map:tex(nc), transparent:true, toneMapped:false, depthWrite:false });
    for (let i = 0; i < 7; i++){ const s = new THREE.Sprite(nm); s.scale.set(0.16, 0.16, 1); S.anim.add(s); notes.push(s); }
    const desk = WP.desk(S, 1.9, -2.0, 0.9, 0.55, 0.74, -0.3, m.pale);
    WP.screen(S, desk, 0, 0.74, -0.08, 0, 'model', 0.5, 0.3);
    WP.chair(S, 1.767, -1.57, 2.842, 0.42);
    const player = S.fig({ av:'ma12', scale:0.92, body:'boy', skin:WAX_SKIN.deep, hair:0x0e0b09, hairStyle:'curly', top:0xd9a441, bottom:0x2b2f38, eyes:0x2a1a10 }, [-1.84, -1.94], 20);
    const builder = S.fig({ av:'fa11', scale:0.93, body:'girl', skin:WAX_SKIN.brown, hair:0x120c0a, hairStyle:'braids', top:0xe9e2d0, jacket:0x6b2f3a, bottom:0x2b3445, eyes:0x2a1a10 }, [0.0, -1.6], 0);
    const modeler = S.fig({ av:'ma09', scale:0.92, body:'boy', skin:WAX_SKIN.medium, hair:0x1a120c, hairStyle:'crop', top:0x2f5d7c, bottom:0x3a3530 }, [1.767, -1.57], 162.8);
    S.carry(waxHeadset(), HS_GRIPS, [WCK(0, 0, WC.head(builder))]);
    /* His hands travel along the keys as he plays */
    const play = (ph, sp) => (t) => [0.065 * Math.sin(t * sp + ph) + 0.025 * Math.sin(t * sp * 2.3 + ph * 2), 0.011 * Math.max(0, Math.sin(t * 9 + ph * 3)), 0];
    S.carry(kb, { L:TYPE_GRIP(-0.17, 0.988, 0.115), R:TYPE_GRIP(0.17, 0.988, 0.115) }, [WCK(0, 0, WC.at(-1.7, 0, -1.55, [0, 200, 0]))],
      [WCH(player, 'L', 'L', 0, 99, 0.3, { off:play(0, 1.1) }), WCH(player, 'R', 'R', 0, 99, 0.3, { off:play(1.9, 1.4) })]);
    const bob = []; for (let t = 0, i = 0; t <= 16.001; t += 0.8, i++) bob.push(WK(t, { p:'ease', ry:20, spine:[8, 0, 0], head:[20 + (i % 2) * 7, 0, (i % 4 - 1.5) * 4], chest:[4, 0, i % 2 ? 2 : -2] }));
    S.keys(player, bob);
    const place = (t, i) => [WK(t, { armR:[80, 20 + (i % 3) * 14, 0], elR:20, armL:[30, 14, -20], elL:40, head:[-10, 0, (i % 3) * 14 - 14], ry:(i % 3) * 14 - 14, pointR:0.6 }), WK(t + 0.5, { armR:[60, 10 + (i % 3) * 14, -20], elR:46, head:[0, 0, (i % 3) * 14 - 14], ry:(i % 3) * 14 - 14, pointR:0.6 })];
    S.keys(builder, [WK(0, { p:'ease' }), ...[...Array(10).keys()].flatMap((i) => place(0.8 + i * 0.8, i)), WK(9.4, { p:'ease', head:[-10, 0, 0] }), WK(11.0, { p:'faceHands', armL:[60, 20, -40], armR:[60, 20, -40], elL:90, elR:90 }), WK(12.6, { p:'ease', head:[-16, 0, -30] }), WK(16, { p:'ease' })]);
    /* The modeler types at his desk, points at the hull, and claps when it is done */
    const DK = S.live3(0, 0, 0); S.box(0.42, 0.02, 0.14, m.black, 0, 0.01, 0, 0, DK); S.box(0.39, 0.004, 0.11, stdMat(0x3a3f46, 0.6), 0, 0.022, 0, 0, DK); S.box(0.06, 0.02, 0.1, m.black, 0.29, 0.01, 0.01, 0, DK);
    S.carry(DK, { L:TYPE_GRIP(-0.09, 0.06, 0.02), R:TYPE_GRIP(0.09, 0.06, 0.02) }, [WCK(0, 0, WC.at(1.865, 0.74, -1.885, [0, -17.2, 0]))],
      [WCH(modeler, 'L', 'L', 0, 4.6, 0.35, { off:waxTyping(0.4) }), WCH(modeler, 'R', 'R', 0, 9.3, 0.35, { off:waxTyping(2.2) }), WCH(modeler, 'L', 'L', 6.7, 9.3, 0.35, { off:waxTyping(1.0) }),
        WCH(modeler, 'L', 'L', 14.0, 99, 0.35, { off:waxTyping(0.4) }), WCH(modeler, 'R', 'R', 14.0, 99, 0.35, { off:waxTyping(2.2) })]);
    const sitT = (t, ex) => WK(t, Object.assign({ p:'sit', dy:-0.43, ry:162.8, spine:[10, 0, 0], armL:[40, 6, -20], armR:[40, 6, -20], elL:66, elR:66, handL:[-16, 0, 80], handR:[-16, 0, 80], head:[18, 0, 0] }, ex));
    S.keys(modeler, [sitT(0), sitT(3.0, { head:[22, 0, 4] }), sitT(4.95, { armL:[72, 42, 0], elL:6, pointL:1, head:[-6, 0, -40], talk:1 }), sitT(6.3, { armL:[72, 42, 0], elL:6, pointL:1, head:[-8, 0, -42], talk:0 }), sitT(7.0), sitT(9.0, { head:[18, 0, -8] }),
      WK(9.9, { p:'sit', dy:-0.43, ry:162.8, spine:[2, 0, 0], head:[-12, 0, -46] }), ...waxClaps(11.9, 12.9, { p:'sit', dy:-0.43, ry:162.8, spine:[2, 0, 0], head:[-12, 0, -40] }), WK(13.2, { p:'sit', dy:-0.43, ry:162.8, spine:[4, 0, 0], head:[-6, 0, -30] }), sitT(14.1), sitT(16)]);
    S.tick((t) => {
      const built = clamp(Math.floor((t - 0.8) / 0.8) + 1, 0, 11);
      ribs.forEach((rb, i) => { rb.visible = i < built && t < 15.2; });
      keel.visible = t > 0.6 && t < 15.2; ship.position.y = 1.15 + 0.04 * Math.sin(t * 1.2);
      notes.forEach((s, i) => { const tt = ((t * 0.55 + i / 7) % 1); s.visible = t > 0.6 && t < 15.4; s.position.set(-1.75 + Math.sin(tt * 6 + i) * 0.25, 1.05 + tt * 1.6, -1.5 + Math.cos(i * 2) * 0.2); s.material.opacity = 1 - tt; });
    });
  } },
/* ---------------------------------------------------------------- 11 */
{ id:'wax-2024', n:11, year:'2024', title:'Children Draw War, Not Flowers', backdrop:'vrgallery', floor:'grid', loop:16,
  lines:[[0, 'A VR gallery of art by Ukrainian children opens online.'], [5, 'Anyone can walk through it free, in a web browser.'], [10.4, 'XRLibraries helped design the exhibition.']],
  item:{ title:'Children Draw War, Not Flowers', date:'2024', where:'Online, in the browser', partners:'SJSU School of Information, Ukrainian librarians and children', src:['sjsu2024', 'metaverse'],
    desc:'XRLibraries helped design “Children Draw War, Not Flowers,” a browser-based VR art exhibition from the San José State University School of Information. It shows art by Ukrainian children aged 4 to 16 and virtual galleries showing the destruction of Ukrainian libraries, and anyone can visit it free in a web browser.',
    more:'XRLibraries lists the exhibition, which was honored at the Anthem Awards, among its shared worlds.' },
  build(S){
    const m = waxM();
    /* Floating frames with gentle crayon drawings */
    const frames = [], r = rnd(2024);
    for (let i = 0; i < 7; i++){
      const c = mk(256, 320), x = c.getContext('2d');
      x.fillStyle = '#fbf6ea'; x.fillRect(0, 0, 256, 320);
      x.lineWidth = 7; x.lineCap = 'round';
      const cols = ['#3b6ea8', '#f2c14e', '#e76f51', '#2a9d8f', '#6a4a8a', '#5a3a22'];
      for (let k = 0; k < 9; k++){ x.strokeStyle = cols[Math.floor(r() * cols.length)]; x.beginPath(); let px = 30 + r() * 196, py = 40 + r() * 240; x.moveTo(px, py); for (let s = 0; s < 6; s++){ px += (r() - 0.5) * 90; py += (r() - 0.5) * 90; x.lineTo(clamp(px, 20, 236), clamp(py, 20, 300)); } x.stroke(); }
      x.fillStyle = '#f2c14e'; x.beginPath(); x.arc(200, 60, 26, 0, Math.PI * 2); x.fill();
      const g = S.live3(0, 0, 0), fr = new THREE.Mesh(new THREE.BoxGeometry(0.62, 0.76, 0.03), stdMat(0x2a1d14, 0.5)); g.add(fr);
      const pic = new THREE.Mesh(new THREE.PlaneGeometry(0.54, 0.68), new THREE.MeshBasicMaterial({ map:tex(c), toneMapped:false })); pic.position.z = 0.017; g.add(pic);
      const glow = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 1.05), new THREE.MeshBasicMaterial({ map:tex(canvasPool()), transparent:true, opacity:0.35, blending:THREE.AdditiveBlending, depthWrite:false, toneMapped:false })); glow.position.z = -0.03; g.add(glow);
      frames.push({ g, a:i / 7 * Math.PI * 2 });
    }
    const stand = S.grp(2.9, 0, -2.2, -0.5); S.cyl(0.03, 0.05, 1.0, m.steel, 0, 0.5, 0, 12, stand); const lsc = S.grp(0, 1.0, 0, 0, stand); lsc.rotation.x = -0.4; S.box(0.42, 0.28, 0.02, m.black, 0, 0.14, 0, 0, lsc); S.plane(0.39, 0.25, waxScreenMat('gallery'), 0, 0.14, 0.011, 0, 0, lsc);
    const visitor = S.fig({ av:'fa08', body:'woman', skin:WAX_SKIN.light, hair:0x3a2a1e, hairStyle:'ponytail', top:0x3b6ea8, bottom:0x2b2f38, eyes:0x4a6a8a }, [-1.6, -2.0], 30);
    const lib = S.fig({ av:'fa01', body:'woman', skin:WAX_SKIN.olive, hair:0x2a1d14, hairStyle:'bob', top:0xf2c14e, jacket:0x2b2f38, bottom:0x2b2f38, legs:'skirt', hem:0.7, tights:0x2a2228, glasses:true }, [1.3, -1.6], -30);
    const kid = S.fig({ av:'fc01', scale:0.88, dye:[305, 22, 32, 1.0, 1.0], body:'kid', skin:WAX_SKIN.fair, hair:0xd8a85a, hairStyle:'bob', top:0xe76f51, sleeves:'long', bottom:0x3a4a6a }, [1.9, -1.9], -60);
    S.carry(waxHeadset(), HS_GRIPS, [WCK(0, 0, WC.head(visitor))]);
    S.keys(visitor, [WK(0, { p:'ease', ry:30 }), WK(3.4, { p:'ease', at:[-0.6, -2.5], ry:60, head:[-6, 0, -20] }), WK(5.6, { p:'reach', at:[-0.6, -2.5], ry:0, head:[-14, 0, 0] }), WK(7.6, { p:'ease', at:[-0.6, -2.5], ry:-30, head:[-10, 0, 20] }),
      WK(10.4, { p:'ease', at:[-1.6, -2.0], ry:-120 }), WK(12.4, { p:'faceHands', armL:[70, 20, -40], armR:[70, 20, -40], elL:110, elR:110, ry:30, head:[10, 0, 0] }), WK(14.0, { p:'ease', ry:30 }), WK(16, { p:'ease', ry:30 })]);
    S.keys(lib, [WK(0, { p:'ease', ry:-30, head:[10, 0, -30] }), WK(2.4, { p:'kneel', ry:-60, head:[0, 0, -20], talk:1 }), WK(4.0, { p:'kneel', ry:-60, armR:[60, 30, -10], elR:40, talk:0 }), WK(6.6, { p:'kneel', ry:-40, armL:[90, 30, 0], elL:20, head:[-24, 0, 0], talk:1 }),
      WK(9.0, { p:'kneel', ry:-60, armR:[50, 40, -30], elR:80, talk:0 }), WK(12.0, { p:'ease', ry:-30, head:[0, 0, -30] }), WK(16, { p:'ease', ry:-30, head:[10, 0, -30] })]);
    S.keys(kid, [WK(0, { p:'ease', ry:-60, head:[-10, 0, 20] }), WK(3.0, { p:'point', ry:-20, armR:[110, 20, 0], head:[-30, 0, 0] }), WK(5.0, { p:'ease', ry:-30, head:[-24, 0, 20], talk:1 }), WK(7.4, { p:'ease', ry:-90, head:[-10, 0, 30], talk:0 }), WK(9.6, { p:'faceHands', armL:[90, 20, -40], armR:[90, 20, -40], elL:120, elR:120, ry:-40, head:[-20, 0, 0] }), WK(12.0, { p:'ease', ry:-60, head:[-10, 0, 20] }), WK(16, { p:'ease', ry:-60, head:[-10, 0, 20] })]);
    S.tick((t) => {
      frames.forEach((f, i) => {
        const a = f.a + t * 0.16, on = clamp(Math.min(t - 0.4, 15.4 - t) * 1.5, 0, 1);
        f.g.visible = on > 0.01;
        f.g.position.set(Math.cos(a) * 2.6, 1.9 + 0.35 * Math.sin(t * 0.5 + i * 1.3), -2.2 + Math.sin(a) * 1.1);
        f.g.rotation.y = Math.atan2(-f.g.position.x * 0.4, 1.8 - f.g.position.z * 0.0) * 0.6; f.g.scale.setScalar(on);
      });
    });
  } },
/* ---------------------------------------------------------------- 12 */
{ id:'wax-2025', n:12, year:'2025', title:'Pollinators at the Fair', backdrop:'fair', floor:'fair', loop:16,
  lines:[[0, 'At the Marin County Fair, kids plant flowers in AR.'], [4.6, 'Monarch butterflies hatch and fly from flower to flower.'], [10.4, 'XRLibraries’ booth turns the fair into a pollinator garden.']],
  item:{ title:'Pollinators at the Fair', date:'2025', where:'Marin County Fair, California', partners:'Artist Cynthia Jensen', src:['fair'],
    desc:'At the 2025 Marin County Fair, XRLibraries’ bug-themed booth featured Pollinators, an augmented-reality app where fairgoers planted flowers and released monarch butterflies that flew around pollinating them. Marin artist Cynthia Jensen lent bug sculptures for the booth.' },
  build(S){
    const m = waxM();
    const booth = S.grp(-2.6, 0, -2.9, 0.35); S.box(1.4, 0.8, 0.6, stdMat(0x1d3b52, 0.7), 0, 0.4, 0, 0, booth); S.box(1.5, 0.04, 0.66, m.pale, 0, 0.82, 0, 0, booth);
    const bc = mk(512, 128), bx = bc.getContext('2d'); bx.fillStyle = '#f2c14e'; bx.fillRect(0, 0, 512, 128); bx.fillStyle = '#1d3b52'; bx.textAlign = 'center'; bx.font = '700 58px ' + F.display; bx.fillText('Pollinators', 256, 70); bx.font = '700 22px ' + F.type; bx.fillText('PLANT A FLOWER IN AR', 256, 108);
    S.plane(1.3, 0.32, new THREE.MeshStandardMaterial({ map:tex(bc), roughness:0.8 }), 0, 0.5, 0.305, 0, 0, booth);
    for (const sx of [-0.68, 0.68]) S.box(0.04, 1.6, 0.04, m.wood, sx, 1.6, -0.25, 0, booth);
    S.box(1.5, 0.3, 0.04, stdMat(0xc0392b, 0.7), 0, 2.3, -0.25, 0, booth);
    /* A big ladybug sculpture */
    const bug = S.grp(2.9, 0, -2.9, -0.6); const shell = S.sph(0.5, stdMat(0xc0392b, 0.35), 0, 0.42, 0, 1, 0.75, 1.3, bug); void shell;
    S.sph(0.26, m.black, 0, 0.42, 0.62, 1, 0.9, 0.9, bug); S.box(0.02, 0.62, 1.3, m.black, 0, 0.62, 0, 0, bug);
    for (const [px, pz] of [[0.25, 0.2], [-0.25, 0.2], [0.3, -0.25], [-0.3, -0.25], [0.15, -0.6], [-0.15, -0.6]]) S.sph(0.08, m.black, px, 0.7, pz, 1, 0.5, 1, bug);
    /* AR flowers sprout around the children as they tap their screens */
    const spots = [[-0.95, -0.62], [0.95, -0.6], [-0.35, -0.72], [0.4, -0.66], [-0.6, -2.1], [0.3, -2.05], [-1.0, -2.75], [0.85, -2.6], [-0.15, -2.95]];
    const flowers = spots.map(([x, z], i) => { const f = WP.flower(S, x, z, [0xf2c14e, 0xe76f51, 0xc77dff, 0xff9fbf][i % 4], 0.3 + (i % 3) * 0.07); f.scale.setScalar(0.01); return { f, at:1.6 + i * 0.45 }; });
    const flies = []; for (let i = 0; i < 6; i++){ const b = WP.butterfly(S); b.visible = false; flies.push(b); }
    /* Tablets: the screen faces the child holding it */
    const tabM = () => { const g = S.live3(0, 0, 0); S.box(0.24, 0.17, 0.012, m.black, 0, 0, 0, 0, g); S.plane(0.21, 0.14, waxScreenMat('ar'), 0, 0, -0.007, Math.PI, 0, g); return g; };
    const k1 = S.fig({ av:'mc02', scale:0.86, dye:[20, 50, 18, 1.0, 1.25, [0.28, 0.0, 0.72, 0.8]], body:'kid', skin:WAX_SKIN.brown, hair:0x120c0a, hairStyle:'puffs', top:0xf2c14e, sleeves:'short', bottom:0x2a9d8f, legs:'skirt', hem:0.5 }, [-0.7, -1.25], 14);
    const k2 = S.fig({ av:'mc01', scale:0.88, dye:[215, 2, 28, 1.0, 1.0], body:'kid', skin:WAX_SKIN.fair, hair:0x6a4a2e, hairStyle:'short', top:0x3b6ea8, sleeves:'short', bottom:0x4a3a2a, legs:'shorts', socks:0xffffff, cap:0xc0392b }, [0.7, -1.2], -14);
    const dad = S.fig({ av:'ma20', body:'man', skin:WAX_SKIN.tan, hair:0x2a1d14, hairStyle:'short', top:0x6b7a4a, bottom:0x3a3f46, beard:'full', glasses:0x2a221c }, [1.9, -1.9], -40);
    const vol = S.fig({ av:'fa17', body:'woman', skin:WAX_SKIN.medium, hair:0x2a1d14, hairStyle:'long', top:0x2a9d8f, bottom:0x2b2f38, lanyard:0xf2c14e }, [-2.2, -2.1], 45);
    /* Each child holds the tablet in the left hand and plants with the right index finger,
       then lifts it to follow the butterflies */
    const lowT = (f) => WC.chest(f, [0.03, -0.14, 0.27], [42, 0, 0]), upT = (f) => WC.chest(f, [0.02, 0.0, 0.3], [14, 0, 0]);
    const kidTab = (f, taps, cheer) => S.carry(tabM(), TAB_GRIPS, [WCK(0, 0, lowT(f)), WCK(5.5, 0.8, upT(f)), WCK(8.8, 0.8, lowT(f))],
      [WCH(f, 'L', 'L', 0, 99), WCH(f, 'R', 'R', 0, 1.0), WCH(f, 'R', 'tap', 1.0, 5.5, 0.3, { off:waxTaps(taps) }), WCH(f, 'R', 'R', 5.5, cheer), WCH(f, 'R', 'R', cheer + 2.2, 99)]);
    kidTab(k1, [1.4, 2.3, 3.2, 4.1, 4.85], 10.0); kidTab(k2, [1.85, 2.75, 3.65, 4.55], 10.3);
    const hold = { armL:[54, 10, -40], armR:[54, 10, -40], elL:76, elR:76, handL:[-24, 0, 70], handR:[-24, 0, 70], gripL:0.55, gripR:0.55 };
    const kidKeys = (ry, side, c) => [WK(0, Object.assign({ ry, head:[24, 0, 0] }, hold)), WK(1.2, Object.assign({ ry, head:[26, 0, side * 4] }, hold)), WK(3.4, Object.assign({ ry:ry - side * 6, head:[26, 0, side * 8] }, hold)), WK(5.2, Object.assign({ ry, head:[16, 0, 0] }, hold)),
      WK(6.4, Object.assign({ ry:ry + side * 20, head:[-14, 0, -side * 10] }, hold)), WK(8.0, Object.assign({ ry:ry - side * 10, head:[-22, 0, side * 14] }, hold)), WK(9.4, Object.assign({ ry, head:[20, 0, 0] }, hold)),
      WK(c + 0.4, Object.assign({ ry, head:[-6, 0, 0], talk:1 }, hold, { armR:[150, 22, 0], elR:20, gripR:0.9 })), WK(c + 1.5, Object.assign({ ry, head:[-4, 0, 0], talk:0 }, hold, { armR:[146, 18, 0], elR:26, gripR:0.9 })),
      WK(c + 2.5, Object.assign({ ry, head:[20, 0, side * 10], talk:1 }, hold)), WK(14.0, Object.assign({ ry, head:[24, 0, 0], talk:0 }, hold)), WK(16, Object.assign({ ry, head:[24, 0, 0] }, hold))];
    S.keys(k1, kidKeys(14, 1, 10.0)); S.keys(k2, kidKeys(-14, -1, 10.3));
    /* Dad keeps his phone in his hand, then lifts it to take a picture */
    const ph = S.live3(0, 0, 0); S.box(0.075, 0.15, 0.01, m.black, 0, 0, 0, 0, ph); S.plane(0.065, 0.13, waxScreenMat('ar'), 0, 0, 0.006, 0, 0, ph); S.sph(0.006, stdMat(0x111820, 0.1, 0.4), 0.025, 0.06, -0.006, 1, 1, 0.4, ph);
    S.carry(ph, PHONE_GRIPS, [WCK(0, 0, WC.palm(dad, 'R', PHONE_GRIPS.R)), WCK(8.7, 0.7, WC.chest(dad, [-0.04, 0.2, 0.34], [4, 180, 0])), WCK(12.3, 0.75, WC.palm(dad, 'R', PHONE_GRIPS.R))],
      [WCH(dad, 'R', 'R', 8.7, 13.1)]);
    S.keys(dad, [WK(0, { p:'ease', ry:-40, head:[10, 0, 0], gripR:0.62 }), WK(3.0, { p:'ease', ry:-60, armL:[78, 22, 0], elL:6, pointL:1, head:[-10, 0, 0], talk:1, gripR:0.62 }), WK(5.6, { p:'ease', ry:-30, head:[-26, 0, 0], talk:0, gripR:0.62 }),
      WK(8.3, { p:'ease', ry:-45, head:[0, 0, 0], gripR:0.62 }), WK(9.4, { p:'phone', ry:-50, head:[0, 0, 0], gripR:0.62 }), WK(11.8, { p:'phone', ry:-44, head:[0, 0, 0], gripR:0.62 }), WK(13.0, { p:'ease', ry:-40, head:[4, 0, 0], gripR:0.62 }), WK(16, { p:'ease', ry:-40, head:[10, 0, 0], gripR:0.62 })]);
    S.keys(vol, [WK(0, { p:'present', ry:45, talk:1 }), WK(2.6, { p:'ease', ry:45, talk:0 }), WK(4.6, { p:'point', ry:30, armR:[120, 20, 0], head:[-24, 0, 0] }), WK(7.0, { p:'ease', ry:60 }), WK(9.4, { p:'present', ry:40, talk:1 }), WK(11.6, { p:'ease', ry:45, talk:0 }), WK(16, { p:'present', ry:45, talk:1 })]);
    S.tick((t) => {
      for (const q of flowers){ const k = clamp(Math.min((t - q.at) / 0.6, (15.2 - t) / 0.8), 0, 1); q.f.scale.setScalar(Math.max(0.01, k)); q.f.visible = k > 0.01; q.f.rotation.y = t * 0.3; }
      flies.forEach((b, i) => {
        const on = clamp(Math.min((t - 4.8 - i * 0.3) / 0.5, (14.8 - t) / 0.6), 0, 1); b.visible = on > 0.01; if (!b.visible) return;
        const sp = spots[(i * 2 + Math.floor(t / 2.2)) % spots.length], a = t * (1.1 + i * 0.1) + i;
        b.position.set(sp[0] + Math.cos(a) * 0.35, 0.55 + 0.35 * Math.sin(t * 1.7 + i) + (t > 13.4 ? (t - 13.4) * 1.4 : 0), sp[1] + Math.sin(a) * 0.3);
        b.rotation.y = -a; b.scale.setScalar(on * 1.6);
        const f = Math.sin(t * 16 + i * 2) * 0.9; b.userData.r.rotation.z = f; b.userData.l.rotation.z = -f;
      });
    });
  } }
];
