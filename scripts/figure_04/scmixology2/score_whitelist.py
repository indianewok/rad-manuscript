#!/usr/bin/env python3
"""Calculate barcode-set agreement with the matched short-read reference."""
import argparse
import csv
import gzip
from pathlib import Path
import re

def barcodes(path):
    opener=gzip.open if path.suffix=='.gz' else open
    values=[]
    with opener(path,'rt') as handle:
        for line in handle:
            value=re.split(r'[\s,]+',line.strip())[0].removesuffix('-1')
            if not value or value.lower()=='barcode':
                continue
            if not re.fullmatch('[ACGT]{16}',value):
                raise ValueError('Expected a16-base barcode: '+value)
            values.append(value)
    if len(values)!=len(set(values)):
        raise ValueError('Duplicate barcode identity: '+str(path))
    return set(values)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool',choices=['BLAZE','Flexiplex'],required=True)
    parser.add_argument('--selected',type=Path,required=True)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    selected,reference=barcodes(args.selected),barcodes(args.reference)
    if not reference:
        raise ValueError('The reference set is empty')
    tp,fp,fn=len(selected&reference),len(selected-reference),len(reference-selected)
    row=dict(tool=args.tool,calls=len(selected),reference_n=len(reference),tp=tp,fp=fp,fn=fn,
             precision=tp/len(selected) if selected else 0,recall=tp/len(reference),
             f1=2*tp/(len(selected)+len(reference)))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(row),delimiter='\t',lineterminator='\n')
        writer.writeheader();writer.writerow(row)
    print(row)

if __name__=='__main__':
    main()
