#!/usr/bin/env python3
"""Aggregate the ScTagger-L false-whitelist native runs.

The presentation CSV intentionally contains exactly nine numeric columns.  Its
row number (1..5000) is the within-replicate sorted whitelist row index; the
barcode identities are retained only in the identity-bearing audit table.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
import shutil
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple


BARCODE_RE = re.compile(r"^[ACGT]{16}$")
TOOLS = ("rad", "blaze", "flexiplex")
REPS = (1, 2, 3)
INPUT_READS = 4_993_805
TARGET_N = 5_000


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_targets(path: Path) -> List[str]:
    rows = [line.strip() for line in path.open() if line.strip()]
    if len(rows) != TARGET_N or len(set(rows)) != TARGET_N:
        raise RuntimeError(f"{path}: expected {TARGET_N} unique rows, got {len(rows)}")
    bad = [x for x in rows if not BARCODE_RE.fullmatch(x)]
    if bad:
        raise RuntimeError(f"{path}: invalid barcode(s), first={bad[0]}")
    if rows != sorted(rows):
        raise RuntimeError(f"{path}: whitelist is not deterministically sorted")
    return rows


def iter_fastq_headers(path: Path) -> Iterator[str]:
    with gzip.open(path, "rt", newline="") as fh:
        n = 0
        while True:
            header = fh.readline()
            if not header:
                break
            seq = fh.readline()
            plus = fh.readline()
            qual = fh.readline()
            n += 1
            if not (seq and plus and qual):
                raise RuntimeError(f"truncated FASTQ at record {n}: {path}")
            if not header.startswith("@") or not plus.startswith("+"):
                raise RuntimeError(f"invalid FASTQ record {n}: {path}")
            yield header.rstrip("\r\n")


def tag_fields(header: str) -> Tuple[str, Dict[str, str]]:
    fields = header[1:].split()
    if not fields:
        return "", {}
    tags: Dict[str, str] = {}
    for token in fields[1:]:
        if len(token) >= 5 and token[2:5] == ":Z:":
            tags[token[:2]] = token[5:]
    return fields[0], tags


def raw_read_id(core: str, tool: str) -> str:
    """Recover the original read ID for duplicate/input-coverage checks."""
    if tool == "blaze" and "#" in core:
        # BLAZE emits <assigned_bc>_<umi>#<original_read_id>_<orientation>.
        return re.sub(r"_[+-]$", "", core.split("#", 1)[1])
    # RAD IDs are e.g. <original_read_id>-F or -R.  Preserve the full ID when
    # no suffix is present; source truth is the first 16 bases below.
    return re.sub(r"-[FR](?:-CT)?$", "", core)


def percentile(values: Sequence[int], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    pos = (len(ordered) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return ordered[lo] + frac * (ordered[hi] - ordered[lo])


def fastq_assignment(path: Path, targets: Sequence[str], tool: str):
    target_set = set(targets)
    entries: List[Tuple[str, str, str, str]] = []
    outside = 0
    missing_cb = 0
    records = 0
    for header in iter_fastq_headers(path):
        records += 1
        core, tags = tag_fields(header)
        cb = tags.get("CB", "")
        raw = tags.get("CR", "")
        rid = raw_read_id(core, tool)
        if not cb:
            missing_cb += 1
            continue
        if cb not in target_set:
            outside += 1
            continue
        # BLAZE's putative barcode is joined below from putative_bc.csv.
        # Counts are deliberately delayed until duplicate physical read IDs
        # have been identified.  A multi-record ID is ambiguous and every
        # record for that ID is excluded from strict counts.
        entries.append((rid, cb, raw, core))
    return {
        "entries": entries,
        "records": records,
        "outside": outside,
        "missing_cb": missing_cb,
    }


def join_blaze_putative(result: dict, putative_path: Path) -> None:
    entries: List[Tuple[str, str, str, str]] = result["entries"]
    wanted = {x[0] for x in entries}
    putative: Dict[str, str] = {}
    if putative_path.exists() and wanted:
        with putative_path.open("r", newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            if header is None or not header or header[0] != "read_id":
                raise RuntimeError(f"unexpected BLAZE putative header: {putative_path}")
            for row in reader:
                if not row:
                    continue
                rid = row[0]
                if rid in wanted:
                    putative[rid] = row[1].strip() if len(row) > 1 else ""
    result["entries"] = [
        (rid, cb, putative.get(rid, ""), core)
        for rid, cb, _raw, core in entries
    ]
    result["putative_rows_joined"] = len(putative)
    result["putative_rows_needed"] = len(wanted)


def flex_assignment(sidecar: Path, targets: Sequence[str]):
    target_set = set(targets)
    rows: List[Tuple[str, str, str, str]] = []
    outside = 0
    missing_cb = 0
    with sidecar.open("r", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        expected = {"Read", "CellBarcode", "RawCellBarcode"}
        if not expected.issubset(set(reader.fieldnames or [])):
            raise RuntimeError(f"unexpected Flexiplex sidecar header: {sidecar}")
        for row in reader:
            rid = (row.get("Read") or "").strip()
            cb = (row.get("CellBarcode") or "").strip()
            raw = (row.get("RawCellBarcode") or "").strip()
            if not cb:
                missing_cb += 1
                continue
            if cb not in target_set:
                outside += 1
                continue
            rows.append((rid, cb, raw, rid))
    return {
        "entries": rows,
        "records": len(rows) + outside + missing_cb,
        "outside": outside,
        "missing_cb": missing_cb,
    }


def add_ambiguity(result: dict, targets: Sequence[str], tool: str) -> None:
    """Build strict physical-read counts after excluding every duplicate ID."""
    ids = Counter(row[0] for row in result["entries"])
    counts = Counter({x: 0 for x in targets})
    native = Counter({x: 0 for x in targets})
    corrected = Counter({x: 0 for x in targets})
    raw_unavailable = Counter({x: 0 for x in targets})
    truth_matches = Counter({x: 0 for x in targets})
    ambig = Counter({x: 0 for x in targets})
    ambiguous_records = 0
    for rid, cb, raw, _core in result["entries"]:
        if ids[rid] > 1:
            ambig[cb] += 1
            ambiguous_records += 1
            continue
        counts[cb] += 1
        if rid[:16] == cb:
            truth_matches[cb] += 1
        if tool == "rad":
            # RAD only writes CR when it changed the initially extracted
            # barcode.  An empty CR therefore denotes a native assignment.
            if raw:
                corrected[cb] += 1
            else:
                native[cb] += 1
        else:
            if raw and raw == cb:
                native[cb] += 1
            else:
                corrected[cb] += 1
                if not raw:
                    raw_unavailable[cb] += 1
    result["counts"] = counts
    result["native"] = native
    result["corrected"] = corrected
    result["raw_unavailable"] = raw_unavailable
    result["truth_matches"] = truth_matches
    result["ambiguity"] = ambig
    result["unique_read_ids"] = len(ids)
    result["ambiguous_records"] = ambiguous_records
    result["duplicate_read_ids"] = sum(1 for n in ids.values() if n > 1)


def write_tsv(path: Path, header: Sequence[str], rows: Iterable[Sequence[object]]) -> None:
    with path.open("w", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root: Path = args.root.resolve()
    wl_dir = root / "whitelists"
    runs = root / "runs"
    results_dir = root / "results"
    summaries_dir = root / "summaries"
    validation_dir = root / "validation"
    scripts_dir = root / "scripts"
    results_dir.mkdir(parents=True, exist_ok=True)
    summaries_dir.mkdir(parents=True, exist_ok=True)
    validation_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir.mkdir(parents=True, exist_ok=True)

    all_results = {}
    audit_rows: List[List[object]] = []
    summary_rows: List[List[object]] = []
    dist_rows: List[List[object]] = []

    for tool in TOOLS:
        for rep in REPS:
            targets = load_targets(wl_dir / f"false_rep{rep}.txt")
            if tool == "rad":
                d = runs / "rad" / f"rep{rep}"
                fq = d / f"L_flatQ20_false_rep{rep}_rad.fq.gz"
                if not fq.exists():
                    raise RuntimeError(f"missing RAD assigned FASTQ: {fq}")
                result = fastq_assignment(fq, targets, "rad")
            elif tool == "blaze":
                d = runs / "blaze" / f"rep{rep}"
                fq = d / "matched_reads.fastq.gz"
                if not fq.exists():
                    raise RuntimeError(f"missing BLAZE assigned FASTQ: {fq}")
                result = fastq_assignment(fq, targets, "blaze")
                join_blaze_putative(result, d / "putative_bc.csv")
            else:
                d = runs / "flexiplex" / f"rep{rep}"
                sidecar = d / f"flexiplex_L_flatQ20_false_rep{rep}_audit_reads_barcodes.txt"
                if not sidecar.exists():
                    raise RuntimeError(f"missing Flexiplex audit sidecar: {sidecar}")
                result = flex_assignment(sidecar, targets)
            add_ambiguity(result, targets, tool)
            result["targets"] = targets
            result["tool"] = tool
            result["rep"] = rep
            all_results[(tool, rep)] = result

            counts = result["counts"]
            vals = [counts[x] for x in targets]
            assigned = sum(vals)
            nonzero = sum(v > 0 for v in vals)
            summary_rows.append([
                tool, rep, TARGET_N, assigned, result["records"], result["unique_read_ids"],
                INPUT_READS, INPUT_READS - result["unique_read_ids"],
                f"{result['unique_read_ids'] / INPUT_READS:.12f}", nonzero,
                min(vals), f"{percentile(vals, .50):.6f}", f"{percentile(vals, .95):.6f}",
                f"{percentile(vals, .99):.6f}", max(vals), result["outside"],
                result["missing_cb"], sum(result["native"].values()), sum(result["corrected"].values()),
                sum(result["raw_unavailable"].values()), result["ambiguous_records"],
                result["duplicate_read_ids"], sum(result["truth_matches"].values()),
                result.get("putative_rows_joined", ""), result.get("putative_rows_needed", ""),
            ])
            dist_rows.extend([
                [tool, rep, "assigned_records", assigned],
                [tool, rep, "nonzero_targets", nonzero],
                [tool, rep, "zero_targets", TARGET_N - nonzero],
                [tool, rep, "min_assigned_per_target", min(vals)],
                [tool, rep, "median_assigned_per_target", f"{percentile(vals, .50):.6f}"],
                [tool, rep, "p95_assigned_per_target", f"{percentile(vals, .95):.6f}"],
                [tool, rep, "p99_assigned_per_target", f"{percentile(vals, .99):.6f}"],
                [tool, rep, "max_assigned_per_target", max(vals)],
                [tool, rep, "native_records", sum(result["native"].values())],
                [tool, rep, "corrected_records", sum(result["corrected"].values())],
                [tool, rep, "raw_unavailable_records", sum(result["raw_unavailable"].values())],
                [tool, rep, "ambiguous_records", result["ambiguous_records"]],
                [tool, rep, "duplicate_read_ids", result["duplicate_read_ids"]],
                [tool, rep, "source_truth_matches", sum(result["truth_matches"].values())],
                [tool, rep, "unique_input_read_ids", result["unique_read_ids"]],
                [tool, rep, "input_reads", INPUT_READS],
                [tool, rep, "input_coverage_fraction", f"{result['unique_read_ids'] / INPUT_READS:.12f}"],
            ])
            for i, barcode in enumerate(targets, 1):
                audit_rows.append([
                    tool, rep, i, barcode, counts[barcode], result["native"][barcode],
                    result["corrected"][barcode], result["raw_unavailable"][barcode],
                    result["ambiguity"][barcode], result["truth_matches"][barcode],
                ])

    # Identity-bearing audit table.  This is deliberately separate from the
    # requested presentation CSV, which omits barcode identity entirely.
    write_tsv(
        results_dir / "false_target_assigned_reads_long.tsv",
        ["tool", "replicate", "whitelist_row_index", "barcode", "assigned_reads",
         "native_reads", "corrected_reads", "raw_unavailable_reads", "ambiguous_reads",
         "source_truth_matches"],
        audit_rows,
    )

    # Exactly nine columns, all numeric data.  The 1-based row number is
    # implicit and documented in wide_csv_schema.txt.
    columns = [f"{tool}_rep{rep}" for tool in TOOLS for rep in REPS]
    with (results_dir / "false_target_assigned_reads_wide.csv").open("w", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(columns)
        for i in range(TARGET_N):
            writer.writerow([
                all_results[(tool, rep)]["counts"][all_results[(tool, rep)]["targets"][i]]
                for tool in TOOLS for rep in REPS
            ])
    identity_rows = []
    for rep in REPS:
        targets = all_results[("rad", rep)]["targets"]
        for i, barcode in enumerate(targets, 1):
            identity_rows.append([
                rep, i, barcode,
                all_results[("rad", rep)]["counts"][barcode],
                all_results[("blaze", rep)]["counts"][barcode],
                all_results[("flexiplex", rep)]["counts"][barcode],
            ])
    write_tsv(
        results_dir / "false_target_identity_and_counts.tsv",
        ["replicate", "whitelist_row_index", "barcode", "rad_assigned_reads",
         "blaze_assigned_reads", "flexiplex_assigned_reads"],
        identity_rows,
    )
    (results_dir / "wide_csv_schema.txt").write_text(
        "false_target_assigned_reads_wide.csv has exactly nine numeric columns and no barcode column.\n"
        "The data row number (1..5000, excluding header) is the within-replicate sorted whitelist row index.\n"
        "Column order: rad_rep1, rad_rep2, rad_rep3, blaze_rep1, blaze_rep2, blaze_rep3,\n"
        "flexiplex_rep1, flexiplex_rep2, flexiplex_rep3. Row i pairs only sampling position i\n"
        "within each replicate; it does not assert cross-replicate barcode identity.\n"
    )
    write_tsv(
        summaries_dir / "per_run_summary.tsv",
        ["tool", "replicate", "target_count", "assigned_records", "output_records", "unique_read_ids",
         "input_reads", "unassigned_by_unique_id", "input_coverage_fraction", "nonzero_targets",
         "min_target_reads", "median_target_reads", "p95_target_reads", "p99_target_reads",
         "max_target_reads", "outside_target_records", "missing_cb_records", "native_records",
         "corrected_records", "raw_unavailable_records", "ambiguous_records", "duplicate_read_ids",
         "source_truth_matches", "putative_rows_joined", "putative_rows_needed"],
        summary_rows,
    )
    write_tsv(summaries_dir / "per_cell_distribution.tsv", ["tool", "replicate", "metric", "value"], dist_rows)

    # Compact machine-readable run inventory links every scored arm to its
    # durable assigned artifact and supplied whitelist.  Run-level commands,
    # versions, hashes, time/RSS, logs and exit markers remain in runs/.
    inventory_rows = []
    for tool in TOOLS:
        for rep in REPS:
            if tool == "rad":
                d = runs / "rad" / f"rep{rep}"
                assigned = d / f"L_flatQ20_false_rep{rep}_rad.fq.gz"
                marker = d / "RAD_EXIT0"
            elif tool == "blaze":
                d = runs / "blaze" / f"rep{rep}"
                assigned = d / "matched_reads.fastq.gz"
                marker = d / "BLAZE_EXIT0"
            else:
                d = runs / "flexiplex" / f"rep{rep}"
                assigned = d / f"flexiplex_L_flatQ20_false_rep{rep}_audit_reads_barcodes.txt"
                marker = d / "FLEXIPLEX_AUDIT_EXIT0"
            wl = wl_dir / f"false_rep{rep}.txt"
            inventory_rows.append([
                tool, rep, str(wl), sha256(wl), str(assigned), assigned.stat().st_size,
                sha256(assigned), str(d / "run_metadata.tsv"), str(d / "time.verbose.txt" if tool == "rad" else d / ("blaze.time.txt" if tool == "blaze" else "flexiplex.time.txt")),
                str(marker), marker.exists(),
            ])
    write_tsv(
        results_dir / "run_inventory.tsv",
        ["tool", "replicate", "whitelist", "whitelist_sha256", "assigned_artifact", "assigned_bytes",
         "assigned_sha256", "run_metadata", "time_rss_file", "exit_marker", "exit_marker_present"],
        inventory_rows,
    )

    # Builder validation.  An independent validator is run separately before
    # the package receives its final COMPLETE marker.
    checks: List[List[object]] = []

    def check(name: str, observed: object, expected: object, ok: bool) -> None:
        checks.append([name, observed, expected, "PASS" if ok else "FAIL"])

    truth = set(load_targets(root / "provenance" / "truth_shortread_matched_5000_barcodes.txt"))
    for rep in REPS:
        wl = all_results[("rad", rep)]["targets"]
        check(f"rep{rep}_truth_overlap", len(set(wl) & truth), 0, not (set(wl) & truth))
        for tool in TOOLS:
            r = all_results[(tool, rep)]
            strict = sum(r["counts"].values())
            ambiguous_ids = r["duplicate_read_ids"]
            unassigned = INPUT_READS - r["unique_read_ids"]
            check(f"{tool}_rep{rep}_outside_whitelist", r["outside"], 0, r["outside"] == 0)
            check(f"{tool}_rep{rep}_missing_cb", r["missing_cb"], 0, r["missing_cb"] == 0)
            check(
                f"{tool}_rep{rep}_strict_category_closure",
                sum(r["native"].values()) + sum(r["corrected"].values()),
                strict,
                sum(r["native"].values()) + sum(r["corrected"].values()) == strict,
            )
            check(
                f"{tool}_rep{rep}_output_record_closure",
                strict + r["ambiguous_records"], r["records"],
                strict + r["ambiguous_records"] == r["records"],
            )
            check(
                f"{tool}_rep{rep}_input_partition",
                strict + ambiguous_ids + unassigned, INPUT_READS,
                strict + ambiguous_ids + unassigned == INPUT_READS,
            )
            check(
                f"{tool}_rep{rep}_false_target_truth_matches",
                sum(r["truth_matches"].values()), 0,
                sum(r["truth_matches"].values()) == 0,
            )
            if tool == "blaze":
                check(
                    f"blaze_rep{rep}_putative_join",
                    r.get("putative_rows_joined", -1), r.get("putative_rows_needed", -2),
                    r.get("putative_rows_joined") == r.get("putative_rows_needed"),
                )
    wide = results_dir / "false_target_assigned_reads_wide.csv"
    with wide.open(newline="") as fh:
        wide_rows = list(csv.reader(fh))
    check("wide_numeric_columns", len(wide_rows[0]), 9, len(wide_rows[0]) == 9)
    check("wide_data_rows", len(wide_rows) - 1, TARGET_N, len(wide_rows) - 1 == TARGET_N)
    numeric_ok = all(len(row) == 9 and all(cell.isdigit() for cell in row) for row in wide_rows[1:])
    check("wide_all_numeric_fixed_width", numeric_ok, True, numeric_ok)
    check("identity_rows", len(identity_rows), TARGET_N * 3, len(identity_rows) == TARGET_N * 3)
    marker_ok = all(
        ((runs / tool / f"rep{rep}" / ("RAD_EXIT0" if tool == "rad" else
          "BLAZE_EXIT0" if tool == "blaze" else "FLEXIPLEX_AUDIT_EXIT0")).exists())
        for tool in TOOLS for rep in REPS
    )
    check("all_9_exit0_markers", marker_ok, True, marker_ok)
    write_tsv(validation_dir / "BUILDER_VALIDATION.tsv", ["check", "observed", "expected", "status"], checks)
    failures = [row[0] for row in checks if row[3] != "PASS"]
    (validation_dir / "BUILDER_VALIDATION.json").write_text(json.dumps({
        "checks": len(checks), "passed": len(checks) - len(failures),
        "failed": len(failures), "failed_checks": failures,
    }, indent=2, sort_keys=True) + "\n")

    shutil.copy2(Path(__file__).resolve(), scripts_dir / Path(__file__).name)
    (root / "DATA_DICTIONARY.md").write_text(
        "# ScTagger-L false-whitelist count tables\n\n"
        "`results/false_target_assigned_reads_wide.csv` has exactly 5,000 data rows and "
        "nine integer columns. It intentionally has no identity column. Row position is the "
        "sorted whitelist rank within that replicate. Pair tools within one replicate by row; "
        "do not interpret the same row across different replicates as the same barcode.\n\n"
        "`results/false_target_identity_and_counts.tsv` preserves replicate, rank, barcode, and "
        "the three tool counts. `false_target_assigned_reads_long.tsv` additionally separates "
        "native/corrected and reports records excluded for physical-read ambiguity.\n"
    )
    (root / "README.md").write_text(
        "# ScTagger-L random false-whitelist experiment (2026-08-13)\n\n"
        "All nine arms use the same 4,993,805-read flat-Q20 ScTagger-L FASTQ. For each of "
        "three fixed RNG seeds, 5,000 unique 10x 3' v3 catalogue barcodes were sampled after "
        "excluding all 5,000 synthetic truth barcodes. RAD, BLAZE and the pinned Flexiplex "
        "audit build were each forced to use that exact replicate list.\n\n"
        "Counts use strict physical-read semantics: one emitted assignment gives one count; "
        "if a physical read ID has more than one emitted record, the entire ID is classified "
        "as ambiguous and excluded from all per-cell counts. Zero-count targets are retained. "
        "A 'false' barcode here means absent from the known synthetic truth list, not a general "
        "claim about every possible biological library.\n\n"
        "The requested presentation file is `results/false_target_assigned_reads_wide.csv`. "
        "Use the identity-bearing companion for audits. Commands, versions, logs, wall time, "
        "maximum RSS, supplied lists and exit markers remain under `runs/`.\n"
    )
    if failures:
        raise RuntimeError("builder validation failed: " + ", ".join(failures))
    (validation_dir / "BUILDER_COMPLETE").write_text(
        f"PASS\t{len(checks)}/{len(checks)}\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
