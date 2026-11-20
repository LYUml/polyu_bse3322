/* Emit a design input to stdout; no solver is started by this generator.
   node generate_design.cjs OP soot curtainDepth_m totalFlow_m3s endTime_s
   flow=0 leaves the ceiling closed unless a final natural argument opens both vents. */
const fs = require('node:fs');
const path = require('node:path');
const [op,soot,depth,flow,end] = process.argv.slice(2).map(Number);
if (![1,6].includes(op) || ![0.02,0.05,0.1].includes(soot)
    || !Number.isFinite(depth) || depth<0 || depth>=0.38
    || !Number.isFinite(flow) || flow<0 || !(end>0)) throw Error('Invalid design parameters');
const natural = process.argv[7] === 'natural';
if (process.argv[7] && (!natural || flow!==0)) throw Error('Natural vent requires zero mechanical flow');
const id = [natural?'natural':'design',op,soot,depth,flow,end].join('_').replaceAll('.','p');
const base = fs.readFileSync(path.join(__dirname,'../03_Models/op1_106_coarse.fds'),'utf8');
let lines = base.split(/\r?\n/).filter(l => l && !l.startsWith('&HEAD') && !l.startsWith('&TIME')
  && !l.startsWith('&PROP') && !l.startsWith('&DEVC') && !l.startsWith('&TAIL')
  && (!l.startsWith('&HOLE') || op===1 || l.startsWith('&HOLE XB=3.91,4.34,')));
lines=lines.map(l=>l.startsWith('&REAC') ? "&REAC FUEL='PROPYLENE', SOOT_YIELD="+soot+", CO_YIELD=0.01 /" : l);
lines.unshift("&HEAD CHID='"+id+"', TITLE='Group 18 curtain and exhaust screening' /","&TIME T_END="+end+" /");
if(depth>0) {
  for(const x of [2.8,3.8]) lines.push('&OBST XB='+[x,x,0,0.9,(0.76-depth).toFixed(4),0.76].join(',')+' /');
}
if(natural) {
  for(const [side,x] of [['L',2.95],['R',3.35]]) {
    const x2=(x+0.3).toFixed(2);
    lines.push("&VENT XB="+[x,x2,0.3,0.6,0.76,0.76].join(',')+", SURF_ID='OPEN' /");
    // One face inside the domain to measure net upward transport beneath the vent.
    lines.push("&DEVC ID='roof"+side+"', XB="+[x,x2,0.3,0.6,0.72,0.72].join(',')+", QUANTITY='W-VELOCITY', SPATIAL_STATISTIC='AREA INTEGRAL' /");
  }
}
if(flow>0) {
  for(const [side,x] of [['L',2.95],['R',3.35]]) {
    lines.push("&VENT ID='vent"+side+"', XB="+[x,(x+0.3).toFixed(2),0.3,0.6,0.76,0.76].join(',')+", SURF_ID='HVAC' /",
      "&HVAC ID='in"+side+"', TYPE_ID='NODE', DUCT_ID='duct"+side+"', VENT_ID='vent"+side+"' /",
      "&HVAC ID='out"+side+"', TYPE_ID='NODE', DUCT_ID='duct"+side+"', AMBIENT=.TRUE., XYZ="+x+",0.45,1.16 /",
      "&HVAC ID='duct"+side+"', TYPE_ID='DUCT', NODE_ID='in"+side+"','out"+side+"', AREA=0.09, LENGTH=0.4, VOLUME_FLOW="+flow/2+" /",
      "&DEVC ID='flow"+side+"', DUCT_ID='duct"+side+"', QUANTITY='DUCT VOLUME FLOW' /");
  }
}
for(const x of [0.5,1.7,2.4,3,3.6,4.2,4.9,6.1]) {
  lines.push("&DEVC ID='layer"+x+"', XB="+[x,x,0.45,0.45,0,0.76].join(',')+", QUANTITY='LAYER HEIGHT' /");
  for(const [label,quantity,spec] of [['co','VOLUME FRACTION',", SPEC_ID='CARBON MONOXIDE'"],['vis','VISIBILITY','']])
    lines.push("&DEVC ID='"+label+x+"', XYZ="+x+",0.45,0.38, QUANTITY='"+quantity+"'"+spec+" /");
}
lines.push("&SLCF PBY=0.45, QUANTITY='EXTINCTION COEFFICIENT' /",'&TAIL /');
console.log(lines.join('\n'));
