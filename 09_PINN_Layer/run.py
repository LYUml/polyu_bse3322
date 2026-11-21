"""Whole-design leave-one-out time-series experiment, using existing FDS device files."""
import csv
import gzip
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
X = np.array([0.5, 1.7, 2.4, 3, 3.6, 4.2, 4.9, 6.1])
H, LIMIT = 0.76, 0.38
# Voronoi lengths on the compartment centreline approximate a volume average.
width = np.diff(np.r_[0, (X[1:] + X[:-1]) / 2, 6.6])
direction = width / np.linalg.norm(width)
rng = np.random.default_rng(3322)
centres = rng.uniform(0, 120, 96)
scales = np.exp(rng.uniform(np.log(1), np.log(25), 96))
slopes = rng.normal(0, 0.7, (2, 96))


def features(t, design):
    """Fixed tanh hidden units and analytic time derivatives, hard initial condition."""
    a = np.tanh((t[:, None] - centres) / scales + design @ slopes)
    raw = np.column_stack((np.ones(len(t)), a))
    derivative = np.column_stack((np.zeros(len(t)), (1 - a*a) / scales))
    gate = np.exp(-t[:, None] / 2)
    return (1 - gate)*raw, gate*raw/2 + (1 - gate)*derivative


def case_data(row):
    d, q, soot = (float(row[k]) for k in ('depth_m', 'flow_m3_s', 'soot_yield'))
    tall = row['layout'] == 'tall'
    prefix = 'tall_makeup' if tall else 'design'
    tag = '_'.join(f'{v:g}'.replace('.', 'p') for v in (soot, d, q))
    name = f'{prefix}_6_{tag}_120'
    folder = ROOT / '04_Results' / name
    log = (folder / (name + '.out')).read_text(errors='replace')
    if f'FDS completed successfully (CHID: {name})' not in log:
        raise ValueError(f'Incomplete run: {name}')
    with (folder / (name + '_devc.csv')).open() as file:
        reader = csv.reader(file)
        units, names = next(reader), next(reader)
        cols = [names.index(key) for key in ['Time', *(f'layer{x:g}' for x in X)]]
        if [units[i] for i in cols] != ['s'] + ['m']*8:
            raise ValueError(name + ' units')
        arr = np.array([[float(fields[i]) for i in cols] for fields in reader])
    t, y = arr[:, 0], arr[:, 1:]
    if not (t[0] == 0 and t[-1] == 120 and np.all((np.diff(t)>0) & (np.diff(t)<0.75))
            and np.all((0 <= y) & (y <= H)) and np.allclose(y[0], H)
            and abs(y.min()-float(row['fds_min_m'])) < 1e-8):
        raise ValueError(name + ' label or time mismatch')
    design = np.array([(d-.12)/.08, (soot-.06)/.04 if tall else (q-.20)/.08])
    phi, deriv = features(t, design)
    # Constant net source after startup; projecting out its per-design mean
    # eliminates that unknown from the linear residual.
    residual = (deriv + q/(6.6*.9*H)*phi)[t >= 10]
    residual -= residual.mean(axis=0)
    return dict(name=name, layout=row['layout'], design=design, t=t, y=y, phi=phi,
                gram=phi.T@phi, rhs=phi.T@(H-y), physics=residual.T@residual, row=row)


def forecast(train, test):
    gram = sum(c['gram'] for c in train) + .1*np.eye(test['phi'].shape[1])
    rhs = sum(c['rhs'] for c in train)
    w = np.linalg.solve(gram, rhs)
    # Only the spatially averaged upper-layer depth is constrained.
    avg = np.linalg.solve(gram + 25*sum(c['physics'] for c in train), rhs@direction)
    constrained = w + np.outer(avg - w@direction, direction)
    # Extend the earlier linear baseline to eight time series. Align training
    # curves to query times; no test heights enter any of these fits.
    aligned = np.stack([np.column_stack([np.interp(test['t'], c['t'], series)
                        for series in c['y'].T]) for c in train])
    inputs = np.array([np.r_[1, c['design']] for c in train])
    weights = np.r_[1, test['design']] @ np.linalg.pinv(inputs)
    return {k: np.clip(v, 0, H) for k, v in {
        'linear_time': np.tensordot(weights, aligned, axes=1),
        'without_residual': H-test['phi']@w,
        'pinn': H-test['phi']@constrained}.items()}


def intervals(t, y):
    """Open sublevel intervals of the piecewise linear station trace."""
    low = y < LIMIT
    edges = np.flatnonzero(low[1:] != low[:-1])
    cross = t[edges] + (LIMIT-y[edges])*np.diff(t)[edges]/np.diff(y)[edges]
    bounds = np.r_[t[0] if low[0] else [], cross, t[-1] if low[-1] else []]
    return bounds.reshape(-1, 2)


def score_events(t, actual, pred):
    n = short = hits = short_hits = alarms = 0
    for y, p in zip(actual.T, pred.T):
        truth, forecast_events = intervals(t, y), intervals(t, p)
        n += len(truth)
        alarms += len(forecast_events)
        matched = set()
        for a, b in truth:
            short += int(b-a <= 2)
            for j, (c, d) in enumerate(forecast_events):
                overlap = min(b,d)-max(a,c)
                if j not in matched and overlap > 0 and overlap >= .5*(max(b,d)-min(a,c)):
                    matched.add(j)
                    hits += 1
                    short_hits += int(b-a <= 2)
                    break
    return dict(events=n, matched=hits, short_events=short, short_matched=short_hits,
                alarms=alarms, unmatched_alarms=alarms-hits)


def write_rows(path, rows):
    with path.open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    with (ROOT/'05_Calculations/layer_surrogate_holdouts.csv').open(encoding='utf-8-sig') as f:
        cases = [case_data(row) for row in csv.DictReader(f)]
    if len({c['name'] for c in cases}) != 22:
        raise ValueError('Expected 22 unique designs')
    scores, minima = [], []
    with gzip.open(HERE/'holdout_curves.csv.gz', 'wt', newline='') as output:
        curves = csv.writer(output)
        curves.writerow(['case','time_s','x_m','fds_m','linear_time_m','without_residual_m','pinn_m'])
        for c in cases:
            train = [s for s in cases if s['layout'] == c['layout'] and s is not c]
            preds = forecast(train, c)
            actual = c['y']
            common = dict(layout=c['layout'], case=c['name'])
            minimums = {key: float(c['row'][key+'_pred_m']) for key in ('mean','linear','gp')}
            for model, p in preds.items():
                minimums[model] = p.min()
                scores.append(dict(**common, model=model, mae_m=np.abs(p-actual).mean(),
                                   **score_events(c['t'], actual, p)))
            for model, value in minimums.items():
                minima.append(dict(**common, model=model, actual_min_m=actual.min(),
                                   predicted_min_m=value, false_pass=int(actual.min()<LIMIT<=value)))
            for i,t in enumerate(c['t']):
                for j,x in enumerate(X):
                    curves.writerow([c['name'],t,x,actual[i,j],
                                     *(round(p[i,j],8) for p in preds.values())])
    write_rows(HERE/'event_scores.csv', scores)
    write_rows(HERE/'minimum_scores.csv', minima)


if __name__ == '__main__':
    main()
