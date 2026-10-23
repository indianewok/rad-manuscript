#!/usr/bin/env bash
# Complete-input RAD correction audit retaining concatenate/chimeric-derived
# records tagged -CT. This makes RAD's raw LongBench counting scope match the
# existing Flexiplex scope. The SQLite grouping proof is job-local.
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "usage: $0 SC_ONT|SN_ONT|SC_PB|SN_PB" >&2
    exit 2
fi

arm=$1
case "${arm}" in
    SC_ONT|SC_PB)
        truth=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/raw_fastq_datasets/longbench/truth
        cellranger=${truth}/count_matrix_barcodes/ill_sc_barcodes.tsv.gz
        label_dir=${truth}/cell_line_annotation/merged_annotation/sc
        ;;
    SN_ONT|SN_PB)
        truth=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/raw_fastq_datasets/longbench/truth
        cellranger=${truth}/count_matrix_barcodes/ill_sn_barcodes.tsv.gz
        label_dir=${truth}/cell_line_annotation/merged_annotation/sn
        ;;
    *)
        echo "unknown arm: ${arm}" >&2
        exit 2
        ;;
esac

root=/scratch-nfs/f005f43/longbench_rad_4acbe00_raw_prism_20260827
prefix=${arm}_RAD
assignments=${root}/runs/${arm}/demux/${prefix}.fq.gz
selected=${root}/inputs/${arm}/custom_whitelist.txt
catalog=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/cellranger_whitelists/3M-february-2018-3v3.txt
catalog_cache=${root}/reference_cache/3M-february-2018.u32
analyzer=${root}/scripts/analyze_correction_events.py
out_name=${RAD_AUDIT_OUT_NAME:-audit_raw_all}
out=${root}/runs/${arm}/${out_name}
manifest=${out}/run_metadata.tsv

validate_outputs() {
    test -s "${out}/summary.tsv"
    test -s "${out}/per_target.tsv"
    test -s "${out}/invariants.tsv"
    awk -F '\t' -v arm="${arm}" '
        NR == 1 { if ($1 != "dataset" || $2 != "tool") exit 1; next }
        NR == 2 { if ($1 != arm || $2 != "rad") exit 1; rows++; next }
        { exit 1 }
        END { exit(rows == 1 ? 0 : 1) }
    ' "${out}/summary.tsv"
    awk -F '\t' '
        NR == 1 { if ($1 != "target_barcode") exit 1; next }
        NR > 1 { rows++ }
        END { exit(rows > 0 ? 0 : 1) }
    ' "${out}/per_target.tsv"
    awk -F '\t' 'NR > 1 && $2 == "FAIL" { failed=1 } END { exit(failed ? 1 : 0) }' \
        "${out}/invariants.tsv"
    awk -F '\t' '
        NR > 1 && $1 == "physical_read_grouping_nonreentry" && $2 == "PASS" { pass++ }
        END { exit(pass == 1 ? 0 : 1) }
    ' "${out}/invariants.tsv"
    jq -e --arg arm "${arm}" '
        .dataset == $arm and
        .tool == "rad" and
        .exclude_rad_ct == false and
        .grouping_check == "sqlite" and
        .adapter_stats.fastq_records_read == .adapter_stats.assignment_rows_yielded and
        .adapter_stats.rad_ct_records_seen > 0 and
        (.adapter_stats.rad_ct_records_excluded // 0) == 0
    ' "${out}/run_metadata.json" >/dev/null
}

mkdir -p "${out}"
exec 9>"${out}/run.lock"
flock -n 9 || { echo "${arm}: another all-record audit owns the lock" >&2; exit 3; }
if [[ -e "${out}/DONE" ]]; then
    validate_outputs
    echo "${arm}: all-record audit already complete"
    exit 0
fi

for required in "${assignments}" "${selected}" "${cellranger}" "${catalog}" \
                "${catalog_cache}" "${analyzer}"; do
    test -s "${required}"
done
test -d "${label_dir}"

cpus=${SLURM_CPUS_PER_TASK:-16}
if (( cpus < 2 )); then
    echo "${arm}: at least two CPUs are required" >&2
    exit 2
fi
pigz_threads=$(( cpus - 1 ))
if (( pigz_threads > 12 )); then pigz_threads=12; fi
tmp_parent=${RAD_AUDIT_TMP_PARENT:-${SLURM_TMPDIR:-/tmp}}
tmpdir=$(mktemp -d "${tmp_parent%/}/rad_raw_all_${arm}.${SLURM_JOB_ID:-manual}.XXXXXX")
cleanup() { rm -rf "${tmpdir}"; }
trap cleanup EXIT INT TERM
grouping_dir=${tmpdir}/grouping
mkdir -p "${grouping_dir}"

{
    printf 'field\tvalue\n'
    printf 'dataset\t%s\n' "${arm}"
    printf 'scope\traw_CR_source_only__RAD_CT_suffix_included\n'
    printf 'assignments\t%s\n' "${assignments}"
    printf 'selected_whitelist\t%s\n' "${selected}"
    printf 'cellranger_filtered\t%s\n' "${cellranger}"
    printf 'global_catalog\t%s\n' "${catalog}"
    printf 'catalog_cache\t%s\n' "${catalog_cache}"
    printf 'label_dir\t%s\n' "${label_dir}"
    printf 'slurm_job_id\t%s\n' "${SLURM_JOB_ID:-none}"
    printf 'slurm_cpus_per_task\t%s\n' "${cpus}"
    printf 'started_utc\t%s\n' "$(date -u +%FT%TZ)"
} > "${manifest}.partial"
mv "${manifest}.partial" "${manifest}"

/usr/bin/time -v -o "${out}/time.txt" \
    python3 "${analyzer}" \
        --tool rad \
        --dataset "${arm}" \
        --assignments "${assignments}" \
        --selected-whitelist "${selected}" \
        --cellranger-filtered "${cellranger}" \
        --global-catalog "${catalog}" \
        --catalog-cache "${catalog_cache}" \
        --label-dir "${label_dir}" \
        --grouping-check sqlite \
        --grouping-db-dir "${grouping_dir}" \
        --decompress-threads "${pigz_threads}" \
        --outdir "${out}" \
        > "${out}/stdout.log" 2> "${out}/stderr.log"

validate_outputs
printf 'finished_utc\t%s\n' "$(date -u +%FT%TZ)" >> "${manifest}"
jq -r '
    ["metric", "count"],
    ["input_fastq_records", .adapter_stats.fastq_records_read],
    ["kept_all_records", .adapter_stats.assignment_rows_yielded],
    ["included_CT_records", .adapter_stats.rad_ct_records_seen]
    | @tsv
' "${out}/run_metadata.json" > "${out}/ct_inclusion_counts.tsv.partial"
mv "${out}/ct_inclusion_counts.tsv.partial" "${out}/ct_inclusion_counts.tsv"
touch "${out}/DONE"
echo "${arm}: RAW all-record correction audit PASS"
