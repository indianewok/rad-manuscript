#!/usr/bin/env python3
"""Generate deterministic 5,000-barcode ScTagger-L false target lists.

The RAD 10x 3v3 catalog is a bitlist (one integer per line).  We sample
catalog *row indices* with Python's explicitly recorded Mersenne Twister
implementation, reject the 5,000 known/short-read-matched barcodes, then sort
each emitted list lexicographically.  Sampling by row index avoids loading the
6.8M-entry catalog into a Python set and makes the exact source auditable.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import random
import sys
from pathlib import Path

BASES = "ACTG"  # 2-bit code order used by RAD's bitlist decoder
N = 5_000


def decode(value: int, length: int = 16) -> str:
    chars = []
    for _ in range(length):
        chars.append(BASES[value & 3])
        value >>= 2
    if value:
        raise ValueError("bitlist value exceeds declared barcode length")
    return "".join(reversed(chars))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def catalog_count(path: Path) -> int:
    count = 0
    with gzip.open(path, "rt", encoding="ascii", newline="") as fh:
        for line in fh:
            if line.strip():
                count += 1
    return count


def selected_barcodes(path: Path, indices: set[int]) -> dict[int, str]:
    selected: dict[int, str] = {}
    with gzip.open(path, "rt", encoding="ascii", newline="") as fh:
        for i, line in enumerate(fh):
            if i in indices:
                raw = line.strip()
                if not raw.isdigit():
                    raise ValueError(f"non-integer bitlist row {i}: {raw!r}")
                selected[i] = decode(int(raw))
                if len(selected) == len(indices):
                    break
    if len(selected) != len(indices):
        raise ValueError("selected row index was outside the catalog")
    return selected


def sample_one(path: Path, truth: set[str], seed: int, n: int, catalog_n: int):
    rng = random.Random(seed)
    # Repeated fixed-size draws are equivalent to rejection sampling without
    # replacement.  Every RNG draw is recorded through the seed and Python
    # version in the manifest; no system entropy is consulted.
    selected: dict[str, int] = {}
    draws = 0
    batches = 0
    processed = 0
    while len(selected) < n:
        need = n - len(selected)
        # A modest cushion reduces streaming passes while retaining deterministic
        # rejection semantics.  There are only 5,000 exclusions in 6.79M rows.
        batch = min(catalog_n - draws, max(need + 32, int(need * 1.01) + 16))
        if batch <= 0:
            raise RuntimeError("catalog exhausted before enough non-truth barcodes")
        indices = rng.sample(range(catalog_n), batch)
        draws += batch
        batches += 1
        values = selected_barcodes(path, set(indices))
        for index in indices:
            processed += 1
            barcode = values[index]
            if barcode in truth or barcode in selected:
                continue
            selected[barcode] = index
            if len(selected) == n:
                break
    return sorted(selected), {
        "seed": seed,
        "rng": "random.Random (MT19937), Python %s" % sys.version.split()[0],
        "requested": n,
        "accepted": len(selected),
        "catalog_rows_drawn": draws,
        "catalog_rows_processed": processed,
        "streaming_passes": batches,
        "rejected_truth_or_duplicate": processed - len(selected),
        "unused_cushion_draws": draws - processed,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--global-bitlist", type=Path, required=True)
    ap.add_argument("--truth", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--seeds", type=int, nargs=3, default=[20260813, 20260814, 20260815])
    args = ap.parse_args()

    truth = {line.strip() for line in args.truth.read_text().splitlines() if line.strip()}
    if len(truth) != N or any(len(x) != 16 or set(x) - set("ACGT") for x in truth):
        raise ValueError("truth list must contain exactly 5,000 unique 16-mer ACGT barcodes")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    count = catalog_count(args.global_bitlist)
    if count != 6_794_880:
        raise ValueError(f"unexpected 10x3v3 catalog row count: {count}")
    manifest = {
        "catalog": {
            "path": str(args.global_bitlist),
            "sha256": sha256(args.global_bitlist),
            "rows": count,
            "decoder": "RAD 2-bit A=0,C=1,T=2,G=3; low-to-high then reverse; length=16",
        },
        "truth": {
            "path": str(args.truth),
            "sha256": sha256(args.truth),
            "rows": len(truth),
        },
        "sample_size": N,
        "replicates": [],
    }
    all_lists: list[set[str]] = []
    for rep, seed in enumerate(args.seeds, start=1):
        barcodes, details = sample_one(args.global_bitlist, truth, seed, N, count)
        values = set(barcodes)
        if len(values) != N or values & truth:
            raise AssertionError("false-list uniqueness/truth exclusion failed")
        out = args.output_dir / f"false_rep{rep}.txt"
        out.write_text("\n".join(barcodes) + "\n")
        details.update({
            "replicate": rep,
            "path": str(out),
            "sha256": sha256(out),
            "min_barcode": barcodes[0],
            "max_barcode": barcodes[-1],
        })
        manifest["replicates"].append(details)
        all_lists.append(values)
    manifest["pairwise_overlap"] = {
        "rep1_rep2": len(all_lists[0] & all_lists[1]),
        "rep1_rep3": len(all_lists[0] & all_lists[2]),
        "rep2_rep3": len(all_lists[1] & all_lists[2]),
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
