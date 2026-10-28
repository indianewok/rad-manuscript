#!/usr/bin/env python3
"""Validate the recovered selected RAD emitted-assignment checkpoint in full."""
import argparse,collections,csv,datetime,gzip,hashlib,json,os,socket
from pathlib import Path
from source_paths import reviewer_root
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--input',type=Path,default=reviewer_root() / 'scratch_preservation_20260921/files/SN_ONT_RAD_4acbe00_full_matrix_rebuild_20260828/assignments/RAD_4acbe00.assign.tsv.gz')
p.add_argument('--barcodes',type=Path,default=ROOT/'checkpoints/figure_07/native/RAD/all/barcodes.tsv.gz')
a=p.parse_args();started=datetime.datetime.utcnow().isoformat()+'Z'
h=hashlib.sha256()
with a.input.open('rb') as f:
    for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
digest=h.hexdigest();expected='a5dc369445826fdd36541a301b1b85448438fb52d351ce8883a12ef456457c48'
assert digest==expected, 'Recovered assignment compressed-byte SHA mismatch'
with gzip.open(str(a.barcodes),'rt') as f: selected=set(x.strip() for x in f)
assert len(selected)==12423
counts=collections.Counter();flags=collections.Counter();lengths=collections.Counter();first=[];n=0
with gzip.open(str(a.input),'rt') as f:
    for ordinal,line in enumerate(f,1):
        fields=line.rstrip('\n').split('\t');assert len(fields)==5,(ordinal,len(fields))
        read,cell,umi,raw,flag=fields
        assert read and cell in selected and flag in ('0','1'), ordinal
        assert raw,ordinal
        if flag=='0':assert raw==cell,ordinal
        n+=1;counts[cell]+=1;flags[flag]+=1;lengths[len(umi)]+=1
        if len(first)<10:first.append(dict(source_data_row=ordinal,original_read_id=read,cell_barcode=cell,UMI=umi,raw_barcode=raw,corrected_flag=flag))
assert n==57885606,n
assert flags=={'0':49555699,'1':8329907},dict(flags)
def write(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
example=ROOT/'data/examples/figure_07'
write(example/'RAD_emitted_assignment_rows.tsv',first)
write(ROOT/'source_data/figure_07/RAD_assignment_rows_by_barcode.tsv',[dict(cell_barcode=cell,emitted_assignment_rows=counts[cell],selected=1) for cell in sorted(selected)])
receipt=dict(status='passed',source=str(a.input),source_bytes=a.input.stat().st_size,source_sha256=digest,
    recorded_expected_sha256=expected,complete_gzip_stream_valid=True,assignment_rows=n,
    exact_flag_rows=flags['0'],corrected_flag_rows=flags['1'],selected_barcodes=len(selected),observed_barcodes=len(counts),UMI_length_histogram=dict(lengths),
    schema=['original_read_id','cell_barcode','UMI','raw_barcode','corrected_flag'],
    source_row_scope='all emitted assignments including concatemer records; not unique physical reads',
    limits='Extractor removed orientation/-CT suffixes. No gene IDs, segment coordinates or original record labels are retained. Frozen read-gene input and emitted FASTQ are still missing; no matrix replay or explicit CT ledger is claimed.',
    example_selection='first10 actual rows after full SHA/schema/count validation; public SN_ONT cell-line mixture',
    source_barcodes=str(a.barcodes),source_barcodes_sha256=hashlib.sha256(a.barcodes.read_bytes()).hexdigest(),
    host=socket.gethostname(),slurm_job_id=os.environ.get('SLURM_JOB_ID'),start_utc=started,finish_utc=datetime.datetime.utcnow().isoformat()+'Z')
(ROOT/'validation/figures_567_assignment_recovery.json').write_text(json.dumps(receipt,indent=2)+'\n')
(example/'assignment_extraction.json').write_text(json.dumps({k:receipt[k] for k in ('source','source_bytes','source_sha256','schema','example_selection','source_row_scope','limits')},indent=2)+'\n')
print('Recovered selected assignment checkpoint verified:',n,'rows;',digest)
