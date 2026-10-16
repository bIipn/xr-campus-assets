/* ================================================================
   Room 103: the five blueprints, drawn line by line
   Every drawing lives in an 880 × 720 space. Each part has an anchor (a),
   a numbered balloon (b), hit shapes and its own drawing.
   ================================================================ */
const BPC = { bg0:'#1f5596', bg1:'#143d70', line:'#eaf4ff', faint:'rgba(234,244,255,0.42)', grid:'rgba(255,255,255,0.065)', grid2:'rgba(255,255,255,0.14)', hi:'#ffd166', hiFill:'rgba(255,209,102,0.2)', ink:'#183f70' };
const BPW = 880, BPH = 720;
function bP(ctx, pts, close){ ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]); if (close) ctx.closePath(); }
function bSF(ctx, hl){ if (hl) ctx.fill(); ctx.stroke(); }
function bR(ctx, x0, y0, x1, y1, hl){ ctx.beginPath(); ctx.rect(x0, y0, x1 - x0, y1 - y0); bSF(ctx, hl); }
function bC(ctx, x, y, r, hl){ ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); bSF(ctx, hl); }
function bL(ctx, x0, y0, x1, y1){ ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke(); }
function bThin(ctx, k, fn){ ctx.save(); ctx.lineWidth *= k; ctx.shadowBlur = 0; fn(); ctx.restore(); }
function bDash(ctx, d, fn){ ctx.save(); ctx.setLineDash(d); fn(); ctx.restore(); }
function bTag(ctx, t, x, y){ ctx.save(); ctx.shadowBlur = 0; ctx.fillStyle = BPC.ink; ctx.strokeStyle = BPC.line; ctx.lineWidth = 1.4; ctx.beginPath(); ctx.roundRect ? ctx.roundRect(x - 9, y - 9, 18, 18, 4) : ctx.rect(x - 9, y - 9, 18, 18); ctx.fill(); ctx.stroke(); ctx.fillStyle = BPC.line; ctx.font = '700 12px ' + F.type; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(t, x, y + 1); ctx.restore(); }
function bTxt(ctx, s, x, y, size, align, weight){ ctx.save(); ctx.shadowBlur = 0; ctx.fillStyle = ctx.strokeStyle; ctx.font = (weight || '700') + ' ' + (size || 13) + 'px ' + F.type; ctx.textAlign = align || 'center'; ctx.textBaseline = 'middle'; ctx.fillText(s, x, y); ctx.restore(); }
function bClip(ctx, pathFn, fn){ ctx.save(); pathFn(); ctx.clip(); fn(); ctx.restore(); }
function bHatch(ctx, x0, y0, x1, y1, step){ ctx.beginPath(); const h = y1 - y0; for (let k = x0 - h; k < x1; k += step){ ctx.moveTo(k, y1); ctx.lineTo(k + h, y0); } ctx.stroke(); }
function bArrow(ctx, x0, y0, x1, y1, s){ const a = Math.atan2(y1 - y0, x1 - x0), k = s || 9; bL(ctx, x0, y0, x1, y1); bP(ctx, [[x1 - Math.cos(a - 0.4) * k, y1 - Math.sin(a - 0.4) * k], [x1, y1], [x1 - Math.cos(a + 0.4) * k, y1 - Math.sin(a + 0.4) * k]]); ctx.stroke(); }
function bDim(ctx, x0, y0, x1, y1, text){
  bThin(ctx, 0.6, () => {
    bL(ctx, x0, y0, x1, y1);
    const a = Math.atan2(y1 - y0, x1 - x0), k = 10;
    for (const [x, y, s] of [[x0, y0, 1], [x1, y1, -1]]){ bP(ctx, [[x + s * Math.cos(a - 0.3) * k, y + s * Math.sin(a - 0.3) * k], [x, y], [x + s * Math.cos(a + 0.3) * k, y + s * Math.sin(a + 0.3) * k]]); ctx.stroke(); }
  });
  ctx.save(); ctx.translate((x0 + x1) / 2, (y0 + y1) / 2); let a = Math.atan2(y1 - y0, x1 - x0); if (a > Math.PI / 2) a -= Math.PI; if (a < -Math.PI / 2) a += Math.PI; ctx.rotate(a);
  ctx.font = '700 13px ' + F.type; const w = ctx.measureText(text).width + 12; ctx.fillStyle = BPC.ink; ctx.fillRect(-w / 2, -9, w, 18); bTxt(ctx, text, 0, 0, 13); ctx.restore();
}
function bCyl(ctx, x0, y0, x1, y1, w, k, hl){
  /* A hydraulic cylinder: a fat barrel, then a thin rod, with pins at both ends */
  const dx = x1 - x0, dy = y1 - y0, L = Math.hypot(dx, dy), ux = dx / L, uy = dy / L, nx = -uy, ny = ux, xm = x0 + dx * k, ym = y0 + dy * k, r = w * 0.32;
  bP(ctx, [[x0 + nx * w / 2, y0 + ny * w / 2], [xm + nx * w / 2, ym + ny * w / 2], [xm - nx * w / 2, ym - ny * w / 2], [x0 - nx * w / 2, y0 - ny * w / 2]], true); bSF(ctx, hl);
  bP(ctx, [[xm + nx * r, ym + ny * r], [x1 + nx * r, y1 + ny * r], [x1 - nx * r, y1 - ny * r], [xm - nx * r, ym - ny * r]], true); bSF(ctx, hl);
  bC(ctx, x0, y0, w * 0.32, false); bC(ctx, x1, y1, w * 0.32, false);
}
function bFan(ctx, x, y, r, n){
  bC(ctx, x, y, r, false); bC(ctx, x, y, r * 0.2, false);
  bThin(ctx, 0.7, () => { for (let k = 0; k < (n || 6); k++){ const a = k * Math.PI * 2 / (n || 6); ctx.beginPath(); ctx.moveTo(x + Math.cos(a) * r * 0.22, y + Math.sin(a) * r * 0.22); ctx.quadraticCurveTo(x + Math.cos(a + 0.5) * r * 0.75, y + Math.sin(a + 0.5) * r * 0.75, x + Math.cos(a + 0.2) * r * 0.94, y + Math.sin(a + 0.2) * r * 0.94); ctx.stroke(); } });
}
function bWheel(ctx, x, y, hl){
  bC(ctx, x, y, 55, hl); bC(ctx, x, y, 36, false); bC(ctx, x, y, 9, false);
  bThin(ctx, 0.7, () => { for (let k = 0; k < 5; k++){ const a = k * Math.PI * 2 / 5 - Math.PI / 2; bL(ctx, x + Math.cos(a) * 12, y + Math.sin(a) * 12, x + Math.cos(a) * 34, y + Math.sin(a) * 34); } for (let k = 0; k < 28; k++){ const a = k * Math.PI * 2 / 28; bL(ctx, x + Math.cos(a) * 49, y + Math.sin(a) * 49, x + Math.cos(a) * 55, y + Math.sin(a) * 55); } });
}
function bWavy(ctx, x0, y0, x1, y1, vertical){
  ctx.beginPath();
  if (vertical){ const mid = (x0 + x1) / 2, amp = (x1 - x0) / 2 - 1; for (let y = y0; y <= y1; y += 2){ const x = mid + Math.sin((y - y0) * 0.45) * amp; y === y0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y); } }
  else { const mid = (y0 + y1) / 2, amp = (y1 - y0) / 2 - 1; for (let x = x0; x <= x1; x += 2){ const y = mid + Math.sin((x - x0) * 0.45) * amp; x === x0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y); } }
  ctx.stroke();
}
const bRect = (x0, y0, x1, y1) => ({ r:[x0, y0, x1, y1] });
const bCirc = (x, y, r) => ({ c:[x, y, r] });
const bSeg = (x0, y0, x1, y1, w) => ({ s:[x0, y0, x1, y1, w] });
const bPoly = (pts) => ({ p:pts });

/* ---------- 1. Automobile ---------- */
const CAR_BODY = [[122, 560], [112, 528], [114, 500], [128, 474], [200, 462], [330, 446], [425, 372], [612, 366], [650, 372], [752, 432], [796, 444], [806, 470], [808, 520], [800, 560]];
function carBodyPath(ctx){
  ctx.beginPath(); ctx.moveTo(CAR_BODY[0][0], CAR_BODY[0][1]);
  for (const p of CAR_BODY.slice(1)) ctx.lineTo(p[0], p[1]);
  ctx.lineTo(718, 560); ctx.lineTo(718, 545); ctx.arc(650, 545, 68, 0, Math.PI, true); ctx.lineTo(582, 560);
  ctx.lineTo(298, 560); ctx.lineTo(298, 545); ctx.arc(230, 545, 68, 0, Math.PI, true); ctx.lineTo(162, 560); ctx.closePath();
}
const BP_CAR = {
  base(ctx){
    bL(ctx, 40, 600, 840, 600); bThin(ctx, 0.7, () => { for (let x = 44; x < 840; x += 16) bL(ctx, x, 600, x - 10, 611); });
    bDash(ctx, [4, 5], () => { bThin(ctx, 0.6, () => { bL(ctx, 112, 500, 112, 270); bL(ctx, 808, 520, 808, 270); bL(ctx, 230, 545, 230, 636); bL(ctx, 650, 545, 650, 636); bL(ctx, 600, 366, 864, 366); }); });
    bDim(ctx, 112, 280, 808, 280, '4,250'); bDim(ctx, 230, 628, 650, 628, '2,600'); bDim(ctx, 852, 366, 852, 600, '1,450');
    bDash(ctx, [12, 4, 2, 4], () => { bThin(ctx, 0.6, () => { for (const x of [230, 650]){ bL(ctx, x - 70, 545, x + 70, 545); bL(ctx, x, 475, x, 615); } }); });
    bTxt(ctx, 'FRONT', 70, 600 - 14, 12); bTxt(ctx, 'ALL DIMENSIONS IN MM', 760, 700, 11, 'center', '400');
  },
  parts:[
    { a:[222, 510], b:[200, 395], hit:[bRect(148, 462, 294, 542)], draw(ctx, hl){
      bP(ctx, [[150, 480], [292, 480], [292, 540], [166, 540], [150, 524]], true); bSF(ctx, hl);
      rrect(ctx, 158, 464, 128, 16, 5); bSF(ctx, hl);
      bThin(ctx, 0.7, () => { for (let i = 0; i < 4; i++) bC(ctx, 178 + i * 30, 472, 3.5, false); bC(ctx, 168, 522, 13, false); bC(ctx, 196, 494, 8, false); bL(ctx, 159, 513, 190, 488); bL(ctx, 177, 531, 203, 499); for (let i = 0; i < 4; i++) bL(ctx, 215 + i * 18, 488, 215 + i * 18, 532); });
      bTxt(ctx, 'ENGINE', 240, 510, 12);
    } },
    { a:[330, 530], b:[360, 664], hit:[bRect(290, 486, 354, 548)], draw(ctx, hl){
      bP(ctx, [[292, 488], [352, 500], [352, 546], [292, 546]], true); bSF(ctx, hl);
      bC(ctx, 322, 524, 14, false);
      bThin(ctx, 0.7, () => { for (let k = 0; k < 12; k++){ const a = k * Math.PI / 6; bL(ctx, 322 + Math.cos(a) * 14, 524 + Math.sin(a) * 14, 322 + Math.cos(a) * 18, 524 + Math.sin(a) * 18); } bC(ctx, 322, 524, 4, false); });
    } },
    { a:[285, 544], b:[272, 664], hit:[bRect(228, 532, 342, 558)], draw(ctx, hl){
      bDash(ctx, [10, 5], () => { bL(ctx, 334, 540, 240, 547); });
      bC(ctx, 334, 540, 6, hl); bC(ctx, 240, 547, 6, hl);
    } },
    { a:[135, 505], b:[70, 430], hit:[bRect(122, 468, 150, 542)], draw(ctx, hl){
      bR(ctx, 128, 474, 143, 536, hl);
      bThin(ctx, 0.6, () => { for (let y = 480; y < 534; y += 6) bL(ctx, 128, y, 143, y); });
      ctx.beginPath(); ctx.moveTo(143, 482); ctx.quadraticCurveTo(150, 470, 158, 480); ctx.stroke();
    } },
    { a:[324, 465], b:[300, 395], hit:[bRect(298, 442, 350, 482)], draw(ctx, hl){
      bR(ctx, 302, 452, 346, 478, hl); bR(ctx, 308, 446, 316, 452, hl); bR(ctx, 332, 446, 340, 452, hl);
      bTxt(ctx, '+', 312, 464, 13); bTxt(ctx, '−', 336, 464, 13);
    } },
    { a:[594, 536], b:[566, 664], hit:[bRect(544, 516, 644, 556), bSeg(640, 528, 744, 468, 10)], draw(ctx, hl){
      rrect(ctx, 548, 520, 92, 32, 8); bSF(ctx, hl);
      ctx.beginPath(); ctx.moveTo(640, 528); ctx.lineTo(700, 500); ctx.lineTo(740, 472); ctx.stroke(); bC(ctx, 744, 469, 5, hl);
      bTxt(ctx, 'FUEL', 594, 536, 11);
    } },
    { a:[384, 557], b:[458, 664], hit:[bRect(288, 546, 810, 574)], draw(ctx, hl){
      ctx.beginPath(); ctx.moveTo(292, 553); ctx.lineTo(360, 557); ctx.stroke();
      bR(ctx, 360, 550, 408, 565, hl); bThin(ctx, 0.6, () => { for (let x = 366; x < 406; x += 6) bL(ctx, x, 551, x, 564); });
      bL(ctx, 408, 557, 689, 559);
      ctx.beginPath(); ctx.ellipse(725, 559, 36, 9, 0, 0, Math.PI * 2); bSF(ctx, hl);
      bL(ctx, 761, 559, 806, 556);
    } },
    { a:[652, 468], b:[700, 330], hit:[bRect(636, 438, 682, 494)], draw(ctx, hl){
      const pts = []; for (let i = 0; i <= 10; i++) pts.push([650 + (i % 2 ? 9 : -9), 488 - i * 4]); pts[0][0] = 650; pts[10][0] = 650;
      bP(ctx, pts); ctx.stroke();
      bR(ctx, 664, 466, 674, 490, hl); bL(ctx, 669, 466, 669, 446);
      bR(ctx, 640, 444, 680, 448, hl);
    } },
    { a:[254, 520], b:[178, 664], hit:[bCirc(230, 545, 30), bPoly([[248, 510], [270, 520], [268, 545], [252, 538]])], draw(ctx, hl){
      bThin(ctx, 0.75, () => { bC(ctx, 230, 545, 29, false); bC(ctx, 230, 545, 13, false); for (let k = 0; k < 10; k++){ const a = k * Math.PI / 5; bC(ctx, 230 + Math.cos(a) * 21, 545 + Math.sin(a) * 21, 1.6, false); } });
      ctx.beginPath(); ctx.arc(230, 545, 37, -1.15, -0.25); ctx.arc(230, 545, 22, -0.25, -1.15, true); ctx.closePath(); bSF(ctx, hl);
    } },
    { a:[618, 585], b:[652, 668], hit:[bCirc(230, 545, 58), bCirc(650, 545, 58)], draw(ctx, hl){ bWheel(ctx, 230, 545, hl); bWheel(ctx, 650, 545, hl); } },
    { a:[404, 432], b:[430, 330], hit:[bRect(388, 402, 420, 462), bRect(240, 512, 288, 534)], draw(ctx, hl){
      ctx.save(); ctx.translate(404, 432); ctx.rotate(-0.38); ctx.beginPath(); ctx.ellipse(0, 0, 7, 24, 0, 0, Math.PI * 2); bSF(ctx, hl); ctx.restore();
      bDash(ctx, [8, 5], () => { bL(ctx, 406, 446, 268, 520); });
      bR(ctx, 244, 518, 282, 528, hl); bThin(ctx, 0.6, () => { for (let x = 248; x < 280; x += 4) bL(ctx, x, 518, x, 522); });
    } },
    { a:[540, 368], b:[560, 318], hit:[bPoly(CAR_BODY)], draw(ctx, hl){
      carBodyPath(ctx); bSF(ctx, hl);
      bThin(ctx, 0.7, () => {
        bP(ctx, [[346, 440], [430, 382], [602, 376], [698, 430]], true); ctx.stroke();
        bL(ctx, 515, 378, 515, 440); bL(ctx, 335, 446, 335, 548); bL(ctx, 515, 440, 515, 548); bL(ctx, 700, 430, 700, 548);
        bR(ctx, 470, 456, 492, 461, false); bR(ctx, 650, 452, 672, 457, false);
        bClip(ctx, () => { ctx.beginPath(); ctx.rect(112, 470, 62, 90); }, () => { carBodyPath(ctx); ctx.clip(); bHatch(ctx, 112, 470, 174, 560, 9); });
        bClip(ctx, () => { ctx.beginPath(); ctx.rect(752, 430, 58, 130); }, () => { carBodyPath(ctx); ctx.clip(); bHatch(ctx, 752, 430, 810, 560, 9); });
        bDash(ctx, [6, 4], () => { bP(ctx, [[340, 448], [428, 380], [606, 374], [690, 428], [690, 546], [340, 546]], true); ctx.stroke(); });
      });
      bTxt(ctx, 'CRUMPLE', 142, 450, 11); bTxt(ctx, 'ZONE', 142, 462, 11); bTxt(ctx, 'CRUMPLE ZONE', 780, 418, 11); bTxt(ctx, 'SAFETY CELL', 600, 500, 12);
    } }
  ]
};

/* ---------- 2. Excavator ---------- */
const EX_BOOM = [[462, 452], [400, 300], [280, 222], [296, 254], [438, 322], [486, 490]];
const BP_EXCAVATOR = {
  base(ctx){
    bL(ctx, 30, 600, 850, 600); bThin(ctx, 0.7, () => { for (let x = 34; x < 850; x += 16) bL(ctx, x, 600, x - 10, 611); });
    bThin(ctx, 0.8, () => { bP(ctx, [[36, 600], [62, 584], [96, 590], [124, 600]]); ctx.stroke(); });
    bDim(ctx, 390, 696, 760, 696, '4,450');
    bDash(ctx, [12, 4, 2, 4], () => { bThin(ctx, 0.6, () => { bL(ctx, 590, 300, 590, 560); }); });
    bTxt(ctx, 'SWING CENTER', 590, 290, 11, 'center', '400');
  },
  parts:[
    { a:[560, 597], b:[520, 664], hit:[bRect(388, 543, 762, 604)], draw(ctx, hl){
      rrect(ctx, 390, 545, 370, 55, 27); bSF(ctx, hl);
      bC(ctx, 733, 572, 22, false); bC(ctx, 417, 572, 21, false);
      bThin(ctx, 0.7, () => { for (let k = 0; k < 10; k++){ const a = k * Math.PI / 5; bL(ctx, 733 + Math.cos(a) * 22, 572 + Math.sin(a) * 22, 733 + Math.cos(a) * 26, 572 + Math.sin(a) * 26); } for (let x = 465; x <= 690; x += 45) bC(ctx, x, 589, 7, false); bC(ctx, 540, 553, 5, false); bC(ctx, 640, 553, 5, false); for (let x = 412; x < 740; x += 14) bL(ctx, x, 600, x, 605); });
    } },
    { a:[640, 537], b:[845, 610], hit:[bRect(516, 524, 666, 548)], draw(ctx, hl){
      bR(ctx, 520, 528, 662, 545, hl);
      bThin(ctx, 0.6, () => { for (let x = 524; x < 660; x += 8) bL(ctx, x, 528, x, 533); for (let x = 530; x < 660; x += 12) bC(ctx, x, 538.5, 3, false); });
    } },
    { a:[620, 474], b:[650, 362], hit:[bRect(466, 398, 776, 530)], draw(ctx, hl){
      bP(ctx, [[470, 528], [470, 442], [482, 430], [762, 430], [772, 444], [772, 528]], true); bSF(ctx, hl);
      bThin(ctx, 0.7, () => { bL(ctx, 600, 420, 760, 420); for (const x of [600, 680, 760]) bL(ctx, x, 420, x, 430); ctx.beginPath(); ctx.rect(650, 440, 92, 26); ctx.stroke(); for (let x = 656; x < 742; x += 7) bL(ctx, x, 442, x, 464); });
      bR(ctx, 700, 400, 710, 430, hl);
    } },
    { a:[530, 360], b:[560, 268], hit:[bRect(478, 314, 592, 434)], draw(ctx, hl){
      bP(ctx, [[482, 430], [482, 334], [500, 318], [576, 318], [588, 334], [588, 430]], true); bSF(ctx, hl);
      bThin(ctx, 0.7, () => { bP(ctx, [[492, 338], [504, 328], [572, 328], [580, 338], [580, 392], [492, 392]], true); ctx.stroke(); bL(ctx, 560, 338, 560, 428); bDash(ctx, [4, 3], () => { bP(ctx, [[512, 420], [512, 396], [540, 396]]); ctx.stroke(); }); bL(ctx, 548, 412, 548, 400); bC(ctx, 548, 397, 3, false); });
    } },
    { a:[795, 480], b:[845, 420], hit:[bPoly([[762, 434], [800, 438], [814, 468], [810, 522], [772, 528]])], draw(ctx, hl){
      bP(ctx, [[762, 434], [800, 438], [814, 468], [810, 522], [772, 528]], true); bSF(ctx, hl);
      bThin(ctx, 0.6, () => bClip(ctx, () => bP(ctx, [[762, 434], [800, 438], [814, 468], [810, 522], [772, 528]], true), () => bHatch(ctx, 760, 430, 816, 530, 8)));
    } },
    { a:[380, 300], b:[470, 232], hit:[bPoly(EX_BOOM)], draw(ctx, hl){
      ctx.beginPath(); ctx.moveTo(462, 452); ctx.quadraticCurveTo(408, 262, 280, 222); ctx.lineTo(296, 254); ctx.quadraticCurveTo(438, 300, 484, 490); ctx.closePath(); bSF(ctx, hl);
      bThin(ctx, 0.6, () => { bDash(ctx, [8, 5], () => { ctx.beginPath(); ctx.moveTo(472, 470); ctx.quadraticCurveTo(423, 282, 289, 238); ctx.stroke(); }); });
      bC(ctx, 472, 470, 8, false); bC(ctx, 289, 238, 8, false);
    } },
    { a:[218, 350], b:[120, 330], hit:[bPoly([[300, 192], [326, 204], [166, 478], [138, 468]])], draw(ctx, hl){
      bP(ctx, [[300, 192], [326, 204], [166, 478], [138, 468]], true); bSF(ctx, hl);
      bC(ctx, 150, 470, 7, false);
    } },
    { a:[132, 556], b:[60, 470], hit:[bPoly([[156, 462], [200, 520], [162, 580], [102, 592], [74, 590], [96, 568], [130, 512]])], draw(ctx, hl){
      ctx.beginPath(); ctx.moveTo(156, 462); ctx.quadraticCurveTo(200, 520, 162, 580); ctx.lineTo(102, 592); ctx.lineTo(82, 586); ctx.lineTo(96, 570); ctx.lineTo(130, 512); ctx.closePath(); bSF(ctx, hl);
      for (const dy of [0, 6]) { bP(ctx, [[86, 582 + dy * 0.3], [72, 589 + dy * 0.5], [90, 592]], true); bSF(ctx, hl); }
      bThin(ctx, 0.6, () => { ctx.beginPath(); ctx.moveTo(150, 478); ctx.quadraticCurveTo(178, 520, 152, 568); ctx.stroke(); });
    } },
    { a:[470, 420], b:[360, 470], hit:[bSeg(524, 502, 412, 330, 14)], draw(ctx, hl){ bCyl(ctx, 524, 502, 412, 330, 17, 0.55, hl); } },
    { a:[360, 236], b:[330, 140], hit:[bSeg(402, 270, 314, 200, 13)], draw(ctx, hl){ bCyl(ctx, 402, 270, 314, 200, 14, 0.55, hl); } },
    { a:[245, 345], b:[258, 470], hit:[bSeg(296, 262, 190, 430, 12), bRect(162, 424, 216, 496)], draw(ctx, hl){
      bCyl(ctx, 296, 262, 190, 430, 13, 0.55, hl);
      ctx.save(); ctx.lineWidth *= 1.8; bP(ctx, [[190, 430], [210, 470], [172, 490]]); ctx.stroke(); ctx.restore();
      bC(ctx, 210, 470, 5, false); bC(ctx, 172, 490, 5, false);
    } },
    { a:[700, 483], b:[770, 360], hit:[bRect(598, 442, 754, 524)], draw(ctx, hl){
      bDash(ctx, [6, 4], () => { ctx.beginPath(); ctx.rect(640, 446, 110, 74); bSF(ctx, hl); });
      bThin(ctx, 0.75, () => { ctx.beginPath(); ctx.rect(660, 456, 64, 54); ctx.stroke(); for (let i = 0; i < 4; i++) bC(ctx, 672 + i * 14, 466, 4, false); });
      bC(ctx, 620, 500, 13, hl); bThin(ctx, 0.7, () => bC(ctx, 620, 500, 5, false));
      bDash(ctx, [6, 4], () => { bThin(ctx, 0.8, () => { ctx.beginPath(); ctx.moveTo(607, 500); ctx.lineTo(530, 500); ctx.stroke(); ctx.beginPath(); ctx.moveTo(607, 494); ctx.quadraticCurveTo(470, 440, 420, 330); ctx.stroke(); }); });
      bTxt(ctx, 'ENGINE', 692, 492, 11); bTxt(ctx, 'PUMP', 620, 524, 10);
    } }
  ]
};

/* ---------- 3. House ---------- */
function houseStuds(ctx, x0, x1, y0, y1, openings){
  for (let x = x0; x <= x1; x += 26){ if (openings.some(([a, b]) => x + 5 > a - 8 && x < b + 8)) continue; ctx.beginPath(); ctx.rect(x, y0, 5, y1 - y0); ctx.stroke(); }
}
function houseOpening(ctx, a, b, top, bot, y0, y1, sill){
  /* King studs, jack studs, cripples above the header and below the sill */
  for (const x of [a - 13, b + 8]){ ctx.beginPath(); ctx.rect(x, y0, 5, y1 - y0); ctx.stroke(); }
  for (const x of [a - 7, b + 2]){ ctx.beginPath(); ctx.rect(x, top, 5, y1 - top); ctx.stroke(); }
  for (let x = a + 8; x < b - 4; x += 26){ if (top - 16 > y0 + 2){ ctx.beginPath(); ctx.rect(x, y0, 5, top - 16 - y0); ctx.stroke(); } if (sill){ ctx.beginPath(); ctx.rect(x, bot + 6, 5, y1 - bot - 6); ctx.stroke(); } }
  if (sill){ ctx.beginPath(); ctx.rect(a, bot, b - a, 6); ctx.stroke(); }
}
const HOUSE_TRUSS = [[100, 158], [444, 32], [788, 158]];
const BP_HOUSE = {
  base(ctx){
    bL(ctx, 40, 560, 136, 560); bL(ctx, 752, 560, 840, 560);
    bThin(ctx, 0.6, () => { bClip(ctx, () => { ctx.beginPath(); ctx.rect(40, 560, 96, 140); ctx.rect(752, 560, 88, 140); ctx.rect(166, 600, 556, 50); }, () => bHatch(ctx, 40, 560, 840, 700, 14)); });
    bL(ctx, 166, 600, 722, 600);
    bDash(ctx, [10, 6], () => { bThin(ctx, 0.7, () => bL(ctx, 40, 632, 840, 632)); });
    bTxt(ctx, 'FROST LINE', 470, 642, 11, 'center', '400'); bTxt(ctx, 'GRADE', 70, 551, 11, 'center', '400'); bTxt(ctx, 'CRAWLSPACE', 300, 588, 11, 'center', '400');
    bTxt(ctx, '16 IN O.C.', 444, 470, 11, 'center', '400');
  },
  parts:[
    { a:[151, 662], b:[80, 690], hit:[bRect(114, 648, 188, 676), bRect(700, 648, 774, 676)], draw(ctx, hl){
      for (const x of [116, 702]){ bR(ctx, x, 650, x + 70, 674, hl); bThin(ctx, 0.5, () => { for (let i = 0; i < 14; i++) bC(ctx, x + 6 + (i * 37) % 60, 655 + (i * 13) % 16, 1.4, false); }); }
    } },
    { a:[737, 600], b:[820, 620], hit:[bRect(134, 546, 168, 652), bRect(720, 546, 754, 652)], draw(ctx, hl){
      for (const x of [136, 722]){ bR(ctx, x, 548, x + 30, 650, hl); bThin(ctx, 0.5, () => bClip(ctx, () => { ctx.beginPath(); ctx.rect(x, 548, 30, 102); }, () => bHatch(ctx, x, 548, x + 30, 650, 9))); bC(ctx, x + 15, 600, 2.6, true); bC(ctx, x + 15, 630, 2.6, true); }
    } },
    { a:[151, 543], b:[70, 520], hit:[bRect(132, 532, 170, 550), bRect(718, 532, 756, 550)], draw(ctx, hl){
      for (const x of [136, 722]){ bR(ctx, x, 538, x + 30, 548, hl); bThin(ctx, 0.8, () => { bL(ctx, x + 15, 536, x + 15, 594); ctx.beginPath(); ctx.rect(x + 10, 533, 10, 5); ctx.stroke(); }); }
    } },
    { a:[400, 528], b:[440, 574], hit:[bRect(136, 510, 752, 540), bRect(140, 312, 748, 342)], draw(ctx, hl){
      for (const [y0, y1, y2, x0, x1] of [[512, 520, 538, 136, 752], [314, 320, 340, 140, 748]]){
        bR(ctx, x0, y0, x1, y1, hl); bR(ctx, x0, y1, x1, y2, hl);
        bThin(ctx, 0.55, () => { for (let x = x0 + 30; x < x1; x += 60) bL(ctx, x, y1, x, y2); });
      }
    } },
    { a:[197, 430], b:[90, 420], hit:[bRect(158, 352, 730, 504), bRect(158, 168, 730, 306)], draw(ctx, hl){
      bThin(ctx, 0.75, () => {
        houseStuds(ctx, 171, 717, 352, 504, [[214, 322], [458, 540], [594, 686]]);
        houseOpening(ctx, 220, 316, 392, 458, 352, 504, true); houseOpening(ctx, 470, 528, 372, 504, 352, 504, false); houseOpening(ctx, 600, 680, 392, 458, 352, 504, true);
        houseStuds(ctx, 171, 717, 168, 306, [[224, 316], [464, 556], [604, 696]]);
        houseOpening(ctx, 230, 310, 200, 262, 168, 306, true); houseOpening(ctx, 470, 550, 200, 262, 168, 306, true); houseOpening(ctx, 610, 690, 200, 262, 168, 306, true);
        ctx.beginPath(); ctx.rect(158, 504, 572, 8); ctx.stroke(); ctx.beginPath(); ctx.rect(158, 306, 572, 8); ctx.stroke();
      });
      for (const [x0, x1] of [[140, 158], [730, 748]]){ bR(ctx, x0, 352, x1, 504, hl); bR(ctx, x0, 168, x1, 306, hl); }
    } },
    { a:[268, 384], b:[268, 425], hit:[bRect(212, 374, 324, 394), bRect(462, 354, 536, 374), bRect(592, 374, 688, 394), bRect(222, 184, 318, 202), bRect(462, 184, 558, 202), bRect(602, 184, 698, 202)], draw(ctx, hl){
      for (const [a, b, y] of [[214, 322, 376], [464, 534, 356], [594, 686, 376], [224, 316, 186], [464, 556, 186], [604, 696, 186]]){ bR(ctx, a, y, b, y + 16, hl); bThin(ctx, 0.6, () => bL(ctx, a, y + 8, b, y + 8)); }
    } },
    { a:[444, 346], b:[520, 284], hit:[bRect(138, 338, 750, 354), bRect(138, 154, 750, 170)], draw(ctx, hl){
      for (const y of [340, 156]){ bR(ctx, 140, y, 748, y + 12, hl); bThin(ctx, 0.6, () => bL(ctx, 140, y + 6, 748, y + 6)); }
    } },
    { a:[330, 120], b:[250, 80], hit:[bPoly(HOUSE_TRUSS)], draw(ctx, hl){
      bR(ctx, 118, 150, 770, 156, hl);
      ctx.save(); ctx.lineWidth *= 2.2; bP(ctx, [[104, 158], [444, 36], [784, 158]]); ctx.stroke(); ctx.restore();
      bThin(ctx, 1.2, () => { bL(ctx, 330, 150, 274, 97); bL(ctx, 330, 150, 444, 40); bL(ctx, 558, 150, 444, 40); bL(ctx, 558, 150, 614, 97); });
      for (const [x, y] of [[330, 150], [558, 150], [444, 40], [274, 97], [614, 97]]){ ctx.beginPath(); ctx.rect(x - 6, y - 6, 12, 12); ctx.stroke(); }
    } },
    { a:[750, 250], b:[820, 250], hit:[bRect(128, 166, 142, 506), bRect(746, 166, 760, 506), bRect(600, 168, 730, 504)], draw(ctx, hl){
      bR(ctx, 134, 168, 140, 504, hl); bR(ctx, 748, 168, 754, 504, hl);
      bDash(ctx, [3, 3], () => { bL(ctx, 131, 168, 131, 504); bL(ctx, 757, 168, 757, 504); });
      bThin(ctx, 0.5, () => { const r = rnd(5); ctx.beginPath(); for (let i = 0; i < 260; i++){ const x = 604 + r() * 122, y = 172 + r() * 328; if ((y > 306 && y < 352) || (x > 596 && x < 690 && ((y > 374 && y < 466) || (y > 184 && y < 270)))) continue; const a = r() * Math.PI; ctx.moveTo(x, y); ctx.lineTo(x + Math.cos(a) * 9, y + Math.sin(a) * 9); } ctx.stroke(); ctx.beginPath(); ctx.rect(600, 168, 130, 138); ctx.rect(600, 352, 130, 152); ctx.stroke(); });
      bTxt(ctx, 'OSB', 666, 486, 11);
    } },
    { a:[149, 260], b:[70, 250], hit:[bRect(140, 168, 158, 504), bRect(730, 168, 748, 504), bRect(170, 126, 718, 150)], draw(ctx, hl){
      bThin(ctx, 0.7, () => { for (const x of [142, 732]){ bWavy(ctx, x, 170, x + 14, 302, true); bWavy(ctx, x, 354, x + 14, 502, true); } });
      bClip(ctx, () => { bP(ctx, [[112, 150], [444, 42], [776, 150]], true); }, () => { bThin(ctx, 0.7, () => { bWavy(ctx, 170, 132, 718, 149, false); bL(ctx, 170, 131, 718, 131); }); if (hl){ ctx.beginPath(); ctx.rect(170, 131, 548, 19); ctx.fill(); } });
    } },
    { a:[620, 90], b:[700, 50], hit:[bPoly([[96, 152], [444, 22], [792, 152], [784, 162], [444, 34], [104, 162]])], draw(ctx, hl){
      for (const s of [-1, 1]){
        const x0 = s < 0 ? 96 : 792, x1 = 444, y0 = 152, y1 = 24;
        bP(ctx, [[x0, y0], [x1, y1]]); ctx.stroke();
        bThin(ctx, 0.7, () => { const n = 22; for (let i = 1; i < n; i++){ const t = i / n, x = x0 + (x1 - x0) * t, y = y0 + (y1 - y0) * t; bL(ctx, x, y, x + s * 3, y + 7); } bP(ctx, [[x0 - s * 4, y0 + 6], [x1, y1 + 8]]); ctx.stroke(); });
      }
      if (hl){ bP(ctx, [[96, 152], [444, 22], [792, 152], [784, 160], [444, 34], [104, 160]], true); ctx.fill(); }
    } },
    { a:[776, 420], b:[822, 420], hit:[bRect(764, 150, 790, 670), bSeg(452, 18, 800, 146, 12)], draw(ctx, hl){
      ctx.save(); ctx.lineWidth *= 1.4; ctx.setLineDash([10, 7]);
      bArrow(ctx, 452, 18, 796, 146, 11); bArrow(ctx, 776, 172, 776, 652, 11); bArrow(ctx, 776, 652, 760, 668, 9); ctx.restore();
      for (const y of [260, 400, 540]) bArrow(ctx, 776, y - 30, 776, y, 10);
      bTxt(ctx, 'LOAD PATH', 812, 470, 11); bTxt(ctx, 'TO SOIL', 812, 690, 11);
    } }
  ]
};

/* ---------- 4. Bridge ---------- */
const BRX = (k) => 180 + 65 * k;
const BR_ABUT_L = [[110, 456], [170, 456], [170, 470], [196, 470], [196, 560], [110, 560]];
const BR_ABUT_R = [[770, 456], [710, 456], [710, 470], [684, 470], [684, 560], [770, 560]];
const BP_BRIDGE = {
  base(ctx){
    bP(ctx, [[30, 456], [110, 456]]); ctx.stroke(); bP(ctx, [[770, 456], [850, 456]]); ctx.stroke();
    bP(ctx, [[196, 560], [240, 592]]); ctx.stroke(); bP(ctx, [[684, 560], [640, 592]]); ctx.stroke();
    bThin(ctx, 0.7, () => { bP(ctx, [[240, 592], [262, 640], [618, 640], [640, 592]]); ctx.stroke(); for (let r = 0; r < 3; r++){ ctx.beginPath(); for (let x = 250 + r * 14; x < 630; x += 28){ ctx.moveTo(x, 600 + r * 12); ctx.quadraticCurveTo(x + 7, 595 + r * 12, x + 14, 600 + r * 12); } ctx.stroke(); } bL(ctx, 240, 592, 640, 592); });
    bThin(ctx, 0.55, () => { bClip(ctx, () => { bP(ctx, [[30, 456], [110, 456], [110, 560], [196, 560], [240, 592], [262, 640], [30, 640]], true); bP(ctx, [[850, 456], [770, 456], [770, 560], [684, 560], [640, 592], [618, 640], [850, 640]], true); }, () => bHatch(ctx, 30, 456, 850, 700, 14)); });
    bThin(ctx, 0.7, () => { bP(ctx, [[330, 436], [330, 404], [372, 404], [372, 396], [420, 396], [420, 436]], true); ctx.stroke(); bC(ctx, 345, 436, 6, false); bC(ctx, 405, 436, 6, false); });
    bDim(ctx, 180, 690, 700, 690, 'SPAN 52 M');
    bTxt(ctx, 'C = COMPRESSION   T = TENSION', 440, 668, 11, 'center', '400');
  },
  /* Force tags sit right on the members they describe */
  over(ctx){ for (const [t, x, y] of [['C', 407.5, 350], ['T', 602.5, 440], ['T', 537.5, 395], ['C', 310, 395]]) bTag(ctx, t, x, y); },
  parts:[
    { a:[480, 350], b:[480, 290], hit:[bRect(240, 340, 640, 360)], draw(ctx, hl){ bR(ctx, 245, 346, 635, 354, hl); } },
    { a:[600, 440], b:[600, 520], hit:[bRect(176, 432, 704, 448)], draw(ctx, hl){ bR(ctx, 180, 436, 700, 444, hl); } },
    { a:[342, 395], b:[330, 290], hit:[1, 2, 3].map((k) => bSeg(BRX(k), 350, BRX(k + 1), 440, 9)).concat([5, 6, 7].map((k) => bSeg(BRX(k), 350, BRX(k - 1), 440, 9))), draw(ctx, hl){
      ctx.save(); ctx.lineWidth *= 1.9; for (const k of [1, 2, 3]) bL(ctx, BRX(k), 354, BRX(k + 1), 436); for (const k of [5, 6, 7]) bL(ctx, BRX(k), 354, BRX(k - 1), 436); ctx.restore();
    } },
    { a:[570, 395], b:[640, 290], hit:[1, 2, 3, 4, 5, 6, 7].map((k) => bSeg(BRX(k), 354, BRX(k), 436, 8)), draw(ctx, hl){
      ctx.save(); ctx.lineWidth *= 1.9; for (let k = 1; k <= 7; k++) bL(ctx, BRX(k), 354, BRX(k), 436); ctx.restore();
    } },
    { a:[212, 395], b:[150, 330], hit:[bSeg(180, 440, 245, 350, 10), bSeg(700, 440, 635, 350, 10)], draw(ctx, hl){
      ctx.save(); ctx.lineWidth *= 2.6; bL(ctx, 180, 440, 245, 350); bL(ctx, 700, 440, 635, 350); ctx.restore();
    } },
    { a:[400, 450], b:[380, 520], hit:[bRect(176, 442, 704, 458), bRect(30, 442, 112, 458), bRect(768, 442, 850, 458)], draw(ctx, hl){
      bR(ctx, 176, 444, 704, 456, hl); bR(ctx, 30, 444, 110, 456, hl); bR(ctx, 770, 444, 850, 456, hl);
      bThin(ctx, 0.5, () => { for (let x = 184; x < 700; x += 16) bL(ctx, x, 445, x - 8, 455); });
    } },
    { a:[505, 461], b:[490, 560], hit:[bRect(176, 455, 704, 469)], draw(ctx, hl){
      for (let k = 0; k <= 8; k++) bR(ctx, BRX(k) - 4, 456, BRX(k) + 4, 466, hl);
      bDash(ctx, [6, 4], () => bL(ctx, 176, 461, 704, 461));
    } },
    { a:[180, 463], b:[110, 400], hit:[bRect(162, 452, 198, 478)], draw(ctx, hl){
      bP(ctx, [[180, 456], [169, 470], [191, 470]], true); bSF(ctx, hl); bC(ctx, 180, 460, 3, false); bR(ctx, 165, 470, 195, 473, hl);
    } },
    { a:[700, 464], b:[780, 400], hit:[bRect(682, 440, 718, 478)], draw(ctx, hl){
      bR(ctx, 688, 456, 712, 460, hl); bC(ctx, 694, 465, 4.5, hl); bC(ctx, 706, 465, 4.5, hl); bR(ctx, 684, 470, 716, 473, hl);
      bThin(ctx, 0.8, () => { bP(ctx, [[704, 444], [709, 448], [704, 452], [709, 456]]); ctx.stroke(); });
    } },
    { a:[728, 520], b:[800, 560], hit:[bPoly(BR_ABUT_L), bPoly(BR_ABUT_R)], draw(ctx, hl){
      for (const A of [BR_ABUT_L, BR_ABUT_R]){ bP(ctx, A, true); bSF(ctx, hl); bThin(ctx, 0.5, () => bClip(ctx, () => bP(ctx, A, true), () => bHatch(ctx, 100, 450, 780, 566, 10))); }
    } },
    { a:[310, 350], b:[250, 260], hit:[0, 1, 2, 3, 4, 5, 6, 7, 8].map((k) => bRect(BRX(k) - 9, 431, BRX(k) + 9, 449)).concat([1, 2, 3, 4, 5, 6, 7].map((k) => bRect(BRX(k) - 9, 341, BRX(k) + 9, 359))), draw(ctx, hl){
      for (let k = 0; k <= 8; k++) bR(ctx, BRX(k) - 7, 433, BRX(k) + 7, 447, hl);
      for (let k = 1; k <= 7; k++) bR(ctx, BRX(k) - 7, 343, BRX(k) + 7, 357, hl);
      bThin(ctx, 0.5, () => { for (let k = 1; k <= 7; k++) for (const [dx, dy] of [[-3, -3], [3, -3], [-3, 3], [3, 3]]) bC(ctx, BRX(k) + dx, 350 + dy, 1, false); });
    } },
    { a:[260, 428], b:[270, 520], hit:[bRect(176, 422, 704, 434)], draw(ctx, hl){
      bL(ctx, 176, 428, 704, 428); bThin(ctx, 0.6, () => { for (let x = 184; x < 704; x += 33) bL(ctx, x, 428, x, 436); });
      if (hl){ ctx.beginPath(); ctx.rect(176, 425, 528, 6); ctx.fill(); }
    } }
  ]
};

/* ---------- 5. Computer ---------- */
const BP_COMPUTER = {
  base(ctx){
    bDash(ctx, [8, 6], () => { ctx.beginPath(); ctx.rect(30, 20, 820, 680); ctx.stroke(); });
    bTxt(ctx, 'CASE · SIDE PANEL REMOVED', 440, 686, 11, 'center', '400'); bTxt(ctx, '← REAR', 70, 686, 11, 'center', '400'); bTxt(ctx, 'FRONT →', 800, 686, 11, 'center', '400');
    bThin(ctx, 0.6, () => { ctx.beginPath(); ctx.rect(110, 326, 380, 10); ctx.stroke(); });
  },
  parts:[
    { a:[345, 175], b:[660, 110], hit:[bRect(300, 130, 390, 220)], draw(ctx, hl){
      bThin(ctx, 0.7, () => { ctx.beginPath(); ctx.rect(300, 130, 90, 90); ctx.stroke(); });
      bR(ctx, 312, 142, 378, 208, hl); bP(ctx, [[314, 144], [324, 144], [314, 154]], true); ctx.stroke();
      bTxt(ctx, 'CPU', 345, 175, 14);
    } },
    { a:[405, 122], b:[660, 172], hit:[bCirc(345, 175, 66)], draw(ctx, hl){
      bDash(ctx, [8, 5], () => { ctx.beginPath(); ctx.rect(268, 98, 154, 154); ctx.stroke(); });
      if (hl){ ctx.beginPath(); ctx.arc(345, 175, 64, 0, Math.PI * 2); ctx.fill(); }
      bFan(ctx, 345, 175, 64, 7);
    } },
    { a:[486, 220], b:[660, 234], hit:[bRect(442, 86, 522, 334)], draw(ctx, hl){
      bThin(ctx, 0.6, () => { for (let i = 0; i < 4; i++){ ctx.beginPath(); ctx.rect(446 + i * 20, 90, 10, 240); ctx.stroke(); } });
      for (const i of [1, 3]){ const x = 446 + i * 20; bR(ctx, x - 2, 94, x + 12, 326, hl); bThin(ctx, 0.5, () => { for (let y = 104; y < 320; y += 28) { ctx.beginPath(); ctx.rect(x + 1, y, 8, 18); ctx.stroke(); } }); }
    } },
    { a:[574, 386], b:[660, 296], hit:[bRect(110, 70, 590, 470)], draw(ctx, hl){
      bR(ctx, 110, 70, 590, 470, hl);
      bThin(ctx, 0.6, () => { for (const [x, y] of [[126, 86], [574, 86], [126, 454], [574, 454], [126, 300], [574, 300], [400, 454]]) bC(ctx, x, y, 6, false); ctx.beginPath(); ctx.moveTo(390, 200); ctx.lineTo(430, 200); ctx.lineTo(440, 210); ctx.moveTo(390, 190); ctx.lineTo(436, 190); ctx.lineTo(446, 180); ctx.moveTo(400, 250); ctx.lineTo(420, 290); ctx.lineTo(420, 320); ctx.moveTo(300, 240); ctx.lineTo(260, 280); ctx.moveTo(520, 360); ctx.lineTo(560, 360); ctx.lineTo(560, 300); ctx.stroke(); });
    } },
    { a:[520, 351], b:[660, 404], hit:[bRect(90, 324, 624, 378)], draw(ctx, hl){
      bR(ctx, 100, 330, 620, 372, hl); bR(ctx, 92, 326, 104, 376, hl);
      bThin(ctx, 0.75, () => { bFan(ctx, 240, 351, 17, 5); bFan(ctx, 420, 351, 17, 5); bL(ctx, 520, 336, 600, 336); bL(ctx, 520, 366, 600, 366); });
      bTxt(ctx, 'GPU', 540, 351, 14);
    } },
    { a:[290, 296], b:[200, 520], hit:[bRect(196, 282, 400, 310)], draw(ctx, hl){
      bR(ctx, 200, 286, 382, 306, hl); bThin(ctx, 0.6, () => { ctx.beginPath(); ctx.rect(220, 290, 40, 12); ctx.rect(270, 290, 60, 12); ctx.stroke(); bC(ctx, 392, 296, 4, false); });
      bTxt(ctx, 'M.2', 352, 296, 10);
    } },
    { a:[715, 590], b:[560, 604], hit:[bRect(606, 516, 824, 664), bRect(550, 158, 578, 252), bRect(118, 76, 158, 96)], draw(ctx, hl){
      bR(ctx, 610, 520, 820, 660, hl); bFan(ctx, 715, 590, 44, 7);
      bThin(ctx, 0.5, () => { for (let r = 12; r < 44; r += 8) bC(ctx, 715, 590, r, false); });
      bR(ctx, 552, 160, 576, 250, hl); bR(ctx, 120, 78, 156, 94, hl);
      bThin(ctx, 0.6, () => { for (let y = 166; y < 248; y += 8) bL(ctx, 556, y, 572, y); });
      bDash(ctx, [6, 4], () => { bThin(ctx, 0.8, () => { ctx.beginPath(); ctx.moveTo(650, 520); ctx.bezierCurveTo(630, 400, 600, 300, 576, 206); ctx.stroke(); ctx.beginPath(); ctx.moveTo(700, 520); ctx.lineTo(620, 52); ctx.lineTo(138, 52); ctx.lineTo(138, 78); ctx.stroke(); }); });
      bTxt(ctx, 'PSU', 650, 640, 13);
    } },
    { a:[246, 176], b:[46, 176], hit:[bRect(228, 112, 264, 242), bRect(292, 94, 406, 120)], draw(ctx, hl){
      for (let i = 0; i < 6; i++) bR(ctx, 239, 122 + i * 19, 253, 136 + i * 19, hl);
      for (let i = 0; i < 5; i++) bR(ctx, 304 + i * 20, 100, 318 + i * 20, 114, hl);
      bThin(ctx, 0.6, () => { ctx.beginPath(); ctx.rect(231, 116, 30, 124); ctx.rect(298, 96, 104, 22); ctx.stroke(); });
    } },
    { a:[470, 410], b:[380, 520], hit:[bRect(436, 376, 504, 444)], draw(ctx, hl){
      bR(ctx, 440, 380, 500, 440, hl); bThin(ctx, 0.6, () => { for (let x = 446; x < 498; x += 8) bL(ctx, x, 384, x, 436); });
    } },
    { a:[808, 255], b:[808, 384], hit:[bCirc(808, 210, 34), bCirc(808, 300, 34), bCirc(62, 330, 28)], draw(ctx, hl){
      for (const [x, y, r] of [[808, 210, 32], [808, 300, 32], [62, 330, 26]]){ if (hl){ ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill(); } bFan(ctx, x, y, r, 6); }
      bThin(ctx, 0.9, () => { bArrow(ctx, 768, 210, 728, 210, 8); bArrow(ctx, 768, 300, 728, 300, 8); bArrow(ctx, 34, 330, 12, 330, 8); });
      bTxt(ctx, 'AIR IN', 748, 250, 11); bTxt(ctx, 'OUT', 62, 372, 11);
    } },
    { a:[540, 412], b:[520, 520], hit:[bCirc(540, 410, 17), bRect(524, 434, 552, 458)], draw(ctx, hl){
      bC(ctx, 540, 410, 15, hl); bThin(ctx, 0.6, () => bC(ctx, 540, 410, 10, false)); bTxt(ctx, '+', 540, 410, 12);
      bR(ctx, 526, 436, 550, 456, hl); bThin(ctx, 0.5, () => { for (let y = 438; y < 456; y += 4){ bL(ctx, 522, y, 526, y); bL(ctx, 550, y, 554, y); } });
    } },
    { a:[88, 176], b:[52, 52], hit:[bRect(68, 86, 108, 266)], draw(ctx, hl){
      bR(ctx, 72, 90, 104, 262, hl);
      bThin(ctx, 0.7, () => { for (let i = 0; i < 4; i++){ ctx.beginPath(); ctx.rect(78, 98 + i * 12, 20, 8); ctx.stroke(); } for (let i = 0; i < 3; i++) bC(ctx, 88, 160 + i * 12, 4.5, false); ctx.beginPath(); ctx.rect(78, 200, 20, 18); ctx.rect(80, 228, 16, 12); ctx.stroke(); });
    } }
  ]
};
const BP_GEO = { car:BP_CAR, excavator:BP_EXCAVATOR, house:BP_HOUSE, bridge:BP_BRIDGE, computer:BP_COMPUTER };

/* ---------- Drawing a whole sheet ---------- */
function bpBalloon(ctx, x, y, n, on){
  ctx.save(); ctx.shadowBlur = 0;
  ctx.beginPath(); ctx.arc(x, y, 19, 0, Math.PI * 2); ctx.fillStyle = on ? BPC.hi : BPC.ink; ctx.fill(); ctx.lineWidth = 2; ctx.strokeStyle = on ? BPC.hi : BPC.line; ctx.stroke();
  ctx.fillStyle = on ? '#1b2a33' : BPC.line; ctx.font = '700 19px ' + F.type; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(String(n), x, y + 1);
  ctx.restore();
}
function bpDrawing(ctx, id, sel){
  const G = BP_GEO[id];
  ctx.save(); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  ctx.strokeStyle = BPC.faint; ctx.fillStyle = BPC.faint; ctx.lineWidth = 1.6; G.base(ctx);
  G.parts.forEach((p, i) => {
    const on = sel === i, dim = sel != null && !on;
    ctx.save(); ctx.globalAlpha = dim ? 0.4 : 1;
    ctx.strokeStyle = on ? BPC.hi : BPC.line; ctx.fillStyle = on ? BPC.hiFill : 'rgba(0,0,0,0)'; ctx.lineWidth = on ? 3.1 : 2.1;
    if (on){ ctx.shadowColor = 'rgba(255,209,102,0.55)'; ctx.shadowBlur = 8; }
    p.draw(ctx, on); ctx.restore();
  });
  if (G.over){ ctx.save(); ctx.globalAlpha = sel != null ? 0.55 : 1; G.over(ctx); ctx.restore(); }
  G.parts.forEach((p, i) => {
    const on = sel === i, dx = p.a[0] - p.b[0], dy = p.a[1] - p.b[1], L = Math.hypot(dx, dy) || 1;
    ctx.save(); ctx.globalAlpha = sel != null && !on ? 0.55 : 1; ctx.strokeStyle = on ? BPC.hi : BPC.line; ctx.lineWidth = on ? 2 : 1.2;
    bL(ctx, p.b[0] + dx / L * 19, p.b[1] + dy / L * 19, p.a[0], p.a[1]);
    ctx.beginPath(); ctx.arc(p.a[0], p.a[1], on ? 4 : 3, 0, Math.PI * 2); ctx.fillStyle = on ? BPC.hi : BPC.line; ctx.fill();
    ctx.restore();
    bpBalloon(ctx, p.b[0], p.b[1], i + 1, on);
  });
  ctx.restore();
}
function bpPaper(ctx, W, H){
  const g = ctx.createLinearGradient(0, 0, W * 0.4, H); g.addColorStop(0, BPC.bg0); g.addColorStop(1, BPC.bg1);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.lineWidth = 1;
  for (let x = 0; x <= W; x += 20){ ctx.strokeStyle = x % 100 ? BPC.grid : BPC.grid2; ctx.beginPath(); ctx.moveTo(x + 0.5, 0); ctx.lineTo(x + 0.5, H); ctx.stroke(); }
  for (let y = 0; y <= H; y += 20){ ctx.strokeStyle = y % 100 ? BPC.grid : BPC.grid2; ctx.beginPath(); ctx.moveTo(0, y + 0.5); ctx.lineTo(W, y + 0.5); ctx.stroke(); }
}
/* The board on the classroom wall: drawing, parts list and a title block */
const BP_BOARD = { W:1280, H:800, ox:20, oy:64, lx:918 };
function drawBpBoard(id, sel, c){
  const { W, H, ox, oy, lx } = BP_BOARD, B = BP_INFO[id];
  c = c || mk(W, H); const ctx = c.getContext('2d');
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  bpPaper(ctx, W, H);
  ctx.strokeStyle = BPC.line; ctx.lineWidth = 3; ctx.strokeRect(10, 10, W - 20, H - 20); ctx.lineWidth = 1.2; ctx.strokeRect(17, 17, W - 34, H - 34);
  const tt = 'BLUEPRINT · ' + B.title.toUpperCase();
  ctx.fillStyle = BPC.line; ctx.font = '700 30px ' + F.type; ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic'; ctx.fillText(tt, 38, 52);
  const tw = ctx.measureText(tt).width;
  ctx.font = '400 17px ' + F.type; ctx.fillStyle = BPC.faint; ctx.fillText(B.sub.toUpperCase(), 38 + tw + 24, 50);
  ctx.save(); ctx.translate(ox, oy); bpDrawing(ctx, id, sel); ctx.restore();
  ctx.strokeStyle = BPC.line; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(lx - 14, 22); ctx.lineTo(lx - 14, H - 22); ctx.stroke();
  ctx.fillStyle = BPC.hi; ctx.font = '700 18px ' + F.type; ctx.fillText('PARTS', lx + 4, 60);
  B.parts.forEach((p, i) => {
    const y = 96 + i * 40, on = sel === i;
    if (on){ ctx.fillStyle = 'rgba(255,209,102,0.16)'; ctx.fillRect(lx - 4, y - 22, W - lx - 20, 36); }
    ctx.beginPath(); ctx.arc(lx + 16, y - 4, 13, 0, Math.PI * 2); ctx.fillStyle = on ? BPC.hi : BPC.ink; ctx.fill(); ctx.strokeStyle = on ? BPC.hi : BPC.line; ctx.lineWidth = 1.5; ctx.stroke();
    ctx.fillStyle = on ? '#1b2a33' : BPC.line; ctx.font = '700 14px ' + F.type; ctx.textAlign = 'center'; ctx.fillText(String(i + 1), lx + 16, y + 1);
    ctx.textAlign = 'left'; ctx.fillStyle = on ? BPC.hi : BPC.line; fit(ctx, p.name.toUpperCase(), F.type, '700', 17, W - lx - 70); ctx.fillText(p.name.toUpperCase(), lx + 40, y + 2);
  });
  const ty = 590;
  ctx.strokeStyle = BPC.line; ctx.lineWidth = 1.5; ctx.strokeRect(lx - 4, ty, W - lx - 18, H - ty - 26);
  for (const y of [ty + 44, ty + 88, ty + 132]){ ctx.beginPath(); ctx.moveTo(lx - 4, y); ctx.lineTo(W - 22, y); ctx.stroke(); }
  ctx.fillStyle = BPC.line; ctx.font = '700 15px ' + F.type; ctx.fillText('XRLIBRARIES CAMPUS · ROOM 103', lx + 6, ty + 28);
  ctx.font = '400 14px ' + F.type; fit(ctx, B.spec, F.type, '400', 14, W - lx - 40); ctx.fillText(B.spec, lx + 6, ty + 72);
  ctx.font = '400 14px ' + F.type; ctx.fillText('DWG ' + B.dwg + '   SCALE: NTS   SHEET 1 OF 1', lx + 6, ty + 116);
  ctx.fillStyle = BPC.hi; ctx.font = '700 15px ' + F.type; ctx.fillText(COARSE ? 'TAP A PART TO LEARN IT' : 'CLICK A PART TO LEARN IT', lx + 6, ty + 160);
  return c;
}
/* The drawing alone, for the full-screen viewer */
const BP_VIEW = { W:920, H:780, ox:20, oy:40 };
function drawBpView(c, id, sel){
  const { W, H, ox, oy } = BP_VIEW, ctx = c.getContext('2d');
  const k = Math.min(2, Math.max(1, window.devicePixelRatio || 1));
  if (c.width !== W * k){ c.width = W * k; c.height = H * k; }
  ctx.setTransform(k, 0, 0, k, 0, 0);
  bpPaper(ctx, W, H);
  ctx.save(); ctx.translate(ox, oy); bpDrawing(ctx, id, sel); ctx.restore();
}
/* Which part is at a point in drawing space */
function bpHit(id, x, y){
  const G = BP_GEO[id]; let best = null, ba = Infinity;
  G.parts.forEach((p, i) => { if (Math.hypot(x - p.b[0], y - p.b[1]) < 27 && ba > 0){ best = i; ba = 0; } });
  if (best != null) return best;
  const segD = (px, py, x0, y0, x1, y1) => { const dx = x1 - x0, dy = y1 - y0, t = clamp(((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy || 1), 0, 1); return Math.hypot(px - x0 - dx * t, py - y0 - dy * t); };
  G.parts.forEach((p, i) => {
    for (const h of p.hit){
      let inside = false, area = Infinity;
      if (h.r){ const [a, b, c, d] = h.r; inside = x >= a && x <= c && y >= b && y <= d; area = (c - a) * (d - b); }
      else if (h.c){ const [cx, cy, r] = h.c; inside = Math.hypot(x - cx, y - cy) <= r; area = Math.PI * r * r; }
      else if (h.s){ const [x0, y0, x1, y1, w] = h.s; inside = segD(x, y, x0, y0, x1, y1) <= w; area = Math.hypot(x1 - x0, y1 - y0) * w * 2; }
      else if (h.p){ inside = inPoly(x, y, h.p); let s = 0; for (let k = 0, j = h.p.length - 1; k < h.p.length; j = k++) s += (h.p[j][0] + h.p[k][0]) * (h.p[j][1] - h.p[k][1]); area = Math.abs(s / 2); }
      if (inside && area < ba){ ba = area; best = i; }
    }
  });
  return best;
}
