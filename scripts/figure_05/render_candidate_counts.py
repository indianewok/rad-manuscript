#!/usr/bin/env python3
"""Render candidate receptor and selected Split-seq source-verification proofs."""
import argparse
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input',type=Path,default=root/'source_data/figure_05/candidate_receptor_totals.tsv')
parser.add_argument('--output-dir',type=Path,default=root/'figures/figure_05')
parser.add_argument('--splitseq-input',type=Path)
parser.add_argument('--splitseq-summary',type=Path)
args=parser.parse_args()
if bool(args.splitseq_input)!=bool(args.splitseq_summary):
    parser.error('Pass both --splitseq-input and --splitseq-summary')
plt.rcParams.update({'svg.fonttype':'none','pdf.fonttype':42})
rows=list(csv.DictReader(args.input.open(),delimiter='\t'))
fig,ax=plt.subplots(figsize=(6,3.8))
for i,r in enumerate(rows):
    native=int(r['native'])/1e6; corrected=int(r['corrected_only'])/1e6
    ax.bar(i,native,color='#416b91',label='Native' if i==0 else None)
    ax.bar(i,corrected,bottom=native,color='#d7b36a',label='Corrected only' if i==0 else None)
    ax.text(i,native+corrected+.1,'{:,}'.format(int(r['assigned'])),ha='center',fontsize=8)
ax.set_xticks(range(len(rows)));ax.set_xticklabels([r['tool'] for r in rows]);ax.set_ylabel('Assigned original reads (millions)')
ax.set_title('Recovered receptor candidates: source verification\nFinal Figure 5 source binding remains unresolved',fontsize=10)
ax.legend(fontsize=8);ax.set_ylim(0,10);fig.tight_layout()
dest=args.output_dir;dest.mkdir(parents=True,exist_ok=True)
for ext in ('png','svg','pdf'):fig.savefig(str(dest/('candidate_receptor_count_verification.'+ext)),dpi=180)
plt.close(fig)

if args.splitseq_input:
    pairs=list(csv.DictReader(args.splitseq_input.open(),delimiter='\t'))
    summary=list(csv.DictReader(args.splitseq_summary.open(),delimiter='\t'))
    if len(pairs)!=568 or len({x['canonical_barcode'] for x in pairs})!=568:
        raise ValueError('Expected568 unique physical-cell pairs')
    fig,axes=plt.subplots(1,2,figsize=(10,4.3))
    for i,row in enumerate(summary):
        value=float(row['full_unique_source_read_percent'])
        axes[0].bar(i,value,color=['#4995a4','#c6aa58'][i])
        axes[0].text(i,value+.7,f"{value:.2f}%\n{int(row['full_unique_source_reads']):,} reads",ha='center',fontsize=8)
    axes[0].set(xticks=[0,1],xticklabels=['RAD ED2','Component\nFlexiplex + poly-T'],ylim=(0,55),
                ylabel='Distinct original reads assigned (%)',title='Full input: 5,764,421 original reads')
    sample_colors={'MB_cells':'#437ea8','MB_nuclei':'#d68840','MT_nuclei':'#6f9a54'}
    for sample,color in sample_colors.items():
        sub=[x for x in pairs if x['sample']==sample]
        axes[1].scatter([int(x['rad_reads']) for x in sub],[int(x['component_polyt_reads']) for x in sub],
                        s=11,color=color,alpha=.7,label=sample.replace('_',' '))
    axes[1].plot([5,70000],[5,70000],color='#777777',linestyle=':',linewidth=1)
    axes[1].set(xscale='log',yscale='log',xlim=(5,70000),ylim=(5,70000),
                xlabel='RAD: distinct reads per cell',ylabel='Component Flexiplex: distinct reads per cell',
                title='568 matched physical cells; dotted line y=x')
    axes[1].legend(frameon=False,fontsize=8)
    fig.suptitle('Selected LR-Split-seq source verification; final artwork QA remains separate',fontsize=10)
    fig.tight_layout()
    for ext in ('png','svg','pdf'):fig.savefig(str(dest/('splitseq_selected_read_verification.'+ext)),dpi=180)
    plt.close(fig)
