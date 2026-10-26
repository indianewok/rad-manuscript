#!/usr/bin/env python3
"""Reapply the exact diagnostic patch, build, and test unfiltered equivalence.

Requires only Python 3, patch, and a C++11 compiler. No network is used.
Outputs go to --output, never into the pinned source directories.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build')
    parser.add_argument('--cxx', default='g++')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    for row in manifest['files']:
        assert sha(ROOT / row['path']) == row['sha256'], row['path']

    # Recover the modified source from the pristine upstream file plus the patch.
    patched = output / 'patched'
    patched.mkdir(exist_ok=True)
    shutil.copy2(str(ROOT / 'source/base/flexiplex.c++'), str(patched / 'flexiplex.c++'))
    subprocess.run(['patch', '-p1', '-i', str(ROOT / 'patches/raw_cell_barcode_audit.patch')],
                   cwd=str(patched), check=True)
    assert sha(patched / 'flexiplex.c++') == sha(ROOT / 'source/modified/flexiplex.c++')

    commands = []
    for name, source in [('pristine', ROOT / 'source/base/flexiplex.c++'),
                         ('audit', patched / 'flexiplex.c++')]:
        command = [args.cxx, str(source), '-Ofast', '-pthread', '-std=c++11',
                   '-o', str(output / name), str(ROOT / 'source/edlib-1.2.7/edlib.cpp'),
                   '-I', str(ROOT / 'source/edlib-1.2.7')]
        subprocess.run(command, check=True)
        commands.append(command)

    # A designed fixture tests exact, corrected, reverse-strand, and rejected reads.
    # Its known sequences are test assertions, never supplied as extraction truth.
    barcode = 'ACGTCAGTACGATCGA'
    mutant = 'TCGTCAGTACGATCGA'
    adapter = 'CTACACGACGCTCTTCCGATCT'
    umi = 'GACATCGTAGCA'
    payload = 'GCTACGATCAGCTAGCATCGATCGACTACGATCAGCTAGCATCGATCGACTACGATCAGC'
    sequence = adapter + barcode + umi + 'T' * 13 + payload
    rc = lambda seq: seq.translate(str.maketrans('ACGT', 'TGCA'))[::-1]
    reads = [('exact', sequence), ('corrected', adapter + mutant + umi + 'T' * 13 + payload),
             ('reverse', rc(sequence)), ('no_adapter', 'CGAC' * 40)]
    fastq = output / 'fixture.fastq'
    fastq.write_text(''.join('@{}\n{}\n+\n{}\n'.format(name, seq, 'I' * len(seq)) for name, seq in reads))
    targets = output / 'targets.txt'
    targets.write_text(barcode + '\n')
    env = os.environ.copy()
    env.pop('FLEXIPLEX_AUDIT_SOURCE_FILE', None)
    result = {}
    binary_paths = {'pristine': output / 'pristine', 'audit': output / 'audit',
                    'pinned': ROOT / 'bin/flexiplex_v1.02.6_raw_to_assigned_audit'}
    for name, binary in binary_paths.items():
        prefix = output / name
        argv = [str(binary), '-d', '10x3v3', '-f', '8', '-e', '2', '-p', '1',
                '-k', str(targets), '-n', str(prefix), str(fastq)]
        with (output / (name + '.fastq')).open('wb') as stdout, (output / (name + '.stderr')).open('wb') as stderr:
            subprocess.run(argv, env=env, stdout=stdout, stderr=stderr, check=True)
        table = output / (name + '_reads_barcodes.txt')
        with table.open() as handle:
            rows = list(csv.DictReader(handle, delimiter='\t'))
        result[name] = {'command': argv, 'binary_sha256': sha(binary), 'rows': rows,
                        'fastq_sha256': sha(output / (name + '.fastq'))}
    common = ['Read', 'CellBarcode', 'FlankEditDist', 'BarcodeEditDist', 'UMI']
    strip = lambda rows: sorted(tuple(row[key] for key in common) for row in rows)
    assert result['pristine']['fastq_sha256'] == result['audit']['fastq_sha256'] == result['pinned']['fastq_sha256']
    assert strip(result['pristine']['rows']) == strip(result['audit']['rows']) == strip(result['pinned']['rows'])
    assert len(result['audit']['rows']) == 3, result['audit']['rows']
    assert result['audit']['rows'] == result['pinned']['rows']
    observed = {row['Read']: row for row in result['audit']['rows']}
    assert observed['exact']['RawCellBarcode'] == barcode
    assert observed['reverse']['RawCellBarcode'] == barcode
    assert observed['corrected']['RawCellBarcode'] == mutant
    assert all(row['CellBarcode'] == barcode for row in observed.values())
    report = {'status': 'passed', 'scope': 'designed four-read fixture; not a full-data equivalence claim',
              'source_filter': 'unset', 'compiler': subprocess.check_output([args.cxx, '--version'], universal_newlines=True),
              'build_commands': commands, 'results': result}
    (output / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS: patch identity, three binaries, emitted FASTQ, common columns, and raw barcode extraction')


if __name__ == '__main__':
    main()
