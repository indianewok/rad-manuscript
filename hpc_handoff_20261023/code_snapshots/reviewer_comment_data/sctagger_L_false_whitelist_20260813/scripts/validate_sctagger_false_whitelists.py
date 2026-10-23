#!/usr/bin/env python3
"""Independent validation of deterministic false-target whitelist files."""

from __future__ import annotations

import argparse
import gzip
import hashlib
from pathlib import Path

BASES = "ACTG"


def decode(value: int) -> str:
    chars = []
    for _ in range(16):
        chars.append(BASES[value & 3])
        value >>= 2
    return "".join(reversed(chars))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--global-bitlist", type=Path, required=True)
    ap.add_argument("--truth", type=Path, required=True)
    ap.add_argument("--whitelist-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    truth = {x.strip() for x in args.truth.read_text().splitlines() if x.strip()}
    reps = {}
    for i in (1, 2, 3):
        p = args.whitelist_dir / f"false_rep{i}.txt"
        vals = [x.strip() for x in p.read_text().splitlines() if x.strip()]
        reps[i] = set(vals)
    expected = []
    checks = []
    def check(name, observed, expected_value, status):
        checks.append((name, observed, expected_value, status))
    check("truth_rows", len(truth), 5000, "PASS" if len(truth) == 5000 else "FAIL")
    check("truth_unique", len(truth), 5000, "PASS" if len(truth) == 5000 else "FAIL")
    for i, vals in reps.items():
        p = args.whitelist_dir / f"false_rep{i}.txt"
        check(f"rep{i}_rows", sum(1 for _ in p.open()), 5000,
              "PASS" if sum(1 for _ in p.open()) == 5000 else "FAIL")
        check(f"rep{i}_unique", len(vals), 5000, "PASS" if len(vals) == 5000 else "FAIL")
        check(f"rep{i}_truth_overlap", len(vals & truth), 0, "PASS" if not vals & truth else "FAIL")
        check(f"rep{i}_format", sum(1 for x in vals if len(x) == 16 and not (set(x) - set("ACGT"))), 5000,
              "PASS" if all(len(x) == 16 and not (set(x) - set("ACGT")) for x in vals) else "FAIL")
    check("rep1_rep2_overlap", len(reps[1] & reps[2]), "report", "PASS")
    check("rep1_rep3_overlap", len(reps[1] & reps[3]), "report", "PASS")
    check("rep2_rep3_overlap", len(reps[2] & reps[3]), "report", "PASS")
    targets = set().union(*reps.values())
    found = set()
    catalog_rows = 0
    with gzip.open(args.global_bitlist, "rt", encoding="ascii", newline="") as fh:
        for line in fh:
            raw = line.strip()
            if not raw:
                continue
            catalog_rows += 1
            bc = decode(int(raw))
            if bc in targets:
                found.add(bc)
    check("global_catalog_rows", catalog_rows, 6794880, "PASS" if catalog_rows == 6794880 else "FAIL")
    for i, vals in reps.items():
        check(f"rep{i}_global_membership", len(found & vals), 5000,
              "PASS" if len(found & vals) == 5000 else "FAIL")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as out:
        out.write("check\tobserved\texpected\tstatus\n")
        for row in checks:
            out.write("%s\t%s\t%s\t%s\n" % row)
        out.write("global_bitlist_sha256\t%s\t(recorded)\tPASS\n" % sha(args.global_bitlist))
        out.write("truth_sha256\t%s\t(recorded)\tPASS\n" % sha(args.truth))
        for i in (1, 2, 3):
            p = args.whitelist_dir / f"false_rep{i}.txt"
            out.write(f"rep{i}_sha256\t{sha(p)}\t(recorded)\tPASS\n")
    failed = [x for x in checks if x[3] == "FAIL"]
    print(f"checks={len(checks)} failed={len(failed)} global_rows={catalog_rows} targets_found={len(found)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
