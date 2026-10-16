/* ================================================================
   Hands that really hold things: palm frames, two-bone arm IK, grips
   A grip says where a palm touches an object (in the object's frame),
   which way the palm faces into it and which way the fingers run.
   ================================================================ */
const _ik = {
  a:new THREE.Vector3(), b:new THREE.Vector3(), c:new THREE.Vector3(), d:new THREE.Vector3(), e:new THREE.Vector3(), t:new THREE.Vector3(), s:new THREE.Vector3(),
  x:new THREE.Vector3(), y:new THREE.Vector3(), z:new THREE.Vector3(), u:new THREE.Vector3(), v:new THREE.Vector3(), one:new THREE.Vector3(1, 1, 1),
  q:new THREE.Quaternion(), q2:new THREE.Quaternion(), q3:new THREE.Quaternion(), pq:new THREE.Quaternion(), uq:new THREE.Quaternion(), fq:new THREE.Quaternion(), hq:new THREE.Quaternion(),
  q0a:new THREE.Quaternion(), q0f:new THREE.Quaternion(), q0h:new THREE.Quaternion(), m:new THREE.Matrix4(), m2:new THREE.Matrix4()
};
const IK_X = new THREE.Vector3(1, 0, 0), IK_Y = new THREE.Vector3(0, 1, 0);

/* The palm frame of one hand in the hand bone's rest frame (figure units): origin on the palm surface,
   Y along the fingers, Z out of the palm toward whatever the hand holds */
function hkPalmDef(R, s){
  R.palm = R.palm || {};
  if (R.palm[s]) return R.palm[s];
  const P = R.P, W = P[HB[s + '_Hand']], M = P[HB[s + '_Finger2']], M1 = P[HB[s + '_Finger21']], I = P[HB[s + '_Finger1']], K = P[HB[s + '_Finger4']];
  const along = new THREE.Vector3().subVectors(M, W).normalize();
  const n = new THREE.Vector3().subVectors(K, I).cross(new THREE.Vector3().subVectors(M1, M)).normalize().multiplyScalar(s === 'L' ? 1 : -1);
  n.addScaledVector(along, -n.dot(along)).normalize();
  const x = new THREE.Vector3().crossVectors(along, n).normalize();
  const q = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, along, n));
  const c = new THREE.Vector3().subVectors(M, W).multiplyScalar(0.6).addScaledVector(n, 0.017);
  return (R.palm[s] = { q, qi:q.clone().invert(), c, len:M.distanceTo(W) });
}
/* World palm frame (needs the figure's world matrices up to date) */
function hkPalmWorld(fig, s, pos, quat){
  const D = hkPalmDef(fig.R, s), hd = fig.all[HB[s + '_Hand']];
  hd.matrixWorld.decompose(pos, quat, _ik.s);
  pos.add(_ik.a.copy(D.c).multiplyScalar(fig.S).applyQuaternion(quat));
  quat.multiply(D.q);
}
/* A grip as a matrix in its object's frame: p where the palm touches, into = palm normal (into the object),
   fingers = the way the fingers run */
function gripMatrix(g){
  if (g.M) return g.M;
  const z = new THREE.Vector3().fromArray(g.into).normalize(), y = new THREE.Vector3().fromArray(g.fingers);
  y.addScaledVector(z, -y.dot(z)).normalize();
  const x = new THREE.Vector3().crossVectors(y, z).normalize();
  g.M = new THREE.Matrix4().makeBasis(x, y, z).setPosition(g.p[0], g.p[1], g.p[2]);
  g.Mi = g.M.clone().invert();
  return g.M;
}

/* Two-bone IK for one arm. Puts the palm on (pos, quat) in world space, the elbow pointing toward pole
   (a world direction), blended over the current pose by w. The elbow is a hinge; half the wrist's roll
   goes into the forearm so the skin twists along it instead of at the wrist. */
function hkArmIK(fig, s, palmPos, palmQuat, pole, w){
  if (!(w > 0.001)) return;
  const ua = fig.all[HB[s + '_UpperArm']], fa = fig.all[HB[s + '_Forearm']], hd = fig.all[HB[s + '_Hand']], D = hkPalmDef(fig.R, s), K = _ik;
  K.q0a.copy(ua.quaternion); K.q0f.copy(fa.quaternion); K.q0h.copy(hd.quaternion);
  /* Wrist target from the palm target */
  K.hq.copy(palmQuat).multiply(D.qi);
  K.t.copy(D.c).multiplyScalar(fig.S).applyQuaternion(K.hq); K.t.subVectors(palmPos, K.t);
  ua.parent.matrixWorld.decompose(K.a, K.pq, K.s);
  const S0 = K.b.setFromMatrixPosition(ua.matrixWorld);
  const L1 = fa.position.length(), L2 = hd.position.length();
  const dir = K.c.subVectors(K.t, S0); let d = dir.length(); if (d < 1e-6) return; dir.divideScalar(d);
  d = clamp(d, Math.abs(L1 - L2) + 1e-4, (L1 + L2) * 0.9995);
  const a = (L1 * L1 - L2 * L2 + d * d) / (2 * d), h = Math.sqrt(Math.max(0, L1 * L1 - a * a));
  const pd = K.d.copy(pole).addScaledVector(dir, -pole.dot(dir));
  if (pd.lengthSq() < 1e-8) pd.set(0, -1, 0).addScaledVector(dir, dir.y); pd.normalize();
  const E = K.e.copy(S0).addScaledVector(dir, a).addScaledVector(pd, h);
  const u = K.u.subVectors(E, S0).normalize(), v = K.v.copy(S0).addScaledVector(dir, d).sub(E).normalize();
  const ce = clamp(u.dot(v), -1, 1), el = Math.acos(ce), se = Math.sin(el);
  /* Upper arm frame: the bone runs along -Y, bends about X, toward +Z */
  const Y = K.y.copy(u).negate(), Z = K.z;
  if (se > 1e-3) Z.copy(v).addScaledVector(u, -ce).divideScalar(se); else Z.copy(pd).negate();
  Z.addScaledVector(Y, -Z.dot(Y)).normalize();
  const X = K.x.crossVectors(Y, Z).normalize();
  K.uq.setFromRotationMatrix(K.m.makeBasis(X, Y, Z));
  ua.quaternion.copy(K.pq).invert().multiply(K.uq);
  K.fq.setFromAxisAngle(IK_X, -el);
  /* Hand: what's left after the arm, with the roll shared with the forearm */
  K.q.copy(K.uq).multiply(K.fq).invert().multiply(K.hq);
  const tw = 2 * Math.atan2(K.q.y, K.q.w);
  const roll = Math.abs(tw) > 0.02 ? tw * 0.5 : 0;
  fa.quaternion.copy(K.fq).multiply(K.q2.setFromAxisAngle(IK_Y, roll));
  hd.quaternion.copy(K.q3.setFromAxisAngle(IK_Y, -roll)).multiply(K.q);
  if (w < 0.999){ ua.quaternion.slerpQuaternions(K.q0a, ua.quaternion, w); fa.quaternion.slerpQuaternions(K.q0f, fa.quaternion, w); hd.quaternion.slerpQuaternions(K.q0h, hd.quaternion, w); }
  ua.updateMatrixWorld(true);
}
/* The default elbow direction: down, a little out and back, in the figure's frame */
function hkPole(fig, s, out, v){
  const sd = s === 'L' ? 1 : -1;
  v = v || new THREE.Vector3();
  v.set(sd * (out == null ? 0.55 : out), -1, -0.3).normalize().applyQuaternion(fig.root.quaternion);
  return v;
}
/* Put a palm on a grip of an object whose world matrix is M */
const _hkGp = new THREE.Vector3(), _hkGq = new THREE.Quaternion(), _hkGpole = new THREE.Vector3();
function hkGrip(fig, s, M, grip, w, pole){
  _ik.m2.multiplyMatrices(M, gripMatrix(grip)).decompose(_hkGp, _hkGq, _ik.s);
  hkArmIK(fig, s, _hkGp, _hkGq, pole || hkPole(fig, s, grip.out, _hkGpole), w);
}
/* World matrix that puts grip g of an object exactly in fig's palm s */
function hkAnchorMatrix(fig, s, grip, out){
  hkPalmWorld(fig, s, _hkGp, _hkGq);
  out.compose(_hkGp, _hkGq, _ik.one);
  gripMatrix(grip);
  return out.multiply(grip.Mi);
}
