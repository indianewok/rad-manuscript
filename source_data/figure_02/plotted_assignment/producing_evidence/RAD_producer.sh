#!/usr/bin/env bash
# Portable path form of the recorded command; original byte hash is in source_manifest.json.
set -euo pipefail

RUN_ROOT=results/sctagger_L_rad_fixed5000_adapter_fix_20260817
RAD_BIN=external_data/software/rad_24d5ce4/build/rad
INPUT=external_data/reviewer_comment_data/wl_scan/20260731_sctagger_badread_quality_full/inputs/L/flatQ20.fq.gz
BASE=external_data/reviewer_comment_data/sctagger_L_fixed5000_three_tool_20260812/rad
LAYOUT=${BASE}/three_prime_10x3v3_umi12_layout.csv
GLOBAL_WL=${BASE}/L_truth_5000_rad_global.csv
CUSTOM_WL=${BASE}/L_truth_5000_rad_custom.csv
PREFIX=L_flatQ20_rad_adapter_fix
CPU_SET=0-63
THREADS=64

if [[ -e "${RUN_ROOT}/COMPLETE" ]]; then
    echo "Refusing to overwrite completed run: ${RUN_ROOT}" >&2
    exit 1
fi

date -u +%FT%TZ > "${RUN_ROOT}/started_utc.txt"
{
    printf 'run_root\t%s\n' "${RUN_ROOT}"
    printf 'rad_binary\t%s\n' "${RAD_BIN}"
    printf 'rad_version\t%s\n' "$("${RAD_BIN}" --version)"
    printf 'rad_binary_sha256\t%s\n' "$(sha256sum "${RAD_BIN}" | awk '{print $1}')"
    printf 'git_commit\t%s\n' "$(git -C external_data/software/rad_24d5ce4 rev-parse HEAD)"
    printf 'git_remote_main\t%s\n' "$(git -C external_data/software/rad_24d5ce4 ls-remote origin refs/heads/main | awk '{print $1}')"
    printf 'input\t%s\n' "${INPUT}"
    printf 'input_sha256\t%s\n' "$(sha256sum "${INPUT}" | awk '{print $1}')"
    printf 'layout\t%s\n' "${LAYOUT}"
    printf 'layout_sha256\t%s\n' "$(sha256sum "${LAYOUT}" | awk '{print $1}')"
    printf 'global_whitelist\t%s\n' "${GLOBAL_WL}"
    printf 'global_whitelist_sha256\t%s\n' "$(sha256sum "${GLOBAL_WL}" | awk '{print $1}')"
    printf 'custom_whitelist\t%s\n' "${CUSTOM_WL}"
    printf 'custom_whitelist_sha256\t%s\n' "$(sha256sum "${CUSTOM_WL}" | awk '{print $1}')"
    printf 'cpu_affinity\t%s\n' "${CPU_SET}"
    printf 'threads\t%s\n' "${THREADS}"
    printf 'chunk_size\t5000\n'
    printf 'barcode_correction_mode\toffensive\n'
    printf 'whitelist_mutation\t2\n'
    printf 'generated_mutation\t2\n'
    printf 'auto_whitelist\tfalse\n'
} > "${RUN_ROOT}/provenance.tsv"

printf '%q ' taskset -c "${CPU_SET}" /usr/bin/time -v -o "${RUN_ROOT}/time.verbose.txt" -- \
    "${RAD_BIN}" demux -l "${LAYOUT}" -q "${INPUT}" -g "${GLOBAL_WL}" -c "${CUSTOM_WL}" \
    -R offensive -M 2 -m 2 -z 5000 -o "${PREFIX}" -d "${RUN_ROOT}" \
    -F "${RUN_ROOT}/${PREFIX}.log" -t "${THREADS}" -v \
    > "${RUN_ROOT}/command.sh.txt"
printf '\n' >> "${RUN_ROOT}/command.sh.txt"

set +e
taskset -c "${CPU_SET}" /usr/bin/time -v -o "${RUN_ROOT}/time.verbose.txt" -- \
    "${RAD_BIN}" demux \
    -l "${LAYOUT}" \
    -q "${INPUT}" \
    -g "${GLOBAL_WL}" \
    -c "${CUSTOM_WL}" \
    -R offensive -M 2 -m 2 -z 5000 \
    -o "${PREFIX}" -d "${RUN_ROOT}" \
    -F "${RUN_ROOT}/${PREFIX}.log" \
    -t "${THREADS}" -v \
    > "${RUN_ROOT}/stdout.log" 2> "${RUN_ROOT}/stderr.log"
run_rc=$?
set -e

printf '%s\n' "${run_rc}" > "${RUN_ROOT}/exit_status.txt"
date -u +%FT%TZ > "${RUN_ROOT}/finished_utc.txt"
if [[ "${run_rc}" -ne 0 ]]; then
    exit "${run_rc}"
fi

gzip -t "${RUN_ROOT}/${PREFIX}.fq.gz"
printf 'RAD_EXIT0\n' > "${RUN_ROOT}/RAD_EXIT0"
