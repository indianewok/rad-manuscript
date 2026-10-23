#!/usr/bin/env python3
"""Compare long-read (RAD) barcode+UMI calls against the short-read table,
restricted to the 568 split-pipe called cells.

RAD's splitseq.csv.gz is headerless long-format:  read_id, element, orientation, sequence
with elements barcode_1 (RT), barcode_2, barcode_3 (ligation), umi, read.

RAD's reported sequences are NOT consistently normalised: ~60% match the whitelist as-is
and ~20-29% only after reverse-complementing, and this is independent of RAD's own
forward/reverse label. So orientation is resolved PER READ from the barcodes, and the
same decision is applied to that read's UMI.
"""
import collections, csv, gzip, subprocess, sys, io, json, os

W = "/scratch-nfs/f005f43/splitseq_shortread_20260727"
LR = "/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/20250514_splitseq_out/splitseq.csv.gz"
COMP = str.maketrans("ACGTN", "TGCAN")


def rc(s):
    return s.translate(COMP)[::-1]


def build_corrector(bcs):
    m = {b: b for b in bcs}
    amb = set()
    for b in bcs:
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
    for b in bcs:
        m[b] = b
    return m


rt_well = {}
for i, l in enumerate(open(f"{W}/ref/rt_bc_well_map.tsv")):
    if i:
        s, w, _ = l.split()
        rt_well[s] = int(w)
lig = [l.split()[0] for i, l in enumerate(open(f"{W}/ref/lig_bc_well_map.tsv")) if i]
RT = build_corrector(sorted(rt_well))
LIG = build_corrector(sorted(lig))

pub = {r["cell_barcode"] for r in
       csv.DictReader(gzip.open(f"{W}/ref/GSM5169184_C2C12_short_1k_cell_metadata.csv.gz", "rt"))}


def resolve(b1, b2, b3):
    """Return (cell_bc, flipped) or (None, None). Tries as-is then all-revcomp."""
    for flip in (False, True):
        x1, x2, x3 = (rc(b1), rc(b2), rc(b3)) if flip else (b1, b2, b3)
        k1, k2, k3 = RT.get(x1), LIG.get(x2), LIG.get(x3)
        if k1 and k2 and k3:
            return f"{k3}{k2}_{rt_well[k1]}", flip
    return None, None


p = subprocess.Popen(["pigz", "-dc", "-p", "12", LR], stdout=subprocess.PIPE)
fh = io.TextIOWrapper(p.stdout, encoding="ascii", errors="replace")

st = collections.Counter()
lr_pairs_asis = collections.defaultdict(set)   # cell -> set(umi) with per-read flip applied
lr_pairs_noflip = collections.defaultdict(set)  # control: never flip the UMI
cur = None
rec = {}


def flush(rid, rec):
    st["reads"] += 1
    need = ("barcode_1", "barcode_2", "barcode_3", "umi")
    if not all(k in rec for k in need):
        st["incomplete"] += 1
        return
    if any(len(rec[k]) > 1 for k in need):
        st["multi_valued(concatemer)"] += 1
        return
    b1, b2, b3, umi = (rec["barcode_1"][0], rec["barcode_2"][0],
                       rec["barcode_3"][0], rec["umi"][0])
    if not (b1 and b2 and b3 and umi):
        st["empty_field"] += 1
        return
    cell, flip = resolve(b1, b2, b3)
    if cell is None:
        st["barcode_unresolved"] += 1
        return
    st["flipped" if flip else "asis"] += 1
    st["resolved"] += 1
    if len(umi) != 10 or "N" in umi:
        st["umi_bad"] += 1
        return
    st["usable"] += 1
    lr_pairs_asis[cell].add(rc(umi) if flip else umi)
    lr_pairs_noflip[cell].add(umi)


for line in fh:
    q = line.rstrip("\n").split(",")
    if len(q) < 4:
        continue
    rid, el, ori, seq = q[0], q[1], q[2], q[3]
    if el == "read":
        continue
    if rid != cur:
        if cur is not None:
            flush(cur, rec)
        cur, rec = rid, {}
    rec.setdefault(el, []).append(seq)
if cur is not None:
    flush(cur, rec)
p.wait()

print("=== long-read parse ===")
for k, v in sorted(st.items()):
    print(f"  {k:26} {v:>12,}")
print(f"  long-read cells (any)      {len(lr_pairs_asis):>12,}")
print(f"  long-read cells in the 568 {len(set(lr_pairs_asis) & pub):>12,}")

# short-read UMIs for the called cells
sr = collections.defaultdict(set)
with gzip.open(f"{W}/csv/called_cells_barcode_umi_reads_fastq.csv.gz", "rt") as f:
    r = csv.reader(f)
    next(r)
    for cb, umi, n in r:
        sr[cb].add(umi)
print(f"\nshort-read called cells {len(sr):,}, UMIs {sum(len(v) for v in sr.values()):,}")

for tag, lrmap in (("per-read orientation (correct)", lr_pairs_asis),
                   ("no UMI flip (control)", lr_pairs_noflip)):
    cells = set(lrmap) & pub
    lr_tot = sum(len(lrmap[c]) for c in cells)
    inter = sum(len(lrmap[c] & sr[c]) for c in cells)
    sr_tot = sum(len(sr[c]) for c in cells)
    print(f"\n--- {tag} ---")
    print(f"  cells compared            : {len(cells)}")
    print(f"  long-read UMIs in them    : {lr_tot:,}")
    print(f"  short-read UMIs in them   : {sr_tot:,}")
    print(f"  intersection              : {inter:,}")
    print(f"  % of long-read UMIs found in short read : {100*inter/max(1,lr_tot):.2f}%")
    print(f"  % of short-read UMIs found in long read : {100*inter/max(1,sr_tot):.4f}%")

# per-cell detail for the correct orientation
rows = []
for c in sorted(set(lr_pairs_asis) & pub, key=lambda c: -len(lr_pairs_asis[c])):
    L, S = lr_pairs_asis[c], sr[c]
    rows.append((c, len(L), len(S), len(L & S)))
with open(f"{W}/results/lr_vs_sr_umi_overlap.tsv", "w") as fh2:
    fh2.write("cell_bc\tlr_umis\tsr_umis\tshared_umis\tpct_lr_found_in_sr\n")
    for c, l, s, i in rows:
        fh2.write(f"{c}\t{l}\t{s}\t{i}\t{100*i/max(1,l):.2f}\n")
print(f"\nwrote results/lr_vs_sr_umi_overlap.tsv ({len(rows)} cells)")
print("\ntop cells:")
print(f"  {'cell_bc':<22}{'lr_umis':>9}{'sr_umis':>10}{'shared':>9}{'%lr found':>11}")
for c, l, s, i in rows[:10]:
    print(f"  {c:<22}{l:>9,}{s:>10,}{i:>9,}{100*i/max(1,l):>10.1f}%")
