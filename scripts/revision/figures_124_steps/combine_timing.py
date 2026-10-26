#!/usr/bin/env python3
"""Accepted phase rows -> one total-time / peak-memory row per repetition."""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('input',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
with a.input.open() as f:
    phases=list(csv.DictReader(f,delimiter='\t'))
groups=defaultdict(list)
for row in phases:
    if row['accepted']!='true' or row['exit_status']!='0':
        raise ValueError('Input includes an unaccepted/nonzero-exit attempt')
    key=tuple(row[k] for k in ('dataset','tool','threads','replicate'))
    groups[key].append(row)
output=[]
for key,pair in sorted(groups.items()):
    if len(pair)!=2 or {r['phase'] for r in pair}!={'whitelist_detection','demultiplexing'}:
        raise ValueError('Expected exactly one detection and one demultiplexing row: '+str(key))
    seconds=sum(float(r['elapsed_seconds']) for r in pair)
    peak=max(int(r['gnu_time_max_rss_kib']) for r in pair)
    output.append(dict(zip(('dataset','tool','threads','replicate'),key),
                       total_wall_seconds=seconds,total_wall_hours=seconds/3600,
                       max_process_rss_GB=peak*1024/1e9,
                       memory_definition='max GNU time process maxRSS over phases; decimal GB'))
a.output.parent.mkdir(parents=True,exist_ok=True)
with a.output.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(output[0]),delimiter='\t',lineterminator='\n')
    w.writeheader();w.writerows(output)
print(f'{len(phases)} accepted phases -> {len(output)} paired repetitions')
