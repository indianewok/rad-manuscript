#!/usr/bin/env python3
"""Build the complete whitelist-detection data handoff for GraphPad Prism.

The native Prism archive is intentionally never edited.  This script builds a
documented, data-only PZFX project from the validated native 36-input master,
then appends the later ScMixology2 reconstruction in a separately labelled
panel.  The RAGEseq TNBC draining-lymph-node input is intentionally rescored
against the explicitly annotated adaptive-immune subset of its matched
short-read barcodes.  It also writes the paper/processing inventory and
validates every numeric cell after reparsing the generated XML.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html
import json
import math
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


TOOLS = ["RAD", "BLAZE", "Flexiplex"]
COUNT_FIELDS = ["tp", "fp", "fn"]
METRIC_FIELDS = ["f1", "precision", "recall"]

RAD_DATA = Path("/dartfs/rc/lab/A/AckermanLab/CMV/rad_data")
REVIEW = RAD_DATA / "reviewer_comment_data"
ORIGINAL_PRISM = RAD_DATA / "three_tool_whitelist_data.prism"
ORIGINAL_PRISM_SHA256 = "8e34e08f5f233e90c5d508904c5ceb54e7daae7fdec3abd53022c24869691c50"
MASTER = REVIEW / "master_native_comparison_20260811/tables/master_native_comparison_long.csv"
ORIGINAL_GRAPH_READY = REVIEW / (
    "whitelist_native_three_tool_graph_ready_20260810/"
    "native_three_tool_TP_FP_FN_graph_ready.csv"
)

SCMIX_RDS = REVIEW / (
    "reviewer_response_20260804/objects/other_streams/objects/"
    "scmixology2_performance.rds"
)
SCMIX_RAD_NATIVE = Path(
    "/scratch-nfs/f005f43/rad_scmix2_20260726/results/"
    "fixed_scmix2_scanwl_e03_t24_full_20260726/cases/01_full/output/scanwl.txt"
)
SCMIX_TRUTH = Path(
    "/scratch/f005f43/blaze_analysis_data_20335203/data/scmixology/"
    "cellranger/whitelist.tsv"
)
SCMIX_BLAZE = REVIEW / (
    "blaze_single_cell_expect_sweep_20260810/exploratory/scmixology2/"
    "callsets/expect500_whitelist.txt"
)
SCMIX_BLAZE_METRICS = REVIEW / (
    "blaze_single_cell_expect_sweep_20260810/exploratory/scmixology2/"
    "tables/expect_sensitivity_metrics.tsv"
)
SCMIX_SELECTOR_MEMBERSHIP = REVIEW / (
    "wl_scan/20260804_common_count_selector_ablation/full37/"
    "selector_membership.tsv.gz"
)

RAGESEQ_ROOT = REVIEW / (
    "wl_scan/20260730_rageseq_ERR3268990_tnbc_lymphnode_four_tool"
)
RAGESEQ_ANNOTATIONS = RAGESEQ_ROOT / "analysis/barcode_level_annotations.tsv"
RAGESEQ_LABELS = (
    RAGESEQ_ROOT / "input_evidence/Lymph_node_official_barcodes_labels.tsv.gz"
)
RAGESEQ_BROAD_LABEL_RECALL = RAGESEQ_ROOT / "analysis/broad_label_recall.tsv"
RAGESEQ_CALLSET_METRICS = RAGESEQ_ROOT / "analysis/callset_metrics.tsv"
RAGESEQ_CALL_COLUMNS = {
    "RAD": "called_RAD",
    "BLAZE": "called_BLAZE_2.6.0a0_expect10433",
    "Flexiplex": "called_Flexiplex_f8",
}
RAGESEQ_EXPECTED_IMMUNE_COUNTS = {
    "RAD": (5605, 5978, 5490, 115, 488),
    "BLAZE": (4474, 5978, 3908, 566, 2070),
    "Flexiplex": (3707, 5978, 3677, 30, 2301),
}

PAPER_URL = "https://pmc.ncbi.nlm.nih.gov/articles/PMC13251922/"
PAPER_DOI = "10.64898/2026.05.29.728810"


# Preserve the current Prism's order and display labels, then append the 19
# validated native inputs that it lacks.
CURRENT_17 = [
    ("ScTagger-S_flatQ20", "ScTagger-S_flatQ20"),
    ("ScTagger-L_flatQ20", "ScTagger-L_flatQ20"),
    ("Measles-P7", "Measles-P7"),
    ("Measles-P8-VDJ-enriched", "Measles-P8-VDJ-enriched"),
    ("Measles-P8-WTA", "Measles-P8-WTA"),
    ("PromethION_iPSC", "PromethION_iPSC"),
    ("RAGEseq-cell-line", "RAGEseq-cell-line"),
    ("RAGEseq-TNBC-LN", "RAGEseq-TNBC-LN"),
    ("LongBench-SC-ONT", "LongBench-SC-ONT"),
    ("LongBench-SN-ONT", "LongBench-SN-ONT"),
    ("LongBench-SC-PB", "LongBench-SC-PB"),
    ("LongBench-SN-PB", "LongBench-SN-PB"),
    ("LeBrigand-MOB", "LeBrigand-MOB"),
    ("Isosceles-ovarian-GSE248115", "Isosceles-ovarian-GSE248115"),
    ("Hipp_SN_m1_ONT_Run1", "Tilgner-m1-ONT-Run1"),
    ("Hipp_SN_m1_ONT_Run2", "Tilgner-m1-ONT-Run2"),
    ("Hipp_SN_m1_ONT_Run3", "Tilgner-m1-ONT-Run3"),
]

MISSING_19 = [
    ("ERR15095094_MPNST1_scNaUMIseq_MinION", "ERR15095094_MPNST1_scNaUMIseq_MinION"),
    ("ERR15095095_MPNST1_scNaUMIseq_PromethION", "ERR15095095_MPNST1_scNaUMIseq_PromethION"),
    ("ERR15095096", "ERR15095096"),
    ("ERR15095097", "ERR15095097"),
    ("section12", "section12"),
    ("section16", "section16"),
    ("section17_1T_1B", "section17_1T_1B"),
    ("section17_4T_1B", "section17_4T_1B"),
    ("section22", "section22"),
    ("section31", "section31"),
    ("section32_1T_1B", "section32_1T_1B"),
    ("section32_4T_1B", "section32_4T_1B"),
    ("Hipp_SN_f1_ONT_Run1", "Hipp_SN_f1_ONT_Run1"),
    ("Hipp_SN_f1_ONT_Run2", "Hipp_SN_f1_ONT_Run2"),
    ("Hipp_SN_f2_ONT", "Hipp_SN_f2_ONT"),
    ("Hipp_SN_f3_ONT_Run1", "Hipp_SN_f3_ONT_Run1"),
    ("Hipp_SN_f3_ONT_Run2", "Hipp_SN_f3_ONT_Run2"),
    ("Hipp_SN_m2_ONT", "Hipp_SN_m2_ONT"),
    ("Hipp_SN_m3_ONT", "Hipp_SN_m3_ONT"),
]

NATIVE_ORDER = CURRENT_17 + MISSING_19
ORIGINAL_CANONICAL_IDS = {canonical for canonical, _display in CURRENT_17}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fmt9(value: float) -> str:
    return f"{value:.9f}"


def esc(value: object) -> str:
    return html.escape(str(value), quote=False)


def metric_values(tp: int, fp: int, fn: int) -> tuple[str, str, str]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return fmt9(precision), fmt9(recall), fmt9(f1)


def make_row(
    *, panel: str, display_dataset: str, canonical_id: str, family: str,
    tool: str, calls: int, reference_n: int, tp: int, fp: int, fn: int,
    reference_type: str, reference_description: str, validation_tier: str,
    source_path: str, source_method: str,
) -> dict[str, str]:
    precision, recall, f1 = metric_values(tp, fp, fn)
    return {
        "score_panel": panel,
        "display_dataset": display_dataset,
        "canonical_id": canonical_id,
        "dataset_family": family,
        "tool": tool,
        "calls": str(calls),
        "reference_n": str(reference_n),
        "tp": str(tp),
        "fp": str(fp),
        "fn": str(fn),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "reference_type": reference_type,
        "reference_description": reference_description,
        "validation_tier": validation_tier,
        "source_path": source_path,
        "source_method": source_method,
    }


def read_rageseq_immune_counts() -> dict[str, tuple[int, int, int, int, int]]:
    """Recompute the annotated adaptive-immune proxy directly from barcode rows."""
    truth: set[str] = set()
    calls: dict[str, set[str]] = {tool: set() for tool in TOOLS}
    with RAGESEQ_ANNOTATIONS.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            barcode = row["barcode"]
            label = row["deposited_label"]
            if (
                row["in_deposited_shortread_list"] == "True"
                and (
                    label.startswith("T_cell")
                    or label.startswith("B_cell")
                    or label == "T_B_doublet"
                )
            ):
                truth.add(barcode)
            for tool, column in RAGESEQ_CALL_COLUMNS.items():
                if row[column] == "True":
                    calls[tool].add(barcode)

    observed: dict[str, tuple[int, int, int, int, int]] = {}
    for tool in TOOLS:
        tp = len(calls[tool] & truth)
        fp = len(calls[tool] - truth)
        fn = len(truth - calls[tool])
        observed[tool] = (len(calls[tool]), len(truth), tp, fp, fn)
    if observed != RAGESEQ_EXPECTED_IMMUNE_COUNTS:
        raise SystemExit(
            "RAGEseq annotated-immune counts changed: "
            f"{observed} != {RAGESEQ_EXPECTED_IMMUNE_COUNTS}"
        )
    return observed


def read_native_rows() -> list[dict[str, str]]:
    with MASTER.open(newline="", encoding="utf-8") as handle:
        source = list(csv.DictReader(handle))
    by_key = {(r["physical_input_run"], r["tool"]): r for r in source}
    expected_ids = {r["physical_input_run"] for r in source}
    ordered_ids = {canonical for canonical, _display in NATIVE_ORDER}
    if len(source) != 108 or expected_ids != ordered_ids:
        raise SystemExit(
            f"native master/order mismatch: rows={len(source)}, "
            f"missing={sorted(expected_ids - ordered_ids)}, "
            f"extra={sorted(ordered_ids - expected_ids)}"
        )

    rageseq_counts = read_rageseq_immune_counts()
    rows: list[dict[str, str]] = []
    for canonical, display in NATIVE_ORDER:
        for tool in TOOLS:
            s = by_key[(canonical, tool)]
            if canonical == "RAGEseq-TNBC-LN":
                calls, reference_n, tp, fp, fn = rageseq_counts[tool]
                row = make_row(
                    panel="native_validated_36",
                    display_dataset=display,
                    canonical_id=canonical,
                    family=s["dataset_family"],
                    tool=tool,
                    calls=calls,
                    reference_n=reference_n,
                    tp=tp,
                    fp=fp,
                    fn=fn,
                    reference_type="study_deposited_named_t_b_targetable_positive_proxy",
                    reference_description=(
                        "Explicitly annotated B-cell, T-cell, and T/B-doublet "
                        "barcodes from the matched RAGE-seq TNBC draining-lymph-node "
                        "short-read table (n=5,978). Epithelial_Cancer and the 4,433 "
                        "numeric/unannotated barcodes are not credited as positives; "
                        "therefore precision is conservative. Calls outside this "
                        "named positive proxy are operational FPs, not proven "
                        "biological negatives."
                    ),
                    validation_tier="study_deposited_annotation_proxy",
                    source_path=str(RAGESEQ_ANNOTATIONS),
                    source_method=(
                        "direct barcode-set rescore of ERR3268990: positive labels "
                        "T_cell*, B_cell*, or T_B_doublet; call columns "
                        f"{RAGESEQ_CALL_COLUMNS[tool]}; every selected barcode outside "
                        "the annotated immune set counted as FP"
                    ),
                )
            else:
                row = make_row(
                    panel="native_validated_36",
                    display_dataset=display,
                    canonical_id=canonical,
                    family=s["dataset_family"],
                    tool=tool,
                    calls=int(s["calls"]),
                    reference_n=int(s["reference_n"]),
                    tp=int(s["tp_overlap"]),
                    fp=int(s["fp_unmatched"]),
                    fn=int(s["fn_missed"]),
                    reference_type=s["reference_type"],
                    reference_description=s["reference_description"],
                    validation_tier=s["validation_tier"],
                    source_path=str(MASTER),
                    source_method=(
                        f"master row {s['source_row_key']}; upstream {s['source_table_path']}"
                    ),
                )
                for field, source_field in (
                    ("precision", "precision"), ("recall", "recall"), ("f1", "f1")
                ):
                    if abs(float(row[field]) - float(s[source_field])) > 1e-8:
                        raise SystemExit(
                            f"native metric mismatch {canonical}/{tool}/{field}: "
                            f"{row[field]} vs {s[source_field]}"
                        )
            rows.append(row)
    return rows


def normalized_lines(path: Path) -> set[str]:
    return {
        line.strip().split()[0].removesuffix("-1")
        for line in path.open(encoding="utf-8")
        if line.strip()
    }


def rad_scmix_rds_calls() -> set[str]:
    expression = (
        "x <- readRDS(" + json.dumps(str(SCMIX_RDS)) + "); "
        "cat(x$selected_barcodes, sep='\\n')"
    )
    run = subprocess.run(
        ["Rscript", "-e", expression], check=True, capture_output=True, text=True
    )
    return {line.strip().removesuffix("-1") for line in run.stdout.splitlines() if line.strip()}


def flex_scmix_calls() -> set[str]:
    calls: set[str] = set()
    with gzip.open(SCMIX_SELECTOR_MEMBERSHIP, "rt", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if (
                row["dataset"] == "scMixology2"
                and row["method"] == "Flexiplex"
                and row["mode"] == "exact_flexiplex_filter_v1.02.6"
            ):
                calls.add(row["barcode"].removesuffix("-1"))
    return calls


def read_scmix_rows() -> list[dict[str, str]]:
    truth = normalized_lines(SCMIX_TRUTH)
    rad_native = normalized_lines(SCMIX_RAD_NATIVE)
    rad_rds = rad_scmix_rds_calls()
    if rad_native != rad_rds:
        raise SystemExit("ScMixology2 native RAD callset differs from retained RDS callset")
    calls_by_tool = {
        "RAD": rad_native,
        "BLAZE": normalized_lines(SCMIX_BLAZE),
        "Flexiplex": flex_scmix_calls(),
    }
    source_by_tool = {
        "RAD": str(SCMIX_RAD_NATIVE),
        "BLAZE": str(SCMIX_BLAZE),
        "Flexiplex": str(SCMIX_SELECTOR_MEMBERSHIP),
    }
    method_by_tool = {
        "RAD": (
            "native RAD scan-wl selected callset; set-identical cross-check against "
            f"retained RDS {SCMIX_RDS}"
        ),
        "BLAZE": (
            "published expect-cells=500 selector reconstructed from preserved native "
            "BLAZE raw barcode counts; authentic historical selected file was not retained"
        ),
        "Flexiplex": (
            "Flexiplex v1.02.6 filter replay on the common RAD retained-count table; "
            "not native Flexiplex FASTQ extraction"
        ),
    }
    expected_counts = {
        "RAD": (279, 233, 46, 15),
        "BLAZE": (188, 188, 0, 60),
        "Flexiplex": (184, 183, 1, 65),
    }
    rows: list[dict[str, str]] = []
    for tool in TOOLS:
        calls = calls_by_tool[tool]
        tp = len(calls & truth)
        fp = len(calls - truth)
        fn = len(truth - calls)
        observed = (len(calls), tp, fp, fn)
        if observed != expected_counts[tool]:
            raise SystemExit(
                f"ScMixology2 {tool} changed: {observed} != {expected_counts[tool]}"
            )
        rows.append(make_row(
            panel="scmixology2_reconstructed",
            display_dataset="ScMixology2 [reconstructed]",
            canonical_id="ScMixology2",
            family="ScMixology2",
            tool=tool,
            calls=len(calls),
            reference_n=len(truth),
            tp=tp,
            fp=fp,
            fn=fn,
            reference_type="matched_cellranger_positive_proxy",
            reference_description=(
                "Matched Cell Ranger whitelist of 248 retained barcodes is a positive "
                "proxy, not exhaustive biological negative truth. Metrics are an "
                "operational concordance comparison, and tool execution sources are "
                "heterogeneous; see validation_tier and source_method."
            ),
            validation_tier="exploratory_reconstructed_mixed_execution",
            source_path=source_by_tool[tool],
            source_method=method_by_tool[tool],
        ))

    with SCMIX_BLAZE_METRICS.open(newline="", encoding="utf-8") as handle:
        baseline = next(
            r for r in csv.DictReader(handle, delimiter="\t")
            if r["mode"] == "expect500"
        )
    blaze = next(r for r in rows if r["tool"] == "BLAZE")
    for ours, source_name in (
        ("tp", "true_positives"), ("fp", "false_positives"),
        ("fn", "false_negatives"), ("precision", "precision"),
        ("recall", "recall"), ("f1", "f1")
    ):
        if abs(float(blaze[ours]) - float(baseline[source_name])) > 1e-9:
            raise SystemExit(f"ScMixology2 BLAZE reconstruction mismatch for {ours}")
    return rows


def validate_metric_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    problems: list[str] = []
    by_dataset: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_dataset[(row["score_panel"], row["display_dataset"])].append(row)
        calls, ref = int(row["calls"]), int(row["reference_n"])
        tp, fp, fn = (int(row[field]) for field in COUNT_FIELDS)
        if calls != tp + fp:
            problems.append(f"{row['display_dataset']}/{row['tool']}: calls != TP+FP")
        if ref != tp + fn:
            problems.append(f"{row['display_dataset']}/{row['tool']}: reference != TP+FN")
        precision, recall, f1 = metric_values(tp, fp, fn)
        for field, expected in (("precision", precision), ("recall", recall), ("f1", f1)):
            if row[field] != expected:
                problems.append(
                    f"{row['display_dataset']}/{row['tool']}: {field} "
                    f"{row[field]} != {expected}"
                )
    for key, group in by_dataset.items():
        if [r["tool"] for r in group] != TOOLS:
            problems.append(f"{key}: tool order/presence is not {TOOLS}")
        if len({r["reference_n"] for r in group}) != 1:
            problems.append(f"{key}: reference size varies by tool")
    if problems:
        raise SystemExit("metric validation FAILED:\n  " + "\n  ".join(problems))
    return [{"check": "metric_rows", "status": "PASS", "detail": (
        f"{len(rows)} rows; {len(by_dataset)} scored inputs; TP/FP/FN identities "
        "and recalculated precision/recall/F1 all match"
    )}]


def validate_original_overlap(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    native = {
        (row["canonical_id"], row["tool"]): row
        for row in rows if row["score_panel"] == "native_validated_36"
    }
    aliases = {
        f"Tilgner-m1-ONT-Run{run}": f"Hipp_SN_m1_ONT_Run{run}"
        for run in (1, 2, 3)
    }
    with ORIGINAL_GRAPH_READY.open(newline="", encoding="utf-8") as handle:
        original = list(csv.DictReader(handle))
    if len(original) != 51:
        raise SystemExit(f"original graph-ready row count changed: {len(original)}")
    fields = [
        ("TP", "tp"), ("FP", "fp"), ("FN", "fn"), ("F1", "f1"),
        ("Precision", "precision"), ("Recall", "recall"),
    ]
    comparisons = 0
    original_rageseq = {
        "RAD": (5585, 20, 4848),
        "BLAZE": (4109, 365, 6324),
        "Flexiplex": (3696, 11, 6737),
    }
    for source in original:
        canonical = aliases.get(source["Dataset"], source["Dataset"])
        current = native[(canonical, source["Tool"])]
        if canonical == "RAGEseq-TNBC-LN":
            got = (int(source["TP"]), int(source["FP"]), int(source["FN"]))
            if got != original_rageseq[source["Tool"]]:
                raise SystemExit(
                    f"original RAGEseq baseline changed for {source['Tool']}: "
                    f"{got} != {original_rageseq[source['Tool']]}"
                )
            continue
        for source_field, current_field in fields:
            if abs(float(source[source_field]) - float(current[current_field])) > 1e-8:
                raise SystemExit(
                    f"original overlap changed: {source['Dataset']}/{source['Tool']}/"
                    f"{source_field} {source[source_field]} != {current[current_field]}"
                )
            comparisons += 1
    return [
        {
            "check": "original_overlap_except_rageseq_immune_override",
            "status": "PASS",
            "detail": (
                f"16 original inputs x 3 tools x 6 numeric fields = {comparisons} "
                "comparisons; 0 mismatches"
            ),
        },
        {
            "check": "rageseq_tnbc_ln_immune_override",
            "status": "PASS",
            "detail": (
                "Original all-10,433 proxy baseline preserved as audit input; output "
                "recomputed from 5,978 explicitly annotated B/T/T-B-doublet barcodes"
            ),
        },
    ]


def write_delimited(path: Path, rows: list[dict[str, str]], delimiter: str) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter=delimiter,
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def paper_fields(canonical_id: str) -> tuple[str, str, str]:
    if canonical_id == "ScTagger-L_flatQ20":
        return "TRUE", "ScTagger", "Whitelist precision/recall/F1 and read assignment"
    if canonical_id == "RAGEseq-cell-line":
        return "TRUE", "RAGE-Seq Cell Lines", "Whitelist precision/recall/F1 and receptor analysis"
    if canonical_id == "LongBench-SC-ONT":
        return "TRUE", "LongBench SC-ONT", "Runtime comparison in frozen v1; later whitelist comparison"
    if canonical_id.startswith("section"):
        return "TRUE", "Visium 3' Tonsil", "Spatial VDJ biology in frozen v1; later per-library whitelist comparison"
    if canonical_id == "ScMixology2":
        return "TRUE", "ScMixology2", "Timing/memory and depth in frozen v1; later reconstructed whitelist comparison"
    return "FALSE", "", ""


def build_inventory(metric_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for metric in metric_rows:
        key = (metric["score_panel"], metric["canonical_id"])
        if key in seen:
            continue
        seen.add(key)
        in_paper, paper_dataset, paper_use = paper_fields(metric["canonical_id"])
        unit_type = "physical_or_technical_input"
        if metric["canonical_id"].startswith("section"):
            unit_type = "technical_library_within_paper_dataset"
        if metric["canonical_id"].startswith("ScTagger"):
            unit_type = "synthetic_benchmark_input"
        rows.append({
            "inventory_order": str(len(rows) + 1),
            "canonical_id": metric["canonical_id"],
            "display_dataset": metric["display_dataset"],
            "dataset_family": metric["dataset_family"],
            "unit_type": unit_type,
            "in_frozen_paper_v1": in_paper,
            "paper_dataset": paper_dataset,
            "paper_use": paper_use,
            "in_original_prism": (
                "TRUE" if metric["canonical_id"] in ORIGINAL_CANONICAL_IDS else "FALSE"
            ),
            "processed": "TRUE",
            "processed_not_original_prism": (
                "FALSE" if metric["canonical_id"] in ORIGINAL_CANONICAL_IDS else "TRUE"
            ),
            "three_tool_score_available": "TRUE",
            "score_panel": metric["score_panel"],
            "reference_type": metric["reference_type"],
            "validation_tier": metric["validation_tier"],
            "notes": metric["reference_description"],
        })

    # User requested that LR-Split-seq and NBC be left out. Visium HD remains
    # inventory-only because its split-barcode exact-read endpoint is not a
    # comparable scalar whitelist P/R/F1 measurement.
    rows.append({
        "inventory_order": str(len(rows) + 1),
        "canonical_id": "Visium-HD-3p-mouse-brain",
        "display_dataset": "Visium HD 3' mouse brain",
        "dataset_family": "Visium HD",
        "unit_type": "paper_dataset_parent",
        "in_frozen_paper_v1": "TRUE",
        "paper_dataset": "Visium HD 3' mouse brain",
        "paper_use": (
            "Four ONT flowcells; PBC44593 plotted for spatial exact-read recovery"
        ),
        "in_original_prism": "FALSE",
        "processed": "TRUE",
        "processed_not_original_prism": "TRUE",
        "three_tool_score_available": "FALSE",
        "score_panel": "",
        "reference_type": "split_barcode_exact_read_recovery_not_scalar_f1",
        "validation_tier": "not_comparable_to_single_barcode_whitelist_detection",
        "notes": (
            "Inventory only. Physical inputs PBC44593, PBC44760, PBC49262, "
            "PBC52788; no comparable scalar RAD/BLAZE/Flexiplex precision, recall, F1."
        ),
    })
    return rows


def build_paper_inventory() -> list[dict[str, str]]:
    return [
        {
            "paper_order": "1", "paper_dataset": "ScTagger",
            "local_mapping": "ScTagger-L_flatQ20",
            "paper_endpoint": "Whitelist P/R/F1 and read assignment",
            "project_score_status": "native_validated_36",
            "notes": "ScTagger-S is retained as a processed/original-Prism benchmark, not an extra paper dataset.",
        },
        {
            "paper_order": "2", "paper_dataset": "ScMixology2",
            "local_mapping": "ScMixology2",
            "paper_endpoint": "Timing/memory and depth",
            "project_score_status": "scmixology2_reconstructed",
            "notes": "Later score uses the 248-barcode Cell Ranger reference and heterogeneous reconstructed execution; see metric provenance.",
        },
        {
            "paper_order": "3", "paper_dataset": "RAGE-Seq Cell Lines",
            "local_mapping": "RAGEseq-cell-line / ERR3268991",
            "paper_endpoint": "Whitelist P/R/F1 and receptor concordance",
            "project_score_status": "native_validated_36", "notes": "",
        },
        {
            "paper_order": "4", "paper_dataset": "LongBench SC-ONT",
            "local_mapping": "LongBench-SC-ONT",
            "paper_endpoint": "Runtime in frozen v1",
            "project_score_status": "native_validated_36",
            "notes": "Later reviewer analysis supplies the whitelist metrics.",
        },
        {
            "paper_order": "5", "paper_dataset": "Visium 3' Tonsil",
            "local_mapping": (
                "section12; section16; section17_1T_1B; section17_4T_1B; "
                "section22; section31; section32_1T_1B; section32_4T_1B"
            ),
            "paper_endpoint": "Spatial VDJ biology",
            "project_score_status": "native_validated_36",
            "notes": "One paper dataset represented by six sections/eight technical libraries.",
        },
        {
            "paper_order": "6", "paper_dataset": "Visium HD 3' mouse brain",
            "local_mapping": "PBC44593; PBC44760; PBC49262; PBC52788",
            "paper_endpoint": "Split-barcode spatial exact-read recovery",
            "project_score_status": "inventory_only_not_comparable",
            "notes": "No scalar single-barcode three-tool P/R/F1.",
        },
    ]


def grouped_table_xml(
    table_id: str, title: str, row_titles: list[str],
    columns: list[tuple[str, list[str]]], decimals: int,
    table_type: str = "TwoWay", row_width: int = 220, col_width: int = 105,
) -> str:
    parts = [
        f'  <Table ID="{table_id}" XFormat="none" YFormat="replicates" '
        f'Replicates="1" TableType="{table_type}" EVFormat="AsteriskAfterNumber">\n',
        f"    <Title>{esc(title)}</Title>\n",
        f'    <RowTitlesColumn Width="{row_width}">\n',
        "      <Subcolumn>\n",
    ]
    parts.extend(f"        <d>{esc(label)}</d>\n" for label in row_titles)
    parts.append("      </Subcolumn>\n    </RowTitlesColumn>\n")
    for col_title, values in columns:
        if len(values) != len(row_titles):
            raise SystemExit(f"{title}/{col_title}: ragged column")
        parts.extend([
            f'    <YColumn Width="{col_width}" Decimals="{decimals}" Subcolumns="1">\n',
            f"      <Title>{esc(col_title)}</Title>\n",
            "      <Subcolumn>\n",
        ])
        parts.extend(f"        <d>{esc(value)}</d>\n" for value in values)
        parts.append("      </Subcolumn>\n    </YColumn>\n")
    parts.append("  </Table>\n")
    return "".join(parts)


def make_table_specs(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    by_panel_dataset: dict[tuple[str, str], dict[str, dict[str, str]]] = defaultdict(dict)
    panel_order: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        key = (row["score_panel"], row["display_dataset"])
        by_panel_dataset[key][row["tool"]] = row
        if row["display_dataset"] not in panel_order[row["score_panel"]]:
            panel_order[row["score_panel"]].append(row["display_dataset"])

    specs: list[dict[str, object]] = []
    panel_titles = {
        "native_validated_36": "Native validated 36",
        "scmixology2_reconstructed": "ScMixology2 reconstructed",
    }
    for panel in ("native_validated_36", "scmixology2_reconstructed"):
        datasets = panel_order[panel]
        for dataset in datasets:
            cells = by_panel_dataset[(panel, dataset)]
            specs.append({
                "panel": panel,
                "title": f"{dataset} TP-FP-FN",
                "rows": TOOLS,
                "columns": [
                    (field.upper(), [cells[tool][field] for tool in TOOLS])
                    for field in COUNT_FIELDS
                ],
                "decimals": 0,
                "table_type": "TwoWay",
            })
        for metric in METRIC_FIELDS:
            specs.append({
                "panel": panel,
                "title": f"{panel_titles[panel]} {metric.capitalize()} by dataset",
                "rows": datasets,
                "columns": [
                    (tool, [by_panel_dataset[(panel, ds)][tool][metric] for ds in datasets])
                    for tool in TOOLS
                ],
                "decimals": 9,
                "table_type": "TwoWay",
            })
        if len(datasets) > 1:
            for metric in METRIC_FIELDS:
                specs.append({
                    "panel": panel,
                    "title": f"{panel_titles[panel]} matched {metric.capitalize()}",
                    "rows": datasets,
                    "columns": [
                        (tool, [by_panel_dataset[(panel, ds)][tool][metric] for ds in datasets])
                        for tool in TOOLS
                    ],
                    "decimals": 9,
                    "table_type": "OneWay",
                })

    # Combined convenience summaries are intentionally labelled scope-mixed.
    combined_order = (
        panel_order["native_validated_36"]
        + panel_order["scmixology2_reconstructed"]
    )
    row_lookup = {r["display_dataset"]: {} for r in rows}
    for row in rows:
        row_lookup[row["display_dataset"]][row["tool"]] = row
    for metric in METRIC_FIELDS:
        specs.append({
            "panel": "all_scored_scope_mixed",
            "title": f"All scored scope-mixed {metric.capitalize()} by dataset",
            "rows": combined_order,
            "columns": [
                (tool, [row_lookup[ds][tool][metric] for ds in combined_order])
                for tool in TOOLS
            ],
            "decimals": 9,
            "table_type": "TwoWay",
        })
    return specs


def write_pzfx(path: Path, specs: list[dict[str, object]], generated_utc: str) -> None:
    notes = (
        "Complete whitelist-detection data project. Native panel: 36 physical inputs, "
        "108 tool rows; 35 inputs retain the independently validated native master and "
        "RAGEseq-TNBC-LN is rescored against 5,978 explicitly annotated B/T/T-B-doublet "
        "barcodes. Its 4,433 numeric/unannotated short-read barcodes are not credited as "
        "positives, so its precision is conservative. The first 17 preserve the uploaded "
        "Prism order and 19 missing native inputs are appended. ScMixology2 is isolated "
        "in a reconstructed panel using a matched "
        "248-barcode Cell Ranger positive proxy: RAD is the live native scan-wl "
        "scan-wl callset, BLAZE is reconstructed from preserved native raw counts at the "
        "published 500-cell expectation, and Flexiplex is a filter replay on common RAD "
        "counts. Do not describe that mixed-execution panel as a native head-to-head run. "
        "The final three scope-mixed sheets are graphing conveniences and must retain that "
        "qualification. Visium HD is inventory-only because its split-barcode exact-read "
        "endpoint is not a comparable scalar whitelist F1. LR-Split-seq, NBC, AIR-SPACE, "
        "and extra ScTagger quality conditions were omitted at the user's direction. "
        "Reference semantics remain explicit in complete_three_tool_metrics.csv. The "
        "original native .prism was not overwritten. Open this PZFX in Prism and Save As "
        f"a new .prism file. Generated {generated_utc}."
    )
    with path.open("w", encoding="utf-8", newline="") as out:
        out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        out.write('<GraphPadPrismFile PrismXMLVersion="5.00">\n')
        out.write("  <Created>\n")
        out.write(
            '    <OriginalVersion CreatedByProgram="GraphPad Prism" '
            f'CreatedByVersion="6.0f.254" Login="" DateTime="{esc(generated_utc)}"/>\n'
        )
        out.write("  </Created>\n")
        out.write("  <InfoSequence>\n    <Ref ID=\"Info0\" Selected=\"1\"/>\n  </InfoSequence>\n")
        out.write("  <Info ID=\"Info0\">\n")
        out.write("    <Title>Complete whitelist comparison provenance</Title>\n")
        out.write("    <Notes>\n")
        out.write(f'      <Font Color="#000000" Face="Helvetica">{esc(notes)}<BR/></Font>\n')
        out.write("    </Notes>\n  </Info>\n")
        out.write("  <TableSequence>\n")
        for index in range(len(specs)):
            selected = ' Selected="1"' if index == 0 else ""
            out.write(f'    <Ref ID="Table{index}"{selected}/>\n')
        out.write("  </TableSequence>\n")
        for index, spec in enumerate(specs):
            out.write(grouped_table_xml(
                f"Table{index}", str(spec["title"]), list(spec["rows"]),
                list(spec["columns"]), int(spec["decimals"]),
                str(spec["table_type"]),
            ))
        out.write("</GraphPadPrismFile>\n")


def validate_pzfx(path: Path, specs: list[dict[str, object]]) -> list[dict[str, str]]:
    root = ET.parse(path).getroot()
    xml_tables = root.findall("Table")
    if len(xml_tables) != len(specs):
        raise SystemExit(f"PZFX table count {len(xml_tables)} != {len(specs)}")
    sequence = [ref.get("ID") for ref in root.find("TableSequence").findall("Ref")]
    if sequence != [f"Table{i}" for i in range(len(specs))]:
        raise SystemExit("PZFX TableSequence mismatch")
    report: list[dict[str, str]] = []
    for index, (node, spec) in enumerate(zip(xml_tables, specs)):
        title = node.findtext("Title")
        row_titles = [d.text or "" for d in node.findall("RowTitlesColumn/Subcolumn/d")]
        ycols = node.findall("YColumn")
        if title != spec["title"] or row_titles != spec["rows"]:
            raise SystemExit(f"Table{index}: title/row mismatch")
        if node.get("TableType") != spec["table_type"] or node.get("Replicates") != "1":
            raise SystemExit(f"Table{index}: attribute mismatch")
        if [y.findtext("Title") for y in ycols] != [c[0] for c in spec["columns"]]:
            raise SystemExit(f"Table{index}: column-title mismatch")
        numeric_cells = 0
        for ycol, (_title, wanted) in zip(ycols, spec["columns"]):
            got = [d.text or "" for d in ycol.findall("Subcolumn/d")]
            if got != wanted:
                raise SystemExit(f"Table{index}: cell mismatch")
            for value in got:
                parsed = float(value)
                if not math.isfinite(parsed):
                    raise SystemExit(f"Table{index}: non-finite cell {value}")
            numeric_cells += len(got)
        report.append({
            "table": f"Table{index}", "title": str(spec["title"]),
            "panel": str(spec["panel"]), "rows": str(len(spec["rows"])),
            "columns": str(len(spec["columns"])),
            "numeric_cells": str(numeric_cells), "status": "PASS",
        })
    return report


def write_readme(path: Path, inventory_rows: list[dict[str, str]], metric_rows: list[dict[str, str]]) -> None:
    native_missing = [display for canonical, display in MISSING_19]
    text = f"""# Complete three-tool whitelist data handoff (2026-09-01; RAGEseq immune correction)

## Result

This package reconciles the paper, the uploaded `three_tool_whitelist_data.prism`,
and completed whitelist-detection analyses within the requested scope. The
RAGEseq-TNBC-LN row is rescored against the explicitly annotated adaptive-immune
short-read subset rather than treating every deposited short-read cell as an
expected positive.

- **38 inventory entries**: 37 scored entries plus Visium HD as inventory-only.
- **37 scored entries / {len(metric_rows)} tool rows**: 35 native inputs retain the
  independently validated master, RAGEseq-TNBC-LN has a separately validated
  immune-only rescore, and ScMixology2 remains separately labelled reconstruction.
- **17 native inputs already in the uploaded Prism; 19 native inputs added.**
- LR-Split-seq, NBC, AIR-SPACE, and extra ScTagger quality conditions are omitted
  per user direction. The two canonical ScTagger flat-Q20 entries remain.

## Primary files

- `three_tool_whitelist_data_COMPLETE_RAGESEQ_IMMUNE_20260901.pzfx`: data-only
  Prism XML project.
- `complete_three_tool_metrics.csv` / `.tsv`: all scored rows and provenance.
- `sample_inventory.tsv`: paper / original-Prism / processed status for every
  included inventory entry.
- `paper_inventory.tsv`: frozen-paper top-level mapping within the requested scope.
- `PZFX_VALIDATION.tsv`: table-by-table cell-level reparse validation.
- `VALIDATION_SUMMARY.json`: global invariants and counts.
- `SOURCE_MANIFEST.tsv`, `SHA256SUMS`: source and package integrity.
- `scripts/build_complete_whitelist_project_rageseq_immune.py`: exact reproducible
  builder.

## Native expansion

The 19 native inputs absent from the uploaded Prism are:

{chr(10).join(f'- `{name}`' for name in native_missing)}

The baseline native source is `{MASTER}`. Its upstream package reports 687/687
independent validation checks passing. Sixteen of the 17 overlapping inputs remain
cell-for-cell identical to the uploaded Prism (after the documented Tilgner alias
mapping). RAGEseq-TNBC-LN is the intentional exception described below.

## RAGEseq TNBC draining-lymph-node immune correction

The public matched short-read file has 10,433 barcodes, but only 5,978 are
explicitly annotated adaptive-immune-containing cells: 4,255 T cells, 1,637 B
cells, and 86 T/B doublets. The prior project treated all 10,433 as expected
positives. This project recomputes TP/FP/FN directly from `{RAGESEQ_ANNOTATIONS}`
using those 5,978 barcodes as the positive set. Calls to the 22 epithelial cells,
the 4,433 numeric/unannotated barcodes, or barcodes outside the deposited list are
counted as false positives. The numeric block has undocumented biology, so these
precision values are conservative and the reference is labelled
`study_deposited_named_t_b_targetable_positive_proxy`, not exhaustive biological
truth.

## ScMixology2 boundary

ScMixology2 is scored against the matched 248-barcode Cell Ranger positive proxy, but
it is **not pooled into the native matched-statistics sheets**. RAD uses the live
native scan-wl callset (cross-checked set-identical against the retained RDS); BLAZE uses the published 500-cell selector reconstructed
from its preserved native raw-count table; Flexiplex uses its v1.02.6 filter replay
on common RAD retained counts. The source paths and method caveats appear on every
row in `complete_three_tool_metrics.csv`.

## Prism format limitation

The original native `.prism` is unchanged. Writing new table data into GraphPad's
undocumented native `.prism` archive is not safely supported, and no licensed Prism
runtime is installed on this host. Open the generated `.pzfx` in Prism and use
**Save As** to create a new native `.prism` file. The uploaded native file also has
a pre-existing Layout 1 structural-verification failure, which is another reason it
was not binary-edited.

## Reference semantics

Do not collapse the reference classes:

- `exact_truth`: synthetic truth.
- `matched_short_read_positive_proxy`: matched short-read retained cells; positive
  evidence, not literal exhaustive biological truth.
- `study_deposited_named_t_b_targetable_positive_proxy`: explicitly annotated
  B/T/T-B-doublet subset of the matched RAGEseq TNBC lymph-node short-read
  barcodes; numeric labels are not credited as positives, making precision
  conservative. Calls outside the named proxy are operational false positives,
  not proven biological negatives.
- `spatial_on_tissue_operational`: operational on-tissue spatial reference.
- `matched_cellranger_positive_proxy`: the separately labelled ScMixology2
  reconstruction.

Frozen paper source: {PAPER_URL} (DOI `{PAPER_DOI}`).
"""
    path.write_text(text, encoding="utf-8")


def source_manifest(paths: list[Path]) -> list[dict[str, str]]:
    rows = []
    for path in paths:
        if not path.is_file():
            raise SystemExit(f"required source missing: {path}")
        rows.append({
            "path": str(path), "size_bytes": str(path.stat().st_size),
            "sha256": sha256(path), "status": "LIVE_HASHED",
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--convenience-pzfx", type=Path)
    args = parser.parse_args()
    if args.out_dir.exists():
        raise SystemExit(f"refusing to overwrite existing output directory: {args.out_dir}")

    if sha256(ORIGINAL_PRISM) != ORIGINAL_PRISM_SHA256:
        raise SystemExit("uploaded Prism SHA-256 changed; stop and re-audit")

    generated_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    metric_rows = read_native_rows() + read_scmix_rows()
    global_checks = validate_metric_rows(metric_rows)
    global_checks.extend(validate_original_overlap(metric_rows))
    inventory_rows = build_inventory(metric_rows)
    paper_rows = build_paper_inventory()

    args.out_dir.mkdir(parents=True)
    pzfx = args.out_dir / "three_tool_whitelist_data_COMPLETE_RAGESEQ_IMMUNE_20260901.pzfx"
    metrics_csv = args.out_dir / "complete_three_tool_metrics.csv"
    metrics_tsv = args.out_dir / "complete_three_tool_metrics.tsv"
    inventory_tsv = args.out_dir / "sample_inventory.tsv"
    paper_tsv = args.out_dir / "paper_inventory.tsv"
    validation_tsv = args.out_dir / "PZFX_VALIDATION.tsv"

    write_delimited(metrics_csv, metric_rows, ",")
    write_delimited(metrics_tsv, metric_rows, "\t")
    write_delimited(inventory_tsv, inventory_rows, "\t")
    write_delimited(paper_tsv, paper_rows, "\t")

    specs = make_table_specs(metric_rows)
    write_pzfx(pzfx, specs, generated_utc)
    table_report = validate_pzfx(pzfx, specs)
    write_delimited(validation_tsv, table_report, "\t")

    sources = [
        ORIGINAL_PRISM, ORIGINAL_GRAPH_READY, MASTER, SCMIX_RAD_NATIVE, SCMIX_RDS,
        SCMIX_TRUTH, SCMIX_BLAZE,
        SCMIX_BLAZE_METRICS, SCMIX_SELECTOR_MEMBERSHIP,
        RAGESEQ_ANNOTATIONS, RAGESEQ_LABELS, RAGESEQ_BROAD_LABEL_RECALL,
        RAGESEQ_CALLSET_METRICS,
    ]
    write_delimited(args.out_dir / "SOURCE_MANIFEST.tsv", source_manifest(sources), "\t")

    original_after = sha256(ORIGINAL_PRISM)
    if original_after != ORIGINAL_PRISM_SHA256:
        raise SystemExit("original Prism changed during build")
    native_rows = [r for r in metric_rows if r["score_panel"] == "native_validated_36"]
    scmix_rows = [r for r in metric_rows if r["score_panel"] == "scmixology2_reconstructed"]
    global_checks.extend([
        {"check": "native_shape", "status": "PASS", "detail": f"{len(native_rows)} rows = 36 inputs x 3 tools"},
        {"check": "scmix_shape", "status": "PASS", "detail": f"{len(scmix_rows)} rows = 1 input x 3 tools"},
        {"check": "inventory_shape", "status": "PASS", "detail": f"{len(inventory_rows)} entries; 37 scored + Visium HD inventory-only"},
        {"check": "original_prism_unchanged", "status": "PASS", "detail": original_after},
        {"check": "pzfx_cell_reparse", "status": "PASS", "detail": (
            f"{len(table_report)} tables; {sum(int(r['numeric_cells']) for r in table_report)} numeric cells"
        )},
    ])
    summary = {
        "status": "PASS",
        "generated_utc": generated_utc,
        "inventory_entries": len(inventory_rows),
        "scored_inputs": len(metric_rows) // 3,
        "metric_rows": len(metric_rows),
        "native_inputs": len(native_rows) // 3,
        "original_prism_native_inputs": 17,
        "new_native_inputs": 19,
        "scmixology2_reconstructed_inputs": len(scmix_rows) // 3,
        "pzfx_tables": len(table_report),
        "pzfx_numeric_cells": sum(int(r["numeric_cells"]) for r in table_report),
        "checks": global_checks,
    }
    (args.out_dir / "VALIDATION_SUMMARY.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    write_readme(args.out_dir / "README.md", inventory_rows, metric_rows)
    script_dir = args.out_dir / "scripts"
    script_dir.mkdir()
    shutil.copy2(Path(__file__).resolve(), script_dir / Path(__file__).name)

    if args.convenience_pzfx:
        if args.convenience_pzfx.exists():
            raise SystemExit(f"refusing to overwrite convenience file: {args.convenience_pzfx}")
        shutil.copy2(pzfx, args.convenience_pzfx)

    package_files = sorted(
        path for path in args.out_dir.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS"
    )
    with (args.out_dir / "SHA256SUMS").open("w", encoding="utf-8") as handle:
        for path in package_files:
            handle.write(f"{sha256(path)}  {path.relative_to(args.out_dir)}\n")

    print(json.dumps(summary, indent=2))
    print(f"PZFX: {pzfx}")
    if args.convenience_pzfx:
        print(f"Convenience copy: {args.convenience_pzfx}")


if __name__ == "__main__":
    main()
