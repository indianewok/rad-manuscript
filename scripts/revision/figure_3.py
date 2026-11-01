#!/usr/bin/env python3
"""Build, validate and plot the Figure 3 supplied-list and correction analyses."""
import argparse
import collections
import csv
import contextlib
import gzip
import hashlib
import io
import json
import os
import tempfile
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ['RAD', 'BLAZE', 'Flexiplex']
ARMS = ['SC_ONT', 'SN_ONT', 'SC_PB', 'SN_PB']
CLASSES = {'noncatalog_to_selected': 'Corrected off-list',
           'cellranger_to_different_cellranger_K': 'Failure Mode 1',
           'catalog_noncell_to_selected_A': 'Failure Mode 2'}
PACKAGES = {'ScTagger-L': 'sctagger_L_false_whitelist_20260813',
            'LongBench SC-ONT': 'longbench_sc_ont_false_whitelist_20260813'}
DATASETS = [*PACKAGES, 'RAGE-seq']
EXPECTED = {
 'ScTagger-L': {'RAD':[48997,49004,49292], 'BLAZE':[294175,304701,299332], 'Flexiplex':[462690,465375,458773]},
 'LongBench SC-ONT': {'RAD':[46487,46961,46568], 'BLAZE':[1005393,1024563,1097594], 'Flexiplex':[1364364,1370330,1422565]}}
EXPECTED_CORRECTION = {
 'SC_ONT': [(9690454,0,0,96569433),(8672726,1101618,61301,93175479),(10386527,1429752,31,103475960)],
 'SN_ONT': [(8311132,0,0,57487924),(5800878,10562779,738294,59984175),(8221126,14331912,108704,73883233)],
 'SC_PB': [(4816829,0,0,178846937),(3932949,1511949,122127,178095634),(4331943,1876614,11,185509618)],
 'SN_PB': [(3945475,0,0,86368809),(2304139,17061625,1267182,93568220),(3292660,21703944,202701,107301108)]}

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for block in iter(lambda: f.read(4*1024*1024), b''): h.update(block)
    return h.hexdigest()

def read(p, delimiter='\t'):
    op=gzip.open if str(p).endswith('.gz') else open
    with op(p,'rt',newline='') as f: return list(csv.DictReader(f, delimiter=delimiter))

def write(p, rows, fields=None):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(rows[0])
    tmp = p.with_suffix(p.suffix+'.tmp')
    with contextlib.ExitStack() as stack:
        if str(p).endswith('.gz'):
            raw=stack.enter_context(open(tmp,'wb'))
            compressed=stack.enter_context(gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0))
            f=stack.enter_context(io.TextIOWrapper(compressed,encoding='utf-8',newline=''))
        else:f=stack.enter_context(open(tmp,'w',newline=''))
        w = csv.DictWriter(f, fields, delimiter='\t', lineterminator='\n');w.writeheader();w.writerows(rows)
    tmp.replace(p)

def js(p, obj):
    p = Path(p);p.parent.mkdir(parents=True, exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(obj, indent=2)+'\n');tmp.replace(p)

def tool(t): return {'rad':'RAD','blaze':'BLAZE','flexiplex':'Flexiplex','flex_v1026':'Flexiplex'}[t.lower()]

def build(a):
    out=a.output;out.mkdir(parents=True,exist_ok=True)
    b=a.project_root
    assets=[];checks=[];off=[];summaries=[];fates=[];whitelists=[];cor=[];cs=[];bindings=[]
    def asset(p):
        p=Path(p);digest=sha(p);assets.append(dict(path=str(p),sha256=digest,bytes=p.stat().st_size,role='retained_checkpoint',validation_status='verified_content'));return digest
    def check(name,observed,expected):
        checks.append(dict(check_id=name,observed=observed,expected=expected,status='passed' if observed==expected else 'failed',tolerance=0))
    for dataset,package in PACKAGES.items():
        base=b/package;p=base/'results/false_target_assigned_reads_long.tsv';digest=asset(p);rows=read(p)
        grouped=collections.defaultdict(list)
        for r in rows:
            t=tool(r['tool']);rep=int(r['replicate'].replace('rep',''));bc=r['barcode']
            count=int(r.get('assigned_reads',r.get('count')))
            if count<0:raise ValueError('Negative off-list assignment count')
            rank=int(r.get('whitelist_row_index',r.get('rank')))
            row=dict(dataset=dataset,tool=t,replicate=rep,original_row_index=rank,
                     barcode=bc,identity_status='verified_supplied_list_identity',
                     assigned_count=count,unit='strict_physical_reads',
                     source_sha256=digest)
            off.append(row);grouped[t,rep].append(row)
        for (t,rep), rr in grouped.items():
            total=sum(r['assigned_count'] for r in rr);n=5000 if dataset=='ScTagger-L' else 5211
            check(f'offlist/{dataset}/{t}/{rep}/target_count',len(rr),n)
            check(f'offlist/{dataset}/{t}/{rep}/unique_rows',len({r['original_row_index'] for r in rr}),n)
            check(f'offlist/{dataset}/{t}/{rep}/sum',total,EXPECTED[dataset][t][rep-1])
            summaries.append(dict(dataset=dataset,tool=t,replicate=rep,assigned_count=total,target_count=n,unit=rr[0]['unit'],source_sha256=digest))
        for rep in (1,2,3):
            p=base/'whitelists'/f'false_rep{rep}.txt'
            if not p.exists():
                candidates=list((base/'whitelists').glob(f'*rep{rep}*'))
                if len(candidates)!=1: raise ValueError(f'Cannot resolve target list: {p}')
                p=candidates[0]
            hd=asset(p);targets=p.read_text().splitlines()
            check(f'offlist/{dataset}/rep{rep}/list_unique',len(set(targets)),len(targets))
            for rank,bc in enumerate(targets,1): whitelists.append(dict(dataset=dataset,replicate=rep,rank=rank,barcode=bc,list_sha256=hd))
            expected_targets=set(targets)
            for t in TOOLS:
                observed={r['barcode'] for r in grouped[t,rep]}
                check(f'offlist/{dataset}/{t}/rep{rep}/target_identity',sorted(observed),sorted(expected_targets))
        p=base/'summaries/per_run_summary.tsv';asset(p)
        for r in read(p):
            t=tool(r['tool']);rep=int(r['replicate']);strict=int(r.get('strict_unique_assigned_total',r.get('assigned_records')))
            amb=int(r.get('ambiguous_physical_read_ids',r.get('duplicate_read_ids')))
            inp=4993805 if dataset=='ScTagger-L' else 10000000
            unique=int(r.get('unique_physical_read_ids',r.get('unique_read_ids')))
            check(f'offlist/{dataset}/{t}/{rep}/physical_conservation',strict+amb,unique)
            fates.append(dict(dataset=dataset,tool=t,replicate=rep,input_reads=inp,strict_assigned=strict,ambiguous_ids=amb,unassigned=inp-unique,unit='physical_reads',evidence_level='retained_C2_fully_recounted'))
    # RAGE uses the completed matched raw replay and the same strict-read unit.
    rage=ROOT/'checkpoints/figure_03/rage_matched';current=rage/'counts'
    validation=json.loads((current/'validation.json').read_text())
    if validation['status']!='passed' or len(validation['runs'])!=9:raise ValueError('Full matched RAGE validation has not passed')
    if sha(rage/'experiment.json')!=validation['experiment_sha256']:raise ValueError('RAGE experiment manifest changed after validated counting')
    for name,key in [('per_target.tsv','per_target_sha256'),('per_run_summary.tsv','per_run_summary_sha256'),('sources.tsv','source_hashes')]:
        if sha(current/name)!=validation[key]:raise ValueError('RAGE count checkpoint differs from its validation receipt: '+name)
    for r in read(current/'sources.tsv'):
        producer=rage/'runs'/r['tool'].lower()/f'rep{r["replicate"]}'/'run_manifest.json'
        if sha(producer)!=r['run_manifest_sha256']:raise ValueError('RAGE producer changed after its validated recount')
    asset(current/'validation.json');digest=asset(current/'per_target.tsv');rows=read(current/'per_target.tsv');asset(current/'per_run_summary.tsv')
    for rep in (1,2,3):
        p=rage/'inputs'/f'false_rep{rep}.txt';hd=asset(p);targets=p.read_text().splitlines()
        check(f'offlist/RAGE-seq/rep{rep}/list_unique',len(set(targets)),4505)
        for rank,bc in enumerate(targets,1):whitelists.append(dict(dataset='RAGE-seq',replicate=rep,rank=rank,barcode=bc,list_sha256=hd))
        for t in TOOLS:
            rr=[r for r in rows if r['tool']==t and int(r['replicate'])==rep]
            check(f'offlist/RAGE-seq/{t}/rep{rep}/target_identity',sorted(r['barcode'] for r in rr),sorted(targets))
            for r in rr:off.append(dict(dataset='RAGE-seq',tool=t,replicate=rep,original_row_index=int(r['rank']),barcode=r['barcode'],identity_status='verified_supplied_list_identity',assigned_count=int(r['count']),unit='strict_physical_reads',source_sha256=digest))
    for r in read(current/'per_run_summary.tsv'):
        t=r['tool'];rep=int(r['replicate']);strict=int(r['strict_unique_assigned_total']);amb=int(r['ambiguous_physical_read_ids']);inp=int(r['input_reads']);unassigned=int(r['unassigned'])
        observed=sum(x['assigned_count'] for x in off if x['dataset']=='RAGE-seq' and x['tool']==t and x['replicate']==rep)
        check(f'offlist/RAGE-seq/{t}/{rep}/sum',observed,strict)
        check(f'offlist/RAGE-seq/{t}/{rep}/physical_conservation',strict+amb+unassigned,inp)
        summaries.append(dict(dataset='RAGE-seq',tool=t,replicate=rep,assigned_count=strict,target_count=4505,unit='strict_physical_reads',source_sha256=digest))
        fates.append(dict(dataset='RAGE-seq',tool=t,replicate=rep,input_reads=inp,strict_assigned=strict,ambiguous_ids=amb,unassigned=unassigned,unit='physical_reads',evidence_level='full_raw_replay_and_ID_universe'))
    latest=b/'scratch_preservation_20260921/files/longbench_rad_4acbe00_raw_prism_20260827'
    competitor=b/'LongBench_comps/full_A_to_B_audit_20260731'
    for d in ARMS:
        for i,t in enumerate(TOOLS):
            p=latest/'runs'/d/'audit_raw_all_fast_exact' if t=='RAD' else competitor/'results/arms'/('blaze' if t=='BLAZE' else 'flex_v1026')/d
            summary=read(p/'summary.tsv')[0];asset(p/'summary.tsv');digest=asset(p/'per_target.tsv');asset(p/'invariants.tsv')
            rr=read(p/'per_target.tsv');keys=['noncatalog_to_selected','catalog_noncell_to_selected_A','cellranger_to_different_cellranger_K','unique_read_target_assignments_O']
            check(f'correction/{d}/{t}/unique_targets',len({r['target_barcode'] for r in rr}),len(rr))
            for k,expected in zip(keys,EXPECTED_CORRECTION[d][i]):
                marginal=sum(int(r[k]) for r in rr);check(f'correction/{d}/{t}/{k}/marginal',marginal,int(summary[k]));check(f'correction/{d}/{t}/{k}/selected_checkpoint',marginal,expected)
            for r in read(p/'invariants.tsv'):
                expected_status='NOT_CHECKED' if t=='Flexiplex' and r['invariant']=='blaze_header_prefix_matches_CB' else 'PASS'
                check(f'correction/{d}/{t}/retained_invariant/{r["invariant"]}',r['status'],expected_status)
            for r in rr:
                o=int(r['unique_read_target_assignments_O'])
                for k,label in CLASSES.items():
                    n=int(r[k]);
                    if not 0<=n<=o: raise ValueError(f'count outside [0,O]: {d}/{t}/{r["target_barcode"]}/{k}')
                    cor.append(dict(dataset=d,tool=t,barcode=r['target_barcode'],selected_by_tool=1,category=label,count=n,denominator_O=o,percent=(100*n/o if o else ''),unit='unique_original_read_target_pairs',source_sha256=digest))
            for k,label in CLASSES.items():
                n=int(summary[k]);o=int(summary['unique_read_target_assignments_O'])
                cs.append(dict(dataset=d,tool=t,category=label,count=n,denominator_O=o,percent=100*n/o,unit='unique_original_read_target_pairs',scope='all_records_including_CT' if t=='RAD' else 'complete_input',source_sha256=digest))
            if t=='RAD':
                for name in ['summary.tsv','per_target.tsv']:
                    other=p.parent/'audit_raw_all_fast'/name
                    if other.exists():asset(other);check(f'correction/{d}/RAD/fast_exact_parity/{name}',sha(other),sha(p/name))
    # Outer identity join: an unselected tool-target combination is explicit,
    # never silently dropped or treated as a measured zero-percent event.
    all_targets=collections.defaultdict(set);present=set()
    for r in cor:all_targets[r['dataset']].add(r['barcode']);present.add((r['dataset'],r['tool'],r['barcode'],r['category']))
    for d,targets in all_targets.items():
        for t in TOOLS:
            for bc in sorted(targets):
                for label in CLASSES.values():
                    if (d,t,bc,label) not in present:
                        cor.append(dict(dataset=d,tool=t,barcode=bc,selected_by_tool=0,category=label,count=0,denominator_O=0,percent='',unit='unique_original_read_target_pairs',source_sha256=''))
    input_counts={r['dataset']:r['input_reads'] for r in fates}
    for r in summaries:
        r['input_reads']=input_counts[r['dataset']]
        r['assignment_fraction']=r['assigned_count']/r['input_reads']
        r['mean_assigned_per_target']=r['assigned_count']/r['target_count']
    write(out/'offlist_per_target.tsv.gz',off);write(out/'offlist_totals.tsv',summaries);write(out/'offlist_read_fates.tsv',fates)
    write(out/'replicate_whitelists.tsv',whitelists)
    write(out/'correction_per_target.tsv.gz',cor);write(out/'correction_totals.tsv',cs)
    write(out/'measured_category_definitions.tsv',[
        dict(category='Corrected off-list',observed_source='Outside the full chemistry catalog',selected_target='In the tool-selected set',condition='source != target; observed source required'),
        dict(category='Failure Mode 1',observed_source='In the matched filtered reference',selected_target='In both the matched filtered reference and tool-selected set',condition='source != target; observed source required'),
        dict(category='Failure Mode 2',observed_source='In the chemistry catalog; outside the matched filtered reference',selected_target='In the tool-selected set',condition='source != target; observed source required')])
    for panel,table,key,metric,unit,decision in [
        ('A','replicate_whitelists.tsv','dataset,replicate,barcode','supplied barcode identity','catalog sequences outside the matched reference','workflow diagram'),
        ('B','offlist_totals.tsv','dataset,tool,replicate','assigned_count','strict physical reads','manuscript statistical analysis'),
        ('B_normalized_companion','offlist_totals.tsv','dataset,tool,replicate','assignment_fraction','strict physical reads / all input physical reads; display100*ratio','descriptive input-depth normalization'),
        ('C','offlist_per_target.tsv.gz','dataset,tool,replicate,barcode','assigned_count','strict physical reads per target','replicate 1; manuscript statistical analysis'),
        ('D','measured_category_definitions.tsv','category','condition','observed source and selected target sequence membership',''),
        ('E','correction_totals.tsv','dataset,tool,category','count','unique original-read–target pairs',''),
        ('F','correction_per_target.tsv.gz','dataset,tool,barcode,category','count','unique original-read–target pairs','manuscript statistical analysis'),
        ('G','correction_per_target.tsv.gz','dataset,tool,barcode,category','percent','100*category_pairs/all_assignment_pairs_O','manuscript statistical analysis')]:
        bindings.append(dict(panel=panel,table=table,row_key=key,metric=metric,unit=unit,statistical_policy=decision,sha256=sha(out/table),render_scope='rendered from source tables'))
    write(out/'panel_data_manifest.tsv',bindings)
    # Compact equal checks rather than duplicating whole barcode sets in the report.
    for c in checks:
        if isinstance(c['observed'],list) and c['status']=='passed':c['observed']=c['expected']=f'{len(c["observed"])} identical identities'
    js(a.report,dict(status='passed' if all(c['status']=='passed' for c in checks) else 'failed',level='validated_C5_to_C6',checks=checks,raw_rerun='RAGE complete; retained ScTagger/LongBench C2 fully recounted',read_target_ledger='not recovered for full D-G streams; aggregates do not establish pair overlaps'))
    write(ROOT/'manifests/figure_3_sources.tsv',assets)
    js(out/'schema.json',{'format':'UTF-8 tab separated, header row; empty numeric value is null','keys':{p.name:list(read(p)[0]) for p in list(out.glob('*.tsv'))+list(out.glob('*.tsv.gz'))},'contracts':{'offlist':'All three datasets count strict physical reads. A physical ID with multiple assignment rows is wholly excluded, including identical duplicates.','correction':'Within each class collapse original-read–target pairs; classes can overlap. No source means unknown, not noncatalog. Percent denominator O includes all pairs to target.','identity':'Each offlist target is the actual supplied nucleotide barcode; pairing requires dataset,replicate,barcode.','zero':'Targets with zero assignments retained; percent is null when O=0. Tool-unselected targets explicitly selected_by_tool=0.'}})
    checksums={p.name:sha(p) for p in out.glob('*') if p.is_file() and p.name!='checksums.json'};js(out/'checksums.json',checksums)
    if any(c['status']!='passed' for c in checks):raise SystemExit('Figure 3 checkpoint validation failed; inspect report')
    print(json.dumps({'status':'passed','checks':len(checks),'offlist_rows':len(off),'correction_rows':len(cor)}))

def validate(a):
    data=a.output;checks=json.loads((data/'checksums.json').read_text())
    for p,digest in checks.items():
        if sha(data/p)!=digest:raise ValueError(f'Hash mismatch: {p}')
    for r in read(data/'correction_per_target.tsv.gz'):
        n,o=int(r['count']),int(r['denominator_O'])
        assert 0<=n<=o
        assert (r['percent']=='' if o==0 else abs(float(r['percent'])-100*n/o)<1e-10)
    for r in read(data/'offlist_read_fates.tsv'):
        assert int(r['input_reads'])==sum(int(r[k]) for k in ['strict_assigned','ambiguous_ids','unassigned'])
    for r in read(data/'offlist_totals.tsv'):
        assert abs(float(r['assignment_fraction'])-int(r['assigned_count'])/int(r['input_reads']))<1e-12
        assert abs(float(r['mean_assigned_per_target'])-int(r['assigned_count'])/int(r['target_count']))<1e-12
    for r in read(data/'offlist_per_target.tsv.gz'):
        assert len(r['barcode'])==16 and r['unit']=='strict_physical_reads'
    print(json.dumps({'status':'passed','files':len(checks),'checks':'content hashes, percentages, conservation, supplied barcode identity, strict physical read units'}))

def render(a):
    validate(a)
    os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'rad-figure3-matplotlib'))
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.size':9,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none'})
    colors={'RAD':'#367DB0','BLAZE':'#E49F41','Flexiplex':'#42A88F'}
    a.figures.mkdir(parents=True,exist_ok=True)

    def save_plot(figure, name):
        for extension in ('pdf', 'svg', 'png'):
            target = a.figures / (name + '.' + extension)
            figure.savefig(target, dpi=200)
            if extension == 'svg':
                target.write_text('\n'.join(line.rstrip() for line in target.read_text().splitlines())+'\n')
    off=read(a.output/'offlist_totals.tsv');cor=read(a.output/'correction_per_target.tsv.gz');sums=read(a.output/'correction_totals.tsv')
    off_targets=read(a.output/'offlist_per_target.tsv.gz')
    fig,axes=plt.subplots(1,3,figsize=(11,3.5),constrained_layout=True)
    for ax,d in zip(axes,DATASETS):
        for t in TOOLS:
            x=np.sort([int(r['assigned_count']) for r in off_targets if r['dataset']==d and r['tool']==t and r['replicate']=='1'])
            ax.step(x,np.arange(1,len(x)+1)/len(x),where='post',color=colors[t],label=t)
        ax.set_xscale('symlog',linthresh=1);ax.set_title(d+' · replicate 1');ax.set_xlabel('Assignments per supplied target');ax.set_ylabel('Fraction of supplied targets');ax.spines[['top','right']].set_visible(False)
    axes[0].legend(frameon=False);fig.suptitle('Figure 3C · assignments per supplied barcode (replicate 1)')
    save_plot(fig, 'offlist_per_target')
    plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(11,3.5),constrained_layout=True)
    for ax,d in zip(axes,DATASETS):
        for j,t in enumerate(TOOLS):
            ys=[int(r['assigned_count'])/1e6 for r in off if r['dataset']==d and r['tool']==t]
            ax.scatter([j-.12,j,j+.12],ys,color=colors[t],s=32,zorder=3)
            ax.plot([j-.17,j+.17],[np.mean(ys)]*2,color=colors[t],lw=2)
        ax.set_xticks(range(3),TOOLS);ax.set_title(d);ax.set_ylabel('Strict physical reads (millions)');ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Figure 3B · total reads assigned to supplied lists')
    save_plot(fig, 'offlist_counts')
    plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(11,3.5),sharey=True,constrained_layout=True)
    for ax,d in zip(axes,DATASETS):
        for j,t in enumerate(TOOLS):
            ys=[100*float(r['assignment_fraction']) for r in off if r['dataset']==d and r['tool']==t]
            ax.scatter([j-.12,j,j+.12],ys,color=colors[t],s=32,zorder=3)
            ax.plot([j-.17,j+.17],[np.mean(ys)]*2,color=colors[t],lw=2)
        ax.set_xticks(range(3),TOOLS);ax.set_title(d);ax.set_ylabel('Strict assigned / input reads (%)');ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Figure 3B · strict assignments normalized by complete input depth')
    save_plot(fig, 'offlist_assignment_fraction')
    plt.close(fig)
    fig,axes=plt.subplots(3,4,figsize=(13,8),constrained_layout=True)
    for row,label in enumerate(CLASSES.values()):
        for col,d in enumerate(ARMS):
            ax=axes[row,col]
            for t in TOOLS:
                x=np.sort([int(r['count']) for r in cor if r['dataset']==d and r['tool']==t and r['category']==label and r['selected_by_tool']=='1'])
                ax.step(x,np.arange(1,len(x)+1)/len(x),where='post',color=colors[t],label=t)
            ax.set_xscale('symlog',linthresh=1);ax.set_title(d+' · '+label);ax.set_xlabel('Read–target pairs per selected target');ax.set_ylabel('Fraction of selected targets');ax.spines[['top','right']].set_visible(False)
    axes[0,0].legend(frameon=False);fig.suptitle('Figure 3F · correction counts per selected barcode')
    save_plot(fig, 'correction_counts')
    plt.close(fig)
    fig,axes=plt.subplots(3,4,figsize=(13,8),constrained_layout=True)
    for row,label in enumerate(CLASSES.values()):
        for col,d in enumerate(ARMS):
            ax=axes[row,col]
            for j,t in enumerate(TOOLS):
                values=[float(r['percent']) for r in cor if r['dataset']==d and r['tool']==t and r['category']==label and r['percent']!='']
                x=np.sort(values);y=np.arange(1,len(x)+1)/len(x)
                ax.step(x,y,where='post',color=colors[t],label=t)
            ax.set_title(d+' · '+label);ax.set_xlabel('Pairs in class / all pairs to target (%)');ax.set_ylabel('Fraction of selected targets');ax.spines[['top','right']].set_visible(False)
    axes[0,0].legend(frameon=False);fig.suptitle('Figure 3G · correction-category fractions per selected barcode')
    save_plot(fig, 'correction_percentages')
    plt.close(fig)
    fig,axes=plt.subplots(1,4,figsize=(13,3.5),constrained_layout=True)
    for ax,d in zip(axes,ARMS):
        for j,t in enumerate(TOOLS):
            vals=[int(next(r['count'] for r in sums if r['dataset']==d and r['tool']==t and r['category']==cat))/1e6 for cat in CLASSES.values()]
            ax.bar(np.arange(3)+(j-1)*.25,vals,width=.24,color=colors[t],label=t)
        ax.set_title(d);ax.set_xticks(range(len(CLASSES)),['Off-list' if c=='Corrected off-list' else c.replace('Failure Mode ','FM') for c in CLASSES.values()]);ax.set_ylabel('Read–target pairs (millions)');ax.spines[['top','right']].set_visible(False)
    axes[0].legend(frameon=False);fig.suptitle('Figure 3E · total correction-category counts')
    save_plot(fig, 'correction_totals')
    plt.close(fig)
    js(a.figures/'render_manifest.json',dict(source_checksums_sha256=sha(a.output/'checksums.json'),renderer_sha256=sha(__file__),matplotlib=matplotlib.__version__,numpy=np.__version__,exports={p.name:sha(p) for p in a.figures.glob('*') if p.suffix in ['.pdf','.svg','.png']},status='passed'))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['build','render','validate'])
    p.add_argument('--project-root',type=Path);p.add_argument('--output',type=Path,default=ROOT/'source_data/figure_03')
    p.add_argument('--figures',type=Path,default=ROOT/'figures/figure_03');p.add_argument('--report',type=Path,default=ROOT/'validation/figure_3_resume.json')
    a=p.parse_args()
    if a.mode=='build' and not a.project_root:p.error('build requires --project-root; render and validate use deposited source tables only')
    {'build':build,'render':render,'validate':validate}[a.mode](a)
if __name__=='__main__':main()
