#!/usr/bin/env python3
"""
Exact-match-only uncorrected counts per spot, per flowcell.

For each 2 um spot, the assumed canonical uncorrected_barcode is the
uncorrected_barcode with the highest *total* count summed across all four
per-flowcell CSVs. Then for each flowcell, we sum the count of rows where
ub == canonical[spot]. Aggregated up to 16 um (sr16) for the final wide table.

Outputs:
  - exact_match_counts_by_sr16.csv       (sr16, PBC*, PBC*, PBC*, PBC*)
  - exact_match_canonical_per_spot.csv   (spot_2um, canonical_ub, total_count)
  - exact_match_summary.tsv              (per-flowcell totals)
"""
import csv
import os
import sys
import time
from collections import defaultdict
from typing import Dict, Tuple

OUTDIR = "/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/raw_fastq_datasets/complex_outsourced_datasets/visium_hd_lr/uncorrected_spot_counts"
FLOWCELLS = ["PBC44593", "PBC44760", "PBC49262", "PBC52788"]
PREFIX_2UM = "s_002um_"
SUFFIX = "-1"


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def to_sr16(spot_2um):
    body = spot_2um[len(PREFIX_2UM): -len(SUFFIX)]
    col_str, row_str = body.split("_")
    col = int(col_str) // 8
    row = int(row_str) // 8
    return f"s_016um_{col:05d}_{row:05d}-1"


def main():
    # --- Pass 1: cross-flowcell aggregation to find canonical per spot ---
    log("Pass 1: aggregating (spot, ub) counts across all 4 flowcells")
    total = defaultdict(int)  # type: Dict[Tuple[str, str], int]
    for fc in FLOWCELLS:
        path = os.path.join(OUTDIR, f"{fc}_uncorrected_spot_counts.csv")
        log(f"  reading {fc}")
        with open(path) as fh:
            fh.readline()  # header
            for line in fh:
                spot, ub, c_str = line.rstrip("\n").split(",", 2)
                total[(spot, ub)] += int(c_str)
    log(f"  total unique (spot, ub) pairs: {len(total):,}")

    log("deriving canonical = max-count ub per spot")
    canonical = {}  # type: Dict[str, str]
    best_count = {}  # type: Dict[str, int]
    for (spot, ub), c in total.items():
        if c > best_count.get(spot, 0):
            best_count[spot] = c
            canonical[spot] = ub
    log(f"  canonical map size (unique 2um spots): {len(canonical):,}")

    # Dump canonical map so user can inspect
    canon_path = os.path.join(OUTDIR, "exact_match_canonical_per_spot.csv")
    log(f"writing canonical map: {canon_path}")
    with open(canon_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["spot_2um", "canonical_ub", "total_count_4_flowcells"])
        # sort by spot for stable diffs
        for spot in sorted(canonical):
            w.writerow([spot, canonical[spot], best_count[spot]])

    # free pass-1 RAM before pass 2
    del total

    # --- Pass 2: per-flowcell exact-match counts ---
    log("Pass 2: tallying exact-match counts per flowcell at 2um, then sr16")
    # sr16_counts[sr16][fc] -> int
    sr16_counts = defaultdict(lambda: {fc: 0 for fc in FLOWCELLS})
    stats = {fc: {"exact_reads": 0, "all_reads": 0, "rows_kept": 0, "rows_dropped": 0}
             for fc in FLOWCELLS}

    for fc in FLOWCELLS:
        path = os.path.join(OUTDIR, f"{fc}_uncorrected_spot_counts.csv")
        log(f"  reading {fc}")
        with open(path) as fh:
            fh.readline()
            for line in fh:
                spot, ub, c_str = line.rstrip("\n").split(",", 2)
                c = int(c_str)
                stats[fc]["all_reads"] += c
                if canonical.get(spot) == ub:
                    sr16 = to_sr16(spot)
                    sr16_counts[sr16][fc] += c
                    stats[fc]["exact_reads"] += c
                    stats[fc]["rows_kept"] += 1
                else:
                    stats[fc]["rows_dropped"] += 1
        s = stats[fc]
        frac = s["exact_reads"] / s["all_reads"] if s["all_reads"] else 0
        log(f"    {fc}: exact={s['exact_reads']:,} / all={s['all_reads']:,} "
            f"= {frac:.1%}; rows kept={s['rows_kept']:,} dropped={s['rows_dropped']:,}")

    out_csv = os.path.join(OUTDIR, "exact_match_counts_by_sr16.csv")
    log(f"writing {out_csv}  (rows = unique sr16 bins with >= 1 exact-match read = {len(sr16_counts):,})")
    with open(out_csv, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["sr16"] + FLOWCELLS)
        for sr16 in sorted(sr16_counts):
            row = sr16_counts[sr16]
            w.writerow([sr16] + [row[fc] for fc in FLOWCELLS])

    summary_path = os.path.join(OUTDIR, "exact_match_summary.tsv")
    with open(summary_path, "w") as fh:
        fh.write("flowcell\tall_reads\texact_match_reads\texact_match_fraction\trows_kept\trows_dropped\n")
        for fc in FLOWCELLS:
            s = stats[fc]
            frac = s["exact_reads"] / s["all_reads"] if s["all_reads"] else 0
            fh.write(f"{fc}\t{s['all_reads']}\t{s['exact_reads']}\t{frac:.6f}\t"
                     f"{s['rows_kept']}\t{s['rows_dropped']}\n")
    log(f"summary: {summary_path}")


if __name__ == "__main__":
    main()
