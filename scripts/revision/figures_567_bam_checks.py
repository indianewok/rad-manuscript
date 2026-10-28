#!/usr/bin/env python3
"""Hash retained BAM/BAI bytes, quickcheck boundaries, and export index/header evidence.

Quickcheck and index queries are explicitly not a full decoded-record validation.
The separate SHA-256 covers every compressed byte in each retained BAM.
"""
import argparse
import json
from pathlib import Path
from source_paths import reviewer_root
import subprocess
from figures_567 import sha, write

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--project-root',type=Path,default=reviewer_root())
parser.add_argument('--output-root',type=Path,default=Path(__file__).resolve().parents[2])
parser.add_argument('--samtools',default='samtools')
a=parser.parse_args()
root=a.project_root/'scratch_preservation_20260921/files'
paths={t:root/('longbench_snont_postdemux_vireo_20260803/align/'+t+'/align2genome.bam') for t in ('RAD','Flexiplex')}
paths['BLAZE']=root/'longbench_full_demux_20260730/runs/flames2.0.1_longbench_published/SN_ONT/align2genome.bam'
results=[]
for tool,path in paths.items():
    index=Path(str(path)+'.bai')
    subprocess.check_call([a.samtools,'quickcheck','-v',str(path)])
    header=subprocess.check_output([a.samtools,'view','-H',str(path)],universal_newlines=True)
    stats=subprocess.check_output([a.samtools,'idxstats',str(path)],universal_newlines=True)
    dest=a.output_root/'source_data/figure_06'
    (dest/(tool+'_alignment_header.sam')).write_text(header)
    (dest/(tool+'_alignment_idxstats.tsv')).write_text(stats)
    sq={}
    for line in header.splitlines():
        if line.startswith('@SQ\t'):
            fields=dict(x.split(':',1) for x in line.split('\t')[1:]);sq[fields['SN']]=int(fields['LN'])
    observed={line.split('\t')[0]:int(line.split('\t')[1]) for line in stats.splitlines() if not line.startswith('*\t')}
    assert sq==observed,'BAM/index reference names or lengths differ'
    results.append(dict(tool=tool,bam=str(path),bam_bytes=path.stat().st_size,bam_sha256=sha(path),index_sha256=sha(index),quickcheck='passed',index_header_contig_identity='passed',full_decoded_record_scan='not_run',boundary='Complete compressed-byte hash; quickcheck boundaries and index/header identity only; no full decoded-record or per-record CB/UB audit'))
    write(a.output_root/'validation/figures_567_bam_checks.tsv',results)
    print(tool+' BAM/BAI bytes hashed and index/header checked',flush=True)
(a.output_root/'validation/figures_567_bam_tool.json').write_text(json.dumps({'samtools_path':a.samtools,'samtools_sha256':sha(a.samtools),'version':subprocess.check_output([a.samtools,'--version'],universal_newlines=True)},indent=2)+'\n')
