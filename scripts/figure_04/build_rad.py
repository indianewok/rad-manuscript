#!/usr/bin/env python3
"""Build RAD from the exact Figure4 source checkout and record its identity.

The executable hash is specific to your compiler and dependencies. This helper
checks the source commit, refuses tracked changes and an existing build folder,
and records the actual CMake commands, logs and resulting executable hash.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

RAD_COMMIT='4acbe004ba11b150d6832395452632f367a6e6c1'


def require(condition,message):
    if not condition:raise ValueError(message)


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda:handle.read(8*1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def git(source,*args):
    return subprocess.check_output(['git','-C',str(source),*args],text=True).strip()


def verify_source(source):
    source=Path(source).resolve()
    require(git(source,'rev-parse','HEAD')==RAD_COMMIT,'RAD source must be checked out at '+RAD_COMMIT)
    require(not git(source,'status','--porcelain','--untracked-files=no'),
            'RAD source has tracked modifications; use a clean pinned checkout')
    require((source/'src/main.cpp').is_file() and (source/'CMakeLists.txt').is_file(),
            'Not a complete RAD source checkout')
    return git(source,'rev-parse','HEAD^{tree}')


def verify_build(rad,source,receipt_path,expected_sha256=None):
    receipt=json.loads(Path(receipt_path).read_text());actual=sha(rad)
    require(receipt.get('status')=='passed' and receipt.get('rad_commit')==RAD_COMMIT
            and receipt.get('built_from_verified_source') is True and receipt.get('fresh_build_directory') is True,
            'Unverified RAD build receipt')
    require(Path(receipt['source_dir']).resolve()==Path(source).resolve(),
            'Build receipt belongs to another source checkout')
    require(receipt['source_tree']==verify_source(source),'RAD source tree differs from the verified build')
    require(Path(receipt['rad_path']).resolve()==Path(rad).resolve() and receipt['rad_sha256']==actual,
            'Executable differs from its verified source build')
    require(receipt.get('build_helper_sha256')==sha(__file__),'Build helper identity differs from this public recipe')
    build=Path(receipt['build_dir'])
    for name,digest in receipt['logs'].items():
        require(sha(build/name)==digest,'Build log changed: '+name)
    require(expected_sha256 is None or actual==expected_sha256,'Executable differs from the optional binary pin')
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rad-source',type=Path,required=True)
    parser.add_argument('--build-dir',type=Path,required=True)
    parser.add_argument('--threads',type=int,required=True)
    args=parser.parse_args();source=args.rad_source.resolve();build=args.build_dir.resolve()
    require(args.threads>0,'Threads must be positive')
    tree=verify_source(source)
    require(not build.exists(),'Build directory must be new; a cached executable is not accepted')
    build.mkdir(parents=True,exist_ok=False)
    commands=[['cmake','-S',str(source),'-B',str(build),'-DCMAKE_BUILD_TYPE=Release'],
              ['cmake','--build',str(build),'--target','rad','--parallel',str(args.threads)]]
    for name,command in zip(['configure.log','build.log'],commands):
        with (build/name).open('x') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
    require(verify_source(source)==tree,'Source changed during compilation')
    rad=build/'rad';require(rad.is_file(),'CMake did not produce the expected rad executable')
    receipt=dict(status='passed',rad_commit=RAD_COMMIT,source_tree=tree,source_dir=str(source),
        build_dir=str(build),rad_path=str(rad),rad_sha256=sha(rad),built_from_verified_source=True,
        fresh_build_directory=True,commands=commands,
        cmake_version=subprocess.check_output(['cmake','--version'],text=True).splitlines()[0],
        build_helper_sha256=sha(__file__),
        logs={name:sha(build/name) for name in ['configure.log','build.log','CMakeCache.txt']},
        completed_utc=datetime.now(timezone.utc).isoformat())
    (build/'build_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('Verified RAD build:',rad,'SHA256',receipt['rad_sha256'])
    print('Build receipt:',build/'build_receipt.json')


if __name__=='__main__':main()
