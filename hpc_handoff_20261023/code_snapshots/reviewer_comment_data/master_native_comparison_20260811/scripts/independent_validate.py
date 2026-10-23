#!/usr/bin/env python3
"""Independent, source-facing validation for the native comparison master.

This intentionally does not import build_master.py.  It rereads the emitted
master tables and each upstream source using a separate set of parsing and
matching rules.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_ROOT = Path("/scratch/f005f43/master_native_comparison_20260811")
CORE = Path("/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/whitelist_native_three_tool_graph_ready_20260810/native_three_tool_TP_FP_FN_graph_ready.csv")
TILGNER = Path("/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/tilgner_all10_native_three_tool_whitelist_20260810/tables/tilgner_all10_native_three_tool_metrics.tsv")
VISIUM = Path("/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/visium_three_tool_splitaware_scatter_20260802/tables/visium_eight_library_three_tool_confusion.csv")
VISIUM_MANIFEST = Path("/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/visium_three_tool_splitaware_scatter_20260802/provenance/status_callset_manifest.csv")
TOOLS = ("RAD", "BLAZE", "Flexiplex")


def read(path: Path, delimiter: str):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def nonempty_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(bool(line.strip()) for line in handle)


def close(a, b, tol=5e-9):
    return math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=tol)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    long_tsv_path = root / "tables/master_native_comparison_long.tsv"
    long_csv_path = root / "tables/master_native_comparison_long.csv"
    wide_tsv_path = root / "tables/master_native_comparison_wide.tsv"
    wide_csv_path = root / "tables/master_native_comparison_wide.csv"
    source_tables_path = root / "provenance/source_tables.tsv"
    out_rows = []
    failures = []

    master = read(long_tsv_path, "\t")
    master_csv = read(long_csv_path, ",")
    core_rows = read(CORE, ",")
    tilgner_rows = read(TILGNER, "\t")
    visium_rows = read(VISIUM, ",")
    visium_manifest = {
        (r["library_input"], r["tool"]): r
        for r in read(VISIUM_MANIFEST, ",") if r["library_input"] != "all"
    }

    core_filtered = [r for r in core_rows if not r["Dataset"].startswith("Tilgner-")]
    core = {(r["Dataset"], r["Tool"]): r for r in core_filtered}
    tilgner = {(r["Dataset"], r["Tool"]): r for r in tilgner_rows}
    visium = {(r["library"], r["tool"]): r for r in visium_rows}
    source_maps = {str(CORE): core, str(TILGNER): tilgner, str(VISIUM): visium}
    source_key_counts = {
        str(CORE): Counter((r["Dataset"], r["Tool"]) for r in core_filtered),
        str(TILGNER): Counter((r["Dataset"], r["Tool"]) for r in tilgner_rows),
        str(VISIUM): Counter((r["library"], r["tool"]) for r in visium_rows),
    }
    recorded_sources = read(source_tables_path, "\t")
    mpnst_manifests = {}
    for src in recorded_sources:
        p = Path(src["path"])
        if p.name == "mpnst_native_three_tool_metrics.tsv" and p.is_file():
            rows = read(p, "\t")
            source_maps[str(p)] = {(r["physical_input_run"], r["tool"]): r for r in rows}
            source_key_counts[str(p)] = Counter((r["physical_input_run"], r["tool"]) for r in rows)
        elif p.name == "callset_manifest.tsv" and p.is_file():
            for row in read(p, "\t"):
                mpnst_manifests[(row["physical_input_run"], row["tool"])] = row

    def record(scope, key, check, ok, detail=""):
        status = "PASS" if ok else "FAIL"
        out_rows.append({"scope": scope, "key": key, "check": check, "status": status, "detail": detail})
        if not ok:
            failures.append(f"{scope}:{key}:{check}")

    # File-format equivalence and global structure.
    record("global", "long", "csv_tsv_row_identity", master == master_csv, f"rows={len(master)}")
    expected_rows = 108 if any(r["dataset_family"] == "MPNST" for r in master) else 96
    expected_inputs = 36 if expected_rows == 108 else 32
    record("global", "long", "row_count", len(master) == expected_rows, f"observed={len(master)} expected={expected_rows}")
    keys = [(r["physical_input_run"], r["tool"]) for r in master]
    record("global", "long", "unique_row_keys", len(keys) == len(set(keys)) == expected_rows)
    grouped = defaultdict(set)
    for dataset, tool in keys:
        grouped[dataset].add(tool)
    record("global", "long", "input_count", len(grouped) == expected_inputs, f"observed={len(grouped)} expected={expected_inputs}")
    record("global", "long", "three_tools_each", all(v == set(TOOLS) for v in grouped.values()))

    if expected_rows == 108:
        mpnst_inputs = {r["physical_input_run"] for r in master if r["dataset_family"] == "MPNST"}
        expected_accessions = {"ERR15095094", "ERR15095095", "ERR15095096", "ERR15095097"}
        observed_accessions = {a for n in mpnst_inputs for a in expected_accessions if a in n}
        record("global", "MPNST", "four_expected_accessions", len(mpnst_inputs) == 4 and observed_accessions == expected_accessions,
               f"inputs={sorted(mpnst_inputs)}")

    # Validate the recorded source-table inventory before row matching.
    for src in recorded_sources:
        p = Path(src["path"])
        ok = p.is_file() and p.stat().st_size == int(src["bytes"]) and digest(p) == src["sha256"]
        record("source_table", str(p), "bytes_and_sha256", ok,
               f"recorded_bytes={src['bytes']}; recorded_sha256={src['sha256']}")
        used = sum(r["source_table_path"] == str(p) for r in master)
        record("source_table", str(p), "rows_used_matches_master", used == int(src["rows_used"]),
               f"observed={used}; recorded={src['rows_used']}")

    # Every master row is matched to exactly one row in its named source.
    for row in master:
        key = (row["physical_input_run"], row["tool"])
        label = row["source_row_key"]
        srcmap = source_maps.get(row["source_table_path"], {})
        source = srcmap.get(key)
        unique = source is not None and source_key_counts.get(row["source_table_path"], Counter())[key] == 1
        record("row", label, "source_row_present_unique", unique,
               f"source={row['source_table_path']}")
        if not unique:
            continue

        triple = (int(row["tp_overlap"]), int(row["fp_unmatched"]), int(row["fn_missed"]))
        source_fields = ("TP", "FP", "FN") if "TP" in source else ("tp_overlap", "fp_unmatched", "fn_missed")
        source_triple = tuple(int(source[f]) for f in source_fields)
        record("row", label, "source_counts_exact", triple == source_triple,
               f"master={triple}; source={source_triple}")
        calls = triple[0] + triple[1]
        reference_n = triple[0] + triple[2]
        record("row", label, "count_identities", int(row["calls"]) == calls and int(row["reference_n"]) == reference_n,
               f"calls={calls}; reference_n={reference_n}")
        precision = triple[0] / calls if calls else 0.0
        recall = triple[0] / reference_n if reference_n else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        metric_ok = close(row["precision"], precision) and close(row["recall"], recall) and close(row["f1"], f1)
        record("row", label, "metrics_recomputed", metric_ok,
               f"precision={precision:.12f}; recall={recall:.12f}; f1={f1:.12f}")
        source_metric_ok = close(source.get("Precision", source.get("precision")), precision, 1e-8) \
            and close(source.get("Recall", source.get("recall")), recall, 1e-8) \
            and close(source.get("F1", source.get("f1")), f1, 1e-8)
        record("row", label, "source_metrics_recomputed", source_metric_ok)

        # Raw callset evidence where it was supplied.  The Visium package has a
        # durable hash/count manifest even when an older absolute path has since
        # disappeared; this is reported explicitly rather than hidden.
        if row["source_table_path"] == str(TILGNER):
            p = Path(row["source_callset_path"])
            exists = p.is_file()
            lines = nonempty_lines(p) if exists else -1
            record("row", label, "tilgner_callset_exists", exists, str(p))
            record("row", label, "tilgner_callset_line_count", exists and lines == int(row["calls"]),
                   f"observed={lines}; expected={row['calls']}")
        elif row["source_table_path"] == str(VISIUM):
            manifest_row = visium_manifest.get(key)
            ok = manifest_row is not None and int(manifest_row["nonempty_lines"]) == int(row["calls"])
            record("row", label, "visium_manifest_call_count", ok,
                   "missing manifest row" if manifest_row is None else f"manifest_nonempty_lines={manifest_row['nonempty_lines']}")
            if manifest_row:
                p = Path(manifest_row["path"])
                if p.is_file():
                    live_ok = p.stat().st_size == int(manifest_row["bytes"]) and digest(p) == manifest_row["sha256"]
                    record("row", label, "visium_live_callset_hash", live_ok, str(p))
        elif row["dataset_family"] == "MPNST":
            manifest_row = mpnst_manifests.get(key)
            path_ok = manifest_row is not None and row["source_callset_path"] == manifest_row["path"]
            record("row", label, "mpnst_manifest_path", path_ok,
                   "missing manifest row" if manifest_row is None else manifest_row["path"])
            if manifest_row is not None:
                p = Path(manifest_row["path"])
                regular = p.is_file() and not p.is_symlink()
                record("row", label, "mpnst_callset_regular_non_symlink", regular, str(p))
                if regular:
                    lines = nonempty_lines(p)
                    integrity = (p.stat().st_size == int(manifest_row["bytes"])
                                 and digest(p) == manifest_row["sha256"]
                                 and lines == int(manifest_row["nonempty_lines"])
                                 and lines == int(row["calls"]))
                    record("row", label, "mpnst_callset_bytes_sha256_lines", integrity,
                           f"bytes={p.stat().st_size}; lines={lines}")

    # Reconstruct every wide value from long, and verify CSV/TSV equivalence.
    wide_tsv = read(wide_tsv_path, "\t")
    wide_csv = read(wide_csv_path, ",")
    record("global", "wide", "csv_tsv_row_identity", wide_tsv == wide_csv, f"rows={len(wide_tsv)}")
    record("global", "wide", "row_count", len(wide_tsv) == expected_inputs, f"observed={len(wide_tsv)} expected={expected_inputs}")
    long_by_key = {(r["physical_input_run"], r["tool"]): r for r in master}
    wide_ok = True
    for wr in wide_tsv:
        for tool in TOOLS:
            lr = long_by_key[(wr["physical_input_run"], tool)]
            for metric in ("calls", "tp_overlap", "fp_unmatched", "fn_missed", "precision", "recall", "f1", "tool_version", "tool_settings", "source_table_path", "source_callset_path"):
                if wr[f"{tool}_{metric}"] != lr[metric]:
                    wide_ok = False
    record("global", "wide", "reconstructed_from_long", wide_ok)

    fields = ["scope", "key", "check", "status", "detail"]
    out_path = root / "validation/independent_validation.tsv"
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(out_rows)

    visium_live = sum(Path(r["path"]).is_file() for r in visium_manifest.values())
    summary = {
        "status": "PASS" if not failures else "FAIL",
        "validation_implementation": "independent; does not import build_master.py",
        "master_rows": len(master),
        "physical_inputs": len(grouped),
        "source_rows_matched": sum(1 for r in out_rows if r["check"] == "source_row_present_unique" and r["status"] == "PASS"),
        "checks_total": len(out_rows),
        "checks_failed": len(failures),
        "failed_check_ids": failures,
        "tilgner_live_callsets": sum(Path(r["source_callset_path"]).is_file() for r in master if r["source_table_path"] == str(TILGNER)),
        "tilgner_expected_callsets": 30,
        "visium_live_original_callsets": visium_live,
        "visium_manifested_callsets": len(visium_manifest),
        "visium_evidence_note": "All 24 call counts and expected hashes are retained in the source manifest; only currently existing absolute callset paths receive a live hash check.",
    }
    with (root / "validation/independent_validation_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    if failures:
        raise SystemExit(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
