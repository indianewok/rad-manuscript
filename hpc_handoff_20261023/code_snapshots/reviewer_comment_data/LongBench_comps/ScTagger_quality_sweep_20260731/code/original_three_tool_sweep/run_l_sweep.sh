#!/usr/bin/env bash
set -euo pipefail

root=/scratch/f005f43/sctagger_sl_three_tool_quality_20260731
runner=${root}/scripts/run_case.sh
variant_dir=${root}/inputs/L_variants
flat_q20=/scratch-nfs/f005f43/rad_longbench_20260726/data/shuffled_L_lr_synth.fq.gz
status=${root}/logs/L_sweep.status.log

note() {
    printf '%s\t%s\n' "$(date -u +%FT%TZ)" "$*" >> "${status}"
}

if [[ -e "${root}/L_SWEEP_DONE" ]]; then
    exit 0
fi

note "starting L/flatQ20 while quality variants are generated"
"${runner}" L flatQ20 "${flat_q20}"
note "complete L/flatQ20"

while [[ ! -e "${root}/L_VARIANTS_READY" ]]; do
    note "waiting for 11 L quality variants"
    sleep 60
done

mapfile -t variants < <(
    find "${variant_dir}" -maxdepth 1 -type f -name '*.fq.gz' | sort
)
[[ "${#variants[@]}" -eq 11 ]]
for input in "${variants[@]}"; do
    filename=${input##*/}
    tag=${filename#shuffled_L_lr_synth.badread2018_truthbc.}
    tag=${tag%.fq.gz}
    note "starting L/${tag}"
    "${runner}" L "${tag}" "${input}"
    note "complete L/${tag}"
done

touch "${root}/L_SWEEP_DONE"
note "L sweep complete"
