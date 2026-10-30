#!/usr/bin/env python3
"""Verify the preserved FLAMES configurations and their source-file hashes."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

META = 'source_data/pinned_flames_configs'
F5 = 'source_data/figure_05/provenance/flames_paper_snapshot'
F6 = 'source_data/figure_06/provenance/flames_alignment_snapshot'


def scalar(value):
    return value[0] if isinstance(value, list) and len(value) == 1 else value


def verify(root):
    with (root / META / 'files.tsv').open() as handle:
        rows = list(csv.DictReader(handle, delimiter='\t'))
    paths = [row['path'] for row in rows]
    if not rows or len(set(paths)) != len(paths):
        raise ValueError('The source manifest is empty or has duplicate paths')
    for row in rows:
        path = (root / row['path']).resolve()
        path.relative_to(root)
        data = path.read_bytes()
        if len(data) != int(row['bytes']):
            raise ValueError('Changed file length: ' + row['path'])
        if hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Changed SHA-256: ' + row['path'])
        blob = b'blob ' + str(len(data)).encode() + b'\0' + data
        if hashlib.sha1(blob).hexdigest() != row['git_blob_sha1']:
            raise ValueError('Changed Git blob: ' + row['path'])
    actual = set()
    for folder in [F5, F6, META]:
        for path in (root / folder).rglob('*'):
            if path.is_file() and path.name not in ['files.tsv', 'SHA256SUMS', '.DS_Store'] and '__pycache__' not in path.parts:
                actual.add(str(path.relative_to(root)))
    expected = {p for p in paths if any(p.startswith(folder + '/') for folder in [F5, F6, META])}
    if actual != expected:
        raise ValueError('Snapshot file inventory changed: ' + repr(sorted(actual ^ expected)))
    checksums = (root / META / 'SHA256SUMS').read_text().splitlines()
    if checksums != [row['sha256'] + '  ' + row['path'] for row in rows]:
        raise ValueError('The two checksum manifests disagree')

    paper = root / F5 / 'upstream/ChangqingW_FLAMES_figures/files'
    component = json.loads((paper / 'config_splitseq.json').read_text())['barcode_parameters']
    segments = component['segments']
    matched = [s for s in segments if s['type'] == 'MATCHED']
    if len(matched) != 3 or any(s['max_edit_distance'] != 1 or s['buffer_size'] != 1 for s in matched):
        raise ValueError('The preserved paper component configuration is not ED1/buffer1')
    if scalar(component['max_flank_editdistance']) != 3:
        raise ValueError('Unexpected paper component flank limit')
    if not any(s.get('name') == 'polyT' and s.get('pattern') == 'TTTTTTTT' for s in segments):
        raise ValueError('Missing paper terminal T8 segment')
    whole = json.loads((paper / 'config_splitseq_bc.json').read_text())['barcode_parameters']
    if scalar(whole['max_flank_editdistance']) != 10:
        raise ValueError('Unexpected complete-cell configuration flank limit')
    if len([s for s in whole['segments'] if s['type'] == 'MATCHED_SPLIT']) != 3:
        raise ValueError('Unexpected complete-cell barcode segment types')
    for folder, polyt in [('flexiplex_ed2_native', True), ('flexiplex_no_polyt_ed2_native', False)]:
        text = (root / F5 / 'executed' / folder / 'run_native_ed2.R').read_text()
        if text.count('max_edit_distance=2') != 3 or ('"TTTTTTTT"' in text) != polyt:
            raise ValueError('Unexpected executed ED2 layout: ' + folder)

    path = root / F6 / 'upstream/LongBench_workflow_37a9506df7bcd92c488c0e4b2a5cbe09fa1fc19d/sub_workflows/lr_sc_sn/config/flames_genome_map.json'
    config = json.loads(path.read_text())
    pipeline = config['pipeline_parameters']
    if scalar(pipeline['threads']) != 32 or scalar(pipeline['seed']) != 2023:
        raise ValueError('Figure 6 is not the executed seed/thread configuration')
    if scalar(pipeline['do_genome_alignment']) is not True or scalar(pipeline['do_barcode_demultiplex']) is not False:
        raise ValueError('Unexpected Figure 6 active stages')
    if hashlib.sha256(path.read_bytes()).hexdigest() != '18dcabed08851f25a2bf7fdf361eaa1ea238afe32e506491d3582fe92d64b2a2':
        raise ValueError('Figure 6 configuration differs from the execution-manifest hash')
    return dict(status='PASS', files_verified=len(rows), bytes_verified=sum(int(r['bytes']) for r in rows),
                source_file_inventory_verified=True, configuration_roles_verified=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.root.resolve())
    except Exception as error:
        result = dict(status='FAIL', error=str(error))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
