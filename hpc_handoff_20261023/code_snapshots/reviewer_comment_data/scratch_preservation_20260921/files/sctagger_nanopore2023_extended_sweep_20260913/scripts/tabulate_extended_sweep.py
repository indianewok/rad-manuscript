#!/usr/bin/env python3
"""Combine new BLAZE selection results with invariant and archived callsets."""
import csv
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results'
NATIVE=Path('/scratch-nfs/f005f43/sctagger_nanopore2023_unadjusted_20260913')
ARCHIVE18=Path('/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731')
TOOLS=['RAD','BLAZE','Flexiplex_f0','Flexiplex_f8']


def read_table(path):
    with path.open(newline='') as f:return list(csv.DictReader(f,delimiter='\t'))


def write_table(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n')
        w.writeheader();w.writerows(rows)


def metrics(tp,fp,fn):
    return dict(calls=tp+fp,tp=tp,fp=fp,fn=fn,precision=tp/(tp+fp) if tp+fp else 0,
                recall=tp/(tp+fn) if tp+fn else 0,f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0)


def main():
    assert (ROOT/'blaze_replay/DONE').exists()
    nv=json.loads((ROOT/'blaze_replay/native_validation.json').read_text())
    assert nv['passed'] and nv['byte_identical_whitelist'] and nv['other_validation_controls_run']==[]
    replay=read_table(ROOT/'blaze_replay/results.tsv')
    assert len(replay)==12
    quality=read_table(ROOT/'quality/quality_summary.tsv')
    qmap={(r['model'],int(r['shift'])):r for r in quality}
    matching=read_table(ROOT/'quality/matched_quality_levels.tsv')
    old=[r for r in read_table(ARCHIVE18/'ALL_TOOLS_SWEEP_WITH_QUALITY.tsv') if r['dataset']=='L']
    native=read_table(NATIVE/'results/native_whitelist_metrics.tsv')
    invariant={r['tool']:r for r in native if r['tool']!='BLAZE'}
    truth=set((NATIVE/'metadata/L_truth_barcodes.txt').read_text().splitlines())
    assert len(truth)==5000
    callsets={
        'RAD':NATIVE/'runs/L/nanopore2023_native_unadjusted/rad/scanwl.txt',
        'Flexiplex_f0':NATIVE/'runs/L/nanopore2023_native_unadjusted/flex_f0/selected.txt',
        'Flexiplex_f8':NATIVE/'runs/L/nanopore2023_native_unadjusted/flex_f8/selected.txt'}
    audits=[]
    for tool,path in callsets.items():
        selected={line.strip().split()[0] for line in path.read_text().splitlines() if line.strip()}
        m=metrics(len(selected&truth),len(selected-truth),len(truth-selected))
        assert all(m[k]==int(invariant[tool][k]) for k in ['calls','tp','fp','fn'])
        audits.append(dict(tool=tool,condition='invariant_source',source=str(path),**m))
    for r in replay:
        path=Path(r['whitelist_path'])
        lines=path.read_text().splitlines();selected=set(lines)
        assert len(lines)==len(selected)
        m=metrics(len(selected&truth),len(selected-truth),len(truth-selected))
        for key,sourcekey in [('calls','called_barcodes'),('tp','true_positives'),('fp','false_positives'),('fn','false_negatives')]:
            assert m[key]==int(r[sourcekey]),(r['condition'],key)
        assert abs(m['f1']-float(r['f1']))<1e-14
        assert hashlib.sha256(path.read_bytes()).hexdigest()==r['whitelist_sha256']
        audits.append(dict(tool='BLAZE',condition=r['condition'],source=str(path),**m))

    combined=[]
    def row(model,condition,shift,tool,values,whole,barcode,sd,gap,mode,source,whitelist='',blaze_readpass='',blaze_cutoff=''):
        return dict(dataset='L',quality_model=model,condition=condition,shift=shift,tool=tool,
            full_dataset_mean_Q=float(whole),full_located_barcode_mean_Q=float(barcode),
            sample_barcode_mean_Q=20.0 if model=='flatQ20' else float(qmap[(model,shift)]['sample_mean_barcode_Q']),
            sample_barcode_mean_SD=float(sd),sample_clean_error_gap=float(gap),
            **values,result_origin=mode,source_metrics=str(source),source_whitelist=str(whitelist),
            blaze_high_quality_candidate_reads=blaze_readpass,blaze_count_threshold=blaze_cutoff)
    for r in old:
        isflat=r['quality_tag']=='flatQ20'
        shift=None if isflat else int(r['phred_shift'])
        q=None if isflat else qmap[('nanopore2018',shift)]
        m=metrics(*[int(r[k]) for k in ['tp','fp','fn']])
        combined.append(row('flatQ20' if isflat else 'nanopore2018',r['quality_tag'],'' if isflat else shift,r['tool'],m,
            r['mean_all_base_q'],r['mean_barcode_base_q'],0 if isflat else q['sample_SD'],0 if isflat else q['sample_clean_error_gap'],
            'archived full FASTQ benchmark',ARCHIVE18/'ALL_TOOLS_SWEEP_WITH_QUALITY.tsv'))
    for r in replay:
        shift=int(r['nanopore2023_shift']);q=qmap[('nanopore2023',shift)]
        for tool in TOOLS:
            if tool=='BLAZE':
                m=metrics(*[int(r[k]) for k in ['true_positives','false_positives','false_negatives']])
                mode='native extraction replay; unadjusted-only validation' if shift else 'native validation replay; byte-identical whitelist'
                source=ROOT/'blaze_replay/results.tsv';wl=r['whitelist_path']
            else:
                m=metrics(*[int(invariant[tool][k]) for k in ['tp','fp','fn']])
                mode='reused invariant callset; identical underlying sequences'
                source=NATIVE/'results/native_whitelist_metrics.tsv';wl=callsets[tool]
            combined.append(row('nanopore2023',q['condition'],shift,tool,m,q['full_dataset_mean_Q'],q['full_located_barcode_mean_Q'],
                q['sample_SD'],q['sample_clean_error_gap'],mode,source,wl,
                r['high_quality_candidate_reads'] if tool=='BLAZE' else '',r['count_threshold'] if tool=='BLAZE' else ''))
    assert len(combined)==96
    new=[r for r in combined if r['quality_model']=='nanopore2023']
    assert len(new)==48
    write_table(OUT/'all_tools_both_models.tsv',combined)
    write_table(OUT/'all_tools_2023_sweep.tsv',new)
    b23=sorted([r for r in new if r['tool']=='BLAZE'],key=lambda r:r['full_dataset_mean_Q'])
    write_table(OUT/'BLAZE_2023_sweep.tsv',b23)
    pairrows=[]
    for pair in matching:
        a=next(r for r in combined if r['quality_model']=='nanopore2018' and r['shift']==int(pair['shift2018']) and r['tool']=='BLAZE')
        b=next(r for r in b23 if r['shift']==int(pair['shift2023']))
        p=dict(shift2018=a['shift'],shift2023=b['shift'],whole_mean_Q2018=a['full_dataset_mean_Q'],whole_mean_Q2023=b['full_dataset_mean_Q'])
        for key in ['tp','fp','fn','precision','recall','f1']:
            p[key+'2018']=a[key];p[key+'2023']=b[key]
        p['F1_difference2023_minus2018']=b['f1']-a['f1']
        pairrows.append(p)
    write_table(OUT/'BLAZE_2018_vs2023.tsv',pairrows)
    write_table(OUT/'callset_rescoring_audit.tsv',audits)

    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    fig,axes=plt.subplots(2,2,figsize=(12.3,8.5))
    for model,color in [('nanopore2018','#2869A6'),('nanopore2023','#C45828')]:
        subset=sorted([r for r in combined if r['quality_model']==model and r['tool']=='BLAZE' and r['shift']!=0],key=lambda r:r['full_dataset_mean_Q'])
        for ax,key,title in zip(axes.ravel(),['f1','tp','fp','fn'],['Whitelist F1','True-positive barcodes','False-positive barcodes','False-negative barcodes']):
            ax.plot([r['full_dataset_mean_Q'] for r in subset],[r[key] for r in subset],'-o',color=color,label=model)
            if model=='nanopore2023':
                native_r=next(r for r in b23 if r['shift']==0)
                ax.plot(native_r['full_dataset_mean_Q'],native_r[key],marker='*',markersize=13,color=color,linestyle='none')
            ax.set(title=title,xlabel='Achieved whole-read mean Q',ylabel=title)
            ax.grid(axis='y',alpha=.15)
    axes[0,0].set_ylim(-.02,1.03)
    axes[0,0].legend(frameon=False)
    fig.suptitle('BLAZE across the 2018 and extended 2023 quality sweeps',fontsize=15,y=.98)
    fig.text(.5,.015,'Same 4,993,805 ScTagger-L sequences. Stars: unadjusted 2023. New BLAZE callsets replay its original selection code on full saved extraction.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,.94))
    for ext in ['png','pdf']:fig.savefig(OUT/f'BLAZE_model_comparison.{ext}',dpi=180)
    plt.close(fig)

    table=['| 2023 shift | Whole-read mean Q | TP | FP | FN | F1 |','|---|---:|---:|---:|---:|---:|']
    for r in b23:
        label='Unadjusted' if r['shift']==0 else str(r['shift'])
        table.append(f"| {label} | {r['full_dataset_mean_Q']:.4f} | {r['tp']} | {r['fp']} | {r['fn']} | {r['f1']:.6f} |")
    invtable=['| Tool | TP | FP | FN | F1 |','|---|---:|---:|---:|---:|']
    for tool in ['RAD','Flexiplex_f0','Flexiplex_f8']:
        r=next(r for r in new if r['tool']==tool)
        invtable.append(f"| {tool} | {r['tp']} | {r['fp']} | {r['fn']} | {r['f1']:.6f} |")
    report='''# ScTagger-L extended nanopore2023 quality sweep

Completed 2026-09-13. Eleven 2023 score shifts now cover the quality levels
in the 2018 sweep. The full underlying 4,993,805 reads and their nucleotide
errors are unchanged. BLAZE was replayed on its full native extraction cache;
RAD and Flexiplex callsets are explicitly reused because they are quality
invariant for these fixed sequences and settings.

## BLAZE results

'''+ '\n'.join(table)+'''

These are cell-barcode discovery metrics against 5,000 truth barcodes, not
read-assignment accuracy or new sequencing-error simulations.

## Quality-invariant results reused at every condition

'''+ '\n'.join(invtable)+'''

## Matching the quality levels

For each saved 2018 shift (+1,+2,+3,+4,+5,+6,+8,+10,+11,+12,+13), the 2023
shift was chosen to minimize the difference in achieved full-dataset mean
base Q. Integer shifts were searched using the validated native full-base
histogram, applying clip(Q+shift,1,50). The selected shifts are
-17,-16,-15,-14,-12,-11,-9,-7,-6,-5,-4. Maximum mismatch is 0.373602 Q.
We report both achieved means; the conditions are approximately matched.
Barcode means are not the matching target.

Barcode distributions use the same 50,000 located reads as the Figure 2
quality tables, spanning all 5,000 truth barcodes. Scores are shifted and
clipped at the individual-base level before averaging the 16 barcode bases.
All 750,000 overlapping values from the earlier comparison were unchanged.
Native model references retain their original scores, including 2023 Q>50.

## BLAZE replay and validation

BLAZE 2.6.0a0 extracts candidate positions from sequence, then filters by
the minimum quality of the extracted barcode. For the proposed uniform
shifts and clipping to Q1..50, shifted minimum Q>=15 is exactly equivalent
to native minimum Q>=15-shift. The frozen candidate table includes all reads,
including candidates below native Q15, so the required evidence is retained.

The replay uses the original pandas counting expression and the installed
`blaze.main.get_bc_whitelist` function, with 5,000 expected cells, chemistry
3v3, default sensitivity, and no empty-drop output or demultiplexing. It
recomputes counts and the selection threshold at each quality level.

Only the unadjusted BLAZE callset was used as a replay validation control,
as requested. It reproduced all 5,015 entries byte for byte: 5,000 TP,
15 FP, 0 FN. That check passed before the shifted conditions ran. No shifted
archived BLAZE callset was used as an additional validation control.
Every new output callset was independently rescored against truth for the
combined tables. RAD and Flexiplex source callsets were also rescored.

## Files

- `results/BLAZE_2023_sweep.tsv`: all eleven shifts plus the native reference.
- `results/BLAZE_2018_vs2023.tsv`: paired BLAZE TP/FP/FN and F1 across models.
- `results/all_tools_2023_sweep.tsv`: 48 rows, with actual versus reused origins.
- `results/all_tools_both_models.tsv`: 96 rows combining 2018, 2023 and flat Q20.
- `results/BLAZE_model_comparison.png` and `.pdf`: F1, TP, FP and FN curves.
- `quality/matched_quality_levels.tsv`: exact shifts, achieved means and offsets.
- `quality/quality_summary.tsv`: full-data quality means and sample distributions.
- `quality/paired_50000_barcode_mean_Q.csv`: paired distributions, ready for import.
- `quality/matched_distribution_grid.png` and `.pdf`: all paired distributions.
- `quality/barcode_quality_trends.png` and `.pdf`: mean, SD and clean/error gaps.
- `quality/reconstructed_full_quality_histograms.tsv`: exact transformed histograms.
- `blaze_replay/conditions/`: each selected list, counts and TP/FP/FN barcode IDs.
- `blaze_replay/native_validation.json`: the requested unadjusted-only control.
- `blaze_replay/provenance/` and `scripts/`: source hashes, environment and code.

All new artifacts are under /scratch-nfs/f005f43. No full shifted FASTQs were
written, no read demultiplexing was performed, and no Prism project changed.
The completed native2023 input and benchmark directory remains read-only.
'''
    (ROOT/'README.md').write_text(report)
    (ROOT/'RESULTS.md').write_text('# Extended 2023 sweep: BLAZE barcode discovery\n\n'+'\n'.join(table)+'\n\n'+
        'RAD and Flexiplex are reused at every condition:\n\n'+'\n'.join(invtable)+'\n')
    validation=dict(status='PASS',native_only_BLAZE_validation=nv,combined_rows=len(combined),new_model_rows=len(new),
        independently_rescored_callsets=len(audits),paired_levels=len(pairrows),other_BLAZE_validation_controls=[],
        sequence_invariance_basis='All new results derive from the same frozen native extraction or existing invariant callsets; no nucleotide sequence transformation occurs.',
        combined_metrics_sha256=hashlib.sha256((OUT/'all_tools_both_models.tsv').read_bytes()).hexdigest())
    (ROOT/'provenance/combined_validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    print('\n'.join(table))
    print(json.dumps({k:v for k,v in validation.items() if k!='native_only_BLAZE_validation'},indent=2))


if __name__=='__main__':main()
