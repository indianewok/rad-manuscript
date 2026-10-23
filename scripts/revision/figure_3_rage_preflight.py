#!/usr/bin/env python3
"""Validate the full shared RAGE input and make a small parser/producer pilot."""
import argparse,gzip,json,subprocess
from pathlib import Path
from figure_3 import ROOT,sha,js
from figure_3_fastq_identity import fingerprint

def main():
    base=ROOT/'checkpoints/figure_03/rage_matched';m=json.loads((base/'experiment.json').read_text());raw=Path(m['input'])
    counts=base/'counts';counts.mkdir(exist_ok=True)
    identity=fingerprint(raw,counts/'input_id_validation.json',counts/'input_original_ids.txt.gz')
    if identity['status']!='passed' or identity['records']!=m['expected_input_reads'] or identity['sequence_bases']!=m['expected_input_sequence_bases']:raise ValueError('Complete input count, bases or physical-ID uniqueness failed')
    if identity['canonical_record_sha256']!=m['expected_input_canonical_record_sha256']:raise ValueError('Input differs in ordered physical IDs, sequences or qualities; public files must be reconstructed into the selected order first')
    with gzip.open(raw,'rt') as source,gzip.open(base/'inputs/pilot_10000.fastq.gz','wt') as out:
        for _ in range(10000):
            for _ in range(4):out.write(source.readline())
    report=dict(status='passed',source=str(raw),compressed_sha256=identity['compressed_sha256'],bytes=raw.stat().st_size,mtime_ns=raw.stat().st_mtime_ns,physical_reads=identity['records'],sequence_bases=identity['sequence_bases'],canonical_record_sha256=identity['canonical_record_sha256'],identity_mode='selected compressed bytes' if identity['compressed_sha256']==m['expected_input_sha256'] else 'verified equivalent ordered records with different compression/header descriptions',parser='complete canonical ordered physical-ID/sequence/quality verification; unique input IDs; FASTQ lengths',pilot_sha256=sha(base/'inputs/pilot_10000.fastq.gz'))
    js(base/'input_validation.json',report);js(ROOT/'validation/figure_3_rage_input.json',report)
    print(json.dumps(report))
if __name__=='__main__':main()
