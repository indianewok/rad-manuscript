#!/usr/bin/env python3
"""Restore a public FASTQ to a verified original-read order and check every payload.

Requires Python 3, GNU sort and pigz. No RAD/BLAZE/Flexiplex analysis is run.
The selected order and fingerprint must come from figure_3_fastq_identity.py.
Only a complete canonical match publishes the output; descriptions and plus-line
annotations may differ and are separately covered by the exact-byte digest.
"""
import argparse
import base64
import contextlib
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import socket
import subprocess
import sys
import tempfile
import time


def file_hashes(path):
    md5, sha = hashlib.md5(), hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b''):
            md5.update(block)
            sha.update(block)
    return dict(md5=md5.hexdigest(), sha256=sha.hexdigest(), bytes=path.stat().st_size)


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.partial.' + str(os.getpid()))
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def record_parts(lines, number):
    header, sequence_line, plus, quality_line = lines
    sequence = sequence_line.rstrip(b'\r\n')
    quality = quality_line.rstrip(b'\r\n')
    if (not header.startswith(b'@') or not plus.startswith(b'+') or
            not quality_line or len(sequence) != len(quality)):
        raise ValueError('Malformed four-line FASTQ record {}'.format(number))
    words = header[1:].split()
    if not words:
        raise ValueError('Empty read ID at record {}'.format(number))
    return words[0], sequence, quality


def stop(process):
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def run(args):
    started = time.time()
    receipt = dict(status='running', started_utc=datetime.datetime.utcnow().isoformat() + 'Z',
                   host=socket.gethostname(), argv=sys.argv,
                   script_sha256=file_hashes(Path(__file__))['sha256'],
                   public_input=str(args.public.resolve()), selected_order=str(args.order.resolve()),
                   selected_identity=str(args.identity.resolve()), output=str(args.output.resolve()) if args.output else None,
                   mode='verify_only' if args.verify_only else 'reconstruct_and_verify',
                   raw_tools_rerun=False)
    temporary_output = args.output.with_name(args.output.name + '.partial.' + str(os.getpid())) if args.output else None
    sort_process = decompress = compress = None
    try:
        receipt['software'] = dict(python=sys.version,
            sort=subprocess.check_output(['sort', '--version'], stderr=subprocess.STDOUT).decode().splitlines()[0],
            pigz=subprocess.check_output(['pigz', '--version'], stderr=subprocess.STDOUT).decode().splitlines()[0])
        receipt['scheduler'] = {key: os.environ[key] for key in ('SLURM_JOB_ID', 'SLURM_JOB_PARTITION', 'SLURM_CPUS_PER_TASK', 'SLURMD_NODENAME') if key in os.environ}
        if args.output and args.output.exists():
            raise ValueError('Output already exists; inspect its receipt instead of overwriting it')
        identity = json.loads(args.identity.read_text())
        if identity['status'] != 'passed' or identity['duplicate_original_ids'] != 0:
            raise ValueError('Selected identity receipt must establish unique original read IDs')
        if identity['records'] != identity['unique_original_ids']:
            raise ValueError('Selected identity record/unique-ID counts disagree')
        expected_count = int(identity['records'])
        if len(identity['canonical_record_sha256']) != 64:
            raise ValueError('Selected canonical SHA-256 is malformed')
        receipt['selected_identity_sha256'] = file_hashes(args.identity)['sha256']
        receipt['selected_order_hashes'] = file_hashes(args.order)
        if receipt['selected_order_hashes']['sha256'] != identity['input_ids_sha256']:
            raise ValueError('Selected-order compressed SHA-256 differs from its identity receipt')
        receipt['public_input_hashes'] = file_hashes(args.public)
        if args.acquisition_report:
            acquisition = json.loads(args.acquisition_report.read_text())
            if acquisition['status'] != 'passed':
                raise ValueError('Public acquisition report has not passed')
            for key in ('bytes', 'md5', 'sha256'):
                if receipt['public_input_hashes'][key] != acquisition[key]:
                    raise ValueError('Public input differs from acquisition receipt: ' + key)
            receipt['acquisition_report_sha256'] = file_hashes(args.acquisition_report)['sha256']
        receipt['phase_seconds'] = {'input_hashes_and_receipts': round(time.time() - started, 3)}
        public_stat = args.public.stat()
        args.scratch.mkdir(parents=True, exist_ok=True)
        free_bytes = shutil.disk_usage(str(args.scratch)).free
        receipt['temporary_disk_free_bytes_before'] = free_bytes
        if free_bytes < args.min_temp_free_bytes:
            raise ValueError('Insufficient temporary space: {} bytes free'.format(free_bytes))
        ranks = {}
        load_started = time.time()
        id_order = hashlib.sha256()
        with gzip.open(str(args.order), 'rb') as handle:
            for rank, line in enumerate(handle):
                rid = line.rstrip(b'\r\n')
                if not rid or any(c in rid for c in (b' ', b'\t', b'\r', b'\n')):
                    raise ValueError('Malformed selected-order ID at line {}'.format(rank + 1))
                if rid in ranks:
                    raise ValueError('Duplicate selected-order ID: ' + repr(rid))
                ranks[rid] = rank
                id_order.update(rid + b'\n')
        if len(ranks) != expected_count or id_order.hexdigest() != identity['original_id_order_sha256']:
            raise ValueError('Selected-order count or ordered-ID SHA-256 differs from identity receipt')
        receipt['phase_seconds']['load_selected_order'] = round(time.time() - load_started, 3)
        print(json.dumps(dict(stage='selected_order_loaded', records=len(ranks))), flush=True)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        sort_log = args.report.with_name(args.report.stem + '.sort.stderr.log')
        pigz_log = args.report.with_name(args.report.stem + '.pigz.stderr.log')
        receipt['diagnostic_logs'] = {'sort': str(sort_log), 'pigz': str(pigz_log)}
        with tempfile.TemporaryDirectory(prefix='rage_fastq_order_', dir=str(args.scratch)) as tmp:
            tmp = Path(tmp)
            environment = dict(os.environ, LC_ALL='C')
            sort_command = ['sort', '--parallel=' + str(args.sort_threads),
                            '--buffer-size=' + args.sort_memory, '--temporary-directory=' + str(tmp),
                            '-t', '\t', '-k1,1']
            receipt['sort_command'] = sort_command
            receipt['pigz_threads'] = args.pigz_threads
            with sort_log.open('wb') as sort_error, pigz_log.open('wb') as pigz_error:
                sort_process = subprocess.Popen(sort_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                                stderr=sort_error, env=environment)
                decompress = subprocess.Popen(['pigz', '-dc', '-p', str(args.pigz_threads), str(args.public)],
                                               stdout=subprocess.PIPE, stderr=pigz_error)
                public_records = 0
                indexing_started = time.time()
                while True:
                    header = decompress.stdout.readline()
                    if not header:
                        break
                    lines = (header, decompress.stdout.readline(), decompress.stdout.readline(), decompress.stdout.readline())
                    rid, sequence, quality = record_parts(lines, public_records + 1)
                    rank = ranks.pop(rid, None)
                    if rank is None:
                        raise ValueError('Duplicate public ID or ID outside selected order: ' + repr(rid))
                    encoded = base64.b64encode(b''.join(lines))
                    sort_process.stdin.write(('{:020d}\t'.format(rank)).encode('ascii') + encoded + b'\n')
                    public_records += 1
                    if public_records % 5000000 == 0:
                        print(json.dumps(dict(stage='public_records_indexed', records=public_records)), flush=True)
                if decompress.wait() != 0:
                    raise ValueError('Public gzip decompression or CRC check failed')
                decompress.stdout.close()
                if ranks:
                    raise ValueError('Public FASTQ is missing {} selected IDs'.format(len(ranks)))
                del ranks
                if public_records != expected_count:
                    raise ValueError('Public FASTQ record count differs from selected input')
                sort_process.stdin.close()
                receipt['phase_seconds']['index_public_records_and_sort_runs'] = round(time.time() - indexing_started, 3)
                print(json.dumps(dict(stage='public_ID_set_verified', records=public_records)), flush=True)
                canonical, exact, sequence_quality, ordered_ids = (hashlib.sha256() for _ in range(4))
                records = bases = 0
                reconstruction_started = time.time()
                with contextlib.ExitStack() as output_stack:
                    if not args.verify_only:
                        destination = output_stack.enter_context(temporary_output.open('wb'))
                        compress = subprocess.Popen(['pigz', '-n', '-6', '-p', str(args.pigz_threads), '-c'],
                                                    stdin=subprocess.PIPE, stdout=destination, stderr=pigz_error)
                    for line in sort_process.stdout:
                        rank_text, encoded = line.rstrip(b'\n').split(b'\t', 1)
                        if int(rank_text) != records:
                            raise ValueError('Sorted rank is missing, repeated or out of order')
                        raw = base64.b64decode(encoded, validate=True)
                        lines = raw.splitlines(keepends=True)
                        if len(lines) != 4:
                            raise ValueError('Encoded FASTQ did not preserve exactly four lines')
                        rid, sequence, quality = record_parts(lines, records + 1)
                        payload = len(sequence).to_bytes(8, 'big') + sequence + quality
                        canonical.update(len(rid).to_bytes(8, 'big') + rid + payload)
                        sequence_quality.update(payload)
                        ordered_ids.update(rid + b'\n')
                        exact.update(raw)
                        if compress:
                            compress.stdin.write(raw)
                        records += 1
                        bases += len(sequence)
                        if records % 5000000 == 0:
                            print(json.dumps(dict(stage='ordered_records_verified', records=records)), flush=True)
                    if sort_process.wait() != 0:
                        raise ValueError('External sort failed; inspect ' + str(sort_log))
                    sort_process.stdout.close()
                    if compress:
                        compress.stdin.close()
                        if compress.wait() != 0:
                            raise ValueError('Output gzip compression failed')
                comparisons = dict(records=records, sequence_bases=bases,
                                   canonical_record_sha256=canonical.hexdigest(),
                                   sequence_quality_order_sha256=sequence_quality.hexdigest(),
                                   original_id_order_sha256=ordered_ids.hexdigest())
                receipt['reconstructed_identity'] = dict(comparisons,
                    exact_decompressed_fastq_sha256=exact.hexdigest())
                for key, observed in comparisons.items():
                    if observed != identity[key]:
                        raise ValueError('Reconstructed selected identity mismatch: ' + key)
                after_stat = args.public.stat()
                if (after_stat.st_size, after_stat.st_mtime_ns) != (public_stat.st_size, public_stat.st_mtime_ns):
                    raise ValueError('Public input changed during reconstruction')
                receipt['exact_decompressed_fastq_matches_selected'] = exact.hexdigest() == identity['exact_decompressed_fastq_sha256']
                receipt['metadata_scope'] = ('Canonical comparison covers every ordered physical read ID, sequence and quality; '
                    'header descriptions and plus-line annotations are excluded. The exact decompressed digest covers the '
                    'original public record bytes in selected order, including metadata, whether or not a FASTQ is written.')
                receipt['phase_seconds']['merge_verify_and_optional_compression'] = round(time.time() - reconstruction_started, 3)
                if not args.verify_only:
                    output_hash_started = time.time()
                    receipt['output_hashes'] = file_hashes(temporary_output)
                    receipt['phase_seconds']['output_compressed_hashes'] = round(time.time() - output_hash_started, 3)
                    temporary_output.replace(args.output)
                receipt['status'] = 'passed'
                receipt['complete_unique_ID_set_and_payload_identity'] = True
                receipt['full_ordered_stream_verified'] = True
                receipt['full_fastq_written'] = not args.verify_only
                receipt['completed_utc'] = datetime.datetime.utcnow().isoformat() + 'Z'
                receipt['elapsed_seconds'] = round(time.time() - started, 3)
                receipt['python_peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                receipt['largest_child_peak_rss_kib'] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
                save_json(args.report, receipt)
                print(json.dumps(receipt), flush=True)
                return receipt
    except BaseException as error:
        stop(decompress)
        stop(sort_process)
        stop(compress)
        if temporary_output and temporary_output.exists():
            temporary_output.unlink()
        receipt.update(status='failed', error=str(error), elapsed_seconds=round(time.time() - started, 3))
        save_json(args.report, receipt)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public', type=Path, required=True, help='Public gzip-compressed four-line FASTQ')
    parser.add_argument('--order', type=Path, required=True, help='Verified selected-order original IDs, one per line, gzip')
    parser.add_argument('--identity', type=Path, required=True, help='Selected figure_3_fastq_identity.py JSON receipt')
    parser.add_argument('--acquisition-report', type=Path, help='Require input MD5/SHA/byte agreement with download receipt')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--output', type=Path, help='Write and atomically publish the verified gzip FASTQ')
    mode.add_argument('--verify-only', action='store_true', help='Verify the complete sorted stream without writing a FASTQ')
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True, help='Temporary external-sort directory, preferably node local')
    parser.add_argument('--sort-threads', type=int, default=3)
    parser.add_argument('--sort-memory', default='6G')
    parser.add_argument('--pigz-threads', type=int, default=2)
    parser.add_argument('--min-temp-free-bytes', type=int, default=100000000000)
    args = parser.parse_args()
    if min(args.sort_threads, args.pigz_threads) < 1:
        parser.error('Thread counts must be positive')
    run(args)


if __name__ == '__main__':
    main()
