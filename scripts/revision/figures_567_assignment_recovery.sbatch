#!/usr/bin/env bash
#SBATCH --job-name=rad_f7_assign_check
#SBATCH --account=lsonglab
#SBATCH --qos=lsonglab_gpu
#SBATCH --partition=standard
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:30:00
#SBATCH --gres=gpu:0
#SBATCH --output=validation/figures_567_assignment_job_%j.log
set -euo pipefail
cd "${RAD_REPO_ROOT:-${SLURM_SUBMIT_DIR:?Submit this script from the repository root}}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
exec /usr/bin/python3 scripts/revision/figures_567_assignment_recovery.py
