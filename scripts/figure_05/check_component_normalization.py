#!/usr/bin/env python3
"""Verify every selected native component record against its saved normalized row."""
import argparse
import itertools
import json
from pathlib import Path
from aggregate_splitseq import read_table, sha
from normalize_component_stats import COMPLEMENT


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native',type=Path,required=True)
    p.add_argument('--normalized',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();n=0
    for n,(native,row) in enumerate(itertools.zip_longest(read_table(a.native),read_table(a.normalized)),1):
        if native is None or row is None:raise ValueError('Different native and normalized row counts')
        expected=dict(read_id=native['Read'],barcode='_'.join([native['BC3'],native['BC2'],native['BC1']]),
            umi=native['UB'].translate(COMPLEMENT)[::-1],orientation='',flank_edit_distance=native['FlankEditDist'])
        if row!=expected:raise ValueError('Native-to-normalized mismatch at data row '+str(n))
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(dict(status='passed',rows_compared=n,mismatches=0,
        native_sha256=sha(a.native),normalized_sha256=sha(a.normalized),code_sha256=sha(Path(__file__)),
        rule='Read copied; BC3_BC2_BC1; reverse-complement UB; empty orientation; FlankEditDist copied',
        raw_demultiplexing_rerun=False),indent=2)+'\n')
    print(f'Passed: all {n} native component records exactly match saved normalized assignments.')


if __name__=='__main__':main()
