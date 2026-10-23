#!/usr/bin/env python3
"""Resolve the first eight RAD CellSNP AD entries through variant/cell labels."""
import argparse,csv,gzip,hashlib,itertools,json
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--project-root',type=Path,required=True)
p.add_argument('--output',type=Path,default=Path('data/examples/figure_06'))
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
repo=Path(__file__).resolve().parents[2]
base=a.project_root/'LongBench_comps/SN_ONT_RAD_bulk_cellline_bundle_20260803/RAD/cellsnp'
paths=[base/'cellSNP.tag.AD.mtx',base/'cellSNP.base.vcf.gz',base/'cellSNP.samples.tsv']
entries=[];dims=None
with paths[0].open() as f:
    for line in f:
        if line.startswith('%'):continue
        if dims is None:dims=line.strip();continue
        entries.append(tuple(map(int,line.split())))
        if len(entries)==8:break
variants=[]
with gzip.open(str(paths[1]),'rt') as f:
    for line in f:
        if line.startswith('#'):continue
        variants.append(line.strip().split('\t'))
        if len(variants)>=max(x[0] for x in entries):break
cells=paths[2].read_text().splitlines()
genotypes={r['cell_barcode']:r for r in csv.DictReader((repo/'source_data/figure_06/union_per_cell_genotype.tsv').open(),delimiter='\t') if r['tool']=='RAD'}
coords={r['cell_barcode']:r for r in csv.DictReader((repo/'source_data/figure_06/fixed_coordinates.tsv').open(),delimiter='\t')}
rows=[]
for i,(v,c,n) in enumerate(entries,1):
    var=variants[v-1];cell=cells[c-1];g=genotypes[cell];xy=coords.get(cell,{})
    rows.append(dict(source_AD_entry=i,variant_row_1based=v,cell_column_1based=c,CHROM=var[0],POS=var[1],REF=var[3],ALT=var[4],
        cell_barcode=cell,alternate_allele_molecules=n,selected=g['selected'],query_state=g['query_state'],query_label=g['query_label'],
        reference_present=g['reference_present'],reference_label=g['reference_label'],UMAP_1=xy.get('UMAP_1','NA'),UMAP_2=xy.get('UMAP_2','NA')))
with (a.output/'allele_to_genotype.tsv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
sources=[]
for path in paths+[repo/'source_data/figure_06/union_per_cell_genotype.tsv',repo/'source_data/figure_06/fixed_coordinates.tsv']:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    sources.append(dict(path=str(path),sha256=h.hexdigest()))
(a.output/'allele_extraction.json').write_text(json.dumps(dict(scope='eight real first AD entries; 1-based variant/cell joins; query labels and fixed UMAP added by exact barcode; no allele fraction inferred',AD_dimensions=dims,sources=sources),indent=2)+'\n')
print('Wrote 8 real allele entries joined to genotype and fixed UMAP')
