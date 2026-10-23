#!/usr/bin/env python3
"""Normalize FLAMESv2 MATCHED_SPLIT statistics to the RAD comparison schema."""

from __future__ import annotations

import argparse
import csv
import gzip
from pathlib import Path


COMPLEMENT = str.maketrans("ACGTNacgtn", "TGCANtgcan")


def reverse_complement(sequence: str) -> str:
    return sequence.translate(COMPLEMENT)[::-1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_stats", type=Path)
    parser.add_argument("output_assignments", type=Path)
    args = parser.parse_args()

    args.output_assignments.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(args.input_stats, "rt", newline="") as source, gzip.open(
        args.output_assignments, "wt", newline=""
    ) as dest:
        reader = csv.DictReader(source, delimiter="\t")
        required = {"Read", "UB", "BC1", "BC2", "BC3", "FlankEditDist"}
        missing = required.difference(reader.fieldnames or ())
        if missing:
            raise ValueError(f"missing FLAMESv2 columns: {sorted(missing)}")

        writer = csv.writer(dest, delimiter="\t", lineterminator="\n")
        writer.writerow(
            ["read_id", "barcode", "umi", "orientation", "flank_edit_distance"]
        )
        for row in reader:
            # FLAMESv2 traverses BC1 -> BC2 -> BC3. RAD and the published-cell
            # map use the opposite, cDNA-proximal ordering: BC3_BC2_BC1.
            barcode = "_".join((row["BC3"], row["BC2"], row["BC1"]))
            writer.writerow(
                [
                    row["Read"],
                    barcode,
                    reverse_complement(row["UB"]),
                    "",
                    row["FlankEditDist"],
                ]
            )


if __name__ == "__main__":
    main()
