/* Usage: node summarize_design.cjs CASE_DIRECTORY [start_s=0].
   Entire observed fire is used for the design threshold; an optional later
   window is a diagnostic only. Refuses truncated or unsuccessful runs. */
const fs = require('node:fs');
const path = require('node:path');
const [dir, startArg='0'] = process.argv.slice(2);
const start=Number(startArg);
const files=fs.readdirSync(dir);
const resultFile=files.find(f=>f.endsWith('_devc.csv'));
const id=resultFile?.slice(0,-9);
if(!id || !Number.isFinite(start) || start<0) throw Error('Invalid case or start time');
const out=fs.readFileSync(path.join(dir,id+'.out'),'utf8');
if(!out.includes('FDS completed successfully')) throw Error('Case has not completed successfully');
const input=fs.readFileSync(path.join(dir,files.find(f=>f.endsWith('.fds'))),'utf8');
const end=Number(input.match(/T_END\s*=\s*([\d.]+)/i)?.[1]);
const [unitLine,nameLine,...data]=fs.readFileSync(path.join(dir,resultFile),'utf8').trim().split(/\r?\n/);
const names=nameLine.replaceAll('"','').split(',');
const units=unitLine.split(',');
const rows=data.map(l=>l.split(',').map(Number));
if(rows.some((r,i)=>r.length!==names.length || r.some(v=>!Number.isFinite(v)) || (i && r[0]<=rows[i-1][0]))) throw Error('Invalid time series');
if(!Number.isFinite(end) || Math.abs(rows.at(-1)[0]-end)>0.001 || rows[0][0]>start || start>=end) throw Error('Incomplete requested interval');
function column(name,unit) {
  const j=names.indexOf(name);
  if(j<0 || units[j]!==unit) throw Error('Missing column or unexpected unit: '+name);
  return j;
}
const interpolate=(a,b,t)=>a.map((v,i)=>v+(b[i]-v)*(t-a[0])/(b[0]-a[0]));
const next=rows.findIndex(r=>r[0]>=start);
const window=rows.slice(next);
if(window[0][0]>start) window.unshift(interpolate(rows[next-1],rows[next],start));
const layers=names.filter(n=>n.startsWith('layer'));
if(layers.length!==8) throw Error('Expected eight layer columns');
const threshold=0.38;
console.log('case,x_m,start_s,end_s,min_height_m,time_at_min_s,first_below_s,below_duration_s,max_co_ppm,min_visibility_m,mean_mechanical_exhaust_m3_s,mean_net_flow_below_roof_vents_m3_s,time_at_max_co_s,time_at_min_visibility_s');
const flow=names.filter(n=>/^flow(L|R|C1|C2)$/.test(n)).map(n=>column(n,'m3/s'));
if(flow.length!==((input.match(/TYPE_ID='DUCT'/g)||[]).length)) throw Error('Unexpected duct count');
const roof=names.filter(n=>/^roof[LR]$/.test(n)).map(n=>column(n,'m3/s'));
if (id.startsWith('natural_') && roof.length!==2) throw Error('Missing roof flux readings');
const total=r=>flow.reduce((s,j)=>s+r[j],0);
let roofVolume=0;
for(let i=1;i<window.length;i++){
  const dt=window[i][0]-window[i-1][0];
  for(const j of roof) roofVolume+=(window[i][j]+window[i-1][j])*0.5*dt;
}
let volume=0;
for(let i=1;i<window.length;i++) volume+=(total(window[i])+total(window[i-1]))*0.5*(window[i][0]-window[i-1][0]);
const belowIntervals=[];
for(const name of layers){
  const x=name.slice(5), j=column(name,'m'), co=column('co'+x,'mol/mol'), vis=column('vis'+x,'m');
  let min=window[0],maxCO=window[0],minVis=window[0],first=null,duration=0;
  for(let i=1;i<window.length;i++){
    const a=window[i-1],b=window[i];
    if(b[j]<min[j]) min=b;
    if(b[co]>maxCO[co]) maxCO=b;
    if(b[vis]<minVis[vis]) minVis=b;
    const lowA=a[j]<threshold,lowB=b[j]<threshold;
    if(!lowA && !lowB) continue;
    const crossing=lowA===lowB ? a[0] : a[0]+(threshold-a[j])*(b[0]-a[0])/(b[j]-a[j]);
    const from=lowA?a[0]:crossing, to=lowB?b[0]:crossing;
    first??=from;
    duration+=to-from;
    belowIntervals.push([from,to]);
  }
  console.log([id,x,start,end,min[j],min[0],first?.toFixed(3)??'',duration.toFixed(3),maxCO[co]*1e6,minVis[vis],(volume/(end-start)).toFixed(5),roof.length?(roofVolume/(end-start)).toFixed(5):'',maxCO[0],minVis[0]].join(','));
}
// Merge overlapping excursions so simultaneous violations count only once.
belowIntervals.sort((a,b)=>a[0]-b[0]);
let coveredUntil=start, anyBelow=0;
for(const [from,to] of belowIntervals){
  anyBelow+=Math.max(0,to-Math.max(from,coveredUntil));
  coveredUntil=Math.max(coveredUntil,to);
}
console.error(JSON.stringify({case:id,start_s:start,end_s:end,any_station_below_duration_s:anyBelow}));
