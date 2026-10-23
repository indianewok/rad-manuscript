#!/dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/miniconda3/bin/python
"""
Generate heterogeneous, truth-conditioned FASTQ qualities for ScTagger reads.

The input sequences and headers are copied verbatim.  Background qualities are
sampled from the marginal distribution of a Badread qscore model.  At the known
16 nt barcode locus, qualities are sampled from the same model conditional on
the edit CIGAR between the observed barcode and the truth barcode encoded in
the read header.

Expected read ID form:
    @ACGTACGTACGTACGT-1234
"""

from __future__ import annotations

import argparse
import bisect
import collections
import gzip
import hashlib
import io
import math
import os
import pathlib
import random
import re
import shutil
import subprocess
import sys
import time
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import edlib
import numpy as np

from badread.qscore_model import QScoreModel, get_qscores


ADAPTER = "CTACACGACGCTCTTCCGATCT"
BARCODE_LENGTH = 16
READ_ID_RE = re.compile(r"^@([ACGT]{16})-(\d+)(?:\s|$)")
RC_TABLE = str.maketrans("ACGTNacgtn", "TGCANtgcan")


def reverse_complement(sequence: str) -> str:
    return sequence.translate(RC_TABLE)[::-1]


def stable_seed(text: str, seed: int, purpose: str) -> int:
    payload = f"{seed}\0{purpose}\0{text}".encode("ascii")
    return int.from_bytes(hashlib.blake2b(payload, digest_size=8).digest(), "little")


def parse_shifts(raw: str) -> List[int]:
    shifts = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        shifts.append(int(token))
    if not shifts:
        raise ValueError("at least one shift is required")
    if len(set(shifts)) != len(shifts):
        raise ValueError("shifts must be unique")
    if min(shifts) < -30 or max(shifts) > 60:
        raise ValueError("shifts outside the supported range [-30, 60]")
    return shifts


def parse_model_overall(model_path: pathlib.Path) -> Tuple[np.ndarray, np.ndarray]:
    opener = gzip.open if model_path.suffix == ".gz" else open
    with opener(model_path, "rt") as handle:
        for line in handle:
            fields = line.rstrip("\n").split(";")
            if fields[0] != "overall":
                continue
            scores: List[int] = []
            probabilities: List[float] = []
            for item in fields[2].split(","):
                if not item:
                    continue
                score, probability = item.split(":")
                scores.append(int(score))
                probabilities.append(float(probability))
            probs = np.asarray(probabilities, dtype=np.float64)
            probs /= probs.sum()
            return np.asarray(scores, dtype=np.uint8), probs
    raise ValueError(f"no overall distribution in qscore model: {model_path}")


def make_quality_tape(
    scores: np.ndarray,
    probabilities: np.ndarray,
    seed: int,
    size: int,
) -> bytes:
    rng = np.random.default_rng(seed)
    sampled = rng.choice(scores, size=size, replace=True, p=probabilities)
    sampled += 33
    return sampled.tobytes()


def tape_slice(tape: bytes, offset: int, length: int) -> bytearray:
    if length <= len(tape) - offset:
        return bytearray(tape[offset : offset + length])
    result = bytearray()
    remaining = length
    cursor = offset
    while remaining:
        take = min(remaining, len(tape) - cursor)
        result.extend(tape[cursor : cursor + take])
        remaining -= take
        cursor = 0
    return result


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


class PigzWriter:
    def __init__(
        self,
        final_path: pathlib.Path,
        threads: int,
        force: bool,
    ) -> None:
        self.final_path = final_path
        self.partial_path = final_path.with_name(
            f"{final_path.name}.partial.{os.getpid()}"
        )
        if final_path.exists() and not force:
            raise FileExistsError(f"output exists (use --force): {final_path}")
        self.output_handle = open(self.partial_path, "wb")
        self.process = subprocess.Popen(
            ["pigz", "-1", "-p", str(threads), "-c"],
            stdin=subprocess.PIPE,
            stdout=self.output_handle,
            stderr=subprocess.PIPE,
        )
        assert self.process.stdin is not None

    def write(self, data: bytes) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(data)

    def finish(self) -> None:
        assert self.process.stdin is not None
        self.process.stdin.close()
        stderr = self.process.stderr.read().decode("utf-8", "replace")
        return_code = self.process.wait()
        self.output_handle.close()
        if return_code != 0:
            raise RuntimeError(
                f"pigz failed for {self.final_path} ({return_code}): {stderr}"
            )
        os.replace(self.partial_path, self.final_path)

    def abort(self) -> None:
        try:
            if self.process.stdin is not None:
                self.process.stdin.close()
        except BrokenPipeError:
            pass
        if self.process.poll() is None:
            self.process.terminate()
            self.process.wait()
        self.output_handle.close()


def make_shift_table(shift: int) -> bytes:
    return bytes(
        max(33 + 1, min(33 + 50, value + shift)) for value in range(256)
    )


def quantile_from_histogram(histogram: collections.Counter, fraction: float) -> int:
    total = sum(histogram.values())
    target = math.ceil(total * fraction)
    cumulative = 0
    for value in sorted(histogram):
        cumulative += histogram[value]
        if cumulative >= target:
            return int(value)
    raise ValueError("empty histogram")


def calibrated_shift(
    min_q_histogram: collections.Counter,
    target_pass_fraction: float,
    threshold: int = 15,
) -> Tuple[int, float]:
    total = sum(min_q_histogram.values())
    best: Optional[Tuple[float, int, float]] = None
    for shift in range(-30, 61):
        passed = sum(
            count
            for min_q, count in min_q_histogram.items()
            if min_q + shift >= threshold
        )
        fraction = passed / total
        candidate = (abs(fraction - target_pass_fraction), shift, fraction)
        if best is None or candidate < best:
            best = candidate
    assert best is not None
    return best[1], best[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=pathlib.Path)
    parser.add_argument("--output-dir", required=True, type=pathlib.Path)
    parser.add_argument(
        "--model",
        type=pathlib.Path,
        default=pathlib.Path(
            "/dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/miniconda3/"
            "lib/python3.9/site-packages/badread/qscore_models/"
            "nanopore2018.gz"
        ),
    )
    parser.add_argument(
        "--shifts",
        default="1,2,3,4,5,6,8,10",
        help="comma-delimited integer Phred shifts",
    )
    parser.add_argument("--seed", type=int, default=20260727)
    parser.add_argument("--adapter-max-ed", type=int, default=7)
    parser.add_argument("--boundary-slop", type=int, default=8)
    parser.add_argument("--tape-size", type=int, default=1 << 24)
    parser.add_argument("--pigz-threads", type=int, default=1)
    parser.add_argument("--progress-every", type=int, default=10000)
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    shifts = parse_shifts(args.shifts)
    shift_tables = {shift: make_shift_table(shift) for shift in shifts}
    if not args.input.is_file():
        raise FileNotFoundError(args.input)
    if not args.model.is_file():
        raise FileNotFoundError(args.model)
    if shutil.which("pigz") is None:
        raise RuntimeError("pigz is required")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    scores, probabilities = parse_model_overall(args.model)
    tape = make_quality_tape(
        scores,
        probabilities,
        stable_seed(str(args.model), args.seed, "quality-tape"),
        args.tape_size,
    )
    conditional_model = QScoreModel(str(args.model), output=io.StringIO())

    stem = args.input.name
    for suffix in (".fastq.gz", ".fq.gz", ".fastq", ".fq"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break

    writers: Dict[int, PigzWriter] = {}
    output_paths: Dict[int, pathlib.Path] = {}
    for shift in shifts:
        shift_label = f"p{shift:02d}" if shift >= 0 else f"m{abs(shift):02d}"
        output_path = (
            args.output_dir
            / f"{stem}.badread2018_truthbc.shift_{shift_label}.fq.gz"
        )
        output_paths[shift] = output_path
        writers[shift] = PigzWriter(
            output_path,
            threads=args.pigz_threads,
            force=args.force,
        )

    start_time = time.monotonic()
    reads = 0
    bases = 0
    located = 0
    model_failures = 0
    orientation_counts = collections.Counter()
    adapter_ed_counts = collections.Counter()
    barcode_ed_counts = collections.Counter()
    boundary_delta_counts = collections.Counter()
    barcode_min_q_counts = collections.Counter()
    barcode_base_q_counts = collections.Counter()
    source_header_sequence_hash = hashlib.sha256()

    try:
        with gzip.open(args.input, "rt") as input_handle:
            while True:
                header = input_handle.readline()
                if not header:
                    break
                sequence_line = input_handle.readline()
                plus = input_handle.readline()
                original_quality = input_handle.readline()
                if not sequence_line or not plus or not original_quality:
                    raise ValueError(f"truncated FASTQ after record {reads}")

                header = header.rstrip("\r\n")
                sequence = sequence_line.rstrip("\r\n").upper()
                plus = plus.rstrip("\r\n")
                original_quality = original_quality.rstrip("\r\n")
                if not header.startswith("@") or not plus.startswith("+"):
                    raise ValueError(f"malformed FASTQ record {reads + 1}")
                if len(sequence) != len(original_quality):
                    raise ValueError(
                        f"sequence/quality length mismatch at {header}"
                    )
                match = READ_ID_RE.match(header)
                if match is None:
                    raise ValueError(
                        f"header does not encode 16 nt truth barcode: {header}"
                    )
                truth = match.group(1)

                read_seed = stable_seed(header, args.seed, "read")
                offset = stable_seed(header, args.seed, "background") % len(tape)
                quality = tape_slice(tape, offset, len(sequence))
                location = locate_truth_barcode(
                    sequence,
                    truth,
                    adapter_max_ed=args.adapter_max_ed,
                    boundary_slop=args.boundary_slop,
                )

                if location is not None:
                    located += 1
                    orientation = str(location["orientation"])
                    observed = str(location["observed_oriented"])
                    original_start = int(location["barcode_start_original"])
                    try:
                        random.seed(read_seed)
                        q16, _actual_identity, _identity_by_qscores = get_qscores(
                            observed,
                            truth,
                            conditional_model,
                        )
                        q16_bytes = q16.encode("ascii")
                    except Exception:
                        model_failures += 1
                        q16_bytes = bytes(
                            quality[original_start : original_start + BARCODE_LENGTH]
                        )

                    if orientation == "-":
                        q16_bytes = q16_bytes[::-1]
                    quality[
                        original_start : original_start + BARCODE_LENGTH
                    ] = q16_bytes

                    min_q = min(value - 33 for value in q16_bytes)
                    barcode_min_q_counts[min_q] += 1
                    barcode_base_q_counts.update(value - 33 for value in q16_bytes)
                    orientation_counts[orientation] += 1
                    adapter_ed_counts[int(location["adapter_ed"])] += 1
                    barcode_ed_counts[int(location["barcode_ed"])] += 1
                    boundary_delta_counts[int(location["boundary_delta"])] += 1
                else:
                    orientation_counts["not_located"] += 1

                prefix = (
                    header.encode("ascii")
                    + b"\n"
                    + sequence.encode("ascii")
                    + b"\n"
                    + plus.encode("ascii")
                    + b"\n"
                )
                source_header_sequence_hash.update(header.encode("ascii"))
                source_header_sequence_hash.update(b"\n")
                source_header_sequence_hash.update(sequence.encode("ascii"))
                source_header_sequence_hash.update(b"\n")
                for shift, writer in writers.items():
                    writer.write(prefix)
                    writer.write(bytes(quality).translate(shift_tables[shift]))
                    writer.write(b"\n")

                reads += 1
                bases += len(sequence)
                if args.progress_every and reads % args.progress_every == 0:
                    elapsed = time.monotonic() - start_time
                    print(
                        f"processed={reads} located={located} "
                        f"elapsed_s={elapsed:.1f}",
                        file=sys.stderr,
                        flush=True,
                    )
    except BaseException:
        for writer in writers.values():
            writer.abort()
        raise

    for writer in writers.values():
        writer.finish()

    elapsed = time.monotonic() - start_time
    summary_path = args.output_dir / f"{stem}.generation_summary.tsv"
    with open(summary_path, "w") as summary:
        summary.write("metric\tvalue\n")
        summary.write(f"input\t{args.input}\n")
        summary.write(f"model\t{args.model}\n")
        summary.write(f"seed\t{args.seed}\n")
        summary.write(f"reads\t{reads}\n")
        summary.write(f"bases\t{bases}\n")
        summary.write(f"located\t{located}\n")
        summary.write(f"located_fraction\t{located / reads:.12f}\n")
        summary.write(f"model_failures\t{model_failures}\n")
        summary.write(f"elapsed_seconds\t{elapsed:.6f}\n")
        summary.write(
            "header_sequence_sha256\t"
            f"{source_header_sequence_hash.hexdigest()}\n"
        )
        for key, value in sorted(orientation_counts.items()):
            summary.write(f"orientation_{key}\t{value}\n")
        for key, value in sorted(adapter_ed_counts.items()):
            summary.write(f"adapter_ed_{key}\t{value}\n")
        for key, value in sorted(barcode_ed_counts.items()):
            summary.write(f"barcode_ed_{key}\t{value}\n")
        for key, value in sorted(boundary_delta_counts.items()):
            summary.write(f"boundary_delta_{key}\t{value}\n")

    per_shift_path = args.output_dir / f"{stem}.per_shift_summary.tsv"
    with open(per_shift_path, "w") as summary:
        summary.write(
            "shift\toutput\tlocated_barcodes\tpass_minQ15\t"
            "pass_fraction\tmean_barcode_base_q\t"
            "median_barcode_min_q\n"
        )
        total_barcode_bases = sum(barcode_base_q_counts.values())
        native_mean = (
            sum(q * count for q, count in barcode_base_q_counts.items())
            / total_barcode_bases
        )
        for shift in shifts:
            passed = sum(
                count
                for min_q, count in barcode_min_q_counts.items()
                if min_q + shift >= 15
            )
            median_min = quantile_from_histogram(barcode_min_q_counts, 0.5)
            summary.write(
                f"{shift}\t{output_paths[shift]}\t{located}\t{passed}\t"
                f"{passed / located:.12f}\t{native_mean + shift:.6f}\t"
                f"{median_min + shift}\n"
            )

    calibration_path = args.output_dir / f"{stem}.calibrated_shifts.tsv"
    with open(calibration_path, "w") as summary:
        summary.write("target_pass_fraction\tshift\tachieved_pass_fraction\n")
        for target in (0.60, 0.825, 0.95):
            shift, achieved = calibrated_shift(barcode_min_q_counts, target)
            summary.write(f"{target:.6f}\t{shift}\t{achieved:.12f}\n")

    histogram_path = args.output_dir / f"{stem}.native_barcode_min_q.tsv"
    with open(histogram_path, "w") as summary:
        summary.write("min_q\tcount\n")
        for q, count in sorted(barcode_min_q_counts.items()):
            summary.write(f"{q}\t{count}\n")

    print(f"summary={summary_path}", file=sys.stderr)
    print(f"per_shift={per_shift_path}", file=sys.stderr)
    print(f"calibration={calibration_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
