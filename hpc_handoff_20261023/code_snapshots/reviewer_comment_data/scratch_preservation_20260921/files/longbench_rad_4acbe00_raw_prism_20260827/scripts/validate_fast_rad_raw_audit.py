#!/usr/bin/env python3
"""Exact integer parity check for compact fast RAD raw-audit outputs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


SUMMARY_INTEGER_FIELDS = (
    "assignment_records",
    "unique_physical_reads",
    "multi_target_physical_reads",
    "unique_read_target_assignments_O",
    "native_exact",
    "all_corrected",
    "selected_source_changed",
    "missed_cellranger_to_selected",
    "cellranger_to_different_cellranger_K",
    "consensus_cross_line_X",
    "consensus_same_line_different_cell",
    "consensus_label_incomplete",
    "catalog_noncell_to_selected_A",
    "noncatalog_to_selected",
    "raw_source_unavailable",
)

PER_TARGET_INTEGER_FIELDS = (
    "assignment_records",
    "unique_read_target_assignments_O",
    "native_exact",
    "all_corrected",
    "missed_cellranger_to_selected",
    "cellranger_to_different_cellranger_K",
    "consensus_same_line_different_cell",
    "consensus_cross_line_X",
    "consensus_label_incomplete",
    "catalog_noncell_to_selected_A",
    "noncatalog_to_selected",
    "raw_source_unavailable",
)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    differences: list[dict[str, object]] = []
    ref_summary = read_rows(args.reference / "summary.tsv")
    got_summary = read_rows(args.candidate / "summary.tsv")
    if len(ref_summary) != 1 or len(got_summary) != 1:
        raise RuntimeError("expected one summary row in reference and candidate")
    for field in SUMMARY_INTEGER_FIELDS:
        expected = int(ref_summary[0][field])
        observed = int(got_summary[0][field])
        if observed != expected:
            differences.append(
                {"table": "summary", "key": ref_summary[0]["dataset"], "field": field,
                 "expected": expected, "observed": observed}
            )

    ref_targets = {row["target_barcode"]: row for row in read_rows(args.reference / "per_target.tsv")}
    got_targets = {row["target_barcode"]: row for row in read_rows(args.candidate / "per_target.tsv")}
    if set(ref_targets) != set(got_targets):
        differences.append(
            {"table": "per_target", "key": "ROW_UNIVERSE", "field": "target_barcode",
             "expected": len(ref_targets), "observed": len(got_targets),
             "missing": sorted(set(ref_targets) - set(got_targets))[:20],
             "extra": sorted(set(got_targets) - set(ref_targets))[:20]}
        )
    compared_cells = 0
    for barcode in sorted(set(ref_targets) & set(got_targets)):
        compared_cells += 1
        if ref_targets[barcode]["target_consensus_label"] != got_targets[barcode]["target_consensus_label"]:
            differences.append(
                {"table": "per_target", "key": barcode, "field": "target_consensus_label",
                 "expected": ref_targets[barcode]["target_consensus_label"],
                 "observed": got_targets[barcode]["target_consensus_label"]}
            )
        for field in PER_TARGET_INTEGER_FIELDS:
            expected = int(ref_targets[barcode][field])
            observed = int(got_targets[barcode][field])
            if observed != expected:
                differences.append(
                    {"table": "per_target", "key": barcode, "field": field,
                     "expected": expected, "observed": observed}
                )

    result = {
        "status": "PASS" if not differences else "FAIL",
        "reference": str(args.reference.resolve()),
        "candidate": str(args.candidate.resolve()),
        "summary_integer_fields_compared": len(SUMMARY_INTEGER_FIELDS),
        "per_target_integer_fields_compared": len(PER_TARGET_INTEGER_FIELDS),
        "per_target_rows_compared": compared_cells,
        "integer_comparisons": len(SUMMARY_INTEGER_FIELDS) + compared_cells * len(PER_TARGET_INTEGER_FIELDS),
        "label_comparisons": compared_cells,
        "difference_count": len(differences),
        "differences": differences[:100],
    }
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if not differences else 1


if __name__ == "__main__":
    raise SystemExit(main())
