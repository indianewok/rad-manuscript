#!/usr/bin/env python3
"""Convert saved native component statistics to the executed assignment schema."""
import argparse
import csv
import gzip
from pathlib import Path

COMPLEMENT=str.maketrans('ACGTNacgtn','TGCANtgcan')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    opener=gzip.open if a.input.suffix=='.gz' else open
    output_opener=gzip.open if a.output.suffix=='.gz' else open
    with opener(a.input,'rt') as source,output_opener(a.output,'wt') as target:
        rows=csv.DictReader(source,delimiter='\t')
        writer=csv.DictWriter(target,fieldnames=['read_id','barcode','umi','orientation','flank_edit_distance'],delimiter='\t',lineterminator='\n')
        writer.writeheader();n=0
        for row in rows:
            writer.writerow(dict(read_id=row['Read'],barcode='_'.join([row['BC3'],row['BC2'],row['BC1']]),
                umi=row['UB'].translate(COMPLEMENT)[::-1],orientation='',flank_edit_distance=row['FlankEditDist']))
            n+=1
    print(f'Normalized {n} saved component assignment records; no read deduplication or UMI length filter applied.')

if __name__=='__main__':main()
