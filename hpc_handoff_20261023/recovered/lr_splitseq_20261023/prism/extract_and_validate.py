#!/usr/bin/env python3
"""Recover saved LR-Split-seq values/metadata without inventing cell identities.

Usage: python3 extract_and_validate.py --source MASTER.prism --out DIRECTORY
Reads an existing native archive. Does not open or edit Prism.
"""
import argparse, csv, hashlib, io, json, math, statistics
from pathlib import Path
from zipfile import ZipFile

SID = '6D466B4F-8636-4547-8F4E-B45C30CA7F51'
CONT = '7F52648E-85D1-4920-A525-216AA6D45C42'
TEST = 'F616A250-536B-42B0-B4E6-23C2BF786E46'
EXPECTED_CSV_SHA256 = '386f9dc0e09128d6d5f86166196473ac2c124d10366b3393951133c5038b4492'

def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    copied = {}
    with ZipFile(args.source) as z:
        def readj(n): return json.loads(z.read(n))
        def keep(n):
            p = args.out/'native_components'/n
            p.parent.mkdir(parents=True, exist_ok=True)
            raw = z.read(n); p.write_bytes(raw)
            copied[n] = {'sha256': sha(raw), 'bytes': len(raw)}
        sheets = {s:readj(f'data/sheets/{s}/sheet.json') for s in [SID,CONT]}
        keep('document.json')
        table_rows, labels, all_sets = {}, {}, set()
        for sid, s in sheets.items():
            keep(f'data/sheets/{sid}/sheet.json')
            t = s['table']
            assert 'rowTitlesDataSet' not in t, 'Archive changed: inspect actual row titles.'
            sets = ([t['xDataSet']] if 'xDataSet' in t else [])+t['dataSets']
            all_sets.update(sets)
            labels[sid] = []
            for did in sets:
                n = f'data/sets/{did}.json';keep(n)
                labels[sid].append(readj(n)['title'])
            base = f"data/tables/{t['uid']}"
            for suffix in ['content.json','data.csv']:keep(f'{base}/{suffix}')
            raw = z.read(f'{base}/data.csv')
            table_rows[sid] = list(csv.reader(io.StringIO(raw.decode())))
            if sid == SID: assert sha(raw) == EXPECTED_CSV_SHA256
            assert len(table_rows[sid]) == 568
        a, b = table_rows[SID], table_rows[CONT]
        assert b == [r[1:] for r in a]
        assert all(r[0] == r[5] for r in a)
        assert labels[SID] == ['rad_ed2_assigned_reads','component-based Flexiplex, no poly-T','component-based Flexiplex, poly-T','GitHub FLAMESV2 (Newest)','Preprint FLAMESV2 (Canonical)','Identity Line']
        for sid, name in [(SID,'splitseq_all_methods_by_prism_row.csv'),(CONT,'splitseq_continued_by_prism_row.csv')]:
            with (args.out/name).open('w',newline='') as f:
                w=csv.writer(f);w.writerow(['prism_row_1based']+labels[sid]);w.writerows([[i]+r for i,r in enumerate(table_rows[sid],1)])
        with (args.out/'rad_vs_component_polyT_by_prism_row.csv').open('w',newline='') as f:
            w=csv.writer(f);w.writerow(['prism_row_1based','rad_ed2_assigned_reads','component_flexiplex_polyT_assigned_reads']);w.writerows([[i,r[0],r[2]] for i,r in enumerate(a,1)])
        # Preserve the exact saved analysis, parameters, results and result-view metadata.
        analysis_ids = []
        relevant_sets = set(all_sets)
        for n in z.namelist():
            if n.startswith('analyses/') and n.endswith('/sheet.json'):
                j=readj(n)
                if any(i.get('uid') in sheets for i in j.get('inputSheets',[])):
                    aid=j['uid'];analysis_ids.append(aid)
                    for m in z.namelist():
                        if m.startswith(f'analyses/{aid}/') and m.endswith('.json'):keep(m)
                    for view in j.get('resultSheets',[]):
                        v=readj(f"analyses/{aid}/result_sheets/{view['uid']}.json")
                        dsid=v.get('dataSheet')
                        if not dsid:continue
                        path=f'data/sheets/{dsid}/sheet.json';keep(path)
                        rs=readj(path);rt=rs['table']
                        rsets=([rt['xDataSet']] if 'xDataSet' in rt else [])+rt.get('dataSets',[])+([rt['rowTitlesDataSet']] if 'rowTitlesDataSet' in rt else [])
                        relevant_sets.update(rsets)
                        for did in rsets:keep(f'data/sets/{did}.json')
                        for ext in ['content.json','data.csv']:
                            m=f"data/tables/{rt['uid']}/{ext}"
                            if m in z.namelist():keep(m)
        graphs = []
        for n in z.namelist():
            if n.startswith('graphs/') and n.endswith('/sheet.json'):
                g=readj(n)
                if any(s in relevant_sets for s in g.get('inputDataSets',[])):
                    keep(n);graphs.append(g)
        p=readj(f'analyses/{TEST}/parameters.json')['content']
        res=readj(f'analyses/{TEST}/results.json')['content']
        test=res['pairedTTestModel']['pairedTTest']
        assert p['experimentalDesign']=='PAIRED_T_TEST'
        assert p['options']['pValueTailType']=='P_VALUE_TWO_TAILED'
        vals=[[int(v) for v in r] for r in a]
        stats=[{'column_1based':c+1,'label':labels[SID][c],'n':568,'sum':sum(r[c] for r in vals),'median':statistics.median(r[c] for r in vals)} for c in range(6)]
        assert stats[0]['sum']==2078171 and stats[2]['sum']==1156252
        assert stats[0]['median']==1979.5 and stats[2]['median']==1102.5
        diff=[r[0]-r[2] for r in vals]
        t=statistics.mean(diff)/(statistics.stdev(diff)/math.sqrt(len(diff)))
        assert math.isclose(t,test['t'],rel_tol=1e-12)
        report={
            'source_archive':str(args.source.resolve()),'source_archive_sha256':sha(args.source.read_bytes()),
            'document_modification_date':readj('document.json').get('modificationDate'),
            'primary_sheet_id':SID,'primary_table_id':sheets[SID]['table']['uid'],
            'continued_sheet_id':CONT,'primary_csv_sha256':EXPECTED_CSV_SHA256,
            'column_statistics':stats,
            'continued_is_exact_primary_columns_2_to_6':True,
            'continued_column_labels':labels[CONT],
            'cell_ids_present':False,'prism_row_is_cell_id':False,
            'cell_identity_mapping_status':'Not stored in the native archive; both source tables have no rowTitlesDataSet. A separate keyed-export comparison is required; see cell_mapping_validation.json.',
            'selected_comparison_primary_columns_1based':[1,3],
            'selected_comparison_continued_columns_1based':[5,2],
            'saved_test':{'analysis_id':TEST,'design':p['experimentalDesign'],'tail':p['options']['pValueTailType'],'t':test['t'],'df':test['df'],'p':test['pValue']['value'],'recalculated_t_from_table':t},
            'analysis_ids':analysis_ids,'graph_sheet_metadata':graphs,
            'validation':'passed: exact archived numeric CSV hash, source labels, 568 rows, two-table equivalence, totals, medians and recomputed paired t statistic',
            'limitations':['Final component tool code, run commands and read-level outputs are not contained in this recovery.','No cell ID is inferred from a Prism row number.','Graph sheet metadata verifies dataset references; figures were not rendered or opened in Prism.','Saved paired t result identifies the test executed; this does not choose the final statistical method for the authors.'],
            'native_component_manifest':copied}
        (args.out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['source_archive_sha256','cell_ids_present','saved_test','validation']}))
if __name__=='__main__':main()
