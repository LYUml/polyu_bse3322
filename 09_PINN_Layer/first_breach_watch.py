"""Freeze pre-output first-breach forecasts; verify device evidence separately."""
import csv
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from first_breach import HORIZONS, hazards
from margin_monitor import HERE, ROOT, LIMIT, PATTERN, X, design, save

ARCHIVE = HERE/'first_breach_frozen'


def training():
    path=HERE/'first_breach_scores.csv'
    with path.open() as f:
        labels={r['case']:float(r['first_breach_s'] or 'inf')
                for r in csv.DictReader(f) if int(r['horizon_s'])==120}
    return labels,hashlib.sha256(path.read_bytes()).hexdigest()


def already_observed(name):
    results=ROOT/'04_Results'
    return (any(results.glob('*/'+name+'.out')) or any(results.glob('*/'+name+'_devc.csv'))
            or any((ROOT/'05_Calculations').glob(name+'_*')))


def freeze(deck,labels,digest):
    name=deck.stem
    target=ARCHIVE/(name+'.json')
    if target.exists() or name in labels or already_observed(name):
        return
    raw=deck.read_bytes()
    if not re.search(r"\bCHID\s*=\s*'"+re.escape(name)+"'",raw.decode()) or not re.search(
            r'\bT_END\s*=\s*120(?:\.0*)?(?=[,/\s])',raw.decode()):
        raise ValueError('Unexpected deck: '+name)
    query=design(name)
    names=sorted(n for n in labels if np.any(design(n)[:-1]!=query[:-1]))
    risks=hazards(np.array([design(n) for n in names]),np.array([labels[n] for n in names]),query)
    data=dict(case=name,frozen_utc=datetime.now(timezone.utc).isoformat(),deck_sha256=hashlib.sha256(raw).hexdigest(),
              training_sha256=digest,training_cases=names,threshold=.5,
              risks={str(h):float(p) for h,p in zip(HORIZONS,risks)})
    ARCHIVE.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=ARCHIVE,delete=False,mode='w',encoding='utf-8') as f:
        json.dump(data,f,indent=2,allow_nan=False)
        f.write('\n')
    try:
        if not already_observed(name):
            try:
                os.link(f.name,target)  # Immutable first writer wins.
                print('frozen',name)
            except FileExistsError:
                pass
    finally:
        Path(f.name).unlink()


def device_evidence(path):
    # Ignore a trailing record still being written, validate every complete row.
    lines=path.read_bytes().splitlines(keepends=True)
    if lines and not lines[-1].endswith((b'\n',b'\r')):
        lines.pop()
    if len(lines)<3:
        return None
    reader=csv.reader(line.decode('utf-8-sig').strip() for line in lines)
    units,header=next(reader),next(reader)
    cols=[header.index(f'layer{x:g}') for x in X]
    if header[0]!='Time' or units[0]!='s' or any(units[j]!='m' for j in cols):
        raise ValueError('Device units or column mismatch: '+str(path))
    previous=None
    first=np.inf
    for row in reader:
        t=float(row[0])
        h=np.array([float(row[j]) for j in cols])
        if (not np.isfinite(t) or not np.all((0<=h)&(h<=.76)) or
                (previous is None and t!=0) or
                (previous is not None and not 0<t-previous<=.75)):
            raise ValueError('Invalid device record: '+str(path))
        if min(h)<LIMIT:
            first=min(first,t)
        previous=t
    return previous,first


def score(archive):
    name=archive['case']
    observations={}
    for path in (ROOT/'04_Results').glob('*/'+name+'_devc.csv'):
        deck=path.with_name(name+'.fds')
        if not deck.exists() or hashlib.sha256(deck.read_bytes()).hexdigest()!=archive['deck_sha256']:
            print('Skipped changed or missing input',path.parent)
            continue
        evidence=device_evidence(path)
        if evidence is None:
            continue
        end,first=evidence
        log=path.with_name(name+'.out')
        completed=(abs(end-120)<=.001 and log.exists() and
                   f'STOP: FDS completed successfully (CHID: {name})' in log.read_text(errors='replace')[-2048:])
        for h in HORIZONS:
            positive=first<=h
            if not positive and (end<h or (h==120 and not completed)):
                continue
            # Separate replicas cannot silently supply contradictory labels.
            if h in observations and observations[h]!=positive:
                raise ValueError(f'Conflicting results for {name} at {h} s')
            observations[h]=positive
    for h,outcome in sorted(observations.items()):
        p=archive['risks'][str(h)]
        yield dict(case=name,frozen_utc=archive['frozen_utc'],horizon_s=h,risk=p,
                   observed=int(outcome),correct=int((p>=archive['threshold'])==outcome))


def main():
    labels,digest=training()
    for deck in sorted((ROOT/'03_Models').glob('*.fds')):
        if PATTERN.fullmatch(deck.stem):
            freeze(deck,labels,digest)
    result=[]
    for path in sorted(ARCHIVE.glob('*.json')):
        result.extend(score(json.loads(path.read_text())))
    score_path=HERE/'first_breach_prospective.csv'
    recorded={}
    if score_path.exists():
        with score_path.open() as f:
            recorded={(r['case'],int(r['horizon_s'])):r for r in csv.DictReader(f)}
    for r in result:
        key=(r['case'],int(r['horizon_s']))
        if key in recorded and int(recorded[key]['observed'])!=r['observed']:
            raise ValueError(f'Previously scored outcome changed: {key}')
        recorded[key]=r
    if result:
        save(score_path,[recorded[k] for k in sorted(recorded)])
    print('frozen designs',len(list(ARCHIVE.glob('*.json'))),'resolved horizons',len(recorded))


if __name__=='__main__':
    main()
