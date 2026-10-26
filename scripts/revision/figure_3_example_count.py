#!/usr/bin/env python3
"""Count an identity-closed C2 excerpt; a duplicate row excludes the whole read."""
import collections
import csv
import sys

assignments, target_file, output = sys.argv[1:]
with open(assignments, newline='') as stream:
    rows = list(csv.DictReader(stream, delimiter='\t'))
with open(target_file) as stream:
    targets = stream.read().splitlines()
assert len(targets) == len(set(targets)), 'Duplicate supplied target'
multiplicity = collections.Counter(row['original_id'] for row in rows)
counts = collections.Counter({target: 0 for target in targets})
for row in rows:
    assert row['original_id'], 'Missing physical read identity'
    if row['target'] in counts and multiplicity[row['original_id']] == 1:
        counts[row['target']] += 1
with open(output, 'w', newline='') as stream:
    writer = csv.writer(stream, delimiter='\t', lineterminator='\n')
    writer.writerow(['barcode', 'strict_physical_reads'])
    writer.writerows(counts.items())
print(f'{len(rows)} assignment rows; {len(multiplicity)} physical IDs; '
      f'{sum(n > 1 for n in multiplicity.values())} ambiguous IDs excluded; '
      f'{sum(counts.values())} strict reads to requested targets')
