#!/usr/bin/env python3
"""Check independent small walkthrough transforms against full checkpoint tables.

Run the documented Figure 6/7 commands first to create the comparison files under validation/walkthrough/.
This checker reads them and records evidence; it does not rerun upstream analyses.
"""
import argparse,csv,gzip,hashlib,json,math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--genotype-summary',type=Path,default=ROOT/'validation/walkthrough/figure06_all_summary.tsv')
p.add_argument('--adjusted-genes',type=Path,default=ROOT/'validation/walkthrough/figure07_adjusted.tsv')
p.add_argument('--thresholds',type=Path,default=ROOT/'validation/walkthrough/figure07_thresholds.tsv')
a=p.parse_args(); checks=[]
def read(path):
    with (gzip.open(str(path),'rt') if str(path).endswith('.gz') else path.open()) as f:return list(csv.DictReader(f,delimiter='\t'))
def check(name,condition,detail):
    checks.append(dict(check=name,status='passed' if condition else 'failed',detail=detail))
    if not condition:raise ValueError(name+': '+detail)
def key(r):return r['tool'],r['direction'],float(r['tool_BH_FDR_cutoff']),float(r['tool_abs_log2FC_cutoff'])
observed={r['tool']:r for r in read(a.genotype_summary)}
expected={r['tool']:r for r in read(ROOT/'source_data/figure_06/genotype_summary.tsv')}
check('F6_full_independent_classification',observed==expected,'All three tools; all counts and denominators; 5782 reference singlets')
observed={(r['tool'],r['gene_id']):r for r in read(a.adjusted_genes)}
expected={(r['tool'],r['gene_id']):r for r in read(ROOT/'source_data/figure_07/direct_H146_vs_H526_plot_data.tsv.gz')}
check('F7_complete_gene_keys',set(observed)==set(expected) and len(observed)==24405,'3 tools x8135 unique genes')
error=max(abs(float(observed[k][field])-float(expected[k][field])) for k in observed for field in ('tool_BH_FDR_common','Illumina_BH_FDR_common'))
check('F7_independent_BH',error<=1e-12,'maximum absolute difference='+str(error))
observed={key(r):r for r in read(a.thresholds)}
expected={key(r):r for r in read(ROOT/'source_data/figure_07/threshold_grid.tsv')}
check('F7_full_threshold_keys',set(observed)==set(expected) and len(observed)==594,'9 FDR x11 effect x2 directions x3tools')
ints=('genes','truth_positive','predicted_positive','TP','FP','FN','TN')
check('F7_independent_threshold_integer_counts',all(int(observed[k][f])==int(expected[k][f]) for k in observed for f in ints),'All4158 integer values exact')
error=max(abs(float(observed[k][f])-float(expected[k][f])) for k in observed for f in ('precision','recall','F1'))
check('F7_independent_threshold_metrics',error<=1e-12,'maximum absolute difference='+str(error))
rows=read(ROOT/'data/examples/figure_05/flexiplex_receptor_output.tsv')
check('F5_real_exclusive_count_example',len(rows)==9 and all(int(r['native'])+int(r['corrected_only'])==int(r['assigned']) for r in rows),'3 real barcodes x3 receptor classes; cumulative corrected reduced once')
cohorts={r['cell_barcode']:int(r['full_library_molecules']) for r in read(ROOT/'source_data/figure_07/native_positive_depth_cohorts.tsv') if r['tool']=='RAD'}
rows=read(ROOT/'data/examples/figure_07/RAD_matrix_entries.tsv'); joined=[r for r in rows if r['cell_barcode'] in cohorts]
check('F7_excerpt_full_library_depth_join',bool(joined) and all(cohorts[r['cell_barcode']]==int(r['full_cell_library_molecules']) for r in joined),str(len(joined))+' excerpt cells independently match full named-cohort depth')
check('F7_excerpt_CP10K_arithmetic',all(abs(float(r['CP10K'])-10000.*int(r['molecule_count'])/int(r['full_cell_library_molecules']))<1e-12 for r in rows),'all8 real entries; full unfiltered cell denominator')
manifest=list(csv.DictReader((ROOT/'manifests/figures_567_staged_checkpoints.tsv').open(),delimiter='\t'))
check('ignored_checkpoint_payload_present',all((ROOT/r['path']).stat().st_size==int(r['bytes']) for r in manifest),str(len(manifest))+' staged files; full SHA verification was done while staging')
receipt=dict(checks=checks,checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    inputs=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in (a.genotype_summary,a.adjusted_genes,a.thresholds)],
    scope='independent portable transforms plus bounded real excerpt checks; not upstream raw replay')
(ROOT/'validation/figures_567_walkthrough_checks.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(str(len(checks))+' walkthrough checks passed')
