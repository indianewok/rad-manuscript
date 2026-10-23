#!/usr/bin/env python3
"""Show raw/target/truth classification for a bounded real assignment excerpt.

Duplicate decisions are not inferred from a truncated excerpt. Full physical-ID
accounting is in figures_124_assignment_audit.py and uses every source record.
"""
import argparse,csv
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--tool',choices=['RAD','Flexiplex','BLAZE'],required=True)
p.add_argument('input',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();result=[]
with a.input.open() as f:
 for row in csv.DictReader(f,delimiter='\t'):
  if a.tool=='RAD':
   rid=row['read_id'];truth=row['truth_barcode'];target=row['rad_cb']
   raw=row['rad_cr'];corrected=bool(raw)
   note='RAD nonempty CR tag indicates corrected; raw tag can be reverse orientation'
  elif a.tool=='Flexiplex':
   rid=row['Read'];truth=rid.rsplit('-',1)[0];target=row['CellBarcode'];raw=row['RawCellBarcode']
   corrected=raw!=target;note='compare native raw barcode and final target'
  else:
   rid=row['read_id'];truth=row['true_barcode'];target=row['assigned_barcode'];raw=row['putative_barcode']
   corrected=raw!=target;note='empty assigned target means unassigned'
  state='unassigned' if not target else ('corrected' if corrected else 'native')+('_correct' if target==truth else '_incorrect')
  result.append(dict(tool=a.tool,read_id=rid,truth_barcode=truth,raw_barcode_or_CR=raw,target_barcode=target,record_state=state,interpretation=note,duplicate_status='not assessed from bounded excerpt'))
a.output.parent.mkdir(parents=True,exist_ok=True)
with a.output.open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(result[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(result)
print(f'Classified {len(result)} preview records; full physical-ID counts require complete input')
