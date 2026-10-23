#!/usr/bin/env python3
"""Count the current matched RAGE experiment from all nine producer outputs.

The complete raw input ID universe is checked independently. Every duplicate
assignment ID is excluded before per-target counting, even if targets agree.
"""
import collections,csv,gzip,json,re,subprocess
from pathlib import Path
from figure_3 import ROOT,TOOLS,sha,write,js
from figure_3_count import fastq_rows,flex_rows,strict_counts,reverse_complement
from figure_3_fastq_identity import fingerprint

ASSIGNMENT_FIELDS=['original_id','record_id','target','source','source_evidence','source_kind','orientation','ct','emitted_fastq','assignment_row']
READ_FATE_FIELDS=['original_id','assignment_rows','state']

def save_gz(path,rows,fields):
    with gzip.open(path,'wt',newline='') as f:
        w=csv.DictWriter(f,fields,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)

def main():
    executed_code={name:sha(ROOT/'scripts/revision'/name) for name in ['figure_3_rage_count.py','figure_3_count.py','figure_3_fastq_identity.py','figure_3.py']}
    base=ROOT/'checkpoints/figure_03/rage_matched';out=base/'counts';out.mkdir(exist_ok=True)
    m=json.loads((base/'experiment.json').read_text());raw_validation=json.loads((base/'input_validation.json').read_text())
    if raw_validation['status']!='passed':raise ValueError('Input preflight not passed')
    if sha(m['input'])!=raw_validation['compressed_sha256']:raise ValueError('Full raw input changed after preflight')
    identity_path=out/'input_id_validation.json';id_path=out/'input_original_ids.txt.gz'
    if not identity_path.exists():fingerprint(Path(m['input']),identity_path,id_path)
    identity=json.loads(identity_path.read_text())
    if identity['status']!='passed' or identity['compressed_sha256']!=raw_validation['compressed_sha256'] or identity['input_ids_sha256']!=sha(id_path):raise ValueError('Full input-ID checkpoint is stale or invalid')
    if identity['canonical_record_sha256']!=m['expected_input_canonical_record_sha256']:raise ValueError('Complete canonical ordered input identity differs')
    with gzip.open(id_path,'rt') as saved:raw_ids={line.rstrip('\n') for line in saved}
    input_records=identity['records'];duplicate_ids=identity['duplicate_original_ids']
    if duplicate_ids or input_records!=m['expected_input_reads'] or len(raw_ids)!=input_records:raise ValueError('Raw original IDs are not unique or input count differs')
    js(ROOT/'validation/figure_3_rage_input_identity.json',identity)
    per_target=[];summaries=[];validations=[];sources=[]
    for t in TOOLS:
        for rep in (1,2,3):
            run=base/'runs'/t.lower()/f'rep{rep}';manifest=json.loads((run/'run_manifest.json').read_text())
            if manifest['status']!='passed':raise ValueError(f'Producer not complete {t}/{rep}')
            if t=='RAD':producer_log=next(run.glob('*.log')) if not (run/f'rage_rep{rep}_rad.log').exists() else run/f'rage_rep{rep}_rad.log';pattern=r'Total reads processed:\s*([0-9,]+)'
            elif t=='Flexiplex':producer_log=run/'stderr.log';pattern=r'Number of reads processed:\s*([0-9,]+)'
            else:producer_log=run/'stdout.log';pattern=r'Total number of reads:\s*([0-9,]+)'
            observed=re.findall(pattern,producer_log.read_text())
            if not observed or int(observed[-1].replace(',',''))!=input_records:raise ValueError(f'{t}/{rep}: producer did not report complete raw input processing')
            for item in manifest['outputs']:
                if sha(item['path'])!=item['sha256']:raise ValueError('Producer output changed after successful completion')
            target_path=base/'inputs'/f'false_rep{rep}.txt';targets=target_path.read_text().splitlines()
            if sha(target_path)!=manifest['target_sha256']:raise ValueError('Target list drift')
            if t=='Flexiplex':
                assignment=next(run.glob('*_reads_barcodes.txt'));rows=list(flex_rows(assignment))
                fq=next(run.glob('*.fastq.gz'));fq_pairs=collections.Counter((r['original_id'],r['target']) for r in fastq_rows(fq,t));sc_pairs=collections.Counter((r['original_id'],r['target']) for r in rows)
                if fq_pairs-sc_pairs:raise ValueError('FASTQ assignments absent from diagnostic sidecar')
                missing=sc_pairs-fq_pairs
                for r in rows:
                    key=(r['original_id'],r['target']);emitted=fq_pairs[key];diagnostic=sc_pairs[key]
                    r['emitted_fastq']=1 if emitted==diagnostic else 0 if emitted==0 else 'undetermined_within_repeated_pair'
                parity=dict(fastq_rows=sum(fq_pairs.values()),sidecar_rows=len(rows),sidecar_only_rows=sum(missing.values()),fastq_only_rows=0,partially_emitted_repeated_pairs=sum(0<fq_pairs[k]<n for k,n in sc_pairs.items()),sidecar_only_assignment_pairs=[dict(original_id=k[0],target=k[1],rows=n) for k,n in missing.items()])
                js(out/f'flexiplex_rep{rep}_parity.json',dict(status='passed',**parity))
                del fq_pairs,sc_pairs
            else:
                assignment=next(run.glob('*.fq.gz')) if t=='RAD' else run/'matched_reads.fastq.gz'
                rows=list(fastq_rows(assignment,t));parity={}
                if t=='BLAZE':
                    wanted={r['original_id'] for r in rows};raw={};putative_rows=0;putative_ids=set()
                    with (run/'putative_bc.csv').open(newline='') as f:
                        reader=csv.reader(f);header=next(reader)
                        if header[0]!='read_id':raise ValueError('Unexpected BLAZE extraction schema')
                        for r in reader:
                            if r:
                                putative_rows+=1
                                if r[0] not in raw_ids:raise ValueError('BLAZE extraction ID absent from raw input')
                                if r[0] in putative_ids:raise ValueError('Duplicate physical ID in BLAZE extraction table')
                                putative_ids.add(r[0])
                            if r and r[0] in wanted:
                                if r[0] in raw and raw[r[0]]!=r[1]:raise ValueError('Conflicting BLAZE raw source rows')
                                raw[r[0]]=r[1]
                    if putative_rows!=input_records or len(putative_ids)!=input_records:raise ValueError('BLAZE extraction table does not cover the complete raw input')
                    for r in rows:
                        r['source']=raw.get(r['original_id'],'');r['source_evidence']='BLAZE_putative_csv' if r['original_id'] in raw else 'missing'
                        r['orientation']='as_reported_in_putative_table'
                    del wanted,raw,putative_ids
            unknown={r['original_id'] for r in rows if r['original_id'] not in raw_ids}
            if unknown:raise ValueError(f'{t}/{rep}: assigned IDs absent from raw input: {len(unknown)}')
            counts,fate=strict_counts(rows,targets,len(raw_ids));multiplicity=collections.Counter(r['original_id'] for r in rows)
            native=collections.Counter();corrected=collections.Counter();missing_source=collections.Counter();ambiguous=collections.Counter()
            for r in rows:
                if multiplicity[r['original_id']]>1:ambiguous[r['target']]+=1;continue
                source=r['source']
                if t=='RAD' and not source:source=r['target']
                elif r['orientation']=='reverse_raw':source=reverse_complement(source)
                if not source:missing_source[r['target']]+=1
                elif source==r['target']:native[r['target']]+=1
                else:corrected[r['target']]+=1
            for rank,bc in enumerate(targets,1):per_target.append(dict(tool=t,replicate=rep,rank=rank,barcode=bc,count=counts[bc],native=native[bc],corrected=corrected[bc],raw_unavailable=missing_source[bc],ambiguous_assignment_rows=ambiguous[bc]))
            ledger=out/f'{t.lower()}_rep{rep}_assignments.tsv.gz';save_gz(ledger,rows,ASSIGNMENT_FIELDS)
            read_fates=[dict(original_id=rid,assignment_rows=n,state='strict_assigned' if n==1 else 'ambiguous_excluded') for rid,n in multiplicity.items()]
            save_gz(out/f'{t.lower()}_rep{rep}_assigned_read_fates.tsv.gz',read_fates,READ_FATE_FIELDS)
            summaries.append(dict(tool=t,replicate=rep,target_count=len(targets),strict_unique_assigned_total=fate['strict_assigned'],assignment_records=fate['assignment_rows'],unique_physical_read_ids=fate['unique_assignment_ids'],ambiguous_physical_read_ids=fate['ambiguous_ids'],input_reads=fate['input_reads'],unassigned=fate['unassigned'],assignment_fraction=fate['strict_assigned']/fate['input_reads'],sidecar_only_assignment_rows=parity.get('sidecar_only_rows',0),assignment_ledger_sha256=sha(ledger)))
            validations.append(dict(tool=t,replicate=rep,status='passed',unknown_input_ids=0,producer_reported_input_reads=input_records,producer_log_sha256=sha(producer_log),strict_assigned=fate['strict_assigned'],ambiguous_ids=fate['ambiguous_ids'],unassigned=fate['unassigned'],input_reads=fate['input_reads'],conservation=fate['strict_assigned']+fate['ambiguous_ids']+fate['unassigned']==fate['input_reads'],target_count=len(targets),assignment_rows=fate['assignment_rows']))
            sources.append(dict(tool=t,replicate=rep,assignment_path=str(assignment),assignment_sha256=sha(assignment),run_manifest_sha256=sha(run/'run_manifest.json'),target_sha256=sha(target_path)))
            write(out/'per_target.tsv',per_target);write(out/'per_run_summary.tsv',summaries);write(out/'sources.tsv',sources)
            js(out/'validation.json',dict(status='running',runs=validations));print(json.dumps(validations[-1]),flush=True)
            del rows,read_fates,multiplicity
    report=dict(status='passed',scope='full raw-to-assignment-to-strict-count matched RAGE replication',runs=validations,input_ids=dict(records=input_records,unique=len(raw_ids),duplicate=duplicate_ids),input_sha256=raw_validation['compressed_sha256'],input_canonical_record_sha256=identity['canonical_record_sha256'],experiment_sha256=sha(base/'experiment.json'),source_hashes=sha(out/'sources.tsv'),per_target_sha256=sha(out/'per_target.tsv'),per_run_summary_sha256=sha(out/'per_run_summary.tsv'),counting_code_sha256=executed_code['figure_3_rage_count.py'],executed_code_sha256=executed_code,statistics='No new hypothesis test or annotation selection')
    js(out/'validation.json',report);js(ROOT/'validation/figure_3_rage_complete.json',report)
    print(json.dumps({'status':'passed','all_runs':9,'input_reads':input_records,'summary':str(out/'per_run_summary.tsv')}),flush=True)
if __name__=='__main__':main()
