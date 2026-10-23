#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "usage: $0 SC_ONT|SC_PB|SN_ONT|SN_PB" >&2
    exit 2
fi

dataset=$1
case "${dataset}" in
    SC_ONT)
        selected_name=SC_flexiplex_whitelist.txt
        ;;
    SC_PB)
        selected_name=SC_PB_flexiplex_whitelist.txt
        ;;
    SN_ONT)
        selected_name=SN_flexiplex_whitelist.txt
        ;;
    SN_PB)
        selected_name=SN_PB_flexiplex_whitelist.txt
        ;;
    *)
        echo "unknown dataset: ${dataset}" >&2
        exit 2
        ;;
esac

audit_root=/scratch/f005f43/longbench_full_ab_audit_20260730
input_root=/scratch-nfs/f005f43/rad_longbench_20260726/data/sc_sn/raw_fastq
source_root=/scratch/f005f43/rad_longbench_20260726/benchmarks/flexiplex_valid_to_valid_correction_audit_20260728
binary="${source_root}/tools/flexiplex-v1.02.6-audit/flexiplex"
selected="${source_root}/inputs/${selected_name}"
input="${input_root}/${dataset}.fastq.gz"
out_dir="${audit_root}/flexiplex_v1026_current_diagnostic/${dataset}"
prefix="${dataset}_flexiplex_v1026_audit"
sidecar="${out_dir}/${prefix}_reads_barcodes.txt"
threads=${FLEX_AUDIT_THREADS:-16}

mkdir -p "${out_dir}"
if [[ -e "${out_dir}/DONE" ]]; then
    echo "${dataset}: Flexiplex v1.02.6 audit already complete"
    exit 0
fi

test -x "${binary}"
test -s "${input}"
test -s "${selected}"
unset FLEXIPLEX_AUDIT_SOURCE_FILE

{
    echo "dataset=${dataset}"
    echo "scope=full LongBench input"
    echo "role=user-authorized updated Flexiplex arm for the complete four-dataset comparison"
    echo "matching_logic_change=none"
    echo "added_field=RawCellBarcode"
    echo "input=${input}"
    echo "selected_whitelist=${selected}"
    echo "selected_barcodes=$(wc -l < "${selected}")"
    echo "threads=${threads}"
    echo "discovery_flank_edit_distance=0"
    echo "demultiplexing_flank_edit_distance=8"
    echo "command=pigz -dc INPUT | flexiplex-audit -d 10x3v3 -f 8 -e 2 -k SELECTED -p THREADS -n PREFIX > /dev/null"
    echo "binary_sha256=$(sha256sum "${binary}" | awk '{print $1}')"
    echo "start_utc=$(date -u +%FT%TZ)"
} > "${out_dir}/run_metadata.txt"

exec 9>"${out_dir}/run.lock"
flock -n 9 || {
    echo "${dataset}: another audit owns the lock" >&2
    exit 3
}

/usr/bin/time -v -o "${out_dir}/time.txt" \
    bash -c '
        set -o pipefail
        cd "$1"
        pigz -dc -p "$2" "$3" |
            "$4" -d 10x3v3 -f 8 -e 2 -k "$5" -p "$2" -n "$6" \
            > /dev/null
    ' _ "${out_dir}" "${threads}" "${input}" "${binary}" "${selected}" "${prefix}" \
    > "${out_dir}/stdout.log" 2> "${out_dir}/stderr.log"

test -s "${sidecar}"
head -1 "${sidecar}" |
    grep -Fx $'Read\tCellBarcode\tRawCellBarcode\tFlankEditDist\tBarcodeEditDist\tUMI'
assignment_rows=$(($(wc -l < "${sidecar}") - 1))
pigz -p "${threads}" "${sidecar}"
gzip -t "${sidecar}.gz"
touch "${out_dir}/DONE"
{
    echo "assignment_rows=${assignment_rows}"
    echo "sidecar_size_bytes=$(stat --printf='%s' "${sidecar}.gz")"
    echo "finish_utc=$(date -u +%FT%TZ)"
} >> "${out_dir}/run_metadata.txt"
