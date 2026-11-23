"""Leave an entire inlet family out across depths, flows, doors, soot and meshes."""
import csv
import json

import numpy as np

from margin_monitor import HERE, ROOT, LIMIT, PATTERN, design, load_complete, model

METHODS = ("pinn", "ridge", "nearest")


def main():
    cases = load_complete()
    labels = {n: (float(c["y"].min()), True) for n, c in cases.items()}
    for path in sorted((ROOT / "05_Calculations").glob("*_screen_failure.json")):
        name = path.name.removesuffix("_screen_failure.json")
        if PATTERN.fullmatch(name):
            event = json.loads(path.read_text())
            assert event["chid"] == name and event["observed_min_m"] < LIMIT and name not in labels
            labels[name] = (event["observed_min_m"], False)
    family = {n: PATTERN.fullmatch(n)[1] for n in labels}
    rows = []
    for group in sorted(set(family.values())):
        train = [c for n, c in cases.items() if family[n] != group]
        x = np.array([c["design"] for c in train])
        y = np.array([c["y"].min() for c in train])
        centered = x - x.mean(axis=0)
        # Fixed L2 penalty, physical feature scales from design(), unpenalised intercept.
        coef = np.linalg.solve(centered.T @ centered + np.eye(x.shape[1]), centered.T @ (y-y.mean()))
        for n in sorted(labels):
            if family[n] != group:
                continue
            d = design(n)
            distance = np.linalg.norm(x-d, axis=1)
            observed, complete = labels[n]
            rows.append(dict(case=n, family=group, train_count=len(train), complete=int(complete),
                             observed_min_m=observed, passed=int(complete and observed >= LIMIT),
                             pinn=float(model(train,n)[1].min()), ridge=float(y.mean()+(d-x.mean(axis=0))@coef),
                             nearest=float(y[np.isclose(distance,distance.min())].mean())))
    with (HERE/"layout_family_comparison.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for group in sorted(set(family.values()))+["all"]:
        subset=[r for r in rows if group=="all" or r["family"]==group]
        print(group,len(subset),"complete",sum(r["complete"] for r in subset),"fails",sum(not r["passed"] for r in subset))
        for method in METHODS:
            err=[abs(r[method]-r["observed_min_m"]) for r in subset if r["complete"]]
            misses=sum(r[method]>=LIMIT and not r["passed"] for r in subset)
            rejects=sum(r[method]<LIMIT and r["passed"] for r in subset)
            shortlist=sorted(subset,key=lambda r:-r[method])[:3]
            print(method,round(np.mean(err)*100,2) if err else None,misses,rejects,"top3",sum(r["passed"] for r in shortlist))


if __name__=="__main__":
    main()
