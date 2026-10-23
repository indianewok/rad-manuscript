#!/usr/bin/env bash
set -Eeuo pipefail
umask 0027

if [[ $# -ne 3 ]]; then
    printf 'usage: %s SN_ONT|SC_PB 4|16|64 1|2|3\n' "$0" >&2
    exit 2
fi

DATASET="$1"
THREADS="$2"
REPLICATE="$3"
REQUESTED_TOOL="${BENCHMARK_TOOL_ONLY:-}"
SOURCE_SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_DIR="${BENCHMARK_SCRIPT_DIR:-${SOURCE_SCRIPT_DIR}}"
if [[ ! -r "${SCRIPT_DIR}/config.sh" ]]; then
    SCRIPT_DIR="/scratch-nfs/f005f43/three_tool_phase_benchmark_20260902/scripts"
fi
# shellcheck source=config.sh
source "${SCRIPT_DIR}/config.sh"
dataset_config "${DATASET}"
BLAZE_FIFO_LAUNCHER="${BLAZE_FIFO_LAUNCHER:-${SCRIPT_DIR}/blaze_fifo_launcher.py}"

[[ "${THREADS}" =~ ^(4|16|64)$ ]] || { printf 'invalid threads: %s\n' "${THREADS}" >&2; exit 2; }
[[ "${REPLICATE}" =~ ^[123]$ ]] || { printf 'invalid replicate: %s\n' "${REPLICATE}" >&2; exit 2; }
if [[ -n "${REQUESTED_TOOL}" ]]; then
    case "${REQUESTED_TOOL}" in
        RAD|Flexiplex|BLAZE) ;;
        *) printf 'invalid tool: %s (expected RAD, Flexiplex, or BLAZE)\n' "${REQUESTED_TOOL}" >&2; exit 2 ;;
    esac
fi
if [[ "${BENCHMARK_ALLOW_UNPINNED_HOST:-0}" != 1 && "$(hostname -s)" != "${PINNED_NODE}" ]]; then
    printf '%s is pinned to %s; refusing host %s\n' "${DATASET}" "${PINNED_NODE}" "$(hostname -s)" >&2
    exit 2
fi

required_paths=("${RAW_FASTQ}" "${GLOBAL_WHITELIST}")
case "${REQUESTED_TOOL:-all}" in
    RAD) required_paths+=("${RAD_BIN}" "${LAYOUT}" "${RAD_SCAN_WHITELIST}") ;;
    BLAZE) required_paths+=("${BLAZE_BIN}" "${BLAZE_FIFO_LAUNCHER}" "${PROCESS_SAMPLER}") ;;
    Flexiplex) required_paths+=("${FLEXIPLEX_BIN}" "${FLEXIPLEX_FILTER}" "${AGGREGATE_METRICS}") ;;
    all) required_paths+=("${RAD_BIN}" "${BLAZE_BIN}" "${BLAZE_FIFO_LAUNCHER}" "${FLEXIPLEX_BIN}" \
        "${FLEXIPLEX_FILTER}" "${LAYOUT}" "${RAD_SCAN_WHITELIST}" \
        "${PROCESS_SAMPLER}" "${AGGREGATE_METRICS}") ;;
esac
for required in "${required_paths[@]}"; do
    [[ -r "${required}" ]] || { printf 'missing required path: %s\n' "${required}" >&2; exit 2; }
done
command -v pigz >/dev/null
command -v setsid >/dev/null
command -v mkfifo >/dev/null
command -v wc >/dev/null
[[ -x /usr/bin/time ]]
[[ -z "${REQUESTED_TOOL}" ]] || command -v flock >/dev/null

BLOCK_ROOT="${RUN_ROOT}/raw/${DATASET}/threads_${THREADS}/rep_${REPLICATE}"
BLOCK_WORK="${LOCAL_WORK_ROOT}/${DATASET}/threads_${THREADS}/rep_${REPLICATE}"
mkdir -p -- "${BLOCK_ROOT}" "${BLOCK_WORK}"

safe_remove_tree() {
    local target="$1"
    case "${target}" in
        "${LOCAL_WORK_ROOT}"/*)
            rm -rf -- "${target}"
            ;;
        *)
            printf 'refusing unsafe cleanup target: %s\n' "${target}" >&2
            return 2
            ;;
    esac
}

new_attempt() {
    local phase_root="$1"
    local directory suffix highest=0
    mkdir -p -- "${phase_root}"
    shopt -s nullglob
    for directory in "${phase_root}"/attempt_*; do
        suffix="${directory##*/attempt_}"
        if [[ "${suffix}" =~ ^[0-9]+$ ]] && ((10#${suffix} > highest)); then
            highest=$((10#${suffix}))
        fi
    done
    shopt -u nullglob
    printf '%s/attempt_%03d\n' "${phase_root}" "$((highest + 1))"
}

accepted_attempt() {
    local phase_root="$1" name path
    [[ -s "${phase_root}/ACCEPTED" ]] || return 1
    IFS= read -r name < "${phase_root}/ACCEPTED"
    path="${phase_root}/${name}"
    [[ -f "${path}/COMPLETE" && -s "${path}/metrics.tsv" ]] || return 1
    printf '%s\n' "${path}"
}

mark_complete() {
    local phase_root="$1" attempt="$2" marker
    marker="${phase_root}/ACCEPTED.partial.$$"
    touch "${attempt}/COMPLETE"
    printf '%s\n' "${attempt##*/}" > "${marker}"
    mv -f -- "${marker}" "${phase_root}/ACCEPTED"
}

write_command() {
    local output="$1"
    shift
    {
        printf '#!/usr/bin/env bash\n'
        printf 'exec'
        printf ' %q' "$@"
        printf '\n'
    } > "${output}"
}

write_attempt_metadata() {
    local output="$1" tool="$2" phase="$3"
    {
        printf 'key\tvalue\n'
        printf 'dataset\t%s\n' "${DATASET}"
        printf 'tool\t%s\n' "${tool}"
        printf 'phase\t%s\n' "${phase}"
        printf 'threads\t%s\n' "${THREADS}"
        printf 'replicate\t%s\n' "${REPLICATE}"
        printf 'hostname\t%s\n' "$(hostname -s)"
        printf 'cpu_model\t%s\n' "$(awk -F: '/model name/ {gsub(/^[ \t]+/, "", $2); print $2; exit}' /proc/cpuinfo)"
        printf 'slurm_job_id\t%s\n' "${SLURM_JOB_ID:-none}"
        printf 'slurm_cpus_per_task\t%s\n' "${SLURM_CPUS_PER_TASK:-unknown}"
        printf 'input_fastq\t%s\n' "${RAW_FASTQ}"
        printf 'input_size_bytes\t%s\n' "$(stat -Lc %s "${RAW_FASTQ}")"
        printf 'input_sha256_preverified\t%s\n' "${INPUT_SHA256}"
        printf 'expected_reads\t%s\n' "${EXPECTED_READS}"
        printf 'flex_transport_threads\t%s\n' "${FLEX_TRANSPORT_THREADS}"
        printf 'rad_demux_pigz_threads\t%s\n' "${RAD_DEMUX_PIGZ_THREADS}"
        printf 'started_utc\t%s\n' "$(date -u +%FT%TZ)"
    } > "${output}"
}

write_whitelist_metadata() {
    local whitelist="$1" attempt="$2"
    cp -a -- "${whitelist}" "${attempt}/whitelist.txt"
    {
        printf 'key\tvalue\n'
        printf 'source\t%s\n' "${whitelist}"
        printf 'rows_nonempty\t%s\n' "$(awk 'NF {n++} END {print n+0}' "${whitelist}")"
        printf 'sha256\t%s\n' "$(sha256sum "${whitelist}" | awk '{print $1}')"
    } > "${attempt}/whitelist_metadata.tsv"
}

timing_format() {
    local phase="$1" tool="$2" component="$3"
    printf 'GNU_TIME_V1\\tdataset=%s\\tphase=%s\\ttool=%s\\tthreads=%s\\treplicate=%s\\tcomponent=%s\\tuser_seconds=%%U\\tsystem_seconds=%%S\\telapsed_seconds=%%e\\tmax_rss_kib=%%M\\texit_status=%%x' \
        "${DATASET}" "${phase}" "${tool}" "${THREADS}" "${REPLICATE}" "${component}"
}

run_timed_direct() {
    local attempt="$1" cwd="$2" phase="$3" tool="$4" sample_tree="$5"
    shift 5
    local -a command=("$@")
    local format partial pid sampler_pid='' rc started ended
    format="$(timing_format "${phase}" "${tool}" main)"
    partial="${attempt}/metrics.partial"
    write_command "${attempt}/command.sh" "${command[@]}"
    started="$(date -u +%FT%TZ)"

    (
        cd -- "${cwd}"
        exec setsid /usr/bin/time -q -f "${format}" -o "${partial}" -- "${command[@]}"
    ) > "${attempt}/stdout.log" 2> "${attempt}/stderr.log" &
    pid=$!

    if [[ "${sample_tree}" == 1 ]]; then
        "${PROCESS_SAMPLER}" "${pid}" \
            "${attempt}/process_samples.tsv" \
            "${attempt}/process_tree_totals.tsv" \
            "${RSS_SAMPLE_INTERVAL_SECONDS}" \
            "${attempt}/stdout.log" \
            > "${attempt}/sampler.log" 2>&1 &
        sampler_pid=$!
    fi

    if wait "${pid}"; then
        rc=0
    else
        rc=$?
    fi
    if [[ -n "${sampler_pid}" ]]; then
        wait "${sampler_pid}" || true
    fi
    ended="$(date -u +%FT%TZ)"
    [[ -f "${partial}" ]] && mv -f -- "${partial}" "${attempt}/metrics.tsv"
    {
        printf 'key\tvalue\n'
        printf 'started_utc\t%s\n' "${started}"
        printf 'ended_utc\t%s\n' "${ended}"
        printf 'wrapper_exit_status\t%s\n' "${rc}"
    } > "${attempt}/status.tsv"
    return "${rc}"
}

run_rad() {
    local tool=RAD tool_root="${BLOCK_ROOT}/RAD" tool_work="${BLOCK_WORK}/RAD"
    local det_root="${tool_root}/whitelist_detection" demux_root="${tool_root}/demultiplexing"
    local det_work="${tool_work}/detection" demux_work="${tool_work}/demux"
    local attempt accepted='' rc output

    accepted="$(accepted_attempt "${demux_root}" 2>/dev/null || true)"
    if [[ -n "${accepted}" ]]; then
        safe_remove_tree "${tool_work}"
        return 0
    fi

    accepted="$(accepted_attempt "${det_root}" 2>/dev/null || true)"
    if [[ -n "${accepted}" && ! -s "${det_work}/${DATASET}_RAD.txt" ]]; then
        [[ -s "${accepted}/whitelist.txt" ]] || {
            printf 'accepted RAD detection lacks restart whitelist: %s\n' "${accepted}" >&2
            return 1
        }
        mkdir -p -- "${det_work}" "${demux_work}"
        cp -a -- "${accepted}/whitelist.txt" "${det_work}/${DATASET}_RAD.txt.partial.$$"
        mv -f -- "${det_work}/${DATASET}_RAD.txt.partial.$$" "${det_work}/${DATASET}_RAD.txt"
    fi
    if [[ -z "${accepted}" ]]; then
        safe_remove_tree "${tool_work}"
        mkdir -p -- "${det_work}" "${demux_work}"
        attempt="$(new_attempt "${det_root}")"
        mkdir -p -- "${attempt}"
        write_attempt_metadata "${attempt}/run_metadata.tsv" "${tool}" whitelist_detection
        local -a command=(
            env OMP_DYNAMIC=FALSE OMP_MAX_ACTIVE_LEVELS=1 OMP_NUM_THREADS="${THREADS}" OMP_PROC_BIND=FALSE
            "${RAD_BIN}" scan-wl
            --input "${RAW_FASTQ}"
            --output-prefix "${det_work}/${DATASET}_RAD"
            --adapter_seq CTACACGACGCTCTTCCGATCT
            --barcode-length 16
            --max-error 0.1
            "--whitelist=${RAD_SCAN_WHITELIST}"
            --threads "${THREADS}"
            --chunk-size 10000
        )
        set +e
        run_timed_direct "${attempt}" "${det_work}" whitelist_detection "${tool}" 0 "${command[@]}"
        rc=$?
        set -e
        if ((rc != 0)) || [[ ! -s "${det_work}/${DATASET}_RAD.txt" ]]; then
            touch "${attempt}/FAILED"
            return 1
        fi
        write_whitelist_metadata "${det_work}/${DATASET}_RAD.txt" "${attempt}"
        mark_complete "${det_root}" "${attempt}"
    fi

    accepted="$(accepted_attempt "${demux_root}" 2>/dev/null || true)"
    if [[ -z "${accepted}" ]]; then
        mkdir -p -- "${demux_work}"
        output="${demux_work}/${DATASET}_RAD.fq.gz"
        rm -f -- "${output}"
        attempt="$(new_attempt "${demux_root}")"
        mkdir -p -- "${attempt}"
        write_attempt_metadata "${attempt}/run_metadata.tsv" "${tool}" demultiplexing
        local -a command=(
            env OMP_DYNAMIC=FALSE OMP_MAX_ACTIVE_LEVELS=1 OMP_NUM_THREADS="${THREADS}" OMP_PROC_BIND=FALSE RAD_PIGZ_THREADS="${RAD_DEMUX_PIGZ_THREADS}"
            "${RAD_BIN}" demux
            --layout "${LAYOUT}"
            --fastq "${RAW_FASTQ}"
            --global-whitelist "${GLOBAL_WHITELIST}"
            --custom-whitelist "${det_work}/${DATASET}_RAD.txt"
            --bc-correction-mode offensive
            --whitelist-mutation 2
            --generated-mutation 2
            --min-read-length 85
            --dir "${demux_work}"
            --output "${DATASET}_RAD"
            --log-file "${demux_work}/${DATASET}_RAD.log"
            --threads "${THREADS}"
            --chunk-size 5000
        )
        set +e
        run_timed_direct "${attempt}" "${demux_work}" demultiplexing "${tool}" 0 "${command[@]}"
        rc=$?
        set -e
        if ((rc != 0)) || [[ ! -s "${output}" ]]; then
            touch "${attempt}/FAILED"
            return 1
        fi
        cp -a -- "${demux_work}/${DATASET}_RAD.log" "${attempt}/tool.log"
        printf 'output_size_bytes\t%s\n' "$(stat -Lc %s "${output}")" > "${attempt}/output_metadata.tsv"
        write_whitelist_metadata "${det_work}/${DATASET}_RAD.txt" "${attempt}"
        mark_complete "${demux_root}" "${attempt}"
    fi
    safe_remove_tree "${tool_work}"
}

run_blaze() {
    local tool=BLAZE tool_root="${BLOCK_ROOT}/BLAZE" tool_work="${BLOCK_WORK}/BLAZE"
    local det_root="${tool_root}/whitelist_detection" demux_root="${tool_root}/demultiplexing"
    local det_work="${tool_work}/detection" attempt accepted='' rc output output_size output_storage
    local checkpoint putative_size_before putative_size_after putative_mtime_before putative_mtime_after
    local drain_pid='' drain_rc=0 drain_bytes=0 fifo_guard_fd='' drain_started='' drain_ended=''

    accepted="$(accepted_attempt "${demux_root}" 2>/dev/null || true)"
    if [[ -n "${accepted}" ]]; then
        safe_remove_tree "${tool_work}"
        return 0
    fi

    accepted="$(accepted_attempt "${det_root}" 2>/dev/null || true)"
    if [[ -n "${accepted}" && ! -s "${det_work}/whitelist.csv" ]]; then
        [[ -s "${accepted}/whitelist.txt" ]] || {
            printf 'accepted BLAZE detection lacks restart whitelist: %s\n' "${accepted}" >&2
            return 1
        }
        mkdir -p -- "${det_work}/mpl"
        cp -a -- "${accepted}/whitelist.txt" "${det_work}/whitelist.csv.partial.$$"
        mv -f -- "${det_work}/whitelist.csv.partial.$$" "${det_work}/whitelist.csv"
    fi
    if [[ -n "${accepted}" && ! -s "${det_work}/putative_bc.csv" ]]; then
        checkpoint="${RUN_ROOT}/checkpoints/${DATASET}/threads_${THREADS}/rep_${REPLICATE}/BLAZE/putative_bc.csv"
        if [[ ! -s "${checkpoint}" ]]; then
            printf 'accepted BLAZE detection cannot be resumed on %s: required local putative_bc.csv and central checkpoint are absent\n' \
                "$(hostname -s)" >&2
            return 1
        fi
        mkdir -p -- "${det_work}"
        cp -a -- "${checkpoint}" "${det_work}/putative_bc.csv.partial.$$"
        [[ "$(stat -Lc %s "${det_work}/putative_bc.csv.partial.$$")" == "$(stat -Lc %s "${checkpoint}")" ]] || {
            rm -f -- "${det_work}/putative_bc.csv.partial.$$"
            printf 'restored BLAZE putative table size mismatch: %s\n' "${checkpoint}" >&2
            return 1
        }
        mv -f -- "${det_work}/putative_bc.csv.partial.$$" "${det_work}/putative_bc.csv"
        {
            printf 'key\tvalue\n'
            printf 'source\t%s\n' "${checkpoint}"
            printf 'target\t%s\n' "${det_work}/putative_bc.csv"
            printf 'size_bytes\t%s\n' "$(stat -Lc %s "${det_work}/putative_bc.csv")"
            printf 'restored_utc\t%s\n' "$(date -u +%FT%TZ)"
            printf 'hostname\t%s\n' "$(hostname -s)"
            printf 'slurm_job_id\t%s\n' "${SLURM_JOB_ID:-none}"
        } > "${det_work}/checkpoint_restore_metadata.tsv"
    fi
    if [[ -z "${accepted}" ]]; then
        safe_remove_tree "${tool_work}"
        mkdir -p -- "${det_work}/mpl"
        attempt="$(new_attempt "${det_root}")"
        mkdir -p -- "${attempt}"
        write_attempt_metadata "${attempt}/run_metadata.tsv" "${tool}" whitelist_detection
        local -a command=(
            env MPLCONFIGDIR="${det_work}/mpl" PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
            "${BLAZE_BIN}"
            "${BLAZE_SELECTOR[@]}"
            --10x-kit-version 3v3
            --full-bc-whitelist "${GLOBAL_WHITELIST}"
            --minQ 15
            --max-edit-distance 2
            --threads "${THREADS}"
            --batch-size 1000
            --no-demultiplexing
            --output-prefix "${det_work}/"
            --output-fastq matched_reads.fastq
            --minimal_stdout
            "${RAW_FASTQ}"
        )
        set +e
        run_timed_direct "${attempt}" "${det_work}" whitelist_detection "${tool}" 1 "${command[@]}"
        rc=$?
        set -e
        if ((rc != 0)) || [[ ! -s "${det_work}/whitelist.csv" || ! -s "${det_work}/putative_bc.csv" ]]; then
            touch "${attempt}/FAILED"
            return 1
        fi
        [[ -s "${det_work}/summary.txt" ]] && cp -a -- "${det_work}/summary.txt" "${attempt}/tool_summary.txt"
        write_whitelist_metadata "${det_work}/whitelist.csv" "${attempt}"
        mark_complete "${det_root}" "${attempt}"
    fi

    accepted="$(accepted_attempt "${demux_root}" 2>/dev/null || true)"
    if [[ -z "${accepted}" ]]; then
        # SC-PB's uncompressed BLAZE FASTQ is larger than the 272-GiB local
        # scratch filesystem. BLAZE still writes its complete plain FASTQ byte
        # stream, but a sibling wc process drains a FIFO and records the byte
        # count instead of persisting the disposable FASTQ. The drain is not a
        # descendant of the timed BLAZE process and is therefore excluded from
        # BLAZE CPU/RSS accounting. SN-ONT retains its original node-local file
        # output for continuity with its already accepted runs.
        if [[ "${DATASET}" == SC_PB ]]; then
            output="${det_work}/matched_reads.discarded.fastq"
            output_storage=node-local_fifo_counted_discard
        else
            output="${det_work}/matched_reads.fastq"
            output_storage=node-local
        fi
        putative_size_before="$(stat -Lc %s "${det_work}/putative_bc.csv")"
        putative_mtime_before="$(stat -Lc %Y "${det_work}/putative_bc.csv")"
        rm -f -- "${output}"
        attempt="$(new_attempt "${demux_root}")"
        mkdir -p -- "${attempt}"
        write_attempt_metadata "${attempt}/run_metadata.tsv" "${tool}" demultiplexing
        if [[ "${DATASET}" == SC_PB ]]; then
            mkfifo -- "${output}"
            # Opening the FIFO read/write prevents either endpoint from
            # blocking during startup. The drain closes its inherited guard;
            # the parent closes the last guard after BLAZE and its sampler end.
            exec {fifo_guard_fd}<>"${output}"
            drain_started="$(date -u +%FT%TZ)"
            (
                exec {fifo_guard_fd}>&-
                wc -c
            ) < "${output}" > "${attempt}/output_bytes.partial" \
                2> "${attempt}/output_drain.stderr.log" &
            drain_pid=$!
            write_command "${attempt}/output_drain_command.sh" wc -c
        fi
        local -a command=(
            env MPLCONFIGDIR="${det_work}/mpl" PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
        )
        if [[ "${DATASET}" == SC_PB ]]; then
            # BLAZE normally treats an existing FIFO as a completed output and
            # skips demultiplexing.  The launcher changes only that one parser
            # existence check, then restores os.path.exists before computation.
            # Do not use BLAZE --overwrite here: it would also rerun barcode
            # detection and invalidate the phase boundary/checkpoint.
            command+=(BLAZE_FIFO_OUTPUT="${output}" "${BLAZE_FIFO_LAUNCHER}")
        else
            command+=("${BLAZE_BIN}")
        fi
        command+=(
            --no-whitelisting
            --known-bc-list "${det_work}/whitelist.csv"
            --10x-kit-version 3v3
            --full-bc-whitelist "${GLOBAL_WHITELIST}"
            --max-edit-distance 2
            --threads "${THREADS}"
            --batch-size 1000
            --output-fastq "${output}"
            --minimal_stdout
            "${RAW_FASTQ}"
        )
        set +e
        run_timed_direct "${attempt}" "${det_work}" demultiplexing "${tool}" 1 "${command[@]}"
        rc=$?
        set -e
        if [[ "${DATASET}" == SC_PB ]]; then
            exec {fifo_guard_fd}>&-
            set +e
            wait "${drain_pid}"
            drain_rc=$?
            set -e
            drain_ended="$(date -u +%FT%TZ)"
            rm -f -- "${output}"
            if [[ -s "${attempt}/output_bytes.partial" ]]; then
                IFS= read -r drain_bytes < "${attempt}/output_bytes.partial"
                mv -f -- "${attempt}/output_bytes.partial" "${attempt}/output_bytes.txt"
            fi
            {
                printf 'key\tvalue\n'
                printf 'started_utc\t%s\n' "${drain_started}"
                printf 'ended_utc\t%s\n' "${drain_ended}"
                printf 'wrapper_exit_status\t%s\n' "${drain_rc}"
                printf 'uncompressed_bytes_consumed\t%s\n' "${drain_bytes}"
                printf 'sink\tfifo_to_wc_c_discard\n'
            } > "${attempt}/output_drain_status.tsv"
        fi
        putative_size_after="$(stat -Lc %s "${det_work}/putative_bc.csv")"
        putative_mtime_after="$(stat -Lc %Y "${det_work}/putative_bc.csv")"
        if ((rc != 0)) || ((drain_rc != 0)) || \
            { [[ "${DATASET}" == SC_PB ]] && [[ ! "${drain_bytes}" =~ ^[1-9][0-9]*$ ]]; } || \
            { [[ "${DATASET}" != SC_PB ]] && [[ ! -s "${output}" ]]; } || \
            [[ "${putative_size_after}" != "${putative_size_before}" ]] || \
            [[ "${putative_mtime_after}" != "${putative_mtime_before}" ]]; then
            output_size="$(stat -Lc %s "${output}" 2>/dev/null || printf 0)"
            [[ "${DATASET}" == SC_PB ]] && output_size="${drain_bytes}"
            printf 'failed_output_size_bytes\t%s\nfailed_output_path\t%s\n' \
                "${output_size}" "${output}" > "${attempt}/failed_output_metadata.tsv"
            touch "${attempt}/FAILED"
            rm -f -- "${output}"
            return 1
        fi
        {
            printf 'key\tvalue\n'
            printf 'putative_size_before\t%s\n' "${putative_size_before}"
            printf 'putative_size_after\t%s\n' "${putative_size_after}"
            printf 'putative_mtime_before\t%s\n' "${putative_mtime_before}"
            printf 'putative_mtime_after\t%s\n' "${putative_mtime_after}"
            printf 'barcode_search_skip_confirmed_by_unchanged_table\ttrue\n'
        } > "${attempt}/putative_table_reuse.tsv"
        [[ -s "${det_work}/summary.txt" ]] && cp -a -- "${det_work}/summary.txt" "${attempt}/tool_summary.txt"
        if [[ "${DATASET}" == SC_PB ]]; then
            output_size="${drain_bytes}"
        else
            output_size="$(stat -Lc %s "${output}")"
        fi
        {
            printf 'output_size_bytes\t%s\n' "${output_size}"
            printf 'output_path\t%s\n' "${output}"
            printf 'output_storage\t%s\n' "${output_storage}"
            printf 'output_compression\tnone\n'
            printf 'output_persisted\tfalse\n'
            printf 'output_deleted_after_acceptance\ttrue\n'
        } > "${attempt}/output_metadata.tsv"
        write_whitelist_metadata "${det_work}/whitelist.csv" "${attempt}"
        mark_complete "${demux_root}" "${attempt}"
        rm -f -- "${output}"
    fi
    safe_remove_tree "${tool_work}"
}

run_flex_detection_timed() {
    local attempt="$1" det_work="$2" format_discovery format_filter rc_discovery rc_filter
    local -a pipeline_status
    format_discovery="$(timing_format whitelist_detection Flexiplex discovery)"
    format_filter="$(timing_format whitelist_detection Flexiplex filter)"
    {
        printf '#!/usr/bin/env bash\nset -o pipefail\n'
        printf 'pigz -dc -p %q -- %q | ' "${FLEX_TRANSPORT_THREADS}" "${RAW_FASTQ}"
        printf '/usr/bin/time -q -f %q -o component_discovery.metrics.tsv -- ' "${format_discovery}"
        printf '%q ' "${FLEXIPLEX_BIN}" -f 0 -p "${THREADS}"
        printf '> read_count_histogram.tsv\n'
        printf '/usr/bin/time -q -f %q -o component_filter.metrics.tsv -- ' "${format_filter}"
        printf '%q ' env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 "${FLEXIPLEX_FILTER}" --whitelist "${GLOBAL_WHITELIST}" --outfile filtered_barcodes.txt flexiplex_barcodes_counts.txt
        printf '\n'
    } > "${attempt}/command.sh"

    set +e
    (
        cd -- "${det_work}"
        set +e
        pigz -dc -p "${FLEX_TRANSPORT_THREADS}" -- "${RAW_FASTQ}" 2> "${attempt}/input_pigz.stderr.log" |
            LC_ALL=C /usr/bin/time -q -f "${format_discovery}" -o "${attempt}/component_discovery.metrics.partial" -- \
                "${FLEXIPLEX_BIN}" -f 0 -p "${THREADS}" \
                > "${det_work}/read_count_histogram.tsv" 2> "${attempt}/discovery.stderr.log"
        pipeline_status=("${PIPESTATUS[@]}")
        printf 'input_pigz_exit_status\t%s\nflexiplex_exit_status\t%s\n' \
            "${pipeline_status[0]}" "${pipeline_status[1]}" > "${attempt}/discovery_pipeline_status.tsv"
        ((pipeline_status[0] == 0 && pipeline_status[1] == 0))
    )
    rc_discovery=$?
    set -e
    [[ -f "${attempt}/component_discovery.metrics.partial" ]] && mv -f -- \
        "${attempt}/component_discovery.metrics.partial" "${attempt}/component_discovery.metrics.tsv"

    rc_filter=1
    if ((rc_discovery == 0)) && [[ -s "${det_work}/flexiplex_barcodes_counts.txt" ]]; then
        set +e
        (
            cd -- "${det_work}"
            LC_ALL=C /usr/bin/time -q -f "${format_filter}" -o "${attempt}/component_filter.metrics.partial" -- \
                env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
                "${FLEXIPLEX_FILTER}" --whitelist "${GLOBAL_WHITELIST}" \
                --outfile "${det_work}/filtered_barcodes.txt" "${det_work}/flexiplex_barcodes_counts.txt" \
                > "${attempt}/filter.stdout.log" 2> "${attempt}/filter.stderr.log"
        )
        rc_filter=$?
        set -e
        [[ -f "${attempt}/component_filter.metrics.partial" ]] && mv -f -- \
            "${attempt}/component_filter.metrics.partial" "${attempt}/component_filter.metrics.tsv"
    fi
    {
        printf 'key\tvalue\n'
        printf 'discovery_wrapper_exit_status\t%s\n' "${rc_discovery}"
        printf 'filter_wrapper_exit_status\t%s\n' "${rc_filter}"
    } > "${attempt}/status.tsv"
    ((rc_discovery == 0 && rc_filter == 0)) || return 1
    python3 "${AGGREGATE_METRICS}" \
        --output "${attempt}/metrics.tsv" --dataset "${DATASET}" --phase whitelist_detection \
        --tool Flexiplex --threads "${THREADS}" --replicate "${REPLICATE}" \
        "${attempt}/component_discovery.metrics.tsv" "${attempt}/component_filter.metrics.tsv"
}

run_flex_demux_timed() {
    local attempt="$1" demux_work="$2" whitelist="$3" output_bytes_file="$4" format rc output_bytes
    local -a pipeline_status
    format="$(timing_format demultiplexing Flexiplex main)"
    {
        printf '#!/usr/bin/env bash\nset -o pipefail\n'
        printf 'pigz -dc -p %q -- %q | ' "${FLEX_TRANSPORT_THREADS}" "${RAW_FASTQ}"
        printf '/usr/bin/time -q -f %q -o metrics.tsv -- ' "${format}"
        printf '%q ' "${FLEXIPLEX_BIN}" -d 10x3v3 -e 2 -f 8 -k "${whitelist}" -p "${THREADS}"
        printf '| wc -c > %q\n' "${output_bytes_file}"
    } > "${attempt}/command.sh"

    set +e
    (
        cd -- "${demux_work}"
        set +e
        pigz -dc -p "${FLEX_TRANSPORT_THREADS}" -- "${RAW_FASTQ}" 2> "${attempt}/input_pigz.stderr.log" |
            LC_ALL=C /usr/bin/time -q -f "${format}" -o "${attempt}/metrics.partial" -- \
                "${FLEXIPLEX_BIN}" -d 10x3v3 -e 2 -f 8 \
                -k "${whitelist}" -p "${THREADS}" \
                2> "${attempt}/stderr.log" |
            wc -c > "${output_bytes_file}.partial" 2> "${attempt}/output_sink.stderr.log"
        pipeline_status=("${PIPESTATUS[@]}")
        printf 'input_pigz_exit_status\t%s\nflexiplex_exit_status\t%s\noutput_sink_exit_status\t%s\n' \
            "${pipeline_status[0]}" "${pipeline_status[1]}" "${pipeline_status[2]}" > "${attempt}/pipeline_status.tsv"
        ((pipeline_status[0] == 0 && pipeline_status[1] == 0 && pipeline_status[2] == 0))
    )
    rc=$?
    set -e
    [[ -f "${attempt}/metrics.partial" ]] && mv -f -- "${attempt}/metrics.partial" "${attempt}/metrics.tsv"
    if ((rc == 0)); then
        output_bytes="$(tr -d '[:space:]' < "${output_bytes_file}.partial")"
        if [[ "${output_bytes}" =~ ^[1-9][0-9]*$ ]]; then
            mv -f -- "${output_bytes_file}.partial" "${output_bytes_file}"
        else
            printf 'invalid counted Flexiplex stdout byte count: %q\n' "${output_bytes}" >&2
            rc=1
        fi
    fi
    {
        printf 'key\tvalue\n'
        printf 'wrapper_exit_status\t%s\n' "${rc}"
    } > "${attempt}/status.tsv"
    return "${rc}"
}

run_flexiplex() {
    local tool=Flexiplex tool_root="${BLOCK_ROOT}/Flexiplex" tool_work="${BLOCK_WORK}/Flexiplex"
    local det_root="${tool_root}/whitelist_detection" demux_root="${tool_root}/demultiplexing"
    local det_work="${tool_work}/detection" demux_work="${tool_work}/demux"
    local attempt accepted='' legacy_compressed_output rc output_bytes output_bytes_file whitelist

    whitelist="${det_work}/filtered_barcodes.txt"
    accepted="$(accepted_attempt "${demux_root}" 2>/dev/null || true)"
    if [[ -n "${accepted}" ]]; then
        safe_remove_tree "${tool_work}"
        return 0
    fi

    accepted="$(accepted_attempt "${det_root}" 2>/dev/null || true)"
    if [[ -n "${accepted}" && ! -s "${whitelist}" ]]; then
        [[ -s "${accepted}/whitelist.txt" ]] || {
            printf 'accepted Flexiplex detection lacks restart whitelist: %s\n' "${accepted}" >&2
            return 1
        }
        mkdir -p -- "${det_work}" "${demux_work}"
        cp -a -- "${accepted}/whitelist.txt" "${whitelist}.partial.$$"
        mv -f -- "${whitelist}.partial.$$" "${whitelist}"
    fi
    if [[ -z "${accepted}" ]]; then
        safe_remove_tree "${tool_work}"
        mkdir -p -- "${det_work}" "${demux_work}"
        attempt="$(new_attempt "${det_root}")"
        mkdir -p -- "${attempt}"
        write_attempt_metadata "${attempt}/run_metadata.tsv" "${tool}" whitelist_detection
        set +e
        run_flex_detection_timed "${attempt}" "${det_work}"
        rc=$?
        set -e
        if ((rc != 0)) || [[ ! -s "${whitelist}" ]]; then
            touch "${attempt}/FAILED"
            return 1
        fi
        write_whitelist_metadata "${whitelist}" "${attempt}"
        mark_complete "${det_root}" "${attempt}"
    fi

    accepted="$(accepted_attempt "${demux_root}" 2>/dev/null || true)"
    if [[ -z "${accepted}" ]]; then
        mkdir -p -- "${demux_work}"
        legacy_compressed_output="${demux_work}/${DATASET}_Flexiplex.fastq.gz"
        rm -f -- "${legacy_compressed_output}" "${legacy_compressed_output}.partial"
        output_bytes_file="${demux_work}/${DATASET}_Flexiplex.stdout_bytes.txt"
        rm -f -- "${output_bytes_file}" "${output_bytes_file}.partial"
        attempt="$(new_attempt "${demux_root}")"
        mkdir -p -- "${attempt}"
        write_attempt_metadata "${attempt}/run_metadata.tsv" "${tool}" demultiplexing
        set +e
        run_flex_demux_timed "${attempt}" "${demux_work}" "${whitelist}" "${output_bytes_file}"
        rc=$?
        set -e
        if ((rc != 0)) || [[ ! -s "${output_bytes_file}" ]]; then
            touch "${attempt}/FAILED"
            return 1
        fi
        output_bytes="$(tr -d '[:space:]' < "${output_bytes_file}")"
        {
            printf 'output_size_bytes\t%s\n' "${output_bytes}"
            printf 'uncompressed_bytes_consumed\t%s\n' "${output_bytes}"
            printf 'output_path\tstdout\n'
            printf 'output_storage\tcounted_discard\n'
            printf 'output_compression\tnone\n'
            printf 'output_persisted\tfalse\n'
            printf 'output_sink\twc_-c\n'
        } > "${attempt}/output_metadata.tsv"
        write_whitelist_metadata "${whitelist}" "${attempt}"
        mark_complete "${demux_root}" "${attempt}"
    fi
    safe_remove_tree "${tool_work}"
}

tool_phases_complete() {
    local tool_root="$1"
    accepted_attempt "${tool_root}/whitelist_detection" >/dev/null 2>&1 &&
        accepted_attempt "${tool_root}/demultiplexing" >/dev/null 2>&1
}

prewarm_for_tool() {
    local tool="$1" tool_root="$2" prewarm_root attempt started rc marker
    prewarm_root="${tool_root}/input_prewarm"
    attempt="$(new_attempt "${prewarm_root}")"
    mkdir -p -- "${attempt}"
    started="$(date -u +%FT%TZ)"
    {
        printf 'key\tvalue\n'
        printf 'dataset\t%s\n' "${DATASET}"
        printf 'tool\t%s\n' "${tool}"
        printf 'threads\t%s\n' "${THREADS}"
        printf 'replicate\t%s\n' "${REPLICATE}"
        printf 'hostname\t%s\n' "$(hostname -s)"
        printf 'cpu_model\t%s\n' "$(awk -F: '/model name/ {gsub(/^[ \t]+/, "", $2); print $2; exit}' /proc/cpuinfo)"
        printf 'pinned_node\t%s\n' "${PINNED_NODE}"
        printf 'host_matches_pin\t%s\n' "$([[ "$(hostname -s)" == "${PINNED_NODE}" ]] && printf true || printf false)"
        printf 'slurm_job_id\t%s\n' "${SLURM_JOB_ID:-none}"
        printf 'slurm_cpus_per_task\t%s\n' "${SLURM_CPUS_PER_TASK:-unknown}"
        printf 'input_fastq\t%s\n' "${RAW_FASTQ}"
        printf 'input_size_bytes\t%s\n' "$(stat -Lc %s "${RAW_FASTQ}")"
        printf 'input_sha256_preverified\t%s\n' "${INPUT_SHA256}"
        printf 'method\tdd compressed bytes to /dev/null, bs=32M\n'
        printf 'started_utc\t%s\n' "${started}"
    } > "${attempt}/metadata.tsv"

    set +e
    /usr/bin/time -q \
        -f 'user_seconds=%U\tsystem_seconds=%S\telapsed_seconds=%e\tmax_rss_kib=%M\texit_status=%x' \
        -o "${attempt}/metrics.partial" -- \
        dd if="${RAW_FASTQ}" of=/dev/null bs=32M status=none
    rc=$?
    set -e
    [[ -f "${attempt}/metrics.partial" ]] && mv -f -- \
        "${attempt}/metrics.partial" "${attempt}/metrics.tsv"
    {
        printf 'key\tvalue\n'
        printf 'started_utc\t%s\n' "${started}"
        printf 'ended_utc\t%s\n' "$(date -u +%FT%TZ)"
        printf 'wrapper_exit_status\t%s\n' "${rc}"
    } > "${attempt}/status.tsv"
    if ((rc != 0)); then
        touch "${attempt}/FAILED"
        return "${rc}"
    fi
    touch "${attempt}/COMPLETE"
    marker="${prewarm_root}/LATEST.partial.$$"
    printf '%s\n' "${attempt##*/}" > "${marker}"
    mv -f -- "${marker}" "${prewarm_root}/LATEST"
    PREWARM_ATTEMPT="${attempt}"
}

run_one_tool() {
    case "$1" in
        RAD) run_rad ;;
        Flexiplex) run_flexiplex ;;
        BLAZE) run_blaze ;;
    esac
}

if [[ -n "${REQUESTED_TOOL}" ]]; then
    tool_root="${BLOCK_ROOT}/${REQUESTED_TOOL}"
    mkdir -p -- "${tool_root}"
    exec {tool_lock_fd}> "${tool_root}/RUNNER.lock"
    flock -n "${tool_lock_fd}" || {
        printf '%s threads=%s replicate=%s tool=%s is already owned by another runner\n' \
            "${DATASET}" "${THREADS}" "${REPLICATE}" "${REQUESTED_TOOL}" >&2
        exit 3
    }

    if tool_phases_complete "${tool_root}"; then
        touch "${tool_root}/DONE"
        printf '%s threads=%s replicate=%s tool=%s already complete\n' \
            "${DATASET}" "${THREADS}" "${REPLICATE}" "${REQUESTED_TOOL}"
        exit 0
    fi

    PREWARM_ATTEMPT=''
    prewarm_for_tool "${REQUESTED_TOOL}" "${tool_root}"
    runner_started="$(date -u +%FT%TZ)"
    set +e
    run_one_tool "${REQUESTED_TOOL}"
    runner_rc=$?
    set -e
    {
        printf 'key\tvalue\n'
        printf 'dataset\t%s\n' "${DATASET}"
        printf 'tool\t%s\n' "${REQUESTED_TOOL}"
        printf 'threads\t%s\n' "${THREADS}"
        printf 'replicate\t%s\n' "${REPLICATE}"
        printf 'started_utc\t%s\n' "${runner_started}"
        printf 'ended_utc\t%s\n' "$(date -u +%FT%TZ)"
        printf 'wrapper_exit_status\t%s\n' "${runner_rc}"
    } > "${PREWARM_ATTEMPT}/tool_runner_status.tsv"
    ((runner_rc == 0)) || exit "${runner_rc}"
    tool_phases_complete "${tool_root}" || {
        printf '%s returned success without two accepted phases: %s\n' "${REQUESTED_TOOL}" "${tool_root}" >&2
        exit 1
    }
    touch "${tool_root}/DONE"
    printf 'PASS %s threads=%s replicate=%s tool=%s\n' \
        "${DATASET}" "${THREADS}" "${REPLICATE}" "${REQUESTED_TOOL}"
    exit 0
fi

if [[ -f "${BLOCK_ROOT}/DONE" ]]; then
    printf '%s threads=%s replicate=%s already complete\n' "${DATASET}" "${THREADS}" "${REPLICATE}"
    exit 0
fi

# Read the compressed bytes once outside every timed region so the first tool
# in a block is not uniquely penalized by a cold client page cache. This does
# not decompress or persist another copy of the input.
prewarm_started="$(date -u +%FT%TZ)"
set +e
/usr/bin/time -q \
    -f 'user_seconds=%U\tsystem_seconds=%S\telapsed_seconds=%e\tmax_rss_kib=%M\texit_status=%x' \
    -o "${BLOCK_ROOT}/input_prewarm.time.tsv.partial" -- \
    dd if="${RAW_FASTQ}" of=/dev/null bs=32M status=none
prewarm_rc=$?
set -e
[[ -f "${BLOCK_ROOT}/input_prewarm.time.tsv.partial" ]] && mv -f -- \
    "${BLOCK_ROOT}/input_prewarm.time.tsv.partial" "${BLOCK_ROOT}/input_prewarm.time.tsv"
((prewarm_rc == 0)) || { printf 'input prewarm failed with %s\n' "${prewarm_rc}" >&2; exit "${prewarm_rc}"; }
printf 'started_utc\t%s\nended_utc\t%s\nwrapper_exit_status\t%s\n' \
    "${prewarm_started}" "$(date -u +%FT%TZ)" "${prewarm_rc}" > "${BLOCK_ROOT}/input_prewarm.status.tsv"

case "${REPLICATE}" in
    1) TOOL_ORDER=(RAD Flexiplex BLAZE) ;;
    2) TOOL_ORDER=(Flexiplex BLAZE RAD) ;;
    3) TOOL_ORDER=(BLAZE RAD Flexiplex) ;;
esac

{
    printf 'key\tvalue\n'
    printf 'dataset\t%s\n' "${DATASET}"
    printf 'threads\t%s\n' "${THREADS}"
    printf 'replicate\t%s\n' "${REPLICATE}"
    printf 'tool_order\t%s\n' "${TOOL_ORDER[*]}"
    printf 'pinned_node\t%s\n' "${PINNED_NODE}"
    printf 'started_utc\t%s\n' "$(date -u +%FT%TZ)"
} > "${BLOCK_ROOT}/block_metadata.tsv"

for tool in "${TOOL_ORDER[@]}"; do
    case "${tool}" in
        RAD) run_rad ;;
        Flexiplex) run_flexiplex ;;
        BLAZE) run_blaze ;;
    esac
done

printf 'ended_utc\t%s\n' "$(date -u +%FT%TZ)" >> "${BLOCK_ROOT}/block_metadata.tsv"
touch "${BLOCK_ROOT}/DONE"
printf 'PASS %s threads=%s replicate=%s\n' "${DATASET}" "${THREADS}" "${REPLICATE}"
