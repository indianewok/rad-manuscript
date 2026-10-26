#!/usr/bin/env python3
"""Show real native MEX entries, their cell/gene identities, and full-cell CP10K."""
import argparse, csv, gzip, hashlib, itertools, json, math
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1048576), b''): h.update(block)
    return h.hexdigest()

def write(path, rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--matrix-dir',type=Path,required=True)
p.add_argument('--de-table',type=Path,required=True)
p.add_argument('--output',type=Path,default=Path('data/examples/figure_07'))
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
paths={name:a.matrix_dir/(name+'.gz') for name in ('matrix.mtx','features.tsv','barcodes.tsv')}
with gzip.open(str(paths['features.tsv']),'rt') as f: genes=[x.rstrip().split('\t') for x in f]
with gzip.open(str(paths['barcodes.tsv']),'rt') as f: cells=[x.strip() for x in f]
entries=[];totals={}; dims=None
with gzip.open(str(paths['matrix.mtx']),'rt') as f:
    for line in f:
        if line.startswith('%'):continue
        if dims is None:dims=tuple(map(int,line.split()));continue
        gene,cell,count=map(int,line.split())
        if len(entries)<8:entries.append((gene,cell,count));totals.setdefault(cell,0)
        if cell in totals:totals[cell]+=count
assert dims==(45224,12423,15772545)
# Every selected cell appears in the first eight entries; its preceding entries
# were already counted while the selection was being assembled.
rows=[]
for ordinal,(g,c,n) in enumerate(entries,1):
    cp10k=10000.*n/totals[c]
    rows.append(dict(source_entry=ordinal,gene_index_1based=g,cell_index_1based=c,
        gene_id=genes[g-1][0],gene_symbol=genes[g-1][1],cell_barcode=cells[c-1],
        molecule_count=n,full_cell_library_molecules=totals[c],CP10K=cp10k,log2_1_plus_CP10K=math.log2(1+cp10k)))
write(a.output/'RAD_matrix_entries.tsv',rows)
de=[];ordinals=[]
with gzip.open(str(a.de_table),'rt') as f:
    for i,r in enumerate(csv.DictReader(f,delimiter='\t'),1):
        if r['gene_symbol'] in ('DPM1','ASCL1','POU2F3'): de.append(r);ordinals.append(i)
write(a.output/'de_gene_rows.tsv',de)
manifest=[dict(source=str(path),source_sha256=sha(path),role=name,
    selection='first 8 nonzero entries, 1-based labels; library totals use complete source matrix') for name,path in paths.items()]
manifest.append(dict(source=str(a.de_table),source_sha256=sha(a.de_table),role='C5',
    selection='all tool rows for DPM1, ASCL1, POU2F3',source_data_rows=ordinals))
(a.output/'extraction.json').write_text(json.dumps(dict(scope='real bounded public cell-line excerpts; neither DE inference nor BH is reproducible from the excerpt alone',matrix_dimensions=dims,inputs=manifest),indent=2)+'\n')
print('Wrote 8 MEX entries and {} real DE rows with hashes'.format(len(de)))
