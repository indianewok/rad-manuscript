#!/bin/bash
#SBATCH --job-name=rad_handoff_bam567
#SBATCH --account=lsonglab
#SBATCH --partition=standard
#SBATCH --qos=lsonglab_gpu
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=01:00:00
#SBATCH --gres=gpu:0
#SBATCH --output=validation/figures_567_bam_job_%j.log
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
exec /usr/bin/python3 scripts/revision/figures_567_bam_checks.py
