#!/usr/bin/env bash
set -euo pipefail
cd -- /scratch/f005f43/rad_longbench_20260726/rad_work
exec env OMP_DYNAMIC=FALSE OMP_MAX_ACTIVE_LEVELS=1 /scratch/f005f43/rad_longbench_20260726/rad_work/build_fixed/rad scan-wl --input /dartfs/rc/lab/A/AckermanLab/CMV/rad_data/raw_fastq_datasets/scmix2.fq.gz --output-prefix /scratch/f005f43/rad_scmix2_20260726/results/fixed_scmix2_scanwl_e03_t24_full_20260726/cases/01_full/output/scanwl --adapter_seq CTACACGACGCTCTTCCGATCT --barcode-length 16 --max-error 0.3 --threads 24 --chunk-size 10000 --whitelist=10x_3v3 
