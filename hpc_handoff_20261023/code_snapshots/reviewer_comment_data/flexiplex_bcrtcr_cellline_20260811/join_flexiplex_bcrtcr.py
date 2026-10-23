#!/usr/bin/env python3
"""Join Flexiplex assignments with BCR/TCR read classes and cell types.

Inputs (in the scratchpad):
  rage_flex_f8_full_reads_barcodes.txt  Flexiplex sidecar (Read, CellBarcode,
                                        FlankEditDist, BarcodeEditDist, UMI)
  rage_bcrtcr_hits.tsv                  minimap2 hits (read, target, matches)
  rageseq_barcode_celltype_map.csv      original Figure 3 cell-type map

Rules (match the cluster analysis and the manuscript method):
  * A read with more than one distinct barcode is ambiguous. Drop it.
  * Read class = best alignment target. IG* = BCR. TR* = TCR.
    A read with no alignment = unmapped.
  * Native = BarcodeEditDist 0. Corrected = all assigned reads.

Outputs:
  flexiplex_bcrtcr_summary.tsv      celltype x class x native/corrected
  flexiplex_bcrtcr_data11_shape.tsv Data-11 layout (rows = class rows)
  flexiplex_per_barcode_bcrtcr.tsv  per-barcode counts
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict

# ---- read class per read: keep the best hit ----------------------------
best: dict[str, tuple[int, str]] = {}
with open("rage_bcrtcr_hits.tsv") as fh:
    for line in fh:
        parts = line.rstrip("\n").split("\t")
        if len(parts) != 3:
            continue
        read, target, matches = parts
        try:
            m = int(matches)
        except ValueError:
            continue
        cur = best.get(read)
        if cur is None or m > cur[0]:
            best[read] = (m, target)

def read_class(read: str) -> str:
    hit = best.get(read)
    if hit is None:
        return "unmapped"
    t = hit[1]
    if t.startswith("IG"):
        return "BCR"
    if t.startswith("TR"):
        return "TCR"
    return "unmapped"

print(f"reads with alignments: {len(best)}")

# ---- flexiplex assignments: drop ambiguous reads -----------------------
read_bc: dict[str, str] = {}
read_ed: dict[str, int] = {}
ambiguous: set[str] = set()
records = 0
with open("rage_flex_f8_full_reads_barcodes.txt") as fh:
    header = fh.readline()
    for line in fh:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 4:
            continue
        read, bc, _flank, bc_ed = parts[0], parts[1], parts[2], parts[3]
        records += 1
        if read in ambiguous:
            continue
        seen = read_bc.get(read)
        if seen is None:
            read_bc[read] = bc
            read_ed[read] = int(bc_ed)
        elif seen != bc:
            ambiguous.add(read)
            del read_bc[read]
            del read_ed[read]
        else:
            # Same barcode again. Keep the lowest edit distance.
            read_ed[read] = min(read_ed[read], int(bc_ed))

print(f"assignment records: {records}")
print(f"ambiguous reads dropped: {len(ambiguous)}")
print(f"assigned unique reads: {len(read_bc)}")

# ---- cell types --------------------------------------------------------
celltype: dict[str, str] = {}
with open("rageseq_barcode_celltype_map.csv") as fh:
    for row in csv.DictReader(fh):
        celltype[row["barcode"]] = row["celltype"]

# ---- tabulate ----------------------------------------------------------
CT_ORDER = ["Ramos", "Jurkat", "Monocyte", "undetermined"]
CLS_ORDER = ["BCR", "TCR", "unmapped"]
counts: Counter = Counter()
per_bc: dict[str, Counter] = defaultdict(Counter)
for read, bc in read_bc.items():
    ct = celltype.get(bc, "undetermined")
    cls = read_class(read)
    native = read_ed[read] == 0
    counts[(ct, cls, "corrected")] += 1
    per_bc[bc][(cls, "corrected")] += 1
    if native:
        counts[(ct, cls, "native")] += 1
        per_bc[bc][(cls, "native")] += 1

with open("flexiplex_bcrtcr_summary.tsv", "w", newline="") as fh:
    w = csv.writer(fh, delimiter="\t", lineterminator="\n")
    w.writerow(["celltype", "read_class", "phase", "reads"])
    for ct in CT_ORDER:
        for cls in CLS_ORDER:
            for phase in ("native", "corrected"):
                w.writerow([ct, cls, phase, counts[(ct, cls, phase)]])

with open("flexiplex_bcrtcr_data11_shape.tsv", "w", newline="") as fh:
    w = csv.writer(fh, delimiter="\t", lineterminator="\n")
    w.writerow(["row"] + CT_ORDER)
    for cls in ("BCR", "TCR"):
        for phase in ("native", "corrected"):
            label = f"{phase.capitalize()} {cls}"
            w.writerow([label] + [counts[(ct, cls, phase)]
                                  for ct in CT_ORDER])

with open("flexiplex_per_barcode_bcrtcr.tsv", "w", newline="") as fh:
    w = csv.writer(fh, delimiter="\t", lineterminator="\n")
    w.writerow(["barcode", "celltype",
                "native_bcr", "corrected_bcr",
                "native_tcr", "corrected_tcr",
                "native_unmapped", "corrected_unmapped"])
    for bc in sorted(per_bc):
        c = per_bc[bc]
        w.writerow([bc, celltype.get(bc, "undetermined"),
                    c[("BCR", "native")], c[("BCR", "corrected")],
                    c[("TCR", "native")], c[("TCR", "corrected")],
                    c[("unmapped", "native")],
                    c[("unmapped", "corrected")]])

print("summary by celltype (corrected):")
for ct in CT_ORDER:
    row = {cls: counts[(ct, cls, "corrected")] for cls in CLS_ORDER}
    print(f"  {ct:14s} {row}")
