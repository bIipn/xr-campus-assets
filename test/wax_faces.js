const looks = [
  { body:'man', skin:WAX_SKIN.fair, hair:0x3b2a1e, hairStyle:'short', top:0x2f5d7c, collar:0xe8e2d6, eyes:0x3a5a7a },
  { body:'woman', skin:WAX_SKIN.brown, hair:0x1a1310, hairStyle:'curly', top:0xb5473a, jacket:0x2a3a4e, eyes:0x3a2416 },
  { body:'girl', skin:WAX_SKIN.light, hair:0x8a5a2e, hairStyle:'ponytail', top:0x2aa198 },
  { body:'elder', skin:WAX_SKIN.olive, hair:0xc9c4bc, hairStyle:'balding', top:0x6b5a44, glasses:true, beard:'full' }
];
looks.forEach((L, i) => {
  const f = makeWaxFigure(L); scene.add(f.root);
  f.track = waxTrack([{ t:0, p:'stand', head:[0, 0, i === 3 ? -35 : 0] }], { at:[(i - 1.5) * 0.36, 0], ry:i === 2 ? -0.5 : 0 });
  waxSample(f, 0); waxApply(f, false, 0);
  if (i === 1){ f.body.morphTargetInfluences[1] = 1; }
  if (i === 0){ f.body.morphTargetInfluences[0] = 0.6; }
});
cam.fov = 18; cam.position.set(0, 1.6, 2.4); cam.lookAt(0, 1.58, 0); cam.updateProjectionMatrix();
