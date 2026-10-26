#!/usr/bin/env python3
"""Extract a uniform per-read assignment table from each tool's native output.

Output (gzipped TSV, no header):  read_id, cell_barcode, umi, raw_barcode, corrected_flag

corrected_flag: 1 if the tool changed the observed barcode, 0 if the assignment was an exact match,
                . if the tool does not report enough information to tell.
raw_barcode:    the barcode as observed in the read before correction ('.' if not reported).

Tool formats
------------
rad       FASTQ.gz headers:  @<read_id>-{F,R}[-CT]<TAB>CB:Z:<bc><TAB>CR:Z:<raw><TAB>UB:Z:<umi><TAB>TS:A:<strand>
          CR:Z: is populated only when the barcode was corrected; empty means exact.
          The -F/-R/-CT suffix is a RAD orientation tag, not part of the physical read id.
blaze     matched_reads.fastq headers: @<CB>_<UMI>#<read_id>_<strand><TAB>CB:Z:<bc><TAB>UB:Z:<umi>
          raw barcode comes from the companion putative_bc.csv (read_id -> putative_bc).
flexiplex <prefix>_reads_barcodes.txt: Read, CellBarcode, FlankEditDist, BarcodeEditDist, UMI
          BarcodeEditDist == 0 means exact; > 0 means corrected. Raw barcode is not emitted by the
          stock build, so raw_barcode is '.' unless --flexiplex-raw supplies the audit-build stream.
flames    matched_reads.fastq.gz headers written by FLAMES::find_barcode (same shape as blaze).
"""
from __future__ import annotations
import argparse, gzip, io, re, sys, json
from collections import Counter

RAD_SUFFIX = re.compile(r'-(?:F|R)(?:-CT)?$')


def opener(path, mode='rt'):
    if path.endswith('.gz'):
        return gzip.open(path, mode)
    return open(path, mode)


def fastq_headers(path):
    """Yield header lines (without '@') from a possibly-gzipped FASTQ, streaming."""
    with opener(path, 'rb') as raw:
        buf = io.BufferedReader(raw, buffer_size=1 << 22)
        i = 0
        for line in buf:
            if i & 3 == 0:
                yield line[1:].rstrip(b'\n').decode('ascii', 'replace')
            i += 1


def run_rad(path, out, stats):
    for h in fastq_headers(path):
        parts = h.split('\t')
        rid = RAD_SUFFIX.sub('', parts[0])
        cb = ub = ''
        raw = ''
        for p in parts[1:]:
            if p.startswith('CB:Z:'): cb = p[5:]
            elif p.startswith('CR:Z:'): raw = p[5:]
            elif p.startswith('UB:Z:'): ub = p[5:]
        if not cb:
            stats['no_cb'] += 1; continue
        if raw:
            corrected = '1'; stats['corrected'] += 1
        else:
            corrected = '0'; raw = cb; stats['exact'] += 1
        out.write(f'{rid}\t{cb}\t{ub}\t{raw}\t{corrected}\n')
        stats['rows'] += 1


BLAZE_HDR = re.compile(r'^([ACGTN]+)_([ACGTN]*)#(.+?)_[+-]')


def load_putative(path):
    m = {}
    with opener(path, 'rt') as fh:
        head = fh.readline().rstrip('\n').split(',')
        try:
            i_rid = head.index('read_id'); i_bc = head.index('putative_bc')
        except ValueError:
            sys.stderr.write('[warn] putative_bc.csv header unexpected: %s\n' % head)
            return m
        for line in fh:
            f = line.rstrip('\n').split(',')
            if len(f) > max(i_rid, i_bc):
                m[f[i_rid]] = f[i_bc]
    return m


def run_blaze(path, out, stats, putative=None):
    put = load_putative(putative) if putative else None
    for h in fastq_headers(path):
        parts = h.split('\t')
        m = BLAZE_HDR.match(parts[0])
        if not m:
            stats['bad_header'] += 1; continue
        cb, ub, rid = m.group(1), m.group(2), m.group(3)
        for p in parts[1:]:
            if p.startswith('CB:Z:'): cb = p[5:]
            elif p.startswith('UB:Z:'): ub = p[5:]
        if put is not None:
            raw = put.get(rid, '.')
            if raw == '.':
                corrected = '.'; stats['no_raw'] += 1
            elif raw == cb:
                corrected = '0'; stats['exact'] += 1
            else:
                corrected = '1'; stats['corrected'] += 1
        else:
            raw, corrected = '.', '.'
        out.write(f'{rid}\t{cb}\t{ub}\t{raw}\t{corrected}\n')
        stats['rows'] += 1


def run_flexiplex(path, out, stats):
    """Handles both the stock build (no raw barcode) and the raw-barcode audit build.

    The audit build (flexiplex 1.02.6+d84c8ae) adds a RawCellBarcode column carrying the barcode
    as observed in the read before correction. Without it the A-to-B audit subset cannot be
    identified for Flexiplex at all, so the audit build is the preferred input; when it is used,
    both the barcode assignment and the raw barcode come from the SAME flexiplex run.
    """
    with opener(path, 'rt') as fh:
        head = fh.readline().rstrip('\n').split('\t')
        idx = {k: i for i, k in enumerate(head)}
        for k in ('Read', 'CellBarcode', 'UMI', 'BarcodeEditDist'):
            if k not in idx:
                sys.stderr.write(f'[fatal] flexiplex column {k} missing: {head}\n'); sys.exit(2)
        iR, iC, iU, iE = idx['Read'], idx['CellBarcode'], idx['UMI'], idx['BarcodeEditDist']
        iRaw = idx.get('RawCellBarcode')
        if iRaw is None:
            sys.stderr.write('[warn] no RawCellBarcode column: this is the STOCK flexiplex build. '
                             'raw_barcode will be "." and the A-to-B audit subset CANNOT be '
                             'identified for this tool.\n')
        n = max(iR, iC, iU, iE, iRaw if iRaw is not None else 0)
        for line in fh:
            f = line.rstrip('\n').split('\t')
            if len(f) <= n:
                stats['short_row'] += 1; continue
            try:
                ed = int(f[iE])
            except ValueError:
                ed = -1
            if ed == 0:
                corrected = '0'; stats['exact'] += 1
            elif ed > 0:
                corrected = '1'; stats['corrected'] += 1
            else:
                corrected = '.'
            raw = f[iRaw] if iRaw is not None and f[iRaw] else '.'
            if iRaw is not None and raw == '.':
                stats['no_raw'] += 1
            out.write(f'{f[iR]}\t{f[iC]}\t{f[iU]}\t{raw}\t{corrected}\n')
            stats['rows'] += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tool', required=True, choices=['rad', 'blaze', 'flexiplex', 'flames'])
    ap.add_argument('--input', required=True)
    ap.add_argument('--putative', default=None, help='blaze putative_bc.csv')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    stats = Counter()
    with gzip.open(a.out, 'wt', compresslevel=1) as out:
        if a.tool == 'rad':
            run_rad(a.input, out, stats)
        elif a.tool in ('blaze', 'flames'):
            run_blaze(a.input, out, stats, a.putative)
        else:
            run_flexiplex(a.input, out, stats)
    with open(a.out + '.stats.json', 'w') as fh:
        json.dump(dict(stats), fh, indent=2, sort_keys=True)
    sys.stderr.write(json.dumps(dict(stats), indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
