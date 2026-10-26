#!/usr/bin/env bash
# Submit only after live verification that the requested partition has no GPU GRES.
# Resource flags are supplied explicitly in the recorded sbatch invocation.
set -euo pipefail
repository=$1
project_root=$2
requested_checkpoint_root=$3
# /scratch is node-local. Retain ledgers on the shared repository filesystem so
# the controlling HPC session can validate and archive them after the job ends.
checkpoint_root="$repository/checkpoints/figure_03/offlist_recount"
mkdir -p "$checkpoint_root"
printf 'Requested temporary path: %s\nDurable output: %s\n' "$requested_checkpoint_root" "$checkpoint_root"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$repository"
python3 scripts/revision/figure_3_count.py offlist \
  --project-root "$project_root" --output "$checkpoint_root"
