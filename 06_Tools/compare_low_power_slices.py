"""Compare late mean fields on the two matched OP-1/OP-6 propane centreplane slices."""
import csv
import struct
from pathlib import Path

import numpy as np

from summarize_soot_continuity import record

ROOT = Path(__file__).resolve().parents[1]


def field(directory, index, quantity, metadata):
    path = directory / f'{directory.name}_1_{index}.sf'
    line = metadata.index(path.name)
    assert metadata[line-1].startswith('SLCF ') and metadata[line+1] == quantity
    times, frames = [], []
    with path.open('rb') as stream:
        assert record(stream).decode().strip() == quantity
        record(stream)
        unit = record(stream).decode().strip()
        assert unit == ('C' if index == 1 else 'm/s')
        assert struct.unpack('<6i', record(stream)) == (0,132,9,9,0,19)
        while stream.peek(1):
            times.append(struct.unpack('<f', record(stream))[0])
            frames.append(np.frombuffer(record(stream), '<f4').reshape(20,133))
    t = np.array(times)
    assert t[0] == 0 and t[-1] == 120 and np.allclose(np.diff(t), 1, atol=.03)
    # These are instantaneous output frames. Interpolate the lower endpoint and integrate.
    start = t.searchsorted(90)
    frames = np.asarray(frames, dtype=float)
    first = frames[start-1] + (frames[start]-frames[start-1])*(90-t[start-1])/(t[start]-t[start-1])
    v = np.concatenate(([first], frames[start:]))
    return np.tensordot(np.diff(np.r_[90,t[start:]])/30, (v[1:]+v[:-1])/2, axes=1)


def run():
    rows, profiles = [], []
    for op in (1,6):
        case = f'op{op}_47_coarse'
        directory = ROOT/'04_Results'/case
        metadata = [s.strip() for s in (directory/(case+'.smv')).read_text().splitlines()]
        for axis, expected in [('X', np.linspace(0,6.6,133)),('Y',np.linspace(0,1.4,29)),('Z',np.linspace(0,.76,20))]:
            i = metadata.index('TRN'+axis)+2
            assert np.allclose([float(line.split()[1]) for line in metadata[i:i+len(expected)]],expected)
        temp,u,v,w = [field(directory, i, name, metadata) for i,name in
                      enumerate(('TEMPERATURE','U-VELOCITY','V-VELOCITY','W-VELOCITY'),1)]
        for k in range(1,19):
            peak = temp[k].argmax()
            rows.append(dict(case=case,z_m=round(k*.04,2),y_m=.45,peak_offset_m=round((peak-66)*.05,2),
                             peak_rise_K=temp[k,peak]-27.5,axis_rise_K=temp[k,66]-27.5,
                             axis_u_m_s=u[k,66],axis_v_m_s=v[k,66],axis_w_m_s=w[k,66]))
        ref = ROOT/'05_Calculations'/(case+'_90_120.csv')
        with ref.open() as stream:
            for row in csv.DictReader(stream):
                x = float(row['model_x_cm'])/100
                # Experimental height is midway between exported z nodes .72 and .76.
                gas = np.interp(x,np.arange(133)*.05,(temp[18]+temp[19])/2)-27.5
                profiles.append(dict(case=case,x_m=x,estimated_slice_rise_at_074_K=gas,
                                     experiment_rise_K=row['exp_rise_K'],device_tc_rise_K=row['fds_rise_K']))
    for name, data in [('heights', rows),('ceiling',profiles)]:
        with (ROOT/'05_Calculations'/f'op1_op6_47_slice_{name}.csv').open('w',newline='') as f:
            wr = csv.DictWriter(f, fieldnames=data[0])
            wr.writeheader()
            wr.writerows(data)


if __name__ == '__main__':
    run()

