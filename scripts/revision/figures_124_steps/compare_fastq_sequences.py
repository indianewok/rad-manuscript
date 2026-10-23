#!/usr/bin/env python3
"""Compare paired FASTQ sequences and quality strings; works on plain previews."""
import argparse
import csv
from pathlib import Path

def records(path):
    with path.open() as f:
        while True:
            header=f.readline()
            if not header:break
            seq=f.readline().strip();plus=f.readline();q=f.readline().strip()
            if not header.startswith('@') or not plus.startswith('+') or len(seq)!=len(q):
                raise ValueError('Malformed FASTQ')
            yield header.strip(),seq,q

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('flat',type=Path);p.add_argument('native',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();left=list(records(a.flat));right=list(records(a.native))
if len(left)!=len(right):raise ValueError('Different record counts')
output=[]
for (h,s,q),(h2,s2,q2) in zip(left,right):
    if (h,s)!=(h2,s2):raise ValueError('Header/sequence changed')
    output.append(dict(read_id=h[1:],bases=len(s),sequence_equal=True,quality_equal=q==q2,
                       flat_mean_Q=sum(ord(c)-33 for c in q)/len(q),
                       native_mean_Q=sum(ord(c)-33 for c in q2)/len(q2)))
a.output.parent.mkdir(parents=True,exist_ok=True)
with a.output.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(output[0]),delimiter='\t',lineterminator='\n')
    w.writeheader();w.writerows(output)
print(f'{len(output)} preview records retain identical ordered headers/sequences')
