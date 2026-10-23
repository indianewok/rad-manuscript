#!/usr/bin/env python3
"""Export/replay the retained RAD ED2 published-cell assignment checkpoint.

No demultiplexing is run. Source mode reads the existing normalized ED2 ledger,
maps both RT-primer types to the same well's T-primer sequence, and retains the
published cell set. Replay mode reads the resulting small assignment checkpoint.
Distinct reads and distinct UMIs are counted independently within each cell.
"""
import argparse
import collections
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path, delimiter=","):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def read_key(value):
    prefix = "SRR13948564."
    if not value.startswith(prefix) or not value[len(prefix):].isdigit():
        raise ValueError("Unexpected original-read identifier: " + value)
    return int(value[len(prefix):])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--source", type=Path, help="Original ED2 assignments_normalized.tsv.gz")
    mode.add_argument("--checkpoint", type=Path, help="Selected published-cell checkpoint to replay")
    parser.add_argument("--master", required=True, type=Path)
    parser.add_argument("--expected", required=True, type=Path,
                        help="ed1_ed2_per_published_cell.tsv")
    parser.add_argument("--rt-metadata", type=Path, help="bc_data_v2.csv; required in source mode")
    parser.add_argument("--output", type=Path, help="Deterministic gzip checkpoint; required in source mode")
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    if args.source and (not args.rt_metadata or not args.output):
        parser.error("Source mode requires --rt-metadata and --output")
    master = read_csv(args.master)
    cells = {row["canonical_barcode"] for row in master}
    if len(master) != 568 or len(cells) != 568:
        raise ValueError("Expected 568 unique canonical cell identifiers")
    expected_rows = [row for row in read_csv(args.expected, "\t")
                     if row["tool"] == "ED2 current main"]
    expected = {row["barcode"]: row for row in expected_rows}
    if len(expected_rows) != 568 or set(expected) != cells:
        raise ValueError("ED2 expected table does not match the complete published cell set")
    primer_map = {}
    if args.source:
        rt_rows = read_csv(args.rt_metadata)
        canonical = {row["well"]: row["sequence"].strip()
                     for row in rt_rows if row["type"] == "T"}
        primer_map = {row["sequence"].strip(): canonical[row["well"]] for row in rt_rows}
        if len(primer_map) != 96 or len(canonical) != 48:
            raise ValueError("Unexpected RT primer map cardinality")
    reads = {cell: set() for cell in cells}
    umis = {cell: set() for cell in cells}
    global_reads = set()
    counts = collections.Counter()
    source_path = args.source or args.checkpoint
    raw_output = zipped_output = text_output = None
    writer = None
    if args.source:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        raw_output = open(args.output, "wb")
        zipped_output = gzip.GzipFile(filename="", mode="wb", fileobj=raw_output,
                                      compresslevel=6, mtime=0)
        text_output = io.TextIOWrapper(zipped_output, encoding="utf-8", newline="")
        writer = csv.writer(text_output, delimiter="\t", lineterminator="\n")
        writer.writerow(["read_id", "canonical_barcode", "umi"])
    try:
        with gzip.open(source_path, "rt", newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                counts["input_rows"] += 1
                if args.source:
                    observed = row["normalized_barcode"]
                    umi = row["umi"]
                    if not observed or not umi:
                        counts["empty_barcode_or_umi_rows"] += 1
                        continue
                    parts = observed.split("_")
                    if len(parts) != 3 or parts[0] not in primer_map:
                        counts["unmappable_rt_barcode_rows"] += 1
                        continue
                    cell = "_".join([primer_map[parts[0]], parts[1], parts[2]])
                    if cell not in cells:
                        counts["outside_published_cells_rows"] += 1
                        continue
                else:
                    cell, umi = row["canonical_barcode"], row["umi"]
                    if cell not in cells or not umi:
                        raise ValueError("Checkpoint contains an invalid cell or empty UMI")
                rid = read_key(row["read_id"])
                counts["selected_assignment_rows"] += 1
                reads[cell].add(rid)
                umis[cell].add(umi)
                global_reads.add(rid)
                if writer:
                    writer.writerow([row["read_id"], cell, umi])
    finally:
        if text_output:
            text_output.close()
        if raw_output:
            raw_output.close()
    mismatches = []
    for cell in sorted(cells):
        actual = (len(reads[cell]), len(umis[cell]))
        wanted = (int(expected[cell]["reads"]), int(expected[cell]["umis"]))
        if actual != wanted:
            mismatches.append({"cell": cell, "actual_reads_umis": actual,
                               "expected_reads_umis": wanted})
    inputs = {"ledger": source_path, "master": args.master, "expected": args.expected}
    if args.source:
        inputs["rt_metadata"] = args.rt_metadata
    report = {
        "status": "PASS" if not mismatches else "FAIL",
        "scope": "RAD ED2 assignments to the 568 published cells; includes both RT primer types normalized to the T-primer key",
        "counting_unit": "Distinct read_id per canonical cell; distinct exact UMI per canonical cell",
        "source_demultiplexing_rerun": False,
        "input_files": {key: {"path": str(value), "bytes": value.stat().st_size,
                              "sha256": sha256(value)} for key, value in inputs.items()},
        "row_accounting": dict(counts),
        "published_cells": len(cells),
        "cells_with_reads": sum(bool(values) for values in reads.values()),
        "read_cell_pairs": sum(map(len, reads.values())),
        "globally_unique_published_cell_reads": len(global_reads),
        "cell_umi_pairs": sum(map(len, umis.values())),
        "per_cell_read_and_umi_mismatches": mismatches,
        "limitations": ["The original RAD ED2 tally-producing script has not been located.",
                        "This checkpoint omits assignments outside the published cell set and does not replace the full source ledger.",
                        "Source ordering is retained, gzip mtime is zero and its embedded filename is empty."],
    }
    if args.source:
        report["checkpoint"] = {"path": str(args.output), "bytes": args.output.stat().st_size,
                                "sha256": sha256(args.output)}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ["status", "row_accounting", "published_cells",
                     "read_cell_pairs", "globally_unique_published_cell_reads", "cell_umi_pairs"]}, indent=2))
    if mismatches:
        raise SystemExit("Per-cell validation failed; inspect the saved report")


if __name__ == "__main__":
    main()
