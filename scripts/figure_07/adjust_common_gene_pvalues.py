#!/usr/bin/env python3
"""Recompute BH adjustment over the complete selected common gene family.

Input contains retained Wilcoxon P values and effect sizes. This does not rerun
Wilcoxon tests, normalize counts, or derive a common universe from raw matrices.
Do not substitute a preview excerpt for the full 8,135-gene family.
"""
import argparse
import csv
import gzip


def bh(pvalues):
    order = sorted(range(len(pvalues)), key=pvalues.__getitem__)
    adjusted = [0.0] * len(order)
    previous = 1.0
    for rank in range(len(order), 0, -1):
        index = order[rank - 1]
        previous = min(previous, pvalues[index] * len(order) / rank)
        adjusted[index] = previous
    return adjusted


p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--input', required=True)
p.add_argument('--output', required=True)
p.add_argument('--expected-genes', type=int, default=8135)
a = p.parse_args()
opener = gzip.open if a.input.endswith('.gz') else open
with opener(a.input, 'rt') as source:
    rows = list(csv.DictReader(source, delimiter='\t'))
genes = None
for tool in ('RAD', 'BLAZE', 'Flexiplex'):
    group = [row for row in rows if row['tool'] == tool]
    ids = {row['gene_id'] for row in group}
    if len(group) != a.expected_genes or len(ids) != a.expected_genes:
        raise ValueError('Incomplete or duplicated gene family for ' + tool)
    if genes is not None and genes != ids:
        raise ValueError('Different gene universe for ' + tool)
    genes = ids
    for prefix in ('tool', 'Illumina'):
        values = [float(row[prefix + '_p_value']) for row in group]
        if any(not 0 <= value <= 1 for value in values):
            raise ValueError('Invalid P value')
        for row, adjusted in zip(group, bh(values)):
            row[prefix + '_BH_FDR_common'] = adjusted
with open(a.output, 'w', newline='') as target:
    fields = ['gene_id', 'gene_symbol', 'tool', 'tool_log2FC', 'tool_p_value',
              'tool_BH_FDR_common', 'Illumina_log2FC', 'Illumina_p_value',
              'Illumina_BH_FDR_common']
    writer = csv.DictWriter(target, delimiter='\t', fieldnames=fields)
    writer.writeheader()
    writer.writerows({key: row[key] for key in fields} for row in rows)
