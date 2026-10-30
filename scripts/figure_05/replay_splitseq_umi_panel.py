#!/usr/bin/env python3
"""Recount Figure 5H from final RAD ED2 and native Flexiplex ED2 records.

Records with a nonempty barcode and UMI contribute to the comparison. Distinct
read IDs and exact UMI strings are counted within each published physical cell.
The published short-read UMI counts are retained from the expected source table.
No read-depth sampling, UMI clustering or UMI-intersection calculation is applied.
"""
import argparse
import collections
import csv
import gzip
import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPLEMENT = str.maketrans('ACGTNacgtn', 'TGCANtgcan')
FIELDS = ['prism_row_1based', 'published_cell_barcode', 'canonical_barcode', 'sample',
          'published_sr_umis', 'rad_ed2_reads', 'rad_ed2_umis',
          'flexiplex_ed2_polyt_reads', 'flexiplex_ed2_polyt_umis']
COUNT_FIELDS = FIELDS[5:]
IDENTITY_FIELDS = FIELDS[:4]


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read_rows(path):
    opener = gzip.open if path.suffix == '.gz' else open
    delimiter = ',' if '.csv' in path.name else '\t'
    with opener(path, 'rt') as handle:
        yield from csv.DictReader(handle, delimiter=delimiter)


def write_rows(path, rows):
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def aggregate(path, cells, primers, native_component=False):
    """Apply the executed inclusion and physical-well normalization rules."""
    reads = {cell: set() for cell in cells}
    umis = {cell: set() for cell in cells}
    global_reads, published_reads = set(), set()
    counts = collections.Counter()
    for row in read_rows(path):
        counts['assignment_rows'] += 1
        if native_component:
            read_id = row['Read']
            barcode = '_'.join([row['BC3'], row['BC2'], row['BC1']])
            umi = row['UB'].translate(COMPLEMENT)[::-1]
        else:
            read_id, barcode, umi = row['read_id'], row['normalized_barcode'], row['umi']
        if not read_id.startswith('SRR13948564.') or not read_id[12:].isdigit():
            raise ValueError('Unexpected original read ID: ' + read_id)
        number = int(read_id[12:])
        global_reads.add(number)
        if not barcode or not umi:
            counts['empty_barcode_or_umi_rows'] += 1
            continue
        parts = barcode.split('_')
        if len(parts) != 3 or parts[0] not in primers:
            counts['unmappable_rt_primer_rows'] += 1
            continue
        cell = '_'.join([primers[parts[0]], parts[1], parts[2]])
        if cell not in cells:
            counts['outside_published_cells_rows'] += 1
            continue
        counts['published_assignment_rows'] += 1
        counts['published_10nt_umi_rows' if len(umi) == 10 else 'published_other_umi_length_rows'] += 1
        reads[cell].add(number)
        umis[cell].add(umi)
        published_reads.add(number)
    excluded = sum(counts[k] for k in ['empty_barcode_or_umi_rows', 'unmappable_rt_primer_rows',
                                      'outside_published_cells_rows'])
    if counts['assignment_rows'] != excluded + counts['published_assignment_rows']:
        raise ValueError('Assignment-row conservation failed')
    totals = dict(counts, globally_distinct_source_reads=len(global_reads),
                  published_distinct_source_reads=len(published_reads),
                  published_read_cell_pairs=sum(map(len, reads.values())),
                  published_cell_umi_pairs=sum(map(len, umis.values())),
                  published_cells=len(cells), cells_with_reads=sum(bool(v) for v in reads.values()),
                  median_reads_per_cell=statistics.median(map(len, reads.values())),
                  median_umis_per_cell=statistics.median(map(len, umis.values())))
    totals['repeated_read_cell_records'] = counts['published_assignment_rows'] - totals['published_read_cell_pairs']
    if not (totals['published_distinct_source_reads'] <= totals['globally_distinct_source_reads']
            and totals['published_distinct_source_reads'] <= totals['published_read_cell_pairs']
            and totals['published_read_cell_pairs'] <= counts['published_assignment_rows']
            and totals['published_cell_umi_pairs'] <= counts['published_assignment_rows']):
        raise ValueError('Read/UMI count conservation failed')
    return {cell: (len(reads[cell]), len(umis[cell])) for cell in cells}, totals


def run(args, report):
    sources = [('rad_assignments', args.rad_assignments), ('component_native_stats', args.component_native_stats),
               ('published_cells', args.cells), ('rt_primer_map', args.rt_primers),
               ('expected_figure5H_table', args.expected_table)]
    report['inputs'] = [dict(role=role, path=str(path), bytes=path.stat().st_size, sha256=sha256(path))
                        for role, path in sources]
    cells = list(read_rows(args.cells))
    by_cell = {row['canonical_barcode']: row for row in cells}
    if len(cells) != 568 or len(by_cell) != 568:
        raise ValueError('Expected exactly 568 distinct published physical cells')
    if [int(row['prism_row_1based']) for row in cells] != list(range(1, 569)):
        raise ValueError('Published cell rows must retain original Prism order 1–568')
    rt = list(read_rows(args.rt_primers))
    t_primers = {row['well']: row['sequence'].strip() for row in rt if row['type'] == 'T'}
    primers = {row['sequence'].strip(): t_primers[row['well']] for row in rt}
    if len(primers) != 96 or len(t_primers) != 48:
        raise ValueError('Expected 96 RT sequences paired into 48 physical wells')
    expected = list(read_rows(args.expected_table))
    if len(expected) != 568 or len({row['canonical_barcode'] for row in expected}) != 568:
        raise ValueError('Expected table must contain 568 distinct physical cells')
    for cell, row in zip(cells, expected):
        for field in IDENTITY_FIELDS:
            if cell[field] != row[field]:
                raise ValueError('Expected-table cell identity or row-order mismatch: ' + field)
        if int(row['published_sr_umis']) < 0:
            raise ValueError('Published short-read UMI count must be nonnegative')
    rad, report['rad_ed2'] = aggregate(args.rad_assignments, by_cell, primers)
    print('RAD ED2 assignment counts completed', flush=True)
    component, report['flexiplex_ed2_polyt'] = aggregate(args.component_native_stats, by_cell, primers, True)
    print('Flexiplex ED2 native-record counts completed', flush=True)
    observed, mismatches = [], []
    for row in expected:
        key = row['canonical_barcode']
        result = {field: row[field] for field in FIELDS[:5]}
        result.update(rad_ed2_reads=rad[key][0], rad_ed2_umis=rad[key][1],
                      flexiplex_ed2_polyt_reads=component[key][0], flexiplex_ed2_polyt_umis=component[key][1])
        for field in COUNT_FIELDS:
            if result[field] != int(row[field]):
                mismatches.append(dict(cell=key, field=field, expected=int(row[field]), observed=result[field]))
        observed.append(result)
    report['compared_count_values'] = 568 * len(COUNT_FIELDS)
    report['count_mismatches'] = mismatches
    if mismatches:
        raise ValueError('Final ED2 counts differ from expected table: ' + str(len(mismatches)) + ' values')
    output = args.output_dir / 'per_cell_counts.tsv'
    write_rows(output, observed)
    report['output'] = dict(path=str(output), bytes=output.stat().st_size, sha256=sha256(output))
    report['output_valid'] = True
    report['status'] = 'PASS'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rad-assignments', type=Path, default=ROOT / 'checkpoints/figure_05/RAD_ED2_assignments.tsv.gz')
    parser.add_argument('--component-native-stats', type=Path, default=ROOT / 'checkpoints/figure_05/component_ED2_polyT_native_stats.tsv.gz')
    parser.add_argument('--cells', type=Path, default=ROOT / 'data/figure_05/splitseq_cells.tsv')
    parser.add_argument('--rt-primers', type=Path, default=ROOT / 'data/figure_05/rt_primer_well_map.csv')
    parser.add_argument('--expected-table', '--expected5Htable', dest='expected_table', type=Path,
                        default=ROOT / 'source_data/figure_05/splitseq_umi_panel_ED2_568.tsv')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'results/figure_05_umi_panel_ED2')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = dict(status='FAILED', output_valid=False, raw_demultiplexing_rerun=False, depth_sampling=False,
                  umi_correction_or_clustering=False,
                  rule='Include records with a nonempty barcode and UMI. Count distinct original read IDs and exact UMI strings within each published physical cell; both RT primer variants map to the well T-primer sequence.',
                  component_normalization='BC3_BC2_BC1; reverse complement UB; preserve all UMI lengths.',
                  shortread_axis='Published short-read UMI annotations retained from expected source table.',
                  code_sha256=sha256(Path(__file__)))
    try:
        run(args, report)
    except Exception as error:
        report['error'] = str(error)
        print('FAILED: ' + str(error), file=sys.stderr)
    (args.output_dir / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    if report['status'] != 'PASS':
        return 1
    print('PASS: all 2,272 final ED2 read/UMI values match across 568 published cells.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
