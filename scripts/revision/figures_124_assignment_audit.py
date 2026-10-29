#!/usr/bin/env python3
"""Independently resume Figure 2 counts from complete retained read-level tables."""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from source_paths import data_root
from figures_124 import NREADS, REPO, STATES, TOOLS, rows, sha, write_json, write_rows, assignment_state_counts

FIELDS=('native_correct','corrected_correct','native_incorrect','corrected_incorrect')


def count_records(records,tool,truth,selected):
    """Count assignments using each tool's physical-read duplicate rules."""
    seen={};per=defaultdict(Counter);counts=Counter();n=0
    for rid,target,source,corrected in records:
        n+=1
        if source not in truth or (target not in selected and tool!='RAD'):
            raise ValueError('truth/selected identity failure')
        state=('corrected' if corrected else 'native')+('_correct' if target==source else '_incorrect')
        if rid not in seen:
            seen[rid]=(target,state);counts[state]+=1;per[target][state]+=1
        elif seen[rid] is not None and (tool=='RAD' or seen[rid][0]!=target):
            old,oldstate=seen[rid];counts[oldstate]-=1;per[old][oldstate]-=1
            counts['excluded_multiple_outputs']+=1;seen[rid]=None
    counts['unassigned']=NREADS-len(seen)
    return counts,per,n,len(seen)


def fixtures():
    truth={'A','B'};selected={'A','B'}
    sample=[('same','A','A',False),('same','A','A',False),
            ('multi','A','A',False),('multi','B','A',True),('multi','A','A',False),
            ('one','B','A',True)]
    rad,_,_,_=count_records(iter(sample),'RAD',truth,selected)
    flex,_,_,_=count_records(iter(sample),'Flexiplex',truth,selected)
    if rad['excluded_multiple_outputs']!=2 or rad['corrected_incorrect']!=1 or rad['native_correct']!=0:
        raise ValueError('RAD duplicate fixture failed')
    if flex['excluded_multiple_outputs']!=1 or flex['corrected_incorrect']!=1 or flex['native_correct']!=1:
        raise ValueError('Flex same-target collapse fixture failed')
    for tool, raw, assigned in [('RAD',rad,1),('Flexiplex',flex,2)]:
        grouped=assignment_state_counts(raw)
        if set(grouped)!=set(STATES) or len(grouped)!=5 or sum(grouped.values())!=NREADS:
            raise ValueError(tool+' five-state conservation fixture failed')
        if grouped['unassigned']!=NREADS-assigned:
            raise ValueError(tool+' discarded reads were not included in unassigned')
    return {'five_state_unassigned_includes_discarded_outputs':'passed','RAD_identical_duplicate_excluded':'passed','Flex_same_target_duplicate_collapsed':'passed',
            'different_target_id_excluded_after_later_repeat':'passed'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root',type=Path,default=data_root())
    p.add_argument('--output-root',type=Path,default=REPO)
    p.add_argument('--fixtures-only',action='store_true')
    a=p.parse_args();f=fixtures()
    if a.fixtures_only:print(json.dumps(f));return
    b=a.project_root/'reviewer_comment_data';out=a.output_root
    truth={x['barcode'] for x in rows(out/'source_data/figure_02/truth_barcodes.tsv')}
    expectedrows=rows(out/'source_data/figure_02/assignment_per_target.tsv')
    selected={tool:{x['barcode'] for x in expectedrows if x['tool']==tool and x['selected']=='1'} for tool in TOOLS}
    sources={'RAD':b/'Figure2_RAD_full_global_20261029/runs/RAD_full_global/scoring/record_audit.tsv.gz',
             'Flexiplex':b/'sctagger_flexiplex_audit_20260812/L_flatQ20_audit_reads_barcodes.txt',
             'BLAZE':b/'paper_revision_20261022/prism/blaze2023_assignment_replay/assignment_records.tsv.gz'}
    expectedstates=rows(out/'source_data/figure_02/assignment_states.tsv')
    report={'command':[sys.executable,*sys.argv],'code_sha256':sha(Path(__file__)),'fixtures':f,'sources':[],
            'scope':'complete retained read-table resumption, not tool execution from raw FASTQ','tools':{},
            'expected_table_hashes':{str(x.relative_to(out)):sha(x) for x in
                [out/'source_data/figure_02/assignment_per_target.tsv',out/'source_data/figure_02/assignment_states.tsv']}}
    rebuilt=[]
    for tool in ('RAD','Flexiplex','BLAZE'):
        start=time.time();path=sources[tool]
        report['sources'].append({'tool':tool,'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path)})
        if tool in ('RAD','Flexiplex'):
            op=gzip.open if tool=='RAD' else open
            with op(path,'rt',newline='') as h:
                def records():
                    for r in csv.DictReader(h,delimiter='\t'):
                        if tool=='RAD':
                            if r['truth_barcode']!=r['read_id'][:16]:raise ValueError('RAD truth/read key')
                            yield r['read_id'],r['rad_cb'],r['truth_barcode'],bool(r['rad_cr'])
                        else:
                            yield r['Read'],r['CellBarcode'],r['Read'].rsplit('-',1)[0],r['RawCellBarcode']!=r['CellBarcode']
                counts,per,n,ids=count_records(records(),tool,truth,selected[tool])
        else:
            counts=Counter();per=defaultdict(Counter);seen=set();n=0
            with gzip.open(path,'rt',newline='') as h:
                for r in csv.DictReader(h,delimiter='\t'):
                    n+=1;rid=r['read_id'];true=r['true_barcode'];target=r['assigned_barcode']
                    if rid in seen or true not in truth or true!=rid[:16]:raise ValueError('BLAZE input identity')
                    seen.add(rid)
                    if target:
                        if target not in selected[tool]:raise ValueError('BLAZE unknown target')
                        state=('native' if r['putative_barcode']==target else 'corrected')+('_correct' if target==true else '_incorrect')
                        if state!=r['state']:raise ValueError('BLAZE stored state differs from independently classified state')
                        per[target][state]+=1
                    else:
                        state='unassigned'
                        if r['state']!=state:raise ValueError('BLAZE empty target state')
                    counts[state]+=1
            ids=len(seen)
            if ids!=NREADS:raise ValueError('BLAZE input universe incomplete')
        want={r['state']:int(r['reads']) for r in expectedstates if r['tool']==tool}
        got=assignment_state_counts(counts)
        if sum(got.values())!=NREADS:raise ValueError((tool,'assignment count conservation'))
        if got!=want:raise ValueError((tool,'state mismatch',got,want))
        compared=0
        for r in expectedrows:
            if r['tool']!=tool or r['selected']!='1':continue
            bc=r['barcode']
            for field in FIELDS:
                if per[bc][field]!=int(r[field]):raise ValueError((tool,bc,field,per[bc][field],r[field]))
                compared+=1
            rebuilt.append(dict(tool=tool,barcode=bc,**{field:per[bc][field] for field in FIELDS}))
        report['tools'][tool]={'status':'passed','records':n,'unique_physical_ids_in_checkpoint':ids,
                              'state_counts':got,'exact_per_target_value_comparisons':compared,'elapsed_seconds':time.time()-start}
        print(tool,report['tools'][tool],flush=True)
    report['independent_reconstruction']={'selected_rows':len(rebuilt),
        'canonical_json_sha256':hashlib.sha256(json.dumps(rebuilt,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        'publication':'one canonical assignment_per_target.tsv; every selected category checked above; duplicate rebuilt table not published'}
    report['status']='passed'
    write_json(out/'validation/figures_124_assignment_resume.json',report)


if __name__=='__main__':main()
