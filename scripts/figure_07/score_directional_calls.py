#!/usr/bin/env python3
"""Build the 594-cell directional threshold grid from adjusted gene statistics.

Illumina truth stays fixed at BH FDR < .05 and abs(log2FC) > 1. All cutoffs
are strict. A zero precision/recall/F1 denominator yields zero.
"""
import argparse
import csv

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--input', required=True)
p.add_argument('--output', required=True)
a = p.parse_args()
with open(a.input) as source:
    rows = list(csv.DictReader(source, delimiter='\t'))
output = []
for tool in ('RAD', 'BLAZE', 'Flexiplex'):
    group = [row for row in rows if row['tool'] == tool]
    genes = {row['gene_id'] for row in group}
    if len(group) != 8135 or len(genes) != 8135:
        raise ValueError('The complete 8,135-gene family is required')
    for direction, sign in [('H146_high', 1), ('H526_high', -1)]:
        truth = {row['gene_id'] for row in group
                 if float(row['Illumina_BH_FDR_common']) < .05
                 and sign * float(row['Illumina_log2FC']) > 1}
        for fdr in (1e-8, 1e-6, 1e-5, 1e-4, .001, .005, .01, .05, .1):
            for effect in (.1, .25, .5, .75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3):
                called = {row['gene_id'] for row in group
                          if float(row['tool_BH_FDR_common']) < fdr
                          and sign * float(row['tool_log2FC']) > effect}
                tp, fp, fn = len(called & truth), len(called - truth), len(truth - called)
                tn = len(genes - called - truth)
                output.append(dict(tool=tool, direction=direction, tool_BH_FDR_cutoff=fdr,
                    tool_abs_log2FC_cutoff=effect, genes=len(genes), truth_positive=len(truth),
                    predicted_positive=len(called), TP=tp, FP=fp, FN=fn, TN=tn,
                    precision=tp/(tp+fp) if tp+fp else 0,
                    recall=tp/(tp+fn) if tp+fn else 0,
                    F1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0))
with open(a.output, 'w', newline='') as target:
    writer = csv.DictWriter(target, delimiter='\t', fieldnames=list(output[0]))
    writer.writeheader()
    writer.writerows(output)
