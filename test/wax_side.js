const looks = [
  { body:'man', skin:WAX_SKIN.fair, hair:0x3b2a1e, hairStyle:'short', top:0x2f5d7c, bottom:0x2b2f38, belt:0x2a1c12, collar:0xe8e2d6 },
  { body:'woman', skin:WAX_SKIN.medium, hair:0x24170f, hairStyle:'bob', top:0xe9e2d0, bottom:0x6b2f3a, legs:'skirt', hem:0.35 },
  { body:'kid', skin:WAX_SKIN.brown, hair:0x161210, hairStyle:'puffs', top:0xf2c14e, sleeves:'short', bottom:0x5a3e8a, legs:'shorts', socks:0xffffff },
  { body:'elder', skin:WAX_SKIN.olive, hair:0xc9c4bc, hairStyle:'balding', top:0x6b5a44, bottom:0x3a3a3a, glasses:true }
];
const P = [{ p:'stand' }, { p:'sit' }, { p:'sitFloor' }, { p:'kneel' }];
looks.forEach((L, i) => {
  const f = makeWaxFigure(L); scene.add(f.root);
  f.track = waxTrack([Object.assign({ t:0 }, P[i])], { at:[(i - 1.5) * 1.0, 0], ry:i % 2 ? 0.9 : -0.9 });
  waxSample(f, 0); waxApply(f, false, 0);
});
cam.position.set(0, 1.3, 5.6); cam.lookAt(0, 0.85, 0);
