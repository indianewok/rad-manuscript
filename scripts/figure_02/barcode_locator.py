"""Unchanged truth-barcode locator from the selected native2023 generator.

Only the three locator functions and their constants/imports are retained.
No quality-model sampling or FASTQ generation is imported or executed.
"""
from typing import Dict, Optional, Tuple, List
import edlib

ORIGINAL_SOURCE_PATH = 'scratch_preservation_20260921/files/sctagger_nanopore2023_unadjusted_20260913/scripts/generate_truth_conditioned_qscores.py'
ORIGINAL_SOURCE_SHA256 = 'aef619a3f417c4aa4c2c9ac3bfd161916a7e85efa23720ae74a8b630a9026e49'
COPIED_FUNCTIONS_SHA256 = '1d6e2734bb901c2bfe01b99a5aa60dfb6b51508f6dcc3d195b926d2739da4b5b'
ADAPTER = "CTACACGACGCTCTTCCGATCT"
BARCODE_LENGTH = 16
RC_TABLE = str.maketrans("ACGTNacgtn", "TGCANtgcan")


def reverse_complement(sequence: str) -> str:
    return sequence.translate(RC_TABLE)[::-1]


def nw_edit_distance(left: str, right: str) -> int:
    return int(edlib.align(left, right, mode="NW", task="distance")["editDistance"])


def locate_truth_barcode(
    sequence: str,
    truth: str,
    adapter_max_ed: int,
    boundary_slop: int,
) -> Optional[Dict[str, object]]:
    """
    Locate the barcode in a method-neutral way from the known read layout.

    Both read orientations are converted to the canonical
    adapter->barcode->UMI orientation.  Candidate barcode starts are constrained
    to a small window around the aligned adapter boundary, and truth is used
    only to resolve boundary shifts caused by sequencing indels.
    """
    candidates: List[Tuple[Tuple[int, ...], Dict[str, object]]] = []
    for orientation_rank, (orientation, oriented) in enumerate(
        (("+", sequence), ("-", reverse_complement(sequence)))
    ):
        adapter_result = edlib.align(
            ADAPTER,
            oriented,
            mode="HW",
            task="locations",
            k=adapter_max_ed,
        )
        adapter_ed = int(adapter_result["editDistance"])
        if adapter_ed < 0:
            continue

        for adapter_start, adapter_end in adapter_result["locations"]:
            nominal_start = int(adapter_end) + 1
            window_start = max(0, nominal_start - boundary_slop)
            window_end = min(
                len(oriented),
                nominal_start + BARCODE_LENGTH + boundary_slop,
            )
            neighborhood = oriented[window_start:window_end]
            if len(neighborhood) < BARCODE_LENGTH:
                continue

            truth_result = edlib.align(
                truth,
                neighborhood,
                mode="HW",
                task="locations",
            )
            truth_ed = int(truth_result["editDistance"])
            if truth_ed < 0:
                continue

            for local_start, _local_end in truth_result["locations"]:
                oriented_start = window_start + max(0, int(local_start))
                if oriented_start + BARCODE_LENGTH > len(oriented):
                    continue
                observed = oriented[
                    oriented_start : oriented_start + BARCODE_LENGTH
                ]
                physical_ed = nw_edit_distance(observed, truth)
                boundary_delta = oriented_start - nominal_start
                if orientation == "+":
                    original_start = oriented_start
                else:
                    original_start = (
                        len(sequence) - oriented_start - BARCODE_LENGTH
                    )

                candidate = {
                    "orientation": orientation,
                    "adapter_start_oriented": int(adapter_start),
                    "adapter_end_oriented": int(adapter_end),
                    "adapter_ed": adapter_ed,
                    "nominal_barcode_start_oriented": nominal_start,
                    "barcode_start_oriented": oriented_start,
                    "barcode_start_original": original_start,
                    "boundary_delta": boundary_delta,
                    "observed_oriented": observed,
                    "barcode_ed": physical_ed,
                }
                # Combined layout evidence first, then deterministic tie-breaks.
                rank = (
                    adapter_ed + physical_ed,
                    adapter_ed,
                    physical_ed,
                    abs(boundary_delta),
                    orientation_rank,
                    oriented_start,
                )
                candidates.append((rank, candidate))

    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]

