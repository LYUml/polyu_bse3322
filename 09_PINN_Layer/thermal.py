"""Predict temperature columns from training designs, then apply a thermal layer readout."""
import csv
import struct
import sys

import numpy as np
from run import H, HERE, LIMIT, ROOT, X, case_data, features, forecast, score_events, write_rows

sys.path.insert(0, str(ROOT/'06_Tools'))
from summarize_soot_continuity import record

AMBIENT_K = 273.15 + 27.5


def read_columns(case, directory=None):
    path = (directory or ROOT/'04_Results'/case)/(case+'_1_1.sf')
    times, columns = [], []
    with path.open('rb') as f:
        quantity, _, units = [record(f).decode().strip() for _ in range(3)]
        bounds = struct.unpack('<6i', record(f))
        if (quantity, units) != ('TEMPERATURE', 'C') or bounds[:5] != (0,132,9,9,0) or bounds[5] not in (19,38):
            raise ValueError(f'Unexpected slice: {path}')
        while f.peek(1):
            times.append(struct.unpack('<f', record(f))[0])
            nodes = np.frombuffer(record(f), dtype='<f4').reshape(bounds[5]+1,133)
            station_nodes = nodes[:, np.rint(X/.05).astype(int)].T.astype(float)
            columns.append(.5*(station_nodes[:,1:]+station_nodes[:,:-1])+273.15)
    times, columns = np.array(times), np.array(columns)
    if (times[0] != 0 or abs(times[-1]-120)>.01 or np.any(np.diff(times)<=0)
            or np.max(np.diff(times))>1.1 or not np.all(np.isfinite(columns))):
        raise ValueError(f'Incomplete temperature slices: {path}')
    return times, columns


def layer_height(kelvin):
    """FDS 6.10.1 integral relation on uniform approximate cell temperatures."""
    if np.any(kelvin <= 0) or not np.all(np.isfinite(kelvin)):
        raise ValueError('Expected positive absolute temperatures')
    cells = kelvin.shape[-1]
    dz = H/cells
    base = kelvin[:,:,0]
    # Algebraically equivalent, with less cancellation when T is nearly uniform.
    diff = kelvin-base[:,:,None]
    denom = dz*np.sum(diff**2/kelvin, axis=2)
    numerator = base*dz**2*(np.sum(diff,axis=2)*np.sum(1/kelvin,axis=2)
                             - cells*np.sum(diff/kelvin,axis=2))
    z_int = np.clip(np.divide(numerator,denom,out=np.full_like(base,H),
                              where=denom>1e-12),0,H)
    previous = np.vstack([np.full((1,len(X)),H), z_int[:-1]])
    thickness = np.clip(dz*np.arange(1,cells+1)-previous[:,:,None],0,dz)
    upper = np.divide(np.sum(thickness*kelvin,axis=2),thickness.sum(axis=2),
                      out=base.copy(),where=thickness.sum(axis=2)>1e-12)
    return np.where(upper-base < 1,H,z_int)


def main():
    with (ROOT/'05_Calculations/layer_surrogate_holdouts.csv').open(encoding='utf-8-sig') as f:
        cases = [case_data(r) for r in csv.DictReader(f)]
    with (ROOT/'05_Calculations/tall_makeup_op6_completed_scenarios.csv').open(encoding='utf-8-sig') as f:
        extra, = [r for r in csv.DictReader(f) if r['case_id']=='tall_makeup_6_0p1_0p32_1p28_120']
    external = case_data(dict(layout='tall', depth_m=.32,flow_m3_s=1.28,soot_yield=.1,
                              fds_min_m=extra['min_layer_m']))
    for c in cases:
        t, columns = read_columns(c['name'])
        phi,_ = features(t,c['design'])
        c['temp_gram'] = phi.T@phi
        c['temp_rhs'] = phi.T@(columns-AMBIENT_K).reshape(len(t),-1)
    rows, diagnostics = [], []
    for c in [*cases,external]:
        train = [s for s in cases if s is not c and s['layout']==c['layout']]
        direct = forecast(train,c)['pinn']
        gram = sum(s['temp_gram'] for s in train)
        coef = np.linalg.solve(gram+.1*np.eye(len(gram)),sum(s['temp_rhs'] for s in train))
        temperatures = (c['phi']@coef).reshape(len(direct),len(X),19)+AMBIENT_K
        thermal = layer_height(temperatures)
        # Diagnostic only: compare observed slice reconstruction at nearly coincident samples.
        slice_t, observed = read_columns(c['name'])
        idx = np.abs(slice_t[:,None]-c['t']).argmin(axis=1)
        keep = np.abs(slice_t-c['t'][idx]) <= .05
        if not np.any(keep):
            raise ValueError('No coincident slice and device records')
        recon, reference = layer_height(observed)[keep], c['y'][idx[keep]]
        diagnostics.append(dict(case=c['name'], aligned_frames=int(keep.sum()),
                                mae_m=np.abs(recon-reference).mean(),
                                fds_low_points=int((reference<LIMIT).sum()),
                                coincident_low_points=int(((recon<LIMIT)&(reference<LIMIT)).sum()),
                                false_low_points=int(((recon<LIMIT)&(reference>=LIMIT)).sum())))
        for method,h in [('baseline',direct),('thermal',thermal),('hybrid',.5*(direct+thermal))]:
            y = c['y']
            rows.append(dict(case=c['name'], split='depth32' if c is external else c['layout'],
                             model=method, mae_m=np.abs(y-h).mean(), min_error_m=h.min()-y.min(),
                             false_pass=int(h.min()>=LIMIT>y.min()), **score_events(c['t'],y,h)))
    write_rows(HERE/'thermal_holdouts.csv',rows)
    write_rows(HERE/'thermal_slice_check.csv',diagnostics)


if __name__=='__main__':
    main()
