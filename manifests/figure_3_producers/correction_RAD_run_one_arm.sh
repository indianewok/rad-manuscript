#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "usage: $0 SC_ONT|SN_ONT|SC_PB|SN_PB" >&2
    exit 2
fi

arm=$1
case "${arm}" in
    SC_ONT)
        raw=external_data/reviewer_comment_data/scratch_preservation_20260921/files/rad_longbench_20260726/data/SC_ONT.fastq.gz
        expected_reads=117002380
        ;;
    SN_ONT)
        raw=external_data/reviewer_comment_data/scratch_preservation_20260921/files/rad_longbench_20260726/data/sc_sn/raw_fastq/SN_ONT.fastq.gz
        expected_reads=119016231
        ;;
    SC_PB)
        raw=external_data/reviewer_comment_data/scratch_preservation_20260921/files/rad_longbench_20260726/data/sc_sn/raw_fastq/SC_PB.fastq.gz
        expected_reads=195242482
        ;;
    SN_PB)
        raw=external_data/reviewer_comment_data/scratch_preservation_20260921/files/rad_longbench_20260726/data/sc_sn/raw_fastq/SN_PB.fastq.gz
        expected_reads=161917662
        ;;
    *)
        echo "unknown arm: ${arm}" >&2
        exit 2
        ;;
esac

root=external_data/reviewer_comment_data/scratch_preservation_20260921/files/longbench_rad_4acbe00_raw_prism_20260827
rad=${root}/tools/rad_4acbe00
layout=${root}/inputs/common/longbench_three_prime_v31.csv
global=${root}/inputs/common/3M-february-2018-3v3.txt
custom=${root}/inputs/${arm}/custom_whitelist.txt
out=${root}/runs/${arm}/demux
prefix=${arm}_RAD
mkdir -p "${out}"

exec 9>"${root}/runs/${arm}/run.lock"
flock -n 9 || { echo "${arm}: another job owns the lock" >&2; exit 3; }
if [[ -e "${root}/runs/${arm}/DONE" ]]; then
    echo "${arm}: already complete"
    exit 0
fi

cp -a "${root}/inputs/${arm}/${prefix}_layout.csv" "${out}/${prefix}_layout.csv"
cp -a "${root}/inputs/${arm}/${prefix}_position_map.csv" "${out}/${prefix}_position_map.csv"

allocated=${SLURM_CPUS_PER_TASK:-32}
pigz_threads=4
if (( allocated <= pigz_threads )); then
    echo "allocated CPUs (${allocated}) must exceed pigz threads (${pigz_threads})" >&2
    exit 2
fi
rad_threads=$((allocated - pigz_threads))

export OMP_DYNAMIC=FALSE
export OMP_MAX_ACTIVE_LEVELS=1
export OMP_NUM_THREADS=${rad_threads}
export OMP_PROC_BIND=FALSE
export RAD_PIGZ_THREADS=${pigz_threads}
export TMPDIR=${root}/runs/${arm}/tmp
mkdir -p "${TMPDIR}"

{
    echo "arm=${arm}"
    echo "rad_commit=4acbe004ba11b150d6832395452632f367a6e6c1"
    echo "rad_binary=${rad}"
    echo "rad_binary_sha256=$(sha256sum "${rad}" | awk '{print $1}')"
    echo "rad_version=$(${rad} --version)"
    echo "raw=${raw}"
    echo "raw_size_bytes=$(stat -Lc %s "${raw}")"
    echo "expected_input_reads=${expected_reads}"
    echo "layout=${layout}"
    echo "layout_sha256=$(sha256sum "${layout}" | awk '{print $1}')"
    echo "global_whitelist=${global}"
    echo "global_whitelist_sha256=$(sha256sum "${global}" | awk '{print $1}')"
    echo "custom_whitelist=${custom}"
    echo "custom_whitelist_rows=$(awk 'NF {n++} END {print n+0}' "${custom}")"
    echo "custom_whitelist_sha256=$(sha256sum "${custom}" | awk '{print $1}')"
    echo "cached_layout_sha256=$(sha256sum "${out}/${prefix}_layout.csv" | awk '{print $1}')"
    echo "cached_position_map_sha256=$(sha256sum "${out}/${prefix}_position_map.csv" | awk '{print $1}')"
    echo "slurm_job_id=${SLURM_JOB_ID:-none}"
    echo "slurm_node=${SLURMD_NODENAME:-none}"
    echo "slurm_cpus_per_task=${allocated}"
    echo "rad_threads=${rad_threads}"
    echo "pigz_threads=${pigz_threads}"
    echo "min_read_length=85"
    echo "start_utc=$(date -u +%FT%TZ)"
} > "${root}/runs/${arm}/run_metadata.txt"

/usr/bin/time -v -o "${out}/time.txt" \
    "${rad}" demux \
    --layout "${layout}" \
    --fastq "${raw}" \
    --global-whitelist "${global}" \
    --custom-whitelist "${custom}" \
    --bc-correction-mode offensive \
    --whitelist-mutation 2 \
    --generated-mutation 2 \
    --min-read-length 85 \
    --dir "${out}" \
    --output "${prefix}" \
    --log-file "${out}/${prefix}.log" \
    --threads "${rad_threads}" \
    --chunk-size 5000 \
    --verbose \
    > "${out}/stdout.log" 2> "${out}/stderr.log"

test -s "${out}/${prefix}.fq.gz"
pigz -t "${out}/${prefix}.fq.gz"
test -s "${out}/${prefix}_whitelist_true.csv"
test -s "${out}/${prefix}_whitelist_global.csv"

processed=$(awk -F': *' '/Total reads processed/ {gsub(/,/,"",$2); value=$2} END {print value}' "${out}/${prefix}.log")
if [[ "${processed}" != "${expected_reads}" ]]; then
    echo "${arm}: processed-read gate failed: ${processed} != ${expected_reads}" >&2
    exit 1
fi

{
    echo "end_utc=$(date -u +%FT%TZ)"
    echo "processed_reads=${processed}"
    echo "output_fastq_bytes=$(stat -Lc %s "${out}/${prefix}.fq.gz")"
    echo "output_fastq_sha256=$(sha256sum "${out}/${prefix}.fq.gz" | awk '{print $1}')"
} >> "${root}/runs/${arm}/run_metadata.txt"
touch "${root}/runs/${arm}/DONE"
echo "${arm}: PASS"
