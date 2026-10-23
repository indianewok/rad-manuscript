#!/usr/bin/env python3
"""Compare SN-ONT tool Vireo calls with published Illumina and merged labels.

The primary reference is the platform-specific Illumina-SN Vireo call for
each 10x barcode.  The LongBench majority-vote merged annotation is emitted as
a separate secondary comparison because it is not independent of ONT/PacBio.

Every tool must be supplied with both a Vireo donor_ids.tsv and the barcode
whitelist used for CellSNP.  This keeps `not_selected` distinct from
`selected_no_vireo_call`; neither is silently treated as `unassigned`.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil
import sys
from typing import Any, Iterable


DONORS = ("H146", "H1975", "H211", "H2228", "H526", "H69", "HCC827", "SHP77")
DONOR_SET = set(DONORS)
VALID_VIREO_LABELS = DONOR_SET | {"doublet", "unassigned"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--illumina-vireo", required=True,
                        help="Published Illumina-SN donor_ids.tsv")
    parser.add_argument("--merged-dir", required=True,
                        help="Directory with eight *_BC_list.txt files")
    parser.add_argument(
        "--tool", action="append", nargs=4, required=True,
        metavar=("NAME", "DONOR_IDS", "WHITELIST", "PROVENANCE"),
        help="Repeat once per tool; PROVENANCE is a concise model/input label",
    )
    parser.add_argument("--out-dir", required=True)
    return parser.parse_args()


def normalize_barcode(value: str) -> str:
    return re.sub(r"-1$", "", value.strip())


def valid_barcode(value: str) -> bool:
    return len(value) == 16 and set(value) <= set("ACGT")


def read_vireo(path: Path) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"cell", "donor_id"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path}: expected donor_ids.tsv with cell and donor_id")
        for row in reader:
            barcode = normalize_barcode(row["cell"])
            if not valid_barcode(barcode):
                raise ValueError(f"{path}: invalid barcode {row['cell']!r}")
            if barcode in result:
                raise ValueError(f"{path}: duplicate after -1 normalization: {barcode}")
            if row["donor_id"] not in VALID_VIREO_LABELS:
                raise ValueError(f"{path}: unexpected donor_id {row['donor_id']!r}")
            result[barcode] = row
    if not result:
        raise ValueError(f"{path}: no Vireo rows")
    return result


def read_whitelist(path: Path) -> set[str]:
    barcodes: set[str] = set()
    with path.open() as handle:
        for line_number, line in enumerate(handle, 1):
            text = line.strip()
            if not text:
                continue
            token = re.split(r"[\s,]+", text, maxsplit=1)[0]
            barcode = normalize_barcode(token)
            if not valid_barcode(barcode):
                raise ValueError(f"{path}:{line_number}: invalid barcode {token!r}")
            if barcode in barcodes:
                raise ValueError(f"{path}:{line_number}: duplicate barcode {barcode}")
            barcodes.add(barcode)
    if not barcodes:
        raise ValueError(f"{path}: empty whitelist")
    return barcodes


def read_merged(directory: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for donor in DONORS:
        path = directory / f"{donor}_BC_list.txt"
        if not path.is_file():
            raise ValueError(f"missing merged annotation file: {path}")
        with path.open() as handle:
            for line_number, line in enumerate(handle, 1):
                barcode = normalize_barcode(line)
                if not valid_barcode(barcode):
                    raise ValueError(f"{path}:{line_number}: invalid barcode")
                if barcode in result:
                    raise ValueError(
                        f"merged barcode {barcode} occurs in {result[barcode]} and {donor}"
                    )
                result[barcode] = donor
    if not result:
        raise ValueError(f"{directory}: empty merged annotation")
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def state(label: str) -> str:
    if label in DONOR_SET:
        return "singlet"
    if label in {"doublet", "unassigned", "not_selected", "selected_no_vireo_call"}:
        return label
    if label in {"not_in_illumina_reference", "not_in_merged_reference"}:
        return label
    raise ValueError(f"cannot classify label {label!r}")


def query_call(
    barcode: str,
    query: dict[str, dict[str, str]],
    selected: set[str],
) -> tuple[str, str, dict[str, str] | None]:
    row = query.get(barcode)
    is_selected = barcode in selected
    if row is not None and not is_selected:
        raise ValueError(f"Vireo emitted barcode outside supplied whitelist: {barcode}")
    if not is_selected:
        return "not_selected", "not_selected", None
    if row is None:
        return "selected_no_vireo_call", "selected_no_vireo_call", None
    label = row["donor_id"]
    return label, state(label), row


def outcome(reference_label: str, query_label: str, reference_kind: str) -> str:
    if reference_label.startswith("not_in_"):
        return reference_label
    if query_label in {"not_selected", "selected_no_vireo_call"}:
        return query_label
    if reference_label in DONOR_SET:
        if query_label == reference_label:
            return "same_donor"
        if query_label in DONOR_SET:
            return "different_donor"
        if query_label == "doublet":
            return "singlet_to_doublet"
        if query_label == "unassigned":
            return "singlet_to_unassigned"
    if reference_label == "doublet":
        if query_label == "doublet":
            return "retained_doublet"
        if query_label in DONOR_SET:
            return "doublet_to_singlet"
        if query_label == "unassigned":
            return "doublet_to_unassigned"
    if reference_label == "unassigned":
        if query_label == "unassigned":
            return "retained_unassigned"
        if query_label in DONOR_SET:
            return "unassigned_to_singlet"
        if query_label == "doublet":
            return "unassigned_to_doublet"
    raise ValueError(
        f"unsupported {reference_kind} transition {reference_label}->{query_label}"
    )


def numeric(row: dict[str, str] | None, key: str) -> str:
    if row is None:
        return ""
    return row.get(key, "")


def ratio(numerator: int, denominator: int) -> str:
    return f"{numerator / denominator:.8f}" if denominator else "NA"


def write_tsv(path: Path, header: Iterable[str], rows: Iterable[Iterable[Any]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(list(header))
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    illumina_path = Path(args.illumina_vireo).resolve()
    merged_dir = Path(args.merged_dir).resolve()
    target = Path(args.out_dir).resolve()
    if target.exists():
        raise ValueError(f"refusing existing output directory: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + f".partial.{os.getpid()}")
    if temporary.exists():
        raise ValueError(f"refusing existing temporary directory: {temporary}")
    temporary.mkdir()

    try:
        illumina = read_vireo(illumina_path)
        merged = read_merged(merged_dir)
        tools: dict[str, dict[str, Any]] = {}
        for name, query_text, whitelist_text, provenance in args.tool:
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
                raise ValueError(f"invalid tool name {name!r}")
            if name in tools:
                raise ValueError(f"duplicate tool name {name}")
            query_path = Path(query_text).resolve()
            whitelist_path = Path(whitelist_text).resolve()
            query = read_vireo(query_path)
            selected = read_whitelist(whitelist_path)
            outside = set(query) - selected
            if outside:
                raise ValueError(
                    f"{name}: {len(outside)} Vireo rows outside supplied whitelist"
                )
            tools[name] = {
                "query_path": query_path,
                "whitelist_path": whitelist_path,
                "provenance": provenance,
                "query": query,
                "selected": selected,
            }

        universe = set(illumina) | set(merged)
        for data in tools.values():
            universe.update(data["selected"])
            universe.update(data["query"])
        ordered_cells = sorted(universe)

        long_header = [
            "tool", "cell", "selected", "tool_label", "tool_state",
            "tool_prob_max", "tool_prob_doublet", "tool_n_vars",
            "illumina_label", "illumina_state", "illumina_prob_max",
            "illumina_prob_doublet", "illumina_n_vars", "outcome_vs_illumina",
            "merged_label", "outcome_vs_merged", "query_provenance",
        ]
        long_rows: list[list[Any]] = []
        wide_header = [
            "cell", "illumina_label", "illumina_state", "merged_label"
        ]
        for name in tools:
            wide_header.extend([
                f"{name}_selected", f"{name}_label", f"{name}_state",
                f"{name}_prob_max", f"{name}_prob_doublet", f"{name}_n_vars",
                f"{name}_outcome_vs_illumina", f"{name}_outcome_vs_merged",
            ])
        wide_rows: list[list[Any]] = []
        summary_rows: list[list[Any]] = []
        state_rows: list[list[Any]] = []
        donor_transition_rows: list[list[Any]] = []
        per_donor_rows: list[list[Any]] = []
        label_change_rows: list[list[Any]] = []
        doublet_change_rows: list[list[Any]] = []

        for cell in ordered_cells:
            illumina_row = illumina.get(cell)
            illumina_label = (
                illumina_row["donor_id"] if illumina_row
                else "not_in_illumina_reference"
            )
            illumina_state = state(illumina_label)
            merged_label = merged.get(cell, "not_in_merged_reference")
            wide = [cell, illumina_label, illumina_state, merged_label]
            for name, data in tools.items():
                query_label, query_state, query_row = query_call(
                    cell, data["query"], data["selected"]
                )
                illumina_outcome = outcome(illumina_label, query_label, "Illumina")
                merged_outcome = outcome(merged_label, query_label, "merged")
                long_rows.append([
                    name, cell, int(cell in data["selected"]), query_label,
                    query_state, numeric(query_row, "prob_max"),
                    numeric(query_row, "prob_doublet"), numeric(query_row, "n_vars"),
                    illumina_label, illumina_state,
                    numeric(illumina_row, "prob_max"),
                    numeric(illumina_row, "prob_doublet"),
                    numeric(illumina_row, "n_vars"), illumina_outcome,
                    merged_label, merged_outcome, data["provenance"],
                ])
                wide.extend([
                    int(cell in data["selected"]), query_label, query_state,
                    numeric(query_row, "prob_max"),
                    numeric(query_row, "prob_doublet"), numeric(query_row, "n_vars"),
                    illumina_outcome, merged_outcome,
                ])
            wide_rows.append(wide)

        write_tsv(temporary / "all_tools.per_cell_long.tsv", long_header, long_rows)
        write_tsv(temporary / "all_tools.per_cell_wide.tsv", wide_header, wide_rows)

        # All remaining summaries are computed from the same long table so the
        # cell-level artifact is the auditable source of every reported count.
        columns = {name: index for index, name in enumerate(long_header)}
        for name, data in tools.items():
            rows = [row for row in long_rows if row[columns["tool"]] == name]
            illumina_outcomes = Counter(row[columns["outcome_vs_illumina"]] for row in rows)
            merged_outcomes = Counter(row[columns["outcome_vs_merged"]] for row in rows)
            illumina_named_rows = [
                row for row in rows if row[columns["illumina_label"]] in DONOR_SET
            ]
            illumina_named_outcomes = Counter(
                row[columns["outcome_vs_illumina"]] for row in illumina_named_rows
            )
            merged_named_rows = [
                row for row in rows if row[columns["merged_label"]] in DONOR_SET
            ]
            selected_no_call = len(data["selected"] - set(data["query"]))
            same_ill = illumina_outcomes["same_donor"]
            diff_ill = illumina_outcomes["different_donor"]
            same_merged = merged_outcomes["same_donor"]
            diff_merged = merged_outcomes["different_donor"]
            summary_rows.append([
                name, data["provenance"], len(data["selected"]), len(data["query"]),
                selected_no_call, len(illumina),
                sum(1 for row in illumina.values() if row["donor_id"] in DONOR_SET),
                sum(1 for row in illumina.values() if row["donor_id"] == "doublet"),
                sum(1 for row in illumina.values() if row["donor_id"] == "unassigned"),
                sum(int(row[columns["selected"]]) for row in illumina_named_rows),
                same_ill, diff_ill, illumina_outcomes["singlet_to_doublet"],
                illumina_outcomes["singlet_to_unassigned"],
                illumina_named_outcomes["selected_no_vireo_call"],
                illumina_named_outcomes["not_selected"],
                illumina_outcomes["selected_no_vireo_call"],
                illumina_outcomes["not_selected"],
                ratio(sum(int(row[columns["selected"]]) for row in illumina_named_rows),
                      len(illumina_named_rows)),
                ratio(same_ill, len(illumina_named_rows)),
                ratio(same_ill, same_ill + diff_ill),
                len(merged), same_merged, diff_merged,
                merged_outcomes["singlet_to_doublet"],
                merged_outcomes["singlet_to_unassigned"],
                merged_outcomes["selected_no_vireo_call"],
                merged_outcomes["not_selected"],
                ratio(same_merged, len(merged_named_rows)),
                ratio(same_merged, same_merged + diff_merged),
                len(data["selected"] - set(illumina)),
            ])

            state_counts = Counter()
            donor_counts = Counter()
            per_donor: dict[str, Counter[str]] = defaultdict(Counter)
            for row in rows:
                ref_label = row[columns["illumina_label"]]
                ref_state = row[columns["illumina_state"]]
                query_label = row[columns["tool_label"]]
                query_state = row[columns["tool_state"]]
                if ref_label != "not_in_illumina_reference":
                    state_counts[(ref_state, query_state)] += 1
                if ref_label in DONOR_SET:
                    donor_counts[(ref_label, query_label)] += 1
                    per_donor[ref_label][row[columns["outcome_vs_illumina"]]] += 1
                    per_donor[ref_label]["selected"] += int(row[columns["selected"]])
                if ref_label in DONOR_SET and query_label in DONOR_SET and ref_label != query_label:
                    label_change_rows.append([
                        name, row[columns["cell"]], ref_label, query_label,
                        row[columns["illumina_prob_max"]], row[columns["tool_prob_max"]],
                        row[columns["illumina_n_vars"]], row[columns["tool_n_vars"]],
                    ])
                if {ref_state, query_state} == {"singlet", "doublet"}:
                    doublet_change_rows.append([
                        name, row[columns["cell"]], ref_label, query_label,
                        ref_state, query_state, row[columns["illumina_prob_max"]],
                        row[columns["tool_prob_max"]], row[columns["illumina_n_vars"]],
                        row[columns["tool_n_vars"]],
                    ])

            for (left, right), count in sorted(state_counts.items()):
                state_rows.append([name, left, right, count])
            for (left, right), count in sorted(donor_counts.items()):
                donor_transition_rows.append([name, left, right, count])
            for donor in DONORS:
                counts = per_donor[donor]
                total = sum(
                    counts[key] for key in (
                        "same_donor", "different_donor", "singlet_to_doublet",
                        "singlet_to_unassigned", "selected_no_vireo_call", "not_selected",
                    )
                )
                per_donor_rows.append([
                    name, donor, total, counts["selected"],
                    counts["same_donor"], counts["different_donor"],
                    counts["singlet_to_doublet"], counts["singlet_to_unassigned"],
                    counts["selected_no_vireo_call"], counts["not_selected"],
                    ratio(counts["selected"], total),
                    ratio(counts["same_donor"], total),
                    ratio(counts["same_donor"],
                          counts["same_donor"] + counts["different_donor"]),
                ])

        summary_header = [
            "tool", "query_provenance", "selected_barcodes", "vireo_rows",
            "selected_without_vireo_row", "illumina_reference_cells",
            "illumina_named_singlets", "illumina_doublets", "illumina_unassigned",
            "illumina_named_selected", "illumina_same_donor", "illumina_different_donor",
            "illumina_singlet_to_doublet", "illumina_singlet_to_unassigned",
            "illumina_named_selected_no_vireo_call", "illumina_named_not_selected",
            "illumina_all_selected_no_vireo_call", "illumina_all_not_selected",
            "illumina_named_selection_recall", "illumina_strict_identity_recall",
            "illumina_agreement_among_both_singlets", "merged_named_cells",
            "merged_same_donor", "merged_different_donor", "merged_singlet_to_doublet",
            "merged_singlet_to_unassigned", "merged_selected_no_vireo_call",
            "merged_not_selected", "merged_strict_identity_recall",
            "merged_agreement_among_both_singlets", "selected_not_in_illumina_reference",
        ]
        write_tsv(temporary / "all_tools.summary.tsv", summary_header, summary_rows)
        write_tsv(
            temporary / "all_tools.illumina_state_transitions.tsv",
            ["tool", "illumina_state", "tool_state", "cells"], state_rows,
        )
        write_tsv(
            temporary / "all_tools.illumina_donor_transitions.tsv",
            ["tool", "illumina_donor", "tool_label", "cells"], donor_transition_rows,
        )
        write_tsv(
            temporary / "all_tools.per_donor_illumina.tsv",
            [
                "tool", "illumina_donor", "reference_cells", "selected",
                "same_donor", "different_donor", "to_doublet", "to_unassigned",
                "selected_no_vireo_call", "not_selected", "selection_recall",
                "strict_identity_recall", "agreement_among_both_singlets",
            ], per_donor_rows,
        )
        write_tsv(
            temporary / "all_tools.cross_line_label_changes.tsv",
            [
                "tool", "cell", "illumina_donor", "tool_donor",
                "illumina_prob_max", "tool_prob_max", "illumina_n_vars", "tool_n_vars",
            ], label_change_rows,
        )
        write_tsv(
            temporary / "all_tools.singlet_doublet_transitions.tsv",
            [
                "tool", "cell", "illumina_label", "tool_label", "illumina_state",
                "tool_state", "illumina_prob_max", "tool_prob_max",
                "illumina_n_vars", "tool_n_vars",
            ], doublet_change_rows,
        )

        manifest_rows = []
        manifest_inputs = [("illumina_vireo", illumina_path)]
        for donor in DONORS:
            manifest_inputs.append((f"merged_{donor}", merged_dir / f"{donor}_BC_list.txt"))
        for name, data in tools.items():
            manifest_inputs.extend([
                (f"{name}_vireo", data["query_path"]),
                (f"{name}_whitelist", data["whitelist_path"]),
            ])
        for role, path in manifest_inputs:
            manifest_rows.append([role, str(path), path.stat().st_size, sha256(path)])
        write_tsv(
            temporary / "input_manifest.tsv",
            ["role", "path", "bytes", "sha256"], manifest_rows,
        )
        metadata = {
            "completed_utc": datetime.now(timezone.utc).isoformat(),
            "primary_reference": "published Illumina-SN Vireo labels",
            "secondary_reference": "published majority-vote merged SN named labels",
            "interpretation": {
                "not_selected": "barcode absent from the tool CellSNP whitelist",
                "selected_no_vireo_call": "barcode selected but absent from donor_ids.tsv",
                "different_donor": "both calls are named singlets but donor names differ",
                "merged_caveat": "merged labels include long-read votes and are not independent",
            },
            "donor_order": list(DONORS),
            "tools": {
                name: {
                    "query_vireo": str(data["query_path"]),
                    "whitelist": str(data["whitelist_path"]),
                    "query_provenance": data["provenance"],
                }
                for name, data in tools.items()
            },
        }
        (temporary / "analysis_metadata.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n"
        )
        os.replace(temporary, target)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise

    print(f"comparison_complete\t{target}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, csv.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
