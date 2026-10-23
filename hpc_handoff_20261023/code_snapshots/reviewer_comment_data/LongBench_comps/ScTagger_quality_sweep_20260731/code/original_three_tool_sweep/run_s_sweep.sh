#!/usr/bin/env bash
set -euo pipefail

root=/scratch/f005f43/sctagger_sl_three_tool_quality_20260731
runner=${root}/scripts/run_case.sh
source_dir=/scratch/f005f43/rad_sctagger_badread_quality_20260727/output/S
flat_q20=/scratch-nfs/f005f43/rad_longbench_20260726/data/shuffled_S_lr_synth.fq.gz
status=${root}/logs/S_sweep.status.log

note() {
    printf '%s\t%s\n' "$(date -u +%FT%TZ)" "$*" >> "${status}"
}

if [[ -e "${root}/S_SWEEP_DONE" ]]; then
    exit 0
fi

note "starting S complete-data sweep"
"${runner}" S flatQ20 "${flat_q20}"
note "complete S/flatQ20"

mapfile -t variants < <(
    find "${source_dir}" -maxdepth 1 -type f -name '*.fq.gz' | sort
)
[[ "${#variants[@]}" -eq 11 ]]
for input in "${variants[@]}"; do
    filename=${input##*/}
    tag=${filename#shuffled_S_lr_synth.badread2018_truthbc.}
    tag=${tag%.fq.gz}
    note "starting S/${tag}"
    "${runner}" S "${tag}" "${input}"
    note "complete S/${tag}"
done

touch "${root}/S_SWEEP_DONE"
note "S sweep complete"
