#!/usr/bin/env python3
"""Generate deterministic false target whitelists for LongBench SC-ONT.

The global catalog and matched Cell Ranger list are supplied as paths.  The
global file is the canonical 16-mer text catalog (one barcode per line); the
matched file may be gzip-compressed and may carry a terminal ``-1`` suffix.
Each replicate is a uniform sample without replacement from the global
catalog after removing every normalized matched barcode.  The sampled rows
are emitted in lexical order, making row/rank pairing reproducible.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import random
from pathlib import Path


def open_text(path: Path):
    return gzip.open(path, "rt") if path.name.endswith(".gz") else path.open("rt")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def normalized(barcode: str) -> str:
    return barcode.strip().removesuffix("-1")


def read_matched(path: Path) -> list[str]:
    out: list[str] = []
    with open_text(path) as fh:
        for raw in fh:
            bc = normalized(raw)
            if bc:
                out.append(bc)
    if len(out) != len(set(out)):
        raise RuntimeError("matched Cell Ranger list contains duplicates")
    return out


def read_global(path: Path) -> list[str]:
    out: list[str] = []
    with open_text(path) as fh:
        for raw in fh:
            bc = raw.strip()
            if bc:
                out.append(bc)
    if len(out) != len(set(out)):
        raise RuntimeError("global catalog contains duplicates")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--global-catalog", type=Path, required=True)
    ap.add_argument("--matched", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--seed", type=int, action="append", required=True)
    ap.add_argument("--prefix", default="false_whitelist")
    ap.add_argument("--manifest", type=Path, required=True)
    args = ap.parse_args()
    if len(args.seed) != 3:
        raise SystemExit("exactly three --seed values are required")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    matched = read_matched(args.matched)
    matched_set = set(matched)
    global_catalog = read_global(args.global_catalog)
    eligible = [bc for bc in global_catalog if bc not in matched_set]
    if len(eligible) < args.n:
        raise RuntimeError(f"eligible global catalog ({len(eligible)}) smaller than N={args.n}")

    outputs: list[Path] = []
    rows = []
    for rep, seed in enumerate(args.seed, 1):
        rng = random.Random(seed)
        # random.sample is a uniform no-replacement sample; sort only the
        # selected values so rank is independent of hash/set iteration order.
        selected = sorted(rng.sample(eligible, args.n))
        path = args.output_dir / f"{args.prefix}_rep{rep}.txt"
        with path.open("wt", newline="\n") as fh:
            fh.write("\n".join(selected) + "\n")
        outputs.append(path)
        rows.append((rep, seed, len(selected), len(set(selected)), sum(bc in matched_set for bc in selected), digest(path)))

    # Exact pairwise intersections are retained in the manifest for review.
    sets = [set(p.read_text().splitlines()) for p in outputs]
    pairwise = {
        "rep1_rep2": len(sets[0] & sets[1]),
        "rep1_rep3": len(sets[0] & sets[2]),
        "rep2_rep3": len(sets[1] & sets[2]),
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest.open("wt", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["field", "value"])
        w.writerow(["global_catalog_path", str(args.global_catalog)])
        w.writerow(["global_catalog_sha256", digest(args.global_catalog)])
        w.writerow(["global_catalog_rows", len(global_catalog)])
        w.writerow(["matched_path", str(args.matched)])
        w.writerow(["matched_sha256", digest(args.matched)])
        w.writerow(["matched_rows", len(matched)])
        w.writerow(["matched_normalization", "strip terminal -1"])
        w.writerow(["eligible_rows", len(eligible)])
        w.writerow(["sample_size_N", args.n])
        w.writerow(["sampling_method", "random.Random(seed).sample(eligible, N), then lexical sort"])
        w.writerow(["replicate_seeds", ",".join(map(str, args.seed))])
        for rep, seed, size, unique, overlap, sha in rows:
            w.writerow([f"rep{rep}_seed", seed])
            w.writerow([f"rep{rep}_rows", size])
            w.writerow([f"rep{rep}_unique", unique])
            w.writerow([f"rep{rep}_overlap_matched", overlap])
            w.writerow([f"rep{rep}_sha256", sha])
        for key, value in pairwise.items():
            w.writerow([f"pairwise_{key}", value])


if __name__ == "__main__":
    main()
