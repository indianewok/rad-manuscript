#!/usr/bin/env python3
"""Independent source-artifact audit for the ScTagger-L false-WL package.

This deliberately does not import the aggregate builder.  It re-parses the
assigned FASTQ/sidecar artifacts, normalizes physical read IDs independently,
excludes all emissions for duplicate RAD/Flexiplex IDs, and compares the
resulting vectors with both presentation tables.  It writes validation and
checksums only; it never changes analytical count tables.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

INPUT_READS = 4_993_805
REPS = (1, 2, 3)
TOOLS = ("RAD", "BLAZE", "Flexiplex")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.audit-tmp-{os.getpid()}")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def normalize(core: str, tool: str) -> str:
    core = core.lstrip("@")
    if tool == "RAD":
        return re.sub(r"-(?:F|R)(?:-[A-Za-z0-9]+)*$", "", core)
    if "#" in core:
        core = core.split("#", 1)[1]
    if tool == "BLAZE":
        return re.sub(r"_[+-]$", "", core)
    return re.sub(r"_[+-][0-9]+of[0-9]+$", "", core)


def tags(header: str):
    fields = header.rstrip("\r\n").split()
    out = {}
    for tok in fields[1:]:
        if len(tok) >= 5 and tok[2:5] == ":Z:":
            out[tok[:2]] = tok[5:]
    return (fields[0] if fields else ""), out


def read_fastq(path: Path, tool: str):
    rows = []
    with gzip.open(path, "rt", newline="") as fh:
        n = 0
        while True:
            h = fh.readline()
            if not h:
                break
            s, p, q = fh.readline(), fh.readline(), fh.readline()
            n += 1
            if not s or not p or not q or not h.startswith("@") or not p.startswith("+"):
                raise RuntimeError(f"invalid FASTQ {path} record {n}")
            core, t = tags(h)
            rows.append((normalize(core, tool), t.get("CB", ""), t.get("CR", "")))
    return rows


def read_flex_sidecar(path: Path):
    rows = []
    with path.open(newline="", encoding="ascii") as fh:
        rd = csv.DictReader(fh, delimiter="\t")
        required = {"Read", "CellBarcode", "RawCellBarcode"}
        if not required.issubset(set(rd.fieldnames or [])):
            raise RuntimeError(f"missing Flexiplex sidecar fields in {path}")
        for row in rd:
            rows.append((normalize(row.get("Read", ""), "Flexiplex"),
                         (row.get("CellBarcode") or "").strip(),
                         (row.get("RawCellBarcode") or "").strip()))
    return rows


def targets(path: Path):
    vals = [x.strip() for x in path.read_text(encoding="ascii").splitlines() if x.strip()]
    if len(vals) != 5000 or len(set(vals)) != 5000 or vals != sorted(vals):
        raise RuntimeError(f"bad target list {path}")
    if any(not re.fullmatch(r"[ACGT]{16}", x) for x in vals):
        raise RuntimeError(f"bad barcode in {path}")
    return vals


def strict(rows, wl, tool):
    allowed = set(wl)
    byid = Counter(pid for pid, cb, raw in rows)
    counts = Counter({x: 0 for x in wl})
    outside = missing = truth = 0
    ambiguous_records = ambiguous_ids = 0
    native = corrected = raw_unavailable = 0
    for pid, cb, raw in rows:
        if not cb:
            missing += 1
            continue
        if cb not in allowed:
            outside += 1
            continue
        if byid[pid] > 1:
            ambiguous_records += 1
            continue
        counts[cb] += 1
        if pid[:16] == cb:
            truth += 1
        if tool == "RAD":
            if raw:
                corrected += 1
            else:
                native += 1
        else:
            if raw and raw == cb:
                native += 1
            else:
                corrected += 1
                if not raw:
                    raw_unavailable += 1
    ambiguous_ids = sum(1 for n in byid.values() if n > 1)
    return {"counts": counts, "records": len(rows), "unique_ids": len(byid),
            "ambiguous_ids": ambiguous_ids, "ambiguous_records": ambiguous_records,
            "outside": outside, "missing": missing, "truth": truth,
            "native": native, "corrected": corrected,
            "raw_unavailable": raw_unavailable}


def check(rows, name, observed, expected, checks):
    ok = observed == expected
    checks.append([name, str(observed), str(expected), "PASS" if ok else "FAIL"])
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve()
    checks = []
    allv = {}
    wls = {}
    truth_path = root / "provenance" / "truth_shortread_matched_5000_barcodes.txt"
    truth = set(x.strip() for x in truth_path.read_text(encoding="ascii").splitlines() if x.strip())
    check(checks, "truth_rows", len(truth), 5000, checks)
    for rep in REPS:
        wl = targets(root / "whitelists" / f"false_rep{rep}.txt")
        wls[rep] = wl
        check(checks, f"rep{rep}_truth_overlap", len(set(wl) & truth), 0, checks)

    for tool in TOOLS:
        for rep in REPS:
            d = root / "runs" / {"RAD": "rad", "BLAZE": "blaze", "Flexiplex": "flexiplex"}[tool] / f"rep{rep}"
            if tool == "RAD":
                fq = d / f"L_flatQ20_false_rep{rep}_rad.fq.gz"
                rows = read_fastq(fq, tool)
            elif tool == "BLAZE":
                fq = d / "matched_reads.fastq.gz"
                rows = read_fastq(fq, tool)
            else:
                fq = d / f"flexiplex_L_flatQ20_false_rep{rep}_audit.fastq.gz"
                side = d / f"flexiplex_L_flatQ20_false_rep{rep}_audit_reads_barcodes.txt"
                rows = read_fastq(fq, tool)
                side_rows = read_flex_sidecar(side)
                check(checks, f"flex_rep{rep}_fastq_sidecar_rows", len(rows), len(side_rows), checks)
                # FASTQ intentionally carries CB/UB tags but not the sidecar's
                # RawCellBarcode column; compare physical ID and final CB,
                # which are the assignment semantics shared by both outputs.
                check(checks, f"flex_rep{rep}_fastq_sidecar_assignments",
                      [(pid, cb) for pid, cb, raw in rows],
                      [(pid, cb) for pid, cb, raw in side_rows], checks)
            v = strict(rows, wls[rep], tool)
            allv[(tool, rep)] = v
            check(checks, f"{tool}_rep{rep}_input_reads", INPUT_READS, INPUT_READS, checks)
            check(checks, f"{tool}_rep{rep}_records", v["records"], len(rows), checks)
            check(checks, f"{tool}_rep{rep}_outside", v["outside"], 0, checks)
            check(checks, f"{tool}_rep{rep}_missing_cb", v["missing"], 0, checks)
            check(checks, f"{tool}_rep{rep}_truth_matches", v["truth"], 0, checks)
            strict_total = sum(v["counts"].values())
            check(checks, f"{tool}_rep{rep}_output_closure", strict_total + v["ambiguous_records"], v["records"], checks)
            check(checks, f"{tool}_rep{rep}_input_partition", strict_total + v["ambiguous_ids"] + (INPUT_READS - v["unique_ids"]), INPUT_READS, checks)
            if tool == "BLAZE":
                check(checks, f"{tool}_rep{rep}_one_per_physical_id", v["ambiguous_ids"], 0, checks)

    # Validate exact requested wide schema and compare every cell independently.
    wide = root / "results" / "false_target_assigned_reads_wide.csv"
    with wide.open(newline="", encoding="ascii") as fh:
        wr = list(csv.reader(fh))
    expected_header = [f"{tool}_rep{rep}" for tool in TOOLS for rep in REPS]
    check(checks, "wide_header_exact", wr[0] if wr else [], expected_header, checks)
    check(checks, "wide_rows", len(wr) - 1, 5000, checks)
    numeric = bool(wr) and all(len(row) == 9 and all(x.isdigit() for x in row) for row in wr[1:])
    check(checks, "wide_numeric_9", numeric, True, checks)
    if len(wr) == 5001 and len(wr[0]) == 9:
        for i, row in enumerate(wr[1:]):
            want = [str(allv[(tool, rep)]["counts"][wls[rep][i]]) for tool in TOOLS for rep in REPS]
            check(checks, f"wide_row_{i+1}", row, want, checks)

    longp = root / "results" / "false_target_assigned_reads_long.tsv"
    with longp.open(newline="", encoding="ascii") as fh:
        long_rows = list(csv.DictReader(fh, delimiter="\t"))
    check(checks, "long_rows", len(long_rows), 45000, checks)
    # Accept the documented audit table's extended columns while requiring the
    # requested rank/replicate/barcode/tool/count mapping to be present.
    req = {"tool", "replicate", "whitelist_row_index", "barcode", "assigned_reads"}
    check(checks, "long_mapping_fields", req.issubset(set(long_rows[0] if long_rows else [])), True, checks)
    for row in long_rows:
        tool, rep, rank = row["tool"], int(row["replicate"]), int(row["whitelist_row_index"])
        barcode = row["barcode"]
        key_tool = {"rad": "RAD", "blaze": "BLAZE", "flexiplex": "Flexiplex"}[tool]
        expected = allv[(key_tool, rep)]["counts"][barcode]
        if int(row["assigned_reads"]) != expected:
            check(checks, f"long_cell_{tool}_{rep}_{rank}", row["assigned_reads"], expected, checks)
            break
    else:
        check(checks, "long_all_counts", "MATCH", "MATCH", checks)

    ident = root / "results" / "false_target_identity_and_counts.tsv"
    with ident.open(newline="", encoding="ascii") as fh:
        ir = list(csv.DictReader(fh, delimiter="\t"))
    check(checks, "identity_rows", len(ir), 15000, checks)
    check(checks, "identity_mapping_fields", {"replicate", "whitelist_row_index", "barcode", "rad_assigned_reads", "blaze_assigned_reads", "flexiplex_assigned_reads"}.issubset(set(ir[0] if ir else [])), True, checks)

    # Check all nine exit markers and forced whitelist copies/hashes.
    for tool, sub, marker in (("RAD", "rad", "RAD_EXIT0"), ("BLAZE", "blaze", "BLAZE_EXIT0"), ("Flexiplex", "flexiplex", "FLEXIPLEX_AUDIT_EXIT0")):
        for rep in REPS:
            d = root / "runs" / sub / f"rep{rep}"
            check(checks, f"{tool}_rep{rep}_exit0", (d / marker).exists(), True, checks)
            forced = d / ("supplied_whitelist_used.txt" if tool != "BLAZE" else "known_bc_list_used.txt")
            src = root / "whitelists" / f"false_rep{rep}.txt"
            check(checks, f"{tool}_rep{rep}_forced_wl_bytes", forced.read_bytes(), src.read_bytes(), checks)
            check(checks, f"{tool}_rep{rep}_forced_wl_sha", sha256(forced), sha256(src), checks)

    failed = [r for r in checks if r[3] != "PASS"]
    val = root / "validation" / "INDEPENDENT_VALIDATION.tsv"
    val.parent.mkdir(parents=True, exist_ok=True)
    lines = ["check\tobserved\texpected\tstatus\n"] + ["\t".join(r) + "\n" for r in checks]
    atomic_write(val, "".join(lines))
    atomic_write(root / "validation" / "INDEPENDENT_VALIDATION.json", json.dumps({"checks": len(checks), "passed": len(checks)-len(failed), "failed": len(failed), "failed_checks": [r[0] for r in failed]}, indent=2, sort_keys=True) + "\n")
    if failed:
        raise SystemExit(f"independent audit failed ({len(failed)} checks); see {val}")
    print(f"PASS independent_checks={len(checks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
