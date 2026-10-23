#!/usr/bin/env python3
"""Resolve Figure 3 producer/reference metadata without modifying source assets."""
import argparse
import collections
import csv
import gzip
import json
from pathlib import Path
import re
import subprocess
from figure_3 import ROOT, ARMS, TOOLS, PACKAGES, sha, read, write, js

def main():
    p=argparse.ArgumentParser();p.add_argument('--project-root',type=Path,required=True);a=p.parse_args();b=a.project_root
    latest=b/'scratch_preservation_20260921/files/longbench_rad_4acbe00_raw_prism_20260827'
    competitor=b/'LongBench_comps/full_A_to_B_audit_20260731'
    assets=[];arms=[];checks=[]
    def inspect(path,role,hash_content=False):
        path=Path(path);exists=path.is_file()
        r=dict(path=str(path),role=role,status='verified_content' if exists and hash_content else 'present_metadata_only' if exists else 'missing_at_checked_path',bytes=path.stat().st_size if exists else '',sha256=sha(path) if exists and hash_content else '',symlink_target=str(path.resolve()) if path.is_symlink() else '')
        assets.append(r);return r
    catalog=inspect(latest/'inputs/common/3M-february-2018-3v3.txt','chemistry_catalog',True)
    rad_binary=inspect(latest/'tools/rad_4acbe00','RAD_4acbe00_binary',True)
    for d in ARMS:
        cell=inspect(competitor/'references/cellranger_filtered'/('ill_sc_barcodes.tsv.gz' if d.startswith('SC') else 'ill_sn_barcodes.tsv.gz'),'matched_filtered_reference',True)
        for t in TOOLS:
            name={'RAD':'rad','BLAZE':'blaze','Flexiplex':'flex_v1026'}[t]
            checkpoint=latest/'runs'/d/'audit_raw_all_fast_exact' if t=='RAD' else competitor/'results/arms'/name/d
            s=inspect(checkpoint/'per_target.tsv','C5_per_target',True)
            if t=='RAD':
                selected=latest/'inputs'/d/'custom_whitelist.txt'
                stream=Path('/scratch-nfs/f005f43/longbench_rad_4acbe00_raw_prism_20260827/runs')/d/'demux'/f'{d}_RAD.fq.gz'
                meta=latest/'runs'/d/'audit_raw_all_fast_exact/fast_run_metadata.tsv'
            elif t=='BLAZE':
                selected=competitor/'provenance/selected_whitelists/blaze'/d/'whitelist.csv'
                stream=Path('/scratch-nfs/f005f43/longbench_full_demux_20260730/runs/blaze2_2.5.0_longbench_published')/d/'matched_reads.fastq'
                meta=competitor/'provenance/producers'/name/d/'run_metadata.txt'
                inspect(stream.parent/'putative_bc.csv','BLAZE_raw_extraction',False)
            else:
                selected=next((competitor/'provenance/selected_whitelists'/name/d).glob('*.txt'))
                stream=Path('/scratch/f005f43/longbench_full_ab_audit_20260730/flexiplex_v1026_current_diagnostic')/d/f'{d}_flexiplex_v1026_audit_reads_barcodes.txt.gz'
                meta=competitor/'provenance/producers'/name/d/'run_metadata.txt'
            w=inspect(selected,'tool_selected_whitelist',True);producer=inspect(meta,'producer_metadata',True);st=inspect(stream,'full_C2_assignment_stream',False)
            targets={r['target_barcode'] for r in read(checkpoint/'per_target.tsv')}
            selected_targets=set(re.findall(r'\b[ACGT]{16}\b',selected.read_text()))
            checks.append(dict(check_id=f'{d}/{t}/selected_target_identity',status='passed' if targets==selected_targets else 'failed',observed=len(targets),expected=len(selected_targets),missing=sorted(selected_targets-targets),extra=sorted(targets-selected_targets)))
            arms.append(dict(dataset=d,tool=t,version='4acbe004ba11b150d6832395452632f367a6e6c1' if t=='RAD' else '2.5.0' if t=='BLAZE' else '1.02.6 diagnostic',binary_sha256=rad_binary['sha256'] if t=='RAD' else '38dccd37f1747e5105b62eacde572b7e4c5206fb925dc1fdbe8210ffe8b1e8c4' if t=='Flexiplex' else '',producer_metadata_sha256=producer['sha256'],selected_sha256=w['sha256'],catalog_sha256=catalog['sha256'],reference_sha256=cell['sha256'],checkpoint_sha256=s['sha256'],full_assignments_status=st['status'],full_assignments_checked_path=st['path'],CT_scope='all emitted CT records included' if t=='RAD' else 'tool-native records',hash_seed='UNSET (retained execution)' if t=='BLAZE' else 'not applicable',resume_level='C5 verified',pair_ledger_status='blocked-missing-asset' if st['status']=='missing_at_checked_path' else 'not yet reprocessed'))
    inspect('/scratch/f005f43/longbench_sc_ont_false_whitelist_20260813/fastq/SC_ONT_10M_seqkit_seed2026081326.fastq.gz','exact_10M_offlist_input_metadata_recovered',False)
    inspect(b/'wl_scan/20260731_sctagger_badread_quality_full/inputs/L/flatQ20.fq.gz','ScTagger_flatQ20_input',False)
    for dataset,package in PACKAGES.items():
        base=b/package
        for path in sorted((base/'scripts').glob('*')):
            if path.is_file():inspect(path,'retained_executed_script',True)
        for path in sorted((base/'runs').glob('*/rep*/run_metadata.tsv')):inspect(path,'offlist_producer_metadata',True)
    write(ROOT/'manifests/figure_3_arms.tsv',arms);write(ROOT/'manifests/figure_3_recovery.tsv',assets)
    js(ROOT/'validation/figure_3_reference_identity.json',dict(status='passed' if all(c['status']=='passed' for c in checks) else 'failed',checks=checks,scope='actual selected target lists compared with all twelve retained per-target tables',source_asset_hashes='manifests/figure_3_recovery.tsv'))
    if any(c['status']!='passed' for c in checks):raise SystemExit('selected target identities do not agree')
    print(json.dumps({'status':'passed','arm_count':len(arms),'assets_checked':len(assets)}))
if __name__=='__main__':main()
