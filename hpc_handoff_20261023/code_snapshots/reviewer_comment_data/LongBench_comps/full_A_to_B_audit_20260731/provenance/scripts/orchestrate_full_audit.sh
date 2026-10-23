#!/usr/bin/env bash
set -euo pipefail

audit_root=/scratch/f005f43/longbench_full_ab_audit_20260730
producer_root=/scratch-nfs/f005f43/longbench_full_demux_20260730
status_log="${audit_root}/logs/orchestrator.log"

mkdir -p "${audit_root}/logs"
exec >> "${status_log}" 2>&1

echo "$(date -u +%FT%TZ) orchestrator started"

# The node was heavily oversubscribed when this audit was staged. Wait for
# the current full demultiplexing producers before launching extra full-file
# passes, while leaving the already-running jobs untouched.
while true; do
    missing=0
    for marker in \
        "${producer_root}/runs/blaze2_2.5.0_longbench_published/SC_PB/DONE" \
        "${producer_root}/runs/blaze2_2.5.0_longbench_published/SN_PB/DONE" \
        "${producer_root}/runs/rad_920adda_current/SN_PB/DONE"; do
        [[ -e "${marker}" ]] || missing=$((missing + 1))
    done
    read -r load_one _ < /proc/loadavg
    printf '%s producer_markers_missing=%d load1=%s\n' \
        "$(date -u +%FT%TZ)" "${missing}" "${load_one}"
    if [[ "${missing}" -eq 0 ]] &&
        awk -v value="${load_one}" 'BEGIN {exit !(value < 160)}'; then
        break
    fi
    sleep 60
done

echo "$(date -u +%FT%TZ) starting updated Flexiplex full-data audit passes"

FLEX_AUDIT_THREADS=16 "${audit_root}/scripts/run_flex_v1026_audit_one.sh" SC_PB &
pid_v1026_scpb=$!
FLEX_AUDIT_THREADS=16 "${audit_root}/scripts/run_flex_v1026_audit_one.sh" SC_ONT &
pid_v1026_scont=$!
wait "${pid_v1026_scpb}" "${pid_v1026_scont}"

FLEX_AUDIT_THREADS=16 "${audit_root}/scripts/run_flex_v1026_audit_one.sh" SN_PB &
pid_v1026_snpb=$!
FLEX_AUDIT_THREADS=16 "${audit_root}/scripts/run_flex_v1026_audit_one.sh" SN_ONT &
pid_v1026_snont=$!
wait "${pid_v1026_snpb}" "${pid_v1026_snont}"

echo "$(date -u +%FT%TZ) Flexiplex diagnostics complete; starting analyzers"

for arm in blaze flex_v1026 rad; do
    analysis_pids=()
    for dataset in SC_ONT SC_PB SN_ONT SN_PB; do
        "${audit_root}/scripts/run_analyzer_one.sh" "${dataset}" "${arm}" &
        analysis_pids+=("$!")
    done
    for analysis_pid in "${analysis_pids[@]}"; do
        wait "${analysis_pid}"
    done
    printf '%s completed_analysis_arm=%s\n' "$(date -u +%FT%TZ)" "${arm}"
done

touch "${audit_root}/ANALYSIS_ARMS_DONE"
echo "$(date -u +%FT%TZ) all full-read analysis arms complete"
