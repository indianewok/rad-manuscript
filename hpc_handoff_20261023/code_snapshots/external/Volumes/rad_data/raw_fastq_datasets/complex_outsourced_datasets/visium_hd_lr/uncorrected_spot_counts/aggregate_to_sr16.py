#!/usr/bin/env python3
"""
Aggregate per-flowcell uncorrected_spot_counts CSVs (keyed by 2 um spot ID +
uncorrected_barcode) up to 16 um SpaceRanger bins (sr16). Emit a single wide
table: sr16, PBC44593, PBC44760, PBC49262, PBC52788.

Binning: 16 um col = 2um col // 8, 16 um row = 2um row // 8 (8x8 aggregation).
Spot ID format: s_002um_<col>_<row>-1 and s_016um_<col>_<row>-1, 5-digit zero pad.

Rows where corrected_barcode was '-' (no whitelist match) are skipped.
"""
import csv
import os
import sys
import time
from collections import defaultdict
from typing import Optional, Dict

OUTDIR = "/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/raw_fastq_datasets/complex_outsourced_datasets/visium_hd_lr/uncorrected_spot_counts"
FLOWCELLS = ["PBC44593", "PBC44760", "PBC49262", "PBC52788"]
OUT_CSV = os.path.join(OUTDIR, "uncorrected_counts_by_sr16.csv")
OUT_SUMMARY = os.path.join(OUTDIR, "sr16_aggregation_summary.tsv")

PREFIX_2UM = "s_002um_"
SUFFIX = "-1"


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def to_sr16(spot_2um):
    # type: (str) -> Optional[str]
    """s_002um_01015_02787-1 -> s_016um_00126_00348-1"""
    if not spot_2um.startswith(PREFIX_2UM) or not spot_2um.endswith(SUFFIX):
        return None
    body = spot_2um[len(PREFIX_2UM): -len(SUFFIX)]
    parts = body.split("_")
    if len(parts) != 2:
        return None
    try:
        col = int(parts[0]) // 8
        row = int(parts[1]) // 8
    except ValueError:
        return None
    return f"s_016um_{col:05d}_{row:05d}-1"


def main():
    # counts[sr16][fc] -> int
    counts = defaultdict(lambda: {fc: 0 for fc in FLOWCELLS})  # type: Dict[str, Dict[str, int]]
    stats = {fc: {"rows": 0, "skipped_no_spot": 0, "reads_in": 0, "reads_aggregated": 0}
             for fc in FLOWCELLS}

    for fc in FLOWCELLS:
        path = os.path.join(OUTDIR, f"{fc}_uncorrected_spot_counts.csv")
        log(f"reading {path}")
        with open(path, "r") as fh:
            header = fh.readline().rstrip("\n").split(",")
            assert header == ["spot", "uncorrected_barcode", "count"], header
            for line in fh:
                spot, _ub, c_str = line.rstrip("\n").split(",", 2)
                cnt = int(c_str)
                stats[fc]["rows"] += 1
                stats[fc]["reads_in"] += cnt
                sr16 = to_sr16(spot)
                if sr16 is None:
                    stats[fc]["skipped_no_spot"] += cnt
                    continue
                counts[sr16][fc] += cnt
                stats[fc]["reads_aggregated"] += cnt
        log(f"  {fc}: rows={stats[fc]['rows']:,}  reads_in={stats[fc]['reads_in']:,}  "
            f"reads_aggregated={stats[fc]['reads_aggregated']:,}  "
            f"skipped_no_spot={stats[fc]['skipped_no_spot']:,}")

    log(f"writing {OUT_CSV}  unique sr16 spots = {len(counts):,}")
    with open(OUT_CSV, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["sr16"] + FLOWCELLS)
        for sr16 in sorted(counts):
            row = counts[sr16]
            w.writerow([sr16] + [row[fc] for fc in FLOWCELLS])

    with open(OUT_SUMMARY, "w") as fh:
        fh.write("flowcell\trows_in\treads_in\treads_aggregated\tskipped_no_spot\tsr16_with_counts\n")
        for fc in FLOWCELLS:
            s = stats[fc]
            n_sr16 = sum(1 for d in counts.values() if d[fc] > 0)
            fh.write(f"{fc}\t{s['rows']}\t{s['reads_in']}\t{s['reads_aggregated']}\t"
                     f"{s['skipped_no_spot']}\t{n_sr16}\n")
    log(f"summary: {OUT_SUMMARY}")


if __name__ == "__main__":
    main()
