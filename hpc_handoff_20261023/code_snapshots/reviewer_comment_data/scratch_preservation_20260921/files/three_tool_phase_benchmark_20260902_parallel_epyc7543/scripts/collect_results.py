#!/usr/bin/env python3
"""Collect the three-tool phase benchmark into fixed-shape wide CSV files.

The benchmark runner writes attempt-specific records below::

    RUN_ROOT/raw/{SN_ONT,SC_PB}/threads_{4,16,64}/rep_{1,2,3}/
      {RAD,Flexiplex,BLAZE}/{whitelist_detection,demultiplexing}/attempt_NNN/

Only attempts with a valid zero-exit GNU_TIME_V1 record, the required sidecar
files, and a COMPLETE marker are eligible.  If more than one attempt is
eligible, the highest numbered attempt supplies the wide table and every
attempt remains represented in the provenance table.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple


RAW_TO_DISPLAY_DATASET: Mapping[str, str] = {
    "SN_ONT": "SN-ONT",
    "SC_PB": "SC-PB",
}
DISPLAY_DATASETS: Tuple[str, ...] = tuple(RAW_TO_DISPLAY_DATASET.values())
THREADS: Tuple[int, ...] = (4, 16, 64)
REPLICATES: Tuple[int, ...] = (1, 2, 3)
TOOLS: Tuple[str, ...] = ("RAD", "Flexiplex", "BLAZE")
PHASES: Tuple[str, ...] = ("whitelist_detection", "demultiplexing")
EXPECTED_PHASE_KEYS = (
    len(DISPLAY_DATASETS) * len(THREADS) * len(REPLICATES) * len(TOOLS) * len(PHASES)
)

TIME_TAG = "GNU_TIME_V1"
TIME_REQUIRED_FIELDS: Tuple[str, ...] = (
    "user_seconds",
    "system_seconds",
    "elapsed_seconds",
    "max_rss_kib",
    "exit_status",
)
ATTEMPT_RE = re.compile(r"^attempt_(\d+)$")

WIDE_COLUMNS: Tuple[str, ...] = ("threads",) + tuple(
    f"{tool}_rep_{replicate}" for tool in TOOLS for replicate in REPLICATES
)

RSS_WIDE_METRICS: Tuple[str, ...] = (
    "selected_max_rss_kib",
    "gnu_time_max_rss_kib",
    "process_tree_peak_total_rss_kib",
)
RSS_WIDE_COLUMNS: Tuple[str, ...] = ("threads",) + tuple(
    f"{metric}__{tool}_rep_{replicate}"
    for metric in RSS_WIDE_METRICS
    for tool in TOOLS
    for replicate in REPLICATES
)

LONG_COLUMNS: Tuple[str, ...] = (
    "dataset",
    "raw_dataset",
    "phase",
    "tool",
    "threads",
    "replicate",
    "attempt",
    "attempt_dir",
    "accepted_pointer_path",
    "accepted_pointer_value",
    "expected_key",
    "accepted",
    "record_status",
    "complete_marker",
    "user_seconds",
    "system_seconds",
    "cpu_seconds",
    "elapsed_seconds",
    "observed_mean_cores",
    "gnu_time_max_rss_kib",
    "process_tree_peak_total_rss_kib",
    "process_tree_peak_elapsed_seconds",
    "process_tree_peak_process_count",
    "process_tree_peak_timestamp_utc",
    "process_tree_sample_count",
    "process_tree_totals_path",
    "selected_max_rss_kib",
    "selected_max_rss_source",
    "exit_status",
    "metrics_path",
    "metrics_sha256",
    "metrics_extra_json",
    "component_discovery_user_seconds",
    "component_discovery_system_seconds",
    "component_discovery_cpu_seconds",
    "component_discovery_elapsed_seconds",
    "component_discovery_max_rss_kib",
    "component_discovery_exit_status",
    "component_discovery_metrics_path",
    "component_filter_user_seconds",
    "component_filter_system_seconds",
    "component_filter_cpu_seconds",
    "component_filter_elapsed_seconds",
    "component_filter_max_rss_kib",
    "component_filter_exit_status",
    "component_filter_metrics_path",
    "status_path",
    "status_metadata_json",
    "run_metadata_path",
    "run_metadata_json",
    "hostname",
    "cpu_model",
    "slurm_job_id",
    "slurm_cpus_per_task",
    "input_fastq",
    "input_size_bytes",
    "input_sha256_preverified",
    "expected_reads",
    "command_path",
    "command_sha256",
    "command",
    "stdout_path",
    "stderr_path",
    "whitelist_metadata_path",
    "whitelist_metadata_sha256",
    "whitelist_metadata_json",
    "whitelist_rows_nonempty",
    "whitelist_sha256",
    "output_metadata_path",
    "output_metadata_json",
    "warnings",
)


class RecordError(ValueError):
    """Raised when a raw timing record is missing or malformed."""


@dataclass(frozen=True)
class TimingMetrics:
    user_seconds: Decimal
    system_seconds: Decimal
    elapsed_seconds: Decimal
    max_rss_kib: int
    exit_status: int
    extras: Mapping[str, str]
    selected_max_rss_kib: Optional[int] = None
    selected_max_rss_source: str = "gnu_time:%M"
    process_tree_peak_total_rss_kib: Optional[int] = None

    @property
    def cpu_seconds(self) -> Decimal:
        return self.user_seconds + self.system_seconds

    @property
    def effective_max_rss_kib(self) -> int:
        return self.max_rss_kib if self.selected_max_rss_kib is None else self.selected_max_rss_kib


@dataclass(frozen=True)
class ProcessTreePeak:
    total_rss_kib: int
    elapsed_seconds: Decimal
    process_count: int
    timestamp_utc: str
    sample_count: int


PhaseKey = Tuple[str, str, int, int, str]


def decimal_text(value: Decimal) -> str:
    """Render a finite Decimal without exponent notation."""

    return format(value, "f")


def observed_mean_cores(metrics: TimingMetrics) -> str:
    if metrics.elapsed_seconds == 0:
        return ""
    return format(metrics.cpu_seconds / metrics.elapsed_seconds, ".6f")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def escaped_single_line(text: str) -> str:
    return text.replace("\\", "\\\\").replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")


def parse_nonnegative_decimal(raw: str, field: str, source: Path) -> Decimal:
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise RecordError(f"{source}: {field} is not numeric: {raw!r}") from exc
    if not value.is_finite() or value < 0:
        raise RecordError(f"{source}: {field} must be finite and nonnegative: {raw!r}")
    return value


def parse_timing(path: Path) -> TimingMetrics:
    """Parse exactly one tagged, tab-delimited GNU time record."""

    try:
        lines = [line for line in path.read_text(errors="replace").splitlines() if line.strip()]
    except OSError as exc:
        raise RecordError(f"{path}: cannot read timing record: {exc}") from exc
    if len(lines) != 1:
        raise RecordError(f"{path}: expected exactly one nonempty timing line, found {len(lines)}")

    fields = lines[0].split("\t")
    if not fields or fields[0] != TIME_TAG:
        observed = fields[0] if fields else ""
        raise RecordError(f"{path}: expected leading tag {TIME_TAG!r}, found {observed!r}")

    values: Dict[str, str] = {}
    for token in fields[1:]:
        if "=" not in token:
            raise RecordError(f"{path}: malformed timing token: {token!r}")
        key, value = token.split("=", 1)
        if not key:
            raise RecordError(f"{path}: empty timing field name")
        if key in values:
            raise RecordError(f"{path}: duplicate timing field: {key}")
        values[key] = value

    missing = [field for field in TIME_REQUIRED_FIELDS if field not in values]
    if missing:
        raise RecordError(f"{path}: missing timing fields: {', '.join(missing)}")

    user_seconds = parse_nonnegative_decimal(values["user_seconds"], "user_seconds", path)
    system_seconds = parse_nonnegative_decimal(values["system_seconds"], "system_seconds", path)
    elapsed_seconds = parse_nonnegative_decimal(values["elapsed_seconds"], "elapsed_seconds", path)

    if not re.fullmatch(r"\d+", values["max_rss_kib"]):
        raise RecordError(f"{path}: max_rss_kib is not a nonnegative integer")
    max_rss_kib = int(values["max_rss_kib"])
    if max_rss_kib <= 0:
        raise RecordError(f"{path}: max_rss_kib must be greater than zero")

    if not re.fullmatch(r"-?\d+", values["exit_status"]):
        raise RecordError(f"{path}: exit_status is not an integer")
    exit_status = int(values["exit_status"])

    extras = {key: value for key, value in values.items() if key not in TIME_REQUIRED_FIELDS}
    return TimingMetrics(
        user_seconds=user_seconds,
        system_seconds=system_seconds,
        elapsed_seconds=elapsed_seconds,
        max_rss_kib=max_rss_kib,
        exit_status=exit_status,
        extras=extras,
    )


def parse_process_tree_peak(path: Path) -> ProcessTreePeak:
    """Return max(total_rss_kb) from the process-tree sampler table."""

    try:
        handle = path.open("r", newline="", errors="replace")
    except OSError as exc:
        raise RecordError(f"{path}: cannot read process-tree totals: {exc}") from exc
    with handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise RecordError(f"{path}: missing process-tree header")
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise RecordError(f"{path}: duplicate process-tree header fields")
        required = {"timestamp_utc", "elapsed_seconds", "process_count", "total_rss_kb"}
        missing = sorted(required - set(reader.fieldnames))
        if missing:
            raise RecordError(f"{path}: missing process-tree fields: {', '.join(missing)}")

        peak: Optional[ProcessTreePeak] = None
        sample_count = 0
        for row_number, row in enumerate(reader, 2):
            if None in row:
                raise RecordError(f"{path}:{row_number}: ragged process-tree row")
            if not any((value or "").strip() for value in row.values()):
                continue
            sample_count += 1
            raw_rss = (row.get("total_rss_kb") or "").strip()
            raw_process_count = (row.get("process_count") or "").strip()
            if not re.fullmatch(r"\d+", raw_rss) or int(raw_rss) <= 0:
                raise RecordError(f"{path}:{row_number}: invalid total_rss_kb {raw_rss!r}")
            if not re.fullmatch(r"\d+", raw_process_count) or int(raw_process_count) <= 0:
                raise RecordError(
                    f"{path}:{row_number}: invalid process_count {raw_process_count!r}"
                )
            elapsed = parse_nonnegative_decimal(
                (row.get("elapsed_seconds") or "").strip(), "elapsed_seconds", path
            )
            candidate = ProcessTreePeak(
                total_rss_kib=int(raw_rss),
                elapsed_seconds=elapsed,
                process_count=int(raw_process_count),
                timestamp_utc=(row.get("timestamp_utc") or "").strip(),
                sample_count=sample_count,
            )
            if peak is None or candidate.total_rss_kib > peak.total_rss_kib:
                peak = candidate

    if peak is None:
        raise RecordError(f"{path}: process-tree table has no data rows")
    return replace(peak, sample_count=sample_count)


def looks_like_field_name(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", value.strip()))


def parse_small_tsv(path: Path) -> Tuple[Dict[str, str], List[str]]:
    """Parse common one-row or key/value metadata TSV layouts.

    Metadata is provenance rather than the primary timing source, so an
    unfamiliar but nonempty layout is retained as raw text and warned about
    rather than discarded.
    """

    warnings: List[str] = []
    try:
        raw = path.read_text(errors="replace")
    except OSError as exc:
        return {}, [f"cannot_read_metadata:{exc}"]
    if not raw.strip():
        return {}, ["empty_metadata"]

    rows = [row for row in csv.reader(raw.splitlines(), delimiter="\t") if any(cell.strip() for cell in row)]
    result: Dict[str, str] = {}
    if not rows:
        return {}, ["empty_metadata"]

    explicit_key_value_header = (
        len(rows[0]) == 2
        and rows[0][0].strip().lower() in {"key", "field", "name"}
        and rows[0][1].strip().lower() in {"value", "val"}
    )
    if explicit_key_value_header and all(len(row) == 2 for row in rows):
        for key, value in rows[1:]:
            key = key.strip()
            if not key:
                warnings.append("metadata_empty_key")
                continue
            if key in result:
                warnings.append(f"metadata_duplicate_key:{key}")
            result[key] = value
    elif (
        len(rows) >= 2
        and len(rows[0]) == len(rows[1])
        and len(rows[0]) >= 2
        and all(looks_like_field_name(cell) for cell in rows[0])
        and not all(looks_like_field_name(cell) for cell in rows[1])
    ):
        if len(rows) > 2:
            warnings.append("metadata_has_multiple_data_rows_using_first")
        result = {key.strip(): value for key, value in zip(rows[0], rows[1]) if key.strip()}
    elif all(len(row) == 2 for row in rows):
        for key, value in rows:
            key = key.strip()
            if not key:
                warnings.append("metadata_empty_key")
                continue
            if key in result:
                warnings.append(f"metadata_duplicate_key:{key}")
            result[key] = value
    elif len(rows) == 2 and len(rows[0]) == len(rows[1]):
        result = {key.strip(): value for key, value in zip(rows[0], rows[1]) if key.strip()}
    else:
        result = {"raw_text": escaped_single_line(raw)}
        warnings.append("metadata_layout_unparsed")
    return result, warnings


def metadata_exit_status(metadata: Mapping[str, str]) -> Optional[int]:
    lowered = {key.lower(): value for key, value in metadata.items()}
    for key in ("exit_status", "command_exit_status", "wrapper_exit_status", "return_code", "rc"):
        if key not in lowered:
            continue
        value = lowered[key].strip()
        if re.fullmatch(r"-?\d+", value):
            return int(value)
        return None
    return None


def status_indicates_failure(metadata: Mapping[str, str]) -> bool:
    lowered = {key.lower(): value.strip().lower() for key, value in metadata.items()}
    failure_values = {
        "failed",
        "failure",
        "error",
        "cancelled",
        "canceled",
        "timeout",
        "timed_out",
        "preempted",
        "oom",
        "out_of_memory",
    }
    return any(lowered.get(key) in failure_values for key in ("status", "state", "result"))


def blank_record(
    dataset: str,
    raw_dataset: str,
    phase: str,
    tool: str,
    threads: object,
    replicate: object,
    attempt: str,
    attempt_dir: Path,
    expected_key: bool,
) -> MutableMapping[str, str]:
    record: MutableMapping[str, str] = {column: "" for column in LONG_COLUMNS}
    record.update(
        {
            "dataset": dataset,
            "raw_dataset": raw_dataset,
            "phase": phase,
            "tool": tool,
            "threads": str(threads),
            "replicate": str(replicate),
            "attempt": attempt,
            "attempt_dir": str(attempt_dir),
            "expected_key": "true" if expected_key else "false",
            "accepted": "false",
        }
    )
    return record


def fill_metrics(record: MutableMapping[str, str], metrics: TimingMetrics, prefix: str = "") -> None:
    record[f"{prefix}user_seconds"] = decimal_text(metrics.user_seconds)
    record[f"{prefix}system_seconds"] = decimal_text(metrics.system_seconds)
    record[f"{prefix}cpu_seconds"] = decimal_text(metrics.cpu_seconds)
    record[f"{prefix}elapsed_seconds"] = decimal_text(metrics.elapsed_seconds)
    record[f"{prefix}exit_status"] = str(metrics.exit_status)
    if prefix:
        record[f"{prefix}max_rss_kib"] = str(metrics.max_rss_kib)
    else:
        record["gnu_time_max_rss_kib"] = str(metrics.max_rss_kib)
        record["observed_mean_cores"] = observed_mean_cores(metrics)
        record["metrics_extra_json"] = json.dumps(metrics.extras, sort_keys=True, separators=(",", ":"))


def identity_errors(
    values: Mapping[str, str],
    raw_dataset: str,
    phase: str,
    tool: str,
    threads: object,
    replicate: object,
    source_label: str,
    component: Optional[str] = None,
) -> List[str]:
    expected = {
        "dataset": raw_dataset,
        "phase": phase,
        "tool": tool,
        "threads": str(threads),
        "replicate": str(replicate),
    }
    if component is not None:
        expected["component"] = component
    errors: List[str] = []
    for field, expected_value in expected.items():
        if field not in values:
            errors.append(f"{source_label}_missing_identity:{field}")
        elif values[field] != expected_value:
            errors.append(
                f"{source_label}_identity_mismatch:{field}={values[field]!r}_expected={expected_value!r}"
            )
    return errors


def append_warning(record: MutableMapping[str, str], warning: str) -> None:
    current = [part for part in record.get("warnings", "").split(";") if part]
    if warning not in current:
        current.append(warning)
    record["warnings"] = ";".join(current)


def parse_attempt(
    dataset: str,
    raw_dataset: str,
    phase: str,
    tool: str,
    threads: object,
    replicate: object,
    attempt_dir: Path,
    expected_key: bool,
) -> Tuple[MutableMapping[str, str], bool, Optional[TimingMetrics], int]:
    match = ATTEMPT_RE.fullmatch(attempt_dir.name)
    attempt_number = int(match.group(1)) if match else -1
    attempt_label = match.group(1) if match else attempt_dir.name
    record = blank_record(
        dataset,
        raw_dataset,
        phase,
        tool,
        threads,
        replicate,
        attempt_label,
        attempt_dir,
        expected_key,
    )
    errors: List[str] = []
    if not match:
        errors.append("noncanonical_attempt_directory")
    if not expected_key:
        append_warning(record, "unexpected_run_key")

    required_paths = {
        "metrics": attempt_dir / "metrics.tsv",
        "status": attempt_dir / "status.tsv",
        "run_metadata": attempt_dir / "run_metadata.tsv",
        "command": attempt_dir / "command.sh",
        "stdout": attempt_dir / "stdout.log",
        "stderr": attempt_dir / "stderr.log",
        "whitelist_metadata": attempt_dir / "whitelist_metadata.tsv",
        "complete": attempt_dir / "COMPLETE",
    }
    for name, path in required_paths.items():
        if name == "complete":
            if not path.is_file():
                errors.append("missing_COMPLETE")
        elif name in {"stdout", "stderr"}:
            if not path.is_file():
                append_warning(record, f"missing_optional_log:{path.name}")
        elif not path.is_file():
            errors.append(f"missing_file:{path.name}")

    record.update(
        {
            "metrics_path": str(required_paths["metrics"]),
            "status_path": str(required_paths["status"]),
            "run_metadata_path": str(required_paths["run_metadata"]),
            "command_path": str(required_paths["command"]),
            "stdout_path": str(required_paths["stdout"]),
            "stderr_path": str(required_paths["stderr"]),
            "whitelist_metadata_path": str(required_paths["whitelist_metadata"]),
            "complete_marker": "true" if required_paths["complete"].is_file() else "false",
        }
    )

    metrics: Optional[TimingMetrics] = None
    if required_paths["metrics"].is_file():
        try:
            metrics = parse_timing(required_paths["metrics"])
            fill_metrics(record, metrics)
            record["metrics_sha256"] = sha256_file(required_paths["metrics"])
            if expected_key:
                errors.extend(
                    identity_errors(
                        metrics.extras,
                        raw_dataset,
                        phase,
                        tool,
                        threads,
                        replicate,
                        "metrics",
                        component=None
                        if tool == "Flexiplex" and phase == "whitelist_detection"
                        else "main",
                    )
                )
                if (
                    tool == "Flexiplex"
                    and phase == "whitelist_detection"
                    and metrics.extras.get("component_count") != "2"
                ):
                    errors.append("metrics_component_count_not_two")
            if metrics.exit_status != 0:
                errors.append(f"nonzero_metrics_exit:{metrics.exit_status}")
            if metrics.elapsed_seconds == 0:
                append_warning(record, "zero_elapsed_seconds")
            else:
                try:
                    requested_threads = Decimal(str(threads))
                except InvalidOperation:
                    requested_threads = Decimal(0)
                if (
                    requested_threads > 0
                    and metrics.cpu_seconds / metrics.elapsed_seconds
                    > requested_threads * Decimal("1.10")
                ):
                    append_warning(record, "observed_mean_cores_exceeds_requested_threads")
        except (OSError, RecordError) as exc:
            errors.append(f"metrics_parse_error:{exc}")

    status_metadata: Dict[str, str] = {}
    if required_paths["status"].is_file():
        status_metadata, status_warnings = parse_small_tsv(required_paths["status"])
        for warning in status_warnings:
            append_warning(record, f"status_{warning}")
        record["status_metadata_json"] = json.dumps(status_metadata, sort_keys=True, separators=(",", ":"))
        if required_paths["status"].stat().st_size == 0:
            errors.append("empty_status.tsv")
        status_exit = metadata_exit_status(status_metadata)
        if status_indicates_failure(status_metadata):
            errors.append("status_metadata_indicates_failure")
        all_status_exits: Dict[str, int] = {}
        for status_key, status_value in status_metadata.items():
            if not status_key.lower().endswith("exit_status"):
                continue
            if re.fullmatch(r"-?\d+", status_value.strip()):
                all_status_exits[status_key] = int(status_value)
            else:
                errors.append(f"nonnumeric_status_exit:{status_key}")
        for status_key, status_value in all_status_exits.items():
            if status_value != 0:
                errors.append(f"nonzero_status_exit:{status_key}={status_value}")
        if status_exit is not None:
            if metrics is not None and status_exit != metrics.exit_status:
                errors.append("status_metrics_exit_mismatch")

    if required_paths["run_metadata"].is_file():
        run_metadata, run_metadata_warnings = parse_small_tsv(required_paths["run_metadata"])
        for warning in run_metadata_warnings:
            append_warning(record, f"run_metadata_{warning}")
        record["run_metadata_json"] = json.dumps(run_metadata, sort_keys=True, separators=(",", ":"))
        for field in (
            "hostname",
            "cpu_model",
            "slurm_job_id",
            "slurm_cpus_per_task",
            "input_fastq",
            "input_size_bytes",
            "input_sha256_preverified",
            "expected_reads",
        ):
            record[field] = run_metadata.get(field, "")
        if required_paths["run_metadata"].stat().st_size == 0:
            errors.append("empty_run_metadata.tsv")
        elif expected_key:
            errors.extend(
                identity_errors(
                    run_metadata,
                    raw_dataset,
                    phase,
                    tool,
                    threads,
                    replicate,
                    "run_metadata",
                )
            )
            allocated_cpus = run_metadata.get("slurm_cpus_per_task", "")
            if allocated_cpus != str(threads):
                errors.append(
                    f"run_metadata_slurm_cpus_per_task_mismatch:{allocated_cpus!r}_expected={threads!r}"
                )

    if required_paths["command"].is_file():
        command_text = required_paths["command"].read_text(errors="replace")
        record["command"] = escaped_single_line(command_text)
        record["command_sha256"] = sha256_file(required_paths["command"])
        if not command_text.strip():
            errors.append("empty_command.sh")

    if required_paths["whitelist_metadata"].is_file():
        whitelist_metadata, whitelist_warnings = parse_small_tsv(required_paths["whitelist_metadata"])
        for warning in whitelist_warnings:
            append_warning(record, f"whitelist_{warning}")
        record["whitelist_metadata_json"] = json.dumps(
            whitelist_metadata, sort_keys=True, separators=(",", ":")
        )
        record["whitelist_metadata_sha256"] = sha256_file(required_paths["whitelist_metadata"])
        if required_paths["whitelist_metadata"].stat().st_size == 0:
            errors.append("empty_whitelist_metadata.tsv")
        else:
            whitelist_rows = whitelist_metadata.get("rows_nonempty", "")
            whitelist_sha256 = whitelist_metadata.get("sha256", "")
            record["whitelist_rows_nonempty"] = whitelist_rows
            record["whitelist_sha256"] = whitelist_sha256
            if not re.fullmatch(r"\d+", whitelist_rows) or int(whitelist_rows) <= 0:
                errors.append("invalid_whitelist_rows_nonempty")
            if not re.fullmatch(r"[0-9a-fA-F]{64}", whitelist_sha256):
                errors.append("invalid_whitelist_sha256")

    output_metadata_path = attempt_dir / "output_metadata.tsv"
    record["output_metadata_path"] = str(output_metadata_path)
    if output_metadata_path.is_file():
        output_metadata, output_metadata_warnings = parse_small_tsv(output_metadata_path)
        for warning in output_metadata_warnings:
            append_warning(record, f"output_{warning}")
        record["output_metadata_json"] = json.dumps(output_metadata, sort_keys=True, separators=(",", ":"))

    process_tree_path = attempt_dir / "process_tree_totals.tsv"
    if tool == "BLAZE":
        record["process_tree_totals_path"] = str(process_tree_path)
        if not process_tree_path.is_file():
            errors.append("missing_file:process_tree_totals.tsv")
        else:
            try:
                tree_peak = parse_process_tree_peak(process_tree_path)
                record["process_tree_peak_total_rss_kib"] = str(tree_peak.total_rss_kib)
                record["process_tree_peak_elapsed_seconds"] = decimal_text(
                    tree_peak.elapsed_seconds
                )
                record["process_tree_peak_process_count"] = str(tree_peak.process_count)
                record["process_tree_peak_timestamp_utc"] = tree_peak.timestamp_utc
                record["process_tree_sample_count"] = str(tree_peak.sample_count)
                record["selected_max_rss_kib"] = str(tree_peak.total_rss_kib)
                record["selected_max_rss_source"] = (
                    "process_tree_totals.tsv:max(total_rss_kb)"
                )
                if metrics is not None:
                    metrics = replace(
                        metrics,
                        selected_max_rss_kib=tree_peak.total_rss_kib,
                        selected_max_rss_source=(
                            "process_tree_totals.tsv:max(total_rss_kb)"
                        ),
                        process_tree_peak_total_rss_kib=tree_peak.total_rss_kib,
                    )
                    if tree_peak.total_rss_kib < metrics.max_rss_kib:
                        append_warning(record, "process_tree_peak_below_gnu_time_max_rss")
            except (OSError, RecordError) as exc:
                errors.append(f"process_tree_totals_parse_error:{exc}")
    elif metrics is not None:
        record["selected_max_rss_kib"] = str(metrics.max_rss_kib)
        record["selected_max_rss_source"] = "gnu_time:%M"

    component_metrics: Dict[str, TimingMetrics] = {}
    if tool == "Flexiplex" and phase == "whitelist_detection":
        for component in ("discovery", "filter"):
            component_path = attempt_dir / f"component_{component}.metrics.tsv"
            record[f"component_{component}_metrics_path"] = str(component_path)
            if not component_path.is_file():
                errors.append(f"missing_file:{component_path.name}")
                continue
            try:
                parsed = parse_timing(component_path)
                component_metrics[component] = parsed
                fill_metrics(record, parsed, prefix=f"component_{component}_")
                if expected_key:
                    errors.extend(
                        identity_errors(
                            parsed.extras,
                            raw_dataset,
                            phase,
                            tool,
                            threads,
                            replicate,
                            f"component_{component}",
                            component=component,
                        )
                    )
                if parsed.exit_status != 0:
                    errors.append(f"nonzero_component_{component}_exit:{parsed.exit_status}")
            except (OSError, RecordError) as exc:
                errors.append(f"component_{component}_parse_error:{exc}")

        if metrics is not None and len(component_metrics) == 2:
            component_user = sum((item.user_seconds for item in component_metrics.values()), Decimal(0))
            component_system = sum((item.system_seconds for item in component_metrics.values()), Decimal(0))
            component_elapsed = sum((item.elapsed_seconds for item in component_metrics.values()), Decimal(0))
            component_rss = max(item.max_rss_kib for item in component_metrics.values())
            tolerance = Decimal("0.05")
            if abs(metrics.user_seconds - component_user) > tolerance:
                append_warning(record, "aggregate_user_differs_from_component_sum")
            if abs(metrics.system_seconds - component_system) > tolerance:
                append_warning(record, "aggregate_system_differs_from_component_sum")
            if abs(metrics.elapsed_seconds - component_elapsed) > tolerance:
                append_warning(record, "aggregate_elapsed_differs_from_component_sum")
            if metrics.max_rss_kib != component_rss:
                append_warning(record, "aggregate_rss_differs_from_component_max")

    for error in errors:
        append_warning(record, error)
    valid = not errors and metrics is not None
    record["record_status"] = "eligible" if valid else "invalid"
    return record, valid, metrics, attempt_number


def expected_keys() -> Iterable[Tuple[str, str, int, int, str, str]]:
    for raw_dataset, dataset in RAW_TO_DISPLAY_DATASET.items():
        for threads in THREADS:
            for replicate in REPLICATES:
                for tool in TOOLS:
                    for phase in PHASES:
                        yield raw_dataset, dataset, threads, replicate, tool, phase


def key_for(dataset: str, phase: str, threads: int, replicate: int, tool: str) -> PhaseKey:
    return dataset, phase, threads, replicate, tool


def discover_attempt_dirs(phase_dir: Path) -> List[Path]:
    if not phase_dir.is_dir():
        return []
    return sorted(
        (path for path in phase_dir.iterdir() if path.is_dir() and path.name.startswith("attempt_")),
        key=lambda path: (
            int(ATTEMPT_RE.fullmatch(path.name).group(1)) if ATTEMPT_RE.fullmatch(path.name) else -1,
            path.name,
        ),
    )


def collect(raw_root: Path) -> Tuple[List[MutableMapping[str, str]], Dict[PhaseKey, TimingMetrics]]:
    records: List[MutableMapping[str, str]] = []
    selected: Dict[PhaseKey, TimingMetrics] = {}
    selected_records: Dict[PhaseKey, MutableMapping[str, str]] = {}
    known_attempt_dirs: set[Path] = set()

    for raw_dataset, dataset, threads, replicate, tool, phase in expected_keys():
        phase_dir = (
            raw_root
            / raw_dataset
            / f"threads_{threads}"
            / f"rep_{replicate}"
            / tool
            / phase
        )
        attempt_dirs = discover_attempt_dirs(phase_dir)
        accepted_pointer_path = phase_dir / "ACCEPTED"
        accepted_pointer_value = ""
        pointer_error = ""
        if not accepted_pointer_path.is_file():
            pointer_error = "missing_ACCEPTED_pointer"
        else:
            pointer_lines = [
                line.strip()
                for line in accepted_pointer_path.read_text(errors="replace").splitlines()
                if line.strip()
            ]
            if len(pointer_lines) != 1:
                pointer_error = f"invalid_ACCEPTED_pointer_line_count:{len(pointer_lines)}"
            else:
                accepted_pointer_value = pointer_lines[0]
                if ATTEMPT_RE.fullmatch(accepted_pointer_value) is None:
                    pointer_error = f"invalid_ACCEPTED_pointer_value:{accepted_pointer_value}"
        if not attempt_dirs:
            record = blank_record(
                dataset,
                raw_dataset,
                phase,
                tool,
                threads,
                replicate,
                "",
                phase_dir,
                True,
            )
            record["accepted_pointer_path"] = str(accepted_pointer_path)
            record["accepted_pointer_value"] = accepted_pointer_value
            record["record_status"] = "missing"
            append_warning(record, "no_attempt_directory")
            if pointer_error:
                append_warning(record, pointer_error)
            else:
                append_warning(record, "ACCEPTED_pointer_target_missing")
            records.append(record)
            continue

        candidates: List[Tuple[int, MutableMapping[str, str], TimingMetrics]] = []
        key = key_for(dataset, phase, threads, replicate, tool)
        key_records: List[MutableMapping[str, str]] = []
        for attempt_dir in attempt_dirs:
            normalized_attempt_dir = attempt_dir.resolve()
            known_attempt_dirs.add(normalized_attempt_dir)
            record, valid, metrics, attempt_number = parse_attempt(
                dataset,
                raw_dataset,
                phase,
                tool,
                threads,
                replicate,
                attempt_dir,
                True,
            )
            records.append(record)
            key_records.append(record)
            record["accepted_pointer_path"] = str(accepted_pointer_path)
            record["accepted_pointer_value"] = accepted_pointer_value
            if valid and metrics is not None:
                candidates.append((attempt_number, record, metrics))

        candidates.sort(key=lambda item: item[0])
        pointed_candidate = next(
            (
                item
                for item in candidates
                if Path(item[1]["attempt_dir"]).name == accepted_pointer_value
            ),
            None,
        )
        if not pointer_error and pointed_candidate is None:
            pointer_error = "ACCEPTED_pointer_target_missing_or_ineligible"
        if pointer_error:
            for key_record in key_records:
                append_warning(key_record, pointer_error)

        if pointed_candidate is not None and not pointer_error:
            accepted_number, accepted_record, accepted_metrics = pointed_candidate
            accepted_record["accepted"] = "true"
            accepted_record["record_status"] = "accepted"
            selected[key] = accepted_metrics
            selected_records[key] = accepted_record
            if len(candidates) > 1:
                candidate_labels = ",".join(item[1]["attempt"] for item in candidates)
                for _, candidate_record, _ in candidates:
                    append_warning(candidate_record, f"multiple_eligible_attempts:{candidate_labels}")
                    if candidate_record is not accepted_record:
                        candidate_record["record_status"] = "superseded_eligible"
            if any(
                record["attempt"].isdigit() and int(record["attempt"]) > accepted_number
                for record in key_records
            ):
                append_warning(accepted_record, "newer_ineligible_attempt_present")
            if any(number > accepted_number for number, _, _ in candidates):
                append_warning(accepted_record, "newer_eligible_attempt_not_accepted")
        else:
            for _, candidate_record, _ in candidates:
                candidate_record["record_status"] = "unreferenced_eligible"

    # A demultiplexing phase must consume the whitelist recorded by its paired
    # detection phase.  Variation across thread/replicate detection runs is
    # retained as a warning because it changes the demultiplexing workload.
    for dataset in DISPLAY_DATASETS:
        for threads in THREADS:
            for replicate in REPLICATES:
                for tool in TOOLS:
                    detection_record = selected_records.get(
                        key_for(dataset, "whitelist_detection", threads, replicate, tool)
                    )
                    demux_record = selected_records.get(
                        key_for(dataset, "demultiplexing", threads, replicate, tool)
                    )
                    if detection_record is None or demux_record is None:
                        continue
                    if detection_record["whitelist_sha256"] != demux_record["whitelist_sha256"]:
                        append_warning(detection_record, "paired_phase_whitelist_sha256_mismatch")
                        append_warning(demux_record, "paired_phase_whitelist_sha256_mismatch")
                    if (
                        detection_record["whitelist_rows_nonempty"]
                        != demux_record["whitelist_rows_nonempty"]
                    ):
                        append_warning(detection_record, "paired_phase_whitelist_row_count_mismatch")
                        append_warning(demux_record, "paired_phase_whitelist_row_count_mismatch")

    for dataset in DISPLAY_DATASETS:
        for tool in TOOLS:
            detection_records = [
                selected_records[key_for(dataset, "whitelist_detection", threads, replicate, tool)]
                for threads in THREADS
                for replicate in REPLICATES
                if key_for(dataset, "whitelist_detection", threads, replicate, tool)
                in selected_records
            ]
            hashes = {record["whitelist_sha256"] for record in detection_records}
            row_counts = {record["whitelist_rows_nonempty"] for record in detection_records}
            if len(hashes) > 1:
                for record in detection_records:
                    append_warning(record, "detection_whitelist_varies_across_thread_or_replicate")
            if len(row_counts) > 1:
                for record in detection_records:
                    append_warning(record, "detection_whitelist_row_count_varies_across_thread_or_replicate")

    if raw_root.is_dir():
        for attempt_dir in sorted(path for path in raw_root.rglob("attempt_*") if path.is_dir()):
            if attempt_dir.resolve() in known_attempt_dirs:
                continue
            relative = attempt_dir.relative_to(raw_root)
            parts = relative.parts
            raw_dataset = parts[0] if len(parts) > 0 else ""
            dataset = RAW_TO_DISPLAY_DATASET.get(raw_dataset, raw_dataset)
            threads_text = parts[1].removeprefix("threads_") if len(parts) > 1 else ""
            replicate_text = parts[2].removeprefix("rep_") if len(parts) > 2 else ""
            tool = parts[3] if len(parts) > 3 else ""
            phase = parts[4] if len(parts) > 4 else ""
            record, _, _, _ = parse_attempt(
                dataset,
                raw_dataset,
                phase,
                tool,
                threads_text,
                replicate_text,
                attempt_dir,
                False,
            )
            record["record_status"] = "unexpected"
            records.append(record)

    return records, selected


def atomic_write_rows(path: Path, fieldnames: Sequence[str], rows: Iterable[Mapping[str, object]], delimiter: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        with temporary.open("w", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=fieldnames,
                delimiter=delimiter,
                lineterminator="\n",
                extrasaction="ignore",
            )
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def wide_rows(
    selected: Mapping[PhaseKey, TimingMetrics], dataset: str, phase: str, metric: str
) -> Iterable[Mapping[str, object]]:
    for threads in THREADS:
        row: Dict[str, object] = {"threads": threads}
        for tool in TOOLS:
            for replicate in REPLICATES:
                column = f"{tool}_rep_{replicate}"
                metrics = selected.get(key_for(dataset, phase, threads, replicate, tool))
                if metrics is None:
                    row[column] = "NA"
                elif metric == "cpu_seconds":
                    row[column] = decimal_text(metrics.cpu_seconds)
                elif metric == "wall_seconds":
                    row[column] = decimal_text(metrics.elapsed_seconds)
                elif metric == "max_rss_kib":
                    row[column] = str(metrics.effective_max_rss_kib)
                else:
                    raise AssertionError(f"unknown wide metric: {metric}")
        yield row


def rss_wide_rows(
    selected: Mapping[PhaseKey, TimingMetrics], dataset: str, phase: str
) -> Iterable[Mapping[str, object]]:
    """Expose GNU-time, sampled-tree, and legacy-selected RSS side by side."""

    for threads in THREADS:
        row: Dict[str, object] = {"threads": threads}
        for metric in RSS_WIDE_METRICS:
            for tool in TOOLS:
                for replicate in REPLICATES:
                    column = f"{metric}__{tool}_rep_{replicate}"
                    metrics = selected.get(key_for(dataset, phase, threads, replicate, tool))
                    if metrics is None:
                        row[column] = "NA"
                    elif metric == "selected_max_rss_kib":
                        row[column] = str(metrics.effective_max_rss_kib)
                    elif metric == "gnu_time_max_rss_kib":
                        row[column] = str(metrics.max_rss_kib)
                    elif metric == "process_tree_peak_total_rss_kib":
                        tree_rss = metrics.process_tree_peak_total_rss_kib
                        row[column] = "NA" if tree_rss is None else str(tree_rss)
                    else:
                        raise AssertionError(f"unknown RSS metric: {metric}")
        yield row


def write_outputs(
    run_root: Path,
    records: Sequence[Mapping[str, str]],
    selected: Mapping[PhaseKey, TimingMetrics],
) -> List[Path]:
    outputs: List[Path] = []
    result_root = run_root / "results"
    for dataset in DISPLAY_DATASETS:
        dataset_root = result_root / dataset
        for phase in PHASES:
            cpu_output = dataset_root / f"{phase}_cpu_seconds.csv"
            atomic_write_rows(
                cpu_output,
                WIDE_COLUMNS,
                wide_rows(selected, dataset, phase, "cpu_seconds"),
                delimiter=",",
            )
            outputs.append(cpu_output)

            wall_output = dataset_root / f"{phase}_wall_seconds.csv"
            atomic_write_rows(
                wall_output,
                WIDE_COLUMNS,
                wide_rows(selected, dataset, phase, "wall_seconds"),
                delimiter=",",
            )
            outputs.append(wall_output)

            rss_output = dataset_root / f"{phase}_max_rss_kib.csv"
            atomic_write_rows(
                rss_output,
                RSS_WIDE_COLUMNS,
                rss_wide_rows(selected, dataset, phase),
                delimiter=",",
            )
            outputs.append(rss_output)

    provenance = run_root / "provenance" / "all_runs_long.tsv"
    atomic_write_rows(provenance, LONG_COLUMNS, records, delimiter="\t")
    outputs.append(provenance)
    return outputs


def resolve_run_root(args: argparse.Namespace, parser: argparse.ArgumentParser) -> Path:
    values = [value for value in (args.run_root, args.run_root_option) if value is not None]
    if len(values) > 1:
        parser.error("provide RUN_ROOT either positionally or through --run-root, not both")
    if values:
        return values[0].expanduser().resolve()
    environment_value = os.environ.get("RUN_ROOT")
    if environment_value:
        return Path(environment_value).expanduser().resolve()
    parser.error("RUN_ROOT is required (positional, --run-root, or environment variable)")
    raise AssertionError("argparse.error did not exit")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", nargs="?", type=Path, metavar="RUN_ROOT")
    parser.add_argument("--run-root", dest="run_root_option", type=Path, help="benchmark run root")
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help=f"exit nonzero unless all {EXPECTED_PHASE_KEYS} expected phase keys are accepted",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    run_root = resolve_run_root(args, parser)
    raw_root = run_root / "raw"

    try:
        records, selected = collect(raw_root)
        outputs = write_outputs(run_root, records, selected)
    except (OSError, RecordError, ValueError) as exc:
        print(f"ERROR: collection failed: {exc}", file=sys.stderr)
        return 2

    complete = len(selected)
    incomplete = EXPECTED_PHASE_KEYS - complete
    warning_records = sum(bool(record.get("warnings")) for record in records)
    print(f"run_root={run_root}")
    print(f"complete_phase_keys={complete}/{EXPECTED_PHASE_KEYS}")
    print(f"incomplete_phase_keys={incomplete}")
    print(f"provenance_rows={len(records)}")
    print(f"records_with_warnings={warning_records}")
    print(f"outputs_written={len(outputs)}")

    if args.require_complete and complete != EXPECTED_PHASE_KEYS:
        print(
            f"ERROR: --require-complete requested, but only {complete} of "
            f"{EXPECTED_PHASE_KEYS} phase keys are complete",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
