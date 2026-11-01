#!/usr/bin/env python3
"""Calculate the three correction-category percentages for each example target."""
import csv
import sys

source, destination = sys.argv[1:]
classes = {'noncatalog_to_selected': 'Corrected off-list',
           'cellranger_to_different_cellranger_K': 'Failure Mode 1',
           'catalog_noncell_to_selected_A': 'Failure Mode 2'}
with open(source, newline='') as stream:
    rows = list(csv.DictReader(stream, delimiter='\t'))
with open(destination, 'w', newline='') as stream:
    writer = csv.writer(stream, delimiter='\t', lineterminator='\n')
    writer.writerow(['tool', 'barcode', 'category', 'count', 'denominator_O', 'percent'])
    for row in rows:
        denominator = int(row['unique_read_target_assignments_O'])
        for column, category in classes.items():
            count = int(row[column])
            assert 0 <= count <= denominator
            percent = 100 * count / denominator if denominator else ''
            writer.writerow([row['tool'], row['target_barcode'], category,
                             count, denominator, percent])
