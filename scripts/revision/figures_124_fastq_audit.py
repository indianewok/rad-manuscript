#!/usr/bin/env python3
"""Full source FASTQ identity audit; no generation or demultiplexing."""
import argparse
import gzip
import hashlib
import os
import re
import sys
import time
from pathlib import Path
import numpy as np
from figures_124 import REPO, sha, write_json


def inspect(path,flat=False):
    start=time.time();header_sequence=hashlib.sha256();quality=hashlib.sha256()
    seen=set();truth=set();n=0;bases=0;hist=np.zeros(256,dtype=np.int64);buffer=bytearray()
    with gzip.open(path,'rb') as f:
        while True:
            h=f.readline()
            if not h:break
            s=f.readline();p=f.readline();q=f.readline()
            if not s or not p or not q:raise ValueError('truncated FASTQ: '+str(path))
            h,s,p,q=(x.rstrip(b'\r\n') for x in (h,s,p,q))
            if not h.startswith(b'@') or not p.startswith(b'+') or len(s)!=len(q):
                raise ValueError('malformed FASTQ: '+str(path))
            rid=h.split()[0]
            if rid in seen:raise ValueError('duplicate physical read ID: '+str(rid))
            match=re.match(rb'^@([ACGT]{16})-[0-9]+$',rid)
            if not match:raise ValueError('unrecognized truth-bearing read ID: '+str(rid))
            seen.add(rid);truth.add(match.group(1));n+=1;bases+=len(s)
            header_sequence.update(h+b'\n'+s.upper()+b'\n');quality.update(q+b'\n')
            if flat:
                if q.strip(b'5'):raise ValueError('flatQ20 file has other quality characters')
                hist[53]+=len(q)
            else:
                buffer.extend(q)
                if len(buffer)>=8*1024*1024:
                    hist+=np.bincount(np.frombuffer(buffer,dtype=np.uint8),minlength=256)
                    buffer=bytearray()
            if n%1000000==0:print(path.name,n,'records',round(time.time()-start,1),'seconds',flush=True)
    if buffer:hist+=np.bincount(np.frombuffer(buffer,dtype=np.uint8),minlength=256)
    qs=np.flatnonzero(hist)-33
    if min(qs)<0 or max(qs)>93:raise ValueError('invalid quality range')
    return dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path),reads=n,bases=bases,
                unique_read_ids=len(seen),truth_barcodes=len(truth),malformed_records=0,
                gzip_crc_checked_by_complete_stream_read=True,header_sequence_sha256=header_sequence.hexdigest(),
                quality_sha256=quality.hexdigest(),min_q=int(min(qs)),max_q=int(max(qs)),
                mean_q=float(sum((i-33)*int(v) for i,v in enumerate(hist))/bases),
                quality_histogram={str(i-33):int(v) for i,v in enumerate(hist) if v},elapsed_seconds=time.time()-start)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root',type=Path,default=Path('/dartfs/rc/lab/A/AckermanLab/CMV/rad_data'))
    p.add_argument('--output-root',type=Path,default=REPO)
    a=p.parse_args();b=a.project_root/'reviewer_comment_data/scratch_preservation_20260921/files'
    sources={'S_flatQ20':b/'rad_longbench_20260726/data/shuffled_S_lr_synth.fq.gz',
             'L_flatQ20':b/'rad_longbench_20260726/data/shuffled_L_lr_synth.fq.gz',
             'L_native2023':b/'sctagger_nanopore2023_unadjusted_20260913/inputs/L_variants/shuffled_L_lr_synth.nanopore2023_truthbc.native_unadjusted.fq.gz'}
    result={'command':[sys.executable,*sys.argv],'script_sha256':sha(Path(__file__)),'numpy':np.__version__,
            'job_id':os.environ.get('SLURM_JOB_ID'),'cpus':os.environ.get('SLURM_CPUS_PER_TASK'),'host':os.uname().nodename,
            'scope':'complete retained FASTQ byte/content verification; no raw tool rerun','sources':{}}
    target=a.output_root/'validation/figures_124_fastq_identity.json'
    for name,path in sources.items():
        r=inspect(path,'flatQ20' in name)
        expected=(98873,320489068,50) if name=='S_flatQ20' else (4993805,8394808882,5000)
        got=(r['reads'],r['bases'],r['truth_barcodes'])
        if got!=expected:raise ValueError((name,got,expected))
        result['sources'][name]=r;write_json(target,result)
    native=result['sources']['L_native2023'];source=result['sources']['L_flatQ20']
    if native['header_sequence_sha256']!=source['header_sequence_sha256'] or native['header_sequence_sha256']!='ca3073f0a44d03b40a5919e01e59a8df89ceceafa086ee7580fae2daa3bf2f61':
        raise ValueError('source/native ordered header-sequence mismatch')
    if native['sha256']!='69b3da301d03d57f3932cfe2d227cc4c0a63ad45191d48eead36d00171471f67' or native['quality_sha256']!='1356a4993a6cc31ca80857f99d105da376534d594112588af4e32b3cdf138841':
        raise ValueError('native quality/byte identity mismatch')
    if native['min_q']!=1 or native['max_q']!=90 or abs(native['mean_q']-31.669502288616844)>1e-12:
        raise ValueError('native quality distribution mismatch')
    result['status']='passed';write_json(target,result);print('Full FASTQ identity audit passed',flush=True)


if __name__=='__main__':main()
