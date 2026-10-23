#!/usr/bin/env python3
"""Freeze evidence for the selected current Figure3 analysis after full checks."""
import json,subprocess
from pathlib import Path
from figure_3 import ROOT,sha,js,write

def stage_audit_manifest(rage):
    """Index current audit evidence without raw producers or the separate ID archive."""
    paths=[rage/'experiment.json',rage/'input_validation.json']
    paths += [p for p in (rage/'counts').glob('*') if p.is_file() and p.name!='input_original_ids.txt.gz']
    paths += [rage/'inputs'/name for name in ['false_rep1.txt','false_rep2.txt','false_rep3.txt','whitelist_manifest.tsv','rage_3v2_umi10_layout.csv','chemistry_3v2_catalog_bitlist.csv.gz']]
    paths += [p for p in (rage/'runs').glob('*/rep*/*') if p.is_file() and (p.suffix=='.log' or p.name=='run_manifest.json')]
    paths += [p for p in (rage/'execution_code').glob('*') if p.is_file()]
    rows=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(set(paths))]
    write(ROOT/'manifests/figure_03_staged_checkpoints.tsv',rows)
    return rows

def main():
    validation=ROOT/'validation';checkpoint=ROOT/'checkpoints/figure_03/offlist_recount';rage=ROOT/'checkpoints/figure_03/rage_matched'
    recount=json.loads((checkpoint/'validation.json').read_text());parity=json.loads((validation/'figure_3_flexparity.json').read_text());current=json.loads((rage/'counts/validation.json').read_text());resume=json.loads((validation/'figure_3_resume.json').read_text())
    assert recount['status']=='passed' and len(recount['runs'])==18
    assert parity['status']=='passed' and current['status']=='passed' and len(current['runs'])==9 and resume['status']=='passed'
    staged=stage_audit_manifest(rage)
    repository_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    code_identity=('repository_base_commit identifies the checkout base, not a claim that the selected scripts exist in that commit. '
                   'local_code_sha256 identifies the actual working-tree files at this evidence freeze, including uncommitted changes. '
                   'selected_execution_source_sha256 separately identifies the exact source snapshots used by the selected input, producer and count jobs; their receipts record executed code hashes.')
    code={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'scripts/revision').glob('figure_3*') if p.is_file()}
    execution_sources={str(p.relative_to(ROOT)):sha(p) for p in (rage/'execution_code').glob('*') if p.is_file()}
    for name,digest in current['executed_code_sha256'].items():
        assert execution_sources[str((rage/'execution_code'/name).relative_to(ROOT))]==digest
    paths=[p for p in checkpoint.glob('*') if p.is_file()]+[p for p in (rage/'counts').glob('*') if p.is_file()]+list((rage/'runs').glob('*/rep*/run_manifest.json'))
    checkpoints={str(p.relative_to(ROOT)):sha(p) for p in paths}
    reports={str(p.relative_to(ROOT)):sha(p) for p in validation.glob('figure_3*.json') if p.is_file() and p.name!='figure_3_final_evidence.json'}
    source={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'source_data/figure_03').glob('*') if p.is_file()}
    outputs={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'figures/figure_03').glob('*') if p.is_file()}
    commands={
      'inventory':'python3 scripts/revision/figure_3_inventory.py --project-root /path/to/reviewer_comment_data',
      'parameters':'python3 scripts/revision/figure_3_parameters.py',
      'build':'python3 scripts/revision/figure_3.py build --project-root /path/to/reviewer_comment_data',
      'render':'python3 scripts/revision/figure_3.py render',
      'validate':'python3 scripts/revision/figure_3.py validate',
      'fixture':'python3 scripts/revision/figure_3_count.py fixture',
      'retained_recount':'python3 scripts/revision/figure_3_count.py offlist --project-root /path/to/reviewer_comment_data --output checkpoints/figure_03/offlist_recount',
      'retained_flex_parity':'python3 scripts/revision/figure_3_count.py flex-parity --project-root /path/to/reviewer_comment_data --output validation/figure_3_flexparity.json',
      'rage_prepare':'python3 scripts/revision/figure_3_rage_prepare.py --input RAW --reference FILTERED_BARCODES_GZ --catalog CATALOG --rad-source SOURCE --rad-binary RAD --blaze-python PYTHON --blaze-entrypoint BLAZE --flex-binary FLEX',
      'rage_input':'python3 scripts/revision/figure_3_rage_preflight.py',
      'rage_producer':'python3 scripts/revision/figure_3_rage_run.py TOOL REPLICATE (RAD/BLAZE/Flexiplex by1/2/3)',
      'rage_count':'python3 scripts/revision/figure_3_rage_count.py',
      'human_example':'python3 scripts/revision/figure_3_example_count.py data/examples/figure_03/sctagger_rad_rep1_assignments.tsv data/examples/figure_03/sctagger_rad_rep1_targets.txt /tmp/sc_counts.tsv'}
    tasks=[
      ('F3-01','passed','Selected measured definitions and common strict physical-read metric deposited. B compares strict assigned/input physical reads; raw totals remain a diagnostic companion. Author authorized matched RAGE replication and preservation of existing statistics.','None for data definitions'),
      ('F3-02','passed','Full ERR3268991 raw identity, FASTQ structure, unique physical-ID universe,4505-reference and737280-catalog identities validated for the selected current replication.','None for selected input provenance'),
      ('F3-03','passed','Pinned RAD source rebuilt without modification; all119 source files match git archive. BLAZE2.6.0a0 nine source modules match pin; dependency lock supplied. Exact diagnostic Flex source/patch/binary vendored. Every argv and output hash saved.','Retained D-G BLAZE2.5.0 execution receipt lacks an executable hash; recovered source is separately identified'),
      ('F3-04','passed','All18 retained C2 recounts match every target; six complete Flex sidecar/FASTQ comparisons pass. Current RAGE adds nine full raw-to-count validations and identity-bearing ledgers.','None for selected off-list counts'),
      ('F3-05','passed','All nine authorized matched RAGE raw runs completed. Three4505-target lists share exact input/list bytes across tools. Full physical-ID conservation and source output hashes pass.','None for selected RAGE counts'),
      ('F3-06','blocked-missing-asset','All12 retained full C5 correction checkpoints and actual selected/reference lists hashed and validated, preserving all-record RAD4acbe00 scope.','Full D-G assignment streams, BLAZE raw extraction and Flex diagnostic streams are missing at recorded paths'),
      ('F3-07','blocked-missing-asset','All12 correction marginals reproduce selected totals; source-to-category definitions and pair/overlap semantics have hand-computable fixtures. Identity-based target outer join and correct O denominators deposited.','Full D-G source-bearing pair ledger required to reconstruct intersections; aggregates cannot supply pair overlaps'),
      ('F3-08','changed-result-review','Current source tables and B-G scripted data proofs rebuilt. Native table-update instructions contain only selected current values. Existing test/annotation choices unchanged.','Native Prism table binding/recalculation/export and publication-size annotated artwork inspection'),
      ('F3-09','blocked-missing-asset','Human walkthrough includes actual raw/assignment data, identity-closed excerpts, explicit small scripts and outputs, per-analysis tool parameters, full replay commands and source/checkpoint hashes.','Full D-G pair-source recovery and native annotated artwork QA remain incomplete')]
    records=[dict(task_id=t,status=s,evidence=e,next_dependency=n,repository_base_commit=repository_base_commit,code_identity=code_identity,code_hashes='validation/figure_3_final_evidence.json',commands=commands,validation_evidence=list(reports),checkpoint_hashes='manifests/figure_3_checkpoint_files.tsv',author_decisions='Matched RAGE authorized; preserve existing statistics; selected current material only',unresolved_decisions=[]) for t,s,e,n in tasks]
    js(ROOT/'manifests/figure_3_tasks.json',records)
    js(validation/'figure_3_final_evidence.json',dict(repository_base_commit=repository_base_commit,code_identity=code_identity,local_code_sha256=code,selected_execution_source_sha256=execution_sources,checkpoint_sha256=checkpoints,source_data_sha256=source,figure_sha256=outputs,validation_sha256=reports,commands=commands,jobs=dict(retained_recount='9976797',retained_flex_parity='9976832',rage_preflight='9977113',rage_build='9977114',rage_pilot='9977156',rage_input_ids='9978042',rage_full_array='9977160',rage_count='9977234'),scope='Selected matched RAGE raw replay, retained C2/C5 validation, current C6 source data and scripted data proofs',native_prism='pending recalculation/export and final annotated artwork QA; preserve existing statistical choices',source_originals='read-only throughout'))
    write(ROOT/'manifests/figure_3_checkpoint_files.tsv',[dict(path=p,sha256=h,role='Selected current C2/C5 identity-bearing checkpoint or producer receipt; large artifact excluded from Git') for p,h in checkpoints.items()])
    print(json.dumps({'status':'evidence_frozen','tasks':len(records),'checkpoint_files':len(checkpoints),'audit_archive_files':len(staged),'audit_archive_bytes':sum(r['bytes'] for r in staged),'remaining':'Full D-G source pair-ledgers and native annotated artwork QA'}))
if __name__=='__main__':main()
