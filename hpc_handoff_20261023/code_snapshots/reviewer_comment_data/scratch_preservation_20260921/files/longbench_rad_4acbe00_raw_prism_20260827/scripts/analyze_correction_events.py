#!/usr/bin/env python3
"""Stream LongBench demultiplexing outputs into barcode-flow summaries.

The primary unit is a unique (physical_read_id, target_barcode) assignment.
Assignment-record totals are retained separately.  Tool outputs are required
to group all records from a physical read contiguously.  The default
disk-backed grouping check proves that contract without retaining read IDs in
RAM; a non-contiguous re-entry aborts the analysis.

Only exact observed source barcodes support source-membership claims.  A
catalog-valid source outside the Cell Ranger filtered set is kept as an
operational ambient/non-cell tier and is never assigned a donor or cell line.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import gzip
import hashlib
import io
import itertools
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from array import array
from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Set, TextIO, Tuple


DNA = frozenset("ACGT")
RAD_SUFFIX = re.compile(r"-(?:F|R)(?:-CT)?$")
BARCODE_SUFFIX = re.compile(r"-\d+$")
OCTAMER_CODES = {
    "".join(bases): code
    for code, bases in enumerate(itertools.product("ACGT", repeat=8))
}

CLASS_NAMES = (
    "all_assignments",
    "native_exact",
    "all_corrected",
    "selected_source_changed",
    "missed_cellranger_to_selected",
    "cellranger_to_different_cellranger",
    "consensus_cross_line",
    "consensus_same_line_different_cell",
    "consensus_label_incomplete",
    "cellranger_to_noncellranger_selected",
    "catalog_noncell_to_selected",
    "noncatalog_to_selected",
    "raw_source_unavailable",
    "correction_state_unknown",
    "correction_hint_conflict",
    "target_outside_selected",
    "target_invalid_barcode",
    "multiple_exact_sources",
)


def barcode_code(value: str) -> Optional[int]:
    value = value.strip().upper()
    if len(value) != 16:
        return None
    try:
        return (OCTAMER_CODES[value[:8]] << 16) | OCTAMER_CODES[value[8:]]
    except KeyError:
        return None


def code_barcode(code: int) -> str:
    chars = ["A"] * 16
    alphabet = "ACGT"
    for index in range(15, -1, -1):
        chars[index] = alphabet[code & 3]
        code >>= 2
    return "".join(chars)


def normalize_barcode(value: str) -> str:
    value = value.strip().strip("\"'").upper()
    return BARCODE_SUFFIX.sub("", value)


def revcomp(value: str) -> str:
    return value.upper().translate(str.maketrans("ACGT", "TGCA"))[::-1]


def first_barcode_in_line(line: str) -> Optional[str]:
    for token in re.split(r"[\t,\s]+", line.strip()):
        candidate = normalize_barcode(token)
        if barcode_code(candidate) is not None:
            return candidate
    return None


@contextmanager
def open_text(path: Path, decompress_threads: int = 1) -> Iterator[TextIO]:
    """Open plain/gzip text; optionally use pigz for large gzip streams."""
    if str(path) == "-":
        yield sys.stdin
        return
    if path.suffix != ".gz":
        with path.open("r", newline="") as handle:
            yield handle
        return
    pigz = shutil.which("pigz") if decompress_threads > 1 else None
    if pigz is None:
        with gzip.open(path, "rt", newline="") as handle:
            yield handle
        return
    process = subprocess.Popen(
        [pigz, "-dc", "-p", str(decompress_threads), str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1024 * 1024,
    )
    assert process.stdout is not None
    try:
        yield process.stdout
    finally:
        process.stdout.close()
        return_code = process.wait()
        stderr = process.stderr.read() if process.stderr is not None else ""
        if process.stderr is not None:
            process.stderr.close()
        # A caller that deliberately stops at --max-rows closes the pipe and
        # can give pigz SIGPIPE.  Full-file callers verify completion later.
        if return_code not in (0, -13, 141):
            raise RuntimeError(
                "pigz failed for {} (status {}): {}".format(
                    path, return_code, stderr.strip()
                )
            )


@contextmanager
def open_reference_text(path: Path) -> Iterator[TextIO]:
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            members = [name for name in archive.namelist() if not name.endswith("/")]
            if len(members) != 1:
                raise RuntimeError(
                    "Expected one file in barcode-catalog zip {}, found {}".format(
                        path, members
                    )
                )
            with archive.open(members[0]) as raw:
                with io.TextIOWrapper(raw) as handle:
                    yield handle
        return
    if path.suffix == ".gz":
        with gzip.open(path, "rt") as handle:
            yield handle
        return
    with path.open() as handle:
        yield handle


def load_barcode_set(path: Path) -> Tuple[Set[int], Dict[str, int]]:
    values: Set[int] = set()
    rows = 0
    invalid_rows = 0
    duplicate_rows = 0
    with open_reference_text(path) as handle:
        for line in handle:
            if not line.strip():
                continue
            rows += 1
            barcode = first_barcode_in_line(line)
            if barcode is None:
                invalid_rows += 1
                continue
            code = barcode_code(barcode)
            assert code is not None
            if code in values:
                duplicate_rows += 1
            values.add(code)
    if not values:
        raise RuntimeError("No 16-nt DNA barcodes were read from {}".format(path))
    return values, {
        "nonempty_rows": rows,
        "valid_unique_barcodes": len(values),
        "invalid_rows": invalid_rows,
        "duplicate_rows": duplicate_rows,
    }


class SortedCatalog:
    """Compact exact membership for a lexicographically sorted 16-mer catalog."""

    def __init__(self, path: Path, cache_path: Optional[Path] = None) -> None:
        self.path = path
        self.codes = array("I")
        self.rows = 0
        self.invalid_rows = 0
        self.duplicate_rows = 0
        self.loaded_from_cache = False
        source_stat = path.stat()
        expected_source = {
            "resolved_path": str(path.resolve()),
            "size_bytes": source_stat.st_size,
            "mtime_ns": source_stat.st_mtime_ns,
        }
        cache_meta_path = (
            Path(str(cache_path) + ".json") if cache_path is not None else None
        )
        if (
            cache_path is not None
            and cache_path.is_file()
            and cache_meta_path is not None
            and cache_meta_path.is_file()
        ):
            with cache_meta_path.open() as handle:
                cache_meta = json.load(handle)
            if (
                cache_meta.get("source") == expected_source
                and cache_meta.get("itemsize") == self.codes.itemsize
                and cache_meta.get("byteorder") == sys.byteorder
                and cache_path.stat().st_size
                == cache_meta.get("valid_unique_barcodes", -1) * self.codes.itemsize
            ):
                with cache_path.open("rb") as handle:
                    self.codes.fromfile(
                        handle, cache_meta["valid_unique_barcodes"]
                    )
                self.rows = cache_meta["nonempty_rows"]
                self.invalid_rows = cache_meta["invalid_rows"]
                self.duplicate_rows = cache_meta["duplicate_rows"]
                self.loaded_from_cache = True
                return
        previous: Optional[int] = None
        with open_reference_text(path) as handle:
            for line in handle:
                if not line.strip():
                    continue
                self.rows += 1
                barcode = first_barcode_in_line(line)
                if barcode is None:
                    self.invalid_rows += 1
                    continue
                code = barcode_code(barcode)
                assert code is not None
                if previous is not None and code < previous:
                    raise RuntimeError(
                        "Global catalog is not sorted by barcode at row {}: {}".format(
                            self.rows, path
                        )
                    )
                if previous == code:
                    self.duplicate_rows += 1
                    continue
                self.codes.append(code)
                previous = code
        if not self.codes:
            raise RuntimeError("No valid barcodes in global catalog {}".format(path))
        if cache_path is not None:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                prefix=".catalog.",
                suffix=".u32",
                dir=str(cache_path.parent),
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                self.codes.tofile(temporary)
            os.replace(str(temporary_path), str(cache_path))
            cache_meta = {
                "source": expected_source,
                "itemsize": self.codes.itemsize,
                "byteorder": sys.byteorder,
                "nonempty_rows": self.rows,
                "valid_unique_barcodes": len(self.codes),
                "invalid_rows": self.invalid_rows,
                "duplicate_rows": self.duplicate_rows,
            }
            assert cache_meta_path is not None
            with tempfile.NamedTemporaryFile(
                mode="w",
                prefix=".catalog.",
                suffix=".json",
                dir=str(cache_path.parent),
                delete=False,
            ) as temporary:
                temporary_meta_path = Path(temporary.name)
                json.dump(cache_meta, temporary, indent=2, sort_keys=True)
                temporary.write("\n")
            os.replace(str(temporary_meta_path), str(cache_meta_path))

    def __contains__(self, code: object) -> bool:
        if not isinstance(code, int):
            return False
        index = bisect.bisect_left(self.codes, code)
        return index < len(self.codes) and self.codes[index] == code

    def __len__(self) -> int:
        return len(self.codes)


def load_labels(label_dir: Optional[Path]) -> Tuple[Dict[int, str], Dict[str, object]]:
    if label_dir is None:
        return {}, {
            "label_directory": None,
            "label_files": 0,
            "labeled_barcodes": 0,
            "conflicts": 0,
        }
    paths = sorted(label_dir.glob("*_BC_list.txt"))
    if not paths:
        raise RuntimeError("No *_BC_list.txt files found under {}".format(label_dir))
    labels: Dict[int, str] = {}
    conflicts: List[Tuple[str, str, str]] = []
    rows = 0
    for path in paths:
        label = path.name[: -len("_BC_list.txt")]
        with path.open() as handle:
            for line in handle:
                if not line.strip():
                    continue
                rows += 1
                barcode = first_barcode_in_line(line)
                if barcode is None:
                    raise RuntimeError(
                        "Invalid label barcode in {}: {!r}".format(path, line.rstrip())
                    )
                code = barcode_code(barcode)
                assert code is not None
                old = labels.get(code)
                if old is not None and old != label:
                    conflicts.append((barcode, old, label))
                labels[code] = label
    if conflicts:
        raise RuntimeError(
            "Conflicting consensus labels; first examples: {}".format(conflicts[:5])
        )
    return labels, {
        "label_directory": str(label_dir),
        "label_files": len(paths),
        "label_rows": rows,
        "labeled_barcodes": len(labels),
        "conflicts": 0,
        "labels": sorted(set(labels.values())),
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def path_metadata(path: Optional[Path], include_hash: bool = False) -> Optional[Dict[str, object]]:
    if path is None:
        return None
    stat = path.stat()
    result: Dict[str, object] = {
        "path": str(path),
        "resolved_path": str(path.resolve()),
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }
    if include_hash:
        result["sha256"] = sha256(path)
    return result


@dataclass
class Assignment:
    read_id: str
    target: str
    source: Optional[str]
    corrected_hint: Optional[bool]
    raw_quality: Optional[float]
    source_evidence: str


@dataclass
class Classified:
    assignment: Assignment
    flags: Set[str]
    tier: str
    target_code: Optional[int]
    source_code: Optional[int]
    target_label: Optional[str]
    source_label: Optional[str]
    quality_tier: str


@dataclass
class SourceState:
    rows: int = 0
    flags: Set[str] = field(default_factory=set)
    source_code: Optional[int] = None
    source: Optional[str] = None
    source_label: Optional[str] = None
    target_label: Optional[str] = None
    source_evidence: Set[str] = field(default_factory=set)
    quality_tiers: Set[str] = field(default_factory=set)
    minimum_raw_quality: Optional[float] = None
    maximum_raw_quality: Optional[float] = None


@dataclass
class UnitState:
    target: str
    target_code: Optional[int]
    rows: int = 0
    flags: Set[str] = field(default_factory=set)
    sources: Dict[str, SourceState] = field(default_factory=dict)


def quality_tier(value: Optional[float]) -> str:
    if value is None or math.isnan(value):
        return "quality_unavailable"
    if value < 5:
        return "q_lt_5"
    if value < 10:
        return "q_5_to_lt_10"
    if value < 15:
        return "q_10_to_lt_15"
    return "q_ge_15"


def evidence_tier(flags: Set[str]) -> str:
    if "multiple_exact_sources" in flags:
        return "ambiguous_mixed_sources_within_read_target"
    if "target_outside_selected" in flags or "target_invalid_barcode" in flags:
        return "invariant_violation_invalid_target"
    if "consensus_cross_line" in flags:
        return "strict_consensus_cross_line_cellranger_redirect"
    if "consensus_same_line_different_cell" in flags:
        return "consensus_same_line_different_cell_redirect"
    if "cellranger_to_different_cellranger" in flags:
        return "cellranger_redirect_consensus_label_incomplete"
    if "missed_cellranger_to_selected" in flags:
        return "cellranger_source_to_noncellranger_selected"
    if "selected_source_changed" in flags:
        return "invariant_violation_selected_source_changed"
    if "catalog_noncell_to_selected" in flags:
        return "catalog_valid_unfiltered_operational_noncell_redirect"
    if "noncatalog_to_selected" in flags:
        return "noncatalog_redirect"
    if "raw_source_unavailable" in flags and "all_corrected" in flags:
        return "corrected_assignment_raw_source_unavailable"
    if "native_exact" in flags:
        return "native_exact"
    return "correction_state_or_source_ambiguous"


def source_relationship(classified: Classified) -> Tuple[str, str, str]:
    assignment = classified.assignment
    source_label = classified.source_label or "UNLABELED"
    target_label = classified.target_label or "UNLABELED"
    if assignment.source is None:
        return "raw_source_unavailable", "UNAVAILABLE", target_label
    if assignment.source == assignment.target:
        return "native_exact", source_label, target_label
    if "consensus_cross_line" in classified.flags:
        return "consensus_cross_line", source_label, target_label
    if "consensus_same_line_different_cell" in classified.flags:
        return "consensus_same_line_different_cell", source_label, target_label
    if "cellranger_to_different_cellranger" in classified.flags:
        return "cellranger_redirect_label_incomplete", source_label, target_label
    if "missed_cellranger_to_selected" in classified.flags:
        return "cellranger_source_to_noncellranger_selected", source_label, target_label
    if "catalog_noncell_to_selected" in classified.flags:
        return "catalog_valid_unfiltered", "NOT_APPLICABLE", target_label
    if "noncatalog_to_selected" in classified.flags:
        return "noncatalog", "NOT_APPLICABLE", target_label
    if "selected_source_changed" in classified.flags:
        return "selected_source_changed", source_label, target_label
    return "ambiguous", source_label, target_label


def parse_fastq_header_tags(header: str) -> Tuple[str, Dict[str, str]]:
    fields = header.rstrip("\r\n").split("\t")
    token = fields[0].lstrip("@>").split()[0]
    tags: Dict[str, str] = {}
    for field_value in fields[1:]:
        parts = field_value.split(":", 2)
        if len(parts) == 3:
            tags[parts[0]] = parts[2]
    return token, tags


def iter_fastq_headers(
    path: Path,
    stats: Counter,
    decompress_threads: int,
) -> Iterator[str]:
    with open_text(path, decompress_threads) as handle:
        while True:
            header = handle.readline()
            if not header:
                return
            sequence = handle.readline()
            plus = handle.readline()
            quality = handle.readline()
            if not sequence or not plus or not quality:
                raise RuntimeError("Truncated FASTQ record in {}".format(path))
            if not header.startswith("@") or not plus.startswith("+"):
                raise RuntimeError(
                    "Malformed FASTQ record {} in {}".format(
                        stats["fastq_records_read"] + 1, path
                    )
                )
            if len(sequence.rstrip("\r\n")) != len(quality.rstrip("\r\n")):
                raise RuntimeError(
                    "Sequence/quality length mismatch in {} at record {}".format(
                        path, stats["fastq_records_read"] + 1
                    )
                )
            stats["fastq_records_read"] += 1
            yield header


def iter_rad(
    path: Path,
    stats: Counter,
    decompress_threads: int,
    max_rows: Optional[int],
    exclude_rad_ct: bool,
) -> Iterator[Assignment]:
    for header in iter_fastq_headers(path, stats, decompress_threads):
        token, tags = parse_fastq_header_tags(header)
        if token.endswith("-CT"):
            stats["rad_ct_records_seen"] += 1
            if exclude_rad_ct:
                stats["rad_ct_records_excluded"] += 1
                continue
        target = normalize_barcode(tags.get("CB", ""))
        if not target:
            raise RuntimeError("RAD header lacks CB:Z: {}".format(header.rstrip()))
        read_id = RAD_SUFFIX.sub("", token)
        raw = tags.get("CR", "")
        strand = tags.get("TS", "")
        if raw:
            source = normalize_barcode(raw)
            if strand == "-":
                source = revcomp(source)
                stats["rad_reverse_raw_normalized_records"] += 1
            corrected_hint: Optional[bool] = True
            source_evidence = "RAD_CR"
        else:
            source = target
            corrected_hint = False
            source_evidence = "RAD_CB_native_when_CR_empty"
        yield Assignment(
            read_id=read_id,
            target=target,
            source=source,
            corrected_hint=corrected_hint,
            raw_quality=None,
            source_evidence=source_evidence,
        )
        stats["assignment_rows_yielded"] += 1
        if max_rows is not None and stats["assignment_rows_yielded"] >= max_rows:
            stats["truncated_by_max_rows"] = 1
            return


def parse_blaze_output_header(header: str) -> Tuple[str, str]:
    token, tags = parse_fastq_header_tags(header)
    if "#" not in token:
        raise RuntimeError("BLAZE output header lacks '#': {}".format(header.rstrip()))
    prefix, suffix = token.split("#", 1)
    read_id = suffix.rsplit("_", 1)[0] if "_" in suffix else suffix
    prefix_target = normalize_barcode(prefix.split("_", 1)[0])
    cb_target = normalize_barcode(tags.get("CB", ""))
    if not cb_target:
        raise RuntimeError(
            "BLAZE output header lacks CB:Z target: {}".format(header.rstrip())
        )
    if prefix_target != cb_target:
        raise RuntimeError(
            "BLAZE header target mismatch: prefix={} CB={} header={!r}".format(
                prefix_target, cb_target, header.rstrip()
            )
        )
    target = cb_target
    if not read_id or not target:
        raise RuntimeError("Could not parse BLAZE header: {}".format(header.rstrip()))
    if barcode_code(prefix_target) is None or barcode_code(target) is None:
        raise RuntimeError(
            "BLAZE header contains an invalid 16-nt target: {}".format(
                header.rstrip()
            )
        )
    return read_id, target


def iter_blaze(
    output_fastq: Path,
    putative_csv: Path,
    stats: Counter,
    decompress_threads: int,
    max_input_rows: Optional[int],
) -> Iterator[Assignment]:
    output_headers = iter_fastq_headers(output_fastq, stats, decompress_threads)

    def next_output() -> Optional[Tuple[str, str]]:
        try:
            parsed = parse_blaze_output_header(next(output_headers))
            stats["blaze_header_prefix_cb_consistent_records"] += 1
            return parsed
        except StopIteration:
            return None

    current = next_output()
    with open_text(putative_csv, decompress_threads) as handle:
        reader = csv.DictReader(handle)
        required = {"read_id", "putative_bc"}
        if reader.fieldnames is None or not required <= set(reader.fieldnames):
            raise RuntimeError(
                "BLAZE putative table requires {}; observed {}".format(
                    sorted(required), reader.fieldnames
                )
            )
        for raw_row in reader:
            read_id = raw_row.get("read_id", "")
            if not read_id:
                raise RuntimeError("BLAZE putative row lacks read_id")
            stats["blaze_putative_rows"] += 1
            raw = normalize_barcode(raw_row.get("putative_bc", ""))
            quality_value: Optional[float]
            try:
                quality_value = float(raw_row.get("putative_bc_min_q", ""))
            except (TypeError, ValueError):
                quality_value = None
            matched = False
            while current is not None and current[0] == read_id:
                matched = True
                yield Assignment(
                    read_id=read_id,
                    target=current[1],
                    source=raw or None,
                    corrected_hint=None,
                    raw_quality=quality_value,
                    source_evidence="BLAZE_putative_bc_input_order_join",
                )
                stats["assignment_rows_yielded"] += 1
                current = next_output()
            if matched:
                stats["blaze_putative_rows_with_assignment"] += 1
            if (
                max_input_rows is not None
                and stats["blaze_putative_rows"] >= max_input_rows
            ):
                stats["truncated_by_max_rows"] = 1
                return
    if current is not None:
        raise RuntimeError(
            "BLAZE emitted FASTQ was not exhausted by the putative table; "
            "next output read ID is {}".format(current[0])
        )
    stats["blaze_join_exhaustive"] = 1


def find_field(fieldnames: Sequence[str], candidates: Sequence[str]) -> Optional[str]:
    by_lower = {name.lower(): name for name in fieldnames}
    for candidate in candidates:
        if candidate.lower() in by_lower:
            return by_lower[candidate.lower()]
    return None


def iter_flexiplex(
    assignment_table: Path,
    stats: Counter,
    decompress_threads: int,
    max_rows: Optional[int],
) -> Iterator[Assignment]:
    with open_text(assignment_table, decompress_threads) as handle:
        first = handle.readline()
        if not first:
            raise RuntimeError("Empty Flexiplex assignment table {}".format(assignment_table))
        delimiter = "\t" if "\t" in first else ","
        reader = csv.DictReader(
            itertools_chain([first], handle), delimiter=delimiter
        )
        if reader.fieldnames is None:
            raise RuntimeError("Flexiplex assignment table has no header")
        read_field = find_field(reader.fieldnames, ("Read", "read_id", "read"))
        target_field = find_field(
            reader.fieldnames, ("CellBarcode", "CB", "target_barcode")
        )
        raw_field = find_field(
            reader.fieldnames,
            ("RawCellBarcode", "RawBarcode", "raw_barcode", "CR"),
        )
        edit_field = find_field(
            reader.fieldnames, ("BarcodeEditDist", "barcode_edit_distance")
        )
        if read_field is None or target_field is None:
            raise RuntimeError(
                "Flexiplex table needs read/target fields; observed {}".format(
                    reader.fieldnames
                )
            )
        stats["flexiplex_has_raw_source_column"] = int(raw_field is not None)
        stats["flexiplex_has_edit_distance_column"] = int(edit_field is not None)
        for row in reader:
            read_id = row.get(read_field, "")
            target = normalize_barcode(row.get(target_field, ""))
            if not read_id or not target:
                raise RuntimeError("Invalid Flexiplex assignment row: {}".format(row))
            edit_distance: Optional[int] = None
            if edit_field is not None and row.get(edit_field, "") != "":
                try:
                    edit_distance = int(row[edit_field])
                except ValueError as error:
                    raise RuntimeError(
                        "Invalid Flexiplex barcode edit distance: {}".format(row)
                    ) from error
            raw_value = normalize_barcode(row.get(raw_field, "")) if raw_field else ""
            if raw_value:
                source: Optional[str] = raw_value
                source_evidence = "Flexiplex_RawCellBarcode"
                stats["flexiplex_rows_with_exact_raw_source"] += 1
            else:
                source = None
                source_evidence = "Flexiplex_raw_source_unavailable"
                stats["flexiplex_rows_raw_source_unavailable"] += 1
                if edit_distance == 0:
                    stats[
                        "flexiplex_edit_distance_zero_raw_source_unavailable"
                    ] += 1
            corrected_hint = (
                edit_distance > 0 if edit_distance is not None else None
            )
            yield Assignment(
                read_id=read_id,
                target=target,
                source=source,
                corrected_hint=corrected_hint,
                raw_quality=None,
                source_evidence=source_evidence,
            )
            stats["assignment_rows_yielded"] += 1
            if max_rows is not None and stats["assignment_rows_yielded"] >= max_rows:
                stats["truncated_by_max_rows"] = 1
                return


def itertools_chain(first: Iterable[str], second: Iterable[str]) -> Iterator[str]:
    for value in first:
        yield value
    for value in second:
        yield value


class GroupingVerifier:
    """Disk-backed proof that each physical read appears in one contiguous group."""

    def __init__(
        self,
        out_dir: Path,
        mode: str,
        database_dir: Optional[Path] = None,
    ) -> None:
        self.mode = mode
        self.path: Optional[Path] = None
        self.connection: Optional[sqlite3.Connection] = None
        self.pending = 0
        self.reentries = 0
        if mode == "sqlite":
            temporary_dir = database_dir or out_dir
            temporary_dir.mkdir(parents=True, exist_ok=True)
            temporary = tempfile.NamedTemporaryFile(
                prefix=".grouping_check.",
                suffix=".sqlite",
                dir=str(temporary_dir),
                delete=False,
            )
            temporary.close()
            self.path = Path(temporary.name)
            self.connection = sqlite3.connect(str(self.path))
            self.connection.execute("PRAGMA journal_mode=OFF")
            self.connection.execute("PRAGMA synchronous=OFF")
            self.connection.execute("PRAGMA temp_store=FILE")
            self.connection.execute(
                "CREATE TABLE seen_reads (read_id TEXT PRIMARY KEY) WITHOUT ROWID"
            )
            self.connection.execute("BEGIN")

    def observe(self, read_id: str) -> None:
        if self.connection is None:
            return
        try:
            self.connection.execute(
                "INSERT INTO seen_reads(read_id) VALUES (?)", (read_id,)
            )
        except sqlite3.IntegrityError as error:
            self.reentries += 1
            raise RuntimeError(
                "Physical read ID re-entered after its group ended: {}".format(read_id)
            ) from error
        self.pending += 1
        if self.pending >= 100000:
            self.connection.commit()
            self.connection.execute("BEGIN")
            self.pending = 0

    def close(self) -> None:
        if self.connection is not None:
            self.connection.commit()
            self.connection.close()
            self.connection = None
        if self.path is not None and self.path.exists():
            self.path.unlink()


class Aggregator:
    def __init__(
        self,
        selected: Set[int],
        cellranger: Set[int],
        catalog: SortedCatalog,
        labels: Mapping[int, str],
        verifier: GroupingVerifier,
        out_dir: Path,
    ) -> None:
        self.selected = selected
        self.cellranger = cellranger
        self.catalog = catalog
        self.labels = labels
        self.verifier = verifier
        self.current_read: Optional[str] = None
        self.current_targets: Dict[str, UnitState] = {}
        self.assignment_rows = 0
        self.unique_physical_reads = 0
        self.multi_target_physical_reads = 0
        self.row_classes: Counter = Counter()
        self.unit_classes: Counter = Counter()
        self.unit_source_classes: Counter = Counter()
        self.read_classes: Counter = Counter()
        self.row_tiers: Counter = Counter()
        self.unit_tiers: Counter = Counter()
        self.target_rows: Dict[str, Counter] = defaultdict(Counter)
        self.target_units: Dict[str, Counter] = defaultdict(Counter)
        self.source_rows: Dict[str, Counter] = defaultdict(Counter)
        self.source_units: Dict[str, Counter] = defaultdict(Counter)
        self.source_reads: Dict[str, Counter] = defaultdict(Counter)
        self.pair_rows: Counter = Counter()
        self.pair_unit_sources: Counter = Counter()
        self.target_source_rows: Counter = Counter()
        self.target_source_unit_sources: Counter = Counter()
        self.class_quality_rows: Counter = Counter()
        self.source_evidence_rows: Counter = Counter()
        self.strict_event_count = 0
        self.strict_event_path = out_dir / "strict_cellranger_redirect_events.tsv.gz"
        self.strict_event_handle: Optional[TextIO] = gzip.open(
            self.strict_event_path, "wt", newline=""
        )
        self.strict_event_writer: Optional[csv.writer] = csv.writer(
            self.strict_event_handle, delimiter="\t", lineterminator="\n"
        )
        self.strict_event_writer.writerow(
            [
                "physical_read_id",
                "source_cellranger_barcode_A",
                "target_cellranger_barcode_B",
                "source_consensus_label",
                "target_consensus_label",
                "consensus_relation",
                "source_evidence",
                "assignment_records",
                "raw_quality_tiers",
                "minimum_raw_quality",
                "maximum_raw_quality",
                "read_target_has_multiple_exact_sources",
                "membership_classes",
            ]
        )

    def classify(self, assignment: Assignment) -> Classified:
        target = normalize_barcode(assignment.target)
        source = (
            normalize_barcode(assignment.source)
            if assignment.source is not None
            else None
        )
        assignment.target = target
        assignment.source = source
        target_code = barcode_code(target)
        source_code = barcode_code(source) if source is not None else None
        flags: Set[str] = {"all_assignments"}
        target_selected = target_code is not None and target_code in self.selected
        if target_code is None:
            flags.add("target_invalid_barcode")
        if not target_selected:
            flags.add("target_outside_selected")

        if source is None:
            flags.add("raw_source_unavailable")
            if assignment.corrected_hint is True:
                flags.add("all_corrected")
            else:
                flags.add("correction_state_unknown")
        elif source == target:
            flags.add("native_exact")
            if assignment.corrected_hint is True:
                flags.add("correction_hint_conflict")
        else:
            flags.add("all_corrected")
            if assignment.corrected_hint is False:
                flags.add("correction_hint_conflict")
            # Memberships are intentionally non-exclusive.  In particular, an
            # exact filtered source can also be selected by the tool; that
            # invariant violation must not hide the strict filtered A != B
            # barcode-flow classes.
            if target_selected and source_code in self.selected:
                flags.add("selected_source_changed")
            if target_selected and source_code in self.cellranger:
                flags.add("missed_cellranger_to_selected")
                if target_code in self.cellranger:
                    flags.add("cellranger_to_different_cellranger")
                    source_label = self.labels.get(source_code)
                    target_label = self.labels.get(target_code)
                    if source_label is not None and target_label is not None:
                        if source_label != target_label:
                            flags.add("consensus_cross_line")
                        else:
                            flags.add("consensus_same_line_different_cell")
                    else:
                        flags.add("consensus_label_incomplete")
                else:
                    flags.add("cellranger_to_noncellranger_selected")
            elif target_selected and source_code in self.catalog:
                flags.add("catalog_noncell_to_selected")
            elif target_selected:
                flags.add("noncatalog_to_selected")

        target_label = self.labels.get(target_code) if target_code is not None else None
        source_label = self.labels.get(source_code) if source_code is not None else None
        tier = evidence_tier(flags)
        return Classified(
            assignment=assignment,
            flags=flags,
            tier=tier,
            target_code=target_code,
            source_code=source_code,
            target_label=target_label,
            source_label=source_label,
            quality_tier=quality_tier(assignment.raw_quality),
        )

    def consume(self, assignment: Assignment) -> None:
        if not assignment.read_id:
            raise RuntimeError("Assignment has an empty physical read ID")
        if assignment.read_id != self.current_read:
            self.flush_read()
            self.current_read = assignment.read_id
            self.verifier.observe(assignment.read_id)
        classified = self.classify(assignment)
        self.assignment_rows += 1
        self.source_evidence_rows[assignment.source_evidence] += 1
        for flag in classified.flags:
            self.row_classes[flag] += 1
            self.target_rows[assignment.target][flag] += 1
            self.class_quality_rows[(flag, classified.quality_tier)] += 1
            if (
                classified.source_code is not None
                and classified.source_code in self.cellranger
                and assignment.source is not None
            ):
                self.source_rows[assignment.source][flag] += 1
        self.row_tiers[classified.tier] += 1

        relationship, source_label, target_label = source_relationship(classified)
        label_key = (
            assignment.target,
            source_label,
            target_label,
            relationship,
        )
        self.target_source_rows[label_key] += 1

        if (
            assignment.source is not None
            and assignment.source != assignment.target
            and "missed_cellranger_to_selected" in classified.flags
        ):
            self.pair_rows[(assignment.source, assignment.target)] += 1

        unit = self.current_targets.get(assignment.target)
        if unit is None:
            unit = UnitState(
                target=assignment.target,
                target_code=classified.target_code,
            )
            self.current_targets[assignment.target] = unit
        unit.rows += 1
        unit.flags.update(classified.flags)
        source_key = assignment.source if assignment.source is not None else "<UNAVAILABLE>"
        state = unit.sources.get(source_key)
        if state is None:
            state = SourceState(
                source_code=classified.source_code,
                source=assignment.source,
                source_label=classified.source_label,
                target_label=classified.target_label,
            )
            unit.sources[source_key] = state
        state.rows += 1
        state.flags.update(classified.flags)
        state.source_evidence.add(assignment.source_evidence)
        state.quality_tiers.add(classified.quality_tier)
        if assignment.raw_quality is not None and not math.isnan(
            assignment.raw_quality
        ):
            if (
                state.minimum_raw_quality is None
                or assignment.raw_quality < state.minimum_raw_quality
            ):
                state.minimum_raw_quality = assignment.raw_quality
            if (
                state.maximum_raw_quality is None
                or assignment.raw_quality > state.maximum_raw_quality
            ):
                state.maximum_raw_quality = assignment.raw_quality

    def flush_read(self) -> None:
        if self.current_read is None:
            return
        self.unique_physical_reads += 1
        if len(self.current_targets) > 1:
            self.multi_target_physical_reads += 1
        read_flags: Set[str] = set()
        source_read_flags: Dict[str, Set[str]] = defaultdict(set)
        for target, unit in self.current_targets.items():
            exact_sources = {
                state.source
                for state in unit.sources.values()
                if state.source is not None
            }
            if len(exact_sources) > 1:
                unit.flags.add("multiple_exact_sources")
            unit_tier = evidence_tier(unit.flags)
            for flag in unit.flags:
                self.unit_classes[flag] += 1
                self.target_units[target][flag] += 1
            read_flags.update(unit.flags)
            self.unit_tiers[unit_tier] += 1

            for state in unit.sources.values():
                for flag in state.flags:
                    self.unit_source_classes[flag] += 1
                    if (
                        state.source_code is not None
                        and state.source_code in self.cellranger
                        and state.source is not None
                    ):
                        self.source_units[state.source][flag] += 1
                        source_read_flags[state.source].add(flag)
                source_assignment = Assignment(
                    read_id=self.current_read,
                    target=target,
                    source=state.source,
                    corrected_hint=None,
                    raw_quality=None,
                    source_evidence="unit_source",
                )
                source_classified = Classified(
                    assignment=source_assignment,
                    flags=state.flags,
                    tier=evidence_tier(state.flags),
                    target_code=unit.target_code,
                    source_code=state.source_code,
                    target_label=state.target_label,
                    source_label=state.source_label,
                    quality_tier="quality_not_aggregated",
                )
                relationship, source_label, target_label = source_relationship(
                    source_classified
                )
                label_key = (target, source_label, target_label, relationship)
                self.target_source_unit_sources[label_key] += 1
                if (
                    state.source is not None
                    and state.source != target
                    and "missed_cellranger_to_selected" in state.flags
                ):
                    self.pair_unit_sources[(state.source, target)] += 1
                if (
                    state.source is not None
                    and state.source != target
                    and "cellranger_to_different_cellranger" in state.flags
                ):
                    if state.source_label is not None and state.target_label is not None:
                        consensus_relation = (
                            "cross_line"
                            if state.source_label != state.target_label
                            else "same_line_different_cell"
                        )
                    else:
                        consensus_relation = "label_incomplete"
                    if self.strict_event_writer is None:
                        raise RuntimeError("Strict-event writer was closed too early")
                    self.strict_event_writer.writerow(
                        [
                            self.current_read,
                            state.source,
                            target,
                            state.source_label or "UNLABELED",
                            state.target_label or "UNLABELED",
                            consensus_relation,
                            ",".join(sorted(state.source_evidence)),
                            state.rows,
                            ",".join(sorted(state.quality_tiers)),
                            format_number(state.minimum_raw_quality)
                            if state.minimum_raw_quality is not None
                            else "NA",
                            format_number(state.maximum_raw_quality)
                            if state.maximum_raw_quality is not None
                            else "NA",
                            int(len(exact_sources) > 1),
                            ",".join(sorted(state.flags)),
                        ]
                    )
                    self.strict_event_count += 1
        for flag in read_flags:
            self.read_classes[flag] += 1
        for source, flags in source_read_flags.items():
            for flag in flags:
                self.source_reads[source][flag] += 1
        self.current_targets = {}

    def finish(self) -> None:
        self.flush_read()
        self.current_read = None
        self.close()

    def close(self) -> None:
        if self.strict_event_handle is not None:
            self.strict_event_handle.close()
            self.strict_event_handle = None
            self.strict_event_writer = None


def format_number(value: object) -> object:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return "NA"
        return "{:.12g}".format(value)
    return value


def ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else float("nan")


def excess(numerator: int, total: int) -> float:
    return ratio(numerator, total - numerator)


def write_tsv(path: Path, header: Sequence[str], rows: Iterable[Sequence[object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        for row in rows:
            writer.writerow([format_number(value) for value in row])


def invariant_row(
    name: str,
    passed: Optional[bool],
    observed: object,
    expected: object,
    note: str,
) -> Tuple[object, ...]:
    status = "NOT_CHECKED" if passed is None else ("PASS" if passed else "FAIL")
    return (name, status, observed, expected, note)


def write_outputs(
    args: argparse.Namespace,
    aggregate: Aggregator,
    selected_stats: Mapping[str, int],
    cellranger_stats: Mapping[str, int],
    catalog: SortedCatalog,
    label_stats: Mapping[str, object],
    adapter_stats: Counter,
    started_utc: str,
) -> List[Tuple[object, ...]]:
    out_dir: Path = args.outdir
    out_dir.mkdir(parents=True, exist_ok=True)
    o_value = aggregate.unit_classes["all_assignments"]
    k_value = aggregate.unit_classes["cellranger_to_different_cellranger"]
    x_value = aggregate.unit_classes["consensus_cross_line"]
    a_value = aggregate.unit_classes["catalog_noncell_to_selected"]
    summary_header = [
        "dataset",
        "tool",
        "scope",
        "assignment_records",
        "unique_physical_reads",
        "multi_target_physical_reads",
        "unique_read_target_assignments_O",
        "native_exact",
        "all_corrected",
        "selected_source_changed",
        "missed_cellranger_to_selected",
        "cellranger_to_different_cellranger_K",
        "consensus_cross_line_X",
        "consensus_same_line_different_cell",
        "consensus_label_incomplete",
        "catalog_noncell_to_selected_A",
        "noncatalog_to_selected",
        "raw_source_unavailable",
        "K_over_O",
        "X_over_O",
        "K_plus_A_over_O",
        "X_excess_over_guarded",
        "K_excess_over_guarded",
        "K_plus_A_excess_over_guarded",
    ]
    summary_row = [
        args.dataset,
        args.tool,
        "truncated_prefix" if adapter_stats["truncated_by_max_rows"] else "complete_input",
        aggregate.assignment_rows,
        aggregate.unique_physical_reads,
        aggregate.multi_target_physical_reads,
        o_value,
        aggregate.unit_classes["native_exact"],
        aggregate.unit_classes["all_corrected"],
        aggregate.unit_classes["selected_source_changed"],
        aggregate.unit_classes["missed_cellranger_to_selected"],
        k_value,
        x_value,
        aggregate.unit_classes["consensus_same_line_different_cell"],
        aggregate.unit_classes["consensus_label_incomplete"],
        a_value,
        aggregate.unit_classes["noncatalog_to_selected"],
        aggregate.unit_classes["raw_source_unavailable"],
        ratio(k_value, o_value),
        ratio(x_value, o_value),
        ratio(k_value + a_value, o_value),
        excess(x_value, o_value),
        excess(k_value, o_value),
        excess(k_value + a_value, o_value),
    ]
    write_tsv(out_dir / "summary.tsv", summary_header, [summary_row])

    write_tsv(
        out_dir / "class_summary.tsv",
        [
            "class",
            "assignment_records",
            "unique_physical_reads",
            "unique_read_target_assignments",
            "unique_read_target_source_assignments",
        ],
        (
            (
                name,
                aggregate.row_classes[name],
                aggregate.read_classes[name],
                aggregate.unit_classes[name],
                aggregate.unit_source_classes[name],
            )
            for name in CLASS_NAMES
        ),
    )

    tiers = sorted(set(aggregate.row_tiers) | set(aggregate.unit_tiers))
    write_tsv(
        out_dir / "evidence_tier_summary.tsv",
        [
            "evidence_tier",
            "assignment_records",
            "unique_read_target_assignments",
        ],
        (
            (
                tier,
                aggregate.row_tiers[tier],
                aggregate.unit_tiers[tier],
            )
            for tier in tiers
        ),
    )

    all_target_codes = sorted(aggregate.selected)
    per_target_rows: List[List[object]] = []
    for target_code in all_target_codes:
        target = code_barcode(target_code)
        counters = aggregate.target_units[target]
        row_counters = aggregate.target_rows[target]
        o_target = counters["all_assignments"]
        k_target = counters["cellranger_to_different_cellranger"]
        x_target = counters["consensus_cross_line"]
        a_target = counters["catalog_noncell_to_selected"]
        per_target_rows.append(
            [
                target,
                aggregate.labels.get(target_code, "UNLABELED"),
                row_counters["all_assignments"],
                o_target,
                counters["native_exact"],
                counters["all_corrected"],
                counters["missed_cellranger_to_selected"],
                k_target,
                counters["consensus_same_line_different_cell"],
                x_target,
                counters["consensus_label_incomplete"],
                a_target,
                counters["noncatalog_to_selected"],
                counters["raw_source_unavailable"],
                ratio(k_target, o_target),
                ratio(x_target, o_target),
                ratio(k_target + a_target, o_target),
                excess(x_target, o_target),
                excess(k_target, o_target),
                excess(k_target + a_target, o_target),
            ]
        )
    write_tsv(
        out_dir / "per_target.tsv",
        [
            "target_barcode",
            "target_consensus_label",
            "assignment_records",
            "unique_read_target_assignments_O",
            "native_exact",
            "all_corrected",
            "missed_cellranger_to_selected",
            "cellranger_to_different_cellranger_K",
            "consensus_same_line_different_cell",
            "consensus_cross_line_X",
            "consensus_label_incomplete",
            "catalog_noncell_to_selected_A",
            "noncatalog_to_selected",
            "raw_source_unavailable",
            "K_over_O",
            "X_over_O",
            "K_plus_A_over_O",
            "X_excess_over_guarded",
            "K_excess_over_guarded",
            "K_plus_A_excess_over_guarded",
        ],
        per_target_rows,
    )

    per_source_rows: List[List[object]] = []
    for source_code in sorted(aggregate.cellranger):
        source = code_barcode(source_code)
        row_counters = aggregate.source_rows[source]
        read_counters = aggregate.source_reads[source]
        unit_counters = aggregate.source_units[source]
        source_units = unit_counters["all_assignments"]
        k_source = unit_counters["cellranger_to_different_cellranger"]
        x_source = unit_counters["consensus_cross_line"]
        per_source_rows.append(
            [
                source,
                aggregate.labels.get(source_code, "UNLABELED"),
                int(source_code in aggregate.selected),
                row_counters["all_assignments"],
                read_counters["all_assignments"],
                source_units,
                unit_counters["native_exact"],
                unit_counters["all_corrected"],
                unit_counters["selected_source_changed"],
                unit_counters["missed_cellranger_to_selected"],
                k_source,
                x_source,
                unit_counters["consensus_same_line_different_cell"],
                unit_counters["consensus_label_incomplete"],
                unit_counters["cellranger_to_noncellranger_selected"],
                ratio(k_source, source_units),
                ratio(x_source, source_units),
            ]
        )
    write_tsv(
        out_dir / "per_source.tsv",
        [
            "source_cellranger_barcode",
            "source_consensus_label",
            "source_in_selected_whitelist",
            "assignment_records",
            "unique_physical_reads",
            "unique_read_target_source_assignments",
            "native_exact",
            "all_corrected",
            "selected_source_changed",
            "cellranger_source_to_selected",
            "cellranger_to_different_cellranger_K",
            "consensus_cross_line_X",
            "consensus_same_line_different_cell",
            "consensus_label_incomplete",
            "cellranger_to_noncellranger_selected",
            "K_over_source_assignments",
            "X_over_source_assignments",
        ],
        per_source_rows,
    )

    pair_rows = []
    pair_keys = sorted(
        set(aggregate.pair_rows) | set(aggregate.pair_unit_sources),
        key=lambda key: (-aggregate.pair_rows[key], key[1], key[0]),
    )
    for source, target in pair_keys:
        source_code = barcode_code(source)
        target_code = barcode_code(target)
        source_label = (
            aggregate.labels.get(source_code, "UNLABELED")
            if source_code is not None
            else "UNLABELED"
        )
        target_label = (
            aggregate.labels.get(target_code, "UNLABELED")
            if target_code is not None
            else "UNLABELED"
        )
        if source_label != "UNLABELED" and target_label != "UNLABELED":
            label_relation = (
                "cross_line" if source_label != target_label else "same_line_different_cell"
            )
        else:
            label_relation = "label_incomplete"
        pair_rows.append(
            [
                source,
                target,
                source_label,
                target_label,
                label_relation,
                aggregate.pair_rows[(source, target)],
                aggregate.pair_unit_sources[(source, target)],
            ]
        )
    write_tsv(
        out_dir / "cellranger_source_target_pairs.tsv",
        [
            "source_cellranger_barcode",
            "target_selected_barcode",
            "source_consensus_label",
            "target_consensus_label",
            "consensus_relation",
            "assignment_records",
            "unique_read_target_source_assignments",
        ],
        pair_rows,
    )

    label_keys = sorted(
        set(aggregate.target_source_rows)
        | set(aggregate.target_source_unit_sources)
    )
    write_tsv(
        out_dir / "target_source_labels.tsv",
        [
            "target_barcode",
            "source_consensus_label",
            "target_consensus_label",
            "source_target_relation",
            "assignment_records",
            "unique_read_target_source_assignments",
        ],
        (
            (
                key[0],
                key[1],
                key[2],
                key[3],
                aggregate.target_source_rows[key],
                aggregate.target_source_unit_sources[key],
            )
            for key in label_keys
        ),
    )

    write_tsv(
        out_dir / "class_by_raw_quality.tsv",
        ["class", "raw_quality_tier", "assignment_records"],
        (
            (key[0], key[1], count)
            for key, count in sorted(aggregate.class_quality_rows.items())
        ),
    )
    write_tsv(
        out_dir / "source_evidence_summary.tsv",
        ["source_evidence", "assignment_records"],
        sorted(aggregate.source_evidence_rows.items()),
    )

    selected_outside_catalog = sum(code not in catalog for code in aggregate.selected)
    cellranger_outside_catalog = sum(
        code not in catalog for code in aggregate.cellranger
    )
    labels_outside_cellranger = sum(
        code not in aggregate.cellranger for code in aggregate.labels
    )
    target_row_k = sum(
        counter["cellranger_to_different_cellranger"]
        for counter in aggregate.target_rows.values()
    )
    target_unit_k = sum(
        counter["cellranger_to_different_cellranger"]
        for counter in aggregate.target_units.values()
    )
    pair_row_k = sum(aggregate.pair_rows.values())
    pair_unit_source_k = sum(aggregate.pair_unit_sources.values())
    source_row_k = sum(
        counter["cellranger_to_different_cellranger"]
        for counter in aggregate.source_rows.values()
    )
    source_unit_k = sum(
        counter["cellranger_to_different_cellranger"]
        for counter in aggregate.source_units.values()
    )
    invariants: List[Tuple[object, ...]] = [
        invariant_row(
            "all_emitted_targets_in_selected_whitelist",
            aggregate.row_classes["target_outside_selected"] == 0,
            aggregate.row_classes["target_outside_selected"],
            0,
            "Every output target must belong to the tool-selected whitelist.",
        ),
        invariant_row(
            "selected_source_never_changed",
            aggregate.row_classes["selected_source_changed"] == 0,
            aggregate.row_classes["selected_source_changed"],
            0,
            "An exact source already selected by the tool must remain unchanged.",
        ),
        invariant_row(
            "selected_whitelist_subset_global_catalog",
            selected_outside_catalog == 0,
            selected_outside_catalog,
            0,
            "Selected targets should be valid manufacturer-catalog barcodes.",
        ),
        invariant_row(
            "cellranger_filtered_subset_global_catalog",
            cellranger_outside_catalog == 0,
            cellranger_outside_catalog,
            0,
            "CellRanger filtered cells should be valid manufacturer barcodes.",
        ),
        invariant_row(
            "consensus_labels_subset_cellranger_filtered",
            labels_outside_cellranger == 0,
            labels_outside_cellranger,
            0,
            "Consensus donor/cell-line labels are only interpreted for filtered cells.",
        ),
        invariant_row(
            "unique_read_target_assignments_not_above_records",
            o_value <= aggregate.assignment_rows,
            o_value,
            "<={}".format(aggregate.assignment_rows),
            "The primary unique unit cannot exceed assignment-record rows.",
        ),
        invariant_row(
            "target_record_marginal_reproduces_K",
            target_row_k == aggregate.row_classes[
                "cellranger_to_different_cellranger"
            ],
            target_row_k,
            aggregate.row_classes["cellranger_to_different_cellranger"],
            "Per-target record counts must reproduce the global K count.",
        ),
        invariant_row(
            "target_unique_marginal_reproduces_K",
            target_unit_k == k_value,
            target_unit_k,
            k_value,
            "Per-target unique counts must reproduce the global K count.",
        ),
        invariant_row(
            "pair_record_marginal_reproduces_missed_cellranger",
            pair_row_k == aggregate.row_classes["missed_cellranger_to_selected"],
            pair_row_k,
            aggregate.row_classes["missed_cellranger_to_selected"],
            "CellRanger-source pair rows include targets both inside and outside CellRanger.",
        ),
        invariant_row(
            "pair_unique_source_marginal_matches_source_units_missed_cellranger",
            pair_unit_source_k
            == aggregate.unit_source_classes["missed_cellranger_to_selected"],
            pair_unit_source_k,
            aggregate.unit_source_classes["missed_cellranger_to_selected"],
            "The source-pair marginal uses read-target-source units, so multi-source read-target units are represented once per exact source.",
        ),
        invariant_row(
            "per_source_record_marginal_reproduces_K",
            source_row_k
            == aggregate.row_classes["cellranger_to_different_cellranger"],
            source_row_k,
            aggregate.row_classes["cellranger_to_different_cellranger"],
            "Every strict K record has one exact filtered source.",
        ),
        invariant_row(
            "per_source_unique_source_marginal_reproduces_K",
            source_unit_k
            == aggregate.unit_source_classes[
                "cellranger_to_different_cellranger"
            ],
            source_unit_k,
            aggregate.unit_source_classes[
                "cellranger_to_different_cellranger"
            ],
            "Per-source unique counts use read-target-source units and therefore preserve multi-source read-target units.",
        ),
        invariant_row(
            "strict_event_rows_reproduce_unique_source_K",
            aggregate.strict_event_count
            == aggregate.unit_source_classes[
                "cellranger_to_different_cellranger"
            ],
            aggregate.strict_event_count,
            aggregate.unit_source_classes[
                "cellranger_to_different_cellranger"
            ],
            "The compressed strict-event file contains one row per physical-read, exact-source-A, target-B triple.",
        ),
        invariant_row(
            "physical_read_K_not_above_read_target_K",
            aggregate.read_classes["cellranger_to_different_cellranger"]
            <= aggregate.unit_classes["cellranger_to_different_cellranger"],
            aggregate.read_classes["cellranger_to_different_cellranger"],
            "<={}".format(
                aggregate.unit_classes["cellranger_to_different_cellranger"]
            ),
            "A physical read is counted once even if it has multiple target or source units.",
        ),
        invariant_row(
            "read_target_K_not_above_read_target_source_K",
            aggregate.unit_classes["cellranger_to_different_cellranger"]
            <= aggregate.unit_source_classes[
                "cellranger_to_different_cellranger"
            ],
            aggregate.unit_classes["cellranger_to_different_cellranger"],
            "<={}".format(
                aggregate.unit_source_classes[
                    "cellranger_to_different_cellranger"
                ]
            ),
            "Multiple exact filtered sources can contribute to one read-target unit.",
        ),
        invariant_row(
            "blaze_header_prefix_matches_CB",
            (
                adapter_stats["blaze_header_prefix_cb_consistent_records"]
                == adapter_stats["fastq_records_read"]
                if args.tool == "blaze"
                else None
            ),
            (
                adapter_stats["blaze_header_prefix_cb_consistent_records"]
                if args.tool == "blaze"
                else "NOT_APPLICABLE"
            ),
            (
                adapter_stats["fastq_records_read"]
                if args.tool == "blaze"
                else "NOT_APPLICABLE"
            ),
            "Every BLAZE emitted record was required to have identical header-prefix and CB targets.",
        ),
        invariant_row(
            "physical_read_grouping_nonreentry",
            True if args.grouping_check == "sqlite" else None,
            aggregate.verifier.reentries,
            0,
            (
                "Disk-backed read-ID grouping proof completed."
                if args.grouping_check == "sqlite"
                else "Not checked; exact uniqueness assumes contiguous per-read output groups."
            ),
        ),
    ]
    write_tsv(
        out_dir / "invariants.tsv",
        ["invariant", "status", "observed", "expected", "note"],
        invariants,
    )

    metadata = {
        "analysis_model": "LongBench barcode-flow and contamination model",
        "dataset": args.dataset,
        "tool": args.tool,
        "started_utc": started_utc,
        "finished_utc": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "primary_unit": "(physical_read_id,target_barcode)",
        "source_resolved_unit": "(physical_read_id,target_barcode,exact_source_barcode)",
        "per_class_unique_physical_read_counts": True,
        "strict_individual_events": {
            "path": str(aggregate.strict_event_path),
            "rows": aggregate.strict_event_count,
            "unit": "(physical_read_id,source_cellranger_barcode_A,target_cellranger_barcode_B)",
        },
        "assignment_record_totals_retained": True,
        "grouping_check": args.grouping_check,
        "grouping_db_dir": str(args.grouping_db_dir)
        if args.grouping_db_dir is not None
        else str(args.outdir),
        "max_rows": args.max_rows,
        "max_input_rows": args.max_input_rows,
        "decompress_threads": args.decompress_threads,
        "exclude_rad_ct": args.exclude_rad_ct,
        "inputs": {
            "assignments": path_metadata(args.assignments),
            "putative_csv": path_metadata(args.putative_csv),
            "selected_whitelist": path_metadata(
                args.selected_whitelist, include_hash=True
            ),
            "cellranger_filtered": path_metadata(
                args.cellranger_filtered, include_hash=True
            ),
            "global_catalog": path_metadata(args.global_catalog, include_hash=True),
            "label_dir": str(args.label_dir) if args.label_dir else None,
        },
        "reference_stats": {
            "selected": dict(selected_stats),
            "cellranger_filtered": dict(cellranger_stats),
            "global_catalog": {
                "nonempty_rows": catalog.rows,
                "valid_unique_barcodes": len(catalog),
                "invalid_rows": catalog.invalid_rows,
                "duplicate_rows": catalog.duplicate_rows,
                "compact_array_bytes": len(catalog.codes) * catalog.codes.itemsize,
                "loaded_from_cache": catalog.loaded_from_cache,
                "cache_path": str(args.catalog_cache)
                if args.catalog_cache is not None
                else None,
            },
            "labels": dict(label_stats),
        },
        "adapter_stats": dict(adapter_stats),
        "interpretation_boundaries": [
            "Barcode membership classes are non-exclusive; selected-source changes remain strict filtered A-to-B events when both endpoints are filtered cells.",
            "Consensus cross-line requires exact filtered source and target barcodes with different majority-consensus labels.",
            "Catalog-valid CellRanger-unfiltered redirects are operational non-cell/ambient-compatible evidence, not donor attribution.",
            "Unlabeled filtered barcodes remain label-incomplete and are not assigned a donor or cell line.",
            "Flexiplex edit distance alone never reconstructs an exact raw source; rows without RawCellBarcode are source-unavailable even at edit distance zero.",
            "Exact barcode membership is barcode-flow evidence, not molecule-level biological ground truth.",
        ],
    }
    with (out_dir / "run_metadata.json").open("w") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return invariants


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stream RAD/BLAZE/Flexiplex correction events into LongBench metrics."
    )
    parser.add_argument("--tool", choices=("rad", "blaze", "flexiplex"), required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument(
        "--assignments",
        type=Path,
        required=True,
        help="RAD/BLAZE FASTQ or Flexiplex assignment TSV.",
    )
    parser.add_argument(
        "--putative-csv",
        type=Path,
        help="BLAZE putative_bc.csv; required with --tool blaze.",
    )
    parser.add_argument("--selected-whitelist", type=Path, required=True)
    parser.add_argument("--cellranger-filtered", type=Path, required=True)
    parser.add_argument("--global-catalog", type=Path, required=True)
    parser.add_argument(
        "--catalog-cache",
        type=Path,
        help="Reusable compact uint32 catalog cache; validated against source path/size/mtime.",
    )
    parser.add_argument(
        "--label-dir",
        type=Path,
        help="LongBench merged_annotation/{sc,sn} directory of *_BC_list.txt files.",
    )
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument(
        "--grouping-check",
        choices=("sqlite", "assume"),
        default="sqlite",
        help="Default sqlite proves no physical read ID re-enters non-contiguously.",
    )
    parser.add_argument(
        "--grouping-db-dir",
        type=Path,
        help="Directory for the temporary grouping SQLite DB; local scratch avoids NFS metadata latency.",
    )
    parser.add_argument("--decompress-threads", type=int, default=1)
    parser.add_argument(
        "--max-rows",
        type=int,
        help="Stop after this many RAD/Flexiplex assignment rows (validation only).",
    )
    parser.add_argument(
        "--max-input-rows",
        type=int,
        help="Stop after this many BLAZE putative/input rows (validation only).",
    )
    parser.add_argument(
        "--allow-invariant-failures",
        action="store_true",
        help="Write results and return success even if a required invariant fails.",
    )
    parser.add_argument(
        "--exclude-rad-ct",
        action="store_true",
        help=(
            "Exclude RAD records whose read token ends in -F-CT or -R-CT. "
            "RAD marks concatenate/chimeric-derived records this way."
        ),
    )
    args = parser.parse_args()
    if args.tool == "blaze" and args.putative_csv is None:
        parser.error("--putative-csv is required with --tool blaze")
    if args.tool != "blaze" and args.putative_csv is not None:
        parser.error("--putative-csv is only valid with --tool blaze")
    if args.decompress_threads < 1:
        parser.error("--decompress-threads must be positive")
    if args.max_rows is not None and args.tool == "blaze":
        parser.error("Use --max-input-rows, not --max-rows, for BLAZE")
    if args.max_input_rows is not None and args.tool != "blaze":
        parser.error("--max-input-rows is only valid with BLAZE")
    if args.exclude_rad_ct and args.tool != "rad":
        parser.error("--exclude-rad-ct is only valid with RAD")
    return args


def main() -> int:
    args = parse_args()
    for path in (
        args.assignments,
        args.selected_whitelist,
        args.cellranger_filtered,
        args.global_catalog,
    ):
        if not path.exists() or not path.is_file():
            raise RuntimeError("Required input is missing: {}".format(path))
    if args.putative_csv is not None and not args.putative_csv.is_file():
        raise RuntimeError("Required BLAZE putative table is missing: {}".format(args.putative_csv))
    if args.label_dir is not None and not args.label_dir.is_dir():
        raise RuntimeError("Label directory is missing: {}".format(args.label_dir))
    args.outdir.mkdir(parents=True, exist_ok=True)
    started_utc = __import__("datetime").datetime.now(
        __import__("datetime").timezone.utc
    ).isoformat()

    selected, selected_stats = load_barcode_set(args.selected_whitelist)
    cellranger, cellranger_stats = load_barcode_set(args.cellranger_filtered)
    catalog = SortedCatalog(args.global_catalog, args.catalog_cache)
    labels, label_stats = load_labels(args.label_dir)
    adapter_stats: Counter = Counter()
    verifier = GroupingVerifier(
        args.outdir,
        args.grouping_check,
        args.grouping_db_dir,
    )
    aggregate = Aggregator(
        selected,
        cellranger,
        catalog,
        labels,
        verifier,
        args.outdir,
    )
    try:
        if args.tool == "rad":
            assignments = iter_rad(
                args.assignments,
                adapter_stats,
                args.decompress_threads,
                args.max_rows,
                args.exclude_rad_ct,
            )
        elif args.tool == "blaze":
            assert args.putative_csv is not None
            assignments = iter_blaze(
                args.assignments,
                args.putative_csv,
                adapter_stats,
                args.decompress_threads,
                args.max_input_rows,
            )
        else:
            assignments = iter_flexiplex(
                args.assignments,
                adapter_stats,
                args.decompress_threads,
                args.max_rows,
            )
        for assignment in assignments:
            aggregate.consume(assignment)
        aggregate.finish()
        invariants = write_outputs(
            args,
            aggregate,
            selected_stats,
            cellranger_stats,
            catalog,
            label_stats,
            adapter_stats,
            started_utc,
        )
    finally:
        aggregate.close()
        verifier.close()
    failed = [row for row in invariants if row[1] == "FAIL"]
    print(
        json.dumps(
            {
                "dataset": args.dataset,
                "tool": args.tool,
                "assignment_records": aggregate.assignment_rows,
                "unique_physical_reads": aggregate.unique_physical_reads,
                "unique_read_target_assignments": aggregate.unit_classes[
                    "all_assignments"
                ],
                "failed_invariants": [row[0] for row in failed],
                "outdir": str(args.outdir),
            },
            sort_keys=True,
        )
    )
    if failed and not args.allow_invariant_failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
