#!/usr/bin/env bash
set -euo pipefail
cd -- external_data/reviewer_comment_data/scratch_preservation_20260921/files/rad_longbench_20260726/rad_work
exec env OMP_DYNAMIC=FALSE OMP_MAX_ACTIVE_LEVELS=1 external_data/reviewer_comment_data/scratch_preservation_20260921/files/rad_longbench_20260726/rad_work/build_fixed/rad scan-wl --input external_data/raw_fastq_datasets/scmix2.fq.gz --output-prefix external_data/reviewer_comment_data/scratch_preservation_20260921/files/rad_scmix2_20260726/results/fixed_scmix2_scanwl_e03_t24_full_20260726/cases/01_full/output/scanwl --adapter_seq CTACACGACGCTCTTCCGATCT --barcode-length 16 --max-error 0.3 --threads 24 --chunk-size 10000 --whitelist=10x_3v3 
