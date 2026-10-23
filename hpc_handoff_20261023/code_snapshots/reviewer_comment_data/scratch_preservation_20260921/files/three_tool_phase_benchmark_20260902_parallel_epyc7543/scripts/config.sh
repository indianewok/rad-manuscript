#!/usr/bin/env bash

# Shared, immutable configuration for the SN-ONT / SC-PB scaling benchmark.
# Override RUN_ROOT only when intentionally cloning the complete run.

RUN_ROOT="${RUN_ROOT:-/scratch-nfs/f005f43/three_tool_phase_benchmark_20260902}"
LOCAL_WORK_ROOT="${LOCAL_WORK_ROOT:-/scratch/f005f43/three_tool_phase_benchmark_20260902}"

RAD_BIN="/scratch-nfs/f005f43/longbench_rad_4acbe00_raw_prism_20260827/tools/rad_4acbe00"
BLAZE_BIN="/scratch-nfs/f005f43/longbench_agent_runs_20260803/shared/tools/blaze2-2.5.0/venv/bin/blaze"
FLEXIPLEX_BIN="/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/software_pins_20260810/flexiplex_raw_to_assigned_audit/bin/flexiplex_v1.02.6_pristine"
FLEXIPLEX_FILTER="/scratch-nfs/f005f43/longbench_full_demux_20260730/tools/flexiplex-v1.01-paper/install/filter-env-pinned/bin/flexiplex-filter"

LAYOUT="/scratch-nfs/f005f43/longbench_rad_4acbe00_raw_prism_20260827/inputs/common/longbench_three_prime_v31.csv"
GLOBAL_WHITELIST="/scratch-nfs/f005f43/longbench_rad_4acbe00_raw_prism_20260827/inputs/common/3M-february-2018-3v3.txt"
RAD_SCAN_WHITELIST="${RUN_ROOT}/inputs/3M-february-2018-3v3.txt_bitlist.csv.gz"
PROCESS_SAMPLER="/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/rad_longbench_timing_memory_20260726/harness/sample_process_tree.sh"
AGGREGATE_METRICS="${RUN_ROOT}/scripts/aggregate_metrics.py"

# External Flexiplex transport is deliberately fixed and is outside the timed
# Flexiplex process. RAD scan-wl retains its native hard-wired pigz -p T path,
# per the user's request to observe that extra CPU burden rather than normalize it.
FLEX_TRANSPORT_THREADS="${FLEX_TRANSPORT_THREADS:-1}"
RAD_DEMUX_PIGZ_THREADS="${RAD_DEMUX_PIGZ_THREADS:-1}"
RSS_SAMPLE_INTERVAL_SECONDS="${RSS_SAMPLE_INTERVAL_SECONDS:-2}"

dataset_config() {
    local dataset="$1"
    case "${dataset}" in
        SN_ONT)
            RAW_FASTQ="${BENCHMARK_RAW_FASTQ:-/scratch-nfs/f005f43/rad_longbench_20260726/data/sc_sn/raw_fastq/SN_ONT.fastq.gz}"
            EXPECTED_READS=119016231
            INPUT_SHA256="62e75b222c7046cfa0297ca59f56a26fdb923e3307edda0bb69701713719801a"
            BLAZE_SELECTOR=(--force-cells 10000)
            PINNED_NODE=a02
            ;;
        SC_PB)
            RAW_FASTQ="${BENCHMARK_RAW_FASTQ:-/scratch-nfs/f005f43/rad_longbench_20260726/data/sc_sn/raw_fastq/SC_PB.fastq.gz}"
            EXPECTED_READS=195242483
            INPUT_SHA256="68e818fdd9d329e56fd159ac90befba8350d30a4eaa959610fe03fd4484d07d4"
            BLAZE_SELECTOR=(--expect-cells 5000)
            PINNED_NODE=t02
            ;;
        *)
            printf 'Unsupported dataset: %s\n' "${dataset}" >&2
            return 2
            ;;
    esac
}
