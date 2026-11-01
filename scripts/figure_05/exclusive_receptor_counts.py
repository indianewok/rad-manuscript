#!/usr/bin/env python3
"""Convert per-barcode receptor counts to native / corrected-only / assigned.

The Flexiplex `corrected_*` columns include native reads. RAD and
BLAZE's candidate tables already contain corrected-only reads. Require the
caller to state this contract rather than guessing from the tool name.
"""
import argparse
import csv

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--input', required=True)
p.add_argument('--output', required=True)
p.add_argument('--tool', required=True)
p.add_argument('--corrected-column', choices=['cumulative', 'exclusive'], required=True)
a = p.parse_args()

with open(a.input) as source, open(a.output, 'w', newline='') as target:
    reader = csv.DictReader(source, delimiter='\t')
    writer = csv.DictWriter(target, delimiter='\t', fieldnames=[
        'tool', 'barcode', 'celltype', 'receptor',
        'native', 'corrected_only', 'assigned'])
    writer.writeheader()
    seen = set()
    for row in reader:
        barcode = row['barcode']
        if barcode in seen:
            raise ValueError('Duplicate barcode: ' + barcode)
        seen.add(barcode)
        for receptor in ('bcr', 'tcr', 'unmapped'):
            native = int(row['native_' + receptor])
            corrected_only = int(row['corrected_' + receptor])
            if a.corrected_column == 'cumulative':
                corrected_only -= native
            if native < 0 or corrected_only < 0:
                raise ValueError('Invalid counts for ' + barcode)
            writer.writerow(dict(tool=a.tool, barcode=barcode,
                celltype=row['celltype'], receptor=receptor,
                native=native, corrected_only=corrected_only,
                assigned=native + corrected_only))
