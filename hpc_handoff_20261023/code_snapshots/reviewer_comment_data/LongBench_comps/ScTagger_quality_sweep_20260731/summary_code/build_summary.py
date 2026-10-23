#!/usr/bin/env python3
import csv,hashlib,io,json,pathlib,shutil
r=pathlib.Path('/scratch/f005f43/sctagger_quality_sweep_summary_20260912')
c=pathlib.Path('/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731')
prov=pathlib.Path('/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/081226_Figure_2_CMV_V14_Q20p18_20260912_provenance')
out=r/'canonical'
def read_tsv(p):
 with p.open(newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def write_table(path,rows,fields,delimiter='\t'):
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,delimiter=delimiter,lineterminator='\n');w.writeheader();w.writerows(rows)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
metrics=read_tsv(c/'callset_metrics.tsv');qualities=read_tsv(c/'quality_conditions.tsv')
q={(x['dataset'],x['quality_tag']):x for x in qualities}
assert len(metrics)==96 and len(q)==24
order=['flatQ20']+[f'shift_p{i:02d}' for i in [1,2,3,4,5,6,8,10,11,12,13]]
tools=['RAD','BLAZE','Flexiplex_f0','Flexiplex_f8']
expected={(d,t,k) for d in ['S','L'] for t in order for k in tools}
assert {(m['dataset'],m['quality_tag'],m['tool']) for m in metrics}==expected
joined=[]
for m in metrics:
 tp,fp,fn=[int(m[k]) for k in ['tp','fp','fn']]
 assert int(m['calls'])==tp+fp
 assert tp+fn=={'S':50,'L':5000}[m['dataset']]
 assert abs(float(m['f1'])-2*tp/(2*tp+fp+fn))<1e-11
 for k,val in [('precision',tp/(tp+fp)),('recall',tp/(tp+fn))]:assert abs(float(m[k])-val)<1e-11
 v=q[m['dataset'],m['quality_tag']]
 row={k:m[k] for k in ['dataset','quality_tag','tool','calls','tp','fp','fn','precision','recall','f1']}
 row.update({k:v[k] for k in ['quality_model','phred_shift','seed','reads','mean_all_base_q','mean_barcode_base_q','min_all_base_q','max_all_base_q','located_barcodes','pass_minQ15','pass_fraction']})
 row['input']=m['input'];joined.append(row)
fields=list(joined[0]);write_table(out/'ALL_TOOLS_SWEEP_WITH_QUALITY.tsv',joined,fields)
blaze=[x for x in joined if x['tool']=='BLAZE']
write_table(out/'BLAZE_SWEEP_ALL_METRICS.tsv',blaze,fields)
write_table(out/'BLAZE_SWEEP_ALL_METRICS.csv',blaze,fields,',')
indexed={(x['dataset'],x['quality_tag']):x for x in blaze}
wide=[]
for tag in order:
 l,s=[indexed[d,tag] for d in ['L','S']]
 wide.append({'quality_tag':tag,'quality_model':l['quality_model'],'phred_shift':l['phred_shift'],
              'mean_q_L':l['mean_all_base_q'],'mean_q_S':s['mean_all_base_q'],
              'BLAZE_f1_L':l['f1'],'BLAZE_f1_S':s['f1'],
              'L_tp':l['tp'],'L_fp':l['fp'],'L_fn':l['fn'],
              'S_tp':s['tp'],'S_fp':s['fp'],'S_fn':s['fn']})
write_table(out/'BLAZE_F1_SWEEP.tsv',wide,list(wide[0]))
lines=['| Condition | Mean Q, L / S | BLAZE F1, L | BLAZE F1, S | L TP | L FP | L FN |',
       '|---|---:|---:|---:|---:|---:|---:|']
short=['| Mean Q, L / S | BLAZE F1, L | BLAZE F1, S |','|---|---:|---:|']
for row in wide:
 tag=row['quality_tag'];label='Original flat Q20' if tag=='flatQ20' else '+'+row['phred_shift']
 means='20.00 / 20.00 (flat)' if tag=='flatQ20' else f"{float(row['mean_q_L']):.2f} / {float(row['mean_q_S']):.2f}"
 lines.append(f"| {label} | {means} | {float(row['BLAZE_f1_L']):.6f} | {float(row['BLAZE_f1_S']):.6f} | {row['L_tp']} | {row['L_fp']} | {row['L_fn']} |")
 short.append(f"| {means} | {float(row['BLAZE_f1_L']):.6f} | {float(row['BLAZE_f1_S']):.6f} |")
table='\n'.join(lines);short_table='\n'.join(short)
(r/'answer_table.md').write_text(short_table+'\n')
script=c/'code/original_quality_generation/generate_truth_conditioned_qscores.py'
report=f'''# ScTagger quality sweep: complete results and Figure 2 follow-through

Updated 2026-09-12. This is the current truth-conditioned **Badread nanopore2018 S/L quality sweep**. It records the complete whitelist sweep and the later flat-Q20 versus Q20.18 read-assignment/Prism follow-through. It does not replace the older marginal-quality pilot report or merge in the separate nanopore2023 and expected-cell-setting experiments.

## What was generated and run

The input datasets are ScTagger-S (98,873 reads; 50 true cell barcodes) and ScTagger-L (4,993,805 reads; 5,000 true cell barcodes). All nucleotide sequences and read IDs remain fixed across quality conditions.

The generator samples background qualities with probability-weighted draws from the Badread `nanopore2018` overall score distribution into a reusable quality tape. A deterministic read-specific offset selects each read's background qualities. It locates the barcode using the adapter/layout and truth barcode encoded in the simulated read ID, then calls Badread's stock `QScoreModel`/`get_qscores` on the observed and true 16-base barcode. Those stock routines condition quality draws on local matching/error patterns. The custom wrapper replaces the located barcode's background scores with the conditional scores and handles orientation. Locations not found or conditional failures retain the sampled background qualities; the original generation summaries record these counts.

The custom code controls the truth-aware barcode locator, background tape, deterministic seeds (S20260727, L20260731), quality substitution and output variants. It reuses Badread's model and conditional quality-sampling routines; it does not regenerate or mutate the simulated nucleotide sequences. The same sampled quality string underlies every shifted version of a read. Whole-read shifts +1,+2,+3,+4,+5,+6,+8,+10,+11,+12,+13 are applied, clipped to Phred1..50. The original uniform-Q20 FASTQ is a separate control. These are paired score shifts, not 11 independently generated sequencing-error replicates.

Each of 24 dataset/quality combinations was processed with RAD, BLAZE, Flexiplex_f0 and Flexiplex_f8: **96 complete whitelist results**. BLAZE used `--expect-cells 50` for S or5000 for L, chemistry3v3, minQ15, no empty-drop testing and no demultiplexing in the original sweep. Native BLAZE's quality gate is applied to barcode observations used for whitelist selection. The truth-located `pass_minQ15` diagnostic in `quality_conditions.tsv` is not the count of BLAZE-selected cells and can use a different barcode window from BLAZE's extractor.

This tests sensitivity of whitelist selection to assigned confidence values on fixed erroneous sequences. It does not establish performance across newly simulated nucleotide-error rates or independent biological datasets.

## Entire-sweep BLAZE F1

These are **cell-barcode discovery / whitelist F1 scores**, computed as `2TP/(2TP+FP+FN)`. They are not read-assignment F1, nor the fraction of reads correctly assigned. L has5000 truth barcodes; S has50. All mean quality values below are arithmetic means of per-base Phred scores. The short Q20.18 label refers to L; S's +6 mean is20.187683390810697, which rounds to20.19.

{table}

The maximum observed L F1 among the tested conditions is **0.991375037177 at +6 (meanQ20.181087743552993)**, with5000TP,87FP,0FN. S reaches F1=1 at +5 and+8. Low-quality conditions lose many true barcodes; at higher qualities false barcodes enter the selected lists. The observed response is not monotonic, including the +5/+6 change in L. FlatQ20 is a uniform-score control and must not be connected into the heterogeneous series as if it were another shift.

RAD has F1=1 throughout both datasets. Flexiplex_f0 is invariant at0.423728813559 for S and0.563570784491 for L; Flexiplex_f8 is invariant at1 for S and0.750624687656 for L.

[Curve (PNG)](BLAZE_F1_SWEEP.png) · [Curve (PDF)](BLAZE_F1_SWEEP.pdf) · [F1 summary TSV](BLAZE_F1_SWEEP.tsv) · [All BLAZE metrics TSV](BLAZE_SWEEP_ALL_METRICS.tsv) · [All96 results with quality metadata](ALL_TOOLS_SWEEP_WITH_QUALITY.tsv).

## Read-assignment follow-through completed on 2026-09-12

**Read-level assignments were reconstructed for L flatQ20 and L+6 only. There is no completed read-assignment matrix across every quality shift in this package.** The original full sweep deliberately used BLAZE `--no-demultiplexing`, so its F1 table alone cannot answer how many reads are misassigned at every quality condition.

For the Figure2 update, the archived stock BLAZE2.6.0a0 row matcher was applied to the complete saved extraction table with the paired old5607 and new5087 selected lists, ED2 and native demultiplexing minQ0. The final replay pins Python3.9/PYTHONHASHSEED0 and archives actual whitelist iteration order. No transcript FASTQ was emitted. Every non-quality extraction field matches across all4,993,805 reads. A separate full comparison also matches all fields and row order against the August17 flat control extraction table. An independent scorer confirmed that the original reverse-complement-equivalent classification and strict orientation classify every assigned read identically.

| Disjoint read category | FlatQ20 paired control | Q20.18 (+6) |
|---|---:|---:|
| Native correct |640957|640957|
| Corrected correct |1810128|1871785|
| Native incorrect |7526|1392|
| Corrected incorrect |153636|135358|
| Unassigned |2381558|2344313|
| Input total |4993805|4993805|

Q20.18's135358 incorrect corrections comprise130922 reads sent to another true cell barcode and4436 sent to false whitelist barcodes. Another1392 native-incorrect reads were accepted without correction; total wrongly assigned=136750. Incorrect corrections represent6.7438% of corrected reads. All assignments to false whitelist targets total5247=4436corrected+811native; this overlapping diagnostic must not be added as an extra category to a pie of the disjoint states.

This explains why a whitelist F1 of0.991375 can coexist with135K incorrectly corrected reads: whitelist selection accuracy and read-to-cell assignment accuracy are different quantities. BLAZE's minQ15 whitelist gate is not reapplied by default as a per-read demultiplexing threshold. Most remaining bad corrections go to other real cells.

The paired flat reconstruction is not numerically identical to the original manuscript totals: corrected-correct is+289, corrected-incorrect -46 and false-target assignments -102, while native totals match. An additional random-hash replay differs as well. The stock matcher iterates a set and its tie handling is sensitive to that order. The pinned replay and actual orders make the present results traceable; do not falsely attribute the flat-control drift to the quality treatment.

## Figure2 outcome and remaining Prism step

Updated project: [`081226_Figure_2_CMV_V14_Q20p18_20260912.prism`](/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/081226_Figure_2_CMV_V14_Q20p18_20260912.prism). Its [detailed provenance summary]({prov}/README.md) contains the full read metrics and change log.

Every affected used data table/copy, saved transpose, and typed graph label was updated; Figure2H now has87 BLAZE FP observations. The BLAZE pie was corrected to disjoint categories. Quality-independent RAD/Flexiplex and supplied-list BLAZE counts were retained with source and sequence invariance evidence. LongBench/RAGE-seq content is unchanged. The user explicitly excluded unused M/size/downsampling panels, which remain historical flat-Q20 data. The original V14 project remains unchanged.

Four affected statistical analyses (Hdescriptives, IRM-ANOVA, JRM-ANOVA, Jmixed-effects) have old results cleared and are marked for recalculation in Prism; the previously interrupted Imixed-effects analysis remains pending. No new p-values were generated here. Both structural validators, an independent audit of all29 tables, and a complete graph-label audit passed. Prism GUI rendering and statistics were not run.

## Provenance and tabulated data

- Immutable original complete metrics: [callset_metrics.tsv](callset_metrics.tsv), [CSV](callset_metrics.csv), [terminal summary](callset_metrics_terminal.tsv), [TP/FP/FN wide table](callset_tp_fp_fn_wide.tsv).
- Quality metadata: [quality_conditions.tsv](quality_conditions.tsv); definitions: [QUALITY_LABELS.md](QUALITY_LABELS.md).
- Original generator and executed commands: [code archive](code/README.md), [source manifest](code/SOURCE_MANIFEST.tsv). Generator: `code/original_quality_generation/generate_truth_conditioned_qscores.py`; runner: `code/original_three_tool_sweep/run_case.sh`; scorer: `summarize_callsets.py` in the same directory.
- Original working directory: `/scratch/f005f43/sctagger_sl_three_tool_quality_20260731`; original FASTQ inputs include `/scratch-nfs/f005f43/rad_longbench_20260726/data/`. The durable archive preserves scripts whose historical absolute paths may no longer all exist.
- Final read-level replay: `/scratch-nfs/f005f43/sctagger_q20p18_prism_update_20260912/blaze_native_replay_seed0`; copied metrics/scoring/code are in the Figure2 provenance directory linked above.
- Separate experiments: `../ScTagger_nanopore2023_Q15_Q20_20260819/`, the earlier `wl_scan/20260731_sctagger_badread_quality_full/` marginal pilot, and `blaze_single_cell_expect_sweep_20260810`. Their results are not mixed into this96-row sweep.

`summary_validation_20260912.json` records input hashes and recomputation checks. `SUMMARY_ADDITIONS_SHA256SUMS.txt` checks the new summary/exports/curve without replacing original experiment checksum manifests. No simulation or pipeline jobs were rerun for this summary update.
'''
(out/'SWEEP_SUMMARY.md').write_text(report)
# Preserve before-images of the two existing summaries and their checksum lists.
for label,path in [('QUALITY_LABELS.md',c/'QUALITY_LABELS.md'),('ADDED_METRICS_SHA256SUMS.txt',c/'ADDED_METRICS_SHA256SUMS.txt'),('Prism_README.md',prov/'README.md'),('Prism_SHA256SUMS',prov/'SHA256SUMS')]:
 shutil.copy2(path,r/'source_snapshot'/label)
quality=(c/'QUALITY_LABELS.md').read_text().split('\n## Complete results and follow-through')[0]
quality+='\n## Complete results and follow-through\n\nSee [SWEEP_SUMMARY.md](SWEEP_SUMMARY.md) for all96 whitelist results, BLAZE F1 across every quality condition, and the completed flat-Q20 versus Q20.18 read-assignment/Prism follow-through. The complete whitelist sweep and the two-condition read-level follow-up are distinguished explicitly.\n'
(out/'QUALITY_LABELS.md').write_text(quality)
old=(c/'ADDED_METRICS_SHA256SUMS.txt').read_text().splitlines()
updated=[]
for line in old:
 digest,name=line.split('  ',1)
 if name=='QUALITY_LABELS.md':digest=sha(out/'QUALITY_LABELS.md')
 updated.append(digest+'  '+name)
(out/'ADDED_METRICS_SHA256SUMS.txt').write_text('\n'.join(updated)+'\n')
append=f'''\n## Complete quality sweep: results recorded 2026-09-12\n\nThe [full sweep summary]({c}/SWEEP_SUMMARY.md) now records generation, every quality condition, tool settings, and the read-assignment/Prism follow-through. [All96 whitelist results with quality metadata]({c}/ALL_TOOLS_SWEEP_WITH_QUALITY.tsv) and [all24 BLAZE results]({c}/BLAZE_SWEEP_ALL_METRICS.tsv) are tabulated.\n\nThe following scores are **whitelist/cell-discovery F1**, not read-assignment accuracy. L has5000 true cells; S has50. Full read-assignment metrics are available for LflatQ20 and L+6, as described above, not every sweep condition.\n\n{short_table}\n\nL's highest observed F1 is0.991375037177 at +6/meanQ20.1811; S reaches1 at +5 and+8. The original flatQ20 control is separate from the heterogeneous quality series.\n'''
readme=(prov/'README.md').read_text().split('\n## Complete quality sweep: results recorded')[0]+append
(r/'prism_provenance/README.md').write_text(readme)
manifest=[]
for line in (prov/'SHA256SUMS').read_text().splitlines():
 digest,name=line.split('  ',1)
 if name=='README.md':digest=sha(r/'prism_provenance/README.md')
 manifest.append(digest+'  '+name)
(r/'prism_provenance/SHA256SUMS').write_text('\n'.join(manifest)+'\n')
validation={'date':'2026-09-12','input_hashes':{str(c/n):sha(c/n) for n in ['callset_metrics.tsv','quality_conditions.tsv']},'unique_complete_combinations':len(expected),'quality_records':len(q),'BLAZE_rows':len(blaze),'all_f1_precision_recall_recomputed':'PASS','model':'nanopore2018 truth-conditioned','read_assignment_scope':'L flatQ20 and shift_p06 only','source_original_metrics_unchanged':True}
(out/'summary_validation_20260912.json').write_text(json.dumps(validation,indent=2)+'\n')
print(short_table)
print('Validated96metrics; wrotejoinedexports,summaryandupdatedsummarylinks')
