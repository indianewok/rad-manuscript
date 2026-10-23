#!/usr/bin/env python3
import csv,pathlib,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/sctagger_sweep_summary_mpl_20260912')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=pathlib.Path('/scratch/f005f43/sctagger_quality_sweep_summary_20260912/canonical')
with (r/'BLAZE_F1_SWEEP.tsv').open() as f:rows=list(csv.DictReader(f,delimiter='\t'))
shifted=[x for x in rows if x['quality_tag']!='flatQ20'];flat=rows[0]
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42})
fig,ax=plt.subplots(figsize=(8.6,4.8),layout='constrained')
for d,color,marker,label in [('L','#6C3BAA','o','ScTagger-L (5,000 cells)'),('S','#127C93','s','ScTagger-S (50 cells)')]:
 ax.plot([float(x['mean_q_'+d]) for x in shifted],[float(x['BLAZE_f1_'+d]) for x in shifted],color=color,marker=marker,markersize=5,linewidth=1.8,label=label)
 ax.scatter([20],[float(flat['BLAZE_f1_'+d])],s=80,marker='D',facecolors='none',edgecolors=color,linewidths=1.7,zorder=6)
selected=next(x for x in shifted if x['quality_tag']=='shift_p06')
x=float(selected['mean_q_L']);y=float(selected['BLAZE_f1_L'])
ax.annotate('L: Q20.18, F1 = 0.991375',xy=(x,y),xytext=(20.5,.77),arrowprops={'arrowstyle':'-','color':'#6C3BAA'},color='#553080')
ax.annotate('Flat Q20 controls\nL: 0.942774; S: 0.943396',xy=(20,float(flat['BLAZE_f1_L'])),xytext=(18.3,.43),arrowprops={'arrowstyle':'-','color':'#555555'},fontsize=10,color='#444444')
ax.set(xlabel='Mean per-base Phred score',ylabel='Cell-barcode discovery F1',xlim=(14.7,27.7),ylim=(0,1.045),title='BLAZE across the ScTagger quality sweep')
ax.set_xticks(range(15,28,2));ax.set_yticks([0,.2,.4,.6,.8,1]);ax.grid(axis='y',alpha=.2)
ax.legend(loc='lower right',frameon=False)
fig.savefig(r/'BLAZE_F1_SWEEP.png',dpi=200)
fig.savefig(r/'BLAZE_F1_SWEEP.pdf')
print('Saved PNG and PDF from validated BLAZE_F1_SWEEP.tsv')
