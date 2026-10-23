#!/usr/bin/env python3
"""Replay frozen BLAZE selection; validate only against the unadjusted callset."""
import csv
import hashlib
import importlib
import importlib.metadata
import json
import os
import pathlib
import shutil
import socket
import sys
from collections import Counter
from datetime import datetime, timezone

import pandas as pd

ROOT = pathlib.Path('/scratch-nfs/f005f43/sctagger_nanopore2023_extended_sweep_20260913/blaze_replay')
NATIVE = pathlib.Path('/scratch-nfs/f005f43/sctagger_nanopore2023_unadjusted_20260913')
NATIVE_RUN = NATIVE / 'runs/L/nanopore2023_native_unadjusted/blaze'
CANDIDATES = NATIVE_RUN / 'putative_bc.csv'
TRUTH = NATIVE / 'metadata/L_truth_barcodes.txt'
TARGETS = [(1, -17), (2, -16), (3, -15), (4, -14), (5, -12), (6, -11),
           (8, -9), (10, -7), (11, -6), (12, -5), (13, -4)]
CHUNKSIZE = 1_000_000  # Same as frozen BLAZE main.py counting stage.


def now():
    return datetime.now(timezone.utc).isoformat()


def log(message):
    print(f'[{now()}] {message}', flush=True)


def sha256(path):
    digest = hashlib.sha256()
    with pathlib.Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, data):
    pathlib.Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def write_tsv(path, rows, fields):
    with pathlib.Path(path).open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)


def load_barcode_set(path):
    rows = pathlib.Path(path).read_text().splitlines()
    assert len(rows) == len(set(rows)), f'Duplicate barcodes: {path}'
    return set(rows)


def count_native_thresholds(thresholds):
    counts = {threshold: Counter() for threshold in thresholds}
    read_pass = Counter()
    total_reads = candidate_reads = 0
    for chunk_index, df in enumerate(pd.read_csv(CANDIDATES, chunksize=CHUNKSIZE), 1):
        total_reads += len(df)
        candidate_reads += int(df.putative_bc.notna().sum())
        for threshold in thresholds:
            mask = df.putative_bc_min_q >= threshold
            # Deliberately use the exact frozen BLAZE counting expression.
            counts[threshold] += Counter(df[mask].putative_bc.value_counts().to_dict())
            read_pass[threshold] += int(mask.sum())
        log(f'Counted chunk {chunk_index}; {total_reads:,} rows; thresholds {thresholds}')
    assert total_reads == 4_993_805
    assert candidate_reads == 4_302_026
    for threshold in thresholds:
        assert sum(counts[threshold].values()) == read_pass[threshold]
    return counts, read_pass, total_reads, candidate_reads


def main():
    started = now()
    assert ROOT.exists()
    assert not (ROOT / 'DONE').exists(), 'Completed replay is immutable; choose a new directory.'
    blaze_main = importlib.import_module('blaze.main')
    config = importlib.import_module('blaze.config')
    module_root = pathlib.Path(blaze_main.__file__).resolve().parent
    expected_root = NATIVE / 'tools/blaze_venv/lib/python3.9/site-packages/blaze'
    assert module_root == expected_root.resolve()
    full_whitelist = pathlib.Path(config.DEFAULT_GRB_WHITELIST_3V3)
    truth = load_barcode_set(TRUTH)
    assert len(truth) == 5000
    import io
    import zipfile
    with zipfile.ZipFile(full_whitelist) as archive:
        assert len(archive.namelist()) == 1
        with io.TextIOWrapper(archive.open(archive.namelist()[0])) as handle:
            tenx = {line.strip() for line in handle}

    source_paths = [CANDIDATES, TRUTH, NATIVE_RUN / 'whitelist.csv',
                    NATIVE_RUN / 'run_metadata.tsv', NATIVE_RUN / 'summary.txt',
                    NATIVE / 'provenance/blaze_environment_freeze.txt', full_whitelist]
    source_paths += sorted(module_root.glob('*.py'))
    log('Hashing read-only inputs and frozen BLAZE source.')
    source_manifest = [{'path': str(path), 'bytes': path.stat().st_size,
                        'sha256': sha256(path)} for path in source_paths]
    write_tsv(ROOT / 'provenance/input_sha256.tsv', source_manifest, ['path', 'bytes', 'sha256'])
    shutil.copyfile(NATIVE_RUN / 'run_metadata.tsv', ROOT / 'provenance/native_run_metadata.tsv')
    shutil.copyfile(NATIVE / 'provenance/blaze_environment_freeze.txt', ROOT / 'provenance/blaze_environment_freeze.txt')
    versions = {name: importlib.metadata.version(name)
                for name in ['blaze2', 'pandas', 'numpy', 'matplotlib']}
    provenance = {
        'started_utc': started, 'host': socket.gethostname(), 'python': sys.executable,
        'python_version': sys.version, 'slurm_job_id': os.environ.get('SLURM_JOB_ID'),
        'slurm_cpus_per_task': os.environ.get('SLURM_CPUS_PER_TASK'),
        'versions': versions, 'frozen_blaze_module_directory': str(module_root),
        'source_candidate_csv': str(CANDIDATES), 'source_truth': str(TRUTH),
        'source_native_whitelist': str(NATIVE_RUN / 'whitelist.csv'),
        'full_10x_whitelist': str(full_whitelist), 'full_10x_whitelist_barcodes': len(tenx),
        'biology_quality_transform': 'Shifted conditions: Q_shifted = max(1, min(50, Q_native + delta)); native validation: none (cached unadjusted qualities).',
        'biology_minimum_barcode_quality': 15,
        'equivalent_native_minQ': '15 - delta',
        'equivalence': 'Monotone clipping commutes with the minimum; threshold 15 is interior to [1,50]. Sequence-only extraction is unchanged.',
        'source_expression': 'raw_bc_count += Counter(df[df.putative_bc_min_q >= minQ].putative_bc.value_counts().to_dict())',
        'selection_function': 'blaze.main.get_bc_whitelist',
        'selection_parameters': {'exp_cells': 5000, 'count_t': None, 'force_cell_n': None,
                                 'high_sensitivity_mode': False, 'output_empty': False},
        'validation_scope': 'Only native unadjusted Q15 is compared against a previously completed BLAZE callset. Shifted conditions are requested sweep outputs, not additional controls.',
        'analysis_scope': 'Whitelist discovery only; no FASTQ reconstruction, extraction rerun, demultiplexing, RAD or Flexiplex execution.',
        'targets_2018_shift_to_2023_delta': TARGETS,
        'script_sha256': sha256(__file__),
    }
    write_json(ROOT / 'provenance/provenance.json', provenance)

    def select(condition, target_2018_shift, delta, raw_counts, read_pass, total_reads, candidate_reads):
        out = ROOT / 'conditions' / condition
        out.mkdir()
        native_minq = 15 - delta
        log(f'Selecting {condition}: shifted-Q15 = native-Q{native_minq}.')
        selected, empty = blaze_main.get_bc_whitelist(
            raw_counts, full_bc_whitelist=str(full_whitelist), exp_cells=5000,
            count_t=None, force_cell_n=None, high_sensitivity_mode=False,
            output_empty=False, out_plot_fn=str(out / 'knee_plot.png'))
        assert empty == []
        selected_set = set(selected)
        assert selected_set <= tenx
        whitelist_path = out / 'whitelist.csv'
        whitelist_path.write_text(''.join(barcode + '\n' for barcode in selected))
        valid_counts = {barcode: count for barcode, count in raw_counts.items() if barcode in tenx}
        threshold = float(config.default_count_threshold_calculation(list(valid_counts.values()), 5000))
        tp = len(selected_set & truth)
        fp = len(selected_set - truth)
        fn = len(truth - selected_set)
        precision = tp / len(selected_set) if selected_set else 0.0
        recall = tp / len(truth)
        f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
        count_rows = ({'barcode': barcode, 'high_quality_read_count': count,
                       'in_10x_whitelist': int(barcode in tenx),
                       'selected': int(barcode in selected_set), 'in_truth': int(barcode in truth)}
                      for barcode, count in sorted(raw_counts.items(), key=lambda item: (-item[1], item[0])))
        write_tsv(out / 'barcode_counts.tsv', count_rows,
                  ['barcode', 'high_quality_read_count', 'in_10x_whitelist', 'selected', 'in_truth'])
        for label, values in [('true_positive_barcodes', selected_set & truth),
                              ('false_positive_barcodes', selected_set - truth),
                              ('false_negative_barcodes', truth - selected_set)]:
            (out / f'{label}.txt').write_text(''.join(barcode + '\n' for barcode in sorted(values)))
        metrics = {
            'condition': condition, 'target_2018_shift': target_2018_shift,
            'nanopore2023_shift': delta, 'quality_clip_min': 1 if delta else None,
            'quality_clip_max': 50 if delta else None,
            'shifted_minQ': 15, 'effective_native_minQ': native_minq,
            'total_reads': total_reads, 'extractable_candidate_reads': candidate_reads,
            'high_quality_candidate_reads': int(read_pass),
            'high_quality_candidate_read_fraction': read_pass / total_reads,
            'high_quality_unique_candidate_barcodes': len(raw_counts),
            'high_quality_reads_in_10x_whitelist': sum(valid_counts.values()),
            'high_quality_unique_10x_barcodes': len(valid_counts),
            'count_threshold': threshold, 'count_selection_rule': 'strictly_greater_than_threshold',
            'called_barcodes': len(selected_set), 'truth_barcodes': len(truth),
            'true_positives': tp, 'false_positives': fp, 'false_negatives': fn,
            'precision': precision, 'recall': recall, 'f1': f1,
            'whitelist_path': str(whitelist_path), 'whitelist_sha256': sha256(whitelist_path),
        }
        write_json(out / 'metrics.json', metrics)
        write_json(out / 'selection_call.json', {
            'function': 'blaze.main.get_bc_whitelist', 'native_count_threshold': native_minq,
            'source_candidate_csv': str(CANDIDATES), 'quality_shift': delta,
            'biological_shifted_minQ': 15, 'quality_clip': [1, 50] if delta else None,
            'quality_transform': 'clip(Q_native + delta, 1, 50)' if delta else 'none',
            'kwargs': {'full_bc_whitelist': str(full_whitelist), 'exp_cells': 5000,
                       'count_t': None, 'force_cell_n': None, 'high_sensitivity_mode': False,
                       'output_empty': False, 'out_plot_fn': str(out / 'knee_plot.png')},
        })
        log(f'{condition}: called {len(selected_set)}; TP {tp}; FP {fp}; FN {fn}; threshold {threshold}.')
        return metrics, selected_set

    # Native validation is a hard dependency; shifted counting starts only after it passes.
    log('Starting ONLY validation control: native unadjusted Q15.')
    counts, passed, total, extracted = count_native_thresholds([15])
    native_metrics, native_replay_set = select('native_unadjusted_validation', None, 0,
                                              counts[15], passed[15], total, extracted)
    original_set = load_barcode_set(NATIVE_RUN / 'whitelist.csv')
    validation = {
        'checked_utc': now(), 'passed': native_replay_set == original_set,
        'original_whitelist': str(NATIVE_RUN / 'whitelist.csv'),
        'replayed_whitelist': native_metrics['whitelist_path'],
        'original_count': len(original_set), 'replay_count': len(native_replay_set),
        'missing_from_replay': sorted(original_set - native_replay_set),
        'added_by_replay': sorted(native_replay_set - original_set),
        'true_positives': native_metrics['true_positives'],
        'false_positives': native_metrics['false_positives'],
        'false_negatives': native_metrics['false_negatives'],
        'high_quality_candidate_reads': native_metrics['high_quality_candidate_reads'],
        'byte_identical_whitelist': sha256(NATIVE_RUN / 'whitelist.csv') == native_metrics['whitelist_sha256'],
        'other_validation_controls_run': [],
    }
    validation['passed'] = validation['passed'] and (
        validation['original_count'], validation['replay_count'], validation['true_positives'],
        validation['false_positives'], validation['false_negatives'],
        validation['high_quality_candidate_reads']) == (5015, 5015, 5000, 15, 0, 227812)
    write_json(ROOT / 'native_validation.json', validation)
    assert validation['passed'], 'Native replay validation failed; shifted conditions were not started.'
    log('NATIVE VALIDATION PASSED: identical whitelist set, TP5000/FP15/FN0.')
    del counts

    thresholds = [15 - delta for _, delta in TARGETS]
    counts, passed, total, extracted = count_native_thresholds(thresholds)
    metrics_rows = [native_metrics]
    for target, delta in TARGETS:
        condition = f'nanopore2023_shift_m{abs(delta):02d}_target_2018_p{target:02d}'
        metrics, _ = select(condition, target, delta, counts[15 - delta], passed[15 - delta], total, extracted)
        metrics_rows.append(metrics)
    write_tsv(ROOT / 'results.tsv', metrics_rows, list(metrics_rows[0]))
    provenance['finished_utc'] = now()
    provenance['native_validation_passed'] = True
    provenance['completed_shifted_conditions'] = len(TARGETS)
    write_json(ROOT / 'provenance/provenance.json', provenance)
    (ROOT / 'DONE').write_text(now() + '\n')
    log('Completed native validation and all eleven shifted whitelist replays.')


if __name__ == '__main__':
    main()
