#!/usr/bin/env bash
set -euo pipefail
# Flexiplex 1.02.7 (release v1.02.7.1); commit c85543d820030ae970d6ed8d18d6f1ad9f631911
export PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 MPLBACKEND=Agg LANG=C.UTF-8 LC_ALL=C.UTF-8 TZ=UTC PYTHONNOUSERSITE=1
unset PYTHONPATH
mkdir -p results/figure_04/ScMixology2/Flexiplex
gzip -cd external_data/figure_04/inputs/ScMixology2.fastq.gz | flexiplex -d 10x3v3 -f 0 -e 2 -p 16 -n results/figure_04/ScMixology2/Flexiplex/ScMixology2
flexiplex-filter --whitelist external_data/figure_04/catalogues/3M-february-2018-3v3.txt --outfile results/figure_04/ScMixology2/Flexiplex/selected_native.tsv results/figure_04/ScMixology2/Flexiplex/ScMixology2_barcodes_counts.txt
