#!/usr/bin/env bash
set -euo pipefail

root=/scratch/f005f43/sctagger_sl_three_tool_quality_20260731
input=/scratch-nfs/f005f43/rad_longbench_20260726/data/shuffled_L_lr_synth.fq.gz
output_dir=${root}/inputs/L_variants
generator=/scratch/f005f43/rad_sctagger_badread_quality_20260727/scripts/generate_truth_conditioned_qscores.py
validator=/scratch/f005f43/rad_sctagger_badread_quality_20260727/scripts/validate_fastq_invariants.py
model=/scratch/f005f43/rad_sctagger_badread_quality_20260727/models/nanopore2018.gz
log_dir=${root}/logs/L_generation

mkdir -p "${output_dir}" "${log_dir}"
if [[ -e "${root}/L_VARIANTS_VALIDATED" ]]; then
    exit 0
fi

if [[ ! -e "${root}/L_VARIANTS_READY" ]]; then
    /usr/bin/time -v -o "${log_dir}/generation.time.txt" \
        "${generator}" \
        --input "${input}" \
        --output-dir "${output_dir}" \
        --model "${model}" \
        --shifts 1,2,3,4,5,6,8,10,11,12,13 \
        --seed 20260731 \
        --adapter-max-ed 7 \
        --boundary-slop 8 \
        --tape-size 16777216 \
        --pigz-threads 2 \
        --progress-every 100000 \
        > "${log_dir}/generation.stdout.log" \
        2> "${log_dir}/generation.stderr.log"

    mapfile -t variants < <(
        find "${output_dir}" -maxdepth 1 -type f -name '*.fq.gz' | sort
    )
    [[ "${#variants[@]}" -eq 11 ]]
    printf '%s\0' "${variants[@]}" | xargs -0 -n 1 -P 8 pigz -t
    touch "${root}/L_VARIANTS_READY"
fi

mapfile -t variants < <(
    find "${output_dir}" -maxdepth 1 -type f -name '*.fq.gz' | sort
)
/usr/bin/time -v -o "${log_dir}/validation.time.txt" \
    "${validator}" --reference "${input}" "${variants[@]}" \
    > "${root}/results/L_variant_invariants.tsv"
touch "${root}/L_VARIANTS_VALIDATED"
