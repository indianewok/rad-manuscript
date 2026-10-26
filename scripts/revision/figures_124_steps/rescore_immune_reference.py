#!/usr/bin/env python3
"""Build the RAGE T/B-containing positive proxy from explicit deposited labels."""
import argparse
import csv
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('input',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
with a.input.open() as f:rows=list(csv.DictReader(f,delimiter='\t'))
truth={r['barcode'] for r in rows if r['in_deposited_shortread_list']=='True' and
       (r['deposited_label'].startswith(('T_cell','B_cell')) or r['deposited_label']=='T_B_doublet')}
columns={'RAD':'called_RAD','BLAZE':'called_BLAZE_2.6.0a0_expect10433','Flexiplex':'called_Flexiplex_f8'}
output=[]
for tool,column in columns.items():
    calls={r['barcode'] for r in rows if r[column]=='True'}
    output.append(dict(tool=tool,input_annotation_rows=len(rows),reference_n=len(truth),calls=len(calls),
                       tp=len(calls&truth),fp=len(calls-truth),fn=len(truth-calls)))
a.output.parent.mkdir(parents=True,exist_ok=True)
with a.output.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(output[0]),delimiter='\t',lineterminator='\n')
    w.writeheader();w.writerows(output)
print(f'{len(rows)} annotation rows -> {len(truth)} named T/B-containing reference barcodes')
