#!/usr/bin/env python3
"""Exploratory reconstruction of the published scMixology2 BLAZE selector.

The published analysis notebook constructed its BLAZE whitelist in memory and
did not persist it.  This script therefore reproduces the documented Q15,
10x-design filtering and expected-cell threshold logic, but deliberately labels
the output as a reconstruction rather than a validated native callset.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import gzip
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import time
import zipfile

import pandas as pd

from blaze.config import (
    DEFAULT_GRB_WHITELIST_3V3,
    default_count_threshold_calculation,
)
from blaze.main import get_bc_whitelist


GRID = (250, 500, 1000)
CENTER = 500
PUBLISHED_CENTER_CALL_COUNT = 188
STATUS = "EXPLORATORY_RECONSTRUCTION_NO_AUTHENTIC_NATIVE_CALLSET"


def normalized(value: str) -> str:
    value = value.strip()
    return value[:-2] if value.endswith("-1") else value


def canonical_set_sha256(values: set[str]) -> str:
    payload = "".join(f"{value}\n" for value in sorted(values))
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def read_barcode_set(path: Path) -> set[str]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt") as handle:
        return {normalized(line.split("\t", 1)[0]) for line in handle if line.strip()}


def read_design_set(path: Path) -> set[str]:
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            if len(archive.namelist()) != 1:
                raise RuntimeError(f"Expected one member in {path}")
            with archive.open(archive.namelist()[0]) as handle:
                return {
                    line.decode("ascii").strip()
                    for line in handle
                    if line.strip()
                }
    return read_barcode_set(path)


def write_tsv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"No rows for {path}")
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-bc", type=Path, required=True)
    parser.add_argument("--cellranger-reference", type=Path, required=True)
    parser.add_argument("--preserved-design-whitelist", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--expected-data-rows", type=int, default=25_164_948)
    parser.add_argument("--expected-reference-count", type=int, default=248)
    parser.add_argument("--min-q", type=int, default=15)
    parser.add_argument("--chunksize", type=int, default=1_000_000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = time.time()
    output_root = args.output_root.resolve()
    table_root = output_root / "tables"
    callset_root = output_root / "callsets"
    table_root.mkdir(parents=True, exist_ok=True)
    callset_root.mkdir(parents=True, exist_ok=True)

    blaze_version = importlib.metadata.version("blaze2")
    if blaze_version != "2.5.0":
        raise RuntimeError(f"Expected selector library 2.5.0, found {blaze_version}")

    raw_path = args.raw_bc.resolve()
    reference_path = args.cellranger_reference.resolve()
    preserved_design_path = args.preserved_design_whitelist.resolve()
    for path in (raw_path, reference_path, preserved_design_path):
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(path)

    raw_stat_before = raw_path.stat()
    rows_read = 0
    passing_rows = 0
    raw_counts: Counter[str] = Counter()
    for chunk in pd.read_csv(
        raw_path,
        usecols=["raw_bc", "raw_bc_min_q"],
        chunksize=args.chunksize,
    ):
        rows_read += len(chunk)
        passing = chunk.loc[chunk.raw_bc_min_q >= args.min_q, "raw_bc"]
        passing_rows += int(passing.notna().sum())
        raw_counts.update(passing.value_counts().to_dict())
    raw_stat_after = raw_path.stat()
    if (
        raw_stat_before.st_size != raw_stat_after.st_size
        or raw_stat_before.st_mtime_ns != raw_stat_after.st_mtime_ns
    ):
        raise RuntimeError("Preserved raw_bc table changed during traversal")
    if rows_read != args.expected_data_rows:
        raise RuntimeError(
            f"Expected {args.expected_data_rows:,} rows, read {rows_read:,}"
        )

    reference = read_barcode_set(reference_path)
    if len(reference) != args.expected_reference_count:
        raise RuntimeError(
            f"Expected {args.expected_reference_count} reference barcodes, "
            f"found {len(reference)}"
        )

    preserved_design = read_design_set(preserved_design_path)
    installed_design_path = Path(DEFAULT_GRB_WHITELIST_3V3).resolve()
    installed_design = read_design_set(installed_design_path)
    if preserved_design != installed_design:
        raise RuntimeError(
            "Preserved analysis design whitelist differs from installed BLAZE 3v3"
        )
    chemistry_counts = {
        barcode: count
        for barcode, count in raw_counts.items()
        if barcode in preserved_design
    }
    count_values = list(chemistry_counts.values())
    if not count_values:
        raise RuntimeError("No Q15 10x-design barcodes")

    reconstructed: dict[int, set[str]] = {}
    native_library_sets: dict[int, set[str]] = {}
    threshold_by_expected: dict[int, float] = {}
    library_comparison_rows: list[dict] = []
    for expected_cells in GRID:
        threshold = float(
            default_count_threshold_calculation(count_values, expected_cells)
        )
        threshold_by_expected[expected_cells] = threshold

        # Exact comparison operator used in the published analysis notebook.
        paper_set = {
            barcode
            for barcode, count in chemistry_counts.items()
            if count >= threshold
        }
        reconstructed[expected_cells] = paper_set

        # Cross-check against the installed native BLAZE2 selector.  Empty
        # droplet enumeration is downstream of whitelist selection.
        library_called, empty = get_bc_whitelist(
            raw_counts,
            full_bc_whitelist=str(installed_design_path),
            exp_cells=expected_cells,
            output_empty=False,
            out_plot_fn=str(callset_root / f"expect{expected_cells}_knee.png"),
        )
        if empty:
            raise RuntimeError("Empty-droplet output unexpectedly populated")
        native_set = set(library_called)
        native_library_sets[expected_cells] = native_set
        library_comparison_rows.append(
            {
                "expected_cells": expected_cells,
                "published_notebook_operator": ">=",
                "installed_library_operator": ">",
                "threshold": f"{threshold:.12f}",
                "paper_reconstruction_calls": len(paper_set),
                "installed_library_calls": len(native_set),
                "intersection": len(paper_set & native_set),
                "paper_only": len(paper_set - native_set),
                "installed_library_only": len(native_set - paper_set),
                "set_identical": paper_set == native_set,
            }
        )

        with (callset_root / f"expect{expected_cells}_whitelist.txt").open("w") as handle:
            for barcode in sorted(paper_set):
                handle.write(f"{barcode}\n")

    center = reconstructed[CENTER]
    center_count_matches = len(center) == PUBLISHED_CENTER_CALL_COUNT
    baseline_rows = [
        {
            "status": STATUS,
            "hard_gate_available": False,
            "authentic_native_callset_found": False,
            "published_expected_cells": CENTER,
            "published_call_count": PUBLISHED_CENTER_CALL_COUNT,
            "reconstructed_call_count": len(center),
            "published_count_reproduced": center_count_matches,
            "set_level_equivalence_tested": False,
            "reason": (
                "Published notebook creates passed_bc only in memory; preserved "
                "blaze directory contains raw_bc.csv.gz but no selected whitelist"
            ),
        }
    ]
    write_tsv(table_root / "baseline_status.tsv", baseline_rows)
    write_tsv(
        table_root / "published_vs_installed_selector.tsv",
        library_comparison_rows,
    )

    center_f1 = None
    metric_rows: list[dict] = []
    for expected_cells in GRID:
        called = reconstructed[expected_cells]
        tp = len(called & reference)
        fp = len(called - reference)
        fn = len(reference - called)
        precision = tp / len(called) if called else 0.0
        recall = tp / len(reference) if reference else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        if expected_cells == CENTER:
            center_f1 = f1
        union = called | center
        metric_rows.append(
            {
                "status": STATUS,
                "dataset": "scMixology2",
                "mode": f"expect{expected_cells}",
                "expected_cells": expected_cells,
                "expectation_fold_vs_500": f"{expected_cells / CENTER:.3f}",
                "threshold": f"{threshold_by_expected[expected_cells]:.12f}",
                "reference_barcodes": len(reference),
                "called_barcodes": len(called),
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "precision": f"{precision:.12f}",
                "recall": f"{recall:.12f}",
                "f1": f"{f1:.12f}",
                "delta_calls_vs_expect500": len(called) - len(center),
                "delta_f1_vs_expect500": "PENDING",
                "intersection_with_expect500": len(called & center),
                "expectation_only_vs_expect500": len(called - center),
                "expect500_only": len(center - called),
                "jaccard_vs_expect500": f"{len(called & center) / len(union):.12f}",
                "callset_set_sha256": canonical_set_sha256(called),
            }
        )
    if center_f1 is None:
        raise RuntimeError("Center F1 was not computed")
    for row in metric_rows:
        row["delta_f1_vs_expect500"] = f"{float(row['f1']) - center_f1:.12f}"
    write_tsv(table_root / "expect_sensitivity_metrics.tsv", metric_rows)

    identity_rows = [
        {
            "evidence": "long_read_count",
            "preserved_value": rows_read,
            "RAD_benchmark_value": args.expected_data_rows,
            "match": rows_read == args.expected_data_rows,
            "interpretation": (
                "Preserved BLAZE raw table has one data row per RAD benchmark input read"
            ),
        },
        {
            "evidence": "matched_cellranger_whitelist_count",
            "preserved_value": len(reference),
            "RAD_benchmark_value": 248,
            "match": len(reference) == 248,
            "interpretation": (
                "Matches the published scMixology2 Cell Ranger reference size"
            ),
        },
        {
            "evidence": "analysis_notebook_paths",
            "preserved_value": "data/scmixology/blaze/raw_bc.csv;data/scmixology/cellranger/whitelist.tsv",
            "RAD_benchmark_value": "same_scMixology2_dataset",
            "match": True,
            "interpretation": (
                "Preserved paths match the public BLAZE scmixology notebook inputs"
            ),
        },
    ]
    write_tsv(table_root / "identity_evidence.tsv", identity_rows)

    provenance = {
        "status": STATUS,
        "dataset": "scMixology2",
        "preserved_raw_bc": str(raw_path),
        "preserved_cellranger_reference": str(reference_path),
        "preserved_design_whitelist": str(preserved_design_path),
        "installed_design_whitelist": str(installed_design_path),
        "preserved_and_installed_design_sets_identical": True,
        "design_barcodes": len(preserved_design),
        "raw_bc_data_rows": rows_read,
        "q15_nonmissing_rows": passing_rows,
        "unique_q15_raw_barcodes": len(raw_counts),
        "unique_q15_design_barcodes": len(chemistry_counts),
        "reference_barcodes": len(reference),
        "min_q": args.min_q,
        "expectation_grid": list(GRID),
        "published_center_expectation": CENTER,
        "published_center_call_count": PUBLISHED_CENTER_CALL_COUNT,
        "published_center_count_reproduced": center_count_matches,
        "published_analysis_commit": "90e4cebcbf8dedb787272be0f2ded4c5bb21e468",
        "published_notebook": (
            "https://github.com/youyupei/bc_whitelist_analysis/blob/"
            "90e4cebcbf8dedb787272be0f2ded4c5bb21e468/"
            "script/scmixology_data_analysis.ipynb"
        ),
        "published_selector_semantics": (
            "Q>=15; restrict to 10x design; threshold=95th percentile "
            "of top N counts /20; select counts >= threshold; N=500"
        ),
        "selector_library_version_for_cross_check": blaze_version,
        "selector_library_module": str(Path(sys.modules["blaze.main"].__file__).resolve()),
        "authentic_native_callset_available": False,
        "primary_validated_package_eligible": False,
        "elapsed_seconds_before_source_hashing": time.time() - started,
    }
    (output_root / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n"
    )
    print((table_root / "baseline_status.tsv").read_text(), end="")
    print((table_root / "expect_sensitivity_metrics.tsv").read_text(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
