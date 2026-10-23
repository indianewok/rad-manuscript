"""Assemble audit/task indexes and transport snapshots; never execute project analyses."""
from pathlib import Path
import csv
import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime, timezone

H=Path(__file__).resolve().parents[1]
B=Path('/Volumes/rad_data/reviewer_comment_data')
components=['global_tasks.json','figures_1_2_4_tasks.json','figure_3_tasks.json','figures_5_6_7_tasks.json']
required={'id','priority','panels','purpose','inputs','scripts','checkpoints','actions','validation','dependencies','decision_needed','public_outputs','availability_notes'}
tasks=[]
for name in components:
    data=json.loads((H/'components'/name).read_text())
    assert isinstance(data,list),name
    for task in data:
        assert required <= set(task),(name,task.get('id'),required-set(task))
        task=dict(task)
        task['component_file']='components/'+name
        task['status']='deferred' if task['priority']=='DEFERRED' else 'planned'
        if task['id'].startswith('F') and 'G-01' not in task['dependencies']:
            task['dependencies']=['G-01']+task['dependencies']
        tasks.append(task)
ids=[t['id'] for t in tasks]
assert len(ids)==len(set(ids)),'Duplicate task IDs'
byid={t['id']:t for t in tasks}
byid['G-06']['dependencies']+= [i for i in ids if i.startswith('F') and byid[i]['priority']!='DEFERRED']
for t in tasks:
    assert all(x in byid for x in t['dependencies']),(t['id'],t['dependencies'])
visited=set(); active=set(); order=[]
def visit(i):
    assert i not in active,('Dependency cycle',i)
    if i in visited:return
    active.add(i)
    for d in byid[i]['dependencies']:visit(d)
    active.remove(i);visited.add(i);order.append(i)
for i in ids:visit(i)
meta={'prepared_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'Current RAD manuscript Figures 1-7; Figure 8 removed; Figure 7E pending','purpose':'HPC execution plan, not evidence of completed reruns','repository_url':'https://github.com/indianewok/rad-manuscript','repository_commit':'3465937aa6a8e51b9f6989e750d45990a2a3d7d6','original_project_root':str(B),'path_mapping_required':True,'authority':'AUTHOR_DECISIONS.md','checkpoint_contract':'CHECKPOINT_AND_RELEASE_SPEC.md','topological_task_order':order,'task_count':len(tasks),'priority_counts':dict(Counter(t['priority'] for t in tasks))}
(H/'regeneration_tasks.json').write_text(json.dumps({'metadata':meta,'tasks':tasks},indent=2,ensure_ascii=False)+'\n')
def flat(x):
    if isinstance(x,list):return ' | '.join(str(v).replace('\n',' ') for v in x)
    return str(x).replace('\n',' ')
with (H/'REGENERATION_MATRIX.tsv').open('w') as f:
    w=csv.writer(f,delimiter='\t');w.writerow(['task_id','priority','panels','purpose','dependencies','decision_needed','key_checkpoints','validation','detail_file'])
    for t in tasks:w.writerow([t['id'],t['priority'],flat(t['panels']),flat(t['purpose']),flat(t['dependencies']),flat(t['decision_needed']),flat(t['checkpoints']),flat(t['validation']),t['component_file']])

# Inspect only explicitly named assets. Do not recursively discover data.
assets={}
for t in tasks:
    for kind in ['inputs','scripts']:
        for raw in t[kind]:
            p=Path(str(raw))
            if not p.is_absolute():continue
            row=assets.setdefault(str(p),{'original_path':str(p),'task_ids':[],'roles':[]})
            if t['id'] not in row['task_ids']:row['task_ids'].append(t['id'])
            if kind not in row['roles']:row['roles'].append(kind)
for row in assets.values():
    p=Path(row['original_path'])
    row['is_symlink']=p.is_symlink()
    if row['is_symlink']:row['symlink_target']=str(p.readlink())
    try:
        st=p.stat()
        row['bytes']=st.st_size
        row['kind']='directory' if p.is_dir() else 'file'
        row['status']='present_metadata_only'
    except (OSError,ValueError) as e:
        row.update(status='missing_at_checked_path',kind='unknown',bytes=None,error=str(e))

# Snapshot explicitly named code; expand only one level of a named scripts directory.
code_extensions={'.py','.R','.r','.Rmd','.sh','.cpp','.c','.h','.hpp','.yaml','.yml','.toml','.nf','.smk'}
code_paths=set()
for row in assets.values():
    p=Path(row['original_path'])
    if row['status']!='present_metadata_only' or 'scripts' not in row['roles']:continue
    if p.is_file() and p.suffix in code_extensions:code_paths.add(p)
    elif p.is_dir():
        for q in p.iterdir():
            if q.is_file() and q.suffix in code_extensions:code_paths.add(q)
code_rows=[]
for p in sorted(code_paths):
    if H in p.parents:continue
    if p.stat().st_size>5_000_000:continue
    try:rel=Path('reviewer_comment_data')/p.relative_to(B)
    except ValueError:rel=Path('external')/str(p).lstrip('/')
    dest=H/'code_snapshots'/rel
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(p,dest)
    code_rows.append({'original_path':str(p),'snapshot':str(dest.relative_to(H)),'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'status':'copied_and_hashed_not_executed'})
# Code source paths retain original dependencies; source collection != portable build.
(H/'audit/code_snapshot_manifest.json').write_text(json.dumps(code_rows,indent=2)+'\n')
for r in code_rows:
    if r['original_path'] in assets:
        assets[r['original_path']]['snapshot']=r['snapshot'];assets[r['original_path']]['snapshot_sha256']=r['sha256']
# Include named compact checkpoint/provenance files; large analyses stay at their source.
small_rows=[]
for r in assets.values():
    p=Path(r['original_path'])
    if r['status']!='present_metadata_only' or r.get('snapshot') or H in p.parents:continue
    if not p.is_file() or p.suffix not in {'.md','.json','.tsv','.csv','.txt','.yaml','.yml'}:continue
    if p.stat().st_size>2_000_000:continue
    try:rel=Path('reviewer_comment_data')/p.relative_to(B)
    except ValueError:rel=Path('external')/str(p).lstrip('/')
    dest=H/'checkpoint_snapshots'/rel
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(p,dest)
    sha=hashlib.sha256(dest.read_bytes()).hexdigest()
    r['snapshot']=str(dest.relative_to(H));r['snapshot_sha256']=sha
    small_rows.append({'original_path':str(p),'snapshot':r['snapshot'],'bytes':dest.stat().st_size,'sha256':sha,'status':'copied_and_hashed; scientific validation remains task-specific'})
(H/'audit/checkpoint_snapshot_manifest.json').write_text(json.dumps(small_rows,indent=2)+'\n')
(H/'audit/asset_availability.json').write_text(json.dumps(list(assets.values()),indent=2)+'\n')
with (H/'TRANSFER_AND_AVAILABILITY.tsv').open('w') as f:
    w=csv.writer(f,delimiter='\t');w.writerow(['original_path','task_ids','role','kind','local_status','bytes','symlink_target','included_snapshot','hpc_action'])
    for r in sorted(assets.values(),key=lambda x:x['original_path']):
        action='Map/check on HPC; transfer or restore if needed; verify content before reuse'
        if r.get('snapshot'):action='Snapshot included; compare hash and restore dependencies before use'
        elif r['status']=='missing_at_checked_path':action='Check original HPC location first; recover/download/regenerate only after identity and scope review'
        elif str(H) in r['original_path']:action='Included handoff context; resolve bundle-relative path'
        w.writerow([r['original_path'],flat(r['task_ids']),flat(r['roles']),r['kind'],r['status'],r['bytes'],r.get('symlink_target',''),r.get('snapshot',''),action])
# Capture the four archive assets without downloading them.
z=json.loads((H/'audit/zenodo_record.json').read_text())
(H/'audit/zenodo_files.json').write_text(json.dumps(z.get('files',[]),indent=2)+'\n')
report={'task_count':len(tasks),'priority_counts':meta['priority_counts'],'task_required_fields':'passed','task_ids_unique':'passed','dependency_references':'passed','dependency_graph_acyclic':'passed','named_asset_count':len(assets),'asset_status_counts':dict(Counter(r['status'] for r in assets.values())),'code_files_snapshotted':len(code_rows),'compact_checkpoint_files_snapshotted':len(small_rows),'project_analysis_execution':'not performed','large_asset_hashing':'not performed; metadata checks only unless a prior evidence report states otherwise'}
(H/'audit/handoff_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
