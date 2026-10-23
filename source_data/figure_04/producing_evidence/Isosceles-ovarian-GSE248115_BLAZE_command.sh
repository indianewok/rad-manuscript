#!/usr/bin/env bash
# verbatim reconstruction of GSE248115_BLAZE_expect
/scratch/f005f43/blaze2_260a0_native_20260727/venv/bin/blaze --expect-cells 2462 --10x-kit-version 3v3 --threads 20 --max-edit-distance 2 --output-prefix /scratch-nfs/f005f43/rad_biological_benchmark_20260731/runs/GSE248115/BLAZE_expect2462/ --output-fastq matched_reads.fastq.gz --minimal_stdout --overwrite /scratch-nfs/f005f43/rad_biological_benchmark_20260731/raw/GSE248115/SRR26865982_ONT_PromethION.fastq.gz 
