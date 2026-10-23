"""Package the private handoff; exclude Git internals and all external large data."""
from pathlib import Path
import hashlib, json, os, re, subprocess, zipfile
H=Path(__file__).resolve().parents[1]
W=H.parent
archive=W/'RAD_HPC_handoff_20261023.zip'
# Validate local links in the authored top-level documents only.
link_checks=[]
for p in sorted(H.glob('*.md')):
    for label,target in re.findall(r'\[([^\]]+)\]\(([^\)]+)\)',p.read_text()):
        target=target.strip('<>')
        if '://' in target or target.startswith('#'):continue
        clean=target.split('#',1)[0]
        q=Path(clean) if clean.startswith('/') else p.parent/clean
        link_checks.append({'file':p.name,'label':label,'target':target,'exists':q.exists()})
assert all(r['exists'] for r in link_checks),[x for x in link_checks if not x['exists']]
meta=json.loads((H/'regeneration_tasks.json').read_text())
repo=json.loads((H/'audit/repository_snapshot.json').read_text())
assert subprocess.check_output(['git','status','--porcelain'],cwd=H/'rad-manuscript',text=True)==''
for r in repo['files']:
    p=H/'rad-manuscript'/r['path']
    assert p.stat().st_size==r['bytes']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
report={'top_level_markdown_links':link_checks,'all_top_level_links_exist':True,'repository_tracked_files_match_snapshot':True,'repository_worktree_clean':True,'task_count':meta['metadata']['task_count'],'note':'Scientific reruns and native Prism QA are not part of these packaging checks.'}
(H/'audit/package_preflight.json').write_text(json.dumps(report,indent=2)+'\n')
paths=[]
for root,dirs,files in os.walk(H):
    dirs[:]=sorted(d for d in dirs if d not in {'.git','__pycache__'})
    for name in sorted(files):
        p=Path(root)/name
        if name=='SHA256SUMS' and p.parent==H:continue
        if p.is_symlink():raise ValueError('Unexpected package symlink: '+str(p))
        paths.append(p)
paths.sort()
sha=[]
for p in paths:
    sha.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(H).as_posix())
(H/'SHA256SUMS').write_text('\n'.join(sha)+'\n')
paths.append(H/'SHA256SUMS')
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4,allowZip64=True) as z:
    for p in paths:z.write(p,Path(H.name)/p.relative_to(H))
with zipfile.ZipFile(archive) as z:
    err=z.testzip()
    assert err is None,err
    count=len(z.infolist())
report={'archive':str(archive),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'file_count':count,'zip_crc_test':'passed','sha256_manifest_entries':len(sha),'task_count':meta['metadata']['task_count'],'scope':'Private handoff, not public release; no external raw sequence/BAM/RData downloads included','excluded':['rad-manuscript/.git/','__pycache__/']}
(W/'RAD_HPC_handoff_20261023_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
