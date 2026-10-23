#!/usr/bin/env python3
"""
SPLiT-seq short-read barcode/UMI tabulation for SRR13948565 (GSM5169184,
"C2C12_short_1k") -- the Illumina library matched to the long-read run
SRR13948564 (GSM5169183, "C2C12_long_1k"), GEO series GSE168776.

Read 2 (86 nt) architecture, anchored on the two linkers:

    [ UMI 10 ][ BC3 8 ][ LINK_A 30 ][ BC2 8 ][ LINK_B 22 ][ BC1 8 ]
    0        10       18           48       56           78      86

  LINK_A = GTGGCCGATGTTTCGCATCGGCGTACGACT
  LINK_B = ATCCACGTGCTTGAGACTGTGG

BC3 = round-3 ligation, BC2 = round-2 ligation (rounds 2 and 3 share one
96-barcode set with a shared plate map), BC1 = round-1 RT barcode.

Round 1 is the subtle part: the 96 RT barcodes occupy only 48 wells, two
barcodes per well (oligo-dT and random-hexamer primers in the same well label
the SAME cell). The cell barcode therefore collapses round 1 to its WELL, which
reproduces the published Parse split-pipe identifier exactly:

    cell_bc = BC3seq + BC2seq + "_" + rnd1_well

Outputs (to --outdir):
  barcode_umi_counts.tsv.gz   cell_bc, umi, n_reads          (every observed UMI)
  umis_per_barcode.tsv        cell_bc + round identities + n_reads/n_umis
  parse_stats.json            read-level accounting
"""
import argparse, collections, gzip, io, json, os, subprocess, sys
from multiprocessing import Pool

LINK_A = "GTGGCCGATGTTTCGCATCGGCGTACGACT"
LINK_B = "ATCCACGTGCTTGAGACTGTGG"
UMI_S, UMI_E = 0, 10
BC3_S, BC3_E = 10, 18
LA_S, LA_E = 18, 48
BC2_S, BC2_E = 48, 56
LB_S, LB_E = 56, 78
BC1_S, BC1_E = 78, 86
SHIFTS = (0, 1, -1, 2, -2, 3, -3, 4, -4)
MIN_UMI = 8   # shortest UMI we will accept after a 5' deletion


def hamming_le(a, b, k):
    if len(a) != len(b):
        return False
    d = 0
    for x, y in zip(a, b):
        if x != y:
            d += 1
            if d > k:
                return False
    return True


def build_corrector(barcodes):
    """8-mer -> canonical barcode: exact, plus unique Hamming-1. Ambiguous dropped."""
    m = {b: b for b in barcodes}
    amb = set()
    for b in barcodes:
        for i in range(len(b)):
            for c in "ACGT":
                if c == b[i]:
                    continue
                v = b[:i] + c + b[i + 1:]
                if v in m and m[v] != b:
                    amb.add(v)
                elif v not in m:
                    m[v] = b
    for v in amb:
        m.pop(v, None)
    for b in barcodes:
        m[b] = b
    return m


G = {}


def init_pool(g):
    global G
    G = g


def find_anchor(seq, motif, expect_s, max_mm):
    L = len(motif)
    for s in SHIFTS:
        p = expect_s + s
        if 0 <= p and p + L <= len(seq) and hamming_le(seq[p:p + L], motif, max_mm):
            return p
    return -1


def parse_one(seq):
    """-> (umi, bc3, bc2, bc1, mode) or None"""
    if len(seq) >= BC1_E and hamming_le(seq[LA_S:LA_E], LINK_A, 3) \
            and hamming_le(seq[LB_S:LB_E], LINK_B, 2):
        return (seq[UMI_S:UMI_E], seq[BC3_S:BC3_E], seq[BC2_S:BC2_E],
                seq[BC1_S:BC1_E], "fixed")
    pa = find_anchor(seq, LINK_A, LA_S, 5)
    pb = find_anchor(seq, LINK_B, LB_S, 4)
    if pa < 0 and pb < 0:
        return None
    if pa < 0:
        pa = pb - (LB_S - LA_S)
    if pb < 0:
        pb = pa + (LB_S - LA_S)
    bc3_s = pa - 8
    umi_s = max(0, pa - 18)          # tolerate a 5'-truncated UMI
    bc2_s = pa + len(LINK_A)
    bc1_s = pb + len(LINK_B)
    if bc3_s < 0 or (bc3_s - umi_s) < MIN_UMI or bc1_s + 8 > len(seq):
        return None
    return (seq[umi_s:bc3_s], seq[bc3_s:bc3_s + 8], seq[bc2_s:bc2_s + 8],
            seq[bc1_s:bc1_s + 8], "anchored")


def worker(chunk):
    cnt = collections.Counter()
    rt_reads = collections.Counter()
    st = collections.Counter()
    rt, lig, rtw = G["rt"], G["lig"], G["rtw"]
    for seq in chunk:
        st["total"] += 1
        p = parse_one(seq)
        if p is None:
            st["no_linker_structure"] += 1
            continue
        umi, b3, b2, b1, mode = p
        st[mode] += 1
        k3, k2, k1 = lig.get(b3), lig.get(b2), rt.get(b1)
        if k3 is None:
            st["bc3_not_in_whitelist"] += 1
        if k2 is None:
            st["bc2_not_in_whitelist"] += 1
        if k1 is None:
            st["bc1_not_in_whitelist"] += 1
        if k3 is None or k2 is None or k1 is None:
            st["dropped_barcode_fail"] += 1
            continue
        if "N" in umi:
            st["dropped_umi_has_N"] += 1
            continue
        st["assigned"] += 1
        cell = f"{k3}{k2}_{rtw[k1]}"
        cnt[(cell, umi)] += 1
        rt_reads[(cell, k1)] += 1
    return cnt, rt_reads, st


def collapse_directional(umi_counts):
    """UMI-tools 'directional': greedy, an abundant UMI absorbs 1-mismatch
    neighbours with count <= parent/2 + 1."""
    order = sorted(umi_counts.items(), key=lambda kv: (-kv[1], kv[0]))
    remaining = dict(umi_counts)
    n = 0
    for umi, c in order:
        if umi not in remaining:
            continue
        n += 1
        del remaining[umi]
        stack = [(umi, c)]
        while stack:
            u, uc = stack.pop()
            thr = uc // 2 + 1
            for i in range(len(u)):
                for b in "ACGT":
                    if b == u[i]:
                        continue
                    v = u[:i] + b + u[i + 1:]
                    vc = remaining.get(v)
                    if vc is not None and vc <= thr:
                        del remaining[v]
                        stack.append((v, vc))
    return n


def read2_stream(path):
    if path.endswith(".gz"):
        p = subprocess.Popen(["pigz", "-dc", "-p", "12", path], stdout=subprocess.PIPE)
        fh = io.TextIOWrapper(p.stdout, encoding="ascii", errors="replace")
    else:
        p, fh = None, open(path, "r")
    for i, line in enumerate(fh):
        if i & 3 == 1:
            yield line[:-1]
    if p is not None:
        p.wait()


def chunker(it, n):
    buf = []
    for x in it:
        buf.append(x)
        if len(buf) >= n:
            yield buf
            buf = []
    if buf:
        yield buf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--r2", required=True)
    ap.add_argument("--rt-map", required=True, help="rt_barcode<TAB>rnd1_well<TAB>slot")
    ap.add_argument("--lig-map", required=True, help="barcode<TAB>rnd3_well<TAB>rnd2_well")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--threads", type=int, default=48)
    ap.add_argument("--chunk", type=int, default=400000)
    ap.add_argument("--collapse-min-reads", type=int, default=100,
                    help="run directional UMI collapse for cells with >= this many reads")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    rt_well, lig_w3, lig_w2 = {}, {}, {}
    for i, ln in enumerate(open(a.rt_map)):
        if i == 0:
            continue
        s, w, _slot = ln.rstrip("\n").split("\t")
        rt_well[s] = int(w)
    for i, ln in enumerate(open(a.lig_map)):
        if i == 0:
            continue
        s, w3, w2 = ln.rstrip("\n").split("\t")
        lig_w3[s] = int(w3)
        lig_w2[s] = int(w2)

    G_ = {"rt": build_corrector(sorted(rt_well)),
          "lig": build_corrector(sorted(lig_w3)),
          "rtw": rt_well}
    print(f"[wl] RT: {len(rt_well)} barcodes -> {len(set(rt_well.values()))} wells "
          f"({len(G_['rt'])} keys incl. 1mm)", file=sys.stderr)
    print(f"[wl] ligation: {len(lig_w3)} barcodes ({len(G_['lig'])} keys incl. 1mm)",
          file=sys.stderr, flush=True)

    total = collections.Counter()
    rt_reads = collections.Counter()
    stats = collections.Counter()
    done = 0
    with Pool(a.threads, initializer=init_pool, initargs=(G_,)) as pool:
        for cnt, rr, st in pool.imap_unordered(worker, chunker(read2_stream(a.r2), a.chunk)):
            total.update(cnt)
            rt_reads.update(rr)
            stats.update(st)
            done += 1
            if done % 25 == 0:
                print(f"[progress] {stats['total']:,} reads | "
                      f"{stats['assigned']:,} assigned | "
                      f"{len(total):,} (cell,umi) pairs", file=sys.stderr, flush=True)

    per_reads = collections.Counter()
    per_umis = collections.defaultdict(collections.Counter)
    pu = os.path.join(a.outdir, "barcode_umi_counts.tsv.gz")
    with gzip.open(pu, "wt", compresslevel=4) as fh:
        fh.write("cell_bc\tumi\tn_reads\n")
        for (bc, umi), n in total.items():
            fh.write(f"{bc}\t{umi}\t{n}\n")
            per_reads[bc] += n
            per_umis[bc][umi] = n

    rt_by_cell = collections.defaultdict(dict)
    for (cell, b1), n in rt_reads.items():
        rt_by_cell[cell][b1] = n

    rows = []
    for bc, reads in per_reads.items():
        lig16, w1 = bc.split("_")
        b3, b2 = lig16[:8], lig16[8:16]
        umis = per_umis[bc]
        ncol = collapse_directional(umis) if reads >= a.collapse_min_reads else len(umis)
        rts = sorted(rt_by_cell.get(bc, {}).items(), key=lambda kv: -kv[1])
        rows.append((bc, b3, b2, int(w1), lig_w3.get(b3, -1), lig_w2.get(b2, -1),
                     ",".join(f"{s}:{n}" for s, n in rts), reads, len(umis), ncol))
    rows.sort(key=lambda r: -r[9])

    with open(os.path.join(a.outdir, "umis_per_barcode.tsv"), "w") as fh:
        fh.write("cell_bc\tbc3_lig_seq\tbc2_lig_seq\trnd1_well\trnd3_well\trnd2_well"
                 "\trt_barcodes_reads\tn_reads\tn_umis_raw\tn_umis_collapsed\n")
        for r in rows:
            fh.write("\t".join(map(str, r)) + "\n")

    stats["distinct_cell_barcodes"] = len(per_reads)
    stats["distinct_cell_umi_pairs"] = len(total)
    with open(os.path.join(a.outdir, "parse_stats.json"), "w") as fh:
        json.dump(dict(sorted(stats.items())), fh, indent=2)
    print(json.dumps(dict(sorted(stats.items())), indent=2), file=sys.stderr)


if __name__ == "__main__":
    main()
