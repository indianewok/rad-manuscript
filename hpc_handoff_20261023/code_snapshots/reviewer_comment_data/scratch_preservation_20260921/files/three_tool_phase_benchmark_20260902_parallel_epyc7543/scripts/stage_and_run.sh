#!/usr/bin/env bash
set -Eeuo pipefail
umask 0027

if [[ $# -lt 4 ]]; then
    printf 'usage: %s block DATASET THREADS REPLICATE | tool DATASET THREADS REPLICATE TOOL\n' "$0" >&2
    exit 2
fi

MODE="$1"
DATASET="$2"
THREADS="$3"
REPLICATE="$4"
TOOL="${5:-}"
: "${RUN_ROOT:?RUN_ROOT must be exported}"
: "${LOCAL_WORK_ROOT:?LOCAL_WORK_ROOT must be exported}"
: "${BENCHMARK_SCRIPT_DIR:?BENCHMARK_SCRIPT_DIR must be exported}"

case "${MODE}" in
    block) [[ $# -eq 4 ]] || { printf 'block mode takes four arguments\n' >&2; exit 2; } ;;
    tool)
        [[ $# -eq 5 ]] || { printf 'tool mode takes five arguments\n' >&2; exit 2; }
        case "${TOOL}" in RAD|Flexiplex|BLAZE) ;; *) printf 'invalid tool: %s\n' "${TOOL}" >&2; exit 2 ;; esac
        ;;
    *) printf 'invalid mode: %s\n' "${MODE}" >&2; exit 2 ;;
esac

# shellcheck source=config.sh
source "${BENCHMARK_SCRIPT_DIR}/config.sh"
unset BENCHMARK_RAW_FASTQ
dataset_config "${DATASET}"
SOURCE_FASTQ="${RAW_FASTQ}"
SOURCE_SIZE="$(stat -Lc %s "${SOURCE_FASTQ}")"

STAGE_DIR="${LOCAL_WORK_ROOT}/staged_inputs"
STAGED_FASTQ="${STAGE_DIR}/${DATASET}.fastq.gz"
STAGE_META="${RUN_ROOT}/provenance/input_staging/${DATASET}/${MODE}"
[[ "${MODE}" == block ]] || STAGE_META="${STAGE_META}/${TOOL}"
STAGE_META="${STAGE_META}/threads_${THREADS}/rep_${REPLICATE}"
mkdir -p -- "${STAGE_DIR}" "${STAGE_META}"

exec {stage_lock_fd}> "${STAGE_DIR}/${DATASET}.lock"
flock "${stage_lock_fd}"
if [[ ! -s "${STAGED_FASTQ}" || "$(stat -Lc %s "${STAGED_FASTQ}" 2>/dev/null || printf 0)" != "${SOURCE_SIZE}" ]]; then
    PARTIAL="${STAGED_FASTQ}.partial.${SLURM_JOB_ID:-$$}"
    rm -f -- "${PARTIAL}"
    started="$(date -u +%FT%TZ)"
    set +e
    /usr/bin/time -q -f 'user_seconds=%U\tsystem_seconds=%S\telapsed_seconds=%e\tmax_rss_kib=%M\texit_status=%x' \
        -o "${STAGE_META}/copy.metrics.partial" -- \
        cp --reflink=auto -- "${SOURCE_FASTQ}" "${PARTIAL}"
    rc=$?
    set -e
    [[ -f "${STAGE_META}/copy.metrics.partial" ]] && mv -f -- \
        "${STAGE_META}/copy.metrics.partial" "${STAGE_META}/copy.metrics.tsv"
    if ((rc != 0)); then
        printf 'input staging failed with status %s\n' "${rc}" >&2
        exit "${rc}"
    fi
    [[ "$(stat -Lc %s "${PARTIAL}")" == "${SOURCE_SIZE}" ]] || {
        printf 'staged input size mismatch\n' >&2
        exit 1
    }
    mv -f -- "${PARTIAL}" "${STAGED_FASTQ}"
    {
        printf 'key\tvalue\n'
        printf 'source\t%s\n' "${SOURCE_FASTQ}"
        printf 'target\t%s\n' "${STAGED_FASTQ}"
        printf 'size_bytes\t%s\n' "${SOURCE_SIZE}"
        printf 'sha256_preverified\t%s\n' "${INPUT_SHA256}"
        printf 'started_utc\t%s\n' "${started}"
        printf 'ended_utc\t%s\n' "$(date -u +%FT%TZ)"
        printf 'hostname\t%s\n' "$(hostname -s)"
        printf 'slurm_job_id\t%s\n' "${SLURM_JOB_ID:-none}"
    } > "${STAGE_META}/copy.metadata.tsv"
else
    {
        printf 'key\tvalue\n'
        printf 'source\t%s\n' "${SOURCE_FASTQ}"
        printf 'target\t%s\n' "${STAGED_FASTQ}"
        printf 'size_bytes\t%s\n' "${SOURCE_SIZE}"
        printf 'sha256_preverified\t%s\n' "${INPUT_SHA256}"
        printf 'reused_existing_staged_copy\ttrue\n'
        printf 'checked_utc\t%s\n' "$(date -u +%FT%TZ)"
        printf 'hostname\t%s\n' "$(hostname -s)"
        printf 'slurm_job_id\t%s\n' "${SLURM_JOB_ID:-none}"
    } > "${STAGE_META}/reuse.metadata.tsv"
fi
flock -u "${stage_lock_fd}"

export BENCHMARK_RAW_FASTQ="${STAGED_FASTQ}"
export BENCHMARK_ALLOW_UNPINNED_HOST=1
case "${MODE}" in
    block)
        exec "${BENCHMARK_SCRIPT_DIR}/run_block.sh" "${DATASET}" "${THREADS}" "${REPLICATE}"
        ;;
    tool)
        exec "${BENCHMARK_SCRIPT_DIR}/run_tool.sh" "${DATASET}" "${THREADS}" "${REPLICATE}" "${TOOL}"
        ;;
esac
