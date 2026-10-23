#!/usr/bin/env python3
"""
Bin-level set overlap: RAD-detected bins vs Seurat-input (Space Ranger
filtered_feature_bc_matrix) bins, at 2um / 8um / 16um. Pure presence/absence.

RAD attribution to spots: for each RAD pair sequence, look up the spot wf
attributed it to (using ALL wf (spot, ub) observations, not just canonicals).
~20% of RAD pairs that wf never extracted at all stay unmapped; report them.
"""
import csv
import gzip
import os
import time
from collections import defaultdict
from typing import Set

OUTDIR = "/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/raw_fastq_datasets/complex_outsourced_datasets/visium_hd_lr/uncorrected_spot_counts"
RAD = "/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/raw_fastq_datasets/complex_outsourced_datasets/visium_hd_lr/valid_pair_output"
WL = os.path.join(OUTDIR, "visium_hd_whitelist")
FLOWCELLS = ["PBC44593", "PBC44760", "PBC49262", "PBC52788"]


def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def spot_to_resolution(spot_2um, factor):
    """s_002um_<col>_<row>-1 -> s_<NNN>um_<col//factor>_<row//factor>-1"""
    body = spot_2um[len("s_002um_"):-2]
    c, r = body.split("_")
    if factor == 1:
        return spot_2um
    elif factor == 4:
        return f"s_008um_{int(c)//4:05d}_{int(r)//4:05d}-1"
    elif factor == 8:
        return f"s_016um_{int(c)//8:05d}_{int(r)//8:05d}-1"


def load_seurat_set(path):
    s = set()
    with gzip.open(path, "rt") as fh:
        for line in fh:
            s.add(line.rstrip())
    return s


def main():
    # 1) RAD pair union across the 4 flowcells
    log("loading RAD pair union")
    rad_pairs = set()
    for fc in FLOWCELLS:
        with open(os.path.join(RAD, f"{fc}_wl_valid_pairs.csv")) as fh:
            r = csv.DictReader(fh)
            for row in r:
                rad_pairs.add(row["pair"])
    log(f"  RAD union pairs: {len(rad_pairs):,}")

    # 2) For each RAD pair, find a spot that wf attributed it to
    #    Iterate wf per-flowcell CSVs; for each (spot, ub) row where ub in rad_pairs,
    #    record pair -> spot (first wins; consistent because wf's whitelist match is deterministic per ub)
    log("scanning wf per-flowcell CSVs to map RAD pairs to spots")
    pair_to_spot_2um = {}
    for fc in FLOWCELLS:
        path = os.path.join(OUTDIR, f"{fc}_uncorrected_spot_counts.csv")
        log(f"  scanning {fc}")
        with open(path) as fh:
            fh.readline()
            for line in fh:
                spot, ub, _ = line.rstrip("\n").split(",", 2)
                if ub in rad_pairs and ub not in pair_to_spot_2um:
                    pair_to_spot_2um[ub] = spot
    mapped = len(pair_to_spot_2um)
    log(f"  RAD pairs mapped via wf: {mapped:,} / {len(rad_pairs):,} ({mapped/len(rad_pairs):.1%})")
    log(f"  RAD pairs UNMAPPED (wf never extracted this exact sequence): {len(rad_pairs)-mapped:,}")

    # 3) RAD-attributed spot sets at each resolution
    rad_2um = set(pair_to_spot_2um.values())
    rad_8um = {spot_to_resolution(s, 4) for s in rad_2um}
    rad_16um = {spot_to_resolution(s, 8) for s in rad_2um}
    log(f"  RAD-attributed bins  2um: {len(rad_2um):,}   8um: {len(rad_8um):,}   16um: {len(rad_16um):,}")

    # 4) Seurat-input (Space Ranger filtered) bin sets at each resolution
    log("loading Seurat-input (filtered_feature_bc_matrix) bin sets")
    seurat_2um = load_seurat_set(os.path.join(WL, "sup_square_002um_filtered_barcodes.tsv.gz"))
    seurat_8um = load_seurat_set(os.path.join(WL, "sup_square_008um_filtered_barcodes.tsv.gz"))
    seurat_16um = load_seurat_set(os.path.join(WL, "sup_square_016um_filtered_barcodes.tsv.gz"))
    log(f"  Seurat 2um: {len(seurat_2um):,}   8um: {len(seurat_8um):,}   16um: {len(seurat_16um):,}")

    # 5) Per-resolution Venn
    print()
    print(f"{'res':<6}{'RAD':>14}{'Seurat':>14}{'intersect':>14}{'only RAD':>14}{'only Seurat':>14}{'Jaccard':>10}")
    for res, rs, ss in [("2um", rad_2um, seurat_2um),
                        ("8um", rad_8um, seurat_8um),
                        ("16um", rad_16um, seurat_16um)]:
        inter = rs & ss
        only_r = rs - ss
        only_s = ss - rs
        union = rs | ss
        j = len(inter)/len(union) if union else 0
        print(f"{res:<6}{len(rs):>14,}{len(ss):>14,}{len(inter):>14,}{len(only_r):>14,}{len(only_s):>14,}{j:>10.4f}")

    # 6) Also vs the raw (non-tissue-filtered) matrix at 16um, for context
    raw_16um = load_seurat_set(os.path.join(WL, "sup_square_016um_raw_barcodes.tsv.gz"))
    log(f"\nSpace Ranger RAW 16um bin set: {len(raw_16um):,}")
    inter = rad_16um & raw_16um
    only_r = rad_16um - raw_16um
    only_raw = raw_16um - rad_16um
    print(f"vs SR-raw 16um: intersect={len(inter):,}  only-RAD={len(only_r):,}  only-SR-raw={len(only_raw):,}")

    # Write the verdict to disk
    out = os.path.join(OUTDIR, "bin_overlap_rad_vs_seurat.tsv")
    log(f"\nwriting {out}")
    with open(out, "w") as fh:
        fh.write("resolution\trad_bins\tseurat_bins\tintersect\tonly_rad\tonly_seurat\tjaccard\n")
        for res, rs, ss in [("2um", rad_2um, seurat_2um),
                            ("8um", rad_8um, seurat_8um),
                            ("16um", rad_16um, seurat_16um)]:
            inter = rs & ss; only_r = rs - ss; only_s = ss - rs
            union = rs | ss
            j = len(inter)/len(union) if union else 0
            fh.write(f"{res}\t{len(rs)}\t{len(ss)}\t{len(inter)}\t{len(only_r)}\t{len(only_s)}\t{j:.6f}\n")

    # Save the only-RAD bins at each resolution
    for res, rs, ss in [("002um", rad_2um, seurat_2um),
                        ("008um", rad_8um, seurat_8um),
                        ("016um", rad_16um, seurat_16um)]:
        only_r = sorted(rs - ss)
        out_p = os.path.join(OUTDIR, f"bin_only_rad_{res}.txt")
        with open(out_p, "w") as fh:
            for s in only_r: fh.write(s + "\n")
        log(f"  wrote {len(only_r):,} only-RAD {res} bins to {out_p}")


if __name__ == "__main__":
    main()
