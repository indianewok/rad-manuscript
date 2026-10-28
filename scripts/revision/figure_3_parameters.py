#!/usr/bin/env python3
"""Publish exact parameters separately for each selected Figure3 analysis arm."""
import argparse,json,shutil
from pathlib import Path
from source_paths import reviewer_root
from figure_3 import ROOT,sha,read,write,js
from tool_parameter_schema import FIELDS, project_parameters, details_path_name, prepare_evidence_rows

B=reviewer_root()
RAD='cd0582b2440cde0f35725dc557fa47307d74d374'
BLAZE='af8d2cc9f6374caf4d1006d5f8a0e99097211646'
FLEX='d84c8ae4f3865052f2b5ecec816949b94682f302'
PATCH='88dc9cbad139d8ac416803c19c1d4291ebb7e3159f5a1a49205aff59319f86cb'

def metadata(path):
    answer={}
    for line in path.read_text().splitlines():
        sep='\t' if '\t' in line else '='
        if sep in line:k,v=line.split(sep,1);answer[k]=v
    return answer

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root',type=Path,default=reviewer_root(),help='Restored reviewer source archive')
    args=parser.parse_args();B=args.project_root
    out=ROOT/'manifests/figure_3_producers';out.mkdir(exist_ok=True);result=[]
    fields=['analysis','dataset','tool','replicate','version','source_commit','binary_sha256','entrypoint_sha256','patch_sha256','threads','compression_threads','PYTHONHASHSEED','FLEXIPLEX_AUDIT_SOURCE_FILE','chemistry','input_sha256','catalog_sha256','reference_sha256','target_sha256','list_seed','layout_sha256','argv','evidence','evidence_sha256','limitations']
    def record(**kwargs):result.append({k:kwargs.get(k,'') for k in fields})
    for dataset,package in [('ScTagger-L','sctagger_L_false_whitelist_20260813'),('LongBench SC-ONT','longbench_sc_ont_false_whitelist_20260813')]:
        base=B/package
        for t in ['rad','blaze','flexiplex']:
            for rep in (1,2,3):
                p=base/'runs'/t/f'rep{rep}'/'run_metadata.tsv';m=metadata(p)
                saved=out/f'{dataset.split()[0].lower()}_offlist_{t}_rep{rep}.tsv';shutil.copyfile(p,saved)
                record(analysis='offlist',dataset=dataset,tool={'rad':'RAD','blaze':'BLAZE','flexiplex':'Flexiplex'}[t],replicate=rep,version={'rad':'1.0.2','blaze':'2.6.0a0','flexiplex':'1.02.6 diagnostic'}[t],source_commit={'rad':RAD,'blaze':BLAZE,'flexiplex':FLEX}[t],binary_sha256=m.get('rad_sha256',m.get('python_sha256',m.get('binary_sha256',''))),entrypoint_sha256=m.get('blaze_sha256',''),patch_sha256=PATCH if t=='flexiplex' else '',threads=m.get('threads',m.get('flexiplex_threads','')),compression_threads='4+4 pipeline' if t=='flexiplex' else 'not separately recorded',PYTHONHASHSEED='not recorded' if t=='blaze' else 'not applicable',FLEXIPLEX_AUDIT_SOURCE_FILE='not captured by retained producer receipt' if t=='flexiplex' else 'not applicable',chemistry='10x3v3 UMI12',input_sha256=m['input_sha256'],catalog_sha256=m.get('global_catalog_sha256','843a6f7038db8cb3c06f3dc21cc69d04139ffa10689780518d7a9e42dc2e819b'),reference_sha256='2418b849f88ce6f28cf8c702acab795e4b483f6b2da17953675fce96b405899e' if dataset=='ScTagger-L' else '3492fa9dde1af8a2a6e3a687a0fdf26f66ca733f1e828660ea1b37adfdc32e11',target_sha256=m['target_sha256'],list_seed=20260812+rep if dataset=='ScTagger-L' else 2026081300+rep,layout_sha256=m.get('layout_sha256','not used by tool'),argv=m['command'],evidence=str(saved.relative_to(ROOT)),evidence_sha256=sha(saved),limitations='Retained producer C2 fully recounted; raw extraction not rerun')
    latest=B/'scratch_preservation_20260921/files/longbench_rad_4acbe00_raw_prism_20260827';comp=B/'LongBench_comps/full_A_to_B_audit_20260731'
    for arm in read(ROOT/'manifests/figure_3_arms.tsv'):
        d,t=arm['dataset'],arm['tool'];name={'RAD':'rad','BLAZE':'blaze','Flexiplex':'flex_v1026'}[t]
        p=latest/'runs'/d/'run_metadata.txt' if t=='RAD' else comp/'provenance/producers'/name/d/'run_metadata.txt';m=metadata(p)
        saved=out/f'{d}_correction_{name}.txt';shutil.copyfile(p,saved)
        if t=='RAD':
            command=f"{m['rad_binary']} demux --layout {m['layout']} --fastq {m['raw']} --global-whitelist {m['global_whitelist']} --custom-whitelist {m['custom_whitelist']} --bc-correction-mode offensive --whitelist-mutation 2 --generated-mutation 2 --min-read-length 85 --dir {str(Path(m['rad_binary']).parents[1]/'runs'/d/'demux')} --output {d}_RAD --log-file {str(Path(m['rad_binary']).parents[1]/'runs'/d/'demux'/f'{d}_RAD.log')} --threads {m['rad_threads']} --chunk-size 5000 --verbose"
            runner=latest/'scripts/run_one_arm.sh';shutil.copyfile(runner,out/'correction_RAD_run_one_arm.sh')
        elif t=='BLAZE':command=(p.parent/'time.txt').read_text().splitlines()[0].split('Command being timed: ',1)[1].strip('"')
        else:command=m['command']+'; INPUT='+m['input']+'; SELECTED='+m['selected_whitelist']+'; THREADS='+m['threads']
        record(analysis='correction D-G',dataset=d,tool=t,replicate='one full input',version=arm['version'],source_commit=m.get('rad_commit',FLEX if t=='Flexiplex' else 'not recorded in producer receipt'),binary_sha256=m.get('rad_binary_sha256',m.get('binary_sha256','not recorded in producer receipt')),patch_sha256=PATCH if t=='Flexiplex' else '',threads=m.get('rad_threads',m.get('threads','')),compression_threads=m.get('pigz_threads','not separately recorded'),PYTHONHASHSEED=m.get('PYTHONHASHSEED','not applicable'),FLEXIPLEX_AUDIT_SOURCE_FILE='unset by diagnostic runner' if t=='Flexiplex' else 'not applicable',chemistry='10x3v3 UMI12',input_sha256='not recorded in selected receipt',catalog_sha256=arm['catalog_sha256'],reference_sha256=arm['reference_sha256'],target_sha256=arm['selected_sha256'],list_seed='native selected list; no list draw',layout_sha256=m.get('layout_sha256','not used by tool'),argv=command,evidence=str(saved.relative_to(ROOT)),evidence_sha256=sha(saved),limitations='Complete C5 marginals verified; full source-bearing assignment stream unavailable at recorded path; BLAZE2.5.0 receipt does not pin executable/source hash' if t=='BLAZE' else 'Complete C5 marginals verified; full source-bearing assignment stream unavailable at recorded path')
    base=ROOT/'checkpoints/figure_03/rage_matched';exp=json.loads((base/'experiment.json').read_text())
    for t in ['rad','blaze','flexiplex']:
        for rep in (1,2,3):
            p=base/'runs'/t/f'rep{rep}'/'run_manifest.json'
            if not p.exists():continue
            m=json.loads(p.read_text());saved=out/f'rage_offlist_{t}_rep{rep}.json';shutil.copyfile(p,saved)
            record(analysis='offlist matched raw replay',dataset='RAGE-seq',tool=m['tool'],replicate=rep,version={'rad':'1.0.2 rebuilt from pinned source','blaze':'2.6.0a0','flexiplex':'1.02.6 diagnostic'}[t],source_commit={'rad':RAD,'blaze':BLAZE,'flexiplex':FLEX}[t],binary_sha256=m['executable_sha256'],entrypoint_sha256=sha(exp['blaze_entrypoint']) if t=='blaze' else '',patch_sha256=PATCH if t=='flexiplex' else '',threads=16,compression_threads=2,PYTHONHASHSEED='20261023',FLEXIPLEX_AUDIT_SOURCE_FILE='UNSET',chemistry='10x3v2 UMI10',input_sha256=m['input_sha256'],catalog_sha256=m['catalog_sha256'],reference_sha256=m['reference_sha256'],target_sha256=m['target_sha256'],list_seed=2026102300+rep,layout_sha256=m['layout_sha256'],argv=json.dumps(m.get('pipeline',m['argv'])),evidence=str(saved.relative_to(ROOT)),evidence_sha256=sha(saved),limitations='Producer status='+m['status']+'; full physical-ID count validation recorded separately')
    result=prepare_evidence_rows(result,ROOT)
    write(ROOT/'manifests'/details_path_name('3'),result,fields+['evidence_original_sha256'])
    write(ROOT/'manifests/figure_3_tool_parameters.tsv',project_parameters(result,'3',ROOT),FIELDS)
    print(json.dumps({'status':'written','analysis_arms':len(result),'manifest':'manifests/figure_3_tool_parameters.tsv'}))
if __name__=='__main__':main()
