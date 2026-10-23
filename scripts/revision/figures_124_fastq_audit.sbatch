#!/usr/bin/env bash
#SBATCH --job-name=rad_fig2_identity
#SBATCH --account=lsonglab
#SBATCH --qos=lsonglab_gpu
#SBATCH --partition=standard
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:30:00
#SBATCH --gres=gpu:0
#SBATCH --output=/dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/rad-manuscript/validation/figures_124_fastq_%j.log
set -euo pipefail
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
cd /dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/rad-manuscript
/usr/bin/time -v /dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/miniconda3/bin/python3 scripts/revision/figures_124_fastq_audit.py
