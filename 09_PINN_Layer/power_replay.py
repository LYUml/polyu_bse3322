"""Fixed models, zero revealed test labels, 18-query budget per policy.

Use fixed OP6 then OP1, increasing soot within door. For design ranking,
try predicted feasible designs in power order, then the largest predicted
worst-case height, breaking ties by power. After finding a feasible design,
query only cheaper unresolved designs. Unknown labels branch both ways.
"""
import csv
import json
from collections import defaultdict

import numpy as np

from margin_monitor import HERE, ROOT, X, LIMIT, load_complete, save
from minimum_risk import design, estimate, nearest_designs

ARCHIVE = ROOT / '05_Calculations'
POWER = {'0p96': 4.35, '1p12': 6.91, '1p28': 10.32}


def observed(name):
    path = ARCHIVE / (name + '_stations.csv')
    if path.exists():
        with path.open(encoding='utf-8-sig') as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == len(X) and {float(r['x_m']) for r in rows} == set(X)
        assert all(r['case'] == name and float(r['start_s']) == 0
                   and float(r['end_s']) == 120 for r in rows)
        return min(float(r['min_height_m']) for r in rows)
    failure = ARCHIVE / (name + '_screen_failure.json')
    if failure.exists():
        record = json.loads(failure.read_text())
        assert record['chid'] == name and record['observed_min_m'] < LIMIT
        return record['observed_min_m']
    return None


def replay(order, scenarios, labels, unknown_pass, trace):
    count = 0
    best = None
    first = None
    for flow in order:
        if best and POWER[flow] >= POWER[best]:
            continue
        for name in scenarios[flow]:
            count += 1
            value = labels[name]
            passed = unknown_pass[name] if value is None else value >= LIMIT
            if trace is not None:
                trace.append((count, name, value))
                if value is None:
                    return None, None
            if not passed:
                break
        else:
            best = flow
            if first is None:
                first = count
    assert count <= 18 and first is not None
    return first, count


def main():
    from itertools import product

    cases = load_complete()
    train = [case for name, case in cases.items()
             if not name.startswith(('inlet44_1_', 'inlet48_6_'))]
    minima_by_design = defaultdict(list)
    for case in train:
        minima_by_design[tuple(case['design'][:-1])].append(case['y'].min())
    traces, summary, inventory = [], [], []
    for mesh, suffix, flows in [('original', '', ['0p96', '1p28']),
                                ('refined', '_z38', list(POWER))]:
        fixed = {q: [f'{door}_{soot}_0p24_{q}{suffix}_120'
                     for door in ('inlet48_6', 'inlet44_1')
                     for soot in ('0p02', '0p05', '0p1')] for q in flows}
        scores = {}
        for names in fixed.values():
            for n in names:
                neighbors = nearest_designs(minima_by_design, tuple(design(n)[:-1]))
                nearest = np.mean([np.mean(minima_by_design[g]) for g in neighbors])
                scores[n] = (*estimate(train, n), nearest)
        labels = {n: observed(n) for n in scores}
        for q in flows:
            for n in fixed[q]:
                inventory.append(dict(mesh=mesh, case=n, power_W=POWER[q],
                                      observed_min_m=labels[n], pinn=scores[n][0],
                                      direct=scores[n][1], hybrid=scores[n][2], nearest=scores[n][3]))
        missing = [n for n in scores if labels[n] is None]
        for model, column in [('baseline', 0), ('pinn', 0), ('direct', 1), ('hybrid', 2), ('nearest', 3)]:
            modes = ['fixed'] if model == 'baseline' else ['design', 'scenario', 'both']
            for mode in modes:
                minima = {q: min(scores[n][column] for n in fixed[q]) for q in flows}
                order = list(flows)
                if mode in ('design', 'both'):
                    order.sort(key=lambda q: (minima[q] < LIMIT,
                                              POWER[q] if minima[q] >= LIMIT else -minima[q],
                                              POWER[q]))
                scenarios = {q: sorted(fixed[q], key=lambda n: scores[n][column])
                             if mode in ('scenario', 'both') else fixed[q] for q in flows}
                prefix = dict(mesh=mesh, model=model, mode=mode)
                path = []
                replay(order, scenarios, labels, dict.fromkeys(missing, False), path)
                for step, n, v in path:
                    traces.append(dict(**prefix, query=step, case=n, observed_min_m=v,
                                       result='unknown' if v is None else
                                       ('pass' if v >= LIMIT else 'fail')))
                outcomes = [replay(order, scenarios, labels, dict(zip(missing, bits)), None)
                            for bits in product((False, True), repeat=len(missing))]
                first, proof = zip(*outcomes)
                if model == 'baseline':
                    assert min(first) == max(first) and min(proof) == max(proof)
                    reference = first[0], proof[0]
                summary.append(dict(**prefix, first_min=min(first), first_max=max(first),
                                    proof_min=min(proof), proof_max=max(proof),
                                    first_saved_min=reference[0]-max(first),
                                    first_saved_max=reference[0]-min(first),
                                    proof_saved_min=reference[1]-max(proof),
                                    proof_saved_max=reference[1]-min(proof)))
    for name, rows in [('inventory', inventory), ('trace', traces), ('summary', summary)]:
        save(HERE / f'power_replay_{name}.csv', rows)


if __name__ == '__main__':
    main()
