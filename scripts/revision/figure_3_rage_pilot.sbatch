#!/usr/bin/env bash
set -euo pipefail
cd "$1"
for tool in RAD BLAZE Flexiplex; do
  python3 scripts/revision/figure_3_rage_run.py "$tool" 1 --pilot
done
