const L0 = { body:'man', skin:WAX_SKIN.fair, hair:0x3b2a1e, hairStyle:'short', top:0x2f5d7c, bottom:0x2b2f38 };
const P = [
  { armR:[10, 85, 90], elR:100 }, { armR:[10, 85, -90], elR:100 },
  { p:'faceHands' }, { p:'tablet' }, { p:'type' }, { armL:[40, 10, 90], elL:70, armR:[40, 10, 90], elR:70 }, { armL:[40, 10, -90], elL:70, armR:[40, 10, -90], elR:70 }, { p:'hold' }
];
P.forEach((k, i) => {
  const f = makeWaxFigure(L0); scene.add(f.root);
  f.track = waxTrack([Object.assign({ t:0 }, k)], { at:[(i - 3.5) * 0.78, 0], ry:i >= 5 ? 35 : 0 });
  waxSample(f, 0); waxApply(f, false, 0);
});
