#!/usr/bin/env python3
"""Build the validated 32-input base or gated 36-input final master tables."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


DEFAULT_ROOT = Path("/scratch/f005f43/master_native_comparison_20260811")
ROOT = DEFAULT_ROOT
CORE = Path("/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/whitelist_native_three_tool_graph_ready_20260810/native_three_tool_TP_FP_FN_graph_ready.csv")
TILGNER = Path("/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/tilgner_all10_native_three_tool_whitelist_20260810/tables/tilgner_all10_native_three_tool_metrics.tsv")
VISIUM = Path("/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/visium_three_tool_splitaware_scatter_20260802/tables/visium_eight_library_three_tool_confusion.csv")
VISIUM_MANIFEST = Path("/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/visium_three_tool_splitaware_scatter_20260802/provenance/status_callset_manifest.csv")

TOOLS = ["RAD", "BLAZE", "Flexiplex"]
MPNST_EXPECTED_ACCESSIONS = {"ERR15095094", "ERR15095095", "ERR15095096", "ERR15095097"}
LONG_FIELDS = [
    "dataset_family", "physical_input_run", "tool", "calls", "reference_n",
    "tp_overlap", "fp_unmatched", "fn_missed", "precision", "recall", "f1",
    "reference_type", "reference_description", "tool_version", "tool_settings",
    "validation_tier", "source_table_path", "source_callset_path", "source_row_key",
]


def read_delimited(path: Path, delimiter: str):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def dataset_family(name: str) -> str:
    if name.startswith("MPNST") or any(accession in name for accession in MPNST_EXPECTED_ACCESSIONS):
        return "MPNST"
    if name.startswith("ScTagger-"):
        return "ScTagger"
    if name.startswith("Measles-"):
        return "Measles"
    if name == "PromethION_iPSC":
        return "PromethION iPSC"
    if name.startswith("RAGEseq-"):
        return "RAGE-seq"
    if name.startswith("LongBench-"):
        return "LongBench"
    if name.startswith("LeBrigand-"):
        return "Le Brigand MOB"
    if name.startswith("Isosceles-"):
        return "Isosceles ovarian"
    if name.startswith("Hipp_SN_"):
        return "Tilgner hippocampus"
    if name.startswith("section"):
        return "Swedish Visium tonsil"
    raise ValueError(f"Unmapped dataset: {name}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def metric_string(value) -> str:
    return f"{float(value):.9f}"


def ref_semantics(source_value: str):
    if source_value == "exact_synthetic_truth":
        return (
            "exact_truth",
            "Exact known barcode truth from a synthetic benchmark.",
            "validated_exact_truth",
        )
    if source_value == "short_read_matched_proxy":
        return (
            "matched_short_read_positive_proxy",
            "Matched short-read retained barcodes are a positive proxy, not literal biological ground truth.",
            "validated_positive_proxy",
        )
    if source_value == "spatial_short_read_in_tissue_proxy":
        return (
            "spatial_on_tissue_operational",
            "Short-read on-tissue mask is an operational spatial reference, not proof that off-mask spots are biologically empty.",
            "validated_spatial_operational",
        )
    raise ValueError(f"Unknown source reference semantics: {source_value}")


def add_metrics(row, *, name, tool, tp, fp, fn, precision, recall, f1,
                ref_n, ref_type, ref_desc, tier, source_table,
                source_callset="", tool_version="", tool_settings=""):
    tp_i, fp_i, fn_i, ref_i = map(int, (tp, fp, fn, ref_n))
    row.append({
        "dataset_family": dataset_family(name),
        "physical_input_run": name,
        "tool": tool,
        "calls": str(tp_i + fp_i),
        "reference_n": str(ref_i),
        "tp_overlap": str(tp_i),
        "fp_unmatched": str(fp_i),
        "fn_missed": str(fn_i),
        "precision": metric_string(precision),
        "recall": metric_string(recall),
        "f1": metric_string(f1),
        "reference_type": ref_type,
        "reference_description": ref_desc,
        "tool_version": tool_version,
        "tool_settings": tool_settings,
        "validation_tier": tier,
        "source_table_path": str(source_table),
        "source_callset_path": source_callset,
        "source_row_key": f"{name}|{tool}",
    })


def load_mpnst_package(package: Path):
    """Load and fully gate the optional four-input MPNST package."""
    metrics_path = package / "tables/mpnst_native_three_tool_metrics.tsv"
    callset_manifest_path = package / "provenance/callset_manifest.tsv"
    validation_path = package / "validation/validation_summary.json"
    required = (metrics_path, callset_manifest_path, validation_path)
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise ValueError("MPNST package incomplete; required files missing: " + "; ".join(missing))

    with validation_path.open(encoding="utf-8") as handle:
        prior_validation = json.load(handle)
    if not (
        prior_validation.get("status") == "PASS"
        and prior_validation.get("rows") == 12
        and prior_validation.get("physical_inputs") == 4
        and set(prior_validation.get("tools", [])) == set(TOOLS)
        and not prior_validation.get("failed_checks", [])
    ):
        raise ValueError("MPNST package validation_summary.json does not certify PASS/12 rows/4 inputs/3 tools/zero failures")

    metrics = read_delimited(metrics_path, "\t")
    manifest_rows = read_delimited(callset_manifest_path, "\t")
    required_metric_fields = {
        "physical_input_run", "tool", "calls", "reference_n", "tp_overlap", "fp_unmatched", "fn_missed",
        "precision", "recall", "f1", "reference_type", "reference_description", "tool_version",
        "tool_settings", "validation_tier", "source_callset_path",
    }
    required_manifest_fields = {"physical_input_run", "tool", "path", "bytes", "sha256", "nonempty_lines"}
    if len(metrics) != 12 or not metrics or not required_metric_fields.issubset(metrics[0]):
        raise ValueError("MPNST metrics must contain exactly 12 rows and the documented required columns")
    if len(manifest_rows) != 12 or not manifest_rows or not required_manifest_fields.issubset(manifest_rows[0]):
        raise ValueError("MPNST callset manifest must contain exactly 12 rows and the documented required columns")

    metric_keys = [(r["physical_input_run"], r["tool"]) for r in metrics]
    manifest_keys = [(r["physical_input_run"], r["tool"]) for r in manifest_rows]
    inputs = sorted({k[0] for k in metric_keys})
    if len(set(metric_keys)) != 12 or len(set(manifest_keys)) != 12 or set(metric_keys) != set(manifest_keys):
        raise ValueError("MPNST metrics and callset manifest must have identical unique 4-input x 3-tool keys")
    if len(inputs) != 4 or any({t for d, t in metric_keys if d == name} != set(TOOLS) for name in inputs):
        raise ValueError("MPNST package is not exactly four physical inputs with RAD/BLAZE/Flexiplex each")
    accessions = {acc for name in inputs for acc in MPNST_EXPECTED_ACCESSIONS if acc in name}
    if accessions != MPNST_EXPECTED_ACCESSIONS or any(sum(acc in name for acc in MPNST_EXPECTED_ACCESSIONS) != 1 for name in inputs):
        raise ValueError("MPNST physical_input_run names must identify ERR15095094, ERR15095095, ERR15095096, and ERR15095097 exactly once")

    manifest = {(r["physical_input_run"], r["tool"]): r for r in manifest_rows}
    for row in metrics:
        key = (row["physical_input_run"], row["tool"])
        if row["reference_type"] != "matched_short_read_positive_proxy":
            raise ValueError(f"{key}: MPNST reference_type must be matched_short_read_positive_proxy")
        if row["validation_tier"] != "validated_positive_proxy" or not row["reference_description"].strip():
            raise ValueError(f"{key}: invalid validation tier or empty reference description")
        tp, fp, fn = map(int, (row["tp_overlap"], row["fp_unmatched"], row["fn_missed"]))
        calls, ref_n = int(row["calls"]), int(row["reference_n"])
        if calls != tp + fp or ref_n != tp + fn:
            raise ValueError(f"{key}: calls/reference arithmetic failed")
        precision = tp / calls if calls else 0.0
        recall = tp / ref_n if ref_n else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        if not all((
            math.isclose(float(row["precision"]), precision, abs_tol=5e-9),
            math.isclose(float(row["recall"]), recall, abs_tol=5e-9),
            math.isclose(float(row["f1"]), f1, abs_tol=5e-9),
        )):
            raise ValueError(f"{key}: precision/recall/F1 do not reproduce from TP/FP/FN")
        mr = manifest[key]
        if row["source_callset_path"] != mr["path"]:
            raise ValueError(f"{key}: metrics source_callset_path differs from callset manifest")
        callset = Path(mr["path"])
        if not callset.is_file() or callset.is_symlink():
            raise ValueError(f"{key}: callset is missing, not regular, or a symlink: {callset}")
        if callset.stat().st_size != int(mr["bytes"]) or sha256(callset) != mr["sha256"]:
            raise ValueError(f"{key}: callset bytes/SHA256 drift")
        with callset.open("rb") as handle:
            lines = sum(bool(line.strip()) for line in handle)
        if lines != int(mr["nonempty_lines"]) or lines != calls:
            raise ValueError(f"{key}: callset nonempty-line count does not equal manifested count and calls")

    for name in inputs:
        same_input = [r for r in metrics if r["physical_input_run"] == name]
        if len({(r["reference_n"], r["reference_type"], r["reference_description"], r["validation_tier"]) for r in same_input}) != 1:
            raise ValueError(f"{name}: three tools do not share identical reference semantics/count")
    return metrics_path, callset_manifest_path, validation_path, metrics


def build_rows(mpnst_package: Path | None = None):
    rows = []
    source_rows = {}
    extra_sources = []

    for src in read_delimited(CORE, ","):
        name, tool = src["Dataset"], src["Tool"]
        if name.startswith("Tilgner-"):
            continue
        ref_type, ref_desc, tier = ref_semantics(src["Reference_type"])
        add_metrics(
            rows, name=name, tool=tool, tp=src["TP"], fp=src["FP"], fn=src["FN"],
            precision=src["Precision"], recall=src["Recall"], f1=src["F1"],
            ref_n=src["Reference_whitelist_size"], ref_type=ref_type,
            ref_desc=ref_desc, tier=tier, source_table=CORE,
            tool_settings="not recorded in this source table",
        )
        source_rows[(name, tool)] = src

    for src in read_delimited(TILGNER, "\t"):
        name, tool = src["Dataset"], src["Tool"]
        mode = src["Mode"]
        version = ""
        if tool == "RAD" and "commit_" in mode:
            version = "commit " + mode.rsplit("commit_", 1)[1]
        elif tool == "RAD" and "origin_main_" in mode:
            version = "origin/main " + mode.rsplit("origin_main_", 1)[1]
        settings = {
            "RAD": mode,
            "BLAZE": f"{mode}; --expect-cells {src['ExpectedCells']}",
            "Flexiplex": mode,
        }[tool]
        add_metrics(
            rows, name=name, tool=tool, tp=src["TP"], fp=src["FP"], fn=src["FN"],
            precision=src["Precision"], recall=src["Recall"], f1=src["F1"],
            ref_n=src["ShortReadReferenceSize"],
            ref_type="matched_short_read_positive_proxy",
            ref_desc="Released matched Cell Ranger 3.1.0 filtered-MEX barcodes are a positive proxy, not literal biological ground truth.",
            tier="validated_positive_proxy", source_table=TILGNER,
            source_callset=src["SourceCallset"], tool_version=version,
            tool_settings=settings,
        )
        source_rows[(name, tool)] = src

    visium_callsets = {
        (r["library_input"], r["tool"]): r["path"]
        for r in read_delimited(VISIUM_MANIFEST, ",")
        if r["library_input"] != "all"
    }
    for src in read_delimited(VISIUM, ","):
        name, tool = src["library"], src["tool"]
        versions = {"RAD": "main 5cf1ee6", "BLAZE": "2.6.0a0", "Flexiplex": "1.02.6"}
        settings = {
            "RAD": "scan-wl -e 0.30; demux -R offensive -M 2 -m 2; Visium 3-prime layout",
            "BLAZE": "--expect-cells 2500; native installed _match_bc_row replay",
            "Flexiplex": "native 10x3v2 -f 8; selected-list assignments -e 2 linked to full-design -e 0 source evidence",
        }
        ref_n = int(src["TP"]) + int(src["FN"])
        add_metrics(
            rows, name=name, tool=tool, tp=src["TP"], fp=src["FP"], fn=src["FN"],
            precision=src["precision"], recall=src["recall"], f1=src["F1"],
            ref_n=ref_n, ref_type="spatial_on_tissue_operational",
            ref_desc="Author Seurat/on-tissue mask within the complete 4,992-barcode Visium-v1 design; off-mask does not prove biological emptiness.",
            tier="validated_spatial_operational", source_table=VISIUM,
            source_callset=visium_callsets[(name, tool)],
            tool_version=versions[tool], tool_settings=settings[tool],
        )
        source_rows[(name, tool)] = src

    if mpnst_package is not None:
        metrics_path, callset_manifest_path, validation_path, mpnst_rows = load_mpnst_package(mpnst_package)
        for src in mpnst_rows:
            name, tool = src["physical_input_run"], src["tool"]
            add_metrics(
                rows, name=name, tool=tool, tp=src["tp_overlap"], fp=src["fp_unmatched"], fn=src["fn_missed"],
                precision=src["precision"], recall=src["recall"], f1=src["f1"], ref_n=src["reference_n"],
                ref_type=src["reference_type"], ref_desc=src["reference_description"], tier=src["validation_tier"],
                source_table=metrics_path, source_callset=src["source_callset_path"],
                tool_version=src["tool_version"], tool_settings=src["tool_settings"],
            )
            source_rows[(name, tool)] = src
        extra_sources.extend((metrics_path, callset_manifest_path, validation_path))

    rows.sort(key=lambda x: (x["dataset_family"], x["physical_input_run"], TOOLS.index(x["tool"])))
    return rows, source_rows, extra_sources


def validate(rows, source_rows, include_mpnst=False):
    checks = []
    errors = []
    keys = [(r["physical_input_run"], r["tool"]) for r in rows]
    inputs = sorted({r["physical_input_run"] for r in rows})
    families = sorted({r["dataset_family"] for r in rows})
    expected_rows = 108 if include_mpnst else 96
    expected_inputs = 36 if include_mpnst else 32
    global_checks = {
        f"row_count_{expected_rows}": len(rows) == expected_rows,
        f"input_count_{expected_inputs}": len(inputs) == expected_inputs,
        f"unique_keys_{expected_rows}": len(set(keys)) == expected_rows,
        "three_tools_per_input": all({r["tool"] for r in rows if r["physical_input_run"] == name} == set(TOOLS) for name in inputs),
        "no_legacy_tilgner_names": not any(name.startswith("Tilgner-") for name in inputs),
        "reference_types_exactly_three": {r["reference_type"] for r in rows} == {
            "exact_truth", "matched_short_read_positive_proxy", "spatial_on_tissue_operational"
        },
    }
    for check, passed in global_checks.items():
        checks.append({"scope": "global", "key": check, "status": "PASS" if passed else "FAIL", "detail": ""})
        if not passed:
            errors.append(check)

    for row in rows:
        key = (row["physical_input_run"], row["tool"])
        src = source_rows[key]
        numeric_ok = int(row["calls"]) == int(row["tp_overlap"]) + int(row["fp_unmatched"])
        ref_ok = int(row["reference_n"]) == int(row["tp_overlap"]) + int(row["fn_missed"])
        p = int(row["tp_overlap"]) / int(row["calls"]) if int(row["calls"]) else 0.0
        rc = int(row["tp_overlap"]) / int(row["reference_n"]) if int(row["reference_n"]) else 0.0
        f1 = 2 * p * rc / (p + rc) if p + rc else 0.0
        metric_ok = all([
            math.isclose(float(row["precision"]), p, abs_tol=5e-9),
            math.isclose(float(row["recall"]), rc, abs_tol=5e-9),
            math.isclose(float(row["f1"]), f1, abs_tol=5e-9),
        ])
        source_metric_names = ("TP", "FP", "FN") if "TP" in src else ("tp_overlap", "fp_unmatched", "fn_missed")
        source_ok = (
            int(row["tp_overlap"]) == int(src[source_metric_names[0]])
            and int(row["fp_unmatched"]) == int(src[source_metric_names[1]])
            and int(row["fn_missed"]) == int(src[source_metric_names[2]])
        )
        passed = numeric_ok and ref_ok and metric_ok and source_ok
        detail = f"source={row['source_table_path']}; counts={row['tp_overlap']}/{row['fp_unmatched']}/{row['fn_missed']}"
        checks.append({"scope": "row", "key": row["source_row_key"], "status": "PASS" if passed else "FAIL", "detail": detail})
        if not passed:
            errors.append(row["source_row_key"])

    summary = {
        "status": "PASS" if not errors else "FAIL",
        "rows": len(rows),
        "physical_inputs": len(inputs),
        "tools": TOOLS,
        "dataset_families": families,
        "reference_type_counts": {kind: sum(r["reference_type"] == kind for r in rows) for kind in sorted({r["reference_type"] for r in rows})},
        "source_table_counts": {
            path: sum(r["source_table_path"] == path for r in rows)
            for path in sorted({r["source_table_path"] for r in rows})
        },
        "failed_checks": errors,
    }
    return checks, summary


def write_delimited(path: Path, fields, rows, delimiter):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter=delimiter, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def make_wide(rows):
    grouped = {}
    for row in rows:
        key = row["physical_input_run"]
        out = grouped.setdefault(key, {
            "dataset_family": row["dataset_family"],
            "physical_input_run": key,
            "reference_n": row["reference_n"],
            "reference_type": row["reference_type"],
            "reference_description": row["reference_description"],
            "validation_tier": row["validation_tier"],
        })
        prefix = row["tool"]
        for metric in ("calls", "tp_overlap", "fp_unmatched", "fn_missed", "precision", "recall", "f1"):
            out[f"{prefix}_{metric}"] = row[metric]
        for provenance in ("tool_version", "tool_settings", "source_table_path", "source_callset_path"):
            out[f"{prefix}_{provenance}"] = row[provenance]
    fields = ["dataset_family", "physical_input_run", "reference_n", "reference_type", "reference_description", "validation_tier"]
    for tool in TOOLS:
        fields.extend(f"{tool}_{name}" for name in (
            "calls", "tp_overlap", "fp_unmatched", "fn_missed", "precision", "recall", "f1",
            "tool_version", "tool_settings", "source_table_path", "source_callset_path"
        ))
    return fields, [grouped[k] for k in sorted(grouped, key=lambda k: (grouped[k]["dataset_family"], k))]


def main():
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mpnst-package", type=Path, help="Validated four-input MPNST package to append")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_ROOT, help="Destination package root")
    args = parser.parse_args()
    ROOT = args.output_root.resolve()
    if args.mpnst_package is not None and ROOT == DEFAULT_ROOT:
        raise SystemExit("REFUSE: MPNST append must target a staging/final directory, not overwrite the 96-row base package")
    rows, source_rows, extra_sources = build_rows(args.mpnst_package.resolve() if args.mpnst_package else None)
    checks, summary = validate(rows, source_rows, include_mpnst=args.mpnst_package is not None)
    if summary["status"] != "PASS":
        raise SystemExit(json.dumps(summary, indent=2))
    for subdir in ("tables", "validation", "provenance", "scripts", "audit"):
        (ROOT / subdir).mkdir(parents=True, exist_ok=True)
    tables = ROOT / "tables"
    validation = ROOT / "validation"
    write_delimited(tables / "master_native_comparison_long.csv", LONG_FIELDS, rows, ",")
    write_delimited(tables / "master_native_comparison_long.tsv", LONG_FIELDS, rows, "\t")
    wide_fields, wide_rows = make_wide(rows)
    write_delimited(tables / "master_native_comparison_wide.csv", wide_fields, wide_rows, ",")
    write_delimited(tables / "master_native_comparison_wide.tsv", wide_fields, wide_rows, "\t")
    write_delimited(validation / "row_validation.tsv", ["scope", "key", "status", "detail"], checks, "\t")
    with (validation / "validation_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    with (ROOT / "provenance" / "source_tables.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["path", "bytes", "sha256", "rows_used"])
        for path in (CORE, TILGNER, VISIUM, VISIUM_MANIFEST, *extra_sources):
            used = sum(r["source_table_path"] == str(path) for r in rows)
            writer.writerow([path, path.stat().st_size, sha256(path), used])


if __name__ == "__main__":
    main()
