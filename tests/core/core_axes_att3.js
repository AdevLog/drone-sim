const fs=require('fs');
const src=fs.readFileSync(require('path').join(__dirname, '..', '..', 'index.html'),'utf8');
const core=src.split('// === SIM-CORE-BEGIN ===')[1].split('// === SIM-CORE-END ===')[0];
eval(core+';global.createSim=createSim;global.stepMetrics=stepMetrics;global.DEG=DEG;');
const r1=v=>+v.toFixed(2);
function run(o){const s=createSim();Object.assign(s,o);if(o.P)for(const a in o.P)Object.assign(s.params[a],o.P[a]);s.reset();
 let hmin=9,hmax=0,pmax=0,sat=0;for(let i=0;i<(o.T||10)*1000;i++){s.step();if(s.t>2){const h=-s.pos[2];hmin=Math.min(hmin,h);hmax=Math.max(hmax,h);pmax=Math.max(pmax,Math.abs(s.eul[1]/DEG));if(s.sat.some(x=>x))sat++;}}
 const m=stepMetrics(s.segs[s.segs.length-1]);
 console.log(o.tag, m&&{rise:m.rise&&r1(m.rise),os:r1(m.overshoot),settle:m.settle&&r1(m.settle)}, 'eul',s.eul.map(x=>r1(x/DEG)),'h',r1(hmin)+'..'+r1(hmax),'pitchMax',r1(pmax),'satms',sat, s.eul.every(Number.isFinite)?'':'NaN');}
run({tag:'roll single',axis:'roll',focus:'roll'});
run({tag:'yaw single',axis:'yaw',focus:'yaw',amp:30,period:6,T:14});
run({tag:'thr single',axis:'thr',focus:'thr',amp:1,period:10,T:22});
run({tag:'att3 roll sq, alt hold',axis:'att3',waveAxis:'roll',amp:15});
run({tag:'att3 + tiltcomp',axis:'att3',waveAxis:'roll',amp:15,tiltComp:true});
run({tag:'att3 no althold',axis:'att3',waveAxis:'roll',amp:15,altHold:false,T:6});
run({tag:'att3 roll30 yaw90',axis:'att3',waveAxis:'roll',amp:30,manual:[0,0,90],T:10});
run({tag:'att3 yaw sq 90 roll man 30',axis:'att3',waveAxis:'yaw',amp:90,period:8,manual:[30,0,0],T:14});
run({tag:'att3 roll40 yaw sq90 sat',axis:'att3',waveAxis:'yaw',amp:90,period:8,manual:[40,0,0],T:14});
run({tag:'att3 acro',axis:'att3',cascade:false,waveAxis:'roll',amp:90,T:8});
run({tag:'att3 acro pitch flip',axis:'att3',cascade:false,waveAxis:'pitch',amp:300,T:8});
run({tag:'att3 roll30 althold',axis:'att3',waveAxis:'roll',amp:30});
run({tag:'att3 roll30 althold tilt',axis:'att3',waveAxis:'roll',amp:30,tiltComp:true});
run({tag:'att3 roll30 althold noFF',axis:'att3',waveAxis:'roll',amp:30,ff:false});
