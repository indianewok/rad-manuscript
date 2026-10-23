#!/usr/bin/env bash
set -euo pipefail

root=/scratch/f005f43/rad_sctagger_badread_quality_20260727
input=/scratch/f005f43/rad_longbench_20260726/validation_data/shuffled_S_lr_synth.fq.gz
generator=${root}/scripts/generate_truth_conditioned_qscores.py
validator=${root}/scripts/validate_fastq_invariants.py
model=${root}/models/nanopore2018.gz

mkdir -p "${root}/output/S" "${root}/logs" "${root}/qc"

/usr/bin/time -v -o "${root}/logs/S.full.seed20260727.time.verbose.txt" \
    "${generator}" \
    --input "${input}" \
    --output-dir "${root}/output/S" \
    --model "${model}" \
    --shifts 1,2,3,4,5,6,8,10,11,12,13 \
    --seed 20260727 \
    --adapter-max-ed 7 \
    --boundary-slop 8 \
    --tape-size 16777216 \
    --pigz-threads 1 \
    --progress-every 5000 \
    >"${root}/logs/S.full.seed20260727.stdout.log" \
    2>"${root}/logs/S.full.seed20260727.stderr.log"

for seed in 20260728 20260729; do
    output_dir=${root}/output/S_seed${seed}
    mkdir -p "${output_dir}"
    /usr/bin/time -v \
        -o "${root}/logs/S.transition.seed${seed}.time.verbose.txt" \
        "${generator}" \
        --input "${input}" \
        --output-dir "${output_dir}" \
        --model "${model}" \
        --shifts 11,12,13 \
        --seed "${seed}" \
        --adapter-max-ed 7 \
        --boundary-slop 8 \
        --tape-size 16777216 \
        --pigz-threads 1 \
        --progress-every 10000 \
        >"${root}/logs/S.transition.seed${seed}.stdout.log" \
        2>"${root}/logs/S.transition.seed${seed}.stderr.log"
done

find \
    "${root}/output/S" \
    "${root}/output/S_seed20260728" \
    "${root}/output/S_seed20260729" \
    -maxdepth 1 -type f -name '*.fq.gz' -print0 \
    | xargs -0 -n 1 -P 8 pigz -t

"${validator}" \
    --reference "${input}" \
    "${root}"/output/S/*.fq.gz \
    >"${root}/qc/S.full.invariants.tsv"

"${validator}" \
    --reference "${input}" \
    "${root}"/output/S_seed20260728/*.fq.gz \
    "${root}"/output/S_seed20260729/*.fq.gz \
    >"${root}/qc/S.replicates.invariants.tsv"
