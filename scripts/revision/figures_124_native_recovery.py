#!/usr/bin/env python3
"""Recover moved native-master callsets by recorded identity; rescore Tilgner."""
import argparse
import csv
import gzip
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from figures_124 import REPO, sha, write_json


def barcodes(p):
    op=gzip.open if p.suffix=='.gz' else open
    with op(p,'rt') as f:
        return {re.split(r'[\t, ]+',x.strip())[0].removesuffix('-1') for x in f if x.strip()}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project-root',type=Path,default=Path('/dartfs/rc/lab/A/AckermanLab/CMV/rad_data'))
    ap.add_argument('--output-root',type=Path,default=REPO)
    a=ap.parse_args();base=a.project_root/'reviewer_comment_data';out=a.output_root
    dest=Path(tempfile.mkdtemp(prefix='rad_current_native_validation_'));original=base/'master_native_comparison_20260811'
    for name in ('tables','provenance'):shutil.copytree(original/name,dest/name,dirs_exist_ok=True)
    (dest/'validation').mkdir(exist_ok=True)
    mapping={};checks=[];missing=[]
    p=base/'tilgner_all10_native_three_tool_whitelist_20260810'
    index=list(csv.DictReader((p/'provenance/SOURCE_INDEX.tsv').open(),delimiter='\t'))
    for r in index:
        old=Path(r['SourceCallset'])
        target=old if old.is_file() else p/'callsets'/f"{r['Dataset']}.{r['Tool']}.txt"
        digest=sha(target)
        identity='byte-identical' if digest==r['SourceSHA256'] else 'normalized retained copy; independently rescored below'
        mapping[str(old)]=str(target)
        checks.append(dict(original_path=str(old),resolved_path=str(target),sha256=digest,
                           expected_original_sha256=r['SourceSHA256'],identity=identity))
    manifest=base/'visium_three_tool_splitaware_scatter_20260802/provenance/status_callset_manifest.csv'
    for r in csv.DictReader(manifest.open()):
        target=Path(r['path'].replace('/rad_data/wl_scan/','/rad_data/reviewer_comment_data/wl_scan/'))
        if not target.is_file():
            missing.append(dict(original_path=r['path'],checked_path=str(target),expected_sha256=r['sha256'],
                                reason='not at checked original or mapped path; retained metric table still available'))
            continue
        digest=sha(target)
        if digest!=r['sha256']:raise ValueError('Visium moved-file identity mismatch: '+str(target))
        mapping[r['path']]=str(target)
        checks.append(dict(original_path=r['path'],resolved_path=str(target),sha256=digest,identity='byte-identical'))
    write_json(dest/'path_map.json',mapping)
    write_json(out/'validation/figures_124_native_master_path_recovery.json',dict(status='passed with explicit missing callsets',
               command=[sys.executable,*sys.argv],code_sha256=sha(Path(__file__)),checks=checks,missing_callsets=missing))
    subprocess.run([sys.executable,str(Path(__file__).with_name('figures_124_master_validate.py')),
                    '--root',str(dest),'--path-map',str(dest/'path_map.json')],check=True)
    current={(r['canonical_id'],r['tool']):r for r in csv.DictReader((out/'source_data/figure_04/barcode_detection_metrics.tsv').open(),delimiter='\t')}
    checks=[]
    for r in index:
        sample,tool=r['Dataset'],r['Tool'];donor=sample.split('_')[2]
        calls=p/'callsets'/f'{sample}.{tool}.txt';reference=p/'reference'/f'{donor}.cellranger_filtered_barcodes.txt.gz'
        c,t=barcodes(calls),barcodes(reference)
        got=[len(c),len(t),len(c&t),len(c-t),len(t-c)]
        want=[int(current[(sample,tool)][x]) for x in ['calls','reference_n','tp','fp','fn']]
        if got!=want:raise ValueError((sample,tool,got,want))
        checks.append(dict(input_id=sample,tool=tool,status='passed',counts=got,callset_path=str(calls),callset_sha256=sha(calls),
                           reference_path=str(reference),reference_sha256=sha(reference)))
    write_json(out/'validation/figures_124_tilgner_rescore.json',dict(status='passed',
               normalization='first whitespace/comma token; remove terminal -1 only',checks=checks))
    # Recompute the three explicitly reconstructed ScMix rows from selected sources.
    sources = {
        'RAD': base/'scratch_preservation_20260921/files/rad_scmix2_20260726/results/fixed_scmix2_scanwl_e03_t24_full_20260726/cases/01_full/output/scanwl.txt',
        'BLAZE': base/'blaze_single_cell_expect_sweep_20260810/exploratory/scmixology2/callsets/expect500_whitelist.txt',
        'Flexiplex': base/'wl_scan/20260804_common_count_selector_ablation/full37/selector_membership.tsv.gz',
        'truth': Path('/scratch/f005f43/blaze_analysis_data_20335203/data/scmixology/cellranger/whitelist.tsv'),
        'RDS': base/'reviewer_response_20260804/objects/other_streams/objects/scmixology2_performance.rds',
    }
    truth=barcodes(sources['truth'])
    calls={'RAD':barcodes(sources['RAD']),'BLAZE':barcodes(sources['BLAZE'])}
    with gzip.open(sources['Flexiplex'],'rt') as f:
        calls['Flexiplex']={r['barcode'].removesuffix('-1') for r in csv.DictReader(f,delimiter='\t')
            if r['dataset']=='scMixology2' and r['method']=='Flexiplex' and r['mode']=='exact_flexiplex_filter_v1.02.6'}
    expression='x <- readRDS('+json.dumps(str(sources['RDS']))+'); cat(x$selected_barcodes, sep="\\n")'
    rds=subprocess.run(['Rscript','-e',expression],check=True,capture_output=True,text=True)
    assert calls['RAD']=={x.strip().removesuffix('-1') for x in rds.stdout.splitlines() if x.strip()}
    scmix=[]
    for tool,c in calls.items():
        tp,fp,fn=len(c&truth),len(c-truth),len(truth-c)
        got={'calls':len(c),'reference_n':len(truth),'tp':tp,'fp':fp,'fn':fn,
             'precision':tp/(tp+fp),'recall':tp/(tp+fn),'f1':2*tp/(2*tp+fp+fn)}
        expected=current[('ScMixology2',tool)]
        for key,value in got.items():
            if abs(value-float(expected[key]))>1e-9:raise ValueError(('ScMixology2 rescore differs',tool,key))
        scmix.append(dict(tool=tool,**got))
    write_json(out/'validation/figures_124_scmix_rescore.json',dict(status='passed',source_rows=scmix,raw_rerun=False,
               builder_path=str(Path(__file__)),builder_sha256=sha(Path(__file__)),
               sources=[dict(role=k,path=str(v),sha256=sha(v)) for k,v in sources.items()],
               Rscript_version=subprocess.run(['Rscript','--version'],capture_output=True,text=True,check=True).stdout.strip()))
    # Publish the current validation result, without publishing superseded master rows.
    for result in (dest/'validation').iterdir():
        if result.is_file():shutil.copy2(result,out/'validation'/('figures_124_native_'+result.name))
    print(f'Recovered {len(mapping)} mapped artifacts; rescored 30 Tilgner callset/reference pairs; {len(missing)} missing Visium original callsets explicit.')


if __name__=='__main__':main()
