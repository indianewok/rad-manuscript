#!/usr/bin/env python3
"""Validate and recompute discovery metrics, keeping paired input identities."""
import argparse
import csv
from collections import defaultdict
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('input',type=Path);p.add_argument('output',type=Path)
p.add_argument('--expected-inputs',type=int,default=37)
a=p.parse_args()
with a.input.open() as f:rows=list(csv.DictReader(f,delimiter='\t'))
seen=set();tools=defaultdict(set);out=[]
for row in rows:
    key=(row['canonical_id'],row['tool'])
    if key in seen:raise ValueError('Duplicate paired key: '+str(key))
    seen.add(key);tools[key[0]].add(key[1])
    tp,fp,fn,calls,ref=(int(row[x]) for x in ('tp','fp','fn','calls','reference_n'))
    if calls!=tp+fp or ref!=tp+fn or min(tp,fp,fn)<0:raise ValueError('Count identity failed')
    metrics={'precision':tp/calls if calls else 0,'recall':tp/ref if ref else 0,
             'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0}
    for key,value in metrics.items():
        if abs(value-float(row[key]))>1e-9:raise ValueError('Stored metric differs: '+key)
    out.append(dict(canonical_id=row['canonical_id'],tool=row['tool'],
                    input_status=row['input_status'],reference_type=row['reference_type'],
                    calls=calls,reference_n=ref,tp=tp,fp=fp,fn=fn,**metrics))
if len(tools)!=a.expected_inputs or any(t!={'RAD','BLAZE','Flexiplex'} for t in tools.values()):
    raise ValueError('Input count or matched tool triple failed')
a.output.parent.mkdir(parents=True,exist_ok=True)
with a.output.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(out[0]),delimiter='\t',lineterminator='\n')
    w.writeheader();w.writerows(out)
print(f'{len(out)} rows, {len(tools)} matched inputs, all count/metric checks passed')
