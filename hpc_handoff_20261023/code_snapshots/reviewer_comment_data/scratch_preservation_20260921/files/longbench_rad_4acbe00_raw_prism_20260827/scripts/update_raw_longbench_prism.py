#!/usr/bin/env python3
"""Update only raw LongBench RAD tables in an existing rebuttal Prism file.

The edit is deliberately same-shape: row universes, table metadata, graphs,
layouts, analyses, and every Vireo-related member are preserved.  Raw-derived
fraction/baseline result CSVs are recomputed so displayed graphs are not stale.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path


EXPECTED_SOURCE_SHA256 = "8998a5d5d8290c03acbd57a21757d2424960fd86a61ef0837b2e740e3d74c619"
PRISM_TOOL = Path("/dartfs-hpc/scratch/f005f43/codex_home/skills/prism-files/scripts/prism_tool.py")

TOTAL_TABLE = "3F7F1283-00B1-421D-AAEE-6CBCDB3C668C"
ERROR_TABLE = {
    "SC_ONT": ("7C5FA3C4-20DC-4651-8D3B-5E587B70782E", 3),
    "SN_ONT": ("7C29E53B-DBF9-4D44-B2AB-3C2EE54D4207", 1),
    "SC_PB": ("D8258054-0C3C-44C3-831B-EC0F68738311", 1),
    "SN_PB": ("83DF2DE6-AC0A-4345-AE43-B924F65E32D6", 1),
}
PER_CELL_TABLE = {
    "SC_ONT": ("BAE3B971-A810-43B1-B645-66DBB49AAA38", (1, 2, 3, 10)),
    "SN_ONT": ("C88CA73E-CFD7-4DB4-A6C6-98E3122AD04F", (1, 2, 3, 13)),
    "SC_PB": ("81436D18-A1C2-458D-9171-90028050E739", (1, 2, 3, 10)),
    "SN_PB": ("848919EB-EBF3-4BCB-9320-4ED2CC735C43", (1, 2, 3, 10)),
}
BASELINE_RESULT_TABLE = {
    "SC_ONT": "79A0F939-2E79-4140-A690-56A3E0FEEF6A",
    "SN_ONT": "323A257F-0C34-448B-BAE1-E01C7D228DDF",
    "SC_PB": "84B6F2F2-1946-4C39-9FA8-1DD0EF1B1C17",
    "SN_PB": "73FA47B4-5E97-434B-9D37-E3A909A66536",
}
ERROR_FRACTION_RESULT = {
    "SC_ONT": "32FE6F82-D054-4EAE-ACD8-9EC61F33935C",
    "SN_ONT": "2B8CF757-30E2-44CB-BF98-13E1BE3CEF76",
}
ARM_ROW = {"SC_ONT": "SC-ONT", "SN_ONT": "SN-ONT", "SC_PB": "SC-PB", "SN_PB": "SN-PB"}
ARMS = tuple(ARM_ROW)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_prism_tool():
    spec = importlib.util.spec_from_file_location("prism_tool", PRISM_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import prism_tool")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_csv(blob: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(blob.decode("utf-8"))))


def emit_csv(rows: list[list[str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def table_member(uid: str) -> str:
    return f"data/tables/{uid}/data.csv"


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def fmt_percent(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return ""
    # Match Prism's REMOVE_BASELINE/FRACTION_OF_TOTAL evaluation order exactly.
    value = numerator / denominator * 100.0
    if value == 0:
        return "0"
    return format(value, ".18g")


def validate_invariants(path: Path) -> None:
    rows = read_tsv(path)
    failures = [r for r in rows if r.get("status") == "FAIL"]
    if failures:
        raise RuntimeError(f"failed invariants in {path}: {failures[:3]}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--audits-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--change-log", type=Path, required=True)
    parser.add_argument(
        "--audit-subdir",
        default="audit_raw_noct",
        help="Audit result directory name below each arm (default: audit_raw_noct).",
    )
    parser.add_argument(
        "--expected-source-sha256",
        default=EXPECTED_SOURCE_SHA256,
        help="Required SHA256 of the source Prism; guards against editing the wrong revision.",
    )
    args = parser.parse_args()

    source_hash = sha256(args.source)
    if source_hash != args.expected_source_sha256:
        raise RuntimeError(f"unexpected source Prism SHA256: {source_hash}")
    if args.output.resolve() == args.source.resolve():
        raise RuntimeError("refusing to overwrite source Prism file")

    summaries: dict[str, dict[str, str]] = {}
    per_target: dict[str, dict[str, dict[str, str]]] = {}
    for arm in ARMS:
        root = args.audits_root / arm / args.audit_subdir
        if not (root / "DONE").exists():
            raise RuntimeError(f"audit is incomplete: {root}")
        validate_invariants(root / "invariants.tsv")
        summary_rows = read_tsv(root / "summary.tsv")
        if len(summary_rows) != 1 or summary_rows[0].get("dataset") != arm:
            raise RuntimeError(f"unexpected summary rows for {arm}")
        summaries[arm] = summary_rows[0]
        rows = read_tsv(root / "per_target.tsv")
        indexed = {r["target_barcode"]: r for r in rows}
        if len(indexed) != len(rows):
            raise RuntimeError(f"duplicate target barcodes for {arm}")
        per_target[arm] = indexed

    tool = load_prism_tool()
    archive = tool.Archive(str(args.source))
    replaced: dict[str, bytes] = {}
    changes: list[tuple[str, str, str, str, str]] = []

    def load_table(uid: str) -> list[list[str]]:
        member = table_member(uid)
        blob = archive.read(member)
        rows = parse_csv(blob)
        if emit_csv(rows) != blob:
            raise RuntimeError(f"candidate CSV does not round-trip byte-identically: {member}")
        return rows

    def replace_cell(table: str, row_key: str, field: str, row: list[str], idx: int, value: int) -> None:
        old = row[idx]
        new = str(value)
        if old != new:
            changes.append((table, row_key, field, old, new))
        row[idx] = new

    # Aggregate table: native, all corrected, noncatalog, catalog-noncell, CellRanger A->B.
    rows = load_table(TOTAL_TABLE)
    by_name = {r[0]: r for r in rows if r and r[0]}
    if list(by_name) != ["SC-ONT", "SN-ONT", "SC-PB", "SN-PB"]:
        raise RuntimeError(f"unexpected aggregate row labels/order: {list(by_name)}")
    aggregate_fields = (
        "native_exact",
        "all_corrected",
        "noncatalog_to_selected",
        "catalog_noncell_to_selected_A",
        "cellranger_to_different_cellranger_K",
    )
    for arm in ARMS:
        row = by_name[ARM_ROW[arm]]
        for idx, field in enumerate(aggregate_fields, start=1):
            replace_cell("LongBench total RAD read misattributions", ARM_ROW[arm], field, row, idx, int(summaries[arm][field]))
    replaced[table_member(TOTAL_TABLE)] = emit_csv(rows)

    # Error tables and their two existing FRACTION_OF_TOTAL result tables.
    for arm in ARMS:
        uid, rad_col = ERROR_TABLE[arm]
        error_rows = load_table(uid)
        expected_error_labels = [
            "Corrected from non-whitelist",
            "Failure Mode 1",
            "Failure Mode 2",
        ]
        if [r[0] for r in error_rows[:3]] != expected_error_labels:
            raise RuntimeError(f"unexpected error row labels for {arm}")
        values = (
            int(summaries[arm]["noncatalog_to_selected"]),
            int(summaries[arm]["catalog_noncell_to_selected_A"]),
            int(summaries[arm]["cellranger_to_different_cellranger_K"]),
        )
        if len(error_rows) < 3:
            raise RuntimeError(f"short error table for {arm}")
        for error_row, value in zip(error_rows[:3], values):
            replace_cell(f"{arm} Error types per tool", error_row[0], "RAD", error_row, rad_col, value)
        replaced[table_member(uid)] = emit_csv(error_rows)

        if arm in ERROR_FRACTION_RESULT:
            result_uid = ERROR_FRACTION_RESULT[arm]
            result_rows = load_table(result_uid)
            denominator = sum(values)
            for result_row, value in zip(result_rows[:3], values):
                old = result_row[rad_col]
                new = fmt_percent(value, denominator)
                if old != new:
                    changes.append((f"{arm} Error fraction result", result_row[0], "RAD percent", old, new))
                result_row[rad_col] = new
            replaced[table_member(result_uid)] = emit_csv(result_rows)

    # Per-cell raw tables and the four REMOVE_BASELINE cached result tables.
    source_field_names = (
        "noncatalog_to_selected",
        "catalog_noncell_to_selected_A",
        "cellranger_to_different_cellranger_K",
        "unique_read_target_assignments_O",
    )
    for arm in ARMS:
        source_uid, indices = PER_CELL_TABLE[arm]
        source_rows = load_table(source_uid)
        seen: set[str] = set()
        for row in source_rows:
            barcode = row[0] if row else ""
            if not barcode:
                continue
            if barcode in seen:
                raise RuntimeError(f"duplicate Prism barcode {barcode} in {arm}")
            seen.add(barcode)
            values = per_target[arm].get(barcode)
            for field, idx in zip(source_field_names, indices):
                value = int(values[field]) if values is not None else 0
                replace_cell(f"{arm} per cell", barcode, field, row, idx, value)
        missing_prism_rows = sorted(set(per_target[arm]) - seen)
        if missing_prism_rows:
            raise RuntimeError(f"{arm}: {len(missing_prism_rows)} audit targets absent from fixed Prism row universe")
        replaced[table_member(source_uid)] = emit_csv(source_rows)

        result_uid = BASELINE_RESULT_TABLE[arm]
        old_result_rows = load_table(result_uid)
        new_result_rows: list[list[str]] = []
        for row in source_rows:
            barcode = row[0] if row else ""
            if not barcode:
                continue
            nums = [int(row[i]) if row[i] else 0 for i in indices]
            denominator = nums[3]
            if denominator > 0:
                new_result_rows.append([barcode] + [fmt_percent(v, denominator) for v in nums[:3]] + [""])
            else:
                new_result_rows.append(["", "", "", "", ""])
        if len(old_result_rows) != len(new_result_rows):
            raise RuntimeError(f"{arm}: baseline result row count changed")
        for row_idx, (old_row, new_row) in enumerate(zip(old_result_rows, new_result_rows), start=1):
            if old_row != new_row:
                for col_idx, (old, new) in enumerate(zip(old_row, new_row)):
                    if old != new:
                        changes.append((f"{arm} REMOVE_BASELINE result", str(row_idx), f"csv_col_{col_idx + 1}", old, new))
        replaced[table_member(result_uid)] = emit_csv(new_result_rows)

    allowed_csv = {table_member(TOTAL_TABLE)}
    allowed_csv.update(table_member(v[0]) for v in ERROR_TABLE.values())
    allowed_csv.update(table_member(v[0]) for v in PER_CELL_TABLE.values())
    allowed_csv.update(table_member(v) for v in BASELINE_RESULT_TABLE.values())
    allowed_csv.update(table_member(v) for v in ERROR_FRACTION_RESULT.values())
    if set(replaced) != allowed_csv:
        raise RuntimeError("replacement member allowlist mismatch")
    if not changes:
        raise RuntimeError("no Prism values changed")

    # Do not rewrite or refresh tokens for candidate tables whose serialized
    # CSV is already byte-identical (some derived percentages may be unchanged).
    replaced = {member: blob for member, blob in replaced.items() if archive.read(member) != blob}
    changed_csv = set(replaced)
    if not changed_csv or not changed_csv.issubset(allowed_csv):
        raise RuntimeError("changed CSV member set is empty or outside allowlist")

    numeric_change_count = len(changes)

    # Native Prism edits refresh the table-local lowercase 32-hex data.dt token.
    # It is not referenced by analyses elsewhere.  Use a stable content-derived
    # fresh token so identical CSV payloads receive identical tokens.
    token_payloads: dict[str, bytes] = {}
    for csv_member in sorted(changed_csv):
        dt_member = csv_member.rsplit("/", 1)[0] + "/data.dt"
        old_token = archive.read(dt_member)
        new_token = hashlib.sha256(replaced[csv_member]).hexdigest()[:32].encode("ascii")
        if len(new_token) != 32 or any(c not in b"0123456789abcdef" for c in new_token):
            raise RuntimeError(f"invalid new data.dt token for {csv_member}")
        if new_token == old_token:
            raise RuntimeError(f"data.dt token did not refresh for {csv_member}")
        token_text = new_token.decode("ascii")
        if token_text in token_payloads and token_payloads[token_text] != replaced[csv_member]:
            raise RuntimeError("data.dt collision across unequal CSV payloads")
        token_payloads[token_text] = replaced[csv_member]
        replaced[dt_member] = new_token
        changes.append((dt_member, "__token__", "data.dt", old_token.decode("ascii"), token_text))
    allowed = changed_csv | {m.rsplit("/", 1)[0] + "/data.dt" for m in changed_csv}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    tool.rewrite(archive, str(args.output), replaced=replaced)

    with args.change_log.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(("table", "row", "field", "old", "new"))
        writer.writerows(changes)

    # Exact archive closure: only the allowlisted CSV members may differ.
    updated = tool.Archive(str(args.output))
    if [i.filename for i in archive.infos] != [i.filename for i in updated.infos]:
        raise RuntimeError("archive entry order changed")
    differing = []
    for before, after in zip(archive.infos, updated.infos):
        if before.compress_type != after.compress_type or before.date_time != after.date_time or before.external_attr != after.external_attr:
            raise RuntimeError(f"ZipInfo changed for {before.filename}")
        if archive.read(before.filename) != updated.read(after.filename):
            differing.append(before.filename)
    if set(differing) != allowed:
        raise RuntimeError(f"unexpected archive member differences: {sorted(set(differing) ^ allowed)}")

    print(json.dumps({
        "source": str(args.source),
        "source_sha256": source_hash,
        "audit_subdir": args.audit_subdir,
        "rad_ct_records_included": "noct" not in args.audit_subdir.lower(),
        "output": str(args.output),
        "output_sha256": sha256(args.output),
        "changed_members": len(differing),
        "changed_cells": numeric_change_count,
        "changed_tokens": len(changed_csv),
        "change_records": len(changes),
        "change_log": str(args.change_log),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
