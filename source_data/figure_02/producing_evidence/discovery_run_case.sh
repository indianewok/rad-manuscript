#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
    echo "usage: $0 S|L QUALITY_TAG INPUT.fastq.gz" >&2
    exit 2
fi

dataset=$1
tag=$2
input=$3

root=external_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_sl_three_tool_quality_20260731
adapter=CTACACGACGCTCTTCCGATCT
global_whitelist=external_data/cellranger_whitelists/3M-february-2018-3v3.txt
rad=external_data/reviewer_comment_data/scratch_preservation_20260921/files/longbench_full_demux_20260730/tools/rad_920adda_edlibfix/build_release/rad
blaze=external_data/reviewer_comment_data/scratch_preservation_20260921/files/blaze2_260a0_native_20260727/venv/bin/blaze
flex=external_data/reviewer_comment_data/scratch_preservation_20260921/files/measles_p7_p8_four_tool_20260730/tools/flexiplex-v1.02.6/flexiplex-linux
flex_filter=external_data/reviewer_comment_data/scratch_preservation_20260921/files/rad_longbench_20260726/benchmarks/flexiplex_valid_to_valid_correction_audit_20260728/tools/flexiplex-v1.02.6-audit/scripts/flexiplex_filter/main.py
python=external_data/software/miniconda3/bin/python
conda_lib=external_data/software/miniconda3/lib
threads=${SCTAGGER_TOOL_THREADS:-8}

case "${dataset}" in
    S)
        expected=50
        truth=${root}/inputs/S_truth_barcodes.txt
        ;;
    L)
        expected=5000
        truth=${root}/inputs/L_truth_barcodes.txt
        ;;
    *)
        echo "unknown ScTagger dataset: ${dataset}" >&2
        exit 2
        ;;
esac

case_root=${root}/runs/${dataset}/${tag}
mkdir -p "${case_root}"/{rad,blaze,flex_f0,flex_f8}
if [[ -e "${case_root}/DONE" ]]; then
    echo "${dataset}/${tag}: already complete"
    exit 0
fi

test -s "${input}"
test -s "${truth}"
test -s "${global_whitelist}"
test -x "${rad}"
test -x "${blaze}"
test -x "${flex}"
test -s "${flex_filter}"

{
    printf 'dataset\t%s\n' "${dataset}"
    printf 'quality_tag\t%s\n' "${tag}"
    printf 'input\t%s\n' "${input}"
    printf 'truth\t%s\n' "${truth}"
    printf 'expected_cells\t%d\n' "${expected}"
    printf 'threads_per_tool\t%d\n' "${threads}"
    printf 'scope\tcomplete input FASTQ\n'
    printf 'rad_mode\tscan-wl adaptive current\n'
    printf 'blaze_selector\t--expect-cells %d --minQ 15\n' "${expected}"
    printf 'flexiplex_selectors\tf0 and f8, release filtering defaults\n'
    printf 'start_utc\t%s\n' "$(date -u +%FT%TZ)"
} > "${case_root}/run_metadata.tsv"

run_rad() {
    local out=${case_root}/rad
    /usr/bin/time -v -o "${out}/time.txt" \
        "${rad}" scan-wl \
        -i "${input}" -o "${out}/scanwl" \
        -p "${adapter}" -n 16 -e 0.3 -w 10x_3v3 \
        -t "${threads}" -k 10000 -v \
        > "${out}/stdout.log" 2> "${out}/stderr.log"
    test -e "${out}/scanwl.txt"
    touch "${out}/DONE"
}

run_blaze() {
    local out=${case_root}/blaze
    mkdir -p "${out}/mpl"
    MPLCONFIGDIR="${out}/mpl" \
        /usr/bin/time -v -o "${out}/time.txt" \
        "${blaze}" \
        --expect-cells "${expected}" \
        --10x-kit-version 3v3 \
        --minQ 15 \
        --threads "${threads}" \
        --minimal_stdout \
        --no-emtpy-drops \
        --no-demultiplexing \
        --output-prefix "${out}/" \
        "${input}" \
        > "${out}/stdout.log" 2> "${out}/stderr.log"
    test -e "${out}/whitelist.csv"
    touch "${out}/DONE"
}

run_flex() {
    local flank=$1
    local out=${case_root}/flex_f${flank}
    local prefix=${dataset}_${tag}_f${flank}
    (
        cd "${out}"
        /usr/bin/time -v -o discovery.time.txt \
            bash -o pipefail -c \
            'pigz -dc -p 4 "$1" | "$2" -d 10x3v3 -f "$3" -e 2 -p "$4" -n "$5" > /dev/null' \
            _ "${input}" "${flex}" "${flank}" "${threads}" "${prefix}" \
            > discovery.stdout.log 2> discovery.stderr.log
        test -s "${prefix}_barcodes_counts.txt"
        env LD_LIBRARY_PATH="${conda_lib}" \
            /usr/bin/time -v -o filter.time.txt \
            "${python}" "${flex_filter}" \
            -v -w "${global_whitelist}" \
            -o selected.txt "${prefix}_barcodes_counts.txt" \
            > filter.stdout.log 2> filter.stderr.log
        test -e selected.txt
        touch DONE
    )
}

run_rad & pid_rad=$!
run_blaze & pid_blaze=$!
run_flex 0 & pid_f0=$!
run_flex 8 & pid_f8=$!

status=0
for pid in "${pid_rad}" "${pid_blaze}" "${pid_f0}" "${pid_f8}"; do
    if ! wait "${pid}"; then
        status=1
    fi
done
if [[ "${status}" -ne 0 ]]; then
    touch "${case_root}/FAILED"
    exit 1
fi

"${python}" "${root}/scripts/summarize_callsets.py" \
    --truth "${truth}" \
    --output "${case_root}/callset_metrics.tsv" \
    "RAD=${case_root}/rad/scanwl.txt" \
    "BLAZE=${case_root}/blaze/whitelist.csv" \
    "Flexiplex_f0=${case_root}/flex_f0/selected.txt" \
    "Flexiplex_f8=${case_root}/flex_f8/selected.txt"

{
    printf 'finish_utc\t%s\n' "$(date -u +%FT%TZ)"
} >> "${case_root}/run_metadata.tsv"
touch "${case_root}/DONE"
