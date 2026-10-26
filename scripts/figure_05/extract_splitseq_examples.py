#!/usr/bin/env python3
"""Extract LR-Split-seq assignment examples with source hashes and original row numbers."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
from aggregate_splitseq import read_table, sha


def write(path, rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    p.add_argument('--output',type=Path,default=Path('data/examples/figure_05/splitseq'))
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);root=a.root
    cells=list(read_table(root/'data/figure_05/splitseq_cells.tsv'))[:2]
    write(a.output/'cells.tsv',cells);keys={x['canonical_barcode'] for x in cells}
    rt=list(read_table(root/'data/figure_05/rt_primer_well_map.csv'))
    t={x['well']:x['sequence'].strip() for x in rt if x['type']=='T'}
    primer={x['sequence'].strip():t[x['well']] for x in rt}
    def canonical(key):
        x=key.split('_')
        return '_'.join([primer.get(x[0],x[0])]+x[1:])
    sources=[]
    component=root/'checkpoints/figure_05/component_polyT_assignments.tsv.gz'
    stats=root/'checkpoints/figure_05/component_polyT_native_stats.tsv.gz'
    selected=[];native=[];ordinals=[]
    for i,(row,nat) in enumerate(zip(read_table(component),read_table(stats)),1):
        if canonical(row['barcode']) in keys:
            assert row['read_id']==nat['Read']
            selected.append(row);native.append(nat);ordinals.append(i)
            if len(selected)==8:break
    write(a.output/'component_assignments.tsv',selected);write(a.output/'component_native_stats.tsv',native)
    for path,name in [(component,'component_assignments.tsv'),(stats,'component_native_stats.tsv')]:
        sources.append(dict(output=name,source=str(path.relative_to(root)),source_sha256=sha(path),
            source_data_rows=ordinals,selection='first8 rows assigning either of the first2 published physical cells; unchanged columns'))
    rad=root/'checkpoints/figure_05/RAD_ED2_assignments.tsv.gz';selected=[];ordinals=[]
    for i,row in enumerate(read_table(rad),1):
        if canonical(row['normalized_barcode']) in keys:
            selected.append(row);ordinals.append(i)
            if len(selected)==8:break
    write(a.output/'rad_assignments.tsv',selected)
    sources.append(dict(output='rad_assignments.tsv',source=str(rad.relative_to(root)),source_sha256=sha(rad),
        source_data_rows=ordinals,selection='first8 rows assigning either of the first2 published physical cells; unchanged columns'))
    cellpath=root/'data/figure_05/splitseq_cells.tsv'
    sources.append(dict(output='cells.tsv',source=str(cellpath.relative_to(root)),source_sha256=sha(cellpath),
        source_data_rows=[1,2],selection='first2 rows, all columns unchanged'))
    (a.output/'extraction.json').write_text(json.dumps(dict(scope='Eight assignment records per tool for the first two published physical cells',sources=sources),indent=2)+'\n')
    lines=['# LR-Split-seq assignment examples','','These examples follow the first two published physical cells through RAD and component Flexiplex/poly-T assignments. Each tool contributes eight records. [Extraction details](extraction.json) give the source hashes and original row numbers.','','## Native component records','','| Read | BC1 | BC2 | BC3 | UB |','|---|---|---|---|---|']
    lines += ['| '+' | '.join(row[k] for k in ['Read','BC1','BC2','BC3','UB'])+' |' for row in native[:3]]
    lines += ['','The normalization script writes `BC3_BC2_BC1` and reverse-complements `UB`. RT primer variants then map to the T primer of the same physical well; exact read IDs and UMI strings are counted within that cell. The [full selected table](../../../../source_data/figure_05/splitseq_reads_umis_568.tsv) contains the complete 568-cell counts.','','## Physical-cell identities','','| Original Prism row | Published ID | Canonical RT_BC2_BC3 | Sample |','|---|---|---|---|']
    lines += ['| '+' | '.join(row[k] for k in ['prism_row_1based','published_cell_barcode','canonical_barcode','sample'])+' |' for row in cells]
    non10=next(x for x in selected if len(x['umi'])!=10)
    lines += ['','## UMI inclusion','','| Original RAD read | Saved normalized barcode | Canonical physical cell | Exact UMI | Bases |','|---|---|---|---|---|',
              '| '+' | '.join([non10['read_id'],non10['normalized_barcode'],canonical(non10['normalized_barcode']),non10['umi'],str(len(non10['umi']))])+' |',
              '', 'This nine-base UMI passes the nonempty-UMI inclusion rule and contributes to both the read and exact-UMI counts.',
              '', 'The eight RAD example rows give five read–cell pairs for the first cell and three for the second; see [example counts](rad_bounded_counts.tsv).']
    lines += ['','Follow [Figure 5](../../../../docs/figure_05.md) for exact normalization and aggregation commands.']
    (a.output/'PREVIEW.md').write_text('\n'.join(lines)+'\n')
    print('Extracted assignment examples with physical-cell identities and source row numbers.')


if __name__=='__main__':main()
