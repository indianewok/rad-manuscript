#!/usr/bin/env python3
"""Tabulate native and corrected reads from an audit-flexiplex sidecar.

Definition (per the manuscript panels): a read is NATIVE when the raw
extracted barcode already equals the final barcode. A read is CORRECTED
when the raw barcode had to be fixed to become the final barcode.
The audit sidecar gives both: CellBarcode (final) and RawCellBarcode (raw).

The ScTagger read identifier holds the true barcode before the last dash.
A read with 2 different final barcodes is ambiguous. It is dropped.

Usage: python3 join_audit_native.py SIDECAR PREFIX
Writes PREFIX_read_summary.tsv and PREFIX_per_barcode.tsv.
"""
import csv, sys
from collections import Counter, defaultdict

sidecar, prefix = sys.argv[1], sys.argv[2]
assign = {}
ambiguous = set()
with open(sidecar) as fh:
    next(fh)
    for line in fh:
        f = line.rstrip("\n").split("\t")
        if len(f) < 6:
            continue
        read, final, raw = f[0], f[1], f[2]
        if read in ambiguous:
            continue
        prev = assign.get(read)
        if prev is None:
            assign[read] = (final, raw)
        elif prev[0] != final:
            ambiguous.add(read)
            del assign[read]

counts = Counter()
per_bc = defaultdict(Counter)
for read, (final, raw) in assign.items():
    true = read.rsplit("-", 1)[0]
    if final == true:
        key = "native" if raw == final else "corrected"
    else:
        key = "incorrect"
    counts[key] += 1
    per_bc[final][key] += 1
counts["ambiguous"] = len(ambiguous)

with open(f"{prefix}_read_summary.tsv", "w", newline="") as fh:
    w = csv.writer(fh, delimiter="\t", lineterminator="\n")
    w.writerow(["category", "reads"])
    for k in ("native", "corrected", "incorrect", "ambiguous"):
        w.writerow([k, counts[k]])
    w.writerow(["total", sum(counts.values())])

with open(f"{prefix}_per_barcode.tsv", "w", newline="") as fh:
    w = csv.writer(fh, delimiter="\t", lineterminator="\n")
    w.writerow(["barcode", "native", "corrected", "incorrect_in"])
    for bc in sorted(per_bc):
        c = per_bc[bc]
        w.writerow([bc, c["native"], c["corrected"], c["incorrect"]])

print(f"{prefix}: " + ", ".join(f"{k}={counts[k]:,}"
      for k in ("native", "corrected", "incorrect", "ambiguous")))
