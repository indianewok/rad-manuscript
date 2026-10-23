#!/usr/bin/env python3
"""Turn the retained wide Vireo checkpoint into one row per barcode and tool.

Selection, genotype state and reference membership are separate observations.
This script neither calls genotypes nor evaluates a new statistical test.
"""
import argparse
import csv

PREFIX = {'RAD': 'rad', 'BLAZE': 'blaze_panel_matched', 'Flexiplex': 'flexiplex'}
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--input', required=True)
p.add_argument('--output', required=True)
a = p.parse_args()

with open(a.input) as source, open(a.output, 'w', newline='') as target:
    reader = csv.DictReader(source)
    writer = csv.DictWriter(target, delimiter='\t', fieldnames=[
        'cell_barcode', 'tool', 'reference_present', 'reference_state',
        'reference_label', 'selected', 'query_state', 'query_label',
        'strict_identity_eligible', 'outcome'])
    writer.writeheader()
    seen = set()
    for row in reader:
        barcode = row['cell_barcode']
        if barcode in seen:
            raise ValueError('Duplicate barcode: ' + barcode)
        seen.add(barcode)
        present = row['illumina_reference_present'] == 'TRUE'
        reference_state = row['illumina_reference_state']
        reference_label = row['illumina_reference_label']
        eligible = present and reference_state == 'named_singlet'
        for tool, prefix in PREFIX.items():
            selected = row[prefix + '_query_selected'] == 'TRUE'
            state = row[prefix + '_vireo_state']
            label = row[prefix + '_vireo_label']
            if not selected:
                outcome = 'not_selected'
            elif state == 'named_singlet' and eligible:
                outcome = 'same' if label == reference_label else 'different'
            elif state in ('named_singlet', 'doublet', 'unassigned'):
                outcome = state
            else:
                outcome = 'missing_row'
            writer.writerow(dict(cell_barcode=barcode, tool=tool,
                reference_present=int(present), reference_state=reference_state,
                reference_label=reference_label, selected=int(selected),
                query_state=state, query_label=label,
                strict_identity_eligible=int(eligible), outcome=outcome))
