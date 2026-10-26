#!/usr/bin/env python3
"""Download the ENA-submitted RAGE FASTQ and verify its published MD5.

This file has a different read order from the selected experiment. Downloading
it alone is not an exact replay; follow the input-order reconstruction guide.
Range requests can resume completed chunks without restarting the whole file.
"""
import argparse
import concurrent.futures
import hashlib
import json
import subprocess
from pathlib import Path

URL = 'https://ftp.sra.ebi.ac.uk/vol1/run/ERR326/ERR3268991/ramos_nanopore.fastq.gz'
BYTES = 16675472857
MD5 = '93bdd7b64877d96f38720aea13c92bdc'


def hashes(path):
    md5, sha = hashlib.md5(), hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(4*1024*1024), b''):
            md5.update(block)
            sha.update(block)
    return md5.hexdigest(), sha.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--connections', type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.connections <= 8:
        parser.error('Use 1 to 8 connections.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    parts = args.output.parent/(args.output.name+'.parts')
    parts.mkdir(exist_ok=True)
    chunk_size = 512*1024*1024

    def fetch(index):
        start = index*chunk_size
        end = min(start+chunk_size, BYTES)-1
        target = parts/('{:03d}'.format(index))
        if not target.is_file() or target.stat().st_size != end-start+1:
            temporary = target.with_suffix('.partial')
            subprocess.run(['curl','--fail','--location','--silent','--show-error',
                '--retry','3','--connect-timeout','30','--max-time','5400',
                '--max-filesize',str(end-start+1),'--range',str(start)+'-'+str(end),
                '--dump-header',str(target.with_suffix('.headers')),
                '--output',str(temporary),URL], check=True)
            if temporary.stat().st_size != end-start+1:
                raise ValueError('Incomplete or unhonored byte range '+str(index))
            temporary.replace(target)
        print('Verified chunk size', index, end-start+1, flush=True)
        return target

    if args.output.exists():
        if args.output.stat().st_size != BYTES:
            raise ValueError('Existing output is incomplete; keep it separately before using this chunk downloader.')
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.connections) as executor:
            chunks = list(executor.map(fetch, range((BYTES+chunk_size-1)//chunk_size)))
        temporary = args.output.with_suffix(args.output.suffix+'.partial')
        with temporary.open('wb') as destination:
            for chunk in chunks:
                with chunk.open('rb') as source:
                    for block in iter(lambda: source.read(4*1024*1024), b''):
                        destination.write(block)
        if temporary.stat().st_size != BYTES or hashes(temporary)[0] != MD5:
            raise ValueError('Complete ENA byte count or published MD5 mismatch')
        temporary.replace(args.output)
    md5, sha = hashes(args.output)
    if md5 != MD5:
        raise ValueError('Published ENA MD5 mismatch')
    receipt = dict(status='passed', accession='ERR3268991', source_kind='ENA submitted file',
        url=URL, bytes=BYTES, md5=md5, sha256=sha, output=str(args.output.resolve()),
        selected_input_order='different; exact experiment requires order reconstruction and canonical record validation')
    args.output.with_suffix('.acquisition.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
