#!/usr/bin/env bash
set -Eeuo pipefail
umask 0027

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=config.sh
source "${SCRIPT_DIR}/config.sh"

ACCOUNT=lsonglab
PARTITION=preempt_lsong
RUNNER="${RUN_ROOT}/scripts/run_block.sh"
FINALIZER="${RUN_ROOT}/scripts/finalize_job.sh"
JOB_LEDGER="${RUN_ROOT}/provenance/job_ids.tsv"

[[ -x "${RUNNER}" && -x "${FINALIZER}" ]]
mkdir -p -- "${RUN_ROOT}/slurm" "${RUN_ROOT}/provenance"
exec 9> "${RUN_ROOT}/submit.lock"
flock -n 9 || { printf 'another submission process owns %s\n' "${RUN_ROOT}/submit.lock" >&2; exit 3; }
[[ ! -e "${JOB_LEDGER}" ]] || { printf 'job ledger already exists: %s\n' "${JOB_LEDGER}" >&2; exit 3; }

printf 'dataset\tthreads\treplicate\tnode\tjob_id\tdependency\n' > "${JOB_LEDGER}.partial"

submit_block() {
    local dataset="$1" threads="$2" replicate="$3" node="$4" dependency="${5:-}"
    local walltime
    case "${threads}" in
        64) walltime=16:00:00 ;;
        16) walltime=4-00:00:00 ;;
        4) walltime=12-00:00:00 ;;
        *) printf 'unsupported thread count: %s\n' "${threads}" >&2; return 2 ;;
    esac
    local -a args=(
        sbatch --parsable
        --account="${ACCOUNT}"
        --partition="${PARTITION}"
        --nodelist="${node}"
        --nodes=1
        --ntasks=1
        --cpus-per-task="${threads}"
        --hint=nomultithread
        --exclusive
        --mem=64G
        --time="${walltime}"
        --requeue
        --export="ALL,RUN_ROOT=${RUN_ROOT},BENCHMARK_SCRIPT_DIR=${RUN_ROOT}/scripts"
        --job-name="BM_${dataset}_${threads}c_r${replicate}"
        --output="${RUN_ROOT}/slurm/%x.%j.out"
        --error="${RUN_ROOT}/slurm/%x.%j.err"
    )
    [[ -z "${dependency}" ]] || args+=(--dependency="${dependency}")
    local submitted job_id
    submitted="$("${args[@]}" "${RUNNER}" "${dataset}" "${threads}" "${replicate}")"
    job_id="${submitted%%;*}"
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "${dataset}" "${threads}" "${replicate}" \
        "${node}" "${job_id}" "${dependency:-none}" >> "${JOB_LEDGER}.partial"
    printf '%s\n' "${job_id}"
}

declare -a final_dependencies=()
for dataset in SN_ONT SC_PB; do
    dataset_config "${dataset}"
    node="${PINNED_NODE}"

    dependency=''
    for threads in 64 16 4; do
        for replicate in 1 2 3; do
            job_id="$(submit_block "${dataset}" "${threads}" "${replicate}" "${node}" "${dependency}")"
            dependency="afterok:${job_id}"
        done
    done
    final_dependencies+=("${job_id}")
done

final_dependency="afterany:$(IFS=:; printf '%s' "${final_dependencies[*]}")"
final_submitted="$(sbatch --parsable \
    --account="${ACCOUNT}" --partition="${PARTITION}" \
    --nodes=1 --ntasks=1 --cpus-per-task=1 --mem=4G --time=01:00:00 \
    --dependency="${final_dependency}" --job-name=BM_collect \
    --export="ALL,RUN_ROOT=${RUN_ROOT},BENCHMARK_SCRIPT_DIR=${RUN_ROOT}/scripts" \
    --output="${RUN_ROOT}/slurm/%x.%j.out" --error="${RUN_ROOT}/slurm/%x.%j.err" \
    "${FINALIZER}")"
final_job_id="${final_submitted%%;*}"
printf 'FINALIZE\tNA\tNA\tany\t%s\t%s\n' "${final_job_id}" "${final_dependency}" >> "${JOB_LEDGER}.partial"
mv -f -- "${JOB_LEDGER}.partial" "${JOB_LEDGER}"
printf 'Submitted 18 benchmark blocks plus collector job %s\n' "${final_job_id}"
