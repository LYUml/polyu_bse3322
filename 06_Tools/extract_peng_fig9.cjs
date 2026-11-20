/* Extract the vector marker centers from Poppler SVG of Peng PDF page 8.
   Calibration coordinates refer to the same page rendered 1600 pixels high. */
const fs = require('node:fs');
const svg = fs.readFileSync(process.argv[2], 'utf8');
const scale = 1600 / 793.700989;
const rows = [];
for (const line of svg.split('\n')) {
  if (!line.includes('stroke-linejoin="round"') || !line.includes(' Z M ')) continue;
  const op = line.includes('stroke="rgb(0%, 0%, 0%)"') ? 'OP-1' :
    line.includes('stroke="rgb(50.19989%, 0%, 0%)"') ? 'OP-6' : null;
  if (!op) continue;
  const vertices = [...line.matchAll(/[ML] ([-.\de+]+) ([-.\de+]+)/gi)].slice(0,op==='OP-1'?4:3);
  const transform = line.match(/matrix\(([^)]+)\)/);
  if (!transform || vertices.length < 3) continue;
  const [a,b,c,d,e,f] = transform[1].split(',').map(Number);
  const coords = vertices.map(v=>[Number(v[1]),Number(v[2])]);
  const mean = axis => coords.reduce((s,p)=>s+p[axis],0)/coords.length;
  const x = scale*(a*mean(0)+c*mean(1)+e);
  const y = scale*(b*mean(0)+d*mean(1)+f);
  const upper = y < 423;
  if (x < 685 || x > 1020 || y < 119 || y > 850) continue;
  if (upper ? x>897 && y<223 : y<540 || x>907 && y<649) continue;
  const r = upper ? (x-848.5)*800/376 : (x-854)*800/383;
  const dt = upper ? 400+(362-y)*300/243 : 400+(827-y)*600/266;
  if(Math.abs(r)>334) continue;
  rows.push([upper?47.2:106.2,op,r.toFixed(1),dt.toFixed(1)]);
}
rows.sort((a,b)=>a[0]-b[0]||a[1].localeCompare(b[1])||Number(a[2])-Number(b[2]));
console.log('hrr_kw,opening,r_cm,delta_T_K');
for(const row of rows) console.log(row.join(','));
