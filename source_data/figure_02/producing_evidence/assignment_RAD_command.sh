#!/usr/bin/env bash
set -euo pipefail
# RAD 1.0.2, commit 24d5ce47e172222c96cd7dd19e94758d32aa5009
mkdir -p results/figure_02/RAD_full_global
rad demux \
  -l source_data/figure_02/producing_evidence/assignment_RAD_input_layout.csv \
  -q external_data/figure_02/L_flatQ20.fq.gz \
  -g external_data/figure_02/3M-february-2018-3v3.txt \
  -c external_data/figure_02/L_truth_5000_rad_custom.csv \
  -R offensive -M 2 -m 2 -z 5000 \
  -o L_RAD_full_global -d results/figure_02/RAD_full_global \
  -F results/figure_02/RAD_full_global/L_RAD_full_global.log \
  -t 64 -v
