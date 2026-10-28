#!/usr/bin/env python3
"""Extract actual bounded, identity-closed examples, with source hashes."""
import collections,csv,gzip,json,subprocess,sys
from pathlib import Path
from source_paths import reviewer_root
from figure_3 import ROOT,sha,read,write,js
from figure_3_count import fastq_rows

OUT=ROOT/'data/examples/figure_03'
CHECKPOINT=ROOT/'checkpoints/figure_03/offlist_recount'
SOURCE=reviewer_root()

def rows(path):
    with gzip.open(path,'rt',newline='') as f:yield from csv.DictReader(f,delimiter='\t')

def main():
    OUT.mkdir(parents=True,exist_ok=True);manifest=[]
    for name,target in [('sctagger_rad_rep1','AAACCCACACAGTGAG'),('longbench_flexiplex_rep1','CCACTTGTCTTTCTTC')]:
        path=CHECKPOINT/(name+'_assignments.tsv.gz')
        initial=[r for r in rows(path) if r['target']==target]
        assert initial,'Requested example target absent'
        ids={r['original_id'] for r in initial}
        selected=[r for r in rows(path) if r['original_id'] in ids]
        write(OUT/(name+'_assignments.tsv'),selected)
        (OUT/(name+'_targets.txt')).write_text(target+'\n')
        command=[sys.executable,str(ROOT/'scripts/revision/figure_3_example_count.py'),str(OUT/(name+'_assignments.tsv')),str(OUT/(name+'_targets.txt')),str(OUT/(name+'_counts.tsv'))]
        result=subprocess.run(command,check=True,capture_output=True,text=True)
        (OUT/(name+'_stdout.txt')).write_text(result.stdout)
        expected=next(r for r in read(CHECKPOINT/'per_target.tsv') if r['barcode']==target and r['tool']==('RAD' if 'rad' in name else 'Flexiplex') and r['replicate']=='1' and r['dataset']==('ScTagger-L' if name.startswith('sctagger') else 'LongBench SC-ONT'))
        observed=read(OUT/(name+'_counts.tsv'))[0]['strict_physical_reads']
        assert observed==expected['strict_assigned']
        manifest.append(dict(example=name,source=str(path),source_sha256=sha(path),selection=f'All rows with target={target}, then all rows sharing ANY selected original_id; complete identity closure, no row limit',assignment_rows=len(selected),physical_ids=len(ids),barcode=target,strict_physical_reads=int(observed),checkpoint_row=expected,output_sha256=sha(OUT/(name+'_assignments.tsv'))))
        if 'flexiplex' in name:
            original=SOURCE/'longbench_sc_ont_false_whitelist_20260813/runs/flexiplex/rep1/flexiplex_SC_ONT_10M_false_rep1_audit_reads_barcodes.txt'
            with original.open(newline='') as f: side=[r for r in csv.DictReader(f,delimiter='\t') if r['Read'] in ids]
            write(OUT/(name+'_diagnostic.tsv'),side)
            report=json.loads((ROOT/'validation/figure_3_flexparity.json').read_text())
            parity=next(r for r in report['runs'] if r['dataset']=='LongBench SC-ONT' and r['replicate']==1)
            missing=[r for r in parity['sidecar_only_assignments'] if r['original_id'] in ids]
            assert len(missing)==1
            js(OUT/(name+'_sidecar_only.json'),dict(source=str(original),source_sha256=parity['sidecar_sha256'],comparison_fastq_sha256=parity['fastq_sha256'],selection='Sidecar-only IDs in the complete target example',sidecar_only_assignments=missing,full_run_sidecar_only_rows=parity['sidecar_only_rows']))
        else:
            original=next((SOURCE/'sctagger_L_false_whitelist_20260813/runs/rad/rep1').glob('*.fq.gz'))
            selected_ordinals={int(r['assignment_row']) for r in selected}
            with gzip.open(original,'rt') as f,(OUT/(name+'_assigned.fastq')).open('w') as g:
                i=0
                while True:
                    record=[f.readline() for _ in range(4)]
                    if not record[0]:break
                    i+=1
                    if i in selected_ordinals:g.writelines(record)
            manifest[-1]['producer_fastq']=str(original);manifest[-1]['producer_fastq_sha256']=sha(original)
    # A separate actual multi-target duplicate demonstrates the strict row rule.
    path=CHECKPOINT/'sctagger_rad_rep1_assignments.tsv.gz'
    allrows=list(rows(path));mult=collections.Counter(r['original_id'] for r in allrows)
    duplicate=next(r['original_id'] for r in allrows if mult[r['original_id']]>1)
    selected=[r for r in allrows if r['original_id']==duplicate]
    write(OUT/'actual_duplicate_assignments.tsv',selected)
    (OUT/'actual_duplicate_targets.txt').write_text('\n'.join(sorted({r['target'] for r in selected}))+'\n')
    subprocess.run([sys.executable,str(ROOT/'scripts/revision/figure_3_example_count.py'),str(OUT/'actual_duplicate_assignments.tsv'),str(OUT/'actual_duplicate_targets.txt'),str(OUT/'actual_duplicate_counts.tsv')],check=True)
    manifest.append(dict(example='actual_duplicate',source=str(path),source_sha256=sha(path),selection='First physical ID in source row order having >1 assignment row; all rows for that ID',original_id=duplicate,rows=len(selected)))
    # Actual full-run RAD assignments. The first10,000 raw reads are a bounded
    # retrieval source only; pilot calibration/assignments are not used here.
    base=ROOT/'checkpoints/figure_03/rage_matched';pilot=base/'inputs/pilot_10000.fastq.gz'
    fq=next((base/'runs/rad/rep1').glob('*.fq.gz'));all_assignments=list(fastq_rows(fq,'RAD'));multiplicity=collections.Counter(r['original_id'] for r in all_assignments)
    input_ids=set()
    with gzip.open(pilot,'rt') as f:
        while True:
            h=f.readline()
            if not h:break
            input_ids.add(h[1:].split()[0]);f.readline();f.readline();f.readline()
    selected=[r for r in all_assignments if multiplicity[r['original_id']]==1 and r['original_id'] in input_ids][:3]
    assert len(selected)==3
    ids={r['original_id'] for r in selected}
    write(OUT/'rage_raw_to_rad_assignments.tsv',selected)
    for source,dest,normalizer in [(pilot,OUT/'rage_raw_reads.fastq',lambda h:h[1:].split()[0]),(fq,OUT/'rage_rad_assigned.fastq',lambda h:__import__('re').sub(r'-[FR](?:-CT)?$','',h[1:].split()[0]))]:
        with gzip.open(source,'rt') as f,dest.open('w') as g:
            while True:
                record=[f.readline() for _ in range(4)]
                if not record[0]:break
                if normalizer(record[0]) in ids:g.writelines(record)
    checkpoint=read(base/'counts/per_target.tsv')
    c5=[r for r in checkpoint if r['tool']=='RAD' and r['replicate']=='1' and r['barcode'] in {x['target'] for x in selected}]
    write(OUT/'rage_raw_to_rad_C5_targets.tsv',c5)
    manifest.append(dict(example='rage_raw_to_rad',source=str(pilot),source_sha256=sha(pilot),full_raw_sha256=json.loads((base/'experiment.json').read_text())['expected_input_sha256'],selection='First three single-assignment physical IDs in FULL RADrep1 output order whose raw reads are in the verified first10,000raw-read slice; include every emitted full-run record for those IDs',physical_ids=sorted(ids),assigned_fastq_source=str(fq),assigned_fastq_sha256=sha(fq),full_C5_source=str(base/'counts/per_target.tsv'),full_C5_sha256=sha(base/'counts/per_target.tsv'),scope='actual full-run extraction illustration; linked complete target counts are deposited separately'))
    js(OUT/'selection_manifest.json',dict(status='passed',examples=manifest,script_sha256=sha(__file__)))
    print(json.dumps({'status':'passed','examples':len(manifest),'output':str(OUT)}))
if __name__=='__main__':main()
