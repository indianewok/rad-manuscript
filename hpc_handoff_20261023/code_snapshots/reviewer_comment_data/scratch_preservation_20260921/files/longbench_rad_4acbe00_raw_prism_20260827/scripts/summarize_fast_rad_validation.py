#!/usr/bin/env python3
"""Summarize all-record RAD CT deltas and compiled-audit validation gates."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path("/scratch-nfs/f005f43/longbench_rad_4acbe00_raw_prism_20260827")
ARMS = ("SN_ONT", "SC_ONT", "SN_PB", "SC_PB")


def one_row(path: Path) -> dict[str, str]:
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(rows) != 1:
        raise RuntimeError(f"expected one row: {path}")
    return rows[0]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    delta_rows: list[dict[str, object]] = []
    checks: list[dict[str, object]] = []
    all_pass = True
    for arm in ARMS:
        run = ROOT / "runs" / arm
        noct_ref = run / "audit_raw_noct"
        noct_fast = run / "audit_raw_noct_fast"
        all_fast = run / "audit_raw_all_fast"
        all_exact = run / "audit_raw_all_fast_exact"
        for required in (noct_ref, noct_fast, all_fast, all_exact):
            if not (required / "DONE").exists():
                raise RuntimeError(f"incomplete audit: {required}")

        parity = json.loads((noct_fast / "parity_report.json").read_text())
        exact_invariants = list(csv.DictReader((all_exact / "invariants.tsv").open(newline=""), delimiter="\t"))
        failed_invariants = [row for row in exact_invariants if row["status"] == "FAIL"]
        grouping = [row for row in exact_invariants if row["invariant"] == "physical_read_grouping_nonreentry"]
        summary_identical = (all_fast / "summary.tsv").read_bytes() == (all_exact / "summary.tsv").read_bytes()
        per_target_identical = (all_fast / "per_target.tsv").read_bytes() == (all_exact / "per_target.tsv").read_bytes()
        arm_pass = (
            parity["status"] == "PASS"
            and not failed_invariants
            and len(grouping) == 1
            and grouping[0]["status"] == "PASS"
            and grouping[0]["observed"] == "0"
            and summary_identical
            and per_target_identical
        )
        all_pass &= arm_pass
        checks.append(
            {
                "arm": arm,
                "status": "PASS" if arm_pass else "FAIL",
                "noct_python_parity": parity["status"],
                "noct_integer_comparisons": parity["integer_comparisons"],
                "noct_label_comparisons": parity["label_comparisons"],
                "all_exact_grouping_status": grouping[0]["status"] if grouping else "MISSING",
                "all_exact_grouping_reentries": int(grouping[0]["observed"]) if grouping else None,
                "all_failed_invariants": len(failed_invariants),
                "all_fast_exact_summary_byte_identical": summary_identical,
                "all_fast_exact_per_target_byte_identical": per_target_identical,
            }
        )

        before = one_row(noct_ref / "summary.tsv")
        after = one_row(all_exact / "summary.tsv")
        ct = one_row(all_exact / "ct_filter_counts.tsv")
        integer = lambda row, field: int(row[field])
        delta_rows.append(
            {
                "arm": arm,
                "ct_records_seen": int(ct["rad_ct_records_seen"]),
                "noct_assignment_records": integer(before, "assignment_records"),
                "all_assignment_records": integer(after, "assignment_records"),
                "assignment_record_delta": integer(after, "assignment_records") - integer(before, "assignment_records"),
                "noct_unique_physical_reads": integer(before, "unique_physical_reads"),
                "all_unique_physical_reads": integer(after, "unique_physical_reads"),
                "added_unique_physical_reads": integer(after, "unique_physical_reads") - integer(before, "unique_physical_reads"),
                "all_multi_target_physical_reads": integer(after, "multi_target_physical_reads"),
                "noct_O": integer(before, "unique_read_target_assignments_O"),
                "all_O": integer(after, "unique_read_target_assignments_O"),
                "added_O": integer(after, "unique_read_target_assignments_O") - integer(before, "unique_read_target_assignments_O"),
                "noct_native_exact": integer(before, "native_exact"),
                "all_native_exact": integer(after, "native_exact"),
                "native_exact_delta": integer(after, "native_exact") - integer(before, "native_exact"),
                "noct_all_corrected": integer(before, "all_corrected"),
                "all_all_corrected": integer(after, "all_corrected"),
                "all_corrected_delta": integer(after, "all_corrected") - integer(before, "all_corrected"),
                "all_native_corrected_overlap": integer(after, "native_exact") + integer(after, "all_corrected") - integer(after, "unique_read_target_assignments_O"),
                "all_noncatalog_to_selected": integer(after, "noncatalog_to_selected"),
                "all_catalog_noncell_A": integer(after, "catalog_noncell_to_selected_A"),
                "all_cellranger_K": integer(after, "cellranger_to_different_cellranger_K"),
            }
        )

    delta_path = ROOT / "fast_all_vs_noct_RAD_CT_deltas.tsv"
    with delta_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(delta_rows[0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(delta_rows)

    report = {
        "status": "PASS" if all_pass else "FAIL",
        "model": "Compiled RAD raw audit validated against Python CT-excluded reference and exact all-record grouping",
        "source": str((ROOT / "scripts/fast_rad_raw_audit.cpp").resolve()),
        "source_sha256": sha256(ROOT / "scripts/fast_rad_raw_audit.cpp"),
        "binary": str((ROOT / "tools/fast_rad_raw_audit_exact").resolve()),
        "binary_sha256": sha256(ROOT / "tools/fast_rad_raw_audit_exact"),
        "checks": checks,
        "delta_table": str(delta_path.resolve()),
        "canonical_update_authorized_here": False,
    }
    report_path = ROOT / "fast_rad_raw_audit_validation_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
