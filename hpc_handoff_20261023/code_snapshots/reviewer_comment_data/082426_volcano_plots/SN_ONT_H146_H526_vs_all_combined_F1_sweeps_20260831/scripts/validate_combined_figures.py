#!/usr/bin/env python3
"""Independent validation for combined one-vs-all and direct F1 sweeps."""

from __future__ import annotations

import csv
import gzip
import hashlib
import math
import struct
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INPUTS = ROOT / "inputs"
FIGURES_DIR = ROOT / "figures"
OVA_GRID = INPUTS / "directional_F1_threshold_sweep_grid.tsv"
DIRECT_DATA = INPUTS / "direct_H146_vs_H526_plot_data.tsv.gz"
DIRECT_GRID = INPUTS / "direct_H146_H526_F1_threshold_sweep_grid.tsv"
DIRECT_REFERENCE = INPUTS / "direct_H146_H526_reference_threshold_results.tsv"
DIRECT_BEST = INPUTS / "direct_H146_H526_best_thresholds.tsv"
DIRECT_PARAMETERS = INPUTS / "direct_H146_H526_analysis_parameters.tsv"
LAYOUT = ROOT / "PANEL_LAYOUT.tsv"
SOURCE = ROOT / "SOURCE_INPUT_SHA256.tsv"
REPORT = ROOT / "VALIDATION.tsv"
GENERATOR = ROOT / "scripts" / "generate_combined_figures.R"

OVA_ROOT = Path(
    "/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/"
    "082426_volcano_plots/SN_ONT_H146_H526_vs_all_directional_F1_sweeps_20260831"
)
DIRECT_ROOT = Path(
    "/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/"
    "082426_volcano_plots/Illumina_tool_confidence_19plots_20260825"
)

FIGURES = {
    "01_H146_low_high_combined_3tools_F1_threshold_sweep": (5400, 7200),
    "02_H526_low_high_combined_3tools_F1_threshold_sweep": (5400, 7200),
    "03_H526_high_H146_high_direct_side_by_side_3tools_F1_threshold_sweep": (5700, 7200),
}
TOOLS = ("RAD", "BLAZE", "Flexiplex")
FDRS = (1e-8, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2, 1e-1)
FCS = (0.10, 0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 2.00, 2.50, 3.00)
DIRECT_DIRECTIONS = ("H526_high", "H146_high")
EXPECTED_DIRECT_REFERENCE = {
    ("H146_high", "RAD"): 0.677524429967427,
    ("H146_high", "BLAZE"): 0.612665684830633,
    ("H146_high", "Flexiplex"): 0.643147896879240,
    ("H526_high", "RAD"): 0.540284360189574,
    ("H526_high", "BLAZE"): 0.473962264150943,
    ("H526_high", "Flexiplex"): 0.496111975116641,
}
EXPECTED_DIRECT_BEST = {
    ("H146_high", "RAD"): (0.10, 1.25, 0.694581280788177),
    ("H146_high", "BLAZE"): (0.10, 1.25, 0.639344262295082),
    ("H146_high", "Flexiplex"): (0.10, 1.00, 0.646766169154229),
    ("H526_high", "RAD"): (0.01, 0.75, 0.549044585987261),
    ("H526_high", "BLAZE"): (0.05, 0.75, 0.482278481012658),
    ("H526_high", "Flexiplex"): (0.10, 0.75, 0.512195121951220),
}

checks: list[tuple[str, str, str]] = []


def record(name: str, passed: bool, detail: str) -> None:
    checks.append((name, "PASS" if passed else "FAIL", detail))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def flag(value: str) -> bool:
    return value.upper() == "TRUE"


required = [
    OVA_GRID, DIRECT_DATA, DIRECT_GRID, DIRECT_REFERENCE, DIRECT_BEST,
    DIRECT_PARAMETERS, LAYOUT, SOURCE, GENERATOR,
    INPUTS / "reference_threshold_results.tsv",
    INPUTS / "best_thresholds.tsv",
    INPUTS / "analysis_parameters.tsv",
    INPUTS / "UPSTREAM_SOURCE_INPUT_SHA256.tsv",
    INPUTS / "UPSTREAM_VALIDATION.tsv",
    INPUTS / "UPSTREAM_SHA256SUMS",
    INPUTS / "UPSTREAM_README.md",
    INPUTS / "UPSTREAM_COMPLETE",
    INPUTS / "DIRECT_SOURCE_INPUT_SHA256.tsv",
    INPUTS / "DIRECT_VALIDATION.tsv",
    INPUTS / "DIRECT_COMPLETE",
]
for stem in FIGURES:
    required.extend((FIGURES_DIR / f"{stem}.png", FIGURES_DIR / f"{stem}.svg"))
record(
    "required_files",
    all(path.is_file() and path.stat().st_size > 0 for path in required),
    f"{len(required)} source, derived-table, layout, and figure files present",
)

# The one-vs-all inputs are unchanged from the independently validated package.
ova_rows = read_tsv(OVA_GRID)
ova_keys = {
    (
        row["contrast"], row["direction"], row["tool"],
        float(row["tool_BH_FDR_cutoff"]), float(row["tool_abs_log2FC_cutoff"]),
    )
    for row in ova_rows
}
expected_ova_keys = {
    (contrast, direction, tool, fdr, fc)
    for contrast in ("H146_vs_rest", "H526_vs_rest")
    for direction in ("high", "low")
    for tool in TOOLS for fdr in FDRS for fc in FCS
}
record("ova_grid_rows", len(ova_rows) == 1188, f"rows={len(ova_rows)} expected=1188")
record(
    "ova_grid_keys",
    len(ova_keys) == 1188 and ova_keys == expected_ova_keys,
    "all one-vs-all keys unique and exact",
)
record(
    "ova_grid_universe",
    all(int(row["genes"]) == 12206 for row in ova_rows),
    "12,206 shared genes in every one-vs-all grid cell",
)
ova_truth = {
    (row["contrast"], row["direction"]): int(row["truth_positive"])
    for row in ova_rows
}
record(
    "ova_truth_counts",
    ova_truth == {
        ("H146_vs_rest", "high"): 205,
        ("H146_vs_rest", "low"): 535,
        ("H526_vs_rest", "high"): 186,
        ("H526_vs_rest", "low"): 353,
    },
    "H146 high/low=205/535; H526 high/low=186/353",
)
record(
    "ova_grid_byte_identical_to_upstream",
    sha256(OVA_GRID) == sha256(OVA_ROOT / "tables" / OVA_GRID.name),
    f"SHA256={sha256(OVA_GRID)}",
)

# Independently recompute the complete direct grid from gene-level source data.
direct_rows = read_tsv(DIRECT_DATA)
grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
for row in direct_rows:
    grouped[row["tool"]].append(row)
record("direct_source_rows", len(direct_rows) == 24405, f"rows={len(direct_rows)} expected=24405")
record("direct_source_tools", set(grouped) == set(TOOLS), f"tools={sorted(grouped)}")
record(
    "direct_rows_per_tool",
    all(len(grouped[tool]) == 8135 for tool in TOOLS),
    ", ".join(f"{tool}={len(grouped[tool])}" for tool in TOOLS),
)
direct_gene_sets = {tool: {row["gene_id"] for row in grouped[tool]} for tool in TOOLS}
record(
    "direct_shared_gene_universe",
    all(direct_gene_sets[tool] == direct_gene_sets["RAD"] for tool in TOOLS),
    f"shared genes={len(direct_gene_sets['RAD'])}",
)


def score_direct(rows: list[dict[str, str]], direction: str, fdr: float, fc: float) -> dict[str, float | int]:
    if direction == "H526_high":
        truth = [
            float(row["Illumina_BH_FDR_common"]) < 0.05
            and float(row["Illumina_log2FC"]) < -1.0
            for row in rows
        ]
        predicted = [
            float(row["tool_BH_FDR_common"]) < fdr
            and float(row["tool_log2FC"]) < -fc
            for row in rows
        ]
    else:
        truth = [
            float(row["Illumina_BH_FDR_common"]) < 0.05
            and float(row["Illumina_log2FC"]) > 1.0
            for row in rows
        ]
        predicted = [
            float(row["tool_BH_FDR_common"]) < fdr
            and float(row["tool_log2FC"]) > fc
            for row in rows
        ]
    tp = sum(t and p for t, p in zip(truth, predicted))
    fp = sum((not t) and p for t, p in zip(truth, predicted))
    fn = sum(t and (not p) for t, p in zip(truth, predicted))
    tn = sum((not t) and (not p) for t, p in zip(truth, predicted))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
    return {
        "genes": len(rows), "truth_positive": sum(truth),
        "predicted_positive": sum(predicted), "TP": tp, "FP": fp,
        "FN": fn, "TN": tn, "precision": precision, "recall": recall, "F1": f1,
    }


truth_sets = {
    direction: {
        row["gene_id"]
        for row in grouped["RAD"]
        if float(row["Illumina_BH_FDR_common"]) < 0.05
        and (
            float(row["Illumina_log2FC"]) < -1.0
            if direction == "H526_high"
            else float(row["Illumina_log2FC"]) > 1.0
        )
    }
    for direction in DIRECT_DIRECTIONS
}
record(
    "direct_truth_counts",
    len(truth_sets["H526_high"]) == 769 and len(truth_sets["H146_high"]) == 412,
    f"H526-high={len(truth_sets['H526_high'])}; H146-high={len(truth_sets['H146_high'])}",
)

grid_rows = read_tsv(DIRECT_GRID)
grid_map = {
    (
        row["direction"], row["tool"], float(row["tool_BH_FDR_cutoff"]),
        float(row["tool_abs_log2FC_cutoff"]),
    ): row
    for row in grid_rows
}
expected_direct_keys = {
    (direction, tool, fdr, fc)
    for direction in DIRECT_DIRECTIONS for tool in TOOLS for fdr in FDRS for fc in FCS
}
record("direct_grid_rows", len(grid_rows) == 594, f"rows={len(grid_rows)} expected=594")
record(
    "direct_grid_keys",
    len(grid_map) == 594 and set(grid_map) == expected_direct_keys,
    "all direct keys unique and exact",
)

integer_fields = ("genes", "truth_positive", "predicted_positive", "TP", "FP", "FN", "TN")
float_fields = ("precision", "recall", "F1")
metric_errors: list[str] = []
for key in sorted(expected_direct_keys):
    direction, tool, fdr, fc = key
    expected = score_direct(grouped[tool], direction, fdr, fc)
    observed = grid_map[key]
    for field in integer_fields:
        if int(observed[field]) != expected[field]:
            metric_errors.append(f"{key} {field}: {observed[field]} != {expected[field]}")
    for field in float_fields:
        if not math.isclose(float(observed[field]), float(expected[field]), rel_tol=0, abs_tol=5e-15):
            metric_errors.append(f"{key} {field}: {observed[field]} != {expected[field]}")
record(
    "direct_independent_recalculation_all_594_cells",
    not metric_errors,
    "all direct counts and metrics exact" if not metric_errors else "; ".join(metric_errors[:5]),
)
record(
    "direct_confusion_matrices_close",
    all(sum(int(row[field]) for field in ("TP", "FP", "FN", "TN")) == 8135 for row in grid_rows),
    "TP+FP+FN+TN=8,135 in every direct grid cell",
)

reference_rows = [row for row in grid_rows if flag(row["is_reference"])]
reference_errors: list[str] = []
for row in reference_rows:
    key = (row["direction"], row["tool"])
    if key not in EXPECTED_DIRECT_REFERENCE:
        reference_errors.append(f"unexpected {key}")
    elif not math.isclose(float(row["F1"]), EXPECTED_DIRECT_REFERENCE[key], abs_tol=5e-15):
        reference_errors.append(f"{key} F1={row['F1']}")
    if float(row["tool_BH_FDR_cutoff"]) != 0.05 or float(row["tool_abs_log2FC_cutoff"]) != 1.0:
        reference_errors.append(f"{key} threshold")
record(
    "direct_reference_results",
    len(reference_rows) == 6 and not reference_errors,
    "six reference F1 values match independent expectations"
    if not reference_errors else "; ".join(reference_errors),
)

best_rows = [row for row in grid_rows if flag(row["is_best_in_grid"])]
best_errors: list[str] = []
for row in best_rows:
    key = (row["direction"], row["tool"])
    expected = EXPECTED_DIRECT_BEST.get(key)
    observed = (
        float(row["tool_BH_FDR_cutoff"]), float(row["tool_abs_log2FC_cutoff"]), float(row["F1"])
    )
    if expected is None or any(
        not math.isclose(left, right, rel_tol=0, abs_tol=5e-15)
        for left, right in zip(observed, expected)
    ):
        best_errors.append(f"{key}: {observed} != {expected}")
record(
    "direct_unique_best_results",
    len(best_rows) == 6 and not best_errors,
    "six unique best cells match independent expectations"
    if not best_errors else "; ".join(best_errors),
)

reference_table = read_tsv(DIRECT_REFERENCE)
best_table = read_tsv(DIRECT_BEST)
row_key = lambda row: (
    row["direction"], row["tool"], float(row["tool_BH_FDR_cutoff"]),
    float(row["tool_abs_log2FC_cutoff"]), float(row["F1"]),
)
record(
    "direct_reference_table_matches_grid",
    len(reference_table) == 6 and {row_key(row) for row in reference_table} == {row_key(row) for row in reference_rows},
    "six-row direct reference table matches grid flags",
)
record(
    "direct_best_table_matches_grid",
    len(best_table) == 6 and {row_key(row) for row in best_table} == {row_key(row) for row in best_rows},
    "six-row direct best table matches grid flags",
)

# Explicit panel mapping and signed-axis orientation.
layout_rows = read_tsv(LAYOUT)
record("panel_layout_rows", len(layout_rows) == 18, f"rows={len(layout_rows)} expected=18")
layout_errors: list[str] = []
for row in layout_rows:
    figure = row["figure"]
    tool = row["tool"]
    row_index = int(row["row"])
    column = int(row["column"])
    if tool not in TOOLS or row_index != TOOLS.index(tool) + 1 or column not in (1, 2):
        layout_errors.append(f"row/tool {figure}/{row_index}/{tool}/{column}")
        continue
    if figure.startswith("01_"):
        expected = (
            "H146_vs_rest", "low" if column == 1 else "high", "viridis C (plasma)",
            "negative_reversed" if column == 1 else "positive",
        )
    elif figure.startswith("02_"):
        expected = (
            "H526_vs_rest", "low" if column == 1 else "high", "viridis D",
            "negative_reversed" if column == 1 else "positive",
        )
    elif figure.startswith("03_"):
        expected = (
            "H146_vs_H526_direct", "H526_high" if column == 1 else "H146_high",
            "viridis D" if column == 1 else "viridis C (plasma)",
            "negative_reversed" if column == 1 else "positive",
        )
    else:
        layout_errors.append(f"unexpected figure {figure}")
        continue
    observed = (row["contrast"], row["direction"], row["palette"], row["x_axis"])
    if observed != expected:
        layout_errors.append(f"{figure}/{tool}/col{column}: {observed}!={expected}")
record(
    "exact_requested_panel_layout",
    not layout_errors,
    "one-vs-all low|high and direct H526-high|H146-high mappings are exact"
    if not layout_errors else "; ".join(layout_errors[:5]),
)
record(
    "two_columns_three_rows_each",
    all(
        Counter((int(row["row"]), int(row["column"])) for row in layout_rows if row["figure"] == stem)
        == Counter((r, c) for r in (1, 2, 3) for c in (1, 2))
        for stem in FIGURES
    ),
    "each figure has one panel at every position in a 3x2 grid",
)

# Image structure and visible annotation checks.
image_errors: list[str] = []
svg_texts: dict[str, str] = {}
for stem, expected_dimensions in FIGURES.items():
    png = FIGURES_DIR / f"{stem}.png"
    svg = FIGURES_DIR / f"{stem}.svg"
    with png.open("rb") as handle:
        header = handle.read(24)
    png_ok = header[:8] == b"\x89PNG\r\n\x1a\n"
    dimensions = struct.unpack(">II", header[16:24]) if png_ok else (0, 0)
    if not png_ok or dimensions != expected_dimensions:
        image_errors.append(f"{stem} PNG={dimensions} expected={expected_dimensions}")
    try:
        svg_root = ET.parse(svg).getroot()
        if not svg_root.tag.endswith("svg"):
            image_errors.append(f"{stem} SVG root")
    except ET.ParseError as exc:
        image_errors.append(f"{stem} SVG parse={exc}")
    svg_texts[stem] = svg.read_text(encoding="utf-8")
record(
    "png_svg_structure",
    not image_errors,
    "two 5400x7200 PNGs, one 5700x7200 PNG, and three well-formed SVGs"
    if not image_errors else "; ".join(image_errors),
)

annotation_expectations = {
    "01_H146_low_high_combined_3tools_F1_threshold_sweep": (
        "H146 versus all", "Low (Illumina truth n = 535)", "High (Illumina truth n = 205)",
        "-3.00", "-0.10", "0.10", "3.00", "RAD", "BLAZE", "Flexiplex", "REF", "BEST",
    ),
    "02_H526_low_high_combined_3tools_F1_threshold_sweep": (
        "H526 versus all", "Low (Illumina truth n = 353)", "High (Illumina truth n = 186)",
        "-3.00", "-0.10", "0.10", "3.00", "RAD", "BLAZE", "Flexiplex", "REF", "BEST",
    ),
    "03_H526_high_H146_high_direct_side_by_side_3tools_F1_threshold_sweep": (
        "Direct H146 versus H526", "H526-high (Illumina truth n = 769)",
        "H146-high (Illumina truth n = 412)", "negative direct log2FC", "positive direct log2FC",
        "-3.00", "-0.10", "0.10", "3.00", "RAD", "BLAZE", "Flexiplex", "REF", "BEST",
    ),
}
annotation_errors: list[str] = []
for stem, tokens in annotation_expectations.items():
    missing = [token for token in tokens if token not in svg_texts[stem]]
    if missing:
        annotation_errors.append(f"{stem}: {missing}")
record(
    "figure_annotations_and_signed_axes",
    not annotation_errors,
    "titles, direct semantics, tool rows, labels, and signed axis extremes present"
    if not annotation_errors else "; ".join(annotation_errors),
)
record(
    "old_one_vs_all_high_figure_removed",
    not any(FIGURES_DIR.glob("03_H146_high_H526_high_side_by_side_3tools_F1_threshold_sweep.*")),
    "stale one-vs-all high-comparison figure is absent",
)

generator_text = GENERATOR.read_text(encoding="utf-8")
record(
    "generator_direction_semantics",
    all(token in generator_text for token in (
        'z$Illumina_log2FC < -truth_abs_log2fc', 'z$tool_log2FC < -fc_i',
        'z$Illumina_log2FC > truth_abs_log2fc', 'z$tool_log2FC > fc_i',
        'sprintf("-%.2f", rev(log2fc_grid))', 'sprintf("%.2f", log2fc_grid)',
    )),
    "strict direct inequalities and negative-left/positive-right axes encoded",
)
record(
    "palette_definitions",
    'palettes <- c(H146 = "C", H526 = "D")' in generator_text
    and "direction = -1" in generator_text and "limits = c(0, 1)" in generator_text,
    "H146=viridis C, H526=viridis D, reversed with fixed F1 [0,1]",
)

# Packaged-source and transitive validation integrity.
source_rows = read_tsv(SOURCE)
source_errors: list[str] = []
for row in source_rows:
    packaged = ROOT / row["packaged_relative_path"]
    origin = Path(row["origin_path"])
    for label, path in (("packaged", packaged), ("origin", origin)):
        if (
            not path.is_file()
            or sha256(path) != row["sha256"]
            or path.stat().st_size != int(row["bytes"])
        ):
            source_errors.append(f"{label}:{row['role']}")
record(
    "source_manifest_integrity",
    len(source_rows) == 13 and not source_errors,
    f"verified {len(source_rows)} packaged/origin pairs"
    if not source_errors else "; ".join(source_errors),
)
record(
    "direct_source_sha",
    sha256(DIRECT_DATA) == "c4c038bffcc1db6a98444e12b74cc3a5b6dc85f329defeb87eeec1084c75ef48",
    f"SHA256={sha256(DIRECT_DATA)}",
)

upstream_validation = read_tsv(INPUTS / "UPSTREAM_VALIDATION.tsv")
direct_validation = read_tsv(INPUTS / "DIRECT_VALIDATION.tsv")
record(
    "one_vs_all_upstream_validation",
    len(upstream_validation) == 29 and all(row["status"] == "PASS" for row in upstream_validation),
    f"passing checks={sum(row['status'] == 'PASS' for row in upstream_validation)}/{len(upstream_validation)}",
)
record(
    "direct_upstream_validation",
    len(direct_validation) == 94 and all(row["status"] == "PASS" for row in direct_validation),
    f"passing checks={sum(row['status'] == 'PASS' for row in direct_validation)}/{len(direct_validation)}",
)

upstream_checksum_errors: list[str] = []
with (INPUTS / "UPSTREAM_SHA256SUMS").open("r", encoding="utf-8") as handle:
    upstream_entries = [line.rstrip("\n").split("  ", 1) for line in handle if line.strip()]
for expected_sha, relative in upstream_entries:
    path = OVA_ROOT / relative
    if not path.is_file() or sha256(path) != expected_sha:
        upstream_checksum_errors.append(relative)
record(
    "one_vs_all_upstream_checksum_closure",
    not upstream_checksum_errors,
    f"verified {len(upstream_entries)} upstream checksum entries"
    if not upstream_checksum_errors else "; ".join(upstream_checksum_errors[:5]),
)

with REPORT.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("check", "status", "detail"))
    writer.writerows(checks)

failures = [name for name, status, _ in checks if status != "PASS"]
print(f"validation: {len(checks) - len(failures)}/{len(checks)} checks passed")
print(f"report: {REPORT}")
if failures:
    print("failed: " + ", ".join(failures), file=sys.stderr)
    raise SystemExit(1)
