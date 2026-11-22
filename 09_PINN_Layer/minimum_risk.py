"""Nested whole-design comparison for the minimum across all stations and times."""
import csv
import math
from collections import defaultdict

import numpy as np

from margin_monitor import HERE, LIMIT, X, design, load_complete, model, save


def estimate(train, test):
    coords = np.array([c['design'] for c in train])
    targets = np.array([c['y'].min() for c in train])
    # Same scales and ridge coefficient as the existing margin correction.
    def kernel(x):
        return np.exp(-.5*np.sum((x[:, None]-coords[None, :])**2, axis=2))
    weights = np.linalg.solve(kernel(coords)+.25*np.eye(len(train)),targets-targets.mean())
    direct = float((kernel(design(test)[None, :])@weights)[0]+targets.mean())
    pinn = float(model(train,test)[1].min())
    return pinn,direct,(direct+pinn)/2


def main():
    with (HERE/'margin_grouped.csv').open() as f:
        archive = defaultdict(list)
        for row in csv.DictReader(f):
            archive[row['case']].append(row)
    cases = load_complete()
    groups = defaultdict(list)
    for name in archive:
        groups[tuple(design(name)[:-1])].append(name)
        if {float(r['station_m']) for r in archive[name]} != set(X):
            raise ValueError(name)
    rows = []
    stacked_rows = []
    neighbor_rows = []
    for outer, tests in groups.items():
        train = [cases[n] for g,names in groups.items() if g!=outer for n in names]
        other_groups = [g for g in groups if g != outer]
        distances = np.linalg.norm(np.array(other_groups) - outer, axis=1)
        nearest = [g for g,d in zip(other_groups, distances) if np.isclose(d, distances.min())]
        # Give each physical design one vote, including designs with two meshes.
        nearest_min = np.mean([np.mean([cases[n]['y'].min() for n in groups[g]]) for g in nearest])
        point = {test:estimate(train,test) for test in tests}
        candidates = defaultdict(list)
        numerator = denominator = 0.
        for inner, calibration in groups.items():
            if inner==outer:
                continue
            smaller = [c for c in train if tuple(c['design'][:-1])!=inner]
            # Use the largest calibration error within a physical design.
            inner_predictions = np.array([estimate(smaller,n) for n in calibration])
            inner_truth = np.array([cases[n]['y'].min() for n in calibration])
            residual = max(abs(inner_predictions[:,2]-inner_truth))
            # Equal influence per physical design, including designs with two meshes.
            difference = inner_predictions[:,0]-inner_predictions[:,1]
            numerator += np.mean(difference*(inner_truth-inner_predictions[:,1]))
            denominator += np.mean(difference**2)
            for test in tests:
                candidates[test].append(estimate(smaller,test)[2]-residual)
        for test in tests:
            pinn,direct,hybrid = point[test]
            neighbor_rows.append(dict(case=test, actual_m=cases[test]['y'].min(),
                                      nearest_m=nearest_min, hybrid_m=hybrid,
                                      neighbor_cases='|'.join(n for g in nearest for n in groups[g])))
            weight = float(np.clip(numerator/denominator,0,1)) if denominator else .5
            stacked_rows.append(dict(case=test,actual_m=cases[test]['y'].min(),
                                     pinn_weight=weight,fixed_m=hybrid,
                                     stacked_m=weight*pinn+(1-weight)*direct))
            np.testing.assert_allclose(pinn,min(float(r['corrected_m']) for r in archive[test]),atol=1e-8)
            ordered = sorted(candidates[test])
            rank = math.floor(.10*(len(ordered)+1))
            lower = max(0,ordered[rank-1]) if rank else 0.
            rows.append(dict(case=test,actual_m=cases[test]['y'].min(),pinn_m=pinn,
                             direct_m=direct,hybrid_m=hybrid,lower_m=lower))
    save(HERE/'minimum_risk_holdouts.csv',rows)
    save(HERE/'minimum_stack_holdouts.csv',stacked_rows)
    save(HERE/'minimum_neighbor_holdouts.csv',neighbor_rows)
    actual=np.array([r['actual_m'] for r in rows])
    for key in ['pinn_m','direct_m','hybrid_m','lower_m']:
        pred=np.array([r[key] for r in rows])
        print(key,'mae',np.mean(abs(pred-actual)), 'false pass',sum((actual<LIMIT)&(pred>=LIMIT)),
              'true pass',sum((actual>=LIMIT)&(pred>=LIMIT)), 'below bound',sum(actual<pred))


if __name__=='__main__':
    main()
