"""Paired OP-6 holdouts with station-specific near-threshold loss weights."""
import csv
from collections import defaultdict

import numpy as np

from run import HERE, ROOT, H, LIMIT, X, case_data, direction, forecast, intervals, score_events, write_rows

SCHEMES = {'uniform': (1, 1), 'moderate': (2, 4), 'strong': (4, 16)}


def weighted_forecast(train, phi_test, near, low):
    phi = np.vstack([c['phi'] for c in train])
    y = np.vstack([c['y'] for c in train])
    weights = np.where(y < LIMIT, low, np.where(y <= .43, near, 1))
    n = phi.shape[1]
    # Station-major coefficients; the same spatial-average physics penalty
    # couples otherwise independent weighted regressions.
    system = 25*np.kron(np.outer(direction, direction), sum(c['physics'] for c in train))
    for j, w in enumerate(weights.T):
        block = slice(j*n, (j+1)*n)
        system[block, block] += phi.T @ (w[:, None]*phi) + .1*np.eye(n)
    rhs = (weights*(H-y)).T @ phi
    coef = np.linalg.solve(system, rhs.ravel()).reshape(len(X), n)
    return np.clip(H-phi_test @ coef.T, 0, H)


def matches(reference, predicted):
    used = set()
    pairs = {}
    for i, (a, b) in enumerate(reference):
        for j, (c, d) in enumerate(predicted):
            overlap = min(b, d)-max(a, c)
            if j not in used and overlap > 0 and overlap >= .5*(max(b,d)-min(a,c)):
                pairs[i] = j
                used.add(j)
                break
    return pairs


def main():
    with (ROOT/'05_Calculations/layer_surrogate_holdouts.csv').open(encoding='utf-8-sig') as f:
        cases = [case_data(row) for row in csv.DictReader(f)]
    with (HERE/'event_scores.csv').open() as f:
        previous = {r['case']:r for r in csv.DictReader(f) if r['model']=='pinn'}
    scores, events = [], []
    for case in cases:
        train = [c for c in cases if c['layout']==case['layout'] and c is not case]
        truth = case['y']
        base_alarms = {}
        for scheme, weights in SCHEMES.items():
            p = weighted_forecast(train, case['phi'], *weights)
            score = score_events(case['t'], truth, p)
            if scheme == 'uniform':
                np.testing.assert_allclose(p, forecast(train, case)['pinn'], atol=1e-8, rtol=0)
                assert all(v==int(previous[case['name']][k]) for k,v in score.items())
            novel = removed = counted_false = counted_short = 0
            for j, x in enumerate(X):
                ref = intervals(case['t'], truth[:,j])
                alarm = intervals(case['t'], p[:,j])
                pairs = matches(ref, alarm)
                matched_indices = set(pairs.values())
                false = [ev for k,ev in enumerate(alarm) if k not in matched_indices]
                if scheme == 'uniform':
                    base_alarms[j] = false
                retained = matches(base_alarms[j], false)
                novel += len(false)-len(retained)
                removed += len(base_alarms[j])-len(retained)
                counted_false += len(false)
                retained_false = set(retained.values())
                for k, (a,b) in enumerate(false):
                    kind = 'retained_false' if k in retained_false else 'new_false'
                    events.append(dict(case=case['name'], scheme=scheme, x_m=x, kind=kind,
                                       alarm_start_s=a, alarm_end_s=b))
                for k, (a,b) in enumerate(ref):
                    if b-a <= 2 and k in pairs:
                        counted_short += 1
                        c,d = alarm[pairs[k]]
                        events.append(dict(case=case['name'], scheme=scheme, x_m=x,
                                           kind='short_hit', truth_start_s=a, truth_end_s=b, alarm_start_s=c, alarm_end_s=d))
            assert counted_false == score['unmatched_alarms'] and counted_short == score['short_matched']
            scores.append(dict(layout=case['layout'],case=case['name'],scheme=scheme,**score,
                               new_false=novel,removed_false=removed,mae_m=np.abs(truth-p).mean(),
                               false_pass=int(p.min()>=LIMIT and truth.min()<LIMIT)))
    write_rows(HERE/'weighted_scores.csv', scores)
    with (HERE/'weighted_event_audit.csv').open('w',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=['case','scheme','x_m','kind','truth_start_s','truth_end_s',
                                               'alarm_start_s','alarm_end_s'])
        writer.writeheader()
        writer.writerows(events)
    by_group = defaultdict(list)
    for r in scores:
        by_group[r['layout'], r['scheme']].append(r)
    for group, rows in by_group.items():
        print(group,{k:sum(r[k] for r in rows) for k in ('short_matched','alarms','matched','unmatched_alarms',
                                                         'new_false','removed_false','false_pass')},
              'MAE',np.mean([r['mae_m'] for r in rows]))


if __name__ == '__main__':
    main()
