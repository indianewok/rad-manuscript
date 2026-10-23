#!/usr/bin/env python3
"""Join per-read barcode assignments with BCR/TCR classes and cell types.

This is the tool-independent half of the Figure 3G-H analysis. It accepts
the per-read TSV that extract_per_read.py writes, so it works for RAD,
BLAZE, and Flexiplex without a change.

The BCR/TCR alignment does not depend on the tool. All tools read the same
raw reads. So this script reuses rage_bcrtcr_hits.tsv, which the Flexiplex
run already made. Do not align the reads again.

Categories, as the Figure 3 panels define them:
  native     the tool did not correct the barcode
  corrected  the tool corrected the barcode (rescued reads only)
  total      native + corrected
A read with 2 different barcodes is ambiguous. This script drops it.

Outputs:
  <prefix>_bcrtcr_summary.tsv        cell type x class x phase counts
  <prefix>_bcrtcr_data11.tsv         the Data-11 panel shape, rescued-only
  <prefix>_per_barcode_bcrtcr.tsv    per-barcode counts, rescued-only
"""

from __future__ import annotations

import argparse
import csv
import gzip
import sys
from collections import Counter, defaultdict

CT_ORDER = ["Ramos", "Jurkat", "Monocyte", "undetermined"]
CLS_ORDER = ["BCR", "TCR", "unmapped"]


def opener(path):
    return gzip.open(path, "rt") if path.endswith(".gz") else open(path)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--per-read", required=True)
    p.add_argument("--hits", required=True)
    p.add_argument("--celltypes", required=True)
    p.add_argument("--prefix", required=True)
    a = p.parse_args()

    # Pass 1: per-read assignments. Drop reads with 2 different barcodes.
    assign: dict[str, tuple[str, int]] = {}
    ambiguous: set[str] = set()
    with opener(a.per_read) as fh:
        next(fh)
        for line in fh:
            read, bc, nat = line.rstrip("\n").split("\t")
            if read in ambiguous:
                continue
            prev = assign.get(read)
            if prev is None:
                assign[read] = (bc, int(nat))
            elif prev[0] != bc:
                ambiguous.add(read)
                del assign[read]
            else:
                # Same barcode again. Native wins over corrected.
                assign[read] = (bc, max(prev[1], int(nat)))
    print(f"assigned unique reads: {len(assign):,}; "
          f"ambiguous dropped: {len(ambiguous):,}", file=sys.stderr)

    # Pass 2: best BCR/TCR hit per read, for assigned reads only.
    best: dict[str, tuple[int, str]] = {}
    with opener(a.hits) as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            read, target, matches = parts
            if read not in assign:
                continue
            try:
                m = int(matches)
            except ValueError:
                continue
            cur = best.get(read)
            if cur is None or m > cur[0]:
                best[read] = (m, target)
    print(f"assigned reads with an alignment: {len(best):,}", file=sys.stderr)

    celltype = {}
    with open(a.celltypes) as fh:
        for row in csv.DictReader(fh):
            celltype[row["barcode"]] = row["celltype"]

    def read_class(read: str) -> str:
        hit = best.get(read)
        if hit is None:
            return "unmapped"
        if hit[1].startswith("IG"):
            return "BCR"
        if hit[1].startswith("TR"):
            return "TCR"
        return "unmapped"

    counts = Counter()
    per_bc = defaultdict(Counter)
    for read, (bc, nat) in assign.items():
        ct = celltype.get(bc, "undetermined")
        cls = read_class(read)
        phase = "native" if nat else "corrected"
        counts[(ct, cls, phase)] += 1
        per_bc[bc][(cls, phase)] += 1

    with open(f"{a.prefix}_bcrtcr_summary.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["celltype", "read_class", "phase", "reads"])
        for ct in CT_ORDER:
            for cls in CLS_ORDER:
                for ph in ("native", "corrected"):
                    w.writerow([ct, cls, ph, counts[(ct, cls, ph)]])

    with open(f"{a.prefix}_bcrtcr_data11.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["row"] + CT_ORDER)
        for cls in ("BCR", "TCR"):
            for ph in ("native", "corrected"):
                w.writerow([f"{ph.capitalize()} {cls}"]
                           + [counts[(ct, cls, ph)] for ct in CT_ORDER])

    with open(f"{a.prefix}_per_barcode_bcrtcr.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["barcode", "celltype", "native_bcr", "corrected_bcr",
                    "native_tcr", "corrected_tcr", "native_unmapped",
                    "corrected_unmapped"])
        for bc in sorted(per_bc):
            c = per_bc[bc]
            w.writerow([bc, celltype.get(bc, "undetermined"),
                        c[("BCR", "native")], c[("BCR", "corrected")],
                        c[("TCR", "native")], c[("TCR", "corrected")],
                        c[("unmapped", "native")],
                        c[("unmapped", "corrected")]])

    print("corrected (rescued) reads by cell type:", file=sys.stderr)
    for ct in CT_ORDER:
        row = {cls: counts[(ct, cls, "corrected")] for cls in CLS_ORDER}
        print(f"  {ct:14s} {row}", file=sys.stderr)


if __name__ == "__main__":
    main()
