/* Generate controlled propane comparisons from the checked coarse baseline. */
const fs = require('node:fs');
const path = require('node:path');
const models = path.join(__dirname,'../03_Models');
const baseline = fs.readFileSync(path.join(models,'op1_106_coarse.fds'),'utf8');
const variants = [
  ['op1_47_coarse',47.2,1], ['op6_47_coarse',47.2,6], ['op6_106_coarse',106.2,6],
  ['op1_47_medium',47.2,1,'176,36,25'], ['op1_47_fine',47.2,1,'220,48,32'],
  ['op1_106_medium',106.2,1,'176,36,25'], ['op1_106_fine',106.2,1,'220,48,32'],
  ['op1_106_wale',106.2,1,null,'WALE'], ['op1_106_rad020',106.2,1,null,null,0.20],
  ['op1_106_rad050',106.2,1,null,null,0.50]
];
for (const [id,q,op,mesh,sgs,fraction] of variants) {
  let deck=baseline.replace("CHID='op1_106_coarse'", "CHID='"+id+"'")
    .replace('HRRPUA=1699.2','HRRPUA='+(q/0.0625).toFixed(1));
  if (op===6) deck=deck.split(/\r?\n/).filter(l=>!l.startsWith('&HOLE')||l.startsWith('&HOLE XB=3.91,4.34,')).join('\n');
  if (mesh) deck=deck.replace('IJK=132,28,19','IJK='+mesh);
  if (sgs) deck=deck.replace('TMPA=27.5',"TMPA=27.5, TURBULENCE_MODEL='"+sgs+"'");
  if (fraction) deck=deck.replace("FUEL='PROPANE'","FUEL='PROPANE', RADIATIVE_FRACTION="+fraction);
  if ((deck.match(/^&HOLE/gm)||[]).length!==(op===6?1:4) || (deck.match(/ID='TC_/g)||[]).length!==51)
    throw Error('Unexpected opening or thermocouple count: '+id);
  fs.writeFileSync(path.join(models,id+'.fds'),deck);
}
