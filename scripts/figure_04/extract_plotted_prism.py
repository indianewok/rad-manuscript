#!/usr/bin/env python3
"""Extract Figure 4's exact 37-input Prism metrics and paired statistics.

Producer barcode counts remain in barcode_detection_metrics.tsv. This script
extracts the metrics selected for the saved manuscript layout, including its
best-F1 selection from the recorded Flexiplex f0/f8 comparison. It does not
infer new barcode counts from rounded plotted metrics.
"""
import argparse
import csv
from decimal import Decimal
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import zipfile

LAYOUT='A832BFDA-4E92-4AB6-BA27-1DC54997A075'
GRAPHS={'f1':'467B647E-9581-43A1-8D34-EC648F3C844A',
        'precision':'5977DCE9-EF13-4207-873F-147504A3586E',
        'recall':'11E96F24-6450-442A-8E09-25EE32C26895'}
VARIANTS_TABLE='36865BC4-70F6-5C9D-8F89-D86B82E7F4D0'
TOOLS=('RAD','BLAZE','Flexiplex')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_table(path, fields, rows):
    with path.open('w',newline='') as h:
        w=csv.DictWriter(h,fieldnames=fields,delimiter='\t',lineterminator='\n')
        w.writeheader();w.writerows(rows)


def close(a,b):
    return abs(float(a)-float(b)) <= 1e-9


def median(values):
    ordered=sorted(values);n=len(ordered)
    return ordered[n//2] if n%2 else (ordered[n//2-1]+ordered[n//2])/2


def validate_checkpoint(folder):
    provenance=json.loads((folder/'panel_bindings.json').read_text())
    for name,expected in provenance['outputs'].items():
        assert sha((folder/name).read_bytes())==expected,('output hash',name)
    with (folder/'plotted_metrics.tsv').open(newline='') as h:
        rows=list(csv.DictReader(h,delimiter='\t'))
    assert len(rows)==111
    keys={(x['canonical_id'],x['tool']) for x in rows}
    ids={x['canonical_id'] for x in rows}
    assert len(ids)==37 and keys=={(d,t) for d in ids for t in TOOLS}
    by_key={(x['canonical_id'],x['tool']):x for x in rows}
    for x in rows:
        p,r,f=(float(x[m]) for m in ('precision','recall','f1'))
        assert all(0<=v<=1 for v in (p,r,f))
        assert abs(f-(2*p*r/(p+r) if p+r else 0))<=2e-9
    for metric in GRAPHS:
        with (folder/('paired_'+metric+'.tsv')).open(newline='') as h:
            paired=list(csv.DictReader(h,delimiter='\t'))
        assert len(paired)==37 and {x['paired_input_id'] for x in paired}==ids
        for x in paired:
            for tool in TOOLS:
                assert x[tool]==by_key[x['paired_input_id'],tool][metric]
    with (folder/'flexiplex_selected_conditions.tsv').open(newline='') as h:
        choices=list(csv.DictReader(h,delimiter='\t'))
    assert len(choices)==37
    for x in choices:
        options={f:x['f'+f+'_f1'] for f in ('0','8') if x['f'+f+'_f1']}
        assert close(x['plotted_f1'],max(map(float,options.values())))
        assert close(x['plotted_f1'],options[x['selected_flank_distance']])
        assert close(x['plotted_f1'],by_key[x['canonical_id'],'Flexiplex']['f1'])
    return {'status':'passed','matched_inputs':37,'tool_observations':111,
            'metric_values':333,'output_hashes':len(provenance['outputs'])}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prism',type=Path)
    parser.add_argument('--producer-metrics',type=Path)
    parser.add_argument('--statistics-script',type=Path,default=Path(__file__).with_name('statistics.py'))
    parser.add_argument('--output-dir',required=True,type=Path)
    parser.add_argument('--validate-only',action='store_true')
    args=parser.parse_args()
    if args.validate_only:
        print(json.dumps(validate_checkpoint(args.output_dir),indent=2));return
    if args.prism is None or args.producer_metrics is None:
        parser.error('--prism and --producer-metrics are required for extraction')
    args.output_dir.mkdir(parents=True,exist_ok=True)
    native=args.prism.read_bytes();producer_bytes=args.producer_metrics.read_bytes()
    producers=list(csv.DictReader(io.StringIO(producer_bytes.decode('utf-8-sig')),delimiter='\t'))
    producer={(x['canonical_id'],x['tool']):x for x in producers}
    aliases={}
    for x in producers:
        for key in ('canonical_id','display_dataset','paired_input_id'):
            if x.get(key):
                old=aliases.setdefault(x[key],x['canonical_id'])
                assert old==x['canonical_id'],('ambiguous alias',x[key])
    provenance={'source_prism_sha256':sha(native),'layout_uid':LAYOUT,
                'producer_metrics_sha256':sha(producer_bytes),'tables':[]}
    values={};paired={};variants=[];differences=[]
    with zipfile.ZipFile(io.BytesIO(native)) as z:
        layout=json.loads(z.read('layouts/'+LAYOUT+'/sheet.json'))
        sheets=[json.loads(z.read(n)) for n in z.namelist()
                if n.startswith('data/sheets/') and n.endswith('sheet.json')]
        for metric,gid in GRAPHS.items():
            assert gid in layout['linkedGraphSheets']
            graph=json.loads(z.read('graphs/'+gid+'/sheet.json'))
            ids=set(graph['inputDataSets'])
            matched=[x for x in sheets if set(x.get('table',{}).get('dataSets',[]))==ids]
            assert len(matched)==1,(metric,len(matched))
            sheet=matched[0];table=sheet['table'];member='data/tables/'+table['uid']+'/data.csv'
            data=z.read(member);rows=list(csv.reader(io.StringIO(data.decode('utf-8-sig'))))
            tools=[json.loads(z.read('data/sets/'+uid+'.json'))['title'] for uid in table['dataSets']]
            assert tuple(tools)==TOOLS and len(rows)==37
            paired[metric]=[]
            for order,row in enumerate(rows,1):
                label=row[0];canonical=aliases[label]
                paired_row={'paired_input_id':canonical,'display_dataset':label}
                for tool,text in zip(tools,row[1:]):
                    value=Decimal(text);assert 0<=value<=1
                    values.setdefault((canonical,tool),{'canonical_id':canonical,'display_dataset':label,'tool':tool,'input_order':order})[metric]=text
                    paired_row[tool]=text
                    old=producer[(canonical,tool)][metric]
                    if not close(text,old):
                        differences.append({'canonical_id':canonical,'display_dataset':label,
                          'tool':tool,'metric':metric,'plotted_value':text,'producer_value':old})
                paired[metric].append(paired_row)
            (args.output_dir/(metric+'_native.csv')).write_bytes(data)
            provenance['tables'].append({'metric':metric,'graph_uid':gid,'graph_title':graph['title'],
              'sheet_uid':sheet['uid'],'table_uid':table['uid'],'csv_member':member,
              'csv_sha256':sha(data),'dataset_uids':table['dataSets'],'rows':len(rows)})
        # The modality panels use transposed copies of the same 37 inputs.
        provenance['modality_tables']=[]
        example_graphs={'f1':'964784E4-4787-4A44-BBAA-D14A068F6540',
                        'precision':'8BE8B167-74A0-4B7E-A36C-E1356C7F3800',
                        'recall':'5A9EC4D9-CD8E-4C64-AF60-26C461EC9223'}
        for metric,example_gid in example_graphs.items():
            example=json.loads(z.read('graphs/'+example_gid+'/sheet.json'))
            choices=[s for s in sheets if set(example['inputDataSets']).issubset(set(s.get('table',{}).get('dataSets',[])))]
            assert len(choices)==1
            sheet=choices[0];table=sheet['table'];ids=table['dataSets']
            assert len(ids)==37
            member='data/tables/'+table['uid']+'/data.csv';data=z.read(member)
            rows=list(csv.reader(io.StringIO(data.decode('utf-8-sig'))))
            seen=set()
            for row in rows:
                if not row or row[0] not in TOOLS:continue
                tool=row[0];assert tool not in seen;seen.add(tool)
                for index,value in enumerate(row[1:]):
                    canonical=paired[metric][index]['paired_input_id']
                    assert close(value,values[(canonical,tool)][metric]),(metric,'modality copy',canonical,tool)
            assert seen==set(TOOLS)
            name=metric+'_modality_native.csv';(args.output_dir/name).write_bytes(data)
            graphs=[];covered=set()
            for gid in layout['linkedGraphSheets']:
                graph=json.loads(z.read('graphs/'+gid+'/sheet.json'))
                selected=set(graph.get('inputDataSets',[]))
                if selected and selected.issubset(set(ids)):
                    graphs.append({'graph_uid':gid,'title':graph['title'],'dataset_uids':graph['inputDataSets']})
                    covered|=selected
            assert covered==set(ids) and len(graphs)==5
            columns=[]
            for index,uid in enumerate(ids):
                title=json.loads(z.read('data/sets/'+uid+'.json'))['title']
                if isinstance(title,dict):title=title['string']
                columns.append({'dataset_uid':uid,'modality':title,
                    'canonical_id':paired[metric][index]['paired_input_id'],
                    'display_dataset':paired[metric][index]['display_dataset']})
            provenance['modality_tables'].append({'metric':metric,'sheet_uid':sheet['uid'],
                'table_uid':table['uid'],'csv_member':member,'csv_sha256':sha(data),
                'archived_csv':name,'columns':columns,'graphs':graphs,
                'observations_verified_against_paired_table':111})
        member='data/tables/'+VARIANTS_TABLE+'/data.csv';variant_data=z.read(member)
        for row in csv.reader(io.StringIO(variant_data.decode('utf-8-sig'))):
            label=row[0];canonical=aliases[label];plotted=values[(canonical,'Flexiplex')]['f1']
            scores={str(f):v for f,v in zip((0,8),row[3:]) if v}
            matched=[f for f,v in scores.items() if close(v,plotted)]
            assert len(matched)==1 and close(max(map(float,scores.values())),plotted),(label,scores,plotted)
            chosen=matched[0]
            values[(canonical,'Flexiplex')]['selected_flank_distance']=chosen
            variants.append({'canonical_id':canonical,'display_dataset':label,
              'f0_f1':scores.get('0',''),'f8_f1':scores.get('8',''),
              'selected_flank_distance':chosen,'plotted_f1':plotted})
        (args.output_dir/'flexiplex_variants_native.csv').write_bytes(variant_data)
        provenance['flexiplex_variants']={'table_uid':VARIANTS_TABLE,'csv_member':member,
             'csv_sha256':sha(variant_data),'selection':'Choose the higher recorded F1; retain its precision and recall.'}
        # Retain the saved Prism statistical-result tables as native checkpoints.
        result_tables=[]
        for sheet in sheets:
            title=sheet.get('title','')
            if 'Friedman test of' in title and any(s in title for s in ('ANOVA results','Multiple comparisons','Descriptive statistics')):
                member='data/tables/'+sheet['table']['uid']+'/data.csv';data=z.read(member)
                name='prism_statistics_'+sheet['table']['uid']+'.csv'
                (args.output_dir/name).write_bytes(data)
                result_tables.append({'title':title,'file':name,'sheet_uid':sheet['uid'],
                                     'table_uid':sheet['table']['uid'],'csv_sha256':sha(data)})
        provenance['saved_prism_statistics']=result_tables
    ordered=sorted(values.values(),key=lambda x:(x['input_order'],TOOLS.index(x['tool'])))
    assert len(ordered)==111 and len({x['canonical_id'] for x in ordered})==37
    for x in ordered:
        p=float(x['precision']);r=float(x['recall']);f=float(x['f1'])
        expected=2*p*r/(p+r) if p+r else 0
        assert abs(f-expected)<=2e-9,('F1 arithmetic',x)
        x.setdefault('selected_flank_distance','')
        x['reference_type']=producer[(x['canonical_id'],x['tool'])]['reference_type']
    write_table(args.output_dir/'plotted_metrics.tsv',
       ['input_order','canonical_id','display_dataset','tool','selected_flank_distance','reference_type','precision','recall','f1'],ordered)
    for metric,rows in paired.items():
        write_table(args.output_dir/('paired_'+metric+'.tsv'),['paired_input_id','display_dataset',*TOOLS],rows)
    write_table(args.output_dir/'flexiplex_selected_conditions.tsv',
       ['canonical_id','display_dataset','f0_f1','f8_f1','selected_flank_distance','plotted_f1'],variants)
    write_table(args.output_dir/'producer_comparison.tsv',
       ['canonical_id','display_dataset','tool','metric','plotted_value','producer_value'],differences)
    spec=importlib.util.spec_from_file_location('_rad_statistics',args.statistics_script)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    datasets=[x['paired_input_id'] for x in paired['f1']]
    by_key={(x['canonical_id'],x['tool']):{m:Decimal(x[m]) for m in GRAPHS} for x in ordered}
    friedman,dunn=module.calculate(datasets,by_key)
    write_table(args.output_dir/'friedman.tsv',list(friedman[0]),friedman)
    write_table(args.output_dir/'dunn.tsv',list(dunn[0]),dunn)
    native_statistics_checks=[]
    for metric in GRAPHS:
        label={'f1':'f1','precision':'precision','recall':'recall'}[metric]
        matches=[x for x in provenance['saved_prism_statistics']
                 if ('of '+label+' by dataset') in x['title'].lower()]
        for record in matches:
            data=list(csv.reader(io.StringIO((args.output_dir/record['file']).read_text())))
            if 'ANOVA results' in record['title']:
                observed=next(float(x[1]) for x in data if x and x[0].strip()=='Friedman statistic')
                expected=next(x['statistic'] for x in friedman if x['metric']==metric)
                assert abs(observed-expected)<=0.0051,(metric,'native Friedman',observed,expected)
                native_statistics_checks.append({'metric':metric,'check':'Friedman statistic','saved':observed,'recalculated':expected})
            if 'Multiple comparisons' in record['title']:
                detail=next(i for i,x in enumerate(data) if x and x[0]=='Test details')
                for row in data[detail+1:]:
                    if not row or not row[0].strip().startswith('RAD vs.'):continue
                    comparator=row[0].strip().split('RAD vs. ',1)[1]
                    calc=next(x for x in dunn if x['metric']==metric and x['comparator']==comparator)
                    assert abs(float(row[1])-calc['control_rank_sum'])<1e-9
                    assert abs(float(row[2])-calc['comparator_rank_sum'])<1e-9
                    assert abs(float(row[6])-calc['z'])<=0.00051
                    native_statistics_checks.append({'metric':metric,'check':'Dunn ranks and Z','comparator':comparator,'status':'matches saved Prism rounding'})
    summary={'inputs':37,'tool_observations':111,'metric_values':333,'modality_metric_values_verified':333,'modality_graphs_verified':15,
             'maximum_P_R_F1_rounding_error':2e-9,
             'selected_flexiplex_flanks':{f:sum(x['selected_flank_distance']==f for x in variants) for f in ('0','8')},
             'medians':{m:{t:median(float(x[m]) for x in ordered if x['tool']==t) for t in TOOLS} for m in GRAPHS},
             'producer_metric_differences':len(differences),'native_statistics_checks':native_statistics_checks,
             'statistics':{'matched_inputs':37,'test':'Friedman with two Dunn comparisons per metric against RAD',
                           'adjustment':'min(1,2*P_raw)','alpha':0.05,
                           'implementation_sha256':sha(args.statistics_script.read_bytes())}}
    wins={t:0 for t in TOOLS}
    for dataset in datasets:
        fs={t:float(by_key[(dataset,t)]['f1']) for t in TOOLS};best=max(fs.values())
        for t,v in fs.items():wins[t]+=v==best
    summary['highest_F1_counts']=wins
    (args.output_dir/'checkpoint_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    provenance['outputs']={p.name:sha(p.read_bytes()) for p in sorted(args.output_dir.iterdir()) if p.is_file() and p.name!='panel_bindings.json'}
    (args.output_dir/'panel_bindings.json').write_text(json.dumps(provenance,indent=2)+'\n')
    validate_checkpoint(args.output_dir)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
