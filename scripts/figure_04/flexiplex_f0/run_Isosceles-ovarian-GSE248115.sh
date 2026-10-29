#!/usr/bin/env bash
set -euo pipefail
# Flexiplex 1.02.6; filter 1.02
INPUT=external_data/figure_04/inputs/SRR26865982.sra
OUT=results/figure_04/Isosceles-ovarian-GSE248115/Flexiplex
FILTER=external_data/software/flexiplex/scripts/flexiplex_filter/main.py
CATALOGUE=external_data/figure_04/catalogues/3M-february-2018-3v3.txt
export PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 LANG=C.UTF-8 LC_ALL=C.UTF-8 TZ=UTC PYTHONNOUSERSITE=1
unset PYTHONPATH
mkdir -p "$OUT"
WORK=$(mktemp -d "$OUT/converter_tmp.XXXXXX")
trap 'rm -rf -- "$WORK"' EXIT
fasterq-dump-orig.3.4.1 "$INPUT" --split-spot --include-technical --min-read-len 0 --threads 16 --mem 256M --temp "$WORK" --stdout | \
  flexiplex -d 10x3v3 -f 0 -e 2 -p 16 -n "$OUT/Isosceles" > "$OUT/discovery.stdout.log"
python3 "$FILTER" --whitelist "$CATALOGUE" --outfile "$OUT/selected_native.tsv" "$OUT/Isosceles_barcodes_counts.txt"
