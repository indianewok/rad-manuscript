#!/usr/bin/env python3
"""Assign each aligned read to at most one gene, once per arm, shared by every tool.

Feature-assignment rules (IDENTICAL for every tool by construction, since this runs once on the
single shared BAM):
  * primary alignments only (no secondary, no supplementary), mapped, MAPQ >= MIN_MAPQ
  * a read is assigned to the gene whose exonic-union footprint it overlaps by the most bases
  * strand-agnostic: raw 10x ONT cDNA reads occur in both orientations and were NOT re-oriented
    before alignment, so requiring strand concordance would drop antisense-oriented reads
    unevenly. Strand is therefore ignored identically for all tools.
  * if the best and second-best gene overlaps tie exactly, the read is AMBIGUOUS and discarded
  * reads overlapping no gene are UNASSIGNED and discarded

Output: <out_prefix>.readgene.tsv.gz  (read_id <TAB> gene_index)
        <out_prefix>.genes.tsv        (gene_index <TAB> gene_id <TAB> gene_name <TAB> gene_type)
        <out_prefix>.stats.json
"""
from __future__ import annotations
import argparse, gzip, json, sys, os
from collections import defaultdict
import numpy as np
import pysam

MIN_MAPQ = 1


def load_gtf_exons(gtf_path):
    """Return per-chrom sorted exon interval arrays + gene metadata."""
    genes = {}           # gene_id -> index
    gmeta = []           # index -> (gene_id, gene_name, gene_type)
    per_chrom = defaultdict(list)   # chrom -> list of (start, end, gene_idx)
    opener = gzip.open if gtf_path.endswith('.gz') else open
    with opener(gtf_path, 'rt') as fh:
        for line in fh:
            if line[0] == '#':
                continue
            f = line.rstrip('\n').split('\t')
            if len(f) < 9 or f[2] != 'exon':
                continue
            attr = f[8]
            def get(key):
                i = attr.find(key + ' "')
                if i < 0:
                    return None
                i += len(key) + 2
                j = attr.find('"', i)
                return attr[i:j]
            gid = get('gene_id')
            if gid is None:
                continue
            gi = genes.get(gid)
            if gi is None:
                gi = len(gmeta)
                genes[gid] = gi
                gmeta.append((gid, get('gene_name') or gid, get('gene_type') or 'NA'))
            per_chrom[f[0]].append((int(f[3]) - 1, int(f[4]), gi))   # BED-like half-open
    packed = {}
    for chrom, iv in per_chrom.items():
        iv.sort(key=lambda x: x[0])
        packed[chrom] = (
            np.fromiter((x[0] for x in iv), dtype=np.int64, count=len(iv)),
            np.fromiter((x[1] for x in iv), dtype=np.int64, count=len(iv)),
            np.fromiter((x[2] for x in iv), dtype=np.int32, count=len(iv)),
        )
    # running max of ends, so an interval scan can stop early
    for chrom, (s, e, g) in packed.items():
        packed[chrom] = (s, e, g, np.maximum.accumulate(e))
    return packed, gmeta


def read_blocks(aln):
    """Aligned reference blocks (skips N/introns and D>0 handled by get_blocks)."""
    return aln.get_blocks()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bam', required=True)
    ap.add_argument('--gtf', required=True)
    ap.add_argument('--out-prefix', required=True)
    ap.add_argument('--max-reads', type=int, default=0)
    ap.add_argument('--region', default=None,
                    help='restrict to one reference contig; enables per-contig parallelism. '
                         'Results are identical to a whole-BAM run because gene assignment is '
                         'per-read and never crosses contigs.')
    a = ap.parse_args()

    sys.stderr.write('[assign_genes] loading GTF exons\n'); sys.stderr.flush()
    packed, gmeta = load_gtf_exons(a.gtf)
    if a.region:
        packed = {k: v for k, v in packed.items() if k == a.region}
    sys.stderr.write(f'[assign_genes] {len(gmeta)} genes, {len(packed)} contigs\n'); sys.stderr.flush()

    with open(a.out_prefix + '.genes.tsv', 'w') as fh:
        fh.write('gene_index\tgene_id\tgene_name\tgene_type\n')
        for i, (gid, gname, gtype) in enumerate(gmeta):
            fh.write(f'{i}\t{gid}\t{gname}\t{gtype}\n')

    stats = defaultdict(int)
    bam = pysam.AlignmentFile(a.bam, 'rb', threads=4)
    out = gzip.open(a.out_prefix + '.readgene.tsv.gz', 'wt', compresslevel=1)

    itr = bam.fetch(a.region) if a.region else bam.fetch(until_eof=True)
    for aln in itr:
        stats['records'] += 1
        if a.max_reads and stats['records'] > a.max_reads:
            break
        if aln.is_unmapped:
            stats['unmapped'] += 1; continue
        if aln.is_secondary or aln.is_supplementary:
            stats['non_primary'] += 1; continue
        if aln.mapping_quality < MIN_MAPQ:
            stats['low_mapq'] += 1; continue
        chrom = aln.reference_name
        arr = packed.get(chrom)
        if arr is None:
            stats['no_contig'] += 1; continue
        starts, ends, gidx, maxend = arr

        cover = defaultdict(int)
        for bs, be in read_blocks(aln):
            # candidate exons: those beginning before the block ends
            hi = np.searchsorted(starts, be, side='right')
            if hi == 0:
                continue
            lo = int(np.searchsorted(maxend[:hi], bs, side='right'))
            if lo >= hi:
                continue
            s = starts[lo:hi]; e = ends[lo:hi]; g = gidx[lo:hi]
            ov = np.minimum(e, be) - np.maximum(s, bs)
            m = ov > 0
            if not m.any():
                continue
            for gg, oo in zip(g[m], ov[m]):
                cover[int(gg)] += int(oo)

        if not cover:
            stats['no_gene'] += 1; continue
        if len(cover) == 1:
            best = next(iter(cover))
        else:
            ranked = sorted(cover.items(), key=lambda kv: -kv[1])
            if ranked[0][1] == ranked[1][1]:
                stats['ambiguous'] += 1; continue
            best = ranked[0][0]
        stats['assigned'] += 1
        out.write(f'{aln.query_name}\t{best}\n')

    out.close(); bam.close()
    stats = dict(stats)
    stats['n_genes'] = len(gmeta)
    stats['min_mapq'] = MIN_MAPQ
    with open(a.out_prefix + '.stats.json', 'w') as fh:
        json.dump(stats, fh, indent=2, sort_keys=True)
    sys.stderr.write(json.dumps(stats, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
