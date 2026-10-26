#!/usr/bin/env python3
"""Read only: compare corrected Prism CSV values to canonical keyed tables."""
import argparse
import csv
import io
import json
import sys
import zipfile
from pathlib import Path
from figures_124 import REPO, STATES, rows, sha, write_json


def title(value):
    return value['string'] if isinstance(value,dict) else value


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prism',type=Path,default=Path('/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/paper_revision_20261022/prism/Figure2_corrected_20261022.prism'))
    p.add_argument('--output-root',type=Path,default=REPO)
    a=p.parse_args();out=a.output_root
    prism=a.prism
    expected={(r['tool'],r['barcode']):r for r in rows(out/'source_data/figure_02/assignment_per_target.tsv')}
    want={'Native correct assignments per selected truth barcode':'native_correct',
          'Corrected correct assignments per selected truth barcode':'corrected_correct',
          'Corrected incorrect assignments per selected truth target barcode':'corrected_incorrect'}
    checks=[];compared=0;found=set()
    with zipfile.ZipFile(prism) as z:
        for name in z.namelist():
            if not name.startswith('data/sheets/') or not name.endswith('/sheet.json'):continue
            sheet=json.loads(z.read(name));name=title(sheet['title'])
            if name not in want:continue
            found.add(name);table=sheet['table'];field=want[name]
            bindings=[title(json.loads(z.read('data/sets/'+u+'.json'))['title']) for u in table['dataSets']]
            if bindings[0]!='BLAZE' or bindings[1]!='RAD' or not bindings[2].startswith('Flexiplex'):
                raise ValueError(('unexpected current column binding',name,bindings))
            values=list(csv.reader(io.StringIO(z.read('data/tables/'+table['uid']+'/data.csv').decode())))
            if len(values)!=5000 or len({r[0] for r in values})!=5000:raise ValueError('Prism truth-key universe mismatch')
            for r in values:
                bc=r[0]
                for column,tool in ((1,'BLAZE'),(2,'RAD'),(3,'Flexiplex')):
                    wanted=expected[(tool,bc)][field]
                    actual=r[column]
                    if wanted=='' and actual!='':raise ValueError(('Prism missing target replaced with value',name,tool,bc))
                    if wanted!='' and (actual=='' or float(actual)!=int(wanted)):raise ValueError(('Prism numeric mismatch',name,tool,bc,actual,wanted))
                    compared+=1
            checks.append(dict(sheet=name,table_uid=table['uid'],rows=5000,selected_tool_columns=bindings[:3],
                               compared_values=15000,status='passed',missing_policy='unselected truth targets stay blank'))
    if found!=set(want):raise ValueError('missing required Prism table')
    write_json(out/'validation/figures_124_prism_values.json',dict(status='passed',command=[sys.executable,*sys.argv],
               prism_path=str(prism),prism_sha256=sha(prism),script_sha256=sha(Path(__file__)),checks=checks,compared_values=compared,
               limitation='CSV data and JSON bindings only. Separate structural duplicate-layout-ID finding and native Prism recalculation remain unresolved.'))
    print(f'Prism selected-truth values and blank cells: {compared} comparisons passed')


if __name__=='__main__':main()
