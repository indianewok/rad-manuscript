#!/usr/bin/env python3
"""Paired barcode distributions and exact histogram-derived whole-file means."""
import csv
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'quality'
NATIVE = Path('/scratch-nfs/f005f43/sctagger_nanopore2023_unadjusted_20260913')
ARCHIVE18 = Path('/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731')
EVIDENCE = Path('/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/081226_Figure_2_CMV_V14_Q20p18_sweep_20260913_provenance/quality/sample_replay_evidence.jsonl.gz')
SHIFTS18 = [1,2,3,4,5,6,8,10,11,12,13]
BLUE, ORANGE = '#2869A6', '#C45828'


def read_table(path, sep='\t'):
    with path.open(newline='') as f:
        return list(csv.DictReader(f, delimiter=sep))


def write_table(path, rows, sep='\t'):
    with path.open('w', newline='') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0]), delimiter=sep, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def main():
    OUT.mkdir(exist_ok=True)
    metadata18 = {int(r['phred_shift']):r for r in read_table(ARCHIVE18/'quality_conditions.tsv')
                  if r['dataset']=='L' and r['phred_shift']!='NA'}
    hist=read_table(NATIVE/'results/quality_distribution.tsv')
    score=np.array([int(r['q']) for r in hist])
    whole_n=np.array([int(r['whole_count']) for r in hist], dtype=np.int64)
    barcode_n=np.array([int(r['barcode_base_count']) for r in hist], dtype=np.int64)
    minimum_n=np.array([int(r['barcode_window_min_count']) for r in hist], dtype=np.int64)
    assert whole_n.sum()==8394808882 and minimum_n.sum()==4976160
    assert barcode_n.sum()==16*minimum_n.sum()
    means={s:float(np.dot(np.clip(score+s,1,50),whole_n)/whole_n.sum()) for s in range(-89,1)}
    matching=[]
    for s18 in SHIFTS18:
        target=float(metadata18[s18]['mean_all_base_q'])
        s23=min(means, key=lambda s:(abs(means[s]-target),abs(s),s))
        matching.append(dict(dataset='L', shift2018=s18, condition2018=f'shift_p{s18:02d}',
            mean_whole_Q2018=target, shift2023=s23, condition2023=f'shift_m{abs(s23):02d}',
            mean_whole_Q2023=means[s23], mean_Q_difference2023_minus2018=means[s23]-target,
            biological_minQ=15, effective_native_BLAZE_minQ=15-s23,
            matching_rule='nearest achievable full-dataset whole-base mean using an integer negative shift and per-base Q1..50 clipping'))
    assert [r['shift2023'] for r in matching]==[-17,-16,-15,-14,-12,-11,-9,-7,-6,-5,-4]
    assert max(abs(r['mean_Q_difference2023_minus2018']) for r in matching)<.38
    write_table(OUT/'matched_quality_levels.tsv', matching)

    ids, truth, ed = [], [], []
    native={m:[] for m in ['nanopore2018','nanopore2023']}
    with gzip.open(EVIDENCE,'rt') as f:
        for line in f:
            row=json.loads(line)
            ids.append(row['header'][1:]); truth.append(row['truth_barcode']); ed.append(row['location']['barcode_ed'])
            for m in native:
                q=[ord(c)-33 for c in row['native_barcode_qualities_canonical'][m]]
                assert len(q)==16
                native[m].append(q)
    assert len(ids)==len(set(ids))==50000 and len(set(truth))==5000
    native={m:np.asarray(v,dtype=np.int16) for m,v in native.items()}
    clean=np.asarray(ed)==0
    assert clean.sum()==8887
    records, arrays, histogram_rows=[], {}, []
    def add(model, shift, tag, fullmean, pair18, fullbc=None, fullpass=None, unadjusted=False):
        q=native[model].copy() if unadjusted else np.clip(native[model]+shift,1,50)
        x=q.mean(axis=1)
        arrays[(model,shift)]=x
        label=f'{model} native' if unadjusted else f'{model} {shift:+d}'
        records.append(dict(dataset='L',model=model,condition=tag,shift=shift,paired2018_shift=pair18,
            label=label,quality_transform='none; raw native scores' if unadjusted else 'per-base clip(Q+shift,1,50)',
            full_dataset_mean_Q=fullmean,full_located_barcode_mean_Q=fullbc,
            full_truth_located_barcode_minQ15_pass_n=fullpass,
            sample_reads=50000,sample_mean_barcode_Q=float(x.mean()),sample_SD=float(x.std(ddof=1)),
            sample_median=float(np.median(x)),sample_P2_5=float(np.quantile(x,.025)),sample_P97_5=float(np.quantile(x,.975)),
            sample_clean_mean_Q=float(x[clean].mean()),sample_error_mean_Q=float(x[~clean].mean()),
            sample_clean_error_gap=float(x[clean].mean()-x[~clean].mean()),
            sample_minQ15_pass_n=int((q.min(axis=1)>=15).sum())))
        if model=='nanopore2023':
            transformed=score if unadjusted else np.clip(score+shift,1,50)
            for newq in sorted(set(transformed)):
                mask=transformed==newq
                histogram_rows.append(dict(model=model,condition=tag,shift=shift,q=int(newq),
                    whole_base_count=int(whole_n[mask].sum()),barcode_base_count=int(barcode_n[mask].sum()),
                    truth_located_barcode_window_min_count=int(minimum_n[mask].sum())))
    for r in matching:
        s18,s23=r['shift2018'],r['shift2023']
        add('nanopore2018',s18,r['condition2018'],r['mean_whole_Q2018'],s18,
            float(metadata18[s18]['mean_barcode_base_q']),int(metadata18[s18]['pass_minQ15']))
        transform=np.clip(score+s23,1,50)
        add('nanopore2023',s23,r['condition2023'],r['mean_whole_Q2023'],s18,
            float(np.dot(transform,barcode_n)/barcode_n.sum()),int(minimum_n[transform>=15].sum()))
    add('nanopore2018',0,'native_unadjusted',float(metadata18[1]['mean_all_base_q'])-1,None,
        float(metadata18[1]['mean_barcode_base_q'])-1,None,True)
    add('nanopore2023',0,'native_unadjusted',float(np.dot(score,whole_n)/whole_n.sum()),None,
        float(np.dot(score,barcode_n)/barcode_n.sum()),int(minimum_n[score>=15].sum()),True)
    assert sum(r['model']=='nanopore2023' for r in records)==12
    write_table(OUT/'quality_summary.tsv',records)
    write_table(OUT/'reconstructed_full_quality_histograms.tsv',histogram_rows)
    paired=[]
    for i,readid in enumerate(ids):
        row=dict(read_id=readid,truth_barcode=truth[i],barcode_ED=ed[i])
        row.update({r['label']:float(arrays[(r['model'],r['shift'])][i]) for r in records})
        paired.append(row)
    write_table(OUT/'paired_50000_barcode_mean_Q.csv',paired,',')

    # Every original 2018 column and both existing 2023 columns must be unchanged.
    prior=read_table(Path('/scratch-nfs/f005f43/sctagger_all_quality_distributions_20260913/paired_50000_all_conditions.csv'),',')
    check_labels=[r['label'] for r in records if r['label'] in prior[0]]
    nchecked=0
    for i,row in enumerate(prior):
        assert row['read_id']==ids[i]
        for label in check_labels:
            assert float(row[label])==paired[i][label]
            nchecked+=1
    assert nchecked==750000

    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    fig,axes=plt.subplots(3,4,figsize=(15.5,10),sharex=True,sharey=True)
    for ax,r in zip(axes.ravel(),matching):
        for model,s,color in [('nanopore2018',r['shift2018'],BLUE),('nanopore2023',r['shift2023'],ORANGE)]:
            ax.hist(arrays[(model,s)],bins=np.arange(0,53,.5),density=True,histtype='step',lw=1.5,
                    color=color,label=f'{model[-4:]} {s:+d}')
        ax.set_title(f"Whole-read Q {r['mean_whole_Q2018']:.2f} / {r['mean_whole_Q2023']:.2f}",fontsize=10)
        ax.legend(frameon=False,fontsize=9,loc='upper right')
    ax=axes.ravel()[-1]
    for model,color in [('nanopore2018',BLUE),('nanopore2023',ORANGE)]:
        ax.hist(arrays[(model,0)],bins=np.arange(0,53,.5),density=True,histtype='step',lw=1.5,color=color,label=model[-4:]+' native')
    ax.set_title('Unadjusted references (different whole Q)',fontsize=10)
    ax.legend(frameon=False,fontsize=9,loc='upper right')
    for ax in axes.ravel():
        ax.set(xlim=(0,52),ylim=(0,.19),xticks=[0,10,20,30,40,50])
    for ax in axes[-1]: ax.set_xlabel('Mean barcode Q per read')
    for ax in axes[:,0]: ax.set_ylabel('Density')
    fig.suptitle('Extended 2023 sweep compared with all 2018 quality levels',fontsize=16,y=.99)
    fig.text(.5,.955,'Same 50,000 ScTagger-L reads; blue = 2018, orange = 2023. Panel headings show achieved whole-read means in that order.',ha='center',fontsize=10)
    fig.text(.5,.014,'Negative 2023 shifts match whole-read quality as closely as integer Phred shifts permit. Shifted scores are clipped per base to Q1–Q50.',ha='center',fontsize=10)
    fig.tight_layout(rect=(0,.04,1,.93),h_pad=2)
    for ext in ['png','pdf']: fig.savefig(OUT/f'matched_distribution_grid.{ext}',dpi=170)
    plt.close(fig)

    fig,axes=plt.subplots(1,3,figsize=(14.8,4.8))
    for model,color in [('nanopore2018',BLUE),('nanopore2023',ORANGE)]:
        subset=[r for r in records if r['model']==model and r['shift']!=0]
        for ax,key,title in zip(axes,['sample_mean_barcode_Q','sample_SD','sample_clean_error_gap'],
                                ['Mean barcode Q','SD of barcode means','Clean–error mean Q gap']):
            ax.plot([r['full_dataset_mean_Q'] for r in subset],[r[key] for r in subset],'-o',color=color,label=model)
            native_row=next(r for r in records if r['model']==model and r['shift']==0)
            ax.plot(native_row['full_dataset_mean_Q'],native_row[key],marker='*',markersize=12,color=color,linestyle='none')
            ax.set(xlabel='Achieved whole-read mean Q',ylabel=title,title=title)
    axes[0].legend(frameon=False)
    fig.suptitle('How barcode quality changes across the extended sweep',fontsize=15)
    fig.text(.5,.015,'Lines connect shifted conditions. Stars show the unadjusted models. Barcode statistics use the same 50,000-read sample.',ha='center',fontsize=10)
    fig.tight_layout(rect=(0,.06,1,.93))
    for ext in ['png','pdf']: fig.savefig(OUT/f'barcode_quality_trends.{ext}',dpi=180)
    plt.close(fig)
    validation=dict(status='PASS',sample_reads=50000,truth_barcodes=5000,paired_quality_levels=11,
        conditions_including_two_native_references=len(records),unchanged_existing_values_checked=nchecked,
        maximum_whole_mean_matching_error=max(abs(r['mean_Q_difference2023_minus2018']) for r in matching),
        note='Full quality histograms are exact transformations of the validated native histogram; no full FASTQ is generated.',
        source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                      [EVIDENCE,NATIVE/'results/quality_distribution.tsv',ARCHIVE18/'quality_conditions.tsv']})
    (OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    print(json.dumps(validation,indent=2))
    print(json.dumps(matching,indent=2))


if __name__=='__main__':main()
