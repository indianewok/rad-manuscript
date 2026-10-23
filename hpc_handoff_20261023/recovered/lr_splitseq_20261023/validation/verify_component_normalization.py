#!/usr/bin/env python3
"""Verify the preserved component-polyT Flexiplex normalization checkpoint.

This checks every row against the retained native statistics. It does not rerun
demultiplexing, modify either input, or treat assignment records as unique reads.
All paths are supplied by the caller so the check can run on an HPC checkout.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from itertools import zip_longest
from pathlib import Path


COMPLEMENT = str.maketrans("ACGTNacgtn", "TGCANtgcan")
STATS_COLUMNS = {"Read", "UB", "BC1", "BC2", "BC3", "FlankEditDist"}
NORMALIZED_COLUMNS = {
    "read_id", "barcode", "umi", "orientation", "flank_edit_distance"
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stats", required=True, type=Path)
    parser.add_argument("--assignments", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--expected-records", type=int, default=1345255)
    parser.add_argument("--expected-source-reads", type=int, default=1338285)
    args = parser.parse_args()
    if args.report.resolve() in {args.stats.resolve(), args.assignments.resolve()}:
        parser.error("The report must not overwrite either input.")

    count = 0
    unique_reads: set[str] = set()
    discrepancies = []
    with gzip.open(args.stats, "rt", newline="") as native_file, gzip.open(
        args.assignments, "rt", newline=""
    ) as normalized_file:
        native = csv.DictReader(native_file, delimiter="\t")
        normalized = csv.DictReader(normalized_file, delimiter="\t")
        if not STATS_COLUMNS.issubset(native.fieldnames or ()):
            raise ValueError("Native statistics lack required column names.")
        if set(normalized.fieldnames or ()) != NORMALIZED_COLUMNS:
            raise ValueError("Normalized assignments have unexpected columns.")

        for index, (original, observed) in enumerate(
            zip_longest(native, normalized), start=1
        ):
            if original is None or observed is None:
                discrepancies.append({"row": index, "kind": "row_count_mismatch"})
                break
            expected = {
                "read_id": original["Read"],
                "barcode": "_".join(
                    (original["BC3"], original["BC2"], original["BC1"])
                ),
                "umi": original["UB"].translate(COMPLEMENT)[::-1],
                "orientation": "",
                "flank_edit_distance": original["FlankEditDist"],
            }
            if observed != expected:
                discrepancies.append(
                    {"row": index, "kind": "normalization_mismatch"}
                )
                if len(discrepancies) >= 20:
                    break
            count += 1
            unique_reads.add(observed["read_id"])

    counts_match = (
        count == args.expected_records
        and len(unique_reads) == args.expected_source_reads
    )
    passed = not discrepancies and counts_match
    result = {
        "status": "PASS" if passed else "FAIL",
        "stats_source": str(args.stats),
        "stats_sha256": sha256(args.stats),
        "normalized_source": str(args.assignments),
        "normalized_sha256": sha256(args.assignments),
        "normalization_rule": (
            "read_id=Read; barcode=BC3_BC2_BC1; umi=reverse_complement(UB); "
            "orientation empty; flank_edit_distance=FlankEditDist"
        ),
        "rows_compared": count,
        "unique_source_reads": len(unique_reads),
        "expected_stats_rows": args.expected_records,
        "expected_unique_source_reads": args.expected_source_reads,
        "mismatches": discrepancies,
        "counts_match": counts_match,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
