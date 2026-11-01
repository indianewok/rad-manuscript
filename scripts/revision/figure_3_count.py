#!/usr/bin/env python3
"""Figure 3 C2 strict-read recount and independent pair-classification fixtures.

No producer is rerun. Input package directories are always read-only.
The full offlist command writes compressed identity-bearing assignment ledgers.
"""
import argparse
import collections
import csv
import gzip
import json
import re
from pathlib import Path
import sys
from figure_3 import ROOT, PACKAGES, TOOLS, EXPECTED, sha, read, write, js, tool

def physical_id(record_id, name):
    if name=='BLAZE':
        return re.sub(r'_[+-]$', '', record_id.split('#',1)[1]) if '#' in record_id else record_id
    if name=='RAD':return re.sub(r'-[FR](?:-CT)?$', '',record_id)
    if name=='Flexiplex' and '#' in record_id:return re.sub(r'_[+-]?\d+of\d+$','',record_id.split('#',1)[1])
    return record_id

def reverse_complement(seq):return seq.translate(str.maketrans('ACGTNacgtn','TGCANtgcan'))[::-1]

def strict_counts(rows, targets, input_count):
    """Multiplicity counts assignment rows, NOT distinct target identities."""
    multiplicities=collections.Counter(r['original_id'] for r in rows)
    counts=collections.Counter({t:0 for t in targets})
    for r in rows:
        if not r['original_id'] or r['target'] not in counts:raise ValueError('missing ID or off-target assignment')
        if multiplicities[r['original_id']]==1:counts[r['target']]+=1
    amb=sum(n>1 for n in multiplicities.values());assigned=sum(counts.values())
    unassigned=input_count-len(multiplicities)
    if unassigned<0 or input_count!=assigned+amb+unassigned:raise ValueError('physical-read conservation failed')
    return counts,dict(input_reads=input_count,strict_assigned=assigned,ambiguous_ids=amb,unassigned=unassigned,assignment_rows=len(rows),unique_assignment_ids=len(multiplicities))

def pair_ledger(rows,catalog,reference,selected):
    """Exact unordered grouping preserves read re-entry and category overlap.

    Rows must already hold forward-normalized observed sources. Missing source
    is unknown except explicit source_kind=rad_empty_CR_native.
    """
    pairs={}
    for r in rows:
        rid=r['original_id'];target=r['target']
        if not rid or target not in selected:raise ValueError('missing ID or target not selected')
        key=(rid,target)
        p=pairs.setdefault(key,dict(original_id=rid,target=target,sources=set(),source_evidence=set(),assignment_record_count=0,CT_records=0,corrected_off_list=False,failure_mode_1=False,failure_mode_2=False,missing_source=False))
        p['assignment_record_count']+=1;p['CT_records']+=int(r.get('ct',False));p['source_evidence'].add(r.get('source_evidence',''))
        source=r.get('source','')
        if not source and r.get('source_kind')=='rad_empty_CR_native':source=target
        if not source:p['missing_source']=True;continue
        if r.get('orientation')=='reverse_raw':source=reverse_complement(source)
        p['sources'].add(source)
        if source==target:continue
        if source not in catalog:p['corrected_off_list']=True
        if source in reference and target in reference:p['failure_mode_1']=True
        if source in catalog and source not in reference:p['failure_mode_2']=True
    return [dict(p,sources=sorted(p['sources']),source_evidence=sorted(p['source_evidence']),conflicting_sources=len(p['sources'])>1) for p in pairs.values()]

def fastq_rows(path,name):
    op=gzip.open if str(path).endswith('.gz') else open
    with op(path,'rt') as f:
        ordinal=0
        while True:
            h=f.readline()
            if not h:break
            s=f.readline();plus=f.readline();q=f.readline();ordinal+=1
            if not (h.startswith('@') and plus.startswith('+') and s and q and len(s.rstrip())==len(q.rstrip())):raise ValueError(f'Malformed FASTQ record {ordinal}: {path}')
            fields=h[1:].split();record=fields[0];tags={x[:2]:x[5:] for x in fields[1:] if len(x)>=5 and x[2:5]==':Z:'}
            cb=tags.get('CB','');raw=tags.get('CR','')
            if not cb:raise ValueError(f'Missing CB at {path}:{ordinal}')
            yield dict(original_id=physical_id(record,name),record_id=record,target=cb,source=raw,source_evidence='RAD_CR' if name=='RAD' else 'BLAZE_putative_pending',source_kind='rad_empty_CR_native' if name=='RAD' and not raw else 'observed',orientation='reverse_raw' if name=='RAD' and re.search(r'-R(?:-CT)?$',record) else 'forward',ct=int(record.endswith('-CT')),emitted_fastq=1,assignment_row=ordinal)

def flex_rows(path):
    with open(path,newline='') as f:
        reader=csv.DictReader(f,delimiter='\t')
        if not {'Read','CellBarcode','RawCellBarcode'}<=set(reader.fieldnames):raise ValueError('invalid diagnostic sidecar schema')
        for i,r in enumerate(reader,1):
            yield dict(original_id=r['Read'],record_id=r['Read'],target=r['CellBarcode'],source=r['RawCellBarcode'],source_evidence='Flexiplex_RawCellBarcode',source_kind='observed',orientation='as_reported',ct=0,emitted_fastq='not_checked',assignment_row=i)

def fixture(out):
    # IDs intentionally re-enter; duplicate identical targets must not survive.
    rows=[dict(original_id='a',target='AAAA'),dict(original_id='b',target='AAAA'),dict(original_id='c',target='CCCC'),dict(original_id='a',target='AAAA'),dict(original_id='c',target='AAAA')]
    counts,fate=strict_counts(rows,['AAAA','CCCC','GGGG'],5)
    assert dict(counts)=={'AAAA':1,'CCCC':0,'GGGG':0}
    assert fate['strict_assigned']==1 and fate['ambiguous_ids']==2 and fate['unassigned']==2
    pairrows=[dict(original_id='x',target='AAAA',source='NNNN'),dict(original_id='z',target='AAAA',source=''),dict(original_id='x',target='AAAA',source='CCCC',ct=1),dict(original_id='x',target='AAAA',source='GGGG'),dict(original_id='x',target='AAAA',source='NNNN'),dict(original_id='x',target='CCCC',source='NNNN'),dict(original_id='n',target='AAAA',source='',source_kind='rad_empty_CR_native'),dict(original_id='rev',target='AAAA',source='GGGG',orientation='reverse_raw')]
    ledger=pair_ledger(pairrows,{'AAAA','CCCC','GGGG'},{'AAAA','GGGG'},{'AAAA','CCCC'})
    p=next(r for r in ledger if r['original_id']=='x' and r['target']=='AAAA')
    assert p['corrected_off_list'] and p['failure_mode_1'] and p['failure_mode_2'] and p['assignment_record_count']==4 and p['CT_records']==1
    assert len(ledger)==5
    assert next(r for r in ledger if r['original_id']=='z')['missing_source']
    assert not next(r for r in ledger if r['original_id']=='z')['corrected_off_list']
    assert not next(r for r in ledger if r['original_id']=='n')['corrected_off_list']
    reverse=next(r for r in ledger if r['original_id']=='rev')
    assert reverse['failure_mode_2'] and not reverse['failure_mode_1']
    reference_change=pair_ledger([dict(original_id='reference_change',target='AAAA',source='GGGG')],{'AAAA','CCCC','GGGG'},{'AAAA','GGGG'},{'AAAA','CCCC'})[0]
    assert reference_change['failure_mode_1'] and not reference_change['failure_mode_2']
    assert physical_id('r-R-CT','RAD')=='r' and physical_id('AAAA_UMI#read_+','BLAZE')=='read'
    assert physical_id('AAAA_UMI#read_-1of2','Flexiplex')=='read'
    for bad in [[dict(original_id='',target='AAAA')],[dict(original_id='a',target='TTTT')]]:
        try:strict_counts(bad,['AAAA'],5)
        except ValueError:pass
        else:raise AssertionError('invalid identity was accepted')
    js(out,dict(status='passed',scope='independent hand-computable fixtures only',checks=['same-target duplicate exclusion','multitarget exclusion in strict counts','zero-count target','input conservation','read re-entry','pair deduplication','multitarget retention for correction','overlapping class flags','missing source unknown','RAD empty CR native','reverse complement','CT retention','identity/schema rejection'],strict_expected=fate,pair_ledger=ledger))
    print('Figure 3 counting fixtures passed')

def flex_parity(a):
    reports=[]
    for dataset in ['ScTagger-L','LongBench SC-ONT']:
        base=a.project_root/PACKAGES[dataset]
        for rep in (1,2,3):
            run=base/'runs/flexiplex'/f'rep{rep}'
            sidecar=next(run.glob('*_reads_barcodes.txt'));fastq=next(run.glob('*.fastq.gz'))
            sc=collections.Counter((r['original_id'],r['target']) for r in flex_rows(sidecar))
            fq=collections.Counter((r['original_id'],r['target']) for r in fastq_rows(fastq,'Flexiplex'))
            missing=sc-fq;extra=fq-sc
            side_ids={x[0] for x in sc};fq_ids={x[0] for x in fq}
            shared=side_ids&fq_ids
            mismatches=sum(sc[k]!=fq[k] for k in sc.keys()|fq.keys() if k[0] in shared)
            expected_missing=([4,1,0][rep-1] if dataset=='LongBench SC-ONT' else 0)
            good=sum(missing.values())==expected_missing and not extra and mismatches==0
            reports.append(dict(dataset=dataset,replicate=rep,status='passed' if good else 'failed',sidecar_rows=sum(sc.values()),fastq_rows=sum(fq.values()),sidecar_only_rows=sum(missing.values()),sidecar_only_ids=len(side_ids-fq_ids),fastq_only_rows=sum(extra.values()),shared_pair_mismatches=mismatches,sidecar_sha256=sha(sidecar),fastq_sha256=sha(fastq),sidecar_only_assignments=[dict(original_id=key[0],target=key[1],rows=n) for key,n in missing.items()]))
            print(json.dumps(reports[-1]),flush=True)
            js(a.output,dict(status='running' if good else 'failed',scope='full retained Flex diagnostic sidecar versus emitted FASTQ',runs=reports))
            if not good:raise ValueError('Flex sidecar/FASTQ mismatch')
    js(a.output,dict(status='passed',scope='full retained Flex diagnostic sidecar versus emitted FASTQ',runs=reports,script_sha256=sha(__file__)))

def offlist(a):
    a.output.mkdir(parents=True,exist_ok=True)
    validations=[];sources=[];all_counts=[];fates=[]
    for dataset in ['ScTagger-L','LongBench SC-ONT']:
        base=a.project_root/PACKAGES[dataset]
        input_count=4993805 if dataset=='ScTagger-L' else 10000000
        expected_rows=read(base/'results/false_target_assigned_reads_long.tsv')
        expected={(tool(r['tool']),int(r['replicate']),r['barcode']):int(r.get('assigned_reads',r.get('count'))) for r in expected_rows}
        for t in TOOLS:
            for rep in (1,2,3):
                if a.dataset and a.dataset!=dataset:continue
                run=base/'runs'/t.lower()/f'rep{rep}'
                p=run/'supplied_whitelist_used.txt'
                if t=='BLAZE':p=run/'known_bc_list_used.txt'
                if not p.exists():p=base/'whitelists'/f'false_rep{rep}.txt'
                targets=p.read_text().splitlines()
                if len(set(targets))!=len(targets):raise ValueError('duplicate supplied target')
                sources.append(dict(path=str(p),sha256=sha(p),role='supplied_target_list'))
                if t=='Flexiplex':
                    files=list(run.glob('*_reads_barcodes.txt'))
                    if len(files)!=1:raise ValueError(f'expected one sidecar: {run}')
                    assignment=files[0];rows=list(flex_rows(assignment))
                else:
                    files=list(run.glob('*.fq.gz')) if t=='RAD' else [run/'matched_reads.fastq.gz']
                    if len(files)!=1:raise ValueError(f'expected one assigned FASTQ: {run}')
                    assignment=files[0];rows=list(fastq_rows(assignment,t))
                    if t=='BLAZE':
                        wanted={r['original_id'] for r in rows};raw={};p=run/'putative_bc.csv'
                        with open(p,newline='') as f:
                            rd=csv.reader(f);header=next(rd)
                            if header[0]!='read_id':raise ValueError('bad BLAZE source schema')
                            for r in rd:
                                if r and r[0] in wanted:
                                    value=r[1].strip()
                                    if r[0] in raw and raw[r[0]]!=value:raise ValueError('conflicting BLAZE source rows')
                                    raw[r[0]]=value
                        for r in rows:r['source']=raw.get(r['original_id'],'');r['source_evidence']='BLAZE_putative_csv' if r['original_id'] in raw else 'missing'
                        sources.append(dict(path=str(p),sha256=sha(p),role='extracted_raw_barcodes'))
                sources.append(dict(path=str(assignment),sha256=sha(assignment),role='retained_C2_assignment'))
                counts,fate=strict_counts(rows,targets,input_count)
                differences=[dict(barcode=bc,expected=expected.get((t,rep,bc)),observed=n) for bc,n in counts.items() if expected.get((t,rep,bc))!=n]
                status='passed' if not differences else 'failed'
                validations.append(dict(dataset=dataset,tool=t,replicate=rep,status=status,all_targets_compared=len(counts),differences=differences,observed_total=sum(counts.values()),expected_total=EXPECTED[dataset][t][rep-1]))
                stem=('sctagger' if dataset=='ScTagger-L' else 'longbench')+'_'+t.lower()+f'_rep{rep}'
                tmp=a.output/(stem+'_assignments.tsv.gz.tmp');final=a.output/(stem+'_assignments.tsv.gz')
                with gzip.open(tmp,'wt',newline='') as f:
                    w=csv.DictWriter(f,list(rows[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
                tmp.replace(final)
                multiplicity=collections.Counter(r['original_id'] for r in rows)
                read_rows=[dict(original_id=rid,assignment_rows=n,state='strict_assigned' if n==1 else 'ambiguous_excluded') for rid,n in multiplicity.items()]
                with gzip.open(a.output/(stem+'_assigned_read_fates.tsv.gz'),'wt',newline='') as f:
                    w=csv.DictWriter(f,list(read_rows[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(read_rows)
                fates.append(dict(dataset=dataset,tool=t,replicate=rep,**fate,ledger_sha256=sha(final)))
                all_counts.extend(dict(dataset=dataset,tool=t,replicate=rep,barcode=bc,strict_assigned=n) for bc,n in sorted(counts.items()))
                write(a.output/'per_target.tsv',all_counts);write(a.output/'read_fates.tsv',fates);write(a.output/'source_hashes.tsv',sources)
                js(a.output/'validation.json',dict(status='running' if status=='passed' else 'failed',level='full_retained_C2_to_C5',raw_rerun='not run',runs=validations))
                print(json.dumps(validations[-1]),flush=True)
                if differences:raise ValueError('full-data per-target recount mismatch')
    js(a.output/'validation.json',dict(status='passed',level='full_retained_C2_to_C5',raw_rerun='not run',runs=validations,script_sha256=sha(__file__),ledgers='all assigned physical IDs retained; unassigned identities require raw input ID universe',limitations='Flex sidecar retained even when no FASTQ record; emitted_fastq flag not yet independently reconciled'))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['fixture','offlist','flex-parity']);p.add_argument('--project-root',type=Path);p.add_argument('--output',type=Path);p.add_argument('--dataset',choices=['ScTagger-L','LongBench SC-ONT']);a=p.parse_args()
    if a.mode=='fixture':fixture(a.output or ROOT/'validation/figure_3_counting_fixtures.json')
    else:
        if not a.output or not a.project_root:p.error('offlist needs --output and --project-root')
        (flex_parity if a.mode=='flex-parity' else offlist)(a)
if __name__=='__main__':main()
