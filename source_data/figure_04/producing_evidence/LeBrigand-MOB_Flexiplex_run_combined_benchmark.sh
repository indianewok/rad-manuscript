#!/usr/bin/env bash
set -euo pipefail

root=external_data/reviewer_comment_data/scratch_preservation_20260921/files/visium_lebrigand_combined_full_auto_wl_20260731
input_dir=external_data/raw_fastq_datasets/visium_lebrigand_GSE153859_MOB
input_one="${input_dir}/SRR12157794_1.fastq.gz"
input_two="${input_dir}/SRR12157795_1.fastq.gz"
combined="${root}/MOB_SRR12157794_SRR12157795.fastq.gz"
design=external_data/reviewer_comment_data/scratch_preservation_20260921/files/visium_lebrigand_mob_redirect_audit_20260730/inputs/visium_v2_full_4992.txt
truth=external_data/reviewer_comment_data/scratch_preservation_20260921/files/visium_lebrigand_mob_redirect_audit_20260730/inputs/MOB_in_tissue_918.txt
positions="${input_dir}/mob164315-spatial-illumina/spatial/tissue_positions_list.csv"
blaze=external_data/reviewer_comment_data/scratch_preservation_20260921/files/blaze2_260a0_native_20260727/venv/bin/blaze
flex_root=external_data/temporary/flexiplex_release.GqgaKA/flexiplex
flex="${flex_root}/bin/flexiplex-linux"
threads=${LEBRIGAND_THREADS:-12}

mkdir -p "${root}/logs" "${root}/blaze_expect918" \
    "${root}/flex_f0" "${root}/flex_f8"
exec >>"${root}/logs/controller.log" 2>&1

echo "$(date -u +%FT%TZ) validating source FASTQs"
[[ "$(md5sum "${input_one}" | awk '{print $1}')" == ac05146de32ac04bc42e5b6ef36d1a5a ]]
[[ "$(md5sum "${input_two}" | awk '{print $1}')" == d1cd65d8f5a55fb1b189c0019204f872 ]]
pigz -t -p "${threads}" "${input_one}"
pigz -t -p "${threads}" "${input_two}"

if [[ ! -e "${root}/COMBINED_FASTQ_DONE" ]]; then
    temporary="${combined}.building.$$"
    cp --sparse=never "${input_one}" "${temporary}"
    dd if="${input_two}" of="${temporary}" bs=16M oflag=append conv=notrunc status=progress
    mv "${temporary}" "${combined}"
    pigz -t -p "${threads}" "${combined}"
    [[ "$(stat --printf='%s' "${combined}")" -eq 34253341514 ]]
    touch "${root}/COMBINED_FASTQ_DONE"
fi

run_blaze() {
    if [[ -e "${root}/blaze_expect918/DONE" ]]; then return; fi
    /usr/bin/time -v -o "${root}/blaze_expect918/time.txt" \
        "${blaze}" --expect-cells 918 --full-bc-whitelist "${design}" \
        --umi-len 12 --threads "${threads}" --batch-size 1000 \
        --no-emtpy-drops --no-demultiplexing \
        --output-prefix "${root}/blaze_expect918/" "${combined}" \
        >"${root}/blaze_expect918/stdout.log" \
        2>"${root}/blaze_expect918/stderr.log"
    test -s "${root}/blaze_expect918/whitelist.csv"
    touch "${root}/blaze_expect918/DONE"
}

run_flex() {
    local flank=$1
    local label="f${flank}"
    local out="${root}/flex_${label}"
    local prefix="MOB_${label}"
    if [[ -e "${out}/DONE" ]]; then return; fi
    (
        cd "${out}"
        export LD_LIBRARY_PATH=external_data/software/miniconda3/lib
        /usr/bin/time -v -o time.txt bash -c '
            set -o pipefail
            pigz -dc -p "$1" "$2" |
                "$3" -d 10x3v3 -f "$4" -e 2 -p "$1" -n "$5" > /dev/null
        ' _ "${threads}" "${combined}" "${flex}" "${flank}" "${prefix}" \
            >stdout.log 2>stderr.log
        test -s "${prefix}_barcodes_counts.txt"
        test -s "${prefix}_barcodes_final.txt"
        touch DONE
    )
}

echo "$(date -u +%FT%TZ) starting BLAZE and Flexiplex complete-data selectors"
run_blaze & pid_blaze=$!
run_flex 0 & pid_f0=$!
run_flex 8 & pid_f8=$!

status=0
for item in "blaze:${pid_blaze}" "flex_f0:${pid_f0}" "flex_f8:${pid_f8}"; do
    label=${item%%:*}
    pid=${item##*:}
    if wait "${pid}"; then
        echo "$(date -u +%FT%TZ) PASS ${label}"
    else
        return_code=$?
        echo "$(date -u +%FT%TZ) FAIL ${label} status=${return_code}"
        status=1
    fi
done
[[ "${status}" -eq 0 ]]
