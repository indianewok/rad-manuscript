#!/usr/bin/env python3
"""Expose fields from a retained GNU_TIME_V1 log without a timing rerun."""
import argparse
import csv
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('logs',type=Path,nargs='+')
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();rows=[]
for path in a.logs:
    text=path.read_text().strip().replace('\\t','\t')
    fields=text.split('\t')
    if fields[0]!='GNU_TIME_V1':raise ValueError('Unknown timing format: '+str(path))
    row=dict(field.split('=',1) for field in fields[1:])
    if row['exit_status']!='0':raise ValueError('Nonzero-exit phase: '+str(path))
    row['source_log']=str(path);rows.append(row)
columns=sorted({key for row in rows for key in row})
a.output.parent.mkdir(parents=True,exist_ok=True)
with a.output.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=columns,delimiter='\t',lineterminator='\n')
    w.writeheader();w.writerows(rows)
print(f'Read {len(rows)} measured GNU-time records; no program was benchmarked again')
