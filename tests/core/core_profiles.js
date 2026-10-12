const fs=require('fs');
const src=fs.readFileSync(require('path').join(__dirname, '..', '..', 'index.html'),'utf8');
const core=src.split('// === SIM-CORE-BEGIN ===')[1].split('// === SIM-CORE-END ===')[0];
eval(core+';global.createSim=createSim;global.DEG=DEG;');
for (const prof of ['px4','consumer']) {
const s=createSim(); s.axis='fly'; s.fmode='pos'; s.setProfile(prof); s.reset();
const f=v=>+v.toFixed(2); let maxTilt=0, os=0;
const run=(sec,st,tag)=>{Object.assign(s.sticks,st);for(let i=0;i<sec*1000;i++){s.step();maxTilt=Math.max(maxTilt,Math.abs(s.eul[0]),Math.abs(s.eul[1]));if(!Number.isFinite(s.pos[0]))throw 'NaN';} if(tag)console.log(prof.padEnd(9),tag.padEnd(14),'pos',s.pos.map(f),'v',s.vel.map(f),'yaw',f(s.eul[2]/DEG),'tilt',f(maxTilt/DEG));};
run(1.2,{thr:-1,yaw:1}); run(0.1,{yaw:0,thr:0});
run(1.0,{thr:1},'climb 1s'); run(3,{thr:0},'hold');
run(3,{pitch:1},'fwd 3s'); maxTilt=0;
let x0=s.pos[0]; run(5,{pitch:0},'release'); console.log('   stop dist', f(s.pos[0]-x0));
run(1.5,{yaw:1},'yaw 1.5s'); run(2,{yaw:0},'yaw stop');
run(2,{pitch:0.3},'small 0.3');
run(4,{pitch:0},'');
s.kickCh=4; s.kick=0.12; let mx=0; for(let i=0;i<5000;i++){s.step();mx=Math.max(mx,Math.abs(s.pos[1]-0));} console.log('   kick east max dev', f(mx), 'final E', f(s.pos[1]));
}
