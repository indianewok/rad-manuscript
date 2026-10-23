#!/usr/bin/env python3
"""Aggregate tagged GNU-time component records without losing precision."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
from pathlib import Path


PREFIX = "GNU_TIME_V1"


def read_record(path: Path) -> dict[str, str]:
    lines = [line.rstrip("\n") for line in path.read_text().splitlines() if line.strip()]
    if len(lines) != 1:
        raise ValueError(f"{path}: expected exactly one nonempty timing record")
    fields = lines[0].split("\t")
    if fields[0] != PREFIX:
        raise ValueError(f"{path}: missing {PREFIX} prefix")
    result: dict[str, str] = {}
    for field in fields[1:]:
        if "=" not in field:
            raise ValueError(f"{path}: malformed field {field!r}")
        key, value = field.split("=", 1)
        if key in result:
            raise ValueError(f"{path}: duplicate key {key!r}")
        result[key] = value
    required = {"user_seconds", "system_seconds", "elapsed_seconds", "max_rss_kib", "exit_status"}
    missing = required - result.keys()
    if missing:
        raise ValueError(f"{path}: missing fields {sorted(missing)}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--tool", required=True)
    parser.add_argument("--threads", type=int, required=True)
    parser.add_argument("--replicate", type=int, required=True)
    parser.add_argument("components", nargs="+", type=Path)
    args = parser.parse_args()

    records = [read_record(path) for path in args.components]
    try:
        user = sum((Decimal(record["user_seconds"]) for record in records), Decimal(0))
        system = sum((Decimal(record["system_seconds"]) for record in records), Decimal(0))
        elapsed = sum((Decimal(record["elapsed_seconds"]) for record in records), Decimal(0))
        rss = max(int(record["max_rss_kib"]) for record in records)
        exits = [int(record["exit_status"]) for record in records]
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid numeric timing field: {exc}") from exc
    exit_status = 0 if all(code == 0 for code in exits) else next(code for code in exits if code != 0)

    fields = [
        PREFIX,
        f"dataset={args.dataset}",
        f"phase={args.phase}",
        f"tool={args.tool}",
        f"threads={args.threads}",
        f"replicate={args.replicate}",
        f"user_seconds={user}",
        f"system_seconds={system}",
        f"elapsed_seconds={elapsed}",
        f"max_rss_kib={rss}",
        f"exit_status={exit_status}",
        f"component_count={len(records)}",
    ]
    args.output.write_text("\t".join(fields) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

