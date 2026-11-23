"""Analyse the OP-1 diagnostic alongside the original four-door baseline."""
import csv
import json
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / '05_Calculations'
CASE = 'op1_47_plume_diag'
BASE = 'op1_47_coarse'


def devices(case):
    with (ROOT / '04_Results' / case / (case + '_devc.csv')).open() as stream:
        reader = csv.reader(stream)
        next(reader)
        names = next(reader)
        values = np.array(list(reader), dtype=float)
    assert np.isfinite(values).all() and np.all(np.diff(values[:, 0]) > 0)
    return names, values


def averages(series, lo, hi):
    names, values = series
    t = values[:, 0]
    widths = np.maximum(0, np.minimum(t[1:], hi) - np.maximum(t[:-1], lo))
    assert np.isclose(widths.sum(), hi - lo) and np.diff(t).max() < .76
    return dict(zip(names, widths @ values[1:] / (hi - lo)))


def write_csv(name, rows):
    with (RESULTS / (CASE + '_' + name + '.csv')).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)


def run():
    out = subprocess.run(['node', str(ROOT / '06_Tools/compare_propane.cjs'),
                          str(ROOT / '04_Results' / CASE), '90', '120'],
                         text=True, capture_output=True, check=True)
    meta = json.loads(out.stderr)
    records = list(csv.DictReader(out.stdout.splitlines()))
    x = np.array([int(row['sensor_x_cm']) for row in records])
    experiment = np.array([float(row['exp_rise_K']) for row in records])
    diag = devices(CASE)
    base = devices(BASE)
    def profile(avg, prefix):
        return np.array([avg[f'{prefix}_{p}'] - 27.5 for p in x])
    avg = averages(diag, 90, 120)
    tc, gas = [profile(avg, prefix) for prefix in ('TC', 'G')]
    assert np.allclose(tc, [float(row['fds_rise_K']) for row in records], atol=.006)
    delta = gas - tc
    meta.update(gas_rmse_K=np.mean((gas-experiment)**2)**.5,
                gas_bias_K=(gas-experiment).mean(), gas_minus_tc_mean_K=delta.mean(),
                gas_minus_tc_range_K=[delta.min(), delta.max()])
    for row, g, diff in zip(records, gas, delta):
        row.update(gas_rise_K=round(g, 3), gas_minus_tc_K=round(diff, 3))
    write_csv('stations', records)
    plume = []
    for name in avg:
        if name.startswith('P_TEMPERATURE_'):
            z = name.split('_')[-1]
            plume.append(dict(x_m=3.325, y_m=.475, z_m=z, gas_C=avg[name],
                              tc_C=avg['P_THERMOCOUPLE_'+z], w_m_s=avg['P_W-VELOCITY_'+z]))
    write_csv('plume_90_120', plume)
    trends = []
    for case, data in ((BASE, base), (CASE, diag)):
        for lo, hi in ((60, 75), (75, 90), (90, 105), (105, 120), (90,120)):
            a = averages(data, lo, hi)
            for signal in (('TC','G') if case == CASE else ('TC',)):
                v = profile(a, signal)
                for region, mask in [('left', x<=120), ('peak', abs(x-330)<=30),
                                     ('right', x>=540), ('all_stations', x>=0)]:
                    trends.append(dict(case=case, signal=signal, start_s=lo, end_s=hi,
                                       region=region, count=int(mask.sum()), mean_rise_K=v[mask].mean(),
                                       mean_bias_K=(v-experiment)[mask].mean()))
    write_csv('time_windows', trends)
    (RESULTS / (CASE + '_metrics.json')).write_text(json.dumps(meta, indent=2)+'\n')


if __name__ == '__main__':
    run()
