#!/usr/bin/env python3
"""Count the reference-present named genotypes used in Figure 6C.

The plotted checkpoint retains the published BLAZE ONT-SN genotype stream.
The separately supplied panel-matched BLAZE calls define other source tables.
Do not substitute one annotation stream for the other during replay.
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
import zipfile

TOOLS = ['RAD', 'BLAZE', 'Flexiplex']
DONORS = ['H146', 'H1975', 'H211', 'H2228', 'H526', 'H69', 'HCC827', 'SHP77']
GRAPH_UID = 'A802F129-B689-40F8-B170-DDBCDC54A6DE'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_calls(path):
    opener = gzip.open if path.suffix == '.gz' else open
    counts = Counter()
    with opener(path, 'rt') as source:
        reader = csv.DictReader(source, delimiter='\t')
        rows = list(reader)
    if 'illumina_state' in reader.fieldnames:
        reference_rows = 0
        for row in rows:
            if row['illumina_state'] not in ['singlet', 'doublet', 'unassigned']:
                continue
            reference_rows += 1
            for tool in TOOLS:
                if row[tool + '_selected'] == '1' and row[tool + '_state'] == 'singlet':
                    donor = row[tool + '_label']
                    if donor not in DONORS:
                        raise ValueError('Unknown named cell line: ' + donor)
                    counts[tool, donor] += 1
        return counts, dict(input_rows=len(rows), reference_barcodes=reference_rows,
                            input_format='wide producing genotype checkpoint')
    for row in rows:
        if row.get('reference_present', '1') == '1' and row['selected'] == '1' and row['query_state'] == 'named_singlet':
            counts[row['tool'], row['query_label']] += 1
    return counts, dict(input_rows=len(rows), input_format='long reference-matched genotype calls')


def prism_counts(path):
    with zipfile.ZipFile(path) as archive:
        graph = json.loads(archive.read('graphs/' + GRAPH_UID + '/sheet.json'))
        wanted = set(graph['inputDataSets'])
        document = json.loads(archive.read('document.json'))
        candidates = []
        for uid in document['sheets']['data']:
            sheet = json.loads(archive.read('data/sheets/' + uid + '/sheet.json'))
            if wanted.issubset(set(sheet['table']['dataSets'])):
                candidates.append(sheet)
        if len(candidates) != 1:
            raise ValueError('Expected one table for the Figure 6C graph')
        sheet = candidates[0]
        table = sheet['table']
        if table['dataFormat'] != 'y_single' or 'rowTitlesDataSet' not in table:
            raise ValueError('Unexpected Figure 6C table format')
        columns = {}
        for index, uid in enumerate(table['dataSets'], 1):
            if uid in wanted:
                dataset = json.loads(archive.read('data/sets/' + uid + '.json'))
                title = dataset['title']
                columns[index] = title['string'] if isinstance(title, dict) else title
        content = archive.read('data/tables/' + table['uid'] + '/data.csv').decode()
        counts = Counter()
        for row in csv.reader(io.StringIO(content)):
            if row and row[0] in DONORS:
                for index, tool in columns.items():
                    counts[tool, row[0]] = int(row[index])
        return counts, dict(graph_uid=GRAPH_UID, data_sheet_uid=sheet['uid'],
                            data_table_uid=table['uid'], csv_sha256=hashlib.sha256(content.encode()).hexdigest())


def differences(left, right):
    return [dict(tool=tool, donor=donor, plotted=left[tool, donor], comparison=right[tool, donor],
                 difference=left[tool, donor] - right[tool, donor])
            for tool in TOOLS for donor in DONORS if left[tool, donor] != right[tool, donor]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--calls', type=Path, default=Path('source_data/figure_06/plotted_genotype_calls.tsv.gz'))
    parser.add_argument('--expected', type=Path, default=Path('source_data/figure_06/plotted_panel_c_counts.tsv'))
    parser.add_argument('--output', type=Path, default=Path('results/figure06_panel_c_counts.tsv'))
    parser.add_argument('--report', type=Path, default=Path('results/figure06_panel_c_replay.json'))
    parser.add_argument('--prism', type=Path)
    parser.add_argument('--comparison-calls', type=Path)
    args = parser.parse_args()
    counts, summary = count_calls(args.calls)
    if sum(counts.values()) <= 0 or len(counts) != 24:
        raise ValueError('Expected 24 nonempty tool-by-cell-line counts')
    with args.expected.open() as source:
        expected = Counter({(row['tool'], row['donor']): int(row['nuclei'])
                            for row in csv.DictReader(source, delimiter='\t')})
    if differences(expected, counts):
        raise ValueError('Producing genotype checkpoint differs from the plotted count table')
    report = dict(status='PASS', counts_verified=24, source_sha256=digest(args.calls),
                  totals={tool: sum(counts[tool, donor] for donor in DONORS) for tool in TOOLS}, **summary)
    if args.prism:
        native, origin = prism_counts(args.prism)
        if differences(native, counts):
            raise ValueError('Producing genotype counts differ from the saved Prism graph')
        report['native_prism'] = dict(sha256=digest(args.prism), all_counts_match=True, **origin)
    if args.comparison_calls:
        other, _ = count_calls(args.comparison_calls)
        report['comparison_annotation_stream'] = dict(path=str(args.comparison_calls),
            sha256=digest(args.comparison_calls), differences=differences(counts, other))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', newline='') as target:
        writer = csv.DictWriter(target, delimiter='\t', fieldnames=['tool', 'donor', 'nuclei', 'count_unit'], lineterminator='\n')
        writer.writeheader()
        for tool in TOOLS:
            for donor in DONORS:
                writer.writerow(dict(tool=tool, donor=donor, nuclei=counts[tool, donor],
                    count_unit='selected named Vireo singlets among Illumina-reference barcodes; plotted genotype stream'))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
