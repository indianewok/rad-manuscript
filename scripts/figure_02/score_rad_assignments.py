#!/usr/bin/env python3
"""Score RAD assignments for the complete Figure 2 ScTagger-L input.

An original read with more than one emitted record is unassigned.  The CR tag
defines whether a retained assignment was corrected; CB is the assigned barcode.
The truth barcode is the first 16 bases of the original synthetic read ID.
"""
import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re


STATES = ('native_correct', 'corrected_correct', 'corrected_incorrect',
          'native_incorrect', 'unassigned')
TARGET_FIELDS = ('native_correct', 'corrected_correct', 'native_incorrect',
                 'corrected_incorrect')
ORIENTATION_SUFFIX = re.compile(r'-[FR](?:-CT)?$')
COMPLEMENT = str.maketrans('ACGTNacgtn', 'TGCANtgcan')
RAW_CLASSES = ('truth', 'other_custom_truth', 'global_catalogue_outside_custom',
               'outside_global_catalogue')


def open_text(path):
    return gzip.open(path, 'rt') if path.suffix == '.gz' else path.open()


def barcode_set(path):
    values = []
    with open_text(path) as handle:
        for line in handle:
            value = re.split(r'[\s,]+', line.strip())[0].removesuffix('-1')
            if not value or value.lower() == 'barcode':
                continue
            if not re.fullmatch('[ACGT]{16}', value):
                raise ValueError('Expected a 16-base barcode in ' + str(path))
            values.append(value)
    if len(values) != len(set(values)):
        raise ValueError('Duplicate barcode in ' + str(path))
    return set(values)


def canonical_barcode_sha256(values):
    return hashlib.sha256(('\n'.join(sorted(values)) + '\n').encode()).hexdigest()


def fastq_records(path):
    with open_text(path) as handle:
        while True:
            header = handle.readline()
            if not header:
                return
            sequence, separator, quality = (handle.readline() for _ in range(3))
            if not quality or not header.startswith('@') or not separator.startswith('+'):
                raise ValueError('Incomplete or invalid FASTQ record in ' + str(path))
            if len(sequence.rstrip('\r\n')) != len(quality.rstrip('\r\n')):
                raise ValueError('Sequence/quality lengths differ in ' + str(path))
            yield header.rstrip('\r\n')


def original_id(header):
    emitted_id = header[1:].split()[0]
    return ORIENTATION_SUFFIX.sub('', emitted_id)


def write_table(path, fields, records):
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter='\t',
                                lineterminator='\n')
        writer.writeheader()
        writer.writerows(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-fastq', type=Path, required=True)
    parser.add_argument('--output-fastq', type=Path, required=True)
    parser.add_argument('--truth-barcodes', type=Path, required=True)
    parser.add_argument('--catalogue-barcodes', type=Path, required=True,
                        help='Original Cell Ranger catalogue as DNA text, not a RAD bitlist')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--expected-reads', type=int, default=4993805)
    parser.add_argument('--expected-truth-barcodes', type=int, default=5000)
    args = parser.parse_args()
    destination = args.output_dir.resolve()
    if destination.exists():
        raise ValueError('Use a new scoring output directory')
    destination.mkdir(parents=True)
    truth = barcode_set(args.truth_barcodes)
    catalogue = barcode_set(args.catalogue_barcodes)
    if len(truth) != args.expected_truth_barcodes or not truth <= catalogue:
        raise ValueError('The complete truth whitelist must be contained in the catalogue')

    input_ids, input_truth = set(), set()
    id_hash = hashlib.sha256()
    for header in fastq_records(args.input_fastq):
        read_id = original_id(header)
        if read_id in input_ids or read_id[:16] not in truth:
            raise ValueError('Duplicate input ID or unknown truth barcode: ' + read_id)
        input_ids.add(read_id)
        input_truth.add(read_id[:16])
        id_hash.update((read_id + '\n').encode())
    total_reads = len(input_ids)
    if total_reads != args.expected_reads or input_truth != truth:
        raise ValueError('Input does not contain the complete stated ScTagger read universe')
    print('Validated input:', total_reads, 'reads and', len(input_truth), 'truth barcodes', flush=True)

    # First assignment is provisional.  A second record removes that original
    # ID's entire contribution, even if both records have the same final barcode.
    seen = {}
    counts, record_counts = Counter(), Counter()
    per_target = defaultdict(Counter)
    per_raw_source = defaultdict(Counter)
    emitted_targets = set()
    emitted_records = 0
    audit_path = destination / 'record_audit.tsv.gz'
    with gzip.open(audit_path, 'wt', compresslevel=6, newline='') as audit:
        writer = csv.writer(audit, delimiter='\t', lineterminator='\n')
        writer.writerow(['read_id', 'truth_barcode', 'rad_cb', 'rad_cr', 'strand',
                         'record_category', 'state', 'target_in_custom', 'target_in_catalogue',
                         'oriented_raw_barcode', 'raw_source_class'])
        for header in fastq_records(args.output_fastq):
            emitted_records += 1
            read_id = original_id(header)
            if read_id not in input_ids:
                raise ValueError('Emitted read ID is absent from the input: ' + read_id)
            tags = {}
            for field in header.split('\t')[1:]:
                parts = field.split(':', 2)
                if len(parts) == 3:
                    tags[parts[0]] = parts[2]
            target, raw = tags.get('CB', ''), tags.get('CR', '')
            if target and not re.fullmatch('[ACGT]{16}', target):
                raise ValueError('Invalid assigned CB: ' + target)
            true = read_id[:16]
            if target:
                state = ('corrected' if raw else 'native') + ('_correct' if target == true else '_incorrect')
                category = 'incorrect' if target != true else 'corrected' if raw else 'native'
                emitted_targets.add(target)
            else:
                state = category = 'unassigned'
            observed = raw or target
            if raw and tags.get('TS') == '-':
                observed = raw.translate(COMPLEMENT)[::-1]
            raw_class = ('truth' if observed == true else 'other_custom_truth' if observed in truth
                         else 'global_catalogue_outside_custom' if observed in catalogue
                         else 'outside_global_catalogue')
            record_counts[state] += 1
            writer.writerow([read_id, true, target, raw, tags.get('TS', ''), category,
                             state, int(target in truth), int(target in catalogue), observed, raw_class])
            if read_id not in seen:
                seen[read_id] = (target, state, raw_class)
                if state != 'unassigned':
                    counts[state] += 1
                    per_target[target][state] += 1
                    per_raw_source[raw_class][state] += 1
            elif seen[read_id] is not None:
                previous_target, previous_state, previous_raw_class = seen[read_id]
                if previous_state != 'unassigned':
                    counts[previous_state] -= 1
                    per_target[previous_target][previous_state] -= 1
                    per_raw_source[previous_raw_class][previous_state] -= 1
                counts['excluded_multiple_outputs'] += 1
                seen[read_id] = None
            if emitted_records % 1000000 == 0:
                print('Scored output records:', emitted_records, flush=True)

    assigned = sum(counts[state] for state in TARGET_FIELDS)
    states = {state: counts[state] for state in STATES[:-1]}
    states['unassigned'] = total_reads - assigned
    if sum(states.values()) != total_reads or min(states.values()) < 0:
        raise ValueError('Physical-read state partition does not conserve input reads')
    for state in TARGET_FIELDS:
        if sum(row[state] for row in per_target.values()) != states[state]:
            raise ValueError('Per-target counts differ from the physical-read totals')
        if sum(row[state] for row in per_raw_source.values()) != states[state]:
            raise ValueError('Raw-source classes differ from the physical-read totals')

    state_rows = [dict(tool='RAD', state=state, reads=value, denominator=total_reads,
                       fraction=value / total_reads, count_unit='unique physical read')
                  for state, value in states.items()]
    write_table(destination/'assignment_states.tsv', list(state_rows[0]), state_rows)
    fields = ['tool', 'barcode', 'is_truth', 'selected', *TARGET_FIELDS]
    target_rows = [dict(tool='RAD', barcode=barcode, is_truth=1, selected=1,
                        **{state: per_target[barcode][state] for state in TARGET_FIELDS})
                   for barcode in sorted(truth)]
    write_table(destination/'assignment_per_target.tsv', fields, target_rows)
    outside_rows = [dict(barcode=barcode, in_catalogue=int(barcode in catalogue),
                         **{state: per_target[barcode][state] for state in TARGET_FIELDS})
                    for barcode in sorted(emitted_targets-truth)]
    write_table(destination/'outside_custom_per_target.tsv',
                ['barcode', 'in_catalogue', *TARGET_FIELDS], outside_rows)
    raw_rows = [dict(raw_source_class=raw_class, state=state, reads=per_raw_source[raw_class][state])
                for raw_class in RAW_CLASSES for state in TARGET_FIELDS]
    write_table(destination/'raw_source_membership_by_outcome.tsv', list(raw_rows[0]), raw_rows)
    corrected = states['corrected_correct'] + states['corrected_incorrect']
    correction_rows = [dict(tool='RAD', state=state, reads=states[state], denominator=corrected,
                            fraction=states[state]/corrected if corrected else 0)
                       for state in ('corrected_correct', 'corrected_incorrect')]
    write_table(destination/'correction_only.tsv', list(correction_rows[0]), correction_rows)
    summary = dict(status='complete', input_reads=total_reads,
                   input_read_ids_sha256=id_hash.hexdigest(), truth_barcodes=len(truth),
                   truth_barcode_sha256=canonical_barcode_sha256(truth),
                   catalogue_barcodes=len(catalogue),
                   catalogue_barcode_sha256=canonical_barcode_sha256(catalogue),
                   output_records=emitted_records, unique_emitted_input_ids=len(seen),
                   assigned_physical_reads=assigned, excluded_multiple_outputs=counts['excluded_multiple_outputs'],
                   input_ids_with_no_output=total_reads-len(seen), states=states,
                   record_level_states=dict(record_counts),
                   distinct_emitted_targets=len(emitted_targets),
                   emitted_targets_outside_custom=len(emitted_targets-truth),
                   emitted_targets_outside_catalogue=len(emitted_targets-catalogue),
                   all_emitted_targets_in_custom=emitted_targets <= truth,
                   all_emitted_targets_in_catalogue=emitted_targets <= catalogue,
                   strict_raw_source_membership={name:dict(per_raw_source[name]) for name in RAW_CLASSES},
                   global_catalogue_outside_custom_assigned_reads=sum(per_raw_source['global_catalogue_outside_custom'].values()),
                   scoring_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   scope='Complete physical-read scoring; multiple emitted records for one original ID are unassigned')
    (destination/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
