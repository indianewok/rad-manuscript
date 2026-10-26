#!/usr/bin/env python3
"""Fail closed on arbitrary software paths before labeling a matched RAGE run."""
import hashlib,json,subprocess
from pathlib import Path
from figure_3 import ROOT,read,sha,js

RAD_BINARY='fc424779c1aba3f112930b4ec8c0dc874b421a217bd53ce6f227e719489a2b2d'
FLEX_BINARY='38dccd37f1747e5105b62eacde572b7e4c5206fb925dc1fdbe8210ffe8b1e8c4'

def verify_tools(rad_source,rad_binary,blaze_python,blaze_entrypoint,flex_binary,build_rad=False):
    locked=[]
    for r in read(ROOT/'manifests/figure_3_rad_source_files.tsv'):
        p=rad_source/r['path']
        if not p.is_file() or sha(p)!=r['sha256']:raise ValueError(f'RAD source differs from cd0582b: {p}')
        locked.append(dict(path=str(p),sha256=r['sha256'],role='RAD pinned source'))
    build_receipt=None
    if build_rad:
        directory=ROOT/'checkpoints/figure_03/rage_matched/tools/rad_verified_rebuild'
        commands=[['cmake','-S',str(rad_source),'-B',str(directory),'-DCMAKE_BUILD_TYPE=Release','-DBUILD_TESTING=OFF'],['cmake','--build',str(directory),'-j4']]
        for command in commands:subprocess.run(command,check=True)
        rad_binary=directory/'rad'
        build_receipt=dict(status='passed',commands=commands,source_inventory_sha256=sha(ROOT/'manifests/figure_3_rad_source_files.tsv'),binary_sha256=sha(rad_binary),identity='new executable built here from verified pinned source; binary may differ from selected execution')
        js(directory/'verified_build.json',build_receipt)
    elif sha(rad_binary)!=RAD_BINARY:
        raise ValueError('RAD executable is not the selected binary. Use --build-rad to build it explicitly from the verified119-file source; a version string alone cannot establish provenance.')
    if sha(flex_binary)!=FLEX_BINARY:raise ValueError('Flexiplex executable differs from the pinned diagnostic binary')
    dependencies=dict(line.split('==',1) for line in (ROOT/'environments/figure_3_blaze_2.6.0a0.txt').read_text().splitlines() if line and not line.startswith('#'))
    probe="import importlib.metadata,importlib.util,json,pathlib,sys; names=json.loads(sys.argv[1]); print(json.dumps({'package':str(pathlib.Path(importlib.util.find_spec('blaze').origin).parent),'version':importlib.metadata.version('blaze2'),'python':sys.version.split()[0],'dependencies':{name:{'version':importlib.metadata.version(name),'metadata':str(importlib.metadata.distribution(name)._path/'METADATA')} for name in names}}))"
    b=json.loads(subprocess.check_output([str(blaze_python),'-c',probe,json.dumps(list(dependencies))],text=True))
    if b['version']!='2.6.0a0' or b['python']!='3.9.16':raise ValueError('Selected BLAZE requires2.6.0a0 with Python3.9.16')
    for name,version in dependencies.items():
        actual=b['dependencies'][name]
        if actual['version']!=version:raise ValueError(f'BLAZE dependency differs: {name} expected{version}, observed{actual["version"]}')
        locked.append(dict(path=actual['metadata'],sha256=sha(actual['metadata']),role='BLAZE dependency version metadata'))
    for r in read(ROOT/'manifests/figure_3_blaze_source_modules.tsv'):
        if r['version']!='2.6.0a0':continue
        p=Path(b['package'])/r['module']
        if sha(p)!=r['source_sha256']:raise ValueError(f'BLAZE module differs from af8d2cc: {p}')
        locked.append(dict(path=str(p),sha256=r['source_sha256'],role='BLAZE pinned source'))
    # A venv changes the shebang only. Validate the complete executable body.
    expected_body='f6fe58083f2c9bdbcd913d502e37293f4a2b95fd58c2746a12fab0a52ca3027d'
    body=hashlib.sha256(b''.join(blaze_entrypoint.read_bytes().splitlines(keepends=True)[1:])).hexdigest()
    if body!=expected_body:raise ValueError('BLAZE entrypoint body differs from the selected CLI')
    for p,role in [(rad_binary,'RAD executable'),(blaze_python,'BLAZE Python executable'),(blaze_entrypoint,'BLAZE entrypoint'),(flex_binary,'Flexiplex diagnostic executable')]:locked.append(dict(path=str(p),sha256=sha(p),role=role))
    return dict(status='passed',source_pins=dict(RAD='cd0582b2440cde0f35725dc557fa47307d74d374',BLAZE='af8d2cc9f6374caf4d1006d5f8a0e99097211646',Flexiplex='d84c8ae4f3865052f2b5ecec816949b94682f302'),locked_files=locked,rad_binary=str(rad_binary),rad_build=build_receipt,blaze=b)

def verify_frozen_files(report):
    if report.get('status')!='passed':raise ValueError('Software verification did not pass')
    for r in report['locked_files']:
        if sha(r['path'])!=r['sha256']:raise ValueError('Verified software changed before execution: '+r['path'])
