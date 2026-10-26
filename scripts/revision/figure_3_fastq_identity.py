#!/usr/bin/env python3
"""Fingerprint every ordered FASTQ record, independent of gzip recompression.

Canonical records include physical ID, sequence and quality. A separate digest
omits IDs to diagnose renamed reads; it does not by itself authorize replacement.
"""
import argparse,contextlib,gzip,hashlib,json,subprocess
from pathlib import Path
from figure_3 import sha,js

def fingerprint(source,report_path,ids_output=None):
    compressed=sha(source);exact=hashlib.sha256();canonical=hashlib.sha256();sequence_quality=hashlib.sha256();id_order=hashlib.sha256()
    ids=set();records=0;bases=0;duplicates=0
    with contextlib.ExitStack() as stack:
        saved=None
        if ids_output:
            ids_output.parent.mkdir(parents=True,exist_ok=True);temporary=ids_output.with_suffix(ids_output.suffix+'.tmp')
            raw=stack.enter_context(temporary.open('wb'));saved=stack.enter_context(gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0))
        proc=stack.enter_context(subprocess.Popen(['pigz','-dc','-p','2',str(source)],stdout=subprocess.PIPE))
        stream=proc.stdout
        while True:
            header=stream.readline()
            if not header:break
            seq_line=stream.readline();plus=stream.readline();quality_line=stream.readline()
            seq=seq_line.rstrip(b'\r\n');quality=quality_line.rstrip(b'\r\n')
            if not header.startswith(b'@') or not plus.startswith(b'+') or not quality_line or len(seq)!=len(quality):raise ValueError(f'Malformed FASTQ record{records+1}')
            rid=header[1:].split()[0]
            if not rid:raise ValueError('Empty physical read ID')
            duplicates+=rid in ids;ids.add(rid);records+=1;bases+=len(seq)
            for line in [header,seq_line,plus,quality_line]:exact.update(line)
            payload=len(seq).to_bytes(8,'big')+seq+quality
            sequence_quality.update(payload);canonical.update(len(rid).to_bytes(8,'big')+rid+payload);id_order.update(rid+b'\n')
            if saved:saved.write(rid+b'\n')
            if records%5000000==0:print(json.dumps({'records_processed':records}),flush=True)
        if proc.wait():raise ValueError('FASTQ decompression failed')
    if ids_output:temporary.replace(ids_output)
    report=dict(status='passed' if duplicates==0 else 'duplicate_input_ids',source=str(source),compressed_sha256=compressed,compressed_bytes=source.stat().st_size,records=records,unique_original_ids=len(ids),duplicate_original_ids=duplicates,sequence_bases=bases,exact_decompressed_fastq_sha256=exact.hexdigest(),canonical_record_sha256=canonical.hexdigest(),canonical_record_encoding='For each ordered record: uint64be ID byte length, ID bytes (first header token without @), uint64be sequence length, sequence bytes, quality bytes. Strip CR/LF line endings only. Header descriptions and plus-line annotations excluded.',sequence_quality_order_sha256=sequence_quality.hexdigest(),sequence_quality_encoding='For each ordered record: uint64be sequence length, sequence bytes, quality bytes; IDs excluded. Diagnostic only, not sufficient alone to replace input.',original_id_order_sha256=id_order.hexdigest(),input_ids_sha256=sha(ids_output) if ids_output else None,input_ids_path=str(ids_output) if ids_output else None,script_sha256=sha(__file__))
    js(report_path,report);print(json.dumps(report),flush=True)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path);p.add_argument('--report',type=Path,required=True);p.add_argument('--ids-output',type=Path);a=p.parse_args()
    report=fingerprint(a.input,a.report,a.ids_output)
    if report['duplicate_original_ids']:raise SystemExit('Input contains duplicate physical read IDs')
if __name__=='__main__':main()
