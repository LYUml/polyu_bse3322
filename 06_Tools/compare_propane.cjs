/* Time-weighted comparison of an actual FDS output interval to Peng Fig. 9.
   node compare_propane.cjs CASE_DIRECTORY START END [--diagnostic]
   CSV stdout, metadata and metrics stderr. Neither metric implies acceptance. */
const fs=require('node:fs');
const path=require('node:path');
const [dir,from,to,mode]=process.argv.slice(2);
const start=Number(from), end=Number(to), mid=(start+end)/2;
if(!(end>start && start>=0)) throw Error('Invalid analysis interval');
const id=path.basename(path.resolve(dir));
const match=id.match(/^op([16])_(47|106)_/);
if(!match) throw Error('Unrecognised case');
const q=match[2]==='47'?47.2:106.2;
const file=ext=>path.join(dir,id+ext);
if(mode!=='--diagnostic' && !fs.readFileSync(file('.out'),'utf8').includes('FDS completed successfully')) throw Error('Incomplete run');
function series(ext) {
  const [units,headers,...rows]=fs.readFileSync(file(ext),'utf8').trim().split(/\r?\n/);
  const names=headers.replaceAll('"','').split(',');
  const values=rows.map(r=>r.split(',').map(value=>value.trim()==='' ? NaN : Number(value)));
  if(values[0][0]>start || values.at(-1)[0]<end-1e-5) throw Error('Requested interval unavailable');
  if(values.some((r,i)=>r.length!==names.length || r.some(v=>!Number.isFinite(v)) || (i && r[0]<=values[i-1][0]))) throw Error('Invalid data');
  return (name,unit,lo=start,hi=end)=>{
    const col=names.indexOf(name);
    if(col<0 || units.split(',')[col]!==unit) throw Error('Unexpected column '+name);
    let sum=0;
    for(let i=1;i<values.length;i++){
      const a=values[i-1],b=values[i], l=Math.max(lo,a[0]), h=Math.min(hi,b[0]);
      if(h<=l) continue;
      const slope=(b[col]-a[col])/(b[0]-a[0]);
      sum+=(h-l)*(a[col]+slope*((l+h)/2-a[0]));
    }
    return sum/(hi-lo);
  };
}
const avg=series('_devc.csv'), heat=series('_hrr.csv');
const ref=fs.readFileSync(path.join(__dirname,'../05_Calculations/peng_fig9.csv'),'utf8').trim().split(/\r?\n/).slice(1).map(l=>l.split(',')).filter(r=>Number(r[0])===q && r[1]==='OP-'+match[1]);
if(ref.length!==51) throw Error('Expected 51 experiment points');
const deck=fs.readFileSync(file('.fds'),'utf8');
const ambient=Number(deck.match(/TMPA=([\d.]+)/)[1]);
const sensorPositions=new Map(Array.from(deck.matchAll(/&DEVC\s+ID='(TC_\d+)'[^/]*?\bXYZ=([\d.]+),/g),
  ([,name,xMetres])=>[name,Number(xMetres)*100]));
let experimentPeak, modelPeak;
let signedError=0,abs=0,sq=0,worstDrift=0;
console.log('sensor_x_cm,figure_r_cm,exp_rise_K,fds_rise_K,error_K,second_minus_first_half_K,model_x_cm');
ref.forEach((r,i)=>{
  const x=i<8?30*i:240+10*(i-8), tc='TC_'+x;
  if(!sensorPositions.has(tc)) throw Error('Missing model coordinate for '+tc);
  // Reference coordinates are digitized to 0.1 cm. Allow 0.5 cm for plot registration.
  if(Math.abs(Number(r[2])-(x-330))>0.5) throw Error('Station mismatch');
  const rise=avg(tc,'C')-ambient, error=rise-Number(r[3]);
  if(!experimentPeak || Number(r[3])>experimentPeak.rise_K) experimentPeak={rise_K:Number(r[3]),r_cm:Number(r[2])};
  if(!modelPeak || rise>modelPeak.rise_K) modelPeak={rise_K:rise,r_cm:sensorPositions.get(tc)-330};
  const drift=avg(tc,'C',mid,end)-avg(tc,'C',start,mid);
  signedError+=error;
  abs+=Math.abs(error); sq+=error*error; worstDrift=Math.max(worstDrift,Math.abs(drift));
  console.log([x,r[2],r[3],rise.toFixed(2),error.toFixed(2),drift.toFixed(2),sensorPositions.get(tc).toFixed(3)].join(','));
});
const budgetTerms=['Q_RADI','Q_CONV','Q_COND','Q_DIFF','Q_PRES','Q_PART','Q_ENTH','Q_TOTAL'];
const mean_domain_budget_kW=Object.fromEntries(budgetTerms.map(name=>[name,heat(name,'kW')]));
let mean_door_flow_kg_s;
if(id.endsWith('_doorflow')){
  const doors=match[1]==='1'?['L2','L1','R1','R2']:['R1'];
  mean_door_flow_kg_s={};
  for(const door of doors){
    const outward=avg(door+'_out','kg/s'), inward=-avg(door+'_in','kg/s');
    mean_door_flow_kg_s[door]={outward,inward,net_outward:outward-inward};
  }
}
console.error(JSON.stringify({id,diagnostic:mode==='--diagnostic',start,end,mean_HRR_kW:heat('HRR','kW'),mean_domain_budget_kW,mean_door_flow_kg_s,experimentPeak,modelPeak,mean_signed_error_K:signedError/ref.length,MAE_K:abs/51,RMSE_K:Math.sqrt(sq/51),max_half_window_drift_K:worstDrift}));
