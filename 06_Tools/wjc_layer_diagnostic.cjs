/* WJC single-mesh diagnostic: Temp slice, 203 x 40 x 32, upper room face k=23.
   Input argument: Task 2 directory. Output: diagnostic CSV on stdout.
   Use interior midpoint temperatures, avoiding floor and ceiling surface nodes. */
const fs = require('node:fs');
const path = require('node:path');
const rooms = {'no_curtain':'Smoke Extraction 1 but soot=0.1', curtain:'Smoke Extraction 1 but Fire curtain'};
console.log('case,time_s,x_m,height_m,vertical_range_K,status');
for (const [name,folder] of Object.entries(rooms)) {
  const data=fs.readFileSync(path.join(process.argv[2],folder,'BSE3322_Fire_CFD_Model_1_1.sf'));
  let offset=0;
  function record() {
    const n=data.readInt32LE(offset);
    if(n<0 || data.readInt32LE(offset+4+n)!==n) throw Error('Invalid Fortran record');
    const value=data.subarray(offset+4,offset+4+n);
    offset+=n+8;
    return value;
  }
  if(record().toString().trim()!=='TEMPERATURE') throw Error('Wrong quantity');
  record();
  if(record().toString().trim()!=='C') throw Error('Wrong units');
  const bounds=record();
  const indices=Array.from({length:6},(_,i)=>bounds.readInt32LE(4*i));
  if(indices.join(',')!=='0,203,14,14,0,32') throw Error('Unexpected grid');
  while(offset<data.length) {
    const time=record().readFloatLE();
    const frame=record();
    if(frame.length!==204*33*4) throw Error('Wrong frame size');
    if(time<50) continue;
    for(const location of [0.5,2.4,3.0,3.6,4.2,6.1]) {
      const i=Math.round(location*203/6.6);
      const temp=Array.from({length:22},(_,k)=>273.15+frame.readFloatLE(4*(i+204*(k+1))));
      const range=Math.max(...temp)-Math.min(...temp);
      // Extend the nearest interior sample to each wall using half-cell weights.
      const dz=1.06/32, H=23*dz, bottom=temp[0];
      let I=0,J=0;
      temp.forEach((v,k)=>{
        const w=(k===0 || k===21 ? 1.5:1)*dz;
        I+=v*w; J+=w/v;
      });
      const height=bottom*(I*J-H*H)/(I+J*bottom*bottom-2*bottom*H);
      const status=range<5?'weak_gradient':height>=0 && height<=H?'estimate':'invalid';
      console.log([name,time.toFixed(3),(i*6.6/203).toFixed(3),status==='estimate'?height.toFixed(4):'',range.toFixed(2),status].join(','));
    }
  }
}
