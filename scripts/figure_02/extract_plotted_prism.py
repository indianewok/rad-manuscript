#!/usr/bin/env python3
"""Extract the series actually selected in the manuscript Figure 2 layout."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import zipfile
from pathlib import Path

LAYOUT = '30A33090-FD85-4730-B1A1-CDE05A559C52'
TARGETS = {
 'E': ('63D81234-28AC-46E8-8332-CB1AE2FC1AFF', {
   '55733904-0FA1-4462-9987-5CDECF83A340': ('BLAZE','detected_list'),
   'B7A95E01-DCE4-4964-ADD1-71CF919FE6DE': ('RAD','truth5000_global_and_custom'),
   '7A817AB2-8B3F-4B5F-85FB-0984A7A35D99': ('Flexiplex','supplied_truth5000')}),
 'G': ('66EF3D96-C86B-4FA9-ACE5-53621808DA50', {
   '25C79583-B71F-4587-A42E-2C295A006D14': ('BLAZE','detected_list'),
   'FF40BBC9-474C-49EC-85C5-707493619F18': ('RAD','truth5000_global_and_custom'),
   '33CFF86A-A5F5-4454-B030-E0492F0A9B49': ('Flexiplex','supplied_truth5000')}),
 'H': ('98505F94-3866-4F00-A8CD-E076CF542357', {
   '9EAF2EAD-1268-45DD-A97B-95FB03243A40': ('BLAZE','detected_list_truth_targets'),
   'BA645DAC-CA07-4E30-82F8-81C9505CB8BF': ('RAD','truth5000_global_and_custom'),
   '594B2375-BAC7-43FF-8B3D-89B48CF0526B': ('Flexiplex','detected_list')})}
PIES = {'RAD':'B3E0F44C-855D-4363-A355-2267133BA781',
        'BLAZE':'6A891CCF-953F-4BA6-B06C-DA6B6693C7FE',
        'Flexiplex':'28DC41C5-EC81-4A2B-87F9-2D94E2314B62'}


def write_tsv(path, fields, rows):
    text = io.StringIO(newline='')
    writer = csv.DictWriter(text, fieldnames=fields, delimiter='\t', lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    data = text.getvalue().encode('utf-8')
    if path.suffix == '.gz':
        with path.open('wb') as raw:
            with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as handle:
                handle.write(data)
    else:
        path.write_bytes(data)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prism',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();source=args.prism.read_bytes()
    provenance=dict(source_sha256=hashlib.sha256(source).hexdigest(),layout_id=LAYOUT,series=[])
    targets=[];states=[];discovery=[]
    with zipfile.ZipFile(io.BytesIO(source)) as archive:
        layout=json.loads(archive.read('layouts/'+LAYOUT+'/sheet.json'))
        graphs=[json.loads(archive.read('graphs/'+uid+'/sheet.json')) for uid in layout['linkedGraphSheets']]

        def table(sheet_id):
            sheet=json.loads(archive.read('data/sheets/'+sheet_id+'/sheet.json'))
            member='data/tables/'+sheet['table']['uid']+'/data.csv'
            content=archive.read(member)
            return sheet,list(csv.reader(io.StringIO(content.decode('utf-8-sig')))),member,hashlib.sha256(content).hexdigest()

        for panel,(sheet_id,selected) in TARGETS.items():
            sheet,rows,member,digest=table(sheet_id)
            graph=next(g for g in graphs if set(g.get('inputDataSets',[]))==set(selected))
            for dsid,(tool,condition) in selected.items():
                column=sheet['table']['dataSets'].index(dsid)+1
                values=[]
                for ordinal,row in enumerate(rows,1):
                    if column<len(row) and row[column].strip():
                        barcode=row[0];count=int(float(row[column]))
                        targets.append(dict(panel=panel,tool=tool,condition=condition,
                            barcode=barcode,reads=count,prism_row=ordinal,dataset_id=dsid))
                        values.append(count)
                provenance['series'].append(dict(panel=panel,tool=tool,condition=condition,
                    graph_id=graph['uid'],sheet_id=sheet_id,dataset_id=dsid,
                    csv_member=member,csv_sha256=digest,target_observations=len(values),reads_sum=sum(values)))
        for tool,sheet_id in PIES.items():
            sheet,rows,member,digest=table(sheet_id)
            for row in rows:
                if len(row)>1 and row[1].strip():
                    state=row[0].strip().lower().replace(' ','_')
                    states.append(dict(tool=tool,state=state,reads=int(float(row[1])),
                        denominator=4993805,fraction=int(float(row[1]))/4993805,
                        count_unit='unique physical read'))
            provenance['series'].append(dict(panel='F_source_partition',tool=tool,
                sheet_id=sheet_id,csv_member=member,csv_sha256=digest))
        _,rows,member,digest=table('9FA3BE17-60E1-4F42-8084-62CD9B3AE250')
        for row in rows:
            if row and row[0].strip():
                tool=row[0];tp,fp,fn=map(lambda x:int(float(x)),row[1:4])
                discovery.append(dict(tool=tool,tp=tp,fp=fp,fn=fn,precision=tp/(tp+fp),
                    recall=tp/(tp+fn),f1=2*tp/(2*tp+fp+fn),condition='Nanopore2023_native'))
        provenance['discovery_csv']=dict(member=member,sha256=digest)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    write_tsv(args.output_dir/'panel_per_target.tsv.gz',
        ['panel','tool','condition','barcode','reads','prism_row','dataset_id'],targets)
    write_tsv(args.output_dir/'assignment_states.tsv',
        ['tool','state','reads','denominator','fraction','count_unit'],states)
    write_tsv(args.output_dir/'discovery_condition_plotted.tsv',
        ['tool','tp','fp','fn','precision','recall','f1','condition'],discovery)
    (args.output_dir/'panel_bindings.json').write_text(json.dumps(provenance,indent=2)+'\n')
    for tool in PIES:
        if sum(r['reads'] for r in states if r['tool']==tool)!=4993805:
            raise ValueError('Input partition failed for '+tool)
    print(json.dumps(dict(target_rows=len(targets),state_rows=len(states),discovery_rows=len(discovery),series=provenance['series']),indent=2))


if __name__=='__main__':
    main()
