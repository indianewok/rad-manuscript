#!/usr/bin/env python3
"""Run and score one full-input RAD 4acbe00 barcode scan at error0.3.

The dataset JSON supplies its real adapter, margins, catalogue and reference.
Use a fresh output directory. This script never submits scheduler jobs. Unknown
input hashes are computed once and recorded; known hashes must match exactly.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
import sys
import time

from build_rad import verify_build
from score_scan import (RAD_COMMIT, file_stat, input_digests, load_record, read_json,
                        require, reference_identity, score, sha, validate_input_receipt, write_json)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-record', type=Path, required=True)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--rad', type=Path, required=True)
    parser.add_argument('--catalogue', type=Path, required=True)
    parser.add_argument('--rad-source', type=Path, required=True, help='Clean checkout at the exact Figure4 source commit')
    parser.add_argument('--rad-build-receipt', type=Path, required=True, help='Receipt written by build_rad.py')
    parser.add_argument('--rad-sha256', help='Optional additional pin for your compiled executable')
    parser.add_argument('--threads', type=int, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--input-receipt', type=Path,
                        help='Passed staging SHA/size receipt with output and file_stat fields; otherwise hash input now')
    args = parser.parse_args()
    record = load_record(args.dataset_record)
    raw, rad, catalogue = args.input.resolve(), args.rad.resolve(), args.catalogue.resolve()
    output = args.output_dir.resolve()
    require(args.threads > 0, 'Threads must be positive')
    reference_identity(Path(record['reference_path']).expanduser().resolve(), record)
    require(stat.S_ISREG(raw.stat().st_mode),
            'Input must be a complete regular file; FIFO streaming requires a separately verified contract')
    if record.get('input_format'):
        with raw.open('rb') as handle:
            actual_format = 'fastq.gz' if handle.read(2) == b'\x1f\x8b' else 'fastq'
        require(actual_format == record['input_format'], 'Input format differs from the accepted FASTQ representation')
    build = verify_build(rad, args.rad_source, args.rad_build_receipt, args.rad_sha256)
    require(sha(catalogue) == record['catalogue_sha256'], 'Catalogue differs from the dataset profile')
    require(shutil.which('pigz') is not None, 'pigz must be available on PATH')
    require(not output.exists(), 'Output directory must be new')
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/'dataset_record.json', record)
    shutil.copyfile(args.rad_build_receipt, output/'rad_build_receipt.json')
    started = time.monotonic()
    state = dict(status='validating_input', dataset_id=record['dataset_id'],
                 started_utc=datetime.now(timezone.utc).isoformat())

    def save_state(**values):
        state.update(values, updated_utc=datetime.now(timezone.utc).isoformat())
        temporary = output/'state.json.tmp'
        temporary.write_text(json.dumps(state, indent=2)+'\n')
        temporary.replace(output/'state.json')

    save_state()
    try:
        before_hash = file_stat(raw)
        if args.input_receipt:
            receipt = read_json(args.input_receipt)
            validate_input_receipt(receipt, record, raw)
            require(receipt.get('file_stat') == before_hash,
                    'Staging receipt file_stat differs from the current input; revalidate its bytes')
            input_identity = dict(receipt, verification_basis='Passed staging digest with matching current file_stat',
                                  original_receipt_path=str(args.input_receipt.resolve()),
                                  original_receipt_sha256=sha(args.input_receipt))
        else:
            digests = input_digests(raw)
            require(file_stat(raw) == before_hash, 'Input changed while its SHA256 was computed')
            input_identity = dict(status='passed', output=str(raw), bytes=before_hash['size'], **digests,
                                  file_stat=before_hash, verification_basis='Complete regular-file SHA256 before native scan')
            validate_input_receipt(input_identity, record, raw)
        write_json(output/'input_receipt.json', input_identity)
        prefix = output/'rad'
        command = [str(rad), 'scan-wl', '--input', str(raw), '--output-prefix', str(prefix),
                   '--adapter_seq', record['adapter_seq'], '--barcode-length', str(record['barcode_length']),
                   '--left-margin', str(record['left_margin']), '--right-margin', str(record['right_margin']),
                   '--max-error', '0.3', '--whitelist', str(catalogue), '--threads', str(args.threads),
                   '--chunk-size', '10000']
        write_json(output/'command.json', command)
        (output/'command.sh').write_text('#!/usr/bin/env bash\n'+shlex.join(command)+'\n')
        env = os.environ.copy()
        for key in ['RAD_NO_PIGZ', 'RAD_PIGZ', 'OMP_THREAD_LIMIT']:
            env.pop(key, None)
        env.update(OMP_NUM_THREADS=str(args.threads), OMP_DYNAMIC='FALSE', OMP_MAX_ACTIVE_LEVELS='1',
                   OMP_PROC_BIND='FALSE', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', LC_ALL='C')
        write_json(output/'environment.json', {key:env.get(key) for key in
            ['OMP_NUM_THREADS','OMP_DYNAMIC','OMP_MAX_ACTIVE_LEVELS','OMP_PROC_BIND','OPENBLAS_NUM_THREADS',
             'MKL_NUM_THREADS','LC_ALL','RAD_NO_PIGZ','RAD_PIGZ','OMP_THREAD_LIMIT']})
        before_scan = file_stat(raw)
        save_state(status='scanning', command=command)
        scan_started = time.monotonic()
        with (output/'stdout.log').open('x') as out, (output/'stderr.log').open('x') as err:
            result = subprocess.run(['/usr/bin/time', '-v', '-o', str(output/'time.txt'), *command],
                                    stdout=out, stderr=err, env=env)
        scan_seconds = time.monotonic()-scan_started
        require(result.returncode == 0, 'Native RAD exit '+str(result.returncode))
        require(file_stat(raw) == before_scan == before_hash, 'Input changed during the native scan')
        write_json(output/'native_success.json', dict(status='passed', native_exit_code=0,
            input_stat_unchanged=True, input_file_stat=before_scan, scan_wall_seconds=scan_seconds,
            rad_commit=RAD_COMMIT, rad_sha256=build['rad_sha256'],
            rad_source_path=str(args.rad_source.resolve()),
            rad_build_receipt_sha256=sha(output/'rad_build_receipt.json'), command_sha256=sha(output/'command.json'),
            input_receipt_sha256=sha(output/'input_receipt.json'), runner_sha256=sha(__file__),
            output_sha256={path.name:sha(path) for path in [output/'time.txt', output/'stderr.log',
                          Path(str(prefix)+'_scan_wl.log'), Path(str(prefix)+'.txt')]}))
        save_state(status='scoring', native_exit_code=0, scan_wall_seconds=scan_seconds)
        metrics = score(output/'dataset_record.json', output, output/'score')
        save_state(status='complete', metrics=metrics, total_wall_seconds=time.monotonic()-started,
                   completed_utc=datetime.now(timezone.utc).isoformat())
        print(json.dumps(metrics, indent=2))
    except BaseException as error:
        save_state(status='failed', error_type=type(error).__name__, error=str(error))
        raise


if __name__ == '__main__':
    main()
