#!/usr/bin/env bash
# Submit from the repository root with the native FASTQ and output directory:
# RAD_PYTHON=/path/to/python sbatch scripts/figure_02/summarize_full_barcode_quality.sbatch \
#   /path/to/native_unadjusted.fq.gz source_data/figure_02/full_read_quality
#
# Dartmouth CPU-only placement was verified on 2026-10-24. The lsonglab account
# inherits its allowed QoS; the CPU-only standard partition prevents GPU-node use.
#SBATCH --job-name=rad-full-barcode-q
#SBATCH --account=lsonglab
#SBATCH --partition=standard
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --gres=gpu:0

set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: sbatch $0 NATIVE_FASTQ OUTPUT_DIRECTORY" >&2
    exit 2
fi

cd "${SLURM_SUBMIT_DIR:?Submit from the repository root}"
native_fastq=$1
output_directory=$2
python_binary=${RAD_PYTHON:-python3}

# Seven barcode-location workers plus one FASTQ reader use the eight CPUs.
"$python_binary" scripts/figure_02/summarize_full_barcode_quality.py \
    --fastq "$native_fastq" \
    --output-dir "$output_directory" \
    --workers 7 \
    --sample-csv source_data/figure_02/paired_50000_barcode_mean_Q.csv.gz
