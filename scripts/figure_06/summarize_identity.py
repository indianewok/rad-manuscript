#!/usr/bin/env python3
"""Count fixed-reference identity outcomes with explicit denominators.

An excerpt produces excerpt counts only. Require --expected-reference-singlets
5782 for the full selected Figure 6 summary.
"""
import argparse
import collections
import csv

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--input', required=True)
p.add_argument('--output', required=True)
p.add_argument('--expected-reference-singlets', type=int, required=True)
a = p.parse_args()
counts = collections.defaultdict(collections.Counter)
with open(a.input) as source:
    for row in csv.DictReader(source, delimiter='\t'):
        if row['strict_identity_eligible'] == '1':
            counts[row['tool']][row['outcome']] += 1
with open(a.output, 'w', newline='') as target:
    fields = ['tool', 'reference_denominator', 'same', 'different', 'doublet',
              'unassigned', 'not_selected', 'missing_row', 'strict_recall',
              'conditional_concordance']
    writer = csv.DictWriter(target, delimiter='\t', fieldnames=fields)
    writer.writeheader()
    for tool, counter in sorted(counts.items()):
        denominator = sum(counter.values())
        if denominator != a.expected_reference_singlets:
            raise ValueError('Unexpected reference denominator for ' + tool)
        named = counter['same'] + counter['different']
        result = {key: counter[key] for key in fields[2:8]}
        result.update(tool=tool, reference_denominator=denominator,
            strict_recall=counter['same'] / denominator if denominator else '',
            conditional_concordance=counter['same'] / named if named else '')
        writer.writerow(result)
