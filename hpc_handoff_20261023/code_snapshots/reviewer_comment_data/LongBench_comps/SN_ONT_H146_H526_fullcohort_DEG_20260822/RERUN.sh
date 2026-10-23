#!/usr/bin/env bash
set -euo pipefail

package_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$package_root/logs" "$package_root/results" "$package_root/provenance"
export WORK_ROOT="$package_root"
export DEG_WORKERS="${DEG_WORKERS:-16}"

Rscript "$package_root/scripts/run_analysis.R" \
  >"$package_root/logs/run_analysis.stdout.log" \
  2>"$package_root/logs/run_analysis.stderr.log"

python3 "$package_root/scripts/build_cohort_composition.py" \
  >"$package_root/logs/cohort_composition.stdout.log" \
  2>"$package_root/logs/cohort_composition.stderr.log"

python3 "$package_root/scripts/build_key_results.py" \
  >"$package_root/logs/key_results.stdout.log" \
  2>"$package_root/logs/key_results.stderr.log"

python3 "$package_root/scripts/validate_results.py" \
  >"$package_root/logs/validate.stdout.log" \
  2>"$package_root/logs/validate.stderr.log"
