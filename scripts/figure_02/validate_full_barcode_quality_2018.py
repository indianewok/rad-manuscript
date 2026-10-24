#!/usr/bin/env python3
"""Validate full Nanopore2018 barcode qualities and join existing BLAZE F1.

Reads only compact scan outputs, preserved provenance and the paired 50,000-read
sample. Native Q is recovered from the retained +1 FASTQ by exact subtraction;
the original model Q1..28 proves that the +1 transform was not clipped. Native
BLAZE metrics are unavailable and remain blank, rather than being set to zero.
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

SHIFTS = (1, 2, 3, 4, 5, 6, 8, 10, 11, 12, 13, 0)
CONDITIONS = {('native_unadjusted' if s == 0 else 'shift_p%02d' % s): s for s in SHIFTS}
SHIFTED = set(CONDITIONS) - {'native_unadjusted'}
SOURCE = Path(__file__).resolve().parents[2] / 'source_data/figure_02'
# Pins recovered from the actual selected original producer receipts/model.
SOURCE_PINS = {
    'generation_summary': '783a9695cd1f270917f25370409c2411ab2e0900ac233c1222ebef9ff8dcac14',
    'native_minimum_histogram': 'b567c5b185776a329a42e2127a255c7e7ce7e98ddc88cc32688d7a242b4ebcfb',
    'source_invariants': '9ed7c41ebc4f6b88e0e21e9db94be4872d032e1af4069ccc0bdb99625fb4b00b',
    'model': '6f60b7db6691bdf5955da54f621776bd7584d6c21b30f7290dff82d7037a0a85',
}
GENERATOR_SHA = '3efcd5b677bc65b3eebcfb9ed48432829b3c3a5cbb2521807e24f85cd57c834d'


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


def histogram(path, q_field, count_field):
    result = Counter()
    for row in rows(path):
        ed, q, n = integer(row['barcode_ED']), integer(row[q_field]), integer(row[count_field])
        require(0 <= ed <= 16 and 1 <= q <= 28 and n > 0, 'Invalid recovered-native histogram row')
        require((ed, q) not in result, 'Duplicate histogram key')
        result[ed, q] = n
    require(result, 'Empty histogram')
    return result


def transform(q, shift):
    return q if shift == 0 else max(1, min(50, q + shift))


def validate(args):
    inputs = {}

    def record(name, path):
        inputs[name] = dict(path=str(path.resolve()), bytes=path.stat().st_size, sha256=sha(path))
        if name in SOURCE_PINS:
            require(inputs[name]['sha256'] == SOURCE_PINS[name], 'Preserved source hash differs: ' + name)

    for name in ['generation_summary', 'native_minimum_histogram', 'source_invariants', 'model',
                 'source_manifest', 'quality_conditions', 'quality_summary', 'discovery_metrics',
                 'sample_csv', 'scanner_script', 'locator_script']:
        record(name, getattr(args, name))
    record('full_scan_receipt', args.scan_dir / 'run.json')
    run = json.loads((args.scan_dir / 'run.json').read_text())
    require(run['status'] == 'passed complete scan and internal conservation', 'Full scan did not pass')
    for flag in ['input_unchanged_during_scan', 'gzip_crc_checked_by_complete_stream_read']:
        require(run[flag] is True, 'Missing complete input scan guarantee: ' + flag)
    require(run['quality_regenerated'] is False and run['blaze_rerun'] is False, 'Unexpected resimulation or BLAZE rerun')
    require(run['script_sha256'] == inputs['scanner_script']['sha256'], 'Scanner source hash differs')
    require(run['locator_sha256'] == inputs['locator_script']['sha256'], 'Locator source hash differs')
    require(run['input_shift'] == 1 and run['input_quality_condition'] == 'shift_p01', 'Expected retained +1 FASTQ')
    require(run['input_quality_support_checked'] == [2, 29] and run['recovered_native_quality_support'] == [1, 28],
            'Exact inversion quality-range check missing')
    require(run['original_2018_generator_sha256'] == GENERATOR_SHA, 'Original generator hash differs')
    require(run['original_2018_model_sha256'] == inputs['model']['sha256'], 'Original model hash differs')
    generator_rows = [r for r in rows(args.source_manifest)
                      if r['archived_path'] == 'original_quality_generation/generate_truth_conditioned_qscores.py']
    require(len(generator_rows) == 1 and generator_rows[0]['sha256'] == GENERATOR_SHA, 'Generator manifest binding differs')
    support = set()
    with gzip.open(args.model, 'rt') as handle:
        for line in handle:
            for entry in line.rstrip().split(';')[2].split(','):
                if entry:
                    q, probability = entry.split(':')
                    if float(probability) > 0:
                        support.add(integer(q))
    require(min(support) == 1 and max(support) == 28, 'Original model support does not allow exact inversion')
    require(len(run['recovered_native_quality_sha256']) == 64 and
            set(run['recovered_native_quality_sha256']) <= set('0123456789abcdef'), 'Invalid recovered native digest')

    produced = keyed(run['outputs'], lambda r: r['path'], 'scan output')
    for name in ['full_quality_summary.tsv', 'barcode_quality_by_ed.tsv',
                 'barcode_minimum_quality_by_ed.tsv', 'barcode_edit_distance_counts.tsv']:
        record(name, args.scan_dir / name)
        require(name in produced and inputs[name]['sha256'] == produced[name]['sha256'] and
                inputs[name]['bytes'] == produced[name]['bytes'], 'Scan output hash/size mismatch: ' + name)
    generation = {k: r['value'] for k, r in keyed(rows(args.generation_summary),
                  lambda r: r['metric'], 'generation metric').items()}
    require(generation['model'].endswith('/nanopore2018.gz') and integer(generation['seed']) == 20260731 and
            integer(generation['model_failures']) == 0, 'Wrong original generation contract')
    original = [r for r in rows(args.source_invariants) if Path(r['path']).name.endswith('.shift_p01.fq.gz')]
    require(len(original) == 1, 'Original invariants must contain exactly one +1 input')
    original = original[0]
    require(integer(original['malformed']) == 0 and original['matches_reference'] == 'true', 'Original input invariant audit failed')
    require(integer(original['min_q']) == 2 and integer(original['max_q']) == 29, 'Original +1 quality range differs')
    for key in ['reads', 'bases']:
        require(run[key] == integer(generation[key]) == integer(original[key]), 'Full stream ' + key + ' differs')
    require(run['header_sequence_sha256'] == generation['header_sequence_sha256'] == original['header_sequence_sha256'],
            'Ordered input header/sequence hash differs')
    require(run['quality_sha256'] == original['quality_sha256'], 'Ordered stored +1 quality hash differs')
    expected_ed = {int(k[len('barcode_ed_'):]): integer(v) for k, v in generation.items() if k.startswith('barcode_ed_')}
    require(run['located_reads'] == integer(generation['located']) == sum(expected_ed.values()), 'Located reads differ')
    require(run['unlocated_reads'] == integer(generation['orientation_not_located']), 'Unlocated reads differ')
    require(run['reads'] == run['located_reads'] + run['unlocated_reads'], 'Read conservation failed')
    require(run['correct_reads'] == expected_ed[0] and
            run['error_reads'] == sum(n for ed, n in expected_ed.items() if ed > 0), 'ED0/ED>0 group counts differ')
    require({int(k): v for k, v in run['barcode_ed_counts'].items()} == expected_ed, 'Receipt ED counts differ')
    require(run['orientation_counts'] == {s: integer(generation['orientation_' + s]) for s in ['+', '-']}, 'Orientations differ')
    ed_rows = keyed(rows(args.scan_dir / 'barcode_edit_distance_counts.tsv'), lambda r: integer(r['barcode_ED']), 'ED count')
    base_hist = histogram(args.scan_dir / 'barcode_quality_by_ed.tsv', 'q', 'base_count')
    min_hist = histogram(args.scan_dir / 'barcode_minimum_quality_by_ed.tsv', 'min_q', 'read_count')
    require(set(ed_rows) == set(expected_ed) == {ed for ed, q in base_hist} == {ed for ed, q in min_hist}, 'ED classes differ')
    for ed, n in expected_ed.items():
        require(integer(ed_rows[ed]['reads']) == n and integer(ed_rows[ed]['barcode_bases']) == 16*n, 'ED table counts differ')
        require(sum(v for (e, q), v in base_hist.items() if e == ed) == 16*n, 'ED barcode-base conservation failed')
        require(sum(v for (e, q), v in min_hist.items() if e == ed) == n, 'ED minimum-quality conservation failed')
    native_min = keyed(rows(args.native_minimum_histogram), lambda r: integer(r['min_q']), 'native minimum Q')
    saved_min = Counter({q: integer(r['count']) for q, r in native_min.items()})
    require(all(n > 0 for n in saved_min.values()), 'Invalid original native minimum-Q counts')
    computed_min = Counter()
    for (ed, q), n in min_hist.items():
        computed_min[q] += n
    require(computed_min == saved_min, 'Exact original native minimum-Q histogram differs')

    summaries = keyed(rows(args.scan_dir / 'full_quality_summary.tsv'), lambda r: r['condition'], 'full summary')
    pooled = keyed([r for r in rows(args.quality_summary) if r['dataset'] == 'L' and r['model'] == 'nanopore2018'],
                   lambda r: r['condition'], 'pooled summary')
    conditions = keyed([r for r in rows(args.quality_conditions) if r['dataset'] == 'L' and
                        r['quality_model'] == 'Badread_nanopore2018_truth_conditioned'], lambda r: r['quality_tag'], 'original condition')
    blaze = keyed([r for r in rows(args.discovery_metrics) if r['dataset'] == 'L' and
                   r['model'] == 'nanopore2018' and r['tool'] == 'BLAZE'], lambda r: r['condition'], 'BLAZE condition')
    require(set(summaries) == set(pooled) == set(CONDITIONS), 'Expected all 12 quality conditions')
    require(set(conditions) == set(blaze) == SHIFTED, 'Expected exactly 11 shifted BLAZE conditions and no native metric')
    joined = []
    for name, shift in CONDITIONS.items():
        row = summaries[name]
        require(row['model'] == 'nanopore2018' and integer(row['shift']) == integer(pooled[name]['shift']) == shift,
                'Summary model/shift differs')
        transform_label = 'none; raw native scores' if shift == 0 else 'per-base clip(Q+shift,1,50)'
        require(row['quality_transform'] == pooled[name]['quality_transform'] == transform_label, 'Quality transform differs')
        correct_sum = sum(n*transform(q, shift) for (ed, q), n in base_hist.items() if ed == 0)
        error_sum = sum(n*transform(q, shift) for (ed, q), n in base_hist.items() if ed > 0)
        clean, error = correct_sum/(16*run['correct_reads']), error_sum/(16*run['error_reads'])
        mean = (correct_sum+error_sum)/(16*run['located_reads'])
        counts = dict(total_reads=run['reads'], located_reads=run['located_reads'], unlocated_reads=run['unlocated_reads'],
                      correct_reads=run['correct_reads'], error_reads=run['error_reads'], correct_barcode_bases=16*run['correct_reads'],
                      error_barcode_bases=16*run['error_reads'], correct_quality_sum=correct_sum, error_quality_sum=error_sum)
        for field, n in counts.items():
            require(integer(row[field]) == n, name + ': ' + field + ' differs')
        for field, value in dict(correct_mean_barcode_Q=clean, error_mean_barcode_Q=error,
                                 correct_minus_error_mean_Q=clean-error, pooled_mean_barcode_Q=mean).items():
            close(row[field], value, name + ': ' + field)
        # Original generator reported only six decimal places for full barcode means.
        close(mean, pooled[name]['full_located_barcode_mean_Q'], name + ': rounded preserved pooled mean', 5.00001e-7)
        min_pass = sum(n for q, n in computed_min.items() if transform(q, shift) >= 15)
        saved_pass = pooled[name]['full_truth_located_barcode_minQ15_pass_n']
        if saved_pass != '':
            require(min_pass == integer(saved_pass), 'minQ15 count differs')
        else:
            require(shift == 0, 'Missing shifted-condition minQ15 count')
        if shift:
            old = conditions[name]
            require(integer(old['phred_shift']) == shift and integer(old['reads']) == run['reads'] and
                    integer(old['located_barcodes']) == run['located_reads'] and integer(old['pass_minQ15']) == min_pass,
                    name + ': original condition counts differ')
            require(old['headers_and_sequences_unchanged'] == 'TRUE' and integer(old['seed']) == 20260731, 'Original condition contract differs')
            require(integer(old['min_all_base_q']) == 1+shift and integer(old['max_all_base_q']) == 28+shift,
                    'Original shifted quality range differs')
            close(mean, old['mean_barcode_base_q'], name + ': rounded original barcode mean', 5.00001e-7)
            close(pooled[name]['full_dataset_mean_Q'], old['mean_all_base_q'], name + ': whole-base mean')
            close(float(original['mean_q'])+shift-1, old['mean_all_base_q'], name + ': exact shift whole-base mean')
            metrics = blaze[name]
            require(integer(metrics['shift']) == shift, 'BLAZE condition shift differs')
            tp, fp, fn = [integer(metrics[k]) for k in ['tp', 'fp', 'fn']]
            require(min(tp, fp, fn) >= 0 and tp+fp == integer(metrics['calls']) and
                    tp+fn == run['distinct_header_truth_barcodes'] == 5000, 'BLAZE count conservation differs')
            precision, recall, f1 = tp/(tp+fp), tp/(tp+fn), 2*tp/(2*tp+fp+fn)
            for field, value in [('precision', precision), ('recall', recall), ('f1', f1)]:
                close(metrics[field], value, name + ': BLAZE ' + field)
            close(metrics['full_dataset_mean_Q'], pooled[name]['full_dataset_mean_Q'], name + ': BLAZE whole-base mean join')
            addition = dict(blaze_metrics_status='available', blaze_tp=tp, blaze_fp=fp, blaze_fn=fn, blaze_calls=tp+fp,
                            blaze_precision=precision, blaze_recall=recall, blaze_f1=f1,
                            blaze_origin=metrics['origin'], blaze_source_table=metrics['source_table'])
        else:
            close(pooled[name]['full_dataset_mean_Q'], float(original['mean_q'])-1, 'Native whole-base mean from exact inverse')
            addition = dict(blaze_metrics_status='unavailable: no selected native2018 BLAZE discovery result',
                            blaze_tp='', blaze_fp='', blaze_fn='', blaze_calls='', blaze_precision='', blaze_recall='',
                            blaze_f1='', blaze_origin='', blaze_source_table='')
        joined.append(dict(dataset='L', **row, full_dataset_mean_Q=pooled[name]['full_dataset_mean_Q'],
                           full_truth_located_barcode_minQ15_pass_n=min_pass, **addition,
                           blaze_metric_scope='barcode discovery; TP/FP/FN count barcodes; unavailable is blank, not zero'))

    sample_check = run['sample_validation']
    require(sample_check['requested'] is True and sample_check['expected_reads'] == sample_check['found_reads'] == 50000 and
            sample_check['conditions_per_read'] == 12 and sample_check['read_condition_values_compared'] == 600000,
            'Incomplete 50,000-read sample verification')
    require(sample_check['source_sha256'] == inputs['sample_csv']['sha256'], 'Sample source hash differs')
    close(sample_check['maximum_absolute_mean_Q_difference'], 0, 'Sample maximum per-read difference')
    close(sample_check['tolerance'], 1e-12, 'Sample comparison tolerance', 0)
    sample = keyed(rows(args.sample_csv, delimiter=','), lambda r: r['read_id'], 'sample read ID')
    require(len(sample) == 50000 and len({r['truth_barcode'] for r in sample.values()}) == 5000,
            'Sample must contain 50,000 unique reads and all 5,000 truth barcodes')
    clean_rows = [r for r in sample.values() if integer(r['barcode_ED']) == 0]
    error_rows = [r for r in sample.values() if integer(r['barcode_ED']) > 0]
    require(clean_rows and error_rows and len(clean_rows)+len(error_rows) == 50000, 'Invalid sample ED groups')
    for name, shift in CONDITIONS.items():
        label = 'nanopore2018 native' if not shift else 'nanopore2018 +%d' % shift
        for field, group in [('sample_mean_barcode_Q', list(sample.values())),
                             ('sample_clean_mean_Q', clean_rows), ('sample_error_mean_Q', error_rows)]:
            close(math.fsum(float(r[label]) for r in group)/len(group), pooled[name][field], name + ': ' + field)
        require(integer(pooled[name]['sample_reads']) == 50000, 'Preserved sample count differs')
    return joined, dict(status='passed', output_published=False, full_fastq_read_by_validator=False,
        scope='Full selected Nanopore2018 input scan validated; exact inverse +1 to native; 12 quality conditions and 11 existing BLAZE results',
        reads=run['reads'], bases=run['bases'], located_reads=run['located_reads'], correct_ED0_reads=run['correct_reads'],
        incorrect_EDgt0_reads=run['error_reads'], unlocated_reads_excluded_from_quality_groups=run['unlocated_reads'],
        edit_distance_classes_checked=len(expected_ed), quality_conditions_checked=12, blaze_conditions_checked=11,
        native_blaze_available=False, missing_metric_encoding='blank; unavailable, not zero',
        exact_original_native_minimum_quality_histogram_checked=True,
        native_minQ15_read_count_from_exact_histogram=sum(n for q, n in computed_min.items() if q >= 15),
        independent_original_native_barcode_base_histogram='unavailable: original generator did not write it; new bins checked for integer conservation, group sums and rounded pooled means',
        mean_absolute_tolerance=1e-12, original_six_decimal_mean_tolerance=5.00001e-7,
        sample_read_condition_values_checked=600000, original_model_quality_support=[min(support), max(support)],
        original_header_sequence_sha256=run['header_sequence_sha256'], original_stored_p01_quality_sha256=run['quality_sha256'],
        recovered_native_quality_sha256=run['recovered_native_quality_sha256'],
        recovered_native_digest_scope='Newly computed digest of the deterministic inverse; no independent original native-quality digest was preserved',
        f1_formula='2*TP/(2*TP+FP+FN)', quality_regenerated=False, blaze_rerun=False,
        quality_groups='ED0 and ED>0 refer to observed truth-located 16-base barcode, independently of any tool assignment',
        inputs=inputs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name, help_text in [('scan-dir', 'Full scan output directory'), ('generation-summary', 'Original metric/value TSV'),
                            ('source-invariants', 'Original L_variant_invariants.tsv'),
                            ('native-minimum-histogram', 'Original native_barcode_min_q.tsv'),
                            ('output', 'Destination full_quality_with_blaze_f1.tsv'), ('report', 'Destination validation JSON')]:
        parser.add_argument('--'+name, type=Path, required=True, help=help_text)
    for name, default in [('model', SOURCE/'models/nanopore2018.gz'), ('source-manifest', SOURCE/'generator_source_manifest.tsv'),
                          ('quality-conditions', SOURCE/'quality_conditions_2018.tsv'), ('quality-summary', SOURCE/'quality_summary.tsv'),
                          ('discovery-metrics', SOURCE/'discovery_metrics.tsv'), ('sample-csv', SOURCE/'paired_50000_barcode_mean_Q.csv.gz'),
                          ('scanner-script', Path(__file__).with_name('summarize_full_barcode_quality_2018.py')),
                          ('locator-script', Path(__file__).with_name('barcode_locator.py'))]:
        parser.add_argument('--'+name, type=Path, default=default)
    args = parser.parse_args()
    report = dict(status='failed', output_published=False)
    try:
        joined, report = validate(args)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_name(args.output.name+'.partial')
        with temporary.open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(joined[0]), delimiter='\t', lineterminator='\n')
            writer.writeheader()
            writer.writerows(joined)
        temporary.replace(args.output)
        report['output_published'] = True
        report['output'] = dict(path=str(args.output.resolve()), rows=len(joined), bytes=args.output.stat().st_size, sha256=sha(args.output))
    except Exception as exc:
        report.update(status='failed', error=str(exc))
        raise
    finally:
        report.update(validator_sha256=sha(Path(__file__)), argv=sys.argv,
                      completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2)+'\n')
    print('Passed: %s reads; 12 quality conditions; 11 BLAZE F1 results; native BLAZE explicitly unavailable.' % report['reads'])


if __name__ == '__main__':
    main()
