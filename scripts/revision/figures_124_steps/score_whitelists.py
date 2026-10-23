#!/usr/bin/env python3
"""Exact barcode-set scoring: TP=call∩truth, FP=call−truth, FN=truth−call."""
import argparse
import csv
import re
from pathlib import Path

def barcodes(path):
    result=set()
    for line in path.read_text().splitlines():
        first=re.split(r'[\s,]+',line.strip())[0]
        if len(first)==16 and set(first)<=set('ACGT'):result.add(first)
    return result

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--truth',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('callsets',nargs='+',help='tool=path')
a=p.parse_args();truth=barcodes(a.truth);output=[]
if not truth:raise ValueError('Truth set is empty')
for specification in a.callsets:
    tool,path=specification.split('=',1);calls=barcodes(Path(path))
    tp=len(calls&truth);fp=len(calls-truth);fn=len(truth-calls)
    output.append(dict(tool=tool,reference_n=len(truth),calls=len(calls),tp=tp,fp=fp,fn=fn,
                       precision=tp/len(calls) if calls else 0,recall=tp/len(truth),
                       f1=2*tp/(2*tp+fp+fn)))
a.output.parent.mkdir(parents=True,exist_ok=True)
with a.output.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(output[0]),delimiter='\t',lineterminator='\n')
    w.writeheader();w.writerows(output)
print(f'Scored {len(output)} callsets against {len(truth)} known barcodes')
