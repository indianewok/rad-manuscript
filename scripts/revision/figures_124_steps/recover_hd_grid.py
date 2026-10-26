#!/usr/bin/env python3
"""Recover only plotting-required16um grid columns; verify saved barcode sets."""
import argparse,csv,gzip,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--input',type=Path,required=True)
p.add_argument('--raw-barcodes',type=Path,required=True)
p.add_argument('--filtered-barcodes',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--report',type=Path,required=True)
a=p.parse_args()
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def barcodes(path):
 with gzip.open(path,'rt') as f:return {x.strip() for x in f}
with a.input.open() as f:records=list(csv.DictReader(f,delimiter='\t'))
grid=[dict(barcode=r['bin_id'],in_tissue=int(r['in_tissue']),array_row=int(r['array_row']),array_col=int(r['array_col'])) for r in records]
ids={r['barcode'] for r in grid};coords={(r['array_row'],r['array_col']) for r in grid}
inside={r['barcode'] for r in grid if r['in_tissue']==1}
assert len(grid)==len(ids)==len(coords)==419*419
assert coords=={(row,col) for row in range(419) for col in range(419)}
assert all(r['barcode']==f"s_016um_{r['array_row']:05d}_{r['array_col']:05d}-1" for r in grid)
assert all(r['in_tissue'] in (0,1) for r in grid)
assert ids==barcodes(a.raw_barcodes)
assert inside==barcodes(a.filtered_barcodes)
a.output.parent.mkdir(parents=True,exist_ok=True)
with a.output.open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(grid[0]),lineterminator='\n');w.writeheader();w.writerows(grid)
a.report.parent.mkdir(parents=True,exist_ok=True)
a.report.write_text(json.dumps(dict(status='passed reconstructed plotting-required grid',grid_rows=len(grid),in_tissue_rows=len(inside),source=[dict(path=str(x),sha256=digest(x)) for x in (a.input,a.raw_barcodes,a.filtered_barcodes)],output=dict(path=str(a.output),sha256=digest(a.output)),limitations='Original named tissue_positions CSV not recovered. Only required barcode/array_row/array_col/in_tissue columns reconstructed exactly from deposited wide-derived data; no pixel coordinates or Seurat expression imputed.'),indent=2)+'\n')
print(f'Reconstructed {len(grid)} full-grid rows; {len(inside)} in-tissue IDs exactly match saved filtered reference')
