// 第 4 批：馬達效率、陀螺儀 / 加速度計誤差、姿態估測、懸停調參模式（hover）
// 每一項印出 PASS / FAIL 與實際數值；輸出需與 baseline 逐字相同（亂數有固定種子）
const fs = require('fs');
const src = fs.readFileSync(require('path').join(__dirname, '..', '..', 'index.html'), 'utf8');
const core = src.split('// === SIM-CORE-BEGIN ===')[1].split('// === SIM-CORE-END ===')[0];
eval(core + ';global.createSim=createSim;global.DEG=DEG;global.defaultSensors=defaultSensors;');
const f2 = (v) => +v.toFixed(2);
function mk(o = {}) {
  const s = createSim(); s.axis = 'hover'; s.fmode = o.fmode || 'alt'; s.reset();
  if (o.sens) Object.assign(s.sens, o.sens);
  if (o.eff) s.env.motorEff = o.eff;
  if (o.P) for (const a in o.P) Object.assign(s.params[a], o.P[a]);
  return s;
}
function run(s, sec, fn) { for (let i = 0; i < sec * 1000; i++) { s.step(); if (fn) fn(s, i); } }
function check(name, ok, info) { console.log((ok ? 'PASS ' : 'FAIL ') + name.padEnd(46) + JSON.stringify(info)); }
const real = defaultSensors('real'), noI = { roll: { MC_ROLLRATE_I: 0 }, pitch: { MC_PITCHRATE_I: 0 }, yaw: { MC_YAWRATE_I: 0 } };
const dist = (s) => f2(Math.hypot(s.pos[0], s.pos[1]));
const eul = (s) => s.eul.map((x) => f2(x / DEG));

{ const s = mk(); run(s, 5); check('理想懸停 5 s 不動', dist(s) < 1e-3 && Math.abs(2 + s.pos[2]) < 1e-3, { dist: dist(s), h: f2(-s.pos[2]) }); }
{ const a = mk({ eff: [0.9, 1, 1, 1] }); run(a, 8); const b = mk({ eff: [0.9, 1, 1, 1], P: noI }); run(b, 8);
  check('M1 90%：有 I 項 → 姿態拉回', Math.abs(a.eul[0]) < 0.3 * DEG && Math.abs(a.eul[1]) < 0.3 * DEG, { eul: eul(a), dist: dist(a) });
  check('M1 90%：I=0 → roll/pitch/yaw 固定偏角', Math.abs(b.eul[0] / DEG) > 0.8 && Math.abs(b.eul[1] / DEG) > 0.8 && Math.abs(b.eul[2] / DEG) > 1.5, { eul: eul(b) });
  check('M1 90%：I=0 → 越飄越遠', dist(b) > 4 * dist(a) && dist(b) > 3, { withI: dist(a), noI: dist(b) }); }
{ const s = mk({ fmode: 'stab', eff: [0.9, 1, 1, 1] }); run(s, 8); check('Stabilized + M1 90% → 推力不足掉高', -s.pos[2] < 1.5, { h: f2(-s.pos[2]) }); }
function kickMax(P) { const s = mk({ P }); run(s, 0.5); s.kickCh = 0; s.kick = 0.1; let m = 0; run(s, 4, (s) => { m = Math.max(m, Math.abs(s.eul[0] / DEG)); }); return f2(m); }
{ const d = kickMax({}), lo = kickMax({ roll: { MC_ROLLRATE_P: 0.04 } });
  check('內迴圈 P 太小 → 晃動大（推一下）', lo > 3 * d, { default: d, P004: lo }); }
function pwmJitter(o) { const s = mk(o); run(s, 1); let n = 0, a = 0, a2 = 0; run(s, 3, (s) => { const p = s.pwm[0]; a += p; a2 += p * p; n++; }); return f2(Math.sqrt(Math.max(0, a2 / n - (a / n) ** 2))); }
{ const ideal = pwmJitter({ P: { roll: { MC_ROLLRATE_D: 0.02 } } }), d0 = pwmJitter({ sens: real }), d1 = pwmJitter({ sens: real, P: { roll: { MC_ROLLRATE_D: 0.02 } } }), p1 = pwmJitter({ sens: real, P: { roll: { MC_ROLLRATE_P: 0.6 } } });
  check('理想感測器：D 再大也不抖', ideal < 0.5, { pwmStd: ideal });
  check('有雜訊：D 調大 → 馬達 PWM 抖動變大', d1 > 2.5 * d0, { D0003: d0, D002: d1 });
  check('有雜訊：P 調大 → 馬達 PWM 抖動變大', p1 > 1.3 * d0, { P015: d0, P06: p1 }); }
function estErr(o, sec, stick) { const s = mk(o); let se = 0, n = 0, mx = 0; run(s, sec, (s, i) => { if (stick && i === 3000) Object.assign(s.sticks, stick); if (stick && i === 5000) Object.assign(s.sticks, { roll: 0, pitch: 0 }); if (i > 1000) { const e = (s.ea[0] - s.eul[0]) / DEG; se += e * e; n++; mx = Math.max(mx, Math.abs(e)); } }); return { rms: f2(Math.sqrt(se / n)), max: f2(mx), crashed: s.crashed, bias: f2(s.kfBias(0)) }; }
const E = (x) => ({ ...real, est: true, ...x });
{ const g = estErr({ sens: E({ useAcc: false, gyroBias: 0.5 }) }, 20); check('只用陀螺儀 + 偏差 0.5°/s → 積分漂移', g.max > 5, g); }
{ const a = estErr({ sens: E({ useGyro: false }) }, 10); check('只用加速度計 → 估測角度帶雜訊', a.rms > 1.5, a); }
{ const a = estErr({ sens: E({ useGyro: false }) }, 10, { roll: 0.6 }); check('只用加速度計 + 推搖桿 → 估測失準', a.max > 20, a); }
{ const k = estErr({ sens: E({}) }, 15); check('Kalman（預設參數）懸停估測誤差小', k.rms < 1, k); }
{ const k = estErr({ sens: E({}) }, 10, { roll: 0.6 }); check('Kalman（預設參數）推搖桿仍可用', k.max < 6 && !k.crashed, k); }
{ const k = estErr({ sens: E({ kfR: 0.3 }) }, 10, { roll: 0.6 }); check('Kalman R 太小（太信加速度計）→ 推搖桿失準', k.max > 20, k); }
{ const s = mk({ sens: { ...real, accBias: 0.2 } }); run(s, 10); const t = mk({ sens: E({ accBias: 0.2 }) }); run(t, 10);
  check('加速度計偏差：估測關 → 不影響', dist(s) < 0.5, { dist: dist(s) });
  check('加速度計偏差：Kalman 開 → 把傾斜當水平、飄走', Math.abs(t.eul[0] / DEG) > 0.8 && dist(t) > 1, { dist: dist(t), roll: eul(t)[0] }); }
