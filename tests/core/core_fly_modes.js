const fs=require('fs');
const src=fs.readFileSync(require('path').join(__dirname, '..', '..', 'index.html'),'utf8');
const core=src.split('// === SIM-CORE-BEGIN ===')[1].split('// === SIM-CORE-END ===')[0];
eval(core+';global.createSim=createSim;global.DEG=DEG;');
const f=v=>+v.toFixed(2);
const s=createSim(); s.axis='fly'; s.focus='roll'; s.fmode='alt'; s.reset();
function run(sec, sticks, tag){ Object.assign(s.sticks, sticks); for(let i=0;i<sec*1000;i++) s.step();
  console.log(tag.padEnd(22), 'armed',s.armed,'landed',s.landed,'pos',s.pos.map(f),'vel',s.vel.map(f),'eul',s.eul.map(x=>f(x/DEG)),'msg',s.armMsg, s.crashed?'CRASH '+s.crashInfo:'', s.pos.every(Number.isFinite)?'':'NaN'); }
run(0.5,{thr:-1,yaw:0},'idle');
run(1.2,{thr:-1,yaw:1},'arm gesture');
run(0.5,{thr:-1,yaw:0},'armed idle');
run(3,{thr:0.5},'alt climb');
run(3,{thr:0},'alt hold');
s.fmode='pos';
run(3,{pitch:1},'pos fwd');
run(4,{pitch:0},'pos release');
run(2,{roll:1},'pos right');
run(4,{roll:0},'pos release2');
run(3,{yaw:1},'yaw spin');
run(2,{yaw:0},'yaw stop');
s.fmode='stab';
run(3,{thr:0},'stab center');
run(2,{roll:0.5},'stab roll');
run(2,{roll:0},'stab roll rel');
s.fmode='alt';
run(6,{thr:-1},'descend');
run(3,{thr:-1},'after land');
// crash test
const c=createSim(); c.axis='fly'; c.fmode='alt'; c.reset();
Object.assign(c.sticks,{thr:-1,yaw:1}); for(let i=0;i<1200;i++)c.step(); Object.assign(c.sticks,{yaw:0,thr:0.8}); for(let i=0;i<5000;i++)c.step();
console.log('h before cut', f(-c.pos[2])); c.fmode='stab'; c.sticks.thr=-1; for(let i=0;i<5000;i++)c.step();
console.log('crash', c.crashed, c.crashInfo, c.armed);
// acro test
const a=createSim(); a.axis='fly'; a.fmode='acro'; a.reset(); Object.assign(a.sticks,{thr:-1,yaw:1}); for(let i=0;i<1200;i++)a.step(); Object.assign(a.sticks,{yaw:0,thr:0.3}); for(let i=0;i<2000;i++)a.step();
a.sticks.roll=0.3; for(let i=0;i<500;i++)a.step(); a.sticks.roll=0; for(let i=0;i<500;i++)a.step();
console.log('acro', a.eul.map(x=>f(x/DEG)), 'h', f(-a.pos[2]), a.armed);
