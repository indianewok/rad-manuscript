#!/usr/bin/env python3
"""Rescore deposited public identifier sets and label aggregate-only input rows."""
import argparse
import csv
import gzip
import hashlib
import re
from pathlib import Path


def table(path):
    with path.open() as handle:return list(csv.DictReader(handle, delimiter='\t'))


def read_set(root, path, expected_sha):
    source = root / path
    if hashlib.sha256(source.read_bytes()).hexdigest() != expected_sha:
        raise ValueError('Source hash mismatch: '+path)
    with gzip.open(source, 'rt') as handle:values = [x.rstrip('\n') for x in handle]
    if values != sorted(set(values)) or not all(re.fullmatch('[ACGT]{16}',x) for x in values):
        raise ValueError('Expected sorted unique 16nt identifiers: '+path)
    return set(values)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--manifest', type=Path, default=Path('data/figure_04/identifier_manifest.tsv'))
    parser.add_argument('--expected', type=Path, default=Path('source_data/figure_04/barcode_detection_metrics.tsv'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    expected = table(args.root / args.expected)
    manifest = table(args.root / args.manifest)
    index = {(r['canonical_id'],r['tool']):r for r in manifest}
    expected_keys = {(r['canonical_id'],r['tool']) for r in expected}
    if len(expected_keys)!=111 or len(index)!=111 or len(manifest)!=111 or set(index)!=expected_keys:
        raise ValueError('Manifest and selected table must contain the same 37 inputs × three tools')
    inputs={sample for sample,tool in expected_keys}
    if len(inputs)!=37 or expected_keys!={(sample,tool) for sample in inputs for tool in ('RAD','BLAZE','Flexiplex')}:
        raise ValueError('Every one of the 37 inputs must have all three tools')
    result=[]
    for row in expected:
        sample, tool = row['canonical_id'], row['tool']
        source = index[sample,tool]
        if source['status']=='public-identifiers-recomputed':
            calls=read_set(args.root,source['callset_path'],source['callset_sha256'])
            truth=read_set(args.root,source['reference_path'],source['reference_sha256'])
            tp,fp,fn=len(calls&truth),len(calls-truth),len(truth-calls)
            values=dict(calls=len(calls),reference_n=len(truth),tp=tp,fp=fp,fn=fn,
                        precision=tp/len(calls),recall=tp/len(truth),f1=2*tp/(2*tp+fp+fn))
            for field,value in values.items():
                if abs(value-float(row[field]))>1e-9:raise ValueError((sample,tool,field,value,row[field]))
        elif source['status']=='aggregate-only-controlled-access':
            values={field:int(row[field]) for field in ('calls','reference_n','tp','fp','fn')}
            values.update({field:float(row[field]) for field in ('precision','recall','f1')})
        else:raise ValueError('Unknown row status: '+source['status'])
        result.append(dict(canonical_id=sample,tool=tool,**values,status=source['status']))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(result[0]),delimiter='\t',lineterminator='\n')
        writer.writeheader();writer.writerows(result)
    rescored=sum(r['status']=='public-identifiers-recomputed' for r in result)
    print(f'Counts exact, metrics within 1e-9: {rescored} public rows recomputed; {len(result)-rescored} controlled rows retained as aggregates.')


if __name__=='__main__':main()
