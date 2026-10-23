"""Truth-score the native-2023 cache with the unchanged BLAZE row matcher.

An exact incremental replay reuses old calls only when no member of the
whitelist symmetric difference is within the maximum distance. Common
candidate iteration order is preserved. Full old/new matcher calls validate
a deterministic sample; every sequence-dependent extraction field is checked.
"""
from pathlib import Path
import ast,collections,csv,gzip,hashlib,itertools,json,multiprocessing as mp,os,sys,time

ROOT=Path('/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022')
FILES=Path('/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files')
OLD=FILES/'sctagger_q20p18_prism_update_20260912'
NEW=FILES/'sctagger_nanopore2023_unadjusted_20260913'
OUT=ROOT/'prism/blaze2023_assignment_replay'
MATCHER=Path('/Volumes/rad_data/reviewer_comment_data/software_pins_20260810/blaze_fast_selector/upstream_v2.6.0a0/source/read_assignment.py')
sys.path.insert(0,str(ROOT/'prism/dependencies'))
from fast_edit_distance import sub_edit_distance

FIELDS=['read_id','putative_bc','putative_bc_min_q','putative_umi','polyT_end','pre_bc_flanking','post_umi_flanking']
Row=collections.namedtuple('Row',FIELDS)
class OrderedSet(set):
    def __init__(self,order):
        super().__init__(order);self.order=tuple(order)
    def __iter__(self):return iter(self.order)

def init(old_order,new_order):
    global old_wl,new_wl,changed,match
    old_wl=OrderedSet(old_order);new_wl=OrderedSet(new_order)
    changed=sorted(set(old_order)^set(new_order))
    tree=ast.parse(MATCHER.read_text())
    f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_match_bc_row')
    env={'sub_edit_distance':sub_edit_distance,'DEFAULT_ED_FLANKING':2}
    exec(compile(ast.Module(body=[f],type_ignores=[]),str(MATCHER),'exec'),env)
    match=env['_match_bc_row']

def score(batch):
    out=[]
    for index,v,old_final in batch:
        row=Row(v[0],v[1],float(v[2]) if v[2] else '',v[3],float(v[4]) if v[4] else '',v[5],v[6])
        if not row.putative_bc or row.putative_bc in new_wl:
            final=match(row,new_wl,2,0)[0];mode='direct'
        else:
            extended=row.pre_bc_flanking[-2:]+row.putative_bc+row.putative_umi[:2]
            affected=any(sub_edit_distance(bc,extended,2)[0]<=2 for bc in changed)
            if affected:
                final=match(row,new_wl,2,0)[0];mode='full_changed_neighborhood'
            else:
                final=old_final;mode='unchanged_neighborhood'
                assert not final or final in new_wl
        validated=False
        if index%4999==0:
            assert match(row,old_wl,2,0)[0]==old_final,('old replay validation',index)
            assert match(row,new_wl,2,0)[0]==final,('new replay validation',index)
            validated=True
        out.append((row.read_id,row.putative_bc,old_final,final,mode,validated))
    return out

def stream(new_path,old_path,old_calls,audit):
    h=hashlib.sha256();n=0;batch=[]
    with new_path.open(newline='') as a,gzip.open(old_path,'rt',newline='') as b,gzip.open(old_calls,'rt',newline='') as c:
        ra=csv.reader(a);rb=csv.reader(b);rc=csv.reader(c,delimiter='\t')
        assert next(ra)==next(rb)==FIELDS
        assert next(rc)==['read_id','true_barcode','putative_barcode','assigned_barcode','state','target_class']
        for va,vb,vc in itertools.zip_longest(ra,rb,rc):
            assert va is not None and vb is not None and vc is not None
            assert va[:2]+va[3:]==vb[:2]+vb[3:],('changed extraction',n)
            assert va[0]==vc[0] and va[1]==vc[2]
            assert vc[1]==va[0].split('-',1)[0]
            h.update(('\t'.join(va[:2]+va[3:])+'\n').encode())
            batch.append((n,va,vc[3]));n+=1
            if len(batch)==1000:yield batch;batch=[]
        if batch:yield batch
    audit.update(rows=n,nonquality_extraction_fields_identical=True,nonquality_extraction_sha256=h.hexdigest())

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assert not (OUT/'DONE').exists(),'Already completed'
    old_order=(OLD/'blaze_native_replay_seed0/shift_p06_Q20p1811/matcher_whitelist_iteration_order.txt').read_text().splitlines()
    newset={x.split('-')[0].strip() for x in (NEW/'runs/L/nanopore2023_native_unadjusted/blaze/whitelist.csv').read_text().splitlines() if x.strip()}
    truth=set((NEW/'metadata/L_truth_barcodes.txt').read_text().splitlines())
    assert len(old_order)==5087 and len(newset)==5015 and len(truth)==5000 and truth<=newset
    new_order=[x for x in old_order if x in newset]+sorted(newset-set(old_order))
    assert len(new_order)==len(set(new_order))==5015
    (OUT/'matcher_whitelist_iteration_order.txt').write_text('\n'.join(new_order)+'\n')
    metrics=collections.Counter();baseline=collections.Counter();per=collections.defaultdict(collections.Counter);raw_support=collections.Counter();modes=collections.Counter();audit={};started=time.time()
    inputs={'new_raw':NEW/'runs/L/nanopore2023_native_unadjusted/blaze/putative_bc.csv','old_raw':OLD/'replay_inputs/shift_p06/putative_bc.csv.gz','old_calls':OLD/'blaze_native_replay_seed0/shift_p06_Q20p1811/assignment_records.tsv.gz'}
    with gzip.open(OUT/'assignment_records.tsv.gz','wt',compresslevel=1,newline='') as f:
        writer=csv.writer(f,delimiter='\t',lineterminator='\n');writer.writerow(['read_id','true_barcode','putative_barcode','assigned_barcode','state','target_class'])
        with mp.Pool(6,initializer=init,initargs=(old_order,new_order)) as pool:
            for batch in pool.imap(score,stream(inputs['new_raw'],inputs['old_raw'],inputs['old_calls'],audit),chunksize=1):
                for rid,raw,old_final,final,mode,validated in batch:
                    true=rid.split('-',1)[0];assert true in truth
                    raw_support[raw]+=1;modes[mode]+=1;modes['validated_full_old_and_new']+=validated
                    metrics['input_reads']+=1;baseline['input_reads']+=1
                    if old_final:
                        state=('native' if old_final==raw else 'corrected')+('_correct' if old_final==true else '_incorrect');baseline['assigned']+=1;baseline[state]+=1
                    else:baseline['unassigned']+=1
                    if final:
                        assert final in newset
                        state=('native' if final==raw else 'corrected')+('_correct' if final==true else '_incorrect');target='truth' if final in truth else 'extra'
                        metrics['assigned']+=1;metrics[state]+=1;metrics[target+'_assigned']+=1;per[final]['assigned']+=1;per[final][state]+=1
                    else:state='unassigned';target='';metrics['unassigned']+=1
                    metrics['changed_call']+=final!=old_final
                    writer.writerow([rid,true,raw,final,state,target])
                n=metrics['input_reads']
                if n%100000==0:print(json.dumps({'processed':n,'elapsed_seconds':round(time.time()-started,1),'modes':modes}),flush=True)
    assert audit['rows']==metrics['input_reads']==4993805
    original=json.loads((OLD/'blaze_native_replay_seed0/shift_p06_Q20p1811/metrics.json').read_text())
    for k in ['input_reads','assigned','unassigned','native_correct','native_incorrect','corrected_correct','corrected_incorrect']:assert baseline[k]==original[k],(k,baseline[k],original[k])
    assert metrics['assigned']+metrics['unassigned']==4993805
    metrics.update(whitelist_barcodes=len(newset),truth_barcodes=len(newset&truth),false_barcodes=len(newset-truth))
    (OUT/'metrics.json').write_text(json.dumps(metrics,indent=2))
    with (OUT/'per_barcode.tsv').open('w',newline='') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n');cols=['assigned','native_correct','corrected_correct','native_incorrect','corrected_incorrect'];w.writerow(['barcode','is_true','raw_extraction_count']+cols)
        for bc in sorted(newset):w.writerow([bc,bc in truth,raw_support[bc]]+[per[bc][c] for c in cols])
    prov={'method':'Unchanged BLAZE2.6.0a0 _match_bc_row; exact incremental whitelist replay. Common iteration order retained from archived seed0 run, new candidates appended lexically. Calls reused only if no changed whitelist candidate can match at edit distance<=2.','matcher_source':str(MATCHER),'matcher_sha256':hashlib.sha256(MATCHER.read_bytes()).hexdigest(),'max_edit_distance':2,'minQ':0,'python':sys.version,'fast_edit_distance':'1.2.2','inputs':{k:str(v) for k,v in inputs.items()},'audit':audit,'baseline_metrics_reproduced':baseline,'modes':modes,'removed_candidates':sorted(set(old_order)-newset),'added_candidates':sorted(newset-set(old_order)),'elapsed_seconds':time.time()-started,'no_fastq_reprocessing':True}
    (OUT/'provenance.json').write_text(json.dumps(prov,indent=2));(OUT/'DONE').write_text('PASS\n');print(json.dumps({'complete':True,'metrics':metrics,'seconds':time.time()-started}),flush=True)

if __name__=='__main__':main()
