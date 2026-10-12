const fs=require('fs');
const src=fs.readFileSync(require('path').join(__dirname, '..', '..', 'index.html'),'utf8');
const core=src.split('// === SIM-CORE-BEGIN ===')[1].split('// === SIM-CORE-END ===')[0];
eval(core+';global.createSim=createSim;');
const s=createSim(); s.axis='fly'; s.fmode='pos'; s.reset();
const run=(ms,st)=>{Object.assign(s.sticks,st);for(let i=0;i<ms;i++){s.step(); if(!Number.isFinite(s.pos[2])){console.log('NaN at',s.t.toFixed(3),JSON.stringify([s.vel,s.w,s.Fcmd,s.tauCmd,s.ch.map(c=>c.inner),s.pc]));process.exit();}}};
run(1300,{thr:-1,yaw:1}); run(600,{thr:1,yaw:0}); run(4000,{thr:0}); console.log('ok',s.pos);
