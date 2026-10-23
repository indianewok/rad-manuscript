#!/usr/bin/env python3
"""Count distinct reads and exact UMIs per physical cell from selected ledgers.

RT primer variants from the same well map to that well's T-primer sequence.
The executed inclusion rule requires a nonempty UMI, not a ten-base UMI.
"""
import argparse
import collections
import csv
import gzip
import hashlib
import json
import statistics
from pathlib import Path


def read_table(path):
    op = gzip.open if path.suffix == '.gz' else open
    with op(path, 'rt') as handle:
        yield from csv.DictReader(handle, delimiter=',' if '.csv' in path.name else '\t')


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def aggregate(assignments, cells_path, rt_path, kind):
    cells=list(read_table(cells_path))
    by_key={r['canonical_barcode']:r for r in cells}
    if len(by_key)!=len(cells):raise ValueError('Duplicate physical-cell keys')
    rt=list(read_table(rt_path))
    t_primer={r['well']:r['sequence'].strip() for r in rt if r['type']=='T'}
    primer={r['sequence'].strip():t_primer[r['well']] for r in rt}
    if len(primer)!=96 or len(t_primer)!=48:raise ValueError('Expected 96 RT primers in 48 physical wells')
    reads={key:set() for key in by_key};umis={key:set() for key in by_key}
    global_reads=set();published_reads=set();counts=collections.Counter()
    for row in read_table(assignments):
        counts['assignment_rows']+=1
        rid=row['read_id']
        if not rid.startswith('SRR13948564.') or not rid[12:].isdigit():
            raise ValueError('Unexpected original read ID: '+rid)
        read_number=int(rid[12:]);global_reads.add(read_number)
        observed=row['normalized_barcode'] if kind=='rad' else row['barcode']
        umi=row['umi']
        if not observed or not umi:
            counts['empty_barcode_or_umi']+=1;continue
        parts=observed.split('_')
        if len(parts)!=3 or parts[0] not in primer:
            counts['unmappable_rt_primer']+=1;continue
        cell='_'.join([primer[parts[0]],parts[1],parts[2]])
        if cell not in by_key:
            counts['outside_published_cells']+=1;continue
        counts['published_assignment_rows']+=1
        counts['published_full_10nt_umi_rows' if len(umi)==10 else 'published_other_umi_length_rows']+=1
        reads[cell].add(read_number);umis[cell].add(umi);published_reads.add(read_number)
    result=[dict(prism_row_1based=r['prism_row_1based'],published_cell_barcode=r['published_cell_barcode'],
                 canonical_barcode=r['canonical_barcode'],sample=r['sample'],
                 reads=len(reads[r['canonical_barcode']]),umis=len(umis[r['canonical_barcode']])) for r in cells]
    summary=dict(counts,unique_source_reads=len(global_reads),published_cells=len(cells),
                 published_cells_with_reads=sum(bool(v) for v in reads.values()),
                 published_unique_source_reads=len(published_reads),
                 read_cell_pairs=sum(map(len,reads.values())),cell_umi_pairs=sum(map(len,umis.values())),
                 median_reads=statistics.median(map(len,reads.values())),median_umis=statistics.median(map(len,umis.values())))
    return result,summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--assignments',type=Path,required=True)
    p.add_argument('--cells',type=Path,required=True)
    p.add_argument('--rt-primers',type=Path,required=True)
    p.add_argument('--format',choices=('rad','component'),required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();result,summary=aggregate(a.assignments,a.cells,a.rt_primers,a.format)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(result[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(result)
    report=dict(status='completed aggregation; compare with selected checkpoint',tool=a.format,
                summary=summary,code_sha256=sha(Path(__file__)),
                inputs=[dict(path=str(x),sha256=sha(x)) for x in [a.assignments,a.cells,a.rt_primers]],
                output_sha256=sha(a.output),raw_demultiplexing_rerun=False,
                unit='distinct read IDs and exact UMI strings within each canonical cell; sums are cell pairs')
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(summary))


if __name__=='__main__':main()
