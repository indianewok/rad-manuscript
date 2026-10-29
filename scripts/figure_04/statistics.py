#!/usr/bin/env python3
"""Friedman and Dunn tests for Figure 4's 37 matched inputs and three tools.

Each metric is a separate family: Friedman omnibus test, then two Dunn
comparisons (RAD versus BLAZE and RAD versus Flexiplex), with alpha=0.05.
Within-input ties receive average ranks. Friedman uses its tie correction and
the chi-square approximation with two degrees of freedom. Dunn uses two-sided
normal probabilities, multiplied by the two comparisons in that metric.

GraphPad's methods:
https://www.graphpad.com/guides/prism/latest/statistics/how_the_friedman_test_works.htm
https://www.graphpad.com/guides/prism/latest/statistics/stat_how_the_dunn_method_for_nonpar.htm

Run from the repository root. Outputs contain three Friedman rows, six Dunn
rows and a JSON receipt binding both tables to the exact input bytes. Use a
new output directory; existing result files are not replaced.
"""
import argparse
import csv
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import hashlib
import io
import json
import math
from pathlib import Path

TOOLS = ('RAD', 'BLAZE', 'Flexiplex')
METRICS = ('precision', 'recall', 'f1')
MATCHED_INPUTS = 37
ALPHA = 0.05


def read_metrics(path):
    """Validate 37 complete tool triplets and the metrics' barcode counts."""
    contents = path.read_bytes()
    reader = csv.DictReader(io.StringIO(contents.decode('utf-8-sig')), delimiter='\t')
    required = {'canonical_id', 'tool', 'calls', 'reference_n', 'tp', 'fp', 'fn', *METRICS}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError('Missing required metric-table columns')
    rows = list(reader)
    datasets, by_key, references = [], {}, {}
    for row in rows:
        dataset, tool = row['canonical_id'], row['tool']
        if not dataset or tool not in TOOLS or (dataset, tool) in by_key:
            raise ValueError('Invalid or duplicate input/tool: ' + repr((dataset, tool)))
        if dataset not in datasets:
            datasets.append(dataset)
        try:
            calls, reference, tp, fp, fn = (int(row[key]) for key in ('calls', 'reference_n', 'tp', 'fp', 'fn'))
            values = [Decimal(row[key]) for key in METRICS]
        except (ValueError, InvalidOperation) as error:
            raise ValueError('Invalid numeric field for ' + dataset + '/' + tool) from error
        if reference <= 0 or min(calls, tp, fp, fn) < 0 or calls != tp + fp or reference != tp + fn:
            raise ValueError('Inconsistent barcode counts for ' + dataset + '/' + tool)
        if dataset in references and references[dataset] != reference:
            raise ValueError('Tools must share one reference size for ' + dataset)
        references[dataset] = reference
        expected = (tp / calls if calls else 0.0, tp / reference, 2 * tp / (calls + reference))
        for metric, observed, wanted in zip(METRICS, values, expected):
            if not observed.is_finite() or not Decimal(0) <= observed <= Decimal(1):
                raise ValueError('Metric must be finite and within 0–1: ' + dataset + '/' + metric)
            if abs(float(observed) - wanted) > 1e-9:
                raise ValueError('Metric differs from its counts: ' + dataset + '/' + metric)
        by_key[dataset, tool] = dict(zip(METRICS, values))
    if len(rows) != MATCHED_INPUTS * len(TOOLS) or len(datasets) != MATCHED_INPUTS:
        raise ValueError('Expected 111 observations from 37 inputs')
    if set(by_key) != {(dataset, tool) for dataset in datasets for tool in TOOLS}:
        raise ValueError('Every input must contain RAD, BLAZE and Flexiplex')
    return datasets, by_key, hashlib.sha256(contents).hexdigest()


def rank_row(values):
    """Rank one input's three values from low to high; average tied ranks."""
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks, tie_sum = [None] * len(values), 0
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        average_rank = Fraction(start + 1 + end, 2)
        for column in order[start:end]:
            ranks[column] = average_rank
        size = end - start
        tie_sum += size**3 - size
        start = end
    return ranks, tie_sum


def calculate(datasets, by_key):
    """Compute the same Friedman/Dunn procedure separately for each metric."""
    friedman_rows, dunn_rows = [], []
    n, k = len(datasets), len(TOOLS)
    for metric in METRICS:
        ranked = [rank_row([by_key[dataset, tool][metric] for tool in TOOLS]) for dataset in datasets]
        rank_sums = [sum((row[0][column] for row in ranked), Fraction()) for column in range(k)]
        mean_ranks = [total / n for total in rank_sums]
        tie_sum = sum(row[1] for row in ranked)
        tie_correction = 1 - Fraction(tie_sum, n * (k**3 - k))
        if tie_correction == 0:
            raise ValueError('Friedman is undefined: all tools tie in every input for ' + metric)
        uncorrected = Fraction(12, n*k*(k+1)) * sum(total**2 for total in rank_sums) - 3*n*(k+1)
        statistic = float(uncorrected / tie_correction)
        # Three tools give df=2; the chi-square survival probability is exp(-Q/2).
        p_value = math.exp(-statistic / 2)
        friedman = dict(metric=metric, matched_inputs=n, groups=k,
                       tie_sum=tie_sum, tie_correction=float(tie_correction),
                       statistic=statistic, df=k-1, p_value=p_value,
                       alpha=ALPHA, significant=p_value < ALPHA)
        for tool, total, mean in zip(TOOLS, rank_sums, mean_ranks):
            friedman['rank_sum_' + tool] = float(total)
            friedman['mean_rank_' + tool] = float(mean)
        friedman_rows.append(friedman)

        # GraphPad's repeated-measures Dunn denominator. Ranks use all three tools.
        standard_error = math.sqrt(k*(k+1)/(6*n))
        family_size = k - 1
        for column in (1, 2):
            difference = float(mean_ranks[0] - mean_ranks[column])
            z = abs(difference) / standard_error
            p_raw = math.erfc(z / math.sqrt(2))
            p_adjusted = min(1.0, family_size * p_raw)
            dunn_rows.append(dict(metric=metric, control='RAD', comparator=TOOLS[column],
                matched_inputs=n, groups=k, comparisons_in_family=family_size,
                control_rank_sum=float(rank_sums[0]), comparator_rank_sum=float(rank_sums[column]),
                control_mean_rank=float(mean_ranks[0]), comparator_mean_rank=float(mean_ranks[column]),
                mean_rank_difference=difference, standard_error=standard_error,
                z=z, p_raw=p_raw, p_adjusted=p_adjusted, alpha=ALPHA,
                significant=p_adjusted < ALPHA))
    return friedman_rows, dunn_rows


def write_table(path, fields, rows):
    with path.open('x', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metrics', type=Path, default=Path('source_data/figure_04/barcode_detection_metrics.tsv'))
    parser.add_argument('--output-dir', type=Path, default=Path('results/figure_04/statistics'))
    args = parser.parse_args()
    destinations = [args.output_dir / name for name in ('friedman.tsv', 'dunn.tsv', 'statistics.json')]
    if any(path.exists() or path.is_symlink() for path in destinations):
        raise FileExistsError('Use a new output directory; statistical result files already exist')
    datasets, by_key, metrics_sha256 = read_metrics(args.metrics)
    friedman, dunn = calculate(datasets, by_key)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_table(destinations[0], ['metric', 'matched_inputs', 'groups',
        'rank_sum_RAD', 'rank_sum_BLAZE', 'rank_sum_Flexiplex',
        'mean_rank_RAD', 'mean_rank_BLAZE', 'mean_rank_Flexiplex',
        'tie_sum', 'tie_correction', 'statistic', 'df', 'p_value', 'alpha', 'significant'], friedman)
    write_table(destinations[1], ['metric', 'control', 'comparator', 'matched_inputs', 'groups',
        'comparisons_in_family', 'control_rank_sum', 'comparator_rank_sum',
        'control_mean_rank', 'comparator_mean_rank', 'mean_rank_difference',
        'standard_error', 'z', 'p_raw', 'p_adjusted', 'alpha', 'significant'], dunn)
    receipt = dict(schema_version=1, metrics_sha256=metrics_sha256,
        method_settings=dict(matched_inputs=MATCHED_INPUTS, tools=list(TOOLS), metrics=list(METRICS),
            control='RAD', comparisons_per_metric=2, alpha=ALPHA,
            friedman='within-row average ranks; tie-corrected; chi-square df2 approximation',
            dunn='two-sided normal; adjusted P=min(1,2*P_raw)'),
        outputs={path.name: dict(rows=len(rows), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                 for path, rows in zip(destinations[:2], (friedman, dunn))})
    with destinations[2].open('x') as handle:
        json.dump(receipt, handle, indent=2)
        handle.write('\n')
    print('Wrote 3 Friedman rows, 6 Dunn rows and their receipt to', args.output_dir)


if __name__ == '__main__':
    main()
