"""Matched OP-1 exterior sensitivity; device windows and projected mean flow paths."""
import csv
import io
import json
import struct
import subprocess
from pathlib import Path

import numpy as np

from summarize_soot_continuity import record

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / '05_Calculations'
BASE, WIDE = 'op1_47_doorflow', 'op1_47_outer185'
DOORS = ('L2', 'L1', 'R1', 'R2')


def save(name, rows):
    with (OUTPUT / f'{WIDE}_{name}.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)


def device_comparison():
    flows, profiles = [], []
    for lo, hi in [(90,105),(105,120),(90,120)]:
        for case in (BASE, WIDE):
            result = subprocess.run(['node', str(ROOT/'06_Tools/compare_propane.cjs'),
                                     str(ROOT/'04_Results'/case), str(lo), str(hi)],
                                    capture_output=True, text=True, check=True)
            meta = json.loads(result.stderr)
            stations = list(csv.DictReader(io.StringIO(result.stdout)))
            errors = np.array([float(s['error_K']) for s in stations])
            x = np.array([int(s['sensor_x_cm']) for s in stations])
            row = dict(case=case, start_s=lo, end_s=hi, hrr_kW=meta['mean_HRR_kW'],
                       rmse_K=meta['RMSE_K'], bias_K=meta['mean_signed_error_K'],
                       peak_K=meta['modelPeak']['rise_K'], peak_r_cm=meta['modelPeak']['r_cm'])
            for zone, mask in [('left',x<230),('centre',(x>=230)&(x<=430)),('right',x>430)]:
                row[zone+'_bias_K'] = errors[mask].mean()
            profiles.append(row)
            if case == WIDE and (lo,hi) == (90,120):
                save('stations', stations)
            for door, values in meta['mean_door_flow_kg_s'].items():
                flows.append(dict(case=case,start_s=lo,end_s=hi,door=door,**values))
    save('profiles', profiles)
    save('flows', flows)


def slice_mean(index, quantity, metadata):
    folder = ROOT/'04_Results'/WIDE
    path = folder/f'{WIDE}_1_{index}.sf'
    i = metadata.index(path.name)
    assert metadata[i-1].startswith('SLCF') and metadata[i+1] == quantity
    t, frames = [], []
    with path.open('rb') as stream:
        assert record(stream).decode().strip() == quantity
        record(stream)
        record(stream)
        x0,x1,y0,y1,z0,z1 = struct.unpack('<6i',record(stream))
        assert (x0,y0,y1,z0,z1)==(x1,0,74,0,23)
        while stream.peek(1):
            t.append(struct.unpack('<f',record(stream))[0])
            frames.append(np.frombuffer(record(stream),'<f4').reshape(24,75))
    t = np.array(t)
    frames = np.array(frames, dtype=float)
    assert np.isfinite(frames).all() and t[0]==0 and t[-1]==120 and np.allclose(np.diff(t),1,atol=.03)
    k = t.searchsorted(90)
    first = frames[k-1]+(frames[k]-frames[k-1])*(90-t[k-1])/(t[k]-t[k-1])
    data = np.concatenate(([first],frames[k:]))
    weights = np.diff(np.r_[90,t[k:]])
    return x0*6.6/154, np.tensordot(weights/30,(data[:-1]+data[1:])/2,axes=1)


def projected_paths(v,w):
    dy,dz = .025,.76/23
    def interp(a,y,z):
        j,k = int(y/dy),int(z/dz)
        f,g = y/dy-j,z/dz-k
        return ((1-g)*((1-f)*a[k,j]+f*a[k,j+1])+
                g*((1-f)*a[k+1,j]+f*a[k+1,j+1]))
    far = returned = reverse = 0
    max_y = .975
    for z0 in np.arange(.035,.626,.005):
        y,z = .975,z0
        if interp(v,y,z)<=0:
            continue
        reached = turned = False
        for _ in range(5000):
            vy,vz = interp(v,y,z),interp(w,y,z)
            speed=np.hypot(vy,vz)
            if speed<.005:
                break
            if reached and vy<-.02:
                turned=True
            y += .0025*vy/speed
            z += .0025*vz/speed
            max_y=max(y,max_y)
            reached |= y>1.4
            if y<=.95:
                returned += int(reached and z<.63 and z>0)
                break
            if y>=1.85 or z<=0 or z>=.76:
                break
        far += int(reached)
        reverse += int(turned)
    return far,reverse,returned,max_y


def exterior():
    metadata=[s.strip() for s in (ROOT/'04_Results'/WIDE/(WIDE+'.smv')).read_text().splitlines()]
    rows, nodes = [], []
    for n,door in enumerate(DOORS):
        parts=[slice_mean(9+4*n+j,q,metadata) for j,q in
               enumerate(('TEMPERATURE','U-VELOCITY','V-VELOCITY','W-VELOCITY'))]
        x = parts[0][0]
        temp,u,v,w = [a for _,a in parts]
        far,turn,ret,max_y = projected_paths(v,w)
        # Exclude floor, roof and OPEN boundary nodes from extrema.
        region=np.s_[1:-1,57:74]
        vr=v[region]
        negative=vr<-.02
        rows.append(dict(door=door,x_m=x,min_mean_v_m_s=vr.min(),max_mean_v_m_s=vr.max(),
                         n_inward_nodes=int(negative.sum()),n_nodes=vr.size,
                         warmest_mean_inward_rise_K=(temp[region][negative]-27.5).max() if negative.any() else None,
                         outward_seeds_beyond_old=far,turn_inward_after_crossing=turn,
                         projected_returns_to_door=ret,max_projected_y_m=max_y))
        for k in range(1,23):
            for j in (38,48,56,60,64,68,72):
                nodes.append(dict(door=door,x_m=x,y_m=j*.025,z_m=k*.76/23,
                                  temperature_C=temp[k,j],u_m_s=u[k,j],v_m_s=v[k,j],w_m_s=w[k,j]))
    save('exterior',rows)
    save('sections',nodes)


if __name__=='__main__':
    device_comparison()
    exterior()
