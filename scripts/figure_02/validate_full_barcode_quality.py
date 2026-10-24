#!/usr/bin/env python3
"""Validate compact full-read barcode-Q outputs and join existing BLAZE metrics.

This script never opens a full FASTQ. It independently recomputes the 12
condition summaries from integer histograms and checks them against preserved
producer counts, native stream hashes, pooled-quality tables, and the 50,000
read sample. The output is written only after every check passes.
"""
import argparse
from collections import Counter
import csv
import datetime
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys

SHIFTS = (-17, -16, -15, -14, -12, -11, -9, -7, -6, -5, -4, 0)
CONDITIONS = {('native_unadjusted' if s == 0 else 'shift_m%02d' % abs(s)): s for s in SHIFTS}
REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / 'source_data/figure_02'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def rows(path, delimiter='\t'):
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', newline='') as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value):
    # No float conversion: preserve exact large integer counts and sums.
    require(not isinstance(value, bool), 'Boolean supplied as an integer')
    result = int(value)
    require(str(result) == str(value), 'Noncanonical integer: %r' % value)
    return result


def close(actual, expected, label, tolerance=1e-12):
    a, b = float(actual), float(expected)
    require(math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tolerance,
            '%s differs: %r versus %r' % (label, a, b))


def keyed(records, key, label):
    result = {}
    for row in records:
        k = key(row)
        require(k not in result, 'Duplicate %s key: %r' % (label, k))
        result[k] = row
    require(result, 'Empty ' + label)
    return result


def transform(q, shift):
    # Native is unclipped, including Q>50; every negative shift clips per base.
    return q if shift == 0 else max(1, min(50, q + shift))


def histogram(path, q_field, count_field):
    result = Counter()
    for row in rows(path):
        ed, q, n = integer(row['barcode_ED']), integer(row[q_field]), integer(row[count_field])
        require(0 <= ed <= 16 and 1 <= q <= 90 and n > 0, 'Invalid histogram row in ' + str(path))
        require((ed, q) not in result, 'Duplicate histogram key in ' + str(path))
        result[ed, q] = n
    require(result, 'Empty histogram: ' + str(path))
    return result


def selected_conditions(path, tool=None):
    selected = [r for r in rows(path) if r['dataset'] == 'L' and r['model'] == 'nanopore2023'
                and (tool is None or r['tool'] == tool)]
    result = keyed(selected, lambda r: r['condition'], str(path))
    require(set(result) == set(CONDITIONS), 'Expected exactly the 12 selected conditions in ' + str(path))
    for name, shift in CONDITIONS.items():
        require(integer(result[name]['shift']) == shift, 'Condition/shift mismatch in ' + str(path))
    return result


def validate(args):
    inputs = {}

    def record_input(name, path):
        inputs[name] = dict(path=str(path.resolve()), bytes=path.stat().st_size, sha256=sha(path))

    for name in ['generation_summary', 'native_audit', 'quality_summary', 'histograms',
                 'discovery_metrics', 'sample_csv', 'scanner_script', 'locator_script']:
        record_input(name, getattr(args, name))
    report_path = args.scan_dir / 'run.json'
    record_input('full_scan_receipt', report_path)
    run = json.loads(report_path.read_text())
    require(run['status'] == 'passed complete scan and internal conservation', 'Full scan did not pass')
    for flag in ['input_unchanged_during_scan', 'gzip_crc_checked_by_complete_stream_read']:
        require(run[flag] is True, 'Missing complete native scan guarantee: ' + flag)
    require(run['quality_regenerated'] is False and run['blaze_rerun'] is False,
            'Expected a native-quality scan with existing BLAZE metrics')
    require(run['script_sha256'] == inputs['scanner_script']['sha256'], 'Scanner source hash differs')
    require(run['locator_sha256'] == inputs['locator_script']['sha256'], 'Locator source hash differs')

    # Bind every consumed scan table to the producer receipt before calculation.
    produced = keyed(run['outputs'], lambda r: r['path'], 'scan output')
    for name in ['full_quality_summary.tsv', 'barcode_quality_by_ed.tsv',
                 'barcode_minimum_quality_by_ed.tsv', 'barcode_edit_distance_counts.tsv']:
        path = args.scan_dir / name
        require(name in produced, 'Scan receipt omits ' + name)
        record_input(name, path)
        require(inputs[name]['sha256'] == produced[name]['sha256'] and
                inputs[name]['bytes'] == produced[name]['bytes'], 'Scan output hash/size mismatch: ' + name)

    generation_rows = keyed(rows(args.generation_summary), lambda r: r['metric'], 'generation metric')
    generation = {k: r['value'] for k, r in generation_rows.items()}
    require(generation['model_label'] == 'nanopore2023' and
            generation['quality_mode'] == 'native_unadjusted_no_shift_no_ceiling', 'Wrong native generation contract')
    require(integer(generation['model_failures']) == 0, 'Native generation model failures')
    expected_ed = {int(k.removeprefix('barcode_ed_')): integer(v)
                   for k, v in generation.items() if k.startswith('barcode_ed_')}
    require(expected_ed and min(expected_ed) == 0, 'No expected barcode edit-distance counts')
    native = json.loads(args.native_audit.read_text())
    for key in ['reads', 'bases']:
        require(run[key] == integer(generation[key]) == native[key], 'Full stream ' + key + ' differs')
    require(run['distinct_header_truth_barcodes'] == native['distinct_header_truth_barcodes'], 'Truth barcode count differs')
    require(run['located_reads'] == integer(generation['located']) == sum(expected_ed.values()), 'Located reads differ')
    require(run['unlocated_reads'] == integer(generation['orientation_not_located']), 'Unlocated reads differ')
    require(run['reads'] == run['located_reads'] + run['unlocated_reads'], 'Read conservation failed')
    require(run['correct_reads'] == expected_ed[0] and
            run['error_reads'] == sum(n for ed, n in expected_ed.items() if ed > 0), 'ED0/ED>0 cohort counts differ')
    require({int(k): v for k, v in run['barcode_ed_counts'].items()} == expected_ed, 'Scan receipt ED counts differ')
    require(run['orientation_counts'] == {s: integer(generation['orientation_' + s]) for s in ['+', '-']},
            'Orientation counts differ')
    require(run['header_sequence_sha256'] == generation['header_sequence_sha256'] ==
            native['native_header_sequence_sha256'] == native['source_header_sequence_sha256'], 'Native ordered header/sequence hash differs')
    require(run['quality_sha256'] == native['native_quality_sha256'], 'Native ordered quality hash differs')
    require(native['gzip_crc_checked_by_complete_stream_read'] is True and native['header_sequence_hashes_match'] is True,
            'Preserved native stream audit did not pass')
    for key in ['header_mismatches_vs_source', 'plus_line_mismatches_vs_source', 'sequence_mismatches_vs_source',
                'quality_length_mismatches', 'malformed_records']:
        require(native[key] == 0, 'Preserved native audit has ' + key)

    ed_rows = keyed(rows(args.scan_dir / 'barcode_edit_distance_counts.tsv'),
                    lambda r: integer(r['barcode_ED']), 'ED count')
    require(set(ed_rows) == set(expected_ed), 'Edit-distance table classes differ')
    base_hist = histogram(args.scan_dir / 'barcode_quality_by_ed.tsv', 'q', 'base_count')
    min_hist = histogram(args.scan_dir / 'barcode_minimum_quality_by_ed.tsv', 'min_q', 'read_count')
    require({ed for ed, q in base_hist} == set(expected_ed) == {ed for ed, q in min_hist}, 'Histogram ED classes differ')
    for ed, n in expected_ed.items():
        require(integer(ed_rows[ed]['reads']) == n and integer(ed_rows[ed]['barcode_bases']) == 16 * n,
                'Edit-distance table count differs for ED' + str(ed))
        require(sum(v for (e, q), v in base_hist.items() if e == ed) == 16 * n, 'Barcode-base conservation failed')
        require(sum(v for (e, q), v in min_hist.items() if e == ed) == n, 'Minimum-quality conservation failed')

    # Compare native and every shifted histogram, not only rounded means.
    saved_hist = keyed([r for r in rows(args.histograms) if r['model'] == 'nanopore2023'],
                       lambda r: (r['condition'], integer(r['q'])), 'preserved histogram')
    require({c for c, q in saved_hist} == set(CONDITIONS), 'Preserved histogram condition set differs')
    summaries = keyed(rows(args.scan_dir / 'full_quality_summary.tsv'), lambda r: r['condition'], 'full summary')
    require(set(summaries) == set(CONDITIONS), 'Full summary condition set differs')
    pooled = selected_conditions(args.quality_summary)
    blaze = selected_conditions(args.discovery_metrics, tool='BLAZE')
    joined = []
    for name, shift in CONDITIONS.items():
        base_by_q, min_by_q = Counter(), Counter()
        for (ed, q), n in base_hist.items():
            base_by_q[transform(q, shift)] += n
        for (ed, q), n in min_hist.items():
            min_by_q[transform(q, shift)] += n
        saved_base, saved_min = Counter(), Counter()
        for (condition, q), r in saved_hist.items():
            if condition == name:
                require(integer(r['shift']) == shift, 'Preserved histogram shift differs')
                for field in ['whole_base_count', 'barcode_base_count', 'truth_located_barcode_window_min_count']:
                    require(integer(r[field]) >= 0, 'Negative preserved histogram count')
                saved_base[q] = integer(r['barcode_base_count'])
                saved_min[q] = integer(r['truth_located_barcode_window_min_count'])
        require(dict(+base_by_q) == dict(+saved_base), name + ': pooled barcode-base histogram differs')
        require(dict(+min_by_q) == dict(+saved_min), name + ': pooled minimum-quality histogram differs')
        correct_sum = sum(n * transform(q, shift) for (ed, q), n in base_hist.items() if ed == 0)
        error_sum = sum(n * transform(q, shift) for (ed, q), n in base_hist.items() if ed > 0)
        correct_mean = correct_sum / (16 * run['correct_reads'])
        error_mean = error_sum / (16 * run['error_reads'])
        mean = (correct_sum + error_sum) / (16 * run['located_reads'])
        row = summaries[name]
        require(row['model'] == 'nanopore2023' and integer(row['shift']) == shift, 'Summary condition/model differs')
        transform_label = 'none; raw native scores' if shift == 0 else 'per-base clip(Q+shift,1,50)'
        require(row['quality_transform'] == pooled[name]['quality_transform'] == transform_label, 'Quality transform differs')
        expected_counts = dict(total_reads=run['reads'], located_reads=run['located_reads'],
            unlocated_reads=run['unlocated_reads'], correct_reads=run['correct_reads'], error_reads=run['error_reads'],
            correct_barcode_bases=16 * run['correct_reads'], error_barcode_bases=16 * run['error_reads'],
            correct_quality_sum=correct_sum, error_quality_sum=error_sum)
        for key, n in expected_counts.items():
            require(integer(row[key]) == n, name + ': summary ' + key + ' differs')
        for key, value in dict(correct_mean_barcode_Q=correct_mean, error_mean_barcode_Q=error_mean,
                               correct_minus_error_mean_Q=correct_mean-error_mean, pooled_mean_barcode_Q=mean).items():
            close(row[key], value, name + ': ' + key)
        close(mean, pooled[name]['full_located_barcode_mean_Q'], name + ': preserved pooled mean')
        require(sum(n for q, n in min_by_q.items() if q >= 15) ==
                integer(pooled[name]['full_truth_located_barcode_minQ15_pass_n']), name + ': minQ15 count differs')
        metrics = blaze[name]
        tp, fp, fn = [integer(metrics[k]) for k in ['tp', 'fp', 'fn']]
        require(min(tp, fp, fn) >= 0 and tp + fn == native['distinct_header_truth_barcodes'] and
                tp + fp == integer(metrics['calls']), name + ': BLAZE count conservation failed')
        f1 = 2 * tp / (2 * tp + fp + fn)
        precision, recall = tp / (tp + fp), tp / (tp + fn)
        for key, value in [('f1', f1), ('precision', precision), ('recall', recall)]:
            close(metrics[key], value, name + ': BLAZE ' + key)
        close(metrics['full_dataset_mean_Q'], pooled[name]['full_dataset_mean_Q'], name + ': whole-read mean join')
        joined.append(dict(dataset='L', **row, full_dataset_mean_Q=pooled[name]['full_dataset_mean_Q'],
                           blaze_tp=tp, blaze_fp=fp, blaze_fn=fn, blaze_calls=tp+fp,
                           blaze_precision=precision, blaze_recall=recall, blaze_f1=f1,
                           blaze_metric_scope='barcode discovery; TP/FP/FN are barcode counts',
                           blaze_origin=metrics['origin'], blaze_source_table=metrics['source_table']))

    # The producer checked every sampled read's truth, ED and 12 means in-stream.
    # Here bind its report to the actual sample bytes and recompute sample means.
    sample_check = run['sample_validation']
    require(sample_check['requested'] is True and sample_check['expected_reads'] == 50000 and
            sample_check['found_reads'] == 50000 and sample_check['conditions_per_read'] == 12 and
            sample_check['read_condition_values_compared'] == 600000, 'Incomplete 50,000-read sample verification')
    require(sample_check['source_sha256'] == inputs['sample_csv']['sha256'], 'Sample source hash differs')
    close(sample_check['maximum_absolute_mean_Q_difference'], 0, 'Per-read sample maximum difference')
    close(sample_check['tolerance'], 1e-12, 'Per-read sample tolerance', tolerance=0)
    sample = keyed(rows(args.sample_csv, delimiter=','), lambda r: r['read_id'], 'sample read ID')
    require(len(sample) == 50000, 'Sample does not have 50,000 unique reads')
    sample_clean = [r for r in sample.values() if integer(r['barcode_ED']) == 0]
    sample_error = [r for r in sample.values() if integer(r['barcode_ED']) > 0]
    require(sample_clean and sample_error and len(sample_clean) + len(sample_error) == 50000, 'Invalid sample ED groups')
    for name, shift in CONDITIONS.items():
        label = 'nanopore2023 native' if shift == 0 else 'nanopore2023 %d' % shift
        for field, group in [('sample_mean_barcode_Q', list(sample.values())),
                             ('sample_clean_mean_Q', sample_clean), ('sample_error_mean_Q', sample_error)]:
            mean = math.fsum(float(r[label]) for r in group) / len(group)
            close(mean, pooled[name][field], name + ': ' + field)
        require(integer(pooled[name]['sample_reads']) == 50000, 'Preserved summary sample size differs')

    return joined, dict(status='passed', scope='Full native-read scan validated; 12 conditions joined to existing BLAZE discovery metrics',
        full_fastq_read_by_validator=False, quality_regenerated=False, blaze_rerun=False,
        reads=run['reads'], bases=run['bases'], located_reads=run['located_reads'],
        correct_ED0_reads=run['correct_reads'], incorrect_EDgt0_reads=run['error_reads'],
        unlocated_reads_excluded_from_quality_groups=run['unlocated_reads'],
        edit_distance_classes_checked=len(expected_ed), conditions_checked=len(joined),
        native_and_shifted_histograms_checked=2 * len(CONDITIONS), sample_read_condition_values_checked=600000,
        native_header_sequence_sha256=run['header_sequence_sha256'], native_quality_sha256=run['quality_sha256'],
        mean_absolute_tolerance=1e-12, f1_formula='2*TP/(2*TP+FP+FN)',
        means='Arithmetic mean of 16 Phred scores per truth-located read, then across reads in the ED group; integer histogram gives the identical mean',
        quality_groups='ED0 and ED>0 refer to the observed truth-located barcode, independent of a tool assignment or discovery call',
        limitation='Preserved BLAZE discovery TP/FP/FN are joined and arithmetic checked; this validator does not rerun BLAZE or rescore callsets',
        inputs=inputs, scanner_report=str(report_path.resolve()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scan-dir', type=Path, required=True, help='Directory produced by summarize_full_barcode_quality.py')
    parser.add_argument('--generation-summary', type=Path, required=True, help='Preserved native generator metric/value TSV')
    parser.add_argument('--output', type=Path, required=True, help='Destination full_quality_with_blaze_f1.tsv')
    parser.add_argument('--report', type=Path, required=True, help='Destination validation JSON')
    for name, default in [('native-audit', SOURCE/'native_fastq_validation.json'),
                          ('quality-summary', SOURCE/'quality_summary.tsv'),
                          ('histograms', SOURCE/'reconstructed_full_quality_histograms.tsv'),
                          ('discovery-metrics', SOURCE/'discovery_metrics.tsv'),
                          ('sample-csv', SOURCE/'paired_50000_barcode_mean_Q.csv.gz'),
                          ('scanner-script', Path(__file__).with_name('summarize_full_barcode_quality.py')),
                          ('locator-script', Path(__file__).with_name('barcode_locator.py'))]:
        parser.add_argument('--' + name, type=Path, default=default)
    args = parser.parse_args()
    report = dict(status='failed', output_published=False)
    try:
        joined, report = validate(args)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_name(args.output.name + '.partial')
        with temporary.open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(joined[0]), delimiter='\t', lineterminator='\n')
            writer.writeheader()
            writer.writerows(joined)
        temporary.replace(args.output)
        report['output_published'] = True
        report['output'] = dict(path=str(args.output.resolve()), rows=len(joined),
                                bytes=args.output.stat().st_size, sha256=sha(args.output))
    except Exception as exc:
        report['status'] = 'failed'
        report['error'] = str(exc)
        raise
    finally:
        report.update(validator_sha256=sha(Path(__file__)), argv=sys.argv,
                      completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print('Passed: %s full reads; 12 conditions; all 600,000 sampled read-condition values; BLAZE F1 join.' % report['reads'])


if __name__ == '__main__':
    main()
