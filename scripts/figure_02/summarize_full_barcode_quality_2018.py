#!/usr/bin/env python3
"""Recover exact Nanopore2018 barcode qualities from one retained shifted FASTQ.

The selected model supports Q1..28; every original positive shift was unclipped.
Subtract the known input shift exactly, then count with the unchanged locator.
No quality sampling, nucleotide simulation or BLAZE execution is performed.
"""
import argparse
import collections
from concurrent.futures import ProcessPoolExecutor
import csv
import datetime
import gzip
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import socket
import sys
import time

import barcode_locator as locator

SHIFTS = [1, 2, 3, 4, 5, 6, 8, 10, 11, 12, 13, 0]
ORIGINAL_2018_GENERATOR = 'LongBench_comps/ScTagger_quality_sweep_20260731/code/original_quality_generation/generate_truth_conditioned_qscores.py'
ORIGINAL_2018_SHA256 = '3efcd5b677bc65b3eebcfb9ed48432829b3c3a5cbb2521807e24f85cd57c834d'
MODEL_2018_SHA256 = '6f60b7db6691bdf5955da54f621776bd7584d6c21b30f7290dff82d7037a0a85'
READ_ID = re.compile(r'^@([ACGT]{16})-(\d+)(?:\s|$)')
PREVIEW_READS = 20


def condition(shift):
    return 'native_unadjusted' if shift == 0 else f'shift_p{shift:02d}'


def label(shift):
    return 'nanopore2018 native' if shift == 0 else f'nanopore2018 {shift:+d}'


def transform(q, shift):
    # Original model Q1..28 plus any selected shift1..13 never reaches a clip bound.
    return q if shift == 0 else max(1, min(50, q + shift))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def open_text(path):
    return gzip.open(path, 'rt') if path.suffix == '.gz' else path.open()


def load_sample(path):
    expected = {}
    if path is None:
        return expected
    with open_text(path) as handle:
        for row in csv.DictReader(handle):
            rid = row['read_id']
            if rid in expected:
                raise ValueError('Duplicate sample read ID: ' + rid)
            values = tuple(float(row[label(s)]) for s in SHIFTS)
            if not all(math.isfinite(x) for x in values):
                raise ValueError('Nonfinite sample quality')
            expected[rid] = (row['truth_barcode'], int(row['barcode_ED']), values)
    if not expected:
        raise ValueError('Sample CSV has no data rows')
    return expected


def count_batch(batch):
    """Worker: return compact integer histograms; never retain full read sets."""
    ed_counts = collections.Counter()
    base_hist = collections.Counter()
    min_hist = collections.Counter()
    orientation = collections.Counter()
    unlocated = 0
    checked_ids = []
    max_difference = 0.0
    preview = []
    for ordinal, rid, truth, sequence, quality, expected in batch:
        found = locator.locate_truth_barcode(sequence, truth, 7, 8)
        row = dict(input_record_1based=ordinal, read_id=rid, read_length=len(sequence),
                   truth_barcode=truth, located=found is not None,
                   orientation='', barcode_start_original_0based='',
                   observed_barcode_canonical='', barcode_ED='',
                   native_quality_vector_canonical='', native_mean_barcode_Q='')
        if found is None:
            unlocated += 1
            if expected is not None:
                raise ValueError('Previously located sample is now unlocated: ' + rid)
        else:
            start = int(found['barcode_start_original'])
            q = tuple(x - 33 for x in quality[start:start + 16])
            if len(q) != 16 or not all(1 <= x <= 28 for x in q):
                raise ValueError('Invalid recovered native Q1..28 barcode quality window: ' + rid)
            if found['orientation'] == '-':
                q = q[::-1]
            ed = int(found['barcode_ed'])
            ed_counts[ed] += 1
            base_hist.update((ed, x) for x in q)
            min_hist[(ed, min(q))] += 1
            orientation[found['orientation']] += 1
            row.update(orientation=found['orientation'], barcode_start_original_0based=start,
                       observed_barcode_canonical=found['observed_oriented'], barcode_ED=ed,
                       native_quality_vector_canonical=','.join(map(str, q)),
                       native_mean_barcode_Q=sum(q) / 16)
            if expected is not None:
                expected_truth, expected_ed, values = expected
                if truth != expected_truth or ed != expected_ed:
                    raise ValueError('Sample truth/edit-distance mismatch: ' + rid)
                differences = [abs(sum(transform(x, s) for x in q) / 16 - value)
                               for s, value in zip(SHIFTS, values)]
                difference = max(differences)
                if difference > 1e-12:
                    raise ValueError(f'Sample quality mismatch: {rid}: {difference}')
                max_difference = max(max_difference, difference)
                checked_ids.append(rid)
        if ordinal <= PREVIEW_READS:
            preview.append(row)
    return dict(ed_counts=ed_counts, base_hist=base_hist, min_hist=min_hist,
                orientation=orientation, unlocated=unlocated, preview=preview,
                checked_ids=checked_ids, max_sample_difference=max_difference)


def batches(path, expected, batch_size, stream, input_shift):
    """Parent: read through EOF/CRC, hash ordered identities/qualities once."""
    opener = gzip.open if path.suffix == '.gz' else open
    batch = []
    # The exact stored condition had no clipping: invert every original score.
    # Sentinel zero rejects any byte outside the model support plus input shift.
    inverse = bytes(q-input_shift if 34+input_shift <= q <= 61+input_shift else 0
                    for q in range(256))
    with opener(path, 'rb') as handle:
        while True:
            header = handle.readline()
            if not header:
                break
            lines = [header, handle.readline(), handle.readline(), handle.readline()]
            if any(not x for x in lines):
                raise ValueError('Truncated four-line FASTQ')
            header, sequence, plus, quality = [x.rstrip(b'\r\n') for x in lines]
            if not header.startswith(b'@') or not plus.startswith(b'+'):
                raise ValueError('Malformed FASTQ record')
            if len(sequence) != len(quality) or not sequence:
                raise ValueError('Sequence/quality lengths differ or read is empty')
            text_header = header.decode('ascii')
            match = READ_ID.match(text_header)
            if match is None:
                raise ValueError('Read header lacks known ScTagger truth: ' + text_header)
            truth = match.group(1)
            rid = text_header[1:]
            sequence = sequence.upper()
            stream['header_sequence_hash'].update(header + b'\n' + sequence + b'\n')
            stream['quality_hash'].update(quality + b'\n')
            quality = quality.translate(inverse)
            if b'\0' in quality:
                raise ValueError('Stored input quality is outside Q(1+shift)..Q(28+shift)')
            stream['recovered_native_quality_hash'].update(quality + b'\n')
            stream['reads'] += 1
            stream['bases'] += len(sequence)
            stream['truth_barcodes'].add(truth)
            batch.append((stream['reads'], rid, truth, sequence.decode('ascii'),
                          quality, expected.get(rid)))
            if len(batch) == batch_size:
                yield batch
                batch = []
        if batch:
            yield batch
    stream['read_through_eof'] = True


def write_tsv(path, rows, fields=None):
    fields = fields or list(rows[0])
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fastq', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--input-shift', type=int, required=True, choices=SHIFTS[:-1],
                        help='Known positive shift of the retained input; p01 requires1')
    parser.add_argument('--workers', type=int, default=1)
    parser.add_argument('--batch-size', type=int, default=1000)
    parser.add_argument('--sample-csv', type=Path,
                        help='Optional paired_50000_barcode_mean_Q.csv[.gz]; require every listed ID')
    args = parser.parse_args()
    if args.workers < 1 or not 1 <= args.batch_size <= 10000:
        parser.error('workers must be positive; batch-size must be between1 and10000')
    started = time.monotonic()
    started_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    initial_stat = args.fastq.stat()
    expected = load_sample(args.sample_csv)
    stream = dict(reads=0, bases=0, truth_barcodes=set(), read_through_eof=False,
                  header_sequence_hash=hashlib.sha256(), quality_hash=hashlib.sha256(),
                  recovered_native_quality_hash=hashlib.sha256())
    totals = dict(ed_counts=collections.Counter(), base_hist=collections.Counter(),
                  min_hist=collections.Counter(), orientation=collections.Counter(),
                  unlocated=0, preview=[], checked_ids=set(), max_sample_difference=0.0)
    completed = 0
    next_progress = 100000

    def merge(result):
        nonlocal completed, next_progress
        for key in ['ed_counts', 'base_hist', 'min_hist', 'orientation']:
            totals[key].update(result[key])
        totals['unlocated'] += result['unlocated']
        totals['preview'].extend(result['preview'])
        for rid in result['checked_ids']:
            if rid in totals['checked_ids']:
                raise ValueError('Duplicate sample read in input: ' + rid)
            totals['checked_ids'].add(rid)
        totals['max_sample_difference'] = max(totals['max_sample_difference'],
                                              result['max_sample_difference'])
        completed += sum(result['ed_counts'].values()) + result['unlocated']
        if completed >= next_progress:
            print(f'Located/classified {completed:,} reads; elapsed {time.monotonic()-started:.1f}s', flush=True)
            next_progress += 100000

    records = batches(args.fastq, expected, args.batch_size, stream, args.input_shift)
    if args.workers == 1:
        for batch in records:
            merge(count_batch(batch))
    else:
        # At most2*workers submitted batches, consumed in source order.
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            pending = collections.deque()
            for batch in records:
                pending.append(pool.submit(count_batch, batch))
                if len(pending) >= 2 * args.workers:
                    merge(pending.popleft().result())
            while pending:
                merge(pending.popleft().result())
    final_stat = args.fastq.stat()
    if (initial_stat.st_size, initial_stat.st_mtime_ns) != (final_stat.st_size, final_stat.st_mtime_ns):
        raise ValueError('Input file changed during scan')
    if not stream['read_through_eof'] or stream['reads'] == 0 or completed != stream['reads']:
        raise ValueError('Incomplete or empty FASTQ scan')
    if totals['checked_ids'] != set(expected):
        raise ValueError(f'Sample coverage differs: found{len(totals["checked_ids"])} expected{len(expected)}')
    located = sum(totals['ed_counts'].values())
    if located + totals['unlocated'] != stream['reads']:
        raise ValueError('Located/unlocated read conservation failed')
    for ed, n in totals['ed_counts'].items():
        if sum(count for (e, q), count in totals['base_hist'].items() if e == ed) != 16*n:
            raise ValueError('Per-edit-distance barcode-base conservation failed')
        if sum(count for (e, q), count in totals['min_hist'].items() if e == ed) != n:
            raise ValueError('Per-edit-distance minimum-quality conservation failed')

    correct_n = totals['ed_counts'][0]
    error_n = located - correct_n
    summary = []
    for shift in SHIFTS:
        correct_sum = sum(count*transform(q, shift) for (ed, q), count in totals['base_hist'].items() if ed == 0)
        error_sum = sum(count*transform(q, shift) for (ed, q), count in totals['base_hist'].items() if ed > 0)
        correct_mean = correct_sum/(16*correct_n) if correct_n else ''
        error_mean = error_sum/(16*error_n) if error_n else ''
        summary.append(dict(model='nanopore2018', condition=condition(shift), shift=shift,
            quality_transform='none; raw native scores' if shift == 0 else 'per-base clip(Q+shift,1,50)',
            total_reads=stream['reads'], located_reads=located, unlocated_reads=totals['unlocated'],
            correct_reads=correct_n, error_reads=error_n, correct_barcode_bases=16*correct_n,
            error_barcode_bases=16*error_n, correct_quality_sum=correct_sum, error_quality_sum=error_sum,
            correct_mean_barcode_Q=correct_mean, error_mean_barcode_Q=error_mean,
            correct_minus_error_mean_Q=correct_mean-error_mean if correct_n and error_n else '',
            pooled_mean_barcode_Q=(correct_sum+error_sum)/(16*located) if located else ''))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(args.output_dir/'full_quality_summary.tsv', summary)
    write_tsv(args.output_dir/'barcode_quality_by_ed.tsv',
              [dict(barcode_ED=ed, q=q, base_count=n) for (ed, q), n in sorted(totals['base_hist'].items())],
              ['barcode_ED', 'q', 'base_count'])
    write_tsv(args.output_dir/'barcode_minimum_quality_by_ed.tsv',
              [dict(barcode_ED=ed, min_q=q, read_count=n) for (ed, q), n in sorted(totals['min_hist'].items())],
              ['barcode_ED', 'min_q', 'read_count'])
    write_tsv(args.output_dir/'barcode_edit_distance_counts.tsv',
              [dict(barcode_ED=ed, reads=n, barcode_bases=16*n) for ed, n in sorted(totals['ed_counts'].items())],
              ['barcode_ED', 'reads', 'barcode_bases'])
    write_tsv(args.output_dir/'first20_barcode_windows.tsv', sorted(totals['preview'], key=lambda x:x['input_record_1based']))
    versions = {}
    for package in ['edlib']:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = 'unrecovered'
    outputs = [dict(path=p.name, bytes=p.stat().st_size, sha256=sha(p))
               for p in sorted(args.output_dir.glob('*.tsv'))]
    report = dict(status='passed complete scan and internal conservation', started_utc=started_utc,
        elapsed_seconds=time.monotonic()-started, host=socket.gethostname(), python=sys.version,
        package_versions=versions, argv=sys.argv, workers=args.workers, batch_size=args.batch_size,
        maximum_pending_batches=2*args.workers if args.workers > 1 else 1,
        slurm={k:os.environ.get(k) for k in ['SLURM_JOB_ID','SLURM_JOB_NODELIST','SLURM_CPUS_PER_TASK']},
        input=dict(path=str(args.fastq.resolve()), bytes=initial_stat.st_size, mtime_ns=initial_stat.st_mtime_ns),
        input_unchanged_during_scan=True, reads=stream['reads'], bases=stream['bases'],
        distinct_header_truth_barcodes=len(stream['truth_barcodes']), located_reads=located,
        correct_reads=correct_n, error_reads=error_n, unlocated_reads=totals['unlocated'],
        barcode_ed_counts=dict(sorted(totals['ed_counts'].items())), orientation_counts=dict(totals['orientation']),
        header_sequence_sha256=stream['header_sequence_hash'].hexdigest(),
        quality_sha256=stream['quality_hash'].hexdigest(),
        recovered_native_quality_sha256=stream['recovered_native_quality_hash'].hexdigest(),
        input_shift=args.input_shift,
        input_quality_condition=condition(args.input_shift),
        input_quality_support_checked=[1+args.input_shift, 28+args.input_shift],
        recovered_native_quality_support=[1,28],
        native_recovery='Qnative=Qstored-input_shift; selected original model support1..28 and offsets1..13 imply no clipping; all stored quality bytes checked before inversion',
        quality_hash_scope='quality_sha256 hashes actual stored shifted FASTQ qualities; recovered_native_quality_sha256 hashes their exact inverse',
        original_2018_generator=ORIGINAL_2018_GENERATOR,
        original_2018_generator_sha256=ORIGINAL_2018_SHA256,
        original_2018_model_sha256=MODEL_2018_SHA256,
        locator_identity='All three copied locator function ASTs are identical to the original2018 generator',
        digest_contract='CR/LF stripped; header including @ plus LF, uppercase sequence plus LF; quality plus LF; source order',
        gzip_crc_checked_by_complete_stream_read=args.fastq.suffix == '.gz',
        sample_validation=dict(requested=args.sample_csv is not None, expected_reads=len(expected),
            found_reads=len(totals['checked_ids']), conditions_per_read=len(SHIFTS),
            read_condition_values_compared=len(totals['checked_ids'])*len(SHIFTS),
            maximum_absolute_mean_Q_difference=totals['max_sample_difference'], tolerance=1e-12,
            source=str(args.sample_csv) if args.sample_csv else None,
            source_sha256=sha(args.sample_csv) if args.sample_csv else None),
        script_sha256=sha(Path(__file__)), locator_sha256=sha(Path(locator.__file__)),
        locator_original_source=locator.ORIGINAL_SOURCE_PATH,
        locator_original_source_sha256=locator.ORIGINAL_SOURCE_SHA256,
        locator_copied_functions_sha256=locator.COPIED_FUNCTIONS_SHA256,
        counting='Truth-located 16-base window ED0 versus ED>0; per-base transform precedes averaging; unlocated reads excluded from both groups',
        outputs=outputs, quality_regenerated=False, blaze_rerun=False,
        limitation='Read IDs are hashed in order; global read-ID uniqueness is not re-audited. Existing BLAZE F1 is joined separately.')
    (args.output_dir/'run.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f'Complete: {stream["reads"]:,} reads; {correct_n:,} correct, {error_n:,} error-containing, {totals["unlocated"]:,} unlocated; {len(summary)} quality conditions.', flush=True)


if __name__ == '__main__':
    main()
