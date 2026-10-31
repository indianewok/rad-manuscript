#!/usr/bin/env python3
"""Preserve the exact native Prism tables used in Figure 7B-D.

CSV files are copied without numeric conversion. Dataset bounds, exclusions,
graph bindings and the saved regression parameters/results accompany them.
The layout's Venn artwork has a separately transcribed region-count table;
no gene IDs are inferred from that image.
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
import re
from pathlib import Path
import zipfile

LAYOUT = 'C3B5C198-E4BA-4C34-9580-B55EA23BE9C3'
SOURCES = [
 ('panel_B_RAD','47E987CA-3F8E-471A-AC95-9D87BAA35A0A','B6477F54-FD88-4B35-B4A3-6CF772448B29'),
 ('panel_B_Flexiplex','468DB8AA-7B62-4DDC-8A6D-F673B2FC1F9A','71BF5FE5-AB99-4585-A45A-4AAA6DF6A2CA'),
 ('panel_B_BLAZE','D85F9BC6-EB04-4C69-B70B-5269D382A31A','34ABB35B-AA49-41E6-89FF-6EBC4FA87D2D'),
 ('panel_C_H146_high','97C1162B-73F7-4BB2-AF2A-F872C4F43B57','A88C95DF-CE6C-4C79-B0F8-9170C95315E7'),
 ('panel_C_H526_high','4165C95D-F3D3-4958-8E3C-163EDB7F9054','C9EB40C2-68E8-48D6-886F-EB26AA6FF5AF'),
 ('panel_D_RAD_H146_high','58A38F11-631D-432F-8B24-79E308A0F714','12011C8C-565B-4114-87E8-101CF5F7C64B'),
 ('panel_D_Flexiplex_H146_high','9B191ADC-4CE2-4D3A-9632-C0C9CE933267','6D6F803F-C56F-4871-9A6C-92FC035C248A'),
 ('panel_D_BLAZE_H146_high','8C740359-D2CE-49F6-A9C2-A495CE34B5DF','5665A9B6-0090-44A3-8FEC-4241BCE65F89'),
 ('panel_D_RAD_H526_high','F3C2D864-DFC0-4DEA-9F52-6190712A9E5E','302ED075-D851-49EE-AB9E-C2D3632115F8'),
 ('panel_D_Flexiplex_H526_high','BD4FB324-5DDC-43A2-8E39-626CA2212D87','A47098EC-83DB-4141-ABA3-B4BE57A36D65'),
 ('panel_D_BLAZE_H526_high','FFD84336-E158-43E2-BB5D-2A60E372DA84','807BA25A-B693-4A59-A62D-CC22CCD2A6A3'),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def title(dataset):
    value = dataset.get('title', '')
    return value.get('string', '') if isinstance(value, dict) else value


def excluded(replica, row):
    for item in replica.get('cellAttributes', []):
        if 'EXCLUDED' not in item.get('attributes', []):
            continue
        for block in item['rows'].split(','):
            bounds = [int(x) for x in block.split('~')]
            if bounds[0] <= row <= bounds[-1]:
                return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prism', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, default=Path('source_data/figure_07/plotted'))
    parser.add_argument('--threshold-grid', type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = dict(source_prism_sha256=sha(args.prism.read_bytes()), layout_uid=LAYOUT, tables=[], regressions=[])
    points = []
    with zipfile.ZipFile(args.prism) as archive:
        document = json.loads(archive.read('document.json'))
        layout = json.loads(archive.read('layouts/' + LAYOUT + '/sheet.json'))
        linked = set(layout['linkedGraphSheets'])
        for stem, graph_id, sheet_id in SOURCES:
            if graph_id not in linked:
                raise ValueError('Graph not linked to Figure 7 layout: ' + stem)
            graph = json.loads(archive.read('graphs/' + graph_id + '/sheet.json'))
            sheet = json.loads(archive.read('data/sheets/' + sheet_id + '/sheet.json'))
            table = sheet['table']
            raw = archive.read('data/tables/' + table['uid'] + '/data.csv')
            path = args.output_dir / (stem + '.csv.gz')
            path.write_bytes(gzip.compress(raw, mtime=0))
            ids = ([table['rowTitlesDataSet']] if table.get('rowTitlesDataSet') else [])
            ids += ([table['xDataSet']] if table.get('xDataSet') else [])
            ids += table['dataSets']
            datasets = {uid: json.loads(archive.read('data/sets/' + uid + '.json')) for uid in ids}
            rows = list(csv.reader(io.StringIO(raw.decode())))
            report['tables'].append(dict(name=stem, file=path.name, graph_uid=graph_id, graph_title=graph['title'],
                graph_specification=graph, input_graph_datasets=graph.get('inputDataSets', []), data_sheet_uid=sheet_id, data_sheet_title=sheet['title'],
                table=table, datasets=datasets, csv_rows=len(rows), csv_sha256=sha(raw), gzip_sha256=sha(path.read_bytes())))
            # Preserve the actual plotted XY points, honoring each Y dataset's row bounds.
            if stem.startswith(('panel_B_', 'panel_C_')):
                if table['format'] != 'xy' or table['dataFormat'] != 'y_single':
                    raise ValueError('Unexpected XY format: ' + stem)
                offset = int(bool(table.get('rowTitlesDataSet')))
                for col, uid in enumerate(table['dataSets'], offset + 1):
                    dataset = datasets[uid]
                    if len(dataset['replicates']) != 1:
                        raise ValueError('Expected a single Y value: ' + stem)
                    rep = dataset['replicates'][0]
                    for index, row in enumerate(rows):
                        if not rep.get('firstRow', 0) <= index <= rep.get('lastRow', -1) or excluded(rep, index):
                            continue
                        if len(row) <= col or row[offset] == '' or row[col] == '':
                            continue
                        points.append(dict(panel=stem, series=title(dataset), source_row_1based=index+1,
                            label=row[0] if offset else '', x=row[offset], y=row[col]))
        for uid in document['sheets']['analyses']:
            sheet = json.loads(archive.read('analyses/' + uid + '/sheet.json'))
            matches = [stem for stem, _, sid in SOURCES if stem.startswith('panel_C_') and sid in {s['uid'] for s in sheet.get('inputSheets', [])}]
            if not matches or sheet.get('analysisClass') != 'SIMPLE_LINEAR_REGRESSION':
                continue
            files = {}
            for member in ['sheet.json', 'parameters.json', 'results.json']:
                data = archive.read('analyses/' + uid + '/' + member)
                name = matches[0] + '_regression_' + member
                (args.output_dir / name).write_bytes(data)
                files[name] = sha(data)
            report['regressions'].append(dict(panel=matches[0], analysis_uid=uid, files=files))
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, delimiter='\t', fieldnames=['panel','series','source_row_1based','label','x','y'], lineterminator='\n')
    writer.writeheader(); writer.writerows(points)
    (args.output_dir / 'panel_B_C_points.tsv.gz').write_bytes(gzip.compress(buffer.getvalue().encode(),mtime=0))
    report['xy_points'] = len(points)
    if args.threshold_grid:
        with args.threshold_grid.open() as source:
            expected = {(row['tool'],row['direction'],float(row['tool_BH_FDR_cutoff']),float(row['tool_abs_log2FC_cutoff'])):float(row['F1'])
                        for row in csv.DictReader(source,delimiter='\t')}
        checked = 0
        max_error = 0.0
        for table in report['tables']:
            if not table['name'].startswith('panel_D_'):
                continue
            parts = table['name'].split('_')
            tool, direction = parts[2], '_'.join(parts[3:])
            columns = [float(title(table['datasets'][uid])) for uid in table['table']['dataSets']]
            raw = gzip.decompress((args.output_dir/table['file']).read_bytes()).decode()
            for row in csv.reader(io.StringIO(raw)):
                if not row or not row[0]:
                    continue
                label = re.sub(r'^FDR\s*(?:<=|<|≤)?\s*', '', row[0], flags=re.I)
                match = re.fullmatch(r'\s*([0-9.]+)\s*x\s*10\s*(-?[0-9]+)\s*',label)
                cutoff = float(match[1])*10**int(match[2]) if match else float(label)
                for col,fold_change in enumerate(columns,1):
                    value = expected[tool,direction,cutoff,fold_change]
                    max_error = max(max_error,abs(float(row[col])-value))
                    checked += 1
        if checked != 594 or max_error > 1e-12:
            raise ValueError('Native threshold grid differs from the common-gene F1 table')
        report['common_gene_threshold_comparison'] = dict(status='PASS',cells=checked,max_absolute_error=max_error)
    (args.output_dir / 'prism_table_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(tables=len(report['tables']), regression_analyses=len(report['regressions']), xy_points=len(points)),indent=2))


if __name__ == '__main__':
    main()
