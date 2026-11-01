#!/usr/bin/env python3
"""Tabulate Figure 2 RAD assignments from the source-bearing record audit.

This reproduces the plotted truth-5000 global/custom-list run. Any original
read with multiple emitted records is excluded, including duplicate records
to the same target. Native status follows the producer's empty-CR convention.
"""
import argparse
import csv
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path


STATES = ['native_correct', 'corrected_correct', 'native_incorrect', 'corrected_incorrect']


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for data in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--truth', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--input-reads', type=int, default=4993805)
    args = parser.parse_args()
    truth = sorted({line.strip() for line in args.truth.read_text().splitlines() if line.strip()})
    if len(truth) != 5000:
        raise ValueError('The plotted run requires the complete 5,000-barcode truth list')
    target_index = {barcode: i for i, barcode in enumerate(truth)}
    target_counts = [[0] * 4 for _ in truth]
    counts = Counter()
    seen = {}
    ambiguous = records = 0
    opener = gzip.open if args.audit.suffix == '.gz' else open
    with opener(args.audit, 'rt', newline='') as handle:
        for row in csv.DictReader(handle, delimiter='\t'):
            records += 1
            rid = row['read_id']
            previous = seen.get(rid)
            if previous is not None:
                if previous:
                    index, state = divmod(previous - 1, 4)
                    counts[STATES[state]] -= 1
                    target_counts[index][state] -= 1
                    seen[rid] = 0
                    ambiguous += 1
                continue
            source = row['truth_barcode']
            target = row['rad_cb']
            if source != rid[:16] or source not in target_index or target not in target_index:
                raise ValueError('Record violates the plotted truth-list assignment contract: ' + rid)
            corrected = bool(row['rad_cr'])
            correct = target == source
            state = (1 if corrected else 0) if correct else (3 if corrected else 2)
            index = target_index[target]
            seen[rid] = index * 4 + state + 1
            counts[STATES[state]] += 1
            target_counts[index][state] += 1
    assigned = sum(counts.values())
    unassigned = args.input_reads - assigned - ambiguous
    if unassigned < 0 or assigned + ambiguous != len(seen):
        raise ValueError('Input-read conservation failed')
    counts['multiple_outputs_excluded'] = ambiguous
    counts['unassigned'] = unassigned
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / 'RAD_assignment_states.tsv').open('w', newline='') as handle:
        writer = csv.writer(handle, delimiter='\t', lineterminator='\n')
        writer.writerow(['tool', 'state', 'reads', 'input_reads'])
        for state in STATES + ['multiple_outputs_excluded', 'unassigned']:
            writer.writerow(['RAD', state, counts[state], args.input_reads])
    with (args.output_dir / 'RAD_assignment_per_target.tsv').open('w', newline='') as handle:
        writer = csv.writer(handle, delimiter='\t', lineterminator='\n')
        writer.writerow(['tool', 'barcode', 'selected'] + STATES)
        for barcode, values in zip(truth, target_counts):
            writer.writerow(['RAD', barcode, 1] + values)
    summary = dict(tool='RAD', input_reads=args.input_reads, emitted_records=records,
        distinct_emitted_input_ids=len(seen), assigned_unambiguous=assigned,
        assignment_states=dict(counts), global_whitelist='truth5000', custom_whitelist='truth5000',
        counting_unit='original input read with exactly one emitted record',
        audit_sha256=digest(args.audit), truth_sha256=digest(args.truth))
    (args.output_dir / 'RAD_assignment_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
