#!/usr/bin/env python3
"""Compare every reconstructed selected-cell count and preserve count units."""
import argparse
import csv
import hashlib
import json
import statistics
from pathlib import Path


def read(path):
    with path.open() as f:return list(csv.DictReader(f,delimiter='\t'))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--expected',type=Path,required=True)
    p.add_argument('--rad-counts',type=Path,required=True)
    p.add_argument('--component-counts',type=Path,required=True)
    p.add_argument('--rad-report',type=Path,required=True)
    p.add_argument('--component-report',type=Path,required=True)
    p.add_argument('--input-reads',type=int,default=5764421)
    p.add_argument('--summary',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();expected=read(a.expected);by_key={r['canonical_barcode']:r for r in expected}
    if len(expected)!=568 or len(by_key)!=568:raise ValueError('Expected 568 unique paired cells')
    summaries=[];checks=[]
    for tool,counts_path,report_path,prefix in [('RAD',a.rad_counts,a.rad_report,'rad'),
                                              ('Component Flexiplex polyT',a.component_counts,a.component_report,'component_polyt')]:
        counts=read(counts_path);got={r['canonical_barcode']:r for r in counts}
        if len(counts)!=568 or set(got)!=set(by_key):raise ValueError('Cell identities differ: '+tool)
        for key,row in by_key.items():
            observed=got[key]
            for field in ['published_cell_barcode','prism_row_1based','sample']:
                if observed[field]!=row[field]:raise ValueError((tool,key,field))
            for field in ['reads','umis']:
                if int(observed[field])!=int(row[prefix+'_'+field]):raise ValueError((tool,key,field))
        report=json.loads(report_path.read_text());s=report['summary']
        if report['output_sha256']!=hashlib.sha256(counts_path.read_bytes()).hexdigest():
            raise ValueError('Aggregation report does not bind to these exact counts')
        if s['published_cells']!=568:raise ValueError('Aggregation report cell count')
        for field in ['reads','umis']:
            if s['median_'+field]!=statistics.median(int(x[field]) for x in counts):
                raise ValueError('Median differs from paired count table: '+field)
        if s['read_cell_pairs']!=sum(int(x['reads']) for x in counts):raise ValueError('Read-pair conservation')
        if s['cell_umi_pairs']!=sum(int(x['umis']) for x in counts):raise ValueError('UMI-pair conservation')
        summaries.append(dict(tool=tool,input_source_reads=a.input_reads,full_assignment_rows=s['assignment_rows'],
            full_unique_source_reads=s['unique_source_reads'],
            full_unique_source_read_percent=100*s['unique_source_reads']/a.input_reads,
            full_assignment_row_percent=100*s['assignment_rows']/a.input_reads,
            published_cells=s['published_cells'],published_assignment_rows=s['published_assignment_rows'],
            published_unique_source_reads=s['published_unique_source_reads'],
            read_cell_pairs=s['read_cell_pairs'],cell_umi_pairs=s['cell_umi_pairs'],
            median_reads=s['median_reads'],median_umis=s['median_umis']))
        checks.append(dict(tool=tool,paired_cells=568,read_counts_equal=568,umi_counts_equal=568,
                           report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest()))
    a.summary.parent.mkdir(parents=True,exist_ok=True)
    with a.summary.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(summaries[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(summaries)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(dict(status='passed',checks=checks,integer_counts_compared=2272,
        raw_demultiplexing_rerun=False,code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        expected_sha256=hashlib.sha256(a.expected.read_bytes()).hexdigest(),
        summary_sha256=hashlib.sha256(a.summary.read_bytes()).hexdigest(),
        counting='Within-cell distinct original-read IDs; within-cell distinct exact UMI strings. Sums are read-cell or cell-UMI pairs, not globally unique reads.',
        displayed_23p35_status='not reproduced: selected full-input unique-read and assignment-row fractions are reported separately; no silent replacement annotation'),indent=2)+'\n')
    print('Passed: all 2272 selected read/UMI counts, all568 cell identities and complete source-row accounting.')


if __name__=='__main__':main()
