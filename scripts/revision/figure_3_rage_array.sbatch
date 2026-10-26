#!/usr/bin/env bash
set -euo pipefail
cd "$1"
task_index=${SLURM_ARRAY_TASK_ID:?}
replicate=$((task_index % 3 + 1))
case $((task_index / 3)) in
  0) tool=RAD ;;
  1) tool=BLAZE ;;
  2) tool=Flexiplex ;;
  *) exit 2 ;;
esac
python3 scripts/revision/figure_3_rage_run.py "$tool" "$replicate"
