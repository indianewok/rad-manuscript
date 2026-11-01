#!/usr/bin/env python3
"""Extract the Figure 3B–C observations from the saved manuscript Prism layout.

The historical RAGE-seq arm retains assignment-record counts. The ScTagger
and LongBench arms retain strict single-output physical-read counts. Prism
stores target-count observations without the original target barcode strings;
row ordinals preserve their plotted order without inventing barcode identities.
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

LAYOUT = '4B74E124-3EC5-4749-A164-AA426B306E0C'
DATASETS = {'ScT': 'ScTagger-L', 'LB': 'LongBench SC-ONT', 'RSQ': 'RAGE-seq'}
INPUT_READS = {'ScTagger-L': 4993805, 'LongBench SC-ONT': 10000000, 'RAGE-seq': 20346396}
TOOLS = {'R': 'RAD', 'B': 'BLAZE', 'F': 'Flexiplex'}


def title(value):
    return value.get('string', '') if isinstance(value, dict) else value


def integer(value):
    number = float(value)
    if not number.is_integer():
        raise ValueError('Expected an integer read count: ' + value)
    return int(number)


def write_tsv(path, columns, rows, compressed=False):
    text = io.StringIO(newline='')
    writer = csv.DictWriter(text, fieldnames=columns, delimiter='\t', lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    data = text.getvalue().encode('utf-8')
    if compressed:
        with path.open('wb') as raw:
            with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as handle:
                handle.write(data)
    else:
        path.write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prism', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    source = args.prism.read_bytes()
    provenance = dict(source_sha256=hashlib.sha256(source).hexdigest(), layout_id=LAYOUT,
        barcode_identities_in_target_table=False, historical_RAGE_list_seeds=None,
        historical_RAGE_complete_BLAZE_execution_logs=False, tables=[])
    with zipfile.ZipFile(io.BytesIO(source)) as archive:
        doc = json.loads(archive.read('document.json'))
        layout = json.loads(archive.read('layouts/' + LAYOUT + '/sheet.json'))
        graphs = [json.loads(archive.read('graphs/' + uid + '/sheet.json')) for uid in layout['linkedGraphSheets']]
        totals_graph = next(g for g in graphs if g['title'] == 'Panel J')
        targets_graph = next(g for g in graphs if g['title'] == 'Panel K')
        sheets = {}
        owners = {}
        for uid in doc['sheets']['data']:
            sheet = json.loads(archive.read('data/sheets/' + uid + '/sheet.json'))
            sheets[uid] = sheet
            for ds in sheet['table'].get('dataSets', []):
                owners[ds] = uid

        def get_table(graph):
            owner_ids = {owners[uid] for uid in graph['inputDataSets']}
            if len(owner_ids) != 1:
                raise ValueError('Graph uses multiple tables: ' + graph['title'])
            sheet = sheets[owner_ids.pop()]
            path = 'data/tables/' + sheet['table']['uid'] + '/data.csv'
            data = archive.read(path)
            provenance['tables'].append(dict(graph_id=graph['uid'], graph_title=graph['title'],
                sheet_id=sheet['uid'], csv_member=path, csv_sha256=hashlib.sha256(data).hexdigest(),
                plotted_dataset_ids=graph['inputDataSets']))
            return sheet, list(csv.reader(io.StringIO(data.decode('utf-8-sig'))))

        sheet, cells = get_table(totals_graph)
        offsets = {}
        offset = 1
        for uid in sheet['table']['dataSets']:
            ds = json.loads(archive.read('data/sets/' + uid + '.json'))
            width = len(ds['replicates']) if 'replicates' in ds else sheet['table'].get('replicatesCount', 1)
            offsets[uid] = (offset, width, title(ds['title']))
            offset += width
        totals = []
        for row in cells:
            if not row or not row[0].strip():
                continue
            dataset = {'scTagger-L': 'ScTagger-L', 'LongBench sc-ONT': 'LongBench SC-ONT', 'RAGE-seq': 'RAGE-seq'}[row[0]]
            unit = 'assignment_records' if dataset == 'RAGE-seq' else 'strict_single_output_original_reads'
            for uid in totals_graph['inputDataSets']:
                start, width, tool = offsets[uid]
                for rep in range(width):
                    totals.append(dict(dataset=dataset, tool=tool, replicate=rep + 1,
                        assigned_reads=integer(row[start + rep]), input_reads=INPUT_READS[dataset], count_unit=unit))

        sheet, cells = get_table(targets_graph)
        offsets = {}
        offset = 1
        for uid in sheet['table']['dataSets']:
            ds = json.loads(archive.read('data/sets/' + uid + '.json'))
            width = len(ds['replicates']) if 'replicates' in ds else sheet['table'].get('replicatesCount', 1)
            if width != 1:
                raise ValueError('Expected one count column per target dataset')
            offsets[uid] = (offset, title(ds['title']))
            offset += 1
        targets = []
        for uid in targets_graph['inputDataSets']:
            column, name = offsets[uid]
            match = re.fullmatch(r'([RBF])_(ScT|LB|RSQ)(\d+)', name)
            if not match:
                raise ValueError('Unexpected target dataset name: ' + name)
            tool, dataset, rep = TOOLS[match[1]], DATASETS[match[2]], int(match[3])
            unit = 'assignment_records' if dataset == 'RAGE-seq' else 'strict_single_output_original_reads'
            for ordinal, row in enumerate(cells, 1):
                if column < len(row) and row[column].strip():
                    targets.append(dict(dataset=dataset, tool=tool, replicate=rep,
                        prism_row=ordinal, assigned_reads=integer(row[column]), count_unit=unit))
    checks = []
    for row in totals:
        matching = [r for r in targets if all(r[k] == row[k] for k in ['dataset', 'tool', 'replicate'])]
        if matching:
            observed_sum = sum(r['assigned_reads'] for r in matching)
            checks.append(dict(dataset=row['dataset'], tool=row['tool'], replicate=row['replicate'],
                target_observations=len(matching), target_count_sum=observed_sum,
                plotted_total=row['assigned_reads'], sums_match=observed_sum == row['assigned_reads']))
    provenance['target_sum_checks'] = checks
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(args.output_dir / 'plotted_offlist_totals.tsv',
        ['dataset', 'tool', 'replicate', 'assigned_reads', 'input_reads', 'count_unit'], totals)
    write_tsv(args.output_dir / 'plotted_offlist_per_target.tsv.gz',
        ['dataset', 'tool', 'replicate', 'prism_row', 'assigned_reads', 'count_unit'], targets, compressed=True)
    (args.output_dir / 'plotted_offlist_provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps(dict(totals=len(totals), target_observations=len(targets), checks=checks), indent=2))


if __name__ == '__main__':
    main()
