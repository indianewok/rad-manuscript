#!/usr/bin/env bash
# Submit from the repository root. The input is the retained shift+1 FASTQ.
# RAD_PYTHON=/path/to/python sbatch scripts/figure_02/summarize_full_barcode_quality_2018.sbatch \
#   /path/to/shuffled_L_lr_synth.badread2018_truthbc.shift_p01.fq.gz OUTPUT_DIRECTORY
#
# CPU-only standard placement was verified on 2026-10-24. The lsonglab account
# inherits its allowed QoS; do not place this job on a GPU-equipped node.
#SBATCH --job-name=rad-full-q2018
#SBATCH --account=lsonglab
#SBATCH --partition=standard
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --gres=gpu:0

set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: sbatch $0 SHIFT_PLUS_1_FASTQ OUTPUT_DIRECTORY" >&2
    exit 2
fi

cd "${SLURM_SUBMIT_DIR:?Submit from the repository root}"
shifted_fastq=$1
output_directory=$2
python_binary=${RAD_PYTHON:-python3}

"$python_binary" scripts/figure_02/summarize_full_barcode_quality_2018.py \
    --fastq "$shifted_fastq" \
    --input-shift 1 \
    --output-dir "$output_directory" \
    --workers 7 \
    --sample-csv source_data/figure_02/paired_50000_barcode_mean_Q.csv.gz
