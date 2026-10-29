#!/usr/bin/env bash
set -euo pipefail
# BLAZE 2.5.1; commit 9845ec129624f2210c389e67506e29fab849a23d
export PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 MPLBACKEND=Agg LANG=C.UTF-8 LC_ALL=C.UTF-8 TZ=UTC PYTHONNOUSERSITE=1
unset PYTHONPATH
mkdir -p results/figure_04/ScMixology2/BLAZE
blaze --expect-cells 500 --10x-kit-version 3v3 --minQ 15 --max-edit-distance 2 --threads 16 --batch-size 1000 --no-demultiplexing --output-prefix results/figure_04/ScMixology2/BLAZE/ external_data/figure_04/inputs/ScMixology2.fastq.gz
