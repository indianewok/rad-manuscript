#!/usr/bin/env python3
"""Compare the pinned current Figure 2 Prism tables with deposited keyed data."""
import argparse
import csv
import io
import json
import sys
import zipfile
from pathlib import Path
from figures_124 import REPO, rows, sha, write_json


def title(value):
    return value['string'] if isinstance(value, dict) else value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--identity', type=Path, default=REPO/'source_data/figure_02/producing_evidence/assignment_Prism_identity.json')
    parser.add_argument('--prism', type=Path, required=True, help='External author Prism project')
    parser.add_argument('--output-root', type=Path, default=REPO)
    args = parser.parse_args()
    identity = json.loads(args.identity.read_text())
    prism = args.prism
    if sha(prism) != identity['sha256']:
        raise ValueError('Prism SHA-256 differs from the deposited current identity')
    for name, expected_hash in identity['source_tables'].items():
        if sha(args.output_root/'source_data/figure_02'/name) != expected_hash:
            raise ValueError('Deposited source table differs from the Prism identity: '+name)
    expected = {(row['tool'], row['barcode']):row for row in rows(args.output_root/'source_data/figure_02/assignment_per_target.tsv')}
    bindings = identity['assignment_tables']
    if {row['assignment_field'] for row in bindings} != {'native_correct', 'corrected_correct', 'corrected_incorrect'} or len(bindings) != 3:
        raise ValueError('Expected the three pinned selected-truth assignment tables')
    checks = []
    compared = 0
    with zipfile.ZipFile(prism) as archive:
        for binding in bindings:
            sheet = json.loads(archive.read('data/sheets/'+binding['sheet_uid']+'/sheet.json'))
            table = sheet['table']
            if title(sheet['title']) != binding['title'] or table['uid'] != binding['table_uid']:
                raise ValueError('Pinned Prism sheet/table binding differs')
            columns = [title(json.loads(archive.read('data/sets/'+uid+'.json'))['title']) for uid in table['dataSets']]
            if columns != binding['data_set_titles'] or table['dataSets'] != binding['data_set_uids']:
                raise ValueError(('Pinned Prism column binding differs', columns))
            values = list(csv.reader(io.StringIO(archive.read('data/tables/'+table['uid']+'/data.csv').decode())))
            if len(values) != 5000 or len({row[0] for row in values}) != 5000:
                raise ValueError('Prism truth-key universe differs from the supplied 5,000 barcodes')
            for row in values:
                barcode = row[0]
                for column, tool in ((1, 'BLAZE'), (2, 'RAD'), (3, 'Flexiplex')):
                    wanted = expected[(tool, barcode)][binding['assignment_field']]
                    actual = row[column]
                    if wanted == '' and actual != '':
                        raise ValueError(('Unselected target replaced with a value', tool, barcode))
                    if wanted != '' and (actual == '' or float(actual) != int(wanted)):
                        raise ValueError(('Prism assignment differs', tool, barcode, actual, wanted))
                    compared += 1
            checks.append(dict(sheet=binding['title'], sheet_uid=binding['sheet_uid'], table_uid=table['uid'],
                               rows=5000, selected_tool_columns=columns[:3], compared_values=15000,
                               status='passed', missing_policy='unselected truth targets stay blank'))
    write_json(args.output_root/'validation/figures_124_prism_values.json', dict(
        status='passed', command=[sys.executable, *sys.argv], prism_sha256=sha(prism),
        identity_sha256=sha(args.identity), script_sha256=sha(Path(__file__)), checks=checks,
        compared_values=compared,
        native_Prism_analysis_state=identity.get('native_Prism_analysis_state'),
        native_Prism_export_verified=identity.get('native_Prism_export_verified', False),
        scope='Pinned CSV data and JSON bindings; calculation status is recorded in the project identity.'))
    print(f'Current Prism selected-truth values and blank cells: {compared} comparisons passed')


if __name__ == '__main__':
    main()
