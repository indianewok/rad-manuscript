#!/usr/bin/env python3
"""Build cell x gene count matrices from a shared read->gene table plus per-tool read assignments.

Every matrix state for every tool is produced by THIS script from THE SAME read->gene table, so
reference, aligner, feature-assignment rules, UMI collapsing and gene filtering are identical by
construction and cannot differ between tools.

Matrix states produced per tool (nested removals, all on the SAME selected cells):
  all        every read the tool assigned to a selected cell
  exact      only reads the tool assigned WITHOUT error correction
  noAB       'all' minus CROSS-CELL theft: reads whose pre-correction barcode was itself a
             DIFFERENT CellRanger cell ("missed CellRanger cell A -> different cell B")
  noAmbient  'all' minus AMBIENT ABSORPTION: reads whose pre-correction barcode was an exact,
             valid member of the 10x barcode catalogue but is NOT a called cell in this dataset.
             These are empty-droplet / non-cell-associated molecules being corrected into a real
             cell, and they are the dominant contamination class for BLAZE and Flexiplex.
  noContam   'all' minus BOTH of the above -- i.e. keeping exact matches plus only the benign
             corrections, those whose observed barcode was not a real 10x barcode at all
             (genuine sequencing-error rescue).

The three removal states are deliberately reported separately rather than summed: a read can be
counted in only one of noAB / noAmbient (the source is either a called cell or it is not), but
keeping them apart makes the biological cost of each mechanism separately attributable.

UMI collapsing: a (cell_barcode, gene, UMI) triple counts once. UMIs are compared exactly; reads
with an empty UMI are counted individually (they cannot be collapsed) and are tallied separately.

Also writes, once per arm, the tool-neutral RAW DROPLET matrix used as the common ambient/soup
reference: every read whose observed (pre-correction) barcode is an exact member of the 10x
catalogue, assigned to that barcode with no correction of any kind. This is a purely mechanical,
selection-free assignment, so the soup profile is a property of the experiment rather than of any
one tool.

Outputs 10x-style MatrixMarket triplets per state: matrix.mtx.gz, barcodes.tsv.gz, features.tsv.gz
"""
from __future__ import annotations
import argparse, gzip, json, os, sys
from collections import defaultdict
import numpy as np
import scipy.sparse as sp
import scipy.io


def log(m):
    sys.stderr.write(f'[{__file__.split("/")[-1]}] {m}\n'); sys.stderr.flush()


def load_readgene(path):
    """read_id -> gene_index."""
    d = {}
    with gzip.open(path, 'rt') as fh:
        for line in fh:
            i = line.rfind('\t')
            d[line[:i]] = int(line[i + 1:])
    return d


def load_set(path, strip_suffix=True):
    s = set()
    op = gzip.open if path.endswith('.gz') else open
    with op(path, 'rt') as fh:
        for line in fh:
            b = line.strip()
            if not b:
                continue
            if strip_suffix:
                b = b.split('-')[0]
            s.add(b)
    return s


def write_10x(outdir, counts, genes_meta, umi_less):
    """counts: dict (cb, gene_idx) -> count."""
    os.makedirs(outdir, exist_ok=True)
    if not counts:
        log(f'  !! no counts for {outdir}')
        return 0, 0
    cbs = sorted({cb for cb, _ in counts})
    cb_i = {c: i for i, c in enumerate(cbs)}
    gset = sorted({g for _, g in counts})
    g_i = {g: i for i, g in enumerate(gset)}
    rows = np.empty(len(counts), dtype=np.int64)   # genes
    cols = np.empty(len(counts), dtype=np.int64)   # cells
    vals = np.empty(len(counts), dtype=np.int64)
    for k, ((cb, g), v) in enumerate(counts.items()):
        rows[k] = g_i[g]; cols[k] = cb_i[cb]; vals[k] = v
    m = sp.coo_matrix((vals, (rows, cols)), shape=(len(gset), len(cbs)), dtype=np.int64)
    with gzip.open(os.path.join(outdir, 'matrix.mtx.gz'), 'wb') as fh:
        scipy.io.mmwrite(fh, m, field='integer')
    with gzip.open(os.path.join(outdir, 'barcodes.tsv.gz'), 'wt') as fh:
        for c in cbs:
            fh.write(c + '\n')
    with gzip.open(os.path.join(outdir, 'features.tsv.gz'), 'wt') as fh:
        for g in gset:
            gid, gname, gtype = genes_meta[g]
            fh.write(f'{gid}\t{gname}\t{gtype}\n')
    with open(os.path.join(outdir, 'matrix_stats.json'), 'w') as fh:
        json.dump({'n_cells': len(cbs), 'n_genes': len(gset), 'n_nonzero': int(m.nnz),
                   'total_umis': int(vals.sum()), 'reads_without_umi': umi_less}, fh, indent=2)
    return len(cbs), len(gset)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--readgene', required=True)
    ap.add_argument('--genes', required=True)
    ap.add_argument('--assignments', required=True, help='per-read table from extract_assignments.py')
    ap.add_argument('--tool', required=True)
    ap.add_argument('--arm', required=True)
    ap.add_argument('--cellranger-filtered', required=True)
    ap.add_argument('--global-catalog', default=None,
                    help='10x barcode catalogue (e.g. 3M-february-2018-3v3.txt). Required for the '
                         'noAmbient / noContam states: without it there is no way to tell an '
                         'ambient valid-barcode source from a sequencing-error barcode.')
    ap.add_argument('--outdir', required=True)
    ap.add_argument('--states', default='all,exact,noAB,noAmbient,noContam')
    a = ap.parse_args()

    genes_meta = {}
    with open(a.genes) as fh:
        fh.readline()
        for line in fh:
            f = line.rstrip('\n').split('\t')
            genes_meta[int(f[0])] = (f[1], f[2], f[3])
    log(f'{len(genes_meta)} genes')

    log('loading read->gene table')
    r2g = load_readgene(a.readgene)
    log(f'{len(r2g):,} reads with a gene call')

    cr_cells = load_set(a.cellranger_filtered)
    log(f'{len(cr_cells):,} CellRanger filtered cells')

    catalog = None
    if a.global_catalog:
        catalog = load_set(a.global_catalog, strip_suffix=False)
        log(f'{len(catalog):,} barcodes in the 10x global catalogue')
    need_cat = {'noAmbient', 'noContam'} & set(a.states.split(','))
    if need_cat and catalog is None:
        sys.exit(f'--global-catalog is required for states {sorted(need_cat)}')

    states = a.states.split(',')
    seen = {s: set() for s in states}          # (cb, gene, umi) dedup
    counts = {s: defaultdict(int) for s in states}
    umiless = {s: 0 for s in states}
    stats = defaultdict(int)

    with gzip.open(a.assignments, 'rt') as fh:
        for line in fh:
            f = line.rstrip('\n').split('\t')
            if len(f) < 5:
                stats['malformed'] += 1; continue
            rid, cb, umi, raw, corr = f[0], f[1], f[2], f[3], f[4]
            g = r2g.get(rid)
            stats['rows'] += 1
            if g is None:
                stats['no_gene'] += 1; continue
            stats['with_gene'] += 1

            is_exact = (corr == '0')
            have_raw = (corr == '1' and raw not in ('.', '') and raw != cb)
            # A->B: pre-correction barcode was a DIFFERENT CellRanger cell than the assigned cell
            is_ab = (have_raw and raw in cr_cells and cb in cr_cells)
            # ambient: pre-correction barcode was a real 10x catalogue barcode but NOT a called
            # cell -- an empty droplet / non-cell molecule corrected into a real cell
            is_ambient = (have_raw and catalog is not None
                          and raw in catalog and raw not in cr_cells)
            if is_ab:
                stats['A_to_B'] += 1
            if is_ambient:
                stats['ambient_valid_noncell'] += 1
            if have_raw and not is_ab and not is_ambient:
                stats['benign_noncatalog_correction'] += 1

            for s in states:
                if s == 'exact' and not is_exact:
                    continue
                if s == 'noAB' and is_ab:
                    continue
                if s == 'noAmbient' and is_ambient:
                    continue
                if s == 'noContam' and (is_ab or is_ambient):
                    continue
                if umi:
                    key = (cb, g, umi)
                    if key in seen[s]:
                        continue
                    seen[s].add(key)
                else:
                    umiless[s] += 1
                counts[s][(cb, g)] += 1

    for s in states:
        d = os.path.join(a.outdir, a.arm, a.tool, s)
        nc, ng = write_10x(d, counts[s], genes_meta, umiless[s])
        log(f'{a.arm}/{a.tool}/{s}: {nc} cells x {ng} genes')

    with open(os.path.join(a.outdir, a.arm, a.tool, 'build_stats.json'), 'w') as fh:
        json.dump(dict(stats), fh, indent=2, sort_keys=True)
    log(json.dumps(dict(stats), sort_keys=True))


if __name__ == '__main__':
    main()
