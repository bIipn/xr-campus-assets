const looks = [
  { body:'man', skin:WAX_SKIN.fair, hair:0x3b2a1e, hairStyle:'short', top:0x2f5d7c, bottom:0x2b2f38, belt:0x2a1c12, collar:0xe8e2d6, eyes:0x3a5a7a },
  { body:'woman', skin:WAX_SKIN.brown, hair:0x1a1310, hairStyle:'curly', top:0xb5473a, jacket:0x2a3a4e, bottom:0x23262e, eyes:0x3a2416 },
  { body:'girl', skin:WAX_SKIN.light, hair:0x8a5a2e, hairStyle:'ponytail', top:0x2aa198, sleeves:'short', bottom:0x3a4a6a, legs:'shorts', socks:0xf0ece2, lanyard:0xcda961 },
  { body:'kid', skin:WAX_SKIN.medium, hair:0x161210, hairStyle:'puffs', top:0xf2c14e, sleeves:'short', bottom:0x5a3e8a, legs:'skirt', hem:0.5 },
  { body:'elder', skin:WAX_SKIN.olive, hair:0xc9c4bc, hairStyle:'balding', top:0x6b5a44, bottom:0x3a3a3a, glasses:true, beard:'full' },
  { body:'woman', skin:WAX_SKIN.tan, hair:0x24170f, hairStyle:'bob', top:0xe9e2d0, bottom:0x6b2f3a, legs:'skirt', hem:0.35, dress:true },
  { body:'boy', skin:WAX_SKIN.deep, hair:0x0e0b09, hairStyle:'crop', top:0x3a6b3a, bottom:0x2b3445, cap:0xb5473a },
  { body:'woman', skin:WAX_SKIN.medium, hair:0x1a1310, scarf:0x2f6b5a, top:0x5a4a7a, bottom:0x2a2a30, legs:'skirt', hem:0.95, dress:true }
];
const poses = ['ease', 'present', 'wave', 'clap', 'stand', 'think', 'cheer', 'hold'];
looks.forEach((L, i) => {
  const f = makeWaxFigure(L);
  scene.add(f.root);
  f.track = waxTrack([{ t:0, p:poses[i] }], { at:[(i - 3.5) * 0.78, 0], ry:0 });
  waxSample(f, 0); waxApply(f, false, 0);
  if (i === 6){ waxGiveHeadset(f); f.pose[WR + 5] = 2; waxApply(f, false, 0); }
});
